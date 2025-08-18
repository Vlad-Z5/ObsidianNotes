# AWS CloudFormation

> **Service Type:** Infrastructure as Code | **Tier:** Essential DevOps | **Global/Regional:** Regional

## Overview

AWS CloudFormation is a declarative Infrastructure as Code (IaC) service that enables you to model, provision, and manage AWS resources using templates. It provides version control, repeatability, and consistency for infrastructure deployments.

## DevOps Use Cases

### Infrastructure Automation
- **Environment provisioning** for dev/staging/prod environments
- **Multi-region deployments** with consistent configurations
- **Disaster recovery** infrastructure automation
- **Blue-green deployments** with parallel stack creation

### CI/CD Integration
- **Pipeline infrastructure** created alongside application code
- **Automated testing environments** provisioned per commit/PR
- **Application stack updates** triggered by code changes
- **Infrastructure validation** through stack drift detection

### Governance & Compliance
- **Standardized resource configurations** across teams
- **Policy enforcement** through template validation
- **Cost control** with predictable resource definitions
- **Audit trails** for infrastructure changes

### Advanced Patterns
- **Nested stacks** for modular, reusable components
- **Stack sets** for multi-account deployments
- **Custom resources** for extending CloudFormation capabilities
- **Macros and transforms** for template preprocessing

## Core Components

### Templates
- **Language:** Written in **YAML** or **JSON**
- **Sections:** Resources (required), Parameters, Outputs, Mappings, Conditions, Metadata
- **Best Practice:** Use YAML for readability, version control templates

### Stacks
- **Definition:** A deployed instance of a template
- **Features:** 
  - **Nested stacks** for modular design
  - **Change sets** preview changes before update
  - **Stack policies** prevent accidental changes to critical resources
  - **Termination protection** prevents accidental deletion

### Resources
- **Coverage:** EC2, S3, RDS, VPC, IAM, Lambda, and 600+ AWS services
- **Dependencies:** Implicit (Ref, GetAtt) and explicit (DependsOn)
- **Properties:** Service-specific configuration parameters

### Parameters
- **Purpose:** User-defined inputs during deployment
- **Types:** String, Number, List, AWS-specific types (VPC ID, Subnet ID)
- **Validation:** AllowedValues, AllowedPattern, MinLength, MaxLength

### Outputs
- **Purpose:** Export values for cross-stack reference or display
- **Export:** Makes outputs available to other stacks via ImportValue
- **Use Cases:** Shared VPC IDs, security group IDs, endpoint URLs

### Mappings
- **Purpose:** Key-value lookups for static data
- **Common Use:** Region-to-AMI mapping, environment-specific configurations
- **Access:** FindInMap intrinsic function

### Conditions
- **Purpose:** Create resources only if specific conditions are met
- **Logic:** And, Equals, If, Not, Or functions
- **Use Cases:** Environment-specific resources, optional features

## Advanced Features

### Drift Detection
- **Purpose:** Detect changes made outside CloudFormation
- **Process:** Compare current resource state with stack template
- **Actions:** Remediate drift or update template to match reality

### Rollback Triggers
- **Purpose:** Automatically revert stack if deployment fails
- **Monitoring:** CloudWatch alarms trigger rollback
- **Use Cases:** Application health checks, performance thresholds

### Stack Sets
- **Purpose:** Deploy stacks across multiple accounts/regions
- **Management:** Centralized administration from master account
- **Use Cases:** Organizational standards, security baselines

## Template Example Structure

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: 'Web application infrastructure'

Parameters:
  Environment:
    Type: String
    AllowedValues: [dev, staging, prod]
    Default: dev

Mappings:
  EnvironmentMap:
    dev:
      InstanceType: t3.micro
    prod:
      InstanceType: t3.medium

Conditions:
  IsProd: !Equals [!Ref Environment, prod]

Resources:
  WebServerInstance:
    Type: AWS::EC2::Instance
    Properties:
      InstanceType: !FindInMap [EnvironmentMap, !Ref Environment, InstanceType]
      ImageId: ami-0abcdef1234567890

Outputs:
  InstanceId:
    Description: 'Web server instance ID'
    Value: !Ref WebServerInstance
    Export:
      Name: !Sub '${AWS::StackName}-WebServerInstanceId'
