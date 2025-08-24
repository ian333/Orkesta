# 🔄 AGENT COMMUNICATION FLOWS - ORKESTA

## 📡 ARQUITECTURA MULTI-AGENTE CON LANGGRAPH

### ARQUITECTURAS IMPLEMENTADAS (2024-2025)

#### 1. HIERARCHICAL TEAMS (Principal)
**Para qué**: Extracción compleja de catálogos con delegación clara
```python
# Arquitectura jerárquica con subgrafos especializados
Catalog Extraction Orchestrator (Supervisor)
├── Web Scraping Team
│   ├── MercadoLibre Specialist (con patterns específicos)
│   ├── Amazon Specialist (maneja variaciones de Amazon)
│   ├── Generic E-commerce Agent (sitios desconocidos)
│   └── Dynamic Content Handler (JavaScript/React sites)
├── Document Processing Team  
│   ├── PDF Table Extractor (Tesseract OCR + Layout detection)
│   ├── Image Analyzer (Multi-modal LLM para productos)
│   ├── Excel/CSV Parser (estructuras complejas)
│   └── Scanned Catalog OCR (multi-pass processing)
├── Normalization Pipeline
│   ├── Schema Detection Agent (identifica estructura)
│   ├── Data Mapping Agent (crea reglas de transformación)
│   ├── Validation Agent (quality assurance)
│   └── Enrichment Agent (completa info faltante)
└── Integration Team
    ├── Multi-tenant Router (aislamiento por cliente)
    ├── Database Writer (PostgreSQL + pgvector)
    └── Notification Agent (alertas y reportes)
```

#### 2. PLAN-AND-EXECUTE ARCHITECTURE
**Para qué**: Procesamiento batch de catálogos grandes
- **Planner**: Analiza el catálogo completo y crea plan detallado
- **Executor**: Ejecuta el plan con modelos más pequeños/rápidos
- **Ventaja**: Menos llamadas a LLM, más eficiente en costo

#### 3. REFLECTION PATTERN (LATS)
**Para qué**: Auto-corrección y mejora continua
- Language Agent Tree Search para explorar mejores estrategias
- Reflection loops para validar calidad de extracción
- Self-critique para mejorar accuracy

#### 4. COLLABORATIVE AGENTS WITH SHARED MEMORY
**Para qué**: Agentes especializados trabajando en paralelo
```python
class CatalogExtractionState(TypedDict):
    # Estado compartido entre todos los agentes
    raw_sources: List[str]  # URLs, PDFs, etc
    extracted_products: List[Product]
    validation_errors: List[Error]
    enrichment_suggestions: List[Suggestion]
    tenant_context: TenantConfig
    extraction_patterns: Dict[str, Pattern]  # Aprendizaje
```

## 🛠️ PROTOCOLO DE MENSAJES CON LANGGRAPH

### Estado Base con LangGraph (2024-2025)
```python
from typing import TypedDict, List, Annotated, Sequence
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.graph.message import add_messages
from langgraph.checkpoint.postgres import PostgresSaver
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

# Estado para el grafo de extracción de catálogos
class CatalogExtractionState(TypedDict):
    # Mensajes con memoria completa
    messages: Annotated[Sequence[BaseMessage], add_messages]
    
    # Estado específico del catálogo
    source_type: str  # "web", "pdf", "api", "image"
    source_url: str
    tenant_id: str
    
    # Productos extraídos progresivamente
    raw_products: List[dict]
    normalized_products: List[dict]
    validation_results: dict
    
    # Patrones aprendidos (para mejorar con el tiempo)
    extraction_patterns: dict
    confidence_scores: dict
    
    # Control flow
    next_action: str
    requires_human_approval: bool
    error_count: int
    
    # Checkpointing para trabajos largos
    checkpoint_id: str
    last_checkpoint: str

# Comando para handoffs entre agentes
class Command(TypedDict):
    """Comando para navegación dinámica en el grafo"""
    goto: str  # Nodo destino
    update: dict  # Actualización de estado
    interrupt: bool  # Si requiere intervención humana
```

