-- Seed data for testing with realistic tenant scenarios

-- Insert demo tenants
INSERT INTO tenants (id, name, settings, extraction_config, is_active) 
VALUES 
(
    'avaz_automotive',
    'Equipo Automotriz AVAZ',
    '{
        "industry": "automotive",
        "location": "Mexico",
        "catalog_sources": ["mercadolibre", "pdf", "website"]
    }',
    '{
        "max_concurrent_jobs": 10,
        "ocr_quality": "high", 
        "confidence_threshold": 0.90,
        "auto_approval_threshold": 0.95,
        "rate_limits": {
            "web_scraping": 15,
            "ocr_processing": 8
        },
        "preferred_sources": ["pdf", "website", "mercadolibre"]
    }',
    true
),
(
    'ferreteria_central',
    'Ferretería Central',
    '{
        "industry": "hardware_store",
        "location": "Mexico",
        "catalog_sources": ["pdf", "excel", "manual"]
    }',
    '{
        "max_concurrent_jobs": 5,
        "ocr_quality": "medium",
        "confidence_threshold": 0.85,
        "auto_approval_threshold": 0.90,
        "rate_limits": {
            "web_scraping": 10,
            "ocr_processing": 5
        }
    }',
    true
),
(
    'industrial_tools',
    'Industrial Tools MX',
    '{
        "industry": "industrial_tools",
        "location": "Mexico", 
        "catalog_sources": ["website", "api", "pdf"]
    }',
    '{
        "max_concurrent_jobs": 8,
        "ocr_quality": "high",
        "confidence_threshold": 0.88,
        "auto_approval_threshold": 0.93,
        "rate_limits": {
            "web_scraping": 20,
            "ocr_processing": 10
        }
    }',
    true
) 
ON CONFLICT (id) DO UPDATE SET 
    name = EXCLUDED.name,
    settings = EXCLUDED.settings,
    extraction_config = EXCLUDED.extraction_config,
    updated_at = NOW();

-- Create schemas and tables for each tenant
SELECT create_tenant_schema('avaz_automotive');
SELECT create_tenant_schema('ferreteria_central'); 
SELECT create_tenant_schema('industrial_tools');

-- Create indexes for each tenant
SELECT create_tenant_indexes('avaz_automotive');
SELECT create_tenant_indexes('ferreteria_central');
SELECT create_tenant_indexes('industrial_tools');

-- Seed extraction patterns for common domains
INSERT INTO tenant_avaz_automotive.extraction_patterns (domain, pattern_type, selector, confidence, success_rate, times_used)
VALUES 
-- MercadoLibre patterns
('mercadolibre.com.mx', 'product_listing', '.ui-search-result__content', 0.95, 0.98, 150),
('mercadolibre.com.mx', 'product_title', '.ui-search-item__title', 0.98, 0.99, 150),
('mercadolibre.com.mx', 'product_price', '.andes-money-amount__fraction', 0.97, 0.96, 150),
('mercadolibre.com.mx', 'product_image', '.ui-search-result__image img', 0.95, 0.98, 150),
('mercadolibre.com.mx', 'next_page', '.andes-pagination__button--next', 0.99, 0.99, 45),

-- Generic e-commerce patterns
('*', 'product_container', '.product, .item, [class*="product"]', 0.85, 0.80, 25),
('*', 'price_pattern', '[class*="price"], .precio, .cost', 0.90, 0.85, 30),
('*', 'image_pattern', '.product img, [class*="product"] img', 0.95, 0.92, 28)
ON CONFLICT (tenant_id, domain, pattern_type) DO NOTHING;

-- Seed some product sources for AVAZ
INSERT INTO tenant_avaz_automotive.product_sources (source_type, source_url, source_name, extraction_config)
VALUES 
('mercadolibre', 'https://listado.mercadolibre.com.mx/_CustId_123456789', 'AVAZ MercadoLibre Store', 
 '{"max_pages": 50, "extract_variations": true, "monitor_prices": true}'),
