# Terraform Production Infrastructure Patterns

**Production Infrastructure Patterns** provide battle-tested, scalable, and maintainable Terraform configurations for real-world enterprise environments with proper security, monitoring, and operational practices.

## Multi-Environment Architecture

### Environment Separation Strategy

#### Directory Structure for Production
```
terraform-infrastructure/
├── environments/
│   ├── dev/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   ├── terraform.tfvars
│   │   └── backend.tf
│   ├── staging/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   ├── terraform.tfvars
│   │   └── backend.tf
│   └── prod/
│       ├── main.tf
│       ├── variables.tf
│       ├── terraform.tfvars
│       └── backend.tf
├── modules/
│   ├── vpc/
│   ├── eks/
│   ├── rds/
│   ├── monitoring/
│   └── security/
├── shared/
│   ├── backend-config/
│   ├── provider-config/
│   └── common-variables/
└── scripts/
    ├── deploy.sh
    ├── validate.sh
    └── destroy.sh
```

#### Complete Environment Configuration

**environments/prod/main.tf:**
```hcl
terraform {
  required_version = ">= 1.5"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.23"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.10"
    }
  }

  backend "s3" {
    bucket         = "company-terraform-state-prod"
    key            = "infrastructure/terraform.tfstate"
    region         = "us-west-2"
    encrypt        = true
    dynamodb_table = "terraform-state-lock-prod"

    # Workspace-based state separation
    workspace_key_prefix = "workspaces"
  }
}

# Provider configurations
provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Environment   = "production"
      ManagedBy     = "terraform"
      Project       = var.project_name
      CostCenter    = var.cost_center
      Owner         = var.owner_team
      LastUpdated   = timestamp()
    }
  }
}

# Data sources for existing resources
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}
data "aws_availability_zones" "available" {
  state = "available"
}

# Local values for computed configurations
locals {
  account_id = data.aws_caller_identity.current.account_id
  region     = data.aws_region.current.name

  # Environment-specific configurations
  environment_config = {
    production = {
      instance_types = ["m5.large", "m5.xlarge"]
      min_size       = 3
      max_size       = 20
      desired_size   = 5
    }
    staging = {
      instance_types = ["t3.medium", "t3.large"]
      min_size       = 1
      max_size       = 5
      desired_size   = 2
    }
    development = {
      instance_types = ["t3.small"]
      min_size       = 1
      max_size       = 3
      desired_size   = 1
    }
  }

  # Common tags merged with environment-specific tags
  common_tags = merge(var.common_tags, {
    Environment = var.environment
    Region      = local.region
    AccountId   = local.account_id
  })
}

# VPC Module
module "vpc" {
  source = "../../modules/vpc"

  name               = "${var.project_name}-${var.environment}"
  cidr               = var.vpc_cidr
  azs                = data.aws_availability_zones.available.names
  private_subnets    = var.private_subnet_cidrs
  public_subnets     = var.public_subnet_cidrs
  database_subnets   = var.database_subnet_cidrs

  enable_nat_gateway   = true
  enable_vpn_gateway   = false
  enable_dns_hostnames = true
  enable_dns_support   = true

  # VPC Flow Logs for security monitoring
  enable_flow_log                      = true
  create_flow_log_cloudwatch_log_group = true
  create_flow_log_cloudwatch_iam_role  = true
  flow_log_destination_type            = "cloud-watch-logs"

  tags = local.common_tags
}

# Security Groups Module
module "security_groups" {
  source = "../../modules/security"

  vpc_id      = module.vpc.vpc_id
  environment = var.environment

  # Application-specific security group rules
  application_ports = var.application_ports
  database_ports    = var.database_ports

  tags = local.common_tags
}

# EKS Cluster Module
module "eks" {
  source = "../../modules/eks"

  cluster_name    = "${var.project_name}-${var.environment}"
  cluster_version = var.kubernetes_version

  vpc_id          = module.vpc.vpc_id
  subnet_ids      = module.vpc.private_subnets
  control_plane_subnet_ids = module.vpc.intra_subnets

  # Cluster endpoint configuration
  cluster_endpoint_private_access = true
  cluster_endpoint_public_access  = true
  cluster_endpoint_public_access_cidrs = var.allowed_cidr_blocks

  # Cluster encryption
  cluster_encryption_config = [
    {
      provider_key_arn = module.kms.key_arn
      resources        = ["secrets"]
    }
  ]

  # Enable logging
  cluster_enabled_log_types = ["api", "audit", "authenticator", "controllerManager", "scheduler"]

  # Node groups
  node_groups = {
    main = {
      name_prefix      = "main"
      instance_types   = local.environment_config[var.environment].instance_types
      capacity_type    = "ON_DEMAND"

      min_size         = local.environment_config[var.environment].min_size
      max_size         = local.environment_config[var.environment].max_size
      desired_size     = local.environment_config[var.environment].desired_size

      disk_size        = 50
      ami_type         = "AL2_x86_64"

      k8s_labels = {
        Environment = var.environment
        NodeGroup   = "main"
      }

      update_config = {
        max_unavailable_percentage = 25
      }
    }

    spot = {
      name_prefix      = "spot"
      instance_types   = ["t3.medium", "t3.large", "m5.large"]
      capacity_type    = "SPOT"

      min_size         = 0
      max_size         = 10
      desired_size     = 2

      k8s_labels = {
        Environment = var.environment
        NodeGroup   = "spot"
      }

      taints = {
        spot = {
          key    = "spot"
          value  = "true"
          effect = "NO_SCHEDULE"
        }
      }
    }
  }

  tags = local.common_tags
}

# RDS Database Module
module "rds" {
  source = "../../modules/rds"

  identifier     = "${var.project_name}-${var.environment}-db"
  engine         = "postgres"
  engine_version = "14.9"
  instance_class = var.db_instance_class

  allocated_storage     = var.db_allocated_storage
  max_allocated_storage = var.db_max_allocated_storage
  storage_type          = "gp3"
  storage_encrypted     = true
  kms_key_id           = module.kms.key_arn

  db_name  = var.db_name
  username = var.db_username
  password = var.db_password # Should come from AWS Secrets Manager

  vpc_security_group_ids = [module.security_groups.database_sg_id]
  db_subnet_group_name   = module.vpc.database_subnet_group

  backup_retention_period = var.environment == "production" ? 30 : 7
  backup_window          = "03:00-04:00"
  maintenance_window     = "sun:04:00-sun:05:00"

  enabled_cloudwatch_logs_exports = ["postgresql"]
  monitoring_interval             = 60
  monitoring_role_arn            = aws_iam_role.rds_enhanced_monitoring.arn
  performance_insights_enabled   = true

  deletion_protection = var.environment == "production" ? true : false
  skip_final_snapshot = var.environment == "production" ? false : true

  tags = local.common_tags
}

# KMS Module for encryption
module "kms" {
  source = "../../modules/kms"

  description = "KMS key for ${var.project_name} ${var.environment}"
  key_usage   = "ENCRYPT_DECRYPT"

  key_administrators = var.kms_key_administrators
  key_users         = var.kms_key_users

  tags = local.common_tags
}

# Monitoring and Logging Module
module "monitoring" {
  source = "../../modules/monitoring"

  environment    = var.environment
  cluster_name   = module.eks.cluster_id
  vpc_id         = module.vpc.vpc_id

  # CloudWatch Log Groups
  log_retention_in_days = var.environment == "production" ? 90 : 30

  # SNS topics for alerts
  notification_endpoints = var.notification_endpoints

  tags = local.common_tags
}

# Application Load Balancer
resource "aws_lb" "main" {
  name               = "${var.project_name}-${var.environment}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [module.security_groups.alb_sg_id]
  subnets           = module.vpc.public_subnets

  enable_deletion_protection = var.environment == "production" ? true : false

  access_logs {
    bucket  = aws_s3_bucket.alb_logs.bucket
    prefix  = "alb-logs"
    enabled = true
  }

  tags = local.common_tags
}

# S3 bucket for ALB access logs
resource "aws_s3_bucket" "alb_logs" {
  bucket        = "${var.project_name}-${var.environment}-alb-logs-${random_id.bucket_suffix.hex}"
  force_destroy = var.environment != "production"

  tags = local.common_tags
}

resource "aws_s3_bucket_lifecycle_configuration" "alb_logs" {
  bucket = aws_s3_bucket.alb_logs.id

  rule {
    id     = "alb_logs_lifecycle"
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
      days = var.environment == "production" ? 365 : 90
    }
  }
}

# Random ID for unique bucket naming
resource "random_id" "bucket_suffix" {
  byte_length = 4
}

# IAM role for RDS enhanced monitoring
resource "aws_iam_role" "rds_enhanced_monitoring" {
  name = "${var.project_name}-${var.environment}-rds-monitoring-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "monitoring.rds.amazonaws.com"
        }
      }
    ]
  })

  tags = local.common_tags
}

resource "aws_iam_role_policy_attachment" "rds_enhanced_monitoring" {
  role       = aws_iam_role.rds_enhanced_monitoring.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonRDSEnhancedMonitoringRole"
}
```

