# Linux Logging & Journald

**Linux logging** provides comprehensive system monitoring, troubleshooting, and audit capabilities through traditional syslog and modern systemd journal for production environments.


## Logging Architecture

### Linux Logging Stack

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

### Logging Components

**journald**: Systemd's logging daemon collecting all system logs
**rsyslog**: Traditional syslog daemon for compatibility and forwarding
**logrotate**: Automatic log rotation and cleanup
**auditd**: Security audit logging
**systemd-cat**: Bridge for sending logs to journal

### Log Destinations

```bash
# Log storage locations
/var/log/journal/            # Persistent journal storage
/run/log/journal/            # Runtime journal storage
/var/log/                    # Traditional log files
/var/log/syslog              # System messages
/var/log/auth.log            # Authentication logs
/var/log/kern.log            # Kernel messages
/var/log/audit/              # Audit logs
```

---

## Systemd Journal (journald)

### Journal Configuration

```bash
# Main configuration: /etc/systemd/journald.conf
cat << 'EOF' > /etc/systemd/journald.conf
[Journal]
# Storage configuration
Storage=persistent
Compress=yes
Seal=yes
SplitMode=uid

# Size limits
SystemMaxUse=4G
SystemKeepFree=1G
SystemMaxFileSize=128M
SystemMaxFiles=100
RuntimeMaxUse=512M
RuntimeKeepFree=256M

# Time-based retention
MaxRetentionSec=1month
MaxFileSec=1week

# Rate limiting
RateLimitIntervalSec=30s
RateLimitBurst=10000

# Forwarding
ForwardToSyslog=yes
ForwardToKMsg=no
ForwardToConsole=no
ForwardToWall=yes
MaxLevelStore=info
MaxLevelSyslog=info
MaxLevelKMsg=notice
MaxLevelConsole=info
MaxLevelWall=emerg

# Synchronization
SyncIntervalSec=5m
EOF

systemctl restart systemd-journald
```

### Journal Operations

```bash
# Basic journal queries
journalctl                             # All journal entries
journalctl -n 50                       # Last 50 entries
journalctl -f                          # Follow journal (tail -f)
journalctl --since today               # Today's entries
journalctl --since "2024-01-01 00:00:00"
journalctl --until "1 hour ago"
journalctl --since yesterday --until today

# Time-based filtering
journalctl --since "10 minutes ago"
journalctl --since "2024-01-01" --until "2024-01-31"
journalctl --boot                      # Current boot
journalctl --boot -1                   # Previous boot
journalctl --list-boots                # Available boot sessions

# Service-specific logs
journalctl -u nginx                    # Specific service
journalctl -u nginx --since today
journalctl -u nginx -f                 # Follow service logs
journalctl _SYSTEMD_UNIT=nginx.service # Alternative syntax

# Priority filtering
journalctl -p err                      # Error and above
journalctl -p warning..err             # Warning to error range
journalctl PRIORITY=3                  # Numeric priority (err=3)

# Advanced filtering
journalctl _PID=1234                   # By process ID
journalctl _UID=1000                   # By user ID
journalctl _COMM=sshd                  # By command name
journalctl /usr/bin/nginx              # By executable path
journalctl _HOSTNAME=server1           # By hostname
```

### Journal Output Formats

```bash
# Output format options
journalctl -o short                    # Default format
journalctl -o short-iso                # ISO timestamps
journalctl -o short-precise            # Microsecond precision
journalctl -o verbose                  # All available fields
journalctl -o json                     # JSON format
journalctl -o json-pretty              # Pretty JSON
journalctl -o cat                      # Message only
journalctl -o export                   # Binary export format

# Custom field extraction
journalctl -o json | jq -r '.MESSAGE'
journalctl --output-fields=MESSAGE,_PID,_COMM
```

### Journal Fields and Metadata

