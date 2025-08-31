# Bash Security Best Practices

## Overview
Bash security best practices cover comprehensive techniques for writing secure shell scripts that protect against common vulnerabilities, implement proper access controls, handle sensitive data securely, and follow defense-in-depth principles for production environments.

## Input Validation and Sanitization

### 1. Secure Input Handling
```bash
#!/bin/bash

# Input validation framework
readonly VALID_EMAIL_REGEX='^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
readonly VALID_HOSTNAME_REGEX='^[a-zA-Z0-9][a-zA-Z0-9.-]*[a-zA-Z0-9]$'
readonly VALID_IP_REGEX='^([0-9]{1,3}\.){3}[0-9]{1,3}$'
readonly VALID_PORT_REGEX='^[0-9]+$'
readonly VALID_USERNAME_REGEX='^[a-zA-Z0-9_][a-zA-Z0-9._-]{2,31}$'

# Secure input validation
validate_input() {
    local input="$1"
    local validation_type="$2"
    local max_length="${3:-256}"
    local allow_empty="${4:-false}"
    
    # Check for empty input
    if [[ -z "$input" ]]; then
        if [[ "$allow_empty" == "true" ]]; then
            return 0
        else
            log_error "Input validation failed: empty input not allowed"
            return 1
        fi
    fi
    
    # Check input length
    if [[ ${#input} -gt $max_length ]]; then
        log_error "Input validation failed: input too long (${#input} > $max_length)"
        return 1
    fi
    
    # Check for null bytes and control characters
    if [[ "$input" =~ $'\0' ]]; then
        log_error "Input validation failed: null byte detected"
        return 1
    fi
    
    if [[ "$input" =~ [[:cntrl:]] ]]; then
        log_error "Input validation failed: control characters detected"
        return 1
    fi
    
    # Type-specific validation
    case "$validation_type" in
        email)
            if [[ ! "$input" =~ $VALID_EMAIL_REGEX ]]; then
                log_error "Input validation failed: invalid email format"
                return 1
            fi
            ;;
        hostname)
            if [[ ! "$input" =~ $VALID_HOSTNAME_REGEX ]]; then
                log_error "Input validation failed: invalid hostname format"
                return 1
            fi
            if [[ ${#input} -gt 253 ]]; then
                log_error "Input validation failed: hostname too long"
                return 1
            fi
            ;;
        ip)
            if [[ ! "$input" =~ $VALID_IP_REGEX ]]; then
                log_error "Input validation failed: invalid IP address format"
                return 1
            fi
            # Validate IP octets
            IFS='.' read -ra octets <<< "$input"
            for octet in "${octets[@]}"; do
                if [[ $octet -gt 255 ]]; then
                    log_error "Input validation failed: invalid IP octet value: $octet"
                    return 1
                fi
            done
            ;;
        port)
            if [[ ! "$input" =~ $VALID_PORT_REGEX ]]; then
                log_error "Input validation failed: invalid port format"
                return 1
            fi
            if [[ $input -lt 1 || $input -gt 65535 ]]; then
                log_error "Input validation failed: port out of range (1-65535)"
                return 1
            fi
            ;;
        username)
            if [[ ! "$input" =~ $VALID_USERNAME_REGEX ]]; then
                log_error "Input validation failed: invalid username format"
                return 1
            fi
            ;;
        alphanumeric)
            if [[ ! "$input" =~ ^[a-zA-Z0-9]+$ ]]; then
                log_error "Input validation failed: non-alphanumeric characters detected"
                return 1
            fi
            ;;
        filename)
            # Secure filename validation
            if [[ "$input" =~ [/\\:*?"<>|] ]]; then
                log_error "Input validation failed: invalid filename characters"
                return 1
            fi
            if [[ "$input" =~ ^\. || "$input" =~ \.\. ]]; then
                log_error "Input validation failed: invalid filename (starts with dot or contains ..)"
                return 1
            fi
            ;;
        path)
            # Prevent directory traversal
            if [[ "$input" =~ \.\./|/\.\. ]]; then
                log_error "Input validation failed: directory traversal attempt detected"
                return 1
            fi
            if [[ "$input" =~ ^/ ]]; then
                log_error "Input validation failed: absolute path not allowed"
                return 1
            fi
            ;;
        *)
            log_error "Input validation failed: unknown validation type: $validation_type"
            return 1
            ;;
    esac
    
    return 0
}

# Sanitize input for safe use
sanitize_input() {
    local input="$1"
    local sanitization_type="$2"
    
    case "$sanitization_type" in
        shell)
            # Remove shell metacharacters
            echo "$input" | tr -d '`$(){}[]|&;<>*?~'
            ;;
        sql)
            # Basic SQL injection prevention (escape single quotes)
            echo "${input//\'/\'\'}"
            ;;
        html)
            # HTML entity encoding
            echo "$input" | sed 's/&/\&amp;/g; s/</\&lt;/g; s/>/\&gt;/g; s/"/\&quot;/g; s/'"'"'/\&#39;/g'
            ;;
        filename)
            # Safe filename sanitization
            echo "$input" | tr -d '/<>:"|?*\' | tr ' ' '_'
            ;;
        *)
            # Default: remove non-printable characters
            echo "$input" | tr -cd '[:print:]'
            ;;
    esac
}

