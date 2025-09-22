# Linux Systemd & Services

**Systemd** is the modern init system and service manager for Linux, providing parallel service startup, dependency management, and comprehensive system control for production environments.


## Systemd Architecture

### Core Components

**systemd**: Main system and service manager (PID 1)
**systemctl**: Primary tool for controlling systemd services
**journald**: Centralized logging service
**logind**: Login and session management
**networkd**: Network configuration management
**resolved**: DNS resolution service

### Systemd Unit Types

```bash
# Unit types and their purposes
.service     # System services (daemons)
.socket      # Network or IPC sockets
.mount       # Filesystem mount points
.target      # Groups of units (runlevels)
.timer       # Scheduled tasks (cron alternative)
.path        # Path-based activation
.device      # Device files
.swap        # Swap files/partitions
.slice       # Resource management groups
.scope       # Externally created processes
```

### Systemd Directory Structure

```bash
# Systemd directories hierarchy
/etc/systemd/system/          # Local unit files (highest priority)
/run/systemd/system/          # Runtime unit files
/usr/lib/systemd/system/      # Distribution unit files
/lib/systemd/system/          # Distribution unit files (symlink)

# Configuration directories
/etc/systemd/                 # Main systemd configuration
/etc/systemd/system.conf      # Main systemd configuration file
/etc/systemd/user.conf        # User session configuration
/etc/systemd/logind.conf      # Login manager configuration
```

---

## Service Management

### Basic Service Operations

```bash
# Service status and control
systemctl status service_name          # Show service status
systemctl is-active service_name       # Check if service is running
systemctl is-enabled service_name      # Check if service is enabled
systemctl is-failed service_name       # Check if service failed

# Service lifecycle management
systemctl start service_name           # Start service
systemctl stop service_name            # Stop service
systemctl restart service_name         # Restart service
systemctl reload service_name          # Reload configuration
systemctl kill service_name            # Send signal to service

# Service enablement (auto-start)
systemctl enable service_name          # Enable at boot
systemctl disable service_name         # Disable at boot
systemctl enable --now service_name    # Enable and start immediately
systemctl mask service_name            # Prevent service from starting
systemctl unmask service_name          # Remove mask
```

### Advanced Service Control

```bash
# Service information and analysis
systemctl show service_name            # Show all properties
systemctl cat service_name             # Show unit file content
systemctl list-dependencies service_name  # Show dependencies
systemctl list-units --type=service    # List all services

# Service filtering and selection
systemctl list-units --state=running   # Show running units
systemctl list-units --state=failed    # Show failed units
systemctl list-unit-files --state=enabled  # Show enabled services
systemctl --failed                     # Quick view of failed units

# Service logs
journalctl -u service_name             # Show service logs
journalctl -u service_name -f          # Follow service logs
journalctl -u service_name --since today
journalctl -u service_name --since "2024-01-01 00:00:00"
```

### Service Configuration Override

```bash
# Create service override directory
mkdir -p /etc/systemd/system/service_name.service.d/

# Create override configuration
cat << 'EOF' > /etc/systemd/system/nginx.service.d/override.conf
[Service]
# Increase restart attempts
Restart=always
RestartSec=5
StartLimitBurst=10
StartLimitIntervalSec=60

# Resource limits
LimitNOFILE=65536
LimitNPROC=4096

# Security hardening
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
PrivateTmp=true
EOF

# Reload systemd configuration
systemctl daemon-reload
systemctl restart nginx
```

---

## Unit Files & Configuration

### Service Unit File Structure

