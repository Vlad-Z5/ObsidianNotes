# AWS CodeBuild

> **Service Type:** CI/CD Build Service | **Tier:** CI/CD and Automation | **Global/Regional:** Regional

## Overview

AWS CodeBuild is a fully managed continuous integration service that compiles source code, runs tests, and produces software packages. It scales automatically and integrates seamlessly with other AWS services to provide comprehensive DevOps workflows.

## DevOps Use Cases

### Continuous Integration
- **Automated builds** triggered by source code commits
- **Multi-branch builds** for feature development and releases
- **Parallel testing** across multiple environments and configurations
- **Code quality gates** with static analysis and security scanning

### Container Workflows
- **Docker image building** with multi-stage builds and optimization
- **Container security scanning** using ECR image scanning
- **Multi-architecture builds** for ARM and x86 platforms
- **Container registry publishing** to ECR, Docker Hub, or private registries

### Testing Automation
- **Unit test execution** with coverage reporting
- **Integration testing** against real AWS services
- **Performance testing** with load testing frameworks
- **Security testing** with SAST/DAST tools integration

### Package Management
- **Artifact creation** for deployment pipelines
- **Dependency management** with caching for faster builds
- **Multi-environment packaging** with environment-specific configurations
- **Version tagging** and semantic versioning automation

### Infrastructure Testing
- **Infrastructure as Code validation** for CloudFormation and Terraform
- **Configuration testing** using tools like Terratest
- **Compliance scanning** for security and governance requirements
- **Cost estimation** for infrastructure changes

## Build Environment Types

### Linux Environments
- **Amazon Linux 2** - Standard AWS Linux environment
- **Ubuntu 18.04/20.04** - Popular development environment
- **Custom Docker images** - Your own containerized build environment

### Windows Environments
- **Windows Server 2019** - .NET applications and Windows-specific builds
- **Windows Server Core** - Lightweight Windows environment

### ARM Environments
- **Graviton2-based builds** - Cost-effective ARM64 builds
- **Multi-architecture** - Build for both x86 and ARM platforms

## Core Features

### Build Specifications
- **buildspec.yml** - Declarative build configuration
- **Inline build commands** - Simple command execution
- **Multi-phase builds** - Pre-build, build, post-build phases
- **Environment variables** - Dynamic configuration injection

### Source Integration
- **GitHub/GitHub Enterprise** - Direct integration with webhooks
- **AWS CodeCommit** - Native AWS Git repository service
- **Bitbucket** - Atlassian source code management
- **S3** - Source code stored in S3 buckets

### Advanced Features
- **Build caching** - S3-based caching for dependencies and artifacts
- **VPC support** - Access to private resources in your VPC
- **Batch builds** - Multiple related builds in a single operation
- **Report groups** - Test results and code coverage reporting

## Practical CLI Examples

### Project Management

```bash
# Create CodeBuild project
aws codebuild create-project \
  --name my-web-app-build \
  --description "Build project for web application" \
  --source '{
    "type": "GITHUB",
    "location": "https://github.com/myorg/web-app.git",
    "gitCloneDepth": 1,
    "buildspec": "buildspec.yml",
    "reportBuildStatus": true
  }' \
  --artifacts '{
    "type": "S3",
    "location": "my-build-artifacts/web-app"
  }' \
  --environment '{
    "type": "LINUX_CONTAINER",
    "image": "aws/codebuild/amazonlinux2-x86_64-standard:3.0",
    "computeType": "BUILD_GENERAL1_MEDIUM",
    "environmentVariables": [
      {
        "name": "NODE_ENV",
        "value": "production"
      },
      {
        "name": "AWS_DEFAULT_REGION",
        "value": "us-west-2"
      }
    ]
  }' \
  --service-role arn:aws:iam::123456789012:role/CodeBuildServiceRole

# Update project configuration
aws codebuild update-project \
  --name my-web-app-build \
  --environment '{
    "type": "LINUX_CONTAINER",
    "image": "aws/codebuild/amazonlinux2-x86_64-standard:4.0",
    "computeType": "BUILD_GENERAL1_LARGE",
    "environmentVariables": [
      {
        "name": "NODE_ENV",
        "value": "production"
      },
      {
        "name": "BUILD_CACHE",
        "value": "enabled"
      }
    ]
  }'

# Start build
aws codebuild start-build \
  --project-name my-web-app-build \
  --source-version main \
  --environment-variables-override name=BUILD_NUMBER,value=123 name=DEPLOYMENT_ENV,value=staging

# Start batch build
aws codebuild start-build-batch \
  --project-name my-web-app-build \
  --source-version main
```

