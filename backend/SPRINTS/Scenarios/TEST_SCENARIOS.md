# 🧪 ESCENARIOS DE PRUEBA - ORKESTA

> **IMPORTANTE**: Estos escenarios deben pasar ANTES de escribir código de producción.

## 🎯 FILOSOFÍA DE TESTING

**Test-First Development**: Definimos el comportamiento esperado antes de implementar.
Cada escenario representa un caso de uso REAL de extracción y procesamiento de catálogos.

## 📊 MATRIZ DE ESCENARIOS

| ID | Escenario | Prioridad | Sprint | Complejidad | Estado |
|----|-----------|-----------|--------|-------------|--------|
| S01 | Extracción de catálogo desde MercadoLibre | 🔴 Alta | 1 | Alta | 🔄 |
| S02 | Procesamiento de PDF con tablas y OCR | 🔴 Alta | 1 | Alta | 🔄 |
| S03 | Web scraping con paginación y JS rendering | 🔴 Alta | 1 | Alta | 🔄 |
| S04 | Normalización multi-fuente (ML + PDF + Web) | 🔴 Alta | 1 | Muy Alta | 🔄 |
| S05 | Detección y aprendizaje de patterns | 🔴 Alta | 2 | Alta | ⏳ |
| S06 | Enriquecimiento con búsqueda de imágenes | 🟡 Media | 2 | Media | ⏳ |
| S07 | Multi-tenant catalog isolation | 🔴 Alta | 1 | Alta | 🔄 |
| S08 | Human-in-the-loop para validación | 🟡 Media | 2 | Media | ⏳ |
| S09 | Procesamiento de catálogo Excel complejo | 🟡 Media | 2 | Media | ⏳ |
| S10 | Carga masiva (10,000+ productos) | 🔴 Alta | 3 | Muy Alta | ⏳ |

## 🔄 ESCENARIOS DETALLADOS

### 🎬 ESCENARIO S01: Extracción de Catálogo desde MercadoLibre

**Tenant**: AVAZ Automotive
**Fuente**: https://listado.mercadolibre.com.mx/_CustId_AVAZ
**Contexto**: 500+ productos con variaciones, múltiples páginas

#### Flujo de Extracción:
```python
async def test_s01_mercadolibre_extraction():
    """
    Extraer catálogo completo de AVAZ desde MercadoLibre
    """
    # Arrange
    config = {
        "tenant_id": "avaz_automotive",
        "source": {
            "type": "mercadolibre",
            "url": "https://listado.mercadolibre.com.mx/_CustId_123456",
            "config": {
                "follow_pagination": True,
                "max_pages": 50,
                "extract_variations": True,
                "extract_images": True,
                "extract_questions": True,
                "monitor_price_changes": True
            }
        }
    }
    
    # Act - Iniciar extracción con LangGraph
    graph = CatalogExtractionGraph()
    extraction_job = await graph.start_extraction(config)
    
    # Stream de eventos para monitorear progreso
    events = []
    async for event in extraction_job.stream():
        events.append(event)
        
        if event.type == "page_processed":
            print(f"📄 Página {event.page_num}: {event.products_found} productos")
        elif event.type == "pattern_learned":
            print(f"🧠 Pattern aprendido: {event.pattern_name}")
    
    # Esperar resultado final
    result = await extraction_job.result()
    
    # Assert - Verificaciones detalladas
    assert result.status == "completed"
    assert result.products_extracted >= 500
    assert result.pages_processed >= 10
    
    # Verificar estructura de productos
    sample_product = result.products[0]
    assert all([
        sample_product.get("sku"),
        sample_product.get("title"),
        sample_product.get("price"),
        sample_product.get("images"),
        sample_product.get("description"),
        sample_product.get("stock_status"),
        sample_product.get("seller_reputation"),
        sample_product.get("shipping_info")
    ])
    
    # Verificar variaciones extraídas
    products_with_variations = [p for p in result.products if p.get("variations")]
    assert len(products_with_variations) > 50  # Al menos 50 productos con variaciones
    
    # Verificar patterns aprendidos para futuras extracciones
    learned_patterns = result.learned_patterns
    assert "product_listing_selector" in learned_patterns
    assert "price_selector" in learned_patterns
    assert "pagination_pattern" in learned_patterns
    
    # Verificar calidad de datos
    assert result.data_quality_score > 0.85  # 85% de calidad mínima
    
    # Guardar en base de datos con pgvector
    saved_count = await save_to_database(result.products, config["tenant_id"])
    assert saved_count == len(result.products)
```

