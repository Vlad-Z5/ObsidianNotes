# Bash Log Processing & Analysis

## Overview
Bash log processing and analysis covers techniques for parsing, filtering, analyzing, and monitoring log files using shell scripts. This includes real-time log monitoring, log aggregation, pattern detection, and generating insights from application and system logs.

## Log Parsing and Filtering

### 1. Basic Log Processing Functions
```bash
#!/bin/bash

# Log processing configuration
readonly LOG_DATE_FORMAT="%Y-%m-%d %H:%M:%S"
readonly DEFAULT_LOG_LEVEL="INFO"

# Common log patterns
readonly APACHE_LOG_PATTERN='^([^ ]+) [^ ]+ [^ ]+ \[([^\]]+)\] "([^"]*)" ([0-9]+) ([0-9]+|-)'
readonly NGINX_LOG_PATTERN='^([^ ]+) - - \[([^\]]+)\] "([^"]*)" ([0-9]+) ([0-9]+) "([^"]*)" "([^"]*)"'
readonly SYSLOG_PATTERN='^([A-Z][a-z]{2} [0-9 ][0-9] [0-9]{2}:[0-9]{2}:[0-9]{2}) ([^ ]+) ([^:]+): (.*)'
readonly APPLICATION_LOG_PATTERN='^\[([^\]]+)\] \[([A-Z]+)\] (.*)$'

# Parse log lines by type
parse_log_line() {
    local log_line="$1"
    local log_type="$2"
    local -A parsed_data
    
    case "$log_type" in
        apache|httpd)
            if [[ $log_line =~ $APACHE_LOG_PATTERN ]]; then
                parsed_data[ip]="${BASH_REMATCH[1]}"
                parsed_data[timestamp]="${BASH_REMATCH[2]}"
                parsed_data[request]="${BASH_REMATCH[3]}"
                parsed_data[status]="${BASH_REMATCH[4]}"
                parsed_data[size]="${BASH_REMATCH[5]}"
            else
                return 1
            fi
            ;;
        nginx)
            if [[ $log_line =~ $NGINX_LOG_PATTERN ]]; then
                parsed_data[ip]="${BASH_REMATCH[1]}"
                parsed_data[timestamp]="${BASH_REMATCH[2]}"
                parsed_data[request]="${BASH_REMATCH[3]}"
                parsed_data[status]="${BASH_REMATCH[4]}"
                parsed_data[size]="${BASH_REMATCH[5]}"
                parsed_data[referer]="${BASH_REMATCH[6]}"
                parsed_data[user_agent]="${BASH_REMATCH[7]}"
            else
                return 1
            fi
            ;;
        application)
            if [[ $log_line =~ $APPLICATION_LOG_PATTERN ]]; then
                parsed_data[timestamp]="${BASH_REMATCH[1]}"
                parsed_data[level]="${BASH_REMATCH[2]}"
                parsed_data[message]="${BASH_REMATCH[3]}"
            else
                return 1
            fi
            ;;
        *)
            log_error "Unknown log type: $log_type"
            return 1
            ;;
    esac
    
    # Output parsed data as key=value pairs
    for key in "${!parsed_data[@]}"; do
        echo "${key}=${parsed_data[$key]}"
    done
}

# Filter logs by time range
filter_logs_by_time() {
    local log_file="$1"
    local start_time="$2"
    local end_time="$3"
    local time_pattern="$4"
    
    log_info "Filtering logs between $start_time and $end_time"
    
    # Convert times to epoch for comparison
    local start_epoch=$(date -d "$start_time" +%s 2>/dev/null)
    local end_epoch=$(date -d "$end_time" +%s 2>/dev/null)
    
    if [[ -z "$start_epoch" || -z "$end_epoch" ]]; then
        log_error "Invalid time format. Use format like '2023-01-01 10:00:00'"
        return 1
    fi
    
    local filtered_count=0
    
    while IFS= read -r line; do
        # Extract timestamp based on pattern
        local timestamp=""
        case "$time_pattern" in
            apache|nginx)
                if [[ $line =~ \[([^\]]+)\] ]]; then
                    timestamp="${BASH_REMATCH[1]}"
                    # Convert Apache/Nginx timestamp format
                    timestamp=$(date -d "$(echo "$timestamp" | sed 's|/| |g' | sed 's|:| |')" +%s 2>/dev/null)
                fi
                ;;
            iso8601)
                if [[ $line =~ ([0-9]{4}-[0-9]{2}-[0-9]{2}[T ][0-9]{2}:[0-9]{2}:[0-9]{2}) ]]; then
                    timestamp=$(date -d "${BASH_REMATCH[1]}" +%s 2>/dev/null)
                fi
                ;;
            syslog)
                if [[ $line =~ ^([A-Z][a-z]{2} [0-9 ][0-9] [0-9]{2}:[0-9]{2}:[0-9]{2}) ]]; then
                    timestamp=$(date -d "${BASH_REMATCH[1]}" +%s 2>/dev/null)
                fi
                ;;
        esac
        
        # Check if timestamp is within range
        if [[ -n "$timestamp" && "$timestamp" -ge "$start_epoch" && "$timestamp" -le "$end_epoch" ]]; then
            echo "$line"
            ((filtered_count++))
        fi
        
    done < "$log_file"
    
    log_info "Filtered $filtered_count log entries"
}

# Extract specific log levels
filter_by_log_level() {
    local log_file="$1"
    local level="$2"
    local case_sensitive="${3:-false}"
    
    local grep_options=""
    if [[ "$case_sensitive" == "false" ]]; then
        grep_options="-i"
    fi
    
    case "$level" in
        ERROR|CRITICAL|FATAL)
            grep $grep_options -E "\[(ERROR|CRITICAL|FATAL)\]|\bERROR\b|\bCRITICAL\b|\bFATAL\b" "$log_file"
            ;;
        WARN|WARNING)
            grep $grep_options -E "\[(WARN|WARNING)\]|\bWARN\b|\bWARNING\b" "$log_file"
            ;;
        INFO)
            grep $grep_options -E "\[INFO\]|\bINFO\b" "$log_file"
            ;;
        DEBUG)
            grep $grep_options -E "\[DEBUG\]|\bDEBUG\b" "$log_file"
            ;;
        *)
            grep $grep_options "\\[$level\\]\\|\\b$level\\b" "$log_file"
            ;;
    esac
}
```

