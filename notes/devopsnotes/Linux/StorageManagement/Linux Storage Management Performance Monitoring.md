# Linux Storage Management Performance Monitoring

**Storage Performance and Monitoring** covers I/O analysis tools, performance testing methodologies, and storage optimization techniques for maintaining optimal storage system performance.

## Storage Performance Analysis

### I/O Monitoring Tools

#### iostat - I/O Statistics
```bash
# Basic iostat usage
iostat                                  # Basic I/O statistics snapshot
iostat 1                                # Update every second
iostat 5 10                             # 5-second intervals, 10 samples
iostat -x                               # Extended statistics
iostat -x 1                             # Extended stats every second
iostat -x -d 5 10                       # Device stats only, 5-second intervals, 10 times

# iostat output interpretation:
# Device    - Device name
# r/s       - Read operations per second
# w/s       - Write operations per second
# rkB/s     - Kilobytes read per second
# wkB/s     - Kilobytes written per second
# rrqm/s    - Read requests merged per second
# wrqm/s    - Write requests merged per second
# %rrqm     - Percentage of read requests merged
# %wrqm     - Percentage of write requests merged
# r_await   - Average wait time for read requests (ms)
# w_await   - Average wait time for write requests (ms)
# aqu-sz    - Average queue size
# rareq-sz  - Average request size for reads (KB)
# wareq-sz  - Average request size for writes (KB)
# svctm     - Average service time (deprecated)
# %util     - Percentage of time device was busy

# Specific device monitoring
iostat -x /dev/sda                      # Monitor specific device
iostat -x -p /dev/sda                   # Include partition statistics
iostat -k                               # Display in kilobytes
iostat -m                               # Display in megabytes

# Network filesystem statistics
iostat -n                               # Display NFS statistics
```

#### iotop - Process I/O Usage
```bash
# Basic iotop usage
iotop                                   # Interactive I/O monitor
iotop -o                                # Only show processes with I/O activity
iotop -a                                # Show accumulated I/O since iotop started
iotop -k                                # Use kilobytes instead of percentages
iotop -t                                # Add timestamps
iotop -q                                # Quiet mode (non-interactive)

# iotop with specific options
iotop -P                                # Show processes instead of threads
iotop -u user                           # Show only specific user's processes
iotop -p PID                            # Monitor specific process
iotop -d 5                              # Update delay of 5 seconds

# iotop batch mode for logging
iotop -b -o -d 10 -n 12 > iotop.log     # Batch mode, 10-second intervals, 12 samples

# Alternative: pidstat for I/O
pidstat -d 1                            # I/O statistics for all processes
pidstat -d -p PID 1                     # I/O stats for specific process
pidstat -d 1 5                          # 5 samples, 1-second intervals
```

### Advanced I/O Monitoring

#### System-wide I/O Analysis
```bash
# Block device statistics
cat /proc/diskstats                     # Raw disk statistics
# Fields: major minor name reads reads_merged read_sectors read_time
#         writes writes_merged write_sectors write_time
#         io_in_progress io_time weighted_io_time

# I/O pressure monitoring (if supported)
cat /proc/pressure/io                   # I/O pressure information (cgroup v2)

# dstat - Comprehensive statistics
dstat                                   # Basic system stats
dstat -d                                # Disk statistics only
dstat -D sda,sdb                        # Specific disks
dstat --disk-util --disk-tps            # Disk utilization and transactions per second
dstat --top-io --top-bio               # Top I/O processes

# Per-process I/O statistics
cat /proc/PID/io                        # I/O stats for specific process
# rchar/wchar: Total bytes read/written (including cached)
# read_bytes/write_bytes: Actual storage I/O
# syscr/syscw: Read/write system calls
# cancelled_write_bytes: Cancelled write operations

# Monitor I/O for all processes
for pid in $(ps -eo pid --no-headers); do
    if [[ -f "/proc/$pid/io" ]]; then
        echo "PID $pid:"
        cat "/proc/$pid/io" 2>/dev/null | grep -E "read_bytes|write_bytes"
        echo "---"
    fi
done | head -50
```

