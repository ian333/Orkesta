"""
Configuration management for Orkesta Graph system
"""
from typing import Dict, Any, List, Optional
from pydantic import BaseSettings, Field
from pydantic_settings import BaseSettings
import os
from pathlib import Path


class DatabaseConfig(BaseSettings):
    """Database configuration"""
    
    # PostgreSQL settings
    host: str = Field(default="localhost", env="POSTGRES_HOST")
    port: int = Field(default=5432, env="POSTGRES_PORT")
    database: str = Field(default="orkesta", env="POSTGRES_DB")
    username: str = Field(default="orkesta", env="POSTGRES_USER")
    password: str = Field(default="orkesta_password_2024", env="POSTGRES_PASSWORD")
    
    # Connection pooling
    pool_size: int = Field(default=20, env="DB_POOL_SIZE")
    max_overflow: int = Field(default=30, env="DB_MAX_OVERFLOW")
    pool_timeout: int = Field(default=30, env="DB_POOL_TIMEOUT")
    
    @property
    def url(self) -> str:
        """Get database URL"""
        return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"
    
    @property
    def async_url(self) -> str:
        """Get async database URL"""
        return f"postgresql+asyncpg://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"


class RedisConfig(BaseSettings):
    """Redis configuration for caching and message queuing"""
    
    host: str = Field(default="localhost", env="REDIS_HOST")
    port: int = Field(default=6379, env="REDIS_PORT")
    database: int = Field(default=0, env="REDIS_DB")
    password: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    
    @property
    def url(self) -> str:
        """Get Redis URL"""
        if self.password:
            return f"redis://:{self.password}@{self.host}:{self.port}/{self.database}"
        return f"redis://{self.host}:{self.port}/{self.database}"


class LLMConfig(BaseSettings):
    """LLM configuration for various providers"""
    
    # Primary LLM (Groq)
    groq_api_key: Optional[str] = Field(default=None, env="GROQ_API_KEY")
    groq_model: str = Field(default="llama-3.1-70b-versatile", env="GROQ_MODEL")
    groq_temperature: float = Field(default=0.1, env="GROQ_TEMPERATURE")
    groq_max_tokens: int = Field(default=4000, env="GROQ_MAX_TOKENS")
    
    # Fallback LLM (Azure OpenAI)
    azure_openai_api_key: Optional[str] = Field(default=None, env="AZURE_OPENAI_API_KEY")
    azure_openai_endpoint: Optional[str] = Field(default=None, env="AZURE_OPENAI_ENDPOINT")
    azure_openai_deployment: str = Field(default="gpt-4", env="AZURE_OPENAI_DEPLOYMENT")
    
    # OpenAI for embeddings
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    embedding_model: str = Field(default="text-embedding-3-small", env="EMBEDDING_MODEL")
    embedding_dimensions: int = Field(default=1536, env="EMBEDDING_DIMENSIONS")
    
    # Rate limiting
    max_requests_per_minute: int = Field(default=60, env="LLM_MAX_REQUESTS_PER_MINUTE")
    max_concurrent_requests: int = Field(default=10, env="LLM_MAX_CONCURRENT")


class ScrapingConfig(BaseSettings):
    """Web scraping configuration"""
    
    # Selenium settings
    headless: bool = Field(default=True, env="SELENIUM_HEADLESS")
    implicit_wait: int = Field(default=10, env="SELENIUM_IMPLICIT_WAIT")
    page_load_timeout: int = Field(default=30, env="SELENIUM_PAGE_LOAD_TIMEOUT")
    
    # Anti-detection
    use_stealth: bool = Field(default=True, env="USE_STEALTH")
    rotate_user_agents: bool = Field(default=True, env="ROTATE_USER_AGENTS")
    use_proxy_rotation: bool = Field(default=False, env="USE_PROXY_ROTATION")
    
    # Rate limiting
    delay_between_requests: float = Field(default=2.0, env="SCRAPING_DELAY")
    max_concurrent_scrapers: int = Field(default=3, env="MAX_CONCURRENT_SCRAPERS")
    
    # Retry settings
    max_retries: int = Field(default=3, env="SCRAPING_MAX_RETRIES")
    retry_delay: float = Field(default=5.0, env="SCRAPING_RETRY_DELAY")


