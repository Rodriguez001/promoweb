"""
Promotion schemas for PromoWeb Africa.
Pydantic models for promotions and discounts validation.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from decimal import Decimal
from enum import Enum


# Enums
class PromotionType(str, Enum):
    """Promotion type options."""
    PERCENTAGE = "percentage"
    FIXED_AMOUNT = "fixed_amount"
    FREE_SHIPPING = "free_shipping"
    BUY_ONE_GET_ONE = "buy_one_get_one"


# Promotion schemas
class PromotionBase(BaseModel):
    """Base promotion schema."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    code: Optional[str] = Field(None, min_length=3, max_length=50, regex=r"^[A-Z0-9_-]+$")
    type: PromotionType
    discount_value: Decimal = Field(..., ge=0)
    min_order_amount: Optional[Decimal] = Field(None, ge=0)
    max_discount_amount: Optional[Decimal] = Field(None, ge=0)
    min_quantity: Optional[int] = Field(None, ge=1)
    usage_limit: Optional[int] = Field(None, ge=1)
    usage_limit_per_user: Optional[int] = Field(None, ge=1)
    first_time_customers_only: bool = Field(default=False)
    user_group_ids: List[str] = Field(default_factory=list)
    allowed_regions: List[str] = Field(default_factory=list)
    excluded_regions: List[str] = Field(default_factory=list)
    start_date: datetime
    end_date: datetime
    is_active: bool = Field(default=True)
    is_stackable: bool = Field(default=False)
    priority: int = Field(default=0)
    
    @validator('discount_value')
    def validate_discount_value(cls, v, values):
        if 'type' in values and values['type'] == PromotionType.PERCENTAGE and v > 100:
            raise ValueError('Percentage discount cannot exceed 100%')
        return v
    
    @validator('end_date')
    def validate_date_range(cls, v, values):
        if 'start_date' in values and v <= values['start_date']:
            raise ValueError('End date must be after start date')
        return v


class PromotionCreate(PromotionBase):
    """Schema for creating promotion."""
    product_ids: List[str] = Field(default_factory=list)
    category_ids: List[str] = Field(default_factory=list)


class PromotionUpdate(BaseModel):
    """Schema for updating promotion."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    discount_value: Optional[Decimal] = Field(None, ge=0)
    min_order_amount: Optional[Decimal] = Field(None, ge=0)
    max_discount_amount: Optional[Decimal] = Field(None, ge=0)
    min_quantity: Optional[int] = Field(None, ge=1)
    usage_limit: Optional[int] = Field(None, ge=1)
    usage_limit_per_user: Optional[int] = Field(None, ge=1)
    first_time_customers_only: Optional[bool] = None
    user_group_ids: Optional[List[str]] = None
    allowed_regions: Optional[List[str]] = None
    excluded_regions: Optional[List[str]] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    is_active: Optional[bool] = None
    is_stackable: Optional[bool] = None
    priority: Optional[int] = None
    product_ids: Optional[List[str]] = None
    category_ids: Optional[List[str]] = None


class PromotionResponse(PromotionBase):
    """Schema for promotion response."""
    id: str
    used_count: int
    is_valid_now: bool
    is_code_based: bool
    usage_percentage: float
    discount_display: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class PromotionDetail(PromotionResponse):
    """Detailed promotion information."""
    products: List[Dict[str, Any]] = []
    categories: List[Dict[str, Any]] = []
    usage_history: List["PromotionUsageResponse"] = []


# Promotion usage schemas
class PromotionUsageResponse(BaseModel):
    """Promotion usage response."""
    id: str
    promotion_id: str
    user_id: Optional[str]
    order_id: Optional[str]
    discount_amount: Optional[Decimal]
    original_amount: Optional[Decimal]
    user_name: Optional[str]
    order_number: Optional[str]
    used_at: datetime
    
    class Config:
        from_attributes = True


# Flash sale schemas
class FlashSaleBase(BaseModel):
    """Base flash sale schema."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    start_time: datetime
    end_time: datetime
    banner_image_url: Optional[str] = None
    countdown_text: Optional[str] = Field(None, max_length=100)
    is_active: bool = Field(default=True)
    
    @validator('end_time')
    def validate_time_range(cls, v, values):
        if 'start_time' in values and v <= values['start_time']:
            raise ValueError('End time must be after start time')
        return v


class FlashSaleCreate(FlashSaleBase):
    """Schema for creating flash sale."""
    items: List["FlashSaleItemCreate"] = Field(..., min_items=1)


