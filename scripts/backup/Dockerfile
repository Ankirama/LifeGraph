# Dockerfile for backup service
FROM alpine:3.19

# Install required tools
RUN apk add --no-cache \
    bash \
    postgresql16-client \
    curl \
    gzip \
    tar

# Install supercronic (container-friendly cron)
ARG SUPERCRONIC_URL=https://github.com/aptible/supercronic/releases/download/v0.2.29/supercronic-linux-amd64
ARG SUPERCRONIC_SHA1SUM=cd48d45c4b10f3f0bfdd3a57d054cd05ac96812b
RUN curl -fsSLO "$SUPERCRONIC_URL" \
    && echo "${SUPERCRONIC_SHA1SUM}  supercronic-linux-amd64" | sha1sum -c - \
    && chmod +x supercronic-linux-amd64 \
    && mv supercronic-linux-amd64 /usr/local/bin/supercronic

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
RUN echo "0 2 * * * /usr/local/bin/backup-all --daily" > /etc/crontab && \
    echo "0 3 * * 0 /usr/local/bin/backup-all --weekly" >> /etc/crontab && \
    echo "0 4 1 * * /usr/local/bin/backup-all --monthly" >> /etc/crontab

# Health check
HEALTHCHECK --interval=60s --timeout=10s --start-period=5s --retries=3 \
    CMD pgrep supercronic || exit 1

# Volume for backups
VOLUME ["/backups"]

# Default command
CMD ["supercronic", "/etc/crontab"]
