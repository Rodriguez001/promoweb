"""
Analytics endpoints for PromoWeb Africa.
Handles analytics, reporting, and business intelligence.
"""

from typing import List, Optional
from datetime import datetime, date, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload

from app.api.dependencies import get_current_admin_user, get_db_session
from app.models.analytics import (
    SearchAnalytic, ProductView, ConversionFunnel, PerformanceMetric
)
from app.models.product import Product
from app.models.order import Order
from app.models.user import User
from app.schemas.analytics import (
    DashboardOverview, KPIMetric, SalesAnalyticsResponse, SalesMetrics,
    ProductAnalyticsResponse, UserAnalyticsResponse, SearchTrends,
    RealTimeMetrics, AnalyticsPeriod
)
from app.schemas.common import BaseResponse
from app.core.database import get_db_context
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/dashboard", response_model=DashboardOverview)
async def get_dashboard_overview(
    admin_user: object = Depends(get_current_admin_user),
    period: AnalyticsPeriod = Query(AnalyticsPeriod.DAILY, description="Time period for metrics")
):
    """
    Get dashboard overview with key metrics.
    
    Returns KPIs, recent activity, and quick stats for admin dashboard.
    """
    try:
        async with get_db_context() as db:
            # Calculate date range based on period
            now = datetime.utcnow()
            if period == AnalyticsPeriod.DAILY:
                start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
                previous_start = start_date - timedelta(days=1)
            elif period == AnalyticsPeriod.WEEKLY:
                start_date = now - timedelta(days=7)
                previous_start = start_date - timedelta(days=7)
            elif period == AnalyticsPeriod.MONTHLY:
                start_date = now - timedelta(days=30)
                previous_start = start_date - timedelta(days=30)
            else:
                start_date = now - timedelta(days=1)
                previous_start = start_date - timedelta(days=1)
            
            # Get current period metrics
            current_metrics = await get_period_metrics(db, start_date, now)
            previous_metrics = await get_period_metrics(db, previous_start, start_date)
            
            # Calculate KPIs with change percentages
            kpis = []
            
            for metric_name, current_value in current_metrics.items():
                previous_value = previous_metrics.get(metric_name, 0)
                
                # Calculate change percentage
                change_percentage = None
                trend = None
                if previous_value > 0:
                    change_percentage = ((current_value - previous_value) / previous_value) * 100
                    trend = "up" if change_percentage > 0 else "down" if change_percentage < 0 else "stable"
                
                # Format value based on metric type
                if metric_name in ['revenue', 'avg_order_value']:
                    formatted_value = f"{current_value:,.0f} XAF"
                elif metric_name in ['conversion_rate']:
                    formatted_value = f"{current_value:.1f}%"
                else:
                    formatted_value = f"{current_value:,.0f}"
                
                kpis.append(KPIMetric(
                    name=metric_name.replace('_', ' ').title(),
                    value=current_value,
                    formatted_value=formatted_value,
                    change_percentage=change_percentage,
                    trend=trend
                ))
            
            # Get recent orders
            recent_orders = await db.execute(
                select(Order)
                .options(selectinload(Order.user))
                .order_by(Order.created_at.desc())
                .limit(10)
            )
            
            recent_orders_data = []
            for order in recent_orders.scalars().all():
                recent_orders_data.append({
                    "id": str(order.id),
                    "order_number": order.order_number,
                    "customer_name": f"{order.user.first_name} {order.user.last_name}",
                    "total_amount": float(order.total_amount),
                    "status": order.status,
                    "created_at": order.created_at
                })
            
            # Get top products
            top_products = await get_top_products(db, start_date, now)
            
            # Traffic sources (mock data for now)
            traffic_sources = {
                "Direct": 45,
                "Google Search": 30,
                "Social Media": 15,
                "Email": 10
            }
            
            # System alerts
            alerts = await get_system_alerts(db)
            
            # Quick stats
            quick_stats = {
                "active_users_today": current_metrics.get("active_users", 0),
                "orders_processing": current_metrics.get("processing_orders", 0),
                "low_stock_products": await get_low_stock_count(db),
                "pending_payments": current_metrics.get("pending_payments", 0)
            }
            
            return DashboardOverview(
                kpis=kpis,
                recent_orders=recent_orders_data,
                top_products=top_products,
                traffic_sources=traffic_sources,
                alerts=alerts,
                quick_stats=quick_stats,
                period_start=start_date.date(),
                period_end=now.date()
            )
            
    except Exception as e:
        logger.error(f"Failed to get dashboard overview: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve dashboard data"
        )


