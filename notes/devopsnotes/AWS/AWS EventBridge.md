# AWS EventBridge: Enterprise Event-Driven Architecture Platform

## Overview
AWS EventBridge is a comprehensive serverless event bus service designed for building scalable, loosely coupled, event-driven applications. It enables real-time data routing between applications, microservices, and SaaS platforms with intelligent event pattern matching and enterprise-grade reliability.

## Event Bus Architecture & Types

### Default Event Bus
- **Purpose**: AWS service-generated events (EC2, S3, RDS, etc.)
- **Event Sources**: 90+ AWS services with automatic integration
- **Use Cases**: Infrastructure monitoring, automated remediation
- **Security**: IAM-based access control with resource policies

### Custom Event Buses
- **Purpose**: Application-specific and custom business events
- **Event Sources**: Custom applications, microservices, APIs
- **Use Cases**: Business process coordination, workflow orchestration
- **Features**: Multi-tenant isolation, custom naming conventions

### Partner Event Buses
- **Purpose**: Third-party SaaS integration and partner events
- **Event Sources**: 130+ SaaS providers (Zendesk, DataDog, Auth0)
- **Use Cases**: SaaS ecosystem integration, partner data synchronization
- **Benefits**: Pre-configured integrations, managed connectivity

## Core Features & Enterprise Capabilities

### Advanced Event Processing
- **Scheduled Events**: Cron-based and rate-based event triggers
- **Content-Based Routing**: Sophisticated event pattern matching
- **Event Transformation**: JSON path-based data manipulation
- **Event Filtering**: Complex rule-based event selection

### Schema Registry & Discovery
- **Event Schema Management**: Versioned schema definitions
- **Code Generation**: Auto-generated language bindings
- **Schema Evolution**: Backward/forward compatibility management
- **Event Discovery**: Schema-based event exploration

### Enterprise Reliability
- **Event Replay**: Point-in-time event reconstruction
- **Event Archive**: Long-term event storage and retrieval
- **Dead Letter Queues**: Failed event handling and analysis
- **Retry Policies**: Configurable exponential backoff strategies

### Global Event Distribution
- **Cross-Account Routing**: Secure multi-account event sharing
- **Cross-Region Replication**: Global event distribution patterns
- **Event Ordering**: FIFO event processing capabilities
- **Batch Processing**: High-throughput batch event handling

## Enterprise EventBridge Framework

### 1. Advanced Event-Driven Architecture Manager

