### Linux Philosophy & Architecture

Linux follows the Unix philosophy: "Do one thing and do it well." Understanding this principle is crucial for DevOps engineers who need to chain together simple tools to create complex automation workflows.

**Key Architecture Components:**

- **Kernel**: Core system managing hardware, processes, memory, and system calls
- **Shell**: Command interpreter (bash, zsh, fish) - your primary interface for automation
- **Filesystem**: Hierarchical structure starting from root (`/`)
- **Process Model**: Everything is a process with parent-child relationships
- **User Space vs Kernel Space**: Critical for understanding permissions and security boundaries

**DevOps Relevance**: Understanding the kernel-userspace boundary helps with container technology, system performance tuning, and debugging production issues.

### System Calls & Process Model

Every program interacts with the kernel through system calls. Key concepts:

- **fork()**: Creates child processes (how new processes are born)
- **exec()**: Replaces current process with new program
- **wait()**: Parent waits for child completion
- **Signal handling**: Inter-process communication mechanism

**DevOps Application**: Essential for understanding how containers work, process monitoring, and building robust service management scripts.

---

## 🗂️ Filesystem & File Management

### Linux Directory Structure (FHS - Filesystem Hierarchy Standard)

**Critical DevOps Directories:**

- **`/etc`**: System configuration files, service configs, cron jobs
    - `/etc/systemd/system/`: Custom systemd service files
    - `/etc/nginx/`, `/etc/apache2/`: Web server configurations
    - `/etc/ssl/`: SSL certificates and keys
    - `/etc/sudoers.d/`: Sudo privilege configurations
- **`/var`**: Variable data, logs, databases, web content
    - `/var/log/`: All system and application logs
    - `/var/lib/`: Application data (databases, package manager state)
    - `/var/spool/`: Mail, print jobs, cron jobs
    - `/var/www/`: Web server document root
- **`/tmp`**: Temporary files (cleaned on reboot)
- **`/home`**: User home directories
- **`/usr`**: User programs and utilities
    - `/usr/local/`: Locally installed software (not package managed)
    - `/usr/bin/`: User commands
    - `/usr/sbin/`: System administration commands
- **`/proc`**: Virtual filesystem exposing kernel information
    - `/proc/cpuinfo`: CPU information
    - `/proc/meminfo`: Memory statistics
    - `/proc/PID/`: Information about specific processes
- **`/sys`**: Virtual filesystem for kernel objects and hardware info
- **`/dev`**: Device files (block and character devices)
- **`/opt`**: Optional/third-party software packages
- **`/mnt`**: Temporary mount points
- **`/media`**: Removable media mount points

**DevOps Pro Tips:**

- Always use `/opt` for custom applications in production
- Monitor `/var/log` sizes - they can fill disks quickly
- `/proc` and `/sys` are goldmines for system monitoring scripts

### File Permissions & Security

#### Standard Permissions (rwx)

```bash
# Read permissions structure
ls -la
-rwxr-xr--  1 user group  4096 Jan 15 10:30 script.sh
# │││││││││
# ││││││└└└─ Other permissions (r--)
# │││└└└──── Group permissions (r-x)  
# └└└─────── Owner permissions (rwx)
```

**Permission Commands:**

```bash
# Symbolic mode
chmod u+x file.sh          # Add execute for owner
chmod g-w file             # Remove write for group
chmod o=r file             # Set other to read-only
chmod a+r file             # Add read for all

# Octal mode (more common in scripts)
chmod 755 script.sh        # rwxr-xr-x
chmod 600 private.key      # rw-------
chmod 644 config.conf      # rw-r--r--
chmod 400 secret.key       # r--------
```

**Ownership Management:**

```bash
chown user:group file      # Change owner and group
chown -R user:group dir/   # Recursive
chgrp group file           # Change group only

# DevOps common patterns
chown www-data:www-data /var/www/html
chown -R jenkins:jenkins /var/lib/jenkins
```

#### Advanced Permissions

**Sticky Bit** (`+t`):

```bash
chmod +t /tmp              # Only file owner can delete
ls -ld /tmp                # drwxrwxrwt
```

**SetUID/SetGID**:

```bash
chmod u+s /usr/bin/passwd  # Run as file owner
chmod g+s /shared/project  # New files inherit group
```

**Umask** (Default Permissions):

```bash
umask 022                  # Default: 755 for dirs, 644 for files
umask 077                  # Restrictive: 700 for dirs, 600 for files

# In DevOps scripts
umask 077                  # Secure defaults for sensitive files
```

**DevOps Security Best Practices:**

- Never use 777 permissions in production
- SSH keys should be 600 (private) and 644 (public)
- Config files with secrets: 600 or 640
- Service account permissions: principle of least privilege

### Links and Inodes

#### Hard Links vs Soft Links

```bash
# Hard link (same inode, same file)
ln file.txt hardlink.txt
ls -li file.txt hardlink.txt    # Same inode number

# Soft link (pointer to filename)
ln -s /path/to/file symlink
ls -li symlink                  # Different inode, shows target
```

**DevOps Use Cases:**

- **Hard links**: Backup strategies, ensuring files persist even if original is deleted
- **Soft links**: Configuration management, version switching, atomic deployments

```bash
# Atomic deployment pattern
ln -sfn /app/releases/v2.1.0 /app/current
systemctl restart myapp
```

#### Understanding Inodes

```bash
df -i                      # Show inode usage
ls -i file                 # Show inode number
find /path -inum 12345     # Find files by inode
```

**DevOps Monitoring**: Inode exhaustion can break systems even with free disk space.

### Mounting and Filesystems

#### Mount Operations

```bash
# View current mounts
mount                      # All mounts
mount | grep -E '^/dev'    # Just disk mounts
findmnt                    # Tree view of mounts

# Manual mounting
mount /dev/sdb1 /mnt/data
mount -t nfs server:/share /mnt/nfs
mount -o bind /src /dst    # Bind mount

# Unmounting
umount /mnt/data
umount -l /mnt/stuck       # Lazy unmount
```

#### /etc/fstab Configuration

```bash
# Device      Mount Point   FS Type  Options                    Dump Pass
/dev/sda1     /            ext4     defaults                   1    1
/dev/sda2     /home        ext4     defaults                   1    2
tmpfs         /tmp         tmpfs    defaults,noatime,size=2G   0    0
//server/share /mnt/cifs   cifs     credentials=/etc/cifs.creds 0   0
```

**DevOps fstab Options:**

- `noatime`: Better performance (no access time updates)
- `defaults`: Standard options (rw,suid,dev,exec,auto,nouser,async)
- `nofail`: Don't fail boot if mount fails
- `x-systemd.automount`: Mount on first access

#### Bind Mounts for DevOps

```bash
# Container-like isolation
mount --bind /app/config /chroot/app/config

# Read-only mounts for security
mount --bind -o ro /etc/secrets /app/secrets
```

---

## 📂 File Manipulation

### Search and Find Operations

#### find Command Mastery

```bash
# Basic syntax
find /path -name "pattern" -type f -exec command {} \;

# DevOps Examples
find /var/log -name "*.log" -mtime +7 -delete
find /home -name ".ssh" -type d -exec chmod 700 {} \;
find /opt -perm 777 -type f                          # Security audit
find /tmp -user nobody -atime +1 -delete             # Cleanup

# Advanced patterns
find /var/log -name "*.log" -size +100M -printf "%s %p\n" | sort -n
find /etc -type f -readable ! -executable -exec grep -l "password" {} \;
```

#### locate and updatedb

```bash
# Fast filename search (uses database)
locate nginx.conf
locate -r '/etc.*\.conf$'      # Regex pattern

# Update database
updatedb                       # Run as root
locate -S                      # Database statistics
```

#### xargs for Parallel Processing

```bash
# Basic usage
find /var/log -name "*.log" | xargs grep "ERROR"

# DevOps patterns
find /opt -name "*.jar" | xargs -I {} java -jar {} --version
echo "server1 server2 server3" | xargs -n1 -P3 ssh {} "uptime"
ps aux | grep python | awk '{print $2}' | xargs kill
```

### Text Processing Powerhouse

#### grep - Pattern Matching

```bash
# Basic patterns
grep "ERROR" /var/log/app.log
grep -r "TODO" /code/                    # Recursive
grep -v "DEBUG" app.log                  # Invert match
grep -c "ERROR" app.log                  # Count matches
grep -n "function" script.sh             # Line numbers

# DevOps regex patterns
grep -E '\b([0-9]{1,3}\.){3}[0-9]{1,3}\b' access.log  # Find IPs
grep -P '(?=.*ERROR)(?=.*database)' app.log           # Positive lookahead
grep -o -E '\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b' file.txt # Extract emails
```

#### awk - Pattern Scanning and Processing

```bash
# Field processing
awk '{print $1, $3}' /var/log/access.log
awk -F: '{print $1}' /etc/passwd         # Custom delimiter

# DevOps examples
ps aux | awk '$3 > 50 {print $2, $11}'   # High CPU processes
awk '/ERROR/ {count++} END {print count}' app.log
df -h | awk '$5+0 > 80 {print $6, $5}'   # Disk usage > 80%

# Complex processing
awk '{
    if ($9 ~ /^[45]/) 
        errors++ 
    else 
        success++
} 
END {
    print "Success:", success, "Errors:", errors
}' access.log
```

#### sed - Stream Editor

```bash
# Basic substitution
sed 's/old/new/g' file.txt              # Global replace
sed -i 's/DEBUG/INFO/g' config.conf     # In-place edit
sed '5d' file.txt                       # Delete line 5
sed -n '10,20p' file.txt                # Print lines 10-20

# DevOps configuration management
sed -i 's/^#\(ServerName\)/\1/' /etc/apache2/apache2.conf
sed -i '/^$/d' config.file               # Remove empty lines
sed -E 's/([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)/REDACTED/g' log.file
```

#### cut and tr - Field Extraction and Translation

```bash
# cut examples
cut -d: -f1,3 /etc/passwd               # Users and UIDs
ps aux | cut -c1-20                     # Character positions
echo "user@domain.com" | cut -d@ -f2    # Extract domain

# tr examples
tr '[:lower:]' '[:upper:]' < file.txt   # Case conversion
tr -d '\r' < dos.txt > unix.txt         # Remove carriage returns
echo "a,b,c" | tr ',' '\n'              # Convert delimiters
```

### File Compression and Archives

#### tar Command

```bash
# Create archives
tar -czf backup.tar.gz /home/user       # Gzip compressed
tar -cjf backup.tar.bz2 /opt/app        # Bzip2 compressed
tar -cJf backup.tar.xz /var/www         # XZ compressed

# Extract archives
tar -xzf backup.tar.gz                  # Extract gzip
tar -tf backup.tar.gz                   # List contents
tar -xzf backup.tar.gz --strip-components=1  # Remove top directory

# DevOps backup patterns
tar --exclude='*.log' --exclude='node_modules' -czf app-$(date +%Y%m%d).tar.gz /opt/app
```

#### Compression Tools

```bash
# gzip/gunzip
gzip file.txt                           # Creates file.txt.gz
gunzip file.txt.gz                      # Restores file.txt
zcat file.txt.gz                        # View without extracting

# Advanced compression
xz -9 largefile.txt                     # Best compression
pigz file.txt                           # Parallel gzip
```

### Streams and Redirection

#### Redirection Operators

```bash
# Output redirection
command > file.txt                      # Redirect stdout
command >> file.txt                     # Append stdout
command 2> error.log                    # Redirect stderr
command &> all.log                      # Redirect both stdout/stderr
command > output.log 2>&1               # Redirect stderr to stdout

# Input redirection
command < input.txt                     # Read from file
command <<< "string"                    # Here string
```

#### Here Documents and Here Strings

```bash
# Here document
cat << EOF > config.txt
server=production
port=8080
debug=false
EOF

# Here document in scripts
mysql -u root -p << SQL
CREATE DATABASE myapp;
GRANT ALL ON myapp.* TO 'user'@'localhost';
SQL
```

#### Pipes and tee

```bash
# Basic piping
ps aux | grep nginx | awk '{print $2}'

# tee for splitting output
command | tee output.txt                # Copy to file and stdout
command | tee -a log.txt | grep ERROR   # Append and continue pipeline
```

### Working with Large Files

#### Efficient File Viewing

```bash
# less with search and navigation
less +F /var/log/app.log                # Follow mode (like tail -f)
less +G file.txt                        # Start at end
less -S file.txt                        # No line wrapping

# tail variations
tail -f /var/log/messages               # Follow
tail -F /var/log/app.log                # Follow with retry
tail -n 100 large.log                  # Last 100 lines
tail -c 1024 file.txt                  # Last 1024 bytes

# head variations
head -n 50 file.txt                     # First 50 lines
head -c 1024 file.txt                   # First 1024 bytes
```

#### File Splitting and Processing

```bash
# split command
split -l 1000 large.log small_          # Split by lines
split -b 100M huge.file chunk_          # Split by size
split -n 5 file.txt part_               # Split into 5 parts

# Process large files efficiently
while IFS= read -r line; do
    # Process each line
    echo "Processing: $line"
done < large_file.txt
```

---

## ⚙️ Process & System Management

## 🧩 Process Control

### Process Monitoring and Management

#### ps Command Variations

```bash
# Standard formats
ps aux                                  # All processes, user-oriented
ps -ef                                  # All processes, full format
ps -eo pid,ppid,cmd,%mem,%cpu --sort=-%cpu  # Custom format

# DevOps-specific patterns
ps -C nginx                            # Processes by command name
ps --forest                            # Process tree
ps -o pid,ppid,state,comm -g $(pgrep -f myapp)  # Process group info

# Memory and CPU analysis
ps aux --sort=-%mem | head -10          # Top memory consumers
ps aux --sort=-%cpu | head -10          # Top CPU consumers
```

#### Process States and Signals

```bash
# Process states
ps -eo pid,stat,comm
# D: Uninterruptible sleep (IO)
# R: Running or runnable
# S: Interruptible sleep
# T: Stopped
# Z: Zombie

# Signal management
kill -l                                 # List all signals
kill -TERM pid                         # Graceful termination
kill -KILL pid                         # Force kill
kill -HUP pid                          # Reload configuration
kill -USR1 pid                         # User-defined signal 1

# Process groups and sessions
killall nginx                          # Kill all nginx processes
pkill -f "python.*myapp"               # Kill by pattern
pgrep -u apache                        # Find processes by user
```

#### Job Control

```bash
# Background and foreground
command &                              # Run in background
jobs                                   # List active jobs
fg %1                                  # Bring job 1 to foreground
bg %2                                  # Send job 2 to background
nohup command &                        # Persist after logout
disown %1                              # Remove from job table

# Screen and tmux for persistent sessions
screen -S session_name                 # Create named screen
screen -r session_name                 # Reattach to screen
tmux new-session -s mysession          # Create tmux session
tmux attach -t mysession               # Attach to tmux session
```

### Advanced Process Management

#### nice and renice - Priority Control

```bash
# nice levels (-20 to 19, lower = higher priority)
nice -n 10 ./cpu_intensive_task        # Lower priority
nice -n -5 ./critical_task             # Higher priority (requires root)
renice -n 5 -p 1234                    # Change existing process priority
renice -n 10 -u apache                 # Change priority for user's processes
```

#### Process Resource Limits

```bash
# ulimit for current shell
ulimit -a                              # Show all limits
ulimit -n 4096                         # Increase file descriptor limit
ulimit -c unlimited                    # Enable core dumps
ulimit -u 1000                         # Limit processes per user

# Persistent limits in /etc/security/limits.conf
# username hard nproc 100
# username soft nofile 4096
```

---

## 📈 Performance & Resource Usage

### Memory Management

#### Understanding Memory Usage

```bash
# Basic memory info
free -h                                # Human readable
free -s 5                              # Update every 5 seconds
cat /proc/meminfo                      # Detailed memory info

# Memory breakdown
# MemTotal: Total physical RAM
# MemFree: Unused RAM
# MemAvailable: Available for new applications
# Buffers: File metadata cache
# Cached: File content cache
# SwapTotal/SwapFree: Swap space usage
```