```ini
# Example comprehensive service unit file
[Unit]
Description=My Application Service
Documentation=https://company.com/docs/myapp
Wants=network-online.target
After=network-online.target
Requires=postgresql.service
Before=nginx.service
Conflicts=myapp-old.service

[Service]
Type=simple
ExecStart=/usr/local/bin/myapp --config /etc/myapp/config.yml
ExecReload=/bin/kill -HUP $MAINPID
ExecStop=/bin/kill -TERM $MAINPID
PIDFile=/run/myapp/myapp.pid
Restart=always
RestartSec=5
StartLimitBurst=3
StartLimitIntervalSec=60

# User and permissions
User=myapp
Group=myapp
WorkingDirectory=/var/lib/myapp

# Security settings
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
PrivateTmp=true
PrivateDevices=true
ProtectKernelTunables=true
ProtectControlGroups=true
RestrictRealtime=true
MemoryDenyWriteExecute=true

# Resource limits
LimitNOFILE=65536
LimitNPROC=4096
MemoryMax=1G
CPUQuota=200%

# Environment
Environment=NODE_ENV=production
Environment=LOG_LEVEL=info
EnvironmentFile=/etc/myapp/environment

[Install]
WantedBy=multi-user.target
RequiredBy=nginx.service
```

### Service Types

```bash
# Service type options
Type=simple      # Default, process doesn't fork
Type=forking     # Process forks and parent exits
Type=oneshot     # Process exits after completion
Type=notify      # Process sends notification when ready
Type=idle        # Wait for all jobs to complete before starting
Type=dbus        # Process takes D-Bus name when ready

# Examples for different types
[Service]
Type=simple
ExecStart=/usr/bin/myapp

[Service]
Type=forking
ExecStart=/usr/sbin/nginx
PIDFile=/run/nginx.pid

[Service]
Type=oneshot
ExecStart=/usr/local/bin/backup-script.sh
RemainAfterExit=yes

[Service]
Type=notify
ExecStart=/usr/bin/myapp-with-notify
NotifyAccess=main
```

### Advanced Unit Configuration

```ini
# Multi-instance service template (myapp@.service)
[Unit]
Description=My Application Instance %i
Documentation=https://company.com/docs/myapp
After=network.target

[Service]
Type=simple
ExecStart=/usr/local/bin/myapp --instance %i
ExecReload=/bin/kill -HUP $MAINPID
Restart=always
User=myapp
Group=myapp

# Instance-specific configuration
Environment=INSTANCE_NAME=%i
EnvironmentFile=/etc/myapp/instances/%i.conf
WorkingDirectory=/var/lib/myapp/%i

[Install]
WantedBy=multi-user.target

# Usage: systemctl start myapp@web.service myapp@api.service
```

---

## Targets & Boot Process

### Understanding Targets

```bash
# List available targets
systemctl list-units --type=target      # Active targets
systemctl list-unit-files --type=target # All available targets

# Common targets (runlevels equivalent)
emergency.target      # Emergency shell (runlevel 1)
rescue.target         # Rescue mode (single user)
multi-user.target     # Multi-user mode (runlevel 3)
graphical.target      # Graphical mode (runlevel 5)
reboot.target         # Reboot system
poweroff.target       # Power off system

# Target operations
systemctl get-default              # Show default target
systemctl set-default multi-user.target  # Set default target
systemctl isolate rescue.target    # Switch to target immediately
```

### Custom Target Creation

```ini
# Create custom target: /etc/systemd/system/myapp.target
[Unit]
Description=My Application Stack
Documentation=https://company.com/docs/deployment
Requires=multi-user.target
After=multi-user.target
AllowIsolate=yes

[Install]
WantedBy=multi-user.target

# Services that want this target
# Add to each service: WantedBy=myapp.target
```

### Boot Process Analysis

```bash
# Analyze boot performance
systemd-analyze                    # Overall boot time
systemd-analyze blame              # Services by start time
systemd-analyze critical-chain     # Critical path analysis
systemd-analyze plot > boot.svg    # Visual boot chart

# Verify boot process
systemd-analyze verify service_name.service  # Verify unit file
systemctl list-jobs                # Show active jobs
systemctl list-dependencies --before multi-user.target
```

---

## Timers & Scheduling

### Timer Unit Files

