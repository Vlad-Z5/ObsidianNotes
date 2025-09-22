# Docker Fundamentals

**Docker** is a containerization platform that packages applications with their dependencies into lightweight, portable containers that share the host OS kernel.


## Core Concepts

### What is Docker?
Docker is a **containerization platform** that enables developers to package applications and their dependencies into **lightweight, portable containers**. Unlike virtual machines, containers share the host operating system kernel, making them significantly more efficient.

### Key Principles
- **Immutable Images**: Read-only templates containing application code and dependencies
- **Container Instances**: Running instances of images with an additional writable layer
- **Registry Distribution**: Centralized storage and sharing of container images
- **Copy-on-Write**: Efficient storage using layered filesystem (OverlayFS/AUFS)
- **Process Isolation**: Containers run as isolated processes on the host system

### Docker vs Virtual Machines

```
┌─────────────────────────────────────┐
│           CONTAINERS                │
├─────────────────────────────────────┤
│    App A    │    App B    │  App C  │ ← Applications
├─────────────┼─────────────┼─────────┤
│   Runtime   │   Runtime   │ Runtime │ ← Container Runtime
├─────────────┴─────────────┴─────────┤
│          Docker Engine              │ ← Container Engine
├─────────────────────────────────────┤
│         Host OS (Linux)             │ ← Single OS Kernel
├─────────────────────────────────────┤
│         Physical Server             │ ← Hardware
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│         VIRTUAL MACHINES            │
├─────────────────────────────────────┤
│    App A    │    App B    │  App C  │ ← Applications
├─────────────┼─────────────┼─────────┤
│   Guest OS  │   Guest OS  │Guest OS │ ← Multiple OS Kernels
├─────────────┼─────────────┼─────────┤
│      VM     │      VM     │   VM    │ ← Virtual Machines
├─────────────┴─────────────┴─────────┤
│           Hypervisor                │ ← Virtualization Layer
├─────────────────────────────────────┤
│         Host OS                     │ ← Host Operating System
├─────────────────────────────────────┤
│         Physical Server             │ ← Hardware
└─────────────────────────────────────┘
```

**Benefits of Containers over VMs:**
- **Resource Efficiency**: 10-100x less overhead than VMs
- **Faster Startup**: Containers start in seconds vs minutes for VMs
- **Higher Density**: Run more containers per host than VMs
- **Consistent Environment**: Same runtime across dev/staging/production

---

## Docker Architecture

### Client-Server Architecture

Docker uses a **client-server architecture** with the following components:

```bash
# Command flow: docker run nginx:alpine
1. Docker Client (docker CLI) → REST API call
2. Docker Daemon (dockerd) → receives request
3. Image Management → checks local images, pulls if needed
4. containerd → creates container spec
5. runc → spawns container process
6. Namespace/cgroup setup → process isolation
7. Network setup → container networking
8. Volume mounts → storage attachment
```

#### Core Components

**Docker Client (`docker`)**
- Command-line interface (CLI) that communicates with Docker daemon
- Sends commands via REST API over Unix socket or network
- Can connect to local or remote Docker daemons

**Docker Daemon (`dockerd`)**
- Background service managing containers, images, networks, and volumes
- Listens to Docker API requests and manages Docker objects
- Handles image building, container lifecycle, and resource management

**containerd**
- High-level container runtime managing container lifecycle
- Handles image management, storage, and container execution
- Interface between Docker daemon and low-level runtime (runc)

**runc**
- Low-level OCI-compliant container runtime
- Spawns and runs containers according to OCI specification
- Manages Linux kernel features (namespaces, cgroups, capabilities)

**Docker Registry**
- Centralized storage for Docker images
- Public registries: Docker Hub, Quay.io, GitHub Container Registry
- Private registries: ECR, Harbor, Nexus, GitLab Registry

### Runtime Architecture

