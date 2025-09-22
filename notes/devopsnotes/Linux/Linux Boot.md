
# Linux Boot Process & Troubleshooting

## Boot Process Overview

### **Boot Sequence Components**
- **BIOS** (Basic Input/Output System): initializes hardware, runs POST
- **UEFI** (Unified Extensible Firmware Interface): modern BIOS replacement with advanced features
- **POST** (Power-On Self-Test): checks hardware on startup
- **MBR** (Master Boot Record): legacy partition table and bootloader location (first 512 bytes)
- **GPT** (GUID Partition Table): modern replacement for MBR, supports large disks and more partitions
- **Bootloader**: loads OS kernel (e.g., GRUB, LILO)
- **GRUB** (GRand Unified Bootloader): popular bootloader, supports multi-OS
- **Kernel**: core of the OS, manages hardware and system calls
- **init / systemd**: first user-space process started by kernel
- **/etc/fstab**: defines mount points
- **/boot/**: contains kernel, initramfs, GRUB files
- **initramfs**: temporary root filesystem loaded into memory before actual root

### **Detailed Boot Sequence**
1. **Power On** → BIOS/UEFI initialization
2. **POST** → Hardware component verification
3. **Boot Device Selection** → First bootable device detection
4. **Bootloader Loading** → GRUB loaded from MBR/GPT
5. **Kernel Loading** → Linux kernel loaded into memory
6. **initramfs** → Initial RAM filesystem mounted
7. **Kernel Initialization** → Hardware detection and driver loading
8. **Root Filesystem Mount** → Real root filesystem mounted
9. **init/systemd Start** → First user-space process
10. **Service Initialization** → System services started
11. **Login Prompt** → System ready for user interaction

## Advanced Boot Troubleshooting

### **Common Boot Failures and Solutions**

#### **GRUB Boot Issues**
```bash
# GRUB rescue mode commands
# When system shows "grub rescue>"

# List available partitions
ls

# Set root partition (example: hd0,msdos1)
set root=(hd0,msdos1)

# Set prefix path
set prefix=(hd0,msdos1)/boot/grub

# Load normal module
insmod normal

# Start normal boot
normal

# Or boot directly
linux /vmlinuz root=/dev/sda1
initrd /initrd.img
boot
```

#### **GRUB Configuration Recovery**
```bash
# Boot from live USB/CD and chroot into system

# Mount the root filesystem
mount /dev/sda1 /mnt

# Mount additional filesystems
mount /dev/sda2 /mnt/boot  # if separate /boot partition
mount --bind /dev /mnt/dev
mount --bind /proc /mnt/proc
mount --bind /sys /mnt/sys

# Chroot into the system
chroot /mnt

# Reinstall GRUB
grub-install /dev/sda

# Update GRUB configuration
update-grub

# Exit chroot and reboot
exit
umount /mnt/dev /mnt/proc /mnt/sys /mnt/boot /mnt
reboot
```

#### **Kernel Panic Troubleshooting**
```bash
# Boot parameters for troubleshooting (added to kernel line in GRUB)

# Single user mode
single

# Specific runlevel
init=3

# Disable problematic modules
modprobe.blacklist=module_name

# Enable verbose output
debug loglevel=7

# Disable ACPI (hardware compatibility)
acpi=off noapic nolapic

# Memory testing
memtest=1

# Disable SELinux
selinux=0

# Recovery mode with read-only filesystem
ro recovery
```

### **Boot Performance Analysis**

#### **Systemd Boot Analysis**
```bash
# Analyze boot time
systemd-analyze

# Show service startup times
systemd-analyze blame

# Show critical path
systemd-analyze critical-chain

# Generate boot chart
systemd-analyze plot > boot-chart.svg

# Show service dependencies
systemd-analyze dot | dot -Tsvg > dependencies.svg

# Time to reach specific target
systemd-analyze critical-chain multi-user.target
```

#### **Boot Optimization Strategies**
```bash
# Disable unnecessary services
systemctl disable service_name

# Mask services to prevent activation
systemctl mask service_name

# Parallel service startup (default in systemd)
# Check service types in unit files:
# Type=simple - default, starts immediately
# Type=forking - traditional daemon
# Type=oneshot - single action, then exits
# Type=notify - service notifies when ready

# Optimize initramfs
# Remove unnecessary modules from initramfs
echo 'MODULES=dep' >> /etc/initramfs-tools/conf.d/modules
update-initramfs -u

# Use faster I/O scheduler for SSDs
echo 'GRUB_CMDLINE_LINUX_DEFAULT="quiet splash elevator=noop"' >> /etc/default/grub
update-grub
```

### **Emergency Boot Procedures**

#### **Single User Mode Recovery**
```bash
# Access single user mode from GRUB
# 1. Select kernel in GRUB menu
# 2. Press 'e' to edit
# 3. Add 'single' or 'init=/bin/bash' to kernel line
# 4. Press Ctrl+X to boot

# Common recovery tasks in single user mode:

# Reset root password
passwd root

# Check filesystem
fsck /dev/sda1

# Mount filesystem read-write
mount -o remount,rw /

# Fix /etc/fstab issues
vi /etc/fstab

# Check system logs
journalctl -b
```

#### **Live USB/CD Recovery**
```bash
# Boot from live system and recover

# Identify partitions
fdisk -l
lsblk

# Mount system partitions
mkdir /mnt/recovery
mount /dev/sda1 /mnt/recovery
mount /dev/sda2 /mnt/recovery/boot  # if separate
mount /dev/sda3 /mnt/recovery/home  # if separate

# Mount virtual filesystems for chroot
for i in /dev /dev/pts /proc /sys /run; do
    mount --bind $i /mnt/recovery$i
done

# Chroot into system
chroot /mnt/recovery

# Perform recovery operations
# - Fix bootloader
# - Repair filesystems
# - Recover data
# - Reset passwords
# - Fix configuration files

# Exit and cleanup
exit
umount -R /mnt/recovery
```

### **Boot Security and Hardening**

#### **GRUB Security Configuration**
```bash
# Set GRUB password protection
# Generate password hash
grub-mkpasswd-pbkdf2

# Add to /etc/grub.d/40_custom
cat >> /etc/grub.d/40_custom << 'EOF'
set superusers="admin"
password_pbkdf2 admin grub.pbkdf2.sha512.10000.HASH_HERE
EOF

# Protect menu editing
echo 'CLASS="--class gnu-linux --class gnu --class os --unrestricted"' >> /etc/grub.d/10_linux

# Update GRUB configuration
update-grub

# Set BIOS/UEFI password
# - Enter BIOS/UEFI setup during boot
# - Set administrator/supervisor password
# - Enable secure boot (UEFI systems)
```

#### **Secure Boot Configuration**
```bash
# Check secure boot status
mokutil --sb-state

# List enrolled keys
mokutil --list-enrolled

# For custom kernels or modules
# Sign kernel modules
/usr/src/linux-headers-$(uname -r)/scripts/sign-file \
    sha256 /path/to/private.key /path/to/public.der module.ko

# Enroll Machine Owner Key (MOK)
mokutil --import /path/to/key.der
```

## Boot Monitoring and Logging

### **Boot Log Analysis**
```bash
# View boot messages
dmesg | less
dmesg -T | less  # Human readable timestamps

# Previous boot logs
journalctl -b -1  # Previous boot
journalctl -b -2  # Two boots ago

# Boot-related journalctl filters
journalctl -u systemd-boot
journalctl -k  # Kernel messages only
journalctl --since="2024-01-01" --until="2024-01-02"

# Boot time analysis
journalctl --boot=0 --no-pager | grep "Startup finished"
```

### **Automated Boot Monitoring**
```bash
# Create boot monitoring script
cat > /usr/local/bin/boot-monitor.sh << 'EOF'
#!/bin/bash
# boot-monitor.sh - Monitor boot process and alert on issues

BOOT_TIME_THRESHOLD=60  # seconds
ALERT_EMAIL="admin@company.com"

# Get last boot time
BOOT_TIME=$(systemd-analyze | grep "Startup finished" | \
    awk '{print $4}' | sed 's/s//')

# Check if boot time exceeds threshold
if (( $(echo "$BOOT_TIME > $BOOT_TIME_THRESHOLD" | bc -l) )); then
    echo "ALERT: Boot time ${BOOT_TIME}s exceeds threshold ${BOOT_TIME_THRESHOLD}s" | \
        mail -s "Boot Performance Alert - $(hostname)" "$ALERT_EMAIL"
fi

# Log boot performance
echo "$(date): Boot completed in ${BOOT_TIME}s" >> /var/log/boot-performance.log
EOF

chmod +x /usr/local/bin/boot-monitor.sh

# Create systemd service for boot monitoring
cat > /etc/systemd/system/boot-monitor.service << 'EOF'
[Unit]
Description=Boot Performance Monitor
After=multi-user.target

[Service]
Type=oneshot
ExecStart=/usr/local/bin/boot-monitor.sh

[Install]
WantedBy=multi-user.target
EOF

systemctl enable boot-monitor.service
```

## Integration with DevOps Tools

### **Automated System Recovery**
- Implement automated recovery scripts triggered by monitoring systems
- Use configuration management (Ansible/Puppet) to maintain consistent boot configurations
- Create infrastructure as code templates for bootloader configurations
- Integrate boot performance metrics with monitoring dashboards

### **Cross-References**
- **[[Linux System Administration]]** - Service management and systemd
- **[[Linux Security]]** - Boot security and hardening measures
- **[[Linux Storage Management]]** - Filesystem and partition management
- **[[Linux fundamental]]** - System troubleshooting methodology