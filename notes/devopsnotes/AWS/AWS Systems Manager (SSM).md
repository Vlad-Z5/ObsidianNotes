# AWS Systems Manager (SSM)

> **Service Type:** Infrastructure Management | **Tier:** CI/CD and Automation | **Global/Regional:** Regional

## Overview

AWS Systems Manager is a unified interface for managing AWS infrastructure and applications at scale. It provides operational insights, automation capabilities, and secure access management for EC2 instances, on-premises servers, and other AWS resources.

## DevOps Use Cases

### Infrastructure Automation
- **Configuration management** with consistent settings across environments
- **Automated patching** for security updates and compliance
- **Software deployment** and application lifecycle management
- **Infrastructure compliance** monitoring and remediation

### Operational Excellence
- **Centralized operations** dashboard for multi-service management
- **Incident response** automation with predefined runbooks
- **Change management** with controlled deployment processes
- **Operational insights** through inventory and compliance reporting

### Security and Compliance
- **Secure access** to instances without SSH keys or bastion hosts
- **Audit trails** for all administrative actions and changes
- **Compliance monitoring** with automated remediation
- **Secret and configuration management** with Parameter Store

### DevOps Pipeline Integration
- **CI/CD automation** with deployment and testing workflows
- **Environment management** for consistent dev/staging/production setups
- **Application configuration** management across deployments
- **Monitoring and alerting** integration with operational workflows

### Hybrid Cloud Management
- **On-premises integration** with SSM Agent on non-AWS servers
- **Unified management** across AWS and on-premises infrastructure
- **Consistent tooling** regardless of infrastructure location
- **Cloud migration** support with gradual transition capabilities

## Core Components

### Parameter Store
- **Secure storage** for configuration data, secrets, and license keys
- **Hierarchical organization** with path-based parameter structure
- **Encryption support** with AWS KMS for sensitive data
- **Version control** with parameter history and change tracking
- **Integration** with CloudFormation, Lambda, and other services

### Session Manager
- **Browser-based access** to EC2 instances without SSH
- **Audit logging** of all session activities
- **IAM-based access control** with fine-grained permissions
- **Port forwarding** for secure tunneling to services
- **No open ports** required - works through SSM Agent

### Run Command
- **Remote execution** of commands across multiple instances
- **Document-based** automation with pre-built and custom documents
- **Target selection** using tags, instance IDs, or resource groups
- **Output collection** and centralized logging
- **Rate controls** to manage execution across large fleets

### Patch Manager
- **Automated patching** with predefined maintenance windows
- **Patch baselines** for different operating systems and applications
- **Compliance reporting** showing patch status across instances
- **Custom patch groups** for different update requirements
- **Integration** with maintenance windows for scheduled updates

### Automation
- **Workflow orchestration** with step-by-step execution
- **Multi-service integration** across AWS services
- **Conditional logic** and error handling in workflows
- **Scheduled execution** with CloudWatch Events integration
- **Approval workflows** for sensitive operations

## Practical CLI Examples

### Parameter Store Operations

```bash
# Store parameters
aws ssm put-parameter \
  --name "/myapp/database/username" \
  --value "dbuser" \
  --type "String" \
  --description "Database username for MyApp"

aws ssm put-parameter \
  --name "/myapp/database/password" \
  --value "supersecret" \
  --type "SecureString" \
  --key-id "alias/parameter-store-key" \
  --description "Database password for MyApp"

# Store with tags
aws ssm put-parameter \
  --name "/myapp/api/key" \
  --value "api-key-value" \
  --type "SecureString" \
  --tags Key=Environment,Value=Production Key=Application,Value=MyApp

# Get parameters
aws ssm get-parameter \
  --name "/myapp/database/username"

aws ssm get-parameter \
  --name "/myapp/database/password" \
  --with-decryption

# Get multiple parameters
aws ssm get-parameters \
  --names "/myapp/database/username" "/myapp/database/password" \
  --with-decryption

# Get parameters by path
aws ssm get-parameters-by-path \
  --path "/myapp" \
  --recursive \
  --with-decryption

# Update parameter
aws ssm put-parameter \
  --name "/myapp/database/password" \
  --value "newsecret" \
  --type "SecureString" \
  --overwrite

# Delete parameter
aws ssm delete-parameter \
  --name "/myapp/old-config"
```

### Session Manager Operations

```bash
# Start interactive session
aws ssm start-session \
  --target i-1234567890abcdef0

# Start session with specific user
aws ssm start-session \
  --target i-1234567890abcdef0 \
  --document-name "SSM-SessionManagerRunShell" \
  --parameters 'shellProfile=["sudo su - ec2-user"]'

# Start port forwarding session
aws ssm start-session \
  --target i-1234567890abcdef0 \
  --document-name "AWS-StartPortForwardingSession" \
  --parameters '{"portNumber":["3306"],"localPortNumber":["9999"]}'

# Terminate session
aws ssm terminate-session \
  --session-id "session-id-here"

# List active sessions
aws ssm describe-sessions \
  --state "Active"
```

### Run Command Operations

```bash
# Run command on specific instances
aws ssm send-command \
  --instance-ids "i-1234567890abcdef0" "i-0987654321fedcba0" \
  --document-name "AWS-RunShellScript" \
  --parameters 'commands=["#!/bin/bash","yum update -y","systemctl restart httpd"]' \
  --comment "Update and restart web servers"

# Run command using tags
aws ssm send-command \
  --targets "Key=tag:Environment,Values=Production" "Key=tag:Role,Values=WebServer" \
  --document-name "AWS-RunShellScript" \
  --parameters 'commands=["ps aux | grep httpd","systemctl status httpd"]' \
  --max-concurrency "5" \
  --max-errors "1"

# Get command execution status
aws ssm list-command-invocations \
  --command-id "command-id-here" \
  --details

# Get command output
aws ssm get-command-invocation \
  --command-id "command-id-here" \
  --instance-id "i-1234567890abcdef0"
```

### Patch Manager Operations

```bash
# Create patch baseline
aws ssm create-patch-baseline \
  --name "MyApp-Baseline" \
  --operating-system "AMAZON_LINUX_2" \
  --approval-rules '{
    "PatchRules": [
      {
        "PatchFilterGroup": {
          "PatchFilters": [
            {
              "Key": "CLASSIFICATION",
              "Values": ["Security", "Critical"]
            }
          ]
        },
        "ApproveAfterDays": 0,
        "ComplianceLevel": "CRITICAL"
      }
    ]
  }' \
  --description "Security and critical patches for MyApp servers"

# Register patch baseline with targets
aws ssm register-patch-baseline-for-patch-group \
  --baseline-id "pb-1234567890abcdef0" \
  --patch-group "WebServers"

# Create maintenance window
aws ssm create-maintenance-window \
  --name "WebServer-Maintenance" \
  --description "Maintenance window for web servers" \
  --duration 4 \
  --cutoff 1 \
  --schedule "cron(0 2 ? * SUN *)" \
  --allow-unassociated-targets

# Register targets with maintenance window
aws ssm register-target-with-maintenance-window \
  --window-id "mw-1234567890abcdef0" \
  --target-type "Instance" \
  --targets "Key=tag:PatchGroup,Values=WebServers" \
  --resource-type "INSTANCE"

# Register patch task
aws ssm register-task-with-maintenance-window \
  --window-id "mw-1234567890abcdef0" \
  --target-id "target-id-here" \
  --task-arn "AWS-RunPatchBaseline" \
  --task-type "RUN_COMMAND" \
  --service-role-arn "arn:aws:iam::123456789012:role/MW-Role" \
  --task-parameters '{
    "Operation": {
      "Values": ["Install"]
    }
  }'
```

### Automation Workflows

```bash
# Create automation document
cat > restart-services.json << 'EOF'
{
  "schemaVersion": "0.3",
  "description": "Restart application services",
  "parameters": {
    "InstanceIds": {
      "type": "StringList",
      "description": "Instance IDs to restart services on"
    },
    "ServiceName": {
      "type": "String",
      "description": "Name of service to restart",
      "default": "httpd"
    }
  },
  "mainSteps": [
    {
      "name": "StopService",
      "action": "aws:runCommand",
      "inputs": {
        "DocumentName": "AWS-RunShellScript",
        "InstanceIds": "{{ InstanceIds }}",
        "Parameters": {
          "commands": [
            "systemctl stop {{ ServiceName }}"
          ]
        }
      }
    },
    {
      "name": "WaitForStop",
      "action": "aws:sleep",
      "inputs": {
        "Duration": "PT10S"
      }
    },
    {
      "name": "StartService",
      "action": "aws:runCommand",
      "inputs": {
        "DocumentName": "AWS-RunShellScript",
        "InstanceIds": "{{ InstanceIds }}",
        "Parameters": {
          "commands": [
            "systemctl start {{ ServiceName }}",
            "systemctl enable {{ ServiceName }}"
          ]
        }
      }
    }
  ]
}
EOF

aws ssm create-document \
  --content file://restart-services.json \
  --name "RestartApplicationServices" \
  --document-type "Automation" \
  --document-format "JSON"

# Execute automation
aws ssm start-automation-execution \
  --document-name "RestartApplicationServices" \
  --parameters 'InstanceIds=["i-1234567890abcdef0","i-0987654321fedcba0"],ServiceName=["nginx"]'

# Monitor automation execution
aws ssm describe-automation-executions \
  --filters "Key=DocumentName,Values=RestartApplicationServices"

# Get execution details
aws ssm get-automation-execution \
  --automation-execution-id "execution-id-here"
```

## DevOps Automation Scripts

### Configuration Deployment Script

