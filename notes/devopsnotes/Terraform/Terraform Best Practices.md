## Code Organisation and Structure

### Project Structure

```
terraform-infrastructure/
├── environments/
│   ├── dev/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   ├── outputs.tf
│   │   └── terraform.tfvars
│   ├── staging/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   ├── outputs.tf
│   │   └── terraform.tfvars
│   └── prod/
│       ├── main.tf
│       ├── variables.tf
│       ├── outputs.tf
│       └── terraform.tfvars
├── modules/
│   ├── vpc/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   ├── outputs.tf
│   │   └── README.md
│   ├── security-groups/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   └── ec2/
│       ├── main.tf
│       ├── variables.tf
│       ├── outputs.tf
│       └── user-data.sh
├── shared/
│   ├── backend.tf
│   ├── providers.tf
│   └── versions.tf
├── scripts/
│   ├── deploy.sh
│   ├── validate.sh
│   └── cleanup.sh
├── docs/
│   ├── architecture.md
│   └── runbook.md
├── .gitignore
├── .terraform-version
└── README.md
```

### File Naming Conventions

```hcl
# main.tf - Primary resource definitions
# variables.tf - Input variable declarations
# outputs.tf - Output value declarations
# versions.tf - Provider version constraints
# locals.tf - Local value definitions
# data.tf - Data source definitions
# providers.tf - Provider configurations
```

### Module Structure Best Practices

```hcl
# modules/vpc/main.tf
resource "aws_vpc" "main" {
  cidr_block           = var.cidr_block
  enable_dns_hostnames = var.enable_dns_hostnames
  enable_dns_support   = var.enable_dns_support

  tags = merge(var.tags, {
    Name = var.name
  })
}

resource "aws_internet_gateway" "main" {
  count  = var.create_igw ? 1 : 0
  vpc_id = aws_vpc.main.id

  tags = merge(var.tags, {
    Name = "${var.name}-igw"
  })
}

# modules/vpc/variables.tf
variable "name" {
  description = "Name to be used on all resources as identifier"
  type        = string
}

variable "cidr_block" {
  description = "The CIDR block for the VPC"
  type        = string
  
  validation {
    condition     = can(cidrhost(var.cidr_block, 0))
    error_message = "The cidr_block must be a valid CIDR block."
  }
}

variable "enable_dns_hostnames" {
  description = "Should be true to enable DNS hostnames in the VPC"
  type        = bool
  default     = true
}

variable "tags" {
  description = "A map of tags to assign to the resource"
  type        = map(string)
  default     = {}
}

# modules/vpc/outputs.tf
output "vpc_id" {
  description = "ID of the VPC"
  value       = aws_vpc.main.id
}

output "vpc_cidr_block" {
  description = "The CIDR block of the VPC"
  value       = aws_vpc.main.cidr_block
}

output "internet_gateway_id" {
  description = "The ID of the Internet Gateway"
  value       = try(aws_internet_gateway.main[0].id, null)
}
```

## Variable Management and Configuration

### Variable Declaration Best Practices

```hcl
# Good: Descriptive with validation
variable "instance_type" {
  description = "EC2 instance type for web servers"
  type        = string
  default     = "t3.micro"
  
  validation {
    condition = contains([
      "t3.micro", "t3.small", "t3.medium", "t3.large"
    ], var.instance_type)
    error_message = "Instance type must be a valid t3 instance type."
  }
}

# Good: Complex object with defaults
variable "database_config" {
  description = "Database configuration settings"
  type = object({
    engine         = string
    engine_version = string
    instance_class = string
    allocated_storage = number
    backup_retention_period = optional(number, 7)
    backup_window = optional(string, "03:00-04:00")
    maintenance_window = optional(string, "sun:04:00-sun:05:00")
  })
  
  validation {
    condition = contains([
      "mysql", "postgres", "mariadb"
    ], var.database_config.engine)
    error_message = "Database engine must be mysql, postgres, or mariadb."
  }
}

# Good: Environment-specific defaults
variable "scaling_config" {
  description = "Auto scaling configuration"
  type = object({
    min_size         = number
    max_size         = number
    desired_capacity = number
  })
  
  default = {
    min_size         = 1
    max_size         = 3
    desired_capacity = 2
  }
}
```

