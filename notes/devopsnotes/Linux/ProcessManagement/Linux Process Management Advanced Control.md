# Linux Process Management Advanced Control

**Advanced Process Management** covers process priority control, resource limits, and sophisticated process management techniques for production environments.

## Process Priority Control

### nice and renice Commands
```bash
# Process priority levels (-20 to 19, lower = higher priority)
nice -n 10 ./cpu_intensive_task        # Start with lower priority
nice -n -5 ./critical_task             # Start with higher priority (requires root)
nice -20 ./background_task             # Lowest priority
nice --20 ./highest_priority           # Highest priority (requires root)

# Understanding nice values
# -20: Highest priority (most favorable scheduling)
#   0: Default priority
#  19: Lowest priority (least favorable scheduling)

# Changing priority of running processes
renice -n 5 -p 1234                    # Change priority by PID
renice -n 10 -u apache                 # Change priority for user's processes
renice -n -5 -g developers             # Change priority for group
renice +5 1234                         # Alternative syntax (increase nice value)
renice 15 $(pgrep -f "backup_script")  # Set priority for all backup processes

# Monitoring priority levels
ps -eo pid,nice,pri,comm               # Show process priorities
ps -eo pid,ni,pri,pcpu,comm --sort=-pcpu  # Sort by CPU usage with priority info
top -o %CPU                            # Sort top by CPU usage
htop                                   # Interactive process viewer with priority display
```

### Advanced Priority Management
```bash
# Batch process priority management
cat << 'EOF' > priority_manager.sh
#!/bin/bash
# Priority management for different process types

set_batch_priority() {
    local pattern="$1"
    local nice_value="$2"

    pgrep -f "$pattern" | while read -r pid; do
        if [[ -n "$pid" ]]; then
            renice -n "$nice_value" -p "$pid"
            echo "Set priority $nice_value for PID $pid"
        fi
    done
}

# Set priorities for different workload types
set_batch_priority "backup" 15          # Low priority for backups
set_batch_priority "analytics" 10       # Medium-low priority for analytics
set_batch_priority "webserver" -5       # Higher priority for web servers
set_batch_priority "database" -10       # High priority for databases

# Monitor priority distribution
echo "Current priority distribution:"
ps -eo nice | sort -n | uniq -c | sort -nr
EOF

chmod +x priority_manager.sh

# Real-time priority monitoring
watch 'ps -eo pid,ni,pri,pcpu,comm --sort=-pcpu | head -20'
```

## Process Resource Limits (ulimit)

### Understanding and Setting Limits
```bash
# View current limits
ulimit -a                              # Show all current limits
ulimit -n                              # File descriptor limit
ulimit -u                              # Process/thread limit
ulimit -m                              # Memory limit (KB)
ulimit -f                              # File size limit (blocks)
ulimit -c                              # Core dump size limit
ulimit -t                              # CPU time limit (seconds)
ulimit -v                              # Virtual memory limit (KB)

# Set limits for current session
ulimit -n 4096                         # Increase file descriptor limit
ulimit -c unlimited                    # Enable unlimited core dumps
ulimit -u 1000                         # Limit number of processes
ulimit -f 1000000                      # Limit file size to ~1GB
ulimit -t 3600                         # Limit CPU time to 1 hour

# Soft vs hard limits
ulimit -Sn 2048                        # Set soft file descriptor limit
ulimit -Hn 4096                        # Set hard file descriptor limit
ulimit -Su 500                         # Set soft process limit
ulimit -Hu 1000                        # Set hard process limit
```

### Persistent Limits Configuration
```bash
# System-wide limits configuration (/etc/security/limits.conf)
cat << 'EOF' > /etc/security/limits.d/custom.conf
# Domain    Type  Item         Value
*          soft  nofile       4096      # Soft file descriptor limit
*          hard  nofile       8192      # Hard file descriptor limit
*          soft  nproc        2048      # Soft process limit
*          hard  nproc        4096      # Hard process limit
*          soft  core         0         # Disable core dumps by default
*          hard  core         unlimited # Allow unlimited core dumps if needed

# User-specific limits
deploy     soft  nofile       8192      # Deploy user file descriptors
deploy     hard  nofile       16384
deploy     soft  memlock      unlimited # Memory lock limit for deploy user
deploy     hard  memlock      unlimited

# Group-specific limits
@developers soft  nproc        4096     # Developer group process limit
@developers hard  nproc        8192
@developers soft  nofile       8192     # Developer group file descriptors
@developers hard  nofile       16384

# Database user limits
mysql      soft  nofile       16384     # MySQL user file descriptors
mysql      hard  nofile       32768
mysql      soft  memlock      unlimited # Allow memory locking for MySQL
mysql      hard  memlock      unlimited

# Web server limits
nginx      soft  nofile       8192      # Nginx user file descriptors
nginx      hard  nofile       16384
apache     soft  nofile       8192      # Apache user file descriptors
apache     hard  nofile       16384
EOF

# Systemd service limits
cat << 'EOF' > /etc/systemd/system/myapp.service
[Unit]
Description=My Application
After=network.target

[Service]
Type=simple
User=myapp
Group=myapp
ExecStart=/opt/myapp/bin/myapp

# Resource limits
LimitNOFILE=8192                       # File descriptor limit
LimitNPROC=4096                        # Process limit
LimitMEMLOCK=infinity                  # Memory lock limit
LimitCORE=0                            # Core dump limit
LimitCPU=3600                          # CPU time limit (seconds)
LimitFSIZE=1073741824                  # File size limit (1GB)

# Memory and CPU controls
MemoryLimit=1G                         # Memory limit
CPUQuota=50%                           # CPU usage limit

[Install]
WantedBy=multi-user.target
EOF
```