## 🚀 LANGGRAPH STATE MANAGEMENT & PERSISTENCE

### Configuración con PostgreSQL Checkpointer
```python
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.graph import StateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_groq import ChatGroq
import asyncpg
import os

class OrkestaGraphBuilder:
    def __init__(self):
        # LLM principal con Groq
        self.llm = ChatGroq(
            model="llama-3.1-70b-versatile",
            temperature=0.1,  # Más determinístico para extracción
            api_key=os.getenv("GROQ_API_KEY")
        )
        
        # Checkpointer para persistencia y human-in-the-loop
        self.checkpointer = PostgresSaver.from_conn_string(
            "postgresql://user:pass@localhost:5432/orkesta"
        )
        
        # Store para memoria a largo plazo
        self.store = InMemoryStore()  # O PostgresStore para producción
        
    def build_catalog_extraction_graph(self):
        """Construir el grafo de extracción de catálogos"""
        workflow = StateGraph(CatalogExtractionState)
        
        # Nodos especializados
        workflow.add_node("source_detector", self.detect_source_type)
        workflow.add_node("web_scraper_team", self.web_scraping_subgraph())
        workflow.add_node("pdf_processor_team", self.pdf_processing_subgraph())
        workflow.add_node("normalizer", self.normalize_products)
        workflow.add_node("validator", self.validate_with_reflection)
        workflow.add_node("human_review", self.human_review_interrupt)
        
        # Edges condicionales basados en tipo de fuente
        workflow.add_conditional_edges(
            "source_detector",
            self.route_by_source_type,
            {
                "web": "web_scraper_team",
                "pdf": "pdf_processor_team",
                "needs_human": "human_review"
            }
        )
        
        # Compilar con checkpointing
        return workflow.compile(
            checkpointer=self.checkpointer,
            interrupt_before=["human_review"]  # Pausa para aprobación
        )
```

## 📊 FLUJOS DE COMUNICACIÓN COMPLEJOS

### 1. Flujo de Extracción de Catálogo Complejo (MercadoLibre + PDF)
```python
# Ejemplo real de extracción multi-fuente
async def extract_automotive_catalog():
    """Extraer catálogo de Equipo Automotriz AVAZ"""
    
    # Crear grafo con checkpointing
    graph = OrkestaGraphBuilder().build_catalog_extraction_graph()
    
    # Estado inicial con múltiples fuentes
    initial_state = {
        "messages": [HumanMessage(
            "Extraer catálogo completo de AVAZ: "
            "1. Scrape https://listado.mercadolibre.com.mx/_CustId_123456"
            "2. Procesar PDF: catalogo_avaz_2024.pdf"
            "3. Enriquecer con API de proveedores"
        )],
        "source_urls": [
            "https://listado.mercadolibre.com.mx/_CustId_123456",
            "file:///catalogs/avaz/catalogo_2024.pdf",
            "api://suppliers/avaz/products"
        ],
        "tenant_id": "avaz_automotive",
        "extraction_config": {
            "deep_scraping": True,
            "follow_pagination": True,
            "extract_images": True,
            "ocr_quality": "high",
            "price_monitoring": True
        }
    }
    
    # Ejecutar con streaming para ver progreso
    async for event in graph.astream(
        initial_state,
        {"configurable": {"thread_id": "avaz_catalog_extraction_001"}}
    ):
        if "web_scraper_team" in event:
            print(f"📦 Productos de MercadoLibre: {len(event['web_scraper_team']['raw_products'])}")
        elif "pdf_processor_team" in event:
            print(f"📄 Productos del PDF: {len(event['pdf_processor_team']['raw_products'])}")
        elif "validator" in event:
            print(f"✅ Validación: {event['validator']['validation_results']}")
```

