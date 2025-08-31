# Bash Error Handling & Debugging

## Overview
Bash error handling and debugging covers comprehensive techniques for writing robust scripts with proper error detection, logging, debugging capabilities, and recovery mechanisms. This includes error trapping, debugging tools, logging frameworks, and systematic troubleshooting approaches.

## Error Handling Fundamentals

### 1. Error Detection and Exit Codes
```bash
#!/bin/bash

# Strict error handling
set -euo pipefail  # Exit on error, undefined vars, pipe failures

# Custom error codes
readonly E_SUCCESS=0
readonly E_GENERAL_ERROR=1
readonly E_MISUSE=2
readonly E_CONFIG_ERROR=3
readonly E_NETWORK_ERROR=4
readonly E_PERMISSION_ERROR=5
readonly E_FILE_NOT_FOUND=6
readonly E_TIMEOUT=7

# Error logging function
log_error() {
    local error_code="${1:-$E_GENERAL_ERROR}"
    local error_message="$2"
    local function_name="${FUNCNAME[1]:-main}"
    local line_number="${BASH_LINENO[0]:-0}"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    echo "[$timestamp] ERROR [$error_code] in $function_name:$line_number: $error_message" >&2
    
    # Log to file if LOG_FILE is set
    if [[ -n "${LOG_FILE:-}" ]]; then
        echo "[$timestamp] ERROR [$error_code] in $function_name:$line_number: $error_message" >> "$LOG_FILE"
    fi
}

# Success logging
log_success() {
    local message="$1"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] SUCCESS: $message"
    
    if [[ -n "${LOG_FILE:-}" ]]; then
        echo "[$timestamp] SUCCESS: $message" >> "$LOG_FILE"
    fi
}

# Warning logging
log_warning() {
    local message="$1"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] WARNING: $message" >&2
    
    if [[ -n "${LOG_FILE:-}" ]]; then
        echo "[$timestamp] WARNING: $message" >> "$LOG_FILE"
    fi
}

# Function execution with error handling
execute_with_error_handling() {
    local command="$1"
    local error_message="$2"
    local expected_exit_code="${3:-0}"
    
    log_info "Executing: $command"
    
    if eval "$command"; then
        local actual_exit_code=$?
        if [[ $actual_exit_code -eq $expected_exit_code ]]; then
            log_success "Command executed successfully: $command"
            return 0
        else
            log_error "$E_GENERAL_ERROR" "Command returned unexpected exit code $actual_exit_code (expected $expected_exit_code): $command"
            return $actual_exit_code
        fi
    else
        local exit_code=$?
        log_error "$exit_code" "$error_message: $command"
        return $exit_code
    fi
}

# Retry mechanism with exponential backoff
retry_command() {
    local command="$1"
    local max_attempts="${2:-3}"
    local base_delay="${3:-2}"
    local max_delay="${4:-60}"
    local attempt=1
    local delay=$base_delay
    
    while [[ $attempt -le $max_attempts ]]; do
        log_info "Attempt $attempt/$max_attempts: $command"
        
        if eval "$command"; then
            log_success "Command succeeded on attempt $attempt: $command"
            return 0
        else
            local exit_code=$?
            log_warning "Command failed on attempt $attempt with exit code $exit_code: $command"
            
            if [[ $attempt -eq $max_attempts ]]; then
                log_error "$exit_code" "Command failed after $max_attempts attempts: $command"
                return $exit_code
            fi
            
            log_info "Retrying in ${delay}s..."
            sleep "$delay"
            
            # Exponential backoff with max delay
            delay=$((delay * 2))
            if [[ $delay -gt $max_delay ]]; then
                delay=$max_delay
            fi
            
            ((attempt++))
        fi
    done
}

# Validate command exists
require_command() {
    local command="$1"
    local package_hint="${2:-}"
    
    if ! command -v "$command" >/dev/null 2>&1; then
        local error_msg="Required command not found: $command"
        if [[ -n "$package_hint" ]]; then
            error_msg="$error_msg (install with: $package_hint)"
        fi
        log_error "$E_MISUSE" "$error_msg"
        return $E_MISUSE
    fi
}

# Validate file exists and is readable
require_file() {
    local file_path="$1"
    local description="${2:-file}"
    
    if [[ ! -f "$file_path" ]]; then
        log_error "$E_FILE_NOT_FOUND" "$description not found: $file_path"
        return $E_FILE_NOT_FOUND
    fi
    
    if [[ ! -r "$file_path" ]]; then
        log_error "$E_PERMISSION_ERROR" "$description is not readable: $file_path"
        return $E_PERMISSION_ERROR
    fi
    
    return 0
}

# Validate directory exists and is writable
require_directory() {
    local dir_path="$1"
    local description="${2:-directory}"
    local create_if_missing="${3:-false}"
    
    if [[ ! -d "$dir_path" ]]; then
        if [[ "$create_if_missing" == "true" ]]; then
            if mkdir -p "$dir_path" 2>/dev/null; then
                log_success "Created $description: $dir_path"
            else
                log_error "$E_PERMISSION_ERROR" "Cannot create $description: $dir_path"
                return $E_PERMISSION_ERROR
            fi
        else
            log_error "$E_FILE_NOT_FOUND" "$description not found: $dir_path"
            return $E_FILE_NOT_FOUND
        fi
    fi
    
    if [[ ! -w "$dir_path" ]]; then
        log_error "$E_PERMISSION_ERROR" "$description is not writable: $dir_path"
        return $E_PERMISSION_ERROR
    fi
    
    return 0
}
```

