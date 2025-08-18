# AWS Secrets Manager

> **Service Type:** Security & Secret Management | **Tier:** CI/CD and Automation | **Global/Regional:** Regional

## Overview

AWS Secrets Manager helps you protect secrets needed to access your applications, services, and IT resources. It enables you to store, rotate, and manage access to secrets such as database credentials, application passwords, OAuth tokens, API keys, and other sensitive information throughout their lifecycle.

## DevOps Use Cases

### Application Security Management
- **Database credentials** automatic rotation without application downtime
- **API keys** centralized storage and access control for third-party integrations
- **Application secrets** secure distribution to containers and Lambda functions
- **Cross-environment management** with environment-specific secret versions

### CI/CD Pipeline Security
- **Build secrets** secure access to private repositories and registries
- **Deployment credentials** automated secret injection during deployments
- **Third-party integrations** secure storage of CI/CD tool authentication
- **Multi-environment promotion** with automated secret synchronization

### Infrastructure Automation
- **Terraform secrets** secure variable management for IaC deployments
- **Configuration management** dynamic secret injection for applications
- **Container orchestration** seamless secret mounting in ECS and EKS
- **Serverless applications** Lambda environment variable encryption

### Compliance and Governance
- **Audit trails** comprehensive logging of secret access and modifications
- **Access control** fine-grained IAM policies for secret permissions
- **Encryption** end-to-end encryption with customer-managed KMS keys
- **Compliance reporting** automated secret usage and rotation tracking

### DevOps Automation
- **Automatic rotation** for database, SSH, and API credentials
- **Zero-downtime updates** application secret rotation without restarts
- **Secret lifecycle management** automated expiration and renewal
- **Cross-service integration** with RDS, DocumentDB, and Redshift

## Core Features

### Secret Storage and Management
- **Multiple secret types** text, binary, and structured JSON secrets
- **Version control** automatic versioning with labels (AWSCURRENT, AWSPENDING)
- **Encryption** at rest and in transit using AWS KMS
- **Cross-region replication** for disaster recovery and global applications

### Automatic Rotation
- **Database rotation** built-in rotation for RDS, Aurora, DocumentDB, Redshift
- **Custom rotation** Lambda-based rotation for custom applications
- **Rotation schedules** configurable rotation intervals and windows
- **Multi-user rotation** alternating between database users for zero downtime

### Access Control and Security
- **IAM integration** resource-based and identity-based policies
- **VPC endpoints** private network access without internet connectivity
- **Resource policies** cross-account access with fine-grained controls
- **Condition keys** time-based and IP-based access restrictions

### Integration Capabilities
- **AWS SDKs** native integration across all programming languages
- **Parameter Store** seamless migration path from Systems Manager
- **ECS/EKS integration** automatic secret mounting and environment injection
- **Lambda integration** environment variable and code-based access

## Secret Types and Structure

### Database Secrets

```json
{
  "username": "admin",
  "password": "super-secret-password",
  "engine": "mysql",
  "host": "mydb.cluster-abc123.us-west-2.rds.amazonaws.com",
  "port": 3306,
  "dbname": "production"
}
```

### API Key Secrets

```json
{
  "api_key": "ak_1234567890abcdef",
  "api_secret": "as_abcdef1234567890",
  "endpoint": "https://api.example.com/v1",
  "environment": "production"
}
```

### Application Configuration

```json
{
  "database_url": "postgresql://user:pass@host:5432/db",
  "redis_url": "redis://redis.example.com:6379",
  "encryption_key": "base64-encoded-key",
  "jwt_secret": "jwt-signing-secret",
  "third_party_tokens": {
    "slack": "xoxb-token",
    "github": "ghp_token"
  }
}
```

## Practical CLI Examples

### Secret Management Operations