**environments/prod/variables.tf:**
```hcl
# Project Configuration
variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "myapp"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "production"

  validation {
    condition     = contains(["development", "staging", "production"], var.environment)
    error_message = "Environment must be one of: development, staging, production."
  }
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-west-2"
}

variable "cost_center" {
  description = "Cost center for billing"
  type        = string
}

variable "owner_team" {
  description = "Team responsible for the infrastructure"
  type        = string
}

# Network Configuration
variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"

  validation {
    condition     = can(cidrhost(var.vpc_cidr, 0))
    error_message = "VPC CIDR must be a valid IPv4 CIDR block."
  }
}

variable "private_subnet_cidrs" {
  description = "CIDR blocks for private subnets"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for public subnets"
  type        = list(string)
  default     = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]
}

variable "database_subnet_cidrs" {
  description = "CIDR blocks for database subnets"
  type        = list(string)
  default     = ["10.0.201.0/24", "10.0.202.0/24", "10.0.203.0/24"]
}

variable "allowed_cidr_blocks" {
  description = "CIDR blocks allowed to access the cluster endpoint"
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

# Kubernetes Configuration
variable "kubernetes_version" {
  description = "Kubernetes version"
  type        = string
  default     = "1.27"
}

# Database Configuration
variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.micro"
}

variable "db_allocated_storage" {
  description = "Initial allocated storage in GB"
  type        = number
  default     = 20
}

variable "db_max_allocated_storage" {
  description = "Maximum allocated storage in GB"
  type        = number
  default     = 100
}

variable "db_name" {
  description = "Database name"
  type        = string
  default     = "myapp"
}

variable "db_username" {
  description = "Database username"
  type        = string
  default     = "admin"
}

variable "db_password" {
  description = "Database password"
  type        = string
  sensitive   = true
}

# Security Configuration
variable "kms_key_administrators" {
  description = "ARNs of KMS key administrators"
  type        = list(string)
  default     = []
}

variable "kms_key_users" {
  description = "ARNs of KMS key users"
  type        = list(string)
  default     = []
}

variable "application_ports" {
  description = "Application ports to allow"
  type        = list(number)
  default     = [80, 443, 8080]
}

variable "database_ports" {
  description = "Database ports to allow"
  type        = list(number)
  default     = [5432]
}

# Monitoring Configuration
variable "notification_endpoints" {
  description = "SNS notification endpoints"
  type = object({
    email = list(string)
    slack = list(string)
  })
  default = {
    email = []
    slack = []
  }
}

# Common Tags
variable "common_tags" {
  description = "Common tags to apply to all resources"
  type        = map(string)
  default = {
    Terraform = "true"
  }
}
```