### 2. Advanced Log Analysis Functions
```bash
#!/bin/bash

# Analyze HTTP access logs
analyze_access_logs() {
    local log_file="$1"
    local output_dir="${2:-./analysis}"
    
    mkdir -p "$output_dir"
    log_info "Analyzing access logs: $log_file"
    
    # Top IP addresses
    log_info "Analyzing top IP addresses..."
    awk '{print $1}' "$log_file" | sort | uniq -c | sort -rn | head -20 > "$output_dir/top_ips.txt"
    
    # HTTP status code distribution
    log_info "Analyzing status codes..."
    awk '{print $9}' "$log_file" | sort | uniq -c | sort -rn > "$output_dir/status_codes.txt"
    
    # Most requested URLs
    log_info "Analyzing most requested URLs..."
    awk '{print $7}' "$log_file" | sort | uniq -c | sort -rn | head -20 > "$output_dir/top_urls.txt"
    
    # User agents analysis
    log_info "Analyzing user agents..."
    awk -F'"' '{print $6}' "$log_file" | sort | uniq -c | sort -rn | head -10 > "$output_dir/user_agents.txt"
    
    # Hourly request distribution
    log_info "Analyzing hourly distribution..."
    awk -F'[/:]' '{print $4":"$5}' "$log_file" | sort | uniq -c | sort -k2 > "$output_dir/hourly_distribution.txt"
    
    # Large response analysis (>1MB)
    log_info "Analyzing large responses..."
    awk '$10 > 1048576 {print $0}' "$log_file" | sort -k10 -rn > "$output_dir/large_responses.txt"
    
    # Error analysis (4xx and 5xx)
    log_info "Analyzing errors..."
    awk '$9 ~ /^[45]/ {print $0}' "$log_file" > "$output_dir/errors.txt"
    
    # Generate summary report
    generate_access_log_summary "$log_file" "$output_dir"
}

# Generate access log summary
generate_access_log_summary() {
    local log_file="$1"
    local output_dir="$2"
    local summary_file="$output_dir/summary.txt"
    
    local total_requests=$(wc -l < "$log_file")
    local unique_ips=$(awk '{print $1}' "$log_file" | sort -u | wc -l)
    local error_count=$(awk '$9 ~ /^[45]/ {count++} END {print count+0}' "$log_file")
    local total_bytes=$(awk '{sum+=$10} END {print sum+0}' "$log_file")
    
    cat > "$summary_file" << EOF
Access Log Analysis Summary
==========================
Generated: $(date)
Log File: $log_file

Statistics:
-----------
Total Requests: $total_requests
Unique IP Addresses: $unique_ips
Error Requests (4xx/5xx): $error_count
Error Rate: $(echo "scale=2; $error_count * 100 / $total_requests" | bc -l)%
Total Bytes Transferred: $(numfmt --to=iec $total_bytes)

Top 5 IP Addresses:
------------------
$(head -5 "$output_dir/top_ips.txt")

Top 5 URLs:
-----------
$(head -5 "$output_dir/top_urls.txt")

Status Code Distribution:
------------------------
$(cat "$output_dir/status_codes.txt")
EOF
    
    log_info "Summary report generated: $summary_file"
}

# Analyze application logs for errors and patterns
analyze_application_logs() {
    local log_file="$1"
    local output_dir="${2:-./app_analysis}"
    local app_name="${3:-application}"
    
    mkdir -p "$output_dir"
    log_info "Analyzing application logs for: $app_name"
    
    # Error analysis
    log_info "Extracting error patterns..."
    grep -iE "(error|exception|fail|fatal|critical)" "$log_file" > "$output_dir/errors.txt"
    
    # Exception stack traces
    log_info "Extracting stack traces..."
    awk '/Exception|Error/{flag=1} flag && /^\s*at /{print} flag && /^$/{flag=0}' "$log_file" > "$output_dir/stack_traces.txt"
    
    # Performance issues (slow queries, timeouts)
    log_info "Analyzing performance issues..."
    grep -iE "(timeout|slow|performance|latency|response time)" "$log_file" > "$output_dir/performance_issues.txt"
    
    # Database-related issues
    log_info "Analyzing database issues..."
    grep -iE "(database|sql|connection|query|deadlock)" "$log_file" > "$output_dir/database_issues.txt"
    
    # Memory and resource issues
    log_info "Analyzing resource issues..."
    grep -iE "(memory|heap|garbage|cpu|resource)" "$log_file" > "$output_dir/resource_issues.txt"
    
    # Security-related events
    log_info "Analyzing security events..."
    grep -iE "(security|authentication|authorization|login|access denied)" "$log_file" > "$output_dir/security_events.txt"
    
    # Generate application log summary
    generate_application_log_summary "$log_file" "$output_dir" "$app_name"
}

# Generate application log summary
generate_application_log_summary() {
    local log_file="$1"
    local output_dir="$2"
    local app_name="$3"
    local summary_file="$output_dir/summary.txt"
    
    local total_lines=$(wc -l < "$log_file")
    local error_count=$(wc -l < "$output_dir/errors.txt")
    local performance_count=$(wc -l < "$output_dir/performance_issues.txt")
    local security_count=$(wc -l < "$output_dir/security_events.txt")
    
    cat > "$summary_file" << EOF
Application Log Analysis Summary
===============================
Application: $app_name
Generated: $(date)
Log File: $log_file

Statistics:
-----------
Total Log Lines: $total_lines
Error/Exception Lines: $error_count
Performance Issues: $performance_count
Security Events: $security_count

Error Rate: $(echo "scale=2; $error_count * 100 / $total_lines" | bc -l)%

Top Error Patterns:
------------------
$(grep -ioE "(error|exception|fail): [^,.]+" "$output_dir/errors.txt" | sort | uniq -c | sort -rn | head -5)

Recent Errors (Last 10):
------------------------
$(tail -10 "$output_dir/errors.txt")

Performance Issues Summary:
--------------------------
$(wc -l "$output_dir/performance_issues.txt" | awk '{print $1}') performance-related entries found
$(if [[ -s "$output_dir/performance_issues.txt" ]]; then head -5 "$output_dir/performance_issues.txt"; fi)

Security Events Summary:
-----------------------
$(wc -l "$output_dir/security_events.txt" | awk '{print $1}') security-related entries found
$(if [[ -s "$output_dir/security_events.txt" ]]; then head -5 "$output_dir/security_events.txt"; fi)
EOF
    
    log_info "Application log summary generated: $summary_file"
}
```

