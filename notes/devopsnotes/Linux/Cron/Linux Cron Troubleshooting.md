# Linux Cron Troubleshooting

**Cron troubleshooting** involves identifying why scheduled jobs aren't running or producing expected results.

## Common Issues Checklist

1. **Is cron running?**
2. **Is the syntax correct?**
3. **Are permissions set correctly?**
4. **Is the script executable?**
5. **Are paths absolute?**
6. **Is the environment correct?**

## Check if Cron is Running

```bash
# Check cron service status
systemctl status cron          # Debian/Ubuntu
systemctl status crond         # RHEL/CentOS

# Check cron process
ps aux | grep cron | grep -v grep

# Check if cron is enabled
systemctl is-enabled cron
```

## Verify Crontab Syntax

```bash
# Check crontab syntax
crontab -l

# Validate before installing
crontab -l > temp_crontab
# Edit temp_crontab
crontab temp_crontab

# Use online cron validators
# https://crontab.guru/
```

## Check Cron Logs

```bash
# View cron logs
tail -f /var/log/cron                    # RHEL/CentOS
tail -f /var/log/syslog | grep CRON      # Debian/Ubuntu
journalctl -u cron -f                    # Systemd

# Filter for specific user
grep "username" /var/log/cron

# Check for errors
grep -i error /var/log/cron
```

## Test Script Manually

```bash
# Run script as the same user
sudo -u username /path/to/script.sh

# Test with minimal environment (like cron)
env -i /bin/bash -c '/path/to/script.sh'

# Test with cron environment
env -i PATH=/usr/bin:/bin /path/to/script.sh
```

## Debug Cron Environment

```bash
# Create debug cron job
* * * * * env > /tmp/cron-env-$(date +\%Y\%m\%d-\%H\%M).txt

# Check what cron sees
* * * * * echo "Current dir: $(pwd)" >> /tmp/cron-debug.log
* * * * * echo "PATH: $PATH" >> /tmp/cron-debug.log
* * * * * echo "User: $(whoami)" >> /tmp/cron-debug.log
```

## Common Solutions

### Script Not Executing

```bash
# Check if script is executable
ls -la /path/to/script.sh
chmod +x /path/to/script.sh

# Use absolute path to interpreter
0 2 * * * /bin/bash /path/to/script.sh

# Check shebang line
#!/bin/bash  # Make sure this is the first line
```

### Command Not Found

```bash
# Use full paths
0 2 * * * /usr/bin/mysqldump ...

# Or set PATH in crontab
PATH=/usr/local/bin:/usr/bin:/bin
0 2 * * * mysqldump ...
```

### Permission Denied

```bash
# Check file permissions
ls -la /path/to/script.sh

# Check directory permissions
ls -ld /path/to/

# Run as specific user
0 2 * * * sudo -u username /path/to/script.sh
```

### No Output/Silent Failures

```bash
# Redirect output to file
0 2 * * * /path/to/script.sh >> /var/log/script.log 2>&1

# Capture both success and error
0 2 * * * /path/to/script.sh > /tmp/script.out 2> /tmp/script.err

# Test mail delivery
0 2 * * * echo "Test" | mail -s "Cron Test" user@example.com
```

## Advanced Debugging

### Wrapper Script Method

```bash
# Create wrapper script /usr/local/bin/cron-wrapper.sh
#!/bin/bash
{
    echo "=== $(date) ==="
    echo "Running: $*"
    echo "PWD: $(pwd)"
    echo "User: $(whoami)"
    echo "Environment:"
    env
    echo "=== Output ==="
    "$@"
    echo "=== Exit code: $? ==="
} >> /var/log/cron-wrapper.log 2>&1

# Use in crontab
0 2 * * * /usr/local/bin/cron-wrapper.sh /path/to/original/script.sh
```

### Monitoring Script

```bash
# Monitor cron execution
#!/bin/bash
# /usr/local/bin/cron-monitor.sh

EXPECTED_JOBS=(
    "backup.sh"
    "cleanup.sh"
    "report.sh"
)

for job in "${EXPECTED_JOBS[@]}"; do
    if ! pgrep -f "$job" > /dev/null; then
        echo "WARNING: $job not running" | logger -t cron-monitor
    fi
done
```

## Quick Diagnostic Commands

```bash
# One-liner to check cron status
systemctl is-active cron && echo "Cron is running" || echo "Cron is not running"

# Check recent cron activity
journalctl -u cron --since "1 hour ago"

# Verify user can use cron
[ -f /etc/cron.allow ] && grep "^$(whoami)$" /etc/cron.allow || echo "Check cron.allow"

# Test cron job will run soon
crontab -l | head -1  # Should show a test job
```