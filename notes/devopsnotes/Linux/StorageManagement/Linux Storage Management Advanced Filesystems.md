# Linux Storage Management Advanced Filesystems

**Advanced Filesystem Management** covers sophisticated filesystem features including Btrfs subvolumes, snapshots, and ZFS pool management for advanced storage scenarios.

## Btrfs Advanced Features

### Subvolumes and Snapshots

#### Btrfs Subvolume Management
```bash
# Create and manage subvolumes
btrfs subvolume create /mnt/btrfs/subvol1     # Create subvolume
btrfs subvolume create /mnt/btrfs/home        # Create home subvolume
btrfs subvolume create /mnt/btrfs/var/log     # Create nested subvolume

# List and inspect subvolumes
btrfs subvolume list /mnt/btrfs               # List all subvolumes
btrfs subvolume list -p /mnt/btrfs            # List with parent info
btrfs subvolume show /mnt/btrfs/subvol1       # Show subvolume details
btrfs subvolume get-default /mnt/btrfs        # Show default subvolume

# Set default subvolume
btrfs subvolume set-default 256 /mnt/btrfs    # Set subvolume ID 256 as default
btrfs subvolume set-default /mnt/btrfs/root   # Set subvolume path as default

# Delete subvolumes
btrfs subvolume delete /mnt/btrfs/subvol1     # Delete subvolume
btrfs subvolume delete -c /mnt/btrfs/subvol1  # Delete with commit

# Subvolume mounting
mount -o subvol=subvol1 /dev/sdb1 /mnt/subvol1
mount -o subvolid=256 /dev/sdb1 /mnt/subvol1
```

#### Btrfs Snapshot Management
```bash
# Create snapshots
btrfs subvolume snapshot /mnt/btrfs/home /mnt/btrfs/snapshots/home-$(date +%Y%m%d)
btrfs subvolume snapshot -r /mnt/btrfs/data /mnt/btrfs/snapshots/data-readonly
btrfs subvolume snapshot /mnt/btrfs/root /mnt/btrfs/snapshots/root-backup

# Automated snapshot script
cat << 'EOF' > /usr/local/bin/btrfs-snapshot
#!/bin/bash
# Automated Btrfs snapshot creation

MOUNT_POINT="$1"
SUBVOLUME="$2"
RETENTION_DAYS="${3:-7}"

if [[ -z "$MOUNT_POINT" || -z "$SUBVOLUME" ]]; then
    echo "Usage: $0 <mount_point> <subvolume> [retention_days]"
    echo "Example: $0 /mnt/btrfs home 7"
    exit 1
fi

SNAPSHOT_DIR="$MOUNT_POINT/snapshots"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
SNAPSHOT_NAME="${SUBVOLUME}-${TIMESTAMP}"

# Create snapshots directory if it doesn't exist
[[ ! -d "$SNAPSHOT_DIR" ]] && btrfs subvolume create "$SNAPSHOT_DIR"

# Create snapshot
echo "Creating snapshot: $SNAPSHOT_NAME"
btrfs subvolume snapshot -r "$MOUNT_POINT/$SUBVOLUME" "$SNAPSHOT_DIR/$SNAPSHOT_NAME"

# Cleanup old snapshots
echo "Cleaning up snapshots older than $RETENTION_DAYS days"
find "$SNAPSHOT_DIR" -name "${SUBVOLUME}-*" -type d -mtime +$RETENTION_DAYS | while read -r old_snapshot; do
    echo "Deleting old snapshot: $(basename $old_snapshot)"
    btrfs subvolume delete "$old_snapshot"
done

echo "Snapshot creation completed"
EOF

chmod +x /usr/local/bin/btrfs-snapshot

# Snapshot management functions
list_snapshots() {
    local mount_point="$1"
    echo "=== Btrfs Snapshots in $mount_point ==="
    btrfs subvolume list -s "$mount_point"
}

restore_from_snapshot() {
    local snapshot_path="$1"
    local restore_path="$2"

    echo "Restoring from snapshot: $snapshot_path"
    echo "Restore to: $restore_path"

    read -p "This will overwrite the current data. Continue? (yes/no): " confirm
    if [[ "$confirm" == "yes" ]]; then
        # Create writable snapshot for restoration
        btrfs subvolume snapshot "$snapshot_path" "$restore_path.tmp"

        # Move current data aside
        mv "$restore_path" "$restore_path.old"

        # Move restored data to target
        mv "$restore_path.tmp" "$restore_path"

        echo "Restoration completed. Old data saved as $restore_path.old"
    fi
}
```

