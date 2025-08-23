# AWS API Gateway: Enterprise API Management & Integration Platform

> **Service Type:** Application Integration | **Scope:** Regional | **Serverless:** Yes

## Overview

AWS API Gateway is a comprehensive, fully managed API management service that enables enterprises to create, deploy, secure, and monitor APIs at massive scale. It serves as the critical integration layer between client applications and backend services, providing advanced traffic management, security controls, and operational insights essential for modern microservices architectures and digital transformation initiatives.

## Core Architecture Components

- **API Gateway Engine:** High-performance request routing and processing with built-in caching and transformation capabilities
- **Integration Framework:** Native connectors for Lambda, HTTP/HTTPS backends, AWS services, and VPC resources
- **Security Layer:** Multi-layered authentication, authorization, and threat protection with WAF integration
- **Traffic Management:** Advanced throttling, rate limiting, and request/response transformation
- **Monitoring & Analytics:** Real-time metrics, logging, and tracing with CloudWatch and X-Ray integration
- **Developer Portal:** Self-service API documentation, SDK generation, and developer onboarding
- **Deployment Pipeline:** Multi-stage deployment with canary releases and rollback capabilities

## DevOps & Enterprise Use Cases

### API-First Development & Architecture
- **Microservices API Gateway:** Central entry point for distributed microservices with service discovery integration
- **API Contract Management:** OpenAPI specification-driven development with automated validation and testing
- **Cross-Platform SDK Generation:** Automated client library generation for mobile, web, and server applications
- **API Versioning Strategy:** Backward-compatible API evolution with version-specific routing and deprecation management

### CI/CD Pipeline Integration
- **Infrastructure as Code:** Automated API deployment through CloudFormation, Terraform, and CDK templates
- **Multi-Environment Management:** Isolated dev, staging, and production API stages with environment-specific configurations
- **Blue-Green API Deployments:** Zero-downtime deployments with instant traffic switching and automated rollback
- **Canary Release Automation:** Gradual traffic shifting with automated performance monitoring and rollback triggers

### Security & Compliance Operations
- **Zero Trust API Security:** Multi-factor authentication with IAM, Cognito, and custom authorizers
- **Compliance Automation:** GDPR, HIPAA, and SOC 2 compliance with automated audit logging and data protection
- **Threat Protection Integration:** AWS WAF integration for DDoS protection, SQL injection, and XSS prevention
- **API Key Management:** Centralized API key lifecycle management with usage tracking and automated rotation

### Monitoring & Operational Excellence
- **Real-Time Observability:** Comprehensive API analytics with latency, error rate, and throughput monitoring
- **Proactive Alerting:** CloudWatch integration with custom metrics and automated incident response
- **Performance Optimization:** Caching strategies, compression, and request optimization for enhanced user experience
- **Cost Management:** Usage-based billing with detailed cost allocation and optimization recommendations

## Service Features & Capabilities

### API Types & Deployment Models
- **REST APIs:** Full-featured APIs with extensive customization, caching, and request/response transformation
- **HTTP APIs:** Cost-optimized, low-latency APIs designed for serverless and microservices architectures
- **WebSocket APIs:** Real-time bidirectional communication with connection management and routing
- **Private APIs:** VPC-only access for internal services with enhanced security and network isolation

### Integration Patterns
- **Lambda Proxy Integration:** Direct Lambda function invocation with event context and response formatting
- **HTTP/HTTPS Integration:** Backend service integration with custom headers, query parameters, and body transformation
- **AWS Service Integration:** Direct integration with S3, DynamoDB, SNS, SQS, and other AWS services
- **VPC Link Integration:** Private connectivity to resources in VPC through Network Load Balancers

### Security & Authentication
- **IAM Authentication:** Role-based access control with AWS credentials and temporary tokens
- **API Key Management:** Usage tracking, quotas, and lifecycle management for API consumers
- **Cognito Integration:** User pool and identity pool authentication for web and mobile applications
- **Custom Authorizers:** Lambda-based authorization logic with JWT token validation and custom claims
- **OAuth 2.0 & OIDC:** Standards-based authentication with third-party identity providers
- **WAF Integration:** Application-layer protection against common web exploits and vulnerabilities

