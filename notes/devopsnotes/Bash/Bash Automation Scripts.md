## Production Bash Automation Scripts

### Deployment Script Template
```bash
#!/bin/bash
set -euo pipefail

# Production deployment script template
# Usage: ./deploy.sh <environment> <service> [--dry-run]

# Configuration
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly LOG_FILE="/var/log/deployment.log"
readonly LOCK_FILE="/tmp/deploy.lock"
readonly TIMEOUT=1800  # 30 minutes

# Color codes for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m' # No Color

# Logging functions
log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${timestamp} [${level}] ${message}" | tee -a "${LOG_FILE}"
}

log_info() { log "${BLUE}INFO${NC}" "$@"; }
log_warn() { log "${YELLOW}WARN${NC}" "$@"; }
log_error() { log "${RED}ERROR${NC}" "$@"; }
log_success() { log "${GREEN}SUCCESS${NC}" "$@"; }

# Error handling
error_exit() {
    log_error "$1"
    cleanup
    exit 1
}

cleanup() {
    log_info "Cleaning up..."
    [[ -f "${LOCK_FILE}" ]] && rm -f "${LOCK_FILE}"
    # Additional cleanup tasks
}

# Trap for cleanup on exit
trap cleanup EXIT
trap 'error_exit "Script interrupted"' INT TERM

# Lock mechanism to prevent concurrent deployments
acquire_lock() {
    if [[ -f "${LOCK_FILE}" ]]; then
        local lock_pid=$(cat "${LOCK_FILE}")
        if kill -0 "$lock_pid" 2>/dev/null; then
            error_exit "Another deployment is already running (PID: ${lock_pid})"
        else
            log_warn "Stale lock file found, removing..."
            rm -f "${LOCK_FILE}"
        fi
    fi
    echo $$ > "${LOCK_FILE}"
    log_info "Acquired deployment lock"
}

# Validation functions
validate_environment() {
    local env="$1"
    case "$env" in
        dev|staging|prod)
            return 0
            ;;
        *)
            error_exit "Invalid environment: $env. Must be dev, staging, or prod"
            ;;
    esac
}

validate_service() {
    local service="$1"
    local config_file="${SCRIPT_DIR}/configs/${service}.conf"
    
    if [[ ! -f "$config_file" ]]; then
        error_exit "Service configuration not found: $config_file"
    fi
    
    # Source service configuration
    source "$config_file"
    
    # Validate required variables
    local required_vars=("SERVICE_NAME" "DOCKER_IMAGE" "HEALTH_CHECK_URL")
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var:-}" ]]; then
            error_exit "Required variable $var not defined in $config_file"
        fi
    done
}

# Pre-deployment checks
pre_deployment_checks() {
    local environment="$1"
    local service="$2"
    
    log_info "Running pre-deployment checks..."
    
    # Check disk space
    local available_space=$(df / | tail -1 | awk '{print $4}')
    if [[ $available_space -lt 1048576 ]]; then  # Less than 1GB
        error_exit "Insufficient disk space: ${available_space}KB available"
    fi
    
    # Check memory
    local available_memory=$(free | grep MemAvailable | awk '{print $2}')
    if [[ $available_memory -lt 524288 ]]; then  # Less than 512MB
        error_exit "Insufficient memory: ${available_memory}KB available"
    fi
    
    # Check if service is already running
    if systemctl is-active --quiet "${service}"; then
        log_info "Service $service is currently running"
    else
        log_warn "Service $service is not running"
    fi
    
    # Validate configuration files
    if [[ "$environment" == "prod" ]]; then
        log_info "Production environment - running additional validations..."
        validate_production_config "$service"
    fi
    
    log_success "Pre-deployment checks passed"
}

validate_production_config() {
    local service="$1"
    
    # Check SSL certificates
    local cert_file="/etc/ssl/certs/${service}.crt"
    if [[ -f "$cert_file" ]]; then
        local cert_expiry=$(openssl x509 -enddate -noout -in "$cert_file" | cut -d= -f2)
        local expiry_timestamp=$(date -d "$cert_expiry" +%s)
        local current_timestamp=$(date +%s)
        local days_until_expiry=$(( (expiry_timestamp - current_timestamp) / 86400 ))
        
        if [[ $days_until_expiry -lt 30 ]]; then
            log_warn "SSL certificate expires in $days_until_expiry days"
        fi
    fi
    
    # Check database connectivity
    if command -v mysql >/dev/null 2>&1; then
        if ! mysql -h "${DB_HOST}" -u "${DB_USER}" -p"${DB_PASSWORD}" -e "SELECT 1" >/dev/null 2>&1; then
            error_exit "Database connectivity check failed"
        fi
    fi
}

# Backup current version
backup_current_version() {
    local service="$1"
    local backup_dir="/opt/backups/${service}"
    local timestamp=$(date '+%Y%m%d_%H%M%S')
    
    log_info "Creating backup of current version..."
    
    mkdir -p "$backup_dir"
    
    # Backup application files
    if [[ -d "/opt/${service}" ]]; then
        tar -czf "${backup_dir}/${service}_${timestamp}.tar.gz" -C "/opt" "${service}"
        log_info "Application backup created: ${backup_dir}/${service}_${timestamp}.tar.gz"
    fi
    
    # Backup configuration
    if [[ -d "/etc/${service}" ]]; then
        cp -r "/etc/${service}" "${backup_dir}/config_${timestamp}"
        log_info "Configuration backup created: ${backup_dir}/config_${timestamp}"
    fi
    
    # Keep only last 5 backups
    find "$backup_dir" -name "${service}_*.tar.gz" | sort -r | tail -n +6 | xargs -r rm
    find "$backup_dir" -name "config_*" -type d | sort -r | tail -n +6 | xargs -r rm -rf
}

# Deploy application
deploy_application() {
    local environment="$1"
    local service="$2"
    local dry_run="$3"
    
    log_info "Starting deployment of $service to $environment..."
    
    if [[ "$dry_run" == "true" ]]; then
        log_info "DRY RUN MODE - No actual changes will be made"
        return 0
    fi
    
    # Pull latest Docker image
    log_info "Pulling Docker image: ${DOCKER_IMAGE}"
    if ! docker pull "${DOCKER_IMAGE}"; then
        error_exit "Failed to pull Docker image: ${DOCKER_IMAGE}"
    fi
    
    # Stop current service
    log_info "Stopping current service..."
    systemctl stop "$service" || log_warn "Service was not running"
    
    # Deploy new version
    log_info "Deploying new version..."
    
    # Update Docker container
    docker stop "${service}" 2>/dev/null || true
    docker rm "${service}" 2>/dev/null || true
    
    docker run -d \
        --name "$service" \
        --restart unless-stopped \
        -p "${SERVICE_PORT}:${SERVICE_PORT}" \
        -v "/etc/${service}:/app/config:ro" \
        -v "/var/log/${service}:/app/logs" \
        --env-file "/etc/${service}/.env" \
        "${DOCKER_IMAGE}"
    
    # Start service
    log_info "Starting service..."
    systemctl start "$service"
    
    # Wait for service to be ready
    wait_for_service_ready "$service"
    
    log_success "Deployment completed successfully"
}

# Wait for service to be ready
wait_for_service_ready() {
    local service="$1"
    local max_attempts=30
    local attempt=1
    
    log_info "Waiting for service to be ready..."
    
    while [[ $attempt -le $max_attempts ]]; do
        if health_check "$service"; then
            log_success "Service is ready after $attempt attempts"
            return 0
        fi
        
        log_info "Attempt $attempt/$max_attempts - Service not ready yet, waiting..."
        sleep 10
        ((attempt++))
    done
    
    error_exit "Service failed to become ready after $max_attempts attempts"
}

# Health check
health_check() {
    local service="$1"
    
    # Check if service is running
    if ! systemctl is-active --quiet "$service"; then
        return 1
    fi
    
    # Check HTTP health endpoint
    if [[ -n "${HEALTH_CHECK_URL:-}" ]]; then
        local response_code=$(curl -s -o /dev/null -w "%{http_code}" "${HEALTH_CHECK_URL}" || echo "000")
        if [[ "$response_code" == "200" ]]; then
            return 0
        else
            log_warn "Health check failed: HTTP $response_code"
            return 1
        fi
    fi
    
    return 0
}

# Rollback function
rollback() {
    local service="$1"
    local backup_dir="/opt/backups/${service}"
    
    log_warn "Rolling back $service..."
    
    # Find latest backup
    local latest_backup=$(find "$backup_dir" -name "${service}_*.tar.gz" | sort -r | head -1)
    
    if [[ -z "$latest_backup" ]]; then
        error_exit "No backup found for rollback"
    fi
    
    log_info "Restoring from backup: $latest_backup"
    
    # Stop service
    systemctl stop "$service"
    
    # Restore backup
    tar -xzf "$latest_backup" -C "/opt"
    
    # Start service
    systemctl start "$service"
    
    # Verify rollback
    if health_check "$service"; then
        log_success "Rollback completed successfully"
    else
        error_exit "Rollback failed - service is not healthy"
    fi
}

# Post-deployment tasks
post_deployment_tasks() {
    local environment="$1"
    local service="$2"
    
    log_info "Running post-deployment tasks..."
    
    # Update monitoring configuration
    if [[ -f "/etc/prometheus/targets/${service}.json" ]]; then
        systemctl reload prometheus
        log_info "Prometheus configuration reloaded"
    fi
    
    # Send deployment notification
    send_notification "$environment" "$service" "success"
    
    # Update deployment tracking
    echo "$(date '+%Y-%m-%d %H:%M:%S'),${environment},${service},${DOCKER_IMAGE},success" >> "/var/log/deployments.csv"
    
    log_success "Post-deployment tasks completed"
}

# Send notification (Slack webhook)
send_notification() {
    local environment="$1"
    local service="$2"
    local status="$3"
    
    if [[ -z "${SLACK_WEBHOOK_URL:-}" ]]; then
        return 0
    fi
    
    local color="good"
    [[ "$status" != "success" ]] && color="danger"
    
    local payload=$(cat <<EOF
{
    "attachments": [
        {
            "color": "$color",
            "title": "Deployment $status",
            "fields": [
                {
                    "title": "Environment",
                    "value": "$environment",
                    "short": true
                },
                {
                    "title": "Service",
                    "value": "$service",
                    "short": true
                },
                {
                    "title": "Image",
                    "value": "${DOCKER_IMAGE}",
                    "short": false
                }
            ],
            "ts": $(date +%s)
        }
    ]
}
EOF
)
    
    curl -X POST -H 'Content-type: application/json' \
         --data "$payload" \
         "${SLACK_WEBHOOK_URL}" >/dev/null 2>&1 || log_warn "Failed to send notification"
}

# Main function
main() {
    local environment="${1:-}"
    local service="${2:-}"
    local dry_run="false"
    
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --dry-run)
                dry_run="true"
                shift
                ;;
            --rollback)
                rollback "$service"
                exit 0
                ;;
            -h|--help)
                cat <<EOF
Usage: $0 <environment> <service> [options]

Environments: dev, staging, prod
Options:
  --dry-run     Show what would be done without making changes
  --rollback    Rollback to previous version
  -h, --help    Show this help message

Examples:
  $0 staging api-service
  $0 prod web-app --dry-run
  $0 prod api-service --rollback
EOF
                exit 0
                ;;
            *)
                if [[ -z "$environment" ]]; then
                    environment="$1"
                elif [[ -z "$service" ]]; then
                    service="$1"
                else
                    error_exit "Unknown argument: $1"
                fi
                shift
                ;;
        esac
    done
    
    # Validate arguments
    [[ -z "$environment" ]] && error_exit "Environment is required"
    [[ -z "$service" ]] && error_exit "Service name is required"
    
    # Start deployment process
    log_info "Starting deployment process..."
    log_info "Environment: $environment"
    log_info "Service: $service"
    log_info "Dry run: $dry_run"
    
    acquire_lock
    validate_environment "$environment"
    validate_service "$service"
    
    pre_deployment_checks "$environment" "$service"
    
    if [[ "$dry_run" != "true" ]]; then
        backup_current_version "$service"
    fi
    
    deploy_application "$environment" "$service" "$dry_run"
    
    if [[ "$dry_run" != "true" ]]; then
        post_deployment_tasks "$environment" "$service"
    fi
    
    log_success "Deployment process completed successfully!"
}

# Run main function if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
```

