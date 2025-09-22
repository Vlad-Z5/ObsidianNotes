# Linux Process Management Performance Monitoring

**Performance Monitoring and Analysis** covers comprehensive system performance monitoring including memory, CPU, and I/O analysis for effective system optimization and troubleshooting.

## Memory Management and Monitoring

### Understanding Memory Usage
```bash
# Basic memory information
free -h                                # Human-readable memory usage
free -s 5                              # Update every 5 seconds
free -w                                # Wide output with separate buffer/cache
free -m                                # Display in megabytes
free -g                                # Display in gigabytes
cat /proc/meminfo                      # Detailed memory information

# Key memory metrics explained:
# MemTotal: Total physical RAM
# MemFree: Unused RAM (not including cache/buffers)
# MemAvailable: Available for new applications (most important metric)
# Buffers: File metadata cache
# Cached: File content cache
# SwapTotal/SwapFree: Swap space usage
# Active/Inactive: Recently used vs. less recently used memory
# Dirty: Memory waiting to be written to disk
# Slab: Kernel data structures cache

# Memory usage calculations
echo "Memory utilization: $(free | awk 'NR==2{printf "%.1f%%\n", ($3/$2)*100}')"
echo "Cache ratio: $(free | awk 'NR==2{printf "%.1f%%\n", ($6/$2)*100}')"
```

### Advanced Memory Monitoring
```bash
# vmstat - Virtual memory statistics
vmstat 5                               # Update every 5 seconds
vmstat -S M                            # Display in MB
vmstat -d                              # Disk statistics
vmstat -s                              # Summary statistics
vmstat -w                              # Wide output format

# Key vmstat fields:
# procs r: Processes waiting for runtime
# procs b: Processes blocked (I/O wait)
# memory swpd: Swap memory used (KB)
# memory free: Free memory (KB)
# memory buff: Buffer cache (KB)
# memory cache: Page cache (KB)
# io bi: Blocks received from devices (blocks/s)
# io bo: Blocks sent to devices (blocks/s)
# system in: Interrupts per second
# system cs: Context switches per second
# cpu us: User CPU time percentage
# cpu sy: System CPU time percentage
# cpu id: Idle CPU time percentage
# cpu wa: I/O wait time percentage

# Process memory analysis
ps aux --sort=-%mem                    # Sort processes by memory usage
ps aux --sort=-%mem | head -20         # Top 20 memory consumers
ps -eo pid,ppid,cmd,pmem,rss,vsz --sort=-pmem | head -15  # Detailed memory info

# Memory mapping analysis
pmap -x PID                            # Memory map of specific process
pmap -d PID                            # Device memory mapping
pmap -X PID                            # More detailed mapping information

# System-wide memory analysis
smem -tk                               # Memory usage with totals (if available)
ps -eo comm,pmem --sort=-pmem | head -10  # Memory usage by command
```

### Buffer and Cache Management
```bash
# Cache and buffer analysis
cat /proc/meminfo | grep -E 'Buffers|Cached|MemFree|MemAvailable'

# Calculate cache effectiveness
buffer_cache_ratio() {
    local total=$(grep MemTotal /proc/meminfo | awk '{print $2}')
    local cached=$(grep "^Cached:" /proc/meminfo | awk '{print $2}')
    local buffers=$(grep Buffers /proc/meminfo | awk '{print $2}')
    local cache_total=$((cached + buffers))

    echo "scale=2; $cache_total / $total * 100" | bc
}

echo "Buffer+Cache ratio: $(buffer_cache_ratio)%"

# Memory pressure indicators
cat /proc/vmstat | grep -E 'pgpgin|pgpgout|pswpin|pswpout'

# Monitor memory allocation patterns
watch 'cat /proc/meminfo | grep -E "MemTotal|MemFree|MemAvailable|Buffers|Cached|SwapTotal|SwapFree"'

# Clear caches (use with extreme caution in production!)
sync                                   # Flush filesystem buffers first
echo 1 > /proc/sys/vm/drop_caches      # Clear page cache only
echo 2 > /proc/sys/vm/drop_caches      # Clear dentries and inodes
echo 3 > /proc/sys/vm/drop_caches      # Clear all caches

# Monitor cache effectiveness over time
sar -r 5 12                            # Memory usage every 5 seconds, 12 times
sar -R 5 12                            # Memory activity statistics
iostat -x 1 10                         # I/O statistics to correlate with cache usage
```

## CPU Performance Analysis