### 2. Flujo con Human-in-the-Loop para Aprobación
```python
# Interrupción para revisión humana
config = {"configurable": {"thread_id": "review_123"}}

# Primera ejecución - se detiene en human_review
result = await graph.ainvoke(initial_state, config)

if result.get("requires_human_approval"):
    print("🔍 Revisión requerida:")
    print(f"- Productos extraídos: {len(result['normalized_products'])}")
    print(f"- Confianza promedio: {result['confidence_scores']['average']}")
    
    # Usuario revisa y aprueba con cambios
    human_feedback = {
        "approved": True,
        "corrections": [
            {"product_id": "123", "field": "price", "new_value": 450.00}
        ]
    }
    
    # Continuar desde checkpoint con feedback
    final_result = await graph.ainvoke(
        Command(resume=human_feedback),
        config
    )
```

### 3. Flujo de Web Scraping Inteligente con Detección de Patterns
```python
# Subgrafo especializado para MercadoLibre
class MercadoLibreScraperGraph:
    def __init__(self):
        self.workflow = StateGraph(ScrapingState)
        
    def build(self):
        # Nodos especializados para MercadoLibre
        self.workflow.add_node("detect_layout", self.detect_page_layout)
        self.workflow.add_node("extract_listings", self.extract_product_listings)
        self.workflow.add_node("extract_details", self.extract_product_details)
        self.workflow.add_node("handle_pagination", self.handle_pagination)
        self.workflow.add_node("extract_images", self.extract_and_analyze_images)
        
        # Routing inteligente
        self.workflow.add_conditional_edges(
            "detect_layout",
            self.route_by_layout,
            {
                "grid": "extract_listings",
                "list": "extract_listings",
                "single": "extract_details",
                "unknown": "fallback_extractor"
            }
        )
        
        return self.workflow.compile()
    
    async def extract_product_listings(self, state: ScrapingState):
        """Extracción inteligente con patterns aprendidos"""
        
        # Usar patterns guardados si existen
        if state.get("learned_patterns"):
            products = await self.apply_learned_patterns(state)
        else:
            # Detección automática de estructura
            products = await self.auto_detect_structure(state)
            
            # Guardar patterns exitosos
            if products and len(products) > 0:
                state["learned_patterns"] = self.extract_patterns(products)
        
        # Validación con LLM
        validated = await self.validate_with_llm(products)
        
        return {"products": validated, "confidence": 0.95}
```

### 4. Flujo de Normalización con Schema Detection
```python
# Pipeline de normalización inteligente
class NormalizationPipeline:
    def __init__(self):
        self.schema_detector = SchemaDetectionAgent()
        self.mapper = DataMappingAgent()
        self.validator = ValidationAgent()
        
    async def normalize_batch(self, raw_products: List[dict]) -> List[Product]:
        """Normalización inteligente de productos diversos"""
        
        # 1. Detectar schema automáticamente
        detected_schema = await self.schema_detector.detect(raw_products)
        
        # 2. Crear mapping rules con LLM
        mapping_rules = await self.mapper.create_rules(
            source_schema=detected_schema,
            target_schema=ProductSchema,
            examples=raw_products[:5]
        )
        
        # 3. Aplicar transformaciones
        normalized = []
        for product in raw_products:
            try:
                normalized_product = await self.mapper.apply_rules(
                    product, 
                    mapping_rules
                )
                
                # 4. Validar y enriquecer
                validated = await self.validator.validate(
                    normalized_product,
                    confidence_threshold=0.8
                )
                
                if validated.is_valid:
                    normalized.append(validated.product)
                else:
                    # Intentar auto-corrección
                    corrected = await self.auto_correct(validated)
                    if corrected:
                        normalized.append(corrected)
                        
            except Exception as e:
                # Log para mejorar patterns
                await self.log_extraction_error(product, e)
        
        return normalized
```

## 🧠 AGENTES ESPECIALIZADOS COMPLEJOS

