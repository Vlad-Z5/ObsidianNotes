# Linux Systemd Resource Management

**Systemd resource management** uses Linux cgroups to control CPU, memory, I/O, and other resources for services, providing fine-grained control over system resource allocation.

## Cgroup Integration

```bash
# View service cgroup
systemctl status service_name       # Shows cgroup path
systemd-cgls                        # Show cgroup tree
systemd-cgtop                       # Real-time cgroup statistics

# Cgroup hierarchy location
/sys/fs/cgroup/system.slice/service_name.service/
```

## CPU Resource Control

### CPU Limits
```bash
# CPU configuration options
CPUAccounting=true              # Enable CPU accounting
CPUQuota=200%                   # 2 CPU cores maximum
CPUShares=1024                  # Relative CPU weight (default)
CPUWeight=100                   # Modern CPU weight (1-10000)
CPUAffinity=0 1 2 3            # Bind to specific CPU cores
```

### CPU Configuration Example
```bash
# /etc/systemd/system/cpu-limited.service
[Unit]
Description=CPU Limited Service

[Service]
Type=simple
ExecStart=/usr/local/bin/myapp
CPUAccounting=true
CPUQuota=150%                   # 1.5 CPU cores max
CPUShares=2048                  # Higher priority
CPUAffinity=0 1                 # Use only cores 0 and 1

[Install]
WantedBy=multi-user.target
```

## Memory Resource Control

### Memory Limits
```bash
# Memory configuration options
MemoryAccounting=true           # Enable memory accounting
MemoryMax=1G                    # Hard memory limit
MemoryHigh=800M                 # Soft limit (throttling begins)
MemorySwapMax=512M              # Maximum swap usage
MemoryLow=200M                  # Memory protection threshold
```

### Memory Configuration Example
```bash
# /etc/systemd/system/memory-limited.service
[Unit]
Description=Memory Limited Service

[Service]
Type=simple
ExecStart=/usr/local/bin/memory-intensive-app
MemoryAccounting=true
MemoryMax=2G                    # Hard limit
MemoryHigh=1.5G                 # Start throttling
MemorySwapMax=500M              # Swap limit
MemoryLow=512M                  # Protected memory

[Install]
WantedBy=multi-user.target
```

## I/O Resource Control

### I/O Limits
```bash
# I/O configuration options
IOAccounting=true               # Enable I/O accounting
IOWeight=100                    # I/O priority weight (1-10000)
IODeviceWeight=/dev/sda 200     # Device-specific weight
IOReadBandwidthMax=/dev/sda 50M # Read bandwidth limit
IOWriteBandwidthMax=/dev/sda 25M # Write bandwidth limit
IOReadIOPSMax=/dev/sda 1000     # Read IOPS limit
IOWriteIOPSMax=/dev/sda 500     # Write IOPS limit
```

### I/O Configuration Example
```bash
# /etc/systemd/system/io-limited.service
[Unit]
Description=I/O Limited Service

[Service]
Type=simple
ExecStart=/usr/local/bin/data-processor
IOAccounting=true
IOWeight=200                    # Higher I/O priority
IOReadBandwidthMax=/dev/sda 100M
IOWriteBandwidthMax=/dev/sda 50M
IOReadIOPSMax=/dev/sda 2000
IOWriteIOPSMax=/dev/sda 1000

[Install]
WantedBy=multi-user.target
```

## Process and Task Limits

### Task Configuration
```bash
# Task and process limits
TasksAccounting=true            # Enable task accounting
TasksMax=1000                   # Maximum number of tasks/threads
LimitNOFILE=65536              # File descriptor limit
LimitNPROC=4096                # Process limit
LimitCORE=infinity             # Core dump size limit
LimitMEMLOCK=64M               # Memory lock limit
```

