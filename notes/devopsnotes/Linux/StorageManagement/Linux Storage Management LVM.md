# Linux Storage Management LVM

**Logical Volume Management (LVM)** provides flexible disk management through physical volumes, volume groups, and logical volumes, enabling dynamic storage allocation and advanced features like snapshots.

## LVM Setup and Configuration

### Physical Volume Operations

#### Creating and Managing Physical Volumes
```bash
# Initialize physical volumes
pvcreate /dev/sdb1                   # Create physical volume from partition
pvcreate /dev/sdb1 /dev/sdc1         # Create multiple PVs simultaneously
pvcreate --metadatasize 128k /dev/sdb1  # Specify metadata size
pvcreate -ff /dev/sdb1               # Force creation (overwrite existing)

# Display physical volume information
pvdisplay                            # Show detailed PV information
pvs                                  # Show brief PV summary
pvscan                               # Scan and list all PVs
pvdisplay /dev/sdb1                  # Show specific PV details
pvs -o +pv_used                      # Show additional columns

# Physical volume attributes
pvs -o pv_name,pv_size,pv_free,vg_name  # Custom column display
pvs --units g                        # Display sizes in GB
pvs --units m                        # Display sizes in MB
```

#### Physical Volume Maintenance
```bash
# Resize physical volume after partition expansion
pvresize /dev/sdb1                   # Resize PV to match partition size
pvresize --setphysicalvolumesize 50G /dev/sdb1  # Set specific size

# Move data from a physical volume
pvmove /dev/sdb1                     # Move all data from PV to other PVs in VG
pvmove /dev/sdb1 /dev/sdc1           # Move data to specific target PV
pvmove -n lv_data /dev/sdb1          # Move only specific logical volume

# Physical volume allocation
pvchange -x n /dev/sdb1              # Disable allocation from PV
pvchange -x y /dev/sdb1              # Enable allocation to PV

# Remove physical volume
pvremove /dev/sdb1                   # Remove PV (must be unused and removed from VG)

# Check physical volume consistency
pvck /dev/sdb1                       # Check PV metadata consistency
```

### Volume Group Operations

#### Creating and Managing Volume Groups
```bash
# Create volume groups
vgcreate vg_data /dev/sdb1 /dev/sdc1 # Create VG from multiple PVs
vgcreate -s 32M vg_data /dev/sdb1    # Specify physical extent size (32MB)
vgcreate --clustered y vg_cluster /dev/sdb1  # Create clustered VG

# Extend and reduce volume groups
vgextend vg_data /dev/sdd1           # Add PV to existing VG
vgreduce vg_data /dev/sdd1           # Remove PV from VG (must move data first)
vgreduce --removemissing vg_data     # Remove missing PVs from VG

# Display volume group information
vgdisplay                            # Show detailed VG information
vgs                                  # Show brief VG summary
vgscan                               # Scan for volume groups
vgdisplay vg_data                    # Show specific VG details
vgs -o +vg_free_count,vg_extent_count  # Show extent information
```

#### Volume Group Administration
```bash
# Volume group state management
vgchange -a y vg_data                # Activate volume group
vgchange -a n vg_data                # Deactivate volume group
vgchange -a y                        # Activate all volume groups

# Volume group maintenance
vgrename vg_data vg_production       # Rename volume group
vgremove vg_data                     # Remove volume group (must be empty)
vgcfgbackup vg_data                  # Backup VG configuration
vgcfgrestore vg_data                 # Restore VG configuration

# Volume group export/import
vgexport vg_data                     # Export VG (makes it inactive and unknown)
vgimport vg_data                     # Import previously exported VG

# Split volume group
vgsplit vg_data vg_new /dev/sdc1     # Split VG, move PV to new VG
vgmerge vg_data vg_old               # Merge VGs together

# Volume group monitoring
vgs --units g -o vg_name,vg_size,vg_free,vg_free_percent  # Space usage
watch 'vgs --units g'                # Monitor VG space in real-time
```

### Logical Volume Operations

