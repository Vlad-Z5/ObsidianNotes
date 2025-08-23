# AWS CodePipeline: Enterprise CI/CD Orchestration & Release Management Platform

> **Service Type:** Developer Tools | **Scope:** Regional | **Serverless:** Yes

## Overview

AWS CodePipeline is a comprehensive, fully managed continuous delivery service designed for enterprise-scale software delivery orchestration. It provides sophisticated workflow automation, multi-stage release management, and advanced integration capabilities with comprehensive security, compliance, and governance features for complex DevOps ecosystems.

## Enterprise CodePipeline Framework

### 1. Advanced Pipeline Orchestration Manager

```python
import boto3
import json
import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import uuid
import asyncio
from concurrent.futures import ThreadPoolExecutor
import time
import yaml

class PipelineStatus(Enum):
    SUCCEEDED = "Succeeded"
    FAILED = "Failed"
    IN_PROGRESS = "InProgress"
    STOPPED = "Stopped"
    STOPPING = "Stopping"
    SUPERSEDED = "Superseded"

class ActionCategory(Enum):
    SOURCE = "Source"
    BUILD = "Build"
    TEST = "Test"
    DEPLOY = "Deploy"
    INVOKE = "Invoke"
    APPROVAL = "Approval"

class DeploymentStrategy(Enum):
    BLUE_GREEN = "blue_green"
    CANARY = "canary"
    ROLLING = "rolling"
    ALL_AT_ONCE = "all_at_once"
    FEATURE_TOGGLE = "feature_toggle"

@dataclass
class PipelineAction:
    name: str
    category: ActionCategory
    provider: str
    version: str = "1"
    configuration: Dict[str, Any] = field(default_factory=dict)
    input_artifacts: List[str] = field(default_factory=list)
    output_artifacts: List[str] = field(default_factory=list)
    run_order: Optional[int] = None
    namespace: Optional[str] = None
    region: Optional[str] = None
    role_arn: Optional[str] = None
    timeout_minutes: Optional[int] = None

@dataclass
class PipelineStage:
    name: str
    actions: List[PipelineAction]
    on_failure: str = "STOP_PIPELINE"
    blockers: List[Dict[str, str]] = field(default_factory=list)

@dataclass
class PipelineConfig:
    name: str
    description: str
    role_arn: str
    stages: List[PipelineStage]
    artifact_store: Dict[str, Any]
    tags: Dict[str, str] = field(default_factory=dict)
    encryption_key: Optional[str] = None
    execution_mode: str = "QUEUED"
    pipeline_type: str = "V2"
    variables: List[Dict[str, str]] = field(default_factory=list)
    triggers: List[Dict[str, Any]] = field(default_factory=list)

@dataclass
class PipelineMetrics:
    total_executions: int
    successful_executions: int
    failed_executions: int
    avg_execution_duration: float
    success_rate_percent: float
    deployment_frequency: float
    lead_time_minutes: float
    mttr_minutes: float
    change_failure_rate: float
    recovery_time_minutes: float

class EnterpriseCodePipelineManager:
    """
    Enterprise-grade AWS CodePipeline manager with advanced orchestration,
    governance, compliance, and automated release management capabilities.
    """
    
    def __init__(self, region: str = 'us-east-1'):
        self.codepipeline = boto3.client('codepipeline', region_name=region)
        self.codebuild = boto3.client('codebuild', region_name=region)
        self.codedeploy = boto3.client('codedeploy', region_name=region)
        self.cloudformation = boto3.client('cloudformation', region_name=region)
        self.s3 = boto3.client('s3', region_name=region)
        self.lambda_client = boto3.client('lambda', region_name=region)
        self.sns = boto3.client('sns', region_name=region)
        self.cloudwatch = boto3.client('cloudwatch', region_name=region)
        self.events = boto3.client('events', region_name=region)
        self.iam = boto3.client('iam', region_name=region)
        self.region = region
        self.logger = self._setup_logging()
        
        # Pipeline tracking and management
        self.pipelines = {}
        self.execution_history = {}
        self.deployment_strategies = {}
        self.quality_gates = {}
        self.approval_workflows = {}
        self.compliance_rules = {}
        self.release_management = {}
        
    def _setup_logging(self) -> logging.Logger:
        """Configure structured logging for pipeline operations"""
        logger = logging.getLogger('pipeline_manager')
        logger.setLevel(logging.INFO)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - '
            '%(pipeline_name)s - %(execution_id)s - %(message)s'
        )
        
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    def create_enterprise_pipeline(self, 
                                  config: PipelineConfig,
                                  governance_config: Optional[Dict[str, Any]] = None,
                                  compliance_frameworks: Optional[List[str]] = None,
                                  deployment_strategy: Optional[DeploymentStrategy] = None) -> Dict[str, Any]:
        """Create enterprise pipeline with advanced governance and compliance"""
        
        # Validate pipeline configuration
        self._validate_pipeline_config(config)
        
        # Apply enterprise governance policies
        if governance_config:
            config = self._apply_governance_policies(config, governance_config)
        
        # Add compliance validations
        if compliance_frameworks:
            config = self._add_compliance_validations(config, compliance_frameworks)
        
        # Configure deployment strategy
        if deployment_strategy:
            config = self._configure_deployment_strategy(config, deployment_strategy)
        
        try:
            # Prepare pipeline parameters
            pipeline_params = self._prepare_pipeline_params(config)
            
            # Create CodePipeline
            response = self.codepipeline.create_pipeline(**pipeline_params)
            
            # Store pipeline configuration
            self.pipelines[config.name] = {
                'config': config,
                'pipeline_arn': response['pipeline']['name'],
                'created_at': datetime.utcnow(),
                'execution_count': 0,
                'metrics': PipelineMetrics(
                    total_executions=0,
                    successful_executions=0,
                    failed_executions=0,
                    avg_execution_duration=0.0,
                    success_rate_percent=100.0,
                    deployment_frequency=0.0,
                    lead_time_minutes=0.0,
                    mttr_minutes=0.0,
                    change_failure_rate=0.0,
                    recovery_time_minutes=0.0
                )
            }
            
            # Set up advanced monitoring
            self._setup_pipeline_monitoring(config.name)
            
            # Configure automated governance
            self._setup_automated_governance(config.name, governance_config or {})
            
            # Set up release management
            self._setup_release_management(config.name)
            
            self.logger.info(
                f"Enterprise pipeline created: {config.name}",
                extra={'pipeline_name': config.name, 'execution_id': 'create'}
            )
            
            return {
                'pipeline_name': config.name,
                'pipeline_arn': response['pipeline']['name'],
                'status': 'created',
                'governance_enabled': governance_config is not None,
                'compliance_frameworks': compliance_frameworks or [],
                'deployment_strategy': deployment_strategy.value if deployment_strategy else None,
                'monitoring_enabled': True,
                'release_management_enabled': True
            }
            
        except Exception as e:
            self.logger.error(
                f"Failed to create pipeline: {e}",
                extra={'pipeline_name': config.name, 'execution_id': 'create'}
            )
            raise
    
    def _validate_pipeline_config(self, config: PipelineConfig):
        """Validate pipeline configuration for enterprise requirements"""
        
        # Basic validation
        if not config.name or len(config.name) < 1:
            raise ValueError("Pipeline name is required")
        
        if len(config.name) > 100:
            raise ValueError("Pipeline name must be 100 characters or less")
        
        if not config.role_arn:
            raise ValueError("Service role ARN is required")
        
        if not config.stages:
            raise ValueError("At least one stage is required")
        
        # Validate stages and actions
        for stage in config.stages:
            if not stage.actions:
                raise ValueError(f"Stage '{stage.name}' must have at least one action")
            
            for action in stage.actions:
                self._validate_action_config(action)
        
        # Enterprise security validation
        self._validate_pipeline_security(config)
    
    def _validate_action_config(self, action: PipelineAction):
        """Validate individual action configuration"""
        
        if not action.name or not action.provider:
            raise ValueError("Action name and provider are required")
        
        # Validate action type specific requirements
        if action.category == ActionCategory.SOURCE:
            self._validate_source_action(action)
        elif action.category == ActionCategory.BUILD:
            self._validate_build_action(action)
        elif action.category == ActionCategory.DEPLOY:
            self._validate_deploy_action(action)
    
    def _validate_pipeline_security(self, config: PipelineConfig):
        """Validate pipeline security requirements"""
        
        # Check for encryption
        if not config.encryption_key:
            self.logger.warning("No encryption key specified for pipeline artifacts")
        
        # Validate IAM roles
        try:
            self.iam.get_role(RoleName=config.role_arn.split('/')[-1])
        except Exception as e:
            raise ValueError(f"Invalid service role ARN: {config.role_arn}")
        
        # Check for secure artifact storage
        artifact_bucket = config.artifact_store.get('location')
        if artifact_bucket:
            try:
                bucket_encryption = self.s3.get_bucket_encryption(Bucket=artifact_bucket)
                if not bucket_encryption:
                    self.logger.warning(f"Artifact bucket {artifact_bucket} is not encrypted")
            except Exception:
                self.logger.warning(f"Could not verify encryption for bucket {artifact_bucket}")
    
    def _apply_governance_policies(self, 
                                 config: PipelineConfig,
                                 governance_config: Dict[str, Any]) -> PipelineConfig:
        """Apply enterprise governance policies to pipeline"""
        
        # Add mandatory approval stages for production
        if governance_config.get('require_production_approval', True):
            config = self._add_approval_gates(config, governance_config)
        
        # Add security scanning stages
        if governance_config.get('require_security_scanning', True):
            config = self._add_security_scanning(config)
        
        # Add compliance validation stages
        if governance_config.get('require_compliance_validation', True):
            config = self._add_compliance_validation(config)
        
        # Add automated testing requirements
        if governance_config.get('require_automated_testing', True):
            config = self._add_automated_testing(config)
        
        return config
    
    def _add_approval_gates(self, 
                          config: PipelineConfig,
                          governance_config: Dict[str, Any]) -> PipelineConfig:
        """Add approval gates based on governance requirements"""
        
        approval_stages = governance_config.get('approval_stages', [])
        
        for approval_config in approval_stages:
            approval_action = PipelineAction(
                name=approval_config['name'],
                category=ActionCategory.APPROVAL,
                provider="Manual",
                configuration={
                    'NotificationArn': approval_config.get('notification_arn'),
                    'CustomData': approval_config.get('custom_data', 'Approval required'),
                    'ExternalEntityLink': approval_config.get('external_link')
                }
            )
            
            # Insert approval stage at specified position
            approval_stage = PipelineStage(
                name=f"Approval-{approval_config['name']}",
                actions=[approval_action]
            )
            
            insert_position = approval_config.get('insert_after_stage', len(config.stages))
            config.stages.insert(insert_position, approval_stage)
        
        return config
    
    async def execute_enterprise_pipeline(self, 
                                        pipeline_name: str,
                                        source_overrides: Optional[Dict[str, Any]] = None,
                                        variable_overrides: Optional[Dict[str, str]] = None,
                                        execution_mode: str = "STANDARD") -> Dict[str, Any]:
        """Execute enterprise pipeline with comprehensive monitoring"""
        
        if pipeline_name not in self.pipelines:
            raise ValueError(f"Pipeline '{pipeline_name}' not found")
        
        # Prepare execution parameters
        execution_params = {
            'pipelineName': pipeline_name
        }
        
        if source_overrides:
            execution_params['sourceRevisions'] = source_overrides
        
        if variable_overrides:
            execution_params['variableOverrides'] = [
                {'name': k, 'value': v} for k, v in variable_overrides.items()
            ]
        
        try:
            # Start pipeline execution
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.codepipeline.start_pipeline_execution(**execution_params)
            )
            
            execution_id = response['pipelineExecutionId']
            
            # Track execution
            execution_context = {
                'pipeline_name': pipeline_name,
                'execution_id': execution_id,
                'started_at': datetime.utcnow(),
                'status': PipelineStatus.IN_PROGRESS,
                'stages': [],
                'current_stage': None,
                'source_overrides': source_overrides,
                'variable_overrides': variable_overrides
            }
            
            self.execution_history[execution_id] = execution_context
            
            # Update pipeline metrics
            self.pipelines[pipeline_name]['execution_count'] += 1
            
            self.logger.info(
                f"Pipeline execution started: {execution_id}",
                extra={'pipeline_name': pipeline_name, 'execution_id': execution_id}
            )
            
            # Start monitoring task
            asyncio.create_task(
                self._monitor_pipeline_execution(execution_context)
            )
            
            return {
                'pipeline_name': pipeline_name,
                'execution_id': execution_id,
                'status': 'started',
                'monitoring_enabled': True,
                'started_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(
                f"Failed to start pipeline execution: {e}",
                extra={'pipeline_name': pipeline_name, 'execution_id': 'failed'}
            )
            raise
    
    async def _monitor_pipeline_execution(self, execution_context: Dict[str, Any]):
        """Monitor pipeline execution with real-time updates and analysis"""
        
        pipeline_name = execution_context['pipeline_name']
        execution_id = execution_context['execution_id']
        
        while True:
            try:
                # Get pipeline execution status
                response = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self.codepipeline.get_pipeline_execution(
                        pipelineName=pipeline_name,
                        pipelineExecutionId=execution_id
                    )
                )
                
                execution_info = response['pipelineExecution']
                current_status = PipelineStatus(execution_info['status'])
                
                # Update execution context
                execution_context['status'] = current_status
                execution_context['last_updated'] = datetime.utcnow()
                
                # Log status changes
                if execution_context.get('previous_status') != current_status:
                    self.logger.info(
                        f"Pipeline status: {current_status.value}",
                        extra={'pipeline_name': pipeline_name, 'execution_id': execution_id}
                    )
                    execution_context['previous_status'] = current_status
                
                # Monitor stage executions
                await self._monitor_stage_executions(execution_context)
                
                # Check if execution completed
                if current_status in [PipelineStatus.SUCCEEDED, PipelineStatus.FAILED, 
                                    PipelineStatus.STOPPED, PipelineStatus.SUPERSEDED]:
                    
                    await self._handle_pipeline_completion(
                        execution_context,
                        execution_info
                    )
                    break
                
                # Continue monitoring
                await asyncio.sleep(15)
                
            except Exception as e:
                self.logger.error(
                    f"Error monitoring pipeline execution: {e}",
                    extra={'pipeline_name': pipeline_name, 'execution_id': execution_id}
                )
                await asyncio.sleep(30)
    
    def setup_advanced_deployment_strategies(self, 
                                           pipeline_name: str) -> Dict[str, Any]:
        """Set up advanced deployment strategies for pipeline"""
        
        if pipeline_name not in self.pipelines:
            raise ValueError(f"Pipeline '{pipeline_name}' not found")
        
        deployment_strategies = {
            'blue_green_with_canary': {
                'name': 'Blue-Green with Canary Analysis',
                'description': 'Combined blue-green deployment with intelligent canary analysis',
                'stages': [
                    {
                        'name': 'deploy_blue_environment',
                        'description': 'Deploy to isolated blue environment',
                        'actions': [
                            'create_blue_infrastructure',
                            'deploy_application_blue',
                            'run_smoke_tests',
                            'validate_blue_environment'
                        ]
                    },
                    {
                        'name': 'canary_analysis',
                        'description': 'Intelligent canary traffic analysis',
                        'duration_minutes': 15,
                        'traffic_percentage': 5,
                        'success_criteria': {
                            'error_rate_threshold': 0.1,
                            'latency_p95_threshold': 500,
                            'cpu_utilization_threshold': 70,
                            'memory_utilization_threshold': 75
                        },
                        'actions': [
                            'shift_canary_traffic',
                            'monitor_canary_metrics',
                            'analyze_canary_performance',
                            'decision_canary_promotion'
                        ]
                    },
                    {
                        'name': 'progressive_rollout',
                        'description': 'Progressive traffic rollout with monitoring',
                        'phases': [
                            {'traffic_percent': 25, 'duration_minutes': 10},
                            {'traffic_percent': 50, 'duration_minutes': 15},
                            {'traffic_percent': 75, 'duration_minutes': 10},
                            {'traffic_percent': 100, 'duration_minutes': 5}
                        ]
                    },
                    {
                        'name': 'completion_and_cleanup',
                        'description': 'Complete deployment and cleanup old environment',
                        'actions': [
                            'validate_full_deployment',
                            'update_dns_records',
                            'cleanup_old_environment',
                            'send_deployment_notification'
                        ]
                    }
                ],
                'rollback_strategy': {
                    'automatic': True,
                    'triggers': [
                        'error_rate_spike',
                        'latency_degradation',
                        'resource_exhaustion',
                        'health_check_failure'
                    ],
                    'rollback_time_limit': 300  # 5 minutes
                }
            },
            'feature_flag_deployment': {
                'name': 'Feature Flag Controlled Deployment',
                'description': 'Deployment with progressive feature enablement',
                'stages': [
                    {
                        'name': 'deploy_with_flags_disabled',
                        'description': 'Deploy code with all new features disabled'
                    },
                    {
                        'name': 'progressive_feature_enablement',
                        'description': 'Gradually enable features for user segments',
                        'rollout_phases': [
                            {'segment': 'internal_users', 'percentage': 100, 'duration_hours': 2},
                            {'segment': 'beta_users', 'percentage': 100, 'duration_hours': 4},
                            {'segment': 'premium_users', 'percentage': 25, 'duration_hours': 6},
                            {'segment': 'all_users', 'percentage': 10, 'duration_hours': 12},
                            {'segment': 'all_users', 'percentage': 50, 'duration_hours': 24},
                            {'segment': 'all_users', 'percentage': 100, 'duration_hours': 0}
                        ]
                    }
                ],
                'monitoring': {
                    'feature_usage_analytics': True,
                    'user_feedback_collection': True,
                    'business_metrics_tracking': True,
                    'a_b_testing_integration': True
                },
                'rollback_method': 'feature_flag_disable'
            },
            'multi_region_deployment': {
                'name': 'Multi-Region Deployment Strategy',
                'description': 'Coordinated deployment across multiple AWS regions',
                'regions': ['us-east-1', 'us-west-2', 'eu-west-1'],
                'deployment_order': 'sequential_with_validation',
                'stages': [
                    {
                        'name': 'primary_region_deployment',
                        'region': 'us-east-1',
                        'strategy': 'blue_green',
                        'validation_duration': 30
                    },
                    {
                        'name': 'secondary_region_deployment',
                        'region': 'us-west-2',
                        'strategy': 'rolling',
                        'depends_on': 'primary_region_deployment',
                        'validation_duration': 20
                    },
                    {
                        'name': 'tertiary_region_deployment',
                        'region': 'eu-west-1',
                        'strategy': 'canary',
                        'depends_on': 'secondary_region_deployment',
                        'validation_duration': 15
                    }
                ],
                'rollback_coordination': {
                    'cross_region_rollback': True,
                    'dns_failover_integration': True,
                    'traffic_routing_update': True
                }
            }
        }
        
        # Store deployment strategies
        self.deployment_strategies[pipeline_name] = deployment_strategies
        
        # Create deployment strategy Lambda functions
        self._create_deployment_strategy_functions(pipeline_name, deployment_strategies)
        
        return deployment_strategies

# Usage Example
if __name__ == "__main__":
    # Initialize CodePipeline manager
    pipeline_manager = EnterpriseCodePipelineManager()
    
    # Configure enterprise pipeline
    source_action = PipelineAction(
        name="SourceAction",
        category=ActionCategory.SOURCE,
        provider="GitHub",
        configuration={
            "Owner": "enterprise-org",
            "Repo": "web-application",
            "Branch": "main",
            "OAuthToken": "{{resolve:secretsmanager:github-token}}"
        },
        output_artifacts=["SourceOutput"]
    )
    
    build_action = PipelineAction(
        name="BuildAction",
        category=ActionCategory.BUILD,
        provider="CodeBuild",
        configuration={
            "ProjectName": "enterprise-build-project"
        },
        input_artifacts=["SourceOutput"],
        output_artifacts=["BuildOutput"]
    )
    
    security_scan_action = PipelineAction(
        name="SecurityScanAction",
        category=ActionCategory.TEST,
        provider="CodeBuild",
        configuration={
            "ProjectName": "security-scan-project"
        },
        input_artifacts=["BuildOutput"],
        run_order=2
    )
    
    deploy_staging_action = PipelineAction(
        name="DeployToStaging",
        category=ActionCategory.DEPLOY,
        provider="CloudFormation",
        configuration={
            "ActionMode": "CREATE_UPDATE",
            "StackName": "enterprise-app-staging",
            "TemplatePath": "BuildOutput::template.yaml",
            "Capabilities": "CAPABILITY_IAM,CAPABILITY_NAMED_IAM",
            "RoleArn": "arn:aws:iam::123456789012:role/CloudFormationRole",
            "ParameterOverrides": json.dumps({
                "Environment": "staging",
                "InstanceType": "t3.medium"
            })
        },
        input_artifacts=["BuildOutput"]
    )
    
    approval_action = PipelineAction(
        name="ProductionApproval",
        category=ActionCategory.APPROVAL,
        provider="Manual",
        configuration={
            "NotificationArn": "arn:aws:sns:us-east-1:123456789012:deployment-approvals",
            "CustomData": "Please review staging deployment before promoting to production"
        }
    )
    
    deploy_production_action = PipelineAction(
        name="DeployToProduction",
        category=ActionCategory.DEPLOY,
        provider="CodeDeploy",
        configuration={
            "ApplicationName": "enterprise-web-app",
            "DeploymentGroupName": "production-servers",
            "DeploymentConfigName": "CodeDeployDefault.BlueGreenDeployment"
        },
        input_artifacts=["BuildOutput"]
    )
    
    # Define pipeline stages
    pipeline_stages = [
        PipelineStage(
            name="Source",
            actions=[source_action]
        ),
        PipelineStage(
            name="BuildAndTest",
            actions=[build_action, security_scan_action]
        ),
        PipelineStage(
            name="DeployToStaging",
            actions=[deploy_staging_action]
        ),
        PipelineStage(
            name="ProductionApproval",
            actions=[approval_action]
        ),
        PipelineStage(
            name="DeployToProduction",
            actions=[deploy_production_action]
        )
    ]
    
    # Configure pipeline
    pipeline_config = PipelineConfig(
        name="enterprise-web-app-pipeline",
        description="Enterprise web application CI/CD pipeline with advanced governance",
        role_arn="arn:aws:iam::123456789012:role/CodePipelineServiceRole",
        stages=pipeline_stages,
        artifact_store={
            "type": "S3",
            "location": "enterprise-pipeline-artifacts-123456789012",
            "encryptionKey": {
                "id": "arn:aws:kms:us-east-1:123456789012:key/12345678-1234-1234-1234-123456789012",
                "type": "KMS"
            }
        },
        encryption_key="arn:aws:kms:us-east-1:123456789012:key/12345678-1234-1234-1234-123456789012",
        tags={
            "Environment": "Production",
            "Team": "DevOps",
            "Application": "WebApp",
            "CostCenter": "Engineering"
        }
    )
    
    # Governance configuration
    governance_config = {
        "require_production_approval": True,
        "require_security_scanning": True,
        "require_compliance_validation": True,
        "require_automated_testing": True,
        "approval_stages": [
            {
                "name": "SecurityReview",
                "insert_after_stage": 1,
                "notification_arn": "arn:aws:sns:us-east-1:123456789012:security-approvals",
                "custom_data": "Security team approval required"
            }
        ]
    }
    
    # Compliance frameworks
    compliance_frameworks = ["SOX", "PCI_DSS", "GDPR"]
    
    # Create enterprise pipeline
    result = pipeline_manager.create_enterprise_pipeline(
        pipeline_config,
        governance_config,
        compliance_frameworks,
        DeploymentStrategy.BLUE_GREEN
    )
    
    print(f"Pipeline created: {result['pipeline_name']}")
    print(f"Governance enabled: {result['governance_enabled']}")
    print(f"Compliance frameworks: {result['compliance_frameworks']}")
    
    # Set up deployment strategies
    strategies = pipeline_manager.setup_advanced_deployment_strategies(
        "enterprise-web-app-pipeline"
    )
    
    print(f"Deployment strategies configured: {len(strategies)}")
    
    # Execute pipeline
    async def run_pipeline():
        execution_result = await pipeline_manager.execute_enterprise_pipeline(
            "enterprise-web-app-pipeline",
            variable_overrides={
                "BUILD_NUMBER": "123",
                "DEPLOYMENT_ENV": "production",
                "FEATURE_FLAGS": "advanced-features=true"
            }
        )
        
        print(f"Pipeline execution started: {execution_result['execution_id']}")
        return execution_result
    
    # Run the pipeline example
    import asyncio
    execution_result = asyncio.run(run_pipeline())
```