## Real-Time Log Monitoring

### 1. Log Monitoring and Alerting
```bash
#!/bin/bash

# Real-time log monitoring with alerting
monitor_logs() {
    local log_file="$1"
    local config_file="$2"
    local alert_script="${3:-./send_alert.sh}"
    
    if [[ ! -f "$log_file" ]]; then
        log_error "Log file not found: $log_file"
        return 1
    fi
    
    if [[ ! -f "$config_file" ]]; then
        log_error "Configuration file not found: $config_file"
        return 1
    fi
    
    log_info "Starting real-time monitoring of: $log_file"
    
    # Load monitoring configuration
    declare -A patterns
    declare -A thresholds
    declare -A actions
    
    while IFS='=' read -r key value; do
        [[ $key =~ ^[[:space:]]*# ]] && continue
        [[ -z "$key" ]] && continue
        
        key=$(echo "$key" | xargs)
        value=$(echo "$value" | xargs)
        
        if [[ $key =~ ^pattern_ ]]; then
            pattern_name="${key#pattern_}"
            patterns["$pattern_name"]="$value"
        elif [[ $key =~ ^threshold_ ]]; then
            threshold_name="${key#threshold_}"
            thresholds["$threshold_name"]="$value"
        elif [[ $key =~ ^action_ ]]; then
            action_name="${key#action_}"
            actions["$action_name"]="$value"
        fi
    done < "$config_file"
    
    # Start monitoring with tail
    tail -F "$log_file" | while IFS= read -r line; do
        process_log_line "$line" patterns thresholds actions "$alert_script"
    done
}

# Process individual log lines for patterns
process_log_line() {
    local line="$1"
    local -n pattern_ref=$2
    local -n threshold_ref=$3
    local -n action_ref=$4
    local alert_script="$5"
    
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    # Check each pattern
    for pattern_name in "${!pattern_ref[@]}"; do
        local pattern="${pattern_ref[$pattern_name]}"
        
        if [[ $line =~ $pattern ]]; then
            local threshold="${threshold_ref[$pattern_name]:-1}"
            local action="${action_ref[$pattern_name]:-log}"
            
            # Update pattern counter
            local counter_file="/tmp/log_monitor_${pattern_name}.count"
            local current_count=$(cat "$counter_file" 2>/dev/null || echo "0")
            ((current_count++))
            echo "$current_count" > "$counter_file"
            
            log_info "Pattern '$pattern_name' matched: $line"
            
            # Check threshold
            if [[ $current_count -ge $threshold ]]; then
                case "$action" in
                    alert)
                        "$alert_script" "$pattern_name" "$current_count" "$line" &
                        ;;
                    email)
                        send_email_alert "$pattern_name" "$current_count" "$line" &
                        ;;
                    slack)
                        send_slack_alert "$pattern_name" "$current_count" "$line" &
                        ;;
                    webhook)
                        send_webhook_alert "$pattern_name" "$current_count" "$line" &
                        ;;
                    log)
                        log_warn "Threshold exceeded for pattern '$pattern_name': $current_count occurrences"
                        ;;
                esac
                
                # Reset counter after alerting
                echo "0" > "$counter_file"
            fi
        fi
    done
}

# Continuous log analysis with rotation handling
continuous_log_analysis() {
    local log_file="$1"
    local analysis_interval="${2:-300}"  # 5 minutes
    local output_dir="${3:-./continuous_analysis}"
    
    mkdir -p "$output_dir"
    log_info "Starting continuous analysis of: $log_file"
    
    local last_position=0
    local analysis_count=0
    
    while true; do
        if [[ -f "$log_file" ]]; then
            local current_size=$(stat -f%z "$log_file" 2>/dev/null || stat -c%s "$log_file" 2>/dev/null || echo "0")
            
            # Check if log file was rotated
            if [[ $current_size -lt $last_position ]]; then
                log_info "Log rotation detected, resetting position"
                last_position=0
            fi
            
            # Process new log entries
            if [[ $current_size -gt $last_position ]]; then
                local temp_file=$(mktemp)
                tail -c +$((last_position + 1)) "$log_file" > "$temp_file"
                
                # Analyze new entries
                ((analysis_count++))
                local analysis_output="$output_dir/analysis_$(date +%Y%m%d_%H%M%S).txt"
                
                analyze_log_chunk "$temp_file" "$analysis_output"
                
                rm -f "$temp_file"
                last_position=$current_size
            fi
        else
            log_warn "Log file not found: $log_file"
        fi
        
        sleep "$analysis_interval"
    done
}

# Analyze a chunk of log data
analyze_log_chunk() {
    local chunk_file="$1"
    local output_file="$2"
    
    local chunk_lines=$(wc -l < "$chunk_file")
    
    if [[ $chunk_lines -eq 0 ]]; then
        return
    fi
    
    log_info "Analyzing $chunk_lines new log lines"
    
    cat > "$output_file" << EOF
Log Chunk Analysis
==================
Timestamp: $(date)
Lines Analyzed: $chunk_lines

Error Summary:
--------------
$(grep -ic "error" "$chunk_file" 2>/dev/null || echo "0") error entries
$(grep -ic "warn" "$chunk_file" 2>/dev/null || echo "0") warning entries
$(grep -ic "critical" "$chunk_file" 2>/dev/null || echo "0") critical entries

Top Error Messages:
------------------
$(grep -i "error" "$chunk_file" | head -5)

Response Time Analysis:
----------------------
$(grep -oE "response_time=[0-9.]+" "$chunk_file" | awk -F'=' '{sum+=$2; count++} END {if(count>0) print "Average: " sum/count "ms, Count: " count}')

Recent Activity:
---------------
$(tail -10 "$chunk_file")
EOF
    
    log_info "Chunk analysis saved: $output_file"
}
```

