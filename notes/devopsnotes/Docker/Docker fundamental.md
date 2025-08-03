### Core Dockerfile Instructions

#### COPY vs ADD

```dockerfile
# COPY - Simple file/directory copying (preferred)
COPY src/ /app/src/                    # Copy directory
COPY package.json /app/               # Copy single file
COPY --from=builder /app/dist /app/   # Multi-stage copy
COPY --chown=1000:1000 app.jar /app/  # Set ownership during copy

# ADD - Extended functionality (use sparingly)
ADD https://example.com/file.tar.gz /tmp/  # Download and extract
ADD archive.tar.gz /opt/                   # Auto-extract archives
ADD --chown=nginx:nginx web.tar /var/www/  # Extract with ownership

# Best Practices
# ✅ Use COPY for local files
# ✅ Use ADD only for auto-extraction or remote URLs
# ❌ Don't use ADD for simple file copying
```

#### CMD vs ENTRYPOINT

```dockerfile
# CMD - Default command (can be overridden)
CMD ["nginx", "-g", "daemon off;"]        # Exec form (preferred)
CMD nginx -g "daemon off;"                # Shell form

# ENTRYPOINT - Always executed (not overridden)
ENTRYPOINT ["nginx", "-g", "daemon off;"] # Exec form
ENTRYPOINT nginx -g "daemon off;"         # Shell form

# Combined usage (flexible configuration)
ENTRYPOINT ["nginx"]                      # Fixed executable
CMD ["-g", "daemon off;"]                 # Default arguments

# Advanced pattern - entrypoint script
ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["nginx", "-g", "daemon off;"]

# DevOps Best Practice: Entrypoint script example
#!/bin/bash
set -e
# Environment setup
export DATABASE_URL=${DATABASE_URL:-"postgresql://localhost/myapp"}
# Configuration templating
envsubst < /app/config.template > /app/config.yml
# Execute main command
exec "$@"
```

#### Environment Variables and Build Arguments

```dockerfile
# ARG - Build-time variables
ARG NODE_VERSION=18                       # Build argument with default
ARG BUILD_DATE                           # Build argument without default
FROM node:${NODE_VERSION}-alpine

# ENV - Runtime environment variables
ENV NODE_ENV=production                   # Simple assignment
ENV PATH="/app/bin:${PATH}"              # Path modification
ENV DATABASE_URL="" \
    REDIS_URL="" \
    LOG_LEVEL="info"                     # Multi-line assignment

# Build-time to runtime variable passing
ARG VERSION
ENV APP_VERSION=${VERSION}

# DevOps pattern: Multi-environment configuration
ARG ENV=production
ENV ENVIRONMENT=${ENV}
COPY config/app-${ENVIRONMENT}.yml /app/config.yml

# Secrets handling (avoid hardcoding)
# ❌ Bad - hardcoded secret
ENV API_KEY="secret123"
# ✅ Good - runtime secret injection
ENV API_KEY_FILE="/run/secrets/api_key"
```

#### Filesystem Operations

```dockerfile
# WORKDIR - Set working directory
WORKDIR /app                             # Creates directory if not exists
WORKDIR /app/src                        # Nested directories
RUN pwd                                 # Shows /app/src

# USER - Set user context
USER 1000:1000                         # UID:GID format
USER appuser                           # Username format
USER appuser:appgroup                  # User:group format

# RUN - Execute commands during build
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/*      # Clean up in same layer

# Multi-line RUN with line continuation
RUN set -eux; \
    addgroup --gid 1001 appgroup; \
    adduser --uid 1001 --gid 1001 --disabled-password appuser

# DevOps optimization: Layer consolidation
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        python3-dev \
    && pip install -r requirements.txt \
    && apt-get purge -y build-essential python3-dev \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*
```

### Advanced Dockerfile Patterns

#### Multi-stage Builds

