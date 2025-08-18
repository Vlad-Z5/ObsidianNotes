# Linux Storage Management

## Disk Partitioning

### Traditional Partitioning with fdisk

#### Basic fdisk Operations

```bash
# List all disks and partitions
fdisk -l                              # List all disks and their partitions
fdisk -l /dev/sda                     # List partitions on specific disk
lsblk                                 # Tree view of all block devices
lsblk -f                              # Include filesystem information

# Interactive partitioning
fdisk /dev/sdb                        # Enter fdisk interactive mode

# Common fdisk commands (within fdisk):
# n - create new partition
# d - delete partition
# p - print partition table
# t - change partition type
# a - toggle bootable flag
# w - write changes and exit
# q - quit without saving changes
# m - display help menu

# Example: Create a new primary partition
# fdisk /dev/sdb
# Command: n (new partition)
# Partition type: p (primary)
# Partition number: 1
# First sector: (default)
# Last sector: +10G (for 10GB partition)
# Command: w (write changes)

# Verify partition creation
partprobe /dev/sdb                    # Re-read partition table
cat /proc/partitions                  # Show kernel's partition table
```

#### Partition Management

```bash
# Check partition types
fdisk -l | grep "Linux swap"          # Find swap partitions
fdisk -l | grep "Linux filesystem"    # Find Linux filesystem partitions
fdisk -l | grep "LVM"                 # Find LVM partitions

# Create different partition types
# Within fdisk, use 't' command to change type:
# 82 - Linux swap
# 83 - Linux filesystem
# 8e - Linux LVM
# ef - EFI System Partition

# Example fdisk session for creating swap partition
cat << 'EOF'
fdisk /dev/sdb
n       # New partition
p       # Primary
2       # Partition number 2
(enter) # Default first sector
+2G     # 2GB size
t       # Change type
2       # Partition number 2
82      # Linux swap type
w       # Write changes
EOF
```

### Advanced Partitioning with parted

#### GPT Partitioning with parted

```bash
# parted - More powerful partitioning tool
parted --version                      # Check parted version
parted /dev/sdb print                 # Show current partition table
parted /dev/sdb print free            # Show free space

# Create GPT partition table (supports >2TB disks)
parted /dev/sdb mklabel gpt           # Create GPT partition table
parted /dev/sdb mklabel msdos         # Create MBR partition table (legacy)

# Interactive partitioning
parted /dev/sdb                       # Enter interactive mode
# Commands within parted:
# print - show partition table
# mkpart - create partition
# rm - remove partition
# resizepart - resize partition
# quit - exit

# Batch operations (non-interactive)
parted -s /dev/sdb mklabel gpt                    # Create GPT table
parted -s /dev/sdb mkpart primary 0% 50%         # Create first partition (50% of disk)
parted -s /dev/sdb mkpart primary 50% 100%       # Create second partition (remaining space)
parted -s /dev/sdb mkpart primary ext4 1MiB 10GiB # Create 10GB ext4 partition
parted -s /dev/sdb set 1 boot on                 # Set boot flag on partition 1

# Advanced partition creation
parted -s /dev/sdb mkpart ESP fat32 1MiB 513MiB   # EFI System Partition
parted -s /dev/sdb mkpart boot ext4 513MiB 1537MiB # Boot partition
parted -s /dev/sdb mkpart root ext4 1537MiB 100%  # Root partition
```

#### Partition Alignment and Optimization

```bash
# Check partition alignment
parted /dev/sdb align-check optimal 1  # Check if partition 1 is optimally aligned

# Create optimally aligned partitions
parted -s /dev/sdb mkpart primary 2048s 2097151s  # Use sector alignment
parted -s /dev/sdb mkpart primary 1MiB 1GiB       # Use MiB alignment (recommended)

# Show detailed information
parted /dev/sdb unit s print           # Show in sectors
parted /dev/sdb unit MiB print         # Show in MiB
parted /dev/sdb unit % print           # Show in percentages

# Resize partitions
parted /dev/sdb resizepart 1 20GiB     # Resize partition 1 to 20GiB
```

## Filesystem Management

### Creating Filesystems

#### Common Filesystem Types

