# LangChain In-Memory Vector Stores Guide

## Overview

LangChain supports multiple vector store implementations, including both **persistent** and **in-memory** options. This guide covers when and how to use in-memory vector stores.

## In-Memory vs Persistent Vector Stores

| Feature | In-Memory | Persistent |
|--------|-----------|------------|
| **Speed** | ⚡ Very Fast | 🐢 Slower (disk I/O) |
| **Data Persistence** | ❌ Lost on restart | ✅ Saved to disk |
| **Memory Usage** | 💾 RAM only | 💾 RAM + Disk |
| **Setup Complexity** | ⭐ Easy | ⭐⭐ Medium |
| **Use Case** | Testing, Dev, Temporary data | Production, Long-term storage |

## Supported In-Memory Stores

### 1. **ChromaDB In-Memory** (Current Implementation)

The most flexible option - supports both modes:

```python
from llm.vector_store import VectorStore

# In-memory mode
vector_store = VectorStore("default", in_memory=True)

# Or via config
# .env: VECTOR_STORE_MODE=in_memory
vector_store = VectorStore("default")  # Uses config
```

**Pros:**
- ✅ Same API as persistent mode
- ✅ Easy to switch between modes
- ✅ Supports tenant isolation
- ✅ Works with any embeddings

**Cons:**
- ❌ Data lost on restart
- ❌ Limited by RAM size

### 2. **FAISS In-Memory** (Alternative)

Pure in-memory, very fast, but requires explicit embeddings:

```python
from llm.vector_store_faiss import FAISSVectorStore

vector_store = FAISSVectorStore("default")
await vector_store.add_documents(documents, metadatas)
results = await vector_store.search("query")
```

**Pros:**
- ⚡ Extremely fast search
- ✅ Good for large-scale similarity search
- ✅ Can save/load index files

**Cons:**
- ❌ Requires explicit embeddings (no defaults)
- ❌ No native metadata filtering
- ❌ More complex setup

### 3. **In-Memory Embeddings Store**

Simple dictionary-based store (not recommended for production):

```python
from langchain.vectorstores import InMemoryVectorStore

# Very simple, but limited functionality
```

## Configuration

### Option 1: Environment Variable

```env
# .env
VECTOR_STORE_MODE=in_memory  # or "persistent"
```

### Option 2: Explicit Parameter

```python
# Force in-memory mode
vector_store = VectorStore("default", in_memory=True)

# Force persistent mode
vector_store = VectorStore("default", in_memory=False)
```

### Option 3: Test vs Production

```python
import os

# In tests or development
is_test = os.getenv("ENVIRONMENT") == "test"
vector_store = VectorStore("default", in_memory=is_test)
```

## Use Cases

### ✅ When to Use In-Memory

1. **Development/Testing**
   ```python
   # Fast iteration, don't need persistence
   vector_store = VectorStore("test", in_memory=True)
   ```

2. **Temporary Data Processing**
   ```python
   # Process batch of documents, then discard
   vector_store = VectorStore("batch_123", in_memory=True)
   # Process...
   # Data automatically cleaned up when process ends
   ```

3. **Unit Tests**
   ```python
   def test_retrieval():
       store = VectorStore("test", in_memory=True)
       await store.add_documents(["doc1"], [{}])
       results = await store.search("query")
       assert len(results) > 0
   ```

4. **High-Performance Temporary Search**
   - Need fast search for short-lived data
   - Data can be regenerated if needed

### ❌ When NOT to Use In-Memory

1. **Production Systems**
   - Data must persist across restarts
   - Use persistent mode

2. **Large Datasets**
   - Limited by RAM
   - Better to use persistent + pagination

3. **Multi-Process Applications**
   - In-memory data not shared between processes
   - Use persistent store or shared cache

## Code Examples

### Basic In-Memory Usage

```python
from llm.vector_store import VectorStore
import asyncio

async def example():
    # Create in-memory store
    store = VectorStore("default", in_memory=True)
    
    # Add documents
    await store.add_documents(
        documents=["Service code 99223 requires approval"],
        metadatas=[{"rule_type": "technical"}],
        ids=["rule_1"],
    )
    
    # Search
    results = await store.search("approval requirements", n_results=3)
    print(f"Found {len(results)} results")
    
    # Data exists only in memory - lost when process ends
```

### Switching Between Modes

```python
def get_vector_store(tenant_id: str, use_cache: bool = False):
    """
    Get vector store with appropriate mode.
    
    Args:
        tenant_id: Tenant identifier
        use_cache: If True, use in-memory for faster access
    """
    if use_cache:
        # Fast in-memory cache (data reloaded from persistent store)
        return VectorStore(tenant_id, in_memory=True)
    else:
        # Persistent storage
        return VectorStore(tenant_id, in_memory=False)
```

### Testing with In-Memory

