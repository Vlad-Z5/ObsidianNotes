# Docker Commands

**Docker CLI** provides comprehensive command-line interface for managing containers, images, networks, and volumes in Docker environments.


## Essential Commands

### Quick Start Commands
```bash
# Basic workflow
docker --version                    # Check Docker version
docker info                        # System information
docker pull nginx:alpine           # Download image
docker run -d -p 80:80 nginx:alpine # Run container
docker ps                         # List running containers
docker stop container_name        # Stop container
docker rm container_name          # Remove container
docker rmi nginx:alpine           # Remove image
```

### Command Structure
```bash
# Docker command syntax
docker [OPTIONS] COMMAND [ARG...]

# Common options
--help              # Show help for command
--version          # Show Docker version
-v, --verbose      # Verbose output
--config string    # Location of client config files
-D, --debug        # Enable debug mode
```

---

## Image Management

### Building Images
```bash
# Basic build
docker build -t myapp:latest .                    # Build with tag
docker build -t myapp:v1.0 .                     # Build with version
docker build --no-cache -t myapp:latest .        # Build without cache
docker build -f Dockerfile.prod -t myapp:prod .  # Custom Dockerfile

# Advanced build options
docker build \
  --build-arg NODE_VERSION=18 \                  # Build arguments
  --build-arg BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ') \
  --target production \                          # Multi-stage target
  --platform linux/amd64,linux/arm64 \         # Multi-platform
  --progress=plain \                             # Build output format
  --secret id=mysecret,src=./secret.txt \       # BuildKit secrets
  --ssh default \                               # SSH agent forwarding
  -t myapp:$(git rev-parse --short HEAD) .

# BuildKit features (set DOCKER_BUILDKIT=1)
export DOCKER_BUILDKIT=1
docker build --cache-from myapp:cache --cache-to myapp:cache -t myapp:latest .
```

### Image Operations
```bash
# Image listing and information
docker images                               # List all images
docker images -a                           # Include intermediate images
docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"
docker images --filter "dangling=true"     # Show untagged images
docker images --filter "before=nginx:latest"
docker images --filter "since=nginx:alpine"

# Image inspection
docker inspect nginx:alpine                # Image metadata
docker history nginx:alpine               # Image layers
docker history --no-trunc nginx:alpine    # Full layer history
docker manifest inspect nginx:alpine      # Image manifest

# Image tagging and management
docker tag nginx:alpine myregistry.com/nginx:v1.0
docker tag myapp:latest myapp:$(git rev-parse --short HEAD)
docker tag myapp:latest myapp:stable
```

### Image Import/Export
```bash
# Save and load images
docker save nginx:alpine > nginx.tar           # Export image to tar
docker save -o nginx.tar nginx:alpine         # Export with -o flag
docker load < nginx.tar                       # Import from tar
docker load -i nginx.tar                      # Import with -i flag

# Export container filesystem
docker export container_name > container.tar   # Export container
docker import container.tar newimage:latest    # Import as new image
docker import - newimage:latest < container.tar

# Multiple images
docker save -o images.tar nginx:alpine redis:alpine
```

### Image Cleanup
```bash
# Remove images
docker rmi nginx:alpine                    # Remove specific image
docker rmi $(docker images -q)           # Remove all images
docker rmi $(docker images -f "dangling=true" -q)  # Remove dangling images

# Image pruning
docker image prune                        # Remove unused images
docker image prune -a                     # Remove all unused images
docker image prune --filter until=24h    # Remove images older than 24h
docker image prune --filter label=env=test  # Remove by label
```

---

## Container Operations

