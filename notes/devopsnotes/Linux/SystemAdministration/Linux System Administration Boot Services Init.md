# Linux System Administration Boot Services Init

**System Boot, Services & Init** covers systemd service management, timer configuration, boot process understanding, and system initialization control.

## System Services with systemd

### Service Control Operations
```bash
# Basic service operations
systemctl status nginx                 # Check service status
systemctl start nginx                  # Start service
systemctl stop nginx                   # Stop service
systemctl restart nginx                # Restart service
systemctl reload nginx                 # Reload configuration without restart
systemctl enable nginx                 # Enable service at boot
systemctl disable nginx                # Disable service at boot

# Multiple service operations
systemctl start nginx apache2 mysql   # Start multiple services
systemctl restart nginx apache2       # Restart multiple services

# Service information
systemctl is-active nginx             # Check if service is active
systemctl is-enabled nginx            # Check if service is enabled
systemctl list-units --type=service   # List all service units
systemctl list-unit-files --type=service  # List all service unit files
```

### Service Configuration and Creation
```bash
# View service configuration
systemctl cat nginx                   # Show service unit file
systemctl show nginx                  # Show all properties
systemctl edit nginx                  # Edit service configuration

# Create custom service
cat << 'EOF' > /etc/systemd/system/myapp.service
[Unit]
Description=My Custom Application
After=network.target
Wants=network.target

[Service]
Type=simple
User=myapp
Group=myapp
WorkingDirectory=/opt/myapp
ExecStart=/opt/myapp/bin/myapp
ExecReload=/bin/kill -HUP $MAINPID
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd and start service
systemctl daemon-reload
systemctl enable myapp
systemctl start myapp
```

### Advanced Service Management
```bash
# Service dependencies
systemctl list-dependencies nginx     # Show service dependencies
systemctl list-dependencies --reverse nginx  # Show what depends on nginx

# Service isolation and sandboxing
cat << 'EOF' > /etc/systemd/system/secure-app.service
[Unit]
Description=Secure Application
After=network.target

[Service]
Type=simple
User=secureapp
Group=secureapp
ExecStart=/opt/secureapp/bin/app

# Security settings
NoNewPrivileges=true
PrivateTmp=true
PrivateDevices=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/var/lib/secureapp

[Install]
WantedBy=multi-user.target
EOF

# Service resource limits
systemctl set-property nginx MemoryLimit=512M
systemctl set-property nginx CPUQuota=50%
```

## systemd Timers

### Timer Creation and Management
```bash
# Create timer unit
cat << 'EOF' > /etc/systemd/system/backup.timer
[Unit]
Description=Run backup daily
Requires=backup.service

[Timer]
OnCalendar=daily
Persistent=true

[Install]
WantedBy=timers.target
EOF

# Create corresponding service
cat << 'EOF' > /etc/systemd/system/backup.service
[Unit]
Description=Backup Service

[Service]
Type=oneshot
ExecStart=/usr/local/bin/backup.sh
User=backup
Group=backup
EOF

# Enable and start timer
systemctl daemon-reload
systemctl enable backup.timer
systemctl start backup.timer
```

### Timer Scheduling Examples
```bash
# Timer scheduling options
OnCalendar=hourly                     # Every hour
OnCalendar=daily                      # Every day at midnight
OnCalendar=weekly                     # Every Monday at midnight
OnCalendar=monthly                    # First day of month at midnight
OnCalendar=*-*-* 02:00:00            # Daily at 2 AM
OnCalendar=Mon,Tue,Wed,Thu,Fri 09:00  # Weekdays at 9 AM
OnCalendar=*-*-01 03:00:00           # First day of every month at 3 AM

# Relative timers
OnBootSec=15min                       # 15 minutes after boot
OnStartupSec=30min                    # 30 minutes after systemd started
OnUnitActiveSec=5min                  # 5 minutes after unit was activated
OnUnitInactiveSec=1h                  # 1 hour after unit became inactive
```

### Timer Management Commands
```bash
# Timer operations
systemctl list-timers                # List all timers
systemctl list-timers --all          # Include inactive timers
systemctl status backup.timer        # Check timer status
systemctl show backup.timer          # Show timer properties

# Timer information
systemctl list-timers backup.timer   # Show specific timer
journalctl -u backup.timer           # View timer logs
journalctl -u backup.service         # View service logs
```

## Boot Process and Targets

### systemd Targets
```bash
# Target management
systemctl get-default                 # Show default target
systemctl set-default multi-user.target  # Set default target
systemctl isolate rescue.target      # Switch to rescue mode
systemctl isolate multi-user.target  # Switch to multi-user mode

# Common targets
systemctl list-units --type=target   # List all targets
systemctl list-dependencies graphical.target  # Show target dependencies

# Target states
systemctl is-active multi-user.target    # Check if target is active
systemctl list-unit-files --type=target  # List all target unit files
```

### Boot Analysis
```bash
# Boot time analysis
systemd-analyze                      # Show boot time
systemd-analyze blame                # Show service startup times
systemd-analyze critical-chain       # Show critical path
systemd-analyze plot > boot.svg      # Generate boot chart

# Boot troubleshooting
systemd-analyze verify unit.service  # Verify unit file syntax
systemctl list-jobs                  # Show active jobs
systemctl list-dependencies --failed # Show failed dependencies
```

