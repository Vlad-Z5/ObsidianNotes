## Core Commands

### terraform init

Initializes a Terraform working directory by downloading provider plugins, setting up backend configuration, and creating `.terraform` directory structure.

**DevOps Responsibility**: First command run in any new Terraform project or when switching backends.

```bash
# Basic initialization
terraform init

# Initialize with backend reconfiguration
terraform init -reconfigure

# Initialize and upgrade providers
terraform init -upgrade

# Initialize with specific backend config
terraform init -backend-config="bucket=my-terraform-state"
```

**Common Use Cases**:

- Setting up new infrastructure repositories
- Onboarding team members to existing projects
- Switching between different backend configurations
- Updating provider versions

### terraform plan

Creates an execution plan showing what actions Terraform will take to reach the desired state defined in configuration files.

**DevOps Responsibility**: Essential for code review process and change validation before applying infrastructure changes.

```bash
# Basic plan
terraform plan

# Save plan to file for later apply
terraform plan -out=tfplan

# Plan with specific variable file
terraform plan -var-file="prod.tfvars"

# Plan with target resource
terraform plan -target=aws_instance.web

# Plan destroy
terraform plan -destroy
```

**Best Practices**:

- Always run plan before apply in production
- Save plans to files for audit trails
- Use in CI/CD pipelines for automated validation
- Review plans in pull requests

### terraform apply

Applies the changes required to reach the desired state of configuration.

**DevOps Responsibility**: Core deployment command that must be executed with proper approvals and monitoring.

```bash
# Apply with confirmation prompt
terraform apply

# Apply saved plan without prompt
terraform apply tfplan

# Apply with auto-approval (CI/CD)
terraform apply -auto-approve

# Apply specific targets only
terraform apply -target=aws_instance.web
```

**Production Considerations**:

- Implement approval workflows
- Monitor apply operations
- Have rollback plans ready
- Use saved plans for consistency

### terraform destroy

Destroys all resources managed by the Terraform configuration.

**DevOps Responsibility**: Critical for environment cleanup and cost management.

```bash
# Destroy with confirmation
terraform destroy

# Destroy with auto-approval
terraform destroy -auto-approve

# Destroy specific resources
terraform destroy -target=aws_instance.test

# Plan destroy first
terraform plan -destroy
```

**Safety Measures**:

- Use `prevent_destroy` lifecycle rule
- Implement destroy approval processes
- Backup critical data before destruction
- Use separate destroy pipelines

### terraform validate

Validates the configuration files for syntax and internal consistency.

**DevOps Responsibility**: Quality assurance step in development workflow.

```bash
# Validate current directory
terraform validate

# Validate specific directory
terraform validate /path/to/config
```

**Integration Points**:

- Pre-commit hooks
- CI/CD pipeline validation
- Local development workflow
- Code quality gates

### terraform fmt

Formats Terraform configuration files to canonical format and style.

**DevOps Responsibility**: Code consistency and readability maintenance.

```bash
# Format current directory
terraform fmt

# Format recursively
terraform fmt -recursive

# Check formatting without changes
terraform fmt -check

# Show diff of formatting changes
terraform fmt -diff
```

**Automation**:

- Pre-commit hooks integration
- CI/CD formatting checks
- IDE integration
- Team coding standards enforcement

## State Management

### terraform state

Manages Terraform state with various subcommands for advanced state operations.

**DevOps Responsibility**: Critical for state file maintenance and troubleshooting.

```bash
# List all resources in state
terraform state list

# Show detailed resource information
terraform state show aws_instance.web

# Remove resource from state
terraform state rm aws_instance.web

# Move resource in state
terraform state mv aws_instance.web aws_instance.web_server

# Pull remote state
terraform state pull

# Push local state to remote
terraform state push
```

**Common Scenarios**:

- Resource refactoring
- Fixing state inconsistencies
- Resource adoption
- State file recovery

### State File Management

#### terraform.tfstate

Local state file that tracks resource mappings and metadata.

**DevOps Responsibility**: Protect and backup state files, never commit to version control.

**Security Considerations**:

- Contains sensitive data
- Should be stored in secure remote backends
- Access control required
- Encryption at rest and in transit

#### Remote State Backend

Stores state files in remote locations for team collaboration and security.

**S3 Backend Configuration**:

```hcl
terraform {
  backend "s3" {
    bucket         = "my-terraform-state"
    key            = "prod/terraform.tfstate"
    region         = "us-west-2"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
```

#### Collection Functions

```hcl
locals {
  # List operations
  instance_types = ["t3.micro", "t3.small", "t3.medium"]
  selected_type  = element(local.instance_types, 1) # t3.small
  
  # Map operations
  environments = {
    dev  = "development"
    stg  = "staging"
    prod = "production"
  }
  
  env_full_name = lookup(local.environments, var.env, "unknown")
  
  # Merge maps
  base_tags = {
    Terraform = "true"
    Owner     = "devops"
  }
  
  resource_tags = merge(local.base_tags, {
    Environment = var.environment
    Name        = var.resource_name
  })
  
  # Conditional expressions
  instance_type = var.environment == "prod" ? "t3.large" : "t3.micro"
  
  # For expressions
  subnet_tags = {
    for idx, subnet in aws_subnet.private : 
    subnet.id => {
      Name = "private-subnet-${idx + 1}"
      Type = "private"
    }
  }
}
```

#### File Functions

```hcl
locals {
  # Read file contents
  ssh_public_key = file("~/.ssh/id_rsa.pub")
  
  # Template file with variables
  user_data = templatefile("${path.module}/templates/user_data.sh", {
    app_name    = var.app_name
    environment = var.environment
    region      = var.region
  })
  
  # YAML decode
  config = yamldecode(file("${path.module}/config.yaml"))
  
  # Base64 encode
  encoded_script = base64encode(file("${path.module}/scripts/init.sh"))
}
```

### Conditional Expressions and Logic

```hcl
# Ternary operator
resource "aws_instance" "web" {
  count = var.create_instance ? 1 : 0
  
  ami           = var.ami_id
  instance_type = var.environment == "production" ? "t3.large" : "t3.micro"
  
  # Complex conditional
  root_block_device {
    volume_size = var.environment == "production" ? (
      var.high_performance ? 100 : 50
    ) : 20
  }
}

# Conditional resource creation
resource "aws_cloudwatch_log_group" "app_logs" {
  count = var.enable_logging ? 1 : 0
  
  name              = "/aws/application/${var.app_name}"
  retention_in_days = var.log_retention_days
}
```

### Error Handling and Validation

```hcl
variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  
  validation {
    condition = can(regex("^[tm][0-9]", var.instance_type))
    error_message = "Instance type must start with 't' or 'm' followed by a number."
  }
}

variable "cidr_block" {
  description = "CIDR block for VPC"
  type        = string
  
  validation {
    condition     = can(cidrhost(var.cidr_block, 0))
    error_message = "CIDR block must be a valid IPv4 CIDR."
  }
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  
  validation {
    condition     = contains(keys(var.tags), "Environment")
    error_message = "Tags must include an Environment key."
  }
}
```

### Terraform Graph and Visualization

```bash
# Generate dependency graph
terraform graph | dot -Tsvg > graph.svg

# Generate graph for specific resources
terraform graph -type=plan | dot -Tpng > plan_graph.png

# Generate graph with modules expanded
terraform graph -draw-cycles | dot -Tpdf > dependency_graph.pdf
```

**Graph Analysis Use Cases**:

- Identify circular dependencies
- Visualize resource relationships
- Optimize resource creation order
- Debug complex configurations

### terraform show

Display human-readable output from state or plan files.

