# AWS CloudWatch

> **Service Type:** Monitoring & Observability | **Tier:** Essential DevOps | **Global/Regional:** Regional

## Overview

Amazon CloudWatch is a comprehensive monitoring and observability service for AWS resources and applications. It provides real-time monitoring, alerting, and log analysis capabilities essential for maintaining reliable, scalable systems and implementing effective DevOps practices.

## DevOps Use Cases

### Infrastructure Monitoring
- **System metrics monitoring** for CPU, memory, disk, and network utilization
- **Auto Scaling triggers** based on performance thresholds
- **Cost optimization** through resource utilization analysis
- **Capacity planning** using historical performance data

### Application Performance Management
- **Application-level metrics** for response times, error rates, throughput
- **Custom business metrics** tracking user behavior and business KPIs
- **Database performance monitoring** for RDS, DynamoDB, and custom databases
- **API monitoring** for latency, error rates, and request patterns

### DevOps Pipeline Monitoring
- **CI/CD pipeline metrics** for build success rates, deployment frequency
- **Deployment monitoring** with automatic rollback triggers
- **Blue-green deployment validation** using health metrics
- **Feature flag effectiveness** tracking through custom metrics

### Security and Compliance
- **Security event monitoring** from CloudTrail and VPC Flow Logs
- **Compliance dashboards** for audit and regulatory requirements
- **Anomaly detection** for unusual access patterns or performance
- **Real-time alerting** for security incidents and policy violations

### Centralized Logging
- **Multi-service log aggregation** from EC2, Lambda, ECS, and custom applications
- **Structured logging** with JSON parsing and field extraction
- **Log correlation** across distributed systems and microservices
- **Audit trail maintenance** for security and compliance requirements

## Core Components

### Metrics
- **Definition:** Numerical data points collected over time (CPU, RAM, Disk space, Network, Processes, Swap)
- **Sources:** AWS services, custom applications, CloudWatch Agent
- **Resolution:** Standard (5-minute) or high-resolution (1-second intervals)
- **Retention:** Automatic data retention based on age (15 months for 5-minute data)

### Logs
- **Purpose:** Log file monitoring and analysis from multiple sources
- **Destinations:** S3, Kinesis Streams, Kinesis Firehose, Lambda functions
- **Sources:** SDK, CloudWatch Agents, Elastic Beanstalk, ECS, Lambda, VPC Flow Logs, API Gateway, CloudTrail, Route 53
- **Features:** Real-time streaming, filtering, and metric generation from logs

### Events/EventBridge
- **Function:** Rule-based event processing and routing
- **Triggers:** AWS service state changes, scheduled events, custom applications
- **Targets:** Lambda, SNS, SQS, Step Functions, ECS tasks
- **Use Cases:** Infrastructure automation, incident response, workflow orchestration

### Alarms
- **Purpose:** Threshold-based notifications and automated actions
- **States:** OK, INSUFFICIENT_DATA, ALARM
- **Actions:** SNS notifications, Auto Scaling actions, EC2 actions (stop/terminate/reboot)
- **Types:** Static thresholds, anomaly detection, composite alarms

## Advanced Features

### Custom Metrics and Dashboards
- **Custom Metrics:** Application-specific performance indicators
- **Interactive Dashboards:** Real-time visualization with drill-down capabilities
- **Cross-Region Views:** Unified monitoring across multiple AWS regions
- **Shared Dashboards:** Team collaboration and standardized views

### Log Insights
- **Purpose:** Interactive search and analysis across multiple log groups
- **Query Language:** Purpose-built query syntax for log analysis
- **Visualization:** Charts, tables, and time-series analysis
- **Performance:** Fast queries across large log datasets

### Specialized Monitoring

#### Application Insights
- **Supported:** .NET and SQL Server applications
- **Features:** Automatic application discovery and monitoring setup
- **Metrics:** Application performance, dependencies, and health

#### Container Insights
- **Supported:** Amazon ECS and Amazon EKS
- **Metrics:** Container-level CPU, memory, network, and storage
- **Logs:** Container logs with automatic parsing

#### Synthetics
- **Purpose:** Proactive endpoint monitoring and user experience testing
- **Canaries:** Automated scripts that run on scheduled intervals
- **Monitoring:** Website availability, API functionality, user workflows

### Anomaly Detection
- **Machine Learning:** Automatic baseline establishment and anomaly detection
- **Adaptive Thresholds:** Dynamic alarm thresholds based on historical patterns
- **Seasonality:** Recognition of daily, weekly, and monthly patterns

### Composite Alarms
- **Function:** Combine multiple alarms using Boolean logic
- **Use Cases:** Complex alerting scenarios, reduced alarm noise
- **Actions:** Same as standard alarms but with more sophisticated triggering

## Practical CLI Examples

### Metrics Management

```bash
# Put custom metric
aws cloudwatch put-metric-data \
  --namespace "MyApp/Performance" \
  --metric-data \
    MetricName=ResponseTime,Value=150,Unit=Milliseconds,Dimensions=[{Name=Environment,Value=Production},{Name=Service,Value=API}] \
    MetricName=ErrorRate,Value=0.05,Unit=Percent,Dimensions=[{Name=Environment,Value=Production},{Name=Service,Value=API}]

# Get metric statistics
aws cloudwatch get-metric-statistics \
  --namespace AWS/EC2 \
  --metric-name CPUUtilization \
  --dimensions Name=InstanceId,Value=i-1234567890abcdef0 \
  --start-time 2024-01-15T00:00:00Z \
  --end-time 2024-01-15T23:59:59Z \
  --period 3600 \
  --statistics Average,Maximum

# List metrics
aws cloudwatch list-metrics \
  --namespace "MyApp/Performance" \
  --metric-name ResponseTime
```

### Alarms Management

```bash
# Create CPU alarm
aws cloudwatch put-metric-alarm \
  --alarm-name "High-CPU-Usage" \
  --alarm-description "Alarm when server CPU exceeds 80%" \
  --metric-name CPUUtilization \
  --namespace AWS/EC2 \
  --statistic Average \
  --period 300 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2 \
  --alarm-actions arn:aws:sns:us-west-2:123456789012:high-cpu-alert \
  --dimensions Name=InstanceId,Value=i-1234567890abcdef0

# Create composite alarm
aws cloudwatch put-composite-alarm \
  --alarm-name "Application-Health-Check" \
  --alarm-description "Overall application health" \
  --alarm-rule "(ALARM('High-CPU-Usage') OR ALARM('High-Memory-Usage')) AND ALARM('Low-Disk-Space')" \
  --actions-enabled \
  --alarm-actions arn:aws:sns:us-west-2:123456789012:critical-alerts

# Create anomaly detector
aws cloudwatch put-anomaly-detector \
  --namespace AWS/ApplicationELB \
  --metric-name TargetResponseTime \
  --dimensions Name=LoadBalancer,Value=app/my-load-balancer/1234567890123456 \
  --stat Average

# Test alarm
aws cloudwatch set-alarm-state \
  --alarm-name "High-CPU-Usage" \
  --state-value ALARM \
  --state-reason "Testing alarm notification"
```

### Log Management

