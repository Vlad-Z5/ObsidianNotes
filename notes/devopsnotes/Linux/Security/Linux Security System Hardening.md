# Linux Security System Hardening

**System hardening** strengthens Linux systems against security threats through service reduction, file system security, kernel configuration, and comprehensive security controls.

## Basic Security Hardening

### System Updates and Package Management

#### Automated Updates Configuration
```bash
# Keep system updated (Debian/Ubuntu)
apt update && apt upgrade -y
apt autoremove -y
apt autoclean

# RHEL/CentOS/Fedora updates
dnf upgrade -y
dnf autoremove -y
dnf clean all

# Enable automatic security updates (Ubuntu)
apt install unattended-upgrades
dpkg-reconfigure -plow unattended-upgrades

# Configure automatic updates
cat << 'EOF' > /etc/apt/apt.conf.d/50unattended-upgrades
Unattended-Upgrade::Allowed-Origins {
    "${distro_id}:${distro_codename}-security";
    "${distro_id} ESMApps:${distro_codename}-apps-security";
    "${distro_id} ESM:${distro_codename}-infra-security";
};

Unattended-Upgrade::Package-Blacklist {
    "kernel*";
    "linux-*";
};

Unattended-Upgrade::Remove-Unused-Dependencies "true";
Unattended-Upgrade::Automatic-Reboot "false";
Unattended-Upgrade::Automatic-Reboot-Time "02:00";
Unattended-Upgrade::Mail "admin@company.com";
Unattended-Upgrade::MailOnlyOnError "true";
EOF

# Enable automatic updates
cat << 'EOF' > /etc/apt/apt.conf.d/20auto-upgrades
APT::Periodic::Update-Package-Lists "1";
APT::Periodic::Download-Upgradeable-Packages "1";
APT::Periodic::AutocleanInterval "7";
APT::Periodic::Unattended-Upgrade "1";
EOF
```

#### RHEL/CentOS Automatic Updates
```bash
# Install and configure dnf-automatic
dnf install dnf-automatic

cat << 'EOF' > /etc/dnf/automatic.conf
[commands]
upgrade_type = security
random_sleep = 3600
download_updates = yes
apply_updates = yes

[emitters]
emit_via = stdio,email

[email]
email_from = system@company.com
email_to = admin@company.com
email_host = localhost
EOF

systemctl enable --now dnf-automatic.timer
```

### Service Hardening

#### Disable Unnecessary Services
```bash
# List all enabled services
systemctl list-unit-files --state=enabled

# Common services to disable if not needed
services_to_disable=(
    "telnet"
    "rsh"
    "rlogin"
    "vsftpd"
    "xinetd"
    "cups"
    "avahi-daemon"
    "bluetooth"
    "rpcbind"
    "nfs-server"
    "ypbind"
    "tftp"
)

echo "Disabling unnecessary services..."
for service in "${services_to_disable[@]}"; do
    if systemctl is-enabled "$service" &>/dev/null; then
        systemctl disable "$service"
        systemctl stop "$service"
        echo "✓ Disabled $service"
    else
        echo "- $service not found or already disabled"
    fi
done

# Remove unnecessary packages
packages_to_remove=(
    "telnet"
    "rsh-client"
    "rsh-redone-client"
    "talk"
    "ntalk"
    "ypbind"
    "xinetd"
    "tftp-server"
    "bind"
)

echo "Removing unnecessary packages..."
for package in "${packages_to_remove[@]}"; do
    if command -v apt &>/dev/null; then
        apt remove --purge "$package" -y 2>/dev/null || echo "- $package not installed"
    elif command -v dnf &>/dev/null; then
        dnf remove "$package" -y 2>/dev/null || echo "- $package not installed"
    fi
done
```

