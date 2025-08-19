# AWS X-Ray: Enterprise Distributed Tracing & Observability Platform

## Overview
AWS X-Ray is a comprehensive distributed tracing service designed for analyzing, debugging, and optimizing production applications across complex microservices architectures. It provides real-time visibility into application performance, service dependencies, and request flows.

## Core Architecture Components

### Service Types & Capabilities
- **Service Map:** Interactive visual topology with dependency analysis
- **Traces:** Complete end-to-end request journey tracking
- **Analytics:** Performance insights, trends, and anomaly detection
- **Segments:** Individual service execution units
- **Subsegments:** Granular operation tracking within services
- **Annotations:** Searchable key-value metadata
- **Metadata:** Detailed contextual information

### Enterprise Features
- Distributed tracing across multi-cloud and hybrid environments
- Real-time performance bottleneck identification
- Advanced error analysis with root cause investigation
- Native integration with Lambda, ECS, API Gateway, ALB
- Intelligent sampling rules for cost optimization
- Service insights with ML-powered anomaly detection
- Cross-region trace aggregation
- Compliance and security monitoring

## Enterprise X-Ray Framework Implementation

### 1. Advanced Distributed Tracing Manager

```python
import boto3
import json
import logging
from typing import Dict, List, Optional, Any
from aws_xray_sdk.core import xray_recorder, patch_all
from aws_xray_sdk.core.context import Context
from aws_xray_sdk.core.models import subsegment
from dataclasses import dataclass
from datetime import datetime, timedelta
import asyncio
import time
import uuid

@dataclass
class TraceConfiguration:
    sampling_rate: float
    service_name: str
    environment: str
    annotations: Dict[str, str]
    metadata: Dict[str, Any]
    plugins: List[str]

class EnterpriseXRayManager:
    """
    Enterprise-grade AWS X-Ray distributed tracing manager with advanced
    monitoring, sampling, and performance optimization capabilities.
    """
    
    def __init__(self, config: TraceConfiguration):
        self.config = config
        self.xray_client = boto3.client('xray')
        self.logger = self._setup_logging()
        self._configure_xray()
        
    def _setup_logging(self) -> logging.Logger:
        """Configure structured logging for X-Ray operations"""
        logger = logging.getLogger('xray_manager')
        logger.setLevel(logging.INFO)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - '
            '%(trace_id)s - %(message)s'
        )
        
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    def _configure_xray(self):
        """Configure X-Ray SDK with enterprise settings"""
        # Patch AWS services for automatic tracing
        patch_all()
        
        # Configure service name and plugins
        xray_recorder.configure(
            service=self.config.service_name,
            plugins=self.config.plugins,
            daemon_address='127.0.0.1:2000',
            use_ssl=True
        )
        
        # Set sampling rules
        self._configure_sampling_rules()
    
    def _configure_sampling_rules(self):
        """Configure intelligent sampling rules for cost optimization"""
        sampling_rules = {
            "version": 2,
            "default": {
                "fixed_target": 1,
                "rate": self.config.sampling_rate
            },
            "rules": [
                {
                    "description": "Critical endpoints",
                    "service_name": "*",
                    "http_method": "*",
                    "url_path": "/api/critical/*",
                    "fixed_target": 2,
                    "rate": 1.0
                },
                {
                    "description": "Health checks",
                    "service_name": "*",
                    "http_method": "GET",
                    "url_path": "/health",
                    "fixed_target": 0,
                    "rate": 0.1
                },
                {
                    "description": "Error traces",
                    "service_name": "*",
                    "http_method": "*",
                    "url_path": "*",
                    "fixed_target": 1,
                    "rate": 1.0,
                    "attributes": {
                        "error": "true"
                    }
                }
            ]
        }
        
        try:
            self.xray_client.put_sampling_rule(
                SamplingRule=sampling_rules
            )
            self.logger.info("Sampling rules configured successfully")
        except Exception as e:
            self.logger.error(f"Failed to configure sampling rules: {e}")
    
    @xray_recorder.capture('enterprise_operation')
    def trace_enterprise_operation(self, 
                                 operation_name: str,
                                 business_context: Dict[str, Any],
                                 performance_sla: float = 1.0):
        """Trace enterprise operation with business context and SLA monitoring"""
        
        start_time = time.time()
        operation_id = str(uuid.uuid4())
        
        # Add annotations for searchability
        xray_recorder.put_annotation('operation_name', operation_name)
        xray_recorder.put_annotation('operation_id', operation_id)
        xray_recorder.put_annotation('environment', self.config.environment)
        xray_recorder.put_annotation('sla_threshold', performance_sla)
        
        # Add business context metadata
        xray_recorder.put_metadata('business_context', business_context)
        xray_recorder.put_metadata('compliance', {
            'data_classification': business_context.get('data_classification', 'internal'),
            'retention_policy': '7_years',
            'gdpr_applicable': business_context.get('gdpr_applicable', True)
        })
        
        try:
            # Create subsegment for detailed tracking
            with xray_recorder.in_subsegment(f'{operation_name}_execution') as subseg:
                subseg.put_annotation('execution_start', datetime.utcnow().isoformat())
                
                # Simulate operation execution
                result = self._execute_operation(operation_name, business_context)
                
                execution_time = time.time() - start_time
                subseg.put_annotation('execution_time', execution_time)
                
                # SLA compliance check
                if execution_time > performance_sla:
                    subseg.put_annotation('sla_violation', True)
                    self.logger.warning(
                        f"SLA violation: {operation_name} took {execution_time:.2f}s "
                        f"(threshold: {performance_sla}s)",
                        extra={'trace_id': operation_id}
                    )
                    self._trigger_sla_alert(operation_name, execution_time, performance_sla)
                
                return result
                
        except Exception as e:
            xray_recorder.put_annotation('error', True)
            xray_recorder.put_annotation('error_type', type(e).__name__)
            xray_recorder.put_metadata('error_details', {
                'message': str(e),
                'operation_id': operation_id,
                'timestamp': datetime.utcnow().isoformat()
            })
            
            self.logger.error(
                f"Operation failed: {operation_name}",
                exc_info=True,
                extra={'trace_id': operation_id}
            )
            
            self._trigger_error_alert(operation_name, str(e), operation_id)
            raise
    
    def _execute_operation(self, operation_name: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the actual business operation"""
        # Simulate various operation types
        if 'database' in operation_name.lower():
            return self._trace_database_operation(context)
        elif 'api' in operation_name.lower():
            return self._trace_api_operation(context)
        elif 'queue' in operation_name.lower():
            return self._trace_queue_operation(context)
        else:
            return self._trace_generic_operation(context)
    
    @xray_recorder.capture('database_operation')
    def _trace_database_operation(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Trace database operations with detailed performance metrics"""
        
        with xray_recorder.in_subsegment('database_connection') as subseg:
            subseg.put_annotation('database_type', context.get('db_type', 'postgresql'))
            subseg.put_annotation('query_type', context.get('query_type', 'SELECT'))
            subseg.put_metadata('connection_pool', {
                'pool_size': context.get('pool_size', 10),
                'active_connections': context.get('active_connections', 3)
            })
            
            # Simulate database query
            time.sleep(0.1)  # Simulate DB latency
            
            return {
                'rows_affected': context.get('expected_rows', 100),
                'execution_plan': 'index_scan',
                'cache_hit': True
            }
    
    @xray_recorder.capture('api_operation')
    def _trace_api_operation(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Trace external API calls with retry and circuit breaker patterns"""
        
        with xray_recorder.in_subsegment('external_api_call') as subseg:
            subseg.put_annotation('api_endpoint', context.get('endpoint', '/api/v1/resource'))
            subseg.put_annotation('http_method', context.get('method', 'GET'))
            subseg.put_metadata('request_headers', {
                'authorization': '[REDACTED]',
                'content_type': 'application/json',
                'user_agent': 'enterprise-service/1.0'
            })
            
            # Simulate API call with potential retry
            for attempt in range(context.get('max_retries', 3)):
                try:
                    subseg.put_annotation(f'attempt_{attempt + 1}', True)
                    time.sleep(0.05)  # Simulate API latency
                    
                    if attempt < 2 and context.get('simulate_failure', False):
                        raise Exception("Simulated API failure")
                    
                    return {
                        'status_code': 200,
                        'response_time': 50,
                        'attempts': attempt + 1
                    }
                    
                except Exception as e:
                    subseg.put_annotation(f'attempt_{attempt + 1}_failed', True)
                    if attempt == context.get('max_retries', 3) - 1:
                        raise
                    time.sleep(2 ** attempt)  # Exponential backoff
    
    def get_service_analytics(self, 
                            service_name: str,
                            start_time: datetime,
                            end_time: datetime) -> Dict[str, Any]:
        """Get comprehensive service analytics and insights"""
        
        try:
            # Get service statistics
            response = self.xray_client.get_service_statistics(
                StartTime=start_time,
                EndTime=end_time,
                GroupName=service_name
            )
            
            # Get trace summaries
            trace_summaries = self.xray_client.get_trace_summaries(
                TimeRangeType='TimeRange',
                StartTime=start_time,
                EndTime=end_time,
                FilterExpression=f'service("{service_name}")',
                SamplingStrategy={
                    'Name': 'PartialScan',
                    'Value': 0.1
                }
            )
            
            # Calculate insights
            analytics = self._calculate_service_insights(
                response.get('ServiceStatistics', []),
                trace_summaries.get('TraceSummaries', [])
            )
            
            return analytics
            
        except Exception as e:
            self.logger.error(f"Failed to get service analytics: {e}")
            return {}
    
    def _calculate_service_insights(self, 
                                  service_stats: List[Dict],
                                  trace_summaries: List[Dict]) -> Dict[str, Any]:
        """Calculate detailed service insights from X-Ray data"""
        
        total_requests = sum(stat.get('RequestCount', 0) for stat in service_stats)
        total_errors = sum(stat.get('ErrorStatistics', {}).get('TotalCount', 0) 
                          for stat in service_stats)
        
        response_times = []
        for summary in trace_summaries:
            if 'Duration' in summary:
                response_times.append(summary['Duration'])
        
        if response_times:
            avg_response_time = sum(response_times) / len(response_times)
            p95_response_time = sorted(response_times)[int(len(response_times) * 0.95)]
            p99_response_time = sorted(response_times)[int(len(response_times) * 0.99)]
        else:
            avg_response_time = p95_response_time = p99_response_time = 0
        
        error_rate = (total_errors / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'performance_metrics': {
                'total_requests': total_requests,
                'error_rate_percent': round(error_rate, 2),
                'avg_response_time_ms': round(avg_response_time * 1000, 2),
                'p95_response_time_ms': round(p95_response_time * 1000, 2),
                'p99_response_time_ms': round(p99_response_time * 1000, 2)
            },
            'health_score': self._calculate_health_score(error_rate, avg_response_time),
            'recommendations': self._generate_recommendations(error_rate, avg_response_time),
            'anomalies': self._detect_anomalies(trace_summaries)
        }
    
    def _calculate_health_score(self, error_rate: float, avg_response_time: float) -> int:
        """Calculate service health score (0-100)"""
        
        error_score = max(0, 100 - (error_rate * 10))
        performance_score = max(0, 100 - (avg_response_time * 100))
        
        return int((error_score + performance_score) / 2)
    
    def _generate_recommendations(self, 
                               error_rate: float, 
                               avg_response_time: float) -> List[str]:
        """Generate performance improvement recommendations"""
        
        recommendations = []
        
        if error_rate > 5:
            recommendations.append(
                "High error rate detected. Implement circuit breaker pattern "
                "and improve error handling."
            )
        
        if avg_response_time > 1.0:
            recommendations.append(
                "High response time detected. Consider caching, database "
                "optimization, or horizontal scaling."
            )
        
        if error_rate < 1 and avg_response_time < 0.5:
            recommendations.append(
                "Excellent performance! Consider reducing sampling rate "
                "to optimize costs."
            )
        
        return recommendations
    
    def _detect_anomalies(self, trace_summaries: List[Dict]) -> List[Dict[str, Any]]:
        """Detect performance anomalies in trace data"""
        
        anomalies = []
        
        if not trace_summaries:
            return anomalies
        
        # Calculate response time threshold (mean + 2 * std dev)
        response_times = [s.get('Duration', 0) for s in trace_summaries]
        mean_time = sum(response_times) / len(response_times)
        
        variance = sum((x - mean_time) ** 2 for x in response_times) / len(response_times)
        std_dev = variance ** 0.5
        threshold = mean_time + (2 * std_dev)
        
        for summary in trace_summaries:
            duration = summary.get('Duration', 0)
            if duration > threshold:
                anomalies.append({
                    'trace_id': summary.get('Id'),
                    'anomaly_type': 'high_latency',
                    'duration': duration,
                    'threshold': threshold,
                    'severity': 'high' if duration > threshold * 1.5 else 'medium'
                })
        
        return anomalies
    
    def _trigger_sla_alert(self, operation: str, actual_time: float, sla_time: float):
        """Trigger SLA violation alert"""
        
        alert_data = {
            'alert_type': 'sla_violation',
            'operation': operation,
            'actual_time': actual_time,
            'sla_time': sla_time,
            'violation_percentage': ((actual_time - sla_time) / sla_time) * 100,
            'timestamp': datetime.utcnow().isoformat(),
            'environment': self.config.environment
        }
        
        # Send to monitoring system (CloudWatch, SNS, etc.)
        self.logger.warning(f"SLA Alert: {json.dumps(alert_data)}")
    
    def _trigger_error_alert(self, operation: str, error_message: str, operation_id: str):
        """Trigger error alert for immediate attention"""
        
        alert_data = {
            'alert_type': 'operation_error',
            'operation': operation,
            'error_message': error_message,
            'operation_id': operation_id,
            'timestamp': datetime.utcnow().isoformat(),
            'environment': self.config.environment,
            'severity': 'high'
        }
        
        # Send to alerting system
        self.logger.error(f"Error Alert: {json.dumps(alert_data)}")

# Usage Example
if __name__ == "__main__":
    # Configure enterprise tracing
    config = TraceConfiguration(
        sampling_rate=0.1,
        service_name="enterprise-api",
        environment="production",
        annotations={
            "version": "1.2.3",
            "region": "us-east-1",
            "team": "platform"
        },
        metadata={
            "deployment_date": "2024-01-15",
            "build_number": "456"
        },
        plugins=["ECSPlugin", "EC2Plugin"]
    )
    
    # Initialize X-Ray manager
    xray_manager = EnterpriseXRayManager(config)
    
    # Trace enterprise operations
    business_context = {
        "user_id": "user123",
        "transaction_type": "payment",
        "amount": 299.99,
        "currency": "USD",
        "data_classification": "confidential",
        "gdpr_applicable": True
    }
    
    try:
        result = xray_manager.trace_enterprise_operation(
            "process_payment",
            business_context,
            performance_sla=0.8
        )
        print(f"Operation completed: {result}")
        
        # Get analytics
        analytics = xray_manager.get_service_analytics(
            "enterprise-api",
            datetime.utcnow() - timedelta(hours=1),
            datetime.utcnow()
        )
        print(f"Service analytics: {json.dumps(analytics, indent=2)}")
        
    except Exception as e:
        print(f"Operation failed: {e}")
```

