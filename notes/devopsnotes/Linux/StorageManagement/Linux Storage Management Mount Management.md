# Linux Storage Management Mount Management

**Mount Management** covers manual mounting/unmounting operations and persistent mount configuration through /etc/fstab for reliable filesystem access across system reboots.

## Manual Mounting and Unmounting

### Basic Mount Operations

#### Standard Mounting
```bash
# Basic mount operations
mount /dev/sdb1 /mnt/data               # Mount with auto-detected filesystem
mount -t ext4 /dev/sdb1 /mnt/data       # Mount with specific filesystem type
mount -t xfs /dev/sdb1 /mnt/data        # Mount XFS filesystem
mount -t btrfs /dev/sdb1 /mnt/data      # Mount Btrfs filesystem

# Mount with specific options
mount -o ro /dev/sdb1 /mnt/data         # Mount read-only
mount -o rw /dev/sdb1 /mnt/data         # Mount read-write
mount -o rw,noatime /dev/sdb1 /mnt/data # Mount with no access time updates
mount -o rw,noatime,nodiratime /dev/sdb1 /mnt/data  # No access time for dirs either

# Mount by UUID or label
mount UUID=12345678-1234-1234-1234-123456789abc /mnt/data
mount LABEL=DATA /mnt/data              # Mount by filesystem label
mount /dev/disk/by-uuid/12345678-1234-1234-1234-123456789abc /mnt/data
```

#### Special Mount Types
```bash
# Temporary filesystem (RAM disk)
mount -t tmpfs tmpfs /mnt/temp          # Basic tmpfs mount
mount -t tmpfs -o size=1G tmpfs /mnt/ramdisk  # 1GB RAM disk
mount -t tmpfs -o size=50%,mode=1777 tmpfs /mnt/tmp  # 50% of RAM, writable by all

# System filesystems
mount -t proc proc /mnt/chroot/proc     # Mount proc filesystem
mount -t sysfs sysfs /mnt/chroot/sys    # Mount sysfs filesystem
mount -t devtmpfs devtmpfs /mnt/chroot/dev  # Mount device filesystem

# Bind mounts
mount --bind /home /mnt/backup/home     # Bind mount (same filesystem, different path)
mount --bind /var/log /mnt/logs         # Bind mount logs directory
mount -o bind,ro /etc /mnt/etc-readonly # Read-only bind mount

# Loop device mounts
mount -o loop disk.img /mnt/loop        # Mount disk image file
mount -o loop,ro backup.iso /mnt/iso    # Mount ISO image read-only
losetup /dev/loop0 disk.img && mount /dev/loop0 /mnt/loop  # Manual loop setup
```

#### Network Mounts
```bash
# NFS mounts
mount -t nfs server:/path /mnt/nfs      # Basic NFS mount
mount -t nfs -o vers=3 server:/path /mnt/nfs  # NFSv3
mount -t nfs -o vers=4,proto=tcp server:/path /mnt/nfs  # NFSv4 over TCP

# SMB/CIFS mounts
mount -t cifs //server/share /mnt/smb -o username=user  # SMB with username
mount -t cifs //server/share /mnt/smb -o credentials=/etc/cifs-creds  # Using creds file
mount -t cifs //server/share /mnt/smb -o username=user,password=pass,uid=1000,gid=1000

# SSH filesystem (SSHFS)
sshfs user@server:/remote/path /mnt/ssh  # Mount remote directory via SSH
sshfs -o allow_other user@server:/path /mnt/ssh  # Allow other users access
```

