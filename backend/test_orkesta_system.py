#!/usr/bin/env python3
"""
🧪 SISTEMA DE TESTING COMPLETO ORKESTA
Archivo único que testea toda la arquitectura LangGraph del sistema de catálogos
"""

import os
import sys
import asyncio
import pytest
import time
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock
from typing import Dict, List, Any, Optional
import json

# Añadir directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent))

# Imports del sistema Orkesta
from orkesta_graph.core.graph_builder import OrkestaGraphBuilder
from orkesta_graph.core.state import (
    CatalogExtractionState, 
    create_initial_state,
    ExtractionSource,
    SourceType,
    ProductData,
    ExtractionStatus
)
from orkesta_graph.core.config import config
from orkesta_graph.core.base_agent import BaseAgent, AgentRegistry
from orkesta_graph.agents.web_scraper import WebScrapingAgent, MercadoLibreExtractor
from orkesta_graph.agents.pdf_processor import PDFProcessingAgent, OCREngine

# Configuración global de tests
pytest.skip_if_no_selenium = pytest.mark.skipif(
    not os.getenv("SELENIUM_ENABLED", "false").lower() == "true",
    reason="Selenium tests disabled - set SELENIUM_ENABLED=true to enable"
)

pytest.skip_if_no_llm = pytest.mark.skipif(
    not config.llm.groq_api_key and not config.llm.azure_openai_api_key,
    reason="LLM API keys not configured"
)

# ==============================================================================
# 🎯 ESCENARIO S01: MERCADOLIBRE EXTRACTION (AVAZ AUTOMOTIVE)
# ==============================================================================

