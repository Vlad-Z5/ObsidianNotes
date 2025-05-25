## Core Workflow Commands

### Initialize (`terraform init`)

```bash
# Basic initialization
terraform init

# Initialize with backend configuration
terraform init -backend-config="bucket=my-terraform-state"

# Initialize without backend
terraform init -backend=false

# Upgrade providers
terraform init -upgrade

# Initialize specific directory
terraform init /path/to/terraform/config

# Initialize with plugin directory
terraform init -plugin-dir=/path/to/plugins

# Skip plugin installation
terraform init -get-plugins=false

# Reconfigure backend
terraform init -reconfigure

# Migrate state to new backend
terraform init -migrate-state
```

### Plan (`terraform plan`)

```bash
# Basic plan
terraform plan

# Save plan to file
terraform plan -out=tfplan

# Plan with specific variables
terraform plan -var="environment=production"

# Plan with variable file
terraform plan -var-file="production.tfvars"

# Plan with target resources
terraform plan -target=aws_instance.web

# Plan for destroy
terraform plan -destroy

# Detailed exit codes
terraform plan -detailed-exitcode

# Refresh state during plan
terraform plan -refresh=true

# Parallelism control
terraform plan -parallelism=10

# JSON output
terraform plan -json
```

### Apply (`terraform apply`)

```bash
# Interactive apply
terraform apply

# Apply saved plan
terraform apply tfplan

# Auto-approve (non-interactive)
terraform apply -auto-approve

# Apply with variables
terraform apply -var="instance_count=3"

# Apply specific targets
terraform apply -target=aws_instance.web

# Apply with parallelism
terraform apply -parallelism=5

# Apply with backup
terraform apply -backup=terraform.tfstate.backup

# Apply without state backup
terraform apply -backup="-"
```

### Destroy (`terraform destroy`)

```bash
# Interactive destroy
terraform destroy

# Auto-approve destroy
terraform destroy -auto-approve

# Destroy specific resources
terraform destroy -target=aws_instance.web

# Destroy with variables
terraform destroy -var-file="production.tfvars"

# Plan destroy first
terraform plan -destroy -out=destroy.tfplan
terraform apply destroy.tfplan
```

## State Management Commands

### State Inspection

```bash
# List resources in state
terraform state list

# Show resource details
terraform state show aws_instance.web

# Show all state
terraform show

# Show state in JSON
terraform show -json

# Pull remote state
terraform state pull

# Push state to remote
terraform state push terraform.tfstate
```

### State Manipulation

```bash
# Move resource in state
terraform state mv aws_instance.web aws_instance.web_server

# Remove resource from state
terraform state rm aws_instance.old_server

# Import existing resource
terraform import aws_instance.web i-1234567890abcdef0

# Replace provider address
terraform state replace-provider registry.terraform.io/hashicorp/aws hashicorp/aws

# Force unlock state
terraform force-unlock LOCK_ID
```

### Refresh and Sync

```bash
# Refresh state
terraform refresh

# Refresh with variables
terraform refresh -var-file="production.tfvars"

# Refresh specific targets
terraform refresh -target=aws_instance.web
```

## Validation and Formatting

### Validation

```bash
# Validate configuration
terraform validate

# Validate with JSON output
terraform validate -json

# Validate specific directory
terraform validate /path/to/config
```

### Formatting

```bash
# Format all files
terraform fmt

# Format specific file
terraform fmt main.tf

# Recursive format
terraform fmt -recursive

# Check formatting (exit code)
terraform fmt -check

# Show differences
terraform fmt -diff

# Write to stdout
terraform fmt -write=false
```

## Advanced Workflow Patterns

### Environment-Specific Workflows

```bash
# Development workflow
terraform workspace new development
terraform plan -var-file="environments/dev.tfvars"
terraform apply -var-file="environments/dev.tfvars"

# Staging workflow
terraform workspace select staging
terraform plan -var-file="environments/staging.tfvars" -out=staging.tfplan
terraform apply staging.tfplan

# Production workflow (with extra safety)
terraform workspace select production
terraform plan -var-file="environments/prod.tfvars" -out=prod.tfplan
# Review plan carefully
terraform apply prod.tfplan
```