### Build Monitoring

```bash
# List builds for project
aws codebuild list-builds-for-project \
  --project-name my-web-app-build \
  --sort-order DESCENDING

# Get build details
aws codebuild batch-get-builds \
  --ids my-web-app-build:12345678-1234-1234-1234-123456789012

# Get build logs
aws logs get-log-events \
  --log-group-name /aws/codebuild/my-web-app-build \
  --log-stream-name 12345678-1234-1234-1234-123456789012

# Stop build
aws codebuild stop-build \
  --id my-web-app-build:12345678-1234-1234-1234-123456789012
```

### Report Groups

```bash
# Create test report group
aws codebuild create-report-group \
  --name my-web-app-test-reports \
  --type TEST \
  --export-config '{
    "exportConfigType": "S3",
    "s3Destination": {
      "bucket": "my-test-reports",
      "path": "codebuild-reports",
      "packaging": "ZIP"
    }
  }'

# Create code coverage report group
aws codebuild create-report-group \
  --name my-web-app-coverage-reports \
  --type CODE_COVERAGE \
  --export-config '{
    "exportConfigType": "S3",
    "s3Destination": {
      "bucket": "my-coverage-reports",
      "path": "coverage"
    }
  }'
```

## Build Specification Examples

### Node.js Application Build

```yaml
# buildspec.yml for Node.js application
version: 0.2

env:
  variables:
    NODE_ENV: production
  parameter-store:
    DATABASE_URL: /myapp/database-url
    API_KEY: /myapp/api-key

phases:
  install:
    runtime-versions:
      nodejs: 18
    commands:
      - echo "Installing dependencies..."
      - npm ci --only=production
      
  pre_build:
    commands:
      - echo "Running pre-build tasks..."
      - npm run lint
      - npm run test:unit
      - echo "Logging in to Amazon ECR..."
      - aws ecr get-login-password --region $AWS_DEFAULT_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com
      
  build:
    commands:
      - echo "Building application..."
      - npm run build
      - echo "Building Docker image..."
      - docker build -t $IMAGE_REPO_NAME:$IMAGE_TAG .
      - docker tag $IMAGE_REPO_NAME:$IMAGE_TAG $AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com/$IMAGE_REPO_NAME:$IMAGE_TAG
      
  post_build:
    commands:
      - echo "Pushing Docker image..."
      - docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com/$IMAGE_REPO_NAME:$IMAGE_TAG
      - echo "Creating deployment artifact..."
      - printf '[{"name":"web-app","imageUri":"%s"}]' $AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com/$IMAGE_REPO_NAME:$IMAGE_TAG > imagedefinitions.json

artifacts:
  files:
    - imagedefinitions.json
    - dist/**/*
  name: web-app-$(date +%Y-%m-%d)

reports:
  test-reports:
    files:
      - 'coverage/lcov.info'
      - 'junit.xml'
    file-format: 'JUNITXML'
    base-directory: '.'

cache:
  paths:
    - '/root/.npm/**/*'
    - 'node_modules/**/*'
```

### Python Application with Testing

```yaml
# buildspec.yml for Python application
version: 0.2

env:
  variables:
    PYTHONPATH: /codebuild/output/src123456789/src
  parameter-store:
    DATABASE_PASSWORD: /myapp/db-password

phases:
  install:
    runtime-versions:
      python: 3.9
    commands:
      - echo "Installing dependencies..."
      - pip install --upgrade pip
      - pip install -r requirements.txt
      - pip install -r requirements-dev.txt
      
  pre_build:
    commands:
      - echo "Running security and quality checks..."
      - bandit -r src/
      - flake8 src/
      - mypy src/
      - echo "Running unit tests..."
      - python -m pytest tests/unit/ --cov=src --cov-report=xml --junitxml=test-results.xml
      
  build:
    commands:
      - echo "Running integration tests..."
      - python -m pytest tests/integration/ --junitxml=integration-results.xml
      - echo "Building package..."
      - python setup.py sdist bdist_wheel
      
  post_build:
    commands:
      - echo "Uploading to PyPI..."
      - twine upload dist/* --repository-url $PYPI_REPOSITORY_URL

artifacts:
  files:
    - dist/*
  name: python-package-$(date +%Y-%m-%d)

reports:
  unit-test-reports:
    files:
      - test-results.xml
    file-format: JUNITXML
  integration-test-reports:
    files:
      - integration-results.xml
    file-format: JUNITXML
  coverage-reports:
    files:
      - coverage.xml
    file-format: COBERTURAXML

cache:
  paths:
    - '/root/.cache/pip/**/*'
```

