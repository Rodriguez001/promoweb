"""
Product and Category models for PromoWeb Africa.
Handles product catalog, pricing, inventory, and categorization.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from decimal import Decimal
from sqlalchemy import (
    Column, String, Boolean, DateTime, Text, ForeignKey, Integer, 
    Numeric, JSON, Index
)
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship, validates
from sqlalchemy.sql import func
import uuid

from app.core.database import Base


class Category(Base):
    """Product category model with hierarchical structure."""
    
    __tablename__ = "categories"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Category information
    name = Column(String(100), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Hierarchy
    parent_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"), nullable=True)
    
    # Display settings
    image_url = Column(String(500), nullable=True)
    sort_order = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # SEO fields
    meta_title = Column(String(255), nullable=True)
    meta_description = Column(String(500), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    parent = relationship("Category", remote_side=[id], back_populates="children")
    children = relationship("Category", back_populates="parent", cascade="all, delete-orphan")
    products = relationship("Product", back_populates="category")
    
    def __repr__(self):
        return f"<Category(id={self.id}, name='{self.name}', slug='{self.slug}')>"
    
    @property
    def path(self) -> List[str]:
        """Get category path from root to current."""
        path = []
        current = self
        while current:
            path.insert(0, current.name)
            current = current.parent
        return path
    
    @property
    def breadcrumb(self) -> str:
        """Get breadcrumb string."""
        return " > ".join(self.path)
    
    @property
    def level(self) -> int:
        """Get category depth level."""
        level = 0
        current = self.parent
        while current:
            level += 1
            current = current.parent
        return level
    
    def get_all_children(self) -> List["Category"]:
        """Get all descendant categories."""
        children = []
        for child in self.children:
            children.append(child)
            children.extend(child.get_all_children())
        return children
    
    def get_product_count(self, include_children: bool = True) -> int:
        """Get product count in this category."""
        count = len([p for p in self.products if p.is_active])
        
        if include_children:
            for child in self.children:
                count += child.get_product_count(include_children=True)
        
        return count


class Product(Base):
    """Product model with pricing, inventory, and metadata."""
    
    __tablename__ = "products"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Basic information
    title = Column(String(255), nullable=False, index=True)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    short_description = Column(String(500), nullable=True)
    
    # Product identifiers
    isbn = Column(String(20), nullable=True, index=True)
    ean = Column(String(20), nullable=True, index=True)
    sku = Column(String(100), nullable=True, unique=True, index=True)
    brand = Column(String(100), nullable=True, index=True)
    
    # Category
    category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"), nullable=True)
    
    # Pricing (in cents to avoid floating point issues)
    price_eur = Column(Numeric(10, 2), nullable=False)  # Original price in EUR
    price_xaf = Column(Numeric(12, 2), nullable=False)  # Calculated price in XAF
    cost_price_eur = Column(Numeric(10, 2), nullable=True)  # Cost price for margin calculation
    margin_percentage = Column(Numeric(5, 2), default=30.00, nullable=False)
    
    # Physical properties
    weight_kg = Column(Numeric(8, 3), nullable=True)  # Weight in kg
    dimensions_cm = Column(String(50), nullable=True)  # "L x W x H" format
    
    # Media
    images = Column(JSON, default=list, nullable=False)  # Array of image URLs
    
    # Search and categorization
    tags = Column(ARRAY(String(50)), default=list, nullable=False)
    
    # SEO fields
    meta_title = Column(String(255), nullable=True)
    meta_description = Column(String(500), nullable=True)
    
    # Status and visibility
    is_active = Column(Boolean, default=True, nullable=False)
    is_featured = Column(Boolean, default=False, nullable=False)
    is_digital = Column(Boolean, default=False, nullable=False)
    
    # Google Merchant integration
    google_merchant_id = Column(String(100), nullable=True, index=True)
    last_sync_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    category = relationship("Category", back_populates="products")
    inventory = relationship("Inventory", back_populates="product", uselist=False, cascade="all, delete-orphan")
    cart_items = relationship("CartItem", back_populates="product")
    order_items = relationship("OrderItem", back_populates="product")
    product_views = relationship("ProductView", back_populates="product")
    promotions = relationship("Promotion", secondary="product_promotions", back_populates="products")
    reviews = relationship("ProductReview", back_populates="product")
    
    # Indexes
    __table_args__ = (
        Index('idx_products_search', 'title', 'description', postgresql_using='gin'),
        Index('idx_products_price_range', 'price_xaf'),
        Index('idx_products_active_featured', 'is_active', 'is_featured'),
    )
    
    def __repr__(self):
        return f"<Product(id={self.id}, title='{self.title}', price_xaf={self.price_xaf})>"
    
    @validates('price_eur', 'price_xaf')
    def validate_price(self, key, value):
        """Validate that prices are positive."""
        if value is not None and value < 0:
            raise ValueError(f"{key} must be positive")
        return value
    
    @property
    def main_image(self) -> Optional[str]:
        """Get main product image URL."""
        return self.images[0] if self.images else None
    
    @property
    def price_eur_display(self) -> str:
        """Get formatted EUR price for display."""
        return f"€{self.price_eur:.2f}"
    
    @property
    def price_xaf_display(self) -> str:
        """Get formatted XAF price for display."""
        return f"{self.price_xaf:,.0f} XAF"
    
    @property
    def is_in_stock(self) -> bool:
        """Check if product is in stock."""
        return self.inventory and self.inventory.available_quantity > 0
    
    @property
    def stock_quantity(self) -> int:
        """Get available stock quantity."""
        return self.inventory.available_quantity if self.inventory else 0
    
    @property
    def is_low_stock(self) -> bool:
        """Check if product is low in stock."""
        if not self.inventory:
            return False
        return self.inventory.available_quantity <= self.inventory.min_threshold
    
    @property
    def calculated_margin(self) -> Optional[Decimal]:
        """Calculate actual margin if cost price is available."""
        if self.cost_price_eur and self.price_eur:
            return ((self.price_eur - self.cost_price_eur) / self.price_eur) * 100
        return None
    
    def calculate_xaf_price(self, eur_to_xaf_rate: Decimal) -> Decimal:
        """Calculate XAF price from EUR price and exchange rate."""
        base_xaf = self.price_eur * eur_to_xaf_rate
        
        # Add margin
        margin_multiplier = (100 + self.margin_percentage) / 100
        final_price = base_xaf * margin_multiplier
        
        # Round to nearest 100 XAF (configurable)
        from app.core.config import get_settings
        settings = get_settings()
        rounding = settings.PRICE_ROUNDING_THRESHOLD
        
        return Decimal(int(final_price / rounding) * rounding)
    
    def update_xaf_price(self, eur_to_xaf_rate: Decimal) -> None:
        """Update XAF price based on current EUR price and exchange rate."""
        self.price_xaf = self.calculate_xaf_price(eur_to_xaf_rate)
    
    def get_current_price(self) -> Decimal:
        """Get current price considering active promotions."""
        current_price = self.price_xaf
        
        # Apply best available promotion
        best_discount = Decimal('0')
        for promotion in self.promotions:
            if promotion.is_active and promotion.is_valid_now():
                discount = promotion.calculate_discount(current_price)
                if discount > best_discount:
                    best_discount = discount
        
        return current_price - best_discount
    
    def add_view(self, user_id: Optional[str] = None, session_id: Optional[str] = None, 
                 ip_address: Optional[str] = None) -> None:
        """Add a product view for analytics."""
        from app.models.analytics import ProductView
        
        view = ProductView(
            product_id=self.id,
            user_id=user_id,
            session_id=session_id,
            ip_address=ip_address
        )
        
        # This would be added to the session in the actual endpoint
        return view


class Inventory(Base):
    """Inventory management for products."""
    
    __tablename__ = "inventory"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign key
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), 
                        unique=True, nullable=False)
    
    # Inventory quantities
    quantity = Column(Integer, default=0, nullable=False)
    reserved_quantity = Column(Integer, default=0, nullable=False)
    
    # Thresholds
    min_threshold = Column(Integer, default=10, nullable=False)
    max_threshold = Column(Integer, nullable=True)
    
    # Timestamp
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationship
    product = relationship("Product", back_populates="inventory")
    
    def __repr__(self):
        return f"<Inventory(product_id={self.product_id}, quantity={self.quantity}, reserved={self.reserved_quantity})>"
    
    @property
    def available_quantity(self) -> int:
        """Get available quantity (total - reserved)."""
        return max(0, self.quantity - self.reserved_quantity)
    
    @property
    def is_low_stock(self) -> bool:
        """Check if inventory is below minimum threshold."""
        return self.available_quantity <= self.min_threshold
    
    @property
    def is_out_of_stock(self) -> bool:
        """Check if product is out of stock."""
        return self.available_quantity <= 0
    
    def can_reserve(self, quantity: int) -> bool:
        """Check if specified quantity can be reserved."""
        return self.available_quantity >= quantity
    
    def reserve(self, quantity: int) -> bool:
        """Reserve specified quantity."""
        if self.can_reserve(quantity):
            self.reserved_quantity += quantity
            return True
        return False
    
    def release_reservation(self, quantity: int) -> None:
        """Release reserved quantity."""
        self.reserved_quantity = max(0, self.reserved_quantity - quantity)
    
    def reduce_stock(self, quantity: int) -> bool:
        """Reduce actual stock quantity."""
        if self.quantity >= quantity:
            self.quantity -= quantity
            return True
        return False
    
    def add_stock(self, quantity: int) -> None:
        """Add stock quantity."""
        self.quantity += quantity


class ProductReview(Base):
    """Product reviews and ratings."""
    
    __tablename__ = "product_reviews"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign keys
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=True)  # Optional order reference
    
    # Review content
    rating = Column(Integer, nullable=False)  # 1-5 stars
    title = Column(String(255), nullable=True)
    comment = Column(Text, nullable=True)
    
    # Status
    is_verified = Column(Boolean, default=False, nullable=False)  # Verified purchase
    is_approved = Column(Boolean, default=True, nullable=False)  # Moderation
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    product = relationship("Product", back_populates="reviews")
    user = relationship("User")
    order = relationship("Order")
    
    def __repr__(self):
        return f"<ProductReview(id={self.id}, product_id={self.product_id}, rating={self.rating})>"
    
    @validates('rating')
    def validate_rating(self, key, value):
        """Validate rating is between 1 and 5."""
        if value < 1 or value > 5:
            raise ValueError("Rating must be between 1 and 5")
        return value