#### Creating Logical Volumes
```bash
# Basic logical volume creation
lvcreate -L 10G -n lv_app vg_data           # Create 10GB logical volume
lvcreate -l 2560 -n lv_data vg_data         # Create using extent count
lvcreate -l 50%VG -n lv_data vg_data        # Use 50% of VG space
lvcreate -l 100%FREE -n lv_logs vg_data     # Use all free space

# Logical volume with specific properties
lvcreate -L 5G -n lv_tmp vg_data --addtag temp  # Add tag to LV
lvcreate -L 5G -n lv_cache vg_data --type cache  # Create cache volume
lvcreate -L 5G -n lv_thin vg_data --type thin    # Create thin volume

# Striped logical volumes (for performance)
lvcreate -L 10G -i 2 -I 64 -n lv_stripe vg_data  # Stripe across 2 PVs, 64KB stripe size
lvcreate -L 10G -i 3 -n lv_stripe3 vg_data       # Stripe across 3 PVs

# Mirrored logical volumes (for redundancy)
lvcreate -L 10G -m 1 -n lv_mirror vg_data        # Create mirrored LV
lvcreate -L 10G -m 2 -n lv_mirror3 vg_data       # Triple mirror
```

#### Logical Volume Management
```bash
# Display logical volume information
lvdisplay                                  # Show detailed LV information
lvs                                        # Show brief LV summary
lvscan                                     # Scan and list all LVs
lvdisplay /dev/vg_data/lv_app              # Show specific LV details
lvs -o +lv_layout,stripes,stripe_size      # Show layout information

# Logical volume state management
lvchange -a y /dev/vg_data/lv_app          # Activate logical volume
lvchange -a n /dev/vg_data/lv_app          # Deactivate logical volume
lvchange -p r /dev/vg_data/lv_app          # Set to read-only
lvchange -p rw /dev/vg_data/lv_app         # Set to read-write

# Rename logical volume
lvrename vg_data lv_app lv_application     # Rename logical volume
lvrename /dev/vg_data/lv_old /dev/vg_data/lv_new  # Alternative syntax
```

### Logical Volume Resizing

#### Extending Logical Volumes
```bash
# Extend logical volume size
lvextend -L +5G /dev/vg_data/lv_app        # Extend by 5GB
lvextend -L 20G /dev/vg_data/lv_app        # Extend to total 20GB
lvextend -l +100%FREE /dev/vg_data/lv_app  # Extend by all free space
lvextend -l +50 /dev/vg_data/lv_app        # Extend by 50 extents

# Extend with automatic filesystem resize
lvextend -r -L +5G /dev/vg_data/lv_app     # Extend LV and resize filesystem (ext4/xfs)
lvextend -r -l +100%FREE /dev/vg_data/lv_app  # Use all free space and resize FS
```

#### Reducing Logical Volumes
```bash
# Reduce logical volume (DANGEROUS - always backup first!)
# Note: XFS filesystems cannot be reduced, only ext2/3/4

# Step-by-step reduction for ext4
umount /mnt/app                           # Unmount filesystem
e2fsck -f /dev/vg_data/lv_app             # Force filesystem check
resize2fs /dev/vg_data/lv_app 10G         # Shrink filesystem first
lvreduce -L 10G /dev/vg_data/lv_app       # Then reduce LV
mount /dev/vg_data/lv_app /mnt/app        # Remount

# One-step reduction (ext4 only)
lvreduce -r -L 10G /dev/vg_data/lv_app    # Reduce LV and filesystem together

# Resize to specific size
lvresize -L 15G /dev/vg_data/lv_app       # Resize to exactly 15GB
lvresize -r -L 15G /dev/vg_data/lv_app    # Resize LV and filesystem
```

## LVM Advanced Features

### LVM Snapshots