```bash
# Show all available fields
journalctl -N

# Common journal fields
_BOOT_ID                    # Boot session identifier
_MACHINE_ID                 # Machine identifier
_HOSTNAME                   # Hostname
_TRANSPORT                  # Transport mechanism
_PID, _UID, _GID           # Process identifiers
_COMM                       # Command name
_EXE                        # Executable path
_CMDLINE                    # Command line
_SYSTEMD_UNIT              # Systemd unit
_SOURCE_REALTIME_TIMESTAMP # Original timestamp
MESSAGE                     # Log message
PRIORITY                    # Syslog priority
SYSLOG_FACILITY            # Syslog facility
SYSLOG_IDENTIFIER          # Syslog identifier

# Custom filtering examples
journalctl _TRANSPORT=kernel          # Kernel messages
journalctl _TRANSPORT=stdout          # Service stdout
journalctl _TRANSPORT=syslog          # Syslog messages
journalctl SYSLOG_FACILITY=0          # Kernel facility
journalctl SYSLOG_FACILITY=10         # Security/authorization
```

### Journal Maintenance

```bash
# Journal disk usage
journalctl --disk-usage                # Current usage
du -sh /var/log/journal/               # Disk usage verification

# Journal verification
journalctl --verify                    # Verify journal integrity
journalctl --verify --quiet            # Silent verification

# Journal cleanup
journalctl --vacuum-time=2weeks        # Keep 2 weeks
journalctl --vacuum-size=1G            # Keep 1GB
journalctl --vacuum-files=10           # Keep 10 files
journalctl --rotate                    # Force rotation

# Manual journal rotation
systemctl kill --kill-who=main --signal=SIGUSR2 systemd-journald
```

---

## Traditional Syslog (rsyslog)

### Rsyslog Configuration

```bash
# Main configuration: /etc/rsyslog.conf
cat << 'EOF' > /etc/rsyslog.conf
# Global directives
$ModLoad imjournal
$ModLoad imklog
$ModLoad immark
$ModLoad imuxsock

# Journal input
$IMJournalStateFile imjournal.state
$IMJournalRatelimitInterval 600
$IMJournalRatelimitBurst 20000

# Default permissions
$FileOwner root
$FileGroup adm
$FileCreateMode 0640
$DirCreateMode 0755
$Umask 0022

# Default template
$ActionFileDefaultTemplate RSYSLOG_TraditionalFileFormat

# System logging rules
auth,authpriv.*                 /var/log/auth.log
*.*;auth,authpriv.none         -/var/log/syslog
daemon.*                       -/var/log/daemon.log
kern.*                         -/var/log/kern.log
lpr.*                          -/var/log/lpr.log
mail.*                         -/var/log/mail.log
user.*                         -/var/log/user.log

# Emergency messages to console
*.emerg                         :omusrmsg:*

# High-priority messages to specific log
*.=debug;*.=info;*.=notice;*.=warn    /var/log/messages

# Application-specific logging
local0.*                        /var/log/local0.log
local1.*                        /var/log/local1.log

# Remote logging
*.* @@log-server.company.com:514

# Include custom configurations
$IncludeConfig /etc/rsyslog.d/*.conf
EOF

systemctl restart rsyslog
```

### Advanced Rsyslog Features

```bash
# Custom rsyslog configuration: /etc/rsyslog.d/custom.conf
cat << 'EOF' > /etc/rsyslog.d/custom.conf
# Custom templates
$template CustomFormat,"%timegenerated% %HOSTNAME% %syslogtag% %msg%\n"
$template DynamicFile,"/var/log/%programname%.log"

# Application-specific logging
:programname, isequal, "nginx"          /var/log/nginx/nginx.log;CustomFormat
:programname, isequal, "mysql"          /var/log/mysql/mysql.log;CustomFormat

# Filtering by message content
:msg, contains, "ERROR"                 /var/log/errors.log
:msg, regex, "Failed login.*"           /var/log/security.log

# Property-based filtering
:hostname, isequal, "web-server"        /var/log/web-server.log
:syslogfacility-text, isequal, "mail"   /var/log/mail/mail.log

# High-performance queue
$WorkDirectory /var/spool/rsyslog
$ActionQueueFileName queue
$ActionQueueMaxDiskSpace 1g
$ActionQueueSaveOnShutdown on
$ActionQueueType LinkedList
$ActionResumeRetryCount -1

# TLS configuration for remote logging
$DefaultNetstreamDriver gtls
$ActionSendStreamDriverMode 1
$ActionSendStreamDriverAuthMode x509/name
$ActionSendStreamDriverPermittedPeer log-server.company.com
EOF
```

