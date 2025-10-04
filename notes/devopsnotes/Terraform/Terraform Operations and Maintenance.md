# Terraform Operations and Maintenance

**Terraform Operations and Maintenance** encompasses day-to-day operational tasks, monitoring, drift detection, upgrades, backup strategies, and long-term maintenance of infrastructure as code deployments.

## Operational Workflows

### Daily Operations

#### Health Check Script
```bash
#!/bin/bash
# scripts/terraform-health-check.sh

set -euo pipefail

# Configuration
TERRAFORM_DIRS=(
    "environments/dev"
    "environments/staging"
    "environments/prod"
)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARN: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}" >&2
}

info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO: $1${NC}"
}

# Check Terraform state health
check_state_health() {
    local env_dir=$1
    local env_name=$(basename "$env_dir")

    log "Checking state health for environment: $env_name"

    cd "$env_dir"

    # Initialize if needed
    if [[ ! -d ".terraform" ]]; then
        warn "Terraform not initialized in $env_name, initializing..."
        terraform init
    fi

    # Check state lock
    if ! terraform force-unlock -force 2>/dev/null; then
        info "No state lock to release in $env_name"
    fi

    # Refresh state
    log "Refreshing state for $env_name..."
    if ! terraform refresh -input=false; then
        error "Failed to refresh state for $env_name"
        return 1
    fi

    # Check for drift
    log "Checking for configuration drift in $env_name..."
    if terraform plan -detailed-exitcode -input=false > /dev/null; then
        log "✅ No drift detected in $env_name"
    elif [ $? -eq 2 ]; then
        warn "⚠️  Configuration drift detected in $env_name"
        terraform plan -no-color | head -50
        echo "... (truncated)"
    else
        error "❌ Error checking drift in $env_name"
        return 1
    fi

    cd - > /dev/null
    return 0
}

# Check backend health
check_backend_health() {
    local env_dir=$1
    local env_name=$(basename "$env_dir")

    log "Checking backend health for $env_name..."

    cd "$env_dir"

    # Extract backend configuration
    local backend_type
    backend_type=$(terraform init -backend=false && terraform providers lock -fs-mirror=.terraform/providers | grep backend | head -1 | awk '{print $2}' || echo "unknown")

    case $backend_type in
        "s3")
            check_s3_backend_health "$env_name"
            ;;
        "azurerm")
            check_azure_backend_health "$env_name"
            ;;
        "gcs")
            check_gcs_backend_health "$env_name"
            ;;
        *)
            warn "Unknown backend type: $backend_type"
            ;;
    esac

    cd - > /dev/null
}

# Check S3 backend health
check_s3_backend_health() {
    local env_name=$1

    # Extract S3 backend info from Terraform config
    local bucket
    local key
    local region

    bucket=$(grep -A 10 'backend "s3"' *.tf | grep 'bucket' | head -1 | awk -F'"' '{print $2}' || echo "")
    key=$(grep -A 10 'backend "s3"' *.tf | grep 'key' | head -1 | awk -F'"' '{print $2}' || echo "")
    region=$(grep -A 10 'backend "s3"' *.tf | grep 'region' | head -1 | awk -F'"' '{print $2}' || echo "us-west-2")

    if [[ -n "$bucket" && -n "$key" ]]; then
        # Check if state file exists
        if aws s3 ls "s3://$bucket/$key" --region "$region" >/dev/null 2>&1; then
            log "✅ S3 backend state file exists for $env_name"

            # Check state file size
            local size
            size=$(aws s3 ls "s3://$bucket/$key" --region "$region" | awk '{print $3}')
            if [[ -n "$size" && "$size" -gt 0 ]]; then
                log "✅ S3 state file size: ${size} bytes"
            else
                warn "⚠️  S3 state file is empty"
            fi

            # Check versioning
            local versioning
            versioning=$(aws s3api get-bucket-versioning --bucket "$bucket" --region "$region" --query 'Status' --output text 2>/dev/null || echo "Disabled")
            if [[ "$versioning" == "Enabled" ]]; then
                log "✅ S3 bucket versioning enabled"
            else
                warn "⚠️  S3 bucket versioning not enabled"
            fi
        else
            error "❌ S3 backend state file not found"
        fi
    else
        error "❌ Could not extract S3 backend configuration"
    fi
}

# Generate health report
generate_health_report() {
    local report_file="terraform-health-report-$(date +%Y%m%d-%H%M%S).json"

    log "Generating health report: $report_file"

    cat > "$report_file" << EOF
{
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "environments": []
}
EOF

    for env_dir in "${TERRAFORM_DIRS[@]}"; do
        if [[ -d "$env_dir" ]]; then
            local env_name=$(basename "$env_dir")
            local env_report

            cd "$env_dir"

            # Get resource count
            local resource_count
            resource_count=$(terraform state list 2>/dev/null | wc -l || echo "0")

            # Get last applied time
            local last_applied
            last_applied=$(terraform show -json 2>/dev/null | jq -r '.values.root_module.resources[0].values.tags.LastUpdated // "unknown"' || echo "unknown")

            # Get provider versions
            local providers
            providers=$(terraform providers 2>/dev/null | grep -E '├─|└─' | sed 's/^[├└]─ //g' || echo "unknown")

            env_report=$(cat << EOF
    {
        "name": "$env_name",
        "resource_count": $resource_count,
        "last_applied": "$last_applied",
        "providers": "$providers",
        "status": "healthy"
    }
EOF
            )

            # Update report file
            jq ".environments += [$env_report]" "$report_file" > "${report_file}.tmp" && mv "${report_file}.tmp" "$report_file"

            cd - > /dev/null
        fi
    done

    log "Health report generated: $report_file"
}

# Monitor resource usage
monitor_resource_usage() {
    log "Monitoring resource usage across environments..."

    local total_resources=0

    for env_dir in "${TERRAFORM_DIRS[@]}"; do
        if [[ -d "$env_dir" ]]; then
            local env_name=$(basename "$env_dir")
            cd "$env_dir"

            local resource_count
            resource_count=$(terraform state list 2>/dev/null | wc -l || echo "0")

            total_resources=$((total_resources + resource_count))

            log "Environment $env_name: $resource_count resources"

            # List resource types
            if [[ "$resource_count" -gt 0 ]]; then
                log "Resource breakdown for $env_name:"
                terraform state list 2>/dev/null | cut -d'.' -f1 | sort | uniq -c | sort -nr | head -10 | while read count type; do
                    info "  $type: $count"
                done
            fi

            cd - > /dev/null
        fi
    done

    log "Total resources across all environments: $total_resources"

    # Alert if resource count is high
    if [[ "$total_resources" -gt 1000 ]]; then
        warn "High resource count detected: $total_resources (consider reviewing resource usage)"
    fi
}

# Main execution
main() {
    log "Starting Terraform health check..."

    local overall_status="healthy"

    for env_dir in "${TERRAFORM_DIRS[@]}"; do
        if [[ -d "$env_dir" ]]; then
            if ! check_state_health "$env_dir"; then
                overall_status="unhealthy"
            fi

            check_backend_health "$env_dir"
        else
            warn "Environment directory not found: $env_dir"
        fi
    done

    monitor_resource_usage
    generate_health_report

    if [[ "$overall_status" == "healthy" ]]; then
        log "✅ Overall health check passed"
        exit 0
    else
        error "❌ Health check failed"
        exit 1
    fi
}

# Run main function
main "$@"
```