### Viewing Mount Information
```bash
# Show mounted filesystems
mount                                   # Show all current mounts
mount | column -t                       # Show in table format
mount | grep /dev/sdb                   # Show specific device mounts
mount -l                                # Show with filesystem labels

# Advanced mount information
findmnt                                 # Tree view of all mounts
findmnt /mnt/data                       # Show specific mount point info
findmnt --df                            # Show in df-like format
findmnt -D                              # Show with additional columns
findmnt -t ext4                         # Show only ext4 filesystems

# Filesystem usage
df -h                                   # Show mounted filesystems with usage
df -h /mnt/data                         # Show specific mount point usage
df -i                                   # Show inode usage
df -T                                   # Show filesystem types

# Process mount namespace
lsof +D /mnt/data                       # List open files in directory
fuser -v /mnt/data                      # Show processes using mount point
```

## Unmounting

### Basic Unmount Operations
```bash
# Standard unmounting
umount /mnt/data                        # Unmount by mount point
umount /dev/sdb1                        # Unmount by device
umount -v /mnt/data                     # Verbose unmount

# Multiple unmounts
umount /mnt/data /mnt/backup            # Unmount multiple mount points
umount -a -t ext4                       # Unmount all ext4 filesystems
umount -a -O nodev                      # Unmount all with nodev option
```

### Force Unmount and Troubleshooting
```bash
# Force unmount options
umount -l /mnt/data                     # Lazy unmount (detach immediately)
umount -f /mnt/data                     # Force unmount (mainly for network mounts)
umount -f -l /mnt/data                  # Force lazy unmount

# Find processes preventing unmount
lsof +D /mnt/data                       # List open files in directory tree
lsof /mnt/data                          # Check open files at mount point
fuser -v /mnt/data                      # Show processes using mount point
fuser -m /mnt/data                      # Show processes with files open on filesystem

# Kill processes and unmount
fuser -km /mnt/data                     # Kill processes and unmount
fuser -k /mnt/data && umount /mnt/data  # Kill processes then unmount

# Unmount troubleshooting script
cat << 'EOF' > /usr/local/bin/force-umount
#!/bin/bash
# Force unmount helper script

MOUNT_POINT="$1"

if [[ -z "$MOUNT_POINT" ]]; then
    echo "Usage: $0 <mount_point>"
    exit 1
fi

if ! mount | grep -q "$MOUNT_POINT"; then
    echo "Mount point $MOUNT_POINT is not mounted"
    exit 1
fi

echo "Attempting to unmount: $MOUNT_POINT"

# Try normal unmount first
if umount "$MOUNT_POINT" 2>/dev/null; then
    echo "Successfully unmounted $MOUNT_POINT"
    exit 0
fi

echo "Normal unmount failed. Checking for processes..."

# Show processes using the mount point
echo "Processes using $MOUNT_POINT:"
fuser -v "$MOUNT_POINT" 2>/dev/null

echo "Files open in $MOUNT_POINT:"
lsof +D "$MOUNT_POINT" 2>/dev/null | head -20

read -p "Kill processes and force unmount? (y/N): " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Killing processes..."
    fuser -k "$MOUNT_POINT"
    sleep 2

    echo "Attempting unmount again..."
    if umount "$MOUNT_POINT"; then
        echo "Successfully unmounted $MOUNT_POINT"
    else
        echo "Trying lazy unmount..."
        umount -l "$MOUNT_POINT" && echo "Lazy unmount successful"
    fi
else
    echo "Operation cancelled"
fi
EOF

chmod +x /usr/local/bin/force-umount
```

## Persistent Mounts with /etc/fstab

### fstab Configuration