### Btrfs Filesystem Operations

#### Space Management and Balancing
```bash
# Filesystem usage and balance
btrfs filesystem show                        # Show all Btrfs filesystems
btrfs filesystem usage /mnt/btrfs            # Show detailed space usage
btrfs filesystem df /mnt/btrfs               # Show space allocation
btrfs filesystem balance /mnt/btrfs          # Balance entire filesystem

# Targeted balancing
btrfs balance start -dusage=50 /mnt/btrfs    # Balance data blocks 50% full
btrfs balance start -musage=50 /mnt/btrfs    # Balance metadata blocks 50% full
btrfs balance start -susage=50 /mnt/btrfs    # Balance system blocks 50% full

# Monitor balance operation
btrfs balance status /mnt/btrfs              # Check balance status
btrfs balance pause /mnt/btrfs               # Pause balance operation
btrfs balance resume /mnt/btrfs              # Resume balance operation
btrfs balance cancel /mnt/btrfs              # Cancel balance operation

# Defragmentation
btrfs filesystem defragment /mnt/btrfs/file  # Defragment single file
btrfs filesystem defragment -r /mnt/btrfs    # Defragment recursively
btrfs filesystem defragment -c /mnt/btrfs    # Defragment with compression
```

#### Device Management
```bash
# Multi-device operations
btrfs device add /dev/sdc1 /mnt/btrfs        # Add device to filesystem
btrfs device remove /dev/sdc1 /mnt/btrfs     # Remove device from filesystem
btrfs device delete /dev/sdc1 /mnt/btrfs     # Delete device (alias for remove)

# Device scanning and detection
btrfs device scan                            # Scan for all Btrfs devices
btrfs device scan /dev/sdc1                  # Scan specific device
btrfs device ready /dev/sdc1                 # Check if device is ready

# Device statistics
btrfs device stats /mnt/btrfs                # Show device I/O statistics
btrfs device stats -z /mnt/btrfs             # Reset statistics after showing

# Replace failed device
btrfs replace start /dev/old_device /dev/new_device /mnt/btrfs
btrfs replace status /mnt/btrfs              # Check replace progress
btrfs replace cancel /mnt/btrfs              # Cancel replace operation

# RAID level conversion
btrfs balance start -dconvert=raid1 /mnt/btrfs     # Convert data to RAID1
btrfs balance start -mconvert=raid1 /mnt/btrfs     # Convert metadata to RAID1
btrfs balance start -sconvert=raid1 /mnt/btrfs     # Convert system to RAID1
```

### Btrfs Maintenance and Monitoring

#### Scrub Operations
```bash
# Data integrity checking
btrfs scrub start /mnt/btrfs              # Start scrub (data integrity check)
btrfs scrub start -B /mnt/btrfs           # Start scrub in background
btrfs scrub start -r /mnt/btrfs           # Start read-only scrub

# Monitor scrub progress
btrfs scrub status /mnt/btrfs             # Check scrub status
btrfs scrub cancel /mnt/btrfs             # Cancel running scrub
btrfs scrub resume /mnt/btrfs             # Resume paused scrub

# Automated scrub script
cat << 'EOF' > /usr/local/bin/btrfs-scrub-all
#!/bin/bash
# Scrub all Btrfs filesystems

echo "=== Btrfs Scrub Report $(date) ==="

# Find all Btrfs mount points
btrfs filesystem show | grep uuid | while read -r line; do
    uuid=$(echo "$line" | awk '{print $4}')
    mount_point=$(findmnt -n -o TARGET --source UUID="$uuid")

    if [[ -n "$mount_point" ]]; then
        echo "Scrubbing filesystem: $mount_point (UUID: $uuid)"
        btrfs scrub start -B "$mount_point"

        # Check scrub results
        btrfs scrub status "$mount_point"
        echo "---"
    fi
done

echo "Scrub operations completed"
EOF

chmod +x /usr/local/bin/btrfs-scrub-all
```

## ZFS Management (where available)

### ZFS Pool Management

