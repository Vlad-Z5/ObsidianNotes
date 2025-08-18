# Linux System Administration

## System Boot, Services & Init

### Systemd Service Management

#### Service Control Operations

```bash
# Basic service control
systemctl status nginx                 # Check service status
systemctl start nginx                  # Start service
systemctl stop nginx                   # Stop service
systemctl restart nginx                # Restart service (stop then start)
systemctl reload nginx                 # Reload configuration without restart
systemctl enable nginx                 # Enable service at boot
systemctl disable nginx                # Disable service at boot
systemctl mask nginx                   # Prevent service from being started
systemctl unmask nginx                 # Remove mask

# System state management
systemctl list-units                   # List active units
systemctl list-units --failed          # List failed units only
systemctl list-unit-files              # List all unit files
systemctl list-unit-files --state=enabled  # List enabled units only
systemctl get-default                  # Show default target (runlevel)
systemctl set-default multi-user.target # Set default target
systemctl isolate graphical.target     # Switch to graphical target immediately
```

#### Creating Custom Services

```bash
# Create custom service file: /etc/systemd/system/myapp.service
cat << 'EOF' > /etc/systemd/system/myapp.service
[Unit]
Description=My Application Service
Documentation=https://example.com/docs
After=network.target network-online.target
Wants=network-online.target
Requires=postgresql.service

[Service]
Type=simple
User=myapp
Group=myapp
WorkingDirectory=/opt/myapp
Environment=NODE_ENV=production
Environment=DATABASE_URL=postgresql://user:pass@localhost/myapp
ExecStart=/opt/myapp/bin/start.sh
ExecReload=/bin/kill -HUP $MAINPID
ExecStop=/opt/myapp/bin/stop.sh
Restart=always
RestartSec=10
TimeoutStartSec=300
TimeoutStopSec=30
StandardOutput=journal
StandardError=journal

# Security settings
NoNewPrivileges=true
PrivateTmp=true
PrivateDevices=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/myapp/data /var/log/myapp
ReadOnlyPaths=/etc/myapp
CapabilityBoundingSet=CAP_NET_BIND_SERVICE
AmbientCapabilities=CAP_NET_BIND_SERVICE

# Resource limits
LimitNOFILE=8192
LimitNPROC=4096
MemoryLimit=1G
CPUQuota=150%

[Install]
WantedBy=multi-user.target
EOF

# Service management commands
systemctl daemon-reload                # Reload systemd configuration
systemctl enable myapp                 # Enable service for automatic start
systemctl start myapp                  # Start the service
systemctl status myapp                 # Check service status
```

#### Systemd Unit Types

```bash
# Service units (.service) - Main application services
systemctl status nginx.service         # Web server service
systemctl cat nginx.service            # View service unit file

# Socket units (.socket) - Socket activation
systemctl status docker.socket         # Docker daemon socket
systemctl list-sockets                 # List all socket units

# Target units (.target) - Grouping and dependencies
systemctl status multi-user.target     # Multi-user system state
systemctl list-dependencies graphical.target  # Show target dependencies

# Timer units (.timer) - Scheduled tasks (cron replacement)
systemctl list-timers                  # List active timers
systemctl status backup.timer          # Timer status

# Mount units (.mount) - Filesystem mounts
systemctl status tmp.mount             # Temporary filesystem mount
systemctl list-units --type=mount      # List all mount units

# Path units (.path) - Path-based activation
systemctl status systemd-ask-password-wall.path
systemctl list-units --type=path       # List path units

# Device units (.device) - Hardware devices
systemctl list-units --type=device     # List device units
```

### Systemd Timers (Modern Scheduling)

#### Creating Timer Units