```ini
# Example timer: /etc/systemd/system/backup.timer
[Unit]
Description=Daily Backup Timer
Requires=backup.service

[Timer]
# Scheduling options
OnCalendar=daily
OnCalendar=*-*-* 02:00:00          # Daily at 2 AM
OnCalendar=Mon *-*-* 09:00:00      # Mondays at 9 AM
OnCalendar=*-*-01 03:00:00         # Monthly on 1st at 3 AM

# Alternative scheduling
OnBootSec=15min                    # 15 minutes after boot
OnUnitActiveSec=1h                 # 1 hour after last activation
OnUnitInactiveSec=30min            # 30 minutes after deactivation

# Timer behavior
Persistent=true                    # Run if system was down
RandomizedDelaySec=300             # Random delay up to 5 minutes
AccuracySec=1min                   # Timer accuracy

[Install]
WantedBy=timers.target

# Corresponding service: /etc/systemd/system/backup.service
[Unit]
Description=System Backup Service
Wants=network-online.target
After=network-online.target

[Service]
Type=oneshot
ExecStart=/usr/local/bin/backup-script.sh
User=backup
Group=backup
```

### Timer Management

```bash
# Timer operations
systemctl enable --now backup.timer   # Enable and start timer
systemctl list-timers                 # List all timers
systemctl list-timers --all           # Include inactive timers
systemctl status backup.timer         # Timer status

# Advanced timer information
systemctl show backup.timer --property=NextElapseUSSec
journalctl -u backup.timer            # Timer logs
systemctl edit backup.timer           # Edit timer configuration
```

### Complex Timer Examples

```ini
# Weekly maintenance timer
[Timer]
OnCalendar=weekly
Persistent=true
RandomizedDelaySec=3600

# Business hours timer (weekdays 9-17)
[Timer]
OnCalendar=Mon..Fri *-*-* 09,10,11,12,13,14,15,16,17:00:00

# Multiple time specification
[Timer]
OnCalendar=*-*-* 06:00:00
OnCalendar=*-*-* 18:00:00

# High-frequency timer
[Timer]
OnUnitActiveSec=30s
AccuracySec=1s
```

---

## Journald & Logging

### Journal Configuration

```bash
# Main configuration: /etc/systemd/journald.conf
cat << 'EOF' > /etc/systemd/journald.conf
[Journal]
# Storage configuration
Storage=persistent
Compress=yes
SystemMaxUse=4G
SystemKeepFree=1G
SystemMaxFileSize=128M
SystemMaxFiles=100

# Runtime configuration
RuntimeMaxUse=512M
RuntimeKeepFree=256M
RuntimeMaxFileSize=64M
RuntimeMaxFiles=20

# Log forwarding
ForwardToSyslog=no
ForwardToKMsg=no
ForwardToConsole=no
ForwardToWall=yes

# Message processing
MaxRetentionSec=1month
SyncIntervalSec=5m
RateLimitInterval=30s
RateLimitBurst=10000
EOF

systemctl restart systemd-journald
```

### Journal Operations

```bash
# Basic journal queries
journalctl                         # All journal entries
journalctl -n 50                   # Last 50 entries
journalctl -f                      # Follow journal
journalctl --since today           # Today's entries
journalctl --since "2024-01-01"    # Since specific date
journalctl --until "1 hour ago"    # Until specific time

# Service-specific logs
journalctl -u service_name         # Specific service
journalctl -u service_name --since today
journalctl -u service_name -o json # JSON output format

# Advanced filtering
journalctl _PID=1234               # By process ID
journalctl _UID=1000               # By user ID
journalctl PRIORITY=3              # By priority (err)
journalctl _COMM=sshd              # By command name
journalctl /usr/bin/nginx          # By executable path

# Priority levels
journalctl PRIORITY=0              # Emergency
journalctl PRIORITY=1              # Alert
journalctl PRIORITY=2              # Critical
journalctl PRIORITY=3              # Error
journalctl PRIORITY=4              # Warning
journalctl PRIORITY=5              # Notice
journalctl PRIORITY=6              # Info
journalctl PRIORITY=7              # Debug
```

### Journal Maintenance