### Infrastructure as Code Validation

```yaml
# buildspec.yml for Terraform validation
version: 0.2

env:
  variables:
    TF_VERSION: 1.5.0
    TF_IN_AUTOMATION: true

phases:
  install:
    commands:
      - echo "Installing Terraform..."
      - wget https://releases.hashicorp.com/terraform/${TF_VERSION}/terraform_${TF_VERSION}_linux_amd64.zip
      - unzip terraform_${TF_VERSION}_linux_amd64.zip
      - mv terraform /usr/local/bin/
      - echo "Installing additional tools..."
      - curl -L "$(curl -s https://api.github.com/repos/aquasecurity/tfsec/releases/latest | grep -o -E "https://.+?_linux_amd64.tar.gz")" > tfsec.tar.gz
      - tar -xzf tfsec.tar.gz
      - mv tfsec /usr/local/bin/
      
  pre_build:
    commands:
      - echo "Terraform version"
      - terraform version
      - echo "Initializing Terraform..."
      - terraform init -backend=false
      - echo "Validating Terraform syntax..."
      - terraform validate
      - echo "Running security scan..."
      - tfsec . --format junit > tfsec-results.xml
      
  build:
    commands:
      - echo "Planning Terraform changes..."
      - terraform plan -out=tfplan
      - echo "Generating plan summary..."
      - terraform show -json tfplan > tfplan.json
      
  post_build:
    commands:
      - echo "Terraform validation completed"
      - echo "Plan summary:"
      - terraform show tfplan

artifacts:
  files:
    - tfplan
    - tfplan.json
  name: terraform-plan-$(date +%Y-%m-%d)

reports:
  security-scan:
    files:
      - tfsec-results.xml
    file-format: JUNITXML
```

## DevOps Automation Scripts

### Multi-Environment Build Script

```bash
#!/bin/bash
# multi-env-build.sh - Build application for multiple environments

PROJECT_NAME="my-web-app-build"
ENVIRONMENTS=("development" "staging" "production")
SOURCE_VERSION=${1:-main}

echo "Starting multi-environment builds for ${PROJECT_NAME}"

BUILD_IDS=()

# Start builds for each environment
for env in "${ENVIRONMENTS[@]}"; do
    echo "Starting build for ${env} environment..."
    
    BUILD_ID=$(aws codebuild start-build \
        --project-name ${PROJECT_NAME} \
        --source-version ${SOURCE_VERSION} \
        --environment-variables-override \
            name=ENVIRONMENT,value=${env} \
            name=BUILD_TIMESTAMP,value=$(date -Iseconds) \
        --query 'build.id' \
        --output text)
    
    BUILD_IDS+=($BUILD_ID)
    echo "Build started for ${env}: ${BUILD_ID}"
done

echo "Monitoring build progress..."

# Monitor all builds
ALL_COMPLETE=false
while [ "$ALL_COMPLETE" = false ]; do
    ALL_COMPLETE=true
    
    for build_id in "${BUILD_IDS[@]}"; do
        STATUS=$(aws codebuild batch-get-builds \
            --ids ${build_id} \
            --query 'builds[0].buildStatus' \
            --output text)
        
        if [ "$STATUS" = "IN_PROGRESS" ]; then
            ALL_COMPLETE=false
        fi
        
        echo "Build ${build_id}: ${STATUS}"
    done
    
    if [ "$ALL_COMPLETE" = false ]; then
        echo "Waiting for builds to complete..."
        sleep 30
    fi
done

# Report final results
echo "All builds completed. Final status:"
for i in "${!BUILD_IDS[@]}"; do
    build_id=${BUILD_IDS[$i]}
    env=${ENVIRONMENTS[$i]}
    
    RESULT=$(aws codebuild batch-get-builds \
        --ids ${build_id} \
        --query 'builds[0].buildStatus' \
        --output text)
    
    echo "${env}: ${RESULT}"
    
    if [ "$RESULT" != "SUCCEEDED" ]; then
        echo "Build failed for ${env}. Check logs:"
        echo "aws logs get-log-events --log-group-name /aws/codebuild/${PROJECT_NAME} --log-stream-name ${build_id}"
    fi
done
```

