# Linux Security Auditing Monitoring

**Security auditing and monitoring** provides comprehensive system activity tracking, file integrity monitoring, and real-time security event detection using auditd, AIDE, and custom monitoring solutions.

## Linux Audit Framework (auditd)

### Audit System Configuration

#### Installation and Setup
```bash
# Install and enable auditd
systemctl enable auditd
systemctl start auditd
systemctl status auditd

# Check audit system status
auditctl -s
auditctl -l
```

#### Main Configuration
```bash
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

### Audit Rules Configuration

#### Comprehensive Audit Rules
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

#### Targeted Audit Rules
```bash
# Monitor specific user activities
-a always,exit -F uid=1000 -S execve -k user_commands

# Monitor root access
-a always,exit -F uid=0 -S execve -k root_commands

# Monitor failed access attempts
-a always,exit -F arch=b64 -S open -F exit=-EACCES -k access_denied
-a always,exit -F arch=b64 -S open -F exit=-EPERM -k access_denied

# Monitor logins
-w /var/log/lastlog -p wa -k logins
-w /var/run/faillock/ -p wa -k logins

# Monitor kernel module loading
-w /sbin/insmod -p x -k modules
-w /sbin/rmmod -p x -k modules
-w /sbin/modprobe -p x -k modules
-a always,exit -F arch=b64 -S init_module -k modules
-a always,exit -F arch=b64 -S delete_module -k modules
```

### Audit Log Analysis

#### Basic Log Searches
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

# Advanced searches
ausearch -x /bin/bash                   # Search by executable
ausearch -a 12345                       # Search by audit event ID
ausearch --gid 0                        # Search by group ID
ausearch --pid 1234                     # Search by process ID
```

#### Audit Report Generation
```bash
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

# Custom reports
aureport -u --summary                  # User activity summary
aureport -f --summary                  # File access summary
aureport -x --summary                  # Executable summary
aureport --login --summary             # Login summary
```

#### Real-time Monitoring
```bash
# Real-time monitoring
ausearch -ts recent | tail -f          # Monitor recent events
tail -f /var/log/audit/audit.log | ausearch --input-logs

# Custom monitoring script
#!/bin/bash
while true; do
    ausearch -ts recent -k failed_login 2>/dev/null | tail -n 5
    sleep 10
done
```

#### Advanced Analysis Examples
```bash
# Extract command executions
ausearch -k command_exec -i | grep -E "exe=|proctitle="

# Monitor failed login attempts
ausearch -k failed_login -ts today -i

# Check for privilege escalation attempts
ausearch -k privilege_escalation -i

# Monitor file deletions
ausearch -k file_deletion -ts today | grep -E "unlink|unlinkat"

# Find suspicious network connections
ausearch -k network_connect -ts today | grep -v "comm=\"systemd\""
```

## File Integrity Monitoring

### AIDE (Advanced Intrusion Detection Environment)

#### Installation and Configuration
```bash
# Install AIDE
apt install aide aide-common          # Debian/Ubuntu
dnf install aide                      # RHEL/CentOS/Fedora

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
!/var/lib/aide
!/var/log/audit/audit.log
EOF
```

#### AIDE Operations
```bash
# Initialize AIDE database
aide --init
cp /var/lib/aide/aide.db.new /var/lib/aide/aide.db

# Run integrity check
aide --check
aide --check --verbose

# Update database after legitimate changes
aide --update
cp /var/lib/aide/aide.db.new /var/lib/aide/aide.db

# Compare specific database
aide --check --compare
```

#### Automated AIDE Monitoring
```bash
# Automated daily checks
cat << 'EOF' > /etc/cron.daily/aide-check
#!/bin/bash
AIDE_LOG="/var/log/aide/aide-$(date +%Y%m%d).log"
mkdir -p /var/log/aide

aide --check > "$AIDE_LOG" 2>&1

if [ $? -ne 0 ]; then
    echo "AIDE detected changes on $(hostname)" | \
    mail -s "AIDE Alert: File System Changes Detected" -a "$AIDE_LOG" root
fi
EOF

chmod +x /etc/cron.daily/aide-check

# Weekly database update
cat << 'EOF' > /etc/cron.weekly/aide-update
#!/bin/bash
aide --update
cp /var/lib/aide/aide.db.new /var/lib/aide/aide.db
echo "AIDE database updated on $(hostname)" | mail -s "AIDE Database Updated" root
EOF

chmod +x /etc/cron.weekly/aide-update
```

### Custom File Integrity Monitoring

