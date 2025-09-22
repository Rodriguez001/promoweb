"""
Analytics schemas for PromoWeb Africa.
Pydantic models for analytics and reporting data validation.
"""

from datetime import datetime, date
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, validator
from decimal import Decimal
from enum import Enum


# Enums
class AnalyticsPeriod(str, Enum):
    """Analytics time period options."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class MetricType(str, Enum):
    """Metric type options."""
    REVENUE = "revenue"
    ORDERS = "orders"
    USERS = "users"
    PRODUCTS = "products"
    CONVERSION = "conversion"
    TRAFFIC = "traffic"


# Search analytics schemas
class SearchAnalyticsQuery(BaseModel):
    """Search analytics query parameters."""
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    period: AnalyticsPeriod = Field(default=AnalyticsPeriod.DAILY)
    limit: int = Field(default=50, ge=1, le=1000)


class SearchAnalyticsResponse(BaseModel):
    """Search analytics response."""
    query: str
    search_count: int
    results_count: int
    click_count: int
    click_through_rate: float
    conversion_count: int
    conversion_rate: float
    revenue_generated: Decimal


class SearchTrends(BaseModel):
    """Search trends data."""
    trending_queries: List[SearchAnalyticsResponse]
    no_results_queries: List[Dict[str, Any]]
    top_clicked_products: List[Dict[str, Any]]
    search_volume_by_date: Dict[str, int]
    period_start: date
    period_end: date


# Product analytics schemas
class ProductAnalyticsQuery(BaseModel):
    """Product analytics query parameters."""
    product_ids: Optional[List[str]] = None
    category_ids: Optional[List[str]] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    period: AnalyticsPeriod = Field(default=AnalyticsPeriod.DAILY)
    metric: Optional[MetricType] = None
    limit: int = Field(default=50, ge=1, le=1000)


class ProductPerformanceMetrics(BaseModel):
    """Product performance metrics."""
    product_id: str
    product_title: str
    product_image: Optional[str]
    views: int
    unique_views: int
    cart_additions: int
    purchases: int
    revenue: Decimal
    conversion_rate: float
    bounce_rate: float
    average_time_on_page: int  # seconds
    rating: Optional[float]
    review_count: int


class ProductAnalyticsResponse(BaseModel):
    """Product analytics response."""
    products: List[ProductPerformanceMetrics]
    summary: Dict[str, Any]
    period_start: date
    period_end: date


# User analytics schemas
class UserAnalyticsQuery(BaseModel):
    """User analytics query parameters."""
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    period: AnalyticsPeriod = Field(default=AnalyticsPeriod.DAILY)
    user_segment: Optional[str] = None  # new, returning, vip, etc.


class UserMetrics(BaseModel):
    """User metrics data."""
    total_users: int
    new_users: int
    returning_users: int
    active_users: int
    user_retention_rate: float
    average_session_duration: int  # seconds
    pages_per_session: float
    bounce_rate: float


class UserSegmentAnalytics(BaseModel):
    """User segment analytics."""
    segment_name: str
    user_count: int
    percentage: float
    average_order_value: Decimal
    total_revenue: Decimal
    conversion_rate: float
    retention_rate: float


class UserAnalyticsResponse(BaseModel):
    """User analytics response."""
    metrics: UserMetrics
    segments: List[UserSegmentAnalytics]
    user_acquisition_by_channel: Dict[str, int]
    user_activity_by_date: Dict[str, int]
    period_start: date
    period_end: date


# Sales analytics schemas
class SalesAnalyticsQuery(BaseModel):
    """Sales analytics query parameters."""
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    period: AnalyticsPeriod = Field(default=AnalyticsPeriod.DAILY)
    category_ids: Optional[List[str]] = None
    payment_methods: Optional[List[str]] = None
    regions: Optional[List[str]] = None


class SalesMetrics(BaseModel):
    """Sales metrics data."""
    total_revenue: Decimal
    total_orders: int
    average_order_value: Decimal
    total_items_sold: int
    conversion_rate: float
    refund_rate: float
    tax_collected: Decimal
    shipping_revenue: Decimal


class SalesByPeriod(BaseModel):
    """Sales data by time period."""
    period: str  # Date string
    revenue: Decimal
    orders: int
    average_order_value: Decimal
    items_sold: int


class SalesAnalyticsResponse(BaseModel):
    """Sales analytics response."""
    metrics: SalesMetrics
    sales_by_period: List[SalesByPeriod]
    sales_by_category: Dict[str, Decimal]
    sales_by_payment_method: Dict[str, Decimal]
    sales_by_region: Dict[str, Decimal]
    top_selling_products: List[Dict[str, Any]]
    period_start: date
    period_end: date


# Conversion funnel analytics
class ConversionFunnelQuery(BaseModel):
    """Conversion funnel query parameters."""
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    source: Optional[str] = None
    medium: Optional[str] = None
    device_type: Optional[str] = None


class FunnelStep(BaseModel):
    """Conversion funnel step data."""
    step_name: str
    users: int
    conversion_rate: float
    drop_off_rate: float


class ConversionFunnelResponse(BaseModel):
    """Conversion funnel response."""
    steps: List[FunnelStep]
    overall_conversion_rate: float
    total_sessions: int
    converted_sessions: int
    average_time_to_conversion: int  # seconds
    conversion_by_source: Dict[str, float]
    period_start: date
    period_end: date


# Cart abandonment analytics
class CartAbandonmentQuery(BaseModel):
    """Cart abandonment query parameters."""
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    abandonment_stage: Optional[str] = None


class CartAbandonmentMetrics(BaseModel):
    """Cart abandonment metrics."""
    total_carts_created: int
    abandoned_carts: int
    abandonment_rate: float
    recovered_carts: int
    recovery_rate: float
    average_abandoned_value: Decimal
    total_potential_revenue: Decimal
    recovered_revenue: Decimal


class AbandonmentByStage(BaseModel):
    """Abandonment breakdown by stage."""
    stage: str
    abandoned_count: int
    abandonment_rate: float
    recovery_rate: float


class CartAbandonmentResponse(BaseModel):
    """Cart abandonment response."""
    metrics: CartAbandonmentMetrics
    abandonment_by_stage: List[AbandonmentByStage]
    abandonment_by_day: Dict[str, int]
    recovery_campaigns_performance: Dict[str, Any]
    period_start: date
    period_end: date


# Revenue analytics
class RevenueAnalyticsQuery(BaseModel):
    """Revenue analytics query parameters."""
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    period: AnalyticsPeriod = Field(default=AnalyticsPeriod.DAILY)
    currency: str = Field(default="XAF")


class RevenueMetrics(BaseModel):
    """Revenue metrics data."""
    gross_revenue: Decimal
    net_revenue: Decimal
    tax_revenue: Decimal
    shipping_revenue: Decimal
    refunded_amount: Decimal
    discount_amount: Decimal
    average_revenue_per_user: Decimal
    revenue_growth_rate: float


class RevenueBySource(BaseModel):
    """Revenue breakdown by source."""
    source: str
    revenue: Decimal
    percentage: float
    orders: int
    average_order_value: Decimal


class RevenueAnalyticsResponse(BaseModel):
    """Revenue analytics response."""
    metrics: RevenueMetrics
    revenue_by_period: List[Dict[str, Any]]
    revenue_by_source: List[RevenueBySource]
    revenue_by_product_category: Dict[str, Decimal]
    revenue_forecast: Optional[Dict[str, Any]]
    period_start: date
    period_end: date


# Dashboard overview
class DashboardOverviewQuery(BaseModel):
    """Dashboard overview query parameters."""
    period: AnalyticsPeriod = Field(default=AnalyticsPeriod.DAILY)
    compare_previous: bool = Field(default=True)


class KPIMetric(BaseModel):
    """Key Performance Indicator metric."""
    name: str
    value: Union[int, float, Decimal, str]
    formatted_value: str
    change_percentage: Optional[float] = None
    trend: Optional[str] = None  # up, down, stable
    target: Optional[Union[int, float, Decimal]] = None


class DashboardOverview(BaseModel):
    """Dashboard overview data."""
    kpis: List[KPIMetric]
    recent_orders: List[Dict[str, Any]]
    top_products: List[Dict[str, Any]]
    traffic_sources: Dict[str, int]
    alerts: List[Dict[str, Any]]
    quick_stats: Dict[str, Any]
    period_start: date
    period_end: date


# Custom reports
class CustomReportQuery(BaseModel):
    """Custom report query parameters."""
    report_name: str
    metrics: List[str]
    dimensions: List[str]
    filters: Dict[str, Any] = Field(default_factory=dict)
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    period: AnalyticsPeriod = Field(default=AnalyticsPeriod.DAILY)
    limit: int = Field(default=100, ge=1, le=10000)
    format: str = Field(default="json", pattern=r"^(json|csv|xlsx)$")


class CustomReportResponse(BaseModel):
    """Custom report response."""
    report_name: str
    data: List[Dict[str, Any]]
    summary: Dict[str, Any]
    metadata: Dict[str, Any]
    generated_at: datetime


# A/B Test analytics
class ABTestAnalyticsQuery(BaseModel):
    """A/B test analytics query parameters."""
    test_id: Optional[str] = None
    status: Optional[str] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None


class ABTestVariantPerformance(BaseModel):
    """A/B test variant performance."""
    variant_name: str
    participants: int
    conversions: int
    conversion_rate: float
    revenue: Decimal
    statistical_significance: Optional[float]
    confidence_interval: Optional[tuple[float, float]]


class ABTestAnalyticsResponse(BaseModel):
    """A/B test analytics response."""
    test_id: str
    test_name: str
    status: str
    variants: List[ABTestVariantPerformance]
    winner: Optional[str]
    improvement: Optional[float]
    statistical_significance: Optional[float]
    period_start: date
    period_end: date


# Real-time analytics
class RealTimeMetrics(BaseModel):
    """Real-time metrics data."""
    active_users: int
    current_orders: int
    today_revenue: Decimal
    today_orders: int
    conversion_rate_today: float
    top_pages: List[Dict[str, Any]]
    recent_conversions: List[Dict[str, Any]]
    system_health: Dict[str, Any]
    last_updated: datetime


# Export schemas
class AnalyticsExportRequest(BaseModel):
    """Analytics export request."""
    report_type: str
    format: str = Field(default="csv", pattern=r"^(csv|xlsx|json|pdf)$")
    query_params: Dict[str, Any]
    email_delivery: bool = Field(default=False)
    recipient_email: Optional[str] = None


class AnalyticsExportResponse(BaseModel):
    """Analytics export response."""
    export_id: str
    download_url: Optional[str]
    status: str  # processing, completed, failed
    file_size: Optional[int]
    expires_at: Optional[datetime]
    created_at: datetime