```bash
# Create a database secret
aws secretsmanager create-secret \
  --name "prod/myapp/database" \
  --description "Production database credentials for MyApp" \
  --secret-string '{
    "username": "dbadmin",
    "password": "MySecureP@ssw0rd123!",
    "engine": "postgres",
    "host": "myapp-prod.cluster-abc123.us-west-2.rds.amazonaws.com",
    "port": 5432,
    "dbname": "myapp_production"
  }' \
  --kms-key-id alias/secrets-manager-key \
  --tags '[
    {"Key": "Environment", "Value": "Production"},
    {"Key": "Application", "Value": "MyApp"},
    {"Key": "Owner", "Value": "DevOps"}
  ]'

# Create API key secret
aws secretsmanager create-secret \
  --name "prod/myapp/stripe-api" \
  --description "Stripe API credentials" \
  --secret-string '{
    "publishable_key": "pk_live_1234567890abcdef",
    "secret_key": "sk_live_abcdef1234567890",
    "webhook_secret": "whsec_1234567890abcdef"
  }'

# Update secret value
aws secretsmanager update-secret \
  --secret-id "prod/myapp/database" \
  --secret-string '{
    "username": "dbadmin",
    "password": "NewSecureP@ssw0rd456!",
    "engine": "postgres",
    "host": "myapp-prod.cluster-abc123.us-west-2.rds.amazonaws.com",
    "port": 5432,
    "dbname": "myapp_production"
  }'

# Put secret value with version stage
aws secretsmanager put-secret-value \
  --secret-id "prod/myapp/api-key" \
  --secret-string "new-api-key-value" \
  --version-stages AWSPENDING

# Promote pending version to current
aws secretsmanager update-secret-version-stage \
  --secret-id "prod/myapp/api-key" \
  --version-stage AWSCURRENT \
  --move-to-version-id "$(aws secretsmanager describe-secret --secret-id prod/myapp/api-key --query 'VersionIdsToStages | to_entries(@)[?value[0]==`AWSPENDING`] | [0].key' --output text)"
```

### Secret Retrieval Operations

```bash
# Get secret value
aws secretsmanager get-secret-value \
  --secret-id "prod/myapp/database" \
  --query 'SecretString' \
  --output text

# Get specific version
aws secretsmanager get-secret-value \
  --secret-id "prod/myapp/database" \
  --version-stage AWSPENDING

# Get secret metadata
aws secretsmanager describe-secret \
  --secret-id "prod/myapp/database"

# List all secrets
aws secretsmanager list-secrets \
  --filter Key="tag-key",Values="Environment" \
  --sort-order asc

# Batch retrieve secrets
aws secretsmanager batch-get-secret-value \
  --secret-id-list "prod/myapp/database" "prod/myapp/stripe-api" "prod/myapp/jwt-secret"
```

### Rotation Management

```bash
# Enable automatic rotation
aws secretsmanager rotate-secret \
  --secret-id "prod/myapp/database" \
  --rotation-lambda-arn "arn:aws:lambda:us-west-2:123456789012:function:rds-postgres-rotation" \
  --rotation-rules AutomaticallyAfterDays=30

# Configure rotation for RDS
aws secretsmanager update-secret \
  --secret-id "prod/myapp/database" \
  --rotation-lambda-arn "arn:aws:lambda:us-west-2:123456789012:function:SecretsManagerRDSPostgreSQLRotationSingleUser" \
  --rotation-rules '{
    "AutomaticallyAfterDays": 30
  }'

# Immediately rotate secret
aws secretsmanager rotate-secret \
  --secret-id "prod/myapp/database" \
  --force-rotate-immediately

# Cancel in-progress rotation
aws secretsmanager cancel-rotate-secret \
  --secret-id "prod/myapp/database"

# Get rotation status
aws secretsmanager describe-secret \
  --secret-id "prod/myapp/database" \
  --query '{
    Name: Name,
    RotationEnabled: RotationEnabled,
    RotationLambdaARN: RotationLambdaARN,
    RotationRules: RotationRules,
    LastRotatedDate: LastRotatedDate,
    NextRotationDate: NextRotationDate
  }'
```

### Access Control Management

```bash
# Set resource policy
cat > secret-policy.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::123456789012:role/MyAppRole"
      },
      "Action": "secretsmanager:GetSecretValue",
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "secretsmanager:VersionStage": "AWSCURRENT"
        }
      }
    },
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::123456789012:role/DevOpsRole"
      },
      "Action": [
        "secretsmanager:DescribeSecret",
        "secretsmanager:GetSecretValue",
        "secretsmanager:PutSecretValue",
        "secretsmanager:UpdateSecret"
      ],
      "Resource": "*"
    }
  ]
}
EOF

aws secretsmanager put-resource-policy \
  --secret-id "prod/myapp/database" \
  --resource-policy file://secret-policy.json \
  --block-public-policy

# Remove resource policy
aws secretsmanager delete-resource-policy \
  --secret-id "prod/myapp/database"

# Get resource policy
aws secretsmanager get-resource-policy \
  --secret-id "prod/myapp/database"
```

