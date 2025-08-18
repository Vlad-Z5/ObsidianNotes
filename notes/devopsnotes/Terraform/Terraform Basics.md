## Terraform Basics Comprehensive Guide

### What is Terraform?

Open-source Infrastructure as Code (IaC) tool by HashiCorp that enables you to define and provision infrastructure using declarative configuration files. Terraform supports multi-cloud environments, has a large ecosystem with wide support, and uses declarative HCL (HashiCorp Configuration Language) syntax.

### Key Benefits

- **Infrastructure as Code**: Version control your infrastructure configurations
- **Execution Plans**: Preview changes before applying with detailed diff output
- **Resource Graph**: Understands dependencies between resources for optimal provisioning order
- **Change Automation**: Complex changesets with minimal human interaction
- **Multi-Cloud**: Works with 3000+ providers across all major cloud platforms
- **State Management**: Tracks infrastructure state for drift detection and consistency
- **Immutable Infrastructure**: Promotes infrastructure replacement over modification
- **Collaboration**: Team-friendly with remote state and locking mechanisms

### Core Workflow

1. **Write** - Author infrastructure as code using HCL
2. **Plan** - Preview changes before applying with `terraform plan`
3. **Apply** - Provision reproducible infrastructure with `terraform apply`
4. **Destroy** - Clean up resources when no longer needed

### Installation and Setup

#### Installation Methods

```bash
# Download from terraform.io or use package managers

# MacOS with Homebrew
brew install terraform

# Windows with Chocolatey
choco install terraform

# Windows with Scoop
scoop bucket add hashicorp
scoop install terraform

# Ubuntu/Debian
wget -O- https://apt.releases.hashicorp.com/gpg | gpg --dearmor | sudo tee /usr/share/keyrings/hashicorp-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
sudo apt update && sudo apt install terraform

# CentOS/RHEL/Fedora
sudo yum install -y yum-utils
sudo yum-config-manager --add-repo https://rpm.releases.hashicorp.com/RHEL/hashicorp.repo
sudo yum -y install terraform

# Manual Installation (Linux/MacOS)
wget https://releases.hashicorp.com/terraform/1.6.0/terraform_1.6.0_linux_amd64.zip
unzip terraform_1.6.0_linux_amd64.zip
sudo mv terraform /usr/local/bin/

# Verify installation
terraform version
terraform -help
```

#### Version Management with tfenv

```bash
# Install tfenv (Terraform version manager)
git clone https://github.com/tfutils/tfenv.git ~/.tfenv
echo 'export PATH="$HOME/.tfenv/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# Install and use specific Terraform version
tfenv install 1.5.7
tfenv use 1.5.7
tfenv list
```

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

# Initialize without downloading plugins (offline)
terraform init -get-plugins=false

# Initialize with plugin directory
terraform init -plugin-dir=/path/to/plugins
```

**Common Use Cases**:
- Setting up new infrastructure repositories
- Onboarding team members to existing projects
- Switching between different backend configurations
- Updating provider versions
- Migrating state backends

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

# Plan with inline variables
terraform plan -var="instance_type=t3.large"

# Plan with target resource
terraform plan -target=aws_instance.web

# Plan destroy
terraform plan -destroy

# Detailed exit codes
terraform plan -detailed-exitcode
# Exit codes: 0 = no changes, 1 = error, 2 = changes present

# Refresh state before planning
terraform plan -refresh=true

# Generate machine-readable output
terraform plan -json
```

**Best Practices**:
- Always run plan before apply in production
- Save plans to files for audit trails
- Use in CI/CD pipelines for automated validation
- Review plans in pull requests
- Use `-detailed-exitcode` in automation

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

# Apply with variable overrides
terraform apply -var="environment=staging"

# Apply with variable file
terraform apply -var-file="staging.tfvars"

# Apply with parallelism control
terraform apply -parallelism=5

# Apply with refresh disabled
terraform apply -refresh=false
```

**Production Considerations**:
- Implement approval workflows
- Monitor apply operations
- Have rollback plans ready
- Use saved plans for consistency
- Set up proper logging and auditing

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

# Destroy with variable overrides
terraform destroy -var="environment=dev"
```

**Safety Measures**:
- Use `prevent_destroy` lifecycle rule
- Implement destroy approval processes
- Backup critical data before destruction
- Use separate destroy pipelines
- Verify target environments

### terraform validate

Validates the configuration files for syntax and internal consistency.

**DevOps Responsibility**: Quality assurance step in development workflow.

```bash
# Validate current directory
terraform validate

# Validate specific directory
terraform validate /path/to/config

# JSON output for automation
terraform validate -json
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

# Format specific file
terraform fmt main.tf

# Write formatted files to stdout
terraform fmt -write=false
```

