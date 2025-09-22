# Linux Systemd Advanced Features

**Systemd advanced features** include socket activation, path-based activation, user services, service templates, and sophisticated activation mechanisms for modern system architecture.

## Socket Activation

### Socket Unit Configuration
```bash
# /etc/systemd/system/myapp.socket
[Unit]
Description=My Application Socket
Documentation=https://company.com/docs/socket
PartOf=myapp.service

[Socket]
ListenStream=8080              # TCP socket
ListenDatagram=8081            # UDP socket
ListenFIFO=/run/myapp.fifo     # Named pipe
ListenSpecial=/dev/log         # Special file
ListenNetlink=audit 1          # Netlink socket

# Socket behavior
Accept=false                   # Single service handles all connections
SocketUser=myapp
SocketGroup=myapp
SocketMode=0660
Backlog=256
KeepAlive=true
NoDelay=true

[Install]
WantedBy=sockets.target
```

### Socket Service Integration
```bash
# /etc/systemd/system/myapp.service
[Unit]
Description=My Application Service
Documentation=https://company.com/docs/myapp
Requires=myapp.socket

[Service]
Type=notify
ExecStart=/usr/local/bin/myapp --systemd-socket
StandardInput=socket
User=myapp
Group=myapp
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

### Multi-Socket Services
```bash
# /etc/systemd/system/web-server.socket
[Unit]
Description=Web Server Socket

[Socket]
ListenStream=80
ListenStream=443
ListenStream=[::]:80
ListenStream=[::]:443
ReusePort=true
FreeBind=true

[Install]
WantedBy=sockets.target
```

### Socket Activation Benefits
```bash
# Enable socket without starting service
systemctl enable --now myapp.socket

# Service starts automatically on first connection
# Zero-downtime restarts
systemctl restart myapp.service  # Socket stays active

# Check socket status
systemctl status myapp.socket
ss -tulpn | grep 8080
```

## Path-Based Activation

### Path Unit Configuration
```bash
# /etc/systemd/system/config-watcher.path
[Unit]
Description=Configuration File Watcher
Documentation=https://company.com/docs/config

