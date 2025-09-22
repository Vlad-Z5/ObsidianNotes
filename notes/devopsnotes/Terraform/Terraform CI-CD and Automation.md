# Terraform CI/CD and Automation

**Terraform CI/CD and Automation** enables teams to implement Infrastructure as Code with proper validation, testing, approval workflows, and automated deployment pipelines across multiple environments.

## CI/CD Pipeline Architecture

### GitHub Actions Workflow

#### Complete Terraform CI/CD Pipeline
```yaml
# .github/workflows/terraform.yml
name: Terraform CI/CD

on:
  push:
    branches: [main, develop]
    paths:
      - 'terraform/**'
      - '.github/workflows/terraform.yml'
  pull_request:
    branches: [main]
    paths:
      - 'terraform/**'

env:
  TF_VERSION: '1.5.7'
  AWS_REGION: 'us-west-2'

jobs:
  # Validate Terraform configurations
  validate:
    name: Validate Terraform
    runs-on: ubuntu-latest

    steps:
    - name: Checkout
      uses: actions/checkout@v4

    - name: Setup Terraform
      uses: hashicorp/setup-terraform@v2
      with:
        terraform_version: ${{ env.TF_VERSION }}

    - name: Terraform Format Check
      run: terraform fmt -check -recursive
      working-directory: ./terraform

    - name: Terraform Init
      run: terraform init -backend=false
      working-directory: ./terraform/environments/dev

    - name: Terraform Validate
      run: terraform validate
      working-directory: ./terraform/environments/dev

    - name: TFLint
      uses: terraform-linters/setup-tflint@v3
      with:
        tflint_version: latest

    - name: Run TFLint
      run: |
        tflint --init
        find ./terraform -name "*.tf" -exec dirname {} \; | sort -u | while read dir; do
          echo "Linting $dir"
          tflint --chdir="$dir" --config="$(pwd)/.tflint.hcl"
        done

  # Security scanning
  security:
    name: Security Scan
    runs-on: ubuntu-latest
    needs: validate

    steps:
    - name: Checkout
      uses: actions/checkout@v4

    - name: Checkov Security Scan
      uses: bridgecrewio/checkov-action@master
      with:
        directory: ./terraform
        framework: terraform
        output_format: sarif
        output_file_path: checkov-results.sarif
        skip_check: CKV_AWS_23,CKV_AWS_50 # Skip specific checks if needed

    - name: Upload Checkov results
      uses: github/codeql-action/upload-sarif@v2
      if: always()
      with:
        sarif_file: checkov-results.sarif

    - name: Trivy IaC Scanner
      uses: aquasecurity/trivy-action@master
      with:
        scan-type: 'config'
        scan-ref: './terraform'
        format: 'sarif'
        output: 'trivy-results.sarif'

    - name: Upload Trivy results
      uses: github/codeql-action/upload-sarif@v2
      if: always()
      with:
        sarif_file: 'trivy-results.sarif'

  # Cost estimation
  cost-estimation:
    name: Cost Estimation
    runs-on: ubuntu-latest
    needs: validate

    steps:
    - name: Checkout
      uses: actions/checkout@v4

    - name: Setup Infracost
      uses: infracost/actions/setup@v2
      with:
        api-key: ${{ secrets.INFRACOST_API_KEY }}

    - name: Generate Infracost JSON
      run: |
        infracost breakdown --path ./terraform/environments/dev \
          --format json \
          --out-file infracost-base.json

    - name: Post Infracost comment
      uses: infracost/actions/comment@v1
      with:
        path: infracost-base.json
        behavior: update

  # Plan for development environment
  plan-dev:
    name: Plan Development
    if: github.event_name == 'pull_request'
    runs-on: ubuntu-latest
    needs: [validate, security]
    environment: development

    defaults:
      run:
        working-directory: ./terraform/environments/dev

    steps:
    - name: Checkout
      uses: actions/checkout@v4

    - name: Setup Terraform
      uses: hashicorp/setup-terraform@v2
      with:
        terraform_version: ${{ env.TF_VERSION }}

    - name: Configure AWS credentials
      uses: aws-actions/configure-aws-credentials@v4
      with:
        aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID_DEV }}
        aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY_DEV }}
        aws-region: ${{ env.AWS_REGION }}

    - name: Terraform Init
      run: terraform init

    - name: Terraform Plan
      id: plan
      run: |
        terraform plan -var-file="terraform.tfvars" -out=tfplan -no-color
        terraform show -no-color tfplan > plan-output.txt
      env:
        TF_VAR_db_password: ${{ secrets.DB_PASSWORD_DEV }}

    - name: Comment Plan on PR
      uses: actions/github-script@v6
      if: github.event_name == 'pull_request'
      with:
        script: |
          const fs = require('fs');
          const plan = fs.readFileSync('terraform/environments/dev/plan-output.txt', 'utf8');
          const truncatedPlan = plan.length > 65536 ? plan.substring(0, 65000) + '\n... (truncated)' : plan;

          github.rest.issues.createComment({
            issue_number: context.issue.number,
            owner: context.repo.owner,
            repo: context.repo.repo,
            body: `## Terraform Plan - Development

            <details>
            <summary>Click to expand plan</summary>

            \`\`\`
            ${truncatedPlan}
            \`\`\`
            </details>
            `
          });

    - name: Upload Plan Artifact
      uses: actions/upload-artifact@v3
      with:
        name: dev-tfplan
        path: terraform/environments/dev/tfplan
        retention-days: 7

  # Apply to development environment
  apply-dev:
    name: Apply Development
    if: github.ref == 'refs/heads/develop'
    runs-on: ubuntu-latest
    needs: [validate, security]
    environment: development

    defaults:
      run:
        working-directory: ./terraform/environments/dev

    steps:
    - name: Checkout
      uses: actions/checkout@v4

    - name: Setup Terraform
      uses: hashicorp/setup-terraform@v2
      with:
        terraform_version: ${{ env.TF_VERSION }}

    - name: Configure AWS credentials
      uses: aws-actions/configure-aws-credentials@v4
      with:
        aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID_DEV }}
        aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY_DEV }}
        aws-region: ${{ env.AWS_REGION }}

    - name: Terraform Init
      run: terraform init

    - name: Terraform Apply
      run: terraform apply -var-file="terraform.tfvars" -auto-approve
      env:
        TF_VAR_db_password: ${{ secrets.DB_PASSWORD_DEV }}

    - name: Post deployment tests
      run: |
        # Wait for infrastructure to be ready
        sleep 60

        # Run connectivity tests
        echo "Running post-deployment validation..."
        # Add your validation scripts here

  # Plan for production environment
  plan-prod:
    name: Plan Production
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    needs: [validate, security]
    environment: production

    defaults:
      run:
        working-directory: ./terraform/environments/prod

    steps:
    - name: Checkout
      uses: actions/checkout@v4

    - name: Setup Terraform
      uses: hashicorp/setup-terraform@v2
      with:
        terraform_version: ${{ env.TF_VERSION }}

    - name: Configure AWS credentials
      uses: aws-actions/configure-aws-credentials@v4
      with:
        aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID_PROD }}
        aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY_PROD }}
        aws-region: ${{ env.AWS_REGION }}

    - name: Terraform Init
      run: terraform init

    - name: Terraform Plan
      id: plan
      run: |
        terraform plan -var-file="terraform.tfvars" -out=tfplan
        terraform show -json tfplan > plan.json
      env:
        TF_VAR_db_password: ${{ secrets.DB_PASSWORD_PROD }}

    - name: Generate Plan Summary
      uses: actions/github-script@v6
      with:
        script: |
          const fs = require('fs');
          const plan = JSON.parse(fs.readFileSync('terraform/environments/prod/plan.json', 'utf8'));

          const changes = {
            create: 0,
            update: 0,
            delete: 0
          };

          plan.resource_changes?.forEach(change => {
            change.change.actions.forEach(action => {
              if (action === 'create') changes.create++;
              else if (action === 'update') changes.update++;
              else if (action === 'delete') changes.delete++;
            });
          });

          core.setOutput('plan_summary', JSON.stringify(changes));

    - name: Upload Production Plan
      uses: actions/upload-artifact@v3
      with:
        name: prod-tfplan
        path: |
          terraform/environments/prod/tfplan
          terraform/environments/prod/plan.json
        retention-days: 30

  # Apply to production environment (manual approval)
  apply-prod:
    name: Apply Production
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    needs: plan-prod
    environment:
      name: production
      url: https://myapp.company.com

    defaults:
      run:
        working-directory: ./terraform/environments/prod

    steps:
    - name: Checkout
      uses: actions/checkout@v4

    - name: Setup Terraform
      uses: hashicorp/setup-terraform@v2
      with:
        terraform_version: ${{ env.TF_VERSION }}

    - name: Configure AWS credentials
      uses: aws-actions/configure-aws-credentials@v4
      with:
        aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID_PROD }}
        aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY_PROD }}
        aws-region: ${{ env.AWS_REGION }}

    - name: Download Plan Artifact
      uses: actions/download-artifact@v3
      with:
        name: prod-tfplan
        path: ./terraform/environments/prod/

    - name: Terraform Init
      run: terraform init

    - name: Terraform Apply
      run: terraform apply tfplan

    - name: Post-deployment validation
      run: |
        echo "Running production validation suite..."
        # Add comprehensive production validation

        # Test database connectivity
        # Verify load balancer health
        # Check monitoring endpoints
        # Validate SSL certificates

        echo "Production deployment completed successfully!"

    - name: Notify deployment
      uses: 8398a7/action-slack@v3
      with:
        status: ${{ job.status }}
        channel: '#deployments'
        fields: repo,message,commit,author,action,eventName,ref,workflow
      env:
        SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK }}