### Build Performance Monitor

```bash
#!/bin/bash
# build-performance-monitor.sh - Monitor build performance and costs

PROJECT_NAME=$1
DAYS=${2:-7}

if [ -z "$PROJECT_NAME" ]; then
    echo "Usage: $0 <project-name> [days]"
    exit 1
fi

echo "Analyzing build performance for ${PROJECT_NAME} over the last ${DAYS} days"

# Get builds from the last N days
START_TIME=$(date -d "${DAYS} days ago" -Iseconds)
BUILD_IDS=$(aws codebuild list-builds-for-project \
    --project-name ${PROJECT_NAME} \
    --query "ids[?@]" \
    --output text)

if [ -z "$BUILD_IDS" ]; then
    echo "No builds found for project ${PROJECT_NAME}"
    exit 1
fi

echo "Found $(echo $BUILD_IDS | wc -w) builds"

# Analyze build metrics
TOTAL_DURATION=0
TOTAL_BUILDS=0
SUCCESSFUL_BUILDS=0
FAILED_BUILDS=0

for build_id in $BUILD_IDS; do
    BUILD_INFO=$(aws codebuild batch-get-builds \
        --ids ${build_id} \
        --query 'builds[0].[buildStatus,startTime,endTime,currentPhase]' \
        --output text)
    
    read -r STATUS START_TIME_STR END_TIME_STR PHASE <<< "$BUILD_INFO"
    
    # Skip builds that haven't completed
    if [ "$STATUS" = "IN_PROGRESS" ] || [ -z "$END_TIME_STR" ]; then
        continue
    fi
    
    # Calculate duration
    START_EPOCH=$(date -d "$START_TIME_STR" +%s)
    END_EPOCH=$(date -d "$END_TIME_STR" +%s)
    DURATION=$((END_EPOCH - START_EPOCH))
    
    TOTAL_DURATION=$((TOTAL_DURATION + DURATION))
    TOTAL_BUILDS=$((TOTAL_BUILDS + 1))
    
    if [ "$STATUS" = "SUCCEEDED" ]; then
        SUCCESSFUL_BUILDS=$((SUCCESSFUL_BUILDS + 1))
    else
        FAILED_BUILDS=$((FAILED_BUILDS + 1))
    fi
    
    echo "Build ${build_id}: ${STATUS} (${DURATION}s)"
done

# Calculate averages
if [ $TOTAL_BUILDS -gt 0 ]; then
    AVERAGE_DURATION=$((TOTAL_DURATION / TOTAL_BUILDS))
    SUCCESS_RATE=$((SUCCESSFUL_BUILDS * 100 / TOTAL_BUILDS))
    
    echo ""
    echo "=== Build Performance Summary ==="
    echo "Total builds: ${TOTAL_BUILDS}"
    echo "Successful builds: ${SUCCESSFUL_BUILDS}"
    echo "Failed builds: ${FAILED_BUILDS}"
    echo "Success rate: ${SUCCESS_RATE}%"
    echo "Average build duration: ${AVERAGE_DURATION} seconds"
    echo "Total build time: ${TOTAL_DURATION} seconds"
    
    # Cost estimation (rough calculation)
    # Assuming BUILD_GENERAL1_MEDIUM at $0.005 per minute
    TOTAL_MINUTES=$((TOTAL_DURATION / 60))
    ESTIMATED_COST=$(echo "scale=2; ${TOTAL_MINUTES} * 0.005" | bc)
    echo "Estimated cost: \$${ESTIMATED_COST}"
fi
```

### Build Cache Optimization Script

