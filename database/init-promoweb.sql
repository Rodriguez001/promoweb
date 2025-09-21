-- =========================================
-- PromoWeb Africa - Database Initialization
-- PostgreSQL + PostGIS Setup
-- =========================================

-- Usage: psql -U postgres -d promoweb -f init-promoweb.sql

-- Create database if not exists
CREATE DATABASE IF NOT EXISTS promoweb;

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "postgis";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- Create promoweb user if not exists
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'promoweb') THEN
        CREATE USER promoweb WITH PASSWORD 'password_2024';
    END IF;
END
$$;

-- Grant schema usage and create permissions to the promoweb user
GRANT USAGE, CREATE ON SCHEMA public TO promoweb;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO promoweb;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO promoweb;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO promoweb;

-- Set default privileges for future objects
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL PRIVILEGES ON TABLES TO promoweb;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL PRIVILEGES ON SEQUENCES TO promoweb;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL PRIVILEGES ON FUNCTIONS TO promoweb;

-- =========================================
-- ENUMS AND TYPES
-- =========================================

-- Order Status Enum
CREATE TYPE order_status AS ENUM (
    'pending',
    'partially_paid',
    'processing', 
    'shipped',
    'in_transit',
    'delivered',
    'delivery_failed',
    'paid_full',
    'completed',
    'cancelled',
    'returned',
    'refunded'
);

-- Payment Status Enum
CREATE TYPE payment_status AS ENUM (
    'initiated',
    'processing',
    'pending',
    'success',
    'failed',
    'expired',
    'refunded'
);

-- Payment Gateway Enum
CREATE TYPE payment_gateway AS ENUM (
    'stripe',
    'orange_money',
    'mtn_mobile_money',
    'cash_on_delivery'
);

-- Shipping Status Enum
CREATE TYPE shipping_status AS ENUM (
    'pending',
    'preparing',
    'shipped',
    'in_transit',
    'delivered',
    'failed',
    'returned'
);

-- User Role Enum
CREATE TYPE user_role AS ENUM (
    'customer',
    'admin',
    'super_admin'
);

-- Promotion Type Enum
CREATE TYPE promotion_type AS ENUM (
    'percentage',
    'fixed_amount',
    'free_shipping',
    'buy_one_get_one'
);

-- =========================================
-- CORE TABLES
-- =========================================

-- Users Table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    role user_role DEFAULT 'customer',
    is_active BOOLEAN DEFAULT TRUE,
    email_verified BOOLEAN DEFAULT FALSE,
    phone_verified BOOLEAN DEFAULT FALSE,
    last_login TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User Addresses Table (with PostGIS support)
CREATE TABLE user_addresses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL, -- e.g., "Domicile", "Bureau"
    street_address TEXT NOT NULL,
    city VARCHAR(100) NOT NULL,
    region VARCHAR(100), -- Cameroon regions
    postal_code VARCHAR(10),
    country VARCHAR(2) DEFAULT 'CM',
    location GEOMETRY(Point, 4326), -- GPS coordinates
    is_default BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Categories Table
CREATE TABLE categories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    parent_id UUID REFERENCES categories(id),
    image_url VARCHAR(500),
    sort_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Products Table