```bash
#!/bin/bash
# deploy-config.sh - Deploy configuration using Parameter Store

APP_NAME=$1
ENVIRONMENT=$2
CONFIG_FILE=$3

if [ $# -ne 3 ]; then
    echo "Usage: $0 <app-name> <environment> <config-file>"
    exit 1
fi

echo "Deploying configuration for ${APP_NAME} in ${ENVIRONMENT}"

# Validate config file exists
if [ ! -f "$CONFIG_FILE" ]; then
    echo "Configuration file not found: $CONFIG_FILE"
    exit 1
fi

# Parse JSON config and create parameters
jq -r 'to_entries[] | "\(.key)=\(.value)"' "$CONFIG_FILE" | while IFS='=' read -r key value; do
    PARAM_NAME="/${APP_NAME}/${ENVIRONMENT}/${key}"
    
    echo "Setting parameter: $PARAM_NAME"
    
    # Determine if value should be encrypted (passwords, keys, etc.)
    if [[ "$key" == *"password"* ]] || [[ "$key" == *"secret"* ]] || [[ "$key" == *"key"* ]]; then
        PARAM_TYPE="SecureString"
        echo "  (encrypted)"
    else
        PARAM_TYPE="String"
    fi
    
    aws ssm put-parameter \
        --name "$PARAM_NAME" \
        --value "$value" \
        --type "$PARAM_TYPE" \
        --overwrite \
        --tags "Key=Application,Value=${APP_NAME}" "Key=Environment,Value=${ENVIRONMENT}" "Key=ManagedBy,Value=deployment-script"
done

echo "Configuration deployment completed"

# Trigger application restart if instances are tagged
INSTANCES=$(aws ec2 describe-instances \
    --filters "Name=tag:Application,Values=${APP_NAME}" "Name=tag:Environment,Values=${ENVIRONMENT}" "Name=instance-state-name,Values=running" \
    --query 'Reservations[*].Instances[*].InstanceId' \
    --output text)

if [ ! -z "$INSTANCES" ]; then
    echo "Restarting application on instances: $INSTANCES"
    
    aws ssm send-command \
        --instance-ids $INSTANCES \
        --document-name "AWS-RunShellScript" \
        --parameters 'commands=["#!/bin/bash","sudo systemctl restart '${APP_NAME}'","sudo systemctl status '${APP_NAME}'"]' \
        --comment "Restart ${APP_NAME} after configuration update"
fi
```

### Patch Management Automation

```python
# patch-automation.py - Automated patch management workflow
import boto3
import json
from datetime import datetime, timedelta

def create_patch_deployment(environment, patch_group, maintenance_window_id):
    """Create a comprehensive patch deployment workflow"""
    
    ssm = boto3.client('ssm')
    
    # Get instances in patch group
    instances = get_instances_by_patch_group(patch_group)
    
    if not instances:
        print(f"No instances found in patch group: {patch_group}")
        return False
    
    print(f"Found {len(instances)} instances in patch group {patch_group}")
    
    # Pre-patch health check
    print("Running pre-patch health checks...")
    health_check_results = run_health_checks(instances)
    
    unhealthy_instances = [inst for inst, healthy in health_check_results.items() if not healthy]
    
    if unhealthy_instances:
        print(f"Warning: Unhealthy instances found: {unhealthy_instances}")
        if environment == 'production':
            print("Aborting patch deployment due to unhealthy production instances")
            return False
    
    # Create snapshot of instances
    print("Creating EBS snapshots before patching...")
    snapshot_ids = create_instance_snapshots(instances)
    
    # Start patch deployment
    print("Starting patch deployment...")
    
    automation_execution = ssm.start_automation_execution(
        DocumentName='AWS-PatchInstanceWithRollback',
        Parameters={
            'InstanceId': instances,
            'SnapshotId': snapshot_ids,
            'RebootOption': ['RebootIfNeeded'],
            'Operation': ['Install']
        }
    )
    
    execution_id = automation_execution['AutomationExecutionId']
    print(f"Patch automation started: {execution_id}")
    
    # Monitor execution
    return monitor_patch_execution(execution_id, instances)

def get_instances_by_patch_group(patch_group):
    """Get instances belonging to a specific patch group"""
    ec2 = boto3.client('ec2')
    
    response = ec2.describe_instances(
        Filters=[
            {
                'Name': 'tag:PatchGroup',
                'Values': [patch_group]
            },
            {
                'Name': 'instance-state-name',
                'Values': ['running']
            }
        ]
    )
    
    instances = []
    for reservation in response['Reservations']:
        for instance in reservation['Instances']:
            instances.append(instance['InstanceId'])
    
    return instances

def run_health_checks(instances):
    """Run health checks on instances before patching"""
    ssm = boto3.client('ssm')
    
    # Send health check command
    response = ssm.send_command(
        InstanceIds=instances,
        DocumentName='AWS-RunShellScript',
        Parameters={
            'commands': [
                '#!/bin/bash',
                'echo "=== Disk Space ==="',
                'df -h',
                'echo "=== Memory Usage ==="',
                'free -m',
                'echo "=== Load Average ==="',
                'uptime',
                'echo "=== Service Status ==="',
                'systemctl is-active httpd nginx || true'
            ]
        },
        Comment='Pre-patch health check'
    )
    
    command_id = response['Command']['CommandId']
    
    # Wait for command completion and analyze results
    import time
    time.sleep(30)  # Wait for command to complete
    
    health_results = {}
    
    for instance_id in instances:
        try:
            result = ssm.get_command_invocation(
                CommandId=command_id,
                InstanceId=instance_id
            )
            
            output = result['StandardOutputContent']
            
            # Simple health check logic
            healthy = True
            if 'No space left on device' in output:
                healthy = False
            if 'inactive' in output and 'httpd' in output:
                healthy = False
            
            health_results[instance_id] = healthy
            
        except Exception as e:
            print(f"Health check failed for {instance_id}: {e}")
            health_results[instance_id] = False
    
    return health_results

def create_instance_snapshots(instances):
    """Create EBS snapshots for instances"""
    ec2 = boto3.client('ec2')
    
    snapshot_ids = []
    
    for instance_id in instances:
        # Get instance details
        response = ec2.describe_instances(InstanceIds=[instance_id])
        instance = response['Reservations'][0]['Instances'][0]
        
        # Create snapshots for all EBS volumes
        for device in instance.get('BlockDeviceMappings', []):
            if 'Ebs' in device:
                volume_id = device['Ebs']['VolumeId']
                
                snapshot = ec2.create_snapshot(
                    VolumeId=volume_id,
                    Description=f"Pre-patch snapshot for {instance_id} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                )
                
                snapshot_ids.append(snapshot['SnapshotId'])
                
                # Tag snapshot
                ec2.create_tags(
                    Resources=[snapshot['SnapshotId']],
                    Tags=[
                        {'Key': 'Name', 'Value': f"{instance_id}-pre-patch-{datetime.now().strftime('%Y%m%d')}"},
                        {'Key': 'Purpose', 'Value': 'pre-patch-backup'},
                        {'Key': 'InstanceId', 'Value': instance_id},
                        {'Key': 'CreatedBy', 'Value': 'patch-automation'}
                    ]
                )
    
    return snapshot_ids

def monitor_patch_execution(execution_id, instances):
    """Monitor patch execution and handle results"""
    ssm = boto3.client('ssm')
    sns = boto3.client('sns')
    
    while True:
        response = ssm.get_automation_execution(
            AutomationExecutionId=execution_id
        )
        
        status = response['AutomationExecution']['AutomationExecutionStatus']
        
        if status in ['Success', 'Failed', 'TimedOut', 'Cancelled']:
            break
        
        print(f"Patch execution status: {status}")
        time.sleep(60)  # Check every minute
    
    # Send notification
    if status == 'Success':
        message = f"Patch deployment completed successfully for {len(instances)} instances"
        print(message)
        
        # Run post-patch validation
        run_post_patch_validation(instances)
        
    else:
        message = f"Patch deployment failed with status: {status}"
        print(message)
        
        # Send alert
        sns.publish(
            TopicArn='arn:aws:sns:us-west-2:123456789012:patch-alerts',
            Message=message,
            Subject='Patch Deployment Alert'
        )
    
    return status == 'Success'

def run_post_patch_validation(instances):
    """Run validation checks after patching"""
    ssm = boto3.client('ssm')
    
    print("Running post-patch validation...")
    
    response = ssm.send_command(
        InstanceIds=instances,
        DocumentName='AWS-RunShellScript',
        Parameters={
            'commands': [
                '#!/bin/bash',
                'echo "=== System Status ==="',
                'uptime',
                'echo "=== Service Status ==="',
                'systemctl status httpd nginx || true',
                'echo "=== Recent Patches ==="',
                'rpm -qa --last | head -10 || dpkg -l | grep $(date +%Y-%m-%d) || true'
            ]
        },
        Comment='Post-patch validation'
    )
    
    print(f"Post-patch validation started: {response['Command']['CommandId']}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 4:
        print("Usage: python patch-automation.py <environment> <patch-group> <maintenance-window-id>")
        sys.exit(1)
    
    environment = sys.argv[1]
    patch_group = sys.argv[2]
    maintenance_window_id = sys.argv[3]
    
    success = create_patch_deployment(environment, patch_group, maintenance_window_id)
    
    if success:
        print("Patch deployment completed successfully")
    else:
        print("Patch deployment failed")
        sys.exit(1)
```

### Application Deployment Automation