```python
# optimize-build-cache.py - Analyze and optimize build cache usage
import boto3
import json
from datetime import datetime, timedelta

def analyze_build_cache(project_name, days=30):
    """Analyze build cache effectiveness for a CodeBuild project"""
    
    codebuild = boto3.client('codebuild')
    s3 = boto3.client('s3')
    
    # Get recent builds
    builds_response = codebuild.list_builds_for_project(
        projectName=project_name,
        sortOrder='DESCENDING'
    )
    
    build_ids = builds_response['ids'][:50]  # Analyze last 50 builds
    
    if not build_ids:
        print(f"No builds found for project {project_name}")
        return
    
    # Get detailed build information
    builds_detail = codebuild.batch_get_builds(ids=build_ids)
    
    cache_hits = 0
    cache_misses = 0
    total_duration = 0
    cached_duration = 0
    non_cached_duration = 0
    
    for build in builds_detail['builds']:
        if build['buildStatus'] not in ['SUCCEEDED', 'FAILED']:
            continue
            
        duration = (build['endTime'] - build['startTime']).total_seconds()
        total_duration += duration
        
        # Check if build used cache
        cache_used = False
        if 'cache' in build and build['cache']['type'] != 'NO_CACHE':
            # Look for cache-related log entries
            log_group = f"/aws/codebuild/{project_name}"
            log_stream = build['id']
            
            try:
                logs_client = boto3.client('logs')
                log_events = logs_client.get_log_events(
                    logGroupName=log_group,
                    logStreamName=log_stream,
                    startTime=int(build['startTime'].timestamp() * 1000),
                    endTime=int(build['endTime'].timestamp() * 1000)
                )
                
                for event in log_events['events']:
                    if 'cache hit' in event['message'].lower():
                        cache_used = True
                        break
                        
            except Exception as e:
                print(f"Could not retrieve logs for build {build['id']}: {e}")
        
        if cache_used:
            cache_hits += 1
            cached_duration += duration
        else:
            cache_misses += 1
            non_cached_duration += duration
    
    total_builds = cache_hits + cache_misses
    
    if total_builds > 0:
        cache_hit_rate = (cache_hits / total_builds) * 100
        avg_cached_duration = cached_duration / cache_hits if cache_hits > 0 else 0
        avg_non_cached_duration = non_cached_duration / cache_misses if cache_misses > 0 else 0
        
        time_saved = (avg_non_cached_duration - avg_cached_duration) * cache_hits
        
        print(f"\n=== Build Cache Analysis for {project_name} ===")
        print(f"Total builds analyzed: {total_builds}")
        print(f"Cache hits: {cache_hits}")
        print(f"Cache misses: {cache_misses}")
        print(f"Cache hit rate: {cache_hit_rate:.1f}%")
        print(f"Average cached build duration: {avg_cached_duration:.0f} seconds")
        print(f"Average non-cached build duration: {avg_non_cached_duration:.0f} seconds")
        print(f"Total time saved by caching: {time_saved:.0f} seconds ({time_saved/60:.1f} minutes)")
        
        # Cost savings calculation
        cost_per_minute = 0.005  # BUILD_GENERAL1_MEDIUM rate
        cost_saved = (time_saved / 60) * cost_per_minute
        print(f"Estimated cost saved: ${cost_saved:.2f}")
        
        # Recommendations
        print(f"\n=== Recommendations ===")
        if cache_hit_rate < 50:
            print("- Cache hit rate is low. Consider optimizing cache paths in buildspec.yml")
            print("- Ensure dependencies are cached properly")
        
        if avg_non_cached_duration > 600:  # 10 minutes
            print("- Long build times detected. Consider:")
            print("  - Using a larger compute type")
            print("  - Optimizing build scripts")
            print("  - Implementing better caching strategies")
        
        if cache_hits == 0:
            print("- No cache usage detected. Enable caching in buildspec.yml:")
            print("  cache:")
            print("    paths:")
            print("      - '/root/.npm/**/*'")
            print("      - 'node_modules/**/*'")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python optimize-build-cache.py <project-name> [days]")
        sys.exit(1)
    
    project_name = sys.argv[1]
    days = int(sys.argv[2]) if len(sys.argv) > 2 else 30
    
    analyze_build_cache(project_name, days)
```

## Best Practices

### Performance Optimization
- **Use caching** for dependencies and build artifacts
- **Choose appropriate compute type** based on build requirements
- **Optimize Docker builds** with multi-stage builds and layer caching
- **Parallel builds** for independent components

### Security Best Practices
- **Use IAM roles** with least privilege principle
- **Store secrets** in Parameter Store or Secrets Manager
- **Enable VPC** for builds that need private resource access
- **Scan container images** for vulnerabilities

### Cost Management
- **Right-size compute types** based on actual build requirements
- **Use build caching** to reduce build times and costs
- **Clean up old artifacts** to minimize storage costs
- **Monitor build patterns** to optimize resource usage

### Monitoring and Debugging
- **Use CloudWatch metrics** for build performance monitoring
- **Implement proper logging** with structured log formats
- **Set up build notifications** for success/failure alerts
- **Create build dashboards** for team visibility