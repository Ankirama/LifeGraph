#!/bin/bash
# MinIO bucket initialization script for LifeGraph

set -e

MINIO_HOST=${MINIO_HOST:-"minio:9000"}
MINIO_ACCESS_KEY=${MINIO_ACCESS_KEY:-"minioadmin"}
MINIO_SECRET_KEY=${MINIO_SECRET_KEY:-"minioadmin"}
BUCKET_NAME=${BUCKET_NAME:-"lifegraph"}

echo "Waiting for MinIO to be ready..."
until curl -sf "http://${MINIO_HOST}/minio/health/ready"; do
    sleep 1
done

echo "Configuring MinIO client..."
mc alias set myminio "http://${MINIO_HOST}" "${MINIO_ACCESS_KEY}" "${MINIO_SECRET_KEY}"

echo "Creating bucket: ${BUCKET_NAME}"
mc mb --ignore-existing "myminio/${BUCKET_NAME}"

echo "Setting bucket policy to private..."
mc anonymous set none "myminio/${BUCKET_NAME}"

echo "MinIO initialization complete!"