```bash
#!/bin/bash
# app-deployment.sh - Complete application deployment using SSM

APP_NAME=$1
VERSION=$2
ENVIRONMENT=$3
ROLLBACK=${4:-false}

if [ $# -lt 3 ]; then
    echo "Usage: $0 <app-name> <version> <environment> [rollback=false]"
    exit 1
fi

echo "Deploying ${APP_NAME} version ${VERSION} to ${ENVIRONMENT}"

# Get target instances
INSTANCES=$(aws ec2 describe-instances \
    --filters "Name=tag:Application,Values=${APP_NAME}" \
              "Name=tag:Environment,Values=${ENVIRONMENT}" \
              "Name=instance-state-name,Values=running" \
    --query 'Reservations[*].Instances[*].InstanceId' \
    --output text)

if [ -z "$INSTANCES" ]; then
    echo "No instances found for ${APP_NAME} in ${ENVIRONMENT}"
    exit 1
fi

echo "Target instances: $INSTANCES"

# Create deployment automation document if it doesn't exist
DOC_NAME="${APP_NAME}-Deployment"

if ! aws ssm describe-document --name "$DOC_NAME" >/dev/null 2>&1; then
    echo "Creating deployment automation document..."
    
    cat > deployment-doc.json << EOF
{
  "schemaVersion": "0.3",
  "description": "Deploy ${APP_NAME} application",
  "parameters": {
    "InstanceIds": {
      "type": "StringList",
      "description": "Target instance IDs"
    },
    "Version": {
      "type": "String",
      "description": "Application version to deploy"
    },
    "RollbackVersion": {
      "type": "String",
      "description": "Previous version for rollback",
      "default": ""
    }
  },
  "mainSteps": [
    {
      "name": "StopApplication",
      "action": "aws:runCommand",
      "inputs": {
        "DocumentName": "AWS-RunShellScript",
        "InstanceIds": "{{ InstanceIds }}",
        "Parameters": {
          "commands": [
            "sudo systemctl stop ${APP_NAME}",
            "sleep 5"
          ]
        }
      }
    },
    {
      "name": "BackupCurrentVersion",
      "action": "aws:runCommand",
      "inputs": {
        "DocumentName": "AWS-RunShellScript",
        "InstanceIds": "{{ InstanceIds }}",
        "Parameters": {
          "commands": [
            "sudo cp -r /opt/${APP_NAME} /opt/${APP_NAME}.backup.\$(date +%Y%m%d-%H%M%S)",
            "echo 'Backup created'"
          ]
        }
      }
    },
    {
      "name": "DownloadNewVersion",
      "action": "aws:runCommand",
      "inputs": {
        "DocumentName": "AWS-RunShellScript",
        "InstanceIds": "{{ InstanceIds }}",
        "Parameters": {
          "commands": [
            "cd /tmp",
            "aws s3 cp s3://my-deployments/${APP_NAME}/{{ Version }}/${APP_NAME}-{{ Version }}.tar.gz .",
            "sudo tar -xzf ${APP_NAME}-{{ Version }}.tar.gz -C /opt/",
            "sudo chown -R ${APP_NAME}:${APP_NAME} /opt/${APP_NAME}"
          ]
        }
      }
    },
    {
      "name": "UpdateConfiguration",
      "action": "aws:runCommand",
      "inputs": {
        "DocumentName": "AWS-RunShellScript",
        "InstanceIds": "{{ InstanceIds }}",
        "Parameters": {
          "commands": [
            "# Get configuration from Parameter Store",
            "aws ssm get-parameters-by-path --path '/${APP_NAME}/${ENVIRONMENT}' --recursive --with-decryption --query 'Parameters[*].[Name,Value]' --output text | while read name value; do",
            "  config_key=\$(echo \$name | sed 's|.*${APP_NAME}/${ENVIRONMENT}/||')",
            "  echo \"\$config_key=\$value\" >> /opt/${APP_NAME}/config/app.env",
            "done"
          ]
        }
      }
    },
    {
      "name": "StartApplication",
      "action": "aws:runCommand",
      "inputs": {
        "DocumentName": "AWS-RunShellScript",
        "InstanceIds": "{{ InstanceIds }}",
        "Parameters": {
          "commands": [
            "sudo systemctl start ${APP_NAME}",
            "sleep 10",
            "sudo systemctl status ${APP_NAME}"
          ]
        }
      }
    },
    {
      "name": "HealthCheck",
      "action": "aws:runCommand",
      "inputs": {
        "DocumentName": "AWS-RunShellScript",
        "InstanceIds": "{{ InstanceIds }}",
        "Parameters": {
          "commands": [
            "# Wait for application to be ready",
            "for i in {1..30}; do",
            "  if curl -f http://localhost:8080/health; then",
            "    echo 'Health check passed'",
            "    exit 0",
            "  fi",
            "  sleep 5",
            "done",
            "echo 'Health check failed'",
            "exit 1"
          ]
        }
      }
    }
  ]
}
EOF

    aws ssm create-document \
        --content file://deployment-doc.json \
        --name "$DOC_NAME" \
        --document-type "Automation" \
        --document-format "JSON"
    
    rm deployment-doc.json
fi

# Execute deployment
if [ "$ROLLBACK" = "true" ]; then
    echo "Performing rollback deployment..."
    PREVIOUS_VERSION=$(aws ssm get-parameter --name "/${APP_NAME}/${ENVIRONMENT}/previous-version" --query 'Parameter.Value' --output text 2>/dev/null || echo "")
    
    if [ -z "$PREVIOUS_VERSION" ]; then
        echo "No previous version found for rollback"
        exit 1
    fi
    
    DEPLOY_VERSION="$PREVIOUS_VERSION"
else
    echo "Performing forward deployment..."
    DEPLOY_VERSION="$VERSION"
    
    # Store current version as previous
    CURRENT_VERSION=$(aws ssm get-parameter --name "/${APP_NAME}/${ENVIRONMENT}/current-version" --query 'Parameter.Value' --output text 2>/dev/null || echo "")
    if [ ! -z "$CURRENT_VERSION" ]; then
        aws ssm put-parameter \
            --name "/${APP_NAME}/${ENVIRONMENT}/previous-version" \
            --value "$CURRENT_VERSION" \
            --type "String" \
            --overwrite
    fi
fi

# Start automation execution
EXECUTION_ID=$(aws ssm start-automation-execution \
    --document-name "$DOC_NAME" \
    --parameters "InstanceIds=[$(echo $INSTANCES | tr ' ' ',')],Version=${DEPLOY_VERSION}" \
    --query 'AutomationExecutionId' \
    --output text)

echo "Deployment started: $EXECUTION_ID"

# Monitor execution
while true; do
    STATUS=$(aws ssm get-automation-execution \
        --automation-execution-id "$EXECUTION_ID" \
        --query 'AutomationExecution.AutomationExecutionStatus' \
        --output text)
    
    echo "Deployment status: $STATUS"
    
    if [ "$STATUS" = "Success" ]; then
        echo "Deployment completed successfully!"
        
        # Update current version parameter
        aws ssm put-parameter \
            --name "/${APP_NAME}/${ENVIRONMENT}/current-version" \
            --value "$DEPLOY_VERSION" \
            --type "String" \
            --overwrite
        
        break
    elif [ "$STATUS" = "Failed" ] || [ "$STATUS" = "TimedOut" ] || [ "$STATUS" = "Cancelled" ]; then
        echo "Deployment failed with status: $STATUS"
        
        # Get failure details
        aws ssm get-automation-execution \
            --automation-execution-id "$EXECUTION_ID" \
            --query 'AutomationExecution.FailureMessage' \
            --output text
        
        exit 1
    fi
    
    sleep 30
done

echo "Deployment of ${APP_NAME} ${DEPLOY_VERSION} to ${ENVIRONMENT} completed successfully"
```

## Enterprise Automation Framework

### Advanced Infrastructure Orchestration Engine