### Environment Configuration

```hcl
# environments/prod/terraform.tfvars
environment = "production"
region      = "us-east-1"

# High availability setup
availability_zones = ["us-east-1a", "us-east-1b", "us-east-1c"]

# Production sizing
instance_type = "t3.large"
scaling_config = {
  min_size         = 3
  max_size         = 10
  desired_capacity = 5
}

# Database configuration
database_config = {
  engine         = "postgres"
  engine_version = "14.9"
  instance_class = "db.r5.xlarge"
  allocated_storage = 100
  backup_retention_period = 30
  backup_window = "03:00-04:00"
  maintenance_window = "sun:04:00-sun:05:00"
}

# Security and compliance
enable_encryption = true
enable_logging    = true
enable_monitoring = true

# Cost optimization
enable_spot_instances = false
```

## State Management Best Practices

### Remote State Configuration

```hcl
# shared/backend.tf
terraform {
  backend "s3" {
    bucket         = "my-company-terraform-state"
    key            = "environments/${var.environment}/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-state-locks"
    
    # Workspace-specific state
    workspace_key_prefix = "workspaces"
  }
}

# State bucket configuration (separate Terraform configuration)
resource "aws_s3_bucket" "terraform_state" {
  bucket = "my-company-terraform-state"
  
  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_s3_bucket_versioning" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_dynamodb_table" "terraform_locks" {
  name         = "terraform-state-locks"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "LockID"

  attribute {
    name = "LockID"
    type = "S"
  }
}
```

### State Management Commands

```bash
# State backup before major changes
terraform state pull > backup-$(date +%Y%m%d-%H%M%S).tfstate

# State manipulation best practices
terraform state list
terraform state show aws_instance.web
terraform import aws_instance.existing i-1234567890abcdef0

# Workspace isolation
terraform workspace new production
terraform workspace select production
```

## Security Best Practices

### Sensitive Data Handling

```hcl
# Use sensitive variables
variable "database_password" {
  description = "Database admin password"
  type        = string
  sensitive   = true
}

# Mark outputs as sensitive
output "database_password" {
  description = "Database password"
  value       = random_password.db_password.result
  sensitive   = true
}

# Use AWS Secrets Manager
resource "aws_secretsmanager_secret" "db_password" {
  name                    = "${var.project}-${var.environment}-db-password"
  description             = "Database password for ${var.project}"
  recovery_window_in_days = 7
}

resource "aws_secretsmanager_secret_version" "db_password" {
  secret_id     = aws_secretsmanager_secret.db_password.id
  secret_string = random_password.db_password.result
}

# Reference secrets in resources
resource "aws_db_instance" "main" {
  identifier     = "${var.project}-${var.environment}"
  engine         = "postgres"
  engine_version = "14.9"
  instance_class = "db.t3.micro"
  
  manage_master_user_password = true
  master_username            = "dbadmin"
  
  # Don't store password in state
  # manage_master_user_password handles this automatically
}
```

### Access Control and Permissions

```hcl
# Least privilege IAM policies
data "aws_iam_policy_document" "ec2_assume_role_policy" {
  statement {
    actions = ["sts:AssumeRole"]
    
    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "ec2_role" {
  name               = "${var.project}-${var.environment}-ec2-role"
  assume_role_policy = data.aws_iam_policy_document.ec2_assume_role_policy.json
}

data "aws_iam_policy_document" "ec2_policy" {
  statement {
    sid    = "S3Access"
    effect = "Allow"
    actions = [
      "s3:GetObject",
      "s3:PutObject"
    ]
    resources = [
      "${aws_s3_bucket.app_data.arn}/*"
    ]
  }
  
  statement {
    sid    = "SecretsManagerAccess"
    effect = "Allow"
    actions = [
      "secretsmanager:GetSecretValue"
    ]
    resources = [
      aws_secretsmanager_secret.db_password.arn
    ]
  }
}

resource "aws_iam_role_policy" "ec2_policy" {
  name   = "${var.project}-${var.environment}-ec2-policy"
  role   = aws_iam_role.ec2_role.id
  policy = data.aws_iam_policy_document.ec2_policy.json
}
```