### Running Containers
```bash
# Basic run commands
docker run nginx:alpine                   # Run in foreground
docker run -d nginx:alpine               # Run detached (background)
docker run -it ubuntu:latest bash        # Interactive with terminal
docker run --rm ubuntu:latest echo "hi"  # Remove after exit
docker run --name web nginx:alpine       # Named container

# Advanced run options
docker run -d \
  --name production-web \
  --restart unless-stopped \              # Restart policy
  --memory=512m --memory-swap=1g \        # Memory limits
  --cpus="1.5" --cpu-shares=1024 \       # CPU limits
  --pids-limit=100 \                     # Process limit
  --ulimit nofile=1024:2048 \            # File descriptor limits
  --security-opt=no-new-privileges \     # Security options
  --cap-drop=ALL --cap-add=NET_BIND_SERVICE \  # Capabilities
  -p 8080:80 \                          # Port mapping
  -v app-data:/data \                   # Named volume
  -v /host/logs:/app/logs:ro \          # Bind mount (read-only)
  --tmpfs /tmp:noexec,nosuid,size=100m \ # tmpfs mount
  --network=custom-net \                # Custom network
  -e NODE_ENV=production \              # Environment variable
  -e DB_PASSWORD_FILE=/run/secrets/db_pass \  # Secret file
  --health-cmd="curl -f http://localhost/health" \
  --health-interval=30s \
  --health-timeout=3s \
  --health-retries=3 \
  nginx:alpine
```

### Container Lifecycle
```bash
# Container state management
docker create nginx:alpine              # Create container (not started)
docker start container_name            # Start created/stopped container
docker stop container_name             # Graceful stop (SIGTERM)
docker kill container_name             # Force stop (SIGKILL)
docker restart container_name          # Stop and start container
docker pause container_name            # Pause all processes
docker unpause container_name          # Unpause processes
docker wait container_name             # Wait for container to stop

# Container removal
docker rm container_name               # Remove stopped container
docker rm -f container_name            # Force remove running container
docker rm $(docker ps -aq)            # Remove all containers
docker rm $(docker ps -aq --filter status=exited)  # Remove exited containers
```

### Container Information
```bash
# Container listing
docker ps                             # Running containers
docker ps -a                          # All containers
docker ps -q                          # Container IDs only
docker ps --filter "status=running"   # Filter by status
docker ps --filter "name=web"         # Filter by name
docker ps --filter "ancestor=nginx"   # Filter by image
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Container inspection
docker inspect container_name         # Full container info (JSON)
docker inspect --format '{{.State.Status}}' container_name
docker inspect --format '{{.NetworkSettings.IPAddress}}' container_name
docker inspect --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' container_name

# Container statistics
docker stats                         # Live resource usage (all containers)
docker stats container_name          # Specific container stats
docker stats --no-stream            # One-time snapshot
docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"
```

### Container Execution
```bash
# Execute commands in containers
docker exec -it container_name bash          # Interactive shell
docker exec container_name ls -la /app       # Single command
docker exec -it container_name sh -c 'ps aux | grep nginx'  # Complex commands
docker exec --user root container_name chown -R app:app /data
docker exec -e VAR=value container_name env  # Set environment variables

# Attach to containers
docker attach container_name          # Attach to main process (PID 1)
docker logs container_name           # View container logs
docker logs -f container_name        # Follow logs in real-time
docker logs --tail 100 container_name  # Last 100 lines
docker logs --since "2024-01-01T00:00:00" container_name
docker logs --until "1h" container_name

# Copy files to/from containers
docker cp file.txt container_name:/app/          # Copy to container
docker cp container_name:/app/logs/ ./local-logs/  # Copy from container
docker cp container_name:/app/config.yml - | tar -xv  # Extract via stdout
```

### Container Monitoring
```bash
# Process information
docker top container_name                    # Running processes
docker exec container_name ps aux           # Detailed process list
docker exec container_name pstree -p        # Process tree

# Filesystem changes
docker diff container_name                   # Show changed files
docker export container_name > backup.tar   # Export container filesystem

# Container events
docker events                               # Real-time Docker events
docker events --filter container=myapp     # Filter by container
docker events --filter event=start         # Filter by event type
docker events --since=1h                   # Events in last hour
```

---

## Network Management

### Network Operations
```bash
# Network listing and information
docker network ls                          # List all networks
docker network inspect bridge              # Network details
docker network inspect --format '{{range .IPAM.Config}}{{.Subnet}}{{end}}' mynet

# Create networks
docker network create mynetwork            # Basic bridge network
docker network create \
  --driver bridge \
  --subnet=172.20.0.0/16 \
  --ip-range=172.20.240.0/20 \
  --gateway=172.20.0.1 \
  --opt com.docker.network.bridge.name=custom0 \
  --opt com.docker.network.driver.mtu=1450 \
  --label env=production \
  custom-bridge

# Overlay network (Swarm mode)
docker network create \
  --driver overlay \
  --subnet=10.0.9.0/24 \
  --attachable \
  --opt encrypted=true \
  multi-host-net

# Macvlan network
docker network create \
  --driver macvlan \
  --subnet=192.168.1.0/24 \
  --gateway=192.168.1.1 \
  --opt parent=eth0 \
  macvlan-net
```

