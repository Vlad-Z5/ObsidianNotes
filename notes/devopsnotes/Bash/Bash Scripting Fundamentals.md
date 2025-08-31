# Bash Scripting Fundamentals

## Overview
Bash scripting fundamentals cover the essential concepts, syntax, and patterns needed to write effective shell scripts for DevOps automation, system administration, and infrastructure management. This includes variables, control structures, functions, and best practices for maintainable scripts.

## Basic Script Structure

### 1. Shebang and Script Headers
```bash
#!/bin/bash

# Script: system_backup.sh
# Purpose: Automated system backup with logging
# Author: DevOps Team
# Version: 1.2.0
# Usage: ./system_backup.sh [--dry-run] [--config CONFIG_FILE]

set -euo pipefail  # Exit on error, undefined vars, pipe failures

# Script configuration
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly SCRIPT_NAME="$(basename "$0")"
readonly LOG_FILE="${SCRIPT_DIR}/logs/${SCRIPT_NAME%.*}.log"

# Create log directory if it doesn't exist
mkdir -p "$(dirname "$LOG_FILE")"
```

### 2. Variables and Parameter Expansion
```bash
#!/bin/bash

# Variable declarations
readonly APP_NAME="myapp"
readonly APP_VERSION="1.0.0"
readonly TIMESTAMP="$(date +%Y%m%d_%H%M%S)"

# Environment variables with defaults
readonly ENVIRONMENT="${ENVIRONMENT:-development}"
readonly LOG_LEVEL="${LOG_LEVEL:-INFO}"
readonly BACKUP_RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-7}"

# Parameter expansion examples
config_file="${1:-config.yaml}"                    # Use first arg or default
backup_dir="${BACKUP_DIR:-/var/backups/${APP_NAME}}"
log_file="${LOG_DIR:+${LOG_DIR}/}${SCRIPT_NAME}.log"  # Conditional expansion

# Array variables
declare -a SERVICES=("nginx" "postgresql" "redis")
declare -A CONFIG=(
    [database_host]="localhost"
    [database_port]="5432"
    [redis_port]="6379"
)

# String manipulation
app_upper="${APP_NAME^^}"           # Convert to uppercase
app_lower="${APP_NAME,,}"           # Convert to lowercase
filename="${config_file##*/}"       # Extract filename
extension="${filename##*.}"         # Extract extension
basename="${filename%.*}"           # Remove extension

echo "Processing ${filename} (${extension} file)"
echo "Config: ${CONFIG[database_host]}:${CONFIG[database_port]}"
```

### 3. Command-Line Argument Processing
```bash
#!/bin/bash

# Function to display usage
usage() {
    cat << EOF
Usage: $0 [OPTIONS]

OPTIONS:
    -h, --help              Display this help message
    -c, --config FILE       Configuration file (default: config.yaml)
    -e, --env ENV           Environment (dev/staging/prod)
    -v, --verbose           Enable verbose output
    -d, --dry-run           Show what would be done without executing
    --log-level LEVEL       Log level (DEBUG/INFO/WARN/ERROR)

Examples:
    $0 --config prod.yaml --env production
    $0 --dry-run --verbose
EOF
}

# Initialize variables
CONFIG_FILE="config.yaml"
ENVIRONMENT="development"
VERBOSE=false
DRY_RUN=false
LOG_LEVEL="INFO"

# Process command-line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            usage
            exit 0
            ;;
        -c|--config)
            CONFIG_FILE="$2"
            shift 2
            ;;
        -e|--env)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -d|--dry-run)
            DRY_RUN=true
            shift
            ;;
        --log-level)
            LOG_LEVEL="$2"
            shift 2
            ;;
        -*)
            echo "Error: Unknown option $1" >&2
            usage >&2
            exit 1
            ;;
        *)
            echo "Error: Unexpected argument $1" >&2
            usage >&2
            exit 1
            ;;
    esac
done

# Validate required parameters
if [[ ! -f "$CONFIG_FILE" ]]; then
    echo "Error: Configuration file '$CONFIG_FILE' not found" >&2
    exit 1
fi

echo "Configuration: $CONFIG_FILE"
echo "Environment: $ENVIRONMENT"
echo "Verbose: $VERBOSE"
echo "Dry Run: $DRY_RUN"
```

