
### Complete Optimized Dockerfile

```dockerfile
# syntax=docker/dockerfile:1.4
ARG NODE_VERSION=16
ARG ALPINE_VERSION=3.15

# Base stage with common setup
FROM node:${NODE_VERSION}-alpine${ALPINE_VERSION} AS base
RUN apk add --no-cache \
    dumb-init \
    curl \
    && rm -rf /var/cache/apk/*
WORKDIR /app
ENV NODE_ENV=production
ENV PATH=/app/node_modules/.bin:$PATH

# Dependencies stage (cached separately)
FROM base AS deps
COPY package*.json ./
RUN --mount=type=cache,target=/root/.npm \
    npm ci --only=production --no-audit --no-fund \
    && npm cache clean --force

# Build stage (if needed)
FROM base AS builder
COPY package*.json ./
RUN --mount=type=cache,target=/root/.npm \
    npm ci --no-audit --no-fund
COPY . .
RUN npm run build \
    && npm run test

# Runtime stage
FROM base AS runtime
# Create non-root user
RUN addgroup -g 1001 -S nodejs \
    && adduser -S nextjs -u 1001 -G nodejs

# Copy production dependencies
COPY --from=deps --chown=nextjs:nodejs /app/node_modules ./node_modules
# Copy built application
COPY --from=builder --chown=nextjs:nodejs /app/dist ./dist
COPY --from=builder --chown=nextjs:nodejs /app/package.json ./

# Security hardening
USER nextjs
EXPOSE 3000
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:3000/health || exit 1

# Use dumb-init for proper signal handling
ENTRYPOINT ["dumb-init", "--"]
CMD ["node", "dist/index.js"]
```

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

#### Advanced Container Configuration

```dockerfile
# EXPOSE - Document exposed ports (metadata only)
EXPOSE 8080                            # Single port
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

### BuildKit and Advanced Building

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

### Build Context Optimization

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

### Dockerfile Instructions Deep Dive

```dockerfile
# FROM: Base image with digest for reproducibility
FROM nginx@sha256:abc123... AS base

# ARG: Build-time variables (not in final image)
ARG BUILD_DATE
ARG VERSION=1.0
LABEL build-date=$BUILD_DATE version=$VERSION

# ENV: Runtime environment variables
ENV NODE_ENV=production \
    PORT=3000 \
    LOG_LEVEL=info

# WORKDIR: Sets working directory and creates if not exists
WORKDIR /app

# COPY vs ADD:
COPY src/ ./src/                    # Preferred: simple copy
ADD https://example.com/file.tar.gz /tmp/  # URL download + extraction
ADD archive.tar.gz /app/            # Auto-extraction (security risk)