### 1. PDF Processing Agent con OCR Multi-Pass
```python
class PDFProcessingAgent:
    """Agente especializado en procesamiento de PDFs complejos"""
    
    def __init__(self):
        self.ocr_engine = TesseractOCR()
        self.layout_detector = LayoutDetector()
        self.table_extractor = CamelotTableExtractor()
        self.llm = ChatGroq(model="llama-3.1-70b")
        
    async def process_pdf(self, pdf_path: str, tenant_config: dict):
        """Procesamiento multi-pass de PDF"""
        
        # Pass 1: Detección de layout
        layout = await self.layout_detector.analyze(pdf_path)
        
        # Pass 2: Extracción por tipo de contenido
        extracted_content = {
            "tables": [],
            "images": [],
            "text": []
        }
        
        for page in layout.pages:
            # Extraer tablas
            if page.has_tables:
                tables = await self.table_extractor.extract(page)
                extracted_content["tables"].extend(tables)
            
            # OCR en imágenes
            if page.has_images:
                for image in page.images:
                    ocr_text = await self.ocr_engine.process(
                        image,
                        confidence_threshold=0.8,
                        language="spa+eng"
                    )
                    
                    # Validar con LLM
                    validated = await self.llm.invoke(
                        f"¿Es esto un producto? {ocr_text}"
                    )
                    
                    if validated.is_product:
                        extracted_content["images"].append({
                            "image": image,
                            "text": ocr_text,
                            "confidence": validated.confidence
                        })
        
        # Pass 3: Consolidación y normalización
        products = await self.consolidate_products(extracted_content)
        
        # Pass 4: Validación con reflection
        final_products = await self.validate_with_reflection(products)
        
        return final_products
```

### 2. Web Scraping Agent con Pattern Learning
```python
class IntelligentWebScrapingAgent:
    """Agente que aprende patterns de scraping"""
    
    def __init__(self):
        self.pattern_db = PatternDatabase()
        self.selenium_driver = SeleniumDriver()
        self.beautifulsoup = BeautifulSoupParser()
        
    async def scrape_with_learning(self, url: str):
        """Scraping inteligente con aprendizaje de patterns"""
        
        domain = extract_domain(url)
        
        # Buscar patterns existentes
        existing_patterns = await self.pattern_db.get_patterns(domain)
        
        if existing_patterns:
            # Usar patterns conocidos
            products = await self.apply_patterns(url, existing_patterns)
            
            # Validar efectividad
            if self.validate_extraction(products):
                return products
        
        # Si no hay patterns o fallaron, detectar nuevos
        new_patterns = await self.detect_patterns(url)
        
        # Aplicar y validar nuevos patterns
        products = await self.apply_patterns(url, new_patterns)
        
        if self.validate_extraction(products):
            # Guardar patterns exitosos
            await self.pattern_db.save_patterns(domain, new_patterns)
            
        return products
    
    async def detect_patterns(self, url: str):
        """Detección automática de patterns con LLM"""
        
        # Obtener HTML
        html = await self.selenium_driver.get_page(url)
        
        # Analizar estructura con LLM
        analysis_prompt = f"""
        Analiza esta estructura HTML y detecta patterns para extraer productos:
        {html[:5000]}
        
        Identifica:
        1. Selectores CSS para productos
        2. Estructura de datos
        3. Paginación
        4. Precios y disponibilidad
        """
        
        patterns = await self.llm.analyze(analysis_prompt)
        
        return patterns
```

