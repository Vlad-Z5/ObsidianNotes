# Linux Cron & Task Scheduling

**Cron** is the time-based job scheduler in Linux systems, enabling automated execution of scripts and commands for system administration, backups, monitoring, and DevOps automation workflows.

## Cron Fundamentals

### Cron Daemon & Service

```bash
# Cron service management
systemctl status cron          # Debian/Ubuntu
systemctl status crond         # RHEL/CentOS/Fedora
systemctl start cron
systemctl enable cron

# Cron configuration hierarchy
/etc/crontab                   # System-wide crontab
/etc/cron.d/                   # Drop-in directory for system jobs
/var/spool/cron/crontabs/      # User crontabs (Debian/Ubuntu)
/var/spool/cron/               # User crontabs (RHEL/CentOS)
```

### Cron Directories

```bash
# Predefined time-based directories
/etc/cron.hourly/             # Execute every hour
/etc/cron.daily/              # Execute daily
/etc/cron.weekly/             # Execute weekly
/etc/cron.monthly/            # Execute monthly

# Check scheduled scripts
ls -la /etc/cron.*
run-parts --test /etc/cron.daily    # Test daily scripts
```

---

## Crontab Management

### Basic Crontab Operations

```bash
# User crontab management
crontab -e                    # Edit current user's crontab
crontab -l                    # List current user's crontab
crontab -r                    # Remove current user's crontab

# Managing other users' crontabs (as root)
sudo crontab -u username -e   # Edit user's crontab
sudo crontab -u username -l   # List user's crontab
sudo crontab -u username -r   # Remove user's crontab

# Backup and restore crontabs
crontab -l > ~/crontab-backup-$(date +%Y%m%d).txt
crontab ~/crontab-backup-20241201.txt
```

### System vs User Crontabs

```bash
# System crontab format (/etc/crontab)
# min hour dom mon dow user command
0   2    *   *   *   root /usr/local/bin/backup.sh

# User crontab format (crontab -e)
# min hour dom mon dow command
0   2    *   *   *   /home/user/scripts/backup.sh
```

---

## Cron Syntax & Patterns

### Time Field Format

```bash
# Field positions:
# ┌───────────── minute (0-59)
# │ ┌─────────── hour (0-23)
# │ │ ┌───────── day of month (1-31)
# │ │ │ ┌─────── month (1-12)
# │ │ │ │ ┌───── day of week (0-7, 0 or 7 = Sunday)
# │ │ │ │ │
# * * * * * command

# Special characters
*       # Any value (wildcard)
,       # Value list separator
-       # Range of values
/       # Step values
@       # Special keywords
```

### Common Cron Patterns

```bash
# Basic timing patterns
* * * * *           # Every minute
*/5 * * * *         # Every 5 minutes
0 * * * *           # Every hour (at minute 0)
30 2 * * *          # Daily at 2:30 AM
0 0 * * 0           # Weekly on Sunday at midnight
0 0 1 * *           # Monthly on 1st at midnight

# Advanced patterns
0 9-17 * * 1-5      # Weekdays 9 AM to 5 PM
*/15 9-17 * * 1-5   # Every 15 min during business hours
0 2 * * 1,3,5       # Monday, Wednesday, Friday at 2 AM
0 */6 * * *         # Every 6 hours
0 8,12,17 * * 1-5   # Three times on weekdays

# Range and step combinations
5-59/10 * * * *     # Every 10 minutes starting at minute 5
0 9-17/2 * * 1-5    # Every 2 hours from 9 AM to 5 PM on weekdays
```

### Special Cron Keywords

```bash
@reboot             # Run once at startup
@yearly             # Run once a year (0 0 1 1 *)
@annually           # Same as @yearly
@monthly            # Run once a month (0 0 1 * *)
@weekly             # Run once a week (0 0 * * 0)
@daily              # Run once a day (0 0 * * *)
@midnight           # Same as @daily
@hourly             # Run once an hour (0 * * * *)

# Usage examples
@reboot /usr/local/bin/startup-script.sh
@daily /usr/local/bin/daily-backup.sh
@weekly /usr/local/bin/log-rotation.sh
```

### Environment Variables

```bash
# Set environment in crontab
SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin
MAILTO=admin@example.com
HOME=/home/user
LANG=en_US.UTF-8

# Use variables in commands
0 2 * * * $HOME/scripts/backup.sh >> $HOME/logs/backup.log 2>&1
```

---

## Systemd Timers

### Creating Systemd Timer Units

