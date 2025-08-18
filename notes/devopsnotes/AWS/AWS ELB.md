# AWS ELB (Elastic Load Balancing)

> **Service Type:** Load Balancing | **Tier:** Container Services | **Global/Regional:** Regional

## Overview

AWS Elastic Load Balancing (ELB) automatically distributes incoming application traffic across multiple targets such as EC2 instances, containers, IP addresses, and Lambda functions in multiple Availability Zones. ELB provides the high availability, automatic scaling, and robust security needed to make applications fault tolerant.

## DevOps Use Cases

### High Availability Architecture
- **Multi-AZ deployment** with automatic failover between availability zones
- **Health check automation** removing unhealthy instances from load balancing rotation
- **Auto Scaling integration** dynamically adjusting capacity based on demand
- **Blue-green deployments** seamless traffic switching between environments

### Microservices and Container Orchestration
- **Service discovery** dynamic routing to containerized applications
- **Path-based routing** directing traffic to different microservices based on URL patterns
- **Host-based routing** supporting multiple domains on single load balancer
- **Container deployment** integration with ECS and EKS for containerized workloads

### Security and Compliance
- **SSL/TLS termination** centralized certificate management and encryption
- **WAF integration** protecting applications from common web exploits
- **Security groups** network-level access control for load balancers
- **VPC endpoint support** private connectivity without internet gateway

### Performance Optimization
- **Connection draining** graceful handling of in-flight requests during scaling
- **Sticky sessions** maintaining user session affinity when required
- **Cross-zone load balancing** even distribution across all available zones
- **HTTP/2 and WebSocket support** modern protocol optimization

### Monitoring and Operations
- **CloudWatch metrics** comprehensive monitoring of load balancer performance
- **Access logging** detailed request logs for analysis and troubleshooting
- **Request tracing** end-to-end request tracking through X-Amzn-Trace-Id headers
- **Integration with AWS Config** compliance monitoring and configuration drift detection

## Load Balancer Types

### Application Load Balancer (ALB)
- **Layer 7 (HTTP/HTTPS)** application-aware load balancing
- **Advanced routing** host, path, header, and query string-based routing
- **WebSocket and HTTP/2** support for modern web applications
- **Lambda targets** serverless application integration
- **Container native** first-class support for ECS and EKS

### Network Load Balancer (NLB)
- **Layer 4 (TCP/UDP/TLS)** ultra-high performance load balancing
- **Static IP addresses** consistent IP addresses for whitelisting
- **Extreme performance** millions of requests per second with ultra-low latency
- **Preserve source IP** maintain client IP addresses for applications
- **PrivateLink support** secure service exposure across VPCs

### Gateway Load Balancer (GWLB)
- **Layer 3 networking** transparent network gateway and load balancer
- **Virtual appliance deployment** firewalls, intrusion detection, and deep packet inspection
- **Third-party security services** integration with security vendor appliances
- **GENEVE protocol** encapsulation for traffic routing to security appliances

### Classic Load Balancer (CLB)
- **Legacy support** for applications built within EC2-Classic network
- **Layer 4 and 7** basic load balancing capabilities
- **Sticky sessions** support for session affinity
- **Migration path** to ALB or NLB for enhanced features

## Core Features

### Health Checking
- **Active health checks** regular probes to determine target health
- **Passive health checks** monitoring actual request success/failure rates
- **Custom health check paths** application-specific health endpoints
- **Configurable intervals** adjustable check frequency and timeout values

### Traffic Distribution
- **Round robin** default even distribution algorithm
- **Least outstanding requests** intelligent routing based on active connections
- **Weighted routing** proportional traffic distribution with target weights
- **Zone awareness** balanced distribution across availability zones

### Security Features
- **SSL/TLS termination** certificate management and encryption handling
- **Security groups** network access control at load balancer level
- **AWS WAF integration** web application firewall protection
- **Access control** integration with AWS IdentityCenter and OIDC providers

### Integration Capabilities
- **Auto Scaling Groups** automatic target registration and deregistration
- **ECS services** native container orchestration support
- **EKS clusters** Kubernetes ingress controller integration
- **Lambda functions** serverless application load balancing

## Practical CLI Examples

### Application Load Balancer Management

```bash
# Create Application Load Balancer
aws elbv2 create-load-balancer \
  --name my-application-lb \
  --subnets subnet-12345678 subnet-87654321 \
  --security-groups sg-12345678 \
  --scheme internet-facing \
  --type application \
  --ip-address-type ipv4 \
  --tags Key=Environment,Value=Production Key=Application,Value=WebApp

# Create target group
aws elbv2 create-target-group \
  --name web-servers-tg \
  --protocol HTTP \
  --port 80 \
  --vpc-id vpc-12345678 \
  --health-check-protocol HTTP \
  --health-check-path /health \
  --health-check-interval-seconds 30 \
  --health-check-timeout-seconds 5 \
  --healthy-threshold-count 2 \
  --unhealthy-threshold-count 3 \
  --matcher HttpCode=200 \
  --tags Key=Environment,Value=Production

# Register targets
aws elbv2 register-targets \
  --target-group-arn arn:aws:elasticloadbalancing:us-west-2:123456789012:targetgroup/web-servers-tg/1234567890123456 \
  --targets Id=i-12345678,Port=80 Id=i-87654321,Port=80

# Create listener with SSL
aws elbv2 create-listener \
  --load-balancer-arn arn:aws:elasticloadbalancing:us-west-2:123456789012:loadbalancer/app/my-application-lb/1234567890123456 \
  --protocol HTTPS \
  --port 443 \
  --certificates CertificateArn=arn:aws:acm:us-west-2:123456789012:certificate/12345678-1234-1234-1234-123456789012 \
  --default-actions Type=forward,TargetGroupArn=arn:aws:elasticloadbalancing:us-west-2:123456789012:targetgroup/web-servers-tg/1234567890123456

# Create advanced routing rule
aws elbv2 create-rule \
  --listener-arn arn:aws:elasticloadbalancing:us-west-2:123456789012:listener/app/my-application-lb/1234567890123456/1234567890123456 \
  --priority 100 \
  --conditions Field=path-pattern,Values="/api/*" \
  --actions Type=forward,TargetGroupArn=arn:aws:elasticloadbalancing:us-west-2:123456789012:targetgroup/api-servers-tg/1234567890123456
```

