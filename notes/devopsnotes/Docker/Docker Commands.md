### Images

```bash
# Image management
docker images                                           # List all images
docker images -a                                        # Include intermediate images
docker pull nginx:alpine                                # Pull specific tag
docker pull --all-tags nginx                           # Pull all tags
docker build -t myapp:latest .                         # Build from Dockerfile
docker build --no-cache -t myapp:v1.0 .               # Build without cache
docker build --target production -t myapp:prod .       # Multi-stage build
docker tag myapp:latest myapp:v1.0                     # Tag image
docker rmi image_id                                     # Remove image
docker rmi $(docker images -q)                         # Remove all images
docker image prune -a                                  # Remove unused images
```

### Basic Container Management

```bash
# Container lifecycle
docker run nginx:alpine                                 # Run container (foreground)
docker run -d nginx:alpine                             # Run detached
docker run -it ubuntu:latest bash                      # Interactive terminal
docker run --rm ubuntu:latest echo "hello"             # Remove after exit
docker start container_name                             # Start stopped container
docker stop container_name                              # Graceful stop
docker kill container_name                              # Force kill
docker restart container_name                           # Restart container
docker pause container_name                             # Pause processes
docker unpause container_name                           # Unpause processes
docker rm container_name                                # Remove container
docker rm -f container_name                             # Force remove running container
docker rm $(docker ps -aq)                             # Remove all containers
```

### Container Information

```bash
# Container status and info
docker ps                                               # Running containers
docker ps -a                                            # All containers
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
docker inspect container_name                           # Detailed info (JSON)
docker inspect --format '{{.State.Status}}' container_name
docker logs container_name                              # View logs
docker logs -f container_name                          # Follow logs
docker logs --since=1h --tail=100 container_name       # Filtered logs
docker port container_name                              # Port mappings
```

## Advanced Container Operations

### Resource Management

```bash
# Advanced run options
docker run -d \
  --name web \
  --restart=unless-stopped \                             # Restart policy
  --memory=512m --memory-swap=1g \                       # Memory limits
  --cpus="1.5" --cpu-shares=1024 \                      # CPU limits
  --pids-limit=100 \                                     # Process limit
  --ulimit nofile=1024:2048 \                           # File descriptor limits
  --oom-score-adj=-500 \                                 # OOM killer priority
  --security-opt=no-new-privileges \                     # Security options
  --cap-drop=ALL --cap-add=NET_BIND_SERVICE \           # Capabilities
  -p 8080:80 \                                          # Port mapping
  -v app-data:/data \                                    # Named volume
  -v /host/logs:/app/logs:ro \                          # Bind mount (read-only)
  --tmpfs /tmp:noexec,nosuid,size=100m \                # tmpfs mount
  --network=custom-net \                                 # Custom network
  -e NODE_ENV=production \                               # Environment variable
  -e DB_PASSWORD_FILE=/run/secrets/db_pass \             # Secret file
  nginx:alpine

# Resource monitoring
docker stats                                            # Live resource usage
docker stats --no-stream                               # One-time snapshot
docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"
docker top container_name                               # Process list inside container
```

### Container Execution and Interaction

```bash
# Execute commands in containers
docker exec -it container_name bash                    # Interactive shell
docker exec container_name ls -la /app                 # Single command
docker exec -it web sh -c 'ps aux | grep nginx'       # Complex commands
docker attach container_name                            # Attach to main process
docker cp file.txt container_name:/app/                # Copy file to container
docker cp container_name:/app/logs/ ./local-logs/      # Copy from container
docker diff container_name                              # Show filesystem changes
```

### Container Events and Debugging

```bash
# Monitoring and debugging
docker events                                          # Real-time events
docker events --filter container=web --since=1h       # Filtered events
docker events --filter type=container                  # Container events only
docker wait container_name                              # Wait for container to stop
docker container prune                                  # Remove stopped containers
docker container prune --filter until=24h             # Remove old containers
```

## Networking

### Network Management

