# Alembic Troubleshooting Guide

## Common Errors and Solutions

### Error: `Can't load plugin: sqlalchemy.dialects:driver`

**Cause**: The database URL in `alembic.ini` contains a placeholder "driver" instead of a real driver name, or the database driver isn't installed.

**Solutions**:

1. **Fix the alembic.ini placeholder** (already done):
   ```ini
   sqlalchemy.url = postgresql://user:pass@localhost:5432/claims_db
   ```
   Note: This is overridden by `env.py` which uses your `.env` file.

2. **Install the database driver**:

   For PostgreSQL:
   ```bash
   pip install psycopg2-binary
   ```

   For SQLite (development only):
   ```bash
   # No driver needed, built-in to Python
   # But update DATABASE_URL to:
   DATABASE_URL=sqlite:///./claims_db.db
   ```

3. **Check your .env file**:
   ```env
   DATABASE_URL=postgresql://username:password@localhost:5432/claims_db
   ```
   
   Make sure:
   - No spaces around `=`
   - Correct format: `postgresql://` (not `postgres://`)
   - Valid credentials and database name

### Error: `Field required [type=missing]` for SECRET_KEY

**Cause**: Missing required environment variables.

**Solution**: Create/update `.env` file:
```env
SECRET_KEY=your-secret-key-here
DATABASE_URL=postgresql://user:pass@localhost:5432/claims_db
```

Generate a secure SECRET_KEY:
```bash
openssl rand -hex 32
```

### Error: `No module named 'psycopg2'`

**Cause**: PostgreSQL driver not installed.

**Solution**:
```bash
pip install psycopg2-binary
```

If that fails (especially on macOS):
```bash
# macOS - install PostgreSQL first
brew install postgresql

# Then install Python driver
pip install psycopg2-binary
```

### Error: `Could not translate host name` or connection errors

**Cause**: Database server not running or incorrect connection details.

**Solutions**:

1. **Check PostgreSQL is running**:
   ```bash
   # macOS
   brew services list | grep postgresql
   
   # Linux
   sudo systemctl status postgresql
   ```

2. **Verify connection details**:
   ```bash
   psql -h localhost -U username -d claims_db
   ```

3. **Test the connection string**:
   ```python
   from config import get_settings
   from sqlalchemy import create_engine
   
   settings = get_settings()
   engine = create_engine(settings.DATABASE_URL)
   engine.connect()
   ```

### Error: `target_metadata is None` during migration

**Cause**: `env.py` not importing models correctly.

**Solution**: Ensure `env.py` has:
```python
from models.database import Base
target_metadata = Base.metadata
```

### Error: `Can't locate revision identified by...`

**Cause**: Database and migration files are out of sync.

**Solutions**:

1. **Check current migration**:
   ```bash
   alembic current
   ```

2. **View migration history**:
   ```bash
   alembic history
   ```

3. **Force stamp to specific revision** (if needed):
   ```bash
   alembic stamp head
   ```

### Error: `No 'script_location' key found`

**Cause**: Missing or corrupted `alembic.ini`.

**Solution**: Ensure `alembic.ini` contains:
```ini
[alembic]
script_location = migrations
```

## Quick Fixes

### For Development (SQLite - No driver needed)

1. Update `.env`:
   ```env
   DATABASE_URL=sqlite:///./claims_db.db
   ```

2. Update `app/models/database.py` to handle SQLite:
   ```python
   # Replace ARRAY with JSON for SQLite compatibility
   from sqlalchemy import JSON as SQLJSON
   diagnosis_codes = Column(SQLJSON)  # Instead of ARRAY(String)
   ```

3. Run migrations:
   ```bash
   alembic upgrade head
   ```

### For Production (PostgreSQL)

1. Install driver:
   ```bash
   pip install psycopg2-binary
   ```

2. Set `.env`:
   ```env
   DATABASE_URL=postgresql://user:password@host:5432/database
   ```

3. Run migrations:
   ```bash
   alembic upgrade head
   ```

## Verification Steps

1. **Check Alembic can find config**:
   ```bash
   alembic current
   ```
   Should show: "No current revision" (if first run) or a revision ID.

2. **Check database connection**:
   ```python
   from db.session import engine
   engine.connect()
   ```
   Should connect without errors.

3. **Check models are imported**:
   ```python
   from models.database import Base, User, ClaimMaster
   assert User.__table__ is not None
   ```

## Database URL Formats

### PostgreSQL
```
postgresql://username:password@localhost:5432/database_name
postgresql+psycopg2://username:password@localhost:5432/database_name
```

### SQLite (Development)
```
sqlite:///./claims_db.db
sqlite:///:memory:  # In-memory database
```

### MySQL (Alternative)
```
mysql://username:password@localhost:3306/database_name
mysql+pymysql://username:password@localhost:3306/database_name
```

## Still Having Issues?

1. **Check all dependencies installed**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Verify Python path**:
   ```bash
   python -c "import sys; print('\n'.join(sys.path))"
   ```
   Should include your project directory.

3. **Check Alembic version**:
   ```bash
   alembic --version
   ```

4. **Run with verbose logging**:
   ```bash
   alembic upgrade head -x verbose=true
   ```