```ini
# Service file: /etc/systemd/system/backup.service
[Unit]
Description=Database Backup Service
Documentation=https://company.com/docs/backup
After=network.target postgresql.service

[Service]
Type=oneshot
ExecStart=/usr/local/bin/backup-database.sh
User=backup
Group=backup
WorkingDirectory=/var/backups

# Security hardening
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
PrivateTmp=true
ReadWritePaths=/var/backups
```

```ini
# Timer file: /etc/systemd/system/backup.timer
[Unit]
Description=Run database backup
Documentation=https://company.com/docs/backup
Requires=backup.service

[Timer]
OnCalendar=daily
Persistent=true
RandomizedDelaySec=1800
AccuracySec=1min

[Install]
WantedBy=timers.target
```

### Timer Management

```bash
# Enable and start timer
sudo systemctl enable backup.timer
sudo systemctl start backup.timer

# Timer status and monitoring
systemctl status backup.timer
systemctl list-timers backup.timer
systemctl list-timers --all

# Manual service execution
sudo systemctl start backup.service

# Timer logs
journalctl -u backup.timer -f
journalctl -u backup.service -n 50
```

### OnCalendar Syntax

```bash
# Systemd calendar event format
# DayOfWeek Year-Month-Day Hour:Minute:Second

# Common OnCalendar patterns
OnCalendar=hourly                    # Every hour
OnCalendar=daily                     # Daily at midnight
OnCalendar=weekly                    # Weekly on Monday at midnight
OnCalendar=monthly                   # Monthly on 1st at midnight

# Specific timing
OnCalendar=*-*-* 02:30:00           # Daily at 2:30 AM
OnCalendar=Mon *-*-* 09:00:00       # Every Monday at 9 AM
OnCalendar=*-*-01 00:00:00          # Monthly on 1st at midnight
OnCalendar=*-12-25 00:00:00         # Christmas Day annually

# Advanced patterns
OnCalendar=Mon..Fri 09:00           # Weekdays at 9 AM
OnCalendar=*-*-* 06,18:00           # 6 AM and 6 PM daily
OnCalendar=Sat *-*-* 02:00          # Saturdays at 2 AM
OnCalendar=*-*-* *:00/15            # Every 15 minutes
```

---

## At Command

### One-time Job Scheduling

```bash
# Schedule jobs with at
at 15:30                        # Today at 3:30 PM
at 'now + 30 minutes'          # 30 minutes from now
at 'now + 2 hours'             # 2 hours from now
at 'now + 3 days'              # 3 days from now
at '2024-12-25 09:00'          # Specific date/time
at 'noon tomorrow'             # Tomorrow at noon
at 'midnight'                  # Tonight at midnight

# Interactive job entry
at 15:30
at> /usr/local/bin/maintenance.sh
at> echo "Maintenance completed" | mail admin@example.com
at> <Ctrl+D>

# File-based job submission
echo "/usr/local/bin/backup.sh" | at 'now + 1 hour'
at -f /path/to/script.sh 'now + 30 minutes'
```

### At Job Management

```bash
# List scheduled at jobs
atq                             # List all jobs
at -l                           # Same as atq

# View job details
at -c job_number               # Show job commands

# Remove scheduled jobs
atrm job_number                # Remove specific job
atrm 1 2 3                     # Remove multiple jobs
```

### Batch Processing

```bash
# Run when system load permits
batch
batch> /usr/local/bin/heavy-processing.sh
batch> <Ctrl+D>

# Schedule batch job for specific time
echo "/usr/local/bin/cpu-intensive.sh" | batch
```

---

## Anacron for Non-24/7 Systems

### Anacron Configuration

```bash
# /etc/anacrontab format
# period delay job-identifier command

# Example anacrontab entries
1    5    daily.backup      /usr/local/bin/daily-backup.sh
7    10   weekly.cleanup    /usr/local/bin/weekly-cleanup.sh
30   15   monthly.report    /usr/local/bin/monthly-report.sh

# Field explanations:
# period: days between executions
# delay: minutes to wait before execution
# job-identifier: unique job name
# command: command to execute
```

### Anacron Operations

```bash
# Run anacron jobs
sudo anacron                   # Run due jobs
sudo anacron -f               # Force run all jobs
sudo anacron -n               # Run jobs now (no delay)

# Test configuration
sudo anacron -T               # Test anacrontab syntax

# Job tracking
cat /var/spool/anacron/daily.backup     # Check job timestamp
ls -la /var/spool/anacron/               # List all job timestamps
```