### 2. Advanced Error Trapping
```bash
#!/bin/bash

# Global error tracking
declare -g SCRIPT_ERRORS=0
declare -g LAST_ERROR=""
declare -g ERROR_STACK=()

# Signal trap handler
signal_handler() {
    local signal="$1"
    local exit_code="${2:-130}"
    
    log_warning "Received signal: $signal"
    
    case "$signal" in
        INT)
            log_info "Interrupt signal received, cleaning up..."
            cleanup_handler
            exit 130
            ;;
        TERM)
            log_info "Termination signal received, cleaning up..."
            cleanup_handler
            exit 143
            ;;
        QUIT)
            log_info "Quit signal received, cleaning up..."
            cleanup_handler
            exit 131
            ;;
        *)
            log_error "$E_GENERAL_ERROR" "Unknown signal received: $signal"
            cleanup_handler
            exit "$exit_code"
            ;;
    esac
}

# Error trap handler
error_handler() {
    local exit_code=$?
    local line_number=$1
    local bash_lineno=$2
    local last_command="${3:-}"
    local function_stack=("${FUNCNAME[@]:1}")
    
    # Skip if exit code is 0
    [[ $exit_code -eq 0 ]] && return 0
    
    ((SCRIPT_ERRORS++))
    
    # Build error context
    local error_context=""
    if [[ ${#function_stack[@]} -gt 0 ]]; then
        error_context="Function stack: ${function_stack[*]}"
    fi
    
    # Log detailed error information
    log_error "$exit_code" "Script failed at line $line_number (bash line $bash_lineno)"
    log_error "$exit_code" "Last command: $last_command"
    if [[ -n "$error_context" ]]; then
        log_error "$exit_code" "$error_context"
    fi
    
    # Add to error stack
    ERROR_STACK+=("Line $line_number: $last_command (exit code: $exit_code)")
    LAST_ERROR="Line $line_number: $last_command"
    
    # Generate stack trace
    generate_stack_trace
    
    # Call cleanup and exit
    cleanup_handler
    exit "$exit_code"
}

# Generate stack trace
generate_stack_trace() {
    local frame=0
    
    log_error "$E_GENERAL_ERROR" "=== Stack Trace ==="
    
    while [[ $frame -lt ${#FUNCNAME[@]} ]]; do
        local func_name="${FUNCNAME[$frame]}"
        local source_file="${BASH_SOURCE[$frame]}"
        local line_num="${BASH_LINENO[$frame-1]:-0}"
        
        if [[ "$func_name" != "error_handler" && "$func_name" != "generate_stack_trace" ]]; then
            log_error "$E_GENERAL_ERROR" "  $frame: $func_name() at $source_file:$line_num"
        fi
        
        ((frame++))
    done
    
    log_error "$E_GENERAL_ERROR" "=== End Stack Trace ==="
}

# Set up comprehensive error trapping
setup_error_handling() {
    # Set strict mode
    set -euo pipefail
    
    # Set up signal traps
    trap 'signal_handler INT' INT
    trap 'signal_handler TERM' TERM
    trap 'signal_handler QUIT' QUIT
    
    # Set up error trap with detailed information
    trap 'error_handler $LINENO $BASH_LINENO "$BASH_COMMAND"' ERR
    
    # Set up exit trap
    trap 'exit_handler $?' EXIT
}

# Exit handler
exit_handler() {
    local exit_code=$?
    
    if [[ $exit_code -eq 0 ]]; then
        if [[ $SCRIPT_ERRORS -eq 0 ]]; then
            log_success "Script completed successfully"
        else
            log_warning "Script completed with $SCRIPT_ERRORS non-fatal errors"
        fi
    else
        log_error "$exit_code" "Script failed with exit code $exit_code"
        
        # Print error summary
        if [[ ${#ERROR_STACK[@]} -gt 0 ]]; then
            log_error "$exit_code" "Error Summary:"
            for error in "${ERROR_STACK[@]}"; do
                log_error "$exit_code" "  $error"
            done
        fi
    fi
    
    # Don't call cleanup here as it should be called by error_handler
    return "$exit_code"
}

# Cleanup handler
cleanup_handler() {
    local cleanup_exit_code=$?
    
    log_info "Performing cleanup..."
    
    # Stop any background processes
    if [[ -n "${BACKGROUND_PIDS:-}" ]]; then
        for pid in $BACKGROUND_PIDS; do
            if kill -0 "$pid" 2>/dev/null; then
                log_info "Stopping background process: $pid"
                kill "$pid" 2>/dev/null || true
                wait "$pid" 2>/dev/null || true
            fi
        done
    fi
    
    # Remove temporary files
    if [[ -n "${TEMP_FILES:-}" ]]; then
        for temp_file in $TEMP_FILES; do
            if [[ -f "$temp_file" ]]; then
                log_info "Removing temporary file: $temp_file"
                rm -f "$temp_file"
            fi
        done
    fi
    
    # Remove temporary directories
    if [[ -n "${TEMP_DIRS:-}" ]]; then
        for temp_dir in $TEMP_DIRS; do
            if [[ -d "$temp_dir" ]]; then
                log_info "Removing temporary directory: $temp_dir"
                rm -rf "$temp_dir"
            fi
        done
    fi
    
    # Release locks
    if [[ -n "${LOCK_FILES:-}" ]]; then
        for lock_file in $LOCK_FILES; do
            if [[ -f "$lock_file" ]]; then
                log_info "Releasing lock: $lock_file"
                rm -f "$lock_file"
            fi
        done
    fi
    
    log_info "Cleanup completed"
}

# Safe execution wrapper
safe_execute() {
    local description="$1"
    shift
    local command=("$@")
    
    log_info "Starting: $description"
    
    # Temporarily disable error exit for controlled error handling
    set +e
    "${command[@]}"
    local exit_code=$?
    set -e
    
    if [[ $exit_code -eq 0 ]]; then
        log_success "Completed: $description"
    else
        log_error "$exit_code" "Failed: $description"
        return $exit_code
    fi
}

# Critical section execution (with locking)
execute_critical_section() {
    local section_name="$1"
    local lock_file="/tmp/${SCRIPT_NAME:-bash_script}_${section_name}.lock"
    local timeout="${2:-300}"  # 5 minutes default
    
    shift 2
    local commands=("$@")
    
    # Acquire lock
    local wait_time=0
    local wait_interval=2
    
    while [[ $wait_time -lt $timeout ]]; do
        if (set -C; echo $$ > "$lock_file") 2>/dev/null; then
            log_info "Acquired lock for critical section: $section_name"
            LOCK_FILES="${LOCK_FILES:-} $lock_file"
            break
        fi
        
        log_debug "Waiting for lock: $section_name (${wait_time}s/${timeout}s)"
        sleep $wait_interval
        wait_time=$((wait_time + wait_interval))
    done
    
    if [[ $wait_time -ge $timeout ]]; then
        log_error "$E_TIMEOUT" "Timeout acquiring lock for critical section: $section_name"
        return $E_TIMEOUT
    fi
    
    # Execute commands in critical section
    local section_exit_code=0
    for command in "${commands[@]}"; do
        if ! eval "$command"; then
            section_exit_code=$?
            log_error "$section_exit_code" "Command failed in critical section '$section_name': $command"
            break
        fi
    done
    
    # Release lock
    if [[ -f "$lock_file" ]]; then
        rm -f "$lock_file"
        log_info "Released lock for critical section: $section_name"
    fi
    
    return $section_exit_code
}
```

