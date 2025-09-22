# Linux Process Management Production Troubleshooting

**Production Troubleshooting Scenarios** covers real-world problem-solving approaches for common process management issues in production environments, including memory leaks, high CPU usage, zombie processes, and container process management.

## Scenario 1: Memory Leak Detection and Resolution

**Problem**: Application consuming increasing memory over time, eventually causing OOM kills.

### Detection and Analysis
```bash
# Step 1: Identify the memory leak
ps aux --sort=-%mem | head -10          # Find memory-hungry processes
top -p $(pgrep application_name)        # Monitor specific process memory
htop -p $(pgrep application_name)       # Interactive monitoring
pmap -x PID                             # Detailed memory mapping

# Step 2: Monitor memory growth pattern
cat << 'EOF' > memory_monitor.sh
#!/bin/bash
# Track memory usage over time
PID=$1
LOGFILE="memory_growth_$(date +%Y%m%d_%H%M%S).log"

if [[ -z "$PID" ]]; then
    echo "Usage: $0 <PID>"
    exit 1
fi

echo "Monitoring memory for PID $PID. Log: $LOGFILE"
echo "timestamp,pid,ppid,pcpu,pmem,rss,vsz,comm" > "$LOGFILE"

while [[ -d "/proc/$PID" ]]; do
    ps -o pid,ppid,pcpu,pmem,rss,vsz,comm -p $PID --no-headers | \
        sed "s/^/$(date '+%Y-%m-%d %H:%M:%S'),/" >> "$LOGFILE"
    sleep 60
done

echo "Process $PID terminated. Log saved to $LOGFILE"
EOF

chmod +x memory_monitor.sh
./memory_monitor.sh $(pgrep myapp)

# Step 3: Analyze memory allocation patterns
smem -p                                 # Process memory usage (if available)
cat /proc/PID/smaps | grep -E "Size|Rss|Pss|Swap"  # Detailed memory mapping
cat /proc/PID/status | grep -E "Vm.*|Rss|Swap"      # Virtual memory statistics
```

### Debugging Tools
```bash
# Memory leak detection tools
valgrind --leak-check=full --track-origins=yes ./application  # Memory leak detection
valgrind --tool=massif ./application    # Heap profiler

# System call analysis
strace -f -e trace=mmap,munmap,brk -p PID  # Memory allocation system calls
strace -f -e trace=memory -p PID            # All memory-related calls

# Dynamic analysis
gdb -p PID                              # Attach debugger
(gdb) info proc mappings                # Memory mappings in gdb
(gdb) call malloc_stats()               # Malloc statistics (if available)

# Monitor heap growth
cat << 'EOF' > heap_monitor.sh
#!/bin/bash
# Monitor heap size growth
PID=$1

while [[ -d "/proc/$PID" ]]; do
    heap_size=$(cat /proc/$PID/smaps | awk '/\[heap\]/{getline; print $2}' | sed 's/kB//')
    echo "$(date): Heap size: ${heap_size}kB"
    sleep 30
done
EOF

chmod +x heap_monitor.sh
```

### Mitigation Strategies
```bash
# Step 4: Temporary mitigation - Set memory limits
systemctl edit application.service
# Add to override file:
[Service]
MemoryMax=2G                           # Hard memory limit
MemoryHigh=1.8G                        # Soft memory limit (throttling)
MemorySwapMax=0                        # Disable swap for service

# Automatic restart on high memory usage
cat << 'EOF' > memory_watchdog.sh
#!/bin/bash
# Automatic restart on high memory usage
SERVICE_NAME="$1"
THRESHOLD="${2:-80}"                   # Default 80% memory usage

if [[ -z "$SERVICE_NAME" ]]; then
    echo "Usage: $0 <service_name> [threshold_percent]"
    exit 1
fi

LOGFILE="/var/log/${SERVICE_NAME}_memory_watchdog.log"

while true; do
    PID=$(systemctl show $SERVICE_NAME --property=MainPID --value)

    if [[ "$PID" != "0" && -d "/proc/$PID" ]]; then
        MEM_USAGE=$(ps -o pmem= -p $PID | tr -d ' ' | cut -d. -f1)

        if [[ $MEM_USAGE -gt $THRESHOLD ]]; then
            echo "$(date): High memory usage detected: ${MEM_USAGE}%. Restarting $SERVICE_NAME" | tee -a "$LOGFILE"
            systemctl restart $SERVICE_NAME
            sleep 60  # Wait for restart
        fi
    fi

    sleep 300  # Check every 5 minutes
done
EOF

chmod +x memory_watchdog.sh
./memory_watchdog.sh myapp.service 85 &

# Memory cleanup operations
echo 1 > /proc/sys/vm/drop_caches       # Clear page cache
echo 2 > /proc/sys/vm/drop_caches       # Clear dentries and inodes
echo 3 > /proc/sys/vm/drop_caches       # Clear all caches
```