```python
# enterprise-ssm-orchestrator.py - Advanced SSM automation framework
import boto3
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import concurrent.futures
import hashlib

class OrchestrationStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"
    ROLLBACK = "rollback"

@dataclass
class OrchestrationStep:
    name: str
    action: str
    parameters: Dict[str, Any]
    dependencies: List[str] = None
    timeout: int = 3600
    retry_count: int = 0
    rollback_action: Optional[str] = None
    validation: Optional[Dict[str, Any]] = None

class EnterpriseSSMOrchestrator:
    """
    Enterprise-grade SSM automation orchestrator with advanced workflow management,
    dependency resolution, error handling, and rollback capabilities.
    """
    
    def __init__(self, region_name: str = 'us-west-2'):
        self.ssm = boto3.client('ssm', region_name=region_name)
        self.ec2 = boto3.client('ec2', region_name=region_name)
        self.sns = boto3.client('sns', region_name=region_name)
        self.cloudwatch = boto3.client('cloudwatch', region_name=region_name)
        
        # Configure logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Execution tracking
        self.executions: Dict[str, Dict] = {}
        self.metrics_namespace = 'Enterprise/SSM/Orchestration'
    
    def create_workflow(self, workflow_name: str, steps: List[OrchestrationStep], 
                       metadata: Dict[str, Any] = None) -> str:
        """Create and register a new automation workflow"""
        
        workflow_id = f"{workflow_name}-{int(time.time())}"
        
        # Validate workflow
        self._validate_workflow(steps)
        
        # Create SSM automation document
        document_content = self._generate_automation_document(workflow_name, steps)
        
        try:
            response = self.ssm.create_document(
                Content=json.dumps(document_content),
                Name=workflow_id,
                DocumentType='Automation',
                DocumentFormat='JSON',
                Tags=[
                    {'Key': 'WorkflowName', 'Value': workflow_name},
                    {'Key': 'CreatedBy', 'Value': 'EnterpriseOrchestrator'},
                    {'Key': 'CreatedDate', 'Value': datetime.now().isoformat()}
                ]
            )
            
            self.logger.info(f"Created workflow document: {workflow_id}")
            return workflow_id
            
        except Exception as e:
            self.logger.error(f"Failed to create workflow {workflow_id}: {e}")
            raise
    
    def execute_workflow(self, workflow_id: str, parameters: Dict[str, Any],
                        target_selector: Dict[str, Any]) -> str:
        """Execute a workflow with advanced monitoring and error handling"""
        
        execution_id = f"{workflow_id}-exec-{int(time.time())}"
        
        # Initialize execution tracking
        self.executions[execution_id] = {
            'workflow_id': workflow_id,
            'status': OrchestrationStatus.PENDING,
            'start_time': datetime.now(),
            'parameters': parameters,
            'target_selector': target_selector,
            'steps': {},
            'metrics': {}
        }
        
        try:
            # Pre-execution validation
            target_instances = self._resolve_targets(target_selector)
            
            if not target_instances:
                raise ValueError("No target instances found")
            
            # Start automation execution
            response = self.ssm.start_automation_execution(
                DocumentName=workflow_id,
                Parameters=parameters
            )
            
            automation_execution_id = response['AutomationExecutionId']
            self.executions[execution_id]['automation_execution_id'] = automation_execution_id
            self.executions[execution_id]['status'] = OrchestrationStatus.RUNNING
            
            # Start monitoring in background
            self._start_execution_monitoring(execution_id)
            
            self.logger.info(f"Started workflow execution: {execution_id}")
            return execution_id
            
        except Exception as e:
            self.executions[execution_id]['status'] = OrchestrationStatus.FAILED
            self.executions[execution_id]['error'] = str(e)
            self.logger.error(f"Failed to start execution {execution_id}: {e}")
            raise
    
    def get_execution_status(self, execution_id: str) -> Dict[str, Any]:
        """Get comprehensive execution status and metrics"""
        
        if execution_id not in self.executions:
            raise ValueError(f"Execution {execution_id} not found")
        
        execution = self.executions[execution_id]
        
        # Get detailed status from SSM
        if 'automation_execution_id' in execution:
            try:
                response = self.ssm.get_automation_execution(
                    AutomationExecutionId=execution['automation_execution_id']
                )
                
                automation_execution = response['AutomationExecution']
                execution['detailed_status'] = automation_execution
                
                # Update status
                ssm_status = automation_execution['AutomationExecutionStatus']
                if ssm_status == 'Success':
                    execution['status'] = OrchestrationStatus.SUCCESS
                elif ssm_status in ['Failed', 'TimedOut', 'Cancelled']:
                    execution['status'] = OrchestrationStatus.FAILED
                    
            except Exception as e:
                self.logger.error(f"Failed to get execution details for {execution_id}: {e}")
        
        return execution
    
    def cancel_execution(self, execution_id: str, reason: str = "User cancelled") -> bool:
        """Cancel a running execution with proper cleanup"""
        
        if execution_id not in self.executions:
            raise ValueError(f"Execution {execution_id} not found")
        
        execution = self.executions[execution_id]
        
        try:
            if 'automation_execution_id' in execution:
                self.ssm.stop_automation_execution(
                    AutomationExecutionId=execution['automation_execution_id'],
                    Type='Cancel'
                )
            
            execution['status'] = OrchestrationStatus.CANCELLED
            execution['cancellation_reason'] = reason
            execution['end_time'] = datetime.now()
            
            self.logger.info(f"Cancelled execution {execution_id}: {reason}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to cancel execution {execution_id}: {e}")
            return False
    
    def _validate_workflow(self, steps: List[OrchestrationStep]) -> None:
        """Validate workflow structure and dependencies"""
        
        step_names = {step.name for step in steps}
        
        for step in steps:
            # Validate dependencies exist
            if step.dependencies:
                for dep in step.dependencies:
                    if dep not in step_names:
                        raise ValueError(f"Step {step.name} depends on non-existent step: {dep}")
            
            # Validate action types
            valid_actions = ['aws:runCommand', 'aws:sleep', 'aws:executeScript', 
                           'aws:createSnapshot', 'aws:waitForAwsResourceProperty']
            if step.action not in valid_actions:
                raise ValueError(f"Invalid action type: {step.action}")
    
    def _generate_automation_document(self, workflow_name: str, 
                                     steps: List[OrchestrationStep]) -> Dict[str, Any]:
        """Generate SSM automation document from workflow steps"""
        
        document = {
            "schemaVersion": "0.3",
            "description": f"Enterprise workflow: {workflow_name}",
            "parameters": {
                "InstanceIds": {
                    "type": "StringList",
                    "description": "Target instance IDs"
                },
                "ExecutionMode": {
                    "type": "String",
                    "description": "Execution mode (parallel/sequential)",
                    "default": "sequential"
                }
            },
            "mainSteps": []
        }
        
        # Convert steps to SSM format
        for step in steps:
            ssm_step = {
                "name": step.name,
                "action": step.action,
                "timeoutSeconds": step.timeout,
                "onFailure": "Abort"
            }
            
            # Add inputs based on action type
            if step.action == "aws:runCommand":
                ssm_step["inputs"] = {
                    "DocumentName": "AWS-RunShellScript",
                    "InstanceIds": "{{ InstanceIds }}",
                    "Parameters": step.parameters
                }
            elif step.action == "aws:sleep":
                ssm_step["inputs"] = {
                    "Duration": step.parameters.get('duration', 'PT30S')
                }
            
            document["mainSteps"].append(ssm_step)
        
        return document
    
    def _resolve_targets(self, target_selector: Dict[str, Any]) -> List[str]:
        """Resolve target instances based on selector criteria"""
        
        filters = []
        
        # Build EC2 filters from selector
        if 'tags' in target_selector:
            for key, value in target_selector['tags'].items():
                filters.append({
                    'Name': f'tag:{key}',
                    'Values': [value] if isinstance(value, str) else value
                })
        
        if 'instance_states' in target_selector:
            filters.append({
                'Name': 'instance-state-name',
                'Values': target_selector['instance_states']
            })
        
        # Query instances
        response = self.ec2.describe_instances(Filters=filters)
        
        instances = []
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                instances.append(instance['InstanceId'])
        
        return instances
    
    def _start_execution_monitoring(self, execution_id: str) -> None:
        """Start background monitoring for execution"""
        
        def monitor():
            while True:
                try:
                    execution = self.executions[execution_id]
                    
                    if execution['status'] in [OrchestrationStatus.SUCCESS, 
                                             OrchestrationStatus.FAILED,
                                             OrchestrationStatus.CANCELLED]:
                        break
                    
                    # Update execution status
                    self.get_execution_status(execution_id)
                    
                    # Send metrics to CloudWatch
                    self._send_execution_metrics(execution_id)
                    
                    time.sleep(30)  # Check every 30 seconds
                    
                except Exception as e:
                    self.logger.error(f"Monitoring error for {execution_id}: {e}")
                    break
        
        # Start monitoring thread
        import threading
        monitor_thread = threading.Thread(target=monitor)
        monitor_thread.daemon = True
        monitor_thread.start()
    
    def _send_execution_metrics(self, execution_id: str) -> None:
        """Send execution metrics to CloudWatch"""
        
        execution = self.executions[execution_id]
        
        try:
            # Calculate duration
            duration = (datetime.now() - execution['start_time']).total_seconds()
            
            # Send metrics
            self.cloudwatch.put_metric_data(
                Namespace=self.metrics_namespace,
                MetricData=[
                    {
                        'MetricName': 'ExecutionDuration',
                        'Value': duration,
                        'Unit': 'Seconds',
                        'Dimensions': [
                            {'Name': 'WorkflowId', 'Value': execution['workflow_id']},
                            {'Name': 'ExecutionId', 'Value': execution_id}
                        ]
                    },
                    {
                        'MetricName': 'ExecutionStatus',
                        'Value': 1 if execution['status'] == OrchestrationStatus.RUNNING else 0,
                        'Unit': 'Count',
                        'Dimensions': [
                            {'Name': 'WorkflowId', 'Value': execution['workflow_id']},
                            {'Name': 'Status', 'Value': execution['status'].value}
                        ]
                    }
                ]
            )
            
        except Exception as e:
            self.logger.error(f"Failed to send metrics for {execution_id}: {e}")

class SSMInfrastructureManager:
    """
    Advanced infrastructure management using SSM with GitOps integration,
    compliance monitoring, and automated remediation capabilities.
    """
    
    def __init__(self, region_name: str = 'us-west-2'):
        self.ssm = boto3.client('ssm', region_name=region_name)
        self.ec2 = boto3.client('ec2', region_name=region_name)
        self.config = boto3.client('config', region_name=region_name)
        self.s3 = boto3.client('s3', region_name=region_name)
        
        self.logger = logging.getLogger(__name__)
        
        # Configuration management
        self.config_bucket = None
        self.compliance_rules = {}
    
    def setup_gitops_integration(self, git_repo_url: str, branch: str = 'main',
                                 config_bucket: str = None) -> None:
        """Setup GitOps integration for infrastructure configuration"""
        
        self.config_bucket = config_bucket or f"ssm-gitops-{int(time.time())}"
        
        # Create S3 bucket for config storage
        try:
            self.s3.create_bucket(
                Bucket=self.config_bucket,
                CreateBucketConfiguration={'LocationConstraint': 'us-west-2'}
            )
            
            # Configure bucket versioning
            self.s3.put_bucket_versioning(
                Bucket=self.config_bucket,
                VersioningConfiguration={'Status': 'Enabled'}
            )
            
        except Exception as e:
            self.logger.error(f"Failed to setup GitOps bucket: {e}")
            raise
        
        # Create CodePipeline for GitOps workflow
        pipeline_config = {
            "pipeline": {
                "name": f"ssm-gitops-{int(time.time())}",
                "roleArn": f"arn:aws:iam::{boto3.client('sts').get_caller_identity()['Account']}:role/CodePipelineRole",
                "artifactStore": {
                    "type": "S3",
                    "location": self.config_bucket
                },
                "stages": [
                    {
                        "name": "Source",
                        "actions": [
                            {
                                "name": "SourceAction",
                                "actionTypeId": {
                                    "category": "Source",
                                    "owner": "ThirdParty",
                                    "provider": "GitHub",
                                    "version": "1"
                                },
                                "configuration": {
                                    "Owner": git_repo_url.split('/')[-2],
                                    "Repo": git_repo_url.split('/')[-1].replace('.git', ''),
                                    "Branch": branch,
                                    "OAuthToken": "{{resolve:secretsmanager:github-token}}"
                                },
                                "outputArtifacts": [{"name": "SourceOutput"}]
                            }
                        ]
                    },
                    {
                        "name": "Deploy",
                        "actions": [
                            {
                                "name": "DeployAction",
                                "actionTypeId": {
                                    "category": "Invoke",
                                    "owner": "AWS",
                                    "provider": "Lambda",
                                    "version": "1"
                                },
                                "configuration": {
                                    "FunctionName": "SSMConfigDeployFunction"
                                },
                                "inputArtifacts": [{"name": "SourceOutput"}]
                            }
                        ]
                    }
                ]
            }
        }
        
        self.logger.info(f"GitOps integration configured with bucket: {self.config_bucket}")
    
    def deploy_configuration_template(self, template_name: str, 
                                    configuration: Dict[str, Any],
                                    target_selector: Dict[str, Any]) -> str:
        """Deploy configuration template to target instances"""
        
        deployment_id = f"config-deploy-{int(time.time())}"
        
        # Resolve target instances
        target_instances = self._resolve_targets(target_selector)
        
        # Create configuration package
        config_content = self._generate_configuration_script(configuration)
        
        # Deploy using SSM
        response = self.ssm.send_command(
            InstanceIds=target_instances,
            DocumentName='AWS-RunShellScript',
            Parameters={
                'commands': [config_content]
            },
            Comment=f"Deploy configuration template: {template_name}",
            MaxConcurrency='50%',
            MaxErrors='10%'
        )
        
        command_id = response['Command']['CommandId']
        
        # Track deployment
        self._track_configuration_deployment(deployment_id, command_id, target_instances)
        
        self.logger.info(f"Configuration deployment started: {deployment_id}")
        return deployment_id
    
    def setup_compliance_monitoring(self, compliance_rules: Dict[str, Any]) -> None:
        """Setup automated compliance monitoring and remediation"""
        
        self.compliance_rules = compliance_rules
        
        for rule_name, rule_config in compliance_rules.items():
            # Create Config rule
            config_rule = {
                'ConfigRuleName': f"SSM-{rule_name}",
                'Description': rule_config.get('description', f'Compliance rule: {rule_name}'),
                'Source': {
                    'Owner': 'AWS',
                    'SourceIdentifier': rule_config['config_rule_id']
                },
                'InputParameters': json.dumps(rule_config.get('parameters', {}))
            }
            
            try:
                self.config.put_config_rule(ConfigRule=config_rule)
                
                # Setup remediation if specified
                if 'remediation' in rule_config:
                    remediation_config = {
                        'ConfigRuleName': config_rule['ConfigRuleName'],
                        'TargetType': 'SSM_DOCUMENT',
                        'TargetId': rule_config['remediation']['document'],
                        'TargetVersion': '1',
                        'Parameters': rule_config['remediation'].get('parameters', {}),
                        'MaximumExecutionTime': rule_config['remediation'].get('timeout', 300),
                        'Automatic': rule_config['remediation'].get('automatic', False)
                    }
                    
                    self.config.put_remediation_configuration(
                        RemediationConfigurations=[remediation_config]
                    )
                
                self.logger.info(f"Compliance rule configured: {rule_name}")
                
            except Exception as e:
                self.logger.error(f"Failed to setup compliance rule {rule_name}: {e}")
    
    def perform_infrastructure_audit(self, scope: Dict[str, Any]) -> Dict[str, Any]:
        """Perform comprehensive infrastructure audit using SSM"""
        
        audit_id = f"audit-{int(time.time())}"
        audit_results = {
            'audit_id': audit_id,
            'timestamp': datetime.now().isoformat(),
            'scope': scope,
            'findings': {},
            'recommendations': []
        }
        
        # Resolve target instances
        target_instances = self._resolve_targets(scope.get('targets', {}))
        
        if not target_instances:
            audit_results['error'] = "No target instances found"
            return audit_results
        
        # Define audit checks
        audit_checks = [
            {
                'name': 'security_configuration',
                'commands': [
                    '#!/bin/bash',
                    'echo "=== Security Configuration Audit ==="',
                    '# Check SSH configuration',
                    'grep -E "^(PasswordAuthentication|PermitRootLogin|Port)" /etc/ssh/sshd_config || true',
                    '# Check firewall status',
                    'systemctl is-active iptables firewalld ufw || true',
                    '# Check running services',
                    'systemctl list-units --type=service --state=running | head -20',
                    '# Check listening ports',
                    'netstat -tlnp || ss -tlnp',
                    '# Check sudo configuration',
                    'cat /etc/sudoers | grep -v "^#" | grep -v "^$" || true'
                ]
            },
            {
                'name': 'system_health',
                'commands': [
                    '#!/bin/bash',
                    'echo "=== System Health Audit ==="',
                    '# Check disk usage',
                    'df -h',
                    '# Check memory usage',
                    'free -m',
                    '# Check system load',
                    'uptime',
                    '# Check CPU info',
                    'lscpu | head -10',
                    '# Check kernel version',
                    'uname -a',
                    '# Check last logins',
                    'last -n 10'
                ]
            },
            {
                'name': 'compliance_status',
                'commands': [
                    '#!/bin/bash',
                    'echo "=== Compliance Status Audit ==="',
                    '# Check patch status',
                    'yum list updates 2>/dev/null | wc -l || apt list --upgradable 2>/dev/null | wc -l || echo "0"',
                    '# Check log retention',
                    'find /var/log -name "*.log" -mtime +30 | wc -l',
                    '# Check backup status',
                    'ls -la /backup/ 2>/dev/null || echo "No backup directory found"',
                    '# Check antivirus status',
                    'systemctl is-active clamav-daemon || echo "Antivirus not installed"',
                    '# Check monitoring agent',
                    'systemctl is-active amazon-cloudwatch-agent || echo "CloudWatch agent not active"'
                ]
            }
        ]
        
        # Execute audit checks
        for check in audit_checks:
            try:
                response = self.ssm.send_command(
                    InstanceIds=target_instances,
                    DocumentName='AWS-RunShellScript',
                    Parameters={'commands': check['commands']},
                    Comment=f"Infrastructure audit: {check['name']}",
                    MaxConcurrency='25%'
                )
                
                command_id = response['Command']['CommandId']
                
                # Wait for completion and collect results
                time.sleep(60)  # Allow time for execution
                
                check_results = {}
                for instance_id in target_instances:
                    try:
                        result = self.ssm.get_command_invocation(
                            CommandId=command_id,
                            InstanceId=instance_id
                        )
                        
                        check_results[instance_id] = {
                            'status': result['Status'],
                            'output': result.get('StandardOutputContent', ''),
                            'error': result.get('StandardErrorContent', '')
                        }
                        
                    except Exception as e:
                        check_results[instance_id] = {
                            'status': 'Failed',
                            'error': str(e)
                        }
                
                audit_results['findings'][check['name']] = check_results
                
            except Exception as e:
                audit_results['findings'][check['name']] = {
                    'error': f"Failed to execute audit check: {e}"
                }
        
        # Generate recommendations based on findings
        audit_results['recommendations'] = self._generate_audit_recommendations(audit_results['findings'])
        
        # Store audit results in S3
        if self.config_bucket:
            try:
                self.s3.put_object(
                    Bucket=self.config_bucket,
                    Key=f"audits/{audit_id}.json",
                    Body=json.dumps(audit_results, indent=2),
                    ContentType='application/json'
                )
            except Exception as e:
                self.logger.error(f"Failed to store audit results: {e}")
        
        return audit_results
    
    def _resolve_targets(self, target_selector: Dict[str, Any]) -> List[str]:
        """Resolve target instances based on selector criteria"""
        
        filters = [{'Name': 'instance-state-name', 'Values': ['running']}]
        
        # Build EC2 filters from selector
        if 'tags' in target_selector:
            for key, value in target_selector['tags'].items():
                filters.append({
                    'Name': f'tag:{key}',
                    'Values': [value] if isinstance(value, str) else value
                })
        
        # Query instances
        response = self.ec2.describe_instances(Filters=filters)
        
        instances = []
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                # Check if SSM agent is running
                try:
                    ping_response = self.ssm.describe_instance_information(
                        Filters=[{'Key': 'InstanceIds', 'Values': [instance['InstanceId']]}]
                    )
                    
                    if ping_response['InstanceInformationList']:
                        instances.append(instance['InstanceId'])
                        
                except Exception:
                    # Skip instances without SSM agent
                    continue
        
        return instances
    
    def _generate_configuration_script(self, configuration: Dict[str, Any]) -> str:
        """Generate bash script for configuration deployment"""
        
        script_lines = ['#!/bin/bash', 'set -e', '']
        script_lines.append('echo "Starting configuration deployment..."')
        
        # Process different configuration types
        if 'packages' in configuration:
            script_lines.extend([
                'echo "Installing packages..."',
                'if command -v yum >/dev/null 2>&1; then'
            ])
            for package in configuration['packages']:
                script_lines.append(f'  yum install -y {package}')
            script_lines.extend([
                'elif command -v apt >/dev/null 2>&1; then',
                '  apt update'
            ])
            for package in configuration['packages']:
                script_lines.append(f'  apt install -y {package}')
            script_lines.append('fi')
        
        if 'services' in configuration:
            script_lines.append('echo "Configuring services..."')
            for service_name, service_config in configuration['services'].items():
                if service_config.get('enabled', True):
                    script_lines.extend([
                        f'systemctl enable {service_name}',
                        f'systemctl start {service_name}'
                    ])
                else:
                    script_lines.extend([
                        f'systemctl stop {service_name}',
                        f'systemctl disable {service_name}'
                    ])
        
        if 'files' in configuration:
            script_lines.append('echo "Creating configuration files..."')
            for file_path, file_config in configuration['files'].items():
                script_lines.extend([
                    f'mkdir -p $(dirname {file_path})',
                    f'cat > {file_path} << "EOF"',
                    file_config.get('content', ''),
                    'EOF'
                ])
                
                if 'mode' in file_config:
                    script_lines.append(f'chmod {file_config["mode"]} {file_path}')
                
                if 'owner' in file_config:
                    script_lines.append(f'chown {file_config["owner"]} {file_path}')
        
        script_lines.append('echo "Configuration deployment completed successfully"')
        
        return '\n'.join(script_lines)
    
    def _track_configuration_deployment(self, deployment_id: str, command_id: str, 
                                      instances: List[str]) -> None:
        """Track configuration deployment progress"""
        
        def track():
            while True:
                try:
                    # Check command status
                    response = self.ssm.list_command_invocations(CommandId=command_id)
                    
                    completed = 0
                    failed = 0
                    
                    for invocation in response['CommandInvocations']:
                        status = invocation['Status']
                        if status in ['Success', 'Failed', 'Cancelled', 'TimedOut']:
                            if status == 'Success':
                                completed += 1
                            else:
                                failed += 1
                    
                    total = len(instances)
                    pending = total - completed - failed
                    
                    self.logger.info(f"Deployment {deployment_id}: {completed}/{total} completed, "
                                   f"{failed} failed, {pending} pending")
                    
                    if pending == 0:
                        break
                    
                    time.sleep(30)
                    
                except Exception as e:
                    self.logger.error(f"Tracking error for {deployment_id}: {e}")
                    break
        
        # Start tracking thread
        import threading
        track_thread = threading.Thread(target=track)
        track_thread.daemon = True
        track_thread.start()
    
    def _generate_audit_recommendations(self, findings: Dict[str, Any]) -> List[str]:
        """Generate security and compliance recommendations based on audit findings"""
        
        recommendations = []
        
        # Analyze security findings
        if 'security_configuration' in findings:
            for instance_id, result in findings['security_configuration'].items():
                if result.get('status') == 'Success':
                    output = result.get('output', '')
                    
                    if 'PasswordAuthentication yes' in output:
                        recommendations.append(f"Instance {instance_id}: Disable SSH password authentication")
                    
                    if 'PermitRootLogin yes' in output:
                        recommendations.append(f"Instance {instance_id}: Disable SSH root login")
                    
                    if 'inactive' in output and 'firewall' in output.lower():
                        recommendations.append(f"Instance {instance_id}: Enable firewall service")
        
        # Analyze system health
        if 'system_health' in findings:
            for instance_id, result in findings['system_health'].items():
                if result.get('status') == 'Success':
                    output = result.get('output', '')
                    
                    # Check disk usage
                    for line in output.split('\n'):
                        if '%' in line and ('9[0-9]%' in line or '100%' in line):
                            recommendations.append(f"Instance {instance_id}: High disk usage detected - clean up disk space")
                    
                    # Check load average
                    if 'load average:' in output:
                        load_line = [line for line in output.split('\n') if 'load average:' in line]
                        if load_line:
                            load_values = load_line[0].split('load average:')[1].strip().split(',')
                            try:
                                load_1min = float(load_values[0].strip())
                                if load_1min > 2.0:
                                    recommendations.append(f"Instance {instance_id}: High system load - investigate performance issues")
                            except:
                                pass
        
        # Analyze compliance status
        if 'compliance_status' in findings:
            for instance_id, result in findings['compliance_status'].items():
                if result.get('status') == 'Success':
                    output = result.get('output', '')
                    
                    lines = output.split('\n')
                    if lines and lines[0].strip().isdigit():
                        pending_updates = int(lines[0].strip())
                        if pending_updates > 0:
                            recommendations.append(f"Instance {instance_id}: {pending_updates} pending security updates")
                    
                    if 'CloudWatch agent not active' in output:
                        recommendations.append(f"Instance {instance_id}: Install and configure CloudWatch agent")
                    
                    if 'Antivirus not installed' in output:
                        recommendations.append(f"Instance {instance_id}: Install antivirus solution")
        
        return recommendations

# Usage Example for Enterprise SSM Orchestration
if __name__ == "__main__":
    # Initialize orchestrator
    orchestrator = EnterpriseSSMOrchestrator()
    
    # Define complex workflow steps
    workflow_steps = [
        OrchestrationStep(
            name="PreDeploymentCheck",
            action="aws:runCommand",
            parameters={
                "commands": [
                    "#!/bin/bash",
                    "echo 'Running pre-deployment checks...'",
                    "systemctl status httpd",
                    "df -h | grep '/var' | awk '{print $5}' | sed 's/%//' | while read usage; do [ $usage -lt 80 ] || exit 1; done"
                ]
            },
            timeout=300
        ),
        OrchestrationStep(
            name="StopServices",
            action="aws:runCommand",
            parameters={
                "commands": [
                    "systemctl stop httpd",
                    "systemctl stop nginx"
                ]
            },
            dependencies=["PreDeploymentCheck"],
            timeout=120
        ),
        OrchestrationStep(
            name="DeployApplication",
            action="aws:runCommand",
            parameters={
                "commands": [
                    "#!/bin/bash",
                    "cd /opt/myapp",
                    "aws s3 cp s3://my-deployments/latest.tar.gz .",
                    "tar -xzf latest.tar.gz",
                    "chown -R myapp:myapp ."
                ]
            },
            dependencies=["StopServices"],
            timeout=600
        ),
        OrchestrationStep(
            name="StartServices",
            action="aws:runCommand",
            parameters={
                "commands": [
                    "systemctl start httpd",
                    "systemctl start nginx",
                    "sleep 10"
                ]
            },
            dependencies=["DeployApplication"],
            timeout=180
        ),
        OrchestrationStep(
            name="HealthCheck",
            action="aws:runCommand",
            parameters={
                "commands": [
                    "#!/bin/bash",
                    "for i in {1..30}; do",
                    "  if curl -f http://localhost/health; then",
                    "    echo 'Health check passed'",
                    "    exit 0",
                    "  fi",
                    "  sleep 5",
                    "done",
                    "echo 'Health check failed'",
                    "exit 1"
                ]
            },
            dependencies=["StartServices"],
            timeout=300
        )
    ]
    
    # Create and execute workflow
    workflow_id = orchestrator.create_workflow("ProductionDeployment", workflow_steps)
    
    execution_id = orchestrator.execute_workflow(
        workflow_id=workflow_id,
        parameters={"ExecutionMode": "sequential"},
        target_selector={
            "tags": {
                "Environment": "production",
                "Application": "myapp"
            },
            "instance_states": ["running"]
        }
    )
    
    print(f"Workflow execution started: {execution_id}")
```

