# Linux Storage Management Filesystem Management

**Filesystem Management** covers creating, tuning, checking, and repairing various filesystem types including ext4, XFS, and Btrfs for optimal storage performance and reliability.

## Creating Filesystems

### Common Filesystem Types

#### ext4 Filesystem
```bash
# Basic ext4 creation
mkfs.ext4 /dev/sdb1                   # Create ext4 filesystem
mkfs.ext4 -L "DATA" /dev/sdb1         # Create with label "DATA"
mkfs.ext4 -b 4096 /dev/sdb1           # Specify block size (4KB)
mkfs.ext4 -i 16384 /dev/sdb1          # Bytes per inode (default: varies)

# Advanced ext4 options
mkfs.ext4 -m 1 /dev/sdb1              # Reserve 1% for root (default 5%)
mkfs.ext4 -r 1 /dev/sdb1              # Revision level 1
mkfs.ext4 -J size=128 /dev/sdb1       # Journal size (MB)
mkfs.ext4 -E lazy_itable_init=0,lazy_journal_init=0 /dev/sdb1  # Initialize immediately

# Large filesystem optimization
mkfs.ext4 -T largefile /dev/sdb1      # Optimize for large files
mkfs.ext4 -T largefile4 /dev/sdb1     # Optimize for very large files
mkfs.ext4 -E resize=4T /dev/sdb1      # Allow online resize up to 4TB

# Custom inode and block settings
mkfs.ext4 -N 1000000 /dev/sdb1        # Specify number of inodes
mkfs.ext4 -g 32768 /dev/sdb1          # Blocks per group
```

#### XFS Filesystem
```bash
# Basic XFS creation
mkfs.xfs /dev/sdb1                    # Create XFS filesystem
mkfs.xfs -L "LOGS" /dev/sdb1          # Create with label "LOGS"
mkfs.xfs -b size=4096 /dev/sdb1       # Specify block size
mkfs.xfs -f /dev/sdb1                 # Force creation (overwrite existing)

# Advanced XFS options
mkfs.xfs -i size=512 /dev/sdb1        # Inode size (256, 512, 1024, 2048)
mkfs.xfs -d agcount=8 /dev/sdb1       # Number of allocation groups
mkfs.xfs -l size=128m /dev/sdb1       # Log size
mkfs.xfs -n size=4096 /dev/sdb1       # Directory block size

# Performance optimization
mkfs.xfs -d su=64k,sw=4 /dev/sdb1     # Stripe unit and width for RAID
mkfs.xfs -i align=1 /dev/sdb1         # Align inodes
mkfs.xfs -l lazy-count=1 /dev/sdb1    # Enable lazy counting
```

#### Btrfs Filesystem
```bash
# Basic Btrfs creation
mkfs.btrfs /dev/sdb1                  # Create Btrfs filesystem
mkfs.btrfs -L "BACKUP" /dev/sdb1      # Create with label
mkfs.btrfs -f /dev/sdb1               # Force creation
mkfs.btrfs -d single /dev/sdb1        # Single device, no RAID

# Multi-device Btrfs
mkfs.btrfs -m raid1 -d raid1 /dev/sdb1 /dev/sdc1  # RAID1 setup
mkfs.btrfs -m raid10 -d raid10 /dev/sd{b,c,d,e}1  # RAID10 setup
mkfs.btrfs -d raid0 /dev/sdb1 /dev/sdc1           # RAID0 (striping)

# Btrfs with specific features
mkfs.btrfs --nodesize 16384 /dev/sdb1  # Node size (metadata block size)
mkfs.btrfs --sectorsize 4096 /dev/sdb1 # Sector size
mkfs.btrfs --features compress-lzo /dev/sdb1  # Enable LZO compression
```

#### Other Filesystem Types
```bash
# FAT32 filesystem
mkfs.vfat /dev/sdb1                   # Create FAT32 filesystem
mkfs.vfat -F 32 /dev/sdb1             # Force FAT32 (vs FAT16)
mkfs.vfat -n "USB_DRIVE" /dev/sdb1    # Create with volume label
mkfs.vfat -s 8 /dev/sdb1              # Sectors per cluster

# NTFS filesystem
mkfs.ntfs /dev/sdb1                   # Create NTFS filesystem
mkfs.ntfs -L "WINDOWS_DATA" /dev/sdb1 # Create with label
mkfs.ntfs -f /dev/sdb1                # Fast format
mkfs.ntfs -c 4096 /dev/sdb1           # Cluster size

# Swap space
mkswap /dev/sdb1                      # Create swap space
mkswap -L "SWAP" /dev/sdb1            # Create with label
mkswap -c /dev/sdb1                   # Check for bad blocks first
```

## Filesystem Tuning and Configuration

