# Linux Package Management Troubleshooting

**Package management troubleshooting** covers resolving common issues with package installation, dependency conflicts, repository problems, and system recovery scenarios.

## Common Package Management Issues

### Dependency Conflicts

#### Broken Dependencies (Debian/Ubuntu)
```bash
# Identify broken packages
apt --fix-broken install
apt-get check
dpkg --audit

# Fix dependency issues
apt install -f
apt autoremove
apt autoclean

# Force package configuration
dpkg --configure -a
dpkg --configure --pending

# Remove problematic packages
apt remove --purge problematic_package
apt autoremove --purge
```

#### Dependency Hell Resolution
```bash
# Show dependency tree
apt-cache depends package_name
apt-cache rdepends package_name

# Simulate package operations
apt install -s package_name
apt remove -s package_name

# Force package installation
apt install --no-install-recommends package_name
apt install --allow-downgrades package_name

# Pin package versions to prevent conflicts
cat << 'EOF' > /etc/apt/preferences.d/pin-package
Package: problematic_package
Pin: version 1.0.0
Pin-Priority: 1001
EOF
```

#### RPM Dependency Issues
```bash
# Check for dependency problems
dnf check
rpm -V --all

# Resolve dependency conflicts
dnf install --best --allowerasing package_name
dnf install --nobest package_name
dnf install --skip-broken package_name

# Force package installation (use carefully)
rpm -ivh --force --nodeps package.rpm

# Downgrade packages
dnf downgrade package_name
dnf install package_name-older_version
```

### Repository Problems

#### Repository Access Issues
```bash
# Update repository lists
apt update
dnf makecache

# Check repository connectivity
ping archive.ubuntu.com
curl -I https://repo.company.com

# Validate repository URLs
cat /etc/apt/sources.list
ls /etc/apt/sources.list.d/
cat /etc/yum.repos.d/*.repo

# Test specific repository
apt-cache policy
dnf repolist
dnf repoinfo repository_name
```

#### GPG Key Problems
```bash
# Debian/Ubuntu GPG issues
apt-key list
apt-key adv --recv-keys --keyserver keyserver.ubuntu.com KEY_ID

# Modern key management
curl -fsSL https://repo.example.com/key.gpg | gpg --dearmor -o /usr/share/keyrings/repo.gpg

# RPM GPG issues
rpm --import https://repo.example.com/RPM-GPG-KEY
rpm -q gpg-pubkey
rpm --checksig package.rpm

# Disable GPG checking (temporary)
apt install --allow-unauthenticated package_name
dnf install --nogpgcheck package_name
```

#### Repository Corruption
```bash
# Clean repository cache
apt clean
apt autoclean
rm -rf /var/lib/apt/lists/*
apt update

# DNF cache cleanup
dnf clean all
dnf clean metadata
dnf makecache --refresh

# Reset repository configuration
mv /etc/apt/sources.list /etc/apt/sources.list.backup
# Recreate sources.list with known good repositories
```

### Lock File Issues

#### APT Lock Problems
```bash
# Check for running package managers
ps aux | grep -E '(apt|dpkg)'
lsof /var/lib/dpkg/lock*
lsof /var/cache/apt/archives/lock

# Remove lock files (only if no processes running)
rm /var/lib/apt/lists/lock
rm /var/cache/apt/archives/lock
rm /var/lib/dpkg/lock*

# Fix interrupted dpkg operations
dpkg --configure -a
apt install -f
```

#### DNF/YUM Lock Issues
```bash
# Check for running package managers
ps aux | grep -E '(dnf|yum)'

# Remove lock files
rm -f /var/run/yum.pid
rm -f /var/cache/dnf/metadata_lock.pid

# Clear transaction history if needed
dnf history
dnf history undo last
```

## Database Corruption Issues

### RPM Database Corruption
```bash
# Check database integrity
rpm --rebuilddb
rpm --initdb

# Verify database
rpm -qa | wc -l
rpm -Va | head -20

# Backup and rebuild database
cp -r /var/lib/rpm /var/lib/rpm.backup
rpm --rebuilddb --dbpath /var/lib/rpm

# If severely corrupted
rm -f /var/lib/rpm/__db*
rpm --rebuilddb
```

### DPKG Database Issues
```bash
# Check dpkg database
dpkg --audit
dpkg --verify

# Fix database inconsistencies
dpkg --configure -a
apt install -f

# Rebuild package information
apt-cache gencaches
apt update
```

## Performance Issues

