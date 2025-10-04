# Terraform Testing and Validation

**Terraform Testing and Validation** ensures infrastructure code quality, reliability, and compliance through automated testing frameworks, validation pipelines, and comprehensive testing strategies.

## Testing Strategy Overview

### Testing Pyramid for Infrastructure

#### Testing Levels
```
    ┌─────────────────────────┐
    │    End-to-End Tests     │  ← Full infrastructure deployment
    │                         │
    ├─────────────────────────┤
    │   Integration Tests     │  ← Multi-module interactions
    │                         │
    ├─────────────────────────┤
    │     Unit Tests          │  ← Individual modules
    │                         │
    ├─────────────────────────┤
    │  Static Analysis        │  ← Code quality, security
    │                         │
    └─────────────────────────┘
```

### Testing Framework Selection

#### Terratest (Go-based Testing)
```go
// test/terraform_aws_test.go
package test

import (
    "fmt"
    "strings"
    "testing"
    "time"

    "github.com/gruntwork-io/terratest/modules/aws"
    "github.com/gruntwork-io/terratest/modules/random"
    "github.com/gruntwork-io/terratest/modules/terraform"
    "github.com/stretchr/testify/assert"
    "github.com/stretchr/testify/require"
)

func TestTerraformAwsVpcModule(t *testing.T) {
    t.Parallel()

    // Generate unique name for test resources
    uniqueId := random.UniqueId()
    vpcName := fmt.Sprintf("test-vpc-%s", uniqueId)

    // AWS region for testing
    awsRegion := "us-west-2"

    // Terraform options
    terraformOptions := terraform.WithDefaultRetryableErrors(t, &terraform.Options{
        // Path to Terraform configuration
        TerraformDir: "../examples/vpc",

        // Variables to pass to Terraform
        Vars: map[string]interface{}{
            "vpc_name":    vpcName,
            "vpc_cidr":    "10.0.0.0/16",
            "environment": "test",
            "aws_region":  awsRegion,
        },

        // Environment variables
        EnvVars: map[string]string{
            "AWS_DEFAULT_REGION": awsRegion,
        },

        // Retry configuration
        RetryableTerraformErrors: map[string]string{
            "RequestError": "Temporary AWS request error",
        },
        MaxRetries:         3,
        TimeBetweenRetries: 5 * time.Second,
    })

    // Clean up resources after test
    defer terraform.Destroy(t, terraformOptions)

    // Deploy infrastructure
    terraform.InitAndApply(t, terraformOptions)

    // Test VPC creation
    vpcId := terraform.Output(t, terraformOptions, "vpc_id")
    vpc := aws.GetVpcById(t, vpcId, awsRegion)

    // Assertions
    assert.Equal(t, "10.0.0.0/16", *vpc.CidrBlock)
    assert.Equal(t, "available", *vpc.State)
    assert.True(t, *vpc.EnableDnsSupport)
    assert.True(t, *vpc.EnableDnsHostnames)

    // Test tags
    expectedTags := map[string]string{
        "Name":        vpcName,
        "Environment": "test",
        "ManagedBy":   "terraform",
    }

    for key, expectedValue := range expectedTags {
        actualValue := aws.GetTagsForVpc(t, vpcId, awsRegion)[key]
        assert.Equal(t, expectedValue, actualValue)
    }

    // Test subnets
    publicSubnetIds := terraform.OutputList(t, terraformOptions, "public_subnet_ids")
    privateSubnetIds := terraform.OutputList(t, terraformOptions, "private_subnet_ids")

    require.Len(t, publicSubnetIds, 3)
    require.Len(t, privateSubnetIds, 3)

    // Verify subnet properties
    for _, subnetId := range publicSubnetIds {
        subnet := aws.GetSubnetById(t, subnetId, awsRegion)
        assert.True(t, *subnet.MapPublicIpOnLaunch)
        assert.Contains(t, *subnet.CidrBlock, "10.0.")
    }

    for _, subnetId := range privateSubnetIds {
        subnet := aws.GetSubnetById(t, subnetId, awsRegion)
        assert.False(t, *subnet.MapPublicIpOnLaunch)
        assert.Contains(t, *subnet.CidrBlock, "10.0.")
    }
}

func TestTerraformAwsEksCluster(t *testing.T) {
    t.Parallel()

    uniqueId := random.UniqueId()
    clusterName := fmt.Sprintf("test-eks-%s", uniqueId)
    awsRegion := "us-west-2"

    terraformOptions := terraform.WithDefaultRetryableErrors(t, &terraform.Options{
        TerraformDir: "../examples/eks",
        Vars: map[string]interface{}{
            "cluster_name": clusterName,
            "environment":  "test",
            "aws_region":   awsRegion,
        },
        EnvVars: map[string]string{
            "AWS_DEFAULT_REGION": awsRegion,
        },
    })

    defer terraform.Destroy(t, terraformOptions)

    terraform.InitAndApply(t, terraformOptions)

    // Test EKS cluster
    cluster := aws.GetEksCluster(t, awsRegion, clusterName)
    assert.Equal(t, clusterName, *cluster.Name)
    assert.Equal(t, "ACTIVE", *cluster.Status)

    // Test node groups
    nodeGroups := aws.GetEksNodeGroups(t, awsRegion, clusterName)
    assert.True(t, len(nodeGroups) > 0)

    for _, nodeGroup := range nodeGroups {
        assert.Equal(t, "ACTIVE", *nodeGroup.Status)
        assert.True(t, *nodeGroup.ScalingConfig.MinSize >= 1)
        assert.True(t, *nodeGroup.ScalingConfig.MaxSize >= *nodeGroup.ScalingConfig.MinSize)
    }

    // Test cluster endpoint accessibility
    endpoint := terraform.Output(t, terraformOptions, "cluster_endpoint")
    assert.True(t, strings.HasPrefix(endpoint, "https://"))

    // Verify security groups
    securityGroupIds := terraform.OutputList(t, terraformOptions, "cluster_security_group_ids")
    assert.True(t, len(securityGroupIds) > 0)

    for _, sgId := range securityGroupIds {
        sg := aws.GetSecurityGroupById(t, sgId, awsRegion)
        assert.NotNil(t, sg)
    }
}

func TestTerraformAwsRds(t *testing.T) {
    t.Parallel()

    uniqueId := random.UniqueId()
    dbInstanceId := fmt.Sprintf("test-db-%s", uniqueId)
    awsRegion := "us-west-2"

    terraformOptions := terraform.WithDefaultRetryableErrors(t, &terraform.Options{
        TerraformDir: "../examples/rds",
        Vars: map[string]interface{}{
            "db_instance_identifier": dbInstanceId,
            "db_name":               "testdb",
            "db_username":           "testuser",
            "db_password":           "testpassword123!",
            "environment":           "test",
        },
        EnvVars: map[string]string{
            "AWS_DEFAULT_REGION": awsRegion,
        },
    })

    defer terraform.Destroy(t, terraformOptions)

    terraform.InitAndApply(t, terraformOptions)

    // Test RDS instance
    dbInstance := aws.GetRdsInstanceById(t, dbInstanceId, awsRegion)
    assert.Equal(t, dbInstanceId, *dbInstance.DBInstanceIdentifier)
    assert.Equal(t, "available", *dbInstance.DBInstanceStatus)
    assert.True(t, *dbInstance.StorageEncrypted)
    assert.False(t, *dbInstance.PubliclyAccessible)

    // Test endpoint
    endpoint := terraform.Output(t, terraformOptions, "db_endpoint")
    assert.Contains(t, endpoint, dbInstanceId)
    assert.Contains(t, endpoint, awsRegion)

    // Test security group
    securityGroups := dbInstance.VpcSecurityGroups
    assert.True(t, len(securityGroups) > 0)

    for _, sg := range securityGroups {
        assert.Equal(t, "active", *sg.Status)
    }
}
```

