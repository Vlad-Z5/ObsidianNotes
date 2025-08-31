# Bash Troubleshooting

## System Information & Environment Analysis

### Environment Discovery Framework
```bash
#!/bin/bash
# System environment analyzer
system_info_collector() {
    local output_file="${1:-system_info.json}"
    
    cat > "$output_file" << 'EOF'
{
    "system": {
        "hostname": "$(hostname -f)",
        "kernel": "$(uname -r)",
        "os": "$(cat /etc/os-release | grep PRETTY_NAME | cut -d'=' -f2 | tr -d '\"')",
        "architecture": "$(uname -m)",
        "uptime": "$(uptime -p)",
        "load_average": "$(uptime | awk -F'load average:' '{ print $2 }')",
        "timezone": "$(timedatectl show --property=Timezone --value 2>/dev/null || date +%Z)"
    },
    "hardware": {
        "cpu_cores": "$(nproc)",
        "memory_total": "$(free -h | awk '/^Mem:/ {print $2}')",
        "memory_available": "$(free -h | awk '/^Mem:/ {print $7}')",
        "disk_usage": "$(df -h / | awk 'NR==2 {print $5}')",
        "swap_usage": "$(free -h | awk '/^Swap:/ {print $3}')"
    },
    "network": {
        "interfaces": "$(ip -4 addr show | grep -oP '(?<=inet\s)\d+(\.\d+){3}' | paste -sd ',')",
        "default_route": "$(ip route | grep default | awk '{print $3}')",
        "dns_servers": "$(grep nameserver /etc/resolv.conf | awk '{print $2}' | paste -sd ',')",
        "connectivity": "$(ping -c 1 8.8.8.8 >/dev/null 2>&1 && echo 'online' || echo 'offline')"
    },
    "processes": {
        "total": "$(ps aux | wc -l)",
        "running": "$(ps aux | awk '$8 ~ /^R/ {count++} END {print count+0}')",
        "zombie": "$(ps aux | awk '$8 ~ /^Z/ {count++} END {print count+0}')",
        "top_cpu": "$(ps aux --sort=-%cpu | head -6 | tail -5 | awk '{printf \"%s(%.1f%%) \", $11, $3}')"
    }
}
EOF

    # Process the template with actual values
    eval "cat << 'TEMPLATE' > ${output_file}.tmp
$(cat "$output_file")
TEMPLATE"
    mv "${output_file}.tmp" "$output_file"
    
    echo "System information collected: $output_file"
}
```

### Process & Resource Monitoring
```bash
#!/bin/bash
# Comprehensive process monitor
process_monitor() {
    local duration="${1:-60}"
    local interval="${2:-5}"
    local output_dir="process_monitor_$(date +%Y%m%d_%H%M%S)"
    
    mkdir -p "$output_dir"
    
    # CPU and memory monitoring
    monitor_resources() {
        echo "timestamp,cpu_usage,memory_usage,load_1m,load_5m,load_15m,disk_io_read,disk_io_write" > "$output_dir/resources.csv"
        
        for ((i=0; i<duration; i+=interval)); do
            timestamp=$(date '+%Y-%m-%d %H:%M:%S')
            cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | sed 's/%us,//')
            memory_usage=$(free | grep Mem | awk '{printf "%.1f", ($3/$2) * 100.0}')
            load_avg=$(uptime | awk -F'load average:' '{print $2}' | sed 's/,//g')
            disk_io=$(iostat -d 1 2 | tail -1 | awk '{print $3","$4}')
            
            echo "$timestamp,$cpu_usage,$memory_usage,$load_avg,$disk_io" >> "$output_dir/resources.csv"
            sleep "$interval"
        done
    }
    
    # Process tree monitoring
    monitor_processes() {
        echo "timestamp,pid,ppid,user,cpu,memory,command" > "$output_dir/processes.csv"
        
        for ((i=0; i<duration; i+=interval)); do
            timestamp=$(date '+%Y-%m-%d %H:%M:%S')
            ps -eo pid,ppid,user,%cpu,%mem,comm --sort=-%cpu | head -20 | tail -19 | \
            while read line; do
                echo "$timestamp,$line" >> "$output_dir/processes.csv"
            done
            sleep "$interval"
        done
    }
    
    # Network connection monitoring
    monitor_connections() {
        echo "timestamp,local_address,remote_address,state,pid,program" > "$output_dir/connections.csv"
        
        for ((i=0; i<duration; i+=interval)); do
            timestamp=$(date '+%Y-%m-%d %H:%M:%S')
            netstat -tupln | grep -E '^(tcp|udp)' | \
            while read line; do
                echo "$timestamp,$line" >> "$output_dir/connections.csv"
            done
            sleep "$interval"
        done
    }
    
    # Start monitoring in background
    monitor_resources &
    local res_pid=$!
    monitor_processes &
    local proc_pid=$!
    monitor_connections &
    local conn_pid=$!
    
    echo "Monitoring started for ${duration}s (PIDs: $res_pid, $proc_pid, $conn_pid)"
    echo "Output directory: $output_dir"
    
    # Wait for completion
    wait $res_pid $proc_pid $conn_pid
    echo "Monitoring completed. Data available in: $output_dir"
}
```