### ext4 Filesystem Tuning
```bash
# Display filesystem parameters
tune2fs -l /dev/sdb1                  # Show filesystem parameters
dumpe2fs -h /dev/sdb1                 # Show superblock information
dumpe2fs /dev/sdb1 | grep -A 5 -B 5 "Block size"  # Block size info

# Modify filesystem parameters
tune2fs -L "NEW_LABEL" /dev/sdb1      # Change filesystem label
tune2fs -U random /dev/sdb1           # Generate new UUID
tune2fs -U clear /dev/sdb1            # Clear UUID
tune2fs -c 0 /dev/sdb1                # Disable fsck check count
tune2fs -i 0 /dev/sdb1                # Disable fsck time interval
tune2fs -m 1 /dev/sdb1                # Set reserved blocks to 1%

# Default mount options
tune2fs -o acl,user_xattr /dev/sdb1   # Set default mount options
tune2fs -o ^acl /dev/sdb1              # Remove default mount option

# Journal configuration
tune2fs -j /dev/sdb1                  # Add journal to ext2 (convert to ext3)
tune2fs -J size=128 /dev/sdb1         # Resize journal (must be unmounted)

# Performance tuning
tune2fs -e remount-ro /dev/sdb1       # Set error behavior (remount read-only)
tune2fs -e continue /dev/sdb1         # Continue on errors
tune2fs -e panic /dev/sdb1            # Panic on errors
```

### XFS Filesystem Tuning
```bash
# XFS administration
xfs_admin -L "NEW_LABEL" /dev/sdb1    # Change XFS label
xfs_admin -U generate /dev/sdb1       # Generate new UUID
xfs_admin -U nil /dev/sdb1            # Clear UUID

# Display XFS information (requires mounting)
xfs_info /mnt/xfs                     # Show mounted XFS filesystem info
xfs_growfs /mnt/xfs                   # Grow XFS filesystem to fill device
xfs_growfs -D 10485760 /mnt/xfs       # Grow to specific size (blocks)

# XFS quota management
xfs_quota -x -c 'report -h' /mnt/xfs  # Show quota usage
xfs_quota -x -c 'limit -u bhard=1g user' /mnt/xfs  # Set user quota

# XFS defragmentation
xfs_fsr /mnt/xfs                      # Defragment XFS filesystem
xfs_fsr -v /mnt/xfs                   # Verbose defragmentation
```

### Btrfs Filesystem Management
```bash
# Btrfs filesystem operations
btrfs filesystem show                 # Show all Btrfs filesystems
btrfs filesystem usage /mnt/btrfs     # Show space usage
btrfs filesystem resize +10G /mnt/btrfs  # Grow filesystem by 10GB
btrfs filesystem resize max /mnt/btrfs   # Grow to maximum size

# Btrfs device management
btrfs device add /dev/sdc1 /mnt/btrfs    # Add device to filesystem
btrfs device remove /dev/sdc1 /mnt/btrfs # Remove device from filesystem
btrfs device scan                        # Scan for Btrfs devices

# Btrfs subvolumes
btrfs subvolume create /mnt/btrfs/home   # Create subvolume
btrfs subvolume list /mnt/btrfs          # List subvolumes
btrfs subvolume delete /mnt/btrfs/old    # Delete subvolume

# Btrfs snapshots
btrfs subvolume snapshot /mnt/btrfs/home /mnt/btrfs/home_backup
btrfs subvolume snapshot -r /mnt/btrfs/home /mnt/btrfs/home_readonly
```

## Filesystem Information and Identification
```bash
# Filesystem identification
blkid                                 # Show all filesystems with UUID and labels
blkid /dev/sdb1                       # Show specific filesystem info
file -s /dev/sdb1                     # Identify filesystem type
lsblk -f                              # Tree view with filesystem info
findmnt                               # Show mounted filesystems in tree format

# Detailed filesystem information
df -h                                 # Show mounted filesystem usage
df -i                                 # Show inode usage
du -sh /path/*                        # Directory sizes
stat /dev/sdb1                        # Device file statistics

# UUID and label management
blkid -o value -s UUID /dev/sdb1      # Get UUID only
blkid -o value -s LABEL /dev/sdb1     # Get label only
ls -la /dev/disk/by-uuid/             # List devices by UUID
ls -la /dev/disk/by-label/            # List devices by label
```

## Filesystem Checking and Repair

### ext4 Filesystem Checking
```bash
# Basic filesystem checking
fsck /dev/sdb1                        # Check filesystem (must be unmounted)
fsck -A                               # Check all filesystems in /etc/fstab
fsck -y /dev/sdb1                     # Auto-repair without prompting
fsck -f /dev/sdb1                     # Force check even if filesystem is clean
fsck -v /dev/sdb1                     # Verbose output
fsck -n /dev/sdb1                     # Read-only check (no modifications)

# ext-specific checking
e2fsck -p /dev/sdb1                   # Preen mode (auto-fix safe errors)
e2fsck -f -y /dev/sdb1                # Force check and auto-repair
e2fsck -n /dev/sdb1                   # Check without modifications
e2fsck -c /dev/sdb1                   # Check for bad blocks

# Advanced ext4 checking
e2fsck -cc /dev/sdb1                  # Check filesystem and bad blocks (destructive)
e2fsck -b 32768 /dev/sdb1             # Use alternate superblock
e2fsck -B 4096 /dev/sdb1              # Specify block size

# Repair damaged superblock
e2fsck -b 8193 /dev/sdb1              # Try backup superblock
mke2fs -n /dev/sdb1                   # Show superblock locations without creating
```