@router.get("/sales", response_model=SalesAnalyticsResponse)
async def get_sales_analytics(
    admin_user: object = Depends(get_current_admin_user),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    period: AnalyticsPeriod = Query(AnalyticsPeriod.DAILY)
):
    """
    Get sales analytics data.
    
    - **date_from**: Start date for analysis
    - **date_to**: End date for analysis
    - **period**: Aggregation period (daily, weekly, monthly)
    """
    try:
        # Set default date range if not provided
        if not date_to:
            date_to = datetime.utcnow().date()
        if not date_from:
            if period == AnalyticsPeriod.DAILY:
                date_from = date_to - timedelta(days=30)
            elif period == AnalyticsPeriod.WEEKLY:
                date_from = date_to - timedelta(days=90)
            else:  # monthly
                date_from = date_to - timedelta(days=365)
        
        async with get_db_context() as db:
            # Get overall sales metrics
            sales_query = await db.execute(
                select(
                    func.sum(Order.total_amount).label('total_revenue'),
                    func.count(Order.id).label('total_orders'),
                    func.avg(Order.total_amount).label('avg_order_value'),
                    func.sum(func.case([(Order.status == 'refunded', Order.total_amount)], else_=0)).label('refunded_amount')
                )
                .where(
                    and_(
                        Order.created_at >= date_from,
                        Order.created_at <= date_to,
                        Order.status.in_(['completed', 'delivered', 'paid_full'])
                    )
                )
            )
            sales_data = sales_query.first()
            
            # Calculate metrics
            total_revenue = sales_data.total_revenue or 0
            total_orders = sales_data.total_orders or 0
            avg_order_value = sales_data.avg_order_value or 0
            refunded_amount = sales_data.refunded_amount or 0
            
            # Get total items sold
            items_sold_query = await db.execute(
                select(func.sum(Order.total_items))
                .where(
                    and_(
                        Order.created_at >= date_from,
                        Order.created_at <= date_to,
                        Order.status.in_(['completed', 'delivered', 'paid_full'])
                    )
                )
            )
            total_items_sold = items_sold_query.scalar() or 0
            
            # Calculate conversion rate (orders / unique visitors)
            # This is simplified - in a real system you'd track visitors properly
            conversion_rate = 5.2  # Mock conversion rate
            refund_rate = (refunded_amount / total_revenue * 100) if total_revenue > 0 else 0
            
            metrics = SalesMetrics(
                total_revenue=total_revenue,
                total_orders=total_orders,
                average_order_value=avg_order_value,
                total_items_sold=total_items_sold,
                conversion_rate=conversion_rate,
                refund_rate=refund_rate,
                tax_collected=total_revenue * Decimal('0.1925'),  # 19.25% VAT
                shipping_revenue=0  # Would calculate from shipping costs
            )
            
            # Get sales by period
            sales_by_period = await get_sales_by_period(db, date_from, date_to, period)
            
            # Get sales by category
            sales_by_category = await get_sales_by_category(db, date_from, date_to)
            
            # Get sales by payment method (mock data)
            sales_by_payment_method = {
                "Orange Money": float(total_revenue * Decimal('0.4')),
                "MTN Mobile Money": float(total_revenue * Decimal('0.3')),
                "Stripe": float(total_revenue * Decimal('0.2')),
                "Cash on Delivery": float(total_revenue * Decimal('0.1'))
            }
            
            # Get sales by region (mock data)
            sales_by_region = {
                "Douala": float(total_revenue * Decimal('0.4')),
                "Yaoundé": float(total_revenue * Decimal('0.3')),
                "Bafoussam": float(total_revenue * Decimal('0.15')),
                "Autres": float(total_revenue * Decimal('0.15'))
            }
            
            # Get top selling products
            top_products = await get_top_selling_products(db, date_from, date_to)
            
            return SalesAnalyticsResponse(
                metrics=metrics,
                sales_by_period=sales_by_period,
                sales_by_category=sales_by_category,
                sales_by_payment_method=sales_by_payment_method,
                sales_by_region=sales_by_region,
                top_selling_products=top_products,
                period_start=date_from,
                period_end=date_to
            )
            
    except Exception as e:
        logger.error(f"Failed to get sales analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve sales analytics"
        )


