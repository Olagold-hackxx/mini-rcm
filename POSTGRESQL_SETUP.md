# PostgreSQL Setup and Permission Issues

## Error: `permission denied for schema public`

This error occurs when the database user doesn't have permissions to create tables in the `public` schema.

## Solutions

### Option 1: Grant Permissions to User (Recommended)

Connect to PostgreSQL as a superuser (usually `postgres`) and grant permissions:

```bash
# Connect as postgres superuser
psql -U postgres -d claims_db

# Or if postgres user requires password
psql -U postgres -h localhost -d claims_db
```

Then run these SQL commands:

```sql
-- Grant usage on schema
GRANT USAGE ON SCHEMA public TO your_username;

-- Grant create privileges
GRANT CREATE ON SCHEMA public TO your_username;

-- Grant all privileges on existing tables (if any)
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO your_username;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO your_username;

-- Grant privileges on future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO your_username;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO your_username;
```

Replace `your_username` with the username from your `DATABASE_URL`.

### Option 2: Use Superuser Connection (Development Only)

For development, you can temporarily use the `postgres` superuser:

Update your `.env`:
```env
DATABASE_URL=postgresql://postgres:postgres_password@localhost:5432/claims_db
```

**⚠️ Warning**: Never use superuser in production!

### Option 3: Create Database and User Properly

Set up PostgreSQL from scratch with proper permissions:

```bash
# Connect as postgres superuser
psql -U postgres

# Create database
CREATE DATABASE claims_db;

# Create user with password
CREATE USER claims_user WITH PASSWORD 'your_secure_password';

# Grant privileges
GRANT ALL PRIVILEGES ON DATABASE claims_db TO claims_user;

# Connect to the database
\c claims_db

# Grant schema privileges
GRANT ALL ON SCHEMA public TO claims_user;
GRANT CREATE ON SCHEMA public TO claims_user;
```

Then update `.env`:
```env
DATABASE_URL=postgresql://claims_user:your_secure_password@localhost:5432/claims_db
```

### Option 4: Use a Different Schema

Create and use a custom schema:

```sql
-- Connect as postgres
psql -U postgres -d claims_db

-- Create new schema
CREATE SCHEMA IF NOT EXISTS claims;

-- Grant privileges
GRANT ALL ON SCHEMA claims TO your_username;
```

Update `alembic/env.py` to use the schema:

```python
from alembic import context

config = context.config

# Add schema to search path
context.configure(
    # ... other config ...
    version_table_schema='claims',
    include_schemas=True,
)
```

And in your models:

```python
from sqlalchemy.schema import CreateSchema

# In env.py before creating tables
context.execute(CreateSchema('claims', if_not_exists=True))
```

### Option 5: Use SQLite for Development

If PostgreSQL permissions are too complex, use SQLite for development:

1. **Update `.env`**:
   ```env
   DATABASE_URL=sqlite:///./claims_db.db
   ```

2. **Update migration for SQLite compatibility**:
   - Change `ARRAY(String)` to `JSON` in models (SQLite doesn't support arrays)
   - Or handle in migration script

3. **Run migrations**:
   ```bash
   alembic upgrade head
   ```

## Quick Fix Script

Create a setup script `setup_db.sh`:

```bash
#!/bin/bash

DB_NAME=${1:-claims_db}
DB_USER=${2:-claims_user}
DB_PASS=${3:-change_me}

# Connect as postgres and setup
psql -U postgres <<EOF
CREATE DATABASE $DB_NAME;
CREATE USER $DB_USER WITH PASSWORD '$DB_PASS';
GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;
\c $DB_NAME
GRANT ALL ON SCHEMA public TO $DB_USER;
GRANT CREATE ON SCHEMA public TO $DB_USER;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO $DB_USER;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO $DB_USER;
EOF

echo "Database $DB_NAME created with user $DB_USER"
echo "Update your .env: DATABASE_URL=postgresql://$DB_USER:$DB_PASS@localhost:5432/$DB_NAME"
```

Make it executable:
```bash
chmod +x setup_db.sh
./setup_db.sh
```

## Verify Permissions

Check if your user has the right permissions:

```sql
-- Connect to your database
psql -U your_username -d claims_db

-- Check schema privileges
\dn+

-- Check your privileges
SELECT 
    grantee, 
    privilege_type 
FROM information_schema.role_table_grants 
WHERE grantee = 'your_username';
```

## Common PostgreSQL Commands

```bash
# List all databases
psql -U postgres -l

# List all users
psql -U postgres -c "\du"

# Drop and recreate database (careful!)
psql -U postgres -c "DROP DATABASE claims_db;"
psql -U postgres -c "CREATE DATABASE claims_db;"

# Reset user password
psql -U postgres -c "ALTER USER your_username WITH PASSWORD 'new_password';"
```

## macOS Specific: Install PostgreSQL

```bash
# Install via Homebrew
brew install postgresql@15

# Start service
brew services start postgresql@15

# Create user (default postgres user has no password initially)
psql postgres
```

Then follow Option 1 or 3 above.

## Production Recommendations

1. **Never use superuser** (`postgres`) in production
2. **Create dedicated user** with minimal required permissions
3. **Use connection pooling** (already configured in your app)
4. **Restrict network access** - only allow localhost or specific IPs
5. **Use strong passwords**
6. **Enable SSL** for remote connections

```env
# Production .env example
DATABASE_URL=postgresql://claims_user:secure_password@db_host:5432/claims_db?sslmode=require
```

## Troubleshooting

### Issue: "role does not exist"

```sql
-- Create the role
CREATE ROLE your_username WITH LOGIN PASSWORD 'password';
```

### Issue: "database does not exist"

```sql
-- Create database
CREATE DATABASE claims_db;
```

### Issue: "password authentication failed"

Check:
1. Password in `.env` matches PostgreSQL user password
2. `pg_hba.conf` allows password authentication
3. User exists: `\du` in psql

### Issue: Connection refused

Check:
1. PostgreSQL is running: `brew services list` (macOS) or `systemctl status postgresql` (Linux)
2. Port 5432 is correct
3. Firewall isn't blocking