### Security Group Best Practices

```hcl
# Specific, descriptive security groups
resource "aws_security_group" "web_servers" {
  name_prefix = "${var.project}-${var.environment}-web-"
  description = "Security group for ${var.project} web servers"
  vpc_id      = var.vpc_id

  # Explicit ingress rules
  ingress {
    description = "HTTP from ALB"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr_block]
  }

  ingress {
    description = "HTTPS from ALB"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr_block]
  }

  # Restrictive egress
  egress {
    description = "HTTPS to internet"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "Database access"
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = [var.database_subnet_cidr]
  }

  lifecycle {
    create_before_destroy = true
  }

  tags = merge(var.common_tags, {
    Name = "${var.project}-${var.environment}-web-sg"
  })
}
```

## Performance and Efficiency

### Resource Optimization

```hcl
# Use lifecycle rules appropriately
resource "aws_instance" "web" {
  count                  = var.instance_count
  ami                    = data.aws_ami.app.id
  instance_type          = var.instance_type
  subnet_id              = var.subnet_ids[count.index % length(var.subnet_ids)]
  vpc_security_group_ids = [aws_security_group.web_servers.id]

  # Prevent unnecessary replacements
  lifecycle {
    create_before_destroy = true
    ignore_changes = [
      ami,  # Ignore AMI updates to prevent replacement
      user_data  # Handle user data updates gracefully
    ]
  }

  tags = merge(var.common_tags, {
    Name = "${var.project}-${var.environment}-web-${count.index + 1}"
  })
}

# Use data sources efficiently
data "aws_ami" "app" {
  most_recent = true
  owners      = ["self"]

  filter {
    name   = "name"
    values = ["${var.project}-app-*"]
  }

  filter {
    name   = "state"
    values = ["available"]
  }
}
```

### Efficient State Management

```hcl
# Use depends_on sparingly and explicitly
resource "aws_instance" "web" {
  # ... configuration ...
  
  # Only use depends_on when Terraform can't detect dependency
  depends_on = [
    aws_internet_gateway.main,
    aws_security_group.web_servers
  ]
}

# Prefer implicit dependencies
resource "aws_instance" "web" {
  subnet_id              = aws_subnet.public[0].id  # Implicit dependency
  vpc_security_group_ids = [aws_security_group.web.id]  # Implicit dependency
}
```

## Error Handling and Validation

### Comprehensive Validation

```hcl
variable "availability_zones" {
  description = "List of availability zones"
  type        = list(string)
  
  validation {
    condition     = length(var.availability_zones) >= 2
    error_message = "At least 2 availability zones must be provided for high availability."
  }
  
  validation {
    condition = alltrue([
      for az in var.availability_zones : can(regex("^[a-z]{2}-[a-z]+-[0-9][a-z]$", az))
    ])
    error_message = "All availability zones must be valid AWS AZ format (e.g., us-east-1a)."
  }
}

variable "instance_types" {
  description = "Map of instance types for different components"
  type = map(object({
    instance_type = string
    min_size      = number
    max_size      = number
  }))
  
  validation {
    condition = alltrue([
      for component, config in var.instance_types : 
      config.min_size <= config.max_size && config.min_size >= 0
    ])
    error_message = "Min size must be less than or equal to max size and greater than or equal to 0."
  }
}
```

### Error Prevention Patterns