```

### GitLab CI/CD Pipeline

#### Complete GitLab CI Configuration
```yaml
# .gitlab-ci.yml
stages:
  - validate
  - security
  - plan
  - apply

variables:
  TF_VERSION: "1.5.7"
  TF_ROOT: "terraform"
  AWS_DEFAULT_REGION: "us-west-2"

.terraform_template: &terraform_template
  image:
    name: hashicorp/terraform:$TF_VERSION
    entrypoint: [""]
  before_script:
    - cd $TF_ROOT
    - terraform --version
    - terraform init

.aws_credentials: &aws_credentials
  before_script:
    - export AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID
    - export AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY

# Validate stage
validate:
  stage: validate
  <<: *terraform_template
  script:
    - terraform fmt -check -recursive
    - cd environments/dev
    - terraform init -backend=false
    - terraform validate
  artifacts:
    reports:
      terraform: terraform/environments/dev/plan.json
  only:
    - merge_requests
    - main
    - develop

# Security scanning
security_scan:
  stage: security
  image: bridgecrew/checkov:latest
  script:
    - checkov --directory $TF_ROOT --framework terraform --output sarif --output-file-path checkov-results.sarif
  artifacts:
    reports:
      sast: checkov-results.sarif
    expire_in: 1 week
  only:
    - merge_requests
    - main
    - develop

