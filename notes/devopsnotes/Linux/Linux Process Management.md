# Linux Process Management

## Process Control Fundamentals

### Process Monitoring and Management

#### ps Command Variations

```bash
# Standard process listing formats
ps aux                                  # All processes, user-oriented format
ps -ef                                  # All processes, full format
ps -eo pid,ppid,cmd,%mem,%cpu --sort=-%cpu  # Custom format with sorting

# DevOps-specific process analysis
ps -C nginx                            # Processes by command name
ps --forest                            # Process tree visualization
ps -o pid,ppid,state,comm -g $(pgrep -f myapp)  # Process group information

# Memory and CPU analysis
ps aux --sort=-%mem | head -10          # Top memory consumers
ps aux --sort=-%cpu | head -10          # Top CPU consumers
ps -eo pid,ppid,cmd,pmem,pcpu,time --sort=-pmem # Detailed resource usage
```

#### Process States and Signals

```bash
# Understanding process states
ps -eo pid,stat,comm
# Process state codes:
# D: Uninterruptible sleep (usually I/O wait)
# R: Running or runnable (on run queue)
# S: Interruptible sleep (waiting for event)
# T: Stopped (by job control signal)
# Z: Zombie (terminated but not reaped)
# < : High priority process
# N : Low priority process
# + : Foreground process group

# Signal management
kill -l                                 # List all available signals
kill -TERM pid                         # Graceful termination (SIGTERM)
kill -KILL pid                         # Force kill (SIGKILL)
kill -HUP pid                          # Reload configuration (SIGHUP)
kill -USR1 pid                         # User-defined signal 1
kill -USR2 pid                         # User-defined signal 2
kill -STOP pid                         # Stop process (SIGSTOP)
kill -CONT pid                         # Continue process (SIGCONT)

# Process groups and pattern matching
killall nginx                          # Kill all nginx processes
pkill -f "python.*myapp"               # Kill processes matching pattern
pgrep -u apache                        # Find processes by user
pgrep -f "java.*tomcat"                # Find processes by command pattern
```

#### Job Control and Background Processing

```bash
# Background and foreground job management
command &                              # Run command in background
jobs                                   # List active jobs in current shell
jobs -l                                # List jobs with process IDs
fg %1                                  # Bring job 1 to foreground
bg %2                                  # Send job 2 to background
nohup command &                        # Run command immune to hangups
disown %1                              # Remove job from shell's job table

# Advanced job control
nohup ./long_running_script.sh > /tmp/script.log 2>&1 &
disown -h %1                           # Mark job to ignore SIGHUP
disown -r                              # Remove all running jobs from table

# Screen and tmux for persistent sessions
screen -S session_name                 # Create named screen session
screen -r session_name                 # Reattach to screen session
screen -list                           # List available screen sessions
tmux new-session -s mysession          # Create named tmux session
tmux attach -t mysession               # Attach to tmux session
tmux list-sessions                     # List available tmux sessions
```

## Advanced Process Management

### Process Priority Control

#### nice and renice Commands

```bash
# Process priority levels (-20 to 19, lower = higher priority)
nice -n 10 ./cpu_intensive_task        # Start with lower priority
nice -n -5 ./critical_task             # Start with higher priority (requires root)
nice -20 ./background_task             # Lowest priority

# Changing priority of running processes
renice -n 5 -p 1234                    # Change priority by PID
renice -n 10 -u apache                 # Change priority for user's processes
renice -n -5 -g developers             # Change priority for group
renice +5 1234                         # Alternative syntax (increase nice value)

# Monitoring priority levels
ps -eo pid,nice,pri,comm               # Show process priorities
top -o %CPU                            # Sort top by CPU usage
```

#### Process Resource Limits (ulimit)

