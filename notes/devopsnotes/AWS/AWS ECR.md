# AWS ECR (Elastic Container Registry)

> **Service Type:** Container Registry | **Tier:** CI/CD and Automation | **Global/Regional:** Regional

## Overview

Amazon Elastic Container Registry (ECR) is a fully managed Docker container registry that integrates with Amazon ECS, EKS, and AWS Lambda. It provides secure, scalable, and reliable storage for container images with built-in security scanning and lifecycle management.

## DevOps Use Cases

### Container Image Management
- **Centralized registry** for Docker images across development teams
- **Multi-environment image promotion** from dev to staging to production
- **Version control** with semantic tagging and immutable image tags
- **Artifact storage** for CI/CD pipelines with automated image builds

### Security and Compliance
- **Vulnerability scanning** with automated security assessments
- **Image signing** and verification for supply chain security
- **Access control** with fine-grained IAM permissions
- **Compliance reporting** for security audits and governance

### Multi-Region Deployments
- **Cross-region replication** for disaster recovery and global deployments
- **Edge deployments** with regional image caches for faster pulls
- **Hybrid cloud** integration with on-premises container orchestrators
- **Cost optimization** through regional data transfer reduction

### CI/CD Integration
- **Automated image builds** triggered by source code changes
- **Image promotion pipelines** with approval workflows
- **Integration testing** with fresh image builds
- **Deployment automation** to ECS, EKS, and Lambda services

### Enterprise Features
- **Private repositories** with VPC endpoint access
- **Registry mirroring** from public registries like Docker Hub
- **Organizational governance** with repository policies and controls
- **Cost management** through lifecycle policies and storage optimization

## Core Features

### Repository Management
- **Private repositories** with AWS-managed security
- **Public repositories** via Amazon ECR Public for open-source projects
- **Repository policies** for fine-grained access control
- **Resource-based permissions** with IAM integration

### Image Security
- **Enhanced scanning** with AWS Inspector integration
- **Basic scanning** for common vulnerabilities (CVEs)
- **Scan on push** for immediate vulnerability detection
- **SBOM generation** for software bill of materials

### Lifecycle Management
- **Lifecycle policies** for automated image cleanup
- **Retention rules** based on age, count, or tags
- **Cost optimization** through storage management
- **Policy testing** before applying to production

### Integration and Authentication
- **Docker CLI support** with aws ecr get-login-password
- **ECS/EKS integration** with automatic image pulling
- **Lambda integration** for container-based functions
- **Third-party tools** integration via standard Docker Registry API

## Practical CLI Examples

### Repository Management

```bash
# Create ECR repository
aws ecr create-repository \
  --repository-name my-web-app \
  --image-scanning-configuration scanOnPush=true \
  --encryption-configuration encryptionType=AES256 \
  --tags Key=Project,Value=WebApp Key=Environment,Value=Production

# Create public repository
aws ecr-public create-repository \
  --repository-name my-public-app \
  --catalog-data repositoryDescription="Public web application",usageText="docker pull public.ecr.aws/myorg/my-public-app:latest"

# List repositories
aws ecr describe-repositories
aws ecr describe-repositories --repository-names my-web-app my-api

# Delete repository
aws ecr delete-repository \
  --repository-name my-old-app \
  --force  # Delete even if contains images
```

### Image Operations

```bash
# Get login token for Docker
aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin 123456789012.dkr.ecr.us-west-2.amazonaws.com

# Tag and push image
docker tag my-web-app:latest 123456789012.dkr.ecr.us-west-2.amazonaws.com/my-web-app:latest
docker tag my-web-app:latest 123456789012.dkr.ecr.us-west-2.amazonaws.com/my-web-app:v1.2.3
docker push 123456789012.dkr.ecr.us-west-2.amazonaws.com/my-web-app:latest
docker push 123456789012.dkr.ecr.us-west-2.amazonaws.com/my-web-app:v1.2.3

# List images in repository
aws ecr list-images --repository-name my-web-app

# Get image details
aws ecr describe-images \
  --repository-name my-web-app \
  --image-ids imageTag=latest

# Pull image
docker pull 123456789012.dkr.ecr.us-west-2.amazonaws.com/my-web-app:v1.2.3

# Delete specific image
aws ecr batch-delete-image \
  --repository-name my-web-app \
  --image-ids imageTag=v1.0.0
```

