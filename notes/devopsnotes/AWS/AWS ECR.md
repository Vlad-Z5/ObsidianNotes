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

## Advanced Container Security and DevOps Patterns

### Enterprise Container Security Framework

#### Image Security Scanning and Policy Enforcement
```python
# container_security_scanner.py - Advanced container security scanning
import boto3
import json
import re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import requests
from aws_lambda_powertools import Logger, Tracer

logger = Logger()
tracer = Tracer()

@dataclass
class SecurityPolicy:
    """Container security policy configuration"""
    max_critical_vulnerabilities: int = 0
    max_high_vulnerabilities: int = 5
    max_medium_vulnerabilities: int = 20
    allowed_base_images: List[str] = None
    required_labels: List[str] = None
    prohibited_packages: List[str] = None
    max_image_age_days: int = 30
    require_signed_images: bool = True

@dataclass
class ScanResult:
    """Container scan result"""
    repository: str
    tag: str
    digest: str
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    scan_status: str = "PENDING"
    findings: List[Dict] = None
    compliance_status: str = "UNKNOWN"
    remediation_suggestions: List[str] = None

class ContainerSecurityScanner:
    """
    Advanced container security scanner with policy enforcement
    """
    
    def __init__(self, region: str = 'us-west-2'):
        self.ecr = boto3.client('ecr', region_name=region)
        self.inspector = boto3.client('inspector2', region_name=region)
        self.ssm = boto3.client('ssm', region_name=region)
        self.region = region
        
    @tracer.capture_method
    def scan_image_comprehensive(self, repository: str, tag: str, 
                                policy: SecurityPolicy) -> ScanResult:
        """
        Perform comprehensive security scan with policy enforcement
        """
        logger.info(f"Starting comprehensive scan for {repository}:{tag}")
        
        try:
            # Get image details
            image_details = self._get_image_details(repository, tag)
            if not image_details:
                raise ValueError(f"Image {repository}:{tag} not found")
            
            digest = image_details['imageDigest']
            scan_result = ScanResult(
                repository=repository,
                tag=tag,
                digest=digest
            )
            
            # Start enhanced security scan
            self._start_enhanced_scan(repository, tag)
            
            # Wait for scan completion
            scan_data = self._wait_for_scan_completion(repository, tag)
            
            # Parse vulnerability findings
            scan_result = self._parse_vulnerability_findings(scan_result, scan_data)
            
            # Perform additional security checks
            scan_result = self._perform_additional_checks(scan_result, image_details, policy)
            
            # Evaluate against policy
            scan_result.compliance_status = self._evaluate_policy_compliance(scan_result, policy)
            
            # Generate remediation suggestions
            scan_result.remediation_suggestions = self._generate_remediation_suggestions(
                scan_result, policy
            )
            
            logger.info(f"Scan completed: {scan_result.compliance_status}")
            return scan_result
            
        except Exception as e:
            logger.error(f"Scan failed: {str(e)}")
            raise
    
    def _get_image_details(self, repository: str, tag: str) -> Optional[Dict]:
        """Get detailed image information"""
        try:
            response = self.ecr.describe_images(
                repositoryName=repository,
                imageIds=[{'imageTag': tag}]
            )
            return response['imageDetails'][0] if response['imageDetails'] else None
        except Exception as e:
            logger.error(f"Failed to get image details: {str(e)}")
            return None
    
    def _start_enhanced_scan(self, repository: str, tag: str):
        """Start enhanced security scan"""
        try:
            # Start ECR enhanced scanning
            self.ecr.start_image_scan(
                repositoryName=repository,
                imageId={'imageTag': tag}
            )
            
            # Also trigger Inspector v2 scan if available
            try:
                self.inspector.batch_get_finding_details(
                    findingArns=[f"arn:aws:inspector2:{self.region}:*:finding/*"]
                )
            except:
                pass  # Inspector v2 might not be available
                
        except self.ecr.exceptions.LimitExceededException:
            logger.warning("Scan limit exceeded, waiting for existing scans")
        except Exception as e:
            logger.error(f"Failed to start scan: {str(e)}")
    
    def _wait_for_scan_completion(self, repository: str, tag: str, 
                                  timeout: int = 300) -> Dict:
        """Wait for security scan to complete"""
        import time
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = self.ecr.describe_image_scan_findings(
                    repositoryName=repository,
                    imageId={'imageTag': tag}
                )
                
                if response['imageScanStatus']['status'] == 'COMPLETE':
                    return response
                elif response['imageScanStatus']['status'] == 'FAILED':
                    raise Exception(f"Scan failed: {response['imageScanStatus']}")
                
                time.sleep(10)
                
            except self.ecr.exceptions.ScanNotFoundException:
                time.sleep(5)
                continue
        
        raise TimeoutError(f"Scan did not complete within {timeout} seconds")
    
    def _parse_vulnerability_findings(self, scan_result: ScanResult, 
                                     scan_data: Dict) -> ScanResult:
        """Parse vulnerability findings from scan data"""
        
        findings = scan_data.get('imageScanFindings', {})
        finding_counts = findings.get('findingCounts', {})
        
        scan_result.critical_count = finding_counts.get('CRITICAL', 0)
        scan_result.high_count = finding_counts.get('HIGH', 0)
        scan_result.medium_count = finding_counts.get('MEDIUM', 0)
        scan_result.low_count = finding_counts.get('LOW', 0)
        scan_result.findings = findings.get('findings', [])
        scan_result.scan_status = scan_data['imageScanStatus']['status']
        
        return scan_result
    
    def _perform_additional_checks(self, scan_result: ScanResult, 
                                  image_details: Dict, 
                                  policy: SecurityPolicy) -> ScanResult:
        """Perform additional security checks beyond vulnerability scanning"""
        
        # Check image age
        pushed_at = image_details.get('imagePushedAt')
        if pushed_at:
            age_days = (datetime.now(pushed_at.tzinfo) - pushed_at).days
            if age_days > policy.max_image_age_days:
                scan_result.findings.append({
                    'name': 'IMAGE_AGE_VIOLATION',
                    'severity': 'MEDIUM',
                    'description': f'Image is {age_days} days old, exceeds policy limit of {policy.max_image_age_days} days'
                })
        
        # Check image size (flag very large images)
        image_size = image_details.get('imageSizeInBytes', 0)
        if image_size > 2 * 1024 * 1024 * 1024:  # 2GB
            scan_result.findings.append({
                'name': 'LARGE_IMAGE_SIZE',
                'severity': 'LOW',
                'description': f'Image size ({image_size / (1024*1024*1024):.1f}GB) is unusually large'
            })
        
        # Check for required labels
        if policy.required_labels:
            image_manifest = self._get_image_manifest(scan_result.repository, scan_result.tag)
            self._check_required_labels(scan_result, image_manifest, policy.required_labels)
        
        return scan_result
    
    def _get_image_manifest(self, repository: str, tag: str) -> Optional[Dict]:
        """Get image manifest for label inspection"""
        try:
            response = self.ecr.batch_get_image(
                repositoryName=repository,
                imageIds=[{'imageTag': tag}]
            )
            
            if response['images']:
                manifest = json.loads(response['images'][0]['imageManifest'])
                return manifest
            return None
            
        except Exception as e:
            logger.error(f"Failed to get image manifest: {str(e)}")
            return None
    
    def _check_required_labels(self, scan_result: ScanResult, 
                              manifest: Optional[Dict], 
                              required_labels: List[str]):
        """Check for required Docker labels"""
        if not manifest:
            return
        
        # Extract labels from manifest
        config = manifest.get('config', {})
        labels = config.get('Labels', {}) if config else {}
        
        for required_label in required_labels:
            if required_label not in labels:
                scan_result.findings.append({
                    'name': 'MISSING_REQUIRED_LABEL',
                    'severity': 'MEDIUM',
                    'description': f'Required label "{required_label}" is missing'
                })
    
    def _evaluate_policy_compliance(self, scan_result: ScanResult, 
                                   policy: SecurityPolicy) -> str:
        """Evaluate scan results against security policy"""
        
        violations = []
        
        # Check vulnerability counts
        if scan_result.critical_count > policy.max_critical_vulnerabilities:
            violations.append(f"Critical vulnerabilities: {scan_result.critical_count} > {policy.max_critical_vulnerabilities}")
        
        if scan_result.high_count > policy.max_high_vulnerabilities:
            violations.append(f"High vulnerabilities: {scan_result.high_count} > {policy.max_high_vulnerabilities}")
        
        if scan_result.medium_count > policy.max_medium_vulnerabilities:
            violations.append(f"Medium vulnerabilities: {scan_result.medium_count} > {policy.max_medium_vulnerabilities}")
        
        # Check for policy violations in findings
        policy_violations = [f for f in scan_result.findings if 'VIOLATION' in f.get('name', '')]
        violations.extend([f['description'] for f in policy_violations])
        
        if violations:
            logger.warning(f"Policy violations found: {violations}")
            return "NON_COMPLIANT"
        else:
            return "COMPLIANT"
    
    def _generate_remediation_suggestions(self, scan_result: ScanResult, 
                                        policy: SecurityPolicy) -> List[str]:
        """Generate actionable remediation suggestions"""
        
        suggestions = []
        
        # Vulnerability-based suggestions
        if scan_result.critical_count > 0:
            suggestions.append("CRITICAL: Update base image and dependencies immediately")
            suggestions.append("Run 'docker scout cves' for detailed vulnerability analysis")
        
        if scan_result.high_count > policy.max_high_vulnerabilities:
            suggestions.append("Update vulnerable packages using package manager")
            suggestions.append("Consider using distroless or minimal base images")
        
        # Specific CVE remediation
        critical_cves = [f for f in scan_result.findings if f.get('severity') == 'CRITICAL']
        for cve in critical_cves[:3]:  # Show top 3
            cve_id = cve.get('name', 'Unknown')
            suggestions.append(f"Fix {cve_id}: {cve.get('description', '')[:100]}...")
        
        # General security improvements
        if scan_result.medium_count > 10:
            suggestions.append("Consider multi-stage builds to reduce attack surface")
            suggestions.append("Use .dockerignore to exclude unnecessary files")
        
        return suggestions

class ContainerRegistryManager:
    """
    Advanced ECR registry management with security policies
    """
    
    def __init__(self, region: str = 'us-west-2'):
        self.ecr = boto3.client('ecr', region_name=region)
        self.sts = boto3.client('sts')
        self.account_id = self.sts.get_caller_identity()['Account']
        self.region = region
    
    @tracer.capture_method
    def create_secure_repository(self, repository_name: str, 
                                security_config: Dict[str, Any]) -> Dict:
        """
        Create ECR repository with advanced security configuration
        """
        logger.info(f"Creating secure repository: {repository_name}")
        
        try:
            # Create repository with security settings
            repo_response = self.ecr.create_repository(
                repositoryName=repository_name,
                imageScanningConfiguration={
                    'scanOnPush': True
                },
                encryptionConfiguration={
                    'encryptionType': 'KMS',
                    'kmsKey': security_config.get('kms_key_id', 'alias/aws/ecr')
                },
                imageTagMutability='IMMUTABLE' if security_config.get('immutable_tags', True) else 'MUTABLE',
                tags=[
                    {'Key': 'Environment', 'Value': security_config.get('environment', 'production')},
                    {'Key': 'SecurityLevel', 'Value': security_config.get('security_level', 'high')},
                    {'Key': 'AutoCleanup', 'Value': str(security_config.get('auto_cleanup', True))},
                    {'Key': 'CreatedBy', 'Value': 'ContainerRegistryManager'}
                ]
            )
            
            repository_uri = repo_response['repository']['repositoryUri']
            logger.info(f"Created repository: {repository_uri}")
            
            # Set repository policy for cross-account access
            if security_config.get('cross_account_access'):
                self._set_cross_account_policy(repository_name, security_config['cross_account_access'])
            
            # Set lifecycle policy
            if security_config.get('lifecycle_policy'):
                self._set_lifecycle_policy(repository_name, security_config['lifecycle_policy'])
            
            # Enable replication if specified
            if security_config.get('replication_regions'):
                self._setup_replication(repository_name, security_config['replication_regions'])
            
            return {
                'repository_name': repository_name,
                'repository_uri': repository_uri,
                'arn': repo_response['repository']['repositoryArn'],
                'security_config': security_config
            }
            
        except Exception as e:
            logger.error(f"Failed to create repository: {str(e)}")
            raise
    
    def _set_cross_account_policy(self, repository_name: str, 
                                 cross_account_config: Dict):
        """Set cross-account access policy"""
        
        policy_document = {
            "Version": "2012-10-17",
            "Statement": []
        }
        
        # Add read access for specified accounts
        if cross_account_config.get('read_accounts'):
            policy_document["Statement"].append({
                "Effect": "Allow",
                "Principal": {
                    "AWS": [f"arn:aws:iam::{account}:root" for account in cross_account_config['read_accounts']]
                },
                "Action": [
                    "ecr:GetDownloadUrlForLayer",
                    "ecr:BatchGetImage",
                    "ecr:BatchCheckLayerAvailability"
                ]
            })
        
        # Add write access for CI/CD accounts
        if cross_account_config.get('write_accounts'):
            policy_document["Statement"].append({
                "Effect": "Allow",
                "Principal": {
                    "AWS": [f"arn:aws:iam::{account}:root" for account in cross_account_config['write_accounts']]
                },
                "Action": [
                    "ecr:GetDownloadUrlForLayer",
                    "ecr:BatchGetImage",
                    "ecr:BatchCheckLayerAvailability",
                    "ecr:PutImage",
                    "ecr:InitiateLayerUpload",
                    "ecr:UploadLayerPart",
                    "ecr:CompleteLayerUpload"
                ]
            })
        
        try:
            self.ecr.set_repository_policy(
                repositoryName=repository_name,
                policyText=json.dumps(policy_document)
            )
            logger.info(f"Set cross-account policy for {repository_name}")
        except Exception as e:
            logger.error(f"Failed to set repository policy: {str(e)}")
    
    def _set_lifecycle_policy(self, repository_name: str, 
                             lifecycle_config: Dict):
        """Set advanced lifecycle policy"""
        
        rules = []
        
        # Rule for production tagged images
        if lifecycle_config.get('keep_production_images', 10):
            rules.append({
                "rulePriority": 1,
                "description": "Keep last N production images",
                "selection": {
                    "tagStatus": "tagged",
                    "tagPrefixList": ["v", "release-"],
                    "countType": "imageCountMoreThan",
                    "countNumber": lifecycle_config['keep_production_images']
                },
                "action": {"type": "expire"}
            })
        
        # Rule for development images
        if lifecycle_config.get('keep_dev_images', 5):
            rules.append({
                "rulePriority": 2,
                "description": "Keep last N development images",
                "selection": {
                    "tagStatus": "tagged",
                    "tagPrefixList": ["dev-", "feature-"],
                    "countType": "imageCountMoreThan",
                    "countNumber": lifecycle_config['keep_dev_images']
                },
                "action": {"type": "expire"}
            })
        
        # Rule for untagged images
        rules.append({
            "rulePriority": 3,
            "description": "Delete untagged images after N days",
            "selection": {
                "tagStatus": "untagged",
                "countType": "sinceImagePushed",
                "countUnit": "days",
                "countNumber": lifecycle_config.get('untagged_expiry_days', 1)
            },
            "action": {"type": "expire"}
        })
        
        policy_document = {"rules": rules}
        
        try:
            self.ecr.put_lifecycle_policy(
                repositoryName=repository_name,
                lifecyclePolicyText=json.dumps(policy_document)
            )
            logger.info(f"Set lifecycle policy for {repository_name}")
        except Exception as e:
            logger.error(f"Failed to set lifecycle policy: {str(e)}")
    
    def _setup_replication(self, repository_name: str, 
                          replication_regions: List[str]):
        """Setup cross-region replication"""
        
        replication_config = {
            "rules": [{
                "destinations": [
                    {
                        "region": region,
                        "registryId": self.account_id
                    } for region in replication_regions
                ],
                "repositoryFilters": [{
                    "filter": repository_name,
                    "filterType": "PREFIX_MATCH"
                }]
            }]
        }
        
        try:
            self.ecr.put_replication_configuration(
                replicationConfiguration=replication_config
            )
            logger.info(f"Setup replication for {repository_name} to {replication_regions}")
        except Exception as e:
            logger.error(f"Failed to setup replication: {str(e)}")

class ContainerImageSigner:
    """
    Container image signing and verification using AWS services
    """
    
    def __init__(self, region: str = 'us-west-2'):
        self.region = region
        self.signer = boto3.client('signer', region_name=region)
        self.ecr = boto3.client('ecr', region_name=region)
    
    def setup_signing_profile(self, profile_name: str, 
                             validity_period_years: int = 3) -> Dict:
        """Setup code signing profile for container images"""
        
        try:
            response = self.signer.put_signing_profile(
                profileName=profile_name,
                signingMaterial={
                    'certificateArn': self._create_signing_certificate(profile_name)
                },
                platformId='AWSLambda-SHA384-ECDSA',
                signatureValidityPeriod={
                    'value': validity_period_years,
                    'type': 'YEARS'
                },
                tags={
                    'Environment': 'production',
                    'Purpose': 'container-signing'
                }
            )
            
            logger.info(f"Created signing profile: {profile_name}")
            return response
            
        except Exception as e:
            logger.error(f"Failed to create signing profile: {str(e)}")
            raise
    
    def _create_signing_certificate(self, profile_name: str) -> str:
        """Create certificate for code signing"""
        import boto3
        
        acm = boto3.client('acm', region_name=self.region)
        
        try:
            response = acm.request_certificate(
                DomainName=f"container-signing-{profile_name}.internal",
                ValidationMethod='DNS',
                KeyAlgorithm='EC_secp384r1',
                Options={
                    'CertificateTransparencyLoggingPreference': 'ENABLED'
                },
                Tags=[
                    {'Key': 'Purpose', 'Value': 'container-signing'},
                    {'Key': 'Profile', 'Value': profile_name}
                ]
            )
            
            return response['CertificateArn']
            
        except Exception as e:
            logger.error(f"Failed to create certificate: {str(e)}")
            raise

# Example usage and integration script
def main():
    """Example usage of advanced container security features"""
    
    # Initialize components
    scanner = ContainerSecurityScanner()
    registry_manager = ContainerRegistryManager()
    
    # Define security policy
    security_policy = SecurityPolicy(
        max_critical_vulnerabilities=0,
        max_high_vulnerabilities=3,
        max_medium_vulnerabilities=15,
        allowed_base_images=['ubuntu:22.04', 'alpine:3.18'],
        required_labels=['maintainer', 'version', 'environment'],
        max_image_age_days=30,
        require_signed_images=True
    )
    
    # Create secure repository
    repository_config = {
        'environment': 'production',
        'security_level': 'high',
        'immutable_tags': True,
        'auto_cleanup': True,
        'kms_key_id': 'alias/ecr-encryption-key',
        'lifecycle_policy': {
            'keep_production_images': 15,
            'keep_dev_images': 5,
            'untagged_expiry_days': 1
        },
        'replication_regions': ['us-east-1', 'eu-west-1'],
        'cross_account_access': {
            'read_accounts': ['123456789012', '234567890123'],
            'write_accounts': ['123456789012']
        }
    }
    
    # Create repository
    repo_info = registry_manager.create_secure_repository(
        'my-secure-app', 
        repository_config
    )
    
    print(f"Created secure repository: {repo_info['repository_uri']}")
    
    # Scan image
    scan_result = scanner.scan_image_comprehensive(
        'my-secure-app', 
        'latest', 
        security_policy
    )
    
    print(f"Scan completed: {scan_result.compliance_status}")
    print(f"Vulnerabilities: C:{scan_result.critical_count}, H:{scan_result.high_count}, M:{scan_result.medium_count}")
    
    if scan_result.remediation_suggestions:
        print("Remediation suggestions:")
        for suggestion in scan_result.remediation_suggestions:
            print(f"  - {suggestion}")

if __name__ == "__main__":
    main()
```