## Debugging Tools and Techniques

### 1. Debug Mode and Tracing
```bash
#!/bin/bash

# Debug configuration
DEBUG_ENABLED="${DEBUG:-false}"
DEBUG_LEVEL="${DEBUG_LEVEL:-1}"  # 1=basic, 2=detailed, 3=verbose
DEBUG_OUTPUT="${DEBUG_OUTPUT:-stderr}"  # stderr, file, both
DEBUG_FILE="${DEBUG_FILE:-debug.log}"

# Debug logging function
debug_log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S.%3N')
    local caller="${FUNCNAME[1]:-main}"
    local line="${BASH_LINENO[0]:-0}"
    
    # Check if debug is enabled and level is appropriate
    [[ "$DEBUG_ENABLED" != "true" ]] && return 0
    [[ $level -gt $DEBUG_LEVEL ]] && return 0
    
    local debug_msg="[$timestamp] DEBUG[$level] $caller:$line: $message"
    
    case "$DEBUG_OUTPUT" in
        stderr)
            echo "$debug_msg" >&2
            ;;
        file)
            echo "$debug_msg" >> "$DEBUG_FILE"
            ;;
        both)
            echo "$debug_msg" >&2
            echo "$debug_msg" >> "$DEBUG_FILE"
            ;;
    esac
}

# Function entry/exit tracing
trace_function() {
    local func_name="${FUNCNAME[1]}"
    local args=("$@")
    
    debug_log 2 "ENTER: $func_name(${args[*]})"
    
    # Set up exit trap for this function
    trap "debug_log 2 'EXIT: $func_name (exit code: \$?)'" RETURN
}

# Variable state debugging
debug_vars() {
    local vars=("$@")
    
    debug_log 2 "Variable state:"
    for var in "${vars[@]}"; do
        if [[ -n "${!var:-}" ]]; then
            debug_log 2 "  $var='${!var}'"
        else
            debug_log 2 "  $var=(unset or empty)"
        fi
    done
}

# Debug array contents
debug_array() {
    local array_name="$1"
    local -n array_ref=$1
    
    debug_log 2 "Array $array_name contents:"
    local i=0
    for element in "${array_ref[@]}"; do
        debug_log 2 "  [$i]: '$element'"
        ((i++))
    done
    debug_log 2 "  Total elements: ${#array_ref[@]}"
}

# Command execution with debugging
debug_exec() {
    local command=("$@")
    
    debug_log 1 "Executing: ${command[*]}"
    
    if [[ $DEBUG_LEVEL -ge 3 ]]; then
        # Show environment variables
        debug_log 3 "Environment:"
        env | sort | while IFS='=' read -r key value; do
            debug_log 3 "  $key='$value'"
        done
    fi
    
    # Execute with detailed output in debug mode
    if [[ $DEBUG_LEVEL -ge 2 ]]; then
        set -x  # Enable command tracing
        "${command[@]}"
        local exit_code=$?
        set +x  # Disable command tracing
    else
        "${command[@]}"
        local exit_code=$?
    fi
    
    debug_log 1 "Command exit code: $exit_code"
    return $exit_code
}

# Interactive debugging breakpoint
debug_breakpoint() {
    local message="${1:-Debug breakpoint reached}"
    
    if [[ "$DEBUG_ENABLED" != "true" ]]; then
        return 0
    fi
    
    echo "=== DEBUG BREAKPOINT ===" >&2
    echo "$message" >&2
    echo "Current function: ${FUNCNAME[1]:-main}" >&2
    echo "Line: ${BASH_LINENO[0]:-0}" >&2
    echo >&2
    echo "Available commands:" >&2
    echo "  c - continue execution" >&2
    echo "  v <var> - show variable value" >&2
    echo "  s - show call stack" >&2
    echo "  e <cmd> - execute command" >&2
    echo "  q - quit script" >&2
    echo >&2
    
    while true; do
        read -p "debug> " -r debug_command debug_args
        
        case "$debug_command" in
            c|continue)
                break
                ;;
            v|var)
                if [[ -n "$debug_args" ]]; then
                    if [[ -n "${!debug_args:-}" ]]; then
                        echo "$debug_args='${!debug_args}'" >&2
                    else
                        echo "$debug_args=(unset or empty)" >&2
                    fi
                else
                    echo "Usage: v <variable_name>" >&2
                fi
                ;;
            s|stack)
                echo "Call stack:" >&2
                local i=1
                while [[ $i -lt ${#FUNCNAME[@]} ]]; do
                    echo "  $((i-1)): ${FUNCNAME[i]}() at ${BASH_SOURCE[i]}:${BASH_LINENO[i-1]}" >&2
                    ((i++))
                done
                ;;
            e|exec)
                if [[ -n "$debug_args" ]]; then
                    eval "$debug_args"
                else
                    echo "Usage: e <command>" >&2
                fi
                ;;
            q|quit)
                echo "Exiting script from debugger" >&2
                exit 1
                ;;
            *)
                echo "Unknown command: $debug_command" >&2
                ;;
        esac
    done
    
    echo "Continuing execution..." >&2
}

# Performance timing
time_function() {
    local func_name="$1"
    shift
    local args=("$@")
    
    debug_log 1 "TIMING: Starting $func_name"
    local start_time=$(date +%s.%N)
    
    # Execute function
    "$func_name" "${args[@]}"
    local exit_code=$?
    
    local end_time=$(date +%s.%N)
    local duration=$(echo "$end_time - $start_time" | bc -l 2>/dev/null || echo "unknown")
    
    debug_log 1 "TIMING: $func_name completed in ${duration}s (exit code: $exit_code)"
    
    return $exit_code
}

# Memory usage tracking
debug_memory_usage() {
    local label="${1:-Memory usage}"
    
    if command -v ps >/dev/null 2>&1; then
        local memory_kb=$(ps -o rss= -p $$)
        local memory_mb=$((memory_kb / 1024))
        debug_log 2 "$label: ${memory_mb}MB (${memory_kb}KB)"
    fi
}

# File descriptor debugging
debug_file_descriptors() {
    debug_log 2 "Open file descriptors:"
    if [[ -d /proc/$$/fd ]]; then
        ls -la /proc/$$/fd/ | while read -r line; do
            debug_log 2 "  $line"
        done
    fi
}
```

