# CICD Environment Management

Advanced environment provisioning, configuration management, and infrastructure orchestration for enterprise CICD pipelines.

## Table of Contents
1. [Environment Architecture](#environment-architecture)
2. [Infrastructure as Code](#infrastructure-as-code)
3. [Configuration Management](#configuration-management)
4. [Environment Promotion](#environment-promotion)
5. [Resource Optimization](#resource-optimization)
6. [Compliance & Governance](#compliance--governance)
7. [Monitoring & Observability](#monitoring--observability)
8. [Cost Management](#cost-management)

## Environment Architecture

### Multi-Environment Strategy
```yaml
environment_strategy:
  development:
    purpose: "feature development and unit testing"
    provisioning: "on-demand"
    lifecycle: "ephemeral"
    resources:
      cpu: "2 cores"
      memory: "4GB"
      storage: "20GB"
    networking:
      isolation: "namespace"
      external_access: false
    data:
      strategy: "synthetic"
      retention: "7d"
  
  integration:
    purpose: "integration testing and API validation"
    provisioning: "persistent"
    lifecycle: "stable"
    resources:
      cpu: "4 cores"
      memory: "8GB"
      storage: "50GB"
    networking:
      isolation: "vpc"
      external_access: "limited"
    data:
      strategy: "anonymized_production_subset"
      retention: "30d"
  
  staging:
    purpose: "pre-production validation and performance testing"
    provisioning: "persistent"
    lifecycle: "stable"
    resources:
      cpu: "production-1"
      memory: "production-1"
      storage: "production-1"
    networking:
      isolation: "dedicated_vpc"
      external_access: "restricted"
    data:
      strategy: "production_mirror"
      retention: "90d"
  
  production:
    purpose: "live user traffic"
    provisioning: "persistent"
    lifecycle: "immutable"
    resources:
      cpu: "auto_scaling"
      memory: "auto_scaling"
      storage: "persistent"
    networking:
      isolation: "dedicated_vpc"
      external_access: "public"
    data:
      strategy: "live"
      retention: "indefinite"

environment_provisioning:
  infrastructure_patterns:
    container_orchestration:
      platform: "kubernetes"
      deployment_strategy: "helm"
      ingress: "nginx_ingress"
      service_mesh: "istio"
    
    cloud_resources:
      databases: "managed_services"
      caching: "redis_cluster"
      messaging: "managed_queues"
      storage: "object_storage"
    
    observability:
      metrics: "prometheus"
      logging: "elasticsearch"
      tracing: "jaeger"
      alerting: "alertmanager"
```

### Environment as Code Implementation
```terraform
# environments/modules/application-environment/main.tf
variable "environment_name" {
  description = "Environment name (dev, staging, prod)"
  type        = string
}

variable "application_name" {
  description = "Application name"
  type        = string
}

variable "resource_config" {
  description = "Resource configuration"
  type = object({
    instance_type     = string
    min_capacity      = number
    max_capacity      = number
    desired_capacity  = number
    storage_size      = number
  })
}

variable "networking_config" {
  description = "Networking configuration"
  type = object({
    vpc_cidr           = string
    availability_zones = list(string)
    enable_nat_gateway = bool
    enable_vpn_gateway = bool
  })
}

# VPC and Networking
module "vpc" {
  source = "terraform-aws-modules/vpc/aws"
  
  name = "${var.application_name}-${var.environment_name}"
  cidr = var.networking_config.vpc_cidr
  
  azs             = var.networking_config.availability_zones
  private_subnets = [for i, az in var.networking_config.availability_zones : 
                     cidrsubnet(var.networking_config.vpc_cidr, 4, i)]
  public_subnets  = [for i, az in var.networking_config.availability_zones : 
                     cidrsubnet(var.networking_config.vpc_cidr, 4, i + length(var.networking_config.availability_zones))]
  
  enable_nat_gateway = var.networking_config.enable_nat_gateway
  enable_vpn_gateway = var.networking_config.enable_vpn_gateway
  
  tags = {
    Environment   = var.environment_name
    Application   = var.application_name
    ManagedBy     = "terraform"
    CreatedDate   = formatdate("YYYY-MM-DD", timestamp())
  }
}

# Application Load Balancer
resource "aws_lb" "application" {
  name               = "${var.application_name}-${var.environment_name}-alb"
  internal           = var.environment_name == "prod" ? false : true
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = var.environment_name == "prod" ? module.vpc.public_subnets : module.vpc.private_subnets
  
  enable_deletion_protection = var.environment_name == "prod" ? true : false
  
  tags = {
    Environment = var.environment_name
    Application = var.application_name
  }
}

# EKS Cluster
module "eks" {
  source = "terraform-aws-modules/eks/aws"
  
  cluster_name    = "${var.application_name}-${var.environment_name}"
  cluster_version = "1.28"
  
  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets
  
  node_groups = {
    application = {
      desired_capacity = var.resource_config.desired_capacity
      max_capacity     = var.resource_config.max_capacity
      min_capacity     = var.resource_config.min_capacity
      
      instance_types = [var.resource_config.instance_type]
      
      k8s_labels = {
        Environment = var.environment_name
        Application = var.application_name
        NodeGroup   = "application"
      }
      
      additional_tags = {
        ExtraTag = "application-nodes"
      }
    }
  }
  
  tags = {
    Environment = var.environment_name
    Application = var.application_name
  }
}

# RDS Instance
resource "aws_db_instance" "main" {
  identifier = "${var.application_name}-${var.environment_name}-db"
  
  engine         = "postgresql"
  engine_version = "14.9"
  instance_class = var.environment_name == "prod" ? "db.r5.xlarge" : "db.t3.medium"
  
  allocated_storage     = var.resource_config.storage_size
  max_allocated_storage = var.resource_config.storage_size * 2
  storage_encrypted     = true
  
  db_name  = "${var.application_name}_${var.environment_name}"
  username = "admin"
  password = random_password.db_password.result
  
  vpc_security_group_ids = [aws_security_group.rds.id]
  db_subnet_group_name   = aws_db_subnet_group.main.name
  
  backup_retention_period = var.environment_name == "prod" ? 30 : 7
  backup_window          = "03:00-04:00"
  maintenance_window     = "sun:04:00-sun:05:00"
  
  deletion_protection = var.environment_name == "prod" ? true : false
  skip_final_snapshot = var.environment_name != "prod"
  
  tags = {
    Environment = var.environment_name
    Application = var.application_name
  }
}

# ElastiCache Redis
resource "aws_elasticache_replication_group" "main" {
  replication_group_id       = "${var.application_name}-${var.environment_name}-redis"
  description                = "Redis cluster for ${var.application_name} ${var.environment_name}"
  
  node_type                  = var.environment_name == "prod" ? "cache.r6g.large" : "cache.t3.micro"
  port                       = 6379
  parameter_group_name       = "default.redis7"
  
  num_cache_clusters         = var.environment_name == "prod" ? 3 : 1
  automatic_failover_enabled = var.environment_name == "prod" ? true : false
  
  subnet_group_name = aws_elasticache_subnet_group.main.name
  security_group_ids = [aws_security_group.redis.id]
  
  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
  
  tags = {
    Environment = var.environment_name
    Application = var.application_name
  }
}

# Outputs
output "environment_info" {
  value = {
    vpc_id          = module.vpc.vpc_id
    eks_cluster_id  = module.eks.cluster_id
    alb_dns_name    = aws_lb.application.dns_name
    database_endpoint = aws_db_instance.main.endpoint
    redis_endpoint  = aws_elasticache_replication_group.main.configuration_endpoint_address
  }
  
  sensitive = false
}
```

### Environment Pipeline Implementation
```yaml
# .github/workflows/environment-management.yml
name: Environment Management

on:
  workflow_dispatch:
    inputs:
      action:
        description: 'Action to perform'
        required: true
        type: choice
        options:
          - create
          - update
          - destroy
          - validate
      environment:
        description: 'Target environment'
        required: true
        type: choice
        options:
          - development
          - staging
          - production
      application:
        description: 'Application name'
        required: true
        type: string

jobs:
  environment-operation:
    runs-on: ubuntu-latest
    
    environment: 
      name: ${{ github.event.inputs.environment }}
      url: ${{ steps.deploy.outputs.environment_url }}
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.AWS_ROLE_ARN }}
          aws-region: us-west-2
      
      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: 1.5.0
      
      - name: Load environment configuration
        id: config
        run: |
          ENV_CONFIG=$(cat environments/${{ github.event.inputs.environment }}/config.json)
          echo "config=$ENV_CONFIG" >> $GITHUB_OUTPUT
      
      - name: Terraform Init
        working-directory: environments
        run: |
          terraform init \
            -backend-config="bucket=${{ secrets.TERRAFORM_STATE_BUCKET }}" \
            -backend-config="key=${{ github.event.inputs.application }}/${{ github.event.inputs.environment }}/terraform.tfstate" \
            -backend-config="region=us-west-2"
      
      - name: Terraform Plan
        if: ${{ github.event.inputs.action != 'destroy' }}
        working-directory: environments
        run: |
          terraform plan \
            -var="environment_name=${{ github.event.inputs.environment }}" \
            -var="application_name=${{ github.event.inputs.application }}" \
            -var-file="${{ github.event.inputs.environment }}/terraform.tfvars" \
            -out=tfplan
      
      - name: Terraform Apply
        if: ${{ github.event.inputs.action == 'create' || github.event.inputs.action == 'update' }}
        working-directory: environments
        run: |
          terraform apply -auto-approve tfplan
      
      - name: Terraform Destroy Plan
        if: ${{ github.event.inputs.action == 'destroy' }}
        working-directory: environments
        run: |
          terraform plan -destroy \
            -var="environment_name=${{ github.event.inputs.environment }}" \
            -var="application_name=${{ github.event.inputs.application }}" \
            -var-file="${{ github.event.inputs.environment }}/terraform.tfvars" \
            -out=destroy-plan
      
      - name: Terraform Destroy
        if: ${{ github.event.inputs.action == 'destroy' }}
        working-directory: environments
        run: |
          terraform apply -auto-approve destroy-plan
      
      - name: Configure Kubernetes
        if: ${{ github.event.inputs.action != 'destroy' }}
        run: |
          aws eks update-kubeconfig --region us-west-2 --name ${{ github.event.inputs.application }}-${{ github.event.inputs.environment }}
      
      - name: Deploy application manifests
        if: ${{ github.event.inputs.action == 'create' || github.event.inputs.action == 'update' }}
        run: |
          helm upgrade --install ${{ github.event.inputs.application }} \
            charts/${{ github.event.inputs.application }} \
            --namespace ${{ github.event.inputs.application }}-${{ github.event.inputs.environment }} \
            --create-namespace \
            --values charts/${{ github.event.inputs.application }}/values-${{ github.event.inputs.environment }}.yaml \
            --set image.tag=${{ github.sha }} \
            --wait --timeout 10m
      
      - name: Run environment validation tests
        if: ${{ github.event.inputs.action != 'destroy' }}
        run: |
          npm run test:environment:${{ github.event.inputs.environment }}
      
      - name: Update environment registry
        if: ${{ github.event.inputs.action != 'destroy' }}
        run: |
          curl -X POST "${{ secrets.ENVIRONMENT_REGISTRY_URL }}/environments" \
            -H "Authorization: Bearer ${{ secrets.ENVIRONMENT_REGISTRY_TOKEN }}" \
            -H "Content-Type: application/json" \
            -d '{
              "name": "${{ github.event.inputs.application }}-${{ github.event.inputs.environment }}",
              "status": "active",
              "version": "${{ github.sha }}",
              "created_at": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'",
              "metadata": {
                "environment": "${{ github.event.inputs.environment }}",
                "application": "${{ github.event.inputs.application }}",
                "terraform_state": "${{ github.event.inputs.application }}/${{ github.event.inputs.environment }}/terraform.tfstate"
              }
            }'
```

## Real-World Enterprise Use Cases

### Use Case 1: Multi-Cloud Environment Orchestration
```python
#!/usr/bin/env python3
# multi_cloud_environment_manager.py
# Enterprise multi-cloud environment management and orchestration

import asyncio
import json
import logging
import yaml
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any, Union
from enum import Enum
import boto3
from azure.identity import DefaultAzureCredential
from azure.mgmt.resource import ResourceManagementClient
from google.cloud import resource_manager
from kubernetes import client, config

class CloudProvider(Enum):
    AWS = "aws"
    AZURE = "azure"
    GCP = "gcp"
    ON_PREMISE = "on_premise"

class EnvironmentType(Enum):
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"
    DISASTER_RECOVERY = "disaster_recovery"

class ComplianceFramework(Enum):
    SOX = "sox"
    HIPAA = "hipaa"
    PCI_DSS = "pci_dss"
    GDPR = "gdpr"
    ISO_27001 = "iso_27001"
    FEDRAMP = "fedramp"

@dataclass
class EnvironmentSpec:
    name: str
    environment_type: EnvironmentType
    cloud_provider: CloudProvider
    region: str
    resource_requirements: Dict[str, Any]
    networking: Dict[str, Any]
    security_config: Dict[str, Any]
    compliance_frameworks: List[ComplianceFramework]
    data_classification: str
    backup_retention_days: int
    auto_scaling: bool = True
    high_availability: bool = True
    disaster_recovery: bool = False

@dataclass
class EnvironmentStatus:
    name: str
    status: str  # provisioning, active, updating, destroying, error
    health_score: float  # 0-100
    resource_utilization: Dict[str, float]
    cost_current_month: float
    last_updated: datetime
    alerts: List[str]
    compliance_status: Dict[str, bool]

class MultiCloudEnvironmentManager:
    def __init__(self, config_path: str):
        self.config = self._load_configuration(config_path)
        self.logger = self._setup_logging()
        self.cloud_clients = self._initialize_cloud_clients()
        self.environments: Dict[str, EnvironmentSpec] = {}
        self.environment_status: Dict[str, EnvironmentStatus] = {}
        
    def _load_configuration(self, config_path: str) -> Dict:
        """Load multi-cloud configuration"""
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('environment_manager.log'),
                logging.StreamHandler()
            ]
        )
        return logging.getLogger('MultiCloudEnvironmentManager')
    
    def _initialize_cloud_clients(self) -> Dict[str, Any]:
        """Initialize cloud provider clients"""
        clients = {}
        
        # AWS clients
        if 'aws' in self.config['cloud_providers']:
            aws_config = self.config['cloud_providers']['aws']
            clients['aws'] = {
                'ec2': boto3.client('ec2', region_name=aws_config['default_region']),
                'eks': boto3.client('eks', region_name=aws_config['default_region']),
                'rds': boto3.client('rds', region_name=aws_config['default_region']),
                'cloudformation': boto3.client('cloudformation', region_name=aws_config['default_region']),
                'cost_explorer': boto3.client('ce', region_name='us-east-1'),
                'cloudwatch': boto3.client('cloudwatch', region_name=aws_config['default_region'])
            }
        
        # Azure clients
        if 'azure' in self.config['cloud_providers']:
            azure_credential = DefaultAzureCredential()
            azure_config = self.config['cloud_providers']['azure']
            clients['azure'] = {
                'resource_manager': ResourceManagementClient(
                    azure_credential, 
                    azure_config['subscription_id']
                )
            }
        
        # GCP clients
        if 'gcp' in self.config['cloud_providers']:
            clients['gcp'] = {
                'resource_manager': resource_manager.ProjectsClient()
            }
        
        return clients
    
    async def provision_environment(self, environment_spec: EnvironmentSpec) -> bool:
        """Provision a new environment across specified cloud provider"""
        try:
            self.logger.info(f"Starting provisioning of {environment_spec.name} environment")
            
            # Validate environment specification
            if not await self._validate_environment_spec(environment_spec):
                raise ValueError("Environment specification validation failed")
            
            # Check compliance requirements
            if not await self._validate_compliance_requirements(environment_spec):
                raise ValueError("Compliance requirements not met")
            
            # Create environment tracking
            self.environments[environment_spec.name] = environment_spec
            self.environment_status[environment_spec.name] = EnvironmentStatus(
                name=environment_spec.name,
                status="provisioning",
                health_score=0.0,
                resource_utilization={},
                cost_current_month=0.0,
                last_updated=datetime.utcnow(),
                alerts=[],
                compliance_status={}
            )
            
            # Provision based on cloud provider
            success = False
            if environment_spec.cloud_provider == CloudProvider.AWS:
                success = await self._provision_aws_environment(environment_spec)
            elif environment_spec.cloud_provider == CloudProvider.AZURE:
                success = await self._provision_azure_environment(environment_spec)
            elif environment_spec.cloud_provider == CloudProvider.GCP:
                success = await self._provision_gcp_environment(environment_spec)
            elif environment_spec.cloud_provider == CloudProvider.ON_PREMISE:
                success = await self._provision_on_premise_environment(environment_spec)
            
            if success:
                # Setup monitoring and alerting
                await self._setup_environment_monitoring(environment_spec)
                
                # Configure backup and disaster recovery
                if environment_spec.disaster_recovery:
                    await self._setup_disaster_recovery(environment_spec)
                
                # Apply compliance controls
                await self._apply_compliance_controls(environment_spec)
                
                # Update status
                self.environment_status[environment_spec.name].status = "active"
                self.environment_status[environment_spec.name].health_score = 100.0
                
                self.logger.info(f"Successfully provisioned {environment_spec.name} environment")
                return True
            else:
                self.environment_status[environment_spec.name].status = "error"
                self.logger.error(f"Failed to provision {environment_spec.name} environment")
                return False
                
        except Exception as e:
            self.logger.error(f"Error provisioning environment {environment_spec.name}: {e}")
            if environment_spec.name in self.environment_status:
                self.environment_status[environment_spec.name].status = "error"
                self.environment_status[environment_spec.name].alerts.append(str(e))
            return False
    
    async def _provision_aws_environment(self, spec: EnvironmentSpec) -> bool:
        """Provision AWS environment using CloudFormation"""
        self.logger.info(f"Provisioning AWS environment: {spec.name}")
        
        try:
            # Create CloudFormation template
            template = self._generate_aws_cloudformation_template(spec)
            
            # Deploy stack
            cf_client = self.cloud_clients['aws']['cloudformation']
            
            stack_name = f"{spec.name}-infrastructure"
            
            response = cf_client.create_stack(
                StackName=stack_name,
                TemplateBody=json.dumps(template),
                Capabilities=['CAPABILITY_IAM', 'CAPABILITY_NAMED_IAM'],
                Tags=[
                    {'Key': 'Environment', 'Value': spec.name},
                    {'Key': 'Type', 'Value': spec.environment_type.value},
                    {'Key': 'ManagedBy', 'Value': 'MultiCloudEnvironmentManager'},
                    {'Key': 'ComplianceFrameworks', 'Value': ','.join([f.value for f in spec.compliance_frameworks])}
                ]
            )
            
            stack_id = response['StackId']
            self.logger.info(f"CloudFormation stack created: {stack_id}")
            
            # Wait for stack creation to complete
            waiter = cf_client.get_waiter('stack_create_complete')
            await asyncio.get_event_loop().run_in_executor(
                None, 
                lambda: waiter.wait(
                    StackName=stack_name,
                    WaiterConfig={'Delay': 30, 'MaxAttempts': 60}
                )
            )
            
            # Get stack outputs
            stack_info = cf_client.describe_stacks(StackName=stack_name)
            outputs = {output['OutputKey']: output['OutputValue'] 
                      for output in stack_info['Stacks'][0].get('Outputs', [])}
            
            # Setup Kubernetes cluster if required
            if spec.resource_requirements.get('kubernetes', False):
                await self._setup_eks_cluster(spec, outputs)
            
            return True
            
        except Exception as e:
            self.logger.error(f"AWS provisioning failed: {e}")
            return False
    
    def _generate_aws_cloudformation_template(self, spec: EnvironmentSpec) -> Dict:
        """Generate CloudFormation template based on environment specification"""
        template = {
            "AWSTemplateFormatVersion": "2010-09-09",
            "Description": f"Infrastructure for {spec.name} environment",
            "Parameters": {
                "EnvironmentName": {
                    "Type": "String",
                    "Default": spec.name
                }
            },
            "Resources": {},
            "Outputs": {}
        }
        
        # VPC and Networking
        vpc_cidr = spec.networking.get('vpc_cidr', '10.0.0.0/16')
        template['Resources']['VPC'] = {
            "Type": "AWS::EC2::VPC",
            "Properties": {
                "CidrBlock": vpc_cidr,
                "EnableDnsHostnames": True,
                "EnableDnsSupport": True,
                "Tags": [
                    {"Key": "Name", "Value": f"{spec.name}-vpc"},
                    {"Key": "Environment", "Value": spec.name}
                ]
            }
        }
        
        # Internet Gateway (for public environments)
        if spec.environment_type != EnvironmentType.DEVELOPMENT:
            template['Resources']['InternetGateway'] = {
                "Type": "AWS::EC2::InternetGateway",
                "Properties": {
                    "Tags": [
                        {"Key": "Name", "Value": f"{spec.name}-igw"},
                        {"Key": "Environment", "Value": spec.name}
                    ]
                }
            }
            
            template['Resources']['AttachGateway'] = {
                "Type": "AWS::EC2::VPCGatewayAttachment",
                "Properties": {
                    "VpcId": {"Ref": "VPC"},
                    "InternetGatewayId": {"Ref": "InternetGateway"}
                }
            }
        
        # Subnets
        availability_zones = spec.networking.get('availability_zones', ['a', 'b'])
        for i, az_suffix in enumerate(availability_zones):
            # Private subnet
            template['Resources'][f'PrivateSubnet{i+1}'] = {
                "Type": "AWS::EC2::Subnet",
                "Properties": {
                    "VpcId": {"Ref": "VPC"},
                    "CidrBlock": f"10.0.{i+1}.0/24",
                    "AvailabilityZone": f"{spec.region}{az_suffix}",
                    "Tags": [
                        {"Key": "Name", "Value": f"{spec.name}-private-subnet-{i+1}"},
                        {"Key": "Environment", "Value": spec.name}
                    ]
                }
            }
            
            # Public subnet (if needed)
            if spec.environment_type != EnvironmentType.DEVELOPMENT:
                template['Resources'][f'PublicSubnet{i+1}'] = {
                    "Type": "AWS::EC2::Subnet",
                    "Properties": {
                        "VpcId": {"Ref": "VPC"},
                        "CidrBlock": f"10.0.{i+10}.0/24",
                        "AvailabilityZone": f"{spec.region}{az_suffix}",
                        "MapPublicIpOnLaunch": True,
                        "Tags": [
                            {"Key": "Name", "Value": f"{spec.name}-public-subnet-{i+1}"},
                            {"Key": "Environment", "Value": spec.name}
                        ]
                    }
                }
        
        # Security Groups
        template['Resources']['ApplicationSecurityGroup'] = {
            "Type": "AWS::EC2::SecurityGroup",
            "Properties": {
                "GroupDescription": f"Security group for {spec.name} application",
                "VpcId": {"Ref": "VPC"},
                "SecurityGroupIngress": self._generate_security_group_rules(spec),
                "Tags": [
                    {"Key": "Name", "Value": f"{spec.name}-app-sg"},
                    {"Key": "Environment", "Value": spec.name}
                ]
            }
        }
        
        # RDS Database (if required)
        if spec.resource_requirements.get('database', False):
            template['Resources']['DatabaseSubnetGroup'] = {
                "Type": "AWS::RDS::DBSubnetGroup",
                "Properties": {
                    "DBSubnetGroupDescription": f"Subnet group for {spec.name} database",
                    "SubnetIds": [
                        {"Ref": f"PrivateSubnet{i+1}"} 
                        for i in range(len(availability_zones))
                    ],
                    "Tags": [
                        {"Key": "Environment", "Value": spec.name}
                    ]
                }
            }
            
            db_config = spec.resource_requirements.get('database_config', {})
            template['Resources']['Database'] = {
                "Type": "AWS::RDS::DBInstance",
                "Properties": {
                    "DBInstanceClass": db_config.get('instance_class', 'db.t3.medium'),
                    "Engine": db_config.get('engine', 'postgres'),
                    "EngineVersion": db_config.get('engine_version', '13.7'),
                    "AllocatedStorage": db_config.get('storage_gb', 100),
                    "StorageType": "gp2",
                    "StorageEncrypted": True,
                    "DBSubnetGroupName": {"Ref": "DatabaseSubnetGroup"},
                    "VPCSecurityGroups": [{"Ref": "ApplicationSecurityGroup"}],
                    "BackupRetentionPeriod": spec.backup_retention_days,
                    "MultiAZ": spec.high_availability,
                    "Tags": [
                        {"Key": "Environment", "Value": spec.name}
                    ]
                }
            }
        
        # EKS Cluster (if required)
        if spec.resource_requirements.get('kubernetes', False):
            template['Resources']['EKSServiceRole'] = {
                "Type": "AWS::IAM::Role",
                "Properties": {
                    "AssumeRolePolicyDocument": {
                        "Version": "2012-10-17",
                        "Statement": [{
                            "Effect": "Allow",
                            "Principal": {"Service": "eks.amazonaws.com"},
                            "Action": "sts:AssumeRole"
                        }]
                    },
                    "ManagedPolicyArns": [
                        "arn:aws:iam::aws:policy/AmazonEKSClusterPolicy"
                    ]
                }
            }
            
            template['Resources']['EKSCluster'] = {
                "Type": "AWS::EKS::Cluster",
                "Properties": {
                    "Name": f"{spec.name}-cluster",
                    "Version": "1.28",
                    "RoleArn": {"Fn::GetAtt": ["EKSServiceRole", "Arn"]},
                    "ResourcesVpcConfig": {
                        "SubnetIds": [
                            {"Ref": f"PrivateSubnet{i+1}"} 
                            for i in range(len(availability_zones))
                        ]
                    },
                    "Logging": {
                        "EnabledTypes": [
                            {"Type": "api"},
                            {"Type": "audit"},
                            {"Type": "authenticator"},
                            {"Type": "controllerManager"},
                            {"Type": "scheduler"}
                        ]
                    },
                    "Tags": [
                        {"Key": "Environment", "Value": spec.name}
                    ]
                }
            }
        
        # Outputs
        template['Outputs']['VpcId'] = {
            "Description": "VPC ID",
            "Value": {"Ref": "VPC"},
            "Export": {"Name": f"{spec.name}-vpc-id"}
        }
        
        if spec.resource_requirements.get('kubernetes', False):
            template['Outputs']['EKSClusterName'] = {
                "Description": "EKS Cluster Name",
                "Value": {"Ref": "EKSCluster"},
                "Export": {"Name": f"{spec.name}-eks-cluster-name"}
            }
        
        return template
    
    def _generate_security_group_rules(self, spec: EnvironmentSpec) -> List[Dict]:
        """Generate security group rules based on environment type and compliance"""
        rules = []
        
        # Base rules for all environments
        rules.append({
            "IpProtocol": "tcp",
            "FromPort": 443,
            "ToPort": 443,
            "CidrIp": "0.0.0.0/0",
            "Description": "HTTPS traffic"
        })
        
        # Development environments - more permissive
        if spec.environment_type == EnvironmentType.DEVELOPMENT:
            rules.extend([
                {
                    "IpProtocol": "tcp",
                    "FromPort": 80,
                    "ToPort": 80,
                    "CidrIp": "10.0.0.0/8",
                    "Description": "HTTP traffic from private networks"
                },
                {
                    "IpProtocol": "tcp",
                    "FromPort": 22,
                    "ToPort": 22,
                    "CidrIp": "10.0.0.0/8",
                    "Description": "SSH access from private networks"
                }
            ])
        
        # Production environments - restricted
        elif spec.environment_type == EnvironmentType.PRODUCTION:
            # Only allow specific ports and sources
            rules.append({
                "IpProtocol": "tcp",
                "FromPort": 80,
                "ToPort": 80,
                "SourceSecurityGroupId": "${LoadBalancerSecurityGroup}",
                "Description": "HTTP from load balancer only"
            })
        
        # Compliance-specific rules
        if ComplianceFramework.PCI_DSS in spec.compliance_frameworks:
            # PCI DSS requires encrypted communications
            rules = [rule for rule in rules if rule.get('FromPort') != 80]  # Remove HTTP
        
        if ComplianceFramework.HIPAA in spec.compliance_frameworks:
            # HIPAA requires additional security controls
            rules.append({
                "IpProtocol": "tcp",
                "FromPort": 8443,
                "ToPort": 8443,
                "CidrIp": spec.networking.get('allowed_cidrs', ['10.0.0.0/8'])[0],
                "Description": "Secure healthcare API access"
            })
        
        return rules
    
    async def _setup_eks_cluster(self, spec: EnvironmentSpec, cf_outputs: Dict):
        """Setup and configure EKS cluster with required components"""
        self.logger.info(f"Setting up EKS cluster for {spec.name}")
        
        try:
            cluster_name = cf_outputs.get('EKSClusterName')
            if not cluster_name:
                raise ValueError("EKS cluster name not found in CloudFormation outputs")
            
            # Update kubeconfig
            eks_client = self.cloud_clients['aws']['eks']
            cluster_info = eks_client.describe_cluster(name=cluster_name)
            
            # Configure kubectl
            config.load_incluster_config()
            
            # Install essential Kubernetes components
            await self._install_k8s_components(spec, cluster_name)
            
            return True
            
        except Exception as e:
            self.logger.error(f"EKS setup failed: {e}")
            return False
    
    async def _install_k8s_components(self, spec: EnvironmentSpec, cluster_name: str):
        """Install essential Kubernetes components"""
        components = [
            'nginx-ingress-controller',
            'cert-manager',
            'external-dns',
            'cluster-autoscaler'
        ]
        
        # Compliance-specific components
        if any(framework in [ComplianceFramework.SOX, ComplianceFramework.HIPAA] 
               for framework in spec.compliance_frameworks):
            components.extend([
                'falco',  # Runtime security monitoring
                'opa-gatekeeper',  # Policy enforcement
                'kube-bench'  # Security benchmarking
            ])
        
        for component in components:
            try:
                await self._install_helm_chart(component, spec.name)
                self.logger.info(f"Installed {component} in {cluster_name}")
            except Exception as e:
                self.logger.error(f"Failed to install {component}: {e}")
    
    async def manage_environment_lifecycle(self):
        """Continuous environment lifecycle management"""
        while True:
            try:
                # Check all environments
                for env_name, env_spec in self.environments.items():
                    # Update environment status
                    await self._update_environment_status(env_name)
                    
                    # Perform health checks
                    health_score = await self._calculate_environment_health(env_name)
                    self.environment_status[env_name].health_score = health_score
                    
                    # Check for cost optimization opportunities
                    await self._optimize_environment_costs(env_name)
                    
                    # Validate compliance
                    compliance_status = await self._check_compliance_status(env_name)
                    self.environment_status[env_name].compliance_status = compliance_status
                    
                    # Handle environment-specific lifecycle
                    if env_spec.environment_type == EnvironmentType.DEVELOPMENT:
                        await self._manage_ephemeral_environment(env_name)
                    
                # Generate environment report
                await self._generate_environment_report()
                
                # Wait before next cycle
                await asyncio.sleep(300)  # 5 minutes
                
            except Exception as e:
                self.logger.error(f"Environment lifecycle management error: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retry
    
    async def get_environment_status(self, environment_name: str) -> Optional[EnvironmentStatus]:
        """Get current status of an environment"""
        return self.environment_status.get(environment_name)
    
    async def get_all_environments_status(self) -> Dict[str, EnvironmentStatus]:
        """Get status of all managed environments"""
        return self.environment_status.copy()
    
    # Helper methods (simplified implementations)
    async def _validate_environment_spec(self, spec: EnvironmentSpec) -> bool:
        return True  # Implementation would validate the specification
    
    async def _validate_compliance_requirements(self, spec: EnvironmentSpec) -> bool:
        return True  # Implementation would check compliance requirements
    
    async def _provision_azure_environment(self, spec: EnvironmentSpec) -> bool:
        return True  # Implementation would provision Azure resources
    
    async def _provision_gcp_environment(self, spec: EnvironmentSpec) -> bool:
        return True  # Implementation would provision GCP resources
    
    async def _provision_on_premise_environment(self, spec: EnvironmentSpec) -> bool:
        return True  # Implementation would provision on-premise resources
    
    async def _setup_environment_monitoring(self, spec: EnvironmentSpec):
        pass  # Implementation would setup monitoring
    
    async def _setup_disaster_recovery(self, spec: EnvironmentSpec):
        pass  # Implementation would setup DR
    
    async def _apply_compliance_controls(self, spec: EnvironmentSpec):
        pass  # Implementation would apply compliance controls
    
    async def _install_helm_chart(self, chart_name: str, namespace: str):
        pass  # Implementation would install Helm charts
    
    async def _update_environment_status(self, env_name: str):
        pass  # Implementation would update status
    
    async def _calculate_environment_health(self, env_name: str) -> float:
        return 100.0  # Implementation would calculate health score
    
    async def _optimize_environment_costs(self, env_name: str):
        pass  # Implementation would optimize costs
    
    async def _check_compliance_status(self, env_name: str) -> Dict[str, bool]:
        return {}  # Implementation would check compliance
    
    async def _manage_ephemeral_environment(self, env_name: str):
        pass  # Implementation would manage ephemeral environments
    
    async def _generate_environment_report(self):
        pass  # Implementation would generate reports

# Example usage
if __name__ == "__main__":
    async def main():
        # Initialize environment manager
        manager = MultiCloudEnvironmentManager('multi_cloud_config.yaml')
        
        # Define environment specifications
        dev_env = EnvironmentSpec(
            name="myapp-dev",
            environment_type=EnvironmentType.DEVELOPMENT,
            cloud_provider=CloudProvider.AWS,
            region="us-west-2",
            resource_requirements={
                "kubernetes": True,
                "database": True,
                "database_config": {
                    "engine": "postgres",
                    "instance_class": "db.t3.micro"
                }
            },
            networking={
                "vpc_cidr": "10.1.0.0/16",
                "availability_zones": ["a", "b"]
            },
            security_config={
                "encryption_at_rest": True,
                "encryption_in_transit": True
            },
            compliance_frameworks=[ComplianceFramework.SOX],
            data_classification="internal",
            backup_retention_days=7,
            auto_scaling=True,
            high_availability=False,
            disaster_recovery=False
        )
        
        prod_env = EnvironmentSpec(
            name="myapp-prod",
            environment_type=EnvironmentType.PRODUCTION,
            cloud_provider=CloudProvider.AWS,
            region="us-west-2",
            resource_requirements={
                "kubernetes": True,
                "database": True,
                "database_config": {
                    "engine": "postgres",
                    "instance_class": "db.r5.xlarge"
                }
            },
            networking={
                "vpc_cidr": "10.0.0.0/16",
                "availability_zones": ["a", "b", "c"]
            },
            security_config={
                "encryption_at_rest": True,
                "encryption_in_transit": True
            },
            compliance_frameworks=[ComplianceFramework.SOX, ComplianceFramework.PCI_DSS],
            data_classification="confidential",
            backup_retention_days=90,
            auto_scaling=True,
            high_availability=True,
            disaster_recovery=True
        )
        
        # Provision environments
        dev_success = await manager.provision_environment(dev_env)
        prod_success = await manager.provision_environment(prod_env)
        
        if dev_success and prod_success:
            print("✅ All environments provisioned successfully")
            
            # Start lifecycle management
            lifecycle_task = asyncio.create_task(manager.manage_environment_lifecycle())
            
            # Get environment status
            await asyncio.sleep(10)
            status = await manager.get_all_environments_status()
            for env_name, env_status in status.items():
                print(f"{env_name}: {env_status.status} (Health: {env_status.health_score})")
        
    asyncio.run(main())
```

This comprehensive CICD Environment Management guide provides enterprise-ready patterns for managing infrastructure and application environments through code, ensuring consistency, scalability, and compliance across all deployment targets with advanced multi-cloud orchestration capabilities.