#### fstab Format and Examples
```bash
# /etc/fstab format:
# <device> <mount_point> <filesystem_type> <options> <dump> <fsck_order>

# Example /etc/fstab entries:
cat << 'EOF' > /etc/fstab
# Root filesystem
UUID=12345678-1234-1234-1234-123456789abc / ext4 defaults 0 1

# Local filesystems
/dev/sdb1           /data           ext4    defaults,noatime            0  2
UUID=87654321-4321  /backup         xfs     defaults,noatime,nodiratime 0  2
/dev/vg_data/lv_app /opt/app        ext4    defaults,nodev,nosuid       0  2
LABEL=STORAGE       /storage        ext4    defaults,user,noauto        0  2

# Swap partitions and files
/dev/sdb2           none            swap    defaults                    0  0
/swapfile           none            swap    defaults                    0  0

# Network filesystems
server:/nfs/share   /mnt/nfs        nfs     defaults,_netdev,vers=4     0  0
//server/share      /mnt/smb        cifs    credentials=/etc/cifs-creds,_netdev 0 0

# Special filesystems
tmpfs               /tmp            tmpfs   defaults,size=2G,mode=1777,nodev,nosuid 0 0
tmpfs               /var/tmp        tmpfs   defaults,size=1G,mode=1777  0 0
none                /proc           proc    defaults                    0  0
none                /sys            sysfs   defaults                    0  0
none                /dev/pts        devpts  gid=5,mode=620              0  0

# Bind mounts
/home/shared        /mnt/shared     none    bind,noauto                 0  0
EOF
```

#### Mount Options Reference
```bash
# Common mount options:
# defaults      - rw,suid,dev,exec,auto,nouser,async
# noatime       - Don't update access times (performance)
# nodiratime    - Don't update directory access times
# relatime      - Update access times relatively (compromise)
# nodev         - Don't interpret character/block special devices
# nosuid        - Don't allow set-user-ID or set-group-ID bits
# noexec        - Don't allow execution of binaries
# ro            - Read-only
# rw            - Read-write
# auto          - Mount automatically at boot
# noauto        - Don't mount automatically (manual mount only)
# user          - Allow ordinary users to mount
# nouser        - Only root can mount (default)
# _netdev       - Network device (wait for network before mounting)
# barrier=0     - Disable write barriers (only with battery-backed RAID)
# discard       - Enable TRIM for SSDs
# compress      - Enable compression (Btrfs)
# subvol=name   - Mount Btrfs subvolume

# Security-focused options
# nodev,nosuid,noexec  - Secure mount for user directories
# ro,nodev,nosuid      - Read-only secure mount
# noatime,nodiratime   - Performance-focused options
```

### fstab Management and Testing

#### Validation and Testing
```bash
# Test fstab entries before rebooting
mount -a                                # Mount all entries in fstab
mount -av                               # Verbose mount all
mount -a -t ext4                        # Mount only ext4 entries
mount -a -O noauto                      # Mount entries with noauto option

# Validate fstab syntax
findmnt --verify                        # Verify fstab syntax and consistency
findmnt --verify --verbose              # Detailed verification
mount -fav                              # Fake mount (test without actually mounting)

# Test specific entries
mount /data                             # Mount specific entry (if in fstab)
umount /data && mount /data             # Test unmount/remount cycle

# Check mount after boot
systemctl status local-fs.target       # Check if local filesystems mounted OK
systemctl status remote-fs.target      # Check network filesystems
```

#### fstab Backup and Recovery
```bash
# Backup fstab before making changes
cp /etc/fstab /etc/fstab.backup.$(date +%Y%m%d_%H%M%S)
cp /etc/fstab /etc/fstab.original       # Keep original copy

# Recovery from broken fstab
# If system won't boot due to fstab errors:
# 1. Boot from rescue disk/USB
# 2. Mount root filesystem
# 3. Edit /etc/fstab to fix errors
# 4. Or restore from backup:
cp /etc/fstab.backup /etc/fstab

# Generate UUID entries for fstab
generate_fstab_uuids() {
    echo "# Generated fstab entries with UUIDs"
    mount | grep "^/dev/" | while read -r line; do
        device=$(echo "$line" | awk '{print $1}')
        mount_point=$(echo "$line" | awk '{print $3}')
        fs_type=$(echo "$line" | awk '{print $5}')
        uuid=$(blkid -o value -s UUID "$device" 2>/dev/null)

        if [[ -n "$uuid" ]]; then
            echo "UUID=$uuid $mount_point $fs_type defaults 0 2"
        else
            echo "$device $mount_point $fs_type defaults 0 2"
        fi
    done
}
```

