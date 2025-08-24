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

#### 🚀 Comandos Ejecutables:
```bash
# 1. Setup del test environment
export GROQ_API_KEY="your_groq_key"
export POSTGRES_URL="postgresql://user:pass@localhost:5432/orkesta_test"
export TENANT_ID="avaz_automotive"

# 2. Ejecutar test específico S01
pytest tests/scenarios/test_s01_mercadolibre.py::test_s01_mercadolibre_extraction -v

# 3. Ejecutar con cobertura de código
pytest tests/scenarios/test_s01_mercadolibre.py --cov=src/agents --cov-report=html

# 4. Ejecutar en modo performance
pytest tests/scenarios/test_s01_mercadolibre.py -m performance --durations=10

# 5. Ejecutar solo en CI/CD
pytest tests/scenarios/test_s01_mercadolibre.py -m "not integration" --tb=short
```

#### 🎯 LOGRABLES ESPECÍFICOS:
- ✅ Extraer 500+ productos con 95% accuracy
- ✅ Procesar 10+ páginas en <5 minutos  
- ✅ Aprender 3+ patterns CSS automáticamente
- ✅ Zero cross-tenant contamination
- ✅ <1GB memoria máxima durante extracción

#### 🏷️ TAGS: `#mercadolibre #web-scraping #catalog-extraction #avaz`

