### How Layer Caching Works

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
  
### Advanced Build Techniques

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

## Essential Commands Deep Dive

### Image Management with Internals

```bash
# Build with advanced options
docker build -t app:v1.0 . --no-cache # Skip cache
docker build -t app:v1.0 . --target=builder # Build specific stage
docker build -t app:v1.0 . --build-arg NODE_ENV=prod # Pass build arguments
docker build -t app:v1.0 . --platform=linux/amd64 # Target platform
docker build -t app:v1.0 . --progress=plain # Detailed output

# BuildKit features (enable with: export DOCKER_BUILDKIT=1)
docker build -t app . --secret id=mysecret,src=./secret.txt
docker build -t app . --ssh default # SSH agent forwarding

# Registry Operations with authentication
echo $PASSWORD | docker login -u $USERNAME --password-stdin registry.com
docker pull nginx:alpine
docker tag nginx:alpine myregistry.com/nginx:v1.0
docker push myregistry.com/nginx:v1.0
docker manifest inspect nginx:alpine # Image manifest details

# Image Analysis
docker images --digests # Show image digests
docker history app:v1.0 --no-trunc # Full layer history
docker inspect nginx --format='{{.Config.Env}}' # Extract specific data
docker diff container_name # Show container changes
docker export container_name | docker import - newimage # Container to image
```