## Control Structures

### 1. Conditional Statements
```bash
#!/bin/bash

# Function to check system requirements
check_requirements() {
    local required_commands=("git" "docker" "kubectl" "helm")
    local missing_commands=()
    
    # Check each required command
    for cmd in "${required_commands[@]}"; do
        if ! command -v "$cmd" >/dev/null 2>&1; then
            missing_commands+=("$cmd")
        fi
    done
    
    # Report missing commands
    if [[ ${#missing_commands[@]} -gt 0 ]]; then
        echo "Error: Missing required commands: ${missing_commands[*]}" >&2
        return 1
    fi
    
    # Check Docker daemon
    if ! docker info >/dev/null 2>&1; then
        echo "Error: Docker daemon is not running" >&2
        return 1
    fi
    
    # Check Kubernetes connection
    if ! kubectl cluster-info >/dev/null 2>&1; then
        echo "Warning: Cannot connect to Kubernetes cluster" >&2
    fi
    
    echo "All requirements satisfied"
    return 0
}

# Environment-specific configuration
configure_environment() {
    local env="$1"
    
    case "$env" in
        development|dev)
            readonly REPLICAS=1
            readonly RESOURCE_LIMIT="500m"
            readonly DEBUG_MODE=true
            ;;
        staging|stage)
            readonly REPLICAS=2
            readonly RESOURCE_LIMIT="1000m"
            readonly DEBUG_MODE=false
            ;;
        production|prod)
            readonly REPLICAS=3
            readonly RESOURCE_LIMIT="2000m"
            readonly DEBUG_MODE=false
            ;;
        *)
            echo "Error: Unknown environment '$env'" >&2
            echo "Supported environments: development, staging, production" >&2
            return 1
            ;;
    esac
    
    echo "Environment configured: $env"
    echo "Replicas: $REPLICAS"
    echo "Resource Limit: $RESOURCE_LIMIT"
}

# File validation with multiple conditions
validate_file() {
    local file="$1"
    
    if [[ ! -e "$file" ]]; then
        echo "Error: File '$file' does not exist" >&2
        return 1
    elif [[ ! -f "$file" ]]; then
        echo "Error: '$file' is not a regular file" >&2
        return 1
    elif [[ ! -r "$file" ]]; then
        echo "Error: File '$file' is not readable" >&2
        return 1
    elif [[ ! -s "$file" ]]; then
        echo "Warning: File '$file' is empty" >&2
    fi
    
    # Check file extension
    if [[ "$file" =~ \.(yaml|yml)$ ]]; then
        echo "Processing YAML file: $file"
    elif [[ "$file" =~ \.(json)$ ]]; then
        echo "Processing JSON file: $file"
    else
        echo "Warning: Unknown file type: $file" >&2
    fi
    
    return 0
}
```

