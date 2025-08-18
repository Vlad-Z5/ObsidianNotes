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

## Advanced CloudFormation Patterns

### Enterprise-Grade Infrastructure Templates

#### Multi-Tier Application Stack with Auto Scaling
```yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: 'Enterprise multi-tier application with advanced features'

Parameters:
  Environment:
    Type: String
    AllowedValues: [dev, staging, prod]
    Default: dev
    Description: Target environment for deployment
  
  DatabasePassword:
    Type: String
    NoEcho: true
    MinLength: 8
    Description: Master password for RDS database
    ConstraintDescription: Must be at least 8 characters
  
  ApplicationVersion:
    Type: String
    Default: 'latest'
    Description: Application version to deploy
    
  EnableMultiAZ:
    Type: String
    Default: 'false'
    AllowedValues: ['true', 'false']
    Description: Enable Multi-AZ deployment for production

Mappings:
  EnvironmentMap:
    dev:
      InstanceType: t3.micro
      MinCapacity: 1
      MaxCapacity: 3
      DBInstanceClass: db.t3.micro
      DBAllocatedStorage: 20
    staging:
      InstanceType: t3.small
      MinCapacity: 2
      MaxCapacity: 6
      DBInstanceClass: db.t3.small
      DBAllocatedStorage: 50
    prod:
      InstanceType: m5.large
      MinCapacity: 3
      MaxCapacity: 12
      DBInstanceClass: db.r5.large
      DBAllocatedStorage: 100

Conditions:
  IsProduction: !Equals [!Ref Environment, 'prod']
  EnableBackups: !Or [!Equals [!Ref Environment, 'staging'], !Condition IsProduction]
  EnableEncryption: !Condition IsProduction

Resources:
  # VPC and Networking (Reference: Use modular approach)
  VPCStack:
    Type: AWS::CloudFormation::Stack
    Properties:
      TemplateURL: https://s3.amazonaws.com/cloudformation-templates/vpc-template.yaml
      Parameters:
        EnvironmentName: !Ref Environment
        VpcCIDR: !If 
          - IsProduction
          - '10.0.0.0/16'
          - '10.192.0.0/16'

  # Application Load Balancer Security Group
  ALBSecurityGroup:
    Type: AWS::EC2::SecurityGroup
    Properties:
      GroupDescription: Security group for Application Load Balancer
      VpcId: !GetAtt VPCStack.Outputs.VPC
      SecurityGroupIngress:
        - IpProtocol: tcp
          FromPort: 80
          ToPort: 80
          CidrIp: 0.0.0.0/0
          Description: HTTP traffic from internet
        - IpProtocol: tcp
          FromPort: 443
          ToPort: 443
          CidrIp: 0.0.0.0/0
          Description: HTTPS traffic from internet
      SecurityGroupEgress:
        - IpProtocol: -1
          CidrIp: 0.0.0.0/0
          Description: All outbound traffic
      Tags:
        - Key: Name
          Value: !Sub '${Environment}-ALB-SecurityGroup'
        - Key: Environment
          Value: !Ref Environment

  # Web Server Security Group
  WebServerSecurityGroup:
    Type: AWS::EC2::SecurityGroup
    Properties:
      GroupDescription: Security group for web servers
      VpcId: !GetAtt VPCStack.Outputs.VPC
      SecurityGroupIngress:
        - IpProtocol: tcp
          FromPort: 80
          ToPort: 80
          SourceSecurityGroupId: !Ref ALBSecurityGroup
          Description: HTTP from ALB
        - IpProtocol: tcp
          FromPort: 443
          ToPort: 443
          SourceSecurityGroupId: !Ref ALBSecurityGroup
          Description: HTTPS from ALB
        - IpProtocol: tcp
          FromPort: 22
          ToPort: 22
          SourceSecurityGroupId: !Ref BastionSecurityGroup
          Description: SSH from bastion host
      Tags:
        - Key: Name
          Value: !Sub '${Environment}-WebServer-SecurityGroup'

  # Database Security Group
  DatabaseSecurityGroup:
    Type: AWS::EC2::SecurityGroup
    Properties:
      GroupDescription: Security group for RDS database
      VpcId: !GetAtt VPCStack.Outputs.VPC
      SecurityGroupIngress:
        - IpProtocol: tcp
          FromPort: 3306
          ToPort: 3306
          SourceSecurityGroupId: !Ref WebServerSecurityGroup
          Description: MySQL from web servers
      Tags:
        - Key: Name
          Value: !Sub '${Environment}-Database-SecurityGroup'

  # Bastion Host Security Group
  BastionSecurityGroup:
    Type: AWS::EC2::SecurityGroup
    Properties:
      GroupDescription: Security group for bastion host
      VpcId: !GetAtt VPCStack.Outputs.VPC
      SecurityGroupIngress:
        - IpProtocol: tcp
          FromPort: 22
          ToPort: 22
          CidrIp: 0.0.0.0/0  # Restrict this to your IP in production
          Description: SSH access for administration
      Tags:
        - Key: Name
          Value: !Sub '${Environment}-Bastion-SecurityGroup'

  # IAM Role for EC2 Instances
  EC2InstanceRole:
    Type: AWS::IAM::Role
    Properties:
      AssumeRolePolicyDocument:
        Version: '2012-10-17'
        Statement:
          - Effect: Allow
            Principal:
              Service: ec2.amazonaws.com
            Action: sts:AssumeRole
      ManagedPolicyArns:
        - arn:aws:iam::aws:policy/CloudWatchAgentServerPolicy
        - arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore
      Policies:
        - PolicyName: ApplicationAccess
          PolicyDocument:
            Version: '2012-10-17'
            Statement:
              - Effect: Allow
                Action:
                  - s3:GetObject
                  - s3:PutObject
                Resource: !Sub '${ApplicationBucket}/*'
              - Effect: Allow
                Action:
                  - secretsmanager:GetSecretValue
                Resource: !Ref DatabaseSecret
      Tags:
        - Key: Environment
          Value: !Ref Environment

  EC2InstanceProfile:
    Type: AWS::IAM::InstanceProfile
    Properties:
      Roles:
        - !Ref EC2InstanceRole

  # Database Secret in AWS Secrets Manager
  DatabaseSecret:
    Type: AWS::SecretsManager::Secret
    Properties:
      Name: !Sub '${Environment}/database/credentials'
      Description: Database credentials for application
      GenerateSecretString:
        SecretStringTemplate: '{"username": "admin"}'
        GenerateStringKey: password
        PasswordLength: 16
        ExcludeCharacters: '"@/\'
      Tags:
        - Key: Environment
          Value: !Ref Environment

  # RDS Subnet Group
  DatabaseSubnetGroup:
    Type: AWS::RDS::DBSubnetGroup
    Properties:
      DBSubnetGroupDescription: Subnet group for RDS database
      SubnetIds:
        - !GetAtt VPCStack.Outputs.PrivateSubnet1
        - !GetAtt VPCStack.Outputs.PrivateSubnet2
      Tags:
        - Key: Name
          Value: !Sub '${Environment}-database-subnet-group'

  # RDS Database Instance
  DatabaseInstance:
    Type: AWS::RDS::DBInstance
    DeletionPolicy: !If [IsProduction, 'Snapshot', 'Delete']
    Properties:
      DBInstanceIdentifier: !Sub '${Environment}-application-db'
      DBInstanceClass: !FindInMap [EnvironmentMap, !Ref Environment, DBInstanceClass]
      Engine: mysql
      EngineVersion: '8.0.35'
      MasterUsername: !Sub '{{resolve:secretsmanager:${DatabaseSecret}:SecretString:username}}'
      MasterUserPassword: !Sub '{{resolve:secretsmanager:${DatabaseSecret}:SecretString:password}}'
      AllocatedStorage: !FindInMap [EnvironmentMap, !Ref Environment, DBAllocatedStorage]
      StorageType: gp3
      StorageEncrypted: !If [EnableEncryption, true, false]
      VPCSecurityGroups:
        - !Ref DatabaseSecurityGroup
      DBSubnetGroupName: !Ref DatabaseSubnetGroup
      BackupRetentionPeriod: !If [EnableBackups, 7, 0]
      MultiAZ: !If [IsProduction, true, false]
      DeletionProtection: !If [IsProduction, true, false]
      EnablePerformanceInsights: !If [IsProduction, true, false]
      PerformanceInsightsRetentionPeriod: !If [IsProduction, 7, !Ref 'AWS::NoValue']
      MonitoringInterval: !If [IsProduction, 60, 0]
      MonitoringRoleArn: !If 
        - IsProduction
        - !GetAtt RDSEnhancedMonitoringRole.Arn
        - !Ref 'AWS::NoValue'
      Tags:
        - Key: Name
          Value: !Sub '${Environment}-application-database'
        - Key: Environment
          Value: !Ref Environment

  # RDS Enhanced Monitoring Role (Production only)
  RDSEnhancedMonitoringRole:
    Type: AWS::IAM::Role
    Condition: IsProduction
    Properties:
      AssumeRolePolicyDocument:
        Version: '2012-10-17'
        Statement:
          - Effect: Allow
            Principal:
              Service: monitoring.rds.amazonaws.com
            Action: sts:AssumeRole
      ManagedPolicyArns:
        - arn:aws:iam::aws:policy/service-role/AmazonRDSEnhancedMonitoringRole

  # S3 Bucket for Application Assets
  ApplicationBucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: !Sub '${Environment}-application-assets-${AWS::AccountId}'
      BucketEncryption:
        ServerSideEncryptionConfiguration:
          - ServerSideEncryptionByDefault:
              SSEAlgorithm: AES256
      VersioningConfiguration:
        Status: !If [IsProduction, 'Enabled', 'Suspended']
      LifecycleConfiguration:
        Rules:
          - Id: DeleteOldVersions
            Status: Enabled
            NoncurrentVersionExpirationInDays: 30
          - Id: ArchiveOldObjects
            Status: Enabled
            TransitionInDays: 30
            StorageClass: STANDARD_IA
      PublicAccessBlockConfiguration:
        BlockPublicAcls: true
        BlockPublicPolicy: true
        IgnorePublicAcls: true
        RestrictPublicBuckets: true
      NotificationConfiguration:
        CloudWatchConfigurations:
          - Event: s3:ObjectCreated:*
            CloudWatchConfiguration:
              LogGroupName: !Ref ApplicationLogGroup
      Tags:
        - Key: Environment
          Value: !Ref Environment

  # CloudWatch Log Group
  ApplicationLogGroup:
    Type: AWS::Logs::LogGroup
    Properties:
      LogGroupName: !Sub '/aws/application/${Environment}'
      RetentionInDays: !If [IsProduction, 30, 7]

  # Launch Template for EC2 Instances
  LaunchTemplate:
    Type: AWS::EC2::LaunchTemplate
    Properties:
      LaunchTemplateName: !Sub '${Environment}-web-server-template'
      LaunchTemplateData:
        ImageId: ami-0abcdef1234567890  # Update with latest AMI
        InstanceType: !FindInMap [EnvironmentMap, !Ref Environment, InstanceType]
        IamInstanceProfile:
          Arn: !GetAtt EC2InstanceProfile.Arn
        SecurityGroupIds:
          - !Ref WebServerSecurityGroup
        UserData:
          Fn::Base64: !Sub |
            #!/bin/bash
            yum update -y
            yum install -y httpd mysql-client cloudwatch-agent
            
            # Install application
            cd /var/www/html
            aws s3 cp s3://${ApplicationBucket}/app-${ApplicationVersion}.zip .
            unzip app-${ApplicationVersion}.zip
            
            # Configure CloudWatch agent
            cat > /opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json << 'EOF'
            {
              "logs": {
                "logs_collected": {
                  "files": {
                    "collect_list": [
                      {
                        "file_path": "/var/log/httpd/access_log",
                        "log_group_name": "${ApplicationLogGroup}",
                        "log_stream_name": "{instance_id}/httpd/access"
                      }
                    ]
                  }
                }
              },
              "metrics": {
                "namespace": "CWAgent",
                "metrics_collected": {
                  "cpu": {
                    "measurement": ["cpu_usage_idle", "cpu_usage_iowait", "cpu_usage_user", "cpu_usage_system"],
                    "metrics_collection_interval": 60
                  },
                  "disk": {
                    "measurement": ["used_percent"],
                    "metrics_collection_interval": 60,
                    "resources": ["*"]
                  },
                  "mem": {
                    "measurement": ["mem_used_percent"],
                    "metrics_collection_interval": 60
                  }
                }
              }
            }
            EOF
            
            # Start services
            systemctl start httpd
            systemctl enable httpd
            /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl -a fetch-config -m ec2 -c file:/opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json -s
        TagSpecifications:
          - ResourceType: instance
            Tags:
              - Key: Name
                Value: !Sub '${Environment}-web-server'
              - Key: Environment
                Value: !Ref Environment
              - Key: Application
                Value: WebApplication

  # Application Load Balancer
  ApplicationLoadBalancer:
    Type: AWS::ElasticLoadBalancingV2::LoadBalancer
    Properties:
      Name: !Sub '${Environment}-application-alb'
      Type: application
      Scheme: internet-facing
      SecurityGroups:
        - !Ref ALBSecurityGroup
      Subnets:
        - !GetAtt VPCStack.Outputs.PublicSubnet1
        - !GetAtt VPCStack.Outputs.PublicSubnet2
      LoadBalancerAttributes:
        - Key: idle_timeout.timeout_seconds
          Value: '60'
        - Key: access_logs.s3.enabled
          Value: !If [IsProduction, 'true', 'false']
        - Key: access_logs.s3.bucket
          Value: !If [IsProduction, !Ref ALBLogsBucket, !Ref 'AWS::NoValue']
      Tags:
        - Key: Name
          Value: !Sub '${Environment}-application-alb'
        - Key: Environment
          Value: !Ref Environment

  # Target Group for Auto Scaling Group
  TargetGroup:
    Type: AWS::ElasticLoadBalancingV2::TargetGroup
    Properties:
      Name: !Sub '${Environment}-web-servers'
      Port: 80
      Protocol: HTTP
      VpcId: !GetAtt VPCStack.Outputs.VPC
      HealthCheckPath: /health
      HealthCheckProtocol: HTTP
      HealthCheckIntervalSeconds: 30
      HealthCheckTimeoutSeconds: 5
      HealthyThresholdCount: 2
      UnhealthyThresholdCount: 3
      TargetGroupAttributes:
        - Key: deregistration_delay.timeout_seconds
          Value: '300'
        - Key: stickiness.enabled
          Value: 'true'
        - Key: stickiness.type
          Value: lb_cookie
        - Key: stickiness.lb_cookie.duration_seconds
          Value: '86400'
      Tags:
        - Key: Environment
          Value: !Ref Environment

  # ALB Listener
  ALBListener:
    Type: AWS::ElasticLoadBalancingV2::Listener
    Properties:
      DefaultActions:
        - Type: forward
          TargetGroupArn: !Ref TargetGroup
      LoadBalancerArn: !Ref ApplicationLoadBalancer
      Port: 80
      Protocol: HTTP

  # Auto Scaling Group
  AutoScalingGroup:
    Type: AWS::AutoScaling::AutoScalingGroup
    Properties:
      AutoScalingGroupName: !Sub '${Environment}-web-servers-asg'
      LaunchTemplate:
        LaunchTemplateId: !Ref LaunchTemplate
        Version: !GetAtt LaunchTemplate.LatestVersionNumber
      MinSize: !FindInMap [EnvironmentMap, !Ref Environment, MinCapacity]
      MaxSize: !FindInMap [EnvironmentMap, !Ref Environment, MaxCapacity]
      DesiredCapacity: !FindInMap [EnvironmentMap, !Ref Environment, MinCapacity]
      VPCZoneIdentifier:
        - !GetAtt VPCStack.Outputs.PrivateSubnet1
        - !GetAtt VPCStack.Outputs.PrivateSubnet2
      TargetGroupARNs:
        - !Ref TargetGroup
      HealthCheckType: ELB
      HealthCheckGracePeriod: 300
      DefaultCooldown: 300
      Tags:
        - Key: Name
          Value: !Sub '${Environment}-web-server'
          PropagateAtLaunch: true
        - Key: Environment
          Value: !Ref Environment
          PropagateAtLaunch: true
    UpdatePolicy:
      AutoScalingRollingUpdate:
        MinInstancesInService: 1
        MaxBatchSize: 2
        PauseTime: PT5M
        WaitOnResourceSignals: false

  # Auto Scaling Policies
  ScaleUpPolicy:
    Type: AWS::AutoScaling::ScalingPolicy
    Properties:
      AdjustmentType: ChangeInCapacity
      AutoScalingGroupName: !Ref AutoScalingGroup
      Cooldown: 300
      ScalingAdjustment: 2
      PolicyType: SimpleScaling

  ScaleDownPolicy:
    Type: AWS::AutoScaling::ScalingPolicy
    Properties:
      AdjustmentType: ChangeInCapacity
      AutoScalingGroupName: !Ref AutoScalingGroup
      Cooldown: 300
      ScalingAdjustment: -1
      PolicyType: SimpleScaling

  # CloudWatch Alarms
  HighCPUAlarm:
    Type: AWS::CloudWatch::Alarm
    Properties:
      AlarmName: !Sub '${Environment}-HighCPU'
      AlarmDescription: Alarm when CPU exceeds 70%
      MetricName: CPUUtilization
      Namespace: AWS/EC2
      Statistic: Average
      Period: 300
      EvaluationPeriods: 2
      Threshold: 70
      ComparisonOperator: GreaterThanThreshold
      Dimensions:
        - Name: AutoScalingGroupName
          Value: !Ref AutoScalingGroup
      AlarmActions:
        - !Ref ScaleUpPolicy
        - !Ref SNSTopic

  LowCPUAlarm:
    Type: AWS::CloudWatch::Alarm
    Properties:
      AlarmName: !Sub '${Environment}-LowCPU'
      AlarmDescription: Alarm when CPU falls below 30%
      MetricName: CPUUtilization
      Namespace: AWS/EC2
      Statistic: Average
      Period: 300
      EvaluationPeriods: 2
      Threshold: 30
      ComparisonOperator: LessThanThreshold
      Dimensions:
        - Name: AutoScalingGroupName
          Value: !Ref AutoScalingGroup
      AlarmActions:
        - !Ref ScaleDownPolicy

  # SNS Topic for Notifications
  SNSTopic:
    Type: AWS::SNS::Topic
    Properties:
      TopicName: !Sub '${Environment}-application-alerts'
      DisplayName: !Sub '${Environment} Application Alerts'

  # ALB Access Logs Bucket (Production only)
  ALBLogsBucket:
    Type: AWS::S3::Bucket
    Condition: IsProduction
    Properties:
      BucketName: !Sub '${Environment}-alb-logs-${AWS::AccountId}'
      LifecycleConfiguration:
        Rules:
          - Id: DeleteOldLogs
            Status: Enabled
            ExpirationInDays: 30
      PublicAccessBlockConfiguration:
        BlockPublicAcls: true
        BlockPublicPolicy: true
        IgnorePublicAcls: true
        RestrictPublicBuckets: true

  # CloudWatch Dashboard
  ApplicationDashboard:
    Type: AWS::CloudWatch::Dashboard
    Properties:
      DashboardName: !Sub '${Environment}-Application-Dashboard'
      DashboardBody: !Sub |
        {
          "widgets": [
            {
              "type": "metric",
              "x": 0, "y": 0,
              "width": 12, "height": 6,
              "properties": {
                "metrics": [
                  ["AWS/ApplicationELB", "RequestCount", "LoadBalancer", "${ApplicationLoadBalancer}"],
                  [".", "TargetResponseTime", ".", "."],
                  [".", "HTTPCode_Target_2XX_Count", ".", "."],
                  [".", "HTTPCode_Target_4XX_Count", ".", "."],
                  [".", "HTTPCode_Target_5XX_Count", ".", "."]
                ],
                "period": 300,
                "stat": "Sum",
                "region": "${AWS::Region}",
                "title": "Application Load Balancer Metrics"
              }
            },
            {
              "type": "metric",
              "x": 12, "y": 0,
              "width": 12, "height": 6,
              "properties": {
                "metrics": [
                  ["AWS/EC2", "CPUUtilization", "AutoScalingGroupName", "${AutoScalingGroup}"],
                  ["AWS/AutoScaling", "GroupDesiredCapacity", "AutoScalingGroupName", "."],
                  [".", "GroupInServiceInstances", ".", "."]
                ],
                "period": 300,
                "stat": "Average",
                "region": "${AWS::Region}",
                "title": "Auto Scaling Group Metrics"
              }
            },
            {
              "type": "metric",
              "x": 0, "y": 6,
              "width": 24, "height": 6,
              "properties": {
                "metrics": [
                  ["AWS/RDS", "CPUUtilization", "DBInstanceIdentifier", "${DatabaseInstance}"],
                  [".", "DatabaseConnections", ".", "."],
                  [".", "ReadLatency", ".", "."],
                  [".", "WriteLatency", ".", "."]
                ],
                "period": 300,
                "stat": "Average",
                "region": "${AWS::Region}",
                "title": "RDS Database Metrics"
              }
            }
          ]
        }

Outputs:
  LoadBalancerDNS:
    Description: DNS name of the Application Load Balancer
    Value: !GetAtt ApplicationLoadBalancer.DNSName
    Export:
      Name: !Sub '${Environment}-ALB-DNS'

  DatabaseEndpoint:
    Description: RDS Database endpoint
    Value: !GetAtt DatabaseInstance.Endpoint.Address
    Export:
      Name: !Sub '${Environment}-DB-Endpoint'

  ApplicationBucketName:
    Description: S3 bucket for application assets
    Value: !Ref ApplicationBucket
    Export:
      Name: !Sub '${Environment}-App-Bucket'

  AutoScalingGroupName:
    Description: Auto Scaling Group name
    Value: !Ref AutoScalingGroup
    Export:
      Name: !Sub '${Environment}-ASG-Name'

  DatabaseSecretArn:
    Description: ARN of the database credentials secret
    Value: !Ref DatabaseSecret
    Export:
      Name: !Sub '${Environment}-DB-Secret-ARN'
```