### Load Average Understanding
```bash
# Understanding load average
uptime
# Output example: load average: 0.52, 0.58, 0.59
#                 1-min  5-min  15-min averages

# Load average interpretation:
# < 1.0: System underutilized
# = 1.0: System fully utilized
# > 1.0: System overloaded (tasks waiting)
# Rule of thumb: load should be <= number of CPU cores

nproc                                  # Number of CPU cores
cat /proc/cpuinfo | grep processor | wc -l  # Alternative CPU core count

# Load per core calculation
load_per_core() {
    local load_1min=$(uptime | awk -F'load average:' '{print $2}' | awk -F',' '{print $1}' | tr -d ' ')
    local cores=$(nproc)
    echo "scale=2; $load_1min / $cores" | bc
}

echo "Load per core: $(load_per_core)"

# Historical load analysis
sar -q 5 12                            # Load average and run queue
```

### CPU Monitoring Tools
```bash
# mpstat - Multi-processor statistics
mpstat 5 12                            # 5-second intervals, 12 samples
mpstat -P ALL 5                        # Per-CPU core statistics
mpstat -I CPU 5                        # CPU interrupt statistics
mpstat -A 5 3                          # All activities for 3 samples

# Key mpstat fields:
# %usr: User CPU time (application code)
# %nice: Nice user CPU time (low priority processes)
# %sys: System CPU time (kernel code)
# %iowait: CPU waiting for I/O completion
# %irq: Hardware interrupt time
# %soft: Software interrupt time (soft IRQs)
# %steal: Time stolen by hypervisor (virtualized environments)
# %guest: Time running virtual processor
# %idle: Idle CPU time

# iostat - Combined I/O and CPU statistics
iostat -c 5                            # CPU statistics only
iostat -x 5                            # Extended I/O statistics
iostat -c -x 5 10                      # Both CPU and I/O, 10 samples

# Advanced CPU analysis
sar -u 5 12                            # CPU usage over time
sar -q 5 12                            # Load average and run queue
sar -w 5 12                            # Context switching and interrupts

# CPU utilization breakdown
cat << 'EOF' > cpu_analysis.sh
#!/bin/bash
# Detailed CPU analysis script

echo "=== CPU Analysis Report ==="
echo "Date: $(date)"
echo

# Basic CPU information
echo "CPU Information:"
echo "Cores: $(nproc)"
echo "Threads: $(grep processor /proc/cpuinfo | wc -l)"
echo "Model: $(grep 'model name' /proc/cpuinfo | head -1 | cut -d: -f2 | xargs)"
echo

# Current load
echo "Current Load:"
uptime
echo "Load per core: $(load_per_core)"
echo

# Top CPU consuming processes
echo "Top CPU Consumers:"
ps aux --sort=-%cpu | head -10
echo

# CPU frequency information (if available)
if [[ -f /proc/cpuinfo ]]; then
    echo "CPU Frequencies:"
    grep MHz /proc/cpuinfo | awk '{print $4}' | sort -n | uniq -c
    echo
fi

# Context switches and interrupts
echo "System Activity:"
vmstat 1 3 | tail -1 | awk '{print "Context switches/sec: " $12 "\nInterrupts/sec: " $11}'
EOF

chmod +x cpu_analysis.sh
```

### Process CPU Analysis
```bash
# Interactive process monitoring
top -o %CPU                            # Sort by CPU usage in top
htop                                   # Enhanced interactive process viewer
atop                                   # Advanced system and process monitor

# CPU affinity management
taskset -c 0,1 command                 # Run command on specific CPU cores
taskset -p 0x3 PID                     # Set CPU affinity for existing process (cores 0,1)
taskset -cp 0-3 PID                    # Set affinity to cores 0 through 3
numactl --cpubind=0 --membind=0 command # NUMA-aware process binding

# Check current CPU affinity
taskset -cp PID                        # Show current CPU affinity
cat /proc/PID/status | grep Cpus_allowed_list  # Alternative method

# Process scheduling information
ps -eo pid,class,ni,pri,psr,comm       # Show scheduling class and CPU
chrt -p PID                            # Show scheduling policy
chrt -f -p 99 PID                      # Set FIFO real-time priority
chrt -r -p 50 PID                      # Set round-robin real-time priority

# CPU time analysis
ps -eo pid,comm,time,etime,%cpu --sort=-%cpu | head -15  # Process CPU time usage
```

## I/O Performance Monitoring

### Disk I/O Analysis
```bash
# iotop - I/O usage by process
iotop                                  # Interactive I/O monitor
iotop -o                               # Only show processes with I/O activity
iotop -a                               # Show accumulated I/O usage
iotop -P                               # Show processes instead of threads
iotop -k                               # Use kilobytes instead of percentage
iotop -b -n 3                          # Batch mode, 3 iterations

# iostat - Detailed I/O statistics
iostat -x 1                            # Extended statistics every second
iostat -x -d 5 10                      # Disk only, 5-second intervals, 10 samples
iostat -c -d 2                         # Both CPU and disk every 2 seconds

# Key iostat fields:
# Device: Block device name
# r/s, w/s: Read/write requests per second
# rkB/s, wkB/s: Kilobytes read/written per second
# rrqm/s, wrqm/s: Read/write requests merged per second
# %rrqm, %wrqm: Percentage of read/write requests merged
# r_await, w_await: Average wait time for read/write requests (ms)
# aqu-sz: Average queue size
# rareq-sz, wareq-sz: Average request size (KB)
# svctm: Average service time (deprecated)
# %util: Percentage of time device was busy

# Block device statistics
cat /proc/diskstats                    # Raw disk statistics
lsblk -f                               # Block device filesystem information
lsblk -t                               # Block device topology information
```

