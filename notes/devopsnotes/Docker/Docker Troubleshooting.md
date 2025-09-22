# Docker Troubleshooting

**Docker troubleshooting** encompasses systematic approaches to diagnose, debug, and resolve container, image, network, and resource issues in development and production environments.


## Container Issues

### Container Won't Start

```bash
# Check container status and exit code
docker ps -a
docker logs container_name
docker inspect container_name

# Common startup failures
# Exit code 125: Docker daemon error
# Exit code 126: Container command not executable
# Exit code 127: Container command not found
# Exit code 1: General application error

# Debug container startup
docker run -it --rm image_name /bin/bash
docker run -it --rm --entrypoint="" image_name /bin/bash

# Check image layers and commands
docker history image_name
docker inspect image_name | jq '.[0].Config'
```

### Container Exits Immediately

```bash
# Debug PID 1 issues
docker run -it --rm image_name ps aux

# Check if main process is backgrounding
docker run -it --rm image_name sh -c 'your_command & wait'

# Override entrypoint for debugging
docker run -it --rm --entrypoint=/bin/bash image_name

# Check for missing dependencies
docker run -it --rm image_name ldd /path/to/binary
docker run -it --rm image_name ls -la /usr/local/bin/
```

### Application Not Responding

```bash
# Check if process is running
docker exec container_name ps aux
docker exec container_name top

# Check application logs
docker logs container_name -f --tail 100
docker exec container_name tail -f /var/log/app.log

# Check port binding
docker port container_name
netstat -tlnp | grep :port_number

# Test connectivity
docker exec container_name curl -v localhost:8080
docker exec container_name netstat -tlnp
```

### Container Resource Issues

```bash
# Check container resource usage
docker stats container_name
docker exec container_name free -h
docker exec container_name df -h

# Memory issues debugging
docker exec container_name cat /proc/meminfo
docker exec container_name ps aux --sort=-%mem | head -10

# CPU issues debugging
docker exec container_name top -p 1
docker exec container_name cat /proc/loadavg
```

---

## Image Problems

### Build Failures

```bash
# Debug build context
docker build --no-cache -t image_name .
docker build --progress=plain -t image_name .

# Check build context size
du -sh .
ls -la .dockerignore

# Debug specific build stage
docker build --target stage_name -t debug_image .

# Inspect failed build
docker run -it --rm $(docker build -q --target stage_name .) /bin/bash
```

### Large Image Sizes

```bash
# Analyze image layers
docker history --human image_name
docker inspect image_name | jq '.[0].RootFS.Layers'

# Use dive for detailed analysis
dive image_name

# Check for large files
docker run --rm -it image_name find / -size +100M -type f 2>/dev/null
docker run --rm -it image_name du -sh /* 2>/dev/null | sort -hr

# Optimize Dockerfile
# Use multi-stage builds
# Minimize layers
# Clean up in same RUN command
RUN apt-get update && \
    apt-get install -y package && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
```

### Image Pull Issues

```bash
# Debug registry connectivity
docker pull --disable-content-trust image_name
docker pull --verbose image_name

# Check registry authentication
docker login registry_url
cat ~/.docker/config.json

# Inspect registry
curl -v https://registry_url/v2/
docker search image_name

# Use alternative registry
docker pull alternate_registry/image_name
docker tag alternate_registry/image_name original_name
```

---

## Network Troubleshooting

### Container Connectivity Issues

```bash
# List networks and inspect
docker network ls
docker network inspect network_name

# Check container network settings
docker inspect container_name | jq '.[0].NetworkSettings'

# Test connectivity between containers
docker exec container1 ping container2
docker exec container1 nslookup container2
docker exec container1 telnet container2 port

# Debug DNS resolution
docker exec container_name cat /etc/resolv.conf
docker exec container_name nslookup google.com
```

### Port Binding Problems

```bash
# Check port mappings
docker port container_name
docker ps --format "table {{.Names}}\t{{.Ports}}"

# Test port accessibility
netstat -tlnp | grep :port
ss -tlnp | grep :port
lsof -i :port

# Check firewall rules
iptables -L DOCKER
iptables -L DOCKER-USER
ufw status

# Debug port conflicts
docker run -p host_port:container_port image_name
# Error: port already in use
docker ps --filter "publish=host_port"
```

### Network Performance Issues

```bash
# Test network performance between containers
docker exec container1 iperf3 -s
docker exec container2 iperf3 -c container1

# Check network interface statistics
docker exec container_name cat /proc/net/dev
docker exec container_name ip -s link

# Monitor network traffic
docker exec container_name tcpdump -i eth0
tcpdump -i docker0

# Check network driver issues
docker network ls --format "table {{.Name}}\t{{.Driver}}"
docker system info | grep -A 10 "Network:"
```

