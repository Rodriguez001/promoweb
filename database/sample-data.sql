-- =========================================
-- PromoWeb Africa - Sample Data
-- Sample dataset for database initialization
-- =========================================

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

-- Reset sequences
ALTER SEQUENCE orders_sequence RESTART WITH 1;

-- =========================================
-- SAMPLE USERS
-- =========================================

INSERT INTO users (id, email, password_hash, first_name, last_name, phone, role, is_active, email_verified, phone_verified) VALUES
-- Regular customers
('550e8400-e29b-41d4-a716-446655440001', 'jean.mvondo@gmail.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/lewfBGSGtU4hsuxHq', 'Jean', 'Mvondo', '+237670123456', 'customer', TRUE, TRUE, TRUE),
('550e8400-e29b-41d4-a716-446655440002', 'marie.nkomo@yahoo.fr', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/lewfBGSGtU4hsuxHq', 'Marie', 'Nkomo', '+237680234567', 'customer', TRUE, TRUE, FALSE),
('550e8400-e29b-41d4-a716-446655440003', 'paul.biya@outlook.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/lewfBGSGtU4hsuxHq', 'Paul', 'Biya', '+237690345678', 'customer', TRUE, FALSE, FALSE),
('550e8400-e29b-41d4-a716-446655440004', 'alice.fomo@gmail.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/lewfBGSGtU4hsuxHq', 'Alice', 'Fomo', '+237675456789', 'customer', TRUE, TRUE, TRUE),
-- Store admin
('550e8400-e29b-41d4-a716-446655440005', 'manager@promoweb.cm', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/lewfBGSGtU4hsuxHq', 'Store', 'Manager', '+237655123456', 'admin', TRUE, TRUE, TRUE);

-- =========================================
-- USER ADDRESSES
-- =========================================

INSERT INTO user_addresses (id, user_id, name, street_address, city, region, postal_code, location, is_default) VALUES
('660e8400-e29b-41d4-a716-446655440001', '550e8400-e29b-41d4-a716-446655440001', 'Domicile', 'Quartier Bonapriso, Rue des Cocotiers', 'Douala', 'Littoral', '1001', ST_SetSRID(ST_Point(9.7098, 4.0483), 4326), TRUE),
('660e8400-e29b-41d4-a716-446655440002', '550e8400-e29b-41d4-a716-446655440001', 'Bureau', 'Zone Industrielle Bassa', 'Douala', 'Littoral', '1010', ST_SetSRID(ST_Point(9.6843, 4.0614), 4326), FALSE),
('660e8400-e29b-41d4-a716-446655440003', '550e8400-e29b-41d4-a716-446655440002', 'Maison', 'Quartier Essos, Avenue Kennedy', 'Yaoundé', 'Centre', '2001', ST_SetSRID(ST_Point(11.5174, 3.8480), 4326), TRUE),
('660e8400-e29b-41d4-a716-446655440004', '550e8400-e29b-41d4-a716-446655440004', 'Domicile', 'Quartier Bafoussam-Centre', 'Bafoussam', 'Ouest', '3001', ST_SetSRID(ST_Point(10.4167, 5.4667), 4326), TRUE);

-- =========================================
-- SAMPLE PRODUCTS 
-- =========================================

-- Get category IDs
WITH cat_ids AS (
  SELECT id as livres_id FROM categories WHERE slug = 'livres' LIMIT 1
),
cat_ids2 AS (
  SELECT id as electronique_id FROM categories WHERE slug = 'electronique' LIMIT 1
),
cat_ids3 AS (
  SELECT id as mode_id FROM categories WHERE slug = 'mode' LIMIT 1
)

INSERT INTO products (id, title, slug, description, short_description, brand, category_id, price_eur, price_xaf, cost_price_eur, weight_kg, dimensions_cm, images, tags, is_active, is_featured) VALUES
-- Books (African literature & education)
('770e8400-e29b-41d4-a716-446655440001', 'Une si longue lettre - Mariama Bâ', 'une-si-longue-lettre', 'Roman épistolaire emblématique de la littérature africaine francophone, Prix Noma 1980', 'Chef-d''œuvre de Mariama Bâ sur la condition féminine en Afrique', 'Nouvelles Éditions Africaines', (SELECT id FROM categories WHERE slug = 'livres' LIMIT 1), 15.00, 9839.36, 8.00, 0.250, '19 x 12 x 1.5', '["https://example.com/book1.jpg"]', ARRAY['littérature', 'africaine', 'féminisme'], TRUE, TRUE),

('770e8400-e29b-41d4-a716-446655440002', 'Cahier d''un retour au pays natal - Aimé Césaire', 'cahier-retour-pays-natal', 'Poème fondateur de la négritude par Aimé Césaire', 'Œuvre majeure de la poésie caribéenne et africaine', 'Présence Africaine', (SELECT id FROM categories WHERE slug = 'livres' LIMIT 1), 12.00, 7871.49, 6.50, 0.180, '18 x 11 x 1', '["https://example.com/book2.jpg"]', ARRAY['poésie', 'négritude', 'classique'], TRUE, FALSE),

-- Electronics (popular in Cameroon)
('770e8400-e29b-41d4-a716-446655440003', 'Samsung Galaxy A54 5G', 'samsung-galaxy-a54-5g', 'Smartphone Android avec écran Super AMOLED 6.4", triple caméra 50MP', 'Smartphone performant avec 5G et excellente autonomie', 'Samsung', (SELECT id FROM categories WHERE slug = 'electronique' LIMIT 1), 350.00, 229585.00, 280.00, 0.202, '15.9 x 7.4 x 0.8', '["https://example.com/samsung-a54.jpg"]', ARRAY['smartphone', '5G', 'Android'], TRUE, TRUE),

('770e8400-e29b-41d4-a716-446655440004', 'Tecno Spark 10 Pro', 'tecno-spark-10-pro', 'Smartphone abordable avec écran 6.8" et batterie 5000mAh', 'Excellent rapport qualité-prix pour le marché africain', 'Tecno', (SELECT id FROM categories WHERE slug = 'electronique' LIMIT 1), 180.00, 118073.26, 140.00, 0.193, '16.4 x 7.5 x 0.9', '["https://example.com/tecno-spark10.jpg"]', ARRAY['smartphone', 'batterie longue durée', 'abordable'], TRUE, TRUE);

-- More products (continuing the insert)
INSERT INTO products (id, title, slug, description, short_description, brand, category_id, price_eur, price_xaf, cost_price_eur, weight_kg, dimensions_cm, images, tags, is_active, is_featured) VALUES
-- Fashion items
('770e8400-e29b-41d4-a716-446655440005', 'Boubou Traditionnel Brodé', 'boubou-traditionnel-brode', 'Boubou traditionnel africain en coton brodé à la main', 'Vêtement traditionnel élégant pour hommes', 'Artisans du Cameroun', (SELECT id FROM categories WHERE slug = 'mode' LIMIT 1), 85.00, 55756.35, 45.00, 0.800, '120 x 80 x 5', '["https://example.com/boubou.jpg"]', ARRAY['traditionnel', 'broderie', 'coton'], TRUE, FALSE),

('770e8400-e29b-41d4-a716-446655440006', 'Wax Hollandais Premium', 'wax-hollandais-premium', 'Tissu wax authentique de haute qualité, 6 yards', 'Tissu wax pour confection de vêtements traditionnels', 'Vlisco', (SELECT id FROM categories WHERE slug = 'mode' LIMIT 1), 45.00, 29518.07, 25.00, 0.400, '600 x 120 x 0.2', '["https://example.com/wax-vlisco.jpg"]', ARRAY['wax', 'tissu', 'traditionnel'], TRUE, TRUE),

-- Home & Garden
('770e8400-e29b-41d4-a716-446655440007', 'Moustiquaire Imprégnée', 'moustiquaire-impregnee', 'Moustiquaire imprégnée d''insecticide, protection contre le paludisme', 'Protection efficace recommandée par l''OMS', 'PermaNet', (SELECT id FROM categories WHERE slug = 'maison-jardin' LIMIT 1), 8.00, 5247.66, 4.00, 0.150, '200 x 180 x 0.1', '["https://example.com/moustiquaire.jpg"]', ARRAY['santé', 'paludisme', 'protection'], TRUE, TRUE),

-- Health & Beauty
('770e8400-e29b-41d4-a716-446655440008', 'Beurre de Karité Bio 250g', 'beurre-karite-bio-250g', 'Beurre de karité pur et bio du Burkina Faso', 'Soin naturel pour peau et cheveux', 'Naturel Africa', (SELECT id FROM categories WHERE slug = 'sante-beaute' LIMIT 1), 18.00, 11806.73, 10.00, 0.280, '8 x 8 x 6', '["https://example.com/karite.jpg"]', ARRAY['bio', 'naturel', 'karité'], TRUE, FALSE);

-- =========================================
-- INVENTORY 
-- =========================================

INSERT INTO inventory (product_id, quantity, reserved_quantity, min_threshold, max_threshold) VALUES
('770e8400-e29b-41d4-a716-446655440001', 45, 2, 10, 100),
('770e8400-e29b-41d4-a716-446655440002', 23, 0, 5, 50),
('770e8400-e29b-41d4-a716-446655440003', 12, 3, 5, 30),
('770e8400-e29b-41d4-a716-446655440004', 28, 1, 10, 50),
('770e8400-e29b-41d4-a716-446655440005', 8, 0, 3, 20),
('770e8400-e29b-41d4-a716-446655440006', 35, 5, 15, 100),
('770e8400-e29b-41d4-a716-446655440007', 150, 20, 50, 500),
('770e8400-e29b-41d4-a716-446655440008', 67, 3, 20, 200);

-- =========================================
-- PROMOTIONS
-- =========================================

INSERT INTO promotions (id, name, description, code, type, discount_value, min_order_amount, usage_limit, start_date, end_date, is_active) VALUES
('880e8400-e29b-41d4-a716-446655440001', 'Rentrée Scolaire 2024', 'Promotion sur les livres pour la rentrée', 'RENTREE2024', 'percentage', 15.00, 10000.00, 100, '2024-08-01', '2024-09-30', TRUE),
('880e8400-e29b-41d4-a716-446655440002', 'Nouveaux Clients', 'Réduction pour les nouveaux clients', 'NOUVEAU20', 'percentage', 20.00, 25000.00, 200, '2024-01-01', '2024-12-31', TRUE),
('880e8400-e29b-41d4-a716-446655440003', 'Livraison Gratuite', 'Livraison gratuite au-dessus de 75000 XAF', 'GRATUIT75', 'free_shipping', 0.00, 75000.00, NULL, '2024-01-01', '2024-12-31', TRUE);

-- Apply promotions to products
INSERT INTO product_promotions (product_id, promotion_id) VALUES
('770e8400-e29b-41d4-a716-446655440001', '880e8400-e29b-41d4-a716-446655440001'),
('770e8400-e29b-41d4-a716-446655440002', '880e8400-e29b-41d4-a716-446655440001');

-- =========================================
-- SAMPLE ORDERS
-- =========================================

INSERT INTO orders (id, user_id, status, total_amount, deposit_amount, remaining_amount, shipping_cost, billing_name, billing_email, billing_phone, billing_address, billing_city, billing_region, shipping_name, shipping_address, shipping_city, shipping_region, shipping_location, created_at) VALUES
('990e8400-e29b-41d4-a716-446655440001', '550e8400-e29b-41d4-a716-446655440001', 'delivered', 45000.00, 13500.00, 31500.00, 2000.00, 'Jean Mvondo', 'jean.mvondo@gmail.com', '+237670123456', 'Quartier Bonapriso, Rue des Cocotiers', 'Douala', 'Littoral', 'Jean Mvondo', 'Quartier Bonapriso, Rue des Cocotiers', 'Douala', 'Littoral', ST_SetSRID(ST_Point(9.7098, 4.0483), 4326), '2024-01-15 10:30:00'),
('990e8400-e29b-41d4-a716-446655440002', '550e8400-e29b-41d4-a716-446655440002', 'processing', 89000.00, 26700.00, 62300.00, 2500.00, 'Marie Nkomo', 'marie.nkomo@yahoo.fr', '+237680234567', 'Quartier Essos, Avenue Kennedy', 'Yaoundé', 'Centre', 'Marie Nkomo', 'Quartier Essos, Avenue Kennedy', 'Yaoundé', 'Centre', ST_SetSRID(ST_Point(11.5174, 3.8480), 4326), '2024-02-20 14:15:00');

-- Order items
INSERT INTO order_items (order_id, product_id, quantity, unit_price, total_price, product_snapshot) VALUES
('990e8400-e29b-41d4-a716-446655440001', '770e8400-e29b-41d4-a716-446655440001', 2, 9839.36, 19678.72, '{"title": "Une si longue lettre", "price_xaf": 9839.36}'),
('990e8400-e29b-41d4-a716-446655440001', '770e8400-e29b-41d4-a716-446655440008', 1, 11806.73, 11806.73, '{"title": "Beurre de Karité Bio", "price_xaf": 11806.73}'),
('990e8400-e29b-41d4-a716-446655440002', '770e8400-e29b-41d4-a716-446655440003', 1, 229585.00, 229585.00, '{"title": "Samsung Galaxy A54 5G", "price_xaf": 229585.00}');

-- =========================================
-- EXCHANGE RATES (Historical)
-- =========================================

INSERT INTO exchange_rates (from_currency, to_currency, rate, date, source) VALUES
('EUR', 'XAF', 650.000, '2024-01-01', 'ECB'),
('EUR', 'XAF', 655.957, '2024-01-15', 'ECB'),
('EUR', 'XAF', 658.234, '2024-02-01', 'ECB'),
('EUR', 'XAF', 662.150, '2024-02-15', 'ECB');

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
