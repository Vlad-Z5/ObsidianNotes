# Linux Systemd Unit Files

**Systemd unit files** define how services, mounts, devices, and other system resources are configured and managed.

## Unit File Structure

```bash
# Basic unit file structure
[Unit]          # Metadata and dependencies
[Service]       # Service-specific configuration
[Install]       # Installation information
```

## Unit File Locations

```bash
# Priority order (highest to lowest)
/etc/systemd/system/          # Administrator unit files
/run/systemd/system/          # Runtime unit files
/usr/lib/systemd/system/      # Distribution unit files
/lib/systemd/system/          # Distribution unit files (symlink)

# User unit files
~/.config/systemd/user/       # User-specific units
/etc/systemd/user/            # System-wide user units
/usr/lib/systemd/user/        # Distribution user units
```

## Basic Service Unit File

```bash
# /etc/systemd/system/myapp.service
[Unit]
Description=My Application
Documentation=https://example.com/docs
Wants=network-online.target
After=network-online.target

[Service]
Type=simple
User=myapp
Group=myapp
WorkingDirectory=/opt/myapp
ExecStart=/opt/myapp/bin/myapp
ExecReload=/bin/kill -HUP $MAINPID
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

## [Unit] Section Options

```bash
# Basic information
Description=Brief description of the unit
Documentation=URL or man page reference
Wants=network-online.target           # Soft dependency
Requires=database.service             # Hard dependency
After=network.target database.service # Start order
Before=web-frontend.service           # Start before others

# Conflict resolution
Conflicts=apache2.service             # Cannot run together
BindsTo=device.mount                  # Stop if dependency stops

# Conditions
ConditionPathExists=/etc/myapp/config
ConditionFileNotEmpty=/etc/myapp/license
ConditionHost=production-server
```

## [Service] Section Options

### Service Types
```bash
Type=simple      # Default, process started by ExecStart is main process
Type=exec        # Like simple, but systemd waits for exec() call
Type=forking     # Process forks and parent exits
Type=oneshot     # Process exits after completion
Type=dbus        # Service acquires D-Bus name
Type=notify      # Service sends notification when ready
Type=notify-reload # Like notify, with reload support
Type=idle        # Wait until all jobs are dispatched
```

### Execution Options
```bash
# Main execution
ExecStart=/usr/bin/myapp --config /etc/myapp.conf
ExecStartPre=/usr/bin/myapp-setup      # Run before start
ExecStartPost=/usr/bin/myapp-post      # Run after start
ExecReload=/bin/kill -HUP $MAINPID     # Reload command
ExecStop=/usr/bin/myapp-stop           # Stop command
ExecStopPost=/usr/bin/myapp-cleanup    # Run after stop

# Process control
PIDFile=/var/run/myapp.pid
RemainAfterExit=yes                    # For Type=oneshot
TimeoutStartSec=60                     # Start timeout
TimeoutStopSec=30                      # Stop timeout
```

### User and Permissions
```bash
User=myapp                            # Run as user
Group=myapp                           # Run as group
DynamicUser=yes                       # Create temporary user
SupplementaryGroups=docker,audio      # Additional groups

# Security options
NoNewPrivileges=yes                   # Prevent privilege escalation
PrivateTmp=yes                        # Private /tmp directory
ProtectSystem=strict                  # Read-only filesystem
ProtectHome=yes                       # No access to /home
```

### Restart Behavior
```bash
Restart=no           # Never restart (default)
Restart=always       # Always restart
Restart=on-success   # Restart on clean exit
Restart=on-failure   # Restart on failure
Restart=on-abnormal  # Restart on abnormal exit
Restart=on-abort     # Restart on abort signal
Restart=on-watchdog  # Restart on watchdog timeout

RestartSec=5         # Wait 5 seconds before restart
StartLimitBurst=3    # Max 3 restart attempts
StartLimitIntervalSec=300  # In 5 minute window
```

## Advanced Service Examples

### Web Application Service
```bash
# /etc/systemd/system/webapp.service
[Unit]
Description=Web Application
After=network-online.target postgresql.service
Wants=network-online.target
Requires=postgresql.service