```hcl
# Use try() for graceful error handling
locals {
  # Safe property access
  database_config = try(var.services.database, {
    engine   = "postgres"
    version  = "14.9"
    size     = "small"
  })
  
  # Safe type conversion
  instance_count = try(tonumber(var.instance_count_string), 1)
  
  # Multiple fallback options
  app_domain = coalesce(
    var.custom_domain,
    try(aws_lb.main.dns_name, null),
    "localhost"
  )
}

# Conditional resource creation
resource "aws_cloudwatch_log_group" "app" {
  count             = var.enable_logging ? 1 : 0
  name              = "/aws/ec2/${var.project}-${var.environment}"
  retention_in_days = var.log_retention_days
}

# Safe resource references
resource "aws_instance" "web" {
  # ... other configuration ...
  
  user_data = var.enable_logging ? templatefile("${path.module}/user-data-with-logging.sh", {
    log_group_name = try(aws_cloudwatch_log_group.app[0].name, "")
  }) : file("${path.module}/user-data-basic.sh")
}
```

## Documentation and Maintainability

### Self-Documenting Code

```hcl
# Clear, descriptive resource names
resource "aws_security_group" "web_servers_alb_access" {
  name_prefix = "${var.project}-${var.environment}-web-alb-access-"
  description = "Allows ALB to access web servers on ports 80 and 443"
  vpc_id      = var.vpc_id
}

# Comprehensive variable documentation
variable "backup_configuration" {
  description = <<-EOT
    Backup configuration for RDS instances.
    
    backup_retention_period: Number of days to retain automated backups (1-35)
    backup_window: Daily time range during which automated backups are created
    delete_automated_backups: Whether to remove automated backups immediately when the DB instance is deleted
    skip_final_snapshot: Whether to skip the final DB snapshot when the DB instance is deleted
    final_snapshot_identifier: Name of the final DB snapshot when this DB instance is deleted
  EOT
  
  type = object({
    backup_retention_period     = number
    backup_window              = string
    delete_automated_backups   = bool
    skip_final_snapshot        = bool
    final_snapshot_identifier  = string
  })
  
  default = {
    backup_retention_period     = 7
    backup_window              = "03:00-04:00"
    delete_automated_backups   = true
    skip_final_snapshot        = false
    final_snapshot_identifier  = null
  }
}

# Detailed output descriptions
output "application_endpoints" {
  description = <<-EOT
    Application endpoints for different environments:
    - web_url: Public web application URL
    - api_url: API endpoint URL  
    - admin_url: Admin interface URL (if enabled)
    - health_check_url: Health check endpoint for monitoring
  EOT
  
  value = {
    web_url         = "https://${aws_lb.main.dns_name}"
    api_url         = "https://${aws_lb.main.dns_name}/api"
    admin_url       = var.enable_admin ? "https://${aws_lb.main.dns_name}/admin" : null
    health_check_url = "https://${aws_lb.main.dns_name}/health"
  }
}
```

### README Documentation

````markdown
# Infrastructure Module

## Overview
This module provisions a highly available web application infrastructure on AWS.

## Architecture
- VPC with public and private subnets across multiple AZs
- Application Load Balancer for traffic distribution
- Auto Scaling Group for web servers
- RDS PostgreSQL database with read replicas
- CloudWatch monitoring and alerting

## Usage
```hcl
module "infrastructure" {
  source = "./modules/infrastructure"
  
  project     = "myapp"
  environment = "production"
  
  vpc_cidr = "10.0.0.0/16"
  availability_zones = ["us-east-1a", "us-east-1b", "us-east-1c"]
  
  instance_type = "t3.large"
  min_size      = 3
  max_size      = 10
  
  database_config = {
    engine         = "postgres"
    engine_version = "14.9"
    instance_class = "db.r5.large"
  }
}
````

## Requirements

- Terraform >= 1.0
- AWS Provider >= 5.0
- Authenticated AWS CLI

## Inputs

|Name|Description|Type|Default|Required|
|---|---|---|---|---|
|project|Project name used for resource naming|string|-|yes|
|environment|Environment name (dev/staging/prod)|string|-|yes|
|vpc_cidr|CIDR block for VPC|string|"10.0.0.0/16"|no|

## Outputs

|Name|Description|
|---|---|
|vpc_id|ID of the created VPC|
|load_balancer_dns|DNS name of the load balancer|
|database_endpoint|RDS database endpoint|

````

## Testing and Quality Assurance

### Automated Testing
```bash
#!/bin/bash
# scripts/validate.sh