```bash
# Journal disk usage
journalctl --disk-usage            # Show current usage
journalctl --verify                # Verify journal integrity

# Journal cleanup
journalctl --vacuum-time=1week     # Keep only 1 week
journalctl --vacuum-size=1G        # Keep only 1GB
journalctl --vacuum-files=10       # Keep only 10 files

# Journal rotation
systemctl kill --kill-who=main --signal=SIGUSR2 systemd-journald
```

### Custom Logging

```bash
# Log from scripts
logger "Custom message from script"
logger -t myapp "Application started"
logger -p local0.info "Info message"

# Structured logging
systemd-cat -t myapp /usr/local/bin/myapp
echo "Hello from systemd" | systemd-cat -t myapp -p info

# Journal fields in scripts
#!/bin/bash
exec > >(systemd-cat -t backup-script)
exec 2>&1

echo "Starting backup process"
# Script continues...
```

---

## Resource Management

### Cgroup Integration

```bash
# View service cgroup
systemctl status service_name       # Shows cgroup path
systemd-cgls                        # Show cgroup tree
systemd-cgtop                       # Real-time cgroup statistics

# Cgroup hierarchy
/sys/fs/cgroup/system.slice/service_name.service/
```

### Resource Limits

```ini
# CPU limits
CPUAccounting=true
CPUQuota=200%                      # 2 CPU cores max
CPUShares=1024                     # Relative CPU weight
CPUAffinity=0 1                    # Bind to specific CPUs

# Memory limits
MemoryAccounting=true
MemoryMax=1G                       # Hard limit
MemoryHigh=800M                    # Soft limit (throttling)
MemorySwapMax=512M                 # Swap limit

# I/O limits
IOAccounting=true
IOWeight=100                       # I/O priority weight
IOReadBandwidthMax=/dev/sda 50M    # Read bandwidth limit
IOWriteBandwidthMax=/dev/sda 25M   # Write bandwidth limit
IOReadIOPSMax=/dev/sda 1000        # Read IOPS limit
IOWriteIOPSMax=/dev/sda 500        # Write IOPS limit

# Task limits
TasksAccounting=true
TasksMax=1000                      # Maximum number of tasks

# Device access
DeviceAllow=/dev/null rw
DeviceAllow=/dev/zero rw
DevicePolicy=strict                # Deny all device access by default
```

### Slice Management

```ini
# Custom slice: /etc/systemd/system/myapp.slice
[Unit]
Description=My Application Slice
Before=slices.target

[Slice]
# Resource limits for the entire slice
MemoryMax=4G
CPUQuota=400%
TasksMax=2000

[Install]
WantedBy=slices.target

# Assign services to slice in service file
[Service]
Slice=myapp.slice
```

---

## Service Dependencies

### Dependency Types

```ini
# Dependency types in [Unit] section
Requires=service2.service          # Hard dependency (fails if dependency fails)
Wants=service3.service             # Soft dependency (continues if dependency fails)
Requisite=service4.service         # Must be running already
BindsTo=service5.service           # Stop when dependency stops
PartOf=service6.service            # Start/stop together

# Ordering dependencies
Before=service7.service            # Start before specified service
After=service8.service             # Start after specified service

# Conflict resolution
Conflicts=service9.service         # Cannot run simultaneously
```

### Complex Dependency Examples

```ini
# Web application with database dependency
[Unit]
Description=Web Application
Wants=network-online.target
After=network-online.target
Requires=postgresql.service redis.service
After=postgresql.service redis.service
Before=nginx.service

# Load balancer that requires multiple backends
[Unit]
Description=Load Balancer
Wants=webapp@1.service webapp@2.service webapp@3.service
After=webapp@1.service webapp@2.service webapp@3.service

# Backup service that conflicts with maintenance
[Unit]
Description=Backup Service
Conflicts=maintenance.service
```

### Dependency Analysis

```bash
# Analyze dependencies
systemctl list-dependencies service_name      # Show dependencies
systemctl list-dependencies --reverse service_name  # Reverse dependencies
systemctl list-dependencies --all service_name      # All dependencies

# Dependency graph
systemd-analyze dot service_name.service | dot -Tsvg > deps.svg

# Check ordering
systemctl show service_name --property=After
systemctl show service_name --property=Before
```

