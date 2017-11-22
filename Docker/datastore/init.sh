#!/bin/bash
set -e

echo "creating datastore user and database.."

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
    -- Create a group
CREATE ROLE readaccess;

-- Grant access to existing tables
GRANT USAGE ON SCHEMA public TO readaccess;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO readaccess;

-- Grant access to future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO readaccess;

-- Create a final user with password
CREATE USER $DATASTORE_USER_READ WITH PASSWORD '$DATASTORE_USER_READ_PASSWORD';
GRANT readaccess TO $POSTGRES_DB;

EOSQL

