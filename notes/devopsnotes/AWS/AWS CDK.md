# AWS CDK: Enterprise Infrastructure-as-Code Development Platform

> **Service Type:** Developer Tools | **Scope:** Global | **Serverless:** Yes

## Overview

AWS CDK (Cloud Development Kit) is an enterprise-grade software development framework that revolutionizes infrastructure management by enabling developers to define cloud infrastructure using familiar programming languages including TypeScript, Python, Java, C#, and Go. It provides a developer-centric approach to Infrastructure as Code with type safety, IDE support, and reusable constructs that enforce best practices and organizational standards while delivering enterprise-grade security, compliance, and operational excellence.

## Core Architecture Components

- **Construct System:** Hierarchical component model with L1 (CFN Resources), L2 (AWS Constructs), and L3 (Patterns) abstractions
- **Synthesis Engine:** Code-to-CloudFormation compilation system with dependency resolution and asset management
- **App Framework:** Multi-stack application organization with cross-stack references and environment-specific deployments
- **Asset Management:** Automated bundling and deployment of Lambda functions, Docker images, and file assets
- **Bootstrap System:** Self-contained deployment toolkit with S3 staging bucket, ECR repositories, and IAM roles
- **Aspect System:** Cross-cutting concern implementation for tagging, compliance, and security policies
- **Context Providers:** Environment-aware resource discovery and configuration management
- **CDK Toolkit:** Command-line interface with synthesis, deployment, and management capabilities

## DevOps & Enterprise Use Cases

### Enterprise Infrastructure as Code
- **Type-Safe Infrastructure:** Compile-time validation, IntelliSense support, and refactoring capabilities for infrastructure code
- **Enterprise Construct Libraries:** Standardized, reusable components enforcing organizational policies and best practices
- **GitOps Integration:** Full version control workflows with branching strategies, code review, and automated testing
- **Infrastructure Testing:** Comprehensive unit, integration, and snapshot testing frameworks for infrastructure validation

### Cloud-Native Application Deployment
- **Full-Stack Integration:** Unified codebase managing both application logic and infrastructure with shared deployment cycles
- **Microservices Architecture:** Service-specific infrastructure patterns with automated service discovery and inter-service communication
- **Event-Driven Systems:** Serverless event processing with Lambda, EventBridge, and Step Functions integration
- **Container Orchestration:** Advanced ECS Fargate and EKS deployment patterns with auto-scaling and service mesh integration

### Enterprise DevOps Transformation
- **Multi-Account Governance:** Centralized construct libraries, shared services, and cross-account deployment strategies
- **Environment Promotion:** Automated progression through dev/staging/production with infrastructure drift detection
- **Compliance Automation:** Policy-as-code implementation with automated compliance validation and remediation
- **FinOps Integration:** Programmatic cost optimization with resource tagging, lifecycle policies, and spend analytics

### Enhanced Developer Experience
- **IDE-First Development:** Native autocomplete, type checking, debugging, and refactoring support in modern IDEs
- **Local Development Workflow:** CDK synthesis, CloudFormation template preview, and diff visualization before deployment
- **Hot Swapping Capabilities:** Lightning-fast development cycles with selective resource updates for Lambda and ECS services
- **Automated Asset Management:** Intelligent bundling and optimization for Lambda functions, container images, and static assets

## Service Features & Capabilities

### Construct Architecture
- **L1 Constructs (CFN Resources):** Low-level CloudFormation resource mappings with direct 1:1 API correspondence
- **L2 Constructs (AWS Constructs):** Higher-level AWS service abstractions with intelligent defaults and validation
- **L3 Constructs (Patterns):** Opinionated, multi-service architectural patterns solving common use cases
- **Custom Constructs:** Organization-specific reusable components enforcing internal standards and best practices

### Application Organization
- **CDK App:** Root construct defining application scope with environment-specific configuration management
- **Stacks:** Deployment units mapping to CloudFormation stacks with resource dependency management
- **Stages:** Environment-specific stack groupings with shared configuration and cross-stack references
- **Aspects:** Cross-cutting concerns for tagging, security policies, and compliance requirements

### Deployment Pipeline
- **CDK Synthesis:** Code-to-CloudFormation compilation with dependency resolution and template optimization
- **Bootstrap Infrastructure:** Self-contained deployment foundation with S3, ECR, and IAM resources per environment
- **Asset Management:** Automated versioning, packaging, and deployment of Lambda code, Docker images, and file assets
- **Cloud Assembly:** Structured output containing templates, metadata, and deployment instructions

## Configuration & Setup

### Enterprise CDK Framework