### Network Connectivity
```bash
# Connect/disconnect containers
docker network connect mynetwork container_name    # Connect to network
docker network disconnect mynetwork container_name # Disconnect from network

# Network aliases
docker run -d --network mynet --network-alias database postgres
docker run -d --network mynet --network-alias web nginx

# Port management
docker run -p 80:8080 nginx                # Host:Container port mapping
docker run -p 127.0.0.1:80:8080 nginx     # Bind to specific interface
docker run -P nginx                        # Auto-assign exposed ports
docker run --expose 8080 nginx             # Expose port (no mapping)

# Check port mappings
docker port container_name                 # Show port mappings
docker port container_name 80              # Specific port mapping
```

### Network Cleanup
```bash
# Remove networks
docker network rm mynetwork               # Remove specific network
docker network rm $(docker network ls -q) # Remove all networks
docker network prune                      # Remove unused networks
docker network prune --filter until=24h  # Remove networks older than 24h
```

---

## Volume Management

### Volume Operations
```bash
# Volume listing and information
docker volume ls                          # List all volumes
docker volume inspect myvolume            # Volume details
docker volume inspect --format '{{.Mountpoint}}' myvolume

# Create volumes
docker volume create myvolume             # Basic named volume
docker volume create \
  --driver local \
  --opt type=nfs \
  --opt o=addr=192.168.1.1,rw \
  --opt device=:/path/to/dir \
  --label env=production \
  nfs-volume

# Volume with specific mount options
docker volume create \
  --driver local \
  --opt type=ext4 \
  --opt device=/dev/sdb1 \
  --opt o=defaults \
  block-volume

# Volume with bind mount driver
docker volume create \
  --driver local \
  --opt type=none \
  --opt device=/host/path \
  --opt o=bind \
  bind-volume
```

### Mount Types
```bash
# Named volumes (Docker managed)
docker run -v named-volume:/data nginx                # Named volume
docker run -v app-data:/app/data nginx               # Persistent data

# Bind mounts (Host filesystem)
docker run -v /host/path:/container/path nginx       # Basic bind mount
docker run -v /host/path:/container/path:ro nginx    # Read-only
docker run -v $(pwd)/logs:/app/logs nginx           # Current directory
docker run -v /host/path:/container/path:rw,Z nginx  # SELinux label

# tmpfs mounts (Memory-based)
docker run --tmpfs /tmp nginx                       # Basic tmpfs
docker run --tmpfs /tmp:rw,noexec,nosuid,size=100m nginx

# Mount with --mount syntax (preferred)
docker run --mount type=bind,src=/host,dst=/container nginx
docker run --mount type=volume,src=vol-name,dst=/data nginx
docker run --mount type=tmpfs,dst=/tmp,tmpfs-size=100m nginx
```

### Volume Management
```bash
# Volume backup and restore
docker run --rm \
  -v app-data:/data \
  -v $(pwd):/backup \
  ubuntu tar czf /backup/backup.tar.gz -C /data .

docker run --rm \
  -v app-data:/data \
  -v $(pwd):/backup \
  ubuntu tar xzf /backup/backup.tar.gz -C /data

# Volume migration between hosts
docker run --rm \
  -v source-vol:/data \
  alpine tar czf - -C /data . | \
  ssh remote-host 'docker run --rm -i -v dest-vol:/data alpine tar xzf - -C /data'

# Volume cleanup
docker volume rm myvolume                    # Remove specific volume
docker volume rm $(docker volume ls -q)     # Remove all volumes
docker volume prune                         # Remove unused volumes
docker volume prune --filter label=env=test # Remove by label
```

---

## Docker Compose

