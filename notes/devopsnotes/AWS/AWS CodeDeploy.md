# AWS CodeDeploy

> **Service Type:** Deployment Automation | **Tier:** CI/CD and Automation | **Global/Regional:** Regional

## Overview

AWS CodeDeploy is a fully managed deployment service that automates software deployments to various compute platforms including Amazon EC2, AWS Fargate, AWS Lambda, and on-premises servers. It provides multiple deployment strategies to minimize downtime and reduce deployment risks through automated rollbacks and traffic shifting.

## DevOps Use Cases

### Zero-Downtime Deployments
- **Blue-green deployments** for complete environment switching with instant rollback
- **Rolling deployments** for gradual instance-by-instance updates
- **Traffic shifting** for Lambda functions with weighted routing
- **Canary deployments** for risk mitigation with gradual traffic increase

### Automated Risk Management
- **Health checks** during deployment with automatic rollback on failures
- **Deployment monitoring** with CloudWatch integration for real-time insights
- **Stop conditions** to halt deployments based on CloudWatch alarms
- **Manual approval gates** for production deployments with human oversight

### Multi-Platform Deployment
- **EC2 instances** with Auto Scaling integration for dynamic environments
- **On-premises servers** using CodeDeploy agent for hybrid deployments
- **Lambda functions** with alias-based traffic shifting
- **ECS services** with blue-green container deployments

### CI/CD Pipeline Integration
- **CodePipeline integration** for end-to-end automated delivery
- **GitHub Actions** and Jenkins integration for third-party CI/CD
- **Artifact management** with S3 and GitHub source integration
- **Deployment triggers** based on code commits and manual approvals

### Enterprise Deployment Governance
- **Deployment groups** for organizing targets by environment or function
- **IAM-based permissions** for controlled access to deployment operations
- **Deployment history** and audit trails for compliance requirements
- **Cross-region deployments** for global application distribution

## Core Components

### Applications
- **Container** for deployment groups and revisions
- **Compute platform** specification (EC2/On-Premises, Lambda, ECS)
- **Naming convention** for organization and management
- **IAM permissions** for deployment operations

### Deployment Groups
- **Target definition** using tags, Auto Scaling groups, or instance IDs
- **Load balancer configuration** for traffic management during deployments
- **Auto Scaling integration** for dynamic instance management
- **Alarm configuration** for deployment monitoring and rollback triggers

### Deployment Configurations
- **Predefined configurations** for common deployment patterns
- **Custom configurations** for specific deployment requirements
- **Traffic shifting rules** for Lambda and ECS deployments
- **Health check parameters** for deployment validation

### Application Revisions
- **Source location** (S3 bucket or GitHub repository)
- **AppSpec file** defining deployment instructions
- **Revision metadata** for tracking and rollback purposes
- **Artifact packaging** requirements for different platforms

## Deployment Strategies

### EC2/On-Premises Deployments

#### In-Place Deployments
- **Rolling updates** with configurable batch sizes
- **Health checks** before proceeding to next batch
- **Load balancer deregistration** during instance updates
- **Application lifecycle events** for custom deployment logic

#### Blue-Green Deployments
- **Environment provisioning** with identical infrastructure
- **Traffic switching** through load balancer configuration
- **Automatic termination** of old environment after successful deployment
- **Instant rollback** by switching traffic back to original environment

### Lambda Deployments

#### Traffic Shifting Patterns
- **Canary deployments** with small percentage traffic shifts
- **Linear deployments** with gradual traffic increases over time
- **All-at-once deployments** for immediate complete switching
- **Alias-based routing** for seamless function version management

### ECS Deployments

#### Blue-Green Service Updates
- **Task definition updates** with new container versions
- **Service replacement** with new task definition
- **Load balancer target group** switching for traffic management
- **Rollback capability** through previous task definition restoration

## Practical CLI Examples

### Application and Deployment Group Management