### System Health Check Script
```bash
#!/bin/bash
# System health monitoring script for production servers

set -euo pipefail

# Configuration
readonly SCRIPT_NAME="$(basename "$0")"
readonly LOG_FILE="/var/log/health-check.log"
readonly ALERT_THRESHOLD_CPU=80
readonly ALERT_THRESHOLD_MEMORY=85
readonly ALERT_THRESHOLD_DISK=90
readonly ALERT_THRESHOLD_LOAD=5.0

# Colors
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly NC='\033[0m'

# Logging
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

# Check CPU usage
check_cpu() {
    local cpu_usage
    cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | sed 's/%us,//')
    cpu_usage=${cpu_usage%.*}  # Remove decimal
    
    log "CPU Usage: ${cpu_usage}%"
    
    if [[ $cpu_usage -gt $ALERT_THRESHOLD_CPU ]]; then
        log "⚠️  HIGH CPU USAGE: ${cpu_usage}%"
        
        # Get top CPU consuming processes
        log "Top CPU consuming processes:"
        ps aux --sort=-%cpu | head -6 | tee -a "$LOG_FILE"
        
        return 1
    fi
    
    return 0
}

# Check memory usage
check_memory() {
    local memory_info
    memory_info=$(free | grep Mem)
    local total=$(echo "$memory_info" | awk '{print $2}')
    local used=$(echo "$memory_info" | awk '{print $3}')
    local memory_percent=$((used * 100 / total))
    
    log "Memory Usage: ${memory_percent}% (${used}/${total})"
    
    if [[ $memory_percent -gt $ALERT_THRESHOLD_MEMORY ]]; then
        log "⚠️  HIGH MEMORY USAGE: ${memory_percent}%"
        
        # Get top memory consuming processes
        log "Top memory consuming processes:"
        ps aux --sort=-%mem | head -6 | tee -a "$LOG_FILE"
        
        return 1
    fi
    
    return 0
}

# Check disk usage
check_disk() {
    local alerts=0
    
    log "Disk Usage:"
    while IFS= read -r line; do
        local usage=$(echo "$line" | awk '{print $5}' | sed 's/%//')
        local mount=$(echo "$line" | awk '{print $6}')
        
        log "  $mount: ${usage}%"
        
        if [[ $usage -gt $ALERT_THRESHOLD_DISK ]]; then
            log "⚠️  HIGH DISK USAGE: $mount at ${usage}%"
            
            # Show largest files/directories
            log "Largest items in $mount:"
            du -h "$mount" 2>/dev/null | sort -hr | head -5 | tee -a "$LOG_FILE" || true
            
            ((alerts++))
        fi
    done < <(df -h | grep -E '^/dev')
    
    return $alerts
}

# Check system load
check_load() {
    local load_avg
    load_avg=$(uptime | awk -F'load average:' '{print $2}' | awk '{print $1}' | sed 's/,//')
    
    log "Load Average (1min): $load_avg"
    
    if (( $(echo "$load_avg > $ALERT_THRESHOLD_LOAD" | bc -l) )); then
        log "⚠️  HIGH SYSTEM LOAD: $load_avg"
        
        # Show running processes
        log "Currently running processes:"
        ps aux | awk '$8 ~ /^R/ {print $0}' | tee -a "$LOG_FILE"
        
        return 1
    fi
    
    return 0
}

# Check service status
check_services() {
    local services=("nginx" "docker" "ssh" "systemd-resolved")
    local failed_services=()
    
    log "Service Status Check:"
    
    for service in "${services[@]}"; do
        if systemctl is-active --quiet "$service"; then
            log "  ✅ $service: active"
        else
            log "  ❌ $service: inactive/failed"
            failed_services+=("$service")
        fi
    done
    
    if [[ ${#failed_services[@]} -gt 0 ]]; then
        log "⚠️  FAILED SERVICES: ${failed_services[*]}"
        
        for service in "${failed_services[@]}"; do
            log "Status for $service:"
            systemctl status "$service" --no-pager -l | tee -a "$LOG_FILE"
        done
        
        return 1
    fi
    
    return 0
}

# Check network connectivity
check_network() {
    local test_hosts=("8.8.8.8" "1.1.1.1" "google.com")
    local failed_hosts=()
    
    log "Network Connectivity Check:"
    
    for host in "${test_hosts[@]}"; do
        if ping -c 1 -W 5 "$host" >/dev/null 2>&1; then
            log "  ✅ $host: reachable"
        else
            log "  ❌ $host: unreachable"
            failed_hosts+=("$host")
        fi
    done
    
    if [[ ${#failed_hosts[@]} -gt 0 ]]; then
        log "⚠️  NETWORK ISSUES: Unable to reach ${failed_hosts[*]}"
        
        # Check network interface status
        log "Network interface status:"
        ip addr show | grep -E '^[0-9]:|inet ' | tee -a "$LOG_FILE"
        
        return 1
    fi
    
    return 0
}

# Check Docker containers (if Docker is installed)
check_docker() {
    if ! command -v docker >/dev/null 2>&1; then
        return 0
    fi
    
    log "Docker Container Status:"
    
    local unhealthy_containers
    unhealthy_containers=$(docker ps -a --format "table {{.Names}}\t{{.Status}}" | grep -v "Up\|STATUS" || true)
    
    if [[ -n "$unhealthy_containers" ]]; then
        log "⚠️  UNHEALTHY DOCKER CONTAINERS:"
        echo "$unhealthy_containers" | tee -a "$LOG_FILE"
        
        # Show container logs for failed containers
        while IFS= read -r line; do
            local container_name=$(echo "$line" | awk '{print $1}')
            if [[ -n "$container_name" ]]; then
                log "Last 10 lines from $container_name:"
                docker logs --tail 10 "$container_name" 2>&1 | tee -a "$LOG_FILE"
            fi
        done <<< "$unhealthy_containers"
        
        return 1
    else
        docker ps --format "table {{.Names}}\t{{.Status}}" | tee -a "$LOG_FILE"
        return 0
    fi
}

# Check SSL certificate expiration
check_ssl_certificates() {
    local cert_dir="/etc/ssl/certs"
    local expired_certs=()
    
    if [[ ! -d "$cert_dir" ]]; then
        return 0
    fi
    
    log "SSL Certificate Check:"
    
    for cert_file in "$cert_dir"/*.crt; do
        [[ -f "$cert_file" ]] || continue
        
        local cert_name=$(basename "$cert_file" .crt)
        local expiry_date
        expiry_date=$(openssl x509 -enddate -noout -in "$cert_file" 2>/dev/null | cut -d= -f2)
        
        if [[ -n "$expiry_date" ]]; then
            local expiry_timestamp
            expiry_timestamp=$(date -d "$expiry_date" +%s 2>/dev/null || echo 0)
            local current_timestamp
            current_timestamp=$(date +%s)
            local days_until_expiry=$(( (expiry_timestamp - current_timestamp) / 86400 ))
            
            if [[ $days_until_expiry -lt 0 ]]; then
                log "  ❌ $cert_name: EXPIRED"
                expired_certs+=("$cert_name")
            elif [[ $days_until_expiry -lt 30 ]]; then
                log "  ⚠️  $cert_name: expires in $days_until_expiry days"
            else
                log "  ✅ $cert_name: expires in $days_until_expiry days"
            fi
        fi
    done
    
    if [[ ${#expired_certs[@]} -gt 0 ]]; then
        log "⚠️  EXPIRED CERTIFICATES: ${expired_certs[*]}"
        return 1
    fi
    
    return 0
}

# Generate health report
generate_report() {
    local overall_status="HEALTHY"
    local issues=()
    
    log "=== SYSTEM HEALTH CHECK REPORT ==="
    log "Timestamp: $(date)"
    log "Hostname: $(hostname)"
    log "Uptime: $(uptime)"
    log ""
    
    # Run all checks
    check_cpu || issues+=("CPU")
    check_memory || issues+=("MEMORY")
    check_disk || issues+=("DISK")
    check_load || issues+=("LOAD")
    check_services || issues+=("SERVICES")
    check_network || issues+=("NETWORK")
    check_docker || issues+=("DOCKER")
    check_ssl_certificates || issues+=("SSL")
    
    # Summary
    log ""
    log "=== HEALTH CHECK SUMMARY ==="
    
    if [[ ${#issues[@]} -gt 0 ]]; then
        overall_status="ISSUES DETECTED"
        log "❌ Overall Status: $overall_status"
        log "⚠️  Issues found in: ${issues[*]}"
    else
        log "✅ Overall Status: $overall_status"
        log "All checks passed!"
    fi
    
    return ${#issues[@]}
}

# Send alert
send_alert() {
    local message="$1"
    
    # Send to syslog
    logger -t "$SCRIPT_NAME" "$message"
    
    # Send email if configured
    if [[ -n "${ALERT_EMAIL:-}" ]] && command -v mail >/dev/null 2>&1; then
        echo "$message" | mail -s "Health Check Alert - $(hostname)" "$ALERT_EMAIL"
    fi
    
    # Send to Slack if webhook URL is configured
    if [[ -n "${SLACK_WEBHOOK_URL:-}" ]]; then
        local payload=$(cat <<EOF
{
    "text": "🚨 Health Check Alert",
    "attachments": [
        {
            "color": "danger",
            "fields": [
                {
                    "title": "Server",
                    "value": "$(hostname)",
                    "short": true
                },
                {
                    "title": "Message",
                    "value": "$message",
                    "short": false
                }
            ]
        }
    ]
}
EOF
)
        
        curl -X POST -H 'Content-type: application/json' \
             --data "$payload" \
             "$SLACK_WEBHOOK_URL" >/dev/null 2>&1 || true
    fi
}

# Main execution
main() {
    local exit_code=0
    
    # Check if running as root (recommended for full system access)
    if [[ $EUID -ne 0 ]]; then
        log "⚠️  Warning: Not running as root. Some checks may be limited."
    fi
    
    # Run health checks
    if ! generate_report; then
        exit_code=1
        send_alert "System health check detected issues on $(hostname). Check $LOG_FILE for details."
    fi
    
    # Rotate log file if it gets too large (>10MB)
    if [[ -f "$LOG_FILE" ]] && [[ $(stat -f%z "$LOG_FILE" 2>/dev/null || stat -c%s "$LOG_FILE") -gt 10485760 ]]; then
        mv "$LOG_FILE" "${LOG_FILE}.old"
        log "Log file rotated"
    fi
    
    exit $exit_code
}

# Run main function if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
```

This provides comprehensive production-ready Bash automation scripts with proper error handling, logging, monitoring, and deployment capabilities.