#### Kitchen-Terraform (Ruby-based Testing)
```ruby
# test/integration/default/controls/vpc_test.rb
describe aws_vpc(terraform_output(:vpc_id)) do
  it { should exist }
  it { should be_available }
  its(:cidr_block) { should eq '10.0.0.0/16' }
  its(:state) { should eq 'available' }
end

describe aws_subnets.where(vpc_id: terraform_output(:vpc_id)) do
  its(:count) { should eq 6 }
end

# Public subnets test
terraform_output(:public_subnet_ids).each do |subnet_id|
  describe aws_subnet(subnet_id) do
    it { should exist }
    it { should be_available }
    its(:map_public_ip_on_launch) { should be true }
  end
end

# Private subnets test
terraform_output(:private_subnet_ids).each do |subnet_id|
  describe aws_subnet(subnet_id) do
    it { should exist }
    it { should be_available }
    its(:map_public_ip_on_launch) { should be false }
  end
end

# Internet Gateway test
describe aws_internet_gateway(terraform_output(:internet_gateway_id)) do
  it { should exist }
  it { should be_attached }
end

# Route tables test
describe aws_route_table(terraform_output(:public_route_table_id)) do
  it { should exist }
  it { should have_route('0.0.0.0/0') }
end
```

## Unit Testing

