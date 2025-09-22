"""
Product and Category schemas for PromoWeb Africa.
Pydantic models for product data validation and serialization.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any, TYPE_CHECKING, ForwardRef
from pydantic import BaseModel, Field, validator, HttpUrl
from decimal import Decimal
from enum import Enum

# Import pour éviter les erreurs de référence circulaire
import app.schemas.promotion


# Enums
class ProductSortBy(str, Enum):
    """Product sorting options."""
    CREATED_AT = "created_at"
    PRICE_ASC = "price_asc"
    PRICE_DESC = "price_desc"
    NAME = "name"
    POPULARITY = "popularity"
    RATING = "rating"


class ProductFilterBy(str, Enum):
    """Product filtering options."""
    CATEGORY = "category"
    BRAND = "brand"
    PRICE_RANGE = "price_range"
    IN_STOCK = "in_stock"
    ON_SALE = "on_sale"


# Category schemas
class CategoryBase(BaseModel):
    """Base category schema."""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    image_url: Optional[HttpUrl] = None
    sort_order: int = Field(default=0)
    is_active: bool = Field(default=True)
    meta_title: Optional[str] = Field(None, max_length=255)
    meta_description: Optional[str] = Field(None, max_length=500)


class CategoryCreate(CategoryBase):
    """Schema for creating category."""
    parent_id: Optional[str] = None


class CategoryUpdate(BaseModel):
    """Schema for updating category."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    image_url: Optional[HttpUrl] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None
    meta_title: Optional[str] = Field(None, max_length=255)
    meta_description: Optional[str] = Field(None, max_length=500)
    parent_id: Optional[str] = None


class CategoryResponse(CategoryBase):
    """Schema for category response."""
    id: str
    slug: str
    parent_id: Optional[str]
    level: int
    path: List[str]
    breadcrumb: str
    product_count: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class CategoryTree(CategoryResponse):
    """Category with children for tree structure."""
    children: List["CategoryTree"] = []


# Product schemas
class ProductBase(BaseModel):
    """Base product schema."""
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    short_description: Optional[str] = Field(None, max_length=500)
    isbn: Optional[str] = Field(None, max_length=20)
    ean: Optional[str] = Field(None, max_length=20)
    sku: Optional[str] = Field(None, max_length=100)
    brand: Optional[str] = Field(None, max_length=100)
    category_id: Optional[str] = None
    price_eur: Decimal = Field(..., gt=0, max_digits=10, decimal_places=2)
    margin_percentage: Decimal = Field(default=Decimal('30.00'), ge=0, le=100, max_digits=5, decimal_places=2)
    weight_kg: Optional[Decimal] = Field(None, gt=0, max_digits=8, decimal_places=3)
    dimensions_cm: Optional[str] = Field(None, max_length=50)
    images: List[HttpUrl] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    meta_title: Optional[str] = Field(None, max_length=255)
    meta_description: Optional[str] = Field(None, max_length=500)
    is_active: bool = Field(default=True)
    is_featured: bool = Field(default=False)
    is_digital: bool = Field(default=False)


class ProductCreate(ProductBase):
    """Schema for creating product."""
    pass


class ProductUpdate(BaseModel):
    """Schema for updating product."""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    short_description: Optional[str] = Field(None, max_length=500)
    isbn: Optional[str] = Field(None, max_length=20)
    ean: Optional[str] = Field(None, max_length=20)
    sku: Optional[str] = Field(None, max_length=100)
    brand: Optional[str] = Field(None, max_length=100)
    category_id: Optional[str] = None
    price_eur: Optional[Decimal] = Field(None, gt=0, max_digits=10, decimal_places=2)
    margin_percentage: Optional[Decimal] = Field(None, ge=0, le=100, max_digits=5, decimal_places=2)
    weight_kg: Optional[Decimal] = Field(None, gt=0, max_digits=8, decimal_places=3)
    dimensions_cm: Optional[str] = Field(None, max_length=50)
    images: Optional[List[HttpUrl]] = None
    tags: Optional[List[str]] = None
    meta_title: Optional[str] = Field(None, max_length=255)
    meta_description: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None
    is_featured: Optional[bool] = None
    is_digital: Optional[bool] = None


class ProductResponse(ProductBase):
    """Schema for product response."""
    id: str
    slug: str
    price_xaf: Decimal
    cost_price_eur: Optional[Decimal]
    calculated_margin: Optional[Decimal]
    main_image: Optional[HttpUrl]
    price_eur_display: str
    price_xaf_display: str
    is_in_stock: bool
    stock_quantity: int
    is_low_stock: bool
    current_price: Decimal  # With promotions applied
    savings_amount: Optional[Decimal]  # If on promotion
    google_merchant_id: Optional[str]
    last_sync_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ProductDetail(ProductResponse):
    """Detailed product information."""
    category: Optional[CategoryResponse]
    inventory: Optional["InventoryResponse"]
    reviews: List["ProductReviewResponse"] = []
    related_products: List[ProductResponse] = []
    average_rating: Optional[float] = None
    review_count: int = 0
    promotions: List["app.schemas.promotion.PromotionResponse"] = []


