"""
Category endpoints for PromoWeb Africa.
Handles product category management and hierarchy.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from sqlalchemy.orm import selectinload

from app.api.dependencies import get_current_admin_user, get_db_session
from app.models.product import Category, Product
from app.schemas.product import (
    CategoryResponse, CategoryTree, CategoryCreate, CategoryUpdate
)
from app.schemas.common import BaseResponse
from app.core.database import get_db_context
from slugify import slugify
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_model=List[CategoryResponse])
async def list_categories(
    parent_id: Optional[str] = Query(None, description="Filter by parent category"),
    include_inactive: bool = Query(False, description="Include inactive categories"),
    flat: bool = Query(False, description="Return flat list instead of hierarchy")
):
    """
    List all categories.
    
    - **parent_id**: Filter by parent category (None for root categories)
    - **include_inactive**: Include inactive categories
    - **flat**: Return flat list instead of hierarchy
    """
    try:
        async with get_db_context() as db:
            # Build query
            query = select(Category)
            
            if not include_inactive:
                query = query.where(Category.is_active == True)
            
            if parent_id is not None:
                query = query.where(Category.parent_id == parent_id)
            elif not flat:
                # For hierarchy view, get root categories only
                query = query.where(Category.parent_id.is_(None))
            
            # Order by sort_order and name
            query = query.order_by(Category.sort_order.asc(), Category.name.asc())
            
            categories = await db.execute(query)
            categories_list = categories.scalars().all()
            
            # Add product counts
            result = []
            for category in categories_list:
                category_dict = category.__dict__.copy()
                category_dict['product_count'] = category.get_product_count()
                result.append(CategoryResponse(**category_dict))
            
            return result
            
    except Exception as e:
        logger.error(f"Failed to list categories: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve categories"
        )


@router.get("/tree", response_model=List[CategoryTree])
async def get_category_tree(include_inactive: bool = Query(False)):
    """
    Get complete category tree with nested children.
    
    - **include_inactive**: Include inactive categories
    """
    try:
        async with get_db_context() as db:
            # Get all categories
            query = select(Category)
            if not include_inactive:
                query = query.where(Category.is_active == True)
            
            query = query.order_by(Category.sort_order.asc(), Category.name.asc())
            categories = await db.execute(query)
            categories_list = categories.scalars().all()
            
            # Build tree structure
            category_map = {}
            root_categories = []
            
            # First pass: create all category objects
            for category in categories_list:
                category_tree = CategoryTree(
                    **category.__dict__,
                    product_count=category.get_product_count(),
                    children=[]
                )
                category_map[str(category.id)] = category_tree
                
                if category.parent_id is None:
                    root_categories.append(category_tree)
            
            # Second pass: build parent-child relationships
            for category in categories_list:
                if category.parent_id is not None:
                    parent = category_map.get(str(category.parent_id))
                    if parent:
                        parent.children.append(category_map[str(category.id)])
            
            return root_categories
            
    except Exception as e:
        logger.error(f"Failed to get category tree: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve category tree"
        )


@router.get("/{category_id}", response_model=CategoryResponse)
async def get_category(category_id: str):
    """Get category by ID."""
    try:
        async with get_db_context() as db:
            category = await db.execute(
                select(Category)
                .where(Category.id == category_id)
                .options(selectinload(Category.parent), selectinload(Category.children))
            )
            category = category.scalar_one_or_none()
            
            if not category:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Category not found"
                )
            
            return CategoryResponse(
                **category.__dict__,
                product_count=category.get_product_count()
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get category: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve category"
        )


@router.get("/{category_id}/products", response_model=dict)
async def get_category_products(
    category_id: str,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    include_subcategories: bool = Query(True, description="Include products from subcategories")
):
    """
    Get products in a category.
    
    - **include_subcategories**: Include products from child categories
    """
    try:
        async with get_db_context() as db:
            # Verify category exists
            category = await db.get(Category, category_id)
            if not category:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Category not found"
                )
            
            # Build product query
            if include_subcategories:
                # Get all descendant category IDs
                all_category_ids = [category_id]
                children = category.get_all_children()
                all_category_ids.extend([str(child.id) for child in children])
                
                query = select(Product).where(
                    Product.category_id.in_(all_category_ids),
                    Product.is_active == True
                )
            else:
                query = select(Product).where(
                    Product.category_id == category_id,
                    Product.is_active == True
                )
            
            # Get total count
            count_query = select(func.count()).select_from(query.subquery())
            total = await db.execute(count_query)
            total = total.scalar()
            
            # Get paginated products
            products = await db.execute(
                query.options(selectinload(Product.inventory))
                .order_by(Product.created_at.desc())
                .offset((page - 1) * per_page)
                .limit(per_page)
            )
            
            products_list = products.scalars().all()
            
            # Calculate pagination
            pages = (total + per_page - 1) // per_page
            
            return {
                "category": CategoryResponse(**category.__dict__, product_count=category.get_product_count()),
                "products": {
                    "items": products_list,
                    "total": total,
                    "page": page,
                    "per_page": per_page,
                    "pages": pages,
                    "has_next": page < pages,
                    "has_prev": page > 1
                }
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get category products: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve category products"
        )


# Admin endpoints
@router.post("/", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    category_data: CategoryCreate,
    admin_user: object = Depends(get_current_admin_user)
):
    """Create a new category (admin only)."""
    try:
        async with get_db_context() as db:
            # Generate slug from name
            slug = slugify(category_data.name)
            
            # Ensure unique slug
            existing_slug = await db.execute(
                select(Category).where(Category.slug == slug)
            )
            if existing_slug.scalar_one_or_none():
                slug = f"{slug}-{int(datetime.utcnow().timestamp())}"
            
            # Verify parent category exists if specified
            if category_data.parent_id:
                parent = await db.get(Category, category_data.parent_id)
                if not parent:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Parent category not found"
                    )
            
            # Create category
            category = Category(
                **category_data.dict(),
                slug=slug
            )
            
            db.add(category)
            await db.commit()
            await db.refresh(category)
            
            logger.info(f"Category created: {category.name}")
            return CategoryResponse(
                **category.__dict__,
                product_count=0
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create category: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create category"
        )


@router.put("/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: str,
    category_update: CategoryUpdate,
    admin_user: object = Depends(get_current_admin_user)
):
    """Update category (admin only)."""
    try:
        async with get_db_context() as db:
            category = await db.get(Category, category_id)
            if not category:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Category not found"
                )
            
            # Verify parent category exists if specified
            if category_update.parent_id:
                # Prevent circular references
                if category_update.parent_id == category_id:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Category cannot be its own parent"
                    )
                
                parent = await db.get(Category, category_update.parent_id)
                if not parent:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Parent category not found"
                    )
                
                # Check if new parent would create a circular reference
                current_parent = parent
                while current_parent.parent_id:
                    if str(current_parent.parent_id) == category_id:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Circular reference detected"
                        )
                    current_parent = await db.get(Category, current_parent.parent_id)
                    if not current_parent:
                        break
            
            # Update category
            update_data = category_update.dict(exclude_unset=True)
            if update_data:
                # Update slug if name changed
                if 'name' in update_data:
                    new_slug = slugify(update_data['name'])
                    if new_slug != category.slug:
                        # Check if new slug is unique
                        existing_slug = await db.execute(
                            select(Category).where(
                                Category.slug == new_slug,
                                Category.id != category_id
                            )
                        )
                        if existing_slug.scalar_one_or_none():
                            new_slug = f"{new_slug}-{int(datetime.utcnow().timestamp())}"
                        update_data['slug'] = new_slug
                
                await db.execute(
                    update(Category)
                    .where(Category.id == category_id)
                    .values(**update_data, updated_at=datetime.utcnow())
                )
                await db.commit()
                
                # Refresh category
                await db.refresh(category)
            
            logger.info(f"Category updated: {category.name}")
            return CategoryResponse(
                **category.__dict__,
                product_count=category.get_product_count()
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update category: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update category"
        )


@router.delete("/{category_id}", response_model=BaseResponse)
async def delete_category(
    category_id: str,
    admin_user: object = Depends(get_current_admin_user)
):
    """
    Delete category (admin only).
    
    Categories with products or subcategories will be soft deleted (marked inactive).
    Empty categories will be hard deleted.
    """
    try:
        async with get_db_context() as db:
            category = await db.execute(
                select(Category)
                .where(Category.id == category_id)
                .options(selectinload(Category.children))
            )
            category = category.scalar_one_or_none()
            
            if not category:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Category not found"
                )
            
            # Check for products in this category
            product_count = await db.execute(
                select(func.count(Product.id)).where(Product.category_id == category_id)
            )
            product_count = product_count.scalar()
            
            # Check for subcategories
            has_children = len(category.children) > 0
            
            if product_count > 0 or has_children:
                # Soft delete - mark as inactive
                await db.execute(
                    update(Category)
                    .where(Category.id == category_id)
                    .values(is_active=False, updated_at=datetime.utcnow())
                )
                await db.commit()
                
                logger.info(f"Category soft deleted: {category.name}")
                return BaseResponse(
                    message=f"Category marked as inactive (has {product_count} products and {len(category.children)} subcategories)"
                )
            else:
                # Hard delete - completely remove
                await db.delete(category)
                await db.commit()
                
                logger.info(f"Category hard deleted: {category.name}")
                return BaseResponse(message="Category deleted successfully")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete category: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete category"
        )


@router.post("/{category_id}/reorder", response_model=BaseResponse)
async def reorder_categories(
    category_id: str,
    new_sort_order: int = Query(..., ge=0),
    admin_user: object = Depends(get_current_admin_user)
):
    """Update category sort order (admin only)."""
    try:
        async with get_db_context() as db:
            result = await db.execute(
                update(Category)
                .where(Category.id == category_id)
                .values(sort_order=new_sort_order, updated_at=datetime.utcnow())
            )
            await db.commit()
            
            if result.rowcount == 0:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Category not found"
                )
            
            logger.info(f"Category sort order updated: {category_id} -> {new_sort_order}")
            return BaseResponse(message="Category order updated successfully")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to reorder category: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update category order"
        )


# Import required modules
from datetime import datetime