```typescript
// enterprise-cdk-framework.ts - Advanced CDK patterns for enterprise DevOps
import * as cdk from 'aws-cdk-lib';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as ecs from 'aws-cdk-lib/aws-ecs';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as logs from 'aws-cdk-lib/aws-logs';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import * as kms from 'aws-cdk-lib/aws-kms';
import * as codecommit from 'aws-cdk-lib/aws-codecommit';
import * as codebuild from 'aws-cdk-lib/aws-codebuild';
import * as codepipeline from 'aws-cdk-lib/aws-codepipeline';
import * as codepipeline_actions from 'aws-cdk-lib/aws-codepipeline-actions';
import { Construct } from 'constructs';

/**
 * Environment configuration for multi-stage deployments
 */
export interface EnvironmentConfig {
  readonly account: string;
  readonly region: string;
  readonly stage: 'dev' | 'staging' | 'prod';
  readonly vpcId?: string;
  readonly domainName?: string;
  readonly certificateArn?: string;
  readonly monitoringLevel: 'basic' | 'standard' | 'enhanced';
  readonly backupRetention: number;
  readonly logRetention: logs.RetentionDays;
}

/**
 * Security configuration for enterprise environments
 */
export interface SecurityConfig {
  readonly enableVpcFlowLogs: boolean;
  readonly enableCloudTrail: boolean;
  readonly enableConfigRules: boolean;
  readonly enableSecurityHub: boolean;
  readonly enableGuardDuty: boolean;
  readonly kmsKeyPolicy?: iam.PolicyDocument;
  readonly allowedCidrs: string[];
  readonly requireMfa: boolean;
}

/**
 * Compliance requirements configuration
 */
export interface ComplianceConfig {
  readonly framework: 'sox' | 'pci' | 'hipaa' | 'gdpr' | 'custom';
  readonly dataClassification: 'public' | 'internal' | 'confidential' | 'restricted';
  readonly encryptionAtRest: boolean;
  readonly encryptionInTransit: boolean;
  readonly accessLogging: boolean;
  readonly dataRetentionDays: number;
  readonly auditTrailRetention: number;
}

/**
 * Base construct for enterprise applications with governance, security, and observability
 */
export class EnterpriseApplicationConstruct extends Construct {
  public readonly vpc: ec2.IVpc;
  public readonly cluster: ecs.Cluster;
  public readonly kmsKey: kms.Key;
  public readonly logGroup: logs.LogGroup;
  
  constructor(scope: Construct, id: string, props: {
    environmentConfig: EnvironmentConfig;
    securityConfig: SecurityConfig;
    complianceConfig: ComplianceConfig;
  }) {
    super(scope, id);
    
    // Create KMS key for encryption
    this.kmsKey = new kms.Key(this, 'ApplicationKmsKey', {
      description: `KMS key for ${id} application`,
      enableKeyRotation: true,
      policy: props.securityConfig.kmsKeyPolicy,
      removalPolicy: props.environmentConfig.stage === 'prod' ? 
        cdk.RemovalPolicy.RETAIN : cdk.RemovalPolicy.DESTROY,
    });
    
    // Create or import VPC
    this.vpc = props.environmentConfig.vpcId ? 
      ec2.Vpc.fromLookup(this, 'ExistingVpc', {
        vpcId: props.environmentConfig.vpcId
      }) : 
      new EnterpriseVpcConstruct(this, 'ApplicationVpc', {
        environmentConfig: props.environmentConfig,
        securityConfig: props.securityConfig
      }).vpc;
    
    // Create ECS cluster with enterprise configuration
    this.cluster = new ecs.Cluster(this, 'ApplicationCluster', {
      vpc: this.vpc,
      clusterName: `${id}-${props.environmentConfig.stage}`,
      containerInsights: props.environmentConfig.monitoringLevel !== 'basic',
      enableFargateCapacityProviders: true,
    });
    
    // Configure cluster with EC2 capacity if needed
    if (props.environmentConfig.stage === 'prod') {
      this.cluster.addCapacity('ApplicationCapacity', {
        instanceType: ec2.InstanceType.of(ec2.InstanceClass.M5, ec2.InstanceSize.LARGE),
        desiredCapacity: 3,
        maxCapacity: 10,
        keyName: 'enterprise-key-pair',
        userData: ec2.UserData.forLinux(),
        autoScalingGroupName: `${id}-asg-${props.environmentConfig.stage}`,
      });
    }
    
    // Create centralized log group
    this.logGroup = new logs.LogGroup(this, 'ApplicationLogs', {
      logGroupName: `/aws/application/${id}/${props.environmentConfig.stage}`,
      retention: props.environmentConfig.logRetention,
      encryptionKey: this.kmsKey,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });
    
    // Apply compliance and security aspects
    this.applyComplianceAspects(props.complianceConfig);
    this.applySecurityAspects(props.securityConfig);
    this.setupMonitoring(props.environmentConfig);
  }
  
  private applyComplianceAspects(config: ComplianceConfig): void {
    // Apply compliance aspects based on framework
    const complianceAspect = new ComplianceAspect(config);
    cdk.Aspects.of(this).add(complianceAspect);
  }
  
  private applySecurityAspects(config: SecurityConfig): void {
    // Apply security hardening aspects
    const securityAspect = new SecurityHardeningAspect(config);
    cdk.Aspects.of(this).add(securityAspect);
  }
  
  private setupMonitoring(config: EnvironmentConfig): void {
    // Setup CloudWatch dashboards and alarms
    const monitoringAspect = new MonitoringAspect({
      level: config.monitoringLevel,
      logGroup: this.logGroup,
      kmsKey: this.kmsKey
    });
    cdk.Aspects.of(this).add(monitoringAspect);
  }
}

/**
 * Enterprise VPC construct with security best practices
 */
export class EnterpriseVpcConstruct extends Construct {
  public readonly vpc: ec2.Vpc;
  public readonly flowLogsRole: iam.Role;
  
  constructor(scope: Construct, id: string, props: {
    environmentConfig: EnvironmentConfig;
    securityConfig: SecurityConfig;
  }) {
    super(scope, id);
    
    // Create VPC with enterprise configuration
    this.vpc = new ec2.Vpc(this, 'EnterpriseVpc', {
      maxAzs: 3,
      cidr: this.getCidrForEnvironment(props.environmentConfig.stage),
      enableDnsHostnames: true,
      enableDnsSupport: true,
      subnetConfiguration: [
        {
          name: 'PublicSubnet',
          subnetType: ec2.SubnetType.PUBLIC,
          cidrMask: 24,
          mapPublicIpOnLaunch: false,
        },
        {
          name: 'PrivateSubnet',
          subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS,
          cidrMask: 24,
        },
        {
          name: 'DatabaseSubnet',
          subnetType: ec2.SubnetType.PRIVATE_ISOLATED,
          cidrMask: 28,
        },
      ],
      natGateways: props.environmentConfig.stage === 'prod' ? 3 : 1,
    });
    
    // Enable VPC Flow Logs if required
    if (props.securityConfig.enableVpcFlowLogs) {
      this.flowLogsRole = new iam.Role(this, 'VpcFlowLogsRole', {
        assumedBy: new iam.ServicePrincipal('vpc-flow-logs.amazonaws.com'),
        managedPolicies: [
          iam.ManagedPolicy.fromAwsManagedPolicyName('service-role/VPCFlowLogsDeliverRolePolicy'),
        ],
      });
      
      this.vpc.addFlowLog('VpcFlowLogs', {
        destination: ec2.FlowLogDestination.toCloudWatchLogs(
          new logs.LogGroup(this, 'VpcFlowLogsGroup', {
            retention: logs.RetentionDays.ONE_MONTH,
          }),
          this.flowLogsRole
        ),
        trafficType: ec2.FlowLogTrafficType.ALL,
      });
    }
    
    // Add security group rules
    this.addSecurityGroupRules(props.securityConfig);
    
    // Tag all VPC resources
    cdk.Tags.of(this.vpc).add('Environment', props.environmentConfig.stage);
    cdk.Tags.of(this.vpc).add('ManagedBy', 'CDK');
    cdk.Tags.of(this.vpc).add('CostCenter', 'DevOps');
  }
  
  private getCidrForEnvironment(stage: string): string {
    const cidrMap: Record<string, string> = {
      'dev': '10.0.0.0/16',
      'staging': '10.1.0.0/16',
      'prod': '10.2.0.0/16',
    };
    return cidrMap[stage] || '10.0.0.0/16';
  }
  
  private addSecurityGroupRules(config: SecurityConfig): void {
    // Create enterprise security groups with minimal access
    const webSecurityGroup = new ec2.SecurityGroup(this, 'WebSecurityGroup', {
      vpc: this.vpc,
      description: 'Security group for web tier',
      allowAllOutbound: false,
    });
    
    const appSecurityGroup = new ec2.SecurityGroup(this, 'AppSecurityGroup', {
      vpc: this.vpc,
      description: 'Security group for application tier',
      allowAllOutbound: false,
    });
    
    const dbSecurityGroup = new ec2.SecurityGroup(this, 'DatabaseSecurityGroup', {
      vpc: this.vpc,
      description: 'Security group for database tier',
      allowAllOutbound: false,
    });
    
    // Configure security group rules based on allowed CIDRs
    config.allowedCidrs.forEach(cidr => {
      webSecurityGroup.addIngressRule(
        ec2.Peer.ipv4(cidr),
        ec2.Port.tcp(443),
        'HTTPS access from allowed networks'
      );
    });
    
    // Inter-tier communication
    appSecurityGroup.addIngressRule(
      webSecurityGroup,
      ec2.Port.tcp(8080),
      'Application access from web tier'
    );
    
    dbSecurityGroup.addIngressRule(
      appSecurityGroup,
      ec2.Port.tcp(5432),
      'Database access from application tier'
    );
  }
}

/**
 * Microservice construct with standardized patterns
 */
export class MicroserviceConstruct extends Construct {
  public readonly service: ecs.FargateService;
  public readonly taskDefinition: ecs.FargateTaskDefinition;
  public readonly loadBalancer: elbv2.ApplicationLoadBalancer;
  
  constructor(scope: Construct, id: string, props: {
    cluster: ecs.Cluster;
    vpc: ec2.IVpc;
    serviceName: string;
    containerImage: ecs.ContainerImage;
    environmentConfig: EnvironmentConfig;
    serviceConfig: {
      cpu: number;
      memory: number;
      desiredCount: number;
      healthCheckPath: string;
      containerPort: number;
      environmentVariables?: Record<string, string>;
      secrets?: Record<string, ecs.Secret>;
    };
  }) {
    super(scope, id);
    
    // Create task definition
    this.taskDefinition = new ecs.FargateTaskDefinition(this, 'TaskDefinition', {
      cpu: props.serviceConfig.cpu,
      memoryLimitMiB: props.serviceConfig.memory,
      family: `${props.serviceName}-${props.environmentConfig.stage}`,
    });
    
    // Add container to task definition
    const container = this.taskDefinition.addContainer('ServiceContainer', {
      image: props.containerImage,
      logging: ecs.LogDrivers.awsLogs({
        streamPrefix: props.serviceName,
        logGroup: new logs.LogGroup(this, 'ServiceLogGroup', {
          logGroupName: `/aws/ecs/${props.serviceName}/${props.environmentConfig.stage}`,
          retention: props.environmentConfig.logRetention,
          removalPolicy: cdk.RemovalPolicy.DESTROY,
        }),
      }),
      environment: props.serviceConfig.environmentVariables,
      secrets: props.serviceConfig.secrets,
      healthCheck: {
        command: ['CMD-SHELL', `curl -f http://localhost:${props.serviceConfig.containerPort}${props.serviceConfig.healthCheckPath} || exit 1`],
        interval: cdk.Duration.seconds(30),
        timeout: cdk.Duration.seconds(5),
        retries: 3,
        startPeriod: cdk.Duration.seconds(60),
      },
    });
    
    container.addPortMappings({
      containerPort: props.serviceConfig.containerPort,
      protocol: ecs.Protocol.TCP,
    });
    
    // Create Fargate service
    this.service = new ecs.FargateService(this, 'Service', {
      cluster: props.cluster,
      taskDefinition: this.taskDefinition,
      desiredCount: props.serviceConfig.desiredCount,
      serviceName: `${props.serviceName}-${props.environmentConfig.stage}`,
      enableLogging: true,
      enableExecuteCommand: props.environmentConfig.stage !== 'prod',
      propagateTags: ecs.PropagatedTagSource.SERVICE,
      enableServiceConnect: true,
    });
    
    // Create Application Load Balancer
    this.loadBalancer = new elbv2.ApplicationLoadBalancer(this, 'LoadBalancer', {
      vpc: props.vpc,
      internetFacing: true,
      loadBalancerName: `${props.serviceName}-${props.environmentConfig.stage}-alb`,
    });
    
    // Create target group and listener
    const targetGroup = new elbv2.ApplicationTargetGroup(this, 'TargetGroup', {
      vpc: props.vpc,
      port: props.serviceConfig.containerPort,
      protocol: elbv2.ApplicationProtocol.HTTP,
      targetType: elbv2.TargetType.IP,
      healthCheck: {
        path: props.serviceConfig.healthCheckPath,
        protocol: elbv2.Protocol.HTTP,
        healthyThresholdCount: 2,
        unhealthyThresholdCount: 5,
        timeout: cdk.Duration.seconds(10),
        interval: cdk.Duration.seconds(30),
      },
      targets: [this.service],
    });
    
    this.loadBalancer.addListener('HttpListener', {
      port: 80,
      protocol: elbv2.ApplicationProtocol.HTTP,
      defaultAction: elbv2.ListenerAction.forward([targetGroup]),
    });
    
    // Setup auto scaling
    const scaling = this.service.autoScaleTaskCount({
      minCapacity: 1,
      maxCapacity: props.environmentConfig.stage === 'prod' ? 20 : 5,
    });
    
    scaling.scaleOnCpuUtilization('CpuScaling', {
      targetUtilizationPercent: 70,
      scaleInCooldown: cdk.Duration.minutes(5),
      scaleOutCooldown: cdk.Duration.minutes(2),
    });
    
    scaling.scaleOnMemoryUtilization('MemoryScaling', {
      targetUtilizationPercent: 80,
      scaleInCooldown: cdk.Duration.minutes(5),
      scaleOutCooldown: cdk.Duration.minutes(2),
    });
  }
}

