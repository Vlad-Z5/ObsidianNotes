### Resource Management Deep Dive

```bash
# CPU management
docker run -d \
  --cpus="1.5" \ # CPU limit (1.5 cores)
  --cpu-shares=512 \ # Relative weight (default 1024)
  --cpu-period=100000 \ # CPU period (microseconds)
  --cpu-quota=50000 \ # CPU quota (50% of period)
  --cpuset-cpus="0,1" \ # Pin to specific CPUs
  --cpu-rt-runtime=950000 \ # Real-time scheduling
  nginx

# Memory management with detailed options
docker run -d \
  --memory=512m \ # Memory limit
  --memory-swap=1g \ # Total memory (RAM + swap)
  --memory-swappiness=60 \ # Swap tendency (0-100)
  --memory-reservation=256m \ # Soft limit
  --oom-kill-disable \ # Disable OOM killer
  --oom-score-adj=-500 \ # OOM score adjustment
  nginx

# I/O management
docker run -d \
  --device-read-bps /dev/sda:1mb \ # Read bandwidth limit
  --device-write-bps /dev/sda:1mb \ # Write bandwidth limit
  --device-read-iops /dev/sda:100 \ # Read IOPS limit
  --device-write-iops /dev/sda:100 \ # Write IOPS limit
  --blkio-weight=500 \ # Block I/O weight
  nginx
```

### Monitoring and Observability

```bash
# Real-time monitoring
docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}"
watch -n 1 'docker stats --no-stream'

# cAdvisor (container metrics)
docker run -d \
  --name=cadvisor \
  -p 8080:8080 \
  --volume=/:/rootfs:ro \
  --volume=/var/run:/var/run:ro \
  --volume=/sys:/sys:ro \
  --volume=/var/lib/docker/:/var/lib/docker:ro \
  --volume=/dev/disk/:/dev/disk:ro \
  gcr.io/cadvisor/cadvisor:latest

# Prometheus metrics collection
docker run -d \
  --name prometheus \
  -p 9090:9090 \
  -v prometheus-config:/etc/prometheus \
  prom/prometheus

# Logging drivers configuration
docker run -d \
  --log-driver=fluentd \
  --log-opt fluentd-address=localhost:24224 \
  --log-opt tag="docker.{{.Name}}" \
  nginx

# Custom log format
docker run -d \
  --log-driver=json-file \
  --log-opt max-size=10m \
  --log-opt max-file=5 \
  --log-opt labels=service,version \
  --label service=web \
  --label version=1.0 \
  nginx
```

### Performance Tuning

```bash
# Container performance tuning
docker run -d \
  --shm-size=256m \ # Shared memory size
  --ulimit memlock=-1:-1 \ # Memory lock limit
  --ulimit stack=67108864 \ # Stack size
  --sysctl net.core.somaxconn=65535 \ # Network tuning
  --sysctl vm.max_map_count=262144 \ # Virtual memory tuning
  nginx

# Docker daemon tuning (/etc/docker/daemon.json)
{
  "storage-driver": "overlay2",
  "storage-opts": [
    "overlay2.override_kernel_check=true"
  ],
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  },
  "exec-opts": ["native.cgroupdriver=systemd"],
  "default-ulimits": {
    "nofile": {
      "Name": "nofile",
      "Hard": 64000,
      "Soft": 64000
    }
},
"dns": ["8.8.8.8", "8.8.4.4"],
"live-restore": true,
"max-concurrent-downloads": 3,
"max-concurrent-uploads": 5
}
```

### Container Monitoring and Debugging

#### Logging and Log Management

```bash
# Docker logs commands
docker logs container_name              # View logs
docker logs -f container_name           # Follow logs
docker logs --tail 100 container_name   # Last 100 lines
docker logs --since "2024-01-01T00:00:00" container_name
docker logs --until "1h" container_name # Logs until 1 hour ago

# Logging drivers configuration
docker run --log-driver json-file \
  --log-opt max-size=10m \
  --log-opt max-file=3 \
  myapp:latest

# Centralized logging with fluentd
docker run --log-driver fluentd \
  --log-opt fluentd-address=localhost:24224 \
  --log-opt tag="myapp.{{.Name}}" \
  myapp:latest

# Syslog logging
docker run --log-driver syslog \
  --log-opt syslog-address=tcp://192.168.1.10:514 \
  myapp:latest
```

#### Container Inspection and Debugging

```bash
# Container inspection
docker inspect container_name           # Full container details
docker inspect --format='{{.State.Status}}' container_name
docker inspect --format='{{.NetworkSettings.IPAddress}}' container_name
docker inspect --format='{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' container_name

# Runtime statistics
docker stats                           # All containers
docker stats container_name           # Specific container
docker stats --no-stream             # One-time stats

# Container events
docker events                         # All events
docker events --filter container=myapp
docker events --filter event=start
docker events --since="2024-01-01T00:00:00"

# Process information
docker top container_name             # Running processes
docker exec container_name ps aux     # Detailed process list

# File system changes
docker diff container_name            # Changed files since start
docker cp container_name:/app/config.yml ./config.yml
docker cp ./newfile.txt container_name:/app/
```

#### Health Monitoring

```bash
# Health check status
docker inspect --format='{{.State.Health.Status}}' container_name
docker inspect --format='{{range .State.Health.Log}}{{.Output}}{{end}}' container_name

# Container lifecycle events
docker events --filter container=myapp --filter event=health_status

# Custom health monitoring script
#!/bin/bash
while true; do
    health=$(docker inspect --format='{{.State.Health.Status}}' myapp)
    if [ "$health" != "healthy" ]; then
        echo "Container unhealthy: $health"
        # Send alert or restart container
        docker restart myapp
    fi
    sleep 30
done
```