### Rsyslog Testing and Debugging

```bash
# Test rsyslog configuration
rsyslogd -N1                           # Check syntax
rsyslogd -f /etc/rsyslog.conf -N1      # Test specific config

# Debug mode
rsyslogd -dn                           # Debug, no fork
rsyslogd -d                            # Debug with fork

# Send test messages
logger "Test message"                   # Default facility
logger -p local0.info "Application message"
logger -t myapp "Tagged message"
logger -s "Message to stderr too"

# Manual syslog from applications
echo "<14>Test message" | nc -u localhost 514
```

---

## Log Management & Rotation

### Logrotate Configuration

```bash
# Main configuration: /etc/logrotate.conf
cat << 'EOF' > /etc/logrotate.conf
# Global settings
weekly
rotate 4
create
dateext
compress
delaycompress
notifempty
missingok

# Include custom configurations
include /etc/logrotate.d

# System logs
/var/log/wtmp {
    monthly
    create 0664 root utmp
    minsize 1M
    rotate 1
}

/var/log/btmp {
    missingok
    monthly
    create 0600 root utmp
    rotate 1
}
EOF

# Application-specific rotation: /etc/logrotate.d/nginx
cat << 'EOF' > /etc/logrotate.d/nginx
/var/log/nginx/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 www-data adm
    sharedscripts
    prerotate
        if [ -d /etc/logrotate.d/httpd-prerotate ]; then \
            run-parts /etc/logrotate.d/httpd-prerotate; \
        fi \
    endscript
    postrotate
        invoke-rc.d nginx rotate >/dev/null 2>&1
    endscript
}
EOF
```

### Advanced Log Rotation

```bash
# Application log rotation with custom scripts
cat << 'EOF' > /etc/logrotate.d/myapp
/var/log/myapp/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    copytruncate
    create 0644 myapp myapp

    # Size-based rotation
    size 100M

    # Custom scripts
    prerotate
        /usr/local/bin/myapp-pre-rotate.sh
    endscript

    postrotate
        /bin/kill -USR1 $(cat /var/run/myapp.pid 2>/dev/null) 2>/dev/null || true
        /usr/local/bin/backup-logs.sh /var/log/myapp/
    endscript
}
EOF

# Test logrotate
logrotate -d /etc/logrotate.conf        # Debug mode
logrotate -f /etc/logrotate.conf        # Force rotation
logrotate -v /etc/logrotate.conf        # Verbose output
```

### Custom Log Management Scripts

```bash
#!/bin/bash
# Log cleanup and archival script

set -euo pipefail

LOG_DIR="/var/log"
ARCHIVE_DIR="/backup/logs"
DAYS_TO_KEEP=30
COMPRESS_DAYS=7

# Create archive directory
mkdir -p "$ARCHIVE_DIR"

# Find and compress old logs
find "$LOG_DIR" -name "*.log" -mtime +"$COMPRESS_DAYS" -not -name "*.gz" -exec gzip {} \;

# Archive old compressed logs
find "$LOG_DIR" -name "*.log.gz" -mtime +"$DAYS_TO_KEEP" \
    -exec mv {} "$ARCHIVE_DIR/" \;

# Remove very old archives
find "$ARCHIVE_DIR" -name "*.log.gz" -mtime +90 -delete

# Log cleanup summary
echo "Log cleanup completed at $(date)"
echo "Disk usage: $(du -sh $LOG_DIR)"
```

---

## Centralized Logging

### ELK Stack Integration

