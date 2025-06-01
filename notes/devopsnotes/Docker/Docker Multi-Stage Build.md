
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