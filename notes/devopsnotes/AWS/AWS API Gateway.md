# AWS API Gateway

> **Service Type:** API Management | **Tier:** Essential DevOps | **Global/Regional:** Regional (Edge-Optimized Global)

## Overview

AWS API Gateway is a fully managed service that makes it easy for developers to create, publish, maintain, monitor, and secure APIs at any scale. It serves as a front door for applications to access data, business logic, or functionality from backend services running on EC2, Lambda, or any web application.

## DevOps Use Cases

### API-First Development
- **Microservices architecture** with standardized API interfaces and contracts
- **Version management** for API evolution and backward compatibility
- **API documentation** generation and developer portal automation
- **Contract-driven development** with OpenAPI specifications

### CI/CD Integration
- **Automated deployments** through infrastructure as code
- **Stage management** for dev, staging, and production environments
- **Blue-green deployments** with traffic shifting capabilities
- **Canary releases** for gradual feature rollouts

### Monitoring and Observability
- **Comprehensive logging** with request/response tracing
- **Performance monitoring** with latency and error rate tracking
- **Usage analytics** for API consumption patterns
- **Alerting and dashboards** for operational visibility

### Security and Governance
- **Authentication and authorization** with multiple security models
- **Rate limiting and throttling** to protect backend services
- **Request validation** and transformation capabilities
- **Security scanning** and compliance monitoring

## Core Components

### API Types
- **REST APIs:** Full-featured APIs with extensive customization options
- **HTTP APIs:** Optimized for serverless workloads with lower latency and cost
- **WebSocket APIs:** Real-time bidirectional communication support
- **Private APIs:** VPC-only access for internal services

### Endpoint Types
- **Edge-Optimized:** Global distribution through CloudFront
- **Regional:** Single region deployment for lower latency
- **Private:** VPC endpoint access only

### Integration Types
- **Lambda Proxy Integration:** Direct Lambda function invocation
- **HTTP Integration:** Backend HTTP/HTTPS endpoints
- **AWS Service Integration:** Direct AWS service invocation
- **Mock Integration:** Static responses for testing

## Advanced DevOps Automation Framework

### Enterprise API Gateway Manager