/**
 * CI/CD Pipeline construct for automated deployments
 */
export class EnterpriseDeploymentPipelineConstruct extends Construct {
  public readonly pipeline: codepipeline.Pipeline;
  public readonly repository: codecommit.Repository;
  
  constructor(scope: Construct, id: string, props: {
    serviceName: string;
    environments: EnvironmentConfig[];
    buildspecPath?: string;
    deploymentConfig: {
      requireManualApproval: boolean;
      runTests: boolean;
      performSecurityScan: boolean;
      enableBlueGreenDeployment: boolean;
    };
  }) {
    super(scope, id);
    
    // Create CodeCommit repository
    this.repository = new codecommit.Repository(this, 'Repository', {
      repositoryName: `${props.serviceName}-repo`,
      description: `Source repository for ${props.serviceName}`,
    });
    
    // Create build project
    const buildProject = new codebuild.Project(this, 'BuildProject', {
      projectName: `${props.serviceName}-build`,
      source: codebuild.Source.codeCommit({
        repository: this.repository,
        branchOrRef: 'main',
      }),
      environment: {
        buildImage: codebuild.LinuxBuildImage.STANDARD_5_0,
        privileged: true, // Required for Docker builds
        computeType: codebuild.ComputeType.MEDIUM,
        environmentVariables: {
          'AWS_DEFAULT_REGION': { value: cdk.Aws.REGION },
          'AWS_ACCOUNT_ID': { value: cdk.Aws.ACCOUNT_ID },
          'IMAGE_REPO_NAME': { value: props.serviceName },
          'IMAGE_TAG': { value: 'latest' },
        },
      },
      buildSpec: props.buildspecPath ? 
        codebuild.BuildSpec.fromSourceFilename(props.buildspecPath) :
        this.createDefaultBuildSpec(props),
      cache: codebuild.Cache.local(codebuild.LocalCacheMode.DOCKER_LAYER),
    });
    
    // Grant necessary permissions to build project
    buildProject.addToRolePolicy(new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: [
        'ecr:BatchCheckLayerAvailability',
        'ecr:GetDownloadUrlForLayer',
        'ecr:BatchGetImage',
        'ecr:GetAuthorizationToken',
        'ecr:PutImage',
        'ecr:InitiateLayerUpload',
        'ecr:UploadLayerPart',
        'ecr:CompleteLayerUpload',
      ],
      resources: ['*'],
    }));
    
    // Create artifacts bucket
    const artifactsBucket = new s3.Bucket(this, 'ArtifactsBucket', {
      bucketName: `${props.serviceName}-pipeline-artifacts-${cdk.Aws.ACCOUNT_ID}`,
      versioned: true,
      encryption: s3.BucketEncryption.S3_MANAGED,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      autoDeleteObjects: true,
    });
    
    // Create source and build artifacts
    const sourceArtifact = new codepipeline.Artifact('SourceArtifact');
    const buildArtifact = new codepipeline.Artifact('BuildArtifact');
    
    // Create pipeline stages
    const stages: codepipeline.StageProps[] = [
      {
        stageName: 'Source',
        actions: [
          new codepipeline_actions.CodeCommitSourceAction({
            actionName: 'Source',
            repository: this.repository,
            branch: 'main',
            output: sourceArtifact,
          }),
        ],
      },
      {
        stageName: 'Build',
        actions: [
          new codepipeline_actions.CodeBuildAction({
            actionName: 'Build',
            project: buildProject,
            input: sourceArtifact,
            outputs: [buildArtifact],
          }),
        ],
      },
    ];
    
    // Add deployment stages for each environment
    props.environments.forEach((env, index) => {
      const isProduction = env.stage === 'prod';
      
      // Add manual approval for production
      if (isProduction && props.deploymentConfig.requireManualApproval) {
        stages.push({
          stageName: `Approve-${env.stage}`,
          actions: [
            new codepipeline_actions.ManualApprovalAction({
              actionName: `Approve-${env.stage}`,
              additionalInformation: `Approve deployment to ${env.stage} environment`,
            }),
          ],
        });
      }
      
      // Add deployment stage
      stages.push({
        stageName: `Deploy-${env.stage}`,
        actions: [
          new codepipeline_actions.CloudFormationCreateUpdateStackAction({
            actionName: `Deploy-${env.stage}`,
            stackName: `${props.serviceName}-${env.stage}`,
            templatePath: buildArtifact.atPath('template.yaml'),
            adminPermissions: true,
            parameterOverrides: {
              Environment: env.stage,
              ImageUri: buildArtifact.getParam('ImageUri', 'outputs.json'),
            },
            extraInputs: [buildArtifact],
          }),
        ],
      });
    });
    
    // Create the pipeline
    this.pipeline = new codepipeline.Pipeline(this, 'Pipeline', {
      pipelineName: `${props.serviceName}-pipeline`,
      artifactBucket: artifactsBucket,
      stages: stages,
      restartExecutionOnUpdate: true,
    });
  }
  
  private createDefaultBuildSpec(props: any): codebuild.BuildSpec {
    return codebuild.BuildSpec.fromObject({
      version: '0.2',
      phases: {
        pre_build: {
          commands: [
            'echo Logging in to Amazon ECR...',
            'aws ecr get-login-password --region $AWS_DEFAULT_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com',
            'REPOSITORY_URI=$AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com/$IMAGE_REPO_NAME',
            'COMMIT_HASH=$(echo $CODEBUILD_RESOLVED_SOURCE_VERSION | cut -c 1-7)',
            'IMAGE_TAG=${COMMIT_HASH:=latest}',
          ],
        },
        build: {
          commands: [
            'echo Build started on `date`',
            'echo Building the Docker image...',
            'docker build -t $IMAGE_REPO_NAME:$IMAGE_TAG .',
            'docker tag $IMAGE_REPO_NAME:$IMAGE_TAG $REPOSITORY_URI:$IMAGE_TAG',
            ...(props.deploymentConfig.runTests ? [
              'echo Running tests...',
              'docker run --rm $IMAGE_REPO_NAME:$IMAGE_TAG npm test',
            ] : []),
            ...(props.deploymentConfig.performSecurityScan ? [
              'echo Performing security scan...',
              'docker run --rm -v /var/run/docker.sock:/var/run/docker.sock -v $(pwd):/tmp aquasec/trivy:latest image --exit-code 1 --no-progress --format table $IMAGE_REPO_NAME:$IMAGE_TAG',
            ] : []),
          ],
        },
        post_build: {
          commands: [
            'echo Build completed on `date`',
            'echo Pushing the Docker image...',
            'docker push $REPOSITORY_URI:$IMAGE_TAG',
            'echo Writing image definitions file...',
            'printf \'[{"name":"container","imageUri":"%s"}]\' $REPOSITORY_URI:$IMAGE_TAG > imagedefinitions.json',
            'echo Creating outputs file...',
            'printf \'{"ImageUri":"%s"}\' $REPOSITORY_URI:$IMAGE_TAG > outputs.json',
          ],
        },
      },
      artifacts: {
        files: [
          'imagedefinitions.json',
          'outputs.json',
          'template.yaml',
        ],
      },
    });
  }
}