```

## Best Practices

### Template Design
- **Modular approach** with nested stacks
- **Parameter validation** to prevent deployment errors
- **Meaningful resource names** with logical IDs
- **Comprehensive outputs** for integration points

### Security
- **IAM roles** with least privilege for CloudFormation
- **Cross-stack references** instead of hardcoded values
- **Secrets in Parameter Store/Secrets Manager** not in templates
- **Stack policies** to protect critical resources

### Operations
- **Change sets** for reviewing updates before applying
- **Tagging strategy** for cost allocation and governance
- **Drift detection** monitoring for compliance
- **Stack deletion policies** for data protection

## Troubleshooting

### Common Issues
- **Insufficient permissions:** CloudFormation needs permissions for all resources it manages
- **Resource limits:** AWS service limits can cause stack creation failures
- **Circular dependencies:** Resources that depend on each other
- **Update conflicts:** Some resource properties can't be updated in-place

### Debugging
- **CloudFormation events** show detailed deployment progress
- **Stack status reasons** provide error context
- **CloudTrail logs** for API-level troubleshooting
- **Resource-level events** for specific failure details

## **Practical CLI Examples**

### **Stack Management**

```bash
# Deploy stack
aws cloudformation deploy \
  --template-file infrastructure.yaml \
  --stack-name my-web-app \
  --parameter-overrides Environment=production InstanceType=t3.medium \
  --capabilities CAPABILITY_IAM \
  --tags Project=WebApp Environment=Production

# Create change set for review
aws cloudformation create-change-set \
  --stack-name my-web-app \
  --template-body file://updated-infrastructure.yaml \
  --change-set-name update-2024-01-15 \
  --parameters ParameterKey=Environment,ParameterValue=production

# Review change set
aws cloudformation describe-change-set \
  --stack-name my-web-app \
  --change-set-name update-2024-01-15

# Execute change set
aws cloudformation execute-change-set \
  --stack-name my-web-app \
  --change-set-name update-2024-01-15

# Monitor stack events
aws cloudformation describe-stack-events \
  --stack-name my-web-app \
  --query 'StackEvents[*].[Timestamp,ResourceStatus,ResourceType,LogicalResourceId]' \
  --output table

# Delete stack
aws cloudformation delete-stack --stack-name my-web-app
```

### **Stack Set Operations**

```bash
# Create stack set
aws cloudformation create-stack-set \
  --stack-set-name security-baseline \
  --template-body file://security-baseline.yaml \
  --capabilities CAPABILITY_IAM \
  --parameters ParameterKey=ComplianceLevel,ParameterValue=SOC2

# Deploy to multiple accounts
aws cloudformation create-stack-instances \
  --stack-set-name security-baseline \
  --accounts 123456789012 123456789013 \
  --regions us-west-2 us-east-1 \
  --parameter-overrides ParameterKey=Environment,ParameterValue=production

# Update stack set
aws cloudformation update-stack-set \
  --stack-set-name security-baseline \
  --template-body file://updated-security-baseline.yaml \
  --operation-preferences MaxConcurrentPercentage=50,FailureTolerancePercentage=10

# Monitor stack set operations
aws cloudformation list-stack-set-operations \
  --stack-set-name security-baseline
```

### **Drift Detection**

```bash
# Detect drift
aws cloudformation detect-stack-drift \
  --stack-name my-web-app

# Get drift results
DRIFT_ID=$(aws cloudformation detect-stack-drift \
  --stack-name my-web-app \
  --query 'StackDriftDetectionId' \
  --output text)

aws cloudformation describe-stack-drift-detection-status \
  --stack-drift-detection-id $DRIFT_ID

# Get resource drift details
aws cloudformation describe-stack-resource-drifts \
  --stack-name my-web-app \
  --query 'StackResourceDrifts[?StackResourceDriftStatus!=`IN_SYNC`]'
