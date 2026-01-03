# Dockerfile for backup service
FROM alpine:3.19

# Install required tools
RUN apk add --no-cache \
    bash \
    postgresql16-client \
    curl \
    gzip \
    tar \
    dcron

# Install MinIO client
RUN curl -o /usr/local/bin/mc https://dl.min.io/client/mc/release/linux-amd64/mc && \
    chmod +x /usr/local/bin/mc

# Create backup directory
RUN mkdir -p /backups

# Copy backup scripts
COPY backup-postgres.sh /usr/local/bin/backup-postgres
COPY backup-minio.sh /usr/local/bin/backup-minio
COPY backup-all.sh /usr/local/bin/backup-all
RUN chmod +x /usr/local/bin/backup-*

# Create crontab for scheduled backups
RUN echo "0 2 * * * /usr/local/bin/backup-all --daily >> /var/log/backup.log 2>&1" > /etc/crontabs/root && \
    echo "0 3 * * 0 /usr/local/bin/backup-all --weekly >> /var/log/backup.log 2>&1" >> /etc/crontabs/root && \
    echo "0 4 1 * * /usr/local/bin/backup-all --monthly >> /var/log/backup.log 2>&1" >> /etc/crontabs/root

# Create log file
RUN touch /var/log/backup.log

# Health check
HEALTHCHECK --interval=60s --timeout=10s --start-period=5s --retries=3 \
    CMD pgrep crond || exit 1

# Volume for backups
VOLUME ["/backups"]

# Default command
CMD ["crond", "-f", "-d", "8"]
