# Terraform Advanced Techniques and Patterns

**Advanced Terraform Techniques and Patterns** encompass sophisticated infrastructure management approaches including dynamic configurations, complex state management, advanced provider usage, and enterprise-scale deployment patterns.

## Dynamic Configuration Patterns

### Dynamic Resource Generation

#### For Each and Count Patterns
```hcl
# Dynamic subnet creation with for_each
locals {
  availability_zones = data.aws_availability_zones.available.names

  # Create subnet configuration dynamically
  subnet_configs = {
    for idx, az in local.availability_zones : az => {
      availability_zone = az
      public_cidr      = cidrsubnet(var.vpc_cidr, 8, idx)
      private_cidr     = cidrsubnet(var.vpc_cidr, 8, idx + 100)
      database_cidr    = cidrsubnet(var.vpc_cidr, 8, idx + 200)
    }
  }

  # Environment-specific instance configurations
  instance_configs = {
    web = {
      instance_type = var.environment == "production" ? "m5.large" : "t3.medium"
      min_size     = var.environment == "production" ? 3 : 1
      max_size     = var.environment == "production" ? 10 : 3
      ports        = [80, 443]
    }
    api = {
      instance_type = var.environment == "production" ? "c5.xlarge" : "t3.large"
      min_size     = var.environment == "production" ? 2 : 1
      max_size     = var.environment == "production" ? 8 : 2
      ports        = [8080, 8443]
    }
    worker = {
      instance_type = var.environment == "production" ? "m5.xlarge" : "t3.large"
      min_size     = var.environment == "production" ? 1 : 0
      max_size     = var.environment == "production" ? 5 : 2
      ports        = []
    }
  }
}

# Dynamic public subnets
resource "aws_subnet" "public" {
  for_each = local.subnet_configs

  vpc_id                  = aws_vpc.main.id
  cidr_block              = each.value.public_cidr
  availability_zone       = each.value.availability_zone
  map_public_ip_on_launch = true

  tags = merge(var.common_tags, {
    Name = "${var.project_name}-public-${each.key}"
    Type = "Public"
    AZ   = each.key
  })
}

# Dynamic private subnets
resource "aws_subnet" "private" {
  for_each = local.subnet_configs

  vpc_id            = aws_vpc.main.id
  cidr_block        = each.value.private_cidr
  availability_zone = each.value.availability_zone

  tags = merge(var.common_tags, {
    Name = "${var.project_name}-private-${each.key}"
    Type = "Private"
    AZ   = each.key
  })
}

# Dynamic security groups for different tiers
resource "aws_security_group" "application_tiers" {
  for_each = local.instance_configs

  name_prefix = "${var.project_name}-${each.key}-"
  vpc_id      = aws_vpc.main.id
  description = "Security group for ${each.key} tier"

  # Dynamic ingress rules
  dynamic "ingress" {
    for_each = each.value.ports
    content {
      from_port   = ingress.value
      to_port     = ingress.value
      protocol    = "tcp"
      cidr_blocks = each.key == "web" ? ["0.0.0.0/0"] : [var.vpc_cidr]
      description = "Allow ${ingress.value} for ${each.key} tier"
    }
  }

  # SSH access from bastion
  ingress {
    from_port       = 22
    to_port         = 22
    protocol        = "tcp"
    security_groups = [aws_security_group.bastion.id]
    description     = "SSH access from bastion"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "All outbound traffic"
  }

  tags = merge(var.common_tags, {
    Name = "${var.project_name}-${each.key}-sg"
    Tier = each.key
  })

  lifecycle {
    create_before_destroy = true
  }
}

# Dynamic Auto Scaling Groups
resource "aws_autoscaling_group" "application_tiers" {
  for_each = local.instance_configs

  name                = "${var.project_name}-${each.key}-asg"
  vpc_zone_identifier = values(aws_subnet.private)[*].id
  target_group_arns   = each.key == "web" ? [aws_lb_target_group.web.arn] : []
  health_check_type   = each.key == "web" ? "ELB" : "EC2"
  health_check_grace_period = 300

  min_size         = each.value.min_size
  max_size         = each.value.max_size
  desired_capacity = each.value.min_size

  launch_template {
    id      = aws_launch_template.application_tiers[each.key].id
    version = "$Latest"
  }

  # Dynamic tags
  dynamic "tag" {
    for_each = merge(var.common_tags, {
      Name = "${var.project_name}-${each.key}"
      Tier = each.key
    })
    content {
      key                 = tag.key
      value               = tag.value
      propagate_at_launch = true
    }
  }

  instance_refresh {
    strategy = "Rolling"
    preferences {
      min_healthy_percentage = 50
    }
  }
}

# Launch templates with dynamic user data
resource "aws_launch_template" "application_tiers" {
  for_each = local.instance_configs

  name_prefix   = "${var.project_name}-${each.key}-"
  image_id      = data.aws_ami.amazon_linux.id
  instance_type = each.value.instance_type
  key_name      = aws_key_pair.main.key_name

  vpc_security_group_ids = [aws_security_group.application_tiers[each.key].id]

  user_data = base64encode(templatefile("${path.module}/user-data/${each.key}.sh", {
    environment = var.environment
    tier        = each.key
    region      = data.aws_region.current.name
  }))

  block_device_mappings {
    device_name = "/dev/xvda"
    ebs {
      volume_type           = "gp3"
      volume_size           = each.key == "worker" ? 100 : 20
      encrypted             = true
      delete_on_termination = true
    }
  }

  metadata_options {
    http_endpoint = "enabled"
    http_tokens   = "required"
    http_put_response_hop_limit = 1
  }

  tag_specifications {
    resource_type = "instance"
    tags = merge(var.common_tags, {
      Name = "${var.project_name}-${each.key}"
      Tier = each.key
    })
  }

  lifecycle {
    create_before_destroy = true
  }
}
```

