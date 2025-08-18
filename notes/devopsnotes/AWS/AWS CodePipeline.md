# AWS CodePipeline

> **Service Type:** CI/CD Orchestration | **Tier:** CI/CD and Automation | **Global/Regional:** Regional

## Overview

AWS CodePipeline is a continuous delivery service that automates build, test, and deploy phases of your release process. It provides visual workflow management for end-to-end software delivery pipelines.

## DevOps Use Cases

### Application Delivery
- **Web application deployment** with automated testing and rollback
- **Microservices pipelines** with service-specific deployment stages
- **Mobile app CI/CD** with device testing and app store deployment
- **Multi-environment promotion** from dev to staging to production

### Infrastructure Automation
- **Infrastructure as Code** deployments using CloudFormation/CDK
- **Configuration management** with Ansible, Chef, or Puppet
- **Security compliance** with automated security scanning
- **Multi-account deployments** across AWS Organizations

### Advanced Workflows
- **Blue-green deployments** with traffic shifting validation
- **Canary releases** with automated rollback on metrics
- **Feature branch builds** with parallel environment provisioning
- **Cross-region deployments** for disaster recovery and global reach

## Pipeline Architecture

### Pipeline Types

#### Build Pipelines
- **Flow:** Source → Build → Test → Deploy
- **Artifacts:** Code compilation, dependency resolution, packaging
- **Testing:** Unit tests, integration tests, security scans
- **Deployment:** Application deployment to target environments

#### Infrastructure Pipelines
- **Flow:** Source → Validate → Deploy → Test
- **Templates:** CloudFormation, Terraform, CDK
- **Validation:** Template linting, cost estimation, security analysis
- **Testing:** Infrastructure validation, compliance checks

### Pipeline Components

#### Stages
- **Sequential Execution:** Stages run one after another
- **Gates:** Manual approval or automated validation points
- **Parallel Actions:** Multiple actions within a stage
- **Failure Handling:** Stop pipeline on failure or continue

#### Actions
- **Source Actions:** GitHub, CodeCommit, S3, ECR
- **Build Actions:** CodeBuild, Jenkins, TeamCity
- **Test Actions:** CodeBuild, Device Farm, third-party tools
- **Deploy Actions:** CodeDeploy, CloudFormation, ECS, Lambda
- **Invoke Actions:** Lambda functions, SNS notifications

#### Artifacts
- **Input/Output:** Artifacts passed between actions
- **Storage:** S3 bucket managed by CodePipeline
- **Encryption:** KMS encryption for sensitive artifacts
- **Retention:** Configurable artifact retention policies

## Key Features

### Visual Pipeline Editor
- **Drag-and-drop interface** for pipeline creation
- **Real-time execution tracking** with stage status
- **Pipeline visualization** showing flow and dependencies
- **Execution history** with detailed logs and timings

### Integration Capabilities
- **AWS Services:** Native integration with CodeBuild, CodeDeploy, CloudFormation
- **Third-party Tools:** GitHub, Jenkins, Jira, Slack
- **Custom Actions:** Lambda functions for custom logic
- **Webhooks:** External triggers for pipeline execution

### Advanced Features
- **Pipeline templates** for standardized workflows
- **Cross-region deployments** for global applications
- **CloudWatch Events** integration for automated triggering
- **Variable propagation** between pipeline stages
- **Conditional execution** based on parameters or conditions

## Pipeline Patterns

### Simple Web Application
```yaml
Pipeline:
  - Source: GitHub repository
  - Build: CodeBuild (npm install, npm test, npm run build)
  - Deploy: S3 + CloudFront distribution
```

### Microservice with Containers
```yaml
Pipeline:
  - Source: CodeCommit repository
  - Build: CodeBuild (Docker build, push to ECR)
  - Test: CodeBuild (integration tests)
  - Deploy: ECS service update
```

