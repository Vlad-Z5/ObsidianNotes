### Images

```bash
# Image management
docker images # List all images
docker images -a # Include intermediate images
docker pull nginx:alpine # Pull specific tag
docker pull --all-tags nginx # Pull all tags
docker build -t myapp:latest . # Build from Dockerfile
docker build --no-cache -t myapp:v1.0 . # Build without cache
docker build --target production -t myapp:prod . # Multi-stage build
docker tag myapp:latest myapp:v1.0 # Tag image
docker rmi image_id # Remove image
docker rmi $(docker images -q) # Remove all images
docker image prune -a # Remove unused images
```

### Image Management with Advanced Options

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

### Image Tagging Strategies

```bash
# Semantic versioning
docker tag myapp:latest myapp:1.2.3
docker tag myapp:latest myapp:1.2
docker tag myapp:latest myapp:1

# Git-based tagging
docker tag myapp:latest myapp:$(git rev-parse --short HEAD)
docker tag myapp:latest myapp:$(git describe --tags --always)

# Environment-based tagging
docker tag myapp:latest myapp:dev-$(date +%Y%m%d)
docker tag myapp:latest myapp:staging-v1.2.3
docker tag myapp:latest myapp:prod-$(git rev-parse --short HEAD)

# CI/CD pipeline tagging
docker tag myapp:latest myapp:build-${BUILD_NUMBER}
docker tag myapp:latest myapp:pr-${PULL_REQUEST_ID}
docker tag myapp:latest myapp:branch-${BRANCH_NAME//\//-}

# DevOps tagging script
#!/bin/bash
VERSION=$(git describe --tags --always)
COMMIT=$(git rev-parse --short HEAD)
DATE=$(date +%Y%m%d-%H%M%S)

docker build -t myapp:latest .
docker tag myapp:latest myapp:${VERSION}
docker tag myapp:latest myapp:${COMMIT}
docker tag myapp:latest myapp:${DATE}

if [[ "${BRANCH_NAME}" == "main" ]]; then
    docker tag myapp:latest myapp:stable
fi
```

### Image Size Reduction Techniques

```bash
# Layer consolidation examples
# ❌ Bad - creates multiple layers
docker build -t bad-example - <<EOF
FROM ubuntu:20.04
RUN apt-get update
RUN apt-get install -y curl
RUN apt-get install -y wget
RUN rm -rf /var/lib/apt/lists/*
EOF

# ✅ Good - single layer
docker build -t good-example - <<EOF
FROM ubuntu:20.04
RUN apt-get update && \
    apt-get install -y curl wget && \
    rm -rf /var/lib/apt/lists/*
EOF

# Base image comparison
docker images alpine:latest    # ~5MB
docker images ubuntu:20.04    # ~72MB
docker images node:18-alpine  # ~110MB
docker images node:18         # ~993MB
```

### Basic Container Management

```bash
# Container lifecycle
docker run nginx:alpine # Run container (foreground)
docker run -d nginx:alpine # Run detached
docker run -it ubuntu:latest bash # Interactive terminal
docker run --rm ubuntu:latest echo "hello" # Remove after exit
docker start container_name # Start stopped container
docker stop container_name # Graceful stop
docker kill container_name # Force kill
docker restart container_name # Restart container
docker pause container_name # Pause processes
docker unpause container_name # Unpause processes
docker rm container_name # Remove container
docker rm -f container_name # Force remove running container
docker rm $(docker ps -aq) # Remove all containers
```

### Container Information

```bash
# Container status and info
docker ps # Running containers
docker ps -a # All containers
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
docker inspect container_name # Detailed info (JSON)
docker inspect --format '{{.State.Status}}' container_name
docker logs container_name # View logs
docker logs -f container_name # Follow logs
docker logs --since=1h --tail=100 container_name # Filtered logs
docker port container_name # Port mappings
```

## Advanced Container Operations

### Resource Management

```bash
# Advanced run options
docker run -d \
  --name web \
  --restart=unless-stopped \ # Restart policy
  --memory=512m --memory-swap=1g \ # Memory limits
  --cpus="1.5" --cpu-shares=1024 \ # CPU limits
  --pids-limit=100 \ # Process limit
  --ulimit nofile=1024:2048 \ # File descriptor limits
  --oom-score-adj=-500 \ # OOM killer priority
  --security-opt=no-new-privileges \ # Security options
  --cap-drop=ALL --cap-add=NET_BIND_SERVICE \ # Capabilities
  -p 8080:80 \ # Port mapping
  -v app-data:/data \ # Named volume
  -v /host/logs:/app/logs:ro \ # Bind mount (read-only)
  --tmpfs /tmp:noexec,nosuid,size=100m \ # tmpfs mount
  --network=custom-net \ # Custom network
  -e NODE_ENV=production \ # Environment variable
  -e DB_PASSWORD_FILE=/run/secrets/db_pass \ # Secret file
  nginx:alpine

# Resource monitoring
docker stats # Live resource usage
docker stats --no-stream # One-time snapshot
docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"
docker top container_name # Process list inside container
```