```bash
# Network operations
docker network ls                                       # List networks
docker network create mynetwork                        # Create bridge network
docker network create --driver bridge --subnet=172.20.0.0/16 mynet
docker network create --driver overlay --attachable swarm-net
docker network inspect bridge                          # Network details
docker network connect mynetwork container_name        # Connect container
docker network disconnect mynetwork container_name     # Disconnect container
docker network rm mynetwork                            # Remove network
docker network prune                                   # Remove unused networks
```

### Port and Service Discovery

```bash
# Port mapping variations
docker run -p 80:8080 nginx                           # Host:Container
docker run -p 127.0.0.1:80:8080 nginx                # Bind to localhost
docker run -P nginx                                   # Auto-assign ports
docker run --expose 8080 nginx                        # Expose port (no mapping)
```

## Volume and Storage Management

### Volume Operations

```bash
# Volume management
docker volume ls                                        # List volumes
docker volume create myvolume                          # Create named volume
docker volume create --driver local --opt type=nfs myvolume
docker volume inspect myvolume                         # Volume details
docker volume rm myvolume                              # Remove volume
docker volume prune                                    # Remove unused volumes
docker volume prune --filter label=env=dev            # Conditional removal
```

### Mount Types

```bash
# Different mount types
docker run -v named-volume:/data nginx                 # Named volume
docker run -v /host/path:/container/path nginx         # Bind mount
docker run -v /host/path:/container/path:ro nginx      # Read-only bind mount
docker run --mount type=bind,src=/host,dst=/container nginx
docker run --mount type=volume,src=vol-name,dst=/data nginx
docker run --tmpfs /tmp nginx                          # tmpfs mount
docker run --mount type=tmpfs,dst=/tmp,tmpfs-size=100m nginx
```

## Docker Compose

### Basic Compose Commands

```bash
# Compose operations
docker-compose up                                       # Start services
docker-compose up -d                                   # Start detached
docker-compose up --build                              # Rebuild images
docker-compose up --scale web=3                        # Scale service
docker-compose down                                     # Stop and remove
docker-compose down -v                                 # Remove volumes too
docker-compose stop                                    # Stop services
docker-compose start                                   # Start stopped services
docker-compose restart                                 # Restart services
docker-compose pause                                   # Pause services
docker-compose unpause                                 # Unpause services
```

### Compose Management

```bash
# Service management
docker-compose ps                                      # Service status
docker-compose logs                                    # All service logs
docker-compose logs -f web                            # Follow specific service
docker-compose exec web bash                          # Execute in service
docker-compose run --rm web python manage.py migrate  # One-off commands
docker-compose config                                  # Validate and view config
docker-compose pull                                   # Pull latest images
docker-compose build                                  # Build services
docker-compose images                                 # Show service images
```

## Docker Swarm

### Swarm Management

```bash
# Swarm initialization
docker swarm init                                      # Initialize swarm
docker swarm init --advertise-addr 192.168.1.100     # Specify address
docker swarm join --token TOKEN MANAGER_IP:2377       # Join as worker
docker swarm join-token worker                         # Get worker token
docker swarm join-token manager                        # Get manager token
docker swarm leave                                     # Leave swarm
docker swarm leave --force                             # Force leave (manager)
```

### Service Management

```bash
# Service operations
docker service create --name web --replicas 3 -p 80:80 nginx
docker service ls                                      # List services
docker service ps web                                  # Service tasks
docker service inspect web                             # Service details
docker service scale web=5                            # Scale service
docker service update --image nginx:alpine web        # Update service
docker service rm web                                 # Remove service
docker service logs web                               # Service logs
```

### Stack Management

```bash
# Stack operations
docker stack deploy -c docker-compose.yml mystack     # Deploy stack
docker stack ls                                       # List stacks
docker stack ps mystack                               # Stack tasks
docker stack services mystack                         # Stack services
docker stack rm mystack                               # Remove stack
```

## Registry Operations

### Image Registry