### Advanced CI/CD Integration with Container Security

#### Secure Container Build Pipeline
```yaml
# .github/workflows/secure-container-build.yml
name: Secure Container Build and Deploy

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

env:
  AWS_REGION: us-west-2
  ECR_REGISTRY: ${{ secrets.AWS_ACCOUNT_ID }}.dkr.ecr.us-west-2.amazonaws.com
  
jobs:
  security-scan:
    name: Security Scanning
    runs-on: ubuntu-latest
    outputs:
      image-digest: ${{ steps.build.outputs.digest }}
      security-passed: ${{ steps.security-check.outputs.passed }}
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
      
    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v3
      
    - name: Configure AWS credentials
      uses: aws-actions/configure-aws-credentials@v4
      with:
        role-to-assume: ${{ secrets.AWS_ROLE_ARN }}
        role-session-name: GitHubActions
        aws-region: ${{ env.AWS_REGION }}
        
    - name: Login to Amazon ECR
      id: login-ecr
      uses: aws-actions/amazon-ecr-login@v2
      
    - name: Extract metadata
      id: meta
      uses: docker/metadata-action@v5
      with:
        images: ${{ env.ECR_REGISTRY }}/${{ github.event.repository.name }}
        tags: |
          type=ref,event=branch
          type=ref,event=pr
          type=sha,prefix={{branch}}-
          type=raw,value=latest,enable={{is_default_branch}}
        labels: |
          org.opencontainers.image.title=${{ github.event.repository.name }}
          org.opencontainers.image.description=${{ github.event.repository.description }}
          org.opencontainers.image.vendor=${{ github.repository_owner }}
          org.opencontainers.image.version=${{ github.sha }}
          maintainer=${{ github.actor }}
          environment=${{ github.ref_name == 'main' && 'production' || 'development' }}
          
    - name: Build container image
      id: build
      uses: docker/build-push-action@v5
      with:
        context: .
        platforms: linux/amd64,linux/arm64
        push: false
        tags: ${{ steps.meta.outputs.tags }}
        labels: ${{ steps.meta.outputs.labels }}
        cache-from: type=gha
        cache-to: type=gha,mode=max
        outputs: type=docker,dest=/tmp/image.tar
        
    - name: Load image for scanning
      run: docker load -i /tmp/image.tar
      
    - name: Run Trivy vulnerability scanner
      uses: aquasecurity/trivy-action@master
      with:
        image-ref: '${{ env.ECR_REGISTRY }}/${{ github.event.repository.name }}:${{ github.sha }}'
        format: 'sarif'
        output: 'trivy-results.sarif'
        severity: 'CRITICAL,HIGH,MEDIUM'
        
    - name: Upload Trivy scan results to GitHub Security tab
      uses: github/codeql-action/upload-sarif@v3
      if: always()
      with:
        sarif_file: 'trivy-results.sarif'
        
    - name: Run Grype vulnerability scanner
      uses: anchore/scan-action@v3
      id: grype-scan
      with:
        image: '${{ env.ECR_REGISTRY }}/${{ github.event.repository.name }}:${{ github.sha }}'
        fail-build: false
        severity-cutoff: high
        
    - name: Run Syft SBOM generator
      uses: anchore/sbom-action@v0
      with:
        image: '${{ env.ECR_REGISTRY }}/${{ github.event.repository.name }}:${{ github.sha }}'
        format: 'spdx-json'
        output-file: 'sbom.spdx.json'
        
    - name: Docker Scout CVE scan
      uses: docker/scout-action@v1
      with:
        command: cves
        image: '${{ env.ECR_REGISTRY }}/${{ github.event.repository.name }}:${{ github.sha }}'
        sarif-file: 'scout-results.sarif'
        summary: true
        
    - name: Security policy check
      id: security-check
      run: |
        # Custom security policy enforcement
        python3 -c "
        import json, sys
        
        # Load Trivy results
        try:
            with open('trivy-results.sarif') as f:
                trivy_data = json.load(f)
            
            critical_count = 0
            high_count = 0
            
            for run in trivy_data.get('runs', []):
                for result in run.get('results', []):
                    for rule_result in result.get('ruleResults', []):
                        level = rule_result.get('level', 'note')
                        if level == 'error':
                            critical_count += 1
                        elif level == 'warning':
                            high_count += 1
            
            print(f'Critical vulnerabilities: {critical_count}')
            print(f'High vulnerabilities: {high_count}')
            
            # Security policy: No critical, max 5 high
            if critical_count > 0:
                print('FAIL: Critical vulnerabilities found')
                sys.exit(1)
            elif high_count > 5:
                print(f'FAIL: Too many high vulnerabilities ({high_count} > 5)')
                sys.exit(1)
            else:
                print('PASS: Security policy compliance met')
                print('passed=true' >> '$GITHUB_OUTPUT')
                
        except Exception as e:
            print(f'Error checking security policy: {e}')
            sys.exit(1)
        "
        
    - name: Push image to ECR (if security passed)
      if: steps.security-check.outputs.passed == 'true'
      uses: docker/build-push-action@v5
      with:
        context: .
        platforms: linux/amd64,linux/arm64
        push: true
        tags: ${{ steps.meta.outputs.tags }}
        labels: ${{ steps.meta.outputs.labels }}
        cache-from: type=gha
        
    - name: Start ECR enhanced scan
      if: steps.security-check.outputs.passed == 'true'
      run: |
        aws ecr start-image-scan \
          --repository-name ${{ github.event.repository.name }} \
          --image-id imageTag=${{ github.sha }}
          
    - name: Upload artifacts
      uses: actions/upload-artifact@v4
      if: always()
      with:
        name: security-reports
        path: |
          trivy-results.sarif
          scout-results.sarif
          sbom.spdx.json
        retention-days: 30

  deploy-staging:
    name: Deploy to Staging
    needs: [security-scan]
    if: github.ref == 'refs/heads/develop' && needs.security-scan.outputs.security-passed == 'true'
    runs-on: ubuntu-latest
    environment: staging
    
    steps:
    - name: Deploy to EKS Staging
      run: |
        # Update Kubernetes deployment with new image
        kubectl set image deployment/myapp \
          myapp=${{ env.ECR_REGISTRY }}/${{ github.event.repository.name }}:${{ github.sha }} \
          --namespace=staging
          
        # Wait for rollout to complete
        kubectl rollout status deployment/myapp --namespace=staging --timeout=300s

  deploy-production:
    name: Deploy to Production
    needs: [security-scan]
    if: github.ref == 'refs/heads/main' && needs.security-scan.outputs.security-passed == 'true'
    runs-on: ubuntu-latest
    environment: production
    
    steps:
    - name: Sign container image
      run: |
        # Sign the container image using AWS Signer
        aws signer start-signing-job \
          --source 's3Source={bucketName=my-source-bucket,key=image-manifest.json,version=1}' \
          --destination 's3Destination={bucketName=my-signed-bucket,prefix=signed-images/}' \
          --profile-name production-signing-profile
          
    - name: Deploy to EKS Production
      run: |
        # Update Kubernetes deployment with signed image
        kubectl set image deployment/myapp \
          myapp=${{ env.ECR_REGISTRY }}/${{ github.event.repository.name }}:${{ github.sha }} \
          --namespace=production
          
        # Wait for rollout to complete
        kubectl rollout status deployment/myapp --namespace=production --timeout=600s
        
    - name: Run smoke tests
      run: |
        # Run post-deployment smoke tests
        kubectl run smoke-test \
          --image=curlimages/curl \
          --restart=Never \
          --rm -i \
          --namespace=production \
          -- curl -f http://myapp-service/health
```