### Conditional Resource Creation

#### Environment-Based Conditional Logic
```hcl
# Conditional resource creation based on environment
locals {
  # Environment-specific configurations
  environment_config = {
    production = {
      enable_multi_az           = true
      enable_backup            = true
      enable_monitoring        = true
      enable_cdn              = true
      enable_waf              = true
      db_instance_class       = "db.r5.xlarge"
      cache_node_type         = "cache.r5.large"
      min_capacity            = 2
      max_capacity            = 20
    }
    staging = {
      enable_multi_az           = true
      enable_backup            = true
      enable_monitoring        = true
      enable_cdn              = false
      enable_waf              = false
      db_instance_class       = "db.t3.medium"
      cache_node_type         = "cache.t3.medium"
      min_capacity            = 1
      max_capacity            = 5
    }
    development = {
      enable_multi_az           = false
      enable_backup            = false
      enable_monitoring        = false
      enable_cdn              = false
      enable_waf              = false
      db_instance_class       = "db.t3.micro"
      cache_node_type         = "cache.t3.micro"
      min_capacity            = 1
      max_capacity            = 2
    }
  }

  current_config = local.environment_config[var.environment]
}

# Conditional CloudFront distribution
resource "aws_cloudfront_distribution" "main" {
  count = local.current_config.enable_cdn ? 1 : 0

  origin {
    domain_name = aws_lb.main.dns_name
    origin_id   = "ALB-${aws_lb.main.name}"

    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "https-only"
      origin_ssl_protocols   = ["TLSv1.2"]
    }
  }

  enabled             = true
  is_ipv6_enabled     = true
  default_root_object = "index.html"

  default_cache_behavior {
    allowed_methods        = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    cached_methods         = ["GET", "HEAD"]
    target_origin_id       = "ALB-${aws_lb.main.name}"
    compress               = true
    viewer_protocol_policy = "redirect-to-https"

    forwarded_values {
      query_string = true
      headers      = ["Host", "CloudFront-Forwarded-Proto"]
      cookies {
        forward = "none"
      }
    }

    min_ttl     = 0
    default_ttl = 3600
    max_ttl     = 86400
  }

  # Conditional WAF association
  web_acl_id = local.current_config.enable_waf ? aws_wafv2_web_acl.main[0].arn : null

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    acm_certificate_arn      = aws_acm_certificate.main.arn
    ssl_support_method       = "sni-only"
    minimum_protocol_version = "TLSv1.2_2021"
  }

  tags = var.common_tags
}

# Conditional WAF
resource "aws_wafv2_web_acl" "main" {
  count = local.current_config.enable_waf ? 1 : 0

  name  = "${var.project_name}-${var.environment}-waf"
  scope = "CLOUDFRONT"

  default_action {
    allow {}
  }

  # Rate limiting rule
  rule {
    name     = "RateLimitRule"
    priority = 1

    override_action {
      none {}
    }

    statement {
      rate_based_statement {
        limit              = 2000
        aggregate_key_type = "IP"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "RateLimitRule"
      sampled_requests_enabled   = true
    }

    action {
      block {}
    }
  }

  # AWS Managed Rules
  dynamic "rule" {
    for_each = [
      "AWSManagedRulesCommonRuleSet",
      "AWSManagedRulesKnownBadInputsRuleSet",
      "AWSManagedRulesLinuxRuleSet"
    ]
    content {
      name     = rule.value
      priority = index(["AWSManagedRulesCommonRuleSet", "AWSManagedRulesKnownBadInputsRuleSet", "AWSManagedRulesLinuxRuleSet"], rule.value) + 10

      override_action {
        none {}
      }

      statement {
        managed_rule_group_statement {
          name        = rule.value
          vendor_name = "AWS"
        }
      }

      visibility_config {
        cloudwatch_metrics_enabled = true
        metric_name                = rule.value
        sampled_requests_enabled   = true
      }
    }
  }

  tags = var.common_tags
}

# Conditional monitoring and alerting
resource "aws_cloudwatch_metric_alarm" "high_cpu" {
  count = local.current_config.enable_monitoring ? 1 : 0

  alarm_name          = "${var.project_name}-${var.environment}-high-cpu"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/EC2"
  period              = "120"
  statistic           = "Average"
  threshold           = "80"
  alarm_description   = "This metric monitors ec2 cpu utilization"
  alarm_actions       = [aws_sns_topic.alerts[0].arn]

  dimensions = {
    AutoScalingGroupName = aws_autoscaling_group.application_tiers["web"].name
  }

  tags = var.common_tags
}

resource "aws_sns_topic" "alerts" {
  count = local.current_config.enable_monitoring ? 1 : 0

  name = "${var.project_name}-${var.environment}-alerts"

  tags = var.common_tags
}

# Conditional backup configuration
resource "aws_backup_vault" "main" {
  count = local.current_config.enable_backup ? 1 : 0

  name        = "${var.project_name}-${var.environment}-backup-vault"
  kms_key_arn = aws_kms_key.backup[0].arn

  tags = var.common_tags
}

resource "aws_kms_key" "backup" {
  count = local.current_config.enable_backup ? 1 : 0

  description             = "KMS key for backup vault"
  deletion_window_in_days = 7

  tags = var.common_tags
}

resource "aws_backup_plan" "main" {
  count = local.current_config.enable_backup ? 1 : 0

  name = "${var.project_name}-${var.environment}-backup-plan"

  rule {
    rule_name         = "daily_backup"
    target_vault_name = aws_backup_vault.main[0].name
    schedule          = "cron(0 5 ? * * *)"

    recovery_point_tags = var.common_tags

    lifecycle {
      cold_storage_after = 30
      delete_after       = var.environment == "production" ? 365 : 90
    }
  }

  tags = var.common_tags
}
```