#### Memory Monitoring Tools

```bash
# vmstat - Virtual memory statistics
vmstat 5                               # Update every 5 seconds
vmstat -S M                            # Display in MB
# Key fields:
# - procs r: Running processes
# - procs b: Blocked processes
# - memory swpd: Swap used
# - memory free: Free memory
# - memory buff: Buffer cache
# - memory cache: Page cache
# - io bi: Block read/sec
# - io bo: Block write/sec

# Process memory usage
ps aux --sort=-%mem                    # Sort by memory usage
pmap -x PID                            # Memory map of process
smem -tk                               # Memory usage with totals
```

#### Buffer and Cache Management

```bash
# Clear caches (use carefully!)
echo 1 > /proc/sys/vm/drop_caches      # Clear page cache
echo 2 > /proc/sys/vm/drop_caches      # Clear dentries and inodes
echo 3 > /proc/sys/vm/drop_caches      # Clear all caches

# Monitor cache effectiveness
sar -r 5 12                            # Memory usage over time
```

### CPU Performance Analysis

#### Understanding Load Average

```bash
uptime
# load average: 0.52, 0.58, 0.59
# 1min  5min  15min averages

# Interpretation:
# < 1.0: System not fully utilized
# = 1.0: System fully utilized
# > 1.0: System overloaded (tasks waiting)
# Rule of thumb: load should be < number of CPU cores
```

#### CPU Monitoring Tools

```bash
# mpstat - Multi-processor statistics
mpstat 5 12                            # 5-second intervals, 12 times
mpstat -P ALL 5                        # Per-CPU statistics

# Key fields:
# %usr: User CPU time
# %sys: System CPU time
# %iowait: CPU waiting for I/O
# %idle: Idle time

# iostat - I/O and CPU statistics
iostat -x 5                            # Extended I/O stats
iostat -c 5                            # CPU stats only
```

#### Process CPU Analysis

```bash
# top variations
top -o %CPU                            # Sort by CPU usage
htop                                   # Interactive process viewer
atop                                   # Advanced system monitor

# CPU affinity
taskset -c 0,1 command                 # Run on specific cores
taskset -p 0x3 PID                     # Set CPU affinity for existing process
```

### I/O Performance

#### Disk I/O Monitoring

```bash
# iotop - I/O usage by process
iotop -o                               # Only show processes doing I/O
iotop -a                               # Accumulated I/O

# iostat - Detailed I/O statistics
iostat -x 1                            # Extended stats every second
# Key fields:
# r/s, w/s: Read/write requests per second
# rkB/s, wkB/s: KB read/written per second
# await: Average wait time for I/O requests
# %util: Percentage of time device was busy

# dstat - Comprehensive system stats
dstat -cdngy                           # CPU, disk, network, memory
dstat --top-io --top-bio              # Top I/O processes
```

#### Filesystem Performance

```bash
# Monitor filesystem I/O
df -h                                  # Disk usage
df -i                                  # Inode usage
lsof | grep /path                      # Files open on filesystem
fuser -v /mnt/point                    # Processes using filesystem

# I/O testing
dd if=/dev/zero of=testfile bs=1M count=1000  # Write test
dd if=testfile of=/dev/null bs=1M      # Read test
```

### System Performance Tuning

#### Kernel Parameters (sysctl)

```bash
# View current settings
sysctl -a                              # All parameters
sysctl vm.swappiness                   # Specific parameter

# Temporary changes
sysctl vm.swappiness=10                # Reduce swap usage
sysctl net.core.somaxconn=1024         # Increase socket backlog
sysctl fs.file-max=100000               # Increase file descriptor limit

# Permanent changes in /etc/sysctl.conf or /etc/sysctl.d/
cat << 'EOF' > /etc/sysctl.d/99-performance.conf
# Memory management
vm.swappiness = 10
vm.dirty_ratio = 15
vm.dirty_background_ratio = 5

# Network performance
net.core.somaxconn = 1024
net.core.netdev_max_backlog = 5000
net.ipv4.tcp_congestion_control = bbr
net.ipv4.tcp_slow_start_after_idle = 0

# File system
fs.file-max = 100000
fs.inotify.max_user_watches = 524288
EOF

# Apply changes
sysctl -p /etc/sysctl.d/99-performance.conf
```

#### Network Tuning Parameters

```bash
# TCP/IP stack tuning
cat << 'EOF' > /etc/sysctl.d/10-network.conf
# TCP buffer sizes
net.core.rmem_default = 262144
net.core.rmem_max = 16777216
net.core.wmem_default = 262144
net.core.wmem_max = 16777216
net.ipv4.tcp_rmem = 4096 87380 16777216
net.ipv4.tcp_wmem = 4096 65536 16777216

# Connection handling
net.ipv4.tcp_fin_timeout = 30
net.ipv4.tcp_keepalive_time = 1200
net.ipv4.tcp_max_syn_backlog = 8192
net.ipv4.tcp_tw_reuse = 1

# Security
net.ipv4.conf.all.accept_redirects = 0
net.ipv4.conf.all.send_redirects = 0
net.ipv4.conf.all.accept_source_route = 0
net.ipv6.conf.all.accept_redirects = 0
EOF
```

### Container Technologies and Namespaces

#### Understanding Linux Namespaces

```bash
# View process namespaces
ls -la /proc/$/ns/                    # Current process namespaces
lsns                                   # List all namespaces
lsns -t net                            # Network namespaces only

# Create network namespace
ip netns add testns                    # Create namespace
ip netns list                          # List namespaces
ip netns exec testns ip link list      # Execute in namespace

# Container namespace inspection
docker run -d --name test nginx       # Start container
docker inspect test | grep -A 20 "NetworkMode"
docker exec test ls -la /proc/1/ns/   # Container namespaces
```

#### cgroups (Control Groups)

```bash
# View cgroup hierarchy
mount | grep cgroup                    # Mounted cgroup filesystems
ls /sys/fs/cgroup/                     # Cgroup v1 controllers
ls /sys/fs/cgroup/system.slice/        # Systemd services

# Create custom cgroup
mkdir /sys/fs/cgroup/memory/myapp      # Create memory cgroup
echo 512M > /sys/fs/cgroup/memory/myapp/memory.limit_in_bytes
echo $ > /sys/fs/cgroup/memory/myapp/cgroup.procs # Add current process

# Monitor cgroup usage
cat /sys/fs/cgroup/memory/myapp/memory.usage_in_bytes
cat /sys/fs/cgroup/memory/myapp/memory.stat

# Systemd and cgroups
systemctl show myapp.service --property=ControlGroup
systemd-cgtop                          # Real-time cgroup resource usage
```

### Process Resource Control

#### ulimit - User Limits

```bash
# View current limits
ulimit -a                              # All limits
ulimit -n                              # File descriptor limit
ulimit -u                              # Process limit
ulimit -m                              # Memory limit

# Set limits for current session
ulimit -n 4096                         # Increase file descriptors
ulimit -c unlimited                    # Enable core dumps
ulimit -u 1000                         # Limit processes

# Persistent limits (/etc/security/limits.conf)
cat << 'EOF' >> /etc/security/limits.conf
# Domain    Type  Item         Value
*          soft  nofile       4096
*          hard  nofile       8192
*          soft  nproc        2048
*          hard  nproc        4096
deploy     soft  nofile       8192
deploy     hard  nofile       16384
EOF
```

#### Capabilities

```bash
# View file capabilities
getcap /usr/bin/ping                   # Show capabilities
setcap cap_net_raw+ep /usr/bin/myping  # Set capabilities

# Process capabilities
grep Cap /proc/$/status               # Current process capabilities
capsh --print                          # Readable capability format

# Common capabilities for DevOps
# CAP_NET_BIND_SERVICE - bind to privileged ports
# CAP_NET_RAW - raw sockets (ping)
# CAP_DAC_OVERRIDE - bypass file permissions
# CAP_SETUID/CAP_SETGID - change UID/GID
```

### Cron vs Systemd Timers

#### Traditional Cron

```bash
# System crontab (/etc/crontab)
# m h dom mon dow user  command
0  2  *   *   *  root   /usr/local/bin/backup.sh
30 1  *   *   0  root   /usr/sbin/logrotate /etc/logrotate.conf

# User crontab
crontab -e                             # Edit user crontab
crontab -l                             # List user crontab
crontab -r                             # Remove user crontab

# Cron directories
/etc/cron.d/                           # System cron jobs
/etc/cron.hourly/                      # Hourly scripts
/etc/cron.daily/                       # Daily scripts
/etc/cron.weekly/                      # Weekly scripts
/etc/cron.monthly/                     # Monthly scripts

# Cron job examples
# Every 5 minutes
*/5 * * * * /usr/local/bin/check_service.sh

# Weekdays at 9 AM
0 9 * * 1-5 /usr/local/bin/start_backup.sh

# First day of month at midnight
0 0 1 * * /usr/local/bin/monthly_report.sh
```

#### Systemd Timers (Modern Alternative)

```bash
# Create backup timer: /etc/systemd/system/backup.timer
cat << 'EOF' > /etc/systemd/system/backup.timer
[Unit]
Description=Daily Backup Timer
Requires=backup.service

[Timer]
OnCalendar=*-*-* 02:00:00
Persistent=true
RandomizedDelaySec=300

[Install]
WantedBy=timers.target
EOF

# Create backup service: /etc/systemd/system/backup.service
cat << 'EOF' > /etc/systemd/system/backup.service
[Unit]
Description=Daily Backup Service
After=network.target

[Service]
Type=oneshot
User=backup
ExecStart=/usr/local/bin/backup.sh
StandardOutput=journal
StandardError=journal
EOF

# Enable and manage timer
systemctl daemon-reload
systemctl enable backup.timer
systemctl start backup.timer
systemctl list-timers                  # List all timers
journalctl -u backup.service           # View service logs
```

### chroot and Containers

#### chroot (Change Root)

```bash
# Create chroot environment
mkdir /srv/chroot                      # Base directory
mkdir -p /srv/chroot/{bin,lib,lib64,etc,usr,proc,sys,dev}

# Copy essential binaries
cp /bin/bash /srv/chroot/bin/
cp /bin/ls /srv/chroot/bin/
cp /bin/cat /srv/chroot/bin/

# Copy required libraries
ldd /bin/bash | grep -o '/lib[^ ]*' | xargs -I {} cp {} /srv/chroot/lib/
ldd /bin/ls | grep -o '/lib[^ ]*' | xargs -I {} cp {} /srv/chroot/lib/

# Mount virtual filesystems
mount --bind /proc /srv/chroot/proc
mount --bind /sys /srv/chroot/sys
mount --bind /dev /srv/chroot/dev

# Enter chroot
chroot /srv/chroot /bin/bash
```

#### Understanding Container Fundamentals

```bash
# Container is essentially:
# - chroot (filesystem isolation)
# - namespaces (process, network, mount isolation)
# - cgroups (resource limits)
# - capabilities (privilege control)

# Manual container creation (educational)
unshare --pid --fork --mount-proc chroot /srv/chroot /bin/bash
# This creates:
# - New PID namespace (--pid)
# - New mount namespace (--fork)
# - Mounts /proc (--mount-proc)
# - Changes root (chroot)
```

### Security and Auditing

#### auditd - Linux Audit Framework

```bash
# Install and configure auditd
systemctl enable auditd
systemctl start auditd

# Audit configuration (/etc/audit/auditd.conf)
log_file = /var/log/audit/audit.log
log_format = RAW
log_group = root
priority_boost = 4
flush = INCREMENTAL
freq = 20

# Audit rules (/etc/audit/rules.d/audit.rules)
# Monitor file access
-w /etc/passwd -p wa -k passwd_changes
-w /etc/shadow -p wa -k shadow_changes
-w /etc/ssh/sshd_config -p wa -k ssh_config

# Monitor system calls
-a always,exit -F arch=b64 -S execve -k command_exec
-a always,exit -F arch=b64 -S open -k file_access

# Monitor network connections
-a always,exit -F arch=b64 -S socket -k network_connect

# Apply rules
augenrules --load

# Search audit logs
ausearch -k passwd_changes             # Search by key
ausearch -ui 1000                      # Search by user ID
ausearch -ts today                     # Search by time
aureport --summary                     # Generate report
```

#### File Integrity Monitoring

```bash
# AIDE (Advanced Intrusion Detection Environment)
aide --init                            # Initialize database
cp /var/lib/aide/aide.db.new /var/lib/aide/aide.db
aide --check                           # Check for changes

# Tripwire alternative with find
find /etc -type f -exec md5sum {} \; > /var/lib/integrity/etc.md5
# Later check:
find /etc -type f -exec md5sum {} \; | diff - /var/lib/integrity/etc.md5
```

### System Hardening

#### Basic Hardening Checklist

```bash
# 1. Update system
apt update && apt upgrade              # Debian/Ubuntu
yum update                             # RHEL/CentOS

# 2. Remove unnecessary packages
apt autoremove                         # Remove orphaned packages
systemctl list-unit-files --state=enabled # Review enabled services

# 3. Configure firewall
ufw enable                             # Ubuntu
systemctl enable firewalld             # RHEL

# 4. SSH hardening (covered in SSH section)
# 5. User account security
passwd -l root                         # Lock root account (if not needed)
userdel -r unnecessaryuser             # Remove unnecessary users

# 6. File permission audit
find / -perm -4000 -type f 2>/dev/null # Find SUID files
find / -perm -2000 -type f 2>/dev/null # Find SGID files
find / -perm -002 -type f 2>/dev/null  # Find world-writable files

# 7. Kernel hardening
echo 'kernel.dmesg_restrict = 1' >> /etc/sysctl.conf
echo 'kernel.kptr_restrict = 2' >> /etc/sysctl.conf
echo 'net.ipv4.conf.all.send_redirects = 0' >> /etc/sysctl.conf

# 8. Disable unused network services
systemctl disable telnet               # If installed
systemctl disable rsh                  # If installed
```

---

## 🔐 DevOps-Specific Topics

### Container Management Integration

#### Docker Integration with System Services

```bash
# Docker systemd service management
systemctl status docker                # Docker daemon status
systemctl enable docker                # Enable at boot
journalctl -u docker                   # Docker daemon logs

# Container as systemd service
cat << 'EOF' > /etc/systemd/system/webapp.service
[Unit]
Description=Web Application Container
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/usr/bin/docker run -d --name webapp -p 80:8080 myapp:latest
ExecStop=/usr/bin/docker stop webapp
ExecStopPost=/usr/bin/docker rm webapp

[Install]
WantedBy=multi-user.target
EOF

systemctl enable webapp.service
systemctl start webapp.service
```

#### Container Resource Management

```bash
# Docker with cgroups integration
docker run --memory=512m --cpus=0.5 nginx # Resource limits
docker stats                          # Real-time resource usage
docker system df                       # Disk usage
docker system prune                    # Cleanup unused resources

# Monitor container processes
docker exec container_name ps aux      # Processes in container
docker top container_name              # Host view of container processes
```

### Infrastructure as Code Integration

#### System Configuration Management

```bash
# Ansible integration points
# /etc/ansible/hosts inventory file
[webservers]
web1.example.com ansible_user=deploy
web2.example.com ansible_user=deploy

[databases]
db1.example.com ansible_user=admin

# Common Ansible system tasks
# - User management (useradd, usermod)
# - Package installation (apt, yum)
# - Service management (systemctl)
# - File management (copy, template)
# - Firewall configuration (ufw, iptables)
```

#### Configuration Validation Scripts

