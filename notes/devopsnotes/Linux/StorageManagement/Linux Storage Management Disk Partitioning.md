# Linux Storage Management Disk Partitioning

**Disk Partitioning** covers traditional fdisk operations and advanced GPT partitioning with parted for effective disk layout management and optimization.

## Traditional Partitioning with fdisk

### Basic fdisk Operations
```bash
# List all disks and partitions
fdisk -l                              # List all disks and their partitions
fdisk -l /dev/sda                     # List partitions on specific disk
fdisk -l /dev/sd*                     # List all SATA/SCSI disk partitions
lsblk                                 # Tree view of all block devices
lsblk -f                              # Include filesystem information
lsblk -o NAME,SIZE,TYPE,MOUNTPOINT    # Custom column output

# Device information
ls -la /dev/disk/by-id/               # Disks by hardware ID
ls -la /dev/disk/by-uuid/             # Disks by UUID
ls -la /dev/disk/by-label/            # Disks by filesystem label
cat /proc/partitions                  # Kernel's view of partitions

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
# l - list partition type codes

# Verify partition creation
partprobe /dev/sdb                    # Re-read partition table
partprobe                             # Re-read all partition tables
udevadm settle                        # Wait for udev to process changes
```

### Partition Creation Examples
```bash
# Example: Create a new primary partition
# fdisk /dev/sdb
# Command: n (new partition)
# Partition type: p (primary)
# Partition number: 1
# First sector: (default - press Enter)
# Last sector: +10G (for 10GB partition)
# Command: w (write changes)

# Automated partition creation script
create_partition() {
    local device="$1"
    local size="$2"
    local type="${3:-83}"  # Default to Linux filesystem

    echo "Creating partition on $device with size $size"

    # Use fdisk with here document
    fdisk "$device" << EOF
n
p
1

+${size}
t
${type}
w
EOF

    partprobe "$device"
    echo "Partition created successfully"
}

# Usage examples
create_partition /dev/sdb 10G 83      # 10GB Linux filesystem
create_partition /dev/sdc 2G 82       # 2GB swap partition
create_partition /dev/sdd 50G 8e      # 50GB LVM partition
```

### Partition Management
```bash
# Check partition types
fdisk -l | grep "Linux swap"          # Find swap partitions
fdisk -l | grep "Linux filesystem"    # Find Linux filesystem partitions
fdisk -l | grep "LVM"                 # Find LVM partitions

# Common partition type codes:
# 82 - Linux swap
# 83 - Linux filesystem
# 8e - Linux LVM
# ef - EFI System Partition
# fd - Linux RAID autodetect
# 07 - HPFS/NTFS/exFAT

# Example: Create swap partition
cat << 'EOF' > create_swap_partition.sh
#!/bin/bash
# Create swap partition

DEVICE="$1"
SIZE="$2"

if [[ -z "$DEVICE" || -z "$SIZE" ]]; then
    echo "Usage: $0 <device> <size>"
    echo "Example: $0 /dev/sdb 2G"
    exit 1
fi

echo "Creating swap partition on $DEVICE with size $SIZE"

fdisk "$DEVICE" << FDISK_EOF
n
p
2

+${SIZE}
t
2
82
w
FDISK_EOF

partprobe "$DEVICE"

# Format as swap
mkswap "${DEVICE}2"
echo "Swap partition created and formatted"
EOF

chmod +x create_swap_partition.sh

# Delete partitions safely
delete_partition() {
    local device="$1"
    local partition_num="$2"

    echo "WARNING: This will delete partition $partition_num on $device"
    read -p "Are you sure? (yes/no): " confirm

    if [[ "$confirm" == "yes" ]]; then
        fdisk "$device" << EOF
d
${partition_num}
w
EOF
        partprobe "$device"
        echo "Partition deleted"
    else
        echo "Operation cancelled"
    fi
}
```

## Advanced Partitioning with parted

### GPT Partitioning with parted
```bash
# parted - More powerful partitioning tool
parted --version                      # Check parted version
parted /dev/sdb print                 # Show current partition table
parted /dev/sdb print free            # Show free space
parted /dev/sdb print all             # Show all devices

# Create partition tables
parted /dev/sdb mklabel gpt           # Create GPT partition table (supports >2TB)
parted /dev/sdb mklabel msdos         # Create MBR partition table (legacy)

# Interactive partitioning
parted /dev/sdb                       # Enter interactive mode
# Commands within parted:
# print - show partition table
# mkpart - create partition
# rm - remove partition
# resizepart - resize partition
# name - set partition name (GPT only)
# set - set partition flags
# quit - exit

# Check disk label type
parted /dev/sdb print | grep "Partition Table"
```