### 🎬 ESCENARIO S02: Procesamiento de PDF con Tablas y OCR

**Tenant**: AVAZ Automotive
**Fuente**: catalogo_avaz_2024.pdf (200 páginas, tablas, imágenes)
**Contexto**: PDF escaneado con tablas de productos y especificaciones

#### Flujo de Procesamiento:
```python
async def test_s02_pdf_processing_with_ocr():
    """
    Procesar PDF complejo con OCR multi-pass
    """
    # Arrange
    pdf_config = {
        "tenant_id": "avaz_automotive",
        "source": {
            "type": "pdf",
            "path": "/catalogs/avaz/catalogo_2024.pdf",
            "config": {
                "ocr_enabled": True,
                "ocr_languages": ["spa", "eng"],
                "extract_tables": True,
                "extract_images": True,
                "multi_column_layout": True,
                "confidence_threshold": 0.8
            }
        }
    }
    
    # Act - Procesamiento multi-pass
    pdf_processor = PDFProcessingAgent()
    
    # Pass 1: Análisis de layout
    layout = await pdf_processor.analyze_layout(pdf_config["source"]["path"])
    assert layout.total_pages == 200
    assert layout.has_tables == True
    assert layout.has_images == True
    assert layout.is_scanned == True  # Requiere OCR
    
    # Pass 2: Extracción por tipo de contenido
    extraction_result = await pdf_processor.extract_content(pdf_config)
    
    # Monitorear progreso página por página
    for page_num in range(1, layout.total_pages + 1):
        page_result = await pdf_processor.process_page(page_num)
        
        if page_result.has_table:
            # Extraer tabla con Camelot/Tabula
            table_data = await pdf_processor.extract_table(page_result)
            assert len(table_data.rows) > 0
            
            # Convertir tabla a productos
            products = await pdf_processor.table_to_products(table_data)
            
        if page_result.has_images:
            # OCR en imágenes de productos
            for image in page_result.images:
                ocr_result = await pdf_processor.ocr_image(image)
                
                if ocr_result.confidence > 0.8:
                    # Extraer información del producto
                    product_info = await pdf_processor.extract_product_from_ocr(ocr_result)
                    assert product_info.get("name")
                    assert product_info.get("code") or product_info.get("sku")
    
    # Pass 3: Consolidación y normalización
    all_products = extraction_result.products
    
    # Assert - Verificaciones
    assert len(all_products) >= 1000  # Mínimo 1000 productos del catálogo
    
    # Verificar calidad de OCR
    ocr_quality_metrics = extraction_result.ocr_metrics
    assert ocr_quality_metrics.average_confidence > 0.85
    assert ocr_quality_metrics.failed_pages < 5  # Menos de 5 páginas fallidas
    
    # Verificar extracción de tablas
    assert extraction_result.tables_extracted >= 50  # Al menos 50 tablas
    
    # Verificar estructura de productos extraídos
    sample_product = all_products[0]
    assert sample_product.get("name") or sample_product.get("description")
    assert sample_product.get("sku") or sample_product.get("code")
    assert sample_product.get("price") or sample_product.get("price_text")
    
    # Validación con LLM
    validation_result = await pdf_processor.validate_with_llm(all_products[:10])
    assert validation_result.valid_products >= 8  # 80% válidos
```

### 🎬 ESCENARIO S03: Web Scraping con Paginación y JS Rendering

**Tenant**: Industrial Tools MX
**Fuente**: https://industrialtools.mx/catalogo
**Contexto**: SPA con React, carga dinámica, infinite scroll