### CloudFormation Custom Resources and Advanced Patterns

#### Custom Resource for Dynamic Configuration
```yaml
# Custom resource for external API integration
CustomConfigurationResource:
  Type: AWS::CloudFormation::CustomResource
  Properties:
    ServiceToken: !GetAtt CustomResourceFunction.Arn
    Environment: !Ref Environment
    ConfigurationEndpoint: !Sub 'https://api.example.com/config/${Environment}'
    
CustomResourceFunction:
  Type: AWS::Lambda::Function
  Properties:
    FunctionName: !Sub '${Environment}-custom-config-resource'
    Runtime: python3.9
    Handler: index.lambda_handler
    Role: !GetAtt CustomResourceRole.Arn
    Timeout: 300
    Code:
      ZipFile: |
        import json
        import boto3
        import urllib3
        import cfnresponse
        
        def lambda_handler(event, context):
            print(f"Event: {json.dumps(event)}")
            
            try:
                if event['RequestType'] == 'Create' or event['RequestType'] == 'Update':
                    # Fetch configuration from external API
                    http = urllib3.PoolManager()
                    response = http.request('GET', event['ResourceProperties']['ConfigurationEndpoint'])
                    
                    config_data = json.loads(response.data.decode('utf-8'))
                    
                    # Store configuration in Parameter Store
                    ssm = boto3.client('ssm')
                    ssm.put_parameter(
                        Name=f"/app/{event['ResourceProperties']['Environment']}/config",
                        Value=json.dumps(config_data),
                        Type='String',
                        Overwrite=True
                    )
                    
                    # Return configuration as attributes
                    cfnresponse.send(event, context, cfnresponse.SUCCESS, config_data)
                    
                elif event['RequestType'] == 'Delete':
                    # Clean up parameter
                    ssm = boto3.client('ssm')
                    try:
                        ssm.delete_parameter(
                            Name=f"/app/{event['ResourceProperties']['Environment']}/config"
                        )
                    except ssm.exceptions.ParameterNotFound:
                        pass
                    
                    cfnresponse.send(event, context, cfnresponse.SUCCESS, {})
                    
            except Exception as e:
                print(f"Error: {str(e)}")
                cfnresponse.send(event, context, cfnresponse.FAILED, {})

CustomResourceRole:
  Type: AWS::IAM::Role
  Properties:
    AssumeRolePolicyDocument:
      Version: '2012-10-17'
      Statement:
        - Effect: Allow
          Principal:
            Service: lambda.amazonaws.com
          Action: sts:AssumeRole
    ManagedPolicyArns:
      - arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
    Policies:
      - PolicyName: SSMAccess
        PolicyDocument:
          Version: '2012-10-17'
          Statement:
            - Effect: Allow
              Action:
                - ssm:PutParameter
                - ssm:DeleteParameter
                - ssm:GetParameter
              Resource: !Sub 'arn:aws:ssm:${AWS::Region}:${AWS::AccountId}:parameter/app/*'
```

