# Docker Registry & Distribution

**Docker registries** are centralized repositories for storing, managing, and distributing container images across development, testing, and production environments.


## Registry Architecture

### Registry Components

```bash
# Registry architecture layers
┌─────────────────────────────────────┐
│        Client (docker CLI)         │ ← Push/Pull Interface
├─────────────────────────────────────┤
│         Registry API v2            │ ← REST API Layer
├─────────────────────────────────────┤
│       Authentication/AuthZ         │ ← Security Layer
├─────────────────────────────────────┤
│        Blob Storage Layer          │ ← Image Layer Storage
├─────────────────────────────────────┤
│         Metadata Store             │ ← Manifest Storage
├─────────────────────────────────────┤
│    Storage Backend (S3/FileSystem) │ ← Physical Storage
└─────────────────────────────────────┘
```

### Registry Types

**Public Registries**: Docker Hub, Quay.io, GitHub Container Registry
**Private Cloud**: AWS ECR, Google GCR, Azure ACR
**Self-Hosted**: Docker Registry, Harbor, Nexus, Artifactory
**Hybrid**: On-premises with cloud replication

### Image Naming Convention

```bash
# Registry image naming structure
[REGISTRY_HOST[:PORT]/]NAMESPACE/REPOSITORY[:TAG]

# Examples
docker.io/library/nginx:alpine        # Docker Hub official
docker.io/company/myapp:v1.0.0        # Docker Hub organization
ghcr.io/username/myapp:latest         # GitHub Container Registry
registry.company.com/team/myapp:dev   # Private registry
```

---

## Docker Hub Operations

### Docker Hub Authentication

```bash
# Login to Docker Hub
docker login                          # Interactive login
docker login -u username -p password  # Non-interactive
echo $DOCKER_PASSWORD | docker login -u $DOCKER_USERNAME --password-stdin

# Store credentials securely
docker login --password-stdin <<< "$DOCKER_PASSWORD"

# Logout
docker logout
docker logout registry.example.com
```

### Image Operations

```bash
# Push to Docker Hub
docker build -t username/myapp:v1.0.0 .
docker push username/myapp:v1.0.0
docker push username/myapp:latest

# Pull from Docker Hub
docker pull username/myapp:v1.0.0
docker pull --all-tags username/myapp

# Tag for multiple registries
docker tag myapp:latest username/myapp:latest
docker tag myapp:latest username/myapp:v1.0.0
docker tag myapp:latest ghcr.io/username/myapp:latest
```

### Docker Hub Repository Management

```bash
# Repository visibility and settings
# Configure via Docker Hub web interface:
# - Repository visibility (public/private)
# - Automated builds from GitHub/Bitbucket
# - Webhooks for deployment triggers
# - Team permissions and access control

# Docker Hub API operations
curl -s "https://hub.docker.com/v2/repositories/username/myapp/tags/" \
  | jq -r '.results[].name'           # List tags

# Delete tag via API
curl -X DELETE \
  -H "Authorization: JWT $HUB_TOKEN" \
  "https://hub.docker.com/v2/repositories/username/myapp/tags/old-tag/"
```

---

## Private Registry Setup

### Basic Docker Registry

```bash
# Run basic registry container
docker run -d \
  --name registry \
  --restart unless-stopped \
  -p 5000:5000 \
  -v registry-data:/var/lib/registry \
  registry:2

# Test registry
docker pull alpine:latest
docker tag alpine:latest localhost:5000/alpine:latest
docker push localhost:5000/alpine:latest

# Registry catalog API
curl -X GET http://localhost:5000/v2/_catalog
curl -X GET http://localhost:5000/v2/alpine/tags/list
```

### Production Registry Configuration

