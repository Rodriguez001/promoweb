"""Add shipping, analytics, and promotion tables

Revision ID: 002_shipping_analytics
Revises: 001_initial
Create Date: 2024-12-15 16:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import geoalchemy2

# revision identifiers, used by Alembic.
revision: str = '002_shipping_analytics'
down_revision: Union[str, None] = '001_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create shipping_zones table
    op.create_table('shipping_zones',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('code', sa.String(10), nullable=False, unique=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('base_cost', sa.Numeric(10, 2), nullable=False, server_default=sa.text('0')),
        sa.Column('cost_per_kg', sa.Numeric(10, 2), nullable=False, server_default=sa.text('0')),
        sa.Column('free_shipping_threshold', sa.Numeric(10, 2), nullable=True),
        sa.Column('min_delivery_days', sa.Integer(), nullable=False, server_default=sa.text('1')),
        sa.Column('max_delivery_days', sa.Integer(), nullable=False, server_default=sa.text('7')),
        sa.Column('max_weight_kg', sa.Numeric(8, 3), nullable=True),
        sa.Column('restricted_items', postgresql.ARRAY(sa.String(100)), nullable=False, server_default=sa.text("'{}'::varchar[]")),
        sa.Column('coverage_areas', postgresql.ARRAY(sa.String(100)), nullable=False, server_default=sa.text("'{}'::varchar[]")),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'))
    )
    
    # Create carriers table
    op.create_table('carriers',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('code', sa.String(20), nullable=False, unique=True),
        sa.Column('website', sa.String(255), nullable=True),
        sa.Column('phone', sa.String(20), nullable=True),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('api_endpoint', sa.String(255), nullable=True),
        sa.Column('api_key', sa.Text(), nullable=True),
        sa.Column('api_enabled', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('services', postgresql.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'))
    )
    
    # Create shipping table
    op.create_table('shipping',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('order_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('orders.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('tracking_number', sa.String(100), nullable=False, unique=True, index=True),
        sa.Column('carrier_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('carriers.id', ondelete='SET NULL'), nullable=True),
        sa.Column('carrier', sa.String(50), nullable=False),
        sa.Column('carrier_service', sa.String(50), nullable=True),
        sa.Column('status', sa.String(30), nullable=False, server_default='pending'),
        sa.Column('delivery_address', sa.Text(), nullable=False),
        sa.Column('delivery_location', geoalchemy2.Geography(geometry_type='POINT', srid=4326), nullable=True),
        sa.Column('delivery_instructions', sa.Text(), nullable=True),
        sa.Column('estimated_delivery', sa.DateTime(timezone=True), nullable=True),
        sa.Column('actual_delivery', sa.DateTime(timezone=True), nullable=True),
        sa.Column('delivery_attempts', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('shipping_cost', sa.Numeric(10, 2), nullable=False),
        sa.Column('weight_kg', sa.Numeric(8, 3), nullable=True),
        sa.Column('dimensions', sa.String(50), nullable=True),
        sa.Column('package_count', sa.Integer(), nullable=False, server_default=sa.text('1')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'))
    )
    op.create_index('idx_shipping_order_id', 'shipping', ['order_id'])
    op.create_index('idx_shipping_status', 'shipping', ['status'])
    
    # Create shipping_tracking_events table
    op.create_table('shipping_tracking_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('shipping_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('shipping.id', ondelete='CASCADE'), nullable=False),
        sa.Column('status', sa.String(30), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('location', sa.String(255), nullable=True),
        sa.Column('event_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'))
    )
    op.create_index('idx_tracking_events_shipping_id', 'shipping_tracking_events', ['shipping_id'])
    
    # Create promotions table
    op.create_table('promotions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('code', sa.String(50), nullable=True, unique=True, index=True),
        sa.Column('type', sa.String(20), nullable=False),
        sa.Column('discount_value', sa.Numeric(10, 2), nullable=False),
        sa.Column('min_order_amount', sa.Numeric(10, 2), nullable=True),
        sa.Column('max_discount_amount', sa.Numeric(10, 2), nullable=True),
        sa.Column('min_quantity', sa.Integer(), nullable=True),
        sa.Column('usage_limit', sa.Integer(), nullable=True),
        sa.Column('usage_limit_per_user', sa.Integer(), nullable=True),
        sa.Column('used_count', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('first_time_customers_only', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('user_group_ids', postgresql.ARRAY(postgresql.UUID(as_uuid=True)), nullable=False, server_default=sa.text("'{}'::uuid[]")),
        sa.Column('allowed_regions', postgresql.ARRAY(sa.String(50)), nullable=False, server_default=sa.text("'{}'::varchar[]")),
        sa.Column('excluded_regions', postgresql.ARRAY(sa.String(50)), nullable=False, server_default=sa.text("'{}'::varchar[]")),
        sa.Column('start_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('is_stackable', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('priority', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'))
    )
    op.create_index('idx_promotions_code', 'promotions', ['code'])
    op.create_index('idx_promotions_dates', 'promotions', ['start_date', 'end_date'])
    
    # Create category_promotions table (many-to-many)
    op.create_table('category_promotions',
        sa.Column('promotion_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('promotions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('category_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('categories.id', ondelete='CASCADE'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'))
    )
    op.create_primary_key('pk_category_promotions', 'category_promotions', ['promotion_id', 'category_id'])
    
    # Create product_promotions table (many-to-many)
    op.create_table('product_promotions',
        sa.Column('promotion_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('promotions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('products.id', ondelete='CASCADE'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'))
    )
    op.create_primary_key('pk_product_promotions', 'product_promotions', ['promotion_id', 'product_id'])
    
    # Create promotion_usage table
    op.create_table('promotion_usage',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('promotion_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('promotions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('order_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('orders.id', ondelete='SET NULL'), nullable=True),
        sa.Column('discount_amount', sa.Numeric(10, 2), nullable=True),
        sa.Column('original_amount', sa.Numeric(10, 2), nullable=True),
        sa.Column('used_at', sa.DateTime(timezone=True), server_default=sa.text('now()'))
    )
    op.create_index('idx_promotion_usage_promotion_id', 'promotion_usage', ['promotion_id'])
    op.create_index('idx_promotion_usage_user_id', 'promotion_usage', ['user_id'])
    
    # Create search_analytics table
    op.create_table('search_analytics',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('query', sa.String(500), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('session_id', sa.String(255), nullable=True),
        sa.Column('results_count', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('clicked_product_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('products.id', ondelete='SET NULL'), nullable=True),
        sa.Column('search_duration_ms', sa.Integer(), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'))
    )
    op.create_index('idx_search_analytics_query', 'search_analytics', ['query'])
    op.create_index('idx_search_analytics_user_id', 'search_analytics', ['user_id'])
    op.create_index('idx_search_analytics_created_at', 'search_analytics', ['created_at'])
    
    # Create product_views table
    op.create_table('product_views',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('products.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('session_id', sa.String(255), nullable=True),
        sa.Column('referrer', sa.String(500), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('view_duration_seconds', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'))
    )
    op.create_index('idx_product_views_product_id', 'product_views', ['product_id'])
    op.create_index('idx_product_views_user_id', 'product_views', ['user_id'])
    op.create_index('idx_product_views_created_at', 'product_views', ['created_at'])
    
    # Create cart_abandonment_events table
    op.create_table('cart_abandonment_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('cart_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('carts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('session_id', sa.String(255), nullable=True),
        sa.Column('abandonment_stage', sa.String(20), nullable=False),
        sa.Column('cart_value', sa.Numeric(10, 2), nullable=False),
        sa.Column('item_count', sa.Integer(), nullable=False),
        sa.Column('last_activity', sa.DateTime(timezone=True), nullable=False),
        sa.Column('recovery_email_sent', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('recovered', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('recovered_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'))
    )
    op.create_index('idx_cart_abandonment_cart_id', 'cart_abandonment_events', ['cart_id'])
    op.create_index('idx_cart_abandonment_user_id', 'cart_abandonment_events', ['user_id'])
    
    # Create product_reviews table
    op.create_table('product_reviews',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('products.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('rating', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(255), nullable=True),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('is_verified', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('is_approved', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('helpful_votes', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'))
    )
    op.create_index('idx_product_reviews_product_id', 'product_reviews', ['product_id'])
    op.create_index('idx_product_reviews_user_id', 'product_reviews', ['user_id'])
    op.create_unique_constraint('uq_product_reviews_user_product', 'product_reviews', ['user_id', 'product_id'])
    
    # Create saved_items table (wishlist)
    op.create_table('saved_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('products.id', ondelete='CASCADE'), nullable=False),
        sa.Column('list_name', sa.String(100), nullable=False, server_default='Wishlist'),
        sa.Column('notes', sa.String(500), nullable=True),
        sa.Column('notify_on_price_drop', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('price_when_saved', sa.Numeric(10, 2), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'))
    )
    op.create_index('idx_saved_items_user_id', 'saved_items', ['user_id'])
    op.create_unique_constraint('uq_saved_items_user_product', 'saved_items', ['user_id', 'product_id'])
    
    # Create order_status_history table
    op.create_table('order_status_history',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('order_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('orders.id', ondelete='CASCADE'), nullable=False),
        sa.Column('previous_status', sa.String(30), nullable=True),
        sa.Column('new_status', sa.String(30), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('changed_by_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'))
    )
    op.create_index('idx_order_status_history_order_id', 'order_status_history', ['order_id'])
    
    # Create password reset and email verification tables
    op.create_table('user_password_resets',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('token', sa.String(255), nullable=False, unique=True, index=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_used', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'))
    )
    
    op.create_table('user_email_verifications',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('token', sa.String(255), nullable=False, unique=True, index=True),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_used', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'))
    )
    
    print("✅ Shipping, analytics, and promotion tables created")


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('user_email_verifications')
    op.drop_table('user_password_resets')
    op.drop_table('order_status_history')
    op.drop_table('saved_items')
    op.drop_table('product_reviews')
    op.drop_table('cart_abandonment_events')
    op.drop_table('product_views')
    op.drop_table('search_analytics')
    op.drop_table('promotion_usage')
    op.drop_table('product_promotions')
    op.drop_table('category_promotions')
    op.drop_table('promotions')
    op.drop_table('shipping_tracking_events')
    op.drop_table('shipping')
    op.drop_table('carriers')
    op.drop_table('shipping_zones')
    
    print("✅ Additional tables dropped successfully")