```python
import boto3
import json
import logging
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import uuid
import asyncio
from concurrent.futures import ThreadPoolExecutor
import time
import hashlib

class EventBusType(Enum):
    DEFAULT = "default"
    CUSTOM = "custom"
    PARTNER = "partner"

class EventPriority(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

@dataclass
class EventPattern:
    source: List[str]
    detail_type: List[str]
    detail: Dict[str, Any] = field(default_factory=dict)
    account: List[str] = field(default_factory=list)
    region: List[str] = field(default_factory=list)
    time: List[str] = field(default_factory=list)
    resources: List[str] = field(default_factory=list)

@dataclass
class EventBridgeRule:
    name: str
    description: str
    event_pattern: EventPattern
    targets: List[Dict[str, Any]]
    schedule_expression: Optional[str] = None
    state: str = "ENABLED"
    priority: EventPriority = EventPriority.MEDIUM
    tags: Dict[str, str] = field(default_factory=dict)

@dataclass
class EventMetrics:
    event_count: int
    success_rate: float
    avg_processing_time: float
    error_count: int
    last_event_time: datetime
    throughput_per_minute: float

class EnterpriseEventBridgeManager:
    """
    Enterprise-grade AWS EventBridge manager with advanced event-driven
    architecture patterns, monitoring, and automation capabilities.
    """
    
    def __init__(self, region: str = 'us-east-1'):
        self.events = boto3.client('events', region_name=region)
        self.schemas = boto3.client('schemas', region_name=region)
        self.cloudwatch = boto3.client('cloudwatch', region_name=region)
        self.sns = boto3.client('sns', region_name=region)
        self.logger = self._setup_logging()
        self.region = region
        
        # Event tracking
        self.event_rules = {}
        self.event_buses = {}
        self.event_metrics = {}
        self.event_handlers = {}
        self.schema_registry = {}
        
    def _setup_logging(self) -> logging.Logger:
        """Configure structured logging for EventBridge operations"""
        logger = logging.getLogger('eventbridge_manager')
        logger.setLevel(logging.INFO)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - '
            '%(event_bus)s - %(rule_name)s - %(message)s'
        )
        
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    def create_event_bus(self, 
                        bus_name: str,
                        bus_type: EventBusType = EventBusType.CUSTOM,
                        description: str = "",
                        tags: Dict[str, str] = None) -> Dict[str, Any]:
        """Create enterprise event bus with monitoring and governance"""
        
        tags = tags or {}
        tags.update({
            'ManagedBy': 'EnterpriseEventBridge',
            'CreatedAt': datetime.utcnow().isoformat(),
            'Environment': tags.get('Environment', 'development')
        })
        
        try:
            if bus_type == EventBusType.CUSTOM:
                response = self.events.create_event_bus(
                    Name=bus_name,
                    Tags=[
                        {'Key': k, 'Value': v} for k, v in tags.items()
                    ]
                )
                
                bus_arn = response['EventBusArn']
                
            else:
                # Use default or partner event bus
                bus_arn = f"arn:aws:events:{self.region}:123456789012:event-bus/default"
            
            # Store event bus configuration
            self.event_buses[bus_name] = {
                'name': bus_name,
                'arn': bus_arn,
                'type': bus_type,
                'description': description,
                'tags': tags,
                'created_at': datetime.utcnow(),
                'rules': [],
                'metrics': EventMetrics(
                    event_count=0,
                    success_rate=100.0,
                    avg_processing_time=0.0,
                    error_count=0,
                    last_event_time=datetime.utcnow(),
                    throughput_per_minute=0.0
                )
            }
            
            # Set up monitoring
            self._setup_event_bus_monitoring(bus_name)
            
            self.logger.info(
                f"Event bus created: {bus_name}",
                extra={'event_bus': bus_name, 'rule_name': 'system'}
            )
            
            return {
                'bus_name': bus_name,
                'bus_arn': bus_arn,
                'status': 'created',
                'monitoring_enabled': True
            }
            
        except Exception as e:
            self.logger.error(
                f"Failed to create event bus: {e}",
                extra={'event_bus': bus_name, 'rule_name': 'system'}
            )
            raise
    
    def register_event_rule(self, 
                          event_bus_name: str,
                          rule_config: EventBridgeRule,
                          validation_rules: Optional[List[Callable]] = None) -> str:
        """Register sophisticated event processing rule with validation"""
        
        if event_bus_name not in self.event_buses:
            raise ValueError(f"Event bus '{event_bus_name}' not found")
        
        # Validate rule configuration
        self._validate_rule_config(rule_config, validation_rules or [])
        
        try:
            # Create event pattern
            event_pattern = self._build_event_pattern(rule_config.event_pattern)
            
            # Create EventBridge rule
            rule_kwargs = {
                'Name': rule_config.name,
                'Description': rule_config.description,
                'State': rule_config.state,
                'EventBusName': event_bus_name,
                'Tags': [
                    {'Key': k, 'Value': v} for k, v in rule_config.tags.items()
                ]
            }
            
            if rule_config.schedule_expression:
                rule_kwargs['ScheduleExpression'] = rule_config.schedule_expression
            else:
                rule_kwargs['EventPattern'] = json.dumps(event_pattern)
            
            response = self.events.put_rule(**rule_kwargs)
            rule_arn = response['RuleArn']
            
            # Add targets to rule
            if rule_config.targets:
                self.events.put_targets(
                    Rule=rule_config.name,
                    EventBusName=event_bus_name,
                    Targets=rule_config.targets
                )
            
            # Store rule configuration
            rule_id = f"{event_bus_name}:{rule_config.name}"
            self.event_rules[rule_id] = {
                'config': rule_config,
                'rule_arn': rule_arn,
                'event_bus_name': event_bus_name,
                'created_at': datetime.utcnow(),
                'event_count': 0,
                'last_triggered': None,
                'metrics': EventMetrics(
                    event_count=0,
                    success_rate=100.0,
                    avg_processing_time=0.0,
                    error_count=0,
                    last_event_time=datetime.utcnow(),
                    throughput_per_minute=0.0
                )
            }
            
            # Update event bus rules list
            self.event_buses[event_bus_name]['rules'].append(rule_id)
            
            self.logger.info(
                f"Event rule registered: {rule_config.name}",
                extra={'event_bus': event_bus_name, 'rule_name': rule_config.name}
            )
            
            return rule_arn
            
        except Exception as e:
            self.logger.error(
                f"Failed to register rule: {e}",
                extra={'event_bus': event_bus_name, 'rule_name': rule_config.name}
            )
            raise
    
    def _validate_rule_config(self, 
                            config: EventBridgeRule,
                            validation_rules: List[Callable]):
        """Validate event rule configuration"""
        
        # Basic validation
        if not config.name or not config.description:
            raise ValueError("Rule name and description are required")
        
        if not config.event_pattern.source and not config.schedule_expression:
            raise ValueError("Either event pattern or schedule expression required")
        
        if not config.targets:
            raise ValueError("At least one target is required")
        
        # Enterprise validation rules
        for rule in validation_rules:
            rule(config)
        
        # Security validation
        self._validate_rule_security(config)
    
    def _validate_rule_security(self, config: EventBridgeRule):
        """Validate rule security requirements"""
        
        # Check for sensitive data in event patterns
        pattern_str = json.dumps(config.event_pattern.__dict__)
        sensitive_keywords = ['password', 'secret', 'key', 'token', 'credential']
        
        for keyword in sensitive_keywords:
            if keyword.lower() in pattern_str.lower():
                self.logger.warning(
                    f"Potential sensitive data in event pattern: {keyword}"
                )
        
        # Validate target permissions
        for target in config.targets:
            if 'Arn' in target:
                # Simplified permission check
                if not target['Arn'].startswith('arn:aws:'):
                    raise ValueError(f"Invalid target ARN: {target['Arn']}")
    
    def _build_event_pattern(self, pattern: EventPattern) -> Dict[str, Any]:
        """Build EventBridge event pattern from configuration"""
        
        event_pattern = {}
        
        if pattern.source:
            event_pattern['source'] = pattern.source
        
        if pattern.detail_type:
            event_pattern['detail-type'] = pattern.detail_type
        
        if pattern.detail:
            event_pattern['detail'] = pattern.detail
        
        if pattern.account:
            event_pattern['account'] = pattern.account
        
        if pattern.region:
            event_pattern['region'] = pattern.region
        
        if pattern.time:
            event_pattern['time'] = pattern.time
        
        if pattern.resources:
            event_pattern['resources'] = pattern.resources
        
        return event_pattern
    
    async def publish_enterprise_event(self, 
                                     event_bus_name: str,
                                     source: str,
                                     detail_type: str,
                                     detail: Dict[str, Any],
                                     priority: EventPriority = EventPriority.MEDIUM,
                                     correlation_id: Optional[str] = None,
                                     business_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Publish enterprise event with correlation tracking and monitoring"""
        
        if event_bus_name not in self.event_buses:
            raise ValueError(f"Event bus '{event_bus_name}' not found")
        
        # Generate correlation ID if not provided
        correlation_id = correlation_id or str(uuid.uuid4())
        
        # Enrich event with enterprise metadata
        enriched_detail = {
            **detail,
            'correlation_id': correlation_id,
            'priority': priority.value,
            'timestamp': datetime.utcnow().isoformat(),
            'source_system': 'enterprise-eventbridge',
            'business_context': business_context or {}
        }
        
        # Add compliance and security metadata
        enriched_detail['compliance'] = {
            'data_classification': business_context.get('data_classification', 'internal') if business_context else 'internal',
            'retention_policy': '7_years',
            'gdpr_applicable': business_context.get('gdpr_applicable', True) if business_context else True
        }
        
        try:
            # Publish event
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.events.put_events(
                    Entries=[
                        {
                            'Source': source,
                            'DetailType': detail_type,
                            'Detail': json.dumps(enriched_detail),
                            'EventBusName': event_bus_name,
                            'Resources': [],
                            'Time': datetime.utcnow()
                        }
                    ]
                )
            )
            
            # Update metrics
            await self._update_event_metrics(event_bus_name, source, True)
            
            # Log event publication
            self.logger.info(
                f"Event published: {detail_type}",
                extra={
                    'event_bus': event_bus_name,
                    'rule_name': 'publisher',
                    'correlation_id': correlation_id,
                    'source': source
                }
            )
            
            return {
                'correlation_id': correlation_id,
                'event_id': response['Entries'][0].get('EventId'),
                'status': 'published',
                'failed_entry_count': response['FailedEntryCount'],
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            # Update error metrics
            await self._update_event_metrics(event_bus_name, source, False)
            
            self.logger.error(
                f"Failed to publish event: {e}",
                extra={
                    'event_bus': event_bus_name,
                    'rule_name': 'publisher',
                    'correlation_id': correlation_id,
                    'source': source
                }
            )
            raise
    
    async def _update_event_metrics(self, 
                                  event_bus_name: str,
                                  source: str,
                                  success: bool):
        """Update event metrics for monitoring and analytics"""
        
        if event_bus_name in self.event_buses:
            metrics = self.event_buses[event_bus_name]['metrics']
            metrics.event_count += 1
            metrics.last_event_time = datetime.utcnow()
            
            if not success:
                metrics.error_count += 1
            
            # Calculate success rate
            metrics.success_rate = (
                (metrics.event_count - metrics.error_count) / metrics.event_count * 100
            )
            
            # Send CloudWatch metrics
            await self._send_cloudwatch_metrics(event_bus_name, source, success)
    
    async def _send_cloudwatch_metrics(self, 
                                     event_bus_name: str,
                                     source: str,
                                     success: bool):
        """Send detailed metrics to CloudWatch"""
        
        try:
            metrics = [
                {
                    'MetricName': 'EventCount',
                    'Value': 1,
                    'Unit': 'Count',
                    'Dimensions': [
                        {'Name': 'EventBus', 'Value': event_bus_name},
                        {'Name': 'Source', 'Value': source}
                    ]
                }
            ]
            
            if success:
                metrics.append({
                    'MetricName': 'SuccessfulEvents',
                    'Value': 1,
                    'Unit': 'Count',
                    'Dimensions': [
                        {'Name': 'EventBus', 'Value': event_bus_name},
                        {'Name': 'Source', 'Value': source}
                    ]
                })
            else:
                metrics.append({
                    'MetricName': 'FailedEvents',
                    'Value': 1,
                    'Unit': 'Count',
                    'Dimensions': [
                        {'Name': 'EventBus', 'Value': event_bus_name},
                        {'Name': 'Source', 'Value': source}
                    ]
                })
            
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.cloudwatch.put_metric_data(
                    Namespace='AWS/EventBridge/Enterprise',
                    MetricData=metrics
                )
            )
            
        except Exception as e:
            self.logger.error(f"Failed to send CloudWatch metrics: {e}")
    
    def register_event_schema(self, 
                            registry_name: str,
                            schema_name: str,
                            schema_definition: Dict[str, Any],
                            schema_type: str = 'JSONSchemaDraft4') -> str:
        """Register event schema for discoverability and validation"""
        
        try:
            # Create schema registry if not exists
            try:
                self.schemas.create_registry(
                    RegistryName=registry_name,
                    Description=f"Enterprise event schemas for {registry_name}",
                    Tags={
                        'ManagedBy': 'EnterpriseEventBridge',
                        'CreatedAt': datetime.utcnow().isoformat()
                    }
                )
            except self.schemas.exceptions.ConflictException:
                pass  # Registry already exists
            
            # Create or update schema
            response = self.schemas.create_schema(
                RegistryName=registry_name,
                SchemaName=schema_name,
                Type=schema_type,
                Content=json.dumps(schema_definition),
                Description=f"Schema for {schema_name} events",
                Tags={
                    'SchemaType': schema_type,
                    'CreatedAt': datetime.utcnow().isoformat()
                }
            )
            
            schema_arn = response['SchemaArn']
            
            # Store schema locally
            self.schema_registry[f"{registry_name}:{schema_name}"] = {
                'registry_name': registry_name,
                'schema_name': schema_name,
                'schema_arn': schema_arn,
                'schema_definition': schema_definition,
                'schema_type': schema_type,
                'created_at': datetime.utcnow()
            }
            
            self.logger.info(
                f"Schema registered: {registry_name}:{schema_name}",
                extra={'event_bus': registry_name, 'rule_name': 'schema'}
            )
            
            return schema_arn
            
        except Exception as e:
            self.logger.error(
                f"Failed to register schema: {e}",
                extra={'event_bus': registry_name, 'rule_name': 'schema'}
            )
            raise
    
    def get_event_analytics(self, 
                          event_bus_name: str,
                          days: int = 7) -> Dict[str, Any]:
        """Get comprehensive event analytics and insights"""
        
        if event_bus_name not in self.event_buses:
            raise ValueError(f"Event bus '{event_bus_name}' not found")
        
        bus_config = self.event_buses[event_bus_name]
        
        try:
            # Get CloudWatch metrics
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=days)
            
            metrics_data = self._get_cloudwatch_metrics(
                event_bus_name,
                start_time,
                end_time
            )
            
            # Calculate analytics
            analytics = {
                'event_bus_name': event_bus_name,
                'analysis_period_days': days,
                'bus_info': {
                    'type': bus_config['type'].value,
                    'created_at': bus_config['created_at'].isoformat(),
                    'rule_count': len(bus_config['rules']),
                    'tags': bus_config['tags']
                },
                'event_metrics': {
                    'total_events': metrics_data.get('total_events', 0),
                    'successful_events': metrics_data.get('successful_events', 0),
                    'failed_events': metrics_data.get('failed_events', 0),
                    'success_rate_percent': self._calculate_success_rate(metrics_data),
                    'avg_events_per_hour': self._calculate_avg_events_per_hour(metrics_data, days),
                    'peak_events_per_hour': metrics_data.get('peak_events_per_hour', 0)
                },
                'rule_analytics': self._get_rule_analytics(bus_config['rules']),
                'performance_score': self._calculate_performance_score(metrics_data),
                'recommendations': self._generate_event_recommendations(metrics_data),
                'cost_analysis': self._calculate_cost_analysis(metrics_data)
            }
            
            return analytics
            
        except Exception as e:
            self.logger.error(f"Failed to get analytics: {e}")
            return {}
    
    def _setup_event_bus_monitoring(self, event_bus_name: str):
        """Set up CloudWatch monitoring for event bus"""
        
        try:
            # Create CloudWatch alarms for event bus
            alarm_configs = [
                {
                    'AlarmName': f'{event_bus_name}-HighErrorRate',
                    'MetricName': 'FailedEvents',
                    'Threshold': 10,
                    'ComparisonOperator': 'GreaterThanThreshold'
                },
                {
                    'AlarmName': f'{event_bus_name}-LowThroughput',
                    'MetricName': 'EventCount',
                    'Threshold': 1,
                    'ComparisonOperator': 'LessThanThreshold'
                }
            ]
            
            for alarm_config in alarm_configs:
                self.cloudwatch.put_metric_alarm(
                    AlarmName=alarm_config['AlarmName'],
                    MetricName=alarm_config['MetricName'],
                    Namespace='AWS/EventBridge/Enterprise',
                    Statistic='Sum',
                    Dimensions=[
                        {'Name': 'EventBus', 'Value': event_bus_name}
                    ],
                    Period=300,
                    EvaluationPeriods=2,
                    Threshold=alarm_config['Threshold'],
                    ComparisonOperator=alarm_config['ComparisonOperator'],
                    AlarmDescription=f'Monitor {alarm_config["MetricName"]} for {event_bus_name}',
                    Unit='Count'
                )
            
            self.logger.info(
                f"Monitoring setup completed for {event_bus_name}",
                extra={'event_bus': event_bus_name, 'rule_name': 'monitoring'}
            )
            
        except Exception as e:
            self.logger.error(
                f"Failed to setup monitoring: {e}",
                extra={'event_bus': event_bus_name, 'rule_name': 'monitoring'}
            )

# Usage Example
if __name__ == "__main__":
    # Initialize EventBridge manager
    eb_manager = EnterpriseEventBridgeManager()
    
    # Create enterprise event bus
    eb_manager.create_event_bus(
        "enterprise-orders",
        EventBusType.CUSTOM,
        "Enterprise order processing event bus",
        {
            'Environment': 'production',
            'Team': 'commerce',
            'Project': 'order-management'
        }
    )
    
    # Define complex event pattern
    order_pattern = EventPattern(
        source=["com.enterprise.orders"],
        detail_type=["Order Created", "Order Updated", "Order Cancelled"],
        detail={
            "status": ["pending", "confirmed", "cancelled"],
            "amount": [{"numeric": [">=", 100]}],
            "region": ["us-east-1", "us-west-2"]
        }
    )
    
    # Configure event rule with multiple targets
    order_rule = EventBridgeRule(
        name="enterprise-order-processing",
        description="Process high-value enterprise orders",
        event_pattern=order_pattern,
        targets=[
            {
                'Id': '1',
                'Arn': 'arn:aws:lambda:us-east-1:123456789012:function:ProcessOrder',
                'InputTransformer': {
                    'InputPathsMap': {
                        'orderId': '$.detail.orderId',
                        'amount': '$.detail.amount'
                    },
                    'InputTemplate': '{"orderId": "<orderId>", "amount": <amount>}'
                }
            },
            {
                'Id': '2',
                'Arn': 'arn:aws:sqs:us-east-1:123456789012:order-notifications',
                'SqsParameters': {
                    'MessageGroupId': 'order-processing'
                }
            }
        ],
        priority=EventPriority.HIGH,
        tags={
            'CriticalBusiness': 'true',
            'SLA': '15-minutes'
        }
    )
    
    # Register event rule
    rule_arn = eb_manager.register_event_rule(
        "enterprise-orders",
        order_rule
    )
    
    # Register event schema
    order_schema = {
        "type": "object",
        "properties": {
            "orderId": {"type": "string"},
            "customerId": {"type": "string"},
            "amount": {"type": "number"},
            "currency": {"type": "string"},
            "status": {"type": "string", "enum": ["pending", "confirmed", "cancelled"]},
            "items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "productId": {"type": "string"},
                        "quantity": {"type": "integer"},
                        "price": {"type": "number"}
                    }
                }
            }
        },
        "required": ["orderId", "customerId", "amount", "status"]
    }
    
    eb_manager.register_event_schema(
        "enterprise-commerce",
        "OrderEvent",
        order_schema
    )
    
    # Publish enterprise event
    async def publish_order_event():
        order_detail = {
            "orderId": "ORD-123456",
            "customerId": "CUST-789",
            "amount": 299.99,
            "currency": "USD",
            "status": "confirmed",
            "region": "us-east-1",
            "items": [
                {
                    "productId": "PROD-001",
                    "quantity": 2,
                    "price": 149.99
                }
            ]
        }
        
        business_context = {
            "data_classification": "confidential",
            "gdpr_applicable": True,
            "customer_segment": "enterprise",
            "revenue_impact": "high"
        }
        
        result = await eb_manager.publish_enterprise_event(
            "enterprise-orders",
            "com.enterprise.orders",
            "Order Created",
            order_detail,
            EventPriority.HIGH,
            business_context=business_context
        )
        
        print(f"Order event published: {result['correlation_id']}")
        
        # Get analytics
        analytics = eb_manager.get_event_analytics("enterprise-orders")
        print(f"Event analytics: {json.dumps(analytics, indent=2, default=str)}")
    
    # Run the example
    asyncio.run(publish_order_event())
```