```yaml
# docker-compose.yml for production registry
version: '3.8'

services:
  registry:
    image: registry:2
    container_name: docker-registry
    restart: unless-stopped
    ports:
      - "5000:5000"
    environment:
      REGISTRY_STORAGE_FILESYSTEM_ROOTDIRECTORY: /var/lib/registry
      REGISTRY_AUTH: htpasswd
      REGISTRY_AUTH_HTPASSWD_REALM: Registry Realm
      REGISTRY_AUTH_HTPASSWD_PATH: /auth/htpasswd
      REGISTRY_HTTP_TLS_CERTIFICATE: /certs/domain.crt
      REGISTRY_HTTP_TLS_KEY: /certs/domain.key
      REGISTRY_STORAGE_DELETE_ENABLED: true
      REGISTRY_LOG_LEVEL: info
    volumes:
      - registry-data:/var/lib/registry
      - ./auth:/auth:ro
      - ./certs:/certs:ro
      - ./config.yml:/etc/docker/registry/config.yml:ro
    networks:
      - registry-network

  registry-ui:
    image: joxit/docker-registry-ui:latest
    container_name: registry-ui
    restart: unless-stopped
    ports:
      - "8080:80"
    environment:
      REGISTRY_TITLE: Company Docker Registry
      REGISTRY_URL: https://registry.company.com
      DELETE_IMAGES: true
      SHOW_CONTENT_DIGEST: true
    depends_on:
      - registry
    networks:
      - registry-network

volumes:
  registry-data:
    driver: local

networks:
  registry-network:
    driver: bridge
```

### Advanced Registry Configuration

```yaml
# config.yml - Advanced registry configuration
version: 0.1
log:
  level: info
  formatter: json
  fields:
    service: registry

storage:
  filesystem:
    rootdirectory: /var/lib/registry
  delete:
    enabled: true
  redirect:
    disable: false
  cache:
    blobdescriptor: inmemory

http:
  addr: :5000
  headers:
    X-Content-Type-Options: [nosniff]
    Access-Control-Allow-Origin: ['*']
    Access-Control-Allow-Methods: ['HEAD', 'GET', 'OPTIONS', 'DELETE']
    Access-Control-Allow-Headers: ['Authorization', 'Accept', 'Cache-Control']
  tls:
    certificate: /certs/domain.crt
    key: /certs/domain.key

auth:
  htpasswd:
    realm: basic-realm
    path: /auth/htpasswd

middleware:
  registry:
    - name: cloudfront
      options:
        baseurl: https://cloudfront.company.com
        privatekey: /etc/docker/cloudfront/pk-example.pem
        keypairid: example

health:
  storagedriver:
    enabled: true
    interval: 10s
    threshold: 3

notifications:
  endpoints:
    - name: webhook
      url: https://webhook.company.com/registry-events
      headers:
        Authorization: [Bearer secret-token]
      events:
        - push
        - pull
        - delete
```

### Registry Authentication Setup

```bash
# Create htpasswd file for authentication
docker run --rm --entrypoint htpasswd \
  httpd:2.4 -Bbn username password > auth/htpasswd

# Add additional users
docker run --rm --entrypoint htpasswd \
  httpd:2.4 -Bbn user2 password2 >> auth/htpasswd

# Generate SSL certificates
openssl req -newkey rsa:4096 -nodes -sha256 \
  -keyout certs/domain.key \
  -x509 -days 365 \
  -out certs/domain.crt \
  -subj "/CN=registry.company.com"

# Client configuration for self-signed certs
mkdir -p /etc/docker/certs.d/registry.company.com:5000
cp certs/domain.crt /etc/docker/certs.d/registry.company.com:5000/ca.crt
```

---

## Harbor Enterprise Registry

### Harbor Installation

```bash
# Download Harbor installer
wget https://github.com/goharbor/harbor/releases/download/v2.8.0/harbor-offline-installer-v2.8.0.tgz
tar xzf harbor-offline-installer-v2.8.0.tgz
cd harbor

# Configure Harbor
cp harbor.yml.tmpl harbor.yml
```