# Secure command line argument processing
process_arguments_securely() {
    local -A validated_args
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --config=*)
                local config_file="${1#*=}"
                if validate_input "$config_file" "filename" 255; then
                    validated_args[config_file]="$config_file"
                else
                    log_error "Invalid configuration file argument"
                    exit 1
                fi
                ;;
            --user=*)
                local username="${1#*=}"
                if validate_input "$username" "username" 32; then
                    validated_args[username]="$username"
                else
                    log_error "Invalid username argument"
                    exit 1
                fi
                ;;
            --host=*)
                local hostname="${1#*=}"
                if validate_input "$hostname" "hostname" 253; then
                    validated_args[hostname]="$hostname"
                else
                    log_error "Invalid hostname argument"
                    exit 1
                fi
                ;;
            --port=*)
                local port="${1#*=}"
                if validate_input "$port" "port" 5; then
                    validated_args[port]="$port"
                else
                    log_error "Invalid port argument"
                    exit 1
                fi
                ;;
            -*)
                log_error "Unknown option: $1"
                exit 1
                ;;
            *)
                log_error "Unexpected argument: $1"
                exit 1
                ;;
        esac
        shift
    done
    
    # Export validated arguments
    for key in "${!validated_args[@]}"; do
        declare -g "VALIDATED_${key^^}=${validated_args[$key]}"
        log_debug "Validated argument: $key = ${validated_args[$key]}"
    done
}