### Advanced Parameter Store Management

```python
# parameter-store-manager.py - Enterprise parameter management with encryption and compliance
import boto3
import json
import re
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import hashlib
import yaml

class EnterpriseParameterManager:
    """
    Enterprise-grade parameter management with hierarchical organization,
    encryption, compliance monitoring, and automated lifecycle management.
    """
    
    def __init__(self, region_name: str = 'us-west-2'):
        self.ssm = boto3.client('ssm', region_name=region_name)
        self.kms = boto3.client('kms', region_name=region_name)
        self.cloudwatch = boto3.client('cloudwatch', region_name=region_name)
        
        # Parameter organization patterns
        self.hierarchy_patterns = {
            'application': '/{application}/{environment}/{component}/{parameter}',
            'service': '/{service}/{version}/{environment}/{parameter}',
            'infrastructure': '/infrastructure/{region}/{resource_type}/{parameter}',
            'security': '/security/{domain}/{component}/{parameter}'
        }
        
        # Encryption policies
        self.encryption_policies = {
            'sensitive_patterns': [
                r'.*password.*',
                r'.*secret.*',
                r'.*key.*',
                r'.*token.*',
                r'.*credential.*',
                r'.*api[_-]?key.*',
                r'.*connection[_-]?string.*'
            ],
            'compliance_patterns': [
                r'.*/security/.*',
                r'.*/compliance/.*',
                r'.*/audit/.*'
            ]
        }
    
    def create_parameter_hierarchy(self, hierarchy_type: str, 
                                 parameters: Dict[str, Any],
                                 context: Dict[str, str]) -> Dict[str, str]:
        """Create a hierarchical parameter structure with consistent naming"""
        
        if hierarchy_type not in self.hierarchy_patterns:
            raise ValueError(f"Unknown hierarchy type: {hierarchy_type}")
        
        pattern = self.hierarchy_patterns[hierarchy_type]
        created_parameters = {}
        
        for param_name, param_value in parameters.items():
            # Generate parameter path
            param_path = pattern.format(**context, parameter=param_name)
            
            # Determine parameter type and encryption
            param_type, key_id = self._determine_parameter_security(param_name, param_value)
            
            # Create parameter
            try:
                put_params = {
                    'Name': param_path,
                    'Value': str(param_value),
                    'Type': param_type,
                    'Description': f"Auto-generated parameter for {hierarchy_type}",
                    'Tags': self._generate_parameter_tags(hierarchy_type, context, param_name),
                    'Overwrite': True
                }
                
                if key_id:
                    put_params['KeyId'] = key_id
                
                self.ssm.put_parameter(**put_params)
                created_parameters[param_name] = param_path
                
                print(f"Created parameter: {param_path} (type: {param_type})")
                
            except Exception as e:
                print(f"Failed to create parameter {param_path}: {e}")
                continue
        
        return created_parameters
    
    def bulk_import_parameters(self, import_file: str, format_type: str = 'yaml',
                             hierarchy_type: str = 'application',
                             context: Dict[str, str] = None) -> Dict[str, Any]:
        """Bulk import parameters from configuration files"""
        
        import_results = {
            'success': {},
            'failed': {},
            'skipped': {}
        }
        
        # Read import file
        try:
            with open(import_file, 'r') as f:
                if format_type.lower() == 'yaml':
                    data = yaml.safe_load(f)
                elif format_type.lower() == 'json':
                    data = json.load(f)
                else:
                    raise ValueError(f"Unsupported format: {format_type}")
        except Exception as e:
            raise ValueError(f"Failed to read import file: {e}")
        
        # Process parameters
        def process_nested_dict(nested_data: Dict, prefix: str = ''):
            for key, value in nested_data.items():
                param_name = f"{prefix}/{key}" if prefix else key
                
                if isinstance(value, dict):
                    # Recursively process nested dictionaries
                    process_nested_dict(value, param_name)
                else:
                    # Create parameter
                    try:
                        param_context = context or {}
                        param_context['parameter'] = param_name
                        
                        created_params = self.create_parameter_hierarchy(
                            hierarchy_type, 
                            {param_name: value}, 
                            param_context
                        )
                        
                        import_results['success'].update(created_params)
                        
                    except Exception as e:
                        import_results['failed'][param_name] = str(e)
        
        process_nested_dict(data)
        
        # Generate import summary
        import_results['summary'] = {
            'total_processed': len(import_results['success']) + len(import_results['failed']),
            'successful': len(import_results['success']),
            'failed': len(import_results['failed']),
            'import_time': datetime.now().isoformat()
        }
        
        return import_results
    
    def setup_parameter_lifecycle_management(self, lifecycle_policies: Dict[str, Any]) -> None:
        """Setup automated parameter lifecycle management"""
        
        for policy_name, policy_config in lifecycle_policies.items():
            # Create CloudWatch rule for lifecycle events
            rule_name = f"ParameterLifecycle-{policy_name}"
            
            # Schedule expression for lifecycle checks
            schedule = policy_config.get('schedule', 'rate(7 days)')
            
            # Create lifecycle automation document
            document_content = {
                "schemaVersion": "0.3",
                "description": f"Parameter lifecycle management: {policy_name}",
                "parameters": {
                    "PolicyName": {
                        "type": "String",
                        "description": "Lifecycle policy name",
                        "default": policy_name
                    }
                },
                "mainSteps": [
                    {
                        "name": "IdentifyExpiredParameters",
                        "action": "aws:executeScript",
                        "inputs": {
                            "Runtime": "python3.8",
                            "Handler": "lifecycle_handler",
                            "Script": self._generate_lifecycle_script(policy_config)
                        }
                    }
                ]
            }
            
            try:
                self.ssm.create_document(
                    Content=json.dumps(document_content),
                    Name=f"ParameterLifecycle-{policy_name}",
                    DocumentType='Automation',
                    DocumentFormat='JSON'
                )
                
                print(f"Created lifecycle policy: {policy_name}")
                
            except Exception as e:
                print(f"Failed to create lifecycle policy {policy_name}: {e}")
    
    def audit_parameter_security(self, scope: str = '/*') -> Dict[str, Any]:
        """Comprehensive security audit of parameter store"""
        
        audit_results = {
            'timestamp': datetime.now().isoformat(),
            'scope': scope,
            'findings': {
                'unencrypted_sensitive': [],
                'weak_encryption': [],
                'compliance_violations': [],
                'access_anomalies': []
            },
            'statistics': {},
            'recommendations': []
        }
        
        # Get all parameters in scope
        paginator = self.ssm.get_paginator('get_parameters_by_path')
        
        all_parameters = []
        for page in paginator.paginate(Path=scope, Recursive=True, WithDecryption=False):
            all_parameters.extend(page['Parameters'])
        
        # Analyze parameters
        for param in all_parameters:
            param_name = param['Name']
            param_type = param['Type']
            
            # Check for sensitive parameters without encryption
            if self._is_sensitive_parameter(param_name) and param_type != 'SecureString':
                audit_results['findings']['unencrypted_sensitive'].append({
                    'name': param_name,
                    'type': param_type,
                    'issue': 'Sensitive parameter not encrypted'
                })
            
            # Check encryption key usage
            if param_type == 'SecureString':
                key_id = param.get('KeyId', 'alias/aws/ssm')
                if key_id == 'alias/aws/ssm':
                    audit_results['findings']['weak_encryption'].append({
                        'name': param_name,
                        'key_id': key_id,
                        'issue': 'Using default AWS managed key'
                    })
            
            # Check compliance requirements
            if self._requires_compliance_encryption(param_name) and param_type != 'SecureString':
                audit_results['findings']['compliance_violations'].append({
                    'name': param_name,
                    'type': param_type,
                    'issue': 'Compliance parameter not encrypted'
                })
        
        # Generate statistics
        audit_results['statistics'] = {
            'total_parameters': len(all_parameters),
            'secure_string_count': len([p for p in all_parameters if p['Type'] == 'SecureString']),
            'string_count': len([p for p in all_parameters if p['Type'] == 'String']),
            'string_list_count': len([p for p in all_parameters if p['Type'] == 'StringList']),
            'unencrypted_sensitive_count': len(audit_results['findings']['unencrypted_sensitive']),
            'compliance_violations_count': len(audit_results['findings']['compliance_violations'])
        }
        
        # Generate recommendations
        audit_results['recommendations'] = self._generate_security_recommendations(audit_results['findings'])
        
        return audit_results
    
    def implement_parameter_versioning_strategy(self, versioning_config: Dict[str, Any]) -> None:
        """Implement comprehensive parameter versioning and rollback strategy"""
        
        # Create parameter versioning automation
        versioning_document = {
            "schemaVersion": "0.3",
            "description": "Parameter versioning and rollback automation",
            "parameters": {
                "ParameterName": {
                    "type": "String",
                    "description": "Parameter name to manage"
                },
                "Action": {
                    "type": "String",
                    "description": "Action to perform (backup, rollback, cleanup)",
                    "allowedValues": ["backup", "rollback", "cleanup"]
                }
            },
            "mainSteps": [
                {
                    "name": "ExecuteVersioningAction",
                    "action": "aws:executeScript",
                    "inputs": {
                        "Runtime": "python3.8",
                        "Handler": "versioning_handler",
                        "Script": self._generate_versioning_script(versioning_config)
                    }
                }
            ]
        }
        
        try:
            self.ssm.create_document(
                Content=json.dumps(versioning_document),
                Name="ParameterVersioningManager",
                DocumentType='Automation',
                DocumentFormat='JSON'
            )
            
            print("Parameter versioning strategy implemented successfully")
            
        except Exception as e:
            print(f"Failed to implement versioning strategy: {e}")
    
    def _determine_parameter_security(self, param_name: str, param_value: Any) -> tuple:
        """Determine parameter type and encryption requirements"""
        
        param_type = 'String'
        key_id = None
        
        # Check if parameter is sensitive
        if self._is_sensitive_parameter(param_name):
            param_type = 'SecureString'
            key_id = self._get_encryption_key_for_parameter(param_name)
        
        # Check if parameter requires compliance encryption
        elif self._requires_compliance_encryption(param_name):
            param_type = 'SecureString'
            key_id = 'alias/compliance-key'
        
        return param_type, key_id
    
    def _is_sensitive_parameter(self, param_name: str) -> bool:
        """Check if parameter name matches sensitive patterns"""
        
        for pattern in self.encryption_policies['sensitive_patterns']:
            if re.match(pattern, param_name.lower()):
                return True
        return False
    
    def _requires_compliance_encryption(self, param_name: str) -> bool:
        """Check if parameter requires compliance-level encryption"""
        
        for pattern in self.encryption_policies['compliance_patterns']:
            if re.match(pattern, param_name.lower()):
                return True
        return False
    
    def _get_encryption_key_for_parameter(self, param_name: str) -> str:
        """Get appropriate KMS key for parameter encryption"""
        
        # Default to application-specific key
        if '/application/' in param_name:
            return 'alias/application-parameters-key'
        elif '/infrastructure/' in param_name:
            return 'alias/infrastructure-parameters-key'
        elif '/security/' in param_name:
            return 'alias/security-parameters-key'
        else:
            return 'alias/general-parameters-key'
    
    def _generate_parameter_tags(self, hierarchy_type: str, context: Dict[str, str], 
                                param_name: str) -> List[Dict[str, str]]:
        """Generate appropriate tags for parameter"""
        
        tags = [
            {'Key': 'HierarchyType', 'Value': hierarchy_type},
            {'Key': 'ParameterName', 'Value': param_name},
            {'Key': 'CreatedBy', 'Value': 'EnterpriseParameterManager'},
            {'Key': 'CreatedDate', 'Value': datetime.now().strftime('%Y-%m-%d')},
            {'Key': 'ManagedBy', 'Value': 'Automation'}
        ]
        
        # Add context-specific tags
        for key, value in context.items():
            tags.append({'Key': key.title(), 'Value': value})
        
        return tags
    
    def _generate_lifecycle_script(self, policy_config: Dict[str, Any]) -> str:
        """Generate Python script for parameter lifecycle management"""
        
        script = f'''
import boto3
import json
from datetime import datetime, timedelta

def lifecycle_handler(events, context):
    ssm = boto3.client('ssm')
    
    # Policy configuration
    max_age_days = {policy_config.get('max_age_days', 365)}
    retention_policy = "{policy_config.get('retention_policy', 'archive')}"
    
    # Get parameters matching lifecycle criteria
    paginator = ssm.get_paginator('describe_parameters')
    
    expired_parameters = []
    
    for page in paginator.paginate():
        for param in page['Parameters']:
            last_modified = param['LastModifiedDate']
            age_days = (datetime.now(last_modified.tzinfo) - last_modified).days
            
            if age_days > max_age_days:
                expired_parameters.append({{
                    'name': param['Name'],
                    'age_days': age_days,
                    'last_modified': last_modified.isoformat()
                }})
    
    # Process expired parameters based on retention policy
    if retention_policy == 'delete':
        for param in expired_parameters:
            try:
                ssm.delete_parameter(Name=param['name'])
                print(f"Deleted expired parameter: {{param['name']}}")
            except Exception as e:
                print(f"Failed to delete parameter {{param['name']}}: {{e}}")
    
    elif retention_policy == 'archive':
        # Archive to S3 or move to archive path
        for param in expired_parameters:
            try:
                # Get parameter value
                response = ssm.get_parameter(Name=param['name'], WithDecryption=True)
                param_value = response['Parameter']['Value']
                
                # Create archive parameter
                archive_name = f"/archive{{param['name']}}"
                ssm.put_parameter(
                    Name=archive_name,
                    Value=param_value,
                    Type=response['Parameter']['Type'],
                    Description=f"Archived from {{param['name']}} on {{datetime.now().isoformat()}}"
                )
                
                # Delete original parameter
                ssm.delete_parameter(Name=param['name'])
                print(f"Archived parameter: {{param['name']}} -> {{archive_name}}")
                
            except Exception as e:
                print(f"Failed to archive parameter {{param['name']}}: {{e}}")
    
    return {{
        'statusCode': 200,
        'body': json.dumps({{
            'processed': len(expired_parameters),
            'policy': retention_policy,
            'expired_parameters': expired_parameters
        }})
    }}
'''
        return script
    
    def _generate_versioning_script(self, versioning_config: Dict[str, Any]) -> str:
        """Generate Python script for parameter versioning management"""
        
        script = '''
import boto3
import json
from datetime import datetime

def versioning_handler(events, context):
    ssm = boto3.client('ssm')
    s3 = boto3.client('s3')
    
    parameter_name = events['ParameterName']
    action = events['Action']
    
    backup_bucket = "parameter-store-backups"
    
    if action == 'backup':
        # Create backup of current parameter
        try:
            response = ssm.get_parameter(Name=parameter_name, WithDecryption=True)
            parameter = response['Parameter']
            
            backup_key = f"backups/{parameter_name.lstrip('/')}/{datetime.now().isoformat()}.json"
            
            backup_data = {
                'name': parameter['Name'],
                'value': parameter['Value'],
                'type': parameter['Type'],
                'version': parameter['Version'],
                'last_modified': parameter['LastModifiedDate'].isoformat(),
                'backup_time': datetime.now().isoformat()
            }
            
            s3.put_object(
                Bucket=backup_bucket,
                Key=backup_key,
                Body=json.dumps(backup_data),
                ContentType='application/json'
            )
            
            return {'statusCode': 200, 'message': f'Parameter backed up to {backup_key}'}
            
        except Exception as e:
            return {'statusCode': 500, 'error': str(e)}
    
    elif action == 'rollback':
        # Rollback to previous version
        try:
            # List parameter history
            response = ssm.get_parameter_history(Name=parameter_name)
            history = response['Parameters']
            
            if len(history) < 2:
                return {'statusCode': 400, 'error': 'No previous version available'}
            
            # Get previous version (second most recent)
            previous_version = history[-2]
            
            # Restore previous version
            ssm.put_parameter(
                Name=parameter_name,
                Value=previous_version['Value'],
                Type=previous_version['Type'],
                Overwrite=True,
                Description=f"Rolled back from version {history[-1]['Version']} to {previous_version['Version']}"
            )
            
            return {'statusCode': 200, 'message': f'Parameter rolled back to version {previous_version["Version"]}'}
            
        except Exception as e:
            return {'statusCode': 500, 'error': str(e)}
    
    elif action == 'cleanup':
        # Clean up old parameter versions
        try:
            response = ssm.get_parameter_history(Name=parameter_name)
            history = response['Parameters']
            
            # Keep only the latest 10 versions
            versions_to_keep = 10
            
            if len(history) > versions_to_keep:
                # AWS doesn't support deleting specific parameter versions
                # Log versions that would be cleaned up
                old_versions = history[:-versions_to_keep]
                
                return {
                    'statusCode': 200, 
                    'message': f'Would clean up {len(old_versions)} old versions',
                    'old_versions': [v['Version'] for v in old_versions]
                }
            else:
                return {'statusCode': 200, 'message': 'No cleanup needed'}
                
        except Exception as e:
            return {'statusCode': 500, 'error': str(e)}
    
    return {'statusCode': 400, 'error': 'Invalid action'}
'''
        return script
    
    def _generate_security_recommendations(self, findings: Dict[str, List]) -> List[str]:
        """Generate security recommendations based on audit findings"""
        
        recommendations = []
        
        if findings['unencrypted_sensitive']:
            recommendations.append(
                f"Encrypt {len(findings['unencrypted_sensitive'])} sensitive parameters "
                "using SecureString type with customer-managed KMS keys"
            )
        
        if findings['weak_encryption']:
            recommendations.append(
                f"Upgrade {len(findings['weak_encryption'])} parameters to use "
                "customer-managed KMS keys instead of AWS managed keys"
            )
        
        if findings['compliance_violations']:
            recommendations.append(
                f"Address {len(findings['compliance_violations'])} compliance violations "
                "by implementing proper encryption for regulatory parameters"
            )
        
        recommendations.extend([
            "Implement automated parameter lifecycle management",
            "Setup parameter access monitoring with CloudTrail",
            "Establish parameter naming conventions and hierarchical organization",
            "Create parameter backup and disaster recovery procedures",
            "Implement least-privilege IAM policies for parameter access"
        ])
        
        return recommendations

# Example usage
if __name__ == "__main__":
    param_manager = EnterpriseParameterManager()
    
    # Create application parameter hierarchy
    app_params = {
        'database_host': 'prod-db.company.com',
        'database_port': '5432',
        'database_password': 'super-secret-password',
        'api_key': 'sk-1234567890abcdef',
        'debug_mode': 'false',
        'max_connections': '100'
    }
    
    context = {
        'application': 'myapp',
        'environment': 'production',
        'component': 'backend'
    }
    
    created_params = param_manager.create_parameter_hierarchy(
        'application', app_params, context
    )
    
    print(f"Created {len(created_params)} parameters")
    
    # Perform security audit
    audit_results = param_manager.audit_parameter_security('/myapp/')
    print(f"Security audit found {audit_results['statistics']['total_parameters']} parameters")
```