```bash
# Show current state
terraform show

# Show specific resource
terraform show aws_instance.web

# Show plan file
terraform show tfplan

# Show in JSON format
terraform show -json terraform.tfstate
```

### terraform refresh

Update state file with real-world resource status.

```bash
# Refresh state
terraform refresh

# Refresh with variable file
terraform refresh -var-file="prod.tfvars"

# Refresh specific resource
terraform refresh -target=aws_instance.web
```

**Note**: `terraform refresh` is deprecated in favor of `terraform plan -refresh-only` and `terraform apply -refresh-only`.

## AWS Resources

### Core Infrastructure

#### VPC and Networking

```hcl
resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true
  
  tags = merge(local.common_tags, {
    Name = "${var.environment}-vpc"
  })
}

resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id
  
  tags = merge(local.common_tags, {
    Name = "${var.environment}-igw"
  })
}

resource "aws_nat_gateway" "main" {
  count = length(var.availability_zones)
  
  allocation_id = aws_eip.nat[count.index].id
  subnet_id     = aws_subnet.public[count.index].id
  
  tags = merge(local.common_tags, {
    Name = "${var.environment}-nat-${count.index + 1}"
  })
  
  depends_on = [aws_internet_gateway.main]
}

resource "aws_eip" "nat" {
  count = length(var.availability_zones)
  
  domain = "vpc"
  
  tags = merge(local.common_tags, {
    Name = "${var.environment}-eip-${count.index + 1}"
  })
}

resource "aws_subnet" "public" {
  count = length(var.availability_zones)
  
  vpc_id                  = aws_vpc.main.id
  cidr_block              = cidrsubnet(var.vpc_cidr, 8, count.index + 1)
  availability_zone       = var.availability_zones[count.index]
  map_public_ip_on_launch = true
  
  tags = merge(local.common_tags, {
    Name = "${var.environment}-public-${count.index + 1}"
    Type = "public"
  })
}

resource "aws_subnet" "private" {
  count = length(var.availability_zones)
  
  vpc_id            = aws_vpc.main.id
  cidr_block        = cidrsubnet(var.vpc_cidr, 8, count.index + 101)
  availability_zone = var.availability_zones[count.index]
  
  tags = merge(local.common_tags, {
    Name = "${var.environment}-private-${count.index + 1}"
    Type = "private"
  })
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id
  
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }
  
  tags = merge(local.common_tags, {
    Name = "${var.environment}-public-rt"
  })
}

resource "aws_route_table" "private" {
  count = length(var.availability_zones)
  
  vpc_id = aws_vpc.main.id
  
  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.main[count.index].id
  }
  
  tags = merge(local.common_tags, {
    Name = "${var.environment}-private-rt-${count.index + 1}"
  })
}

resource "aws_route_table_association" "public" {
  count = length(aws_subnet.public)
  
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table_association" "private" {
  count = length(aws_subnet.private)
  
  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private[count.index].id
}
```

#### Security Groups

```hcl
resource "aws_security_group" "web" {
  name_prefix = "${var.environment}-web-"
  vpc_id      = aws_vpc.main.id
  description = "Security group for web servers"
  
  ingress {
    description = "HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  ingress {
    description = "HTTPS"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  ingress {
    description     = "SSH"
    from_port       = 22
    to_port         = 22
    protocol        = "tcp"
    security_groups = [aws_security_group.bastion.id]
  }
  
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  tags = merge(local.common_tags, {
    Name = "${var.environment}-web-sg"
  })
  
  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_security_group" "alb" {
  name_prefix = "${var.environment}-alb-"
  vpc_id      = aws_vpc.main.id
  description = "Security group for Application Load Balancer"
  
  dynamic "ingress" {
    for_each = var.alb_ingress_ports
    content {
      from_port   = ingress.value
      to_port     = ingress.value
      protocol    = "tcp"
      cidr_blocks = ["0.0.0.0/0"]
    }
  }
  
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  tags = merge(local.common_tags, {
    Name = "${var.environment}-alb-sg"
  })
}
```

#### EC2 Instances

```hcl
data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"]
  
  filter {
    name   = "name"
    values = ["amzn2-ami-hvm-*-x86_64-gp2"]
  }
  
  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

resource "aws_key_pair" "main" {
  key_name   = "${var.environment}-key"
  public_key = file(var.public_key_path)
  
  tags = local.common_tags
}

resource "aws_launch_template" "web" {
  name_prefix   = "${var.environment}-web-"
  image_id      = data.aws_ami.amazon_linux.id
  instance_type = var.instance_type
  key_name      = aws_key_pair.main.key_name
  
  vpc_security_group_ids = [aws_security_group.web.id]
  
  user_data = base64encode(templatefile("${path.module}/templates/user_data.sh", {
    app_name    = var.app_name
    environment = var.environment
  }))
  
  block_device_mappings {
    device_name = "/dev/xvda"
    ebs {
      volume_size = var.root_volume_size
      volume_type = "gp3"
      encrypted   = true
    }
  }
  
  iam_instance_profile {
    name = aws_iam_instance_profile.web.name
  }
  
  tag_specifications {
    resource_type = "instance"
    tags = merge(local.common_tags, {
      Name = "${var.environment}-web"
    })
  }
  
  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_autoscaling_group" "web" {
  name                = "${var.environment}-web-asg"
  vpc_zone_identifier = aws_subnet.private[*].id
  target_group_arns   = [aws_lb_target_group.web.arn]
  health_check_type   = "ELB"
  
  min_size         = var.min_size
  max_size         = var.max_size
  desired_capacity = var.desired_capacity
  
  launch_template {
    id      = aws_launch_template.web.id
    version = "$Latest"
  }
  
  dynamic "tag" {
    for_each = local.common_tags
    content {
      key                 = tag.key
      value               = tag.value
      propagate_at_launch = true
    }
  }
  
  tag {
    key                 = "Name"
    value               = "${var.environment}-web-asg"
    propagate_at_launch = false
  }
  
  instance_refresh {
    strategy = "Rolling"
    preferences {
      min_healthy_percentage = 50
    }
  }
}
```

#### Application Load Balancer

```hcl
resource "aws_lb" "main" {
  name               = "${var.environment}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = aws_subnet.public[*].id
  
  enable_deletion_protection = var.environment == "production"
  
  access_logs {
    bucket  = aws_s3_bucket.alb_logs.id
    prefix  = "alb-logs"
    enabled = true
  }
  
  tags = merge(local.common_tags, {
    Name = "${var.environment}-alb"
  })
}

resource "aws_lb_target_group" "web" {
  name     = "${var.environment}-web-tg"
  port     = 80
  protocol = "HTTP"
  vpc_id   = aws_vpc.main.id
  
  health_check {
    enabled             = true
    healthy_threshold   = 2
    interval            = 30
    matcher             = "200"
    path                = "/health"
    port                = "traffic-port"
    protocol            = "HTTP"
    timeout             = 5
    unhealthy_threshold = 2
  }
  
  tags = merge(local.common_tags, {
    Name = "${var.environment}-web-tg"
  })
}

resource "aws_lb_listener" "web" {
  load_balancer_arn = aws_lb.main.arn
  port              = "443"
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS-1-2-2017-01"
  certificate_arn   = aws_acm_certificate.main.arn
  
  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.web.arn
  }
}

resource "aws_lb_listener" "web_redirect" {
  load_balancer_arn = aws_lb.main.arn
  port              = "80"
  protocol          = "HTTP"
  
  default_action {
    type = "redirect"
    
    redirect {
      port        = "443"
      protocol    = "HTTPS"
      status_code = "HTTP_301"
    }
  }
}
```

#### RDS Database