```bash
# ext4 - Most common Linux filesystem
mkfs.ext4 /dev/sdb1                   # Create ext4 filesystem
mkfs.ext4 -L "DATA" /dev/sdb1         # Create with label "DATA"
mkfs.ext4 -b 4096 /dev/sdb1           # Specify block size (4KB)
mkfs.ext4 -m 1 /dev/sdb1              # Reserve 1% for root (default 5%)
mkfs.ext4 -E lazy_itable_init=0,lazy_journal_init=0 /dev/sdb1  # Initialize immediately

# XFS - High-performance filesystem
mkfs.xfs /dev/sdb1                    # Create XFS filesystem
mkfs.xfs -L "LOGS" /dev/sdb1          # Create with label "LOGS"
mkfs.xfs -b size=4096 /dev/sdb1       # Specify block size
mkfs.xfs -f /dev/sdb1                 # Force creation (overwrite existing)

# Btrfs - Modern copy-on-write filesystem
mkfs.btrfs /dev/sdb1                  # Create Btrfs filesystem
mkfs.btrfs -L "BACKUP" /dev/sdb1      # Create with label
mkfs.btrfs -d single /dev/sdb1        # Single device, no RAID
mkfs.btrfs -m raid1 -d raid1 /dev/sdb1 /dev/sdc1  # RAID1 setup

# Other filesystems
mkfs.vfat /dev/sdb1                   # FAT32 filesystem
mkfs.ntfs /dev/sdb1                   # NTFS filesystem
mkswap /dev/sdb1                      # Swap space
```

#### Filesystem Tuning and Configuration

```bash
# ext4 filesystem tuning
tune2fs -l /dev/sdb1                  # Show filesystem parameters
tune2fs -L "NEW_LABEL" /dev/sdb1      # Change filesystem label
tune2fs -c 0 /dev/sdb1                # Disable fsck check count
tune2fs -i 0 /dev/sdb1                # Disable fsck time interval
tune2fs -m 1 /dev/sdb1                # Set reserved blocks to 1%
tune2fs -o acl,user_xattr /dev/sdb1   # Set default mount options
tune2fs -U random /dev/sdb1           # Generate new UUID

# XFS filesystem tuning
xfs_admin -L "NEW_LABEL" /dev/sdb1     # Change XFS label
xfs_admin -U generate /dev/sdb1       # Generate new UUID
xfs_info /mnt/xfs                     # Show mounted XFS info (must be mounted)

# Check filesystem parameters
blkid /dev/sdb1                       # Show UUID, label, and filesystem type
file -s /dev/sdb1                     # Identify filesystem type
```

### Filesystem Checking and Repair

#### Filesystem Verification

```bash
# ext4 filesystem checking
fsck /dev/sdb1                        # Check filesystem (unmounted)
fsck -y /dev/sdb1                     # Auto-repair without prompting
fsck -f /dev/sdb1                     # Force check even if clean
fsck -v /dev/sdb1                     # Verbose output
e2fsck -p /dev/sdb1                   # Preen mode (auto-fix safe errors)
e2fsck -f -y /dev/sdb1               # Force check and auto-repair

# XFS filesystem checking
xfs_check /dev/sdb1                   # Check XFS filesystem (read-only)
xfs_repair /dev/sdb1                  # Repair XFS filesystem
xfs_repair -n /dev/sdb1               # Dry run (no modifications)
xfs_repair -L /dev/sdb1               # Force repair (zero log)

# Btrfs filesystem checking
btrfs check /dev/sdb1                 # Check Btrfs filesystem
btrfs check --repair /dev/sdb1        # Repair Btrfs filesystem
btrfs scrub start /mnt/btrfs          # Start data integrity check (mounted)
btrfs scrub status /mnt/btrfs         # Check scrub status

# Bad block detection
badblocks -v /dev/sdb1                # Check for bad blocks
badblocks -w /dev/sdb1                # Destructive write test
e2fsck -cc /dev/sdb1                  # Check filesystem and bad blocks
```

## Advanced Filesystem Management

### Btrfs Advanced Features

#### Subvolumes and Snapshots

```bash
# Btrfs subvolume management
btrfs subvolume create /mnt/btrfs/subvol1     # Create subvolume
btrfs subvolume list /mnt/btrfs               # List subvolumes
btrfs subvolume show /mnt/btrfs/subvol1       # Show subvolume info
btrfs subvolume delete /mnt/btrfs/subvol1     # Delete subvolume

# Btrfs snapshots
btrfs subvolume snapshot /mnt/btrfs/data /mnt/btrfs/data-snapshot  # Create snapshot
btrfs subvolume snapshot -r /mnt/btrfs/data /mnt/btrfs/data-readonly  # Read-only snapshot

# Btrfs filesystem operations
btrfs filesystem show                         # Show all Btrfs filesystems
btrfs filesystem usage /mnt/btrfs            # Show space usage
btrfs filesystem balance /mnt/btrfs          # Balance filesystem
btrfs filesystem defragment -r /mnt/btrfs    # Defragment recursively

# Btrfs device management
btrfs device add /dev/sdc1 /mnt/btrfs        # Add device to filesystem
btrfs device remove /dev/sdc1 /mnt/btrfs     # Remove device from filesystem
btrfs device scan                            # Scan for Btrfs devices
```

