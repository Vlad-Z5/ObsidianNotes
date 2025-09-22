# Linux Package Management Security Updates

**Security updates and patching** ensure system security through automated vulnerability management, compliance scanning, and systematic patch deployment processes.

## Automated Security Updates

### Ubuntu/Debian Unattended Upgrades

#### Installation and Setup
```bash
# Install unattended-upgrades
apt install unattended-upgrades apt-listchanges

# Check current configuration
dpkg-reconfigure -plow unattended-upgrades

# Manual configuration files
ls /etc/apt/apt.conf.d/
# Key files: 20auto-upgrades, 50unattended-upgrades
```

#### Configuration
```bash
# Main configuration: /etc/apt/apt.conf.d/50unattended-upgrades
cat << 'EOF' > /etc/apt/apt.conf.d/50unattended-upgrades
Unattended-Upgrade::Allowed-Origins {
    "${distro_id}:${distro_codename}-security";
    "${distro_id} ESMApps:${distro_codename}-apps-security";
    "${distro_id} ESM:${distro_codename}-infra-security";
    // "${distro_id}:${distro_codename}-updates";  // Uncomment for all updates
};

// Packages to never upgrade automatically
Unattended-Upgrade::Package-Blacklist {
    "kernel*";
    "linux-*";
    "docker*";
    "kubernetes*";
    "mysql*";
    "postgresql*";
};

// Advanced options
Unattended-Upgrade::AutoFixInterruptedDpkg "true";
Unattended-Upgrade::MinimalSteps "true";
Unattended-Upgrade::InstallOnShutdown "false";
Unattended-Upgrade::Remove-Unused-Dependencies "true";
Unattended-Upgrade::Remove-New-Unused-Dependencies "true";

// Reboot options
Unattended-Upgrade::Automatic-Reboot "false";
Unattended-Upgrade::Automatic-Reboot-WithUsers "false";
Unattended-Upgrade::Automatic-Reboot-Time "02:00";

// Notification settings
Unattended-Upgrade::Mail "admin@company.com";
Unattended-Upgrade::MailOnlyOnError "true";
Unattended-Upgrade::Sender "security-updates@company.com";

// Logging
Unattended-Upgrade::Debug "false";
Unattended-Upgrade::SyslogEnable "true";
Unattended-Upgrade::SyslogFacility "daemon";
EOF

# Enable automatic updates
cat << 'EOF' > /etc/apt/apt.conf.d/20auto-upgrades
APT::Periodic::Update-Package-Lists "1";
APT::Periodic::Download-Upgradeable-Packages "1";
APT::Periodic::AutocleanInterval "7";
APT::Periodic::Unattended-Upgrade "1";
APT::Periodic::Verbose "2";
EOF
```

#### Testing and Validation
```bash
# Test unattended-upgrades configuration
unattended-upgrades --dry-run --debug
unattended-upgrades --dry-run

# Check what would be upgraded
apt list --upgradable | grep -i security

# View logs
tail -f /var/log/unattended-upgrades/unattended-upgrades.log
journalctl -u unattended-upgrades

# Manual run
unattended-upgrades --debug
```

### RHEL/CentOS DNF Automatic

#### Installation and Setup
```bash
# Install dnf-automatic
dnf install dnf-automatic

# Check available timers
systemctl list-timers | grep dnf
```

#### Configuration
```bash
# Main configuration: /etc/dnf/automatic.conf
cat << 'EOF' > /etc/dnf/automatic.conf
[commands]
# What kind of upgrade to perform:
# default = all available upgrades
# security = only the security upgrades
upgrade_type = security
random_sleep = 3600

# Whether to download updates
download_updates = yes

# Whether to apply updates
apply_updates = no

[emitters]
emit_via = stdio,email

[email]
email_from = security@company.com
email_to = admin@company.com
email_host = localhost

[base]
# Override dnf.conf settings
debuglevel = 1
EOF

# Alternative configurations for different scenarios
# Security-only auto-install
cat << 'EOF' > /etc/dnf/automatic-security.conf
[commands]
upgrade_type = security
apply_updates = yes
EOF

# Download-only configuration
cat << 'EOF' > /etc/dnf/automatic-download.conf
[commands]
upgrade_type = default
download_updates = yes
apply_updates = no
EOF
```

#### Service Management
```bash
# Enable automatic security updates
systemctl enable --now dnf-automatic.timer

# Enable different automatic modes
systemctl enable --now dnf-automatic-download.timer
systemctl enable --now dnf-automatic-install.timer

# Check status
systemctl status dnf-automatic.timer
systemctl list-timers | grep dnf

# View logs
journalctl -u dnf-automatic
tail -f /var/log/dnf.log
```