```hcl
resource "aws_db_subnet_group" "main" {
  name       = "${var.environment}-db-subnet-group"
  subnet_ids = aws_subnet.private[*].id
  
  tags = merge(local.common_tags, {
    Name = "${var.environment}-db-subnet-group"
  })
}

resource "aws_security_group" "rds" {
  name_prefix = "${var.environment}-rds-"
  vpc_id      = aws_vpc.main.id
  description = "Security group for RDS database"
  
  ingress {
    from_port       = 3306
    to_port         = 3306
    protocol        = "tcp"
    security_groups = [aws_security_group.web.id]
  }
  
  tags = merge(local.common_tags, {
    Name = "${var.environment}-rds-sg"
  })
}

resource "aws_db_instance" "main" {
  identifier = "${var.environment}-database"
  
  allocated_storage     = var.db_allocated_storage
  max_allocated_storage = var.db_max_allocated_storage
  storage_type          = "gp2"
  storage_encrypted     = true
  
  engine         = "mysql"
  engine_version = "8.0"
  instance_class = var.db_instance_class
  
  db_name  = var.db_name
  username = var.db_username
  password = var.db_password
  
  vpc_security_group_ids = [aws_security_group.rds.id]
  db_subnet_group_name   = aws_db_subnet_group.main.name
  
  backup_retention_period = var.environment == "production" ? 7 : 1
  backup_window          = "03:00-04:00"
  maintenance_window     = "Sun:04:00-Sun:05:00"
  
  skip_final_snapshot       = var.environment != "production"
  final_snapshot_identifier = var.environment == "production" ? "${var.environment}-db-final-snapshot-${formatdate("YYYY-MM-DD-hhmm", timestamp())}" : null
  
  tags = merge(local.common_tags, {
    Name = "${var.environment}-database"
  })
}
```

### Storage and Content Delivery

#### S3 Buckets

```hcl
resource "aws_s3_bucket" "app_data" {
  bucket = "${var.environment}-${var.app_name}-data-${random_id.bucket_suffix.hex}"
  
  tags = merge(local.common_tags, {
    Name        = "${var.environment}-app-data"
    Purpose     = "Application Data Storage"
  })
}

resource "aws_s3_bucket_versioning" "app_data" {
  bucket = aws_s3_bucket.app_data.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_encryption" "app_data" {
  bucket = aws_s3_bucket.app_data.id
  
  server_side_encryption_configuration {
    rule {
      apply_server_side_encryption_by_default {
        kms_master_key_id = aws_kms_key.s3.arn
        sse_algorithm     = "aws:kms"
      }
    }
  }
}

resource "aws_s3_bucket_public_access_block" "app_data" {
  bucket = aws_s3_bucket.app_data.id
  
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_lifecycle_configuration" "app_data" {
  bucket = aws_s3_bucket.app_data.id
  
  rule {
    id     = "transition_to_ia"
    status = "Enabled"
    
    transition {
      days          = 30
      storage_class = "STANDARD_IA"
    }
    
    transition {
      days          = 90
      storage_class = "GLACIER"
    }
    
    expiration {
      days = 365
    }
  }
}

resource "random_id" "bucket_suffix" {
  byte_length = 4
}
```

#### CloudFront Distribution

```hcl
resource "aws_cloudfront_distribution" "main" {
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
  comment             = "${var.environment} CloudFront Distribution"
  default_root_object = "index.html"
  
  aliases = var.domain_names
  
  default_cache_behavior {
    allowed_methods  = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "ALB-${aws_lb.main.name}"
    
    forwarded_values {
      query_string = false
      
      cookies {
        forward = "none"
      }
    }
    
    viewer_protocol_policy = "redirect-to-https"
    min_ttl                = 0
    default_ttl            = 3600
    max_ttl                = 86400
  }
  
  price_class = var.cloudfront_price_class
  
  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }
  
  viewer_certificate {
    acm_certificate_arn = aws_acm_certificate.main.arn
    ssl_support_method  = "sni-only"
  }
  
  tags = merge(local.common_tags, {
    Name = "${var.environment}-cloudfront"
  })
}
```

### Security and Access Management

#### IAM Roles and Policies

```hcl
resource "aws_iam_role" "web_instance" {
  name = "${var.environment}-web-instance-role"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })
  
  tags = local.common_tags
}

resource "aws_iam_policy" "web_instance" {
  name        = "${var.environment}-web-instance-policy"
  description = "Policy for web instance access to AWS services"
  
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
        Resource = "${aws_s3_bucket.app_data.arn}/*"
      },
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = aws_secretsmanager_secret.app_secrets.arn
      },
      {
        Effect = "Allow"
        Action = [
          "ssm:GetParameters",
          "ssm:GetParameter",
          "ssm:GetParametersByPath"
        ]
        Resource = "arn:aws:ssm:${var.region}:${data.aws_caller_identity.current.account_id}:parameter/${var.environment}/*"
      }
    ]
  })
  
  tags = local.common_tags
}

resource "aws_iam_role_policy_attachment" "web_instance" {
  role       = aws_iam_role.web_instance.name
  policy_arn = aws_iam_policy.web_instance.arn
}

resource "aws_iam_instance_profile" "web" {
  name = "${var.environment}-web-instance-profile"
  role = aws_iam_role.web_instance.name
  
  tags = local.common_tags
}
```

#### KMS Key Management

```hcl
resource "aws_kms_key" "main" {
  description             = "${var.environment} main encryption key"
  deletion_window_in_days = var.environment == "production" ? 30 : 7
  
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
      }
    ]
  })
  
  tags = merge(local.common_tags, {
    Name = "${var.environment}-main-key"
  })
}

resource "aws_kms_alias" "main" {
  name          = "alias/${var.environment}-main"
  target_key_id = aws_kms_key.main.key_id
}
```

### Monitoring and Logging

#### CloudWatch

```hcl
resource "aws_cloudwatch_log_group" "app" {
  name              = "/aws/application/${var.app_name}/${var.environment}"
  retention_in_days = var.log_retention_days
  kms_key_id        = aws_kms_key.main.arn
  
  tags = merge(local.common_tags, {
    Name = "${var.environment}-app-logs"
  })
}

resource "aws_cloudwatch_metric_alarm" "high_cpu" {
  alarm_name          = "${var.environment}-high-cpu-utilization"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/EC2"
  period              = "120"
  statistic           = "Average"
  threshold           = "80"
  alarm_description   = "This metric monitors ec2 cpu utilization"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  
  dimensions = {
    AutoScalingGroupName = aws_autoscaling_group.web.name
  }
  
  tags = local.common_tags
}

resource "aws_sns_topic" "alerts" {
  name         = "${var.environment}-alerts"
  display_name = "${var.environment} Alerts"
  kms_master_key_id = aws_kms_key.main.id
  
  tags = local.common_tags
}
```

## Best Practices

### Project Structure and Organization

#### Monorepo Structure

```
terraform-infrastructure/
├── environments/
│   ├── dev/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   ├── outputs.tf
│   │   ├── terraform.tfvars
│   │   └── backend.tf
│   ├── staging/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   ├── outputs.tf
│   │   ├── terraform.tfvars
│   │   └── backend.tf
│   └── production/
│       ├── main.tf
│       ├── variables.tf
│       ├── outputs.tf
│       ├── terraform.tfvars
│       └── backend.tf
├── modules/
│   ├── vpc/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   ├── outputs.tf
│   │   └── README.md
│   ├── compute/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   ├── outputs.tf
│   │   └── README.md
│   └── database/
│       ├── main.tf
│       ├── variables.tf
│       ├── outputs.tf
│       └── README.md
├── shared/
│   ├── locals.tf
│   ├── data.tf
│   └── providers.tf
├── scripts/
│   ├── deploy.sh
│   ├── validate.sh
│   └── cleanup.sh
└── docs/
    ├── architecture.md
    ├── deployment.md
    └── troubleshooting.md
```

