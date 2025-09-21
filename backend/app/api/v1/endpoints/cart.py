"""
Shopping cart endpoints for PromoWeb Africa.
Handles cart operations, items management, and checkout preparation.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete as sql_delete
from sqlalchemy.orm import selectinload

from app.api.dependencies import (
    get_current_user_optional, get_current_user, validate_cart_access, get_db_session
)
from app.models.cart import Cart, CartItem, SavedItem
from app.models.product import Product
from app.schemas.cart import (
    CartResponse, CartDetail, CartTotals, AddToCartRequest, 
    UpdateCartItemRequest, RemoveFromCartRequest, ClearCartRequest,
    SavedItemCreate, SavedItemResponse, SavedItemsList, MoveToCartRequest,
    CartValidationResult, CartSummary, ApplyPromoCodeRequest, PromoCodeResult
)
from app.schemas.common import BaseResponse
from app.core.database import get_db_context
from datetime import datetime, timedelta
import uuid
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_model=CartDetail)
async def get_cart(
    request: Request,
    current_user: Optional[object] = Depends(get_current_user_optional),
    x_session_id: Optional[str] = Header(None)
):
    """
    Get current user's cart or create a new one.
    
    For authenticated users, returns their cart.
    For anonymous users, uses session ID from X-Session-ID header.
    """
    try:
        async with get_db_context() as db:
            cart = None
            
            if current_user:
                # Get authenticated user's cart
                cart_query = await db.execute(
                    select(Cart)
                    .where(Cart.user_id == current_user.id)
                    .options(
                        selectinload(Cart.items).selectinload(CartItem.product).selectinload(Product.inventory)
                    )
                )
                cart = cart_query.scalar_one_or_none()
                
                if not cart:
                    # Create new cart for user
                    cart = Cart(user_id=current_user.id)
                    db.add(cart)
                    await db.commit()
                    await db.refresh(cart)
            else:
                # Anonymous user - use session ID
                session_id = x_session_id
                if not session_id:
                    # Generate new session ID
                    session_id = str(uuid.uuid4())
                
                cart_query = await db.execute(
                    select(Cart)
                    .where(Cart.session_id == session_id)
                    .options(
                        selectinload(Cart.items).selectinload(CartItem.product).selectinload(Product.inventory)
                    )
                )
                cart = cart_query.scalar_one_or_none()
                
                if not cart:
                    # Create new anonymous cart
                    cart = Cart(
                        session_id=session_id,
                        expires_at=datetime.utcnow() + timedelta(days=7)  # 7 days for anonymous carts
                    )
                    db.add(cart)
                    await db.commit()
                    await db.refresh(cart)
            
            # Calculate totals
            totals = cart.calculate_totals()
            
            # Prepare cart items with availability check
            cart_items = []
            for item in cart.items:
                if item.product:
                    cart_items.append({
                        **item.__dict__,
                        "current_price": item.get_total_price(),
                        "savings": item.get_savings(),
                        "is_available": item.is_available,
                        "availability_message": item.availability_message,
                        "max_available_quantity": item.product.stock_quantity if item.product.inventory else 0,
                        "product_title": item.product.title,
                        "product_image": item.product.main_image,
                        "product_brand": item.product.brand,
                        "product_weight_kg": item.product.weight_kg
                    })
            
            return CartDetail(
                **cart.__dict__,
                items=cart_items,
                totals=CartTotals(**totals),
                is_expired=cart.is_expired,
                is_empty=cart.is_empty
            )
            
    except Exception as e:
        logger.error(f"Failed to get cart: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve cart"
        )


@router.post("/items", response_model=BaseResponse, status_code=status.HTTP_201_CREATED)
async def add_to_cart(
    add_request: AddToCartRequest,
    request: Request,
    current_user: Optional[object] = Depends(get_current_user_optional),
    x_session_id: Optional[str] = Header(None)
):
    """
    Add item to cart.
    
    - **product_id**: Product to add
    - **quantity**: Quantity to add (default: 1)
    - **notes**: Optional notes for the item
    """
    try:
        async with get_db_context() as db:
            # Get or create cart
            cart = await get_or_create_cart(db, current_user, x_session_id)
            
            # Verify product exists and is available
            product = await db.execute(
                select(Product)
                .where(Product.id == add_request.product_id, Product.is_active == True)
                .options(selectinload(Product.inventory))
            )
            product = product.scalar_one_or_none()
            
            if not product:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Product not found or unavailable"
                )
            
            # Check stock availability
            if product.inventory and product.inventory.available_quantity < add_request.quantity:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Only {product.inventory.available_quantity} items available in stock"
                )
            
            # Check if item already exists in cart
            existing_item = await db.execute(
                select(CartItem).where(
                    CartItem.cart_id == cart.id,
                    CartItem.product_id == add_request.product_id
                )
            )
            existing_item = existing_item.scalar_one_or_none()
            
            if existing_item:
                # Update existing item
                new_quantity = existing_item.quantity + add_request.quantity
                
                # Check total quantity against stock
                if product.inventory and product.inventory.available_quantity < new_quantity:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Cannot add {add_request.quantity} more items. Only {product.inventory.available_quantity - existing_item.quantity} more available"
                    )
                
                existing_item.quantity = new_quantity
                existing_item.unit_price = product.get_current_price()
                existing_item.total_price = existing_item.unit_price * new_quantity
                if add_request.notes:
                    existing_item.notes = add_request.notes
                existing_item.updated_at = datetime.utcnow()
            else:
                # Create new cart item
                cart_item = CartItem(
                    cart_id=cart.id,
                    product_id=add_request.product_id,
                    quantity=add_request.quantity,
                    unit_price=product.get_current_price(),
                    total_price=product.get_current_price() * add_request.quantity,
                    notes=add_request.notes
                )
                db.add(cart_item)
            
            # Update cart totals
            cart.update_totals()
            await db.commit()
            
            logger.info(f"Item added to cart: {product.title} x{add_request.quantity}")
            return BaseResponse(message="Item added to cart successfully")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to add item to cart: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add item to cart"
        )


@router.put("/items/{item_id}", response_model=BaseResponse)
async def update_cart_item(
    item_id: str,
    update_request: UpdateCartItemRequest,
    current_user: Optional[object] = Depends(get_current_user_optional)
):
    """
    Update cart item quantity or notes.
    
    - **quantity**: New quantity
    - **notes**: Updated notes
    """
    try:
        async with get_db_context() as db:
            # Get cart item and verify access
            cart_item = await db.execute(
                select(CartItem)
                .where(CartItem.id == item_id)
                .options(
                    selectinload(CartItem.cart),
                    selectinload(CartItem.product).selectinload(Product.inventory)
                )
            )
            cart_item = cart_item.scalar_one_or_none()
            
            if not cart_item:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Cart item not found"
                )
            
            # Verify cart access
            cart = cart_item.cart
            if current_user:
                if cart.user_id != current_user.id:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Access denied to this cart item"
                    )
            else:
                # For anonymous users, we'd need session validation
                # This is simplified for now
                pass
            
            # Check stock availability for new quantity
            if cart_item.product.inventory and cart_item.product.inventory.available_quantity < update_request.quantity:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Only {cart_item.product.inventory.available_quantity} items available in stock"
                )
            
            # Update cart item
            cart_item.quantity = update_request.quantity
            cart_item.unit_price = cart_item.product.get_current_price()
            cart_item.total_price = cart_item.unit_price * update_request.quantity
            if update_request.notes is not None:
                cart_item.notes = update_request.notes
            cart_item.updated_at = datetime.utcnow()
            
            # Update cart totals
            cart.update_totals()
            await db.commit()
            
            logger.info(f"Cart item updated: {cart_item.product.title} -> {update_request.quantity}")
            return BaseResponse(message="Cart item updated successfully")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update cart item: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update cart item"
        )


@router.delete("/items/{item_id}", response_model=BaseResponse)
async def remove_cart_item(
    item_id: str,
    current_user: Optional[object] = Depends(get_current_user_optional)
):
    """Remove item from cart."""
    try:
        async with get_db_context() as db:
            # Get cart item and verify access
            cart_item = await db.execute(
                select(CartItem)
                .where(CartItem.id == item_id)
                .options(selectinload(CartItem.cart))
            )
            cart_item = cart_item.scalar_one_or_none()
            
            if not cart_item:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Cart item not found"
                )
            
            # Verify cart access
            cart = cart_item.cart
            if current_user and cart.user_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied to this cart item"
                )
            
            # Remove cart item
            await db.delete(cart_item)
            
            # Update cart totals
            cart.update_totals()
            await db.commit()
            
            logger.info(f"Cart item removed: {item_id}")
            return BaseResponse(message="Item removed from cart successfully")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to remove cart item: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove cart item"
        )


@router.post("/clear", response_model=BaseResponse)
async def clear_cart(
    clear_request: ClearCartRequest,
    request: Request,
    current_user: Optional[object] = Depends(get_current_user_optional),
    x_session_id: Optional[str] = Header(None)
):
    """
    Clear all items from cart.
    
    - **confirm**: Must be true to confirm clearing
    """
    if not clear_request.confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Confirmation required to clear cart"
        )
    
    try:
        async with get_db_context() as db:
            # Get cart
            cart = await get_or_create_cart(db, current_user, x_session_id, create_if_missing=False)
            
            if not cart:
                return BaseResponse(message="Cart is already empty")
            
            # Remove all cart items
            await db.execute(
                sql_delete(CartItem).where(CartItem.cart_id == cart.id)
            )
            
            # Update cart totals
            cart.update_totals()
            await db.commit()
            
            logger.info(f"Cart cleared for {'user' if current_user else 'session'}")
            return BaseResponse(message="Cart cleared successfully")
            
    except Exception as e:
        logger.error(f"Failed to clear cart: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clear cart"
        )


@router.get("/validate", response_model=CartValidationResult)
async def validate_cart(
    request: Request,
    current_user: Optional[object] = Depends(get_current_user_optional),
    x_session_id: Optional[str] = Header(None)
):
    """
    Validate cart items availability and pricing.
    
    Checks if all items are still available and prices are current.
    """
    try:
        async with get_db_context() as db:
            cart = await get_or_create_cart(db, current_user, x_session_id, create_if_missing=False)
            
            if not cart:
                return CartValidationResult(
                    is_valid=True,
                    errors=[],
                    warnings=[],
                    unavailable_items=[],
                    quantity_adjustments={}
                )
            
            # Load cart items with products
            cart_items = await db.execute(
                select(CartItem)
                .where(CartItem.cart_id == cart.id)
                .options(
                    selectinload(CartItem.product).selectinload(Product.inventory)
                )
            )
            cart_items = cart_items.scalars().all()
            
            errors = []
            warnings = []
            unavailable_items = []
            quantity_adjustments = {}
            is_valid = True
            
            for item in cart_items:
                if not item.product or not item.product.is_active:
                    errors.append(f"Product no longer available: {item.product.title if item.product else 'Unknown'}")
                    unavailable_items.append(str(item.product_id))
                    is_valid = False
                    continue
                
                # Check stock availability
                if not item.product.is_in_stock:
                    errors.append(f"Out of stock: {item.product.title}")
                    unavailable_items.append(str(item.product_id))
                    is_valid = False
                    continue
                
                # Check quantity availability
                available_qty = item.product.stock_quantity
                if item.quantity > available_qty:
                    if available_qty > 0:
                        warnings.append(f"Quantity reduced for {item.product.title}: {item.quantity} → {available_qty}")
                        quantity_adjustments[str(item.product_id)] = available_qty
                    else:
                        errors.append(f"Out of stock: {item.product.title}")
                        unavailable_items.append(str(item.product_id))
                        is_valid = False
                
                # Check price changes
                current_price = item.product.get_current_price()
                if item.unit_price != current_price:
                    price_diff = current_price - item.unit_price
                    if price_diff > 0:
                        warnings.append(f"Price increased for {item.product.title}: +{price_diff} XAF")
                    else:
                        warnings.append(f"Price decreased for {item.product.title}: {abs(price_diff)} XAF")
            
            return CartValidationResult(
                is_valid=is_valid,
                errors=errors,
                warnings=warnings,
                unavailable_items=unavailable_items,
                quantity_adjustments=quantity_adjustments
            )
            
    except Exception as e:
        logger.error(f"Failed to validate cart: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to validate cart"
        )


@router.get("/summary", response_model=CartSummary)
async def get_cart_summary(
    request: Request,
    current_user: Optional[object] = Depends(get_current_user_optional),
    x_session_id: Optional[str] = Header(None)
):
    """
    Get cart summary for checkout.
    
    Returns simplified cart information suitable for checkout process.
    """
    try:
        async with get_db_context() as db:
            cart = await get_or_create_cart(db, current_user, x_session_id, create_if_missing=False)
            
            if not cart or cart.is_empty:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cart is empty"
                )
            
            # Get cart totals
            totals = cart.calculate_totals()
            
            # Get simplified items info
            items_summary = []
            requires_shipping = False
            total_weight = 0
            
            cart_items = await db.execute(
                select(CartItem)
                .where(CartItem.cart_id == cart.id)
                .options(selectinload(CartItem.product))
            )
            
            for item in cart_items.scalars().all():
                if item.product:
                    items_summary.append({
                        "product_id": str(item.product.id),
                        "title": item.product.title,
                        "quantity": item.quantity,
                        "unit_price": item.get_total_price() / item.quantity,
                        "total_price": item.get_total_price(),
                        "image": item.product.main_image
                    })
                    
                    if not item.product.is_digital:
                        requires_shipping = True
                    
                    if item.product.weight_kg:
                        total_weight += float(item.product.weight_kg) * item.quantity
            
            return CartSummary(
                cart_id=str(cart.id),
                total_items=totals['item_count'],
                subtotal=totals['subtotal'],
                estimated_tax=totals['tax_amount'],
                estimated_shipping=totals['shipping_estimate'],
                estimated_total=totals['total'],
                items_summary=items_summary,
                requires_shipping=requires_shipping,
                estimated_weight=total_weight
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get cart summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get cart summary"
        )


# Wishlist/Saved items endpoints
@router.get("/saved", response_model=SavedItemsList)
async def get_saved_items(current_user: object = Depends(get_current_user)):
    """Get user's saved items (wishlist)."""
    try:
        async with get_db_context() as db:
            saved_items = await db.execute(
                select(SavedItem)
                .where(SavedItem.user_id == current_user.id)
                .options(selectinload(SavedItem.product))
                .order_by(SavedItem.created_at.desc())
            )
            saved_items = saved_items.scalars().all()
            
            # Group by list name
            lists = {}
            price_drop_alerts = 0
            
            for item in saved_items:
                if item.product:
                    list_name = item.list_name
                    if list_name not in lists:
                        lists[list_name] = []
                    
                    current_price = item.product.get_current_price()
                    
                    item_response = SavedItemResponse(
                        **item.__dict__,
                        current_price=current_price,
                        price_difference=current_price - item.price_when_saved if current_price else None,
                        price_dropped=current_price < item.price_when_saved if current_price else False,
                        savings_amount=item.price_when_saved - current_price if current_price and current_price < item.price_when_saved else 0,
                        product_title=item.product.title,
                        product_image=item.product.main_image,
                        product_brand=item.product.brand,
                        product_is_available=item.product.is_active and item.product.is_in_stock
                    )
                    
                    lists[list_name].append(item_response)
                    
                    if item_response.price_dropped and item.notify_on_price_drop:
                        price_drop_alerts += 1
            
            return SavedItemsList(
                lists=lists,
                total_items=len(saved_items),
                price_drop_alerts=price_drop_alerts
            )
            
    except Exception as e:
        logger.error(f"Failed to get saved items: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve saved items"
        )


