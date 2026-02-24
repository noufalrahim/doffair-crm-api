from pydantic import BaseModel, Field
from typing import Dict, List, Optional

class MetricWithGrowth(BaseModel):
    count: float = Field(..., description="The current value of the metric")
    growth: float = Field(..., description="Percentage growth compared to the previous period")
    status: str = Field(..., description="Direction of growth: positive, negative, or neutral")

class MetricAmountWithGrowth(BaseModel):
    count: int = Field(..., description="Total count")
    amount: float = Field(..., description="Total amount/revenue")
    growth_count: float = Field(..., description="Percentage growth in count")
    growth_amount: float = Field(..., description="Percentage growth in amount")
    status_count: str = Field(..., description="Direction of growth for count: positive, negative, or neutral")
    status_amount: str = Field(..., description="Direction of growth for amount: positive, negative, or neutral")

class VerticalStat(BaseModel):
    completed: int
    growth: float
    status: str = Field(..., description="Direction of growth: positive, negative, or neutral")

class AnalyticsBookings(BaseModel):
    offline: MetricAmountWithGrowth
    online: MetricAmountWithGrowth
    total_completed: MetricWithGrowth
    total_bookings: MetricWithGrowth

class AnalyticsVerticals(BaseModel):
    vet: VerticalStat
    groomer: VerticalStat

class AnalyticsCustomers(BaseModel):
    total: MetricWithGrowth

class PeriodRange(BaseModel):
    start: str
    end: str

class AnalyticsMeta(BaseModel):
    current_period: PeriodRange
    previous_period: PeriodRange

class VendorAnalyticsData(BaseModel):
    period: str
    bookings: AnalyticsBookings
    verticals: AnalyticsVerticals
    customers: AnalyticsCustomers
    meta: AnalyticsMeta

class VendorAnalyticsResponse(BaseModel):
    success: bool
    data: VendorAnalyticsData
    success_message: Optional[str] = None
    error_message: Optional[str] = None