#### Microservice Infrastructure Structure

```
services/
├── service-a/
│   ├── infrastructure/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   ├── outputs.tf
│   │   └── terraform.tfvars
│   └── application/
├── service-b/
│   ├── infrastructure/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   ├── outputs.tf
│   │   └── terraform.tfvars
│   └── application/
└── shared-infrastructure/
    ├── vpc/
    ├── monitoring/
    └── security/
```

### Naming Conventions

```hcl
# Resource naming pattern: {environment}-{service}-{resource-type}-{identifier}
resource "aws_instance" "web" {
  ami           = var.ami_id
  instance_type = var.instance_type
  
  tags = {
    Name        = "${var.environment}-${var.service}-web-${count.index + 1}"
    Environment = var.environment
    Service     = var.service
    ManagedBy   = "terraform"
  }
}

# Consistent tagging strategy
locals {
  mandatory_tags = {
    Environment   = var.environment
    Project       = var.project_name
    Owner         = var.team_name
    ManagedBy     = "terraform"
    CostCenter    = var.cost_center
    CreatedDate   = formatdate("YYYY-MM-DD", timestamp())
  }
  
  # Environment-specific tags
  environment_tags = var.environment == "production" ? {
    Backup        = "required"
    Monitoring    = "enhanced"
    Support       = "24x7"
  } : {
    Backup        = "optional"
    Monitoring    = "basic"
    Support       = "business-hours"
  }
  
  common_tags = merge(local.mandatory_tags, local.environment_tags)
}
```

### DRY Principles and Reusability

#### Shared Variables and Locals

```hcl
# shared/variables.tf
variable "common_config" {
  description = "Common configuration across environments"
  type = object({
    region            = string
    availability_zones = list(string)
    vpc_cidr          = string
    project_name      = string
    team_name         = string
    cost_center       = string
  })
  
  default = {
    region            = "us-west-2"
    availability_zones = ["us-west-2a", "us-west-2b", "us-west-2c"]
    vpc_cidr          = "10.0.0.0/16"
    project_name      = "my-project"
    team_name         = "devops"
    cost_center       = "engineering"
  }
}

# Environment-specific overrides
variable "environment_config" {
  description = "Environment-specific configuration"
  type = map(object({
    instance_type     = string
    min_size         = number
    max_size         = number
    desired_capacity = number
    db_instance_class = string
  }))
  
  default = {
    dev = {
      instance_type     = "t3.micro"
      min_size         = 1
      max_size         = 2
      desired_capacity = 1
      db_instance_class = "db.t3.micro"
    }
    staging = {
      instance_type     = "t3.small"
      min_size         = 1
      max_size         = 3
      desired_capacity = 2
      db_instance_class = "db.t3.small"
    }
    production = {
      instance_type     = "t3.medium"
      min_size         = 2
      max_size         = 10
      desired_capacity = 3
      db_instance_class = "db.t3.medium"
    }
  }
}
```

### Version Management and Constraints

```hcl
terraform {
  required_version = ">= 1.5.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.20"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.4"
    }
    tls = {
      source  = "hashicorp/tls"
      version = "~> 4.0"
    }
  }
}

# Module version constraints
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"
  
  # Module configuration...
}
```

### Testing and Quality Assurance

#### Pre-commit Hooks Configuration

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files

  - repo: https://github.com/antonbabenko/pre-commit-terraform
    rev: v1.83.2
    hooks:
      - id: terraform_fmt
      - id: terraform_validate
      - id: terraform_docs
      - id: terraform_tflint
      - id: terraform_tfsec
        args:
          - --args=--soft-fail

  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.4.0
    hooks:
      - id: detect-secrets
        args: ['--baseline', '.secrets.baseline']
```

#### Unit Testing with Terratest

```go
// test/terraform_vpc_test.go
package test

import (
    "testing"
    
    "github.com/gruntwork-io/terratest/modules/terraform"
    "github.com/stretchr/testify/assert"
)

func TestVPCModule(t *testing.T) {
    terraformOptions := terraform.WithDefaultRetryableErrors(t, &terraform.Options{
        TerraformDir: "../modules/vpc",
        
        Vars: map[string]interface{}{
            "vpc_cidr":             "10.0.0.0/16",
            "availability_zones":   []string{"us-west-2a", "us-west-2b"},
            "environment":          "test",
        },
    })
    
    defer terraform.Destroy(t, terraformOptions)
    
    terraform.InitAndApply(t, terraformOptions)
    
    vpcId := terraform.Output(t, terraformOptions, "vpc_id")
    publicSubnetIds := terraform.OutputList(t, terraformOptions, "public_subnet_ids")
    
    assert.NotEmpty(t, vpcId)
    assert.Len(t, publicSubnetIds, 2)
}
```

#### Integration Testing

```bash
#!/bin/bash
# scripts/integration_test.sh

set -e

ENVIRONMENT="test"
REGION="us-west-2"

echo "Starting integration tests for environment: $ENVIRONMENT"

# Deploy infrastructure
terraform -chdir=environments/$ENVIRONMENT init
terraform -chdir=environments/$ENVIRONMENT apply -auto-approve

# Wait for resources to be ready
echo "Waiting for infrastructure to be ready..."
sleep 60

# Run application tests
./scripts/test_application.sh $ENVIRONMENT

# Verify monitoring and logging
./scripts/test_monitoring.sh $ENVIRONMENT

# Cleanup
terraform -chdir=environments/$ENVIRONMENT destroy -auto-approve

echo "Integration tests completed successfully"
```

### Security Best Practices

#### Input Validation

```hcl
variable "allowed_cidr_blocks" {
  description = "List of CIDR blocks allowed to access resources"
  type        = list(string)
  
  validation {
    condition = alltrue([
      for cidr in var.allowed_cidr_blocks : can(cidrhost(cidr, 0))
    ])
    error_message = "All CIDR blocks must be valid IPv4 CIDR notation."
  }
  
  validation {
    condition = alltrue([
      for cidr in var.allowed_cidr_blocks : !contains(["0.0.0.0/0"], cidr)
    ])
    error_message = "CIDR block 0.0.0.0/0 is not allowed for security reasons."
  }
}

variable "instance_types" {
  description = "Map of allowed instance types per environment"
  type        = map(list(string))
  
  default = {
    dev        = ["t3.micro", "t3.small"]
    staging    = ["t3.small", "t3.medium"]
    production = ["t3.medium", "t3.large", "t3.xlarge"]
  }
  
  validation {
    condition = alltrue([
      for env, types in var.instance_types : alltrue([
        for type in types : can(regex("^[tm][0-9]", type))
      ])
    ])
    error_message = "Instance types must be valid AWS EC2 instance types."
  }
}
```

#### Sensitive Data Handling

```hcl
# Use AWS Secrets Manager for sensitive data
resource "aws_secretsmanager_secret" "db_credentials" {
  name                    = "${var.environment}/database/credentials"
  description             = "Database credentials for ${var.environment}"
  recovery_window_in_days = var.environment == "production" ? 30 : 0
  
  tags = local.common_tags
}

resource "aws_secretsmanager_secret_version" "db_credentials" {
  secret_id = aws_secretsmanager_secret.db_credentials.id
  secret_string = jsonencode({
    username = var.db_username
    password = var.db_password
  })
}

# Reference secrets in resources
data "aws_secretsmanager_secret_version" "db_credentials" {
  secret_id = aws_secretsmanager_secret.db_credentials.id
}