### Container Execution and Interaction

```bash
# Execute commands in containers
docker exec -it container_name bash # Interactive shell
docker exec container_name ls -la /app # Single command
docker exec -it web sh -c 'ps aux | grep nginx' # Complex commands
docker attach container_name # Attach to main process
docker cp file.txt container_name:/app/ # Copy file to container
docker cp container_name:/app/logs/ ./local-logs/ # Copy from container
docker diff container_name # Show filesystem changes
```

### Container Events and Debugging

```bash
# Monitoring and debugging
docker events # Real-time events
docker events --filter container=web --since=1h # Filtered events
docker events --filter type=container # Container events only
docker wait container_name # Wait for container to stop
docker container prune # Remove stopped containers
docker container prune --filter until=24h # Remove old containers
```

## Networking

### Network Management

```bash
# Network operations
docker network ls # List networks
docker network create mynetwork # Create bridge network
docker network create --driver bridge --subnet=172.20.0.0/16 mynet
docker network create --driver overlay --attachable swarm-net
docker network inspect bridge # Network details
docker network connect mynetwork container_name # Connect container
docker network disconnect mynetwork container_name # Disconnect container
docker network rm mynetwork # Remove network
docker network prune # Remove unused networks
```

### Port and Service Discovery

```bash
# Port mapping variations
docker run -p 80:8080 nginx # Host:Container
docker run -p 127.0.0.1:80:8080 nginx # Bind to localhost
docker run -P nginx # Auto-assign ports
docker run --expose 8080 nginx # Expose port (no mapping)
```

## Volume and Storage Management

### Volume Operations

```bash
# Volume management
docker volume ls # List volumes
docker volume create myvolume # Create named volume
docker volume create --driver local --opt type=nfs myvolume
docker volume inspect myvolume # Volume details
docker volume rm myvolume # Remove volume
docker volume prune # Remove unused volumes
docker volume prune --filter label=env=dev # Conditional removal
```

### Mount Types

```bash
# Different mount types
docker run -v named-volume:/data nginx # Named volume
docker run -v /host/path:/container/path nginx # Bind mount
docker run -v /host/path:/container/path:ro nginx # Read-only bind mount
docker run --mount type=bind,src=/host,dst=/container nginx
docker run --mount type=volume,src=vol-name,dst=/data nginx
docker run --tmpfs /tmp nginx # tmpfs mount
docker run --mount type=tmpfs,dst=/tmp,tmpfs-size=100m nginx
```

## Docker Compose

### Basic Compose Commands

```bash
# Compose operations
docker-compose up # Start services
docker-compose up -d # Start detached
docker-compose up --build # Rebuild images
docker-compose up --scale web=3 # Scale service
docker-compose down # Stop and remove
docker-compose down -v # Remove volumes too
docker-compose stop # Stop services
docker-compose start # Start stopped services
docker-compose restart # Restart services
docker-compose pause # Pause services
docker-compose unpause # Unpause services
```

### Compose Management

```bash
# Service management
docker-compose ps # Service status
docker-compose logs # All service logs
docker-compose logs -f web # Follow specific service
docker-compose exec web bash # Execute in service
docker-compose run --rm web python manage.py migrate # One-off commands
docker-compose config # Validate and view config
docker-compose pull # Pull latest images
docker-compose build # Build services
docker-compose images # Show service images
```

## Docker Swarm

### Swarm Management

```bash
# Swarm initialization
docker swarm init # Initialize swarm
docker swarm init --advertise-addr 192.168.1.100 # Specify address
docker swarm join --token TOKEN MANAGER_IP:2377 # Join as worker
docker swarm join-token worker # Get worker token
docker swarm join-token manager # Get manager token
docker swarm leave # Leave swarm
docker swarm leave --force # Force leave (manager)
```

### Service Management

```bash
# Service operations
docker service create --name web --replicas 3 -p 80:80 nginx
docker service ls # List services
docker service ps web # Service tasks
docker service inspect web # Service details
docker service scale web=5 # Scale service
docker service update --image nginx:alpine web # Update service
docker service rm web # Remove service
docker service logs web # Service logs
```

### Stack Management