```yaml
# docker-compose.yml for ELK stack
version: '3.8'

services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
    container_name: elasticsearch
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
    ports:
      - "9200:9200"
    volumes:
      - elasticsearch-data:/usr/share/elasticsearch/data

  logstash:
    image: docker.elastic.co/logstash/logstash:8.11.0
    container_name: logstash
    ports:
      - "5000:5000/tcp"
      - "5000:5000/udp"
      - "9600:9600"
    volumes:
      - ./logstash/pipeline:/usr/share/logstash/pipeline:ro
      - ./logstash/config:/usr/share/logstash/config:ro
    depends_on:
      - elasticsearch

  kibana:
    image: docker.elastic.co/kibana/kibana:8.11.0
    container_name: kibana
    ports:
      - "5601:5601"
    environment:
      ELASTICSEARCH_HOSTS: http://elasticsearch:9200
    depends_on:
      - elasticsearch

volumes:
  elasticsearch-data:
```

### Logstash Configuration

```ruby
# logstash/pipeline/logstash.conf
input {
  beats {
    port => 5044
  }

  syslog {
    port => 5000
    type => "syslog"
  }

  tcp {
    port => 5000
    type => "tcp"
  }

  udp {
    port => 5000
    type => "udp"
  }
}

filter {
  if [type] == "syslog" {
    grok {
      match => {
        "message" => "%{SYSLOGTIMESTAMP:timestamp} %{IPORHOST:host} %{DATA:program}(?:\[%{POSINT:pid}\])?: %{GREEDYDATA:message}"
      }
      overwrite => [ "message" ]
    }

    date {
      match => [ "timestamp", "MMM  d HH:mm:ss", "MMM dd HH:mm:ss" ]
    }
  }

  if [program] == "nginx" {
    grok {
      match => {
        "message" => '%{IPORHOST:remote_addr} - %{DATA:remote_user} \[%{HTTPDATE:time_local}\] "%{WORD:method} %{DATA:request} HTTP/%{NUMBER:http_version}" %{INT:status} %{INT:body_bytes_sent} "%{DATA:http_referer}" "%{DATA:http_user_agent}"'
      }
    }
  }

  # Add geographic information
  if [remote_addr] {
    geoip {
      source => "remote_addr"
      target => "geoip"
    }
  }
}

output {
  elasticsearch {
    hosts => ["elasticsearch:9200"]
    index => "logs-%{+YYYY.MM.dd}"
  }

  stdout {
    codec => rubydebug
  }
}
```

### Filebeat Configuration

```yaml
# filebeat.yml
filebeat.inputs:
- type: log
  enabled: true
  paths:
    - /var/log/*.log
    - /var/log/nginx/*.log
    - /var/log/mysql/*.log
  multiline.pattern: '^\d{4}-\d{2}-\d{2}'
  multiline.negate: true
  multiline.match: after

- type: journald
  enabled: true
  id: systemd-journal

- type: docker
  enabled: true
  containers.ids: "*"
  containers.path: "/var/lib/docker/containers"

processors:
- add_host_metadata:
    when.not.contains.tags: forwarded
- add_docker_metadata: ~

output.logstash:
  hosts: ["logstash:5044"]

output.elasticsearch:
  hosts: ["elasticsearch:9200"]
  index: "filebeat-%{+yyyy.MM.dd}"

logging.level: info
logging.to_files: true
logging.files:
  path: /var/log/filebeat
  name: filebeat
  keepfiles: 7
  permissions: 0644
```

---

## Application Logging

### Structured Logging

```bash
# JSON logging for applications
cat << 'EOF' > /etc/rsyslog.d/json-logs.conf
# JSON template
$template JSONFormat,"{ \"timestamp\": \"%timegenerated:::date-rfc3339%\", \"host\": \"%hostname%\", \"severity\": \"%syslogpriority-text%\", \"facility\": \"%syslogfacility-text%\", \"program\": \"%programname%\", \"message\": \"%msg:::drop-last-lf%\" }\n"

# Application-specific JSON logging
:programname, isequal, "myapp"          /var/log/myapp/app.json;JSONFormat
EOF
```

### Application Integration

