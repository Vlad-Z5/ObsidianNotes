# Linux Process Management Scheduling Automation

**Scheduling and Automation** covers traditional cron management and modern systemd timers for automated task execution and system maintenance.

## Traditional Cron Management

### System-wide Cron Configuration
```bash
# System-wide crontab (/etc/crontab)
# Format: minute hour day month dow user command
0  2  *   *   *  root   /usr/local/bin/backup.sh
30 1  *   *   0  root   /usr/sbin/logrotate /etc/logrotate.conf
*/5 * *   *   *  root   /usr/local/bin/monitor.sh
15 3  1   *   *  root   /usr/local/bin/monthly_cleanup.sh

# View system crontab
cat /etc/crontab

# Environment variables in crontab
PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin
SHELL=/bin/bash
MAILTO=admin@example.com
HOME=/root
```

### User Crontab Management
```bash
# User crontab operations
crontab -e                             # Edit user crontab
crontab -l                             # List user crontab entries
crontab -r                             # Remove user crontab
crontab -u username -l                 # List another user's crontab (root only)
crontab -u username -e                 # Edit another user's crontab (root only)

# Backup and restore user crontabs
crontab -l > ~/crontab_backup.txt      # Backup current crontab
crontab ~/crontab_backup.txt           # Restore from backup

# List all user crontabs (root only)
for user in $(cut -f1 -d: /etc/passwd); do
    echo "=== Crontab for user: $user ==="
    crontab -u $user -l 2>/dev/null || echo "No crontab"
    echo
done
```

### Cron Directories and System Jobs
```bash
# System cron directories
ls -la /etc/cron.d/                    # Additional system cron jobs
ls -la /etc/cron.hourly/               # Scripts run hourly
ls -la /etc/cron.daily/                # Scripts run daily
ls -la /etc/cron.weekly/               # Scripts run weekly
ls -la /etc/cron.monthly/              # Scripts run monthly

# Check cron execution times
cat /etc/crontab | grep -E "cron.hourly|cron.daily"
cat /etc/anacrontab                    # Anacron configuration (if available)

# Add script to system directories
cat << 'EOF' > /etc/cron.daily/system-health-check
#!/bin/bash
# Daily system health check

# Check disk space
df -h | awk '$5 > 80 {print "High disk usage: " $0}' | mail -s "Disk Alert" admin@example.com

# Check memory usage
free | awk 'NR==2 {if ($3/$2 > 0.9) print "High memory usage: " $3/$2*100 "%"}' | \
    mail -s "Memory Alert" admin@example.com

# Check load average
uptime | awk '{if ($10 > 2.0) print "High load average: " $10}' | \
    mail -s "Load Alert" admin@example.com
EOF

chmod +x /etc/cron.daily/system-health-check
```

### Cron Job Examples and Patterns
```bash
# Time format: minute hour day month dow command
# * means "any value"
# */N means "every N units"
# N-M means "range from N to M"
# N,M means "values N and M"

# Common patterns
*/5 * * * * /usr/local/bin/check_service.sh         # Every 5 minutes
0 * * * * /usr/local/bin/hourly_task.sh             # Every hour
0 2 * * * /usr/local/bin/daily_backup.sh            # Daily at 2 AM
0 2 * * 0 /usr/local/bin/weekly_backup.sh           # Weekly on Sunday at 2 AM
0 2 1 * * /usr/local/bin/monthly_report.sh          # Monthly on 1st at 2 AM

# Business hours patterns
0 9 * * 1-5 /usr/local/bin/start_backup.sh          # Weekdays at 9 AM
0 8-18/2 * * 1-5 /usr/local/bin/business_check.sh   # Every 2 hours, business hours
30 12 * * 1-5 /usr/local/bin/lunch_report.sh        # Weekdays at 12:30 PM

# Complex scheduling
0 2 1,15 * * /usr/local/bin/bi_monthly.sh           # 1st and 15th at 2 AM
0 6 * * 1 /usr/local/bin/monday_start.sh            # Every Monday at 6 AM
15,45 * * * * /usr/local/bin/quarter_hour.sh        # Every 15 and 45 minutes

# Seasonal/yearly tasks
0 3 1 1 * /usr/local/bin/new_year_task.sh           # New Year's Day at 3 AM
0 0 25 12 * /usr/local/bin/christmas_task.sh        # Christmas at midnight
```