---

## Environment & Security

### Cron Environment Setup

```bash
# Common environment issues and solutions
SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin
LANG=en_US.UTF-8
LC_ALL=en_US.UTF-8
TZ=America/New_York

# Debug environment differences
* * * * * env > /tmp/cron-env.txt 2>&1
# Compare with: env > /tmp/shell-env.txt
```

### Security Best Practices

```bash
# Restrict cron access
echo "allowed_user" | sudo tee /etc/cron.allow
sudo rm -f /etc/cron.deny

# Secure file permissions
sudo chmod 600 /etc/crontab
sudo chmod 700 /etc/cron.d
sudo chmod 700 /var/spool/cron

# Audit cron jobs
sudo find /etc/cron* -type f -exec ls -la {} \;
for user in $(cut -f1 -d: /etc/passwd); do
    echo "=== $user ==="
    sudo crontab -l -u "$user" 2>/dev/null || echo "No crontab"
done
```

### Production Script Template

```bash
#!/bin/bash
# Production-ready cron script

# Strict error handling
set -euo pipefail

# Script identification
SCRIPT_NAME=$(basename "$0")
SCRIPT_DIR=$(dirname "$0")
LOG_DIR="/var/log/cron-jobs"
LOCK_DIR="/var/lock"

# Logging setup
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/${SCRIPT_NAME%.sh}.log"

# Logging function
log() {
    local level="$1"
    shift
    echo "$(date '+%Y-%m-%d %H:%M:%S') [$SCRIPT_NAME] $level: $*" | tee -a "$LOG_FILE"
}

# Lock mechanism
LOCK_FILE="$LOCK_DIR/${SCRIPT_NAME%.sh}.lock"
exec 200>"$LOCK_FILE"

if ! flock -n 200; then
    log "ERROR" "Script is already running (lock file exists)"
    exit 1
fi

# Cleanup function
cleanup() {
    local exit_code=$?
    flock -u 200
    rm -f "$LOCK_FILE"
    log "INFO" "Script finished with exit code $exit_code"
    exit $exit_code
}
trap cleanup EXIT INT TERM

# Main script logic
log "INFO" "Starting script execution"

# Your actual work here
if /usr/local/bin/actual-work.sh; then
    log "INFO" "Work completed successfully"
else
    log "ERROR" "Work failed"
    exit 1
fi

log "INFO" "Script completed successfully"
```

---

## Monitoring & Logging

### Cron Log Analysis

```bash
# Check cron logs
sudo journalctl -u cron -f              # Follow cron logs
sudo journalctl -u cron --since "1 hour ago"
sudo tail -f /var/log/cron              # Traditional log file
sudo grep CRON /var/log/syslog          # Debian/Ubuntu

# Enhanced logging configuration
echo 'cron.* /var/log/cron.log' | sudo tee -a /etc/rsyslog.conf
sudo systemctl restart rsyslog
```

### Job Monitoring Scripts

```bash
#!/bin/bash
# Cron job health monitor

MONITOR_CONFIG="/etc/cron-monitor.conf"
ALERT_EMAIL="admin@example.com"

# Configuration format: job_name:max_age_hours:log_pattern
# Example: daily_backup:25:/var/log/backup.log

check_job_health() {
    local job_name="$1"
    local max_age_hours="$2"
    local log_pattern="$3"

    local max_age_seconds=$((max_age_hours * 3600))
    local current_time=$(date +%s)

    if [[ -f "$log_pattern" ]]; then
        local file_age=$(stat -c %Y "$log_pattern")
        local age_diff=$((current_time - file_age))

        if [[ $age_diff -gt $max_age_seconds ]]; then
            echo "WARNING: $job_name hasn't updated $log_pattern for $((age_diff / 3600)) hours"
            return 1
        else
            echo "OK: $job_name is healthy"
            return 0
        fi
    else
        echo "ERROR: $job_name log file $log_pattern not found"
        return 1
    fi
}

# Process monitoring configuration
while IFS=':' read -r job_name max_age log_pattern; do
    [[ "$job_name" =~ ^#.*$ ]] && continue  # Skip comments
    [[ -z "$job_name" ]] && continue        # Skip empty lines

    if ! check_job_health "$job_name" "$max_age" "$log_pattern"; then
        echo "Job $job_name requires attention" | mail -s "Cron Job Alert" "$ALERT_EMAIL"
    fi
done < "$MONITOR_CONFIG"
```