class FlashSaleUpdate(BaseModel):
    """Schema for updating flash sale."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    banner_image_url: Optional[str] = None
    countdown_text: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None


class FlashSaleResponse(FlashSaleBase):
    """Schema for flash sale response."""
    id: str
    is_active_now: bool
    time_remaining: Optional[int]  # seconds
    has_started: bool
    has_ended: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class FlashSaleDetail(FlashSaleResponse):
    """Detailed flash sale with items."""
    items: List["FlashSaleItemResponse"] = []


# Flash sale item schemas
class FlashSaleItemBase(BaseModel):
    """Base flash sale item schema."""
    product_id: str
    original_price: Decimal = Field(..., gt=0)
    sale_price: Decimal = Field(..., gt=0)
    available_quantity: Optional[int] = Field(None, gt=0)
    sort_order: int = Field(default=0)
    is_featured: bool = Field(default=False)
    
    @validator('sale_price')
    def validate_sale_price(cls, v, values):
        if 'original_price' in values and v >= values['original_price']:
            raise ValueError('Sale price must be lower than original price')
        return v


class FlashSaleItemCreate(FlashSaleItemBase):
    """Schema for creating flash sale item."""
    pass


class FlashSaleItemUpdate(BaseModel):
    """Schema for updating flash sale item."""
    original_price: Optional[Decimal] = Field(None, gt=0)
    sale_price: Optional[Decimal] = Field(None, gt=0)
    available_quantity: Optional[int] = Field(None, gt=0)
    sort_order: Optional[int] = None
    is_featured: Optional[bool] = None


class FlashSaleItemResponse(FlashSaleItemBase):
    """Schema for flash sale item response."""
    id: str
    flash_sale_id: str
    discount_percentage: Decimal
    sold_quantity: int
    savings_amount: Decimal
    is_available: bool
    remaining_quantity: Optional[int]
    sold_percentage: float
    
    # Product info
    product_title: str
    product_image: Optional[str]
    product_brand: Optional[str]
    
    class Config:
        from_attributes = True


# Promotion validation
class PromotionValidationRequest(BaseModel):
    """Request to validate promotion for user/order."""
    promotion_code: Optional[str] = None
    promotion_id: Optional[str] = None
    user_id: str
    order_amount: Decimal
    product_ids: List[str] = Field(default_factory=list)
    user_region: Optional[str] = None


class PromotionValidationResponse(BaseModel):
    """Response for promotion validation."""
    is_valid: bool
    can_use: bool
    reason: Optional[str] = None
    discount_amount: Decimal = Field(default=Decimal('0'))
    promotion: Optional[PromotionResponse] = None


# Promotion analytics
class PromotionAnalytics(BaseModel):
    """Promotion analytics data."""
    promotion_id: str
    promotion_name: str
    total_usage: int
    unique_users: int
    total_discount_given: Decimal
    revenue_generated: Decimal
    conversion_rate: float
    average_order_value: Decimal
    usage_by_date: Dict[str, int]
    top_products: List[Dict[str, Any]]
    period_start: datetime
    period_end: datetime


class PromotionPerformance(BaseModel):
    """Promotion performance comparison."""
    promotions: List[Dict[str, Any]]
    best_performing: Optional[str]
    total_savings_given: Decimal
    total_revenue_impact: Decimal
    roi: float  # Return on investment


# Coupon generation
class CouponGenerationRequest(BaseModel):
    """Request to generate coupon codes."""
    count: int = Field(..., ge=1, le=1000)
    prefix: Optional[str] = Field(None, max_length=10, regex=r"^[A-Z0-9]+$")
    length: int = Field(default=8, ge=4, le=20)
    promotion_template: PromotionCreate


class CouponBatch(BaseModel):
    """Generated coupon batch."""
    batch_id: str
    promotion_id: str
    codes: List[str]
    count: int
    expires_at: datetime
    created_at: datetime


# Discount calculation
class DiscountCalculationRequest(BaseModel):
    """Request for discount calculation."""
    order_amount: Decimal
    product_quantities: Dict[str, int] = Field(default_factory=dict)
    user_id: str
    promotion_codes: List[str] = Field(default_factory=list)
    region: Optional[str] = None


class DiscountCalculationResponse(BaseModel):
    """Response for discount calculation."""
    original_amount: Decimal
    total_discount: Decimal
    final_amount: Decimal
    applied_promotions: List[Dict[str, Any]]
    savings_percentage: float
    breakdown: Dict[str, Decimal]


# Forward references
FlashSaleDetail.model_rebuild()
PromotionDetail.model_rebuild()
