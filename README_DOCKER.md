# Docker Setup Guide

This guide explains how to build and run the Medical Claims Validator backend using Docker.

## Prerequisites

- Docker and Docker Compose installed
- OpenAI API key (for LLM features and rule loading)

## Quick Start

### 1. Set Environment Variables

Create a `.env` file in the project root:

```bash
# Database
POSTGRES_USER=user
POSTGRES_PASSWORD=pass
POSTGRES_DB=claims_db
POSTGRES_PORT=5432

# Authentication
SECRET_KEY=your-secret-key-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=720

# OpenAI (Required for LLM features)
OPENAI_API_KEY=your-openai-api-key-here
LLM_MODEL=gpt-4o-mini
EMBEDDING_MODEL=text-embedding-3-small

# RAG Configuration
USE_RAG=true
VECTOR_STORE_MODE=persistent

# Runtime Options
RUN_MIGRATIONS=true
LOAD_RULES=true
TENANT_ID=default
```

### 2. Build and Run with Docker Compose

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f backend

# Stop services
docker-compose down

# Stop and remove volumes (clean slate)
docker-compose down -v
```

### 3. Build Docker Image Manually

```bash
# Build the image
docker build -t humaein-backend .

# Run the container
docker run -d \
  --name humaein-backend \
  -p 8000:8000 \
  -e DATABASE_URL=postgresql://user:pass@host:5432/claims_db \
  -e SECRET_KEY=your-secret-key \
  -e OPENAI_API_KEY=your-api-key \
  -e LOAD_RULES=true \
  -v $(pwd)/app/uploads:/app/uploads \
  -v $(pwd)/app/vector_store:/app/vector_store \
  humaein-backend
```

## Environment Variables

### Required

- `DATABASE_URL`: PostgreSQL connection string
- `SECRET_KEY`: JWT secret key for authentication
- `OPENAI_API_KEY`: OpenAI API key for LLM features

### Optional

- `LOAD_RULES`: Set to `true` to automatically load rules from PDFs on startup (default: `true`)
- `RUN_MIGRATIONS`: Set to `true` to run Alembic migrations on startup (default: `true`)
- `TENANT_ID`: Tenant identifier for multi-tenancy (default: `default`)
- `LLM_MODEL`: OpenAI model to use (default: `gpt-4o-mini`)
- `EMBEDDING_MODEL`: Embedding model to use (default: `text-embedding-3-small`)

## Entrypoint Script

The `docker-entrypoint.sh` script automatically:

1. **Waits for database**: Checks if PostgreSQL is ready before proceeding
2. **Runs migrations**: Executes Alembic migrations to set up the database schema
3. **Loads rules**: Runs `load_rules_example.py` to load PDF rules into the vector store
4. **Starts FastAPI**: Launches the uvicorn server

## Volumes

The following directories are mounted as volumes in docker-compose:

- `./app/uploads`: Uploaded claim files
- `./app/vector_store`: Vector database (ChromaDB) data
- `./app/logs`: Application logs

## Health Check

The container includes a health check that pings `/health` endpoint every 30 seconds.

## Manual Rule Loading

To manually load rules after container startup:

```bash
# Enter the container
docker exec -it humaein-backend bash

# Run the script
python scripts/load_rules_example.py default

# Or with a specific tenant
python scripts/load_rules_example.py tenant-123
```

## Troubleshooting

### Database Connection Issues

```bash
# Check if PostgreSQL container is running
docker-compose ps

# Check database logs
docker-compose logs postgres

# Test connection
docker exec -it humaein-backend python -c "from sqlalchemy import create_engine; engine = create_engine('${DATABASE_URL}'); engine.connect()"
```

### Rule Loading Issues

```bash
# Check if PDFs are present
docker exec -it humaein-backend ls -la /app/*.pdf

# Check OpenAI API key
docker exec -it humaein-backend python -c "from config import get_settings; print(get_settings().OPENAI_API_KEY[:10])"

# Manually run rule loading with verbose output
docker exec -it humaein-backend python scripts/load_rules_example.py default
```

### Vector Store Issues

```bash
# Check vector store directory
docker exec -it humaein-backend ls -la /app/vector_store/

# Clear vector store (if needed)
docker exec -it humaein-backend rm -rf /app/vector_store/chroma_db/*
```

## Production Considerations

1. **Security**: Change default `SECRET_KEY` and database passwords
2. **Resource Limits**: Add memory and CPU limits in docker-compose.yml
3. **SSL/TLS**: Configure reverse proxy (nginx/traefik) for HTTPS
4. **Backups**: Set up regular backups for PostgreSQL and vector store
5. **Monitoring**: Add logging and monitoring tools
6. **Scaling**: Consider using Docker Swarm or Kubernetes for production

## API Access

Once running, the API will be available at:

- **API Base**: http://localhost:8000
- **Health Check**: http://localhost:8000/health
- **API Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