### Batch Operations (Non-interactive)
```bash
# Complete disk setup with parted
setup_gpt_disk() {
    local device="$1"

    echo "Setting up GPT disk: $device"

    # Create GPT partition table
    parted -s "$device" mklabel gpt

    # Create EFI System Partition (512MB)
    parted -s "$device" mkpart ESP fat32 1MiB 513MiB
    parted -s "$device" set 1 esp on

    # Create boot partition (1GB)
    parted -s "$device" mkpart boot ext4 513MiB 1537MiB
    parted -s "$device" set 2 boot on

    # Create root partition (remaining space)
    parted -s "$device" mkpart root ext4 1537MiB 100%

    # Verify creation
    parted "$device" print
}

# Percentage-based partitioning
parted -s /dev/sdb mklabel gpt                    # Create GPT table
parted -s /dev/sdb mkpart primary 0% 25%         # 25% of disk
parted -s /dev/sdb mkpart primary 25% 75%        # 50% of disk (25%-75%)
parted -s /dev/sdb mkpart primary 75% 100%       # Remaining 25%

# Size-based partitioning
parted -s /dev/sdb mkpart primary ext4 1MiB 10GiB    # 10GB partition
parted -s /dev/sdb mkpart primary linux-swap 10GiB 12GiB  # 2GB swap
parted -s /dev/sdb mkpart primary ext4 12GiB 100%    # Remaining space

# Set partition flags
parted -s /dev/sdb set 1 boot on                 # Set boot flag
parted -s /dev/sdb set 1 esp on                  # Set ESP flag (EFI)
parted -s /dev/sdb set 2 swap on                 # Set swap flag
```

### Partition Alignment and Optimization
```bash
# Check partition alignment
parted /dev/sdb align-check optimal 1  # Check if partition 1 is optimally aligned
parted /dev/sdb align-check minimal 1  # Check minimal alignment

# Create optimally aligned partitions
parted -s /dev/sdb mkpart primary 2048s 2097151s  # Use sector alignment
parted -s /dev/sdb mkpart primary 1MiB 1GiB       # Use MiB alignment (recommended)

# Show partition information in different units
parted /dev/sdb unit s print           # Show in sectors
parted /dev/sdb unit MiB print         # Show in MiB
parted /dev/sdb unit GiB print         # Show in GiB
parted /dev/sdb unit % print           # Show in percentages
parted /dev/sdb unit B print           # Show in bytes

# Calculate optimal alignment
get_optimal_alignment() {
    local device="$1"

    echo "Alignment information for $device:"
    parted "$device" print | grep -E "Model|Sector size|Partition Table"

    # Check if device supports alignment info
    if parted "$device" align-check optimal 1 2>/dev/null; then
        echo "Device supports alignment checking"
    else
        echo "Device may not support alignment checking"
    fi
}
```

