# LifeGraph Deployment Guide

This guide covers deploying LifeGraph in a production environment.

## Prerequisites

- Docker and Docker Compose v2+
- A domain name with DNS configured
- SSL certificates (Let's Encrypt recommended)
- At least 2GB RAM, 2 CPU cores
- 20GB+ storage for database and media

## Quick Start

```bash
# Clone the repository
git clone https://github.com/your-org/lifegraph.git
cd lifegraph

# Copy and configure environment
cp .env.example .env
# Edit .env with your production values

# Start production stack
docker-compose -f docker-compose.prod.yml up -d
```

## Environment Variables

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `SECRET_KEY` | Django secret key (generate unique) | `your-64-char-random-string` |
| `DB_PASSWORD` | PostgreSQL password | `secure-password-here` |
| `MINIO_ACCESS_KEY` | MinIO access key | `minio-access-key` |
| `MINIO_SECRET_KEY` | MinIO secret key | `minio-secret-key` |
| `ALLOWED_HOSTS` | Comma-separated hosts | `lifegraph.example.com` |
| `FERNET_KEYS` | Encryption key for sensitive data | (generate with command below) |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `CORS_ALLOWED_ORIGINS` | CORS allowed origins | (empty) |
| `CSRF_TRUSTED_ORIGINS` | CSRF trusted origins | (empty) |
| `SECURE_SSL_REDIRECT` | Redirect HTTP to HTTPS | `true` |
| `OPENAI_API_KEY` | OpenAI API key for AI features | (empty) |
| `OAUTH2_CLIENT_ID` | Authentik OAuth2 client ID | (empty) |
| `OAUTH2_CLIENT_SECRET` | Authentik OAuth2 secret | (empty) |
| `OAUTH2_SERVER_URL` | Authentik server URL | (empty) |

### Generating Secret Key

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### Generating Encryption Key

LifeGraph encrypts sensitive personal data (emails, phones, addresses, notes) at rest using Fernet encryption (AES-128-CBC).

```bash
# Using the management command (recommended)
docker-compose exec backend python manage.py generate_encryption_key

# Or manually
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

**CRITICAL**: Back up your encryption key! Data encrypted with this key cannot be recovered without it.

**Key Rotation**: To rotate keys, add the new key before the old key (comma-separated):
```bash
FERNET_KEYS=NEW_KEY_HERE,OLD_KEY_HERE
```

## SSL Configuration

### Using Let's Encrypt with Certbot

```bash
# Install certbot
apt-get install certbot

# Obtain certificate
certbot certonly --standalone -d lifegraph.example.com

# Copy certificates to nginx/ssl
cp /etc/letsencrypt/live/lifegraph.example.com/fullchain.pem nginx/ssl/cert.pem
cp /etc/letsencrypt/live/lifegraph.example.com/privkey.pem nginx/ssl/key.pem
```

### Enable SSL in Nginx

Edit `nginx/conf.d/default.conf`:

1. Uncomment the HTTP to HTTPS redirect block
2. Uncomment the `listen 443 ssl http2` line
3. Uncomment the SSL configuration block

```bash
# Restart nginx
docker-compose -f docker-compose.prod.yml restart nginx
```

## Reverse Proxy Setup

If using an external reverse proxy (Traefik, Caddy, etc.), you may want to:

1. Remove the nginx service from docker-compose.prod.yml
2. Expose backend port 8000 and frontend port 80
3. Configure your reverse proxy to route:
   - `/api/*` → backend:8000
   - `/admin/*` → backend:8000
   - `/static/*` → backend static files
   - `/*` → frontend:80

### Traefik Example

```yaml
# Add labels to services in docker-compose.prod.yml
backend:
  labels:
    - "traefik.enable=true"
    - "traefik.http.routers.backend.rule=Host(`lifegraph.example.com`) && PathPrefix(`/api`, `/admin`)"
    - "traefik.http.services.backend.loadbalancer.server.port=8000"

frontend:
  labels:
    - "traefik.enable=true"
    - "traefik.http.routers.frontend.rule=Host(`lifegraph.example.com`)"
    - "traefik.http.services.frontend.loadbalancer.server.port=80"
```

## Authentik SSO Setup

### 1. Create OAuth2 Provider in Authentik

1. Go to Authentik Admin → Providers → Create
2. Select "OAuth2/OpenID Provider"
3. Configure:
   - Name: LifeGraph
   - Authorization flow: default-provider-authorization-explicit-consent
   - Client type: Confidential
   - Redirect URIs: `https://lifegraph.example.com/accounts/openid_connect/login/callback/`

### 2. Create Application in Authentik

1. Go to Applications → Create
2. Configure:
   - Name: LifeGraph
   - Slug: lifegraph
   - Provider: Select the provider created above

### 3. Configure LifeGraph

Set environment variables:
```bash
OAUTH2_CLIENT_ID=<client-id-from-authentik>
OAUTH2_CLIENT_SECRET=<client-secret-from-authentik>
OAUTH2_SERVER_URL=https://authentik.example.com/application/o/lifegraph/
```

## Backup Configuration

Backups run automatically via cron:
- **Daily**: 2:00 AM (kept for 7 days)
- **Weekly**: 3:00 AM Sunday (kept for 30 days)
- **Monthly**: 4:00 AM 1st of month (kept for 365 days)

### Manual Backup

```bash
# Run backup manually
docker-compose -f docker-compose.prod.yml exec backup backup-all --daily

# View backup logs
docker-compose -f docker-compose.prod.yml logs backup
```

### Restore from Backup

```bash
# List available backups
ls -la backups/postgres/daily/
ls -la backups/minio/daily/

# Restore PostgreSQL
docker-compose -f docker-compose.prod.yml exec backup \
  restore-postgres /backups/postgres/daily/lifegraph_daily_20240101_020000.sql.gz

# Restore MinIO
docker-compose -f docker-compose.prod.yml exec backup \
  restore-minio /backups/minio/daily/lifegraph_daily_20240101_020000.tar.gz
```

### Offsite Backup

For offsite backups, mount an external volume or use rclone:

```bash
# Add to backup service volumes
volumes:
  - /mnt/backup-nas:/backups

# Or use rclone to sync to cloud storage
rclone sync /backups remote:lifegraph-backups
```

## Monitoring

### Health Checks

All services include health checks. Monitor with:

```bash
# Check all service health
docker-compose -f docker-compose.prod.yml ps

# Check specific service
docker inspect --format='{{.State.Health.Status}}' personal_crm-backend-1
```

### Logs

```bash
# View all logs
docker-compose -f docker-compose.prod.yml logs -f

# View specific service logs
docker-compose -f docker-compose.prod.yml logs -f backend

# View last 100 lines
docker-compose -f docker-compose.prod.yml logs --tail=100 backend
```

### Resource Usage

```bash
# View resource usage
docker stats

# View disk usage
docker system df
```

## Scaling

### Horizontal Scaling

For high availability, consider:

1. **Database**: Use managed PostgreSQL (AWS RDS, DigitalOcean Managed DB)
2. **Redis**: Use managed Redis (AWS ElastiCache, Redis Cloud)
3. **Object Storage**: Use S3-compatible storage (AWS S3, DigitalOcean Spaces)
4. **Backend**: Scale workers: `docker-compose -f docker-compose.prod.yml up -d --scale worker=3`

### Resource Limits

Adjust in docker-compose.prod.yml:

```yaml
deploy:
  resources:
    limits:
      memory: 2G
      cpus: '2'
    reservations:
      memory: 1G
      cpus: '1'
```

## Troubleshooting

### Database Connection Issues

```bash
# Check database is running
docker-compose -f docker-compose.prod.yml exec db pg_isready -U lifegraph

# Check database logs
docker-compose -f docker-compose.prod.yml logs db
```

### Backend Not Starting

```bash
# Check backend logs
docker-compose -f docker-compose.prod.yml logs backend

# Run migrations manually
docker-compose -f docker-compose.prod.yml exec backend python manage.py migrate

# Check static files
docker-compose -f docker-compose.prod.yml exec backend python manage.py collectstatic --noinput
```

### Celery Tasks Not Running

```bash
# Check worker logs
docker-compose -f docker-compose.prod.yml logs worker

# Check scheduler logs
docker-compose -f docker-compose.prod.yml logs scheduler

# Inspect Celery
docker-compose -f docker-compose.prod.yml exec worker celery -A lifegraph inspect active
```

### MinIO Issues

```bash
# Check MinIO health
curl http://localhost:9000/minio/health/live

# Check bucket exists
docker-compose -f docker-compose.prod.yml exec minio mc ls local/lifegraph
```

## Updates

### Rolling Updates

```bash
# Pull latest changes
git pull origin main

# Rebuild and restart
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d

# Run migrations
docker-compose -f docker-compose.prod.yml exec backend python manage.py migrate
```

### Zero-Downtime Deployment

For zero-downtime, use blue-green deployment:

1. Deploy new version to separate stack
2. Run migrations
3. Switch load balancer to new stack
4. Tear down old stack

## Security Checklist

- [ ] Generated unique SECRET_KEY
- [ ] Generated and backed up FERNET_KEYS for field encryption
- [ ] Strong DB_PASSWORD and MINIO keys
- [ ] SSL/TLS enabled
- [ ] ALLOWED_HOSTS configured correctly
- [ ] CORS and CSRF origins set
- [ ] Firewall configured (only 80/443 exposed)
- [ ] Regular security updates applied
- [ ] Backup encryption enabled
- [ ] Log rotation configured
- [ ] Rate limiting enabled
- [ ] Validated encryption: `python manage.py generate_encryption_key --validate`