### Drift Detection and Remediation

#### Automated Drift Detection
```bash
#!/bin/bash
# scripts/detect-drift.sh

set -euo pipefail

ENVIRONMENTS=("dev" "staging" "prod")
DRIFT_REPORT_DIR="drift-reports"
SLACK_WEBHOOK_URL="${SLACK_WEBHOOK_URL:-}"

# Create drift report directory
mkdir -p "$DRIFT_REPORT_DIR"

# Function to send Slack notification
send_slack_notification() {
    local message="$1"
    local color="$2"

    if [[ -n "$SLACK_WEBHOOK_URL" ]]; then
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"attachments\":[{\"color\":\"$color\",\"text\":\"$message\"}]}" \
            "$SLACK_WEBHOOK_URL"
    fi
}

# Function to detect drift for an environment
detect_drift() {
    local env="$1"
    local env_dir="environments/$env"

    echo "Checking drift for environment: $env"

    if [[ ! -d "$env_dir" ]]; then
        echo "Environment directory not found: $env_dir"
        return 1
    fi

    cd "$env_dir"

    # Initialize if needed
    terraform init -input=false

    # Generate plan to detect drift
    local plan_output
    local plan_exit_code

    plan_output=$(terraform plan -detailed-exitcode -no-color 2>&1)
    plan_exit_code=$?

    case $plan_exit_code in
        0)
            echo "✅ No drift detected in $env"
            ;;
        1)
            echo "❌ Error detecting drift in $env"
            echo "$plan_output"
            cd - > /dev/null
            return 1
            ;;
        2)
            echo "⚠️  Drift detected in $env"

            # Save drift report
            local report_file="$DRIFT_REPORT_DIR/drift-$env-$(date +%Y%m%d-%H%M%S).txt"
            echo "$plan_output" > "$report_file"

            # Extract drift summary
            local added=$(echo "$plan_output" | grep -c "will be created" || echo "0")
            local changed=$(echo "$plan_output" | grep -c "will be updated" || echo "0")
            local destroyed=$(echo "$plan_output" | grep -c "will be destroyed" || echo "0")

            local drift_summary="Environment: $env\nAdded: $added\nChanged: $changed\nDestroyed: $destroyed"

            echo "Drift Summary:"
            echo -e "$drift_summary"

            # Send notification
            send_slack_notification "🚨 Infrastructure drift detected in $env environment!\n$drift_summary" "warning"

            # Auto-remediation for specific environments
            if [[ "$env" == "dev" && "${AUTO_REMEDIATE_DEV:-false}" == "true" ]]; then
                echo "Auto-remediating drift in $env environment..."
                terraform apply -auto-approve
                send_slack_notification "✅ Auto-remediation completed for $env environment" "good"
            fi
            ;;
    esac

    cd - > /dev/null
    return 0
}

# Main execution
echo "Starting drift detection across all environments..."

for env in "${ENVIRONMENTS[@]}"; do
    detect_drift "$env"
done

echo "Drift detection completed. Reports saved in: $DRIFT_REPORT_DIR"
```