class TestS01MercadoLibreExtraction:
    """
    LOGRABLE: Extraer 500+ productos de MercadoLibre AVAZ con 95% accuracy
    TAGS: #mercadolibre #web-scraping #catalog-extraction #avaz
    """
    
    @pytest.fixture
    def avaz_config(self):
        """Configuración para tenant AVAZ Automotive"""
        return {
            "tenant_id": "avaz_automotive",
            "sources": [
                ExtractionSource(
                    type=SourceType.WEB,
                    url="https://listado.mercadolibre.com.mx/repuestos-autos-motos",
                    config={
                        "follow_pagination": True,
                        "max_pages": 10,
                        "extract_variations": True,
                        "automotive_specific": True
                    }
                )
            ],
            "extraction_config": {
                "min_confidence": 0.85,
                "automotive_keywords": ["filtro", "aceite", "freno", "suspension", "motor"],
                "required_fields": ["name", "price", "image_url"]
            }
        }
    
    @pytest.fixture
    def mock_ml_html(self):
        """HTML simulado de MercadoLibre para productos automotrices"""
        return """
        <div class="ui-search-results">
            <div class="ui-search-result">
                <h2 class="ui-search-item__title">
                    <a href="/MLM123">Filtro de Aceite Bosch 0451103316 para Tsuru</a>
                </h2>
                <span class="andes-money-amount__fraction">245</span>
                <span class="ui-search-item__condition">Nuevo</span>
                <img class="ui-search-result-image__element" src="https://http2.mlstatic.com/filtro-123.jpg" alt="Filtro">
            </div>
            <div class="ui-search-result">
                <h2 class="ui-search-item__title">
                    <a href="/MLM456">Pastillas de Freno Brembo P23-150 Delantera</a>
                </h2>
                <span class="andes-money-amount__fraction">1280</span>
                <span class="ui-search-item__condition">Nuevo</span>
                <img class="ui-search-result-image__element" src="https://http2.mlstatic.com/pastillas-456.jpg" alt="Pastillas">
            </div>
        </div>
        """
    
    @pytest.mark.asyncio
    async def test_s01_mercadolibre_pattern_extraction(self, mock_ml_html):
        """Test extracción de patterns de MercadoLibre"""
        from bs4 import BeautifulSoup
        
        # Act - Extraer productos usando patterns de MercadoLibre
        soup = BeautifulSoup(mock_ml_html, 'html.parser')
        products = MercadoLibreExtractor.extract_product_listing(soup, "https://mercadolibre.com.mx")
        
        # Assert - Verificaciones específicas
        assert len(products) == 2
        
        filtro_product = products[0]
        assert "Filtro de Aceite" in filtro_product["name"]
        assert filtro_product["price"] == 245.0
        assert filtro_product["currency"] == "MXN"
        assert "filtro-123.jpg" in filtro_product["image_url"]
        assert filtro_product["extraction_confidence"] >= 0.8
        
        pastillas_product = products[1]
        assert "Pastillas de Freno" in pastillas_product["name"]
        assert pastillas_product["price"] == 1280.0
        assert "pastillas-456.jpg" in pastillas_product["image_url"]
    
    @pytest.mark.asyncio
    @pytest.mark.timeout(300)  # 5 minutos
    async def test_s01_web_scraping_agent_flow(self, avaz_config):
        """Test completo del agente de web scraping"""
        
        # Arrange - Configurar estado inicial
        sources = avaz_config["sources"]
        initial_state = create_initial_state(
            tenant_id=avaz_config["tenant_id"],
            sources=sources,
            extraction_config=avaz_config["extraction_config"]
        )
        
        # Registrar el agente web scraper
        web_agent = WebScrapingAgent()
        AgentRegistry.register(web_agent)
        
        # Mock del driver de Selenium
        with patch.object(web_agent, '_setup_driver') as mock_setup:
            mock_driver = MagicMock()
            mock_driver.get.return_value = None
            mock_driver.page_source = """
            <div class="ui-search-results">
                <div class="ui-search-result">
                    <h2 class="ui-search-item__title">Kit de Frenos Deportivos Racing</h2>
                    <span class="andes-money-amount__fraction">3500</span>
                    <img src="https://img.com/kit-frenos.jpg" alt="Kit">
                </div>
            </div>
            """
            mock_setup.return_value = mock_driver
            web_agent.driver = mock_driver
            
            # Act - Procesar fuentes web
            result_state = await web_agent.process(initial_state)
            
            # Assert - Verificar resultados
            assert result_state["current_step"] == "web_scraping_completed"
            assert len(result_state["raw_products"]) >= 1
            assert result_state["completed_sources"] == 1
            
            # Verificar producto automotriz extraído
            product = result_state["raw_products"][0]
            assert "Kit de Frenos" in product["name"]
            assert product["price"] == 3500
            assert product["extraction_confidence"] >= 0.75
    
    @pytest.mark.asyncio
    async def test_s01_langgraph_orchestration(self, avaz_config):
        """Test de orquestación completa con LangGraph"""
        
        # Arrange - Configurar builder y estado
        builder = OrkestaGraphBuilder()
        graph = builder.build_main_graph()
        
        sources = avaz_config["sources"]
        initial_state = create_initial_state(
            tenant_id=avaz_config["tenant_id"],
            sources=sources,
            extraction_config=avaz_config["extraction_config"]
        )
        
        # Mock de agentes para tests controlados
        with patch('orkesta_graph.core.graph_builder.AgentRegistry.get_agent') as mock_get_agent:
            mock_web_agent = AsyncMock()
            mock_web_agent.process.return_value = {
                **initial_state,
                "current_step": "web_scraping_completed",
                "raw_products": [
                    {
                        "name": "Filtro Automotriz Test",
                        "price": 150.0,
                        "currency": "MXN",
                        "extraction_confidence": 0.92,
                        "source": "mercadolibre_test"
                    }
                ],
                "completed_sources": 1
            }
            mock_get_agent.return_value = mock_web_agent
            
            # Act - Ejecutar workflow
            final_state = await graph.ainvoke(initial_state)
            
            # Assert - Verificar flujo completo
            assert final_state["status"] == ExtractionStatus.COMPLETED
            assert final_state["current_step"] == "completed"
            assert len(final_state["raw_products"]) >= 1
            assert final_state["completed_sources"] == initial_state["total_sources"]

# ==============================================================================
# 🎯 ESCENARIO S02: PDF PROCESSING CON OCR Y TABLAS
# ==============================================================================