**environments/prod/terraform.tfvars:**
```hcl
# Project Configuration
project_name = "mycompany-app"
environment  = "production"
aws_region   = "us-west-2"
cost_center  = "engineering"
owner_team   = "platform-team"

# Network Configuration
vpc_cidr = "10.0.0.0/16"
private_subnet_cidrs = [
  "10.0.1.0/24",   # us-west-2a
  "10.0.2.0/24",   # us-west-2b
  "10.0.3.0/24"    # us-west-2c
]
public_subnet_cidrs = [
  "10.0.101.0/24", # us-west-2a
  "10.0.102.0/24", # us-west-2b
  "10.0.103.0/24"  # us-west-2c
]
database_subnet_cidrs = [
  "10.0.201.0/24", # us-west-2a
  "10.0.202.0/24", # us-west-2b
  "10.0.203.0/24"  # us-west-2c
]

# Kubernetes Configuration
kubernetes_version = "1.27"

# Database Configuration
db_instance_class       = "db.r5.large"
db_allocated_storage    = 100
db_max_allocated_storage = 1000
db_name                 = "myapp_prod"
db_username            = "admin"
# db_password should be set via environment variable or secrets manager

# Security Configuration
allowed_cidr_blocks = [
  "10.0.0.0/8",     # Internal network
  "172.16.0.0/12",  # Internal network
  "192.168.0.0/16"  # Internal network
]

kms_key_administrators = [
  "arn:aws:iam::123456789012:role/TerraformExecutionRole",
  "arn:aws:iam::123456789012:user/admin"
]

# Monitoring Configuration
notification_endpoints = {
  email = [
    "alerts@company.com",
    "platform-team@company.com"
  ]
  slack = [
    "https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX"
  ]
}

# Common Tags
common_tags = {
  Project     = "mycompany-app"
  Environment = "production"
  Owner       = "platform-team"
  Backup      = "required"
  Compliance  = "required"
}
```