---

## Troubleshooting

### Common Service Issues

#### Service Fails to Start

```bash
# Diagnostic steps
systemctl status service_name       # Check service status
journalctl -u service_name -n 50   # Check recent logs
systemctl cat service_name         # Verify unit file syntax

# Test service manually
sudo -u service_user /usr/bin/service_command  # Test as service user
strace -f systemctl start service_name         # Trace system calls

# Check dependencies
systemctl list-dependencies service_name --failed
systemctl is-active dependency.service
```

#### Service Crashes Repeatedly

```bash
# Check crash information
systemctl status service_name       # Exit codes and signals
journalctl -u service_name --since "1 hour ago"
coredumpctl list service_name       # Core dumps

# Analyze restart behavior
systemctl show service_name --property=StartLimitBurst
systemctl show service_name --property=RestartSec
systemctl reset-failed service_name # Reset failure count

# Temporary debugging
systemctl edit service_name         # Add debug options
# Add: Environment=DEBUG=1
```

#### Permission Issues

```bash
# Check user and group
systemctl show service_name --property=User
systemctl show service_name --property=Group
id service_user                     # Verify user exists

# Check file permissions
ls -la /path/to/service/files
sudo -u service_user ls -la /path/to/files

# SELinux/AppArmor issues
ausearch -m AVC -ts recent          # SELinux denials
journalctl | grep -i apparmor       # AppArmor violations
```

### Debugging Tools

```bash
# Service debugging script
#!/bin/bash
SERVICE_NAME="$1"

echo "=== Service Debug Information for $SERVICE_NAME ==="

echo -e "\n1. Service Status:"
systemctl status "$SERVICE_NAME" --no-pager

echo -e "\n2. Service Configuration:"
systemctl cat "$SERVICE_NAME"

echo -e "\n3. Recent Logs:"
journalctl -u "$SERVICE_NAME" -n 20 --no-pager

echo -e "\n4. Dependencies:"
systemctl list-dependencies "$SERVICE_NAME" --failed

echo -e "\n5. Resource Usage:"
systemctl show "$SERVICE_NAME" --property=CPUUsageNSec,MemoryCurrent,TasksCurrent

echo -e "\n6. Environment:"
systemctl show "$SERVICE_NAME" --property=Environment

echo -e "\n7. File Permissions:"
CONFIG_FILE=$(systemctl show "$SERVICE_NAME" --property=FragmentPath --value)
ls -la "$CONFIG_FILE"

echo -e "\n8. Process Information:"
systemctl show "$SERVICE_NAME" --property=MainPID --value | xargs -I {} ps -p {} -o pid,ppid,user,cmd
```

### Performance Analysis

```bash
# Service performance monitoring
systemd-cgtop                      # Real-time resource usage
systemctl show service_name --property=CPUUsageNSec
systemctl show service_name --property=MemoryCurrent

# Boot performance impact
systemd-analyze blame | grep service_name
systemd-analyze critical-chain service_name

# Resource limit monitoring
journalctl -u service_name | grep -i "memory\|cpu\|limit"
```

---

## Advanced Operations

### Service Templates and Instances

```bash
# Service template file: myapp@.service
systemctl start myapp@web.service   # Start web instance
systemctl start myapp@api.service   # Start API instance
systemctl enable myapp@*.service    # Enable all instances

# Instance management
systemctl list-units "myapp@*"      # List all instances
systemctl stop "myapp@*"            # Stop all instances
```

### Socket Activation

```ini
# Socket unit: myapp.socket
[Unit]
Description=My Application Socket

[Socket]
ListenStream=8080
Accept=false
SocketUser=myapp
SocketGroup=myapp
SocketMode=0660

[Install]
WantedBy=sockets.target

# Corresponding service: myapp.service
[Unit]
Description=My Application
Requires=myapp.socket

[Service]
Type=notify
ExecStart=/usr/local/bin/myapp --systemd-socket
StandardInput=socket
```

