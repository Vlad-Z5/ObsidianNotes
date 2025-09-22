# Linux Systemd Timers

**Systemd timers** provide a modern replacement for cron, offering precise scheduling, better logging, service integration, and advanced timing options.

## Timer Unit Structure

```bash
# Timer file naming convention
backup.timer    # Timer unit
backup.service  # Corresponding service unit

# Timer activates service with same name
# Or specify different service with Unit= directive
```

## Basic Timer Configuration

```bash
# /etc/systemd/system/backup.timer
[Unit]
Description=Daily Backup Timer
Documentation=man:systemd.timer(5)
Requires=backup.service

[Timer]
OnCalendar=daily
Persistent=true

[Install]
WantedBy=timers.target
```

## Timer Scheduling Options

### Calendar-Based Timing
```bash
# Time formats
OnCalendar=hourly              # Every hour
OnCalendar=daily               # Every day at midnight
OnCalendar=weekly              # Every Monday at midnight
OnCalendar=monthly             # First day of month at midnight
OnCalendar=yearly              # January 1st at midnight

# Specific times
OnCalendar=*-*-* 02:00:00      # Daily at 2 AM
OnCalendar=Mon *-*-* 09:00:00  # Mondays at 9 AM
OnCalendar=*-*-01 03:00:00     # Monthly on 1st at 3 AM
OnCalendar=*-01-01 00:00:00    # Yearly on January 1st

# Multiple times
OnCalendar=*-*-* 06:00:00      # 6 AM
OnCalendar=*-*-* 18:00:00      # 6 PM

# Business hours (weekdays 9-17)
OnCalendar=Mon..Fri *-*-* 09,10,11,12,13,14,15,16,17:00:00
```

### Relative Timing
```bash
# Boot-relative timing
OnBootSec=15min                # 15 minutes after boot
OnBootSec=1h 30min             # 1.5 hours after boot

# Service-relative timing
OnUnitActiveSec=1h             # 1 hour after service activation
OnUnitInactiveSec=30min        # 30 minutes after service deactivation

# System startup timing
OnStartupSec=5min              # 5 minutes after systemd startup
```

## Timer Behavior Options

```bash
# Timer configuration options
Persistent=true                # Run if system was down during scheduled time
AccuracySec=1min              # Timer accuracy (default: 1min)
RandomizedDelaySec=300        # Random delay up to 5 minutes
RemainAfterElapse=true        # Keep timer active after elapsed
WakeSystem=false              # Don't wake system from suspend
```

## Timer Management

```bash
# Enable and start timer
systemctl enable --now backup.timer

# Timer operations
systemctl start backup.timer
systemctl stop backup.timer
systemctl restart backup.timer
systemctl reload backup.timer

# Timer status and information
systemctl status backup.timer
systemctl list-timers
systemctl list-timers --all

# Show next scheduled run
systemctl show backup.timer --property=NextElapseUSSec
```

## Real-World Timer Examples

### System Maintenance Timer
```bash
# /etc/systemd/system/maintenance.timer
[Unit]
Description=Weekly System Maintenance
Documentation=https://company.com/docs/maintenance

[Timer]
OnCalendar=Sun *-*-* 02:00:00
Persistent=true
RandomizedDelaySec=1800

[Install]
WantedBy=timers.target

# /etc/systemd/system/maintenance.service
[Unit]
Description=System Maintenance Tasks
Wants=network-online.target
After=network-online.target

[Service]
Type=oneshot
ExecStart=/usr/local/bin/system-maintenance.sh
User=root
Group=root
StandardOutput=journal
StandardError=journal
```

### Log Rotation Timer
```bash
# /etc/systemd/system/log-rotation.timer
[Unit]
Description=Hourly Log Rotation
Documentation=man:logrotate(8)

[Timer]
OnCalendar=hourly
AccuracySec=1min
Persistent=true

[Install]
WantedBy=timers.target

# /etc/systemd/system/log-rotation.service
[Unit]
Description=Rotate Log Files
Documentation=man:logrotate(8)

[Service]
Type=oneshot
ExecStart=/usr/sbin/logrotate /etc/logrotate.conf
StandardOutput=journal
StandardError=journal
```

