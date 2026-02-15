from datetime import datetime, timedelta, time
from typing import List, Optional
from odmantic import AIOEngine
from bson import ObjectId

from vendor.models.doctor_availability import Availability
from vendor.models.holiday import Holiday
from vendor.schemas.availability_helper import (
    AvailabilitySlot,
    AvailabilitySection,
    DailyAvailabilityResponse
)

def parse_time(t_str: str) -> time:
    """Parse HH:MM or HH:MM AM/PM into time object"""
    try:
        if " " in t_str:
            return datetime.strptime(t_str, "%I:%M %p").time()
        return datetime.strptime(t_str, "%H:%M").time()
    except Exception:
        return time(0, 0)

def format_time(t: time) -> str:
    """Format time object to HH:MM AM/PM"""
    dt = datetime.combine(datetime.min, t)
    return dt.strftime("%I:%M %p")

def get_slots_in_range(start_t: time, end_t: time, interval_minutes: int = 30) -> List[AvailabilitySlot]:
    """Split a time range into slots"""
    slots = []
    current_dt = datetime.combine(datetime.min, start_t)
    end_dt = datetime.combine(datetime.min, end_t)
    
    while current_dt + timedelta(minutes=interval_minutes) <= end_dt:
        slot_start = current_dt.time()
        slot_end = (current_dt + timedelta(minutes=interval_minutes)).time()
        slots.append(AvailabilitySlot(
            start_time=format_time(slot_start),
            end_time=format_time(slot_end),
            is_open=True
        ))
        current_dt += timedelta(minutes=interval_minutes)
    
    return slots