## DevOps Automation Scripts

### Secret Provisioning and Management

```bash
#!/bin/bash
# provision-secrets.sh - Automated secret provisioning for new environments

ENVIRONMENT=$1
APP_NAME=$2
CONFIG_FILE=$3

if [ $# -ne 3 ]; then
    echo "Usage: $0 <environment> <app-name> <config-file>"
    exit 1
fi

echo "Provisioning secrets for ${APP_NAME} in ${ENVIRONMENT} environment"

# Validate configuration file
if [ ! -f "$CONFIG_FILE" ]; then
    echo "Configuration file not found: $CONFIG_FILE"
    exit 1
fi

# Read configuration
CONFIG=$(cat "$CONFIG_FILE")

# Create KMS key for environment if it doesn't exist
KMS_KEY_ALIAS="alias/secrets-manager-${ENVIRONMENT}"
if ! aws kms describe-key --key-id "$KMS_KEY_ALIAS" >/dev/null 2>&1; then
    echo "Creating KMS key for environment: $ENVIRONMENT"
    
    KMS_KEY_ID=$(aws kms create-key \
        --description "Secrets Manager key for ${ENVIRONMENT} environment" \
        --key-usage ENCRYPT_DECRYPT \
        --key-spec SYMMETRIC_DEFAULT \
        --query 'KeyMetadata.KeyId' \
        --output text)
    
    aws kms create-alias \
        --alias-name "$KMS_KEY_ALIAS" \
        --target-key-id "$KMS_KEY_ID"
    
    echo "Created KMS key: $KMS_KEY_ID"
fi

# Process each secret from configuration
echo "$CONFIG" | jq -r '.secrets[] | @base64' | while IFS= read -r secret_data; do
    secret_json=$(echo "$secret_data" | base64 -d)
    
    secret_name=$(echo "$secret_json" | jq -r '.name')
    secret_description=$(echo "$secret_json" | jq -r '.description')
    secret_value=$(echo "$secret_json" | jq -r '.value')
    secret_type=$(echo "$secret_json" | jq -r '.type // "string"')
    rotation_enabled=$(echo "$secret_json" | jq -r '.rotation_enabled // false')
    rotation_days=$(echo "$secret_json" | jq -r '.rotation_days // 30')
    
    # Construct full secret name
    FULL_SECRET_NAME="${ENVIRONMENT}/${APP_NAME}/${secret_name}"
    
    echo "Processing secret: $FULL_SECRET_NAME"
    
    # Check if secret exists
    if aws secretsmanager describe-secret --secret-id "$FULL_SECRET_NAME" >/dev/null 2>&1; then
        echo "Secret $FULL_SECRET_NAME already exists, updating..."
        
        aws secretsmanager update-secret \
            --secret-id "$FULL_SECRET_NAME" \
            --description "$secret_description" \
            --secret-string "$secret_value" \
            --kms-key-id "$KMS_KEY_ALIAS"
    else
        echo "Creating new secret: $FULL_SECRET_NAME"
        
        aws secretsmanager create-secret \
            --name "$FULL_SECRET_NAME" \
            --description "$secret_description" \
            --secret-string "$secret_value" \
            --kms-key-id "$KMS_KEY_ALIAS" \
            --tags "[
                {\"Key\": \"Environment\", \"Value\": \"$ENVIRONMENT\"},
                {\"Key\": \"Application\", \"Value\": \"$APP_NAME\"},
                {\"Key\": \"Type\", \"Value\": \"$secret_type\"},
                {\"Key\": \"ManagedBy\", \"Value\": \"automation\"}
            ]"
    fi
    
    # Configure rotation if enabled
    if [ "$rotation_enabled" = "true" ]; then
        echo "Configuring rotation for $FULL_SECRET_NAME"
        
        # Determine rotation function based on secret type
        case $secret_type in
            "database")
                ROTATION_FUNCTION="arn:aws:lambda:us-west-2:123456789012:function:SecretsManagerRDSPostgreSQLRotationSingleUser"
                ;;
            "api_key")
                ROTATION_FUNCTION="arn:aws:lambda:us-west-2:123456789012:function:custom-api-key-rotation"
                ;;
            *)
                echo "No rotation function available for type: $secret_type"
                continue
                ;;
        esac
        
        aws secretsmanager update-secret \
            --secret-id "$FULL_SECRET_NAME" \
            --rotation-lambda-arn "$ROTATION_FUNCTION" \
            --rotation-rules "AutomaticallyAfterDays=$rotation_days"
    fi
    
    echo "Successfully processed: $FULL_SECRET_NAME"
done

echo "Secret provisioning completed for ${APP_NAME} in ${ENVIRONMENT}"
```

