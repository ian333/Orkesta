"""
Main LangGraph builder for Orkesta catalog extraction system
"""
from typing import Dict, Any, List, Optional, Literal
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.prebuilt import ToolNode
from langchain_core.messages import HumanMessage, AIMessage
import asyncio
import logging
from datetime import datetime

from .config import config
from .state import (
    CatalogExtractionState, 
    ExtractionStatus,
    SourceType,
    create_initial_state,
    should_require_human_review
)
from .base_agent import BaseAgent, AgentRegistry


class OrkestaGraphBuilder:
    """
    Main builder for Orkesta catalog extraction workflows
    Creates and manages the LangGraph workflow with specialized agents
    """
    
    def __init__(self):
        self.logger = logging.getLogger("orkesta.graph_builder")
        
        # Initialize checkpointer for persistence
        self.checkpointer = None
        self._setup_checkpointer()
        
        # Agent references (will be populated by specialized agents)
        self.agents = {}
    
    def _setup_checkpointer(self):
        """Setup PostgreSQL checkpointer for workflow persistence"""
        try:
            self.checkpointer = PostgresSaver.from_conn_string(
                config.database.url
            )
            self.logger.info("PostgreSQL checkpointer initialized")
        except Exception as e:
            self.logger.error(f"Failed to setup checkpointer: {e}")
            # For development, we can work without checkpointing
            self.checkpointer = None
    
    def build_main_graph(self) -> StateGraph:
        """
        Build the main catalog extraction workflow
        
        Returns:
            Compiled StateGraph ready for execution
        """
        
        # Create the main workflow graph
        workflow = StateGraph(CatalogExtractionState)
        
        # Add main orchestration nodes
        workflow.add_node("initialize_job", self._initialize_job)
        workflow.add_node("source_detector", self._detect_source_types)
        workflow.add_node("web_scraping_team", self._route_to_web_scraping)
        workflow.add_node("pdf_processing_team", self._route_to_pdf_processing)
        workflow.add_node("api_extraction_team", self._route_to_api_extraction)
        workflow.add_node("normalization_pipeline", self._normalize_products)
        workflow.add_node("consolidation_engine", self._consolidate_products)
        workflow.add_node("quality_validator", self._validate_quality)
        workflow.add_node("human_reviewer", self._human_review_interrupt)
        workflow.add_node("database_writer", self._save_to_database)
        workflow.add_node("job_finalizer", self._finalize_job)
        
        # Set entry point
        workflow.set_entry_point("initialize_job")
        
        # Define the workflow edges
        workflow.add_edge("initialize_job", "source_detector")
        
        # Conditional routing from source detector
        workflow.add_conditional_edges(
            "source_detector",
            self._route_by_source_type,
            {
                "web_only": "web_scraping_team",
                "pdf_only": "pdf_processing_team",
                "api_only": "api_extraction_team",
                "mixed": "web_scraping_team",  # Start with web, then others
                "no_sources": "job_finalizer"
            }
        )
        
        # All extraction paths lead to normalization
        workflow.add_edge("web_scraping_team", "normalization_pipeline")
        workflow.add_edge("pdf_processing_team", "normalization_pipeline")
        workflow.add_edge("api_extraction_team", "normalization_pipeline")
        
        # Normalization to consolidation
        workflow.add_edge("normalization_pipeline", "consolidation_engine")
        
        # Consolidation to quality validation
        workflow.add_edge("consolidation_engine", "quality_validator")
        
        # Conditional routing from quality validator
        workflow.add_conditional_edges(
            "quality_validator",
            self._route_by_quality,
            {
                "approved": "database_writer",
                "needs_review": "human_reviewer",
                "retry_normalization": "normalization_pipeline",
                "failed": "job_finalizer"
            }
        )
        
        # Human reviewer to database writer (after approval)
        workflow.add_edge("human_reviewer", "database_writer")
        
        # Database writer to finalizer
        workflow.add_edge("database_writer", "job_finalizer")
        
        # Finalizer to END
        workflow.add_edge("job_finalizer", END)
        
        # Compile the workflow
        compiled_graph = workflow.compile(
            checkpointer=self.checkpointer,
            interrupt_before=["human_reviewer"] if self.checkpointer else []
        )
        
        self.logger.info("Main catalog extraction workflow compiled successfully")
        return compiled_graph
    
    # Node implementations
    
    async def _initialize_job(self, state: CatalogExtractionState) -> CatalogExtractionState:
        """Initialize the extraction job"""
        
        self.logger.info(f"Initializing job {state['job_id']} for tenant {state['tenant_id']}")
        
        # Add initialization message
        init_message = HumanMessage(
            content=f"Starting catalog extraction job for {len(state['sources'])} sources"
        )
        
        return {
            **state,
            "messages": [init_message],
            "current_step": "initialization",
            "status": ExtractionStatus.RUNNING,
            "started_at": datetime.utcnow(),
            "total_sources": len(state["sources"]),
            "estimated_completion": None  # Will be calculated by agents
        }
    
    async def _detect_source_types(self, state: CatalogExtractionState) -> CatalogExtractionState:
        """Analyze and categorize all sources"""
        
        self.logger.info("Detecting source types and planning extraction strategy")
        
        source_analysis = {
            "web_sources": [],
            "pdf_sources": [],
            "api_sources": [],
            "excel_sources": [],
            "total_sources": len(state["sources"])
        }
        
        # Categorize sources
        for source in state["sources"]:
            if source.type == SourceType.WEB:
                source_analysis["web_sources"].append(source)
            elif source.type == SourceType.PDF:
                source_analysis["pdf_sources"].append(source)
            elif source.type == SourceType.API:
                source_analysis["api_sources"].append(source)
            elif source.type == SourceType.EXCEL:
                source_analysis["excel_sources"].append(source)
        
        detection_message = AIMessage(
            content=f"Detected {len(source_analysis['web_sources'])} web sources, "
                   f"{len(source_analysis['pdf_sources'])} PDF sources, "
                   f"{len(source_analysis['api_sources'])} API sources"
        )
        
        return {
            **state,
            "messages": state["messages"] + [detection_message],
            "current_step": "source_detection",
            "checkpoint_data": source_analysis
        }
    
    def _route_by_source_type(self, state: CatalogExtractionState) -> str:
        """Determine routing based on source types"""
        
        source_types = set(source.type for source in state["sources"])
        
        if not source_types:
            return "no_sources"
        
        if len(source_types) > 1:
            return "mixed"
        
        source_type = next(iter(source_types))
        
        if source_type == SourceType.WEB:
            return "web_only"
        elif source_type == SourceType.PDF:
            return "pdf_only"
        elif source_type == SourceType.API:
            return "api_only"
        else:
            return "mixed"
    
    async def _route_to_web_scraping(self, state: CatalogExtractionState) -> CatalogExtractionState:
        """Route to web scraping subgraph"""
        
        # Get web scraping agent from registry
        web_agent = AgentRegistry.get_agent("web_scraper")
        
        if web_agent:
            self.logger.info("Routing to web scraping agent")
            return await web_agent.process(state)
        else:
            # Placeholder implementation
            self.logger.warning("Web scraping agent not found, using placeholder")
            return {
                **state,
                "current_step": "web_scraping_completed",
                "raw_products": [],  # Would be populated by real agent
                "messages": state["messages"] + [
                    AIMessage(content="Web scraping completed (placeholder)")
                ]
            }
    
    async def _route_to_pdf_processing(self, state: CatalogExtractionState) -> CatalogExtractionState:
        """Route to PDF processing subgraph"""
        
        # Get PDF processing agent from registry
        pdf_agent = AgentRegistry.get_agent("pdf_processor")
        
        if pdf_agent:
            self.logger.info("Routing to PDF processing agent")
            return await pdf_agent.process(state)
        else:
            # Placeholder implementation
            self.logger.warning("PDF processing agent not found, using placeholder")
            return {
                **state,
                "current_step": "pdf_processing_completed",
                "raw_products": [],  # Would be populated by real agent
                "messages": state["messages"] + [
                    AIMessage(content="PDF processing completed (placeholder)")
                ]
            }
    
    async def _route_to_api_extraction(self, state: CatalogExtractionState) -> CatalogExtractionState:
        """Route to API extraction subgraph"""
        
        self.logger.info("Processing API sources")
        
        # Placeholder for API extraction
        return {
            **state,
            "current_step": "api_extraction_completed",
            "raw_products": [],  # Would be populated by real agent
            "messages": state["messages"] + [
                AIMessage(content="API extraction completed (placeholder)")
            ]
        }
    
    async def _normalize_products(self, state: CatalogExtractionState) -> CatalogExtractionState:
        """Normalize products from all sources"""
        
        normalization_agent = AgentRegistry.get_agent("normalizer")
        
        if normalization_agent:
            self.logger.info("Routing to normalization agent")
            return await normalization_agent.process(state)
        else:
            # Placeholder implementation
            self.logger.warning("Normalization agent not found, using placeholder")
            return {
                **state,
                "current_step": "normalization_completed",
                "normalized_products": [],  # Would be populated by real agent
                "messages": state["messages"] + [
                    AIMessage(content="Product normalization completed (placeholder)")
                ]
            }
    
    async def _consolidate_products(self, state: CatalogExtractionState) -> CatalogExtractionState:
        """Consolidate and deduplicate products"""
        
        consolidation_agent = AgentRegistry.get_agent("consolidator")
        
        if consolidation_agent:
            self.logger.info("Routing to consolidation agent")
            return await consolidation_agent.process(state)
        else:
            # Placeholder implementation
            self.logger.warning("Consolidation agent not found, using placeholder")
            return {
                **state,
                "current_step": "consolidation_completed",
                "consolidated_products": state.get("normalized_products", []),
                "messages": state["messages"] + [
                    AIMessage(content="Product consolidation completed (placeholder)")
                ]
            }
    
    async def _validate_quality(self, state: CatalogExtractionState) -> CatalogExtractionState:
        """Validate overall quality of extracted data"""
        
        validator_agent = AgentRegistry.get_agent("validator")
        
        if validator_agent:
            self.logger.info("Routing to quality validator")
            return await validator_agent.process(state)
        else:
            # Placeholder validation
            products = state.get("consolidated_products", [])
            
            validation_results = {
                "total_products": len(products),
                "quality_score": 0.85,  # Placeholder
                "validation_passed": len(products) > 0
            }
            
            return {
                **state,
                "current_step": "quality_validation_completed",
                "validation_results": validation_results,
                "final_products": products,
                "messages": state["messages"] + [
                    AIMessage(content=f"Quality validation completed: {validation_results}")
                ]
            }
    
    def _route_by_quality(self, state: CatalogExtractionState) -> str:
        """Route based on quality validation results"""
        
        validation_results = state.get("validation_results", {})
        quality_score = validation_results.get("quality_score", 0.0)
        
        # Check if human review is required
        if should_require_human_review(state):
            return "needs_review"
        
        # Check if quality is acceptable
        if quality_score >= config.extraction.auto_approval_threshold:
            return "approved"
        elif quality_score >= config.extraction.min_confidence:
            return "needs_review"
        else:
            # Quality too low, try retry or fail
            retry_count = state.get("retry_count", 0)
            if retry_count < 2:
                return "retry_normalization"
            else:
                return "failed"
    
    async def _human_review_interrupt(self, state: CatalogExtractionState) -> CatalogExtractionState:
        """Handle human review requirement"""
        
        self.logger.info("Job requires human review - creating interrupt")
        
        # Prepare items for human review
        review_items = []
        products = state.get("consolidated_products", [])
        
        # Select products that need review (low confidence, errors, etc.)
        for i, product in enumerate(products[:10]):  # Limit to first 10 for review
            if hasattr(product, 'extraction_confidence') and product.extraction_confidence < 0.8:
                review_items.append({
                    "index": i,
                    "product": product.__dict__ if hasattr(product, '__dict__') else product,
                    "issues": getattr(product, 'validation_errors', [])
                })
        
        return {
            **state,
            "current_step": "awaiting_human_review",
            "requires_human_approval": True,
            "human_review_items": review_items,
            "status": ExtractionStatus.REQUIRES_HUMAN_REVIEW,
            "messages": state["messages"] + [
                HumanMessage(content=f"Human review required for {len(review_items)} items")
            ]
        }
    
    async def _save_to_database(self, state: CatalogExtractionState) -> CatalogExtractionState:
        """Save final products to database"""
        
        self.logger.info("Saving products to database")
        
        products = state.get("final_products", [])
        tenant_id = state["tenant_id"]
        
        # Placeholder for database saving
        # In real implementation, this would use the database layer
        
        save_results = {
            "products_saved": len(products),
            "tenant_id": tenant_id,
            "saved_at": datetime.utcnow().isoformat()
        }
        
        return {
            **state,
            "current_step": "database_save_completed",
            "products_processed": len(products),
            "messages": state["messages"] + [
                AIMessage(content=f"Saved {len(products)} products to database")
            ],
            "checkpoint_data": {**state.get("checkpoint_data", {}), **save_results}
        }
    
    async def _finalize_job(self, state: CatalogExtractionState) -> CatalogExtractionState:
        """Finalize the extraction job"""
        
        self.logger.info(f"Finalizing job {state['job_id']}")
        
        # Determine final status
        final_status = ExtractionStatus.COMPLETED
        if state["error_count"] > state.get("max_errors", 50):
            final_status = ExtractionStatus.FAILED
        
        completion_summary = {
            "job_id": state["job_id"],
            "tenant_id": state["tenant_id"],
            "status": final_status,
            "sources_processed": state.get("completed_sources", 0),
            "total_sources": state["total_sources"],
            "products_found": len(state.get("raw_products", [])),
            "products_processed": len(state.get("final_products", [])),
            "errors": state["error_count"],
            "warnings": len(state["warnings"]),
            "started_at": state.get("started_at"),
            "completed_at": datetime.utcnow()
        }
        
        return {
            **state,
            "current_step": "completed",
            "status": final_status,
            "completed_sources": state["total_sources"],
            "messages": state["messages"] + [
                AIMessage(content=f"Job completed: {completion_summary}")
            ],
            "checkpoint_data": completion_summary
        }
    
    # Utility methods
    
    async def start_extraction_job(
        self,
        tenant_id: str,
        sources: List[Any],
        extraction_config: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Start a new catalog extraction job
        
        Args:
            tenant_id: ID of the tenant
            sources: List of extraction sources  
            extraction_config: Optional configuration overrides
            
        Returns:
            Job information including job_id and initial status
        """
        
        # Create initial state
        initial_state = create_initial_state(
            tenant_id=tenant_id,
            sources=sources,
            extraction_config=extraction_config or {}
        )
        
        # Build and compile the graph
        graph = self.build_main_graph()
        
        # Execute the workflow
        job_info = {
            "job_id": initial_state["job_id"],
            "tenant_id": tenant_id,
            "status": "started",
            "sources_count": len(sources),
            "started_at": datetime.utcnow().isoformat()
        }
        
        self.logger.info(f"Started extraction job: {job_info}")
        
        # In a real implementation, this would run asynchronously
        # For now, we'll just return the job info
        return job_info
    
    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Get status of a running job"""
        
        # Placeholder implementation
        # In real system, this would query the checkpointer or job queue
        
        return {
            "job_id": job_id,
            "status": "unknown",
            "message": "Job status tracking not yet implemented"
        }