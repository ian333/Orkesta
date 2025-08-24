-- Install required PostgreSQL extensions
-- This file is executed when the container starts for the first time

-- Vector similarity search
CREATE EXTENSION IF NOT EXISTS vector;

-- Trigram matching for fuzzy search
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Text normalization (remove accents)
CREATE EXTENSION IF NOT EXISTS unaccent;

-- GIN indexes for composite types
CREATE EXTENSION IF NOT EXISTS btree_gin;

-- Query statistics
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- JSONB functions
CREATE EXTENSION IF NOT EXISTS ltree;