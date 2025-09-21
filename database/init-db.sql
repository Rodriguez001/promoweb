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