CREATE TABLE products (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(255) NOT NULL,
    slug VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    short_description VARCHAR(500),
    isbn VARCHAR(20),
    ean VARCHAR(20),
    brand VARCHAR(100),
    category_id UUID REFERENCES categories(id),
    price_eur DECIMAL(10,2) NOT NULL,
    price_xaf DECIMAL(12,2) NOT NULL,
    cost_price_eur DECIMAL(10,2),
    margin_percentage DECIMAL(5,2) DEFAULT 30.00,
    weight_kg DECIMAL(8,3),
    dimensions_cm VARCHAR(50), -- "L x W x H"
    images JSONB DEFAULT '[]', -- Array of image URLs
    tags VARCHAR(255)[],
    meta_title VARCHAR(255),
    meta_description VARCHAR(500),
    is_active BOOLEAN DEFAULT TRUE,
    is_featured BOOLEAN DEFAULT FALSE,
    google_merchant_id VARCHAR(100),
    last_sync_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Inventory Table
CREATE TABLE inventory (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    product_id UUID UNIQUE NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    quantity INTEGER NOT NULL DEFAULT 0,
    reserved_quantity INTEGER NOT NULL DEFAULT 0,
    min_threshold INTEGER DEFAULT 10,
    max_threshold INTEGER,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Promotions Table
CREATE TABLE promotions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    code VARCHAR(50) UNIQUE,
    type promotion_type NOT NULL,
    discount_value DECIMAL(10,2) NOT NULL,
    min_order_amount DECIMAL(10,2),
    max_discount_amount DECIMAL(10,2),
    usage_limit INTEGER,
    used_count INTEGER DEFAULT 0,
    start_date TIMESTAMP WITH TIME ZONE NOT NULL,
    end_date TIMESTAMP WITH TIME ZONE NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Product Promotions Junction Table
CREATE TABLE product_promotions (
    product_id UUID REFERENCES products(id) ON DELETE CASCADE,
    promotion_id UUID REFERENCES promotions(id) ON DELETE CASCADE,
    PRIMARY KEY (product_id, promotion_id)
);

-- Carts Table
CREATE TABLE carts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    session_id VARCHAR(255), -- For anonymous users
    total_amount DECIMAL(10,2) DEFAULT 0.00,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Cart Items Table
CREATE TABLE cart_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    cart_id UUID NOT NULL REFERENCES carts(id) ON DELETE CASCADE,
    product_id UUID NOT NULL REFERENCES products(id),
    quantity INTEGER NOT NULL DEFAULT 1,
    unit_price DECIMAL(10,2) NOT NULL,
    total_price DECIMAL(10,2) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Orders Table
CREATE TABLE orders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    order_number VARCHAR(50) UNIQUE NOT NULL,
    user_id UUID NOT NULL REFERENCES users(id),
    status order_status DEFAULT 'pending',
    total_amount DECIMAL(12,2) NOT NULL,
    deposit_amount DECIMAL(12,2) NOT NULL, -- 30% acompte
    remaining_amount DECIMAL(12,2) NOT NULL,
    shipping_cost DECIMAL(10,2) DEFAULT 0.00,
    tax_amount DECIMAL(10,2) DEFAULT 0.00,
    
    -- Billing Address
    billing_name VARCHAR(200),
    billing_email VARCHAR(255),
    billing_phone VARCHAR(20),
    billing_address TEXT,
    billing_city VARCHAR(100),
    billing_region VARCHAR(100),
    billing_postal_code VARCHAR(10),
    
    -- Shipping Address  
    shipping_name VARCHAR(200),
    shipping_address TEXT,
    shipping_city VARCHAR(100),
    shipping_region VARCHAR(100),
    shipping_postal_code VARCHAR(10),
    shipping_location GEOMETRY(Point, 4326),
    
    -- Metadata
    notes TEXT,
    admin_notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    delivered_at TIMESTAMP WITH TIME ZONE
);

-- Order Items Table
CREATE TABLE order_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    order_id UUID NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    product_id UUID NOT NULL REFERENCES products(id),
    quantity INTEGER NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL,
    total_price DECIMAL(10,2) NOT NULL,
    product_snapshot JSONB -- Store product details at time of order
);

-- Payments Table
CREATE TABLE payments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    order_id UUID NOT NULL REFERENCES orders(id),
    transaction_id VARCHAR(255),
    gateway payment_gateway NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'XAF',
    status payment_status DEFAULT 'initiated',
    gateway_response JSONB,
    failure_reason TEXT,
    processed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Shipping Table
CREATE TABLE shipping (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    order_id UUID UNIQUE NOT NULL REFERENCES orders(id),
    carrier VARCHAR(100),
    tracking_number VARCHAR(100),
    status shipping_status DEFAULT 'pending',
    weight_kg DECIMAL(8,3),
    cost DECIMAL(10,2),
    estimated_delivery DATE,
    shipped_at TIMESTAMP WITH TIME ZONE,
    delivered_at TIMESTAMP WITH TIME ZONE,
    tracking_url VARCHAR(500),
    delivery_notes TEXT
);

-- =========================================
-- CONFIGURATION TABLES
-- =========================================

