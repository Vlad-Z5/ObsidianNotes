
```dockerfile
# Stage 1: Build environment (large, with build tools)
FROM node:16 AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci                    # Install all dependencies (dev + prod)
COPY . .
RUN npm run build            # Build application
RUN npm prune --production   # Remove dev dependencies

# Stage 2: Runtime environment (minimal)
FROM node:16-alpine AS runtime
RUN addgroup -g 1001 -S nodejs && adduser -S nextjs -u 1001
WORKDIR /app
# Copy only production artifacts from builder stage
COPY --from=builder --chown=nextjs:nodejs /app/dist ./dist
COPY --from=builder --chown=nextjs:nodejs /app/node_modules ./node_modules
COPY --from=builder --chown=nextjs:nodejs /app/package.json ./
USER nextjs
EXPOSE 3000
CMD ["node", "dist/index.js"]

# Final image contains only runtime stage, builder stage discarded
# Result: 150MB instead of 1GB+ with build tools
```

**Multi-Stage Benefits:**

- **Size Reduction:** Discard build tools, dev dependencies, source code
- **Security:** Fewer attack vectors in final image
- **Performance:** Faster deployment, less bandwidth
- **Separation:** Build-time vs runtime concerns isolated

### Advanced Multi-Stage Patterns

#### Complex Multi-Stage Build with Multiple Environments

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

#### Advanced Container Configuration with Multi-Stage

```dockerfile
# Stage 1: Dependencies stage (cached separately)
FROM node:18-alpine AS deps
WORKDIR /app
COPY package*.json ./
RUN --mount=type=cache,target=/root/.npm \
    npm ci --only=production --no-audit --no-fund \
    && npm cache clean --force

# Stage 2: Build stage (if needed)
FROM node:18-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN --mount=type=cache,target=/root/.npm \
    npm ci --no-audit --no-fund
COPY . .
RUN npm run build \
    && npm run test

# Stage 3: Runtime stage with security hardening
FROM node:18-alpine AS runtime
# Create non-root user
RUN addgroup -g 1001 -S nodejs \
    && adduser -S nextjs -u 1001 -G nodejs

# Copy production dependencies
COPY --from=deps --chown=nextjs:nodejs /app/node_modules ./node_modules
# Copy built application
COPY --from=build --chown=nextjs:nodejs /app/dist ./dist
COPY --from=build --chown=nextjs:nodejs /app/package.json ./

# Security hardening
USER nextjs
EXPOSE 3000
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:3000/health || exit 1

# Use dumb-init for proper signal handling
ENTRYPOINT ["dumb-init", "--"]
CMD ["node", "dist/index.js"]
```

#### Build-time Optimizations

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