locals {
  db_credentials = jsondecode(data.aws_secretsmanager_secret_version.db_credentials.secret_string)
}

resource "aws_db_instance" "main" {
  # ... other configuration
  username = local.db_credentials.username
  password = local.db_credentials.password
  
  # Mark outputs as sensitive
  tags = merge(local.common_tags, {
    Name = "${var.environment}-database"
  })
}

# Sensitive outputs
output "database_endpoint" {
  description = "RDS instance endpoint"
  value       = aws_db_instance.main.endpoint
  sensitive   = true
}
```

### Cost Optimization Strategies

#### Resource Scheduling

```hcl
# Auto Scaling Schedule for Non-Production
resource "aws_autoscaling_schedule" "scale_down_evening" {
  count = var.environment != "production" ? 1 : 0
  
  scheduled_action_name  = "${var.environment}-scale-down-evening"
  min_size               = 0
  max_size               = 0
  desired_capacity       = 0
  recurrence             = "0 19 * * MON-FRI"
  auto_scaling_group_name = aws_autoscaling_group.web.name
}

resource "aws_autoscaling_schedule" "scale_up_morning" {
  count = var.environment != "production" ? 1 : 0
  
  scheduled_action_name  = "${var.environment}-scale-up-morning"
  min_size               = var.min_size
  max_size               = var.max_size
  desired_capacity       = var.desired_capacity
  recurrence             = "0 8 * * MON-FRI"
  auto_scaling_group_name = aws_autoscaling_group.web.name
}
```

#### Spot Instance Configuration

```hcl
resource "aws_launch_template" "web_spot" {
  count = var.use_spot_instances ? 1 : 0
  
  name_prefix   = "${var.environment}-web-spot-"
  image_id      = data.aws_ami.amazon_linux.id
  instance_type = var.instance_type
  
  instance_market_options {
    market_type = "spot"
    spot_options {
      max_price = var.spot_price
    }
  }
  
  # Mixed instance policy for ASG
  vpc_security_group_ids = [aws_security_group.web.id]
  
  tag_specifications {
    resource_type = "instance"
    tags = merge(local.common_tags, {
      Name = "${var.environment}-web-spot"
      Type = "spot"
    })
  }
}
```

#### Resource Lifecycle Management

```hcl
# EBS Volume cleanup
resource "aws_ebs_volume" "data" {
  count = var.create_data_volume ? 1 : 0
  
  availability_zone = var.availability_zone
  size              = var.data_volume_size
  type              = "gp3"
  encrypted         = true
  
  tags = merge(local.common_tags, {
    Name = "${var.environment}-data-volume"
  })
  
  lifecycle {
    prevent_destroy = true
  }
}

# Automated cleanup for temporary resources
resource "aws_cloudwatch_event_rule" "cleanup_schedule" {
  name                = "${var.environment}-cleanup-schedule"
  description         = "Trigger cleanup for temporary resources"
  schedule_expression = "cron(0 2 * * ? *)"  # Daily at 2 AM
  
  tags = local.common_tags
}

resource "aws_lambda_function" "cleanup" {
  filename      = "cleanup_lambda.zip"
  function_name = "${var.environment}-resource-cleanup"
  role          = aws_iam_role.lambda_cleanup.arn
  handler       = "index.handler"
  runtime       = "python3.9"
  timeout       = 300
  
  environment {
    variables = {
      ENVIRONMENT = var.environment
      REGION      = var.region
    }
  }
  
  tags = local.common_tags
}
```

### Advanced Workflow Patterns

#### Blue-Green Deployment Strategy

```hcl
variable "deployment_color" {
  description = "Current deployment color (blue or green)"
  type        = string
  default     = "blue"
  
  validation {
    condition     = contains(["blue", "green"], var.deployment_color)
    error_message = "Deployment color must be either 'blue' or 'green'."
  }
}

locals {
  inactive_color = var.deployment_color == "blue" ? "green" : "blue"
}

# Blue environment
module "blue_environment" {
  count = var.deployment_color == "blue" ? 1 : 0
  
  source = "./modules/application"
  
  environment_name = "${var.environment}-blue"
  instance_count   = var.instance_count
  # ... other configuration
}

# Green environment
module "green_environment" {
  count = var.deployment_color == "green" ? 1 : 0
  
  source = "./modules/application"
  
  environment_name = "${var.environment}-green"
  instance_count   = var.instance_count
  # ... other configuration
}

# Load balancer target group switching
resource "aws_lb_listener_rule" "main" {
  listener_arn = aws_lb_listener.main.arn
  priority     = 100
  
  action {
    type             = "forward"
    target_group_arn = var.deployment_color == "blue" ? 
                      module.blue_environment[0].target_group_arn : 
                      module.green_environment[0].target_group_arn
  }
  
  condition {
    path_pattern {
      values = ["/*"]
    }
  }
}
```

#### Canary Deployment with Weighted Routing

```hcl
resource "aws_lb_listener_rule" "canary" {
  count = var.enable_canary ? 1 : 0
  
  listener_arn = aws_lb_listener.main.arn
  priority     = 50
  
  action {
    type = "forward"
    forward {
      target_group {
        arn    = aws_lb_target_group.stable.arn
        weight = 100 - var.canary_weight
      }
      target_group {
        arn    = aws_lb_target_group.canary.arn
        weight = var.canary_weight
      }
    }
  }
  
  condition {
    path_pattern {
      values = ["/*"]
    }
  }
}
```

### Disaster Recovery and Backup Strategies

#### Multi-Region Setup

```hcl
# Primary region provider
provider "aws" {
  alias  = "primary"
  region = var.primary_region
}

# DR region provider
provider "aws" {
  alias  = "dr"
  region = var.dr_region
}

# Primary region resources
module "primary_infrastructure" {
  source = "./modules/infrastructure"
  
  providers = {
    aws = aws.primary
  }
  
  environment = var.environment
  region      = var.primary_region
}

# DR region resources
module "dr_infrastructure" {
  source = "./modules/infrastructure"
  
  providers = {
    aws = aws.dr
  }
  
  environment = "${var.environment}-dr"
  region      = var.dr_region
}

# Cross-region replication for S3
resource "aws_s3_bucket_replication_configuration" "primary_to_dr" {
  provider = aws.primary
  
  role   = aws_iam_role.replication.arn
  bucket = module.primary_infrastructure.s3_bucket_id
  
  rule {
    id     = "replicate-to-dr"
    status = "Enabled"
    
    destination {
      bucket        = module.dr_infrastructure.s3_bucket_arn
      storage_class = "STANDARD_IA"
    }
  }
  
  depends_on = [aws_s3_bucket_versioning.primary]
}
```

#### Automated Backup Strategy

```hcl
resource "aws_backup_vault" "main" {
  name        = "${var.environment}-backup-vault"
  kms_key_arn = aws_kms_key.backup.arn
  
  tags = local.common_tags
}

resource "aws_backup_plan" "main" {
  name = "${var.environment}-backup-plan"
  
  rule {
    rule_name         = "daily_backups"
    target_vault_name = aws_backup_vault.main.name
    schedule          = "cron(0 5 ? * * *)"  # Daily at 5 AM
    
    recovery_point_tags = local.common_tags
    
    lifecycle {
      cold_storage_after = 30
      delete_after       = 120
    }
    
    copy_action {
      destination_vault_arn = aws_backup_vault.dr.arn
      
      lifecycle {
        cold_storage_after = 30
        delete_after       = 120
      }
    }
  }
  
  tags = local.common_tags
}