```dockerfile
# Multi-stage build for optimized production images
# Stage 1: Build environment
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production && npm cache clean --force
COPY . .
RUN npm run build

# Stage 2: Runtime environment
FROM node:18-alpine AS runtime
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nextjs -u 1001
WORKDIR /app
COPY --from=builder --chown=nextjs:nodejs /app/dist ./dist
COPY --from=builder --chown=nextjs:nodejs /app/node_modules ./node_modules
USER nextjs
EXPOSE 3000
CMD ["node", "dist/server.js"]

# Stage 3: Development environment
FROM builder AS development
ENV NODE_ENV=development
RUN npm install  # Install dev dependencies
EXPOSE 3000
CMD ["npm", "run", "dev"]

# Multi-architecture builds
FROM --platform=$BUILDPLATFORM node:18-alpine AS builder
ARG TARGETPLATFORM
ARG BUILDPLATFORM
RUN echo "Building on $BUILDPLATFORM for $TARGETPLATFORM"
```

#### Advanced Container Configuration

```dockerfile
# EXPOSE - Document exposed ports (metadata only)
EXPOSE 8080                             # Single port
EXPOSE 8080/tcp 8443/tcp               # Multiple TCP ports
EXPOSE 53/udp                          # UDP port

# HEALTHCHECK - Container health monitoring
HEALTHCHECK --interval=30s --timeout=3s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Custom healthcheck script
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD ["/app/healthcheck.sh"]

# ONBUILD - Triggers for child images
ONBUILD COPY . /app/src
ONBUILD RUN make /app/src

# VOLUME - Declare mount points
VOLUME ["/data", "/logs"]              # Multiple volumes
VOLUME /var/lib/mysql                  # Single volume

# Labels for metadata and automation
LABEL maintainer="devops@company.com"
LABEL version="1.0.0"
LABEL description="Production web application"
LABEL org.opencontainers.image.title="MyApp"
LABEL org.opencontainers.image.version="1.0.0"
LABEL org.opencontainers.image.created="2024-01-01T00:00:00Z"
LABEL org.opencontainers.image.revision="abc123"
LABEL org.opencontainers.image.source="https://github.com/company/myapp"
```

### Build Optimization and Best Practices

#### .dockerignore Configuration

```dockerignore
# Version control
.git
.gitignore
.gitattributes

# Documentation
README.md
docs/
*.md

# Development files
.env.local
.env.development
docker-compose.override.yml
Dockerfile*
.dockerignore

# Dependencies (rebuilt in container)
node_modules/
npm-debug.log*
.npm

# Build artifacts
dist/
build/
target/
*.war
*.jar

# IDE and editor files
.vscode/
.idea/
*.swp
*.swo
*~

# OS generated files
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Temporary files
tmp/
temp/
*.tmp
*.temp

# Logs
logs/
*.log

# Test files
test/
tests/
**/*test*
coverage/
.nyc_output

# DevOps specific ignores
terraform/
ansible/
k8s/
.github/
.gitlab-ci.yml
Jenkinsfile
```

#### BuildKit and Advanced Building

```dockerfile
# Enable BuildKit features
# syntax=docker/dockerfile:1.4

FROM alpine:latest

# BuildKit secrets (avoid copying secrets into layers)
RUN --mount=type=secret,id=aws_credentials \
    AWS_SHARED_CREDENTIALS_FILE=/run/secrets/aws_credentials \
    aws s3 cp s3://bucket/file /app/

# BuildKit cache mounts (speed up builds)
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt

RUN --mount=type=cache,target=/var/cache/apt \
    --mount=type=cache,target=/var/lib/apt/lists \
    apt-get update && apt-get install -y python3

# SSH mounts for private repositories
RUN --mount=type=ssh \
    git clone git@github.com:private/repo.git /app

# Bind mounts for build context
RUN --mount=type=bind,source=.,target=/src \
    cp /src/config.yml /app/
```

#### Build Context Optimization

```bash
# Docker build commands with BuildKit
export DOCKER_BUILDKIT=1

# Basic build with context
docker build -t myapp:latest .

# Build with specific Dockerfile
docker build -f Dockerfile.prod -t myapp:prod .

# Build with build arguments
docker build \
  --build-arg NODE_VERSION=18 \
  --build-arg BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ') \
  -t myapp:$(git rev-parse --short HEAD) .

# Build with secrets
echo "secret_value" | docker build \
  --secret id=my_secret,src=- \
  -t myapp:latest .

# Build with SSH agent forwarding
docker build \
  --ssh default=$SSH_AUTH_SOCK \
  -t myapp:latest .

# Multi-platform builds
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t myapp:latest \
  --push .

# Build with cache from registry
docker build \
  --cache-from myapp:cache \
  --cache-to type=registry,ref=myapp:cache \
  -t myapp:latest .
```