# RUN: Execute commands and commit result as new layer
RUN set -ex \                       # Exit on error, print commands
    && apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/* \ # Clean package cache
    && groupadd -r app \
    && useradd -r -g app app

# USER: Switch to non-root user
USER app:app

# EXPOSE: Document ports (doesn't actually publish)
EXPOSE 3000/tcp 8080/udp

# VOLUME: Create mount point
VOLUME ["/data", "/logs"]

# HEALTHCHECK: Container health monitoring
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:3000/health || exit 1

# STOPSIGNAL: Signal for graceful shutdown
STOPSIGNAL SIGTERM

# SHELL: Change default shell
SHELL ["/bin/bash", "-euo", "pipefail", "-c"]

# CMD vs ENTRYPOINT:
ENTRYPOINT ["node"]                 # Fixed entry point
CMD ["app.js"]                      # Default arguments (can be overridden)
# Result: docker run image -> node app.js
# Override: docker run image server.js -> node server.js
```

### .dockerignore Configuration

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

### Advanced Multi-Stage Build Patterns

#### Production-Optimized Multi-Stage Build

```dockerfile
# syntax=docker/dockerfile:1.4
ARG NODE_VERSION=18
ARG ALPINE_VERSION=3.18

# Base stage with common dependencies
FROM node:${NODE_VERSION}-alpine${ALPINE_VERSION} AS base
RUN apk add --no-cache \
    dumb-init \
    curl \
    tzdata \
    && rm -rf /var/cache/apk/*
WORKDIR /app
ENV NODE_ENV=production
ENV PATH=/app/node_modules/.bin:$PATH

# Dependencies stage with cache optimization
FROM base AS deps
COPY package*.json ./
RUN --mount=type=cache,target=/root/.npm \
    --mount=type=cache,target=/app/node_modules/.cache \
    npm ci --only=production --no-audit --no-fund \
    && npm cache clean --force

# Development dependencies for building
FROM base AS dev-deps
ENV NODE_ENV=development
COPY package*.json ./
RUN --mount=type=cache,target=/root/.npm \
    npm ci --no-audit --no-fund

# Build stage with test execution
FROM dev-deps AS builder
ARG BUILD_DATE
ARG VCS_REF
COPY . .
RUN --mount=type=cache,target=/app/.next/cache \
    npm run build \
    && npm run test:ci

# Security scanning stage (optional)
FROM builder AS security
RUN --mount=type=cache,target=/root/.npm \
    npm audit --audit-level high \
    && npm run security:check

# Final runtime stage
FROM base AS runtime
ARG BUILD_DATE
ARG VCS_REF

# Add metadata labels
LABEL org.opencontainers.image.created="${BUILD_DATE}" \
      org.opencontainers.image.revision="${VCS_REF}" \
      org.opencontainers.image.source="https://github.com/company/app"

# Create non-root user
RUN addgroup -g 1001 -S nodejs \
    && adduser -S nextjs -u 1001 -G nodejs

# Copy dependencies and built application
COPY --from=deps --chown=nextjs:nodejs /app/node_modules ./node_modules
COPY --from=builder --chown=nextjs:nodejs /app/dist ./dist
COPY --from=builder --chown=nextjs:nodejs /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/package.json ./

# Runtime configuration
USER nextjs
EXPOSE 3000
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:3000/health || exit 1

ENTRYPOINT ["dumb-init", "--"]
CMD ["node", "dist/server.js"]
```

#### Multi-Platform Build Configuration

```dockerfile
# syntax=docker/dockerfile:1.4
FROM --platform=$BUILDPLATFORM node:18-alpine AS base
ARG TARGETPLATFORM
ARG BUILDPLATFORM
RUN echo "Building on $BUILDPLATFORM for $TARGETPLATFORM"

# Cross-compilation support
FROM --platform=$BUILDPLATFORM base AS builder
RUN apk add --no-cache \
    python3 \
    make \
    g++
COPY package*.json ./
RUN --mount=type=cache,target=/root/.npm \
    npm ci

# Platform-specific optimizations
FROM base AS runtime
ARG TARGETPLATFORM
RUN case "$TARGETPLATFORM" in \
    "linux/amd64") echo "Optimizing for AMD64" ;; \
    "linux/arm64") echo "Optimizing for ARM64" ;; \
    "linux/arm/v7") echo "Optimizing for ARMv7" ;; \
    *) echo "Default optimization" ;; \
    esac

COPY --from=builder /app /app
CMD ["node", "app.js"]
```

#### Environment-Specific Multi-Stage Pattern

```dockerfile
# syntax=docker/dockerfile:1.4

# Base stage
FROM node:18-alpine AS base
WORKDIR /app
COPY package*.json ./

# Development stage
FROM base AS development
ENV NODE_ENV=development
RUN npm ci
COPY . .
EXPOSE 3000 9229
CMD ["npm", "run", "dev"]

# Testing stage
FROM base AS testing
ENV NODE_ENV=test
RUN npm ci
COPY . .
RUN npm run test
RUN npm run lint
RUN npm audit

# Production build stage
FROM base AS build-production
ENV NODE_ENV=production
RUN npm ci --only=production
COPY . .
RUN npm run build

# Production runtime
FROM node:18-alpine AS production
WORKDIR /app
RUN addgroup -g 1001 -S nodejs \
    && adduser -S nextjs -u 1001 -G nodejs
COPY --from=build-production --chown=nextjs:nodejs /app/dist ./dist
COPY --from=build-production --chown=nextjs:nodejs /app/package.json ./
USER nextjs
EXPOSE 3000
CMD ["node", "dist/index.js"]
```

### Docker Layer Caching Deep Dive

#### How Layer Caching Works

```dockerfile
# BAD - Cache breaks on any file change
FROM node:16-alpine
COPY . /app # Layer 1: All files
WORKDIR /app
RUN npm install # Layer 2: Dependencies (breaks when any file changes)

# GOOD - Optimized for cache
FROM node:16-alpine
WORKDIR /app
COPY package*.json ./ # Layer 1: Only package files
RUN npm ci --only=production # Layer 2: Dependencies (cached unless package.json changes)
COPY . . # Layer 3: Source code
```

**Layer Cache Rules:**
- Each instruction creates new layer if different from previous build
- Cache invalidation: If instruction changes, all subsequent layers rebuild
- Cache key: Instruction + context (files/metadata)
- `COPY/ADD`: Checksum of files determines cache validity
- `RUN`: Command string + previous layer determine cache validity

#### Advanced Build Techniques

```dockerfile
# Build arguments and cache mounts
FROM node:16-alpine AS base
ARG NODE_ENV=production
ENV NODE_ENV=$NODE_ENV

# Cache mount for package managers
FROM base AS deps
WORKDIR /app
COPY package*.json ./
RUN --mount=type=cache,target=/root/.npm \
    npm ci --only=$NODE_ENV

# Bind mount for source (development)
FROM base AS dev
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
RUN --mount=type=bind,source=.,target=/app \
    npm run dev

# Multi-platform builds
FROM --platform=$BUILDPLATFORM node:16-alpine AS builder
ARG TARGETPLATFORM
ARG BUILDPLATFORM
RUN echo "Building on $BUILDPLATFORM for $TARGETPLATFORM"
```

#### Cache Optimization Strategies

```dockerfile
# 1. Order instructions by change frequency (least to most)
FROM node:18-alpine
WORKDIR /app

# System dependencies (rarely change)
RUN apk add --no-cache curl git

# Language dependencies (change occasionally)
COPY package*.json ./
RUN npm ci --only=production

# Application code (changes frequently)
COPY src/ ./src/
COPY public/ ./public/

# 2. Use .dockerignore to exclude unnecessary files
# 3. Separate build and runtime dependencies
FROM node:18-alpine AS build-deps
RUN apk add --no-cache python3 make g++
COPY package*.json ./
RUN npm ci

FROM node:18-alpine AS runtime-deps
COPY package*.json ./
RUN npm ci --only=production

# 4. Leverage BuildKit cache mounts
RUN --mount=type=cache,target=/root/.cache/pip \
    --mount=type=cache,target=/root/.cache/go-build \
    pip install -r requirements.txt

# 5. Use multi-stage for optimal layer reuse
FROM alpine:latest AS certs
RUN apk --no-cache add ca-certificates

FROM scratch AS final
COPY --from=certs /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/
```

### BuildKit Advanced Features

#### Cache Mounts and Optimization

```dockerfile
# syntax=docker/dockerfile:1.4

# NPM cache mount
RUN --mount=type=cache,target=/root/.npm \
    npm ci --only=production

# APT cache mount
RUN --mount=type=cache,target=/var/cache/apt \
    --mount=type=cache,target=/var/lib/apt/lists \
    apt-get update && apt-get install -y python3

# Go module cache
RUN --mount=type=cache,target=/go/pkg/mod \
    go mod download

# Pip cache mount
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt

# Custom cache directory
RUN --mount=type=cache,target=/app/.cache,id=myapp-cache \
    make build
```

#### Secrets and SSH Management

```dockerfile
# syntax=docker/dockerfile:1.4

# Using secrets (build-time only, not in layers)
RUN --mount=type=secret,id=aws_key,target=/root/.aws/credentials \
    aws s3 cp s3://bucket/file /app/

# SSH agent forwarding for private repos
RUN --mount=type=ssh \
    git clone git@github.com:private/repo.git /app

# Multiple SSH keys
RUN --mount=type=ssh,id=github \
    --mount=type=ssh,id=gitlab \
    git clone git@github.com:repo1.git && \
    git clone git@gitlab.com:repo2.git
```

#### Build Context Optimization

```bash
# Build with secrets
echo "secret_content" | docker build \
  --secret id=mysecret,src=- \
  -t myapp .

# Build with SSH forwarding
docker build \
  --ssh default=$SSH_AUTH_SOCK \
  -t myapp .

# Multi-platform build with cache
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  --cache-from type=gha \
  --cache-to type=gha,mode=max \
  -t myapp:latest .

# Build with registry cache
docker build \
  --cache-from myregistry/myapp:cache \
  --cache-to type=registry,ref=myregistry/myapp:cache \
  -t myapp:latest .
```

### Production Build Optimization

#### Size Optimization Techniques

```dockerfile
# 1. Multi-stage with minimal runtime
FROM golang:1.19-alpine AS builder
WORKDIR /app
COPY go.* ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -o app

FROM scratch
COPY --from=builder /app/app /
COPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/
ENTRYPOINT ["/app"]

# 2. Alpine-based minimal images
FROM node:18-alpine
RUN apk add --no-cache dumb-init
USER node
ENTRYPOINT ["dumb-init", "--"]

# 3. Distroless images for maximum security
FROM gcr.io/distroless/java:11
COPY app.jar /app.jar
ENTRYPOINT ["java", "-jar", "/app.jar"]
```

#### Performance Optimization

```dockerfile
# 1. Parallel dependency installation
FROM node:18-alpine AS deps
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production --ignore-scripts --prefer-offline

# 2. Build-time optimizations
FROM base AS builder
ENV NODE_OPTIONS="--max-old-space-size=4096"
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build:production

# 3. Runtime optimizations
FROM node:18-alpine AS runtime
ENV NODE_ENV=production
ENV NODE_OPTIONS="--max-old-space-size=2048"
COPY --from=builder /app/dist ./dist
CMD ["node", "--optimize-for-size", "dist/server.js"]
```

### Cross-References
- **[[Docker Commands]]** - Image management with BuildKit features
- **[[Docker Security]]** - Container hardening in multi-stage builds
- **[[Docker Performance & Monitoring]]** - Build performance optimization
- **[[Docker CICD]]** - Automated build pipelines with multi-stage patterns