```bash
# Create CodeDeploy application
aws deploy create-application \
  --application-name MyWebApp \
  --compute-platform Server \
  --tags Key=Environment,Value=Production Key=Team,Value=DevOps

# Create deployment group for EC2
aws deploy create-deployment-group \
  --application-name MyWebApp \
  --deployment-group-name Production-WebServers \
  --service-role-arn arn:aws:iam::123456789012:role/CodeDeployServiceRole \
  --deployment-config-name CodeDeployDefault.EC2AllAtOneBlueGreen \
  --ec2-tag-filters Key=Environment,Type=KEY_AND_VALUE,Value=Production Key=Role,Type=KEY_AND_VALUE,Value=WebServer \
  --load-balancer-info targetGroupInfoList=[{name=my-target-group}] \
  --blue-green-deployment-configuration 'terminateBlueInstancesOnDeploymentSuccess={action=TERMINATE,terminationWaitTimeInMinutes=5},deploymentReadyOption={actionOnTimeout=CONTINUE_DEPLOYMENT},greenFleetProvisioningOption={action=COPY_AUTO_SCALING_GROUP}'

# Create deployment group for Lambda
aws deploy create-deployment-group \
  --application-name MyLambdaApp \
  --deployment-group-name Production-Lambda \
  --service-role-arn arn:aws:iam::123456789012:role/CodeDeployServiceRole \
  --deployment-config-name CodeDeployDefault.LambdaCanary10Percent5Minutes \
  --alarm-configuration enabled=true,alarms=[{name=MyLambdaErrorAlarm}] \
  --auto-rollback-configuration enabled=true,events=DEPLOYMENT_FAILURE,events=DEPLOYMENT_STOP_ON_ALARM

# Update deployment group
aws deploy update-deployment-group \
  --application-name MyWebApp \
  --current-deployment-group-name Production-WebServers \
  --deployment-config-name CodeDeployDefault.EC2AllAtOneBlueGreenReplacement \
  --alarm-configuration enabled=true,alarms=[{name=HighErrorRate},{name=HighResponseTime}]
```

### Deployment Operations

```bash
# Create deployment from S3
aws deploy create-deployment \
  --application-name MyWebApp \
  --deployment-group-name Production-WebServers \
  --deployment-config-name CodeDeployDefault.EC2AllAtOneBlueGreen \
  --s3-location bucket=my-deployment-bucket,key=applications/myapp-v1.2.3.zip,bundleType=zip \
  --description "Production deployment v1.2.3" \
  --file-exists-behavior OVERWRITE

# Create deployment from GitHub
aws deploy create-deployment \
  --application-name MyWebApp \
  --deployment-group-name Staging-WebServers \
  --github-location repository=myorg/myapp,commitId=abc123def456 \
  --deployment-config-name CodeDeployDefault.EC2OneAtATime \
  --description "Staging deployment from latest commit"

# Create Lambda deployment with traffic shifting
aws deploy create-deployment \
  --application-name MyLambdaApp \
  --deployment-group-name Production-Lambda \
  --deployment-config-name CodeDeployDefault.LambdaLinear10PercentEvery2Minutes \
  --revision '{"revisionType":"S3","s3Location":{"bucket":"my-lambda-bucket","key":"function.zip","bundleType":"zip"}}' \
  --description "Lambda canary deployment"

# Stop deployment
aws deploy stop-deployment \
  --deployment-id d-1234567890abcdef0 \
  --auto-rollback-enabled

# Get deployment status
aws deploy get-deployment \
  --deployment-id d-1234567890abcdef0

# List deployments
aws deploy list-deployments \
  --application-name MyWebApp \
  --deployment-group-name Production-WebServers \
  --include-only-statuses Created InProgress Succeeded Failed Stopped
```

### Deployment Configuration Management

```bash
# Create custom deployment configuration for EC2
aws deploy create-deployment-config \
  --deployment-config-name Custom-75Percent-MinimumHealthy \
  --minimum-healthy-hosts type=FLEET_PERCENT,value=75 \
  --compute-platform Server

# Create custom Lambda deployment configuration
aws deploy create-deployment-config \
  --deployment-config-name Custom-Lambda-Canary5Percent \
  --traffic-routing-config 'type=TimeBasedCanary,timeBasedCanary={canaryPercentage=5,canaryInterval=2}' \
  --compute-platform Lambda

# List deployment configurations
aws deploy list-deployment-configs \
  --compute-platform Server
```

