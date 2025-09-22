# Linux Process Management System Tuning

**System Tuning and Optimization** covers kernel parameter tuning, container technologies, namespaces, and control groups for optimal system performance and resource management.

## Kernel Parameter Tuning (sysctl)

### Understanding and Viewing Parameters
```bash
# View kernel parameters
sysctl -a                              # List all parameters
sysctl -a | grep vm                    # Virtual memory parameters
sysctl -a | grep net                   # Network parameters
sysctl -a | grep fs                    # Filesystem parameters
sysctl -a | grep kernel                # Kernel parameters

# View specific parameters
sysctl vm.swappiness                   # Swap tendency parameter
sysctl net.core.somaxconn              # Socket backlog limit
sysctl fs.file-max                     # System-wide file descriptor limit
sysctl kernel.pid_max                  # Maximum PID value

# Search for parameters
sysctl -a | grep -i tcp                # All TCP-related parameters
sysctl -a | grep dirty                 # Memory dirty page parameters
```

### Temporary Parameter Changes
```bash
# Temporary changes (lost on reboot)
sysctl vm.swappiness=10                # Reduce swap tendency
sysctl net.core.somaxconn=1024         # Increase socket backlog
sysctl fs.file-max=100000              # Increase file descriptor limit
sysctl vm.dirty_ratio=15               # Set dirty page ratio
sysctl net.ipv4.tcp_congestion_control=bbr  # Set TCP congestion control

# Verify changes
sysctl vm.swappiness
sysctl net.core.somaxconn

# Multiple parameter changes
sysctl -w vm.swappiness=5 vm.dirty_ratio=10 fs.file-max=200000
```

### Permanent Configuration
```bash
# Create performance optimization configuration
cat << 'EOF' > /etc/sysctl.d/99-performance.conf
# Memory management optimization
vm.swappiness = 10                     # Reduce swapping (default: 60)
vm.dirty_ratio = 15                    # Dirty page ratio (default: 20)
vm.dirty_background_ratio = 5          # Background dirty ratio (default: 10)
vm.vfs_cache_pressure = 50             # VFS cache pressure (default: 100)
vm.max_map_count = 262144               # Memory map areas limit

# Network performance
net.core.somaxconn = 1024              # Socket backlog (default: 128)
net.core.netdev_max_backlog = 5000     # Network device backlog
net.core.rmem_default = 262144         # Default receive buffer size
net.core.rmem_max = 16777216           # Maximum receive buffer size
net.core.wmem_default = 262144         # Default send buffer size
net.core.wmem_max = 16777216           # Maximum send buffer size
net.ipv4.tcp_congestion_control = bbr  # BBR congestion control
net.ipv4.tcp_slow_start_after_idle = 0 # Disable slow start after idle
net.ipv4.tcp_fin_timeout = 30          # Reduce FIN timeout
net.ipv4.tcp_keepalive_time = 1200     # TCP keepalive time
net.ipv4.tcp_max_syn_backlog = 8192    # SYN backlog queue size

# File system limits
fs.file-max = 100000                   # Maximum file descriptors
fs.inotify.max_user_watches = 524288   # Inotify watch limit
fs.inotify.max_user_instances = 256    # Inotify instance limit

# Process limits
kernel.pid_max = 4194304               # Maximum PID value
kernel.threads-max = 1048576           # Maximum number of threads

# Security parameters
kernel.dmesg_restrict = 1              # Restrict dmesg access
kernel.kptr_restrict = 2               # Restrict kernel pointer access
EOF

# Apply configuration
sysctl -p /etc/sysctl.d/99-performance.conf
sysctl --system                        # Reload all sysctl configurations

# Verify configuration
sysctl -a | grep -E 'vm.swappiness|net.core.somaxconn|fs.file-max'
```