set -e

echo "🔍 Running Terraform validation tests..."

# Format check
echo "Checking Terraform formatting..."
terraform fmt -check -recursive -diff

# Validation
echo "Validating configuration..."
terraform validate

# Security scanning with tfsec
if command -v tfsec &> /dev/null; then
    echo "Running security scan..."
    tfsec .
fi

# Cost estimation with Infracost
if command -v infracost &> /dev/null; then
    echo "Generating cost estimate..."
    infracost breakdown --path .
fi

# Policy validation with OPA/Conftest
if command -v conftest &> /dev/null; then
    echo "Running policy validation..."
    conftest verify --policy policies/ .
fi

echo "✅ All validation tests passed!"
````

### Integration Testing

```bash
#!/bin/bash
# scripts/integration-test.sh

set -e

ENVIRONMENT="test-$(date +%s)"

echo "🧪 Running integration tests for environment: $ENVIRONMENT"

# Deploy test environment
terraform workspace new $ENVIRONMENT
terraform init
terraform plan -var="environment=$ENVIRONMENT" -out=test.tfplan
terraform apply test.tfplan

# Run application tests
echo "Testing application endpoints..."
LOAD_BALANCER_DNS=$(terraform output -raw load_balancer_dns)

# Health check
curl -f "https://$LOAD_BALANCER_DNS/health" || exit 1

# API test
curl -f "https://$LOAD_BALANCER_DNS/api/status" || exit 1

echo "✅ Integration tests passed!"

# Cleanup
echo "🧹 Cleaning up test environment..."
terraform destroy -auto-approve -var="environment=$ENVIRONMENT"
terraform workspace select default
terraform workspace delete $ENVIRONMENT

echo "✅ Test environment cleaned up!"
```

## Monitoring and Observability

### Comprehensive Monitoring Setup

```hcl
# CloudWatch dashboards
resource "aws_cloudwatch_dashboard" "main" {
  dashboard_name = "${var.project}-${var.environment}-overview"

  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        width  = 12
        height = 6
        properties = {
          metrics = [
            ["AWS/ApplicationELB", "RequestCount", "LoadBalancer", aws_lb.main.arn_suffix],
            ["AWS/ApplicationELB", "TargetResponseTime", "LoadBalancer", aws_lb.main.arn_suffix],
            ["AWS/ApplicationELB", "HTTPCode_Target_2XX_Count", "LoadBalancer", aws_lb.main.arn_suffix],
            ["AWS/ApplicationELB", "HTTPCode_Target_4XX_Count", "LoadBalancer", aws_lb.main.arn_suffix],
            ["AWS/ApplicationELB", "HTTPCode_Target_5XX_Count", "LoadBalancer", aws_lb.main.arn_suffix]
          ]
          period = 300
          stat   = "Sum"
          region = var.aws_region
          title  = "Load Balancer Metrics"
        }
      }
    ]
  })
}

# Alerts for critical metrics
resource "aws_cloudwatch_metric_alarm" "high_error_rate" {
  alarm_name          = "${var.project}-${var.environment}-high-error-rate"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "HTTPCode_Target_5XX_Count"
  namespace           = "AWS/ApplicationELB"
  period              = "300"
  statistic           = "Sum"
  threshold           = "10"
  alarm_description   = "This metric monitors 5xx error rate"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    LoadBalancer = aws_lb.main.arn_suffix
  }
}
```