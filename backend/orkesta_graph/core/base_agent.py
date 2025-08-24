"""
Base agent class for Orkesta multi-agent system
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Union
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI, AzureChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
import asyncio
import logging
import time
from datetime import datetime
import json

from .config import config
from .state import CatalogExtractionState, AgentType


class LLMClientManager:
    """Manages multiple LLM clients with fallback logic"""
    
    def __init__(self):
        self.primary_client = None
        self.fallback_client = None
        self._setup_clients()
    
    def _setup_clients(self):
        """Initialize LLM clients based on configuration"""
        
        # Primary: Groq
        if config.llm.groq_api_key:
            self.primary_client = ChatGroq(
                api_key=config.llm.groq_api_key,
                model=config.llm.groq_model,
                temperature=config.llm.groq_temperature,
                max_tokens=config.llm.groq_max_tokens,
            )
        
        # Fallback: Azure OpenAI
        if config.llm.azure_openai_api_key and config.llm.azure_openai_endpoint:
            self.fallback_client = AzureChatOpenAI(
                api_key=config.llm.azure_openai_api_key,
                azure_endpoint=config.llm.azure_openai_endpoint,
                azure_deployment=config.llm.azure_openai_deployment,
                api_version="2024-02-01",
                temperature=0.1,
            )
        # Alternative fallback: Standard OpenAI
        elif config.llm.openai_api_key:
            self.fallback_client = ChatOpenAI(
                api_key=config.llm.openai_api_key,
                model="gpt-4o-mini",
                temperature=0.1,
            )
    
    async def invoke(self, messages: List[BaseMessage], **kwargs) -> AIMessage:
        """Invoke LLM with fallback logic"""
        
        # Try primary client first
        if self.primary_client:
            try:
                response = await self.primary_client.ainvoke(messages, **kwargs)
                return response
            except Exception as e:
                logging.warning(f"Primary LLM failed: {e}. Falling back to secondary.")
        
        # Fallback to secondary client
        if self.fallback_client:
            try:
                response = await self.fallback_client.ainvoke(messages, **kwargs)
                return response
            except Exception as e:
                logging.error(f"Fallback LLM also failed: {e}")
                raise e
        
        raise RuntimeError("No LLM clients available")
    
    async def structured_invoke(
        self, 
        messages: List[BaseMessage],
        response_format: str = "json",
        **kwargs
    ) -> Dict[str, Any]:
        """Invoke LLM expecting structured output"""
        
        # Add instructions for structured output
        system_msg = SystemMessage(content=f"""
        You must respond with valid {response_format.upper()} only. 
        Do not include any additional text or explanations.
        """)
        
        structured_messages = [system_msg] + list(messages)
        
        response = await self.invoke(structured_messages, **kwargs)
        
        try:
            if response_format.lower() == "json":
                return json.loads(response.content)
            else:
                return {"content": response.content}
        except json.JSONDecodeError as e:
            logging.error(f"Failed to parse LLM response as JSON: {response.content}")
            raise ValueError(f"Invalid JSON response from LLM: {e}")


class BaseAgent(ABC):
    """
    Base class for all Orkesta agents
    Provides common functionality for LLM interaction, error handling, and metrics
    """
    
    def __init__(self, agent_type: AgentType, name: Optional[str] = None):
        self.agent_type = agent_type
        self.name = name or agent_type.value
        
        # LLM client
        self.llm = LLMClientManager()
        
        # Metrics and monitoring
        self.metrics = {
            "messages_processed": 0,
            "successful_operations": 0,
            "failed_operations": 0,
            "average_processing_time": 0.0,
            "last_operation_time": None
        }
        
        # Agent-specific configuration
        self.config = self._load_agent_config()
        
        # Logger
        self.logger = logging.getLogger(f"orkesta.agent.{self.name}")
    
    def _load_agent_config(self) -> Dict[str, Any]:
        """Load agent-specific configuration"""
        # This could be loaded from database or config files
        return {
            "max_retries": 3,
            "timeout_seconds": 300,
            "batch_size": 100,
        }
    
    @abstractmethod
    async def process(
        self, 
        state: CatalogExtractionState,
        **kwargs
    ) -> CatalogExtractionState:
        """
        Main processing method that each agent must implement
        
        Args:
            state: Current state of the extraction workflow
            **kwargs: Additional parameters
            
        Returns:
            Updated state
        """
        pass
    
    async def _track_operation(self, operation_name: str, func, *args, **kwargs):
        """Track operation metrics"""
        start_time = time.time()
        
        try:
            result = await func(*args, **kwargs)
            self.metrics["successful_operations"] += 1
            return result
        
        except Exception as e:
            self.metrics["failed_operations"] += 1
            self.logger.error(f"Operation {operation_name} failed: {e}")
            raise
        
        finally:
            end_time = time.time()
            duration = end_time - start_time
            
            # Update metrics
            total_ops = self.metrics["successful_operations"] + self.metrics["failed_operations"]
            if total_ops > 0:
                current_avg = self.metrics["average_processing_time"]
                self.metrics["average_processing_time"] = (
                    (current_avg * (total_ops - 1) + duration) / total_ops
                )
            
            self.metrics["last_operation_time"] = datetime.utcnow()
            self.metrics["messages_processed"] += 1
    
    async def llm_analyze(
        self, 
        prompt: str, 
        context: Optional[Dict[str, Any]] = None,
        response_format: str = "text"
    ) -> Union[str, Dict[str, Any]]:
        """
        Analyze data using LLM
        
        Args:
            prompt: The prompt to send to LLM
            context: Additional context data
            response_format: "text" or "json"
            
        Returns:
            LLM response as text or parsed JSON
        """
        
        messages = [HumanMessage(content=prompt)]
        
        if context:
            context_str = f"Context: {json.dumps(context, indent=2)}\n\n"
            messages[0].content = context_str + messages[0].content
        
        if response_format == "json":
            return await self.llm.structured_invoke(messages, response_format="json")
        else:
            response = await self.llm.invoke(messages)
            return response.content
    
    async def validate_data(
        self, 
        data: List[Dict[str, Any]], 
        validation_rules: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate extracted data using LLM
        
        Args:
            data: List of data items to validate
            validation_rules: Rules for validation
            
        Returns:
            Validation results
        """
        
        validation_prompt = f"""
        Validate the following extracted data according to these rules:
        
        Validation Rules:
        {json.dumps(validation_rules, indent=2)}
        
        Data to validate:
        {json.dumps(data[:5], indent=2)}  # Limit to first 5 items for context
        
        For each item, check:
        1. Required fields are present and not empty
        2. Data types are correct
        3. Values are within expected ranges
        4. No obviously incorrect or corrupted data
        
        Respond with JSON:
        {{
            "validation_summary": {{
                "total_items": {len(data)},
                "valid_items": <count>,
                "invalid_items": <count>,
                "validation_errors": ["error1", "error2"]
            }},
            "item_validations": [
                {{
                    "item_index": 0,
                    "is_valid": true,
                    "errors": [],
                    "confidence": 0.95
                }}
            ]
        }}
        """
        
        return await self.llm_analyze(validation_prompt, response_format="json")
    
    async def extract_with_llm(
        self, 
        raw_text: str, 
        extraction_schema: Dict[str, Any],
        examples: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        """
        Extract structured data from raw text using LLM
        
        Args:
            raw_text: Raw text to extract from
            extraction_schema: Schema defining what to extract
            examples: Example extractions to guide the LLM
            
        Returns:
            List of extracted items
        """
        
        examples_str = ""
        if examples:
            examples_str = f"""
            Examples of correct extractions:
            {json.dumps(examples, indent=2)}
            """
        
        extraction_prompt = f"""
        Extract structured data from the following text according to the schema:
        
        Schema:
        {json.dumps(extraction_schema, indent=2)}
        
        {examples_str}
        
        Text to extract from:
        {raw_text[:3000]}  # Limit text length
        
        Extract all items that match the schema. Return a JSON array:
        [
            {{"field1": "value1", "field2": "value2", "confidence": 0.95}},
            {{"field1": "value1", "field2": "value2", "confidence": 0.90}}
        ]
        
        If no items are found, return an empty array [].
        """
        
        result = await self.llm_analyze(extraction_prompt, response_format="json")
        return result if isinstance(result, list) else []
    
    def update_state(
        self, 
        state: CatalogExtractionState,
        updates: Dict[str, Any]
    ) -> CatalogExtractionState:
        """
        Update state with new data
        
        Args:
            state: Current state
            updates: Dictionary of updates to apply
            
        Returns:
            Updated state
        """
        
        # Create a new state dict with updates
        new_state = dict(state)
        new_state.update(updates)
        
        # Update current agent and step
        new_state["current_agent"] = self.agent_type
        new_state["last_checkpoint_at"] = datetime.utcnow()
        
        return new_state
    
    def add_error(
        self, 
        state: CatalogExtractionState, 
        error_message: str, 
        error_data: Optional[Dict[str, Any]] = None
    ) -> CatalogExtractionState:
        """Add an error to the state"""
        
        error_entry = {
            "agent": self.name,
            "message": error_message,
            "timestamp": datetime.utcnow().isoformat(),
            "data": error_data or {}
        }
        
        new_errors = list(state["errors"])
        new_errors.append(error_entry)
        
        return self.update_state(state, {
            "errors": new_errors,
            "error_count": state["error_count"] + 1
        })
    
    def add_warning(
        self, 
        state: CatalogExtractionState, 
        warning_message: str
    ) -> CatalogExtractionState:
        """Add a warning to the state"""
        
        new_warnings = list(state["warnings"])
        new_warnings.append(f"[{self.name}] {warning_message}")
        
        return self.update_state(state, {
            "warnings": new_warnings
        })
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get agent performance metrics"""
        return {
            "agent_name": self.name,
            "agent_type": self.agent_type.value,
            **self.metrics,
            "config": self.config
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Check agent health status"""
        
        health_status = {
            "agent": self.name,
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": self.get_metrics()
        }
        
        # Test LLM connectivity
        try:
            test_response = await self.llm.invoke([
                HumanMessage(content="Health check. Respond with 'OK'.")
            ])
            health_status["llm_status"] = "connected"
        except Exception as e:
            health_status["status"] = "degraded"
            health_status["llm_status"] = f"error: {str(e)}"
        
        return health_status


class AgentRegistry:
    """Registry for managing agent instances"""
    
    _agents: Dict[str, BaseAgent] = {}
    
    @classmethod
    def register(cls, agent: BaseAgent) -> None:
        """Register an agent instance"""
        cls._agents[agent.name] = agent
    
    @classmethod
    def get_agent(cls, name: str) -> Optional[BaseAgent]:
        """Get an agent by name"""
        return cls._agents.get(name)
    
    @classmethod
    def get_all_agents(cls) -> Dict[str, BaseAgent]:
        """Get all registered agents"""
        return cls._agents.copy()
    
    @classmethod
    async def health_check_all(cls) -> Dict[str, Dict[str, Any]]:
        """Run health checks on all agents"""
        results = {}
        
        for name, agent in cls._agents.items():
            try:
                results[name] = await agent.health_check()
            except Exception as e:
                results[name] = {
                    "agent": name,
                    "status": "error",
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                }
        
        return results