@router.get("/products", response_model=ProductAnalyticsResponse)
async def get_product_analytics(
    admin_user: object = Depends(get_current_admin_user),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    category_ids: Optional[List[str]] = Query(None),
    limit: int = Query(50, ge=1, le=100)
):
    """
    Get product performance analytics.
    
    - **date_from**: Start date for analysis
    - **date_to**: End date for analysis
    - **category_ids**: Filter by specific categories
    - **limit**: Number of products to return
    """
    try:
        # Set default date range
        if not date_to:
            date_to = datetime.utcnow().date()
        if not date_from:
            date_from = date_to - timedelta(days=30)
        
        async with get_db_context() as db:
            # Get product performance metrics
            products_query = select(Product).where(Product.is_active == True)
            
            if category_ids:
                products_query = products_query.where(Product.category_id.in_(category_ids))
            
            products = await db.execute(
                products_query.options(selectinload(Product.category))
                .limit(limit)
            )
            
            products_list = []
            for product in products.scalars().all():
                # Get product views
                views_count = await db.execute(
                    select(func.count(ProductView.id))
                    .where(
                        and_(
                            ProductView.product_id == product.id,
                            ProductView.created_at >= date_from,
                            ProductView.created_at <= date_to
                        )
                    )
                )
                views = views_count.scalar() or 0
                
                # Get unique views
                unique_views_count = await db.execute(
                    select(func.count(func.distinct(ProductView.user_id)))
                    .where(
                        and_(
                            ProductView.product_id == product.id,
                            ProductView.created_at >= date_from,
                            ProductView.created_at <= date_to,
                            ProductView.user_id.isnot(None)
                        )
                    )
                )
                unique_views = unique_views_count.scalar() or 0
                
                # Calculate conversion rate and other metrics
                # This would integrate with actual cart and order data
                cart_additions = views // 10  # Mock data
                purchases = cart_additions // 5  # Mock data
                revenue = purchases * float(product.price_xaf)
                conversion_rate = (purchases / views * 100) if views > 0 else 0
                
                products_list.append({
                    "product_id": str(product.id),
                    "product_title": product.title,
                    "product_image": product.main_image,
                    "views": views,
                    "unique_views": unique_views,
                    "cart_additions": cart_additions,
                    "purchases": purchases,
                    "revenue": Decimal(str(revenue)),
                    "conversion_rate": conversion_rate,
                    "bounce_rate": 65.0,  # Mock data
                    "average_time_on_page": 120,  # Mock data
                    "rating": 4.2,  # Mock data
                    "review_count": 15  # Mock data
                })
            
            # Summary statistics
            summary = {
                "total_products": len(products_list),
                "total_views": sum(p["views"] for p in products_list),
                "total_revenue": sum(p["revenue"] for p in products_list),
                "average_conversion_rate": sum(p["conversion_rate"] for p in products_list) / len(products_list) if products_list else 0
            }
            
            return ProductAnalyticsResponse(
                products=products_list,
                summary=summary,
                period_start=date_from,
                period_end=date_to
            )
            
    except Exception as e:
        logger.error(f"Failed to get product analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve product analytics"
        )


@router.get("/search", response_model=SearchTrends)
async def get_search_analytics(
    admin_user: object = Depends(get_current_admin_user),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    limit: int = Query(50, ge=1, le=100)
):
    """
    Get search analytics and trends.
    
    - **date_from**: Start date for analysis
    - **date_to**: End date for analysis  
    - **limit**: Number of search queries to return
    """
    try:
        # Set default date range
        if not date_to:
            date_to = datetime.utcnow().date()
        if not date_from:
            date_from = date_to - timedelta(days=30)
        
        async with get_db_context() as db:
            # Get trending queries
            trending_queries = await db.execute(
                select(
                    SearchAnalytic.query,
                    func.count(SearchAnalytic.id).label('search_count'),
                    func.avg(SearchAnalytic.results_count).label('avg_results'),
                    func.count(func.case([(SearchAnalytic.clicked_product_id.isnot(None), 1)])).label('click_count'),
                    func.count(func.case([(SearchAnalytic.results_count == 0, 1)])).label('no_results_count')
                )
                .where(
                    and_(
                        SearchAnalytic.created_at >= date_from,
                        SearchAnalytic.created_at <= date_to
                    )
                )
                .group_by(SearchAnalytic.query)
                .order_by(func.count(SearchAnalytic.id).desc())
                .limit(limit)
            )
            
            trending_list = []
            no_results_list = []
            
            for row in trending_queries.all():
                click_through_rate = (row.click_count / row.search_count * 100) if row.search_count > 0 else 0
                
                trend_item = {
                    "query": row.query,
                    "search_count": row.search_count,
                    "results_count": int(row.avg_results or 0),
                    "click_count": row.click_count,
                    "click_through_rate": click_through_rate,
                    "conversion_count": 0,  # Would integrate with order data
                    "conversion_rate": 0.0
                }
                
                trending_list.append(trend_item)
                
                # Collect no-results queries
                if row.no_results_count > 0:
                    no_results_list.append({
                        "query": row.query,
                        "count": row.no_results_count
                    })
            
            # Get search volume by date
            search_volume = await db.execute(
                select(
                    func.date(SearchAnalytic.created_at).label('date'),
                    func.count(SearchAnalytic.id).label('volume')
                )
                .where(
                    and_(
                        SearchAnalytic.created_at >= date_from,
                        SearchAnalytic.created_at <= date_to
                    )
                )
                .group_by(func.date(SearchAnalytic.created_at))
                .order_by(func.date(SearchAnalytic.created_at))
            )
            
            search_volume_by_date = {}
            for row in search_volume.all():
                search_volume_by_date[row.date.strftime('%Y-%m-%d')] = row.volume
            
            # Mock top clicked products
            top_clicked_products = [
                {"product_id": "1", "title": "iPhone 15 Pro", "clicks": 250},
                {"product_id": "2", "title": "Samsung Galaxy S24", "clicks": 180},
                {"product_id": "3", "title": "MacBook Air M3", "clicks": 150}
            ]
            
            return SearchTrends(
                trending_queries=trending_list[:20],  # Top 20
                no_results_queries=no_results_list[:10],  # Top 10
                top_clicked_products=top_clicked_products,
                search_volume_by_date=search_volume_by_date,
                period_start=date_from,
                period_end=date_to
            )
            
    except Exception as e:
        logger.error(f"Failed to get search analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve search analytics"
        )