### Basic Compose Commands
```bash
# Service lifecycle
docker-compose up                          # Start services
docker-compose up -d                       # Start detached
docker-compose up --build                  # Rebuild images
docker-compose up --scale web=3            # Scale specific service
docker-compose up --force-recreate         # Force container recreation
docker-compose up service1 service2        # Start specific services

docker-compose down                        # Stop and remove containers
docker-compose down -v                     # Remove volumes too
docker-compose down --remove-orphans       # Remove orphaned containers

docker-compose stop                        # Stop services
docker-compose start                       # Start stopped services
docker-compose restart                     # Restart services
docker-compose pause                       # Pause services
docker-compose unpause                     # Unpause services
```

### Compose Management
```bash
# Service information
docker-compose ps                          # Service status
docker-compose ps -q                       # Service container IDs
docker-compose top                         # Running processes
docker-compose config                      # Validate and view configuration
docker-compose config --services           # List services
docker-compose port web 80                 # Show port mapping

# Service logs
docker-compose logs                        # All service logs
docker-compose logs -f                     # Follow logs
docker-compose logs -f web                 # Follow specific service
docker-compose logs --tail=100 web         # Last 100 lines
docker-compose logs --since=1h             # Logs since 1 hour ago

# Service execution
docker-compose exec web bash               # Execute in running service
docker-compose run --rm web python manage.py migrate  # One-off commands
docker-compose run --rm --no-deps web npm test        # Without dependencies
```

### Compose Building and Images
```bash
# Image management
docker-compose build                       # Build all services
docker-compose build web                   # Build specific service
docker-compose build --no-cache            # Build without cache
docker-compose build --parallel            # Parallel builds

docker-compose pull                        # Pull latest images
docker-compose push                        # Push images to registry
docker-compose images                      # Show service images
```

### Multi-Environment Compose
```bash
# Environment-specific configurations
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up
docker-compose --env-file .env.prod up
docker-compose -p production up            # Custom project name

# Override files
docker-compose -f docker-compose.yml -f docker-compose.override.yml up
docker-compose -f docker-compose.yml -f docker-compose.test.yml run web pytest
```

---

## Docker Swarm

### Swarm Management
```bash
# Swarm initialization
docker swarm init                          # Initialize swarm mode
docker swarm init --advertise-addr 192.168.1.100  # Specify advertise address
docker swarm join --token TOKEN MANAGER_IP:2377   # Join as worker
docker swarm join-token worker             # Get worker join token
docker swarm join-token manager           # Get manager join token
docker swarm leave                         # Leave swarm
docker swarm leave --force                 # Force leave (manager)

# Node management
docker node ls                            # List swarm nodes
docker node inspect node-id              # Node details
docker node update --availability drain node-id    # Drain node
docker node update --availability active node-id   # Activate node
docker node rm node-id                   # Remove node
docker node promote worker-node          # Promote to manager
docker node demote manager-node          # Demote to worker
```

### Service Management
```bash
# Service creation and management
docker service create --name web --replicas 3 -p 80:80 nginx
docker service create \
  --name web \
  --replicas 3 \
  --constraint 'node.role == worker' \
  --constraint 'node.labels.env == production' \
  --limit-memory=512M \
  --reserve-memory=256M \
  --limit-cpu=0.5 \
  --reserve-cpu=0.25 \
  --restart-condition on-failure \
  --restart-max-attempts 3 \
  --restart-delay 5s \
  --update-delay 10s \
  --update-parallelism 2 \
  --rollback-parallelism 1 \
  -p 80:80 \
  nginx:alpine

# Service information
docker service ls                         # List services
docker service ps web                     # Service tasks/replicas
docker service inspect web                # Service configuration
docker service logs web                   # Service logs
docker service logs -f web                # Follow service logs

# Service updates
docker service scale web=5                # Scale service
docker service update --image nginx:alpine web    # Update image
docker service update --env-add NODE_ENV=production web
docker service update --publish-add 443:443 web
docker service rollback web               # Rollback to previous version

# Service removal
docker service rm web                     # Remove service
docker service rm $(docker service ls -q) # Remove all services
```

### Stack Management
```bash
# Stack deployment
docker stack deploy -c docker-compose.yml mystack    # Deploy stack
docker stack deploy -c stack.yml --with-registry-auth mystack

# Stack information
docker stack ls                           # List stacks
docker stack ps mystack                   # Stack tasks
docker stack services mystack             # Stack services

# Stack management
docker stack rm mystack                   # Remove stack
```