## Log Analysis & Debugging

### Advanced Log Parser
```bash
#!/bin/bash
# Multi-format log analyzer
log_analyzer() {
    local log_file="$1"
    local analysis_type="${2:-full}"
    local output_prefix="${3:-analysis}"
    
    if [[ ! -f "$log_file" ]]; then
        echo "Error: Log file '$log_file' not found"
        return 1
    fi
    
    # Error pattern detection
    analyze_errors() {
        echo "=== Error Analysis ===" > "${output_prefix}_errors.txt"
        echo "Error patterns found:" >> "${output_prefix}_errors.txt"
        
        local error_patterns=(
            'ERROR|Error|error'
            'FATAL|Fatal|fatal'
            'CRITICAL|Critical|critical'
            'EXCEPTION|Exception|exception'
            'FAILED|Failed|failed'
            'TIMEOUT|Timeout|timeout'
            'Connection refused'
            'Permission denied'
            'Out of memory'
            'Disk full'
        )
        
        for pattern in "${error_patterns[@]}"; do
            local count=$(grep -cE "$pattern" "$log_file" 2>/dev/null || echo 0)
            if [[ $count -gt 0 ]]; then
                echo "$pattern: $count occurrences" >> "${output_prefix}_errors.txt"
                echo "Sample entries:" >> "${output_prefix}_errors.txt"
                grep -E "$pattern" "$log_file" | head -5 | sed 's/^/  /' >> "${output_prefix}_errors.txt"
                echo "" >> "${output_prefix}_errors.txt"
            fi
        done
    }
    
    # Performance pattern analysis
    analyze_performance() {
        echo "=== Performance Analysis ===" > "${output_prefix}_performance.txt"
        
        # Response time analysis
        if grep -qE '\d+ms|\d+\.\d+s' "$log_file"; then
            echo "Response time patterns:" >> "${output_prefix}_performance.txt"
            grep -oE '\d+ms|\d+\.\d+s' "$log_file" | sort -n | uniq -c | sort -nr >> "${output_prefix}_performance.txt"
            echo "" >> "${output_prefix}_performance.txt"
        fi
        
        # Memory usage patterns
        if grep -qE '\d+MB|\d+GB' "$log_file"; then
            echo "Memory usage patterns:" >> "${output_prefix}_performance.txt"
            grep -oE '\d+MB|\d+GB' "$log_file" | sort -n | uniq -c | sort -nr >> "${output_prefix}_performance.txt"
            echo "" >> "${output_prefix}_performance.txt"
        fi
        
        # Slow query detection
        if grep -qi 'slow\|timeout\|delay' "$log_file"; then
            echo "Slow operation indicators:" >> "${output_prefix}_performance.txt"
            grep -iE 'slow|timeout|delay' "$log_file" | head -10 >> "${output_prefix}_performance.txt"
        fi
    }
    
    # Timeline analysis
    analyze_timeline() {
        echo "=== Timeline Analysis ===" > "${output_prefix}_timeline.txt"
        
        # Extract timestamps and create hourly breakdown
        if grep -qE '\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4}|\w{3}\s+\d{1,2}' "$log_file"; then
            echo "Activity by hour:" >> "${output_prefix}_timeline.txt"
            
            # Try different timestamp formats
            grep -oE '\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}|\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2}|\w{3} \d{1,2} \d{2}:\d{2}:\d{2}' "$log_file" | \
            cut -d' ' -f2 | cut -d':' -f1 | sort | uniq -c | sort -nr >> "${output_prefix}_timeline.txt"
        fi
    }
    
    # User activity analysis
    analyze_users() {
        echo "=== User Activity Analysis ===" > "${output_prefix}_users.txt"
        
        # IP address analysis
        if grep -qE '\d+\.\d+\.\d+\.\d+' "$log_file"; then
            echo "Top IP addresses:" >> "${output_prefix}_users.txt"
            grep -oE '\d+\.\d+\.\d+\.\d+' "$log_file" | sort | uniq -c | sort -nr | head -20 >> "${output_prefix}_users.txt"
            echo "" >> "${output_prefix}_users.txt"
        fi
        
        # User agent analysis
        if grep -qi 'user-agent\|mozilla\|chrome\|firefox' "$log_file"; then
            echo "User agent patterns:" >> "${output_prefix}_users.txt"
            grep -i 'user-agent' "$log_file" | cut -d'"' -f6 | sort | uniq -c | sort -nr | head -10 >> "${output_prefix}_users.txt"
        fi
    }
    
    # Execute analysis based on type
    case "$analysis_type" in
        "errors")
            analyze_errors
            ;;
        "performance")
            analyze_performance
            ;;
        "timeline")
            analyze_timeline
            ;;
        "users")
            analyze_users
            ;;
        "full")
            analyze_errors
            analyze_performance
            analyze_timeline
            analyze_users
            ;;
        *)
            echo "Unknown analysis type: $analysis_type"
            echo "Available types: errors, performance, timeline, users, full"
            return 1
            ;;
    esac
    
    echo "Log analysis completed. Output files: ${output_prefix}_*.txt"
}
```

