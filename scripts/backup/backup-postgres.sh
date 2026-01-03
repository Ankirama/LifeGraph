#!/bin/bash
#
# PostgreSQL Backup Script for LifeGraph
#
# Creates compressed backups of the PostgreSQL database.
# Supports daily/weekly/monthly retention policies.
#
# Usage: ./backup-postgres.sh [--daily|--weekly|--monthly]
#
# Environment Variables:
#   BACKUP_DIR       - Directory to store backups (default: /backups/postgres)
#   RETENTION_DAILY  - Days to keep daily backups (default: 7)
#   RETENTION_WEEKLY - Days to keep weekly backups (default: 30)
#   RETENTION_MONTHLY - Days to keep monthly backups (default: 365)
#   POSTGRES_HOST    - Database host (default: db)
#   POSTGRES_PORT    - Database port (default: 5432)
#   POSTGRES_DB      - Database name (default: lifegraph)
#   POSTGRES_USER    - Database user (default: lifegraph)
#   PGPASSWORD       - Database password (required)
#

set -euo pipefail

# Configuration with defaults
BACKUP_DIR="${BACKUP_DIR:-/backups/postgres}"
RETENTION_DAILY="${RETENTION_DAILY:-7}"
RETENTION_WEEKLY="${RETENTION_WEEKLY:-30}"
RETENTION_MONTHLY="${RETENTION_MONTHLY:-365}"

POSTGRES_HOST="${POSTGRES_HOST:-db}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
POSTGRES_DB="${POSTGRES_DB:-lifegraph}"
POSTGRES_USER="${POSTGRES_USER:-lifegraph}"

# Validate PGPASSWORD is set
if [[ -z "${PGPASSWORD:-}" ]]; then
    echo "ERROR: PGPASSWORD environment variable is required"
    exit 1
fi

# Parse backup type argument
BACKUP_TYPE="${1:-daily}"
case "$BACKUP_TYPE" in
    --daily)
        BACKUP_TYPE="daily"
        RETENTION_DAYS="$RETENTION_DAILY"
        ;;
    --weekly)
        BACKUP_TYPE="weekly"
        RETENTION_DAYS="$RETENTION_WEEKLY"
        ;;
    --monthly)
        BACKUP_TYPE="monthly"
        RETENTION_DAYS="$RETENTION_MONTHLY"
        ;;
    *)
        BACKUP_TYPE="daily"
        RETENTION_DAYS="$RETENTION_DAILY"
        ;;
esac

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR/$BACKUP_TYPE"

# Generate backup filename with timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/$BACKUP_TYPE/lifegraph_${BACKUP_TYPE}_${TIMESTAMP}.sql.gz"
CHECKSUM_FILE="$BACKUP_FILE.sha256"

echo "=== LifeGraph PostgreSQL Backup ==="
echo "Type: $BACKUP_TYPE"
echo "Timestamp: $TIMESTAMP"
echo "Target: $BACKUP_FILE"
echo ""

# Perform the backup
echo "Starting backup..."
pg_dump \
    -h "$POSTGRES_HOST" \
    -p "$POSTGRES_PORT" \
    -U "$POSTGRES_USER" \
    -d "$POSTGRES_DB" \
    --format=custom \
    --compress=9 \
    --verbose \
    2>&1 | gzip > "$BACKUP_FILE"

# Verify backup was created
if [[ ! -f "$BACKUP_FILE" ]]; then
    echo "ERROR: Backup file was not created"
    exit 1
fi

# Get backup size
BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
echo "Backup size: $BACKUP_SIZE"

# Generate checksum
sha256sum "$BACKUP_FILE" > "$CHECKSUM_FILE"
echo "Checksum generated: $CHECKSUM_FILE"

# Verify backup integrity (quick check)
echo "Verifying backup..."
if gzip -t "$BACKUP_FILE" 2>/dev/null; then
    echo "Backup integrity verified"
else
    echo "ERROR: Backup integrity check failed"
    rm -f "$BACKUP_FILE" "$CHECKSUM_FILE"
    exit 1
fi

# Clean up old backups based on retention policy
echo ""
echo "Cleaning up old backups (keeping last $RETENTION_DAYS days)..."
find "$BACKUP_DIR/$BACKUP_TYPE" -name "*.sql.gz" -mtime +$RETENTION_DAYS -delete 2>/dev/null || true
find "$BACKUP_DIR/$BACKUP_TYPE" -name "*.sha256" -mtime +$RETENTION_DAYS -delete 2>/dev/null || true

# Count remaining backups
BACKUP_COUNT=$(find "$BACKUP_DIR/$BACKUP_TYPE" -name "*.sql.gz" | wc -l)
echo "Remaining backups: $BACKUP_COUNT"

echo ""
echo "=== Backup Complete ==="
echo "File: $BACKUP_FILE"
echo "Size: $BACKUP_SIZE"
echo "Type: $BACKUP_TYPE"
echo ""