### 2. Log Aggregation and Correlation
```bash
#!/bin/bash

# Aggregate logs from multiple sources
aggregate_logs() {
    local config_file="$1"
    local output_file="$2"
    local time_window="${3:-3600}"  # 1 hour in seconds
    
    declare -A log_sources
    declare -A log_formats
    
    # Read configuration
    while IFS='=' read -r key value; do
        [[ $key =~ ^[[:space:]]*# ]] && continue
        [[ -z "$key" ]] && continue
        
        key=$(echo "$key" | xargs)
        value=$(echo "$value" | xargs)
        
        if [[ $key =~ ^source_ ]]; then
            source_name="${key#source_}"
            log_sources["$source_name"]="$value"
        elif [[ $key =~ ^format_ ]]; then
            format_name="${key#format_}"
            log_formats["$format_name"]="$value"
        fi
    done < "$config_file"
    
    log_info "Aggregating logs from ${#log_sources[@]} sources"
    
    # Aggregate with timestamps
    {
        for source_name in "${!log_sources[@]}"; do
            local source_file="${log_sources[$source_name]}"
            local format="${log_formats[$source_name]:-standard}"
            
            if [[ -f "$source_file" ]]; then
                log_info "Processing source: $source_name ($source_file)"
                
                while IFS= read -r line; do
                    local standardized_line=$(standardize_log_line "$line" "$format" "$source_name")
                    echo "$standardized_line"
                done < "$source_file"
            else
                log_warn "Source file not found: $source_file"
            fi
        done
    } | sort -k1,2 > "$output_file"
    
    log_info "Aggregated logs saved to: $output_file"
}

# Standardize log line format
standardize_log_line() {
    local line="$1"
    local format="$2"
    local source="$3"
    
    local timestamp=""
    local level=""
    local message=""
    
    case "$format" in
        apache)
            if [[ $line =~ \[([^\]]+)\] ]]; then
                timestamp=$(date -d "${BASH_REMATCH[1]}" '+%Y-%m-%d %H:%M:%S' 2>/dev/null || echo "$(date '+%Y-%m-%d %H:%M:%S')")
            fi
            level="INFO"
            message="$line"
            ;;
        application)
            if [[ $line =~ ^\[([^\]]+)\][[:space:]]*\[([^\]]+)\][[:space:]]*(.*) ]]; then
                timestamp="${BASH_REMATCH[1]}"
                level="${BASH_REMATCH[2]}"
                message="${BASH_REMATCH[3]}"
            fi
            ;;
        syslog)
            if [[ $line =~ ^([A-Z][a-z]{2}[[:space:]]+[0-9]+[[:space:]]+[0-9]{2}:[0-9]{2}:[0-9]{2})[[:space:]]+([^:]+):[[:space:]]*(.*) ]]; then
                timestamp=$(date -d "${BASH_REMATCH[1]}" '+%Y-%m-%d %H:%M:%S' 2>/dev/null || echo "$(date '+%Y-%m-%d %H:%M:%S')")
                level="INFO"
                message="${BASH_REMATCH[3]}"
            fi
            ;;
        *)
            timestamp="$(date '+%Y-%m-%d %H:%M:%S')"
            level="INFO"
            message="$line"
            ;;
    esac
    
    echo "$timestamp [$level] [$source] $message"
}

# Correlate events across multiple logs
correlate_events() {
    local aggregated_log="$1"
    local correlation_window="${2:-60}"  # seconds
    local output_file="$3"
    
    log_info "Correlating events with ${correlation_window}s window"
    
    declare -A event_groups
    local group_id=0
    
    # Process aggregated logs and group events by time windows
    while IFS= read -r line; do
        if [[ $line =~ ^([0-9]{4}-[0-9]{2}-[0-9]{2}[[:space:]]+[0-9]{2}:[0-9]{2}:[0-9]{2}) ]]; then
            local timestamp="${BASH_REMATCH[1]}"
            local epoch=$(date -d "$timestamp" +%s 2>/dev/null)
            
            if [[ -n "$epoch" ]]; then
                # Find appropriate group or create new one
                local assigned_group=""
                
                for existing_group in "${!event_groups[@]}"; do
                    IFS=',' read -ra group_info <<< "${event_groups[$existing_group]}"
                    local group_start_epoch="${group_info[0]}"
                    local group_end_epoch="${group_info[1]}"
                    
                    if [[ $epoch -ge $group_start_epoch && $epoch -le $((group_end_epoch + correlation_window)) ]]; then
                        assigned_group="$existing_group"
                        # Update group end time
                        event_groups["$existing_group"]="${group_start_epoch},${epoch}"
                        break
                    fi
                done
                
                # Create new group if no suitable group found
                if [[ -z "$assigned_group" ]]; then
                    assigned_group="group_$((++group_id))"
                    event_groups["$assigned_group"]="${epoch},${epoch}"
                fi
                
                # Add event to group file
                echo "$line" >> "${output_file%.txt}_${assigned_group}.txt"
            fi
        fi
    done < "$aggregated_log"
    
    # Generate correlation report
    generate_correlation_report "$output_file" event_groups
}

# Generate correlation report
generate_correlation_report() {
    local output_file="$1"
    local -n groups_ref=$2
    
    cat > "$output_file" << EOF
Event Correlation Report
=======================
Generated: $(date)
Total Event Groups: ${#groups_ref[@]}

Group Summary:
--------------
EOF
    
    for group in "${!groups_ref[@]}"; do
        IFS=',' read -ra group_info <<< "${groups_ref[$group]}"
        local start_epoch="${group_info[0]}"
        local end_epoch="${group_info[1]}"
        local start_time=$(date -d "@$start_epoch" '+%Y-%m-%d %H:%M:%S')
        local end_time=$(date -d "@$end_epoch" '+%Y-%m-%d %H:%M:%S')
        local duration=$((end_epoch - start_epoch))
        local event_count=$(wc -l < "${output_file%.txt}_${group}.txt" 2>/dev/null || echo "0")
        
        cat >> "$output_file" << EOF

$group:
  Time Range: $start_time to $end_time
  Duration: ${duration}s
  Events: $event_count
  File: ${output_file%.txt}_${group}.txt

EOF
        
        # Show sample events from this group
        if [[ -f "${output_file%.txt}_${group}.txt" ]]; then
            echo "  Sample Events:" >> "$output_file"
            head -3 "${output_file%.txt}_${group}.txt" | sed 's/^/    /' >> "$output_file"
            echo >> "$output_file"
        fi
    done
    
    log_info "Correlation report generated: $output_file"
}
```