### 2. X-Ray DevOps Automation & Monitoring

```python
import boto3
import json
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import asyncio
import threading
import time

@dataclass
class XRayMonitoringConfig:
    alert_thresholds: Dict[str, float]
    dashboard_metrics: List[str]
    automated_responses: Dict[str, str]
    notification_channels: List[str]

class XRayDevOpsAutomation:
    """
    Enterprise DevOps automation for X-Ray monitoring, alerting,
    and automated remediation with comprehensive observability.
    """
    
    def __init__(self, config: XRayMonitoringConfig):
        self.config = config
        self.xray_client = boto3.client('xray')
        self.cloudwatch = boto3.client('cloudwatch')
        self.sns = boto3.client('sns')
        self.lambda_client = boto3.client('lambda')
        self.monitoring_active = False
        self.alert_history = []
        
    async def start_continuous_monitoring(self):
        """Start continuous X-Ray monitoring with automated responses"""
        
        self.monitoring_active = True
        
        # Start monitoring tasks
        monitoring_tasks = [
            self._monitor_service_health(),
            self._monitor_error_rates(),
            self._monitor_performance_degradation(),
            self._monitor_trace_anomalies(),
            self._generate_real_time_dashboards()
        ]
        
        await asyncio.gather(*monitoring_tasks)
    
    async def _monitor_service_health(self):
        """Continuous service health monitoring"""
        
        while self.monitoring_active:
            try:
                services = await self._get_service_list()
                
                for service in services:
                    health_metrics = await self._calculate_service_health(service)
                    
                    if health_metrics['health_score'] < self.config.alert_thresholds.get('health_score', 70):
                        await self._trigger_health_alert(service, health_metrics)
                        await self._auto_remediate_health_issue(service, health_metrics)
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                print(f"Health monitoring error: {e}")
                await asyncio.sleep(30)
    
    async def _monitor_error_rates(self):
        """Monitor and alert on error rate spikes"""
        
        while self.monitoring_active:
            try:
                end_time = datetime.utcnow()
                start_time = end_time - timedelta(minutes=5)
                
                services = await self._get_service_list()
                
                for service in services:
                    error_rate = await self._get_error_rate(service, start_time, end_time)
                    
                    threshold = self.config.alert_thresholds.get('error_rate', 5.0)
                    if error_rate > threshold:
                        await self._trigger_error_rate_alert(service, error_rate)
                        await self._auto_scale_on_errors(service, error_rate)
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                print(f"Error rate monitoring error: {e}")
                await asyncio.sleep(15)
    
    async def _monitor_performance_degradation(self):
        """Monitor for performance degradation patterns"""
        
        while self.monitoring_active:
            try:
                end_time = datetime.utcnow()
                start_time = end_time - timedelta(minutes=10)
                
                services = await self._get_service_list()
                
                for service in services:
                    perf_metrics = await self._get_performance_metrics(service, start_time, end_time)
                    
                    # Check for degradation trends
                    if self._detect_performance_degradation(perf_metrics):
                        await self._trigger_performance_alert(service, perf_metrics)
                        await self._auto_optimize_performance(service, perf_metrics)
                
                await asyncio.sleep(120)  # Check every 2 minutes
                
            except Exception as e:
                print(f"Performance monitoring error: {e}")
                await asyncio.sleep(60)
    
    async def _get_service_list(self) -> List[str]:
        """Get list of active services from X-Ray"""
        
        try:
            response = self.xray_client.get_service_graph(
                StartTime=datetime.utcnow() - timedelta(hours=1),
                EndTime=datetime.utcnow()
            )
            
            services = []
            for service in response.get('Services', []):
                if service.get('Name'):
                    services.append(service['Name'])
            
            return services
            
        except Exception as e:
            print(f"Failed to get service list: {e}")
            return []
    
    async def _calculate_service_health(self, service_name: str) -> Dict[str, float]:
        """Calculate comprehensive service health metrics"""
        
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(minutes=15)
        
        try:
            # Get service statistics
            stats_response = self.xray_client.get_service_statistics(
                StartTime=start_time,
                EndTime=end_time,
                GroupName=service_name
            )
            
            # Get trace summaries
            traces_response = self.xray_client.get_trace_summaries(
                TimeRangeType='TimeRange',
                StartTime=start_time,
                EndTime=end_time,
                FilterExpression=f'service("{service_name}")',
                SamplingStrategy={'Name': 'PartialScan', 'Value': 0.1}
            )
            
            # Calculate metrics
            service_stats = stats_response.get('ServiceStatistics', [])
            trace_summaries = traces_response.get('TraceSummaries', [])
            
            total_requests = sum(stat.get('RequestCount', 0) for stat in service_stats)
            total_errors = sum(stat.get('ErrorStatistics', {}).get('TotalCount', 0) 
                             for stat in service_stats)
            
            error_rate = (total_errors / total_requests * 100) if total_requests > 0 else 0
            
            # Calculate response time metrics
            response_times = [t.get('Duration', 0) for t in trace_summaries]
            avg_response_time = sum(response_times) / len(response_times) if response_times else 0
            
            # Calculate health score
            health_score = self._calculate_health_score(error_rate, avg_response_time)
            
            return {
                'health_score': health_score,
                'error_rate': error_rate,
                'avg_response_time': avg_response_time,
                'total_requests': total_requests,
                'total_errors': total_errors
            }
            
        except Exception as e:
            print(f"Failed to calculate health for {service_name}: {e}")
            return {
                'health_score': 0,
                'error_rate': 100,
                'avg_response_time': 10,
                'total_requests': 0,
                'total_errors': 0
            }
    
    def _calculate_health_score(self, error_rate: float, avg_response_time: float) -> float:
        """Calculate service health score"""
        
        # Error rate component (0-50 points)
        error_score = max(0, 50 - (error_rate * 5))
        
        # Response time component (0-50 points)
        response_score = max(0, 50 - (avg_response_time * 25))
        
        return error_score + response_score
    
    async def _trigger_health_alert(self, service: str, metrics: Dict[str, float]):
        """Trigger health degradation alert"""
        
        alert = {
            'type': 'service_health_degradation',
            'service': service,
            'health_score': metrics['health_score'],
            'error_rate': metrics['error_rate'],
            'avg_response_time': metrics['avg_response_time'],
            'timestamp': datetime.utcnow().isoformat(),
            'severity': 'high' if metrics['health_score'] < 40 else 'medium'
        }
        
        self.alert_history.append(alert)
        
        # Send to notification channels
        for channel in self.config.notification_channels:
            await self._send_alert(channel, alert)
    
    async def _auto_remediate_health_issue(self, service: str, metrics: Dict[str, float]):
        """Automated remediation for health issues"""
        
        remediation_action = self.config.automated_responses.get('health_degradation')
        
        if remediation_action == 'scale_out':
            await self._trigger_auto_scaling(service, 'scale_out')
        elif remediation_action == 'restart_instances':
            await self._restart_service_instances(service)
        elif remediation_action == 'enable_circuit_breaker':
            await self._enable_circuit_breaker(service)
    
    async def _trigger_auto_scaling(self, service: str, action: str):
        """Trigger auto-scaling for service"""
        
        try:
            # Invoke Lambda function for auto-scaling
            response = self.lambda_client.invoke(
                FunctionName=f'auto-scale-{action}',
                InvocationType='Event',
                Payload=json.dumps({
                    'service': service,
                    'action': action,
                    'timestamp': datetime.utcnow().isoformat()
                })
            )
            
            print(f"Auto-scaling triggered for {service}: {action}")
            
        except Exception as e:
            print(f"Failed to trigger auto-scaling: {e}")
    
    async def _generate_real_time_dashboards(self):
        """Generate and update real-time monitoring dashboards"""
        
        while self.monitoring_active:
            try:
                services = await self._get_service_list()
                dashboard_data = {}
                
                for service in services:
                    health_metrics = await self._calculate_service_health(service)
                    dashboard_data[service] = health_metrics
                
                # Create CloudWatch dashboard
                await self._create_cloudwatch_dashboard(dashboard_data)
                
                await asyncio.sleep(300)  # Update every 5 minutes
                
            except Exception as e:
                print(f"Dashboard generation error: {e}")
                await asyncio.sleep(60)
    
    async def _create_cloudwatch_dashboard(self, data: Dict[str, Dict]):
        """Create comprehensive CloudWatch dashboard"""
        
        dashboard_body = {
            "widgets": [
                {
                    "type": "metric",
                    "properties": {
                        "metrics": [["AWS/X-Ray", "ServiceResponseTime", "ServiceName", service] 
                                   for service in data.keys()],
                        "period": 300,
                        "stat": "Average",
                        "region": "us-east-1",
                        "title": "Service Response Times"
                    }
                },
                {
                    "type": "metric",
                    "properties": {
                        "metrics": [["AWS/X-Ray", "ServiceErrorRate", "ServiceName", service] 
                                   for service in data.keys()],
                        "period": 300,
                        "stat": "Average",
                        "region": "us-east-1",
                        "title": "Service Error Rates"
                    }
                },
                {
                    "type": "text",
                    "properties": {
                        "markdown": self._generate_health_summary(data)
                    }
                }
            ]
        }
        
        try:
            self.cloudwatch.put_dashboard(
                DashboardName='XRay-Enterprise-Monitoring',
                DashboardBody=json.dumps(dashboard_body)
            )
        except Exception as e:
            print(f"Failed to create dashboard: {e}")
    
    def _generate_health_summary(self, data: Dict[str, Dict]) -> str:
        """Generate health summary markdown"""
        
        summary = "# X-Ray Service Health Summary\n\n"
        
        for service, metrics in data.items():
            health_emoji = "🟢" if metrics['health_score'] > 80 else "🟡" if metrics['health_score'] > 60 else "🔴"
            summary += f"{health_emoji} **{service}**\n"
            summary += f"  - Health Score: {metrics['health_score']:.1f}/100\n"
            summary += f"  - Error Rate: {metrics['error_rate']:.2f}%\n"
            summary += f"  - Avg Response: {metrics['avg_response_time']:.3f}s\n\n"
        
        return summary

# Usage Example
if __name__ == "__main__":
    # Configure monitoring
    monitoring_config = XRayMonitoringConfig(
        alert_thresholds={
            'health_score': 70,
            'error_rate': 5.0,
            'response_time': 1.0
        },
        dashboard_metrics=[
            'response_time',
            'error_rate',
            'throughput',
            'health_score'
        ],
        automated_responses={
            'health_degradation': 'scale_out',
            'high_error_rate': 'restart_instances',
            'performance_degradation': 'enable_circuit_breaker'
        },
        notification_channels=[
            'arn:aws:sns:us-east-1:123456789012:xray-alerts',
            'arn:aws:sns:us-east-1:123456789012:critical-alerts'
        ]
    )
    
    # Start monitoring
    automation = XRayDevOpsAutomation(monitoring_config)
    
    # Run monitoring (in production, this would be in a container/Lambda)
    asyncio.run(automation.start_continuous_monitoring())
```