### Infrastructure as Code
```yaml
Pipeline:
  - Source: CloudFormation templates
  - Validate: cfn-lint, CloudFormation validate
  - Deploy: CloudFormation stack update
  - Test: Infrastructure validation scripts
```

### Multi-Environment Promotion
```yaml
Pipeline:
  - Source: Application code
  - Build: Compile and package
  - Deploy-Dev: Automatic deployment to development
  - Test-Dev: Automated testing in dev environment
  - Approval: Manual approval gate
  - Deploy-Prod: Deployment to production
  - Monitor: CloudWatch dashboard and alarms
```

## Best Practices

### Pipeline Design
- **Fail fast:** Put quick validations early in pipeline
- **Parallel execution:** Run independent actions in parallel
- **Artifact management:** Minimize artifact size and scope
- **Idempotent operations:** Ensure deployments can be safely repeated

### Security
- **IAM roles:** Use service roles with least privilege
- **Artifact encryption:** Enable KMS encryption for sensitive data
- **Secret management:** Use Parameter Store or Secrets Manager
- **Cross-account roles:** Secure multi-account deployments

### Monitoring
- **CloudWatch metrics:** Monitor pipeline success rates and duration
- **CloudTrail logging:** Audit pipeline execution and changes
- **SNS notifications:** Alert on pipeline failures or approvals
- **Custom metrics:** Application-specific deployment metrics

### Cost Optimization
- **On-demand builds:** Use CodeBuild for elastic build capacity
- **Efficient testing:** Optimize test execution time
- **Artifact cleanup:** Implement retention policies
- **Resource scheduling:** Schedule non-critical pipelines during off-hours

## Integration Examples

### GitHub Integration
- **Webhooks:** Automatic pipeline triggers on push/PR
- **OAuth tokens:** Secure GitHub access
- **Branch filtering:** Pipeline execution based on branch patterns
- **Status updates:** Pipeline results posted back to GitHub

### Slack Integration
- **Approval notifications:** Manual approval requests
- **Status updates:** Pipeline execution notifications
- **Deployment announcements:** Successful deployment alerts
- **Failure alerts:** Immediate notification on pipeline failures

### JIRA Integration
- **Ticket creation:** Automatic ticket creation on failures
- **Deployment tracking:** Link deployments to JIRA issues
- **Release notes:** Automatic release note generation
- **Approval workflows:** JIRA-based approval processes

## Troubleshooting

### Common Issues
- **Permission errors:** Check IAM roles and policies for all services
- **Artifact corruption:** Verify artifact integrity and S3 permissions
- **Build failures:** Review CloudWatch logs for detailed error information
- **Deployment timeouts:** Adjust timeout settings for long-running operations

### Debugging Techniques
- **CloudWatch logs:** Detailed execution logs for each action
- **Pipeline execution history:** Compare successful vs failed executions
- **Service limits:** Check AWS service limits for concurrent executions
- **CloudTrail events:** API-level troubleshooting for permission issues

### Performance Optimization
- **Build caching:** Use CodeBuild caching for faster builds
- **Parallel stages:** Optimize pipeline structure for parallel execution
- **Resource sizing:** Right-size CodeBuild environments
- **Artifact optimization:** Minimize artifact transfer time

## Advanced CI/CD Patterns

### Enterprise Deployment Strategies