### Security Scanning

```bash
# Start image scan
aws ecr start-image-scan \
  --repository-name my-web-app \
  --image-id imageTag=latest

# Get scan results
aws ecr describe-image-scan-findings \
  --repository-name my-web-app \
  --image-id imageTag=latest

# Get scan results with filters
aws ecr describe-image-scan-findings \
  --repository-name my-web-app \
  --image-id imageTag=latest \
  --max-items 20 \
  --query 'imageScanFindings.findings[?severity==`HIGH`]'
```

### Lifecycle Policies

```bash
# Create lifecycle policy
cat > lifecycle-policy.json << 'EOF'
{
  "rules": [
    {
      "rulePriority": 1,
      "description": "Keep last 10 production images",
      "selection": {
        "tagStatus": "tagged",
        "tagPrefixList": ["v"],
        "countType": "imageCountMoreThan",
        "countNumber": 10
      },
      "action": {
        "type": "expire"
      }
    },
    {
      "rulePriority": 2,
      "description": "Delete untagged images older than 7 days",
      "selection": {
        "tagStatus": "untagged",
        "countType": "sinceImagePushed",
        "countUnit": "days",
        "countNumber": 7
      },
      "action": {
        "type": "expire"
      }
    }
  ]
}
EOF

aws ecr put-lifecycle-policy \
  --repository-name my-web-app \
  --lifecycle-policy-text file://lifecycle-policy.json

# Preview lifecycle policy
aws ecr preview-lifecycle-policy \
  --repository-name my-web-app \
  --lifecycle-policy-text file://lifecycle-policy.json

# Get lifecycle policy
aws ecr get-lifecycle-policy \
  --repository-name my-web-app
```

### Cross-Region Replication

```bash
# Create replication configuration
cat > replication-config.json << 'EOF'
{
  "rules": [
    {
      "destinations": [
        {
          "region": "us-east-1",
          "registryId": "123456789012"
        },
        {
          "region": "eu-west-1",
          "registryId": "123456789012"
        }
      ],
      "repositoryFilters": [
        {
          "filter": "my-web-app",
          "filterType": "PREFIX_MATCH"
        }
      ]
    }
  ]
}
EOF

aws ecr put-replication-configuration \
  --replication-configuration file://replication-config.json

# Get replication configuration
aws ecr describe-registry \
  --query 'replicationConfiguration'
```

## DevOps Automation Scripts

### Automated Image Build and Push

```bash
#!/bin/bash
# build-and-push.sh - Build and push Docker images to ECR

APP_NAME=$1
VERSION=$2
DOCKERFILE=${3:-Dockerfile}
ECR_REGISTRY="123456789012.dkr.ecr.us-west-2.amazonaws.com"

if [ $# -lt 2 ]; then
    echo "Usage: $0 <app-name> <version> [dockerfile]"
    exit 1
fi

echo "Building and pushing ${APP_NAME}:${VERSION} to ECR"

# Check if repository exists
if ! aws ecr describe-repositories --repository-names ${APP_NAME} >/dev/null 2>&1; then
    echo "Creating ECR repository: ${APP_NAME}"
    aws ecr create-repository \
        --repository-name ${APP_NAME} \
        --image-scanning-configuration scanOnPush=true \
        --encryption-configuration encryptionType=AES256
fi

# Get ECR login token
echo "Logging in to ECR..."
aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin ${ECR_REGISTRY}

# Build image
echo "Building Docker image..."
docker build -f ${DOCKERFILE} -t ${APP_NAME}:${VERSION} .

if [ $? -ne 0 ]; then
    echo "Docker build failed"
    exit 1
fi

# Tag for ECR
docker tag ${APP_NAME}:${VERSION} ${ECR_REGISTRY}/${APP_NAME}:${VERSION}
docker tag ${APP_NAME}:${VERSION} ${ECR_REGISTRY}/${APP_NAME}:latest

# Push to ECR
echo "Pushing images to ECR..."
docker push ${ECR_REGISTRY}/${APP_NAME}:${VERSION}
docker push ${ECR_REGISTRY}/${APP_NAME}:latest

if [ $? -eq 0 ]; then
    echo "Successfully pushed ${APP_NAME}:${VERSION} to ECR"
    
    # Start vulnerability scan
    echo "Starting vulnerability scan..."
    aws ecr start-image-scan \
        --repository-name ${APP_NAME} \
        --image-id imageTag=${VERSION}
    
    # Get image URI for deployment
    IMAGE_URI="${ECR_REGISTRY}/${APP_NAME}:${VERSION}"
    echo "Image URI: ${IMAGE_URI}"
    echo "Latest URI: ${ECR_REGISTRY}/${APP_NAME}:latest"
else
    echo "Failed to push images to ECR"
    exit 1
fi

# Cleanup local images
docker rmi ${APP_NAME}:${VERSION} ${ECR_REGISTRY}/${APP_NAME}:${VERSION} ${ECR_REGISTRY}/${APP_NAME}:latest

echo "Build and push completed successfully"
```