### CI/CD Pipeline Workflow

```bash
#!/bin/bash
# Terraform CI/CD script

set -e

# Initialize
terraform init -input=false

# Validate
terraform validate

# Format check
terraform fmt -check=true -diff=true

# Plan
terraform plan -input=false -var-file="${ENVIRONMENT}.tfvars" -out=tfplan

# Apply (if approved)
if [ "$TERRAFORM_ACTION" = "apply" ]; then
    terraform apply -input=false tfplan
fi

# Output important values
terraform output -json > terraform-outputs.json
```

### Blue-Green Deployment Workflow

```bash
# Create new infrastructure
terraform workspace new blue
terraform apply -var="version=v2.0" -var="environment=blue"

# Test new infrastructure
# ... testing scripts ...

# Switch traffic
terraform apply -var="active_environment=blue"

# Destroy old infrastructure
terraform workspace select green
terraform destroy -auto-approve
```

### Disaster Recovery Workflow

```bash
# Backup current state
terraform state pull > backup-$(date +%Y%m%d-%H%M%S).tfstate

# Create disaster recovery plan
terraform plan -destroy -out=dr-destroy.tfplan
terraform plan -var-file="dr.tfvars" -out=dr-create.tfplan

# In case of disaster, restore from different region
terraform workspace new disaster-recovery
terraform init -backend-config="region=us-west-2"
terraform apply dr-create.tfplan
```

## Workspace Management

### Workspace Operations

```bash
# List workspaces
terraform workspace list

# Create new workspace
terraform workspace new production

# Select workspace
terraform workspace select development

# Show current workspace
terraform workspace show

# Delete workspace
terraform workspace delete old-environment
```

### Workspace-Aware Configuration

```hcl
# Using workspace in configuration
locals {
  workspace_configs = {
    development = {
      instance_type = "t3.micro"
      instance_count = 1
      environment = "dev"
    }
    staging = {
      instance_type = "t3.small"
      instance_count = 2
      environment = "staging"
    }
    production = {
      instance_type = "t3.large"
      instance_count = 3
      environment = "prod"
    }
  }
  
  config = local.workspace_configs[terraform.workspace]
}

resource "aws_instance" "web" {
  count         = local.config.instance_count
  instance_type = local.config.instance_type
  
  tags = {
    Name        = "${local.config.environment}-web-${count.index + 1}"
    Environment = local.config.environment
    Workspace   = terraform.workspace
  }
}
```

## Output and Data Extraction

### Output Commands

```bash
# Show all outputs
terraform output

# Show specific output
terraform output vpc_id

# Output in JSON format
terraform output -json

# Raw output (no quotes)
terraform output -raw private_key

# Save outputs to file
terraform output -json > outputs.json
```

### Graph Generation

```bash
# Generate dependency graph
terraform graph

# Generate graph in DOT format
terraform graph | dot -Tpng > graph.png

# Generate plan graph
terraform graph -plan=tfplan

# Generate graph for specific module
terraform graph -module=vpc
```

## Debugging and Troubleshooting

### Debug Logging

```bash
# Enable debug logging
export TF_LOG=DEBUG
terraform plan

# Log to file
export TF_LOG=DEBUG
export TF_LOG_PATH=terraform.log
terraform apply

# Different log levels
export TF_LOG=TRACE  # Most verbose
export TF_LOG=DEBUG
export TF_LOG=INFO
export TF_LOG=WARN
export TF_LOG=ERROR
```

### Provider Debug

```bash
# Debug specific provider
export TF_LOG_PROVIDER=DEBUG
terraform plan

# AWS provider debug
export AWS_SDK_LOAD_CONFIG=1
export TF_LOG=DEBUG
terraform plan
```

### Console and REPL