## Scenario 2: High CPU Usage Investigation

**Problem**: Server experiencing high CPU load with slow response times.

### CPU Usage Analysis
```bash
# Step 1: Identify CPU-intensive processes
top -o %CPU                             # Sort by CPU usage
htop                                    # Interactive process viewer
ps aux --sort=-%cpu | head -20          # Top CPU consumers

# Step 2: System-wide CPU analysis
vmstat 1 10                             # Virtual memory and CPU statistics
iostat -c 1 10                          # CPU utilization
sar -u 1 10                             # Detailed CPU usage breakdown
mpstat -P ALL 1 10                      # Per-CPU statistics

# Step 3: Load average analysis
uptime                                  # Current load average
sar -q 1 10                             # Load average and run queue length
cat /proc/loadavg                       # Detailed load information
```

### Process Profiling
```bash
# Performance profiling with perf
perf top -p PID                         # Real-time profiling
perf record -p PID sleep 30             # Record performance data for 30 seconds
perf report                             # Analyze recorded data
perf stat -p PID sleep 10               # Performance counter statistics

# Alternative profiling methods
strace -c -p PID                        # System call frequency analysis
ltrace -c -p PID                        # Library call frequency analysis

# Check for specific CPU issues
pidstat -u 1 10                         # CPU usage per process
pidstat -w 1 10                         # Context switching activity
cat /proc/interrupts                    # Hardware interrupts
watch -n 1 'cat /proc/softirqs'        # Software interrupts

# CPU affinity optimization
taskset -cp 0,1 PID                     # Bind process to specific CPUs
numactl --cpubind=0 --membind=0 command # NUMA-aware CPU binding
```

### Advanced CPU Diagnostics
```bash
# CPU usage breakdown script
cat << 'EOF' > cpu_analysis.sh
#!/bin/bash
# Comprehensive CPU usage analysis

PID="$1"
DURATION="${2:-60}"

if [[ -z "$PID" ]]; then
    echo "Usage: $0 <PID> [duration_seconds]"
    exit 1
fi

echo "=== CPU Analysis for PID $PID ==="
echo "Duration: ${DURATION} seconds"
echo "Start: $(date)"
echo

# Process information
ps -p $PID -o pid,ppid,user,pcpu,pmem,etime,cmd
echo

# CPU affinity
echo "CPU Affinity: $(taskset -cp $PID 2>/dev/null || echo 'Unable to determine')"

# Real-time monitoring
echo "Monitoring CPU usage..."
{
    echo "timestamp,cpu_percent,user_time,system_time,voluntary_switches,involuntary_switches"

    for ((i=0; i<$DURATION; i++)); do
        if [[ ! -d "/proc/$PID" ]]; then
            echo "Process terminated"
            break
        fi

        # Get CPU percentage
        cpu_percent=$(ps -p $PID -o %cpu= | tr -d ' ')

        # Get detailed stats from /proc/PID/stat
        if [[ -f "/proc/$PID/stat" ]]; then
            stat_data=($(cat /proc/$PID/stat))
            utime=${stat_data[13]}
            stime=${stat_data[14]}
        else
            utime=0
            stime=0
        fi

        # Get context switch data
        if [[ -f "/proc/$PID/status" ]]; then
            vol_switches=$(grep voluntary_ctxt_switches /proc/$PID/status | awk '{print $2}')
            invol_switches=$(grep nonvoluntary_ctxt_switches /proc/$PID/status | awk '{print $2}')
        else
            vol_switches=0
            invol_switches=0
        fi

        echo "$(date '+%H:%M:%S'),$cpu_percent,$utime,$stime,$vol_switches,$invol_switches"
        sleep 1
    done
} > "cpu_analysis_${PID}_$(date +%Y%m%d_%H%M%S).csv"

echo "Analysis complete. Data saved to cpu_analysis_${PID}_*.csv"
EOF

chmod +x cpu_analysis.sh

# System-wide CPU bottleneck analysis
cat << 'EOF' > system_cpu_check.sh
#!/bin/bash
# System-wide CPU bottleneck analysis

echo "=== System CPU Bottleneck Analysis ==="
echo "Time: $(date)"
echo

# Load averages
echo "Load Averages:"
uptime
echo "CPU cores: $(nproc)"
echo

# Top CPU processes
echo "Top 10 CPU Consumers:"
ps aux --sort=-%cpu | head -11
echo

# CPU usage by state
echo "CPU Time Distribution:"
sar -u 1 1 | tail -1
echo

# Context switching rate
echo "Context Switching:"
vmstat 1 2 | tail -1 | awk '{print "Context switches/sec: " $12 ", Interrupts/sec: " $11}'
echo

# Interrupt analysis
echo "Top Interrupt Sources:"
awk '{if (NR>1) {sum+=$2; lines[NR]=$0}} END {for (i=2; i<=NR; i++) {split(lines[i], a); if (a[2]>sum*0.01) print lines[i]}}' /proc/interrupts
EOF

chmod +x system_cpu_check.sh
```