```python
# Python logging configuration
import logging
import logging.handlers
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }

        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id

        if hasattr(record, 'request_id'):
            log_entry['request_id'] = record.request_id

        return json.dumps(log_entry)

# Configure logger
logger = logging.getLogger('myapp')
logger.setLevel(logging.INFO)

# Syslog handler
syslog_handler = logging.handlers.SysLogHandler(address='/dev/log')
syslog_handler.setFormatter(JSONFormatter())

# File handler with rotation
file_handler = logging.handlers.RotatingFileHandler(
    '/var/log/myapp/app.log',
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5
)
file_handler.setFormatter(JSONFormatter())

logger.addHandler(syslog_handler)
logger.addHandler(file_handler)

# Usage
logger.info("Application started", extra={'user_id': 123, 'request_id': 'abc-123'})
```

### Systemd Service Logging

```bash
# Send application logs to journal
systemd-cat -t myapp /usr/local/bin/myapp

# From within scripts
#!/bin/bash
exec > >(systemd-cat -t backup-script)
exec 2>&1

echo "Starting backup process"
# Script continues with all output going to journal
```

---

## Log Analysis & Monitoring

### Real-time Log Monitoring

```bash
# Real-time log analysis
tail -f /var/log/syslog | grep -i error
journalctl -f | grep -i "failed\|error\|critical"

# Multi-file monitoring
multitail /var/log/syslog /var/log/auth.log /var/log/nginx/access.log

# Advanced monitoring with awk
tail -f /var/log/nginx/access.log | awk '
{
    status = $9
    if (status >= 400) {
        print "Error: " $0
    }
}'
```

### Log Analysis Scripts

```bash
#!/bin/bash
# Comprehensive log analysis script

LOG_FILE="${1:-/var/log/syslog}"
TIME_RANGE="${2:-1 hour ago}"

echo "=== Log Analysis Report for $LOG_FILE ==="
echo "Time range: since $TIME_RANGE"
echo

# Error analysis
echo "=== ERROR SUMMARY ==="
journalctl --since "$TIME_RANGE" | grep -i error | \
    awk '{print $5}' | sort | uniq -c | sort -nr | head -10

echo -e "\n=== FAILED SERVICES ==="
systemctl --failed --no-legend

echo -e "\n=== SSH LOGIN ANALYSIS ==="
journalctl --since "$TIME_RANGE" -u ssh | grep -i "accepted\|failed" | \
    awk '/Accepted/ {print "✓ " $0} /Failed/ {print "✗ " $0}'

echo -e "\n=== DISK SPACE WARNINGS ==="
journalctl --since "$TIME_RANGE" | grep -i "no space\|disk full\|filesystem full"

echo -e "\n=== MEMORY ISSUES ==="
journalctl --since "$TIME_RANGE" | grep -i "out of memory\|oom\|killed process"

echo -e "\n=== NETWORK ISSUES ==="
journalctl --since "$TIME_RANGE" | grep -i "network\|connection refused\|timeout"

echo -e "\n=== TOP LOG PRODUCERS ==="
journalctl --since "$TIME_RANGE" --output=json | \
    jq -r '._COMM' | sort | uniq -c | sort -nr | head -10
```

### Automated Alerting

```bash
#!/bin/bash
# Log-based alerting script

WEBHOOK_URL="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
ALERT_PATTERNS="/etc/log-monitor/patterns.conf"

# Alert patterns configuration
cat << 'EOF' > /etc/log-monitor/patterns.conf
# Pattern format: PRIORITY|PATTERN|DESCRIPTION
CRITICAL|segfault|Application segmentation fault
HIGH|out of memory|System out of memory
HIGH|failed password|SSH authentication failure
MEDIUM|disk.*full|Disk space warning
MEDIUM|connection refused|Service connection refused
EOF

send_alert() {
    local priority="$1"
    local message="$2"
    local hostname=$(hostname)

    curl -X POST -H 'Content-type: application/json' \
        --data "{\"text\":\"[$priority] $hostname: $message\"}" \
        "$WEBHOOK_URL"
}

# Monitor journal for patterns
journalctl -f --output=cat | while read -r line; do
    while IFS='|' read -r priority pattern description; do
        [[ $priority =~ ^#.*$ ]] && continue  # Skip comments

        if echo "$line" | grep -qi "$pattern"; then
            send_alert "$priority" "$description: $line"
        fi
    done < "$ALERT_PATTERNS"
done
```

