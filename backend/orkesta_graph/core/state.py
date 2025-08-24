"""
State management for Orkesta LangGraph workflows
"""
from typing import TypedDict, List, Dict, Any, Optional, Annotated, Sequence
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid


class ExtractionStatus(str, Enum):
    """Status of extraction jobs"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    REQUIRES_HUMAN_REVIEW = "requires_human_review"
    CANCELLED = "cancelled"


class SourceType(str, Enum):
    """Types of data sources"""
    WEB = "web"
    PDF = "pdf"
    API = "api"
    EXCEL = "excel"
    IMAGE = "image"
    MANUAL = "manual"


class AgentType(str, Enum):
    """Types of specialized agents"""
    WEB_SCRAPER = "web_scraper"
    PDF_PROCESSOR = "pdf_processor"
    NORMALIZER = "normalizer"
    VALIDATOR = "validator"
    CONSOLIDATOR = "consolidator"
    PATTERN_LEARNER = "pattern_learner"


@dataclass
class ProductData:
    """Structure for product data at various stages"""
    id: Optional[str] = None
    sku: Optional[str] = None
    name: Optional[str] = None
    normalized_name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    brand: Optional[str] = None
    price: Optional[float] = None
    currency: str = "MXN"
    stock: Optional[int] = None
    images: List[str] = field(default_factory=list)
    
    # Metadata
    source_reference: Optional[Dict[str, Any]] = None
    extraction_confidence: float = 0.0
    data_completeness_score: float = 0.0
    validation_errors: List[str] = field(default_factory=list)
    
    # Timestamps
    extracted_at: Optional[datetime] = None
    normalized_at: Optional[datetime] = None
    validated_at: Optional[datetime] = None


@dataclass
class ExtractionSource:
    """Configuration for an extraction source"""
    type: SourceType
    url: Optional[str] = None
    file_path: Optional[str] = None
    config: Dict[str, Any] = field(default_factory=dict)
    
    # Metadata
    name: Optional[str] = None
    last_extracted_at: Optional[datetime] = None
    success_rate: float = 1.0
    

@dataclass
class ExtractionPattern:
    """Learned patterns for web scraping"""
    domain: str
    pattern_type: str  # "product_listing", "price", "title", etc.
    selector: str      # CSS selector or XPath
    confidence: float = 1.0
    success_rate: float = 1.0
    times_used: int = 0
    last_used_at: Optional[datetime] = None


@dataclass
class QualityMetrics:
    """Quality metrics for extracted data"""
    total_items: int = 0
    valid_items: int = 0
    invalid_items: int = 0
    confidence_scores: List[float] = field(default_factory=list)
    completeness_scores: List[float] = field(default_factory=list)
    
    @property
    def average_confidence(self) -> float:
        if not self.confidence_scores:
            return 0.0
        return sum(self.confidence_scores) / len(self.confidence_scores)
    
    @property
    def average_completeness(self) -> float:
        if not self.completeness_scores:
            return 0.0
        return sum(self.completeness_scores) / len(self.completeness_scores)
    
    @property
    def success_rate(self) -> float:
        if self.total_items == 0:
            return 0.0
        return self.valid_items / self.total_items


class CatalogExtractionState(TypedDict):
    """
    Main state for catalog extraction workflows
    This is the core state that flows through all LangGraph nodes
    """
    
    # Message chain for LangGraph
    messages: Annotated[Sequence[BaseMessage], add_messages]
    
    # Job identification
    job_id: str
    tenant_id: str
    
    # Extraction configuration
    sources: List[ExtractionSource]
    extraction_config: Dict[str, Any]
    
    # Current processing state  
    current_step: str
    current_agent: Optional[AgentType]
    status: ExtractionStatus
    
    # Progressive results at each stage
    raw_products: List[Dict[str, Any]]        # Direct from sources
    normalized_products: List[ProductData]    # After normalization
    consolidated_products: List[ProductData]  # After deduplication
    final_products: List[ProductData]         # Ready for database
    
    # Quality and validation
    quality_metrics: QualityMetrics
    validation_results: Dict[str, Any]
    confidence_scores: Dict[str, float]
    
    # Learning and patterns
    learned_patterns: List[ExtractionPattern]
    mapping_rules: Dict[str, Any]
    normalization_stats: Dict[str, Any]
    
    # Error handling
    errors: List[Dict[str, Any]]
    warnings: List[str]
    error_count: int
    max_errors: int
    
    # Human-in-the-loop
    requires_human_approval: bool
    human_review_items: List[Dict[str, Any]]
    human_feedback: Optional[Dict[str, Any]]
    
    # Progress tracking
    total_sources: int
    completed_sources: int
    total_products_expected: int
    products_processed: int
    
    # Timing
    started_at: Optional[datetime]
    estimated_completion: Optional[datetime]
    last_checkpoint_at: Optional[datetime]
    
    # Checkpointing for long-running jobs
    job_checkpoint_id: str  # Renamed to avoid conflict with LangGraph reserved name
    checkpoint_data: Dict[str, Any]


class WebScrapingState(TypedDict):
    """Specialized state for web scraping subgraph"""
    
    # Inherited from parent
    tenant_id: str
    job_id: str
    
    # Web scraping specific
    target_url: str
    domain: str
    page_type: str  # "listing", "detail", "pagination"
    
    # Browser state
    current_page: int
    total_pages: int
    max_pages: int
    
    # Extraction results
    products_found: List[Dict[str, Any]]
    images_extracted: List[str]
    pagination_urls: List[str]
    
    # Patterns and learning
    detected_patterns: Dict[str, str]
    pattern_confidence: Dict[str, float]
    
    # Anti-detection
    last_request_time: Optional[datetime]
    requests_made: int
    rate_limit_delay: float
    
    # Error handling
    scraping_errors: List[str]
    retry_count: int
    max_retries: int


class PDFProcessingState(TypedDict):
    """Specialized state for PDF processing subgraph"""
    
    # Inherited from parent
    tenant_id: str
    job_id: str
    
    # PDF specific
    file_path: str
    total_pages: int
    current_page: int
    
    # Document analysis
    is_scanned: bool
    has_tables: bool
    has_images: bool
    layout_type: str  # "single_column", "multi_column", "mixed"
    
    # Extraction results
    text_content: Dict[int, str]  # page_num -> extracted_text
    tables_found: List[Dict[str, Any]]
    images_extracted: List[Dict[str, Any]]
    
    # OCR results
    ocr_confidence_by_page: Dict[int, float]
    ocr_engine_used: Dict[int, str]
    
    # Processing stats
    pages_processed: int
    pages_failed: int
    processing_time_per_page: Dict[int, float]


class NormalizationState(TypedDict):
    """Specialized state for normalization pipeline"""
    
    # Inherited from parent
    tenant_id: str
    job_id: str
    
    # Input data from multiple sources
    source_data: Dict[str, List[Dict[str, Any]]]  # source_name -> products
    
    # Schema detection
    detected_schemas: Dict[str, Dict[str, Any]]
    schema_confidence: Dict[str, float]
    
    # Mapping and transformation
    mapping_rules: Dict[str, Dict[str, Any]]
    transformation_results: Dict[str, List[ProductData]]
    
    # Deduplication
    potential_duplicates: List[Dict[str, Any]]
    deduplication_rules: Dict[str, Any]
    merge_decisions: List[Dict[str, Any]]
    
    # Quality assessment
    data_quality_scores: Dict[str, float]
    completeness_by_field: Dict[str, float]
    consistency_scores: Dict[str, float]


# Helper functions for state management

def create_initial_state(
    tenant_id: str,
    sources: List[ExtractionSource],
    extraction_config: Dict[str, Any] = None
) -> CatalogExtractionState:
    """Create initial state for catalog extraction"""
    
    job_id = str(uuid.uuid4())
    
    return CatalogExtractionState(
        messages=[],
        job_id=job_id,
        tenant_id=tenant_id,
        sources=sources,
        extraction_config=extraction_config or {},
        current_step="initialization",
        current_agent=None,
        status=ExtractionStatus.PENDING,
        raw_products=[],
        normalized_products=[],
        consolidated_products=[],
        final_products=[],
        quality_metrics=QualityMetrics(),
        validation_results={},
        confidence_scores={},
        learned_patterns=[],
        mapping_rules={},
        normalization_stats={},
        errors=[],
        warnings=[],
        error_count=0,
        max_errors=50,
        requires_human_approval=False,
        human_review_items=[],
        human_feedback=None,
        total_sources=len(sources),
        completed_sources=0,
        total_products_expected=0,
        products_processed=0,
        started_at=datetime.utcnow(),
        estimated_completion=None,
        last_checkpoint_at=None,
        job_checkpoint_id=str(uuid.uuid4()),
        checkpoint_data={}
    )


def update_quality_metrics(
    state: CatalogExtractionState, 
    products: List[ProductData]
) -> QualityMetrics:
    """Update quality metrics based on processed products"""
    
    if not products:
        return state["quality_metrics"]
    
    confidence_scores = [p.extraction_confidence for p in products if p.extraction_confidence > 0]
    completeness_scores = [p.data_completeness_score for p in products if p.data_completeness_score > 0]
    
    valid_products = len([p for p in products if not p.validation_errors])
    
    return QualityMetrics(
        total_items=len(products),
        valid_items=valid_products,
        invalid_items=len(products) - valid_products,
        confidence_scores=confidence_scores,
        completeness_scores=completeness_scores
    )


def should_require_human_review(
    state: CatalogExtractionState,
    threshold: float = 0.7
) -> bool:
    """Determine if human review is required based on quality metrics"""
    
    metrics = state["quality_metrics"]
    
    # Require review if average confidence is low
    if metrics.average_confidence < threshold:
        return True
    
    # Require review if success rate is low
    if metrics.success_rate < 0.8:
        return True
    
    # Require review if there are many errors
    if state["error_count"] > 10:
        return True
    
    return False


def create_checkpoint_data(state: CatalogExtractionState) -> Dict[str, Any]:
    """Create checkpoint data for resuming workflows"""
    
    return {
        "job_id": state["job_id"],
        "tenant_id": state["tenant_id"],
        "current_step": state["current_step"],
        "status": state["status"],
        "products_processed": state["products_processed"],
        "completed_sources": state["completed_sources"],
        "learned_patterns": [
            {
                "domain": p.domain,
                "pattern_type": p.pattern_type,
                "selector": p.selector,
                "confidence": p.confidence
            }
            for p in state["learned_patterns"]
        ],
        "errors": state["errors"],
        "warnings": state["warnings"],
        "checkpoint_created_at": datetime.utcnow().isoformat()
    }