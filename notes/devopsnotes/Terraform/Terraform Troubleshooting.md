## State-Related Issues

### State Lock Errors

```bash
# Error: Error acquiring the state lock
Error: Error acquiring the state lock

Error message: ConditionalCheckFailedException: The conditional request failed
Lock Info:
  ID:        12345678-1234-1234-1234-123456789012
  Path:      s3://bucket/path/terraform.tfstate
  Operation: OperationTypePlan
  Who:       user@hostname
  Version:   1.6.0
  Created:   2024-01-15 10:30:00.123456 +0000 UTC
  Info:

# Solutions:
# 1. Wait for lock to expire (if process is still running)
# 2. Force unlock (if process is terminated)
terraform force-unlock 12345678-1234-1234-1234-123456789012

# 3. Verify no other Terraform processes are running
ps aux | grep terraform

# 4. Check DynamoDB table for stuck locks
aws dynamodb scan --table-name terraform-state-locks
```

### State Drift Issues

```bash
# Error: Resource not found in state but exists in cloud
# Solution: Import existing resource
terraform import aws_instance.web i-1234567890abcdef0

# Error: Resource exists in state but not in cloud
# Solution: Remove from state
terraform state rm aws_instance.missing

# Error: Resource configuration drift
# Solution: Refresh state and plan
terraform refresh
terraform plan

# Force replace resource if corrupted
terraform apply -replace=aws_instance.web
```

### State File Corruption

```bash
# Backup current state
terraform state pull > backup-$(date +%Y%m%d-%H%M%S).tfstate

# Restore from backup
terraform state push backup-20240115-103000.tfstate

# Recover from S3 versioning
aws s3api list-object-versions --bucket my-terraform-state --prefix path/terraform.tfstate
aws s3api get-object --bucket my-terraform-state --key path/terraform.tfstate --version-id VERSION_ID terraform.tfstate
terraform state push terraform.tfstate
```

## Provider and Authentication Issues

### AWS Provider Authentication

```bash
# Error: NoCredentialsError
Error: NoCredentialsError: Unable to locate credentials

# Solutions:
# 1. Configure AWS credentials
aws configure
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_REGION=us-east-1

# 2. Use IAM role
export AWS_PROFILE=your_profile

# 3. Debug authentication
aws sts get-caller-identity
terraform console
> data.aws_caller_identity.current

# 4. Provider configuration issues
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
  
  # Explicit configuration if needed
  profile = var.aws_profile
  
  default_tags {
    tags = var.common_tags
  }
}
```

### Provider Version Conflicts

```bash
# Error: Terraform version constraint not met
Error: Terraform version constraint not met

# Check versions
terraform version
terraform providers

# Update provider versions
terraform init -upgrade

# Lock specific versions
terraform {
  required_version = ">= 1.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.31.0"
    }
  }
}

# Clean provider cache
rm -rf .terraform
terraform init
```

## Resource Configuration Errors

### Invalid Resource Arguments

```hcl
# Common configuration errors and fixes

# Error: Invalid instance type
resource "aws_instance" "web" {
  ami           = "ami-12345678"
  instance_type = "t3.invalid"  # Invalid type
}

# Fix: Use valid instance type
resource "aws_instance" "web" {
  ami           = data.aws_ami.latest.id
  instance_type = var.instance_type
  
  # Add validation
  lifecycle {
    precondition {
      condition = contains([
        "t3.micro", "t3.small", "t3.medium", "t3.large"
      ], var.instance_type)
      error_message = "Instance type must be a valid t3 type."
    }
  }
}

# Error: Missing required arguments
resource "aws_security_group" "web" {
  name = "web-sg"
  # Missing vpc_id
}

# Fix: Add required arguments
resource "aws_security_group" "web" {
  name   = "web-sg"
  vpc_id = var.vpc_id  # Required argument
}
```

### Dependency Issues

