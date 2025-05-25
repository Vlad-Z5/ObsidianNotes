### Variable Types and Validation

```hcl
# String variable with validation
variable "environment" {
  type        = string
  description = "Environment name"
  
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

# Number variable with constraints
variable "instance_count" {
  type        = number
  description = "Number of instances"
  default     = 1
  
  validation {
    condition     = var.instance_count >= 1 && var.instance_count <= 10
    error_message = "Instance count must be between 1 and 10."
  }
}

# Complex object variable
variable "database_config" {
  type = object({
    engine         = string
    engine_version = string
    instance_class = string
    storage_size   = number
    multi_az       = bool
    backup_retention = number
  })
  
  description = "Database configuration"
  
  validation {
    condition     = var.database_config.storage_size >= 20
    error_message = "Database storage must be at least 20 GB."
  }
}

# Sensitive variable
variable "db_password" {
  type        = string
  description = "Database password"
  sensitive   = true
}
```

### Variable Files

**terraform.tfvars:**

```hcl
environment    = "production"
instance_count = 3
region         = "us-west-2"

common_tags = {
  Environment = "production"
  Owner       = "platform-team"
  Project     = "web-app"
}

database_config = {
  engine           = "mysql"
  engine_version   = "8.0"
  instance_class   = "db.t3.medium"
  storage_size     = 100
  multi_az         = true
  backup_retention = 7
}
```

**dev.tfvars:**

```hcl
environment    = "dev"
instance_count = 1
region         = "us-west-2"

common_tags = {
  Environment = "dev"
  Owner       = "dev-team"
  Project     = "web-app"
}

database_config = {
  engine           = "mysql"
  engine_version   = "8.0"
  instance_class   = "db.t3.micro"
  storage_size     = 20
  multi_az         = false
  backup_retention = 1
}
```

### Outputs

```hcl
# Simple output
output "vpc_id" {
  description = "VPC ID"
  value       = aws_vpc.main.id
}

# Sensitive output
output "database_endpoint" {
  description = "Database endpoint"
  value       = aws_db_instance.main.endpoint
  sensitive   = true
}

# Complex output
output "load_balancer_info" {
  description = "Load balancer information"
  value = {
    dns_name    = aws_lb.main.dns_name
    zone_id     = aws_lb.main.zone_id
    arn         = aws_lb.main.arn
    hosted_zone = aws_lb.main.canonical_hosted_zone_id
  }
}

# Conditional output
output "private_subnet_ids" {
  description = "Private subnet IDs"
  value       = var.create_private_subnets ? aws_subnet.private[*].id : []
}
```