### 2. Enterprise Release Management & Governance

```python
import boto3
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import asyncio
from enum import Enum

class ReleasePhase(Enum):
    PLANNING = "planning"
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"
    ROLLBACK = "rollback"

class ComplianceFramework(Enum):
    SOX = "sox"
    PCI_DSS = "pci_dss"
    GDPR = "gdpr"
    HIPAA = "hipaa"
    SOC2 = "soc2"
    ISO27001 = "iso27001"

@dataclass
class ReleaseConfig:
    name: str
    version: str
    release_date: datetime
    environments: List[str]
    approval_requirements: Dict[str, List[str]]
    rollback_strategy: Dict[str, Any]
    compliance_requirements: List[ComplianceFramework]
    business_impact: str
    risk_assessment: Dict[str, Any]

@dataclass
class QualityGate:
    name: str
    description: str
    validation_type: str  # automated, manual, hybrid
    success_criteria: Dict[str, Any]
    failure_actions: List[str]
    timeout_minutes: int
    blocking: bool = True
    bypass_conditions: List[str] = None

class EnterpriseReleaseManager:
    """
    Enterprise release management with advanced governance,
    compliance validation, and automated quality gates.
    """
    
    def __init__(self):
        self.codepipeline = boto3.client('codepipeline')
        self.stepfunctions = boto3.client('stepfunctions')
        self.dynamodb = boto3.resource('dynamodb')
        self.sns = boto3.client('sns')
        self.cloudwatch = boto3.client('cloudwatch')
        
        self.releases = {}
        self.quality_gates = {}
        self.compliance_rules = {}
        self.approval_workflows = {}
        
    def create_enterprise_release_pipeline(self, 
                                         release_config: ReleaseConfig,
                                         quality_gates: List[QualityGate]) -> Dict[str, Any]:
        """Create enterprise release pipeline with comprehensive governance"""
        
        try:
            # Validate release configuration
            self._validate_release_config(release_config)
            
            # Set up quality gates
            gate_configs = self._setup_quality_gates(release_config.name, quality_gates)
            
            # Create release orchestration workflow
            workflow_arn = self._create_release_workflow(
                release_config,
                quality_gates
            )
            
            # Set up compliance validation
            compliance_config = self._setup_compliance_validation(
                release_config.name,
                release_config.compliance_requirements
            )
            
            # Configure release monitoring
            monitoring_config = self._setup_release_monitoring(
                release_config.name
            )
            
            # Set up automated rollback
            rollback_config = self._setup_automated_rollback(
                release_config.name,
                release_config.rollback_strategy
            )
            
            # Store release configuration
            self.releases[release_config.name] = {
                'config': release_config,
                'workflow_arn': workflow_arn,
                'quality_gates': gate_configs,
                'compliance_config': compliance_config,
                'monitoring_config': monitoring_config,
                'rollback_config': rollback_config,
                'created_at': datetime.utcnow(),
                'status': 'created'
            }
            
            return {
                'release_name': release_config.name,
                'workflow_arn': workflow_arn,
                'quality_gates_count': len(quality_gates),
                'compliance_frameworks': [f.value for f in release_config.compliance_requirements],
                'monitoring_enabled': True,
                'rollback_enabled': True,
                'status': 'created'
            }
            
        except Exception as e:
            print(f"Failed to create release pipeline: {e}")
            raise
    
    def _setup_quality_gates(self, 
                           release_name: str,
                           quality_gates: List[QualityGate]) -> Dict[str, Any]:
        """Set up comprehensive quality gates for release"""
        
        enterprise_quality_gates = {
            'security_gate': QualityGate(
                name="Security Validation Gate",
                description="Comprehensive security scanning and validation",
                validation_type="automated",
                success_criteria={
                    'critical_vulnerabilities': 0,
                    'high_vulnerabilities': 5,
                    'security_score_threshold': 85,
                    'sast_scan_passed': True,
                    'dast_scan_passed': True,
                    'dependency_scan_passed': True,
                    'infrastructure_scan_passed': True
                },
                failure_actions=[
                    'stop_pipeline',
                    'create_security_ticket',
                    'notify_security_team',
                    'block_production_deployment'
                ],
                timeout_minutes=30,
                blocking=True
            ),
            'performance_gate': QualityGate(
                name="Performance Validation Gate",
                description="Application performance and scalability validation",
                validation_type="automated",
                success_criteria={
                    'response_time_p95': 500,  # milliseconds
                    'throughput_rps': 1000,
                    'cpu_utilization_max': 70,  # percentage
                    'memory_utilization_max': 80,  # percentage
                    'error_rate_max': 0.1,  # percentage
                    'load_test_passed': True
                },
                failure_actions=[
                    'run_extended_performance_tests',
                    'notify_performance_team',
                    'create_performance_ticket'
                ],
                timeout_minutes=45,
                blocking=True
            ),
            'compliance_gate': QualityGate(
                name="Compliance Validation Gate",
                description="Regulatory compliance and audit validation",
                validation_type="hybrid",
                success_criteria={
                    'gdpr_compliance_verified': True,
                    'sox_controls_validated': True,
                    'pci_requirements_met': True,
                    'audit_trail_complete': True,
                    'data_classification_validated': True,
                    'retention_policies_applied': True
                },
                failure_actions=[
                    'stop_pipeline',
                    'notify_compliance_team',
                    'create_compliance_ticket',
                    'schedule_compliance_review'
                ],
                timeout_minutes=60,
                blocking=True
            ),
            'business_validation_gate': QualityGate(
                name="Business Validation Gate",
                description="Business stakeholder approval and validation",
                validation_type="manual",
                success_criteria={
                    'business_requirements_validated': True,
                    'user_acceptance_tests_passed': True,
                    'business_metrics_baseline_established': True,
                    'rollback_plan_approved': True,
                    'communication_plan_approved': True
                },
                failure_actions=[
                    'request_business_review',
                    'schedule_stakeholder_meeting',
                    'update_requirements'
                ],
                timeout_minutes=1440,  # 24 hours
                blocking=True,
                bypass_conditions=[
                    'emergency_deployment',
                    'security_hotfix',
                    'compliance_deadline'
                ]
            ),
            'operational_readiness_gate': QualityGate(
                name="Operational Readiness Gate",
                description="Operations team readiness and infrastructure validation",
                validation_type="automated",
                success_criteria={
                    'monitoring_configured': True,
                    'alerting_configured': True,
                    'logging_configured': True,
                    'backup_systems_ready': True,
                    'runbooks_updated': True,
                    'on_call_team_notified': True,
                    'capacity_planning_validated': True
                },
                failure_actions=[
                    'notify_operations_team',
                    'validate_infrastructure',
                    'update_monitoring_configuration'
                ],
                timeout_minutes=30,
                blocking=True
            )
        }
        
        # Add custom quality gates
        for gate in quality_gates:
            enterprise_quality_gates[gate.name.lower().replace(' ', '_')] = gate
        
        # Store quality gates configuration
        self.quality_gates[release_name] = enterprise_quality_gates
        
        return enterprise_quality_gates
    
    def _create_release_workflow(self, 
                               release_config: ReleaseConfig,
                               quality_gates: List[QualityGate]) -> str:
        """Create Step Functions workflow for release orchestration"""
        
        workflow_definition = {
            "Comment": f"Enterprise release workflow for {release_config.name}",
            "StartAt": "InitializeRelease",
            "States": {
                "InitializeRelease": {
                    "Type": "Pass",
                    "Parameters": {
                        "releaseName": release_config.name,
                        "releaseVersion": release_config.version,
                        "startTime.$": "$$.State.EnteredTime",
                        "environments": release_config.environments,
                        "businessImpact": release_config.business_impact
                    },
                    "Next": "ExecuteQualityGates"
                },
                "ExecuteQualityGates": {
                    "Type": "Map",
                    "ItemsPath": "$.qualityGates",
                    "MaxConcurrency": 3,
                    "Iterator": {
                        "StartAt": "ExecuteQualityGate",
                        "States": {
                            "ExecuteQualityGate": {
                                "Type": "Task",
                                "Resource": "arn:aws:lambda:us-east-1:123456789012:function:ExecuteQualityGate",
                                "Parameters": {
                                    "gateName.$": "$.name",
                                    "gateConfig.$": "$",
                                    "releaseContext.$": "$.releaseContext"
                                },
                                "TimeoutSeconds": 7200,
                                "Retry": [
                                    {
                                        "ErrorEquals": ["Lambda.ServiceException", "Lambda.AWSLambdaException"],
                                        "IntervalSeconds": 2,
                                        "MaxAttempts": 3,
                                        "BackoffRate": 2.0
                                    }
                                ],
                                "Catch": [
                                    {
                                        "ErrorEquals": ["States.ALL"],
                                        "Next": "QualityGateFailure",
                                        "ResultPath": "$.error"
                                    }
                                ],
                                "Next": "QualityGateSuccess"
                            },
                            "QualityGateSuccess": {
                                "Type": "Pass",
                                "End": True
                            },
                            "QualityGateFailure": {
                                "Type": "Fail",
                                "Cause": "Quality gate failed"
                            }
                        }
                    },
                    "Next": "ExecuteEnvironmentDeployments",
                    "Catch": [
                        {
                            "ErrorEquals": ["States.ALL"],
                            "Next": "ReleaseFailure",
                            "ResultPath": "$.error"
                        }
                    ]
                },
                "ExecuteEnvironmentDeployments": {
                    "Type": "Map",
                    "ItemsPath": "$.environments",
                    "MaxConcurrency": 1,  # Sequential deployment
                    "Iterator": {
                        "StartAt": "DeployToEnvironment",
                        "States": {
                            "DeployToEnvironment": {
                                "Type": "Task",
                                "Resource": "arn:aws:lambda:us-east-1:123456789012:function:DeployToEnvironment",
                                "Parameters": {
                                    "environment.$": "$",
                                    "releaseConfig.$": "$.releaseConfig"
                                },
                                "TimeoutSeconds": 3600,
                                "Next": "ValidateEnvironmentDeployment"
                            },
                            "ValidateEnvironmentDeployment": {
                                "Type": "Task",
                                "Resource": "arn:aws:lambda:us-east-1:123456789012:function:ValidateDeployment",
                                "Parameters": {
                                    "environment.$": "$",
                                    "validationCriteria.$": "$.validationCriteria"
                                },
                                "End": True
                            }
                        }
                    },
                    "Next": "ReleaseSuccess",
                    "Catch": [
                        {
                            "ErrorEquals": ["States.ALL"],
                            "Next": "InitiateRollback",
                            "ResultPath": "$.error"
                        }
                    ]
                },
                "InitiateRollback": {
                    "Type": "Task",
                    "Resource": "arn:aws:lambda:us-east-1:123456789012:function:InitiateRollback",
                    "Parameters": {
                        "releaseConfig.$": "$.releaseConfig",
                        "error.$": "$.error"
                    },
                    "Next": "ReleaseFailure"
                },
                "ReleaseSuccess": {
                    "Type": "Task",
                    "Resource": "arn:aws:lambda:us-east-1:123456789012:function:ProcessReleaseSuccess",
                    "Parameters": {
                        "releaseName": release_config.name,
                        "releaseResults.$": "$",
                        "endTime.$": "$$.State.EnteredTime"
                    },
                    "End": True
                },
                "ReleaseFailure": {
                    "Type": "Task",
                    "Resource": "arn:aws:lambda:us-east-1:123456789012:function:ProcessReleaseFailure",
                    "Parameters": {
                        "releaseName": release_config.name,
                        "error.$": "$.error",
                        "endTime.$": "$$.State.EnteredTime"
                    },
                    "End": True
                }
            },
            "TimeoutSeconds": 14400  # 4 hours
        }
        
        # Create Step Functions state machine
        response = self.stepfunctions.create_state_machine(
            name=f"release-workflow-{release_config.name}",
            definition=json.dumps(workflow_definition),
            roleArn="arn:aws:iam::123456789012:role/StepFunctionsRole",
            type="STANDARD",
            loggingConfiguration={
                'level': 'ALL',
                'includeExecutionData': True
            },
            tracingConfiguration={
                'enabled': True
            }
        )
        
        return response['stateMachineArn']

# Usage Example
if __name__ == "__main__":
    # Initialize release manager
    release_manager = EnterpriseReleaseManager()
    
    # Configure enterprise release
    release_config = ReleaseConfig(
        name="web-app-v2-1-0",
        version="2.1.0",
        release_date=datetime.utcnow() + timedelta(days=7),
        environments=["development", "staging", "production"],
        approval_requirements={
            "staging": ["tech-lead@enterprise.com"],
            "production": [
                "product-owner@enterprise.com",
                "security-lead@enterprise.com",
                "ops-manager@enterprise.com"
            ]
        },
        rollback_strategy={
            "automatic_triggers": [
                "error_rate_spike",
                "performance_degradation",
                "health_check_failure"
            ],
            "rollback_timeout_minutes": 15,
            "notification_channels": [
                "slack://ops-alerts",
                "email://oncall@enterprise.com"
            ]
        },
        compliance_requirements=[
            ComplianceFramework.SOX,
            ComplianceFramework.PCI_DSS,
            ComplianceFramework.GDPR
        ],
        business_impact="High - Customer-facing application with payment processing",
        risk_assessment={
            "risk_level": "medium",
            "impact_assessment": "medium",
            "rollback_complexity": "low",
            "testing_coverage": "high"
        }
    )
    
    # Define custom quality gates
    custom_quality_gates = [
        QualityGate(
            name="API Contract Validation",
            description="Validate API backward compatibility",
            validation_type="automated",
            success_criteria={
                "breaking_changes": 0,
                "api_version_compatibility": True,
                "schema_validation_passed": True
            },
            failure_actions=["notify_api_team", "update_api_documentation"],
            timeout_minutes=15
        )
    ]
    
    # Create enterprise release pipeline
    result = release_manager.create_enterprise_release_pipeline(
        release_config,
        custom_quality_gates
    )
    
    print(f"Release pipeline created: {result['release_name']}")
    print(f"Quality gates: {result['quality_gates_count']}")
    print(f"Compliance frameworks: {result['compliance_frameworks']}")
```