#### Flujo de Scraping:
```python
async def test_s03_dynamic_web_scraping():
    """
    Scraping de sitio con JavaScript y carga dinámica
    """
    # Arrange
    scraping_config = {
        "tenant_id": "industrial_tools",
        "source": {
            "type": "website",
            "url": "https://industrialtools.mx/catalogo",
            "config": {
                "javascript_enabled": True,
                "wait_for_ajax": True,
                "infinite_scroll": True,
                "max_scroll_attempts": 50,
                "wait_between_scrolls": 2000,  # ms
                "detect_lazy_loading": True,
                "extract_ajax_requests": True
            }
        }
    }
    
    # Act - Scraping inteligente
    scraper = IntelligentWebScrapingAgent()
    
    # Detectar tipo de sitio y tecnología
    site_analysis = await scraper.analyze_site(scraping_config["source"]["url"])
    assert site_analysis.framework == "React"
    assert site_analysis.has_infinite_scroll == True
    assert site_analysis.api_endpoints_found > 0
    
    # Estrategia 1: Interceptar llamadas API
    if site_analysis.api_endpoints_found:
        api_products = await scraper.intercept_api_calls(
            scraping_config["source"]["url"]
        )
        assert len(api_products) > 0
    
    # Estrategia 2: Selenium con scroll dinámico
    selenium_scraper = await scraper.create_selenium_session()
    
    products_found = []
    last_height = 0
    scroll_attempts = 0
    
    while scroll_attempts < 50:
        # Scroll hasta el bottom
        await selenium_scraper.scroll_to_bottom()
        await asyncio.sleep(2)  # Esperar carga
        
        # Extraer productos visibles
        new_products = await selenium_scraper.extract_visible_products()
        products_found.extend(new_products)
        
        # Verificar si hay más contenido
        current_height = await selenium_scraper.get_page_height()
        if current_height == last_height:
            break  # No hay más contenido
        
        last_height = current_height
        scroll_attempts += 1
    
    # Estrategia 3: Buscar patterns en el DOM
    dom_patterns = await scraper.detect_dom_patterns(
        await selenium_scraper.get_page_source()
    )
    
    # Aplicar patterns para extracción más eficiente
    pattern_extracted = await scraper.apply_patterns(dom_patterns)
    
    # Consolidar productos de todas las estrategias
    all_products = scraper.deduplicate_products(
        api_products + products_found + pattern_extracted
    )
    
    # Assert - Verificaciones
    assert len(all_products) >= 500
    
    # Verificar que se extrajeron imágenes lazy-loaded
    products_with_images = [p for p in all_products if p.get("image_url")]
    assert len(products_with_images) / len(all_products) > 0.9  # 90% con imágenes
    
    # Verificar extracción de precios dinámicos
    products_with_prices = [p for p in all_products if p.get("price")]
    assert len(products_with_prices) / len(all_products) > 0.95
    
    # Guardar patterns aprendidos para futuras extracciones
    await scraper.save_learned_patterns(
        scraping_config["source"]["url"],
        dom_patterns
    )
```

### 🎬 ESCENARIO S04: Normalización Multi-Fuente (ML + PDF + Web)

**Tenant**: AVAZ Automotive
**Fuentes**: MercadoLibre + PDF + Sitio Web
**Contexto**: Mismo catálogo en 3 fuentes diferentes, consolidar sin duplicados

