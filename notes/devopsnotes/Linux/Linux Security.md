# Linux Security

## Security Auditing and Monitoring

### Linux Audit Framework (auditd)

#### Audit System Configuration

```bash
# Install and enable auditd
systemctl enable auditd
systemctl start auditd
systemctl status auditd

# Main configuration file: /etc/audit/auditd.conf
cat << 'EOF' > /etc/audit/auditd.conf
# Audit daemon configuration
log_file = /var/log/audit/audit.log
log_group = root
log_format = RAW
flush = INCREMENTAL_ASYNC
freq = 50
max_log_file = 50
num_logs = 10
priority_boost = 4
disp_qos = lossy
dispatcher = /sbin/audispd
name_format = NONE
max_log_file_action = ROTATE
space_left = 75
space_left_action = SYSLOG
verify_email = yes
action_mail_acct = root
admin_space_left = 50
admin_space_left_action = SUSPEND
disk_full_action = SUSPEND
disk_error_action = SUSPEND
use_libwrap = yes
tcp_listen_port = 60
tcp_listen_queue = 5
tcp_max_per_addr = 1
tcp_client_ports = 1024-65535
tcp_client_max_idle = 0
enable_krb5 = no
krb5_principal = auditd
EOF
```

#### Audit Rules Configuration

```bash
# Create comprehensive audit rules: /etc/audit/rules.d/audit.rules
cat << 'EOF' > /etc/audit/rules.d/audit.rules
# Delete all previous rules
-D

# Set buffer size
-b 8192

# Set failure mode
-f 1

# Monitor important files and directories
-w /etc/passwd -p wa -k passwd_changes
-w /etc/shadow -p wa -k shadow_changes
-w /etc/group -p wa -k group_changes
-w /etc/gshadow -p wa -k gshadow_changes
-w /etc/sudoers -p wa -k sudoers_changes
-w /etc/sudoers.d/ -p wa -k sudoers_changes

# Monitor SSH configuration
-w /etc/ssh/sshd_config -p wa -k ssh_config
-w /etc/ssh/ -p wa -k ssh_config

# Monitor systemd configuration
-w /etc/systemd/ -p wa -k systemd_config
-w /lib/systemd/ -p wa -k systemd_config

# Monitor cron jobs
-w /etc/cron.allow -p wa -k cron_config
-w /etc/cron.deny -p wa -k cron_config
-w /etc/cron.d/ -p wa -k cron_config
-w /etc/cron.daily/ -p wa -k cron_config
-w /etc/cron.hourly/ -p wa -k cron_config
-w /etc/cron.monthly/ -p wa -k cron_config
-w /etc/cron.weekly/ -p wa -k cron_config
-w /etc/crontab -p wa -k cron_config

# Monitor network configuration
-w /etc/hosts -p wa -k network_config
-w /etc/hostname -p wa -k network_config
-w /etc/resolv.conf -p wa -k network_config
-w /etc/network/ -p wa -k network_config

# Monitor system calls
-a always,exit -F arch=b64 -S execve -k command_exec
-a always,exit -F arch=b32 -S execve -k command_exec
-a always,exit -F arch=b64 -S open -k file_access
-a always,exit -F arch=b64 -S openat -k file_access
-a always,exit -F arch=b64 -S unlink -k file_deletion
-a always,exit -F arch=b64 -S unlinkat -k file_deletion

# Monitor network connections
-a always,exit -F arch=b64 -S socket -k network_connect
-a always,exit -F arch=b64 -S connect -k network_connect
-a always,exit -F arch=b64 -S accept -k network_accept

# Monitor privilege escalation
-a always,exit -F arch=b64 -S setuid -k privilege_escalation
-a always,exit -F arch=b64 -S setgid -k privilege_escalation
-a always,exit -F arch=b64 -S setreuid -k privilege_escalation
-a always,exit -F arch=b64 -S setregid -k privilege_escalation

# Monitor file permission changes
-a always,exit -F arch=b64 -S chmod -k perm_changes
-a always,exit -F arch=b64 -S fchmod -k perm_changes
-a always,exit -F arch=b64 -S fchmodat -k perm_changes
-a always,exit -F arch=b64 -S chown -k owner_changes
-a always,exit -F arch=b64 -S fchown -k owner_changes
-a always,exit -F arch=b64 -S lchown -k owner_changes
-a always,exit -F arch=b64 -S fchownat -k owner_changes

# Make configuration immutable
-e 2
EOF

# Load audit rules
augenrules --load
systemctl restart auditd
```