```bash
#!/bin/bash
# System validation script for deployment

set -euo pipefail

# Check system resources
check_system_resources() {
    local min_memory=2048  # MB
    local min_disk=10      # GB
    
    memory=$(free -m | awk 'NR==2{print $2}')
    disk=$(df -BG / | awk 'NR==2{print $4}' | sed 's/G//')
    
    if [[ $memory -lt $min_memory ]]; then
        echo "ERROR: Insufficient memory: ${memory}MB < ${min_memory}MB"
        return 1
    fi
    
    if [[ $disk -lt $min_disk ]]; then
        echo "ERROR: Insufficient disk space: ${disk}GB < ${min_disk}GB"
        return 1
    fi
    
    echo "✓ System resources check passed"
    return 0
}

# Check required services
check_services() {
    local required_services=("nginx" "mysql" "redis-server")
    
    for service in "${required_services[@]}"; do
        if ! systemctl is-active --quiet "$service"; then
            echo "ERROR: Service $service is not running"
            return 1
        fi
    done
    
    echo "✓ All required services are running"
    return 0
}

# Check network connectivity
check_connectivity() {
    local endpoints=("8.8.8.8" "github.com" "registry.docker.io")
    
    for endpoint in "${endpoints[@]}"; do
        if ! ping -c 1 "$endpoint" > /dev/null 2>&1; then
            echo "ERROR: Cannot reach $endpoint"
            return 1
        fi
    done
    
    echo "✓ Network connectivity check passed"
    return 0
}

# Main execution
main() {
    echo "Starting system validation..."
    
    check_system_resources
    check_services
    check_connectivity
    
    echo "✓ All validation checks passed"
}

main "$@"
```

### Secrets Management

#### GPG for Secret Management

```bash
# Generate GPG key
gpg --full-generate-key                # Interactive key generation
gpg --list-keys                        # List public keys
gpg --list-secret-keys                 # List private keys

# Encrypt secrets
echo "database_password=secret123" | gpg --armor --encrypt -r user@example.com > secrets.gpg
gpg --decrypt secrets.gpg              # Decrypt secrets

# Automated decryption in scripts
export GPG_PASSPHRASE="your_passphrase"
echo "$GPG_PASSPHRASE" | gpg --batch --yes --passphrase-fd 0 --decrypt secrets.gpg
```

#### Environment Variable Management

```bash
# Secure environment variable patterns
# Use separate files for different environments
cat << 'EOF' > /opt/app/config/production.env
DATABASE_URL=postgresql://user:pass@db.prod.com:5432/myapp
REDIS_URL=redis://cache.prod.com:6379
API_KEY=prod_api_key_here
EOF

# Restrict file permissions
chmod 600 /opt/app/config/production.env
chown app:app /opt/app/config/production.env

# Load in application startup
#!/bin/bash
set -a  # Automatically export variables
source /opt/app/config/production.env
set +a  # Stop auto-export
exec /opt/app/bin/start_application
```

### CI/CD Integration Points

#### Build Agent Configuration

```bash
# Jenkins agent setup
useradd -m -s /bin/bash jenkins         # Create jenkins user
usermod -aG docker jenkins              # Add to docker group
usermod -aG sudo jenkins                # Add to sudo group

# SSH key setup for deployment
su - jenkins
ssh-keygen -t rsa -b 4096 -f ~/.ssh/deploy_key
# Copy public key to deployment targets

# Sudoers configuration for deployment tasks
cat << 'EOF' > /etc/sudoers.d/jenkins
jenkins ALL=(ALL) NOPASSWD: /bin/systemctl restart myapp
jenkins ALL=(ALL) NOPASSWD: /bin/systemctl reload nginx
jenkins ALL=(ALL) NOPASSWD: /usr/bin/docker
EOF
```

#### Deployment Scripts

```bash
#!/bin/bash
# Blue-green deployment script

set -euo pipefail

readonly APP_NAME="myapp"
readonly NEW_VERSION="$1"
readonly HEALTH_CHECK_URL="http://localhost:8080/health"
readonly DEPLOYMENT_USER="deploy"

deploy_new_version() {
    echo "Deploying $APP_NAME version $NEW_VERSION"
    
    # Stop current service
    sudo systemctl stop "$APP_NAME"
    
    # Backup current version
    if [[ -d "/opt/$APP_NAME/current" ]]; then
        sudo cp -r "/opt/$APP_NAME/current" "/opt/$APP_NAME/backup-$(date +%Y%m%d-%H%M%S)"
    fi
    
    # Deploy new version
    sudo tar -xzf "/tmp/${APP_NAME}-${NEW_VERSION}.tar.gz" -C "/opt/$APP_NAME/"
    sudo ln -sfn "/opt/$APP_NAME/releases/$NEW_VERSION" "/opt/$APP_NAME/current"
    
    # Start service
    sudo systemctl start "$APP_NAME"
    
    # Health check
    sleep 10
    if curl -f "$HEALTH_CHECK_URL" > /dev/null 2>&1; then
        echo "✓ Deployment successful"
        # Cleanup old releases (keep last 5)
        cd "/opt/$APP_NAME/releases" && ls -t | tail -n +6 | sudo xargs rm -rf
    else
        echo "✗ Health check failed, rolling back"
        rollback_deployment
        exit 1
    fi
}

rollback_deployment() {
    echo "Rolling back deployment"
    local backup_dir
    backup_dir=$(ls -t "/opt/$APP_NAME/backup-"* 2>/dev/null | head -1)
    
    if [[ -n "$backup_dir" ]]; then
        sudo systemctl stop "$APP_NAME"
        sudo rm -f "/opt/$APP_NAME/current"
        sudo mv "$backup_dir" "/opt/$APP_NAME/current"
        sudo systemctl start "$APP_NAME"
        echo "✓ Rollback completed"
    else
        echo "✗ No backup found for rollback"
        exit 1
    fi
}

# Validation
if [[ $# -ne 1 ]]; then
    echo "Usage: $0 <version>"
    exit 1
fi

if [[ $EUID -eq 0 ]]; then
    echo "Do not run as root"
    exit 1
fi

deploy_new_version
```

### Monitoring Integration

#### System Metrics Collection

```bash
# Custom metrics collection script
#!/bin/bash
# System metrics for monitoring integration

get_cpu_usage() {
    local cpu_usage
    cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | sed 's/%us,//')
    echo "cpu.usage:$cpu_usage"
}

get_memory_usage() {
    local mem_total mem_used mem_percent
    mem_total=$(free | awk 'NR==2{print $2}')
    mem_used=$(free | awk 'NR==2{print $3}')
    mem_percent=$(awk "BEGIN {printf \"%.2f\", $mem_used/$mem_total*100}")
    echo "memory.usage:$mem_percent"
}

get_disk_usage() {
    local disk_usage
    disk_usage=$(df -h / | awk 'NR==2{print $5}' | sed 's/%//')
    echo "disk.usage:$disk_usage"
}

get_load_average() {
    local load_1min
    load_1min=$(uptime | awk -F'load average:' '{print $2}' | awk -F',' '{print $1}' | tr -d ' ')
    echo "load.1min:$load_1min"
}

# Output metrics in format expected by monitoring system
echo "timestamp:$(date +%s)"
get_cpu_usage
get_memory_usage
get_disk_usage
get_load_average
```

#### Log Aggregation Helpers

```bash
# Log parsing for centralized logging
#!/bin/bash
# Parse application logs and send to centralized logging

parse_nginx_logs() {
    tail -F /var/log/nginx/access.log | while read line; do
        # Parse common log format
        ip=$(echo "$line" | awk '{print $1}')
        timestamp=$(echo "$line" | awk '{print $4}' | tr -d '[')
        method=$(echo "$line" | awk '{print $6}' | tr -d '"')
        url=$(echo "$line" | awk '{print $7}')
        status=$(echo "$line" | awk '{print $9}')
        size=$(echo "$line" | awk '{print $10}')
        
        # Send to logging system (example: JSON format)
        cat << EOF | curl -X POST -H "Content-Type: application/json" -d @- http://log-server:9200/nginx-logs/_doc
{
  "timestamp": "$timestamp",
  "source_ip": "$ip",
  "method": "$method",
  "url": "$url",
  "status_code": $status,
  "response_size": $size,
  "server": "$(hostname)"
}
EOF
    done
}

parse_nginx_logs
```

### Security Automation

#### Automated Security Scanning

```bash
#!/bin/bash
# Automated security checks

security_scan() {
    echo "=== Security Scan Report $(date) ===" > /var/log/security-scan.log
    
    # Check for failed login attempts
    echo "Failed login attempts in last 24 hours:" >> /var/log/security-scan.log
    journalctl --since "24 hours ago" | grep "Failed password" | wc -l >> /var/log/security-scan.log
    
    # Check for SUID files
    echo "SUID files:" >> /var/log/security-scan.log
    find / -perm -4000 -type f 2>/dev/null >> /var/log/security-scan.log
    
    # Check open ports
    echo "Open ports:" >> /var/log/security-scan.log
    ss -tuln >> /var/log/security-scan.log
    
    # Check for updates
    echo "Available security updates:" >> /var/log/security-scan.log
    apt list --upgradable 2>/dev/null | grep -i security >> /var/log/security-scan.log
    
    # Send alert if critical issues found
    if grep -q "CRITICAL" /var/log/security-scan.log; then
        mail -s "CRITICAL Security Issues Found" admin@company.com < /var/log/security-scan.log
    fi
}

# Run daily via cron or systemd timer
security_scan
```

#### Compliance Checking

```bash
#!/bin/bash
# CIS (Center for Internet Security) basic compliance check

cis_compliance_check() {
    local score=0
    local total=0
    
    # Check 1: Ensure mounting of cramfs filesystems is disabled
    ((total++))
    if ! lsmod | grep -q cramfs; then
        echo "✓ PASS: cramfs filesystem disabled"
        ((score++))
    else
        echo "✗ FAIL: cramfs filesystem enabled"
    fi
    
    # Check 2: Ensure mounting of vFAT filesystems is disabled
    ((total++))
    if ! lsmod | grep -q vfat; then
        echo "✓ PASS: vfat filesystem disabled"
        ((score++))
    else
        echo "✗ FAIL: vfat filesystem enabled"
    fi
    
    # Check 3: Ensure SSH Protocol is set to 2
    ((total++))
    if grep -q "^Protocol 2" /etc/ssh/sshd_config; then
        echo "✓ PASS: SSH Protocol 2 configured"
        ((score++))
    else
        echo "✗ FAIL: SSH Protocol 2 not configured"
    fi
    
    # Check 4: Ensure permissions on /etc/passwd are configured
    ((total++))
    local passwd_perms
    passwd_perms=$(stat -c "%a" /etc/passwd)
    if [[ "$passwd_perms" == "644" ]]; then
        echo "✓ PASS: /etc/passwd permissions correct (644)"
        ((score++))
    else
        echo "✗ FAIL: /etc/passwd permissions incorrect ($passwd_perms)"
    fi
    
    # Check 5: Ensure password expiration is 365 days or less
    ((total++))
    local max_days
    max_days=$(grep "^PASS_MAX_DAYS" /etc/login.defs | awk '{print $2}')
    if [[ "$max_days" -le 365 && "$max_days" -gt 0 ]]; then
        echo "✓ PASS: Password expiration <= 365 days ($max_days)"
        ((score++))
    else
        echo "✗ FAIL: Password expiration > 365 days or not set ($max_days)"
    fi
    
    # Calculate compliance percentage
    local percentage
    percentage=$(awk "BEGIN {printf \"%.1f\", $score/$total*100}")
    
    echo "=========================="
    echo "CIS Compliance Score: $score/$total ($percentage%)"
    echo "=========================="
    
    # Return non-zero if compliance is below threshold
    if [[ $(echo "$percentage < 80" | bc -l) -eq 1 ]]; then
        return 1
    fi
    
    return 0
}

cis_compliance_checkctl net.core.somaxconn=1024         # Increase socket backlog

# Permanent changes in /etc/sysctl.conf
# vm.swappiness = 10
# net.core.somaxconn = 1024
# fs.file-max = 100000

# Apply changes
sysctl -p                              # Reload from config file
```

#### Performance Profiling Tools

```bash
# perf - Linux profiler
perf top                               # Real-time profiling
perf record -g ./myapp                 # Record with call graphs
perf report                            # Analyze recorded data

# strace - System call tracer
strace -p PID                          # Trace existing process
strace -c ./command                    # Count system calls
strace -e open,read,write ./command    # Trace specific calls

# ltrace - Library call tracer
ltrace ./command                       # Trace library calls
ltrace -c ./command                    # Count library calls
```

---

## 🧰 Networking

## 🌐 Network Basics

### Network Interface Management

#### Modern IP Command

```bash
# Interface information
ip addr show                           # All interfaces
ip addr show eth0                      # Specific interface
ip -4 addr show                        # IPv4 only
ip -6 addr show                        # IPv6 only

# Interface management
ip link set eth0 up                    # Bring interface up
ip link set eth0 down                  # Bring interface down
ip addr add 192.168.1.100/24 dev eth0 # Add IP address
ip addr del 192.168.1.100/24 dev eth0 # Remove IP address

# Routing
ip route show                          # Routing table
ip route add 192.168.2.0/24 via 192.168.1.1  # Add route
ip route del 192.168.2.0/24           # Delete route
ip route get 8.8.8.8                  # Show route to destination
```

#### Legacy ifconfig (still useful)

```bash
ifconfig                               # All interfaces
ifconfig eth0                          # Specific interface
ifconfig eth0 192.168.1.100/24         # Set IP address
ifconfig eth0:1 192.168.1.101/24       # Virtual interface
```

### Network Connectivity Testing

#### Ping and Advanced Testing

```bash
# Basic connectivity
ping -c 4 google.com                   # 4 packets
ping -i 0.2 -c 10 server               # 200ms interval
ping -s 1472 server                    # Large packet size
ping6 ipv6.google.com                  # IPv6 ping

# Traceroute
traceroute google.com                  # Show network path
traceroute -I google.com               # Use ICMP instead of UDP
mtr google.com                         # Continuous traceroute
```

#### Port and Service Testing

```bash
# netcat (nc) - Swiss army knife
nc -zv server 80                       # Test port connectivity
nc -l 8080                             # Listen on port 8080
echo "test" | nc server 80             # Send data to port

# telnet for protocol testing
telnet smtp.gmail.com 587              # Test SMTP
telnet pop.gmail.com 995               # Test POP3

# Modern alternatives
nmap -p 80,443 server                  # Port scanning
nmap -sS -O server                     # SYN scan with OS detection
```

### Network Service Discovery

#### Socket Statistics (ss)

```bash
# Modern replacement for netstat
ss -tuln                               # TCP/UDP listening ports
ss -tulpn                              # Include process names
ss -an | grep :80                      # Connections on port 80
ss -s                                  # Summary statistics

# Filter examples
ss 'sport = :ssh'                      # SSH connections
ss 'dport = :80'                       # HTTP connections
ss 'state connected'                   # Established connections
```

#### Legacy netstat

```bash
netstat -tuln                          # Listening ports
netstat -i                             # Interface statistics
netstat -r                             # Routing table
netstat -c                             # Continuous output
```

### DNS Management

#### DNS Query Tools

```bash
# dig - Domain Information Groper
dig google.com                         # Basic lookup
dig @8.8.8.8 google.com               # Use specific DNS server
dig google.com MX                      # Mail exchange records
dig google.com AAAA                    # IPv6 address
dig +short google.com                  # Brief output
dig +trace google.com                  # Full DNS resolution path

# nslookup (legacy but still used)
nslookup google.com                    # Basic lookup
nslookup google.com 8.8.8.8           # Use specific server

# host command
host google.com                        # Simple lookup
host -t MX google.com                  # Specific record type
```

#### DNS Configuration Files

```bash
# /etc/hosts - Local hostname resolution
127.0.0.1       localhost
192.168.1.100   myserver.local myserver

# /etc/resolv.conf - DNS servers
nameserver 8.8.8.8
nameserver 8.8.4.4
search local.domain
options timeout:2 attempts:3

# /etc/nsswitch.conf - Name resolution order
hosts: files dns myhostname
```

### HTTP/HTTPS Tools

#### curl - Command Line HTTP Client