# Cost estimation
cost_estimation:
  stage: security
  image: infracost/infracost:latest
  variables:
    INFRACOST_API_KEY: $INFRACOST_API_KEY
  script:
    - infracost breakdown --path $TF_ROOT/environments/dev --format json --out-file infracost.json
    - infracost diff --path $TF_ROOT/environments/dev --format table
  artifacts:
    paths:
      - infracost.json
    expire_in: 1 week
  only:
    - merge_requests

# Development environment
plan_dev:
  stage: plan
  <<: *terraform_template
  <<: *aws_credentials
  variables:
    TF_VAR_environment: "development"
  script:
    - cd environments/dev
    - terraform init
    - terraform plan -var-file="terraform.tfvars" -out=dev.tfplan
    - terraform show -json dev.tfplan > plan.json
  artifacts:
    paths:
      - $TF_ROOT/environments/dev/dev.tfplan
      - $TF_ROOT/environments/dev/plan.json
    expire_in: 1 week
  environment:
    name: development
  only:
    - merge_requests
    - develop

apply_dev:
  stage: apply
  <<: *terraform_template
  <<: *aws_credentials
  dependencies:
    - plan_dev
  script:
    - cd environments/dev
    - terraform init
    - terraform apply dev.tfplan
  environment:
    name: development
    url: https://dev.myapp.company.com
  only:
    - develop
  when: manual

