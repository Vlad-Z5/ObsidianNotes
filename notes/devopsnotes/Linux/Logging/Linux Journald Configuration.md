# Linux Journald Configuration

**Journald configuration** controls how systemd journal collects, stores, and manages system logs.

## Main Configuration File

```bash
# Primary config: /etc/systemd/journald.conf
sudo vim /etc/systemd/journald.conf
```

## Production Configuration Example

```bash
# /etc/systemd/journald.conf
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
```

## Storage Options

```bash
# Storage modes
Storage=auto          # Store on disk if /var/log/journal exists
Storage=persistent    # Always store on disk
Storage=volatile      # Store in memory only (/run)
Storage=none          # Don't store logs
```

## Size Management

```bash
# System journal size limits
SystemMaxUse=4G       # Max total disk usage
SystemKeepFree=1G     # Min free space to maintain
SystemMaxFileSize=128M # Max size per journal file
SystemMaxFiles=100    # Max number of journal files

# Runtime journal size limits (memory/tmpfs)
RuntimeMaxUse=512M    # Max memory usage
RuntimeKeepFree=256M  # Min free memory to maintain
RuntimeMaxFileSize=64M # Max size per runtime file
RuntimeMaxFiles=50    # Max number of runtime files
```

## Time-Based Retention

```bash
# Automatic cleanup based on time
MaxRetentionSec=1month    # Delete entries older than 1 month
MaxFileSec=1week          # Rotate files weekly

# Time format examples
MaxRetentionSec=2weeks
MaxRetentionSec=30days
MaxRetentionSec=1year
MaxRetentionSec=0         # No time-based cleanup
```

## Rate Limiting

```bash
# Prevent log flooding
RateLimitIntervalSec=30s  # Time window for rate limiting
RateLimitBurst=10000      # Max messages in time window

# Disable rate limiting
RateLimitIntervalSec=0
```

## Log Forwarding

```bash
# Forward to traditional syslog
ForwardToSyslog=yes

# Forward to kernel log buffer
ForwardToKMsg=no

# Forward to console
ForwardToConsole=no

# Forward to wall (all logged-in users)
ForwardToWall=yes

# Control forwarding levels
MaxLevelSyslog=info       # Max level to forward to syslog
MaxLevelKMsg=notice       # Max level to forward to kmsg
MaxLevelConsole=info      # Max level to forward to console
MaxLevelWall=emerg        # Max level to broadcast to users
```

## Sealing and Security

```bash
# Enable sealing (cryptographic verification)
Seal=yes

# Split logs by user ID
SplitMode=uid

# Compression
Compress=yes              # Compress older journal files
```

## Apply Configuration Changes

```bash
# Restart journald to apply changes
sudo systemctl restart systemd-journald

# Or send signal to reload config
sudo systemctl reload systemd-journald

# Verify configuration
journalctl --verify
```

## Per-Service Configuration

```bash
# Create drop-in directory for specific configuration
sudo mkdir -p /etc/systemd/journald.conf.d/

# Create custom configuration
sudo tee /etc/systemd/journald.conf.d/custom.conf <<EOF
[Journal]
# Custom settings for production
SystemMaxUse=8G
MaxRetentionSec=3months
RateLimitBurst=20000
EOF
```

## Common Configurations

### High-Volume Server
```bash
[Journal]
Storage=persistent
SystemMaxUse=10G
SystemMaxFileSize=256M
MaxRetentionSec=3months
RateLimitBurst=50000
Compress=yes
```

### Development Environment
```bash
[Journal]
Storage=persistent
SystemMaxUse=1G
MaxRetentionSec=1week
RateLimitBurst=5000
ForwardToSyslog=no
```

### Security-Focused
```bash
[Journal]
Storage=persistent
Seal=yes
SplitMode=uid
MaxRetentionSec=1year
ForwardToSyslog=yes
MaxLevelStore=info
```

## Monitoring Configuration

```bash
# Check current settings
journalctl --show-cursor
journalctl --disk-usage

# View effective configuration
systemctl show systemd-journald

# Check journal status
systemctl status systemd-journald
```

## Troubleshooting Configuration

```bash
# Test configuration syntax
sudo systemd-analyze verify /etc/systemd/journald.conf

# Check if changes took effect
journalctl -u systemd-journald

# View current disk usage
journalctl --disk-usage

# Manual cleanup if needed
journalctl --vacuum-size=1G
journalctl --vacuum-time=30days
```

## Environment-Specific Examples

### Container Environment
```bash
[Journal]
Storage=volatile
RuntimeMaxUse=100M
ForwardToConsole=yes
```

### Embedded System
```bash
[Journal]
Storage=auto
SystemMaxUse=100M
MaxRetentionSec=7days
Compress=yes
```

### Log Aggregation Server
```bash
[Journal]
Storage=persistent
SystemMaxUse=50G
MaxRetentionSec=6months
ForwardToSyslog=yes
RateLimitBurst=100000
```