### Container Registry Governance and Compliance

#### Advanced Repository Policies and Automation
```python
# ecr_governance.py - ECR governance and compliance automation
import boto3
import json
from typing import Dict, List, Any
from dataclasses import dataclass
from datetime import datetime, timedelta

@dataclass
class GovernancePolicy:
    """Container registry governance policy"""
    require_vulnerability_scan: bool = True
    max_image_age_days: int = 90
    require_image_signing: bool = False
    allowed_base_images: List[str] = None
    prohibited_packages: List[str] = None
    require_labels: List[str] = None
    max_repository_size_gb: float = 100.0
    compliance_frameworks: List[str] = None

class ECRGovernanceEngine:
    """
    ECR governance and compliance enforcement engine
    """
    
    def __init__(self, region: str = 'us-west-2'):
        self.ecr = boto3.client('ecr', region_name=region)
        self.ssm = boto3.client('ssm', region_name=region)
        self.sns = boto3.client('sns', region_name=region)
        self.region = region
        
    def audit_repositories(self, governance_policy: GovernancePolicy) -> Dict[str, Any]:
        """
        Comprehensive audit of all ECR repositories
        """
        audit_results = {
            'total_repositories': 0,
            'compliant_repositories': 0,
            'non_compliant_repositories': 0,
            'violations': [],
            'recommendations': [],
            'cost_savings_opportunities': []
        }
        
        try:
            # Get all repositories
            repositories = self._get_all_repositories()
            audit_results['total_repositories'] = len(repositories)
            
            for repo in repositories:
                repo_audit = self._audit_single_repository(repo, governance_policy)
                
                if repo_audit['compliant']:
                    audit_results['compliant_repositories'] += 1
                else:
                    audit_results['non_compliant_repositories'] += 1
                    audit_results['violations'].extend(repo_audit['violations'])
                
                audit_results['recommendations'].extend(repo_audit['recommendations'])
                audit_results['cost_savings_opportunities'].extend(repo_audit['cost_opportunities'])
            
            # Generate compliance report
            compliance_percentage = (audit_results['compliant_repositories'] / 
                                   audit_results['total_repositories']) * 100
            
            audit_results['compliance_percentage'] = compliance_percentage
            audit_results['audit_timestamp'] = datetime.now().isoformat()
            
            return audit_results
            
        except Exception as e:
            print(f"Audit failed: {str(e)}")
            raise
    
    def _get_all_repositories(self) -> List[Dict]:
        """Get all ECR repositories with pagination"""
        repositories = []
        paginator = self.ecr.get_paginator('describe_repositories')
        
        for page in paginator.paginate():
            repositories.extend(page['repositories'])
        
        return repositories
    
    def _audit_single_repository(self, repository: Dict, 
                                governance_policy: GovernancePolicy) -> Dict:
        """Audit a single repository against governance policy"""
        
        repo_name = repository['repositoryName']
        violations = []
        recommendations = []
        cost_opportunities = []
        
        # Check repository configuration
        if not repository.get('imageScanningConfiguration', {}).get('scanOnPush', False):
            if governance_policy.require_vulnerability_scan:
                violations.append({
                    'repository': repo_name,
                    'type': 'SCANNING_DISABLED',
                    'severity': 'HIGH',
                    'description': 'Vulnerability scanning on push is disabled'
                })
        
        # Check repository size and cost optimization
        repo_size = self._calculate_repository_size(repo_name)
        if repo_size > governance_policy.max_repository_size_gb:
            violations.append({
                'repository': repo_name,
                'type': 'REPOSITORY_TOO_LARGE',
                'severity': 'MEDIUM',
                'description': f'Repository size ({repo_size:.1f}GB) exceeds limit ({governance_policy.max_repository_size_gb}GB)'
            })
        
        # Check lifecycle policy
        lifecycle_policy = self._get_lifecycle_policy(repo_name)
        if not lifecycle_policy:
            cost_opportunities.append({
                'repository': repo_name,
                'type': 'MISSING_LIFECYCLE_POLICY',
                'potential_savings': f'${repo_size * 0.10:.2f}/month',
                'description': 'No lifecycle policy configured for automatic cleanup'
            })
        
        # Check images for compliance
        images = self._get_repository_images(repo_name)
        old_images = self._find_old_images(images, governance_policy.max_image_age_days)
        
        if old_images:
            violations.append({
                'repository': repo_name,
                'type': 'OLD_IMAGES',
                'severity': 'MEDIUM',
                'description': f'{len(old_images)} images older than {governance_policy.max_image_age_days} days'
            })
        
        # Check for untagged images
        untagged_images = [img for img in images if not img.get('imageTags')]
        if untagged_images:
            cost_opportunities.append({
                'repository': repo_name,
                'type': 'UNTAGGED_IMAGES',
                'potential_savings': f'${len(untagged_images) * 0.01:.2f}/month',
                'description': f'{len(untagged_images)} untagged images can be cleaned up'
            })
        
        # Generate recommendations
        if violations:
            recommendations.append({
                'repository': repo_name,
                'priority': 'HIGH',
                'action': 'Enable vulnerability scanning and implement lifecycle policies'
            })
        
        if cost_opportunities:
            recommendations.append({
                'repository': repo_name,
                'priority': 'MEDIUM',
                'action': 'Implement automated cleanup to reduce storage costs'
            })
        
        return {
            'repository': repo_name,
            'compliant': len(violations) == 0,
            'violations': violations,
            'recommendations': recommendations,
            'cost_opportunities': cost_opportunities
        }
    
    def _calculate_repository_size(self, repository_name: str) -> float:
        """Calculate total repository size in GB"""
        try:
            images = self.ecr.describe_images(repositoryName=repository_name)
            total_size = sum(img.get('imageSizeInBytes', 0) for img in images['imageDetails'])
            return total_size / (1024 ** 3)  # Convert to GB
        except Exception:
            return 0.0
    
    def _get_lifecycle_policy(self, repository_name: str) -> Dict:
        """Get repository lifecycle policy"""
        try:
            response = self.ecr.get_lifecycle_policy(repositoryName=repository_name)
            return json.loads(response['lifecyclePolicyText'])
        except self.ecr.exceptions.LifecyclePolicyNotFoundException:
            return None
        except Exception:
            return None
    
    def _get_repository_images(self, repository_name: str) -> List[Dict]:
        """Get all images in repository"""
        try:
            response = self.ecr.describe_images(repositoryName=repository_name)
            return response['imageDetails']
        except Exception:
            return []
    
    def _find_old_images(self, images: List[Dict], max_age_days: int) -> List[Dict]:
        """Find images older than specified days"""
        cutoff_date = datetime.now() - timedelta(days=max_age_days)
        old_images = []
        
        for image in images:
            pushed_at = image.get('imagePushedAt')
            if pushed_at and pushed_at.replace(tzinfo=None) < cutoff_date:
                old_images.append(image)
        
        return old_images
    
    def generate_compliance_report(self, audit_results: Dict) -> str:
        """Generate detailed compliance report"""
        
        report = f"""
# ECR Governance Compliance Report
Generated: {audit_results['audit_timestamp']}

## Summary
- Total Repositories: {audit_results['total_repositories']}
- Compliant: {audit_results['compliant_repositories']}
- Non-Compliant: {audit_results['non_compliant_repositories']}
- Compliance Rate: {audit_results['compliance_percentage']:.1f}%

## Violations by Severity
"""
        
        # Group violations by severity
        violations_by_severity = {}
        for violation in audit_results['violations']:
            severity = violation['severity']
            if severity not in violations_by_severity:
                violations_by_severity[severity] = []
            violations_by_severity[severity].append(violation)
        
        for severity in ['HIGH', 'MEDIUM', 'LOW']:
            if severity in violations_by_severity:
                report += f"\n### {severity} ({len(violations_by_severity[severity])} issues)\n"
                for violation in violations_by_severity[severity]:
                    report += f"- **{violation['repository']}**: {violation['description']}\n"
        
        # Cost savings opportunities
        if audit_results['cost_savings_opportunities']:
            report += "\n## Cost Optimization Opportunities\n"
            total_potential_savings = 0
            for opportunity in audit_results['cost_savings_opportunities']:
                report += f"- **{opportunity['repository']}**: {opportunity['description']}\n"
                # Extract savings amount (simplified)
                if 'potential_savings' in opportunity:
                    savings_str = opportunity['potential_savings'].replace('$', '').replace('/month', '')
                    try:
                        total_potential_savings += float(savings_str)
                    except:
                        pass
            
            report += f"\n**Total Potential Monthly Savings: ${total_potential_savings:.2f}**\n"
        
        # Recommendations
        if audit_results['recommendations']:
            report += "\n## Recommended Actions\n"
            for rec in audit_results['recommendations']:
                report += f"- **{rec['repository']}** ({rec['priority']}): {rec['action']}\n"
        
        return report

def main():
    """Example usage of ECR governance engine"""
    
    # Define governance policy
    policy = GovernancePolicy(
        require_vulnerability_scan=True,
        max_image_age_days=60,
        require_image_signing=True,
        allowed_base_images=['ubuntu:22.04', 'alpine:3.18', 'python:3.11-slim'],
        require_labels=['maintainer', 'version', 'environment'],
        max_repository_size_gb=50.0,
        compliance_frameworks=['SOC2', 'PCI-DSS']
    )
    
    # Run governance audit
    governance_engine = ECRGovernanceEngine()
    audit_results = governance_engine.audit_repositories(policy)
    
    # Generate and print report
    report = governance_engine.generate_compliance_report(audit_results)
    print(report)
    
    # Save report to file
    with open(f"ecr-compliance-report-{datetime.now().strftime('%Y%m%d')}.md", 'w') as f:
        f.write(report)

if __name__ == "__main__":
    main()
```

This comprehensive enhancement transforms AWS ECR into an enterprise-grade container registry with advanced security scanning, governance policies, automated compliance checking, and sophisticated DevOps integration patterns.