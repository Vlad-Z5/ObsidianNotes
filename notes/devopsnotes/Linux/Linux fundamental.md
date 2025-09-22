# Linux Fundamentals

## Linux Philosophy & Core Architecture

Linux follows the Unix philosophy: "Do one thing and do it well." Understanding this principle is crucial for DevOps engineers who need to chain together simple tools to create complex automation workflows.

### Key Architecture Components

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

## Filesystem Hierarchy Standard (FHS)

### Critical DevOps Directories

- **`/etc`**: System configuration files, service configs, cron jobs
    - `/etc/systemd/system/`: Custom systemd service files
    - `/etc/nginx/`, `/etc/apache2/`: Web server configurations
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

### DevOps Best Practices

- Always use `/opt` for custom applications in production
- Monitor `/var/log` sizes - they can fill disks quickly
- `/proc` and `/sys` are goldmines for system monitoring scripts

## Essential Linux Concepts

### Everything is a File

In Linux, everything is treated as a file:
- Regular files: documents, scripts, binaries
- Directories: special files containing other files
- Device files: `/dev/sda` (hard drive), `/dev/null` (null device)
- Process files: `/proc/1234/` (process information)
- Network sockets: treated as file descriptors

### File Types and Identification

```bash
# File type identification
file /path/to/file                     # Identify file type
ls -la                                 # Show file types with permissions
stat /path/to/file                     # Detailed file information
```

**File Type Indicators (from ls -l):**
- `-`: Regular file
- `d`: Directory
- `l`: Symbolic link
- `c`: Character device
- `b`: Block device
- `s`: Socket
- `p`: Named pipe (FIFO)

### Links and Inodes

#### Hard Links vs Symbolic Links

```bash
# Hard links - multiple names for same file
ln /path/to/original /path/to/hardlink

# Symbolic links - pointer to another file
ln -s /path/to/original /path/to/symlink

# View inode information
ls -li                                 # Show inode numbers
stat filename                         # Detailed inode info
```

**Key Differences:**
- Hard links share the same inode number
- Symbolic links have their own inode but point to another file
- Hard links cannot cross filesystem boundaries
- Symbolic links can point to files on different filesystems

### Basic Text Processing

#### Essential Text Commands

```bash
# View file contents
cat file.txt                          # Display entire file
less file.txt                         # Page through file
head -n 10 file.txt                   # First 10 lines
tail -n 10 file.txt                   # Last 10 lines
tail -f /var/log/syslog               # Follow log file

# Search and filter
grep "pattern" file.txt                # Search for pattern
grep -r "pattern" /var/log/            # Recursive search
grep -v "exclude" file.txt             # Invert match
awk '{print $1}' file.txt             # Print first column
sed 's/old/new/g' file.txt            # Replace text

# Sort and unique
sort file.txt                          # Sort lines
sort -n numbers.txt                    # Numeric sort
uniq file.txt                          # Remove duplicates
sort file.txt | uniq -c                # Count occurrences
```

### Streams and Redirection

#### Understanding Standard Streams

- **stdin (0)**: Standard input (keyboard)
- **stdout (1)**: Standard output (screen)
- **stderr (2)**: Standard error (screen)

```bash
# Redirection examples
command > output.txt                   # Redirect stdout to file
command 2> error.txt                   # Redirect stderr to file
command > output.txt 2>&1             # Redirect both stdout and stderr
command >> output.txt                 # Append to file
command < input.txt                    # Use file as input
command | another_command              # Pipe output to another command

# Advanced redirection
command 2>/dev/null                    # Discard error output
command &>/dev/null                    # Discard all output
```

## Package Management Essentials

### Debian/Ubuntu (APT)

```bash
# Package operations
apt update                             # Update package lists
apt upgrade                            # Upgrade installed packages
apt install package_name               # Install package
apt remove package_name                # Remove package
apt purge package_name                 # Remove package and config files
apt autoremove                         # Remove orphaned packages

# Package information
apt search keyword                     # Search for packages
apt show package_name                  # Show package details
dpkg -l                               # List installed packages
dpkg -L package_name                  # List files in package
```

### RHEL/CentOS/Fedora (YUM/DNF)

```bash
# Package operations
yum update                             # Update all packages
yum install package_name               # Install package
yum remove package_name                # Remove package
yum search keyword                     # Search for packages

# DNF (newer systems)
dnf update                             # Update all packages
dnf install package_name               # Install package
dnf remove package_name                # Remove package
dnf search keyword                     # Search for packages
```

## User and Group Management

### Basic User Operations

