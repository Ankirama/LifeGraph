#!/bin/bash
#
# Complete Backup Script for LifeGraph
#
# Runs both PostgreSQL and MinIO backups with the same type.
#
# Usage: ./backup-all.sh [--daily|--weekly|--monthly]
#
# This script is designed to be run via cron:
#   Daily:   0 2 * * * /path/to/backup-all.sh --daily
#   Weekly:  0 3 * * 0 /path/to/backup-all.sh --weekly
#   Monthly: 0 4 1 * * /path/to/backup-all.sh --monthly
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_TYPE="${1:---daily}"

echo "========================================"
echo "LifeGraph Complete Backup"
echo "Type: $BACKUP_TYPE"
echo "Started: $(date)"
echo "========================================"
echo ""

# Run PostgreSQL backup
echo ">>> PostgreSQL Backup"
"$SCRIPT_DIR/backup-postgres.sh" "$BACKUP_TYPE"
PG_STATUS=$?
echo ""

# Run MinIO backup
echo ">>> MinIO Backup"
"$SCRIPT_DIR/backup-minio.sh" "$BACKUP_TYPE"
MINIO_STATUS=$?
echo ""

# Summary
echo "========================================"
echo "Backup Summary"
echo "========================================"
if [[ $PG_STATUS -eq 0 ]]; then
    echo "PostgreSQL: SUCCESS"
else
    echo "PostgreSQL: FAILED (exit code: $PG_STATUS)"
fi

if [[ $MINIO_STATUS -eq 0 ]]; then
    echo "MinIO: SUCCESS"
else
    echo "MinIO: FAILED (exit code: $MINIO_STATUS)"
fi

echo ""
echo "Completed: $(date)"
echo "========================================"

# Exit with error if any backup failed
if [[ $PG_STATUS -ne 0 ]] || [[ $MINIO_STATUS -ne 0 ]]; then
    exit 1
fi

exit 0