### Network Load Balancer Management

```bash
# Create Network Load Balancer
aws elbv2 create-load-balancer \
  --name my-network-lb \
  --subnets subnet-12345678 subnet-87654321 \
  --scheme internet-facing \
  --type network \
  --ip-address-type ipv4 \
  --tags Key=Environment,Value=Production Key=Service,Value=Database

# Create target group for TCP traffic
aws elbv2 create-target-group \
  --name database-tg \
  --protocol TCP \
  --port 5432 \
  --vpc-id vpc-12345678 \
  --health-check-protocol TCP \
  --health-check-interval-seconds 30 \
  --health-check-timeout-seconds 10 \
  --healthy-threshold-count 2 \
  --unhealthy-threshold-count 3

# Create TCP listener
aws elbv2 create-listener \
  --load-balancer-arn arn:aws:elasticloadbalancing:us-west-2:123456789012:loadbalancer/net/my-network-lb/1234567890123456 \
  --protocol TCP \
  --port 5432 \
  --default-actions Type=forward,TargetGroupArn=arn:aws:elasticloadbalancing:us-west-2:123456789012:targetgroup/database-tg/1234567890123456
```

### Health Check and Target Management

```bash
# Modify health check settings
aws elbv2 modify-target-group \
  --target-group-arn arn:aws:elasticloadbalancing:us-west-2:123456789012:targetgroup/web-servers-tg/1234567890123456 \
  --health-check-interval-seconds 15 \
  --health-check-timeout-seconds 3 \
  --healthy-threshold-count 2 \
  --unhealthy-threshold-count 2 \
  --health-check-path /health \
  --matcher HttpCode=200,201

# Check target health
aws elbv2 describe-target-health \
  --target-group-arn arn:aws:elasticloadbalancing:us-west-2:123456789012:targetgroup/web-servers-tg/1234567890123456

# Deregister unhealthy targets
aws elbv2 deregister-targets \
  --target-group-arn arn:aws:elasticloadbalancing:us-west-2:123456789012:targetgroup/web-servers-tg/1234567890123456 \
  --targets Id=i-12345678,Port=80

# Get load balancer attributes
aws elbv2 describe-load-balancer-attributes \
  --load-balancer-arn arn:aws:elasticloadbalancing:us-west-2:123456789012:loadbalancer/app/my-application-lb/1234567890123456

# Enable access logs
aws elbv2 modify-load-balancer-attributes \
  --load-balancer-arn arn:aws:elasticloadbalancing:us-west-2:123456789012:loadbalancer/app/my-application-lb/1234567890123456 \
  --attributes Key=access_logs.s3.enabled,Value=true Key=access_logs.s3.bucket,Value=my-lb-access-logs Key=access_logs.s3.prefix,Value=production-alb
```

## DevOps Automation Scripts

### Load Balancer Health Monitor