### Swarm Secrets and Configs
```bash
# Secrets management
docker secret create db_password password.txt    # Create from file
echo "mypassword" | docker secret create db_pass -  # Create from stdin
docker secret ls                          # List secrets
docker secret inspect db_password         # Secret details
docker secret rm db_password              # Remove secret

# Service with secrets
docker service create \
  --name web \
  --secret db_password \
  --secret source=db_password,target=/run/secrets/password \
  nginx

# Configs management
docker config create nginx_conf nginx.conf       # Create config
docker config ls                          # List configs
docker config inspect nginx_conf          # Config details
docker config rm nginx_conf               # Remove config
```

---

## System Management

### System Information
```bash
# Docker system information
docker version                           # Docker version details
docker info                             # System-wide information
docker system df                        # Disk usage summary
docker system df -v                     # Detailed disk usage
docker system events                    # Real-time Docker events
docker system events --filter type=container
docker system events --since=1h

# Build information
docker buildx version                    # BuildX version
docker buildx ls                        # List builder instances
docker buildx inspect                   # Builder details
```

### System Cleanup
```bash
# Comprehensive cleanup
docker system prune                     # Remove unused data
docker system prune -a                  # Remove all unused data (including images)
docker system prune -a --volumes        # Include volumes in cleanup
docker system prune --filter until=24h # Remove data unused for 24h
docker system prune --filter label=env=test

# Component-specific cleanup
docker container prune                  # Remove stopped containers
docker image prune                     # Remove unused images
docker image prune -a                  # Remove all unused images
docker volume prune                    # Remove unused volumes
docker network prune                   # Remove unused networks
docker builder prune                   # Clean build cache
docker builder prune --keep-storage 10GB
```

### Daemon Management
```bash
# Daemon configuration
dockerd                                 # Start Docker daemon
dockerd --debug                         # Debug mode
dockerd --log-level=debug              # Debug logging
dockerd --config-file=/etc/docker/daemon.json

# Daemon information
docker info --format '{{.LoggingDriver}}'        # Current logging driver
docker info --format '{{.MemTotal}}'             # Total memory
docker info --format '{{.NCPU}}'                 # CPU count

# Service management (systemd)
systemctl status docker                # Check Docker service
systemctl start docker                 # Start Docker service
systemctl stop docker                  # Stop Docker service
systemctl restart docker               # Restart Docker service
systemctl enable docker                # Enable on boot
```

---

## Registry Operations

### Authentication
```bash
# Registry login/logout
docker login                           # Login to Docker Hub
docker login registry.example.com      # Private registry login
docker login -u username -p password registry.com
echo $PASSWORD | docker login -u $USERNAME --password-stdin registry.com
docker logout                         # Logout from registry
docker logout registry.example.com    # Logout from specific registry
```

### Image Distribution
```bash
# Push/pull operations
docker push myapp:latest              # Push to default registry
docker push registry.com/myapp:latest # Push to private registry
docker push --all-tags myapp          # Push all tags

docker pull nginx:alpine              # Pull from Docker Hub
docker pull registry.com/myapp:latest # Pull from private registry
docker pull --all-tags nginx          # Pull all tags

# Multi-platform operations
docker buildx build --platform linux/amd64,linux/arm64 -t myapp:latest --push .
docker manifest inspect nginx:alpine  # Multi-platform manifest
```

### Registry Management
```bash
# Search and explore
docker search nginx                   # Search Docker Hub
docker search --limit 10 --filter stars=3 nginx

# Local registry
docker run -d -p 5000:5000 --name registry registry:2
docker tag nginx:alpine localhost:5000/nginx:alpine
docker push localhost:5000/nginx:alpine

# Registry API
curl -X GET http://localhost:5000/v2/_catalog    # List repositories
curl -X GET http://localhost:5000/v2/nginx/tags/list  # List tags
```

---

## Monitoring & Debugging

### Performance Monitoring
```bash
# Real-time monitoring
docker stats                          # Live resource usage (all)
docker stats container_name           # Specific container
docker stats --no-stream             # One-time snapshot
docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}"

# Resource usage history
docker exec container_name top        # Process monitor
docker exec container_name htop       # Enhanced process monitor (if available)
docker exec container_name iotop      # I/O monitoring (if available)
```