```yaml
# harbor.yml configuration
hostname: harbor.company.com

http:
  port: 80

https:
  port: 443
  certificate: /data/cert/server.crt
  private_key: /data/cert/server.key

harbor_admin_password: AdminPassword123

database:
  password: DatabasePassword123
  max_idle_conns: 100
  max_open_conns: 900

data_volume: /data/harbor

trivy:
  ignore_unfixed: false
  skip_update: false
  insecure: false

jobservice:
  max_job_workers: 10

notification:
  webhook_job_max_retry: 3

chart:
  absolute_url: disabled

log:
  level: info
  local:
    rotate_count: 50
    rotate_size: 200M
    location: /var/log/harbor

_version: 2.8.0

proxy:
  http_proxy:
  https_proxy:
  no_proxy:
  components:
    - core
    - jobservice
    - trivy

upload_purging:
  enabled: true
  age: 168h
  interval: 24h
  dryrun: false
```

### Harbor Advanced Features

```bash
# Install Harbor
sudo ./install.sh --with-trivy --with-chartmuseum

# Harbor CLI operations
harbor-cli login harbor.company.com -u admin -p password

# Project management
harbor-cli project create myproject --public=false
harbor-cli project list

# User management
harbor-cli user create developer --password DevPass123 --email dev@company.com
harbor-cli user list

# Repository operations
harbor-cli repository list myproject
harbor-cli artifact list myproject/myapp

# Vulnerability scanning
harbor-cli scan start myproject/myapp:latest
harbor-cli scan report myproject/myapp:latest
```

### Harbor Backup and Migration

```bash
# Harbor backup script
#!/bin/bash
BACKUP_DIR="/backup/harbor/$(date +%Y%m%d_%H%M%S)"
HARBOR_DIR="/data/harbor"

mkdir -p "$BACKUP_DIR"

# Stop Harbor
cd /harbor
docker-compose down

# Backup database
docker run --rm \
  -v postgresql-data:/data \
  -v "$BACKUP_DIR":/backup \
  postgres:13 \
  pg_dump -U postgres harbor > "$BACKUP_DIR/harbor_db.sql"

# Backup Harbor data
tar -czf "$BACKUP_DIR/harbor_data.tar.gz" -C "$HARBOR_DIR" .

# Backup configuration
cp harbor.yml "$BACKUP_DIR/"
cp docker-compose.yml "$BACKUP_DIR/"

# Restart Harbor
docker-compose up -d

echo "Harbor backup completed: $BACKUP_DIR"
```

---

## Cloud Registry Services

### AWS Elastic Container Registry (ECR)

```bash
# ECR authentication
aws ecr get-login-password --region us-west-2 | \
  docker login --username AWS --password-stdin 123456789012.dkr.ecr.us-west-2.amazonaws.com

# Create ECR repository
aws ecr create-repository --repository-name myapp --region us-west-2

# Repository lifecycle policy
aws ecr put-lifecycle-configuration \
  --repository-name myapp \
  --lifecycle-policy-text '{
    "rules": [
      {
        "rulePriority": 1,
        "description": "Keep last 10 images",
        "selection": {
          "tagStatus": "any",
          "countType": "imageCountMoreThan",
          "countNumber": 10
        },
        "action": {
          "type": "expire"
        }
      }
    ]
  }'

# Push to ECR
docker tag myapp:latest 123456789012.dkr.ecr.us-west-2.amazonaws.com/myapp:latest
docker push 123456789012.dkr.ecr.us-west-2.amazonaws.com/myapp:latest
```

### Google Container Registry (GCR)

```bash
# GCR authentication
gcloud auth configure-docker

# Alternative authentication
echo $SERVICE_ACCOUNT_KEY | base64 -d | docker login -u _json_key --password-stdin gcr.io

# Push to GCR
docker tag myapp:latest gcr.io/project-id/myapp:latest
docker push gcr.io/project-id/myapp:latest

# GCR lifecycle management
gcloud container images list-tags gcr.io/project-id/myapp \
  --limit=10 --sort-by=~timestamp
```

### Azure Container Registry (ACR)

```bash
# ACR authentication
az acr login --name myregistry

# Create ACR
az acr create --resource-group myResourceGroup --name myregistry --sku Basic

# Push to ACR
docker tag myapp:latest myregistry.azurecr.io/myapp:latest
docker push myregistry.azurecr.io/myapp:latest

# ACR tasks for automated builds
az acr task create \
  --registry myregistry \
  --name buildapp \
  --image myapp:{{.Run.ID}} \
  --context https://github.com/username/myapp.git \
  --file Dockerfile
```