@router.get("/realtime", response_model=RealTimeMetrics)
async def get_realtime_metrics(admin_user: object = Depends(get_current_admin_user)):
    """
    Get real-time metrics for live dashboard.
    
    Returns current active users, orders, revenue, and system health.
    """
    try:
        async with get_db_context() as db:
            now = datetime.utcnow()
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            
            # Active users (last 30 minutes)
            active_users_count = await db.execute(
                select(func.count(func.distinct(ProductView.user_id)))
                .where(
                    and_(
                        ProductView.created_at >= now - timedelta(minutes=30),
                        ProductView.user_id.isnot(None)
                    )
                )
            )
            active_users = active_users_count.scalar() or 0
            
            # Current orders (today)
            current_orders_count = await db.execute(
                select(func.count(Order.id))
                .where(Order.created_at >= today_start)
            )
            current_orders = current_orders_count.scalar() or 0
            
            # Today's revenue
            today_revenue = await db.execute(
                select(func.coalesce(func.sum(Order.total_amount), 0))
                .where(
                    and_(
                        Order.created_at >= today_start,
                        Order.status.in_(['completed', 'delivered', 'paid_full'])
                    )
                )
            )
            today_revenue_amount = today_revenue.scalar() or 0
            
            # Conversion rate today
            conversion_rate_today = 4.8  # Mock data
            
            # Top pages (mock data)
            top_pages = [
                {"page": "/products", "views": 1250},
                {"page": "/", "views": 890},
                {"page": "/categories/electronics", "views": 456}
            ]
            
            # Recent conversions (mock data)
            recent_conversions = [
                {"order_id": "PW202412150001", "amount": 45000, "customer": "Jean D.", "time": "2 min ago"},
                {"order_id": "PW202412150002", "amount": 28500, "customer": "Marie K.", "time": "5 min ago"},
                {"order_id": "PW202412150003", "amount": 67200, "customer": "Paul M.", "time": "8 min ago"}
            ]
            
            # System health
            system_health = {
                "api_status": "healthy",
                "database_status": "healthy",
                "redis_status": "healthy",
                "response_time_ms": 120,
                "error_rate": 0.02
            }
            
            return RealTimeMetrics(
                active_users=active_users,
                current_orders=current_orders,
                today_revenue=today_revenue_amount,
                today_orders=current_orders,
                conversion_rate_today=conversion_rate_today,
                top_pages=top_pages,
                recent_conversions=recent_conversions,
                system_health=system_health,
                last_updated=now
            )
            
    except Exception as e:
        logger.error(f"Failed to get realtime metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve realtime metrics"
        )