## Scenario 3: Zombie Process Cleanup

**Problem**: Accumulating zombie processes causing resource exhaustion.

### Zombie Process Detection
```bash
# Step 1: Identify zombie processes
ps aux | awk '$8 ~ /^Z/ { print }'      # Find zombie processes
ps -eo pid,ppid,state,comm | grep ' Z ' # Alternative method
ps -eo pid,ppid,state,comm | awk '$3=="Z"'  # More precise filtering

# Count zombie processes
ps aux | awk '$8 ~ /^Z/ { count++ } END { print "Zombie processes:", count+0 }'

# Step 2: Identify parent processes
ps -f --ppid $(ps aux | awk '$8 ~ /^Z/ { print $2 }' | tr '\n' ',' | sed 's/,$//')
pstree -p $(ps aux | awk '$8 ~ /^Z/ { print $3 }' | head -1)  # Process tree view
```

### Parent Process Analysis
```bash
# Step 3: Analyze why parent isn't reaping children
PARENT_PID=$(ps aux | awk '$8 ~ /^Z/ { print $3 }' | head -1)

if [[ -n "$PARENT_PID" ]]; then
    echo "Analyzing parent PID: $PARENT_PID"

    # Check parent process status
    ps -p $PARENT_PID -o pid,ppid,state,comm,args

    # Trace wait system calls
    strace -f -e trace=wait4,waitpid,wait -p $PARENT_PID &
    STRACE_PID=$!

    sleep 30
    kill $STRACE_PID

    # Check if parent is handling SIGCHLD
    kill -CHLD $PARENT_PID
fi

# Zombie cleanup script
cat << 'EOF' > zombie_cleanup.sh
#!/bin/bash
# Zombie process cleanup and monitoring

cleanup_zombies() {
    echo "=== Zombie Process Cleanup ==="

    # Find zombie processes
    zombies=$(ps -eo pid,ppid,state,comm | awk '$3=="Z" {print $1":"$2":"$4}')

    if [[ -z "$zombies" ]]; then
        echo "No zombie processes found"
        return 0
    fi

    echo "Found zombie processes:"
    echo "$zombies" | while IFS=':' read -r zpid ppid comm; do
        echo "  Zombie PID: $zpid, Parent: $ppid, Command: $comm"

        # Try to terminate parent gracefully
        if kill -0 $ppid 2>/dev/null; then
            echo "  Sending SIGTERM to parent $ppid"
            kill -TERM $ppid
            sleep 5

            # Check if zombie is cleaned up
            if ! ps -p $zpid >/dev/null 2>&1; then
                echo "  Zombie $zpid cleaned up successfully"
            else
                echo "  Zombie $zpid still exists, trying SIGKILL"
                kill -KILL $ppid 2>/dev/null
            fi
        else
            echo "  Parent process $ppid not found"
        fi
    done
}

# Monitor for zombie accumulation
monitor_zombies() {
    while true; do
        zombie_count=$(ps aux | awk '$8 ~ /^Z/ { count++ } END { print count+0 }')

        if [[ $zombie_count -gt 10 ]]; then
            echo "$(date): High zombie count detected: $zombie_count"
            cleanup_zombies
        fi

        sleep 60
    done
}

case "$1" in
    cleanup)
        cleanup_zombies
        ;;
    monitor)
        monitor_zombies
        ;;
    *)
        echo "Usage: $0 {cleanup|monitor}"
        ;;
esac
EOF

chmod +x zombie_cleanup.sh
```