```bash
# Registry operations
docker login                                           # Login to Docker Hub
docker login registry.example.com                     # Private registry
docker logout                                         # Logout
docker push myapp:latest                              # Push image
docker push --all-tags myapp                          # Push all tags
docker search nginx                                    # Search Docker Hub
docker pull registry.example.com/myapp:latest         # Pull from private registry
```

### Image Management

```bash
# Image operations
docker save -o myapp.tar myapp:latest                 # Export image
docker load -i myapp.tar                              # Import image
docker export container_name > container.tar          # Export container
docker import container.tar myimage:latest            # Import as image
docker history nginx:alpine                           # Image layers
docker image inspect nginx:alpine                     # Image metadata
```

## System Operations

### System Information and Cleanup

```bash
# System information
docker system df                                       # Disk usage summary
docker system df -v                                   # Detailed disk usage
docker system info                                    # System information
docker version                                        # Version information
docker system events                                  # System events
docker system events --filter type=container          # Filtered events
docker system events --since=1h                       # Recent events

# Cleanup operations
docker system prune                                    # Remove unused data
docker system prune -a                                # Remove all unused data
docker system prune -a --volumes                      # Include volumes
docker system prune --filter until=24h                # Remove old data
docker builder prune                                   # Clean build cache
docker builder prune --keep-storage 10GB              # Keep recent cache
docker image prune                                     # Remove unused images
docker container prune                                 # Remove stopped containers
docker volume prune                                    # Remove unused volumes
docker network prune                                   # Remove unused networks
```

### Daemon Configuration

```bash
# Docker daemon
docker info --format '{{.LoggingDriver}}'             # Current settings
dockerd                                                # Start daemon
dockerd --debug                                        # Debug mode
dockerd --log-level=debug                              # Debug logging
systemctl status docker                                # Service status (systemd)
systemctl restart docker                               # Restart service
```

## Security and Secrets

### Security Options

```bash
# Security configurations
docker run --user 1000:1000 nginx                     # Run as specific user
docker run --read-only nginx                          # Read-only filesystem
docker run --security-opt no-new-privileges nginx     # No privilege escalation
docker run --cap-drop ALL --cap-add NET_BIND_SERVICE nginx
docker run --privileged nginx                         # Privileged mode (avoid)
docker run --device /dev/sda:/dev/sda nginx          # Device access
```

### Secrets Management

```bash
# Docker secrets (Swarm mode)
docker secret create db_password /path/to/password.txt
docker secret ls                                       # List secrets
docker secret inspect db_password                      # Secret details
docker secret rm db_password                          # Remove secret
docker service create --secret db_password nginx      # Use secret in service
```

## Troubleshooting

### Common Debugging Commands

```bash
# Debugging containers
docker logs --details container_name                   # Detailed logs
docker exec -it container_name ps aux                 # Process list
docker exec -it container_name netstat -tulpn         # Network connections
docker exec -it container_name df -h                  # Disk usage
docker exec -it container_name env                    # Environment variables
docker inspect --format '{{.State.Health}}' container_name  # Health status
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock docker ps
```

### Performance Monitoring

```bash
# Performance analysis
docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}"
docker exec container_name top                        # Real-time processes
docker exec container_name iotop                      # I/O monitoring
docker exec container_name free -h                    # Memory usage
docker system events --filter event=die               # Container failures
```

## Useful Aliases and Functions

```bash
# Handy aliases (add to ~/.bashrc or ~/.zshrc)
alias dps='docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"'
alias dimg='docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"'
alias dlog='docker logs -f'
alias dexec='docker exec -it'
alias dstop='docker stop $(docker ps -q)'
alias dclean='docker system prune -a --volumes'

# Useful functions
denter() { docker exec -it $1 ${2:-bash}; }           # Enter container
dip() { docker inspect --format '{{.NetworkSettings.IPAddress}}' $1; }
dkill() { docker rm -f $(docker ps -aq); }            # Kill all containers
```