---

## Security & Audit Logging

### Auditd Configuration

```bash
# Configure audit system
cat << 'EOF' > /etc/audit/auditd.conf
# Log file configuration
log_file = /var/log/audit/audit.log
log_format = RAW
log_group = root
priority_boost = 4
flush = INCREMENTAL_ASYNC
freq = 50

# Log rotation
max_log_file = 100
num_logs = 10
max_log_file_action = ROTATE

# Space management
space_left = 100
space_left_action = SYSLOG
admin_space_left = 50
admin_space_left_action = SUSPEND
disk_full_action = SUSPEND
disk_error_action = SUSPEND
EOF

# Audit rules: /etc/audit/rules.d/audit.rules
cat << 'EOF' > /etc/audit/rules.d/audit.rules
# Delete all rules
-D

# Buffer size
-b 8192

# Failure mode (0=silent, 1=printk, 2=panic)
-f 1

# File access monitoring
-w /etc/passwd -p wa -k user_modification
-w /etc/group -p wa -k group_modification
-w /etc/shadow -p wa -k password_modification
-w /etc/sudoers -p wa -k sudo_modification
-w /etc/ssh/sshd_config -p wa -k ssh_config

# System call monitoring
-a always,exit -F arch=b64 -S adjtimex -S settimeofday -k time_change
-a always,exit -F arch=b32 -S adjtimex -S settimeofday -S stime -k time_change
-a always,exit -F arch=b64 -S clock_settime -k time_change
-a always,exit -F arch=b32 -S clock_settime -k time_change

# Network configuration monitoring
-a always,exit -F arch=b64 -S sethostname -S setdomainname -k network_change
-a always,exit -F arch=b32 -S sethostname -S setdomainname -k network_change

# Login monitoring
-w /var/log/faillog -p wa -k logins
-w /var/log/lastlog -p wa -k logins
-w /var/log/tallylog -p wa -k logins

# Process monitoring
-a always,exit -F arch=b64 -S execve -k process_execution
-a always,exit -F arch=b32 -S execve -k process_execution

# Make rules immutable
-e 2
EOF

systemctl restart auditd
```

### Security Log Analysis

```bash
# Audit log analysis
ausearch -k user_modification          # User modifications
ausearch -k password_modification      # Password changes
ausearch -k sudo_modification          # Sudo configuration changes
ausearch -k process_execution          # Process executions
ausearch -ts today -k logins           # Today's login events

# Failed login analysis
ausearch -m USER_LOGIN -sv no          # Failed logins
grep "Failed password" /var/log/auth.log | awk '{print $11}' | sort | uniq -c | sort -nr

# Privilege escalation monitoring
ausearch -m USER_ROLE_CHANGE           # Role changes
grep "sudo:" /var/log/auth.log | grep -v "pam_unix(sudo:session)"
```

---

## Performance & Optimization

### Log Performance Tuning

```bash
# Journal performance configuration
cat << 'EOF' > /etc/systemd/journald.conf
[Journal]
# Optimize for performance
Storage=persistent
Compress=yes
SyncIntervalSec=5m
RateLimitIntervalSec=10s
RateLimitBurst=10000

# Memory usage optimization
SystemMaxUse=2G
RuntimeMaxUse=256M
SystemMaxFileSize=64M
RuntimeMaxFileSize=32M

# Reduce write amplification
Seal=no
SplitMode=uid
EOF
```

### High-Volume Logging