### Network Mount Configuration

#### NFS Configuration
```bash
# NFS client configuration
# Install NFS utilities first:
# Ubuntu/Debian: apt install nfs-common
# RHEL/CentOS: yum install nfs-utils

# NFS fstab entries
cat << 'EOF' >> /etc/fstab
# NFS mounts
nfs-server:/export/data    /mnt/nfs-data    nfs    defaults,_netdev,vers=4,proto=tcp 0 0
nfs-server:/export/home    /mnt/nfs-home    nfs    defaults,_netdev,soft,intr,timeo=30 0 0
nfs-server:/export/backup  /mnt/nfs-backup  nfs    defaults,_netdev,ro,noauto 0 0
EOF

# NFS mount options:
# vers=4           - Use NFSv4
# proto=tcp        - Use TCP protocol
# soft             - Soft mount (timeout and return error)
# hard             - Hard mount (keep trying - default)
# intr             - Allow interrupts
# timeo=30         - Timeout in tenths of seconds
# retrans=3        - Number of retries
```

#### SMB/CIFS Configuration
```bash
# CIFS credentials file
cat << 'EOF' > /etc/cifs-credentials
username=myuser
password=mypassword
domain=mydomain
EOF

chmod 600 /etc/cifs-credentials

# CIFS fstab entries
cat << 'EOF' >> /etc/fstab
# SMB/CIFS mounts
//server/share     /mnt/smb-share    cifs   credentials=/etc/cifs-credentials,_netdev,uid=1000,gid=1000 0 0
//server/backup    /mnt/smb-backup   cifs   credentials=/etc/cifs-credentials,_netdev,ro,noauto 0 0
EOF

# CIFS mount options:
# credentials=file - Credentials file
# uid=1000         - User ID for file ownership
# gid=1000         - Group ID for file ownership
# file_mode=0755   - File permissions
# dir_mode=0755    - Directory permissions
# vers=2.0         - SMB protocol version
```

### Automated Mount Management
```bash
# Systemd mount units (alternative to fstab)
cat << 'EOF' > /etc/systemd/system/mnt-data.mount
[Unit]
Description=Data Mount
After=blockdev@dev-disk-by\x2duuid-12345678\x2d1234\x2d1234\x2d1234\x2d123456789abc.target

[Mount]
What=/dev/disk/by-uuid/12345678-1234-1234-1234-123456789abc
Where=/mnt/data
Type=ext4
Options=defaults,noatime

[Install]
WantedBy=multi-user.target
EOF

# Enable systemd mount
systemctl daemon-reload
systemctl enable mnt-data.mount
systemctl start mnt-data.mount

# Mount management script
cat << 'EOF' > /usr/local/bin/mount-manager
#!/bin/bash
# Mount management helper

case "$1" in
    check)
        echo "=== Mount Status Check ==="
        echo "Failed mounts:"
        systemctl --failed | grep "\.mount"
        echo
        echo "Mount points from fstab not mounted:"
        awk '/^[^#]/ && $2 !~ /^(none|swap)$/ {print $2}' /etc/fstab | while read -r mp; do
            if ! mount | grep -q " $mp "; then
                echo "  $mp"
            fi
        done
        ;;

    remount-all)
        echo "Remounting all fstab entries..."
        mount -a
        ;;

    verify)
        echo "Verifying fstab..."
        findmnt --verify
        ;;

    backup)
        backup_file="/etc/fstab.backup.$(date +%Y%m%d_%H%M%S)"
        cp /etc/fstab "$backup_file"
        echo "fstab backed up to: $backup_file"
        ;;

    *)
        echo "Usage: $0 {check|remount-all|verify|backup}"
        ;;
esac
EOF

chmod +x /usr/local/bin/mount-manager
```