class OCRConfig(BaseSettings):
    """OCR and document processing configuration"""
    
    # Tesseract settings
    tesseract_cmd: str = Field(default="tesseract", env="TESSERACT_CMD")
    tesseract_languages: List[str] = Field(default=["spa", "eng"], env="TESSERACT_LANGUAGES")
    
    # OCR quality settings
    dpi: int = Field(default=300, env="OCR_DPI")
    confidence_threshold: float = Field(default=0.8, env="OCR_CONFIDENCE_THRESHOLD")
    
    # PDF processing
    max_pdf_pages: int = Field(default=1000, env="MAX_PDF_PAGES")
    pdf_timeout: int = Field(default=300, env="PDF_TIMEOUT")  # 5 minutes
    
    # Image preprocessing
    enhance_images: bool = Field(default=True, env="ENHANCE_IMAGES")
    denoise: bool = Field(default=True, env="DENOISE_IMAGES")


class ExtractionConfig(BaseSettings):
    """Catalog extraction configuration"""
    
    # Quality thresholds
    min_confidence: float = Field(default=0.85, env="MIN_EXTRACTION_CONFIDENCE")
    auto_approval_threshold: float = Field(default=0.95, env="AUTO_APPROVAL_THRESHOLD")
    human_review_threshold: float = Field(default=0.7, env="HUMAN_REVIEW_THRESHOLD")
    
    # Batch processing
    batch_size: int = Field(default=100, env="EXTRACTION_BATCH_SIZE")
    max_concurrent_extractions: int = Field(default=5, env="MAX_CONCURRENT_EXTRACTIONS")
    
    # Pattern learning
    pattern_learning_enabled: bool = Field(default=True, env="PATTERN_LEARNING_ENABLED")
    min_pattern_success_rate: float = Field(default=0.8, env="MIN_PATTERN_SUCCESS_RATE")
    max_patterns_per_domain: int = Field(default=20, env="MAX_PATTERNS_PER_DOMAIN")
    
    # Deduplication
    fuzzy_match_threshold: float = Field(default=0.85, env="FUZZY_MATCH_THRESHOLD")
    enable_auto_deduplication: bool = Field(default=True, env="ENABLE_AUTO_DEDUPLICATION")


class OrkestaConfig(BaseSettings):
    """Main application configuration"""
    
    # Environment
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=True, env="DEBUG")
    
    # API settings
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")
    
    # Security
    secret_key: str = Field(default="orkesta-secret-key-change-in-production", env="SECRET_KEY")
    
    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(default="json", env="LOG_FORMAT")
    
    # Component configurations
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    redis: RedisConfig = Field(default_factory=RedisConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    scraping: ScrapingConfig = Field(default_factory=ScrapingConfig)
    ocr: OCRConfig = Field(default_factory=OCRConfig)
    extraction: ExtractionConfig = Field(default_factory=ExtractionConfig)
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global configuration instance
config = OrkestaConfig()


def get_tenant_config(tenant_id: str) -> Dict[str, Any]:
    """
    Get tenant-specific configuration overrides
    This would typically come from the database, but for now return defaults
    """
    tenant_configs = {
        "avaz_automotive": {
            "extraction": {
                "min_confidence": 0.90,
                "auto_approval_threshold": 0.95,
                "batch_size": 200
            },
            "scraping": {
                "max_concurrent_scrapers": 5,
                "delay_between_requests": 1.0
            }
        },
        "ferreteria_central": {
            "extraction": {
                "min_confidence": 0.85,
                "auto_approval_threshold": 0.90,
                "batch_size": 100
            },
            "scraping": {
                "max_concurrent_scrapers": 2,
                "delay_between_requests": 3.0
            }
        }
    }
    
    return tenant_configs.get(tenant_id, {})


def validate_config() -> bool:
    """Validate that all required configuration is present"""
    
    errors = []
    
    # Check required API keys
    if not config.llm.groq_api_key and not config.llm.azure_openai_api_key:
        errors.append("At least one LLM API key (GROQ or Azure OpenAI) must be configured")
    
    if not config.llm.openai_api_key:
        errors.append("OpenAI API key is required for embeddings")
    
    # Check database connectivity (would be implemented with actual DB connection)
    # if not test_database_connection():
    #     errors.append("Cannot connect to PostgreSQL database")
    
    if errors:
        print("Configuration errors:")
        for error in errors:
            print(f"  - {error}")
        return False
    
    return True


if __name__ == "__main__":
    # Validate configuration when run directly
    if validate_config():
        print("✅ Configuration is valid")
        print(f"Database URL: {config.database.url}")
        print(f"Redis URL: {config.redis.url}")
        print(f"Primary LLM: {'Groq' if config.llm.groq_api_key else 'Azure OpenAI'}")
    else:
        print("❌ Configuration validation failed")
        exit(1)