#### Implementación Completa:
```python
# File: tests/scenarios/test_s01_mercadolibre.py
import pytest
import asyncio
import time
import psutil
from unittest.mock import AsyncMock, patch, MagicMock
from src.agents.web_scraping_agent import MercadoLibreAgent
from src.core.orchestrator import CatalogOrchestrator
from src.models.product import Product, ProductSchema
from src.storage.postgres import PostgresStore
from src.utils.metrics import PerformanceTracker

@pytest.mark.asyncio
@pytest.mark.timeout(600)  # 10 minutos máximo
async def test_s01_mercadolibre_extraction():
    """
    LOGRABLE: Extraer 500+ productos de MercadoLibre AVAZ con 95% accuracy
    TAGS: #mercadolibre #web-scraping #catalog-extraction #avaz
    TIMEOUT: 10 minutos
    MEMORY_LIMIT: 1GB
    """
    # Arrange - Configuración específica para AVAZ
    performance_tracker = PerformanceTracker()
    performance_tracker.start()
    
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
                "monitor_price_changes": True,
                "rate_limit": {"requests_per_minute": 60},
                "retry_strategy": {"max_retries": 3, "backoff": "exponential"},
                "user_agent_rotation": True,
                "proxy_rotation": False  # Solo para producción
            }
        },
        "validation": {
            "required_fields": ["sku", "title", "price", "availability", "images"],
            "price_range": {"min": 10, "max": 50000},
            "confidence_threshold": 0.85,
            "duplicate_detection": True
        },
        "storage": {
            "batch_size": 100,
            "upsert_strategy": "merge_on_sku",
            "backup_raw_data": True
            }
        }
        }
    }
    
    # Mock selenium driver para tests controlados
    with patch('src.utils.selenium_driver.SeleniumDriver') as mock_driver:
        mock_driver.return_value.get_page.return_value = SAMPLE_ML_HTML_AVAZ
        mock_driver.return_value.screenshot.return_value = b"fake_screenshot"
        
        # Act - Iniciar extracción con LangGraph
        orchestrator = CatalogOrchestrator()
        extraction_job = await orchestrator.start_catalog_extraction(config)
        
        # Monitorear progreso en tiempo real
        progress_events = []
        timeout_counter = 0
    
        # Stream de eventos para monitorear progreso
        async for event in extraction_job.stream():
            progress_events.append(event)
            
            if event.type == "page_processed":
                print(f"📄 Página {event.page_num}: {event.products_found} productos")
                assert event.products_found > 0, f"Página {event.page_num} sin productos"
                
            elif event.type == "pattern_learned":
                print(f"🧠 Pattern aprendido: {event.pattern_name}")
                
            elif event.type == "error":
                print(f"❌ Error: {event.error_message}")
                
            elif event.type == "memory_warning":
                memory_usage = psutil.Process().memory_info().rss / 1024 / 1024  # MB
                assert memory_usage < 1024, f"Uso de memoria excesivo: {memory_usage}MB"
            
            # Timeout protection
            timeout_counter += 1
            if timeout_counter > 1000:
                pytest.fail("Timeout: demasiados eventos sin completar")
        
        # Esperar resultado final
        result = await extraction_job.result()
        performance_tracker.stop()
    
    # Assert - Verificaciones ESPECÍFICAS para AVAZ
    assert result.status == "completed", f"Extracción falló: {result.error}"
    assert result.products_extracted >= 500, f"Insuficientes productos: {result.products_extracted}"
    assert result.pages_processed >= 10, f"Pocas páginas procesadas: {result.pages_processed}"
    assert result.extraction_accuracy >= 0.95, f"Accuracy baja: {result.extraction_accuracy}"
    
    # Verificar performance
    total_time = performance_tracker.total_time
    assert total_time < 300, f"Extracción muy lenta: {total_time}s (max: 300s)"
    
    # Verificar uso de memoria
    peak_memory = performance_tracker.peak_memory_mb
    assert peak_memory < 1024, f"Uso excesivo de memoria: {peak_memory}MB"
    
    # Verificar estructura de productos AVAZ específica
    products = result.products
    assert len(products) >= 500, "Productos insuficientes"
    
    sample_product = products[0]
    automotive_product = next((p for p in products if "filtro" in p.get("title", "").lower()), None)
    assert automotive_product is not None, "No se encontraron productos automotrices"
    # Validar campos obligatorios
    required_fields = ["sku", "title", "price", "images", "description", "stock_status"]
    for product in products[:10]:  # Verificar primeros 10
        for field in required_fields:
            assert product.get(field) is not None, f"Campo {field} faltante en producto {product.get('sku')}"
        
        # Validaciones específicas
        assert isinstance(product["price"], (int, float)), "Precio debe ser numérico"
        assert product["price"] > 0, "Precio debe ser positivo"
        assert len(product["title"]) > 10, "Título muy corto"
        assert len(product["images"]) > 0, "Producto sin imágenes"
    
    # Verificar variaciones extraídas (típico en productos automotrices)
    products_with_variations = [p for p in products if p.get("variations")]
    assert len(products_with_variations) > 50, f"Pocas variaciones: {len(products_with_variations)}"
    
    # Verificar productos específicos de AVAZ (automotriz)
    automotive_keywords = ["filtro", "aceite", "freno", "suspension", "motor"]
    automotive_products = []
    for product in products:
        title_lower = product.get("title", "").lower()
        if any(keyword in title_lower for keyword in automotive_keywords):
            automotive_products.append(product)
    
    assert len(automotive_products) >= 100, f"Pocos productos automotrices: {len(automotive_products)}"
    
    # Verificar patterns aprendidos para MercadoLibre
    learned_patterns = result.learned_patterns
    assert "product_listing_selector" in learned_patterns, "Pattern de listado no aprendido"
    assert "price_selector" in learned_patterns, "Pattern de precio no aprendido"
    assert "pagination_pattern" in learned_patterns, "Pattern de paginación no aprendido"
    assert "image_selector" in learned_patterns, "Pattern de imágenes no aprendido"
    
    # Verificar que patterns son válidos
    for pattern_name, pattern_value in learned_patterns.items():
        assert pattern_value is not None, f"Pattern {pattern_name} está vacío"
        assert len(str(pattern_value)) > 5, f"Pattern {pattern_name} muy corto"
    
    # Verificar aislamiento multi-tenant
    stored_products = await PostgresStore().get_products(tenant_id="avaz_automotive")
    assert len(stored_products) == len(products), "Productos no guardados correctamente"
    
    # CRÍTICO: Verificar que no hay contaminación cross-tenant
    other_tenant_products = await PostgresStore().get_products(tenant_id="other_company")
    assert len(other_tenant_products) == 0, "VIOLACIÓN: Cross-tenant contamination detectada"
    
    # Verificar métricas de calidad
    quality_metrics = result.quality_metrics
    assert quality_metrics.duplicate_rate < 0.05, f"Muchos duplicados: {quality_metrics.duplicate_rate}"
    assert quality_metrics.invalid_price_rate < 0.02, f"Precios inválidos: {quality_metrics.invalid_price_rate}"
    assert quality_metrics.missing_image_rate < 0.10, f"Muchos sin imagen: {quality_metrics.missing_image_rate}"


# Datos de prueba para mocking
SAMPLE_ML_HTML_AVAZ = """
<div class="ui-search-results">
    <div class="ui-search-result">
        <h2 class="ui-search-item__title">Filtro de Aceite Bosch 0451103316 para Tsuru</h2>
        <span class="price-tag-amount">$245.50</span>
        <span class="ui-search-item__condition">Nuevo</span>
        <div class="ui-search-item__group__element shops__items-group-details">
            <span>12 vendidos</span>
        </div>
        <img src="https://http2.mlstatic.com/filtro-aceite-123.jpg" alt="Filtro">
    </div>
    <div class="ui-search-result">
        <h2 class="ui-search-item__title">Pastillas de Freno Brembo P23-150 Delantera</h2>
        <span class="price-tag-amount">$1,280.00</span>
        <span class="ui-search-item__condition">Nuevo</span>
        <div class="ui-search-item__group__element shops__items-group-details">
            <span>45 vendidos</span>
        </div>
        <img src="https://http2.mlstatic.com/pastillas-freno-456.jpg" alt="Pastillas">
    </div>
    <!-- Simular más productos automotrices -->
</div>
<div class="ui-search-pagination">
    <a href="/page/2">Siguiente</a>
</div>
"""


@pytest.mark.integration
@pytest.mark.skip(reason="Solo ejecutar en CI con datos reales")
async def test_s01_real_mercadolibre_integration():
    """
    LOGRABLE: Test de integración REAL con MercadoLibre AVAZ
    TAGS: #integration #real-data #ci-only #avaz
    REQUIERE: Variables de entorno reales
    """
    if not os.getenv("RUN_INTEGRATION_TESTS"):
        pytest.skip("Integration tests disabled - set RUN_INTEGRATION_TESTS=1")
    
    # Configuración para URL real de AVAZ (controlada)
    real_config = {
        "tenant_id": "avaz_integration_test",
        "source": {
            "type": "mercadolibre",
            "url": os.getenv("AVAZ_ML_URL", "https://listado.mercadolibre.com.mx/repuestos-autos-motos"),
            "config": {
                "max_pages": 3,  # Solo 3 páginas para CI
                "rate_limit": {"requests_per_minute": 30}  # Más conservador
            }
        }
    }
    
    orchestrator = CatalogOrchestrator()
    result = await orchestrator.start_catalog_extraction(real_config)
    
    # Validaciones básicas para datos reales
    assert result.status == "completed"
    assert result.products_extracted > 50  # Al menos 50 productos reales
    assert result.extraction_accuracy > 0.80  # Más permisivo para datos reales
    

@pytest.mark.performance  
@pytest.mark.timeout(900)  # 15 minutos para test de performance
async def test_s01_performance_benchmark():
    """
    LOGRABLE: Procesar 1000+ productos en <10 minutos con <1GB RAM
    TAGS: #performance #benchmark #load-test #memory-test
    TIMEOUT: 15 minutos
    """
    # Configuración para volumen alto
    large_config = {
        "tenant_id": "avaz_performance_test",
        "source": {
            "type": "mercadolibre", 
            "url": "https://mock-mercadolibre.com/avaz",
            "config": {
                "max_pages": 100,  # Simular 100 páginas
                "concurrent_requests": 5,
                "batch_size": 50
            }
        }
    }
    
    # Mock para simular respuesta rápida con muchos productos
    with patch('src.utils.selenium_driver.SeleniumDriver') as mock_driver:
        # Simular página con 20 productos cada una
        mock_html = SAMPLE_ML_HTML_AVAZ * 10  # 20 productos por página
        mock_driver.return_value.get_page.return_value = mock_html
        
        start_time = time.time()
        initial_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
        orchestrator = CatalogOrchestrator()
        result = await orchestrator.start_catalog_extraction(large_config)
        
        duration = time.time() - start_time
        final_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        memory_used = final_memory - initial_memory
    
    # Verificaciones de performance
    assert result.products_extracted >= 1000, f"Insuficientes productos: {result.products_extracted}"
    assert duration < 600, f"Muy lento: {duration}s (max: 600s)"
    assert memory_used < 1024, f"Mucha memoria: {memory_used}MB (max: 1024MB)"
    
    # Métricas adicionales
    products_per_second = result.products_extracted / duration
    assert products_per_second > 2, f"Throughput bajo: {products_per_second} p/s"
    
    print(f"\n🎯 PERFORMANCE RESULTS:")
    print(f"   Productos: {result.products_extracted}")
    print(f"   Tiempo: {duration:.2f}s")
    print(f"   Throughput: {products_per_second:.2f} productos/segundo")
    print(f"   Memoria: {memory_used:.2f}MB")
    print(f"   Páginas: {result.pages_processed}")


### 🎬 ESCENARIO S02: Procesamiento de PDF con Tablas y OCR

**Tenant**: Industrial Supplies Co.
**Fuente**: catalog_industrial_2024.pdf (50+ páginas, múltiples tablas)
**Contexto**: PDF complejo con tablas, imágenes de productos, precios en múltiples columnas

#### 🚀 Comandos Ejecutables:
```bash
# 1. Preparar archivo de prueba
wget https://example.com/test-catalogs/industrial_catalog.pdf -O /tmp/test_catalog.pdf
export PDF_TEST_FILE="/tmp/test_catalog.pdf"

