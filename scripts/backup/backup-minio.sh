#!/bin/bash
#
# MinIO Backup Script for LifeGraph
#
# Creates compressed backups of MinIO object storage (photos, files).
# Uses mc (MinIO Client) to mirror bucket contents.
#
# Usage: ./backup-minio.sh [--daily|--weekly|--monthly]
#
# Environment Variables:
#   BACKUP_DIR       - Directory to store backups (default: /backups/minio)
#   RETENTION_DAILY  - Days to keep daily backups (default: 7)
#   RETENTION_WEEKLY - Days to keep weekly backups (default: 30)
#   RETENTION_MONTHLY - Days to keep monthly backups (default: 365)
#   MINIO_ENDPOINT   - MinIO server endpoint (default: http://minio:9000)
#   MINIO_ACCESS_KEY - MinIO access key (required)
#   MINIO_SECRET_KEY - MinIO secret key (required)
#   MINIO_BUCKET     - Bucket to backup (default: lifegraph)
#

set -euo pipefail

# Configuration with defaults
BACKUP_DIR="${BACKUP_DIR:-/backups/minio}"
RETENTION_DAILY="${RETENTION_DAILY:-7}"
RETENTION_WEEKLY="${RETENTION_WEEKLY:-30}"
RETENTION_MONTHLY="${RETENTION_MONTHLY:-365}"

MINIO_ENDPOINT="${MINIO_ENDPOINT:-http://minio:9000}"
MINIO_BUCKET="${MINIO_BUCKET:-lifegraph}"

# Validate required environment variables
if [[ -z "${MINIO_ACCESS_KEY:-}" ]]; then
    echo "ERROR: MINIO_ACCESS_KEY environment variable is required"
    exit 1
fi

if [[ -z "${MINIO_SECRET_KEY:-}" ]]; then
    echo "ERROR: MINIO_SECRET_KEY environment variable is required"
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
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_PATH="$BACKUP_DIR/$BACKUP_TYPE/lifegraph_${BACKUP_TYPE}_${TIMESTAMP}"
ARCHIVE_FILE="$BACKUP_PATH.tar.gz"
CHECKSUM_FILE="$ARCHIVE_FILE.sha256"

mkdir -p "$BACKUP_DIR/$BACKUP_TYPE"
mkdir -p "$BACKUP_PATH"

echo "=== LifeGraph MinIO Backup ==="
echo "Type: $BACKUP_TYPE"
echo "Timestamp: $TIMESTAMP"
echo "Target: $ARCHIVE_FILE"
echo ""

# Configure mc (MinIO Client)
echo "Configuring MinIO client..."
mc alias set lifegraph_backup "$MINIO_ENDPOINT" "$MINIO_ACCESS_KEY" "$MINIO_SECRET_KEY" --api S3v4 >/dev/null 2>&1

# Verify bucket exists
echo "Verifying bucket exists..."
if ! mc ls "lifegraph_backup/$MINIO_BUCKET" >/dev/null 2>&1; then
    echo "ERROR: Bucket $MINIO_BUCKET does not exist or is not accessible"
    exit 1
fi

# Get bucket stats before backup
OBJECT_COUNT=$(mc ls --recursive "lifegraph_backup/$MINIO_BUCKET" 2>/dev/null | wc -l)
echo "Objects to backup: $OBJECT_COUNT"

# Mirror bucket contents to local directory
echo "Mirroring bucket contents..."
mc mirror "lifegraph_backup/$MINIO_BUCKET" "$BACKUP_PATH" --overwrite 2>&1

# Create compressed archive
echo "Creating compressed archive..."
cd "$BACKUP_DIR/$BACKUP_TYPE"
tar -czf "$ARCHIVE_FILE" -C "$BACKUP_DIR/$BACKUP_TYPE" "$(basename "$BACKUP_PATH")"

# Remove uncompressed backup directory
rm -rf "$BACKUP_PATH"

# Verify archive was created
if [[ ! -f "$ARCHIVE_FILE" ]]; then
    echo "ERROR: Archive file was not created"
    exit 1
fi

# Get backup size
BACKUP_SIZE=$(du -h "$ARCHIVE_FILE" | cut -f1)
echo "Backup size: $BACKUP_SIZE"

# Generate checksum
sha256sum "$ARCHIVE_FILE" > "$CHECKSUM_FILE"
echo "Checksum generated: $CHECKSUM_FILE"

# Verify archive integrity
echo "Verifying archive..."
if tar -tzf "$ARCHIVE_FILE" >/dev/null 2>&1; then
    echo "Archive integrity verified"
else
    echo "ERROR: Archive integrity check failed"
    rm -f "$ARCHIVE_FILE" "$CHECKSUM_FILE"
    exit 1
fi

# Clean up old backups based on retention policy
echo ""
echo "Cleaning up old backups (keeping last $RETENTION_DAYS days)..."
find "$BACKUP_DIR/$BACKUP_TYPE" -name "*.tar.gz" -mtime +$RETENTION_DAYS -delete 2>/dev/null || true
find "$BACKUP_DIR/$BACKUP_TYPE" -name "*.sha256" -mtime +$RETENTION_DAYS -delete 2>/dev/null || true

# Count remaining backups
BACKUP_COUNT=$(find "$BACKUP_DIR/$BACKUP_TYPE" -name "*.tar.gz" | wc -l)
echo "Remaining backups: $BACKUP_COUNT"

# Clean up mc alias
mc alias rm lifegraph_backup >/dev/null 2>&1 || true

echo ""
echo "=== Backup Complete ==="
echo "File: $ARCHIVE_FILE"
echo "Size: $BACKUP_SIZE"
echo "Objects: $OBJECT_COUNT"
echo "Type: $BACKUP_TYPE"
echo ""