```python
# enterprise-api-gateway-manager.py - Advanced API Gateway DevOps automation
import boto3
import json
import time
import yaml
import hashlib
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import logging
import concurrent.futures
import re

@dataclass
class APIStage:
    name: str
    description: str
    variables: Dict[str, str]
    throttling: Dict[str, int]
    caching_enabled: bool = False
    cache_ttl: int = 300
    logging_level: str = "INFO"
    data_trace_enabled: bool = False
    metrics_enabled: bool = True

@dataclass
class APIDeploymentConfig:
    api_name: str
    api_description: str
    api_type: str  # REST, HTTP, WebSocket
    endpoint_type: str  # EDGE, REGIONAL, PRIVATE
    stages: List[APIStage]
    cors_config: Optional[Dict[str, Any]] = None
    authorizer_config: Optional[Dict[str, Any]] = None
    usage_plan_config: Optional[Dict[str, Any]] = None
    
@dataclass
class MonitoringConfig:
    dashboard_enabled: bool = True
    alarms_enabled: bool = True
    error_rate_threshold: float = 5.0
    latency_threshold: int = 5000
    throttle_rate_threshold: float = 10.0
    custom_metrics: List[str] = None

class EnterpriseAPIGatewayManager:
    """
    Enterprise-grade API Gateway management with DevOps automation,
    monitoring, security, and compliance capabilities.
    """
    
    def __init__(self, region_name: str = 'us-west-2'):
        self.api_gateway = boto3.client('apigateway', region_name=region_name)
        self.api_gateway_v2 = boto3.client('apigatewayv2', region_name=region_name)
        self.cloudwatch = boto3.client('cloudwatch', region_name=region_name)
        self.logs = boto3.client('logs', region_name=region_name)
        self.lambda_client = boto3.client('lambda', region_name=region_name)
        self.iam = boto3.client('iam', region_name=region_name)
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Metrics namespace
        self.metrics_namespace = 'Enterprise/APIGateway'
        
        # API registry for tracking
        self.api_registry = {}
    
    def create_api_from_openapi(self, openapi_spec: Dict[str, Any], 
                               deployment_config: APIDeploymentConfig) -> Dict[str, Any]:
        """Create API Gateway from OpenAPI specification with enterprise configuration"""
        
        api_creation_result = {
            'api_id': None,
            'api_arn': None,
            'stages': {},
            'monitoring': {},
            'security': {},
            'deployment_time': datetime.now().isoformat()
        }
        
        try:
            # Validate OpenAPI spec
            self._validate_openapi_spec(openapi_spec)
            
            # Enhance OpenAPI spec with enterprise configurations
            enhanced_spec = self._enhance_openapi_spec(openapi_spec, deployment_config)
            
            # Create API based on type
            if deployment_config.api_type == 'REST':
                api_result = self._create_rest_api(enhanced_spec, deployment_config)
            elif deployment_config.api_type == 'HTTP':
                api_result = self._create_http_api(enhanced_spec, deployment_config)
            elif deployment_config.api_type == 'WebSocket':
                api_result = self._create_websocket_api(enhanced_spec, deployment_config)
            else:
                raise ValueError(f"Unsupported API type: {deployment_config.api_type}")
            
            api_creation_result['api_id'] = api_result['api_id']
            api_creation_result['api_arn'] = api_result['api_arn']
            
            # Create stages and deployments
            for stage_config in deployment_config.stages:
                stage_result = self._create_stage(
                    api_result['api_id'], 
                    stage_config, 
                    deployment_config.api_type
                )
                api_creation_result['stages'][stage_config.name] = stage_result
            
            # Setup monitoring and alerting
            monitoring_result = self._setup_api_monitoring(
                api_result['api_id'],
                deployment_config,
                MonitoringConfig()
            )
            api_creation_result['monitoring'] = monitoring_result
            
            # Configure security
            security_result = self._configure_api_security(
                api_result['api_id'],
                deployment_config
            )
            api_creation_result['security'] = security_result
            
            # Register API in enterprise registry
            self._register_api(api_result['api_id'], deployment_config, api_creation_result)
            
            self.logger.info(f"Successfully created API: {deployment_config.api_name}")
            return api_creation_result
            
        except Exception as e:
            self.logger.error(f"Failed to create API {deployment_config.api_name}: {e}")
            # Cleanup partial resources if needed
            self._cleanup_partial_deployment(api_creation_result)
            raise
    
    def _create_rest_api(self, openapi_spec: Dict[str, Any], 
                        config: APIDeploymentConfig) -> Dict[str, Any]:
        """Create REST API with enterprise configuration"""
        
        # Create REST API
        response = self.api_gateway.create_rest_api(
            name=config.api_name,
            description=config.api_description,
            body=json.dumps(openapi_spec),
            endpointConfiguration={
                'types': [config.endpoint_type]
            },
            tags={
                'Environment': 'production',
                'ManagedBy': 'EnterpriseAPIManager',
                'APIType': 'REST',
                'CreatedDate': datetime.now().strftime('%Y-%m-%d')
            }
        )
        
        api_id = response['id']
        api_arn = f"arn:aws:apigateway:{self.api_gateway.meta.region_name}::/restapis/{api_id}"
        
        # Configure binary media types
        self.api_gateway.put_rest_api(
            restApiId=api_id,
            body=json.dumps(openapi_spec),
            parameters={
                'basepath': 'ignore',
                'endpointConfigurationTypes': config.endpoint_type
            }
        )
        
        return {
            'api_id': api_id,
            'api_arn': api_arn,
            'api_type': 'REST'
        }
    
    def _create_http_api(self, openapi_spec: Dict[str, Any], 
                        config: APIDeploymentConfig) -> Dict[str, Any]:
        """Create HTTP API with enterprise configuration"""
        
        # Create HTTP API
        response = self.api_gateway_v2.create_api(
            Name=config.api_name,
            Description=config.api_description,
            ProtocolType='HTTP',
            Body=json.dumps(openapi_spec),
            Tags={
                'Environment': 'production',
                'ManagedBy': 'EnterpriseAPIManager',
                'APIType': 'HTTP',
                'CreatedDate': datetime.now().strftime('%Y-%m-%d')
            }
        )
        
        api_id = response['ApiId']
        api_arn = f"arn:aws:apigateway:{self.api_gateway_v2.meta.region_name}::/apis/{api_id}"
        
        # Configure CORS if specified
        if config.cors_config:
            self.api_gateway_v2.update_api(
                ApiId=api_id,
                CorsConfiguration=config.cors_config
            )
        
        return {
            'api_id': api_id,
            'api_arn': api_arn,
            'api_type': 'HTTP'
        }
    
    def _create_websocket_api(self, openapi_spec: Dict[str, Any], 
                             config: APIDeploymentConfig) -> Dict[str, Any]:
        """Create WebSocket API with enterprise configuration"""
        
        # Create WebSocket API
        response = self.api_gateway_v2.create_api(
            Name=config.api_name,
            Description=config.api_description,
            ProtocolType='WEBSOCKET',
            RouteSelectionExpression='$request.body.action',
            Tags={
                'Environment': 'production',
                'ManagedBy': 'EnterpriseAPIManager',
                'APIType': 'WebSocket',
                'CreatedDate': datetime.now().strftime('%Y-%m-%d')
            }
        )
        
        api_id = response['ApiId']
        api_arn = f"arn:aws:apigateway:{self.api_gateway_v2.meta.region_name}::/apis/{api_id}"
        
        return {
            'api_id': api_id,
            'api_arn': api_arn,
            'api_type': 'WebSocket'
        }
    
    def _create_stage(self, api_id: str, stage_config: APIStage, 
                     api_type: str) -> Dict[str, Any]:
        """Create and configure API stage with enterprise settings"""
        
        stage_result = {
            'stage_name': stage_config.name,
            'stage_arn': None,
            'invoke_url': None,
            'configuration': asdict(stage_config)
        }
        
        try:
            if api_type == 'REST':
                # Create deployment first for REST API
                deployment_response = self.api_gateway.create_deployment(
                    restApiId=api_id,
                    stageName=stage_config.name,
                    description=stage_config.description
                )
                
                # Update stage configuration
                self.api_gateway.update_stage(
                    restApiId=api_id,
                    stageName=stage_config.name,
                    patchOps=[
                        {
                            'op': 'replace',
                            'path': '/throttle/rateLimit',
                            'value': str(stage_config.throttling.get('rate', 1000))
                        },
                        {
                            'op': 'replace',
                            'path': '/throttle/burstLimit',
                            'value': str(stage_config.throttling.get('burst', 2000))
                        },
                        {
                            'op': 'replace',
                            'path': '/caching/enabled',
                            'value': str(stage_config.caching_enabled).lower()
                        },
                        {
                            'op': 'replace',
                            'path': '/caching/ttlInSeconds',
                            'value': str(stage_config.cache_ttl)
                        },
                        {
                            'op': 'replace',
                            'path': '/logging/level',
                            'value': stage_config.logging_level
                        },
                        {
                            'op': 'replace',
                            'path': '/logging/dataTrace',
                            'value': str(stage_config.data_trace_enabled).lower()
                        },
                        {
                            'op': 'replace',
                            'path': '/metricsEnabled',
                            'value': str(stage_config.metrics_enabled).lower()
                        }
                    ]
                )
                
                # Set stage variables
                for key, value in stage_config.variables.items():
                    self.api_gateway.update_stage(
                        restApiId=api_id,
                        stageName=stage_config.name,
                        patchOps=[
                            {
                                'op': 'replace',
                                'path': f'/variables/{key}',
                                'value': value
                            }
                        ]
                    )
                
                stage_result['stage_arn'] = f"arn:aws:apigateway:{self.api_gateway.meta.region_name}::/restapis/{api_id}/stages/{stage_config.name}"
                stage_result['invoke_url'] = f"https://{api_id}.execute-api.{self.api_gateway.meta.region_name}.amazonaws.com/{stage_config.name}"
                
            else:  # HTTP or WebSocket API
                # Create stage for HTTP/WebSocket API
                response = self.api_gateway_v2.create_stage(
                    ApiId=api_id,
                    StageName=stage_config.name,
                    Description=stage_config.description,
                    StageVariables=stage_config.variables,
                    ThrottleSettings={
                        'RateLimit': stage_config.throttling.get('rate', 1000),
                        'BurstLimit': stage_config.throttling.get('burst', 2000)
                    },
                    Tags={
                        'Environment': stage_config.name,
                        'ManagedBy': 'EnterpriseAPIManager'
                    }
                )
                
                stage_result['stage_arn'] = response['StageName']  # V2 doesn't return ARN directly
                stage_result['invoke_url'] = f"https://{api_id}.execute-api.{self.api_gateway_v2.meta.region_name}.amazonaws.com/{stage_config.name}"
            
            self.logger.info(f"Created stage {stage_config.name} for API {api_id}")
            return stage_result
            
        except Exception as e:
            self.logger.error(f"Failed to create stage {stage_config.name}: {e}")
            raise
    
    def _setup_api_monitoring(self, api_id: str, deployment_config: APIDeploymentConfig,
                             monitoring_config: MonitoringConfig) -> Dict[str, Any]:
        """Setup comprehensive monitoring for API Gateway"""
        
        monitoring_result = {
            'dashboard_name': None,
            'alarms': [],
            'log_groups': [],
            'custom_metrics': []
        }
        
        try:
            # Create CloudWatch dashboard
            if monitoring_config.dashboard_enabled:
                dashboard_name = f"{deployment_config.api_name}-dashboard"
                dashboard_body = self._create_dashboard_definition(api_id, deployment_config)
                
                self.cloudwatch.put_dashboard(
                    DashboardName=dashboard_name,
                    DashboardBody=json.dumps(dashboard_body)
                )
                
                monitoring_result['dashboard_name'] = dashboard_name
                self.logger.info(f"Created dashboard: {dashboard_name}")
            
            # Create CloudWatch alarms
            if monitoring_config.alarms_enabled:
                alarms = self._create_api_alarms(api_id, deployment_config, monitoring_config)
                monitoring_result['alarms'] = alarms
            
            # Setup custom log groups for each stage
            for stage_config in deployment_config.stages:
                log_group_name = f"/aws/apigateway/{deployment_config.api_name}/{stage_config.name}"
                
                try:
                    self.logs.create_log_group(
                        logGroupName=log_group_name,
                        tags={
                            'APIName': deployment_config.api_name,
                            'Stage': stage_config.name,
                            'ManagedBy': 'EnterpriseAPIManager'
                        }
                    )
                    monitoring_result['log_groups'].append(log_group_name)
                except self.logs.exceptions.ResourceAlreadyExistsException:
                    monitoring_result['log_groups'].append(log_group_name)
            
            # Setup custom metrics
            custom_metrics = self._setup_custom_metrics(api_id, deployment_config)
            monitoring_result['custom_metrics'] = custom_metrics
            
            return monitoring_result
            
        except Exception as e:
            self.logger.error(f"Failed to setup monitoring for API {api_id}: {e}")
            raise
    
    def _create_api_alarms(self, api_id: str, deployment_config: APIDeploymentConfig,
                          monitoring_config: MonitoringConfig) -> List[Dict[str, Any]]:
        """Create CloudWatch alarms for API Gateway metrics"""
        
        alarms = []
        
        for stage_config in deployment_config.stages:
            # Error rate alarm
            error_alarm_name = f"{deployment_config.api_name}-{stage_config.name}-ErrorRate"
            self.cloudwatch.put_metric_alarm(
                AlarmName=error_alarm_name,
                ComparisonOperator='GreaterThanThreshold',
                EvaluationPeriods=2,
                MetricName='4XXError',
                Namespace='AWS/ApiGateway',
                Period=300,
                Statistic='Sum',
                Threshold=monitoring_config.error_rate_threshold,
                ActionsEnabled=True,
                AlarmDescription=f'Error rate alarm for {deployment_config.api_name} {stage_config.name}',
                Dimensions=[
                    {'Name': 'ApiName', 'Value': deployment_config.api_name},
                    {'Name': 'Stage', 'Value': stage_config.name}
                ],
                Unit='Count'
            )
            alarms.append({'name': error_alarm_name, 'type': 'error_rate'})
            
            # Latency alarm
            latency_alarm_name = f"{deployment_config.api_name}-{stage_config.name}-Latency"
            self.cloudwatch.put_metric_alarm(
                AlarmName=latency_alarm_name,
                ComparisonOperator='GreaterThanThreshold',
                EvaluationPeriods=2,
                MetricName='Latency',
                Namespace='AWS/ApiGateway',
                Period=300,
                Statistic='Average',
                Threshold=monitoring_config.latency_threshold,
                ActionsEnabled=True,
                AlarmDescription=f'Latency alarm for {deployment_config.api_name} {stage_config.name}',
                Dimensions=[
                    {'Name': 'ApiName', 'Value': deployment_config.api_name},
                    {'Name': 'Stage', 'Value': stage_config.name}
                ],
                Unit='Milliseconds'
            )
            alarms.append({'name': latency_alarm_name, 'type': 'latency'})
            
            # Throttle alarm
            throttle_alarm_name = f"{deployment_config.api_name}-{stage_config.name}-Throttles"
            self.cloudwatch.put_metric_alarm(
                AlarmName=throttle_alarm_name,
                ComparisonOperator='GreaterThanThreshold',
                EvaluationPeriods=1,
                MetricName='ThrottledRequests',
                Namespace='AWS/ApiGateway',
                Period=300,
                Statistic='Sum',
                Threshold=monitoring_config.throttle_rate_threshold,
                ActionsEnabled=True,
                AlarmDescription=f'Throttle alarm for {deployment_config.api_name} {stage_config.name}',
                Dimensions=[
                    {'Name': 'ApiName', 'Value': deployment_config.api_name},
                    {'Name': 'Stage', 'Value': stage_config.name}
                ],
                Unit='Count'
            )
            alarms.append({'name': throttle_alarm_name, 'type': 'throttle'})
        
        return alarms
    
    def _create_dashboard_definition(self, api_id: str, 
                                   deployment_config: APIDeploymentConfig) -> Dict[str, Any]:
        """Create CloudWatch dashboard definition for API Gateway"""
        
        widgets = []
        
        # API Overview metrics
        widgets.append({
            "type": "metric",
            "x": 0, "y": 0, "width": 12, "height": 6,
            "properties": {
                "metrics": [
                    ["AWS/ApiGateway", "Count", "ApiName", deployment_config.api_name],
                    [".", "4XXError", ".", "."],
                    [".", "5XXError", ".", "."],
                    [".", "Latency", ".", "."]
                ],
                "period": 300,
                "stat": "Sum",
                "region": self.cloudwatch.meta.region_name,
                "title": f"{deployment_config.api_name} - Overview"
            }
        })
        
        # Stage-specific metrics
        for i, stage_config in enumerate(deployment_config.stages):
            y_position = 6 + (i * 6)
            
            widgets.append({
                "type": "metric",
                "x": 0, "y": y_position, "width": 12, "height": 6,
                "properties": {
                    "metrics": [
                        ["AWS/ApiGateway", "Count", "ApiName", deployment_config.api_name, "Stage", stage_config.name],
                        [".", "Latency", ".", ".", ".", "."],
                        [".", "4XXError", ".", ".", ".", "."],
                        [".", "5XXError", ".", ".", ".", "."]
                    ],
                    "period": 300,
                    "stat": "Average",
                    "region": self.cloudwatch.meta.region_name,
                    "title": f"{deployment_config.api_name} - {stage_config.name} Stage"
                }
            })
        
        return {
            "widgets": widgets
        }
    
    def perform_api_deployment(self, api_id: str, deployment_config: Dict[str, Any]) -> Dict[str, Any]:
        """Perform automated API deployment with validation and rollback capabilities"""
        
        deployment_result = {
            'deployment_id': None,
            'status': 'pending',
            'validation_results': {},
            'performance_baseline': {},
            'rollback_info': None,
            'deployment_time': datetime.now().isoformat()
        }
        
        try:
            # Pre-deployment validation
            validation_results = self._validate_api_before_deployment(api_id, deployment_config)
            deployment_result['validation_results'] = validation_results
            
            if not validation_results['passed']:
                deployment_result['status'] = 'failed'
                deployment_result['error'] = 'Pre-deployment validation failed'
                return deployment_result
            
            # Capture current performance baseline
            baseline = self._capture_performance_baseline(api_id, deployment_config.get('stage', 'prod'))
            deployment_result['performance_baseline'] = baseline
            
            # Store rollback information
            rollback_info = self._prepare_rollback_info(api_id, deployment_config.get('stage', 'prod'))
            deployment_result['rollback_info'] = rollback_info
            
            # Perform deployment based on strategy
            deployment_strategy = deployment_config.get('strategy', 'blue_green')
            
            if deployment_strategy == 'blue_green':
                deployment_id = self._perform_blue_green_deployment(api_id, deployment_config)
            elif deployment_strategy == 'canary':
                deployment_id = self._perform_canary_deployment(api_id, deployment_config)
            else:
                deployment_id = self._perform_standard_deployment(api_id, deployment_config)
            
            deployment_result['deployment_id'] = deployment_id
            deployment_result['status'] = 'success'
            
            # Post-deployment validation
            post_validation = self._validate_api_after_deployment(api_id, deployment_config)
            deployment_result['post_validation'] = post_validation
            
            if not post_validation['passed']:
                self.logger.warning("Post-deployment validation failed, considering rollback")
                if deployment_config.get('auto_rollback', True):
                    self._perform_automatic_rollback(api_id, rollback_info)
                    deployment_result['status'] = 'rolled_back'
            
            return deployment_result
            
        except Exception as e:
            self.logger.error(f"Deployment failed for API {api_id}: {e}")
            deployment_result['status'] = 'failed'
            deployment_result['error'] = str(e)
            
            # Attempt rollback on failure
            if deployment_result.get('rollback_info') and deployment_config.get('auto_rollback', True):
                try:
                    self._perform_automatic_rollback(api_id, deployment_result['rollback_info'])
                    deployment_result['status'] = 'rolled_back'
                except Exception as rollback_error:
                    self.logger.error(f"Rollback failed: {rollback_error}")
                    deployment_result['rollback_error'] = str(rollback_error)
            
            return deployment_result
    
    def _perform_blue_green_deployment(self, api_id: str, config: Dict[str, Any]) -> str:
        """Perform blue-green deployment for API Gateway"""
        
        stage_name = config.get('stage', 'prod')
        
        # Create new deployment (green)
        green_deployment = self.api_gateway.create_deployment(
            restApiId=api_id,
            stageName=f"{stage_name}-green",
            description=f"Green deployment for {stage_name} - {datetime.now().isoformat()}"
        )
        
        # Wait for green deployment to be ready
        time.sleep(10)
        
        # Validate green deployment
        green_validation = self._validate_deployment_health(api_id, f"{stage_name}-green")
        
        if green_validation['healthy']:
            # Switch traffic to green
            self.api_gateway.update_stage(
                restApiId=api_id,
                stageName=stage_name,
                patchOps=[
                    {
                        'op': 'replace',
                        'path': '/deploymentId',
                        'value': green_deployment['id']
                    }
                ]
            )
            
            # Clean up green stage
            try:
                self.api_gateway.delete_stage(
                    restApiId=api_id,
                    stageName=f"{stage_name}-green"
                )
            except:
                pass  # Stage might not exist
            
            return green_deployment['id']
        else:
            raise Exception("Green deployment validation failed")
    
    def _perform_canary_deployment(self, api_id: str, config: Dict[str, Any]) -> str:
        """Perform canary deployment for API Gateway"""
        
        stage_name = config.get('stage', 'prod')
        canary_percentage = config.get('canary_percentage', 10)
        
        # Create new deployment
        new_deployment = self.api_gateway.create_deployment(
            restApiId=api_id,
            description=f"Canary deployment for {stage_name} - {datetime.now().isoformat()}"
        )
        
        # Update stage with canary configuration
        self.api_gateway.update_stage(
            restApiId=api_id,
            stageName=stage_name,
            patchOps=[
                {
                    'op': 'replace',
                    'path': '/canarySettings/deploymentId',
                    'value': new_deployment['id']
                },
                {
                    'op': 'replace',
                    'path': '/canarySettings/percentTraffic',
                    'value': str(canary_percentage)
                },
                {
                    'op': 'replace',
                    'path': '/canarySettings/useStageCache',
                    'value': 'false'
                }
            ]
        )
        
        # Monitor canary for specified duration
        canary_duration = config.get('canary_duration_minutes', 30)
        self.logger.info(f"Monitoring canary deployment for {canary_duration} minutes")
        
        # In a real implementation, you would monitor metrics here
        time.sleep(60)  # Simplified monitoring
        
        # Promote canary to full deployment if healthy
        canary_health = self._monitor_canary_health(api_id, stage_name, canary_duration)
        
        if canary_health['healthy']:
            # Promote canary to 100%
            self.api_gateway.update_stage(
                restApiId=api_id,
                stageName=stage_name,
                patchOps=[
                    {
                        'op': 'replace',
                        'path': '/deploymentId',
                        'value': new_deployment['id']
                    },
                    {
                        'op': 'remove',
                        'path': '/canarySettings'
                    }
                ]
            )
        else:
            # Remove canary deployment
            self.api_gateway.update_stage(
                restApiId=api_id,
                stageName=stage_name,
                patchOps=[
                    {
                        'op': 'remove',
                        'path': '/canarySettings'
                    }
                ]
            )
            raise Exception("Canary deployment failed health checks")
        
        return new_deployment['id']
    
    def generate_api_analytics_report(self, api_id: str, 
                                    time_range_days: int = 7) -> Dict[str, Any]:
        """Generate comprehensive analytics report for API Gateway"""
        
        end_time = datetime.now()
        start_time = end_time - timedelta(days=time_range_days)
        
        report = {
            'api_id': api_id,
            'report_period': {
                'start': start_time.isoformat(),
                'end': end_time.isoformat(),
                'days': time_range_days
            },
            'traffic_analytics': {},
            'performance_metrics': {},
            'error_analysis': {},
            'cost_analysis': {},
            'security_insights': {},
            'recommendations': []
        }
        
        try:
            # Get API details
            api_info = self._get_api_info(api_id)
            report['api_info'] = api_info
            
            # Collect traffic analytics
            traffic_metrics = self._collect_traffic_metrics(api_id, start_time, end_time)
            report['traffic_analytics'] = traffic_metrics
            
            # Collect performance metrics
            performance_metrics = self._collect_performance_metrics(api_id, start_time, end_time)
            report['performance_metrics'] = performance_metrics
            
            # Analyze errors
            error_analysis = self._analyze_api_errors(api_id, start_time, end_time)
            report['error_analysis'] = error_analysis
            
            # Calculate cost estimates
            cost_analysis = self._calculate_api_costs(api_id, traffic_metrics)
            report['cost_analysis'] = cost_analysis
            
            # Security insights
            security_insights = self._analyze_security_patterns(api_id, start_time, end_time)
            report['security_insights'] = security_insights
            
            # Generate recommendations
            recommendations = self._generate_optimization_recommendations(report)
            report['recommendations'] = recommendations
            
            return report
            
        except Exception as e:
            self.logger.error(f"Failed to generate analytics report for API {api_id}: {e}")
            report['error'] = str(e)
            return report
    
    def _collect_traffic_metrics(self, api_id: str, start_time: datetime, 
                               end_time: datetime) -> Dict[str, Any]:
        """Collect traffic metrics from CloudWatch"""
        
        metrics = {}
        
        try:
            # Get request count
            count_response = self.cloudwatch.get_metric_statistics(
                Namespace='AWS/ApiGateway',
                MetricName='Count',
                Dimensions=[{'Name': 'ApiName', 'Value': api_id}],
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,  # 1 hour periods
                Statistics=['Sum']
            )
            
            total_requests = sum(point['Sum'] for point in count_response['Datapoints'])
            metrics['total_requests'] = total_requests
            metrics['hourly_breakdown'] = [
                {
                    'timestamp': point['Timestamp'].isoformat(),
                    'requests': point['Sum']
                }
                for point in sorted(count_response['Datapoints'], key=lambda x: x['Timestamp'])
            ]
            
            # Calculate average requests per hour
            hours = len(count_response['Datapoints'])
            metrics['avg_requests_per_hour'] = total_requests / max(hours, 1)
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Failed to collect traffic metrics: {e}")
            return {'error': str(e)}
    
    def _collect_performance_metrics(self, api_id: str, start_time: datetime, 
                                   end_time: datetime) -> Dict[str, Any]:
        """Collect performance metrics from CloudWatch"""
        
        metrics = {}
        
        try:
            # Get latency metrics
            latency_response = self.cloudwatch.get_metric_statistics(
                Namespace='AWS/ApiGateway',
                MetricName='Latency',
                Dimensions=[{'Name': 'ApiName', 'Value': api_id}],
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,
                Statistics=['Average', 'Maximum', 'Minimum']
            )
            
            if latency_response['Datapoints']:
                avg_latency = sum(point['Average'] for point in latency_response['Datapoints']) / len(latency_response['Datapoints'])
                max_latency = max(point['Maximum'] for point in latency_response['Datapoints'])
                min_latency = min(point['Minimum'] for point in latency_response['Datapoints'])
                
                metrics['latency'] = {
                    'average_ms': round(avg_latency, 2),
                    'maximum_ms': round(max_latency, 2),
                    'minimum_ms': round(min_latency, 2)
                }
            
            # Get integration latency
            integration_latency_response = self.cloudwatch.get_metric_statistics(
                Namespace='AWS/ApiGateway',
                MetricName='IntegrationLatency',
                Dimensions=[{'Name': 'ApiName', 'Value': api_id}],
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,
                Statistics=['Average']
            )
            
            if integration_latency_response['Datapoints']:
                avg_integration_latency = sum(point['Average'] for point in integration_latency_response['Datapoints']) / len(integration_latency_response['Datapoints'])
                metrics['integration_latency_ms'] = round(avg_integration_latency, 2)
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Failed to collect performance metrics: {e}")
            return {'error': str(e)}
    
    def _validate_openapi_spec(self, spec: Dict[str, Any]) -> bool:
        """Validate OpenAPI specification"""
        required_fields = ['openapi', 'info', 'paths']
        for field in required_fields:
            if field not in spec:
                raise ValueError(f"Missing required field in OpenAPI spec: {field}")
        return True
    
    def _enhance_openapi_spec(self, spec: Dict[str, Any], 
                             config: APIDeploymentConfig) -> Dict[str, Any]:
        """Enhance OpenAPI spec with enterprise configurations"""
        enhanced_spec = spec.copy()
        
        # Add security schemes if not present
        if 'components' not in enhanced_spec:
            enhanced_spec['components'] = {}
        
        if 'securitySchemes' not in enhanced_spec['components']:
            enhanced_spec['components']['securitySchemes'] = {
                'ApiKeyAuth': {
                    'type': 'apiKey',
                    'in': 'header',
                    'name': 'X-API-Key'
                },
                'OAuth2': {
                    'type': 'oauth2',
                    'flows': {
                        'authorizationCode': {
                            'authorizationUrl': 'https://example.com/oauth/authorize',
                            'tokenUrl': 'https://example.com/oauth/token',
                            'scopes': {
                                'read': 'Read access',
                                'write': 'Write access'
                            }
                        }
                    }
                }
            }
        
        # Add request validation
        for path, methods in enhanced_spec.get('paths', {}).items():
            for method, operation in methods.items():
                if method.upper() in ['POST', 'PUT', 'PATCH']:
                    operation['x-amazon-apigateway-request-validator'] = 'body-and-params'
        
        # Add integration configurations
        enhanced_spec['x-amazon-apigateway-request-validators'] = {
            'body-and-params': {
                'validateRequestBody': True,
                'validateRequestParameters': True
            },
            'params-only': {
                'validateRequestBody': False,
                'validateRequestParameters': True
            }
        }
        
        return enhanced_spec
    
    def _register_api(self, api_id: str, config: APIDeploymentConfig, 
                     creation_result: Dict[str, Any]) -> None:
        """Register API in enterprise registry"""
        self.api_registry[api_id] = {
            'config': asdict(config),
            'creation_result': creation_result,
            'registered_at': datetime.now().isoformat()
        }

# Example usage and configuration
if __name__ == "__main__":
    # Initialize the API Gateway manager
    api_manager = EnterpriseAPIGatewayManager()
    
    # Example OpenAPI specification
    openapi_spec = {
        "openapi": "3.0.1",
        "info": {
            "title": "User Management API",
            "version": "1.0.0",
            "description": "Enterprise user management API"
        },
        "paths": {
            "/users": {
                "get": {
                    "summary": "Get users",
                    "responses": {
                        "200": {
                            "description": "List of users"
                        }
                    }
                },
                "post": {
                    "summary": "Create user",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "name": {"type": "string"},
                                        "email": {"type": "string"}
                                    },
                                    "required": ["name", "email"]
                                }
                            }
                        }
                    },
                    "responses": {
                        "201": {
                            "description": "User created"
                        }
                    }
                }
            }
        }
    }
    
    # Example deployment configuration
    deployment_config = APIDeploymentConfig(
        api_name="user-management-api",
        api_description="Enterprise user management API with DevOps automation",
        api_type="REST",
        endpoint_type="REGIONAL",
        stages=[
            APIStage(
                name="dev",
                description="Development environment",
                variables={"env": "development", "debug": "true"},
                throttling={"rate": 100, "burst": 200},
                caching_enabled=False,
                logging_level="INFO",
                data_trace_enabled=True,
                metrics_enabled=True
            ),
            APIStage(
                name="prod",
                description="Production environment",
                variables={"env": "production", "debug": "false"},
                throttling={"rate": 1000, "burst": 2000},
                caching_enabled=True,
                cache_ttl=300,
                logging_level="ERROR",
                data_trace_enabled=False,
                metrics_enabled=True
            )
        ],
        cors_config={
            "allowOrigins": ["https://myapp.com"],
            "allowMethods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allowHeaders": ["Content-Type", "Authorization", "X-API-Key"]
        }
    )
    
    # Create API with enterprise configuration
    try:
        result = api_manager.create_api_from_openapi(openapi_spec, deployment_config)
        print(f"API created successfully: {result['api_id']}")
        
        # Generate analytics report
        report = api_manager.generate_api_analytics_report(result['api_id'], time_range_days=7)
        print(f"Analytics report generated for API: {result['api_id']}")
        
    except Exception as e:
        print(f"Failed to create API: {e}")
```

