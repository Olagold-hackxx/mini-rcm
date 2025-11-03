"""Script to load rule documents from PDF files into vector store using OpenAI embeddings."""
import asyncio
import sys
import re
from pathlib import Path
from typing import List, Tuple

try:
    from pypdf import PdfReader
except ImportError:
    print("Error: pypdf is not installed. Install it with: pip install pypdf")
    sys.exit(1)

# Add app directory to path (so relative imports work)
app_dir = Path(__file__).parent.parent
sys.path.insert(0, str(app_dir))

from llm.vector_store import VectorStore
from config import get_settings

settings = get_settings()

# Validate OpenAI API key is set
if not settings.OPENAI_API_KEY:
    print("❌ ERROR: OPENAI_API_KEY is not set in environment variables or .env file")
    print("\nPlease set your OpenAI API key:")
    print("  1. Add to .env file: OPENAI_API_KEY=your-api-key-here")
    print("  2. Or export: export OPENAI_API_KEY=your-api-key-here")
    sys.exit(1)

# Ensure OpenAI embeddings are being used
if "text-embedding" not in settings.EMBEDDING_MODEL.lower():
    print(f"⚠️  WARNING: EMBEDDING_MODEL is set to '{settings.EMBEDDING_MODEL}'")
    print("   Expected OpenAI embedding model (e.g., 'text-embedding-3-small')")
    print("   Using OpenAI anyway if API key is available...\n")

print(f"🔑 Using OpenAI embeddings with model: {settings.EMBEDDING_MODEL}\n")


def extract_text_from_pdf(pdf_path: Path) -> str:
    """Extract text content from a PDF file."""
    try:
        reader = PdfReader(pdf_path)
        text_parts = []
        
        for page_num, page in enumerate(reader.pages):
            text = page.extract_text()
            if text.strip():
                text_parts.append(text)
        
        full_text = "\n\n".join(text_parts)
        return full_text
    except Exception as e:
        raise RuntimeError(f"Failed to extract text from {pdf_path}: {str(e)}") from e


def chunk_text(text: str, chunk_size: int = 500, chunk_overlap: int = 50) -> List[str]:
    """
    Split text into chunks with overlap.
    
    Args:
        text: The text to chunk
        chunk_size: Maximum size of each chunk
        chunk_overlap: Number of characters to overlap between chunks
        
    Returns:
        List of text chunks
    """
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        
        # Try to break at sentence boundary if possible
        if end < len(text):
            # Look for sentence endings near the chunk boundary
            for delimiter in ['. ', '.\n', '! ', '!\n', '? ', '?\n']:
                last_delimiter = text.rfind(delimiter, start, end)
                if last_delimiter > start + chunk_size // 2:  # Only if not too early
                    end = last_delimiter + len(delimiter)
                    break
        
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        
        # Move start position with overlap
        start = end - chunk_overlap
        if start >= len(text):
            break
    
    return chunks


def parse_rules_from_text(text: str, rule_type: str) -> List[Tuple[str, dict]]:
    """
    Parse text and extract rule documents with metadata.
    
    Args:
        text: Extracted text from PDF
        rule_type: Type of rules ('technical' or 'medical')
        
    Returns:
        List of tuples: (document_text, metadata)
    """
    # Clean up the text
    text = re.sub(r'\s+', ' ', text)  # Normalize whitespace
    text = text.strip()
    
    # Split into chunks
    chunks = chunk_text(text, chunk_size=settings.CHUNK_SIZE, chunk_overlap=settings.CHUNK_OVERLAP)
    
    # Create documents with metadata
    documents = []
    for i, chunk in enumerate(chunks):
        if not chunk.strip():
            continue
        
        metadata = {
            "rule_type": rule_type,
            "chunk_index": i,
            "source": f"{rule_type}_rules.pdf",
            "total_chunks": len(chunks),
        }
        
        documents.append((chunk, metadata))
    
    return documents


