# AWS CodeDeploy: Enterprise Deployment Automation & Risk Management Platform

> **Service Type:** Deployment Automation | **Tier:** CI/CD and Automation | **Global/Regional:** Regional

## Overview

AWS CodeDeploy is a comprehensive, fully managed deployment service designed for enterprise-scale application delivery across diverse compute platforms. It provides sophisticated deployment strategies, automated risk management, and zero-downtime deployment capabilities with advanced monitoring, rollback mechanisms, and enterprise governance features.

## Enterprise CodeDeploy Framework

### 1. Advanced Deployment Orchestration Manager

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

class ComputePlatform(Enum):
    SERVER = "Server"  # EC2/On-premises
    LAMBDA = "Lambda"
    ECS = "ECS"

class DeploymentStrategy(Enum):
    BLUE_GREEN = "blue_green"
    ROLLING = "rolling"
    CANARY = "canary"
    ALL_AT_ONCE = "all_at_once"
    FEATURE_TOGGLE = "feature_toggle"

class DeploymentStatus(Enum):
    CREATED = "Created"
    QUEUED = "Queued"
    IN_PROGRESS = "InProgress"
    SUCCEEDED = "Succeeded"
    FAILED = "Failed"
    STOPPED = "Stopped"
    READY = "Ready"

@dataclass
class DeploymentConfig:
    name: str
    compute_platform: ComputePlatform
    strategy: DeploymentStrategy
    minimum_healthy_hosts: Optional[Dict[str, Any]] = None
    traffic_routing_config: Optional[Dict[str, Any]] = None
    blue_green_config: Optional[Dict[str, Any]] = None
    tags: Dict[str, str] = field(default_factory=dict)

@dataclass
class ApplicationConfig:
    name: str
    compute_platform: ComputePlatform
    description: str
    tags: Dict[str, str] = field(default_factory=dict)

@dataclass
class DeploymentGroupConfig:
    name: str
    service_role_arn: str
    deployment_config_name: str
    ec2_tag_filters: List[Dict[str, str]] = field(default_factory=list)
    auto_scaling_groups: List[str] = field(default_factory=list)
    load_balancer_info: Optional[Dict[str, Any]] = None
    alarm_configuration: Optional[Dict[str, Any]] = None
    auto_rollback_configuration: Optional[Dict[str, Any]] = None
    blue_green_deployment_configuration: Optional[Dict[str, Any]] = None
    ecs_services: List[Dict[str, str]] = field(default_factory=list)
    on_premises_instance_tag_filters: List[Dict[str, str]] = field(default_factory=list)
    trigger_configurations: List[Dict[str, Any]] = field(default_factory=list)
    outdated_instances_strategy: str = "UPDATE"
    deployment_style: Optional[Dict[str, str]] = None
    tags: Dict[str, str] = field(default_factory=dict)

@dataclass
class DeploymentMetrics:
    total_deployments: int
    successful_deployments: int
    failed_deployments: int
    rollback_count: int
    avg_deployment_duration: float
    success_rate_percent: float
    mttr_minutes: float  # Mean Time To Recovery
    deployment_frequency: float  # Deployments per day
    change_failure_rate: float
    lead_time_minutes: float