#### Audit Log Analysis

```bash
# Search audit logs
ausearch -k passwd_changes              # Search by key
ausearch -ui 1000                       # Search by user ID
ausearch -p 1234                        # Search by process ID
ausearch -ts today                      # Search by time (today)
ausearch -ts 10:00:00 -te 11:00:00     # Search time range
ausearch -f /etc/passwd                 # Search by file
ausearch -sc execve                     # Search by system call
ausearch -sv yes                        # Successful events only
ausearch -sv no                         # Failed events only
ausearch -m LOGIN                       # Search by message type

# Generate audit reports
aureport                                # Summary report
aureport --summary                      # Detailed summary
aureport -u                            # User summary
aureport -f                            # File summary
aureport -s                            # Syscall summary
aureport -n                            # Network summary
aureport --login                       # Login report
aureport --failed                      # Failed events
aureport -ts today                     # Today's report

# Real-time monitoring
ausearch -ts recent | tail -f          # Monitor recent events
tail -f /var/log/audit/audit.log | ausearch --input-logs

# Advanced analysis
# Extract command executions
ausearch -k command_exec -i | grep -E "exe=|proctitle="

# Monitor failed login attempts
ausearch -k failed_login -ts today -i

# Check for privilege escalation attempts
ausearch -k privilege_escalation -i
```

### File Integrity Monitoring

#### AIDE (Advanced Intrusion Detection Environment)

```bash
# Install AIDE
apt install aide aide-common          # Debian/Ubuntu
yum install aide                      # RHEL/CentOS

# Configuration file: /etc/aide/aide.conf
cat << 'EOF' > /etc/aide/aide.conf
# AIDE configuration
database_in = file:/var/lib/aide/aide.db
database_out = file:/var/lib/aide/aide.db.new
database_new = file:/var/lib/aide/aide.db.new
gzip_dbout = yes

# Default rules
All = p+i+n+u+g+s+m+c+md5+sha1+sha256+rmd160+tiger+haval+gost+crc32
Norm = s+n+b+md5+sha1+sha256+rmd160+tiger+haval+gost+crc32
Dir = p+i+n+u+g+acl+selinux+xattrs
LooseDir = p+i+n+u+g+acl+selinux+xattrs
VarDir = p+i+n+u+g+acl+selinux+xattrs
Log = p+u+g+n+S+acl+selinux+xattrs
VarLog = p+u+g+n+S+acl+selinux+xattrs
VarFile = p+u+g+n+acl+selinux+xattrs
StaticFile = p+i+n+u+g+s+acl+selinux+xattrs+md5+sha1+sha256+rmd160+tiger+haval+gost+crc32

# Monitored directories
/boot           StaticFile
/bin            StaticFile
/sbin           StaticFile
/lib            StaticFile
/lib64          StaticFile
/opt            StaticFile
/usr            StaticFile
/etc            Norm
/var/log        VarLog
/var/run        VarDir
/var/lib        VarDir

# Exclusions
!/proc
!/sys
!/dev
!/tmp
!/var/tmp
!/home
!/root/.bash_history
!/var/log/aide.log
EOF

# Initialize AIDE database
aide --init
cp /var/lib/aide/aide.db.new /var/lib/aide/aide.db

# Run integrity check
aide --check
aide --check --verbose

# Update database after legitimate changes
aide --update
cp /var/lib/aide/aide.db.new /var/lib/aide/aide.db

# Automated daily checks
cat << 'EOF' > /etc/cron.daily/aide-check
#!/bin/bash
/usr/bin/aide --check | /bin/mail -s "AIDE Report $(hostname)" root
EOF
chmod +x /etc/cron.daily/aide-check
```

#### Custom File Integrity Monitoring