#### Blue-Green Deployment with Traffic Shifting
```yaml
# CodePipeline configuration for blue-green deployments
Pipeline:
  - Source: GitHub webhook trigger
  - Build: 
      Provider: CodeBuild
      Configuration:
        ProjectName: enterprise-build-project
        EnvironmentVariables:
          - Name: BUILD_VERSION
            Value: "#{codepipeline.PipelineExecutionId}"
          - Name: DEPLOYMENT_STRATEGY
            Value: "blue-green"
  - DeployBlue:
      Provider: CodeDeploy
      Configuration:
        ApplicationName: enterprise-app
        DeploymentGroupName: blue-environment
        DeploymentConfigName: CodeDeployDefault.BlueGreenDeployment
  - TrafficShift:
      Provider: Lambda
      Configuration:
        FunctionName: traffic-shift-controller
        UserParameters: |
          {
            "shift_percentage": 10,
            "monitoring_duration": "PT10M",
            "rollback_threshold": 0.01
          }
  - ValidateBlue:
      Provider: CodeBuild
      Configuration:
        ProjectName: integration-tests
        EnvironmentVariables:
          - Name: TARGET_ENVIRONMENT
            Value: "blue"
  - PromoteToGreen:
      Provider: CodeDeploy
      Configuration:
        ApplicationName: enterprise-app
        DeploymentGroupName: green-environment
```

#### Canary Deployment with Automated Rollback
```python
# Lambda function for intelligent canary deployment
import boto3
import json
from datetime import datetime, timedelta

class CanaryDeploymentController:
    def __init__(self):
        self.codedeploy = boto3.client('codedeploy')
        self.cloudwatch = boto3.client('cloudwatch')
        self.codepipeline = boto3.client('codepipeline')
        
    def lambda_handler(self, event, context):
        """
        Intelligent canary deployment with automated rollback
        """
        deployment_id = event['CodePipeline.job']['data']['inputArtifacts'][0]['location']['s3Location']['objectKey']
        job_id = event['CodePipeline.job']['id']
        
        try:
            # Start canary deployment
            canary_result = self.deploy_canary(deployment_id)
            
            # Monitor canary metrics
            metrics_healthy = self.monitor_canary_health(canary_result['deployment_id'])
            
            if metrics_healthy:
                # Promote canary to full deployment
                self.promote_canary(canary_result['deployment_id'])
                self.codepipeline.put_job_success_result(jobId=job_id)
            else:
                # Rollback canary deployment
                self.rollback_canary(canary_result['deployment_id'])
                self.codepipeline.put_job_failure_result(
                    jobId=job_id,
                    failureDetails={'message': 'Canary deployment failed health checks', 'type': 'JobFailed'}
                )
                
        except Exception as e:
            self.codepipeline.put_job_failure_result(
                jobId=job_id,
                failureDetails={'message': str(e), 'type': 'JobFailed'}
            )
    
    def monitor_canary_health(self, deployment_id):
        """
        Monitor canary deployment health metrics
        """
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(minutes=15)
        
        # Check error rate
        error_rate = self.get_metric_value(
            'AWS/ApplicationELB', 'HTTPCode_Target_5XX_Count',
            start_time, end_time
        )
        
        # Check response time
        response_time = self.get_metric_value(
            'AWS/ApplicationELB', 'TargetResponseTime',
            start_time, end_time
        )
        
        # Health criteria
        return (
            error_rate < 0.1 and  # Less than 0.1% error rate
            response_time < 0.5   # Less than 500ms response time
        )
```

### Advanced Integration Patterns

