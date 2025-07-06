## Core Workflow Commands

### Initialize (`terraform init`)

```bash
terraform init # Basic initialization
terraform init -backend-config="bucket=my-terraform-state" # Initialize with backend configuration
terraform init -backend=false # Initialize without backend
terraform init -upgrade # Upgrade providers
terraform init /path/to/terraform/config # Initialize specific directory
terraform init -plugin-dir=/path/to/plugins # Initialize with plugin directory
terraform init -get-plugins=false # Skip plugin installation
terraform init -reconfigure # Reconfigure backend
terraform init -migrate-state # Migrate state to new backend
```

### Plan (`terraform plan`)

```bash
terraform plan # Basic plan
terraform plan -out=tfplan # Save plan to file
terraform plan -var="environment=production" # Plan with specific variables
terraform plan -var-file="production.tfvars" # Plan with variable file
terraform plan -target=aws_instance.web # Plan with target resources
terraform plan -destroy # Plan for destroy
terraform plan -detailed-exitcode # Detailed exit codes
terraform plan -refresh=true # Refresh state during plan
terraform plan -parallelism=10 # Parallelism control
terraform plan -json # JSON output
```

### Apply (`terraform apply`)

```bash
terraform apply # Interactive apply
terraform apply tfplan # Apply saved plan
terraform apply -auto-approve # Auto-approve (non-interactive)
terraform apply -var="instance_count=3" # Apply with variables
terraform apply -target=aws_instance.web # Apply specific targets
terraform apply -parallelism=5 # Apply with parallelism
terraform apply -backup=terraform.tfstate.backup # Apply with backup
terraform apply -backup="-" # Apply without state backup
```

### Destroy (`terraform destroy`)

```bash
terraform destroy # Interactive destroy
terraform destroy -auto-approve # Auto-approve destroy
terraform destroy -target=aws_instance.web # Destroy specific resources
terraform destroy -var-file="production.tfvars" # Destroy with variables
terraform plan -destroy -out=destroy.tfplan # Plan destroy first
terraform apply destroy.tfplan # Apply destroy plan
```

## State Management Commands

### State Inspection

```bash
terraform state list # List resources in state
terraform state show aws_instance.web # Show resource details
terraform show # Show all state
terraform show -json # Show state in JSON
terraform state pull # Pull remote state
terraform state push terraform.tfstate # Push state to remote
```

### State Manipulation

```bash
terraform state mv aws_instance.web aws_instance.web_server # Move resource in state
terraform state rm aws_instance.old_server # Remove resource from state
terraform import aws_instance.web i-1234567890abcdef0 # Import existing resource
terraform state replace-provider registry.terraform.io/hashicorp/aws hashicorp/aws # Replace provider address
terraform force-unlock LOCK_ID # Force unlock state
```

### Refresh and Sync

```bash
terraform refresh # Refresh state
terraform refresh -var-file="production.tfvars" # Refresh with variables
terraform refresh -target=aws_instance.web # Refresh specific targets
```

## Validation and Formatting

### Validation

```bash
terraform validate # Validate configuration
terraform validate -json # Validate with JSON output
terraform validate /path/to/config # Validate specific directory
```

### Formatting

```bash
terraform fmt # Format all files
terraform fmt main.tf # Format specific file
terraform fmt -recursive # Recursive format
terraform fmt -check # Check formatting (exit code)
terraform fmt -diff # Show differences
terraform fmt -write=false # Write to stdout
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
set -e

terraform init -input=false # Initialize
terraform validate # Validate
terraform fmt -check=true -diff=true # Format check
terraform plan -input=false -var-file="${ENVIRONMENT}.tfvars" -out=tfplan # Plan

if [ "$TERRAFORM_ACTION" = "apply" ]; then
    terraform apply -input=false tfplan # Apply (if approved)
fi

terraform output -json > terraform-outputs.json # Output important values
```

### Blue-Green Deployment Workflow

```bash
terraform workspace new blue # Create new infrastructure
terraform apply -var="version=v2.0" -var="environment=blue"
# Test new infrastructure
terraform apply -var="active_environment=blue" # Switch traffic
terraform workspace select green
terraform destroy -auto-approve # Destroy old infrastructure
```

### Disaster Recovery Workflow

```bash
terraform state pull > backup-$(date +%Y%m%d-%H%M%S).tfstate # Backup current state

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
terraform workspace list # List workspaces
terraform workspace new production # Create new workspace
terraform workspace select development # Select workspace
terraform workspace show # Show current workspace
terraform workspace delete old-environment # Delete workspace
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
terraform output # Show all outputs
terraform output vpc_id # Show specific output
terraform output -json # Output in JSON format
terraform output -raw private_key # Raw output (no quotes)
terraform output -json > outputs.json # Save outputs to file
```

### Graph Generation

```bash
terraform graph # Generate dependency graph
terraform graph | dot -Tpng > graph.png # Generate graph in DOT format
terraform graph -plan=tfplan # Generate plan graph
terraform graph -module=vpc # Generate graph for specific module
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
terraform console # Interactive console

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
terraform apply -parallelism=20 # Control parallelism
terraform refresh -target=aws_instance.web # Refresh only specific resources
terraform plan -refresh=false # Skip refresh during plan
terraform plan -compact-warnings # Use -compact-warnings
```

### State Optimization

```bash
terraform state list | grep 'module.old_module' | xargs terraform state rm # Clean up state
terraform state pull | terraform state push # Optimize state file
terraform init -backend-config=backend.hcl # Use partial backend configuration
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