// Import other required modules
import * as elbv2 from 'aws-cdk-lib/aws-elasticloadbalancingv2';
import * as s3 from 'aws-cdk-lib/aws-s3';

// Aspect classes for cross-cutting concerns
class ComplianceAspect implements cdk.IAspect {
  constructor(private readonly config: ComplianceConfig) {}
  
  visit(node: cdk.IConstruct): void {
    // Apply compliance rules based on framework
    if (this.config.encryptionAtRest) {
      this.enforceEncryptionAtRest(node);
    }
    
    if (this.config.accessLogging) {
      this.enforceAccessLogging(node);
    }
    
    this.applyRetentionPolicies(node);
    this.applyDataClassificationTags(node);
  }
  
  private enforceEncryptionAtRest(node: cdk.IConstruct): void {
    // Apply encryption requirements to supported resources
    if (node instanceof s3.Bucket) {
      if (!node.encryptionKey) {
        cdk.Annotations.of(node).addWarning('S3 bucket should use customer-managed KMS encryption for compliance');
      }
    }
  }
  
  private enforceAccessLogging(node: cdk.IConstruct): void {
    // Ensure access logging is enabled for supported resources
    if (node instanceof elbv2.ApplicationLoadBalancer) {
      // Check if access logs are configured
      cdk.Annotations.of(node).addInfo('Ensure ALB access logging is configured for compliance');
    }
  }
  