#### Multi-Account Deployment Pipeline
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::CICD-ACCOUNT:role/CodePipelineServiceRole"
      },
      "Action": "sts:AssumeRole",
      "Condition": {
        "StringEquals": {
          "sts:ExternalId": "unique-external-id-for-security"
        }
      }
    }
  ]
}
```

```yaml
# Multi-account pipeline configuration
Pipeline:
  - Source: Central repository
  - Build: Shared CI/CD account
  - DeployDev:
      Provider: CloudFormation
      Configuration:
        ActionMode: CREATE_UPDATE
        RoleArn: "arn:aws:iam::DEV-ACCOUNT:role/CloudFormationRole"
        StackName: application-stack-dev
        TemplatePath: BuildArtifacts::infrastructure/template.yaml
        Capabilities: CAPABILITY_IAM
        ParameterOverrides: |
          {
            "Environment": "development",
            "InstanceType": "t3.micro",
            "MinCapacity": "1",
            "MaxCapacity": "3"
          }
  - ApprovalGate:
      Provider: Manual
      Configuration:
        NotificationArn: "arn:aws:sns:region:account:deployment-approvals"
        CustomData: "Please review dev deployment and approve for staging"
  - DeployStaging:
      Provider: CloudFormation
      Configuration:
        ActionMode: CREATE_UPDATE
        RoleArn: "arn:aws:iam::STAGING-ACCOUNT:role/CloudFormationRole"
        StackName: application-stack-staging
        TemplatePath: BuildArtifacts::infrastructure/template.yaml
        Capabilities: CAPABILITY_IAM
        ParameterOverrides: |
          {
            "Environment": "staging",
            "InstanceType": "t3.small",
            "MinCapacity": "2",
            "MaxCapacity": "10"
          }
  - SecurityScan:
      Provider: CodeBuild
      Configuration:
        ProjectName: security-compliance-scan
        EnvironmentVariables:
          - Name: TARGET_ACCOUNT
            Value: "STAGING-ACCOUNT"
          - Name: STACK_NAME
            Value: "application-stack-staging"
```

### Comprehensive Testing Strategies

#### Automated Quality Gates
```python
# CodeBuild buildspec for comprehensive testing
version: 0.2

phases:
  install:
    runtime-versions:
      python: 3.9
      nodejs: 16
    commands:
      - pip install -r requirements.txt
      - npm install -g @aws-cdk/cli snyk
      
  pre_build:
    commands:
      # Security scanning
      - echo "Running security scans..."
      - snyk test --severity-threshold=high
      - bandit -r src/ -f json -o security-report.json
      
      # Code quality checks
      - echo "Running code quality checks..."
      - pylint src/ --output-format=json > pylint-report.json
      - black --check src/
      - mypy src/ --json-report mypy-report.json
      
  build:
    commands:
      # Unit tests with coverage
      - echo "Running unit tests..."
      - pytest tests/unit/ --cov=src --cov-report=xml --cov-report=html --junit-xml=unit-test-results.xml
      
      # Integration tests
      - echo "Running integration tests..."
      - pytest tests/integration/ --junit-xml=integration-test-results.xml
      
      # Performance tests
      - echo "Running performance tests..."
      - locust -f tests/performance/locustfile.py --headless -u 100 -r 10 -t 60s --html performance-report.html
      
      # Infrastructure tests
      - echo "Testing infrastructure..."
      - cdk synth
      - cdk diff --strict
      
  post_build:
    commands:
      # Generate deployment artifacts
      - echo "Building deployment artifacts..."
      - docker build -t $IMAGE_REPO_URI:$IMAGE_TAG .
      - docker push $IMAGE_REPO_URI:$IMAGE_TAG
      
      # Update deployment manifest
      - sed -i 's@CONTAINER_IMAGE@'$IMAGE_REPO_URI:$IMAGE_TAG'@' deployment/k8s-deployment.yaml
      
      # Create deployment package
      - aws cloudformation package --template-file infrastructure/template.yaml --s3-bucket $ARTIFACTS_BUCKET --output-template-file packaged-template.yaml

artifacts:
  files:
    - packaged-template.yaml
    - deployment/**/*
    - scripts/**/*
  secondary-artifacts:
    TestResults:
      files:
        - '**/*-test-results.xml'
        - coverage.xml
        - performance-report.html
    SecurityReports:
      files:
        - security-report.json
        - pylint-report.json
```

### Production-Ready CloudFormation Templates

#### Scalable Pipeline Infrastructure
```yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: 'Enterprise-grade CodePipeline with advanced features'

Parameters:
  Environment:
    Type: String
    AllowedValues: [dev, staging, prod]
    Description: Target environment
  
  MultiRegionDeployment:
    Type: String
    Default: 'false'
    AllowedValues: ['true', 'false']
    Description: Enable multi-region deployment