```bash
# Simple checksum-based monitoring
create_integrity_baseline() {
    local watch_dirs=("/etc" "/usr/bin" "/usr/sbin" "/boot")
    local baseline_file="/var/lib/integrity/baseline.md5"
    
    mkdir -p /var/lib/integrity
    
    for dir in "${watch_dirs[@]}"; do
        if [[ -d "$dir" ]]; then
            find "$dir" -type f -exec md5sum {} \; >> "$baseline_file"
        fi
    done
    
    echo "Baseline created: $baseline_file"
}

check_integrity() {
    local baseline_file="/var/lib/integrity/baseline.md5"
    local current_file="/tmp/current.md5"
    local watch_dirs=("/etc" "/usr/bin" "/usr/sbin" "/boot")
    
    if [[ ! -f "$baseline_file" ]]; then
        echo "ERROR: Baseline file not found. Run create_integrity_baseline first."
        return 1
    fi
    
    # Generate current checksums
    > "$current_file"
    for dir in "${watch_dirs[@]}"; do
        if [[ -d "$dir" ]]; then
            find "$dir" -type f -exec md5sum {} \; >> "$current_file"
        fi
    done
    
    # Compare with baseline
    if diff "$baseline_file" "$current_file" > /dev/null; then
        echo "✓ Integrity check passed"
        return 0
    else
        echo "⚠ Integrity check failed. Changes detected:"
        diff "$baseline_file" "$current_file"
        return 1
    fi
}

# Usage
create_integrity_baseline
check_integrity
```

## System Hardening

### Basic Security Hardening

#### System Updates and Package Management

```bash
# Keep system updated
# Debian/Ubuntu
apt update && apt upgrade -y
apt autoremove -y
apt autoclean

# RHEL/CentOS/Fedora
yum update -y
dnf upgrade -y

# Enable automatic security updates (Ubuntu)
apt install unattended-upgrades
dpkg-reconfigure -plow unattended-upgrades

# Configure automatic updates
cat << 'EOF' > /etc/apt/apt.conf.d/50unattended-upgrades
Unattended-Upgrade::Allowed-Origins {
    "${distro_id}:${distro_codename}-security";
};
Unattended-Upgrade::Remove-Unused-Dependencies "true";
Unattended-Upgrade::Automatic-Reboot "false";
EOF
```

#### Service Hardening

```bash
# Disable unnecessary services
systemctl list-unit-files --state=enabled  # List enabled services

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
)

for service in "${services_to_disable[@]}"; do
    if systemctl is-enabled "$service" &>/dev/null; then
        systemctl disable "$service"
        systemctl stop "$service"
        echo "Disabled $service"
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
)

for package in "${packages_to_remove[@]}"; do
    apt remove --purge "$package" -y 2>/dev/null || yum remove "$package" -y 2>/dev/null
done
```

#### File System Security

```bash
# Find and secure SUID/SGID files
find / -perm -4000 -type f 2>/dev/null > /tmp/suid_files.txt
find / -perm -2000 -type f 2>/dev/null > /tmp/sgid_files.txt

# Review and remove unnecessary SUID/SGID bits
# Example: Remove SUID from specific binaries if not needed
chmod u-s /usr/bin/passwd  # Only if using alternative authentication

# Find world-writable files
find / -perm -002 -type f 2>/dev/null | grep -v /proc | grep -v /sys

# Find files with no owner
find / -nouser -o -nogroup 2>/dev/null

# Secure important directories
chmod 700 /root
chmod 750 /home
chmod 755 /tmp
chmod 1777 /tmp  # Sticky bit for /tmp

# Set proper permissions on critical files
chmod 600 /etc/shadow
chmod 600 /etc/gshadow
chmod 644 /etc/passwd
chmod 644 /etc/group
chmod 600 /boot/grub/grub.cfg
```

#### Network Security Configuration

```bash
# Kernel network security parameters
cat << 'EOF' > /etc/sysctl.d/99-network-security.conf
# IP Spoofing protection
net.ipv4.conf.all.rp_filter = 1
net.ipv4.conf.default.rp_filter = 1

# Ignore ICMP ping requests
net.ipv4.icmp_echo_ignore_all = 1

# Ignore Directed pings
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

# Log Martians
net.ipv4.conf.all.log_martians = 1

# Ignore IPv6 router advertisements
net.ipv6.conf.all.accept_ra = 0
net.ipv6.conf.default.accept_ra = 0
EOF

# Apply network security settings
sysctl --system
```

### Advanced Security Hardening

#### Kernel Security Parameters