resource "aws_backup_selection" "main" {
  iam_role_arn = aws_iam_role.backup.arn
  name         = "${var.environment}-backup-selection"
  plan_id      = aws_backup_plan.main.id
  
  selection_tag {
    type  = "STRINGEQUALS"
    key   = "Backup"
    value = "required"
  }
}
```

### Monitoring and Observability

#### Comprehensive Monitoring Setup

```hcl
resource "aws_cloudwatch_dashboard" "main" {
  dashboard_name = "${var.environment}-infrastructure-dashboard"
  
  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6
        
        properties = {
          metrics = [
            ["AWS/EC2", "CPUUtilization", "AutoScalingGroupName", aws_autoscaling_group.web.name],
            [".", "NetworkIn", ".", "."],
            [".", "NetworkOut", ".", "."]
          ]
          period = 300
          stat   = "Average"
          region = var.region
          title  = "EC2 Metrics"
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 6
        width  = 12
        height = 6
        
        properties = {
          metrics = [
            ["AWS/ApplicationELB", "RequestCount", "LoadBalancer", aws_lb.main.arn_suffix],
            [".", "TargetResponseTime", ".", "."],
            [".", "HTTPCode_Target_2XX_Count", ".", "."]
          ]
          period = 300
          stat   = "Sum"
          region = var.region
          title  = "Load Balancer Metrics"
        }
      }
    ]
  })
}

# Custom metrics via CloudWatch agent
resource "aws_ssm_parameter" "cloudwatch_config" {
  name  = "/${var.environment}/cloudwatch-agent/config"
  type  = "String"
  value = jsonencode({
    agent = {
      metrics_collection_interval = 60
      run_as_user                 = "cwagent"
    }
    logs = {
      logs_collected = {
        files = {
          collect_list = [
            {
              file_path      = "/var/log/application.log"
              log_group_name = aws_cloudwatch_log_group.app.name
              log_stream_name = "{instance_id}/application"
            }
          ]
        }
      }
    }
    metrics = {
      namespace = "CustomApp/${var.environment}"
      metrics_collected = {
        cpu = {
          measurement = ["cpu_usage_idle", "cpu_usage_iowait"]
          metrics_collection_interval = 60
        }
        disk = {
          measurement = ["used_percent"]
          metrics_collection_interval = 60
          resources = ["*"]
        }
        mem = {
          measurement = ["mem_used_percent"]
          metrics_collection_interval = 60
        }
      }
    }
  })
  
  tags = local.common_tags
}
```

This comprehensive Terraform guide covers all essential DevOps responsibilities and best practices. From basic commands to advanced deployment strategies, it provides practical examples for managing infrastructure as code at scale. The guide emphasizes security, cost optimization, testing, and operational excellence throughout the infrastructure lifecycle. }

````

#### DynamoDB Locking
Prevents concurrent Terraform operations that could corrupt state.

```hcl
resource "aws_dynamodb_table" "terraform_locks" {
  name           = "terraform-locks"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "LockID"

  attribute {
    name = "LockID"
    type = "S"
  }

  tags = {
    Name = "Terraform State Lock Table"
  }
}
````

**DevOps Benefits**:

- Prevents state corruption
- Team collaboration safety
- Automated conflict resolution
- Audit trail for changes

### terraform import

Imports existing infrastructure resources into Terraform state.

**DevOps Responsibility**: Adopting existing infrastructure and migration scenarios.

```bash
# Import AWS instance
terraform import aws_instance.web i-1234567890abcdef0

# Import with specific provider
terraform import -provider=aws.us-east-1 aws_instance.web i-1234567890abcdef0
```

**Migration Strategy**:

1. Create resource configuration
2. Import existing resource
3. Run terraform plan to verify
4. Adjust configuration as needed

### terraform taint

Marks a resource for recreation on next apply.

**DevOps Responsibility**: Force resource recreation when needed.

```bash
# Taint a resource
terraform taint aws_instance.web

# Untaint a resource
terraform untaint aws_instance.web
```

**Use Cases**:

- Force VM recreation
- Reset corrupted resources
- Apply configuration changes requiring recreation
- Testing disaster recovery procedures

## Configuration Management

### Variables and Precedence

#### terraform.tfvars

Default variable values file automatically loaded by Terraform.

```hcl
# terraform.tfvars
environment = "production"
instance_type = "t3.large"
region = "us-west-2"
```

#### auto.tfvars

Automatically loaded variable files with specific naming pattern.

```hcl
# prod.auto.tfvars
environment = "prod"
db_instance_class = "db.t3.large"
```

#### Variable Precedence Order

1. Command line flags (`-var` and `-var-file`)
2. `*.auto.tfvars` files (alphabetical order)
3. `terraform.tfvars` file
4. Environment variables (`TF_VAR_name`)
5. Variable defaults in configuration

#### Variable Types and Validation

```hcl
variable "environment" {
  description = "Environment name"
  type        = string
  default     = "dev"
  
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

variable "availability_zones" {
  description = "List of availability zones"
  type        = list(string)
  default     = ["us-west-2a", "us-west-2b"]
}

variable "instance_config" {
  description = "Instance configuration"
  type = object({
    instance_type = string
    ami_id        = string
    key_name      = string
  })
}
```

#### Environment Variables

Access system environment variables in Terraform.

```bash
# Set Terraform variables via environment
export TF_VAR_region="us-west-2"
export TF_VAR_instance_type="t3.medium"

# AWS credentials
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
```

### terraform locals

Local values for reducing repetition and improving readability.

```hcl
locals {
  common_tags = {
    Environment = var.environment
    Project     = "my-project"
    Owner       = "devops-team"
  }
  
  vpc_cidr = "10.0.0.0/16"
  
  subnet_cidrs = {
    public  = cidrsubnet(local.vpc_cidr, 8, 1)
    private = cidrsubnet(local.vpc_cidr, 8, 2)
  }
}

resource "aws_instance" "web" {
  ami           = var.ami_id
  instance_type = var.instance_type
  
  tags = merge(local.common_tags, {
    Name = "web-server"
  })
}
```

### terraform outputs

Define values to be returned after Terraform applies configuration.

```hcl
output "instance_ip" {
  description = "Public IP of the web server"
  value       = aws_instance.web.public_ip
  sensitive   = false
}

output "vpc_id" {
  description = "ID of the VPC"
  value       = aws_vpc.main.id
}

output "database_endpoint" {
  description = "RDS instance endpoint"
  value       = aws_db_instance.main.endpoint
  sensitive   = true
}
```

**DevOps Usage**:

- Share values between Terraform configurations
- Integration with CI/CD pipelines
- Documentation and reporting
- Dependency management between environments

### terraform data sources

Fetch information about existing resources not managed by current configuration.

```hcl
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-focal-20.04-amd64-server-*"]
  }
}

data "aws_availability_zones" "available" {
  state = "available"
}

data "aws_caller_identity" "current" {}

resource "aws_instance" "web" {
  ami               = data.aws_ami.ubuntu.id
  availability_zone = data.aws_availability_zones.available.names[0]
  
  tags = {
    Owner = data.aws_caller_identity.current.user_id
  }
}
```

## Modules

### Module Structure and Composition

Modules enable code reusability and organization.

**Standard Module Structure**:

```
modules/
├── vpc/
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   └── README.md
├── ec2/
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   └── README.md
└── rds/
    ├── main.tf
    ├── variables.tf
    ├── outputs.tf
    └── README.md
```

### Module Usage and Versioning

```hcl
module "vpc" {
  source = "./modules/vpc"
  # source = "git::https://github.com/company/terraform-modules.git//vpc?ref=v1.0.0"
  # source = "terraform-aws-modules/vpc/aws"
  # version = "~> 3.0"
  
  vpc_cidr             = "10.0.0.0/16"
  availability_zones   = ["us-west-2a", "us-west-2b"]
  environment         = var.environment
  
  tags = local.common_tags
}

module "web_servers" {
  source = "./modules/ec2"
  
  count = var.instance_count
  
  subnet_id      = module.vpc.public_subnet_ids[count.index]
  security_group = module.vpc.web_security_group_id
  instance_type  = var.instance_type
  
  depends_on = [module.vpc]
}
```

