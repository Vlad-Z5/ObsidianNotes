### Volume

```bash
# Named volumes (Docker managed in /var/lib/docker/volumes/)
docker volume create \
  --driver local \
  --opt type=nfs \
  --opt o=addr=192.168.1.1,rw \
  --opt device=:/path/to/dir \
  nfs-volume

# Volume with specific mount options
docker volume create \
  --driver local \
  --opt type=ext4 \
  --opt device=/dev/sdb1 \
  block-volume

# Bind mounts with options
docker run -v /host/path:/container/path:ro,Z nginx # Read-only, SELinux label
docker run -v /host/path:/container/path:rw,cached nginx # macOS performance

# tmpfs mounts (memory-based)
docker run --tmpfs /tmp:rw,noexec,nosuid,size=100m nginx

# Volume plugins for distributed storage
docker plugin install store/sumologic/docker-logging-driver:1.0.0
docker volume create -d sumologic-driver my-vol
```

### Storage Drivers and Performance

```bash
# Storage driver information
docker info | grep "Storage Driver"
docker info | grep "Backing Filesystem"

# overlay2 driver (default, best performance)
# Files: /var/lib/docker/overlay2/
# Layers: lower (read-only) + upper (writable) + work + merged

# Container layer inspection
docker diff container_name # Shows changes in writable layer
docker export container_name > container.tar # Export container filesystem
```

### Volume Management and Operations

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

### Advanced Volume Configurations

```bash
# Volume with specific mount options
docker volume create \
  --driver local \
  --opt type=nfs \
  --opt o=addr=192.168.1.1,rw \
  --opt device=:/path/to/dir \
  nfs-volume

# Volume with specific mount options
docker volume create \
  --driver local \
  --opt type=ext4 \
  --opt device=/dev/sdb1 \
  block-volume

# Bind mounts with options
docker run -v /host/path:/container/path:ro,Z nginx # Read-only, SELinux label
docker run -v /host/path:/container/path:rw,cached nginx # macOS performance

# tmpfs mounts (memory-based)
docker run --tmpfs /tmp:rw,noexec,nosuid,size=100m nginx

# Volume plugins for distributed storage
docker plugin install store/sumologic/docker-logging-driver:1.0.0
docker volume create -d sumologic-driver my-vol
```