## Advanced Enterprise Use Cases

### Multi-Cloud Pipeline Orchestration
- **Hybrid Cloud Deployments**: Coordinate deployments across AWS, Azure, GCP
- **Cross-Cloud Data Synchronization**: Automated data pipeline management
- **Global Application Distribution**: Multi-region, multi-cloud release coordination
- **Cloud Migration Pipelines**: Automated workload migration orchestration

### AI/ML Pipeline Integration
- **Model Training Pipelines**: Automated ML model training and validation
- **Data Pipeline Orchestration**: ETL/ELT workflow automation
- **A/B Testing Automation**: Intelligent experiment deployment
- **Model Performance Monitoring**: Continuous model validation and rollback

### Security-First DevSecOps
- **Shift-Left Security**: Security validation at every pipeline stage
- **Compliance Automation**: Automated regulatory compliance validation
- **Zero-Trust Deployments**: Identity-based deployment authorization
- **Threat Intelligence Integration**: Real-time security threat assessment

### Enterprise Governance & Compliance
- **Multi-Tenant Pipeline Management**: Isolated tenant-specific deployments
- **Cost Attribution & Optimization**: Team/project-based cost tracking
- **Audit Trail Generation**: Comprehensive compliance audit trails
- **Policy-as-Code Enforcement**: Automated governance policy enforcement