```bash
# View current limits
ulimit -a                              # Show all current limits
ulimit -n                              # File descriptor limit
ulimit -u                              # Process/thread limit
ulimit -m                              # Memory limit (KB)
ulimit -f                              # File size limit (blocks)
ulimit -c                              # Core dump size limit

# Set limits for current session
ulimit -n 4096                         # Increase file descriptor limit
ulimit -c unlimited                    # Enable unlimited core dumps
ulimit -u 1000                         # Limit number of processes
ulimit -f 1000000                      # Limit file size to ~1GB

# Persistent limits configuration (/etc/security/limits.conf)
cat << 'EOF' >> /etc/security/limits.conf
# Domain    Type  Item         Value
*          soft  nofile       4096      # Soft file descriptor limit
*          hard  nofile       8192      # Hard file descriptor limit
*          soft  nproc        2048      # Soft process limit
*          hard  nproc        4096      # Hard process limit
deploy     soft  nofile       8192      # User-specific limits
deploy     hard  nofile       16384
deploy     soft  memlock      unlimited # Memory lock limit
EOF

# Per-service limits in systemd units
# Add to [Service] section:
# LimitNOFILE=8192
# LimitNPROC=4096
# LimitMEMLOCK=infinity
```

## Performance Monitoring and Analysis

### Memory Management and Monitoring

#### Understanding Memory Usage

```bash
# Basic memory information
free -h                                # Human-readable memory usage
free -s 5                              # Update every 5 seconds
free -w                                # Wide output with separate buffer/cache
cat /proc/meminfo                      # Detailed memory information

# Key memory metrics explained:
# MemTotal: Total physical RAM
# MemFree: Unused RAM
# MemAvailable: Available for new applications (most important)
# Buffers: File metadata cache
# Cached: File content cache
# SwapTotal/SwapFree: Swap space usage
# Active/Inactive: Recently used vs. less recently used memory
```

#### Advanced Memory Monitoring

```bash
# vmstat - Virtual memory statistics
vmstat 5                               # Update every 5 seconds
vmstat -S M                            # Display in MB
vmstat -d                              # Disk statistics
vmstat -s                              # Summary statistics

# Key vmstat fields:
# procs r: Processes waiting for runtime
# procs b: Processes blocked (I/O wait)
# memory swpd: Swap memory used
# memory free: Free memory
# memory buff: Buffer cache
# memory cache: Page cache
# io bi: Blocks received from devices
# io bo: Blocks sent to devices
# system in: Interrupts per second
# system cs: Context switches per second

# Process memory analysis
ps aux --sort=-%mem                    # Sort processes by memory usage
pmap -x PID                            # Memory map of specific process
pmap -d PID                            # Device memory mapping
smem -tk                               # Memory usage with totals (if available)

# Memory usage by command
ps -eo comm,pmem --sort=-pmem | head -10
```

#### Buffer and Cache Management

```bash
# Cache and buffer analysis
cat /proc/meminfo | grep -E 'Buffers|Cached|MemFree|MemAvailable'
echo "Buffer hit ratio: $(echo "scale=2; $(grep Cached /proc/meminfo | head -1 | awk '{print $2}') / $(grep MemTotal /proc/meminfo | awk '{print $2}') * 100" | bc)%"

# Clear caches (use with extreme caution in production!)
sync                                   # Flush filesystem buffers first
echo 1 > /proc/sys/vm/drop_caches      # Clear page cache only
echo 2 > /proc/sys/vm/drop_caches      # Clear dentries and inodes
echo 3 > /proc/sys/vm/drop_caches      # Clear all caches

# Monitor cache effectiveness over time
sar -r 5 12                            # Memory usage every 5 seconds, 12 times
iostat -x 1 10                         # I/O statistics to correlate with cache usage
```

### CPU Performance Analysis

#### Load Average Understanding

```bash
# Understanding load average
uptime
# Output: load average: 0.52, 0.58, 0.59
#         1-min  5-min  15-min averages

# Load average interpretation:
# < 1.0: System underutilized
# = 1.0: System fully utilized
# > 1.0: System overloaded (tasks waiting)
# Rule of thumb: load should be <= number of CPU cores
nproc                                  # Number of CPU cores
```

#### CPU Monitoring Tools

