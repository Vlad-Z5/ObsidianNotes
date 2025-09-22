# Terraform Security and Compliance

**Terraform Security and Compliance** ensures infrastructure deployments meet security standards, regulatory requirements, and enterprise policies through secure coding practices, secret management, policy as code, and compliance frameworks.

## Security Best Practices

### Secure State Management

#### Remote State with Encryption
```hcl
# terraform/backend.tf
terraform {
  backend "s3" {
    bucket               = "company-terraform-state"
    key                  = "infrastructure/terraform.tfstate"
    region               = "us-west-2"
    encrypt              = true
    kms_key_id          = "arn:aws:kms:us-west-2:123456789012:key/12345678-1234-1234-1234-123456789012"
    dynamodb_table      = "terraform-state-lock"
    workspace_key_prefix = "workspaces"

    # Additional security configurations
    versioning                = true
    server_side_encryption_configuration {
      rule {
        apply_server_side_encryption_by_default {
          kms_master_key_id = "arn:aws:kms:us-west-2:123456789012:key/12345678-1234-1234-1234-123456789012"
          sse_algorithm     = "aws:kms"
        }
      }
    }

    # Access logging
    logging {
      target_bucket = "company-terraform-state-logs"
      target_prefix = "access-logs/"
    }
  }
}

# DynamoDB table for state locking with encryption
resource "aws_dynamodb_table" "terraform_state_lock" {
  name           = "terraform-state-lock"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "LockID"

  attribute {
    name = "LockID"
    type = "S"
  }

  # Encryption at rest
  server_side_encryption {
    enabled     = true
    kms_key_arn = aws_kms_key.terraform_state.arn
  }

  # Point-in-time recovery
  point_in_time_recovery {
    enabled = true
  }

  tags = {
    Name        = "Terraform State Lock"
    Environment = "shared"
    Purpose     = "terraform-state-management"
  }
}

# KMS key for state encryption
resource "aws_kms_key" "terraform_state" {
  description             = "KMS key for Terraform state encryption"
  deletion_window_in_days = 7
  enable_key_rotation     = true

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "Enable IAM User Permissions"
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"
        }
        Action   = "kms:*"
        Resource = "*"
      },
      {
        Sid    = "Allow Terraform execution role"
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/TerraformExecutionRole"
        }
        Action = [
          "kms:Encrypt",
          "kms:Decrypt",
          "kms:ReEncrypt*",
          "kms:GenerateDataKey*",
          "kms:DescribeKey"
        ]
        Resource = "*"
      }
    ]
  })

  tags = {
    Name        = "Terraform State KMS Key"
    Environment = "shared"
  }
}

resource "aws_kms_alias" "terraform_state" {
  name          = "alias/terraform-state"
  target_key_id = aws_kms_key.terraform_state.key_id
}
```

### Secret Management

