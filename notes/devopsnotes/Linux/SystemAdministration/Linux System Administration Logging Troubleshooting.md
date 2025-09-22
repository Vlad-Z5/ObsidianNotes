# Linux System Administration Logging Troubleshooting

**System Logging and Troubleshooting** covers log file management, system performance analysis, and diagnostic tools for maintaining system health and troubleshooting issues.

## Traditional Log Files

### Important System Log Locations
```bash
# Core system logs
/var/log/messages                      # General system messages (RHEL/CentOS)
/var/log/syslog                        # System log (Debian/Ubuntu)
/var/log/auth.log                      # Authentication logs (Debian/Ubuntu)
/var/log/secure                        # Authentication logs (RHEL/CentOS)
/var/log/kern.log                      # Kernel messages
/var/log/dmesg                         # Boot messages
/var/log/cron                          # Cron job logs
/var/log/mail.log                      # Mail system logs
/var/log/daemon.log                    # System daemon logs
/var/log/user.log                      # User-level logs

# Application-specific logs
/var/log/apache2/                      # Apache web server logs
/var/log/nginx/                        # Nginx web server logs
/var/log/mysql/                        # MySQL database logs
/var/log/postgresql/                   # PostgreSQL database logs
/var/log/docker/                       # Docker daemon logs
```

### Log Analysis Commands
```bash
# Real-time log monitoring
tail -f /var/log/syslog                # Follow system log
tail -n 100 /var/log/auth.log          # Last 100 authentication entries
multitail /var/log/syslog /var/log/auth.log  # Monitor multiple logs

# Log searching and filtering
grep "ERROR" /var/log/apache2/error.log # Find errors in Apache log
grep -i "failed" /var/log/auth.log      # Case-insensitive failed login search
egrep "(ERROR|WARN|CRITICAL)" /var/log/syslog  # Multiple patterns

# Advanced log analysis
awk '/ERROR/ {print $1, $2, $NF}' /var/log/syslog # Extract error timestamps
sed -n '/2024-01-01/,/2024-01-02/p' /var/log/messages # Date range extraction
cut -d' ' -f1-3,9- /var/log/auth.log | grep "Failed password"  # Extract failed logins

# Log statistics
grep -c "ERROR" /var/log/syslog         # Count error occurrences
awk '{print $5}' /var/log/auth.log | sort | uniq -c | sort -nr  # Count by process
```

## Log Rotation Management

### Logrotate Configuration
```bash
# Main configuration
cat /etc/logrotate.conf                # Main logrotate configuration
ls /etc/logrotate.d/                   # Service-specific configurations

# Test logrotate configuration
logrotate -d /etc/logrotate.conf       # Debug mode (dry run)
logrotate -v /etc/logrotate.conf       # Verbose output
logrotate -f /etc/logrotate.d/nginx    # Force rotation

# Check logrotate status
cat /var/lib/logrotate/status          # View rotation status
logrotate -s /var/lib/logrotate/status /etc/logrotate.conf # Specify state file
```

### Custom Logrotate Configuration
```bash
# Application log rotation
cat << 'EOF' > /etc/logrotate.d/myapp
/var/log/myapp/*.log {
    daily                              # Rotate daily
    rotate 30                          # Keep 30 days of logs
    compress                           # Compress old logs
    delaycompress                      # Delay compression for one cycle
    missingok                          # OK if log file is missing
    notifempty                         # Don't rotate empty files
    create 0644 myapp myapp            # Create new log with permissions
    sharedscripts                      # Run scripts once for all logs
    postrotate                         # Run after rotation
        systemctl reload myapp > /dev/null 2>&1 || true
    endscript
}
EOF

# Web server log rotation
cat << 'EOF' > /etc/logrotate.d/nginx-custom
/var/log/nginx/*.log {
    hourly                             # Rotate hourly for high-traffic sites
    rotate 168                         # Keep 1 week (24*7) of logs
    compress
    delaycompress
    missingok
    notifempty
    create 0644 www-data www-data
    postrotate
        systemctl reload nginx > /dev/null 2>&1 || true
    endscript
}
EOF

# Database log rotation
cat << 'EOF' > /etc/logrotate.d/mysql-custom
/var/log/mysql/mysql.log {
    weekly                             # Rotate weekly
    rotate 8                           # Keep 8 weeks of logs
    compress
    delaycompress
    missingok
    notifempty
    create 0640 mysql mysql
    postrotate
        mysqladmin --defaults-file=/etc/mysql/debian.cnf flush-logs
    endscript
}
EOF
```

## System Performance Analysis

### Resource Monitoring Tools
```bash
# Process and system monitoring
top                                    # Traditional process monitor
htop                                   # Enhanced interactive process viewer
atop                                   # Advanced system and process monitor
iotop                                  # I/O usage by process
powertop                               # Power usage analysis
nmon                                   # System performance monitor

# Real-time system statistics
vmstat 5                               # Virtual memory statistics every 5 seconds
iostat -x 1                            # Extended I/O statistics every second
sar -u 5 12                            # CPU usage every 5 seconds, 12 times
sar -r 5 12                            # Memory usage statistics
sar -d 5 12                            # Disk activity statistics
sar -n DEV 5 12                        # Network statistics

# Network monitoring
netstat -tulpn                         # Network connections and listening ports
ss -tulpn                              # Modern netstat replacement
iftop                                  # Real-time network traffic
nethogs                                # Network usage by process
```

