#!/bin/bash
#
# PostgreSQL Restore Script for LifeGraph
#
# Restores a PostgreSQL backup from a compressed dump file.
#
# Usage: ./restore-postgres.sh <backup_file.sql.gz>
#
# WARNING: This will DROP and recreate the database!
#
# Environment Variables:
#   POSTGRES_HOST    - Database host (default: db)
#   POSTGRES_PORT    - Database port (default: 5432)
#   POSTGRES_DB      - Database name (default: lifegraph)
#   POSTGRES_USER    - Database user (default: lifegraph)
#   PGPASSWORD       - Database password (required)
#

set -euo pipefail

# Configuration with defaults
POSTGRES_HOST="${POSTGRES_HOST:-db}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
POSTGRES_DB="${POSTGRES_DB:-lifegraph}"
POSTGRES_USER="${POSTGRES_USER:-lifegraph}"

# Validate arguments
if [[ $# -lt 1 ]]; then
    echo "Usage: $0 <backup_file.sql.gz>"
    exit 1
fi

BACKUP_FILE="$1"

# Validate backup file exists
if [[ ! -f "$BACKUP_FILE" ]]; then
    echo "ERROR: Backup file not found: $BACKUP_FILE"
    exit 1
fi

# Validate PGPASSWORD is set
if [[ -z "${PGPASSWORD:-}" ]]; then
    echo "ERROR: PGPASSWORD environment variable is required"
    exit 1
fi

echo "=== LifeGraph PostgreSQL Restore ==="
echo "Backup file: $BACKUP_FILE"
echo "Target database: $POSTGRES_DB"
echo ""
echo "WARNING: This will DROP and recreate the database!"
echo ""

# Prompt for confirmation
read -p "Are you sure you want to continue? (yes/no): " CONFIRM
if [[ "$CONFIRM" != "yes" ]]; then
    echo "Restore cancelled."
    exit 0
fi

# Verify checksum if available
CHECKSUM_FILE="$BACKUP_FILE.sha256"
if [[ -f "$CHECKSUM_FILE" ]]; then
    echo "Verifying backup checksum..."
    if sha256sum -c "$CHECKSUM_FILE" 2>/dev/null; then
        echo "Checksum verified"
    else
        echo "ERROR: Checksum verification failed"
        exit 1
    fi
fi

# Verify backup file integrity
echo "Verifying backup file integrity..."
if ! gzip -t "$BACKUP_FILE" 2>/dev/null; then
    echo "ERROR: Backup file is corrupted"
    exit 1
fi
echo "Backup file integrity verified"

# Create temporary directory for extraction
TEMP_DIR=$(mktemp -d)
TEMP_DUMP="$TEMP_DIR/restore.dump"
trap "rm -rf $TEMP_DIR" EXIT

# Extract backup
echo "Extracting backup..."
gunzip -c "$BACKUP_FILE" > "$TEMP_DUMP"

# Terminate existing connections to the database
echo "Terminating existing connections..."
psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d postgres -c \
    "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '$POSTGRES_DB' AND pid <> pg_backend_pid();" \
    >/dev/null 2>&1 || true

# Drop and recreate database
echo "Dropping and recreating database..."
psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d postgres -c "DROP DATABASE IF EXISTS $POSTGRES_DB;"
psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d postgres -c "CREATE DATABASE $POSTGRES_DB OWNER $POSTGRES_USER;"

# Restore the database
echo "Restoring database..."
pg_restore \
    -h "$POSTGRES_HOST" \
    -p "$POSTGRES_PORT" \
    -U "$POSTGRES_USER" \
    -d "$POSTGRES_DB" \
    --verbose \
    --no-owner \
    --no-privileges \
    "$TEMP_DUMP" 2>&1 || true  # pg_restore may return non-zero on warnings

# Verify restore
echo "Verifying restore..."
TABLE_COUNT=$(psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -t -c \
    "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';")

echo ""
echo "=== Restore Complete ==="
echo "Database: $POSTGRES_DB"
echo "Tables restored: $TABLE_COUNT"
echo ""
echo "NOTE: You may need to run Django migrations to ensure schema is up to date:"
echo "  python manage.py migrate"
echo ""