---

## Registry Security

### Access Control Implementation

```bash
# Registry with RBAC (Harbor example)
# Create user groups
harbor-cli usergroup create developers
harbor-cli usergroup create admins

# Assign permissions
harbor-cli project member add myproject --member developers --role developer
harbor-cli project member add myproject --member admins --role projectadmin

# Robot accounts for automation
harbor-cli robot create project-robot \
  --project myproject \
  --permissions pull,push
```

### Image Vulnerability Scanning

```bash
# Trivy scanning
trivy image myregistry.com/myapp:latest
trivy image --format json myregistry.com/myapp:latest > scan-results.json

# Clair scanning (with Harbor)
curl -X POST "https://harbor.company.com/api/v2.0/projects/myproject/repositories/myapp/artifacts/latest/scan"

# Snyk scanning
snyk container test myregistry.com/myapp:latest
snyk container monitor myregistry.com/myapp:latest
```

### Content Trust and Signing

```bash
# Enable Docker Content Trust
export DOCKER_CONTENT_TRUST=1

# Initialize trust for repository
docker trust key generate user
docker trust signer add --key user.pub user myregistry.com/myapp

# Sign and push image
docker build -t myregistry.com/myapp:signed .
docker push myregistry.com/myapp:signed

# Verify signatures
docker trust inspect myregistry.com/myapp:signed

# Notary operations
notary init myregistry.com/myapp
notary publish myregistry.com/myapp
notary list myregistry.com/myapp
```

### Registry Security Hardening

```yaml
# Security-focused registry configuration
version: 0.1

storage:
  filesystem:
    rootdirectory: /var/lib/registry
  delete:
    enabled: false  # Disable deletion in production

http:
  addr: :5000
  headers:
    X-Content-Type-Options: [nosniff]
    Strict-Transport-Security: [max-age=31536000; includeSubDomains]
    X-Frame-Options: [DENY]
    Content-Security-Policy: [default-src 'self']
  tls:
    certificate: /certs/domain.crt
    key: /certs/domain.key
    minimumtls: tls1.2

auth:
  htpasswd:
    realm: secure-registry
    path: /auth/htpasswd

validation:
  manifests:
    urls:
      allow:
        - ^https://
      deny:
        - ^http://

health:
  storagedriver:
    enabled: true
    interval: 10s
    threshold: 3
```

---

## Image Distribution Strategies

### Multi-Registry Replication

```bash
# Registry replication script
#!/bin/bash
set -euo pipefail

SOURCE_REGISTRY="registry.company.com"
TARGET_REGISTRIES=("backup-registry.company.com" "dr-registry.company.com")
REPOSITORIES=("myapp" "api" "worker")

replicate_image() {
    local repo=$1
    local tag=$2
    local source_image="${SOURCE_REGISTRY}/${repo}:${tag}"

    echo "Replicating ${source_image}"

    # Pull from source
    docker pull "${source_image}"

    # Push to each target registry
    for target_registry in "${TARGET_REGISTRIES[@]}"; do
        local target_image="${target_registry}/${repo}:${tag}"
        docker tag "${source_image}" "${target_image}"
        docker push "${target_image}"
        echo "✓ Replicated to ${target_image}"
    done
}

# Replicate latest images
for repo in "${REPOSITORIES[@]}"; do
    replicate_image "$repo" "latest"
    replicate_image "$repo" "$(date +%Y%m%d)"
done
```

### Geographic Distribution

```yaml
# Global registry distribution with CloudFront
version: 0.1

storage:
  s3:
    accesskey: $S3_ACCESS_KEY
    secretkey: $S3_SECRET_KEY
    region: us-west-2
    bucket: company-docker-registry
    encrypt: true
    secure: true
    v4auth: true

middleware:
  storage:
    - name: cloudfront
      options:
        baseurl: https://d123456789.cloudfront.net
        privatekey: /etc/docker/cloudfront/private-key.pem
        keypairid: APKAEIBAERJR2EXAMPLE

# Regional registry endpoints
# US East: registry-east.company.com
# US West: registry-west.company.com
# Europe: registry-eu.company.com
# Asia: registry-asia.company.com
```

