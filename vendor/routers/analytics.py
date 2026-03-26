from fastapi import APIRouter, Depends, HTTPException, Query
from odmantic import AIOEngine
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
from bson import ObjectId

from core.database import get_engine, get_secondary_engine
from core.security import require_vendor
from utils.response import success_response
from core.enums import BookingStatus
from vendor.schemas.analytics import VendorAnalyticsResponse, RevenueAnalyticsResponse

router = APIRouter(
    prefix="/vendor/statistics",
    tags=["Vendor Statistics"],
)

# Vertical IDs identified from research
GROOMER_VERTICAL_ID = "69522b6ce6a07c46de0f88d7"
VET_VERTICAL_ID = "69529fdb5a26a27c25c7c65a"

def get_period_ranges(period: str) -> Tuple[datetime, datetime, datetime, datetime]:
    """
    Returns (current_start, current_end, previous_start, previous_end)
    """
    now = datetime.now(timezone.utc)
    
    if period == "today":
        current_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        previous_start = current_start - timedelta(days=1)
        previous_end = current_start
        return current_start, now, previous_start, previous_end
        
    elif period == "week":
        current_start = now - timedelta(days=7)
        previous_start = current_start - timedelta(days=7)
        previous_end = current_start
        return current_start, now, previous_start, previous_end
        
    elif period == "year":
        current_start = now - timedelta(days=365)
        previous_start = current_start - timedelta(days=365)
        previous_end = current_start
        return current_start, now, previous_start, previous_end
        
    else: # Default: month
        current_start = now - timedelta(days=30)
        previous_start = current_start - timedelta(days=30)
        previous_end = current_start
        return current_start, now, previous_start, previous_end

def calculate_growth(current: float, previous: float) -> float:
    if previous == 0:
        return 100.0 if current > 0 else 0.0
    return round(((current - previous) / previous) * 100, 2)

def get_growth_status(growth: float) -> str:
    if growth > 0:
        return "positive"
    elif growth < 0:
        return "negative"
    return "neutral"

ACTIVE_STATUSES = [BookingStatus.CONFIRMED, BookingStatus.ONGOING, BookingStatus.PENDING_APPROVAL]

async def aggregate_metrics(
    primary_db, 
    secondary_db, 
    vendor_id: str, 
    vendor_oid: Optional[ObjectId],
    start_date: datetime, 
    end_date: datetime
):
    walkin_coll = primary_db.get_collection("walkin_bookings")
    online_coll = secondary_db.get_collection("bookings")
    
    # Offline
    offline_criteria = {
        "vendor_id": vendor_id, 
        "is_offline": True,
        "booking_date": {"$gte": start_date, "$lt": end_date}
    }
    total_offline_count = await walkin_coll.count_documents(offline_criteria)
    
    offline_amount_pipeline = [
        {"$match": offline_criteria},
        {"$group": {"_id": None, "total": {"$sum": "$final_amount"}}}
    ]
    offline_amount_res = await walkin_coll.aggregate(offline_amount_pipeline).to_list(1)
    total_offline_amount = offline_amount_res[0]["total"] if offline_amount_res else 0

    # Online
    online_vendor_or = [{"serviceProviderId": vendor_id}, {"vendor_id": vendor_id}]
    if vendor_oid:
        online_vendor_or.append({"serviceProviderId": vendor_oid})
        
    online_criteria = {
        "$and": [
            {"$or": online_vendor_or},
            {"$or": [
                {"booking_date": {"$gte": start_date, "$lt": end_date}},
                {"startTime": {"$gte": start_date, "$lt": end_date}}
            ]}
        ]
    }
    
    total_online_count = await online_coll.count_documents(online_criteria)
    
    online_amount_pipeline = [
        {"$match": online_criteria},
        {"$group": {"_id": None, "total": {"$sum": {"$ifNull": ["$bookingAmount", "$final_amount", 0]}}}}
    ]
    online_amount_res = await online_coll.aggregate(online_amount_pipeline).to_list(1)
    total_online_amount = online_amount_res[0]["total"] if online_amount_res else 0

    total_completed = await walkin_coll.count_documents({**offline_criteria, "status": "completed"}) + \
                      await online_coll.count_documents({**online_criteria, "status": "completed"})
    
    total_active = await walkin_coll.count_documents({**offline_criteria, "status": {"$in": ACTIVE_STATUSES}}) + \
                   await online_coll.count_documents({**online_criteria, "status": {"$in": ACTIVE_STATUSES}})

    total_cancelled = await walkin_coll.count_documents({**offline_criteria, "status": "cancelled"}) + \
                      await online_coll.count_documents({**online_criteria, "status": {"$in": ["cancelled", "cancelByProvider", "rejected"]}})

    vet_codes = ['veteran', 'vet', 'veterinary']
    groomer_codes = ['groomer', 'groom', 'grooming']
    
    async def get_v_data(v_id, codes):
        p_crit = {
            "vendor_id": vendor_id,
            "booking_date": {"$gte": start_date, "$lt": end_date},
            "$or": [{"vertical_id": v_id}, {"vertical_id": ObjectId(v_id)}]
        }
        s_crit = {
            **online_criteria,
            "serviceProviderType": {"$in": codes}
        }
        comp = await walkin_coll.count_documents({**p_crit, "status": "completed"}) + \
               await online_coll.count_documents({**s_crit, "status": "completed"})
        
        active = await walkin_coll.count_documents({**p_crit, "status": {"$in": ACTIVE_STATUSES}}) + \
                 await online_coll.count_documents({**s_crit, "status": {"$in": ACTIVE_STATUSES}})
        
        cancelled = await walkin_coll.count_documents({**p_crit, "status": "cancelled"}) + \
                    await online_coll.count_documents({**s_crit, "status": {"$in": ["cancelled", "cancelByProvider", "rejected"]}})
                    
        return {
            "completed": comp,
            "active": active,
            "cancelled": cancelled
        }

    vet_data = await get_v_data(VET_VERTICAL_ID, vet_codes)
    groomer_data = await get_v_data(GROOMER_VERTICAL_ID, groomer_codes)

    off_cust = await walkin_coll.distinct("user_phone", {"vendor_id": vendor_id, "booking_date": {"$gte": start_date, "$lt": end_date}})
    on_cust = await online_coll.distinct("userId", online_criteria)
    on_phones = await online_coll.distinct("user_phone", online_criteria)
    total_cust = len(set(off_cust).union(set(on_phones or [])).union(set(str(u) for u in on_cust)))

    return {
        "offline_count": total_offline_count,
        "offline_amount": total_offline_amount,
        "online_count": total_online_count,
        "online_amount": total_online_amount,
        "total_completed": total_completed,
        "total_active": total_active,
        "total_cancelled": total_cancelled,
        "total_bookings": total_offline_count + total_online_count,
        "vet": vet_data,
        "groomer": groomer_data,
        "total_customers": total_cust
    }