## AppSpec File Examples

### EC2/On-Premises AppSpec (appspec.yml)

```yaml
version: 0.0
os: linux
files:
  - source: /
    destination: /opt/myapp
    overwrite: yes
permissions:
  - object: /opt/myapp
    pattern: "**"
    owner: myapp
    group: myapp
    mode: 755
  - object: /opt/myapp/bin
    pattern: "**"
    mode: 755
  - object: /opt/myapp/config
    pattern: "**"
    mode: 600
hooks:
  BeforeInstall:
    - location: scripts/install_dependencies.sh
      timeout: 300
      runas: root
  AfterInstall:
    - location: scripts/setup_application.sh
      timeout: 300
      runas: myapp
  ApplicationStart:
    - location: scripts/start_server.sh
      timeout: 300
      runas: myapp
  ApplicationStop:
    - location: scripts/stop_server.sh
      timeout: 300
      runas: myapp
  ValidateService:
    - location: scripts/validate_service.sh
      timeout: 300
      runas: myapp
```

### Lambda AppSpec (appspec.yml)

```yaml
version: 0.0
Resources:
  - MyLambdaFunction:
      Type: AWS::Lambda::Function
      Properties:
        Name: "MyFunction"
        Alias: "MyFunctionAlias"
        CurrentVersion: "1"
        TargetVersion: "2"
Hooks:
  BeforeAllowTraffic:
    - MyValidationFunction
  AfterAllowTraffic:
    - MyPostDeploymentFunction
```

### ECS AppSpec (appspec.yml)

```yaml
version: 0.0
Resources:
  - TargetService:
      Type: AWS::ECS::Service
      Properties:
        TaskDefinition: "arn:aws:ecs:us-west-2:123456789012:task-definition/my-app:2"
        LoadBalancerInfo:
          ContainerName: "my-app-container"
          ContainerPort: 80
Hooks:
  BeforeInstall:
    - BeforeInstallHookFunctionName
  AfterInstall:
    - AfterInstallHookFunctionName
  AfterAllowTestTraffic:
    - AfterAllowTestTrafficHookFunctionName
  BeforeAllowTraffic:
    - BeforeAllowTrafficHookFunctionName
  AfterAllowTraffic:
    - AfterAllowTrafficHookFunctionName
```

## DevOps Automation Scripts

### Automated Deployment Pipeline