## Enterprise DevOps Use Cases

### Application Delivery Automation
- **Web application deployment** with automated testing and intelligent rollback
- **Microservices pipelines** with service mesh integration and canary analysis
- **Mobile app CI/CD** with device farm testing and app store automation
- **Multi-environment promotion** with progressive delivery and feature flags

### Infrastructure Automation
- **Infrastructure as Code** deployments using CloudFormation, CDK, and Terraform
- **Configuration management** with Ansible, Chef, Puppet integration
- **Security compliance** with automated policy validation and drift detection
- **Multi-account deployments** across AWS Organizations with cross-account roles

### Advanced Deployment Strategies
- **Blue-green deployments** with traffic shifting validation and automated rollback
- **Canary releases** with ML-powered anomaly detection and intelligent promotion
- **Feature flag deployments** with progressive user segment rollouts
- **Cross-region deployments** for disaster recovery and global application distribution

### Container Orchestration
- **Kubernetes deployment pipelines** with Helm chart management
- **ECS/Fargate container deployments** with service discovery integration
- **Container security scanning** with vulnerability assessment and compliance
- **Multi-cluster deployments** with traffic routing and load balancing

## Core Architecture Components

### Pipeline Orchestration Engine
- **Visual Pipeline Editor**: Drag-and-drop interface for complex workflow design
- **Real-time Execution Tracking**: Stage-level monitoring with detailed progress insights
- **Pipeline Templates**: Standardized enterprise workflow templates
- **Conditional Logic**: Advanced branching and decision-making capabilities