```

## **Real-World Templates**

### **VPC with Public/Private Subnets**

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: 'VPC with public and private subnets across 2 AZs'

Parameters:
  EnvironmentName:
    Description: Environment name prefix
    Type: String
    Default: Production
  
  VpcCIDR:
    Description: CIDR block for VPC
    Type: String
    Default: 10.192.0.0/16

Resources:
  VPC:
    Type: AWS::EC2::VPC
    Properties:
      CidrBlock: !Ref VpcCIDR
      EnableDnsHostnames: true
      EnableDnsSupport: true
      Tags:
        - Key: Name
          Value: !Sub ${EnvironmentName}-VPC

  InternetGateway:
    Type: AWS::EC2::InternetGateway
    Properties:
      Tags:
        - Key: Name
          Value: !Sub ${EnvironmentName}-IGW

  InternetGatewayAttachment:
    Type: AWS::EC2::VPCGatewayAttachment
    Properties:
      InternetGatewayId: !Ref InternetGateway
      VpcId: !Ref VPC

  PublicSubnet1:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref VPC
      AvailabilityZone: !Select [0, !GetAZs '']
      CidrBlock: !Sub '10.192.10.0/24'
      MapPublicIpOnLaunch: true
      Tags:
        - Key: Name
          Value: !Sub ${EnvironmentName}-Public-Subnet-AZ1

  PrivateSubnet1:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref VPC
      AvailabilityZone: !Select [0, !GetAZs '']
      CidrBlock: !Sub '10.192.20.0/24'
      Tags:
        - Key: Name
          Value: !Sub ${EnvironmentName}-Private-Subnet-AZ1

  NatGateway1EIP:
    Type: AWS::EC2::EIP
    DependsOn: InternetGatewayAttachment
    Properties:
      Domain: vpc

  NatGateway1:
    Type: AWS::EC2::NatGateway
    Properties:
      AllocationId: !GetAtt NatGateway1EIP.AllocationId
      SubnetId: !Ref PublicSubnet1

  PublicRouteTable:
    Type: AWS::EC2::RouteTable
    Properties:
      VpcId: !Ref VPC
      Tags:
        - Key: Name
          Value: !Sub ${EnvironmentName}-Public-Routes

  DefaultPublicRoute:
    Type: AWS::EC2::Route
    DependsOn: InternetGatewayAttachment
    Properties:
      RouteTableId: !Ref PublicRouteTable
      DestinationCidrBlock: 0.0.0.0/0
      GatewayId: !Ref InternetGateway

  PublicSubnet1RouteTableAssociation:
    Type: AWS::EC2::SubnetRouteTableAssociation
    Properties:
      RouteTableId: !Ref PublicRouteTable
      SubnetId: !Ref PublicSubnet1

Outputs:
  VPC:
    Description: VPC ID
    Value: !Ref VPC
    Export:
      Name: !Sub ${EnvironmentName}-VPCID

  PublicSubnets:
    Description: Public subnet ID
    Value: !Ref PublicSubnet1
    Export:
      Name: !Sub ${EnvironmentName}-PUB-SN

  PrivateSubnets:
    Description: Private subnet ID
    Value: !Ref PrivateSubnet1
    Export:
      Name: !Sub ${EnvironmentName}-PRI-SN
```

### **Auto Scaling Web Application**

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: 'Auto Scaling web application with ALB'

Parameters:
  KeyName:
    Type: AWS::EC2::KeyPair::KeyName
    Description: EC2 Key Pair
  
  VpcId:
    Type: AWS::EC2::VPC::Id
    Description: VPC ID
  
  SubnetIds:
    Type: List<AWS::EC2::Subnet::Id>
    Description: Subnet IDs for ALB and Auto Scaling

Resources:
  WebServerSecurityGroup:
    Type: AWS::EC2::SecurityGroup
    Properties:
      GroupDescription: Security group for web servers
      VpcId: !Ref VpcId
      SecurityGroupIngress:
        - IpProtocol: tcp
          FromPort: 80
          ToPort: 80
          SourceSecurityGroupId: !Ref ALBSecurityGroup
        - IpProtocol: tcp
          FromPort: 22
          ToPort: 22
          CidrIp: 10.0.0.0/8

  ALBSecurityGroup:
    Type: AWS::EC2::SecurityGroup
    Properties:
      GroupDescription: Security group for ALB
      VpcId: !Ref VpcId
      SecurityGroupIngress:
        - IpProtocol: tcp
          FromPort: 80
          ToPort: 80
          CidrIp: 0.0.0.0/0
        - IpProtocol: tcp
          FromPort: 443
          ToPort: 443
          CidrIp: 0.0.0.0/0

  LaunchTemplate:
    Type: AWS::EC2::LaunchTemplate
    Properties:
      LaunchTemplateName: WebServerTemplate
      LaunchTemplateData:
        ImageId: ami-0abcdef1234567890
        InstanceType: t3.micro
        KeyName: !Ref KeyName
        SecurityGroupIds:
          - !Ref WebServerSecurityGroup
        UserData:
          Fn::Base64: !Sub |
            #!/bin/bash
            yum update -y
            yum install -y httpd
            systemctl start httpd
            systemctl enable httpd
            echo "<h1>Hello from $(hostname -f)</h1>" > /var/www/html/index.html

  ApplicationLoadBalancer:
    Type: AWS::ElasticLoadBalancingV2::LoadBalancer
    Properties:
      Scheme: internet-facing
      SecurityGroups:
        - !Ref ALBSecurityGroup
      Subnets: !Ref SubnetIds
      Type: application

  TargetGroup:
    Type: AWS::ElasticLoadBalancingV2::TargetGroup
    Properties:
      Port: 80
      Protocol: HTTP
      VpcId: !Ref VpcId
      HealthCheckPath: /
      HealthCheckProtocol: HTTP

  Listener:
    Type: AWS::ElasticLoadBalancingV2::Listener
    Properties:
      DefaultActions:
        - Type: forward
          TargetGroupArn: !Ref TargetGroup
      LoadBalancerArn: !Ref ApplicationLoadBalancer
      Port: 80
      Protocol: HTTP

  AutoScalingGroup:
    Type: AWS::AutoScaling::AutoScalingGroup
    Properties:
      LaunchTemplate:
        LaunchTemplateId: !Ref LaunchTemplate
        Version: !GetAtt LaunchTemplate.LatestVersionNumber
      MinSize: 2
      MaxSize: 6
      DesiredCapacity: 3
      TargetGroupARNs:
        - !Ref TargetGroup
      VPCZoneIdentifier: !Ref SubnetIds
      HealthCheckType: ELB
      HealthCheckGracePeriod: 300

