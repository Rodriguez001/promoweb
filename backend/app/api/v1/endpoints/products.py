"""
Product endpoints for PromoWeb Africa.
Handles product catalog, search, reviews, and inventory management.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func, and_, or_
from sqlalchemy.orm import selectinload

from app.api.dependencies import (
    get_current_user_optional, get_current_user, get_current_admin_user,
    get_pagination_params, get_db_session
)
from app.models.product import Product, Category, Inventory, ProductReview
from app.models.analytics import ProductView, SearchAnalytic
from app.schemas.product import (
    ProductResponse, ProductDetail, ProductListResponse, ProductCreate,
    ProductUpdate, ProductSearchQuery, ProductSearchResponse,
    InventoryResponse, InventoryUpdate, ProductReviewCreate,
    ProductReviewResponse, ProductAnalytics, ProductBulkUpdate
)
from app.schemas.common import BaseResponse, PaginatedResponse
from app.core.database import get_db_context
from app.core.redis import get_cache
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_model=ProductListResponse)
async def list_products(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    category_id: Optional[str] = Query(None),
    brand: Optional[str] = Query(None),
    min_price: Optional[Decimal] = Query(None, ge=0),
    max_price: Optional[Decimal] = Query(None, ge=0),
    in_stock: Optional[bool] = Query(None),
    is_featured: Optional[bool] = Query(None),
    sort_by: str = Query("created_at", regex="^(created_at|price_asc|price_desc|name|popularity)$"),
    current_user: Optional[object] = Depends(get_current_user_optional)
):
    """
    List products with filtering and pagination.
    
    - **category_id**: Filter by category
    - **brand**: Filter by brand
    - **min_price**: Minimum price in XAF
    - **max_price**: Maximum price in XAF
    - **in_stock**: Only show products in stock
    - **is_featured**: Only show featured products
    - **sort_by**: Sort criteria (created_at, price_asc, price_desc, name, popularity)
    """
    try:
        async with get_db_context() as db:
            # Build query
            query = select(Product).where(Product.is_active == True)
            
            # Apply filters
            if category_id:
                query = query.where(Product.category_id == category_id)
            
            if brand:
                query = query.where(Product.brand.ilike(f"%{brand}%"))
            
            if min_price is not None:
                query = query.where(Product.price_xaf >= min_price)
            
            if max_price is not None:
                query = query.where(Product.price_xaf <= max_price)
            
            if in_stock:
                query = query.join(Inventory).where(
                    Inventory.quantity - Inventory.reserved_quantity > 0
                )
            
            if is_featured is not None:
                query = query.where(Product.is_featured == is_featured)
            
            # Apply sorting
            if sort_by == "price_asc":
                query = query.order_by(Product.price_xaf.asc())
            elif sort_by == "price_desc":
                query = query.order_by(Product.price_xaf.desc())
            elif sort_by == "name":
                query = query.order_by(Product.title.asc())
            elif sort_by == "popularity":
                # Join with product views for popularity
                from app.models.analytics import ProductView
                query = query.outerjoin(ProductView).group_by(Product.id).order_by(
                    func.count(ProductView.id).desc()
                )
            else:  # created_at (default)
                query = query.order_by(Product.created_at.desc())
            
            # Get total count
            count_query = select(func.count()).select_from(query.subquery())
            total = await db.execute(count_query)
            total = total.scalar()
            
            # Get paginated results with relationships
            products = await db.execute(
                query.options(
                    selectinload(Product.category),
                    selectinload(Product.inventory),
                    selectinload(Product.promotions)
                )
                .offset((page - 1) * per_page)
                .limit(per_page)
            )
            
            products_list = products.scalars().all()
            
            # Calculate pagination info
            pages = (total + per_page - 1) // per_page
            
            return ProductListResponse(
                items=products_list,
                total=total,
                page=page,
                per_page=per_page,
                pages=pages,
                has_next=page < pages,
                has_prev=page > 1
            )
            
    except Exception as e:
        logger.error(f"Failed to list products: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve products"
        )


@router.get("/search", response_model=ProductSearchResponse)
async def search_products(
    q: str = Query(..., min_length=1, description="Search query"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    category_id: Optional[str] = Query(None),
    min_price: Optional[Decimal] = Query(None, ge=0),
    max_price: Optional[Decimal] = Query(None, ge=0),
    sort_by: str = Query("relevance", regex="^(relevance|price_asc|price_desc|name|created_at)$"),
    current_user: Optional[object] = Depends(get_current_user_optional),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Search products with full-text search.
    
    - **q**: Search query (required)
    - **category_id**: Filter by category
    - **min_price**: Minimum price in XAF
    - **max_price**: Maximum price in XAF
    - **sort_by**: Sort criteria
    """
    try:
        search_start_time = datetime.utcnow()
        
        async with get_db_context() as db:
            # Build search query using PostgreSQL full-text search
            search_query = select(Product).where(
                and_(
                    Product.is_active == True,
                    or_(
                        Product.title.ilike(f"%{q}%"),
                        Product.description.ilike(f"%{q}%"),
                        Product.brand.ilike(f"%{q}%"),
                        Product.tags.contains([q.lower()])
                    )
                )
            )
            
            # Apply additional filters
            if category_id:
                search_query = search_query.where(Product.category_id == category_id)
            
            if min_price is not None:
                search_query = search_query.where(Product.price_xaf >= min_price)
            
            if max_price is not None:
                search_query = search_query.where(Product.price_xaf <= max_price)
            
            # Apply sorting
            if sort_by == "price_asc":
                search_query = search_query.order_by(Product.price_xaf.asc())
            elif sort_by == "price_desc":
                search_query = search_query.order_by(Product.price_xaf.desc())
            elif sort_by == "name":
                search_query = search_query.order_by(Product.title.asc())
            elif sort_by == "created_at":
                search_query = search_query.order_by(Product.created_at.desc())
            else:  # relevance (default)
                # Simple relevance scoring - title matches score higher
                search_query = search_query.order_by(
                    func.case(
                        [(Product.title.ilike(f"%{q}%"), 1)],
                        else_=2
                    ),
                    Product.created_at.desc()
                )
            
            # Get total count
            count_query = select(func.count()).select_from(search_query.subquery())
            total = await db.execute(count_query)
            total = total.scalar()
            
            # Get paginated results
            products = await db.execute(
                search_query.options(
                    selectinload(Product.category),
                    selectinload(Product.inventory),
                    selectinload(Product.promotions)
                )
                .offset((page - 1) * per_page)
                .limit(per_page)
            )
            
            products_list = products.scalars().all()
            
            # Calculate search time
            search_time_ms = int((datetime.utcnow() - search_start_time).total_seconds() * 1000)
            
            # Log search analytics in background
            background_tasks.add_task(
                log_search_analytics,
                query=q,
                user_id=str(current_user.id) if current_user else None,
                results_count=total,
                search_time_ms=search_time_ms
            )
            
            # Calculate pagination
            pages = (total + per_page - 1) // per_page
            
            # Create product list response
            product_list = ProductListResponse(
                items=products_list,
                total=total,
                page=page,
                per_page=per_page,
                pages=pages,
                has_next=page < pages,
                has_prev=page > 1
            )
            
            # Get facets (categories, brands, price ranges)
            facets = await get_search_facets(db, q)
            
            return ProductSearchResponse(
                products=product_list,
                facets=facets,
                suggestions=[],  # TODO: Implement search suggestions
                total_results=total,
                search_time_ms=search_time_ms
            )
            
    except Exception as e:
        logger.error(f"Product search failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Search failed"
        )