### Secret Rotation Automation

```python
# secret-rotation-manager.py - Automated secret rotation management
import boto3
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SecretRotationManager:
    def __init__(self, region_name: str = 'us-west-2'):
        self.secrets_client = boto3.client('secretsmanager', region_name=region_name)
        self.lambda_client = boto3.client('lambda', region_name=region_name)
        self.sns_client = boto3.client('sns', region_name=region_name)
        
    def get_secrets_due_for_rotation(self, days_ahead: int = 7) -> List[Dict]:
        """Get secrets that are due for rotation within specified days"""
        
        secrets_due = []
        paginator = self.secrets_client.get_paginator('list_secrets')
        
        for page in paginator.paginate():
            for secret in page['SecretList']:
                if not secret.get('RotationEnabled', False):
                    continue
                
                secret_arn = secret['ARN']
                
                # Get detailed secret information
                try:
                    detail = self.secrets_client.describe_secret(SecretId=secret_arn)
                    
                    next_rotation = detail.get('NextRotationDate')
                    if next_rotation:
                        days_until_rotation = (next_rotation.date() - datetime.now().date()).days
                        
                        if days_until_rotation <= days_ahead:
                            secrets_due.append({
                                'name': detail['Name'],
                                'arn': secret_arn,
                                'next_rotation': next_rotation,
                                'days_until': days_until_rotation,
                                'rotation_lambda': detail.get('RotationLambdaARN'),
                                'rotation_rules': detail.get('RotationRules', {})
                            })
                except Exception as e:
                    logger.error(f"Error getting details for secret {secret_arn}: {e}")
        
        return sorted(secrets_due, key=lambda x: x['days_until'])
    
    def rotate_secret_safely(self, secret_arn: str, force: bool = False) -> bool:
        """Safely rotate a secret with validation and rollback capability"""
        
        try:
            logger.info(f"Starting rotation for secret: {secret_arn}")
            
            # Get current secret value for rollback
            current_secret = self.secrets_client.get_secret_value(
                SecretId=secret_arn,
                VersionStage='AWSCURRENT'
            )
            
            # Perform rotation
            response = self.secrets_client.rotate_secret(
                SecretId=secret_arn,
                ForceRotateImmediately=force
            )
            
            rotation_id = response.get('VersionId')
            logger.info(f"Rotation initiated with version ID: {rotation_id}")
            
            # Monitor rotation progress
            return self._monitor_rotation(secret_arn, rotation_id)
            
        except Exception as e:
            logger.error(f"Failed to rotate secret {secret_arn}: {e}")
            return False
    
    def _monitor_rotation(self, secret_arn: str, rotation_id: str, timeout_minutes: int = 30) -> bool:
        """Monitor rotation progress and handle failures"""
        
        import time
        start_time = datetime.now()
        timeout = timedelta(minutes=timeout_minutes)
        
        while datetime.now() - start_time < timeout:
            try:
                # Check rotation status
                detail = self.secrets_client.describe_secret(SecretId=secret_arn)
                versions = detail.get('VersionIdsToStages', {})
                
                if rotation_id in versions:
                    stages = versions[rotation_id]
                    
                    if 'AWSCURRENT' in stages:
                        logger.info(f"Rotation completed successfully for {secret_arn}")
                        return True
                    elif 'AWSPENDING' in stages:
                        logger.info(f"Rotation in progress for {secret_arn}")
                    else:
                        logger.warning(f"Unexpected rotation state for {secret_arn}: {stages}")
                
                time.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Error monitoring rotation for {secret_arn}: {e}")
                return False
        
        logger.error(f"Rotation timeout for {secret_arn}")
        return False
    
    def validate_secret_connectivity(self, secret_arn: str) -> bool:
        """Validate that applications can still connect using the rotated secret"""
        
        try:
            # Get secret details to determine type
            detail = self.secrets_client.describe_secret(SecretId=secret_arn)
            tags = {tag['Key']: tag['Value'] for tag in detail.get('Tags', [])}
            secret_type = tags.get('Type', 'unknown')
            
            # Get current secret value
            secret_value = self.secrets_client.get_secret_value(
                SecretId=secret_arn,
                VersionStage='AWSCURRENT'
            )
            
            secret_data = json.loads(secret_value['SecretString'])
            
            # Validate based on secret type
            if secret_type == 'database':
                return self._validate_database_connectivity(secret_data)
            elif secret_type == 'api_key':
                return self._validate_api_connectivity(secret_data)
            else:
                logger.warning(f"No validation method for secret type: {secret_type}")
                return True
                
        except Exception as e:
            logger.error(f"Error validating secret connectivity for {secret_arn}: {e}")
            return False
    
    def _validate_database_connectivity(self, secret_data: Dict) -> bool:
        """Validate database connectivity"""
        
        try:
            import psycopg2  # For PostgreSQL
            # import pymysql   # For MySQL
            
            conn = psycopg2.connect(
                host=secret_data['host'],
                port=secret_data['port'],
                database=secret_data['dbname'],
                user=secret_data['username'],
                password=secret_data['password']
            )
            
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
            
            conn.close()
            return result[0] == 1
            
        except Exception as e:
            logger.error(f"Database connectivity validation failed: {e}")
            return False
    
    def _validate_api_connectivity(self, secret_data: Dict) -> bool:
        """Validate API connectivity"""
        
        try:
            import requests
            
            # Simple API health check
            endpoint = secret_data.get('endpoint', '')
            api_key = secret_data.get('api_key', '')
            
            if not endpoint or not api_key:
                logger.warning("Missing endpoint or API key for validation")
                return True
            
            headers = {'Authorization': f'Bearer {api_key}'}
            response = requests.get(f"{endpoint}/health", headers=headers, timeout=10)
            
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"API connectivity validation failed: {e}")
            return False
    
    def generate_rotation_report(self, days_ahead: int = 30) -> Dict:
        """Generate comprehensive rotation report"""
        
        secrets_due = self.get_secrets_due_for_rotation(days_ahead)
        
        report = {
            'generated_at': datetime.now().isoformat(),
            'reporting_period_days': days_ahead,
            'total_secrets_due': len(secrets_due),
            'secrets_by_urgency': {
                'overdue': [],
                'due_today': [],
                'due_this_week': [],
                'due_this_month': []
            },
            'rotation_summary': {
                'total_enabled': 0,
                'by_type': {},
                'by_environment': {}
            }
        }
        
        # Categorize secrets by urgency
        today = datetime.now().date()
        
        for secret in secrets_due:
            days_until = secret['days_until']
            
            if days_until < 0:
                report['secrets_by_urgency']['overdue'].append(secret)
            elif days_until == 0:
                report['secrets_by_urgency']['due_today'].append(secret)
            elif days_until <= 7:
                report['secrets_by_urgency']['due_this_week'].append(secret)
            else:
                report['secrets_by_urgency']['due_this_month'].append(secret)
        
        # Get overall statistics
        paginator = self.secrets_client.get_paginator('list_secrets')
        
        for page in paginator.paginate():
            for secret in page['SecretList']:
                if secret.get('RotationEnabled', False):
                    report['rotation_summary']['total_enabled'] += 1
                    
                    # Get tags for categorization
                    try:
                        detail = self.secrets_client.describe_secret(SecretId=secret['ARN'])
                        tags = {tag['Key']: tag['Value'] for tag in detail.get('Tags', [])}
                        
                        secret_type = tags.get('Type', 'unknown')
                        environment = tags.get('Environment', 'unknown')
                        
                        report['rotation_summary']['by_type'][secret_type] = \
                            report['rotation_summary']['by_type'].get(secret_type, 0) + 1
                        
                        report['rotation_summary']['by_environment'][environment] = \
                            report['rotation_summary']['by_environment'].get(environment, 0) + 1
                            
                    except Exception as e:
                        logger.error(f"Error getting details for {secret['ARN']}: {e}")
        
        return report
    
    def send_rotation_notifications(self, report: Dict, sns_topic_arn: str):
        """Send rotation notifications"""
        
        try:
            # Prepare notification message
            overdue_count = len(report['secrets_by_urgency']['overdue'])
            due_today_count = len(report['secrets_by_urgency']['due_today'])
            due_week_count = len(report['secrets_by_urgency']['due_this_week'])
            
            message = f"""
Secret Rotation Report - {report['generated_at']}

URGENT ATTENTION REQUIRED:
- Overdue rotations: {overdue_count}
- Due today: {due_today_count}
- Due this week: {due_week_count}

Summary:
- Total secrets with rotation enabled: {report['rotation_summary']['total_enabled']}
- Secrets due within {report['reporting_period_days']} days: {report['total_secrets_due']}

Overdue Secrets:
"""
            
            for secret in report['secrets_by_urgency']['overdue']:
                message += f"- {secret['name']} (overdue by {abs(secret['days_until'])} days)\n"
            
            if not report['secrets_by_urgency']['overdue']:
                message += "None\n"
            
            # Send notification
            self.sns_client.publish(
                TopicArn=sns_topic_arn,
                Message=message,
                Subject=f"Secret Rotation Report - {overdue_count + due_today_count} urgent items"
            )
            
            logger.info("Rotation report sent successfully")
            
        except Exception as e:
            logger.error(f"Failed to send rotation notification: {e}")

def main():
    """Main rotation management workflow"""
    
    # Initialize rotation manager
    rotation_manager = SecretRotationManager()
    
    # Generate rotation report
    report = rotation_manager.generate_rotation_report(days_ahead=30)
    
    print(f"Secret Rotation Report - {report['generated_at']}")
    print(f"Total secrets due for rotation: {report['total_secrets_due']}")
    print(f"Overdue: {len(report['secrets_by_urgency']['overdue'])}")
    print(f"Due today: {len(report['secrets_by_urgency']['due_today'])}")
    print(f"Due this week: {len(report['secrets_by_urgency']['due_this_week'])}")
    
    # Send notifications if configured
    sns_topic = 'arn:aws:sns:us-west-2:123456789012:secret-rotation-alerts'
    rotation_manager.send_rotation_notifications(report, sns_topic)
    
    # Rotate overdue secrets
    for secret in report['secrets_by_urgency']['overdue']:
        print(f"Rotating overdue secret: {secret['name']}")
        success = rotation_manager.rotate_secret_safely(secret['arn'], force=True)
        
        if success:
            # Validate connectivity after rotation
            if rotation_manager.validate_secret_connectivity(secret['arn']):
                print(f"✅ Successfully rotated and validated: {secret['name']}")
            else:
                print(f"⚠️  Rotated but validation failed: {secret['name']}")
        else:
            print(f"❌ Failed to rotate: {secret['name']}")

if __name__ == "__main__":
    main()
```