```bash
# Docker Engine Components
┌─────────────────────────────────────┐
│           Docker CLI                │ ← User Interface
├─────────────────────────────────────┤
│           Docker API                │ ← REST API
├─────────────────────────────────────┤
│         Docker Daemon               │ ← Engine Core
├─────────────────────────────────────┤
│           containerd                │ ← Container Runtime
├─────────────────────────────────────┤
│             runc                    │ ← OCI Runtime
├─────────────────────────────────────┤
│         Linux Kernel                │ ← Host OS
└─────────────────────────────────────┘
```

---

## Container Technology

### Linux Kernel Features

Docker containers leverage several Linux kernel features for isolation and resource management:

#### Namespaces (Process Isolation)
```bash
PID namespace    # Process ID isolation - containers see only their processes
Net namespace    # Network isolation - separate network stack per container
IPC namespace    # Inter-process communication isolation
UTS namespace    # Hostname/domain isolation
User namespace   # User ID isolation and mapping
Mount namespace  # Filesystem mount isolation
Cgroup namespace # Control group isolation
```

#### Control Groups (Resource Limits)
```bash
CPU cgroup       # CPU usage limits and scheduling
Memory cgroup    # Memory usage limits and accounting
Block I/O cgroup # Disk I/O limits and priorities
Network cgroup   # Network bandwidth limits
Devices cgroup   # Device access control
Freezer cgroup   # Process suspension/resumption
```

#### Capabilities (Privilege Management)
```bash
# Linux capabilities provide fine-grained privilege control
CAP_NET_ADMIN    # Network administration
CAP_SYS_ADMIN    # System administration
CAP_DAC_OVERRIDE # File permission override
CAP_SETUID       # User ID manipulation
CAP_SETGID       # Group ID manipulation

# Default container security
- Containers run with restricted capabilities
- Drop all capabilities by default
- Add only necessary capabilities
- Non-root user execution recommended
```

### Container Security Boundaries

```bash
# Default Security Features
┌─────────────────────────────────────┐
│     Application Process             │
├─────────────────────────────────────┤
│   Non-privileged Container          │ ← Default non-root execution
├─────────────────────────────────────┤
│   Restricted Capabilities           │ ← Limited system access
├─────────────────────────────────────┤
│   Seccomp Filtering                 │ ← System call restrictions
├─────────────────────────────────────┤
│   AppArmor/SELinux MAC              │ ← Mandatory access control
├─────────────────────────────────────┤
│   Namespace Isolation               │ ← Process/network/filesystem isolation
├─────────────────────────────────────┤
│   Cgroup Resource Limits            │ ← CPU/memory/I/O constraints
├─────────────────────────────────────┤
│   Host OS Kernel                    │ ← Shared kernel with isolation
└─────────────────────────────────────┘
```

---

## Image System

### Image Architecture

Docker images are **immutable, layered templates** that contain everything needed to run an application.

```bash
# Image Layer Structure
┌─────────────────────────────────────┐
│      Application Layer              │ ← App code, configs
├─────────────────────────────────────┤
│      Dependencies Layer             │ ← Libraries, frameworks
├─────────────────────────────────────┤
│      Runtime Layer                  │ ← Language runtime
├─────────────────────────────────────┤
│      OS Package Layer               │ ← System packages
├─────────────────────────────────────┤
│      Base OS Layer                  │ ← Alpine, Ubuntu, etc.
└─────────────────────────────────────┘
```

#### Key Image Concepts

**Read-only Layers**
- Each Dockerfile instruction creates a new read-only layer
- Layers are cached and reused across images
- Union filesystem combines layers into single view

**Layer Sharing**
- Multiple images can share identical layers
- Reduces storage requirements and transfer time
- Base images (alpine, ubuntu) shared across applications

**Image Manifest**
- JSON document describing image layers and metadata
- Contains layer checksums for integrity verification
- Platform-specific information for multi-architecture images

### Union Filesystem

Docker uses **union filesystems** to combine multiple layers:

```bash
# OverlayFS (default driver)
/var/lib/docker/overlay2/
├── lower/     # Read-only base layers
├── upper/     # Container's writable layer
├── work/      # Temporary workspace
└── merged/    # Combined filesystem view

# Layer Inspection
docker history nginx:alpine    # Show image layers
docker inspect nginx:alpine    # Image metadata
docker diff container_name     # Container changes
```