## Advanced State Management

### Remote State Data Sources

#### Cross-Stack State References
```hcl
# Network stack state reference
data "terraform_remote_state" "network" {
  backend = "s3"
  config = {
    bucket = "company-terraform-state"
    key    = "network/${var.environment}/terraform.tfstate"
    region = "us-west-2"
  }
}

# Security stack state reference
data "terraform_remote_state" "security" {
  backend = "s3"
  config = {
    bucket = "company-terraform-state"
    key    = "security/${var.environment}/terraform.tfstate"
    region = "us-west-2"
  }
}

# Database stack state reference
data "terraform_remote_state" "database" {
  backend = "s3"
  config = {
    bucket = "company-terraform-state"
    key    = "database/${var.environment}/terraform.tfstate"
    region = "us-west-2"
  }
}

# Use remote state outputs
locals {
  # Network configuration from network stack
  vpc_id             = data.terraform_remote_state.network.outputs.vpc_id
  private_subnet_ids = data.terraform_remote_state.network.outputs.private_subnet_ids
  public_subnet_ids  = data.terraform_remote_state.network.outputs.public_subnet_ids

  # Security groups from security stack
  web_security_group_id      = data.terraform_remote_state.security.outputs.web_security_group_id
  app_security_group_id      = data.terraform_remote_state.security.outputs.app_security_group_id
  database_security_group_id = data.terraform_remote_state.security.outputs.database_security_group_id

  # Database configuration
  database_endpoint = data.terraform_remote_state.database.outputs.database_endpoint
  database_port     = data.terraform_remote_state.database.outputs.database_port
}

# Application load balancer using network stack outputs
resource "aws_lb" "app" {
  name               = "${var.project_name}-${var.environment}-app-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [local.web_security_group_id]
  subnets           = local.public_subnet_ids

  enable_deletion_protection = var.environment == "production"

  tags = var.common_tags
}

# ECS cluster using multiple stack outputs
resource "aws_ecs_cluster" "main" {
  name = "${var.project_name}-${var.environment}-cluster"

  configuration {
    execute_command_configuration {
      kms_key_id = aws_kms_key.ecs.arn
      logging    = "OVERRIDE"

      log_configuration {
        cloud_watch_encryption_enabled = true
        cloud_watch_log_group_name     = aws_cloudwatch_log_group.ecs.name
      }
    }
  }

  tags = var.common_tags
}

# ECS service using cross-stack references
resource "aws_ecs_service" "app" {
  name            = "${var.project_name}-${var.environment}-app"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.app.arn
  desired_count   = var.app_desired_count

  network_configuration {
    subnets          = local.private_subnet_ids
    security_groups  = [local.app_security_group_id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.app.arn
    container_name   = "app"
    container_port   = 8080
  }

  deployment_configuration {
    maximum_percent         = 200
    minimum_healthy_percent = 100
  }

  tags = var.common_tags

  depends_on = [
    aws_lb_listener.app,
    aws_iam_role_policy.ecs_task_execution
  ]
}
```