### Application Secret Integration

```bash
#!/bin/bash
# inject-secrets.sh - Inject secrets into application environments

APPLICATION=$1
ENVIRONMENT=$2
OUTPUT_FORMAT=${3:-env}  # env, json, docker

if [ $# -lt 2 ]; then
    echo "Usage: $0 <application> <environment> [output-format]"
    echo "Output formats: env, json, docker"
    exit 1
fi

SECRET_PREFIX="${ENVIRONMENT}/${APPLICATION}"

echo "Retrieving secrets for ${APPLICATION} in ${ENVIRONMENT} environment"

# Get all secrets for the application
SECRETS=$(aws secretsmanager list-secrets \
    --filter Key="name",Values="${SECRET_PREFIX}/" \
    --query 'SecretList[*].Name' \
    --output text)

if [ -z "$SECRETS" ]; then
    echo "No secrets found for ${SECRET_PREFIX}/"
    exit 1
fi

case $OUTPUT_FORMAT in
    "env")
        echo "# Environment variables for ${APPLICATION} (${ENVIRONMENT})"
        echo "# Generated on $(date)"
        echo ""
        
        for secret_name in $SECRETS; do
            # Get secret value
            SECRET_VALUE=$(aws secretsmanager get-secret-value \
                --secret-id "$secret_name" \
                --query 'SecretString' \
                --output text)
            
            # Extract the key name (last part after /)
            KEY_NAME=$(echo "$secret_name" | awk -F'/' '{print $NF}' | tr '[:lower:]' '[:upper:]' | tr '-' '_')
            
            # Check if secret is JSON or plain text
            if echo "$SECRET_VALUE" | jq . >/dev/null 2>&1; then
                # JSON secret - extract each key
                echo "$SECRET_VALUE" | jq -r 'to_entries[] | "\(.key | ascii_upcase | gsub("-"; "_"))=\(.value)"'
            else
                # Plain text secret
                echo "${KEY_NAME}=${SECRET_VALUE}"
            fi
        done
        ;;
        
    "json")
        echo "{"
        FIRST=true
        
        for secret_name in $SECRETS; do
            if [ "$FIRST" = false ]; then
                echo ","
            fi
            FIRST=false
            
            SECRET_VALUE=$(aws secretsmanager get-secret-value \
                --secret-id "$secret_name" \
                --query 'SecretString' \
                --output text)
            
            KEY_NAME=$(echo "$secret_name" | awk -F'/' '{print $NF}')
            
            if echo "$SECRET_VALUE" | jq . >/dev/null 2>&1; then
                echo "  \"$KEY_NAME\": $SECRET_VALUE"
            else
                echo "  \"$KEY_NAME\": \"$SECRET_VALUE\""
            fi
        done
        
        echo ""
        echo "}"
        ;;
        
    "docker")
        echo "# Docker environment file for ${APPLICATION} (${ENVIRONMENT})"
        echo "# Usage: docker run --env-file secrets.env <image>"
        echo ""
        
        for secret_name in $SECRETS; do
            SECRET_VALUE=$(aws secretsmanager get-secret-value \
                --secret-id "$secret_name" \
                --query 'SecretString' \
                --output text)
            
            KEY_NAME=$(echo "$secret_name" | awk -F'/' '{print $NF}' | tr '[:lower:]' '[:upper:]' | tr '-' '_')
            
            if echo "$SECRET_VALUE" | jq . >/dev/null 2>&1; then
                # JSON secret - flatten for Docker env
                echo "$SECRET_VALUE" | jq -r 'to_entries[] | "\(.key | ascii_upcase | gsub("-"; "_"))=\(.value)"'
            else
                echo "${KEY_NAME}=${SECRET_VALUE}"
            fi
        done
        ;;
        
    *)
        echo "Unknown output format: $OUTPUT_FORMAT"
        echo "Supported formats: env, json, docker"
        exit 1
        ;;
esac
```