### CI/CD Integration

```yaml
# GitLab CI registry integration
stages:
  - build
  - test
  - security
  - deploy

variables:
  REGISTRY: registry.company.com
  IMAGE_NAME: $REGISTRY/$CI_PROJECT_PATH
  IMAGE_TAG: $CI_COMMIT_SHA

before_script:
  - echo $CI_REGISTRY_PASSWORD | docker login -u $CI_REGISTRY_USER --password-stdin $REGISTRY

build:
  stage: build
  script:
    - docker build -t $IMAGE_NAME:$IMAGE_TAG .
    - docker tag $IMAGE_NAME:$IMAGE_TAG $IMAGE_NAME:latest
    - docker push $IMAGE_NAME:$IMAGE_TAG
    - docker push $IMAGE_NAME:latest

security-scan:
  stage: security
  script:
    - trivy image --exit-code 1 --severity CRITICAL $IMAGE_NAME:$IMAGE_TAG

deploy:
  stage: deploy
  script:
    - kubectl set image deployment/myapp myapp=$IMAGE_NAME:$IMAGE_TAG
  only:
    - main
```

---

## Registry High Availability

### Load Balanced Registry Setup

```yaml
# HA Registry with Redis backend
version: '3.8'

services:
  redis:
    image: redis:7-alpine
    container_name: registry-redis
    restart: unless-stopped
    volumes:
      - redis-data:/data
    networks:
      - registry-network

  registry-1:
    image: registry:2
    container_name: registry-node-1
    restart: unless-stopped
    environment:
      REGISTRY_STORAGE_CACHE_BLOBDESCRIPTOR: redis
      REGISTRY_STORAGE_CACHE_BLOBDESCRIPTORSIZE: 10000
      REGISTRY_REDIS_ADDR: redis:6379
      REGISTRY_REDIS_DB: 0
    volumes:
      - registry-data:/var/lib/registry
      - ./config.yml:/etc/docker/registry/config.yml:ro
    networks:
      - registry-network
    depends_on:
      - redis

  registry-2:
    image: registry:2
    container_name: registry-node-2
    restart: unless-stopped
    environment:
      REGISTRY_STORAGE_CACHE_BLOBDESCRIPTOR: redis
      REGISTRY_STORAGE_CACHE_BLOBDESCRIPTORSIZE: 10000
      REGISTRY_REDIS_ADDR: redis:6379
      REGISTRY_REDIS_DB: 0
    volumes:
      - registry-data:/var/lib/registry
      - ./config.yml:/etc/docker/registry/config.yml:ro
    networks:
      - registry-network
    depends_on:
      - redis

  nginx:
    image: nginx:alpine
    container_name: registry-lb
    restart: unless-stopped
    ports:
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./certs:/etc/nginx/certs:ro
    networks:
      - registry-network
    depends_on:
      - registry-1
      - registry-2

volumes:
  registry-data:
  redis-data:

networks:
  registry-network:
    driver: bridge
```

### NGINX Load Balancer Configuration

```nginx
# nginx.conf for registry load balancing
events {
    worker_connections 1024;
}

http {
    upstream registry {
        server registry-1:5000 max_fails=3 fail_timeout=30s;
        server registry-2:5000 max_fails=3 fail_timeout=30s;
        keepalive 32;
    }

    map $upstream_http_docker_distribution_api_version $docker_distribution_api_version {
        '' 'registry/2.0';
    }

    server {
        listen 443 ssl http2;
        server_name registry.company.com;

        ssl_certificate /etc/nginx/certs/domain.crt;
        ssl_certificate_key /etc/nginx/certs/domain.key;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers HIGH:!aNULL:!MD5;

        client_max_body_size 0;
        chunked_transfer_encoding on;

        location /v2/ {
            proxy_pass http://registry;
            proxy_set_header Host $http_host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_read_timeout 900;
            proxy_buffering off;
        }

        location /health {
            access_log off;
            return 200 "healthy\n";
            add_header Content-Type text/plain;
        }
    }
}
```

---

## Registry Maintenance