[Service]
Type=simple
User=webapp
Group=webapp
WorkingDirectory=/opt/webapp
Environment=NODE_ENV=production
Environment=PORT=3000
ExecStart=/usr/bin/node server.js
ExecReload=/bin/kill -USR1 $MAINPID
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

# Security hardening
NoNewPrivileges=yes
PrivateTmp=yes
ProtectSystem=strict
ProtectHome=yes
ReadWritePaths=/opt/webapp/logs /opt/webapp/uploads

[Install]
WantedBy=multi-user.target
```

### Database Service
```bash
# /etc/systemd/system/mydb.service
[Unit]
Description=My Database Service
After=network.target

[Service]
Type=forking
User=postgres
Group=postgres
WorkingDirectory=/var/lib/postgresql
ExecStart=/usr/bin/pg_ctl start -D /var/lib/postgresql/data -l /var/log/postgresql/postgresql.log
ExecReload=/usr/bin/pg_ctl reload -D /var/lib/postgresql/data
ExecStop=/usr/bin/pg_ctl stop -D /var/lib/postgresql/data -m fast
PIDFile=/var/lib/postgresql/data/postmaster.pid
TimeoutSec=300

[Install]
WantedBy=multi-user.target
```

## Resource Management

```bash
# Memory limits
MemoryAccounting=yes
MemoryMax=1G
MemoryHigh=800M

# CPU limits
CPUAccounting=yes
CPUQuota=50%                          # 50% of one CPU
CPUShares=1024                        # Relative weight

# I/O limits
IOAccounting=yes
IOWeight=100                          # I/O weight (1-10000)

# Process limits
TasksAccounting=yes
TasksMax=100                          # Max processes/threads
```

## [Install] Section

```bash
# Installation targets
WantedBy=multi-user.target           # Default runlevel
WantedBy=graphical.target            # GUI environment
RequiredBy=network.target            # Hard dependency

# Aliases
Alias=myapp.service                  # Alternative name
Also=myapp-helper.service            # Enable together
```

## Creating Custom Unit Files

```bash
# Create new service file
sudo vim /etc/systemd/system/myservice.service

# Reload systemd to recognize new file
sudo systemctl daemon-reload

# Enable and start service
sudo systemctl enable myservice
sudo systemctl start myservice

# Check status
systemctl status myservice
```

## Unit File Templates

### Template Service
```bash
# /etc/systemd/system/myapp@.service
[Unit]
Description=My App Instance %i
After=network.target

[Service]
Type=simple
User=myapp
ExecStart=/usr/bin/myapp --instance %i --config /etc/myapp/%i.conf
Restart=always

[Install]
WantedBy=multi-user.target
```

### Using Templates
```bash
# Start specific instances
systemctl start myapp@web
systemctl start myapp@api
systemctl enable myapp@web

# List template instances
systemctl list-units | grep myapp@
```

## Drop-in Directories

```bash
# Override specific settings without editing main file
mkdir -p /etc/systemd/system/nginx.service.d/

# Create override file
cat > /etc/systemd/system/nginx.service.d/override.conf <<EOF
[Service]
Restart=always
RestartSec=10
EOF

# Reload configuration
systemctl daemon-reload
systemctl restart nginx
```

## Validation and Testing

```bash
# Check unit file syntax
systemd-analyze verify myservice.service

# View effective configuration
systemctl cat myservice

# Test service start (dry run)
systemctl --dry-run start myservice

# Show all properties
systemctl show myservice
```

## Common Patterns

### Oneshot Service
```bash
[Unit]
Description=One-time Setup Task

[Service]
Type=oneshot
ExecStart=/usr/local/bin/setup-script.sh
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
```

### Socket-Activated Service
```bash
# myapp.socket
[Unit]
Description=My App Socket

[Socket]
ListenStream=8080
Accept=false

[Install]
WantedBy=sockets.target

# myapp.service
[Unit]
Description=My App Service

[Service]
Type=simple
ExecStart=/usr/bin/myapp
```