## Best Practices

### Security Best Practices
- **Encryption:** Use customer-managed KMS keys for sensitive secrets
- **Access control:** Implement least privilege IAM policies with resource-based policies
- **Network security:** Use VPC endpoints for private network access
- **Audit logging:** Enable CloudTrail for all Secrets Manager API calls
- **Secret structure:** Use JSON format for structured secrets with multiple values

### Operational Excellence
- **Naming conventions:** Use consistent hierarchical naming (environment/app/secret-type)
- **Tagging strategy:** Implement comprehensive tagging for organization and automation
- **Rotation schedules:** Align rotation with business requirements and compliance needs
- **Monitoring:** Set up CloudWatch alarms for rotation failures and access patterns
- **Documentation:** Maintain secret inventory and usage documentation

### Cost Optimization
- **Secret consolidation:** Group related secrets to minimize storage costs
- **Retention management:** Delete unused secrets and old versions
- **Cross-region replication:** Use only when necessary for disaster recovery
- **API optimization:** Cache secret values appropriately to reduce API calls
- **Lifecycle management:** Automate secret cleanup for temporary environments

### Integration Best Practices
- **Application design:** Implement secret caching with appropriate TTL
- **Error handling:** Graceful degradation when secrets are unavailable
- **Secret validation:** Verify secret format and connectivity after rotation
- **Environment separation:** Strict isolation between development, staging, and production
- **CI/CD integration:** Automate secret deployment and validation in pipelines