```bash
# Basic requests
curl https://api.example.com           # GET request
curl -X POST https://api.example.com   # POST request
curl -H "Content-Type: application/json" -d '{"key":"value"}' api.url

# DevOps common patterns
curl -I https://site.com               # Headers only
curl -L https://bit.ly/shorturl        # Follow redirects
curl -k https://self-signed.com        # Ignore certificate errors
curl -w "%{http_code}\n" -o /dev/null -s https://site.com  # Just status code

# Authentication and cookies
curl -u username:password https://api.com
curl -b cookies.txt -c cookies.txt https://site.com
curl -H "Authorization: Bearer $TOKEN" https://api.com

# File operations
curl -O https://site.com/file.tar.gz   # Download with original name
curl -o myfile.tar.gz https://site.com/archive.tar.gz
curl -T localfile.txt ftp://server/    # Upload file
```

#### wget - Web Get

```bash
# Basic download
wget https://example.com/file.tar.gz
wget -O newname.tar.gz https://example.com/file.tar.gz
wget -c https://example.com/largefile.iso  # Continue interrupted download

# Recursive download
wget -r -np -k https://site.com/docs/   # Mirror directory
wget --mirror --convert-links https://site.com/
```

---

## 🔒 Security & Firewall Management

### iptables - Advanced Firewall

#### Basic iptables Operations

```bash
# View current rules
iptables -L                            # List all rules
iptables -L -n                         # Numeric output (no DNS lookups)
iptables -L -v                         # Verbose (packet counts)

# Basic rule management
iptables -A INPUT -p tcp --dport 22 -j ACCEPT    # Allow SSH
iptables -A INPUT -p tcp --dport 80 -j ACCEPT    # Allow HTTP
iptables -A INPUT -p tcp --dport 443 -j ACCEPT   # Allow HTTPS
iptables -A INPUT -j DROP                        # Default drop

# Delete rules
iptables -D INPUT 1                    # Delete rule number 1
iptables -F                            # Flush all rules
```

#### DevOps iptables Patterns

```bash
# Allow specific IP ranges
iptables -A INPUT -s 192.168.0.0/16 -j ACCEPT
iptables -A INPUT -s 10.0.0.0/8 -j ACCEPT

# Rate limiting (DoS protection)
iptables -A INPUT -p tcp --dport 80 -m limit --limit 25/minute --limit-burst 100 -j ACCEPT

# Connection tracking
iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT
iptables -A INPUT -m state --state NEW -p tcp --dport 22 -j ACCEPT

# Save and restore rules
iptables-save > /etc/iptables/rules.v4
iptables-restore < /etc/iptables/rules.v4
```

### UFW - Uncomplicated Firewall

#### UFW Basic Operations

```bash
# Enable/disable
ufw enable                             # Enable firewall
ufw disable                            # Disable firewall
ufw --force reset                      # Reset to defaults

# Basic rules
ufw allow 22                           # Allow SSH
ufw allow ssh                          # Allow SSH (by name)
ufw allow 80/tcp                       # Allow HTTP
ufw allow 443/tcp                      # Allow HTTPS
ufw deny 23                            # Deny telnet

# Advanced rules
ufw allow from 192.168.1.0/24          # Allow from subnet
ufw allow from 192.168.1.100 to any port 22  # Specific source to SSH
ufw limit ssh                          # Rate limit SSH connections

# Application logs
/var/log/apache2/                      # Apache logs
/var/log/nginx/                        # Nginx logs
/var/log/mysql/                        # MySQL logs
/var/log/postgresql/                   # PostgreSQL logs

# Log analysis commands
tail -f /var/log/messages              # Follow system messages
grep "ERROR" /var/log/apache2/error.log # Find errors
awk '/Jan 15/ {print}' /var/log/messages # Filter by date
zcat /var/log/messages.1.gz | grep "kernel" # Search compressed logs
```

#### Centralized Logging with rsyslog

```bash
# rsyslog configuration: /etc/rsyslog.conf
# Facility.Priority    Action
*.info                 /var/log/messages
mail.*                 /var/log/mail.log
authpriv.*             /var/log/secure
cron.*                 /var/log/cron

# Remote logging configuration
# Send logs to remote server
*.* @@log-server.example.com:514       # TCP
*.* @log-server.example.com:514        # UDP

# Receive logs from remote servers
$ModLoad imudp
$UDPServerRun 514
$UDPServerAddress 0.0.0.0

# Custom log formats
$template CustomFormat,"%timegenerated% %HOSTNAME% %syslogtag% %msg%\n"
*.* /var/log/custom.log;CustomFormat

# Restart rsyslog
systemctl restart rsyslog
```

### Process Debugging and Tracing

#### strace - System Call Tracer

```bash
# Basic strace usage
strace ls /tmp                         # Trace system calls
strace -p 1234                         # Attach to running process
strace -f -p 1234                      # Follow child processes
strace -e open,read,write ls           # Trace specific calls only

# Advanced strace options
strace -c ls                           # Count system calls
strace -T ls                           # Show time spent in calls
strace -s 1000 cat file.txt            # Increase string length
strace -o trace.log ls                 # Output to file

# DevOps debugging scenarios
strace -e file nginx                   # File operations only
strace -e network curl https://api.com # Network operations
strace -f -e clone,exec,exit systemctl start myapp # Process creation
```

#### lsof - List Open Files

```bash
# Basic lsof usage
lsof                                   # All open files
lsof /var/log/messages                 # Processes using specific file
lsof -p 1234                           # Files opened by process
lsof -u username                       # Files opened by user
lsof -c nginx                          # Files opened by command

# Network connections
lsof -i                                # All network connections
lsof -i :80                            # Connections on port 80
lsof -i tcp                            # TCP connections only
lsof -i udp                            # UDP connections only
lsof -i @192.168.1.100                 # Connections to specific IP

# DevOps troubleshooting
lsof +D /var/log                       # Recursively show directory usage
lsof | grep deleted                    # Find deleted files still open
lsof -i :443 | grep LISTEN             # Who's listening on HTTPS port
```

#### ltrace - Library Call Tracer

```bash
# Basic ltrace usage
ltrace ls                              # Trace library calls
ltrace -p 1234                         # Attach to running process
ltrace -c ls                           # Count library calls
ltrace -e malloc,free program          # Trace specific functions

# Memory debugging
ltrace -e malloc,free,realloc program  # Memory allocation calls
ltrace -S program                      # Include system calls
```

### Performance Analysis Tools

#### perf - Linux Profiler

```bash
# Performance counters
perf list                              # List available events
perf stat ls                           # Basic performance stats
perf stat -e cycles,instructions ls    # Specific counters

# CPU profiling
perf top                               # Real-time profiling
perf top -p 1234                       # Profile specific process
perf record -g ./program               # Record with call graphs
perf report                            # Analyze recorded data

# Advanced profiling
perf record -e cycles -g -p 1234 sleep 10 # Profile for 10 seconds
perf script | head -100                # Raw profiling data
perf annotate function_name            # Annotate function
```

#### System Resource Monitoring

```bash
# iotop - I/O usage by process
iotop                                  # Interactive I/O monitor
iotop -o                               # Only processes doing I/O
iotop -a                               # Accumulated I/O usage
iotop -P                               # Show processes, not threads

# dstat - Comprehensive system stats
dstat                                  # Basic system stats
dstat -cdngy                           # CPU, disk, network, memory
dstat --top-cpu --top-mem              # Top consumers
dstat --output /tmp/stats.csv          # CSV output

# nmon - System monitor
nmon                                   # Interactive system monitor
# Press keys for different views:
# c - CPU, m - Memory, d - Disk, n - Network
```

### Hardware Information and Diagnostics

#### Hardware Discovery Commands

```bash
# CPU information
lscpu                                  # CPU details
cat /proc/cpuinfo                      # Detailed CPU info
nproc                                  # Number of CPU cores
lscpu | grep -E 'Model name|Socket|Core|Thread'

# Memory information
lsmem                                  # Memory ranges and blocks
dmidecode -t memory                    # Memory modules info
free -h                                # Memory usage
cat /proc/meminfo                      # Detailed memory info

# Storage information
lsblk                                  # Block devices tree
lsblk -f                               # Include filesystem info
fdisk -l                               # Partition tables
blkid                                  # Block device attributes

# PCI devices
lspci                                  # PCI devices
lspci -v                               # Verbose PCI info
lspci | grep -i network                # Network cards only

# USB devices
lsusb                                  # USB devices
lsusb -v                               # Verbose USB info

# Complete hardware summary
dmidecode                              # DMI/SMBIOS info
dmidecode -t system                    # System information
dmidecode -t baseboard                 # Motherboard info
dmidecode -t chassis                   # Chassis info
```

#### System Health Monitoring

```bash
# Temperature monitoring
sensors                                # Hardware sensors
watch -n 2 sensors                     # Continuous monitoring

# Disk health
smartctl -a /dev/sda                   # SMART data for disk
smartctl -t short /dev/sda             # Run short self-test
smartctl -l selftest /dev/sda          # View test results

# System uptime and load
uptime                                 # System uptime and load
w                                      # Who is logged in and load
cat /proc/loadavg                      # Load average details
```

### Crash Analysis and Core Dumps

#### Core Dump Management

```bash
# Enable core dumps
ulimit -c unlimited                    # Current shell
echo 'ulimit -c unlimited' >> ~/.bashrc # Permanent for user

# System-wide core dump settings
# /etc/security/limits.conf
* soft core unlimited
* hard core unlimited

# Core dump pattern
echo '/tmp/core.%e.%p' > /proc/sys/kernel/core_pattern
# %e - executable name, %p - PID, %t - timestamp

# Analyze core dumps with gdb
gdb program core.file                  # Load program and core
(gdb) bt                              # Backtrace
(gdb) info registers                  # Register contents
(gdb) print variable_name             # Variable values
```

#### Memory Analysis

```bash
# Out of Memory (OOM) killer analysis
dmesg | grep -i "killed process"       # OOM killer messages
grep -i "out of memory" /var/log/messages
journalctl | grep -i oom               # OOM events in journal

# Memory leak detection
valgrind --leak-check=full ./program   # Memory leak detection
valgrind --tool=massif ./program       # Memory profiling

# /proc/sys/vm tuning for OOM
echo 2 > /proc/sys/vm/overcommit_memory # Always overcommit
echo 80 > /proc/sys/vm/overcommit_ratio # Overcommit ratio
```

### Network Troubleshooting

#### Network Connectivity Debugging

```bash
# Basic connectivity tests
ping -c 4 8.8.8.8                     # Test internet connectivity
ping -c 4 gateway                     # Test gateway connectivity
ping6 -c 4 ipv6.google.com            # IPv6 connectivity

# Advanced ping options
ping -I eth0 8.8.8.8                  # Use specific interface
ping -s 1472 8.8.8.8                  # Test MTU (1500 - 28 = 1472)
ping -f 8.8.8.8                       # Flood ping (root only)

# Traceroute variations
traceroute 8.8.8.8                    # UDP traceroute (default)
traceroute -I 8.8.8.8                 # ICMP traceroute
traceroute -T -p 80 google.com        # TCP traceroute to port 80
mtr google.com                         # My TraceRoute (continuous)
```

#### Port and Service Testing

```bash
# Port connectivity testing
nc -zv google.com 80                  # Test if port is open
nc -zv -w 5 server 22                 # 5-second timeout
nc -u -zv server 53                   # UDP port test

# Service banner grabbing
nc google.com 80 << EOF                # HTTP request
GET / HTTP/1.1
Host: google.com

EOF

# Telnet for protocol testing
telnet smtp.gmail.com 587              # SMTP connection
telnet pop.gmail.com 995               # POP3 connection
telnet imap.gmail.com 993              # IMAP connection
```

#### Network Interface Debugging

```bash
# Interface statistics
cat /proc/net/dev                      # Network interface stats
ip -s link show                       # Interface statistics
ethtool eth0                          # Ethernet tool info
ethtool -S eth0                       # Interface statistics

# Packet capture
tcpdump -i eth0                       # Capture on interface
tcpdump -i eth0 port 80               # HTTP traffic only
tcpdump -i eth0 -w capture.pcap       # Save to file
tcpdump -r capture.pcap               # Read from file

# Advanced tcpdump filters
tcpdump 'host 192.168.1.100'         # Specific host
tcpdump 'net 192.168.1.0/24'         # Network range
tcpdump 'port 53 or port 80'         # Multiple ports
tcpdump 'tcp[tcpflags] & (tcp-syn) != 0' # SYN packets only
```

---

## 🔐 SSH & Remote Access

### SSH Client Configuration

#### SSH Client Basics

```bash
# Basic SSH connection
ssh user@hostname                      # Connect with username
ssh -p 2222 user@hostname             # Custom port
ssh -i ~/.ssh/custom_key user@host     # Specific key file
ssh -X user@hostname                   # X11 forwarding
ssh -A user@hostname                   # Agent forwarding

# SSH with command execution
ssh user@host 'uptime'                 # Execute single command
ssh user@host 'cd /var/log && tail -f messages' # Complex command
ssh user@host << 'EOF'                 # Multiple commands
uptime
df -h
free -m
EOF
```

#### Advanced SSH Client Configuration (~/.ssh/config)

```bash
# ~/.ssh/config structure
Host production
    HostName prod.example.com
    User deploy
    Port 2222
    IdentityFile ~/.ssh/prod_key
    IdentitiesOnly yes
    ServerAliveInterval 60
    ServerAliveCountMax 3
    
Host staging
    HostName staging.example.com
    User developer
    IdentityFile ~/.ssh/dev_key
    LocalForward 3306 localhost:3306    # Port forwarding
    
Host jump-box
    HostName jump.example.com
    User admin
    IdentityFile ~/.ssh/jump_key
    
# Jump through bastion host
Host internal-*
    ProxyJump jump-box
    User developer
    IdentityFile ~/.ssh/internal_key
    
# Wildcard patterns
Host *.example.com
    User myuser
    IdentityFile ~/.ssh/company_key
    
# Global defaults
Host *
    ServerAliveInterval 60
    ServerAliveCountMax 3
    HashKnownHosts yes
    VisualHostKey yes
    ControlMaster auto
    ControlPath ~/.ssh/master-%r@%h:%p
    ControlPersist 10m
```

### SSH Key Management

#### SSH Key Types and Generation

```bash
# RSA keys (traditional, widely supported)
ssh-keygen -t rsa -b 4096 -C "your.email@example.com"
ssh-keygen -t rsa -b 4096 -f ~/.ssh/production_key -N ""

# Ed25519 keys (modern, more secure, smaller)
ssh-keygen -t ed25519 -C "your.email@example.com"
ssh-keygen -t ed25519 -f ~/.ssh/ed25519_key

# ECDSA keys (elliptic curve)
ssh-keygen -t ecdsa -b 521 -C "your.email@example.com"

# Key fingerprints and validation
ssh-keygen -lf ~/.ssh/id_rsa.pub       # Show fingerprint
ssh-keygen -lf ~/.ssh/id_rsa.pub -E md5 # MD5 fingerprint
ssh-keygen -R hostname                 # Remove host from known_hosts
```

#### SSH Agent Management

```bash
# Start SSH agent
eval $(ssh-agent)                      # Start agent and set environment
ssh-agent bash                         # Start new shell with agent

# Add keys to agent
ssh-add ~/.ssh/id_rsa                  # Add default key
ssh-add ~/.ssh/production_key          # Add specific key
ssh-add -l                             # List loaded keys
ssh-add -D                             # Remove all keys
ssh-add -d ~/.ssh/id_rsa               # Remove specific key

# Agent forwarding
ssh -A user@hostname                   # Forward agent
# In ~/.ssh/config:
ForwardAgent yes

# Persistent agent (add to ~/.bashrc)
if [ -z "$SSH_AGENT_PID" ]; then
    eval $(ssh-agent -s)
    ssh-add ~/.ssh/id_rsa
fi
```

### SSH Server Configuration

#### SSH Server Security Hardening (/etc/ssh/sshd_config)