#### Storage Device Information
```bash
# Device hardware information
lsblk -d -o NAME,SIZE,MODEL,VENDOR,REV  # Storage device overview
lsblk -o NAME,SIZE,TYPE,FSTYPE,MOUNTPOINT,UUID  # Detailed block device info

# SATA/IDE disk information
hdparm -I /dev/sda                      # Detailed ATA/SATA disk information
hdparm -t /dev/sda                      # Buffered disk read test
hdparm -T /dev/sda                      # Cached disk read test
hdparm -i /dev/sda                      # Device identification

# SCSI disk information
lsscsi                                  # List SCSI devices
lsscsi -s                               # Include device sizes

# SMART disk health monitoring
smartctl -a /dev/sda                    # Complete SMART information
smartctl -H /dev/sda                    # Health status only
smartctl -t short /dev/sda              # Run short self-test
smartctl -t long /dev/sda               # Run extended self-test
smartctl -l selftest /dev/sda           # Show self-test results

# NVMe SSD information
nvme list                               # List NVMe devices
nvme smart-log /dev/nvme0n1             # SMART information for NVMe
nvme id-ctrl /dev/nvme0n1               # Controller identification
```

## Performance Testing

### Disk Performance Testing

#### Basic Performance Tests with dd
```bash
# Sequential write test
echo "Sequential write test:"
sync && echo 3 > /proc/sys/vm/drop_caches  # Clear caches
dd if=/dev/zero of=/tmp/testfile bs=1M count=1000 oflag=direct conv=fdatasync
# oflag=direct: Bypass cache, conv=fdatasync: Sync before finishing

# Sequential read test
echo "Sequential read test:"
sync && echo 3 > /proc/sys/vm/drop_caches  # Clear caches
dd if=/tmp/testfile of=/dev/null bs=1M iflag=direct

# Random write test (limited effectiveness with dd)
echo "Random write test:"
dd if=/dev/urandom of=/tmp/random_testfile bs=4k count=10000 oflag=direct

# Cleanup
rm -f /tmp/testfile /tmp/random_testfile

# Write performance with different block sizes
for bs in 4k 8k 16k 32k 64k 128k 1M; do
    echo "Testing block size: $bs"
    dd if=/dev/zero of=/tmp/test_$bs bs=$bs count=1000 oflag=direct 2>&1 | grep copied
    rm -f /tmp/test_$bs
done
```

#### Advanced Performance Testing with fio
```bash
# Random read/write test
fio --name=random-rw --ioengine=libaio --rw=randrw --bs=4k --direct=1 \
    --size=1G --numjobs=4 --runtime=60 --group_reporting \
    --filename=/tmp/fio-test

# Sequential read test
fio --name=seq-read --ioengine=libaio --rw=read --bs=1M --direct=1 \
    --size=2G --numjobs=1 --runtime=60 --group_reporting \
    --filename=/tmp/fio-seq-test

# Random write IOPS test
fio --name=random-write-iops --ioengine=libaio --rw=randwrite --bs=4k \
    --direct=1 --size=1G --numjobs=1 --runtime=60 --time_based \
    --filename=/tmp/fio-randwrite

# Mixed workload test
fio --name=mixed-workload --ioengine=libaio --rw=randrw --rwmixread=70 \
    --bs=4k --direct=1 --size=1G --numjobs=2 --runtime=120 \
    --filename=/tmp/fio-mixed

# Comprehensive storage test script
cat << 'EOF' > /usr/local/bin/storage-benchmark
#!/bin/bash
# Comprehensive storage performance test

TEST_DIR="${1:-/tmp}"
TEST_SIZE="${2:-1G}"

echo "=== Storage Performance Benchmark ==="
echo "Test directory: $TEST_DIR"
echo "Test size: $TEST_SIZE"
echo "Start time: $(date)"
echo

# Create test directory
mkdir -p "$TEST_DIR/benchmark"
cd "$TEST_DIR/benchmark"

echo "1. Sequential Write Test"
fio --name=seq-write --ioengine=libaio --rw=write --bs=1M --direct=1 \
    --size="$TEST_SIZE" --numjobs=1 --runtime=60 --time_based \
    --filename=seq-write-test --output-format=normal | grep -E "write:|WRITE:"

echo
echo "2. Sequential Read Test"
fio --name=seq-read --ioengine=libaio --rw=read --bs=1M --direct=1 \
    --size="$TEST_SIZE" --numjobs=1 --runtime=60 --time_based \
    --filename=seq-write-test --output-format=normal | grep -E "read:|READ:"

echo
echo "3. Random Read IOPS Test"
fio --name=rand-read --ioengine=libaio --rw=randread --bs=4k --direct=1 \
    --size="$TEST_SIZE" --numjobs=4 --runtime=60 --time_based \
    --filename=rand-test --output-format=normal | grep -E "read:|READ:"

echo
echo "4. Random Write IOPS Test"
fio --name=rand-write --ioengine=libaio --rw=randwrite --bs=4k --direct=1 \
    --size="$TEST_SIZE" --numjobs=4 --runtime=60 --time_based \
    --filename=rand-test --output-format=normal | grep -E "write:|WRITE:"

echo
echo "5. Mixed Random 70/30 Read/Write Test"
fio --name=mixed-rw --ioengine=libaio --rw=randrw --rwmixread=70 --bs=4k \
    --direct=1 --size="$TEST_SIZE" --numjobs=2 --runtime=60 --time_based \
    --filename=mixed-test --output-format=normal | grep -E "read:|READ:|write:|WRITE:"

# Cleanup
rm -f seq-write-test rand-test mixed-test
cd - > /dev/null
rmdir "$TEST_DIR/benchmark" 2>/dev/null

echo
echo "Benchmark completed: $(date)"
EOF

chmod +x /usr/local/bin/storage-benchmark

# Filesystem-specific benchmarks
bonnie++ -u root -d /tmp -s 2g           # Comprehensive filesystem benchmark
iozone -a -g 4G                         # Automated test suite
```