### Workload-Specific Tuning
```bash
# Database server tuning
cat << 'EOF' > /etc/sysctl.d/98-database.conf
# Database-specific optimizations
vm.swappiness = 1                      # Minimal swapping for databases
vm.dirty_ratio = 5                     # Lower dirty ratio for faster writes
vm.dirty_background_ratio = 2          # Background write threshold
kernel.shmmax = 17179869184            # Shared memory segment size (16GB)
kernel.shmall = 4194304                # Total shared memory pages
kernel.sem = 250 32000 100 128         # Semaphore limits
EOF

# Web server tuning
cat << 'EOF' > /etc/sysctl.d/97-webserver.conf
# Web server optimizations
net.core.somaxconn = 8192              # High connection backlog
net.ipv4.tcp_max_syn_backlog = 8192    # SYN flood protection
net.ipv4.tcp_syncookies = 1            # Enable SYN cookies
net.ipv4.tcp_tw_reuse = 1              # Reuse TIME_WAIT sockets
net.ipv4.tcp_fin_timeout = 15          # Faster connection cleanup
net.ipv4.ip_local_port_range = 1024 65535  # Port range for outgoing connections
EOF

# High-performance computing tuning
cat << 'EOF' > /etc/sysctl.d/96-hpc.conf
# HPC optimizations
vm.zone_reclaim_mode = 0               # Disable NUMA zone reclaim
vm.stat_interval = 120                 # Reduce stat updates
kernel.numa_balancing = 0              # Disable automatic NUMA balancing
net.core.busy_read = 50                # Busy polling for low latency
net.core.busy_poll = 50                # Busy polling threshold
EOF
```

## Container Technologies and Namespaces

### Linux Namespaces
```bash
# View process namespaces
ls -la /proc/$$/ns/                    # Current process namespaces
ls -la /proc/1/ns/                     # Init process namespaces
lsns                                   # List all namespaces
lsns -t net                            # Network namespaces only
lsns -t pid                            # PID namespaces only
lsns -t mnt                            # Mount namespaces only
lsns -t uts                            # UTS (hostname) namespaces
lsns -t ipc                            # IPC namespaces
lsns -t user                           # User namespaces

# Compare namespaces between processes
diff <(ls -la /proc/1/ns/) <(ls -la /proc/$$/ns/)

# Namespace types and their purposes:
# PID: Process isolation
# NET: Network isolation
# MNT: Mount point isolation
# UTS: Hostname and domain isolation
# IPC: Inter-process communication isolation
# USER: User and group ID isolation
# CGROUP: Control group isolation
```

### Network Namespace Management
```bash
# Create and manage network namespaces
ip netns add testns                    # Create network namespace
ip netns list                          # List network namespaces
ip netns exec testns ip link list      # Execute command in namespace
ip netns exec testns bash             # Start shell in namespace

# Configure network namespace
ip netns exec testns ip link set lo up  # Enable loopback in namespace
ip link add veth0 type veth peer name veth1  # Create veth pair
ip link set veth1 netns testns         # Move one end to namespace
ip addr add 192.168.1.1/24 dev veth0   # Configure host end
ip link set veth0 up
ip netns exec testns ip addr add 192.168.1.2/24 dev veth1  # Configure namespace end
ip netns exec testns ip link set veth1 up

# Test namespace connectivity
ping -c 3 192.168.1.2                  # From host
ip netns exec testns ping -c 3 192.168.1.1  # From namespace

# Cleanup
ip netns delete testns                 # Delete namespace
ip link delete veth0                   # Delete veth pair
```

### Process Namespace Operations
```bash
# Create PID namespace
unshare --pid --fork --mount-proc bash  # New PID namespace with new /proc
ps aux                                  # Shows only processes in namespace

# Create multiple namespaces
unshare --pid --net --mount --fork bash  # PID, network, and mount namespaces
unshare --user --map-root-user bash     # User namespace with root mapping

# Enter existing namespaces
nsenter -t PID -n -p                   # Enter network and PID namespaces of process
nsenter -t PID -a                      # Enter all namespaces of process

# Container namespace inspection
docker run -d --name test nginx       # Start test container
docker inspect test | grep -A 20 "NetworkMode"
docker exec test ls -la /proc/1/ns/   # View container namespaces

# Enter container namespaces
container_pid=$(docker inspect -f '{{.State.Pid}}' test)
nsenter -t $container_pid -n -p        # Enter container network and PID namespaces
```