#### Simple Checksum-based Monitoring
```bash
# Simple checksum-based monitoring script
create_integrity_baseline() {
    local watch_dirs=("/etc" "/usr/bin" "/usr/sbin" "/boot")
    local baseline_file="/var/lib/integrity/baseline.md5"

    mkdir -p /var/lib/integrity

    echo "Creating integrity baseline..."
    > "$baseline_file"

    for dir in "${watch_dirs[@]}"; do
        if [[ -d "$dir" ]]; then
            echo "Processing $dir..."
            find "$dir" -type f -exec md5sum {} \; >> "$baseline_file"
        fi
    done

    echo "Baseline created: $baseline_file"
    echo "Files monitored: $(wc -l < "$baseline_file")"
}

check_integrity() {
    local baseline_file="/var/lib/integrity/baseline.md5"
    local current_file="/tmp/current.md5"
    local changes_file="/tmp/integrity_changes.txt"
    local watch_dirs=("/etc" "/usr/bin" "/usr/sbin" "/boot")

    if [[ ! -f "$baseline_file" ]]; then
        echo "ERROR: Baseline file not found. Run create_integrity_baseline first."
        return 1
    fi

    echo "Checking file integrity..."

    # Generate current checksums
    > "$current_file"
    for dir in "${watch_dirs[@]}"; do
        if [[ -d "$dir" ]]; then
            find "$dir" -type f -exec md5sum {} \; >> "$current_file"
        fi
    done

    # Compare with baseline
    if diff "$baseline_file" "$current_file" > "$changes_file"; then
        echo "✓ Integrity check passed"
        return 0
    else
        echo "⚠ Integrity check failed. Changes detected:"
        cat "$changes_file"

        # Email alert
        mail -s "File Integrity Alert on $(hostname)" root < "$changes_file"
        return 1
    fi
}

# Usage examples
create_integrity_baseline
check_integrity
```

#### Advanced File Monitoring Script
```bash
#!/bin/bash
# advanced-file-monitor.sh

MONITOR_CONFIG="/etc/file-monitor.conf"
LOG_FILE="/var/log/file-monitor.log"
ALERT_EMAIL="admin@company.com"

# Configuration file format: path:checksum_type:alert_level
cat << 'EOF' > "$MONITOR_CONFIG"
/etc/passwd:sha256:critical
/etc/shadow:sha256:critical
/etc/sudoers:sha256:high
/boot/grub/grub.cfg:md5:medium
/etc/ssh/sshd_config:sha256:high
/etc/hosts:md5:low
EOF

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

monitor_files() {
    local baseline_dir="/var/lib/file-monitor"
    mkdir -p "$baseline_dir"

    while IFS=: read -r file_path checksum_type alert_level; do
        [[ -z "$file_path" || "$file_path" =~ ^# ]] && continue

        if [[ ! -f "$file_path" ]]; then
            log "WARNING: Monitored file not found: $file_path"
            continue
        fi

        local baseline_file="$baseline_dir/$(echo "$file_path" | tr '/' '_').baseline"
        local current_checksum

        case "$checksum_type" in
            md5)    current_checksum=$(md5sum "$file_path" | cut -d' ' -f1) ;;
            sha256) current_checksum=$(sha256sum "$file_path" | cut -d' ' -f1) ;;
            sha1)   current_checksum=$(sha1sum "$file_path" | cut -d' ' -f1) ;;
            *)      log "ERROR: Unknown checksum type: $checksum_type"; continue ;;
        esac

        if [[ -f "$baseline_file" ]]; then
            local baseline_checksum=$(cat "$baseline_file")

            if [[ "$current_checksum" != "$baseline_checksum" ]]; then
                log "ALERT ($alert_level): File changed: $file_path"

                # Send alert based on level
                case "$alert_level" in
                    critical|high)
                        echo "CRITICAL: File $file_path has been modified on $(hostname)" | \
                        mail -s "Critical File Change Alert" "$ALERT_EMAIL"
                        ;;
                esac

                # Update baseline
                echo "$current_checksum" > "$baseline_file"
            fi
        else
            # Create initial baseline
            echo "$current_checksum" > "$baseline_file"
            log "INFO: Created baseline for $file_path"
        fi

    done < "$MONITOR_CONFIG"
}

# Run monitoring
monitor_files
```

## Security Event Monitoring