#### AWS Secrets Manager Integration
```hcl
# modules/secrets/main.tf
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.0"
    }
  }
}

# Database credentials secret
resource "aws_secretsmanager_secret" "db_credentials" {
  name                    = "${var.environment}-${var.application}-db-credentials"
  description             = "Database credentials for ${var.application}"
  recovery_window_in_days = var.environment == "production" ? 30 : 0

  # Automatic rotation configuration
  rotation_rules {
    automatically_after_days = 90
  }

  # KMS encryption
  kms_key_id = var.kms_key_id

  tags = merge(var.tags, {
    Name        = "${var.environment}-${var.application}-db-credentials"
    SecretType  = "database-credentials"
    Application = var.application
  })
}

# Initial secret version with generated password
resource "aws_secretsmanager_secret_version" "db_credentials" {
  secret_id = aws_secretsmanager_secret.db_credentials.id
  secret_string = jsonencode({
    username = var.db_username
    password = random_password.db_password.result
  })

  lifecycle {
    ignore_changes = [secret_string]
  }
}

# Generate secure random password
resource "random_password" "db_password" {
  length  = 32
  special = true
  keepers = {
    version = "1"
  }
}

# Application API keys secret
resource "aws_secretsmanager_secret" "api_keys" {
  name                    = "${var.environment}-${var.application}-api-keys"
  description             = "API keys and tokens for ${var.application}"
  recovery_window_in_days = var.environment == "production" ? 30 : 0

  kms_key_id = var.kms_key_id

  tags = merge(var.tags, {
    Name        = "${var.environment}-${var.application}-api-keys"
    SecretType  = "api-keys"
    Application = var.application
  })
}

resource "aws_secretsmanager_secret_version" "api_keys" {
  secret_id = aws_secretsmanager_secret.api_keys.id
  secret_string = jsonencode({
    stripe_api_key     = var.stripe_api_key
    sendgrid_api_key   = var.sendgrid_api_key
    jwt_secret         = random_password.jwt_secret.result
    encryption_key     = random_password.encryption_key.result
  })

  lifecycle {
    ignore_changes = [secret_string]
  }
}

resource "random_password" "jwt_secret" {
  length  = 64
  special = false
  keepers = {
    version = "1"
  }
}

resource "random_password" "encryption_key" {
  length  = 32
  special = false
  keepers = {
    version = "1"
  }
}

# Lambda function for secret rotation
resource "aws_lambda_function" "secret_rotation" {
  filename         = "secret_rotation.zip"
  function_name    = "${var.environment}-${var.application}-secret-rotation"
  role            = aws_iam_role.secret_rotation.arn
  handler         = "index.handler"
  runtime         = "python3.9"
  timeout         = 300

  environment {
    variables = {
      SECRETS_MANAGER_ENDPOINT = "https://secretsmanager.${data.aws_region.current.name}.amazonaws.com"
    }
  }

  tags = var.tags
}

# IAM role for secret rotation Lambda
resource "aws_iam_role" "secret_rotation" {
  name = "${var.environment}-${var.application}-secret-rotation-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = var.tags
}

# IAM policy for secret rotation
resource "aws_iam_role_policy" "secret_rotation" {
  name = "${var.environment}-${var.application}-secret-rotation-policy"
  role = aws_iam_role.secret_rotation.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:DescribeSecret",
          "secretsmanager:GetSecretValue",
          "secretsmanager:PutSecretValue",
          "secretsmanager:UpdateSecretVersionStage"
        ]
        Resource = [
          aws_secretsmanager_secret.db_credentials.arn,
          aws_secretsmanager_secret.api_keys.arn
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      }
    ]
  })
}

# Secret rotation configuration
resource "aws_secretsmanager_secret_rotation" "db_credentials" {
  secret_id           = aws_secretsmanager_secret.db_credentials.id
  rotation_lambda_arn = aws_lambda_function.secret_rotation.arn

  rotation_rules {
    automatically_after_days = 90
  }

  depends_on = [aws_lambda_permission.secret_rotation]
}

resource "aws_lambda_permission" "secret_rotation" {
  statement_id  = "AllowExecutionFromSecretsManager"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.secret_rotation.function_name
  principal     = "secretsmanager.amazonaws.com"
}
```

#### Secure Variable Usage Pattern
```hcl
# main.tf - Secure way to use secrets
data "aws_secretsmanager_secret" "db_credentials" {
  name = "${var.environment}-${var.application}-db-credentials"
}

data "aws_secretsmanager_secret_version" "db_credentials" {
  secret_id = data.aws_secretsmanager_secret.db_credentials.id
}

locals {
  db_credentials = jsondecode(data.aws_secretsmanager_secret_version.db_credentials.secret_string)
}

# RDS instance using secret
resource "aws_db_instance" "main" {
  identifier = "${var.environment}-${var.application}-db"

  # Use credentials from Secrets Manager
  username = local.db_credentials.username
  password = local.db_credentials.password

  # Never store passwords in variables or outputs
  manage_master_user_password = false

  # Other configuration...
  engine               = "postgres"
  engine_version       = "14.9"
  instance_class       = var.db_instance_class
  allocated_storage    = var.db_allocated_storage
  storage_encrypted    = true
  kms_key_id          = var.kms_key_id

  # Network security
  vpc_security_group_ids = [aws_security_group.database.id]
  db_subnet_group_name   = aws_db_subnet_group.main.name

  # Backup and maintenance
  backup_retention_period = 30
  backup_window          = "03:00-04:00"
  maintenance_window     = "sun:04:00-sun:05:00"

  # Monitoring and logging
  enabled_cloudwatch_logs_exports = ["postgresql"]
  monitoring_interval             = 60
  monitoring_role_arn            = aws_iam_role.rds_monitoring.arn

  # Security
  deletion_protection = var.environment == "production"
  skip_final_snapshot = var.environment != "production"

  tags = var.tags
}

# Never output sensitive values
output "db_endpoint" {
  description = "Database endpoint"
  value       = aws_db_instance.main.endpoint
}

# DON'T DO THIS - Never output secrets
# output "db_password" {
#   value = local.db_credentials.password
# }
```

