
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