## Manual Security Updates

### Debian/Ubuntu Security Updates
```bash
# List security updates only
apt list --upgradable | grep -i security
grep security /var/log/apt/history.log

# Install security updates only
apt upgrade -s | grep -i security  # Simulate
unattended-upgrades --dry-run      # Test automatic security updates

# Manual security-only upgrade (requires careful filtering)
apt-get upgrade $(apt list --upgradable 2>/dev/null | grep -i security | cut -d/ -f1)
```

### RHEL/CentOS Security Updates
```bash
# List security advisories
dnf updateinfo list security
dnf updateinfo info security
dnf updateinfo summary

# Install security updates only
dnf update --security
dnf upgrade --security

# Specific advisory
dnf updateinfo info RHSA-2021:1234
dnf update --advisory RHSA-2021:1234

# Check specific packages for security updates
dnf updateinfo list security kernel
```

## Security Scanning and Compliance

### OpenSCAP Security Scanning
```bash
# Install OpenSCAP (Ubuntu)
apt install libopenscap8 ssg-debderived

# Install OpenSCAP (RHEL/CentOS)
dnf install openscap-scanner scap-security-guide

# List available profiles
oscap info /usr/share/xml/scap/ssg/content/ssg-ubuntu2004-ds.xml
oscap info /usr/share/xml/scap/ssg/content/ssg-rhel8-ds.xml

# Run security scan
oscap xccdf eval \
  --profile xccdf_org.ssgproject.content_profile_standard \
  --results scan-results.xml \
  --report scan-report.html \
  /usr/share/xml/scap/ssg/content/ssg-ubuntu2004-ds.xml

# Generate remediation script
oscap xccdf generate fix \
  --profile xccdf_org.ssgproject.content_profile_standard \
  --output remediation.sh \
  /usr/share/xml/scap/ssg/content/ssg-ubuntu2004-ds.xml
```

### Vulnerability Scanning Tools
```bash
# Install and use Lynis
apt install lynis  # Ubuntu
dnf install lynis  # RHEL/CentOS

# Run Lynis security audit
lynis audit system
lynis show report
lynis show details TEST-ID

# Vulnerability scanning with Nessus (commercial)
# Download from tenable.com
dpkg -i Nessus-*-ubuntu1404_amd64.deb
systemctl start nessusd

# OVAL vulnerability scanning
apt install oval-tools
oval-eval --definition security.oval.xml --result scan-results.xml
```

## Package Security Verification

### GPG Signature Verification
```bash
# Debian/Ubuntu package verification
apt-key list
debsums -c  # Verify installed packages
debsums -l  # List packages with missing checksums

# Manual package verification
dpkg --verify package_name
apt-cache policy package_name

# RPM package verification
rpm --checksig package.rpm
rpm -V package_name
rpm -Va  # Verify all packages

# Check package signatures before installation
rpm --import https://example.com/RPM-GPG-KEY
rpm --checksig package.rpm
```

### Package Integrity Monitoring
```bash
# Create baseline of installed packages
dpkg --get-selections > installed-packages-baseline.txt
rpm -qa --queryformat '%{NAME}-%{VERSION}-%{RELEASE}\n' > installed-packages-baseline.txt

# Compare current state
dpkg --get-selections > installed-packages-current.txt
diff installed-packages-baseline.txt installed-packages-current.txt

# Monitor file integrity
apt install aide  # Ubuntu
dnf install aide  # RHEL/CentOS

# Initialize AIDE database
aide --init
mv /var/lib/aide/aide.db.new.gz /var/lib/aide/aide.db.gz

# Run integrity check
aide --check
```

## Security Update Automation Scripts

### Comprehensive Security Update Script
```bash
#!/bin/bash
# security-update-manager.sh

LOG_FILE="/var/log/security-updates.log"
EMAIL="admin@company.com"

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# Detect package manager
if command -v apt &> /dev/null; then
    PKG_MGR="apt"
elif command -v dnf &> /dev/null; then
    PKG_MGR="dnf"
else
    log "ERROR: No supported package manager found"
    exit 1
fi

case "$PKG_MGR" in
    apt)
        log "Starting APT security update process"

        # Update package lists
        apt update

        # Check for security updates
        SECURITY_UPDATES=$(apt list --upgradable 2>/dev/null | grep -c security)
        log "Found $SECURITY_UPDATES security updates"

        if [ "$SECURITY_UPDATES" -gt 0 ]; then
            # Apply security updates
            unattended-upgrades --dry-run | tee -a "$LOG_FILE"

            if [ "$1" = "--apply" ]; then
                unattended-upgrades | tee -a "$LOG_FILE"
                log "Security updates applied"
            else
                log "Dry run completed. Use --apply to install updates"
            fi
        fi
        ;;

    dnf)
        log "Starting DNF security update process"

        # Check for security updates
        SECURITY_UPDATES=$(dnf updateinfo list security | wc -l)
        log "Found $SECURITY_UPDATES security updates"

        if [ "$SECURITY_UPDATES" -gt 0 ]; then
            # List security updates
            dnf updateinfo list security | tee -a "$LOG_FILE"

            if [ "$1" = "--apply" ]; then
                dnf update --security -y | tee -a "$LOG_FILE"
                log "Security updates applied"
            else
                log "Dry run completed. Use --apply to install updates"
            fi
        fi
        ;;
esac

# Check if reboot required
if [ -f /var/run/reboot-required ]; then
    log "REBOOT REQUIRED after security updates"
    echo "Security updates installed. Reboot required." | mail -s "Reboot Required: $(hostname)" "$EMAIL"
fi

log "Security update process completed"
```