```python
# lb-health-monitor.py - Monitor load balancer and target health
import boto3
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LoadBalancerHealthMonitor:
    def __init__(self, region_name: str = 'us-west-2'):
        self.elbv2_client = boto3.client('elbv2', region_name=region_name)
        self.cloudwatch_client = boto3.client('cloudwatch', region_name=region_name)
        self.sns_client = boto3.client('sns', region_name=region_name)
        
    def get_all_load_balancers(self) -> List[Dict]:
        """Get all load balancers in the region"""
        
        paginator = self.elbv2_client.get_paginator('describe_load_balancers')
        load_balancers = []
        
        for page in paginator.paginate():
            load_balancers.extend(page['LoadBalancers'])
        
        return load_balancers
    
    def check_load_balancer_health(self, lb_arn: str) -> Dict:
        """Check health of a specific load balancer"""
        
        health_report = {
            'load_balancer_arn': lb_arn,
            'healthy_targets': 0,
            'unhealthy_targets': 0,
            'target_groups': [],
            'overall_status': 'healthy',
            'issues': []
        }
        
        try:
            # Get target groups for this load balancer
            target_groups_response = self.elbv2_client.describe_target_groups(
                LoadBalancerArn=lb_arn
            )
            
            for target_group in target_groups_response['TargetGroups']:
                tg_arn = target_group['TargetGroupArn']
                tg_name = target_group['TargetGroupName']
                
                # Check target health
                health_response = self.elbv2_client.describe_target_health(
                    TargetGroupArn=tg_arn
                )
                
                tg_health = {
                    'name': tg_name,
                    'arn': tg_arn,
                    'healthy_count': 0,
                    'unhealthy_count': 0,
                    'targets': []
                }
                
                for target_health in health_response['TargetHealthDescriptions']:
                    target = target_health['Target']
                    health_state = target_health['TargetHealth']['State']
                    
                    target_info = {
                        'id': target['Id'],
                        'port': target.get('Port', 'N/A'),
                        'state': health_state,
                        'reason': target_health['TargetHealth'].get('Reason', ''),
                        'description': target_health['TargetHealth'].get('Description', '')
                    }
                    
                    tg_health['targets'].append(target_info)
                    
                    if health_state == 'healthy':
                        tg_health['healthy_count'] += 1
                        health_report['healthy_targets'] += 1
                    else:
                        tg_health['unhealthy_count'] += 1
                        health_report['unhealthy_targets'] += 1
                        
                        if health_state in ['unhealthy', 'draining']:
                            health_report['issues'].append(
                                f"Target {target['Id']} in {tg_name} is {health_state}: {target_info['description']}"
                            )
                
                # Check if target group has no healthy targets
                if tg_health['healthy_count'] == 0 and tg_health['unhealthy_count'] > 0:
                    health_report['overall_status'] = 'critical'
                    health_report['issues'].append(f"Target group {tg_name} has no healthy targets")
                elif tg_health['unhealthy_count'] > 0:
                    if health_report['overall_status'] == 'healthy':
                        health_report['overall_status'] = 'warning'
                
                health_report['target_groups'].append(tg_health)
                
        except Exception as e:
            logger.error(f"Error checking health for load balancer {lb_arn}: {e}")
            health_report['overall_status'] = 'error'
            health_report['issues'].append(f"Health check failed: {str(e)}")
        
        return health_report
    
    def get_load_balancer_metrics(self, lb_arn: str, hours: int = 1) -> Dict:
        """Get CloudWatch metrics for load balancer"""
        
        lb_name = lb_arn.split('/')[-3]  # Extract LB name from ARN
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)
        
        metrics = {}
        
        # Define metrics to retrieve
        metric_names = [
            'RequestCount',
            'TargetResponseTime',
            'HTTPCode_Target_2XX_Count',
            'HTTPCode_Target_4XX_Count',
            'HTTPCode_Target_5XX_Count',
            'UnHealthyHostCount',
            'HealthyHostCount'
        ]
        
        for metric_name in metric_names:
            try:
                response = self.cloudwatch_client.get_metric_statistics(
                    Namespace='AWS/ApplicationELB',
                    MetricName=metric_name,
                    Dimensions=[
                        {
                            'Name': 'LoadBalancer',
                            'Value': lb_name
                        }
                    ],
                    StartTime=start_time,
                    EndTime=end_time,
                    Period=300,  # 5 minutes
                    Statistics=['Sum', 'Average', 'Maximum']
                )
                
                if response['Datapoints']:
                    # Get the latest datapoint
                    latest_datapoint = max(response['Datapoints'], key=lambda x: x['Timestamp'])
                    metrics[metric_name] = {
                        'timestamp': latest_datapoint['Timestamp'],
                        'value': latest_datapoint.get('Sum', latest_datapoint.get('Average', latest_datapoint.get('Maximum', 0)))
                    }
                else:
                    metrics[metric_name] = {'value': 0, 'timestamp': None}
                    
            except Exception as e:
                logger.error(f"Error getting metric {metric_name} for {lb_arn}: {e}")
                metrics[metric_name] = {'value': 0, 'timestamp': None, 'error': str(e)}
        
        return metrics
    
    def analyze_performance_trends(self, lb_arn: str) -> Dict:
        """Analyze performance trends and identify issues"""
        
        metrics = self.get_load_balancer_metrics(lb_arn, hours=24)
        analysis = {
            'performance_status': 'good',
            'recommendations': [],
            'alerts': [],
            'metrics_summary': metrics
        }
        
        # Analyze error rates
        total_requests = metrics.get('RequestCount', {}).get('value', 0)
        error_5xx = metrics.get('HTTPCode_Target_5XX_Count', {}).get('value', 0)
        error_4xx = metrics.get('HTTPCode_Target_4XX_Count', {}).get('value', 0)
        
        if total_requests > 0:
            error_rate_5xx = (error_5xx / total_requests) * 100
            error_rate_4xx = (error_4xx / total_requests) * 100
            
            if error_rate_5xx > 5:
                analysis['performance_status'] = 'critical'
                analysis['alerts'].append(f"High 5xx error rate: {error_rate_5xx:.2f}%")
            elif error_rate_5xx > 1:
                analysis['performance_status'] = 'warning'
                analysis['alerts'].append(f"Elevated 5xx error rate: {error_rate_5xx:.2f}%")
            
            if error_rate_4xx > 20:
                analysis['alerts'].append(f"High 4xx error rate: {error_rate_4xx:.2f}%")
        
        # Analyze response time
        response_time = metrics.get('TargetResponseTime', {}).get('value', 0)
        if response_time > 2:  # 2 seconds
            analysis['performance_status'] = 'warning'
            analysis['alerts'].append(f"High response time: {response_time:.2f}s")
            analysis['recommendations'].append("Consider optimizing application performance or scaling targets")
        
        # Analyze healthy host count
        unhealthy_hosts = metrics.get('UnHealthyHostCount', {}).get('value', 0)
        healthy_hosts = metrics.get('HealthyHostCount', {}).get('value', 0)
        
        if unhealthy_hosts > 0:
            if healthy_hosts == 0:
                analysis['performance_status'] = 'critical'
                analysis['alerts'].append("No healthy hosts available")
            else:
                analysis['performance_status'] = 'warning'
                analysis['alerts'].append(f"{unhealthy_hosts} unhealthy hosts detected")
        
        return analysis
    
    def generate_health_report(self, lb_filters: Dict = None) -> Dict:
        """Generate comprehensive health report"""
        
        load_balancers = self.get_all_load_balancers()
        
        # Apply filters if provided
        if lb_filters:
            if 'name_pattern' in lb_filters:
                load_balancers = [lb for lb in load_balancers 
                                if lb_filters['name_pattern'] in lb['LoadBalancerName']]
            if 'environment' in lb_filters:
                # Filter by tags (would need to fetch tags separately)
                pass
        
        report = {
            'generated_at': datetime.utcnow().isoformat(),
            'total_load_balancers': len(load_balancers),
            'summary': {
                'healthy': 0,
                'warning': 0,
                'critical': 0,
                'error': 0
            },
            'load_balancers': []
        }
        
        for lb in load_balancers:
            lb_arn = lb['LoadBalancerArn']
            lb_name = lb['LoadBalancerName']
            
            logger.info(f"Checking health for load balancer: {lb_name}")
            
            # Check health
            health_report = self.check_load_balancer_health(lb_arn)
            
            # Analyze performance
            performance_analysis = self.analyze_performance_trends(lb_arn)
            
            # Combine reports
            lb_report = {
                'name': lb_name,
                'arn': lb_arn,
                'type': lb['Type'],
                'state': lb['State']['Code'],
                'scheme': lb['Scheme'],
                'health': health_report,
                'performance': performance_analysis,
                'overall_status': health_report['overall_status']
            }
            
            # Determine overall status (health takes precedence over performance)
            if health_report['overall_status'] == 'critical' or performance_analysis['performance_status'] == 'critical':
                lb_report['overall_status'] = 'critical'
            elif health_report['overall_status'] == 'warning' or performance_analysis['performance_status'] == 'warning':
                lb_report['overall_status'] = 'warning'
            elif health_report['overall_status'] == 'error':
                lb_report['overall_status'] = 'error'
            else:
                lb_report['overall_status'] = 'healthy'
            
            report['summary'][lb_report['overall_status']] += 1
            report['load_balancers'].append(lb_report)
        
        return report
    
    def send_alert_notifications(self, report: Dict, sns_topic_arn: str):
        """Send alert notifications for critical issues"""
        
        critical_issues = []
        warning_issues = []
        
        for lb in report['load_balancers']:
            if lb['overall_status'] == 'critical':
                critical_issues.append({
                    'name': lb['name'],
                    'issues': lb['health']['issues'] + lb['performance']['alerts']
                })
            elif lb['overall_status'] == 'warning':
                warning_issues.append({
                    'name': lb['name'],
                    'issues': lb['health']['issues'] + lb['performance']['alerts']
                })
        
        if critical_issues or warning_issues:
            message = f"Load Balancer Health Report - {report['generated_at']}\\n\\n"
            
            if critical_issues:
                message += "CRITICAL ISSUES:\\n"
                for issue in critical_issues:
                    message += f"\\n• {issue['name']}:\\n"
                    for detail in issue['issues']:
                        message += f"  - {detail}\\n"
            
            if warning_issues:
                message += "\\nWARNING ISSUES:\\n"
                for issue in warning_issues:
                    message += f"\\n• {issue['name']}:\\n"
                    for detail in issue['issues']:
                        message += f"  - {detail}\\n"
            
            message += f"\\nSummary: {report['summary']}\\n"
            
            try:
                self.sns_client.publish(
                    TopicArn=sns_topic_arn,
                    Message=message,
                    Subject=f"Load Balancer Alert - {len(critical_issues)} Critical, {len(warning_issues)} Warning"
                )
                logger.info("Alert notification sent successfully")
            except Exception as e:
                logger.error(f"Failed to send alert notification: {e}")

def main():
    """Main function for load balancer health monitoring"""
    
    # Initialize monitor
    monitor = LoadBalancerHealthMonitor()
    
    # Generate health report
    print("Generating load balancer health report...")
    report = monitor.generate_health_report()
    
    # Print summary
    print(f"\\nLoad Balancer Health Report - {report['generated_at']}")
    print(f"Total Load Balancers: {report['total_load_balancers']}")
    print(f"Healthy: {report['summary']['healthy']}")
    print(f"Warning: {report['summary']['warning']}")
    print(f"Critical: {report['summary']['critical']}")
    print(f"Error: {report['summary']['error']}")
    
    # Print details for non-healthy load balancers
    for lb in report['load_balancers']:
        if lb['overall_status'] != 'healthy':
            print(f"\\n{lb['name']} ({lb['overall_status'].upper()}):")
            for issue in lb['health']['issues']:
                print(f"  - {issue}")
            for alert in lb['performance']['alerts']:
                print(f"  - {alert}")
    
    # Send notifications if there are issues
    sns_topic_arn = 'arn:aws:sns:us-west-2:123456789012:lb-health-alerts'
    monitor.send_alert_notifications(report, sns_topic_arn)

if __name__ == "__main__":
    main()
```

