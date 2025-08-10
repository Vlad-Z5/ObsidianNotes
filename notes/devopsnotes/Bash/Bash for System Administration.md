## Production System Administration Scripts

### Log Analysis and Monitoring
```bash
#!/bin/bash
# Production log analysis and alerting script

set -euo pipefail

# Configuration
readonly LOG_DIRS=("/var/log" "/opt/app/logs" "/var/log/nginx" "/var/log/apache2")
readonly ALERT_PATTERNS=("ERROR" "CRITICAL" "FATAL" "Out of memory" "Connection refused")
readonly TEMP_DIR="/tmp/log-analysis"
readonly REPORT_FILE="/var/log/log-analysis-report.txt"
readonly MAX_LOG_SIZE=100000000  # 100MB

# Colors for output
readonly RED='\033[0;31m'
readonly YELLOW='\033[1;33m'
readonly GREEN='\033[0;32m'
readonly NC='\033[0m'

log_info() { echo -e "[$(date '+%H:%M:%S')] ${GREEN}INFO${NC}: $*"; }
log_warn() { echo -e "[$(date '+%H:%M:%S')] ${YELLOW}WARN${NC}: $*"; }
log_error() { echo -e "[$(date '+%H:%M:%S')] ${RED}ERROR${NC}: $*"; }

# Analyze log files for patterns
analyze_logs() {
    local time_range="${1:-1}"  # Default to last 1 hour
    local output_file="$TEMP_DIR/analysis_$(date +%s).txt"
    
    mkdir -p "$TEMP_DIR"
    
    log_info "Analyzing logs from last $time_range hour(s)..."
    
    {
        echo "=== LOG ANALYSIS REPORT ==="
        echo "Timestamp: $(date)"
        echo "Analysis Period: Last $time_range hour(s)"
        echo "=================================="
        echo
    } > "$output_file"
    
    local total_issues=0
    
    for log_dir in "${LOG_DIRS[@]}"; do
        [[ ! -d "$log_dir" ]] && continue
        
        echo "Analyzing directory: $log_dir" >> "$output_file"
        echo "----------------------------------------" >> "$output_file"
        
        # Find log files modified in the last N hours
        while IFS= read -r -d '' log_file; do
            [[ ! -r "$log_file" ]] && continue
            
            # Skip binary files
            if file "$log_file" | grep -q "binary"; then
                continue
            fi
            
            local file_issues=0
            
            echo "File: $log_file" >> "$output_file"
            
            # Check for alert patterns
            for pattern in "${ALERT_PATTERNS[@]}"; do
                local matches
                matches=$(grep -c "$pattern" "$log_file" 2>/dev/null || echo "0")
                
                if [[ $matches -gt 0 ]]; then
                    echo "  $pattern: $matches occurrences" >> "$output_file"
                    
                    # Show sample lines with timestamp
                    echo "    Sample entries:" >> "$output_file"
                    grep "$pattern" "$log_file" | tail -3 | sed 's/^/      /' >> "$output_file"
                    
                    ((file_issues += matches))
                fi
            done
            
            # Check for unusual patterns
            check_unusual_patterns "$log_file" "$output_file"
            
            if [[ $file_issues -eq 0 ]]; then
                echo "  No issues found" >> "$output_file"
            else
                ((total_issues += file_issues))
            fi
            
            echo >> "$output_file"
            
        done < <(find "$log_dir" -name "*.log" -o -name "*.log.*" -not -name "*.gz" -mtime -"$time_range" -type f -print0 2>/dev/null)
    done
    
    # Summary
    {
        echo "=== SUMMARY ==="
        echo "Total issues found: $total_issues"
        echo "Report generated: $(date)"
    } >> "$output_file"
    
    # Copy to main report file
    cp "$output_file" "$REPORT_FILE"
    
    log_info "Analysis complete. Report saved to: $REPORT_FILE"
    
    # Alert if issues found
    if [[ $total_issues -gt 0 ]]; then
        log_warn "Found $total_issues issues in log files"
        return 1
    else
        log_info "No critical issues found"
        return 0
    fi
}

# Check for unusual patterns
check_unusual_patterns() {
    local log_file="$1"
    local output_file="$2"
    
    # Check for repeated IP addresses (potential attacks)
    local suspicious_ips
    suspicious_ips=$(grep -oE '\b([0-9]{1,3}\.){3}[0-9]{1,3}\b' "$log_file" 2>/dev/null | \
                    sort | uniq -c | sort -nr | head -5 | awk '$1 > 100 {print $2 " (" $1 " times)"}')
    
    if [[ -n "$suspicious_ips" ]]; then
        echo "  Suspicious IP activity:" >> "$output_file"
        echo "$suspicious_ips" | sed 's/^/    /' >> "$output_file"
    fi
    
    # Check for disk space warnings
    local disk_warnings
    disk_warnings=$(grep -i "disk\|space\|full" "$log_file" 2>/dev/null | wc -l)
    
    if [[ $disk_warnings -gt 0 ]]; then
        echo "  Disk space warnings: $disk_warnings" >> "$output_file"
    fi
    
    # Check for authentication failures
    local auth_failures
    auth_failures=$(grep -i "authentication\|login.*fail\|invalid.*user" "$log_file" 2>/dev/null | wc -l)
    
    if [[ $auth_failures -gt 0 ]]; then
        echo "  Authentication failures: $auth_failures" >> "$output_file"
    fi
}

# Rotate large log files
rotate_large_logs() {
    log_info "Checking for large log files..."
    
    local rotated_count=0
    
    for log_dir in "${LOG_DIRS[@]}"; do
        [[ ! -d "$log_dir" ]] && continue
        
        while IFS= read -r -d '' log_file; do
            local file_size
            file_size=$(stat -c%s "$log_file" 2>/dev/null || echo "0")
            
            if [[ $file_size -gt $MAX_LOG_SIZE ]]; then
                log_warn "Large log file detected: $log_file ($(($file_size / 1024 / 1024))MB)"
                
                # Create backup with timestamp
                local backup_name="${log_file}.$(date +%Y%m%d_%H%M%S)"
                
                if cp "$log_file" "$backup_name" && gzip "$backup_name"; then
                    # Truncate original file
                    > "$log_file"
                    log_info "Rotated: $log_file -> ${backup_name}.gz"
                    ((rotated_count++))
                else
                    log_error "Failed to rotate: $log_file"
                fi
            fi
            
        done < <(find "$log_dir" -name "*.log" -type f -print0 2>/dev/null)
    done
    
    log_info "Rotated $rotated_count large log files"
}

# Clean up old log files
cleanup_old_logs() {
    local days_old="${1:-7}"
    
    log_info "Cleaning up log files older than $days_old days..."
    
    local deleted_count=0
    
    for log_dir in "${LOG_DIRS[@]}"; do
        [[ ! -d "$log_dir" ]] && continue
        
        # Delete old compressed log files
        while IFS= read -r -d '' old_file; do
            if rm "$old_file" 2>/dev/null; then
                log_info "Deleted old log: $old_file"
                ((deleted_count++))
            fi
        done < <(find "$log_dir" -name "*.log.*.gz" -mtime +$days_old -type f -print0 2>/dev/null)
        
        # Delete old rotated files
        while IFS= read -r -d '' old_file; do
            if rm "$old_file" 2>/dev/null; then
                log_info "Deleted old rotated file: $old_file"
                ((deleted_count++))
            fi
        done < <(find "$log_dir" -name "*.log.[0-9]*" -mtime +$days_old -type f -print0 2>/dev/null)
    done
    
    log_info "Deleted $deleted_count old log files"
}
```