### 3. Data Enrichment Agent
```python
class DataEnrichmentAgent:
    """Agente que enriquece productos con datos externos"""
    
    def __init__(self):
        self.google_search = GoogleSearchAPI()
        self.price_apis = [MercadoLibreAPI(), AmazonAPI()]
        self.image_search = GoogleImageSearch()
        
    async def enrich_product(self, product: dict):
        """Enriquecimiento multi-fuente"""
        
        enriched = product.copy()
        
        # 1. Buscar imágenes si faltan
        if not enriched.get("images"):
            images = await self.image_search.find(
                f"{product['name']} {product.get('brand', '')}"
            )
            enriched["images"] = images[:3]
        
        # 2. Comparar precios
        price_comparison = []
        for api in self.price_apis:
            try:
                competitor_price = await api.get_price(product["sku"])
                price_comparison.append({
                    "source": api.name,
                    "price": competitor_price
                })
            except:
                continue
        
        enriched["price_comparison"] = price_comparison
        
        # 3. Obtener descripción completa si falta
        if not enriched.get("description") or len(enriched["description"]) < 50:
            search_result = await self.google_search.search(
                f"{product['name']} descripción especificaciones"
            )
            
            # Usar LLM para extraer descripción relevante
            description = await self.llm.extract(
                f"Extrae una descripción de producto de: {search_result}"
            )
            
            enriched["description"] = description
        
        # 4. Categorización automática
        if not enriched.get("category"):
            category = await self.llm.categorize(product)
            enriched["category"] = category
        
        return enriched
```

## 📈 MONITOREO Y MÉTRICAS

### Dashboard de Agentes en Tiempo Real
```python
class AgentMonitor:
    """Monitor en tiempo real de todos los agentes"""
    
    def __init__(self):
        self.metrics = {}
        self.prometheus = PrometheusClient()
        
    async def track_agent_performance(self):
        """Métricas detalladas por agente"""
        
        return {
            "web_scraping_team": {
                "productos_extraidos": 1234,
                "sitios_procesados": 45,
                "errores": 3,
                "latencia_promedio": "234ms",
                "patterns_aprendidos": 12
            },
            "pdf_processing_team": {
                "pdfs_procesados": 67,
                "paginas_analizadas": 890,
                "ocr_accuracy": 0.94,
                "tablas_extraidas": 234
            },
            "normalization_pipeline": {
                "productos_normalizados": 2340,
                "schemas_detectados": 8,
                "mapping_rules_creadas": 45,
                "validation_rate": 0.92
            }
        }
```

## 🎯 CASOS DE USO ESPECÍFICOS

### Caso 1: Catálogo AVAZ Automotive
```python
# Configuración específica para AVAZ
avaz_config = {
    "tenant_id": "avaz_automotive",
    "sources": [
        {
            "type": "mercadolibre",
            "url": "https://listado.mercadolibre.com.mx/_CustId_AVAZ",
            "config": {
                "follow_all_pages": True,
                "extract_variations": True,
                "monitor_prices": True
            }
        },
        {
            "type": "pdf",
            "path": "/catalogs/avaz/master_catalog_2024.pdf",
            "config": {
                "ocr_quality": "high",
                "extract_tables": True,
                "multi_column": True
            }
        },
        {
            "type": "website",
            "url": "https://avaz.com.mx/catalogo",
            "config": {
                "javascript_render": True,
                "wait_for_ajax": True
            }
        }
    ],
    "enrichment": {
        "cross_reference": True,
        "competitor_pricing": True,
        "image_search": True
    },
    "validation": {
        "required_fields": ["sku", "name", "price", "category"],
        "price_range": [10, 50000],
        "confidence_threshold": 0.85
    }
}

# Ejecutar extracción completa
async def extract_avaz_catalog():
    graph = build_extraction_graph(avaz_config)
    result = await graph.ainvoke(avaz_config)
    return result
```

## ✅ DECISIONES CLAVE

1. **LangGraph sobre otras opciones**: Mejor soporte para grafos complejos y checkpointing
2. **Hierarchical Teams**: Permite especialización y escalabilidad
3. **PostgreSQL para persistencia**: Checkpointing y vector search en un solo lugar
4. **Groq como LLM principal**: Rápido y costo-efectivo
5. **Pattern Learning**: Los agentes mejoran con el tiempo
6. **Human-in-the-Loop**: Control cuando la confianza es baja

## 🚀 PRÓXIMOS PASOS

1. Implementar OrkestaGraphBuilder base
2. Crear subgrafos especializados (Web, PDF, API)
3. Configurar PostgreSQL con pgvector
4. Implementar pattern database
5. Testing con catálogos reales
6. Dashboard de monitoreo