## Backup and Recovery

### State Backup Strategy

#### Automated State Backup
```bash
#!/bin/bash
# scripts/backup-terraform-state.sh

set -euo pipefail

# Configuration
BACKUP_BUCKET="${BACKUP_BUCKET:-terraform-state-backups}"
BACKUP_PREFIX="${BACKUP_PREFIX:-daily-backups}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
AWS_REGION="${AWS_REGION:-us-west-2}"

# Environments to backup
ENVIRONMENTS=("dev" "staging" "prod")

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

# Function to backup state for an environment
backup_environment_state() {
    local env="$1"
    local env_dir="environments/$env"
    local timestamp=$(date +%Y%m%d-%H%M%S)

    log "Backing up state for environment: $env"

    if [[ ! -d "$env_dir" ]]; then
        log "Environment directory not found: $env_dir"
        return 1
    fi

    cd "$env_dir"

    # Initialize terraform
    terraform init -input=false

    # Pull latest state
    terraform state pull > "terraform-state-$env-$timestamp.json"

    # Backup to S3
    aws s3 cp "terraform-state-$env-$timestamp.json" \
        "s3://$BACKUP_BUCKET/$BACKUP_PREFIX/$env/terraform-state-$env-$timestamp.json" \
        --region "$AWS_REGION"

    # Create metadata file
    cat > "backup-metadata-$env-$timestamp.json" << EOF
{
    "environment": "$env",
    "timestamp": "$timestamp",
    "backup_date": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "terraform_version": "$(terraform version -json | jq -r '.terraform_version')",
    "state_version": $(jq '.version // 0' "terraform-state-$env-$timestamp.json"),
    "resource_count": $(jq '.resources | length' "terraform-state-$env-$timestamp.json"),
    "backup_size_bytes": $(wc -c < "terraform-state-$env-$timestamp.json")
}
EOF

    # Upload metadata
    aws s3 cp "backup-metadata-$env-$timestamp.json" \
        "s3://$BACKUP_BUCKET/$BACKUP_PREFIX/$env/backup-metadata-$env-$timestamp.json" \
        --region "$AWS_REGION"

    # Cleanup local files
    rm -f "terraform-state-$env-$timestamp.json" "backup-metadata-$env-$timestamp.json"

    log "✅ State backup completed for $env"

    cd - > /dev/null
}

# Function to cleanup old backups
cleanup_old_backups() {
    log "Cleaning up backups older than $RETENTION_DAYS days..."

    for env in "${ENVIRONMENTS[@]}"; do
        aws s3api list-objects-v2 \
            --bucket "$BACKUP_BUCKET" \
            --prefix "$BACKUP_PREFIX/$env/" \
            --query "Contents[?LastModified<='$(date -d "$RETENTION_DAYS days ago" -u +%Y-%m-%dT%H:%M:%SZ)'].Key" \
            --output text \
            --region "$AWS_REGION" | \
        while read -r key; do
            if [[ -n "$key" && "$key" != "None" ]]; then
                log "Deleting old backup: s3://$BACKUP_BUCKET/$key"
                aws s3 rm "s3://$BACKUP_BUCKET/$key" --region "$AWS_REGION"
            fi
        done
    done
}

# Function to verify backup integrity
verify_backup_integrity() {
    local env="$1"
    local backup_date="$2"

    log "Verifying backup integrity for $env ($backup_date)..."

    # Download backup
    aws s3 cp "s3://$BACKUP_BUCKET/$BACKUP_PREFIX/$env/terraform-state-$env-$backup_date.json" \
        "/tmp/verify-state-$env.json" \
        --region "$AWS_REGION"

    # Verify JSON structure
    if jq empty "/tmp/verify-state-$env.json" 2>/dev/null; then
        log "✅ Backup integrity verified for $env"
    else
        log "❌ Backup integrity check failed for $env"
        return 1
    fi

    # Cleanup
    rm -f "/tmp/verify-state-$env.json"
}

# Main execution
log "Starting Terraform state backup process..."

# Create backup bucket if it doesn't exist
if ! aws s3 ls "s3://$BACKUP_BUCKET" --region "$AWS_REGION" >/dev/null 2>&1; then
    log "Creating backup bucket: $BACKUP_BUCKET"
    aws s3 mb "s3://$BACKUP_BUCKET" --region "$AWS_REGION"

    # Enable versioning
    aws s3api put-bucket-versioning \
        --bucket "$BACKUP_BUCKET" \
        --versioning-configuration Status=Enabled \
        --region "$AWS_REGION"

    # Enable encryption
    aws s3api put-bucket-encryption \
        --bucket "$BACKUP_BUCKET" \
        --server-side-encryption-configuration '{
            "Rules": [{
                "ApplyServerSideEncryptionByDefault": {
                    "SSEAlgorithm": "AES256"
                }
            }]
        }' \
        --region "$AWS_REGION"
fi

# Backup all environments
for env in "${ENVIRONMENTS[@]}"; do
    backup_environment_state "$env"
done

# Cleanup old backups
cleanup_old_backups

log "Backup process completed successfully"
```