```bash
#!/bin/bash
# deploy-application.sh - Comprehensive deployment automation

APP_NAME=$1
ENVIRONMENT=$2
VERSION=$3
DEPLOYMENT_TYPE=${4:-blue-green}

if [ $# -lt 3 ]; then
    echo "Usage: $0 <app-name> <environment> <version> [deployment-type]"
    exit 1
fi

echo "Starting deployment of ${APP_NAME} v${VERSION} to ${ENVIRONMENT}"

# Set deployment configuration based on type and environment
case $DEPLOYMENT_TYPE in
    "blue-green")
        if [ "$ENVIRONMENT" = "production" ]; then
            DEPLOYMENT_CONFIG="CodeDeployDefault.EC2AllAtOneBlueGreen"
        else
            DEPLOYMENT_CONFIG="CodeDeployDefault.EC2AllAtOneBlueGreenReplacement"
        fi
        ;;
    "rolling")
        DEPLOYMENT_CONFIG="CodeDeployDefault.EC2OneAtATime"
        ;;
    "canary")
        DEPLOYMENT_CONFIG="Custom-50Percent-MinimumHealthy"
        ;;
    *)
        echo "Unknown deployment type: $DEPLOYMENT_TYPE"
        exit 1
        ;;
esac

# Build deployment package if needed
if [ ! -f "deployments/${APP_NAME}-${VERSION}.zip" ]; then
    echo "Building deployment package..."
    mkdir -p deployments
    
    # Create deployment structure
    mkdir -p temp-deploy/{scripts,config}
    
    # Copy application files
    cp -r src/* temp-deploy/
    cp appspec.yml temp-deploy/
    cp scripts/* temp-deploy/scripts/
    cp config/${ENVIRONMENT}.conf temp-deploy/config/app.conf
    
    # Create deployment package
    cd temp-deploy
    zip -r ../deployments/${APP_NAME}-${VERSION}.zip .
    cd ..
    rm -rf temp-deploy
fi

# Upload to S3
echo "Uploading deployment package to S3..."
aws s3 cp deployments/${APP_NAME}-${VERSION}.zip s3://my-deployment-bucket/applications/

# Verify deployment group exists
if ! aws deploy get-deployment-group \
    --application-name ${APP_NAME} \
    --deployment-group-name ${ENVIRONMENT}-servers >/dev/null 2>&1; then
    echo "Deployment group ${ENVIRONMENT}-servers does not exist"
    exit 1
fi

# Create deployment
echo "Creating deployment..."
DEPLOYMENT_ID=$(aws deploy create-deployment \
    --application-name ${APP_NAME} \
    --deployment-group-name ${ENVIRONMENT}-servers \
    --deployment-config-name ${DEPLOYMENT_CONFIG} \
    --s3-location bucket=my-deployment-bucket,key=applications/${APP_NAME}-${VERSION}.zip,bundleType=zip \
    --description "Automated deployment of ${APP_NAME} v${VERSION} to ${ENVIRONMENT}" \
    --query 'deploymentId' \
    --output text)

echo "Deployment created: ${DEPLOYMENT_ID}"

# Monitor deployment progress
echo "Monitoring deployment progress..."
while true; do
    STATUS=$(aws deploy get-deployment \
        --deployment-id ${DEPLOYMENT_ID} \
        --query 'deploymentInfo.status' \
        --output text)
    
    echo "Deployment status: ${STATUS}"
    
    case $STATUS in
        "Succeeded")
            echo "Deployment completed successfully!"
            break
            ;;
        "Failed"|"Stopped")
            echo "Deployment failed with status: ${STATUS}"
            
            # Get failure details
            aws deploy get-deployment \
                --deployment-id ${DEPLOYMENT_ID} \
                --query 'deploymentInfo.errorInformation' \
                --output table
            
            exit 1
            ;;
        "Created"|"Queued"|"InProgress")
            sleep 30
            ;;
        *)
            echo "Unknown deployment status: ${STATUS}"
            exit 1
            ;;
    esac
done

# Verify deployment health
echo "Verifying deployment health..."
sleep 60  # Allow time for application to start

# Check application health endpoint
HEALTH_CHECK_URL="http://${APP_NAME}-${ENVIRONMENT}.example.com/health"
if curl -f ${HEALTH_CHECK_URL} >/dev/null 2>&1; then
    echo "Health check passed - deployment verified"
else
    echo "Health check failed - consider rollback"
    
    # Automatic rollback for production
    if [ "$ENVIRONMENT" = "production" ]; then
        echo "Initiating automatic rollback..."
        aws deploy stop-deployment \
            --deployment-id ${DEPLOYMENT_ID} \
            --auto-rollback-enabled
    fi
    
    exit 1
fi

echo "Deployment of ${APP_NAME} v${VERSION} to ${ENVIRONMENT} completed successfully"
```

### Deployment Monitoring and Rollback