```bash
# Advanced kernel hardening
cat << 'EOF' > /etc/sysctl.d/99-kernel-security.conf
# Hide kernel pointers
kernel.kptr_restrict = 2

# Restrict access to kernel logs
kernel.dmesg_restrict = 1

# Restrict ptrace scope
kernel.yama.ptrace_scope = 3

# Disable core dumps
fs.suid_dumpable = 0

# Control kernel module loading
kernel.modules_disabled = 1  # Set only after all needed modules are loaded

# Address space layout randomization
kernel.randomize_va_space = 2

# Restrict access to kernel address exposures
kernel.kguard.kguard = 1

# Control system request debug functionality
kernel.sysrq = 0

# Control BPF system call access
kernel.unprivileged_bpf_disabled = 1

# Restrict performance events
kernel.perf_event_paranoid = 3

# Control userfaultfd system call
vm.unprivileged_userfaultfd = 0
EOF

sysctl --system
```

#### Process and Memory Security

```bash
# Configure process limits
cat << 'EOF' > /etc/security/limits.d/99-security.conf
# Disable core dumps for all users
* hard core 0

# Limit process counts
* soft nproc 4096
* hard nproc 8192

# Limit file descriptors
* soft nofile 8192
* hard nofile 16384

# Limit memory usage (in KB)
* soft rss 1048576
* hard rss 2097152

# Limit CPU time (in minutes)
* soft cpu 60
* hard cpu 120
EOF

# Configure PAM limits
cat << 'EOF' >> /etc/pam.d/common-session
session required pam_limits.so
EOF

# Memory protection
echo 'vm.mmap_min_addr = 65536' >> /etc/sysctl.d/99-memory-security.conf
sysctl vm.mmap_min_addr=65536
```

## Access Control and Authentication

### User Account Security

#### Strong Password Policies

```bash
# Configure password policies with PAM
cat << 'EOF' > /etc/pam.d/common-password
# Password strength requirements
password required pam_pwquality.so retry=3 \
    minlen=12 \
    dcredit=-1 \
    ucredit=-1 \
    lcredit=-1 \
    ocredit=-1 \
    maxrepeat=3 \
    reject_username \
    enforce_for_root

# Password history
password required pam_unix.so use_authtok sha512 shadow remember=12
EOF

# Configure password quality requirements
cat << 'EOF' > /etc/security/pwquality.conf
# Minimum password length
minlen = 12

# Character class requirements
minclass = 3
dcredit = -1    # At least 1 digit
ucredit = -1    # At least 1 uppercase
lcredit = -1    # At least 1 lowercase
ocredit = -1    # At least 1 special character

# Additional restrictions
maxrepeat = 3   # Max consecutive identical characters
maxsequence = 3 # Max sequence of characters
gecoscheck = 1  # Check against GECOS field
dictcheck = 1   # Check against dictionary words
enforcing = 1   # Enforce for all users including root
EOF

# Set password aging policies
cat << 'EOF' >> /etc/login.defs
PASS_MAX_DAYS 90    # Maximum password age
PASS_MIN_DAYS 7     # Minimum password age
PASS_WARN_AGE 14    # Password expiration warning
PASS_MIN_LEN 12     # Minimum password length
EOF

# Apply password aging to existing users
for user in $(grep -E '^[^:]+:[^:]+:[0-9]{4}:' /etc/passwd | cut -d: -f1); do
    chage -M 90 -m 7 -W 14 "$user"
done
```

#### Account Management

```bash
# Lock unused accounts
for user in games news uucp; do
    if id "$user" &>/dev/null; then
        usermod -L "$user"
        usermod -s /usr/sbin/nologin "$user"
    fi
done

# Disable root login (if using sudo)
passwd -l root

# Set account lockout policies
cat << 'EOF' > /etc/pam.d/common-auth
# Account lockout after failed attempts
auth required pam_tally2.so deny=5 unlock_time=1800 onerr=fail

# Standard authentication
auth [success=1 default=ignore] pam_unix.so nullok_secure
auth requisite pam_deny.so
auth required pam_permit.so
EOF

# Monitor failed login attempts
faillog -a                              # Show all failed logins
lastlog | head -20                      # Show last logins
last | head -20                         # Show login history

# Check for users with empty passwords
awk -F: '($2 == "") {print $1}' /etc/shadow

# Check for duplicate UIDs
awk -F: '{print $3}' /etc/passwd | sort | uniq -d

# Check for users with UID 0 (should only be root)
awk -F: '($3 == 0) {print $1}' /etc/passwd
```

### SSH Security Hardening

#### Advanced SSH Configuration

