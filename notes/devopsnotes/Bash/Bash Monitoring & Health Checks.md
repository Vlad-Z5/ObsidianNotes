## Production Monitoring & Health Check Scripts

### Comprehensive Application Health Monitor
```bash
#!/bin/bash
# Production application health monitoring system

set -euo pipefail

# Configuration
readonly CONFIG_FILE="${BASH_SOURCE[0]%/*}/health-check.conf"
readonly STATE_DIR="/var/lib/health-checker"
readonly LOG_FILE="/var/log/health-checker.log"
readonly PID_FILE="/var/run/health-checker.pid"

# Default thresholds
DEFAULT_HTTP_TIMEOUT=10
DEFAULT_TCP_TIMEOUT=5
DEFAULT_RETRY_COUNT=3
DEFAULT_RETRY_DELAY=2

# Colors
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m'

# Initialize
mkdir -p "$STATE_DIR"

# Logging with rotation
log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    echo -e "${timestamp} [${level}] ${message}" | tee -a "$LOG_FILE"
    
    # Rotate log file if it gets too large (>50MB)
    if [[ -f "$LOG_FILE" ]] && [[ $(stat -c%s "$LOG_FILE" 2>/dev/null || stat -f%z "$LOG_FILE") -gt 52428800 ]]; then
        mv "$LOG_FILE" "${LOG_FILE}.old"
        echo "${timestamp} [INFO] Log file rotated" > "$LOG_FILE"
    fi
}

log_info() { log "${BLUE}INFO${NC}" "$@"; }
log_warn() { log "${YELLOW}WARN${NC}" "$@"; }
log_error() { log "${RED}ERROR${NC}" "$@"; }
log_success() { log "${GREEN}SUCCESS${NC}" "$@"; }

# Load configuration
load_config() {
    if [[ -f "$CONFIG_FILE" ]]; then
        source "$CONFIG_FILE"
        log_info "Configuration loaded from $CONFIG_FILE"
    else
        log_warn "No configuration file found at $CONFIG_FILE, using defaults"
    fi
}

# HTTP health check with advanced features
http_check() {
    local name="$1"
    local url="$2"
    local expected_status="${3:-200}"
    local timeout="${4:-$DEFAULT_HTTP_TIMEOUT}"
    local expected_content="${5:-}"
    local headers="${6:-}"
    
    local start_time=$(date +%s%N)
    local curl_opts=(-s -o /tmp/http_response_$$ -w "%{http_code}|%{time_total}|%{size_download}")
    
    # Add custom headers if provided
    if [[ -n "$headers" ]]; then
        while IFS=':' read -r header_name header_value; do
            curl_opts+=(-H "$header_name: $header_value")
        done <<< "$headers"
    fi
    
    local response
    response=$(curl "${curl_opts[@]}" --max-time "$timeout" "$url" 2>/dev/null || echo "000|0|0")
    
    local http_code time_total size_download
    IFS='|' read -r http_code time_total size_download <<< "$response"
    
    local end_time=$(date +%s%N)
    local response_time=$(( (end_time - start_time) / 1000000 ))  # Convert to milliseconds
    
    # Check HTTP status
    if [[ "$http_code" == "$expected_status" ]]; then
        # Check content if specified
        if [[ -n "$expected_content" ]]; then
            if grep -q "$expected_content" "/tmp/http_response_$$" 2>/dev/null; then
                log_success "$name: HTTP $http_code, ${response_time}ms, content match ✓"
                record_metric "$name" "http" "success" "$response_time" "$http_code"
                rm -f "/tmp/http_response_$$"
                return 0
            else
                log_error "$name: HTTP $http_code but content mismatch"
                record_metric "$name" "http" "content_mismatch" "$response_time" "$http_code"
                rm -f "/tmp/http_response_$$"
                return 1
            fi
        else
            log_success "$name: HTTP $http_code, ${response_time}ms"
            record_metric "$name" "http" "success" "$response_time" "$http_code"
            rm -f "/tmp/http_response_$$"
            return 0
        fi
    else
        log_error "$name: HTTP $http_code (expected $expected_status), ${response_time}ms"
        record_metric "$name" "http" "failed" "$response_time" "$http_code"
        
        # Log response body for debugging
        if [[ -f "/tmp/http_response_$$" ]]; then
            log_error "$name: Response body: $(head -c 500 /tmp/http_response_$$ | tr '\n' ' ')"
        fi
        
        rm -f "/tmp/http_response_$$"
        return 1
    fi
}

# TCP port check with connection timing
tcp_check() {
    local name="$1"
    local host="$2"
    local port="$3"
    local timeout="${4:-$DEFAULT_TCP_TIMEOUT}"
    
    local start_time=$(date +%s%N)
    
    if timeout "$timeout" bash -c "exec 3<>/dev/tcp/$host/$port" 2>/dev/null; then
        exec 3<&-
        exec 3>&-
        
        local end_time=$(date +%s%N)
        local response_time=$(( (end_time - start_time) / 1000000 ))
        
        log_success "$name: TCP connection to $host:$port successful, ${response_time}ms"
        record_metric "$name" "tcp" "success" "$response_time" "0"
        return 0
    else
        local end_time=$(date +%s%N)
        local response_time=$(( (end_time - start_time) / 1000000 ))
        
        log_error "$name: TCP connection to $host:$port failed, ${response_time}ms"
        record_metric "$name" "tcp" "failed" "$response_time" "1"
        return 1
    fi
}

# Database connectivity check
database_check() {
    local name="$1"
    local db_type="$2"
    local connection_string="$3"
    local test_query="${4:-SELECT 1}"
    
    local start_time=$(date +%s%N)
    
    case "$db_type" in
        "mysql"|"mariadb")
            if command -v mysql >/dev/null 2>&1; then
                if mysql --connect-timeout=5 -e "$test_query" "$connection_string" >/dev/null 2>&1; then
                    local end_time=$(date +%s%N)
                    local response_time=$(( (end_time - start_time) / 1000000 ))
                    log_success "$name: MySQL connection and query successful, ${response_time}ms"
                    record_metric "$name" "mysql" "success" "$response_time" "0"
                    return 0
                fi
            fi
            ;;
        "postgresql"|"postgres")
            if command -v psql >/dev/null 2>&1; then
                if PGCONNECT_TIMEOUT=5 psql "$connection_string" -c "$test_query" >/dev/null 2>&1; then
                    local end_time=$(date +%s%N)
                    local response_time=$(( (end_time - start_time) / 1000000 ))
                    log_success "$name: PostgreSQL connection and query successful, ${response_time}ms"
                    record_metric "$name" "postgresql" "success" "$response_time" "0"
                    return 0
                fi
            fi
            ;;
        "redis")
            if command -v redis-cli >/dev/null 2>&1; then
                if timeout 5 redis-cli -u "$connection_string" ping | grep -q PONG; then
                    local end_time=$(date +%s%N)
                    local response_time=$(( (end_time - start_time) / 1000000 ))
                    log_success "$name: Redis connection successful, ${response_time}ms"
                    record_metric "$name" "redis" "success" "$response_time" "0"
                    return 0
                fi
            fi
            ;;
    esac
    
    local end_time=$(date +%s%N)
    local response_time=$(( (end_time - start_time) / 1000000 ))
    log_error "$name: Database check failed, ${response_time}ms"
    record_metric "$name" "$db_type" "failed" "$response_time" "1"
    return 1
}

# Process check with resource monitoring
process_check() {
    local name="$1"
    local process_pattern="$2"
    local min_count="${3:-1}"
    local max_cpu="${4:-90}"
    local max_memory="${5:-90}"
    
    local pids
    pids=$(pgrep -f "$process_pattern" 2>/dev/null || true)
    
    if [[ -z "$pids" ]]; then
        log_error "$name: No processes found matching '$process_pattern'"
        record_metric "$name" "process" "not_found" "0" "0"
        return 1
    fi
    
    local process_count
    process_count=$(echo "$pids" | wc -w)
    
    if [[ $process_count -lt $min_count ]]; then
        log_error "$name: Only $process_count processes found (minimum: $min_count)"
        record_metric "$name" "process" "insufficient" "$process_count" "$min_count"
        return 1
    fi
    
    # Check resource usage for each process
    local high_resource_processes=0
    
    echo "$pids" | tr ' ' '\n' | while read -r pid; do
        [[ -z "$pid" ]] && continue
        
        local process_info
        process_info=$(ps -p "$pid" -o pid,pcpu,pmem,cmd --no-headers 2>/dev/null || continue)
        
        local cpu_usage memory_usage
        cpu_usage=$(echo "$process_info" | awk '{print $2}' | cut -d. -f1)
        memory_usage=$(echo "$process_info" | awk '{print $3}' | cut -d. -f1)
        
        if [[ ${cpu_usage:-0} -gt $max_cpu ]] || [[ ${memory_usage:-0} -gt $max_memory ]]; then
            log_warn "$name: High resource usage - PID $pid: CPU ${cpu_usage}%, Memory ${memory_usage}%"
            ((high_resource_processes++))
        fi
    done
    
    log_success "$name: $process_count processes running"
    record_metric "$name" "process" "success" "$process_count" "$high_resource_processes"
    return 0
}

# File system check
filesystem_check() {
    local name="$1"
    local path="$2"
    local expected_permissions="${3:-}"
    local expected_owner="${4:-}"
    local max_age_days="${5:-}"
    
    if [[ ! -e "$path" ]]; then
        log_error "$name: Path does not exist: $path"
        record_metric "$name" "filesystem" "not_found" "0" "1"
        return 1
    fi
    
    # Check permissions
    if [[ -n "$expected_permissions" ]]; then
        local actual_permissions
        actual_permissions=$(stat -c "%a" "$path" 2>/dev/null || stat -f "%Lp" "$path" 2>/dev/null)
        
        if [[ "$actual_permissions" != "$expected_permissions" ]]; then
            log_error "$name: Permission mismatch on $path: got $actual_permissions, expected $expected_permissions"
            record_metric "$name" "filesystem" "permission_mismatch" "0" "1"
            return 1
        fi
    fi
    
    # Check owner
    if [[ -n "$expected_owner" ]]; then
        local actual_owner
        actual_owner=$(stat -c "%U:%G" "$path" 2>/dev/null || stat -f "%Su:%Sg" "$path" 2>/dev/null)
        
        if [[ "$actual_owner" != "$expected_owner" ]]; then
            log_error "$name: Owner mismatch on $path: got $actual_owner, expected $expected_owner"
            record_metric "$name" "filesystem" "owner_mismatch" "0" "1"
            return 1
        fi
    fi
    
    # Check age
    if [[ -n "$max_age_days" ]] && [[ -f "$path" ]]; then
        local file_age_days
        file_age_days=$(( ($(date +%s) - $(stat -c "%Y" "$path" 2>/dev/null || stat -f "%m" "$path" 2>/dev/null)) / 86400 ))
        
        if [[ $file_age_days -gt $max_age_days ]]; then
            log_warn "$name: File is old: $path ($file_age_days days, max: $max_age_days)"
            record_metric "$name" "filesystem" "old_file" "$file_age_days" "$max_age_days"
        fi
    fi
    
    log_success "$name: Filesystem check passed for $path"
    record_metric "$name" "filesystem" "success" "0" "0"
    return 0
}

# Custom command check
command_check() {
    local name="$1"
    local command="$2"
    local expected_exit_code="${3:-0}"
    local timeout="${4:-30}"
    
    local start_time=$(date +%s%N)
    local output
    local exit_code
    
    output=$(timeout "$timeout" bash -c "$command" 2>&1) || exit_code=$?
    exit_code=${exit_code:-0}
    
    local end_time=$(date +%s%N)
    local execution_time=$(( (end_time - start_time) / 1000000 ))
    
    if [[ $exit_code -eq $expected_exit_code ]]; then
        log_success "$name: Command executed successfully, ${execution_time}ms"
        record_metric "$name" "command" "success" "$execution_time" "$exit_code"
        return 0
    else
        log_error "$name: Command failed with exit code $exit_code (expected $expected_exit_code), ${execution_time}ms"
        log_error "$name: Command output: $(echo "$output" | head -c 200)"
        record_metric "$name" "command" "failed" "$execution_time" "$exit_code"
        return 1
    fi
}

# Record metrics for monitoring systems
record_metric() {
    local service="$1"
    local check_type="$2"
    local status="$3"
    local response_time="$4"
    local extra_data="$5"
    
    local timestamp=$(date +%s)
    local metric_file="$STATE_DIR/metrics.txt"
    
    # Write metric in format: timestamp,service,type,status,response_time,extra_data
    echo "$timestamp,$service,$check_type,$status,$response_time,$extra_data" >> "$metric_file"
    
    # Send to Prometheus pushgateway if configured
    if [[ -n "${PUSHGATEWAY_URL:-}" ]]; then
        send_to_pushgateway "$service" "$check_type" "$status" "$response_time"
    fi
    
    # Keep only last 10000 metrics
    if [[ $(wc -l < "$metric_file" 2>/dev/null || echo 0) -gt 10000 ]]; then
        tail -n 10000 "$metric_file" > "${metric_file}.tmp"
        mv "${metric_file}.tmp" "$metric_file"
    fi
}

# Send metrics to Prometheus Pushgateway
send_to_pushgateway() {
    local service="$1"
    local check_type="$2"
    local status="$3"
    local response_time="$4"
    
    local success_value=0
    [[ "$status" == "success" ]] && success_value=1
    
    local payload=$(cat <<EOF
# HELP health_check_success Health check success status
# TYPE health_check_success gauge
health_check_success{service="$service",type="$check_type"} $success_value

# HELP health_check_response_time_ms Health check response time in milliseconds  
# TYPE health_check_response_time_ms gauge
health_check_response_time_ms{service="$service",type="$check_type"} $response_time
EOF
)
    
    curl -X POST --data-binary "$payload" \
         "${PUSHGATEWAY_URL}/metrics/job/health_checker/instance/$(hostname)" \
         >/dev/null 2>&1 || true
}

# Main health check runner with retry logic
run_health_check() {
    local check_config="$1"
    
    local name type url host port timeout expected_status expected_content headers
    local db_type connection_string test_query process_pattern min_count max_cpu max_memory
    local path permissions owner max_age_days command expected_exit_code
    local retry_count retry_delay
    
    # Parse check configuration (simple key=value format)
    while IFS='=' read -r key value; do
        case "$key" in
            name) name="$value" ;;
            type) type="$value" ;;
            url) url="$value" ;;
            host) host="$value" ;;
            port) port="$value" ;;
            timeout) timeout="$value" ;;
            expected_status) expected_status="$value" ;;
            expected_content) expected_content="$value" ;;
            headers) headers="$value" ;;
            db_type) db_type="$value" ;;
            connection_string) connection_string="$value" ;;
            test_query) test_query="$value" ;;
            process_pattern) process_pattern="$value" ;;
            min_count) min_count="$value" ;;
            max_cpu) max_cpu="$value" ;;
            max_memory) max_memory="$value" ;;
            path) path="$value" ;;
            permissions) permissions="$value" ;;
            owner) owner="$value" ;;
            max_age_days) max_age_days="$value" ;;
            command) command="$value" ;;
            expected_exit_code) expected_exit_code="$value" ;;
            retry_count) retry_count="$value" ;;
            retry_delay) retry_delay="$value" ;;
        esac
    done <<< "$check_config"
    
    # Set defaults
    retry_count=${retry_count:-$DEFAULT_RETRY_COUNT}
    retry_delay=${retry_delay:-$DEFAULT_RETRY_DELAY}
    
    local attempt=1
    local success=false
    
    while [[ $attempt -le $retry_count ]] && [[ "$success" != "true" ]]; do
        if [[ $attempt -gt 1 ]]; then
            log_info "$name: Retry attempt $attempt/$retry_count"
            sleep "$retry_delay"
        fi
        
        case "$type" in
            "http")
                if http_check "$name" "$url" "$expected_status" "$timeout" "$expected_content" "$headers"; then
                    success=true
                fi
                ;;
            "tcp")
                if tcp_check "$name" "$host" "$port" "$timeout"; then
                    success=true
                fi
                ;;
            "database")
                if database_check "$name" "$db_type" "$connection_string" "$test_query"; then
                    success=true
                fi
                ;;
            "process")
                if process_check "$name" "$process_pattern" "$min_count" "$max_cpu" "$max_memory"; then
                    success=true
                fi
                ;;
            "filesystem")
                if filesystem_check "$name" "$path" "$permissions" "$owner" "$max_age_days"; then
                    success=true
                fi
                ;;
            "command")
                if command_check "$name" "$command" "$expected_exit_code" "$timeout"; then
                    success=true
                fi
                ;;
            *)
                log_error "$name: Unknown check type: $type"
                return 1
                ;;
        esac
        
        ((attempt++))
    done
    
    if [[ "$success" != "true" ]]; then
        log_error "$name: All $retry_count attempts failed"
        return 1
    fi
    
    return 0
}

# Generate health report
generate_health_report() {
    local report_file="${1:-$STATE_DIR/health_report_$(date +%Y%m%d_%H%M%S).txt}"
    
    {
        echo "=== HEALTH CHECK REPORT ==="
        echo "Generated: $(date)"
        echo "Hostname: $(hostname)"
        echo "=============================="
        echo
        
        # Read recent metrics
        if [[ -f "$STATE_DIR/metrics.txt" ]]; then
            local total_checks passed_checks failed_checks
            local last_hour_timestamp=$(($(date +%s) - 3600))
            
            total_checks=$(awk -F',' -v ts="$last_hour_timestamp" '$1 >= ts' "$STATE_DIR/metrics.txt" | wc -l)
            passed_checks=$(awk -F',' -v ts="$last_hour_timestamp" '$1 >= ts && $4 == "success"' "$STATE_DIR/metrics.txt" | wc -l)
            failed_checks=$((total_checks - passed_checks))
            
            echo "Last Hour Summary:"
            echo "  Total Checks: $total_checks"
            echo "  Passed: $passed_checks"
            echo "  Failed: $failed_checks"
            echo "  Success Rate: $(( passed_checks * 100 / (total_checks > 0 ? total_checks : 1) ))%"
            echo
            
            echo "Service Status:"
            awk -F',' -v ts="$last_hour_timestamp" '$1 >= ts' "$STATE_DIR/metrics.txt" | \
            sort -t',' -k2,2 -k1,1nr | \
            awk -F',' '!seen[$2]++ {printf "  %-20s %-10s %s\n", $2, $4, ($4=="success" ? "✅" : "❌")}'
        fi
        
    } > "$report_file"
    
    echo "Health report generated: $report_file"
    return 0
}

# Main execution
main() {
    local action="${1:-check}"
    
    case "$action" in
        "daemon")
            # Run as daemon
            if [[ -f "$PID_FILE" ]] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
                log_error "Health checker daemon is already running"
                exit 1
            fi
            
            echo $$ > "$PID_FILE"
            log_info "Starting health checker daemon"
            
            trap 'log_info "Stopping daemon"; rm -f "$PID_FILE"; exit 0' TERM INT
            
            while true; do
                main check
                sleep "${DAEMON_INTERVAL:-60}"
            done
            ;;
        "check")
            load_config
            
            local failed_checks=0
            local total_checks=0
            
            # Run predefined health checks from configuration
            if [[ -f "$CONFIG_FILE" ]]; then
                while IFS= read -r line; do
                    [[ "$line" =~ ^#.*$ ]] || [[ -z "$line" ]] && continue
                    
                    if [[ "$line" =~ ^\[.*\]$ ]]; then
                        # Start of new check section
                        if [[ $total_checks -gt 0 ]]; then
                            if ! run_health_check "$current_check"; then
                                ((failed_checks++))
                            fi
                        fi
                        
                        ((total_checks++))
                        current_check=""
                        continue
                    fi
                    
                    current_check+="$line"$'\n'
                done < "$CONFIG_FILE"
                
                # Run last check
                if [[ $total_checks -gt 0 ]] && [[ -n "$current_check" ]]; then
                    if ! run_health_check "$current_check"; then
                        ((failed_checks++))
                    fi
                fi
            fi
            
            log_info "Health checks completed: $((total_checks - failed_checks))/$total_checks passed"
            
            if [[ $failed_checks -gt 0 ]]; then
                exit 1
            fi
            ;;
        "report")
            generate_health_report "$2"
            ;;
        *)
            cat <<EOF
Health Check Monitor

Usage: $0 <command> [options]

Commands:
  check           - Run all health checks once
  daemon          - Run as daemon (continuous monitoring)
  report [file]   - Generate health report

Configuration file: $CONFIG_FILE
EOF
            ;;
    esac
}

# Run main function if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
```

This provides comprehensive monitoring capabilities with HTTP checks, database connectivity, process monitoring, filesystem validation, and custom command execution - all with proper metrics collection and reporting.