## Storage Optimization

### I/O Scheduler Optimization

#### I/O Scheduler Configuration
```bash
# Check current I/O scheduler
cat /sys/block/sda/queue/scheduler       # Shows available schedulers, current in []

# Available schedulers:
# noop/none     - No-operation scheduler (good for SSDs, VMs)
# deadline      - Deadline scheduler (good for HDDs)
# cfq           - Completely Fair Queuing (default on many systems)
# bfq           - Budget Fair Queuing (good for interactive workloads)
# mq-deadline   - Multi-queue deadline (for modern systems)
# kyber         - Multi-queue scheduler for low-latency

# Set I/O scheduler temporarily
echo noop > /sys/block/sda/queue/scheduler      # For SSDs
echo deadline > /sys/block/sda/queue/scheduler  # For HDDs
echo bfq > /sys/block/sda/queue/scheduler       # For interactive workloads

# Check if device is SSD or HDD
cat /sys/block/sda/queue/rotational      # 0 = SSD, 1 = HDD
lsblk -d -o NAME,ROTA                    # Show rotation status for all devices

# Persistent I/O scheduler configuration via udev
cat << 'EOF' > /etc/udev/rules.d/60-ioschedulers.rules
# Set noop scheduler for SSDs
ACTION=="add|change", KERNEL=="sd[a-z]|nvme[0-9]*n[0-9]*", \
ATTR{queue/rotational}=="0", ATTR{queue/scheduler}="noop"

# Set deadline scheduler for HDDs
ACTION=="add|change", KERNEL=="sd[a-z]", \
ATTR{queue/rotational}=="1", ATTR{queue/scheduler}="deadline"

# Set scheduler for specific devices by ID
ACTION=="add|change", KERNEL=="sd[a-z]", \
ATTRS{serial}=="WD-WCAV12345678", ATTR{queue/scheduler}="cfq"
EOF

# Apply udev rules
udevadm control --reload-rules
udevadm trigger
```

#### Queue Depth and Read-ahead Optimization
```bash
# Adjust queue depth
echo 32 > /sys/block/sda/queue/nr_requests  # Set queue depth

# Read-ahead optimization
# Check current read-ahead
blockdev --getra /dev/sda                # Get read-ahead in 512-byte sectors

# Set read-ahead
blockdev --setra 256 /dev/sda           # Set to 256 sectors (128KB)
blockdev --setra 512 /dev/sda           # Set to 512 sectors (256KB)
blockdev --setra 1024 /dev/sda          # Set to 1024 sectors (512KB)

# Optimal read-ahead for different workloads:
# Small random I/O: 128-256KB
# Sequential I/O: 512KB-1MB
# Database workloads: 256-512KB

# Make read-ahead persistent
cat << 'EOF' > /etc/udev/rules.d/61-readahead.rules
# Set read-ahead for SSDs
ACTION=="add|change", KERNEL=="sd[a-z]|nvme[0-9]*n[0-9]*", \
ATTR{queue/rotational}=="0", ATTR{bdi/read_ahead_kb}="128"

# Set read-ahead for HDDs
ACTION=="add|change", KERNEL=="sd[a-z]", \
ATTR{queue/rotational}=="1", ATTR{bdi/read_ahead_kb}="512"
EOF
```

### Filesystem Mount Optimization