### Module Registry

Terraform Registry provides reusable modules for common infrastructure patterns.

**Using Registry Modules**:

```hcl
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 3.0"

  name = "my-vpc"
  cidr = "10.0.0.0/16"

  azs             = ["us-west-2a", "us-west-2b", "us-west-2c"]
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]

  enable_nat_gateway = true
  enable_vpn_gateway = true

  tags = {
    Terraform = "true"
    Environment = "dev"
  }
}
```

### Module Inputs and Outputs

**Module Variables** (`variables.tf`):

```hcl
variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "List of availability zones"
  type        = list(string)
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}
```

**Module Outputs** (`outputs.tf`):

```hcl
output "vpc_id" {
  description = "ID of the VPC"
  value       = aws_vpc.main.id
}

output "public_subnet_ids" {
  description = "IDs of the public subnets"
  value       = aws_subnet.public[*].id
}

output "private_subnet_ids" {
  description = "IDs of the private subnets"
  value       = aws_subnet.private[*].id
}
```

## Resource Management

### Lifecycle Management

```hcl
resource "aws_instance" "web" {
  ami           = var.ami_id
  instance_type = var.instance_type
  
  lifecycle {
    create_before_destroy = true
    prevent_destroy       = true
    ignore_changes       = [ami, user_data]
  }
  
  tags = {
    Name = "web-server"
  }
}
```

**Lifecycle Rules**:

- `create_before_destroy`: Create replacement before destroying original
- `prevent_destroy`: Prevent accidental resource destruction
- `ignore_changes`: Ignore changes to specified attributes

### Meta-Arguments

#### depends_on

Explicit dependency declaration between resources.

```hcl
resource "aws_instance" "web" {
  ami           = var.ami_id
  instance_type = var.instance_type
  
  depends_on = [
    aws_security_group.web,
    aws_key_pair.deployer
  ]
}
```

#### count

Create multiple similar resources.

```hcl
resource "aws_instance" "web" {
  count = var.instance_count
  
  ami           = var.ami_id
  instance_type = var.instance_type
  subnet_id     = var.subnet_ids[count.index]
  
  tags = {
    Name = "web-${count.index + 1}"
  }
}
```

#### for_each

Create resources based on map or set of strings.

```hcl
variable "users" {
  type = map(object({
    role = string
    groups = list(string)
  }))
  default = {
    "alice" = {
      role = "admin"
      groups = ["admins", "developers"]
    }
    "bob" = {
      role = "developer"
      groups = ["developers"]
    }
  }
}

resource "aws_iam_user" "users" {
  for_each = var.users
  
  name = each.key
  
  tags = {
    Role = each.value.role
  }
}
```

### Dynamic Blocks

Generate nested configuration blocks dynamically.

```hcl
resource "aws_security_group" "web" {
  name_prefix = "web-"
  
  dynamic "ingress" {
    for_each = var.ingress_rules
    content {
      from_port   = ingress.value.from_port
      to_port     = ingress.value.to_port
      protocol    = ingress.value.protocol
      cidr_blocks = ingress.value.cidr_blocks
    }
  }
}
```

### Provisioners

#### local-exec

Execute commands on machine running Terraform.

```hcl
resource "aws_instance" "web" {
  ami           = var.ami_id
  instance_type = var.instance_type
  
  provisioner "local-exec" {
    command = "echo ${self.private_ip} >> private_ips.txt"
  }
  
  provisioner "local-exec" {
    when    = destroy
    command = "echo 'Instance ${self.id} is being destroyed' >> destroy.log"
  }
}
```

#### remote-exec

Execute commands on remote resource.

```hcl
resource "aws_instance" "web" {
  ami           = var.ami_id
  instance_type = var.instance_type
  key_name      = var.key_name
  
  connection {
    type        = "ssh"
    user        = "ubuntu"
    private_key = file(var.private_key_path)
    host        = self.public_ip
  }
  
  provisioner "remote-exec" {
    inline = [
      "sudo apt-get update",
      "sudo apt-get install -y nginx",
      "sudo systemctl start nginx"
    ]
  }
}
```

#### null_resource

Execute provisioners without associated infrastructure resource.

```hcl
resource "null_resource" "deploy_app" {
  triggers = {
    instance_ids = join(",", aws_instance.web[*].id)
    app_version  = var.app_version
  }
  
  provisioner "local-exec" {
    command = "./deploy.sh ${var.app_version}"
  }
  
  depends_on = [aws_instance.web]
}
```

## Providers

### Provider Configuration

```hcl
terraform {
  required_version = ">= 1.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.1"
    }
  }
}

provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Terraform   = "true"
      Environment = var.environment
    }
  }
}
```

### Multiple Providers and Aliases

```hcl
provider "aws" {
  alias  = "us_east_1"
  region = "us-east-1"
}

provider "aws" {
  alias  = "us_west_2"
  region = "us-west-2"
}

resource "aws_instance" "east" {
  provider = aws.us_east_1
  
  ami           = data.aws_ami.ubuntu_east.id
  instance_type = "t3.micro"
}

resource "aws_instance" "west" {
  provider = aws.us_west_2
  
  ami           = data.aws_ami.ubuntu_west.id
  instance_type = "t3.micro"
}
```

### Assume Role Configuration

```hcl
provider "aws" {
  region = "us-west-2"
  
  assume_role {
    role_arn     = "arn:aws:iam::123456789012:role/TerraformRole"
    session_name = "terraform-session"
    external_id  = "unique-external-id"
  }
}
```

## Environment Management

### Workspace Management

#### terraform workspace

Manage multiple environments with workspace isolation.

```bash
# List workspaces
terraform workspace list

# Create new workspace
terraform workspace new production

# Select workspace
terraform workspace select staging

# Delete workspace
terraform workspace delete development

# Show current workspace
terraform workspace show
```

**Workspace Usage in Configuration**:

```hcl
locals {
  environment = terraform.workspace
  
  instance_counts = {
    default    = 1
    staging    = 2
    production = 5
  }
}

resource "aws_instance" "web" {
  count = local.instance_counts[local.environment]
  
  ami           = var.ami_id
  instance_type = local.environment == "production" ? "t3.large" : "t3.micro"
  
  tags = {
    Name        = "web-${local.environment}-${count.index + 1}"
    Environment = local.environment
  }
}
```

### Environment Folders Structure

```
environments/
├── dev/
│   ├── main.tf
│   ├── variables.tf
│   ├── terraform.tfvars
│   └── backend.tf
├── staging/
│   ├── main.tf
│   ├── variables.tf
│   ├── terraform.tfvars
│   └── backend.tf
└── prod/
    ├── main.tf
    ├── variables.tf
    ├── terraform.tfvars
    └── backend.tf
```

### Multi-Account Setup

```hcl
# Account-specific provider configuration
provider "aws" {
  alias  = "dev"
  region = var.region
  
  assume_role {
    role_arn = "arn:aws:iam::111111111111:role/TerraformRole"
  }
}

provider "aws" {
  alias  = "prod"
  region = var.region
  
  assume_role {
    role_arn = "arn:aws:iam::222222222222:role/TerraformRole"
  }
}

module "dev_infrastructure" {
  source = "../modules/infrastructure"
  
  providers = {
    aws = aws.dev
  }
  
  environment = "dev"
}

module "prod_infrastructure" {
  source = "../modules/infrastructure"
  
  providers = {
    aws = aws.prod
  }
  
  environment = "prod"
}
```