### Task Limit Example
```bash
# /etc/systemd/system/task-limited.service
[Unit]
Description=Task Limited Service

[Service]
Type=simple
ExecStart=/usr/local/bin/multi-threaded-app
TasksAccounting=true
TasksMax=500                    # Limit to 500 threads
LimitNOFILE=32768              # 32k file descriptors
LimitNPROC=2048                # 2k processes
LimitCORE=0                    # No core dumps

[Install]
WantedBy=multi-user.target
```

## Device Access Control

### Device Configuration
```bash
# Device access control
DevicePolicy=strict             # Deny all device access by default
DevicePolicy=auto              # Allow access to standard devices
DeviceAllow=/dev/null rw       # Allow specific device access
DeviceAllow=/dev/zero rw
DeviceAllow=/dev/random r
DeviceAllow=char-pts rw        # Allow character device class
```

### Device Control Example
```bash
# /etc/systemd/system/device-restricted.service
[Unit]
Description=Device Restricted Service

[Service]
Type=simple
ExecStart=/usr/local/bin/secure-app
DevicePolicy=strict
DeviceAllow=/dev/null rw
DeviceAllow=/dev/zero rw
DeviceAllow=/dev/urandom r
PrivateDevices=true

[Install]
WantedBy=multi-user.target
```

## Slice Management

### Custom Slice Creation
```bash
# /etc/systemd/system/myapp.slice
[Unit]
Description=My Application Slice
Documentation=https://company.com/docs/resources
Before=slices.target

[Slice]
# Resource limits for entire slice
MemoryMax=4G
CPUQuota=400%
TasksMax=2000
IOWeight=500

[Install]
WantedBy=slices.target
```

### Assign Services to Slice
```bash
# Service configuration using custom slice
[Service]
Type=simple
ExecStart=/usr/local/bin/myapp
Slice=myapp.slice               # Assign to custom slice
```

## Resource Monitoring

### Real-Time Monitoring
```bash
# Monitor resource usage
systemd-cgtop                   # Real-time cgroup statistics
systemd-cgtop --depth=3         # Limit depth
systemd-cgtop --order=memory    # Sort by memory

# Service-specific monitoring
systemctl status service_name   # Basic resource info
systemctl show service_name --property=CPUUsageNSec
systemctl show service_name --property=MemoryCurrent
systemctl show service_name --property=TasksCurrent
```

### Resource Usage Commands
```bash
# CPU usage
systemctl show service_name --property=CPUUsageNSec

# Memory usage
systemctl show service_name --property=MemoryCurrent
systemctl show service_name --property=MemoryPeak

# I/O statistics
systemctl show service_name --property=IOReadBytes
systemctl show service_name --property=IOWriteBytes

# Task count
systemctl show service_name --property=TasksCurrent
```

## Production Resource Configuration

### High-Performance Service
```bash
# /etc/systemd/system/high-performance.service
[Unit]
Description=High Performance Application
Documentation=https://company.com/docs/performance

[Service]
Type=simple
ExecStart=/usr/local/bin/high-perf-app
Restart=always
RestartSec=5

# Resource allocation
CPUAccounting=true
CPUQuota=800%                   # 8 CPU cores
CPUAffinity=0-7                 # Dedicated cores
MemoryAccounting=true
MemoryMax=16G
MemoryHigh=14G
IOAccounting=true
IOWeight=1000                   # Highest I/O priority
TasksMax=10000

# Security with performance
NoNewPrivileges=true
PrivateTmp=true
LimitNOFILE=1048576            # High file descriptor limit

[Install]
WantedBy=multi-user.target
```

### Resource-Constrained Service
```bash
# /etc/systemd/system/constrained.service
[Unit]
Description=Resource Constrained Service
Documentation=https://company.com/docs/constrained

[Service]
Type=simple
ExecStart=/usr/local/bin/light-app
Restart=always

# Minimal resource allocation
CPUAccounting=true
CPUQuota=50%                    # Half CPU core
MemoryAccounting=true
MemoryMax=128M                  # 128MB memory limit
MemoryHigh=96M                  # Throttle at 96MB
IOAccounting=true
IOWeight=10                     # Low I/O priority
TasksMax=50                     # Limit processes/threads

# Additional constraints
LimitNOFILE=1024
LimitNPROC=50

[Install]
WantedBy=multi-user.target
```