#### Flujo de Normalización:
```python
async def test_s04_multi_source_normalization():
    """
    Consolidar catálogo desde múltiples fuentes
    """
    # Arrange - 3 fuentes diferentes
    sources = [
        {
            "type": "mercadolibre",
            "url": "https://listado.mercadolibre.com.mx/_CustId_AVAZ",
            "products_expected": 500
        },
        {
            "type": "pdf",
            "path": "/catalogs/avaz/catalogo_2024.pdf",
            "products_expected": 1000
        },
        {
            "type": "website",
            "url": "https://avaz.com.mx/productos",
            "products_expected": 800
        }
    ]
    
    # Act - Extraer de cada fuente en paralelo
    extraction_tasks = []
    for source in sources:
        if source["type"] == "mercadolibre":
            task = extract_from_mercadolibre(source)
        elif source["type"] == "pdf":
            task = extract_from_pdf(source)
        elif source["type"] == "website":
            task = extract_from_website(source)
        extraction_tasks.append(task)
    
    # Ejecutar extracciones en paralelo
    extraction_results = await asyncio.gather(*extraction_tasks)
    
    # Verificar extracciones individuales
    ml_products = extraction_results[0]
    pdf_products = extraction_results[1]
    web_products = extraction_results[2]
    
    assert len(ml_products) >= 500
    assert len(pdf_products) >= 1000
    assert len(web_products) >= 800
    
    # Normalización inteligente
    normalizer = NormalizationPipeline()
    
    # Detectar schema de cada fuente
    ml_schema = await normalizer.detect_schema(ml_products[:10])
    pdf_schema = await normalizer.detect_schema(pdf_products[:10])
    web_schema = await normalizer.detect_schema(web_products[:10])
    
    # Crear mapping rules con LLM
    target_schema = ProductSchema()  # Schema objetivo unificado
    
    ml_mapping = await normalizer.create_mapping(ml_schema, target_schema)
    pdf_mapping = await normalizer.create_mapping(pdf_schema, target_schema)
    web_mapping = await normalizer.create_mapping(web_schema, target_schema)
    
    # Aplicar normalizaciones
    ml_normalized = await normalizer.normalize_batch(ml_products, ml_mapping)
    pdf_normalized = await normalizer.normalize_batch(pdf_products, pdf_mapping)
    web_normalized = await normalizer.normalize_batch(web_products, web_mapping)
    
    # Consolidación y deduplicación
    consolidator = ProductConsolidator()
    
    # Configurar estrategia de deduplicación
    dedup_config = {
        "match_fields": ["sku", "name", "barcode"],
        "fuzzy_match_threshold": 0.85,
        "prefer_source_priority": ["pdf", "website", "mercadolibre"],
        "merge_strategy": "combine_best_fields"
    }
    
    # Consolidar productos
    all_products = ml_normalized + pdf_normalized + web_normalized
    consolidated = await consolidator.consolidate(all_products, dedup_config)
    
    # Assert - Verificaciones de consolidación
    
    # No debe haber más productos que el máximo esperado (con margen)
    assert len(consolidated) <= 1200  # ~1000 únicos esperados
    assert len(consolidated) >= 900   # Al menos 900 únicos
    
    # Verificar que se detectaron duplicados
    assert consolidator.duplicates_found >= 300  # Overlap esperado
    
    # Verificar enriquecimiento (campos combinados)
    enriched_products = [
        p for p in consolidated 
        if len(p.get("merged_from", [])) > 1
    ]
    assert len(enriched_products) >= 200  # Al menos 200 productos enriquecidos
    
    # Verificar calidad de normalización
    quality_check = await normalizer.validate_quality(consolidated)
    assert quality_check.completeness_score > 0.9  # 90% campos completos
    assert quality_check.consistency_score > 0.95  # 95% formato consistente
    
    # Verificar que cada producto tiene los campos requeridos
    for product in consolidated[:100]:  # Muestra de 100
        assert product.get("sku") or product.get("internal_code")
        assert product.get("name")
        assert product.get("normalized_name")  # Nombre normalizado
        assert product.get("category")  # Categorizado
        assert product.get("price") or product.get("price_range")
        assert product.get("source_references")  # De dónde viene
        
    # Guardar en base de datos con embeddings
    embedder = ProductEmbedder()
    for product in consolidated:
        # Generar embedding para búsqueda semántica
        product["embedding"] = await embedder.generate_embedding(product)
    
    saved = await save_to_postgres_with_vector(consolidated, "avaz_automotive")
    assert saved == len(consolidated)
```

### 🎬 ESCENARIO S05: Detección y Aprendizaje de Patterns

**Contexto**: Sistema aprende patterns de extracción automáticamente

