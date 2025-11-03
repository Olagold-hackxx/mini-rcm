"""Vector store implementation using LangChain ChromaDB."""
import os
import asyncio
from typing import List, Dict, Optional
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from config import get_settings
from utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()


class VectorStore:
    """LangChain ChromaDB vector store for rule document embeddings.
    
    Supports both persistent and in-memory modes.
    """

    def __init__(self, tenant_id: str, in_memory: Optional[bool] = None):
        """
        Initialize vector store.
        
        Args:
            tenant_id: Tenant identifier
            in_memory: Force in-memory mode (overrides config). 
                       None uses VECTOR_STORE_MODE from config
        """
        self.tenant_id = tenant_id
        self.collection_name = f"rules_{tenant_id}"
        
        # Determine if in-memory mode
        if in_memory is None:
            self.in_memory = settings.VECTOR_STORE_MODE.lower() == "in_memory"
        else:
            self.in_memory = in_memory
        
        self.vector_store = self._initialize_vector_store()
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
        )

    def _initialize_vector_store(self) -> Chroma:
        """Initialize LangChain ChromaDB vector store."""
        # Initialize embeddings
        embeddings = self._get_embeddings()
        
        if self.in_memory:
            # In-memory mode: no persistence
            vector_store = Chroma(
                collection_name=self.collection_name,
                embedding_function=embeddings,
                # No persist_directory = in-memory
            )
            logger.info(
                f"Initialized in-memory LangChain ChromaDB, "
                f"collection: {self.collection_name}"
            )
        else:
            # Persistent mode
            persist_directory = settings.VECTOR_STORE_PATH
            os.makedirs(persist_directory, exist_ok=True)
            
            # Check if collection exists and has incompatible embeddings
            vector_store = self._initialize_with_dimension_check(
                embeddings, persist_directory
            )
            
            logger.info(
                f"Initialized persistent LangChain ChromaDB at {persist_directory}, "
                f"collection: {self.collection_name}"
            )
        
        return vector_store
    
    def _initialize_with_dimension_check(
        self, embeddings, persist_directory: str
    ) -> Chroma:
        """
        Initialize ChromaDB with dimension checking and auto-recovery.
        
        If an existing collection has incompatible embedding dimensions,
        it will be deleted and recreated.
        """
        # Get expected embedding dimension
        test_embedding = embeddings.embed_query("test")
        expected_dim = len(test_embedding)
        
        try:
            # Try to create/get collection with new embeddings
            vector_store = Chroma(
                collection_name=self.collection_name,
                embedding_function=embeddings,
                persist_directory=persist_directory,
            )
            
            # Try to verify the collection is compatible
            # by attempting a simple operation
            try:
                _ = vector_store._collection.count()
                logger.info(
                    f"Collection '{self.collection_name}' exists with compatible embeddings"
                )
            except Exception as check_error:
                # If we get a dimension mismatch error, handle it
                error_str = str(check_error).lower()
                if "dimension" in error_str or "invalidargument" in error_str:
                    raise  # Re-raise to outer handler
                # Other errors are fine, collection might be empty
                
            return vector_store
            
        except Exception as e:
            # Check if it's a dimension mismatch error
            error_str = str(e).lower()
            error_type = str(type(e).__name__)
            
            if "dimension" in error_str or "InvalidArgument" in error_type:
                logger.warning(
                    f"Embedding dimension mismatch detected in collection '{self.collection_name}'. "
                    f"Expected {expected_dim} dimensions (OpenAI), but collection was created with "
                    "different embeddings (likely ChromaDB default with 384 dimensions)."
                )
                logger.info("Deleting incompatible collection and recreating with OpenAI embeddings...")
                
                # Delete the incompatible collection
                self._delete_collection(persist_directory)
                
                # Recreate with correct embeddings
                vector_store = Chroma(
                    collection_name=self.collection_name,
                    embedding_function=embeddings,
                    persist_directory=persist_directory,
                )
                logger.info(f"Successfully recreated collection with {expected_dim}-dimensional OpenAI embeddings")
                return vector_store
            else:
                # Some other error, re-raise
                raise
    
    def _delete_collection(self, persist_directory: str) -> None:
        """Delete an existing ChromaDB collection."""
        try:
            import chromadb
            
            # Get ChromaDB client
            client = chromadb.PersistentClient(path=persist_directory)
            
            # Try to delete the collection
            try:
                client.delete_collection(name=self.collection_name)
                logger.info(f"Deleted collection: {self.collection_name}")
            except Exception as delete_error:
                # Collection might not exist or already deleted
                logger.debug(f"Collection deletion note: {delete_error}")
                
        except Exception as e:
            logger.warning(f"Could not cleanly delete collection via API: {e}")
            # Fallback: try to delete the directory directly
            try:
                import shutil
                # ChromaDB stores collections in subdirectories
                # The exact path structure may vary, so try multiple locations
                possible_paths = [
                    os.path.join(persist_directory, self.collection_name),
                    os.path.join(persist_directory, "chroma.sqlite3"),
                ]
                
                for path in possible_paths:
                    if os.path.exists(path):
                        if os.path.isdir(path):
                            shutil.rmtree(path)
                        else:
                            os.remove(path)
                        logger.info(f"Removed: {path}")
                        
            except Exception as cleanup_error:
                logger.error(f"Failed to cleanup collection: {cleanup_error}")
                # Continue anyway - ChromaDB may handle it on next initialization

    def _get_embeddings(self):
        """Get embedding model - OpenAI or ChromaDB default."""
        if settings.OPENAI_API_KEY and "text-embedding" in settings.EMBEDDING_MODEL.lower():
            logger.info(f"Using OpenAI embeddings: {settings.EMBEDDING_MODEL}")
            return OpenAIEmbeddings(
                model=settings.EMBEDDING_MODEL,
                openai_api_key=settings.OPENAI_API_KEY,
            )
        else:
            # Use ChromaDB default embeddings
            logger.info("Using ChromaDB default embeddings")
            from langchain_chroma import Chroma
            # ChromaDB will use its default embedding function
            from chromadb.utils import embedding_functions
            default_ef = embedding_functions.DefaultEmbeddingFunction()
            # Wrap in a LangChain-compatible interface
            from langchain_core.embeddings import Embeddings
            class ChromaDefaultEmbeddings(Embeddings):
                def embed_documents(self, texts):
                    return default_ef(texts)
                def embed_query(self, text):
                    return default_ef([text])[0]
            return ChromaDefaultEmbeddings()

    async def add_documents(
        self, documents: List[str], metadatas: List[Dict], ids: Optional[List[str]] = None
    ) -> None:
        """
        Add documents to vector store.
        
        Args:
            documents: List of document texts
            metadatas: List of metadata dicts
            ids: Optional list of unique IDs
        """
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
            split_docs, doc_ids = self._prepare_documents(langchain_docs, ids)
            
            # Add to vector store (run in thread pool since it's sync)
            await asyncio.to_thread(
                self._add_documents_sync, split_docs, doc_ids
            )
            
            logger.info(f"Added {len(split_docs)} documents to vector store")
        except Exception as e:
            logger.error(f"Failed to add documents: {e}")
            raise

    def _prepare_documents(
        self, docs: List[Document], ids: Optional[List[str]]
    ) -> tuple[List[Document], List[str]]:
        """Prepare documents and IDs, splitting if needed."""
        split_docs = []
        doc_ids = []
        
        for i, doc in enumerate(docs):
            if len(doc.page_content) > settings.CHUNK_SIZE:
                splits = self.text_splitter.split_documents([doc])
                base_id = ids[i] if ids else f"{self.collection_name}_doc_{i}"
                for j, split in enumerate(splits):
                    split_docs.append(split)
                    doc_ids.append(f"{base_id}_chunk_{j}")
            else:
                split_docs.append(doc)
                doc_ids.append(
                    ids[i] if ids else f"{self.collection_name}_doc_{i}"
                )
        
        return split_docs, doc_ids

    def _add_documents_sync(
        self, split_docs: List[Document], doc_ids: List[str]
    ) -> None:
        """Synchronously add documents to vector store."""
        try:
            self.vector_store.add_documents(documents=split_docs, ids=doc_ids)
            # ChromaDB with persist_directory automatically persists,
            # no explicit persist() call needed
        except Exception as e:
            # Check for dimension mismatch errors
            error_str = str(e).lower()
            if "dimension" in error_str or "InvalidArgument" in str(type(e).__name__):
                logger.error(
                    "Embedding dimension mismatch when adding documents. "
                    "This should have been caught during initialization. "
                    "Please restart and reload rules."
                )
            raise

    async def search(
        self, query: str, n_results: int = 5, filter_metadata: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Search for similar documents using LangChain retriever.
        
        Args:
            query: Search query text
            n_results: Number of results to return
            filter_metadata: Optional metadata filters
            
        Returns:
            List of relevant documents with metadata
        """
        try:
            # Create retriever with tenant filter
            where_dict = {"tenant_id": self.tenant_id}
            if filter_metadata:
                where_dict.update(filter_metadata)
            
            retriever = self.vector_store.as_retriever(
                search_kwargs={
                    "k": n_results,
                    "filter": where_dict,
                }
            )
            
            # Search
            docs = await retriever.ainvoke(query)
            
            # Format results
            formatted_results = []
            for doc in docs:
                formatted_results.append({
                    "id": doc.metadata.get("id", ""),
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                })
            
            logger.info(f"Found {len(formatted_results)} results for query")
            return formatted_results
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return []

    async def delete_by_ids(self, ids: List[str]) -> None:
        """Delete documents by IDs."""
        try:
            await asyncio.to_thread(self._delete_sync, ids)
            logger.info(f"Deleted {len(ids)} documents")
        except Exception as e:
            logger.error(f"Failed to delete documents: {e}")
            raise

    def _delete_sync(self, ids: List[str]) -> None:
        """Synchronously delete documents."""
        self.vector_store.delete(ids=ids)
        # ChromaDB with persist_directory automatically persists,
        # no explicit persist() call needed

    async def reset_collection(self) -> None:
        """Reset the collection (useful for testing)."""
        try:
            import shutil
            collection_path = os.path.join(
                settings.VECTOR_STORE_PATH, 
                self.collection_name
            )
            if os.path.exists(collection_path):
                await asyncio.to_thread(shutil.rmtree, collection_path)
            
            # Reinitialize
            self.vector_store = self._initialize_vector_store()
            logger.info(f"Reset collection: {self.collection_name}")
        except Exception as e:
            logger.error(f"Failed to reset collection: {e}")
            raise