# Secure environment variable handling
validate_environment() {
    local required_vars=("$@")
    local validation_failed=false
    
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var:-}" ]]; then
            log_error "Required environment variable not set: $var"
            validation_failed=true
            continue
        fi
        
        # Check for suspicious content
        local value="${!var}"
        if [[ "$value" =~ \$\( || "$value" =~ \`.*\` || "$value" =~ \$\{.*\} ]]; then
            log_error "Suspicious content detected in environment variable $var"
            validation_failed=true
        fi
        
        # Length check
        if [[ ${#value} -gt 4096 ]]; then
            log_error "Environment variable $var is too long (${#value} > 4096)"
            validation_failed=true
        fi
    done
    
    if [[ "$validation_failed" == "true" ]]; then
        exit 1
    fi
}
```

### 2. Command Injection Prevention
```bash
#!/bin/bash

# Safe command execution framework
execute_command_safely() {
    local command_name="$1"
    shift
    local args=("$@")
    
    # Validate command name
    if [[ ! "$command_name" =~ ^[a-zA-Z0-9_/-]+$ ]]; then
        log_error "Invalid command name: $command_name"
        return 1
    fi
    
    # Check if command exists
    if ! command -v "$command_name" >/dev/null 2>&1; then
        log_error "Command not found: $command_name"
        return 1
    fi
    
    # Validate arguments
    local validated_args=()
    for arg in "${args[@]}"; do
        # Check for shell metacharacters
        if [[ "$arg" =~ [;\&\|\`\$\(\)\{\}\[\]\<\>\*\?\~] ]]; then
            log_error "Unsafe characters detected in argument: $arg"
            return 1
        fi
        validated_args+=("$arg")
    done
    
    log_info "Executing: $command_name ${validated_args[*]}"
    
    # Execute with explicit argument array (prevents shell interpretation)
    "$command_name" "${validated_args[@]}"
}

# Whitelist-based command execution
declare -A ALLOWED_COMMANDS=(
    [ls]="ls"
    [cat]="cat"
    [grep]="grep"
    [awk]="awk"
    [sed]="sed"
    [find]="find"
    [sort]="sort"
    [uniq]="uniq"
    [wc]="wc"
    [head]="head"
    [tail]="tail"
    [curl]="curl"
    [wget]="wget"
    [docker]="docker"
    [kubectl]="kubectl"
)

execute_whitelisted_command() {
    local command_name="$1"
    shift
    local args=("$@")
    
    # Check if command is whitelisted
    if [[ -z "${ALLOWED_COMMANDS[$command_name]:-}" ]]; then
        log_error "Command not in whitelist: $command_name"
        return 1
    fi
    
    execute_command_safely "$command_name" "${args[@]}"
}

# Safe file operations
safe_read_file() {
    local file_path="$1"
    local max_size="${2:-1048576}"  # 1MB default
    
    # Validate file path
    if ! validate_input "$file_path" "path" 4096; then
        return 1
    fi
    
    # Resolve to absolute path to prevent traversal
    local abs_path
    abs_path=$(realpath "$file_path" 2>/dev/null) || {
        log_error "Cannot resolve file path: $file_path"
        return 1
    }
    
    # Check if file exists and is readable
    if [[ ! -f "$abs_path" ]]; then
        log_error "File not found: $abs_path"
        return 1
    fi
    
    if [[ ! -r "$abs_path" ]]; then
        log_error "File not readable: $abs_path"
        return 1
    fi
    
    # Check file size
    local file_size
    file_size=$(stat -f%z "$abs_path" 2>/dev/null || stat -c%s "$abs_path" 2>/dev/null || echo "0")
    
    if [[ $file_size -gt $max_size ]]; then
        log_error "File too large: $abs_path ($file_size > $max_size bytes)"
        return 1
    fi
    
    # Safe read with timeout
    timeout 30s cat "$abs_path"
}

# Safe file writing
safe_write_file() {
    local file_path="$1"
    local content="$2"
    local mode="${3:-644}"
    local max_size="${4:-1048576}"  # 1MB default
    
    # Validate file path
    if ! validate_input "$file_path" "path" 4096; then
        return 1
    fi
    
    # Check content size
    if [[ ${#content} -gt $max_size ]]; then
        log_error "Content too large: ${#content} > $max_size bytes"
        return 1
    fi
    
    # Create temporary file securely
    local temp_file
    temp_file=$(mktemp) || {
        log_error "Cannot create temporary file"
        return 1
    }
    
    # Set secure permissions on temp file
    chmod 600 "$temp_file"
    
    # Write content to temp file
    if ! echo "$content" > "$temp_file"; then
        log_error "Failed to write to temporary file: $temp_file"
        rm -f "$temp_file"
        return 1
    fi
    
    # Atomic move to final location
    if ! mv "$temp_file" "$file_path"; then
        log_error "Failed to move file to final location: $file_path"
        rm -f "$temp_file"
        return 1
    fi
    
    # Set final permissions
    chmod "$mode" "$file_path"
    
    log_info "File written securely: $file_path"
}

# Prevent shell expansion attacks
quote_safely() {
    local input="$1"
    printf '%q' "$input"
}

# Execute SQL safely (parameterized queries)
execute_sql_safely() {
    local query_template="$1"
    shift
    local parameters=("$@")
    
    # Simple parameter substitution (use proper DB libraries in production)
    local query="$query_template"
    local param_index=1
    
    for param in "${parameters[@]}"; do
        # Sanitize parameter
        local safe_param
        safe_param=$(sanitize_input "$param" "sql")
        
        # Replace placeholder
        query="${query//\$$param_index/\'$safe_param\'}"
        ((param_index++))
    done
    
    log_debug "Executing SQL: $query"
    
    # Execute through safe command
    execute_command_safely "mysql" "-e" "$query"
}
```

## Secret Management and Credential Security

### 1. Secure Secret Handling
```bash
#!/bin/bash

# Secure secret management
readonly SECRETS_DIR="${SECRETS_DIR:-/var/secrets}"
readonly SECRET_FILE_MODE="600"
readonly SECRET_DIR_MODE="700"

# Initialize secure secrets directory
init_secrets_dir() {
    if [[ ! -d "$SECRETS_DIR" ]]; then
        if ! mkdir -p "$SECRETS_DIR"; then
            log_error "Cannot create secrets directory: $SECRETS_DIR"
            return 1
        fi
        chmod "$SECRET_DIR_MODE" "$SECRETS_DIR"
        log_info "Created secure secrets directory: $SECRETS_DIR"
    fi
    
    # Verify permissions
    local current_perms
    current_perms=$(stat -c%a "$SECRETS_DIR" 2>/dev/null || stat -f%A "$SECRETS_DIR" 2>/dev/null)
    
    if [[ "$current_perms" != "$SECRET_DIR_MODE" ]]; then
        log_warn "Fixing secrets directory permissions: $SECRETS_DIR"
        chmod "$SECRET_DIR_MODE" "$SECRETS_DIR"
    fi
}

# Store secret securely
store_secret() {
    local secret_name="$1"
    local secret_value="$2"
    local expiry_hours="${3:-24}"
    
    # Validate secret name
    if ! validate_input "$secret_name" "alphanumeric" 64; then
        log_error "Invalid secret name: $secret_name"
        return 1
    fi
    
    init_secrets_dir || return 1
    
    local secret_file="$SECRETS_DIR/$secret_name"
    local expiry_time=$(($(date +%s) + expiry_hours * 3600))
    
    # Create secret file with metadata
    {
        echo "EXPIRY=$expiry_time"
        echo "CREATED=$(date -Iseconds)"
        echo "VALUE=$secret_value"
    } > "$secret_file"
    
    # Set secure permissions
    chmod "$SECRET_FILE_MODE" "$secret_file"
    
    log_info "Secret stored: $secret_name (expires in ${expiry_hours}h)"
}

# Retrieve secret securely
get_secret() {
    local secret_name="$1"
    local secret_file="$SECRETS_DIR/$secret_name"
    
    # Validate secret name
    if ! validate_input "$secret_name" "alphanumeric" 64; then
        log_error "Invalid secret name: $secret_name"
        return 1
    fi
    
    if [[ ! -f "$secret_file" ]]; then
        log_error "Secret not found: $secret_name"
        return 1
    fi
    
    # Check permissions
    local current_perms
    current_perms=$(stat -c%a "$secret_file" 2>/dev/null || stat -f%A "$secret_file" 2>/dev/null)
    
    if [[ "$current_perms" != "$SECRET_FILE_MODE" ]]; then
        log_error "Insecure permissions on secret file: $secret_file"
        return 1
    fi
    
    # Read and validate secret
    local expiry value created
    while IFS='=' read -r key val; do
        case "$key" in
            EXPIRY) expiry="$val" ;;
            VALUE) value="$val" ;;
            CREATED) created="$val" ;;
        esac
    done < "$secret_file"
    
    # Check expiry
    if [[ -n "$expiry" && "$expiry" -lt $(date +%s) ]]; then
        log_error "Secret expired: $secret_name"
        rm -f "$secret_file"  # Clean up expired secret
        return 1
    fi
    
    # Return value without logging it
    echo "$value"
}

# Clean expired secrets
cleanup_expired_secrets() {
    local current_time
    current_time=$(date +%s)
    
    if [[ ! -d "$SECRETS_DIR" ]]; then
        return 0
    fi
    
    local cleaned_count=0
    
    for secret_file in "$SECRETS_DIR"/*; do
        [[ -f "$secret_file" ]] || continue
        
        local expiry
        expiry=$(grep '^EXPIRY=' "$secret_file" 2>/dev/null | cut -d'=' -f2)
        
        if [[ -n "$expiry" && "$expiry" -lt "$current_time" ]]; then
            local secret_name
            secret_name=$(basename "$secret_file")
            log_info "Removing expired secret: $secret_name"
            rm -f "$secret_file"
            ((cleaned_count++))
        fi
    done
    
    log_info "Cleaned up $cleaned_count expired secrets"
}

# Secure password generation
generate_password() {
    local length="${1:-32}"
    local include_symbols="${2:-true}"
    
    local charset="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    
    if [[ "$include_symbols" == "true" ]]; then
        charset="${charset}!@#$%^&*()_+-=[]{}|;:,.<>?"
    fi
    
    # Generate password using /dev/urandom
    if [[ -r /dev/urandom ]]; then
        tr -dc "$charset" < /dev/urandom | head -c "$length"
        echo
    else
        log_error "/dev/urandom not available for secure password generation"
        return 1
    fi
}

# Mask secrets in logs
mask_secrets() {
    local text="$1"
    local -a secret_patterns=(
        's/password=[^[:space:]]*/password=***MASKED***/gi'
        's/token=[^[:space:]]*/token=***MASKED***/gi'
        's/key=[^[:space:]]*/key=***MASKED***/gi'
        's/secret=[^[:space:]]*/secret=***MASKED***/gi'
        's/api_key=[^[:space:]]*/api_key=***MASKED***/gi'
        's/"password"[[:space:]]*:[[:space:]]*"[^"]*"/"password": "***MASKED***"/gi'
        's/"token"[[:space:]]*:[[:space:]]*"[^"]*"/"token": "***MASKED***"/gi'
    )
    
    local masked_text="$text"
    for pattern in "${secret_patterns[@]}"; do
        masked_text=$(echo "$masked_text" | sed -E "$pattern")
    done
    
    echo "$masked_text"
}

# Secure environment variable handling
secure_env_var() {
    local var_name="$1"
    local var_value="$2"
    local mask_in_ps="${3:-true}"
    
    # Set the variable
    export "$var_name"="$var_value"
    
    # If masking is enabled, set up process substitution to hide from ps
    if [[ "$mask_in_ps" == "true" ]]; then
        # This technique helps hide sensitive env vars from process lists
        exec {fd}< <(echo "$var_value")
        export "$var_name"="$(cat <&$fd)"
        exec {fd}<&-
    fi
}

# AWS credentials security
setup_aws_credentials() {
    local access_key="$1"
    local secret_key="$2"
    local region="${3:-us-east-1}"
    
    # Validate AWS credentials format
    if [[ ! "$access_key" =~ ^AKIA[0-9A-Z]{16}$ ]]; then
        log_error "Invalid AWS access key format"
        return 1
    fi
    
    if [[ ${#secret_key} -ne 40 ]]; then
        log_error "Invalid AWS secret key length"
        return 1
    fi
    
    # Store credentials securely
    store_secret "aws_access_key" "$access_key" 8
    store_secret "aws_secret_key" "$secret_key" 8
    
    # Set up AWS CLI configuration
    local aws_config_dir="$HOME/.aws"
    mkdir -p "$aws_config_dir"
    chmod 700 "$aws_config_dir"
    
    # Create credentials file
    cat > "$aws_config_dir/credentials" << EOF
[default]
aws_access_key_id = $access_key
aws_secret_access_key = $secret_key
EOF
    
    chmod 600 "$aws_config_dir/credentials"
    
    # Create config file
    cat > "$aws_config_dir/config" << EOF
[default]
region = $region
output = json
EOF
    
    chmod 600 "$aws_config_dir/config"
    
    log_info "AWS credentials configured securely"
}
```

### 2. Access Control and Permissions
```bash
#!/bin/bash

# Privilege escalation protection
check_running_as_root() {
    if [[ $EUID -eq 0 ]]; then
        log_error "This script should not be run as root for security reasons"
        exit 1
    fi
}

# Require specific user
require_user() {
    local required_user="$1"
    local current_user
    current_user=$(id -un)
    
    if [[ "$current_user" != "$required_user" ]]; then
        log_error "This script must be run as user: $required_user (current: $current_user)"
        exit 1
    fi
}

# Check group membership
check_group_membership() {
    local required_group="$1"
    local current_user
    current_user=$(id -un)
    
    if ! groups "$current_user" | grep -q "\b$required_group\b"; then
        log_error "User $current_user is not a member of required group: $required_group"
        exit 1
    fi
}

# Secure file permissions checker
check_file_permissions() {
    local file_path="$1"
    local expected_perms="$2"
    local expected_owner="${3:-}"
    local expected_group="${4:-}"
    
    if [[ ! -e "$file_path" ]]; then
        log_error "File does not exist: $file_path"
        return 1
    fi
    
    # Check permissions
    local current_perms
    current_perms=$(stat -c%a "$file_path" 2>/dev/null || stat -f%A "$file_path" 2>/dev/null)
    
    if [[ "$current_perms" != "$expected_perms" ]]; then
        log_error "Incorrect permissions on $file_path: $current_perms (expected: $expected_perms)"
        return 1
    fi
    
    # Check owner
    if [[ -n "$expected_owner" ]]; then
        local current_owner
        current_owner=$(stat -c%U "$file_path" 2>/dev/null || stat -f%Su "$file_path" 2>/dev/null)
        
        if [[ "$current_owner" != "$expected_owner" ]]; then
            log_error "Incorrect owner on $file_path: $current_owner (expected: $expected_owner)"
            return 1
        fi
    fi
    
    # Check group
    if [[ -n "$expected_group" ]]; then
        local current_group
        current_group=$(stat -c%G "$file_path" 2>/dev/null || stat -f%Sg "$file_path" 2>/dev/null)
        
        if [[ "$current_group" != "$expected_group" ]]; then
            log_error "Incorrect group on $file_path: $current_group (expected: $expected_group)"
            return 1
        fi
    fi
    
    return 0
}

# Set secure permissions recursively
set_secure_permissions() {
    local target_path="$1"
    local dir_perms="${2:-755}"
    local file_perms="${3:-644}"
    local owner="${4:-}"
    local group="${5:-}"
    
    if [[ ! -e "$target_path" ]]; then
        log_error "Target does not exist: $target_path"
        return 1
    fi
    
    # Set ownership if specified
    if [[ -n "$owner" || -n "$group" ]]; then
        local ownership="${owner:-}${group:+:$group}"
        if ! chown -R "$ownership" "$target_path"; then
            log_error "Failed to set ownership on $target_path"
            return 1
        fi
    fi
    
    # Set directory permissions
    if [[ -d "$target_path" ]]; then
        find "$target_path" -type d -exec chmod "$dir_perms" {} \;
        find "$target_path" -type f -exec chmod "$file_perms" {} \;
    else
        chmod "$file_perms" "$target_path"
    fi
    
    log_info "Set secure permissions on: $target_path"
}

# Create secure temporary directory
create_secure_temp_dir() {
    local prefix="${1:-secure_temp}"
    local temp_dir
    
    # Create temporary directory with secure permissions
    temp_dir=$(mktemp -d -t "${prefix}.XXXXXXXX") || {
        log_error "Failed to create secure temporary directory"
        return 1
    }
    
    # Set restrictive permissions
    chmod 700 "$temp_dir"
    
    # Register for cleanup
    TEMP_DIRS="${TEMP_DIRS:-} $temp_dir"
    
    echo "$temp_dir"
}

# Umask enforcement
enforce_secure_umask() {
    local required_umask="${1:-022}"
    local current_umask
    current_umask=$(umask)
    
    if [[ "$current_umask" != "$required_umask" ]]; then
        log_info "Setting secure umask: $required_umask (was: $current_umask)"
        umask "$required_umask"
    fi
}

# File integrity checking
calculate_file_hash() {
    local file_path="$1"
    local algorithm="${2:-sha256}"
    
    if [[ ! -f "$file_path" ]]; then
        log_error "File not found for hashing: $file_path"
        return 1
    fi
    
    case "$algorithm" in
        md5)
            md5sum "$file_path" | cut -d' ' -f1
            ;;
        sha1)
            sha1sum "$file_path" | cut -d' ' -f1
            ;;
        sha256)
            sha256sum "$file_path" | cut -d' ' -f1
            ;;
        *)
            log_error "Unsupported hash algorithm: $algorithm"
            return 1
            ;;
    esac
}

# Verify file integrity
verify_file_integrity() {
    local file_path="$1"
    local expected_hash="$2"
    local algorithm="${3:-sha256}"
    
    local actual_hash
    actual_hash=$(calculate_file_hash "$file_path" "$algorithm") || return 1
    
    if [[ "$actual_hash" == "$expected_hash" ]]; then
        log_info "File integrity verified: $file_path"
        return 0
    else
        log_error "File integrity verification failed: $file_path"
        log_error "Expected: $expected_hash"
        log_error "Actual:   $actual_hash"
        return 1
    fi
}
```

### 3. Network Security and Communication
```bash
#!/bin/bash

# Secure HTTP requests
secure_http_request() {
    local method="$1"
    local url="$2"
    local timeout="${3:-30}"
    local max_redirects="${4:-3}"
    local verify_ssl="${5:-true}"
    
    # Validate URL
    if [[ ! "$url" =~ ^https?://[a-zA-Z0-9.-]+[a-zA-Z0-9](:[0-9]{1,5})?(/.*)?$ ]]; then
        log_error "Invalid URL format: $url"
        return 1
    fi
    
    # Build curl options
    local curl_options=(
        --max-time "$timeout"
        --max-redirs "$max_redirects"
        --user-agent "SecureScript/1.0"
        --location
        --silent
        --show-error
        --fail
    )
    
    # SSL verification
    if [[ "$verify_ssl" == "true" ]]; then
        curl_options+=(--cacert /etc/ssl/certs/ca-certificates.crt)
    else
        curl_options+=(--insecure)
        log_warn "SSL verification disabled for: $url"
    fi
    
    # Method-specific options
    case "$method" in
        GET)
            curl_options+=(--request GET)
            ;;
        POST)
            curl_options+=(--request POST)
            ;;
        PUT)
            curl_options+=(--request PUT)
            ;;
        DELETE)
            curl_options+=(--request DELETE)
            ;;
        *)
            log_error "Unsupported HTTP method: $method"
            return 1
            ;;
    esac
    
    # Execute request
    log_debug "Making $method request to: $url"
    curl "${curl_options[@]}" "$url"
}

# Secure SSH connection
secure_ssh_connect() {
    local host="$1"
    local user="$2"
    local port="${3:-22}"
    local key_file="${4:-}"
    local command="${5:-}"
    
    # Validate inputs
    validate_input "$host" "hostname" 253 || return 1
    validate_input "$user" "username" 32 || return 1
    validate_input "$port" "port" 5 || return 1
    
    # Build SSH options
    local ssh_options=(
        -o "StrictHostKeyChecking=yes"
        -o "UserKnownHostsFile=$HOME/.ssh/known_hosts"
        -o "Protocol=2"
        -o "Compression=yes"
        -o "ConnectTimeout=30"
        -o "ServerAliveInterval=60"
        -o "ServerAliveCountMax=3"
        -p "$port"
    )
    
    # Add key file if specified
    if [[ -n "$key_file" ]]; then
        if [[ ! -f "$key_file" ]]; then
            log_error "SSH key file not found: $key_file"
            return 1
        fi
        
        # Check key file permissions
        if ! check_file_permissions "$key_file" "600"; then
            log_error "SSH key file has insecure permissions: $key_file"
            return 1
        fi
        
        ssh_options+=(-i "$key_file")
    fi
    
    # Execute SSH command
    if [[ -n "$command" ]]; then
        log_debug "Executing SSH command on $host: $command"
        ssh "${ssh_options[@]}" "$user@$host" "$command"
    else
        log_debug "Opening SSH connection to: $user@$host:$port"
        ssh "${ssh_options[@]}" "$user@$host"
    fi
}

# Secure file transfer
secure_file_transfer() {
    local operation="$1"  # upload or download
    local local_file="$2"
    local remote_host="$3"
    local remote_user="$4"
    local remote_file="$5"
    local key_file="${6:-}"
    
    # Validate inputs
    validate_input "$remote_host" "hostname" 253 || return 1
    validate_input "$remote_user" "username" 32 || return 1
    
    # Build SCP options
    local scp_options=(
        -o "StrictHostKeyChecking=yes"
        -o "UserKnownHostsFile=$HOME/.ssh/known_hosts"
        -o "Protocol=2"
        -C  # Compression
        -p  # Preserve timestamps and permissions
    )
    
    # Add key file if specified
    if [[ -n "$key_file" ]]; then
        if ! check_file_permissions "$key_file" "600"; then
            log_error "SSH key file has insecure permissions: $key_file"
            return 1
        fi
        scp_options+=(-i "$key_file")
    fi
    
    # Execute transfer
    case "$operation" in
        upload)
            if [[ ! -f "$local_file" ]]; then
                log_error "Local file not found: $local_file"
                return 1
            fi
            log_info "Uploading $local_file to $remote_host:$remote_file"
            scp "${scp_options[@]}" "$local_file" "$remote_user@$remote_host:$remote_file"
            ;;
        download)
            log_info "Downloading $remote_host:$remote_file to $local_file"
            scp "${scp_options[@]}" "$remote_user@$remote_host:$remote_file" "$local_file"
            ;;
        *)
            log_error "Invalid operation: $operation (use 'upload' or 'download')"
            return 1
            ;;
    esac
}

# TLS certificate validation
validate_tls_certificate() {
    local hostname="$1"
    local port="${2:-443}"
    local ca_file="${3:-/etc/ssl/certs/ca-certificates.crt}"
    
    validate_input "$hostname" "hostname" 253 || return 1
    validate_input "$port" "port" 5 || return 1
    
    # Check certificate
    local cert_info
    cert_info=$(echo | openssl s_client -servername "$hostname" -connect "$hostname:$port" -CAfile "$ca_file" 2>/dev/null | openssl x509 -noout -text 2>/dev/null)
    
    if [[ -z "$cert_info" ]]; then
        log_error "Failed to retrieve certificate from $hostname:$port"
        return 1
    fi
    
    # Check certificate expiry
    local expiry_date
    expiry_date=$(echo | openssl s_client -servername "$hostname" -connect "$hostname:$port" 2>/dev/null | openssl x509 -noout -enddate 2>/dev/null | cut -d'=' -f2)
    
    if [[ -n "$expiry_date" ]]; then
        local expiry_epoch
        expiry_epoch=$(date -d "$expiry_date" +%s 2>/dev/null)
        local current_epoch
        current_epoch=$(date +%s)
        
        if [[ $expiry_epoch -lt $current_epoch ]]; then
            log_error "Certificate expired for $hostname"
            return 1
        elif [[ $expiry_epoch -lt $((current_epoch + 2592000)) ]]; then  # 30 days
            log_warn "Certificate expires soon for $hostname: $expiry_date"
        fi
    fi
    
    log_info "TLS certificate validation passed for: $hostname"
    return 0
}
```

This comprehensive security framework provides robust protection against common vulnerabilities, implements proper access controls, handles secrets securely, and follows security best practices for production Bash scripts in DevOps environments.