---

## Storage & Volume Issues

### Volume Mount Problems

```bash
# Check volume mounts
docker inspect container_name | jq '.[0].Mounts'
docker exec container_name mount | grep -E "(bind|volume)"

# Debug permission issues
docker exec container_name ls -la /mounted/path
docker exec container_name id
stat /host/path

# Fix ownership issues
docker exec container_name chown -R user:group /mounted/path
docker run -v /host/path:/container/path:Z image_name  # SELinux

# Check volume driver
docker volume ls
docker volume inspect volume_name
```

### Disk Space Issues

```bash
# Check Docker disk usage
docker system df
docker system df -v

# Clean up Docker resources
docker system prune -a
docker image prune -a
docker container prune
docker volume prune
docker network prune

# Check container filesystem usage
docker exec container_name df -h
docker exec container_name du -sh /var/log

# Monitor disk I/O
docker exec container_name iostat 1 5
iotop -p $(docker inspect container_name | jq -r '.[0].State.Pid')
```

### File Permission Issues

```bash
# Debug user/group mapping
docker exec container_name id
id $(whoami)

# Check file ownership
docker exec container_name ls -la /problematic/path
ls -la /host/path

# Use user namespace mapping
docker run --user $(id -u):$(id -g) image_name
docker run --userns=host image_name

# Fix with init container
docker run --rm -v volume_name:/data alpine chown -R 1000:1000 /data
```

---

## Performance Problems

### Slow Container Startup

```bash
# Profile container startup
time docker run image_name
docker run --init image_name  # Use init process

# Check image pull time
time docker pull image_name

# Analyze startup commands
docker run --rm image_name time command
strace -f -e trace=execve docker run image_name

# Optimize with multi-stage builds
FROM node:alpine AS builder
COPY package*.json ./
RUN npm ci --only=production

FROM node:alpine
COPY --from=builder /app/node_modules ./node_modules
COPY . .
CMD ["node", "app.js"]
```

### High CPU Usage

```bash
# Monitor CPU usage
docker stats container_name
docker exec container_name top
htop -p $(docker inspect container_name | jq -r '.[0].State.Pid')

# Profile application
docker exec container_name perf top
docker exec container_name strace -p 1

# Check for CPU throttling
docker exec container_name cat /sys/fs/cgroup/cpu/cpu.stat
docker exec container_name cat /proc/loadavg

# Set CPU limits
docker run --cpus="1.5" image_name
docker update --cpus="1.0" container_name
```

### Memory Issues

```bash
# Monitor memory usage
docker stats --no-stream container_name
docker exec container_name free -h
docker exec container_name cat /proc/meminfo

# Check for memory leaks
docker exec container_name ps aux --sort=-%mem
docker exec container_name pmap -x 1

# Check OOM kills
dmesg | grep -i "killed process"
journalctl -u docker | grep -i oom

# Set memory limits
docker run -m 512m image_name
docker update -m 1g container_name

# Debug memory allocation
docker exec container_name cat /proc/1/status | grep -i vmsize
docker exec container_name cat /sys/fs/cgroup/memory/memory.usage_in_bytes
```

---

## Resource Constraints

### Docker Daemon Issues

```bash
# Check Docker daemon status
systemctl status docker
journalctl -u docker -f

# Docker daemon configuration
cat /etc/docker/daemon.json
docker system info

# Debug daemon startup
dockerd --debug --log-level=debug

# Check disk space for Docker
df -h /var/lib/docker
du -sh /var/lib/docker/*

# Restart Docker daemon safely
docker container ls -q | xargs docker container stop
systemctl restart docker
```

### System Resource Limits

```bash
# Check system limits
ulimit -a
cat /proc/sys/fs/file-max
cat /proc/sys/kernel/pid_max

# Check Docker limits
docker run --rm alpine ulimit -a
docker info | grep -i limit

# Increase limits
echo "* soft nofile 65536" >> /etc/security/limits.conf
echo "* hard nofile 65536" >> /etc/security/limits.conf

# Check cgroup limits
cat /sys/fs/cgroup/memory/memory.limit_in_bytes
cat /sys/fs/cgroup/cpu/cpu.shares
```

### Container Limits