#### Pool Creation and Configuration
```bash
# Basic pool creation
zpool create mypool /dev/sdb                 # Create simple pool
zpool create -f mypool /dev/sdb               # Force creation
zpool create -m /data mypool /dev/sdb         # Custom mountpoint

# Redundant pool configurations
zpool create mypool mirror /dev/sdb /dev/sdc # Create mirrored pool
zpool create mypool raidz /dev/sdb /dev/sdc /dev/sdd  # Create RAID-Z pool
zpool create mypool raidz2 /dev/sd{b,c,d,e}  # Create RAID-Z2 pool
zpool create mypool raidz3 /dev/sd{b,c,d,e,f,g}  # Create RAID-Z3 pool

# Advanced pool features
zpool create -o ashift=12 mypool /dev/sdb     # Set sector size alignment
zpool create -O compression=lz4 mypool /dev/sdb  # Enable compression
zpool create -O atime=off mypool /dev/sdb     # Disable access time updates

# Pool management
zpool status                                 # Show all pool status
zpool status mypool                          # Show specific pool status
zpool list                                   # List all pools with basic info
zpool list -v                                # Verbose pool listing

# Pool operations
zpool scrub mypool                           # Start data integrity scrub
zpool export mypool                          # Export pool
zpool import                                 # List importable pools
zpool import mypool                          # Import pool
zpool destroy mypool                         # Destroy pool (careful!)
```

#### Pool Maintenance
```bash
# Add and remove devices
zpool add mypool /dev/sde                    # Add device to pool
zpool add mypool mirror /dev/sde /dev/sdf    # Add mirrored vdev
zpool remove mypool /dev/sde                 # Remove device
zpool offline mypool /dev/sdb                # Take device offline
zpool online mypool /dev/sdb                 # Bring device online

# Replace failed devices
zpool replace mypool /dev/sdb /dev/sdg       # Replace device
zpool replace mypool /dev/sdb                # Replace with spare

# Pool properties
zpool get all mypool                         # Show all pool properties
zpool set autoreplace=on mypool              # Enable auto-replace
zpool set autoexpand=on mypool               # Enable auto-expand

# Pool health monitoring
zpool status -x                              # Show only pools with issues
zpool iostat mypool 5                        # I/O statistics every 5 seconds
zpool iostat -v mypool                       # Verbose I/O statistics
```

### ZFS Dataset Management

#### Dataset Creation and Configuration
```bash
# Create datasets
zfs create mypool/dataset1                   # Create dataset
zfs create -o mountpoint=/data mypool/data   # Custom mountpoint
zfs create -o quota=10G mypool/limited       # Dataset with quota
zfs create -o compression=gzip mypool/compressed  # Compressed dataset

# Dataset hierarchy
zfs create mypool/users                      # Parent dataset
zfs create mypool/users/alice                # Child dataset
zfs create mypool/users/bob                  # Another child dataset

# List and inspect datasets
zfs list                                     # List all datasets
zfs list -r mypool                           # List datasets recursively
zfs list -t all                              # Include snapshots and volumes
zfs get all mypool/dataset1                  # Show all properties
zfs get compression mypool/dataset1          # Show specific property

# Dataset properties
zfs set compression=lz4 mypool/dataset1      # Enable LZ4 compression
zfs set atime=off mypool/dataset1            # Disable access time
zfs set quota=5G mypool/dataset1             # Set quota
zfs set reservation=1G mypool/dataset1       # Set reservation
zfs set readonly=on mypool/dataset1          # Make read-only

# Dataset operations
zfs mount mypool/dataset1                    # Mount dataset
zfs unmount mypool/dataset1                  # Unmount dataset
zfs rename mypool/old mypool/new             # Rename dataset
zfs destroy mypool/dataset1                  # Destroy dataset
```

#### ZFS Snapshots and Clones
```bash
# Snapshot management
zfs snapshot mypool/dataset1@snap1           # Create snapshot
zfs snapshot mypool/users@backup-$(date +%Y%m%d)  # Dated snapshot
zfs list -t snapshot                         # List all snapshots
zfs list -t snapshot mypool/dataset1         # List dataset snapshots

# Recursive snapshots
zfs snapshot -r mypool/users@backup          # Snapshot all child datasets

# Clone operations
zfs clone mypool/dataset1@snap1 mypool/clone1  # Create clone from snapshot
zfs promote mypool/clone1                    # Promote clone to dataset

# Rollback operations
zfs rollback mypool/dataset1@snap1           # Rollback to snapshot
zfs rollback -r mypool/dataset1@snap1        # Recursive rollback

# Snapshot cleanup
zfs destroy mypool/dataset1@snap1            # Destroy single snapshot
zfs destroy mypool/dataset1@snap1,snap2      # Destroy multiple snapshots
zfs destroy -r mypool/users@backup           # Destroy recursive snapshots

# Automated snapshot management
cat << 'EOF' > /usr/local/bin/zfs-snapshot
#!/bin/bash
# ZFS snapshot management script

DATASET="$1"
SNAPSHOT_PREFIX="${2:-auto}"
RETENTION_DAYS="${3:-7}"

if [[ -z "$DATASET" ]]; then
    echo "Usage: $0 <dataset> [prefix] [retention_days]"
    echo "Example: $0 mypool/data daily 30"
    exit 1
fi

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
SNAPSHOT_NAME="${SNAPSHOT_PREFIX}-${TIMESTAMP}"

# Create snapshot
echo "Creating snapshot: ${DATASET}@${SNAPSHOT_NAME}"
zfs snapshot "${DATASET}@${SNAPSHOT_NAME}"

# Cleanup old snapshots
echo "Cleaning up snapshots older than $RETENTION_DAYS days"
cutoff_date=$(date -d "$RETENTION_DAYS days ago" +%Y%m%d)

zfs list -H -t snapshot -o name "${DATASET}" | grep "@${SNAPSHOT_PREFIX}-" | while read -r snapshot; do
    snapshot_date=$(echo "$snapshot" | sed "s/.*@${SNAPSHOT_PREFIX}-//" | cut -d_ -f1)

    if [[ "$snapshot_date" < "$cutoff_date" ]]; then
        echo "Deleting old snapshot: $snapshot"
        zfs destroy "$snapshot"
    fi
done

echo "Snapshot management completed"
EOF

chmod +x /usr/local/bin/zfs-snapshot
```

