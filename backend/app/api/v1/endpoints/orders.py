"""
Order endpoints for PromoWeb Africa.
Handles order creation, management, and tracking.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func, and_, or_
from sqlalchemy.orm import selectinload

from app.api.dependencies import (
    get_current_user, get_current_admin_user, get_pagination_params, get_db_session
)
from app.models.order import Order, OrderItem, OrderStatusHistory
from app.models.cart import Cart, CartItem
from app.models.user import UserAddress
from app.schemas.order import (
    OrderResponse, OrderDetail, OrderCreate, OrderUpdate, OrderListResponse,
    CartCheckout, OrderSearchQuery, OrderAnalytics, OrderBulkStatusUpdate,
    OrderStatus, PaymentGateway
)
from app.schemas.common import BaseResponse, PaginatedResponse
from app.core.database import get_db_context
from decimal import Decimal
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_model=OrderListResponse)
async def get_user_orders(
    current_user: object = Depends(get_current_user),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=50),
    status: Optional[OrderStatus] = Query(None, description="Filter by order status")
):
    """
    Get current user's orders with pagination.
    
    - **status**: Filter by order status
    """
    try:
        async with get_db_context() as db:
            # Build query
            query = select(Order).where(Order.user_id == current_user.id)
            
            if status:
                query = query.where(Order.status == status)
            
            # Get total count
            count_query = select(func.count()).select_from(query.subquery())
            total = await db.execute(count_query)
            total = total.scalar()
            
            # Get paginated orders
            orders = await db.execute(
                query.options(selectinload(Order.items).selectinload(OrderItem.product))
                .order_by(Order.created_at.desc())
                .offset((page - 1) * per_page)
                .limit(per_page)
            )
            
            orders_list = orders.scalars().all()
            
            # Calculate pagination
            pages = (total + per_page - 1) // per_page
            
            return OrderListResponse(
                items=orders_list,
                total=total,
                page=page,
                per_page=per_page,
                pages=pages,
                has_next=page < pages,
                has_prev=page > 1
            )
            
    except Exception as e:
        logger.error(f"Failed to get user orders: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve orders"
        )


@router.get("/{order_id}", response_model=OrderDetail)
async def get_order(
    order_id: str,
    current_user: object = Depends(get_current_user)
):
    """
    Get order details by ID.
    
    Returns complete order information including items, payments, and shipping.
    """
    try:
        async with get_db_context() as db:
            # Get order with all related data
            order = await db.execute(
                select(Order)
                .where(Order.id == order_id, Order.user_id == current_user.id)
                .options(
                    selectinload(Order.items).selectinload(OrderItem.product),
                    selectinload(Order.payments),
                    selectinload(Order.shipping).selectinload(Order.shipping.tracking_events),
                    selectinload(Order.status_history).selectinload(OrderStatusHistory.changed_by),
                    selectinload(Order.user)
                )
            )
            order = order.scalar_one_or_none()
            
            if not order:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Order not found"
                )
            
            return OrderDetail(
                **order.__dict__,
                items=order.items,
                payments=order.payments,
                shipping=order.shipping,
                status_history=order.status_history,
                user_name=f"{order.user.first_name} {order.user.last_name}",
                user_email=order.user.email
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get order: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve order"
        )


@router.post("/checkout", response_model=OrderDetail, status_code=status.HTTP_201_CREATED)
async def checkout_cart(
    checkout_data: CartCheckout,
    current_user: object = Depends(get_current_user),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Create order from cart (checkout process).
    
    - **cart_id**: Cart to convert to order
    - **billing_address**: Billing address information
    - **shipping_address**: Shipping address (optional, uses billing if not provided)
    - **shipping_address_id**: Use saved shipping address
    - **billing_address_id**: Use saved billing address
    - **notes**: Order notes
    - **payment_gateway**: Preferred payment method
    """
    try:
        async with get_db_context() as db:
            # Get cart with items
            cart = await db.execute(
                select(Cart)
                .where(Cart.id == checkout_data.cart_id, Cart.user_id == current_user.id)
                .options(
                    selectinload(Cart.items).selectinload(CartItem.product).selectinload(Product.inventory)
                )
            )
            cart = cart.scalar_one_or_none()
            
            if not cart or cart.is_empty:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cart is empty or not found"
                )
            
            # Validate cart items availability
            for item in cart.items:
                if not item.product or not item.product.is_active:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Product no longer available: {item.product.title if item.product else 'Unknown'}"
                    )
                
                if not item.product.inventory.can_reserve(item.quantity):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Insufficient stock for: {item.product.title}"
                    )
            
            # Get or validate addresses
            billing_address = None
            shipping_address = None
            
            if checkout_data.billing_address_id:
                billing_address = await db.execute(
                    select(UserAddress).where(
                        UserAddress.id == checkout_data.billing_address_id,
                        UserAddress.user_id == current_user.id
                    )
                )
                billing_address = billing_address.scalar_one_or_none()
                if not billing_address:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Billing address not found"
                    )
            
            if checkout_data.shipping_address_id:
                shipping_address = await db.execute(
                    select(UserAddress).where(
                        UserAddress.id == checkout_data.shipping_address_id,
                        UserAddress.user_id == current_user.id
                    )
                )
                shipping_address = shipping_address.scalar_one_or_none()
                if not shipping_address:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Shipping address not found"
                    )
            
            # Calculate order totals
            totals = cart.calculate_totals()
            
            # Generate order number
            order_count = await db.execute(
                select(func.count(Order.id)).where(
                    func.date(Order.created_at) == func.date(datetime.utcnow())
                )
            )
            daily_count = order_count.scalar() + 1
            order_number = f"PW{datetime.utcnow().strftime('%Y%m%d')}{daily_count:04d}"
            
            # Create order
            order = Order(
                order_number=order_number,
                user_id=current_user.id,
                total_amount=totals['total'],
                shipping_cost=totals['shipping_estimate'],
                tax_amount=totals['tax_amount'],
                discount_amount=totals['discount_amount'],
                notes=checkout_data.notes
            )
            
            # Set addresses from saved addresses or provided data
            if billing_address:
                order.billing_name = billing_address.name
                order.billing_address = billing_address.full_address
                order.billing_address_id = billing_address.id
            elif checkout_data.billing_address:
                addr = checkout_data.billing_address
                order.billing_name = addr.name
                order.billing_email = addr.email
                order.billing_phone = addr.phone
                order.billing_address = addr.address
                order.billing_city = addr.city
                order.billing_region = addr.region
                order.billing_postal_code = addr.postal_code
                order.billing_country = addr.country
            
            # Set shipping address (use billing if not provided)
            if shipping_address:
                order.shipping_name = shipping_address.name
                order.shipping_address = shipping_address.full_address
                order.shipping_address_id = shipping_address.id
                if shipping_address.location:
                    order.shipping_location = shipping_address.location
            elif checkout_data.shipping_address:
                addr = checkout_data.shipping_address
                order.shipping_name = addr.name
                order.shipping_address = addr.address
                order.shipping_city = addr.city
                order.shipping_region = addr.region
                order.shipping_postal_code = addr.postal_code
                order.shipping_country = addr.country
                if addr.latitude and addr.longitude:
                    from geoalchemy2 import WKTElement
                    order.shipping_location = WKTElement(
                        f'POINT({addr.longitude} {addr.latitude})',
                        srid=4326
                    )
            else:
                # Use billing address for shipping
                order.shipping_name = order.billing_name
                order.shipping_address = order.billing_address
                order.shipping_city = order.billing_city
                order.shipping_region = order.billing_region
                order.shipping_postal_code = order.billing_postal_code
                order.shipping_country = order.billing_country
            
            # Calculate deposit and remaining amounts
            from app.core.config import get_settings
            settings = get_settings()
            deposit_percentage = settings.DEFAULT_DEPOSIT_PERCENTAGE
            
            order.deposit_amount = (order.total_amount * deposit_percentage) / 100
            order.remaining_amount = order.total_amount - order.deposit_amount
            
            db.add(order)
            await db.commit()
            await db.refresh(order)
            
            # Create order items
            for cart_item in cart.items:
                order_item = OrderItem(
                    order_id=order.id,
                    product_id=cart_item.product_id,
                    quantity=cart_item.quantity,
                    unit_price=cart_item.unit_price,
                    total_price=cart_item.total_price
                )
                order_item.create_product_snapshot()
                db.add(order_item)
            
            # Reserve inventory
            for cart_item in cart.items:
                cart_item.product.inventory.reserve(cart_item.quantity)
            
            # Clear cart after successful order creation
            await db.execute(
                select(CartItem).where(CartItem.cart_id == cart.id)
            ).delete()
            cart.update_totals()
            
            await db.commit()
            
            # Create initial payment record in background
            background_tasks.add_task(
                create_initial_payment,
                order.id,
                checkout_data.payment_gateway,
                order.deposit_amount
            )
            
            # Send order confirmation email in background
            background_tasks.add_task(send_order_confirmation, order.id)
            
            logger.info(f"Order created: {order.order_number} for user {current_user.email}")
            
            # Reload order with relationships for response
            order_with_relations = await db.execute(
                select(Order)
                .where(Order.id == order.id)
                .options(
                    selectinload(Order.items).selectinload(OrderItem.product),
                    selectinload(Order.payments),
                    selectinload(Order.user)
                )
            )
            order = order_with_relations.scalar_one()
            
            return OrderDetail(
                **order.__dict__,
                items=order.items,
                payments=order.payments,
                shipping=None,
                status_history=[],
                user_name=f"{order.user.first_name} {order.user.last_name}",
                user_email=order.user.email
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Checkout failed: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Checkout failed. Please try again."
        )