## 🏗️ Image Management and Optimization

### Base Image Selection and Optimization

```dockerfile
# Base image comparison and selection
FROM ubuntu:22.04                      # Full Ubuntu (large, ~72MB)
FROM python:3.11                      # Python official (large, ~900MB)
FROM python:3.11-slim                 # Python slim (~120MB)
FROM python:3.11-alpine               # Alpine-based (~50MB)
FROM gcr.io/distroless/python3        # Distroless (~50MB, no shell)

# Alpine optimizations
FROM alpine:3.18
RUN apk add --no-cache \
    python3 \
    py3-pip \
    && ln -sf python3 /usr/bin/python

# Distroless for maximum security
FROM gcr.io/distroless/java17-debian11
COPY app.jar /app.jar
EXPOSE 8080
ENTRYPOINT ["java", "-jar", "/app.jar"]

# Multi-stage with minimal runtime
FROM golang:1.21-alpine AS builder
WORKDIR /app
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -o main .

FROM scratch
COPY --from=builder /app/main /main
EXPOSE 8080
ENTRYPOINT ["/main"]
```

### Image Tagging Strategies

```bash
# Semantic versioning
docker tag myapp:latest myapp:1.2.3
docker tag myapp:latest myapp:1.2
docker tag myapp:latest myapp:1

# Git-based tagging
docker tag myapp:latest myapp:$(git rev-parse --short HEAD)
docker tag myapp:latest myapp:$(git describe --tags --always)

# Environment-based tagging
docker tag myapp:latest myapp:dev-$(date +%Y%m%d)
docker tag myapp:latest myapp:staging-v1.2.3
docker tag myapp:latest myapp:prod-$(git rev-parse --short HEAD)

# CI/CD pipeline tagging
docker tag myapp:latest myapp:build-${BUILD_NUMBER}
docker tag myapp:latest myapp:pr-${PULL_REQUEST_ID}
docker tag myapp:latest myapp:branch-${BRANCH_NAME//\//-}

# DevOps tagging script
#!/bin/bash
VERSION=$(git describe --tags --always)
COMMIT=$(git rev-parse --short HEAD)
DATE=$(date +%Y%m%d-%H%M%S)

docker build -t myapp:latest .
docker tag myapp:latest myapp:${VERSION}
docker tag myapp:latest myapp:${COMMIT}
docker tag myapp:latest myapp:${DATE}

if [[ "${BRANCH_NAME}" == "main" ]]; then
    docker tag myapp:latest myapp:stable
fi
```

### Image Size Reduction Techniques

```dockerfile
# Technique 1: Layer consolidation
# ❌ Bad - creates multiple layers
RUN apt-get update
RUN apt-get install -y curl
RUN apt-get install -y wget
RUN rm -rf /var/lib/apt/lists/*

# ✅ Good - single layer
RUN apt-get update && \
    apt-get install -y curl wget && \
    rm -rf /var/lib/apt/lists/*

# Technique 2: Multi-stage builds for build tools
FROM node:18-alpine AS dependencies
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

FROM node:18-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:18-alpine AS runtime
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nextjs -u 1001
WORKDIR /app
COPY --from=dependencies /app/node_modules ./node_modules
COPY --from=build /app/dist ./dist
USER nextjs
CMD ["node", "dist/server.js"]

# Technique 3: Remove unnecessary files
RUN apt-get update && \
    apt-get install -y build-essential python3-dev && \
    pip install -r requirements.txt && \
    apt-get purge -y build-essential python3-dev && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/* \
           /tmp/* \
           /var/tmp/* \
           ~/.cache
```

## 🔄 Multi-container Applications with Docker Compose

### Docker Compose Fundamentals

