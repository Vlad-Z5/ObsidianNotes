# Linux Log Rotation

**Log rotation** prevents log files from consuming excessive disk space by automatically archiving, compressing, and deleting old log files.

## Logrotate Overview

Logrotate is the standard tool for managing log file rotation:
- Runs daily via cron
- Configurable rotation schedules
- Compression and archival
- Post-rotation commands
- Email notifications

## Main Configuration

```bash
# Main logrotate configuration
/etc/logrotate.conf

# Application-specific configurations
/etc/logrotate.d/

# Check logrotate status
cat /var/lib/logrotate/status
```

## Basic Logrotate Configuration

```bash
# /etc/logrotate.conf
# Global settings
weekly
rotate 4
create
dateext
compress
delaycompress
notifempty
missingok

# Include application configs
include /etc/logrotate.d
```

## Logrotate Directives

### Rotation Schedule
```bash
daily          # Rotate daily
weekly         # Rotate weekly
monthly        # Rotate monthly
yearly         # Rotate yearly
size 10M       # Rotate when file reaches 10MB
```

### Retention
```bash
rotate 7       # Keep 7 old versions
maxage 30      # Delete files older than 30 days
```

### Compression
```bash
compress       # Compress rotated files
nocompress     # Don't compress
delaycompress  # Compress on next rotation
compresscmd gzip    # Use specific compression command
compressext .gz     # Use specific extension
```

### File Handling
```bash
create 644 root root    # Create new file with permissions
nocreate               # Don't create new file
copytruncate          # Copy file and truncate original
copy                  # Copy file without truncating
```

## Application Configuration Examples

### Web Server Logs
```bash
# /etc/logrotate.d/nginx
/var/log/nginx/*.log {
    daily
    rotate 30
    missingok
    notifempty
    compress
    delaycompress
    create 644 nginx nginx
    postrotate
        systemctl reload nginx
    endscript
}
```

### Application Logs
```bash
# /etc/logrotate.d/myapp
/var/log/myapp/*.log {
    weekly
    rotate 12
    compress
    delaycompress
    missingok
    notifempty
    create 640 myapp myapp
    postrotate
        systemctl kill -s USR1 myapp
    endscript
}
```

### High-Volume Logs
```bash
# /etc/logrotate.d/high-volume
/var/log/app/access.log {
    hourly
    rotate 168
    size 100M
    compress
    delaycompress
    notifempty
    create 644 app app
    postrotate
        kill -USR1 $(cat /var/run/app.pid)
    endscript
}
```

## Database Log Rotation

### MySQL Logs
```bash
# /etc/logrotate.d/mysql
/var/log/mysql/*.log {
    daily
    rotate 7
    missingok
    notifempty
    compress
    delaycompress
    copytruncate
}

# For binary logs - don't use copytruncate
/var/log/mysql/mysql-bin.* {
    daily
    rotate 14
    missingok
    notifempty
    compress
    delaycompress
    postrotate
        mysql -e "FLUSH LOGS"
    endscript
}
```

### PostgreSQL Logs
```bash
# /etc/logrotate.d/postgresql
/var/log/postgresql/*.log {
    weekly
    rotate 8
    compress
    delaycompress
    missingok
    notifempty
    create 640 postgres postgres
    postrotate
        systemctl reload postgresql
    endscript
}
```

## Manual Rotation

```bash
# Run logrotate manually
logrotate /etc/logrotate.conf

# Debug mode (don't actually rotate)
logrotate -d /etc/logrotate.conf

# Force rotation
logrotate -f /etc/logrotate.conf

# Test specific config
logrotate -d /etc/logrotate.d/nginx

# Verbose output
logrotate -v /etc/logrotate.conf
```

## Advanced Features

### Multiple Log Files
```bash
# Rotate multiple files together
/var/log/app/*.log /var/log/app/*/*.log {
    daily
    rotate 30
    compress
    missingok
    notifempty
    sharedscripts
    postrotate
        systemctl reload app
    endscript
}
```

### Conditional Rotation
```bash
# Rotate based on file size and time
/var/log/app/huge.log {
    daily
    rotate 7
    size 1G
    compress
    missingok
    notifempty
    maxage 30
}
```

### Email Notifications
```bash
# Email compressed logs before deletion
/var/log/important/*.log {
    weekly
    rotate 4
    compress
    mail admin@company.com
    mailfirst      # Email newest log
    # or maillast  # Email oldest log before deletion
}
```

## Custom Scripts

### Pre/Post Rotation Scripts
```bash
/var/log/app/*.log {
    daily
    rotate 7
    compress

    prerotate
        # Run before rotation
        echo "Starting log rotation for $(date)" >> /var/log/rotation.log
    endscript

    postrotate
        # Run after rotation
        systemctl reload app
        echo "Log rotation completed for $(date)" >> /var/log/rotation.log
    endscript

    firstaction
        # Run once before all files are rotated
        echo "Beginning rotation cycle" >> /var/log/rotation.log
    endscript

    lastaction
        # Run once after all files are rotated
        echo "Rotation cycle complete" >> /var/log/rotation.log
    endscript
}
```

## Monitoring and Troubleshooting

### Check Logrotate Status
```bash
# View last rotation times
cat /var/lib/logrotate/status

# Check if logrotate is running
systemctl status logrotate.timer

# Check cron job
cat /etc/cron.daily/logrotate
```

### Debug Issues
```bash
# Test configuration
logrotate -d /etc/logrotate.conf

# Check for errors
journalctl -u logrotate

# Manual test run
logrotate -f -v /etc/logrotate.d/myapp

# Check permissions
ls -la /var/log/
ls -la /etc/logrotate.d/
```

## Alternative Rotation Methods

### Using Systemd Timers
```bash
# Create systemd timer for custom rotation
sudo tee /etc/systemd/system/custom-logrotate.service <<EOF
[Unit]
Description=Custom Log Rotation

[Service]
Type=oneshot
ExecStart=/usr/sbin/logrotate /etc/logrotate.d/custom
EOF

sudo tee /etc/systemd/system/custom-logrotate.timer <<EOF
[Unit]
Description=Run custom log rotation hourly

[Timer]
OnCalendar=hourly
Persistent=true

[Install]
WantedBy=timers.target
EOF

sudo systemctl enable custom-logrotate.timer
sudo systemctl start custom-logrotate.timer
```

### Using Rsyslog Rotation
```bash
# Built-in rsyslog rotation
$outchannel log_rotation,/var/log/app.log,52428800,/usr/local/bin/rotate-log.sh
*.* :omfile:$log_rotation
```

## Production Best Practices

```bash
# Production logrotate configuration
/var/log/production/*.log {
    daily
    rotate 30
    maxage 90
    size 100M
    compress
    delaycompress
    missingok
    notifempty
    create 640 app app
    dateext
    dateformat -%Y%m%d-%s

    sharedscripts
    postrotate
        # Graceful reload
        systemctl reload app 2>/dev/null || true
        # Notify monitoring system
        curl -X POST "http://monitoring/api/log-rotated" -d "service=app" 2>/dev/null || true
    endscript
}
```

## Emergency Log Cleanup

```bash
#!/bin/bash
# Emergency log cleanup script

# Find large log files
find /var/log -type f -size +100M -name "*.log" -exec ls -lh {} \;

# Compress large logs
find /var/log -type f -size +100M -name "*.log" -exec gzip {} \;

# Remove old compressed logs
find /var/log -type f -name "*.gz" -mtime +30 -delete

# Truncate current logs if too large
find /var/log -type f -size +1G -name "*.log" -exec truncate -s 100M {} \;
```