### Integration Framework
- **Native AWS Services**: Deep integration with CodeBuild, CodeDeploy, CloudFormation
- **Third-party Platforms**: GitHub, GitLab, Jenkins, Jira, ServiceNow integration
- **Custom Actions**: Lambda-based custom action development
- **Webhook Management**: External trigger configuration and management

### Artifact Management
- **Secure Artifact Storage**: S3-based artifact storage with KMS encryption
- **Version Control**: Comprehensive artifact versioning and lineage tracking
- **Cross-Stage Artifacts**: Efficient artifact propagation between pipeline stages
- **Retention Policies**: Automated artifact lifecycle management

### Advanced Workflow Features
- **Pipeline Variables**: Dynamic variable propagation and substitution
- **Cross-Region Support**: Multi-region deployment coordination
- **CloudWatch Events**: Event-driven pipeline triggering and monitoring
- **Execution Modes**: Queued, parallel, and superseded execution strategies

## Configuration & Setup

### Enterprise Pipeline Configuration

```yaml
# Enterprise pipeline template with governance
apiVersion: codepipeline/v1
kind: Pipeline
metadata:
  name: enterprise-web-app-pipeline
  labels:
    environment: production
    team: devops
    compliance: sox-pci
spec:
  serviceRole: arn:aws:iam::123456789012:role/CodePipelineEnterpriseRole
  artifactStore:
    type: S3
    location: enterprise-pipeline-artifacts-encrypted
    encryptionKey:
      id: arn:aws:kms:us-east-1:123456789012:key/pipeline-encryption-key
      type: KMS
  stages:
    - name: Source
      actions:
        - name: SourceAction
          actionTypeId:
            category: Source
            owner: ThirdParty
            provider: GitHub
            version: '1'
          configuration:
            Owner: enterprise-org
            Repo: web-application
            Branch: main
            OAuthToken: '{{resolve:secretsmanager:github-oauth-token}}'
          outputArtifacts:
            - name: SourceOutput
    
    - name: SecurityValidation
      actions:
        - name: StaticSecurityScan
          actionTypeId:
            category: Test
            owner: AWS
            provider: CodeBuild
            version: '1'
          configuration:
            ProjectName: sast-security-scan
            EnvironmentVariables: |
              [
                {"name": "SCAN_TYPE", "value": "SAST"},
                {"name": "SEVERITY_THRESHOLD", "value": "HIGH"}
              ]
          inputArtifacts:
            - name: SourceOutput
          runOrder: 1
        
        - name: DependencySecurityScan
          actionTypeId:
            category: Test
            owner: AWS
            provider: CodeBuild
            version: '1'
          configuration:
            ProjectName: dependency-security-scan
          inputArtifacts:
            - name: SourceOutput
          runOrder: 2
    
    - name: Build
      actions:
        - name: BuildApplication
          actionTypeId:
            category: Build
            owner: AWS
            provider: CodeBuild
            version: '1'
          configuration:
            ProjectName: enterprise-build-project
            EnvironmentVariables: |
              [
                {"name": "BUILD_ENV", "value": "production"},
                {"name": "ENABLE_CACHING", "value": "true"},
                {"name": "RUN_TESTS", "value": "true"}
              ]
          inputArtifacts:
            - name: SourceOutput
          outputArtifacts:
            - name: BuildOutput
    
    - name: QualityGates
      actions:
        - name: CodeQualityGate
          actionTypeId:
            category: Invoke
            owner: AWS
            provider: Lambda
            version: '1'
          configuration:
            FunctionName: code-quality-gate-validator
            UserParameters: |
              {
                "coverage_threshold": 80,
                "code_smells_threshold": 10,
                "technical_debt_threshold": "1h"
              }
          inputArtifacts:
            - name: BuildOutput
          runOrder: 1
        
        - name: PerformanceGate
          actionTypeId:
            category: Test
            owner: AWS
            provider: CodeBuild
            version: '1'
          configuration:
            ProjectName: performance-testing
          inputArtifacts:
            - name: BuildOutput
          runOrder: 2
    
    - name: ComplianceValidation
      actions:
        - name: SOXComplianceCheck
          actionTypeId:
            category: Invoke
            owner: AWS
            provider: Lambda
            version: '1'
          configuration:
            FunctionName: sox-compliance-validator
          inputArtifacts:
            - name: BuildOutput
        
        - name: PCIComplianceCheck
          actionTypeId:
            category: Invoke
            owner: AWS
            provider: Lambda
            version: '1'
          configuration:
            FunctionName: pci-compliance-validator
          inputArtifacts:
            - name: BuildOutput
    
    - name: ProductionApproval
      actions:
        - name: SecurityTeamApproval
          actionTypeId:
            category: Approval
            owner: AWS
            provider: Manual
            version: '1'
          configuration:
            NotificationArn: arn:aws:sns:us-east-1:123456789012:security-approvals
            CustomData: 'Security team approval required for production deployment'
            ExternalEntityLink: 'https://security-dashboard.enterprise.com/approvals'
        
        - name: BusinessApproval
          actionTypeId:
            category: Approval
            owner: AWS
            provider: Manual
            version: '1'
          configuration:
            NotificationArn: arn:aws:sns:us-east-1:123456789012:business-approvals
            CustomData: 'Business stakeholder approval for production release'
          runOrder: 2
    
    - name: ProductionDeployment
      actions:
        - name: DeployToProduction
          actionTypeId:
            category: Deploy
            owner: AWS
            provider: CodeDeploy
            version: '1'
          configuration:
            ApplicationName: enterprise-web-app
            DeploymentGroupName: production-blue-green
            DeploymentConfigName: CodeDeployDefault.BlueGreenDeployment
          inputArtifacts:
            - name: BuildOutput
          region: us-east-1
        
        - name: MultiRegionDeployment
          actionTypeId:
            category: Deploy
            owner: AWS
            provider: CloudFormation
            version: '1'
          configuration:
            ActionMode: CREATE_UPDATE
            StackName: enterprise-web-app-global
            TemplatePath: BuildOutput::global-deployment-template.yaml
            Capabilities: CAPABILITY_IAM,CAPABILITY_NAMED_IAM
            RoleArn: arn:aws:iam::123456789012:role/CloudFormationCrossRegionRole
            ParameterOverrides: |
              {
                "PrimaryRegion": "us-east-1",
                "SecondaryRegions": "us-west-2,eu-west-1",
                "DeploymentStrategy": "blue-green"
              }
          inputArtifacts:
            - name: BuildOutput
          runOrder: 2
    
    - name: PostDeploymentValidation
      actions:
        - name: SmokeTests
          actionTypeId:
            category: Test
            owner: AWS
            provider: CodeBuild
            version: '1'
          configuration:
            ProjectName: smoke-tests-production
          runOrder: 1
        
        - name: HealthCheck
          actionTypeId:
            category: Invoke
            owner: AWS
            provider: Lambda
            version: '1'
          configuration:
            FunctionName: production-health-check
            UserParameters: |
              {
                "endpoint": "https://app.enterprise.com/health",
                "timeout": 30,
                "retries": 3
              }
          runOrder: 2
  
  governance:
    approvalTimeoutMinutes: 1440  # 24 hours
    rollbackOnFailure: true
    notificationChannels:
      - arn:aws:sns:us-east-1:123456789012:pipeline-notifications
      - slack://ops-alerts
    complianceFrameworks:
      - sox
      - pci-dss
      - gdpr
    auditLogging: true
    crossAccountRoles:
      - arn:aws:iam::STAGING-ACCOUNT:role/PipelineCrossAccountRole
      - arn:aws:iam::PROD-ACCOUNT:role/PipelineCrossAccountRole
```