```yaml
# docker-compose.yml - Production-ready configuration
version: '3.8'

services:
  web:
    build:
      context: .
      dockerfile: Dockerfile.prod
      args:
        - NODE_ENV=production
        - BUILD_DATE=${BUILD_DATE}
    image: myapp:${VERSION:-latest}
    container_name: myapp-web
    restart: unless-stopped
    ports:
      - "80:3000"
      - "443:3443"
    environment:
      - NODE_ENV=production
      - DATABASE_URL=postgresql://user:${DB_PASSWORD}@db:5432/myapp
      - REDIS_URL=redis://redis:6379
    env_file:
      - .env.production
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_started
    volumes:
      - ./uploads:/app/uploads
      - app-logs:/app/logs
    networks:
      - app-network
      - monitoring
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.web.rule=Host(`myapp.com`)"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  db:
    image: postgres:15-alpine
    container_name: myapp-db
    restart: unless-stopped
    environment:
      - POSTGRES_DB=myapp
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - db-data:/var/lib/postgresql/data
      - ./init-scripts:/docker-entrypoint-initdb.d
    networks:
      - app-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U user -d myapp"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: myapp-redis
    restart: unless-stopped
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis-data:/data
    networks:
      - app-network
    sysctls:
      - net.core.somaxconn=1024

  nginx:
    image: nginx:alpine
    container_name: myapp-nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
      - static-assets:/var/www/static
    depends_on:
      - web
    networks:
      - app-network

volumes:
  db-data:
    driver: local
    driver_opts:
      type: none
      device: /opt/myapp/data/postgres
      o: bind
  redis-data:
  app-logs:
  static-assets:

networks:
  app-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
  monitoring:
    external: true
```

### Advanced Compose Patterns

```yaml
# docker-compose.override.yml - Development overrides
version: '3.8'

services:
  web:
    build:
      target: development
    volumes:
      - .:/app
      - /app/node_modules
    environment:
      - NODE_ENV=development
      - DEBUG=*
    ports:
      - "3000:3000"
      - "9229:9229"  # Debug port
    command: npm run dev

  db:
    ports:
      - "5432:5432"  # Expose for local development

# docker-compose.test.yml - Testing configuration
version: '3.8'

services:
  web:
    build:
      target: test
    environment:
      - NODE_ENV=test
      - CI=true
    command: npm test
    depends_on:
      - db-test

  db-test:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=myapp_test
      - POSTGRES_USER=test
      - POSTGRES_PASSWORD=test
    tmpfs:
      - /var/lib/postgresql/data

# docker-compose.monitoring.yml - Monitoring stack
version: '3.8'

services:
  prometheus:
    image: prom/prometheus
    container_name: prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'

  grafana:
    image: grafana/grafana
    container_name: grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
    volumes:
      - grafana-data:/var/lib/grafana
      - ./monitoring/grafana:/etc/grafana/provisioning

volumes:
  prometheus-data:
  grafana-data:
```

## 💾 Volume Management and Data Persistence

### Volume Types and Usage

```bash
# Named volumes (managed by Docker)
docker volume create app-data
docker volume create --driver local \
  --opt type=none \
  --opt device=/host/path \
  --opt o=bind \
  app-data

docker run -v app-data:/app/data myapp:latest

# Anonymous volumes (temporary)
docker run -v /app/cache myapp:latest

# Bind mounts (host filesystem)
docker run -v /host/path:/container/path myapp:latest
docker run -v $(pwd)/logs:/app/logs myapp:latest

# Read-only mounts
docker run -v /host/config:/app/config:ro myapp:latest

# Volume with specific mount options
docker run -v app-data:/app/data:rw,Z myapp:latest
```

### Volume Management Commands

```bash
# Volume operations
docker volume ls                       # List volumes
docker volume inspect app-data        # Inspect volume
docker volume rm app-data             # Remove volume
docker volume prune                   # Remove unused volumes

# Volume backup and restore
docker run --rm -v app-data:/data -v $(pwd):/backup \
  ubuntu tar czf /backup/backup.tar.gz -C /data .

docker run --rm -v app-data:/data -v $(pwd):/backup \
  ubuntu tar xzf /backup/backup.tar.gz -C /data

# Volume migration between hosts
docker run --rm -v source-vol:/data alpine tar czf - -C /data . | \
  ssh remote-host 'docker run --rm -i -v dest-vol:/data alpine tar xzf - -C /data'
```