## Policy as Code

### Open Policy Agent (OPA) Integration

#### OPA Policy Framework
```rego
# policies/terraform/security.rego
package terraform.security

import future.keywords.in
import future.keywords.if

# Deny resources without encryption
deny[msg] {
    resource := input.resource_changes[_]
    resource.type == "aws_s3_bucket"
    not resource.change.after.server_side_encryption_configuration
    msg := sprintf("S3 bucket '%s' must have server-side encryption enabled", [resource.address])
}

deny[msg] {
    resource := input.resource_changes[_]
    resource.type == "aws_db_instance"
    resource.change.after.storage_encrypted == false
    msg := sprintf("RDS instance '%s' must have storage encryption enabled", [resource.address])
}

deny[msg] {
    resource := input.resource_changes[_]
    resource.type == "aws_ebs_volume"
    resource.change.after.encrypted == false
    msg := sprintf("EBS volume '%s' must be encrypted", [resource.address])
}

# Deny overly permissive security groups
deny[msg] {
    resource := input.resource_changes[_]
    resource.type == "aws_security_group_rule"
    resource.change.after.type == "ingress"
    resource.change.after.from_port == 0
    resource.change.after.to_port == 65535
    msg := sprintf("Security group rule '%s' allows access to all ports", [resource.address])
}

deny[msg] {
    resource := input.resource_changes[_]
    resource.type == "aws_security_group_rule"
    resource.change.after.type == "ingress"
    "0.0.0.0/0" in resource.change.after.cidr_blocks
    resource.change.after.from_port == 22
    msg := sprintf("Security group rule '%s' allows SSH access from anywhere", [resource.address])
}

# Require specific tags
required_tags := ["Environment", "Owner", "CostCenter", "Project"]

deny[msg] {
    resource := input.resource_changes[_]
    resource.type in ["aws_instance", "aws_rds_cluster", "aws_s3_bucket"]
    tags := object.get(resource.change.after, "tags", {})
    missing_tags := required_tags - object.keys(tags)
    count(missing_tags) > 0
    msg := sprintf("Resource '%s' is missing required tags: %v", [resource.address, missing_tags])
}

# Deny public RDS instances
deny[msg] {
    resource := input.resource_changes[_]
    resource.type == "aws_db_instance"
    resource.change.after.publicly_accessible == true
    msg := sprintf("RDS instance '%s' must not be publicly accessible", [resource.address])
}

# Require VPC for EC2 instances
deny[msg] {
    resource := input.resource_changes[_]
    resource.type == "aws_instance"
    not resource.change.after.vpc_security_group_ids
    msg := sprintf("EC2 instance '%s' must be launched in a VPC", [resource.address])
}

# Cost control policies
deny[msg] {
    resource := input.resource_changes[_]
    resource.type == "aws_instance"
    instance_type := resource.change.after.instance_type
    expensive_types := ["c5.24xlarge", "m5.24xlarge", "r5.24xlarge"]
    instance_type in expensive_types
    msg := sprintf("EC2 instance '%s' uses expensive instance type '%s'", [resource.address, instance_type])
}

# Network security policies
deny[msg] {
    resource := input.resource_changes[_]
    resource.type == "aws_subnet"
    resource.change.after.map_public_ip_on_launch == true
    not contains(resource.change.after.tags.Name, "public")
    msg := sprintf("Subnet '%s' auto-assigns public IPs but is not tagged as public", [resource.address])
}

# IAM security policies
deny[msg] {
    resource := input.resource_changes[_]
    resource.type == "aws_iam_policy"
    policy_doc := json.unmarshal(resource.change.after.policy)
    statement := policy_doc.Statement[_]
    statement.Effect == "Allow"
    statement.Action == "*"
    statement.Resource == "*"
    msg := sprintf("IAM policy '%s' grants overly broad permissions", [resource.address])
}
```

