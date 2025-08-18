## Terraform Configuration Language (HCL) Comprehensive Guide

HashiCorp Configuration Language (HCL) is a structured configuration language designed to be human-readable and machine-friendly. It's the primary language for writing Terraform configurations.

### Basic Syntax

#### Comments and Structure

```hcl
# Single-line comments start with #
// Alternative single-line comment style

/* 
   Multi-line comments
   use C-style syntax
*/

# Resource block with proper formatting
resource "aws_instance" "example" {
  ami           = "ami-0c02fb55956c7d316"
  instance_type = "t3.micro"
  
  tags = {
    Name        = "HelloWorld"
    Environment = "dev"
  }
}

# Data source block
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical
  
  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-focal-20.04-amd64-server-*"]
  }
  
  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# Variable block with validation
variable "instance_count" {
  description = "Number of instances to create"
  type        = number
  default     = 1
  
  validation {
    condition     = var.instance_count >= 1 && var.instance_count <= 10
    error_message = "Instance count must be between 1 and 10."
  }
}

# Output block with sensitive data
output "instance_ip" {
  description = "The public IP address of the instance"
  value       = aws_instance.example.public_ip
  sensitive   = false
}

output "instance_private_ip" {
  description = "The private IP address of the instance"
  value       = aws_instance.example.private_ip
  sensitive   = true
}
```

#### String Literals and Interpolation

```hcl
# String literals
variable "simple_string" {
  default = "hello world"
}

# String interpolation
variable "interpolated_string" {
  default = "Hello ${var.name}!"
}

# Multi-line strings
variable "multiline_string" {
  default = <<EOT
This is a multi-line string
that spans several lines
and preserves formatting.
EOT
}

# Heredoc with interpolation
locals {
  user_data = <<-EOF
    #!/bin/bash
    echo "Environment: ${var.environment}"
    echo "Region: ${var.region}"
    EOF
}

# Raw strings (no interpolation)
variable "raw_string" {
  default = <<'EOF'
This string contains ${not_interpolated}
and preserves literal content.
EOF
}
```

### Block Types and Structure

#### Core Block Types

```hcl
# Terraform configuration block
terraform {
  required_version = ">= 1.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.4"
    }
  }
  
  backend "s3" {
    bucket = "my-terraform-state"
    key    = "terraform.tfstate"
    region = "us-west-2"
  }
}

# Provider configuration
provider "aws" {
  region = var.aws_region
  
  assume_role {
    role_arn = var.assume_role_arn
  }
  
  default_tags {
    tags = {
      ManagedBy   = "terraform"
      Environment = var.environment
    }
  }
}

# Resource block
resource "aws_instance" "web" {
  ami           = data.aws_ami.ubuntu.id
  instance_type = var.instance_type
  key_name      = aws_key_pair.deployer.key_name
  
  vpc_security_group_ids = [aws_security_group.web.id]
  subnet_id              = aws_subnet.public.id
  
  user_data = base64encode(templatefile("${path.module}/user_data.sh", {
    app_name = var.app_name
  }))
  
  root_block_device {
    volume_type = "gp3"
    volume_size = 20
    encrypted   = true
  }
  
  tags = merge(local.common_tags, {
    Name = "${var.environment}-web-server"
    Role = "web"
  })
  
  lifecycle {
    create_before_destroy = true
    ignore_changes       = [ami, user_data]
  }
}

# Data source block
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"]
  
  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }
  
  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# Local values block
locals {
  common_tags = {
    Environment = var.environment
    Project     = var.project_name
    Owner       = var.team_name
    ManagedBy   = "terraform"
    CreatedOn   = formatdate("YYYY-MM-DD", timestamp())
  }
  
  vpc_cidr = "10.0.0.0/16"
  
  public_subnets = [
    cidrsubnet(local.vpc_cidr, 8, 1),
    cidrsubnet(local.vpc_cidr, 8, 2),
    cidrsubnet(local.vpc_cidr, 8, 3)
  ]
  
  private_subnets = [
    cidrsubnet(local.vpc_cidr, 8, 101),
    cidrsubnet(local.vpc_cidr, 8, 102),
    cidrsubnet(local.vpc_cidr, 8, 103)
  ]
}

# Module block
module "vpc" {
  source = "./modules/vpc"
  # source = "terraform-aws-modules/vpc/aws"
  # version = "~> 3.0"
  
  name = var.vpc_name
  cidr = local.vpc_cidr
  
  azs             = var.availability_zones
  private_subnets = local.private_subnets
  public_subnets  = local.public_subnets
  
  enable_nat_gateway = var.enable_nat_gateway
  enable_vpn_gateway = var.enable_vpn_gateway
  
  tags = local.common_tags
}
```