### Integration with External Monitoring

```bash
# Healthcheck.io integration
0 2 * * * /usr/local/bin/backup.sh && curl -fsS --retry 3 "https://hc-ping.com/uuid-here"

# Custom webhook notification
send_notification() {
    local job_name="$1"
    local status="$2"
    local message="$3"

    curl -X POST \
        -H "Content-Type: application/json" \
        -d "{\"job\":\"$job_name\",\"status\":\"$status\",\"message\":\"$message\",\"timestamp\":\"$(date -Iseconds)\"}" \
        "https://monitoring.example.com/webhook/cron"
}

# Usage in cron scripts
if /usr/local/bin/backup.sh; then
    send_notification "backup" "success" "Backup completed successfully"
else
    send_notification "backup" "failure" "Backup failed with exit code $?"
fi
```

---

## DevOps Integration

### Docker Cron Containers

```dockerfile
# Dockerfile for cron services
FROM ubuntu:22.04

# Install cron and dependencies
RUN apt-get update && \
    apt-get install -y cron curl && \
    rm -rf /var/lib/apt/lists/*

# Copy cron jobs and scripts
COPY crontab /etc/cron.d/app-cron
COPY scripts/ /usr/local/bin/
RUN chmod 0644 /etc/cron.d/app-cron && \
    chmod +x /usr/local/bin/* && \
    crontab /etc/cron.d/app-cron

# Create log directory
RUN mkdir -p /var/log/cron-jobs

# Start cron in foreground
CMD ["cron", "-f"]
```

### Kubernetes CronJobs

```yaml
# kubernetes-backup-cronjob.yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: database-backup
  namespace: production
spec:
  schedule: "0 2 * * *"
  timeZone: "America/New_York"
  concurrencyPolicy: Forbid
  successfulJobsHistoryLimit: 3
  failedJobsHistoryLimit: 1
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: backup
            image: backup-tools:v1.2.3
            command:
            - /usr/local/bin/backup-database.sh
            env:
            - name: DB_HOST
              value: "postgres.database.svc.cluster.local"
            - name: BACKUP_BUCKET
              value: "s3://company-backups/database"
            volumeMounts:
            - name: backup-config
              mountPath: /etc/backup
              readOnly: true
          volumes:
          - name: backup-config
            configMap:
              name: backup-config
          restartPolicy: OnFailure
```

### Ansible Cron Management

```yaml
# ansible-cron-deployment.yml
---
- name: Configure cron jobs across servers
  hosts: production_servers
  become: yes

  vars:
    cron_jobs:
      - name: "Daily backup"
        minute: "0"
        hour: "2"
        job: "/usr/local/bin/backup.sh"
        user: "backup"
      - name: "Log rotation"
        minute: "0"
        hour: "0"
        weekday: "0"
        job: "/usr/local/bin/log-rotation.sh"
        user: "root"
      - name: "System health check"
        minute: "*/15"
        job: "/usr/local/bin/health-check.sh"
        user: "monitoring"

  tasks:
    - name: Install cron jobs
      cron:
        name: "{{ item.name }}"
        minute: "{{ item.minute | default('*') }}"
        hour: "{{ item.hour | default('*') }}"
        day: "{{ item.day | default('*') }}"
        month: "{{ item.month | default('*') }}"
        weekday: "{{ item.weekday | default('*') }}"
        job: "{{ item.job }}"
        user: "{{ item.user | default('root') }}"
        state: present
      loop: "{{ cron_jobs }}"

    - name: Remove old cron jobs
      cron:
        name: "{{ item }}"
        state: absent
      loop:
        - "Old backup job"
        - "Deprecated monitoring"
```

---

## Troubleshooting

### Common Issues and Solutions

**Issue**: Cron job not executing
```bash
# Check cron daemon status
systemctl status cron

# Verify cron job syntax
crontab -l | head -5

# Test script manually
/bin/bash -c 'source ~/.bashrc; /path/to/script.sh'

# Check system timezone
timedatectl status
date
```

**Issue**: Script works manually but fails in cron
```bash
# Compare environments
* * * * * env > /tmp/cron-env.txt 2>&1
env > /tmp/shell-env.txt
diff /tmp/shell-env.txt /tmp/cron-env.txt

# Common fixes
SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin
HOME=/home/username
```