## Enterprise Implementation Examples

### Multi-Account Enterprise Pipeline

```python
# Cross-account pipeline deployment automation
import boto3
import json
from typing import Dict, List

class MultiAccountPipelineManager:
    """Manage pipelines across multiple AWS accounts"""
    
    def __init__(self, master_account_id: str):
        self.master_account = master_account_id
        self.account_sessions = {}
        self.pipeline_configs = {}
        
    def setup_cross_account_pipeline(self, 
                                   pipeline_config: Dict[str, Any],
                                   target_accounts: List[str]) -> Dict[str, Any]:
        """Set up pipeline with cross-account deployments"""
        
        # Create pipeline in master account
        master_pipeline = self._create_master_pipeline(pipeline_config)
        
        # Set up cross-account roles and permissions
        cross_account_setup = self._setup_cross_account_permissions(target_accounts)
        
        # Configure account-specific deployment stages
        account_stages = self._configure_account_deployment_stages(
            pipeline_config, 
            target_accounts
        )
        
        return {
            'master_pipeline_arn': master_pipeline['pipelineArn'],
            'cross_account_roles': cross_account_setup,
            'account_stages': account_stages,
            'status': 'configured'
        }
    
    def _create_master_pipeline(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Create master pipeline in CI/CD account"""
        
        codepipeline = boto3.client('codepipeline')
        
        pipeline_definition = {
            'name': config['name'],
            'roleArn': config['serviceRoleArn'],
            'artifactStore': {
                'type': 'S3',
                'location': config['artifactBucket'],
                'encryptionKey': {
                    'id': config['kmsKeyArn'],
                    'type': 'KMS'
                }
            },
            'stages': self._build_cross_account_stages(config)
        }
        
        response = codepipeline.create_pipeline(pipeline=pipeline_definition)
        
        return response['pipeline']
    
    def _build_cross_account_stages(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Build stages for cross-account deployments"""
        
        stages = [
            # Source stage
            {
                'name': 'Source',
                'actions': [
                    {
                        'name': 'SourceAction',
                        'actionTypeId': {
                            'category': 'Source',
                            'owner': 'ThirdParty',
                            'provider': 'GitHub',
                            'version': '1'
                        },
                        'configuration': {
                            'Owner': config['github']['owner'],
                            'Repo': config['github']['repo'],
                            'Branch': config['github']['branch'],
                            'OAuthToken': config['github']['token']
                        },
                        'outputArtifacts': [{'name': 'SourceOutput'}]
                    }
                ]
            },
            # Build stage
            {
                'name': 'Build',
                'actions': [
                    {
                        'name': 'BuildAction',
                        'actionTypeId': {
                            'category': 'Build',
                            'owner': 'AWS',
                            'provider': 'CodeBuild',
                            'version': '1'
                        },
                        'configuration': {
                            'ProjectName': config['buildProject']
                        },
                        'inputArtifacts': [{'name': 'SourceOutput'}],
                        'outputArtifacts': [{'name': 'BuildOutput'}]
                    }
                ]
            }
        ]
        
        # Add deployment stages for each account
        for account in config['targetAccounts']:
            account_stage = {
                'name': f'Deploy-{account["name"]}',
                'actions': [
                    {
                        'name': f'Deploy-{account["name"]}',
                        'actionTypeId': {
                            'category': 'Deploy',
                            'owner': 'AWS',
                            'provider': 'CloudFormation',
                            'version': '1'
                        },
                        'configuration': {
                            'ActionMode': 'CREATE_UPDATE',
                            'StackName': f'{config["name"]}-{account["name"]}',
                            'TemplatePath': 'BuildOutput::packaged-template.yaml',
                            'Capabilities': 'CAPABILITY_IAM,CAPABILITY_NAMED_IAM',
                            'RoleArn': f'arn:aws:iam::{account["id"]}:role/CrossAccountDeploymentRole',
                            'ParameterOverrides': json.dumps(account.get('parameters', {}))
                        },
                        'inputArtifacts': [{'name': 'BuildOutput'}],
                        'region': account.get('region', 'us-east-1')
                    }
                ]
            }
            stages.append(account_stage)
        
        return stages
```