### Module Unit Testing

#### Terraform Module Test Structure
```hcl
# test/fixtures/vpc_test/main.tf
module "vpc_test" {
  source = "../../../modules/vpc"

  name                = var.vpc_name
  cidr                = var.vpc_cidr
  azs                 = var.availability_zones
  private_subnets     = var.private_subnets
  public_subnets      = var.public_subnets
  database_subnets    = var.database_subnets

  enable_nat_gateway = var.enable_nat_gateway
  enable_vpn_gateway = false
  enable_flow_log    = true

  tags = {
    Environment = var.environment
    TestSuite   = "unit-test"
  }
}
```

```hcl
# test/fixtures/vpc_test/variables.tf
variable "vpc_name" {
  description = "Name of the VPC"
  type        = string
  default     = "test-vpc"
}

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "List of availability zones"
  type        = list(string)
  default     = ["us-west-2a", "us-west-2b", "us-west-2c"]
}

variable "private_subnets" {
  description = "List of private subnet CIDR blocks"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
}

variable "public_subnets" {
  description = "List of public subnet CIDR blocks"
  type        = list(string)
  default     = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]
}

variable "database_subnets" {
  description = "List of database subnet CIDR blocks"
  type        = list(string)
  default     = ["10.0.201.0/24", "10.0.202.0/24", "10.0.203.0/24"]
}

variable "enable_nat_gateway" {
  description = "Enable NAT Gateway"
  type        = bool
  default     = true
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "test"
}
```

```hcl
# test/fixtures/vpc_test/outputs.tf
output "vpc_id" {
  description = "ID of the VPC"
  value       = module.vpc_test.vpc_id
}

output "vpc_cidr_block" {
  description = "CIDR block of the VPC"
  value       = module.vpc_test.vpc_cidr_block
}

output "public_subnet_ids" {
  description = "List of IDs of public subnets"
  value       = module.vpc_test.public_subnets
}

output "private_subnet_ids" {
  description = "List of IDs of private subnets"
  value       = module.vpc_test.private_subnets
}

output "database_subnet_ids" {
  description = "List of IDs of database subnets"
  value       = module.vpc_test.database_subnets
}

output "internet_gateway_id" {
  description = "ID of the Internet Gateway"
  value       = module.vpc_test.igw_id
}

output "nat_gateway_ids" {
  description = "List of IDs of the NAT Gateways"
  value       = module.vpc_test.natgw_ids
}

output "public_route_table_id" {
  description = "ID of the public route table"
  value       = module.vpc_test.public_route_table_ids[0]
}

output "private_route_table_ids" {
  description = "List of IDs of private route tables"
  value       = module.vpc_test.private_route_table_ids
}
```