```bash
# Comprehensive SSH hardening: /etc/ssh/sshd_config
cat << 'EOF' > /etc/ssh/sshd_config
# Protocol and encryption
Protocol 2
Port 2222  # Change default port

# Host keys
HostKey /etc/ssh/ssh_host_rsa_key
HostKey /etc/ssh/ssh_host_ecdsa_key
HostKey /etc/ssh/ssh_host_ed25519_key

# Ciphers and algorithms
Ciphers chacha20-poly1305@openssh.com,aes256-gcm@openssh.com,aes128-gcm@openssh.com,aes256-ctr,aes192-ctr,aes128-ctr
MACs hmac-sha2-256-etm@openssh.com,hmac-sha2-512-etm@openssh.com,hmac-sha2-256,hmac-sha2-512
KexAlgorithms curve25519-sha256,curve25519-sha256@libssh.org,diffie-hellman-group14-sha256,diffie-hellman-group16-sha512,diffie-hellman-group18-sha512

# Authentication
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
AuthorizedKeysFile .ssh/authorized_keys
PermitEmptyPasswords no
ChallengeResponseAuthentication no
UsePAM yes

# Connection limits
MaxAuthTries 3
MaxSessions 3
MaxStartups 3:30:10
LoginGraceTime 60

# User restrictions
AllowGroups sshusers
DenyUsers root guest

# Session settings
ClientAliveInterval 300
ClientAliveCountMax 2
TCPKeepAlive no
Compression delayed

# Logging
SyslogFacility AUTHPRIV
LogLevel VERBOSE

# X11 and forwarding
X11Forwarding no
AllowAgentForwarding no
AllowTcpForwarding no
GatewayPorts no
PermitTunnel no

# Misc security
StrictModes yes
IgnoreRhosts yes
HostbasedAuthentication no
PermitUserEnvironment no
AcceptEnv LANG LC_*
PrintMotd no
PrintLastLog yes
Banner /etc/ssh/banner
EOF

# Create SSH banner
cat << 'EOF' > /etc/ssh/banner
****************************************************************************
*                                                                          *
*                     UNAUTHORIZED ACCESS PROHIBITED                      *
*                                                                          *
*    This system is for authorized users only. All activities on this     *
*    system are monitored and recorded. Unauthorized access is            *
*    prohibited and will be prosecuted to the full extent of the law.     *
*                                                                          *
****************************************************************************
EOF

# Restart SSH service
systemctl restart sshd
```

#### SSH Key Management

```bash
# Generate strong SSH keys
ssh-keygen -t ed25519 -b 4096 -f ~/.ssh/id_ed25519 -C "user@hostname"
ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa -C "user@hostname"

# Configure SSH client security: ~/.ssh/config
cat << 'EOF' > ~/.ssh/config
# Global defaults
Host *
    Protocol 2
    Port 2222
    PubkeyAuthentication yes
    PasswordAuthentication no
    ChallengeResponseAuthentication no
    GSSAPIAuthentication no
    HashKnownHosts yes
    Ciphers chacha20-poly1305@openssh.com,aes256-gcm@openssh.com,aes128-gcm@openssh.com
    MACs hmac-sha2-256-etm@openssh.com,hmac-sha2-512-etm@openssh.com
    KexAlgorithms curve25519-sha256,curve25519-sha256@libssh.org,diffie-hellman-group14-sha256
    ServerAliveInterval 300
    ServerAliveCountMax 2
    VisualHostKey yes
    
# Production servers
Host prod-*
    User deploy
    Port 2222
    IdentityFile ~/.ssh/production_key
    IdentitiesOnly yes
    
# Development servers
Host dev-*
    User developer
    Port 22
    IdentityFile ~/.ssh/development_key
    IdentitiesOnly yes
EOF

chmod 600 ~/.ssh/config

# Secure SSH directory and files
chmod 700 ~/.ssh
chmod 600 ~/.ssh/id_*
chmod 644 ~/.ssh/id_*.pub
chmod 600 ~/.ssh/authorized_keys
chmod 600 ~/.ssh/known_hosts
```

## Firewall and Network Security

### iptables Advanced Configuration