#### SSH Hardening
```bash
# SSH security configuration
cat << 'EOF' > /etc/ssh/sshd_config
# Protocol and encryption
Protocol 2
Port 22
AddressFamily inet

# Authentication
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
AuthorizedKeysFile .ssh/authorized_keys
PermitEmptyPasswords no
ChallengeResponseAuthentication no
UsePAM yes

# Connection settings
ClientAliveInterval 300
ClientAliveCountMax 2
MaxAuthTries 3
MaxSessions 4
LoginGraceTime 30

# Security options
X11Forwarding no
AllowTcpForwarding no
GatewayPorts no
PermitTunnel no
Banner /etc/issue.net

# Allowed users/groups
AllowUsers admin deploy
AllowGroups ssh-users

# Logging
SyslogFacility AUTH
LogLevel VERBOSE

# Ciphers and algorithms
Ciphers chacha20-poly1305@openssh.com,aes256-gcm@openssh.com,aes128-gcm@openssh.com,aes256-ctr,aes192-ctr,aes128-ctr
MACs hmac-sha2-256-etm@openssh.com,hmac-sha2-512-etm@openssh.com,hmac-sha2-256,hmac-sha2-512
KexAlgorithms curve25519-sha256@libssh.org,ecdh-sha2-nistp521,ecdh-sha2-nistp384,ecdh-sha2-nistp256,diffie-hellman-group-exchange-sha256
HostKeyAlgorithms ssh-rsa,rsa-sha2-256,rsa-sha2-512,ecdsa-sha2-nistp256,ecdsa-sha2-nistp384,ecdsa-sha2-nistp521,ssh-ed25519
EOF

# Restart SSH service
systemctl restart sshd

# Create SSH banner
cat << 'EOF' > /etc/issue.net
**************************************************************************
                    AUTHORIZED ACCESS ONLY
This system is for the use of authorized users only. Individuals using
this computer system without authority, or in excess of their authority,
are subject to having all of their activities on this system monitored
and recorded by system personnel.
**************************************************************************
EOF
```

### File System Security

#### File and Directory Permissions
```bash
# Find and review SUID/SGID files
echo "Finding SUID files..."
find / -perm -4000 -type f 2>/dev/null > /tmp/suid_files.txt
echo "SUID files found: $(wc -l < /tmp/suid_files.txt)"

echo "Finding SGID files..."
find / -perm -2000 -type f 2>/dev/null > /tmp/sgid_files.txt
echo "SGID files found: $(wc -l < /tmp/sgid_files.txt)"

# Review and remove unnecessary SUID/SGID bits
# Example removals (be careful!)
# chmod u-s /usr/bin/chsh      # If not needed
# chmod u-s /usr/bin/chfn      # If not needed
# chmod u-s /usr/bin/wall      # If not needed

# Find world-writable files (security risk)
echo "Finding world-writable files..."
find / -perm -002 -type f 2>/dev/null | grep -v /proc | grep -v /sys | grep -v /dev > /tmp/world_writable.txt
echo "World-writable files found: $(wc -l < /tmp/world_writable.txt)"

# Find files with no owner (orphaned files)
echo "Finding orphaned files..."
find / -nouser -o -nogroup 2>/dev/null | head -20 > /tmp/orphaned_files.txt

# Secure important directories
chmod 700 /root
chmod 755 /home
chmod 1777 /tmp        # Sticky bit for /tmp
chmod 1777 /var/tmp    # Sticky bit for /var/tmp

# Set proper permissions on critical files
chmod 600 /etc/shadow
chmod 600 /etc/gshadow
chmod 644 /etc/passwd
chmod 644 /etc/group
chmod 600 /boot/grub/grub.cfg 2>/dev/null || chmod 600 /boot/grub2/grub.cfg 2>/dev/null
chmod 600 /etc/ssh/ssh_host_*_key
chmod 644 /etc/ssh/ssh_host_*_key.pub

# Secure log files
chmod 640 /var/log/messages 2>/dev/null
chmod 640 /var/log/secure 2>/dev/null
chmod 640 /var/log/auth.log 2>/dev/null
```

#### File System Monitoring Script
```bash
#!/bin/bash
# filesystem-security-check.sh

REPORT_FILE="/tmp/filesystem-security-$(date +%Y%m%d).txt"

{
    echo "=== File System Security Check ==="
    echo "Date: $(date)"
    echo "Hostname: $(hostname)"
    echo ""

    echo "=== SUID Files ==="
    find / -perm -4000 -type f 2>/dev/null

    echo ""
    echo "=== SGID Files ==="
    find / -perm -2000 -type f 2>/dev/null

    echo ""
    echo "=== World-Writable Files ==="
    find / -perm -002 -type f 2>/dev/null | grep -v /proc | grep -v /sys | grep -v /dev | head -20

    echo ""
    echo "=== Orphaned Files ==="
    find / -nouser -o -nogroup 2>/dev/null | head -10

    echo ""
    echo "=== Critical File Permissions ==="
    ls -l /etc/shadow /etc/passwd /etc/group /etc/sudoers 2>/dev/null

} > "$REPORT_FILE"

echo "File system security check completed: $REPORT_FILE"
```