### Real-time Security Monitoring
```bash
#!/bin/bash
# security-monitor.sh

ALERT_EMAIL="security@company.com"
LOG_FILE="/var/log/security-monitor.log"

log_alert() {
    local alert_type="$1"
    local message="$2"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')

    echo "$timestamp - ALERT [$alert_type]: $message" | tee -a "$LOG_FILE"
    echo "$message" | mail -s "Security Alert: $alert_type" "$ALERT_EMAIL"
}

monitor_failed_logins() {
    local failed_count=$(ausearch -m USER_LOGIN -ts today -sv no 2>/dev/null | grep -c "res=failed" || echo "0")

    if [[ $failed_count -gt 10 ]]; then
        log_alert "FAILED_LOGINS" "High number of failed login attempts: $failed_count"
    fi
}

monitor_privilege_escalation() {
    local priv_events=$(ausearch -k privilege_escalation -ts recent 2>/dev/null | wc -l)

    if [[ $priv_events -gt 0 ]]; then
        log_alert "PRIVILEGE_ESCALATION" "Privilege escalation events detected: $priv_events"
    fi
}

monitor_file_changes() {
    local critical_changes=$(ausearch -k passwd_changes -k shadow_changes -ts recent 2>/dev/null | wc -l)

    if [[ $critical_changes -gt 0 ]]; then
        log_alert "CRITICAL_FILE_CHANGE" "Critical system files modified"
    fi
}

# Run all monitoring functions
monitor_failed_logins
monitor_privilege_escalation
monitor_file_changes
```

### Automated Security Reports
```bash
#!/bin/bash
# security-report.sh

REPORT_FILE="/tmp/security-report-$(date +%Y%m%d).html"
EMAIL_RECIPIENT="security-team@company.com"

generate_security_report() {
    cat << 'EOF' > "$REPORT_FILE"
<!DOCTYPE html>
<html>
<head>
    <title>Daily Security Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { background: #f0f0f0; padding: 10px; margin-bottom: 20px; }
        .section { margin: 20px 0; }
        .alert { color: red; font-weight: bold; }
        .warning { color: orange; }
        .info { color: blue; }
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Daily Security Report</h1>
        <p>Generated: $(date)</p>
        <p>Hostname: $(hostname)</p>
    </div>
EOF

    # Login Activity
    echo '<div class="section">' >> "$REPORT_FILE"
    echo '<h2>Login Activity</h2>' >> "$REPORT_FILE"
    echo '<table>' >> "$REPORT_FILE"
    echo '<tr><th>Time</th><th>User</th><th>Source</th><th>Status</th></tr>' >> "$REPORT_FILE"

    ausearch -m USER_LOGIN -ts today 2>/dev/null | grep -E "USER_LOGIN" | head -10 | \
    while read line; do
        echo "<tr><td>$(echo "$line" | grep -o 'msg=audit([^:]*' | cut -d'(' -f2)</td>" >> "$REPORT_FILE"
        echo "<td>$(echo "$line" | grep -o 'acct="[^"]*"' | cut -d'"' -f2)</td>" >> "$REPORT_FILE"
        echo "<td>$(echo "$line" | grep -o 'addr=[^ ]*' | cut -d'=' -f2)</td>" >> "$REPORT_FILE"
        echo "<td>$(echo "$line" | grep -o 'res=[^ ]*' | cut -d'=' -f2)</td></tr>" >> "$REPORT_FILE"
    done 2>/dev/null || echo "<tr><td colspan='4'>No login data available</td></tr>" >> "$REPORT_FILE"

    echo '</table>' >> "$REPORT_FILE"
    echo '</div>' >> "$REPORT_FILE"

    # File Changes
    echo '<div class="section">' >> "$REPORT_FILE"
    echo '<h2>Critical File Changes</h2>' >> "$REPORT_FILE"

    local changes=$(ausearch -k passwd_changes -k shadow_changes -k sudoers_changes -ts today 2>/dev/null | wc -l)
    if [[ $changes -gt 0 ]]; then
        echo "<p class='alert'>$changes critical file changes detected!</p>" >> "$REPORT_FILE"
    else
        echo "<p class='info'>No critical file changes detected.</p>" >> "$REPORT_FILE"
    fi
    echo '</div>' >> "$REPORT_FILE"

    # System Summary
    echo '<div class="section">' >> "$REPORT_FILE"
    echo '<h2>System Summary</h2>' >> "$REPORT_FILE"
    echo "<p>Uptime: $(uptime)</p>" >> "$REPORT_FILE"
    echo "<p>Load Average: $(cat /proc/loadavg)</p>" >> "$REPORT_FILE"
    echo "<p>Failed Login Attempts: $(ausearch -m USER_LOGIN -ts today -sv no 2>/dev/null | wc -l)</p>" >> "$REPORT_FILE"
    echo '</div>' >> "$REPORT_FILE"

    echo '</body></html>' >> "$REPORT_FILE"
}

# Generate and send report
generate_security_report
mail -s "Daily Security Report - $(hostname)" -a "Content-Type: text/html" "$EMAIL_RECIPIENT" < "$REPORT_FILE"

echo "Security report generated: $REPORT_FILE"
```