**Issue**: No output or error messages
```bash
# Add comprehensive logging
0 2 * * * /path/to/script.sh >> /var/log/cron-script.log 2>&1

# Email output (ensure MAILTO is set)
MAILTO=admin@example.com
0 2 * * * /path/to/script.sh

# Use logger for syslog
0 2 * * * /path/to/script.sh 2>&1 | logger -t backup-script
```

**Issue**: Job runs multiple times
```bash
# Implement proper locking
#!/bin/bash
LOCK_FILE="/var/lock/$(basename "$0").lock"
exec 200>"$LOCK_FILE"

if ! flock -n 200; then
    echo "Script already running" >&2
    exit 1
fi

# Your script logic here
```

### Systemd Timer Troubleshooting

```bash
# Check timer configuration
systemctl cat backup.timer
systemctl show backup.timer

# Verify service unit
systemctl cat backup.service
systemctl show backup.service

# Check timer status
systemctl list-timers backup.timer
systemctl status backup.timer

# View logs
journalctl -u backup.timer -n 50
journalctl -u backup.service -n 50

# Test service manually
sudo systemctl start backup.service
journalctl -u backup.service -f
```

---

## Production Examples

### Database Backup with Rotation

```bash
#!/bin/bash
# /usr/local/bin/database-backup.sh

set -euo pipefail

# Configuration
DB_NAME="production_db"
DB_USER="backup_user"
BACKUP_DIR="/var/backups/database"
RETENTION_DAYS=30
S3_BUCKET="s3://company-backups/database"

# Logging setup
LOG_FILE="/var/log/cron-jobs/database-backup.log"
exec 1> >(tee -a "$LOG_FILE")
exec 2>&1

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') $*"
}

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Generate backup filename
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/${DB_NAME}_${TIMESTAMP}.sql.gz"

# Perform backup
log "Starting database backup for $DB_NAME"
if pg_dump -U "$DB_USER" -h localhost "$DB_NAME" | gzip > "$BACKUP_FILE"; then
    log "Backup created successfully: $BACKUP_FILE"

    # Upload to S3
    if aws s3 cp "$BACKUP_FILE" "$S3_BUCKET/"; then
        log "Backup uploaded to S3 successfully"
    else
        log "ERROR: Failed to upload backup to S3"
        exit 1
    fi

    # Cleanup old local backups
    find "$BACKUP_DIR" -name "${DB_NAME}_*.sql.gz" -mtime +$RETENTION_DAYS -delete
    log "Cleaned up backups older than $RETENTION_DAYS days"

else
    log "ERROR: Database backup failed"
    exit 1
fi

log "Database backup completed successfully"

# Crontab entry:
# 0 2 * * * /usr/local/bin/database-backup.sh
```

### Multi-Environment Deployment Pipeline

```bash
#!/bin/bash
# /usr/local/bin/deploy-pipeline.sh

set -euo pipefail

# Configuration
ENVIRONMENTS=("staging" "production")
DEPLOYMENT_HOUR=2
STAGING_DELAY=0
PRODUCTION_DELAY=600  # 10 minutes after staging

# Current time check
CURRENT_HOUR=$(date +%H)
CURRENT_MINUTE=$(date +%M)

deploy_to_environment() {
    local env="$1"
    local config_file="/etc/deployment/$env.conf"

    if [[ ! -f "$config_file" ]]; then
        echo "ERROR: Configuration file not found: $config_file" >&2
        return 1
    fi

    source "$config_file"

    echo "$(date '+%Y-%m-%d %H:%M:%S') Starting deployment to $env"

    # Pull latest code
    cd "$REPO_PATH"
    git fetch origin
    git checkout "$BRANCH"
    git pull origin "$BRANCH"

    # Run deployment
    if ./deploy.sh "$env"; then
        echo "$(date '+%Y-%m-%d %H:%M:%S') Deployment to $env successful"

        # Health check
        sleep 30
        if curl -f "$HEALTH_CHECK_URL" > /dev/null 2>&1; then
            echo "$(date '+%Y-%m-%d %H:%M:%S') Health check passed for $env"
            return 0
        else
            echo "$(date '+%Y-%m-%d %H:%M:%S') Health check failed for $env" >&2
            return 1
        fi
    else
        echo "$(date '+%Y-%m-%d %H:%M:%S') Deployment to $env failed" >&2
        return 1
    fi
}

# Only run during deployment hour
if [[ "$CURRENT_HOUR" -eq "$DEPLOYMENT_HOUR" ]]; then

    # Staging deployment
    if [[ "$CURRENT_MINUTE" -eq "$STAGING_DELAY" ]]; then
        deploy_to_environment "staging"
    fi

    # Production deployment (weekdays only)
    if [[ "$CURRENT_MINUTE" -eq "$((STAGING_DELAY + PRODUCTION_DELAY / 60))" ]] && [[ $(date +%u) -le 5 ]]; then
        if deploy_to_environment "staging"; then
            deploy_to_environment "production"
        else
            echo "$(date '+%Y-%m-%d %H:%M:%S') Skipping production deployment due to staging failure" >&2
            exit 1
        fi
    fi
fi

# Crontab entry:
# * 2 * * * /usr/local/bin/deploy-pipeline.sh
```