### Slow Package Operations
```bash
# Enable parallel downloads (APT)
echo 'APT::Acquire::Queue-Mode "host";' > /etc/apt/apt.conf.d/99parallel

# DNF parallel downloads
echo 'max_parallel_downloads=10' >> /etc/dnf/dnf.conf
echo 'fastestmirror=True' >> /etc/dnf/dnf.conf

# Check mirror performance
apt-get update -o Debug::Acquire::http=true
dnf repolist -v

# Use local mirror
# Edit sources.list to use geographically closer mirrors
```

### Disk Space Issues
```bash
# Check available space
df -h /var/cache/apt/
df -h /var/cache/dnf/

# Clean package cache
apt clean
apt autoclean
dnf clean packages
dnf clean all

# Remove old kernels (Ubuntu)
apt autoremove --purge

# Remove old packages (RHEL)
dnf remove $(dnf repoquery --installonly --latest-limit=-2 -q)
```

## Network and Connectivity Issues

### Proxy Configuration
```bash
# APT proxy configuration
cat << 'EOF' > /etc/apt/apt.conf.d/01proxy
Acquire::http::Proxy "http://proxy.company.com:8080";
Acquire::https::Proxy "http://proxy.company.com:8080";
EOF

# Environment proxy variables
export http_proxy=http://proxy.company.com:8080
export https_proxy=http://proxy.company.com:8080
export no_proxy=localhost,127.0.0.1,.company.com

# DNF proxy configuration
echo 'proxy=http://proxy.company.com:8080' >> /etc/dnf/dnf.conf
```

### SSL/TLS Issues
```bash
# Check SSL certificates
curl -v https://repo.example.com

# Update CA certificates
apt update && apt install ca-certificates
dnf update ca-certificates

# Temporarily disable SSL verification (not recommended)
echo 'Acquire::https::Verify-Peer "false";' > /etc/apt/apt.conf.d/99ssl
echo 'sslverify=False' >> /etc/dnf/dnf.conf
```

### DNS Resolution Problems
```bash
# Test DNS resolution
nslookup archive.ubuntu.com
dig archive.ubuntu.com

# Check DNS configuration
cat /etc/resolv.conf

# Use alternative DNS
echo 'nameserver 8.8.8.8' >> /etc/resolv.conf
echo 'nameserver 1.1.1.1' >> /etc/resolv.conf
```

## Emergency Recovery

### System Recovery from Package Issues
```bash
# Boot from rescue media or single-user mode
# Mount root filesystem
mount /dev/sda1 /mnt
mount --bind /dev /mnt/dev
mount --bind /proc /mnt/proc
mount --bind /sys /mnt/sys
chroot /mnt

# Fix package database
dpkg --configure -a
apt install -f

# Reinstall critical packages
apt install --reinstall ubuntu-minimal
apt install --reinstall systemd
```

### Package Manager Recovery
```bash
# Recover APT
apt install --reinstall apt
apt update
apt install -f

# Recover DNF/YUM
dnf reinstall dnf
dnf clean all
dnf makecache
```

### Critical System Package Recovery
```bash
# Download packages manually
wget http://archive.ubuntu.com/ubuntu/pool/main/a/apt/apt_*.deb
dpkg -i apt_*.deb

# Use different package manager temporarily
snap install --classic dpkg
flatpak install org.freedesktop.Platform

# Compile from source as last resort
wget https://source.package.com/package.tar.gz
tar xzf package.tar.gz
cd package
./configure --prefix=/usr/local
make && make install
```

## Diagnostic Tools and Commands