### User and Process Management
```bash
#!/bin/bash
# User and process management utilities

set -euo pipefail

# Process monitoring and management
monitor_processes() {
    local cpu_threshold="${1:-80}"
    local memory_threshold="${2:-80}"
    
    log_info "Monitoring processes (CPU > ${cpu_threshold}%, Memory > ${memory_threshold}%)"
    
    # Get high CPU processes
    local high_cpu_processes
    high_cpu_processes=$(ps aux --sort=-%cpu | awk -v threshold="$cpu_threshold" 'NR>1 && $3>threshold {print $2, $3, $4, $11}')
    
    if [[ -n "$high_cpu_processes" ]]; then
        log_warn "High CPU processes found:"
        echo "$high_cpu_processes" | while IFS= read -r line; do
            local pid cpu memory command
            read -r pid cpu memory command <<< "$line"
            echo "  PID: $pid, CPU: ${cpu}%, Memory: ${memory}%, Command: $command"
            
            # Get additional process info
            local process_info
            process_info=$(ps -p "$pid" -o pid,ppid,user,start,etime,command --no-headers 2>/dev/null || echo "Process not found")
            echo "    Details: $process_info"
        done
    fi
    
    # Get high memory processes
    local high_memory_processes
    high_memory_processes=$(ps aux --sort=-%mem | awk -v threshold="$memory_threshold" 'NR>1 && $4>threshold {print $2, $3, $4, $11}')
    
    if [[ -n "$high_memory_processes" ]]; then
        log_warn "High memory processes found:"
        echo "$high_memory_processes" | while IFS= read -r line; do
            local pid cpu memory command
            read -r pid cpu memory command <<< "$line"
            echo "  PID: $pid, CPU: ${cpu}%, Memory: ${memory}%, Command: $command"
        done
    fi
}

# Kill processes by pattern
kill_processes_by_pattern() {
    local pattern="$1"
    local signal="${2:-TERM}"
    local dry_run="${3:-false}"
    
    log_info "Finding processes matching pattern: $pattern"
    
    local matching_pids
    matching_pids=$(pgrep -f "$pattern" 2>/dev/null || true)
    
    if [[ -z "$matching_pids" ]]; then
        log_info "No processes found matching pattern: $pattern"
        return 0
    fi
    
    log_warn "Found matching processes:"
    echo "$matching_pids" | while read -r pid; do
        local process_info
        process_info=$(ps -p "$pid" -o pid,user,command --no-headers 2>/dev/null || echo "Process not found")
        echo "  $process_info"
    done
    
    if [[ "$dry_run" == "true" ]]; then
        log_info "DRY RUN: Would send $signal signal to ${#matching_pids[@]} processes"
        return 0
    fi
    
    # Confirm before killing (except for TERM signal)
    if [[ "$signal" != "TERM" ]]; then
        echo -n "Send $signal signal to these processes? [y/N]: "
        read -r confirmation
        if [[ "$confirmation" != [Yy] ]]; then
            log_info "Operation cancelled"
            return 0
        fi
    fi
    
    # Kill processes
    local killed_count=0
    echo "$matching_pids" | while read -r pid; do
        if kill -"$signal" "$pid" 2>/dev/null; then
            log_info "Sent $signal signal to PID $pid"
            ((killed_count++))
        else
            log_error "Failed to send signal to PID $pid"
        fi
    done
    
    log_info "Sent $signal signal to $killed_count processes"
}

# User session management
manage_user_sessions() {
    log_info "Current user sessions:"
    
    # Show logged in users
    who -u | while IFS= read -r line; do
        echo "  $line"
    done
    
    # Show idle sessions
    log_info "Idle sessions (>1 hour):"
    who -u | awk '$6 ~ /[0-9][0-9]:[0-9][0-9]/ && $6 > "01:00" {print "  Idle user:", $1, "Terminal:", $2, "Idle:", $6}'
    
    # Show failed login attempts
    log_info "Recent failed login attempts:"
    lastb -n 10 2>/dev/null | head -10 | while IFS= read -r line; do
        echo "  $line"
    done || log_info "No failed login records available"
}

# System resource cleanup
cleanup_system_resources() {
    log_info "Starting system resource cleanup..."
    
    # Clean package cache
    if command -v apt-get >/dev/null 2>&1; then
        log_info "Cleaning APT cache..."
        apt-get clean
        apt-get autoclean
        apt-get autoremove -y
    elif command -v yum >/dev/null 2>&1; then
        log_info "Cleaning YUM cache..."
        yum clean all
    fi
    
    # Clean temporary files
    log_info "Cleaning temporary files..."
    local temp_dirs=("/tmp" "/var/tmp")
    
    for temp_dir in "${temp_dirs[@]}"; do
        if [[ -d "$temp_dir" ]]; then
            # Remove files older than 7 days
            find "$temp_dir" -type f -atime +7 -delete 2>/dev/null || true
            # Remove empty directories
            find "$temp_dir" -type d -empty -delete 2>/dev/null || true
        fi
    done
    
    # Clean system logs if they're too large
    rotate_large_logs
    
    # Clean user cache directories
    log_info "Cleaning user cache directories..."
    find /home -name ".cache" -type d 2>/dev/null | while IFS= read -r cache_dir; do
        local cache_size
        cache_size=$(du -sm "$cache_dir" 2>/dev/null | cut -f1)
        
        if [[ $cache_size -gt 100 ]]; then  # Larger than 100MB
            log_info "Large cache directory found: $cache_dir (${cache_size}MB)"
            # Clean files older than 30 days
            find "$cache_dir" -type f -atime +30 -delete 2>/dev/null || true
        fi
    done
    
    log_info "System cleanup completed"
}
```