# Staging environment
plan_staging:
  stage: plan
  <<: *terraform_template
  <<: *aws_credentials
  variables:
    TF_VAR_environment: "staging"
  script:
    - cd environments/staging
    - terraform init
    - terraform plan -var-file="terraform.tfvars" -out=staging.tfplan
  artifacts:
    paths:
      - $TF_ROOT/environments/staging/staging.tfplan
    expire_in: 1 week
  environment:
    name: staging
  only:
    - main

apply_staging:
  stage: apply
  <<: *terraform_template
  <<: *aws_credentials
  dependencies:
    - plan_staging
  script:
    - cd environments/staging
    - terraform init
    - terraform apply staging.tfplan
  environment:
    name: staging
    url: https://staging.myapp.company.com
  only:
    - main

# Production environment
plan_prod:
  stage: plan
  <<: *terraform_template
  <<: *aws_credentials
  variables:
    TF_VAR_environment: "production"
  script:
    - cd environments/prod
    - terraform init
    - terraform plan -var-file="terraform.tfvars" -out=prod.tfplan
  artifacts:
    paths:
      - $TF_ROOT/environments/prod/prod.tfplan
    expire_in: 1 month
  environment:
    name: production
  only:
    - main

apply_prod:
  stage: apply
  <<: *terraform_template
  <<: *aws_credentials
  dependencies:
    - plan_prod
  script:
    - cd environments/prod
    - terraform init
    - terraform apply prod.tfplan
    - echo "Production deployment completed!"
  environment:
    name: production
    url: https://myapp.company.com
  only:
    - main
  when: manual
  allow_failure: false
```

## Automation Scripts

### Comprehensive Deployment Script

#### Advanced Deployment Automation
```bash
#!/bin/bash
# scripts/deploy-infrastructure.sh

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TERRAFORM_DIR="$PROJECT_ROOT/terraform"

# Default values
ENVIRONMENT=""
ACTION=""
AUTO_APPROVE=false
DESTROY=false
PLAN_ONLY=false
VALIDATE_ONLY=false
DRY_RUN=false

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    local level=$1
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')

    case $level in
        ERROR)
            echo -e "${RED}[$timestamp] ERROR: $message${NC}" >&2
            ;;
        WARN)
            echo -e "${YELLOW}[$timestamp] WARN: $message${NC}" >&2
            ;;
        INFO)
            echo -e "${GREEN}[$timestamp] INFO: $message${NC}"
            ;;
        DEBUG)
            echo -e "${BLUE}[$timestamp] DEBUG: $message${NC}"
            ;;
    esac
}

# Error handling
error_exit() {
    log ERROR "$1"
    exit 1
}

# Usage function
usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Deploy or manage Terraform infrastructure

OPTIONS:
    -e, --environment ENVIRONMENT   Target environment (dev, staging, prod)
    -a, --action ACTION            Action to perform (plan, apply, destroy, validate)
    -y, --auto-approve             Auto approve apply operations
    -d, --destroy                  Destroy infrastructure
    -p, --plan-only               Only run terraform plan
    -v, --validate-only           Only validate configuration
    -n, --dry-run                 Show what would be done without executing
    -h, --help                    Show this help message

EXAMPLES:
    $0 -e dev -a plan              # Plan development environment
    $0 -e prod -a apply           # Apply production environment
    $0 -e staging -a destroy -y   # Destroy staging environment with auto-approve
    $0 -e dev -v                  # Validate development configuration

EOF
}

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -e|--environment)
                ENVIRONMENT="$2"
                shift 2
                ;;
            -a|--action)
                ACTION="$2"
                shift 2
                ;;
            -y|--auto-approve)
                AUTO_APPROVE=true
                shift
                ;;
            -d|--destroy)
                DESTROY=true
                ACTION="destroy"
                shift
                ;;
            -p|--plan-only)
                PLAN_ONLY=true
                ACTION="plan"
                shift
                ;;
            -v|--validate-only)
                VALIDATE_ONLY=true
                ACTION="validate"
                shift
                ;;
            -n|--dry-run)
                DRY_RUN=true
                shift
                ;;
            -h|--help)
                usage
                exit 0
                ;;
            *)
                error_exit "Unknown option: $1"
                ;;
        esac
    done
}