```python
# deployment-monitor.py - Monitor deployments and handle rollbacks
import boto3
import json
import time
import sys
from datetime import datetime

def monitor_deployment(deployment_id, auto_rollback=False):
    """Monitor CodeDeploy deployment and handle failures"""
    
    codedeploy = boto3.client('codedeploy')
    cloudwatch = boto3.client('cloudwatch')
    sns = boto3.client('sns')
    
    print(f"Monitoring deployment: {deployment_id}")
    
    start_time = datetime.now()
    
    while True:
        try:
            response = codedeploy.get_deployment(deploymentId=deployment_id)
            deployment_info = response['deploymentInfo']
            
            status = deployment_info['status']
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Status: {status}")
            
            if status == 'Succeeded':
                duration = (datetime.now() - start_time).total_seconds()
                print(f"Deployment completed successfully in {duration:.0f} seconds")
                
                # Send success notification
                send_notification(
                    f"Deployment {deployment_id} completed successfully",
                    "DEPLOYMENT_SUCCESS"
                )
                
                # Record success metric
                record_deployment_metric(deployment_info, 'Success', duration)
                return True
                
            elif status in ['Failed', 'Stopped']:
                error_info = deployment_info.get('errorInformation', {})
                error_code = error_info.get('code', 'Unknown')
                error_message = error_info.get('message', 'No details available')
                
                print(f"Deployment failed: {error_code} - {error_message}")
                
                # Get detailed failure information
                failure_details = get_deployment_failures(codedeploy, deployment_id)
                
                # Send failure notification
                send_notification(
                    f"Deployment {deployment_id} failed: {error_message}\\n\\nDetails:\\n{failure_details}",
                    "DEPLOYMENT_FAILURE"
                )
                
                # Record failure metric
                duration = (datetime.now() - start_time).total_seconds()
                record_deployment_metric(deployment_info, 'Failed', duration)
                
                # Automatic rollback if enabled
                if auto_rollback and status == 'Failed':
                    perform_rollback(codedeploy, deployment_info)
                
                return False
                
            elif status in ['Created', 'Queued', 'InProgress']:
                # Check for stuck deployments
                duration = (datetime.now() - start_time).total_seconds()
                if duration > 3600:  # 1 hour timeout
                    print("Deployment taking too long, stopping...")
                    codedeploy.stop_deployment(
                        deploymentId=deployment_id,
                        autoRollbackEnabled=auto_rollback
                    )
                    return False
                
                time.sleep(30)
            else:
                print(f"Unknown status: {status}")
                time.sleep(30)
                
        except Exception as e:
            print(f"Error monitoring deployment: {e}")
            time.sleep(30)

def get_deployment_failures(codedeploy, deployment_id):
    """Get detailed failure information"""
    
    try:
        instances_response = codedeploy.list_deployment_instances(
            deploymentId=deployment_id
        )
        
        failures = []
        for instance_id in instances_response['instancesList']:
            instance_response = codedeploy.get_deployment_instance(
                deploymentId=deployment_id,
                instanceId=instance_id
            )
            
            instance_summary = instance_response['instanceSummary']
            if instance_summary['status'] == 'Failed':
                failures.append(f"Instance {instance_id}: {instance_summary.get('lastUpdatedAt', 'Unknown time')}")
                
                # Get lifecycle events
                for event in instance_summary.get('lifecycleEvents', []):
                    if event['status'] == 'Failed':
                        failures.append(f"  - {event['lifecycleEventName']}: {event.get('diagnostics', {}).get('message', 'No details')}")
        
        return "\\n".join(failures) if failures else "No detailed failure information available"
        
    except Exception as e:
        return f"Could not retrieve failure details: {e}"

def perform_rollback(codedeploy, deployment_info):
    """Perform automatic rollback"""
    
    app_name = deployment_info['applicationName']
    deployment_group = deployment_info['deploymentGroupName']
    
    print(f"Performing automatic rollback for {app_name}/{deployment_group}")
    
    try:
        # Get previous successful deployment
        deployments_response = codedeploy.list_deployments(
            applicationName=app_name,
            deploymentGroupName=deployment_group,
            includeOnlyStatuses=['Succeeded']
        )
        
        if deployments_response['deployments']:
            previous_deployment_id = deployments_response['deployments'][0]
            
            # Get previous deployment revision
            previous_deployment = codedeploy.get_deployment(
                deploymentId=previous_deployment_id
            )
            
            previous_revision = previous_deployment['deploymentInfo']['revision']
            
            # Create rollback deployment
            rollback_response = codedeploy.create_deployment(
                applicationName=app_name,
                deploymentGroupName=deployment_group,
                revision=previous_revision,
                description=f"Automatic rollback from failed deployment {deployment_info['deploymentId']}"
            )
            
            print(f"Rollback deployment created: {rollback_response['deploymentId']}")
            
            # Monitor rollback
            return monitor_deployment(rollback_response['deploymentId'], auto_rollback=False)
            
        else:
            print("No previous successful deployment found for rollback")
            return False
            
    except Exception as e:
        print(f"Rollback failed: {e}")
        return False

def send_notification(message, event_type):
    """Send notification via SNS"""
    
    try:
        sns = boto3.client('sns')
        
        topic_arn_map = {
            'DEPLOYMENT_SUCCESS': 'arn:aws:sns:us-west-2:123456789012:deployment-success',
            'DEPLOYMENT_FAILURE': 'arn:aws:sns:us-west-2:123456789012:deployment-failure'
        }
        
        topic_arn = topic_arn_map.get(event_type)
        if topic_arn:
            sns.publish(
                TopicArn=topic_arn,
                Message=message,
                Subject=f"CodeDeploy {event_type.replace('_', ' ').title()}"
            )
    except Exception as e:
        print(f"Failed to send notification: {e}")

def record_deployment_metric(deployment_info, status, duration):
    """Record deployment metrics to CloudWatch"""
    
    try:
        cloudwatch = boto3.client('cloudwatch')
        
        cloudwatch.put_metric_data(
            Namespace='CodeDeploy/Deployments',
            MetricData=[
                {
                    'MetricName': 'DeploymentDuration',
                    'Value': duration,
                    'Unit': 'Seconds',
                    'Dimensions': [
                        {
                            'Name': 'ApplicationName',
                            'Value': deployment_info['applicationName']
                        },
                        {
                            'Name': 'DeploymentGroup',
                            'Value': deployment_info['deploymentGroupName']
                        },
                        {
                            'Name': 'Status',
                            'Value': status
                        }
                    ]
                },
                {
                    'MetricName': 'DeploymentCount',
                    'Value': 1,
                    'Unit': 'Count',
                    'Dimensions': [
                        {
                            'Name': 'ApplicationName',
                            'Value': deployment_info['applicationName']
                        },
                        {
                            'Name': 'Status',
                            'Value': status
                        }
                    ]
                }
            ]
        )
    except Exception as e:
        print(f"Failed to record metrics: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python deployment-monitor.py <deployment-id> [auto-rollback]")
        sys.exit(1)
    
    deployment_id = sys.argv[1]
    auto_rollback = len(sys.argv) > 2 and sys.argv[2].lower() == 'true'
    
    success = monitor_deployment(deployment_id, auto_rollback)
    
    if success:
        print("Deployment monitoring completed successfully")
        sys.exit(0)
    else:
        print("Deployment failed or was stopped")
        sys.exit(1)
```

