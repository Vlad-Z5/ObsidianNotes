# Linux Systemd Targets

**Systemd targets** are special unit types that group other units together, similar to runlevels in traditional init systems, providing system state management and boot process control.

## Understanding Targets

Targets define system states and group related services together:
- Emergency shell access
- Single-user rescue mode
- Multi-user non-graphical mode
- Full graphical desktop mode
- System shutdown and reboot

## Common System Targets

```bash
# Default system targets
emergency.target      # Emergency shell (minimal system)
rescue.target         # Rescue mode (single user)
multi-user.target     # Multi-user mode (no GUI)
graphical.target      # Graphical mode (full desktop)
reboot.target         # System reboot
poweroff.target       # System shutdown
halt.target           # System halt
```

## Target Operations

```bash
# View current target
systemctl get-default
systemctl list-units --type=target

# Change default target
systemctl set-default multi-user.target
systemctl set-default graphical.target

# Switch to target immediately
systemctl isolate rescue.target
systemctl isolate multi-user.target
systemctl isolate graphical.target

# List all available targets
systemctl list-unit-files --type=target
systemctl list-units --type=target --all
```

## Target Dependencies

```bash
# Show target dependencies
systemctl list-dependencies graphical.target
systemctl list-dependencies multi-user.target --reverse

# Analyze target structure
systemctl show graphical.target --property=Wants
systemctl show graphical.target --property=Requires
systemctl show graphical.target --property=After
```

## Custom Target Creation

```bash
# Create custom application target
# /etc/systemd/system/myapp.target
[Unit]
Description=My Application Stack
Documentation=https://company.com/docs/deployment
Requires=multi-user.target
After=multi-user.target
AllowIsolate=yes
Conflicts=shutdown.target

[Install]
WantedBy=multi-user.target
```

### Custom Target Usage

```bash
# Enable custom target
systemctl enable myapp.target

# Services that belong to custom target
# Add to service files: WantedBy=myapp.target

# Switch to custom target
systemctl isolate myapp.target
```

## Boot Process Analysis

```bash
# Overall boot performance
systemd-analyze
systemd-analyze time

# Service startup times
systemd-analyze blame

# Critical path analysis
systemd-analyze critical-chain
systemd-analyze critical-chain multi-user.target

# Visual boot chart
systemd-analyze plot > boot.svg
systemd-analyze plot --no-pager > boot.svg

# Target verification
systemd-analyze verify multi-user.target
```

## Special Targets

### Network Targets
```bash
# Network-related targets
network.target           # Basic network setup
network-online.target    # Network is fully configured
network-pre.target       # Before network setup
```

### System State Targets
```bash
# System state targets
sysinit.target          # System initialization
basic.target            # Basic system services
local-fs.target         # Local filesystems mounted
remote-fs.target        # Remote filesystems mounted
swap.target             # Swap devices activated
time-sync.target        # Time synchronization
```

### Service Group Targets
```bash
# Service grouping targets
sockets.target          # All socket units
timers.target           # All timer units
paths.target            # All path units
slices.target           # All slice units
```

## Target Configuration Examples

### Development Environment Target
```bash
# /etc/systemd/system/dev-environment.target
[Unit]
Description=Development Environment
Documentation=man:systemd.special(7)
Requires=multi-user.target
After=multi-user.target
AllowIsolate=yes

[Install]
WantedBy=multi-user.target
```

### Production Stack Target
```bash
# /etc/systemd/system/production.target
[Unit]
Description=Production Application Stack
Requires=multi-user.target
After=multi-user.target
Wants=nginx.service postgresql.service redis.service
AllowIsolate=yes

[Install]
WantedBy=multi-user.target
```

## Target Management Scripts

### Switch Target Script
```bash
#!/bin/bash
# switch-target.sh

TARGET="$1"

if [ -z "$TARGET" ]; then
    echo "Usage: $0 <target>"
    echo "Available targets:"
    systemctl list-unit-files --type=target --state=enabled
    exit 1
fi

echo "Switching to target: $TARGET"
systemctl isolate "$TARGET"

echo "Current target status:"
systemctl list-units --type=target --state=active
```

### Target Status Check
```bash
#!/bin/bash
# target-status.sh

echo "=== Current System Target Status ==="
echo "Default target: $(systemctl get-default)"
echo "Active targets:"
systemctl list-units --type=target --state=active --no-pager

echo -e "\n=== Target Dependencies ==="
CURRENT_TARGET=$(systemctl get-default)
systemctl list-dependencies "$CURRENT_TARGET" --no-pager

echo -e "\n=== Failed Units ==="
systemctl --failed --no-pager
```

## Boot Target Customization

```bash
# Create custom boot sequence
mkdir -p /etc/systemd/system/custom-boot.target.wants/

# Link services to custom target
ln -s /etc/systemd/system/myservice.service \
      /etc/systemd/system/custom-boot.target.wants/

# Set as default
systemctl set-default custom-boot.target
```

## Target Isolation

```bash
# Safe target switching
systemctl list-jobs                    # Check running jobs
systemctl isolate --no-block rescue.target  # Non-blocking switch

# Emergency target access
systemctl emergency                     # Switch to emergency target
systemctl default                      # Return to default target
```

## Target Debugging

```bash
# Debug target issues
systemctl status multi-user.target
journalctl -u multi-user.target

# Check target conflicts
systemctl show multi-user.target --property=Conflicts

# Verify target configuration
systemd-analyze verify /etc/systemd/system/custom.target
```

## Production Target Practices

```bash
# Minimal production target
[Unit]
Description=Production Services Only
Requires=basic.target
After=basic.target
Wants=network-online.target
After=network-online.target

# Security-focused target
Conflicts=rescue.target emergency.target
AllowIsolate=no

[Install]
WantedBy=multi-user.target
```