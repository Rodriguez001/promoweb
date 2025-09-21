"""Initial migration - Create all tables

Revision ID: 001_initial
Revises: 
Create Date: 2024-12-15 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import geoalchemy2

# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable PostGIS extension
    op.execute('CREATE EXTENSION IF NOT EXISTS postgis')
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    
    # Create users table
    op.create_table('users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('email', sa.String(255), nullable=False, unique=True, index=True),
        sa.Column('password_hash', sa.Text(), nullable=False),
        sa.Column('first_name', sa.String(100), nullable=False),
        sa.Column('last_name', sa.String(100), nullable=False),
        sa.Column('phone', sa.String(20), nullable=True),
        sa.Column('role', sa.String(20), nullable=False, server_default='customer'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('email_verified', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('phone_verified', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('last_login', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'))
    )
    
    # Create user_addresses table
    op.create_table('user_addresses',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('street_address', sa.Text(), nullable=False),
        sa.Column('city', sa.String(100), nullable=False),
        sa.Column('region', sa.String(100), nullable=True),
        sa.Column('postal_code', sa.String(10), nullable=True),
        sa.Column('country', sa.String(2), nullable=False, server_default='CM'),
        sa.Column('is_default', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('location', geoalchemy2.Geography(geometry_type='POINT', srid=4326, spatial_index=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'))
    )
    op.create_index('idx_user_addresses_user_id', 'user_addresses', ['user_id'])
    
    # Create user_preferences table
    op.create_table('user_preferences',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('language', sa.String(2), nullable=False, server_default='fr'),
        sa.Column('currency', sa.String(3), nullable=False, server_default='XAF'),
        sa.Column('timezone', sa.String(50), nullable=False, server_default='Africa/Douala'),
        sa.Column('email_notifications', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('sms_notifications', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('marketing_emails', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('items_per_page', sa.Integer(), nullable=False, server_default=sa.text('20')),
        sa.Column('theme', sa.String(10), nullable=False, server_default='light'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'))
    )
    
    # Create user_sessions table
    op.create_table('user_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('session_token', sa.String(100), nullable=False),
        sa.Column('refresh_token', sa.Text(), nullable=False),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('device_info', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('last_activity', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'))
    )
    op.create_index('idx_user_sessions_user_id', 'user_sessions', ['user_id'])
    op.create_index('idx_user_sessions_token', 'user_sessions', ['session_token'])
    
    # Create categories table
    op.create_table('categories',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('slug', sa.String(150), nullable=False, unique=True, index=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('image_url', sa.Text(), nullable=True),
        sa.Column('parent_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('categories.id', ondelete='SET NULL'), nullable=True),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('meta_title', sa.String(255), nullable=True),
        sa.Column('meta_description', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'))
    )
    op.create_index('idx_categories_parent_id', 'categories', ['parent_id'])
    
    # Create products table
    op.create_table('products',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('slug', sa.String(300), nullable=False, unique=True, index=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('short_description', sa.String(500), nullable=True),
        sa.Column('isbn', sa.String(20), nullable=True),
        sa.Column('ean', sa.String(20), nullable=True),
        sa.Column('sku', sa.String(100), nullable=True),
        sa.Column('brand', sa.String(100), nullable=True),
        sa.Column('category_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('categories.id', ondelete='SET NULL'), nullable=True),
        sa.Column('price_eur', sa.Numeric(10, 2), nullable=False),
        sa.Column('price_xaf', sa.Numeric(10, 2), nullable=False),
        sa.Column('margin_percentage', sa.Numeric(5, 2), nullable=False, server_default=sa.text('30.00')),
        sa.Column('cost_price_eur', sa.Numeric(10, 2), nullable=True),
        sa.Column('weight_kg', sa.Numeric(8, 3), nullable=True),
        sa.Column('dimensions_cm', sa.String(50), nullable=True),
        sa.Column('images', postgresql.ARRAY(sa.Text()), nullable=False, server_default=sa.text("'{}'::text[]")),
        sa.Column('tags', postgresql.ARRAY(sa.String(50)), nullable=False, server_default=sa.text("'{}'::varchar[]")),
        sa.Column('meta_title', sa.String(255), nullable=True),
        sa.Column('meta_description', sa.String(500), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('is_featured', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('is_digital', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('google_merchant_id', sa.String(100), nullable=True),
        sa.Column('last_sync_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'))
    )
    op.create_index('idx_products_category_id', 'products', ['category_id'])
    op.create_index('idx_products_brand', 'products', ['brand'])
    op.create_index('idx_products_price', 'products', ['price_xaf'])
    op.create_index('idx_products_featured', 'products', ['is_featured'])
    
    # Create inventory table
    op.create_table('inventory',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('products.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('quantity', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('reserved_quantity', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('min_threshold', sa.Integer(), nullable=False, server_default=sa.text('10')),
        sa.Column('max_threshold', sa.Integer(), nullable=True),
        sa.Column('last_updated', sa.DateTime(timezone=True), server_default=sa.text('now()'))
    )
    
    # Create carts table
    op.create_table('carts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=True),
        sa.Column('session_id', sa.String(255), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'))
    )
    op.create_index('idx_carts_user_id', 'carts', ['user_id'])
    op.create_index('idx_carts_session_id', 'carts', ['session_id'])
    
    # Create cart_items table
    op.create_table('cart_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('cart_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('carts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('products.id', ondelete='CASCADE'), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('unit_price', sa.Numeric(10, 2), nullable=False),
        sa.Column('total_price', sa.Numeric(10, 2), nullable=False),
        sa.Column('notes', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'))
    )
    op.create_index('idx_cart_items_cart_id', 'cart_items', ['cart_id'])
    op.create_unique_constraint('uq_cart_items_cart_product', 'cart_items', ['cart_id', 'product_id'])
    
    # Create orders table
    op.create_table('orders',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('order_number', sa.String(50), nullable=False, unique=True, index=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('status', sa.String(30), nullable=False, server_default='pending'),
        sa.Column('total_amount', sa.Numeric(10, 2), nullable=False),
        sa.Column('deposit_amount', sa.Numeric(10, 2), nullable=False, server_default=sa.text('0')),
        sa.Column('remaining_amount', sa.Numeric(10, 2), nullable=False, server_default=sa.text('0')),
        sa.Column('shipping_cost', sa.Numeric(10, 2), nullable=False, server_default=sa.text('0')),
        sa.Column('tax_amount', sa.Numeric(10, 2), nullable=False, server_default=sa.text('0')),
        sa.Column('discount_amount', sa.Numeric(10, 2), nullable=False, server_default=sa.text('0')),
        sa.Column('billing_name', sa.String(200), nullable=True),
        sa.Column('billing_email', sa.String(255), nullable=True),
        sa.Column('billing_phone', sa.String(20), nullable=True),
        sa.Column('billing_address', sa.Text(), nullable=True),
        sa.Column('billing_city', sa.String(100), nullable=True),
        sa.Column('billing_region', sa.String(100), nullable=True),
        sa.Column('billing_postal_code', sa.String(10), nullable=True),
        sa.Column('billing_country', sa.String(2), nullable=True),
        sa.Column('billing_address_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('shipping_name', sa.String(200), nullable=True),
        sa.Column('shipping_address', sa.Text(), nullable=True),
        sa.Column('shipping_city', sa.String(100), nullable=True),
        sa.Column('shipping_region', sa.String(100), nullable=True),
        sa.Column('shipping_postal_code', sa.String(10), nullable=True),
        sa.Column('shipping_country', sa.String(2), nullable=True),
        sa.Column('shipping_address_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('shipping_location', geoalchemy2.Geography(geometry_type='POINT', srid=4326), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('admin_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('delivered_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('cancelled_at', sa.DateTime(timezone=True), nullable=True)
    )
    op.create_index('idx_orders_user_id', 'orders', ['user_id'])
    op.create_index('idx_orders_status', 'orders', ['status'])
    op.create_index('idx_orders_created_at', 'orders', ['created_at'])
    
    # Create order_items table
    op.create_table('order_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('order_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('orders.id', ondelete='CASCADE'), nullable=False),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('products.id', ondelete='SET NULL'), nullable=True),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('unit_price', sa.Numeric(10, 2), nullable=False),
        sa.Column('total_price', sa.Numeric(10, 2), nullable=False),
        sa.Column('product_snapshot', postgresql.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'))
    )
    op.create_index('idx_order_items_order_id', 'order_items', ['order_id'])
    
    # Create payments table
    op.create_table('payments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('order_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('orders.id', ondelete='CASCADE'), nullable=False),
        sa.Column('transaction_id', sa.String(255), nullable=True),
        sa.Column('reference_id', sa.String(100), nullable=False, unique=True, index=True),
        sa.Column('gateway', sa.String(30), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='initiated'),
        sa.Column('amount', sa.Numeric(10, 2), nullable=False),
        sa.Column('currency', sa.String(3), nullable=False, server_default='XAF'),
        sa.Column('customer_phone', sa.String(20), nullable=True),
        sa.Column('customer_email', sa.String(255), nullable=True),
        sa.Column('gateway_transaction_id', sa.String(255), nullable=True),
        sa.Column('gateway_response', postgresql.JSON(), nullable=True),
        sa.Column('failure_reason', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('initiated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'))
    )
    op.create_index('idx_payments_order_id', 'payments', ['order_id'])
    op.create_index('idx_payments_gateway', 'payments', ['gateway'])
    op.create_index('idx_payments_status', 'payments', ['status'])
    
    print("✅ Initial migration completed - all tables created")


def downgrade() -> None:
    # Drop all tables in reverse order
    op.drop_table('payments')
    op.drop_table('order_items')
    op.drop_table('orders')
    op.drop_table('cart_items')
    op.drop_table('carts')
    op.drop_table('inventory')
    op.drop_table('products')
    op.drop_table('categories')
    op.drop_table('user_sessions')
    op.drop_table('user_preferences')
    op.drop_table('user_addresses')
    op.drop_table('users')
    
    # Drop extensions
    op.execute('DROP EXTENSION IF EXISTS postgis')
    op.execute('DROP EXTENSION IF EXISTS "uuid-ossp"')
    
    print("✅ Tables dropped successfully")
