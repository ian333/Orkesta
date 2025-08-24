-- Multi-tenant architecture with Row Level Security
-- Each tenant gets isolated data access

-- Master tenants table (public)
CREATE TABLE IF NOT EXISTS tenants (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    settings JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    
    -- Configuration for catalog extraction
    extraction_config JSONB DEFAULT '{
        "max_concurrent_jobs": 5,
        "ocr_quality": "high",
        "confidence_threshold": 0.85,
        "auto_approval_threshold": 0.95,
        "rate_limits": {
            "web_scraping": 10,
            "ocr_processing": 5
        }
    }'
);

-- Function to create tenant-specific schema
CREATE OR REPLACE FUNCTION create_tenant_schema(tenant_id TEXT)
RETURNS void AS $$
BEGIN
    -- Create schema for tenant
    EXECUTE format('CREATE SCHEMA IF NOT EXISTS tenant_%s', tenant_id);
    
    -- Set search path to tenant schema
    EXECUTE format('SET search_path TO tenant_%s, public', tenant_id);
    
    -- Create tenant-specific tables
    PERFORM create_tenant_tables(tenant_id);
    
    -- Set up RLS policies
    PERFORM setup_tenant_security(tenant_id);
    
END;
$$ LANGUAGE plpgsql;

-- Function to create all tenant tables
CREATE OR REPLACE FUNCTION create_tenant_tables(tenant_id TEXT)
RETURNS void AS $$
DECLARE
    schema_name TEXT := 'tenant_' || tenant_id;