### Security Scan Monitor

```bash
#!/bin/bash
# scan-monitor.sh - Monitor ECR vulnerability scans

REPOSITORY_NAME=$1
IMAGE_TAG=${2:-latest}
SEVERITY_THRESHOLD=${3:-HIGH}

if [ -z "$REPOSITORY_NAME" ]; then
    echo "Usage: $0 <repository-name> [image-tag] [severity-threshold]"
    exit 1
fi

echo "Monitoring vulnerability scan for ${REPOSITORY_NAME}:${IMAGE_TAG}"

# Start scan if not already running
aws ecr start-image-scan \
    --repository-name ${REPOSITORY_NAME} \
    --image-id imageTag=${IMAGE_TAG} >/dev/null 2>&1

# Wait for scan to complete
SCAN_STATUS="IN_PROGRESS"
WAIT_TIME=0
MAX_WAIT=300  # 5 minutes

while [ "$SCAN_STATUS" = "IN_PROGRESS" ] && [ $WAIT_TIME -lt $MAX_WAIT ]; do
    echo "Waiting for scan to complete... (${WAIT_TIME}s)"
    sleep 10
    WAIT_TIME=$((WAIT_TIME + 10))
    
    SCAN_STATUS=$(aws ecr describe-image-scan-findings \
        --repository-name ${REPOSITORY_NAME} \
        --image-id imageTag=${IMAGE_TAG} \
        --query 'imageScanStatus.status' \
        --output text 2>/dev/null || echo "IN_PROGRESS")
done

if [ "$SCAN_STATUS" != "COMPLETE" ]; then
    echo "Scan did not complete within timeout period"
    exit 1
fi

# Get scan results
echo "Scan completed. Analyzing results..."

SCAN_RESULTS=$(aws ecr describe-image-scan-findings \
    --repository-name ${REPOSITORY_NAME} \
    --image-id imageTag=${IMAGE_TAG})

# Count vulnerabilities by severity
CRITICAL_COUNT=$(echo "$SCAN_RESULTS" | jq -r '.imageScanFindings.findingCounts.CRITICAL // 0')
HIGH_COUNT=$(echo "$SCAN_RESULTS" | jq -r '.imageScanFindings.findingCounts.HIGH // 0')
MEDIUM_COUNT=$(echo "$SCAN_RESULTS" | jq -r '.imageScanFindings.findingCounts.MEDIUM // 0')
LOW_COUNT=$(echo "$SCAN_RESULTS" | jq -r '.imageScanFindings.findingCounts.LOW // 0')

echo "=== Vulnerability Scan Results ==="
echo "Image: ${REPOSITORY_NAME}:${IMAGE_TAG}"
echo "Critical: ${CRITICAL_COUNT}"
echo "High: ${HIGH_COUNT}"
echo "Medium: ${MEDIUM_COUNT}"
echo "Low: ${LOW_COUNT}"

# Check against threshold
FAIL_SCAN=false

if [ "$SEVERITY_THRESHOLD" = "CRITICAL" ] && [ $CRITICAL_COUNT -gt 0 ]; then
    FAIL_SCAN=true
elif [ "$SEVERITY_THRESHOLD" = "HIGH" ] && [ $((CRITICAL_COUNT + HIGH_COUNT)) -gt 0 ]; then
    FAIL_SCAN=true
elif [ "$SEVERITY_THRESHOLD" = "MEDIUM" ] && [ $((CRITICAL_COUNT + HIGH_COUNT + MEDIUM_COUNT)) -gt 0 ]; then
    FAIL_SCAN=true
fi

if [ "$FAIL_SCAN" = true ]; then
    echo "FAIL: Image contains vulnerabilities above ${SEVERITY_THRESHOLD} threshold"
    
    # Show details of high-severity vulnerabilities
    echo ""
    echo "=== High-Severity Vulnerabilities ==="
    echo "$SCAN_RESULTS" | jq -r '.imageScanFindings.findings[] | select(.severity == "CRITICAL" or .severity == "HIGH") | "\(.name): \(.description[:100])..."'
    
    exit 1
else
    echo "PASS: No vulnerabilities above ${SEVERITY_THRESHOLD} threshold"
    exit 0
fi
```