@router.patch("/{order_id}/cancel", response_model=BaseResponse)
async def cancel_order(
    order_id: str,
    current_user: object = Depends(get_current_user)
):
    """
    Cancel order (if cancellable).
    
    Orders can only be cancelled if they haven't been shipped yet.
    """
    try:
        async with get_db_context() as db:
            order = await db.execute(
                select(Order)
                .where(Order.id == order_id, Order.user_id == current_user.id)
                .options(selectinload(Order.items).selectinload(OrderItem.product))
            )
            order = order.scalar_one_or_none()
            
            if not order:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Order not found"
                )
            
            if not order.can_be_cancelled:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Order cannot be cancelled at this stage"
                )
            
            # Cancel order
            order.change_status("cancelled", "Cancelled by customer", str(current_user.id))
            
            # Release inventory reservations
            for item in order.items:
                if item.product and item.product.inventory:
                    item.product.inventory.release_reservation(item.quantity)
            
            await db.commit()
            
            logger.info(f"Order cancelled: {order.order_number}")
            return BaseResponse(message="Order cancelled successfully")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel order: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel order"
        )


# Admin endpoints
@router.get("/admin/orders", response_model=PaginatedResponse[OrderResponse])
async def list_all_orders(
    admin_user: object = Depends(get_current_admin_user),
    pagination: dict = Depends(get_pagination_params),
    status: Optional[OrderStatus] = Query(None),
    payment_gateway: Optional[PaymentGateway] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    search: Optional[str] = Query(None, description="Search by order number or customer email")
):
    """
    List all orders with filtering (admin only).
    
    - **status**: Filter by order status
    - **payment_gateway**: Filter by payment method
    - **date_from**: Orders from date
    - **date_to**: Orders to date
    - **search**: Search by order number or customer email
    """
    try:
        async with get_db_context() as db:
            # Build query
            query = select(Order).options(selectinload(Order.user))
            
            # Apply filters
            if status:
                query = query.where(Order.status == status)
            
            if date_from:
                query = query.where(Order.created_at >= date_from)
            
            if date_to:
                query = query.where(Order.created_at <= date_to)
            
            if search:
                from app.models.user import User
                query = query.join(User).where(
                    or_(
                        Order.order_number.ilike(f"%{search}%"),
                        User.email.ilike(f"%{search}%"),
                        func.concat(User.first_name, ' ', User.last_name).ilike(f"%{search}%")
                    )
                )
            
            # Get total count
            count_query = select(func.count()).select_from(query.subquery())
            total = await db.execute(count_query)
            total = total.scalar()
            
            # Get paginated results
            orders = await db.execute(
                query.order_by(Order.created_at.desc())
                .offset(pagination['offset'])
                .limit(pagination['per_page'])
            )
            
            return PaginatedResponse.create(
                items=orders.scalars().all(),
                page=pagination['page'],
                per_page=pagination['per_page'],
                total=total
            )
            
    except Exception as e:
        logger.error(f"Failed to list orders: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve orders"
        )


