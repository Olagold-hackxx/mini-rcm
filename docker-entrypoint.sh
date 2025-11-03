#!/bin/bash
set -e

echo "🚀 Starting Medical Claims Validator Backend..."

# Wait for PostgreSQL to be ready (if DATABASE_URL is set)
if [ -n "$DATABASE_URL" ]; then
    echo "⏳ Waiting for database connection..."
    until python -c "from sqlalchemy import create_engine; engine = create_engine('${DATABASE_URL}'); engine.connect()" 2>/dev/null; do
        echo "   Database not ready, waiting..."
        sleep 2
    done
    echo "✅ Database connection established"
fi

# Run database migrations
if [ -n "$DATABASE_URL" ] && [ "$RUN_MIGRATIONS" != "false" ]; then
    echo "📦 Running database migrations..."
    alembic upgrade head || echo "⚠️  Migration failed or already up to date"
fi

# Load rules into vector store if requested
if [ "$LOAD_RULES" = "true" ]; then
    echo "📚 Loading rules into vector store..."
    if [ -z "$OPENAI_API_KEY" ]; then
        echo "⚠️  WARNING: OPENAI_API_KEY not set, skipping rule loading"
    else
        echo "   Running load_rules_example.py for tenant: ${TENANT_ID:-default}"
        python scripts/load_rules_example.py ${TENANT_ID:-default} || echo "⚠️  Rule loading failed or already loaded"
    fi
else
    echo "⏭️  Skipping rule loading (set LOAD_RULES=true to enable)"
fi

# Start the application
echo "🌟 Starting FastAPI application..."
exec python -m uvicorn main:app --host 0.0.0.0 --port 8000