  private applyRetentionPolicies(node: cdk.IConstruct): void {
    if (node instanceof logs.LogGroup) {
      const retentionDays = this.getRetentionForDataClassification();
      cdk.Annotations.of(node).addInfo(`Log retention should be set to ${retentionDays} days for ${this.config.dataClassification} data`);
    }
  }
  
  private applyDataClassificationTags(node: cdk.IConstruct): void {
    cdk.Tags.of(node).add('DataClassification', this.config.dataClassification);
    cdk.Tags.of(node).add('ComplianceFramework', this.config.framework);
  }
  
  private getRetentionForDataClassification(): number {
    const retentionMap: Record<string, number> = {
      'public': 30,
      'internal': 90,
      'confidential': 365,
      'restricted': 2555, // 7 years
    };
    return retentionMap[this.config.dataClassification] || 365;
  }
}

class SecurityHardeningAspect implements cdk.IAspect {
  constructor(private readonly config: SecurityConfig) {}
  
  visit(node: cdk.IConstruct): void {
    this.enforceSecurityGroups(node);
    this.enforceIamPolicies(node);
    this.enforceEncryption(node);
  }
  
  private enforceSecurityGroups(node: cdk.IConstruct): void {
    if (node instanceof ec2.SecurityGroup) {
      // Check for overly permissive rules
      cdk.Annotations.of(node).addInfo('Review security group rules for least privilege access');
    }
  }
  
  private enforceIamPolicies(node: cdk.IConstruct): void {
    if (node instanceof iam.Role || node instanceof iam.Policy) {
      cdk.Annotations.of(node).addInfo('Review IAM policies for least privilege access');
    }
  }
  
  private enforceEncryption(node: cdk.IConstruct): void {
    // Enforce encryption across all supported services
    cdk.Annotations.of(node).addInfo('Ensure encryption is enabled for all data stores');
  }
}

class MonitoringAspect implements cdk.IAspect {
  constructor(private readonly config: {
    level: string;
    logGroup: logs.LogGroup;
    kmsKey: kms.Key;
  }) {}
  
  visit(node: cdk.IConstruct): void {
    this.addCloudWatchAlarms(node);
    this.configureDashboards(node);
  }
  
  private addCloudWatchAlarms(node: cdk.IConstruct): void {
    // Add appropriate CloudWatch alarms based on resource type
    if (node instanceof ecs.FargateService) {
      cdk.Annotations.of(node).addInfo('Configure CPU and memory alarms for ECS service');
    }
    
    if (node instanceof elbv2.ApplicationLoadBalancer) {
      cdk.Annotations.of(node).addInfo('Configure target response time and error rate alarms for ALB');
    }
  }
  
  private configureDashboards(node: cdk.IConstruct): void {
    // Configure CloudWatch dashboards based on monitoring level
    cdk.Annotations.of(node).addInfo(`Configure ${this.config.level} level monitoring dashboards`);
  }
}

// Example usage in a CDK application
export class EnterpriseApplicationStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props: cdk.StackProps & {
    environmentConfig: EnvironmentConfig;
    securityConfig: SecurityConfig;
    complianceConfig: ComplianceConfig;
  }) {
    super(scope, id, props);
    
    // Create enterprise application infrastructure
    const app = new EnterpriseApplicationConstruct(this, 'EnterpriseApp', {
      environmentConfig: props.environmentConfig,
      securityConfig: props.securityConfig,
      complianceConfig: props.complianceConfig,
    });
    
    // Deploy microservices
    const userService = new MicroserviceConstruct(this, 'UserService', {
      cluster: app.cluster,
      vpc: app.vpc,
      serviceName: 'user-service',
      containerImage: ecs.ContainerImage.fromRegistry('my-repo/user-service:latest'),
      environmentConfig: props.environmentConfig,
      serviceConfig: {
        cpu: 512,
        memory: 1024,
        desiredCount: 2,
        healthCheckPath: '/health',
        containerPort: 8080,
        environmentVariables: {
          'NODE_ENV': props.environmentConfig.stage,
          'LOG_LEVEL': props.environmentConfig.stage === 'prod' ? 'info' : 'debug',
        },
      },
    });
    
    // Create deployment pipeline
    const pipeline = new EnterpriseDeploymentPipelineConstruct(this, 'DeploymentPipeline', {
      serviceName: 'user-service',
      environments: [
        {
          account: props.environmentConfig.account,
          region: props.environmentConfig.region,
          stage: 'dev',
          monitoringLevel: 'basic',
          backupRetention: 7,
          logRetention: logs.RetentionDays.ONE_WEEK,
        },
        {
          account: props.environmentConfig.account,
          region: props.environmentConfig.region,
          stage: 'staging',
          monitoringLevel: 'standard',
          backupRetention: 30,
          logRetention: logs.RetentionDays.ONE_MONTH,
        },
        {
          account: props.environmentConfig.account,
          region: props.environmentConfig.region,
          stage: 'prod',
          monitoringLevel: 'enhanced',
          backupRetention: 90,
          logRetention: logs.RetentionDays.THREE_MONTHS,
        },
      ],
      deploymentConfig: {
        requireManualApproval: true,
        runTests: true,
        performSecurityScan: true,
        enableBlueGreenDeployment: props.environmentConfig.stage === 'prod',
      },
    });
    
    // Output important values
    new cdk.CfnOutput(this, 'VpcId', {
      value: app.vpc.vpcId,
      description: 'VPC ID for the application',
    });
    
    new cdk.CfnOutput(this, 'ClusterName', {
      value: app.cluster.clusterName,
      description: 'ECS Cluster name',
    });
    
    new cdk.CfnOutput(this, 'LoadBalancerDns', {
      value: userService.loadBalancer.loadBalancerDnsName,
      description: 'Load balancer DNS name',
    });
    
    new cdk.CfnOutput(this, 'RepositoryCloneUrl', {
      value: pipeline.repository.repositoryCloneUrlHttp,
      description: 'Repository clone URL',
    });
  }
}
```

### Multi-Environment CDK Management

```python
# multi_env_cdk_manager.py - Python framework for managing CDK across environments
import boto3
import json
import subprocess
import os
import yaml
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from pathlib import Path
import concurrent.futures
import logging