### 2. Loops and Iteration
```bash
#!/bin/bash

# Process multiple services
deploy_services() {
    local services=("$@")
    local failed_services=()
    
    echo "Deploying ${#services[@]} services..."
    
    # For loop with array
    for service in "${services[@]}"; do
        echo "Deploying service: $service"
        
        if deploy_single_service "$service"; then
            echo "✓ Successfully deployed $service"
        else
            echo "✗ Failed to deploy $service" >&2
            failed_services+=("$service")
        fi
    done
    
    # Report results
    if [[ ${#failed_services[@]} -gt 0 ]]; then
        echo "Failed services: ${failed_services[*]}" >&2
        return 1
    fi
    
    echo "All services deployed successfully"
    return 0
}

# Wait for services to be ready
wait_for_services() {
    local services=("$@")
    local timeout=300  # 5 minutes
    local interval=10  # 10 seconds
    local elapsed=0
    
    echo "Waiting for services to be ready..."
    
    while [[ $elapsed -lt $timeout ]]; do
        local ready_count=0
        
        # Check each service
        for service in "${services[@]}"; do
            if kubectl get deployment "$service" -o jsonpath='{.status.readyReplicas}' >/dev/null 2>&1; then
                local ready_replicas=$(kubectl get deployment "$service" -o jsonpath='{.status.readyReplicas}')
                local desired_replicas=$(kubectl get deployment "$service" -o jsonpath='{.spec.replicas}')
                
                if [[ "$ready_replicas" == "$desired_replicas" && "$ready_replicas" -gt 0 ]]; then
                    ((ready_count++))
                fi
            fi
        done
        
        # Check if all services are ready
        if [[ $ready_count -eq ${#services[@]} ]]; then
            echo "✓ All services are ready"
            return 0
        fi
        
        echo "Waiting... ($ready_count/${#services[@]} services ready)"
        sleep $interval
        ((elapsed += interval))
    done
    
    echo "✗ Timeout waiting for services to be ready" >&2
    return 1
}

# Process files in directory
process_config_files() {
    local config_dir="$1"
    
    if [[ ! -d "$config_dir" ]]; then
        echo "Error: Directory '$config_dir' not found" >&2
        return 1
    fi
    
    # While loop reading from find output
    while IFS= read -r -d '' file; do
        echo "Processing config file: $file"
        
        # Validate YAML syntax
        if ! yq eval . "$file" >/dev/null 2>&1; then
            echo "Warning: Invalid YAML in $file" >&2
            continue
        fi
        
        # Apply configuration
        kubectl apply -f "$file"
        
    done < <(find "$config_dir" -name "*.yaml" -o -name "*.yml" -print0)
}

# C-style for loop for retry logic
retry_command() {
    local command="$1"
    local max_attempts=5
    local delay=2
    
    for ((attempt=1; attempt<=max_attempts; attempt++)); do
        echo "Attempt $attempt/$max_attempts: $command"
        
        if eval "$command"; then
            echo "✓ Command succeeded on attempt $attempt"
            return 0
        fi
        
        if [[ $attempt -lt $max_attempts ]]; then
            echo "Retrying in $delay seconds..."
            sleep $delay
            ((delay *= 2))  # Exponential backoff
        fi
    done
    
    echo "✗ Command failed after $max_attempts attempts" >&2
    return 1
}
```

## Functions and Modular Design