# 2. Ejecutar test de OCR
pytest tests/scenarios/test_s02_pdf_processing.py::test_s02_pdf_ocr_extraction -v --tb=long

# 3. Test con diferentes calidades de OCR
pytest tests/scenarios/test_s02_pdf_processing.py -k "ocr_quality" --capture=no

# 4. Verificar accuracy de extracción de tablas
pytest tests/scenarios/test_s02_pdf_processing.py::test_table_extraction_accuracy -s

# 5. Benchmark de performance con PDFs grandes
pytest tests/scenarios/test_s02_pdf_processing.py -m "pdf_performance" --durations=0
```

#### 🎯 LOGRABLES ESPECÍFICOS:
- ✅ Extraer 800+ productos de PDF de 50 páginas
- ✅ OCR accuracy >90% en texto legible  
- ✅ Detectar y extraer 20+ tablas automáticamente
- ✅ Procesar en <8 minutos con <2GB RAM
- ✅ Manejar múltiples layouts de página

#### 🏷️ TAGS: `#pdf-processing #ocr #table-extraction #industrial`

#### Implementación Completa:
```python
# File: tests/scenarios/test_s02_pdf_processing.py
import pytest
import os
import time
from unittest.mock import patch, MagicMock
from src.agents.pdf_processing_agent import PDFProcessingAgent
from src.utils.ocr_engine import TesseractOCR
from src.utils.table_extractor import CamelotTableExtractor
from src.models.product import ProductSchema
import pandas as pd

@pytest.mark.asyncio
@pytest.mark.timeout(600)  # 10 minutos máximo
async def test_s02_pdf_ocr_extraction():
    """
    LOGRABLE: Extraer 800+ productos de PDF industrial con OCR >90% accuracy
    TAGS: #pdf-processing #ocr #table-extraction #industrial
    TIMEOUT: 10 minutos
    MEMORY_LIMIT: 2GB
    """
    # Arrange
    pdf_config = {
        "tenant_id": "industrial_supplies_co",
        "source": {
            "type": "pdf",
            "file_path": "/tmp/industrial_catalog_2024.pdf",
            "config": {
                "ocr_quality": "high",
                "ocr_languages": ["spa", "eng"],
                "extract_tables": True,
                "extract_images": True,
                "multi_column_detection": True,
                "page_range": {"start": 1, "end": 50},
                "confidence_threshold": 0.80
            }
        },
        "validation": {
            "required_fields": ["codigo", "descripcion", "precio", "categoria"],
            "price_validation": True,
            "duplicate_detection": True
        }
    }
    
    # Mock PDF data para testing controlado
    with patch('src.utils.pdf_reader.PDFReader') as mock_reader:
        mock_reader.return_value.get_page_count.return_value = 50
        mock_reader.return_value.extract_page.return_value = SAMPLE_PDF_PAGE_CONTENT
        
        with patch('src.utils.table_extractor.CamelotTableExtractor') as mock_table:
            mock_table.return_value.extract_tables.return_value = SAMPLE_TABLE_DATA
            
            # Act
            pdf_agent = PDFProcessingAgent()
            result = await pdf_agent.process_pdf(pdf_config)
    
    # Assert - Verificaciones específicas para PDF industrial
    assert result.status == "completed", f"Procesamiento falló: {result.error}"
    assert result.products_extracted >= 800, f"Insuficientes productos: {result.products_extracted}"
    assert result.pages_processed == 50, f"No se procesaron todas las páginas: {result.pages_processed}"
    
    # Verificar OCR accuracy
    assert result.ocr_accuracy >= 0.90, f"OCR accuracy baja: {result.ocr_accuracy}"
    
    # Verificar extracción de tablas
    assert result.tables_detected >= 20, f"Pocas tablas detectadas: {result.tables_detected}"
    assert result.tables_extracted >= 18, f"Pocas tablas extraídas: {result.tables_extracted}"
    
    # Verificar productos específicos industriales
    products = result.products
    industrial_keywords = ["tuerca", "tornillo", "arandela", "perno", "brida"]
    industrial_products = [
        p for p in products 
        if any(kw in p.get("descripcion", "").lower() for kw in industrial_keywords)
    ]
    assert len(industrial_products) >= 200, f"Pocos productos industriales: {len(industrial_products)}"
    
    # Verificar structure de productos industriales
    for product in products[:10]:
        assert product.get("codigo"), "Código de producto faltante"
        assert product.get("descripcion"), "Descripción faltante"
        assert product.get("precio"), "Precio faltante"
        assert isinstance(product["precio"], (int, float)), "Precio no numérico"
        
        # Validaciones específicas industriales
        if product.get("categoria"):
            industrial_categories = ["ferreteria", "tornilleria", "hidraulica", "neumatica"]
            assert any(cat in product["categoria"].lower() for cat in industrial_categories), \
                   f"Categoría no industrial: {product['categoria']}"

# Datos de prueba
SAMPLE_PDF_PAGE_CONTENT = """
CATÁLOGO INDUSTRIAL 2024 - Página 15

TORNILLERÍA MÉTRICA

Código    Descripción                     Precio  Stock
TM-001    Tornillo M8x20 Zincado         $12.50   500
TM-002    Tuerca M8 Hexagonal           $5.80    1000
TM-003    Arandela M8 Plana             $2.30    2000

HIDRÁULICA

Código    Descripción                     Precio  Stock  
HD-001    Manguera 1/2" x 10m           $245.00   50
HD-002    Conexión NPT 1/4"             $18.50    200
"""

SAMPLE_TABLE_DATA = [
    pd.DataFrame({
        'Código': ['TM-001', 'TM-002', 'TM-003'],
        'Descripción': ['Tornillo M8x20 Zincado', 'Tuerca M8 Hexagonal', 'Arandela M8 Plana'],
        'Precio': [12.50, 5.80, 2.30],
        'Stock': [500, 1000, 2000]
    }),
    pd.DataFrame({
        'Código': ['HD-001', 'HD-002'],
        'Descripción': ['Manguera 1/2" x 10m', 'Conexión NPT 1/4"'],
        'Precio': [245.00, 18.50],
        'Stock': [50, 200]
    })
]

@pytest.mark.performance
async def test_s02_pdf_performance_benchmark():
    """
    LOGRABLE: Procesar PDF de 100+ páginas en <15 minutos
    TAGS: #pdf-performance #memory-test #ocr-benchmark
    """
    large_pdf_config = {
        "tenant_id": "performance_test",
        "source": {
            "file_path": "/tmp/large_catalog.pdf",
            "config": {
                "page_range": {"start": 1, "end": 100},
                "parallel_processing": True,
                "batch_size": 10
            }
        }
    }
    
    start_time = time.time()
    initial_memory = psutil.Process().memory_info().rss / 1024 / 1024
    
    # Mock para simular procesamiento rápido
    with patch('src.agents.pdf_processing_agent.PDFProcessingAgent') as mock_agent:
        mock_agent.return_value.process_pdf.return_value = MagicMock(
            status="completed",
            products_extracted=2000,
            pages_processed=100,
            ocr_accuracy=0.92
        )
        
        agent = PDFProcessingAgent()
        result = await agent.process_pdf(large_pdf_config)
    
    duration = time.time() - start_time
    final_memory = psutil.Process().memory_info().rss / 1024 / 1024
    memory_used = final_memory - initial_memory
    
    # Verificaciones de performance
    assert duration < 900, f"Muy lento: {duration}s (max: 900s)"  # 15 min
    assert memory_used < 2048, f"Mucha memoria: {memory_used}MB (max: 2GB)"
    assert result.products_extracted >= 1500, f"Pocos productos: {result.products_extracted}"
    
    pages_per_minute = result.pages_processed / (duration / 60)
    assert pages_per_minute > 6, f"Procesamiento lento: {pages_per_minute} páginas/min"
```
    
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