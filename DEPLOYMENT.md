# 🚢 Deployment Guide

## Development → Production Checklist

### 1. Security Hardening

```bash
# Update .env for production
SECRET_KEY=$(openssl rand -hex 64)  # Stronger key
DATABASE_URL="postgresql://admin:strong-password@postgres-db/crew_scheduler"
DEBUG=false

# Change default passwords!
POSTGRES_PASSWORD=your-super-secure-password
ADMIN_USER_PASSWORD=another-secure-password
```

### 2. Database Setup

```bash
# Create production database
docker exec -it postgres psql -U admin -c "CREATE DATABASE crew_prod;"

# Run init script with production data
docker cp init.sql postgres:/tmp/init.sql
docker exec -i postgres psql -U admin -d crew_prod < /tmp/init.sql
```

### 3. Environment Variables

Required for production:

```bash
DATABASE_URL="postgresql://user:pass@host:5432/dbname"
REDIS_URL="redis://cache-host:6379/0"
SECRET_KEY="strong-secure-key-here"
ENVIRONMENT=production
DEBUG=false
ALLOWED_HOSTS="yourdomain.com,app.yourdomain.com"
```

### 4. Production Docker Build

```bash
# Build with production settings
docker-compose --profile prod build

# Or create production docker-compose.yml
docker-compose -f docker-compose.prod.yml up -d
```

### 5. Health Verification

```bash
# Check all services
docker-compose ps

# Test API health
curl http://localhost:8000/health

# Check database connectivity
docker exec crew-scheduler-app python -c "from app.main import engine; print(engine.connect())"
```

### 6. Monitoring Setup (Optional)

Add to docker-compose.yml:

```yaml
services:
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
  
  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
```

### 7. Backup Strategy

```bash
# Database backup
docker exec postgres pg_dump -U admin crew_scheduler > backup_$(date +%Y%m%d).sql

# Restore from backup
docker exec -i postgres psql -U admin crew_scheduler < backup_20240101.sql
```

### 8. SSL/TLS Configuration (Let's Encrypt)

```bash
# Install certbot
docker run --rm \
  -v /var/lib/docker/volumes/crew-scheduler_postgres_data/_data:/data:rw \
  -v "$(pwd)/certs:/etc/letsencrypt" \
  certbot/certbot certonly --standalone -d yourdomain.com

# Update Nginx config for HTTPS
```

## Cloud Deployment Options

### Option 1: AWS ECS/EKS

```yaml
# docker-compose.prod.yml snippet
app:
  build: .
  deploy:
    replicas: 3
    resources:
      limits:
        cpus: '0.5'
        memory: 512M
  environment_file: .env.production
  secrets:
    - db_password
    - api_key
```

### Option 2: Digital Ocean App Platform

1. Connect your Git repo
2. Add PostgreSQL add-on
3. Add Redis add-on
4. Deploy!

### Option 3: Heroku

```bash
# Add buildpacks
heroku buildpacks:set heroku/python

# Set config vars
heroku config:set DATABASE_URL=postgres://...
heroku config:set SECRET_KEY=...

# Deploy
git push heroku main
```

## Production Recommendations

### Security
- [ ] Change all default passwords
- [ ] Enable HTTPS (SSL/TLS)
- [ ] Restrict CORS origins
- [ ] Set up fail2ban or WAF
- [ ] Enable database connection pooling
- [ ] Implement rate limiting

### Reliability
- [ ] Configure auto-scaling
- [ ] Set up monitoring (Prometheus + Grafana)
- [ ] Configure log aggregation (ELK/Loki)
- [ ] Create backup automation
- [ ] Test disaster recovery

### Performance
- [ ] Enable database query logging
- [ ] Implement Redis caching layer
- [ ] Use CDN for static assets
- [ ] Optimize image size (<100MB)
- [ ] Set up load balancer

---

## Quick Production Deploy

```bash
# 1. Generate strong secrets
openssl rand -hex 64 > .env.production.secret

# 2. Update docker-compose.prod.yml
cp docker-compose.yml docker-compose.prod.yml

# Edit docker-compose.prod.yml:
# - Set DEBUG=false
# - Add healthcheck retries
# - Configure resource limits

# 3. Deploy
docker-compose -f docker-compose.prod.yml up -d

# 4. Verify
curl http://localhost:8000/health
```

---

Need help with a specific deployment target? Check the [Architecture](./ARCHITECTURE.md) document for detailed setup instructions!