#!/bin/bash

# PromoWeb Africa - Complete Installation Script
# This script installs all dependencies and sets up the entire project

set -e

echo "🛍️ PromoWeb Africa - Complete Installation"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
print_status "Checking prerequisites..."

if ! command -v node &> /dev/null; then
    print_error "Node.js is not installed. Please install Node.js 18+ first."
    exit 1
fi

if ! command -v npm &> /dev/null; then
    print_error "npm is not installed. Please install npm first."
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed. Please install Python 3.9+ first."
    exit 1
fi

if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

print_success "All prerequisites are installed"

# Install Frontend Dependencies
print_status "Installing frontend dependencies..."
cd frontend

# Create package-lock.json if it doesn't exist
if [ ! -f package-lock.json ]; then
    print_status "Creating package-lock.json..."
    npm install --package-lock-only
fi

# Install dependencies
npm install
if [ $? -eq 0 ]; then
    print_success "Frontend dependencies installed successfully"
else
    print_error "Failed to install frontend dependencies"
    exit 1
fi

# Build the frontend to check for errors
print_status "Building frontend to verify installation..."
npm run build
if [ $? -eq 0 ]; then
    print_success "Frontend builds successfully"
else
    print_warning "Frontend build has warnings/errors but continuing..."
fi

cd ..

# Install Backend Dependencies
print_status "Installing backend dependencies..."
cd backend

# Create virtual environment
if [ ! -d "venv" ]; then
    print_status "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
print_status "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
print_status "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
print_status "Installing Python packages..."
pip install -r requirements.txt
if [ $? -eq 0 ]; then
    print_success "Backend dependencies installed successfully"
else
    print_error "Failed to install backend dependencies"
    exit 1
fi

cd ..

# Setup Environment Files
print_status "Setting up environment files..."

if [ ! -f "frontend/.env.local" ]; then
    cp frontend/env.example frontend/.env.local
    print_success "Created frontend/.env.local"
else
    print_warning "frontend/.env.local already exists"
fi

if [ ! -f "backend/.env" ]; then
    cp backend/env.example backend/.env
    print_success "Created backend/.env"
else
    print_warning "backend/.env already exists"
fi

# Create necessary directories
print_status "Creating necessary directories..."
mkdir -p logs
mkdir -p uploads
mkdir -p backups
mkdir -p frontend/public/icons
mkdir -p backend/uploads

print_success "Directories created"

# Set permissions
chmod 755 logs uploads backups
chmod +x deploy.sh setup-dev.sh

print_success "Permissions set"

# Start Docker Services
print_status "Starting Docker services..."
docker-compose up -d postgres redis

# Wait for services
print_status "Waiting for services to start..."
sleep 15

# Check if services are running
if docker-compose ps | grep -q "postgres.*Up"; then
    print_success "PostgreSQL is running"
else
    print_error "PostgreSQL failed to start"
    exit 1
fi

if docker-compose ps | grep -q "redis.*Up"; then
    print_success "Redis is running"
else
    print_error "Redis failed to start"
    exit 1
fi

# Run Database Migrations
print_status "Running database migrations..."
cd backend
source venv/bin/activate
alembic upgrade head
if [ $? -eq 0 ]; then
    print_success "Database migrations completed"
else
    print_error "Database migrations failed"
    exit 1
fi
cd ..

# Create placeholder images
print_status "Creating placeholder images..."
cd frontend/public

# Create simple placeholder SVGs
cat > placeholder-product.svg << 'EOF'
<svg width="400" height="400" xmlns="http://www.w3.org/2000/svg">
  <rect width="400" height="400" fill="#f3f4f6"/>
  <text x="200" y="200" text-anchor="middle" font-family="Arial" font-size="16" fill="#6b7280">Product Image</text>
</svg>
EOF

cat > icons/icon-192x192.png << 'EOF'
# This would be a real PNG file in production
EOF

print_success "Placeholder images created"
cd ../..

print_success "🎉 Installation completed successfully!"
echo ""
echo "📍 Next Steps:"
echo "=============="
echo ""
echo "1. 🔧 Configure your environment:"
echo "   - Edit frontend/.env.local with your API keys"
echo "   - Edit backend/.env with your database and service credentials"
echo ""
echo "2. 🚀 Start the development servers:"
echo "   - Backend: cd backend && source venv/bin/activate && uvicorn app.main:app --reload"
echo "   - Frontend: cd frontend && npm run dev"
echo ""
echo "3. 🌐 Access your application:"
echo "   - Frontend: http://localhost:3000"
echo "   - Backend API: http://localhost:8000"
echo "   - API Docs: http://localhost:8000/docs"
echo "   - pgAdmin: http://localhost:5050"
echo ""
echo "4. 🔑 Configure services:"
echo "   - Stripe payment gateway"
echo "   - Orange Money & MTN Mobile Money"
echo "   - Email service (SMTP)"
echo "   - SMS service (Twilio/Africa's Talking)"
echo ""
echo "📚 Documentation:"
echo "   - API Documentation: http://localhost:8000/docs"
echo "   - Frontend Storybook: npm run storybook (if configured)"
echo ""
echo "🛠️  Useful Commands:"
echo "   - Start all: docker-compose up"
echo "   - Stop all: docker-compose down"
echo "   - View logs: docker-compose logs -f [service]"
echo "   - Reset DB: docker-compose down -v && docker-compose up -d postgres"
echo ""
print_success "Happy coding! 🚀💼"
