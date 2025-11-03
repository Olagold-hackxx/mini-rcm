#!/bin/bash

# PostgreSQL Database Setup Script
# Usage: ./setup_postgres.sh [db_name] [db_user] [db_password]

DB_NAME=${1:-claims_db}
DB_USER=${2:-claims_user}
DB_PASS=${3:-$(openssl rand -base64 12)}

echo "Setting up PostgreSQL database..."
echo "Database: $DB_NAME"
echo "User: $DB_USER"
echo ""

# Check if postgres is running
if ! pg_isready -U postgres > /dev/null 2>&1; then
    echo "❌ PostgreSQL is not running. Please start it first:"
    echo "   brew services start postgresql@15"
    exit 1
fi

# Run setup commands
psql -U postgres <<EOF 2>/dev/null

-- Create database (ignore error if exists)
SELECT 'CREATE DATABASE $DB_NAME'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '$DB_NAME')\gexec

-- Drop user if exists and recreate
DROP USER IF EXISTS $DB_USER;
CREATE USER $DB_USER WITH PASSWORD '$DB_PASS';

-- Grant privileges on database
GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;

-- Connect to database
\c $DB_NAME

-- Grant schema privileges
GRANT ALL ON SCHEMA public TO $DB_USER;
GRANT CREATE ON SCHEMA public TO $DB_USER;

-- Grant privileges on future objects
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO $DB_USER;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO $DB_USER;

EOF

if [ $? -eq 0 ]; then
    echo "✅ Database setup complete!"
    echo ""
    echo "Add this to your .env file:"
    echo "DATABASE_URL=postgresql://$DB_USER:$DB_PASS@localhost:5432/$DB_NAME"
    echo ""
    echo "Password: $DB_PASS"
else
    echo "❌ Setup failed. You may need to run as postgres user or provide password."
    echo "Try: PGPASSWORD=your_postgres_password ./setup_postgres.sh"
fi