### Advanced Security Integration

```python
# Security-integrated pipeline with comprehensive scanning
import boto3
import json
from typing import Dict, List, Any

class SecureEnterpriseCodePipeline:
    """Enterprise pipeline with advanced security integration"""
    
    def __init__(self):
        self.codepipeline = boto3.client('codepipeline')
        self.codebuild = boto3.client('codebuild')
        self.lambda_client = boto3.client('lambda')
        self.inspector = boto3.client('inspector2')
        self.securityhub = boto3.client('securityhub')
        
    def create_security_integrated_pipeline(self, 
                                           pipeline_config: Dict[str, Any],
                                           security_config: Dict[str, Any]) -> Dict[str, Any]:
        """Create pipeline with comprehensive security integration"""
        
        # Create security scanning projects
        security_projects = self._create_security_scanning_projects(security_config)
        
        # Create security validation Lambda functions
        security_functions = self._create_security_validation_functions(security_config)
        
        # Build security-enhanced pipeline
        enhanced_pipeline_config = self._enhance_pipeline_with_security(
            pipeline_config,
            security_projects,
            security_functions
        )
        
        # Create the pipeline
        pipeline_response = self.codepipeline.create_pipeline(
            pipeline=enhanced_pipeline_config
        )
        
        # Set up Security Hub integration
        security_hub_integration = self._setup_security_hub_integration(
            pipeline_config['name']
        )
        
        # Configure automated security notifications
        notification_config = self._setup_security_notifications(
            pipeline_config['name'],
            security_config.get('notification_channels', [])
        )
        
        return {
            'pipeline_arn': pipeline_response['pipeline']['name'],
            'security_projects': security_projects,
            'security_functions': security_functions,
            'security_hub_integration': security_hub_integration,
            'notification_config': notification_config,
            'status': 'created_with_security'
        }
    
    def _create_security_scanning_projects(self, 
                                         security_config: Dict[str, Any]) -> Dict[str, str]:
        """Create CodeBuild projects for security scanning"""
        
        projects = {}
        
        # SAST (Static Application Security Testing)
        if security_config.get('enable_sast', True):
            sast_project = self._create_sast_project(security_config)
            projects['sast'] = sast_project
        
        # DAST (Dynamic Application Security Testing)
        if security_config.get('enable_dast', True):
            dast_project = self._create_dast_project(security_config)
            projects['dast'] = dast_project
        
        # Container Security Scanning
        if security_config.get('enable_container_scan', True):
            container_project = self._create_container_security_project(security_config)
            projects['container_security'] = container_project
        
        # Infrastructure Security Scanning
        if security_config.get('enable_infrastructure_scan', True):
            infra_project = self._create_infrastructure_security_project(security_config)
            projects['infrastructure_security'] = infra_project
        
        # Dependency Vulnerability Scanning
        if security_config.get('enable_dependency_scan', True):
            dependency_project = self._create_dependency_security_project(security_config)
            projects['dependency_security'] = dependency_project
        
        return projects
    
    def _create_sast_project(self, security_config: Dict[str, Any]) -> str:
        """Create SAST scanning CodeBuild project"""
        
        buildspec = {
            'version': 0.2,
            'phases': {
                'install': {
                    'runtime-versions': {
                        'python': 3.9,
                        'nodejs': 16
                    },
                    'commands': [
                        'pip install bandit safety semgrep',
                        'npm install -g eslint @typescript-eslint/parser @typescript-eslint/eslint-plugin',
                        'curl -L https://github.com/securecodewarrior/github-action-add-sarif/releases/download/v1.1.0/sarif-multitool-linux > sarif-multitool',
                        'chmod +x sarif-multitool'
                    ]
                },
                'pre_build': {
                    'commands': [
                        'echo "Starting SAST security scanning..."'
                    ]
                },
                'build': {
                    'commands': [
                        # Python security scanning
                        'bandit -r . -f json -o bandit-report.json || true',
                        'safety check --json --output safety-report.json || true',
                        
                        # Multi-language security scanning with Semgrep
                        'semgrep --config=auto . --json --output=semgrep-report.json || true',
                        
                        # JavaScript/TypeScript security scanning
                        'npm audit --json > npm-audit-report.json 2>/dev/null || true',
                        
                        # Convert to SARIF format for Security Hub
                        './sarif-multitool merge bandit-report.json semgrep-report.json --output-file sast-sarif-report.json',
                        
                        # Security gate validation
                        'python /opt/security-scripts/sast-gate-validator.py'
                    ]
                },
                'post_build': {
                    'commands': [
                        'echo "SAST scanning completed"',
                        'aws securityhub batch-import-findings --findings file://security-findings.json'
                    ]
                }
            },
            'artifacts': {
                'files': [
                    '**/*-report.json',
                    'sast-sarif-report.json'
                ]
            },
            'reports': {
                'security-reports': {
                    'files': [
                        'sast-sarif-report.json'
                    ],
                    'file-format': 'SARIF'
                }
            }
        }
        
        project_response = self.codebuild.create_project(
            name=f"{security_config['project_prefix']}-sast-scan",
            description="Static Application Security Testing (SAST) scanning",
            source={
                'type': 'CODEPIPELINE',
                'buildspec': json.dumps(buildspec, indent=2)
            },
            artifacts={
                'type': 'CODEPIPELINE'
            },
            environment={
                'type': 'LINUX_CONTAINER',
                'image': 'aws/codebuild/amazonlinux2-x86_64-standard:4.0',
                'computeType': 'BUILD_GENERAL1_MEDIUM',
                'privilegedMode': False,
                'environmentVariables': [
                    {
                        'name': 'SECURITY_THRESHOLD',
                        'value': security_config.get('sast_threshold', 'MEDIUM')
                    },
                    {
                        'name': 'FAIL_ON_HIGH',
                        'value': str(security_config.get('fail_on_high_severity', True))
                    }
                ]
            },
            serviceRole=security_config['codebuild_role_arn'],
            timeoutInMinutes=30,
            tags=[
                {'key': 'Purpose', 'value': 'SAST-Security-Scanning'},
                {'key': 'Compliance', 'value': 'SOX-PCI-GDPR'}
            ]
        )
        
        return project_response['project']['name']
```

## Monitoring & Observability

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