BEGIN
    
    -- Products table with vector embeddings
    EXECUTE format('
    CREATE TABLE IF NOT EXISTS %I.products (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id TEXT NOT NULL DEFAULT %L,
        
        -- Identification
        sku TEXT,
        internal_code TEXT,
        barcode TEXT,
        source_id TEXT, -- ID from original source
        
        -- Basic info
        name TEXT NOT NULL,
        normalized_name TEXT, -- For fuzzy search
        description TEXT,
        category TEXT,
        subcategory TEXT,
        brand TEXT,
        
        -- Vector embeddings for semantic search
        name_embedding VECTOR(1536),
        description_embedding VECTOR(1536),
        
        -- Pricing
        price DECIMAL(12,4),
        cost DECIMAL(12,4),
        currency TEXT DEFAULT ''MXN'',
        price_history JSONB DEFAULT ''[]'',
        
        -- Stock & availability
        stock INTEGER DEFAULT 0,
        reserved_stock INTEGER DEFAULT 0,
        is_available BOOLEAN DEFAULT true,
        
        -- Source metadata
        source_references JSONB DEFAULT ''[]'', -- Array of {source, url, extracted_at}
        extraction_confidence FLOAT CHECK (extraction_confidence >= 0 AND extraction_confidence <= 1),
        last_validated_at TIMESTAMPTZ,
        
        -- Quality scores
        data_completeness_score FLOAT DEFAULT 0,
        data_consistency_score FLOAT DEFAULT 0,
        
        -- Timestamps
        created_at TIMESTAMPTZ DEFAULT NOW(),
        updated_at TIMESTAMPTZ DEFAULT NOW(),
        
        UNIQUE(tenant_id, sku)
    )', schema_name, tenant_id);
    
    -- Product sources tracking
    EXECUTE format('
    CREATE TABLE IF NOT EXISTS %I.product_sources (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id TEXT NOT NULL DEFAULT %L,
        
        source_type TEXT NOT NULL, -- ''web'', ''pdf'', ''api'', ''excel''
        source_url TEXT,
        source_name TEXT,
        
        -- Extraction metadata
        last_extracted_at TIMESTAMPTZ,
        total_products_found INTEGER DEFAULT 0,
        extraction_success_rate FLOAT DEFAULT 0,
        
        -- Configuration
        extraction_config JSONB DEFAULT ''{}''
    )', schema_name, tenant_id);
    
    -- Pattern learning database
    EXECUTE format('
    CREATE TABLE IF NOT EXISTS %I.extraction_patterns (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id TEXT NOT NULL DEFAULT %L,
        
        domain TEXT NOT NULL, -- e.g., ''mercadolibre.com.mx''
        pattern_type TEXT NOT NULL, -- ''product_listing'', ''price'', ''pagination''
        selector TEXT NOT NULL, -- CSS selector or XPath
        
        -- Performance metrics
        confidence FLOAT NOT NULL DEFAULT 1.0,
        success_rate FLOAT DEFAULT 1.0,
        times_used INTEGER DEFAULT 0,
        last_used_at TIMESTAMPTZ DEFAULT NOW(),
        
        -- Learning metadata
        created_at TIMESTAMPTZ DEFAULT NOW(),
        created_by TEXT DEFAULT ''system'',
        
        UNIQUE(tenant_id, domain, pattern_type)
    )', schema_name, tenant_id);
    
    -- Extraction jobs tracking
    EXECUTE format('
    CREATE TABLE IF NOT EXISTS %I.extraction_jobs (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id TEXT NOT NULL DEFAULT %L,
        
        job_type TEXT NOT NULL, -- ''full_catalog'', ''incremental'', ''single_source''
        status TEXT NOT NULL DEFAULT ''pending'', -- pending, running, completed, failed
        
        -- Source info
        sources JSONB NOT NULL, -- Array of source configurations
        
        -- Progress tracking
        total_sources INTEGER DEFAULT 0,
        completed_sources INTEGER DEFAULT 0,
        total_products_found INTEGER DEFAULT 0,
        total_products_processed INTEGER DEFAULT 0,
        
        -- Results
        products_created INTEGER DEFAULT 0,
        products_updated INTEGER DEFAULT 0,
        products_merged INTEGER DEFAULT 0,
        errors_count INTEGER DEFAULT 0,
        
        -- Timing
        started_at TIMESTAMPTZ,
        completed_at TIMESTAMPTZ,
        estimated_completion TIMESTAMPTZ,
        
        -- Metadata
        created_at TIMESTAMPTZ DEFAULT NOW(),
        created_by TEXT,
        
        -- Job configuration
        config JSONB DEFAULT ''{}''
    )', schema_name, tenant_id);
    
    -- Normalization rules
    EXECUTE format('
    CREATE TABLE IF NOT EXISTS %I.normalization_rules (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id TEXT NOT NULL DEFAULT %L,
        
        rule_name TEXT NOT NULL,
        source_field TEXT NOT NULL,
        target_field TEXT NOT NULL,
        
        -- Transformation logic
        transformation_type TEXT NOT NULL, -- ''direct'', ''regex'', ''llm'', ''lookup''
        transformation_config JSONB DEFAULT ''{}''
        
        -- Performance
        success_rate FLOAT DEFAULT 1.0,
        times_applied INTEGER DEFAULT 0,
        
        created_at TIMESTAMPTZ DEFAULT NOW(),
        created_by TEXT DEFAULT ''system''
    )', schema_name, tenant_id);
    
    -- Consolidation log
    EXECUTE format('
    CREATE TABLE IF NOT EXISTS %I.consolidation_log (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id TEXT NOT NULL DEFAULT %L,
        
        -- Products involved
        master_product_id UUID,
        duplicate_product_ids UUID[],
        
        -- Consolidation details
        merge_strategy TEXT NOT NULL,
        fields_merged TEXT[],
        conflicts_resolved JSONB DEFAULT ''[]'',
        
        -- Confidence
        consolidation_confidence FLOAT,
        human_validated BOOLEAN DEFAULT false,
        
        -- Metadata
        consolidated_at TIMESTAMPTZ DEFAULT NOW(),
        consolidated_by TEXT DEFAULT ''system''
    )', schema_name, tenant_id);
    
    RAISE NOTICE ''Created tables for tenant %'', tenant_id;
    
END;
$$ LANGUAGE plpgsql;

-- Function to set up security policies
CREATE OR REPLACE FUNCTION setup_tenant_security(tenant_id TEXT)
RETURNS void AS $$
DECLARE
    schema_name TEXT := 'tenant_' || tenant_id;
    table_name TEXT;
BEGIN
    
    -- Enable RLS on all tenant tables
    FOR table_name IN 
        SELECT tablename 
        FROM pg_tables 
        WHERE schemaname = schema_name
    LOOP
        EXECUTE format('ALTER TABLE %I.%I ENABLE ROW LEVEL SECURITY', schema_name, table_name);
        
        -- Policy: tenant can only see their own data
        EXECUTE format('
            CREATE POLICY tenant_%s_isolation ON %I.%I
            FOR ALL TO PUBLIC
            USING (tenant_id = current_setting(''app.current_tenant'', true))
        ', tenant_id, schema_name, table_name);
        
    END LOOP;
    
    RAISE NOTICE 'Set up RLS policies for tenant %', tenant_id;
    
END;
$$ LANGUAGE plpgsql;

-- Function to switch tenant context
CREATE OR REPLACE FUNCTION set_tenant_context(tenant_id TEXT)
RETURNS void AS $$
BEGIN
    PERFORM set_config('app.current_tenant', tenant_id, false);
    EXECUTE format('SET search_path TO tenant_%s, public', tenant_id);
END;
$$ LANGUAGE plpgsql;