### Cron Logging and Debugging
```bash
# View cron logs
grep CRON /var/log/syslog              # Ubuntu/Debian
grep CRON /var/log/cron                # RHEL/CentOS
journalctl _COMM=cron                  # Systemd-based systems
journalctl -u cron                     # Alternative systemd method

# Enable detailed cron logging (edit /etc/rsyslog.conf)
# Uncomment: cron.*    /var/log/cron.log

# Debug cron issues
tail -f /var/log/cron                  # Watch cron activity in real-time
grep "$(whoami)" /var/log/cron         # Filter by current user

# Test cron job execution
# Create test job that runs every minute
echo "* * * * * echo 'Cron test at $(date)' >> /tmp/cron_test.log" | crontab -
# Wait and check
tail /tmp/cron_test.log
# Remove test job
crontab -r

# Common cron issues and solutions
cat << 'EOF' > /usr/local/bin/cron-debug
#!/bin/bash
# Cron debugging helper

echo "=== Cron Environment Debug ==="
echo "Date: $(date)"
echo "User: $(whoami)"
echo "PATH: $PATH"
echo "SHELL: $SHELL"
echo "HOME: $HOME"
echo "PWD: $(pwd)"
echo

# Test command availability
which python3 || echo "python3 not found in PATH"
which /usr/bin/python3 && echo "python3 found at /usr/bin/python3"

# Environment comparison
echo "=== Environment Variables ==="
env | sort
EOF

chmod +x /usr/local/bin/cron-debug
```

## Systemd Timers (Modern Scheduling)

### Creating Timer Units
```bash
# Create backup timer unit
cat << 'EOF' > /etc/systemd/system/backup.timer
[Unit]
Description=Daily Backup Timer
Requires=backup.service

[Timer]
OnCalendar=*-*-* 02:00:00             # Daily at 2 AM
Persistent=true                        # Run missed timers on boot
RandomizedDelaySec=300                # Add up to 5 minutes random delay
AccuracySec=1m                        # 1-minute accuracy

[Install]
WantedBy=timers.target
EOF

# Create corresponding service unit
cat << 'EOF' > /etc/systemd/system/backup.service
[Unit]
Description=Daily Backup Service
After=network.target

[Service]
Type=oneshot
User=backup
Group=backup
ExecStart=/usr/local/bin/backup.sh
StandardOutput=journal
StandardError=journal
TimeoutStartSec=3600                  # 1-hour timeout
EnvironmentFile=-/etc/default/backup  # Optional environment file

[Install]
WantedBy=multi-user.target
EOF

# Create environment file for the service
cat << 'EOF' > /etc/default/backup
BACKUP_DIR=/backup
RETENTION_DAYS=30
LOG_LEVEL=INFO
EOF
```

### Timer Management Commands
```bash
# Timer lifecycle management
systemctl daemon-reload                # Reload systemd configuration
systemctl enable backup.timer          # Enable timer to start on boot
systemctl start backup.timer           # Start timer immediately
systemctl stop backup.timer            # Stop timer
systemctl restart backup.timer         # Restart timer
systemctl disable backup.timer         # Disable timer from starting on boot

# Timer status and monitoring
systemctl status backup.timer          # Check timer status
systemctl list-timers                  # List all active timers
systemctl list-timers --all            # List all timers (active and inactive)
systemctl list-timers backup.timer     # Show specific timer

# View timer details
systemctl show backup.timer            # Show all timer properties
systemctl cat backup.timer             # Show timer unit file
```

### Timer Calendar Expressions
```bash
# Basic calendar expressions
OnCalendar=hourly                      # Every hour (same as *-*-* *:00:00)
OnCalendar=daily                       # Every day at midnight
OnCalendar=weekly                      # Every week on Monday at midnight
OnCalendar=monthly                     # Every month on the 1st at midnight
OnCalendar=yearly                      # Every year on January 1st at midnight

# Specific time patterns
OnCalendar=*-*-* 06:30:00             # Daily at 6:30 AM
OnCalendar=*-*-* 14:00,18:00          # Daily at 2 PM and 6 PM
OnCalendar=Mon,Tue *-*-* 09:00:00     # Monday and Tuesday at 9 AM
OnCalendar=Mon..Fri *-*-* 17:00:00    # Weekdays at 5 PM

# Advanced patterns
OnCalendar=*-*-01 03:00:00            # First day of every month at 3 AM
OnCalendar=*-01,07-01 00:00:00        # January 1st and July 1st
OnCalendar=Sat *-*-* 20:00:00         # Every Saturday at 8 PM
OnCalendar=*-*-* 08:00:00/2           # Every 2 hours starting at 8 AM

# Test calendar expressions
systemd-analyze calendar "Mon,Tue *-*-* 09:00:00"
systemd-analyze calendar "daily"
systemd-analyze calendar "*-*-* 08:00:00/2"
```