```bash
# Create log group
aws logs create-log-group \
  --log-group-name /aws/lambda/my-function \
  --retention-in-days 14

# Create log stream
aws logs create-log-stream \
  --log-group-name /aws/lambda/my-function \
  --log-stream-name "2024/01/15/production"

# Put log events
aws logs put-log-events \
  --log-group-name /aws/lambda/my-function \
  --log-stream-name "2024/01/15/production" \
  --log-events \
    timestamp=$(date +%s)000,message='{"level":"INFO","message":"Application started","service":"api"}' \
    timestamp=$(date +%s)001,message='{"level":"ERROR","message":"Database connection failed","service":"api","error":"timeout"}'

# Query logs with CloudWatch Insights
aws logs start-query \
  --log-group-name /aws/lambda/my-function \
  --start-time $(date -d '1 hour ago' +%s) \
  --end-time $(date +%s) \
  --query-string 'fields @timestamp, @message | filter @message like /ERROR/ | sort @timestamp desc | limit 20'

# Create metric filter
aws logs put-metric-filter \
  --log-group-name /aws/lambda/my-function \
  --filter-name ErrorCount \
  --filter-pattern '{ $.level = "ERROR" }' \
  --metric-transformations \
    metricName=ApplicationErrors,metricNamespace=MyApp/Errors,metricValue=1,defaultValue=0
```

### Dashboard Management

```bash
# Create dashboard
cat > dashboard.json << 'EOF'
{
  "widgets": [
    {
      "type": "metric",
      "properties": {
        "metrics": [
          ["AWS/EC2", "CPUUtilization", "InstanceId", "i-1234567890abcdef0"],
          ["AWS/ApplicationELB", "TargetResponseTime", "LoadBalancer", "app/my-load-balancer/1234567890123456"]
        ],
        "period": 300,
        "stat": "Average",
        "region": "us-west-2",
        "title": "Application Performance"
      }
    },
    {
      "type": "log",
      "properties": {
        "query": "SOURCE '/aws/lambda/my-function' | fields @timestamp, @message | filter @message like /ERROR/ | sort @timestamp desc | limit 20",
        "region": "us-west-2",
        "title": "Recent Errors"
      }
    }
  ]
}
EOF

aws cloudwatch put-dashboard \
  --dashboard-name "Production-Overview" \
  --dashboard-body file://dashboard.json
```

## DevOps Automation Scripts

### Application Monitoring Setup

```bash
#!/bin/bash
# setup-monitoring.sh - Automated monitoring setup for new applications

APP_NAME=$1
ENVIRONMENT=$2
SNS_TOPIC_ARN=$3

if [ $# -ne 3 ]; then
    echo "Usage: $0 <app-name> <environment> <sns-topic-arn>"
    exit 1
fi

NAMESPACE="Custom/${APP_NAME}"
LOG_GROUP="/aws/application/${APP_NAME}"

echo "Setting up monitoring for ${APP_NAME} in ${ENVIRONMENT}"

# Create log group
aws logs create-log-group \
  --log-group-name ${LOG_GROUP} \
  --retention-in-days 30

# Create error metric filter
aws logs put-metric-filter \
  --log-group-name ${LOG_GROUP} \
  --filter-name "${APP_NAME}-ErrorCount" \
  --filter-pattern '{ $.level = "ERROR" }' \
  --metric-transformations \
    metricName=ErrorCount,metricNamespace=${NAMESPACE},metricValue=1,defaultValue=0

# Create response time alarm
aws cloudwatch put-metric-alarm \
  --alarm-name "${APP_NAME}-HighResponseTime" \
  --alarm-description "High response time for ${APP_NAME}" \
  --metric-name ResponseTime \
  --namespace ${NAMESPACE} \
  --statistic Average \
  --period 300 \
  --threshold 2000 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2 \
  --alarm-actions ${SNS_TOPIC_ARN} \
  --dimensions Name=Environment,Value=${ENVIRONMENT}

# Create error rate alarm
aws cloudwatch put-metric-alarm \
  --alarm-name "${APP_NAME}-HighErrorRate" \
  --alarm-description "High error rate for ${APP_NAME}" \
  --metric-name ErrorCount \
  --namespace ${NAMESPACE} \
  --statistic Sum \
  --period 300 \
  --threshold 10 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 1 \
  --alarm-actions ${SNS_TOPIC_ARN} \
  --dimensions Name=Environment,Value=${ENVIRONMENT}

echo "Monitoring setup completed for ${APP_NAME}"
```

### Infrastructure Health Check

```bash
#!/bin/bash
# health-check.sh - Comprehensive infrastructure health monitoring

REGION="us-west-2"
SNS_TOPIC="arn:aws:sns:${REGION}:123456789012:infrastructure-alerts"

# Check EC2 instances
echo "Checking EC2 instance health..."
UNHEALTHY_INSTANCES=$(aws ec2 describe-instance-status \
  --region ${REGION} \
  --filters "Name=instance-status.status,Values=impaired" \
  --query 'InstanceStatuses[*].InstanceId' \
  --output text)

if [ ! -z "$UNHEALTHY_INSTANCES" ]; then
    aws sns publish \
      --topic-arn ${SNS_TOPIC} \
      --message "Unhealthy EC2 instances detected: ${UNHEALTHY_INSTANCES}" \
      --subject "EC2 Health Alert"
fi

# Check RDS instances
echo "Checking RDS instance health..."
UNHEALTHY_RDS=$(aws rds describe-db-instances \
  --region ${REGION} \
  --query 'DBInstances[?DBInstanceStatus!=`available`].[DBInstanceIdentifier,DBInstanceStatus]' \
  --output text)

if [ ! -z "$UNHEALTHY_RDS" ]; then
    aws sns publish \
      --topic-arn ${SNS_TOPIC} \
      --message "RDS instances with issues: ${UNHEALTHY_RDS}" \
      --subject "RDS Health Alert"
fi

# Check Load Balancer targets
echo "Checking Load Balancer target health..."
TARGET_GROUPS=$(aws elbv2 describe-target-groups \
  --region ${REGION} \
  --query 'TargetGroups[*].TargetGroupArn' \
  --output text)

for tg in ${TARGET_GROUPS}; do
    UNHEALTHY_TARGETS=$(aws elbv2 describe-target-health \
      --target-group-arn ${tg} \
      --query 'TargetHealthDescriptions[?TargetHealth.State!=`healthy`].Target.Id' \
      --output text)
    
    if [ ! -z "$UNHEALTHY_TARGETS" ]; then
        aws sns publish \
          --topic-arn ${SNS_TOPIC} \
          --message "Unhealthy targets in ${tg}: ${UNHEALTHY_TARGETS}" \
          --subject "Load Balancer Health Alert"
    fi
done

echo "Health check completed"
```

### Log Analysis and Alerting

```bash
#!/bin/bash
# analyze-logs.sh - Automated log analysis and alerting

LOG_GROUP="/aws/lambda/api-gateway"
TIME_WINDOW_MINUTES=15
ERROR_THRESHOLD=50

# Calculate time range
END_TIME=$(date +%s)
START_TIME=$((END_TIME - TIME_WINDOW_MINUTES * 60))

echo "Analyzing logs from $(date -d @${START_TIME}) to $(date -d @${END_TIME})"

# Query for errors in the last 15 minutes
QUERY_ID=$(aws logs start-query \
  --log-group-name ${LOG_GROUP} \
  --start-time ${START_TIME} \
  --end-time ${END_TIME} \
  --query-string 'fields @timestamp, @message | filter @message like /ERROR/ | stats count() as error_count' \
  --query 'queryId' \
  --output text)

echo "Query ID: ${QUERY_ID}"

# Wait for query to complete
sleep 10

# Get query results
RESULTS=$(aws logs get-query-results \
  --query-id ${QUERY_ID} \
  --query 'results[0][0].value' \
  --output text)

ERROR_COUNT=${RESULTS:-0}

echo "Error count in last ${TIME_WINDOW_MINUTES} minutes: ${ERROR_COUNT}"

if [ ${ERROR_COUNT} -gt ${ERROR_THRESHOLD} ]; then
    # Send alert
    aws sns publish \
      --topic-arn arn:aws:sns:us-west-2:123456789012:error-alerts \
      --message "High error count detected: ${ERROR_COUNT} errors in ${TIME_WINDOW_MINUTES} minutes" \
      --subject "Application Error Spike Alert"
    
    # Create CloudWatch metric
    aws cloudwatch put-metric-data \
      --namespace "Custom/ApplicationHealth" \
      --metric-data MetricName=ErrorSpike,Value=1,Unit=Count,Dimensions=[{Name=Service,Value=API}]
fi
```