## Log Alerting and Notification

### 1. Alert Generation and Delivery
```bash
#!/bin/bash

# Send email alert
send_email_alert() {
    local pattern_name="$1"
    local count="$2"
    local sample_line="$3"
    local email_config="${4:-./email_config.conf}"
    
    # Load email configuration
    local smtp_server=""
    local smtp_port=""
    local from_email=""
    local to_emails=""
    local subject_prefix=""
    
    if [[ -f "$email_config" ]]; then
        source "$email_config"
    fi
    
    local subject="${subject_prefix:-[LOG ALERT]} Pattern '$pattern_name' threshold exceeded"
    local body="Log Alert Details:
    
Pattern: $pattern_name
Occurrence Count: $count
Sample Log Entry: $sample_line
Timestamp: $(date)
Hostname: $(hostname)

Please investigate this issue promptly."
    
    # Send email using mail command or curl
    if command -v mail >/dev/null 2>&1; then
        echo "$body" | mail -s "$subject" "$to_emails"
    elif command -v sendmail >/dev/null 2>&1; then
        {
            echo "To: $to_emails"
            echo "Subject: $subject"
            echo "From: $from_email"
            echo
            echo "$body"
        } | sendmail "$to_emails"
    else
        log_error "No email sending capability found"
        return 1
    fi
    
    log_info "Email alert sent for pattern: $pattern_name"
}

# Send Slack alert
send_slack_alert() {
    local pattern_name="$1"
    local count="$2"
    local sample_line="$3"
    local webhook_url="${SLACK_WEBHOOK_URL:-}"
    
    if [[ -z "$webhook_url" ]]; then
        log_error "Slack webhook URL not configured"
        return 1
    fi
    
    local color="danger"
    if [[ $count -lt 5 ]]; then
        color="warning"
    fi
    
    local payload=$(cat << EOF
{
    "attachments": [
        {
            "color": "$color",
            "title": "Log Alert: Pattern '$pattern_name'",
            "fields": [
                {
                    "title": "Pattern",
                    "value": "$pattern_name",
                    "short": true
                },
                {
                    "title": "Count",
                    "value": "$count",
                    "short": true
                },
                {
                    "title": "Hostname",
                    "value": "$(hostname)",
                    "short": true
                },
                {
                    "title": "Timestamp",
                    "value": "$(date)",
                    "short": true
                },
                {
                    "title": "Sample Log Entry",
                    "value": "\`\`\`$sample_line\`\`\`",
                    "short": false
                }
            ]
        }
    ]
}
EOF
    )
    
    if curl -X POST -H 'Content-type: application/json' --data "$payload" "$webhook_url" >/dev/null 2>&1; then
        log_info "Slack alert sent for pattern: $pattern_name"
    else
        log_error "Failed to send Slack alert"
        return 1
    fi
}

# Send webhook alert
send_webhook_alert() {
    local pattern_name="$1"
    local count="$2"
    local sample_line="$3"
    local webhook_url="${WEBHOOK_URL:-}"
    
    if [[ -z "$webhook_url" ]]; then
        log_error "Webhook URL not configured"
        return 1
    fi
    
    local payload=$(cat << EOF
{
    "alert_type": "log_pattern",
    "pattern": "$pattern_name",
    "count": $count,
    "sample_log": "$sample_line",
    "timestamp": "$(date -Iseconds)",
    "hostname": "$(hostname)",
    "severity": "$(if [[ $count -gt 10 ]]; then echo "high"; elif [[ $count -gt 5 ]]; then echo "medium"; else echo "low"; fi)"
}
EOF
    )
    
    if curl -X POST -H 'Content-type: application/json' -H 'User-Agent: log-monitor/1.0' --data "$payload" "$webhook_url" >/dev/null 2>&1; then
        log_info "Webhook alert sent for pattern: $pattern_name"
    else
        log_error "Failed to send webhook alert"
        return 1
    fi
}

# Alert management and deduplication
manage_alerts() {
    local alert_cache_dir="/tmp/log_alerts"
    local alert_cooldown="${ALERT_COOLDOWN:-300}"  # 5 minutes
    
    mkdir -p "$alert_cache_dir"
    
    # Cleanup old alerts
    find "$alert_cache_dir" -type f -mmin +$((alert_cooldown / 60)) -delete
    
    local pattern_name="$1"
    local alert_key="${pattern_name// /_}"
    local alert_file="$alert_cache_dir/$alert_key"
    
    # Check if alert was recently sent
    if [[ -f "$alert_file" ]]; then
        local last_alert=$(cat "$alert_file")
        local current_time=$(date +%s)
        local time_diff=$((current_time - last_alert))
        
        if [[ $time_diff -lt $alert_cooldown ]]; then
            log_debug "Alert suppressed (cooldown): $pattern_name"
            return 1
        fi
    fi
    
    # Record alert timestamp
    date +%s > "$alert_file"
    return 0
}
```