### Traffic Management & Performance
- **Request/Response Transformation:** JSON-to-XML conversion, header manipulation, and payload modification
- **Caching:** Response caching with TTL configuration and cache key customization for improved performance
- **Throttling & Rate Limiting:** Per-client rate limiting, burst capacity management, and backend protection
- **CORS Support:** Cross-origin resource sharing configuration for web application integration

## Configuration & Setup

### Basic API Gateway Setup
```bash
# Create REST API
aws apigateway create-rest-api \
  --name "enterprise-api-gateway" \
  --description "Enterprise API Gateway for microservices architecture" \
  --endpoint-configuration types=REGIONAL \
  --tags Environment=Production,ManagedBy=DevOps

# Create API resources and methods
aws apigateway create-resource \
  --rest-api-id [api-id] \
  --parent-id [root-resource-id] \
  --path-part "users"

# Configure method with Lambda integration
aws apigateway put-method \
  --rest-api-id [api-id] \
  --resource-id [resource-id] \
  --http-method GET \
  --authorization-type AWS_IAM \
  --request-parameters method.request.querystring.limit=false
```

### Advanced Enterprise Configuration
```bash
# Create HTTP API with enhanced features
aws apigatewayv2 create-api \
  --name "enterprise-http-api" \
  --protocol-type HTTP \
  --description "High-performance HTTP API for microservices" \
  --cors-configuration '{
    "AllowOrigins": ["https://enterprise-app.com"],
    "AllowMethods": ["GET", "POST", "PUT", "DELETE"],
    "AllowHeaders": ["Authorization", "Content-Type"],
    "MaxAge": 86400
  }' \
  --tags Environment=Production,Team=Platform,CostCenter=Engineering

# Set up custom domain with SSL certificate
aws apigateway create-domain-name \
  --domain-name "api.enterprise.com" \
  --certificate-arn "arn:aws:acm:region:account:certificate/cert-id" \
  --security-policy TLS_1_2 \
  --endpoint-configuration types=REGIONAL
```

## Enterprise Implementation Examples

### Example 1: Microservices API Gateway with Authentication and Monitoring

**Business Requirement:** Build enterprise API gateway for microservices architecture supporting 1M+ requests/day with comprehensive security, monitoring, and automated deployment.

**Implementation Steps:**
1. **Enterprise API Gateway Architecture Setup**
   ```bash
   # Create production-ready REST API
   aws apigateway create-rest-api \
     --name "microservices-gateway-prod" \
     --description "Production API Gateway for microservices ecosystem" \
     --endpoint-configuration types=REGIONAL \
     --policy '{
       "Version": "2012-10-17",
       "Statement": [
         {
           "Effect": "Allow",
           "Principal": "*",
           "Action": "execute-api:Invoke",
           "Resource": "*",
           "Condition": {
             "IpAddress": {
               "aws:SourceIp": ["10.0.0.0/8", "172.16.0.0/12"]
             }
           }
         }
       ]
     }'
   
   # Enable CloudWatch logging and X-Ray tracing
   aws apigateway update-stage \
     --rest-api-id [api-id] \
     --stage-name prod \
     --patch-ops '[
       {
         "op": "replace",
         "path": "/*/logging/loglevel",
         "value": "INFO"
       },
       {
         "op": "replace",
         "path": "/tracingEnabled",
         "value": "true"
       },
       {
         "op": "replace",
         "path": "/*/throttle/rateLimit",
         "value": "10000"
       },
       {
         "op": "replace",
         "path": "/*/throttle/burstLimit",
         "value": "5000"
       }
     ]'
   ```