### Data Types and Collections

#### Primitive Types

```hcl
# String type
variable "name" {
  description = "Name of the resource"
  type        = string
  default     = "example"
  
  validation {
    condition     = length(var.name) > 0
    error_message = "Name cannot be empty."
  }
}

# Number type (integer or float)
variable "instance_count" {
  description = "Number of instances to create"
  type        = number
  default     = 1
  
  validation {
    condition     = var.instance_count >= 1 && var.instance_count <= 100
    error_message = "Instance count must be between 1 and 100."
  }
}

variable "cpu_utilization_threshold" {
  description = "CPU utilization threshold for scaling"
  type        = number
  default     = 80.5
}

# Boolean type
variable "enable_monitoring" {
  description = "Enable CloudWatch monitoring"
  type        = bool
  default     = true
}

variable "create_backup" {
  description = "Create automated backups"
  type        = bool
  default     = false
}
```

#### Collection Types

```hcl
# List type
variable "availability_zones" {
  description = "List of availability zones"
  type        = list(string)
  default     = ["us-west-2a", "us-west-2b", "us-west-2c"]
  
  validation {
    condition     = length(var.availability_zones) >= 2
    error_message = "At least 2 availability zones are required."
  }
}

variable "allowed_ports" {
  description = "List of allowed ports"
  type        = list(number)
  default     = [80, 443, 22]
}

variable "enable_features" {
  description = "List of features to enable"
  type        = list(bool)
  default     = [true, false, true]
}

# Set type (unique values)
variable "unique_tags" {
  description = "Set of unique tag keys"
  type        = set(string)
  default     = ["Environment", "Project", "Owner"]
}

# Map type
variable "instance_types" {
  description = "Map of environment to instance types"
  type        = map(string)
  default = {
    dev     = "t3.micro"
    staging = "t3.small"
    prod    = "t3.large"
  }
}

variable "resource_tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default = {
    Environment = "dev"
    Project     = "my-app"
    Owner       = "devops-team"
  }
}

variable "port_mapping" {
  description = "Port mapping configuration"
  type        = map(number)
  default = {
    http  = 80
    https = 443
    ssh   = 22
  }
}
```

#### Complex Types

```hcl
# Object type
variable "database_config" {
  description = "Database configuration"
  type = object({
    engine         = string
    engine_version = string
    instance_class = string
    allocated_storage = number
    backup_retention = number
    multi_az       = bool
    tags           = map(string)
  })
  
  default = {
    engine         = "postgres"
    engine_version = "13.7"
    instance_class = "db.t3.micro"
    allocated_storage = 20
    backup_retention = 7
    multi_az       = false
    tags = {
      Component = "database"
    }
  }
}

# Tuple type (ordered list with specific types)
variable "server_config" {
  description = "Server configuration tuple"
  type        = tuple([string, number, bool])
  default     = ["web-server", 2, true]
}

# Complex nested object
variable "application_config" {
  description = "Complete application configuration"
  type = object({
    name    = string
    version = string
    
    compute = object({
      instance_type = string
      min_size      = number
      max_size      = number
      desired_size  = number
    })
    
    networking = object({
      vpc_cidr = string
      subnets  = list(string)
      ports    = map(number)
    })
    
    features = object({
      monitoring = bool
      backup     = bool
      encryption = bool
    })
    
    environments = map(object({
      instance_type = string
      replica_count = number
    }))
  })
  
  default = {
    name    = "my-app"
    version = "1.0.0"
    
    compute = {
      instance_type = "t3.medium"
      min_size      = 1
      max_size      = 10
      desired_size  = 3
    }
    
    networking = {
      vpc_cidr = "10.0.0.0/16"
      subnets  = ["10.0.1.0/24", "10.0.2.0/24"]
      ports = {
        http  = 80
        https = 443
      }
    }
    
    features = {
      monitoring = true
      backup     = true
      encryption = true
    }
    
    environments = {
      dev = {
        instance_type = "t3.micro"
        replica_count = 1
      }
      prod = {
        instance_type = "t3.large"
        replica_count = 5
      }
    }
  }
}
```