### Image Promotion Pipeline

```python
# promote-image.py - Promote images between environments
import boto3
import json
import sys
from datetime import datetime

def promote_image(source_repo, source_tag, target_repo, target_tag, region='us-west-2'):
    """Promote an image from one repository/tag to another"""
    
    ecr = boto3.client('ecr', region_name=region)
    
    try:
        # Get source image manifest
        response = ecr.get-download-url_for_layer(
            repositoryName=source_repo,
            layerDigest='dummy'  # This will fail but we're just checking if repo exists
        )
    except ecr.exceptions.RepositoryNotFoundException:
        print(f"Source repository {source_repo} not found")
        return False
    except:
        pass  # Expected to fail, we're just checking repo existence
    
    try:
        # Get image details
        image_details = ecr.describe_images(
            repositoryName=source_repo,
            imageIds=[{'imageTag': source_tag}]
        )
        
        if not image_details['imageDetails']:
            print(f"Image {source_repo}:{source_tag} not found")
            return False
        
        image_detail = image_details['imageDetails'][0]
        image_digest = image_detail['imageDigest']
        
        print(f"Found source image: {source_repo}:{source_tag} (digest: {image_digest})")
        
        # Check if target repository exists
        try:
            ecr.describe_repositories(repositoryNames=[target_repo])
        except ecr.exceptions.RepositoryNotFoundException:
            print(f"Creating target repository: {target_repo}")
            ecr.create_repository(
                repositoryName=target_repo,
                imageScanningConfiguration={'scanOnPush': True},
                encryptionConfiguration={'encryptionType': 'AES256'}
            )
        
        # Get image manifest
        manifest_response = ecr.get_download_url_for_layer(
            repositoryName=source_repo,
            layerDigest=image_digest
        )
        
        # Put image in target repository with new tag
        put_response = ecr.put_image(
            repositoryName=target_repo,
            imageManifest=manifest_response['downloadUrl'],
            imageTag=target_tag
        )
        
        print(f"Successfully promoted image to {target_repo}:{target_tag}")
        
        # Start vulnerability scan on promoted image
        try:
            ecr.start_image_scan(
                repositoryName=target_repo,
                imageId={'imageTag': target_tag}
            )
            print(f"Started vulnerability scan for {target_repo}:{target_tag}")
        except Exception as e:
            print(f"Warning: Could not start vulnerability scan: {e}")
        
        return True
        
    except Exception as e:
        print(f"Error promoting image: {e}")
        return False

def get_promotion_config():
    """Get promotion configuration from file or environment"""
    try:
        with open('promotion-config.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        # Default configuration
        return {
            "environments": {
                "dev": {
                    "repository_suffix": "-dev",
                    "approval_required": False
                },
                "staging": {
                    "repository_suffix": "-staging",
                    "approval_required": False
                },
                "production": {
                    "repository_suffix": "-prod",
                    "approval_required": True
                }
            },
            "promotion_flow": ["dev", "staging", "production"]
        }

def main():
    if len(sys.argv) < 4:
        print("Usage: python promote-image.py <app-name> <version> <target-environment>")
        print("Example: python promote-image.py my-web-app v1.2.3 production")
        sys.exit(1)
    
    app_name = sys.argv[1]
    version = sys.argv[2]
    target_env = sys.argv[3]
    
    config = get_promotion_config()
    
    if target_env not in config['environments']:
        print(f"Unknown environment: {target_env}")
        print(f"Available environments: {list(config['environments'].keys())}")
        sys.exit(1)
    
    # Determine source environment
    promotion_flow = config['promotion_flow']
    target_index = promotion_flow.index(target_env)
    
    if target_index == 0:
        print(f"Cannot promote to {target_env} - it's the first environment in the flow")
        sys.exit(1)
    
    source_env = promotion_flow[target_index - 1]
    
    # Build repository names
    source_repo = f"{app_name}{config['environments'][source_env]['repository_suffix']}"
    target_repo = f"{app_name}{config['environments'][target_env]['repository_suffix']}"
    
    print(f"Promoting {source_repo}:{version} to {target_repo}:{version}")
    
    # Check if approval is required
    if config['environments'][target_env]['approval_required']:
        approval = input(f"Approval required for {target_env} deployment. Continue? (y/N): ")
        if approval.lower() != 'y':
            print("Promotion cancelled")
            sys.exit(1)
    
    # Perform promotion
    if promote_image(source_repo, version, target_repo, version):
        print(f"Successfully promoted {app_name}:{version} to {target_env}")
        
        # Log promotion event
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "app_name": app_name,
            "version": version,
            "source_environment": source_env,
            "target_environment": target_env,
            "promoted_by": "automation"  # Could be enhanced to get actual user
        }
        
        print(f"Promotion log: {json.dumps(log_entry, indent=2)}")
    else:
        print(f"Failed to promote {app_name}:{version} to {target_env}")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

### Repository Cleanup Script

```bash
#!/bin/bash
# ecr-cleanup.sh - Clean up old ECR images based on lifecycle policies

