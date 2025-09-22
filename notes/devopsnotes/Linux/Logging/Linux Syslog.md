# Linux Syslog

**Syslog** is the traditional logging standard for Unix-like systems, providing structured logging with facilities and priorities.

## Syslog Overview

Syslog provides:
- Standardized message format
- Network-based log forwarding
- Facility and priority classification
- Text-based log files
- Integration with journald

## Rsyslog Configuration

```bash
# Main configuration file
/etc/rsyslog.conf

# Additional configuration directory
/etc/rsyslog.d/*.conf

# Check rsyslog status
systemctl status rsyslog
```

## Basic Rsyslog Configuration

```bash
# /etc/rsyslog.conf example
# Global directives
$ModLoad imuxsock    # provides support for local system logging
$ModLoad imklog      # provides kernel logging support

# Set default permissions
$FileOwner root
$FileGroup adm
$FileCreateMode 0640
$DirCreateMode 0755

# Log by facility and priority
auth,authpriv.*         /var/log/auth.log
*.*;auth,authpriv.none  /var/log/syslog
kern.*                  /var/log/kern.log
mail.*                  /var/log/mail.log
daemon.*                /var/log/daemon.log
user.*                  /var/log/user.log

# Emergency messages to all users
*.emerg                 :omusrmsg:*
```

## Syslog Facilities

```bash
# System facilities (0-15)
kern        # Kernel messages
user        # User-level messages
mail        # Mail system
daemon      # System daemons
auth        # Security/authorization
syslog      # Messages generated internally by syslogd
lpr         # Line printer subsystem
news        # Network news subsystem
uucp        # UUCP subsystem
cron        # Clock daemon
authpriv    # Security/authorization messages
ftp         # FTP daemon

# Local use facilities (16-23)
local0      # Local use facility 0
local1      # Local use facility 1
# ... through local7
```

## Syslog Priorities

```bash
# Priority levels (0-7)
emerg       # Emergency: system is unusable
alert       # Alert: action must be taken immediately
crit        # Critical: critical conditions
err         # Error: error conditions
warning     # Warning: warning conditions
notice      # Notice: normal but significant condition
info        # Informational: informational messages
debug       # Debug: debug-level messages
```

## Rsyslog Rules Syntax

```bash
# Basic syntax: facility.priority    action

# Examples
mail.*                  /var/log/mail.log        # All mail messages
kern.crit               /var/log/kernel-crit     # Critical kernel messages
*.info;mail.none        /var/log/messages        # All info+ except mail
auth.warning            @192.168.1.100:514      # Send auth warnings to remote
local0.*                /var/log/local0.log      # Local facility 0

# Multiple facilities
mail,daemon.*           /var/log/mail-daemon.log
auth,authpriv.*         /var/log/auth.log

# Priority ranges
*.info;*.!warn          /var/log/info-only.log   # Info level only
kern.warning;kern.!err  /var/log/kern-warn.log   # Warning only
```

## Remote Logging Configuration

### Send Logs to Remote Server

```bash
# In /etc/rsyslog.conf or /etc/rsyslog.d/remote.conf

# Send all logs to remote server (UDP)
*.*    @192.168.1.100:514

# Send all logs to remote server (TCP)
*.*    @@192.168.1.100:514

# Send specific facility to remote
mail.*    @log-server.company.com:514
local0.*  @@secure-log.company.com:514

# With specific template
$template RemoteFormat,"%timestamp% %hostname% %syslogtag% %msg%\n"
*.* @@192.168.1.100:514;RemoteFormat
```

### Receive Remote Logs

```bash
# In /etc/rsyslog.conf - enable network reception

# Enable UDP reception
$ModLoad imudp
$UDPServerRun 514
$UDPServerAddress 0.0.0.0

# Enable TCP reception
$ModLoad imtcp
$InputTCPServerRun 514

# Store remote logs separately
$template RemoteHost,"/var/log/remote/%hostname%/%programname%.log"
*.* ?RemoteHost
& stop  # Don't process further
```

## Custom Log Templates

```bash
# Define custom templates
$template CustomFormat,"%timestamp:::date-rfc3339% %hostname% %syslogtag% %msg%\n"
$template JSONFormat,"{\"timestamp\":\"%timestamp:::date-rfc3339%\",\"host\":\"%hostname%\",\"tag\":\"%syslogtag%\",\"message\":\"%msg%\"}\n"

# Use templates
*.info /var/log/custom.log;CustomFormat
local0.* /var/log/json.log;JSONFormat
```

## Log Rotation with Logrotate

```bash
# /etc/logrotate.d/rsyslog
/var/log/syslog
/var/log/mail.log
/var/log/kern.log
{
    daily
    rotate 7
    missingok
    notifempty
    compress
    delaycompress
    postrotate
        systemctl reload rsyslog
    endscript
}
```

## Application Logging to Syslog

### From Command Line

```bash
# Send message to syslog
logger "This is a test message"
logger -p local0.info "Application started"
logger -p daemon.warning "Service warning"
logger -t myapp "Application message with tag"

# From script
logger -p local1.notice "Backup completed successfully"
```

### From Applications

```bash
# C/C++ example
#include <syslog.h>
openlog("myapp", LOG_PID, LOG_LOCAL0);
syslog(LOG_INFO, "Application started");
closelog();

# Python example
import syslog
syslog.openlog("myapp", syslog.LOG_PID, syslog.LOG_LOCAL0)
syslog.syslog(syslog.LOG_INFO, "Application started")
```

## Debugging Syslog

```bash
# Test rsyslog configuration
rsyslogd -N1

# Check rsyslog status
systemctl status rsyslog

# View rsyslog logs
journalctl -u rsyslog

# Test log message
logger -p local0.info "Test message" && tail /var/log/syslog

# Debug rsyslog
rsyslogd -f /etc/rsyslog.conf -d

# Check listening ports
netstat -tulpn | grep rsyslog
```

## Common Syslog Files

```bash
# Standard log files
/var/log/syslog         # General system messages
/var/log/messages       # General system messages (RHEL/CentOS)
/var/log/auth.log       # Authentication messages
/var/log/kern.log       # Kernel messages
/var/log/mail.log       # Mail server logs
/var/log/daemon.log     # System daemon logs
/var/log/user.log       # User-level messages
/var/log/debug          # Debug messages
```

## Syslog Security

```bash
# Secure syslog configuration
# Set proper file permissions
$FileOwner root
$FileGroup adm
$FileCreateMode 0640
$DirCreateMode 0755

# Filter sensitive information
:msg, contains, "password" stop
:msg, contains, "secret" stop

# Rate limiting
$SystemLogRateLimitInterval 2
$SystemLogRateLimitBurst 50
```

## Performance Tuning

```bash
# Async processing
$MainMsgQueueType LinkedList
$MainMsgQueueFileName mainq
$MainMsgQueueMaxFileSize 100m
$MainMsgQueueSaveOnShutdown on
$MainMsgQueueWorkerThreads 3

# Batch processing
$ActionQueueType LinkedList
$ActionQueueFileName dbq
$ActionQueueMaxFileSize 100m
$ActionQueueSaveOnShutdown on
$ActionResumeRetryCount -1
```