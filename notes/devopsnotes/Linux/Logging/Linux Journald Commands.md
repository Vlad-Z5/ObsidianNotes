# Linux Journald Commands

**journalctl** is the primary command for querying and managing systemd journal logs.

## Basic Journal Viewing

```bash
# View all journal entries
journalctl

# Follow new entries (like tail -f)
journalctl -f

# Show last N entries
journalctl -n 50

# Show entries since specific time
journalctl --since "2024-01-01 10:00:00"
journalctl --since yesterday
journalctl --since "1 hour ago"
```

## Service-Specific Logs

```bash
# View logs for specific service
journalctl -u nginx
journalctl -u sshd.service

# Follow service logs
journalctl -u nginx -f

# Show service logs since boot
journalctl -u nginx -b

# Show failed services
journalctl --failed
```

## Time-Based Filtering

```bash
# Show logs from specific date range
journalctl --since "2024-01-01" --until "2024-01-02"
journalctl --since "10:00" --until "11:00"

# Show logs from current boot
journalctl -b

# Show logs from previous boot
journalctl -b -1

# List all boots
journalctl --list-boots
```

## Priority and Facility Filtering

```bash
# Show only error messages and above
journalctl -p err

# Show priority levels
journalctl -p warning..err

# Show kernel messages only
journalctl -k
journalctl --dmesg

# Show by facility
journalctl SYSLOG_FACILITY=10  # authpriv
```

## Output Formatting

```bash
# JSON output
journalctl -o json

# Short format (traditional syslog)
journalctl -o short

# Verbose output with all fields
journalctl -o verbose

# Export format for backup
journalctl -o export

# No pager output
journalctl --no-pager
```

## Advanced Filtering

```bash
# Filter by process ID
journalctl _PID=1234

# Filter by user ID
journalctl _UID=1000

# Filter by executable
journalctl _COMM=nginx

# Filter by systemd unit
journalctl _SYSTEMD_UNIT=nginx.service

# Multiple filters (AND operation)
journalctl _SYSTEMD_UNIT=nginx.service -p err
```

## Journal Management

```bash
# Show journal disk usage
journalctl --disk-usage

# Verify journal integrity
journalctl --verify

# Rotate journal files
systemctl kill --kill-who=main --signal=SIGUSR2 systemd-journald

# Vacuum old logs by size
journalctl --vacuum-size=1G

# Vacuum old logs by time
journalctl --vacuum-time=2weeks

# Vacuum old logs by file count
journalctl --vacuum-files=10
```

## Real-Time Monitoring

```bash
# Follow all logs with highlighting
journalctl -f --output=short-iso

# Follow specific service with colors
journalctl -u nginx -f -o cat

# Monitor multiple services
journalctl -u nginx -u apache2 -f

# Follow with grep filter
journalctl -f | grep -i error
```

## Boot Analysis

```bash
# Show boot time
systemd-analyze

# Show service startup times
systemd-analyze blame

# Show boot chain
systemd-analyze critical-chain

# Show boot logs
journalctl -b

# Show kernel ring buffer
journalctl --dmesg
```

## Security and Audit

```bash
# Show authentication logs
journalctl -u ssh -g "Failed\|Invalid"

# Show sudo usage
journalctl -g "sudo"

# Show system errors
journalctl -p err -b

# Show security-related entries
journalctl --facility=authpriv
```

## Useful Combinations

```bash
# Today's errors for specific service
journalctl -u nginx -p err --since today

# Last hour of authentication attempts
journalctl --since "1 hour ago" -g "authentication\|login\|ssh"

# System startup issues
journalctl -b -p err

# Service restart events
journalctl -u nginx -g "Started\|Stopped\|Reloaded"

# High-frequency log entries
journalctl --since "1 hour ago" | awk '{print $5}' | sort | uniq -c | sort -nr
```

## Performance Tips

```bash
# Use --no-pager for scripts
journalctl --no-pager -n 100

# Limit output size
journalctl --lines=100

# Use specific time ranges
journalctl --since "30 minutes ago"

# Filter early to reduce processing
journalctl -u nginx -p warning
```