### State Recovery Procedures

#### State Recovery Script
```bash
#!/bin/bash
# scripts/recover-terraform-state.sh

set -euo pipefail

# Configuration
BACKUP_BUCKET="${BACKUP_BUCKET:-terraform-state-backups}"
BACKUP_PREFIX="${BACKUP_PREFIX:-daily-backups}"
AWS_REGION="${AWS_REGION:-us-west-2}"

usage() {
    cat << EOF
Usage: $0 [OPTIONS] ENVIRONMENT [BACKUP_DATE]

Recover Terraform state from backup

OPTIONS:
    -l, --list          List available backups
    -d, --dry-run       Show what would be restored without executing
    -f, --force         Force restore without confirmation
    -h, --help          Show this help message

ARGUMENTS:
    ENVIRONMENT         Environment to restore (dev, staging, prod)
    BACKUP_DATE         Backup date in format YYYYMMDD-HHMMSS (optional, latest if not specified)

EXAMPLES:
    $0 -l                           # List all available backups
    $0 dev                          # Restore latest backup for dev environment
    $0 prod 20231201-143022         # Restore specific backup for prod environment
    $0 -d staging                   # Dry run restore for staging environment

EOF
}

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

error() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1" >&2
}

# List available backups
list_backups() {
    local env="${1:-}"

    if [[ -n "$env" ]]; then
        log "Available backups for environment: $env"
        aws s3 ls "s3://$BACKUP_BUCKET/$BACKUP_PREFIX/$env/" --region "$AWS_REGION" | \
        grep "terraform-state-$env-" | \
        awk '{print $4}' | \
        sed "s/terraform-state-$env-//" | \
        sed 's/.json$//' | \
        sort -r
    else
        log "Available backups for all environments:"
        for environment in dev staging prod; do
            echo "=== $environment ==="
            aws s3 ls "s3://$BACKUP_BUCKET/$BACKUP_PREFIX/$environment/" --region "$AWS_REGION" | \
            grep "terraform-state-$environment-" | \
            awk '{print $4}' | \
            sed "s/terraform-state-$environment-//" | \
            sed 's/.json$//' | \
            sort -r | \
            head -5
            echo
        done
    fi
}

# Get latest backup date for environment
get_latest_backup() {
    local env="$1"

    aws s3 ls "s3://$BACKUP_BUCKET/$BACKUP_PREFIX/$env/" --region "$AWS_REGION" | \
    grep "terraform-state-$env-" | \
    awk '{print $4}' | \
    sed "s/terraform-state-$env-//" | \
    sed 's/.json$//' | \
    sort -r | \
    head -1
}

# Verify backup exists
verify_backup_exists() {
    local env="$1"
    local backup_date="$2"

    local backup_path="s3://$BACKUP_BUCKET/$BACKUP_PREFIX/$env/terraform-state-$env-$backup_date.json"

    if aws s3 ls "$backup_path" --region "$AWS_REGION" >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Create backup before recovery
create_pre_recovery_backup() {
    local env="$1"
    local env_dir="environments/$env"

    log "Creating pre-recovery backup for $env..."

    if [[ ! -d "$env_dir" ]]; then
        error "Environment directory not found: $env_dir"
        return 1
    fi

    cd "$env_dir"

    # Initialize terraform
    terraform init -input=false

    # Create current state backup
    local current_timestamp=$(date +%Y%m%d-%H%M%S)
    terraform state pull > "pre-recovery-state-$env-$current_timestamp.json"

    # Upload to S3
    aws s3 cp "pre-recovery-state-$env-$current_timestamp.json" \
        "s3://$BACKUP_BUCKET/pre-recovery-backups/$env/pre-recovery-state-$env-$current_timestamp.json" \
        --region "$AWS_REGION"

    log "✅ Pre-recovery backup created: pre-recovery-state-$env-$current_timestamp.json"

    # Cleanup local file
    rm -f "pre-recovery-state-$env-$current_timestamp.json"

    cd - > /dev/null
}

# Recover state from backup
recover_state() {
    local env="$1"
    local backup_date="$2"
    local dry_run="${3:-false}"
    local force="${4:-false}"

    local env_dir="environments/$env"
    local backup_path="s3://$BACKUP_BUCKET/$BACKUP_PREFIX/$env/terraform-state-$env-$backup_date.json"

    log "Recovering state for environment: $env from backup: $backup_date"

    # Verify environment directory exists
    if [[ ! -d "$env_dir" ]]; then
        error "Environment directory not found: $env_dir"
        return 1
    fi

    # Verify backup exists
    if ! verify_backup_exists "$env" "$backup_date"; then
        error "Backup not found: $backup_path"
        return 1
    fi

    if [[ "$dry_run" == "true" ]]; then
        log "DRY RUN: Would recover state from $backup_path to $env_dir"
        return 0
    fi

    # Confirmation
    if [[ "$force" != "true" ]]; then
        echo
        echo "⚠️  WARNING: This will replace the current Terraform state for environment '$env'"
        echo "   Source: $backup_path"
        echo "   Target: $env_dir"
        echo
        read -p "Are you sure you want to proceed? (yes/no): " -r
        if [[ ! $REPLY =~ ^yes$ ]]; then
            log "Recovery cancelled by user"
            return 0
        fi
    fi

    cd "$env_dir"

    # Create pre-recovery backup
    create_pre_recovery_backup "$env"

    # Download backup
    log "Downloading backup from S3..."
    aws s3 cp "$backup_path" "recovered-state.json" --region "$AWS_REGION"

    # Validate backup file
    if ! jq empty "recovered-state.json" 2>/dev/null; then
        error "Invalid backup file format"
        rm -f "recovered-state.json"
        cd - > /dev/null
        return 1
    fi

    # Initialize terraform
    terraform init -input=false

    # Push recovered state
    log "Pushing recovered state..."
    if terraform state push "recovered-state.json"; then
        log "✅ State recovery completed successfully"
    else
        error "❌ Failed to push recovered state"
        rm -f "recovered-state.json"
        cd - > /dev/null
        return 1
    fi

    # Cleanup
    rm -f "recovered-state.json"

    # Verify recovery
    log "Verifying recovery..."
    if terraform plan -detailed-exitcode -input=false >/dev/null; then
        log "✅ Recovery verification passed - no drift detected"
    else
        log "⚠️  Recovery verification shows configuration drift - manual review required"
    fi

    cd - > /dev/null
}

# Parse command line arguments
ENVIRONMENT=""
BACKUP_DATE=""
LIST_BACKUPS=false
DRY_RUN=false
FORCE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -l|--list)
            LIST_BACKUPS=true
            shift
            ;;
        -d|--dry-run)
            DRY_RUN=true
            shift
            ;;
        -f|--force)
            FORCE=true
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        -*)
            error "Unknown option: $1"
            usage
            exit 1
            ;;
        *)
            if [[ -z "$ENVIRONMENT" ]]; then
                ENVIRONMENT="$1"
            elif [[ -z "$BACKUP_DATE" ]]; then
                BACKUP_DATE="$1"
            else
                error "Too many arguments"
                usage
                exit 1
            fi
            shift
            ;;
    esac
done

# Main execution
if [[ "$LIST_BACKUPS" == "true" ]]; then
    list_backups "$ENVIRONMENT"
    exit 0
fi

if [[ -z "$ENVIRONMENT" ]]; then
    error "Environment must be specified"
    usage
    exit 1
fi

# Validate environment
case "$ENVIRONMENT" in
    dev|staging|prod)
        ;;
    *)
        error "Invalid environment: $ENVIRONMENT. Must be one of: dev, staging, prod"
        exit 1
        ;;
esac

# Get latest backup if not specified
if [[ -z "$BACKUP_DATE" ]]; then
    BACKUP_DATE=$(get_latest_backup "$ENVIRONMENT")
    if [[ -z "$BACKUP_DATE" ]]; then
        error "No backups found for environment: $ENVIRONMENT"
        exit 1
    fi
    log "Using latest backup: $BACKUP_DATE"
fi

# Perform recovery
recover_state "$ENVIRONMENT" "$BACKUP_DATE" "$DRY_RUN" "$FORCE"
```