```bash
# User management
useradd username                       # Add user
usermod -aG group username             # Add user to group
userdel username                       # Delete user
passwd username                        # Change password

# Group management
groupadd groupname                     # Add group
groupmod -n newname oldname            # Rename group
groupdel groupname                     # Delete group

# View user information
id username                            # Show user ID and groups
whoami                                 # Current username
who                                    # Logged in users
w                                      # Detailed user activity
```

### Permission Management

```bash
# Permission commands
chmod 755 file                         # Set permissions (octal)
chmod u+x file                         # Add execute for owner
chmod g-w file                         # Remove write for group
chmod o=r file                         # Set other to read-only

# Ownership commands
chown user:group file                  # Change owner and group
chown -R user:group directory/         # Recursive ownership change

# Special permissions
chmod +t /tmp                          # Sticky bit
chmod g+s directory                    # SGID bit
chmod u+s executable                   # SUID bit
```

## Environment and Variables

### Environment Variables

```bash
# View environment
env                                    # Show all environment variables
echo $PATH                             # Show specific variable
printenv HOME                          # Show HOME variable

# Set variables
export VAR_NAME="value"                # Set and export variable
unset VAR_NAME                         # Remove variable

# Common environment variables
$HOME                                  # User's home directory
$PATH                                  # Executable search path
$USER                                  # Current username
$PWD                                   # Current working directory
$SHELL                                 # Current shell
```

### Shell Configuration

```bash
# Bash configuration files
~/.bashrc                              # User bash configuration
~/.bash_profile                        # User login configuration
/etc/bash.bashrc                       # System-wide bash config
/etc/profile                           # System-wide login config

# Common customizations
alias ll='ls -la'                      # Create command alias
export PATH=$PATH:/opt/bin             # Add to PATH
```

## Basic Troubleshooting

### System Information

```bash
# System overview
uname -a                               # System information
hostnamectl                            # Hostname and system info
uptime                                 # System uptime and load
df -h                                  # Disk usage
free -h                                # Memory usage
lscpu                                  # CPU information
```

### Log Analysis

```bash
# Important log locations
/var/log/syslog                        # System messages (Debian/Ubuntu)
/var/log/messages                      # System messages (RHEL/CentOS)
/var/log/auth.log                      # Authentication logs
/var/log/kern.log                      # Kernel messages

# Log analysis commands
journalctl                             # Systemd journal (all logs)
journalctl -u service_name             # Logs for specific service
journalctl -f                          # Follow logs in real-time
dmesg                                  # Kernel ring buffer
```

## System Troubleshooting Methodology

### Systematic Problem-Solving Approach

When systems run slowly or behave unexpectedly, follow this structured methodology:

#### **1. Understanding the Problem**
- **Processing**: CPU-bound tasks, high load averages
- **Disk I/O**: Storage bottlenecks, filesystem issues
- **Networking**: Connectivity, bandwidth, latency issues
- **Memory**: RAM exhaustion, swapping, memory leaks
- **Hardware**: Hardware failures, driver issues

#### **2. Troubleshooting Steps**
```bash
# Step 1: Verify you're on the correct system
hostname && whoami
cat /etc/os-release

# Step 2: Check disk space (common cause of issues)
df -h                               # Filesystem usage
du -sh /var/log /tmp /home          # Check large directories

# Step 3: Check processing and memory
top                                 # Real-time process view
free -h                             # Memory usage
lsmem                               # Memory configuration
cat /proc/meminfo                   # Detailed memory info
vmstat 1 5                          # Virtual memory statistics
pmap <PID>                          # Memory map of specific process

# Step 4: Check disk I/O issues
iostat -y 5                         # I/O statistics
lsof                                # List open files
iotop                               # I/O usage by process

# Step 5: Check network issues
ss -tuln                            # Open ports and connections
netstat -i                          # Network interface statistics
tcpdump -i eth0                     # Packet capture
iftop                               # Network bandwidth usage

# Step 6: Check system uptime and load
uptime                              # System uptime and load average
w                                   # Logged in users and load

# Step 7: Check system logs
journalctl -f                       # Follow system logs
dmesg | tail                        # Recent kernel messages
tail -f /var/log/syslog             # System log messages

# Step 8: Check hardware status
lscpu                               # CPU information
lshw                                # Hardware information
dmidecode                           # DMI/SMBIOS information
```

#### **3. Advanced Troubleshooting Tools**
```bash
# Performance analysis
htop                                # Enhanced process viewer
iotop                               # I/O monitoring
iptraf                              # Network traffic analyzer
psacct                              # Process accounting

# System call tracing
strace -p <PID>                     # Trace system calls
ltrace -p <PID>                     # Trace library calls

# Network troubleshooting
mtr google.com                      # Network path analysis
nmap -sn 192.168.1.0/24            # Network discovery
ss -i                               # Socket statistics with details
```