# Validate inputs
validate_inputs() {
    if [[ -z "$ENVIRONMENT" ]]; then
        error_exit "Environment must be specified (-e/--environment)"
    fi

    if [[ -z "$ACTION" ]]; then
        error_exit "Action must be specified (-a/--action)"
    fi

    case $ENVIRONMENT in
        dev|staging|prod)
            log INFO "Target environment: $ENVIRONMENT"
            ;;
        *)
            error_exit "Invalid environment: $ENVIRONMENT. Must be one of: dev, staging, prod"
            ;;
    esac

    case $ACTION in
        plan|apply|destroy|validate)
            log INFO "Action: $ACTION"
            ;;
        *)
            error_exit "Invalid action: $ACTION. Must be one of: plan, apply, destroy, validate"
            ;;
    esac

    if [[ ! -d "$TERRAFORM_DIR/environments/$ENVIRONMENT" ]]; then
        error_exit "Environment directory not found: $TERRAFORM_DIR/environments/$ENVIRONMENT"
    fi
}

# Check prerequisites
check_prerequisites() {
    log INFO "Checking prerequisites..."

    # Check Terraform installation
    if ! command -v terraform &> /dev/null; then
        error_exit "Terraform is not installed or not in PATH"
    fi

    local tf_version
    tf_version=$(terraform version -json | jq -r '.terraform_version')
    log INFO "Terraform version: $tf_version"

    # Check AWS CLI
    if ! command -v aws &> /dev/null; then
        error_exit "AWS CLI is not installed or not in PATH"
    fi

    # Verify AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        error_exit "AWS credentials not configured or invalid"
    fi

    local aws_identity
    aws_identity=$(aws sts get-caller-identity --query 'Account' --output text)
    log INFO "AWS Account: $aws_identity"

    # Check required tools
    local required_tools=("jq" "curl")
    for tool in "${required_tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            error_exit "$tool is required but not installed"
        fi
    done
}

# Validate Terraform configuration
validate_terraform() {
    log INFO "Validating Terraform configuration..."

    cd "$TERRAFORM_DIR/environments/$ENVIRONMENT"

    # Format check
    if ! terraform fmt -check -recursive ../../; then
        error_exit "Terraform formatting check failed. Run 'terraform fmt -recursive' to fix."
    fi
    log INFO "Terraform formatting check passed"

    # Initialize for validation
    if ! terraform init -backend=false -input=false; then
        error_exit "Terraform init failed"
    fi

    # Validate
    if ! terraform validate; then
        error_exit "Terraform validation failed"
    fi
    log INFO "Terraform validation passed"
}

# Initialize Terraform
init_terraform() {
    log INFO "Initializing Terraform..."

    cd "$TERRAFORM_DIR/environments/$ENVIRONMENT"

    if [[ "$DRY_RUN" == "true" ]]; then
        log INFO "DRY RUN: Would run: terraform init -upgrade"
        return 0
    fi

    if ! terraform init -upgrade -input=false; then
        error_exit "Terraform init failed"
    fi

    # Select or create workspace
    if ! terraform workspace select "$ENVIRONMENT" 2>/dev/null; then
        log INFO "Creating workspace: $ENVIRONMENT"
        terraform workspace new "$ENVIRONMENT"
    fi

    log INFO "Terraform initialized successfully"
}

# Create Terraform plan
create_plan() {
    log INFO "Creating Terraform plan..."

    cd "$TERRAFORM_DIR/environments/$ENVIRONMENT"

    local plan_file="${ENVIRONMENT}.tfplan"
    local plan_args=()

    plan_args+=("-var-file=terraform.tfvars")
    plan_args+=("-out=$plan_file")
    plan_args+=("-input=false")

    if [[ "$DESTROY" == "true" ]]; then
        plan_args+=("-destroy")
        plan_file="destroy-${ENVIRONMENT}.tfplan"
        plan_args[-1]="-out=$plan_file"
    fi

    if [[ "$DRY_RUN" == "true" ]]; then
        log INFO "DRY RUN: Would run: terraform plan ${plan_args[*]}"
        return 0
    fi

    if ! terraform plan "${plan_args[@]}"; then
        error_exit "Terraform plan failed"
    fi

    # Show plan summary
    if command -v terraform-plan-summary &> /dev/null; then
        terraform-plan-summary "$plan_file"
    fi

    log INFO "Terraform plan created: $plan_file"
}

