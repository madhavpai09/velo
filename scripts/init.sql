-- Database initialization script for Mini Uber
-- This script is run automatically when the database container starts

-- Create extensions
CREATE EXTENSION IF NOT EXISTS uuid-ossp;
CREATE EXTENSION IF NOT EXISTS pg_trgm;  -- For full-text search

-- Create schemas
CREATE SCHEMA IF NOT EXISTS public;

-- Verify tables will be created by SQLAlchemy ORM
-- This file ensures basic setup is ready

-- Create indexes for performance (can also be done in migrations)
-- Note: These will be created by the application on startup via models