### Debug Mode Framework
```bash
#!/bin/bash
# Advanced debugging framework
debug_framework() {
    local script_name="$1"
    local debug_level="${DEBUG_LEVEL:-1}"
    local debug_file="${DEBUG_FILE:-debug.log}"
    
    # Debug levels: 1=ERROR, 2=WARN, 3=INFO, 4=DEBUG, 5=TRACE
    debug() {
        local level="$1"
        local message="$2"
        local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
        local caller="${BASH_SOURCE[2]##*/}:${BASH_LINENO[1]}:${FUNCNAME[2]:-main}"
        
        local level_num
        case "$level" in
            ERROR) level_num=1 ;;
            WARN)  level_num=2 ;;
            INFO)  level_num=3 ;;
            DEBUG) level_num=4 ;;
            TRACE) level_num=5 ;;
            *) level_num=1; level="ERROR" ;;
        esac
        
        if [[ $level_num -le $debug_level ]]; then
            local color=""
            case "$level" in
                ERROR) color="\033[31m" ;;  # Red
                WARN)  color="\033[33m" ;;  # Yellow
                INFO)  color="\033[32m" ;;  # Green
                DEBUG) color="\033[36m" ;;  # Cyan
                TRACE) color="\033[35m" ;;  # Magenta
            esac
            
            # Console output with color
            echo -e "${color}[$timestamp] [$level] [$caller] $message\033[0m" >&2
            
            # File output without color
            echo "[$timestamp] [$level] [$caller] $message" >> "$debug_file"
        fi
    }
    
    # Function call tracer
    trace_function() {
        local func_name="${FUNCNAME[1]}"
        local args="$*"
        debug "TRACE" "ENTER: $func_name($args)"
        
        # Execute the function
        "$@"
        local result=$?
        
        debug "TRACE" "EXIT: $func_name -> $result"
        return $result
    }
    
    # Variable state tracer
    trace_vars() {
        local vars=("$@")
        for var in "${vars[@]}"; do
            if [[ -n "${!var:-}" ]]; then
                debug "TRACE" "VAR: $var=${!var}"
            else
                debug "TRACE" "VAR: $var=<unset>"
            fi
        done
    }
    
    # Command execution tracer
    trace_cmd() {
        local cmd="$*"
        debug "DEBUG" "CMD: $cmd"
        
        local start_time=$(date +%s.%N)
        "$@"
        local result=$?
        local end_time=$(date +%s.%N)
        local duration=$(echo "$end_time - $start_time" | bc -l)
        
        debug "DEBUG" "CMD_RESULT: $cmd -> $result (${duration}s)"
        return $result
    }
    
    # Performance profiler
    profile_block() {
        local block_name="$1"
        shift
        
        debug "INFO" "PROFILE_START: $block_name"
        local start_time=$(date +%s.%N)
        local start_memory=$(ps -o rss= $$)
        
        "$@"
        local result=$?
        
        local end_time=$(date +%s.%N)
        local end_memory=$(ps -o rss= $$)
        local duration=$(echo "$end_time - $start_time" | bc -l)
        local memory_diff=$((end_memory - start_memory))
        
        debug "INFO" "PROFILE_END: $block_name -> ${duration}s, ${memory_diff}KB memory"
        return $result
    }
    
    # Export debug functions
    export -f debug trace_function trace_vars trace_cmd profile_block
    export DEBUG_LEVEL debug_file
    
    debug "INFO" "Debug framework initialized (level=$debug_level, file=$debug_file)"
}
```