```bash
# Set resource limits
docker run \
  --memory=1g \
  --memory-swap=2g \
  --cpus=1.5 \
  --pids-limit=100 \
  --ulimit nofile=1024:2048 \
  image_name

# Monitor limit violations
docker exec container_name cat /sys/fs/cgroup/memory/memory.failcnt
docker exec container_name cat /sys/fs/cgroup/cpu/cpu.stat

# Check for throttling
docker exec container_name cat /sys/fs/cgroup/cpu/cpu.throttled_time
```

---

## Security Issues

### Container Escape Attempts

```bash
# Check container security context
docker exec container_name cat /proc/1/status | grep -E "(Cap|Seccomp)"
docker inspect container_name | jq '.[0].HostConfig.Privileged'

# Audit privileged containers
docker ps --filter "label=privileged=true"
docker inspect $(docker ps -q) | jq '.[] | select(.HostConfig.Privileged == true) | .Name'

# Check capability drops
docker inspect container_name | jq '.[0].HostConfig.CapDrop'
docker exec container_name capsh --print

# Monitor syscalls
docker exec container_name strace -c -p 1
ausearch -m AVC -ts recent  # SELinux denials
```

### Image Vulnerabilities

```bash
# Scan images for vulnerabilities
docker scan image_name
trivy image image_name
clair-scanner image_name

# Check base image age
docker inspect image_name | jq '.[0].Created'
docker history image_name | head -5

# Update base images
docker pull image_name:latest
docker build --pull -t image_name .

# Use minimal base images
FROM alpine:latest
FROM scratch  # For static binaries
FROM distroless/java:11  # Google distroless
```

### Runtime Security

```bash
# Monitor container behavior
docker exec container_name ps aux --forest
docker exec container_name netstat -tlnp

# Check for suspicious processes
docker exec container_name find /proc -name "comm" -exec grep -l "unusual_process" {} \;

# Audit file changes
docker diff container_name
docker exec container_name find / -newer /tmp/reference_file 2>/dev/null

# Use read-only filesystems
docker run --read-only image_name
docker run --tmpfs /tmp --tmpfs /run image_name
```

---

## Multi-Container Applications

### Docker Compose Issues

```bash
# Debug compose configuration
docker-compose config
docker-compose config --resolve-envvars

# Check service dependencies
docker-compose ps
docker-compose logs service_name

# Debug service startup order
docker-compose up --no-deps service_name
docker-compose logs -f

# Check inter-service communication
docker-compose exec service1 ping service2
docker-compose exec service1 curl http://service2:port/health
```

### Service Discovery Problems

```bash
# Check service names resolution
docker-compose exec service1 nslookup service2
docker-compose exec service1 dig service2

# Debug network connectivity
docker network inspect $(docker-compose config | grep -A1 networks: | tail -1)
docker-compose exec service1 netstat -tlnp

# Check environment variables
docker-compose exec service1 env | grep -E "(HOST|PORT|URL)"

# Test service endpoints
docker-compose exec service1 curl -v http://service2:port/api/health
docker-compose exec service1 telnet service2 port
```

### Load Balancer Issues

```bash
# Debug HAProxy/nginx configuration
docker-compose exec loadbalancer cat /etc/haproxy/haproxy.cfg
docker-compose exec loadbalancer cat /etc/nginx/nginx.conf

# Check backend health
docker-compose exec loadbalancer curl http://backend1:port/health
docker-compose exec loadbalancer curl http://backend2:port/health

# Monitor load balancer logs
docker-compose logs -f loadbalancer
docker-compose exec loadbalancer tail -f /var/log/nginx/access.log

# Test load distribution
for i in {1..10}; do
  curl http://localhost/api/test
done
```

---

## Production Debugging

### Live Container Debugging

```bash
# Attach debugger to running container
docker exec -it container_name /bin/bash
docker exec -it container_name sh

# Copy files from/to container
docker cp container_name:/path/to/file ./local_file
docker cp ./local_file container_name:/path/to/file

# Stream container filesystem changes
docker events --filter container=container_name
watch docker diff container_name

# Debug without stopping container
docker exec container_name gdb -p 1
docker exec container_name strace -p 1 -f
```

### Performance Profiling

```bash
# CPU profiling
docker exec container_name perf record -g -p 1
docker exec container_name perf report

# Memory profiling
docker exec container_name valgrind --tool=massif command
docker exec container_name pmap -x 1

# I/O profiling
docker exec container_name iotop -p 1
docker exec container_name strace -e trace=file -p 1

# Network profiling
docker exec container_name tcpdump -i any -w capture.pcap
docker exec container_name ss -tulpn
```

### Production Health Checks

