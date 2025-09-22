# Linux Filesystem Hierarchy & Advanced Concepts

## Filesystem Hierarchy Standard (FHS)

### **Root Filesystem Structure**
- **`/`**: Root directory - everything else mounts here, critical for system boot
- **`/bin`**: Essential user binaries (commands available to all users in single-user mode)
- **`/sbin`**: System binaries (root user and system administration commands)
- **`/etc`**: Configuration files (system-wide settings, no executables)
- **`/var`**: Variable files (logs, emails, databases, web content, package state)
- **`/tmp`**: Temporary files (deleted on reboot, sometimes tmpfs)
- **`/usr`**: User programs (secondary hierarchy, can be network mounted)
- **`/home`**: User home directories (often separate partition/filesystem)
- **`/boot`**: Boot loader files (kernel, initrd, bootloader configuration)
- **`/dev`**: Device files (represent hardware devices as files)
- **`/proc`**: Process information (virtual filesystem, kernel interface)
- **`/sys`**: System information (virtual filesystem, device and driver info)
- **`/run`**: Runtime files (process IDs, sockets, early boot files)
- **`/mnt`**: Mount point for temporary filesystems
- **`/media`**: Mount point for removable media (auto-mounting)
- **`/opt`**: Optional software packages (third-party applications)
- **`/srv`**: Data for services provided by system (web content, FTP files)
- **`/lib`**: Shared libraries essential for system boot
- **`/lib64`**: 64-bit shared libraries (on 64-bit systems)

### **Critical DevOps Directories Deep Dive**

#### **`/etc` - Configuration Hub**
```bash
# System configuration
/etc/passwd                # User account information
/etc/shadow                # User password hashes
/etc/group                 # Group information
/etc/hosts                 # Static hostname resolution
/etc/fstab                 # Filesystem mount table
/etc/crontab               # System-wide cron jobs

# Service configurations
/etc/nginx/                # Nginx web server config
/etc/apache2/              # Apache web server config
/etc/mysql/                # MySQL database config
/etc/ssh/                  # SSH daemon configuration
/etc/systemd/              # Systemd service definitions

# Network configuration
/etc/network/interfaces    # Network interface config (Debian)
/etc/sysconfig/network-scripts/  # Network scripts (RHEL)
/etc/resolv.conf           # DNS resolver configuration
/etc/netplan/              # Network configuration (Ubuntu 18+)

# Security configurations
/etc/sudoers               # Sudo permissions
/etc/security/             # PAM security modules
/etc/ssl/                  # SSL certificates and keys
/etc/iptables/             # Firewall rules
```

#### **`/var` - Dynamic Data Management**
```bash
# Logging directories
/var/log/syslog           # System log messages
/var/log/auth.log         # Authentication logs
/var/log/nginx/           # Web server logs
/var/log/mysql/           # Database logs
/var/log/journal/         # Systemd journal logs

# Application data
/var/lib/docker/          # Docker container data
/var/lib/mysql/           # MySQL database files
/var/lib/postgresql/      # PostgreSQL database files
/var/lib/redis/           # Redis data files

# Package management
/var/cache/apt/           # APT package cache
/var/lib/dpkg/            # Package database (Debian)
/var/lib/rpm/             # RPM package database (RHEL)

# Web content and services
/var/www/                 # Web server document root
/var/ftp/                 # FTP server content
/var/mail/                # User mail spools
```

#### **`/usr` - User Programs Hierarchy**
```bash
# Essential directories
/usr/bin/                 # User commands
/usr/sbin/                # System administration commands
/usr/lib/                 # Libraries for /usr/bin and /usr/sbin
/usr/share/               # Architecture-independent data

# Local installations
/usr/local/bin/           # Locally installed user programs
/usr/local/sbin/          # Locally installed system programs
/usr/local/lib/           # Local libraries
/usr/local/share/         # Local architecture-independent files

# Package-specific
/usr/src/                 # Source code (kernel headers)
/usr/include/             # Header files for compilation
```

## Advanced Filesystem Concepts

### **Virtual Filesystems**

#### **`/proc` - Process and Kernel Interface**
```bash
# Process information
/proc/PID/                # Information about process PID
/proc/PID/cmdline         # Command line that started process
/proc/PID/environ         # Environment variables
/proc/PID/cwd             # Current working directory (symlink)
/proc/PID/exe             # Executable file (symlink)
/proc/PID/fd/             # File descriptors opened by process

# System information
/proc/cpuinfo             # CPU information
/proc/meminfo             # Memory usage information
/proc/loadavg             # System load average
/proc/uptime              # System uptime
/proc/version             # Kernel version
/proc/mounts              # Currently mounted filesystems

# Kernel parameters (sysctl interface)
/proc/sys/                # Kernel parameters
/proc/sys/vm/swappiness   # Swap usage aggressiveness
/proc/sys/net/ipv4/ip_forward  # IP forwarding setting
/proc/sys/fs/file-max     # Maximum number of file handles
```

