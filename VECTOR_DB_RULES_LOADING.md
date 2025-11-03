# Loading Rules into Vector Database

## Overview

The vector database stores rule documents from PDFs for RAG (Retrieval Augmented Generation). The LLM uses these embeddings to retrieve relevant rules when validating claims.

## How It Works

1. **PDF Extraction**: Rules PDFs are parsed and split into chunks
2. **Embedding Generation**: Each chunk is converted to embeddings using OpenAI
3. **Vector Storage**: Embeddings are stored in ChromaDB with metadata
4. **Tenant Isolation**: Each tenant has separate vector collections

## Loading Rules

### Method 1: Using the Script (Recommended)

The `load_rules_example.py` script handles everything automatically:

```bash
# Load rules for default tenant
cd app
python scripts/load_rules_example.py default

# Load rules for a specific tenant
python scripts/load_rules_example.py tenant_acme
```

**Prerequisites:**
- OpenAI API key set in environment: `OPENAI_API_KEY=your-key`
- PDF files in project root:
  - `Humaein_Technical_Rules.pdf`
  - `Humaein_Medical_Rules.pdf`

**What the script does:**
1. Extracts text from both PDF files
2. Splits text into chunks (500 chars with 50 char overlap)
3. Generates embeddings using OpenAI (`text-embedding-3-small`)
4. Stores in ChromaDB with tenant_id metadata
5. Tests search functionality

### Method 2: Docker Entrypoint (Automatic)

When using Docker, rules are automatically loaded on container startup:

```bash
# Set environment variables
export OPENAI_API_KEY=your-key
export LOAD_RULES=true
export TENANT_ID=default

# Start container
docker-compose up
```

The `docker-entrypoint.sh` script:
1. Waits for PostgreSQL to be ready
2. Runs Alembic migrations
3. Loads rules into vector store (if `LOAD_RULES=true`)

### Method 3: Manual Loading (Programmatic)

```python
from app.llm.vector_store import VectorStore
from pathlib import Path
from pypdf import PdfReader

async def load_rules_manually(tenant_id: str):
    # Initialize vector store
    vector_store = VectorStore(tenant_id)
    
    # Extract text from PDF
    pdf_path = Path("Humaein_Technical_Rules.pdf")
    reader = PdfReader(pdf_path)
    text = "\n\n".join([page.extract_text() for page in reader.pages])
    
    # Split into chunks
    chunks = chunk_text(text, chunk_size=500, chunk_overlap=50)
    
    # Create documents with metadata
    documents = []
    metadatas = []
    ids = []
    
    for i, chunk in enumerate(chunks):
        documents.append(chunk)
        metadatas.append({
            "tenant_id": tenant_id,
            "rule_type": "technical",
            "chunk_index": i,
            "source": "Humaein_Technical_Rules.pdf"
        })
        ids.append(f"technical_chunk_{i}")
    
    # Add to vector store
    await vector_store.add_documents(
        documents=documents,
        metadatas=metadatas,
        ids=ids
    )
```

## Configuration

### Environment Variables

```bash
# Required
OPENAI_API_KEY=sk-...              # OpenAI API key for embeddings

# Optional
EMBEDDING_MODEL=text-embedding-3-small  # Embedding model
VECTOR_STORE_PATH=./vector_store/chroma_db  # Storage path
CHUNK_SIZE=500                     # Chunk size for text splitting
CHUNK_OVERLAP=50                   # Overlap between chunks
TOP_K_RETRIEVAL=30                 # Number of rules to retrieve per query
```

### Vector Store Settings

Located in `app/config.py`:

```python
USE_RAG: bool = True
EMBEDDING_MODEL: str = "text-embedding-3-small"
VECTOR_STORE_PATH: str = "./vector_store/chroma_db"
VECTOR_STORE_MODE: str = "persistent"  # or "in_memory"
CHUNK_SIZE: int = 500
CHUNK_OVERLAP: int = 50
TOP_K_RETRIEVAL: int = 30
```

## Multi-Tenant Support