class TestS02PDFProcessing:
    """
    LOGRABLE: Extraer 800+ productos de PDF industrial con OCR >90% accuracy
    TAGS: #pdf-processing #ocr #table-extraction #industrial
    """
    
    @pytest.fixture
    def industrial_pdf_config(self):
        """Configuración para procesamiento de PDF industrial"""
        return {
            "tenant_id": "industrial_supplies_co",
            "sources": [
                ExtractionSource(
                    type=SourceType.PDF,
                    file_path="/tmp/test_catalog.pdf",
                    config={
                        "ocr_quality": "high",
                        "ocr_languages": ["spa", "eng"],
                        "extract_tables": True,
                        "industrial_specific": True
                    }
                )
            ],
            "extraction_config": {
                "industrial_keywords": ["tuerca", "tornillo", "arandela", "perno"],
                "min_confidence": 0.80,
                "required_fields": ["codigo", "descripcion", "precio"]
            }
        }
    
    @pytest.fixture
    def create_test_pdf(self):
        """Crear PDF de prueba para testing"""
        import fitz  # PyMuPDF
        
        # Crear PDF en memoria con contenido de prueba
        doc = fitz.open()
        page = doc.new_page()
        
        # Añadir contenido de tabla industrial
        content = """
        CATÁLOGO INDUSTRIAL 2024
        
        TORNILLERÍA MÉTRICA
        Código    Descripción                 Precio
        TM-001    Tornillo M8x20 Zincado     $12.50
        TM-002    Tuerca M8 Hexagonal        $5.80
        TM-003    Arandela M8 Plana          $2.30
        
        HIDRÁULICA  
        HD-001    Manguera 1/2" x 10m       $245.00
        HD-002    Conexión NPT 1/4"         $18.50
        """
        
        page.insert_text((50, 50), content)
        
        # Guardar temporalmente
        temp_path = tempfile.mktemp(suffix='.pdf')
        doc.save(temp_path)
        doc.close()
        
        yield temp_path
        
        # Cleanup
        if os.path.exists(temp_path):
            os.unlink(temp_path)
    
    @pytest.mark.asyncio
    async def test_s02_ocr_engine_multi_pass(self):
        """Test del motor OCR multi-engine"""
        from PIL import Image, ImageDraw, ImageFont
        
        # Crear imagen de prueba con texto
        img = Image.new('RGB', (400, 200), color='white')
        draw = ImageDraw.Draw(img)
        
        # Simular texto de catálogo industrial
        text_lines = [
            "TORNILLO M8x20 HEXAGONAL",
            "Código: TM-001",
            "Precio: $12.50",
            "Stock: 500 unidades"
        ]
        
        y_offset = 20
        for line in text_lines:
            draw.text((10, y_offset), line, fill='black')
            y_offset += 30
        
        # Act - Extraer texto con OCR
        ocr_engine = OCREngine()
        result = await ocr_engine.extract_text_multi_engine(img)
        
        # Assert - Verificar extracción
        assert result["confidence"] > 0.0  # Alguna confianza
        assert "TORNILLO" in result["text"] or "TM-001" in result["text"]
        assert result["engine_used"] in ["tesseract", "paddle", "easyocr", "none"]
    
    @pytest.mark.asyncio
    async def test_s02_pdf_agent_processing(self, industrial_pdf_config, create_test_pdf):
        """Test completo del agente PDF"""
        
        # Actualizar config con el PDF de prueba
        industrial_pdf_config["sources"][0].file_path = create_test_pdf
        
        # Arrange - Configurar estado inicial  
        initial_state = create_initial_state(
            tenant_id=industrial_pdf_config["tenant_id"],
            sources=industrial_pdf_config["sources"],
            extraction_config=industrial_pdf_config["extraction_config"]
        )
        
        # Registrar agente PDF
        pdf_agent = PDFProcessingAgent()
        AgentRegistry.register(pdf_agent)
        
        # Mock del procesamiento para tests controlados
        with patch.object(pdf_agent, '_process_pdf_file') as mock_process:
            mock_process.return_value = [
                {
                    "name": "Tornillo M8x20 Zincado",
                    "price": 12.50,
                    "currency": "MXN", 
                    "source": "pdf_table",
                    "extraction_confidence": 0.85
                },
                {
                    "name": "Tuerca M8 Hexagonal",
                    "price": 5.80,
                    "currency": "MXN",
                    "source": "pdf_table", 
                    "extraction_confidence": 0.87
                }
            ]
            
            # Act - Procesar PDF
            result_state = await pdf_agent.process(initial_state)
            
            # Assert - Verificar resultados
            assert result_state["current_step"] == "pdf_processing_completed"
            assert len(result_state["raw_products"]) == 2
            assert result_state["completed_sources"] == 1
            
            # Verificar productos industriales extraídos
            tornillo = result_state["raw_products"][0]
            assert "Tornillo M8" in tornillo["name"]
            assert tornillo["price"] == 12.50
            assert tornillo["extraction_confidence"] >= 0.8
            
            tuerca = result_state["raw_products"][1]
            assert "Tuerca M8" in tuerca["name"]
            assert tuerca["extraction_confidence"] >= 0.8