### Storage Cleanup and Optimization

```bash
# Registry garbage collection
docker exec registry bin/registry garbage-collect \
  --delete-untagged=true \
  /etc/docker/registry/config.yml

# Harbor garbage collection
curl -X POST "https://harbor.company.com/api/v2.0/system/gc/schedule" \
  -H "Authorization: Basic $(echo -n admin:password | base64)" \
  -H "Content-Type: application/json" \
  -d '{"schedule": {"type": "Daily", "cron": "0 2 * * *"}}'

# Manual storage cleanup script
#!/bin/bash
REGISTRY_DATA="/var/lib/registry"
DAYS_TO_KEEP=30

echo "Starting registry cleanup..."

# Find and remove old blobs
find "$REGISTRY_DATA/docker/registry/v2/blobs" \
  -type f -mtime +$DAYS_TO_KEEP \
  -exec rm {} \;

# Run garbage collection
docker exec registry bin/registry garbage-collect \
  --delete-untagged=true \
  /etc/docker/registry/config.yml

echo "Registry cleanup completed"
```

### Monitoring and Metrics

```yaml
# Registry monitoring with Prometheus
version: '3.8'

services:
  registry:
    image: registry:2
    environment:
      REGISTRY_HTTP_DEBUG_ADDR: :5001
      REGISTRY_HTTP_DEBUG_PROMETHEUS_ENABLED: true
    ports:
      - "5000:5000"
      - "5001:5001"  # Metrics endpoint

  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml:ro
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'

  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    environment:
      GF_SECURITY_ADMIN_PASSWORD: admin
    volumes:
      - grafana-data:/var/lib/grafana

volumes:
  grafana-data:
```

### Backup and Disaster Recovery

```bash
# Comprehensive registry backup script
#!/bin/bash
set -euo pipefail

BACKUP_DIR="/backup/registry/$(date +%Y%m%d_%H%M%S)"
REGISTRY_DATA="/var/lib/registry"
S3_BUCKET="company-registry-backups"

mkdir -p "$BACKUP_DIR"

echo "Starting registry backup..."

# Stop registry for consistent backup
docker-compose stop registry

# Backup registry data
tar -czf "$BACKUP_DIR/registry_data.tar.gz" \
  -C "$(dirname $REGISTRY_DATA)" \
  "$(basename $REGISTRY_DATA)"

# Backup configuration
cp docker-compose.yml "$BACKUP_DIR/"
cp -r config/ "$BACKUP_DIR/"
cp -r certs/ "$BACKUP_DIR/"

# Upload to S3
aws s3 sync "$BACKUP_DIR" "s3://$S3_BUCKET/$(basename $BACKUP_DIR)/"

# Restart registry
docker-compose start registry

# Cleanup old local backups (keep 7 days)
find /backup/registry -type d -mtime +7 -exec rm -rf {} +

echo "Registry backup completed: $BACKUP_DIR"
```

---

## Troubleshooting

### Common Registry Issues

#### Authentication Problems

```bash
# Debug authentication
docker login registry.company.com -u username
cat ~/.docker/config.json

# Test registry connectivity
curl -v https://registry.company.com/v2/

# Check certificate issues
openssl s_client -connect registry.company.com:443 -servername registry.company.com

# Registry logs
docker logs registry 2>&1 | grep -i auth
journalctl -u harbor-core -f
```

#### Push/Pull Failures

```bash
# Debug network issues
docker pull registry.company.com/myapp:latest -v
docker push registry.company.com/myapp:latest -v

# Check disk space
df -h /var/lib/registry
docker system df

# Registry API debugging
curl -X GET https://registry.company.com/v2/_catalog
curl -X GET https://registry.company.com/v2/myapp/tags/list
```

#### Performance Issues

```bash
# Monitor registry performance
docker stats registry
iostat -x 1
netstat -i

# Registry metrics analysis
curl -s http://localhost:5001/metrics | grep registry_

# Database performance (Harbor)
docker exec harbor-db psql -U postgres -d registry -c "
  SELECT schemaname,tablename,attname,n_distinct,correlation
  FROM pg_stats WHERE tablename='artifact';"
```