### Advanced Timer Configuration
```bash
# High-frequency monitoring timer
cat << 'EOF' > /etc/systemd/system/monitor.timer
[Unit]
Description=System Monitor Timer

[Timer]
OnBootSec=1min                        # Start 1 minute after boot
OnUnitActiveSec=30sec                 # Run every 30 seconds after last activation
AccuracySec=5sec                      # 5-second accuracy

[Install]
WantedBy=timers.target
EOF

cat << 'EOF' > /etc/systemd/system/monitor.service
[Unit]
Description=System Monitor Service

[Service]
Type=oneshot
ExecStart=/usr/local/bin/quick_monitor.sh
TimeoutStartSec=10
EOF

# Complex backup timer with dependencies
cat << 'EOF' > /etc/systemd/system/full-backup.timer
[Unit]
Description=Weekly Full Backup
Requires=full-backup.service

[Timer]
OnCalendar=Sun *-*-* 01:00:00         # Every Sunday at 1 AM
Persistent=true
RandomizedDelaySec=1800               # Random delay up to 30 minutes
WakeSystem=true                       # Wake system from sleep if needed

[Install]
WantedBy=timers.target
EOF

cat << 'EOF' > /etc/systemd/system/full-backup.service
[Unit]
Description=Full System Backup
After=network.target
Wants=incremental-backup.service      # Prefer incremental backup first
Conflicts=incremental-backup.service  # But don't run simultaneously

[Service]
Type=oneshot
User=backup
Group=backup
ExecStartPre=/usr/local/bin/pre_backup_check.sh
ExecStart=/usr/local/bin/full_backup.sh
ExecStartPost=/usr/local/bin/post_backup_cleanup.sh
TimeoutStartSec=7200                  # 2-hour timeout
Restart=on-failure
RestartSec=300

# Resource limits
MemoryLimit=2G
CPUQuota=50%
IOWeight=100

# Security
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ReadWritePaths=/backup
EOF
```

### Timer Logging and Monitoring
```bash
# View timer and service logs
journalctl -u backup.timer             # Timer logs
journalctl -u backup.service           # Service logs
journalctl -f -u backup.timer          # Follow timer logs in real-time
journalctl -u backup.* --since "1 week ago"  # All backup-related logs

# Monitor timer execution
systemctl list-timers --no-pager       # List without pager
watch 'systemctl list-timers'          # Real-time timer monitoring

# Timer performance analysis
cat << 'EOF' > /usr/local/bin/timer-analysis
#!/bin/bash
# Analyze systemd timer performance

echo "=== Systemd Timer Analysis ==="
echo "Date: $(date)"
echo

echo "Active Timers:"
systemctl list-timers --no-pager | head -20
echo

echo "Failed Timer Services:"
systemctl list-units --state=failed --type=service | grep -E "\\.timer|\\.service"
echo

echo "Recent Timer Activations:"
journalctl --since "24 hours ago" | grep "Started\|Finished" | grep -E "backup|monitor|cleanup" | tail -10
echo

echo "Timer Resource Usage:"
systemctl status *.timer --no-pager | grep -A 3 "Active\|Memory\|Tasks"
EOF

chmod +x /usr/local/bin/timer-analysis

# Create comprehensive timer status script
cat << 'EOF' > /usr/local/bin/timer-status
#!/bin/bash
# Comprehensive timer status checker

echo "=== Timer Status Report ==="
echo "Generated: $(date)"
echo

# List all timers with next execution
echo "Timer Schedule:"
echo "==============="
systemctl list-timers --all --no-pager

echo
echo "Timer Service Status:"
echo "===================="
for timer in $(systemctl list-unit-files --type=timer --no-pager | awk 'NR>1 {print $1}' | grep -v "^$"); do
    service=${timer%.timer}.service
    echo "Timer: $timer"
    echo "  Status: $(systemctl is-active $timer)"
    echo "  Enabled: $(systemctl is-enabled $timer)"
    echo "  Service: $service ($(systemctl is-active $service))"
    echo "  Last trigger: $(systemctl show $timer -p LastTriggerUSec --value)"
    echo
done

echo "Recent Timer Activity:"
echo "====================="
journalctl --since "24 hours ago" -u "*.timer" --no-pager | tail -20
EOF

chmod +x /usr/local/bin/timer-status
```