('website', 'https://avaz.com.mx/productos', 'AVAZ Official Website',
 '{"javascript_enabled": true, "wait_for_ajax": true}'),
('pdf', '/catalogs/avaz/catalogo_2024.pdf', 'AVAZ Master Catalog 2024',
 '{"ocr_enabled": true, "extract_tables": true, "multi_column": true}')
ON CONFLICT DO NOTHING;

-- Create a sample extraction job
INSERT INTO tenant_avaz_automotive.extraction_jobs (
    job_type, 
    status, 
    sources, 
    total_sources,
    config,
    created_by
)
VALUES (
    'full_catalog',
    'completed',
    '[
        {
            "type": "mercadolibre",
            "url": "https://listado.mercadolibre.com.mx/_CustId_123456789",
            "config": {"max_pages": 20}
        },
        {
            "type": "pdf", 
            "path": "/catalogs/avaz/catalogo_2024.pdf",
            "config": {"ocr_enabled": true}
        }
    ]'::jsonb,
    2,
    '{
        "merge_duplicates": true,
        "auto_categorize": true,
        "generate_embeddings": true
    }'::jsonb,
    'system'
);

-- Sample normalization rules for AVAZ
INSERT INTO tenant_avaz_automotive.normalization_rules (
    rule_name,
    source_field,
    target_field, 
    transformation_type,
    transformation_config
)
VALUES 
('normalize_automotive_parts', 'raw_name', 'normalized_name',
 'llm', '{"prompt": "Normalize this automotive part name", "model": "groq"}'),
('extract_part_number', 'description', 'sku',
 'regex', '{"pattern": "(?:Part|Parte|#)\\s*:?\\s*([A-Z0-9-]+)", "group": 1}'),
('categorize_by_keywords', 'name', 'category', 
 'lookup', '{
    "mappings": {
        "motor": "Motor",
        "freno": "Frenos",
        "suspension": "Suspensión",
        "transmision": "Transmisión",
        "electrico": "Eléctrico"
    }
 }')
ON CONFLICT DO NOTHING;

-- Create sample realistic products for AVAZ (automotive parts)
INSERT INTO tenant_avaz_automotive.products (
    sku, name, normalized_name, description, category, subcategory, brand,
    price, currency, stock, is_available,
    source_references, extraction_confidence, data_completeness_score
)
VALUES 
('BRK001', 'Balatas Delanteras Honda Civic 2019-2024', 'balatas delanteras honda civic',
 'Balatas de freno delanteras originales para Honda Civic 2019-2024. Incluye hardware de instalación.',
 'Frenos', 'Balatas', 'Honda',
 850.00, 'MXN', 25, true,
 '[{"source": "mercadolibre", "url": "https://articulo.mercadolibre.com.mx/MLM-123456", "extracted_at": "2024-08-24T10:00:00Z"}]'::jsonb,
 0.95, 0.98),

('MTR002', 'Filtro de Aceite Nissan Versa 2018-2023', 'filtro aceite nissan versa',
 'Filtro de aceite original Nissan para Versa 2018-2023. Compatible con motor HR16DE.',
 'Motor', 'Filtros', 'Nissan', 
 180.00, 'MXN', 50, true,
 '[{"source": "pdf", "page": 45, "extracted_at": "2024-08-24T09:30:00Z"}]'::jsonb,
 0.92, 0.90),

('SUS003', 'Amortiguador Trasero Toyota Corolla 2020-2024', 'amortiguador trasero toyota corolla',
 'Amortiguador trasero izquierdo/derecho Toyota Corolla 2020-2024. Incluye soporte superior.',
 'Suspensión', 'Amortiguadores', 'Toyota',
 1250.00, 'MXN', 8, true,
 '[{"source": "website", "url": "https://avaz.com.mx/productos/amortiguador-123", "extracted_at": "2024-08-24T11:15:00Z"}]'::jsonb,
 0.88, 0.85),