### Performance Monitoring Dashboard

```bash
#!/bin/bash
# create-performance-dashboard.sh - Create comprehensive performance dashboard

APP_NAME=$1
ENVIRONMENT=$2

if [ $# -ne 2 ]; then
    echo "Usage: $0 <app-name> <environment>"
    exit 1
fi

DASHBOARD_NAME="${APP_NAME}-${ENVIRONMENT}-Performance"

cat > dashboard.json << EOF
{
  "widgets": [
    {
      "type": "metric",
      "x": 0, "y": 0, "width": 12, "height": 6,
      "properties": {
        "metrics": [
          ["AWS/ApplicationELB", "TargetResponseTime", "LoadBalancer", "app/${APP_NAME}-${ENVIRONMENT}"],
          ["AWS/ApplicationELB", "RequestCount", "LoadBalancer", "app/${APP_NAME}-${ENVIRONMENT}"],
          ["AWS/ApplicationELB", "HTTPCode_Target_4XX_Count", "LoadBalancer", "app/${APP_NAME}-${ENVIRONMENT}"],
          ["AWS/ApplicationELB", "HTTPCode_Target_5XX_Count", "LoadBalancer", "app/${APP_NAME}-${ENVIRONMENT}"]
        ],
        "period": 300,
        "stat": "Average",
        "region": "us-west-2",
        "title": "Application Load Balancer Metrics",
        "yAxis": {"left": {"min": 0}}
      }
    },
    {
      "type": "metric",
      "x": 12, "y": 0, "width": 12, "height": 6,
      "properties": {
        "metrics": [
          ["AWS/ECS", "CPUUtilization", "ServiceName", "${APP_NAME}-${ENVIRONMENT}"],
          ["AWS/ECS", "MemoryUtilization", "ServiceName", "${APP_NAME}-${ENVIRONMENT}"]
        ],
        "period": 300,
        "stat": "Average",
        "region": "us-west-2",
        "title": "ECS Service Metrics",
        "yAxis": {"left": {"min": 0, "max": 100}}
      }
    },
    {
      "type": "log",
      "x": 0, "y": 6, "width": 24, "height": 6,
      "properties": {
        "query": "SOURCE '/aws/ecs/${APP_NAME}-${ENVIRONMENT}' | fields @timestamp, @message | filter @message like /ERROR/ | sort @timestamp desc | limit 50",
        "region": "us-west-2",
        "title": "Recent Application Errors"
      }
    }
  ]
}
EOF

aws cloudwatch put-dashboard \
  --dashboard-name ${DASHBOARD_NAME} \
  --dashboard-body file://dashboard.json

echo "Dashboard created: ${DASHBOARD_NAME}"
rm -f dashboard.json
```

## Best Practices

### Monitoring Strategy
- **Layered Monitoring:** Infrastructure, application, and business metrics
- **Proactive Alerting:** Use anomaly detection and predictive analytics
- **Alert Fatigue Prevention:** Carefully tune thresholds and use composite alarms
- **Metric Standardization:** Consistent naming conventions and dimensions

### Cost Optimization
- **Log Retention:** Set appropriate retention periods for different log types
- **High-Resolution Metrics:** Use only when necessary (additional cost)
- **Cross-Region Data Transfer:** Minimize unnecessary data movement
- **API Usage:** Batch API calls and use efficient query patterns

### Security and Compliance
- **IAM Permissions:** Least privilege access to CloudWatch resources
- **Log Encryption:** Enable encryption for sensitive log data
- **Access Logging:** Monitor who accesses monitoring data
- **Data Retention:** Comply with regulatory requirements for log retention

## Advanced Observability and Site Reliability Engineering Patterns

### Enterprise Observability Architecture