---

## Container Lifecycle

### Container States

```bash
# Container State Transitions
Created → Running → Paused → Stopped → Removed

docker create nginx:alpine        # Created state
docker start container_name       # Created → Running
docker pause container_name       # Running → Paused
docker unpause container_name     # Paused → Running
docker stop container_name        # Running → Stopped (SIGTERM)
docker kill container_name        # Any state → Stopped (SIGKILL)
docker rm container_name          # Stopped → Removed
```

### Process Management

```bash
# PID 1 Significance in Containers
# PID 1 must handle signals and reap zombie processes
# Use init systems or signal-aware entrypoints

# Good Practice - Signal Handling
ENTRYPOINT ["dumb-init", "--"]
CMD ["node", "server.js"]

# Process Monitoring
docker exec container_name ps aux                    # Process list
docker exec container_name pstree -p                # Process tree
docker top container_name                           # Host view of processes
```

### Container Filesystem

```bash
# Container Writable Layer
┌─────────────────────────────────────┐
│      Container Writable Layer      │ ← Read-write layer
├─────────────────────────────────────┤
│           Image Layers              │ ← Read-only layers
├─────────────────────────────────────┤
│      Union Filesystem View          │ ← Combined view
└─────────────────────────────────────┘

# Copy-on-Write (CoW)
- Files from read-only layers copied to writable layer when modified
- Original layers remain unchanged
- Efficient storage utilization
```

---

## Security Model

### Default Security Features

```bash
# Container Security Stack
User Namespaces     # User ID mapping and isolation
Capabilities        # Fine-grained privilege control
Seccomp             # System call filtering
AppArmor/SELinux   # Mandatory access control
Cgroups            # Resource isolation and limits
Namespaces         # Process/network/filesystem isolation
```

### Security Best Practices

```bash
# Secure Container Runtime
docker run \
  --user 1000:1000 \                      # Non-root user
  --read-only \                           # Read-only filesystem
  --tmpfs /tmp \                          # Writable temp space
  --cap-drop=ALL \                        # Drop all capabilities
  --cap-add=NET_BIND_SERVICE \            # Add only needed capabilities
  --security-opt=no-new-privileges \      # Prevent privilege escalation
  --security-opt=seccomp=default.json \   # Custom seccomp profile
  --pids-limit=100 \                      # Process limit
  --memory=512m \                         # Memory limit
  --cpus="0.5" \                          # CPU limit
  nginx:alpine
```

### Image Security

```bash
# Secure Image Building
FROM alpine:3.18                         # Minimal base image
RUN addgroup -g 1001 -S appgroup && \    # Create non-root user
    adduser -u 1001 -S appuser -G appgroup
COPY --chown=appuser:appgroup app /app/  # Set proper ownership
USER appuser                             # Switch to non-root user
HEALTHCHECK CMD /app/healthcheck.sh      # Health monitoring
```

---

## Storage & Networking

### Storage Drivers

Docker supports multiple storage drivers for different use cases:

```bash
# overlay2 (default, best performance)
- Copy-on-write with lower/upper/work/merged layers
- Best for most workloads
- Supported on modern Linux distributions

# devicemapper (enterprise storage)
- Direct LVM thin provisioning
- Better for production with dedicated storage
- Requires configuration

# Storage Driver Information
docker info | grep "Storage Driver"
docker info | grep "Backing Filesystem"
```

### Volume Types

```bash
# Named Volumes (Docker managed)
docker volume create app-data
docker run -v app-data:/app/data nginx

# Bind Mounts (Host filesystem)
docker run -v /host/path:/container/path nginx

# tmpfs Mounts (Memory-based)
docker run --tmpfs /tmp:noexec,nosuid,size=100m nginx
```

### Network Drivers

