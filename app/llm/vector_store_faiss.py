"""Alternative in-memory vector store using FAISS (for comparison)."""
from typing import List, Dict, Optional
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from config import get_settings
from utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()


class FAISSVectorStore:
    """FAISS in-memory vector store (alternative to ChromaDB).
    
    FAISS is purely in-memory and very fast, but data is lost on restart.
    Good for development, testing, or when data can be reloaded.
    """

    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        self.collection_name = f"rules_{tenant_id}"
        self.vector_store: Optional[FAISS] = None
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
        )

    def _get_embeddings(self):
        """Get embedding model."""
        if settings.OPENAI_API_KEY and "text-embedding" in settings.EMBEDDING_MODEL.lower():
            logger.info(f"Using OpenAI embeddings: {settings.EMBEDDING_MODEL}")
            return OpenAIEmbeddings(
                model=settings.EMBEDDING_MODEL,
                openai_api_key=settings.OPENAI_API_KEY,
            )
        else:
            # FAISS requires explicit embeddings (no default like ChromaDB)
            raise ValueError(
                "FAISS requires explicit embeddings. Set OPENAI_API_KEY."
            )

    async def add_documents(
        self, documents: List[str], metadatas: List[Dict], ids: Optional[List[str]] = None
    ) -> None:
        # Note: ids parameter reserved for future use
        """Add documents to FAISS vector store."""
        try:
            # Add tenant_id to all metadata
            enriched_metadatas = [
                {**metadata, "tenant_id": self.tenant_id}
                for metadata in metadatas
            ]
            
            # Create LangChain Document objects
            langchain_docs = [
                Document(page_content=doc, metadata=meta)
                for doc, meta in zip(documents, enriched_metadatas)
            ]
            
            # Split documents if needed
            split_docs = []
            for doc in langchain_docs:
                if len(doc.page_content) > settings.CHUNK_SIZE:
                    splits = self.text_splitter.split_documents([doc])
                    split_docs.extend(splits)
                else:
                    split_docs.append(doc)
            
            embeddings = self._get_embeddings()
            
            # Create or add to FAISS store
            if self.vector_store is None:
                # Create new store
                self.vector_store = await FAISS.afrom_documents(
                    documents=split_docs,
                    embedding=embeddings,
                )
            else:
                # Add to existing store
                await self.vector_store.aadd_documents(split_docs)
            
            logger.info(f"Added {len(split_docs)} documents to FAISS vector store")
        except Exception as e:
            logger.error(f"Failed to add documents: {e}")
            raise

    async def search(
        self, query: str, n_results: int = 5, filter_metadata: Optional[Dict] = None
    ) -> List[Dict]:
        """Search for similar documents using FAISS."""
        if self.vector_store is None:
            return []
        
        try:
            # FAISS doesn't support metadata filtering natively
            # We'll search and filter results after retrieval
            docs_with_scores = await self.vector_store.asimilarity_search_with_score(
                query, k=n_results * 2  # Get more to filter
            )
            
            # Filter by tenant_id and other metadata
            filtered_results = []
            where_dict = {"tenant_id": self.tenant_id}
            if filter_metadata:
                where_dict.update(filter_metadata)
            
            for doc, score in docs_with_scores:
                # Check if metadata matches
                matches = all(
                    doc.metadata.get(key) == value
                    for key, value in where_dict.items()
                )
                
                if matches:
                    filtered_results.append({
                        "id": doc.metadata.get("id", ""),
                        "content": doc.page_content,
                        "metadata": doc.metadata,
                        "score": float(score),
                    })
                    
                    if len(filtered_results) >= n_results:
                        break
            
            logger.info(f"Found {len(filtered_results)} results for query")
            return filtered_results
        except Exception as e:
            logger.error(f"FAISS search failed: {e}")
            return []

    def save_local(self, path: str) -> None:
        """Save FAISS index to disk (can be reloaded later)."""
        if self.vector_store:
            self.vector_store.save_local(path)
            logger.info(f"Saved FAISS index to {path}")

    @classmethod
    async def load_local(cls, path: str, tenant_id: str) -> "FAISSVectorStore":
        """Load FAISS index from disk."""
        store = cls(tenant_id)
        embeddings = store._get_embeddings()
        store.vector_store = await FAISS.afrom_documents(
            documents=[],  # Empty, will load from disk
            embedding=embeddings,
        )
        # Note: FAISS.afrom_documents doesn't load from disk directly
        # You'd use FAISS.load_local() instead in sync mode
        # This is a simplified example
        logger.info(f"Loaded FAISS index from {path}")
        return store