### State Migration and Import

#### State Migration Script
```bash
#!/bin/bash
# scripts/migrate-terraform-state.sh

set -euo pipefail

# Configuration
OLD_BACKEND="local"
NEW_BACKEND="s3"
ENVIRONMENT=${1:-"dev"}
DRY_RUN=${2:-"false"}

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

# Backup current state
backup_state() {
    log "Creating state backup..."

    local backup_dir="./state-backups/$(date +%Y%m%d-%H%M%S)"
    mkdir -p "$backup_dir"

    if [[ -f "terraform.tfstate" ]]; then
        cp terraform.tfstate "$backup_dir/"
        log "Local state backed up to: $backup_dir/terraform.tfstate"
    fi

    if [[ -f "terraform.tfstate.backup" ]]; then
        cp terraform.tfstate.backup "$backup_dir/"
        log "Local state backup copied to: $backup_dir/terraform.tfstate.backup"
    fi

    echo "$backup_dir" > .last-backup-location
}

# Initialize new backend
init_new_backend() {
    log "Initializing new backend configuration..."

    cat > backend.tf << EOF
terraform {
  backend "s3" {
    bucket         = "company-terraform-state-${ENVIRONMENT}"
    key            = "infrastructure/terraform.tfstate"
    region         = "us-west-2"
    encrypt        = true
    dynamodb_table = "terraform-state-lock-${ENVIRONMENT}"
  }
}
EOF

    if [[ "$DRY_RUN" == "true" ]]; then
        info "DRY RUN: Would initialize backend with:"
        cat backend.tf
        return 0
    fi

    terraform init -migrate-state -force-copy
}

# Verify state migration
verify_migration() {
    log "Verifying state migration..."

    if [[ "$DRY_RUN" == "true" ]]; then
        info "DRY RUN: Would verify state migration"
        return 0
    fi

    # Run terraform plan to ensure no changes
    if terraform plan -detailed-exitcode > /dev/null; then
        log "✅ State migration successful - no configuration drift detected"
    else
        error "❌ State migration verification failed - configuration drift detected"
        return 1
    fi
}

# Import existing resources
import_resources() {
    log "Importing existing resources..."

    # List of resources to import (customize as needed)
    local resources_to_import=(
        "aws_vpc.main:vpc-12345678"
        "aws_subnet.public[0]:subnet-12345678"
        "aws_subnet.private[0]:subnet-87654321"
        "aws_internet_gateway.main:igw-12345678"
        "aws_route_table.public:rtb-12345678"
    )

    for resource in "${resources_to_import[@]}"; do
        local resource_address="${resource%:*}"
        local resource_id="${resource#*:}"

        if [[ "$DRY_RUN" == "true" ]]; then
            info "DRY RUN: Would import $resource_address with ID $resource_id"
            continue
        fi

        log "Importing $resource_address..."
        if terraform import "$resource_address" "$resource_id"; then
            log "✅ Successfully imported $resource_address"
        else
            error "❌ Failed to import $resource_address"
        fi
    done
}

# Split monolithic state
split_state() {
    log "Splitting monolithic state into components..."

    # Define state splits
    local state_splits=(
        "network:aws_vpc.main,aws_subnet.public,aws_subnet.private,aws_internet_gateway.main"
        "security:aws_security_group.web,aws_security_group.app,aws_security_group.db"
        "database:aws_db_instance.main,aws_db_subnet_group.main"
    )

    for split in "${state_splits[@]}"; do
        local component="${split%:*}"
        local resources="${split#*:}"

        log "Creating state for component: $component"

        # Create component directory
        mkdir -p "components/$component"

        # Move resources to new state
        IFS=',' read -ra RESOURCE_ARRAY <<< "$resources"
        for resource in "${RESOURCE_ARRAY[@]}"; do
            if [[ "$DRY_RUN" == "true" ]]; then
                info "DRY RUN: Would move $resource to $component state"
                continue
            fi

            terraform state mv "$resource" "components/$component/$resource"
        done
    done
}

# Workspace management
manage_workspaces() {
    log "Managing Terraform workspaces..."

    # Create environment-specific workspaces
    local environments=("dev" "staging" "prod")

    for env in "${environments[@]}"; do
        if [[ "$DRY_RUN" == "true" ]]; then
            info "DRY RUN: Would create workspace: $env"
            continue
        fi

        log "Creating workspace: $env"
        terraform workspace new "$env" 2>/dev/null || terraform workspace select "$env"

        if [[ "$env" == "$ENVIRONMENT" ]]; then
            terraform workspace select "$env"
            log "Selected workspace: $env"
        fi
    done
}

# Clean up old state files
cleanup_old_state() {
    log "Cleaning up old state files..."

    if [[ "$DRY_RUN" == "true" ]]; then
        info "DRY RUN: Would remove old state files"
        return 0
    fi

    read -p "Remove local state files? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -f terraform.tfstate terraform.tfstate.backup
        log "Local state files removed"
    else
        warn "Local state files preserved"
    fi
}

# Main execution
main() {
    log "Starting Terraform state migration for environment: $ENVIRONMENT"

    if [[ "$DRY_RUN" == "true" ]]; then
        warn "Running in DRY RUN mode - no changes will be made"
    fi

    # Validation
    if [[ ! -f "terraform.tfstate" ]] && [[ "$OLD_BACKEND" == "local" ]]; then
        error "No local state file found"
        exit 1
    fi

    # Execute migration steps
    backup_state
    init_new_backend
    verify_migration
    manage_workspaces

    # Optional: import existing resources
    read -p "Import existing resources? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        import_resources
    fi

    # Optional: split monolithic state
    read -p "Split state into components? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        split_state
    fi

    cleanup_old_state

    log "✅ State migration completed successfully!"

    # Final verification
    log "Running final validation..."
    if terraform validate && terraform plan -detailed-exitcode > /dev/null; then
        log "✅ All validations passed"
    else
        warn "⚠️  Manual review required"
    fi
}

# Trap for cleanup
cleanup() {
    local exit_code=$?
    if [[ $exit_code -ne 0 ]]; then
        error "Migration failed with exit code: $exit_code"
        if [[ -f ".last-backup-location" ]]; then
            local backup_location
            backup_location=$(cat .last-backup-location)
            error "State backup available at: $backup_location"
        fi
    fi
    exit $exit_code
}

trap cleanup EXIT

# Parse arguments and run
case "${1:-}" in
    -h|--help)
        echo "Usage: $0 <environment> [dry-run]"
        echo "  environment: dev, staging, prod"
        echo "  dry-run: true/false (default: false)"
        exit 0
        ;;
    *)
        main "$@"
        ;;
esac
```