@router.get("/admin/orders/{order_id}", response_model=OrderDetail)
async def get_order_admin(
    order_id: str,
    admin_user: object = Depends(get_current_admin_user)
):
    """Get order details (admin only)."""
    try:
        async with get_db_context() as db:
            order = await db.execute(
                select(Order)
                .where(Order.id == order_id)
                .options(
                    selectinload(Order.items).selectinload(OrderItem.product),
                    selectinload(Order.payments),
                    selectinload(Order.shipping).selectinload(Order.shipping.tracking_events),
                    selectinload(Order.status_history).selectinload(OrderStatusHistory.changed_by),
                    selectinload(Order.user)
                )
            )
            order = order.scalar_one_or_none()
            
            if not order:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Order not found"
                )
            
            return OrderDetail(
                **order.__dict__,
                items=order.items,
                payments=order.payments,
                shipping=order.shipping,
                status_history=order.status_history,
                user_name=f"{order.user.first_name} {order.user.last_name}",
                user_email=order.user.email
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get order: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve order"
        )


@router.patch("/admin/orders/{order_id}/status", response_model=BaseResponse)
async def update_order_status(
    order_id: str,
    status_update: OrderUpdate,
    admin_user: object = Depends(get_current_admin_user)
):
    """Update order status (admin only)."""
    try:
        async with get_db_context() as db:
            order = await db.get(Order, order_id)
            if not order:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Order not found"
                )
            
            # Update order
            if status_update.status:
                order.change_status(
                    status_update.status,
                    status_update.notes or f"Status updated to {status_update.status} by admin",
                    str(admin_user.id)
                )
            
            if status_update.admin_notes:
                order.admin_notes = status_update.admin_notes
            
            if status_update.notes:
                order.notes = status_update.notes
            
            await db.commit()
            
            logger.info(f"Order status updated by admin: {order.order_number}")
            return BaseResponse(message="Order status updated successfully")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update order status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update order status"
        )


# Background tasks
async def create_initial_payment(order_id: str, gateway: PaymentGateway, amount: Decimal):
    """Create initial payment record for order."""
    try:
        async with get_db_context() as db:
            from app.models.payment import Payment
            
            payment = Payment(
                order_id=order_id,
                gateway=gateway,
                amount=amount,
                currency="XAF"
            )
            payment.generate_reference_id()
            
            db.add(payment)
            await db.commit()
            
            logger.info(f"Initial payment created for order: {order_id}")
            
    except Exception as e:
        logger.error(f"Failed to create initial payment: {e}")


async def send_order_confirmation(order_id: str):
    """Send order confirmation email."""
    try:
        # This would integrate with email service
        logger.info(f"TODO: Send order confirmation email for order: {order_id}")
        
    except Exception as e:
        logger.error(f"Failed to send order confirmation: {e}")


# Import required models
from app.models.product import Product