Conditions:
  IsProduction: !Equals [!Ref Environment, 'prod']
  EnableMultiRegion: !And 
    - !Equals [!Ref MultiRegionDeployment, 'true']
    - !Condition IsProduction

Resources:
  # S3 Bucket for Pipeline Artifacts
  PipelineArtifactsBucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: !Sub '${AWS::StackName}-pipeline-artifacts-${AWS::AccountId}'
      VersioningConfiguration:
        Status: Enabled
      BucketEncryption:
        ServerSideEncryptionConfiguration:
          - ServerSideEncryptionByDefault:
              SSEAlgorithm: aws:kms
              KMSMasterKeyID: !Ref PipelineKMSKey
      PublicAccessBlockConfiguration:
        BlockPublicAcls: true
        BlockPublicPolicy: true
        IgnorePublicAcls: true
        RestrictPublicBuckets: true
      LifecycleConfiguration:
        Rules:
          - Id: DeleteOldArtifacts
            Status: Enabled
            ExpirationInDays: !If [IsProduction, 90, 30]
            NoncurrentVersionExpirationInDays: 7

  # KMS Key for Pipeline Encryption
  PipelineKMSKey:
    Type: AWS::KMS::Key
    Properties:
      Description: 'KMS Key for CodePipeline encryption'
      KeyPolicy:
        Statement:
          - Sid: Enable IAM User Permissions
            Effect: Allow
            Principal:
              AWS: !Sub 'arn:aws:iam::${AWS::AccountId}:root'
            Action: 'kms:*'
            Resource: '*'
          - Sid: Allow CodePipeline Service
            Effect: Allow
            Principal:
              Service: codepipeline.amazonaws.com
            Action:
              - kms:Decrypt
              - kms:GenerateDataKey
            Resource: '*'

  # CodeBuild Project for Advanced Building
  BuildProject:
    Type: AWS::CodeBuild::Project
    Properties:
      Name: !Sub '${AWS::StackName}-build'
      ServiceRole: !GetAtt CodeBuildServiceRole.Arn
      Artifacts:
        Type: CODEPIPELINE
      Environment:
        Type: LINUX_CONTAINER
        ComputeType: !If [IsProduction, 'BUILD_GENERAL1_LARGE', 'BUILD_GENERAL1_MEDIUM']
        Image: aws/codebuild/amazonlinux2-x86_64-standard:4.0
        PrivilegedMode: true
        EnvironmentVariables:
          - Name: AWS_DEFAULT_REGION
            Value: !Ref AWS::Region
          - Name: REPOSITORY_URI
            Value: !Sub '${AWS::AccountId}.dkr.ecr.${AWS::Region}.amazonaws.com/${ECRRepository}'
          - Name: ENVIRONMENT
            Value: !Ref Environment
      Source:
        Type: CODEPIPELINE
        BuildSpec: |
          version: 0.2
          phases:
            pre_build:
              commands:
                - echo Logging in to Amazon ECR...
                - aws ecr get-login-password --region $AWS_DEFAULT_REGION | docker login --username AWS --password-stdin $REPOSITORY_URI
            build:
              commands:
                - echo Build started on `date`
                - echo Building the Docker image...
                - docker build -t $REPOSITORY_URI:latest .
                - docker tag $REPOSITORY_URI:latest $REPOSITORY_URI:$CODEBUILD_RESOLVED_SOURCE_VERSION
            post_build:
              commands:
                - echo Build completed on `date`
                - echo Pushing the Docker images...
                - docker push $REPOSITORY_URI:latest
                - docker push $REPOSITORY_URI:$CODEBUILD_RESOLVED_SOURCE_VERSION
      Cache:
        Type: S3
        Location: !Sub '${PipelineArtifactsBucket}/build-cache'

  # Main CodePipeline
  Pipeline:
    Type: AWS::CodePipeline::Pipeline
    Properties:
      Name: !Sub '${AWS::StackName}-pipeline'
      RoleArn: !GetAtt CodePipelineServiceRole.Arn
      ArtifactStore:
        Type: S3
        Location: !Ref PipelineArtifactsBucket
        EncryptionKey:
          Id: !Ref PipelineKMSKey
          Type: KMS
      Stages:
        - Name: Source
          Actions:
            - Name: SourceAction
              ActionTypeId:
                Category: Source
                Owner: ThirdParty
                Provider: GitHub
                Version: '1'
              Configuration:
                Owner: !Ref GitHubOwner
                Repo: !Ref GitHubRepo
                Branch: !Ref GitHubBranch
                OAuthToken: !Ref GitHubToken
              OutputArtifacts:
                - Name: SourceOutput
        
        - Name: Build
          Actions:
            - Name: BuildAction
              ActionTypeId:
                Category: Build
                Owner: AWS
                Provider: CodeBuild
                Version: '1'
              Configuration:
                ProjectName: !Ref BuildProject
              InputArtifacts:
                - Name: SourceOutput
              OutputArtifacts:
                - Name: BuildOutput
        
        - !If
          - IsProduction
          - Name: ManualApproval
            Actions:
              - Name: ManualApprovalAction
                ActionTypeId:
                  Category: Approval
                  Owner: AWS
                  Provider: Manual
                  Version: '1'
                Configuration:
                  NotificationArn: !Ref ApprovalTopic
                  CustomData: 'Please review the build artifacts before deployment to production'
          - !Ref 'AWS::NoValue'
        
        - Name: Deploy
          Actions:
            - Name: DeployAction
              ActionTypeId:
                Category: Deploy
                Owner: AWS
                Provider: CloudFormation
                Version: '1'
              Configuration:
                ActionMode: CREATE_UPDATE
                RoleArn: !GetAtt CloudFormationServiceRole.Arn
                StackName: !Sub '${AWS::StackName}-application'
                TemplatePath: BuildOutput::packaged-template.yaml
                Capabilities: CAPABILITY_IAM,CAPABILITY_NAMED_IAM
                ParameterOverrides: !Sub |
                  {
                    "Environment": "${Environment}",
                    "ImageUri": "${AWS::AccountId}.dkr.ecr.${AWS::Region}.amazonaws.com/${ECRRepository}:latest"
                  }
              InputArtifacts:
                - Name: BuildOutput

  # CloudWatch Events Rule for Pipeline Monitoring
  PipelineEventRule:
    Type: AWS::Events::Rule
    Properties:
      Description: 'Monitor CodePipeline state changes'
      EventPattern:
        source:
          - aws.codepipeline
        detail-type:
          - CodePipeline Pipeline Execution State Change
          - CodePipeline Stage Execution State Change
        detail:
          pipeline:
            - !Ref Pipeline
          state:
            - FAILED
            - SUCCEEDED
      State: ENABLED
      Targets:
        - Arn: !Ref NotificationTopic
          Id: PipelineNotificationTarget
          InputTransformer:
            InputPathsMap:
              pipeline: '$.detail.pipeline'
              state: '$.detail.state'
              stage: '$.detail.stage'
            InputTemplate: |
              {
                "pipeline": "<pipeline>",
                "state": "<state>",
                "stage": "<stage>",
                "account": "${AWS::AccountId}",
                "region": "${AWS::Region}"
              }