### XFS Filesystem Checking
```bash
# XFS filesystem checking
xfs_check /dev/sdb1                   # Check XFS filesystem (read-only)
xfs_repair /dev/sdb1                  # Repair XFS filesystem
xfs_repair -n /dev/sdb1               # Dry run (no modifications)
xfs_repair -v /dev/sdb1               # Verbose repair
xfs_repair -L /dev/sdb1               # Force repair (zero log)

# XFS log recovery
xfs_repair -L /dev/sdb1               # Clear log and repair
mount -o nouuid /dev/sdb1 /mnt        # Mount with duplicate UUID
```

### Btrfs Filesystem Checking
```bash
# Btrfs filesystem checking
btrfs check /dev/sdb1                 # Check Btrfs filesystem
btrfs check --repair /dev/sdb1        # Repair Btrfs filesystem
btrfs check --init-csum-tree /dev/sdb1 # Initialize checksum tree
btrfs check --init-extent-tree /dev/sdb1 # Initialize extent tree

# Btrfs scrub (online check)
btrfs scrub start /mnt/btrfs          # Start data integrity check (mounted)
btrfs scrub status /mnt/btrfs         # Check scrub status
btrfs scrub cancel /mnt/btrfs         # Cancel running scrub
btrfs scrub resume /mnt/btrfs         # Resume paused scrub

# Btrfs rescue operations
btrfs rescue chunk-recover /dev/sdb1  # Recover chunk tree
btrfs rescue super-recover /dev/sdb1  # Recover superblock
```

### Bad Block Detection and Recovery
```bash
# Bad block detection
badblocks -v /dev/sdb1                # Check for bad blocks (read-only)
badblocks -w /dev/sdb1                # Destructive write test
badblocks -n /dev/sdb1                # Non-destructive read-write test
badblocks -s /dev/sdb1                # Show progress

# Create bad block list
badblocks -o badblocks.txt /dev/sdb1  # Save bad blocks to file
e2fsck -l badblocks.txt /dev/sdb1     # Use bad block list during fsck

# Comprehensive filesystem health check
filesystem_health_check() {
    local device="$1"

    if [[ -z "$device" ]]; then
        echo "Usage: filesystem_health_check <device>"
        return 1
    fi

    echo "=== Filesystem Health Check: $device ==="

    # Check if mounted
    if mount | grep -q "$device"; then
        echo "WARNING: $device is currently mounted"
        mount_point=$(mount | grep "$device" | awk '{print $3}')
        echo "Mounted at: $mount_point"
        echo "Unmount before performing full check"
        return 1
    fi

    # Identify filesystem type
    fs_type=$(blkid -o value -s TYPE "$device")
    echo "Filesystem type: $fs_type"

    # Perform appropriate check
    case "$fs_type" in
        ext2|ext3|ext4)
            echo "Running ext filesystem check..."
            e2fsck -f -v "$device"
            ;;
        xfs)
            echo "Running XFS filesystem check..."
            xfs_repair -n "$device"
            ;;
        btrfs)
            echo "Running Btrfs filesystem check..."
            btrfs check "$device"
            ;;
        *)
            echo "Unsupported filesystem type: $fs_type"
            ;;
    esac

    # Check for bad blocks
    echo "Checking for bad blocks..."
    badblocks -sv "$device"

    echo "Health check completed"
}
```

## Filesystem Performance Optimization
```bash
# Filesystem-specific optimization
optimize_ext4() {
    local device="$1"
    local mount_point="$2"

    # Tune filesystem parameters
    tune2fs -m 1 "$device"              # Reduce reserved space
    tune2fs -c 0 "$device"              # Disable fsck count
    tune2fs -i 0 "$device"              # Disable fsck interval

    # Mount with optimized options
    mount -o noatime,nodiratime,data=writeback "$device" "$mount_point"
}

optimize_xfs() {
    local device="$1"
    local mount_point="$2"

    # Mount with optimized options
    mount -o noatime,nodiratime,allocsize=16m,largeio,inode64 "$device" "$mount_point"
}

# Performance testing
test_filesystem_performance() {
    local mount_point="$1"
    local test_file="$mount_point/performance_test"

    echo "=== Filesystem Performance Test: $mount_point ==="

    # Sequential write test
    echo "Sequential write test..."
    dd if=/dev/zero of="$test_file" bs=1M count=1000 oflag=sync 2>&1 | grep -E "copied|MB/s"

    # Sequential read test
    echo "Sequential read test..."
    dd if="$test_file" of=/dev/null bs=1M 2>&1 | grep -E "copied|MB/s"

    # Random I/O test (if fio is available)
    if command -v fio >/dev/null; then
        echo "Random I/O test..."
        fio --name=random_rw --ioengine=libaio --rw=randrw --bs=4k --direct=1 \
            --size=1G --numjobs=1 --runtime=60 --group_reporting \
            --filename="$test_file.fio"
    fi

    # Cleanup
    rm -f "$test_file" "$test_file.fio"
}
```