## Scenario 4: Process Stuck in Uninterruptible Sleep (D State)

**Problem**: Processes stuck in D state, often due to I/O issues.

### D State Process Analysis
```bash
# Step 1: Identify stuck processes
ps aux | awk '$8 ~ /D/ { print }'       # Find processes in D state
ps -eo pid,stat,comm,wchan | grep ' D ' # Show wait channel

# Step 2: Investigate I/O issues
iostat -x 1 10                          # I/O statistics
iotop -a                                # Accumulated I/O usage
lsof -p PID                             # Files opened by stuck process

# Check what the process is waiting for
cat /proc/PID/wchan                     # Wait channel
cat /proc/PID/stack                     # Kernel stack trace

# Step 3: Storage subsystem analysis
dmesg | grep -i error                   # Kernel error messages
dmesg | grep -i "I/O error"             # I/O specific errors
smartctl -a /dev/sda                    # Hard drive health
```

### Recovery Strategies
```bash
# Step 4: Recovery attempts
sync                                    # Flush filesystem buffers
echo 1 > /proc/sys/vm/drop_caches       # Drop page cache
echo 2 > /proc/sys/vm/drop_caches       # Drop dentries and inodes
echo 3 > /proc/sys/vm/drop_caches       # Drop all caches

# Force filesystem remount (if safe)
mount -o remount,ro /problematic/filesystem
mount -o remount,rw /problematic/filesystem

# Check filesystem
fsck -f /dev/device                     # Force filesystem check (unmount first)

# D state monitoring script
cat << 'EOF' > dstate_monitor.sh
#!/bin/bash
# Monitor and analyze D state processes

monitor_dstate() {
    while true; do
        dstate_procs=$(ps -eo pid,stat,comm,wchan | awk '$2 ~ /D/ {print $1":"$3":"$4}')

        if [[ -n "$dstate_procs" ]]; then
            echo "$(date): D state processes detected:"
            echo "$dstate_procs" | while IFS=':' read -r pid comm wchan; do
                echo "  PID: $pid, Command: $comm, Wait channel: $wchan"

                # Check I/O activity
                if [[ -f "/proc/$pid/io" ]]; then
                    echo "    I/O stats:"
                    cat "/proc/$pid/io" | grep -E "read_bytes|write_bytes"
                fi

                # Check open files
                echo "    Open files:"
                lsof -p $pid 2>/dev/null | head -5
                echo
            done
        fi

        sleep 30
    done
}

monitor_dstate
EOF

chmod +x dstate_monitor.sh
```

## Scenario 5: Container Process Management Issues

**Problem**: Container processes behaving unexpectedly or consuming excessive resources.

### Container Process Analysis
```bash
# Step 1: Container overview
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Image}}\t{{.Ports}}"
docker stats --no-stream                # Resource usage snapshot
docker stats                            # Real-time resource monitoring

# Step 2: Process analysis inside containers
docker exec CONTAINER ps aux            # Processes inside container
docker exec CONTAINER top               # Real-time process monitoring
docker exec CONTAINER pstree            # Process tree

# Container resource constraints
docker inspect CONTAINER | jq '.[0].HostConfig.Memory'
docker inspect CONTAINER | jq '.[0].HostConfig.CpuQuota'
docker exec CONTAINER cat /sys/fs/cgroup/memory/memory.usage_in_bytes
```