**Automation**:
- Pre-commit hooks integration
- CI/CD formatting checks
- IDE integration
- Team coding standards enforcement

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

# Show specific state file
terraform show -state=backup.tfstate
```

### terraform output

Displays output values from the state file.

```bash
# Show all outputs
terraform output

# Show specific output
terraform output vpc_id

# JSON format
terraform output -json

# Raw format (no quotes)
terraform output -raw database_password
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

### terraform graph

Generate visual representation of configuration or execution plan.

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

## Basic Configuration Structure

### Terraform Configuration Files

```hcl
# main.tf - Primary configuration
terraform {
  required_version = ">= 1.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

resource "aws_instance" "web" {
  ami           = var.ami_id
  instance_type = var.instance_type
  
  tags = {
    Name = "web-server"
    Environment = var.environment
  }
}
```

```hcl
# variables.tf - Variable definitions
variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-west-2"
}

variable "ami_id" {
  description = "AMI ID for EC2 instance"
  type        = string
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.micro"
}

variable "environment" {
  description = "Environment name"
  type        = string
  
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}
```

```hcl
# outputs.tf - Output definitions
output "instance_id" {
  description = "ID of the EC2 instance"
  value       = aws_instance.web.id
}

output "instance_public_ip" {
  description = "Public IP address of the instance"
  value       = aws_instance.web.public_ip
}

output "instance_private_ip" {
  description = "Private IP address of the instance"
  value       = aws_instance.web.private_ip
  sensitive   = true
}
```

```hcl
# terraform.tfvars - Variable values
aws_region    = "us-west-2"
ami_id        = "ami-0c02fb55956c7d316"
instance_type = "t3.small"
environment   = "dev"
```

### File Naming Conventions

- `main.tf` - Primary configuration
- `variables.tf` - Variable definitions
- `outputs.tf` - Output definitions
- `providers.tf` - Provider configurations
- `versions.tf` - Version constraints
- `locals.tf` - Local values
- `data.tf` - Data sources
- `terraform.tfvars` - Variable values (not versioned)
- `*.auto.tfvars` - Auto-loaded variable files

## Getting Started Example

### Simple AWS EC2 Instance

1. **Create project directory**:
```bash
mkdir terraform-example
cd terraform-example
```

2. **Create main.tf**:
```hcl
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "us-west-2"
}

resource "aws_instance" "example" {
  ami           = "ami-0c02fb55956c7d316"
  instance_type = "t3.micro"
  
  tags = {
    Name = "terraform-example"
  }
}

output "instance_ip" {
  value = aws_instance.example.public_ip
}
```

3. **Initialize and apply**:
```bash
# Set AWS credentials
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"

# Initialize Terraform
terraform init

# Validate configuration
terraform validate

# Plan deployment
terraform plan

# Apply configuration
terraform apply

# Show outputs
terraform output

# Clean up resources
terraform destroy
```

## Development Best Practices

### Project Organization

```
terraform-project/
├── environments/
│   ├── dev/
│   ├── staging/
│   └── prod/
├── modules/
│   ├── vpc/
│   ├── compute/
│   └── database/
├── shared/
│   ├── data.tf
│   └── locals.tf
└── scripts/
    ├── deploy.sh
    └── validate.sh
```

### Code Quality

```bash
# Format code
terraform fmt -recursive

# Validate syntax
terraform validate

# Security scanning
tfsec .
checkov -d .

# Linting
tflint
```

### Common Patterns

1. **Use locals for computed values**:
```hcl
locals {
  common_tags = {
    Environment = var.environment
    Project     = var.project_name
    ManagedBy   = "terraform"
  }
}
```

2. **Input validation**:
```hcl
variable "environment" {
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Invalid environment specified."
  }
}
```

3. **Resource naming**:
```hcl
resource "aws_instance" "web" {
  tags = {
    Name = "${var.environment}-web-server"
  }
}
```

### Essential Commands Summary

| Command | Purpose | Usage |
|---------|---------|-------|
| `terraform init` | Initialize working directory | First command in new project |
| `terraform plan` | Preview changes | Before applying changes |
| `terraform apply` | Apply changes | Deploy infrastructure |
| `terraform destroy` | Remove all resources | Clean up environment |
| `terraform validate` | Check syntax | During development |
| `terraform fmt` | Format code | Code consistency |
| `terraform show` | Display state/plan | Inspection and debugging |
| `terraform output` | Show output values | Retrieve generated values |

This comprehensive guide covers the essential Terraform basics for DevOps practitioners, from installation to core commands and basic configuration patterns.