### Health Monitoring
```bash
# Health checks
docker inspect --format='{{.State.Health.Status}}' container_name
docker inspect --format='{{range .State.Health.Log}}{{.Output}}{{end}}' container_name

# Custom health monitoring
#!/bin/bash
while true; do
    health=$(docker inspect --format='{{.State.Health.Status}}' myapp)
    if [ "$health" != "healthy" ]; then
        echo "Container unhealthy: $health"
        docker restart myapp
    fi
    sleep 30
done
```

### Debugging Tools
```bash
# Container debugging
docker exec -it container_name bash           # Interactive shell
docker exec container_name ps aux            # Process list
docker exec container_name netstat -tulpn    # Network connections
docker exec container_name ss -tulpn         # Socket statistics
docker exec container_name lsof             # Open files
docker exec container_name df -h            # Disk usage
docker exec container_name free -h          # Memory usage
docker exec container_name env              # Environment variables

# Network debugging
docker exec container_name ping google.com   # Connectivity test
docker exec container_name nslookup service-name  # DNS resolution
docker exec container_name curl -I http://service:80  # HTTP check
docker exec container_name traceroute 8.8.8.8       # Route tracing

# System debugging
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock docker ps
docker run --rm --pid=host --privileged alpine ps aux  # Host processes
```

---

## Security Commands

### Security Scanning
```bash
# Docker Scout (built-in)
docker scout quickview                        # Quick security overview
docker scout cves myapp:latest               # CVE scan
docker scout recommendations myapp:latest     # Security recommendations

# External scanners
trivy image nginx:latest                      # Trivy vulnerability scanner
trivy image --severity HIGH,CRITICAL myapp:latest
snyk container test nginx:latest             # Snyk security scanner
```

### Secure Runtime
```bash
# Security-hardened container run
docker run -d \
  --name secure-app \
  --user 1000:1000 \                         # Non-root user
  --read-only \                              # Read-only filesystem
  --tmpfs /tmp:rw,noexec,nosuid \           # Secure temp filesystem
  --security-opt=no-new-privileges \        # Prevent privilege escalation
  --cap-drop=ALL \                          # Drop all capabilities
  --cap-add=NET_BIND_SERVICE \              # Add only needed capabilities
  --pids-limit=100 \                        # Process limit
  --memory=256m \                           # Memory limit
  --cpus="0.5" \                            # CPU limit
  nginx:alpine

# Security options
--security-opt apparmor:profile_name        # AppArmor profile
--security-opt seccomp=default.json         # Seccomp profile
--security-opt label=level:s0:c100,c200    # SELinux label
--security-opt systempaths=unconfined      # System paths access
```

---

## Advanced Operations

### Multi-Platform Building
```bash
# Setup buildx
docker buildx create --name multiplatform --driver docker-container --use
docker buildx inspect --bootstrap

# Multi-platform builds
docker buildx build \
  --platform linux/amd64,linux/arm64,linux/arm/v7 \
  --tag myapp:latest \
  --push .

# Platform-specific builds
docker buildx build --platform linux/amd64 -t myapp:amd64 --load .
docker buildx build --platform linux/arm64 -t myapp:arm64 --load .
```

### Build Cache Management
```bash
# Cache management
docker buildx build --cache-from type=registry,ref=myapp:cache \
                   --cache-to type=registry,ref=myapp:cache,mode=max \
                   -t myapp:latest .

# Local cache
docker buildx build --cache-from type=local,src=/tmp/cache \
                   --cache-to type=local,dest=/tmp/cache \
                   -t myapp:latest .

# GitHub Actions cache
docker buildx build --cache-from type=gha \
                   --cache-to type=gha,mode=max \
                   -t myapp:latest .
```

### Container Orchestration
```bash
# Docker Swarm service constraints
docker service create \
  --constraint 'node.role == worker' \
  --constraint 'node.labels.env == production' \
  --constraint 'node.hostname != node-1' \
  --placement-pref 'spread=node.labels.zone' \
  nginx

# Update strategies
docker service update \
  --update-parallelism 2 \
  --update-delay 10s \
  --update-failure-action rollback \
  --rollback-parallelism 1 \
  --image nginx:alpine \
  web
```