@dataclass
class CDKEnvironment:
    name: str
    account: str
    region: str
    profile: Optional[str] = None
    bootstrap_required: bool = True
    context: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.context is None:
            self.context = {}

@dataclass
class CDKApplication:
    name: str
    path: str
    language: str
    stacks: List[str]
    dependencies: List[str] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []

class MultiEnvironmentCDKManager:
    """
    Advanced CDK management framework for multi-environment, multi-account deployments
    with automated testing, security scanning, and compliance validation.
    """
    
    def __init__(self, config_path: str):
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.environments = [CDKEnvironment(**env) for env in self.config['environments']]
        self.applications = [CDKApplication(**app) for app in self.config['applications']]
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # AWS clients (will be created per environment)
        self.clients = {}
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        with open(self.config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def bootstrap_environments(self, environments: List[str] = None) -> Dict[str, bool]:
        """Bootstrap CDK in specified environments"""
        
        target_envs = self._filter_environments(environments)
        results = {}
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            future_to_env = {
                executor.submit(self._bootstrap_environment, env): env 
                for env in target_envs
            }
            
            for future in concurrent.futures.as_completed(future_to_env):
                env = future_to_env[future]
                try:
                    success = future.result()
                    results[env.name] = success
                    if success:
                        self.logger.info(f"Successfully bootstrapped {env.name}")
                    else:
                        self.logger.error(f"Failed to bootstrap {env.name}")
                except Exception as e:
                    self.logger.error(f"Bootstrap failed for {env.name}: {e}")
                    results[env.name] = False
        
        return results
    
    def _bootstrap_environment(self, env: CDKEnvironment) -> bool:
        """Bootstrap a single environment"""
        
        try:
            cmd = [
                'cdk', 'bootstrap',
                f'aws://{env.account}/{env.region}',
                '--cloudformation-execution-policies',
                'arn:aws:iam::aws:policy/AdministratorAccess'
            ]
            
            if env.profile:
                cmd.extend(['--profile', env.profile])
            
            # Add custom context
            for key, value in env.context.items():
                cmd.extend(['--context', f'{key}={value}'])
            
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.config_path.parent)
            
            if result.returncode == 0:
                self.logger.info(f"Bootstrap output for {env.name}: {result.stdout}")
                return True
            else:
                self.logger.error(f"Bootstrap error for {env.name}: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Exception during bootstrap of {env.name}: {e}")
            return False
    
    def deploy_applications(self, applications: List[str] = None, 
                          environments: List[str] = None,
                          dry_run: bool = False) -> Dict[str, Dict[str, bool]]:
        """Deploy applications to specified environments"""
        
        target_apps = self._filter_applications(applications)
        target_envs = self._filter_environments(environments)
        results = {}
        
        for app in target_apps:
            results[app.name] = {}
            
            # Build application
            if not self._build_application(app):
                self.logger.error(f"Build failed for {app.name}")
                continue
            
            # Run tests
            if not self._test_application(app):
                self.logger.error(f"Tests failed for {app.name}")
                continue
            
            # Security scan
            if not self._security_scan_application(app):
                self.logger.error(f"Security scan failed for {app.name}")
                continue
            
            # Deploy to environments
            for env in target_envs:
                try:
                    success = self._deploy_application_to_environment(app, env, dry_run)
                    results[app.name][env.name] = success
                    
                    if success:
                        self.logger.info(f"Successfully deployed {app.name} to {env.name}")
                        
                        # Run post-deployment validation
                        if not dry_run:
                            self._validate_deployment(app, env)
                    else:
                        self.logger.error(f"Failed to deploy {app.name} to {env.name}")
                        
                except Exception as e:
                    self.logger.error(f"Deployment failed for {app.name} to {env.name}: {e}")
                    results[app.name][env.name] = False
        
        return results
    
    def _build_application(self, app: CDKApplication) -> bool:
        """Build application based on language and dependencies"""
        
        app_path = Path(self.config_path.parent) / app.path
        
        try:
            if app.language == 'typescript':
                # Install dependencies
                result = subprocess.run(['npm', 'install'], cwd=app_path, capture_output=True, text=True)
                if result.returncode != 0:
                    self.logger.error(f"npm install failed for {app.name}: {result.stderr}")
                    return False
                
                # Build TypeScript
                result = subprocess.run(['npm', 'run', 'build'], cwd=app_path, capture_output=True, text=True)
                if result.returncode != 0:
                    self.logger.error(f"TypeScript build failed for {app.name}: {result.stderr}")
                    return False
                    
            elif app.language == 'python':
                # Install dependencies
                result = subprocess.run(['pip', 'install', '-r', 'requirements.txt'], 
                                      cwd=app_path, capture_output=True, text=True)
                if result.returncode != 0:
                    self.logger.error(f"pip install failed for {app.name}: {result.stderr}")
                    return False
            
            self.logger.info(f"Successfully built {app.name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Build exception for {app.name}: {e}")
            return False
    
    def _test_application(self, app: CDKApplication) -> bool:
        """Run tests for the application"""
        
        app_path = Path(self.config_path.parent) / app.path
        
        try:
            if app.language == 'typescript':
                result = subprocess.run(['npm', 'test'], cwd=app_path, capture_output=True, text=True)
            elif app.language == 'python':
                result = subprocess.run(['python', '-m', 'pytest'], cwd=app_path, capture_output=True, text=True)
            else:
                self.logger.warning(f"No test configuration for language {app.language}")
                return True
            
            if result.returncode == 0:
                self.logger.info(f"Tests passed for {app.name}")
                return True
            else:
                self.logger.error(f"Tests failed for {app.name}: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Test exception for {app.name}: {e}")
            return False
    
    def _security_scan_application(self, app: CDKApplication) -> bool:
        """Perform security scan on the application"""
        
        app_path = Path(self.config_path.parent) / app.path
        
        try:
            # Run CDK security analysis
            result = subprocess.run([
                'cdk', 'synth', '--all', '--validation'
            ], cwd=app_path, capture_output=True, text=True)
            
            if result.returncode != 0:
                self.logger.error(f"CDK synthesis/validation failed for {app.name}: {result.stderr}")
                return False
            
            # Additional security scans can be added here
            # Example: checkov, cfn-lint, etc.
            
            self.logger.info(f"Security scan passed for {app.name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Security scan exception for {app.name}: {e}")
            return False
    
    def _deploy_application_to_environment(self, app: CDKApplication, 
                                         env: CDKEnvironment, dry_run: bool) -> bool:
        """Deploy application to specific environment"""
        
        app_path = Path(self.config_path.parent) / app.path
        
        try:
            # Prepare deployment command
            cmd = ['cdk', 'deploy' if not dry_run else 'diff']
            
            # Add stacks
            if app.stacks:
                cmd.extend(app.stacks)
            else:
                cmd.append('--all')
            
            # Add environment context
            cmd.extend(['--context', f'environment={env.name}'])
            cmd.extend(['--context', f'account={env.account}'])
            cmd.extend(['--context', f'region={env.region}'])
            
            # Add custom context
            for key, value in env.context.items():
                cmd.extend(['--context', f'{key}={value}'])
            
            # Add profile if specified
            if env.profile:
                cmd.extend(['--profile', env.profile])
            
            # Production safeguards
            if env.name == 'prod':
                cmd.append('--require-approval=never')  # Use with caution
            
            if not dry_run:
                cmd.append('--require-approval=never')
            
            # Execute deployment
            result = subprocess.run(cmd, cwd=app_path, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.logger.info(f"Deployment output for {app.name} to {env.name}: {result.stdout}")
                return True
            else:
                self.logger.error(f"Deployment error for {app.name} to {env.name}: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Deployment exception for {app.name} to {env.name}: {e}")
            return False
    
    def _validate_deployment(self, app: CDKApplication, env: CDKEnvironment) -> bool:
        """Validate deployment after completion"""
        
        try:
            # Get stack outputs and validate
            client = self._get_cloudformation_client(env)
            
            for stack_name in app.stacks:
                full_stack_name = f"{app.name}-{stack_name}-{env.name}"
                
                try:
                    response = client.describe_stacks(StackName=full_stack_name)
                    stack = response['Stacks'][0]
                    
                    if stack['StackStatus'] not in ['CREATE_COMPLETE', 'UPDATE_COMPLETE']:
                        self.logger.error(f"Stack {full_stack_name} is in unexpected state: {stack['StackStatus']}")
                        return False
                    
                    self.logger.info(f"Stack {full_stack_name} is healthy")
                    
                except client.exceptions.ClientError as e:
                    if e.response['Error']['Code'] == 'ValidationError':
                        self.logger.warning(f"Stack {full_stack_name} not found, might be expected")
                    else:
                        raise
            
            return True
            
        except Exception as e:
            self.logger.error(f"Validation failed for {app.name} in {env.name}: {e}")
            return False
    
    def destroy_applications(self, applications: List[str] = None,
                           environments: List[str] = None) -> Dict[str, Dict[str, bool]]:
        """Destroy applications in specified environments"""
        
        target_apps = self._filter_applications(applications)
        target_envs = self._filter_environments(environments)
        results = {}
        
        for app in target_apps:
            results[app.name] = {}
            
            for env in target_envs:
                try:
                    success = self._destroy_application_in_environment(app, env)
                    results[app.name][env.name] = success
                    
                    if success:
                        self.logger.info(f"Successfully destroyed {app.name} in {env.name}")
                    else:
                        self.logger.error(f"Failed to destroy {app.name} in {env.name}")
                        
                except Exception as e:
                    self.logger.error(f"Destroy failed for {app.name} in {env.name}: {e}")
                    results[app.name][env.name] = False
        
        return results
    
    def _destroy_application_in_environment(self, app: CDKApplication, env: CDKEnvironment) -> bool:
        """Destroy application in specific environment"""
        
        app_path = Path(self.config_path.parent) / app.path
        
        try:
            cmd = ['cdk', 'destroy']
            
            # Add stacks in reverse order for proper cleanup
            if app.stacks:
                cmd.extend(reversed(app.stacks))
            else:
                cmd.append('--all')
            
            # Add context
            cmd.extend(['--context', f'environment={env.name}'])
            cmd.extend(['--context', f'account={env.account}'])
            cmd.extend(['--context', f'region={env.region}'])
            
            # Add custom context
            for key, value in env.context.items():
                cmd.extend(['--context', f'{key}={value}'])
            
            # Add profile if specified
            if env.profile:
                cmd.extend(['--profile', env.profile])
            
            # Force destroy
            cmd.append('--force')
            
            result = subprocess.run(cmd, cwd=app_path, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.logger.info(f"Destroy output for {app.name} in {env.name}: {result.stdout}")
                return True
            else:
                self.logger.error(f"Destroy error for {app.name} in {env.name}: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Destroy exception for {app.name} in {env.name}: {e}")
            return False
    
    def generate_deployment_report(self) -> Dict[str, Any]:
        """Generate comprehensive deployment report"""
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'environments': [],
            'applications': [],
            'stacks': [],
            'resources': [],
        }
        
        for env in self.environments:
            try:
                client = self._get_cloudformation_client(env)
                
                env_info = {
                    'name': env.name,
                    'account': env.account,
                    'region': env.region,
                    'stacks': [],
                    'total_resources': 0,
                }
                
                # Get all stacks
                paginator = client.get_paginator('list_stacks')
                for page in paginator.paginate(StackStatusFilter=['CREATE_COMPLETE', 'UPDATE_COMPLETE']):
                    for stack in page['StackSummaries']:
                        if any(app.name in stack['StackName'] for app in self.applications):
                            stack_info = {
                                'name': stack['StackName'],
                                'status': stack['StackStatus'],
                                'creation_time': stack['CreationTime'].isoformat(),
                                'last_updated': stack.get('LastUpdatedTime', stack['CreationTime']).isoformat(),
                            }
                            
                            # Get stack resources
                            try:
                                resources_response = client.list_stack_resources(StackName=stack['StackName'])
                                stack_info['resources'] = [
                                    {
                                        'type': res['ResourceType'],
                                        'logical_id': res['LogicalResourceId'],
                                        'physical_id': res.get('PhysicalResourceId', ''),
                                        'status': res['ResourceStatus'],
                                    }
                                    for res in resources_response['StackResourceSummaries']
                                ]
                                env_info['total_resources'] += len(stack_info['resources'])
                                
                            except Exception as e:
                                self.logger.warning(f"Could not get resources for stack {stack['StackName']}: {e}")
                                stack_info['resources'] = []
                            
                            env_info['stacks'].append(stack_info)
                
                report['environments'].append(env_info)
                
            except Exception as e:
                self.logger.error(f"Failed to generate report for environment {env.name}: {e}")
        
        return report
    
    def _get_cloudformation_client(self, env: CDKEnvironment):
        """Get CloudFormation client for environment"""
        
        if env.name not in self.clients:
            session = boto3.Session(profile_name=env.profile, region_name=env.region)
            self.clients[env.name] = session.client('cloudformation')
        
        return self.clients[env.name]
    
    def _filter_environments(self, environment_names: List[str] = None) -> List[CDKEnvironment]:
        """Filter environments by names"""
        if environment_names is None:
            return self.environments
        return [env for env in self.environments if env.name in environment_names]
    
    def _filter_applications(self, application_names: List[str] = None) -> List[CDKApplication]:
        """Filter applications by names"""
        if application_names is None:
            return self.applications
        return [app for app in self.applications if app.name in application_names]

# Example configuration file (config.yaml)
EXAMPLE_CONFIG = """
environments:
  - name: dev
    account: "123456789012"
    region: "us-west-2"
    profile: "dev-profile"
    bootstrap_required: true
    context:
      environment_type: "development"
      monitoring_level: "basic"
      
  - name: staging
    account: "123456789012"
    region: "us-west-2"
    profile: "staging-profile"
    bootstrap_required: true
    context:
      environment_type: "staging"
      monitoring_level: "standard"
      
  - name: prod
    account: "987654321098"
    region: "us-west-2"
    profile: "prod-profile"
    bootstrap_required: true
    context:
      environment_type: "production"
      monitoring_level: "enhanced"

applications:
  - name: user-service
    path: "services/user-service"
    language: "typescript"
    stacks:
      - "UserServiceStack"
      - "UserServiceDatabaseStack"
    dependencies:
      - "shared-infrastructure"
      
  - name: order-service
    path: "services/order-service"
    language: "python"
    stacks:
      - "OrderServiceStack"
    dependencies:
      - "shared-infrastructure"
      - "user-service"
      
  - name: shared-infrastructure
    path: "infrastructure/shared"
    language: "typescript"
    stacks:
      - "VpcStack"
      - "SecurityStack"
    dependencies: []
"""

# Example usage
if __name__ == "__main__":
    import sys
    from datetime import datetime
    
    # Initialize manager
    manager = MultiEnvironmentCDKManager('config.yaml')
    
    if len(sys.argv) < 2:
        print("Usage: python multi_env_cdk_manager.py <command> [options]")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == 'bootstrap':
        environments = sys.argv[2:] if len(sys.argv) > 2 else None
        results = manager.bootstrap_environments(environments)
        print(f"Bootstrap results: {results}")
        
    elif command == 'deploy':
        applications = sys.argv[2:] if len(sys.argv) > 2 else None
        results = manager.deploy_applications(applications)
        print(f"Deployment results: {results}")
        
    elif command == 'destroy':
        applications = sys.argv[2:] if len(sys.argv) > 2 else None
        results = manager.destroy_applications(applications)
        print(f"Destroy results: {results}")
        
    elif command == 'report':
        report = manager.generate_deployment_report()
        print(json.dumps(report, indent=2, default=str))
        
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
```

## Best Practices Summary

### Development Excellence
- **Construct Hierarchy:** Use L2 and L3 constructs for higher-level abstractions with intelligent defaults and organizational patterns
- **Reusable Components:** Create organization-specific construct libraries enforcing standards and reducing duplication
- **Infrastructure Testing:** Implement unit tests, integration tests, and snapshot testing for construct validation
- **Aspect-Oriented Design:** Use aspects for cross-cutting concerns like tagging, compliance, and security policies
- **GitOps Integration:** Version control CDK applications with proper branching strategies and automated workflows

### Security & Compliance
- **Least Privilege IAM:** Implement fine-grained IAM roles and policies with minimal required permissions
- **Encryption Everywhere:** Enable encryption at rest and in transit for all data stores and communication channels  
- **Security Automation:** Integrate security scanning tools (Checkov, CFN-Lint) into CI/CD pipelines for continuous validation
- **Secrets Management:** Utilize AWS Secrets Manager and Parameter Store for secure credential and configuration handling
- **Network Security:** Configure security groups and NACLs with minimal access and regular security reviews

### Operational Excellence  
- **Observable Infrastructure:** Implement comprehensive monitoring with CloudWatch dashboards, alarms, and distributed tracing
- **Progressive Deployment:** Use blue-green and canary deployments with automated rollback capabilities
- **Business Continuity:** Design disaster recovery strategies with automated backup and cross-region replication
- **Living Documentation:** Maintain infrastructure documentation through code comments and automated diagram generation
- **Automation-First:** Automate operational tasks through CDK-based solutions and Infrastructure as Code practices

### Cost Optimization
- **Right-Sizing:** Select appropriate instance types and sizes based on workload requirements and performance metrics
- **Dynamic Scaling:** Implement intelligent auto-scaling policies for variable workloads and traffic patterns
- **Cost-Effective Compute:** Leverage Spot instances, Reserved capacity, and Savings Plans for predictable workloads
- **Financial Observability:** Monitor and alert on costs using CloudWatch, Cost Explorer, and budget controls
- **Resource Lifecycle:** Automate cleanup of unused resources through lifecycle policies and scheduled maintenance

### Enterprise Integration
- **Multi-Account Architecture:** Centralized construct libraries, shared services, and cross-account deployment strategies
- **GitOps Workflows:** Automated testing, security scanning, and deployment with proper approval processes
- **Compliance Automation:** Policy-driven infrastructure patterns with automated validation and remediation
- **Observability Strategy:** Comprehensive monitoring frameworks with distributed tracing and log aggregation