#### Flujo de Pattern Learning:
```python
async def test_s05_pattern_learning():
    """
    El sistema aprende patterns de sitios nuevos
    """
    # Arrange - Sitio nunca antes visto
    new_site = {
        "url": "https://nuevo-proveedor.mx/productos",
        "tenant_id": "test_tenant"
    }
    
    # Act - Primera extracción (sin patterns)
    scraper = IntelligentWebScrapingAgent()
    
    # El agente debe detectar patterns automáticamente
    first_extraction = await scraper.extract_with_learning(new_site["url"])
    
    # Verificar que detectó patterns
    detected_patterns = first_extraction.patterns_detected
    assert "product_container" in detected_patterns
    assert "price_selector" in detected_patterns
    assert "name_selector" in detected_patterns
    assert "image_selector" in detected_patterns
    
    # Guardar patterns
    await scraper.save_patterns(new_site["url"], detected_patterns)
    
    # Segunda extracción (con patterns aprendidos)
    second_extraction = await scraper.extract_with_learning(new_site["url"])
    
    # Assert - Segunda extracción debe ser más rápida y precisa
    assert second_extraction.extraction_time < first_extraction.extraction_time * 0.5
    assert second_extraction.confidence_score > first_extraction.confidence_score
    assert second_extraction.used_learned_patterns == True
    
    # Verificar que los patterns mejoran con el tiempo
    pattern_performance = await scraper.get_pattern_metrics(new_site["url"])
    assert pattern_performance.success_rate > 0.95
    assert pattern_performance.times_used >= 2
```

### 🎬 ESCENARIO S07: Multi-Tenant Catalog Isolation

**Contexto**: Verificar aislamiento completo entre tenants

#### Test de Aislamiento:
```python
async def test_s07_multi_tenant_isolation():
    """
    Datos de catálogos NUNCA se cruzan entre tenants
    """
    # Arrange - 2 empresas competidoras
    tenant_a = {
        "id": "company_a",
        "name": "Ferretería A"
    }
    
    tenant_b = {
        "id": "company_b", 
        "name": "Ferretería B"
    }
    
    # Ambos tienen productos con mismo SKU pero diferentes precios
    product_a = {
        "tenant_id": "company_a",
        "sku": "TUBE-001",
        "name": "Tubo PVC Premium A",
        "price": 100,
        "cost": 50,  # Información sensible
        "supplier": "Proveedor Secreto A"
    }
    
    product_b = {
        "tenant_id": "company_b",
        "sku": "TUBE-001",  # Mismo SKU!
        "name": "Tubo PVC Básico B",
        "price": 80,
        "cost": 40,  # Información sensible
        "supplier": "Proveedor Secreto B"
    }
    
    # Act - Guardar productos
    await save_product(product_a)
    await save_product(product_b)
    
    # Crear contextos de ejecución
    context_a = create_tenant_context("company_a")
    context_b = create_tenant_context("company_b")
    
    # Búsquedas desde cada contexto
    result_a = await context_a.search_product("TUBE-001")
    result_b = await context_b.search_product("TUBE-001")
    
    # Assert - Aislamiento completo
    assert result_a.name == "Tubo PVC Premium A"
    assert result_a.price == 100
    assert result_a.supplier == "Proveedor Secreto A"
    
    assert result_b.name == "Tubo PVC Básico B"
    assert result_b.price == 80
    assert result_b.supplier == "Proveedor Secreto B"
    
    # Intentar acceso cruzado (DEBE FALLAR)
    with pytest.raises(SecurityException) as exc:
        await context_a.get_product(product_b["id"])
    assert "Access denied" in str(exc.value)
    
    # Verificar vector search con aislamiento
    embedding_a = await generate_embedding("tubo pvc")
    
    # Búsqueda vectorial desde contexto A
    vector_results_a = await context_a.vector_search(embedding_a)
    for result in vector_results_a:
        assert result.tenant_id == "company_a"  # Solo productos de A
    
    # Búsqueda vectorial desde contexto B
    vector_results_b = await context_b.vector_search(embedding_a)
    for result in vector_results_b:
        assert result.tenant_id == "company_b"  # Solo productos de B
    
    # Verificar que los agentes respetan el aislamiento
    agent = CatalogAgent()
    
    # Agente en contexto A
    agent.set_context(context_a)
    agent_response_a = await agent.search("TUBE-001")
    assert "Premium A" in agent_response_a
    assert "Secreto B" not in agent_response_a  # No debe ver datos de B
    
    # Verificar logs de auditoría
    audit_logs = await get_audit_logs()
    cross_tenant_attempts = [
        log for log in audit_logs 
        if log.type == "CROSS_TENANT_ACCESS_ATTEMPT"
    ]
    assert len(cross_tenant_attempts) == 1  # El intento fallido de arriba
```