```bash
# mpstat - Multi-processor statistics
mpstat 5 12                            # 5-second intervals, 12 samples
mpstat -P ALL 5                        # Per-CPU core statistics
mpstat -I CPU 5                        # CPU interrupt statistics

# Key mpstat fields:
# %usr: User CPU time (application code)
# %sys: System CPU time (kernel code)
# %iowait: CPU waiting for I/O completion
# %idle: Idle CPU time
# %irq: Hardware interrupt time
# %soft: Software interrupt time

# iostat - Combined I/O and CPU statistics
iostat -c 5                            # CPU statistics only
iostat -x 5                            # Extended I/O statistics
iostat -c -x 5 10                      # Both CPU and I/O, 10 samples

# Advanced CPU analysis
sar -u 5 12                            # CPU usage over time
sar -q 5 12                            # Load average and run queue
```

#### Process CPU Analysis

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

# Process scheduling information
ps -eo pid,class,ni,pri,psr,comm       # Show scheduling class and CPU
chrt -p PID                            # Show scheduling policy
chrt -f -p 99 PID                      # Set FIFO real-time priority
```

### I/O Performance Monitoring

#### Disk I/O Analysis

```bash
# iotop - I/O usage by process
iotop                                  # Interactive I/O monitor
iotop -o                               # Only show processes with I/O activity
iotop -a                               # Show accumulated I/O usage
iotop -P                               # Show processes instead of threads
iotop -k                               # Use kilobytes instead of percentage

# iostat - Detailed I/O statistics
iostat -x 1                            # Extended statistics every second
iostat -x -d 5 10                      # Disk only, 5-second intervals, 10 samples

# Key iostat fields:
# r/s, w/s: Read/write requests per second
# rkB/s, wkB/s: Kilobytes read/written per second
# rrqm/s, wrqm/s: Read/write requests merged per second
# %rrqm, %wrqm: Percentage of read/write requests merged
# r_await, w_await: Average wait time for read/write requests
# aqu-sz: Average queue size
# %util: Percentage of time device was busy

# Block device statistics
cat /proc/diskstats                    # Raw disk statistics
lsblk -f                               # Block device filesystem information
```

#### Advanced I/O Monitoring

```bash
# dstat - Comprehensive system statistics
dstat                                  # Basic system stats
dstat -cdngy                           # CPU, disk, network, memory
dstat --top-io --top-bio              # Top I/O processes
dstat --disk-util --disk-tps          # Disk utilization and transactions

# Process I/O statistics
cat /proc/PID/io                       # I/O stats for specific process
find /proc -name io -exec grep -H "read_bytes\|write_bytes" {} \; 2>/dev/null | head -10

# Filesystem I/O monitoring
df -h                                  # Disk space usage
df -i                                  # Inode usage
lsof +D /path/to/directory             # Files open in directory
fuser -v /mount/point                  # Processes using filesystem
```

## System Tuning and Optimization

### Kernel Parameter Tuning (sysctl)

```bash
# View and modify kernel parameters
sysctl -a                              # List all parameters
sysctl -a | grep vm                    # Virtual memory parameters
sysctl vm.swappiness                   # View specific parameter

# Temporary changes (lost on reboot)
sysctl vm.swappiness=10                # Reduce swap tendency
sysctl net.core.somaxconn=1024         # Increase socket backlog
sysctl fs.file-max=100000               # Increase file descriptor limit

# Permanent changes - create configuration file
cat << 'EOF' > /etc/sysctl.d/99-performance.conf
# Memory management optimization
vm.swappiness = 10                     # Reduce swapping (default: 60)
vm.dirty_ratio = 15                    # Dirty page ratio (default: 20)
vm.dirty_background_ratio = 5          # Background dirty ratio (default: 10)
vm.vfs_cache_pressure = 50             # VFS cache pressure (default: 100)

# Network performance
net.core.somaxconn = 1024              # Socket backlog (default: 128)
net.core.netdev_max_backlog = 5000     # Network device backlog
net.ipv4.tcp_congestion_control = bbr  # BBR congestion control
net.ipv4.tcp_slow_start_after_idle = 0 # Disable slow start after idle