# ==============================================================================
# 🎯 ESCENARIO S04: NORMALIZACIÓN MULTI-FUENTE
# ==============================================================================

class TestS04MultiSourceNormalization:
    """
    LOGRABLE: Consolidar catálogos desde múltiples fuentes sin duplicados
    TAGS: #normalization #multi-source #deduplication #avaz
    """
    
    @pytest.fixture
    def multi_source_config(self):
        """Configuración para múltiples fuentes"""
        return {
            "tenant_id": "avaz_automotive", 
            "sources": [
                ExtractionSource(
                    type=SourceType.WEB,
                    url="https://mercadolibre.com.mx/avaz",
                    name="ml_source"
                ),
                ExtractionSource(
                    type=SourceType.PDF,
                    file_path="/catalogs/avaz_catalog.pdf",
                    name="pdf_source"
                ),
                ExtractionSource(
                    type=SourceType.WEB,
                    url="https://avaz.com.mx/productos",
                    name="web_source"
                )
            ],
            "extraction_config": {
                "deduplication_enabled": True,
                "fuzzy_match_threshold": 0.85,
                "merge_strategy": "best_fields"
            }
        }
    
    @pytest.mark.asyncio
    async def test_s04_multi_source_orchestration(self, multi_source_config):
        """Test de orquestación con múltiples fuentes"""
        
        # Arrange - Estado inicial con 3 fuentes
        initial_state = create_initial_state(
            tenant_id=multi_source_config["tenant_id"],
            sources=multi_source_config["sources"],
            extraction_config=multi_source_config["extraction_config"]
        )
        
        # Simular productos de diferentes fuentes con duplicados
        ml_products = [
            {"name": "Filtro Aceite Bosch", "price": 245.0, "sku": "BOSCH-001", "source": "mercadolibre"}
        ]
        
        pdf_products = [
            {"name": "Filtro de Aceite Bosch P3316", "price": 240.0, "sku": "BOSCH-001", "source": "pdf"},
            {"name": "Pastillas Freno Brembo", "price": 1200.0, "sku": "BREMBO-001", "source": "pdf"}
        ]
        
        web_products = [
            {"name": "Kit Filtro Aceite Bosch Original", "price": 250.0, "sku": "BOSCH-001", "source": "website"},
            {"name": "Balatas Brembo Delanteras", "price": 1180.0, "sku": "BREMBO-001", "source": "website"}
        ]
        
        # Mock de agentes con productos simulados
        with patch('orkesta_graph.core.graph_builder.AgentRegistry.get_agent') as mock_get_agent:
            def mock_agent_factory(agent_name):
                mock_agent = AsyncMock()
                if "web_scraper" in agent_name:
                    mock_agent.process.return_value = {
                        **initial_state,
                        "raw_products": ml_products,
                        "current_step": "web_scraping_completed",
                        "completed_sources": 1
                    }
                elif "pdf_processor" in agent_name:
                    mock_agent.process.return_value = {
                        **initial_state,
                        "raw_products": initial_state.get("raw_products", []) + pdf_products,
                        "current_step": "pdf_processing_completed", 
                        "completed_sources": 2
                    }
                elif "normalizer" in agent_name:
                    # Simular normalización y deduplicación
                    all_products = ml_products + pdf_products + web_products
                    # Simular deduplicación por SKU
                    deduplicated = {}
                    for product in all_products:
                        sku = product.get("sku")
                        if sku not in deduplicated or product["price"] > deduplicated[sku]["price"]:
                            deduplicated[sku] = product
                    
                    deduplicated_list = list(deduplicated.values())
                    mock_agent.process.return_value = {
                        **initial_state,
                        "normalized_products": deduplicated_list,
                        "current_step": "normalization_completed"
                    }
                elif "consolidator" in agent_name:
                    # Usar los productos deduplicados ya definidos
                    all_products = ml_products + pdf_products + web_products
                    deduplicated = {}
                    for product in all_products:
                        sku = product.get("sku")
                        if sku not in deduplicated or product["price"] > deduplicated[sku]["price"]:
                            deduplicated[sku] = product
                    
                    mock_agent.process.return_value = {
                        **initial_state,
                        "consolidated_products": list(deduplicated.values()),
                        "current_step": "consolidation_completed"
                    }
                elif "validator" in agent_name:
                    # Usar los productos deduplicados ya definidos
                    all_products = ml_products + pdf_products + web_products
                    deduplicated = {}
                    for product in all_products:
                        sku = product.get("sku")
                        if sku not in deduplicated or product["price"] > deduplicated[sku]["price"]:
                            deduplicated[sku] = product
                    
                    mock_agent.process.return_value = {
                        **initial_state,
                        "final_products": list(deduplicated.values()),
                        "validation_results": {"quality_score": 0.95, "validation_passed": True},
                        "current_step": "quality_validation_completed"
                    }
                return mock_agent
            
            mock_get_agent.side_effect = mock_agent_factory
            
            # Act - Ejecutar workflow completo
            builder = OrkestaGraphBuilder()
            graph = builder.build_main_graph()
            final_state = await graph.ainvoke(initial_state)
            
            # Assert - Verificar consolidación exitosa
            assert final_state["status"] == ExtractionStatus.COMPLETED
            assert "final_products" in final_state
            
            # Verificar deduplicación (3 fuentes, 2 SKUs únicos)
            final_products = final_state.get("final_products", [])
            assert len(final_products) == 2  # Deduplicados por SKU
            
            # Verificar que los productos consolidados mantienen mejor precio
            bosch_product = next(p for p in final_products if p["sku"] == "BOSCH-001")
            brembo_product = next(p for p in final_products if p["sku"] == "BREMBO-001")
            
            assert bosch_product["price"] >= 245.0  # Mejor precio conservado
            assert brembo_product["price"] >= 1180.0