REPOSITORY_NAME=$1
DRY_RUN=${2:-true}

if [ -z "$REPOSITORY_NAME" ]; then
    echo "Usage: $0 <repository-name> [dry-run=true|false]"
    exit 1
fi

echo "ECR Cleanup for repository: ${REPOSITORY_NAME}"
echo "Dry run: ${DRY_RUN}"

# Get current images
IMAGES=$(aws ecr describe-images \
    --repository-name ${REPOSITORY_NAME} \
    --query 'sort_by(imageDetails, &imagePushedAt)' \
    --output json)

TOTAL_IMAGES=$(echo "$IMAGES" | jq length)
echo "Total images found: ${TOTAL_IMAGES}"

# Separate tagged and untagged images
TAGGED_IMAGES=$(echo "$IMAGES" | jq '[.[] | select(.imageTags != null)]')
UNTAGGED_IMAGES=$(echo "$IMAGES" | jq '[.[] | select(.imageTags == null)]')

TAGGED_COUNT=$(echo "$TAGGED_IMAGES" | jq length)
UNTAGGED_COUNT=$(echo "$UNTAGGED_IMAGES" | jq length)

echo "Tagged images: ${TAGGED_COUNT}"
echo "Untagged images: ${UNTAGGED_COUNT}"

# Cleanup old untagged images (older than 7 days)
CUTOFF_DATE=$(date -d '7 days ago' -Iseconds)
OLD_UNTAGGED=$(echo "$UNTAGGED_IMAGES" | jq --arg cutoff "$CUTOFF_DATE" '[.[] | select(.imagePushedAt < $cutoff)]')
OLD_UNTAGGED_COUNT=$(echo "$OLD_UNTAGGED" | jq length)

echo "Untagged images older than 7 days: ${OLD_UNTAGGED_COUNT}"