### Resource Limit Monitoring
```bash
# Monitor current resource usage
cat << 'EOF' > resource_monitor.sh
#!/bin/bash
# Resource usage monitoring script

monitor_process_limits() {
    local pid="$1"

    if [[ ! -d "/proc/$pid" ]]; then
        echo "Process $pid does not exist"
        return 1
    fi

    echo "Resource limits for PID $pid ($(ps -p $pid -o comm=)):"
    echo "----------------------------------------"

    # Read limits from /proc
    while IFS= read -r line; do
        limit_name=$(echo "$line" | awk '{print $1, $2}')
        soft_limit=$(echo "$line" | awk '{print $3}')
        hard_limit=$(echo "$line" | awk '{print $4}')
        units=$(echo "$line" | awk '{print $5}')

        printf "%-25s: %15s / %-15s %s\n" "$limit_name" "$soft_limit" "$hard_limit" "$units"
    done < "/proc/$pid/limits"

    echo
    echo "Current resource usage:"
    echo "----------------------"

    # File descriptors
    fd_count=$(ls -1 /proc/$pid/fd 2>/dev/null | wc -l)
    fd_limit=$(awk '/Max open files/ {print $4}' /proc/$pid/limits)
    echo "File descriptors: $fd_count / $fd_limit"

    # Memory usage
    if [[ -f "/proc/$pid/status" ]]; then
        vmrss=$(awk '/VmRSS:/ {print $2}' /proc/$pid/status)
        vmsize=$(awk '/VmSize:/ {print $2}' /proc/$pid/status)
        echo "Memory RSS: ${vmrss:-0} KB"
        echo "Memory Virtual: ${vmsize:-0} KB"
    fi
}

# Monitor all processes for a user
monitor_user_processes() {
    local username="$1"

    echo "Process resource usage for user: $username"
    echo "=========================================="

    pgrep -u "$username" | while read -r pid; do
        if [[ -d "/proc/$pid" ]]; then
            cmd=$(ps -p $pid -o comm= 2>/dev/null)
            fd_count=$(ls -1 /proc/$pid/fd 2>/dev/null | wc -l)
            vmrss=$(awk '/VmRSS:/ {print $2}' /proc/$pid/status 2>/dev/null)

            printf "PID: %-8s CMD: %-15s FDs: %-6s RSS: %s KB\n" \
                "$pid" "$cmd" "$fd_count" "${vmrss:-0}"
        fi
    done
}

# Usage examples
case "$1" in
    process)
        monitor_process_limits "$2"
        ;;
    user)
        monitor_user_processes "$2"
        ;;
    *)
        echo "Usage: $0 {process PID|user USERNAME}"
        echo "Examples:"
        echo "  $0 process 1234"
        echo "  $0 user apache"
        ;;
esac
EOF

chmod +x resource_monitor.sh

# System-wide resource monitoring
cat << 'EOF' > system_resource_check.sh
#!/bin/bash
# System-wide resource usage check

echo "System Resource Usage Summary"
echo "============================"
echo "Date: $(date)"
echo

# File descriptor usage
echo "File Descriptor Usage:"
echo "----------------------"
total_fds=0
while read -r pid comm; do
    if [[ -d "/proc/$pid/fd" ]]; then
        fd_count=$(ls -1 /proc/$pid/fd 2>/dev/null | wc -l)
        total_fds=$((total_fds + fd_count))
        if [[ $fd_count -gt 100 ]]; then
            echo "$comm (PID $pid): $fd_count file descriptors"
        fi
    fi
done < <(ps -eo pid,comm --no-headers)

echo "Total system file descriptors in use: $total_fds"
echo "System limit: $(cat /proc/sys/fs/file-max)"
echo

# Process count by user
echo "Process Count by User:"
echo "---------------------"
ps -eo user --no-headers | sort | uniq -c | sort -nr | head -10

echo
echo "Top Memory Consumers:"
echo "--------------------"
ps -eo pid,user,comm,pmem,rss --sort=-rss --no-headers | head -10

echo
echo "Processes with High Nice Values (Low Priority):"
echo "----------------------------------------------"
ps -eo pid,user,ni,comm --no-headers | awk '$3 > 10' | head -10
EOF

chmod +x system_resource_check.sh
```