#### **`/sys` - Device and Driver Interface**
```bash
# Device information
/sys/block/               # Block devices
/sys/class/net/           # Network interfaces
/sys/devices/             # Device tree
/sys/firmware/            # Firmware information

# Practical examples
/sys/class/net/eth0/operstate     # Network interface state
/sys/block/sda/queue/scheduler    # I/O scheduler for disk
/sys/devices/system/cpu/cpu0/cpufreq/  # CPU frequency scaling
```

### **Filesystem Types and Use Cases**

#### **Traditional Filesystems**
```bash
# ext4 - Most common Linux filesystem
# Features: journaling, extents, large file support
mkfs.ext4 /dev/sdb1
mount -t ext4 /dev/sdb1 /mnt

# XFS - High-performance filesystem
# Features: scalability, parallel I/O, online defragmentation
mkfs.xfs /dev/sdb1
mount -t xfs /dev/sdb1 /mnt

# Btrfs - Copy-on-write filesystem
# Features: snapshots, compression, RAID
mkfs.btrfs /dev/sdb1
mount -t btrfs /dev/sdb1 /mnt
```

#### **Special Purpose Filesystems**
```bash
# tmpfs - Memory-based filesystem
mount -t tmpfs -o size=1G tmpfs /tmp
mount -t tmpfs -o size=512M,nodev,nosuid tmpfs /dev/shm

# overlayfs - Union filesystem (used by Docker)
mount -t overlay overlay \
  -o lowerdir=/lower,upperdir=/upper,workdir=/work /merged

# FUSE - Userspace filesystems
# Examples: sshfs, s3fs, encfs
sshfs user@server:/remote/path /local/mount
```

### **Mount Management and Best Practices**

#### **Advanced Mount Options**
```bash
# Performance options
mount -o noatime /dev/sdb1 /data        # Don't update access times
mount -o relatime /dev/sdb1 /data       # Update atime less frequently
mount -o sync /dev/sdb1 /critical       # Synchronous writes
mount -o async /dev/sdb1 /data          # Asynchronous writes (default)

# Security options
mount -o nodev /dev/sdb1 /home          # No device files
mount -o nosuid /dev/sdb1 /tmp          # No SUID executables
mount -o noexec /dev/sdb1 /var          # No executable files
mount -o ro /dev/sdb1 /readonly         # Read-only mount

# Network filesystem options
mount -t nfs -o soft,intr server:/export /mnt/nfs
mount -t cifs -o credentials=/etc/cifs-creds //server/share /mnt/cifs
```

#### **Filesystem Monitoring and Maintenance**
```bash
# Check filesystem usage
df -h                               # Human-readable disk usage
df -i                               # Inode usage
du -sh /var/log                     # Directory size

# Monitor filesystem I/O
iostat -x 1                         # I/O statistics
iotop                               # I/O usage by process
lsof +D /var/log                    # Open files in directory

# Filesystem integrity
fsck /dev/sdb1                      # Check filesystem
fsck -f /dev/sdb1                   # Force check
tune2fs -l /dev/sdb1                # Display filesystem parameters
```

## DevOps Filesystem Strategies

### **Container Filesystem Patterns**
```bash
# Docker volume management
docker volume create app-data
docker run -v app-data:/app/data myapp

# Bind mounts for development
docker run -v $(pwd):/app -v /app/node_modules myapp

# Tmpfs mounts for sensitive data
docker run --tmpfs /tmp:noexec,nosuid,size=100m myapp
```

### **Filesystem Automation and Monitoring**
```bash
# Automated filesystem monitoring script
#!/bin/bash
THRESHOLD=90
df -h | awk 'NR>1 {
  usage = int($5)
  if (usage > threshold) {
    print "WARNING: " $6 " is " usage "% full"
  }
}' threshold=$THRESHOLD

# Log rotation automation
find /var/log -name "*.log" -size +100M -exec gzip {} \;
find /var/log -name "*.gz" -mtime +30 -delete
```

### **Backup and Recovery Strategies**
```bash
# Filesystem snapshots (LVM)
lvcreate -L 1G -s -n backup_snap /dev/vg0/lv_data
mount /dev/vg0/backup_snap /mnt/snapshot

# Incremental backups with rsync
rsync -av --link-dest=/backup/previous /source/ /backup/current/

# Database filesystem optimization
# Mount with noatime and appropriate I/O scheduler
echo deadline > /sys/block/sdb/queue/scheduler
```

## Cross-References
- **[[Linux Storage Management]]** - Advanced storage configurations and LVM
- **[[Linux Commands]]** - Filesystem manipulation commands
- **[[Linux Boot]]** - Boot process and filesystem mounting
- **[[Linux Security]]** - Filesystem security and permissions
- **[[Linux fundamental]]** - Core filesystem concepts and troubleshooting