```bash
# Basic security settings
Port 2222                              # Change default port
PermitRootLogin no                     # Disable root login
PasswordAuthentication no              # Disable password auth
PubkeyAuthentication yes               # Enable key-based auth
AuthorizedKeysFile .ssh/authorized_keys # Key file location

# User and group restrictions
AllowUsers deploy developer            # Only allow specific users
AllowGroups ssh-users                  # Only allow specific groups
DenyUsers baduser                      # Deny specific users

# Connection limits
MaxAuthTries 3                         # Max authentication attempts
MaxSessions 2                          # Max concurrent sessions
ClientAliveInterval 300                # Keep-alive interval
ClientAliveCountMax 2                  # Max keep-alive failures
LoginGraceTime 60                      # Time to complete login

# Protocol and encryption
Protocol 2                             # Use SSH protocol 2 only
Ciphers aes256-ctr,aes192-ctr,aes128-ctr
MACs hmac-sha2-256,hmac-sha2-512
KexAlgorithms diffie-hellman-group14-sha256

# Logging
LogLevel VERBOSE                       # Detailed logging
SyslogFacility AUTH                    # Log facility

# Apply configuration
systemctl restart sshd                 # Restart SSH daemon
systemctl reload sshd                  # Reload config without dropping connections
```

#### SSH Access Control

```bash
# Authorized keys management (~/.ssh/authorized_keys)
# Key format: key-type key-data comment [options]
ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQ... user@hostname

# Key options (restrict access)
command="/usr/local/bin/backup.sh" ssh-rsa AAAAB3... # Force command
from="192.168.1.0/24" ssh-rsa AAAAB3...            # IP restriction
no-port-forwarding ssh-rsa AAAAB3...               # Disable port forwarding
no-X11-forwarding ssh-rsa AAAAB3...                # Disable X11 forwarding

# File permissions (critical for security)
chmod 700 ~/.ssh                       # SSH directory
chmod 600 ~/.ssh/authorized_keys       # Authorized keys file
chmod 600 ~/.ssh/id_rsa                # Private key
chmod 644 ~/.ssh/id_rsa.pub            # Public key
chmod 644 ~/.ssh/known_hosts           # Known hosts file
```

### File Transfer Tools

#### SCP - Secure Copy

```bash
# Basic file copying
scp file.txt user@host:/path/          # Copy file to remote
scp user@host:/path/file.txt .         # Copy file from remote
scp -r directory/ user@host:/path/     # Recursive copy

# Advanced SCP options
scp -P 2222 file.txt user@host:/path/  # Custom port
scp -i ~/.ssh/key file.txt user@host:/ # Specific key
scp -C file.txt user@host:/path/       # Compression
scp -p file.txt user@host:/path/       # Preserve attributes

# Through jump host
scp -o "ProxyJump jump-host" file.txt user@internal-host:/path/
```

#### rsync - Advanced File Synchronization

```bash
# Basic rsync usage
rsync -av source/ destination/         # Archive mode, verbose
rsync -av --delete source/ dest/       # Delete extra files in dest
rsync -avz source/ user@host:dest/     # With compression

# Useful rsync options
rsync -av --progress source/ dest/     # Show progress
rsync -av --exclude='*.log' src/ dest/ # Exclude patterns
rsync -av --include='*.txt' --exclude='*' src/ dest/ # Include only .txt
rsync -av --dry-run src/ dest/         # Test run without changes

# DevOps backup patterns
rsync -av --delete --backup --backup-dir=/backup/$(date +%Y%m%d) \
    /var/www/ user@backup-server:/backups/www/

# Incremental backups
rsync -av --link-dest=/backup/previous /source/ /backup/current/

# Remote to remote via local
rsync -av host1:path/ host2:path/      # Transfer between remote hosts

# Resume interrupted transfers
rsync -av --partial --progress large-file user@host:/path/
```

#### SFTP - Secure File Transfer Protocol

```bash
# Interactive SFTP session
sftp user@hostname                     # Connect to SFTP server
sftp -P 2222 user@hostname            # Custom port

# SFTP commands (in session)
ls                                     # List remote directory
lls                                    # List local directory
pwd                                    # Show remote directory
lpwd                                   # Show local directory
cd /path                               # Change remote directory
lcd /path                              # Change local directory
get file.txt                           # Download file
put file.txt                           # Upload file
get -r directory/                      # Download directory
put -r directory/                      # Upload directory

# Batch SFTP operations
sftp -b commands.txt user@host         # Execute batch commands
# commands.txt content:
# cd /var/log
# get *.log
# quit
```

### SSH Tunneling and Port Forwarding

#### Local Port Forwarding

```bash
# Forward local port to remote
ssh -L 8080:localhost:80 user@host     # Local 8080 -> remote 80
ssh -L 3306:db-server:3306 user@jump-host # Access DB through jump host
ssh -L 0.0.0.0:8080:localhost:80 user@host # Bind to all interfaces

# Access forwarded services
curl http://localhost:8080             # Access remote web service
mysql -h 127.0.0.1 -P 3306 -u user -p # Access remote database
```

#### Remote Port Forwarding

```bash
# Forward remote port to local
ssh -R 9000:localhost:8080 user@host   # Remote 9000 -> local 8080
ssh -R 80:localhost:3000 user@public-server # Expose local dev server

# Reverse tunnel for access to internal services
ssh -R 2222:internal-host:22 user@public-server
# Then from public server: ssh -p 2222 user@localhost
```

#### Dynamic Port Forwarding (SOCKS Proxy)

```bash
# Create SOCKS proxy
ssh -D 1080 user@host                  # SOCKS proxy on port 1080
ssh -D 127.0.0.1:1080 user@host       # Bind to localhost only

# Use SOCKS proxy
curl --socks5 localhost:1080 http://internal-site.com
# Configure browser to use SOCKS5 proxy: localhost:1080
```

#### SSH Multiplexing

```bash
# Control master configuration (in ~/.ssh/config)
Host *
    ControlMaster auto
    ControlPath ~/.ssh/master-%r@%h:%p
    ControlPersist 10m

# Manual multiplexing
ssh -M -S ~/.ssh/control-socket user@host # Master connection
ssh -S ~/.ssh/control-socket user@host    # Use existing connection

# Control commands
ssh -O check user@host                 # Check connection status
ssh -O exit user@host                  # Close master connection
```

---

## 📦 Storage Management

### Disk Partitioning

#### fdisk - Traditional Partitioning

```bash
# List all disks and partitions
fdisk -l                               # List all disks
fdisk -l /dev/sda                      # Specific disk

# Interactive partitioning
fdisk /dev/sdb                         # Enter fdisk for /dev/sdb
# Interactive commands:
# p - print partition table
# n - new partition
# d - delete partition
# t - change partition type
# w - write changes and exit
# q - quit without saving

# Create new partition example
fdisk /dev/sdb << EOF
n
p
1


t
83
w
EOF
```

#### parted - Advanced Partitioning

```bash
# Non-interactive partition creation
parted /dev/sdb mklabel gpt            # Create GPT partition table
parted /dev/sdb mkpart primary ext4 0% 100% # Create partition using full disk
parted /dev/sdb mkpart data ext4 1GiB 10GiB # Create 9GB partition

# Interactive mode
parted /dev/sdb                        # Enter parted
# Commands:
# print - show partition table
# mklabel gpt - create GPT table
# mkpart name fs-type start end - create partition
# resizepart number end - resize partition
# rm number - delete partition

# Resize partition
parted /dev/sdb resizepart 1 20GiB     # Resize partition 1 to 20GB
```

#### GPT vs MBR Partitioning

```bash
# MBR limitations:
# - Maximum 4 primary partitions
# - Maximum 2TB disk size
# - Uses 32-bit LBA addressing

# GPT advantages:
# - Up to 128 partitions
# - Supports disks > 2TB
# - 64-bit LBA addressing
# - Backup partition table

# Convert MBR to GPT (data loss!)
parted /dev/sdb mklabel gpt            # Warning: destroys existing data

# Show partition table type
parted /dev/sdb print | grep "Partition Table"
```

### Filesystem Management

#### Filesystem Creation

```bash
# ext4 filesystem
mkfs.ext4 /dev/sdb1                    # Basic ext4
mkfs.ext4 -L DataDrive /dev/sdb1       # With label
mkfs.ext4 -b 4096 -i 16384 /dev/sdb1   # Custom block/inode ratio

# XFS filesystem (better for large files)
mkfs.xfs /dev/sdb1                     # Basic XFS
mkfs.xfs -L "Data" /dev/sdb1           # With label
mkfs.xfs -f /dev/sdb1                  # Force creation

# Btrfs filesystem (copy-on-write, snapshots)
mkfs.btrfs /dev/sdb1                   # Single device
mkfs.btrfs -L "Storage" /dev/sdb1 /dev/sdc1 # RAID across devices

# FAT32 (for compatibility)
mkfs.fat -F 32 /dev/sdb1               # FAT32 filesystem

# Check filesystem type
file -s /dev/sdb1                      # Show filesystem info
blkid /dev/sdb1                        # Show UUID and type
lsblk -f                               # All filesystems
```

#### Filesystem Tuning and Maintenance

```bash
# ext4 tuning
tune2fs -l /dev/sdb1                   # Show filesystem info
tune2fs -L "NewLabel" /dev/sdb1        # Change label
tune2fs -c 30 /dev/sdb1                # Set max mount count
tune2fs -i 180d /dev/sdb1              # Set check interval (180 days)
tune2fs -m 1 /dev/sdb1                 # Set reserved blocks (1%)

# Filesystem checking
fsck /dev/sdb1                         # Generic filesystem check
fsck.ext4 -f /dev/sdb1                 # Force ext4 check
xfs_repair /dev/sdb1                   # XFS repair
btrfs check /dev/sdb1                  # Btrfs check

# Online filesystem operations
resize2fs /dev/sdb1                    # Resize ext4 to partition size
xfs_growfs /mount/point                # Grow XFS filesystem
```

### LVM (Logical Volume Management)

#### LVM Concepts and Setup

```bash
# LVM hierarchy: Physical Volumes -> Volume Groups -> Logical Volumes

# Create Physical Volumes
pvcreate /dev/sdb1 /dev/sdc1           # Initialize PVs
pvdisplay                              # Show PV information
pvs                                    # Brief PV status

# Create Volume Group
vgcreate data_vg /dev/sdb1 /dev/sdc1   # Create VG from PVs
vgdisplay data_vg                      # Show VG information
vgs                                    # Brief VG status

# Create Logical Volumes
lvcreate -L 10G -n web_lv data_vg      # Create 10GB LV
lvcreate -l 100%FREE -n storage_lv data_vg # Use all remaining space
lvdisplay                              # Show LV information
lvs                                    # Brief LV status

# Create filesystem on LV
mkfs.ext4 /dev/data_vg/web_lv          # Create filesystem
mkdir /var/www                         # Create mount point
mount /dev/data_vg/web_lv /var/www     # Mount LV
```

#### LVM Operations and Management

```bash
# Extend Volume Group
pvcreate /dev/sdd1                     # Initialize new PV
vgextend data_vg /dev/sdd1             # Add PV to VG

# Extend Logical Volume
lvextend -L +5G /dev/data_vg/web_lv    # Add 5GB
lvextend -l +100%FREE /dev/data_vg/web_lv # Use all free space
resize2fs /dev/data_vg/web_lv          # Resize ext4 filesystem

# Reduce Logical Volume (ext4 only, risky!)
umount /var/www                        # Must unmount first
e2fsck -f /dev/data_vg/web_lv          # Check filesystem
resize2fs /dev/data_vg/web_lv 8G       # Shrink filesystem first
lvreduce -L 8G /dev/data_vg/web_lv     # Then reduce LV
mount /dev/data_vg/web_lv /var/www     # Remount

# Remove LVM components
umount /var/www                        # Unmount LV
lvremove /dev/data_vg/web_lv           # Remove LV
vgremove data_vg                       # Remove VG
pvremove /dev/sdb1                     # Remove PV
```

#### LVM Snapshots

```bash
# Create snapshot
lvcreate -L 2G -s -n web_backup /dev/data_vg/web_lv # 2GB snapshot

# Mount snapshot (read-only backup)
mkdir /mnt/snapshot
mount -o ro /dev/data_vg/web_backup /mnt/snapshot

# Merge snapshot (revert changes)
umount /var/www                        # Unmount original
umount /mnt/snapshot                   # Unmount snapshot
lvconvert --merge /dev/data_vg/web_backup # Merge changes back

# Remove snapshot
lvremove /dev/data_vg/web_backup       # Delete snapshot
```

### Advanced Storage Concepts

#### Software RAID with mdadm

```bash
# Create RAID arrays
mdadm --create /dev/md0 --level=1 --raid-devices=2 /dev/sdb1 /dev/sdc1 # RAID 1
mdadm --create /dev/md1 --level=5 --raid-devices=3 /dev/sdd1 /dev/sde1 /dev/sdf1 # RAID 5

# Monitor RAID status
cat /proc/mdstat                       # RAID status
mdadm --detail /dev/md0                # Detailed RAID info

# RAID management
mdadm --add /dev/md0 /dev/sdg1         # Add spare disk
mdadm --fail /dev/md0 /dev/sdb1        # Mark disk as failed
mdadm --remove /dev/md0 /dev/sdb1      # Remove failed disk

# Save RAID configuration
mdadm --detail --scan >> /etc/mdadm/mdadm.conf
update-initramfs -u                    # Update initramfs
```

#### File Permissions and ACLs

```bash
# Extended ACLs (Access Control Lists)
getfacl /path/to/file                  # Show ACL permissions
setfacl -m u:user:rwx /path/to/file    # Grant user permissions
setfacl -m g:group:rw /path/to/file    # Grant group permissions
setfacl -m o::r /path/to/file          # Set other permissions

# Default ACLs for directories
setfacl -d -m u:www-data:rwx /var/www  # Default ACL for new files
setfacl -x u:user /path/to/file        # Remove user ACL
setfacl -b /path/to/file               # Remove all ACLs

# Recursive ACL operations
setfacl -R -m u:deploy:rwx /opt/app    # Recursive ACL setting
```

---

## 🧠 Advanced Topics

### Kernel Tuning and sysctl

#### System Performance Tuning

```bash
# View current kernel parameters
sysctl -a                              # All parameters
sysctl vm.swappiness                   # Specific parameter
sysctl net.ipv4.ip_forward             # IP forwarding status

# Temporary parameter changes
sysctl vm.swappiness=10                # Reduce swap usage
sys profiles
ufw app list                           # List available profiles
ufw allow 'Apache Full'                # Allow Apache HTTP/HTTPS
ufw allow 'OpenSSH'                    # Allow OpenSSH

# Status and logging
ufw status verbose                     # Detailed status
ufw logging on                         # Enable logging
```

### firewalld - Dynamic Firewall Management

#### firewalld Basics

```bash
# Service management
systemctl start firewalld
systemctl enable firewalld
firewall-cmd --state                   # Check if running

# Zone management
firewall-cmd --get-default-zone        # Show default zone
firewall-cmd --list-all-zones          # List all zones
firewall-cmd --set-default-zone=public # Set default zone
firewall-cmd --get-active-zones        # Show active zones

# Service management
firewall-cmd --list-services           # List allowed services
firewall-cmd --add-service=http        # Allow HTTP (temporary)
firewall-cmd --add-service=http --permanent  # Allow HTTP (permanent)
firewall-cmd --reload                  # Apply permanent changes

# Port management
firewall-cmd --add-port=8080/tcp --permanent
firewall-cmd --list-ports              # List open ports
firewall-cmd --remove-port=8080/tcp --permanent
```

### SELinux and AppArmor Basics

#### SELinux Management

```bash
# SELinux status
getenforce                             # Current mode (Enforcing/Permissive/Disabled)
sestatus                               # Detailed status
setenforce 0                           # Set to permissive (temporary)
setenforce 1                           # Set to enforcing (temporary)

# File contexts
ls -Z /var/www/html                    # Show SELinux contexts
restorecon -Rv /var/www/html           # Restore default contexts
chcon -t httpd_exec_t /path/to/cgi     # Change context type

# SELinux booleans
getsebool -a                           # List all booleans
setsebool httpd_can_network_connect on # Allow Apache network connections
setsebool -P httpd_enable_homedirs on  # Make permanent with -P

# Troubleshooting
ausearch -m avc -ts recent             # Recent SELinux denials
audit2allow -w -a                      # Analyze audit logs
```