## Monitoring and Alerting

### Terraform State Monitoring

#### CloudWatch Monitoring Setup
```hcl
# monitoring/terraform-monitoring.tf
resource "aws_cloudwatch_log_group" "terraform_operations" {
  name              = "/aws/terraform/operations"
  retention_in_days = 30

  tags = {
    Environment = "shared"
    Purpose     = "terraform-monitoring"
  }
}

# Lambda function for state monitoring
resource "aws_lambda_function" "terraform_state_monitor" {
  filename         = "terraform_state_monitor.zip"
  function_name    = "terraform-state-monitor"
  role            = aws_iam_role.terraform_monitor.arn
  handler         = "index.handler"
  runtime         = "python3.9"
  timeout         = 300

  environment {
    variables = {
      STATE_BUCKETS = jsonencode([
        "terraform-state-dev",
        "terraform-state-staging",
        "terraform-state-prod"
      ])
      SLACK_WEBHOOK_URL = var.slack_webhook_url
      LOG_GROUP_NAME    = aws_cloudwatch_log_group.terraform_operations.name
    }
  }

  tags = {
    Environment = "shared"
    Purpose     = "terraform-monitoring"
  }
}

# EventBridge rule for S3 state changes
resource "aws_cloudwatch_event_rule" "terraform_state_changes" {
  name        = "terraform-state-changes"
  description = "Capture Terraform state file changes"

  event_pattern = jsonencode({
    source      = ["aws.s3"]
    detail-type = ["AWS API Call via CloudTrail"]
    detail = {
      eventSource = ["s3.amazonaws.com"]
      eventName   = ["PutObject", "DeleteObject"]
      requestParameters = {
        bucketName = [
          "terraform-state-dev",
          "terraform-state-staging",
          "terraform-state-prod"
        ]
        key = [{
          "suffix": ".tfstate"
        }]
      }
    }
  })

  tags = {
    Environment = "shared"
    Purpose     = "terraform-monitoring"
  }
}

# EventBridge target
resource "aws_cloudwatch_event_target" "lambda_target" {
  rule      = aws_cloudwatch_event_rule.terraform_state_changes.name
  target_id = "TerraformStateMonitorTarget"
  arn       = aws_lambda_function.terraform_state_monitor.arn
}

# Lambda permission for EventBridge
resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.terraform_state_monitor.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.terraform_state_changes.arn
}

# CloudWatch alarms for drift detection
resource "aws_cloudwatch_metric_alarm" "terraform_drift_detection" {
  alarm_name          = "terraform-configuration-drift"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "ConfigurationDrift"
  namespace           = "Terraform/Operations"
  period              = "300"
  statistic           = "Sum"
  threshold           = "0"
  alarm_description   = "This metric monitors Terraform configuration drift"
  alarm_actions       = [aws_sns_topic.terraform_alerts.arn]

  tags = {
    Environment = "shared"
    Purpose     = "terraform-monitoring"
  }
}

# SNS topic for alerts
resource "aws_sns_topic" "terraform_alerts" {
  name = "terraform-operations-alerts"

  tags = {
    Environment = "shared"
    Purpose     = "terraform-monitoring"
  }
}
```

This comprehensive Terraform Operations and Maintenance file provides essential operational workflows, backup strategies, drift detection, recovery procedures, and monitoring solutions that enable teams to maintain healthy Terraform deployments in production environments.