```bash
# bridge (default) - Software bridge with NAT
docker network create --driver bridge app-network

# host - Share host network stack
docker run --network host nginx

# overlay - Multi-host networking (Swarm)
docker network create --driver overlay --attachable multi-host

# macvlan - Direct Layer 2 access
docker network create --driver macvlan --subnet=192.168.1.0/24 macvlan-net

# none - No networking
docker run --network none alpine
```

---

## Troubleshooting

### Common Issues and Solutions

#### Container Won't Start
```bash
# Check container logs
docker logs container_name
docker logs --details container_name

# Inspect container configuration
docker inspect container_name

# Check resource constraints
docker stats container_name

# Test image locally
docker run -it --entrypoint=/bin/sh image_name
```

#### Network Connectivity Issues
```bash
# Check network configuration
docker network ls
docker network inspect bridge

# Test container networking
docker exec container_name ping google.com
docker exec container_name nslookup service-name
docker exec container_name ss -tulpn

# Check port mappings
docker port container_name
```

#### Performance Issues
```bash
# Monitor resource usage
docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"

# Check disk usage
docker system df -v

# Analyze container processes
docker exec container_name top
docker exec container_name htop  # if available
```

#### Storage Issues
```bash
# Check volume mounts
docker inspect container_name | grep -A 10 "Mounts"

# Volume disk usage
docker system df
docker volume ls

# Fix permission issues
docker exec container_name chown -R user:group /app/data
```

### Debugging Commands

```bash
# System information
docker version                    # Docker version info
docker info                      # System-wide information
docker system events            # Real-time Docker events

# Container debugging
docker exec -it container_name bash    # Interactive shell
docker cp container_name:/app/log ./   # Copy files from container
docker diff container_name             # Show filesystem changes

# Image analysis
docker history image_name        # Show image layers
docker save image_name > image.tar     # Export image
docker load < image.tar          # Import image
```

---

## Best Practices

### Development Best Practices

```bash
# Image Building
- Use minimal base images (alpine, distroless)
- Implement multi-stage builds for optimization
- Order Dockerfile instructions by change frequency
- Use .dockerignore to exclude unnecessary files
- Pin base image versions for reproducibility

# Security
- Run containers as non-root users
- Use read-only filesystems when possible
- Implement health checks
- Scan images for vulnerabilities
- Follow principle of least privilege
```

### Production Best Practices

```bash
# Resource Management
- Set memory and CPU limits
- Implement proper restart policies
- Use init systems for PID 1
- Configure log rotation
- Monitor container health

# Networking
- Use custom networks instead of default bridge
- Implement service discovery
- Configure proper DNS settings
- Use TLS for encrypted communication
- Isolate sensitive services
```

### Performance Optimization

```bash
# Image Optimization
- Use multi-stage builds to reduce image size
- Leverage layer caching effectively
- Minimize number of layers
- Use specific tags, avoid :latest
- Implement proper .dockerignore

# Runtime Optimization
- Configure appropriate resource limits
- Use volume mounts for persistent data
- Implement efficient logging strategies
- Use container orchestration for scaling
- Monitor and profile applications
```

---

## Cross-References

### Essential Reading
- **[[Dockerfile]]** - Complete container image building guide
- **[[Docker Commands]]** - Comprehensive CLI reference
- **[[Docker Security]]** - Container hardening and security practices
- **[[Docker Networking]]** - Network configuration and service discovery
- **[[Docker Storage & Volumes Internals]]** - Persistent storage management

### Advanced Topics
- **[[Docker Compose Production Setup]]** - Multi-container orchestration
- **[[Docker Performance & Monitoring]]** - Optimization and observability
- **[[Docker CICD]]** - Automated build and deployment pipelines

### Quick Navigation
- **Getting Started**: Docker fundamental → Dockerfile → Docker Commands
- **Production Setup**: Docker Security → Docker Compose Production Setup → Docker Performance & Monitoring
- **DevOps Workflows**: Docker CICD → Docker Commands → Docker Compose Production Setup

---

*This comprehensive guide provides the foundational knowledge for understanding Docker containerization technology and its practical implementation in modern DevOps workflows.*