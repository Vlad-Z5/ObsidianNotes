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
docker run -v /host/path:/container/path:ro,Z nginx    # Read-only, SELinux label
docker run -v /host/path:/container/path:rw,cached nginx  # macOS performance

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
docker diff container_name          # Shows changes in writable layer
docker export container_name > container.tar  # Export container filesystem
```