### API Gateway Testing and Quality Assurance

```python
# api_gateway_testing.py - Comprehensive testing framework for API Gateway
import requests
import json
import time
import concurrent.futures
import statistics
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import boto3
import logging

@dataclass
class TestCase:
    name: str
    method: str
    path: str
    headers: Dict[str, str] = None
    body: Optional[Any] = None
    expected_status: int = 200
    expected_response: Optional[Dict] = None
    timeout: int = 30
    
@dataclass
class LoadTestConfig:
    concurrent_users: int
    duration_seconds: int
    ramp_up_seconds: int
    test_cases: List[TestCase]

class APIGatewayTestingFramework:
    """
    Comprehensive testing framework for API Gateway with functional testing,
    load testing, security testing, and performance validation.
    """
    
    def __init__(self, base_url: str, api_key: str = None):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.session = requests.Session()
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Test results storage
        self.test_results = []
        
        # Default headers
        self.default_headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'APIGatewayTestFramework/1.0'
        }
        
        if self.api_key:
            self.default_headers['X-API-Key'] = self.api_key
    
    def run_functional_tests(self, test_cases: List[TestCase]) -> Dict[str, Any]:
        """Run functional tests against API Gateway endpoints"""
        
        test_results = {
            'total_tests': len(test_cases),
            'passed': 0,
            'failed': 0,
            'test_details': [],
            'execution_time': 0
        }
        
        start_time = time.time()
        
        for test_case in test_cases:
            result = self._execute_test_case(test_case)
            test_results['test_details'].append(result)
            
            if result['passed']:
                test_results['passed'] += 1
            else:
                test_results['failed'] += 1
        
        test_results['execution_time'] = time.time() - start_time
        test_results['success_rate'] = (test_results['passed'] / test_results['total_tests']) * 100
        
        return test_results
    
    def run_load_test(self, config: LoadTestConfig) -> Dict[str, Any]:
        """Run load test with specified configuration"""
        
        load_test_results = {
            'config': config,
            'metrics': {
                'total_requests': 0,
                'successful_requests': 0,
                'failed_requests': 0,
                'average_response_time': 0,
                'min_response_time': float('inf'),
                'max_response_time': 0,
                'requests_per_second': 0,
                'error_rate': 0
            },
            'response_times': [],
            'errors': [],
            'timeline': []
        }
        
        # Prepare test execution
        total_requests = 0
        response_times = []
        errors = []
        
        start_time = time.time()
        
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=config.concurrent_users) as executor:
                # Submit load test tasks
                futures = []
                
                for user_id in range(config.concurrent_users):
                    future = executor.submit(
                        self._run_user_load_test, 
                        user_id, 
                        config, 
                        start_time
                    )
                    futures.append(future)
                
                # Collect results from all users
                for future in concurrent.futures.as_completed(futures):
                    user_results = future.result()
                    total_requests += user_results['requests']
                    response_times.extend(user_results['response_times'])
                    errors.extend(user_results['errors'])
            
            # Calculate metrics
            end_time = time.time()
            duration = end_time - start_time
            
            load_test_results['metrics']['total_requests'] = total_requests
            load_test_results['metrics']['successful_requests'] = total_requests - len(errors)
            load_test_results['metrics']['failed_requests'] = len(errors)
            load_test_results['metrics']['requests_per_second'] = total_requests / duration
            load_test_results['metrics']['error_rate'] = (len(errors) / max(total_requests, 1)) * 100
            
            if response_times:
                load_test_results['metrics']['average_response_time'] = statistics.mean(response_times)
                load_test_results['metrics']['min_response_time'] = min(response_times)
                load_test_results['metrics']['max_response_time'] = max(response_times)
                load_test_results['metrics']['median_response_time'] = statistics.median(response_times)
                load_test_results['metrics']['95th_percentile'] = self._calculate_percentile(response_times, 95)
                load_test_results['metrics']['99th_percentile'] = self._calculate_percentile(response_times, 99)
            
            load_test_results['response_times'] = response_times
            load_test_results['errors'] = errors
            
            return load_test_results
            
        except Exception as e:
            self.logger.error(f"Load test failed: {e}")
            load_test_results['error'] = str(e)
            return load_test_results
    
    def run_security_scan(self) -> Dict[str, Any]:
        """Run security scan against API Gateway"""
        
        security_results = {
            'vulnerabilities': [],
            'security_headers': {},
            'ssl_analysis': {},
            'authentication_tests': {},
            'injection_tests': {},
            'overall_score': 0
        }
        
        try:
            # Test security headers
            security_results['security_headers'] = self._test_security_headers()
            
            # Test SSL/TLS configuration
            security_results['ssl_analysis'] = self._analyze_ssl_configuration()
            
            # Test authentication mechanisms
            security_results['authentication_tests'] = self._test_authentication()
            
            # Test for injection vulnerabilities
            security_results['injection_tests'] = self._test_injection_vulnerabilities()
            
            # Calculate overall security score
            security_results['overall_score'] = self._calculate_security_score(security_results)
            
            return security_results
            
        except Exception as e:
            self.logger.error(f"Security scan failed: {e}")
            security_results['error'] = str(e)
            return security_results
    
    def _execute_test_case(self, test_case: TestCase) -> Dict[str, Any]:
        """Execute a single test case"""
        
        result = {
            'name': test_case.name,
            'method': test_case.method,
            'path': test_case.path,
            'passed': False,
            'response_time': 0,
            'status_code': None,
            'response_body': None,
            'error': None
        }
        
        try:
            # Prepare request
            url = f"{self.base_url}{test_case.path}"
            headers = self.default_headers.copy()
            
            if test_case.headers:
                headers.update(test_case.headers)
            
            # Execute request
            start_time = time.time()
            
            response = self.session.request(
                method=test_case.method,
                url=url,
                headers=headers,
                json=test_case.body if test_case.body else None,
                timeout=test_case.timeout
            )
            
            result['response_time'] = (time.time() - start_time) * 1000  # ms
            result['status_code'] = response.status_code
            
            try:
                result['response_body'] = response.json()
            except:
                result['response_body'] = response.text
            
            # Validate response
            if response.status_code == test_case.expected_status:
                if test_case.expected_response:
                    if self._validate_response_content(result['response_body'], test_case.expected_response):
                        result['passed'] = True
                    else:
                        result['error'] = "Response content validation failed"
                else:
                    result['passed'] = True
            else:
                result['error'] = f"Expected status {test_case.expected_status}, got {response.status_code}"
            
        except requests.RequestException as e:
            result['error'] = f"Request failed: {str(e)}"
        except Exception as e:
            result['error'] = f"Test execution failed: {str(e)}"
        
        return result
    
    def _run_user_load_test(self, user_id: int, config: LoadTestConfig, 
                           start_time: float) -> Dict[str, Any]:
        """Run load test for a single virtual user"""
        
        user_results = {
            'user_id': user_id,
            'requests': 0,
            'response_times': [],
            'errors': []
        }
        
        # Ramp up delay
        ramp_delay = (config.ramp_up_seconds / config.concurrent_users) * user_id
        time.sleep(ramp_delay)
        
        test_end_time = start_time + config.duration_seconds
        
        while time.time() < test_end_time:
            for test_case in config.test_cases:
                if time.time() >= test_end_time:
                    break
                
                try:
                    request_start = time.time()
                    result = self._execute_test_case(test_case)
                    response_time = (time.time() - request_start) * 1000
                    
                    user_results['requests'] += 1
                    user_results['response_times'].append(response_time)
                    
                    if not result['passed']:
                        user_results['errors'].append({
                            'test_case': test_case.name,
                            'error': result['error'],
                            'timestamp': time.time()
                        })
                
                except Exception as e:
                    user_results['errors'].append({
                        'test_case': test_case.name,
                        'error': str(e),
                        'timestamp': time.time()
                    })
                
                # Small delay between requests
                time.sleep(0.1)
        
        return user_results
    
    def _test_security_headers(self) -> Dict[str, Any]:
        """Test for security headers in API responses"""
        
        security_headers_test = {
            'headers_found': {},
            'missing_headers': [],
            'score': 0
        }
        
        required_headers = [
            'X-Content-Type-Options',
            'X-Frame-Options',
            'X-XSS-Protection',
            'Strict-Transport-Security',
            'Content-Security-Policy'
        ]
        
        try:
            response = self.session.get(f"{self.base_url}/")
            
            for header in required_headers:
                if header in response.headers:
                    security_headers_test['headers_found'][header] = response.headers[header]
                else:
                    security_headers_test['missing_headers'].append(header)
            
            # Calculate score
            security_headers_test['score'] = (len(security_headers_test['headers_found']) / len(required_headers)) * 100
            
        except Exception as e:
            security_headers_test['error'] = str(e)
        
        return security_headers_test
    
    def _calculate_percentile(self, values: List[float], percentile: int) -> float:
        """Calculate the nth percentile of a list of values"""
        if not values:
            return 0
        
        sorted_values = sorted(values)
        index = (percentile / 100) * (len(sorted_values) - 1)
        
        if index.is_integer():
            return sorted_values[int(index)]
        else:
            lower = sorted_values[int(index)]
            upper = sorted_values[int(index) + 1]
            return lower + (upper - lower) * (index - int(index))

# Example test configurations
EXAMPLE_FUNCTIONAL_TESTS = [
    TestCase(
        name="Get Users List",
        method="GET",
        path="/users",
        expected_status=200
    ),
    TestCase(
        name="Create New User",
        method="POST",
        path="/users",
        body={"name": "John Doe", "email": "john@example.com"},
        expected_status=201
    ),
    TestCase(
        name="Get User by ID",
        method="GET",
        path="/users/123",
        expected_status=200
    ),
    TestCase(
        name="Update User",
        method="PUT",
        path="/users/123",
        body={"name": "Jane Doe", "email": "jane@example.com"},
        expected_status=200
    ),
    TestCase(
        name="Delete User",
        method="DELETE",
        path="/users/123",
        expected_status=204
    )
]

EXAMPLE_LOAD_TEST_CONFIG = LoadTestConfig(
    concurrent_users=10,
    duration_seconds=60,
    ramp_up_seconds=10,
    test_cases=[
        TestCase(
            name="Load Test - Get Users",
            method="GET",
            path="/users",
            expected_status=200
        )
    ]
)

# Example usage
if __name__ == "__main__":
    # Initialize testing framework
    tester = APIGatewayTestingFramework(
        base_url="https://your-api-id.execute-api.region.amazonaws.com/prod",
        api_key="your-api-key"
    )
    
    # Run functional tests
    functional_results = tester.run_functional_tests(EXAMPLE_FUNCTIONAL_TESTS)
    print(f"Functional tests completed: {functional_results['passed']}/{functional_results['total_tests']} passed")
    
    # Run load test
    load_results = tester.run_load_test(EXAMPLE_LOAD_TEST_CONFIG)
    print(f"Load test completed: {load_results['metrics']['requests_per_second']:.2f} RPS")
    
    # Run security scan
    security_results = tester.run_security_scan()
    print(f"Security scan completed: Score {security_results['overall_score']}/100")
```

