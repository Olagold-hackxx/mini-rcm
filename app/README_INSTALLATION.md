# Installation Guide

## Prerequisites

- Python 3.10 or higher
- PostgreSQL 12+ (for production) or SQLite (for development)
- Virtual environment (recommended)

## Quick Start

### 1. Create Virtual Environment

```bash
python -m venv venv

# Activate on macOS/Linux
source venv/bin/activate

# Activate on Windows
venv\Scripts\activate
```

### 2. Install Dependencies

**Full Installation (with LLM/RAG features):**
```bash
pip install -r requirements.txt
```

**Minimal Installation (without LLM features):**
```bash
pip install -r requirements-minimal.txt
```

**Development Installation (with testing tools):**
```bash
pip install -r requirements-dev.txt
```

### 3. Environment Configuration

Create a `.env` file in the root directory:

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```env
# Required
SECRET_KEY=your-secret-key-here
DATABASE_URL=postgresql://user:password@localhost:5432/claims_db

# Optional - for LLM features
ANTHROPIC_API_KEY=your-anthropic-key
OPENAI_API_KEY=your-openai-key

# Optional - for vector store
VECTOR_STORE_MODE=persistent  # or "in_memory"
```

### 4. Database Setup

**Option A: PostgreSQL (Recommended for Production)**

```bash
# Create database
createdb claims_db

# Run migrations (if using Alembic)
alembic upgrade head
```

**Option B: SQLite (Development Only)**

Update `.env`:
```env
DATABASE_URL=sqlite:///./claims_db.db
```

### 5. Run Application

```bash
# Development
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Production
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

## Optional: Setup Vector Store

If using RAG features, initialize the vector store:

```bash
# Load example rules
python app/scripts/load_rules_example.py
```

## Docker Installation (Alternative)

```bash
# Build image
docker build -t medical-claims-validator .

# Run container
docker run -p 8000:8000 --env-file .env medical-claims-validator
```

## Troubleshooting

### Issue: psycopg2 installation fails

```bash
# macOS
brew install postgresql

# Ubuntu/Debian
sudo apt-get install libpq-dev python3-dev

# Then retry
pip install psycopg2-binary
```

### Issue: ChromaDB installation fails

```bash
# Ensure Python 3.10+
python --version

# Upgrade pip
pip install --upgrade pip

# Retry installation
pip install chromadb
```

### Issue: LangChain version conflicts

```bash
# Use specific versions
pip install langchain==0.1.0 langchain-chroma==0.1.0
```

### Issue: Missing dependencies

```bash
# Update all packages
pip install --upgrade -r requirements.txt
```

## Production Deployment

### 1. Use Production Requirements

```bash
pip install -r requirements.txt --no-deps
pip install --only-binary :all: -r requirements.txt
```

### 2. Set Environment Variables

```bash
export SECRET_KEY=$(openssl rand -hex 32)
export DATABASE_URL=postgresql://user:pass@host:5432/claims_db
export ANTHROPIC_API_KEY=your-key
```

### 3. Run with Gunicorn (recommended)

```bash
pip install gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## Package Versions

All versions are pinned to ensure compatibility. Update carefully:

```bash
# Check for updates
pip list --outdated

# Update specific package
pip install --upgrade package-name
```