# Apply Terraform changes
apply_terraform() {
    log INFO "Applying Terraform changes..."

    cd "$TERRAFORM_DIR/environments/$ENVIRONMENT"

    local plan_file="${ENVIRONMENT}.tfplan"
    if [[ "$DESTROY" == "true" ]]; then
        plan_file="destroy-${ENVIRONMENT}.tfplan"
    fi

    if [[ ! -f "$plan_file" ]]; then
        error_exit "Plan file not found: $plan_file. Run plan first."
    fi

    if [[ "$DRY_RUN" == "true" ]]; then
        log INFO "DRY RUN: Would run: terraform apply $plan_file"
        return 0
    fi

    # Confirmation for production
    if [[ "$ENVIRONMENT" == "prod" && "$AUTO_APPROVE" != "true" ]]; then
        echo
        read -p "Are you sure you want to apply changes to PRODUCTION? (yes/no): " -r
        if [[ ! $REPLY =~ ^yes$ ]]; then
            log INFO "Apply cancelled by user"
            return 0
        fi
    fi

    if ! terraform apply "$plan_file"; then
        error_exit "Terraform apply failed"
    fi

    # Cleanup plan file
    rm -f "$plan_file"

    log INFO "Terraform apply completed successfully"
}

# Run post-deployment validation
post_deployment_validation() {
    log INFO "Running post-deployment validation..."

    cd "$TERRAFORM_DIR/environments/$ENVIRONMENT"

    # Get outputs
    local outputs
    outputs=$(terraform output -json 2>/dev/null || echo '{}')

    # Basic connectivity tests
    if [[ "$DRY_RUN" == "true" ]]; then
        log INFO "DRY RUN: Would run post-deployment validation"
        return 0
    fi

    # Example validations
    local vpc_id
    vpc_id=$(echo "$outputs" | jq -r '.vpc_id.value // empty')

    if [[ -n "$vpc_id" ]]; then
        log INFO "Validating VPC: $vpc_id"
        if aws ec2 describe-vpcs --vpc-ids "$vpc_id" &>/dev/null; then
            log INFO "VPC validation passed"
        else
            log WARN "VPC validation failed"
        fi
    fi

    # Add more validation checks as needed
    log INFO "Post-deployment validation completed"
}

# Generate deployment report
generate_report() {
    log INFO "Generating deployment report..."

    cd "$TERRAFORM_DIR/environments/$ENVIRONMENT"

    local report_file="deployment-report-$(date +%Y%m%d-%H%M%S).json"

    if [[ "$DRY_RUN" == "true" ]]; then
        log INFO "DRY RUN: Would generate report: $report_file"
        return 0
    fi

    local report
    report=$(cat << EOF
{
    "deployment": {
        "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
        "environment": "$ENVIRONMENT",
        "action": "$ACTION",
        "terraform_version": "$(terraform version -json | jq -r '.terraform_version')",
        "aws_account": "$(aws sts get-caller-identity --query 'Account' --output text)",
        "user": "$(whoami)",
        "git_commit": "$(git rev-parse HEAD 2>/dev/null || echo 'unknown')"
    },
    "outputs": $(terraform output -json 2>/dev/null || echo '{}')
}
EOF
    )

    echo "$report" > "$report_file"
    log INFO "Deployment report generated: $report_file"
}

# Main execution
main() {
    log INFO "Starting Terraform deployment script..."

    parse_args "$@"
    validate_inputs
    check_prerequisites

    case $ACTION in
        validate)
            validate_terraform
            ;;
        plan)
            validate_terraform
            init_terraform
            create_plan
            ;;
        apply)
            validate_terraform
            init_terraform
            create_plan
            apply_terraform
            post_deployment_validation
            generate_report
            ;;
        destroy)
            init_terraform
            create_plan
            apply_terraform
            ;;
    esac

    log INFO "Terraform deployment script completed successfully"
}