Outputs:
  PipelineName:
    Description: Name of the created pipeline
    Value: !Ref Pipeline
    Export:
      Name: !Sub '${AWS::StackName}-PipelineName'
  
  PipelineArn:
    Description: ARN of the created pipeline
    Value: !Sub 'arn:aws:codepipeline:${AWS::Region}:${AWS::AccountId}:pipeline/${Pipeline}'
    Export:
      Name: !Sub '${AWS::StackName}-PipelineArn'
```

### Monitoring and Observability

#### Advanced Pipeline Metrics
```python
# Custom CloudWatch metrics for pipeline monitoring
import boto3
from datetime import datetime, timedelta

class PipelineMetricsCollector:
    def __init__(self):
        self.cloudwatch = boto3.client('cloudwatch')
        self.codepipeline = boto3.client('codepipeline')
    
    def collect_pipeline_metrics(self, pipeline_name):
        """Collect comprehensive pipeline metrics"""
        
        # Get pipeline execution history
        executions = self.codepipeline.list_pipeline_executions(
            pipelineName=pipeline_name,
            maxResults=50
        )
        
        # Calculate success rate
        total_executions = len(executions['pipelineExecutionSummaries'])
        successful_executions = len([
            e for e in executions['pipelineExecutionSummaries'] 
            if e['status'] == 'Succeeded'
        ])
        
        success_rate = (successful_executions / total_executions) * 100 if total_executions > 0 else 0
        
        # Calculate average execution time
        execution_times = []
        for execution in executions['pipelineExecutionSummaries']:
            if execution['status'] in ['Succeeded', 'Failed'] and 'endTime' in execution:
                duration = (execution['endTime'] - execution['startTime']).total_seconds()
                execution_times.append(duration)
        
        avg_execution_time = sum(execution_times) / len(execution_times) if execution_times else 0
        
        # Send metrics to CloudWatch
        self.cloudwatch.put_metric_data(
            Namespace='CodePipeline/Custom',
            MetricData=[
                {
                    'MetricName': 'SuccessRate',
                    'Dimensions': [
                        {
                            'Name': 'PipelineName',
                            'Value': pipeline_name
                        }
                    ],
                    'Value': success_rate,
                    'Unit': 'Percent'
                },
                {
                    'MetricName': 'AverageExecutionTime',
                    'Dimensions': [
                        {
                            'Name': 'PipelineName',
                            'Value': pipeline_name
                        }
                    ],
                    'Value': avg_execution_time,
                    'Unit': 'Seconds'
                }
            ]
        )
        
        return {
            'success_rate': success_rate,
            'average_execution_time': avg_execution_time,
            'total_executions': total_executions
        }