### Expressions and Functions

#### Arithmetic and Comparison

```hcl
locals {
  # Arithmetic operations
  total_instances = var.web_instances + var.app_instances
  cpu_limit      = var.base_cpu * 2
  storage_gb     = var.storage_mb / 1024
  percentage     = (var.used_space / var.total_space) * 100
  
  # Comparison operations
  is_production   = var.environment == "prod"
  needs_backup    = var.importance_level >= 3
  is_large_enough = var.disk_size > 100
  
  # Logical operations
  enable_monitoring = var.environment == "prod" && var.enable_features
  skip_backup      = var.environment == "dev" || var.temporary_instance
  
  # Conditional expressions
  instance_type = var.environment == "prod" ? "t3.large" : "t3.micro"
  
  # Complex conditional
  storage_type = (
    var.performance_tier == "high" ? "io2" :
    var.performance_tier == "medium" ? "gp3" :
    "gp2"
  )
  
  # Nested conditionals
  backup_schedule = var.environment == "prod" ? (
    var.critical_app ? "0 */2 * * *" : "0 0 * * *"
  ) : "0 0 * * 0"
}
```

#### String Functions

```hcl
locals {
  # String manipulation
  upper_env     = upper(var.environment)
  lower_name    = lower(var.application_name)
  title_case    = title(var.description)
  
  # String formatting
  resource_name = format("%s-%s-%s", var.project, var.environment, var.component)
  formatted_msg = format("Instance %s has %d CPU cores", var.instance_id, var.cpu_count)
  
  # String operations
  trimmed_space = trimspace(var.user_input)
  prefix_name   = trimprefix(var.full_name, "prefix-")
  suffix_name   = trimsuffix(var.full_name, "-suffix")
  
  # String replacement
  sanitized_name = replace(var.raw_name, "_", "-")
  clean_string   = replace(var.input_string, "/[^a-zA-Z0-9-]/", "")
  
  # String splitting and joining
  name_parts   = split("-", var.resource_name)
  joined_tags  = join(",", var.tag_list)
  
  # String validation
  starts_with_prefix = startswith(var.bucket_name, "company-")
  ends_with_suffix   = endswith(var.log_file, ".log")
  contains_keyword   = contains(var.description, "important")
  
  # String length and substrings
  name_length = length(var.resource_name)
  short_name  = substr(var.long_name, 0, 10)
  
  # Regular expressions
  is_valid_email = can(regex("^[\\w\\._%+-]+@[\\w\\.-]+\\.[A-Za-z]{2,}$", var.email))
  
  # Template rendering
  user_data = templatefile("${path.module}/templates/user_data.sh", {
    app_name    = var.app_name
    environment = var.environment
    region      = var.region
    database_url = "postgresql://${var.db_host}:${var.db_port}/${var.db_name}"
  })
  
  # File operations
  ssh_public_key = file("~/.ssh/id_rsa.pub")
  config_content = file("${path.module}/config/app.conf")
  
  # Encoding operations
  encoded_script = base64encode(file("${path.module}/scripts/init.sh"))
  decoded_data   = base64decode(var.encoded_input)
  
  # JSON operations
  config_json = jsonencode({
    database = {
      host = var.db_host
      port = var.db_port
      name = var.db_name
    }
    features = {
      monitoring = var.enable_monitoring
      backup     = var.enable_backup
    }
  })
  
  parsed_config = jsondecode(var.json_config)
  
  # YAML operations
  yaml_config = yamlencode({
    apiVersion = "v1"
    kind       = "ConfigMap"
    metadata = {
      name = var.config_name
    }
    data = {
      "app.properties" = var.app_properties
    }
  })
  
  parsed_yaml = yamldecode(file("${path.module}/config.yaml"))
}
```

#### Collection Functions

