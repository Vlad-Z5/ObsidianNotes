**Client-Server Model:**

- **Docker Client:** CLI interface (`docker` command), communicates via REST API
- **Docker Daemon (dockerd):** Background service managing containers/images/networks/volumes
- **containerd:** High-level container runtime, manages container lifecycle
- **runc:** Low-level container runtime, OCI-compliant, spawns containers
- **Docker Registry:** Storage for images (Docker Hub, ECR, Harbor, Nexus)

**Storage Drivers:** overlay2 (default), aufs, devicemapper, btrfs, zfs, vfs **Network Drivers:** bridge (default), host, overlay, macvlan, none, ipvlan

**Key Components:**

- **Image:** Read-only template with app + dependencies, composed of layers
- **Container:** Running instance of image with writable layer, process namespace isolation
- **Dockerfile:** Build instructions for images, each instruction = new layer
- **Volume:** Persistent data storage, managed by Docker daemon
- **Network:** Container communication layer with built-in DNS