## Dynamic Resource Management

### Runtime Resource Adjustment
```bash
# Modify resources at runtime
systemctl set-property service_name CPUQuota=150%
systemctl set-property service_name MemoryMax=2G
systemctl set-property service_name TasksMax=500

# View current resource settings
systemctl show service_name --property=CPUQuota
systemctl show service_name --property=MemoryMax

# Reset to unit file defaults
systemctl revert service_name
```

### Temporary Resource Override
```bash
# Create temporary override
systemctl edit service_name

# Add temporary resource limits
[Service]
MemoryMax=1G
CPUQuota=100%

# Apply changes
systemctl daemon-reload
systemctl restart service_name
```

## Resource Monitoring Script

```bash
#!/bin/bash
# resource-monitor.sh

SERVICE="$1"

if [ -z "$SERVICE" ]; then
    echo "Usage: $0 <service_name>"
    exit 1
fi

echo "=== Resource Usage for $SERVICE ==="

# CPU Usage
CPU_USAGE=$(systemctl show "$SERVICE" --property=CPUUsageNSec --value)
echo "CPU Usage: $((CPU_USAGE / 1000000000)) seconds"

# Memory Usage
MEMORY_CURRENT=$(systemctl show "$SERVICE" --property=MemoryCurrent --value)
MEMORY_PEAK=$(systemctl show "$SERVICE" --property=MemoryPeak --value)
echo "Memory Current: $((MEMORY_CURRENT / 1024 / 1024)) MB"
echo "Memory Peak: $((MEMORY_PEAK / 1024 / 1024)) MB"

# Task Count
TASKS_CURRENT=$(systemctl show "$SERVICE" --property=TasksCurrent --value)
echo "Tasks Current: $TASKS_CURRENT"

# I/O Statistics
IO_READ=$(systemctl show "$SERVICE" --property=IOReadBytes --value)
IO_WRITE=$(systemctl show "$SERVICE" --property=IOWriteBytes --value)
echo "I/O Read: $((IO_READ / 1024 / 1024)) MB"
echo "I/O Write: $((IO_WRITE / 1024 / 1024)) MB"

# Resource Limits
echo -e "\n=== Resource Limits ==="
systemctl show "$SERVICE" --property=CPUQuota,MemoryMax,TasksMax --no-pager
```

## Resource Alert Script

```bash
#!/bin/bash
# resource-alert.sh

THRESHOLD_MEMORY=80     # Memory threshold percentage
THRESHOLD_CPU=200       # CPU quota percentage
ALERT_EMAIL="admin@company.com"

systemctl list-units --type=service --state=active --no-legend | while read -r unit _; do
    # Check memory usage
    MEMORY_MAX=$(systemctl show "$unit" --property=MemoryMax --value)
    MEMORY_CURRENT=$(systemctl show "$unit" --property=MemoryCurrent --value)

    if [ "$MEMORY_MAX" != "[not set]" ] && [ "$MEMORY_CURRENT" -gt 0 ]; then
        MEMORY_PERCENT=$((MEMORY_CURRENT * 100 / MEMORY_MAX))
        if [ "$MEMORY_PERCENT" -gt "$THRESHOLD_MEMORY" ]; then
            echo "ALERT: $unit memory usage: ${MEMORY_PERCENT}%" | \
            mail -s "Memory Alert: $unit" "$ALERT_EMAIL"
        fi
    fi

    # Check CPU usage patterns
    CPU_QUOTA=$(systemctl show "$unit" --property=CPUQuota --value)
    if [ "$CPU_QUOTA" != "[not set]" ]; then
        # Additional CPU monitoring logic here
        echo "Monitoring CPU for $unit"
    fi
done
```