```bash
# Error: Resource depends on resource that will be destroyed
Error: Resource "aws_instance.web" depends on resource "aws_security_group.web" that will be destroyed

# Solutions:
# 1. Use lifecycle rules
resource "aws_security_group" "web" {
  name_prefix = "web-sg-"
  vpc_id      = var.vpc_id
  
  lifecycle {
    create_before_destroy = true
  }
}

# 2. Separate the operations
terraform plan -target=aws_security_group.new_web
terraform apply -target=aws_security_group.new_web
terraform plan
terraform apply

# 3. Use moved blocks for resource refactoring
moved {
  from = aws_security_group.web
  to   = aws_security_group.web_servers
}
```

## Validation and Syntax Errors

### Variable Validation Issues

```hcl
# Error: Invalid variable value
variable "environment" {
  description = "Environment name"
  type        = string
  
  validation {
    condition = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be one of: dev, staging, prod."
  }
}

# Error: Type constraint violation
variable "instance_count" {
  description = "Number of instances"
  type        = number
  default     = "2"  # Error: string instead of number
}

# Fix: Correct type
variable "instance_count" {
  description = "Number of instances"
  type        = number
  default     = 2
}
```

### HCL Syntax Errors

```bash
# Error: Invalid HCL syntax
Error: Invalid character

# Common syntax issues:
# 1. Missing quotes around strings
name = web-server  # Error
name = "web-server"  # Correct

# 2. Invalid interpolation syntax
name = "${var.prefix-name}"  # Error: hyphen in variable name
name = "${var.prefix}_name"  # Correct: underscore

# 3. Incorrect block structure
resource aws_instance "web" {  # Error: missing quotes
  # configuration
}

resource "aws_instance" "web" {  # Correct
  # configuration
}

# Debug syntax issues
terraform fmt -check
terraform validate
```

## Module and Configuration Issues

### Module Source Errors

```hcl
# Error: Invalid module source
module "vpc" {
  source = "./modules/vpc"  # Path doesn't exist
}

# Error: Version constraint issues
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"  # Version doesn't exist
}

# Solutions:
# 1. Verify module path
ls -la ./modules/vpc

# 2. Check available versions
terraform init
terraform get -update

# 3. Use specific version
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "5.1.2"
}
```

### Output and Data Source Issues

```hcl
# Error: Invalid output reference
output "instance_ip" {
  value = aws_instance.web.public_ip
  # Error if instance doesn't have public IP
}

# Fix: Handle optional values
output "instance_ip" {
  value = try(aws_instance.web.public_ip, "No public IP")
}

# Error: Data source not found
data "aws_ami" "latest" {
  most_recent = true
  owners      = ["amazon"]
  
  filter {
    name   = "name"
    values = ["amzn2-ami-hvm-*"]
  }
  
  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# Debug data sources
terraform console
> data.aws_ami.latest
```

## Performance and Resource Limit Issues

### Rate Limiting and API Throttling

```bash
# Error: Rate exceeded
Error: Error creating EC2 Instance: RequestLimitExceeded

# Solutions:
# 1. Add delays between resources
resource "time_sleep" "wait_30_seconds" {
  depends_on = [aws_instance.web]
  create_duration = "30s"
}

# 2. Use count with for_each to batch operations
resource "aws_instance" "web" {
  for_each = toset(var.availability_zones)
  
  ami           = data.aws_ami.latest.id
  instance_type = var.instance_type
  subnet_id     = aws_subnet.main[each.key].id
  
  # Stagger creation
  depends_on = [time_sleep.wait_${each.key}]
}

# 3. Adjust parallelism
terraform apply -parallelism=5
```

### Resource Quota Limits

```bash
# Error: Service quota exceeded
Error: Error launching source instance: InstanceLimitExceeded

# Solutions:
# 1. Check current usage
aws ec2 describe-account-attributes --attribute-names supported-platforms
aws service-quotas get-service-quota --service-code ec2 --quota-code L-1216C47A

# 2. Request quota increase
aws service-quotas request-service-quota-increase \
  --service-code ec2 \
  --quota-code L-1216C47A \
  --desired-value 50

# 3. Use different regions or instance types
variable "fallback_regions" {
  default = ["us-east-1", "us-west-2", "eu-west-1"]
}
```