```bash
# Stack operations
docker stack deploy -c docker-compose.yml mystack # Deploy stack
docker stack ls # List stacks
docker stack ps mystack # Stack tasks
docker stack services mystack # Stack services
docker stack rm mystack # Remove stack
```

## Registry Operations

### Image Registry

```bash
# Registry operations
docker login # Login to Docker Hub
docker login registry.example.com # Private registry login
docker logout # Logout from registry
docker push myapp:latest # Push image to registry
docker push --all-tags myapp # Push all tags
docker search nginx # Search images on Docker Hub
docker pull registry.example.com/myapp:latest # Pull image from private registry
```

### Image Management

```bash
# Image management
docker save -o myapp.tar myapp:latest # Export image to tarball
docker load -i myapp.tar # Import image from tarball
docker export container_name > container.tar # Export container filesystem
docker import container.tar myimage:latest # Import tarball as image
docker history nginx:alpine # Show image layers history
docker image inspect nginx:alpine # Show image metadata
```

## System Operations

### System Information and Cleanup

```bash
# System information and cleanup
docker system df # Disk usage summary
docker system df -v # Detailed disk usage
docker system info # Docker system info
docker version # Docker version info
docker system events # Real-time Docker events
docker system events --filter type=container # Filter container events
docker system events --since=1h # Events in last hour

docker system prune # Remove unused data
docker system prune -a # Remove all unused data including images
docker system prune -a --volumes # Include volumes in prune
docker system prune --filter until=24h # Remove data unused for 24h
docker builder prune # Clean build cache
docker builder prune --keep-storage 10GB # Keep 10GB cache
docker image prune # Remove unused images
docker container prune # Remove stopped containers
docker volume prune # Remove unused volumes
docker network prune # Remove unused networks
```

### Daemon Configuration

```bash
# Docker daemon management
docker info --format '{{.LoggingDriver}}' # Show current logging driver
dockerd # Start Docker daemon
dockerd --debug # Start daemon in debug mode
dockerd --log-level=debug # Enable debug logging
systemctl status docker # Check Docker service status (systemd)
systemctl restart docker # Restart Docker service
```

## Security and Secrets

### Security Options

```bash
# Security configurations
docker run --user 1000:1000 nginx # Run container as specific user
docker run --read-only nginx # Run container with read-only filesystem
docker run --security-opt no-new-privileges nginx # Disable privilege escalation
docker run --cap-drop ALL --cap-add NET_BIND_SERVICE nginx # Drop all caps except NET_BIND_SERVICE
docker run --privileged nginx # Run in privileged mode (avoid unless necessary)
docker run --device /dev/sda:/dev/sda nginx # Give container access to host device
```

### Secrets Management

```bash
# Docker secrets (Swarm mode)
docker secret create db_password /path/to/password.txt # Create secret from file
docker secret ls # List all secrets
docker secret inspect db_password # Show secret details
docker secret rm db_password # Remove secret
docker service create --secret db_password nginx # Use secret in a service
```

## Troubleshooting

### Common Debugging Commands

```bash
# Debugging containers
docker logs --details container_name # Show detailed logs
docker exec -it container_name ps aux # List processes inside container
docker exec -it container_name netstat -tulpn # Show network connections
docker exec -it container_name df -h # Disk usage inside container
docker exec -it container_name env # Show environment variables
docker inspect --format '{{.State.Health}}' container_name # Show container health status
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock docker ps # List host containers from container
```

### Performance Monitoring

```bash
# Performance analysis
docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}" # Resource usage table
docker exec container_name top # Real-time process monitor
docker exec container_name iotop # I/O monitoring (if installed)
docker exec container_name free -h # Memory usage inside container
docker system events --filter event=die # Monitor container failures
```

## Useful Aliases and Functions

```bash
# Handy aliases (add to ~/.bashrc or ~/.zshrc)
alias dps='docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"' # Pretty container list
alias dimg='docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"' # Pretty image list
alias dlog='docker logs -f' # Follow container logs
alias dexec='docker exec -it' # Exec into container interactively
alias dstop='docker stop $(docker ps -q)' # Stop all running containers
alias dclean='docker system prune -a --volumes' # Clean all unused data including volumes
```

## Useful Functions

```bash
# Handy functions (add to ~/.bashrc or ~/.zshrc)
denter() { docker exec -it $1 ${2:-bash}; } # Enter container shell (default bash)
dip() { docker inspect --format '{{.NetworkSettings.IPAddress}}' $1; } # Get container IP
dkill() { docker rm -f $(docker ps -aq); } # Kill and remove all containers
```