## Log Analysis Scripts

### 1. Complete Log Analysis Script
```bash
#!/bin/bash

# Complete log analysis script
main() {
    local log_file="$1"
    local log_type="${2:-auto}"
    local output_dir="${3:-./log_analysis_$(date +%Y%m%d_%H%M%S)}"
    local mode="${4:-analysis}"  # analysis, monitor, aggregate
    
    # Validate inputs
    if [[ -z "$log_file" ]]; then
        echo "Usage: $0 <log_file> [log_type] [output_dir] [mode]"
        echo "  log_type: apache, nginx, application, syslog, auto"
        echo "  mode: analysis, monitor, aggregate"
        exit 1
    fi
    
    if [[ ! -f "$log_file" ]]; then
        log_error "Log file not found: $log_file"
        exit 1
    fi
    
    # Auto-detect log type if needed
    if [[ "$log_type" == "auto" ]]; then
        log_type=$(detect_log_type "$log_file")
        log_info "Detected log type: $log_type"
    fi
    
    mkdir -p "$output_dir"
    
    case "$mode" in
        analysis)
            log_info "Starting log analysis..."
            case "$log_type" in
                apache|nginx)
                    analyze_access_logs "$log_file" "$output_dir"
                    ;;
                application)
                    analyze_application_logs "$log_file" "$output_dir"
                    ;;
                *)
                    generic_log_analysis "$log_file" "$output_dir"
                    ;;
            esac
            ;;
        monitor)
            log_info "Starting log monitoring..."
            monitor_logs "$log_file" "${output_dir}/monitor_config.conf"
            ;;
        aggregate)
            log_info "Starting log aggregation..."
            aggregate_logs "${output_dir}/sources.conf" "${output_dir}/aggregated.log"
            ;;
        *)
            log_error "Unknown mode: $mode"
            exit 1
            ;;
    esac
    
    success "Log processing completed. Output saved to: $output_dir"
}

# Auto-detect log type
detect_log_type() {
    local log_file="$1"
    
    # Sample first few lines
    local sample=$(head -10 "$log_file")
    
    if echo "$sample" | grep -q '\[.*\] ".*" [0-9]* [0-9]*'; then
        echo "apache"
    elif echo "$sample" | grep -q '- - \[.*\] ".*" [0-9]* [0-9]* ".*" ".*"'; then
        echo "nginx"
    elif echo "$sample" | grep -q '^\[[0-9T:-]*\] \[[A-Z]*\]'; then
        echo "application"
    elif echo "$sample" | grep -q '^[A-Z][a-z]* *[0-9]* [0-9:]*'; then
        echo "syslog"
    else
        echo "generic"
    fi
}

# Generic log analysis
generic_log_analysis() {
    local log_file="$1"
    local output_dir="$2"
    
    log_info "Performing generic log analysis..."
    
    # Basic statistics
    local total_lines=$(wc -l < "$log_file")
    local unique_lines=$(sort "$log_file" | uniq | wc -l)
    
    # Error analysis
    grep -iE "(error|fail|exception|critical)" "$log_file" > "$output_dir/errors.txt" 2>/dev/null || touch "$output_dir/errors.txt"
    local error_count=$(wc -l < "$output_dir/errors.txt")
    
    # Warning analysis
    grep -iE "(warn|warning|notice)" "$log_file" > "$output_dir/warnings.txt" 2>/dev/null || touch "$output_dir/warnings.txt"
    local warning_count=$(wc -l < "$output_dir/warnings.txt")
    
    # Generate summary
    cat > "$output_dir/summary.txt" << EOF
Generic Log Analysis Summary
===========================
Generated: $(date)
Log File: $log_file

Statistics:
-----------
Total Lines: $total_lines
Unique Lines: $unique_lines
Error Lines: $error_count
Warning Lines: $warning_count

Most Common Lines:
-----------------
$(sort "$log_file" | uniq -c | sort -rn | head -10)

Recent Activity:
---------------
$(tail -20 "$log_file")
EOF
    
    log_info "Generic analysis completed"
}

# Run the main function if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
```

This comprehensive Bash log processing and analysis framework provides powerful tools for parsing, monitoring, analyzing, and alerting on log files in DevOps environments.