### ZFS Replication and Backup

#### Send and Receive Operations
```bash
# Basic send/receive
zfs send mypool/dataset1@snap1 > backup.zfs  # Send to file
zfs send mypool/dataset1@snap1 | ssh remote "zfs receive backup/dataset1"  # Send over network

# Incremental replication
zfs send -i @snap1 mypool/dataset1@snap2 | zfs receive backup/dataset1  # Incremental send
zfs send -I @snap1 mypool/dataset1@snap3 | zfs receive backup/dataset1  # All intermediates

# Recursive send/receive
zfs send -R mypool/users@backup | zfs receive backup/users  # Recursive send

# Compressed send
zfs send -c mypool/dataset1@snap1 | zfs receive backup/dataset1  # Compressed stream

# Resume interrupted send
zfs send -t <token> | zfs receive backup/dataset1  # Resume with token

# Replication script
cat << 'EOF' > /usr/local/bin/zfs-replicate
#!/bin/bash
# ZFS replication script

SOURCE_DATASET="$1"
TARGET_DATASET="$2"
TARGET_HOST="$3"

if [[ -z "$SOURCE_DATASET" || -z "$TARGET_DATASET" ]]; then
    echo "Usage: $0 <source_dataset> <target_dataset> [target_host]"
    echo "Example: $0 mypool/data backup/data"
    echo "Example: $0 mypool/data backup/data remote-server"
    exit 1
fi

# Create snapshot for replication
SNAPSHOT_NAME="repl-$(date +%Y%m%d_%H%M%S)"
zfs snapshot "${SOURCE_DATASET}@${SNAPSHOT_NAME}"

# Get last replicated snapshot
if [[ -n "$TARGET_HOST" ]]; then
    LAST_SNAP=$(ssh "$TARGET_HOST" "zfs list -H -t snapshot -o name $TARGET_DATASET" 2>/dev/null | grep "@repl-" | tail -1 | cut -d@ -f2)
else
    LAST_SNAP=$(zfs list -H -t snapshot -o name "$TARGET_DATASET" 2>/dev/null | grep "@repl-" | tail -1 | cut -d@ -f2)
fi

# Perform replication
if [[ -n "$LAST_SNAP" ]]; then
    echo "Performing incremental replication from @$LAST_SNAP"
    if [[ -n "$TARGET_HOST" ]]; then
        zfs send -i "@$LAST_SNAP" "${SOURCE_DATASET}@${SNAPSHOT_NAME}" | ssh "$TARGET_HOST" "zfs receive $TARGET_DATASET"
    else
        zfs send -i "@$LAST_SNAP" "${SOURCE_DATASET}@${SNAPSHOT_NAME}" | zfs receive "$TARGET_DATASET"
    fi
else
    echo "Performing initial replication"
    if [[ -n "$TARGET_HOST" ]]; then
        zfs send "${SOURCE_DATASET}@${SNAPSHOT_NAME}" | ssh "$TARGET_HOST" "zfs receive $TARGET_DATASET"
    else
        zfs send "${SOURCE_DATASET}@${SNAPSHOT_NAME}" | zfs receive "$TARGET_DATASET"
    fi
fi

echo "Replication completed: ${SOURCE_DATASET}@${SNAPSHOT_NAME}"
EOF

chmod +x /usr/local/bin/zfs-replicate
```