### **Performance Baseline and Monitoring**

#### **Establishing System Baselines**
```bash
# CPU baseline
lscpu                               # CPU architecture info
cat /proc/cpuinfo                   # Detailed CPU information
nproc                               # Number of processing units

# Memory baseline
free -h                             # Current memory usage
cat /proc/meminfo | grep -E 'MemTotal|MemFree|MemAvailable'

# Storage baseline
lsblk -f                            # Block devices and filesystems
df -h                               # Filesystem usage
iostat -x 1 5                       # I/O performance baseline

# Network baseline
ip addr show                        # Network interfaces
ethtool eth0                        # Network interface details
ss -s                               # Socket statistics summary
```

#### **Continuous Monitoring Strategy**
```bash
# Create monitoring scripts
# Memory usage trend
echo "$(date): $(free | grep Mem | awk '{print $3/$2 * 100.0}')% memory used" >> /var/log/memory.log

# Disk usage trend
echo "$(date): $(df / | tail -1 | awk '{print $5}') root disk used" >> /var/log/disk.log

# Load average trend
echo "$(date): $(uptime | awk -F'load average:' '{print $2}')" >> /var/log/load.log

# Monitor specific processes
ps aux --sort=-%cpu | head -10 >> /var/log/top-cpu.log
ps aux --sort=-%mem | head -10 >> /var/log/top-mem.log
```

### **Common System Issues and Solutions**

#### **High Load Average**
```bash
# Identify cause
uptime                              # Check load average
top -o %CPU                         # Sort by CPU usage
ps aux --sort=-%cpu | head -20      # Top CPU consumers

# Solutions
nice -n 19 cpu_intensive_process    # Lower process priority
killall -STOP process_name          # Temporarily stop process
systemctl stop service_name         # Stop problematic service
```

#### **Memory Issues**
```bash
# Identify memory problems
free -h                             # Overall memory usage
ps aux --sort=-%mem | head -20      # Memory-hungry processes
cat /proc/meminfo | grep -E 'SwapTotal|SwapFree'  # Swap usage

# Solutions
sync && echo 3 > /proc/sys/vm/drop_caches  # Clear caches (emergency only)
systemctl restart memory_hungry_service    # Restart problematic service
kill -TERM <PID>                           # Terminate memory-leaking process
```

#### **Disk Space Issues**
```bash
# Find large files and directories
du -sh /* | sort -hr                # Large directories in root
find / -size +100M -type f          # Files larger than 100MB
find /var/log -name "*.log" -size +50M  # Large log files

# Clean up solutions
journalctl --vacuum-size=100M       # Limit journal size
apt autoremove && apt autoclean     # Clean package cache
find /tmp -mtime +7 -delete         # Clean old temporary files
logrotate -f /etc/logrotate.conf    # Force log rotation
```

## System Monitoring and Performance Analysis

### **Essential System Metrics**

#### **The Four Golden Signals**
1. **Latency**: Response time of requests
2. **Traffic**: Demand on the system
3. **Errors**: Rate of failed requests
4. **Saturation**: How full the system is

#### **Key Linux Performance Indicators**
```bash
# CPU Metrics
cat /proc/loadavg                   # Load average (1, 5, 15 min)
vmstat 1 5                          # CPU usage, context switches
mpstat -P ALL 1 5                   # Per-CPU statistics

# Memory Metrics
cat /proc/meminfo                   # Detailed memory information
vmstat -s                           # Memory statistics summary
sar -r 1 10                         # Memory usage over time

# Disk I/O Metrics
iostat -x 1 5                       # Extended I/O statistics
sar -d 1 10                         # Disk activity over time
lsof | wc -l                        # Number of open files

# Network Metrics
ss -s                               # Socket statistics
sar -n DEV 1 10                     # Network interface statistics
netstat -i                          # Network interface statistics
```

## Reference to Specialized Topics

For detailed coverage of specific Linux administration areas, refer to these specialized guides:

- **[[Linux Networking Files and Folders]]** - Network configuration, tools, and troubleshooting
- **[[Linux Process Management]]** - Process control, monitoring, and performance analysis
- **[[Linux System Administration]]** - Systemd, services, logging, and system configuration
- **[[Linux Security]]** - Security hardening, auditing, and access control
- **[[Linux Storage Management]]** - Disk management, filesystems, and LVM
- **[[Linux Commands]]** - Comprehensive command reference with DevOps focus
- **[[Linux Shell Scripting Essentials]]** - Bash scripting fundamentals and automation

This fundamental guide provides the core concepts and troubleshooting methodology needed to understand and maintain Linux systems effectively in DevOps environments.