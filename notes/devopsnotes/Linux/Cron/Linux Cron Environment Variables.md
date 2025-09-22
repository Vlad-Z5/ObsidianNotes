# Linux Cron Environment Variables

**Cron environment** is minimal by default. Setting proper environment variables is crucial for cron jobs to work correctly.

## Default Cron Environment

Cron runs with a minimal environment:
- `PATH=/usr/bin:/bin`
- `SHELL=/bin/sh`
- `HOME=/home/username` (for user crontabs)
- `LOGNAME=username`

## Setting Environment Variables

```bash
# In crontab file (crontab -e)
SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin
HOME=/home/username
MAILTO=admin@example.com

# Environment variables affect all jobs below
0 2 * * * /path/to/script.sh
```

## Common Environment Issues

```bash
# Wrong - relies on interactive shell PATH
0 2 * * * backup.sh

# Right - use full path
0 2 * * * /usr/local/bin/backup.sh

# Right - set PATH in crontab
PATH=/usr/local/bin:/usr/bin:/bin
0 2 * * * backup.sh
```

## Loading Shell Environment

```bash
# Source user's profile in cron job
0 2 * * * source ~/.profile && /path/to/script.sh

# Use bash login shell
0 2 * * * bash -l -c '/path/to/script.sh'

# Load specific environment file
0 2 * * * source /etc/environment && /path/to/script.sh
```

## Mail Configuration

```bash
# Send output to specific email
MAILTO=admin@company.com
0 2 * * * /path/to/script.sh

# Disable email output
MAILTO=""
0 2 * * * /path/to/script.sh

# Send to multiple recipients (system dependent)
MAILTO="admin@company.com,backup@company.com"
0 2 * * * /path/to/script.sh
```

## Working Directory

```bash
# Cron jobs run from user's home directory by default
# Explicitly change directory in script
0 2 * * * cd /opt/app && ./script.sh

# Or use absolute paths
0 2 * * * /opt/app/script.sh
```

## Environment Debugging

```bash
# Create a cron job to dump environment
* * * * * env > /tmp/cron-env.txt

# Debug script environment
0 2 * * * echo "PATH=$PATH" >> /tmp/cron-debug.log
0 2 * * * whoami >> /tmp/cron-debug.log
0 2 * * * pwd >> /tmp/cron-debug.log
```

## Production Environment Template

```bash
# Recommended crontab header
SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin
MAILTO=admin@company.com

# Set timezone if needed
TZ=America/New_York

# Application-specific variables
APP_ENV=production
LOG_LEVEL=info

# Cron jobs
0 2 * * * /usr/local/bin/backup.sh
30 3 * * 0 /usr/local/bin/weekly-maintenance.sh
```

## Security Considerations

```bash
# Don't put sensitive data in environment
# Wrong
DATABASE_PASSWORD=secret123
0 2 * * * backup-db.sh

# Right - use secure methods
0 2 * * * /path/to/script.sh --config /etc/app/secure.conf
```