### ZFS Management (where available)

#### ZFS Pool and Dataset Management

```bash
# ZFS pool operations
zpool create mypool /dev/sdb                 # Create simple pool
zpool create mypool mirror /dev/sdb /dev/sdc # Create mirrored pool
zpool create mypool raidz /dev/sdb /dev/sdc /dev/sdd  # Create RAID-Z pool
zpool status                                 # Show pool status
zpool list                                   # List all pools
zpool destroy mypool                         # Destroy pool

# ZFS dataset operations
zfs create mypool/dataset1                   # Create dataset
zfs create -o mountpoint=/data mypool/data   # Create with custom mountpoint
zfs list                                     # List all datasets
zfs get all mypool/dataset1                  # Show all properties
zfs set compression=lz4 mypool/dataset1      # Enable compression
zfs destroy mypool/dataset1                  # Destroy dataset

# ZFS snapshots and clones
zfs snapshot mypool/dataset1@snap1           # Create snapshot
zfs list -t snapshot                         # List snapshots
zfs clone mypool/dataset1@snap1 mypool/clone1  # Create clone from snapshot
zfs rollback mypool/dataset1@snap1           # Rollback to snapshot
zfs destroy mypool/dataset1@snap1            # Destroy snapshot

# ZFS replication
zfs send mypool/dataset1@snap1 | zfs receive backup/dataset1  # Send/receive
zfs send -i @snap1 mypool/dataset1@snap2 | zfs receive backup/dataset1  # Incremental
```

## Logical Volume Management (LVM)

### LVM Setup and Configuration

#### Physical Volume Operations

```bash
# Initialize physical volumes
pvcreate /dev/sdb1                    # Create physical volume
pvcreate /dev/sdb1 /dev/sdc1         # Create multiple PVs
pvdisplay                            # Show detailed PV information
pvs                                  # Show brief PV summary
pvdisplay /dev/sdb1                  # Show specific PV details

# Physical volume management
pvresize /dev/sdb1                   # Resize PV after partition resize
pvremove /dev/sdb1                   # Remove PV (must be unused)
pvmove /dev/sdb1                     # Move data from PV to other PVs
pvchange -x n /dev/sdb1              # Disable allocation from PV
```

#### Volume Group Operations

```bash
# Create and manage volume groups
vgcreate vg_data /dev/sdb1 /dev/sdc1 # Create volume group from PVs
vgextend vg_data /dev/sdd1           # Add PV to existing VG
vgreduce vg_data /dev/sdd1           # Remove PV from VG
vgdisplay                            # Show detailed VG information
vgs                                  # Show brief VG summary
vgdisplay vg_data                    # Show specific VG details

# Volume group maintenance
vgrename vg_data vg_production       # Rename volume group
vgremove vg_data                     # Remove volume group (must be empty)
vgscan                               # Scan for volume groups
vgchange -a y vg_data                # Activate volume group
vgchange -a n vg_data                # Deactivate volume group
```

#### Logical Volume Operations

```bash
# Create logical volumes
lvcreate -L 10G -n lv_app vg_data           # Create 10GB logical volume
lvcreate -l 50%VG -n lv_data vg_data        # Use 50% of VG space
lvcreate -l 100%FREE -n lv_logs vg_data     # Use all free space
lvcreate -L 5G -n lv_tmp vg_data            # Create 5GB volume

# Logical volume management
lvdisplay                                   # Show detailed LV information
lvs                                         # Show brief LV summary
lvdisplay /dev/vg_data/lv_app              # Show specific LV details
lvrename vg_data lv_app lv_application     # Rename logical volume

# Resize logical volumes
lvextend -L +5G /dev/vg_data/lv_app        # Extend by 5GB
lvextend -l +100%FREE /dev/vg_data/lv_app  # Extend by all free space
lvreduce -L 5G /dev/vg_data/lv_app         # Reduce to 5GB (dangerous!)
lvresize -L 15G /dev/vg_data/lv_app        # Resize to exactly 15GB

# Remove logical volumes
lvremove /dev/vg_data/lv_app               # Remove logical volume
```

### LVM Advanced Features

#### LVM Snapshots