## Enterprise Patterns

### Multi-Account Architecture

#### Cross-Account Resource Sharing
```hcl
# Cross-account IAM role for resource sharing
resource "aws_iam_role" "cross_account_role" {
  name = "${var.project_name}-cross-account-${var.target_account_id}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::${var.target_account_id}:root"
        }
        Condition = {
          StringEquals = {
            "sts:ExternalId" = var.external_id
          }
        }
      }
    ]
  })

  tags = var.common_tags
}

# Cross-account resource sharing policy
resource "aws_iam_policy" "cross_account_policy" {
  name        = "${var.project_name}-cross-account-policy"
  description = "Policy for cross-account resource access"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject"
        ]
        Resource = [
          "${aws_s3_bucket.shared_resources.arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "kms:Decrypt",
          "kms:GenerateDataKey"
        ]
        Resource = [
          aws_kms_key.shared.arn
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = [
          aws_secretsmanager_secret.shared_secrets.arn
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "cross_account" {
  role       = aws_iam_role.cross_account_role.name
  policy_arn = aws_iam_policy.cross_account_policy.arn
}

# Shared S3 bucket with cross-account access
resource "aws_s3_bucket" "shared_resources" {
  bucket = "${var.project_name}-shared-resources-${random_id.bucket_suffix.hex}"

  tags = merge(var.common_tags, {
    Purpose = "cross-account-sharing"
  })
}

resource "aws_s3_bucket_policy" "shared_resources" {
  bucket = aws_s3_bucket.shared_resources.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          AWS = [
            aws_iam_role.cross_account_role.arn,
            "arn:aws:iam::${var.target_account_id}:root"
          ]
        }
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject"
        ]
        Resource = "${aws_s3_bucket.shared_resources.arn}/*"
      },
      {
        Effect = "Allow"
        Principal = {
          AWS = [
            aws_iam_role.cross_account_role.arn,
            "arn:aws:iam::${var.target_account_id}:root"
          ]
        }
        Action = [
          "s3:ListBucket"
        ]
        Resource = aws_s3_bucket.shared_resources.arn
      }
    ]
  })
}

# RAM (Resource Access Manager) resource sharing
resource "aws_ram_resource_share" "shared_subnets" {
  name                      = "${var.project_name}-shared-subnets"
  allow_external_principals = true

  tags = var.common_tags
}

resource "aws_ram_resource_association" "shared_subnets" {
  count = length(aws_subnet.private)

  resource_arn       = aws_subnet.private[count.index].arn
  resource_share_arn = aws_ram_resource_share.shared_subnets.arn
}

resource "aws_ram_principal_association" "shared_subnets" {
  count = length(var.target_account_ids)

  principal          = var.target_account_ids[count.index]
  resource_share_arn = aws_ram_resource_share.shared_subnets.arn
}
```

This comprehensive Terraform Advanced Techniques and Patterns file provides sophisticated infrastructure management approaches that enable teams to implement complex, enterprise-scale deployments with dynamic configurations, advanced state management, and cross-account resource sharing patterns.