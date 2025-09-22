# Linux Cron Production Examples

**Production cron examples** for common DevOps and system administration tasks.

## System Maintenance

### Log Rotation and Cleanup
```bash
# Compress and rotate logs older than 7 days
0 3 * * * find /var/log/app -name "*.log" -mtime +7 -exec gzip {} \;

# Clean old compressed logs (30 days)
0 4 * * 0 find /var/log -name "*.gz" -mtime +30 -delete

# Clean tmp directories
30 3 * * * find /tmp -type f -atime +3 -delete
30 3 * * * find /var/tmp -type f -atime +7 -delete
```

### System Monitoring
```bash
# Check disk space and alert
*/15 * * * * /usr/local/bin/check-disk-space.sh

# Monitor services
*/5 * * * * systemctl is-active nginx || systemctl restart nginx

# System health check
0 */6 * * * /usr/local/bin/system-health.sh | mail -s "System Health $(hostname)" admin@company.com
```

## Database Operations

### MySQL/MariaDB Backups
```bash
# Daily database backup
0 2 * * * mysqldump -u backup_user -p'password' --all-databases | gzip > /backup/mysql/backup-$(date +\%Y\%m\%d).sql.gz

# Weekly full backup with retention
0 3 * * 0 /usr/local/bin/mysql-full-backup.sh

# Hourly binary log backup
0 * * * * mysqladmin flush-logs && rsync -av /var/lib/mysql/mysql-bin.* /backup/binlogs/
```

### PostgreSQL Backups
```bash
# Daily PostgreSQL backup
0 2 * * * sudo -u postgres pg_dumpall | gzip > /backup/postgres/backup-$(date +\%Y\%m\%d).sql.gz

# Backup specific database
30 2 * * * sudo -u postgres pg_dump myapp_db | gzip > /backup/postgres/myapp-$(date +\%Y\%m\%d).sql.gz
```

## Application Management

### Service Monitoring and Restart
```bash
# Application health check
*/2 * * * * curl -f http://localhost:8080/health || systemctl restart myapp

# Memory usage monitoring
*/10 * * * * /usr/local/bin/check-memory-usage.sh

# Certificate expiration check
0 9 * * 1 /usr/local/bin/check-ssl-certs.sh
```

### Deployment and Updates
```bash
# Pull latest code (development environment)
0 1 * * * cd /opt/app && git pull origin main && systemctl restart myapp

# Update package lists
0 6 * * * apt update && apt list --upgradable | mail -s "Available Updates $(hostname)" admin@company.com

# Security updates (automated - use carefully)
0 3 * * 0 apt update && apt upgrade -y
```

## Security Tasks

### Security Monitoring
```bash
# Check for failed login attempts
0 8 * * * grep "Failed password" /var/log/auth.log | tail -20 | mail -s "Failed Logins $(hostname)" security@company.com

# Monitor sudo usage
0 9 * * * grep "sudo" /var/log/auth.log | grep "$(date '+%b %d')" | mail -s "Sudo Activity $(hostname)" admin@company.com

# File integrity check
0 4 * * * /usr/bin/aide --check | mail -s "File Integrity Check $(hostname)" security@company.com
```

### Certificate Management
```bash
# Auto-renew Let's Encrypt certificates
0 3 * * * certbot renew --quiet --post-hook "systemctl reload nginx"

# Check certificate expiration
0 9 * * 1 /usr/local/bin/ssl-cert-check.sh /etc/ssl/certs/
```

## Backup and Sync

### File System Backups
```bash
# Incremental backup with rsync
0 1 * * * rsync -av --delete /home/ backup-server:/backups/$(hostname)/home/

# Tar backup with rotation
0 2 * * * tar -czf /backup/system-$(date +\%Y\%m\%d).tar.gz /etc /opt /usr/local

# AWS S3 sync
0 3 * * * aws s3 sync /backup/ s3://company-backups/$(hostname)/ --delete
```

### Configuration Backup
```bash
# Backup configuration files
0 1 * * * /usr/local/bin/backup-configs.sh

# Git commit for /etc changes
0 5 * * * cd /etc && git add -A && git commit -m "Daily config backup $(date)" || true
```

## Performance and Analytics

### Log Analytics
```bash
# Process web server logs
5 0 * * * /usr/local/bin/process-nginx-logs.sh

# Generate usage reports
0 7 * * 1 /usr/local/bin/weekly-usage-report.sh | mail -s "Weekly Usage Report" management@company.com

# Performance metrics collection
*/5 * * * * /usr/local/bin/collect-metrics.sh
```

### Cleanup and Optimization
```bash
# Clean Docker containers and images
0 4 * * 0 docker system prune -f

# Clear package cache
0 5 * * 0 apt autoremove -y && apt autoclean

# Optimize databases
0 6 * * 0 mysqlcheck --optimize --all-databases
```

## Complete Production Crontab Example

```bash
# Production Server Crontab
SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin
MAILTO=admin@company.com

# System Maintenance
0 3 * * * find /tmp -type f -atime +3 -delete
30 3 * * * find /var/log -name "*.log" -mtime +30 -delete
0 4 * * 0 apt update && apt autoremove -y

# Backups
0 2 * * * /usr/local/bin/database-backup.sh
30 2 * * * rsync -av /opt/app/ backup-server:/backups/app/
0 1 * * 0 /usr/local/bin/full-system-backup.sh

# Monitoring
*/5 * * * * /usr/local/bin/health-check.sh
*/15 * * * * /usr/local/bin/disk-space-check.sh
0 */6 * * * /usr/local/bin/system-report.sh

# Security
0 8 * * * /usr/local/bin/security-scan.sh
0 3 * * * certbot renew --quiet

# Application Management
*/2 * * * * curl -f http://localhost/health || systemctl restart webapp
0 6 * * * cd /opt/app && git pull && systemctl restart webapp

# Reports
0 7 * * 1 /usr/local/bin/weekly-report.sh
0 8 1 * * /usr/local/bin/monthly-report.sh
```

## Cron Script Template

```bash
#!/bin/bash
# Production cron script template

# Set strict error handling
set -euo pipefail

# Configuration
SCRIPT_NAME="$(basename "$0")"
LOG_FILE="/var/log/cron-scripts/${SCRIPT_NAME}.log"
LOCK_FILE="/var/run/${SCRIPT_NAME}.lock"

# Logging function
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $*" >> "$LOG_FILE"
}

# Cleanup function
cleanup() {
    rm -f "$LOCK_FILE"
}
trap cleanup EXIT

# Prevent multiple instances
if [[ -f "$LOCK_FILE" ]]; then
    log "Script already running, exiting"
    exit 1
fi
echo $$ > "$LOCK_FILE"

# Main script logic
log "Starting $SCRIPT_NAME"

# Your script commands here
# ...

log "Completed $SCRIPT_NAME successfully"
```

## Monitoring Cron Jobs

```bash
# Monitor cron job execution
*/1 * * * * echo "$(date): Cron heartbeat" >> /var/log/cron-heartbeat.log

# Alert on job failures
0 8 * * * /usr/local/bin/check-cron-jobs.sh || echo "Cron job failures detected" | mail -s "ALERT: Cron Issues" admin@company.com

# Job duration monitoring
0 2 * * * time /usr/local/bin/backup.sh 2>&1 | logger -t backup-job
```