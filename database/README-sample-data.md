# PromoWeb Sample Data

This directory contains sample data for initializing your PromoWeb database with realistic test data for development and testing purposes.

## Files

- **`sample-data.sql`** - Main sample dataset with comprehensive test data
- **`load-sample-data.sh`** - Bash script to load sample data automatically
- **`init-promoweb.sql`** - Database schema initialization
- **`init-db.sql`** - Database and user creation

## Sample Data Contents

### 👥 Users (6 total)
- **Super Admin**: `admin@promoweb.cm` (password: `admin123!`)
- **Store Manager**: `manager@promoweb.cm` (password: `admin123!`) 
- **Customers**: 
  - `jean.mvondo@gmail.com` (Douala)
  - `marie.nkomo@yahoo.fr` (Yaoundé)
  - `paul.biya@outlook.com` (not verified)
  - `alice.fomo@gmail.com` (Bafoussam)

### 📦 Products (8 items)
- **African Literature**: Mariama Bâ, Aimé Césaire books
- **Electronics**: Samsung Galaxy A54, Tecno Spark 10 Pro
- **Fashion**: Traditional Boubou, Vlisco Wax fabric
- **Health**: Anti-malaria mosquito nets, organic shea butter

### 🛒 Sample Orders
- Delivered order from Jean Mvondo (books + shea butter)
- Processing order from Marie Nkomo (Samsung phone)

### 🎯 Categories
- Livres (Books)
- Électronique (Electronics) 
- Mode (Fashion)
- Maison & Jardin (Home & Garden)
- Santé & Beauté (Health & Beauty)

### 🚚 Shipping Zones (Cameroon regions)
All 10 regions with realistic shipping costs and delivery times:
- Urban zones (Douala, Yaoundé): 1-2 days
- Regional capitals: 3-8 days  
- Remote areas: 10-12 days

### 💰 Exchange Rates
Historical EUR/XAF rates with current rate: 662.150

## Usage

### Method 1: Using the load script (Recommended)
```bash
cd database/
chmod +x load-sample-data.sh
./load-sample-data.sh
```

### Method 2: Manual loading
```bash
# Ensure database is initialized first
psql -U promoweb -d promoweb -f init-promoweb.sql

# Load sample data
psql -U promoweb -d promoweb -f sample-data.sql
```

### Method 3: Docker Compose
```bash
# If using Docker, the sample data will be loaded automatically
docker-compose up -d database
```

## Environment Variables

The load script supports these environment variables:

```bash
export DB_HOST=localhost      # Database host
export DB_PORT=5432          # Database port  
export DB_NAME=promoweb      # Database name
export DB_USER=promoweb      # Database user
export DB_PASSWORD=password_2024  # Database password
```

## Test Scenarios

### Authentication Testing
- Use any sample user email with password `admin123!`
- Test email verification flows with unverified users
- Test admin vs customer role permissions

### E-commerce Testing  
- Browse products by category
- Test search functionality with African product names
- Add items to cart and checkout process
- Test promotion codes: `RENTREE2024`, `NOUVEAU20`, `GRATUIT75`

### Geographic Testing
- Test shipping cost calculations for different Cameroon regions
- Test address validation with PostGIS coordinates
- Test delivery time estimates

### Payment Testing
- Test 30% deposit system (acompte)
- Test multiple payment gateways (Orange Money, MTN MoMo, Stripe, COD)
- Test payment status workflows

### Inventory Testing
- Test stock management with reserved quantities
- Test low stock notifications
- Test product availability checks

## Data Localization

All sample data is localized for the Cameroon/Central Africa market:

- **Names**: Common Cameroonian names (Mvondo, Nkomo, Fomo)
- **Addresses**: Real Cameroon cities and regions
- **Phone Numbers**: Cameroon format (+237...)
- **Products**: Local market relevant items
- **Currency**: XAF (Central African Franc)
- **Languages**: French descriptions (official language)

## Resetting Sample Data

To reset and reload sample data:

```sql
-- Clear all sample data (keeps schema)
DELETE FROM cart_items;
DELETE FROM carts; 
DELETE FROM order_items;
DELETE FROM orders;
DELETE FROM products;
DELETE FROM users WHERE email != 'admin@promoweb.cm';

-- Reload sample data
\i sample-data.sql
```

## Production Notes

⚠️ **Important**: This sample data is for development/testing only. Never load this data in production environments.

For production initialization, only run:
- `init-db.sql` (database setup)
- `init-promoweb.sql` (schema only)

Skip the sample data files completely.