### Infrastructure as Code Best Practices Implementation

#### Template Organization and Modularity
```yaml
# Master template using nested stacks
AWSTemplateFormatVersion: '2010-09-09'
Description: 'Master template for enterprise application infrastructure'

Parameters:
  Environment:
    Type: String
    AllowedValues: [dev, staging, prod]
  
  TemplateBucketName:
    Type: String
    Description: S3 bucket containing nested templates

Resources:
  # Networking Stack
  NetworkingStack:
    Type: AWS::CloudFormation::Stack
    Properties:
      TemplateURL: !Sub 'https://${TemplateBucketName}.s3.amazonaws.com/networking.yaml'
      Parameters:
        Environment: !Ref Environment
        
  # Security Stack
  SecurityStack:
    Type: AWS::CloudFormation::Stack
    DependsOn: NetworkingStack
    Properties:
      TemplateURL: !Sub 'https://${TemplateBucketName}.s3.amazonaws.com/security.yaml'
      Parameters:
        Environment: !Ref Environment
        VpcId: !GetAtt NetworkingStack.Outputs.VpcId
        
  # Application Stack
  ApplicationStack:
    Type: AWS::CloudFormation::Stack
    DependsOn: 
      - NetworkingStack
      - SecurityStack
    Properties:
      TemplateURL: !Sub 'https://${TemplateBucketName}.s3.amazonaws.com/application.yaml'
      Parameters:
        Environment: !Ref Environment
        VpcId: !GetAtt NetworkingStack.Outputs.VpcId
        DatabaseSubnetGroupName: !GetAtt NetworkingStack.Outputs.DatabaseSubnetGroup
        WebServerSecurityGroupId: !GetAtt SecurityStack.Outputs.WebServerSecurityGroup
        DatabaseSecurityGroupId: !GetAtt SecurityStack.Outputs.DatabaseSecurityGroup
        
  # Monitoring Stack
  MonitoringStack:
    Type: AWS::CloudFormation::Stack
    DependsOn: ApplicationStack
    Properties:
      TemplateURL: !Sub 'https://${TemplateBucketName}.s3.amazonaws.com/monitoring.yaml'
      Parameters:
        Environment: !Ref Environment
        ApplicationLoadBalancerFullName: !GetAtt ApplicationStack.Outputs.LoadBalancerFullName
        AutoScalingGroupName: !GetAtt ApplicationStack.Outputs.AutoScalingGroupName
        DatabaseInstanceId: !GetAtt ApplicationStack.Outputs.DatabaseInstanceId

Outputs:
  ApplicationEndpoint:
    Description: Application endpoint URL
    Value: !Sub 
      - 'http://${LoadBalancerDNS}'
      - LoadBalancerDNS: !GetAtt ApplicationStack.Outputs.LoadBalancerDNS
    Export:
      Name: !Sub '${Environment}-ApplicationEndpoint'
```