### Advanced Container Debugging
```bash
# Step 3: Namespace analysis
container_pid=$(docker inspect -f '{{.State.Pid}}' CONTAINER)
nsenter -t $container_pid -p -m ps aux  # Enter container namespaces

# Process tree from host perspective
ps --forest -eo pid,ppid,cmd | grep -A 10 -B 5 $container_pid

# Step 4: Resource management
docker run -m 512m myapp                # Memory limit
docker run --cpus="1.5" myapp           # CPU limit
docker run --oom-kill-disable myapp     # Disable OOM killer
docker update --memory 1g CONTAINER     # Update running container limits

# Container monitoring script
cat << 'EOF' > container_monitor.sh
#!/bin/bash
# Monitor container resource usage

CONTAINER="$1"
INTERVAL="${2:-5}"

if [[ -z "$CONTAINER" ]]; then
    echo "Usage: $0 <container_name> [interval]"
    exit 1
fi

echo "Monitoring container: $CONTAINER"

while docker ps --format '{{.Names}}' | grep -q "^${CONTAINER}$"; do
    clear
    echo "=== Container Monitor: $CONTAINER ==="
    echo "Time: $(date)"
    echo

    # Container status
    docker ps --filter "name=$CONTAINER" --format "table {{.Names}}\t{{.Status}}\t{{.Image}}"
    echo

    # Resource usage
    docker stats --no-stream $CONTAINER
    echo

    # Process list
    echo "Top processes in container:"
    docker exec $CONTAINER ps aux --sort=-%cpu | head -10
    echo

    # Memory details
    echo "Memory details:"
    docker exec $CONTAINER cat /proc/meminfo | grep -E "MemTotal|MemFree|MemAvailable" 2>/dev/null || echo "Unable to read memory info"

    sleep $INTERVAL
done

echo "Container $CONTAINER is no longer running"
EOF

chmod +x container_monitor.sh
```

## Performance Optimization Strategies

### Process Priority and Scheduling
```bash
# CPU-intensive optimization
nice -n 19 cpu_intensive_process        # Lower priority for background tasks
renice -10 PID                          # Increase priority for important processes
ionice -c 3 -p PID                      # Set idle I/O priority

# Real-time scheduling (use with extreme caution)
chrt -f 50 critical_process             # FIFO real-time scheduling
chrt -r 30 time_sensitive_app           # Round-robin real-time scheduling
chrt -o 0 normal_process                # Normal scheduling

# CPU affinity for performance optimization
taskset -c 0,1 network_app              # Bind to specific CPUs
taskset -cp 2-3 PID                     # Change affinity of running process
numactl --cpubind=0 --membind=0 command # NUMA-aware process placement
```

### Memory Optimization
```bash
# Memory management optimization
echo 1 > /proc/sys/vm/compact_memory    # Trigger memory compaction
sysctl vm.swappiness=10                 # Reduce swap usage
sysctl vm.dirty_ratio=15                # Dirty page write threshold

# Process memory limits
prlimit --pid PID --as=1073741824       # Set virtual memory limit (1GB)
prlimit --pid PID --rss=536870912       # Set RSS limit (512MB)
systemctl set-property app.service MemoryMax=2G  # Systemd memory limit

# Memory optimization script
cat << 'EOF' > optimize_memory.sh
#!/bin/bash
# System memory optimization

optimize_system_memory() {
    echo "=== Memory Optimization ==="

    # Show current memory usage
    echo "Before optimization:"
    free -h
    echo

    # Compact memory
    echo "Compacting memory..."
    echo 1 > /proc/sys/vm/compact_memory

    # Adjust swappiness
    echo "Setting swappiness to 10..."
    sysctl vm.swappiness=10

    # Optimize dirty ratios
    echo "Optimizing dirty page ratios..."
    sysctl vm.dirty_ratio=15
    sysctl vm.dirty_background_ratio=5

    # Show result
    echo "After optimization:"
    free -h
}

optimize_system_memory
EOF

chmod +x optimize_memory.sh
```