```bash
# Create snapshots
lvcreate -L 1G -s -n lv_app_snap /dev/vg_data/lv_app    # Create 1GB snapshot
lvcreate -l 10%ORIGIN -s -n lv_data_snap /dev/vg_data/lv_data  # 10% of origin size

# Snapshot management
lvdisplay /dev/vg_data/lv_app_snap         # Show snapshot information
lvs -a                                     # Show all LVs including snapshots

# Snapshot operations
mount /dev/vg_data/lv_app_snap /mnt/snap   # Mount snapshot for backup
lvconvert --merge /dev/vg_data/lv_app_snap # Merge snapshot back to origin
lvremove /dev/vg_data/lv_app_snap          # Remove snapshot
```

#### Filesystem Resizing with LVM

```bash
# Extend filesystem after LV extension
# For ext4 filesystems
lvextend -L +5G /dev/vg_data/lv_app        # Extend logical volume
resize2fs /dev/vg_data/lv_app              # Resize ext4 filesystem

# For XFS filesystems (must be mounted)
lvextend -L +5G /dev/vg_data/lv_logs       # Extend logical volume
xfs_growfs /mnt/logs                       # Resize XFS filesystem

# One-step resize (ext4 only)
lvextend -r -L +5G /dev/vg_data/lv_app     # Extend LV and resize filesystem

# Reduce filesystem and LV (ext4 only, dangerous!)
umount /mnt/app                            # Must unmount first
e2fsck -f /dev/vg_data/lv_app             # Check filesystem
resize2fs /dev/vg_data/lv_app 10G         # Shrink filesystem first
lvreduce -L 10G /dev/vg_data/lv_app       # Then shrink LV
mount /dev/vg_data/lv_app /mnt/app        # Remount
```

## Mount Management

### Manual Mounting and Unmounting

#### Basic Mount Operations

```bash
# Mount filesystems
mount /dev/sdb1 /mnt/data               # Mount with auto-detected filesystem
mount -t ext4 /dev/sdb1 /mnt/data       # Mount with specific filesystem type
mount -o ro /dev/sdb1 /mnt/data         # Mount read-only
mount -o rw,noatime /dev/sdb1 /mnt/data # Mount with specific options

# Special mounts
mount -t tmpfs tmpfs /mnt/temp          # Mount tmpfs (RAM disk)
mount -t proc proc /mnt/chroot/proc     # Mount proc filesystem
mount --bind /home /mnt/backup/home     # Bind mount
mount -o loop disk.img /mnt/loop        # Mount disk image

# Network mounts
mount -t nfs server:/path /mnt/nfs      # Mount NFS share
mount -t cifs //server/share /mnt/smb -o username=user  # Mount SMB/CIFS share

# Show mounted filesystems
mount                                   # Show all mounts
mount | grep /dev/sdb                   # Show specific device mounts
df -h                                   # Show mounted filesystems with usage
findmnt                                 # Tree view of mounts
findmnt /mnt/data                       # Show specific mount point
```

#### Unmounting

```bash
# Basic unmount
umount /mnt/data                        # Unmount by mount point
umount /dev/sdb1                        # Unmount by device

# Force unmount
umount -l /mnt/data                     # Lazy unmount (detach immediately)
umount -f /mnt/data                     # Force unmount (for network mounts)

# Find processes using mount point
lsof +D /mnt/data                       # List open files in directory
fuser -v /mnt/data                      # Show processes using mount point
fuser -km /mnt/data                     # Kill processes and unmount

# Check what's preventing unmount
lsof /mnt/data                          # Check open files
fuser -m /mnt/data                      # Show processes with files open
```

### Persistent Mounts with /etc/fstab

#### fstab Configuration

```bash
# /etc/fstab format:
# <device> <mount_point> <filesystem_type> <options> <dump> <fsck_order>

# Example /etc/fstab entries:
cat << 'EOF' >> /etc/fstab
# Local filesystems
/dev/sdb1           /data           ext4    defaults                    0  2
UUID=12345678-1234  /backup         xfs     defaults,noatime            0  2
/dev/vg_data/lv_app /opt/app        ext4    defaults,nodev,nosuid       0  2

# Swap
/dev/sdb2           none            swap    defaults                    0  0
/swapfile           none            swap    defaults                    0  0

# Network filesystems
server:/nfs/share   /mnt/nfs        nfs     defaults,_netdev            0  0
//server/share      /mnt/smb        cifs    credentials=/etc/cifs-creds 0  0

# Special filesystems
tmpfs               /tmp            tmpfs   defaults,size=2G,mode=1777  0  0
proc                /proc           proc    defaults                    0  0
sysfs               /sys            sysfs   defaults                    0  0
EOF

# Mount options explained:
# defaults      - rw,suid,dev,exec,auto,nouser,async
# noatime       - Don't update access times
# nodiratime    - Don't update directory access times
# nodev         - Don't interpret character/block special devices
# nosuid        - Don't allow set-user-ID or set-group-ID bits
# noexec        - Don't allow execution of binaries
# ro            - Read-only
# rw            - Read-write
# auto          - Mount automatically at boot
# noauto        - Don't mount automatically
# user          - Allow ordinary users to mount
# nouser        - Only root can mount
# _netdev       - Network device (wait for network)
```