#### Performance-oriented Mount Options
```bash
# SSD optimization
mount -o noatime,discard /dev/sdb1 /mnt/ssd
# noatime: Don't update access times (reduces writes)
# discard: Enable TRIM for SSDs

# Database optimization
mount -o noatime,barrier=0 /dev/sdb1 /mnt/db
# WARNING: barrier=0 only safe with battery-backed RAID controller

# General performance optimization
mount -o noatime,nodiratime /dev/sdb1 /mnt/data
# nodiratime: Don't update directory access times

# Large file optimization
mount -o noatime,largeio /dev/sdb1 /mnt/bigfiles  # XFS specific

# Example optimized fstab entries
cat << 'EOF' >> /etc/fstab
# Performance-optimized mounts
UUID=ssd-uuid    /opt/app       ext4  defaults,noatime,discard                    0 2
UUID=hdd-uuid    /data          ext4  defaults,noatime,nodiratime                0 2
UUID=db-uuid     /var/lib/mysql xfs   defaults,noatime,largeio,nobarrier         0 2
UUID=log-uuid    /var/log       ext4  defaults,noatime,nodiratime,commit=60      0 2
EOF
```

### System-wide Storage Optimization

#### Kernel Parameters for Storage
```bash
# VM (Virtual Memory) tuning for storage performance
cat << 'EOF' > /etc/sysctl.d/90-storage-performance.conf
# Reduce swappiness for better I/O performance
vm.swappiness = 1

# Dirty page management
vm.dirty_ratio = 15                    # Percentage of RAM for dirty pages before blocking writes
vm.dirty_background_ratio = 5          # Background dirty page writeback threshold
vm.dirty_expire_centisecs = 1500       # Dirty page expiration time (15 seconds)
vm.dirty_writeback_centisecs = 500     # Writeback interval (5 seconds)

# VFS cache pressure
vm.vfs_cache_pressure = 50             # Reduce tendency to reclaim cache

# Block I/O optimization
vm.block_dump = 0                      # Disable block I/O debugging
EOF

# Apply settings
sysctl -p /etc/sysctl.d/90-storage-performance.conf

# Monitor dirty pages
grep -E "^Dirty|^Writeback" /proc/meminfo
watch 'grep -E "^Dirty|^Writeback" /proc/meminfo'
```

#### Storage Performance Monitoring Script
```bash
# Comprehensive storage monitoring script
cat << 'EOF' > /usr/local/bin/storage-monitor
#!/bin/bash
# Storage performance monitoring script

INTERVAL="${1:-5}"
COUNT="${2:-12}"

echo "=== Storage Performance Monitor ==="
echo "Interval: ${INTERVAL}s, Samples: $COUNT"
echo "Start: $(date)"
echo

# Device selection
devices=$(lsblk -d -n -o NAME | grep -E '^(sd|nvme|vd)' | head -5)
echo "Monitoring devices: $devices"
echo

# Header
printf "%-10s %-8s %-8s %-8s %-8s %-8s %-8s %-8s %-8s\n" \
    "Time" "Device" "r/s" "w/s" "rkB/s" "wkB/s" "await" "%util" "aqu-sz"
echo "---------------------------------------------------------------------------------"

# Main monitoring loop
for ((i=1; i<=COUNT; i++)); do
    timestamp=$(date '+%H:%M:%S')

    iostat -x "$INTERVAL" 1 | grep -E "$(echo $devices | tr ' ' '|')" | while read -r line; do
        printf "%-10s %s\n" "$timestamp" "$line"
    done

    if [[ $i -lt $COUNT ]]; then
        echo "---"
    fi
done

echo
echo "End: $(date)"
EOF

chmod +x /usr/local/bin/storage-monitor

# Real-time storage alerts
cat << 'EOF' > /usr/local/bin/storage-alerts
#!/bin/bash
# Storage performance alerts

UTIL_THRESHOLD=90    # %util threshold
AWAIT_THRESHOLD=100  # await threshold in ms

while true; do
    iostat -x 1 1 | tail -n +4 | while read -r line; do
        if [[ "$line" =~ ^[a-z] ]]; then
            device=$(echo "$line" | awk '{print $1}')
            util=$(echo "$line" | awk '{print $NF}' | cut -d. -f1)
            await=$(echo "$line" | awk '{print $(NF-3)}' | cut -d. -f1)

            if [[ $util -gt $UTIL_THRESHOLD ]]; then
                echo "$(date): WARNING - Device $device utilization: ${util}%"
            fi

            if [[ $await -gt $AWAIT_THRESHOLD ]]; then
                echo "$(date): WARNING - Device $device high latency: ${await}ms"
            fi
        fi
    done

    sleep 10
done
EOF

chmod +x /usr/local/bin/storage-alerts
```