```bash
# Create timer unit: /etc/systemd/system/backup.timer
cat << 'EOF' > /etc/systemd/system/backup.timer
[Unit]
Description=Daily Backup Timer
Documentation=man:systemd.timer(5)
Requires=backup.service

[Timer]
OnCalendar=daily
AccuracySec=1m
Persistent=true
RandomizedDelaySec=300
WakeSystem=false

[Install]
WantedBy=timers.target
EOF

# Create corresponding service: /etc/systemd/system/backup.service
cat << 'EOF' > /etc/systemd/system/backup.service
[Unit]
Description=Daily Backup Service
Documentation=https://company.com/backup-docs
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
User=backup
Group=backup
WorkingDirectory=/opt/backup
ExecStart=/usr/local/bin/backup.sh
StandardOutput=journal
StandardError=journal
TimeoutStartSec=3600
PrivateTmp=true
ProtectSystem=strict
ReadWritePaths=/backup/destination
EOF

# Timer management
systemctl daemon-reload                # Reload systemd configuration
systemctl enable backup.timer          # Enable timer for automatic start
systemctl start backup.timer           # Start timer immediately
systemctl list-timers                  # Verify timer is active
systemctl status backup.timer          # Check timer status
journalctl -u backup.timer             # View timer logs
```

#### Timer Scheduling Syntax

```bash
# OnCalendar scheduling examples

# Predefined shortcuts
OnCalendar=minutely                     # Every minute
OnCalendar=hourly                       # Every hour at minute 0
OnCalendar=daily                        # Every day at 00:00:00
OnCalendar=weekly                       # Every Monday at 00:00:00
OnCalendar=monthly                      # Every first day of month at 00:00:00
OnCalendar=yearly                       # Every January 1st at 00:00:00

# Specific time formats
OnCalendar=*-*-* 02:30:00              # Daily at 2:30 AM
OnCalendar=Mon,Wed,Fri 09:00:00        # Monday, Wednesday, Friday at 9 AM
OnCalendar=*-*-01 00:00:00             # First day of every month at midnight
OnCalendar=*-01-01 06:00:00            # January 1st at 6 AM every year

# Range specifications
OnCalendar=Mon..Fri 09:00:00           # Weekdays at 9 AM
OnCalendar=Sat,Sun 10:00:00            # Weekends at 10 AM
OnCalendar=*-*-* 08:00:00/2:00:00      # Every 2 hours starting at 8 AM

# Multiple schedules (run timer on any matching time)
OnCalendar=Mon..Fri 09:00:00
OnCalendar=Sat,Sun 10:00:00

# Test calendar expressions
systemd-analyze calendar "Mon..Fri 09:00:00"  # Validate expression
systemd-analyze calendar --iterations=10 daily # Show next 10 occurrences
```

### Journal and Logging (journalctl)

#### Basic Journal Operations

```bash
# View logs
journalctl                             # All journal entries
journalctl -f                          # Follow logs in real-time (like tail -f)
journalctl -u nginx                    # Logs for specific service
journalctl -u nginx -f                 # Follow specific service logs
journalctl -u nginx --since "10 minutes ago"  # Recent service logs

# Time-based filtering
journalctl --since "2024-01-01"       # Since specific date
journalctl --since "1 hour ago"       # Since relative time
journalctl --since yesterday           # Since yesterday
journalctl --until "2024-01-31"       # Until specific date
journalctl --since "09:00" --until "17:00"  # During business hours

# Priority filtering (syslog levels)
journalctl -p emerg                    # Emergency messages only
journalctl -p alert                    # Alert level and above
journalctl -p crit                     # Critical level and above
journalctl -p err                      # Error level and above
journalctl -p warning                  # Warning level and above
journalctl -p notice                   # Notice level and above
journalctl -p info                     # Info level and above
journalctl -p debug                    # All messages including debug

# Output formatting
journalctl -o json                     # JSON format
journalctl -o json-pretty              # Pretty-printed JSON
journalctl -o cat                      # Just the message text
journalctl -o short                    # Default short format
journalctl -o verbose                  # All fields
journalctl -o export                   # Binary export format
```

#### Advanced Journal Management