#### Comprehensive Observability Framework
```python
# observability_framework.py - Enterprise observability and SRE patterns
import boto3
import json
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import statistics
from aws_lambda_powertools import Logger, Tracer, Metrics
from aws_lambda_powertools.metrics import MetricUnit

logger = Logger()
tracer = Tracer()
metrics = Metrics()

class AlertSeverity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

class ServiceLevel(Enum):
    AVAILABILITY = "availability"
    LATENCY = "latency"
    ERROR_RATE = "error_rate"
    THROUGHPUT = "throughput"

@dataclass
class SLO:
    """Service Level Objective configuration"""
    name: str
    service: str
    objective_type: ServiceLevel
    target_percentage: float
    measurement_window_days: int = 30
    alert_threshold_percentage: float = 1.0  # Alert when within 1% of breach
    error_budget_policy: str = "linear"
    
@dataclass
class SLI:
    """Service Level Indicator measurement"""
    timestamp: datetime
    service: str
    metric_type: ServiceLevel
    value: float
    target: float
    is_good: bool
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ErrorBudget:
    """Error budget tracking and burn rate analysis"""
    slo_name: str
    total_budget: float
    consumed_budget: float
    remaining_budget: float
    current_burn_rate: float
    time_to_exhaustion_hours: Optional[float]
    health_status: str

class SREObservabilityEngine:
    """
    Advanced Site Reliability Engineering observability platform
    """
    
    def __init__(self, region: str = 'us-west-2'):
        self.cloudwatch = boto3.client('cloudwatch', region_name=region)
        self.logs = boto3.client('logs', region_name=region)
        self.sns = boto3.client('sns', region_name=region)
        self.dynamodb = boto3.resource('dynamodb', region_name=region)
        self.region = region
        
        # Initialize SLO tracking table
        self.slo_table = self.dynamodb.Table('SLOTracking')
    
    @tracer.capture_method
    def track_sli(self, sli: SLI) -> Dict[str, Any]:
        """
        Track Service Level Indicator and evaluate against SLOs
        """
        logger.info(f"Tracking SLI for {sli.service}: {sli.metric_type.value} = {sli.value}")
        
        try:
            # Store SLI measurement
            self._store_sli_measurement(sli)
            
            # Update real-time metrics
            self._publish_sli_metrics(sli)
            
            # Evaluate SLO compliance
            slo_status = self._evaluate_slo_compliance(sli)
            
            # Calculate error budget burn rate
            error_budget = self._calculate_error_budget(sli.service, sli.metric_type)
            
            # Check for SLO violations and alert if necessary
            if error_budget.health_status in ['WARNING', 'CRITICAL']:
                self._trigger_slo_alert(sli, error_budget, slo_status)
            
            return {
                'sli_recorded': True,
                'slo_status': slo_status,
                'error_budget': error_budget.__dict__,
                'alert_triggered': error_budget.health_status in ['WARNING', 'CRITICAL']
            }
            
        except Exception as e:
            logger.error(f"Failed to track SLI: {str(e)}")
            raise
    
    def _store_sli_measurement(self, sli: SLI):
        """Store SLI measurement in DynamoDB"""
        try:
            self.slo_table.put_item(
                Item={
                    'service_metric': f"{sli.service}#{sli.metric_type.value}",
                    'timestamp': int(sli.timestamp.timestamp()),
                    'value': str(sli.value),
                    'target': str(sli.target),
                    'is_good': sli.is_good,
                    'metadata': sli.metadata,
                    'ttl': int((sli.timestamp + timedelta(days=90)).timestamp())
                }
            )
        except Exception as e:
            logger.error(f"Failed to store SLI measurement: {str(e)}")
    
    def _publish_sli_metrics(self, sli: SLI):
        """Publish SLI as CloudWatch custom metrics"""
        try:
            metric_data = [
                {
                    'MetricName': f'{sli.metric_type.value}_value',
                    'Value': sli.value,
                    'Unit': 'None',
                    'Dimensions': [
                        {'Name': 'Service', 'Value': sli.service},
                        {'Name': 'MetricType', 'Value': sli.metric_type.value}
                    ],
                    'Timestamp': sli.timestamp
                },
                {
                    'MetricName': f'{sli.metric_type.value}_compliance',
                    'Value': 1 if sli.is_good else 0,
                    'Unit': 'None',
                    'Dimensions': [
                        {'Name': 'Service', 'Value': sli.service},
                        {'Name': 'MetricType', 'Value': sli.metric_type.value}
                    ],
                    'Timestamp': sli.timestamp
                }
            ]
            
            self.cloudwatch.put_metric_data(
                Namespace='SRE/SLI',
                MetricData=metric_data
            )
            
        except Exception as e:
            logger.error(f"Failed to publish SLI metrics: {str(e)}")
    
    def _evaluate_slo_compliance(self, sli: SLI) -> Dict[str, Any]:
        """Evaluate current SLO compliance"""
        try:
            # Get SLO configuration (would typically come from configuration store)
            slo_config = self._get_slo_config(sli.service, sli.metric_type)
            
            # Calculate compliance over measurement window
            end_time = sli.timestamp
            start_time = end_time - timedelta(days=slo_config['measurement_window_days'])
            
            compliance_rate = self._calculate_compliance_rate(
                sli.service, 
                sli.metric_type, 
                start_time, 
                end_time
            )
            
            is_compliant = compliance_rate >= slo_config['target_percentage']
            margin = compliance_rate - slo_config['target_percentage']
            
            return {
                'slo_name': slo_config['name'],
                'target_percentage': slo_config['target_percentage'],
                'current_compliance': compliance_rate,
                'is_compliant': is_compliant,
                'margin': margin,
                'measurement_window_days': slo_config['measurement_window_days']
            }
            
        except Exception as e:
            logger.error(f"Failed to evaluate SLO compliance: {str(e)}")
            return {}
    
    def _calculate_error_budget(self, service: str, metric_type: ServiceLevel) -> ErrorBudget:
        """Calculate error budget consumption and burn rate"""
        try:
            slo_config = self._get_slo_config(service, metric_type)
            
            # Calculate error budget for 30-day window
            end_time = datetime.now()
            start_time = end_time - timedelta(days=30)
            
            # Get total number of measurements
            total_measurements = self._get_measurement_count(service, metric_type, start_time, end_time)
            
            # Get number of good measurements
            good_measurements = self._get_good_measurement_count(service, metric_type, start_time, end_time)
            
            if total_measurements == 0:
                return ErrorBudget(
                    slo_name=slo_config['name'],
                    total_budget=100.0,
                    consumed_budget=0.0,
                    remaining_budget=100.0,
                    current_burn_rate=0.0,
                    time_to_exhaustion_hours=None,
                    health_status='HEALTHY'
                )
            
            # Calculate current reliability
            current_reliability = (good_measurements / total_measurements) * 100
            
            # Calculate error budget consumption
            target_reliability = slo_config['target_percentage']
            error_budget_allowance = 100 - target_reliability
            error_budget_consumed = max(0, target_reliability - current_reliability)
            remaining_budget = max(0, error_budget_allowance - error_budget_consumed)
            
            # Calculate burn rate (last 1 hour vs last 24 hours)
            current_burn_rate = self._calculate_burn_rate(service, metric_type)
            
            # Calculate time to exhaustion
            if current_burn_rate > 0:
                time_to_exhaustion_hours = remaining_budget / current_burn_rate
            else:
                time_to_exhaustion_hours = None
            
            # Determine health status
            health_status = self._determine_error_budget_health(
                remaining_budget, error_budget_allowance, current_burn_rate, time_to_exhaustion_hours
            )
            
            return ErrorBudget(
                slo_name=slo_config['name'],
                total_budget=error_budget_allowance,
                consumed_budget=error_budget_consumed,
                remaining_budget=remaining_budget,
                current_burn_rate=current_burn_rate,
                time_to_exhaustion_hours=time_to_exhaustion_hours,
                health_status=health_status
            )
            
        except Exception as e:
            logger.error(f"Failed to calculate error budget: {str(e)}")
            return ErrorBudget("unknown", 0, 0, 0, 0, None, "ERROR")
    
    def _calculate_burn_rate(self, service: str, metric_type: ServiceLevel) -> float:
        """Calculate current error budget burn rate"""
        try:
            # Get measurements from last hour
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=1)
            
            hour_total = self._get_measurement_count(service, metric_type, start_time, end_time)
            hour_good = self._get_good_measurement_count(service, metric_type, start_time, end_time)
            
            if hour_total == 0:
                return 0.0
            
            hour_error_rate = (hour_total - hour_good) / hour_total
            
            # Convert to monthly burn rate percentage
            monthly_burn_rate = hour_error_rate * 24 * 30  # Hours in month
            
            return monthly_burn_rate
            
        except Exception as e:
            logger.error(f"Failed to calculate burn rate: {str(e)}")
            return 0.0
    
    def _determine_error_budget_health(self, remaining_budget: float, total_budget: float, 
                                     burn_rate: float, time_to_exhaustion: Optional[float]) -> str:
        """Determine error budget health status"""
        
        budget_percentage = (remaining_budget / total_budget) * 100 if total_budget > 0 else 100
        
        # Critical: Budget exhausted or will be exhausted within 2 hours
        if budget_percentage <= 5 or (time_to_exhaustion and time_to_exhaustion <= 2):
            return "CRITICAL"
        
        # Warning: Less than 25% budget remaining or will be exhausted within 24 hours
        elif budget_percentage <= 25 or (time_to_exhaustion and time_to_exhaustion <= 24):
            return "WARNING"
        
        # Caution: High burn rate detected
        elif burn_rate > 5.0:  # Burning more than 5% per hour
            return "CAUTION"
        
        else:
            return "HEALTHY"
    
    def _get_slo_config(self, service: str, metric_type: ServiceLevel) -> Dict:
        """Get SLO configuration for service and metric type"""
        # This would typically come from a configuration store
        # For demo purposes, using default configurations
        default_configs = {
            ServiceLevel.AVAILABILITY: {
                'name': f"{service}_availability_slo",
                'target_percentage': 99.9,
                'measurement_window_days': 30,
                'alert_threshold_percentage': 1.0
            },
            ServiceLevel.LATENCY: {
                'name': f"{service}_latency_slo",
                'target_percentage': 95.0,  # 95% of requests under threshold
                'measurement_window_days': 30,
                'alert_threshold_percentage': 1.0
            },
            ServiceLevel.ERROR_RATE: {
                'name': f"{service}_error_rate_slo",
                'target_percentage': 99.5,  # 99.5% success rate
                'measurement_window_days': 30,
                'alert_threshold_percentage': 1.0
            }
        }
        
        return default_configs.get(metric_type, {
            'name': f"{service}_{metric_type.value}_slo",
            'target_percentage': 99.0,
            'measurement_window_days': 30,
            'alert_threshold_percentage': 1.0
        })
    
    def _calculate_compliance_rate(self, service: str, metric_type: ServiceLevel, 
                                 start_time: datetime, end_time: datetime) -> float:
        """Calculate SLO compliance rate over time window"""
        try:
            total_measurements = self._get_measurement_count(service, metric_type, start_time, end_time)
            good_measurements = self._get_good_measurement_count(service, metric_type, start_time, end_time)
            
            if total_measurements == 0:
                return 100.0  # No data means perfect compliance
            
            return (good_measurements / total_measurements) * 100
            
        except Exception as e:
            logger.error(f"Failed to calculate compliance rate: {str(e)}")
            return 0.0
    
    def _get_measurement_count(self, service: str, metric_type: ServiceLevel, 
                             start_time: datetime, end_time: datetime) -> int:
        """Get total measurement count from DynamoDB"""
        try:
            response = self.slo_table.query(
                KeyConditionExpression='service_metric = :sm AND #ts BETWEEN :start AND :end',
                ExpressionAttributeNames={'#ts': 'timestamp'},
                ExpressionAttributeValues={
                    ':sm': f"{service}#{metric_type.value}",
                    ':start': int(start_time.timestamp()),
                    ':end': int(end_time.timestamp())
                },
                Select='COUNT'
            )
            return response['Count']
        except Exception as e:
            logger.error(f"Failed to get measurement count: {str(e)}")
            return 0
    
    def _get_good_measurement_count(self, service: str, metric_type: ServiceLevel, 
                                  start_time: datetime, end_time: datetime) -> int:
        """Get good measurement count from DynamoDB"""
        try:
            response = self.slo_table.query(
                KeyConditionExpression='service_metric = :sm AND #ts BETWEEN :start AND :end',
                FilterExpression='is_good = :good',
                ExpressionAttributeNames={'#ts': 'timestamp'},
                ExpressionAttributeValues={
                    ':sm': f"{service}#{metric_type.value}",
                    ':start': int(start_time.timestamp()),
                    ':end': int(end_time.timestamp()),
                    ':good': True
                },
                Select='COUNT'
            )
            return response['Count']
        except Exception as e:
            logger.error(f"Failed to get good measurement count: {str(e)}")
            return 0
    
    def _trigger_slo_alert(self, sli: SLI, error_budget: ErrorBudget, slo_status: Dict):
        """Trigger SLO violation alert"""
        try:
            severity = AlertSeverity.CRITICAL if error_budget.health_status == "CRITICAL" else AlertSeverity.HIGH
            
            alert_message = {
                'service': sli.service,
                'metric_type': sli.metric_type.value,
                'severity': severity.value,
                'error_budget_status': error_budget.health_status,
                'remaining_budget_percentage': (error_budget.remaining_budget / error_budget.total_budget) * 100,
                'current_burn_rate': error_budget.current_burn_rate,
                'time_to_exhaustion_hours': error_budget.time_to_exhaustion_hours,
                'slo_compliance': slo_status.get('current_compliance', 0),
                'slo_target': slo_status.get('target_percentage', 0),
                'timestamp': sli.timestamp.isoformat()
            }
            
            # Send to SNS topic
            self.sns.publish(
                TopicArn=f"arn:aws:sns:{self.region}:123456789012:slo-alerts",
                Message=json.dumps(alert_message, indent=2),
                Subject=f"SLO Alert: {sli.service} {sli.metric_type.value} - {severity.value.upper()}"
            )
            
            logger.warning(f"SLO alert triggered for {sli.service}: {alert_message}")
            
        except Exception as e:
            logger.error(f"Failed to trigger SLO alert: {str(e)}")

class AdvancedMetricsCollector:
    """
    Advanced metrics collection and analysis for observability
    """
    
    def __init__(self, region: str = 'us-west-2'):
        self.cloudwatch = boto3.client('cloudwatch', region_name=region)
        self.logs = boto3.client('logs', region_name=region)
        self.region = region
    
    @tracer.capture_method
    def collect_application_metrics(self, service_name: str, time_window_minutes: int = 5) -> Dict[str, Any]:
        """
        Collect comprehensive application metrics for SLI calculation
        """
        logger.info(f"Collecting metrics for {service_name} over {time_window_minutes} minutes")
        
        end_time = datetime.now()
        start_time = end_time - timedelta(minutes=time_window_minutes)
        
        try:
            metrics = {}
            
            # Collect ALB metrics
            alb_metrics = self._collect_alb_metrics(service_name, start_time, end_time)
            metrics.update(alb_metrics)
            
            # Collect ECS/EKS metrics
            container_metrics = self._collect_container_metrics(service_name, start_time, end_time)
            metrics.update(container_metrics)
            
            # Collect database metrics
            db_metrics = self._collect_database_metrics(service_name, start_time, end_time)
            metrics.update(db_metrics)
            
            # Collect custom application metrics
            app_metrics = self._collect_custom_metrics(service_name, start_time, end_time)
            metrics.update(app_metrics)
            
            # Calculate derived SLI metrics
            sli_metrics = self._calculate_sli_metrics(metrics)
            
            return {
                'service': service_name,
                'time_window_minutes': time_window_minutes,
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'raw_metrics': metrics,
                'sli_metrics': sli_metrics
            }
            
        except Exception as e:
            logger.error(f"Failed to collect application metrics: {str(e)}")
            raise
    
    def _collect_alb_metrics(self, service_name: str, start_time: datetime, end_time: datetime) -> Dict[str, float]:
        """Collect Application Load Balancer metrics"""
        try:
            metric_queries = [
                {
                    'Id': 'request_count',
                    'MetricStat': {
                        'Metric': {
                            'Namespace': 'AWS/ApplicationELB',
                            'MetricName': 'RequestCount',
                            'Dimensions': [
                                {'Name': 'LoadBalancer', 'Value': f'app/{service_name}/*'}
                            ]
                        },
                        'Period': 300,
                        'Stat': 'Sum'
                    }
                },
                {
                    'Id': 'target_response_time',
                    'MetricStat': {
                        'Metric': {
                            'Namespace': 'AWS/ApplicationELB',
                            'MetricName': 'TargetResponseTime',
                            'Dimensions': [
                                {'Name': 'LoadBalancer', 'Value': f'app/{service_name}/*'}
                            ]
                        },
                        'Period': 300,
                        'Stat': 'Average'
                    }
                },
                {
                    'Id': 'http_5xx_count',
                    'MetricStat': {
                        'Metric': {
                            'Namespace': 'AWS/ApplicationELB',
                            'MetricName': 'HTTPCode_Target_5XX_Count',
                            'Dimensions': [
                                {'Name': 'LoadBalancer', 'Value': f'app/{service_name}/*'}
                            ]
                        },
                        'Period': 300,
                        'Stat': 'Sum'
                    }
                },
                {
                    'Id': 'http_4xx_count',
                    'MetricStat': {
                        'Metric': {
                            'Namespace': 'AWS/ApplicationELB',
                            'MetricName': 'HTTPCode_Target_4XX_Count',
                            'Dimensions': [
                                {'Name': 'LoadBalancer', 'Value': f'app/{service_name}/*'}
                            ]
                        },
                        'Period': 300,
                        'Stat': 'Sum'
                    }
                }
            ]
            
            response = self.cloudwatch.get_metric_data(
                MetricDataQueries=metric_queries,
                StartTime=start_time,
                EndTime=end_time
            )
            
            metrics = {}
            for result in response['MetricDataResults']:
                if result['Values']:
                    metrics[f"alb_{result['Id']}"] = statistics.mean(result['Values'])
                else:
                    metrics[f"alb_{result['Id']}"] = 0.0
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to collect ALB metrics: {str(e)}")
            return {}
    
    def _collect_container_metrics(self, service_name: str, start_time: datetime, end_time: datetime) -> Dict[str, float]:
        """Collect container (ECS/EKS) metrics"""
        try:
            # Try ECS metrics first
            ecs_metrics = self._get_ecs_metrics(service_name, start_time, end_time)
            if ecs_metrics:
                return ecs_metrics
            
            # Fallback to EKS metrics
            eks_metrics = self._get_eks_metrics(service_name, start_time, end_time)
            return eks_metrics
            
        except Exception as e:
            logger.error(f"Failed to collect container metrics: {str(e)}")
            return {}
    
    def _get_ecs_metrics(self, service_name: str, start_time: datetime, end_time: datetime) -> Dict[str, float]:
        """Get ECS service metrics"""
        try:
            metric_queries = [
                {
                    'Id': 'cpu_utilization',
                    'MetricStat': {
                        'Metric': {
                            'Namespace': 'AWS/ECS',
                            'MetricName': 'CPUUtilization',
                            'Dimensions': [
                                {'Name': 'ServiceName', 'Value': service_name}
                            ]
                        },
                        'Period': 300,
                        'Stat': 'Average'
                    }
                },
                {
                    'Id': 'memory_utilization',
                    'MetricStat': {
                        'Metric': {
                            'Namespace': 'AWS/ECS',
                            'MetricName': 'MemoryUtilization',
                            'Dimensions': [
                                {'Name': 'ServiceName', 'Value': service_name}
                            ]
                        },
                        'Period': 300,
                        'Stat': 'Average'
                    }
                }
            ]
            
            response = self.cloudwatch.get_metric_data(
                MetricDataQueries=metric_queries,
                StartTime=start_time,
                EndTime=end_time
            )
            
            metrics = {}
            for result in response['MetricDataResults']:
                if result['Values']:
                    metrics[f"ecs_{result['Id']}"] = statistics.mean(result['Values'])
                else:
                    metrics[f"ecs_{result['Id']}"] = 0.0
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to get ECS metrics: {str(e)}")
            return {}
    
    def _get_eks_metrics(self, service_name: str, start_time: datetime, end_time: datetime) -> Dict[str, float]:
        """Get EKS service metrics"""
        try:
            # EKS metrics would come from Container Insights
            metric_queries = [
                {
                    'Id': 'pod_cpu',
                    'MetricStat': {
                        'Metric': {
                            'Namespace': 'ContainerInsights',
                            'MetricName': 'pod_cpu_utilization',
                            'Dimensions': [
                                {'Name': 'Service', 'Value': service_name}
                            ]
                        },
                        'Period': 300,
                        'Stat': 'Average'
                    }
                },
                {
                    'Id': 'pod_memory',
                    'MetricStat': {
                        'Metric': {
                            'Namespace': 'ContainerInsights',
                            'MetricName': 'pod_memory_utilization',
                            'Dimensions': [
                                {'Name': 'Service', 'Value': service_name}
                            ]
                        },
                        'Period': 300,
                        'Stat': 'Average'
                    }
                }
            ]
            
            response = self.cloudwatch.get_metric_data(
                MetricDataQueries=metric_queries,
                StartTime=start_time,
                EndTime=end_time
            )
            
            metrics = {}
            for result in response['MetricDataResults']:
                if result['Values']:
                    metrics[f"eks_{result['Id']}"] = statistics.mean(result['Values'])
                else:
                    metrics[f"eks_{result['Id']}"] = 0.0
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to get EKS metrics: {str(e)}")
            return {}
    
    def _collect_database_metrics(self, service_name: str, start_time: datetime, end_time: datetime) -> Dict[str, float]:
        """Collect database performance metrics"""
        try:
            # Assume RDS instance named after service
            metric_queries = [
                {
                    'Id': 'db_cpu',
                    'MetricStat': {
                        'Metric': {
                            'Namespace': 'AWS/RDS',
                            'MetricName': 'CPUUtilization',
                            'Dimensions': [
                                {'Name': 'DBInstanceIdentifier', 'Value': f'{service_name}-db'}
                            ]
                        },
                        'Period': 300,
                        'Stat': 'Average'
                    }
                },
                {
                    'Id': 'db_connections',
                    'MetricStat': {
                        'Metric': {
                            'Namespace': 'AWS/RDS',
                            'MetricName': 'DatabaseConnections',
                            'Dimensions': [
                                {'Name': 'DBInstanceIdentifier', 'Value': f'{service_name}-db'}
                            ]
                        },
                        'Period': 300,
                        'Stat': 'Average'
                    }
                },
                {
                    'Id': 'read_latency',
                    'MetricStat': {
                        'Metric': {
                            'Namespace': 'AWS/RDS',
                            'MetricName': 'ReadLatency',
                            'Dimensions': [
                                {'Name': 'DBInstanceIdentifier', 'Value': f'{service_name}-db'}
                            ]
                        },
                        'Period': 300,
                        'Stat': 'Average'
                    }
                }
            ]
            
            response = self.cloudwatch.get_metric_data(
                MetricDataQueries=metric_queries,
                StartTime=start_time,
                EndTime=end_time
            )
            
            metrics = {}
            for result in response['MetricDataResults']:
                if result['Values']:
                    metrics[f"db_{result['Id']}"] = statistics.mean(result['Values'])
                else:
                    metrics[f"db_{result['Id']}"] = 0.0
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to collect database metrics: {str(e)}")
            return {}
    
    def _collect_custom_metrics(self, service_name: str, start_time: datetime, end_time: datetime) -> Dict[str, float]:
        """Collect custom application metrics"""
        try:
            metric_queries = [
                {
                    'Id': 'business_transactions',
                    'MetricStat': {
                        'Metric': {
                            'Namespace': f'Custom/{service_name}',
                            'MetricName': 'BusinessTransactions',
                            'Dimensions': [
                                {'Name': 'Service', 'Value': service_name}
                            ]
                        },
                        'Period': 300,
                        'Stat': 'Sum'
                    }
                },
                {
                    'Id': 'user_sessions',
                    'MetricStat': {
                        'Metric': {
                            'Namespace': f'Custom/{service_name}',
                            'MetricName': 'ActiveUserSessions',
                            'Dimensions': [
                                {'Name': 'Service', 'Value': service_name}
                            ]
                        },
                        'Period': 300,
                        'Stat': 'Average'
                    }
                }
            ]
            
            response = self.cloudwatch.get_metric_data(
                MetricDataQueries=metric_queries,
                StartTime=start_time,
                EndTime=end_time
            )
            
            metrics = {}
            for result in response['MetricDataResults']:
                if result['Values']:
                    metrics[f"custom_{result['Id']}"] = statistics.mean(result['Values'])
                else:
                    metrics[f"custom_{result['Id']}"] = 0.0
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to collect custom metrics: {str(e)}")
            return {}
    
    def _calculate_sli_metrics(self, raw_metrics: Dict[str, float]) -> Dict[str, Any]:
        """Calculate SLI metrics from raw metrics"""
        try:
            sli_metrics = {}
            
            # Calculate availability SLI
            total_requests = raw_metrics.get('alb_request_count', 0)
            error_5xx = raw_metrics.get('alb_http_5xx_count', 0)
            
            if total_requests > 0:
                availability_percentage = ((total_requests - error_5xx) / total_requests) * 100
                sli_metrics['availability'] = {
                    'value': availability_percentage,
                    'target': 99.9,
                    'is_good': availability_percentage >= 99.9,
                    'measurement_type': 'percentage'
                }
            
            # Calculate latency SLI (assuming 500ms threshold)
            response_time = raw_metrics.get('alb_target_response_time', 0)
            latency_threshold_ms = 500
            
            sli_metrics['latency'] = {
                'value': response_time * 1000,  # Convert to milliseconds
                'target': latency_threshold_ms,
                'is_good': (response_time * 1000) <= latency_threshold_ms,
                'measurement_type': 'milliseconds'
            }
            
            # Calculate error rate SLI
            total_errors = raw_metrics.get('alb_http_4xx_count', 0) + error_5xx
            if total_requests > 0:
                error_rate_percentage = (total_errors / total_requests) * 100
                sli_metrics['error_rate'] = {
                    'value': 100 - error_rate_percentage,  # Success rate
                    'target': 99.5,
                    'is_good': (100 - error_rate_percentage) >= 99.5,
                    'measurement_type': 'percentage'
                }
            
            return sli_metrics
            
        except Exception as e:
            logger.error(f"Failed to calculate SLI metrics: {str(e)}")
            return {}

# Example usage and integration
def main():
    """Example usage of advanced observability framework"""
    
    # Initialize components
    sre_engine = SREObservabilityEngine()
    metrics_collector = AdvancedMetricsCollector()
    
    # Collect application metrics
    service_name = "user-api"
    raw_metrics = metrics_collector.collect_application_metrics(service_name, time_window_minutes=5)
    
    print(f"Collected metrics for {service_name}:")
    print(json.dumps(raw_metrics, indent=2, default=str))
    
    # Track SLIs and evaluate SLOs
    current_time = datetime.now()
    
    for sli_name, sli_data in raw_metrics['sli_metrics'].items():
        if sli_name == 'availability':
            metric_type = ServiceLevel.AVAILABILITY
        elif sli_name == 'latency':
            metric_type = ServiceLevel.LATENCY
        elif sli_name == 'error_rate':
            metric_type = ServiceLevel.ERROR_RATE
        else:
            continue
        
        sli = SLI(
            timestamp=current_time,
            service=service_name,
            metric_type=metric_type,
            value=sli_data['value'],
            target=sli_data['target'],
            is_good=sli_data['is_good'],
            metadata=raw_metrics['raw_metrics']
        )
        
        # Track SLI and get SLO status
        result = sre_engine.track_sli(sli)
        
        print(f"\nSLI Tracking Result for {sli_name}:")
        print(json.dumps(result, indent=2, default=str))

if __name__ == "__main__":
    main()
```