```hcl
locals {
  # List operations
  instance_types     = ["t3.micro", "t3.small", "t3.medium"]
  selected_type      = element(local.instance_types, 1) # t3.small
  first_type         = local.instance_types[0]
  last_type          = local.instance_types[length(local.instance_types) - 1]
  
  # List manipulation
  extended_types     = concat(local.instance_types, ["t3.large", "t3.xlarge"])
  unique_zones       = distinct(["us-west-2a", "us-west-2b", "us-west-2a"])
  sorted_types       = sort(local.instance_types)
  reversed_types     = reverse(local.instance_types)
  
  # List filtering and transformation
  large_instances    = [for t in local.instance_types : t if can(regex("large|xlarge", t))]
  instance_configs   = [for t in local.instance_types : {
    type = t
    cost = t == "t3.micro" ? "low" : "high"
  }]
  
  # Map operations
  environments = {
    dev  = "development"
    stg  = "staging"
    prod = "production"
  }
  
  env_full_name = lookup(local.environments, var.env, "unknown")
  env_keys      = keys(local.environments)
  env_values    = values(local.environments)
  
  # Merge maps
  base_tags = {
    Terraform = "true"
    Owner     = "devops"
  }
  
  resource_tags = merge(local.base_tags, {
    Environment = var.environment
    Name        = var.resource_name
  })
  
  # Map transformation
  uppercase_envs = { for k, v in local.environments : k => upper(v) }
  
  # Set operations
  allowed_regions = toset(["us-east-1", "us-west-2", "eu-west-1"])
  region_list     = tolist(local.allowed_regions)
  
  # Type conversions
  string_to_number = tonumber(var.string_count)
  number_to_string = tostring(var.numeric_value)
  list_to_set      = toset(var.zone_list)
  
  # Conditional collections
  production_zones = var.environment == "prod" ? [
    "us-west-2a", "us-west-2b", "us-west-2c"
  ] : ["us-west-2a"]
  
  # For expressions with conditions
  subnet_tags = {
    for idx, subnet in aws_subnet.private : 
    subnet.id => {
      Name = "private-subnet-${idx + 1}"
      Type = "private"
      AZ   = subnet.availability_zone
    }
  }
  
  # Grouping and filtering
  instances_by_az = {
    for inst in var.instances :
    inst.availability_zone => inst...
    if inst.state == "running"
  }
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
  
  # Network calculations
  network_address = cidrhost(local.vpc_cidr, 0)      # 10.0.0.0
  first_host      = cidrhost(local.vpc_cidr, 1)      # 10.0.0.1
  gateway_ip      = cidrhost("10.0.1.0/24", 1)       # 10.0.1.1
  
  # CIDR operations
  subnet_netmask = cidrnetmask("10.0.1.0/24")         # 255.255.255.0
  
  # Subnet planning
  db_subnets = [
    for i in range(3) : cidrsubnet(local.vpc_cidr, 8, i + 201)
  ]
}
```

### Advanced HCL Features

#### Dynamic Blocks

```hcl
# Dynamic ingress rules
resource "aws_security_group" "web" {
  name_prefix = "web-"
  vpc_id      = aws_vpc.main.id
  
  dynamic "ingress" {
    for_each = var.ingress_rules
    
    content {
      from_port   = ingress.value.from_port
      to_port     = ingress.value.to_port
      protocol    = ingress.value.protocol
      cidr_blocks = ingress.value.cidr_blocks
      description = ingress.value.description
    }
  }
  
  dynamic "egress" {
    for_each = var.enable_egress ? [1] : []
    
    content {
      from_port   = 0
      to_port     = 0
      protocol    = "-1"
      cidr_blocks = ["0.0.0.0/0"]
    }
  }
}

# Dynamic block with nested iteration
resource "aws_instance" "web" {
  count = var.instance_count
  
  # ... other configuration
  
  dynamic "ebs_block_device" {
    for_each = var.additional_volumes
    
    content {
      device_name = ebs_block_device.value.device
      volume_size = ebs_block_device.value.size
      volume_type = ebs_block_device.value.type
      encrypted   = true
      
      tags = merge(local.common_tags, {
        Name = "${var.name}-volume-${ebs_block_device.key}"
      })
    }
  }
}

# Conditional dynamic blocks
resource "aws_db_instance" "main" {
  # ... basic configuration
  
  dynamic "restore_to_point_in_time" {
    for_each = var.restore_from_backup ? [1] : []
    
    content {
      restore_time                = var.restore_time
      source_db_instance_id      = var.source_db_instance_id
      use_latest_restorable_time = var.use_latest_restorable_time
    }
  }
}
```

#### Meta-Arguments

