# Linux Systemd Timers

**Systemd timers** are a modern alternative to cron for scheduling tasks on systemd-based Linux systems.

## Why Use Systemd Timers?

- Better logging and error handling
- Dependency management
- Resource control (CPU, memory limits)
- More flexible scheduling options
- Integration with systemd ecosystem

## Basic Timer Structure

Timers require two files:
1. **Service file** (`.service`) - defines what to run
2. **Timer file** (`.timer`) - defines when to run

## Creating a Simple Timer

### 1. Create Service File

```bash
# /etc/systemd/system/backup.service
[Unit]
Description=Daily Backup Job
Wants=network-online.target
After=network-online.target

[Service]
Type=oneshot
ExecStart=/usr/local/bin/backup.sh
User=backup
Group=backup
WorkingDirectory=/opt/backup
```

### 2. Create Timer File

```bash
# /etc/systemd/system/backup.timer
[Unit]
Description=Run backup daily at 2 AM
Requires=backup.service

[Timer]
OnCalendar=daily
Persistent=true
RandomizedDelaySec=300

[Install]
WantedBy=timers.target
```

### 3. Enable and Start

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable timer
sudo systemctl enable backup.timer

# Start timer
sudo systemctl start backup.timer

# Check status
sudo systemctl status backup.timer
```

## Timer Scheduling Options

### OnCalendar Examples

```bash
# Daily at 2 AM
OnCalendar=daily
OnCalendar=*-*-* 02:00:00

# Every 15 minutes
OnCalendar=*:0/15

# Weekdays at 9 AM
OnCalendar=Mon..Fri 09:00

# Monthly on 1st at midnight
OnCalendar=monthly
OnCalendar=*-*-01 00:00:00

# Every 6 hours
OnCalendar=0/6:00:00

# Specific times
OnCalendar=Mon,Wed,Fri 10:30
OnCalendar=2023-12-25 09:00:00
```

### Alternative Scheduling

```bash
# Relative to boot
OnBootSec=15min

# Relative to service startup
OnStartupSec=30sec

# Relative to unit activation
OnActiveSec=1h

# Relative to unit deactivation
OnUnitActiveSec=1h

# Relative to inactive state
OnUnitInactiveSec=30min
```

## Managing Timers

```bash
# List all timers
systemctl list-timers

# List only active timers
systemctl list-timers --state=active

# Check specific timer
systemctl status backup.timer

# View timer logs
journalctl -u backup.service
journalctl -u backup.timer

# Stop timer
systemctl stop backup.timer

# Disable timer
systemctl disable backup.timer
```

## Advanced Timer Features

### Timer with Resource Limits

```bash
# /etc/systemd/system/heavy-task.service
[Unit]
Description=Resource-Limited Task

[Service]
Type=oneshot
ExecStart=/usr/local/bin/heavy-script.sh
MemoryMax=1G
CPUQuota=50%
IOWeight=100
```

### Timer with Dependencies

```bash
# /etc/systemd/system/database-backup.service
[Unit]
Description=Database Backup
Wants=database.service
After=database.service

[Service]
Type=oneshot
ExecStart=/usr/local/bin/db-backup.sh
ExecStartPre=/bin/systemctl is-active database.service
```

### Timer with Retry Logic

```bash
# /etc/systemd/system/resilient-task.service
[Unit]
Description=Task with Retry Logic

[Service]
Type=oneshot
ExecStart=/usr/local/bin/task.sh
Restart=on-failure
RestartSec=30
StartLimitBurst=3
StartLimitIntervalSec=300
```

## Monitoring and Debugging

```bash
# Test timer date calculation
systemd-analyze calendar "Mon..Fri 09:00"

# Check when timer will run next
systemctl list-timers backup.timer

# Debug timer issues
systemctl cat backup.timer
systemd-analyze verify backup.timer

# View detailed logs
journalctl -u backup.timer -u backup.service --since today
```

## Converting from Cron

### Cron Job
```bash
# Crontab entry
0 2 * * * /usr/local/bin/backup.sh
```

### Equivalent Systemd Timer

```bash
# backup.service
[Unit]
Description=Backup Service

[Service]
Type=oneshot
ExecStart=/usr/local/bin/backup.sh

# backup.timer
[Unit]
Description=Daily backup at 2 AM

[Timer]
OnCalendar=*-*-* 02:00:00
Persistent=true

[Install]
WantedBy=timers.target
```

## Best Practices

```bash
# Use Persistent=true for important jobs
Persistent=true

# Add randomization to avoid system load spikes
RandomizedDelaySec=600

# Set appropriate user/group
User=backup
Group=backup

# Use proper working directory
WorkingDirectory=/opt/app

# Handle failures gracefully
OnFailure=failure-notification.service
```

## Migration Script

```bash
#!/bin/bash
# Convert cron job to systemd timer

SERVICE_NAME="$1"
CRON_SCHEDULE="$2"
COMMAND="$3"

# Create service file
cat > "/etc/systemd/system/$SERVICE_NAME.service" <<EOF
[Unit]
Description=$SERVICE_NAME

[Service]
Type=oneshot
ExecStart=$COMMAND
EOF

# Create timer file
cat > "/etc/systemd/system/$SERVICE_NAME.timer" <<EOF
[Unit]
Description=Timer for $SERVICE_NAME

[Timer]
OnCalendar=$CRON_SCHEDULE
Persistent=true

[Install]
WantedBy=timers.target
EOF

systemctl daemon-reload
systemctl enable "$SERVICE_NAME.timer"
systemctl start "$SERVICE_NAME.timer"
```