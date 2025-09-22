-- =========================================
-- PromoWeb Africa - Sample Data
-- Sample dataset for database initialization
-- =========================================

-- Create sequence for order numbers if it doesn't exist
CREATE SEQUENCE IF NOT EXISTS orders_sequence START 1001;

-- Clear existing sample data (except admin)
-- DELETE FROM cart_items;
-- DELETE FROM carts;
-- DELETE FROM order_items;
-- DELETE FROM order_status_history;
-- DELETE FROM payments;
-- DELETE FROM shipping;
-- DELETE FROM orders;
-- DELETE FROM product_promotions;
-- DELETE FROM promotions;
-- DELETE FROM inventory;
-- DELETE FROM products;
-- DELETE FROM user_addresses;
-- DELETE FROM users WHERE email != 'admin@promoweb.cm';

-- =========================================
-- SAMPLE ORDERS
-- =========================================

INSERT INTO orders (id, order_number, user_id, status, total_amount, deposit_amount, remaining_amount, shipping_cost, billing_name, billing_email, billing_phone, billing_address, billing_city, billing_region, shipping_name, shipping_address, shipping_city, shipping_region, shipping_location, created_at) VALUES
('990e8400-e29b-41d4-a716-446655440001', '1001', '550e8400-e29b-41d4-a716-446655440001', 'delivered', 45000.00, 13500.00, 31500.00, 2000.00, 'Jean Mvondo', 'jean.mvondo@gmail.com', '+237670123456', 'Quartier Bonapriso, Rue des Cocotiers', 'Douala', 'Littoral', 'Jean Mvondo', 'Quartier Bonapriso, Rue des Cocotiers', 'Douala', 'Littoral', ST_SetSRID(ST_Point(9.7098, 4.0483), 4326), '2024-01-15 10:30:00'),
('990e8400-e29b-41d4-a716-446655440002', '1002', '550e8400-e29b-41d4-a716-446655440002', 'processing', 89000.00, 26700.00, 62300.00, 2500.00, 'Marie Nkomo', 'marie.nkomo@yahoo.fr', '+237680234567', 'Quartier Essos, Avenue Kennedy', 'Yaoundé', 'Centre', 'Marie Nkomo', 'Quartier Essos, Avenue Kennedy', 'Yaoundé', 'Centre', ST_SetSRID(ST_Point(11.5174, 3.8480), 4326), '2024-02-20 14:15:00');

-- Order items
INSERT INTO order_items (order_id, product_id, quantity, unit_price, total_price, product_snapshot) VALUES
('990e8400-e29b-41d4-a716-446655440001', '770e8400-e29b-41d4-a716-446655440001', 2, 9839.36, 19678.72, '{"title": "Une si longue lettre", "price_xaf": 9839.36}'),
('990e8400-e29b-41d4-a716-446655440001', '770e8400-e29b-41d4-a716-446655440008', 1, 11806.73, 11806.73, '{"title": "Beurre de Karité Bio", "price_xaf": 11806.73}'),
('990e8400-e29b-41d4-a716-446655440002', '770e8400-e29b-41d4-a716-446655440003', 1, 229585.00, 229585.00, '{"title": "Samsung Galaxy A54 5G", "price_xaf": 229585.00}');

-- =========================================
-- EXCHANGE RATES (Historical)
-- =========================================

-- Create system_settings table if it doesn't exist
CREATE TABLE IF NOT EXISTS system_settings (
    key VARCHAR(255) PRIMARY KEY,
    value TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

INSERT INTO exchange_rates (id, from_currency, to_currency, rate, date, source, created_at, updated_at) VALUES
('880e8400-e29b-41d4-a716-446655440001', 'EUR', 'XAF', 650.00, '2024-01-01', 'ECB', NOW(), NOW()),
('880e8400-e29b-41d4-a716-446655440002', 'EUR', 'XAF', 655.957, '2024-01-15', 'ECB', NOW(), NOW()),
('880e8400-e29b-41d4-a716-446655440003', 'EUR', 'XAF', 658.234, '2024-02-01', 'ECB', NOW(), NOW()),
('880e8400-e29b-41d4-a716-446655440004', 'EUR', 'XAF', 662.150, '2024-02-15', 'ECB', NOW(), NOW());

-- Update system settings with current rate
UPDATE system_settings SET value = '662.150' WHERE key = 'current_eur_xaf_rate';
INSERT INTO system_settings (key, value, description) VALUES ('current_eur_xaf_rate', '662.150', 'Current EUR to XAF exchange rate') ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value;

-- =========================================
-- COMPLETION MESSAGE
-- =========================================

DO $$
BEGIN
    RAISE NOTICE '✅ Sample data inserted successfully!';
    RAISE NOTICE '👥 Users: % (including admin)', (SELECT COUNT(*) FROM users);
    RAISE NOTICE '📦 Products: %', (SELECT COUNT(*) FROM products);
    RAISE NOTICE '🛒 Orders: %', (SELECT COUNT(*) FROM orders);
    RAISE NOTICE '🎯 Sample data ready for testing!';
END $$;