```bash
# Interactive console
terraform console

# Test expressions in console
> var.environment
> local.instance_count
> aws_instance.web[0].public_ip
> length(var.availability_zones)
```

## Automation and Scripting

### Automated Deployment Script

```bash
#!/bin/bash
# automated-deploy.sh

ENVIRONMENT=${1:-development}
ACTION=${2:-plan}

# Set variables
export TF_VAR_environment=$ENVIRONMENT
export TF_WORKSPACE=$ENVIRONMENT

# Initialize if needed
if [ ! -d ".terraform" ]; then
    terraform init
fi

# Select or create workspace
terraform workspace select $ENVIRONMENT || terraform workspace new $ENVIRONMENT

# Validate configuration
terraform validate
if [ $? -ne 0 ]; then
    echo "Validation failed"
    exit 1
fi

# Format check
terraform fmt -check=true
if [ $? -ne 0 ]; then
    echo "Format check failed"
    exit 1
fi

case $ACTION in
    plan)
        terraform plan -var-file="environments/${ENVIRONMENT}.tfvars"
        ;;
    apply)
        terraform plan -var-file="environments/${ENVIRONMENT}.tfvars" -out=tfplan
        echo "Review the plan above. Continue? (yes/no)"
        read confirm
        if [ "$confirm" = "yes" ]; then
            terraform apply tfplan
        fi
        ;;
    destroy)
        terraform plan -destroy -var-file="environments/${ENVIRONMENT}.tfvars"
        echo "This will destroy infrastructure. Continue? (yes/no)"
        read confirm
        if [ "$confirm" = "yes" ]; then
            terraform destroy -var-file="environments/${ENVIRONMENT}.tfvars"
        fi
        ;;
    *)
        echo "Usage: $0 <environment> <plan|apply|destroy>"
        exit 1
        ;;
esac
```

### Terraform Wrapper Functions

```bash
# Bash functions for common operations
tf_init() {
    terraform init -input=false
}

tf_plan() {
    local env=${1:-development}
    terraform workspace select $env
    terraform plan -var-file="environments/${env}.tfvars" -out=${env}.tfplan
}

tf_apply() {
    local env=${1:-development}
    if [ -f "${env}.tfplan" ]; then
        terraform apply ${env}.tfplan
    else
        echo "Plan file ${env}.tfplan not found. Run tf_plan first."
    fi
}

tf_output() {
    terraform output -json | jq '.'
}

tf_clean() {
    rm -f *.tfplan
    rm -f terraform.tfstate.backup.*
}
```

### GitOps Integration

```yaml
# .github/workflows/terraform.yml
name: Terraform

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  terraform:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Setup Terraform
      uses: hashicorp/setup-terraform@v1
      with:
        terraform_version: 1.6.0
    
    - name: Terraform Init
      run: terraform init
      
    - name: Terraform Format
      run: terraform fmt -check
      
    - name: Terraform Validate
      run: terraform validate
      
    - name: Terraform Plan
      run: terraform plan -no-color
      
    - name: Terraform Apply
      if: github.ref == 'refs/heads/main'
      run: terraform apply -auto-approve
```

## Performance Optimization

### Parallelism and Performance

```bash
# Control parallelism
terraform apply -parallelism=20

# Refresh only specific resources
terraform refresh -target=aws_instance.web

# Skip refresh during plan
terraform plan -refresh=false

# Use -compact-warnings
terraform plan -compact-warnings
```

### State Optimization

```bash
# Clean up state
terraform state list | grep 'module.old_module' | xargs terraform state rm

# Optimize state file
terraform state pull | terraform state push

# Use partial backend configuration
terraform init -backend-config=backend.hcl
```

### Resource Targeting

```bash
# Target specific resources for faster operations
terraform plan -target=module.vpc
terraform apply -target=aws_security_group.web
terraform destroy -target=aws_instance.test

# Multiple targets
terraform plan \
  -target=aws_instance.web \
  -target=aws_security_group.web \
  -target=module.database
```