@router.post("/saved", response_model=SavedItemResponse, status_code=status.HTTP_201_CREATED)
async def save_item(
    save_request: SavedItemCreate,
    current_user: object = Depends(get_current_user)
):
    """Save item to wishlist."""
    try:
        async with get_db_context() as db:
            # Check if product exists
            product = await db.get(Product, save_request.product_id)
            if not product or not product.is_active:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Product not found"
                )
            
            # Check if already saved
            existing_item = await db.execute(
                select(SavedItem).where(
                    SavedItem.user_id == current_user.id,
                    SavedItem.product_id == save_request.product_id
                )
            )
            if existing_item.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Item is already saved"
                )
            
            # Create saved item
            saved_item = SavedItem(
                user_id=current_user.id,
                product_id=save_request.product_id,
                list_name=save_request.list_name,
                notes=save_request.notes,
                notify_on_price_drop=save_request.notify_on_price_drop,
                price_when_saved=product.get_current_price()
            )
            
            db.add(saved_item)
            await db.commit()
            await db.refresh(saved_item)
            
            logger.info(f"Item saved to wishlist: {product.title}")
            
            return SavedItemResponse(
                **saved_item.__dict__,
                current_price=product.get_current_price(),
                price_difference=0,
                price_dropped=False,
                savings_amount=0,
                product_title=product.title,
                product_image=product.main_image,
                product_brand=product.brand,
                product_is_available=product.is_active and product.is_in_stock
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to save item: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save item"
        )


# Helper functions
async def get_or_create_cart(
    db: AsyncSession, 
    current_user: Optional[object], 
    session_id: Optional[str],
    create_if_missing: bool = True
) -> Optional[Cart]:
    """Get existing cart or create new one."""
    if current_user:
        cart_query = await db.execute(
            select(Cart).where(Cart.user_id == current_user.id)
        )
        cart = cart_query.scalar_one_or_none()
        
        if not cart and create_if_missing:
            cart = Cart(user_id=current_user.id)
            db.add(cart)
            await db.commit()
            await db.refresh(cart)
    else:
        if not session_id:
            if not create_if_missing:
                return None
            session_id = str(uuid.uuid4())
        
        cart_query = await db.execute(
            select(Cart).where(Cart.session_id == session_id)
        )
        cart = cart_query.scalar_one_or_none()
        
        if not cart and create_if_missing:
            cart = Cart(
                session_id=session_id,
                expires_at=datetime.utcnow() + timedelta(days=7)
            )
            db.add(cart)
            await db.commit()
            await db.refresh(cart)
    
    return cart