### Advanced Distributed Tracing and Performance Analysis

#### OpenTelemetry Integration with CloudWatch
```python
# distributed_tracing.py - Advanced distributed tracing with OpenTelemetry
import boto3
import json
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from opentelemetry import trace, metrics
from opentelemetry.exporter.cloudwatch.traces import CloudWatchSpanExporter
from opentelemetry.exporter.cloudwatch.metrics import CloudWatchMetricsExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.boto3sqs import Boto3SQSInstrumentor
import requests

@dataclass
class TraceAnalysis:
    """Trace analysis results"""
    trace_id: str
    total_duration_ms: float
    span_count: int
    error_count: int
    service_map: Dict[str, List[str]]
    critical_path: List[str]
    bottlenecks: List[Dict[str, Any]]
    recommendations: List[str]

class AdvancedTracingAnalyzer:
    """
    Advanced distributed tracing analysis and optimization
    """
    
    def __init__(self, region: str = 'us-west-2'):
        self.region = region
        self.xray = boto3.client('xray', region_name=region)
        self.cloudwatch = boto3.client('cloudwatch', region_name=region)
        
        # Setup OpenTelemetry
        self._setup_opentelemetry()
    
    def _setup_opentelemetry(self):
        """Setup OpenTelemetry with CloudWatch exporters"""
        
        # Setup tracing
        trace.set_tracer_provider(TracerProvider())
        tracer_provider = trace.get_tracer_provider()
        
        # Add CloudWatch span exporter
        cloudwatch_exporter = CloudWatchSpanExporter(region_name=self.region)
        span_processor = BatchSpanProcessor(cloudwatch_exporter)
        tracer_provider.add_span_processor(span_processor)
        
        # Setup metrics
        metric_reader = PeriodicExportingMetricReader(
            CloudWatchMetricsExporter(region_name=self.region),
            export_interval_millis=30000  # 30 seconds
        )
        metrics.set_meter_provider(MeterProvider(metric_readers=[metric_reader]))
        
        # Auto-instrument popular libraries
        RequestsInstrumentor().instrument()
        Boto3SQSInstrumentor().instrument()
        
        self.tracer = trace.get_tracer(__name__)
        self.meter = metrics.get_meter(__name__)
        
        # Create custom metrics
        self.request_duration = self.meter.create_histogram(
            name="request_duration_ms",
            description="Request duration in milliseconds",
            unit="ms"
        )
        
        self.request_counter = self.meter.create_counter(
            name="requests_total",
            description="Total number of requests"
        )
    
    def analyze_trace(self, trace_id: str) -> TraceAnalysis:
        """
        Comprehensive analysis of a distributed trace
        """
        try:
            # Get trace details from X-Ray
            trace_details = self._get_trace_details(trace_id)
            
            if not trace_details:
                raise ValueError(f"Trace {trace_id} not found")
            
            # Analyze trace structure
            spans = self._parse_trace_spans(trace_details)
            service_map = self._build_service_map(spans)
            critical_path = self._find_critical_path(spans)
            bottlenecks = self._identify_bottlenecks(spans)
            
            # Calculate metrics
            total_duration = self._calculate_total_duration(spans)
            error_count = self._count_errors(spans)
            
            # Generate recommendations
            recommendations = self._generate_performance_recommendations(spans, bottlenecks)
            
            return TraceAnalysis(
                trace_id=trace_id,
                total_duration_ms=total_duration,
                span_count=len(spans),
                error_count=error_count,
                service_map=service_map,
                critical_path=critical_path,
                bottlenecks=bottlenecks,
                recommendations=recommendations
            )
            
        except Exception as e:
            print(f"Failed to analyze trace {trace_id}: {str(e)}")
            raise
    
    def _get_trace_details(self, trace_id: str) -> Optional[Dict]:
        """Get trace details from AWS X-Ray"""
        try:
            response = self.xray.get_trace_summaries(
                TraceIds=[trace_id]
            )
            
            if not response['TraceSummaries']:
                return None
            
            # Get full trace details
            trace_response = self.xray.batch_get_traces(
                TraceIds=[trace_id]
            )
            
            return trace_response['Traces'][0] if trace_response['Traces'] else None
            
        except Exception as e:
            print(f"Failed to get trace details: {str(e)}")
            return None
    
    def _parse_trace_spans(self, trace_details: Dict) -> List[Dict]:
        """Parse spans from trace details"""
        spans = []
        
        for segment in trace_details.get('Segments', []):
            segment_doc = json.loads(segment['Document'])
            
            # Add root segment as span
            spans.append({
                'id': segment_doc['id'],
                'name': segment_doc.get('name', 'unknown'),
                'service': segment_doc.get('service', {}).get('name', 'unknown'),
                'start_time': segment_doc.get('start_time', 0),
                'end_time': segment_doc.get('end_time', 0),
                'duration': (segment_doc.get('end_time', 0) - segment_doc.get('start_time', 0)) * 1000,  # Convert to ms
                'error': segment_doc.get('error', False),
                'fault': segment_doc.get('fault', False),
                'throttle': segment_doc.get('throttle', False),
                'http': segment_doc.get('http', {}),
                'aws': segment_doc.get('aws', {}),
                'subsegments': segment_doc.get('subsegments', [])
            })
            
            # Add subsegments
            for subsegment in segment_doc.get('subsegments', []):
                spans.append({
                    'id': subsegment['id'],
                    'name': subsegment.get('name', 'unknown'),
                    'service': subsegment.get('namespace', 'unknown'),
                    'start_time': subsegment.get('start_time', 0),
                    'end_time': subsegment.get('end_time', 0),
                    'duration': (subsegment.get('end_time', 0) - subsegment.get('start_time', 0)) * 1000,
                    'error': subsegment.get('error', False),
                    'fault': subsegment.get('fault', False),
                    'throttle': subsegment.get('throttle', False),
                    'parent_id': segment_doc['id'],
                    'http': subsegment.get('http', {}),
                    'aws': subsegment.get('aws', {})
                })
        
        return spans
    
    def _build_service_map(self, spans: List[Dict]) -> Dict[str, List[str]]:
        """Build service dependency map"""
        service_map = {}
        
        for span in spans:
            service = span['service']
            if service not in service_map:
                service_map[service] = []
            
            # Find downstream services
            for other_span in spans:
                if (other_span.get('parent_id') == span['id'] and 
                    other_span['service'] != service and 
                    other_span['service'] not in service_map[service]):
                    service_map[service].append(other_span['service'])
        
        return service_map
    
    def _find_critical_path(self, spans: List[Dict]) -> List[str]:
        """Find the critical path through the trace"""
        # Sort spans by start time
        sorted_spans = sorted(spans, key=lambda x: x['start_time'])
        
        critical_path = []
        current_span = sorted_spans[0] if sorted_spans else None
        
        while current_span:
            critical_path.append(f"{current_span['service']}::{current_span['name']}")
            
            # Find the longest running child span
            children = [s for s in spans if s.get('parent_id') == current_span['id']]
            current_span = max(children, key=lambda x: x['duration']) if children else None
        
        return critical_path
    
    def _identify_bottlenecks(self, spans: List[Dict]) -> List[Dict[str, Any]]:
        """Identify performance bottlenecks in the trace"""
        bottlenecks = []
        
        # Calculate average duration per service
        service_durations = {}
        for span in spans:
            service = span['service']
            if service not in service_durations:
                service_durations[service] = []
            service_durations[service].append(span['duration'])
        
        # Find spans that are significantly slower than average
        for span in spans:
            service = span['service']
            avg_duration = sum(service_durations[service]) / len(service_durations[service])
            
            if span['duration'] > avg_duration * 2:  # 2x slower than average
                bottlenecks.append({
                    'span_id': span['id'],
                    'service': service,
                    'operation': span['name'],
                    'duration_ms': span['duration'],
                    'avg_duration_ms': avg_duration,
                    'slowdown_factor': span['duration'] / avg_duration,
                    'type': 'duration_anomaly'
                })
            
            # Check for errors
            if span['error'] or span['fault']:
                bottlenecks.append({
                    'span_id': span['id'],
                    'service': service,
                    'operation': span['name'],
                    'duration_ms': span['duration'],
                    'type': 'error',
                    'error': span['error'],
                    'fault': span['fault']
                })
        
        return sorted(bottlenecks, key=lambda x: x.get('duration_ms', 0), reverse=True)
    
    def _calculate_total_duration(self, spans: List[Dict]) -> float:
        """Calculate total trace duration"""
        if not spans:
            return 0.0
        
        min_start = min(span['start_time'] for span in spans)
        max_end = max(span['end_time'] for span in spans)
        
        return (max_end - min_start) * 1000  # Convert to milliseconds
    
    def _count_errors(self, spans: List[Dict]) -> int:
        """Count number of errors in trace"""
        return sum(1 for span in spans if span.get('error') or span.get('fault'))
    
    def _generate_performance_recommendations(self, spans: List[Dict], bottlenecks: List[Dict]) -> List[str]:
        """Generate performance optimization recommendations"""
        recommendations = []
        
        # Analyze bottlenecks
        for bottleneck in bottlenecks[:3]:  # Top 3 bottlenecks
            if bottleneck['type'] == 'duration_anomaly':
                if bottleneck['service'] == 'aws:dynamodb':
                    recommendations.append(f"Optimize DynamoDB queries in {bottleneck['operation']} - consider using indexes or reducing item size")
                elif bottleneck['service'] == 'aws:rds':
                    recommendations.append(f"Optimize database queries in {bottleneck['operation']} - consider query optimization or connection pooling")
                elif 'http' in bottleneck['operation'].lower():
                    recommendations.append(f"Optimize HTTP calls in {bottleneck['operation']} - consider caching or async processing")
                else:
                    recommendations.append(f"Investigate performance issue in {bottleneck['service']}::{bottleneck['operation']}")
        
        # Check for excessive service calls
        service_call_counts = {}
        for span in spans:
            service = span['service']
            service_call_counts[service] = service_call_counts.get(service, 0) + 1
        
        for service, count in service_call_counts.items():
            if count > 10:  # More than 10 calls to same service
                recommendations.append(f"Consider batching calls to {service} to reduce latency (currently {count} calls)")
        
        # Check for errors
        error_services = set(span['service'] for span in spans if span.get('error') or span.get('fault'))
        for service in error_services:
            recommendations.append(f"Investigate errors in {service} service and implement proper error handling")
        
        return recommendations

# Integration with CloudWatch for automated trace analysis
def create_trace_analysis_lambda():
    """
    Lambda function to automatically analyze traces and send alerts
    """
    def lambda_handler(event, context):
        """
        Process X-Ray trace events and perform analysis
        """
        analyzer = AdvancedTracingAnalyzer()
        
        # Process CloudWatch Events from X-Ray
        for record in event.get('Records', []):
            if record.get('source') == 'aws.xray':
                detail = record.get('detail', {})
                trace_id = detail.get('trace-id')
                
                if trace_id:
                    try:
                        # Analyze the trace
                        analysis = analyzer.analyze_trace(trace_id)
                        
                        # Check for performance issues
                        if (analysis.total_duration_ms > 5000 or  # Slower than 5 seconds
                            analysis.error_count > 0 or
                            len(analysis.bottlenecks) > 0):
                            
                            # Send alert
                            alert_message = {
                                'trace_id': trace_id,
                                'total_duration_ms': analysis.total_duration_ms,
                                'error_count': analysis.error_count,
                                'bottleneck_count': len(analysis.bottlenecks),
                                'recommendations': analysis.recommendations[:3],  # Top 3
                                'critical_path': analysis.critical_path
                            }
                            
                            # Publish to SNS
                            sns = boto3.client('sns')
                            sns.publish(
                                TopicArn='arn:aws:sns:us-west-2:123456789012:trace-performance-alerts',
                                Message=json.dumps(alert_message, indent=2),
                                Subject=f'Performance Issue Detected in Trace {trace_id}'
                            )
                    
                    except Exception as e:
                        print(f"Failed to analyze trace {trace_id}: {str(e)}")
        
        return {'statusCode': 200, 'body': json.dumps('Trace analysis completed')}
    
    return lambda_handler

# Example usage
if __name__ == "__main__":
    analyzer = AdvancedTracingAnalyzer()
    
    # Example trace analysis
    trace_id = "1-5e4b1234-5678901234567890abcdef"
    
    try:
        analysis = analyzer.analyze_trace(trace_id)
        
        print(f"Trace Analysis for {trace_id}:")
        print(f"Total Duration: {analysis.total_duration_ms:.2f}ms")
        print(f"Span Count: {analysis.span_count}")
        print(f"Error Count: {analysis.error_count}")
        print(f"Service Map: {analysis.service_map}")
        print(f"Critical Path: {' -> '.join(analysis.critical_path)}")
        print(f"Bottlenecks: {len(analysis.bottlenecks)}")
        
        if analysis.recommendations:
            print("\nRecommendations:")
            for i, rec in enumerate(analysis.recommendations, 1):
                print(f"{i}. {rec}")
                
    except Exception as e:
        print(f"Failed to analyze trace: {str(e)}")
```

This comprehensive enhancement transforms AWS CloudWatch into an enterprise-grade observability platform with advanced SRE practices, comprehensive SLI/SLO tracking, error budget management, sophisticated distributed tracing analysis, and automated performance optimization recommendations.