class EnterpriseCodeDeployManager:
    """
    Enterprise-grade AWS CodeDeploy manager with advanced deployment strategies,
    risk management, monitoring, and automated rollback capabilities.
    """
    
    def __init__(self, region: str = 'us-east-1'):
        self.codedeploy = boto3.client('codedeploy', region_name=region)
        self.ec2 = boto3.client('ec2', region_name=region)
        self.elbv2 = boto3.client('elbv2', region_name=region)
        self.autoscaling = boto3.client('autoscaling', region_name=region)
        self.cloudwatch = boto3.client('cloudwatch', region_name=region)
        self.sns = boto3.client('sns', region_name=region)
        self.lambda_client = boto3.client('lambda', region_name=region)
        self.ecs = boto3.client('ecs', region_name=region)
        self.region = region
        self.logger = self._setup_logging()
        
        # Deployment tracking
        self.applications = {}
        self.deployment_groups = {}
        self.active_deployments = {}
        self.deployment_strategies = {}
        self.risk_assessment_rules = {}
        self.canary_analysis_configs = {}
        
    def _setup_logging(self) -> logging.Logger:
        """Configure structured logging for CodeDeploy operations"""
        logger = logging.getLogger('codedeploy_manager')
        logger.setLevel(logging.INFO)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - '
            '%(application_name)s - %(deployment_id)s - %(message)s'
        )
        
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    def create_enterprise_application(self, 
                                    config: ApplicationConfig,
                                    validation_rules: Optional[List] = None) -> Dict[str, Any]:
        """Create enterprise CodeDeploy application with validation"""
        
        # Validate application configuration
        self._validate_application_config(config, validation_rules or [])
        
        try:
            # Create CodeDeploy application
            response = self.codedeploy.create_application(
                applicationName=config.name,
                computePlatform=config.compute_platform.value,
                tags=[
                    {'Key': k, 'Value': v} for k, v in config.tags.items()
                ]
            )
            
            # Store application configuration
            self.applications[config.name] = {
                'config': config,
                'application_id': response['applicationId'],
                'created_at': datetime.utcnow(),
                'deployment_groups': [],
                'metrics': DeploymentMetrics(
                    total_deployments=0,
                    successful_deployments=0,
                    failed_deployments=0,
                    rollback_count=0,
                    avg_deployment_duration=0.0,
                    success_rate_percent=100.0,
                    mttr_minutes=0.0,
                    deployment_frequency=0.0,
                    change_failure_rate=0.0,
                    lead_time_minutes=0.0
                )
            }
            
            self.logger.info(
                f"Application created: {config.name}",
                extra={'application_name': config.name, 'deployment_id': 'app'}
            )
            
            return {
                'application_name': config.name,
                'application_id': response['applicationId'],
                'compute_platform': config.compute_platform.value,
                'status': 'created'
            }
            
        except Exception as e:
            self.logger.error(
                f"Failed to create application: {e}",
                extra={'application_name': config.name, 'deployment_id': 'app'}
            )
            raise
    
    def _validate_application_config(self, 
                                   config: ApplicationConfig,
                                   validation_rules: List):
        """Validate application configuration"""
        
        # Basic validation
        if not config.name or len(config.name) < 1:
            raise ValueError("Application name is required")
        
        if len(config.name) > 100:
            raise ValueError("Application name must be 100 characters or less")
        
        # Enterprise validation rules
        for rule in validation_rules:
            rule(config)
        
        # Security validation
        self._validate_application_security(config)
    
    def _validate_application_security(self, config: ApplicationConfig):
        """Validate application security requirements"""
        
        # Check for required security tags
        required_security_tags = ['Environment', 'Owner', 'DataClassification']
        
        for tag in required_security_tags:
            if tag not in config.tags:
                self.logger.warning(
                    f"Missing required security tag: {tag}"
                )
        
        # Validate data classification
        valid_classifications = ['public', 'internal', 'confidential', 'restricted']
        data_classification = config.tags.get('DataClassification', '').lower()
        
        if data_classification and data_classification not in valid_classifications:
            raise ValueError(f"Invalid data classification: {data_classification}")
    
    def create_enterprise_deployment_group(self, 
                                         application_name: str,
                                         config: DeploymentGroupConfig,
                                         risk_assessment_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create enterprise deployment group with risk assessment"""
        
        if application_name not in self.applications:
            raise ValueError(f"Application '{application_name}' not found")
        
        # Validate deployment group configuration
        self._validate_deployment_group_config(config)
        
        # Set up risk assessment if provided
        if risk_assessment_config:
            self._setup_risk_assessment(application_name, config.name, risk_assessment_config)
        
        try:
            # Prepare deployment group parameters
            params = self._prepare_deployment_group_params(application_name, config)
            
            # Create deployment group
            response = self.codedeploy.create_deployment_group(**params)
            
            # Store deployment group configuration
            group_id = f"{application_name}:{config.name}"
            self.deployment_groups[group_id] = {
                'config': config,
                'application_name': application_name,
                'created_at': datetime.utcnow(),
                'deployment_count': 0,
                'last_deployment_time': None
            }
            
            # Update application deployment groups list
            self.applications[application_name]['deployment_groups'].append(config.name)
            
            # Set up monitoring and alerting
            self._setup_deployment_group_monitoring(application_name, config.name)
            
            self.logger.info(
                f"Deployment group created: {config.name}",
                extra={'application_name': application_name, 'deployment_id': 'group'}
            )
            
            return {
                'deployment_group_id': response['deploymentGroupId'],
                'application_name': application_name,
                'deployment_group_name': config.name,
                'status': 'created',
                'monitoring_enabled': True,
                'risk_assessment_enabled': risk_assessment_config is not None
            }
            
        except Exception as e:
            self.logger.error(
                f"Failed to create deployment group: {e}",
                extra={'application_name': application_name, 'deployment_id': 'group'}
            )
            raise
    
    def _validate_deployment_group_config(self, config: DeploymentGroupConfig):
        """Validate deployment group configuration"""
        
        # Basic validation
        if not config.name or not config.service_role_arn:
            raise ValueError("Deployment group name and service role ARN are required")
        
        # Validate service role ARN format
        if not config.service_role_arn.startswith('arn:aws:iam::'):
            raise ValueError("Invalid service role ARN format")
        
        # Validate target configuration
        has_targets = (
            config.ec2_tag_filters or 
            config.auto_scaling_groups or 
            config.on_premises_instance_tag_filters or
            config.ecs_services
        )
        
        if not has_targets:
            raise ValueError("At least one target configuration is required")
        
        # Validate alarm configuration
        if config.alarm_configuration and config.alarm_configuration.get('enabled'):
            alarms = config.alarm_configuration.get('alarms', [])
            if not alarms:
                raise ValueError("Alarm configuration enabled but no alarms specified")
    
    def _prepare_deployment_group_params(self, 
                                       application_name: str,
                                       config: DeploymentGroupConfig) -> Dict[str, Any]:
        """Prepare deployment group parameters for CodeDeploy"""
        
        params = {
            'applicationName': application_name,
            'deploymentGroupName': config.name,
            'serviceRoleArn': config.service_role_arn,
            'deploymentConfigName': config.deployment_config_name,
            'outdatedInstancesStrategy': config.outdated_instances_strategy,
            'tags': [
                {'Key': k, 'Value': v} for k, v in config.tags.items()
            ]
        }
        
        # Add EC2 tag filters
        if config.ec2_tag_filters:
            params['ec2TagFilters'] = config.ec2_tag_filters
        
        # Add Auto Scaling groups
        if config.auto_scaling_groups:
            params['autoScalingGroups'] = config.auto_scaling_groups
        
        # Add load balancer info
        if config.load_balancer_info:
            params['loadBalancerInfo'] = config.load_balancer_info
        
        # Add alarm configuration
        if config.alarm_configuration:
            params['alarmConfiguration'] = config.alarm_configuration
        
        # Add auto rollback configuration
        if config.auto_rollback_configuration:
            params['autoRollbackConfiguration'] = config.auto_rollback_configuration
        
        # Add blue-green deployment configuration
        if config.blue_green_deployment_configuration:
            params['blueGreenDeploymentConfiguration'] = config.blue_green_deployment_configuration
        
        # Add ECS services
        if config.ecs_services:
            params['ecsServices'] = config.ecs_services
        
        # Add on-premises instance tag filters
        if config.on_premises_instance_tag_filters:
            params['onPremisesInstanceTagFilters'] = config.on_premises_instance_tag_filters
        
        # Add trigger configurations
        if config.trigger_configurations:
            params['triggerConfigurations'] = config.trigger_configurations
        
        # Add deployment style
        if config.deployment_style:
            params['deploymentStyle'] = config.deployment_style
        
        return params
    
    async def execute_enterprise_deployment(self, 
                                          application_name: str,
                                          deployment_group_name: str,
                                          revision: Dict[str, Any],
                                          deployment_config_name: Optional[str] = None,
                                          description: Optional[str] = None,
                                          ignore_application_stop_failures: bool = False,
                                          update_outdated_instances_only: bool = False,
                                          file_exists_behavior: str = "DISALLOW",
                                          auto_rollback_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute enterprise deployment with comprehensive monitoring"""
        
        if application_name not in self.applications:
            raise ValueError(f"Application '{application_name}' not found")
        
        group_id = f"{application_name}:{deployment_group_name}"
        if group_id not in self.deployment_groups:
            raise ValueError(f"Deployment group '{deployment_group_name}' not found")
        
        # Pre-deployment risk assessment
        risk_assessment = await self._perform_pre_deployment_risk_assessment(
            application_name,
            deployment_group_name,
            revision
        )
        
        if risk_assessment['risk_level'] == 'HIGH' and not risk_assessment['approved']:
            raise Exception(f"Deployment blocked due to high risk: {risk_assessment['reasons']}")
        
        # Prepare deployment parameters
        deployment_params = {
            'applicationName': application_name,
            'deploymentGroupName': deployment_group_name,
            'revision': revision,
            'ignoreApplicationStopFailures': ignore_application_stop_failures,
            'updateOutdatedInstancesOnly': update_outdated_instances_only,
            'fileExistsBehavior': file_exists_behavior
        }
        
        if deployment_config_name:
            deployment_params['deploymentConfigName'] = deployment_config_name
        
        if description:
            deployment_params['description'] = description
        
        if auto_rollback_config:
            deployment_params['autoRollbackConfiguration'] = auto_rollback_config
        
        try:
            # Create deployment
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.codedeploy.create_deployment(**deployment_params)
            )
            
            deployment_id = response['deploymentId']
            
            # Track deployment
            deployment_context = {
                'deployment_id': deployment_id,
                'application_name': application_name,
                'deployment_group_name': deployment_group_name,
                'started_at': datetime.utcnow(),
                'status': DeploymentStatus.CREATED,
                'risk_assessment': risk_assessment,
                'revision': revision,
                'monitoring_metrics': [],
                'canary_analysis': None
            }
            
            self.active_deployments[deployment_id] = deployment_context
            
            # Update deployment group metrics
            self.deployment_groups[group_id]['deployment_count'] += 1
            self.deployment_groups[group_id]['last_deployment_time'] = datetime.utcnow()
            
            self.logger.info(
                f"Deployment started: {deployment_id}",
                extra={'application_name': application_name, 'deployment_id': deployment_id}
            )
            
            # Start monitoring task
            asyncio.create_task(
                self._monitor_deployment_execution(deployment_context)
            )
            
            return {
                'deployment_id': deployment_id,
                'application_name': application_name,
                'deployment_group_name': deployment_group_name,
                'status': 'started',
                'risk_assessment': risk_assessment,
                'monitoring_enabled': True,
                'started_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(
                f"Failed to start deployment: {e}",
                extra={'application_name': application_name, 'deployment_id': 'failed'}
            )
            raise
    
    async def _perform_pre_deployment_risk_assessment(self, 
                                                    application_name: str,
                                                    deployment_group_name: str,
                                                    revision: Dict[str, Any]) -> Dict[str, Any]:
        """Perform comprehensive pre-deployment risk assessment"""
        
        risk_factors = []
        risk_score = 0
        
        # Check recent deployment history
        recent_failures = await self._check_recent_deployment_failures(
            application_name,
            deployment_group_name
        )
        
        if recent_failures > 2:
            risk_factors.append(f"Multiple recent failures: {recent_failures}")
            risk_score += 30
        
        # Check system health
        system_health = await self._check_system_health(
            application_name,
            deployment_group_name
        )
        
        if system_health['healthy_instances_percent'] < 80:
            risk_factors.append(f"Low system health: {system_health['healthy_instances_percent']}%")
            risk_score += 25
        
        # Check deployment timing
        deployment_timing = await self._assess_deployment_timing()
        
        if deployment_timing['is_peak_hours']:
            risk_factors.append("Deployment during peak hours")
            risk_score += 15
        
        # Check change magnitude
        change_magnitude = await self._assess_change_magnitude(revision)
        
        if change_magnitude['is_major_change']:
            risk_factors.append(f"Major change detected: {change_magnitude['change_type']}")
            risk_score += 20
        
        # Determine risk level
        if risk_score >= 50:
            risk_level = 'HIGH'
        elif risk_score >= 25:
            risk_level = 'MEDIUM'
        else:
            risk_level = 'LOW'
        
        # Auto-approval logic
        auto_approved = risk_level == 'LOW' or (
            risk_level == 'MEDIUM' and 
            len(risk_factors) <= 2
        )
        
        return {
            'risk_level': risk_level,
            'risk_score': risk_score,
            'risk_factors': risk_factors,
            'approved': auto_approved,
            'reasons': risk_factors,
            'assessment_time': datetime.utcnow().isoformat(),
            'system_health': system_health,
            'deployment_timing': deployment_timing,
            'change_magnitude': change_magnitude
        }
    
    async def _monitor_deployment_execution(self, deployment_context: Dict[str, Any]):
        """Monitor deployment execution with real-time analysis"""
        
        deployment_id = deployment_context['deployment_id']
        application_name = deployment_context['application_name']
        
        while True:
            try:
                # Get deployment status
                response = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self.codedeploy.get_deployment(deploymentId=deployment_id)
                )
                
                deployment_info = response['deploymentInfo']
                current_status = DeploymentStatus(deployment_info['status'])
                
                # Update context
                deployment_context['status'] = current_status
                deployment_context['last_updated'] = datetime.utcnow()
                
                # Log status changes
                if deployment_context.get('previous_status') != current_status:
                    self.logger.info(
                        f"Deployment status: {current_status.value}",
                        extra={'application_name': application_name, 'deployment_id': deployment_id}
                    )
                    deployment_context['previous_status'] = current_status
                
                # Perform canary analysis if applicable
                if current_status == DeploymentStatus.IN_PROGRESS:
                    await self._perform_canary_analysis(deployment_context, deployment_info)
                
                # Check if deployment completed
                if current_status in [DeploymentStatus.SUCCEEDED, DeploymentStatus.FAILED, 
                                    DeploymentStatus.STOPPED]:
                    
                    await self._handle_deployment_completion(
                        deployment_context,
                        deployment_info
                    )
                    break
                
                # Continue monitoring
                await asyncio.sleep(15)
                
            except Exception as e:
                self.logger.error(
                    f"Error monitoring deployment: {e}",
                    extra={'application_name': application_name, 'deployment_id': deployment_id}
                )
                await asyncio.sleep(30)
    
    async def _perform_canary_analysis(self, 
                                     deployment_context: Dict[str, Any],
                                     deployment_info: Dict[str, Any]):
        """Perform real-time canary analysis during deployment"""
        
        deployment_id = deployment_context['deployment_id']
        application_name = deployment_context['application_name']
        
        # Get current deployment overview
        overview = deployment_info.get('deploymentOverview', {})
        
        # Check if we're in a canary phase
        if 'Blue' in overview and 'Green' in overview:
            blue_status = overview.get('Blue')
            green_status = overview.get('Green')
            
            if green_status and green_status in ['InProgress', 'Succeeded']:
                # Perform canary metrics analysis
                canary_metrics = await self._analyze_canary_metrics(
                    deployment_context,
                    deployment_info
                )
                
                deployment_context['canary_analysis'] = canary_metrics
                
                # Check if canary should be stopped
                if canary_metrics['should_stop']:
                    self.logger.warning(
                        f"Canary analysis failed: {canary_metrics['failure_reasons']}",
                        extra={'application_name': application_name, 'deployment_id': deployment_id}
                    )
                    
                    # Stop deployment with rollback
                    await asyncio.get_event_loop().run_in_executor(
                        None,
                        lambda: self.codedeploy.stop_deployment(
                            deploymentId=deployment_id,
                            autoRollbackEnabled=True
                        )
                    )
    
    async def _analyze_canary_metrics(self, 
                                     deployment_context: Dict[str, Any],
                                     deployment_info: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze canary deployment metrics"""
        
        # Get baseline and canary metrics
        baseline_metrics = await self._get_baseline_metrics(
            deployment_context['application_name'],
            deployment_context['deployment_group_name']
        )
        
        canary_metrics = await self._get_canary_metrics(
            deployment_context['application_name'],
            deployment_context['deployment_group_name']
        )
        
        # Analysis criteria
        failure_reasons = []
        should_stop = False
        
        # Error rate analysis
        baseline_error_rate = baseline_metrics.get('error_rate', 0)
        canary_error_rate = canary_metrics.get('error_rate', 0)
        
        if canary_error_rate > baseline_error_rate * 1.5:  # 50% increase threshold
            failure_reasons.append(f"Error rate increased: {baseline_error_rate:.2f}% -> {canary_error_rate:.2f}%")
            should_stop = True
        
        # Response time analysis
        baseline_response_time = baseline_metrics.get('avg_response_time', 0)
        canary_response_time = canary_metrics.get('avg_response_time', 0)
        
        if canary_response_time > baseline_response_time * 1.3:  # 30% increase threshold
            failure_reasons.append(f"Response time increased: {baseline_response_time:.0f}ms -> {canary_response_time:.0f}ms")
            should_stop = True
        
        # CPU utilization analysis
        baseline_cpu = baseline_metrics.get('cpu_utilization', 0)
        canary_cpu = canary_metrics.get('cpu_utilization', 0)
        
        if canary_cpu > 80:  # Absolute threshold
            failure_reasons.append(f"High CPU utilization: {canary_cpu:.1f}%")
            should_stop = True
        
        # Memory utilization analysis
        baseline_memory = baseline_metrics.get('memory_utilization', 0)
        canary_memory = canary_metrics.get('memory_utilization', 0)
        
        if canary_memory > 85:  # Absolute threshold
            failure_reasons.append(f"High memory utilization: {canary_memory:.1f}%")
            should_stop = True
        
        return {
            'should_stop': should_stop,
            'failure_reasons': failure_reasons,
            'baseline_metrics': baseline_metrics,
            'canary_metrics': canary_metrics,
            'analysis_time': datetime.utcnow().isoformat(),
            'confidence_score': self._calculate_confidence_score(
                baseline_metrics, 
                canary_metrics
            )
        }
    
    def _calculate_confidence_score(self, 
                                  baseline_metrics: Dict[str, float],
                                  canary_metrics: Dict[str, float]) -> float:
        """Calculate confidence score for canary analysis"""
        
        # Simple confidence calculation based on metric stability
        stability_factors = []
        
        # Error rate stability
        error_rate_diff = abs(canary_metrics.get('error_rate', 0) - baseline_metrics.get('error_rate', 0))
        if error_rate_diff < 0.5:  # Less than 0.5% difference
            stability_factors.append(0.3)
        
        # Response time stability
        response_time_ratio = canary_metrics.get('avg_response_time', 0) / max(baseline_metrics.get('avg_response_time', 1), 1)
        if 0.9 <= response_time_ratio <= 1.1:  # Within 10%
            stability_factors.append(0.4)
        
        # Resource utilization stability
        cpu_diff = abs(canary_metrics.get('cpu_utilization', 0) - baseline_metrics.get('cpu_utilization', 0))
        if cpu_diff < 10:  # Less than 10% difference
            stability_factors.append(0.3)
        
        return sum(stability_factors)
    
    def setup_advanced_deployment_strategies(self, 
                                           application_name: str) -> Dict[str, Any]:
        """Set up advanced deployment strategies for application"""
        
        if application_name not in self.applications:
            raise ValueError(f"Application '{application_name}' not found")
        
        deployment_strategies = {
            'zero_downtime_blue_green': {
                'name': 'Zero Downtime Blue-Green',
                'description': 'Complete environment switch with instant rollback',
                'configuration': {
                    'deployment_config_name': 'CodeDeployDefault.EC2AllAtOneBlueGreen',
                    'blue_green_config': {
                        'terminateBlueInstancesOnDeploymentSuccess': {
                            'action': 'TERMINATE',
                            'terminationWaitTimeInMinutes': 5
                        },
                        'deploymentReadyOption': {
                            'actionOnTimeout': 'CONTINUE_DEPLOYMENT',
                            'waitTimeInMinutes': 0
                        },
                        'greenFleetProvisioningOption': {
                            'action': 'COPY_AUTO_SCALING_GROUP'
                        }
                    },
                    'load_balancer_info': {
                        'targetGroupInfoList': [
                            {'name': f'{application_name}-tg'}
                        ]
                    }
                },
                'monitoring': {
                    'health_check_grace_period': 300,
                    'validation_tests': [
                        'health_endpoint_check',
                        'functional_smoke_tests',
                        'performance_baseline_test'
                    ]
                },
                'rollback': {
                    'automatic': True,
                    'triggers': [
                        'health_check_failure',
                        'alarm_threshold_breach',
                        'manual_intervention'
                    ]
                }
            },
            'progressive_canary': {
                'name': 'Progressive Canary Deployment',
                'description': 'Gradual traffic shift with continuous monitoring',
                'configuration': {
                    'deployment_config_name': 'Custom.ProgressiveCanary',
                    'traffic_routing': {
                        'type': 'TimeBasedCanary',
                        'timeBasedCanary': {
                            'canaryPercentage': 10,
                            'canaryInterval': 5
                        }
                    },
                    'phases': [
                        {'traffic_percent': 10, 'duration_minutes': 10},
                        {'traffic_percent': 25, 'duration_minutes': 15},
                        {'traffic_percent': 50, 'duration_minutes': 20},
                        {'traffic_percent': 75, 'duration_minutes': 15},
                        {'traffic_percent': 100, 'duration_minutes': 10}
                    ]
                },
                'monitoring': {
                    'canary_analysis': {
                        'enabled': True,
                        'baseline_duration_minutes': 30,
                        'canary_duration_minutes': 15,
                        'success_threshold': 95
                    },
                    'metrics': [
                        'error_rate',
                        'latency_p50',
                        'latency_p95',
                        'latency_p99',
                        'cpu_utilization',
                        'memory_utilization',
                        'request_count'
                    ]
                },
                'failure_criteria': {
                    'error_rate_increase_threshold': 50,  # Percentage
                    'latency_increase_threshold': 30,     # Percentage
                    'resource_utilization_threshold': 80  # Percentage
                }
            },
            'safe_rolling': {
                'name': 'Safe Rolling Deployment',
                'description': 'Instance-by-instance with health validation',
                'configuration': {
                    'deployment_config_name': 'Custom.SafeRolling',
                    'minimum_healthy_hosts': {
                        'type': 'FLEET_PERCENT',
                        'value': 75
                    },
                    'batch_size': {
                        'type': 'FLEET_PERCENT',
                        'value': 25
                    }
                },
                'monitoring': {
                    'health_check_per_instance': True,
                    'wait_time_between_batches': 300,
                    'max_deployment_duration': 3600
                },
                'rollback': {
                    'on_first_failure': True,
                    'health_check_failures_threshold': 1
                }
            },
            'feature_flag_deployment': {
                'name': 'Feature Flag Controlled Deployment',
                'description': 'Deployment with feature toggle control',
                'configuration': {
                    'deployment_config_name': 'CodeDeployDefault.EC2AllAtOnceBlueGreen',
                    'feature_flags': {
                        'service': 'launchdarkly',  # or 'aws-appconfig'
                        'environment': 'production',
                        'flags': [
                            {
                                'name': f'{application_name}_new_features',
                                'initial_state': False,
                                'rollout_strategy': 'user_segment'
                            }
                        ]
                    }
                },
                'rollout_phases': [
                    {'segment': 'internal_users', 'percentage': 100},
                    {'segment': 'beta_users', 'percentage': 100},
                    {'segment': 'premium_users', 'percentage': 20},
                    {'segment': 'all_users', 'percentage': 5},
                    {'segment': 'all_users', 'percentage': 25},
                    {'segment': 'all_users', 'percentage': 100}
                ],
                'monitoring': {
                    'feature_usage_analytics': True,
                    'user_feedback_collection': True,
                    'business_metrics_tracking': True
                }
            }
        }
        
        # Store deployment strategies
        self.deployment_strategies[application_name] = deployment_strategies
        
        # Create custom deployment configurations
        self._create_custom_deployment_configs(deployment_strategies)
        
        return deployment_strategies

# Usage Example
if __name__ == "__main__":
    # Initialize CodeDeploy manager
    cd_manager = EnterpriseCodeDeployManager()
    
    # Create enterprise application
    app_config = ApplicationConfig(
        name="enterprise-web-application",
        compute_platform=ComputePlatform.SERVER,
        description="Enterprise web application with advanced deployment strategies",
        tags={
            "Environment": "Production",
            "Team": "DevOps",
            "Owner": "platform-team@enterprise.com",
            "DataClassification": "confidential",
            "CostCenter": "Engineering",
            "Project": "WebPlatform"
        }
    )
    
    result = cd_manager.create_enterprise_application(app_config)
    print(f"Application created: {result['application_name']}")
    
    # Create deployment group with blue-green configuration
    deployment_group_config = DeploymentGroupConfig(
        name="production-servers",
        service_role_arn="arn:aws:iam::123456789012:role/CodeDeployServiceRole",
        deployment_config_name="CodeDeployDefault.EC2AllAtOneBlueGreen",
        ec2_tag_filters=[
            {
                'Type': 'KEY_AND_VALUE',
                'Key': 'Environment',
                'Value': 'Production'
            },
            {
                'Type': 'KEY_AND_VALUE',
                'Key': 'Application',
                'Value': 'WebApp'
            }
        ],
        auto_scaling_groups=["web-app-asg"],
        load_balancer_info={
            'targetGroupInfoList': [
                {'name': 'web-app-target-group'}
            ]
        },
        alarm_configuration={
            'enabled': True,
            'alarms': [
                {'name': 'HighErrorRate'},
                {'name': 'HighResponseTime'},
                {'name': 'LowHealthyHostCount'}
            ]
        },
        auto_rollback_configuration={
            'enabled': True,
            'events': ['DEPLOYMENT_FAILURE', 'DEPLOYMENT_STOP_ON_ALARM']
        },
        blue_green_deployment_configuration={
            'terminateBlueInstancesOnDeploymentSuccess': {
                'action': 'TERMINATE',
                'terminationWaitTimeInMinutes': 5
            },
            'deploymentReadyOption': {
                'actionOnTimeout': 'CONTINUE_DEPLOYMENT',
                'waitTimeInMinutes': 0
            },
            'greenFleetProvisioningOption': {
                'action': 'COPY_AUTO_SCALING_GROUP'
            }
        },
        trigger_configurations=[
            {
                'triggerName': 'deployment-notification',
                'triggerTargetArn': 'arn:aws:sns:us-east-1:123456789012:deployment-notifications',
                'triggerEvents': [
                    'DeploymentStart',
                    'DeploymentSuccess',
                    'DeploymentFailure',
                    'DeploymentRollback'
                ]
            }
        ],
        tags={
            "Environment": "Production",
            "DeploymentStrategy": "BlueGreen",
            "CriticalityLevel": "High"
        }
    )
    
    # Risk assessment configuration
    risk_assessment_config = {
        'enable_pre_deployment_checks': True,
        'failure_threshold': 2,
        'health_check_minimum_percent': 80,
        'peak_hours': ['09:00-12:00', '14:00-17:00'],
        'blackout_windows': [
            {'start': '2024-12-24T00:00:00Z', 'end': '2024-12-26T23:59:59Z'},
            {'start': '2024-12-31T00:00:00Z', 'end': '2025-01-02T23:59:59Z'}
        ]
    }
    
    group_result = cd_manager.create_enterprise_deployment_group(
        "enterprise-web-application",
        deployment_group_config,
        risk_assessment_config
    )
    
    print(f"Deployment group created: {group_result['deployment_group_name']}")
    
    # Set up advanced deployment strategies
    strategies = cd_manager.setup_advanced_deployment_strategies(
        "enterprise-web-application"
    )
    
    print(f"Deployment strategies configured: {len(strategies)}")
    for strategy_name, strategy_config in strategies.items():
        print(f"  - {strategy_config['name']}: {strategy_config['description']}")
    
    # Execute enterprise deployment
    async def run_deployment():
        revision = {
            'revisionType': 'S3',
            's3Location': {
                'bucket': 'enterprise-deployment-artifacts',
                'key': 'web-app/v2.1.0/web-app-v2.1.0.zip',
                'bundleType': 'zip'
            }
        }
        
        deployment_result = await cd_manager.execute_enterprise_deployment(
            application_name="enterprise-web-application",
            deployment_group_name="production-servers",
            revision=revision,
            description="Production deployment v2.1.0 with enhanced security features",
            auto_rollback_config={
                'enabled': True,
                'events': ['DEPLOYMENT_FAILURE', 'DEPLOYMENT_STOP_ON_ALARM']
            }
        )
        
        print(f"Deployment started: {deployment_result['deployment_id']}")
        print(f"Risk assessment: {deployment_result['risk_assessment']['risk_level']}")
        
        return deployment_result
    
    # Run the deployment example
    import asyncio
    deployment_result = asyncio.run(run_deployment())
```

### 2. Enterprise Deployment Risk Management & Compliance

```python
import boto3
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import asyncio
from enum import Enum

class ComplianceFramework(Enum):
    SOX = "sox"
    PCI_DSS = "pci_dss"
    GDPR = "gdpr"
    HIPAA = "hipaa"
    SOC2 = "soc2"
    ISO27001 = "iso27001"

class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class ComplianceRule:
    name: str
    framework: ComplianceFramework
    description: str
    validation_function: str
    blocking: bool = True
    severity: RiskLevel = RiskLevel.MEDIUM

@dataclass
class DeploymentWindow:
    name: str
    description: str
    start_time: str  # HH:MM format
    end_time: str    # HH:MM format
    days_of_week: List[int]  # 0=Monday, 6=Sunday
    timezone: str = "UTC"
    environments: List[str] = None

class EnterpriseDeploymentGovernance:
    """
    Enterprise deployment governance with compliance validation,
    risk management, and automated approval workflows.
    """
    
    def __init__(self):
        self.codedeploy = boto3.client('codedeploy')
        self.stepfunctions = boto3.client('stepfunctions')
        self.sns = boto3.client('sns')
        self.dynamodb = boto3.resource('dynamodb')
        
        self.compliance_rules = {}
        self.deployment_windows = {}
        self.approval_workflows = {}
        self.risk_policies = {}
        
    def setup_compliance_framework(self, 
                                 framework: ComplianceFramework,
                                 environment: str) -> Dict[str, Any]:
        """Set up compliance framework for deployment governance"""
        
        compliance_rules = self._get_compliance_rules_for_framework(framework)
        
        # Store compliance rules
        framework_key = f"{framework.value}:{environment}"
        self.compliance_rules[framework_key] = compliance_rules
        
        # Create compliance validation workflow
        workflow_arn = self._create_compliance_workflow(framework, environment, compliance_rules)
        
        # Set up compliance monitoring
        monitoring_config = self._setup_compliance_monitoring(framework, environment)
        
        return {
            'framework': framework.value,
            'environment': environment,
            'rules_count': len(compliance_rules),
            'workflow_arn': workflow_arn,
            'monitoring_enabled': True,
            'compliance_rules': [rule.name for rule in compliance_rules]
        }
    
    def _get_compliance_rules_for_framework(self, 
                                          framework: ComplianceFramework) -> List[ComplianceRule]:
        """Get compliance rules for specific framework"""
        
        if framework == ComplianceFramework.SOX:
            return [
                ComplianceRule(
                    name="segregation_of_duties",
                    framework=framework,
                    description="Ensure deployment approver is different from developer",
                    validation_function="validate_segregation_of_duties",
                    blocking=True,
                    severity=RiskLevel.HIGH
                ),
                ComplianceRule(
                    name="audit_trail_completeness",
                    framework=framework,
                    description="Verify complete audit trail for all changes",
                    validation_function="validate_audit_trail",
                    blocking=True,
                    severity=RiskLevel.HIGH
                ),
                ComplianceRule(
                    name="change_documentation",
                    framework=framework,
                    description="Require change documentation and business justification",
                    validation_function="validate_change_documentation",
                    blocking=True,
                    severity=RiskLevel.MEDIUM
                ),
                ComplianceRule(
                    name="rollback_capability",
                    framework=framework,
                    description="Ensure rollback capability is tested and available",
                    validation_function="validate_rollback_capability",
                    blocking=True,
                    severity=RiskLevel.HIGH
                )
            ]
        
        elif framework == ComplianceFramework.PCI_DSS:
            return [
                ComplianceRule(
                    name="cardholder_data_protection",
                    framework=framework,
                    description="Validate cardholder data protection measures",
                    validation_function="validate_cardholder_data_protection",
                    blocking=True,
                    severity=RiskLevel.CRITICAL
                ),
                ComplianceRule(
                    name="security_vulnerability_scan",
                    framework=framework,
                    description="Mandatory security vulnerability scanning",
                    validation_function="validate_security_scan",
                    blocking=True,
                    severity=RiskLevel.HIGH
                ),
                ComplianceRule(
                    name="encryption_validation",
                    framework=framework,
                    description="Verify encryption of sensitive data in transit and at rest",
                    validation_function="validate_encryption",
                    blocking=True,
                    severity=RiskLevel.HIGH
                ),
                ComplianceRule(
                    name="access_control_validation",
                    framework=framework,
                    description="Validate proper access controls and authentication",
                    validation_function="validate_access_controls",
                    blocking=True,
                    severity=RiskLevel.HIGH
                )
            ]
        
        elif framework == ComplianceFramework.GDPR:
            return [
                ComplianceRule(
                    name="data_privacy_impact_assessment",
                    framework=framework,
                    description="Validate GDPR privacy impact assessment",
                    validation_function="validate_privacy_impact",
                    blocking=True,
                    severity=RiskLevel.HIGH
                ),
                ComplianceRule(
                    name="right_to_erasure",
                    framework=framework,
                    description="Ensure right to erasure functionality",
                    validation_function="validate_right_to_erasure",
                    blocking=True,
                    severity=RiskLevel.MEDIUM
                ),
                ComplianceRule(
                    name="consent_management",
                    framework=framework,
                    description="Validate consent management mechanisms",
                    validation_function="validate_consent_management",
                    blocking=True,
                    severity=RiskLevel.MEDIUM
                ),
                ComplianceRule(
                    name="data_portability",
                    framework=framework,
                    description="Ensure data portability capabilities",
                    validation_function="validate_data_portability",
                    blocking=False,
                    severity=RiskLevel.LOW
                )
            ]
        
        return []
    
    def setup_deployment_windows(self, 
                               environment: str,
                               window_configs: List[DeploymentWindow]) -> Dict[str, Any]:
        """Set up deployment windows for controlled release schedules"""
        
        validated_windows = []
        
        for window in window_configs:
            # Validate window configuration
            self._validate_deployment_window(window)
            validated_windows.append(window)
        
        # Store deployment windows
        self.deployment_windows[environment] = validated_windows
        
        # Create EventBridge rules for window enforcement
        rule_arns = self._create_window_enforcement_rules(environment, validated_windows)
        
        return {
            'environment': environment,
            'windows_count': len(validated_windows),
            'enforcement_rules': rule_arns,
            'windows': [
                {
                    'name': w.name,
                    'schedule': f"{w.start_time}-{w.end_time}",
                    'days': w.days_of_week
                }
                for w in validated_windows
            ]
        }
    
    def create_advanced_approval_workflow(self, 
                                        workflow_name: str,
                                        approval_stages: List[Dict[str, Any]],
                                        escalation_config: Dict[str, Any]) -> Dict[str, Any]:
        """Create advanced multi-stage approval workflow"""
        
        # Create Step Functions workflow for approvals
        workflow_definition = self._create_approval_workflow_definition(
            workflow_name,
            approval_stages,
            escalation_config
        )
        
        # Deploy workflow
        workflow_response = self.stepfunctions.create_state_machine(
            name=f"deployment-approval-{workflow_name}",
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
        
        # Store workflow configuration
        self.approval_workflows[workflow_name] = {
            'state_machine_arn': workflow_response['stateMachineArn'],
            'approval_stages': approval_stages,
            'escalation_config': escalation_config,
            'created_at': datetime.utcnow()
        }
        
        # Set up approval notifications
        notification_config = self._setup_approval_notifications(
            workflow_name,
            approval_stages
        )
        
        return {
            'workflow_name': workflow_name,
            'state_machine_arn': workflow_response['stateMachineArn'],
            'approval_stages_count': len(approval_stages),
            'escalation_enabled': bool(escalation_config),
            'notifications_configured': len(notification_config)
        }
    
    def _create_approval_workflow_definition(self, 
                                           workflow_name: str,
                                           approval_stages: List[Dict[str, Any]],
                                           escalation_config: Dict[str, Any]) -> Dict[str, Any]:
        """Create Step Functions definition for approval workflow"""
        
        states = {}
        
        # Initialize approval process
        states["InitializeApproval"] = {
            "Type": "Pass",
            "Parameters": {
                "workflowName": workflow_name,
                "deploymentRequest.$": "$",
                "currentStage": 0,
                "approvalHistory": [],
                "startTime.$": "$$.State.EnteredTime"
            },
            "Next": "ProcessApprovalStages"
        }
        
        # Process approval stages iteratively
        states["ProcessApprovalStages"] = {
            "Type": "Map",
            "ItemsPath": "$.approvalStages",
            "MaxConcurrency": 1,  # Sequential processing
            "Iterator": {
                "StartAt": "RequestApproval",
                "States": {
                    "RequestApproval": {
                        "Type": "Task",
                        "Resource": "arn:aws:states:::lambda:invoke.waitForTaskToken",
                        "Parameters": {
                            "FunctionName": "RequestDeploymentApproval",
                            "Payload": {
                                "taskToken.$": "$$.Task.Token",
                                "approvalStage.$": "$",
                                "deploymentRequest.$": "$.deploymentRequest"
                            }
                        },
                        "TimeoutSeconds": 86400,  # 24 hours
                        "Catch": [
                            {
                                "ErrorEquals": ["States.Timeout"],
                                "Next": "HandleTimeout",
                                "ResultPath": "$.error"
                            }
                        ],
                        "Next": "ValidateApproval"
                    },
                    "ValidateApproval": {
                        "Type": "Choice",
                        "Choices": [
                            {
                                "Variable": "$.approvalResult.decision",
                                "StringEquals": "APPROVED",
                                "Next": "ApprovalGranted"
                            },
                            {
                                "Variable": "$.approvalResult.decision",
                                "StringEquals": "REJECTED",
                                "Next": "ApprovalRejected"
                            }
                        ],
                        "Default": "HandleTimeout"
                    },
                    "ApprovalGranted": {
                        "Type": "Pass",
                        "Parameters": {
                            "status": "approved",
                            "approver.$": "$.approvalResult.approver",
                            "timestamp.$": "$$.State.EnteredTime",
                            "comments.$": "$.approvalResult.comments"
                        },
                        "End": True
                    },
                    "ApprovalRejected": {
                        "Type": "Fail",
                        "Cause": "Deployment approval rejected",
                        "Error": "ApprovalRejected"
                    },
                    "HandleTimeout": {
                        "Type": "Choice",
                        "Choices": [
                            {
                                "Variable": "$.escalationConfig.enabled",
                                "BooleanEquals": True,
                                "Next": "EscalateApproval"
                            }
                        ],
                        "Default": "ApprovalTimeout"
                    },
                    "EscalateApproval": {
                        "Type": "Task",
                        "Resource": "arn:aws:lambda:us-east-1:123456789012:function:EscalateApproval",
                        "Parameters": {
                            "approvalStage.$": "$",
                            "escalationConfig.$": "$.escalationConfig"
                        },
                        "Next": "RequestApproval"
                    },
                    "ApprovalTimeout": {
                        "Type": "Fail",
                        "Cause": "Approval request timed out",
                        "Error": "ApprovalTimeout"
                    }
                }
            },
            "Next": "ApprovalWorkflowComplete",
            "Catch": [
                {
                    "ErrorEquals": ["States.ALL"],
                    "Next": "ApprovalWorkflowFailed",
                    "ResultPath": "$.error"
                }
            ]
        }
        
        # Workflow completion states
        states["ApprovalWorkflowComplete"] = {
            "Type": "Task",
            "Resource": "arn:aws:lambda:us-east-1:123456789012:function:ProcessApprovalComplete",
            "Parameters": {
                "workflowName": workflow_name,
                "approvalResults.$": "$",
                "endTime.$": "$$.State.EnteredTime"
            },
            "End": True
        }
        
        states["ApprovalWorkflowFailed"] = {
            "Type": "Task",
            "Resource": "arn:aws:lambda:us-east-1:123456789012:function:ProcessApprovalFailure",
            "Parameters": {
                "workflowName": workflow_name,
                "error.$": "$.error",
                "endTime.$": "$$.State.EnteredTime"
            },
            "End": True
        }
        
        return {
            "Comment": f"Enterprise deployment approval workflow: {workflow_name}",
            "StartAt": "InitializeApproval",
            "States": states,
            "TimeoutSeconds": 172800  # 48 hours
        }

# Usage Example
if __name__ == "__main__":
    # Initialize governance manager
    governance = EnterpriseDeploymentGovernance()
    
    # Set up SOX compliance for production environment
    sox_compliance = governance.setup_compliance_framework(
        ComplianceFramework.SOX,
        "production"
    )
    
    print(f"SOX compliance configured with {sox_compliance['rules_count']} rules")
    
    # Set up PCI DSS compliance for payment processing environment
    pci_compliance = governance.setup_compliance_framework(
        ComplianceFramework.PCI_DSS,
        "payment-processing"
    )
    
    print(f"PCI DSS compliance configured with {pci_compliance['rules_count']} rules")
    
    # Configure deployment windows
    deployment_windows = [
        DeploymentWindow(
            name="business_hours_window",
            description="Standard business hours deployment window",
            start_time="09:00",
            end_time="17:00",
            days_of_week=[0, 1, 2, 3, 4],  # Monday to Friday
            timezone="America/New_York",
            environments=["staging", "development"]
        ),
        DeploymentWindow(
            name="maintenance_window",
            description="Scheduled maintenance window for production",
            start_time="02:00",
            end_time="06:00",
            days_of_week=[5, 6],  # Saturday and Sunday
            timezone="UTC",
            environments=["production"]
        ),
        DeploymentWindow(
            name="emergency_window",
            description="24/7 emergency deployment window",
            start_time="00:00",
            end_time="23:59",
            days_of_week=[0, 1, 2, 3, 4, 5, 6],  # All days
            timezone="UTC",
            environments=["emergency"]
        )
    ]
    
    windows_config = governance.setup_deployment_windows(
        "production",
        deployment_windows
    )
    
    print(f"Deployment windows configured: {windows_config['windows_count']}")
    
    # Create advanced approval workflow
    approval_stages = [
        {
            "name": "technical_review",
            "description": "Technical architecture and security review",
            "approvers": [
                "senior-architect@enterprise.com",
                "security-lead@enterprise.com"
            ],
            "required_approvals": 2,
            "timeout_hours": 24,
            "approval_criteria": [
                "Architecture review completed",
                "Security scan passed",
                "Performance tests successful"
            ]
        },
        {
            "name": "business_approval",
            "description": "Business stakeholder approval",
            "approvers": [
                "product-owner@enterprise.com",
                "business-sponsor@enterprise.com"
            ],
            "required_approvals": 1,
            "timeout_hours": 48,
            "approval_criteria": [
                "Business requirements validated",
                "User acceptance testing completed",
                "Customer impact assessed"
            ]
        },
        {
            "name": "operations_approval",
            "description": "Operations and infrastructure readiness",
            "approvers": [
                "ops-manager@enterprise.com",
                "devops-lead@enterprise.com"
            ],
            "required_approvals": 1,
            "timeout_hours": 12,
            "approval_criteria": [
                "Infrastructure capacity verified",
                "Monitoring and alerting configured",
                "Rollback plan validated"
            ]
        }
    ]
    
    escalation_config = {
        "enabled": True,
        "escalation_timeout_hours": 8,
        "escalation_contacts": [
            "cto@enterprise.com",
            "engineering-director@enterprise.com"
        ],
        "auto_approve_on_escalation_timeout": False
    }
    
    approval_workflow = governance.create_advanced_approval_workflow(
        "production-deployment-approval",
        approval_stages,
        escalation_config
    )
    
    print(f"Approval workflow created: {approval_workflow['workflow_name']}")
    print(f"Approval stages: {approval_workflow['approval_stages_count']}")
```

## Advanced Enterprise Use Cases

### Multi-Region Deployment Orchestration
- **Global Blue-Green Deployments**: Synchronized deployments across regions
- **Regional Failover Strategies**: Automated disaster recovery deployments
- **Geographic Traffic Routing**: DNS-based deployment traffic management
- **Compliance Zone Deployments**: Region-specific regulatory compliance

### Zero-Trust Deployment Security
- **Cryptographic Artifact Verification**: Signed deployment packages
- **Runtime Security Validation**: Real-time threat detection during deployment
- **Network Segmentation**: Isolated deployment environments
- **Identity-Based Deployment Authorization**: Fine-grained access control

### AI-Powered Deployment Intelligence
- **Predictive Rollback**: ML-based failure prediction
- **Intelligent Traffic Shifting**: AI-optimized canary analysis
- **Automated Performance Tuning**: Resource optimization during deployment
- **Anomaly Detection**: Real-time deployment anomaly identification

### Enterprise Integration Patterns
- **ServiceNow Integration**: ITSM workflow automation
- **Jira Integration**: Change request automation
- **Slack/Teams Integration**: Real-time deployment notifications
- **Datadog/Splunk Integration**: Advanced deployment analytics

## Enterprise DevOps Use Cases

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