[Path]
# Path monitoring options
PathExists=/etc/myapp/config.yml       # Trigger when path exists
PathExistsGlob=/etc/myapp/*.conf       # Glob pattern matching
PathChanged=/etc/myapp/                # Directory contents changed
PathModified=/etc/myapp/config.yml     # File content modified
DirectoryNotEmpty=/var/spool/myapp     # Directory has files

# Path behavior
Unit=config-reload.service             # Service to activate
MakeDirectory=true                     # Create directory if missing

[Install]
WantedBy=multi-user.target
```

### Path-Triggered Service
```bash
# /etc/systemd/system/config-reload.service
[Unit]
Description=Reload Configuration
Documentation=https://company.com/docs/config

[Service]
Type=oneshot
ExecStart=/usr/local/bin/reload-config.sh
User=myapp
Group=myapp
StandardOutput=journal
StandardError=journal
```

### File Processing Example
```bash
# /etc/systemd/system/file-processor.path
[Unit]
Description=File Processor Watcher

[Path]
DirectoryNotEmpty=/var/spool/incoming
Unit=process-files.service

[Install]
WantedBy=multi-user.target

# /etc/systemd/system/process-files.service
[Unit]
Description=Process Incoming Files

[Service]
Type=oneshot
ExecStart=/usr/local/bin/process-files.sh
User=processor
Group=processor
RemainAfterExit=false
```

## Service Templates

### Template Unit Files
```bash
# /etc/systemd/system/worker@.service
[Unit]
Description=Worker Instance %i
Documentation=https://company.com/docs/worker
After=network.target

[Service]
Type=simple
ExecStart=/usr/local/bin/worker --instance %i --config /etc/worker/%i.conf
Restart=always
RestartSec=5
User=worker
Group=worker

# Instance-specific configuration
Environment=INSTANCE_NAME=%i
Environment=INSTANCE_ID=%i
WorkingDirectory=/var/lib/worker/%i
StandardOutput=journal
StandardError=journal
SyslogIdentifier=worker-%i

[Install]
WantedBy=multi-user.target
```

### Template Instance Management
```bash
# Start specific instances
systemctl start worker@web.service
systemctl start worker@api.service
systemctl start worker@queue.service

# Enable instances
systemctl enable worker@web.service
systemctl enable worker@api.service

# Manage all instances
systemctl start worker@{web,api,queue}.service
systemctl status "worker@*"
systemctl stop "worker@*"

# List template instances
systemctl list-units | grep "worker@"
systemctl list-units "worker@*"
```

### Advanced Template Examples
```bash
# Database instance template
# /etc/systemd/system/database@.service
[Unit]
Description=Database Instance %i
After=network.target

[Service]
Type=notify
ExecStart=/usr/bin/database-server --port %i --data-dir /var/lib/db/%i
User=database
Group=database
Environment=DB_INSTANCE=%i
Environment=DB_PORT=%i

# Load balancer backend template
# /etc/systemd/system/backend@.service
[Unit]
Description=Backend Server %i
PartOf=loadbalancer.service

[Service]
Type=simple
ExecStart=/usr/local/bin/backend --instance %i
User=backend
Group=backend
Environment=BACKEND_ID=%i
```

## User Services

### User Service Directory
```bash
# User service locations
~/.config/systemd/user/           # User-specific services
/etc/systemd/user/                # System-wide user services
/usr/lib/systemd/user/            # Distribution user services

# Enable user service lingering
sudo loginctl enable-linger username
```

### User Service Example
```bash
# ~/.config/systemd/user/myapp.service
[Unit]
Description=My User Application
After=graphical-session.target

[Service]
Type=simple
ExecStart=/home/user/bin/myapp
Restart=always
RestartSec=10
Environment=HOME=%h
Environment=USER=%i

[Install]
WantedBy=default.target
```

### User Service Management
```bash
# User service commands (no sudo)
systemctl --user status myapp
systemctl --user start myapp
systemctl --user enable myapp
systemctl --user stop myapp

# User environment
systemctl --user import-environment PATH
systemctl --user set-environment VAR=value
systemctl --user show-environment

# User session management
loginctl list-sessions
loginctl show-session session_id
loginctl enable-linger username
```

### User Service with Timer
```bash
# ~/.config/systemd/user/backup.timer
[Unit]
Description=User Backup Timer

[Timer]
OnCalendar=daily
Persistent=true

[Install]
WantedBy=timers.target

# ~/.config/systemd/user/backup.service
[Unit]
Description=User Backup Service

[Service]
Type=oneshot
ExecStart=/home/user/bin/backup.sh
```

## Device-Based Activation

### Device Unit Configuration
```bash
# /etc/systemd/system/usb-handler@.service
[Unit]
Description=USB Device Handler for %i
BindsTo=dev-%i.device
After=dev-%i.device

[Service]
Type=oneshot
ExecStart=/usr/local/bin/handle-usb-device.sh %i
RemainAfterExit=true

[Install]
WantedBy=multi-user.target
```

### Udev Integration
```bash
# /etc/udev/rules.d/99-usb-handler.rules
ACTION=="add", SUBSYSTEM=="usb", ENV{ID_VENDOR}=="1234", \
TAG+="systemd", ENV{SYSTEMD_WANTS}="usb-handler@$env{DEVNAME}.service"
```

## D-Bus Activation

### D-Bus Service Configuration
```bash
# /etc/systemd/system/dbus-service.service
[Unit]
Description=D-Bus Activated Service
Requires=dbus.socket

[Service]
Type=dbus
BusName=com.company.MyService
ExecStart=/usr/local/bin/my-dbus-service
User=myservice
Group=myservice

[Install]
WantedBy=multi-user.target
```

### D-Bus Service File
```bash
# /usr/share/dbus-1/system-services/com.company.MyService.service
[D-BUS Service]
Name=com.company.MyService
Exec=/usr/local/bin/my-dbus-service
User=myservice
SystemdService=dbus-service.service
```

## Container Integration

### Container Service Template
```bash
# /etc/systemd/system/container@.service
[Unit]
Description=Container %i
Requires=docker.service
After=docker.service
StopWhenUnneeded=true

[Service]
Type=notify
NotifyAccess=all
ExecStart=/usr/bin/docker run --rm --name %i \
  --label=managed-by=systemd \
  --pull=always \
  myregistry/myapp:%i
ExecStop=/usr/bin/docker stop %i
ExecStopPost=/usr/bin/docker rm -f %i
TimeoutStartSec=300
TimeoutStopSec=30
Restart=always

[Install]
WantedBy=multi-user.target
```

### Pod Management
```bash
# /etc/systemd/system/pod@.service
[Unit]
Description=Pod %i
Requires=podman.socket
After=podman.socket

[Service]
Type=notify
NotifyAccess=all
ExecStart=/usr/bin/podman play kube /etc/pods/%i.yaml
ExecStop=/usr/bin/podman pod stop %i
ExecStopPost=/usr/bin/podman pod rm -f %i
PIDFile=/run/pods/%i.pid
KillMode=mixed
TimeoutStopSec=70

[Install]
WantedBy=multi-user.target
```

## Network Namespace Services

### Network Namespace Service
```bash
# /etc/systemd/system/netns@.service
[Unit]
Description=Network Namespace %i
StopWhenUnneeded=true

[Service]
Type=oneshot
RemainAfterExit=true
ExecStart=/bin/ip netns add %i
ExecStart=/bin/ip netns exec %i ip link set lo up
ExecStop=/bin/ip netns delete %i
PrivateNetwork=true

[Install]
WantedBy=multi-user.target
```

### Service in Network Namespace
```bash
# /etc/systemd/system/app-isolated.service
[Unit]
Description=Isolated Application
Requires=netns@isolated.service
After=netns@isolated.service
BindsTo=netns@isolated.service

[Service]
Type=simple
ExecStart=/usr/bin/ip netns exec isolated /usr/local/bin/myapp
User=myapp
Group=myapp
PrivateNetwork=true

[Install]
WantedBy=multi-user.target
```

## Advanced Service Monitoring

### Service Health Check
```bash
# /etc/systemd/system/app-with-health.service
[Unit]
Description=Application with Health Check
StartLimitBurst=5
StartLimitIntervalSec=30

[Service]
Type=notify
ExecStart=/usr/local/bin/myapp
ExecStartPost=/usr/local/bin/health-check.sh
ExecReload=/bin/kill -USR1 $MAINPID
Restart=always
RestartSec=5
WatchdogSec=30
NotifyAccess=main

[Install]
WantedBy=multi-user.target
```

### Service Dependency Graph
```bash
#!/bin/bash
# service-graph.sh

SERVICE="$1"

# Generate dependency graph
systemd-analyze dot "$SERVICE" | \
dot -Tsvg -o "/tmp/${SERVICE}-deps.svg"

echo "Dependency graph saved to /tmp/${SERVICE}-deps.svg"

# Generate reverse dependency graph
systemd-analyze dot "$SERVICE" --to-pattern="$SERVICE" | \
dot -Tsvg -o "/tmp/${SERVICE}-reverse-deps.svg"
```

## Production Advanced Patterns

### Blue-Green Deployment Service
```bash
# /etc/systemd/system/app-blue.service
[Unit]
Description=Application Blue Instance
Conflicts=app-green.service

[Service]
Type=simple
ExecStart=/usr/local/bin/myapp --config /etc/myapp/blue.conf
User=myapp
Group=myapp
Environment=INSTANCE=blue

# /etc/systemd/system/app-green.service
[Unit]
Description=Application Green Instance
Conflicts=app-blue.service

[Service]
Type=simple
ExecStart=/usr/local/bin/myapp --config /etc/myapp/green.conf
User=myapp
Group=myapp
Environment=INSTANCE=green
```

### Circuit Breaker Pattern
```bash
# /etc/systemd/system/circuit-breaker.service
[Unit]
Description=Service with Circuit Breaker
StartLimitBurst=3
StartLimitIntervalSec=60

[Service]
Type=simple
ExecStart=/usr/local/bin/app-with-circuit-breaker
ExecStartPre=/usr/local/bin/check-dependencies.sh
Restart=on-failure
RestartSec=30
TimeoutStartSec=60
WatchdogSec=30

[Install]
WantedBy=multi-user.target
```