### Path-Based Activation

```ini
# Path unit: watch-config.path
[Unit]
Description=Watch Configuration Files
PathExists=/etc/myapp/config.yml
PathChanged=/etc/myapp/

[Path]
PathChanged=/etc/myapp/config.yml
Unit=reload-config.service

[Install]
WantedBy=multi-user.target

# Triggered service: reload-config.service
[Unit]
Description=Reload Configuration

[Service]
Type=oneshot
ExecStart=/usr/local/bin/reload-config.sh
```

### Systemd User Services

```bash
# User service management
systemctl --user status service_name
systemctl --user enable service_name
systemctl --user start service_name

# User service location
~/.config/systemd/user/service_name.service

# Enable lingering for user services
sudo loginctl enable-linger username

# User environment
systemctl --user import-environment PATH
systemctl --user set-environment VAR=value
```

---

## Best Practices

### Production Service Configuration

```ini
# Production-ready service template
[Unit]
Description=Production Service
Documentation=https://company.com/docs/service
Wants=network-online.target
After=network-online.target
StartLimitBurst=3
StartLimitIntervalSec=300

[Service]
Type=simple
ExecStart=/usr/local/bin/service
ExecReload=/bin/kill -HUP $MAINPID
ExecStop=/bin/kill -TERM $MAINPID
KillMode=mixed
KillSignal=SIGTERM
TimeoutStopSec=30
Restart=always
RestartSec=5

# Security hardening
User=service
Group=service
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
PrivateTmp=true
PrivateDevices=true
ProtectKernelTunables=true
ProtectControlGroups=true
RestrictRealtime=true
MemoryDenyWriteExecute=true
SystemCallFilter=@system-service
SystemCallErrorNumber=EPERM

# Resource limits
LimitNOFILE=65536
LimitNPROC=4096
MemoryMax=1G
CPUQuota=200%

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=service

[Install]
WantedBy=multi-user.target
```

### Security Best Practices

```bash
# 1. Run services as non-root users
User=service_user
Group=service_group

# 2. Use security options
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
PrivateTmp=true

# 3. Limit resources
MemoryMax=1G
CPUQuota=100%
TasksMax=1000

# 4. Restrict system calls
SystemCallFilter=@system-service
SystemCallErrorNumber=EPERM

# 5. Use proper file permissions
chmod 644 /etc/systemd/system/service.service
chown root:root /etc/systemd/system/service.service
```

### Monitoring and Alerting

```bash
# Service monitoring script
#!/bin/bash
SERVICES=("nginx" "postgresql" "redis" "myapp")

for service in "${SERVICES[@]}"; do
    if ! systemctl is-active --quiet "$service"; then
        echo "ALERT: $service is not running"
        # Send alert notification
        curl -X POST "$WEBHOOK_URL" -d "Service $service failed on $(hostname)"
    fi
done

# Check for failed services
systemctl --failed --no-legend | while read -r unit load active sub description; do
    echo "FAILED: $unit - $description"
    # Send alert
done
```

---

## Cross-References

### Essential Reading
- **[[Linux fundamental]]** - Core Linux concepts and boot process
- **[[Linux Commands]]** - Command-line tools for service management
- **[[Linux Process Management]]** - Process control and monitoring
- **[[Linux Security]]** - Security hardening and compliance

### Advanced Topics
- **[[Linux Package Management]]** - Service installation and updates
- **[[Linux Shell Scripting Essentials]]** - Automation and service management scripts
- **[[Linux Storage Management]]** - Filesystem services and mount management

### Quick Navigation
- **Getting Started**: Linux fundamental → Linux Systemd & Services → Linux Commands
- **Service Management**: Linux Systemd & Services → Linux Process Management → Linux Security
- **Automation**: Linux Systemd & Services → Linux Shell Scripting Essentials → Linux Package Management

---

*This focused guide provides comprehensive systemd knowledge essential for modern Linux system administration and service management in production environments.*