### Workspace Management

#### Workspace Strategy
```bash
#!/bin/bash
# scripts/manage-workspaces.sh

set -euo pipefail

ENVIRONMENT=${1:-""}
ACTION=${2:-""}

if [[ -z "$ENVIRONMENT" || -z "$ACTION" ]]; then
    echo "Usage: $0 <environment> <action>"
    echo "Environments: dev, staging, prod"
    echo "Actions: create, select, delete, list, plan, apply, destroy"
    exit 1
fi

# Validate environment
case $ENVIRONMENT in
    dev|staging|prod)
        echo "Managing environment: $ENVIRONMENT"
        ;;
    *)
        echo "Invalid environment. Use: dev, staging, or prod"
        exit 1
        ;;
esac

# Change to environment directory
cd "environments/$ENVIRONMENT"

case $ACTION in
    create)
        echo "Creating workspace: $ENVIRONMENT"
        terraform workspace new "$ENVIRONMENT" || echo "Workspace already exists"
        terraform workspace select "$ENVIRONMENT"
        ;;
    select)
        echo "Selecting workspace: $ENVIRONMENT"
        terraform workspace select "$ENVIRONMENT"
        ;;
    delete)
        echo "Deleting workspace: $ENVIRONMENT"
        read -p "Are you sure you want to delete workspace $ENVIRONMENT? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            terraform workspace select default
            terraform workspace delete "$ENVIRONMENT"
        fi
        ;;
    list)
        echo "Available workspaces:"
        terraform workspace list
        ;;
    plan)
        echo "Planning deployment for: $ENVIRONMENT"
        terraform workspace select "$ENVIRONMENT"
        terraform init -upgrade
        terraform plan -var-file="terraform.tfvars" -out="$ENVIRONMENT.tfplan"
        ;;
    apply)
        echo "Applying deployment for: $ENVIRONMENT"
        terraform workspace select "$ENVIRONMENT"
        if [[ -f "$ENVIRONMENT.tfplan" ]]; then
            terraform apply "$ENVIRONMENT.tfplan"
            rm -f "$ENVIRONMENT.tfplan"
        else
            echo "No plan file found. Run plan first."
            exit 1
        fi
        ;;
    destroy)
        echo "Destroying infrastructure for: $ENVIRONMENT"
        read -p "Are you sure you want to destroy $ENVIRONMENT? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            terraform workspace select "$ENVIRONMENT"
            terraform plan -destroy -var-file="terraform.tfvars" -out="destroy-$ENVIRONMENT.tfplan"
            terraform apply "destroy-$ENVIRONMENT.tfplan"
            rm -f "destroy-$ENVIRONMENT.tfplan"
        fi
        ;;
    *)
        echo "Invalid action. Use: create, select, delete, list, plan, apply, destroy"
        exit 1
        ;;
esac
```

