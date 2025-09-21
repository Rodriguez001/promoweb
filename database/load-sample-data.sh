#!/bin/bash
# =========================================
# PromoWeb Africa - Sample Data Loader
# Load sample data into PostgreSQL database
# =========================================

set -e  # Exit on any error

# Database configuration
DB_HOST=${DB_HOST:-localhost}
DB_PORT=${DB_PORT:-5432}
DB_NAME=${DB_NAME:-promoweb} 
DB_USER=${DB_USER:-promoweb}
DB_PASSWORD=${DB_PASSWORD:-password_2024}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}==========================================${NC}"
echo -e "${BLUE} PromoWeb Sample Data Loader${NC}"
echo -e "${BLUE}==========================================${NC}"

# Check if PostgreSQL client is available
if ! command -v psql &> /dev/null; then
    echo -e "${RED}Error: psql client not found. Please install PostgreSQL client tools.${NC}"
    exit 1
fi

# Check database connection
echo -e "${YELLOW}Testing database connection...${NC}"
export PGPASSWORD=$DB_PASSWORD
if ! psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "SELECT 1;" &> /dev/null; then
    echo -e "${RED}Error: Cannot connect to database. Please check your connection settings.${NC}"
    echo -e "${YELLOW}Host: $DB_HOST, Port: $DB_PORT, Database: $DB_NAME, User: $DB_USER${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Database connection successful!${NC}"

# Load sample data
echo -e "${YELLOW}Loading sample data...${NC}"
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f sample-data.sql

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Sample data loaded successfully!${NC}"
    
    # Display summary
    echo -e "${BLUE}==========================================${NC}"
    echo -e "${BLUE} Sample Data Summary${NC}"
    echo -e "${BLUE}==========================================${NC}"
    
    echo -e "${YELLOW}📊 Database Statistics:${NC}"
    psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -t -c "
        SELECT 
            '👥 Users: ' || COUNT(*) FROM users;
        SELECT 
            '📦 Products: ' || COUNT(*) FROM products;
        SELECT 
            '🛒 Orders: ' || COUNT(*) FROM orders;
        SELECT 
            '🎯 Categories: ' || COUNT(*) FROM categories;
        SELECT 
            '🚚 Shipping Zones: ' || COUNT(*) FROM shipping_zones;
    "
    
    echo -e "${YELLOW}🔑 Test Accounts:${NC}"
    echo -e "Super Admin: admin@promoweb.cm (password: admin123!)"
    echo -e "Store Manager: manager@promoweb.cm (password: admin123!)"
    echo -e "Customer: jean.mvondo@gmail.com (password: admin123!)"
    
    echo -e "${GREEN}🚀 Ready for testing!${NC}"
else
    echo -e "${RED}❌ Error loading sample data${NC}"
    exit 1
fi