### Blue-Green Deployment with ALB

```bash
#!/bin/bash
# blue-green-alb-deployment.sh - Blue-green deployment using ALB target groups

APPLICATION_NAME=$1
NEW_VERSION=$2
ENVIRONMENT=${3:-production}

if [ $# -lt 2 ]; then
    echo "Usage: $0 <application-name> <new-version> [environment]"
    exit 1
fi

# Configuration
ALB_ARN="arn:aws:elasticloadbalancing:us-west-2:123456789012:loadbalancer/app/${APPLICATION_NAME}-${ENVIRONMENT}/1234567890123456"
BLUE_TG_NAME="${APPLICATION_NAME}-${ENVIRONMENT}-blue"
GREEN_TG_NAME="${APPLICATION_NAME}-${ENVIRONMENT}-green"
VPC_ID="vpc-12345678"
HEALTH_CHECK_PATH="/health"

echo "Starting blue-green deployment for ${APPLICATION_NAME} v${NEW_VERSION}"

# Get current target group (blue)
CURRENT_TG_ARN=$(aws elbv2 describe-target-groups \
    --names ${BLUE_TG_NAME} \
    --query 'TargetGroups[0].TargetGroupArn' \
    --output text 2>/dev/null)

if [ "$CURRENT_TG_ARN" = "None" ] || [ -z "$CURRENT_TG_ARN" ]; then
    echo "Blue target group not found, creating initial setup..."
    
    # Create blue target group
    BLUE_TG_ARN=$(aws elbv2 create-target-group \
        --name ${BLUE_TG_NAME} \
        --protocol HTTP \
        --port 80 \
        --vpc-id ${VPC_ID} \
        --health-check-path ${HEALTH_CHECK_PATH} \
        --health-check-interval-seconds 30 \
        --health-check-timeout-seconds 5 \
        --healthy-threshold-count 2 \
        --unhealthy-threshold-count 3 \
        --tags Key=Environment,Value=${ENVIRONMENT} Key=Application,Value=${APPLICATION_NAME} \
        --query 'TargetGroups[0].TargetGroupArn' \
        --output text)
    
    echo "Created blue target group: ${BLUE_TG_ARN}"
    CURRENT_TG_ARN=$BLUE_TG_ARN
else
    BLUE_TG_ARN=$CURRENT_TG_ARN
fi

# Create or update green target group
echo "Setting up green environment..."

# Check if green target group exists
GREEN_TG_ARN=$(aws elbv2 describe-target-groups \
    --names ${GREEN_TG_NAME} \
    --query 'TargetGroups[0].TargetGroupArn' \
    --output text 2>/dev/null)

if [ "$GREEN_TG_ARN" = "None" ] || [ -z "$GREEN_TG_ARN" ]; then
    # Create green target group
    GREEN_TG_ARN=$(aws elbv2 create-target-group \
        --name ${GREEN_TG_NAME} \
        --protocol HTTP \
        --port 80 \
        --vpc-id ${VPC_ID} \
        --health-check-path ${HEALTH_CHECK_PATH} \
        --health-check-interval-seconds 30 \
        --health-check-timeout-seconds 5 \
        --healthy-threshold-count 2 \
        --unhealthy-threshold-count 3 \
        --tags Key=Environment,Value=${ENVIRONMENT} Key=Application,Value=${APPLICATION_NAME} \
        --query 'TargetGroups[0].TargetGroupArn' \
        --output text)
    
    echo "Created green target group: ${GREEN_TG_ARN}"
fi

# Deploy new version to green environment
echo "Deploying version ${NEW_VERSION} to green environment..."

# Get current blue instances to replicate the setup
BLUE_TARGETS=$(aws elbv2 describe-target-health \
    --target-group-arn ${BLUE_TG_ARN} \
    --query 'TargetHealthDescriptions[?TargetHealth.State==`healthy`].Target.Id' \
    --output text)

if [ -z "$BLUE_TARGETS" ]; then
    echo "No healthy targets in blue environment. Aborting deployment."
    exit 1
fi

echo "Found healthy blue targets: ${BLUE_TARGETS}"

# Launch new instances for green environment
echo "Launching new instances for green environment..."

# Get the launch template or AMI ID from blue instances
INSTANCE_ID=$(echo $BLUE_TARGETS | cut -d' ' -f1)
INSTANCE_INFO=$(aws ec2 describe-instances --instance-ids $INSTANCE_ID)

AMI_ID=$(echo "$INSTANCE_INFO" | jq -r '.Reservations[0].Instances[0].ImageId')
INSTANCE_TYPE=$(echo "$INSTANCE_INFO" | jq -r '.Reservations[0].Instances[0].InstanceType')
SECURITY_GROUPS=$(echo "$INSTANCE_INFO" | jq -r '.Reservations[0].Instances[0].SecurityGroups[].GroupId' | tr '\n' ' ')
SUBNET_ID=$(echo "$INSTANCE_INFO" | jq -r '.Reservations[0].Instances[0].SubnetId')
KEY_NAME=$(echo "$INSTANCE_INFO" | jq -r '.Reservations[0].Instances[0].KeyName')

# Create user data script for new version deployment
cat > user-data.sh << EOF
#!/bin/bash
yum update -y
yum install -y docker
service docker start
usermod -a -G docker ec2-user

# Pull and run new version
docker pull ${APPLICATION_NAME}:${NEW_VERSION}
docker stop \$(docker ps -q) 2>/dev/null || true
docker run -d -p 80:8080 --name app ${APPLICATION_NAME}:${NEW_VERSION}

# Wait for application to be ready
while ! curl -f http://localhost${HEALTH_CHECK_PATH}; do
    sleep 5
done

echo "Application ${NEW_VERSION} is ready"
EOF

# Launch new instances
GREEN_INSTANCE_IDS=""
for i in {1..2}; do  # Launch 2 instances for redundancy
    INSTANCE_ID=$(aws ec2 run-instances \
        --image-id ${AMI_ID} \
        --count 1 \
        --instance-type ${INSTANCE_TYPE} \
        --key-name ${KEY_NAME} \
        --security-group-ids ${SECURITY_GROUPS} \
        --subnet-id ${SUBNET_ID} \
        --user-data file://user-data.sh \
        --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=${APPLICATION_NAME}-green-${i}},{Key=Environment,Value=${ENVIRONMENT}},{Key=Version,Value=${NEW_VERSION}},{Key=DeploymentType,Value=green}]" \
        --query 'Instances[0].InstanceId' \
        --output text)
    
    GREEN_INSTANCE_IDS="$GREEN_INSTANCE_IDS $INSTANCE_ID"
    echo "Launched green instance: $INSTANCE_ID"
done

# Wait for instances to be running
echo "Waiting for green instances to be running..."
aws ec2 wait instance-running --instance-ids $GREEN_INSTANCE_IDS

# Register green instances with green target group
echo "Registering green instances with target group..."
TARGETS_JSON=""
for instance_id in $GREEN_INSTANCE_IDS; do
    if [ -z "$TARGETS_JSON" ]; then
        TARGETS_JSON="Id=${instance_id},Port=80"
    else
        TARGETS_JSON="${TARGETS_JSON} Id=${instance_id},Port=80"
    fi
done

aws elbv2 register-targets \
    --target-group-arn ${GREEN_TG_ARN} \
    --targets $TARGETS_JSON

# Wait for green targets to be healthy
echo "Waiting for green targets to be healthy..."
HEALTHY_COUNT=0
MAX_WAIT=600  # 10 minutes
WAIT_TIME=0

while [ $HEALTHY_COUNT -lt 2 ] && [ $WAIT_TIME -lt $MAX_WAIT ]; do
    sleep 30
    WAIT_TIME=$((WAIT_TIME + 30))
    
    HEALTHY_COUNT=$(aws elbv2 describe-target-health \
        --target-group-arn ${GREEN_TG_ARN} \
        --query 'length(TargetHealthDescriptions[?TargetHealth.State==`healthy`])' \
        --output text)
    
    echo "Healthy green targets: ${HEALTHY_COUNT}/2"
done

if [ $HEALTHY_COUNT -lt 2 ]; then
    echo "Green environment failed to become healthy. Rolling back..."
    
    # Terminate green instances
    aws ec2 terminate-instances --instance-ids $GREEN_INSTANCE_IDS
    exit 1
fi

echo "Green environment is healthy. Performing traffic switch..."

# Get listener ARN
LISTENER_ARN=$(aws elbv2 describe-listeners \
    --load-balancer-arn ${ALB_ARN} \
    --query 'Listeners[?Port==`80`].ListenerArn' \
    --output text)

if [ -z "$LISTENER_ARN" ]; then
    LISTENER_ARN=$(aws elbv2 describe-listeners \
        --load-balancer-arn ${ALB_ARN} \
        --query 'Listeners[?Port==`443`].ListenerArn' \
        --output text)
fi

# Switch traffic to green
echo "Switching traffic to green environment..."
aws elbv2 modify-listener \
    --listener-arn ${LISTENER_ARN} \
    --default-actions Type=forward,TargetGroupArn=${GREEN_TG_ARN}

echo "Traffic switched to green environment"

# Validation period
echo "Starting validation period (5 minutes)..."
sleep 300

# Check green environment health after traffic switch
FINAL_HEALTH_CHECK=$(aws elbv2 describe-target-health \
    --target-group-arn ${GREEN_TG_ARN} \
    --query 'length(TargetHealthDescriptions[?TargetHealth.State==`healthy`])' \
    --output text)

if [ $FINAL_HEALTH_CHECK -lt 2 ]; then
    echo "Green environment became unhealthy after traffic switch. Rolling back..."
    
    # Switch back to blue
    aws elbv2 modify-listener \
        --listener-arn ${LISTENER_ARN} \
        --default-actions Type=forward,TargetGroupArn=${BLUE_TG_ARN}
    
    echo "Traffic switched back to blue environment"
    
    # Terminate green instances
    aws ec2 terminate-instances --instance-ids $GREEN_INSTANCE_IDS
    exit 1
fi

echo "Deployment validated successfully!"

# Clean up old blue environment
echo "Cleaning up old blue environment..."

# Get blue instance IDs
BLUE_INSTANCE_IDS=$(aws elbv2 describe-target-health \
    --target-group-arn ${BLUE_TG_ARN} \
    --query 'TargetHealthDescriptions[].Target.Id' \
    --output text)

# Deregister blue targets
aws elbv2 deregister-targets \
    --target-group-arn ${BLUE_TG_ARN} \
    --targets $TARGETS_JSON

# Wait for deregistration
sleep 60

# Terminate old blue instances
if [ ! -z "$BLUE_INSTANCE_IDS" ]; then
    aws ec2 terminate-instances --instance-ids $BLUE_INSTANCE_IDS
    echo "Terminated old blue instances: $BLUE_INSTANCE_IDS"
fi

# Swap target group names for next deployment
echo "Swapping target group names for next deployment..."

# Rename current green to blue for next deployment
aws elbv2 modify-target-group \
    --target-group-arn ${GREEN_TG_ARN} \
    --target-group-attributes Key=name,Value=${BLUE_TG_NAME}

echo "Blue-green deployment completed successfully!"
echo "Application ${APPLICATION_NAME} v${NEW_VERSION} is now live in ${ENVIRONMENT}"

# Cleanup
rm -f user-data.sh
```