#### fstab Management

```bash
# Test fstab entries
mount -a                                # Mount all entries in fstab
mount -av                               # Verbose mount all
mount /data                             # Mount specific entry (if in fstab)

# Validate fstab
findmnt --verify                        # Verify fstab syntax
mount -fav                              # Fake mount (test without mounting)

# Backup and restore fstab
cp /etc/fstab /etc/fstab.backup         # Backup fstab
# Edit fstab carefully with:
# vim /etc/fstab
# nano /etc/fstab

# Generate UUID for fstab entries
blkid /dev/sdb1                         # Get UUID for device
# Use UUID instead of device names for reliability:
# UUID=12345678-1234-1234-1234-123456789012 /data ext4 defaults 0 2
```

## Storage Performance and Monitoring

### Storage Performance Analysis

#### I/O Monitoring Tools

```bash
# iostat - I/O statistics
iostat                                  # Basic I/O stats
iostat -x 1                             # Extended stats every second
iostat -x -d 5 10                       # Device stats, 5-second intervals, 10 times

# Key iostat fields:
# r/s, w/s          - Read/write operations per second
# rkB/s, wkB/s      - KB read/written per second
# await             - Average wait time for I/O requests
# %util             - Percentage of time device was busy

# iotop - I/O usage by process
iotop                                   # Interactive I/O monitor
iotop -o                                # Only show processes with I/O
iotop -a                                # Show accumulated I/O
iotop -k                                # Use kilobytes instead of percentages

# Storage device information
lsblk -d -o NAME,SIZE,MODEL,VENDOR      # List storage devices
hdparm -I /dev/sda                      # ATA/SATA disk information
smartctl -a /dev/sda                    # SMART disk health information
```

#### Performance Testing

```bash
# Disk performance testing with dd
# Sequential write test
dd if=/dev/zero of=/tmp/testfile bs=1M count=1000 oflag=direct
# Sequential read test
dd if=/tmp/testfile of=/dev/null bs=1M iflag=direct
# Clean up
rm /tmp/testfile

# Random I/O testing with fio
fio --name=random-write --ioengine=posixaio --rw=randwrite --bs=4k --size=4g --numjobs=1 --iodepth=1 --runtime=60 --time_based --end_fsync=1
fio --name=random-read --ioengine=posixaio --rw=randread --bs=4k --size=4g --numjobs=1 --iodepth=1 --runtime=60 --time_based

# Filesystem benchmark
bonnie++ -u root -d /tmp -s 2g          # Comprehensive filesystem benchmark
```

### Storage Optimization

#### Filesystem Optimization

```bash
# I/O scheduler optimization
# Check current scheduler
cat /sys/block/sda/queue/scheduler

# Set I/O scheduler
echo noop > /sys/block/sda/queue/scheduler      # For SSDs
echo deadline > /sys/block/sda/queue/scheduler  # For HDDs
echo cfq > /sys/block/sda/queue/scheduler       # For mixed workloads

# Persistent I/O scheduler setting
cat << 'EOF' > /etc/udev/rules.d/60-scheduler.rules
# Set noop scheduler for SSDs
ACTION=="add|change", KERNEL=="sd[a-z]", ATTR{queue/rotational}=="0", ATTR{queue/scheduler}="noop"
# Set deadline scheduler for HDDs
ACTION=="add|change", KERNEL=="sd[a-z]", ATTR{queue/rotational}=="1", ATTR{queue/scheduler}="deadline"
EOF

# Mount options for performance
# For SSDs:
mount -o noatime,discard /dev/sdb1 /mnt/ssd
# For databases:
mount -o noatime,barrier=0 /dev/sdb1 /mnt/db    # Only if using battery-backed RAID
# For general use:
mount -o noatime,relatime /dev/sdb1 /mnt/data
```

This comprehensive Linux storage management guide covers everything from basic partitioning to advanced LVM and filesystem management, providing essential knowledge for effective storage administration in DevOps environments.