## Advanced Process Control Techniques

### Process Isolation and Containers
```bash
# Process namespace isolation
unshare --pid --fork --mount-proc bash  # Create new PID namespace
unshare --net --pid --fork bash         # Network and PID isolation
unshare --user --map-root-user bash     # User namespace isolation

# CPU affinity control
taskset -c 0,1 command                  # Run on CPUs 0 and 1
taskset -p 0x3 PID                      # Set CPU affinity for existing process
numactl --cpubind=0 --membind=0 command # NUMA-aware process binding

# I/O scheduling classes
ionice -c 1 -n 4 command                # Real-time I/O class, priority 4
ionice -c 2 -n 7 command                # Best-effort I/O class, priority 7
ionice -c 3 command                     # Idle I/O class

# Combined resource control
nice -n 10 ionice -c 3 taskset -c 0 command  # Low priority, idle I/O, single CPU
```

### Process Control Groups (cgroups)
```bash
# Manual cgroup management
mkdir -p /sys/fs/cgroup/memory/myapp    # Create memory cgroup
echo $$ > /sys/fs/cgroup/memory/myapp/tasks  # Add current shell to cgroup
echo "512M" > /sys/fs/cgroup/memory/myapp/memory.limit_in_bytes  # Set memory limit

# Systemd-managed resource control
systemctl set-property myapp.service MemoryLimit=1G
systemctl set-property myapp.service CPUQuota=50%
systemctl set-property myapp.service BlockIOWeight=500

# Monitor cgroup usage
cat /sys/fs/cgroup/memory/myapp/memory.usage_in_bytes
cat /sys/fs/cgroup/cpu/myapp/cpuacct.usage
systemctl show myapp.service | grep -E "(Memory|CPU)"
```

### Process Debugging and Control
```bash
# Process tracing and debugging
strace -p PID                           # Trace system calls of running process
strace -f -e trace=file command         # Trace file operations
ltrace -p PID                           # Trace library calls
gdb -p PID                              # Attach debugger to running process

# Process state manipulation
kill -STOP PID                          # Pause process
kill -CONT PID                          # Resume process
gdb -p PID -ex "call pause()" -ex "detach" -ex "quit"  # Pause with gdb

# Advanced process monitoring
cat << 'EOF' > advanced_process_monitor.sh
#!/bin/bash
# Advanced process monitoring and control

monitor_process_performance() {
    local pid="$1"
    local duration="${2:-60}"

    if [[ ! -d "/proc/$pid" ]]; then
        echo "Process $pid does not exist"
        return 1
    fi

    echo "Monitoring PID $pid for $duration seconds..."

    # Monitor CPU, memory, and I/O
    {
        echo "timestamp,cpu_percent,memory_rss_kb,memory_vms_kb,read_bytes,write_bytes"

        for ((i=0; i<duration; i++)); do
            if [[ ! -d "/proc/$pid" ]]; then
                echo "Process $pid terminated"
                break
            fi

            # Get CPU usage
            cpu_percent=$(ps -p $pid -o %cpu= 2>/dev/null | tr -d ' ')

            # Get memory usage
            if [[ -f "/proc/$pid/status" ]]; then
                memory_rss=$(awk '/VmRSS:/ {print $2}' /proc/$pid/status)
                memory_vms=$(awk '/VmSize:/ {print $2}' /proc/$pid/status)
            else
                memory_rss=0
                memory_vms=0
            fi

            # Get I/O statistics
            if [[ -f "/proc/$pid/io" ]]; then
                read_bytes=$(awk '/read_bytes:/ {print $2}' /proc/$pid/io)
                write_bytes=$(awk '/write_bytes:/ {print $2}' /proc/$pid/io)
            else
                read_bytes=0
                write_bytes=0
            fi

            timestamp=$(date '+%Y-%m-%d %H:%M:%S')
            echo "$timestamp,$cpu_percent,$memory_rss,$memory_vms,$read_bytes,$write_bytes"

            sleep 1
        done
    } > "process_${pid}_monitor.csv"

    echo "Monitoring data saved to process_${pid}_monitor.csv"
}

# Usage
if [[ $# -eq 0 ]]; then
    echo "Usage: $0 <PID> [duration_seconds]"
    exit 1
fi

monitor_process_performance "$1" "$2"
EOF

chmod +x advanced_process_monitor.sh
```