---

## Troubleshooting

### Common Issues

#### Container Fails to Start
```bash
# Diagnostic steps
docker logs container_name                   # Check container logs
docker logs --details container_name         # Detailed logs
docker inspect container_name               # Container configuration
docker events --filter container=myapp      # Container events

# Test image interactively
docker run -it --entrypoint=/bin/sh myapp:latest
docker run -it --rm --entrypoint=/bin/bash myapp:latest
```

#### Network Connectivity Problems
```bash
# Network diagnostics
docker network ls                           # List networks
docker network inspect bridge               # Network configuration
docker exec container_name ip route         # Container routing
docker exec container_name ss -tulpn        # Socket status
docker port container_name                  # Port mappings
```

#### Performance Issues
```bash
# Performance analysis
docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"
docker system df -v                         # Disk usage
docker exec container_name top              # Process monitor
docker system events --filter event=die    # Container failures
```

#### Storage Problems
```bash
# Storage diagnostics
docker volume ls                            # List volumes
docker system df                           # Disk usage
docker inspect container_name | grep -A 10 "Mounts"
docker exec container_name df -h           # Container disk usage
```

### Advanced Debugging
```bash
# System-level debugging
docker run --rm --privileged --pid=host debian nsenter -t 1 -m -u -n -i sh
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock docker:cli docker ps

# Container filesystem exploration
docker diff container_name                  # Changed files
docker export container_name | tar -tv     # List all files
docker cp container_name:/app/debug.log .  # Extract files

# Performance profiling
docker exec container_name strace -p 1     # System call tracing
docker exec container_name lsof            # Open files and sockets
```

---

## Useful Aliases

### Essential Aliases
```bash
# Add to ~/.bashrc or ~/.zshrc
alias d='docker'
alias dc='docker-compose'
alias dcup='docker-compose up -d'
alias dcdown='docker-compose down'
alias dclog='docker-compose logs -f'

# Container management
alias dps='docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"'
alias dpsa='docker ps -a --format "table {{.Names}}\t{{.Status}}\t{{.CreatedAt}}"'
alias dimg='docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"'

# Logs and execution
alias dlog='docker logs -f'
alias dexec='docker exec -it'
alias dbash='docker exec -it $1 bash'
alias dsh='docker exec -it $1 sh'

# Cleanup aliases
alias dclean='docker system prune -a --volumes'
alias dstop='docker stop $(docker ps -q)'
alias drm='docker rm $(docker ps -aq)'
alias drmi='docker rmi $(docker images -q)'
```

### Useful Functions
```bash
# Add to ~/.bashrc or ~/.zshrc

# Enter container shell
denter() {
    docker exec -it $1 ${2:-bash}
}

# Get container IP
dip() {
    docker inspect --format '{{.NetworkSettings.IPAddress}}' $1
}

# Kill and remove all containers
dkill() {
    docker rm -f $(docker ps -aq)
}

# Build and run with same tag
dbr() {
    docker build -t $1 . && docker run --rm -it $1
}

# Quick container run with cleanup
drun() {
    docker run --rm -it $@
}
```

---

## Cross-References

### Essential Reading
- **[[Docker fundamental]]** - Core Docker concepts and architecture
- **[[Dockerfile]]** - Container image building instructions
- **[[Docker Security]]** - Security commands and best practices
- **[[Docker Networking]]** - Network management and configuration
- **[[Docker Storage & Volumes Internals]]** - Volume and storage operations

### Advanced Topics
- **[[Docker Compose Production Setup]]** - Multi-container orchestration
- **[[Docker Performance & Monitoring]]** - Performance analysis and optimization
- **[[Docker CICD]]** - Automated pipeline integration

### Quick Navigation
- **Getting Started**: Docker Commands → Docker fundamental → Dockerfile
- **Production Setup**: Docker Commands → Docker Security → Docker Compose Production Setup
- **DevOps Workflows**: Docker Commands → Docker CICD → Docker Performance & Monitoring

---

*This comprehensive command reference provides practical Docker CLI usage for development, testing, and production environments.*