# Linux Systemd Troubleshooting

**Systemd troubleshooting** involves systematic diagnosis of service failures, boot issues, dependency problems, and performance bottlenecks using systemctl, journalctl, and analysis tools.

## Service Failure Diagnosis

### Basic Service Status Check
```bash
# Check service status
systemctl status service_name
systemctl is-active service_name
systemctl is-enabled service_name
systemctl is-failed service_name

# Show detailed service information
systemctl show service_name
systemctl cat service_name

# Check service logs
journalctl -u service_name
journalctl -u service_name -f
journalctl -u service_name --since "1 hour ago"
```

### Service Won't Start

#### Check Unit File Syntax
```bash
# Verify unit file syntax
systemd-analyze verify service_name.service
systemctl cat service_name

# Check for syntax errors
systemctl daemon-reload 2>&1 | grep -i error

# Test unit file loading
systemctl show service_name --property=LoadState
systemctl show service_name --property=LoadError
```

#### Permission and Path Issues
```bash
# Check executable permissions
ls -la /path/to/executable
which executable_name

# Test as service user
sudo -u service_user /path/to/executable

# Check working directory
systemctl show service_name --property=WorkingDirectory
ls -la /working/directory

# Verify user and group exist
getent passwd service_user
getent group service_group
```

#### Dependency Issues
```bash
# Check dependencies
systemctl list-dependencies service_name
systemctl list-dependencies service_name --failed

# Check dependency status
systemctl status dependency.service
systemctl is-active dependency.service

# Start dependencies manually
systemctl start dependency.service
```

### Service Crashes Repeatedly

#### Analyze Crash Information
```bash
# Check exit codes and signals
systemctl status service_name
journalctl -u service_name --since "1 hour ago"

# Core dump analysis
coredumpctl list service_name
coredumpctl info service_name
coredumpctl debug service_name

# Check restart behavior
systemctl show service_name --property=Restart
systemctl show service_name --property=RestartSec
systemctl show service_name --property=StartLimitBurst
```

#### Resource-Related Crashes
```bash
# Check resource limits
systemctl show service_name --property=MemoryMax
systemctl show service_name --property=CPUQuota
systemctl show service_name --property=TasksMax

# Monitor resource usage
systemd-cgtop
systemctl show service_name --property=MemoryCurrent
systemctl show service_name --property=CPUUsageNSec

# Check for OOM kills
journalctl | grep -i "killed process\|out of memory"
dmesg | grep -i "killed process"
```

### Service Starts But Doesn't Work

#### Check Service Communication
```bash
# Verify service is listening
ss -tulpn | grep service_name
netstat -tulpn | grep service_name

# Test service endpoints
curl -v http://localhost:port/health
telnet localhost port

# Check firewall rules
iptables -L
ufw status
firewall-cmd --list-all
```

#### Environment and Configuration Issues
```bash
# Check environment variables
systemctl show service_name --property=Environment
systemctl show service_name --property=EnvironmentFiles

# Verify configuration files
systemctl show service_name --property=ExecStart
ls -la /etc/service/config.conf

# Test configuration
service_binary --test-config
service_binary --check-config
```

## Boot Issues

### Boot Process Analysis
```bash
# Overall boot analysis
systemd-analyze
systemd-analyze time
systemd-analyze blame

# Critical path analysis
systemd-analyze critical-chain
systemd-analyze critical-chain multi-user.target

# Visual boot chart
systemd-analyze plot > boot.svg
```

### Services Fail During Boot
```bash
# Check failed services at boot
systemctl --failed
journalctl -b | grep -i failed

# Boot-specific logs
journalctl -b 0          # Current boot
journalctl -b -1         # Previous boot
journalctl --list-boots  # Available boot logs

# Emergency boot options
systemctl emergency      # Emergency target
systemctl rescue         # Rescue target
```