### 🎬 ESCENARIO S08: Human-in-the-Loop para Validación

**Contexto**: Validación humana cuando la confianza es baja

#### Flujo con Intervención Humana:
```python
async def test_s08_human_in_the_loop():
    """
    Sistema pausa para revisión humana cuando es necesario
    """
    # Arrange - Extracción con baja confianza
    ambiguous_source = {
        "type": "pdf",
        "path": "/catalogs/damaged_scan.pdf",  # PDF de mala calidad
        "tenant_id": "test_tenant"
    }
    
    # Act - Iniciar extracción
    graph = CatalogExtractionGraph()
    config = {"configurable": {"thread_id": "test_123"}}
    
    # Primera ejecución - debe detenerse para revisión
    result = await graph.ainvoke(ambiguous_source, config)
    
    # Assert - Sistema solicitó revisión
    assert result["requires_human_approval"] == True
    assert result["confidence_score"] < 0.7
    assert len(result["items_for_review"]) > 0
    
    # Simular revisión humana
    human_feedback = {
        "approved_items": [
            {
                "id": "item_1",
                "corrections": {
                    "name": "Tubo Corregido",
                    "price": 45.50
                }
            }
        ],
        "rejected_items": ["item_2", "item_3"],
        "additional_notes": "El OCR falló en páginas 3-5"
    }
    
    # Continuar con feedback
    final_result = await graph.ainvoke(
        Command(resume=human_feedback),
        config
    )
    
    # Assert - Procesó feedback correctamente
    assert final_result["status"] == "completed_with_review"
    assert len(final_result["products"]) > 0
    assert final_result["human_corrections_applied"] == True
    
    # Verificar que aprendió del feedback
    learning_metrics = final_result["learning_metrics"]
    assert learning_metrics["patterns_updated"] > 0
    assert learning_metrics["confidence_threshold_adjusted"] == True
```

### 🎬 ESCENARIO S10: Carga Masiva (10,000+ productos)

**Contexto**: Performance con catálogos enormes

#### Test de Carga:
```python
async def test_s10_massive_catalog_load():
    """
    Procesar catálogo con 10,000+ productos eficientemente
    """
    # Arrange - Fuente masiva
    massive_source = {
        "type": "api",
        "endpoint": "https://api.megasupplier.com/products",
        "total_products": 15000,
        "tenant_id": "mega_client"
    }
    
    # Act - Procesamiento con streaming y batching
    processor = MassiveCatalogProcessor()
    
    start_time = time.time()
    
    # Configurar procesamiento por batches
    batch_config = {
        "batch_size": 100,
        "parallel_batches": 5,
        "checkpoint_every": 500,
        "memory_limit_mb": 512
    }
    
    processed_count = 0
    errors = []
    
    async for batch_result in processor.process_stream(massive_source, batch_config):
        processed_count += batch_result.products_processed
        errors.extend(batch_result.errors)
        
        # Verificar memory usage
        memory_usage = get_memory_usage()
        assert memory_usage < 512  # MB
        
        # Verificar checkpointing
        if processed_count % 500 == 0:
            checkpoint = await processor.get_checkpoint()
            assert checkpoint.products_saved == processed_count
    
    end_time = time.time()
    duration = end_time - start_time
    
    # Assert - Performance metrics
    assert processed_count >= 14500  # 95%+ success rate
    assert len(errors) < 500  # Menos de 500 errores
    assert duration < 300  # Menos de 5 minutos
    
    # Verificar throughput
    throughput = processed_count / duration
    assert throughput > 50  # Más de 50 productos/segundo
    
    # Verificar que se guardaron en DB con índices
    db_count = await count_products("mega_client")
    assert db_count >= 14500
    
    # Verificar que la búsqueda sigue siendo rápida
    search_time = await measure_search_time("mega_client", "random_query")
    assert search_time < 100  # ms
```