```bash
# Comprehensive iptables ruleset
#!/bin/bash
# iptables security script

# Clear existing rules
iptables -F
iptables -X
iptables -t nat -F
iptables -t nat -X
iptables -t mangle -F
iptables -t mangle -X

# Set default policies
iptables -P INPUT DROP
iptables -P FORWARD DROP
iptables -P OUTPUT ACCEPT

# Allow loopback traffic
iptables -A INPUT -i lo -j ACCEPT
iptables -A OUTPUT -o lo -j ACCEPT

# Allow established and related connections
iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT

# Anti-spoofing rules
iptables -A INPUT -s 10.0.0.0/8 -i eth0 -j DROP
iptables -A INPUT -s 169.254.0.0/16 -i eth0 -j DROP
iptables -A INPUT -s 172.16.0.0/12 -i eth0 -j DROP
iptables -A INPUT -s 192.168.0.0/16 -i eth0 -j DROP
iptables -A INPUT -s 224.0.0.0/4 -i eth0 -j DROP
iptables -A INPUT -d 224.0.0.0/4 -i eth0 -j DROP
iptables -A INPUT -s 240.0.0.0/5 -i eth0 -j DROP
iptables -A INPUT -d 240.0.0.0/5 -i eth0 -j DROP
iptables -A INPUT -s 0.0.0.0/8 -i eth0 -j DROP
iptables -A INPUT -d 0.0.0.0/8 -i eth0 -j DROP
iptables -A INPUT -d 239.255.255.0/24 -i eth0 -j DROP
iptables -A INPUT -d 255.255.255.255 -i eth0 -j DROP

# Rate limiting for SSH
iptables -A INPUT -p tcp --dport 2222 -m conntrack --ctstate NEW -m recent --set
iptables -A INPUT -p tcp --dport 2222 -m conntrack --ctstate NEW -m recent --update --seconds 60 --hitcount 4 -j DROP

# Allow SSH from specific networks
iptables -A INPUT -p tcp -s 192.168.1.0/24 --dport 2222 -j ACCEPT

# Allow HTTP and HTTPS
iptables -A INPUT -p tcp --dport 80 -j ACCEPT
iptables -A INPUT -p tcp --dport 443 -j ACCEPT

# Allow monitoring (from specific IPs)
iptables -A INPUT -p tcp -s 192.168.1.100 --dport 9100 -j ACCEPT  # Node exporter

# Drop invalid packets
iptables -A INPUT -m conntrack --ctstate INVALID -j DROP

# Log dropped packets
iptables -A INPUT -m limit --limit 5/min -j LOG --log-prefix "iptables denied: " --log-level 7

# Save rules
iptables-save > /etc/iptables/rules.v4

# Load rules at boot
cat << 'EOF' > /etc/systemd/system/iptables-restore.service
[Unit]
Description=Restore iptables rules
Before=network-pre.target
Wants=network-pre.target

[Service]
Type=oneshot
ExecStart=/sbin/iptables-restore /etc/iptables/rules.v4

[Install]
WantedBy=multi-user.target
EOF

systemctl enable iptables-restore.service
```

### Intrusion Detection and Prevention

#### Fail2ban Configuration

```bash
# Install and configure fail2ban
apt install fail2ban -y

# Main configuration: /etc/fail2ban/jail.local
cat << 'EOF' > /etc/fail2ban/jail.local
[DEFAULT]
# Ban settings
bantime = 3600
findtime = 600
maxretry = 3
backend = systemd

# Email notifications
destemail = admin@example.com
sendername = Fail2Ban
mta = sendmail

# Actions
action = %(action_mw)s

[sshd]
enabled = true
port = 2222
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
bantime = 3600

[nginx-http-auth]
enabled = true
filter = nginx-http-auth
logpath = /var/log/nginx/error.log
maxretry = 3

[nginx-limit-req]
enabled = true
filter = nginx-limit-req
logpath = /var/log/nginx/error.log
maxretry = 5

[postfix]
enabled = true
filter = postfix
logpath = /var/log/mail.log
maxretry = 3

[dovecot]
enabled = true
filter = dovecot
logpath = /var/log/mail.log
maxretry = 3
EOF

# Custom filter for application logs
cat << 'EOF' > /etc/fail2ban/filter.d/myapp.conf
[Definition]
failregex = ^<HOST> - - \[.*\] "(GET|POST|HEAD)" .* (401|403) .*$
ignoreregex =
EOF

# Enable and start fail2ban
systemctl enable fail2ban
systemctl start fail2ban

# Manage fail2ban
fail2ban-client status                  # Show status
fail2ban-client status sshd             # Show jail status
fail2ban-client set sshd unbanip <IP>   # Unban IP
fail2ban-client reload                  # Reload configuration
```

This comprehensive Linux security guide covers essential security practices including auditing, hardening, access control, and network security, providing a robust foundation for secure Linux system administration in DevOps environments.