### Network Security Configuration

#### Kernel Network Security Parameters
```bash
# Create network security sysctl configuration
cat << 'EOF' > /etc/sysctl.d/99-network-security.conf
# IP Spoofing protection
net.ipv4.conf.all.rp_filter = 1
net.ipv4.conf.default.rp_filter = 1

# Ignore ICMP ping requests
net.ipv4.icmp_echo_ignore_all = 0
net.ipv4.icmp_echo_ignore_broadcasts = 1

# Disable source packet routing
net.ipv4.conf.all.accept_source_route = 0
net.ipv6.conf.all.accept_source_route = 0
net.ipv4.conf.default.accept_source_route = 0
net.ipv6.conf.default.accept_source_route = 0

# Ignore send redirects
net.ipv4.conf.all.send_redirects = 0
net.ipv4.conf.default.send_redirects = 0

# Disable ICMP redirects
net.ipv4.conf.all.accept_redirects = 0
net.ipv6.conf.all.accept_redirects = 0
net.ipv4.conf.default.accept_redirects = 0
net.ipv6.conf.default.accept_redirects = 0

# Ignore bogus ICMP errors
net.ipv4.icmp_ignore_bogus_error_responses = 1

# Enable TCP SYN cookies
net.ipv4.tcp_syncookies = 1

# Log Martian packets
net.ipv4.conf.all.log_martians = 1

# Ignore IPv6 router advertisements
net.ipv6.conf.all.accept_ra = 0
net.ipv6.conf.default.accept_ra = 0

# Disable IPv6 if not needed
net.ipv6.conf.all.disable_ipv6 = 1
net.ipv6.conf.default.disable_ipv6 = 1

# TCP security settings
net.ipv4.tcp_timestamps = 0
net.ipv4.tcp_sack = 1
net.ipv4.tcp_window_scaling = 1

# Control network buffer sizes
net.core.rmem_max = 16777216
net.core.wmem_max = 16777216
net.ipv4.tcp_rmem = 4096 87380 16777216
net.ipv4.tcp_wmem = 4096 65536 16777216
EOF

# Apply network security settings
sysctl --system
echo "Network security parameters applied"
```

## Advanced Security Hardening

### Kernel Security Parameters

#### Advanced Kernel Hardening
```bash
# Advanced kernel security configuration
cat << 'EOF' > /etc/sysctl.d/99-kernel-security.conf
# Hide kernel pointers from unprivileged users
kernel.kptr_restrict = 2

# Restrict access to kernel logs
kernel.dmesg_restrict = 1

# Restrict ptrace scope (prevent process debugging)
kernel.yama.ptrace_scope = 3

# Disable core dumps for SUID programs
fs.suid_dumpable = 0

# Address space layout randomization (maximum)
kernel.randomize_va_space = 2

# Control system request debug functionality
kernel.sysrq = 0

# Control BPF system call access
kernel.unprivileged_bpf_disabled = 1

# Restrict performance events
kernel.perf_event_paranoid = 3

# Control userfaultfd system call
vm.unprivileged_userfaultfd = 0

# Restrict kernel module loading (set after boot)
# kernel.modules_disabled = 1

# Control access to /proc/kallsyms
kernel.kptr_restrict = 2

# Restrict access to kernel debug features
kernel.debug_exception_notify_user = 0
EOF

sysctl --system
echo "Advanced kernel security parameters applied"
```

#### Kernel Module Security
```bash
# List loaded kernel modules
lsmod > /tmp/loaded_modules.txt

# Create kernel module blacklist
cat << 'EOF' > /etc/modprobe.d/blacklist-security.conf
# Disable unused network protocols
blacklist dccp
blacklist sctp
blacklist rds
blacklist tipc

# Disable unused filesystems
blacklist cramfs
blacklist freevxfs
blacklist jffs2
blacklist hfs
blacklist hfsplus
blacklist squashfs
blacklist udf

# Disable unused drivers
blacklist usb-storage
blacklist firewire-core
blacklist thunderbolt
EOF

# Update initramfs
update-initramfs -u 2>/dev/null || dracut -f 2>/dev/null

echo "Kernel module blacklist applied"
```

### Process and Memory Security

