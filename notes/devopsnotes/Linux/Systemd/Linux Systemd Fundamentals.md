# Linux Systemd Fundamentals

**Systemd** is the modern init system and service manager for Linux, providing parallel service startup, dependency management, and comprehensive system control.

## What is Systemd?

Systemd is the first process (PID 1) that starts during boot and manages all other processes. It replaces traditional init systems like SysV init.

**Key Features:**
- Parallel service startup (faster boot)
- Dependency-based service management
- Socket and D-Bus activation
- Comprehensive logging with journald
- Resource management and cgroups
- Timer-based scheduling

## Core Components

```bash
# Main systemd components
systemd          # Main system and service manager (PID 1)
systemctl        # Primary tool for controlling systemd
journald         # Centralized logging service
logind           # Login and session management
networkd         # Network configuration management
resolved         # DNS resolution service
udevd            # Device manager
```

## Systemd Unit Types

```bash
# Unit types and their purposes
.service     # System services (daemons)
.socket      # Network or IPC sockets
.mount       # Filesystem mount points
.target      # Groups of units (like runlevels)
.timer       # Scheduled tasks (cron alternative)
.path        # Path-based activation
.device      # Device files
.swap        # Swap files/partitions
.slice       # Resource management groups
.scope       # Externally created processes
```

## Directory Structure

```bash
# Systemd directories (priority order)
/etc/systemd/system/          # Local unit files (highest priority)
/run/systemd/system/          # Runtime unit files
/usr/lib/systemd/system/      # Distribution unit files
/lib/systemd/system/          # Distribution unit files (symlink)

# Configuration directories
/etc/systemd/system.conf      # Main systemd configuration
/etc/systemd/user.conf        # User session configuration
/etc/systemd/logind.conf      # Login manager configuration
/etc/systemd/journald.conf    # Journal configuration
```

## Basic Commands

```bash
# System status
systemctl status              # Overall system status
systemctl --version           # Systemd version
systemctl list-units          # List all loaded units
systemctl list-unit-files     # List all unit files

# System control
systemctl reboot              # Restart system
systemctl poweroff            # Shutdown system
systemctl suspend             # Suspend system
systemctl hibernate           # Hibernate system
```

## Service States

```bash
# Service states explained
active (running)    # Service is running
active (exited)     # Service completed successfully
active (waiting)    # Service is waiting for an event
inactive (dead)     # Service is stopped
failed             # Service failed to start/run

# Enable states
enabled            # Service will start at boot
disabled           # Service will not start at boot
static             # Service cannot be enabled (dependency only)
masked             # Service is completely disabled
```

## Quick Status Check

```bash
# Check systemd status
systemctl status

# Check failed services
systemctl --failed

# Check boot time
systemd-analyze

# Check service dependencies
systemctl list-dependencies
```

## Systemd vs Traditional Init

| Feature | SysV Init | Systemd |
|---------|-----------|---------|
| Startup | Sequential | Parallel |
| Configuration | Shell scripts | Unit files |
| Logging | Separate tools | Integrated journald |
| Dependencies | Manual | Automatic |
| Resource Control | Limited | Full cgroups |
| Socket Activation | No | Yes |

## Essential Files

```bash
# Key systemd files to know
/etc/systemd/system.conf           # Main configuration
/proc/1/cmdline                    # Verify systemd is PID 1
/sys/fs/cgroup/                    # Control groups
/run/systemd/                      # Runtime state
/var/lib/systemd/                  # Persistent state
```