```hcl
# count meta-argument
resource "aws_instance" "web" {
  count = var.instance_count
  
  ami           = var.ami_id
  instance_type = var.instance_type
  subnet_id     = element(aws_subnet.public.*.id, count.index)
  
  tags = {
    Name = "web-server-${count.index + 1}"
  }
}

# for_each with map
resource "aws_iam_user" "users" {
  for_each = var.users
  
  name = each.key
  
  tags = {
    Role        = each.value.role
    Department  = each.value.department
  }
}

# for_each with set
resource "aws_security_group_rule" "egress" {
  for_each = toset(var.allowed_outbound_ports)
  
  type              = "egress"
  from_port         = each.value
  to_port           = each.value
  protocol          = "tcp"
  security_group_id = aws_security_group.main.id
  cidr_blocks       = ["0.0.0.0/0"]
}

# depends_on meta-argument
resource "aws_instance" "web" {
  # ... configuration
  
  depends_on = [
    aws_security_group.web,
    aws_key_pair.deployer,
    aws_iam_instance_profile.web
  ]
}

# lifecycle meta-argument
resource "aws_db_instance" "main" {
  # ... configuration
  
  lifecycle {
    create_before_destroy = true
    prevent_destroy      = true
    ignore_changes       = [
      password,
      final_snapshot_identifier
    ]
  }
}

# provider meta-argument
resource "aws_instance" "east" {
  provider = aws.us_east_1
  
  ami           = data.aws_ami.ubuntu_east.id
  instance_type = "t3.micro"
}
```

#### Variable Validation

```hcl
variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  
  validation {
    condition = can(regex("^[tm][0-9]", var.instance_type))
    error_message = "Instance type must start with 't' or 'm' followed by a number."
  }
  
  validation {
    condition = contains([
      "t3.micro", "t3.small", "t3.medium", "t3.large",
      "m5.large", "m5.xlarge", "m5.2xlarge"
    ], var.instance_type)
    error_message = "Instance type not in approved list."
  }
}

variable "cidr_block" {
  description = "CIDR block for VPC"
  type        = string
  
  validation {
    condition     = can(cidrhost(var.cidr_block, 0))
    error_message = "CIDR block must be a valid IPv4 CIDR."
  }
  
  validation {
    condition     = !contains(["0.0.0.0/0"], var.cidr_block)
    error_message = "CIDR block cannot be 0.0.0.0/0 for security reasons."
  }
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  
  validation {
    condition     = contains(keys(var.tags), "Environment")
    error_message = "Tags must include an Environment key."
  }
  
  validation {
    condition = alltrue([
      for tag_key in keys(var.tags) :
      can(regex("^[A-Za-z][A-Za-z0-9_-]*$", tag_key))
    ])
    error_message = "Tag keys must start with a letter and contain only letters, numbers, underscores, and hyphens."
  }
}

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
```

### Error Handling and Testing

```hcl
# Using can() function for error handling
locals {
  # Test if a value can be converted
  is_valid_number = can(tonumber(var.user_input))
  
  # Test if a regex matches
  is_valid_email = can(regex("^[\\w\\._%+-]+@[\\w\\.-]+\\.[A-Za-z]{2,}$", var.email))
  
  # Test if a CIDR is valid
  is_valid_cidr = can(cidrhost(var.cidr_block, 0))
  
  # Safe parsing with fallback
  parsed_json = can(jsondecode(var.json_string)) ? jsondecode(var.json_string) : {}
  
  # Safe list access
  first_zone = length(var.availability_zones) > 0 ? var.availability_zones[0] : "us-west-2a"
  
  # Safe map access
  instance_type = can(var.instance_types[var.environment]) ? var.instance_types[var.environment] : "t3.micro"
}

# Using try() function for error handling (Terraform 0.13+)
locals {
  # Try with fallback value
  safe_config = try(jsondecode(var.config_json), {
    default = "config"
  })
  
  # Try multiple expressions
  database_url = try(
    var.database_config.url,
    "postgresql://${var.database_config.host}:${var.database_config.port}/${var.database_config.name}",
    "postgresql://localhost:5432/defaultdb"
  )
  
  # Try with different data sources
  vpc_id = try(
    data.aws_vpc.existing[0].id,
    aws_vpc.new[0].id,
    var.default_vpc_id
  )
}
```

This comprehensive guide covers all essential aspects of HCL for effective Terraform configuration development, from basic syntax to advanced features and error handling patterns.