## Best Practices

### Security Best Practices
- **Use IAM roles** instead of storing credentials in Parameter Store when possible
- **Encrypt sensitive parameters** with customer-managed KMS keys
- **Implement least privilege** access with resource-based permissions
- **Enable CloudTrail logging** for all SSM API calls
- **Use Session Manager** instead of SSH for secure access

### Operational Excellence
- **Organize parameters hierarchically** using consistent naming conventions
- **Use tags extensively** for resource organization and automation
- **Implement automated testing** for SSM documents before production use
- **Monitor execution metrics** and set up alerts for failed operations
- **Document all automation workflows** with clear descriptions

### Cost Optimization
- **Use appropriate parameter tiers** (Standard vs Advanced) based on needs
- **Clean up old parameter versions** regularly
- **Optimize automation documents** to minimize execution time
- **Use resource groups** for efficient bulk operations
- **Monitor API usage** to identify optimization opportunities

### Integration Best Practices
- **Integrate with CI/CD pipelines** for automated deployments
- **Use with CloudFormation** for infrastructure automation
- **Combine with CloudWatch** for comprehensive monitoring
- **Leverage with Lambda** for event-driven automation
- **Connect to on-premises** systems using hybrid activations

### Enterprise Automation Patterns
- **Implement workflow orchestration** with dependency management and error handling
- **Use GitOps integration** for infrastructure configuration management
- **Setup compliance monitoring** with automated remediation capabilities
- **Perform regular infrastructure audits** with comprehensive security analysis
- **Establish parameter lifecycle management** with versioning and rollback strategies