class ProductListResponse(BaseModel):
    """Paginated product list response."""
    items: List[ProductResponse]
    total: int
    page: int
    per_page: int
    pages: int
    has_next: bool
    has_prev: bool


# Inventory schemas
class InventoryBase(BaseModel):
    """Base inventory schema."""
    quantity: int = Field(..., ge=0)
    min_threshold: int = Field(default=10, ge=0)
    max_threshold: Optional[int] = Field(None, ge=0)


class InventoryUpdate(BaseModel):
    """Schema for updating inventory."""
    quantity: Optional[int] = Field(None, ge=0)
    min_threshold: Optional[int] = Field(None, ge=0)
    max_threshold: Optional[int] = Field(None, ge=0)


class InventoryResponse(InventoryBase):
    """Schema for inventory response."""
    id: str
    product_id: str
    reserved_quantity: int
    available_quantity: int
    is_low_stock: bool
    is_out_of_stock: bool
    last_updated: datetime
    
    class Config:
        from_attributes = True


# Product review schemas
class ProductReviewBase(BaseModel):
    """Base product review schema."""
    rating: int = Field(..., ge=1, le=5)
    title: Optional[str] = Field(None, max_length=255)
    comment: Optional[str] = None


class ProductReviewCreate(ProductReviewBase):
    """Schema for creating product review."""
    product_id: str


class ProductReviewUpdate(BaseModel):
    """Schema for updating product review."""
    rating: Optional[int] = Field(None, ge=1, le=5)
    title: Optional[str] = Field(None, max_length=255)
    comment: Optional[str] = None


class ProductReviewResponse(ProductReviewBase):
    """Schema for product review response."""
    id: str
    product_id: str
    user_id: str
    user_name: str  # Computed field
    is_verified: bool
    is_approved: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Product search schemas
class ProductSearchQuery(BaseModel):
    """Product search query parameters."""
    q: Optional[str] = Field(None, description="Search query")
    category_id: Optional[str] = Field(None, description="Filter by category")
    brand: Optional[str] = Field(None, description="Filter by brand")
    min_price: Optional[Decimal] = Field(None, ge=0, description="Minimum price in XAF")
    max_price: Optional[Decimal] = Field(None, ge=0, description="Maximum price in XAF")
    in_stock: Optional[bool] = Field(None, description="Only show in-stock products")
    on_sale: Optional[bool] = Field(None, description="Only show products on sale")
    is_featured: Optional[bool] = Field(None, description="Only show featured products")
    tags: Optional[List[str]] = Field(None, description="Filter by tags")
    sort_by: ProductSortBy = Field(default=ProductSortBy.CREATED_AT, description="Sort criteria")
    page: int = Field(default=1, ge=1, description="Page number")
    per_page: int = Field(default=20, ge=1, le=100, description="Items per page")
    
    @validator('max_price')
    def validate_price_range(cls, v, values):
        if v is not None and 'min_price' in values and values['min_price'] is not None:
            if v < values['min_price']:
                raise ValueError('max_price must be greater than min_price')
        return v


class ProductSearchResponse(BaseModel):
    """Product search response."""
    products: ProductListResponse
    facets: Dict[str, Any]  # Category counts, brand counts, etc.
    suggestions: List[str] = []  # Search suggestions
    total_results: int
    search_time_ms: int


# Product analytics schemas
class ProductAnalytics(BaseModel):
    """Product analytics data."""
    views_count: int
    views_this_week: int
    views_this_month: int
    cart_additions: int
    purchases: int
    conversion_rate: float
    average_rating: Optional[float]
    review_count: int
    revenue_total: Decimal
    revenue_this_month: Decimal


class ProductPerformance(BaseModel):
    """Product performance metrics."""
    product_id: str
    product_title: str
    views: int
    cart_additions: int
    purchases: int
    revenue: Decimal
    conversion_rate: float
    period_start: datetime
    period_end: datetime


# Bulk operations schemas
class ProductBulkUpdate(BaseModel):
    """Schema for bulk product updates."""
    product_ids: List[str] = Field(..., min_items=1)
    updates: ProductUpdate


class ProductBulkPriceUpdate(BaseModel):
    """Schema for bulk price updates."""
    product_ids: List[str] = Field(..., min_items=1)
    price_adjustment_type: str = Field(..., pattern=r"^(percentage|fixed)$")
    price_adjustment_value: Decimal = Field(..., gt=0)
    
    @validator('price_adjustment_value')
    def validate_adjustment_value(cls, v, values):
        if 'price_adjustment_type' in values:
            if values['price_adjustment_type'] == 'percentage' and v > 100:
                raise ValueError('Percentage adjustment cannot exceed 100%')
        return v


class ProductImport(BaseModel):
    """Schema for product import."""
    products: List[ProductCreate]
    update_existing: bool = Field(default=False)
    create_categories: bool = Field(default=True)


class ProductExport(BaseModel):
    """Schema for product export configuration."""
    format: str = Field(default="csv", pattern=r"^(csv|xlsx|json)$")
    include_inventory: bool = Field(default=True)
    include_reviews: bool = Field(default=False)
    category_ids: Optional[List[str]] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None


# Forward references for circular imports
CategoryTree.model_rebuild()
ProductDetail.model_rebuild()
