# Linux Logging Architecture

**Linux logging architecture** provides comprehensive system monitoring through traditional syslog and modern systemd journal systems.

## Logging Stack Overview

```bash
# Modern Linux logging architecture
┌─────────────────────────────────────┐
│        Applications                 │ ← Application logs
├─────────────────────────────────────┤
│      systemd services               │ ← Service stdout/stderr
├─────────────────────────────────────┤
│       systemd-journald              │ ← Central journal daemon
├─────────────────────────────────────┤
│        rsyslog                      │ ← Traditional syslog
├─────────────────────────────────────┤
│    Log Files (/var/log/)            │ ← File-based storage
├─────────────────────────────────────┤
│   Remote Logging (ELK/Splunk)       │ ← Centralized logging
└─────────────────────────────────────┘
```

## Core Components

**journald**: Systemd's logging daemon collecting all system logs
**rsyslog**: Traditional syslog daemon for compatibility and forwarding
**logrotate**: Automatic log rotation and cleanup
**auditd**: Security audit logging
**systemd-cat**: Bridge for sending logs to journal

## Log Storage Locations

```bash
# Primary log directories
/var/log/journal/            # Persistent journal storage
/run/log/journal/            # Runtime journal storage
/var/log/                    # Traditional log files

# Key system logs
/var/log/syslog              # System messages (Debian/Ubuntu)
/var/log/messages            # System messages (RHEL/CentOS)
/var/log/auth.log            # Authentication logs
/var/log/kern.log            # Kernel messages
/var/log/audit/              # Audit logs
/var/log/boot.log            # Boot messages
```

## Log Flow Process

1. **Applications** → Generate log messages
2. **systemd services** → Send stdout/stderr to journal
3. **journald** → Collects, indexes, and stores in binary format
4. **rsyslog** → Receives from journal, writes text files
5. **logrotate** → Rotates and compresses old logs
6. **Remote systems** → Forward logs to centralized systems

## Log Facilities and Priorities

### Syslog Facilities
- `kern` - Kernel messages
- `user` - User programs
- `mail` - Mail system
- `daemon` - System daemons
- `auth` - Security/authorization
- `syslog` - Syslog daemon
- `local0-7` - Custom applications

### Log Priorities
- `emerg` (0) - Emergency (system unusable)
- `alert` (1) - Alert (immediate action needed)
- `crit` (2) - Critical conditions
- `err` (3) - Error conditions
- `warning` (4) - Warning conditions
- `notice` (5) - Normal but significant
- `info` (6) - Informational messages
- `debug` (7) - Debug messages

## Quick Architecture Check

```bash
# Verify logging services
systemctl status systemd-journald
systemctl status rsyslog

# Check log directories
ls -la /var/log/
du -sh /var/log/journal/

# View log configuration
cat /etc/systemd/journald.conf
cat /etc/rsyslog.conf
```