### Boot Hangs or Timeouts
```bash
# Check for hanging jobs
systemctl list-jobs
systemctl cancel job_id

# Identify slow services
systemd-analyze blame | head -20
systemd-analyze critical-chain

# Timeout analysis
journalctl -b | grep -i timeout
systemctl show service_name --property=TimeoutStartSec
```

## Dependency Problems

### Circular Dependencies
```bash
# Detect circular dependencies
systemd-analyze verify service_name.service
systemd-analyze dot | grep -E "color=red|fontcolor=red"

# Analyze dependency chains
systemctl list-dependencies service_name --all
systemd-analyze critical-chain service_name
```

### Missing Dependencies
```bash
# Check for missing units
systemctl list-dependencies service_name | grep -i "not found"
systemctl show service_name --property=LoadError

# Verify required services exist
systemctl list-unit-files | grep dependency_name
ls /etc/systemd/system/dependency_name.service
```

## Resource and Performance Issues

### High Resource Usage
```bash
# Monitor system resources
systemd-cgtop
systemd-cgtop --order=memory
systemd-cgtop --order=cpu

# Service-specific resource monitoring
systemctl show service_name --property=MemoryCurrent
systemctl show service_name --property=CPUUsageNSec
systemctl show service_name --property=TasksCurrent

# I/O monitoring
systemctl show service_name --property=IOReadBytes
systemctl show service_name --property=IOWriteBytes
```

### Memory Issues
```bash
# Check for memory limits
systemctl show service_name --property=MemoryMax
systemctl show service_name --property=MemoryHigh

# Look for OOM conditions
journalctl | grep -i "out of memory\|oom"
dmesg | grep -i oom

# Memory usage history
journalctl -u service_name | grep -i memory
```

## Log Analysis for Troubleshooting

### Journal Analysis
```bash
# Service-specific log analysis
journalctl -u service_name --no-pager
journalctl -u service_name -o json-pretty
journalctl -u service_name --since "1 hour ago" --until "30 minutes ago"

# Error pattern analysis
journalctl -u service_name | grep -i error
journalctl -u service_name | grep -i "fail\|error\|exception"

# Boot log analysis
journalctl -b | grep service_name
journalctl -b -p err
```

### Log Filtering and Search
```bash
# Filter by priority
journalctl -u service_name -p err    # Error level and above
journalctl -u service_name -p warning # Warning level and above

# Filter by time
journalctl -u service_name --since today
journalctl -u service_name --since "2024-01-01 00:00:00"

# Follow logs in real-time
journalctl -u service_name -f
journalctl -u service_name -f --lines=0  # Only new entries
```

## Advanced Troubleshooting

### Debugging Service Startup
```bash
# Enable debug logging
systemctl edit service_name.service
# Add:
[Service]
Environment=DEBUG=1
Environment=RUST_LOG=debug
LogLevel=debug

# Trace service execution
strace -f -o /tmp/service.trace systemctl start service_name
```

### Systemd Debug Mode
```bash
# Enable systemd debug logging
systemctl edit systemd-journald
# Add:
[Service]
Environment=SYSTEMD_LOG_LEVEL=debug

# Boot with debug
# Add to kernel command line: systemd.log_level=debug
```

### Socket and Activation Issues
```bash
# Check socket activation
systemctl status service_name.socket
systemctl show service_name.socket --property=Listen*

# Test socket manually
nc localhost port
telnet localhost port

# Debug socket activation
journalctl -u service_name.socket -f
```

## Troubleshooting Scripts