```bash
# Rsyslog performance configuration
cat << 'EOF' > /etc/rsyslog.d/performance.conf
# High-performance configuration
$MainMsgQueueSize 50000
$MainMsgQueueHighWaterMark 40000
$MainMsgQueueLowWaterMark 20000
$MainMsgQueueDiscardMark 45000
$MainMsgQueueDiscardSeverity 8
$MainMsgQueueWorkerThreads 4
$MainMsgQueueType LinkedList
$MainMsgQueueSaveOnShutdown on

# Buffered writing
$ActionFileEnableSync off
$ActionFileDefaultTemplate RSYSLOG_FileFormat
$RepeatedMsgReduction on

# UDP reception buffer
$UDPServerRun 514
$UDPServerTimeRequery 30
$UDPServerAddress 0.0.0.0
EOF
```

---

## Troubleshooting

### Common Logging Issues

#### Journal Not Persistent

```bash
# Check journal storage
journalctl --disk-usage
ls -la /var/log/journal/

# Enable persistent storage
mkdir -p /var/log/journal
systemctl restart systemd-journald

# Verify configuration
grep Storage /etc/systemd/journald.conf
```

#### Missing Logs

```bash
# Check service status
systemctl status systemd-journald
systemctl status rsyslog

# Check log forwarding
grep ForwardToSyslog /etc/systemd/journald.conf

# Test logging
logger "Test message"
journalctl -n 5 | grep "Test message"
```

#### Performance Issues

```bash
# Monitor logging performance
iostat -x 1 | grep -E 'Device|journal'
iotop -o | grep journal

# Check journal metrics
journalctl --disk-usage
du -sh /var/log/journal/
```

### Diagnostic Tools

```bash
#!/bin/bash
# Logging system diagnostic script

echo "=== Logging System Diagnostics ==="

echo -e "\n1. Service Status:"
systemctl status systemd-journald --no-pager
systemctl status rsyslog --no-pager

echo -e "\n2. Journal Configuration:"
grep -v '^#\|^$' /etc/systemd/journald.conf

echo -e "\n3. Journal Storage:"
journalctl --disk-usage
df -h /var/log/

echo -e "\n4. Recent Errors:"
journalctl --since "1 hour ago" -p err --no-pager -n 5

echo -e "\n5. Log File Sizes:"
du -sh /var/log/* 2>/dev/null | sort -hr | head -10

echo -e "\n6. Active Log Writers:"
lsof +c 15 /var/log/* 2>/dev/null | head -10
```

---

## Best Practices

### Production Logging Configuration

```bash
# 1. Structured logging with JSON format
# 2. Centralized logging for distributed systems
# 3. Log rotation and retention policies
# 4. Security and audit logging
# 5. Performance monitoring and alerting
# 6. Regular log analysis and reporting
# 7. Backup and archival strategies
# 8. Log anonymization for privacy compliance
# 9. Real-time monitoring and alerting
# 10. Documentation and training
```

### Security Best Practices

```bash
# 1. Encrypt logs in transit and at rest
# 2. Implement proper access controls
# 3. Monitor for log tampering
# 4. Regular audit of logging configuration
# 5. Secure log storage and backup
# 6. Log integrity verification
# 7. Privacy-compliant logging
# 8. Incident response logging
# 9. Forensic log preservation
# 10. Compliance reporting
```

---

## Cross-References

### Essential Reading
- **[[Linux fundamental]]** - Core Linux concepts and system architecture
- **[[Linux Systemd & Services]]** - Service management and systemd integration
- **[[Linux Security]]** - Security auditing and compliance logging
- **[[Linux Commands]]** - Command-line tools for log management

### Advanced Topics
- **[[Linux System Administration]]** - System administration and monitoring
- **[[Linux Shell Scripting Essentials]]** - Automation scripts for log management
- **[[Linux Process Management]]** - Process monitoring and troubleshooting

### Quick Navigation
- **Getting Started**: Linux fundamental → Linux Logging & Journald → Linux Commands
- **System Administration**: Linux Logging & Journald → Linux Systemd & Services → Linux Security
- **Automation**: Linux Logging & Journald → Linux Shell Scripting Essentials → Linux System Administration

---

*This focused guide provides comprehensive logging knowledge essential for Linux system monitoring, troubleshooting, and security compliance in production environments.*