# Linux Cron Management

**Crontab management** involves creating, editing, and managing scheduled jobs for users and the system.

## User Crontab Commands

```bash
# Edit current user's crontab
crontab -e

# List current user's crontab
crontab -l

# Remove current user's crontab
crontab -r

# Edit another user's crontab (as root)
crontab -e -u username

# List another user's crontab
crontab -l -u username
```

## System Crontab

```bash
# Edit system crontab
sudo vim /etc/crontab

# System crontab format (includes user field)
# minute hour day month weekday user command
0 2 * * * root /usr/local/bin/backup.sh
```

## Adding Jobs to Cron Directories

```bash
# Add executable script to cron directories
sudo cp script.sh /etc/cron.daily/
sudo chmod +x /etc/cron.daily/script.sh

# Test scripts in cron directories
sudo run-parts --test /etc/cron.daily
sudo run-parts /etc/cron.daily  # Actually run them
```

## Creating System Cron Jobs

```bash
# Create a job in /etc/cron.d/
sudo tee /etc/cron.d/backup-job <<EOF
# Backup job - runs daily at 2 AM
0 2 * * * root /usr/local/bin/backup.sh
EOF
```

## Crontab Environment

```bash
# Set environment variables in crontab
SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin
MAILTO=admin@company.com

# Your cron jobs follow
0 2 * * * /path/to/script.sh
```

## Common Management Tasks

```bash
# Backup user crontab
crontab -l > ~/crontab-backup.txt

# Restore user crontab
crontab ~/crontab-backup.txt

# Temporarily disable all cron jobs
sudo systemctl stop cron

# Check cron job history
grep CRON /var/log/syslog
```

## Permission Management

```bash
# Allow specific users to use cron
echo "username" | sudo tee -a /etc/cron.allow

# Deny specific users from using cron
echo "username" | sudo tee -a /etc/cron.deny

# Check who can use cron
cat /etc/cron.allow
cat /etc/cron.deny
```

## Validation

```bash
# Validate crontab syntax before saving
crontab -l | crontab -T

# Check if cron jobs are actually running
tail -f /var/log/cron | grep username
```