#### AppArmor Basics

```bash
# AppArmor status
aa-status                              # Show loaded profiles
aa-enabled                             # Check if AppArmor is enabled

# Profile management
aa-enforce /etc/apparmor.d/usr.bin.nginx    # Enforce profile
aa-complain /etc/apparmor.d/usr.bin.nginx   # Set to complain mode
aa-disable /etc/apparmor.d/usr.bin.nginx    # Disable profile

# Profile development
aa-genprof nginx                       # Generate profile for nginx
aa-logprof                             # Update profiles from logs
```

---

## 🔐 Users & Permissions

### User Management

#### User Account Operations

```bash
# Create users
useradd -m -s /bin/bash username       # Create with home directory
useradd -m -G sudo,docker username     # Add to groups during creation
useradd -r -s /bin/false serviceuser   # System user for services

# Modify users
usermod -aG sudo username              # Add to sudo group
usermod -s /bin/zsh username           # Change shell
usermod -d /new/home -m username       # Move home directory
usermod -L username                    # Lock account
usermod -U username                    # Unlock account

# Delete users
userdel username                       # Delete user (keep home)
userdel -r username                    # Delete user and home directory

# Password management
passwd username                        # Set password
chage -l username                      # View password aging info
chage -E 2024-12-31 username          # Set account expiration
passwd -e username                     # Force password change on next login
```

#### Group Management

```bash
# Group operations
groupadd developers                    # Create group
groupmod -n newname oldname            # Rename group
groupdel groupname                     # Delete group

# Group membership
groups username                        # Show user's groups
id username                            # Detailed user info
newgrp groupname                       # Switch primary group temporarily

# Add/remove from groups
gpasswd -a username groupname          # Add user to group
gpasswd -d username groupname          # Remove user from group
```

### Sudo Configuration

#### /etc/sudoers Management

```bash
# Edit sudoers safely
visudo                                 # Opens with syntax checking

# Basic sudoers syntax
# user    host=(runas) commands
root     ALL=(ALL:ALL) ALL
%sudo    ALL=(ALL:ALL) ALL
username ALL=(ALL) NOPASSWD: ALL

# DevOps-specific examples
deploy   ALL=(ALL) NOPASSWD: /bin/systemctl restart nginx
monitor  ALL=(ALL) NOPASSWD: /usr/bin/tail -f /var/log/*
backup   ALL=(ALL) NOPASSWD: /bin/tar, /bin/rsync
```

#### Sudoers Drop-in Files

```bash
# Create specific files in /etc/sudoers.d/
echo "deploy ALL=(ALL) NOPASSWD: /bin/systemctl restart myapp" > /etc/sudoers.d/deploy
echo "nagios ALL=(ALL) NOPASSWD: /usr/lib/nagios/plugins/*" > /etc/sudoers.d/nagios

# Verify syntax
visudo -c -f /etc/sudoers.d/deploy
```

### Authentication Systems

#### PAM (Pluggable Authentication Modules)

```bash
# PAM configuration files in /etc/pam.d/
ls /etc/pam.d/                         # List PAM configs

# Common PAM modules
# /etc/pam.d/common-auth    - Authentication
# /etc/pam.d/common-account - Account verification
# /etc/pam.d/common-session - Session setup
# /etc/pam.d/common-password - Password changing

# Example: Enforce strong passwords
# In /etc/pam.d/common-password:
# password requisite pam_pwquality.so retry=3 minlen=12 ucredit=-1 lcredit=-1 dcredit=-1
```

#### Login Shells and Environment

##### Shell Configuration Files

```bash
# System-wide configurations
/etc/profile                           # System-wide environment
/etc/bash.bashrc                       # System-wide bash settings
/etc/environment                       # Environment variables

# User-specific configurations
~/.profile                             # Executed for login shells
~/.bashrc                              # Executed for interactive shells
~/.bash_profile                        # Login shells (overrides .profile)
~/.bash_logout                         # Executed on logout

# DevOps environment setup example
cat << 'EOF' >> ~/.bashrc
# DevOps aliases
alias ll='ls -la'
alias grep='grep --color=auto'
alias k='kubectl'
alias d='docker'

# Environment variables
export EDITOR=vim
export PATH=$PATH:/opt/scripts
export KUBECONFIG=~/.kube/config

# Functions
function aws-profile() {
    export AWS_PROFILE=$1
    echo "AWS profile set to: $1"
}
EOF
```

### SSH Key Management

#### SSH Key Generation and Management

```bash
# Generate SSH keys
ssh-keygen -t rsa -b 4096 -C "your.email@example.com"
ssh-keygen -t ed25519 -C "your.email@example.com"  # More secure
ssh-keygen -t rsa -b 4096 -f ~/.ssh/deploy_key -N ""  # No passphrase

# Copy public keys
ssh-copy-id user@server                # Copy default key
ssh-copy-id -i ~/.ssh/custom_key.pub user@server

# Manual key installation
cat ~/.ssh/id_rsa.pub >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
chmod 700 ~/.ssh
```

#### SSH Configuration

```bash
# ~/.ssh/config for client configuration
Host production
    HostName prod.example.com
    User deploy
    IdentityFile ~/.ssh/prod_key
    Port 2222
    
Host jump-host
    HostName jump.example.com
    User admin
    IdentityFile ~/.ssh/jump_key
    
Host internal-*
    ProxyJump jump-host
    User developer
    IdentityFile ~/.ssh/dev_key

# SSH agent for key management
ssh-agent bash                         # Start SSH agent
ssh-add ~/.ssh/id_rsa                  # Add key to agent
ssh-add -l                             # List loaded keys
ssh-add -D                             # Remove all keys
```

---

## 🧩 Package Management

## Debian-based Systems (apt)

### APT Package Management

```bash
# Update package database
apt update                             # Update package list
apt upgrade                            # Upgrade packages
apt full-upgrade                       # Upgrade with dependency resolution
apt dist-upgrade                       # Distribution upgrade

# Package installation and removal
apt install package1 package2         # Install packages
apt install package=version           # Install specific version
apt remove package                     # Remove package (keep config)
apt purge package                      # Remove package and config
apt autoremove                         # Remove orphaned packages

# Package information
apt search keyword                     # Search packages
apt show package                       # Show package information
apt list --installed                   # List installed packages
apt list --upgradable                  # List upgradable packages
```

### Advanced APT Operations

```bash
# Hold packages (prevent upgrades)
apt-mark hold package                  # Hold package
apt-mark unhold package                # Unhold package
apt-mark showhold                      # Show held packages

# Repository management
add-apt-repository ppa:user/repo       # Add PPA repository
add-apt-repository --remove ppa:user/repo  # Remove PPA
apt-key add keyfile                    # Add repository key (deprecated)

# APT configuration files
/etc/apt/sources.list                  # Main repository list
/etc/apt/sources.list.d/               # Additional repository files
/etc/apt/preferences.d/                # Package preferences
```

### dpkg - Low-level Package Management

```bash
# Package installation from .deb files
dpkg -i package.deb                    # Install package
dpkg -r package                        # Remove package
dpkg -P package                        # Purge package

# Package information
dpkg -l                                # List installed packages
dpkg -L package                        # List files in package
dpkg -S filename                       # Find package owning file
dpkg --get-selections                  # Show package selections

# Fix broken packages
dpkg --configure -a                    # Configure unconfigured packages
apt-get -f install                     # Fix broken dependencies
```

## RHEL-based Systems

### YUM Package Management

```bash
# Package operations
yum update                             # Update all packages
yum install package                    # Install package
yum remove package                     # Remove package
yum group install "Development Tools"  # Install package group

# Package information
yum search keyword                     # Search packages
yum info package                       # Package information
yum list installed                     # List installed packages
yum list available                     # List available packages
yum provides filename                  # Find package providing file

# Repository management
yum repolist                           # List repositories
yum-config-manager --add-repo url      # Add repository
yum-config-manager --disable repo      # Disable repository
```

### DNF Package Management (Fedora/RHEL 8+)

```bash
# Basic operations (similar to yum)
dnf update                             # Update packages
dnf install package                    # Install package
dnf remove package                     # Remove package
dnf autoremove                         # Remove orphaned packages

# Advanced operations
dnf history                            # Show transaction history
dnf history undo ID                    # Undo transaction
dnf mark install package               # Mark as user-installed
dnf module list                        # List available modules
dnf module install nodejs:14          # Install specific module stream
```

### RPM - Low-level Package Management

```bash
# Package installation
rpm -ivh package.rpm                   # Install package (verbose)
rpm -Uvh package.rpm                   # Upgrade package
rpm -e package                         # Remove package

# Package queries
rpm -qa                                # List all installed packages
rpm -ql package                        # List files in package
rpm -qf filename                       # Find package owning file
rpm -qi package                        # Package information
rpm -V package                         # Verify package integrity
```

---

## 🛠️ Shell Scripting (Bash)

### Variables and Environment

#### Variable Declaration and Usage

```bash
#!/bin/bash

# Variable assignment (no spaces around =)
name="John Doe"
age=30
readonly PI=3.14159                    # Read-only variable
declare -i counter=0                   # Integer variable
declare -a array=("item1" "item2")    # Array declaration

# Variable expansion
echo "Hello, $name"                    # Basic expansion
echo "Hello, ${name}"                  # Explicit expansion
echo "Age: ${age:-25}"                 # Default value if unset
echo "Length: ${#name}"                # String length

# Environment variables
export PATH="$PATH:/opt/bin"           # Add to PATH
export DB_PASSWORD="secret123"        # Export for child processes
env | grep DB_                         # Show environment variables

# Special variables
echo "Script name: $0"                # Script name
echo "First argument: $1"             # First argument
echo "All arguments: $@"              # All arguments as array
echo "Number of arguments: $#"         # Argument count
echo "Exit status: $?"                # Last command exit status
echo "Process ID: $"                 # Current process ID
```

#### Quoting Rules

```bash
# Single quotes - literal (no expansion)
echo 'Price: $10'                     # Output: Price: $10

# Double quotes - allow expansion
price=10
echo "Price: $price"                   # Output: Price: 10

# No quotes - word splitting occurs
files=$(ls *.txt)
echo $files                           # May break with spaces in filenames
echo "$files"                         # Preserves formatting

# DevOps best practice - always quote variables
if [ -n "$variable" ]; then
    echo "Variable is set"
fi
```

### Control Structures

#### Conditional Statements

```bash
#!/bin/bash

# if-then-else
if [ "$1" = "start" ]; then
    echo "Starting service..."
    systemctl start myservice
elif [ "$1" = "stop" ]; then
    echo "Stopping service..."
    systemctl stop myservice
else
    echo "Usage: $0 {start|stop}"
    exit 1
fi

# Modern conditional syntax [[ ]]
if [[ $USER == "root" ]]; then
    echo "Running as root"
fi

# Pattern matching
if [[ $filename == *.log ]]; then
    echo "Log file detected"
fi

# Numeric comparisons
if [[ $age -gt 18 ]]; then
    echo "Adult"
fi

# File tests
if [[ -f "/etc/passwd" ]]; then
    echo "File exists"
fi

if [[ -d "/var/log" ]]; then
    echo "Directory exists"
fi

# Multiple conditions
if [[ -f "$config_file" && -r "$config_file" ]]; then
    source "$config_file"
fi
```

#### Case Statements

```bash
#!/bin/bash

case "$1" in
    start)
        echo "Starting application..."
        ./start_app.sh
        ;;
    stop)
        echo "Stopping application..."
        ./stop_app.sh
        ;;
    restart)
        echo "Restarting application..."
        ./stop_app.sh
        sleep 2
        ./start_app.sh
        ;;
    status)
        if pgrep -f myapp > /dev/null; then
            echo "Application is running"
        else
            echo "Application is not running"
        fi
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status}"
        exit 1
        ;;
esac
```

### Loops

#### For Loops

```bash
#!/bin/bash

# Traditional for loop
for i in {1..10}; do
    echo "Number: $i"
done

# Loop over files
for file in /var/log/*.log; do
    if [[ -f "$file" ]]; then
        echo "Processing $file"
        # Process file
    fi
done

# Loop over command output
for server in $(cat servers.txt); do
    echo "Checking $server"
    ping -c 1 "$server" > /dev/null && echo "$server is up" || echo "$server is down"
done

# C-style for loop
for ((i=0; i<10; i++)); do
    echo "Counter: $i"
done

# Loop over array
servers=("web1" "web2" "db1")
for server in "${servers[@]}"; do
    ssh "$server" "uptime"
done
```

#### While and Until Loops

```bash
#!/bin/bash

# While loop
counter=1
while [[ $counter -le 5 ]]; do
    echo "Attempt $counter"
    ((counter++))
done

# Read file line by line
while IFS= read -r line; do
    echo "Processing: $line"
done < input.txt

# Until loop (opposite of while)
until ping -c 1 google.com > /dev/null; do
    echo "Waiting for network..."
    sleep 5
done

# Infinite loop with break
while true; do
    read -p "Enter command (q to quit): " cmd
    if [[ "$cmd" == "q" ]]; then
        break
    fi
    eval "$cmd"
done
```

### Functions

#### Function Definition and Usage

```bash
#!/bin/bash

# Simple function
greet() {
    echo "Hello, $1!"
}

# Function with local variables
calculate_disk_usage() {
    local path="$1"
    local usage
    
    if [[ ! -d "$path" ]]; then
        echo "Error: Directory $path does not exist" >&2
        return 1
    fi
    
    usage=$(du -sh "$path" | cut -f1)
    echo "Disk usage for $path: $usage"
    return 0
}

# Function with return value
is_service_running() {
    local service_name="$1"
    
    if systemctl is-active --quiet "$service_name"; then
        return 0  # Success
    else
        return 1  # Failure
    fi
}

# Usage examples
greet "DevOps Engineer"
calculate_disk_usage "/var/log"

if is_service_running "nginx"; then
    echo "Nginx is running"
else
    echo "Nginx is not running"
fi
```

#### Advanced Function Features

```bash
#!/bin/bash

# Function with multiple return methods
process_log() {
    local logfile="$1"
    local errors warnings
    
    # Use command substitution for return values
    errors=$(grep -c "ERROR" "$logfile")
    warnings=$(grep -c "WARNING" "$logfile")
    
    # Output structured data
    echo "errors:$errors"
    echo "warnings:$warnings"
}

# Parse function output
log_stats=$(process_log "/var/log/app.log")
error_count=$(echo "$log_stats" | grep "errors:" | cut -d: -f2)
warning_count=$(echo "$log_stats" | grep "warnings:" | cut -d: -f2)

echo "Found $error_count errors and $warning_count warnings"
```

### Error Handling and Best Practices

#### Error Handling Strategies

```bash
#!/bin/bash

# Exit on error
set -e                                 # Exit on any error
set -u                                 # Exit on undefined variable
set -o pipefail                        # Exit on pipe failure

# Combined (recommended for DevOps scripts)
set -euo pipefail

# Trap for cleanup
cleanup() {
    echo "Cleaning up temporary files..."
    rm -f /tmp/script.$.*
    exit
}

trap cleanup EXIT                      # Cleanup on exit
trap cleanup INT TERM                  # Cleanup on interrupt

# Check command success
if ! command -v docker > /dev/null; then
    echo "Error: Docker is not installed" >&2
    exit 1
fi

# Function error handling
deploy_app() {
    local app_path="$1"
    
    # Validate input
    if [[ -z "$app_path" ]]; then
        echo "Error: Application path is required" >&2
        return 1
    fi
    
    if [[ ! -d "$app_path" ]]; then
        echo "Error: Application path does not exist: $app_path" >&2
        return 1
    fi
    
    # Perform deployment
    echo "Deploying application from $app_path"
    # ... deployment logic ...
    
    return 0
}

# Use function with error checking
if deploy_app "/opt/myapp"; then
    echo "Deployment successful"
else
    echo "Deployment failed" >&2
    exit 1
fi
```