## Best Practices

### Development Best Practices
- **API-First Design:** Start with OpenAPI specifications and contract-driven development
- **Version Management:** Implement proper API versioning strategies for backward compatibility
- **Request Validation:** Use built-in request validation to reduce backend load
- **Response Transformation:** Leverage mapping templates for data transformation
- **Error Handling:** Implement consistent error response formats across all endpoints

### Security Best Practices
- **Authentication:** Implement multiple auth methods (IAM, API Keys, Cognito, Lambda Authorizers)
- **Authorization:** Use fine-grained permissions and request context validation
- **Rate Limiting:** Configure throttling and usage plans to protect backend services
- **Input Validation:** Validate all input parameters and request bodies
- **CORS Configuration:** Properly configure Cross-Origin Resource Sharing policies

### Performance Optimization
- **Caching Strategy:** Implement response caching for frequently accessed data
- **Compression:** Enable response compression for large payloads
- **Connection Pooling:** Use HTTP/2 and connection reuse for better performance
- **Regional Deployment:** Choose appropriate endpoint types for your use case
- **Monitoring:** Set up comprehensive monitoring and alerting for performance metrics

### DevOps Integration
- **Infrastructure as Code:** Use CDK, CloudFormation, or Terraform for API deployment
- **Automated Testing:** Implement comprehensive testing pipelines for API validation
- **Blue-Green Deployments:** Use deployment strategies for zero-downtime releases
- **Monitoring and Alerting:** Set up CloudWatch dashboards and alarms for operational visibility
- **Cost Optimization:** Monitor usage patterns and optimize pricing models accordingly