### 1. Function Definition and Best Practices
```bash
#!/bin/bash

# Global constants
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly NC='\033[0m' # No Color

# Logging function with levels
log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    case "$level" in
        ERROR)
            echo -e "${timestamp} [${RED}ERROR${NC}] $message" >&2
            ;;
        WARN)
            echo -e "${timestamp} [${YELLOW}WARN${NC}] $message" >&2
            ;;
        INFO)
            echo -e "${timestamp} [INFO] $message"
            ;;
        DEBUG)
            if [[ "${DEBUG:-false}" == "true" ]]; then
                echo -e "${timestamp} [DEBUG] $message"
            fi
            ;;
    esac
}

# Error handling function
die() {
    log ERROR "$@"
    exit 1
}

# Success function
success() {
    echo -e "${GREEN}✓${NC} $*"
}

# Validation function with multiple checks
validate_input() {
    local input="$1"
    local type="$2"
    
    # Check if input is provided
    if [[ -z "$input" ]]; then
        log ERROR "Input cannot be empty"
        return 1
    fi
    
    case "$type" in
        email)
            if [[ ! "$input" =~ ^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$ ]]; then
                log ERROR "Invalid email format: $input"
                return 1
            fi
            ;;
        url)
            if [[ ! "$input" =~ ^https?://[[:alnum:].-]+[[:alnum:]] ]]; then
                log ERROR "Invalid URL format: $input"
                return 1
            fi
            ;;
        port)
            if [[ ! "$input" =~ ^[0-9]+$ ]] || [[ "$input" -lt 1 ]] || [[ "$input" -gt 65535 ]]; then
                log ERROR "Invalid port number: $input (must be 1-65535)"
                return 1
            fi
            ;;
        ip)
            if [[ ! "$input" =~ ^([0-9]{1,3}\.){3}[0-9]{1,3}$ ]]; then
                log ERROR "Invalid IP address format: $input"
                return 1
            fi
            
            # Additional IP validation
            IFS='.' read -ra ADDR <<< "$input"
            for i in "${ADDR[@]}"; do
                if [[ $i -gt 255 ]]; then
                    log ERROR "Invalid IP address: $input"
                    return 1
                fi
            done
            ;;
        *)
            log WARN "Unknown validation type: $type"
            ;;
    esac
    
    return 0
}

# File operations with error handling
backup_file() {
    local source_file="$1"
    local backup_dir="${2:-./backups}"
    
    # Validate inputs
    if [[ ! -f "$source_file" ]]; then
        log ERROR "Source file does not exist: $source_file"
        return 1
    fi
    
    # Create backup directory
    if ! mkdir -p "$backup_dir"; then
        log ERROR "Cannot create backup directory: $backup_dir"
        return 1
    fi
    
    # Generate backup filename with timestamp
    local filename=$(basename "$source_file")
    local backup_file="${backup_dir}/${filename}.$(date +%Y%m%d_%H%M%S).bak"
    
    # Create backup
    if cp "$source_file" "$backup_file"; then
        log INFO "File backed up: $source_file -> $backup_file"
        echo "$backup_file"  # Return backup file path
        return 0
    else
        log ERROR "Failed to backup file: $source_file"
        return 1
    fi
}

# Network connectivity check
check_connectivity() {
    local host="$1"
    local port="${2:-80}"
    local timeout="${3:-5}"
    
    log INFO "Checking connectivity to $host:$port"
    
    if timeout "$timeout" bash -c "</dev/tcp/$host/$port" 2>/dev/null; then
        success "Connection to $host:$port successful"
        return 0
    else
        log ERROR "Cannot connect to $host:$port"
        return 1
    fi
}

# Process management functions
is_process_running() {
    local process_name="$1"
    
    if pgrep -f "$process_name" >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

wait_for_process() {
    local process_name="$1"
    local timeout="${2:-60}"
    local interval="${3:-2}"
    local elapsed=0
    
    log INFO "Waiting for process: $process_name"
    
    while [[ $elapsed -lt $timeout ]]; do
        if is_process_running "$process_name"; then
            success "Process $process_name is running"
            return 0
        fi
        
        sleep "$interval"
        ((elapsed += interval))
    done
    
    log ERROR "Timeout waiting for process: $process_name"
    return 1
}

# Cleanup function (trap handler)
cleanup() {
    local exit_code=$?
    
    log INFO "Performing cleanup..."
    
    # Stop background processes
    if [[ -n "${BACKGROUND_PID:-}" ]]; then
        log INFO "Stopping background process: $BACKGROUND_PID"
        kill "$BACKGROUND_PID" 2>/dev/null || true
    fi
    
    # Remove temporary files
    if [[ -n "${TEMP_DIR:-}" && -d "$TEMP_DIR" ]]; then
        log INFO "Removing temporary directory: $TEMP_DIR"
        rm -rf "$TEMP_DIR"
    fi
    
    # Log exit status
    if [[ $exit_code -eq 0 ]]; then
        success "Script completed successfully"
    else
        log ERROR "Script failed with exit code: $exit_code"
    fi
    
    exit $exit_code
}

# Set up trap for cleanup
trap cleanup EXIT INT TERM
```

## Input/Output and Data Processing