## Network Connectivity & Service Diagnostics

### Network Diagnostic Suite
```bash
#!/bin/bash
# Comprehensive network diagnostics
network_diagnostics() {
    local target="${1:-google.com}"
    local output_dir="network_diag_$(date +%Y%m%d_%H%M%S)"
    
    mkdir -p "$output_dir"
    
    # Basic connectivity test
    connectivity_test() {
        echo "=== Connectivity Test ===" | tee "$output_dir/connectivity.txt"
        
        # Ping test
        echo "Ping test to $target:" | tee -a "$output_dir/connectivity.txt"
        if ping -c 4 "$target" >> "$output_dir/connectivity.txt" 2>&1; then
            echo "✓ Ping successful" | tee -a "$output_dir/connectivity.txt"
        else
            echo "✗ Ping failed" | tee -a "$output_dir/connectivity.txt"
        fi
        
        # DNS resolution test
        echo -e "\nDNS resolution test:" | tee -a "$output_dir/connectivity.txt"
        if nslookup "$target" >> "$output_dir/connectivity.txt" 2>&1; then
            echo "✓ DNS resolution successful" | tee -a "$output_dir/connectivity.txt"
        else
            echo "✗ DNS resolution failed" | tee -a "$output_dir/connectivity.txt"
        fi
        
        # HTTP connectivity test
        echo -e "\nHTTP connectivity test:" | tee -a "$output_dir/connectivity.txt"
        if curl -s -o /dev/null -w "HTTP: %{http_code}, Time: %{time_total}s\n" "http://$target" >> "$output_dir/connectivity.txt" 2>&1; then
            echo "✓ HTTP connection successful" | tee -a "$output_dir/connectivity.txt"
        else
            echo "✗ HTTP connection failed" | tee -a "$output_dir/connectivity.txt"
        fi
    }
    
    # Port scan and service detection
    port_scan() {
        echo "=== Port Scan ===" | tee "$output_dir/ports.txt"
        
        local common_ports=(22 23 25 53 80 110 143 443 993 995)
        
        for port in "${common_ports[@]}"; do
            echo "Testing port $port..." | tee -a "$output_dir/ports.txt"
            if timeout 3 bash -c "echo >/dev/tcp/$target/$port" 2>/dev/null; then
                echo "✓ Port $port is open" | tee -a "$output_dir/ports.txt"
                
                # Service detection
                case $port in
                    22) echo "  - SSH service likely running" | tee -a "$output_dir/ports.txt" ;;
                    25) echo "  - SMTP service likely running" | tee -a "$output_dir/ports.txt" ;;
                    53) echo "  - DNS service likely running" | tee -a "$output_dir/ports.txt" ;;
                    80) echo "  - HTTP service likely running" | tee -a "$output_dir/ports.txt" ;;
                    443) echo "  - HTTPS service likely running" | tee -a "$output_dir/ports.txt" ;;
                esac
            else
                echo "✗ Port $port is closed/filtered" | tee -a "$output_dir/ports.txt"
            fi
        done
    }
    
    # Network interface analysis
    interface_analysis() {
        echo "=== Network Interface Analysis ===" | tee "$output_dir/interfaces.txt"
        
        # Interface information
        echo "Active interfaces:" | tee -a "$output_dir/interfaces.txt"
        ip addr show | tee -a "$output_dir/interfaces.txt"
        
        echo -e "\nRouting table:" | tee -a "$output_dir/interfaces.txt"
        ip route show | tee -a "$output_dir/interfaces.txt"
        
        echo -e "\nNetwork statistics:" | tee -a "$output_dir/interfaces.txt"
        cat /proc/net/dev | tee -a "$output_dir/interfaces.txt"
    }
    
    # Performance testing
    performance_test() {
        echo "=== Network Performance Test ===" | tee "$output_dir/performance.txt"
        
        # Bandwidth test using curl
        echo "Download speed test:" | tee -a "$output_dir/performance.txt"
        curl -o /dev/null -s -w "Speed: %{speed_download} bytes/sec\nTime: %{time_total}s\n" \
             "http://speedtest.tele2.net/1MB.zip" 2>/dev/null | tee -a "$output_dir/performance.txt"
        
        # Latency test
        echo -e "\nLatency test (10 pings):" | tee -a "$output_dir/performance.txt"
        ping -c 10 "$target" | grep "time=" | awk -F'time=' '{print $2}' | \
        awk '{sum+=$1; if(min==""){min=max=$1}; if($1>max) {max=$1}; if($1<min) {min=$1}} 
             END {print "Avg: " sum/NR "ms, Min: " min "ms, Max: " max "ms"}' | tee -a "$output_dir/performance.txt"
    }
    
    # Execute all tests
    connectivity_test
    port_scan
    interface_analysis
    performance_test
    
    echo "Network diagnostics completed. Results in: $output_dir"
}
```