```python
import pytest
from llm.vector_store import VectorStore

@pytest.fixture
async def vector_store():
    """Fixture that provides in-memory vector store for tests."""
    store = VectorStore("test_tenant", in_memory=True)
    yield store
    # Cleanup happens automatically (in-memory, no files to clean)

@pytest.mark.asyncio
async def test_add_and_search(vector_store):
    await vector_store.add_documents(
        documents=["Test document"],
        metadatas=[{"test": True}],
    )
    
    results = await vector_store.search("test", n_results=1)
    assert len(results) == 1
    assert "Test document" in results[0]["content"]
```

### Hybrid Approach

```python
class HybridVectorStore:
    """Use in-memory for cache, persistent for storage."""
    
    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        self.persistent_store = VectorStore(tenant_id, in_memory=False)
        self.cache_store = VectorStore(tenant_id, in_memory=True)
        self._cache_loaded = False
    
    async def search(self, query: str, n_results: int = 5):
        """Search with in-memory cache fallback."""
        # Try cache first
        if self._cache_loaded:
            results = await self.cache_store.search(query, n_results)
            if results:
                return results
        
        # Fallback to persistent
        results = await self.persistent_store.search(query, n_results)
        
        # Update cache for next time
        if not self._cache_loaded:
            await self._load_cache()
            self._cache_loaded = True
        
        return results
    
    async def _load_cache(self):
        """Load frequently accessed data into cache."""
        # Implementation to copy data from persistent to cache
        pass
```

## Performance Comparison

### ChromaDB In-Memory
- **Initialization**: ~50ms
- **Add 100 docs**: ~200ms
- **Search (k=5)**: ~10ms
- **Memory**: ~1MB per 1000 docs (with embeddings)

### FAISS In-Memory
- **Initialization**: ~100ms
- **Add 100 docs**: ~150ms
- **Search (k=5)**: ~5ms (faster!)
- **Memory**: ~2MB per 1000 docs

### Persistent ChromaDB
- **Initialization**: ~100ms (disk access)
- **Add 100 docs**: ~500ms (includes disk write)
- **Search (k=5)**: ~20ms
- **Memory**: Same as in-memory + disk space

## Best Practices

### 1. **Development Workflow**

```python
# Development: Use in-memory for speed
if settings.DEBUG:
    vector_store = VectorStore(tenant_id, in_memory=True)
else:
    vector_store = VectorStore(tenant_id, in_memory=False)
```

### 2. **Testing Strategy**

```python
# Always use in-memory for tests
@pytest.fixture(scope="function")
async def test_vector_store():
    return VectorStore("test", in_memory=True)
```

### 3. **Memory Management**

```python
# For large datasets, consider batching
async def load_large_dataset(documents: List[str]):
    store = VectorStore("default", in_memory=True)
    
    batch_size = 100
    for i in range(0, len(documents), batch_size):
        batch = documents[i:i + batch_size]
        await store.add_documents(
            documents=batch,
            metadatas=[{}] * len(batch),
        )
        
        # Monitor memory
        if i % 1000 == 0:
            import psutil
            memory = psutil.Process().memory_info().rss / 1024 / 1024
            print(f"Memory usage: {memory}MB")
```

### 4. **Data Migration**

```python
# Load from persistent, work in memory
async def migrate_to_in_memory(tenant_id: str):
    # Load from persistent
    persistent = VectorStore(tenant_id, in_memory=False)
    
    # Create in-memory copy
    memory = VectorStore(tenant_id, in_memory=True)
    
    # Copy data (you'd need to implement document retrieval)
    # This is pseudocode
    all_docs = await persistent.get_all_documents()
    await memory.add_documents(all_docs)
    
    return memory
```

## Troubleshooting

### Issue: Out of Memory

```python
# Solution: Use persistent mode or reduce dataset size
vector_store = VectorStore(tenant_id, in_memory=False)

# Or process in batches
for batch in document_batches:
    await vector_store.add_documents(batch)
    # Process batch
    await vector_store.reset_collection()  # Clear for next batch
```

### Issue: Data Lost on Restart

```python
# This is expected with in-memory stores
# Solution: Use persistent mode or reload data on startup

async def startup():
    if settings.VECTOR_STORE_MODE == "in_memory":
        # Reload from persistent source
        await reload_rules_into_memory()
```

### Issue: Slow Initialization

```python
# In-memory is fast, but if slow:
# 1. Check embedding model (OpenAI API calls are slow)
# 2. Use ChromaDB default embeddings for testing
# 3. Consider lazy loading
```

## Summary

| Store Type | Use When | Avoid When |
|------------|----------|------------|
| **ChromaDB In-Memory** | Dev, Testing, Temporary data | Production, Large datasets |
| **FAISS In-Memory** | Fast similarity search, Research | Production, Need persistence |
| **Persistent ChromaDB** | Production, Long-term storage | Development iteration |

**Recommendation**: 
- Use **in-memory** for development and testing
- Use **persistent** for production
- Switch easily with config: `VECTOR_STORE_MODE=in_memory`

