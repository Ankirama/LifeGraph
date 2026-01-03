#!/bin/bash
#
# MinIO Restore Script for LifeGraph
#
# Restores MinIO object storage from a backup archive.
#
# Usage: ./restore-minio.sh <backup_file.tar.gz>
#
# WARNING: This will overwrite existing files in the bucket!
#
# Environment Variables:
#   MINIO_ENDPOINT   - MinIO server endpoint (default: http://minio:9000)
#   MINIO_ACCESS_KEY - MinIO access key (required)
#   MINIO_SECRET_KEY - MinIO secret key (required)
#   MINIO_BUCKET     - Bucket to restore to (default: lifegraph)
#

set -euo pipefail

# Configuration with defaults
MINIO_ENDPOINT="${MINIO_ENDPOINT:-http://minio:9000}"
MINIO_BUCKET="${MINIO_BUCKET:-lifegraph}"

# Validate arguments
if [[ $# -lt 1 ]]; then
    echo "Usage: $0 <backup_file.tar.gz>"
    exit 1
fi

BACKUP_FILE="$1"

# Validate backup file exists
if [[ ! -f "$BACKUP_FILE" ]]; then
    echo "ERROR: Backup file not found: $BACKUP_FILE"
    exit 1
fi

# Validate required environment variables
if [[ -z "${MINIO_ACCESS_KEY:-}" ]]; then
    echo "ERROR: MINIO_ACCESS_KEY environment variable is required"
    exit 1
fi

if [[ -z "${MINIO_SECRET_KEY:-}" ]]; then
    echo "ERROR: MINIO_SECRET_KEY environment variable is required"
    exit 1
fi

echo "=== LifeGraph MinIO Restore ==="
echo "Backup file: $BACKUP_FILE"
echo "Target bucket: $MINIO_BUCKET"
echo ""
echo "WARNING: This will overwrite existing files in the bucket!"
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
if ! tar -tzf "$BACKUP_FILE" >/dev/null 2>&1; then
    echo "ERROR: Backup file is corrupted"
    exit 1
fi
echo "Backup file integrity verified"

# Create temporary directory for extraction
TEMP_DIR=$(mktemp -d)
trap "rm -rf $TEMP_DIR" EXIT

# Extract backup
echo "Extracting backup..."
tar -xzf "$BACKUP_FILE" -C "$TEMP_DIR"

# Find extracted directory
EXTRACTED_DIR=$(find "$TEMP_DIR" -mindepth 1 -maxdepth 1 -type d | head -1)
if [[ -z "$EXTRACTED_DIR" ]]; then
    echo "ERROR: No directory found in backup archive"
    exit 1
fi

# Count files to restore
FILE_COUNT=$(find "$EXTRACTED_DIR" -type f | wc -l)
echo "Files to restore: $FILE_COUNT"

# Configure mc (MinIO Client)
echo "Configuring MinIO client..."
mc alias set lifegraph_restore "$MINIO_ENDPOINT" "$MINIO_ACCESS_KEY" "$MINIO_SECRET_KEY" --api S3v4 >/dev/null 2>&1

# Create bucket if it doesn't exist
echo "Ensuring bucket exists..."
mc mb --ignore-existing "lifegraph_restore/$MINIO_BUCKET" >/dev/null 2>&1 || true

# Restore files
echo "Restoring files to bucket..."
mc mirror "$EXTRACTED_DIR" "lifegraph_restore/$MINIO_BUCKET" --overwrite 2>&1

# Verify restore
RESTORED_COUNT=$(mc ls --recursive "lifegraph_restore/$MINIO_BUCKET" 2>/dev/null | wc -l)

# Clean up mc alias
mc alias rm lifegraph_restore >/dev/null 2>&1 || true

echo ""
echo "=== Restore Complete ==="
echo "Bucket: $MINIO_BUCKET"
echo "Files restored: $RESTORED_COUNT"
echo ""