### Performance Profiling
```bash
# CPU profiling with perf
perf top                               # Real-time CPU profiling
perf record -g command                 # Record with call graphs
perf record -F 99 -a sleep 30          # Sample all CPUs for 30 seconds
perf report                            # Analyze recorded performance data
perf stat command                      # Performance counter statistics

# Memory analysis
free -h                                # Memory usage summary
cat /proc/meminfo                      # Detailed memory information
pmap -x PID                            # Process memory map
smem -p                                # Memory usage by process

# Disk performance
iotop -ao                              # Show accumulated I/O
pidstat -d 1                           # Disk I/O by process
lsof | grep deleted                    # Find deleted files still open
```

## System Information Gathering

### Hardware Information
```bash
# CPU and architecture
lscpu                                  # CPU architecture information
cat /proc/cpuinfo                      # Detailed CPU information
nproc                                  # Number of processing units

# Memory information
lsmem                                  # Memory information
cat /proc/meminfo                      # Detailed memory statistics
dmidecode --type memory                # Physical memory details

# Storage and devices
lsblk                                  # Block device information
lsblk -f                               # Show filesystem information
fdisk -l                               # Disk partition information
blkid                                  # Block device attributes

# Hardware devices
lspci                                  # PCI device information
lspci -v                               # Verbose PCI information
lsusb                                  # USB device information
lshw                                   # Complete hardware information
dmidecode                              # Hardware information from BIOS
```

### System Status Monitoring
```bash
# System uptime and load
uptime                                 # System uptime and load average
cat /proc/loadavg                      # Load average details
w                                      # Detailed user activity
who                                    # Currently logged-in users
last                                   # Login history
lastlog                                # Last login information for all users

# Filesystem information
df -h                                  # Filesystem disk usage
df -i                                  # Inode usage
du -sh /var/*                          # Directory sizes
findmnt                                # Show mounted filesystems
mount | column -t                      # Show mounts in table format

# Process information
ps aux                                 # All running processes
ps -eo pid,ppid,cmd,%mem,%cpu --sort=-%mem  # Processes sorted by memory
pstree                                 # Process tree
jobs                                   # Active jobs
```

## Advanced Troubleshooting

### System Debugging Tools
```bash
# Trace system calls
strace -p PID                          # Trace system calls for running process
strace -e trace=file command           # Trace file operations
ltrace command                         # Trace library calls

# Network debugging
tcpdump -i eth0 host 192.168.1.100     # Capture packets for specific host
wireshark                              # GUI network analyzer (if available)
nc -zv hostname 80                     # Test TCP connectivity
telnet hostname 80                     # Test TCP connection manually

# File system debugging
lsof /path/to/file                     # Show what processes have file open
lsof -p PID                            # Show files opened by process
fuser -v /path/to/file                 # Show processes using file
```

### Log Analysis Automation
```bash
# Automated log analysis script
cat << 'EOF' > /usr/local/bin/log-analyzer
#!/bin/bash
# Log Analysis Script

LOG_FILE="${1:-/var/log/syslog}"
DATE=$(date '+%Y-%m-%d')

echo "=== Log Analysis Report for $DATE ==="
echo "File: $LOG_FILE"
echo

# Error count
echo "Error Summary:"
grep -c "ERROR\|error\|Error" "$LOG_FILE" | head -1
echo

# Top error messages
echo "Top Error Messages:"
grep -i error "$LOG_FILE" | awk '{print $5,$6,$7,$8,$9}' | sort | uniq -c | sort -nr | head -10
echo

# Failed login attempts
echo "Failed Login Attempts:"
grep "Failed password" /var/log/auth.log 2>/dev/null | wc -l
echo

# Disk space warnings
echo "Disk Space Status:"
df -h | awk '$5+0 > 80 {print "WARNING: " $0}'
echo

# Memory usage
echo "Memory Usage:"
free -h
EOF

chmod +x /usr/local/bin/log-analyzer

# Run log analysis
/usr/local/bin/log-analyzer /var/log/syslog
```

### Centralized Logging Setup
```bash
# Rsyslog for centralized logging
cat << 'EOF' >> /etc/rsyslog.conf
# Forward all logs to central server
*.* @@logserver.example.com:514

# Local log filtering
local0.info     /var/log/myapp.log
local0.warn     /var/log/myapp-warnings.log
& stop

# Custom log format
$template CustomFormat,"%timegenerated% %HOSTNAME% %syslogtag% %msg%\n"
*.* /var/log/custom.log;CustomFormat
EOF

# Restart rsyslog
systemctl restart rsyslog

# Configure journald for forwarding
cat << 'EOF' >> /etc/systemd/journald.conf
[Journal]
ForwardToSyslog=yes
MaxLevelStore=info
MaxLevelSyslog=debug
SplitMode=none
EOF

systemctl restart systemd-journald
```