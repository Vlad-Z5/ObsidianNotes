# Linux Cron Fundamentals

**Cron** is the time-based job scheduler in Linux systems that runs background processes at specified times and intervals.

## What is Cron?

Cron is a daemon that reads configuration files called "crontabs" and executes commands at scheduled times. It's essential for:
- System maintenance tasks
- Automated backups
- Log rotation
- Monitoring scripts
- DevOps automation

## Cron Service Management

```bash
# Check cron service status
systemctl status cron          # Debian/Ubuntu
systemctl status crond         # RHEL/CentOS/Fedora

# Start/stop/restart cron
systemctl start cron
systemctl stop cron
systemctl restart cron
systemctl enable cron
```

## Cron Configuration Files

```bash
# System-wide crontab
/etc/crontab                   # Main system crontab

# Drop-in directories
/etc/cron.d/                   # System job definitions
/etc/cron.hourly/              # Scripts run every hour
/etc/cron.daily/               # Scripts run daily
/etc/cron.weekly/              # Scripts run weekly
/etc/cron.monthly/             # Scripts run monthly

# User crontabs
/var/spool/cron/crontabs/      # User crontabs (Debian/Ubuntu)
/var/spool/cron/               # User crontabs (RHEL/CentOS)
```

## Cron Logs

```bash
# View cron logs
tail -f /var/log/cron          # RHEL/CentOS
tail -f /var/log/syslog | grep CRON    # Debian/Ubuntu
journalctl -u cron -f          # Systemd systems
```

## Quick Check

```bash
# Verify cron is running
ps aux | grep cron

# Check if cron jobs are scheduled
crontab -l                     # Current user's crontab
sudo crontab -l                # Root's crontab
ls /etc/cron.d/               # System cron jobs
```