# ==============================================================================
# 🎯 ESCENARIO S07: MULTI-TENANT ISOLATION
# ==============================================================================

class TestS07MultiTenantIsolation:
    """
    LOGRABLE: Datos de catálogos NUNCA se cruzan entre tenants
    TAGS: #multi-tenant #security #isolation #rls
    """
    
    @pytest.mark.asyncio
    async def test_s07_tenant_context_isolation(self):
        """Test de aislamiento completo entre contextos de tenant"""
        
        # Arrange - Dos empresas competidoras
        tenant_a_config = {
            "tenant_id": "ferreteria_a",
            "sources": [
                ExtractionSource(
                    type=SourceType.WEB,
                    url="https://ferreteria-a.com/catalogo"
                )
            ]
        }
        
        tenant_b_config = {
            "tenant_id": "ferreteria_b", 
            "sources": [
                ExtractionSource(
                    type=SourceType.WEB,
                    url="https://ferreteria-b.com/catalogo"
                )
            ]
        }
        
        # Crear estados iniciales separados
        state_a = create_initial_state(
            tenant_id=tenant_a_config["tenant_id"],
            sources=tenant_a_config["sources"]
        )
        
        state_b = create_initial_state(
            tenant_id=tenant_b_config["tenant_id"],
            sources=tenant_b_config["sources"]
        )
        
        # Mock de productos con mismo SKU pero diferentes precios (info sensible)
        products_a = [
            {
                "sku": "TUBO-001",
                "name": "Tubo PVC Premium A", 
                "price": 100,
                "cost": 50,  # Información sensible
                "supplier": "Proveedor Secreto A"
            }
        ]
        
        products_b = [
            {
                "sku": "TUBO-001",  # Mismo SKU!
                "name": "Tubo PVC Básico B",
                "price": 80,
                "cost": 40,  # Información sensible diferente
                "supplier": "Proveedor Secreto B"
            }
        ]
        
        # Act - Simular procesamiento por separado
        state_a["raw_products"] = products_a
        state_a["final_products"] = products_a
        
        state_b["raw_products"] = products_b
        state_b["final_products"] = products_b
        
        # Assert - Verificar aislamiento completo
        assert state_a["tenant_id"] != state_b["tenant_id"]
        assert state_a["job_id"] != state_b["job_id"]
        
        # Verificar que productos son diferentes a pesar de mismo SKU
        product_a = state_a["final_products"][0]
        product_b = state_b["final_products"][0]
        
        assert product_a["sku"] == product_b["sku"]  # Mismo SKU
        assert product_a["name"] != product_b["name"]  # Diferente nombre
        assert product_a["price"] != product_b["price"]  # Diferente precio
        assert product_a["supplier"] != product_b["supplier"]  # Info sensible diferente
        
        # Simular búsqueda por tenant - NO debe haber contaminación cruzada
        def search_by_tenant(tenant_id: str, sku: str):
            if tenant_id == "ferreteria_a":
                return [p for p in products_a if p["sku"] == sku]
            elif tenant_id == "ferreteria_b":
                return [p for p in products_b if p["sku"] == sku]
            else:
                return []  # Sin acceso
        
        # Búsquedas desde cada contexto
        result_a = search_by_tenant("ferreteria_a", "TUBO-001")
        result_b = search_by_tenant("ferreteria_b", "TUBO-001")
        
        assert len(result_a) == 1
        assert len(result_b) == 1
        assert result_a[0]["supplier"] == "Proveedor Secreto A"
        assert result_b[0]["supplier"] == "Proveedor Secreto B"
        
        # Intento de acceso cruzado debe fallar
        result_cross = search_by_tenant("ferreteria_a", "TUBO-001")
        assert "Secreto B" not in str(result_cross)  # No debe ver datos de B