## Advanced DevOps Integration Patterns

### CI/CD Pipeline Integration

```yaml
# .github/workflows/xray-monitoring.yml
name: X-Ray Monitoring Integration

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  deploy-with-xray:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Configure X-Ray Sampling Rules
        run: |
          aws xray put-sampling-rule --cli-input-json file://xray-sampling-rules.json
      
      - name: Deploy Application
        run: |
          # Deploy application with X-Ray tracing enabled
          kubectl apply -f k8s/xray-deployment.yaml
      
      - name: Wait for Deployment
        run: |
          kubectl rollout status deployment/app-deployment
      
      - name: Verify X-Ray Integration
        run: |
          python scripts/verify-xray-traces.py
      
      - name: Run Performance Tests
        run: |
          python scripts/performance-tests.py --with-xray
      
      - name: Generate X-Ray Report
        run: |
          python scripts/generate-xray-report.py > xray-deployment-report.md
      
      - name: Upload X-Ray Report
        uses: actions/upload-artifact@v3
        with:
          name: xray-report
          path: xray-deployment-report.md
```

### Terraform X-Ray Infrastructure

```hcl
# terraform/xray.tf
resource "aws_xray_sampling_rule" "critical_endpoints" {
  rule_name      = "CriticalEndpoints"
  priority       = 1000
  version        = 1
  reservoir_size = 2
  fixed_rate     = 1.0
  url_path       = "/api/critical/*"
  host           = "*"
  http_method    = "*"
  service_name   = "*"
  service_type   = "*"
  resource_arn   = "*"
}

resource "aws_xray_sampling_rule" "health_checks" {
  rule_name      = "HealthChecks"
  priority       = 2000
  version        = 1
  reservoir_size = 0
  fixed_rate     = 0.1
  url_path       = "/health"
  host           = "*"
  http_method    = "GET"
  service_name   = "*"
  service_type   = "*"
  resource_arn   = "*"
}

resource "aws_cloudwatch_dashboard" "xray_monitoring" {
  dashboard_name = "XRay-Enterprise-Monitoring"

  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6

        properties = {
          metrics = [
            ["AWS/X-Ray", "ServiceResponseTime"],
            ["AWS/X-Ray", "ServiceErrorRate"],
            ["AWS/X-Ray", "ServiceThroughput"]
          ]
          period = 300
          stat   = "Average"
          region = "us-east-1"
          title  = "X-Ray Service Metrics"
        }
      }
    ]
  })
}

resource "aws_cloudwatch_metric_alarm" "xray_error_rate" {
  alarm_name          = "xray-high-error-rate"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "ServiceErrorRate"
  namespace           = "AWS/X-Ray"
  period              = "300"
  statistic           = "Average"
  threshold           = "5"
  alarm_description   = "This metric monitors X-Ray error rate"
  alarm_actions       = [aws_sns_topic.xray_alerts.arn]
}

resource "aws_sns_topic" "xray_alerts" {
  name = "xray-monitoring-alerts"
}
```

