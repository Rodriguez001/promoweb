"""
Order service for PromoWeb Africa.
Handles order creation, processing, and state management.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from decimal import Decimal
from dataclasses import dataclass
from enum import Enum
import uuid

from sqlalchemy import select, update, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db_context
from app.models.order import Order, OrderItem, OrderStatusHistory
from app.models.cart import Cart, CartItem
from app.models.product import Product, Inventory
from app.models.user import User, UserAddress
from app.models.shipping import Shipping
from app.services.currency import convert_eur_to_xaf
from app.services.notifications import notification_service

logger = logging.getLogger(__name__)
settings = get_settings()


class OrderStatus(str, Enum):
    """Order status enumeration."""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PAID_PARTIAL = "paid_partial"
    PAID_FULL = "paid_full"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


@dataclass
class OrderSummary:
    """Order summary for creation."""
    subtotal: Decimal
    tax_amount: Decimal
    shipping_cost: Decimal
    discount_amount: Decimal
    total_amount: Decimal
    item_count: int
    total_weight: float


@dataclass
class OrderCreationResult:
    """Result of order creation."""
    success: bool
    order_id: Optional[str] = None
    order_number: Optional[str] = None
    error_message: Optional[str] = None
    order: Optional[Order] = None


class OrderService:
    """Service for handling order operations."""
    
    def __init__(self):
        self.tax_rate = Decimal('0.1925')  # 19.25% VAT in Cameroon
        self.free_shipping_threshold = Decimal('50000')  # Free shipping above 50,000 XAF
        self.base_shipping_cost = Decimal('2500')  # Base shipping cost 2,500 XAF
    
    async def create_order_from_cart(
        self, 
        user_id: str, 
        shipping_address_id: str,
        billing_address_id: Optional[str] = None,
        notes: Optional[str] = None
    ) -> OrderCreationResult:
        """Create order from user's cart."""
        try:
            async with get_db_context() as db:
                # Get user's cart with items
                cart = await db.execute(
                    select(Cart)
                    .where(Cart.user_id == user_id)
                    .options(
                        selectinload(Cart.items).selectinload(CartItem.product).selectinload(Product.inventory)
                    )
                )
                cart = cart.scalar_one_or_none()
                
                if not cart or not cart.items:
                    return OrderCreationResult(
                        success=False,
                        error_message="Cart is empty"
                    )
                
                # Validate cart items availability
                validation_result = await self._validate_cart_items(db, cart.items)
                if not validation_result['valid']:
                    return OrderCreationResult(
                        success=False,
                        error_message=validation_result['error']
                    )
                
                # Get addresses
                shipping_address = await db.get(UserAddress, shipping_address_id)
                if not shipping_address or shipping_address.user_id != user_id:
                    return OrderCreationResult(
                        success=False,
                        error_message="Invalid shipping address"
                    )
                
                billing_address = shipping_address
                if billing_address_id:
                    billing_address = await db.get(UserAddress, billing_address_id)
                    if not billing_address or billing_address.user_id != user_id:
                        return OrderCreationResult(
                            success=False,
                            error_message="Invalid billing address"
                        )
                
                # Calculate order totals
                summary = await self._calculate_order_summary(cart.items, shipping_address)
                
                # Generate order number
                order_number = await self._generate_order_number(db)
                
                # Create order
                order = Order(
                    user_id=user_id,
                    order_number=order_number,
                    status=OrderStatus.PENDING,
                    
                    # Amounts
                    subtotal=summary.subtotal,
                    tax_amount=summary.tax_amount,
                    shipping_cost=summary.shipping_cost,
                    discount_amount=summary.discount_amount,
                    total_amount=summary.total_amount,
                    
                    # Addresses
                    shipping_address_snapshot={
                        "name": f"{shipping_address.first_name} {shipping_address.last_name}",
                        "phone": shipping_address.phone,
                        "address_line_1": shipping_address.address_line_1,
                        "address_line_2": shipping_address.address_line_2,
                        "city": shipping_address.city,
                        "state": shipping_address.state,
                        "postal_code": shipping_address.postal_code,
                        "country": shipping_address.country
                    },
                    billing_address_snapshot={
                        "name": f"{billing_address.first_name} {billing_address.last_name}",
                        "phone": billing_address.phone,
                        "address_line_1": billing_address.address_line_1,
                        "address_line_2": billing_address.address_line_2,
                        "city": billing_address.city,
                        "state": billing_address.state,
                        "postal_code": billing_address.postal_code,
                        "country": billing_address.country
                    },
                    
                    # Additional info
                    notes=notes,
                    estimated_delivery_date=datetime.utcnow() + timedelta(days=7)
                )
                
                db.add(order)
                await db.flush()
                
                # Create order items
                for cart_item in cart.items:
                    order_item = OrderItem(
                        order_id=order.id,
                        product_id=cart_item.product_id,
                        product_snapshot={
                            "title": cart_item.product.title,
                            "brand": cart_item.product.brand,
                            "sku": cart_item.product.sku,
                            "main_image": cart_item.product.main_image,
                            "weight_kg": float(cart_item.product.weight_kg) if cart_item.product.weight_kg else 0
                        },
                        quantity=cart_item.quantity,
                        unit_price=cart_item.unit_price,
                        total_price=cart_item.total_price
                    )
                    db.add(order_item)
                
                # Reserve inventory
                await self._reserve_inventory(db, cart.items)
                
                # Create initial status history
                status_history = OrderStatusHistory(
                    order_id=order.id,
                    status=OrderStatus.PENDING,
                    notes="Order created",
                    changed_by_user_id=user_id
                )
                db.add(status_history)
                
                # Clear cart
                for cart_item in cart.items:
                    await db.delete(cart_item)
                
                await db.commit()
                await db.refresh(order)
                
                # Send order confirmation email
                user = await db.get(User, user_id)
                if user:
                    await notification_service.send_order_confirmation(
                        user_email=user.email,
                        user_phone=user.phone,
                        order=order
                    )
                
                logger.info(f"Order created: {order.order_number}")
                
                return OrderCreationResult(
                    success=True,
                    order_id=str(order.id),
                    order_number=order.order_number,
                    order=order
                )
                
        except Exception as e:
            logger.error(f"Order creation failed: {e}")
            return OrderCreationResult(
                success=False,
                error_message=str(e)
            )
    
    async def update_order_status(
        self, 
        order_id: str, 
        new_status: OrderStatus,
        notes: Optional[str] = None,
        changed_by_user_id: Optional[str] = None
    ) -> bool:
        """Update order status with validation."""
        try:
            async with get_db_context() as db:
                # Get order
                order = await db.get(Order, order_id)
                if not order:
                    return False
                
                # Validate status transition
                if not self._is_valid_status_transition(order.status, new_status):
                    logger.warning(f"Invalid status transition: {order.status} -> {new_status}")
                    return False
                
                # Update order status
                order.status = new_status
                order.updated_at = datetime.utcnow()
                
                # Special handling for specific statuses
                if new_status == OrderStatus.SHIPPED:
                    order.shipped_at = datetime.utcnow()
                elif new_status == OrderStatus.DELIVERED:
                    order.delivered_at = datetime.utcnow()
                elif new_status == OrderStatus.CANCELLED:
                    # Release reserved inventory
                    await self._release_reserved_inventory(db, order_id)
                
                # Create status history entry
                status_history = OrderStatusHistory(
                    order_id=order_id,
                    status=new_status,
                    notes=notes,
                    changed_by_user_id=changed_by_user_id
                )
                db.add(status_history)
                
                await db.commit()
                
                # Send notifications for certain status changes
                if new_status in [OrderStatus.SHIPPED, OrderStatus.DELIVERED]:
                    user = await db.get(User, order.user_id)
                    if user and new_status == OrderStatus.SHIPPED:
                        await notification_service.send_order_shipped(
                            user_email=user.email,
                            user_phone=user.phone,
                            order=order,
                            tracking_number=order.tracking_number or ""
                        )
                
                logger.info(f"Order status updated: {order.order_number} -> {new_status}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to update order status: {e}")
            return False
    
    async def calculate_shipping_cost(self, items: List[CartItem], destination_address: UserAddress) -> Decimal:
        """Calculate shipping cost based on weight and destination."""
        try:
            # Calculate total weight
            total_weight = 0
            for item in items:
                if item.product and item.product.weight_kg:
                    total_weight += float(item.product.weight_kg) * item.quantity
            
            # Get subtotal for free shipping check
            subtotal = sum(item.get_total_price() for item in items)
            
            # Free shipping above threshold
            if subtotal >= self.free_shipping_threshold:
                return Decimal('0')
            
            # Base shipping cost
            shipping_cost = self.base_shipping_cost
            
            # Add weight-based cost (500 XAF per kg above 2kg)
            if total_weight > 2:
                extra_weight = total_weight - 2
                shipping_cost += Decimal(str(extra_weight * 500))
            
            # Location-based multiplier
            city = destination_address.city.lower() if destination_address.city else ""
            if city in ["douala", "yaoundé", "yaounde"]:
                multiplier = Decimal('1.0')  # Major cities
            elif city in ["bamenda", "bafoussam", "garoua", "maroua"]:
                multiplier = Decimal('1.5')  # Regional capitals
            else:
                multiplier = Decimal('2.0')  # Remote areas
            
            final_cost = shipping_cost * multiplier
            
            # Round to nearest 100 XAF
            return Decimal(int(final_cost / 100) * 100)
            
        except Exception as e:
            logger.error(f"Shipping calculation failed: {e}")
            return self.base_shipping_cost
    
    async def _validate_cart_items(self, db: AsyncSession, cart_items: List[CartItem]) -> Dict[str, Any]:
        """Validate cart items availability."""
        for item in cart_items:
            if not item.product or not item.product.is_active:
                return {
                    'valid': False,
                    'error': f"Product no longer available: {item.product.title if item.product else 'Unknown'}"
                }
            
            # Check inventory
            if item.product.inventory:
                available = item.product.inventory.available_quantity
                if item.quantity > available:
                    return {
                        'valid': False,
                        'error': f"Insufficient stock for {item.product.title}. Available: {available}, Requested: {item.quantity}"
                    }
        
        return {'valid': True}
    
    async def _calculate_order_summary(self, cart_items: List[CartItem], shipping_address: UserAddress) -> OrderSummary:
        """Calculate order totals."""
        subtotal = sum(item.get_total_price() for item in cart_items)
        
        # Calculate tax (VAT)
        tax_amount = subtotal * self.tax_rate
        
        # Calculate shipping
        shipping_cost = await self.calculate_shipping_cost(cart_items, shipping_address)
        
        # No discounts for now
        discount_amount = Decimal('0')
        
        # Calculate total
        total_amount = subtotal + tax_amount + shipping_cost - discount_amount
        
        # Round to nearest XAF
        total_amount = total_amount.quantize(Decimal('1'))
        
        return OrderSummary(
            subtotal=subtotal,
            tax_amount=tax_amount,
            shipping_cost=shipping_cost,
            discount_amount=discount_amount,
            total_amount=total_amount,
            item_count=len(cart_items),
            total_weight=sum(
                float(item.product.weight_kg) * item.quantity 
                for item in cart_items 
                if item.product and item.product.weight_kg
            )
        )
    
    async def _generate_order_number(self, db: AsyncSession) -> str:
        """Generate unique order number."""
        today = datetime.utcnow().strftime("%Y%m%d")
        
        # Get count of orders today
        result = await db.execute(
            select(func.count(Order.id))
            .where(Order.created_at >= datetime.utcnow().date())
        )
        daily_count = result.scalar() + 1
        
        return f"PMW{today}{daily_count:04d}"
    
    async def _reserve_inventory(self, db: AsyncSession, cart_items: List[CartItem]):
        """Reserve inventory for order items."""
        for item in cart_items:
            if item.product.inventory:
                inventory = item.product.inventory
                inventory.reserved_quantity += item.quantity
                inventory.last_updated = datetime.utcnow()
    
    async def _release_reserved_inventory(self, db: AsyncSession, order_id: str):
        """Release reserved inventory when order is cancelled."""
        order = await db.execute(
            select(Order)
            .where(Order.id == order_id)
            .options(selectinload(Order.items))
        )
        order = order.scalar_one_or_none()
        
        if order:
            for order_item in order.items:
                # Get current inventory
                inventory = await db.execute(
                    select(Inventory).where(Inventory.product_id == order_item.product_id)
                )
                inventory = inventory.scalar_one_or_none()
                
                if inventory:
                    inventory.reserved_quantity = max(0, inventory.reserved_quantity - order_item.quantity)
                    inventory.last_updated = datetime.utcnow()
    
    def _is_valid_status_transition(self, current_status: str, new_status: str) -> bool:
        """Validate if status transition is allowed."""
        allowed_transitions = {
            OrderStatus.PENDING: [OrderStatus.CONFIRMED, OrderStatus.CANCELLED],
            OrderStatus.CONFIRMED: [OrderStatus.PAID_PARTIAL, OrderStatus.PAID_FULL, OrderStatus.CANCELLED],
            OrderStatus.PAID_PARTIAL: [OrderStatus.PAID_FULL, OrderStatus.PROCESSING, OrderStatus.CANCELLED],
            OrderStatus.PAID_FULL: [OrderStatus.PROCESSING, OrderStatus.CANCELLED],
            OrderStatus.PROCESSING: [OrderStatus.SHIPPED, OrderStatus.CANCELLED],
            OrderStatus.SHIPPED: [OrderStatus.DELIVERED],
            OrderStatus.DELIVERED: [OrderStatus.REFUNDED],
            OrderStatus.CANCELLED: [],  # Terminal state
            OrderStatus.REFUNDED: []   # Terminal state
        }
        
        return new_status in allowed_transitions.get(current_status, [])


# Global service instance
order_service = OrderService()


# Convenience functions
async def create_order_from_cart(
    user_id: str, 
    shipping_address_id: str,
    billing_address_id: Optional[str] = None,
    notes: Optional[str] = None
) -> OrderCreationResult:
    """Create order from cart."""
    return await order_service.create_order_from_cart(
        user_id, shipping_address_id, billing_address_id, notes
    )


async def update_order_status(
    order_id: str, 
    new_status: OrderStatus,
    notes: Optional[str] = None,
    changed_by_user_id: Optional[str] = None
) -> bool:
    """Update order status."""
    return await order_service.update_order_status(
        order_id, new_status, notes, changed_by_user_id
    )