#### OPA Policy Validation Script
```bash
#!/bin/bash
# scripts/validate-terraform-policies.sh

set -euo pipefail

TERRAFORM_DIR=${1:-"./terraform"}
POLICY_DIR=${2:-"./policies"}
ENVIRONMENT=${3:-"dev"}

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}" >&2
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARN: $1${NC}" >&2
}

# Check prerequisites
check_prerequisites() {
    local required_tools=("terraform" "opa" "jq")

    for tool in "${required_tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            error "$tool is required but not installed"
            exit 1
        fi
    done

    if [[ ! -d "$TERRAFORM_DIR" ]]; then
        error "Terraform directory not found: $TERRAFORM_DIR"
        exit 1
    fi

    if [[ ! -d "$POLICY_DIR" ]]; then
        error "Policy directory not found: $POLICY_DIR"
        exit 1
    fi
}

# Generate Terraform plan
generate_plan() {
    log "Generating Terraform plan for policy validation..."

    cd "$TERRAFORM_DIR/environments/$ENVIRONMENT"

    if ! terraform init -backend=false -input=false; then
        error "Terraform init failed"
        exit 1
    fi

    if ! terraform plan -var-file="terraform.tfvars" -out="policy-check.tfplan"; then
        error "Terraform plan failed"
        exit 1
    fi

    if ! terraform show -json policy-check.tfplan > plan.json; then
        error "Failed to generate plan JSON"
        exit 1
    fi

    log "Terraform plan generated successfully"
}

# Validate with OPA policies
validate_policies() {
    log "Validating Terraform plan against OPA policies..."

    cd "$TERRAFORM_DIR/environments/$ENVIRONMENT"

    local policy_violations=()
    local policy_files
    policy_files=$(find "$POLICY_DIR" -name "*.rego" -type f)

    for policy_file in $policy_files; do
        log "Checking policy: $(basename "$policy_file")"

        local result
        result=$(opa eval -d "$policy_file" -i plan.json "data.terraform.security.deny[x]" --format json)

        local violations
        violations=$(echo "$result" | jq -r '.result[].expressions[].value[]? // empty')

        if [[ -n "$violations" ]]; then
            while IFS= read -r violation; do
                policy_violations+=("$violation")
            done <<< "$violations"
        fi
    done

    # Report results
    if [[ ${#policy_violations[@]} -eq 0 ]]; then
        log "✅ All policy validations passed!"
        return 0
    else
        error "❌ Policy validation failed with ${#policy_violations[@]} violations:"
        for violation in "${policy_violations[@]}"; do
            echo "  • $violation"
        done
        return 1
    fi
}

# Security scan with Checkov
run_checkov() {
    log "Running Checkov security scan..."

    cd "$TERRAFORM_DIR"

    if ! command -v checkov &> /dev/null; then
        warn "Checkov not installed, skipping security scan"
        return 0
    fi

    local checkov_output
    checkov_output=$(checkov --directory . --framework terraform --output json --quiet)

    local failed_checks
    failed_checks=$(echo "$checkov_output" | jq '.results.failed_checks | length')

    local passed_checks
    passed_checks=$(echo "$checkov_output" | jq '.results.passed_checks | length')

    log "Checkov results: $passed_checks passed, $failed_checks failed"

    if [[ "$failed_checks" -gt 0 ]]; then
        warn "Checkov found $failed_checks security issues"
        echo "$checkov_output" | jq -r '.results.failed_checks[] | "• \(.file_path):\(.line_range[0]) - \(.check_name): \(.description)"'
        return 1
    fi

    return 0
}

# Cost analysis with Infracost
analyze_costs() {
    log "Analyzing infrastructure costs..."

    cd "$TERRAFORM_DIR/environments/$ENVIRONMENT"

    if ! command -v infracost &> /dev/null; then
        warn "Infracost not installed, skipping cost analysis"
        return 0
    fi

    local cost_breakdown
    cost_breakdown=$(infracost breakdown --path . --format json 2>/dev/null || echo '{}')

    local monthly_cost
    monthly_cost=$(echo "$cost_breakdown" | jq -r '.totalMonthlyCost // "0"')

    if [[ "$monthly_cost" != "0" ]]; then
        log "Estimated monthly cost: \$$monthly_cost"

        # Set cost thresholds based on environment
        local cost_threshold
        case $ENVIRONMENT in
            prod)
                cost_threshold=1000
                ;;
            staging)
                cost_threshold=500
                ;;
            dev)
                cost_threshold=200
                ;;
            *)
                cost_threshold=100
                ;;
        esac

        if (( $(echo "$monthly_cost > $cost_threshold" | bc -l) )); then
            warn "Monthly cost ($monthly_cost) exceeds threshold for $ENVIRONMENT environment ($cost_threshold)"
            return 1
        fi
    fi

    return 0
}

# Cleanup
cleanup() {
    cd "$TERRAFORM_DIR/environments/$ENVIRONMENT" 2>/dev/null || true
    rm -f policy-check.tfplan plan.json
}

# Main execution
main() {
    log "Starting Terraform policy validation for environment: $ENVIRONMENT"

    check_prerequisites

    local exit_code=0

    # Generate plan for validation
    if ! generate_plan; then
        exit_code=1
    fi

    # Run policy validation
    if ! validate_policies; then
        exit_code=1
    fi

    # Run security scan
    if ! run_checkov; then
        exit_code=1
    fi

    # Analyze costs
    if ! analyze_costs; then
        exit_code=1
    fi

    cleanup

    if [[ $exit_code -eq 0 ]]; then
        log "✅ All validations passed successfully!"
    else
        error "❌ One or more validations failed"
    fi

    exit $exit_code
}

# Trap for cleanup
trap cleanup EXIT

# Run main function
main "$@"
```