```bash
# Journal maintenance
journalctl --disk-usage                # Show journal disk usage
journalctl --vacuum-size=100M          # Limit journal to 100MB
journalctl --vacuum-time=30d           # Keep logs for 30 days only
journalctl --vacuum-files=10           # Keep only 10 journal files
journalctl --verify                    # Verify journal file integrity
journalctl --rotate                    # Force log rotation

# Boot-specific logs
journalctl -b                          # Current boot logs
journalctl -b -1                       # Previous boot logs
journalctl -b -2                       # Two boots ago
journalctl --list-boots                # List available boots

# Advanced filtering
journalctl _PID=1234                   # Logs from specific process ID
journalctl _COMM=sshd                  # Logs from specific command
journalctl _UID=1000                   # Logs from specific user ID
journalctl PRIORITY=3                  # Logs with specific priority
journalctl -u docker --grep="ERROR"   # Search within service logs
journalctl -S "2024-01-01" -g "failed" # Search for "failed" since date

# Persistent logging configuration (/etc/systemd/journald.conf)
cat << 'EOF' > /etc/systemd/journald.conf
[Journal]
Storage=persistent                     # Store logs persistently on disk
Compress=yes                          # Compress journal files
SystemMaxUse=1G                       # Maximum disk usage for system journal
SystemKeepFree=512M                   # Keep at least this much disk free
SystemMaxFileSize=64M                 # Maximum size per journal file
MaxRetentionSec=30day                 # Maximum retention time
MaxFileSec=1day                       # Maximum time per journal file
ForwardToSyslog=yes                   # Forward to traditional syslog
ForwardToWall=yes                     # Forward to wall messages
RateLimitInterval=30s                 # Rate limiting interval
RateLimitBurst=1000                   # Rate limiting burst
EOF

# Apply journal configuration
systemctl restart systemd-journald
```

### Boot Process Understanding

#### Boot Analysis and Optimization

```bash
# Boot time analysis
systemd-analyze                        # Overall boot time summary
systemd-analyze blame                  # Time taken by each service
systemd-analyze critical-chain         # Critical path analysis
systemd-analyze critical-chain nginx.service  # Critical path for specific service
systemd-analyze plot > boot-chart.svg  # Generate boot timeline chart
systemd-analyze dump > system-state.txt # Complete system state dump

# Service dependency analysis
systemctl list-dependencies nginx      # Show service dependencies
systemctl list-dependencies --reverse nginx  # Show what depends on nginx
systemctl list-dependencies --all      # Show all dependencies recursively
systemctl show nginx --property=After,Before,Wants,Requires

# Boot messages and debugging
dmesg                                  # Kernel ring buffer messages
dmesg | grep -i error                  # Boot-time errors
dmesg -T                               # Human-readable timestamps
journalctl -b                          # Current boot journal
journalctl -b -1                       # Previous boot journal
journalctl -k                          # Kernel messages only
journalctl --since "$(date -d 'today 00:00:00')"  # Today's logs
```

#### Systemd Targets (Runlevels)

```bash
# Target management
systemctl list-units --type=target     # List active targets
systemctl list-unit-files --type=target # List all available targets
systemctl get-default                  # Show default target
systemctl set-default graphical.target # Set default target

# Common systemd targets
# poweroff.target     - System shutdown (runlevel 0)
# rescue.target       - Single-user rescue mode (runlevel 1)
# multi-user.target   - Multi-user text mode (runlevel 3)
# graphical.target    - Multi-user graphical mode (runlevel 5)
# reboot.target       - System reboot (runlevel 6)
# emergency.target    - Emergency shell

# Target operations
systemctl isolate rescue.target        # Switch to rescue mode immediately
systemctl isolate multi-user.target    # Switch to multi-user mode
systemctl rescue                       # Enter rescue mode
systemctl emergency                    # Enter emergency mode (minimal system)
systemctl poweroff                     # Shutdown system
systemctl reboot                       # Restart system
systemctl suspend                      # Suspend to RAM
systemctl hibernate                    # Suspend to disk
```

## System Logging and Troubleshooting

### Log File Management

#### Traditional Log Files