#### Creating and Managing Snapshots
```bash
# Create snapshots
lvcreate -L 1G -s -n lv_app_snap /dev/vg_data/lv_app    # Create 1GB snapshot
lvcreate -l 10%ORIGIN -s -n lv_data_snap /dev/vg_data/lv_data  # 10% of origin size
lvcreate -L 2G -s -n backup_snap /dev/vg_data/lv_data --permission r  # Read-only snapshot

# Snapshot information
lvdisplay /dev/vg_data/lv_app_snap         # Show snapshot details
lvs -a                                     # Show all LVs including snapshots
lvs -o +snap_percent                       # Show snapshot usage percentage

# Using snapshots for backup
mount /dev/vg_data/lv_app_snap /mnt/snap   # Mount snapshot for backup
tar czf /backup/app_backup.tar.gz -C /mnt/snap .  # Backup from snapshot
umount /mnt/snap                           # Unmount snapshot

# Snapshot operations
lvconvert --merge /dev/vg_data/lv_app_snap # Merge snapshot back to origin
lvremove /dev/vg_data/lv_app_snap          # Remove snapshot

# Automated snapshot script
cat << 'EOF' > /usr/local/bin/lvm-snapshot
#!/bin/bash
# LVM snapshot management script

LV_PATH="$1"
SNAP_SIZE="$2"
RETENTION_DAYS="${3:-7}"

if [[ -z "$LV_PATH" || -z "$SNAP_SIZE" ]]; then
    echo "Usage: $0 <lv_path> <snapshot_size> [retention_days]"
    echo "Example: $0 /dev/vg_data/lv_app 1G 7"
    exit 1
fi

VG_NAME=$(lvs --noheadings -o vg_name "$LV_PATH" | tr -d ' ')
LV_NAME=$(lvs --noheadings -o lv_name "$LV_PATH" | tr -d ' ')
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
SNAP_NAME="${LV_NAME}_snap_${TIMESTAMP}"

# Create snapshot
echo "Creating snapshot: $SNAP_NAME"
lvcreate -L "$SNAP_SIZE" -s -n "$SNAP_NAME" "$LV_PATH"

# Cleanup old snapshots
echo "Cleaning up snapshots older than $RETENTION_DAYS days"
cutoff_date=$(date -d "$RETENTION_DAYS days ago" +%Y%m%d)

lvs --noheadings -o lv_name "$VG_NAME" | grep "${LV_NAME}_snap_" | while read -r snap; do
    snap_date=$(echo "$snap" | sed "s/${LV_NAME}_snap_//" | cut -d_ -f1 | tr -d ' ')

    if [[ "$snap_date" < "$cutoff_date" ]]; then
        echo "Removing old snapshot: $snap"
        lvremove -f "/dev/$VG_NAME/$snap"
    fi
done

echo "Snapshot management completed"
EOF

chmod +x /usr/local/bin/lvm-snapshot
```

### Filesystem Resizing with LVM

#### Extending Filesystems
```bash
# Extend ext4 filesystem after LV extension
lvextend -L +5G /dev/vg_data/lv_app        # Extend logical volume
resize2fs /dev/vg_data/lv_app              # Resize ext4 filesystem

# Extend XFS filesystem (must be mounted)
lvextend -L +5G /dev/vg_data/lv_logs       # Extend logical volume
xfs_growfs /mnt/logs                       # Resize XFS filesystem (must be mounted)

# One-step resize for ext4/xfs
lvextend -r -L +5G /dev/vg_data/lv_app     # Extend LV and resize filesystem automatically

# Check filesystem before and after
df -h                                      # Check filesystem size before
lvextend -r -L +5G /dev/vg_data/lv_app     # Extend
df -h                                      # Verify new size
```