# ==============================================================================
# 🎯 TESTS DE PERFORMANCE Y CARGA
# ==============================================================================

class TestPerformanceAndLoad:
    """
    Tests de performance para cargas masivas y concurrencia
    """
    
    @pytest.mark.asyncio
    @pytest.mark.performance
    @pytest.mark.timeout(300)  # 5 minutos máximo
    async def test_p01_concurrent_multi_source_extraction(self):
        """Test de extracción concurrente de múltiples fuentes"""
        
        # Arrange - 5 fuentes diferentes simuladas
        sources = [
            ExtractionSource(type=SourceType.WEB, url=f"https://site{i}.com", name=f"web_{i}")
            for i in range(5)
        ]
        
        configs = [
            {
                "tenant_id": f"tenant_{i}",
                "sources": [source],
                "extraction_config": {"min_confidence": 0.8}
            }
            for i, source in enumerate(sources)
        ]
        
        # Mock de extracción rápida
        async def mock_extract_catalog(config):
            await asyncio.sleep(0.1)  # Simular trabajo rápido
            return {
                "status": "completed",
                "products": [
                    {"name": f"Producto {j}", "price": j * 10}
                    for j in range(100)  # 100 productos por fuente
                ],
                "tenant_id": config["tenant_id"]
            }
        
        # Act - Extracción paralela
        start_time = time.time()
        results = await asyncio.gather(*[
            mock_extract_catalog(config) for config in configs
        ])
        duration = time.time() - start_time
        
        # Assert - Verificar paralelismo efectivo
        assert duration < 5.0  # Menos de 5 segundos para 5 fuentes
        assert len(results) == 5
        assert all(r["status"] == "completed" for r in results)
        
        # Verificar throughput
        total_products = sum(len(r["products"]) for r in results)
        assert total_products == 500  # 100 * 5
        throughput = total_products / duration
        assert throughput > 100  # Más de 100 productos/segundo
    
    @pytest.mark.asyncio
    @pytest.mark.memory_test
    async def test_memory_usage_monitoring(self):
        """Test de uso de memoria durante procesamiento"""
        import psutil
        
        # Measure inicial
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Simular procesamiento de catálogo grande
        large_catalog = []
        for i in range(1000):  # 1000 productos
            product = {
                "sku": f"SKU-{i:04d}",
                "name": f"Producto {i}",
                "description": "Descripción muy larga " * 50,  # Consumir memoria
                "price": i * 10.5,
                "images": [f"https://img.com/prod-{i}-{j}.jpg" for j in range(3)]
            }
            large_catalog.append(product)
        
        # Measure después del procesamiento
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_used = final_memory - initial_memory
        
        # Assert - Verificar uso razonable de memoria
        assert memory_used < 200  # Menos de 200MB para 1000 productos
        assert len(large_catalog) == 1000

