-- Performance-optimized indexes for catalog extraction system

-- Function to create optimized indexes for a tenant
CREATE OR REPLACE FUNCTION create_tenant_indexes(tenant_id TEXT)
RETURNS void AS $$
DECLARE
    schema_name TEXT := 'tenant_' || tenant_id;
BEGIN
    
    -- Products table indexes
    
    -- Vector similarity search (HNSW for fast approximate search)
    EXECUTE format('
    CREATE INDEX IF NOT EXISTS idx_%s_products_name_embedding 
    ON %I.products USING hnsw (name_embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64)
    ', tenant_id, schema_name);
    
    EXECUTE format('
    CREATE INDEX IF NOT EXISTS idx_%s_products_description_embedding 
    ON %I.products USING hnsw (description_embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64)
    ', tenant_id, schema_name);
    
    -- Full-text search indexes
    EXECUTE format('
    CREATE INDEX IF NOT EXISTS idx_%s_products_search_text 
    ON %I.products USING gin(to_tsvector(''spanish'', 
        COALESCE(name, '''') || '' '' || 
        COALESCE(description, '''') || '' '' || 
        COALESCE(category, '''')
    ))
    ', tenant_id, schema_name);
    
    -- Fuzzy search with trigrams
    EXECUTE format('
    CREATE INDEX IF NOT EXISTS idx_%s_products_name_trgm 
    ON %I.products USING gin(name gin_trgm_ops)
    ', tenant_id, schema_name);
    
    EXECUTE format('
    CREATE INDEX IF NOT EXISTS idx_%s_products_normalized_name_trgm 
    ON %I.products USING gin(normalized_name gin_trgm_ops)
    ', tenant_id, schema_name);
    
    -- Regular B-tree indexes for exact lookups
    EXECUTE format('
    CREATE INDEX IF NOT EXISTS idx_%s_products_sku 
    ON %I.products (tenant_id, sku)
    ', tenant_id, schema_name);
    
    EXECUTE format('
    CREATE INDEX IF NOT EXISTS idx_%s_products_category 
    ON %I.products (tenant_id, category, subcategory)
    ', tenant_id, schema_name);
    
    EXECUTE format('
    CREATE INDEX IF NOT EXISTS idx_%s_products_price 
    ON %I.products (tenant_id, price) 
    WHERE price IS NOT NULL
    ', tenant_id, schema_name);
    
    EXECUTE format('
    CREATE INDEX IF NOT EXISTS idx_%s_products_availability 
    ON %I.products (tenant_id, is_available, stock) 
    WHERE is_available = true
    ', tenant_id, schema_name);
    
    -- JSONB indexes for source references
    EXECUTE format('
    CREATE INDEX IF NOT EXISTS idx_%s_products_source_refs 
    ON %I.products USING gin(source_references)
    ', tenant_id, schema_name);
    
    -- Extraction patterns indexes
    EXECUTE format('
    CREATE INDEX IF NOT EXISTS idx_%s_extraction_patterns_domain 
    ON %I.extraction_patterns (domain, pattern_type, success_rate DESC)
    ', tenant_id, schema_name);
    
    EXECUTE format('
    CREATE INDEX IF NOT EXISTS idx_%s_extraction_patterns_usage 
    ON %I.extraction_patterns (times_used DESC, last_used_at DESC)
    ', tenant_id, schema_name);
    
    -- Extraction jobs indexes
    EXECUTE format('
    CREATE INDEX IF NOT EXISTS idx_%s_extraction_jobs_status 
    ON %I.extraction_jobs (status, created_at DESC)
    ', tenant_id, schema_name);
    
    EXECUTE format('
    CREATE INDEX IF NOT EXISTS idx_%s_extraction_jobs_timing 
    ON %I.extraction_jobs (started_at, completed_at) 
    WHERE started_at IS NOT NULL
    ', tenant_id, schema_name);
    
    -- Consolidation log indexes
    EXECUTE format('
    CREATE INDEX IF NOT EXISTS idx_%s_consolidation_log_master 
    ON %I.consolidation_log (master_product_id, consolidated_at DESC)
    ', tenant_id, schema_name);
    
    EXECUTE format('
    CREATE INDEX IF NOT EXISTS idx_%s_consolidation_log_duplicates 
    ON %I.consolidation_log USING gin(duplicate_product_ids)
    ', tenant_id, schema_name);
    
    RAISE NOTICE 'Created optimized indexes for tenant %', tenant_id;
    
END;
$$ LANGUAGE plpgsql;

-- Create indexes for common query patterns across all tenants
CREATE INDEX IF NOT EXISTS idx_tenants_active ON tenants (is_active, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_tenants_settings ON tenants USING gin(settings);
CREATE INDEX IF NOT EXISTS idx_tenants_extraction_config ON tenants USING gin(extraction_config);