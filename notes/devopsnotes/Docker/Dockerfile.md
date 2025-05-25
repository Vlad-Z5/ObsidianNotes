
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

### .dockerignore Optimization

```bash
# .dockerignore - reduces build context size
node_modules
npm-debug.log*
.git
.gitignore
README.md
Dockerfile*
.dockerignore
.nyc_output
coverage
.env.local
.env.*.local
**/*.test.js
**/*.spec.js
tests/
docs/
```