### 1. Reading and Processing Input
```bash
#!/bin/bash

# Read configuration from file
read_config() {
    local config_file="$1"
    local -n config_array=$2  # Nameref to associative array
    
    if [[ ! -f "$config_file" ]]; then
        log ERROR "Configuration file not found: $config_file"
        return 1
    fi
    
    log INFO "Reading configuration from: $config_file"
    
    # Read key=value pairs
    while IFS='=' read -r key value; do
        # Skip comments and empty lines
        [[ $key =~ ^[[:space:]]*# ]] && continue
        [[ -z "$key" ]] && continue
        
        # Remove leading/trailing whitespace
        key=$(echo "$key" | xargs)
        value=$(echo "$value" | xargs)
        
        # Remove quotes from value
        value="${value#\"}"
        value="${value%\"}"
        value="${value#\'}"
        value="${value%\'}"
        
        config_array["$key"]="$value"
        log DEBUG "Config: $key = $value"
        
    done < "$config_file"
    
    log INFO "Configuration loaded: ${#config_array[@]} entries"
}

# Interactive input with validation
get_user_input() {
    local prompt="$1"
    local var_name="$2"
    local validation_type="${3:-}"
    local default_value="${4:-}"
    local input
    
    while true; do
        if [[ -n "$default_value" ]]; then
            read -p "$prompt [$default_value]: " input
            input="${input:-$default_value}"
        else
            read -p "$prompt: " input
        fi
        
        # Validate input if validation type provided
        if [[ -n "$validation_type" ]]; then
            if validate_input "$input" "$validation_type"; then
                break
            else
                echo "Please try again."
                continue
            fi
        else
            break
        fi
    done
    
    # Set the variable using nameref
    declare -n result_var="$var_name"
    result_var="$input"
}

# Secure password input
get_password() {
    local prompt="$1"
    local var_name="$2"
    local password
    local password_confirm
    
    while true; do
        echo -n "$prompt: "
        read -s password
        echo
        
        echo -n "Confirm password: "
        read -s password_confirm
        echo
        
        if [[ "$password" == "$password_confirm" ]]; then
            if [[ ${#password} -ge 8 ]]; then
                break
            else
                echo "Password must be at least 8 characters long."
            fi
        else
            echo "Passwords do not match. Please try again."
        fi
    done
    
    declare -n result_var="$var_name"
    result_var="$password"
}

# Process CSV data
process_csv() {
    local csv_file="$1"
    local -i line_number=0
    local header_line
    
    if [[ ! -f "$csv_file" ]]; then
        log ERROR "CSV file not found: $csv_file"
        return 1
    fi
    
    log INFO "Processing CSV file: $csv_file"
    
    # Read and process CSV
    while IFS=',' read -ra fields; do
        ((line_number++))
        
        # Process header line
        if [[ $line_number -eq 1 ]]; then
            header_line=("${fields[@]}")
            log DEBUG "Header: ${header_line[*]}"
            continue
        fi
        
        # Process data lines
        log INFO "Processing line $line_number:"
        for i in "${!fields[@]}"; do
            local field_name="${header_line[$i]:-field_$i}"
            local field_value="${fields[$i]}"
            
            # Remove quotes and trim whitespace
            field_value="${field_value#\"}"
            field_value="${field_value%\"}"
            field_value=$(echo "$field_value" | xargs)
            
            log DEBUG "  $field_name: $field_value"
        done
        
    done < "$csv_file"
    
    log INFO "Processed $((line_number - 1)) data rows"
}
```

