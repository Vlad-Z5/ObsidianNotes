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