# File system limits
fs.file-max = 100000                   # Maximum file descriptors
fs.inotify.max_user_watches = 524288   # Inotify watch limit
EOF

# Apply configuration
sysctl -p /etc/sysctl.d/99-performance.conf
sysctl --system                        # Reload all sysctl configurations
```

### Container Technologies and Namespaces

#### Linux Namespaces

```bash
# View process namespaces
ls -la /proc/$$/ns/                    # Current process namespaces
lsns                                   # List all namespaces
lsns -t net                            # Network namespaces only
lsns -t pid                            # PID namespaces only

# Create and manage network namespaces
ip netns add testns                    # Create network namespace
ip netns list                          # List network namespaces
ip netns exec testns ip link list      # Execute command in namespace
ip netns exec testns bash             # Start shell in namespace
ip netns delete testns                # Delete namespace

# Container namespace inspection
docker run -d --name test nginx       # Start test container
docker inspect test | grep -A 20 "NetworkMode"
docker exec test ls -la /proc/1/ns/   # View container namespaces
nsenter -t $(docker inspect -f '{{.State.Pid}}' test) -n -p # Enter container namespaces
```

#### Control Groups (cgroups)

```bash
# View cgroup hierarchy
mount | grep cgroup                    # Show mounted cgroup filesystems
ls /sys/fs/cgroup/                     # Cgroup v1 controllers
ls /sys/fs/cgroup/system.slice/        # Systemd service cgroups

# Create and manage cgroups (cgroup v1)
mkdir /sys/fs/cgroup/memory/myapp      # Create memory cgroup
echo 512M > /sys/fs/cgroup/memory/myapp/memory.limit_in_bytes
echo $$ > /sys/fs/cgroup/memory/myapp/cgroup.procs  # Add current process

# Monitor cgroup resource usage
cat /sys/fs/cgroup/memory/myapp/memory.usage_in_bytes
cat /sys/fs/cgroup/memory/myapp/memory.stat
cat /sys/fs/cgroup/memory/myapp/memory.failcnt

# Systemd and cgroups integration
systemctl show myapp.service --property=ControlGroup
systemd-cgtop                          # Real-time cgroup resource usage
systemd-cgls                           # Show cgroup hierarchy tree
```

## Scheduling and Automation

### Traditional Cron Management

```bash
# System-wide crontab (/etc/crontab)
# Format: minute hour day month dow user command
0  2  *   *   *  root   /usr/local/bin/backup.sh
30 1  *   *   0  root   /usr/sbin/logrotate /etc/logrotate.conf
*/5 * *   *   *  root   /usr/local/bin/monitor.sh

# User crontab management
crontab -e                             # Edit user crontab
crontab -l                             # List user crontab entries
crontab -r                             # Remove user crontab
crontab -u username -l                 # List another user's crontab (root only)

# Cron directories for scripts
/etc/cron.d/                           # Additional system cron jobs
/etc/cron.hourly/                      # Scripts run hourly
/etc/cron.daily/                       # Scripts run daily
/etc/cron.weekly/                      # Scripts run weekly
/etc/cron.monthly/                     # Scripts run monthly

# Cron job examples and patterns
# Every 5 minutes
*/5 * * * * /usr/local/bin/check_service.sh

# Weekdays at 9 AM
0 9 * * 1-5 /usr/local/bin/start_backup.sh

# First day of month at midnight
0 0 1 * * /usr/local/bin/monthly_report.sh

# Every 2 hours during business hours
0 8-18/2 * * 1-5 /usr/local/bin/business_check.sh

# Cron log analysis
grep CRON /var/log/syslog             # Ubuntu/Debian
grep CRON /var/log/cron                # RHEL/CentOS
journalctl _COMM=cron                  # Systemd-based systems
```

### Systemd Timers (Modern Scheduling)

```bash
# Create backup timer unit: /etc/systemd/system/backup.timer
cat << 'EOF' > /etc/systemd/system/backup.timer
[Unit]
Description=Daily Backup Timer
Requires=backup.service