### Service Health Checker
```bash
#!/bin/bash
# Comprehensive service health monitoring
service_health_monitor() {
    local services=("$@")
    local output_file="service_health_$(date +%Y%m%d_%H%M%S).json"
    
    # Default services if none specified
    if [[ ${#services[@]} -eq 0 ]]; then
        services=("ssh" "nginx" "docker" "postgresql" "redis" "elasticsearch")
    fi
    
    echo "{" > "$output_file"
    echo "  \"timestamp\": \"$(date -Iseconds)\"," >> "$output_file"
    echo "  \"hostname\": \"$(hostname)\"," >> "$output_file"
    echo "  \"services\": {" >> "$output_file"
    
    local first=true
    for service in "${services[@]}"; do
        [[ "$first" == true ]] && first=false || echo "," >> "$output_file"
        
        echo "    \"$service\": {" >> "$output_file"
        
        # Check if service exists
        if systemctl list-unit-files | grep -q "^$service.service"; then
            # Service status
            local status=$(systemctl is-active "$service" 2>/dev/null || echo "unknown")
            local enabled=$(systemctl is-enabled "$service" 2>/dev/null || echo "unknown")
            local uptime=$(systemctl show "$service" -p ActiveEnterTimestamp --value 2>/dev/null)
            
            echo "      \"exists\": true," >> "$output_file"
            echo "      \"status\": \"$status\"," >> "$output_file"
            echo "      \"enabled\": \"$enabled\"," >> "$output_file"
            echo "      \"uptime\": \"$uptime\"," >> "$output_file"
            
            # Resource usage
            local pid=$(systemctl show "$service" -p MainPID --value 2>/dev/null)
            if [[ -n "$pid" && "$pid" != "0" ]]; then
                local cpu=$(ps -p "$pid" -o %cpu --no-headers 2>/dev/null | tr -d ' ')
                local memory=$(ps -p "$pid" -o %mem --no-headers 2>/dev/null | tr -d ' ')
                local rss=$(ps -p "$pid" -o rss --no-headers 2>/dev/null | tr -d ' ')
                
                echo "      \"resources\": {" >> "$output_file"
                echo "        \"pid\": $pid," >> "$output_file"
                echo "        \"cpu_percent\": \"$cpu\"," >> "$output_file"
                echo "        \"memory_percent\": \"$memory\"," >> "$output_file"
                echo "        \"memory_rss_kb\": \"$rss\"" >> "$output_file"
                echo "      }," >> "$output_file"
            else
                echo "      \"resources\": null," >> "$output_file"
            fi
            
            # Port connectivity (common ports)
            local ports=""
            case "$service" in
                ssh) ports="22" ;;
                nginx) ports="80 443" ;;
                postgresql) ports="5432" ;;
                redis) ports="6379" ;;
                elasticsearch) ports="9200 9300" ;;
                mysql) ports="3306" ;;
            esac
            
            if [[ -n "$ports" ]]; then
                echo "      \"ports\": [" >> "$output_file"
                local port_first=true
                for port in $ports; do
                    [[ "$port_first" == true ]] && port_first=false || echo "," >> "$output_file"
                    
                    if timeout 2 bash -c "echo >/dev/tcp/localhost/$port" 2>/dev/null; then
                        echo "        {\"port\": $port, \"status\": \"open\"}" >> "$output_file"
                    else
                        echo "        {\"port\": $port, \"status\": \"closed\"}" >> "$output_file"
                    fi
                done
                echo "      ]," >> "$output_file"
            else
                echo "      \"ports\": []," >> "$output_file"
            fi
            
            # Log analysis (recent errors)
            local log_errors=$(journalctl -u "$service" --since "1 hour ago" -p err --no-pager -q | wc -l)
            echo "      \"recent_errors\": $log_errors" >> "$output_file"
            
        else
            echo "      \"exists\": false," >> "$output_file"
            echo "      \"status\": \"not_found\"," >> "$output_file"
            echo "      \"enabled\": \"unknown\"," >> "$output_file"
            echo "      \"uptime\": null," >> "$output_file"
            echo "      \"resources\": null," >> "$output_file"
            echo "      \"ports\": []," >> "$output_file"
            echo "      \"recent_errors\": 0" >> "$output_file"
        fi
        
        echo "    }" >> "$output_file"
    done
    
    echo "  }," >> "$output_file"
    
    # System overview
    echo "  \"system\": {" >> "$output_file"
    echo "    \"load_average\": \"$(uptime | awk -F'load average:' '{print $2}' | sed 's/^[ \t]*//')\"," >> "$output_file"
    echo "    \"memory_usage\": \"$(free | awk '/^Mem:/ {printf \"%.1f%%\", ($3/$2)*100}')\"," >> "$output_file"
    echo "    \"disk_usage\": \"$(df -h / | awk 'NR==2 {print $5}')\"," >> "$output_file"
    echo "    \"uptime\": \"$(uptime -p)\"" >> "$output_file"
    echo "  }" >> "$output_file"
    
    echo "}" >> "$output_file"
    
    echo "Service health report generated: $output_file"
    
    # Display summary
    echo -e "\n=== Service Health Summary ==="
    jq -r '.services | to_entries[] | "\(.key): \(.value.status)"' "$output_file" 2>/dev/null || \
    grep -E '"[^"]+": \{' "$output_file" | sed 's/.*"\([^"]*\)".*/\1/' | while read service; do
        status=$(grep -A 10 "\"$service\":" "$output_file" | grep '"status"' | cut -d'"' -f4)
        echo "$service: $status"
    done
}
```