('ELE004', 'Bujías NGK Platino Ford Focus 2015-2020', 'bujias ngk platino ford focus',  
 'Set de 4 bujías NGK platino para Ford Focus 2015-2020. Motor 2.0L Duratec.',
 'Eléctrico', 'Bujías', 'NGK',
 320.00, 'MXN', 35, true,
 '[{"source": "mercadolibre", "url": "https://articulo.mercadolibre.com.mx/MLM-789012", "extracted_at": "2024-08-24T12:00:00Z"}]'::jsonb,
 0.97, 0.95),

('TRA005', 'Aceite de Transmisión ATF Chevrolet 4L', 'aceite transmision atf chevrolet',
 'Aceite para transmisión automática ATF Dexron VI. Compatible con Chevrolet, GMC, Cadillac.',
 'Transmisión', 'Lubricantes', 'Chevrolet',
 450.00, 'MXN', 20, true,
 '[{"source": "pdf", "page": 78, "extracted_at": "2024-08-24T08:45:00Z"}]'::jsonb,
 0.90, 0.88)
ON CONFLICT (tenant_id, sku) DO NOTHING;

-- Seed similar data for other tenants with their respective products
INSERT INTO tenant_ferreteria_central.products (
    sku, name, normalized_name, description, category, brand,
    price, currency, stock, is_available, extraction_confidence
)
VALUES 
('TUB001', 'Tubo PVC 1/2 pulgada x 6 metros', 'tubo pvc media pulgada',
 'Tubo de PVC cédula 40 de 1/2 pulgada por 6 metros de longitud.',
 'Tubería', 'Pavco',
 45.50, 'MXN', 150, true, 0.95),

('TOR001', 'Tornillo Cabeza Hexagonal 1/4 x 1"', 'tornillo hexagonal cuarto pulgada',
 'Tornillo de acero inoxidable cabeza hexagonal 1/4" x 1" con tuerca.',
 'Tornillería', 'Generic',
 2.50, 'MXN', 500, true, 0.88),

('CEM001', 'Cemento Portland Gris 50kg', 'cemento portland gris',
 'Cemento Portland gris uso general, saco de 50 kilogramos.',
 'Construcción', 'Cemex', 
 195.00, 'MXN', 80, true, 0.92)
ON CONFLICT (tenant_id, sku) DO NOTHING;

-- Log a consolidation example for AVAZ
INSERT INTO tenant_avaz_automotive.consolidation_log (
    master_product_id,
    duplicate_product_ids,
    merge_strategy,
    fields_merged,
    conflicts_resolved,
    consolidation_confidence,
    consolidated_by
)
SELECT 
    p1.id,
    ARRAY[p2.id, p3.id],
    'prefer_pdf_then_website',
    ARRAY['description', 'price', 'stock'],
    '[{"field": "price", "values": [850, 820, 900], "chosen": 850, "reason": "pdf_source_preferred"}]'::jsonb,
    0.92,
    'system'
FROM tenant_avaz_automotive.products p1
CROSS JOIN (SELECT id FROM tenant_avaz_automotive.products LIMIT 1 OFFSET 1) p2
CROSS JOIN (SELECT id FROM tenant_avaz_automotive.products LIMIT 1 OFFSET 2) p3
WHERE p1.sku = 'BRK001'
LIMIT 1;

-- Update job completion
UPDATE tenant_avaz_automotive.extraction_jobs 
SET 
    completed_sources = 2,
    total_products_found = 1250,
    total_products_processed = 1240,
    products_created = 1180,
    products_updated = 60,
    products_merged = 15,
    errors_count = 10,
    started_at = NOW() - INTERVAL '2 hours',
    completed_at = NOW() - INTERVAL '30 minutes'
WHERE job_type = 'full_catalog';

-- Note: Embeddings will be generated by the application when products are inserted
-- The seed data provides a realistic foundation for testing the extraction system