```bash
# Important system log locations
/var/log/messages                      # General system messages (RHEL/CentOS)
/var/log/syslog                        # System log (Debian/Ubuntu)
/var/log/auth.log                      # Authentication logs (Debian/Ubuntu)
/var/log/secure                        # Authentication logs (RHEL/CentOS)
/var/log/kern.log                      # Kernel messages
/var/log/dmesg                         # Boot messages
/var/log/cron                          # Cron job logs
/var/log/mail.log                      # Mail system logs
/var/log/daemon.log                    # System daemon logs
/var/log/user.log                      # User-level logs

# Application-specific logs
/var/log/apache2/                      # Apache web server logs
/var/log/nginx/                        # Nginx web server logs
/var/log/mysql/                        # MySQL database logs
/var/log/postgresql/                   # PostgreSQL database logs
/var/log/docker/                       # Docker daemon logs

# Log analysis commands
tail -f /var/log/syslog                # Follow system log
tail -n 100 /var/log/auth.log          # Last 100 authentication entries
grep "ERROR" /var/log/apache2/error.log # Find errors in Apache log
awk '/ERROR/ {print $1, $2, $NF}' /var/log/syslog # Extract error timestamps
sed -n '/2024-01-01/,/2024-01-02/p' /var/log/messages # Date range extraction
```

#### Log Rotation Management

```bash
# Logrotate configuration
cat /etc/logrotate.conf                # Main logrotate configuration
ls /etc/logrotate.d/                   # Service-specific configurations

# Example logrotate configuration
cat << 'EOF' > /etc/logrotate.d/myapp
/var/log/myapp/*.log {
    daily                              # Rotate daily
    rotate 30                          # Keep 30 days of logs
    compress                           # Compress old logs
    delaycompress                      # Delay compression for one cycle
    missingok                          # OK if log file is missing
    notifempty                         # Don't rotate empty files
    create 0644 myapp myapp            # Create new log with permissions
    postrotate                         # Run after rotation
        systemctl reload myapp
    endscript
}
EOF

# Manual logrotate operations
logrotate -d /etc/logrotate.conf       # Debug mode (dry run)
logrotate -f /etc/logrotate.d/nginx    # Force rotation
logrotate -v /etc/logrotate.conf       # Verbose output
logrotate -s /var/lib/logrotate/status /etc/logrotate.conf # Specify state file
```

### System Performance Analysis

#### Resource Monitoring Tools

```bash
# CPU analysis
top                                    # Traditional process monitor
htop                                   # Enhanced interactive process viewer
atop                                   # Advanced system and process monitor
iotop                                  # I/O usage by process
powertop                               # Power usage analysis

# System statistics
vmstat 5                               # Virtual memory statistics every 5 seconds
iostat -x 1                            # Extended I/O statistics
sar -u 5 12                            # CPU usage every 5 seconds, 12 times
sar -r 5 12                            # Memory usage statistics
sar -d 5 12                            # Disk activity statistics

# Performance profiling
perf top                               # Real-time CPU profiling
perf record -g command                 # Record with call graphs
perf report                            # Analyze recorded performance data
perf stat command                      # Performance counter statistics
```

#### System Information Gathering

```bash
# Hardware information
lscpu                                  # CPU architecture information
lsmem                                  # Memory information
lsblk                                  # Block device information
lspci                                  # PCI device information
lsusb                                  # USB device information
lshw                                   # Complete hardware information
dmidecode                              # Hardware information from BIOS

# System status
uptime                                 # System uptime and load average
who                                    # Currently logged-in users
w                                      # Detailed user activity
last                                   # Login history
lastlog                                # Last login information for all users
df -h                                  # Filesystem disk usage
du -sh /var/*                          # Directory sizes
free -h                                # Memory usage information
```

## DevOps-Specific System Administration

### Container Integration

#### Systemd and Container Services

```bash
# Podman systemd integration
podman generate systemd --name mycontainer --files --new
systemctl --user daemon-reload
systemctl --user enable container-mycontainer.service
systemctl --user start container-mycontainer.service

# Docker with systemd service
cat << 'EOF' > /etc/systemd/system/docker-myapp.service
[Unit]
Description=My Dockerized Application
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=true
ExecStart=/usr/bin/docker run -d --name myapp --restart=unless-stopped \
  -p 8080:8080 \
  -v /opt/myapp/data:/data \
  myapp:latest
ExecStop=/usr/bin/docker stop myapp
ExecStopPost=/usr/bin/docker rm myapp

[Install]
WantedBy=multi-user.target
EOF

# Container health monitoring
systemctl status docker-myapp.service
journalctl -u docker-myapp.service -f
docker logs -f myapp
```

### Configuration Management Integration

#### Ansible Integration