async def get_daily_availability(
    engine: AIOEngine,
    vendor_id: str,
    target_date: datetime,
    location_id: str,
    vertical_id: str,
    care_professional_id: Optional[str] = None
) -> DailyAvailabilityResponse:
    # 1. Setup session boundaries (05:00 AM Today to 05:00 AM Tomorrow)
    midnight = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
    session_window_start_dt = midnight.replace(hour=5)
    session_window_end_dt = session_window_start_dt + timedelta(days=1)
    
    # 2. Helper to get raw availability ranges for a single date
    async def get_ranges_for_date(dt: datetime):
        mid = dt.replace(hour=0, minute=0, second=0, microsecond=0)
        eod = mid.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        # a. Check Holidays
        h_query = {"vendor_id": vendor_id, "date": {"$gte": mid, "$lte": eod}}
        if vertical_id:
            v_conds = [{"vertical_id": vertical_id}, {"vertical_id": None}]
            if ObjectId.is_valid(vertical_id):
                v_conds.insert(1, {"vertical_id": ObjectId(vertical_id)})
            h_query["$or"] = v_conds
        
        holidays_cursor = engine.get_collection(Holiday).find(h_query)
        holidays = await holidays_cursor.to_list(length=5)
        
        is_hol = False
        hol_name = None
        raw_ranges = []
        
        if holidays:
            # Shift selection priority: specific vertical or default
            h = holidays[0]
            if vertical_id:
                spec = next((hol for hol in holidays if hol.get("vertical_id") == vertical_id or (ObjectId.is_valid(vertical_id) and hol.get("vertical_id") == ObjectId(vertical_id))), None)
                if spec: h = spec
            
            is_hol = h.get("is_all_day", True)
            hol_name = h.get("name")
            if not h.get("is_all_day"):
                for s in h.get("slots", []):
                    raw_ranges.append((parse_time(s.get("start_time")), parse_time(s.get("end_time"))))
            return raw_ranges, is_hol, hol_name

        # b. Check Weekly Availability
        filters = [Availability.vendor_id == vendor_id, Availability.day_of_week == dt.weekday()]
        
        if vertical_id:
            if ObjectId.is_valid(vertical_id):
                filters.append((Availability.vertical_id == vertical_id) | (Availability.vertical_id == ObjectId(vertical_id)))
            else:
                filters.append(Availability.vertical_id == vertical_id)
        
        target_id = care_professional_id
        if target_id:
            if ObjectId.is_valid(target_id):
                filters.append(
                    (Availability.care_professional_id == target_id) | 
                    (Availability.care_professional_id == ObjectId(target_id))
                )
            else:
                filters.append(Availability.care_professional_id == target_id)

        if location_id:
            if ObjectId.is_valid(location_id):
                filters.append((Availability.location_id == location_id) | (Availability.location_id == ObjectId(location_id)))
            else:
                filters.append(Availability.location_id == location_id)

        availabilities = await engine.find(Availability, *filters)
        for a in availabilities:
            raw_ranges.append((parse_time(a.start_time), parse_time(a.end_time)))
            
        return raw_ranges, False, None

    # 3. Fetch for Yesterday, Today, Tomorrow to satisfy the 05:00 AM session window
    yest_ranges, _, _ = await get_ranges_for_date(target_date - timedelta(days=1))
    today_ranges, is_holiday, holiday_name = await get_ranges_for_date(target_date)
    tom_ranges, _, _ = await get_ranges_for_date(target_date + timedelta(days=1))

    # 4. Create datetime-based active ranges within the session window
    active_ranges_dt = []
    dates_and_ranges = [
        (target_date - timedelta(days=1), yest_ranges),
        (target_date, today_ranges),
        (target_date + timedelta(days=1), tom_ranges)
    ]
    
    for d_dt, raw_r in dates_and_ranges:
        d_mid = d_dt.replace(hour=0, minute=0, second=0, microsecond=0)
        for rs, re in raw_r:
            start_dt = d_mid.replace(hour=rs.hour, minute=rs.minute)
            end_dt = d_mid.replace(hour=re.hour, minute=re.minute)
            # Handle wrap-around or midnight
            if re < rs or (re == time(0, 0) and rs != time(0, 0)):
                end_dt += timedelta(days=1)
            
            i_start = max(start_dt, session_window_start_dt)
            i_end = min(end_dt, session_window_end_dt)
            
            if i_start < i_end:
                active_ranges_dt.append((i_start, i_end))

    if not active_ranges_dt:
        return DailyAvailabilityResponse(date=target_date.date(), is_holiday=is_holiday, holiday_name=holiday_name, sections=[])

    # 5. Determine session-specific Start and End purely from DB
    session_start_dt = min(r[0] for r in active_ranges_dt)
    session_end_dt = max(r[1] for r in active_ranges_dt)

    if session_start_dt >= session_end_dt:
         return DailyAvailabilityResponse(date=target_date.date(), is_holiday=is_holiday, holiday_name=holiday_name, sections=[])

    # 6. Generate slots
    def generate_slots(b_start_dt: datetime, b_end_dt: datetime) -> List[AvailabilitySlot]:
        slots = []
        act_start = max(b_start_dt, session_start_dt)
        act_end = min(b_end_dt, session_end_dt)
        
        curr = act_start
        while curr + timedelta(minutes=30) <= act_end:
            s_t = curr.time()
            nxt = curr + timedelta(minutes=30)
            e_t = nxt.time()
            
            is_open = False
            for rs_dt, re_dt in active_ranges_dt:
                if rs_dt <= curr and nxt <= re_dt:
                    is_open = True
                    break
            
            slots.append(AvailabilitySlot(start_time=format_time(s_t), end_time=format_time(e_t), is_open=is_open))
            curr = nxt
        return slots

    sections = [
        AvailabilitySection(slot="morning", slot_period=generate_slots(midnight.replace(hour=5), midnight.replace(hour=12))),
        AvailabilitySection(slot="afternoon", slot_period=generate_slots(midnight.replace(hour=12), midnight.replace(hour=17))),
        AvailabilitySection(slot="evening", slot_period=generate_slots(midnight.replace(hour=17), midnight.replace(hour=21))),
        AvailabilitySection(slot="night", slot_period=generate_slots(midnight.replace(hour=21), midnight.replace(hour=5) + timedelta(days=1)))
    ]
    
    return DailyAvailabilityResponse(
        date=target_date.date(),
        is_holiday=is_holiday,
        holiday_name=holiday_name,
        sections=[s for s in sections if s.slot_period]
    )
