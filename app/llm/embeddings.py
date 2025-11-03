"""Embedding generation using LangChain."""
from typing import List, Optional
from langchain_openai import OpenAIEmbeddings
from config import get_settings
from utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()


class EmbeddingService:
    """Service for generating embeddings using LangChain."""

    def __init__(self):
        self.model = settings.EMBEDDING_MODEL
        self.use_openai = settings.OPENAI_API_KEY and "text-embedding" in self.model.lower()
        self.embeddings = self._initialize_embeddings()

    def _initialize_embeddings(self):
        """Initialize LangChain embedding model."""
        if self.use_openai:
            logger.info(f"Initialized OpenAI embeddings: {self.model}")
            return OpenAIEmbeddings(
                model=self.model,
                openai_api_key=settings.OPENAI_API_KEY,
            )
        else:
            # Use ChromaDB default embeddings via LangChain interface
            logger.info("Using ChromaDB default embeddings")
            from chromadb.utils import embedding_functions
            default_ef = embedding_functions.DefaultEmbeddingFunction()
            
            # Create LangChain-compatible wrapper
            from langchain_core.embeddings import Embeddings
            
            class ChromaDefaultEmbeddings(Embeddings):
                """Wrapper for ChromaDB default embeddings."""
                
                def embed_documents(self, texts: List[str]) -> List[List[float]]:
                    """Embed multiple documents."""
                    return default_ef(texts)
                
                def embed_query(self, text: str) -> List[float]:
                    """Embed a single query."""
                    return default_ef([text])[0]
            
            return ChromaDefaultEmbeddings()

    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of texts using LangChain.
        
        Args:
            texts: List of text strings
            
        Returns:
            List of embedding vectors
        """
        try:
            if self.use_openai:
                # Use async method if available
                embeddings = await self.embeddings.aembed_documents(texts)
            else:
                # Sync method for ChromaDB default
                embeddings = self.embeddings.embed_documents(texts)
            
            logger.info(f"Generated {len(embeddings)} embeddings")
            return embeddings
        except Exception as e:
            logger.error(f"Failed to generate embeddings: {e}")
            raise

    async def generate_query_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single query."""
        try:
            if self.use_openai:
                embedding = await self.embeddings.aembed_query(text)
            else:
                embedding = self.embeddings.embed_query(text)
            
            return embedding
        except Exception as e:
            logger.error(f"Failed to generate query embedding: {e}")
            raise
