# Linux Systemd Service Management

**Systemd service management** provides comprehensive control over system services including starting, stopping, enabling, and monitoring services.

## Basic Service Operations

```bash
# Check service status
systemctl status nginx
systemctl is-active nginx       # Just active/inactive
systemctl is-enabled nginx      # Just enabled/disabled
systemctl is-failed nginx       # Just failed/not failed

# Start and stop services
systemctl start nginx
systemctl stop nginx
systemctl restart nginx
systemctl reload nginx          # Reload config without restart

# Enable and disable services
systemctl enable nginx          # Start at boot
systemctl disable nginx         # Don't start at boot
systemctl enable --now nginx    # Enable and start immediately
systemctl disable --now nginx   # Disable and stop immediately
```

## Advanced Service Control

```bash
# Mask and unmask services (prevent starting)
systemctl mask nginx            # Completely disable service
systemctl unmask nginx          # Remove mask

# Reload systemd configuration
systemctl daemon-reload         # Reload unit files

# Reset failed services
systemctl reset-failed
systemctl reset-failed nginx    # Reset specific service

# Kill services
systemctl kill nginx            # Send SIGTERM
systemctl kill -s KILL nginx    # Send SIGKILL
```

## Listing and Searching Services

```bash
# List all services
systemctl list-units --type=service
systemctl list-units --type=service --state=active
systemctl list-units --type=service --state=failed

# List unit files
systemctl list-unit-files --type=service
systemctl list-unit-files --type=service --state=enabled

# Search for services
systemctl list-units | grep nginx
systemctl status "*ssh*"
```

## Service Dependencies

```bash
# Show service dependencies
systemctl list-dependencies nginx
systemctl list-dependencies --reverse nginx    # What depends on nginx

# Show dependency tree
systemctl list-dependencies --all nginx

# Check what services are needed
systemctl show nginx -p Requires
systemctl show nginx -p Wants
systemctl show nginx -p After
systemctl show nginx -p Before
```

## Service Properties

```bash
# Show all service properties
systemctl show nginx

# Show specific properties
systemctl show nginx -p ActiveState
systemctl show nginx -p SubState
systemctl show nginx -p MainPID
systemctl show nginx -p ExecStart

# Show service environment
systemctl show-environment
```

## Monitoring Services

```bash
# Monitor service logs
journalctl -u nginx -f          # Follow logs
journalctl -u nginx --since today
journalctl -u nginx -n 50       # Last 50 lines

# Check service resource usage
systemctl status nginx          # Basic resource info
systemd-cgtop                   # Top-like view of cgroups

# Monitor multiple services
systemctl status nginx apache2 mysql
```

## Service Troubleshooting

```bash
# Check why service failed
systemctl status nginx
systemctl show nginx -p Result
journalctl -u nginx --since "5 minutes ago"

# Verify service files
systemctl cat nginx
systemd-analyze verify nginx.service

# Check service conflicts
systemctl list-dependencies --reverse nginx
```

## User Services

```bash
# User service management (no sudo needed)
systemctl --user status myapp
systemctl --user start myapp
systemctl --user enable myapp

# Enable user services to start at boot
sudo loginctl enable-linger username

# List user services
systemctl --user list-units --type=service
```

## Service Templates

```bash
# Work with templated services
systemctl start getty@tty3       # Start getty on tty3
systemctl enable nginx@ssl       # Enable nginx SSL template

# List template instances
systemctl list-units | grep @
```

## Bulk Operations

```bash
# Start multiple services
systemctl start nginx apache2 mysql

# Stop all user services
systemctl --user stop --all

# Restart all failed services
systemctl reset-failed
systemctl restart $(systemctl list-units --failed --plain | awk '{print $1}')

# Disable all Apache modules
systemctl disable apache2@*
```

## Service Performance

```bash
# Analyze service startup time
systemd-analyze blame
systemd-analyze critical-chain nginx.service

# Show service startup time
systemctl show nginx -p ExecMainStartTimestamp
systemctl show nginx -p ExecMainExitTimestamp
```

## Emergency Service Control

```bash
# Emergency stop (kill all processes)
systemctl kill --kill-who=all nginx

# Force immediate stop
systemctl stop nginx &
sleep 5
systemctl kill -s KILL nginx

# Rescue mode (single user)
systemctl rescue

# Emergency mode (minimal environment)
systemctl emergency
```

## Automation Scripts

```bash
#!/bin/bash
# Service health check script

SERVICE="nginx"

if systemctl is-active "$SERVICE" >/dev/null 2>&1; then
    echo "$SERVICE is running"
else
    echo "$SERVICE is not running, attempting to start..."
    systemctl start "$SERVICE"

    if systemctl is-active "$SERVICE" >/dev/null 2>&1; then
        echo "$SERVICE started successfully"
    else
        echo "$SERVICE failed to start"
        systemctl status "$SERVICE"
        exit 1
    fi
fi
```

## Common Service Patterns

```bash
# Web server management
systemctl enable --now nginx
systemctl reload nginx          # Graceful config reload

# Database management
systemctl start mysql
systemctl status mysql
journalctl -u mysql -f

# Network services
systemctl restart NetworkManager
systemctl status sshd

# Development services
systemctl --user start docker-desktop
systemctl --user enable code-server
```

## Service Configuration Check

```bash
# Validate service configuration
systemctl cat nginx
systemd-analyze verify /etc/systemd/system/nginx.service

# Check syntax errors
systemctl daemon-reload 2>&1 | grep error

# Test service start (dry run)
systemctl --dry-run start nginx
```