### Network and Security Operations
```bash
#!/bin/bash
# Network and security administration tools

# Network connection monitoring
monitor_network_connections() {
    log_info "Monitoring network connections..."
    
    # Show listening ports
    log_info "Listening ports:"
    netstat -tlnp 2>/dev/null | grep LISTEN | while IFS= read -r line; do
        local proto port process
        proto=$(echo "$line" | awk '{print $1}')
        port=$(echo "$line" | awk '{print $4}' | rev | cut -d: -f1 | rev)
        process=$(echo "$line" | awk '{print $7}')
        
        echo "  Port $port/$proto - Process: ${process:-unknown}"
    done
    
    # Show established connections
    log_info "Active connections (top 10):"
    netstat -tn 2>/dev/null | grep ESTABLISHED | head -10 | while IFS= read -r line; do
        echo "  $line"
    done
    
    # Check for suspicious connections
    log_info "Checking for suspicious connections..."
    
    # Connections to unusual ports
    netstat -tn 2>/dev/null | grep ESTABLISHED | \
    awk '{print $5}' | cut -d: -f2 | sort | uniq -c | sort -nr | \
    while read -r count port; do
        if [[ $count -gt 10 ]] && [[ $port -gt 1024 ]] && [[ $port -ne 22 ]] && [[ $port -ne 80 ]] && [[ $port -ne 443 ]]; then
            log_warn "Many connections to port $port: $count connections"
        fi
    done
    
    # Check for connections to foreign countries (requires geoip)
    if command -v geoiplookup >/dev/null 2>&1; then
        log_info "Foreign connections:"
        netstat -tn 2>/dev/null | grep ESTABLISHED | \
        awk '{print $5}' | cut -d: -f1 | sort -u | \
        while read -r ip; do
            local country
            country=$(geoiplookup "$ip" 2>/dev/null | cut -d: -f2 | sed 's/^ *//')
            if [[ -n "$country" ]] && [[ "$country" != *"United States"* ]] && [[ "$country" != *"Private"* ]]; then
                echo "  $ip - $country"
            fi
        done
    fi
}

# Firewall management
manage_firewall() {
    local action="$1"
    local port="${2:-}"
    local protocol="${3:-tcp}"
    
    case "$action" in
        "status")
            log_info "Firewall status:"
            if command -v ufw >/dev/null 2>&1; then
                ufw status verbose
            elif command -v firewall-cmd >/dev/null 2>&1; then
                firewall-cmd --list-all
            elif command -v iptables >/dev/null 2>&1; then
                iptables -L -n
            else
                log_error "No supported firewall found"
            fi
            ;;
        "allow")
            [[ -z "$port" ]] && { log_error "Port number required"; return 1; }
            log_info "Allowing port $port/$protocol"
            
            if command -v ufw >/dev/null 2>&1; then
                ufw allow "$port/$protocol"
            elif command -v firewall-cmd >/dev/null 2>&1; then
                firewall-cmd --permanent --add-port="$port/$protocol"
                firewall-cmd --reload
            else
                iptables -A INPUT -p "$protocol" --dport "$port" -j ACCEPT
            fi
            ;;
        "deny")
            [[ -z "$port" ]] && { log_error "Port number required"; return 1; }
            log_info "Denying port $port/$protocol"
            
            if command -v ufw >/dev/null 2>&1; then
                ufw deny "$port/$protocol"
            elif command -v firewall-cmd >/dev/null 2>&1; then
                firewall-cmd --permanent --remove-port="$port/$protocol"
                firewall-cmd --reload
            else
                iptables -A INPUT -p "$protocol" --dport "$port" -j DROP
            fi
            ;;
        *)
            log_error "Invalid action. Use: status, allow, deny"
            return 1
            ;;
    esac
}

# Security audit
security_audit() {
    log_info "Running security audit..."
    
    # Check for world-writable files
    log_info "Checking for world-writable files..."
    find / -type f -perm -002 2>/dev/null | head -20 | while IFS= read -r file; do
        log_warn "World-writable file: $file"
    done
    
    # Check for SUID/SGID files
    log_info "Checking for SUID/SGID files..."
    find / -type f \( -perm -4000 -o -perm -2000 \) 2>/dev/null | while IFS= read -r file; do
        local perms
        perms=$(ls -l "$file" | awk '{print $1}')
        echo "  $file - $perms"
    done
    
    # Check password policy
    log_info "Password policy check:"
    if [[ -f /etc/login.defs ]]; then
        grep -E "PASS_MAX_DAYS|PASS_MIN_DAYS|PASS_WARN_AGE" /etc/login.defs
    fi
    
    # Check for users with empty passwords
    log_info "Checking for users with empty passwords..."
    awk -F: '$2 == "" {print "User with empty password:", $1}' /etc/shadow 2>/dev/null || \
        log_info "Cannot read /etc/shadow (normal for non-root users)"
    
    # Check for duplicate UIDs
    log_info "Checking for duplicate UIDs..."
    awk -F: '{print $3}' /etc/passwd | sort | uniq -d | while read -r uid; do
        log_warn "Duplicate UID found: $uid"
        awk -F: -v uid="$uid" '$3 == uid {print "  User:", $1}' /etc/passwd
    done
    
    # Check SSH configuration
    if [[ -f /etc/ssh/sshd_config ]]; then
        log_info "SSH security check:"
        
        # Check if root login is disabled
        if grep -q "^PermitRootLogin no" /etc/ssh/sshd_config; then
            echo "  ✅ Root login disabled"
        else
            log_warn "Root login may be enabled"
        fi
        
        # Check if password authentication is disabled
        if grep -q "^PasswordAuthentication no" /etc/ssh/sshd_config; then
            echo "  ✅ Password authentication disabled"
        else
            log_warn "Password authentication may be enabled"
        fi
        
        # Check protocol version
        if grep -q "^Protocol 2" /etc/ssh/sshd_config; then
            echo "  ✅ SSH Protocol 2 configured"
        else
            log_warn "SSH protocol version not explicitly set to 2"
        fi
    fi
    
    log_info "Security audit completed"
}

# Main system administration menu
main() {
    local action="${1:-menu}"
    
    case "$action" in
        "logs")
            analyze_logs "${2:-1}"
            ;;
        "processes")
            monitor_processes "${2:-80}" "${3:-80}"
            ;;
        "network")
            monitor_network_connections
            ;;
        "security")
            security_audit
            ;;
        "cleanup")
            cleanup_system_resources
            ;;
        "firewall")
            manage_firewall "${2:-status}" "${3:-}" "${4:-tcp}"
            ;;
        "menu"|*)
            cat <<EOF
System Administration Tools

Usage: $0 <command> [options]

Commands:
  logs [hours]              - Analyze log files (default: last 1 hour)
  processes [cpu%] [mem%]   - Monitor high resource processes
  network                   - Monitor network connections
  security                  - Run security audit
  cleanup                   - Clean up system resources
  firewall <action> [port]  - Manage firewall (status/allow/deny)

Examples:
  $0 logs 24              # Analyze logs from last 24 hours
  $0 processes 90 95      # Show processes using >90% CPU or >95% memory
  $0 firewall allow 8080  # Allow port 8080
  $0 security             # Run security audit
EOF
            ;;
    esac
}

# Run main function if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
```

This provides comprehensive system administration capabilities with log analysis, process management, network monitoring, security auditing, and firewall management - all essential for production DevOps work.