#!/bin/bash

# PromoWeb Africa - Production Deployment Script
# This script deploys the application to production environment

set -e  # Exit on any error

echo "🚀 Starting PromoWeb Africa deployment..."

# Configuration
ENVIRONMENT=${1:-production}
COMPOSE_FILE="docker-compose.yml"
COMPOSE_PROD_FILE="docker-compose.prod.yml"

echo "📋 Environment: $ENVIRONMENT"

# Check if Docker and Docker Compose are installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p logs
mkdir -p uploads
mkdir -p backups

# Set permissions
chmod 755 logs uploads backups

# Load environment variables
if [ -f ".env.${ENVIRONMENT}" ]; then
    echo "🔧 Loading environment variables from .env.${ENVIRONMENT}"
    export $(cat .env.${ENVIRONMENT} | xargs)
else
    echo "⚠️  Warning: .env.${ENVIRONMENT} file not found"
fi

# Build and start services
echo "🔨 Building Docker images..."
if [ "$ENVIRONMENT" = "production" ]; then
    if [ -f "$COMPOSE_PROD_FILE" ]; then
        docker-compose -f $COMPOSE_FILE -f $COMPOSE_PROD_FILE build --no-cache
    else
        docker-compose -f $COMPOSE_FILE build --no-cache
    fi
else
    docker-compose build --no-cache
fi

# Stop existing containers
echo "🛑 Stopping existing containers..."
docker-compose down

# Start the database first
echo "🗄️  Starting database..."
docker-compose up -d postgres redis

# Wait for database to be ready
echo "⏳ Waiting for database to be ready..."
sleep 30

# Run database migrations
echo "🔄 Running database migrations..."
docker-compose run --rm backend alembic upgrade head

# Start all services
echo "🚀 Starting all services..."
if [ "$ENVIRONMENT" = "production" ]; then
    if [ -f "$COMPOSE_PROD_FILE" ]; then
        docker-compose -f $COMPOSE_FILE -f $COMPOSE_PROD_FILE up -d
    else
        docker-compose up -d
    fi
else
    docker-compose up -d
fi

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 20

# Health checks
echo "🏥 Running health checks..."

# Check backend health
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Backend is healthy"
else
    echo "❌ Backend health check failed"
fi

# Check frontend health
if curl -f http://localhost:3000 > /dev/null 2>&1; then
    echo "✅ Frontend is healthy"
else
    echo "❌ Frontend health check failed"
fi

# Check database connection
if docker-compose exec -T postgres pg_isready -U postgres -d promoweb > /dev/null 2>&1; then
    echo "✅ Database is healthy"
else
    echo "❌ Database health check failed"
fi

# Show running containers
echo "📊 Container status:"
docker-compose ps

# Show logs for any failed containers
echo "📋 Checking for any failed containers..."
FAILED_CONTAINERS=$(docker-compose ps --filter "health=unhealthy" --format "table {{.Name}}")
if [ ! -z "$FAILED_CONTAINERS" ]; then
    echo "❌ Failed containers detected:"
    echo "$FAILED_CONTAINERS"
    echo "📋 Showing logs for failed containers:"
    docker-compose logs --tail=50 $(echo "$FAILED_CONTAINERS" | tail -n +2 | awk '{print $1}')
fi

# Create initial admin user (only for first deployment)
if [ "$ENVIRONMENT" = "production" ] && [ ! -f ".admin_created" ]; then
    echo "👤 Creating initial admin user..."
    docker-compose exec -T backend python -c "
from app.scripts.create_admin import create_initial_admin
create_initial_admin()
"
    touch .admin_created
    echo "✅ Initial admin user created"
fi

# Setup SSL certificates (if in production)
if [ "$ENVIRONMENT" = "production" ]; then
    echo "🔒 Setting up SSL certificates..."
    # Add SSL setup commands here
    echo "⚠️  Please configure SSL certificates manually"
fi

# Show deployment summary
echo ""
echo "🎉 Deployment completed successfully!"
echo ""
echo "📍 Application URLs:"
echo "   Frontend: http://localhost:3000"
echo "   Backend API: http://localhost:8000"
echo "   API Documentation: http://localhost:8000/docs"
echo "   pgAdmin: http://localhost:5050"
echo ""
echo "🔐 Default credentials:"
echo "   pgAdmin: admin@promoweb.cm / admin123"
echo ""
echo "📊 Monitoring:"
echo "   View logs: docker-compose logs -f [service]"
echo "   Container status: docker-compose ps"
echo "   Resource usage: docker stats"
echo ""
echo "🛠️  Management commands:"
echo "   Stop: docker-compose down"
echo "   Restart: docker-compose restart"
echo "   Update: ./deploy.sh $ENVIRONMENT"
echo ""

# Save deployment info
cat > deployment-info.txt << EOF
Deployment Information
=====================
Date: $(date)
Environment: $ENVIRONMENT
Git Commit: $(git rev-parse HEAD 2>/dev/null || echo "N/A")
Docker Compose Version: $(docker-compose --version)
Docker Version: $(docker --version)

Services Status:
$(docker-compose ps)
EOF

echo "📄 Deployment information saved to deployment-info.txt"

echo "✅ PromoWeb Africa is now running!"