### Automated Testing Pipeline

#### GitHub Actions Testing Workflow
```yaml
# .github/workflows/terraform-test.yml
name: Terraform Testing

on:
  push:
    branches: [main, develop]
    paths: ['terraform/**', 'test/**']
  pull_request:
    branches: [main]
    paths: ['terraform/**', 'test/**']

env:
  TF_VERSION: '1.5.7'
  GO_VERSION: '1.20'

jobs:
  # Static Analysis
  static-analysis:
    name: Static Analysis
    runs-on: ubuntu-latest

    steps:
    - name: Checkout
      uses: actions/checkout@v4

    - name: Setup Terraform
      uses: hashicorp/setup-terraform@v2
      with:
        terraform_version: ${{ env.TF_VERSION }}

    - name: Terraform Format Check
      run: terraform fmt -check -recursive terraform/

    - name: Terraform Init and Validate
      run: |
        find terraform/ -name "*.tf" -exec dirname {} \; | sort -u | while read dir; do
          echo "Validating $dir"
          cd "$dir"
          terraform init -backend=false
          terraform validate
          cd - > /dev/null
        done

    - name: TFLint
      uses: terraform-linters/setup-tflint@v3
      with:
        tflint_version: latest

    - name: Run TFLint
      run: |
        tflint --init
        find terraform/ -name "*.tf" -exec dirname {} \; | sort -u | while read dir; do
          echo "Linting $dir"
          tflint --chdir="$dir"
        done

    - name: TFSec Security Scan
      uses: aquasecurity/tfsec-action@v1.0.3
      with:
        working_directory: terraform/

  # Unit Tests
  unit-tests:
    name: Unit Tests
    runs-on: ubuntu-latest
    needs: static-analysis

    strategy:
      matrix:
        test-dir: [vpc, eks, rds, security-groups]

    steps:
    - name: Checkout
      uses: actions/checkout@v4

    - name: Setup Go
      uses: actions/setup-go@v4
      with:
        go-version: ${{ env.GO_VERSION }}

    - name: Setup Terraform
      uses: hashicorp/setup-terraform@v2
      with:
        terraform_version: ${{ env.TF_VERSION }}

    - name: Configure AWS credentials
      uses: aws-actions/configure-aws-credentials@v4
      with:
        aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID_TEST }}
        aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY_TEST }}
        aws-region: us-west-2

    - name: Run Terratest
      working-directory: test
      run: |
        go mod download
        go test -v -timeout 45m -run TestTerraform${{ matrix.test-dir }}

  # Integration Tests
  integration-tests:
    name: Integration Tests
    runs-on: ubuntu-latest
    needs: unit-tests
    if: github.ref == 'refs/heads/main' || github.event_name == 'pull_request'

    steps:
    - name: Checkout
      uses: actions/checkout@v4

    - name: Setup Go
      uses: actions/setup-go@v4
      with:
        go-version: ${{ env.GO_VERSION }}

    - name: Setup Terraform
      uses: hashicorp/setup-terraform@v2
      with:
        terraform_version: ${{ env.TF_VERSION }}

    - name: Configure AWS credentials
      uses: aws-actions/configure-aws-credentials@v4
      with:
        aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID_TEST }}
        aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY_TEST }}
        aws-region: us-west-2

    - name: Run Integration Tests
      working-directory: test
      run: |
        go test -v -timeout 90m -run TestTerraformIntegration
      env:
        TF_VAR_environment: test-integration

  # Contract Tests
  contract-tests:
    name: Contract Tests
    runs-on: ubuntu-latest
    needs: static-analysis

    steps:
    - name: Checkout
      uses: actions/checkout@v4

    - name: Setup Terraform
      uses: hashicorp/setup-terraform@v2
      with:
        terraform_version: ${{ env.TF_VERSION }}

    - name: Run Contract Tests
      run: |
        # Test module interfaces
        find terraform/modules/ -name "*.tf" -exec dirname {} \; | sort -u | while read module_dir; do
          echo "Testing module contract: $module_dir"
          cd "$module_dir"

          # Check required files exist
          if [[ ! -f "main.tf" ]]; then
            echo "ERROR: main.tf missing in $module_dir"
            exit 1
          fi

          if [[ ! -f "variables.tf" ]]; then
            echo "ERROR: variables.tf missing in $module_dir"
            exit 1
          fi

          if [[ ! -f "outputs.tf" ]]; then
            echo "ERROR: outputs.tf missing in $module_dir"
            exit 1
          fi

          # Validate module structure
          terraform init -backend=false
          terraform validate

          cd - > /dev/null
        done

  # Performance Tests
  performance-tests:
    name: Performance Tests
    runs-on: ubuntu-latest
    needs: unit-tests
    if: github.ref == 'refs/heads/main'

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
        aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID_TEST }}
        aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY_TEST }}
        aws-region: us-west-2

    - name: Run Performance Tests
      run: |
        # Test large-scale deployments
        cd test/performance

        # Time the deployment
        start_time=$(date +%s)
        terraform init
        terraform plan -out=perftest.tfplan
        terraform apply perftest.tfplan
        end_time=$(date +%s)

        execution_time=$((end_time - start_time))
        echo "Deployment time: ${execution_time} seconds"

        # Performance thresholds
        if [ $execution_time -gt 1800 ]; then  # 30 minutes
          echo "ERROR: Deployment took too long: ${execution_time}s > 1800s"
          exit 1
        fi

        # Cleanup
        terraform destroy -auto-approve
```