### UID/GID Mapping and Permissions

```dockerfile
# Dockerfile with proper user setup
FROM alpine:latest

# Create user with specific UID/GID
RUN addgroup -g 1001 appgroup && \
    adduser -u 1001 -G appgroup -s /bin/sh -D appuser

# Set ownership of application directory
COPY --chown=appuser:appgroup . /app/
WORKDIR /app

USER appuser

# Volume with proper permissions
VOLUME ["/app/data"]
```

```bash
# Run container with user mapping
docker run -u 1001:1001 -v app-data:/app/data myapp:latest

# Fix permissions on existing volume
docker run --rm -v app-data:/data alpine chown -R 1001:1001 /data

# Use host user mapping
docker run -u $(id -u):$(id -g) -v $(pwd):/app myapp:latest
```

## 🌐 Docker Networking

### Network Types and Configuration

```bash
# Network types overview
docker network ls

# Bridge network (default)
docker network create mybridge
docker network create --driver bridge \
  --subnet=172.20.0.0/16 \
  --ip-range=172.20.240.0/20 \
  mybridge

# Host network (no isolation)
docker run --network host myapp:latest

# None network (no networking)
docker run --network none myapp:latest

# Custom bridge network with advanced options
docker network create \
  --driver bridge \
  --subnet=192.168.1.0/24 \
  --gateway=192.168.1.1 \
  --ip-range=192.168.1.128/25 \
  --opt com.docker.network.bridge.name=br-custom \
  --opt com.docker.network.bridge.enable_icc=true \
  --opt com.docker.network.bridge.host_binding_ipv4=0.0.0.0 \
  custom-network
```

### Container Networking and Service Discovery

```bash
# Connect containers to networks
docker run --network mybridge --name web nginx
docker run --network mybridge --name db postgres

# Multi-network container
docker network create frontend
docker network create backend
docker network connect frontend web
docker network connect backend web
docker network connect backend db

# Port publishing options
docker run -p 8080:80 nginx                    # Host port 8080 to container 80
docker run -p 127.0.0.1:8080:80 nginx         # Bind to localhost only
docker run -p 8080-8090:80 nginx              # Port range
docker run -P nginx                            # Publish all exposed ports

# Container DNS and service discovery
docker run --network mybridge --name web \
  --hostname web.myapp.local \
  --add-host db.external:192.168.1.100 \
  nginx

# Network troubleshooting
docker network inspect mybridge
docker exec container_name nslookup db
docker exec container_name ping -c 3 web
```

### Overlay Networks (Swarm Mode)

```bash
# Initialize Docker Swarm
docker swarm init --advertise-addr 192.168.1.10

# Create overlay network
docker network create --driver overlay \
  --subnet=10.0.9.0/24 \
  --attachable \
  myoverlay

# Deploy service with overlay network
docker service create \
  --network myoverlay \
  --replicas 3 \
  --name web \
  nginx
```

## 📊 Container Monitoring and Debugging

### Logging and Log Management

```bash
# Docker logs commands
docker logs container_name              # View logs
docker logs -f container_name           # Follow logs
docker logs --tail 100 container_name   # Last 100 lines
docker logs --since "2024-01-01T00:00:00" container_name
docker logs --until "1h" container_name # Logs until 1 hour ago

# Logging drivers configuration
docker run --log-driver json-file \
  --log-opt max-size=10m \
  --log-opt max-file=3 \
  myapp:latest

# Centralized logging with fluentd
docker run --log-driver fluentd \
  --log-opt fluentd-address=localhost:24224 \
  --log-opt tag="myapp.{{.Name}}" \
  myapp:latest

# Syslog logging
docker run --log-driver syslog \
  --log-opt syslog-address=tcp://192.168.1.10:514 \
  myapp:latest
```

### Container Inspection and Debugging