2. **Comprehensive Security Implementation**
   ```python
   import boto3
   import json
   from datetime import datetime, timedelta
   import jwt
   
   class EnterpriseAPIGatewayManager:
       def __init__(self):
           self.apigateway = boto3.client('apigateway')
           self.cognito = boto3.client('cognito-idp')
           self.lambda_client = boto3.client('lambda')
           
       def setup_enterprise_authentication(self, api_id, user_pool_id):
           """Setup comprehensive authentication with Cognito and custom authorizers"""
           try:
               # Create Cognito authorizer
               cognito_authorizer = self.apigateway.create_authorizer(
                   restApiId=api_id,
                   name='enterprise-cognito-authorizer',
                   type='COGNITO_USER_POOLS',
                   providerARNs=[
                       f'arn:aws:cognito-idp:{boto3.Session().region_name}:{boto3.STS().get_caller_identity()["Account"]}:userpool/{user_pool_id}'
                   ],
                   identitySource='method.request.header.Authorization'
               )
               
               # Create custom JWT authorizer for API-to-API communication
               custom_authorizer = self.apigateway.create_authorizer(
                   restApiId=api_id,
                   name='enterprise-jwt-authorizer',
                   type='TOKEN',
                   authorizerUri=f'arn:aws:apigateway:{boto3.Session().region_name}:lambda:path/2015-03-31/functions/arn:aws:lambda:{boto3.Session().region_name}:{boto3.STS().get_caller_identity()["Account"]}:function:jwt-authorizer/invocations',
                   identitySource='method.request.header.Authorization',
                   authorizerResultTtlInSeconds=300
               )
               
               return {
                   'cognito_authorizer_id': cognito_authorizer['id'],
                   'custom_authorizer_id': custom_authorizer['id']
               }
               
           except Exception as e:
               print(f"Authentication setup failed: {e}")
               raise
   
       def implement_comprehensive_monitoring(self, api_id, stage_name):
           """Implement comprehensive API monitoring and alerting"""
           try:
               # Create custom dashboard
               dashboard_body = {
                   "widgets": [
                       {
                           "type": "metric",
                           "properties": {
                               "metrics": [
                                   ["AWS/ApiGateway", "Count", "ApiName", f"{api_id}", "Stage", stage_name],
                                   [".", "Latency", ".", ".", ".", "."],
                                   [".", "4XXError", ".", ".", ".", "."],
                                   [".", "5XXError", ".", ".", ".", "."]
                               ],
                               "period": 300,
                               "stat": "Sum",
                               "region": boto3.Session().region_name,
                               "title": "API Gateway Performance Metrics"
                           }
                       }
                   ]
               }
               
               # Create performance alarms
               cloudwatch = boto3.client('cloudwatch')
               
               # High error rate alarm
               cloudwatch.put_metric_alarm(
                   AlarmName=f'{api_id}-high-error-rate',
                   ComparisonOperator='GreaterThanThreshold',
                   EvaluationPeriods=2,
                   MetricName='4XXError',
                   Namespace='AWS/ApiGateway',
                   Period=300,
                   Statistic='Sum',
                   Threshold=100,
                   ActionsEnabled=True,
                   AlarmActions=[
                       'arn:aws:sns:region:account:api-alerts'
                   ],
                   AlarmDescription='High error rate detected',
                   Dimensions=[
                       {'Name': 'ApiName', 'Value': api_id},
                       {'Name': 'Stage', 'Value': stage_name}
                   ],
                   Unit='Count'
               )
               
               # High latency alarm
               cloudwatch.put_metric_alarm(
                   AlarmName=f'{api_id}-high-latency',
                   ComparisonOperator='GreaterThanThreshold',
                   EvaluationPeriods=2,
                   MetricName='Latency',
                   Namespace='AWS/ApiGateway',
                   Period=300,
                   Statistic='Average',
                   Threshold=5000,  # 5 seconds
                   ActionsEnabled=True,
                   AlarmActions=[
                       'arn:aws:sns:region:account:api-alerts'
                   ],
                   AlarmDescription='High API latency detected',
                   Dimensions=[
                       {'Name': 'ApiName', 'Value': api_id},
                       {'Name': 'Stage', 'Value': stage_name}
                   ],
                   Unit='Milliseconds'
               )
               
               return {
                   'dashboard_created': True,
                   'alarms_configured': ['high-error-rate', 'high-latency']
               }
               
           except Exception as e:
               print(f"Monitoring implementation failed: {e}")
               raise
   
       def implement_advanced_caching_strategy(self, api_id, resource_id, method):
           """Implement intelligent caching with TTL optimization"""
           try:
               # Enable method-level caching
               self.apigateway.update_method(
                   restApiId=api_id,
                   resourceId=resource_id,
                   httpMethod=method,
                   patchOps=[
                       {
                           'op': 'replace',
                           'path': '/caching/enabled',
                           'value': 'true'
                       },
                       {
                           'op': 'replace',
                           'path': '/caching/ttlInSeconds',
                           'value': '300'  # 5 minutes
                       },
                       {
                           'op': 'replace',
                           'path': '/caching/cacheKeyParameters',
                           'value': ['method.request.querystring.userId', 'method.request.header.Accept']
                       }
                   ]
               )
               
               return {'caching_enabled': True, 'ttl_seconds': 300}
               
           except Exception as e:
               print(f"Caching implementation failed: {e}")
               raise
   ```

