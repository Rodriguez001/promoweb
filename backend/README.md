# PromoWeb Africa - Backend API

Backend API for PromoWeb Africa e-commerce platform, built with NestJS and TypeScript.

## Features

- **Authentication & Authorization**: JWT-based auth with role-based access control
- **Product Catalog**: Complete product management with categories, search, and filtering
- **Order Management**: Full order lifecycle with status tracking
- **Payment Processing**: Mobile Money (Orange/MTN) and card payment support
- **Shipping & Tracking**: Delivery management with real-time tracking
- **Admin Dashboard**: Comprehensive admin panel for inventory and order management
- **API Documentation**: Auto-generated Swagger documentation
- **Database**: PostgreSQL with TypeORM for data persistence

## Technology Stack

- **Framework**: NestJS 11.x
- **Language**: TypeScript
- **Database**: PostgreSQL with TypeORM
- **Authentication**: JWT + Passport
- **Validation**: class-validator & class-transformer
- **Documentation**: Swagger/OpenAPI
- **Security**: bcryptjs for password hashing, rate limiting

## Prerequisites

- Node.js 18+ 
- PostgreSQL 14+
- npm or yarn

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd promoweb/backend
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Environment Setup**
   ```bash
   cp .env.example .env
   ```
   
   Update the `.env` file with your configuration:
   ```env
   # Database
   DB_HOST=localhost
   DB_PORT=5432
   DB_USERNAME=postgres
   DB_PASSWORD=your_password
   DB_NAME=promoweb_africa
   
   # JWT
   JWT_SECRET=your-super-secret-jwt-key
   JWT_EXPIRES_IN=7d
   
   # Server
   PORT=3001
   API_PREFIX=api/v1
   CORS_ORIGIN=http://localhost:3000
   ```

4. **Database Setup**
   ```bash
   # Create database and run initial setup
   npm run db:setup
   
   # Or seed data separately
   npm run db:seed
   ```

## Running the Application

```bash
# Development mode with hot reload
npm run start:dev

# Production mode
npm run start:prod

# Debug mode
npm run start:debug
```

The API will be available at:
- **API**: http://localhost:3001/api/v1
- **Documentation**: http://localhost:3001/docs

## API Documentation

Interactive API documentation is available at `/docs` when the server is running.

### Key Endpoints

- **Authentication**: `/api/v1/auth/*`
- **Products**: `/api/v1/products/*`
- **Categories**: `/api/v1/categories/*`
- **Orders**: `/api/v1/orders/*`
- **Payments**: `/api/v1/payments/*`
- **Shipments**: `/api/v1/shipments/*`
- **Admin**: `/api/v1/admin/*`

## Database Schema

### Core Entities

- **User**: Customer and admin user management
- **Product**: Product catalog with pricing and inventory
- **Category**: Hierarchical product categorization
- **Order**: Order management with status tracking
- **OrderItem**: Individual items within orders
- **Payment**: Payment processing and tracking
- **Shipment**: Shipping and delivery tracking

## Authentication

The API uses JWT-based authentication with role-based access control:

- **Customer**: Can browse products, place orders, track shipments
- **Admin**: Full access to all resources and admin dashboard

### Usage Example

```bash
# Login
curl -X POST http://localhost:3001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password"}'

# Use token in subsequent requests
curl -X GET http://localhost:3001/api/v1/orders \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## Testing

```bash
# Unit tests
npm run test

# E2E tests
npm run test:e2e

# Test coverage
npm run test:cov
```

## Development Scripts

```bash
# Database
npm run db:setup          # Setup database and seed initial data
npm run db:seed           # Seed initial data only

# Development
npm run start:dev         # Start with hot reload
npm run start:debug       # Start in debug mode

# Code Quality
npm run lint              # Run ESLint
npm run format            # Format code with Prettier

# Build
npm run build             # Build for production
```

## Project Structure

```
src/
├── database/
│   ├── entities/         # TypeORM entities
│   ├── seeds/           # Database seeding
│   └── database.module.ts
├── modules/
│   ├── auth/            # Authentication & authorization
│   ├── users/           # User management
│   ├── products/        # Product catalog
│   ├── categories/      # Product categories
│   ├── orders/          # Order management
│   ├── payments/        # Payment processing
│   ├── shipments/       # Shipping & tracking
│   └── admin/           # Admin dashboard
├── app.module.ts        # Main application module
└── main.ts             # Application entry point
```

## Environment Variables

See `.env.example` for all available configuration options including:

- Database connection
- JWT configuration
- CORS settings
- Rate limiting
- File upload settings
- Email configuration
- Mobile Money API settings
- Currency conversion API
- Shipping provider settings

## Deployment

1. **Build the application**
   ```bash
   npm run build
   ```

2. **Set production environment variables**

3. **Run database migrations**
   ```bash
   npm run db:setup
   ```

4. **Start the application**
   ```bash
   npm run start:prod
   ```

## License

This project is licensed under the MIT License.