## Compliance and Security Testing

### Policy Testing with OPA

#### OPA Policy Testing Framework
```rego
# policies/security_test.rego
package terraform.security_test

import data.terraform.security

# Test cases for security policies
test_s3_bucket_encryption_required {
    # Test case: S3 bucket without encryption should be denied
    input := {
        "resource_changes": [{
            "type": "aws_s3_bucket",
            "address": "aws_s3_bucket.test",
            "change": {
                "after": {
                    "bucket": "test-bucket"
                    # Missing server_side_encryption_configuration
                }
            }
        }]
    }

    violations := security.deny with input as input
    count(violations) > 0
}

test_s3_bucket_encryption_allowed {
    # Test case: S3 bucket with encryption should be allowed
    input := {
        "resource_changes": [{
            "type": "aws_s3_bucket",
            "address": "aws_s3_bucket.test",
            "change": {
                "after": {
                    "bucket": "test-bucket",
                    "server_side_encryption_configuration": {
                        "rule": {
                            "apply_server_side_encryption_by_default": {
                                "sse_algorithm": "AES256"
                            }
                        }
                    }
                }
            }
        }]
    }

    violations := security.deny with input as input
    count(violations) == 0
}

test_rds_encryption_required {
    # Test case: RDS without encryption should be denied
    input := {
        "resource_changes": [{
            "type": "aws_db_instance",
            "address": "aws_db_instance.test",
            "change": {
                "after": {
                    "identifier": "test-db",
                    "storage_encrypted": false
                }
            }
        }]
    }

    violations := security.deny with input as input
    count(violations) > 0
}

test_security_group_ssh_restriction {
    # Test case: Security group allowing SSH from anywhere should be denied
    input := {
        "resource_changes": [{
            "type": "aws_security_group_rule",
            "address": "aws_security_group_rule.test",
            "change": {
                "after": {
                    "type": "ingress",
                    "from_port": 22,
                    "to_port": 22,
                    "protocol": "tcp",
                    "cidr_blocks": ["0.0.0.0/0"]
                }
            }
        }]
    }

    violations := security.deny with input as input
    count(violations) > 0
}

test_required_tags_validation {
    # Test case: Resource without required tags should be denied
    input := {
        "resource_changes": [{
            "type": "aws_instance",
            "address": "aws_instance.test",
            "change": {
                "after": {
                    "instance_type": "t3.micro",
                    "tags": {
                        "Name": "test-instance"
                        # Missing required tags: Environment, Owner, CostCenter, Project
                    }
                }
            }
        }]
    }

    violations := security.deny with input as input
    count(violations) > 0
}
```