### 2. Comprehensive Logging Framework
```bash
#!/bin/bash

# Logging configuration
LOG_LEVEL="${LOG_LEVEL:-INFO}"  # DEBUG, INFO, WARN, ERROR
LOG_FILE="${LOG_FILE:-}"
LOG_MAX_SIZE="${LOG_MAX_SIZE:-10485760}"  # 10MB
LOG_MAX_FILES="${LOG_MAX_FILES:-5}"
LOG_FORMAT="${LOG_FORMAT:-standard}"  # standard, json, syslog

# Log level priorities
declare -A LOG_PRIORITIES=(
    [DEBUG]=10
    [INFO]=20
    [WARN]=30
    [ERROR]=40
)

# Structured logging function
structured_log() {
    local level="$1"
    local message="$2"
    local component="${3:-main}"
    local extra_fields="${4:-}"
    
    # Check if this log level should be output
    local current_priority=${LOG_PRIORITIES[$LOG_LEVEL]:-20}
    local message_priority=${LOG_PRIORITIES[$level]:-20}
    
    [[ $message_priority -lt $current_priority ]] && return 0
    
    local timestamp=$(date -u '+%Y-%m-%dT%H:%M:%S.%3NZ')
    local hostname=$(hostname)
    local process_id=$$
    local thread_id="${BASH_SUBSHELL:-0}"
    
    local log_entry=""
    
    case "$LOG_FORMAT" in
        json)
            # JSON structured logging
            log_entry=$(cat << EOF
{
  "timestamp": "$timestamp",
  "level": "$level",
  "message": "$message",
  "component": "$component",
  "hostname": "$hostname",
  "pid": $process_id,
  "thread": $thread_id,
  "script": "${BASH_SOURCE[1]:-$0}",
  "function": "${FUNCNAME[2]:-main}",
  "line": ${BASH_LINENO[1]:-0}
$(if [[ -n "$extra_fields" ]]; then echo "  ,$extra_fields"; fi)
}
EOF
            )
            ;;
        syslog)
            # Syslog format
            local facility="user"
            local severity=""
            case "$level" in
                DEBUG) severity="debug" ;;
                INFO) severity="info" ;;
                WARN) severity="warning" ;;
                ERROR) severity="err" ;;
            esac
            log_entry="<$facility.$severity> $timestamp $hostname $0[$process_id]: [$level] $component: $message"
            ;;
        *)
            # Standard format
            log_entry="[$timestamp] [$level] [$component] $message"
            ;;
    esac
    
    # Output to appropriate destination
    if [[ "$level" == "ERROR" || "$level" == "WARN" ]]; then
        echo "$log_entry" >&2
    else
        echo "$log_entry"
    fi
    
    # Write to log file if configured
    if [[ -n "$LOG_FILE" ]]; then
        echo "$log_entry" >> "$LOG_FILE"
        
        # Rotate log file if needed
        rotate_log_file
    fi
}

# Log rotation
rotate_log_file() {
    [[ -z "$LOG_FILE" ]] && return 0
    [[ ! -f "$LOG_FILE" ]] && return 0
    
    local file_size=$(stat -f%z "$LOG_FILE" 2>/dev/null || stat -c%s "$LOG_FILE" 2>/dev/null || echo "0")
    
    if [[ $file_size -gt $LOG_MAX_SIZE ]]; then
        log_info "Rotating log file: $LOG_FILE (size: $file_size bytes)"
        
        # Rotate existing files
        for ((i=LOG_MAX_FILES-1; i>0; i--)); do
            local old_file="${LOG_FILE}.$i"
            local new_file="${LOG_FILE}.$((i+1))"
            
            if [[ -f "$old_file" ]]; then
                mv "$old_file" "$new_file" 2>/dev/null || true
            fi
        done
        
        # Move current log to .1
        mv "$LOG_FILE" "${LOG_FILE}.1" 2>/dev/null || true
        
        # Remove oldest log file
        rm -f "${LOG_FILE}.$((LOG_MAX_FILES+1))" 2>/dev/null || true
    fi
}

# Convenience logging functions
log_debug() {
    structured_log "DEBUG" "$1" "${2:-main}" "${3:-}"
}

log_info() {
    structured_log "INFO" "$1" "${2:-main}" "${3:-}"
}

log_warn() {
    structured_log "WARN" "$1" "${2:-main}" "${3:-}"
}

log_error() {
    structured_log "ERROR" "$1" "${2:-main}" "${3:-}"
}

# Context-aware logging
with_log_context() {
    local context="$1"
    shift
    local command=("$@")
    
    log_info "Starting context: $context"
    
    # Execute command with context
    "${command[@]}"
    local exit_code=$?
    
    if [[ $exit_code -eq 0 ]]; then
        log_info "Completed context: $context"
    else
        log_error "Failed context: $context (exit code: $exit_code)"
    fi
    
    return $exit_code
}

# Log aggregation for multiple processes
setup_log_aggregation() {
    local log_dir="$1"
    local aggregated_log="$2"
    
    mkdir -p "$log_dir"
    
    # Watch for new log files and aggregate them
    while true; do
        for log_file in "$log_dir"/*.log; do
            if [[ -f "$log_file" && "$log_file" != "$aggregated_log" ]]; then
                # Add process ID prefix to each line
                local process_id=$(basename "$log_file" .log)
                
                while IFS= read -r line; do
                    echo "[$process_id] $line" >> "$aggregated_log"
                done < "$log_file"
                
                # Clear the individual log file
                > "$log_file"
            fi
        done
        
        sleep 1
    done &
    
    echo $! > "$log_dir/aggregator.pid"
}
```