## Compliance Frameworks

### SOC 2 Compliance Configuration

#### SOC 2 Compliant Infrastructure
```hcl
# modules/compliance/soc2/main.tf
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.0"
    }
  }
}

# CloudTrail for audit logging (SOC 2 requirement)
resource "aws_cloudtrail" "audit_trail" {
  name           = "${var.environment}-audit-trail"
  s3_bucket_name = aws_s3_bucket.cloudtrail_logs.bucket

  # Multi-region trail for comprehensive coverage
  is_multi_region_trail         = true
  include_global_service_events = true

  # Data events for sensitive resources
  event_selector {
    read_write_type                 = "All"
    include_management_events       = true

    data_resource {
      type   = "AWS::S3::Object"
      values = ["${aws_s3_bucket.sensitive_data.arn}/*"]
    }

    data_resource {
      type   = "AWS::Lambda::Function"
      values = ["*"]
    }
  }

  # Insight selectors for advanced analysis
  insight_selector {
    insight_type = "ApiCallRateInsight"
  }

  # KMS encryption for logs
  kms_key_id = aws_kms_key.cloudtrail.arn

  tags = merge(var.tags, {
    Compliance = "SOC2"
    Purpose    = "audit-logging"
  })

  depends_on = [aws_s3_bucket_policy.cloudtrail_logs]
}

# S3 bucket for CloudTrail logs
resource "aws_s3_bucket" "cloudtrail_logs" {
  bucket        = "${var.environment}-cloudtrail-logs-${random_id.bucket_suffix.hex}"
  force_destroy = false

  tags = merge(var.tags, {
    Compliance = "SOC2"
    Purpose    = "audit-logs"
  })
}

# S3 bucket encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "cloudtrail_logs" {
  bucket = aws_s3_bucket.cloudtrail_logs.id

  rule {
    apply_server_side_encryption_by_default {
      kms_master_key_id = aws_kms_key.cloudtrail.arn
      sse_algorithm     = "aws:kms"
    }
    bucket_key_enabled = true
  }
}

# S3 bucket versioning
resource "aws_s3_bucket_versioning" "cloudtrail_logs" {
  bucket = aws_s3_bucket.cloudtrail_logs.id
  versioning_configuration {
    status = "Enabled"
  }
}

# S3 bucket lifecycle configuration
resource "aws_s3_bucket_lifecycle_configuration" "cloudtrail_logs" {
  bucket = aws_s3_bucket.cloudtrail_logs.id

  rule {
    id     = "cloudtrail_logs_lifecycle"
    status = "Enabled"

    # Transition to IA after 30 days
    transition {
      days          = 30
      storage_class = "STANDARD_IA"
    }

    # Transition to Glacier after 90 days
    transition {
      days          = 90
      storage_class = "GLACIER"
    }

    # Transition to Deep Archive after 365 days
    transition {
      days          = 365
      storage_class = "DEEP_ARCHIVE"
    }

    # Retain logs for 7 years (SOC 2 requirement)
    expiration {
      days = 2557  # 7 years
    }

    # Delete old versions after 30 days
    noncurrent_version_expiration {
      noncurrent_days = 30
    }
  }
}

# S3 bucket policy for CloudTrail
resource "aws_s3_bucket_policy" "cloudtrail_logs" {
  bucket = aws_s3_bucket.cloudtrail_logs.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AWSCloudTrailAclCheck"
        Effect = "Allow"
        Principal = {
          Service = "cloudtrail.amazonaws.com"
        }
        Action   = "s3:GetBucketAcl"
        Resource = aws_s3_bucket.cloudtrail_logs.arn
      },
      {
        Sid    = "AWSCloudTrailWrite"
        Effect = "Allow"
        Principal = {
          Service = "cloudtrail.amazonaws.com"
        }
        Action   = "s3:PutObject"
        Resource = "${aws_s3_bucket.cloudtrail_logs.arn}/*"
        Condition = {
          StringEquals = {
            "s3:x-amz-acl" = "bucket-owner-full-control"
          }
        }
      }
    ]
  })
}

# KMS key for CloudTrail encryption
resource "aws_kms_key" "cloudtrail" {
  description             = "KMS key for CloudTrail logs encryption"
  deletion_window_in_days = 7
  enable_key_rotation     = true

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "Enable IAM User Permissions"
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"
        }
        Action   = "kms:*"
        Resource = "*"
      },
      {
        Sid    = "Allow CloudTrail to encrypt logs"
        Effect = "Allow"
        Principal = {
          Service = "cloudtrail.amazonaws.com"
        }
        Action = [
          "kms:GenerateDataKey*",
          "kms:DescribeKey"
        ]
        Resource = "*"
      }
    ]
  })

  tags = merge(var.tags, {
    Compliance = "SOC2"
    Purpose    = "cloudtrail-encryption"
  })
}

# AWS Config for compliance monitoring
resource "aws_config_configuration_recorder" "compliance" {
  name     = "${var.environment}-compliance-recorder"
  role_arn = aws_iam_role.config.arn

  recording_group {
    all_supported = true
    include_global_resource_types = true
    recording_mode {
      recording_frequency = "CONTINUOUS"
    }
  }

  depends_on = [aws_config_delivery_channel.compliance]
}

resource "aws_config_delivery_channel" "compliance" {
  name           = "${var.environment}-compliance-delivery-channel"
  s3_bucket_name = aws_s3_bucket.config_logs.bucket

  snapshot_delivery_properties {
    delivery_frequency = "TwentyFour_Hours"
  }
}

# S3 bucket for AWS Config
resource "aws_s3_bucket" "config_logs" {
  bucket        = "${var.environment}-config-logs-${random_id.bucket_suffix.hex}"
  force_destroy = false

  tags = merge(var.tags, {
    Compliance = "SOC2"
    Purpose    = "config-logs"
  })
}

# IAM role for AWS Config
resource "aws_iam_role" "config" {
  name = "${var.environment}-config-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "config.amazonaws.com"
        }
      }
    ]
  })

  tags = var.tags
}

resource "aws_iam_role_policy_attachment" "config" {
  role       = aws_iam_role.config.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWS_ConfigRole"
}

# GuardDuty for threat detection
resource "aws_guardduty_detector" "main" {
  enable = true

  datasources {
    s3_logs {
      enable = true
    }
    kubernetes {
      audit_logs {
        enable = true
      }
    }
    malware_protection {
      scan_ec2_instance_with_findings {
        ebs_volumes {
          enable = true
        }
      }
    }
  }

  tags = merge(var.tags, {
    Compliance = "SOC2"
    Purpose    = "threat-detection"
  })
}

# Security Hub for centralized security findings
resource "aws_securityhub_account" "main" {}

# Inspector for vulnerability assessments
resource "aws_inspector2_enabler" "main" {
  account_ids    = [data.aws_caller_identity.current.account_id]
  resource_types = ["ECR", "EC2"]
}

random_id "bucket_suffix" {
  byte_length = 4
}
```

This comprehensive Terraform Security and Compliance file provides enterprise-grade security practices, policy as code implementation, and compliance framework configurations that ensure infrastructure deployments meet the highest security standards and regulatory requirements.