#### Policy Test Automation
```bash
#!/bin/bash
# scripts/test-policies.sh

set -euo pipefail

POLICY_DIR="policies"
TEST_DATA_DIR="test/policy-test-data"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}" >&2
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARN: $1${NC}" >&2
}

# Test OPA policies
test_opa_policies() {
    log "Running OPA policy tests..."

    # Run policy tests
    if opa test "$POLICY_DIR" --verbose; then
        log "✅ OPA policy tests passed"
    else
        error "❌ OPA policy tests failed"
        return 1
    fi

    # Test policies against sample Terraform plans
    log "Testing policies against sample plans..."

    local test_plans=(
        "valid_plan.json"
        "invalid_s3_encryption.json"
        "invalid_rds_encryption.json"
        "invalid_security_group.json"
        "missing_tags.json"
    )

    for plan_file in "${test_plans[@]}"; do
        local plan_path="$TEST_DATA_DIR/$plan_file"

        if [[ ! -f "$plan_path" ]]; then
            warn "Test plan not found: $plan_path"
            continue
        fi

        log "Testing plan: $plan_file"

        # Expected to pass/fail based on file name
        if [[ "$plan_file" =~ ^valid_ ]]; then
            # Should pass (no violations)
            local violations
            violations=$(opa eval -d "$POLICY_DIR" -i "$plan_path" "data.terraform.security.deny[x]" --format json | jq -r '.result[].expressions[].value[]? // empty')

            if [[ -z "$violations" ]]; then
                log "✅ $plan_file: No violations (expected)"
            else
                error "❌ $plan_file: Unexpected violations found"
                echo "$violations"
                return 1
            fi
        else
            # Should fail (violations expected)
            local violations
            violations=$(opa eval -d "$POLICY_DIR" -i "$plan_path" "data.terraform.security.deny[x]" --format json | jq -r '.result[].expressions[].value[]? // empty')

            if [[ -n "$violations" ]]; then
                log "✅ $plan_file: Violations found (expected)"
                echo "  Violations:"
                echo "$violations" | sed 's/^/    /'
            else
                error "❌ $plan_file: No violations found (violations expected)"
                return 1
            fi
        fi
    done
}

# Generate test data
generate_test_data() {
    log "Generating test data..."

    mkdir -p "$TEST_DATA_DIR"

    # Valid plan
    cat > "$TEST_DATA_DIR/valid_plan.json" << 'EOF'
{
  "resource_changes": [
    {
      "type": "aws_s3_bucket",
      "address": "aws_s3_bucket.valid",
      "change": {
        "after": {
          "bucket": "valid-bucket",
          "server_side_encryption_configuration": {
            "rule": {
              "apply_server_side_encryption_by_default": {
                "sse_algorithm": "AES256"
              }
            }
          },
          "tags": {
            "Environment": "test",
            "Owner": "platform-team",
            "CostCenter": "engineering",
            "Project": "infrastructure"
          }
        }
      }
    }
  ]
}
EOF

    # Invalid S3 encryption plan
    cat > "$TEST_DATA_DIR/invalid_s3_encryption.json" << 'EOF'
{
  "resource_changes": [
    {
      "type": "aws_s3_bucket",
      "address": "aws_s3_bucket.invalid",
      "change": {
        "after": {
          "bucket": "invalid-bucket",
          "tags": {
            "Environment": "test",
            "Owner": "platform-team",
            "CostCenter": "engineering",
            "Project": "infrastructure"
          }
        }
      }
    }
  ]
}
EOF

    # Invalid RDS encryption plan
    cat > "$TEST_DATA_DIR/invalid_rds_encryption.json" << 'EOF'
{
  "resource_changes": [
    {
      "type": "aws_db_instance",
      "address": "aws_db_instance.invalid",
      "change": {
        "after": {
          "identifier": "invalid-db",
          "storage_encrypted": false,
          "tags": {
            "Environment": "test",
            "Owner": "platform-team",
            "CostCenter": "engineering",
            "Project": "infrastructure"
          }
        }
      }
    }
  ]
}
EOF

    # Invalid security group plan
    cat > "$TEST_DATA_DIR/invalid_security_group.json" << 'EOF'
{
  "resource_changes": [
    {
      "type": "aws_security_group_rule",
      "address": "aws_security_group_rule.invalid",
      "change": {
        "after": {
          "type": "ingress",
          "from_port": 22,
          "to_port": 22,
          "protocol": "tcp",
          "cidr_blocks": ["0.0.0.0/0"]
        }
      }
    }
  ]
}
EOF

    # Missing tags plan
    cat > "$TEST_DATA_DIR/missing_tags.json" << 'EOF'
{
  "resource_changes": [
    {
      "type": "aws_instance",
      "address": "aws_instance.missing_tags",
      "change": {
        "after": {
          "instance_type": "t3.micro",
          "tags": {
            "Name": "test-instance"
          }
        }
      }
    }
  ]
}
EOF

    log "Test data generated successfully"
}

# Main execution
main() {
    log "Starting policy testing..."

    # Check prerequisites
    if ! command -v opa &> /dev/null; then
        error "OPA is not installed"
        exit 1
    fi

    if ! command -v jq &> /dev/null; then
        error "jq is not installed"
        exit 1
    fi

    # Generate test data
    generate_test_data

    # Run tests
    if test_opa_policies; then
        log "✅ All policy tests passed"
        return 0
    else
        error "❌ Policy tests failed"
        return 1
    fi
}

# Run main function
main "$@"
```