### 2. Event-Driven DevOps Automation

```python
import boto3
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import asyncio
import time

@dataclass
class EventDrivenWorkflow:
    name: str
    trigger_pattern: Dict[str, Any]
    actions: List[Dict[str, Any]]
    conditions: Dict[str, Any]
    timeout_minutes: int = 30
    retry_attempts: int = 3

class EventDrivenDevOpsManager:
    """
    DevOps automation manager using EventBridge for event-driven
    infrastructure management and automated remediation.
    """
    
    def __init__(self):
        self.events = boto3.client('events')
        self.stepfunctions = boto3.client('stepfunctions')
        self.lambda_client = boto3.client('lambda')
        self.ec2 = boto3.client('ec2')
        self.rds = boto3.client('rds')
        self.ecs = boto3.client('ecs')
        
        self.workflows = {}
        self.automation_metrics = {
            'total_triggers': 0,
            'successful_automations': 0,
            'failed_automations': 0,
            'avg_resolution_time': 0
        }
    
    def setup_infrastructure_automation(self) -> Dict[str, Any]:
        """Set up comprehensive infrastructure automation workflows"""
        
        automation_workflows = [
            self._create_ec2_auto_recovery_workflow(),
            self._create_rds_performance_optimization_workflow(),
            self._create_ecs_auto_scaling_workflow(),
            self._create_security_incident_response_workflow(),
            self._create_cost_optimization_workflow()
        ]
        
        setup_results = []
        
        for workflow in automation_workflows:
            try:
                result = self._deploy_automation_workflow(workflow)
                setup_results.append(result)
                self.workflows[workflow.name] = workflow
                
            except Exception as e:
                setup_results.append({
                    'workflow_name': workflow.name,
                    'status': 'failed',
                    'error': str(e)
                })
        
        return {
            'total_workflows': len(automation_workflows),
            'successful_deployments': len([r for r in setup_results if r.get('status') == 'deployed']),
            'failed_deployments': len([r for r in setup_results if r.get('status') == 'failed']),
            'workflow_details': setup_results
        }
    
    def _create_ec2_auto_recovery_workflow(self) -> EventDrivenWorkflow:
        """Create EC2 instance auto-recovery workflow"""
        
        return EventDrivenWorkflow(
            name="ec2-auto-recovery",
            trigger_pattern={
                "source": ["aws.ec2"],
                "detail-type": ["EC2 Instance State-change Notification"],
                "detail": {
                    "state": ["stopped", "stopping", "terminated"]
                }
            },
            actions=[
                {
                    "type": "lambda",
                    "function": "ec2-health-check",
                    "parameters": {
                        "instance_id": "$.detail.instance-id",
                        "state": "$.detail.state"
                    }
                },
                {
                    "type": "conditional",
                    "condition": "health_check_failed",
                    "true_action": {
                        "type": "ec2",
                        "action": "start_instance",
                        "parameters": {
                            "instance_id": "$.detail.instance-id"
                        }
                    },
                    "false_action": {
                        "type": "notification",
                        "message": "Instance stopped intentionally"
                    }
                },
                {
                    "type": "monitoring",
                    "action": "create_alarm",
                    "parameters": {
                        "instance_id": "$.detail.instance-id",
                        "metric": "StatusCheckFailed_System"
                    }
                }
            ],
            conditions={
                "health_check_failed": "lambda_result.status == 'unhealthy'",
                "critical_instance": "instance_tags.Environment == 'production'"
            },
            timeout_minutes=15,
            retry_attempts=3
        )
    
    def _create_rds_performance_optimization_workflow(self) -> EventDrivenWorkflow:
        """Create RDS performance optimization workflow"""
        
        return EventDrivenWorkflow(
            name="rds-performance-optimization",
            trigger_pattern={
                "source": ["aws.rds"],
                "detail-type": ["RDS DB Instance Event"],
                "detail": {
                    "EventCategories": ["performance", "availability"]
                }
            },
            actions=[
                {
                    "type": "lambda",
                    "function": "rds-performance-analyzer",
                    "parameters": {
                        "db_instance_id": "$.detail.SourceId",
                        "event_message": "$.detail.Message"
                    }
                },
                {
                    "type": "conditional",
                    "condition": "high_cpu_utilization",
                    "true_action": {
                        "type": "rds",
                        "action": "modify_instance_class",
                        "parameters": {
                            "db_instance_id": "$.detail.SourceId",
                            "new_instance_class": "calculated_optimal_class"
                        }
                    }
                },
                {
                    "type": "conditional",
                    "condition": "storage_full",
                    "true_action": {
                        "type": "rds",
                        "action": "modify_storage",
                        "parameters": {
                            "db_instance_id": "$.detail.SourceId",
                            "storage_increase_percent": 20
                        }
                    }
                }
            ],
            conditions={
                "high_cpu_utilization": "performance_metrics.cpu_percent > 80",
                "storage_full": "performance_metrics.storage_percent > 90",
                "connection_limit_reached": "performance_metrics.connections_percent > 95"
            },
            timeout_minutes=30,
            retry_attempts=2
        )
    
    def _create_ecs_auto_scaling_workflow(self) -> EventDrivenWorkflow:
        """Create ECS auto-scaling workflow"""
        
        return EventDrivenWorkflow(
            name="ecs-auto-scaling",
            trigger_pattern={
                "source": ["aws.ecs"],
                "detail-type": ["ECS Task State Change"],
                "detail": {
                    "lastStatus": ["STOPPED"],
                    "stopCode": ["TaskFailedToStart", "EssentialContainerExited"]
                }
            },
            actions=[
                {
                    "type": "lambda",
                    "function": "ecs-health-analyzer",
                    "parameters": {
                        "cluster_arn": "$.detail.clusterArn",
                        "task_arn": "$.detail.taskArn",
                        "stop_reason": "$.detail.stoppedReason"
                    }
                },
                {
                    "type": "conditional",
                    "condition": "resource_shortage",
                    "true_action": {
                        "type": "ecs",
                        "action": "update_service",
                        "parameters": {
                            "cluster": "$.detail.clusterArn",
                            "service": "derived_service_name",
                            "desired_count": "current_count + 1"
                        }
                    }
                },
                {
                    "type": "conditional",
                    "condition": "repeated_failures",
                    "true_action": {
                        "type": "notification",
                        "severity": "critical",
                        "message": "ECS service experiencing repeated failures"
                    }
                }
            ],
            conditions={
                "resource_shortage": "analysis_result.cause == 'insufficient_memory'",
                "repeated_failures": "failure_count_last_hour > 5",
                "critical_service": "service_tags.Environment == 'production'"
            },
            timeout_minutes=20,
            retry_attempts=3
        )
    
    def _create_security_incident_response_workflow(self) -> EventDrivenWorkflow:
        """Create security incident response workflow"""
        
        return EventDrivenWorkflow(
            name="security-incident-response",
            trigger_pattern={
                "source": ["aws.guardduty", "aws.security-hub", "aws.inspector"],
                "detail-type": [
                    "GuardDuty Finding",
                    "Security Hub Findings - Imported",
                    "Inspector Assessment Run State Change"
                ],
                "detail": {
                    "severity": ["HIGH", "CRITICAL"],
                    "type": [
                        "UnauthorizedAPICall",
                        "Malware",
                        "Backdoor",
                        "Trojan"
                    ]
                }
            },
            actions=[
                {
                    "type": "lambda",
                    "function": "security-incident-analyzer",
                    "parameters": {
                        "finding_id": "$.detail.id",
                        "finding_type": "$.detail.type",
                        "severity": "$.detail.severity",
                        "resource_arn": "$.detail.resource.arn"
                    }
                },
                {
                    "type": "conditional",
                    "condition": "compromised_instance",
                    "true_action": {
                        "type": "ec2",
                        "action": "isolate_instance",
                        "parameters": {
                            "instance_id": "extracted_instance_id",
                            "isolation_sg": "sg-isolation-123456"
                        }
                    }
                },
                {
                    "type": "notification",
                    "channel": "security-team",
                    "severity": "immediate",
                    "parameters": {
                        "incident_id": "generated_incident_id",
                        "finding_details": "$.detail",
                        "automated_actions": "list_of_actions_taken"
                    }
                },
                {
                    "type": "stepfunctions",
                    "workflow": "forensic-data-collection",
                    "parameters": {
                        "resource_arn": "$.detail.resource.arn",
                        "incident_id": "generated_incident_id"
                    }
                }
            ],
            conditions={
                "compromised_instance": "analysis_result.resource_type == 'ec2' and analysis_result.risk == 'high'",
                "data_exfiltration": "finding_type.contains('UnauthorizedAPICall') and analysis_result.data_access == true",
                "critical_environment": "resource_tags.Environment == 'production'"
            },
            timeout_minutes=10,
            retry_attempts=1
        )
    
    def _create_cost_optimization_workflow(self) -> EventDrivenWorkflow:
        """Create cost optimization workflow"""
        
        return EventDrivenWorkflow(
            name="cost-optimization",
            trigger_pattern={
                "source": ["aws.budgets", "aws.cost-explorer"],
                "detail-type": [
                    "Budget Threshold Exceeded",
                    "Cost Anomaly Detection"
                ],
                "detail": {
                    "threshold-type": ["PERCENTAGE", "ABSOLUTE_VALUE"],
                    "comparison-operator": ["GREATER_THAN"]
                }
            },
            actions=[
                {
                    "type": "lambda",
                    "function": "cost-analyzer",
                    "parameters": {
                        "budget_name": "$.detail.budget-name",
                        "actual_amount": "$.detail.actual-amount",
                        "forecasted_amount": "$.detail.forecasted-amount"
                    }
                },
                {
                    "type": "conditional",
                    "condition": "unused_resources_detected",
                    "true_action": {
                        "type": "lambda",
                        "function": "resource-optimizer",
                        "parameters": {
                            "optimization_type": "rightsizing",
                            "resources": "identified_unused_resources"
                        }
                    }
                },
                {
                    "type": "notification",
                    "channel": "finops-team",
                    "parameters": {
                        "budget_status": "$.detail",
                        "optimization_recommendations": "generated_recommendations",
                        "potential_savings": "calculated_savings"
                    }
                }
            ],
            conditions={
                "unused_resources_detected": "analysis_result.unused_resources.count > 0",
                "overprovisioned_detected": "analysis_result.overprovisioned_resources.count > 0",
                "immediate_action_required": "budget_variance_percent > 20"
            },
            timeout_minutes=45,
            retry_attempts=2
        )
    
    def _deploy_automation_workflow(self, workflow: EventDrivenWorkflow) -> Dict[str, Any]:
        """Deploy event-driven automation workflow"""
        
        try:
            # Create EventBridge rule
            rule_response = self.events.put_rule(
                Name=f"automation-{workflow.name}",
                Description=f"Automation workflow: {workflow.name}",
                EventPattern=json.dumps(workflow.trigger_pattern),
                State='ENABLED',
                Tags=[
                    {'Key': 'WorkflowType', 'Value': 'DevOpsAutomation'},
                    {'Key': 'ManagedBy', 'Value': 'EventDrivenDevOps'}
                ]
            )
            
            # Create Step Functions state machine for workflow execution
            state_machine_definition = self._create_state_machine_definition(workflow)
            
            sf_response = self.stepfunctions.create_state_machine(
                name=f"automation-{workflow.name}",
                definition=json.dumps(state_machine_definition),
                roleArn="arn:aws:iam::123456789012:role/AutomationWorkflowRole",
                type="EXPRESS",
                loggingConfiguration={
                    'level': 'ALL',
                    'includeExecutionData': True
                },
                tracingConfiguration={
                    'enabled': True
                }
            )
            
            # Add Step Functions as target
            self.events.put_targets(
                Rule=f"automation-{workflow.name}",
                Targets=[
                    {
                        'Id': '1',
                        'Arn': sf_response['stateMachineArn'],
                        'RoleArn': 'arn:aws:iam::123456789012:role/EventBridgeExecutionRole',
                        'InputTransformer': {
                            'InputPathsMap': {
                                'detail': '$.detail',
                                'source': '$.source',
                                'account': '$.account',
                                'region': '$.region',
                                'time': '$.time'
                            },
                            'InputTemplate': json.dumps({
                                'workflowName': workflow.name,
                                'triggerEvent': {
                                    'detail': '<detail>',
                                    'source': '<source>',
                                    'account': '<account>',
                                    'region': '<region>',
                                    'time': '<time>'
                                },
                                'workflowConfig': {
                                    'timeoutMinutes': workflow.timeout_minutes,
                                    'retryAttempts': workflow.retry_attempts
                                }
                            })
                        }
                    }
                ]
            )
            
            return {
                'workflow_name': workflow.name,
                'status': 'deployed',
                'rule_arn': rule_response['RuleArn'],
                'state_machine_arn': sf_response['stateMachineArn'],
                'deployment_time': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                'workflow_name': workflow.name,
                'status': 'failed',
                'error': str(e)
            }
    
    def _create_state_machine_definition(self, workflow: EventDrivenWorkflow) -> Dict[str, Any]:
        """Create Step Functions state machine definition for workflow"""
        
        states = {}
        
        # Start with initialization
        states["Initialize"] = {
            "Type": "Pass",
            "Parameters": {
                "workflowName.$": "$.workflowName",
                "startTime.$": "$$.State.EnteredTime",
                "executionId.$": "$$.Execution.Name",
                "triggerEvent.$": "$.triggerEvent"
            },
            "Next": "ExecuteActions"
        }
        
        # Execute actions sequentially
        states["ExecuteActions"] = {
            "Type": "Parallel",
            "Branches": [],
            "Next": "RecordMetrics",
            "Catch": [
                {
                    "ErrorEquals": ["States.ALL"],
                    "Next": "HandleFailure",
                    "ResultPath": "$.error"
                }
            ]
        }
        
        # Create branches for each action
        for i, action in enumerate(workflow.actions):
            branch = {
                "StartAt": f"Action{i}",
                "States": {
                    f"Action{i}": self._create_action_state(action)
                }
            }
            states["ExecuteActions"]["Branches"].append(branch)
        
        # Record metrics
        states["RecordMetrics"] = {
            "Type": "Task",
            "Resource": "arn:aws:lambda:us-east-1:123456789012:function:RecordAutomationMetrics",
            "Parameters": {
                "workflowName.$": "$.workflowName",
                "executionTime.$": "$$.State.EnteredTime",
                "status": "success",
                "actionResults.$": "$"
            },
            "End": True
        }
        
        # Handle failures
        states["HandleFailure"] = {
            "Type": "Task",
            "Resource": "arn:aws:lambda:us-east-1:123456789012:function:HandleAutomationFailure",
            "Parameters": {
                "workflowName.$": "$.workflowName",
                "error.$": "$.error",
                "triggerEvent.$": "$.triggerEvent"
            },
            "End": True
        }
        
        return {
            "Comment": f"Event-driven automation workflow: {workflow.name}",
            "StartAt": "Initialize",
            "States": states,
            "TimeoutSeconds": workflow.timeout_minutes * 60
        }
    
    def _create_action_state(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Create state machine state for an action"""
        
        if action["type"] == "lambda":
            return {
                "Type": "Task",
                "Resource": f"arn:aws:lambda:us-east-1:123456789012:function:{action['function']}",
                "Parameters": action.get("parameters", {}),
                "End": True
            }
        elif action["type"] == "conditional":
            return {
                "Type": "Choice",
                "Choices": [
                    {
                        "Variable": "$.condition_result",
                        "BooleanEquals": True,
                        "Next": "TrueAction"
                    }
                ],
                "Default": "FalseAction"
            }
        else:
            # Generic task state
            return {
                "Type": "Task",
                "Resource": "arn:aws:states:::lambda:invoke",
                "Parameters": {
                    "FunctionName": "generic-action-executor",
                    "Payload": action
                },
                "End": True
            }

# Usage Example
if __name__ == "__main__":
    # Initialize DevOps automation manager
    devops_manager = EventDrivenDevOpsManager()
    
    # Set up comprehensive infrastructure automation
    setup_results = devops_manager.setup_infrastructure_automation()
    
    print(f"Infrastructure Automation Setup Results:")
    print(f"Total Workflows: {setup_results['total_workflows']}")
    print(f"Successful Deployments: {setup_results['successful_deployments']}")
    print(f"Failed Deployments: {setup_results['failed_deployments']}")
    
    for workflow_result in setup_results['workflow_details']:
        print(f"\nWorkflow: {workflow_result['workflow_name']}")
        print(f"Status: {workflow_result['status']}")
        if workflow_result.get('rule_arn'):
            print(f"Rule ARN: {workflow_result['rule_arn']}")
        if workflow_result.get('error'):
            print(f"Error: {workflow_result['error']}")
```