#### Process Security Limits
```bash
# Configure comprehensive process limits
cat << 'EOF' > /etc/security/limits.d/99-security.conf
# Disable core dumps for all users
* hard core 0

# Limit process counts per user
* soft nproc 4096
* hard nproc 8192

# Limit file descriptors per user
* soft nofile 8192
* hard nofile 16384

# Limit memory usage per user (in KB)
* soft rss 1048576
* hard rss 2097152

# Limit CPU time per user (in minutes)
* soft cpu 60
* hard cpu 120

# Limit maximum file size (in KB)
* soft fsize 1048576
* hard fsize 2097152

# Limit stack size (in KB)
* soft stack 8192
* hard stack 16384

# Root user limits (more permissive)
root soft nproc unlimited
root hard nproc unlimited
root soft nofile 65536
root hard nofile 65536
EOF

# Configure PAM to enforce limits
grep -q "pam_limits.so" /etc/pam.d/common-session || \
echo "session required pam_limits.so" >> /etc/pam.d/common-session

# Memory protection
cat << 'EOF' > /etc/sysctl.d/99-memory-security.conf
# Minimum virtual address space for mmap
vm.mmap_min_addr = 65536

# Control memory overcommit
vm.overcommit_memory = 2
vm.overcommit_ratio = 80

# Disable swap if possible for security
# vm.swappiness = 1

# Control shared memory
kernel.shmmni = 4096
kernel.shmall = 268435456
kernel.shmmax = 68719476736
EOF

sysctl --system
```

### Security Profiles and Mandatory Access Control

#### AppArmor Configuration (Ubuntu/Debian)
```bash
# Install and enable AppArmor
apt install apparmor apparmor-profiles apparmor-utils

# Enable AppArmor
systemctl enable apparmor
systemctl start apparmor

# Check AppArmor status
aa-status

# Set profiles to enforce mode
aa-enforce /etc/apparmor.d/*

# Create custom AppArmor profile example
cat << 'EOF' > /etc/apparmor.d/usr.local.bin.custom-app
#include <tunables/global>

/usr/local/bin/custom-app {
  #include <abstractions/base>

  # Executable permissions
  /usr/local/bin/custom-app mr,

  # Library access
  /lib/x86_64-linux-gnu/lib*.so* mr,
  /usr/lib/x86_64-linux-gnu/lib*.so* mr,

  # Configuration access
  /etc/custom-app/** r,

  # Data directory access
  /var/lib/custom-app/** rw,

  # Log access
  /var/log/custom-app/ rw,
  /var/log/custom-app/** rw,

  # Deny dangerous capabilities
  deny capability sys_admin,
  deny capability sys_module,
  deny capability sys_rawio,
}
EOF

# Load the profile
apparmor_parser -r /etc/apparmor.d/usr.local.bin.custom-app
```

#### SELinux Configuration (RHEL/CentOS)
```bash
# Check SELinux status
getenforce
sestatus

# Set SELinux to enforcing mode
setenforce 1
sed -i 's/SELINUX=.*/SELINUX=enforcing/' /etc/selinux/config

# Install SELinux management tools
dnf install policycoreutils-python-utils setroubleshoot-server

# Common SELinux operations
# Set file contexts
setsebool -P httpd_can_network_connect 1
setsebool -P httpd_can_network_relay 1

# View SELinux denials
sealert -a /var/log/audit/audit.log

# Create custom SELinux policy (example)
# Use audit2allow to generate policy from denials
audit2allow -a -M mypolicy < /var/log/audit/audit.log
semodule -i mypolicy.pp
```

## Security Hardening Validation