### Backup Timer with Retries
```bash
# /etc/systemd/system/backup.timer
[Unit]
Description=Daily Database Backup
Documentation=https://company.com/docs/backup

[Timer]
OnCalendar=*-*-* 01:00:00
Persistent=true
RandomizedDelaySec=600

[Install]
WantedBy=timers.target

# /etc/systemd/system/backup.service
[Unit]
Description=Database Backup Service
Wants=network-online.target
After=network-online.target

[Service]
Type=oneshot
ExecStart=/usr/local/bin/backup-database.sh
Restart=on-failure
RestartSec=300
StartLimitBurst=3
StartLimitIntervalSec=3600
User=backup
Group=backup
StandardOutput=journal
StandardError=journal
TimeoutStartSec=3600
```

## High-Frequency Timers

### Monitoring Timer
```bash
# /etc/systemd/system/monitor.timer
[Unit]
Description=System Monitoring Every 30 Seconds
Documentation=https://company.com/docs/monitoring

[Timer]
OnUnitActiveSec=30s
AccuracySec=1s

[Install]
WantedBy=timers.target

# /etc/systemd/system/monitor.service
[Unit]
Description=System Health Check
Documentation=https://company.com/docs/monitoring

[Service]
Type=oneshot
ExecStart=/usr/local/bin/health-check.sh
StandardOutput=journal
StandardError=journal
TimeoutStartSec=25s
```

## Timer Debugging and Monitoring

```bash
# View timer status
systemctl list-timers --no-pager
systemctl status backup.timer

# Check timer logs
journalctl -u backup.timer
journalctl -u backup.timer -f

# Analyze timer schedule
systemd-analyze calendar "Mon *-*-* 09:00:00"
systemd-analyze calendar daily
systemd-analyze calendar weekly

# Manual timer trigger
systemctl start backup.service  # Trigger service manually
```

## Advanced Timer Features

### Conditional Timers
```bash
# /etc/systemd/system/conditional-backup.timer
[Unit]
Description=Conditional Backup Timer
ConditionPathExists=/etc/backup.enabled

[Timer]
OnCalendar=daily
Persistent=true

[Install]
WantedBy=timers.target
```

### Timer with Multiple Services
```bash
# /etc/systemd/system/multi-task.timer
[Unit]
Description=Multiple Task Timer

[Timer]
OnCalendar=daily
Unit=task1.service task2.service task3.service

[Install]
WantedBy=timers.target
```

## Timer Performance Optimization

```bash
# Optimize timer accuracy
AccuracySec=1s              # High precision (more CPU)
AccuracySec=5min            # Low precision (less CPU)

# Distribute timer load
RandomizedDelaySec=1800     # Spread timers over 30 minutes

# Resource-aware timing
OnUnitActiveSec=1h          # Relative to service completion
```

## Timer Migration from Cron

### Cron to Systemd Conversion
```bash
# Cron entry
# 0 2 * * * /usr/local/bin/backup.sh

# Equivalent systemd timer
[Timer]
OnCalendar=*-*-* 02:00:00
Persistent=true

# Cron entry with user
# 0 */6 * * * user /usr/local/bin/check.sh

# Equivalent systemd timer + service
[Timer]
OnCalendar=*-*-* 00,06,12,18:00:00

[Service]
User=user
ExecStart=/usr/local/bin/check.sh
```

## Timer Best Practices

### Production Timer Template
```bash
# /etc/systemd/system/production-task.timer
[Unit]
Description=Production Task Timer
Documentation=https://company.com/docs/task
PartOf=production.target

[Timer]
OnCalendar=daily
Persistent=true
RandomizedDelaySec=300
AccuracySec=1min

[Install]
WantedBy=timers.target

# /etc/systemd/system/production-task.service
[Unit]
Description=Production Task Service
Documentation=https://company.com/docs/task
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
ExecStart=/usr/local/bin/production-task.sh
Restart=on-failure
RestartSec=60
StartLimitBurst=3
StartLimitIntervalSec=300
TimeoutStartSec=600

# Security
User=task-user
Group=task-group
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
PrivateTmp=true

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=production-task
```

## Timer Monitoring Script

```bash
#!/bin/bash
# timer-monitor.sh

echo "=== Systemd Timer Status ==="
systemctl list-timers --no-pager

echo -e "\n=== Failed Timers ==="
systemctl list-timers --failed --no-pager

echo -e "\n=== Timer Logs (Last Hour) ==="
journalctl --since="1 hour ago" -u "*.timer" --no-pager

echo -e "\n=== Next Timer Executions ==="
systemctl list-timers --no-pager | awk 'NR>1 {print $1, $2, $3}'
```