```

## Security Integration

### Advanced Security Scanning Pipeline
```yaml
# Security-first pipeline configuration
SecureCodePipeline:
  Stages:
    - Name: SecurityValidation
      Actions:
        - Name: StaticApplicationSecurityTesting
          Provider: CodeBuild
          Configuration:
            ProjectName: sast-scan
            BuildSpec: |
              version: 0.2
              phases:
                pre_build:
                  commands:
                    - pip install bandit safety semgrep
                build:
                  commands:
                    # Static code analysis
                    - bandit -r src/ -f json -o bandit-report.json
                    - safety check --json --output safety-report.json
                    - semgrep --config=auto src/ --json --output=semgrep-report.json
                    
                    # Dependency vulnerability scanning
                    - npm audit --json > npm-audit-report.json
                    
                    # Infrastructure security scanning
                    - checkov -f infrastructure/ --output json > checkov-report.json
                    
                post_build:
                  commands:
                    - python scripts/security-gate.py
              artifacts:
                files:
                  - '*-report.json'
        
        - Name: ContainerSecurityScan
          Provider: CodeBuild
          Configuration:
            ProjectName: container-security-scan
            BuildSpec: |
              version: 0.2
              phases:
                pre_build:
                  commands:
                    - curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin
                build:
                  commands:
                    # Container image vulnerability scanning
                    - trivy image --format json --output trivy-report.json $REPOSITORY_URI:latest
                    
                    # Container configuration scanning
                    - trivy config --format json --output trivy-config-report.json .
                    
                    # Generate SBOM (Software Bill of Materials)
                    - trivy image --format spdx-json --output sbom.json $REPOSITORY_URI:latest
                post_build:
                  commands:
                    - python scripts/container-security-gate.py
```

This comprehensive enhancement transforms the AWS CodePipeline documentation into a production-ready guide with enterprise-grade patterns, advanced security integration, and real-world implementation examples.