3. **Automated Deployment Pipeline Integration**
   ```yaml
   # CloudFormation template for API Gateway with CI/CD
   AWSTemplateFormatVersion: '2010-09-09'
   Description: 'Enterprise API Gateway with automated deployment pipeline'
   
   Parameters:
     EnvironmentName:
       Type: String
       Default: production
       AllowedValues: [development, staging, production]
     
     ApiName:
       Type: String
       Description: Name of the API Gateway
   
   Resources:
     EnterpriseAPIGateway:
       Type: AWS::ApiGateway::RestApi
       Properties:
         Name: !Sub '${ApiName}-${EnvironmentName}'
         Description: !Sub 'Enterprise API Gateway for ${EnvironmentName}'
         EndpointConfiguration:
           Types: [REGIONAL]
         Policy:
           Version: '2012-10-17'
           Statement:
             - Effect: Allow
               Principal: '*'
               Action: 'execute-api:Invoke'
               Resource: '*'
               Condition:
                 IpAddress:
                   aws:SourceIp: ['10.0.0.0/8', '172.16.0.0/12']
         Tags:
           - Key: Environment
             Value: !Ref EnvironmentName
           - Key: ManagedBy
             Value: CloudFormation
   
     APIGatewayDeployment:
       Type: AWS::ApiGateway::Deployment
       DependsOn: [APIGatewayMethod]
       Properties:
         RestApiId: !Ref EnterpriseAPIGateway
         StageName: !Ref EnvironmentName
         StageDescription:
           CachingEnabled: true
           CacheTtlInSeconds: 300
           LoggingLevel: INFO
           DataTraceEnabled: true
           MetricsEnabled: true
           ThrottlingRateLimit: 10000
           ThrottlingBurstLimit: 5000
   
   Outputs:
     APIGatewayURL:
       Description: API Gateway endpoint URL
       Value: !Sub 'https://${EnterpriseAPIGateway}.execute-api.${AWS::Region}.amazonaws.com/${EnvironmentName}'
       Export:
         Name: !Sub '${EnvironmentName}-api-gateway-url'
   ```

**Expected Outcome:** Production-ready API Gateway handling 1M+ requests/day, 99.9% uptime, sub-500ms average latency, comprehensive security and monitoring

### Example 2: Multi-Region API Gateway with Global Load Balancing

**Business Requirement:** Deploy globally distributed API infrastructure supporting international users with automatic failover, region-specific routing, and compliance with data sovereignty requirements.

**Step-by-Step Implementation:**
1. **Global API Architecture Setup**
   ```bash
   # Deploy API Gateway across multiple regions
   regions=("us-east-1" "eu-west-1" "ap-southeast-1")
   
   for region in "${regions[@]}"; do
     aws apigateway create-rest-api \
       --region $region \
       --name "global-enterprise-api-$region" \
       --description "Global API Gateway deployment for region $region" \
       --endpoint-configuration types=REGIONAL \
       --tags Environment=Production,Region=$region,GlobalDeployment=true
   done
   ```

**Expected Outcome:** Global API infrastructure with <100ms regional latency, 99.99% availability, automated failover, compliance-ready data handling

## Advanced Implementation Patterns

### Multi-Stage Deployment with Canary Releases
```bash
# Create canary deployment
aws apigateway create-deployment \
  --rest-api-id [api-id] \
  --stage-name production \
  --canary-settings '{
    "percentTraffic": 10,
    "deploymentId": "[new-deployment-id]",
    "stageVariableOverrides": {
      "version": "v2"
    }
  }'

# Monitor canary metrics and promote if successful
aws apigateway update-stage \
  --rest-api-id [api-id] \
  --stage-name production \
  --patch-ops '[
    {
      "op": "replace",
      "path": "/canarySettings/percentTraffic",
      "value": "100"
    }
  ]'
```

### Cost Optimization Strategies
- **HTTP APIs vs REST APIs:** 70% cost reduction for simple proxy use cases
- **Caching Implementation:** Reduced backend calls and improved response times
- **Request/Response Compression:** Bandwidth optimization for large payloads
- **Usage Plans:** Tiered pricing models with quota management

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