### 2. Output Formatting and Reporting
```bash
#!/bin/bash

# Report generation functions
generate_system_report() {
    local output_file="$1"
    local format="${2:-text}"  # text, json, html
    
    log INFO "Generating system report: $output_file ($format)"
    
    case "$format" in
        text)
            generate_text_report "$output_file"
            ;;
        json)
            generate_json_report "$output_file"
            ;;
        html)
            generate_html_report "$output_file"
            ;;
        *)
            log ERROR "Unsupported report format: $format"
            return 1
            ;;
    esac
}

# Text report generation
generate_text_report() {
    local output_file="$1"
    
    cat > "$output_file" << EOF
System Report
=============
Generated: $(date)
Hostname: $(hostname)
Uptime: $(uptime)

System Information:
-------------------
OS: $(uname -s)
Kernel: $(uname -r)
Architecture: $(uname -m)

Memory Usage:
-------------
$(free -h)

Disk Usage:
-----------
$(df -h | grep -v tmpfs | grep -v udev)

Network Interfaces:
------------------
$(ip addr show | grep -E '^[0-9]+:|inet ' | head -20)

Running Services:
----------------
$(systemctl list-units --type=service --state=running | head -10)

Recent Log Entries:
------------------
$(journalctl --since "1 hour ago" --no-pager | tail -10)
EOF
    
    success "Text report generated: $output_file"
}

# JSON report generation
generate_json_report() {
    local output_file="$1"
    
    # Collect system data
    local hostname=$(hostname)
    local kernel=$(uname -r)
    local arch=$(uname -m)
    local uptime_seconds=$(cat /proc/uptime | cut -d' ' -f1)
    
    # Generate JSON report
    cat > "$output_file" << EOF
{
  "report": {
    "generated": "$(date -Iseconds)",
    "hostname": "$hostname",
    "system": {
      "kernel": "$kernel",
      "architecture": "$arch",
      "uptime_seconds": $uptime_seconds
    },
    "memory": {
      "total_mb": $(free -m | awk '/^Mem:/ {print $2}'),
      "used_mb": $(free -m | awk '/^Mem:/ {print $3}'),
      "available_mb": $(free -m | awk '/^Mem:/ {print $7}')
    },
    "disk_usage": [
$(df -BM | grep -v tmpfs | grep -v udev | tail -n +2 | while read filesystem blocks used available percent mountpoint; do
    echo "      {"
    echo "        \"filesystem\": \"$filesystem\","
    echo "        \"size_mb\": ${blocks%M},"
    echo "        \"used_mb\": ${used%M},"
    echo "        \"available_mb\": ${available%M},"
    echo "        \"percent_used\": \"$percent\","
    echo "        \"mountpoint\": \"$mountpoint\""
    echo "      },"
done | sed '$ s/,$//')
    ],
    "services": {
      "running": $(systemctl list-units --type=service --state=running --no-pager | grep -c "\.service")
    }
  }
}
EOF
    
    success "JSON report generated: $output_file"
}

# Table formatting function
print_table() {
    local -n data=$1  # Array reference
    local headers=("$@")
    headers=("${headers[@]:1}")  # Remove first element (array name)
    
    # Calculate column widths
    local -a col_widths
    for i in "${!headers[@]}"; do
        col_widths[$i]=${#headers[$i]}
    done
    
    # Check data for max widths
    for row in "${data[@]}"; do
        IFS='|' read -ra fields <<< "$row"
        for i in "${!fields[@]}"; do
            if [[ ${#fields[$i]} -gt ${col_widths[$i]:-0} ]]; then
                col_widths[$i]=${#fields[$i]}
            fi
        done
    done
    
    # Print header
    printf "+"
    for width in "${col_widths[@]}"; do
        printf "%*s+" $((width + 2)) "" | tr ' ' '-'
    done
    printf "\n"
    
    printf "|"
    for i in "${!headers[@]}"; do
        printf " %-*s |" "${col_widths[$i]}" "${headers[$i]}"
    done
    printf "\n"
    
    printf "+"
    for width in "${col_widths[@]}"; do
        printf "%*s+" $((width + 2)) "" | tr ' ' '-'
    done
    printf "\n"
    
    # Print data
    for row in "${data[@]}"; do
        IFS='|' read -ra fields <<< "$row"
        printf "|"
        for i in "${!fields[@]}"; do
            printf " %-*s |" "${col_widths[$i]}" "${fields[$i]}"
        done
        printf "\n"
    done
    
    printf "+"
    for width in "${col_widths[@]}"; do
        printf "%*s+" $((width + 2)) "" | tr ' ' '-'
    done
    printf "\n"
}

# Progress bar function
show_progress() {
    local current="$1"
    local total="$2"
    local width="${3:-50}"
    local prefix="${4:-Progress:}"
    
    # Calculate percentage
    local percent=$((current * 100 / total))
    local filled=$((current * width / total))
    local empty=$((width - filled))
    
    # Build progress bar
    local bar=""
    for ((i=0; i<filled; i++)); do
        bar+="█"
    done
    for ((i=0; i<empty; i++)); do
        bar+="░"
    done
    
    # Print progress bar
    printf "\r$prefix [%s] %d%% (%d/%d)" "$bar" "$percent" "$current" "$total"
    
    # New line when complete
    if [[ $current -eq $total ]]; then
        printf "\n"
    fi
}
```

This comprehensive Bash scripting fundamentals guide provides the essential building blocks for creating robust, maintainable shell scripts for DevOps automation and system administration tasks.