### Automated Hardening Check Script
```bash
#!/bin/bash
# security-hardening-check.sh

SCORE=0
TOTAL_CHECKS=0

check_passed() {
    echo "✓ $1"
    ((SCORE++))
}

check_failed() {
    echo "✗ $1"
}

echo "=== Security Hardening Validation ==="

# Check 1: SSH Root Login
((TOTAL_CHECKS++))
if grep -q "PermitRootLogin no" /etc/ssh/sshd_config; then
    check_passed "SSH root login disabled"
else
    check_failed "SSH root login not disabled"
fi

# Check 2: Password Authentication
((TOTAL_CHECKS++))
if grep -q "PasswordAuthentication no" /etc/ssh/sshd_config; then
    check_passed "SSH password authentication disabled"
else
    check_failed "SSH password authentication not disabled"
fi

# Check 3: Automatic Updates
((TOTAL_CHECKS++))
if [[ -f /etc/apt/apt.conf.d/50unattended-upgrades ]] || [[ -f /etc/dnf/automatic.conf ]]; then
    check_passed "Automatic security updates configured"
else
    check_failed "Automatic security updates not configured"
fi

# Check 4: Network Security Parameters
((TOTAL_CHECKS++))
if sysctl net.ipv4.conf.all.rp_filter | grep -q "= 1"; then
    check_passed "IP spoofing protection enabled"
else
    check_failed "IP spoofing protection not enabled"
fi

# Check 5: Kernel Security Parameters
((TOTAL_CHECKS++))
if sysctl kernel.dmesg_restrict | grep -q "= 1"; then
    check_passed "Kernel log access restricted"
else
    check_failed "Kernel log access not restricted"
fi

# Check 6: Core Dumps Disabled
((TOTAL_CHECKS++))
if grep -q "* hard core 0" /etc/security/limits.d/99-security.conf 2>/dev/null; then
    check_passed "Core dumps disabled"
else
    check_failed "Core dumps not disabled"
fi

# Check 7: File Permissions
((TOTAL_CHECKS++))
if [[ $(stat -c %a /etc/shadow) == "600" ]]; then
    check_passed "Shadow file permissions correct"
else
    check_failed "Shadow file permissions incorrect"
fi

# Check 8: Unnecessary Services
((TOTAL_CHECKS++))
RUNNING_RISKY_SERVICES=$(systemctl is-active telnet rsh vsftpd xinetd 2>/dev/null | grep -c "active" || echo "0")
if [[ $RUNNING_RISKY_SERVICES -eq 0 ]]; then
    check_passed "No risky services running"
else
    check_failed "$RUNNING_RISKY_SERVICES risky services still running"
fi

echo ""
echo "Security Score: $SCORE/$TOTAL_CHECKS ($(( SCORE * 100 / TOTAL_CHECKS ))%)"

if [[ $SCORE -eq $TOTAL_CHECKS ]]; then
    echo "🎉 Excellent! All security checks passed."
elif [[ $SCORE -gt $((TOTAL_CHECKS * 3 / 4)) ]]; then
    echo "👍 Good security posture. Address remaining issues."
elif [[ $SCORE -gt $((TOTAL_CHECKS / 2)) ]]; then
    echo "⚠️  Moderate security. Significant improvements needed."
else
    echo "🚨 Poor security posture. Immediate action required."
fi
```

### CIS Benchmark Compliance Check
```bash
#!/bin/bash
# cis-benchmark-check.sh

echo "=== CIS Benchmark Compliance Check ==="

# 1.1.1.1 Ensure mounting of cramfs filesystems is disabled
if modprobe -n -v cramfs 2>&1 | grep -q "install /bin/true"; then
    echo "✓ cramfs filesystem disabled"
else
    echo "✗ cramfs filesystem not disabled"
fi

# 1.3.1 Ensure AIDE is installed
if command -v aide &>/dev/null; then
    echo "✓ AIDE is installed"
else
    echo "✗ AIDE is not installed"
fi

# 1.4.1 Ensure permissions on bootloader config are configured
GRUB_CONFIG=""
[[ -f /boot/grub/grub.cfg ]] && GRUB_CONFIG="/boot/grub/grub.cfg"
[[ -f /boot/grub2/grub.cfg ]] && GRUB_CONFIG="/boot/grub2/grub.cfg"

if [[ -n "$GRUB_CONFIG" ]]; then
    PERMS=$(stat -c %a "$GRUB_CONFIG")
    if [[ "$PERMS" == "600" ]]; then
        echo "✓ Bootloader config permissions correct"
    else
        echo "✗ Bootloader config permissions incorrect ($PERMS)"
    fi
fi

# 2.1.1 Ensure xinetd is not installed
if ! command -v xinetd &>/dev/null; then
    echo "✓ xinetd is not installed"
else
    echo "✗ xinetd is installed"
fi

# 3.1.1 Ensure IP forwarding is disabled
if sysctl net.ipv4.ip_forward | grep -q "= 0"; then
    echo "✓ IP forwarding disabled"
else
    echo "✗ IP forwarding not disabled"
fi

# 4.1.1.1 Ensure auditd is installed
if command -v auditd &>/dev/null; then
    echo "✓ auditd is installed"
else
    echo "✗ auditd is not installed"
fi

# 5.2.5 Ensure SSH root login is disabled
if grep -q "PermitRootLogin no" /etc/ssh/sshd_config; then
    echo "✓ SSH root login disabled"
else
    echo "✗ SSH root login not disabled"
fi

echo "CIS Benchmark check completed"
```