### Load Balancer Cost Optimization

```python
# lb-cost-optimizer.py - Optimize load balancer costs and efficiency
import boto3
import json
from datetime import datetime, timedelta
from typing import Dict, List
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LoadBalancerCostOptimizer:
    def __init__(self, region_name: str = 'us-west-2'):
        self.elbv2_client = boto3.client('elbv2', region_name=region_name)
        self.cloudwatch_client = boto3.client('cloudwatch', region_name=region_name)
        self.ce_client = boto3.client('ce', region_name='us-east-1')  # Cost Explorer is only in us-east-1
        
    def analyze_load_balancer_utilization(self, days: int = 30) -> List[Dict]:
        """Analyze load balancer utilization to identify cost optimization opportunities"""
        
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=days)
        
        load_balancers = self.elbv2_client.describe_load_balancers()['LoadBalancers']
        optimization_recommendations = []
        
        for lb in load_balancers:
            lb_arn = lb['LoadBalancerArn']
            lb_name = lb['LoadBalancerName']
            lb_type = lb['Type']
            
            logger.info(f"Analyzing {lb_name} ({lb_type})")
            
            # Get metrics for analysis
            metrics = self._get_utilization_metrics(lb_arn, start_time, end_time)
            
            # Analyze utilization
            analysis = {
                'load_balancer_name': lb_name,
                'load_balancer_arn': lb_arn,
                'type': lb_type,
                'state': lb['State']['Code'],
                'metrics': metrics,
                'recommendations': [],
                'potential_savings': 0,
                'utilization_score': 0
            }
            
            # Calculate utilization score
            request_count = metrics.get('avg_request_count', 0)
            target_count = metrics.get('avg_healthy_hosts', 0)
            
            if lb_type == 'application':
                # For ALB, calculate based on request count and target utilization
                if request_count == 0:
                    analysis['utilization_score'] = 0
                    analysis['recommendations'].append("Load balancer receives no traffic - consider deletion")
                    analysis['potential_savings'] = self._estimate_lb_cost(lb_type, days)
                elif request_count < 100:  # Very low traffic
                    analysis['utilization_score'] = 25
                    analysis['recommendations'].append("Very low traffic - consider consolidating with other applications")
                elif target_count == 0:
                    analysis['utilization_score'] = 0
                    analysis['recommendations'].append("No healthy targets - load balancer not serving traffic")
                elif target_count == 1:
                    analysis['recommendations'].append("Single target - consider if load balancer is necessary")
                    analysis['utilization_score'] = 50
                else:
                    analysis['utilization_score'] = min(100, (request_count / 1000) * 100)
                    
            elif lb_type == 'network':
                # For NLB, calculate based on connection count and throughput
                connection_count = metrics.get('avg_new_connections', 0)
                if connection_count == 0:
                    analysis['utilization_score'] = 0
                    analysis['recommendations'].append("No connections - consider deletion")
                    analysis['potential_savings'] = self._estimate_lb_cost(lb_type, days)
                else:
                    analysis['utilization_score'] = min(100, (connection_count / 100) * 100)
            
            # Check for idle load balancers
            if metrics.get('max_request_count', 0) == 0 and metrics.get('max_new_connections', 0) == 0:
                analysis['recommendations'].append("IDLE: Load balancer has no traffic and can be deleted")
                analysis['potential_savings'] = self._estimate_lb_cost(lb_type, days)
            
            # Check for over-provisioning
            if target_count > 10 and request_count / target_count < 10:
                analysis['recommendations'].append("Potentially over-provisioned - consider reducing target count")
            
            # Check for underutilized ALB features
            if lb_type == 'application':
                target_groups = self._get_target_groups(lb_arn)
                if len(target_groups) == 1:
                    analysis['recommendations'].append("Single target group - consider NLB for better cost efficiency")
                
                # Check for SSL termination usage
                listeners = self._get_listeners(lb_arn)
                https_listeners = [l for l in listeners if l['Protocol'] == 'HTTPS']
                if not https_listeners:
                    analysis['recommendations'].append("No HTTPS listeners - consider if ALB features are needed")
            
            optimization_recommendations.append(analysis)
        
        return optimization_recommendations
    
    def _get_utilization_metrics(self, lb_arn: str, start_time: datetime, end_time: datetime) -> Dict:
        """Get utilization metrics for a load balancer"""
        
        lb_name = lb_arn.split('/')[-3]
        metrics = {}
        
        # Determine load balancer type for appropriate metrics
        lb_type = 'application' if '/app/' in lb_arn else 'network'
        
        if lb_type == 'application':
            metric_queries = [
                ('RequestCount', 'AWS/ApplicationELB'),
                ('TargetResponseTime', 'AWS/ApplicationELB'),
                ('HealthyHostCount', 'AWS/ApplicationELB'),
                ('UnHealthyHostCount', 'AWS/ApplicationELB')
            ]
        else:
            metric_queries = [
                ('NewFlowCount', 'AWS/NetworkELB'),
                ('ActiveFlowCount', 'AWS/NetworkELB'),
                ('HealthyHostCount', 'AWS/NetworkELB'),
                ('UnHealthyHostCount', 'AWS/NetworkELB')
            ]
        
        for metric_name, namespace in metric_queries:
            try:
                response = self.cloudwatch_client.get_metric_statistics(
                    Namespace=namespace,
                    MetricName=metric_name,
                    Dimensions=[{'Name': 'LoadBalancer', 'Value': lb_name}],
                    StartTime=start_time,
                    EndTime=end_time,
                    Period=3600,  # 1 hour
                    Statistics=['Average', 'Maximum', 'Sum']
                )
                
                if response['Datapoints']:
                    values = [dp.get('Sum', dp.get('Average', 0)) for dp in response['Datapoints']]
                    max_values = [dp.get('Maximum', 0) for dp in response['Datapoints']]
                    
                    metrics[f'avg_{metric_name.lower()}'] = sum(values) / len(values) if values else 0
                    metrics[f'max_{metric_name.lower()}'] = max(max_values) if max_values else 0
                    
                    # Map some metrics to more readable names
                    if metric_name == 'RequestCount':
                        metrics['avg_request_count'] = metrics[f'avg_{metric_name.lower()}']
                        metrics['max_request_count'] = metrics[f'max_{metric_name.lower()}']
                    elif metric_name == 'NewFlowCount':
                        metrics['avg_new_connections'] = metrics[f'avg_{metric_name.lower()}']
                        metrics['max_new_connections'] = metrics[f'max_{metric_name.lower()}']
                    elif metric_name == 'HealthyHostCount':
                        metrics['avg_healthy_hosts'] = metrics[f'avg_{metric_name.lower()}']
                    
            except Exception as e:
                logger.error(f"Error getting metric {metric_name}: {e}")
                metrics[f'avg_{metric_name.lower()}'] = 0
                metrics[f'max_{metric_name.lower()}'] = 0
        
        return metrics
    
    def _get_target_groups(self, lb_arn: str) -> List[Dict]:
        """Get target groups for a load balancer"""
        try:
            response = self.elbv2_client.describe_target_groups(LoadBalancerArn=lb_arn)
            return response['TargetGroups']
        except Exception as e:
            logger.error(f"Error getting target groups for {lb_arn}: {e}")
            return []
    
    def _get_listeners(self, lb_arn: str) -> List[Dict]:
        """Get listeners for a load balancer"""
        try:
            response = self.elbv2_client.describe_listeners(LoadBalancerArn=lb_arn)
            return response['Listeners']
        except Exception as e:
            logger.error(f"Error getting listeners for {lb_arn}: {e}")
            return []
    
    def _estimate_lb_cost(self, lb_type: str, days: int) -> float:
        """Estimate load balancer cost for given period"""
        
        # Pricing estimates (US West 2, as of 2024)
        hourly_rates = {
            'application': 0.0225,  # ALB
            'network': 0.0225,     # NLB
            'gateway': 0.0225      # GWLB
        }
        
        hourly_rate = hourly_rates.get(lb_type, 0.0225)
        hours = days * 24
        
        return hourly_rate * hours
    
    def generate_cost_optimization_report(self) -> Dict:
        """Generate comprehensive cost optimization report"""
        
        logger.info("Generating cost optimization report...")
        
        # Analyze utilization
        utilization_analysis = self.analyze_load_balancer_utilization(days=30)
        
        # Calculate total potential savings
        total_potential_savings = sum(lb['potential_savings'] for lb in utilization_analysis)
        
        # Categorize load balancers
        idle_lbs = [lb for lb in utilization_analysis if lb['utilization_score'] == 0]
        underutilized_lbs = [lb for lb in utilization_analysis if 0 < lb['utilization_score'] < 25]
        well_utilized_lbs = [lb for lb in utilization_analysis if lb['utilization_score'] >= 75]
        
        # Generate report
        report = {
            'generated_at': datetime.utcnow().isoformat(),
            'analysis_period_days': 30,
            'total_load_balancers': len(utilization_analysis),
            'summary': {
                'idle_count': len(idle_lbs),
                'underutilized_count': len(underutilized_lbs),
                'well_utilized_count': len(well_utilized_lbs),
                'total_potential_monthly_savings': total_potential_savings
            },
            'recommendations': {
                'immediate_actions': [],
                'optimization_opportunities': [],
                'monitoring_suggestions': []
            },
            'detailed_analysis': utilization_analysis
        }
        
        # Generate recommendations
        if idle_lbs:
            report['recommendations']['immediate_actions'].append(
                f"Delete {len(idle_lbs)} idle load balancers to save ${sum(lb['potential_savings'] for lb in idle_lbs):.2f}/month"
            )
        
        if underutilized_lbs:
            report['recommendations']['optimization_opportunities'].append(
                f"Review {len(underutilized_lbs)} underutilized load balancers for consolidation opportunities"
            )
        
        # Add specific recommendations
        for lb in utilization_analysis:
            if lb['recommendations']:
                for rec in lb['recommendations']:
                    if 'IDLE' in rec:
                        report['recommendations']['immediate_actions'].append(f"{lb['load_balancer_name']}: {rec}")
                    else:
                        report['recommendations']['optimization_opportunities'].append(f"{lb['load_balancer_name']}: {rec}")
        
        # Add monitoring suggestions
        report['recommendations']['monitoring_suggestions'] = [
            "Set up CloudWatch alarms for request count thresholds",
            "Implement automated cost reporting for load balancers",
            "Review load balancer configurations quarterly",
            "Consider using AWS Cost Explorer for detailed cost analysis"
        ]
        
        return report
    
    def implement_cost_optimizations(self, report: Dict, auto_approve_idle: bool = False) -> Dict:
        """Implement cost optimizations based on analysis"""
        
        results = {
            'actions_taken': [],
            'approvals_required': [],
            'errors': []
        }
        
        for lb in report['detailed_analysis']:
            lb_name = lb['load_balancer_name']
            lb_arn = lb['load_balancer_arn']
            
            # Handle idle load balancers
            if lb['utilization_score'] == 0 and auto_approve_idle:
                try:
                    # Check if load balancer can be safely deleted
                    target_groups = self._get_target_groups(lb_arn)
                    
                    # If no target groups or all empty, it's safe to delete
                    safe_to_delete = True
                    for tg in target_groups:
                        health_response = self.elbv2_client.describe_target_health(
                            TargetGroupArn=tg['TargetGroupArn']
                        )
                        if health_response['TargetHealthDescriptions']:
                            safe_to_delete = False
                            break
                    
                    if safe_to_delete:
                        # Note: In a real implementation, you might want additional safeguards
                        logger.info(f"Would delete idle load balancer: {lb_name}")
                        results['actions_taken'].append(f"Scheduled {lb_name} for deletion (idle)")
                    else:
                        results['approvals_required'].append(f"{lb_name}: Has targets, manual review required")
                        
                except Exception as e:
                    results['errors'].append(f"Error processing {lb_name}: {str(e)}")
            
            elif lb['utilization_score'] == 0:
                results['approvals_required'].append(f"{lb_name}: Idle load balancer requires manual approval for deletion")
        
        return results

def main():
    """Main function for load balancer cost optimization"""
    
    # Initialize optimizer
    optimizer = LoadBalancerCostOptimizer()
    
    # Generate cost optimization report
    print("Generating cost optimization report...")
    report = optimizer.generate_cost_optimization_report()
    
    # Print summary
    print(f"\\nLoad Balancer Cost Optimization Report - {report['generated_at']}")
    print(f"Total Load Balancers: {report['total_load_balancers']}")
    print(f"Idle: {report['summary']['idle_count']}")
    print(f"Underutilized: {report['summary']['underutilized_count']}")
    print(f"Well Utilized: {report['summary']['well_utilized_count']}")
    print(f"Potential Monthly Savings: ${report['summary']['total_potential_monthly_savings']:.2f}")
    
    # Print recommendations
    print("\\n=== IMMEDIATE ACTIONS ===")
    for action in report['recommendations']['immediate_actions']:
        print(f"• {action}")
    
    print("\\n=== OPTIMIZATION OPPORTUNITIES ===")
    for opportunity in report['recommendations']['optimization_opportunities']:
        print(f"• {opportunity}")
    
    # Print detailed analysis for problematic load balancers
    print("\\n=== DETAILED ANALYSIS ===")
    for lb in report['detailed_analysis']:
        if lb['utilization_score'] < 50:
            print(f"\\n{lb['load_balancer_name']} (Score: {lb['utilization_score']}):")
            print(f"  Type: {lb['type']}")
            print(f"  Avg Requests: {lb['metrics'].get('avg_request_count', 0):.0f}")
            print(f"  Recommendations:")
            for rec in lb['recommendations']:
                print(f"    - {rec}")

if __name__ == "__main__":
    main()
```

## Best Practices

### Architecture Design
- **Multi-AZ deployment** ensure load balancers span multiple availability zones for high availability
- **Health check optimization** configure appropriate health check paths and thresholds for application requirements
- **Target group strategy** separate target groups for different application tiers and environments
- **SSL/TLS best practices** use ACM certificates and enable secure ciphers

### Security Configuration
- **Security groups** implement least privilege access with specific port and source restrictions
- **WAF integration** protect against common web exploits with AWS WAF rules
- **Access logging** enable detailed access logs for security monitoring and compliance
- **VPC endpoints** use VPC endpoints for private connectivity when accessing from within VPC

### Performance Optimization
- **Connection draining** configure appropriate deregistration delay for graceful shutdowns
- **Sticky sessions** use when required but consider stateless application design
- **Cross-zone load balancing** enable for even distribution across availability zones
- **Target group health** monitor target health and configure appropriate alarm thresholds

### Cost Management
- **Right-sizing** choose appropriate load balancer type based on actual requirements
- **Idle resource cleanup** regularly review and remove unused load balancers and target groups
- **Monitoring usage** implement CloudWatch metrics and billing alerts for cost control
- **Consolidation opportunities** consider consolidating multiple applications on single ALB with path-based routing