## 🎭 ESCENARIOS DE ERROR

### E01: Sitio Web Cambia Estructura
```python
async def test_e01_website_structure_change():
    """
    El scraper se adapta cuando un sitio cambia su estructura
    """
    # Simular que MercadoLibre cambió su HTML
    old_pattern = {"product_selector": ".ui-search-result"}
    new_pattern = {"product_selector": ".new-product-card"}
    
    scraper = AdaptiveWebScraper()
    
    # Primera extracción falla con pattern viejo
    with pytest.raises(ExtractionFailedException):
        await scraper.extract_with_pattern(url, old_pattern)
    
    # Sistema detecta el fallo y re-analiza
    new_detected_pattern = await scraper.auto_detect_pattern(url)
    assert new_detected_pattern["product_selector"] == ".new-product-card"
    
    # Actualiza pattern y reintenta
    result = await scraper.extract_with_pattern(url, new_detected_pattern)
    assert len(result.products) > 0
```

### E02: PDF Corrupto o Ilegible
```python
async def test_e02_corrupted_pdf():
    """
    Manejo de PDFs dañados con fallback strategies
    """
    corrupted_pdf = "/catalogs/damaged.pdf"
    
    processor = PDFProcessor()
    
    # Intenta procesar con múltiples estrategias
    strategies = [
        "pypdf2",
        "pdfplumber", 
        "ocr_full_page",
        "image_extraction"
    ]
    
    result = await processor.process_with_fallback(corrupted_pdf, strategies)
    
    # Aunque esté dañado, algo debe extraer
    assert result.partial_success == True
    assert len(result.products) > 0
    assert result.quality_warning == True
```

## 📈 MÉTRICAS DE PERFORMANCE

### P01: Extracción Concurrente Multi-Fuente
```python
@pytest.mark.performance
async def test_p01_concurrent_extraction():
    """
    Extraer de 10 fuentes diferentes simultáneamente
    """
    sources = [
        {"type": "mercadolibre", "url": "..."},
        {"type": "pdf", "path": "..."},
        {"type": "website", "url": "..."},
        # ... 7 más
    ]
    
    start = time.time()
    
    # Extracción paralela
    results = await asyncio.gather(*[
        extract_catalog(source) for source in sources
    ])
    
    duration = time.time() - start
    
    # Verificar paralelismo efectivo
    assert duration < 60  # No más de 1 minuto para 10 fuentes
    assert all(r.status == "completed" for r in results)
    
    # Métricas de throughput
    total_products = sum(len(r.products) for r in results)
    throughput = total_products / duration
    assert throughput > 100  # 100+ productos/segundo total
```

## ✅ CHECKLIST DE VALIDACIÓN

Antes de pasar a producción, TODOS estos escenarios deben:

- [ ] Ejecutarse automáticamente en CI/CD
- [ ] Extraer catálogos reales de prueba
- [ ] Validar normalización multi-fuente
- [ ] Probar con PDFs escaneados reales
- [ ] Verificar aislamiento multi-tenant
- [ ] Manejar sitios con JavaScript
- [ ] Procesar al menos 10,000 productos
- [ ] Mantener performance < 100ms por producto
- [ ] Generar embeddings para búsqueda vectorial
- [ ] Validar calidad de datos > 90%

## 📊 MÉTRICAS DE CALIDAD

| Métrica | Target | Actual | Status |
|---------|--------|--------|--------|
| Productos extraídos/hora | > 10,000 | - | ⏳ |
| Accuracy de extracción | > 95% | - | ⏳ |
| OCR confidence promedio | > 85% | - | ⏳ |
| Deduplicación correcta | > 98% | - | ⏳ |
| Latencia búsqueda vectorial | < 50ms | - | ⏳ |
| Memory usage por 1000 productos | < 100MB | - | ⏳ |
| Patterns aprendidos | > 20 | - | ⏳ |
| Human intervention rate | < 5% | - | ⏳ |