#### Return Codes and Exit Status

```bash
#!/bin/bash

# Custom exit codes
readonly SUCCESS=0
readonly ERROR_NO_ARGS=1
readonly ERROR_FILE_NOT_FOUND=2
readonly ERROR_PERMISSION_DENIED=3

# Check previous command
if ! cp source.txt destination.txt; then
    echo "Failed to copy file" >&2
    exit $ERROR_FILE_NOT_FOUND
fi

# Save and check exit status
cp important.txt backup.txt
exit_code=$?
if [[ $exit_code -ne 0 ]]; then
    echo "Backup failed with exit code: $exit_code" >&2
    exit $exit_code
fi
```

### Advanced Scripting Techniques

#### Here Documents and Here Strings

```bash
#!/bin/bash

# Here document for multi-line strings
cat << EOF > config.yaml
server:
  host: ${SERVER_HOST:-localhost}
  port: ${SERVER_PORT:-8080}
database:
  url: ${DB_URL}
  user: ${DB_USER}
EOF

# Here document with command execution
mysql -u root -p << SQL
CREATE DATABASE IF NOT EXISTS myapp;
USE myapp;
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    email VARCHAR(100) NOT NULL
);
SQL

# Here string (single line)
grep pattern <<< "$variable_content"
```

#### Array Operations

```bash
#!/bin/bash

# Array declaration and manipulation
servers=("web1.example.com" "web2.example.com" "db1.example.com")

# Add elements
servers+=("cache1.example.com")

# Access elements
echo "First server: ${servers[0]}"
echo "All servers: ${servers[@]}"
echo "Number of servers: ${#servers[@]}"

# Loop through array
for server in "${servers[@]}"; do
    echo "Checking $server..."
    if ping -c 1 "$server" > /dev/null 2>&1; then
        echo "✓ $server is reachable"
    else
        echo "✗ $server is unreachable"
    fi
done

# Associative arrays (Bash 4+)
declare -A config
config[host]="localhost"
config[port]="8080"
config[debug]="true"

# Access associative array
echo "Host: ${config[host]}"
echo "Port: ${config[port]}"

# Loop through associative array
for key in "${!config[@]}"; do
    echo "$key = ${config[$key]}"
done
```

---

## 🔁 System Boot, Services & Init

### Systemd Service Management

#### Service Control

```bash
# Service status and control
systemctl status nginx                 # Service status
systemctl start nginx                  # Start service
systemctl stop nginx                   # Stop service
systemctl restart nginx                # Restart service
systemctl reload nginx                 # Reload configuration
systemctl enable nginx                 # Enable at boot
systemctl disable nginx                # Disable at boot

# System state
systemctl list-units                   # List active units
systemctl list-units --failed          # List failed units
systemctl list-unit-files              # List all unit files
systemctl get-default                  # Show default target
systemctl set-default multi-user.target # Set default target
```

#### Creating Custom Services

```bash
# Create service file: /etc/systemd/system/myapp.service
cat << 'EOF' > /etc/systemd/system/myapp.service
[Unit]
Description=My Application
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=myapp
Group=myapp
WorkingDirectory=/opt/myapp
ExecStart=/opt/myapp/bin/start.sh
ExecReload=/bin/kill -HUP $MAINPID
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/myapp/data /var/log/myapp

[Install]
WantedBy=multi-user.target
EOF

# Enable and start the service
systemctl daemon-reload                # Reload systemd
systemctl enable myapp                 # Enable at boot
systemctl start myapp                  # Start service
```

#### Systemd Unit Types

```bash
# Service units (.service)
systemctl status nginx.service

# Socket units (.socket) - socket activation
systemctl status docker.socket

# Target units (.target) - grouping units
systemctl status multi-user.target

# Timer units (.timer) - scheduled tasks
systemctl list-timers                  # List active timers
systemctl status logrotate.timer

# Mount units (.mount) - filesystem mounts
systemctl status tmp.mount

# Path units (.path) - path-based activation
systemctl status systemd-ask-password-wall.path
```

### Systemd Timers (Cron Alternative)

#### Creating Timer Units

```bash
# Create timer: /etc/systemd/system/backup.timer
cat << 'EOF' > /etc/systemd/system/backup.timer
[Unit]
Description=Daily Backup Timer
Requires=backup.service

[Timer]
OnCalendar=daily
Persistent=true
RandomizedDelaySec=300

[Install]
WantedBy=timers.target
EOF

# Create corresponding service: /etc/systemd/system/backup.service
cat << 'EOF' > /etc/systemd/system/backup.service
[Unit]
Description=Daily Backup Service

[Service]
Type=oneshot
User=backup
ExecStart=/usr/local/bin/backup.sh
StandardOutput=journal
StandardError=journal
EOF

# Enable and start timer
systemctl daemon-reload
systemctl enable backup.timer
systemctl start backup.timer
systemctl list-timers                  # Verify timer is active
```

#### Timer Scheduling Syntax

```bash
# OnCalendar examples
OnCalendar=minutely                     # Every minute
OnCalendar=hourly                       # Every hour
OnCalendar=daily                        # Every day at midnight
OnCalendar=weekly                       # Every Monday at midnight
OnCalendar=monthly                      # First day of month at midnight
OnCalendar=yearly                       # January 1st at midnight

# Specific times
OnCalendar=*-*-* 02:30:00              # Daily at 2:30 AM
OnCalendar=Mon,Wed,Fri 09:00           # MWF at 9 AM
OnCalendar=*-*-01 00:00:00             # First day of every month

# Multiple schedules
OnCalendar=Mon..Fri 09:00              # Weekdays at 9 AM
OnCalendar=Sat,Sun 10:00               # Weekends at 10 AM
```

### Journal and Logging (journalctl)

#### Basic Journal Operations

```bash
# View logs
journalctl                             # All logs
journalctl -f                          # Follow logs (like tail -f)
journalctl -u nginx                    # Logs for specific service
journalctl -u nginx -f                 # Follow service logs

# Time-based filtering
journalctl --since "2024-01-01"       # Since date
journalctl --since "1 hour ago"       # Since time ago
journalctl --since yesterday           # Since yesterday
journalctl --until "2024-01-31"       # Until date

# Priority filtering
journalctl -p err                      # Error level and above
journalctl -p warning                  # Warning level and above
journalctl -p debug                    # All messages including debug

# Output formatting
journalctl -o json                     # JSON format
journalctl -o json-pretty              # Pretty JSON
journalctl -o cat                      # Just the message
```

#### Advanced Journal Management

```bash
# System information
journalctl --disk-usage                # Journal disk usage
journalctl --vacuum-size=100M          # Limit journal size
journalctl --vacuum-time=30d           # Keep logs for 30 days
journalctl --verify                    # Verify journal integrity

# Persistent logging configuration
# Edit /etc/systemd/journald.conf
Storage=persistent                     # Store logs persistently
SystemMaxUse=1G                        # Maximum disk usage
MaxRetentionSec=30day                  # Maximum retention time
ForwardToSyslog=yes                    # Forward to syslog

# Restart journald to apply changes
systemctl restart systemd-journald
```

### Boot Process Understanding

#### Boot Stages Analysis

```bash
# Analyze boot time
systemd-analyze                        # Overall boot time
systemd-analyze blame                  # Time per service
systemd-analyze critical-chain         # Critical path
systemd-analyze plot > boot.svg        # Generate boot chart

# Service dependencies
systemctl list-dependencies nginx      # Show dependencies
systemctl list-dependencies --reverse nginx  # Show dependents

# Boot messages
dmesg                                  # Kernel messages
dmesg | grep -i error                  # Boot errors
journalctl -b                          # Current boot logs
journalctl -b -1                       # Previous boot logs
```

#### Systemd Targets (Runlevels)

```bash
# Available targets
systemctl list-units --type=target     # List active targets
systemctl list-unit-files --type=target # List all targets

# Common targets
poweroff.target                        # Shutdown (runlevel 0)
rescue.target                          # Single user (runlevel 1)
multi-user.target                      # Multi-user (runlevel 3)
graphical.target                       # GUI (runlevel 5)
reboot.target                          # Reboot (runlevel 6)

# Change targets
systemctl isolate rescue.target        # Switch to rescue mode
systemctl isolate multi-user.target    # Switch to multi-user
systemctl rescue                       # Enter rescue mode
systemctl emergency                    # Enter emergency mode
```

---

## 🔎 Logging & Troubleshooting

### System Logs Analysis

#### Traditional Log Files

bash

```bash
# Important log locations
/var/log/messages                      # General system messages
/var/log/syslog                        # System log (Debian/Ubuntu)
/var/log/auth.log                      # Authentication logs
/var/log/secure                        # Authentication logs (RHEL)
/var/log/kern.log                      # Kernel messages
/var/log/dmesg                         # Boot messages
/var/log/cron                          # Cron job logs
/var/log/mail.log                      # Mail system logs
/var/log/apache2/                      # Apache web server logs
/var/log/nginx/                        # Nginx web server logs
/var/log/mysql/                        # MySQL database logs
/var/log/postgresql/                   # PostgreSQL database logs
```

#### Systemd Journal (journalctl)

bash

```bash
# Basic journal commands
journalctl                             # View all logs
journalctl -f                          # Follow logs in real-time
journalctl -u servicename              # Logs for specific service
journalctl -p err                      # Error priority and above
journalctl --since "2024-01-01"       # Logs since specific date
journalctl --until "1 hour ago"       # Logs until timeframe
journalctl -k                          # Kernel messages only
journalctl --disk-usage               # Check journal disk usage
journalctl --vacuum-size=100M         # Clean up old logs

# Advanced filtering
journalctl _PID=1234                   # Logs from specific PID
journalctl _COMM=sshd                  # Logs from specific command
journalctl -u docker --grep="ERROR"   # Search within service logs
```

#### Log Analysis Tools

bash

```bash
# Text processing for logs
tail -f /var/log/syslog | grep ERROR   # Follow and filter
awk '/ERROR/ {print $1, $2, $9}' /var/log/apache2/access.log
sed -n '/2024-01-01/,/2024-01-02/p' /var/log/messages

# Log rotation management
logrotate -d /etc/logrotate.conf       # Debug logrotate
logrotate -f /etc/logrotate.d/nginx    # Force rotation
```

### Application Debugging

#### System Call Tracing

bash

```bash
# strace - trace system calls
strace -p PID                          # Attach to running process
strace -f -o trace.out command         # Trace with child processes
strace -e open,read,write command      # Trace specific syscalls
strace -c command                      # Count syscalls

# ltrace - trace library calls
ltrace -p PID                          # Attach to process
ltrace -e malloc,free command          # Trace specific functions
```

#### File and Network Analysis

bash

```bash
# lsof - list open files
lsof -p PID                            # Files opened by process
lsof -i :80                            # Processes using port 80
lsof -u username                       # Files opened by user
lsof +D /path/to/directory             # Files under directory
lsof -i TCP:LISTEN                     # All listening TCP ports

# Network debugging
ss -tulpn                              # Modern replacement for netstat
netstat -tulpn                         # Traditional network statistics
tcpdump -i eth0 port 80                # Capture HTTP traffic
```

### Performance Analysis

#### CPU and Memory Profiling

bash

```bash
# perf - performance analysis
perf top                               # Real-time CPU profiling
perf record -g command                 # Record with call graphs
perf report                            # Analyze recorded data
perf stat command                      # Performance statistics

# System monitoring
iotop                                  # I/O usage by process
dstat -cdngy                          # Comprehensive system stats
htop                                   # Interactive process viewer
atop                                   # Advanced system monitor
```

#### Crash Analysis

bash

```bash
# Core dump configuration
echo '/tmp/core.%e.%p' > /proc/sys/kernel/core_pattern
ulimit -c unlimited                    # Enable core dumps

# OOM (Out of Memory) analysis
dmesg | grep -i "killed process"       # Find OOM killer activity
journalctl -k | grep -i "oom"         # OOM messages in journal

# Memory debugging
valgrind --tool=memcheck command       # Memory error detection
gdb command core                       # Debug core dump
```

#### Hardware Information

bash

```bash
# CPU information
lscpu                                  # CPU architecture info
cat /proc/cpuinfo                      # Detailed CPU info
nproc                                  # Number of processing units

# Storage devices
lsblk                                  # Block devices tree
fdisk -l                              # Disk partitions
df -h                                  # Filesystem usage
du -sh /path/*                        # Directory sizes

# Hardware detection
lspci                                  # PCI devices
lsusb                                  # USB devices
dmidecode                             # Hardware information from BIOS
hwinfo --short                       # Hardware detection (SUSE)
```

## 🔐 SSH & Remote Access

### SSH Configuration and Management

#### Client Configuration

bash

```bash
# SSH client config (~/.ssh/config)
Host production
    HostName prod.example.com
    User deploy
    Port 2222
    IdentityFile ~/.ssh/prod_key
    ServerAliveInterval 60
    ServerAliveCountMax 3

Host *.dev
    User developer
    IdentityFile ~/.ssh/dev_key
    ProxyJump bastion.dev

# SSH key management
ssh-keygen -t ed25519 -C "your_email@example.com"  # Generate key
ssh-add ~/.ssh/private_key                          # Add to agent
ssh-add -l                                          # List loaded keys
ssh-copy-id user@server                            # Copy public key
```

#### Server Configuration (/etc/ssh/sshd_config)

bash

```bash
# Security hardening
Port 2222                              # Change default port
PermitRootLogin no                     # Disable root login
PasswordAuthentication no              # Key-only authentication
PubkeyAuthentication yes               # Enable public key auth
MaxAuthTries 3                         # Limit auth attempts
ClientAliveInterval 300                # Keep alive interval
ClientAliveCountMax 2                  # Max missed keepalives

# Advanced features
AllowUsers deploy jenkins              # Restrict user access
Match User jenkins
    ForceCommand /usr/local/bin/restricted-shell
```

#### SSH Security Best Practices

bash

```bash
# Key permissions
chmod 700 ~/.ssh                       # SSH directory
chmod 600 ~/.ssh/id_rsa                # Private key
chmod 644 ~/.ssh/id_rsa.pub            # Public key
chmod 644 ~/.ssh/authorized_keys       # Authorized keys
chmod 644 ~/.ssh/known_hosts           # Known hosts

# SSH agent forwarding (use cautiously)
ssh -A user@server                     # Enable agent forwarding
```

### File Transfer Tools

#### Secure Copy and Sync

bash

```bash
# scp - secure copy
scp file.txt user@server:/path/        # Copy file to server
scp -r directory/ user@server:/path/   # Copy directory recursively
scp user@server:/path/file.txt .       # Copy from server

# rsync - efficient file synchronization
rsync -avz source/ dest/               # Archive, verbose, compress
rsync -avz --delete src/ dest/         # Delete extra files in dest
rsync -avz -e "ssh -p 2222" src/ user@server:dest/  # Custom SSH
rsync --exclude='*.log' src/ dest/     # Exclude patterns
```

#### SFTP and Advanced Transfers

bash

```bash
# sftp - secure file transfer protocol
sftp user@server
put localfile                          # Upload file
get remotefile                         # Download file
mput *.txt                            # Upload multiple files
mirror /local/path /remote/path       # Synchronize directories
```

## 📦 Storage Management

### Disk Partitioning

#### Traditional Partitioning (fdisk)

bash

```bash
# fdisk operations
fdisk -l                              # List all disks
fdisk /dev/sdb                        # Edit partition table
# Commands within fdisk:
# n - new partition
# d - delete partition
# p - print partition table
# w - write changes
# q - quit without saving

# Partition types
fdisk -l | grep "Linux swap"          # Find swap partitions
fdisk -l | grep "Linux filesystem"    # Find Linux partitions
```

#### Advanced Partitioning (parted)

bash

