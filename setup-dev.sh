#!/bin/bash

# PromoWeb Africa - Development Setup Script
# This script sets up the development environment

set -e

echo "🚀 Setting up PromoWeb Africa development environment..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    echo "   Visit: https://docs.docker.com/get-docker/"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    echo "   Visit: https://docs.docker.com/compose/install/"
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 18+ first."
    echo "   Visit: https://nodejs.org/"
    exit 1
fi

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.9+ first."
    echo "   Visit: https://python.org/"
    exit 1
fi

echo "✅ Prerequisites check passed"

# Create environment files
echo "📝 Creating environment files..."

# Backend environment
if [ ! -f "backend/.env" ]; then
    cp backend/env.example backend/.env
    echo "✅ Created backend/.env from example"
else
    echo "⚠️  backend/.env already exists"
fi

# Frontend environment
if [ ! -f "frontend/.env.local" ]; then
    cp frontend/env.example frontend/.env.local
    echo "✅ Created frontend/.env.local from example"
else
    echo "⚠️  frontend/.env.local already exists"
fi

# Install frontend dependencies
echo "📦 Installing frontend dependencies..."
cd frontend
npm install
if [ $? -eq 0 ]; then
    echo "✅ Frontend dependencies installed successfully"
else
    echo "❌ Failed to install frontend dependencies"
    exit 1
fi
cd ..

# Install backend dependencies
echo "📦 Installing backend dependencies..."
cd backend
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
if [ $? -eq 0 ]; then
    echo "✅ Backend dependencies installed successfully"
else
    echo "❌ Failed to install backend dependencies"
    exit 1
fi
cd ..

# Start Docker services
echo "🐳 Starting Docker services..."
docker-compose up -d postgres redis
if [ $? -eq 0 ]; then
    echo "✅ Docker services started successfully"
else
    echo "❌ Failed to start Docker services"
    exit 1
fi

# Wait for database to be ready
echo "⏳ Waiting for database to be ready..."
sleep 10

# Run database migrations
echo "🔄 Running database migrations..."
cd backend
source venv/bin/activate
alembic upgrade head
if [ $? -eq 0 ]; then
    echo "✅ Database migrations completed"
else
    echo "❌ Database migrations failed"
    exit 1
fi
cd ..

# Create initial admin user
echo "👤 Creating initial admin user..."
cd backend
source venv/bin/activate
python -c "
import asyncio
from app.scripts.create_admin import create_initial_admin
asyncio.run(create_initial_admin())
"
cd ..

echo ""
echo "🎉 Development environment setup completed!"
echo ""
echo "📍 Quick Start:"
echo "   1. Start backend: cd backend && source venv/bin/activate && uvicorn app.main:app --reload"
echo "   2. Start frontend: cd frontend && npm run dev"
echo "   3. Visit: http://localhost:3000"
echo ""
echo "📊 Services:"
echo "   Frontend: http://localhost:3000"
echo "   Backend API: http://localhost:8000"
echo "   API Documentation: http://localhost:8000/docs"
echo "   pgAdmin: http://localhost:5050 (admin@promoweb.cm / admin123)"
echo ""
echo "🛠️  Commands:"
echo "   Start all services: docker-compose up"
echo "   Stop all services: docker-compose down"
echo "   View logs: docker-compose logs -f [service]"
echo ""
echo "📝 Next steps:"
echo "   1. Update environment variables in .env files"
echo "   2. Configure payment gateways (Stripe, Orange Money, MTN)"
echo "   3. Set up email service (SMTP)"
echo "   4. Configure SMS service (Twilio/Africa's Talking)"
echo ""
echo "✅ Happy coding! 🚀"