## Advanced Module Patterns

### Reusable VPC Module

**modules/vpc/main.tf:**
```hcl
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.0"
    }
  }
}

# VPC
resource "aws_vpc" "this" {
  cidr_block           = var.cidr
  enable_dns_hostnames = var.enable_dns_hostnames
  enable_dns_support   = var.enable_dns_support

  tags = merge(var.tags, {
    Name = var.name
  })
}

# Internet Gateway
resource "aws_internet_gateway" "this" {
  count  = length(var.public_subnets) > 0 ? 1 : 0
  vpc_id = aws_vpc.this.id

  tags = merge(var.tags, {
    Name = "${var.name}-igw"
  })
}

# Public Subnets
resource "aws_subnet" "public" {
  count = length(var.public_subnets)

  vpc_id                  = aws_vpc.this.id
  cidr_block              = var.public_subnets[count.index]
  availability_zone       = length(regexall("^[a-z]{2}-", element(var.azs, count.index))) > 0 ? element(var.azs, count.index) : null
  map_public_ip_on_launch = var.map_public_ip_on_launch

  tags = merge(var.tags, {
    Name = "${var.name}-public-${element(var.azs, count.index)}"
    Type = "Public"
  })
}

# Private Subnets
resource "aws_subnet" "private" {
  count = length(var.private_subnets)

  vpc_id            = aws_vpc.this.id
  cidr_block        = var.private_subnets[count.index]
  availability_zone = length(regexall("^[a-z]{2}-", element(var.azs, count.index))) > 0 ? element(var.azs, count.index) : null

  tags = merge(var.tags, {
    Name = "${var.name}-private-${element(var.azs, count.index)}"
    Type = "Private"
  })
}

# Database Subnets
resource "aws_subnet" "database" {
  count = length(var.database_subnets)

  vpc_id            = aws_vpc.this.id
  cidr_block        = var.database_subnets[count.index]
  availability_zone = length(regexall("^[a-z]{2}-", element(var.azs, count.index))) > 0 ? element(var.azs, count.index) : null

  tags = merge(var.tags, {
    Name = "${var.name}-db-${element(var.azs, count.index)}"
    Type = "Database"
  })
}

# Database Subnet Group
resource "aws_db_subnet_group" "database" {
  count = length(var.database_subnets) > 0 ? 1 : 0

  name       = "${var.name}-db-subnet-group"
  subnet_ids = aws_subnet.database[*].id

  tags = merge(var.tags, {
    Name = "${var.name}-db-subnet-group"
  })
}

# Elastic IPs for NAT Gateways
resource "aws_eip" "nat" {
  count = var.enable_nat_gateway ? (var.single_nat_gateway ? 1 : length(var.private_subnets)) : 0

  domain = "vpc"

  depends_on = [aws_internet_gateway.this]

  tags = merge(var.tags, {
    Name = "${var.name}-nat-${count.index + 1}"
  })
}

# NAT Gateways
resource "aws_nat_gateway" "this" {
  count = var.enable_nat_gateway ? (var.single_nat_gateway ? 1 : length(var.private_subnets)) : 0

  allocation_id = aws_eip.nat[count.index].id
  subnet_id     = aws_subnet.public[var.single_nat_gateway ? 0 : count.index].id

  depends_on = [aws_internet_gateway.this]

  tags = merge(var.tags, {
    Name = "${var.name}-nat-${count.index + 1}"
  })
}

# Public Route Table
resource "aws_route_table" "public" {
  count = length(var.public_subnets) > 0 ? 1 : 0

  vpc_id = aws_vpc.this.id

  tags = merge(var.tags, {
    Name = "${var.name}-public"
  })
}

# Public Routes
resource "aws_route" "public_internet_gateway" {
  count = length(var.public_subnets) > 0 ? 1 : 0

  route_table_id         = aws_route_table.public[0].id
  destination_cidr_block = "0.0.0.0/0"
  gateway_id             = aws_internet_gateway.this[0].id
}

# Public Route Table Associations
resource "aws_route_table_association" "public" {
  count = length(var.public_subnets)

  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public[0].id
}

# Private Route Tables
resource "aws_route_table" "private" {
  count = length(var.private_subnets)

  vpc_id = aws_vpc.this.id

  tags = merge(var.tags, {
    Name = "${var.name}-private-${element(var.azs, count.index)}"
  })
}

# Private Routes
resource "aws_route" "private_nat_gateway" {
  count = var.enable_nat_gateway ? length(var.private_subnets) : 0

  route_table_id         = aws_route_table.private[count.index].id
  destination_cidr_block = "0.0.0.0/0"
  nat_gateway_id         = aws_nat_gateway.this[var.single_nat_gateway ? 0 : count.index].id
}

# Private Route Table Associations
resource "aws_route_table_association" "private" {
  count = length(var.private_subnets)

  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private[count.index].id
}

# Database Route Table
resource "aws_route_table" "database" {
  count = length(var.database_subnets) > 0 ? 1 : 0

  vpc_id = aws_vpc.this.id

  tags = merge(var.tags, {
    Name = "${var.name}-database"
  })
}

# Database Route Table Associations
resource "aws_route_table_association" "database" {
  count = length(var.database_subnets)

  subnet_id      = aws_subnet.database[count.index].id
  route_table_id = aws_route_table.database[0].id
}

# VPC Flow Logs
resource "aws_flow_log" "this" {
  count = var.enable_flow_log ? 1 : 0

  iam_role_arn    = var.flow_log_destination_type == "cloud-watch-logs" ? aws_iam_role.flow_log[0].arn : null
  log_destination = var.flow_log_destination_type == "cloud-watch-logs" ? aws_cloudwatch_log_group.flow_log[0].arn : var.flow_log_destination_arn
  log_format      = var.flow_log_log_format
  traffic_type    = var.flow_log_traffic_type
  vpc_id          = aws_vpc.this.id

  destination_options {
    file_format        = var.flow_log_file_format
    hive_compatible_partitions = var.flow_log_hive_compatible_partitions
    per_hour_partition = var.flow_log_per_hour_partition
  }

  tags = merge(var.tags, {
    Name = "${var.name}-flow-log"
  })
}

# CloudWatch Log Group for VPC Flow Logs
resource "aws_cloudwatch_log_group" "flow_log" {
  count = var.enable_flow_log && var.create_flow_log_cloudwatch_log_group ? 1 : 0

  name              = "/aws/vpc/flow-logs/${var.name}"
  retention_in_days = var.flow_log_cloudwatch_log_group_retention_in_days

  tags = var.tags
}

# IAM Role for VPC Flow Logs
resource "aws_iam_role" "flow_log" {
  count = var.enable_flow_log && var.flow_log_destination_type == "cloud-watch-logs" && var.create_flow_log_cloudwatch_iam_role ? 1 : 0

  name = "${var.name}-flow-log-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "vpc-flow-logs.amazonaws.com"
        }
      }
    ]
  })

  tags = var.tags
}

# IAM Role Policy for VPC Flow Logs
resource "aws_iam_role_policy" "flow_log" {
  count = var.enable_flow_log && var.flow_log_destination_type == "cloud-watch-logs" && var.create_flow_log_cloudwatch_iam_role ? 1 : 0

  name = "${var.name}-flow-log-policy"
  role = aws_iam_role.flow_log[0].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "logs:DescribeLogGroups",
          "logs:DescribeLogStreams"
        ]
        Effect   = "Allow"
        Resource = "*"
      }
    ]
  })
}
```

This comprehensive Terraform Production Infrastructure Patterns file provides enterprise-ready configurations with proper environment separation, security hardening, monitoring, and operational best practices that can be immediately implemented in production environments.