Each tenant has isolated vector collections:

```python
# Tenant A
vector_store_a = VectorStore("tenant_acme")
await vector_store_a.add_documents(...)

# Tenant B
vector_store_b = VectorStore("tenant_global")
await vector_store_b.add_documents(...)
```

Rules are filtered by `tenant_id` metadata during retrieval.

## Updating Rules

### Full Reload (Replace All)

```bash
# 1. Delete existing collection (optional, will be recreated)
rm -rf vector_store/chroma_db

# 2. Reload rules
python scripts/load_rules_example.py default
```

### Incremental Update

The vector store supports adding new documents without recreating the entire collection:

```python
# Add new rule chunks
await vector_store.add_documents(
    documents=new_chunks,
    metadatas=new_metadatas,
    ids=new_ids
)
```

## Verification

### Check Vector Store Contents

```python
from app.llm.vector_store import VectorStore

async def verify_rules(tenant_id: str):
    vector_store = VectorStore(tenant_id)
    
    # Test search
    results = await vector_store.search(
        query="service code approval requirements",
        n_results=5,
        filter_metadata={"tenant_id": tenant_id}
    )
    
    print(f"Found {len(results)} results")
    for result in results:
        print(f"- {result.get('content', '')[:100]}...")
```

### Test Script Output

The `load_rules_example.py` script includes automatic testing:

```
🔍 Testing search functionality...

   Query: 'service code requires prior approval'
   Found 2 results:
     1. [technical] chunk_3: Service codes SRV1001, SRV1002 require...
     2. [technical] chunk_5: Prior approval must be obtained...
```

## Troubleshooting

### Issue: "Collection expecting embedding with dimension of 384, got 1536"

**Cause**: ChromaDB was initialized with default embeddings, but OpenAI embeddings are 1536-dimensional.

**Solution**: The vector store automatically detects this and recreates the collection. Or manually delete:
```bash
rm -rf vector_store/chroma_db
```

### Issue: Rules not found during validation

**Check**:
1. Rules loaded: `python scripts/load_rules_example.py default`
2. Tenant ID matches: Rules must have `tenant_id` metadata matching claim's tenant
3. Vector store path: Check `VECTOR_STORE_PATH` is correct

### Issue: OpenAI API errors

**Check**:
1. API key is set: `echo $OPENAI_API_KEY`
2. API key is valid: Test with OpenAI API directly
3. Rate limits: Check OpenAI dashboard for usage

## Best Practices

1. **Version Control**: Keep PDF files in version control
2. **Backup**: Backup vector store before major updates
3. **Testing**: Always test search after loading rules
4. **Tenant Isolation**: Ensure tenant_id is correctly set in metadata
5. **Chunking**: Adjust `CHUNK_SIZE` and `CHUNK_OVERLAP` based on rule complexity

## Integration with Rule Configuration

The vector database stores **PDF-extracted rules** for LLM retrieval.

The **JSON rule files** (`technical_rules.json`, `medical_rules.json`) are used for:
- Static rule validation (technical rules engine)
- Thresholds and configuration
- Service/diagnosis lists

**Both work together**:
- LLM uses vector DB for comprehensive rule understanding
- Static engine uses JSON files for deterministic validation

## Example: Complete Setup

```bash
# 1. Set OpenAI API key
export OPENAI_API_KEY=sk-...

# 2. Load rules into vector DB
cd app
python scripts/load_rules_example.py default

# 3. Verify rules are loaded
python -c "
import asyncio
from llm.vector_store import VectorStore

async def test():
    vs = VectorStore('default')
    results = await vs.search('approval requirements', n_results=3)
    print(f'Found {len(results)} rules')

asyncio.run(test())
"

# 4. Update JSON rules (if needed)
# Edit app/rules/default/technical_rules.json
# Or use API: PUT /api/v1/rules/technical
```

## Docker Setup

```yaml
# docker-compose.yml
services:
  backend:
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - LOAD_RULES=true
      - TENANT_ID=default
```

Rules are automatically loaded on first container start.