### Security Compliance Report
```bash
#!/bin/bash
# security-compliance-report.sh

REPORT_FILE="/tmp/security-compliance-$(date +%Y%m%d).html"

cat << 'EOF' > "$REPORT_FILE"
<!DOCTYPE html>
<html>
<head>
    <title>Security Compliance Report</title>
    <style>
        body { font-family: Arial, sans-serif; }
        .header { background: #f0f0f0; padding: 10px; }
        .section { margin: 20px 0; }
        .critical { color: red; }
        .warning { color: orange; }
        .ok { color: green; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Security Compliance Report</h1>
        <p>Generated: $(date)</p>
        <p>Hostname: $(hostname)</p>
    </div>
EOF

# Package update status
echo '<div class="section">' >> "$REPORT_FILE"
echo '<h2>Package Update Status</h2>' >> "$REPORT_FILE"

if command -v apt &> /dev/null; then
    UPDATES=$(apt list --upgradable 2>/dev/null | wc -l)
    SECURITY=$(apt list --upgradable 2>/dev/null | grep -c security)
elif command -v dnf &> /dev/null; then
    UPDATES=$(dnf check-update -q | wc -l)
    SECURITY=$(dnf updateinfo list security | wc -l)
fi

echo "<p>Total updates available: $UPDATES</p>" >> "$REPORT_FILE"
echo "<p class=\"critical\">Security updates: $SECURITY</p>" >> "$REPORT_FILE"
echo '</div>' >> "$REPORT_FILE"

# System information
echo '<div class="section">' >> "$REPORT_FILE"
echo '<h2>System Information</h2>' >> "$REPORT_FILE"
echo "<p>Kernel: $(uname -r)</p>" >> "$REPORT_FILE"
echo "<p>Uptime: $(uptime)</p>" >> "$REPORT_FILE"
echo '</div>' >> "$REPORT_FILE"

echo '</body></html>' >> "$REPORT_FILE"

echo "Security compliance report generated: $REPORT_FILE"
```

### Automated Vulnerability Assessment
```bash
#!/bin/bash
# vulnerability-assessment.sh

SCAN_DIR="/var/log/security-scans"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p "$SCAN_DIR"

# OpenSCAP scan
if command -v oscap &> /dev/null; then
    echo "Running OpenSCAP security scan..."

    if [ -f /usr/share/xml/scap/ssg/content/ssg-ubuntu2004-ds.xml ]; then
        CONTENT_FILE="/usr/share/xml/scap/ssg/content/ssg-ubuntu2004-ds.xml"
    elif [ -f /usr/share/xml/scap/ssg/content/ssg-rhel8-ds.xml ]; then
        CONTENT_FILE="/usr/share/xml/scap/ssg/content/ssg-rhel8-ds.xml"
    fi

    if [ -n "$CONTENT_FILE" ]; then
        oscap xccdf eval \
            --profile xccdf_org.ssgproject.content_profile_standard \
            --results "$SCAN_DIR/openscap_results_$DATE.xml" \
            --report "$SCAN_DIR/openscap_report_$DATE.html" \
            "$CONTENT_FILE"
    fi
fi

# Lynis scan
if command -v lynis &> /dev/null; then
    echo "Running Lynis security audit..."
    lynis audit system --log-file "$SCAN_DIR/lynis_$DATE.log"
fi

# Package vulnerability check
if command -v apt &> /dev/null; then
    apt list --upgradable 2>/dev/null | grep -i security > "$SCAN_DIR/security_updates_$DATE.txt"
elif command -v dnf &> /dev/null; then
    dnf updateinfo list security > "$SCAN_DIR/security_updates_$DATE.txt"
fi

echo "Vulnerability assessment completed. Results in: $SCAN_DIR"
```