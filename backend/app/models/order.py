"""
Order and OrderItem models for PromoWeb Africa.
Handles order management, status tracking, and partial payments.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from decimal import Decimal
from enum import Enum
from sqlalchemy import (
    Column, String, Boolean, DateTime, ForeignKey, Integer, 
    Numeric, Text, Index, event
)
from sqlalchemy.dialects.postgresql import UUID, ENUM
from sqlalchemy.orm import relationship, validates
from sqlalchemy.sql import func
from geoalchemy2 import Geometry
import uuid

from app.core.database import Base


# Order status enum
order_status_enum = ENUM(
    'pending', 'partially_paid', 'processing', 'shipped', 'in_transit',
    'delivered', 'delivery_failed', 'paid_full', 'completed', 
    'cancelled', 'returned', 'refunded',
    name='order_status',
    create_type=False
)


class Order(Base):
    """Order model with partial payment support and geolocation."""
    
    __tablename__ = "orders"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Order identification
    order_number = Column(String(50), unique=True, nullable=False, index=True)
    
    # Foreign key
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Order status
    status = Column(order_status_enum, default='pending', nullable=False, index=True)
    
    # Financial information
    total_amount = Column(Numeric(12, 2), nullable=False)
    deposit_amount = Column(Numeric(12, 2), nullable=False)  # 30% acompte
    remaining_amount = Column(Numeric(12, 2), nullable=False)
    shipping_cost = Column(Numeric(10, 2), default=0.00, nullable=False)
    tax_amount = Column(Numeric(10, 2), default=0.00, nullable=False)
    discount_amount = Column(Numeric(10, 2), default=0.00, nullable=False)
    
    # Billing address
    billing_name = Column(String(200), nullable=True)
    billing_email = Column(String(255), nullable=True)
    billing_phone = Column(String(20), nullable=True)
    billing_address = Column(Text, nullable=True)
    billing_city = Column(String(100), nullable=True)
    billing_region = Column(String(100), nullable=True)
    billing_postal_code = Column(String(10), nullable=True)
    billing_country = Column(String(2), default='CM', nullable=True)
    
    # Shipping address
    shipping_name = Column(String(200), nullable=True)
    shipping_address = Column(Text, nullable=True)
    shipping_city = Column(String(100), nullable=True)
    shipping_region = Column(String(100), nullable=True)
    shipping_postal_code = Column(String(10), nullable=True)
    shipping_country = Column(String(2), default='CM', nullable=True)
    shipping_location = Column(Geometry('POINT', srid=4326), nullable=True)  # PostGIS
    
    # Address references (if using saved addresses)
    billing_address_id = Column(UUID(as_uuid=True), ForeignKey("user_addresses.id"), nullable=True)
    shipping_address_id = Column(UUID(as_uuid=True), ForeignKey("user_addresses.id"), nullable=True)
    
    # Order metadata
    notes = Column(Text, nullable=True)  # Customer notes
    admin_notes = Column(Text, nullable=True)  # Internal notes
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    cancelled_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="order")
    shipping = relationship("Shipping", back_populates="order", uselist=False)
    status_history = relationship("OrderStatusHistory", back_populates="order")
    billing_address_ref = relationship("UserAddress", foreign_keys=[billing_address_id])
    shipping_address_ref = relationship("UserAddress", foreign_keys=[shipping_address_id])
    
    # Indexes
    __table_args__ = (
        Index('idx_order_user_status', 'user_id', 'status'),
        Index('idx_order_created_at', 'created_at'),
        Index('idx_order_shipping_location', 'shipping_location', postgresql_using='gist'),
    )
    
    def __repr__(self):
        return f"<Order(id={self.id}, number='{self.order_number}', status='{self.status}')>"
    
    @validates('deposit_amount', 'remaining_amount', 'total_amount')
    def validate_amounts(self, key, value):
        """Validate that amounts are positive."""
        if value is not None and value < 0:
            raise ValueError(f"{key} must be positive")
        return value
    
    @property
    def is_paid_in_full(self) -> bool:
        """Check if order is fully paid."""
        return self.status in ['paid_full', 'completed']
    
    @property
    def is_partially_paid(self) -> bool:
        """Check if order has partial payment."""
        return self.status == 'partially_paid'
    
    @property
    def can_be_cancelled(self) -> bool:
        """Check if order can be cancelled."""
        return self.status in ['pending', 'partially_paid', 'processing']
    
    @property
    def can_be_shipped(self) -> bool:
        """Check if order can be shipped."""
        return self.status in ['partially_paid', 'processing']
    
    @property
    def is_delivered(self) -> bool:
        """Check if order is delivered."""
        return self.status == 'delivered'
    
    @property
    def payment_progress(self) -> float:
        """Get payment progress as percentage."""
        if self.total_amount == 0:
            return 0.0
        
        paid_amount = sum(p.amount for p in self.payments if p.status == 'success')
        return float(paid_amount / self.total_amount * 100)
    
    @property
    def shipping_address_full(self) -> str:
        """Get formatted shipping address."""
        parts = []
        if self.shipping_address:
            parts.append(self.shipping_address)
        if self.shipping_city:
            parts.append(self.shipping_city)
        if self.shipping_region:
            parts.append(self.shipping_region)
        if self.shipping_postal_code:
            parts.append(self.shipping_postal_code)
        if self.shipping_country:
            parts.append(self.shipping_country)
        return ", ".join(parts)
    
    @property
    def billing_address_full(self) -> str:
        """Get formatted billing address."""
        parts = []
        if self.billing_address:
            parts.append(self.billing_address)
        if self.billing_city:
            parts.append(self.billing_city)
        if self.billing_region:
            parts.append(self.billing_region)
        if self.billing_postal_code:
            parts.append(self.billing_postal_code)
        if self.billing_country:
            parts.append(self.billing_country)
        return ", ".join(parts)
    
    def calculate_totals(self) -> Dict[str, Decimal]:
        """Calculate order totals from items."""
        subtotal = Decimal('0')
        total_weight = Decimal('0')
        
        for item in self.items:
            subtotal += item.total_price
            if item.product and item.product.weight_kg:
                total_weight += item.product.weight_kg * item.quantity
        
        # Calculate shipping based on weight and location
        shipping_cost = self._calculate_shipping_cost(total_weight)
        
        # Calculate taxes
        tax_amount = self._calculate_taxes(subtotal)
        
        total = subtotal + shipping_cost + tax_amount - self.discount_amount
        
        return {
            'subtotal': subtotal,
            'shipping_cost': shipping_cost,
            'tax_amount': tax_amount,
            'discount_amount': self.discount_amount,
            'total': total,
            'total_weight': total_weight,
        }
    
    def _calculate_shipping_cost(self, total_weight: Decimal) -> Decimal:
        """Calculate shipping cost based on weight and location."""
        from app.core.config import get_settings
        settings = get_settings()
        
        base_cost = Decimal(str(settings.DEFAULT_SHIPPING_COST))
        weight_cost = total_weight * Decimal(str(settings.WEIGHT_RATE_PER_KG))
        
        # TODO: Add location-based shipping zones calculation using PostGIS
        
        return base_cost + weight_cost
    
    def _calculate_taxes(self, taxable_amount: Decimal) -> Decimal:
        """Calculate taxes."""
        tax_rate = Decimal('0.1925')  # 19.25% VAT for Cameroon
        return taxable_amount * tax_rate
    
    def calculate_deposit(self, percentage: int = 30) -> Decimal:
        """Calculate deposit amount."""
        return (self.total_amount * percentage) / 100
    
    def update_amounts(self) -> None:
        """Update order amounts based on items."""
        totals = self.calculate_totals()
        
        self.total_amount = totals['total']
        self.shipping_cost = totals['shipping_cost']
        self.tax_amount = totals['tax_amount']
        
        # Recalculate deposit and remaining amounts
        from app.core.config import get_settings
        settings = get_settings()
        deposit_percentage = settings.DEFAULT_DEPOSIT_PERCENTAGE
        
        self.deposit_amount = self.calculate_deposit(deposit_percentage)
        self.remaining_amount = self.total_amount - self.deposit_amount
    
    def change_status(self, new_status: str, notes: str = None, changed_by_id: str = None) -> None:
        """Change order status and log the change."""
        old_status = self.status
        self.status = new_status
        self.updated_at = datetime.utcnow()
        
        # Special handling for certain status changes
        if new_status == 'delivered':
            self.delivered_at = datetime.utcnow()
        elif new_status == 'cancelled':
            self.cancelled_at = datetime.utcnow()
        
        # Create status history entry
        history = OrderStatusHistory(
            order_id=self.id,
            previous_status=old_status,
            new_status=new_status,
            notes=notes,
            changed_by_id=changed_by_id
        )
        self.status_history.append(history)
    
    def get_total_paid(self) -> Decimal:
        """Get total amount paid for this order."""
        return sum(p.amount for p in self.payments if p.status == 'success')
    
    def get_remaining_balance(self) -> Decimal:
        """Get remaining balance to be paid."""
        return self.total_amount - self.get_total_paid()
    
    def can_fulfill(self) -> bool:
        """Check if order can be fulfilled (all items in stock)."""
        for item in self.items:
            if not item.product or not item.product.is_in_stock:
                return False
            if item.product.stock_quantity < item.quantity:
                return False
        return True
    
    def reserve_inventory(self) -> bool:
        """Reserve inventory for all order items."""
        for item in self.items:
            if item.product and item.product.inventory:
                if not item.product.inventory.reserve(item.quantity):
                    # Rollback reservations if any item fails
                    self._release_inventory_reservations()
                    return False
        return True
    
    def _release_inventory_reservations(self) -> None:
        """Release inventory reservations for all items."""
        for item in self.items:
            if item.product and item.product.inventory:
                item.product.inventory.release_reservation(item.quantity)
    
    def fulfill_inventory(self) -> bool:
        """Fulfill inventory (reduce stock) for all order items."""
        for item in self.items:
            if item.product and item.product.inventory:
                # Release reservation and reduce stock
                item.product.inventory.release_reservation(item.quantity)
                if not item.product.inventory.reduce_stock(item.quantity):
                    return False
        return True


class OrderItem(Base):
    """Individual items within an order."""
    
    __tablename__ = "order_items"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign keys
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    
    # Item details
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)  # Price at time of order
    total_price = Column(Numeric(10, 2), nullable=False)
    
    # Product snapshot (in case product is deleted/modified)
    product_snapshot = Column(Text, nullable=True)  # JSON string
    
    # Relationships
    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")
    
    def __repr__(self):
        return f"<OrderItem(id={self.id}, order_id={self.order_id}, quantity={self.quantity})>"
    
    @validates('quantity')
    def validate_quantity(self, key, value):
        """Validate quantity is positive."""
        if value <= 0:
            raise ValueError("Quantity must be positive")
        return value
    
    @property
    def calculated_total(self) -> Decimal:
        """Calculate total price from unit price and quantity."""
        return self.unit_price * self.quantity
    
    def create_product_snapshot(self) -> None:
        """Create a snapshot of product data at time of order."""
        if self.product:
            import json
            snapshot = {
                'id': str(self.product.id),
                'title': self.product.title,
                'description': self.product.description,
                'sku': self.product.sku,
                'brand': self.product.brand,
                'weight_kg': float(self.product.weight_kg) if self.product.weight_kg else None,
                'images': self.product.images,
                'category': self.product.category.name if self.product.category else None,
            }
            self.product_snapshot = json.dumps(snapshot)
    
    def get_product_snapshot(self) -> Optional[Dict]:
        """Get product snapshot as dictionary."""
        if self.product_snapshot:
            import json
            return json.loads(self.product_snapshot)
        return None


class OrderStatusHistory(Base):
    """History of order status changes."""
    
    __tablename__ = "order_status_history"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign keys
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    changed_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Status change
    previous_status = Column(order_status_enum, nullable=True)
    new_status = Column(order_status_enum, nullable=False)
    
    # Additional information
    notes = Column(Text, nullable=True)
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    order = relationship("Order", back_populates="status_history")
    changed_by = relationship("User")
    
    def __repr__(self):
        return f"<OrderStatusHistory(order_id={self.order_id}, {self.previous_status}->{self.new_status})>"


# Event listeners for automatic actions
@event.listens_for(Order.status, 'set')
def order_status_changed(target, value, oldvalue, initiator):
    """Handle automatic actions when order status changes."""
    if oldvalue != value:
        # Update timestamp
        target.updated_at = datetime.utcnow()
        
        # Handle inventory reservations/fulfillment
        if value == 'partially_paid' and oldvalue == 'pending':
            # Reserve inventory when deposit is paid
            target.reserve_inventory()
        elif value == 'shipped' and oldvalue in ['partially_paid', 'processing']:
            # Fulfill inventory when shipped
            target.fulfill_inventory()
        elif value == 'cancelled':
            # Release inventory reservations
            target._release_inventory_reservations()


@event.listens_for(OrderItem, 'before_insert')
def create_order_item_snapshot(mapper, connection, target):
    """Create product snapshot when order item is created."""
    target.create_product_snapshot()
    
    # Ensure total price is calculated
    if target.total_price is None:
        target.total_price = target.calculated_total
