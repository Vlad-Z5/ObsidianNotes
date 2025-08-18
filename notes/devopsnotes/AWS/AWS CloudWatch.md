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