```bash
# System facts gathering
ansible localhost -m setup              # Gather all system facts
ansible localhost -m setup -a 'filter=ansible_memory_mb'  # Specific facts
ansible-playbook -C playbook.yml        # Dry run (check mode)
ansible-vault encrypt_string 'secret' --name 'db_password'  # Encrypt secrets

# Ansible service management playbook example
cat << 'EOF' > service-management.yml
---
- hosts: all
  become: yes
  tasks:
    - name: Ensure nginx is installed
      package:
        name: nginx
        state: present
    
    - name: Start and enable nginx
      systemd:
        name: nginx
        state: started
        enabled: yes
        daemon_reload: yes
    
    - name: Configure firewall for nginx
      firewalld:
        service: http
        permanent: yes
        state: enabled
        immediate: yes
EOF
```

### Monitoring and Observability

#### Prometheus Node Exporter Setup

```bash
# Node exporter service configuration
cat << 'EOF' > /etc/systemd/system/node_exporter.service
[Unit]
Description=Prometheus Node Exporter
After=network.target

[Service]
Type=simple
User=node_exporter
Group=node_exporter
ExecStart=/usr/local/bin/node_exporter \
  --web.listen-address=:9100 \
  --path.procfs=/proc \
  --path.sysfs=/sys \
  --collector.filesystem.ignored-mount-points="^/(sys|proc|dev|host|etc)($|/)"
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# Service management
systemctl enable node_exporter
systemctl start node_exporter
curl http://localhost:9100/metrics       # Verify metrics endpoint

# Custom metrics collection
mkdir -p /var/lib/node_exporter/textfile_collector
echo 'custom_metric{type="gauge"} 42' > /var/lib/node_exporter/textfile_collector/custom.prom
```

#### Log Aggregation Configuration

```bash
# Rsyslog for centralized logging
cat << 'EOF' >> /etc/rsyslog.conf
# Forward all logs to central server
*.* @@logserver.example.com:514

# Local log filtering
local0.info     /var/log/myapp.log
local0.warn     /var/log/myapp-warnings.log
& stop
EOF

# Restart rsyslog
systemctl restart rsyslog

# Journald forwarding to remote syslog
cat << 'EOF' >> /etc/systemd/journald.conf
[Journal]
ForwardToSyslog=yes
MaxLevelStore=info
MaxLevelSyslog=debug
EOF

systemctl restart systemd-journald
```

### Security Hardening

#### System Security Configuration

```bash
# SSH hardening configuration
cat << 'EOF' >> /etc/ssh/sshd_config
# Security hardening
Protocol 2
MaxAuthTries 3
LoginGraceTime 60
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
MaxStartups 3:30:10
AllowGroups sshusers
ClientAliveInterval 300
ClientAliveCountMax 2
EOF

# Firewall configuration
systemctl enable firewalld
firewall-cmd --set-default-zone=public
firewall-cmd --add-service=ssh --permanent
firewall-cmd --add-service=http --permanent
firewall-cmd --add-service=https --permanent
firewall-cmd --reload

# Security limits
cat << 'EOF' >> /etc/security/limits.conf
# Security limits
* hard core 0                          # Disable core dumps
* soft nproc 4096                      # Process limits
* hard nproc 8192
* soft nofile 8192                     # File descriptor limits
* hard nofile 16384
EOF

# Kernel security parameters
cat << 'EOF' > /etc/sysctl.d/99-security.conf
# Network security
net.ipv4.conf.all.send_redirects = 0
net.ipv4.conf.default.send_redirects = 0
net.ipv4.conf.all.accept_redirects = 0
net.ipv4.conf.default.accept_redirects = 0
net.ipv4.conf.all.accept_source_route = 0
net.ipv4.conf.default.accept_source_route = 0
net.ipv4.icmp_echo_ignore_broadcasts = 1
net.ipv4.ip_forward = 0

# System security
kernel.dmesg_restrict = 1
kernel.kptr_restrict = 2
kernel.yama.ptrace_scope = 1
EOF

sysctl --system                        # Apply security settings
```

This comprehensive system administration guide covers essential Linux system management tasks, from service management and logging to monitoring and security hardening, specifically tailored for DevOps environments.