# Deployment Strategies Deployment Monitoring

Advanced deployment monitoring strategies, real-time observability, and automated health assessment systems for enterprise deployment operations.

## Table of Contents
1. [Enterprise Deployment Monitoring Architecture](#enterprise-deployment-monitoring-architecture)
2. [Real-Time Health Assessment](#real-time-health-assessment)
3. [Multi-Layer Monitoring Strategy](#multi-layer-monitoring-strategy)
4. [Automated Anomaly Detection](#automated-anomaly-detection)
5. [Business Impact Monitoring](#business-impact-monitoring)
6. [Deployment Success Validation](#deployment-success-validation)
7. [Cross-Service Dependency Monitoring](#cross-service-dependency-monitoring)
8. [Advanced Alerting and Escalation](#advanced-alerting-and-escalation)

## Enterprise Deployment Monitoring Architecture

### Comprehensive Deployment Monitoring System
```python
#!/usr/bin/env python3
# enterprise_deployment_monitor.py
# Advanced deployment monitoring and health assessment system

import asyncio
import json
import logging
import time
import statistics
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any, Callable, Tuple
from enum import Enum
import aiohttp
import aiokafka
import asyncpg
import numpy as np
from prometheus_client.parser import text_string_to_metric_families

class DeploymentPhase(Enum):
    PRE_DEPLOYMENT = "pre_deployment"
    DEPLOYMENT_ACTIVE = "deployment_active"
    POST_DEPLOYMENT = "post_deployment"
    VALIDATION = "validation"
    MONITORING = "monitoring"
    COMPLETED = "completed"
    FAILED = "failed"

class HealthStatus(Enum):
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"

class MetricType(Enum):
    APPLICATION = "application"
    INFRASTRUCTURE = "infrastructure"
    BUSINESS = "business"
    SECURITY = "security"
    PERFORMANCE = "performance"

@dataclass
class DeploymentContext:
    deployment_id: str
    service_name: str
    version: str
    environment: str
    deployment_strategy: str
    started_at: datetime
    expected_duration: timedelta
    canary_percentage: Optional[float] = None
    feature_flags: List[str] = None

@dataclass
class HealthMetric:
    name: str
    value: float
    threshold: float
    status: HealthStatus
    metric_type: MetricType
    timestamp: datetime
    tags: Dict[str, str]
    context: Optional[str] = None

@dataclass
class DeploymentHealthAssessment:
    deployment_id: str
    overall_status: HealthStatus
    phase: DeploymentPhase
    assessment_timestamp: datetime
    metrics: List[HealthMetric]
    anomalies_detected: List[Dict[str, Any]]
    business_impact_score: float
    confidence_level: float
    recommendations: List[str]
    next_assessment_in: timedelta

class EnterpriseDeploymentMonitor:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Active deployment monitoring
        self.active_deployments: Dict[str, DeploymentContext] = {}
        self.health_assessments: Dict[str, List[DeploymentHealthAssessment]] = {}
        
        # Monitoring integrations
        self.prometheus_url = config.get('prometheus_url', 'http://prometheus:9090')
        self.grafana_url = config.get('grafana_url', 'http://grafana:3000')
        self.elasticsearch_url = config.get('elasticsearch_url', 'http://elasticsearch:9200')
        
        # Database connection for deployment tracking
        self.db_connection = None
        
        # Kafka for real-time events
        self.kafka_producer = None
        self.kafka_consumer = None
        
        # Machine learning models for anomaly detection
        self.anomaly_models = {}
        
        # Monitoring thresholds and weights
        self.metric_thresholds = {
            'error_rate': {'warning': 0.02, 'critical': 0.05},
            'response_time_p99': {'warning': 1000, 'critical': 2000},  # ms
            'cpu_utilization': {'warning': 70, 'critical': 90},
            'memory_utilization': {'warning': 80, 'critical': 95},
            'disk_utilization': {'warning': 85, 'critical': 95},
            'conversion_rate_drop': {'warning': 0.10, 'critical': 0.20},
            'revenue_impact': {'warning': 1000, 'critical': 5000}  # dollars
        }
        
        self.metric_weights = {
            MetricType.APPLICATION: 0.35,
            MetricType.INFRASTRUCTURE: 0.25,
            MetricType.BUSINESS: 0.25,
            MetricType.PERFORMANCE: 0.10,
            MetricType.SECURITY: 0.05
        }
    
    async def initialize(self):
        """Initialize the deployment monitoring system"""
        try:
            # Initialize database connection
            self.db_connection = await asyncpg.connect(**self.config['database'])
            
            # Initialize Kafka connections
            if self.config.get('kafka'):
                self.kafka_producer = aiokafka.AIOKafkaProducer(**self.config['kafka'])
                await self.kafka_producer.start()
                
                self.kafka_consumer = aiokafka.AIOKafkaConsumer(
                    'deployment-events',
                    **self.config['kafka']
                )
                await self.kafka_consumer.start()
            
            # Load anomaly detection models
            await self._load_anomaly_models()
            
            # Start background monitoring tasks
            asyncio.create_task(self._deployment_monitoring_loop())
            asyncio.create_task(self._anomaly_detection_loop())
            asyncio.create_task(self._health_assessment_loop())
            
            self.logger.info("Enterprise Deployment Monitor initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize deployment monitor: {e}")
            raise
    
    async def start_deployment_monitoring(self, context: DeploymentContext) -> str:
        """Start monitoring a new deployment"""
        
        deployment_id = context.deployment_id
        self.active_deployments[deployment_id] = context
        self.health_assessments[deployment_id] = []
        
        self.logger.info(f"Started monitoring deployment: {deployment_id}")
        
        # Create initial health assessment
        initial_assessment = await self._perform_health_assessment(context)
        self.health_assessments[deployment_id].append(initial_assessment)
        
        # Send deployment start event
        await self._send_deployment_event({
            'event_type': 'deployment_monitoring_started',
            'deployment_id': deployment_id,
            'service': context.service_name,
            'version': context.version,
            'environment': context.environment,
            'timestamp': datetime.now().isoformat()
        })
        
        return deployment_id
    
    async def _perform_health_assessment(
        self,
        context: DeploymentContext
    ) -> DeploymentHealthAssessment:
        """Perform comprehensive health assessment for a deployment"""
        
        deployment_id = context.deployment_id
        assessment_start = datetime.now()
        
        self.logger.debug(f"Performing health assessment for {deployment_id}")
        
        try:
            # Collect metrics from various sources
            metrics = []
            
            # Application metrics
            app_metrics = await self._collect_application_metrics(context)
            metrics.extend(app_metrics)
            
            # Infrastructure metrics
            infra_metrics = await self._collect_infrastructure_metrics(context)
            metrics.extend(infra_metrics)
            
            # Business metrics
            business_metrics = await self._collect_business_metrics(context)
            metrics.extend(business_metrics)
            
            # Performance metrics
            perf_metrics = await self._collect_performance_metrics(context)
            metrics.extend(perf_metrics)
            
            # Security metrics
            security_metrics = await self._collect_security_metrics(context)
            metrics.extend(security_metrics)
            
            # Detect anomalies
            anomalies = await self._detect_anomalies(context, metrics)
            
            # Calculate overall health status
            overall_status = self._calculate_overall_health_status(metrics)
            
            # Determine deployment phase
            current_phase = self._determine_deployment_phase(context)
            
            # Calculate business impact score
            business_impact_score = self._calculate_business_impact_score(metrics)
            
            # Calculate confidence level
            confidence_level = self._calculate_confidence_level(metrics, anomalies)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(metrics, anomalies, context)
            
            # Determine next assessment timing
            next_assessment_in = self._calculate_next_assessment_interval(
                current_phase, overall_status
            )
            
            assessment = DeploymentHealthAssessment(
                deployment_id=deployment_id,
                overall_status=overall_status,
                phase=current_phase,
                assessment_timestamp=assessment_start,
                metrics=metrics,
                anomalies_detected=anomalies,
                business_impact_score=business_impact_score,
                confidence_level=confidence_level,
                recommendations=recommendations,
                next_assessment_in=next_assessment_in
            )
            
            # Store assessment in database
            await self._store_health_assessment(assessment)
            
            # Send health assessment event
            await self._send_deployment_event({
                'event_type': 'health_assessment_completed',
                'deployment_id': deployment_id,
                'overall_status': overall_status.value,
                'business_impact_score': business_impact_score,
                'anomalies_count': len(anomalies),
                'timestamp': assessment_start.isoformat()
            })
            
            return assessment
            
        except Exception as e:
            self.logger.error(f"Health assessment failed for {deployment_id}: {e}")
            
            # Return failed assessment
            return DeploymentHealthAssessment(
                deployment_id=deployment_id,
                overall_status=HealthStatus.UNKNOWN,
                phase=DeploymentPhase.FAILED,
                assessment_timestamp=assessment_start,
                metrics=[],
                anomalies_detected=[],
                business_impact_score=0.0,
                confidence_level=0.0,
                recommendations=[f"Health assessment failed: {str(e)}"],
                next_assessment_in=timedelta(minutes=5)
            )
    
    async def _collect_application_metrics(
        self,
        context: DeploymentContext
    ) -> List[HealthMetric]:
        """Collect application-level metrics"""
        
        metrics = []
        service = context.service_name
        version = context.version
        environment = context.environment
        
        try:
            async with aiohttp.ClientSession() as session:
                # Error rate metric
                error_rate_query = f'''
                    sum(rate(http_requests_total{{service="{service}",version="{version}",environment="{environment}",status=~"5.."}[5m])) / 
                    sum(rate(http_requests_total{{service="{service}",version="{version}",environment="{environment}"}}[5m])) * 100
                '''
                
                error_rate = await self._execute_prometheus_query(session, error_rate_query)
                if error_rate is not None:
                    status = self._determine_metric_status(
                        error_rate, self.metric_thresholds['error_rate']
                    )
                    metrics.append(HealthMetric(
                        name='error_rate',
                        value=error_rate,
                        threshold=self.metric_thresholds['error_rate']['critical'],
                        status=status,
                        metric_type=MetricType.APPLICATION,
                        timestamp=datetime.now(),
                        tags={'service': service, 'version': version, 'environment': environment},
                        context='Percentage of HTTP requests returning 5xx status codes'
                    ))
                
                # Response time metric
                response_time_query = f'''
                    histogram_quantile(0.99, 
                        sum(rate(http_request_duration_seconds_bucket{{service="{service}",version="{version}",environment="{environment}"}}[5m])) by (le)
                    ) * 1000
                '''
                
                response_time_p99 = await self._execute_prometheus_query(session, response_time_query)
                if response_time_p99 is not None:
                    status = self._determine_metric_status(
                        response_time_p99, self.metric_thresholds['response_time_p99']
                    )
                    metrics.append(HealthMetric(
                        name='response_time_p99',
                        value=response_time_p99,
                        threshold=self.metric_thresholds['response_time_p99']['critical'],
                        status=status,
                        metric_type=MetricType.APPLICATION,
                        timestamp=datetime.now(),
                        tags={'service': service, 'version': version, 'environment': environment},
                        context='99th percentile response time in milliseconds'
                    ))
                
                # Throughput metric
                throughput_query = f'''
                    sum(rate(http_requests_total{{service="{service}",version="{version}",environment="{environment}"}}[5m])) * 60
                '''
                
                throughput = await self._execute_prometheus_query(session, throughput_query)
                if throughput is not None:
                    metrics.append(HealthMetric(
                        name='throughput_rpm',
                        value=throughput,
                        threshold=0,  # No threshold for throughput
                        status=HealthStatus.HEALTHY,
                        metric_type=MetricType.APPLICATION,
                        timestamp=datetime.now(),
                        tags={'service': service, 'version': version, 'environment': environment},
                        context='Requests per minute'
                    ))
                
        except Exception as e:
            self.logger.error(f"Error collecting application metrics: {e}")
        
        return metrics
    
    async def _collect_infrastructure_metrics(
        self,
        context: DeploymentContext
    ) -> List[HealthMetric]:
        """Collect infrastructure-level metrics"""
        
        metrics = []
        service = context.service_name
        version = context.version
        environment = context.environment
        
        try:
            async with aiohttp.ClientSession() as session:
                # CPU utilization
                cpu_query = f'''
                    avg(100 - (avg by (instance) (rate(node_cpu_seconds_total{{mode="idle",service="{service}",environment="{environment}"}}[5m])) * 100))
                '''
                
                cpu_utilization = await self._execute_prometheus_query(session, cpu_query)
                if cpu_utilization is not None:
                    status = self._determine_metric_status(
                        cpu_utilization, self.metric_thresholds['cpu_utilization']
                    )
                    metrics.append(HealthMetric(
                        name='cpu_utilization',
                        value=cpu_utilization,
                        threshold=self.metric_thresholds['cpu_utilization']['critical'],
                        status=status,
                        metric_type=MetricType.INFRASTRUCTURE,
                        timestamp=datetime.now(),
                        tags={'service': service, 'version': version, 'environment': environment},
                        context='Average CPU utilization percentage'
                    ))
                
                # Memory utilization
                memory_query = f'''
                    avg((1 - (node_memory_MemAvailable_bytes{{service="{service}",environment="{environment}"}} / 
                    node_memory_MemTotal_bytes{{service="{service}",environment="{environment}"}})) * 100)
                '''
                
                memory_utilization = await self._execute_prometheus_query(session, memory_query)
                if memory_utilization is not None:
                    status = self._determine_metric_status(
                        memory_utilization, self.metric_thresholds['memory_utilization']
                    )
                    metrics.append(HealthMetric(
                        name='memory_utilization',
                        value=memory_utilization,
                        threshold=self.metric_thresholds['memory_utilization']['critical'],
                        status=status,
                        metric_type=MetricType.INFRASTRUCTURE,
                        timestamp=datetime.now(),
                        tags={'service': service, 'version': version, 'environment': environment},
                        context='Average memory utilization percentage'
                    ))
                
                # Disk utilization
                disk_query = f'''
                    avg((1 - (node_filesystem_avail_bytes{{fstype!~"tmpfs|fuse.lxcfs",service="{service}",environment="{environment}"}} / 
                    node_filesystem_size_bytes{{fstype!~"tmpfs|fuse.lxcfs",service="{service}",environment="{environment}"}})) * 100)
                '''
                
                disk_utilization = await self._execute_prometheus_query(session, disk_query)
                if disk_utilization is not None:
                    status = self._determine_metric_status(
                        disk_utilization, self.metric_thresholds['disk_utilization']
                    )
                    metrics.append(HealthMetric(
                        name='disk_utilization',
                        value=disk_utilization,
                        threshold=self.metric_thresholds['disk_utilization']['critical'],
                        status=status,
                        metric_type=MetricType.INFRASTRUCTURE,
                        timestamp=datetime.now(),
                        tags={'service': service, 'version': version, 'environment': environment},
                        context='Average disk utilization percentage'
                    ))
                
        except Exception as e:
            self.logger.error(f"Error collecting infrastructure metrics: {e}")
        
        return metrics
    
    async def _collect_business_metrics(
        self,
        context: DeploymentContext
    ) -> List[HealthMetric]:
        """Collect business-level metrics"""
        
        metrics = []
        service = context.service_name
        environment = context.environment
        
        try:
            # This would typically integrate with business analytics systems
            # For example, collecting metrics from data warehouse, analytics APIs, etc.
            
            # Mock business metrics collection
            if service in ['user-service', 'payment-service', 'order-service']:
                # Simulate conversion rate monitoring
                baseline_conversion = await self._get_baseline_conversion_rate(service, environment)
                current_conversion = await self._get_current_conversion_rate(service, environment)
                
                if baseline_conversion and current_conversion:
                    conversion_drop = max(0, (baseline_conversion - current_conversion) / baseline_conversion)
                    
                    status = self._determine_metric_status(
                        conversion_drop, self.metric_thresholds['conversion_rate_drop']
                    )
                    
                    metrics.append(HealthMetric(
                        name='conversion_rate_drop',
                        value=conversion_drop,
                        threshold=self.metric_thresholds['conversion_rate_drop']['critical'],
                        status=status,
                        metric_type=MetricType.BUSINESS,
                        timestamp=datetime.now(),
                        tags={'service': service, 'environment': environment},
                        context='Drop in conversion rate compared to baseline'
                    ))
                
                # Revenue impact estimation
                revenue_impact = await self._estimate_revenue_impact(service, context)
                if revenue_impact is not None:
                    status = self._determine_metric_status(
                        revenue_impact, self.metric_thresholds['revenue_impact']
                    )
                    
                    metrics.append(HealthMetric(
                        name='revenue_impact',
                        value=revenue_impact,
                        threshold=self.metric_thresholds['revenue_impact']['critical'],
                        status=status,
                        metric_type=MetricType.BUSINESS,
                        timestamp=datetime.now(),
                        tags={'service': service, 'environment': environment},
                        context='Estimated revenue impact in dollars'
                    ))
        
        except Exception as e:
            self.logger.error(f"Error collecting business metrics: {e}")
        
        return metrics
    
    async def _detect_anomalies(
        self,
        context: DeploymentContext,
        metrics: List[HealthMetric]
    ) -> List[Dict[str, Any]]:
        """Detect anomalies in deployment metrics"""
        
        anomalies = []
        
        try:
            # Statistical anomaly detection
            statistical_anomalies = await self._detect_statistical_anomalies(context, metrics)
            anomalies.extend(statistical_anomalies)
            
            # Pattern-based anomaly detection
            pattern_anomalies = await self._detect_pattern_anomalies(context, metrics)
            anomalies.extend(pattern_anomalies)
            
            # Machine learning based anomaly detection
            if self.anomaly_models:
                ml_anomalies = await self._detect_ml_anomalies(context, metrics)
                anomalies.extend(ml_anomalies)
            
            # Cross-metric correlation anomalies
            correlation_anomalies = await self._detect_correlation_anomalies(context, metrics)
            anomalies.extend(correlation_anomalies)
            
        except Exception as e:
            self.logger.error(f"Error detecting anomalies: {e}")
        
        return anomalies
    
    async def _detect_statistical_anomalies(
        self,
        context: DeploymentContext,
        metrics: List[HealthMetric]
    ) -> List[Dict[str, Any]]:
        """Detect statistical anomalies using historical data"""
        
        anomalies = []
        
        try:
            # Get historical metric values for comparison
            for metric in metrics:
                if metric.metric_type in [MetricType.APPLICATION, MetricType.PERFORMANCE]:
                    historical_values = await self._get_historical_metric_values(
                        context.service_name,
                        context.environment,
                        metric.name,
                        hours=24
                    )
                    
                    if len(historical_values) >= 10:  # Minimum data points needed
                        mean_value = statistics.mean(historical_values)
                        std_value = statistics.stdev(historical_values)
                        
                        # Z-score based anomaly detection
                        z_score = abs((metric.value - mean_value) / std_value) if std_value > 0 else 0
                        
                        if z_score > 3:  # 3 standard deviations
                            anomalies.append({
                                'type': 'statistical',
                                'metric_name': metric.name,
                                'current_value': metric.value,
                                'historical_mean': mean_value,
                                'z_score': z_score,
                                'severity': 'high' if z_score > 4 else 'medium',
                                'description': f'{metric.name} is {z_score:.2f} standard deviations from historical mean'
                            })
        
        except Exception as e:
            self.logger.error(f"Error in statistical anomaly detection: {e}")
        
        return anomalies
    
    def _calculate_overall_health_status(self, metrics: List[HealthMetric]) -> HealthStatus:
        """Calculate overall health status from all metrics"""
        
        if not metrics:
            return HealthStatus.UNKNOWN
        
        # Count metrics by status
        status_counts = {
            HealthStatus.HEALTHY: 0,
            HealthStatus.WARNING: 0,
            HealthStatus.CRITICAL: 0,
            HealthStatus.UNKNOWN: 0
        }
        
        weighted_score = 0.0
        total_weight = 0.0
        
        for metric in metrics:
            status_counts[metric.status] += 1
            
            # Calculate weighted score
            weight = self.metric_weights.get(metric.metric_type, 0.1)
            total_weight += weight
            
            if metric.status == HealthStatus.CRITICAL:
                weighted_score += weight * 0  # Critical = 0 points
            elif metric.status == HealthStatus.WARNING:
                weighted_score += weight * 0.5  # Warning = 0.5 points
            elif metric.status == HealthStatus.HEALTHY:
                weighted_score += weight * 1.0  # Healthy = 1 point
            # Unknown status gets no points
        
        # Normalize score
        if total_weight > 0:
            normalized_score = weighted_score / total_weight
        else:
            normalized_score = 0
        
        # Determine overall status based on critical metrics and normalized score
        if status_counts[HealthStatus.CRITICAL] > 0:
            return HealthStatus.CRITICAL
        elif status_counts[HealthStatus.WARNING] > 0 and normalized_score < 0.7:
            return HealthStatus.WARNING
        elif normalized_score >= 0.8:
            return HealthStatus.HEALTHY
        else:
            return HealthStatus.WARNING
    
    def _calculate_business_impact_score(self, metrics: List[HealthMetric]) -> float:
        """Calculate business impact score (0-10 scale)"""
        
        business_metrics = [m for m in metrics if m.metric_type == MetricType.BUSINESS]
        
        if not business_metrics:
            # Estimate business impact from application metrics
            app_metrics = [m for m in metrics if m.metric_type == MetricType.APPLICATION]
            impact_score = 0.0
            
            for metric in app_metrics:
                if metric.name == 'error_rate' and metric.status == HealthStatus.CRITICAL:
                    impact_score += 3.0
                elif metric.name == 'response_time_p99' and metric.status == HealthStatus.CRITICAL:
                    impact_score += 2.0
                elif metric.status == HealthStatus.WARNING:
                    impact_score += 1.0
            
            return min(impact_score, 10.0)
        
        # Calculate from actual business metrics
        total_impact = 0.0
        
        for metric in business_metrics:
            if metric.name == 'conversion_rate_drop':
                impact = min(metric.value * 20, 5.0)  # Scale to 0-5
                total_impact += impact
            elif metric.name == 'revenue_impact':
                impact = min(metric.value / 1000, 5.0)  # $1000 = 1 impact point
                total_impact += impact
        
        return min(total_impact, 10.0)
    
    async def _deployment_monitoring_loop(self):
        """Main deployment monitoring loop"""
        
        while True:
            try:
                current_time = datetime.now()
                
                for deployment_id, context in list(self.active_deployments.items()):
                    # Check if deployment monitoring should continue
                    if await self._should_continue_monitoring(context, current_time):
                        # Get latest assessment
                        latest_assessment = self.health_assessments[deployment_id][-1] if self.health_assessments[deployment_id] else None
                        
                        # Check if it's time for next assessment
                        if (latest_assessment is None or 
                            current_time >= latest_assessment.assessment_timestamp + latest_assessment.next_assessment_in):
                            
                            # Perform new health assessment
                            new_assessment = await self._perform_health_assessment(context)
                            self.health_assessments[deployment_id].append(new_assessment)
                            
                            # Check for alerts
                            await self._check_and_send_alerts(context, new_assessment)
                    else:
                        # Remove completed deployment from active monitoring
                        await self._finalize_deployment_monitoring(deployment_id, context)
                        del self.active_deployments[deployment_id]
                
                # Wait before next iteration
                await asyncio.sleep(30)
                
            except Exception as e:
                self.logger.error(f"Error in deployment monitoring loop: {e}")
                await asyncio.sleep(60)  # Wait longer on error
    
    def generate_deployment_health_report(self, deployment_id: str) -> str:
        """Generate comprehensive deployment health report"""
        
        if deployment_id not in self.health_assessments:
            return f"No health assessments found for deployment {deployment_id}"
        
        context = self.active_deployments.get(deployment_id)
        assessments = self.health_assessments[deployment_id]
        
        if not assessments:
            return f"No health assessments available for deployment {deployment_id}"
        
        latest_assessment = assessments[-1]
        
        report = f"""
# Deployment Health Report

**Deployment ID:** {deployment_id}
**Service:** {context.service_name if context else 'Unknown'}
**Version:** {context.version if context else 'Unknown'}
**Environment:** {context.environment if context else 'Unknown'}

## Current Status
- **Overall Health:** {latest_assessment.overall_status.value.upper()}
- **Deployment Phase:** {latest_assessment.phase.value}
- **Business Impact Score:** {latest_assessment.business_impact_score:.1f}/10.0
- **Confidence Level:** {latest_assessment.confidence_level:.1%}
- **Last Assessment:** {latest_assessment.assessment_timestamp}

## Health Metrics Summary
"""
        
        # Group metrics by type
        metrics_by_type = {}
        for metric in latest_assessment.metrics:
            if metric.metric_type not in metrics_by_type:
                metrics_by_type[metric.metric_type] = []
            metrics_by_type[metric.metric_type].append(metric)
        
        for metric_type, metrics in metrics_by_type.items():
            report += f"\n### {metric_type.value.title()} Metrics\n"
            for metric in metrics:
                status_icon = {
                    HealthStatus.HEALTHY: "✅",
                    HealthStatus.WARNING: "⚠️",
                    HealthStatus.CRITICAL: "❌",
                    HealthStatus.UNKNOWN: "❓"
                }[metric.status]
                
                report += f"- {status_icon} **{metric.name}:** {metric.value:.2f} "
                if metric.threshold > 0:
                    report += f"(threshold: {metric.threshold})"
                report += "\n"
        
        # Anomalies section
        if latest_assessment.anomalies_detected:
            report += f"\n## Anomalies Detected ({len(latest_assessment.anomalies_detected)})\n"
            for anomaly in latest_assessment.anomalies_detected:
                report += f"- **{anomaly['type'].title()}:** {anomaly.get('description', 'No description')}\n"
        
        # Recommendations section
        if latest_assessment.recommendations:
            report += "\n## Recommendations\n"
            for recommendation in latest_assessment.recommendations:
                report += f"- {recommendation}\n"
        
        # Historical trend
        if len(assessments) > 1:
            report += f"\n## Health Trend ({len(assessments)} assessments)\n"
            
            status_trend = [a.overall_status.value for a in assessments[-5:]]  # Last 5 assessments
            business_impact_trend = [a.business_impact_score for a in assessments[-5:]]
            
            report += f"- **Status Trend:** {' → '.join(status_trend)}\n"
            report += f"- **Business Impact Trend:** {' → '.join([f'{score:.1f}' for score in business_impact_trend])}\n"
        
        return report

# Usage example
async def main():
    config = {
        'prometheus_url': 'http://prometheus:9090',
        'grafana_url': 'http://grafana:3000',
        'database': {
            'host': 'localhost',
            'port': 5432,
            'database': 'deployment_monitoring',
            'user': 'monitor',
            'password': 'secure_password'
        },
        'kafka': {
            'bootstrap_servers': 'kafka:9092'
        }
    }
    
    monitor = EnterpriseDeploymentMonitor(config)
    await monitor.initialize()
    
    # Example deployment context
    deployment_context = DeploymentContext(
        deployment_id='deploy-20231201-001',
        service_name='user-service',
        version='v2.3.0',
        environment='production',
        deployment_strategy='canary',
        started_at=datetime.now(),
        expected_duration=timedelta(hours=2),
        canary_percentage=10.0,
        feature_flags=['new_user_flow', 'enhanced_validation']
    )
    
    # Start monitoring
    deployment_id = await monitor.start_deployment_monitoring(deployment_context)
    
    # Simulate monitoring for some time
    await asyncio.sleep(300)  # 5 minutes
    
    # Generate report
    report = monitor.generate_deployment_health_report(deployment_id)
    print(report)

if __name__ == "__main__":
    asyncio.run(main())
```

## Real-Time Health Assessment

### Advanced Health Assessment Framework
```yaml
# Real-time health assessment configuration
health_assessment_framework:
  assessment_layers:
    layer_1_immediate:
      interval: "30s"
      timeout: "10s"
      metrics:
        - http_status_codes
        - basic_connectivity
        - container_status
        - load_balancer_health
      
      thresholds:
        error_rate: "> 1%"
        response_time: "> 500ms"
        availability: "< 99.5%"
      
      actions:
        critical: "immediate_alert"
        warning: "log_and_monitor"
    
    layer_2_comprehensive:
      interval: "2m"
      timeout: "30s"
      metrics:
        - detailed_application_metrics
        - infrastructure_utilization
        - database_performance
        - external_dependency_health
      
      thresholds:
        cpu_utilization: "> 80%"
        memory_utilization: "> 85%"
        disk_io_latency: "> 100ms"
        database_connection_pool: "> 80%"
      
      actions:
        critical: "escalate_to_oncall"
        warning: "create_incident"
    
    layer_3_business_impact:
      interval: "5m"
      timeout: "60s"
      metrics:
        - conversion_rates
        - revenue_metrics
        - user_experience_scores
        - business_kpis
      
      thresholds:
        conversion_drop: "> 10%"
        revenue_impact: "> $1000/hour"
        user_satisfaction: "< 4.0/5.0"
      
      actions:
        critical: "executive_notification"
        warning: "business_stakeholder_alert"
  
  assessment_strategies:
    pre_deployment:
      validations:
        - environment_readiness
        - dependency_availability
        - resource_allocation
        - security_compliance
      
      gates:
        - infrastructure_health_check
        - baseline_metric_collection
        - rollback_plan_validation
        - monitoring_system_validation
    
    during_deployment:
      progressive_validation:
        phases:
          - initial_deployment: "0-10%"
          - gradual_rollout: "10-50%"
          - full_deployment: "50-100%"
        
        validation_per_phase:
          - health_check_validation
          - performance_regression_test
          - business_impact_assessment
          - user_feedback_analysis
    
    post_deployment:
      extended_monitoring:
        duration: "24h"
        intervals:
          - first_hour: "1m"
          - next_6_hours: "5m"
          - remaining: "15m"
        
        validation_criteria:
          - metric_stabilization
          - no_regression_detected
          - business_metrics_stable
          - user_feedback_positive

real_time_alerting:
  alert_channels:
    immediate:
      - slack_critical_channel
      - pagerduty_escalation
      - sms_notification
      - email_urgent
    
    delayed:
      - email_summary
      - dashboard_update
      - log_aggregation
      - metrics_update
  
  alert_rules:
    deployment_failure:
      conditions:
        - deployment_status: "failed"
        - error_rate: "> 10%"
        - health_check_failures: "> 3"
      
      severity: "critical"
      channels: ["immediate"]
      escalation_time: "5m"
    
    performance_degradation:
      conditions:
        - response_time_increase: "> 50%"
        - throughput_decrease: "> 30%"
        - error_rate_increase: "> 200%"
      
      severity: "high"
      channels: ["immediate", "delayed"]
      escalation_time: "15m"
    
    business_impact:
      conditions:
        - conversion_rate_drop: "> 15%"
        - revenue_impact: "> $5000"
        - user_complaints: "> 100"
      
      severity: "critical"
      channels: ["immediate"]
      escalation_time: "2m"
      executive_notification: true
```

This comprehensive deployment monitoring system provides enterprise-grade capabilities for real-time health assessment, anomaly detection, business impact monitoring, and automated alerting with sophisticated health scoring and trend analysis.