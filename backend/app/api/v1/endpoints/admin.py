"""
Admin endpoints for PromoWeb Africa.
Handles administrative functions, system management, and bulk operations.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func, text
from sqlalchemy.orm import selectinload
from datetime import datetime, timedelta

from app.api.dependencies import (
    get_current_admin_user, get_current_super_admin_user, 
    get_pagination_params, get_db_session
)
from app.models.user import User
from app.models.product import Product, Category, Inventory
from app.models.order import Order
from app.schemas.common import BaseResponse, PaginatedResponse
from app.schemas.product import ProductBulkUpdate, ProductExport
from app.schemas.order import OrderBulkStatusUpdate, OrderExport
from app.core.database import get_db_context
from app.core.config import get_settings
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/stats", response_model=Dict[str, Any])
async def get_admin_stats(admin_user: User = Depends(get_current_admin_user)):
    """
    Get comprehensive admin statistics.
    
    Returns key metrics and counts for the admin dashboard.
    """
    try:
        async with get_db_context() as db:
            # Users statistics
            total_users = await db.execute(select(func.count(User.id)))
            active_users = await db.execute(
                select(func.count(User.id)).where(User.is_active == True)
            )
            new_users_today = await db.execute(
                select(func.count(User.id)).where(
                    func.date(User.created_at) == func.date(datetime.utcnow())
                )
            )
            
            # Products statistics
            total_products = await db.execute(select(func.count(Product.id)))
            active_products = await db.execute(
                select(func.count(Product.id)).where(Product.is_active == True)
            )
            low_stock_products = await db.execute(
                select(func.count(Inventory.id)).where(
                    Inventory.quantity <= Inventory.min_threshold
                )
            )
            
            # Orders statistics
            total_orders = await db.execute(select(func.count(Order.id)))
            orders_today = await db.execute(
                select(func.count(Order.id)).where(
                    func.date(Order.created_at) == func.date(datetime.utcnow())
                )
            )
            pending_orders = await db.execute(
                select(func.count(Order.id)).where(
                    Order.status.in_(['pending', 'processing'])
                )
            )
            
            # Revenue statistics
            total_revenue = await db.execute(
                select(func.coalesce(func.sum(Order.total_amount), 0)).where(
                    Order.status.in_(['completed', 'delivered', 'paid_full'])
                )
            )
            revenue_today = await db.execute(
                select(func.coalesce(func.sum(Order.total_amount), 0)).where(
                    func.date(Order.created_at) == func.date(datetime.utcnow()),
                    Order.status.in_(['completed', 'delivered', 'paid_full'])
                )
            )
            
            # Categories statistics
            total_categories = await db.execute(select(func.count(Category.id)))
            
            return {
                "users": {
                    "total": total_users.scalar(),
                    "active": active_users.scalar(),
                    "new_today": new_users_today.scalar()
                },
                "products": {
                    "total": total_products.scalar(),
                    "active": active_products.scalar(),
                    "low_stock": low_stock_products.scalar()
                },
                "orders": {
                    "total": total_orders.scalar(),
                    "today": orders_today.scalar(),
                    "pending": pending_orders.scalar()
                },
                "revenue": {
                    "total": float(total_revenue.scalar()),
                    "today": float(revenue_today.scalar())
                },
                "categories": {
                    "total": total_categories.scalar()
                }
            }
            
    except Exception as e:
        logger.error(f"Failed to get admin stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve admin statistics"
        )


@router.get("/system/info", response_model=Dict[str, Any])
async def get_system_info(admin_user: User = Depends(get_current_super_admin_user)):
    """
    Get system information and health status (super admin only).
    
    Returns database status, Redis status, and other system metrics.
    """
    try:
        settings = get_settings()
        
        # Database health check
        database_status = "healthy"
        try:
            async with get_db_context() as db:
                await db.execute(text("SELECT 1"))
        except Exception as e:
            database_status = f"unhealthy: {str(e)}"
        
        # Redis health check
        redis_status = "healthy"
        try:
            from app.core.redis import get_cache
            cache = get_cache()
            await cache.ping()
        except Exception as e:
            redis_status = f"unhealthy: {str(e)}"
        
        return {
            "application": {
                "name": "PromoWeb Africa API",
                "version": "1.0.0",
                "environment": settings.ENVIRONMENT,
                "debug": settings.DEBUG
            },
            "database": {
                "status": database_status,
                "url": settings.DATABASE_URL.replace(settings.DATABASE_PASSWORD, "***") if settings.DATABASE_PASSWORD else settings.DATABASE_URL
            },
            "redis": {
                "status": redis_status,
                "url": settings.REDIS_URL.replace("@", "@***") if "@" in settings.REDIS_URL else settings.REDIS_URL
            },
            "server": {
                "host": settings.HOST,
                "port": settings.PORT,
                "cors_origins": settings.CORS_ORIGINS
            },
            "features": {
                "jwt_auth": True,
                "file_uploads": True,
                "email_notifications": False,  # Would be True when implemented
                "sms_notifications": False     # Would be True when implemented
            },
            "uptime": "Running",  # Would calculate actual uptime
            "timestamp": datetime.utcnow()
        }
        
    except Exception as e:
        logger.error(f"Failed to get system info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve system information"
        )


@router.post("/products/bulk-update", response_model=BaseResponse)
async def bulk_update_products(
    bulk_update: ProductBulkUpdate,
    admin_user: User = Depends(get_current_admin_user)
):
    """
    Bulk update multiple products (admin only).
    
    - **product_ids**: List of product IDs to update
    - **updates**: Fields to update on selected products
    """
    try:
        async with get_db_context() as db:
            # Verify all products exist and are owned by the system
            products = await db.execute(
                select(Product).where(Product.id.in_(bulk_update.product_ids))
            )
            found_products = products.scalars().all()
            
            if len(found_products) != len(bulk_update.product_ids):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Some products not found"
                )
            
            # Prepare update data
            update_data = bulk_update.updates.dict(exclude_unset=True)
            if not update_data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No update fields provided"
                )
            
            update_data['updated_at'] = datetime.utcnow()
            
            # Perform bulk update
            result = await db.execute(
                update(Product)
                .where(Product.id.in_(bulk_update.product_ids))
                .values(**update_data)
            )
            
            await db.commit()
            
            logger.info(f"Bulk updated {result.rowcount} products by admin {admin_user.email}")
            
            return BaseResponse(
                message=f"Successfully updated {result.rowcount} products"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Bulk product update failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Bulk update failed"
        )


@router.post("/orders/bulk-status-update", response_model=BaseResponse)
async def bulk_update_order_status(
    bulk_update: OrderBulkStatusUpdate,
    admin_user: User = Depends(get_current_admin_user)
):
    """
    Bulk update order status (admin only).
    
    - **order_ids**: List of order IDs to update
    - **status**: New status for all orders
    - **notes**: Optional notes for the status change
    """
    try:
        async with get_db_context() as db:
            # Verify all orders exist
            orders = await db.execute(
                select(Order).where(Order.id.in_(bulk_update.order_ids))
            )
            found_orders = orders.scalars().all()
            
            if len(found_orders) != len(bulk_update.order_ids):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Some orders not found"
                )
            
            # Update each order (to trigger status change logic)
            updated_count = 0
            for order in found_orders:
                try:
                    order.change_status(
                        bulk_update.status,
                        bulk_update.notes or f"Bulk status update to {bulk_update.status}",
                        str(admin_user.id)
                    )
                    updated_count += 1
                except Exception as e:
                    logger.warning(f"Failed to update order {order.id}: {e}")
            
            await db.commit()
            
            logger.info(f"Bulk updated {updated_count} orders by admin {admin_user.email}")
            
            return BaseResponse(
                message=f"Successfully updated {updated_count} of {len(bulk_update.order_ids)} orders"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Bulk order status update failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Bulk status update failed"
        )


@router.post("/inventory/sync", response_model=BaseResponse)
async def sync_inventory(
    admin_user: User = Depends(get_current_admin_user),
    force: bool = Query(False, description="Force sync even if recently synced")
):
    """
    Sync inventory levels with external systems (admin only).
    
    - **force**: Force synchronization even if recently synced
    """
    try:
        async with get_db_context() as db:
            # Get all products with inventory
            products = await db.execute(
                select(Product)
                .options(selectinload(Product.inventory))
                .where(Product.is_active == True)
            )
            
            synced_count = 0
            error_count = 0
            
            for product in products.scalars().all():
                try:
                    if product.inventory:
                        # This would integrate with external inventory systems
                        # For now, just update the sync timestamp
                        product.inventory.last_sync_at = datetime.utcnow()
                        synced_count += 1
                except Exception as e:
                    logger.warning(f"Failed to sync inventory for product {product.id}: {e}")
                    error_count += 1
            
            await db.commit()
            
            logger.info(f"Inventory sync completed: {synced_count} success, {error_count} errors")
            
            return BaseResponse(
                message=f"Inventory sync completed. {synced_count} products synced, {error_count} errors"
            )
            
    except Exception as e:
        logger.error(f"Inventory sync failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Inventory sync failed"
        )


@router.post("/data/export", response_model=Dict[str, Any])
async def export_data(
    export_type: str = Query(..., regex="^(products|orders|users|analytics)$"),
    format: str = Query("csv", regex="^(csv|xlsx|json)$"),
    admin_user: User = Depends(get_current_admin_user)
):
    """
    Export data in various formats (admin only).
    
    - **export_type**: Type of data to export (products, orders, users, analytics)
    - **format**: Export format (csv, xlsx, json)
    """
    try:
        # Generate export ID
        import uuid
        export_id = str(uuid.uuid4())
        
        # This would implement actual data export logic
        # For now, return a mock response
        
        logger.info(f"Data export initiated by admin {admin_user.email}: {export_type} as {format}")
        
        return {
            "export_id": export_id,
            "status": "initiated",
            "export_type": export_type,
            "format": format,
            "estimated_completion": datetime.utcnow() + timedelta(minutes=5),
            "download_url": None,  # Would be populated when export is complete
            "message": f"Export of {export_type} data initiated. You will be notified when ready."
        }
        
    except Exception as e:
        logger.error(f"Data export failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Data export failed"
        )


@router.post("/maintenance/cleanup", response_model=BaseResponse)
async def run_maintenance_cleanup(
    admin_user: User = Depends(get_current_super_admin_user),
    cleanup_expired_carts: bool = Query(True),
    cleanup_old_sessions: bool = Query(True),
    cleanup_old_analytics: bool = Query(False)
):
    """
    Run maintenance cleanup tasks (super admin only).
    
    - **cleanup_expired_carts**: Remove expired anonymous carts
    - **cleanup_old_sessions**: Remove old inactive sessions
    - **cleanup_old_analytics**: Remove old analytics data (>1 year)
    """
    try:
        async with get_db_context() as db:
            cleanup_results = []
            
            if cleanup_expired_carts:
                # Clean up expired carts
                from app.models.cart import Cart
                result = await db.execute(
                    select(Cart).where(
                        Cart.expires_at < datetime.utcnow(),
                        Cart.user_id.is_(None)  # Only anonymous carts
                    )
                )
                expired_carts = result.scalars().all()
                
                for cart in expired_carts:
                    await db.delete(cart)
                
                cleanup_results.append(f"Removed {len(expired_carts)} expired carts")
            
            if cleanup_old_sessions:
                # Clean up old sessions (>30 days inactive)
                from app.models.user import UserSession
                cutoff_date = datetime.utcnow() - timedelta(days=30)
                
                result = await db.execute(
                    update(UserSession)
                    .where(
                        UserSession.last_activity < cutoff_date,
                        UserSession.is_active == True
                    )
                    .values(is_active=False)
                )
                
                cleanup_results.append(f"Deactivated {result.rowcount} old sessions")
            
            if cleanup_old_analytics:
                # Clean up old analytics data
                from app.models.analytics import ProductView, SearchAnalytic
                cutoff_date = datetime.utcnow() - timedelta(days=365)
                
                # Remove old product views
                old_views = await db.execute(
                    select(ProductView).where(ProductView.created_at < cutoff_date)
                )
                view_count = len(old_views.scalars().all())
                
                for view in old_views.scalars().all():
                    await db.delete(view)
                
                # Remove old search analytics
                old_searches = await db.execute(
                    select(SearchAnalytic).where(SearchAnalytic.created_at < cutoff_date)
                )
                search_count = len(old_searches.scalars().all())
                
                for search in old_searches.scalars().all():
                    await db.delete(search)
                
                cleanup_results.append(f"Removed {view_count} old product views and {search_count} old searches")
            
            await db.commit()
            
            logger.info(f"Maintenance cleanup completed by {admin_user.email}: {cleanup_results}")
            
            return BaseResponse(
                message=f"Maintenance cleanup completed: {'; '.join(cleanup_results)}"
            )
            
    except Exception as e:
        logger.error(f"Maintenance cleanup failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Maintenance cleanup failed"
        )


@router.get("/logs", response_model=Dict[str, Any])
async def get_system_logs(
    admin_user: User = Depends(get_current_super_admin_user),
    level: str = Query("INFO", regex="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$"),
    limit: int = Query(100, ge=1, le=1000),
    hours: int = Query(24, ge=1, le=168)
):
    """
    Get recent system logs (super admin only).
    
    - **level**: Minimum log level to retrieve
    - **limit**: Maximum number of log entries
    - **hours**: Number of hours to look back
    """
    try:
        # This would integrate with actual logging system
        # For now, return mock log data
        
        since = datetime.utcnow() - timedelta(hours=hours)
        
        mock_logs = [
            {
                "timestamp": datetime.utcnow() - timedelta(minutes=5),
                "level": "INFO",
                "module": "auth.service",
                "message": "User login successful",
                "user_id": "user_123"
            },
            {
                "timestamp": datetime.utcnow() - timedelta(minutes=15),
                "level": "WARNING",
                "module": "payment.gateway",
                "message": "Payment gateway timeout, retrying",
                "transaction_id": "txn_456"
            },
            {
                "timestamp": datetime.utcnow() - timedelta(minutes=30),
                "level": "ERROR",
                "module": "inventory.sync",
                "message": "Failed to sync product inventory",
                "product_id": "prod_789"
            }
        ]
        
        # Filter by level
        level_priority = {"DEBUG": 0, "INFO": 1, "WARNING": 2, "ERROR": 3, "CRITICAL": 4}
        min_priority = level_priority.get(level, 1)
        
        filtered_logs = [
            log for log in mock_logs 
            if level_priority.get(log["level"], 0) >= min_priority
        ]
        
        return {
            "logs": filtered_logs[:limit],
            "total_found": len(filtered_logs),
            "level_filter": level,
            "time_range_hours": hours,
            "generated_at": datetime.utcnow()
        }
        
    except Exception as e:
        logger.error(f"Failed to get system logs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve system logs"
        )


@router.post("/cache/clear", response_model=BaseResponse)
async def clear_cache(
    admin_user: User = Depends(get_current_super_admin_user),
    cache_type: str = Query("all", regex="^(all|user_sessions|product_cache|search_cache)$")
):
    """
    Clear application cache (super admin only).
    
    - **cache_type**: Type of cache to clear (all, user_sessions, product_cache, search_cache)
    """
    try:
        from app.core.redis import get_cache
        cache = get_cache()
        
        cleared_keys = 0
        
        if cache_type == "all":
            # Clear all cache
            await cache.flushall()
            cleared_keys = "all"
        else:
            # Clear specific cache patterns
            pattern_map = {
                "user_sessions": "user_session:*",
                "product_cache": "product:*",
                "search_cache": "search:*"
            }
            
            pattern = pattern_map.get(cache_type)
            if pattern:
                keys = await cache.keys(pattern)
                if keys:
                    await cache.delete(*keys)
                    cleared_keys = len(keys)
        
        logger.info(f"Cache cleared by admin {admin_user.email}: {cache_type} ({cleared_keys} keys)")
        
        return BaseResponse(
            message=f"Cache cleared successfully: {cache_type} ({cleared_keys} keys)"
        )
        
    except Exception as e:
        logger.error(f"Failed to clear cache: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clear cache"
        )


@router.get("/health", response_model=Dict[str, Any])
async def health_check():
    """
    Health check endpoint (no authentication required).
    
    Returns basic system health status.
    """
    try:
        # Basic health checks
        health_status = {
            "status": "healthy",
            "timestamp": datetime.utcnow(),
            "version": "1.0.0",
            "checks": {}
        }
        
        # Database check
        try:
            async with get_db_context() as db:
                await db.execute(text("SELECT 1"))
            health_status["checks"]["database"] = "healthy"
        except Exception as e:
            health_status["checks"]["database"] = f"unhealthy: {str(e)}"
            health_status["status"] = "degraded"
        
        # Redis check
        try:
            from app.core.redis import get_cache
            cache = get_cache()
            await cache.ping()
            health_status["checks"]["redis"] = "healthy"
        except Exception as e:
            health_status["checks"]["redis"] = f"unhealthy: {str(e)}"
            health_status["status"] = "degraded"
        
        return health_status
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow(),
            "error": str(e)
        }