```bash
# Container inspection
docker inspect container_name           # Full container details
docker inspect --format='{{.State.Status}}' container_name
docker inspect --format='{{.NetworkSettings.IPAddress}}' container_name
docker inspect --format='{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' container_name

# Runtime statistics
docker stats                           # All containers
docker stats container_name           # Specific container
docker stats --no-stream             # One-time stats

# Container events
docker events                         # All events
docker events --filter container=myapp
docker events --filter event=start
docker events --since="2024-01-01T00:00:00"

# Process information
docker top container_name             # Running processes
docker exec container_name ps aux     # Detailed process list

# File system changes
docker diff container_name            # Changed files since start
docker cp container_name:/app/config.yml ./config.yml
docker cp ./newfile.txt container_name:/app/
```

### Health Monitoring

```bash
# Health check status
docker inspect --format='{{.State.Health.Status}}' container_name
docker inspect --format='{{range .State.Health.Log}}{{.Output}}{{end}}' container_name

# Container lifecycle events
docker events --filter container=myapp --filter event=health_status

# Custom health monitoring script
#!/bin/bash
while true; do
    health=$(docker inspect --format='{{.State.Health.Status}}' myapp)
    if [ "$health" != "healthy" ]; then
        echo "Container unhealthy: $health"
        # Send alert or restart container
        docker restart myapp
    fi
    sleep 30
done
```

## 🔒 Docker Security

### Running Containers Securely

```dockerfile
# Security-focused Dockerfile
FROM node:18-alpine

# Create non-root user
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nextjs -u 1001

# Install only necessary packages
RUN apk add --no-cache dumb-init

# Set secure directory permissions
WORKDIR /app
COPY --chown=nextjs:nodejs package*.json ./
RUN npm ci --only=production && npm cache clean --force

COPY --chown=nextjs:nodejs . .

# Switch to non-root user
USER nextjs

# Use dumb-init for proper signal handling
ENTRYPOINT ["dumb-init", "--"]
CMD ["node", "server.js"]
```

### Container Security Configuration

```bash
# Run with security constraints
docker run \
  --user 1001:1001 \
  --read-only \
  --tmpfs /tmp \
  --cap-drop=ALL \
  --cap-add=NET_BIND_SERVICE \
  --security-opt=no-new-privileges:true \
  --security-opt=seccomp:default \
  myapp:latest

# Limit resources
docker run \
  --memory=512m \
  --memory-swap=512m \
  --cpus="1.5" \
  --pids-limit=100 \
  --ulimit nofile=1024:1024 \
  myapp:latest

# Use custom seccomp profile
docker run \
  --security-opt seccomp=./security/seccomp-profile.json \
  myapp:latest
```

### Security Scanning and Auditing

```bash
# Docker built-in scanning
docker scan myapp:latest

# Trivy scanning
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  -v $HOME/Library/Caches:/root/.cache/ \
  aquasec/trivy:latest image myapp:latest

# Snyk scanning
snyk container test myapp:latest
snyk container monitor myapp:latest

# Clair scanning
docker run -d --name clair-db arminc/clair-db:latest
docker run -p 6060:6060 --link clair-db:postgres -d --name clair arminc/clair-local-scan:latest
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  --link clair:clair \
  arminc/clair-scanner:latest \
  --clair="http://clair:6060" \
  --ip="$(docker inspect --format='{{.NetworkSettings.IPAddress}}' clair)" \
  myapp:latest
```

## 🚀 CI/CD Integration

### GitHub Actions with Docker

```yaml
# .github/workflows/docker.yml
name: Docker Build and Push

on:
  push:
    branches: [main, develop]
    tags: ['v*']
  pull_request:
    branches: [main]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  build-and-push:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write

    steps:
    - name: Checkout repository
      uses: actions/checkout@v4

    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v3

    - name: Log in to Container Registry
      if: github.event_name != 'pull_request'
      uses: docker/login-action@v3
      with:
        registry: ${{ env.REGISTRY }}
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}

    - name: Extract metadata
      id: meta
      uses: docker/metadata-action@v5
      with:
        images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
        tags: |
          type=ref,event=branch
          type=ref,event=pr
          type=semver,pattern={{version}}
```