### Comprehensive Service Debug Script
```bash
#!/bin/bash
# systemd-debug.sh

SERVICE="$1"
if [ -z "$SERVICE" ]; then
    echo "Usage: $0 <service_name>"
    exit 1
fi

echo "=== Systemd Debug Report for $SERVICE ==="
echo "Generated: $(date)"

echo -e "\n1. Service Status:"
systemctl status "$SERVICE" --no-pager -l

echo -e "\n2. Service Properties:"
systemctl show "$SERVICE" --no-pager

echo -e "\n3. Unit File Content:"
systemctl cat "$SERVICE"

echo -e "\n4. Dependencies:"
echo "Required:"
systemctl show "$SERVICE" --property=Requires --value
echo "Wanted:"
systemctl show "$SERVICE" --property=Wants --value
echo "After:"
systemctl show "$SERVICE" --property=After --value

echo -e "\n5. Dependency Status:"
systemctl list-dependencies "$SERVICE" --no-pager

echo -e "\n6. Recent Logs (Last 50 lines):"
journalctl -u "$SERVICE" -n 50 --no-pager

echo -e "\n7. Error Logs:"
journalctl -u "$SERVICE" -p err --no-pager

echo -e "\n8. Resource Usage:"
echo "Memory: $(systemctl show "$SERVICE" --property=MemoryCurrent --value) bytes"
echo "CPU Time: $(systemctl show "$SERVICE" --property=CPUUsageNSec --value) ns"
echo "Tasks: $(systemctl show "$SERVICE" --property=TasksCurrent --value)"

echo -e "\n9. Process Information:"
MAIN_PID=$(systemctl show "$SERVICE" --property=MainPID --value)
if [ "$MAIN_PID" != "0" ] && [ -n "$MAIN_PID" ]; then
    ps -p "$MAIN_PID" -o pid,ppid,user,cmd
fi

echo -e "\n10. System Context:"
echo "Failed services:"
systemctl --failed --no-legend --no-pager
echo "System load:"
uptime
```

### Boot Troubleshooting Script
```bash
#!/bin/bash
# boot-debug.sh

echo "=== Boot Troubleshooting Report ==="
echo "Generated: $(date)"

echo -e "\n1. Boot Time Analysis:"
systemd-analyze

echo -e "\n2. Slow Services:"
systemd-analyze blame | head -10

echo -e "\n3. Critical Chain:"
systemd-analyze critical-chain

echo -e "\n4. Failed Services:"
systemctl --failed --no-pager

echo -e "\n5. Boot Logs (Errors):"
journalctl -b -p err --no-pager

echo -e "\n6. Boot Jobs:"
systemctl list-jobs --no-pager

echo -e "\n7. Boot Messages:"
journalctl -b | grep -i "fail\|error\|timeout" | tail -20
```

### Performance Monitoring Script
```bash
#!/bin/bash
# systemd-performance.sh

echo "=== Systemd Performance Report ==="
echo "Generated: $(date)"

echo -e "\n1. Resource Usage by Service:"
systemd-cgtop --batch --iterations=1

echo -e "\n2. Memory Usage Top 10:"
systemctl list-units --type=service --state=active --no-legend | \
while read unit _; do
    memory=$(systemctl show "$unit" --property=MemoryCurrent --value)
    if [ "$memory" != "[not set]" ] && [ "$memory" -gt 0 ]; then
        echo "$((memory / 1024 / 1024)) MB - $unit"
    fi
done | sort -nr | head -10

echo -e "\n3. Failed Services:"
systemctl --failed --no-pager

echo -e "\n4. Services with Restart Issues:"
systemctl list-units --type=service --state=active --no-legend | \
while read unit _; do
    restarts=$(systemctl show "$unit" --property=NRestarts --value)
    if [ "$restarts" -gt 0 ]; then
        echo "$restarts restarts - $unit"
    fi
done | sort -nr
```

## Emergency Recovery

### Service Recovery Commands
```bash
# Reset failed state
systemctl reset-failed service_name
systemctl reset-failed

# Force restart
systemctl kill service_name
systemctl start service_name

# Bypass dependencies
systemctl --no-deps start service_name

# Emergency service stop
systemctl kill --kill-who=all service_name
```

### System Recovery
```bash
# Rescue mode
systemctl rescue

# Emergency mode
systemctl emergency

# Reload all unit files
systemctl daemon-reload

# Re-enable all services
systemctl preset-all
```