## Continuous Testing

### Automated Test Execution

#### Makefile for Testing Automation
```makefile
# Makefile for Terraform testing automation

.PHONY: help test test-unit test-integration test-security test-performance clean

# Default target
help:
	@echo "Available targets:"
	@echo "  test              - Run all tests"
	@echo "  test-unit         - Run unit tests"
	@echo "  test-integration  - Run integration tests"
	@echo "  test-security     - Run security and policy tests"
	@echo "  test-performance  - Run performance tests"
	@echo "  clean             - Clean test artifacts"

# Variables
TF_VERSION ?= 1.5.7
GO_VERSION ?= 1.20
TEST_TIMEOUT ?= 45m
INTEGRATION_TIMEOUT ?= 90m
AWS_REGION ?= us-west-2

# Setup targets
setup-go:
	@echo "Setting up Go environment..."
	@if ! command -v go &> /dev/null; then \
		echo "Go is not installed. Please install Go $(GO_VERSION)"; \
		exit 1; \
	fi
	cd test && go mod download

setup-terraform:
	@echo "Setting up Terraform..."
	@if ! command -v terraform &> /dev/null; then \
		echo "Terraform is not installed. Please install Terraform $(TF_VERSION)"; \
		exit 1; \
	fi

setup-tools:
	@echo "Setting up additional tools..."
	@if ! command -v tflint &> /dev/null; then \
		echo "Installing TFLint..."; \
		curl -s https://raw.githubusercontent.com/terraform-linters/tflint/master/install_linux.sh | bash; \
	fi
	@if ! command -v tfsec &> /dev/null; then \
		echo "Installing TFSec..."; \
		curl -s https://raw.githubusercontent.com/aquasecurity/tfsec/master/scripts/install_linux.sh | bash; \
	fi
	@if ! command -v opa &> /dev/null; then \
		echo "Installing OPA..."; \
		curl -L -o opa https://openpolicyagent.org/downloads/v0.56.0/opa_linux_amd64_static; \
		chmod +x opa; \
		sudo mv opa /usr/local/bin/; \
	fi

setup: setup-go setup-terraform setup-tools

# Linting and validation
lint:
	@echo "Running Terraform lint..."
	terraform fmt -check -recursive terraform/
	find terraform/ -name "*.tf" -exec dirname {} \; | sort -u | while read dir; do \
		echo "Validating $$dir"; \
		cd "$$dir" && terraform init -backend=false && terraform validate && cd - > /dev/null; \
	done

tflint:
	@echo "Running TFLint..."
	tflint --init
	find terraform/ -name "*.tf" -exec dirname {} \; | sort -u | while read dir; do \
		echo "Linting $$dir"; \
		tflint --chdir="$$dir"; \
	done

tfsec:
	@echo "Running TFSec security scan..."
	tfsec terraform/ --format json --out tfsec-results.json
	@if [ -s tfsec-results.json ]; then \
		echo "Security issues found:"; \
		cat tfsec-results.json | jq '.results[] | {rule_id: .rule_id, description: .description, location: .location}'; \
	else \
		echo "No security issues found"; \
	fi

# Unit tests
test-unit: setup-go
	@echo "Running unit tests..."
	cd test && \
	go test -v -timeout $(TEST_TIMEOUT) -run "TestTerraform.*" \
		-parallel 4 \
		./...

# Integration tests
test-integration: setup-go
	@echo "Running integration tests..."
	cd test && \
	go test -v -timeout $(INTEGRATION_TIMEOUT) -run "TestTerraformIntegration.*" \
		-parallel 2 \
		./...

# Security tests
test-security: tfsec
	@echo "Running security and policy tests..."
	./scripts/test-policies.sh

# Performance tests
test-performance: setup-go
	@echo "Running performance tests..."
	cd test/performance && \
	go test -v -timeout $(INTEGRATION_TIMEOUT) -run "TestTerraformPerformance.*" \
		./...

# Contract tests
test-contract:
	@echo "Running contract tests..."
	find terraform/modules/ -name "*.tf" -exec dirname {} \; | sort -u | while read module_dir; do \
		echo "Testing module contract: $$module_dir"; \
		cd "$$module_dir" && \
		if [[ ! -f "main.tf" ]] || [[ ! -f "variables.tf" ]] || [[ ! -f "outputs.tf" ]]; then \
			echo "ERROR: Missing required files in $$module_dir"; \
			exit 1; \
		fi && \
		terraform init -backend=false && terraform validate && \
		cd - > /dev/null; \
	done

# Run all tests
test: lint tflint test-contract test-unit test-security
	@echo "All tests completed successfully!"

# Full test suite including integration and performance
test-full: test test-integration test-performance
	@echo "Full test suite completed successfully!"

# Clean up test artifacts
clean:
	@echo "Cleaning up test artifacts..."
	find . -name ".terraform" -type d -exec rm -rf {} + 2>/dev/null || true
	find . -name "terraform.tfstate*" -type f -delete 2>/dev/null || true
	find . -name "*.tfplan" -type f -delete 2>/dev/null || true
	rm -f tfsec-results.json
	cd test && go clean -testcache

# Development helpers
dev-test:
	@echo "Running development tests (fast feedback)..."
	$(MAKE) lint
	$(MAKE) test-unit TEST_TIMEOUT=10m

watch-test:
	@echo "Watching for changes and running tests..."
	while inotifywait -r -e modify terraform/ test/; do \
		$(MAKE) dev-test; \
	done
```

This comprehensive Terraform Testing and Validation file provides a complete testing framework with unit tests, integration tests, security testing, policy validation, and automated CI/CD pipelines that ensure infrastructure code quality and reliability in production environments.