if [ $OLD_UNTAGGED_COUNT -gt 0 ]; then
    echo "Images to delete (untagged, >7 days):"
    echo "$OLD_UNTAGGED" | jq -r '.[] | "\(.imageDigest) - \(.imagePushedAt)"'
    
    if [ "$DRY_RUN" = "false" ]; then
        # Delete old untagged images
        IMAGE_DIGESTS=$(echo "$OLD_UNTAGGED" | jq -r '.[].imageDigest')
        for digest in $IMAGE_DIGESTS; do
            echo "Deleting untagged image: $digest"
            aws ecr batch-delete-image \
                --repository-name ${REPOSITORY_NAME} \
                --image-ids imageDigest=$digest
        done
    else
        echo "(Dry run - no images deleted)"
    fi
fi

# Keep only last 10 tagged images (excluding 'latest' and version tags starting with 'v')
VERSIONED_IMAGES=$(echo "$TAGGED_IMAGES" | jq '[.[] | select(.imageTags[] | test("^v[0-9]"))]')
VERSIONED_COUNT=$(echo "$VERSIONED_IMAGES" | jq length)

if [ $VERSIONED_COUNT -gt 10 ]; then
    OLD_VERSIONED=$(echo "$VERSIONED_IMAGES" | jq '.[:-10]')  # All but last 10
    OLD_VERSIONED_COUNT=$(echo "$OLD_VERSIONED" | jq length)
    
    echo "Old versioned images to delete (keeping last 10): ${OLD_VERSIONED_COUNT}"
    echo "$OLD_VERSIONED" | jq -r '.[] | "\(.imageTags[0]) - \(.imagePushedAt)"'
    
    if [ "$DRY_RUN" = "false" ]; then
        # Delete old versioned images
        IMAGE_TAGS=$(echo "$OLD_VERSIONED" | jq -r '.[].imageTags[0]')
        for tag in $IMAGE_TAGS; do
            echo "Deleting versioned image: $tag"
            aws ecr batch-delete-image \
                --repository-name ${REPOSITORY_NAME} \
                --image-ids imageTag=$tag
        done
    else
        echo "(Dry run - no images deleted)"
    fi
fi

# Calculate storage savings
if [ "$DRY_RUN" = "false" ]; then
    # Get updated image count
    NEW_IMAGES=$(aws ecr describe-images \
        --repository-name ${REPOSITORY_NAME} \
        --query 'imageDetails' \
        --output json)
    NEW_COUNT=$(echo "$NEW_IMAGES" | jq length)
    DELETED_COUNT=$((TOTAL_IMAGES - NEW_COUNT))
    
    echo "Cleanup completed:"
    echo "  Images before: ${TOTAL_IMAGES}"
    echo "  Images after: ${NEW_COUNT}"
    echo "  Images deleted: ${DELETED_COUNT}"
else
    POTENTIAL_DELETIONS=$((OLD_UNTAGGED_COUNT + OLD_VERSIONED_COUNT))
    echo "Dry run completed - would delete ${POTENTIAL_DELETIONS} images"
    echo "Run with 'false' as second parameter to actually delete images"
fi
```

## Best Practices

### Security Best Practices
- **Enable vulnerability scanning** on all repositories
- **Use immutable image tags** for production deployments
- **Implement least privilege** IAM policies for ECR access
- **Enable encryption at rest** with AWS KMS keys
- **Regular security audits** of stored images

### Cost Optimization
- **Implement lifecycle policies** to automatically clean up old images
- **Use cross-region replication** only when necessary
- **Monitor storage usage** and set up billing alerts
- **Clean up untagged images** regularly
- **Optimize image sizes** to reduce storage and transfer costs

### Operational Excellence
- **Use consistent tagging** strategies across all repositories
- **Implement image promotion** workflows between environments
- **Monitor image pull** metrics for usage analysis
- **Set up automated notifications** for scan results
- **Document repository** purposes and access patterns

### Integration Best Practices
- **Use ECR with ECS/EKS** for seamless container deployments
- **Integrate with CI/CD pipelines** for automated image builds
- **Implement blue-green deployments** with image versioning
- **Use repository policies** for cross-account access
- **Enable CloudTrail** for ECR API auditing