### Advanced Partitioning Scenarios
```bash
# UEFI boot disk setup
setup_uefi_boot_disk() {
    local device="$1"
    local root_size="${2:-50GiB}"

    echo "Setting up UEFI boot disk on $device"

    # Verify device exists
    if [[ ! -b "$device" ]]; then
        echo "Error: Device $device not found"
        return 1
    fi

    # Create GPT partition table
    parted -s "$device" mklabel gpt

    # EFI System Partition (512MB, FAT32)
    parted -s "$device" mkpart ESP fat32 1MiB 513MiB
    parted -s "$device" set 1 esp on

    # Boot partition (1GB, ext4)
    parted -s "$device" mkpart boot ext4 513MiB 1537MiB

    # Root partition (specified size, ext4)
    parted -s "$device" mkpart root ext4 1537MiB "$root_size"

    # Home partition (remaining space, ext4)
    parted -s "$device" mkpart home ext4 "$root_size" 100%

    echo "Partitions created. Use mkfs to format filesystems."
    parted "$device" print
}

# Resize partition safely
resize_partition() {
    local device="$1"
    local partition_num="$2"
    local new_size="$3"

    echo "Resizing partition $partition_num on $device to $new_size"

    # Check filesystem type first
    fs_type=$(lsblk -f "${device}${partition_num}" -o FSTYPE --noheadings)

    echo "Filesystem type: $fs_type"
    echo "WARNING: Always backup data before resizing!"
    read -p "Continue? (yes/no): " confirm

    if [[ "$confirm" == "yes" ]]; then
        # Unmount if mounted
        umount "${device}${partition_num}" 2>/dev/null

        # Check filesystem first
        case "$fs_type" in
            ext2|ext3|ext4)
                e2fsck -f "${device}${partition_num}"
                ;;
            xfs)
                xfs_repair "${device}${partition_num}"
                ;;
        esac

        # Resize partition
        parted "$device" resizepart "$partition_num" "$new_size"

        # Resize filesystem
        case "$fs_type" in
            ext2|ext3|ext4)
                resize2fs "${device}${partition_num}"
                ;;
            xfs)
                # XFS requires mounting first
                mkdir -p /tmp/xfs_resize
                mount "${device}${partition_num}" /tmp/xfs_resize
                xfs_growfs /tmp/xfs_resize
                umount /tmp/xfs_resize
                ;;
        esac

        echo "Resize completed"
    fi
}

# Clone partition table
clone_partition_table() {
    local source_device="$1"
    local target_device="$2"

    echo "Cloning partition table from $source_device to $target_device"

    # Backup original partition table
    sfdisk -d "$source_device" > "/tmp/partition_backup_$(basename $source_device).sfdisk"

    # Clone partition table
    sfdisk -d "$source_device" | sfdisk "$target_device"

    echo "Partition table cloned. Backup saved to /tmp/"
    echo "Note: Filesystems are not copied, only partition structure"
}

# Partition table backup and restore
backup_partition_table() {
    local device="$1"
    local backup_file="${2:-partition_table_$(basename $device)_$(date +%Y%m%d_%H%M%S).backup}"

    echo "Backing up partition table for $device"

    # sfdisk backup (works for both MBR and GPT)
    sfdisk -d "$device" > "$backup_file"

    # Additional GPT backup
    if parted "$device" print | grep -q "gpt"; then
        sgdisk --backup="${backup_file}.gpt" "$device"
    fi

    echo "Partition table backed up to: $backup_file"
}

restore_partition_table() {
    local device="$1"
    local backup_file="$2"

    if [[ ! -f "$backup_file" ]]; then
        echo "Error: Backup file $backup_file not found"
        return 1
    fi

    echo "WARNING: This will overwrite the partition table on $device"
    read -p "Are you sure? (yes/no): " confirm

    if [[ "$confirm" == "yes" ]]; then
        sfdisk "$device" < "$backup_file"
        partprobe "$device"
        echo "Partition table restored"
    fi
}
```

### Partition Management Tools
```bash
# Comprehensive partition information
show_partition_info() {
    local device="$1"

    echo "=== Partition Information for $device ==="

    # Basic information
    echo "Device information:"
    lsblk "$device"
    echo

    # Detailed partition table
    echo "Partition table (parted):"
    parted "$device" print 2>/dev/null
    echo

    # Filesystem information
    echo "Filesystem information:"
    lsblk -f "$device"
    echo

    # Disk usage if mounted
    echo "Disk usage (mounted partitions):"
    df -h | grep "$device" || echo "No mounted partitions found"
}

# Check partition health
check_partition_health() {
    local device="$1"

    echo "=== Partition Health Check for $device ==="

    # Check for bad blocks
    echo "Checking for bad blocks..."
    badblocks -sv "$device" || echo "badblocks check failed or not available"

    # Check filesystem (if partition is specified)
    if [[ "$device" =~ [0-9]$ ]]; then
        fs_type=$(lsblk -f "$device" -o FSTYPE --noheadings)
        echo "Filesystem type: $fs_type"

        case "$fs_type" in
            ext2|ext3|ext4)
                echo "Running e2fsck check..."
                e2fsck -n "$device"  # Read-only check
                ;;
            xfs)
                echo "Running xfs_check..."
                xfs_db -r -c check "$device"
                ;;
            *)
                echo "No filesystem check available for $fs_type"
                ;;
        esac
    fi
}
```