### System Maintenance Automation

```bash
#!/bin/bash
# /usr/local/bin/system-maintenance.sh

set -euo pipefail

# Maintenance tasks configuration
TASKS=(
    "update_packages"
    "clean_logs"
    "optimize_database"
    "backup_configs"
    "security_scan"
)

# Logging
LOG_FILE="/var/log/cron-jobs/system-maintenance.log"
exec 1> >(tee -a "$LOG_FILE")
exec 2>&1

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') [MAINTENANCE] $*"
}

update_packages() {
    log "Starting package updates"
    apt-get update
    apt-get upgrade -y
    apt-get autoremove -y
    apt-get autoclean
    log "Package updates completed"
}

clean_logs() {
    log "Starting log cleanup"

    # Rotate and compress logs older than 7 days
    find /var/log -name "*.log" -mtime +7 -exec gzip {} \;

    # Remove compressed logs older than 30 days
    find /var/log -name "*.gz" -mtime +30 -delete

    # Clean journal logs older than 30 days
    journalctl --vacuum-time=30d

    log "Log cleanup completed"
}

optimize_database() {
    log "Starting database optimization"

    # PostgreSQL optimization
    if systemctl is-active postgresql > /dev/null 2>&1; then
        sudo -u postgres psql -c "VACUUM ANALYZE;"
        log "PostgreSQL optimization completed"
    fi

    # MySQL optimization
    if systemctl is-active mysql > /dev/null 2>&1; then
        mysql -e "FLUSH TABLES; OPTIMIZE TABLE information_schema.*;"
        log "MySQL optimization completed"
    fi
}

backup_configs() {
    log "Starting configuration backup"

    BACKUP_DIR="/var/backups/configs/$(date +%Y%m%d)"
    mkdir -p "$BACKUP_DIR"

    # Backup critical configuration files
    tar -czf "$BACKUP_DIR/etc-configs.tar.gz" \
        /etc/nginx/ \
        /etc/apache2/ \
        /etc/ssh/ \
        /etc/cron.d/ \
        /etc/systemd/system/ \
        2>/dev/null || true

    log "Configuration backup completed"
}

security_scan() {
    log "Starting security scan"

    # Check for failed login attempts
    FAILED_LOGINS=$(journalctl --since "24 hours ago" | grep -c "Failed password" || echo "0")
    if [[ $FAILED_LOGINS -gt 10 ]]; then
        log "WARNING: $FAILED_LOGINS failed login attempts in last 24 hours"
    fi

    # Check for listening ports
    ss -tuln > "/tmp/listening-ports-$(date +%Y%m%d).txt"

    log "Security scan completed"
}

# Execute maintenance tasks
log "Starting system maintenance"

for task in "${TASKS[@]}"; do
    log "Executing task: $task"
    if "$task"; then
        log "Task $task completed successfully"
    else
        log "ERROR: Task $task failed"
    fi
done

log "System maintenance completed"

# Crontab entries:
# 0 3 * * 0 /usr/local/bin/system-maintenance.sh  # Weekly on Sunday
```

---

## Cross-References

**Related Documentation:**
- [Linux Systemd & Services](Linux%20Systemd%20&%20Services.md) - Timer units and service management
- [Linux Logging & Journald](Linux%20Logging%20&%20Journald.md) - Log management and monitoring
- [Linux System Administration](Linux%20System%20Administration.md) - User management and security
- [Linux Commands](Linux%20Commands.md) - Basic command reference
- [Linux Shell Scripting Essentials](Linux%20Shell%20Scripting%20Essentials.md) - Script automation

**Integration Points:**
- **Systemd Timers**: Modern alternative to cron with better logging and dependency management
- **Log Management**: Centralized logging for cron job monitoring and troubleshooting
- **Security**: User permissions, environment isolation, and audit logging
- **Automation**: DevOps pipelines, infrastructure as code, and container orchestration