## Network and Security Issues

### VPC and Networking Errors

```hcl
# Error: Invalid CIDR block
resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/8"  # Too broad for AWS
}

# Fix: Use appropriate CIDR
resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true
  
  tags = {
    Name = "main-vpc"
  }
}

# Error: Subnet CIDR conflicts
resource "aws_subnet" "public" {
  count      = 2
  vpc_id     = aws_vpc.main.id
  cidr_block = "10.0.1.0/24"  # Same CIDR for both subnets
}

# Fix: Use different CIDRs
resource "aws_subnet" "public" {
  count             = 2
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.${count.index + 1}.0/24"
  availability_zone = data.aws_availability_zones.available.names[count.index]
}
```

### Security Group Rule Conflicts

```hcl
# Error: Duplicate security group rules
resource "aws_security_group_rule" "ssh" {
  type              = "ingress"
  from_port         = 22
  to_port           = 22
  protocol          = "tcp"
  cidr_blocks       = ["0.0.0.0/0"]
  security_group_id = aws_security_group.web.id
}

resource "aws_security_group_rule" "ssh_duplicate" {
  type              = "ingress"
  from_port         = 22
  to_port           = 22
  protocol          = "tcp"
  cidr_blocks       = ["0.0.0.0/0"]  # Duplicate
  security_group_id = aws_security_group.web.id
}

# Fix: Combine rules or use different approaches
resource "aws_security_group" "web" {
  name   = "web-sg"
  vpc_id = aws_vpc.main.id
  
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
```

## Debugging and Troubleshooting Commands

### Essential Debug Commands

```bash
# Enable detailed logging
export TF_LOG=DEBUG
export TF_LOG_PATH=terraform.log

# Validate configuration
terraform validate

# Check formatting
terraform fmt -check -diff

# Plan with detailed output
terraform plan -out=tfplan
terraform show tfplan

# Show current state
terraform show
terraform state list
terraform state show aws_instance.web

# Graph dependencies
terraform graph | dot -Tpng > graph.png

# Console for testing expressions
terraform console
> var.environment
> local.common_tags

# Refresh and detect drift
terraform plan -detailed-exitcode
# Exit code 0: no changes
# Exit code 1: error
# Exit code 2: changes detected
```

### Recovery and Cleanup

```bash
# Emergency cleanup
terraform destroy -auto-approve

# Selective cleanup
terraform destroy -target=aws_instance.web

# Remove corrupted resources
terraform state rm aws_instance.corrupted

# Import existing resources
terraform import aws_instance.existing i-1234567890abcdef0

# Backup and restore state
terraform state pull > backup.tfstate
terraform state push backup.tfstate

# Reset workspace
rm -rf .terraform
rm terraform.tfstate*
terraform init
```

## Best Practices for Error Prevention

### Code Organization

```hcl
# Use consistent naming conventions
resource "aws_instance" "web_server" {  # snake_case
  name = "web-server"                   # kebab-case for names
}

# Implement proper tagging
locals {
  common_tags = {
    Environment = var.environment
    Project     = var.project_name
    ManagedBy   = "terraform"
    CreatedAt   = timestamp()
  }
}

# Use data sources for dynamic values
data "aws_availability_zones" "available" {
  state = "available"
}

# Implement validation
variable "environment" {
  type = string
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}
```

### State Management

```hcl
# Configure remote state
terraform {
  backend "s3" {
    bucket         = "my-terraform-state"
    key            = "infrastructure/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-state-locks"
  }
}

# Use workspaces for environments
terraform workspace new staging
terraform workspace select prod
```

### Version Pinning

```hcl
terraform {
  required_version = ">= 1.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.31.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.4.0"
    }
  }
}
```