## Control Groups (cgroups)

### Understanding cgroup Hierarchy
```bash
# View cgroup filesystems
mount | grep cgroup                    # Show mounted cgroup filesystems
ls /sys/fs/cgroup/                     # Cgroup v1 controllers or v2 unified hierarchy

# Cgroup v1 structure
ls /sys/fs/cgroup/memory/              # Memory controller
ls /sys/fs/cgroup/cpu/                 # CPU controller
ls /sys/fs/cgroup/blkio/               # Block I/O controller
ls /sys/fs/cgroup/systemd/             # Systemd controller

# Cgroup v2 unified hierarchy
ls /sys/fs/cgroup/                     # Unified hierarchy (if cgroup v2)
cat /sys/fs/cgroup/cgroup.controllers  # Available controllers in v2
```

### Manual cgroup Management (v1)
```bash
# Create memory cgroup
mkdir /sys/fs/cgroup/memory/myapp      # Create memory cgroup
echo 512M > /sys/fs/cgroup/memory/myapp/memory.limit_in_bytes  # Set memory limit
echo $$ > /sys/fs/cgroup/memory/myapp/cgroup.procs  # Add current process

# Monitor memory cgroup
cat /sys/fs/cgroup/memory/myapp/memory.usage_in_bytes  # Current usage
cat /sys/fs/cgroup/memory/myapp/memory.stat            # Detailed statistics
cat /sys/fs/cgroup/memory/myapp/memory.failcnt         # OOM kill count

# Create CPU cgroup
mkdir /sys/fs/cgroup/cpu/myapp         # Create CPU cgroup
echo 50000 > /sys/fs/cgroup/cpu/myapp/cpu.cfs_quota_us   # 50% CPU (50000/100000)
echo 100000 > /sys/fs/cgroup/cpu/myapp/cpu.cfs_period_us  # 100ms period
echo $$ > /sys/fs/cgroup/cpu/myapp/cgroup.procs

# Monitor CPU cgroup
cat /sys/fs/cgroup/cpu/myapp/cpuacct.usage    # CPU usage in nanoseconds
cat /sys/fs/cgroup/cpu/myapp/cpu.stat         # CPU statistics

# Create combined resource limits
cat << 'EOF' > setup_cgroup.sh
#!/bin/bash
# Create and configure cgroup for application

APP_NAME="$1"
MEMORY_LIMIT="$2"
CPU_QUOTA="$3"

if [[ -z "$APP_NAME" || -z "$MEMORY_LIMIT" || -z "$CPU_QUOTA" ]]; then
    echo "Usage: $0 <app_name> <memory_limit> <cpu_quota_percent>"
    echo "Example: $0 myapp 1G 50"
    exit 1
fi

# Create cgroups
mkdir -p "/sys/fs/cgroup/memory/$APP_NAME"
mkdir -p "/sys/fs/cgroup/cpu/$APP_NAME"

# Set memory limit
echo "$MEMORY_LIMIT" > "/sys/fs/cgroup/memory/$APP_NAME/memory.limit_in_bytes"

# Set CPU quota (percentage * 1000)
cpu_quota=$((CPU_QUOTA * 1000))
echo "$cpu_quota" > "/sys/fs/cgroup/cpu/$APP_NAME/cpu.cfs_quota_us"
echo "100000" > "/sys/fs/cgroup/cpu/$APP_NAME/cpu.cfs_period_us"

echo "Cgroup $APP_NAME created with $MEMORY_LIMIT memory and $CPU_QUOTA% CPU"
EOF

chmod +x setup_cgroup.sh
./setup_cgroup.sh webapp 2G 75
```

