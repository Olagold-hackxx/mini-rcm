"""Configuration management for the application."""
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "Medical Claims Validator"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "postgresql://user:pass@localhost:5432/claims_db"
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20

    # Authentication
    SECRET_KEY: str  # Required - must be set in environment
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 720  # 12 hours (720 minutes)

    # LLM Configuration
    OPENAI_API_KEY: str = ""  # Required for LLM features
    LLM_MODEL: str = "gpt-4o-mini"  # Default OpenAI model
    LLM_MAX_TOKENS: int = 2000
    LLM_TEMPERATURE: float = 0.0

    # RAG Configuration
    USE_RAG: bool = True
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    VECTOR_STORE_PATH: str = "./vector_store/chroma_db"
    VECTOR_STORE_MODE: str = "persistent"  # "persistent" or "in_memory"
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50
    TOP_K_RETRIEVAL: int = 30  # Increased to get comprehensive rule coverage

    # LangChain
    USE_LANGCHAIN: bool = True

    # Caching
    ENABLE_LLM_CACHE: bool = True
    CACHE_TTL_SECONDS: int = 3600

    # File Upload
    MAX_UPLOAD_SIZE_MB: int = 50
    ALLOWED_EXTENSIONS: List[str] = [".csv", ".xlsx", ".xls"]

    # Multi-tenant
    DEFAULT_TENANT: str = "default"

    # Performance
    BATCH_SIZE: int = 100
    MAX_WORKERS: int = 4

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()