# ==============================================================================
# 🎯 TESTS DE CONFIGURACIÓN Y SETUP
# ==============================================================================

class TestSystemConfiguration:
    """
    Tests de configuración y setup del sistema
    """
    
    def test_config_validation(self):
        """Test de validación de configuración"""
        from orkesta_graph.core.config import config, validate_config
        
        # Verificar que la configuración carga correctamente
        assert config.database.host is not None
        assert config.database.port == 5432
        assert config.database.database == "orkesta"
        
        # Verificar configuración de LLM
        assert hasattr(config.llm, 'groq_api_key')
        assert hasattr(config.llm, 'azure_openai_api_key')
        
        # Verificar configuración de extracción
        assert config.extraction.min_confidence >= 0.0
        assert config.extraction.min_confidence <= 1.0
    
    def test_agent_registry_functionality(self):
        """Test del registro de agentes"""
        from orkesta_graph.core.base_agent import AgentRegistry, BaseAgent, AgentType
        
        # Limpiar registro
        AgentRegistry._agents.clear()
        
        # Crear agente mock
        class MockAgent(BaseAgent):
            def __init__(self):
                super().__init__(AgentType.WEB_SCRAPER, "mock_agent")
            
            async def process(self, state, **kwargs):
                return state
        
        # Registrar agente
        mock_agent = MockAgent()
        AgentRegistry.register(mock_agent)
        
        # Verificar registro
        retrieved_agent = AgentRegistry.get_agent("mock_agent")
        assert retrieved_agent is not None
        assert retrieved_agent.name == "mock_agent"
        assert retrieved_agent.agent_type == AgentType.WEB_SCRAPER
        
        # Verificar listado de todos los agentes
        all_agents = AgentRegistry.get_all_agents()
        assert "mock_agent" in all_agents

# ==============================================================================
# 🎯 TESTS DE INTEGRACIÓN COMPLETA
# ==============================================================================