### Systemd and cgroups Integration
```bash
# View systemd cgroup hierarchy
systemctl show myapp.service --property=ControlGroup
systemd-cgls                           # Show cgroup hierarchy tree
systemd-cgtop                          # Real-time cgroup resource usage

# Set resource limits via systemd
systemctl set-property myapp.service MemoryLimit=1G
systemctl set-property myapp.service CPUQuota=50%
systemctl set-property myapp.service BlockIOWeight=500

# View current resource settings
systemctl show myapp.service | grep -E "(Memory|CPU|BlockIO)"

# Create service with resource limits
cat << 'EOF' > /etc/systemd/system/resource-limited.service
[Unit]
Description=Resource Limited Service
After=network.target

[Service]
Type=simple
ExecStart=/opt/myapp/bin/myapp
User=myapp
Group=myapp

# Resource limits
MemoryLimit=1G                         # Memory limit
MemorySwapMax=0                        # Disable swap for this service
CPUQuota=50%                           # CPU limit
BlockIOWeight=500                      # Block I/O weight
TasksMax=1000                          # Process/thread limit

# Additional controls
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable resource-limited.service
```

### cgroup Monitoring and Analysis
```bash
# Monitor cgroup resource usage
cat << 'EOF' > cgroup_monitor.sh
#!/bin/bash
# Monitor cgroup resource usage

monitor_cgroup() {
    local cgroup_path="$1"

    if [[ ! -d "$cgroup_path" ]]; then
        echo "Cgroup path does not exist: $cgroup_path"
        return 1
    fi

    echo "Monitoring cgroup: $cgroup_path"
    echo "================================"

    while true; do
        clear
        echo "$(date) - Cgroup Resource Usage"
        echo "================================"

        # Memory usage
        if [[ -f "$cgroup_path/memory.usage_in_bytes" ]]; then
            usage=$(cat "$cgroup_path/memory.usage_in_bytes")
            limit=$(cat "$cgroup_path/memory.limit_in_bytes")
            echo "Memory: $(numfmt --to=iec $usage) / $(numfmt --to=iec $limit)"
        fi

        # CPU usage
        if [[ -f "$cgroup_path/cpuacct.usage" ]]; then
            cpu_usage=$(cat "$cgroup_path/cpuacct.usage")
            echo "CPU usage: $cpu_usage nanoseconds"
        fi

        # Process count
        if [[ -f "$cgroup_path/cgroup.procs" ]]; then
            proc_count=$(wc -l < "$cgroup_path/cgroup.procs")
            echo "Processes: $proc_count"
        fi

        echo
        echo "Press Ctrl+C to stop monitoring"
        sleep 5
    done
}

# Usage
if [[ $# -eq 0 ]]; then
    echo "Usage: $0 <cgroup_path>"
    echo "Example: $0 /sys/fs/cgroup/memory/myapp"
else
    monitor_cgroup "$1"
fi
EOF

chmod +x cgroup_monitor.sh

# System-wide cgroup analysis
cat << 'EOF' > cgroup_analysis.sh
#!/bin/bash
# Analyze system-wide cgroup usage

echo "=== System cgroup Analysis ==="
echo "Date: $(date)"
echo

# Memory usage by cgroup
echo "Top Memory-consuming cgroups:"
find /sys/fs/cgroup/memory -name "memory.usage_in_bytes" -exec sh -c '
    usage=$(cat "{}")
    cgroup=$(dirname "{}" | sed "s|/sys/fs/cgroup/memory||")
    if [[ $usage -gt 0 ]]; then
        echo "$cgroup: $(numfmt --to=iec $usage)"
    fi
' \; | sort -hr | head -10

echo
echo "Systemd service resource usage:"
systemd-cgtop --iterations=1 | head -15
EOF

chmod +x cgroup_analysis.sh
```