-- Exchange Rates Table (EUR to XAF)
CREATE TABLE exchange_rates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    from_currency VARCHAR(3) DEFAULT 'EUR',
    to_currency VARCHAR(3) DEFAULT 'XAF', 
    rate DECIMAL(10,6) NOT NULL,
    date DATE NOT NULL,
    source VARCHAR(100), -- API source
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- System Settings Table
CREATE TABLE system_settings (
    key VARCHAR(100) PRIMARY KEY,
    value TEXT NOT NULL,
    description TEXT,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Shipping Zones Table (Geographic zones for shipping)
CREATE TABLE shipping_zones (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    zone_geometry GEOMETRY(MultiPolygon, 4326), -- Geographic boundaries
    base_cost DECIMAL(10,2) NOT NULL,
    cost_per_kg DECIMAL(10,2) NOT NULL,
    free_shipping_threshold DECIMAL(10,2),
    max_weight_kg DECIMAL(8,3),
    estimated_days INTEGER,
    is_active BOOLEAN DEFAULT TRUE
);

-- =========================================
-- ANALYTICS AND LOGS
-- =========================================

-- Search Analytics Table
CREATE TABLE search_analytics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    query VARCHAR(255) NOT NULL,
    user_id UUID REFERENCES users(id),
    session_id VARCHAR(255),
    results_count INTEGER,
    clicked_product_id UUID REFERENCES products(id),
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Product Views Table
CREATE TABLE product_views (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    product_id UUID NOT NULL REFERENCES products(id),
    user_id UUID REFERENCES users(id),
    session_id VARCHAR(255),
    ip_address INET,
    user_agent TEXT,
    referrer VARCHAR(500),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Order Status History Table
CREATE TABLE order_status_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    order_id UUID NOT NULL REFERENCES orders(id),
    previous_status order_status,
    new_status order_status NOT NULL,
    changed_by UUID REFERENCES users(id),
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Sync Logs Table (Google Merchant sync logs)
CREATE TABLE sync_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    type VARCHAR(50) NOT NULL, -- 'products', 'exchange_rates'
    status VARCHAR(20) NOT NULL, -- 'success', 'error', 'warning'
    records_processed INTEGER,
    records_updated INTEGER,
    records_created INTEGER,
    errors JSONB,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =========================================
-- INDEXES FOR PERFORMANCE
-- =========================================

-- Users indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_active ON users(is_active);

-- Products indexes
CREATE INDEX idx_products_category ON products(category_id);
CREATE INDEX idx_products_active ON products(is_active);
CREATE INDEX idx_products_featured ON products(is_featured);
CREATE INDEX idx_products_price_xaf ON products(price_xaf);
CREATE INDEX idx_products_slug ON products(slug);
CREATE INDEX idx_products_title_gin ON products USING gin(title gin_trgm_ops);
CREATE INDEX idx_products_description_gin ON products USING gin(description gin_trgm_ops);
CREATE INDEX idx_products_tags_gin ON products USING gin(tags);

-- Categories indexes
CREATE INDEX idx_categories_parent ON categories(parent_id);
CREATE INDEX idx_categories_slug ON categories(slug);
CREATE INDEX idx_categories_active ON categories(is_active);

-- Orders indexes
CREATE INDEX idx_orders_user ON orders(user_id);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_orders_number ON orders(order_number);
CREATE INDEX idx_orders_created_at ON orders(created_at);

-- Geographic indexes (PostGIS)
CREATE INDEX idx_user_addresses_location ON user_addresses USING GIST(location);
CREATE INDEX idx_orders_shipping_location ON orders USING GIST(shipping_location);
CREATE INDEX idx_shipping_zones_geometry ON shipping_zones USING GIST(zone_geometry);

-- Cart indexes
CREATE INDEX idx_carts_user ON carts(user_id);
CREATE INDEX idx_carts_session ON carts(session_id);

-- Analytics indexes
CREATE INDEX idx_search_analytics_query ON search_analytics(query);
CREATE INDEX idx_search_analytics_created_at ON search_analytics(created_at);
CREATE INDEX idx_product_views_product ON product_views(product_id);
CREATE INDEX idx_product_views_created_at ON product_views(created_at);

-- =========================================
-- TRIGGERS AND FUNCTIONS
-- =========================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers for updated_at
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_products_updated_at BEFORE UPDATE ON products 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_categories_updated_at BEFORE UPDATE ON categories 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_orders_updated_at BEFORE UPDATE ON orders 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_carts_updated_at BEFORE UPDATE ON carts 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to generate order number
CREATE OR REPLACE FUNCTION generate_order_number()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.order_number IS NULL THEN
        NEW.order_number := 'PW' || TO_CHAR(NOW(), 'YYYYMMDD') || '-' || LPAD(nextval('orders_sequence')::TEXT, 6, '0');
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create sequence for order numbers
CREATE SEQUENCE IF NOT EXISTS orders_sequence START 1;

-- Trigger for order number generation
CREATE TRIGGER generate_order_number_trigger 
    BEFORE INSERT ON orders 
    FOR EACH ROW EXECUTE FUNCTION generate_order_number();

-- Function to update inventory when order status changes
CREATE OR REPLACE FUNCTION update_inventory_on_order_status()
RETURNS TRIGGER AS $$
BEGIN
    -- Reserve stock when order is partially paid
    IF NEW.status = 'partially_paid' AND OLD.status = 'pending' THEN
        UPDATE inventory 
        SET reserved_quantity = reserved_quantity + oi.quantity
        FROM order_items oi
        WHERE inventory.product_id = oi.product_id AND oi.order_id = NEW.id;
    END IF;
    
    -- Release reserved stock and reduce actual stock when shipped
    IF NEW.status = 'shipped' AND OLD.status = 'processing' THEN
        UPDATE inventory 
        SET quantity = quantity - oi.quantity,
            reserved_quantity = reserved_quantity - oi.quantity
        FROM order_items oi
        WHERE inventory.product_id = oi.product_id AND oi.order_id = NEW.id;
    END IF;
    
    -- Release reserved stock if order cancelled
    IF NEW.status = 'cancelled' AND OLD.status IN ('pending', 'partially_paid', 'processing') THEN
        UPDATE inventory 
        SET reserved_quantity = reserved_quantity - oi.quantity
        FROM order_items oi
        WHERE inventory.product_id = oi.product_id AND oi.order_id = NEW.id;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for inventory management
CREATE TRIGGER update_inventory_trigger 
    AFTER UPDATE ON orders 
    FOR EACH ROW EXECUTE FUNCTION update_inventory_on_order_status();

-- =========================================
-- INITIAL DATA
-- =========================================

-- Insert default admin user (password: admin123!)
INSERT INTO users (email, password_hash, first_name, last_name, role, is_active, email_verified) 
VALUES (
    'admin@promoweb.cm',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/lewfBGSGtU4hsuxHq', -- admin123!
    'Admin',
    'PromoWeb',
    'super_admin',
    TRUE,
    TRUE
);

-- Insert system settings
INSERT INTO system_settings (key, value, description) VALUES 
('deposit_percentage', '30', 'Percentage of order total required as deposit'),
('tax_rate', '19.25', 'VAT rate percentage'),
('currency', 'XAF', 'Default currency'),
('free_shipping_threshold', '50000', 'Free shipping threshold in XAF'),
('site_name', 'PromoWeb Africa', 'Site name'),
('admin_email', 'admin@promoweb.cm', 'Admin email for notifications'),
('sms_enabled', 'true', 'Enable SMS notifications'),
('email_enabled', 'true', 'Enable email notifications');

-- Insert default categories
INSERT INTO categories (name, slug, description, sort_order, is_active) VALUES
('Livres', 'livres', 'Livres et publications', 1, TRUE),
('Électronique', 'electronique', 'Produits électroniques', 2, TRUE),
('Mode', 'mode', 'Vêtements et accessoires', 3, TRUE),
('Maison & Jardin', 'maison-jardin', 'Articles pour la maison et le jardin', 4, TRUE),
('Santé & Beauté', 'sante-beaute', 'Produits de santé et beauté', 5, TRUE);

-- Insert default shipping zones (Cameroon regions)
INSERT INTO shipping_zones (name, description, base_cost, cost_per_kg, free_shipping_threshold, estimated_days, is_active) VALUES
('Douala Urbain', 'Zone urbaine de Douala', 2000.00, 500.00, 50000.00, 1, TRUE),
('Yaoundé Urbain', 'Zone urbaine de Yaoundé', 2500.00, 600.00, 50000.00, 2, TRUE),
('Littoral', 'Région du Littoral (hors Douala)', 5000.00, 800.00, 75000.00, 3, TRUE),
('Centre', 'Région du Centre (hors Yaoundé)', 6000.00, 1000.00, 75000.00, 4, TRUE),
('Ouest', 'Région de l\'Ouest', 8000.00, 1200.00, 100000.00, 5, TRUE),
('Nord-Ouest', 'Région du Nord-Ouest', 10000.00, 1500.00, 100000.00, 7, TRUE),
('Sud-Ouest', 'Région du Sud-Ouest', 10000.00, 1500.00, 100000.00, 7, TRUE),
('Adamaoua', 'Région de l\'Adamaoua', 12000.00, 1800.00, 125000.00, 10, TRUE),
('Est', 'Région de l\'Est', 12000.00, 1800.00, 125000.00, 10, TRUE),
('Nord', 'Région du Nord', 15000.00, 2000.00, 150000.00, 12, TRUE),
('Extrême-Nord', 'Région de l\'Extrême-Nord', 15000.00, 2000.00, 150000.00, 12, TRUE),
('Sud', 'Région du Sud', 10000.00, 1500.00, 100000.00, 8, TRUE);

-- Insert current exchange rate (example)
INSERT INTO exchange_rates (from_currency, to_currency, rate, date, source) 
VALUES ('EUR', 'XAF', 655.957, CURRENT_DATE, 'ECB');

-- =========================================
-- VIEWS FOR ANALYTICS
-- =========================================

-- View: Product sales summary
CREATE VIEW product_sales_summary AS
SELECT 
    p.id,
    p.title,
    p.category_id,
    c.name as category_name,
    COUNT(oi.id) as total_orders,
    SUM(oi.quantity) as total_quantity_sold,
    SUM(oi.total_price) as total_revenue,
    AVG(oi.unit_price) as average_price,
    i.quantity as current_stock
FROM products p
LEFT JOIN order_items oi ON p.id = oi.product_id
LEFT JOIN orders o ON oi.order_id = o.id AND o.status IN ('completed', 'delivered', 'paid_full')
LEFT JOIN categories c ON p.category_id = c.id
LEFT JOIN inventory i ON p.id = i.product_id
GROUP BY p.id, p.title, p.category_id, c.name, i.quantity;

-- View: Daily sales report
CREATE VIEW daily_sales_report AS
SELECT 
    DATE(created_at) as sale_date,
    COUNT(*) as total_orders,
    SUM(total_amount) as total_revenue,
    SUM(deposit_amount) as total_deposits,
    AVG(total_amount) as average_order_value
FROM orders 
WHERE status IN ('completed', 'delivered', 'paid_full')
GROUP BY DATE(created_at)
ORDER BY sale_date DESC;

-- =========================================
-- GRANT FINAL PERMISSIONS
-- =========================================

-- Grant permissions on all newly created objects
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO promoweb;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO promoweb;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO promoweb;

-- Grant usage on custom types
GRANT USAGE ON TYPE order_status TO promoweb;
GRANT USAGE ON TYPE payment_status TO promoweb;
GRANT USAGE ON TYPE payment_gateway TO promoweb;
GRANT USAGE ON TYPE shipping_status TO promoweb;
GRANT USAGE ON TYPE user_role TO promoweb;
GRANT USAGE ON TYPE promotion_type TO promoweb;

-- =========================================
-- COMPLETION MESSAGE
-- =========================================

DO $$
BEGIN
    RAISE NOTICE '✅ PromoWeb database initialization completed successfully!';
    RAISE NOTICE '📊 Tables created: %', (SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public');
    RAISE NOTICE '👤 Default admin user: admin@promoweb.cm (password: admin123!)';
    RAISE NOTICE '💰 Default exchange rate: 1 EUR = 655.957 XAF';
    RAISE NOTICE '🚀 Database is ready for FastAPI application!';
END $$;
