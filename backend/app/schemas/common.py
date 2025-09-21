"""
Common schemas for PromoWeb Africa.
Reusable Pydantic models for common responses and data structures.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any, Generic, TypeVar
from pydantic import BaseModel, Field, validator
from pydantic.generics import GenericModel
from decimal import Decimal


# Generic type for paginated responses
T = TypeVar('T')


# Base response schemas
class BaseResponse(BaseModel):
    """Base response schema."""
    success: bool = True
    message: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ErrorResponse(BaseResponse):
    """Error response schema."""
    success: bool = False
    error_code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class ValidationErrorDetail(BaseModel):
    """Validation error detail."""
    field: str
    message: str
    invalid_value: Any


class ValidationErrorResponse(ErrorResponse):
    """Validation error response."""
    error_code: str = "VALIDATION_ERROR"
    validation_errors: List[ValidationErrorDetail] = []


# Pagination schemas
class PaginationParams(BaseModel):
    """Pagination parameters."""
    page: int = Field(default=1, ge=1, description="Page number")
    per_page: int = Field(default=20, ge=1, le=100, description="Items per page")
    
    @property
    def offset(self) -> int:
        """Calculate offset for database queries."""
        return (self.page - 1) * self.per_page


class PaginationInfo(BaseModel):
    """Pagination information."""
    page: int
    per_page: int
    total: int
    pages: int
    has_next: bool
    has_prev: bool
    
    @classmethod
    def create(cls, page: int, per_page: int, total: int) -> "PaginationInfo":
        """Create pagination info from parameters."""
        pages = (total + per_page - 1) // per_page  # Ceiling division
        return cls(
            page=page,
            per_page=per_page,
            total=total,
            pages=pages,
            has_next=page < pages,
            has_prev=page > 1
        )


class PaginatedResponse(GenericModel, Generic[T]):
    """Generic paginated response."""
    items: List[T]
    pagination: PaginationInfo
    
    @classmethod
    def create(
        cls, 
        items: List[T], 
        page: int, 
        per_page: int, 
        total: int
    ) -> "PaginatedResponse[T]":
        """Create paginated response."""
        pagination = PaginationInfo.create(page, per_page, total)
        return cls(items=items, pagination=pagination)


# Search and filter schemas
class SortOrder(BaseModel):
    """Sort order specification."""
    field: str
    direction: str = Field(default="asc", regex=r"^(asc|desc)$")


class FilterCondition(BaseModel):
    """Filter condition."""
    field: str
    operator: str = Field(..., regex=r"^(eq|ne|gt|ge|lt|le|in|nin|like|ilike)$")
    value: Any


class SearchParams(BaseModel):
    """Search parameters."""
    q: Optional[str] = Field(None, description="Search query")
    filters: List[FilterCondition] = Field(default_factory=list)
    sort: List[SortOrder] = Field(default_factory=list)
    pagination: PaginationParams = Field(default_factory=PaginationParams)


class SearchResponse(GenericModel, Generic[T]):
    """Generic search response."""
    results: PaginatedResponse[T]
    facets: Dict[str, List[Dict[str, Any]]] = Field(default_factory=dict)
    suggestions: List[str] = Field(default_factory=list)
    total_results: int
    search_time_ms: int


# File upload schemas
class FileUploadResponse(BaseModel):
    """File upload response."""
    filename: str
    original_filename: str
    size: int
    mime_type: str
    url: str
    upload_id: str
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)


class ImageUploadResponse(FileUploadResponse):
    """Image upload response with additional metadata."""
    width: Optional[int] = None
    height: Optional[int] = None
    thumbnail_url: Optional[str] = None


# Address schemas (reusable)
class AddressBase(BaseModel):
    """Base address schema."""
    street_address: str = Field(..., min_length=1)
    city: str = Field(..., min_length=1, max_length=100)
    region: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=10)
    country: str = Field(default="CM", max_length=2)


class CoordinatesBase(BaseModel):
    """Base coordinates schema."""
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)


class AddressWithCoordinates(AddressBase, CoordinatesBase):
    """Address with GPS coordinates."""
    pass


# Money and pricing schemas
class MoneyAmount(BaseModel):
    """Money amount with currency."""
    amount: Decimal = Field(..., ge=0)
    currency: str = Field(default="XAF", max_length=3)
    
    @property
    def formatted(self) -> str:
        """Get formatted amount with currency."""
        if self.currency == "XAF":
            return f"{self.amount:,.0f} XAF"
        elif self.currency == "EUR":
            return f"€{self.amount:.2f}"
        else:
            return f"{self.amount} {self.currency}"


class PriceRange(BaseModel):
    """Price range filter."""
    min_price: Optional[Decimal] = Field(None, ge=0)
    max_price: Optional[Decimal] = Field(None, ge=0)
    currency: str = Field(default="XAF", max_length=3)
    
    @validator('max_price')
    def validate_price_range(cls, v, values):
        if v is not None and 'min_price' in values and values['min_price'] is not None:
            if v < values['min_price']:
                raise ValueError('max_price must be greater than min_price')
        return v


# Date range schemas
class DateRange(BaseModel):
    """Date range filter."""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    
    @validator('end_date')
    def validate_date_range(cls, v, values):
        if v is not None and 'start_date' in values and values['start_date'] is not None:
            if v <= values['start_date']:
                raise ValueError('end_date must be after start_date')
        return v


# Status schemas
class StatusResponse(BaseModel):
    """Generic status response."""
    status: str
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


class HealthCheckResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    timestamp: datetime
    services: Dict[str, Dict[str, Any]]
    environment: str


# Bulk operation schemas
class BulkOperationRequest(BaseModel):
    """Bulk operation request."""
    operation: str
    item_ids: List[str] = Field(..., min_items=1)
    parameters: Dict[str, Any] = Field(default_factory=dict)


class BulkOperationResult(BaseModel):
    """Bulk operation result."""
    operation: str
    total_items: int
    successful_items: int
    failed_items: int
    errors: List[Dict[str, Any]] = Field(default_factory=list)
    results: List[Dict[str, Any]] = Field(default_factory=list)


# Notification schemas
class NotificationBase(BaseModel):
    """Base notification schema."""
    type: str  # email, sms, push, in_app
    recipient: str
    subject: Optional[str] = None
    message: str
    data: Dict[str, Any] = Field(default_factory=dict)


class NotificationResponse(NotificationBase):
    """Notification response."""
    id: str
    status: str  # pending, sent, delivered, failed
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    error_message: Optional[str] = None
    created_at: datetime


# Cache schemas
class CacheInfo(BaseModel):
    """Cache information."""
    key: str
    exists: bool
    ttl: Optional[int] = None  # Time to live in seconds
    size: Optional[int] = None  # Size in bytes


class CacheStats(BaseModel):
    """Cache statistics."""
    total_keys: int
    memory_usage: int  # Bytes
    hit_rate: float
    miss_rate: float
    operations_per_second: float


# Rate limiting schemas
class RateLimitInfo(BaseModel):
    """Rate limit information."""
    limit: int
    remaining: int
    reset_time: datetime
    retry_after: Optional[int] = None  # Seconds


# Webhook schemas
class WebhookEventBase(BaseModel):
    """Base webhook event schema."""
    event_type: str
    event_id: str
    timestamp: datetime
    data: Dict[str, Any]


class WebhookDelivery(BaseModel):
    """Webhook delivery information."""
    id: str
    webhook_url: str
    event: WebhookEventBase
    status: str  # pending, delivered, failed, retrying
    attempts: int
    last_attempt_at: Optional[datetime] = None
    next_retry_at: Optional[datetime] = None
    response_code: Optional[int] = None
    response_body: Optional[str] = None
    created_at: datetime


# System configuration schemas
class ConfigurationItem(BaseModel):
    """System configuration item."""
    key: str
    value: str
    description: Optional[str] = None
    is_secret: bool = False
    updated_at: datetime


class SystemInfo(BaseModel):
    """System information."""
    application: str
    version: str
    environment: str
    build_time: datetime
    uptime_seconds: int
    database_status: str
    redis_status: str
    dependencies: Dict[str, str]


# Statistics schemas
class StatisticValue(BaseModel):
    """Single statistic value."""
    name: str
    value: Any
    formatted_value: str
    unit: Optional[str] = None
    change_from_previous: Optional[float] = None
    trend: Optional[str] = None  # up, down, stable


class StatisticsGroup(BaseModel):
    """Group of related statistics."""
    group_name: str
    statistics: List[StatisticValue]
    period: Optional[str] = None
    last_updated: datetime


# Export/Import schemas
class ExportRequest(BaseModel):
    """Data export request."""
    format: str = Field(..., regex=r"^(csv|xlsx|json|pdf)$")
    filters: Dict[str, Any] = Field(default_factory=dict)
    fields: Optional[List[str]] = None
    email_delivery: bool = False
    recipient_email: Optional[str] = None


class ExportStatus(BaseModel):
    """Export status."""
    export_id: str
    status: str  # pending, processing, completed, failed
    progress: int = Field(ge=0, le=100)  # Percentage
    file_url: Optional[str] = None
    file_size: Optional[int] = None
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None


class ImportRequest(BaseModel):
    """Data import request."""
    file_url: str
    format: str = Field(..., regex=r"^(csv|xlsx|json)$")
    mapping: Dict[str, str] = Field(default_factory=dict)  # field mapping
    options: Dict[str, Any] = Field(default_factory=dict)
    validate_only: bool = False


class ImportResult(BaseModel):
    """Import result."""
    import_id: str
    status: str  # pending, processing, completed, failed
    total_records: int
    processed_records: int
    successful_records: int
    failed_records: int
    errors: List[Dict[str, Any]] = Field(default_factory=list)
    warnings: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: datetime
    completed_at: Optional[datetime] = None