### 3. Error Recovery and Resilience
```bash
#!/bin/bash

# Circuit breaker implementation
declare -A CIRCUIT_BREAKERS
declare -A CIRCUIT_FAILURE_COUNTS
declare -A CIRCUIT_LAST_FAILURE_TIME

# Circuit breaker states
readonly CB_CLOSED=0
readonly CB_OPEN=1
readonly CB_HALF_OPEN=2

# Circuit breaker configuration
readonly CB_FAILURE_THRESHOLD=5
readonly CB_TIMEOUT=60  # seconds
readonly CB_SUCCESS_THRESHOLD=3

# Initialize circuit breaker
init_circuit_breaker() {
    local name="$1"
    CIRCUIT_BREAKERS["$name"]=$CB_CLOSED
    CIRCUIT_FAILURE_COUNTS["$name"]=0
    CIRCUIT_LAST_FAILURE_TIME["$name"]=0
}

# Execute command through circuit breaker
circuit_breaker_execute() {
    local breaker_name="$1"
    shift
    local command=("$@")
    
    # Initialize if not exists
    [[ -z "${CIRCUIT_BREAKERS[$breaker_name]:-}" ]] && init_circuit_breaker "$breaker_name"
    
    local state=${CIRCUIT_BREAKERS[$breaker_name]}
    local current_time=$(date +%s)
    
    case $state in
        $CB_OPEN)
            # Check if timeout period has passed
            local last_failure=${CIRCUIT_LAST_FAILURE_TIME[$breaker_name]}
            if [[ $((current_time - last_failure)) -gt $CB_TIMEOUT ]]; then
                log_info "Circuit breaker $breaker_name transitioning to HALF_OPEN"
                CIRCUIT_BREAKERS["$breaker_name"]=$CB_HALF_OPEN
            else
                log_error "$E_GENERAL_ERROR" "Circuit breaker $breaker_name is OPEN, request rejected"
                return $E_GENERAL_ERROR
            fi
            ;;
    esac
    
    # Execute command
    if "${command[@]}"; then
        # Success
        case $state in
            $CB_HALF_OPEN)
                log_info "Circuit breaker $breaker_name transitioning to CLOSED"
                CIRCUIT_BREAKERS["$breaker_name"]=$CB_CLOSED
                CIRCUIT_FAILURE_COUNTS["$breaker_name"]=0
                ;;
        esac
        return 0
    else
        # Failure
        local exit_code=$?
        CIRCUIT_FAILURE_COUNTS["$breaker_name"]=$((${CIRCUIT_FAILURE_COUNTS[$breaker_name]} + 1))
        CIRCUIT_LAST_FAILURE_TIME["$breaker_name"]=$current_time
        
        local failure_count=${CIRCUIT_FAILURE_COUNTS[$breaker_name]}
        
        if [[ $failure_count -ge $CB_FAILURE_THRESHOLD ]]; then
            log_error "$E_GENERAL_ERROR" "Circuit breaker $breaker_name transitioning to OPEN (failures: $failure_count)"
            CIRCUIT_BREAKERS["$breaker_name"]=$CB_OPEN
        fi
        
        return $exit_code
    fi
}

# Graceful degradation
graceful_degradation() {
    local primary_command=("$1")
    local fallback_command=("$2")
    local description="$3"
    
    log_info "Attempting primary operation: $description"
    
    if "${primary_command[@]}"; then
        log_success "Primary operation succeeded: $description"
        return 0
    else
        log_warn "Primary operation failed, trying fallback: $description"
        
        if "${fallback_command[@]}"; then
            log_success "Fallback operation succeeded: $description"
            return 0
        else
            log_error "$E_GENERAL_ERROR" "Both primary and fallback operations failed: $description"
            return $E_GENERAL_ERROR
        fi
    fi
}

# Checkpoint and recovery system
create_checkpoint() {
    local checkpoint_name="$1"
    local state_data="$2"
    local checkpoint_dir="${CHECKPOINT_DIR:-./checkpoints}"
    
    mkdir -p "$checkpoint_dir"
    
    local checkpoint_file="$checkpoint_dir/${checkpoint_name}.checkpoint"
    
    cat > "$checkpoint_file" << EOF
#!/bin/bash
# Checkpoint created at: $(date)
# State data:
$state_data
EOF
    
    log_info "Checkpoint created: $checkpoint_name"
}

# Restore from checkpoint
restore_checkpoint() {
    local checkpoint_name="$1"
    local checkpoint_dir="${CHECKPOINT_DIR:-./checkpoints}"
    local checkpoint_file="$checkpoint_dir/${checkpoint_name}.checkpoint"
    
    if [[ -f "$checkpoint_file" ]]; then
        log_info "Restoring from checkpoint: $checkpoint_name"
        source "$checkpoint_file"
        return 0
    else
        log_error "$E_FILE_NOT_FOUND" "Checkpoint not found: $checkpoint_name"
        return $E_FILE_NOT_FOUND
    fi
}

# Health check with recovery
health_check_with_recovery() {
    local service_name="$1"
    local health_check_command=("$2")
    local recovery_command=("$3")
    local max_recovery_attempts="${4:-3}"
    
    local attempt=0
    
    while [[ $attempt -le $max_recovery_attempts ]]; do
        if [[ $attempt -gt 0 ]]; then
            log_info "Health check attempt $attempt for $service_name"
        fi
        
        if "${health_check_command[@]}"; then
            if [[ $attempt -gt 0 ]]; then
                log_success "Service $service_name recovered after $attempt attempts"
            fi
            return 0
        else
            log_warn "Health check failed for $service_name"
            
            if [[ $attempt -lt $max_recovery_attempts ]]; then
                log_info "Attempting recovery for $service_name"
                if "${recovery_command[@]}"; then
                    log_info "Recovery command executed for $service_name"
                    sleep 5  # Wait for recovery to take effect
                else
                    log_error "$E_GENERAL_ERROR" "Recovery command failed for $service_name"
                fi
            fi
        fi
        
        ((attempt++))
    done
    
    log_error "$E_GENERAL_ERROR" "Service $service_name failed to recover after $max_recovery_attempts attempts"
    return $E_GENERAL_ERROR
}

# Bulkhead pattern implementation
execute_with_resource_isolation() {
    local resource_pool="$1"
    local max_concurrent="${2:-5}"
    shift 2
    local command=("$@")
    
    local lock_dir="/tmp/resource_pools/$resource_pool"
    mkdir -p "$lock_dir"
    
    # Count current processes in this pool
    local current_count=$(ls "$lock_dir"/*.lock 2>/dev/null | wc -l)
    
    if [[ $current_count -ge $max_concurrent ]]; then
        log_error "$E_GENERAL_ERROR" "Resource pool $resource_pool at capacity ($current_count/$max_concurrent)"
        return $E_GENERAL_ERROR
    fi
    
    # Acquire resource slot
    local slot_file="$lock_dir/$$.lock"
    echo $$ > "$slot_file"
    
    log_info "Acquired resource slot in pool $resource_pool ($((current_count + 1))/$max_concurrent)"
    
    # Execute command
    "${command[@]}"
    local exit_code=$?
    
    # Release resource slot
    rm -f "$slot_file"
    log_info "Released resource slot in pool $resource_pool"
    
    return $exit_code
}
```

This comprehensive error handling and debugging framework provides robust error detection, detailed logging, debugging tools, and recovery mechanisms for production-ready Bash scripts.