```bash
# parted - more powerful partitioning
parted /dev/sdb                       # Interactive mode
parted /dev/sdb print                 # Show partition table
parted /dev/sdb mklabel gpt           # Create GPT partition table
parted /dev/sdb mkpart primary ext4 0% 100%  # Create partition

# Batch operations
parted -s /dev/sdb mklabel gpt
parted -s /dev/sdb mkpart primary 0% 50%
parted -s /dev/sdb mkpart primary 50% 100%
```

### Filesystem Management

#### Creating and Managing Filesystems

bash

```bash
# Create filesystems
mkfs.ext4 /dev/sdb1                   # Create ext4 filesystem
mkfs.xfs /dev/sdb1                    # Create XFS filesystem
mkfs.btrfs /dev/sdb1                  # Create Btrfs filesystem

# Filesystem tuning
tune2fs -l /dev/sdb1                  # Show ext4 parameters
tune2fs -c 0 /dev/sdb1               # Disable fsck check count
tune2fs -L "DATA" /dev/sdb1          # Set filesystem label

# Filesystem checking and repair
fsck /dev/sdb1                        # Check filesystem
fsck -y /dev/sdb1                     # Auto-repair filesystem
xfs_repair /dev/sdb1                  # Repair XFS filesystem
```

#### Advanced Filesystems

##### Btrfs Management

bash

```bash
# Btrfs operations
btrfs filesystem show                 # Show Btrfs filesystems
btrfs subvolume create /mnt/subvol    # Create subvolume
btrfs subvolume snapshot /mnt/vol /mnt/snap  # Create snapshot
btrfs filesystem balance /mnt         # Balance filesystem
btrfs scrub start /mnt               # Check data integrity
```

##### ZFS Management (where available)

bash

```bash
# ZFS pool management
zpool create mypool /dev/sdb          # Create ZFS pool
zpool status                          # Show pool status
zfs create mypool/dataset            # Create dataset
zfs snapshot mypool/dataset@snap1    # Create snapshot
zfs send mypool/dataset@snap1 | zfs recv backup/dataset  # Replication
```

### Logical Volume Management (LVM)

#### LVM Setup and Management

bash

```bash
# Physical Volume operations
pvcreate /dev/sdb1 /dev/sdc1         # Create physical volumes
pvdisplay                            # Show PV information
pvs                                  # Short PV listing

# Volume Group operations
vgcreate vg_data /dev/sdb1 /dev/sdc1 # Create volume group
vgextend vg_data /dev/sdd1           # Add PV to VG
vgdisplay                            # Show VG information
vgs                                  # Short VG listing

# Logical Volume operations
lvcreate -L 10G -n lv_app vg_data    # Create 10GB logical volume
lvcreate -l 100%FREE -n lv_data vg_data  # Use all free space
lvextend -L +5G /dev/vg_data/lv_app  # Extend logical volume
lvdisplay                            # Show LV information
lvs                                  # Short LV listing
```

#### LVM Snapshots

bash

```bash
# Snapshot operations
lvcreate -L 1G -s -n lv_app_snap /dev/vg_data/lv_app  # Create snapshot
lvconvert --merge /dev/vg_data/lv_app_snap            # Merge snapshot
lvremove /dev/vg_data/lv_app_snap                     # Remove snapshot
```

#### Filesystem Resizing

bash

```bash
# Resize filesystem after LV extension
resize2fs /dev/vg_data/lv_app         # Resize ext4 filesystem
xfs_growfs /mnt/app                   # Resize XFS filesystem (must be mounted)
```

### Mount Management

#### Mounting and Unmounting

bash

```bash
# Manual mounting
mount /dev/sdb1 /mnt/data            # Mount filesystem
mount -t nfs server:/path /mnt/nfs   # Mount NFS share
mount -o loop disk.img /mnt/loop     # Mount disk image

# Unmounting
umount /mnt/data                     # Unmount filesystem
umount -l /mnt/data                  # Lazy unmount
fuser -km /mnt/data                  # Kill processes using mountpoint
```

#### Persistent Mounts (/etc/fstab)

bash

```bash
# /etc/fstab entries
/dev/sdb1    /data         ext4    defaults         0  2
UUID=xxx     /backup       xfs     defaults,noatime 0  2
server:/nfs  /mnt/nfs      nfs     defaults         0  0
tmpfs        /tmp          tmpfs   defaults,size=2G 0  0

# Mount options
defaults                             # Standard mount options
noatime                             # Don't update access times
ro                                  # Read-only
rw                                  # Read-write
auto                                # Mount at boot
noauto                              # Don't mount at boot
```

## 🧠 Advanced System Administration

### Kernel Tuning and System Parameters

#### Sysctl Configuration

bash

```bash
# View current parameters
sysctl -a                            # Show all parameters
sysctl net.ipv4.ip_forward          # Show specific parameter
sysctl -p                           # Reload from /etc/sysctl.conf

# Common performance tunings
# /etc/sysctl.conf or /etc/sysctl.d/*.conf
vm.swappiness = 10                   # Reduce swap usage
vm.dirty_ratio = 15                  # Dirty page cache ratio
net.core.somaxconn = 1024           # Socket listen backlog
net.ipv4.tcp_max_syn_backlog = 2048 # SYN backlog queue
fs.file-max = 65536                 # Maximum file handles

# Apply changes
sysctl -w net.ipv4.ip_forward=1     # Temporary change
echo 1 > /proc/sys/net/ipv4/ip_forward  # Direct proc write
```

#### Kernel Modules

bash

```bash
# Module management
lsmod                               # List loaded modules
modinfo module_name                 # Show module information
modprobe module_name                # Load module
modprobe -r module_name             # Remove module
depmod -a                          # Update module dependencies

# Persistent module loading
# /etc/modules-load.d/modules.conf
br_netfilter
overlay
```

### Process and Resource Management

#### Cgroups (Control Groups)

bash

```bash
# Cgroups v1 (legacy)
ls /sys/fs/cgroup/                  # Available cgroup controllers
cat /sys/fs/cgroup/memory/memory.limit_in_bytes
echo $PID > /sys/fs/cgroup/memory/mygroup/cgroup.procs

# Cgroups v2 (unified hierarchy)
ls /sys/fs/cgroup/                  # Unified cgroup interface
systemd-cgls                        # Show cgroup tree
systemctl set-property httpd.service MemoryLimit=1G  # Set memory limit
```

#### Resource Limits (ulimit)

bash

```bash
# View limits
ulimit -a                           # All limits
ulimit -n                          # File descriptor limit
ulimit -u                          # Process limit

# Set limits
ulimit -n 65536                    # Increase file descriptors
ulimit -c unlimited                # Enable core dumps

# Persistent limits (/etc/security/limits.conf)
*    soft nofile 65536
*    hard nofile 65536
@dba soft nproc  2048
@dba hard nproc  4096
```

#### Linux Capabilities

bash

```bash
# View capabilities
getcap /usr/bin/ping                # Show file capabilities
capsh --print                      # Show current capabilities
getpcaps PID                       # Show process capabilities

# Set capabilities
setcap cap_net_raw+ep /usr/bin/ping  # Set capabilities on file
capsh --drop=cap_sys_admin --       # Drop capabilities
```

### Security and Auditing

#### SELinux Basics

bash

```bash
# SELinux status and modes
getenforce                          # Current SELinux mode
setenforce 0                       # Set to permissive (temporary)
sestatus                           # Detailed SELinux status

# SELinux contexts
ls -Z /path/to/file                # Show SELinux context
ps -eZ                             # Show process contexts
chcon -t httpd_exec_t /path/file   # Change context
restorecon -R /var/www/            # Restore default contexts

# SELinux troubleshooting
sealert -a /var/log/audit/audit.log  # Analyze audit log
ausearch -m avc -ts recent          # Search for recent denials
```

#### System Auditing (auditd)

bash

```bash
# Audit daemon
systemctl status auditd             # Check audit daemon
auditctl -l                        # List audit rules
auditctl -w /etc/passwd -p wa       # Watch file for writes/attributes

# Audit log analysis
ausearch -f /etc/passwd             # Search by file
ausearch -ui 1000                   # Search by user ID
aureport --summary                  # Audit summary report
```

### Time and Job Scheduling

#### Cron vs Systemd Timers

##### Traditional Cron

bash

```bash
# Crontab management
crontab -l                          # List user crontab
crontab -e                          # Edit user crontab
crontab -u username -l              # List another user's crontab

# Cron syntax: minute hour day month weekday command
0 2 * * * /usr/local/bin/backup.sh  # Daily at 2 AM
*/15 * * * * /usr/bin/check-health  # Every 15 minutes
0 0 1 * * /usr/bin/monthly-report   # Monthly report

# System cron directories
/etc/cron.hourly/                   # Hourly scripts
/etc/cron.daily/                    # Daily scripts
/etc/cron.weekly/                   # Weekly scripts
/etc/cron.monthly/                  # Monthly scripts
```

##### Systemd Timers

bash

```bash
# List timers
systemctl list-timers              # Show all timers
systemctl list-timers --all        # Include inactive timers

# Timer unit example (/etc/systemd/system/backup.timer)
[Unit]
Description=Daily backup
Requires=backup.service

[Timer]
OnCalendar=daily
Persistent=true

[Install]
WantedBy=timers.target

# Enable and start timer
systemctl enable backup.timer
systemctl start backup.timer
```

### Containers and Isolation

#### Namespaces and chroot

bash

```bash
# chroot environment
chroot /path/to/new/root /bin/bash  # Change root directory

# Namespace operations
unshare --mount --pid --fork bash  # Create isolated namespaces
lsns                               # List namespaces
nsenter -t PID -n -p               # Enter process namespaces
```

## 🔐 DevOps-Specific Advanced Topics

### Systemd for DevOps

#### Service Management

bash

```bash
# Service unit file (/etc/systemd/system/myapp.service)
[Unit]
Description=My Application
After=network.target
Wants=postgresql.service

[Service]
Type=simple
User=myapp
Group=myapp
WorkingDirectory=/opt/myapp
ExecStart=/opt/myapp/bin/start
ExecReload=/bin/kill -HUP $MAINPID
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target

# Service management
systemctl daemon-reload            # Reload systemd configuration
systemctl enable myapp             # Enable service at boot
systemctl start myapp              # Start service
systemctl status myapp             # Check service status
```

#### Container Integration with systemd

bash

```bash
# Podman systemd integration
podman generate systemd --name mycontainer > mycontainer.service
systemctl --user daemon-reload
systemctl --user enable mycontainer.service

# Docker with systemd
docker run -d --restart=unless-stopped \
  --name myapp \
  --label="systemd.wanted-by=multi-user.target" \
  myimage:latest
```

### Secrets Management

#### GPG for Secret Management

bash

```bash
# GPG operations
gpg --gen-key                       # Generate GPG key pair
gpg --list-keys                     # List public keys
gpg --encrypt -r recipient file.txt # Encrypt file
gpg --decrypt file.txt.gpg          # Decrypt file

# Git-secret integration
git secret init                     # Initialize git-secret
git secret add config/secrets.yml   # Add file to be encrypted
git secret hide                     # Encrypt all secret files
```

#### HashiCorp Vault Integration

bash

```bash
# Vault CLI operations
vault status                        # Check Vault status
vault auth -method=ldap username=user # Authenticate
vault read secret/myapp/config      # Read secret
vault write secret/myapp/config key=value # Write secret

# Vault agent for automatic token renewal
vault agent -config=agent.hcl &
```

### Infrastructure as Code

#### System Configuration Management

bash

```bash
# Ansible facts gathering
ansible hostname -m setup          # Gather system facts
ansible-playbook -C playbook.yml   # Dry run playbook
ansible-vault encrypt secrets.yml  # Encrypt sensitive data

# Salt minion configuration
salt-call state.apply              # Apply Salt states
salt-call grains.items             # Show system grains
```

### CI/CD Integration

#### Jenkins Agent Setup

bash

```bash
# Jenkins user setup
useradd -m -s /bin/bash jenkins
usermod -aG docker jenkins          # Add to docker group
sudo -u jenkins ssh-keygen -t rsa   # Generate SSH key

# Jenkins systemd service
systemctl enable jenkins
systemctl start jenkins
journalctl -u jenkins -f           # Follow Jenkins logs
```

#### GitLab Runner Configuration

bash

```bash
# GitLab Runner registration
gitlab-runner register             # Interactive registration
gitlab-runner list                 # List registered runners
gitlab-runner verify              # Verify runner configuration

# Runner service management
systemctl enable gitlab-runner
systemctl start gitlab-runner
```

### Monitoring and Observability

#### Prometheus Node Exporter

bash

```bash
# Node exporter service
systemctl enable node_exporter
systemctl start node_exporter
curl http://localhost:9100/metrics # Verify metrics endpoint

# Custom metrics collection
echo 'my_custom_metric 42' > /var/lib/node_exporter/custom.prom
```

#### Log Aggregation Setup

bash

```bash
# Rsyslog for centralized logging
# /etc/rsyslog.conf
*.* @@logserver:514                # Forward all logs

# Fluentd configuration
# /etc/fluent/fluent.conf
<source>
  @type tail
  path /var/log/nginx/access.log
  tag nginx.access
  format nginx
</source>
```

### Network and Security Hardening

#### Firewall Management (iptables/nftables)

bash

```bash
# iptables rules
iptables -L                        # List current rules
iptables -A INPUT -p tcp --dport 22 -j ACCEPT  # Allow SSH
iptables -A INPUT -p tcp --dport 80 -j ACCEPT  # Allow HTTP
iptables -P INPUT DROP             # Default policy DROP

# Save iptables rules
iptables-save > /etc/iptables/rules.v4

# nftables (modern replacement)
nft list ruleset                   # Show current rules
nft add rule inet filter input tcp dport 22 accept
```

#### SSH Hardening for Production

bash

```bash
# Advanced SSH configuration
Protocol 2                         # Use SSH protocol 2 only
MaxAuthTries 2                     # Limit authentication attempts
LoginGraceTime 60                  # Grace time for login
MaxStartups 3:30:10               # Limit concurrent connections
AllowGroups sshusers              # Restrict user groups

# SSH monitoring and alerting
journalctl -u sshd | grep "Failed password"  # Monitor failed logins
fail2ban-client status sshd       # Check fail2ban SSH jail
```

### Performance Optimization

#### System Performance Tuning

bash

```bash
# CPU governor settings
echo performance | tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor

# Memory management
echo never > /sys/kernel/mm/transparent_hugepage/enabled
echo 1 > /proc/sys/vm/drop_caches   # Clear page cache

# I/O scheduler optimization
echo noop > /sys/block/sda/queue/scheduler  # For SSDs
echo deadline > /sys/block/sdb/queue/scheduler  # For HDDs
```

#### Network Performance Tuning

bash

```bash
# Network buffer tuning
net.core.rmem_max = 16777216       # Receive buffer size
net.core.wmem_max = 16777216       # Send buffer size
net.ipv4.tcp_congestion_control = bbr  # BBR congestion control
net.ipv4.tcp_window_scaling = 1    # Enable window scaling
```

### Backup and Disaster Recovery

#### Automated Backup Strategies

bash

```bash
# Rsync-based backups
rsync -avz --delete --backup --backup-dir=../backup-$(date +%Y%m%d) \
  /source/ /destination/

# Database backups
mysqldump --all-databases --single-transaction | gzip > backup.sql.gz
pg_dumpall | gzip > postgres_backup.sql.gz

# LVM snapshot backups
lvcreate -L 1G -s -n backup_snap /dev/vg/data
mount /dev/vg/backup_snap /mnt/backup
rsync -av /mnt/backup/ /backup/location/
umount /mnt/backup
lvremove -f /dev/vg/backup_snap
```

### Cloud Integration

#### Cloud-Init Configuration

bash

```bash
# Cloud-init user data example
#cloud-config
packages:
  - docker.io
  - nginx

users:
  - name: deploy
    ssh_authorized_keys:
      - ssh-rsa AAAA...
    sudo: ALL=(ALL) NOPASSWD:ALL

runcmd:
  - systemctl enable docker
  - systemctl start docker
```