Outputs:
  LoadBalancerDNS:
    Description: DNS name of the load balancer
    Value: !GetAtt ApplicationLoadBalancer.DNSName
```

## **DevOps Automation Scripts**

### **Stack Deployment Pipeline**

```bash
#!/bin/bash
# deploy-stack.sh - Automated stack deployment with validation

STACK_NAME=$1
TEMPLATE_FILE=$2
ENVIRONMENT=$3

if [ $# -ne 3 ]; then
    echo "Usage: $0 <stack-name> <template-file> <environment>"
    exit 1
fi

# Validate template
echo "Validating CloudFormation template..."
aws cloudformation validate-template --template-body file://$TEMPLATE_FILE

if [ $? -ne 0 ]; then
    echo "Template validation failed!"
    exit 1
fi

# Check if stack exists
if aws cloudformation describe-stacks --stack-name $STACK_NAME >/dev/null 2>&1; then
    echo "Stack exists, creating change set..."
    
    # Create change set
    CHANGESET_NAME="changeset-$(date +%Y%m%d-%H%M%S)"
    aws cloudformation create-change-set \
        --stack-name $STACK_NAME \
        --template-body file://$TEMPLATE_FILE \
        --change-set-name $CHANGESET_NAME \
        --parameters ParameterKey=Environment,ParameterValue=$ENVIRONMENT \
        --capabilities CAPABILITY_IAM
    
    # Wait for change set creation
    aws cloudformation wait change-set-create-complete \
        --stack-name $STACK_NAME \
        --change-set-name $CHANGESET_NAME
    
    # Display changes
    aws cloudformation describe-change-set \
        --stack-name $STACK_NAME \
        --change-set-name $CHANGESET_NAME \
        --query 'Changes[*].[Action,ResourceChange.LogicalResourceId,ResourceChange.ResourceType]' \
        --output table
    
    # Confirm execution
    read -p "Execute change set? (y/n): " confirm
    if [ "$confirm" = "y" ]; then
        aws cloudformation execute-change-set \
            --stack-name $STACK_NAME \
            --change-set-name $CHANGESET_NAME
        
        aws cloudformation wait stack-update-complete --stack-name $STACK_NAME
        echo "Stack update completed successfully!"
    fi
else
    echo "Creating new stack..."
    aws cloudformation create-stack \
        --stack-name $STACK_NAME \
        --template-body file://$TEMPLATE_FILE \
        --parameters ParameterKey=Environment,ParameterValue=$ENVIRONMENT \
        --capabilities CAPABILITY_IAM
    
    aws cloudformation wait stack-create-complete --stack-name $STACK_NAME
    echo "Stack creation completed successfully!"
fi
```

### **Stack Monitoring Script**

```bash
#!/bin/bash
# monitor-stacks.sh - Monitor CloudFormation stack health

# Get all stacks
STACKS=$(aws cloudformation list-stacks \
    --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE \
    --query 'StackSummaries[*].StackName' \
    --output text)

for stack in $STACKS; do
    echo "Checking stack: $stack"
    
    # Check for drift
    DRIFT_ID=$(aws cloudformation detect-stack-drift \
        --stack-name $stack \
        --query 'StackDriftDetectionId' \
        --output text)
    
    # Wait for drift detection
    aws cloudformation wait \
        --stack-drift-detection-id $DRIFT_ID
    
    # Check results
    DRIFT_STATUS=$(aws cloudformation describe-stack-drift-detection-status \
        --stack-drift-detection-id $DRIFT_ID \
        --query 'StackDriftStatus' \
        --output text)
    
    if [ "$DRIFT_STATUS" != "IN_SYNC" ]; then
        echo "WARNING: Stack $stack has drift status: $DRIFT_STATUS"
        
        # Send alert
        aws sns publish \
            --topic-arn arn:aws:sns:us-west-2:123456789012:cloudformation-alerts \
            --message "CloudFormation stack $stack has configuration drift: $DRIFT_STATUS"
    fi
done
```