# Helper functions
async def get_period_metrics(db: AsyncSession, start_date: datetime, end_date: datetime) -> dict:
    """Get metrics for a specific time period."""
    
    # Revenue
    revenue_query = await db.execute(
        select(func.coalesce(func.sum(Order.total_amount), 0))
        .where(
            and_(
                Order.created_at >= start_date,
                Order.created_at <= end_date,
                Order.status.in_(['completed', 'delivered', 'paid_full'])
            )
        )
    )
    revenue = revenue_query.scalar() or 0
    
    # Orders
    orders_query = await db.execute(
        select(func.count(Order.id))
        .where(
            and_(
                Order.created_at >= start_date,
                Order.created_at <= end_date
            )
        )
    )
    orders = orders_query.scalar() or 0
    
    # Average order value
    avg_order_value = float(revenue / orders) if orders > 0 else 0
    
    # New users
    new_users_query = await db.execute(
        select(func.count(User.id))
        .where(
            and_(
                User.created_at >= start_date,
                User.created_at <= end_date
            )
        )
    )
    new_users = new_users_query.scalar() or 0
    
    # Active users (mock)
    active_users = new_users * 10  # Mock multiplier
    
    # Processing orders
    processing_orders_query = await db.execute(
        select(func.count(Order.id))
        .where(Order.status.in_(['processing', 'shipped', 'in_transit']))
    )
    processing_orders = processing_orders_query.scalar() or 0
    
    return {
        'revenue': float(revenue),
        'orders': orders,
        'avg_order_value': avg_order_value,
        'new_users': new_users,
        'active_users': active_users,
        'conversion_rate': 4.2,  # Mock data
        'processing_orders': processing_orders,
        'pending_payments': 0  # Mock data
    }


async def get_top_products(db: AsyncSession, start_date: datetime, end_date: datetime) -> List[dict]:
    """Get top performing products for the period."""
    # This would integrate with actual order items data
    # For now, return mock data
    
    return [
        {"id": "1", "name": "iPhone 15 Pro", "revenue": 2500000, "units_sold": 50},
        {"id": "2", "name": "Samsung Galaxy S24", "revenue": 1800000, "units_sold": 40},
        {"id": "3", "name": "MacBook Air M3", "revenue": 3200000, "units_sold": 20}
    ]


async def get_system_alerts(db: AsyncSession) -> List[dict]:
    """Get system alerts and notifications."""
    alerts = []
    
    # Check for low stock products
    low_stock_count = await get_low_stock_count(db)
    if low_stock_count > 0:
        alerts.append({
            "type": "warning",
            "message": f"{low_stock_count} products are low in stock",
            "action_url": "/admin/inventory"
        })
    
    # Mock other alerts
    alerts.extend([
        {
            "type": "info",
            "message": "New orders awaiting processing: 5",
            "action_url": "/admin/orders"
        }
    ])
    
    return alerts


async def get_low_stock_count(db: AsyncSession) -> int:
    """Get count of products with low stock."""
    from app.models.product import Inventory
    
    count_query = await db.execute(
        select(func.count(Inventory.id))
        .where(
            Inventory.quantity - Inventory.reserved_quantity <= Inventory.min_threshold
        )
    )
    return count_query.scalar() or 0


async def get_sales_by_period(db: AsyncSession, start_date: date, end_date: date, period: AnalyticsPeriod) -> List[dict]:
    """Get sales data grouped by time period."""
    # This would implement actual period-based grouping
    # For now, return mock data
    
    return [
        {"period": "2024-12-01", "revenue": 125000, "orders": 25, "average_order_value": 5000, "items_sold": 45},
        {"period": "2024-12-02", "revenue": 98000, "orders": 20, "average_order_value": 4900, "items_sold": 38},
        {"period": "2024-12-03", "revenue": 156000, "orders": 31, "average_order_value": 5032, "items_sold": 52}
    ]


async def get_sales_by_category(db: AsyncSession, start_date: date, end_date: date) -> dict:
    """Get sales data by product category."""
    # Mock data - would integrate with actual order items
    return {
        "Electronics": 450000.0,
        "Books": 280000.0,
        "Fashion": 320000.0,
        "Beauty": 180000.0
    }


async def get_top_selling_products(db: AsyncSession, start_date: date, end_date: date) -> List[dict]:
    """Get top selling products by revenue."""
    # Mock data - would integrate with actual order items
    return [
        {"id": "1", "name": "iPhone 15 Pro", "revenue": 2500000, "units_sold": 50, "category": "Electronics"},
        {"id": "2", "name": "MacBook Air M3", "revenue": 3200000, "units_sold": 20, "category": "Electronics"},
        {"id": "3", "name": "Samsung Galaxy S24", "revenue": 1800000, "units_sold": 40, "category": "Electronics"}
    ]