### Diagnostic Scripts

```bash
#!/bin/bash
# Registry health check script

REGISTRY_URL="https://registry.company.com"
REGISTRY_API="$REGISTRY_URL/v2"

echo "=== Registry Health Check ==="

# Check registry availability
if curl -sf "$REGISTRY_API/" >/dev/null; then
    echo "✓ Registry is accessible"
else
    echo "✗ Registry is not accessible"
    exit 1
fi

# Check authentication
if curl -sf -u "$REGISTRY_USER:$REGISTRY_PASS" "$REGISTRY_API/_catalog" >/dev/null; then
    echo "✓ Authentication successful"
else
    echo "✗ Authentication failed"
fi

# Check storage space
REGISTRY_CONTAINER=$(docker ps -q -f name=registry)
if [[ -n "$REGISTRY_CONTAINER" ]]; then
    DISK_USAGE=$(docker exec "$REGISTRY_CONTAINER" df -h /var/lib/registry | tail -1 | awk '{print $5}')
    echo "Registry disk usage: $DISK_USAGE"
fi

# Check recent activity
echo -e "\nRecent registry logs:"
docker logs --tail 10 registry 2>/dev/null || \
journalctl -u harbor-core --since "1 hour ago" --no-pager -n 5
```

---

## Best Practices

### Production Registry Deployment

```bash
# 1. Use HTTPS with valid certificates
# 2. Implement proper authentication and authorization
# 3. Enable vulnerability scanning
# 4. Set up monitoring and alerting
# 5. Implement backup and disaster recovery
# 6. Use storage backend appropriate for scale (S3, GCS, etc.)
# 7. Configure proper logging and auditing
# 8. Implement content trust and image signing
# 9. Set up geographic distribution for global teams
# 10. Regular security updates and maintenance
```

### Security Best Practices

```yaml
# Security-focused registry deployment
services:
  registry:
    image: registry:2
    environment:
      # Force HTTPS
      REGISTRY_HTTP_TLS_CERTIFICATE: /certs/domain.crt
      REGISTRY_HTTP_TLS_KEY: /certs/domain.key

      # Authentication required
      REGISTRY_AUTH: htpasswd
      REGISTRY_AUTH_HTPASSWD_PATH: /auth/htpasswd

      # Disable HTTP API
      REGISTRY_HTTP_SECRET: random-secret-string

      # Enable deletion for cleanup
      REGISTRY_STORAGE_DELETE_ENABLED: true

      # Logging
      REGISTRY_LOG_LEVEL: warn
      REGISTRY_LOG_FORMATTER: json

    # Security options
    read_only: true
    user: "1000:1000"
    cap_drop:
      - ALL
    security_opt:
      - no-new-privileges:true
```

### Performance Optimization

```bash
# 1. Use SSD storage for registry data
# 2. Implement Redis cache for metadata
# 3. Use CDN for image distribution
# 4. Enable compression for image layers
# 5. Implement proper load balancing
# 6. Monitor and tune database performance
# 7. Use regional registries for geographic distribution
# 8. Implement image layer deduplication
# 9. Regular garbage collection
# 10. Optimize network connectivity
```

---

## Cross-References

### Essential Reading
- **[[Docker fundamental]]** - Core Docker concepts and architecture
- **[[Docker Commands]]** - CLI operations for registry management
- **[[Docker Security]]** - Registry security and image scanning
- **[[Docker CICD]]** - Registry integration in pipelines

### Advanced Topics
- **[[Docker Compose Production Setup]]** - Registry in production environments
- **[[Docker Performance & Monitoring]]** - Registry performance optimization
- **[[Docker Networking]]** - Registry network configuration

### Quick Navigation
- **Getting Started**: Docker fundamental → Docker Registry & Distribution → Docker Commands
- **Production Setup**: Docker Registry & Distribution → Docker Security → Docker Compose Production Setup
- **CI/CD Integration**: Docker Registry & Distribution → Docker CICD → Docker Performance & Monitoring

---

*This focused guide provides comprehensive knowledge for implementing and managing Docker registries in enterprise environments with security, scalability, and reliability.*