### Advanced I/O Monitoring
```bash
# dstat - Comprehensive system statistics
dstat                                  # Basic system stats
dstat -cdngy                           # CPU, disk, network, memory
dstat --top-io --top-bio              # Top I/O processes
dstat --disk-util --disk-tps          # Disk utilization and transactions
dstat -D sda,sdb --disk               # Specific disk monitoring

# Process I/O statistics
cat /proc/PID/io                       # I/O stats for specific process
# Key fields:
# rchar: Characters read (including cached)
# wchar: Characters written (including cached)
# read_bytes: Bytes read from storage
# write_bytes: Bytes written to storage

# Find top I/O processes
find /proc -name io -exec grep -H "read_bytes\|write_bytes" {} \; 2>/dev/null | \
    awk -F: '{print $1 " " $3}' | sort -k2 -nr | head -10

# I/O monitoring script
cat << 'EOF' > io_monitor.sh
#!/bin/bash
# I/O performance monitoring script

monitor_io_performance() {
    local duration="${1:-60}"

    echo "=== I/O Performance Monitor ==="
    echo "Monitoring for $duration seconds..."
    echo

    # Capture initial I/O stats
    iostat -x 1 $duration | tee io_report.txt

    echo
    echo "=== I/O Summary ==="

    # Analyze the results
    awk '/^Device:/ {next} /^$/ {next} {
        if (NF >= 10) {
            device=$1; util=$NF;
            if (util > 80) print "High utilization: " device " " util "%"
        }
    }' io_report.txt

    echo
    echo "Top I/O processes during monitoring:"
    ps aux --sort=-majflt | head -10
}

# Usage
monitor_io_performance "$1"
EOF

chmod +x io_monitor.sh

# Filesystem I/O monitoring
df -h                                  # Disk space usage
df -i                                  # Inode usage
lsof +D /path/to/directory             # Files open in directory
fuser -v /mount/point                  # Processes using filesystem

# Advanced filesystem monitoring
watch 'df -h && echo && iostat -x 1 1'  # Combined disk space and I/O
```

## Comprehensive Performance Analysis

### Multi-metric Monitoring
```bash
# Combined performance monitoring
cat << 'EOF' > system_performance_monitor.sh
#!/bin/bash
# Comprehensive system performance monitoring

performance_snapshot() {
    echo "=== System Performance Snapshot ==="
    echo "Date: $(date)"
    echo

    # CPU metrics
    echo "CPU Metrics:"
    echo "Load average: $(uptime | awk -F'load average:' '{print $2}')"
    echo "CPU cores: $(nproc)"
    echo "CPU usage: $(vmstat 1 2 | tail -1 | awk '{print "User: " $13 "%, System: " $14 "%, Idle: " $15 "%"}')"
    echo

    # Memory metrics
    echo "Memory Metrics:"
    free -h | grep -E '^Mem|^Swap'
    echo "Available memory: $(grep MemAvailable /proc/meminfo | awk '{print $2/1024/1024 "GB"}')"
    echo

    # Disk metrics
    echo "Disk Metrics:"
    df -h | grep -E '^/dev/'
    echo

    # Network metrics (if available)
    echo "Network Metrics:"
    if command -v ss >/dev/null; then
        echo "Active connections: $(ss -tun | wc -l)"
        echo "Listening ports: $(ss -tuln | grep LISTEN | wc -l)"
    fi
    echo

    # Top processes
    echo "Top CPU Processes:"
    ps aux --sort=-%cpu | head -6
    echo
    echo "Top Memory Processes:"
    ps aux --sort=-%mem | head -6
    echo
}

# Real-time monitoring function
realtime_monitor() {
    local interval="${1:-5}"

    while true; do
        clear
        performance_snapshot
        echo "Press Ctrl+C to stop monitoring"
        sleep "$interval"
    done
}

# Usage
case "$1" in
    snapshot)
        performance_snapshot
        ;;
    monitor)
        realtime_monitor "$2"
        ;;
    *)
        echo "Usage: $0 {snapshot|monitor [interval]}"
        echo "Examples:"
        echo "  $0 snapshot          # Single performance snapshot"
        echo "  $0 monitor 10        # Monitor every 10 seconds"
        ;;
esac
EOF

chmod +x system_performance_monitor.sh

# Performance trending
sar -A -o /tmp/system_perf_$(date +%Y%m%d).sar 300 288  # Collect data every 5 minutes for 24 hours
```