### Emergency and Recovery
```bash
# Boot into different modes
# Add to kernel command line:
systemd.unit=rescue.target           # Boot into rescue mode
systemd.unit=emergency.target        # Boot into emergency mode
systemd.unit=multi-user.target       # Boot into multi-user mode
init=/bin/bash                       # Boot directly to bash

# Recovery operations
systemctl daemon-reload              # Reload all unit files
systemctl reset-failed               # Reset failed units
systemctl rescue                     # Switch to rescue mode
systemctl emergency                  # Switch to emergency mode
```

## System Logging with journald

### Basic Journal Operations
```bash
# View logs
journalctl                           # View all logs
journalctl -f                        # Follow logs (like tail -f)
journalctl -n 50                     # Show last 50 entries
journalctl --since today             # Show today's logs
journalctl --since "2023-01-01"      # Show logs since date
journalctl --until "1 hour ago"      # Show logs until time

# Service-specific logs
journalctl -u nginx                  # Show logs for nginx service
journalctl -u nginx -f               # Follow nginx logs
journalctl -u nginx --since "10 minutes ago"  # Recent nginx logs
```

### Advanced Journal Filtering
```bash
# Filter by priority
journalctl -p err                    # Show only error messages
journalctl -p warning..emerg         # Show warning and above
journalctl -p debug                  # Show debug messages

# Filter by time
journalctl --since "2023-01-01 00:00:00"
journalctl --since yesterday
journalctl --since "1 hour ago"
journalctl --until "2023-01-31"

# Filter by fields
journalctl _PID=1234                 # Show logs for specific PID
journalctl _UID=1000                 # Show logs for specific user
journalctl _SYSTEMD_UNIT=nginx.service  # Show logs for systemd unit
journalctl SYSLOG_IDENTIFIER=kernel # Show kernel logs
```

### Journal Management
```bash
# Journal disk usage
journalctl --disk-usage              # Show journal disk usage
du -sh /var/log/journal              # Check journal directory size

# Journal cleanup
journalctl --vacuum-time=2weeks      # Keep only 2 weeks of logs
journalctl --vacuum-size=100M        # Keep only 100MB of logs
journalctl --rotate                  # Rotate journal files

# Journal configuration
cat << 'EOF' > /etc/systemd/journald.conf.d/size.conf
[Journal]
SystemMaxUse=500M
SystemKeepFree=1G
SystemMaxFileSize=50M
MaxRetentionSec=1month
EOF

systemctl restart systemd-journald
```

### Journal Export and Analysis
```bash
# Export logs
journalctl -o json > logs.json       # Export as JSON
journalctl -o json-pretty             # Pretty JSON output
journalctl --output=short-iso         # ISO timestamp format
journalctl --output=verbose           # Verbose output

# Log analysis
journalctl | grep -E "(error|failed|warning)"  # Find errors and warnings
journalctl -p err --since today | wc -l        # Count today's errors
journalctl _SYSTEMD_UNIT=nginx.service | grep -c "GET"  # Count GET requests

# Journal fields
journalctl --fields                   # Show available fields
journalctl -F _SYSTEMD_UNIT          # Show all systemd units
journalctl -F SYSLOG_IDENTIFIER      # Show all syslog identifiers
```

## Init System Management

### systemd Unit Types
```bash
# List different unit types
systemctl list-units --type=service  # Service units
systemctl list-units --type=socket   # Socket units
systemctl list-units --type=timer    # Timer units
systemctl list-units --type=mount    # Mount units
systemctl list-units --type=device   # Device units

# Unit file locations
/etc/systemd/system/                 # Local unit files
/usr/lib/systemd/system/             # System unit files
/run/systemd/system/                 # Runtime unit files

# Unit file priority (highest to lowest)
# 1. /etc/systemd/system/
# 2. /run/systemd/system/
# 3. /usr/lib/systemd/system/
```

### Custom Unit Creation
```bash
# Socket activation example
cat << 'EOF' > /etc/systemd/system/myapp.socket
[Unit]
Description=MyApp Socket

[Socket]
ListenStream=8080
Accept=no

[Install]
WantedBy=sockets.target
EOF

# Mount unit example
cat << 'EOF' > /etc/systemd/system/data.mount
[Unit]
Description=Data Mount
Before=myapp.service

[Mount]
What=/dev/disk/by-uuid/12345678-1234-1234-1234-123456789abc
Where=/data
Type=ext4
Options=defaults

[Install]
WantedBy=multi-user.target
EOF
```

### System State Management
```bash
# System control
systemctl poweroff                   # Shutdown system
systemctl reboot                     # Restart system
systemctl suspend                    # Suspend system
systemctl hibernate                  # Hibernate system
systemctl hybrid-sleep               # Hybrid sleep

# System information
systemctl status                     # Show system status
systemctl list-jobs                  # Show active jobs
systemctl list-sockets               # Show active sockets
systemctl list-machines              # Show virtual machines/containers

# Environment
systemctl show-environment           # Show systemd environment
systemctl set-environment VAR=value  # Set environment variable
systemctl unset-environment VAR      # Unset environment variable
```