## CI/CD Integration

### GitHub Actions Integration

```yaml
name: Terraform CI/CD

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  terraform:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup Terraform
      uses: hashicorp/setup-terraform@v2
      with:
        terraform_version: 1.5.0
    
    - name: Terraform Format Check
      run: terraform fmt -check -recursive
    
    - name: Terraform Init
      run: terraform init
      env:
        AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
        AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
    
    - name: Terraform Validate
      run: terraform validate
    
    - name: Terraform Plan
      if: github.event_name == 'pull_request'
      run: terraform plan -out=tfplan
      env:
        AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
        AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
    
    - name: Terraform Apply
      if: github.ref == 'refs/heads/main'
      run: terraform apply -auto-approve
      env:
        AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
        AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
```

### GitLab CI Integration

```yaml
stages:
  - validate
  - plan
  - apply

variables:
  TF_ROOT: ${CI_PROJECT_DIR}
  TF_ADDRESS: ${CI_API_V4_URL}/projects/${CI_PROJECT_ID}/terraform/state/production

cache:
  key: "${TF_ROOT}"
  paths:
    - ${TF_ROOT}/.terraform

before_script:
  - cd ${TF_ROOT}
  - terraform --version
  - terraform init

validate:
  stage: validate
  script:
    - terraform validate
    - terraform fmt -check -recursive

plan:
  stage: plan
  script:
    - terraform plan -out=tfplan
  artifacts:
    paths:
      - ${TF_ROOT}/tfplan
    expire_in: 1 week
  only:
    - merge_requests

apply:
  stage: apply
  script:
    - terraform apply tfplan
  dependencies:
    - plan
  only:
    - main
  when: manual
```

### Jenkins Pipeline

```groovy
pipeline {
    agent any
    
    environment {
        AWS_CREDENTIALS = credentials('aws-credentials')
        TF_VAR_environment = "${env.BRANCH_NAME == 'main' ? 'prod' : 'dev'}"
    }
    
    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        
        stage('Terraform Init') {
            steps {
                sh 'terraform init -input=false'
            }
        }
        
        stage('Terraform Validate') {
            steps {
                sh 'terraform validate'
                sh 'terraform fmt -check -recursive'
            }
        }
        
        stage('Terraform Plan') {
            steps {
                sh 'terraform plan -out=tfplan -input=false'
                publishHTML([
                    allowMissing: false,
                    alwaysLinkToLastBuild: true,
                    keepAll: true,
                    reportDir: '.',
                    reportFiles: 'tfplan',
                    reportName: 'Terraform Plan'
                ])
            }
        }
        
        stage('Terraform Apply') {
            when {
                branch 'main'
            }
            steps {
                input message: 'Apply Terraform changes?', ok: 'Apply'
                sh 'terraform apply tfplan'
            }
        }
    }
    
    post {
        always {
            cleanWs()
        }
    }
}
```

## Security and Compliance

### Secrets Management

#### terraform login/logout

Authenticate with Terraform Cloud or Enterprise.

```bash
# Login to Terraform Cloud
terraform login

# Login to specific hostname
terraform login app.terraform.io

# Logout
terraform logout
```

#### Sensitive Variables

```hcl
variable "db_password" {
  description = "Database password"
  type        = string
  sensitive   = true
}

resource "aws_db_instance" "main" {
  password = var.db_password
  
  # Other configuration...
}

output "db_endpoint" {
  value     = aws_db_instance.main.endpoint
  sensitive = true
}
```

#### AWS Secrets Manager Integration

```hcl
data "aws_secretsmanager_secret" "db_password" {
  name = "prod/database/password"
}

data "aws_secretsmanager_secret_version" "db_password" {
  secret_id = data.aws_secretsmanager_secret.db_password.id
}

resource "aws_db_instance" "main" {
  password = jsondecode(data.aws_secretsmanager_secret_version.db_password.secret_string)["password"]
  
  # Other configuration...
}
```

### Security Scanning Tools

#### TFSec

Security scanner for Terraform code.

```bash
# Install tfsec
curl -s https://raw.githubusercontent.com/aquasecurity/tfsec/master/scripts/install_linux.sh | bash

# Scan current directory
tfsec .

# Scan with custom checks
tfsec --custom-check-dir ./custom-checks .

# Output in JSON format
tfsec --format json .
```

#### Checkov

Static code analysis for infrastructure as code.

```bash
# Install checkov
pip install checkov

# Scan Terraform files
checkov -d .

# Scan with specific framework
checkov -f terraform -d .

# Skip specific checks
checkov -d . --skip-check CKV_AWS_20
```

#### TFLint

Terraform linter focusing on possible errors and best practices.

```bash
# Install tflint
curl -s https://raw.githubusercontent.com/terraform-linters/tflint/master/install_linux.sh | bash

# Initialize tflint
tflint --init

# Lint current directory
tflint

# Lint with custom config
tflint --config=.tflint.hcl
```

### Compliance and Policy

#### Open Policy Agent (OPA)

Policy as code framework for Terraform.

```rego
package terraform.analysis

import input as tfplan

deny[reason] {
    r := tfplan.resource_changes[_]
    r.type == "aws_security_group"
    r.change.after.ingress[_].cidr_blocks[_] == "0.0.0.0/0"
    reason := sprintf("Security group %s allows ingress from 0.0.0.0/0", [r.address])
}

deny[reason] {
    r := tfplan.resource_changes[_]
    r.type == "aws_instance"
    not r.change.after.tags.Environment
    reason := sprintf("Instance %s missing Environment tag", [r.address])
}
```

#### Sentinel (Terraform Enterprise)

Policy as code framework integrated with Terraform Enterprise.

```hcl
import "tfplan/v2" as tfplan

main = rule {
    all tfplan.resource_changes as _, rc {
        rc.type is not "aws_instance" or
        rc.change.after.instance_type in ["t3.micro", "t3.small", "t3.medium"]
    }
}
```

### Cost Management

#### Infracost

Cost estimation for Terraform.

```bash
# Install infracost
curl -fsSL https://raw.githubusercontent.com/infracost/infracost/master/scripts/install.sh | sh

# Generate cost estimate
infracost breakdown --path .

# Compare costs
infracost diff --path .

# Integration with CI/CD
infracost comment github --path . --repo owner/repo --pull-request 123
```

## Advanced Features

### Terraform Functions

#### String Functions

```hcl
locals {
  # String manipulation
  upper_env = upper(var.environment)
  lower_env = lower(var.environment)
  
  # Template rendering
  user_data = templatefile("${path.module}/user_data.tpl", {
    environment = var.environment
    app_name    = var.app_name
  })
  
  # JSON encoding
  policy_document = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = "s3:GetObject"
        Resource = "arn:aws:s3:::bucket/*"
      }
    ]
  })
}
```

#### Network Functions

```hcl
locals {
  vpc_cidr = "10.0.0.0/16"
  
  # CIDR subnet calculation
  public_subnets = [
    cidrsubnet(local.vpc_cidr, 8, 1), # 10.0.1.0/24
    cidrsubnet(local.vpc_cidr, 8, 2), # 10.0.2.0/24
    cidrsubnet(local.vpc_cidr, 8, 3)  # 10.0.3.0/24
  ]
  
  private_subnets = [
    cidrsubnet(local.vpc_cidr, 8, 101), # 10.0.101.0/24
    cidrsubnet(local.vpc_cidr, 8, 102), # 10.0.102.0/24
    cidrsubnet(local.vpc_cidr, 8, 103)  # 10.0.103.0/24
  ]
}
```