@router.get(
    "",
    response_model=VendorAnalyticsResponse,
    summary="Get Vendor Analytics",
    description="Get holistic analytics for the authenticated vendor, including growth metrics for different time periods (today, week, month, year)."
)
async def get_vendor_analytics(
    period: str = Query(
        "month", 
        description="Time period to fetch data for (today, week, month, year)",
        pattern="^(today|week|month|year)$"
    ),
    primary_engine: AIOEngine = Depends(get_engine),
    secondary_engine: AIOEngine = Depends(get_secondary_engine),
    token: dict = Depends(require_vendor())
):
    """
    Get analytics for the authenticated vendor across online and offline bookings with period filtering.
    """
    vendor_id = token.get("vendor_id")
    if not vendor_id:
        raise HTTPException(status_code=401, detail="Vendor ID not found in token")
        
    vendor_oid = ObjectId(vendor_id) if ObjectId.is_valid(vendor_id) else None
    
    c_start, c_end, p_start, p_end = get_period_ranges(period)
    
    current_metrics = await aggregate_metrics(primary_engine.database, secondary_engine.database, vendor_id, vendor_oid, c_start, c_end)
    previous_metrics = await aggregate_metrics(primary_engine.database, secondary_engine.database, vendor_id, vendor_oid, p_start, p_end)

    # Calculate growth values
    off_g_count = calculate_growth(current_metrics["offline_count"], previous_metrics["offline_count"])
    off_g_amount = calculate_growth(current_metrics["offline_amount"], previous_metrics["offline_amount"])
    on_g_count = calculate_growth(current_metrics["online_count"], previous_metrics["online_count"])
    on_g_amount = calculate_growth(current_metrics["online_amount"], previous_metrics["online_amount"])
    total_comp_g = calculate_growth(current_metrics["total_completed"], previous_metrics["total_completed"])
    total_bk_g = calculate_growth(current_metrics["total_bookings"], previous_metrics["total_bookings"])
    vet_g = calculate_growth(current_metrics["vet_completed"], previous_metrics["vet_completed"])
    groomer_g = calculate_growth(current_metrics["groomer_completed"], previous_metrics["groomer_completed"])
    cust_g = calculate_growth(current_metrics["total_customers"], previous_metrics["total_customers"])

    return success_response(data={
        "period": period,
        "bookings": {
            "offline": {
                "count": current_metrics["offline_count"],
                "amount": current_metrics["offline_amount"],
                "growth_count": off_g_count,
                "growth_amount": off_g_amount,
                "status_count": get_growth_status(off_g_count),
                "status_amount": get_growth_status(off_g_amount)
            },
            "online": {
                "count": current_metrics["online_count"],
                "amount": current_metrics["online_amount"],
                "growth_count": on_g_count,
                "growth_amount": on_g_amount,
                "status_count": get_growth_status(on_g_count),
                "status_amount": get_growth_status(on_g_amount)
            },
            "total_completed": {
                "count": current_metrics["total_completed"],
                "growth": total_comp_g,
                "status": get_growth_status(total_comp_g)
            },
            "total_bookings": {
                "count": current_metrics["total_bookings"],
                "growth": total_bk_g,
                "status": get_growth_status(total_bk_g)
            }
        },
        "verticals": {
            "vet": {
                "active": current_metrics["vet"]["active"],
                "completed": current_metrics["vet"]["completed"],
                "cancelled": current_metrics["vet"]["cancelled"],
                "growth": vet_g,
                "status": get_growth_status(vet_g)
            },
            "groomer": {
                "active": current_metrics["groomer"]["active"],
                "completed": current_metrics["groomer"]["completed"],
                "cancelled": current_metrics["groomer"]["cancelled"],
                "growth": groomer_g,
                "status": get_growth_status(groomer_g)
            }
        },
        "customers": {
            "total": {
                "count": current_metrics["total_customers"],
                "growth": cust_g,
                "status": get_growth_status(cust_g)
            }
        },
        "meta": {
            "current_period": {"start": c_start.isoformat(), "end": c_end.isoformat()},
            "previous_period": {"start": p_start.isoformat(), "end": p_end.isoformat()}
        }
    })