### Advanced DevOps Automation with CloudFormation

#### CI/CD Pipeline Integration with Blue-Green Deployments
```python
#!/usr/bin/env python3
"""
Advanced CloudFormation deployment script with blue-green pattern
"""
import boto3
import json
import time
import sys
from datetime import datetime

class BlueGreenDeployment:
    def __init__(self, environment, region='us-west-2'):
        self.environment = environment
        self.region = region
        self.cfn = boto3.client('cloudformation', region_name=region)
        self.elb = boto3.client('elbv2', region_name=region)
        
    def deploy_stack(self, template_url, parameters, timeout_minutes=30):
        """
        Deploy stack with blue-green pattern
        """
        timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
        
        # Determine current and new stack names
        blue_stack = f"{self.environment}-blue"
        green_stack = f"{self.environment}-green"
        
        # Check which stack is currently active
        current_stack, new_stack = self._determine_stacks(blue_stack, green_stack)
        
        print(f"Deploying to {new_stack} stack...")
        
        # Deploy new stack
        self._deploy_new_stack(new_stack, template_url, parameters)
        
        # Wait for deployment completion
        self._wait_for_stack_completion(new_stack, timeout_minutes)
        
        # Perform health checks
        if self._health_check_stack(new_stack):
            print("Health checks passed. Switching traffic...")
            self._switch_traffic(current_stack, new_stack)
            
            # Wait before cleanup
            time.sleep(300)  # 5 minutes
            
            # Cleanup old stack
            if current_stack:
                self._cleanup_old_stack(current_stack)
                
            print(f"Blue-green deployment completed successfully!")
            return True
        else:
            print("Health checks failed. Rolling back...")
            self._cleanup_old_stack(new_stack)
            return False
    
    def _determine_stacks(self, blue_stack, green_stack):
        """Determine which stack is active and which to deploy to"""
        try:
            blue_response = self.cfn.describe_stacks(StackName=blue_stack)
            blue_status = blue_response['Stacks'][0]['StackStatus']
        except:
            blue_status = None
            
        try:
            green_response = self.cfn.describe_stacks(StackName=green_stack)
            green_status = green_response['Stacks'][0]['StackStatus']
        except:
            green_status = None
        
        # Determine active stack
        if blue_status in ['CREATE_COMPLETE', 'UPDATE_COMPLETE']:
            return blue_stack, green_stack
        elif green_status in ['CREATE_COMPLETE', 'UPDATE_COMPLETE']:
            return green_stack, blue_stack
        else:
            return None, blue_stack
    
    def _deploy_new_stack(self, stack_name, template_url, parameters):
        """Deploy new stack version"""
        try:
            response = self.cfn.create_stack(
                StackName=stack_name,
                TemplateURL=template_url,
                Parameters=parameters,
                Capabilities=['CAPABILITY_IAM', 'CAPABILITY_NAMED_IAM'],
                OnFailure='ROLLBACK',
                EnableTerminationProtection=True,
                Tags=[
                    {'Key': 'Environment', 'Value': self.environment},
                    {'Key': 'DeploymentType', 'Value': 'BlueGreen'},
                    {'Key': 'DeploymentTime', 'Value': datetime.now().isoformat()}
                ]
            )
            print(f"Stack creation initiated: {response['StackId']}")
        except self.cfn.exceptions.AlreadyExistsException:
            # Update existing stack
            response = self.cfn.update_stack(
                StackName=stack_name,
                TemplateURL=template_url,
                Parameters=parameters,
                Capabilities=['CAPABILITY_IAM', 'CAPABILITY_NAMED_IAM']
            )
            print(f"Stack update initiated: {response['StackId']}")
    
    def _wait_for_stack_completion(self, stack_name, timeout_minutes):
        """Wait for stack deployment to complete"""
        print(f"Waiting for {stack_name} deployment...")
        
        waiter = self.cfn.get_waiter('stack_create_complete')
        try:
            waiter.wait(
                StackName=stack_name,
                WaiterConfig={'MaxAttempts': timeout_minutes, 'Delay': 60}
            )
        except:
            # Try update waiter if create waiter fails
            waiter = self.cfn.get_waiter('stack_update_complete')
            waiter.wait(
                StackName=stack_name,
                WaiterConfig={'MaxAttempts': timeout_minutes, 'Delay': 60}
            )
    
    def _health_check_stack(self, stack_name):
        """Perform comprehensive health checks on new stack"""
        print(f"Performing health checks on {stack_name}...")
        
        try:
            # Get stack outputs
            response = self.cfn.describe_stacks(StackName=stack_name)
            outputs = {o['OutputKey']: o['OutputValue'] 
                      for o in response['Stacks'][0].get('Outputs', [])}
            
            # Check load balancer health
            if 'LoadBalancerArn' in outputs:
                lb_arn = outputs['LoadBalancerArn']
                return self._check_load_balancer_health(lb_arn)
            
            return True
            
        except Exception as e:
            print(f"Health check failed: {str(e)}")
            return False
    
    def _check_load_balancer_health(self, lb_arn):
        """Check load balancer target health"""
        try:
            # Get target groups
            tg_response = self.elb.describe_target_groups(LoadBalancerArn=lb_arn)
            
            for tg in tg_response['TargetGroups']:
                tg_arn = tg['TargetGroupArn']
                
                # Check target health
                health_response = self.elb.describe_target_health(
                    TargetGroupArn=tg_arn
                )
                
                healthy_targets = [
                    t for t in health_response['TargetHealthDescriptions']
                    if t['TargetHealth']['State'] == 'healthy'
                ]
                
                if len(healthy_targets) == 0:
                    print(f"No healthy targets in target group: {tg_arn}")
                    return False
                    
            return True
            
        except Exception as e:
            print(f"Load balancer health check failed: {str(e)}")
            return False
    
    def _switch_traffic(self, old_stack, new_stack):
        """Switch traffic from old stack to new stack"""
        print(f"Switching traffic from {old_stack} to {new_stack}")
        
        # Implementation depends on your traffic switching mechanism
        # This could involve updating Route 53 records, ALB target groups, etc.
        
        # Example: Update Route 53 alias record
        # route53 = boto3.client('route53')
        # ... implementation
        
        pass
    
    def _cleanup_old_stack(self, stack_name):
        """Clean up old stack after successful deployment"""
        print(f"Cleaning up old stack: {stack_name}")
        
        try:
            # Disable termination protection
            self.cfn.update_termination_protection(
                StackName=stack_name,
                EnableTerminationProtection=False
            )
            
            # Delete stack
            self.cfn.delete_stack(StackName=stack_name)
            
            # Wait for deletion
            waiter = self.cfn.get_waiter('stack_delete_complete')
            waiter.wait(StackName=stack_name)
            
            print(f"Stack {stack_name} deleted successfully")
            
        except Exception as e:
            print(f"Failed to cleanup stack {stack_name}: {str(e)}")

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python deploy.py <environment> <template-url> <parameters-file>")
        sys.exit(1)
    
    environment = sys.argv[1]
    template_url = sys.argv[2]
    parameters_file = sys.argv[3]
    
    # Load parameters
    with open(parameters_file, 'r') as f:
        parameters = json.load(f)
    
    # Deploy with blue-green pattern
    deployment = BlueGreenDeployment(environment)
    success = deployment.deploy_stack(template_url, parameters)
    
    sys.exit(0 if success else 1)
```

This comprehensive enhancement transforms AWS CloudFormation into a production-ready Infrastructure as Code solution with enterprise-grade patterns, advanced automation, and modern DevOps practices.