## Advanced Enterprise Use Cases

### Multi-Cloud Event Integration
- **Hybrid Cloud Orchestration**: Events across AWS, Azure, GCP
- **Cross-Cloud Data Synchronization**: Real-time data replication
- **Multi-Cloud Disaster Recovery**: Automated failover patterns
- **Unified Event Monitoring**: Centralized multi-cloud observability

### Microservices Choreography
- **Service Mesh Integration**: Istio/Envoy event propagation
- **Saga Pattern Implementation**: Distributed transaction coordination
- **Event Sourcing**: Complete audit trail with event replay
- **CQRS Integration**: Command-Query responsibility separation

### Real-Time Analytics & ML
- **Stream Processing**: Kinesis/Kafka integration patterns
- **ML Pipeline Orchestration**: Model training trigger events
- **Real-Time Personalization**: User behavior event processing
- **Fraud Detection**: Real-time anomaly detection workflows

### Compliance & Governance
- **Regulatory Event Tracking**: SOX, GDPR, HIPAA compliance
- **Audit Trail Generation**: Immutable event logging
- **Data Lineage Tracking**: End-to-end data flow monitoring
- **Change Management**: Infrastructure change event validation

This enterprise EventBridge implementation provides comprehensive event-driven architecture capabilities with advanced DevOps automation, security monitoring, and production-ready patterns for scalable, loosely coupled systems.