### Blue-Green Deployment Script

```bash
#!/bin/bash
# blue-green-deploy.sh - Advanced blue-green deployment with validation

APP_NAME=$1
ENVIRONMENT=$2
VERSION=$3
VALIDATION_MINUTES=${4:-5}

if [ $# -lt 3 ]; then
    echo "Usage: $0 <app-name> <environment> <version> [validation-minutes]"
    exit 1
fi

DEPLOYMENT_GROUP="${ENVIRONMENT}-servers"
TARGET_GROUP="my-target-group"

echo "Starting blue-green deployment of ${APP_NAME} v${VERSION} to ${ENVIRONMENT}"

# Pre-deployment validation
echo "Running pre-deployment validation..."

# Check if deployment group exists and is healthy
DEPLOYMENT_GROUP_INFO=$(aws deploy get-deployment-group \
    --application-name ${APP_NAME} \
    --deployment-group-name ${DEPLOYMENT_GROUP})

if [ $? -ne 0 ]; then
    echo "Deployment group ${DEPLOYMENT_GROUP} not found"
    exit 1
fi

# Check current instances health
CURRENT_INSTANCES=$(echo "$DEPLOYMENT_GROUP_INFO" | jq -r '.deploymentGroupInfo.ec2TagFilters[] | .Value')
echo "Current instances in deployment group: ${CURRENT_INSTANCES}"

# Verify load balancer health
HEALTHY_TARGETS=$(aws elbv2 describe-target-health \
    --target-group-arn arn:aws:elasticloadbalancing:us-west-2:123456789012:targetgroup/${TARGET_GROUP} \
    --query 'TargetHealthDescriptions[?TargetHealth.State==`healthy`].Target.Id' \
    --output text)

if [ -z "$HEALTHY_TARGETS" ]; then
    echo "No healthy targets in load balancer - aborting deployment"
    exit 1
fi

echo "Healthy targets: ${HEALTHY_TARGETS}"

# Create blue-green deployment
echo "Creating blue-green deployment..."
DEPLOYMENT_ID=$(aws deploy create-deployment \
    --application-name ${APP_NAME} \
    --deployment-group-name ${DEPLOYMENT_GROUP} \
    --deployment-config-name CodeDeployDefault.EC2AllAtOneBlueGreen \
    --s3-location bucket=my-deployment-bucket,key=applications/${APP_NAME}-${VERSION}.zip,bundleType=zip \
    --description "Blue-green deployment of ${APP_NAME} v${VERSION}" \
    --query 'deploymentId' \
    --output text)

if [ $? -ne 0 ]; then
    echo "Failed to create deployment"
    exit 1
fi

echo "Deployment created: ${DEPLOYMENT_ID}"

# Monitor deployment phases
echo "Monitoring deployment phases..."
PHASE="UNKNOWN"
PREV_PHASE=""

while true; do
    DEPLOYMENT_STATUS=$(aws deploy get-deployment --deployment-id ${DEPLOYMENT_ID})
    STATUS=$(echo "$DEPLOYMENT_STATUS" | jq -r '.deploymentInfo.status')
    PHASE=$(echo "$DEPLOYMENT_STATUS" | jq -r '.deploymentInfo.deploymentOverview.Blue // "UNKNOWN"')
    
    if [ "$PHASE" != "$PREV_PHASE" ]; then
        echo "[$(date '+%H:%M:%S')] Phase: ${PHASE}, Status: ${STATUS}"
        PREV_PHASE="$PHASE"
    fi
    
    case $STATUS in
        "InProgress")
            # Check if we're in the validation phase
            if [[ "$PHASE" == *"Green"* ]]; then
                echo "Green environment is ready - starting validation period"
                break
            fi
            ;;
        "Succeeded")
            echo "Deployment completed successfully!"
            exit 0
            ;;
        "Failed"|"Stopped")
            echo "Deployment failed with status: ${STATUS}"
            
            # Get error information
            ERROR_INFO=$(echo "$DEPLOYMENT_STATUS" | jq -r '.deploymentInfo.errorInformation.message // "No error details available"')
            echo "Error: ${ERROR_INFO}"
            exit 1
            ;;
    esac
    
    sleep 30
done

# Enhanced validation phase
echo "Starting enhanced validation phase (${VALIDATION_MINUTES} minutes)..."

# Get green environment details
GREEN_INSTANCES=$(aws deploy list-deployment-instances \
    --deployment-id ${DEPLOYMENT_ID} \
    --instance-status-filter InProgress \
    --query 'instancesList' \
    --output text)

echo "Green environment instances: ${GREEN_INSTANCES}"

# Validate green environment
VALIDATION_PASSED=true
VALIDATION_END_TIME=$(($(date +%s) + VALIDATION_MINUTES * 60))

while [ $(date +%s) -lt $VALIDATION_END_TIME ]; do
    REMAINING_TIME=$(( (VALIDATION_END_TIME - $(date +%s)) / 60 ))
    echo "Validation in progress... ${REMAINING_TIME} minutes remaining"
    
    # Health check validation
    for instance in $GREEN_INSTANCES; do
        # Get instance IP
        INSTANCE_IP=$(aws ec2 describe-instances \
            --instance-ids $instance \
            --query 'Reservations[0].Instances[0].PrivateIpAddress' \
            --output text)
        
        # Test application health
        if ! curl -f --max-time 10 "http://${INSTANCE_IP}:8080/health" >/dev/null 2>&1; then
            echo "Health check failed for instance ${instance} (${INSTANCE_IP})"
            VALIDATION_PASSED=false
            break
        fi
    done
    
    if [ "$VALIDATION_PASSED" = false ]; then
        break
    fi
    
    # Check CloudWatch metrics for errors
    ERROR_COUNT=$(aws cloudwatch get-metric-statistics \
        --namespace "Custom/${APP_NAME}" \
        --metric-name ErrorCount \
        --start-time $(date -d '5 minutes ago' -Iseconds) \
        --end-time $(date -Iseconds) \
        --period 300 \
        --statistics Sum \
        --query 'Datapoints[0].Sum' \
        --output text)
    
    if [ "$ERROR_COUNT" != "None" ] && [ "$ERROR_COUNT" -gt 0 ]; then
        echo "Elevated error count detected: ${ERROR_COUNT}"
        VALIDATION_PASSED=false
        break
    fi
    
    sleep 60
done

# Decision point
if [ "$VALIDATION_PASSED" = true ]; then
    echo "Validation passed - proceeding with traffic switch"
    
    # Allow deployment to continue (it will automatically switch traffic)
    echo "Waiting for automatic traffic switch..."
    
    # Monitor final deployment completion
    while true; do
        STATUS=$(aws deploy get-deployment \
            --deployment-id ${DEPLOYMENT_ID} \
            --query 'deploymentInfo.status' \
            --output text)
        
        case $STATUS in
            "Succeeded")
                echo "Blue-green deployment completed successfully!"
                
                # Final verification
                sleep 30
                if curl -f "http://${APP_NAME}-${ENVIRONMENT}.example.com/health" >/dev/null 2>&1; then
                    echo "Final health check passed"
                    
                    # Send success notification
                    aws sns publish \
                        --topic-arn arn:aws:sns:us-west-2:123456789012:deployment-success \
                        --message "Blue-green deployment of ${APP_NAME} v${VERSION} to ${ENVIRONMENT} completed successfully" \
                        --subject "Deployment Success: ${APP_NAME}"
                    
                    exit 0
                else
                    echo "Final health check failed - consider immediate investigation"
                    exit 1
                fi
                ;;
            "Failed"|"Stopped")
                echo "Deployment failed during final phase"
                exit 1
                ;;
            *)
                sleep 30
                ;;
        esac
    done
else
    echo "Validation failed - stopping deployment and initiating rollback"
    
    # Stop deployment with automatic rollback
    aws deploy stop-deployment \
        --deployment-id ${DEPLOYMENT_ID} \
        --auto-rollback-enabled
    
    # Send failure notification
    aws sns publish \
        --topic-arn arn:aws:sns:us-west-2:123456789012:deployment-failure \
        --message "Blue-green deployment of ${APP_NAME} v${VERSION} to ${ENVIRONMENT} failed validation and was rolled back" \
        --subject "Deployment Failure: ${APP_NAME}"
    
    exit 1
fi
```

## Best Practices

### Deployment Strategy Selection
- **Production environments:** Use blue-green deployments for zero downtime
- **Staging environments:** Use rolling deployments for cost efficiency
- **Critical applications:** Implement canary deployments with extensive monitoring
- **Lambda functions:** Use traffic shifting with CloudWatch alarm integration

### Security and Access Control
- **IAM roles:** Use least privilege principle for CodeDeploy service roles
- **Instance profiles:** Ensure EC2 instances have proper CodeDeploy agent permissions
- **Cross-account deployments:** Use proper role assumption for multi-account strategies
- **Artifact security:** Encrypt deployment artifacts in S3 with KMS

### Monitoring and Observability
- **CloudWatch integration:** Set up alarms for deployment monitoring and automatic rollback
- **Custom metrics:** Implement application-specific health checks during deployment
- **Notification strategy:** Configure SNS topics for deployment status updates
- **Audit logging:** Enable CloudTrail for all CodeDeploy API calls

### Performance Optimization
- **Deployment package size:** Minimize artifact size for faster downloads
- **Parallel deployments:** Use appropriate batch sizes for rolling deployments
- **Health check tuning:** Optimize validation timeouts and retry logic
- **Resource planning:** Ensure sufficient capacity for blue-green deployments