#### Comprehensive Resize Script
```bash
# Complete LVM and filesystem resize script
cat << 'EOF' > /usr/local/bin/lvm-resize
#!/bin/bash
# LVM and filesystem resize script

LV_PATH="$1"
SIZE="$2"
OPERATION="${3:-extend}"  # extend or reduce

if [[ -z "$LV_PATH" || -z "$SIZE" ]]; then
    echo "Usage: $0 <lv_path> <size> [extend|reduce]"
    echo "Example: $0 /dev/vg_data/lv_app +5G extend"
    echo "Example: $0 /dev/vg_data/lv_app 10G reduce"
    exit 1
fi

# Get filesystem type
FS_TYPE=$(blkid -o value -s TYPE "$LV_PATH")
MOUNT_POINT=$(findmnt -n -o TARGET "$LV_PATH")

echo "=== LVM Resize Operation ==="
echo "Logical Volume: $LV_PATH"
echo "Filesystem Type: $FS_TYPE"
echo "Mount Point: $MOUNT_POINT"
echo "Size: $SIZE"
echo "Operation: $OPERATION"
echo

case "$OPERATION" in
    extend)
        echo "Extending logical volume..."

        if [[ "$FS_TYPE" == "xfs" ]]; then
            # XFS must be mounted for resize
            if [[ -z "$MOUNT_POINT" ]]; then
                echo "Error: XFS filesystem must be mounted for resizing"
                exit 1
            fi
            lvextend -L "$SIZE" "$LV_PATH"
            xfs_growfs "$MOUNT_POINT"
        else
            # ext2/3/4 can use automatic resize
            lvextend -r -L "$SIZE" "$LV_PATH"
        fi
        ;;

    reduce)
        if [[ "$FS_TYPE" == "xfs" ]]; then
            echo "Error: XFS filesystems cannot be reduced"
            exit 1
        fi

        echo "WARNING: Reducing filesystem size can cause data loss!"
        read -p "Are you sure you want to continue? (yes/no): " confirm

        if [[ "$confirm" != "yes" ]]; then
            echo "Operation cancelled"
            exit 0
        fi

        # Must unmount for reduction
        if [[ -n "$MOUNT_POINT" ]]; then
            echo "Unmounting filesystem..."
            umount "$MOUNT_POINT"
        fi

        echo "Checking filesystem..."
        e2fsck -f "$LV_PATH"

        echo "Reducing filesystem..."
        resize2fs "$LV_PATH" "$SIZE"

        echo "Reducing logical volume..."
        lvreduce -L "$SIZE" "$LV_PATH"

        # Remount if it was mounted before
        if [[ -n "$MOUNT_POINT" ]]; then
            echo "Remounting filesystem..."
            mount "$LV_PATH" "$MOUNT_POINT"
        fi
        ;;

    *)
        echo "Error: Invalid operation. Use 'extend' or 'reduce'"
        exit 1
        ;;
esac

echo "Resize operation completed successfully"
df -h "$MOUNT_POINT" 2>/dev/null || echo "Filesystem not mounted"
EOF

chmod +x /usr/local/bin/lvm-resize
```

### LVM Monitoring and Maintenance

#### LVM Status and Health Monitoring
```bash
# Monitor LVM health
lvs -o +lv_health_status                  # Show health status
vgs -o +vg_missing_pv_count               # Show missing PV count
pvs -o +pv_missing                        # Show missing PVs

# LVM system monitoring script
cat << 'EOF' > /usr/local/bin/lvm-monitor
#!/bin/bash
# LVM health monitoring script

echo "=== LVM Health Monitor ==="
echo "Date: $(date)"
echo

# Check for missing PVs
echo "Checking for missing Physical Volumes..."
missing_pvs=$(pvs -o +pv_missing --noheadings | grep -c "missing")
if [[ $missing_pvs -gt 0 ]]; then
    echo "WARNING: $missing_pvs missing physical volumes detected!"
    pvs -o +pv_missing | grep "missing"
else
    echo "All physical volumes are present"
fi
echo

# Check volume group health
echo "Volume Group Status:"
vgs -o vg_name,vg_attr,vg_size,vg_free,vg_missing_pv_count
echo

# Check logical volume health
echo "Logical Volume Status:"
lvs -o lv_name,vg_name,lv_attr,lv_size,lv_health_status | grep -v "^$"
echo

# Check snapshot usage
echo "Snapshot Usage:"
lvs -o lv_name,vg_name,lv_attr,snap_percent 2>/dev/null | grep -E "s.*[0-9]" || echo "No snapshots found"
echo

# Check for full filesystems on LVM volumes
echo "LVM Filesystem Usage:"
df -h | grep "/dev/mapper/" | awk '$5+0 > 80 {print "WARNING: " $0}'
EOF

chmod +x /usr/local/bin/lvm-monitor

# Remove logical volumes safely
safe_lv_remove() {
    local lv_path="$1"

    if [[ -z "$lv_path" ]]; then
        echo "Usage: safe_lv_remove <lv_path>"
        return 1
    fi

    # Check if mounted
    if mount | grep -q "$lv_path"; then
        mount_point=$(mount | grep "$lv_path" | awk '{print $3}')
        echo "WARNING: $lv_path is mounted at $mount_point"
        read -p "Unmount and continue? (yes/no): " confirm
        if [[ "$confirm" == "yes" ]]; then
            umount "$mount_point"
        else
            echo "Operation cancelled"
            return 1
        fi
    fi

    # Confirm removal
    echo "This will permanently remove logical volume: $lv_path"
    lvdisplay "$lv_path"
    read -p "Are you sure you want to remove this LV? (yes/no): " confirm

    if [[ "$confirm" == "yes" ]]; then
        lvremove "$lv_path"
        echo "Logical volume removed successfully"
    else
        echo "Operation cancelled"
    fi
}
```