```bash
# Implement comprehensive health checks
#!/bin/bash
# health-check.sh
check_service() {
    local service="$1"
    local endpoint="$2"

    if curl -f -s "$endpoint" > /dev/null; then
        echo "$service: OK"
        return 0
    else
        echo "$service: FAILED"
        return 1
    fi
}

check_database() {
    if docker exec db-container pg_isready -U postgres; then
        echo "Database: OK"
        return 0
    else
        echo "Database: FAILED"
        return 1
    fi
}

# Main health check
check_service "API" "http://api:8080/health"
check_service "Frontend" "http://frontend:80/health"
check_database

# Docker health check in Dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD curl -f http://localhost:8080/health || exit 1
```

---

## Monitoring & Logging

### Centralized Logging

```bash
# Configure Docker logging drivers
docker run --log-driver=syslog image_name
docker run --log-driver=fluentd --log-opt fluentd-address=localhost:24224 image_name

# Use logging with labels
docker run --log-opt labels=service,version image_name

# Forward logs to external systems
# /etc/docker/daemon.json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
```

### Container Metrics Collection

```bash
# Export container metrics
docker run -d \
  --name cadvisor \
  -p 8080:8080 \
  -v /:/rootfs:ro \
  -v /var/run:/var/run:ro \
  -v /sys:/sys:ro \
  -v /var/lib/docker/:/var/lib/docker:ro \
  gcr.io/cadvisor/cadvisor:latest

# Use Prometheus monitoring
docker run -d \
  --name node-exporter \
  -p 9100:9100 \
  -v /proc:/host/proc:ro \
  -v /sys:/host/sys:ro \
  -v /:/rootfs:ro \
  prom/node-exporter

# Monitor with Grafana dashboards
docker run -d \
  --name grafana \
  -p 3000:3000 \
  -e GF_SECURITY_ADMIN_PASSWORD=admin \
  grafana/grafana
```

### Alert Configuration

```bash
# Alertmanager configuration
# alertmanager.yml
global:
  smtp_smarthost: 'localhost:587'
  smtp_from: 'alerts@company.com'

route:
  group_by: ['alertname']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'team-alerts'

receivers:
- name: 'team-alerts'
  email_configs:
  - to: 'devops@company.com'
    subject: 'Docker Alert: {{ .GroupLabels.alertname }}'
    body: |
      {{ range .Alerts }}
      Alert: {{ .Annotations.summary }}
      Container: {{ .Labels.container }}
      {{ end }}
```

---

## Common Error Patterns

### Image Not Found

```bash
# Error: Unable to find image 'image:tag' locally
docker images | grep image
docker search image
docker pull image:tag

# Check registry connectivity
docker pull registry.example.com/image:tag
curl -v https://registry.example.com/v2/

# Use correct image name
docker tag local_image registry.example.com/image:tag
docker push registry.example.com/image:tag
```

### Port Already in Use

```bash
# Error: bind: address already in use
netstat -tlnp | grep :port
ss -tlnp | grep :port
lsof -i :port

# Find conflicting container
docker ps --filter "publish=port"
docker stop conflicting_container

# Use different port
docker run -p 8081:8080 image_name
```

### Volume Mount Errors

```bash
# Error: invalid mount config
# Check path exists
ls -la /host/path
mkdir -p /host/path

# Check permissions
chmod 755 /host/path
chown user:user /host/path

# Use absolute paths
docker run -v /absolute/host/path:/container/path image_name

# SELinux context (RHEL/CentOS)
docker run -v /host/path:/container/path:Z image_name
```

### Memory/Disk Issues

```bash
# Error: no space left on device
df -h /var/lib/docker
docker system df
docker system prune -a

# Error: cannot allocate memory
free -h
docker stats
echo 1 > /proc/sys/vm/drop_caches

# Error: too many open files
ulimit -n
echo "fs.file-max = 65536" >> /etc/sysctl.conf
sysctl -p
```

---

## Cross-References

**Related Documentation:**
- [Docker Commands](Docker%20Commands.md) - Basic Docker CLI reference and debugging commands
- [Docker fundamental](Docker%20fundamental.md) - Architecture understanding for troubleshooting
- [Dockerfile](Dockerfile.md) - Build optimization and error resolution
- [Docker Registry & Distribution](Docker%20Registry%20&%20Distribution.md) - Registry connectivity issues

**Integration Points:**
- **Monitoring**: Integration with Prometheus, Grafana, and APM tools
- **Logging**: Centralized logging with ELK stack, Fluentd, and log aggregation
- **Security**: Container scanning, runtime protection, and compliance monitoring
- **Orchestration**: Kubernetes troubleshooting, service mesh debugging, and cluster issues