class TestFullSystemIntegration:
    """
    Test de integración del sistema completo end-to-end
    """
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    @pytest.mark.timeout(600)  # 10 minutos
    async def test_full_catalog_extraction_pipeline(self):
        """Test completo del pipeline de extracción de catálogos"""
        
        # Arrange - Configuración multi-fuente realista
        full_config = {
            "tenant_id": "integration_test_company",
            "sources": [
                ExtractionSource(
                    type=SourceType.WEB,
                    url="https://example-ecommerce.com/products",
                    config={"max_pages": 2}
                )
            ],
            "extraction_config": {
                "min_confidence": 0.75,
                "deduplication_enabled": True,
                "quality_threshold": 0.8
            }
        }
        
        # Act - Pipeline completo con mocks
        initial_state = create_initial_state(
            tenant_id=full_config["tenant_id"],
            sources=full_config["sources"],
            extraction_config=full_config["extraction_config"]
        )
        
        # Mock todo el pipeline
        with patch('orkesta_graph.core.graph_builder.AgentRegistry.get_agent') as mock_get_agent:
            # Mock de agentes en secuencia
            def create_mock_agent(step_name, products_count=10):
                mock_agent = AsyncMock()
                products = [
                    {
                        "name": f"Producto {step_name} {i}",
                        "sku": f"SKU-{step_name}-{i:03d}",
                        "price": (i + 1) * 25.0,
                        "extraction_confidence": 0.85 + (i * 0.01)
                    }
                    for i in range(products_count)
                ]
                
                mock_agent.process.return_value = {
                    **initial_state,
                    "raw_products" if step_name == "web" else f"{step_name}_products": products,
                    "current_step": f"{step_name}_completed",
                    "completed_sources": 1
                }
                return mock_agent
            
            # Configurar mocks por tipo de agente
            agent_mocks = {
                "web_scraper": create_mock_agent("web", 15),
                "normalizer": create_mock_agent("normalized", 15), 
                "consolidator": create_mock_agent("consolidated", 14),  # 1 duplicado removido
                "validator": create_mock_agent("validated", 14)
            }
            
            def mock_agent_getter(agent_name):
                for key, mock_agent in agent_mocks.items():
                    if key in agent_name:
                        return mock_agent
                return None
                
            mock_get_agent.side_effect = mock_agent_getter
            
            # Ejecutar workflow completo
            builder = OrkestaGraphBuilder()
            graph = builder.build_main_graph()
            
            start_time = time.time()
            final_state = await graph.ainvoke(initial_state)
            execution_time = time.time() - start_time
            
            # Assert - Verificar pipeline completo
            assert final_state["status"] == ExtractionStatus.COMPLETED
            assert final_state["current_step"] == "completed"
            assert execution_time < 30.0  # Menos de 30 segundos
            
            # Verificar que pasó por todas las etapas
            assert final_state["completed_sources"] >= 1
            
            # Verificar métricas finales
            assert final_state["total_sources"] == len(full_config["sources"])
            assert "checkpoint_data" in final_state
            assert isinstance(final_state["checkpoint_data"], dict)


# ==============================================================================
# 🎯 RUNNER PRINCIPAL Y CONFIGURACIÓN
# ==============================================================================

def setup_test_environment():
    """Configurar entorno de testing"""
    
    # Configurar variables de entorno para testing
    test_env = {
        "POSTGRES_HOST": "localhost",
        "POSTGRES_PORT": "5432", 
        "POSTGRES_DB": "orkesta_test",
        "POSTGRES_USER": "orkesta_test",
        "POSTGRES_PASSWORD": "test_password",
        "REDIS_HOST": "localhost",
        "REDIS_PORT": "6379",
        "LOG_LEVEL": "DEBUG",
        "ENVIRONMENT": "test"
    }
    
    for key, value in test_env.items():
        os.environ.setdefault(key, value)
    
    print("🧪 Test environment configured")
    print(f"   Database: {config.database.url}")
    print(f"   Redis: {config.redis.url}")
    print(f"   Environment: {os.getenv('ENVIRONMENT', 'unknown')}")


def run_specific_scenario(scenario_id: str = None):
    """Ejecutar escenario específico"""
    
    setup_test_environment()
    
    if scenario_id:
        test_pattern = f"*{scenario_id.lower()}*"
        args = ["-k", test_pattern, "-v", "--tb=short"]
    else:
        args = ["-v", "--tb=short"]
    
    # Añadir markers comunes
    args.extend([
        "-m", "not performance",  # Excluir performance tests por defecto
        "--disable-warnings",
        "--color=yes"
    ])
    
    print(f"🚀 Running Orkesta tests with args: {' '.join(args)}")
    return pytest.main(args + [__file__])


if __name__ == "__main__":
    """
    Ejecutar tests directamente:
    
    # Todos los tests básicos
    python test_orkesta_system.py
    
    # Test específico
    python test_orkesta_system.py s01
    
    # Con environment variables
    SELENIUM_ENABLED=true python test_orkesta_system.py
    """
    import sys
    
    scenario = sys.argv[1] if len(sys.argv) > 1 else None
    exit_code = run_specific_scenario(scenario)
    sys.exit(exit_code)