# Trap for cleanup
cleanup() {
    local exit_code=$?
    if [[ $exit_code -ne 0 ]]; then
        log ERROR "Script failed with exit code: $exit_code"
    fi
    exit $exit_code
}

trap cleanup EXIT

# Run main function
main "$@"
```

### Terraform Testing Framework

#### Terratest Integration
```go
// test/terraform_integration_test.go
package test

import (
    "testing"
    "time"

    "github.com/gruntwork-io/terratest/modules/aws"
    "github.com/gruntwork-io/terratest/modules/terraform"
    "github.com/stretchr/testify/assert"
)

func TestTerraformVPCModule(t *testing.T) {
    t.Parallel()

    // Expected values
    expectedVpcCidr := "10.0.0.0/16"
    expectedEnvironment := "test"
    awsRegion := "us-west-2"

    // Terraform options
    terraformOptions := terraform.WithDefaultRetryableErrors(t, &terraform.Options{
        TerraformDir: "../terraform/environments/test",
        Vars: map[string]interface{}{
            "environment": expectedEnvironment,
            "vpc_cidr":    expectedVpcCidr,
        },
        EnvVars: map[string]string{
            "AWS_DEFAULT_REGION": awsRegion,
        },
    })

    // Cleanup resources after test
    defer terraform.Destroy(t, terraformOptions)

    // Deploy the infrastructure
    terraform.InitAndApply(t, terraformOptions)

    // Validate VPC
    vpcId := terraform.Output(t, terraformOptions, "vpc_id")
    vpc := aws.GetVpcById(t, vpcId, awsRegion)

    assert.Equal(t, expectedVpcCidr, *vpc.CidrBlock)
    assert.Equal(t, "available", *vpc.State)

    // Validate subnets
    privateSubnetIds := terraform.OutputList(t, terraformOptions, "private_subnet_ids")
    publicSubnetIds := terraform.OutputList(t, terraformOptions, "public_subnet_ids")

    assert.Equal(t, 3, len(privateSubnetIds))
    assert.Equal(t, 3, len(publicSubnetIds))

    // Test subnet connectivity
    for _, subnetId := range publicSubnetIds {
        subnet := aws.GetSubnetById(t, subnetId, awsRegion)
        assert.True(t, *subnet.MapPublicIpOnLaunch)
    }

    for _, subnetId := range privateSubnetIds {
        subnet := aws.GetSubnetById(t, subnetId, awsRegion)
        assert.False(t, *subnet.MapPublicIpOnLaunch)
    }
}

func TestTerraformEKSModule(t *testing.T) {
    t.Parallel()

    awsRegion := "us-west-2"
    expectedClusterName := "test-eks-cluster"

    terraformOptions := terraform.WithDefaultRetryableErrors(t, &terraform.Options{
        TerraformDir: "../terraform/environments/test",
        Vars: map[string]interface{}{
            "cluster_name": expectedClusterName,
        },
        EnvVars: map[string]string{
            "AWS_DEFAULT_REGION": awsRegion,
        },
    })

    defer terraform.Destroy(t, terraformOptions)

    terraform.InitAndApply(t, terraformOptions)

    // Validate EKS cluster
    clusterName := terraform.Output(t, terraformOptions, "cluster_name")
    cluster := aws.GetEksCluster(t, awsRegion, clusterName)

    assert.Equal(t, expectedClusterName, *cluster.Name)
    assert.Equal(t, "ACTIVE", *cluster.Status)

    // Wait for nodes to be ready
    maxRetries := 30
    timeBetweenRetries := 30 * time.Second

    for i := 0; i < maxRetries; i++ {
        nodeGroups := aws.GetEksNodeGroups(t, awsRegion, clusterName)
        allReady := true

        for _, nodeGroup := range nodeGroups {
            if *nodeGroup.Status != "ACTIVE" {
                allReady = false
                break
            }
        }

        if allReady {
            break
        }

        if i == maxRetries-1 {
            t.Fatal("Node groups did not become ready within timeout")
        }

        time.Sleep(timeBetweenRetries)
    }
}
```

This comprehensive Terraform CI/CD and Automation file provides enterprise-grade pipeline configurations, deployment scripts, and testing frameworks that enable teams to implement robust Infrastructure as Code practices with proper validation, security scanning, and automated deployment workflows.