async def aggregate_monthly_revenue(
    primary_db, 
    secondary_db, 
    vendor_id: str, 
    vendor_oid: Optional[ObjectId],
    start_date: datetime, 
    end_date: datetime,
    vertical_id: Optional[str] = None,
    vertical_codes: Optional[List[str]] = None
):
    walkin_coll = primary_db.get_collection("walkin_bookings")
    online_coll = secondary_db.get_collection("bookings")
    
    # Months list
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    results = {m: {"online": 0.0, "walkin": 0.0} for m in months}

    # Pipeline for walkin/offline bookings
    offline_match = {
        "vendor_id": vendor_id,
        "is_offline": True,
        "booking_date": {"$gte": start_date, "$lt": end_date}
    }
    if vertical_id:
        offline_match["$or"] = [{"vertical_id": vertical_id}, {"vertical_id": ObjectId(vertical_id)}]

    offline_pipeline = [
        {"$match": offline_match},
        {
            "$group": {
                "_id": {"$month": "$booking_date"},
                "total": {"$sum": "$final_amount"}
            }
        }
    ]
    
    off_res = await walkin_coll.aggregate(offline_pipeline).to_list(12)
    for r in off_res:
        results[months[r["_id"] - 1]]["walkin"] = float(r["total"])

    # Pipeline for online bookings
    online_vendor_or = [{"serviceProviderId": vendor_id}, {"vendor_id": vendor_id}]
    if vendor_oid:
        online_vendor_or.append({"serviceProviderId": vendor_oid})

    online_match_and = [
        {"$or": online_vendor_or},
        {
            "$or": [
                {"booking_date": {"$gte": start_date, "$lt": end_date}},
                {"startTime": {"$gte": start_date, "$lt": end_date}}
            ]
        }
    ]
    if vertical_codes:
        online_match_and.append({"serviceProviderType": {"$in": vertical_codes}})

    online_pipeline = [
        {"$match": {"$and": online_match_and}},
        {
            "$group": {
                "_id": {
                    "$month": {
                        "$ifNull": ["$booking_date", "$startTime"]
                    }
                },
                "total": {"$sum": {"$ifNull": ["$bookingAmount", "$final_amount", 0]}}
            }
        }
    ]

    on_res = await online_coll.aggregate(online_pipeline).to_list(12)
    for r in on_res:
        results[months[r["_id"] - 1]]["online"] = float(r["total"])

    return [{"month": m, "online": results[m]["online"], "walkin": results[m]["walkin"]} for m in months]

@router.get(
    "/revenue-monthly",
    response_model=RevenueAnalyticsResponse,
    summary="Get Monthly Revenue Analytics",
    description="Get month-wise revenue for the current year, separated by online and walk-in bookings. Can be filtered by verticalId."
)
async def get_revenue_monthly_analytics(
    verticalId: Optional[str] = Query(None, description="Filter by vertical ID", example="69522b6ce6a07c46de0f88d7"),
    primary_engine: AIOEngine = Depends(get_engine),
    secondary_engine: AIOEngine = Depends(get_secondary_engine),
    token: dict = Depends(require_vendor())
):
    vendor_id = token.get("vendor_id")
    if not vendor_id:
        raise HTTPException(status_code=401, detail="Vendor ID not found in token")
        
    vendor_oid = ObjectId(vendor_id) if ObjectId.is_valid(vendor_id) else None
    
    vertical_codes = None
    if verticalId:
        from admin.models.vertical import Vertical
        v_def = await primary_engine.find_one(Vertical, Vertical.id == ObjectId(verticalId))
        if not v_def:
            raise HTTPException(status_code=404, detail="Vertical not found")
        vertical_codes = v_def.code

    now = datetime.utcnow()
    year_start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    year_end = (year_start + timedelta(days=366)).replace(month=1, day=1) # Start of next year
    
    data = await aggregate_monthly_revenue(
        primary_engine.database, 
        secondary_engine.database, 
        vendor_id, 
        vendor_oid, 
        year_start, 
        year_end,
        vertical_id=verticalId,
        vertical_codes=vertical_codes
    )
    
    return success_response(data=data)