## Performance Analysis & Optimization

### System Performance Profiler
```bash
#!/bin/bash
# Advanced performance profiling toolkit
performance_profiler() {
    local duration="${1:-60}"
    local interval="${2:-5}"
    local output_dir="perf_profile_$(date +%Y%m%d_%H%M%S)"
    
    mkdir -p "$output_dir"
    
    echo "Starting performance profiling for ${duration}s..."
    
    # CPU profiling
    cpu_profiler() {
        echo "timestamp,cpu_user,cpu_system,cpu_idle,cpu_iowait,cpu_steal" > "$output_dir/cpu.csv"
        
        for ((i=0; i<duration; i+=interval)); do
            timestamp=$(date '+%Y-%m-%d %H:%M:%S')
            cpu_stats=$(iostat -c 1 2 | tail -1 | awk '{print $1","$3","$6","$4","$5}')
            echo "$timestamp,$cpu_stats" >> "$output_dir/cpu.csv"
            sleep "$interval"
        done &
    }
    
    # Memory profiling
    memory_profiler() {
        echo "timestamp,total_mb,used_mb,free_mb,available_mb,buffers_mb,cached_mb,swap_used_mb" > "$output_dir/memory.csv"
        
        for ((i=0; i<duration; i+=interval)); do
            timestamp=$(date '+%Y-%m-%d %H:%M:%S')
            mem_stats=$(free -m | awk '
                NR==2 {printf "%d,%d,%d,%d", $2, $3, $4, $7}
                NR==3 {printf ",%d,%d", $3, $4}
                NR==4 {printf ",%d", $3}
            ')
            echo "$timestamp,$mem_stats" >> "$output_dir/memory.csv"
            sleep "$interval"
        done &
    }
    
    # Disk I/O profiling
    disk_profiler() {
        echo "timestamp,device,tps,read_kb_s,write_kb_s,read_kb,write_kb" > "$output_dir/disk_io.csv"
        
        for ((i=0; i<duration; i+=interval)); do
            timestamp=$(date '+%Y-%m-%d %H:%M:%S')
            iostat -d 1 2 | tail -n +4 | grep -v "^$" | tail -n +2 | while read line; do
                echo "$timestamp,$line" >> "$output_dir/disk_io.csv"
            done
            sleep "$interval"
        done &
    }
    
    # Network I/O profiling
    network_profiler() {
        echo "timestamp,interface,rx_bytes,tx_bytes,rx_packets,tx_packets,rx_errors,tx_errors" > "$output_dir/network.csv"
        
        for ((i=0; i<duration; i+=interval)); do
            timestamp=$(date '+%Y-%m-%d %H:%M:%S')
            cat /proc/net/dev | tail -n +3 | while read line; do
                if [[ "$line" =~ ^[[:space:]]*([^:]+):[[:space:]]*([0-9]+)[[:space:]]+([0-9]+)[[:space:]]+([0-9]+)[[:space:]]+([0-9]+)[[:space:]]+[0-9]+[[:space:]]+[0-9]+[[:space:]]+[0-9]+[[:space:]]+[0-9]+[[:space:]]+([0-9]+)[[:space:]]+([0-9]+)[[:space:]]+([0-9]+)[[:space:]]+([0-9]+) ]]; then
                    interface=${BASH_REMATCH[1]}
                    rx_bytes=${BASH_REMATCH[2]}
                    rx_packets=${BASH_REMATCH[3]}
                    rx_errors=${BASH_REMATCH[4]}
                    tx_bytes=${BASH_REMATCH[6]}
                    tx_packets=${BASH_REMATCH[7]}
                    tx_errors=${BASH_REMATCH[8]}
                    echo "$timestamp,$interface,$rx_bytes,$tx_bytes,$rx_packets,$tx_packets,$rx_errors,$tx_errors" >> "$output_dir/network.csv"
                fi
            done
            sleep "$interval"
        done &
    }
    
    # Process profiling
    process_profiler() {
        echo "timestamp,pid,ppid,user,cpu_percent,mem_percent,vsz_kb,rss_kb,tty,stat,start,time,command" > "$output_dir/processes.csv"
        
        for ((i=0; i<duration; i+=interval)); do
            timestamp=$(date '+%Y-%m-%d %H:%M:%S')
            ps aux --sort=-%cpu | head -21 | tail -20 | while read line; do
                echo "$timestamp,$line" >> "$output_dir/processes.csv"
            done
            sleep "$interval"
        done &
    }
    
    # System load profiling
    load_profiler() {
        echo "timestamp,load_1m,load_5m,load_15m,running_processes,total_processes" > "$output_dir/load.csv"
        
        for ((i=0; i<duration; i+=interval)); do
            timestamp=$(date '+%Y-%m-%d %H:%M:%S')
            load_avg=$(uptime | awk -F'load average:' '{print $2}' | sed 's/,//g' | sed 's/^ *//')
            proc_count=$(cat /proc/loadavg | awk '{print $4}')
            echo "$timestamp,$load_avg,$proc_count" >> "$output_dir/load.csv"
            sleep "$interval"
        done &
    }
    
    # Start all profilers
    cpu_profiler
    memory_profiler
    disk_profiler
    network_profiler
    process_profiler
    load_profiler
    
    # Wait for completion
    wait
    
    # Generate summary report
    generate_summary_report() {
        cat > "$output_dir/summary.html" << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <title>Performance Profile Summary</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .metric { margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }
        .metric h3 { margin-top: 0; color: #333; }
        .stats { display: flex; justify-content: space-around; }
        .stat { text-align: center; }
        .stat .value { font-size: 24px; font-weight: bold; color: #007acc; }
        .stat .label { font-size: 12px; color: #666; }
    </style>
</head>
<body>
    <h1>Performance Profile Summary</h1>
    <p>Generated: <script>document.write(new Date().toLocaleString())</script></p>
EOF

        # CPU summary
        echo '<div class="metric"><h3>CPU Usage</h3><div class="stats">' >> "$output_dir/summary.html"
        if [[ -f "$output_dir/cpu.csv" ]]; then
            local avg_cpu=$(tail -n +2 "$output_dir/cpu.csv" | awk -F, '{sum+=$2} END {printf "%.1f", sum/NR}')
            local max_cpu=$(tail -n +2 "$output_dir/cpu.csv" | awk -F, '{if($2>max) max=$2} END {printf "%.1f", max}')
            echo "<div class=\"stat\"><div class=\"value\">${avg_cpu}%</div><div class=\"label\">Average CPU</div></div>" >> "$output_dir/summary.html"
            echo "<div class=\"stat\"><div class=\"value\">${max_cpu}%</div><div class=\"label\">Peak CPU</div></div>" >> "$output_dir/summary.html"
        fi
        echo '</div></div>' >> "$output_dir/summary.html"
        
        # Memory summary
        echo '<div class="metric"><h3>Memory Usage</h3><div class="stats">' >> "$output_dir/summary.html"
        if [[ -f "$output_dir/memory.csv" ]]; then
            local avg_mem=$(tail -n +2 "$output_dir/memory.csv" | awk -F, '{used+=$3; total+=$2} END {printf "%.1f", (used/NR)/(total/NR)*100}')
            local max_mem=$(tail -n +2 "$output_dir/memory.csv" | awk -F, '{pct=$3/$2*100; if(pct>max) max=pct} END {printf "%.1f", max}')
            echo "<div class=\"stat\"><div class=\"value\">${avg_mem}%</div><div class=\"label\">Average Memory</div></div>" >> "$output_dir/summary.html"
            echo "<div class=\"stat\"><div class=\"value\">${max_mem}%</div><div class=\"label\">Peak Memory</div></div>" >> "$output_dir/summary.html"
        fi
        echo '</div></div>' >> "$output_dir/summary.html"
        
        echo '</body></html>' >> "$output_dir/summary.html"
    }
    
    generate_summary_report
    
    echo "Performance profiling completed!"
    echo "Results available in: $output_dir"
    echo "Summary report: $output_dir/summary.html"
    
    # Display quick summary
    echo -e "\n=== Quick Summary ==="
    if [[ -f "$output_dir/cpu.csv" ]]; then
        local avg_cpu=$(tail -n +2 "$output_dir/cpu.csv" | awk -F, '{sum+=$2} END {printf "%.1f", sum/NR}')
        echo "Average CPU usage: ${avg_cpu}%"
    fi
    
    if [[ -f "$output_dir/memory.csv" ]]; then
        local avg_mem=$(tail -n +2 "$output_dir/memory.csv" | awk -F, '{used+=$3; total+=$2} END {printf "%.1f", (used/NR)/(total/NR)*100}')
        echo "Average memory usage: ${avg_mem}%"
    fi
    
    if [[ -f "$output_dir/load.csv" ]]; then
        local avg_load=$(tail -n +2 "$output_dir/load.csv" | awk -F, '{sum+=$2} END {printf "%.2f", sum/NR}')
        echo "Average load (1m): ${avg_load}"
    fi
}
```

This comprehensive Bash troubleshooting guide provides enterprise-grade tools for system diagnostics, log analysis, network troubleshooting, service monitoring, and performance profiling. Each section includes production-ready scripts with detailed analysis capabilities, JSON output formats, and visualization support for DevOps environments.