## Enterprise Use Cases & Best Practices

### Microservices Architecture Monitoring
- **Service Dependency Mapping**: Automatic discovery and visualization
- **Cross-Service Transaction Tracking**: End-to-end request journey
- **Performance Bottleneck Identification**: Critical path analysis
- **Cascading Failure Detection**: Downstream impact assessment

### Compliance & Security Monitoring
- **Data Privacy Tracking**: GDPR/CCPA compliance verification
- **Security Event Correlation**: Anomaly detection across services
- **Audit Trail Generation**: Comprehensive request logging
- **Access Pattern Analysis**: Unusual behavior identification

### Cost Optimization Strategies
- **Intelligent Sampling**: Dynamic rate adjustment based on value
- **Selective Tracing**: Critical path prioritization
- **Storage Optimization**: Automated retention policies
- **Regional Distribution**: Cost-effective trace aggregation

### Performance Engineering
- **SLA Monitoring**: Automated compliance verification
- **Capacity Planning**: Predictive scaling based on trends
- **Code-Level Insights**: Function-level performance analysis
- **Database Query Optimization**: Slow query identification

### Incident Response Integration
- **Automated Alert Correlation**: Multi-signal analysis
- **Root Cause Analysis**: Automated trace analysis
- **Rollback Triggers**: Performance-based deployment decisions
- **Post-Incident Reviews**: Comprehensive trace analysis

This enterprise X-Ray implementation provides comprehensive distributed tracing capabilities with advanced monitoring, automated remediation, and deep integration into DevOps workflows for production-ready observability at scale.