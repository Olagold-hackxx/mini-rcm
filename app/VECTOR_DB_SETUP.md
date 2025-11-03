# Vector Database Setup Guide (LangChain)

## Overview

This application uses **LangChain with ChromaDB** as the vector database for storing and retrieving rule document embeddings. LangChain provides:

- ✅ **Standardized Interface**: Consistent API across different vector stores
- ✅ **Better Integration**: Works seamlessly with LangChain's retrieval chains
- ✅ **Automatic Text Splitting**: Built-in document chunking
- ✅ **Flexible Embeddings**: Support for OpenAI or ChromaDB default embeddings
- ✅ **Tenant Isolation**: Each tenant gets its own collection

## Installation

### 1. Install Required Packages

```bash
pip install langchain langchain-chroma langchain-openai chromadb
```

### 2. Optional: For OpenAI Embeddings

If you want to use OpenAI embeddings:

```bash
pip install openai
```

Add to your `.env`:
```env
OPENAI_API_KEY=your-openai-api-key-here
EMBEDDING_MODEL=text-embedding-3-small
```

## Configuration

Update your `.env` file:

```env
# RAG Configuration
USE_RAG=true
EMBEDDING_MODEL=text-embedding-3-small  # or leave empty for ChromaDB default
VECTOR_STORE_PATH=./vector_store/chroma_db
CHUNK_SIZE=500
CHUNK_OVERLAP=50
TOP_K_RETRIEVAL=5

# LangChain
USE_LANGCHAIN=true

# OpenAI (optional)
OPENAI_API_KEY=your-key-here
```

## LangChain Components

### 1. Vector Store (`app/llm/vector_store.py`)

Uses `langchain_chroma.Chroma`:
- Automatic document chunking
- Tenant-scoped collections
- Persistent storage
- LangChain retriever interface

### 2. Embeddings (`app/llm/embeddings.py`)

Supports:
- **OpenAI Embeddings**: Via `langchain_openai.OpenAIEmbeddings`
- **ChromaDB Default**: Built-in embedding function

### 3. Retriever (`app/llm/retriever.py`)

Uses LangChain's retriever interface:
- Semantic search with metadata filtering
- Automatic tenant isolation
- Async support

## Local Setup Steps

### 1. Install Dependencies

```bash
pip install langchain langchain-chroma langchain-openai chromadb
```

### 2. Create Vector Store Directory

```bash
mkdir -p vector_store/chroma_db
```

### 3. Load Rule Documents

Run the example script:

```bash
python app/scripts/load_rules_example.py
```

Or create your own loader:

```python
from llm.vector_store import VectorStore
import asyncio

async def load_rules():
    vector_store = VectorStore("default")
    
    documents = [
        "Service code 99223 requires prior approval...",
        "Diagnosis code I10 requires approval...",
    ]
    
    metadatas = [
        {"rule_type": "technical", "section": "1"},
        {"rule_type": "technical", "section": "2"},
    ]
    
    ids = ["rule_1", "rule_2"]
    
    await vector_store.add_documents(
        documents=documents,
        metadatas=metadatas,
        ids=ids,
    )

asyncio.run(load_rules())
```

### 4. Test Retrieval

```python
from llm.vector_store import VectorStore
import asyncio

async def test_search():
    vector_store = VectorStore("default")
    results = await vector_store.search(
        query="service code 99223 approval",
        n_results=3,
    )
    print(f"Found {len(results)} results")
    for r in results:
        print(f"- {r['metadata']}: {r['content'][:100]}...")

asyncio.run(test_search())
```

## Directory Structure

```
humaein/
├── app/
│   └── llm/
│       ├── vector_store.py      # LangChain ChromaDB implementation
│       ├── embeddings.py         # LangChain embeddings
│       └── retriever.py          # LangChain retriever
├── vector_store/
│   └── chroma_db/               # ChromaDB persistent storage
│       └── [tenant_collections]/
```

## LangChain Features Used

### Document Chunking

LangChain automatically splits large documents:

```python
from langchain_text_splitters import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50,
)
```

### Retriever Interface

LangChain's retriever provides consistent interface:

```python
retriever = vector_store.as_retriever(
    search_kwargs={
        "k": 5,
        "filter": {"tenant_id": "default"},
    }
)

docs = await retriever.ainvoke("query text")
```

### Metadata Filtering

Filter by tenant and rule type:

```python
results = await vector_store.search(
    query="approval requirements",
    n_results=5,
    filter_metadata={
        "tenant_id": "default",
        "rule_type": "technical",
    },
)
```

## Usage in Application

The vector store is used by the `RuleRetriever`:

```python
from llm.retriever import RuleRetriever

retriever = RuleRetriever(tenant_id="default")
rules = await retriever.retrieve_relevant_rules(claim_data)
```

## Integration with LLM Evaluator

LangChain chains can be used for enhanced retrieval:

```python
from langchain.chains import RetrievalQA
from langchain_anthropic import ChatAnthropic

# Create retrieval chain
llm = ChatAnthropic(model="claude-3-sonnet")
retriever = vector_store.as_retriever()
qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    retriever=retriever,
)

# Query with context
response = await qa_chain.ainvoke({
    "query": "What are the approval requirements for service 99223?"
})
```

## Troubleshooting

### Issue: LangChain imports not found
```bash
pip install langchain langchain-chroma langchain-openai
```

### Issue: ChromaDB not found
```bash
pip install chromadb
```

### Issue: Empty results from search
- Ensure documents are loaded: Check `vector_store/chroma_db/`
- Verify tenant_id matches: Rules are scoped by tenant_id
- Check query relevance: Try broader search terms

### Issue: OpenAI embedding errors
- Check API key is set: `OPENAI_API_KEY` in `.env`
- Verify quota: OpenAI API has usage limits
- Fallback: Remove `OPENAI_API_KEY` to use ChromaDB default embeddings

### Issue: Document chunking too aggressive
Adjust in config:
```env
CHUNK_SIZE=500      # Larger chunks
CHUNK_OVERLAP=50    # Less overlap
```

## Production Considerations

### 1. **Use OpenAI Embeddings**
More accurate but costs money:
```env
OPENAI_API_KEY=your-key
EMBEDDING_MODEL=text-embedding-3-small
```

### 2. **Optimize Chunk Sizes**
Balance between:
- Smaller chunks: More precise retrieval
- Larger chunks: More context per result

### 3. **Metadata Strategy**
Add rich metadata for better filtering:
```python
metadata = {
    "tenant_id": "default",
    "rule_type": "technical",
    "section": "1",
    "topic": "approval",
    "priority": "high",
}
```

### 4. **Migration to Production Vector DBs**

LangChain makes it easy to switch:

```python
# Switch to Pinecone
from langchain_pinecone import PineconeVectorStore
vector_store = PineconeVectorStore(index_name="rules", embedding=embeddings)

# Switch to Weaviate
from langchain_weaviate import WeaviateVectorStore
vector_store = WeaviateVectorStore(client=client, embedding=embeddings)
```

## Example: Full RAG Chain

```python
from langchain.chains import RetrievalQA
from langchain_anthropic import ChatAnthropic
from llm.vector_store import VectorStore

# Setup
vector_store = VectorStore("default")
llm = ChatAnthropic(model="claude-3-sonnet")

# Create chain
retriever = vector_store.as_retriever(search_kwargs={"k": 5})
qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    retriever=retriever,
    return_source_documents=True,
)

# Query
response = await qa_chain.ainvoke({
    "query": "What rules apply to service code 99223?"
})

print(response["result"])
print(f"Sources: {len(response['source_documents'])}")
```