async def load_pdf_rules(tenant_id: str = "default"):
    """
    Load rule documents from PDF files into vector store.
    
    Args:
        tenant_id: Tenant identifier for multi-tenancy
    """
    # Get project root (parent of app directory)
    project_root = Path(__file__).parent.parent.parent
    pdf_dir = project_root
    
    # Define PDF files
    technical_pdf = pdf_dir / "Humaein_Technical_Rules.pdf"
    medical_pdf = pdf_dir / "Humaein_Medical_Rules.pdf"
    
    # Check if files exist
    if not technical_pdf.exists():
        raise FileNotFoundError(f"Technical rules PDF not found: {technical_pdf}")
    if not medical_pdf.exists():
        raise FileNotFoundError(f"Medical rules PDF not found: {medical_pdf}")
    
    print(f"📄 Loading PDF rules for tenant '{tenant_id}'...")
    print(f"   Technical Rules: {technical_pdf.name}")
    print(f"   Medical Rules: {medical_pdf.name}\n")
    
    # Initialize vector store with OpenAI embeddings
    print("🔧 Initializing vector store with OpenAI embeddings...")
    print(f"   Using model: {settings.EMBEDDING_MODEL}")
    print("   Note: If an existing collection uses different embeddings, it will be recreated.\n")
    
    vector_store = VectorStore(tenant_id)
    print(f"   ✅ Vector store initialized (using {settings.EMBEDDING_MODEL})\n")
    
    all_documents = []
    all_metadatas = []
    all_ids = []
    
    # Process Technical Rules PDF
    print("📖 Extracting text from Technical Rules PDF...")
    technical_text = extract_text_from_pdf(technical_pdf)
    technical_docs = parse_rules_from_text(technical_text, "technical")
    
    for i, (doc, metadata) in enumerate(technical_docs):
        all_documents.append(doc)
        metadata["tenant_id"] = tenant_id
        all_metadatas.append(metadata)
        all_ids.append(f"technical_rule_chunk_{i+1}")
    
    print(f"   ✅ Extracted {len(technical_docs)} chunks from Technical Rules\n")
    
    # Process Medical Rules PDF
    print("📖 Extracting text from Medical Rules PDF...")
    medical_text = extract_text_from_pdf(medical_pdf)
    medical_docs = parse_rules_from_text(medical_text, "medical")
    
    for i, (doc, metadata) in enumerate(medical_docs):
        all_documents.append(doc)
        metadata["tenant_id"] = tenant_id
        all_metadatas.append(metadata)
        all_ids.append(f"medical_rule_chunk_{i+1}")
    
    print(f"   ✅ Extracted {len(medical_docs)} chunks from Medical Rules\n")
    
    # Load all documents into vector store
    print(f"💾 Loading {len(all_documents)} document chunks into vector store...")
    
    await vector_store.add_documents(
        documents=all_documents,
        metadatas=all_metadatas,
        ids=all_ids,
    )
    
    print(f"✅ Successfully loaded {len(all_documents)} documents!\n")
    
    # Test search
    print("🔍 Testing search functionality...")
    test_queries = [
        "service code requires prior approval",
        "facility eligibility for inpatient",
        "diagnosis code requirements",
    ]
    
    for query in test_queries:
        print(f"\n   Query: '{query}'")
        results = await vector_store.search(
            query=query,
            n_results=2,
        )
        
        print(f"   Found {len(results)} results:")
        for i, result in enumerate(results, 1):
            rule_type = result.get('metadata', {}).get('rule_type', 'unknown')
            chunk_idx = result.get('metadata', {}).get('chunk_index', '?')
            content = result.get('content', '')[:80]
            print(f"     {i}. [{rule_type}] chunk_{chunk_idx}: {content}...")


if __name__ == "__main__":
    tenant_id = sys.argv[1] if len(sys.argv) > 1 else "default"
    asyncio.run(load_pdf_rules(tenant_id))