[Timer]
OnCalendar=*-*-* 02:00:00             # Daily at 2 AM
Persistent=true                        # Run missed timers on boot
RandomizedDelaySec=300                # Add up to 5 minutes random delay
AccuracySec=1m                        # 1-minute accuracy

[Install]
WantedBy=timers.target
EOF

# Create corresponding service: /etc/systemd/system/backup.service
cat << 'EOF' > /etc/systemd/system/backup.service
[Unit]
Description=Daily Backup Service
After=network.target

[Service]
Type=oneshot
User=backup
Group=backup
ExecStart=/usr/local/bin/backup.sh
StandardOutput=journal
StandardError=journal
TimeoutStartSec=3600                  # 1-hour timeout
EOF

# Timer management
systemctl daemon-reload                # Reload systemd configuration
systemctl enable backup.timer          # Enable timer to start on boot
systemctl start backup.timer           # Start timer immediately
systemctl status backup.timer          # Check timer status
systemctl list-timers                  # List all active timers
systemctl list-timers --all            # List all timers (active and inactive)

# Timer calendar expressions
# OnCalendar=hourly          # Every hour
# OnCalendar=daily           # Every day at midnight
# OnCalendar=weekly          # Every week on Monday at midnight
# OnCalendar=monthly         # Every month on the 1st at midnight
# OnCalendar=*-*-* 06:30:00  # Daily at 6:30 AM
# OnCalendar=Mon,Tue *-*-* 09:00:00  # Monday and Tuesday at 9 AM

# View timer logs
journalctl -u backup.timer             # Timer logs
journalctl -u backup.service           # Service logs
journalctl -f -u backup.timer          # Follow timer logs
```

## Process Debugging and Monitoring

### System Call Tracing

#### strace - System Call Tracer

```bash
# Basic strace usage
strace ls /tmp                         # Trace system calls for ls command
strace -p 1234                         # Attach to running process PID 1234
strace -f -p 1234                      # Follow child processes
strace -e open,read,write ls           # Trace specific system calls only

# Advanced strace options
strace -c ls                           # Count and summarize system calls
strace -T ls                           # Show time spent in each system call
strace -s 1000 cat file.txt            # Increase string display length
strace -o trace.log ls                 # Output trace to file
strace -tt -T -o trace.log program     # Timestamps and timing

# DevOps debugging scenarios
strace -e file nginx                   # File operations only
strace -e network curl https://api.com # Network operations only
strace -f -e clone,exec,exit systemctl start myapp # Process creation tracking
strace -e write -p $(pgrep -f java)   # Track write operations of Java process
```

#### ltrace - Library Call Tracer

```bash
# Basic ltrace usage
ltrace ls                              # Trace library function calls
ltrace -p 1234                         # Attach to running process
ltrace -c ls                           # Count library calls
ltrace -e malloc,free program          # Trace specific functions

# Memory debugging with ltrace
ltrace -e malloc,free,realloc program  # Memory allocation tracking
ltrace -S program                      # Include system calls in output
ltrace -f program                      # Follow child processes
```

### Process Resource Monitoring

#### lsof - List Open Files

```bash
# Basic lsof usage
lsof                                   # List all open files (very verbose)
lsof /var/log/messages                 # Processes using specific file
lsof -p 1234                           # Files opened by specific process
lsof -u username                       # Files opened by user
lsof -c nginx                          # Files opened by command name

# Network connections
lsof -i                                # All network connections
lsof -i :80                            # Connections on port 80
lsof -i tcp                            # TCP connections only
lsof -i udp                            # UDP connections only
lsof -i @192.168.1.100                 # Connections to specific IP

# DevOps troubleshooting scenarios
lsof +D /var/log                       # Recursively show directory usage
lsof | grep deleted                    # Find deleted files still held open
lsof -i :443 | grep LISTEN             # Who's listening on HTTPS port
lsof -i -sTCP:ESTABLISHED              # Established TCP connections
lsof -u apache -i                      # Network connections by apache user
```

This comprehensive guide covers all essential aspects of Linux process management, from basic process control to advanced performance monitoring and system tuning, essential for effective DevOps operations.