@router.get("/{product_id}", response_model=ProductDetail)
async def get_product(
    product_id: str,
    current_user: Optional[object] = Depends(get_current_user_optional),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Get product details by ID.
    
    Returns complete product information including category, inventory, reviews, and related products.
    """
    try:
        async with get_db_context() as db:
            # Get product with all related data
            product = await db.execute(
                select(Product)
                .where(Product.id == product_id, Product.is_active == True)
                .options(
                    selectinload(Product.category),
                    selectinload(Product.inventory),
                    selectinload(Product.reviews).selectinload(ProductReview.user),
                    selectinload(Product.promotions)
                )
            )
            product = product.scalar_one_or_none()
            
            if not product:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Product not found"
                )
            
            # Get related products (same category)
            related_products = await db.execute(
                select(Product)
                .where(
                    Product.category_id == product.category_id,
                    Product.id != product.id,
                    Product.is_active == True
                )
                .options(selectinload(Product.inventory))
                .limit(6)
            )
            related_products = related_products.scalars().all()
            
            # Calculate average rating
            if product.reviews:
                average_rating = sum(review.rating for review in product.reviews) / len(product.reviews)
            else:
                average_rating = None
            
            # Log product view in background
            background_tasks.add_task(
                log_product_view,
                product_id=product_id,
                user_id=str(current_user.id) if current_user else None
            )
            
            return ProductDetail(
                **product.__dict__,
                category=product.category,
                inventory=product.inventory,
                reviews=[
                    ProductReviewResponse(
                        **review.__dict__,
                        user_name=f"{review.user.first_name} {review.user.last_name[0]}."
                    ) for review in product.reviews if review.is_approved
                ],
                related_products=related_products,
                average_rating=average_rating,
                review_count=len([r for r in product.reviews if r.is_approved]),
                promotions=product.promotions
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get product: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve product"
        )


@router.post("/{product_id}/reviews", response_model=ProductReviewResponse, status_code=status.HTTP_201_CREATED)
async def create_product_review(
    product_id: str,
    review_data: ProductReviewCreate,
    current_user: object = Depends(get_current_user)
):
    """
    Create a review for a product.
    
    - **rating**: Rating from 1 to 5 stars
    - **title**: Review title (optional)
    - **comment**: Review comment (optional)
    """
    try:
        async with get_db_context() as db:
            # Check if product exists
            product = await db.get(Product, product_id)
            if not product or not product.is_active:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Product not found"
                )
            
            # Check if user has already reviewed this product
            existing_review = await db.execute(
                select(ProductReview).where(
                    ProductReview.product_id == product_id,
                    ProductReview.user_id == current_user.id
                )
            )
            if existing_review.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="You have already reviewed this product"
                )
            
            # Create review
            review = ProductReview(
                product_id=product_id,
                user_id=current_user.id,
                rating=review_data.rating,
                title=review_data.title,
                comment=review_data.comment,
                is_approved=True  # Auto-approve for now
            )
            
            db.add(review)
            await db.commit()
            await db.refresh(review)
            
            logger.info(f"Review created for product {product_id} by user {current_user.email}")
            
            return ProductReviewResponse(
                **review.__dict__,
                user_name=f"{current_user.first_name} {current_user.last_name[0]}."
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create review: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create review"
        )


# Admin endpoints
@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    product_data: ProductCreate,
    admin_user: object = Depends(get_current_admin_user)
):
    """Create a new product (admin only)."""
    try:
        async with get_db_context() as db:
            # Generate slug from title
            from slugify import slugify
            slug = slugify(product_data.title)
            
            # Ensure unique slug
            existing_slug = await db.execute(
                select(Product).where(Product.slug == slug)
            )
            if existing_slug.scalar_one_or_none():
                slug = f"{slug}-{int(datetime.utcnow().timestamp())}"
            
            # Calculate XAF price (placeholder - should use current exchange rate)
            exchange_rate = Decimal('656')  # EUR to XAF
            price_xaf = product_data.price_eur * exchange_rate * (1 + product_data.margin_percentage / 100)
            # Round to nearest 100 XAF
            price_xaf = Decimal(int(price_xaf / 100) * 100)
            
            # Create product
            product = Product(
                **product_data.dict(),
                slug=slug,
                price_xaf=price_xaf
            )
            
            db.add(product)
            await db.commit()
            await db.refresh(product)
            
            # Create inventory record
            inventory = Inventory(
                product_id=product.id,
                quantity=0,
                min_threshold=10
            )
            db.add(inventory)
            await db.commit()
            
            logger.info(f"Product created: {product.title}")
            return product
            
    except Exception as e:
        logger.error(f"Failed to create product: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create product"
        )


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: str,
    product_update: ProductUpdate,
    admin_user: object = Depends(get_current_admin_user)
):
    """Update product (admin only)."""
    try:
        async with get_db_context() as db:
            product = await db.get(Product, product_id)
            if not product:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Product not found"
                )
            
            # Update product fields
            update_data = product_update.dict(exclude_unset=True)
            if update_data:
                # Recalculate XAF price if EUR price or margin changed
                if 'price_eur' in update_data or 'margin_percentage' in update_data:
                    exchange_rate = Decimal('656')  # Should get from settings/API
                    new_price_eur = update_data.get('price_eur', product.price_eur)
                    new_margin = update_data.get('margin_percentage', product.margin_percentage)
                    
                    price_xaf = new_price_eur * exchange_rate * (1 + new_margin / 100)
                    price_xaf = Decimal(int(price_xaf / 100) * 100)
                    update_data['price_xaf'] = price_xaf
                
                await db.execute(
                    update(Product)
                    .where(Product.id == product_id)
                    .values(**update_data, updated_at=datetime.utcnow())
                )
                await db.commit()
                
                # Refresh product
                await db.refresh(product)
            
            logger.info(f"Product updated: {product.title}")
            return product
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update product: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update product"
        )


@router.delete("/{product_id}", response_model=BaseResponse)
async def delete_product(
    product_id: str,
    admin_user: object = Depends(get_current_admin_user)
):
    """Soft delete product (admin only)."""
    try:
        async with get_db_context() as db:
            result = await db.execute(
                update(Product)
                .where(Product.id == product_id)
                .values(is_active=False, updated_at=datetime.utcnow())
            )
            await db.commit()
            
            if result.rowcount == 0:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Product not found"
                )
            
            logger.info(f"Product deleted: {product_id}")
            return BaseResponse(message="Product deleted successfully")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete product: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete product"
        )


@router.get("/{product_id}/inventory", response_model=InventoryResponse)
async def get_product_inventory(
    product_id: str,
    admin_user: object = Depends(get_current_admin_user)
):
    """Get product inventory (admin only)."""
    async with get_db_context() as db:
        inventory = await db.execute(
            select(Inventory).where(Inventory.product_id == product_id)
        )
        inventory = inventory.scalar_one_or_none()
        
        if not inventory:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Inventory not found"
            )
        
        return inventory


@router.put("/{product_id}/inventory", response_model=InventoryResponse)
async def update_product_inventory(
    product_id: str,
    inventory_update: InventoryUpdate,
    admin_user: object = Depends(get_current_admin_user)
):
    """Update product inventory (admin only)."""
    try:
        async with get_db_context() as db:
            # Update inventory
            update_data = inventory_update.dict(exclude_unset=True)
            if update_data:
                result = await db.execute(
                    update(Inventory)
                    .where(Inventory.product_id == product_id)
                    .values(**update_data, last_updated=datetime.utcnow())
                )
                await db.commit()
                
                if result.rowcount == 0:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Inventory not found"
                    )
            
            # Get updated inventory
            inventory = await db.execute(
                select(Inventory).where(Inventory.product_id == product_id)
            )
            inventory = inventory.scalar_one()
            
            logger.info(f"Inventory updated for product: {product_id}")
            return inventory
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update inventory: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update inventory"
        )


# Helper functions
async def get_search_facets(db: AsyncSession, query: str) -> dict:
    """Get search facets for filtering."""
    # Get category facets
    category_facets = await db.execute(
        select(Category.id, Category.name, func.count(Product.id).label('count'))
        .join(Product)
        .where(
            Product.is_active == True,
            or_(
                Product.title.ilike(f"%{query}%"),
                Product.description.ilike(f"%{query}%")
            )
        )
        .group_by(Category.id, Category.name)
        .order_by(func.count(Product.id).desc())
        .limit(10)
    )
    
    # Get brand facets
    brand_facets = await db.execute(
        select(Product.brand, func.count(Product.id).label('count'))
        .where(
            Product.is_active == True,
            Product.brand.isnot(None),
            or_(
                Product.title.ilike(f"%{query}%"),
                Product.description.ilike(f"%{query}%")
            )
        )
        .group_by(Product.brand)
        .order_by(func.count(Product.id).desc())
        .limit(10)
    )
    
    return {
        "categories": [
            {"id": cat.id, "name": cat.name, "count": cat.count}
            for cat in category_facets.all()
        ],
        "brands": [
            {"name": brand.brand, "count": brand.count}
            for brand in brand_facets.all()
        ]
    }


async def log_search_analytics(query: str, user_id: Optional[str], results_count: int, search_time_ms: int):
    """Log search analytics (background task)."""
    try:
        async with get_db_context() as db:
            analytics = SearchAnalytic(
                query=query,
                user_id=user_id,
                results_count=results_count,
                search_duration_ms=search_time_ms
            )
            db.add(analytics)
            await db.commit()
    except Exception as e:
        logger.error(f"Failed to log search analytics: {e}")


async def log_product_view(product_id: str, user_id: Optional[str]):
    """Log product view (background task)."""
    try:
        async with get_db_context() as db:
            view = ProductView(
                product_id=product_id,
                user_id=user_id
            )
            db.add(view)
            await db.commit()
    except Exception as e:
        logger.error(f"Failed to log product view: {e}")


# Import required modules at the end to avoid circular imports
from datetime import datetime