### Package Management Diagnostics Script
```bash
#!/bin/bash
# package-diagnostics.sh

LOG_FILE="/tmp/package-diagnostics-$(date +%Y%m%d-%H%M%S).log"

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

log "=== Package Management Diagnostics ==="

# System information
log "System Information:"
uname -a >> "$LOG_FILE"
cat /etc/os-release >> "$LOG_FILE"

# Disk space
log "Disk Space:"
df -h | grep -E '(var|tmp)' >> "$LOG_FILE"

# Package manager detection and status
if command -v apt >/dev/null 2>&1; then
    log "APT Package Manager Detected"

    log "APT Status:"
    apt-cache stats >> "$LOG_FILE" 2>&1

    log "Repository Status:"
    apt-cache policy >> "$LOG_FILE" 2>&1

    log "Broken Packages:"
    dpkg --audit >> "$LOG_FILE" 2>&1

    log "Available Updates:"
    apt list --upgradable >> "$LOG_FILE" 2>&1

    log "Package Locks:"
    lsof /var/lib/dpkg/lock* >> "$LOG_FILE" 2>&1 || echo "No locks found" >> "$LOG_FILE"

elif command -v dnf >/dev/null 2>&1; then
    log "DNF Package Manager Detected"

    log "DNF Status:"
    dnf check >> "$LOG_FILE" 2>&1

    log "Repository Status:"
    dnf repolist >> "$LOG_FILE" 2>&1

    log "Available Updates:"
    dnf check-update >> "$LOG_FILE" 2>&1 || true

    log "Transaction History:"
    dnf history | head -10 >> "$LOG_FILE" 2>&1
fi

# Network connectivity
log "Network Connectivity:"
if command -v apt >/dev/null 2>&1; then
    timeout 10 wget -q --spider http://archive.ubuntu.com && echo "Ubuntu archive accessible" >> "$LOG_FILE" || echo "Ubuntu archive not accessible" >> "$LOG_FILE"
elif command -v dnf >/dev/null 2>&1; then
    timeout 10 curl -s --head https://download.fedoraproject.org >/dev/null && echo "Fedora mirror accessible" >> "$LOG_FILE" || echo "Fedora mirror not accessible" >> "$LOG_FILE"
fi

# GPG keys
log "GPG Keys:"
if command -v apt >/dev/null 2>&1; then
    apt-key list >> "$LOG_FILE" 2>&1
elif command -v dnf >/dev/null 2>&1; then
    rpm -q gpg-pubkey >> "$LOG_FILE" 2>&1
fi

log "Diagnostics completed. Report saved to: $LOG_FILE"
```

### Package Health Check Script
```bash
#!/bin/bash
# package-health-check.sh

ISSUES_FOUND=0

check_issue() {
    local test_name="$1"
    local test_command="$2"

    echo -n "Checking $test_name... "

    if eval "$test_command" >/dev/null 2>&1; then
        echo "OK"
    else
        echo "FAILED"
        ((ISSUES_FOUND++))
    fi
}

echo "=== Package Management Health Check ==="

# Check disk space
check_issue "disk space" "[ $(df /var | tail -1 | awk '{print $4}') -gt 1000000 ]"

# Check package database
if command -v apt >/dev/null 2>&1; then
    check_issue "dpkg database" "dpkg --audit | grep -q '^$'"
    check_issue "apt repositories" "apt update"
    check_issue "broken packages" "apt-get check"
elif command -v dnf >/dev/null 2>&1; then
    check_issue "rpm database" "rpm -qa | wc -l | grep -q '[0-9]'"
    check_issue "dnf repositories" "dnf makecache"
    check_issue "package consistency" "dnf check"
fi

# Check network connectivity
check_issue "internet connectivity" "ping -c 1 8.8.8.8"

# Check lock files
check_issue "no package locks" "! pgrep -f 'apt|dpkg|dnf|yum'"

echo ""
if [ $ISSUES_FOUND -eq 0 ]; then
    echo "✅ All checks passed!"
else
    echo "❌ Found $ISSUES_FOUND issue(s)"
    echo "Run package-diagnostics.sh for detailed information"
fi
```

### Automated Package Repair Script
```bash
#!/bin/bash
# package-repair.sh

set -euo pipefail

BACKUP_DIR="/var/backups/package-repair-$(date +%Y%m%d-%H%M%S)"

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1"
}

# Create backup
create_backup() {
    log "Creating backup in $BACKUP_DIR"
    mkdir -p "$BACKUP_DIR"

    if command -v apt >/dev/null 2>&1; then
        cp -r /var/lib/dpkg "$BACKUP_DIR/"
        cp -r /etc/apt "$BACKUP_DIR/"
    elif command -v dnf >/dev/null 2>&1; then
        cp -r /var/lib/rpm "$BACKUP_DIR/"
        cp -r /etc/yum.repos.d "$BACKUP_DIR/"
    fi
}

# Repair APT
repair_apt() {
    log "Repairing APT package manager"

    # Fix broken packages
    apt --fix-broken install -y

    # Configure pending packages
    dpkg --configure -a

    # Clean cache
    apt autoclean
    apt autoremove -y

    # Update package lists
    apt update

    log "APT repair completed"
}

# Repair DNF
repair_dnf() {
    log "Repairing DNF package manager"

    # Check and fix issues
    dnf check

    # Clean cache
    dnf clean all
    dnf makecache

    # Fix any issues
    dnf autoremove -y

    log "DNF repair completed"
}

# Main repair function
main() {
    log "Starting package management repair"

    create_backup

    if command -v apt >/dev/null 2>&1; then
        repair_apt
    elif command -v dnf >/dev/null 2>&1; then
        repair_dnf
    else
        log "ERROR: No supported package manager found"
        exit 1
    fi

    log "Package management repair completed successfully"
    log "Backup created in: $BACKUP_DIR"
}

main "$@"
```