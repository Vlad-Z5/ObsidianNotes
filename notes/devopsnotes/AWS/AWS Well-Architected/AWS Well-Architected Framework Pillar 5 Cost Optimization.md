# AWS Well-Architected Framework - Pillar 5: Cost Optimization

## Strategic Context

Cost optimization enables sustainable growth and competitive pricing while maintaining service quality. Organizations with mature cost optimization practices achieve 20-30% cost savings while improving service delivery through better resource utilization.

### Business Impact of Cost Optimization
- **Cost Savings**: 20-30% reduction in infrastructure costs through optimization
- **Resource Efficiency**: 40-60% improvement in resource utilization
- **Financial Predictability**: Better cost forecasting and budget management
- **Competitive Advantage**: Lower operational costs enable competitive pricing
- **Innovation Investment**: Cost savings can be reinvested in innovation and growth

### Cost Optimization Design Principles
1. **Implement cloud financial management**: Establish cost accountability and governance
2. **Adopt a consumption model**: Pay only for computing resources consumed
3. **Measure overall efficiency**: Track business metrics per dollar spent
4. **Stop spending money on heavy lifting**: Use managed services to reduce operational overhead
5. **Analyze and attribute expenditure**: Understand cost drivers and allocate costs appropriately

## Core Principles and Best Practices

### Financial Governance

**Cost Visibility and Attribution**
Implement comprehensive cost tracking and allocation across business units, projects, and services. Use tagging strategies and cost allocation tools to enable informed decision-making.

```python
# Example: Advanced Cost Analytics and Reporting
import boto3
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json

class AWSCostAnalyzer:
    def __init__(self):
        self.ce_client = boto3.client('ce')  # Cost Explorer
        self.organizations_client = boto3.client('organizations')
        self.pricing_client = boto3.client('pricing', region_name='us-east-1')
    
    def get_cost_by_service(self, 
                           start_date: str, 
                           end_date: str, 
                           granularity: str = 'MONTHLY') -> Dict:
        """Get cost breakdown by AWS service"""
        try:
            response = self.ce_client.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date,
                    'End': end_date
                },
                Granularity=granularity,
                Metrics=['BlendedCost', 'UsageQuantity'],
                GroupBy=[
                    {
                        'Type': 'DIMENSION',
                        'Key': 'SERVICE'
                    }
                ]
            )
            
            cost_data = []
            for result in response['ResultsByTime']:
                for group in result['Groups']:
                    service_name = group['Keys'][0]
                    cost = float(group['Metrics']['BlendedCost']['Amount'])
                    usage = float(group['Metrics']['UsageQuantity']['Amount'])
                    
                    cost_data.append({
                        'date': result['TimePeriod']['Start'],
                        'service': service_name,
                        'cost': cost,
                        'usage': usage
                    })
            
            return {'status': 'success', 'data': cost_data}
            
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def get_cost_by_tags(self, 
                        start_date: str, 
                        end_date: str, 
                        tag_key: str) -> Dict:
        """Get cost breakdown by tag values"""
        try:
            response = self.ce_client.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date,
                    'End': end_date
                },
                Granularity='MONTHLY',
                Metrics=['BlendedCost'],
                GroupBy=[
                    {
                        'Type': 'TAG',
                        'Key': tag_key
                    }
                ]
            )
            
            cost_by_tags = {}
            for result in response['ResultsByTime']:
                for group in result['Groups']:
                    tag_value = group['Keys'][0] or 'untagged'
                    cost = float(group['Metrics']['BlendedCost']['Amount'])
                    
                    if tag_value not in cost_by_tags:
                        cost_by_tags[tag_value] = 0
                    cost_by_tags[tag_value] += cost
            
            return {'status': 'success', 'data': cost_by_tags}
            
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def get_unused_resources(self) -> Dict:
        """Identify unused or underutilized resources"""
        recommendations = []
        
        try:
            # Get EC2 rightsizing recommendations
            ec2_response = self.ce_client.get_rightsizing_recommendation(
                Service='AmazonEC2'
            )
            
            for recommendation in ec2_response.get('RightsizingRecommendations', []):
                recommendations.append({
                    'type': 'EC2_RIGHTSIZING',
                    'resource_id': recommendation.get('CurrentInstance', {}).get('ResourceId'),
                    'current_type': recommendation.get('CurrentInstance', {}).get('InstanceType'),
                    'recommended_type': recommendation.get('RightsizingType'),
                    'estimated_savings': recommendation.get('EstimatedMonthlySavings'),
                    'confidence': recommendation.get('ConfidenceLevel')
                })
            
            # Get reserved instance recommendations
            ri_response = self.ce_client.get_reservation_purchase_recommendation(
                Service='AmazonEC2'
            )
            
            for recommendation in ri_response.get('Recommendations', []):
                recommendations.append({
                    'type': 'RESERVED_INSTANCE',
                    'service': 'EC2',
                    'recommended_instances': recommendation.get('RecommendationDetails', {}).get('InstanceDetails'),
                    'estimated_savings': recommendation.get('RecommendationDetails', {}).get('EstimatedMonthlySavingsAmount'),
                    'break_even_months': recommendation.get('RecommendationDetails', {}).get('EstimatedBreakEvenInMonths')
                })
            
            return {'status': 'success', 'recommendations': recommendations}
            
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def generate_cost_optimization_report(self, 
                                        start_date: str, 
                                        end_date: str) -> Dict:
        """Generate comprehensive cost optimization report"""
        report = {
            'period': f"{start_date} to {end_date}",
            'generated_at': datetime.now().isoformat(),
            'sections': {}
        }
        
        # Service breakdown
        service_costs = self.get_cost_by_service(start_date, end_date)
        if service_costs['status'] == 'success':
            df = pd.DataFrame(service_costs['data'])
            top_services = df.groupby('service')['cost'].sum().sort_values(ascending=False).head(10)
            report['sections']['top_services'] = top_services.to_dict()
        
        # Environment breakdown
        env_costs = self.get_cost_by_tags(start_date, end_date, 'Environment')
        if env_costs['status'] == 'success':
            report['sections']['cost_by_environment'] = env_costs['data']
        
        # Team breakdown
        team_costs = self.get_cost_by_tags(start_date, end_date, 'Team')
        if team_costs['status'] == 'success':
            report['sections']['cost_by_team'] = team_costs['data']
        
        # Optimization recommendations
        recommendations = self.get_unused_resources()
        if recommendations['status'] == 'success':
            total_potential_savings = sum(
                float(rec.get('estimated_savings', {}).get('Amount', 0))
                for rec in recommendations['recommendations']
                if rec.get('estimated_savings')
            )
            report['sections']['optimization_recommendations'] = {
                'total_potential_savings': total_potential_savings,
                'recommendations': recommendations['recommendations']
            }
        
        return report

# Usage Example
analyzer = AWSCostAnalyzer()

# Generate monthly cost report
start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
end_date = datetime.now().strftime('%Y-%m-%d')

cost_report = analyzer.generate_cost_optimization_report(start_date, end_date)
print(json.dumps(cost_report, indent=2, default=str))
```

**Budget Management and Forecasting**
Establish detailed budgeting processes with automated alerts and approval workflows. Use predictive analytics to forecast costs and optimize resource planning.

```terraform
# Example: Comprehensive AWS Budgets with Automation
resource "aws_budgets_budget" "monthly_cost_budget" {
  name         = "monthly-cost-budget"
  budget_type  = "COST"
  limit_amount = "1000"
  limit_unit   = "USD"
  time_unit    = "MONTHLY"
  time_period_start = "2024-01-01_00:00"

  cost_filters {
    service = ["Amazon Elastic Compute Cloud - Compute"]
  }

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                 = 80
    threshold_type            = "PERCENTAGE"
    notification_type         = "ACTUAL"
    subscriber_email_addresses = ["finance@company.com", "engineering@company.com"]
    subscriber_sns_topic_arns  = [aws_sns_topic.budget_alerts.arn]
  }

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                 = 100
    threshold_type            = "PERCENTAGE"
    notification_type          = "FORECASTED"
    subscriber_email_addresses = ["cto@company.com", "cfo@company.com"]
    subscriber_sns_topic_arns  = [aws_sns_topic.budget_alerts.arn]
  }
}

resource "aws_budgets_budget" "usage_budget" {
  name         = "ec2-usage-budget"
  budget_type  = "USAGE"
  limit_amount = "100"
  limit_unit   = "GB"
  time_unit    = "MONTHLY"

  cost_filters {
    service = ["Amazon Elastic Compute Cloud - Compute"]
  }

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                 = 90
    threshold_type            = "PERCENTAGE"
    notification_type          = "ACTUAL"
    subscriber_email_addresses = ["operations@company.com"]
  }
}

# SNS Topic for budget alerts
resource "aws_sns_topic" "budget_alerts" {
  name = "budget-alerts"
}

# Lambda function for automated cost optimization actions
resource "aws_lambda_function" "cost_optimizer" {
  filename         = "cost_optimizer.zip"
  function_name    = "cost-optimizer"
  role            = aws_iam_role.lambda_role.arn
  handler         = "index.handler"
  runtime         = "python3.9"
  timeout         = 300

  environment {
    variables = {
      SNS_TOPIC_ARN = aws_sns_topic.budget_alerts.arn
      SLACK_WEBHOOK_URL = var.slack_webhook_url
    }
  }
}

# EventBridge rule to trigger cost optimization daily
resource "aws_cloudwatch_event_rule" "daily_cost_check" {
  name                = "daily-cost-optimization"
  description         = "Trigger cost optimization checks daily"
  schedule_expression = "cron(0 8 * * ? *)"  # 8 AM UTC daily
}

resource "aws_cloudwatch_event_target" "lambda_target" {
  rule      = aws_cloudwatch_event_rule.daily_cost_check.name
  target_id = "CostOptimizerTarget"
  arn       = aws_lambda_function.cost_optimizer.arn
}
```

**Reserved Capacity and Pricing Models**
Leverage reserved instances, savings plans, and spot instances to optimize costs for predictable workloads. Implement hybrid pricing strategies for different workload types.

```python
# Example: Intelligent Reserved Instance and Spot Instance Management
import boto3
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import numpy as np

class IntelligentPricingOptimizer:
    def __init__(self):
        self.ec2_client = boto3.client('ec2')
        self.ce_client = boto3.client('ce')
        self.autoscaling_client = boto3.client('autoscaling')
    
    def analyze_usage_patterns(self, days_back: int = 90) -> Dict:
        """Analyze EC2 usage patterns to recommend optimal pricing strategy"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        try:
            # Get usage data from Cost Explorer
            response = self.ce_client.get_usage(
                TimePeriod={
                    'Start': start_date.strftime('%Y-%m-%d'),
                    'End': end_date.strftime('%Y-%m-%d')
                },
                Granularity='DAILY',
                Metrics=['UsageQuantity'],
                GroupBy=[
                    {
                        'Type': 'DIMENSION',
                        'Key': 'INSTANCE_TYPE'
                    }
                ],
                Filter={
                    'Dimensions': {
                        'Key': 'SERVICE',
                        'Values': ['Amazon Elastic Compute Cloud - Compute']
                    }
                }
            )
            
            usage_data = []
            for result in response['ResultsByTime']:
                date = result['TimePeriod']['Start']
                for group in result['Groups']:
                    instance_type = group['Keys'][0]
                    usage = float(group['Metrics']['UsageQuantity']['Amount'])
                    
                    usage_data.append({
                        'date': date,
                        'instance_type': instance_type,
                        'usage_hours': usage
                    })
            
            df = pd.DataFrame(usage_data)
            
            # Calculate statistics for each instance type
            instance_stats = {}
            for instance_type in df['instance_type'].unique():
                type_data = df[df['instance_type'] == instance_type]
                
                instance_stats[instance_type] = {
                    'avg_daily_hours': type_data['usage_hours'].mean(),
                    'min_daily_hours': type_data['usage_hours'].min(),
                    'max_daily_hours': type_data['usage_hours'].max(),
                    'std_deviation': type_data['usage_hours'].std(),
                    'utilization_consistency': 1 - (type_data['usage_hours'].std() / type_data['usage_hours'].mean()),
                    'total_hours': type_data['usage_hours'].sum(),
                    'days_with_usage': len(type_data[type_data['usage_hours'] > 0])
                }
            
            return {'status': 'success', 'data': instance_stats}
            
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def recommend_pricing_strategy(self, usage_analysis: Dict) -> Dict:
        """Recommend optimal pricing strategy based on usage patterns"""
        recommendations = []
        
        for instance_type, stats in usage_analysis['data'].items():
            avg_hours = stats['avg_daily_hours']
            consistency = stats['utilization_consistency']
            total_hours = stats['total_hours']
            
            # Determine pricing strategy based on usage patterns
            if avg_hours >= 20 and consistency > 0.8:  # High, consistent usage
                strategy = 'RESERVED_INSTANCE'
                potential_savings = total_hours * 0.72 * 0.4  # Assuming 40% RI discount
                reasoning = 'High, consistent usage makes Reserved Instances optimal'
                
            elif avg_hours >= 12 and consistency > 0.6:  # Moderate, somewhat consistent
                strategy = 'SAVINGS_PLAN'
                potential_savings = total_hours * 0.72 * 0.25  # Assuming 25% Savings Plan discount
                reasoning = 'Moderate usage with flexibility needs makes Savings Plans optimal'
                
            elif avg_hours < 8 or consistency < 0.4:  # Low or variable usage
                strategy = 'SPOT_INSTANCES'
                potential_savings = total_hours * 0.72 * 0.7  # Assuming 70% Spot discount
                reasoning = 'Variable or low usage makes Spot Instances optimal'
                
            else:  # Default to On-Demand
                strategy = 'ON_DEMAND'
                potential_savings = 0
                reasoning = 'Current usage pattern is optimal for On-Demand pricing'
            
            recommendations.append({
                'instance_type': instance_type,
                'current_strategy': 'ON_DEMAND',  # Assumed current state
                'recommended_strategy': strategy,
                'potential_monthly_savings': potential_savings,
                'reasoning': reasoning,
                'avg_daily_hours': avg_hours,
                'utilization_consistency': consistency
            })
        
        return sorted(recommendations, key=lambda x: x['potential_monthly_savings'], reverse=True)
    
    def implement_spot_fleet_strategy(self, 
                                    target_capacity: int,
                                    instance_types: List[str],
                                    az_distribution: str = 'balanced') -> Dict:
        """Implement intelligent Spot Fleet configuration"""
        
        # Get current Spot prices
        spot_prices = {}
        for instance_type in instance_types:
            try:
                response = self.ec2_client.describe_spot_price_history(
                    InstanceTypes=[instance_type],
                    ProductDescriptions=['Linux/UNIX'],
                    MaxResults=1
                )
                
                if response['SpotPriceHistory']:
                    spot_prices[instance_type] = float(response['SpotPriceHistory'][0]['SpotPrice'])
                
            except Exception as e:
                print(f"Error getting spot price for {instance_type}: {e}")
        
        # Calculate weights based on price and performance
        launch_specifications = []
        for instance_type in instance_types:
            if instance_type in spot_prices:
                # Simple weight calculation (can be enhanced with performance metrics)
                weight = max(1, int(10 / spot_prices[instance_type]))
                
                launch_specifications.append({
                    'ImageId': 'ami-0abcdef1234567890',  # Replace with actual AMI
                    'InstanceType': instance_type,
                    'KeyName': 'my-key-pair',
                    'SecurityGroups': [{'GroupId': 'sg-12345678'}],
                    'WeightedCapacity': weight,
                    'SpotPrice': str(spot_prices[instance_type] * 1.2)  # Bid 20% above current price
                })
        
        spot_fleet_config = {
            'IamFleetRole': 'arn:aws:iam::123456789012:role/aws-ec2-spot-fleet-tagging-role',
            'AllocationStrategy': 'diversified',
            'TargetCapacity': target_capacity,
            'SpotPrice': '0.50',  # Maximum price willing to pay
            'LaunchSpecifications': launch_specifications,
            'Type': 'maintain',
            'ReplaceUnhealthyInstances': True,
            'InstanceInterruptionBehavior': 'terminate',
            'TerminateInstancesWithExpiration': True,
            'TagSpecifications': [
                {
                    'ResourceType': 'spot-fleet-request',
                    'Tags': [
                        {'Key': 'Name', 'Value': 'cost-optimized-spot-fleet'},
                        {'Key': 'Environment', 'Value': 'production'},
                        {'Key': 'CostOptimization', 'Value': 'spot-fleet'}
                    ]
                }
            ]
        }
        
        return {
            'spot_fleet_config': spot_fleet_config,
            'estimated_savings': sum(spot_prices.values()) * 0.7 * 24 * 30,  # Rough monthly savings
            'spot_prices': spot_prices
        }

# Usage Example
optimizer = IntelligentPricingOptimizer()

# Analyze usage patterns
usage_analysis = optimizer.analyze_usage_patterns(days_back=90)
if usage_analysis['status'] == 'success':
    # Get pricing recommendations
    recommendations = optimizer.recommend_pricing_strategy(usage_analysis)
    
    print("Pricing Strategy Recommendations:")
    for rec in recommendations[:5]:  # Top 5 recommendations
        print(f"Instance Type: {rec['instance_type']}")
        print(f"Recommended Strategy: {rec['recommended_strategy']}")
        print(f"Potential Monthly Savings: ${rec['potential_monthly_savings']:.2f}")
        print(f"Reasoning: {rec['reasoning']}")
        print("-" * 50)
    
    # Generate Spot Fleet configuration for variable workloads
    spot_fleet_config = optimizer.implement_spot_fleet_strategy(
        target_capacity=10,
        instance_types=['m5.large', 'm5.xlarge', 'c5.large', 'c5.xlarge']
    )
    
    print(f"Spot Fleet Estimated Monthly Savings: ${spot_fleet_config['estimated_savings']:.2f}")
```

### Resource Optimization

**Automated Resource Management**
Implement automated resource lifecycle management including scheduling, right-sizing, and decommissioning. Use machine learning to optimize resource allocation based on usage patterns.

```yaml
# Example: Automated Resource Lifecycle Management
apiVersion: v1
kind: ConfigMap
metadata:
  name: resource-optimizer-config
data:
  config.yaml: |
    resource_policies:
      development:
        schedule:
          start_time: "08:00"
          stop_time: "18:00"
          timezone: "UTC"
          weekdays_only: true
        auto_scaling:
          min_replicas: 1
          max_replicas: 5
          target_cpu: 70
        resource_limits:
          cpu: "2"
          memory: "4Gi"
        idle_threshold_minutes: 30
        
      staging:
        schedule:
          start_time: "06:00"
          stop_time: "22:00"
          timezone: "UTC"
          weekdays_only: false
        auto_scaling:
          min_replicas: 2
          max_replicas: 10
          target_cpu: 60
        resource_limits:
          cpu: "4"
          memory: "8Gi"
        idle_threshold_minutes: 60
        
      production:
        schedule:
          always_on: true
        auto_scaling:
          min_replicas: 3
          max_replicas: 50
          target_cpu: 70
        resource_limits:
          cpu: "8"
          memory: "16Gi"
        idle_threshold_minutes: 0  # Never auto-shutdown
---
apiVersion: batch/v1
kind: CronJob
metadata:
  name: resource-optimizer
spec:
  schedule: "*/15 * * * *"  # Run every 15 minutes
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: optimizer
            image: company/resource-optimizer:latest
            env:
            - name: CLUSTER_NAME
              value: "production-cluster"
            - name: CONFIG_MAP
              value: "resource-optimizer-config"
            command:
            - python
            - -c
            - |
              import kubernetes
              import yaml
              import os
              from datetime import datetime, time
              import pytz
              
              def should_be_running(schedule_config, current_time):
                  if schedule_config.get('always_on'):
                      return True
                  
                  tz = pytz.timezone(schedule_config.get('timezone', 'UTC'))
                  local_time = current_time.astimezone(tz)
                  
                  # Check if it's a weekday
                  if schedule_config.get('weekdays_only') and local_time.weekday() >= 5:
                      return False
                  
                  start_time = datetime.strptime(schedule_config['start_time'], '%H:%M').time()
                  stop_time = datetime.strptime(schedule_config['stop_time'], '%H:%M').time()
                  
                  current_time_only = local_time.time()
                  
                  if start_time <= stop_time:
                      return start_time <= current_time_only <= stop_time
                  else:  # Overnight schedule
                      return current_time_only >= start_time or current_time_only <= stop_time
              
              def optimize_resources():
                  kubernetes.config.load_incluster_config()
                  v1 = kubernetes.client.CoreV1Api()
                  apps_v1 = kubernetes.client.AppsV1Api()
                  
                  # Load configuration
                  config_map = v1.read_namespaced_config_map(
                      name=os.environ['CONFIG_MAP'],
                      namespace='default'
                  )
                  
                  config = yaml.safe_load(config_map.data['config.yaml'])
                  current_time = datetime.now(pytz.UTC)
                  
                  # Get all deployments
                  deployments = apps_v1.list_deployment_for_all_namespaces()
                  
                  for deployment in deployments.items:
                      env_label = deployment.metadata.labels.get('environment')
                      if env_label and env_label in config['resource_policies']:
                          policy = config['resource_policies'][env_label]
                          should_run = should_be_running(policy['schedule'], current_time)
                          
                          current_replicas = deployment.status.replicas or 0
                          
                          if should_run and current_replicas == 0:
                              # Scale up
                              min_replicas = policy['auto_scaling']['min_replicas']
                              deployment.spec.replicas = min_replicas
                              apps_v1.patch_namespaced_deployment(
                                  name=deployment.metadata.name,
                                  namespace=deployment.metadata.namespace,
                                  body=deployment
                              )
                              print(f"Scaled up {deployment.metadata.name} to {min_replicas} replicas")
                              
                          elif not should_run and current_replicas > 0:
                              # Scale down
                              deployment.spec.replicas = 0
                              apps_v1.patch_namespaced_deployment(
                                  name=deployment.metadata.name,
                                  namespace=deployment.metadata.namespace,
                                  body=deployment
                              )
                              print(f"Scaled down {deployment.metadata.name} to 0 replicas")
              
              optimize_resources()
          restartPolicy: OnFailure
```

**Storage Optimization**
Implement intelligent storage tiering and lifecycle policies. Use compression, deduplication, and archival strategies to optimize storage costs.

```terraform
# Example: Intelligent S3 Storage Optimization
resource "aws_s3_bucket" "data_lake" {
  bucket = "company-data-lake-optimized"
}

resource "aws_s3_bucket_lifecycle_configuration" "data_lake_lifecycle" {
  bucket = aws_s3_bucket.data_lake.id

  rule {
    id     = "intelligent_tiering"
    status = "Enabled"

    filter {
      prefix = "raw-data/"
    }

    transition {
      days          = 30
      storage_class = "STANDARD_IA"
    }

    transition {
      days          = 90
      storage_class = "GLACIER"
    }

    transition {
      days          = 365
      storage_class = "DEEP_ARCHIVE"
    }

    expiration {
      days = 2555  # 7 years
    }
  }

  rule {
    id     = "processed_data_lifecycle"
    status = "Enabled"

    filter {
      prefix = "processed-data/"
    }

    transition {
      days          = 7
      storage_class = "STANDARD_IA"
    }

    transition {
      days          = 30
      storage_class = "GLACIER"
    }

    expiration {
      days = 1095  # 3 years
    }
  }

  rule {
    id     = "logs_lifecycle"
    status = "Enabled"

    filter {
      prefix = "logs/"
    }

    transition {
      days          = 1
      storage_class = "STANDARD_IA"
    }

    transition {
      days          = 30
      storage_class = "GLACIER"
    }

    expiration {
      days = 365  # 1 year
    }
  }

  rule {
    id     = "multipart_cleanup"
    status = "Enabled"

    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }
  }
}

resource "aws_s3_bucket_intelligent_tiering_configuration" "data_lake_intelligent_tiering" {
  bucket = aws_s3_bucket.data_lake.id
  name   = "entire-bucket"

  filter {
    prefix = ""
  }

  tiering {
    access_tier = "ARCHIVE_ACCESS"
    days        = 90
  }

  tiering {
    access_tier = "DEEP_ARCHIVE_ACCESS"
    days        = 180
  }

  optional_fields = ["BucketKeyStatus", "ChecksumAlgorithm"]
}

# EBS Volume Optimization
resource "aws_ebs_volume" "optimized_volume" {
  availability_zone = "us-west-2a"
  size             = 100
  type             = "gp3"
  
  # GP3 allows you to provision IOPS and throughput independently
  iops       = 3000
  throughput = 125

  encrypted = true

  tags = {
    Name                = "cost-optimized-volume"
    Environment         = "production"
    CostOptimization   = "gp3-optimized"
    ScheduledSnapshot  = "daily"
  }
}

# Automated EBS Snapshot Lifecycle
resource "aws_dlm_lifecycle_policy" "ebs_snapshot_policy" {
  description        = "Cost-optimized EBS snapshot policy"
  execution_role_arn = aws_iam_role.dlm_lifecycle_role.arn
  state             = "ENABLED"

  policy_details {
    resource_types   = ["VOLUME"]
    target_tags = {
      ScheduledSnapshot = "daily"
    }

    schedule {
      name = "daily-snapshots"

      create_rule {
        interval      = 24
        interval_unit = "HOURS"
        times         = ["03:00"]
      }

      retain_rule {
        count = 7  # Keep 7 daily snapshots
      }

      copy_tags = true

      tags_to_add = {
        SnapshotCreator = "DLM"
        Environment     = "production"
      }
    }

    schedule {
      name = "weekly-snapshots"

      create_rule {
        interval      = 1
        interval_unit = "WEEKS"
        times         = ["03:00"]
        cron_expression = "cron(0 3 ? * SUN *)"
      }

      retain_rule {
        count = 4  # Keep 4 weekly snapshots
      }

      copy_tags = true

      tags_to_add = {
        SnapshotCreator = "DLM"
        SnapshotType    = "weekly"
      }
    }
  }
}
```

**Network Optimization**
Optimize network costs through intelligent routing, bandwidth management, and data transfer optimization. Use content delivery networks and edge computing to reduce data transfer costs.

```python
# Example: Advanced Network Cost Optimization
import boto3
import json
from typing import Dict, List, Tuple
from datetime import datetime, timedelta

class NetworkCostOptimizer:
    def __init__(self):
        self.ec2_client = boto3.client('ec2')
        self.cloudfront_client = boto3.client('cloudfront')
        self.ce_client = boto3.client('ce')
        self.cloudwatch_client = boto3.client('cloudwatch')
    
    def analyze_data_transfer_costs(self, days_back: int = 30) -> Dict:
        """Analyze data transfer costs and patterns"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        try:
            response = self.ce_client.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date.strftime('%Y-%m-%d'),
                    'End': end_date.strftime('%Y-%m-%d')
                },
                Granularity='DAILY',
                Metrics=['BlendedCost'],
                GroupBy=[
                    {
                        'Type': 'DIMENSION',
                        'Key': 'USAGE_TYPE'
                    }
                ],
                Filter={
                    'Dimensions': {
                        'Key': 'USAGE_TYPE_GROUP',
                        'Values': ['EC2-Instance', 'EC2-ELB', 'CloudFront']
                    }
                }
            )
            
            transfer_costs = {}
            for result in response['ResultsByTime']:
                date = result['TimePeriod']['Start']
                for group in result['Groups']:
                    usage_type = group['Keys'][0]
                    cost = float(group['Metrics']['BlendedCost']['Amount'])
                    
                    if 'DataTransfer' in usage_type or 'Transfer' in usage_type:
                        if usage_type not in transfer_costs:
                            transfer_costs[usage_type] = []
                        transfer_costs[usage_type].append({
                            'date': date,
                            'cost': cost
                        })
            
            return {'status': 'success', 'data': transfer_costs}
            
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def recommend_cdn_strategy(self, domain_metrics: Dict) -> Dict:
        """Recommend CDN configuration based on traffic patterns"""
        recommendations = []
        
        for domain, metrics in domain_metrics.items():
            total_requests = metrics.get('requests_per_month', 0)
            data_transfer_gb = metrics.get('data_transfer_gb_per_month', 0)
            geographic_distribution = metrics.get('geographic_distribution', {})
            
            # Calculate potential savings with CloudFront
            origin_data_transfer_cost = data_transfer_gb * 0.09  # Rough AWS data transfer cost
            
            # CloudFront pricing tiers (simplified)
            if data_transfer_gb <= 50:  # First 50 GB
                cloudfront_cost = data_transfer_gb * 0.085
            elif data_transfer_gb <= 10000:  # Next 9.95 TB
                cloudfront_cost = 50 * 0.085 + (data_transfer_gb - 50) * 0.080
            else:
                cloudfront_cost = 50 * 0.085 + 9950 * 0.080 + (data_transfer_gb - 10000) * 0.060
            
            # Add request costs
            cloudfront_cost += (total_requests / 1000) * 0.0075  # $0.0075 per 10,000 requests
            
            potential_savings = origin_data_transfer_cost - cloudfront_cost
            
            # Determine cache configuration based on content type
            if 'images' in domain or 'static' in domain:
                cache_ttl = 86400  # 24 hours
                cache_policy = 'static-content'
            elif 'api' in domain:
                cache_ttl = 300    # 5 minutes
                cache_policy = 'dynamic-content'
            else:
                cache_ttl = 3600   # 1 hour
                cache_policy = 'mixed-content'
            
            recommendations.append({
                'domain': domain,
                'recommended': potential_savings > 10,  # Recommend if savings > $10/month
                'potential_monthly_savings': potential_savings,
                'cloudfront_cost': cloudfront_cost,
                'origin_cost': origin_data_transfer_cost,
                'cache_policy': cache_policy,
                'cache_ttl': cache_ttl,
                'edge_locations': self._recommend_edge_locations(geographic_distribution)
            })
        
        return sorted(recommendations, key=lambda x: x['potential_monthly_savings'], reverse=True)
    
    def _recommend_edge_locations(self, geo_distribution: Dict) -> List[str]:
        """Recommend optimal edge locations based on traffic distribution"""
        edge_locations = []
        
        for region, percentage in geo_distribution.items():
            if percentage > 10:  # More than 10% of traffic
                if region in ['US', 'North America']:
                    edge_locations.extend(['US-East-1', 'US-West-2'])
                elif region in ['Europe', 'EU']:
                    edge_locations.extend(['Europe-London', 'Europe-Frankfurt'])
                elif region in ['Asia', 'APAC']:
                    edge_locations.extend(['Asia-Singapore', 'Asia-Tokyo'])
        
        return list(set(edge_locations))  # Remove duplicates
    
    def optimize_nat_gateway_costs(self) -> Dict:
        """Analyze and optimize NAT Gateway costs"""
        recommendations = []
        
        try:
            # Get all NAT Gateways
            nat_gateways = self.ec2_client.describe_nat_gateways()
            
            for nat_gw in nat_gateways['NatGateways']:
                if nat_gw['State'] == 'available':
                    nat_gw_id = nat_gw['NatGatewayId']
                    subnet_id = nat_gw['SubnetId']
                    
                    # Get metrics for the NAT Gateway
                    end_time = datetime.utcnow()
                    start_time = end_time - timedelta(days=7)
                    
                    # Get data processing metrics
                    processing_response = self.cloudwatch_client.get_metric_statistics(
                        Namespace='AWS/NATGateway',
                        MetricName='BytesOutToDestination',
                        Dimensions=[
                            {
                                'Name': 'NatGatewayId',
                                'Value': nat_gw_id
                            }
                        ],
                        StartTime=start_time,
                        EndTime=end_time,
                        Period=86400,  # Daily
                        Statistics=['Sum']
                    )
                    
                    total_bytes = sum(point['Sum'] for point in processing_response['Datapoints'])
                    total_gb = total_bytes / (1024**3)
                    
                    # Calculate costs
                    hourly_cost = 0.045  # NAT Gateway hourly cost
                    processing_cost = total_gb * 0.045  # Data processing cost
                    weekly_cost = (hourly_cost * 24 * 7) + processing_cost
                    monthly_cost = weekly_cost * 4.33  # Average weeks per month
                    
                    # Determine optimization recommendations
                    if total_gb < 1:  # Very low usage
                        recommendation = 'CONSIDER_NAT_INSTANCE'
                        potential_savings = monthly_cost * 0.6  # ~60% savings with NAT instance
                    elif total_gb < 10:  # Low to moderate usage
                        recommendation = 'OPTIMIZE_PLACEMENT'
                        potential_savings = monthly_cost * 0.2  # ~20% savings with optimization
                    else:
                        recommendation = 'CURRENT_SETUP_OPTIMAL'
                        potential_savings = 0
                    
                    recommendations.append({
                        'nat_gateway_id': nat_gw_id,
                        'subnet_id': subnet_id,
                        'weekly_data_gb': total_gb,
                        'monthly_cost': monthly_cost,
                        'recommendation': recommendation,
                        'potential_monthly_savings': potential_savings
                    })
            
            return {'status': 'success', 'recommendations': recommendations}
            
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def generate_network_optimization_report(self) -> Dict:
        """Generate comprehensive network optimization report"""
        report = {
            'generated_at': datetime.now().isoformat(),
            'sections': {}
        }
        
        # Data transfer cost analysis
        transfer_analysis = self.analyze_data_transfer_costs()
        if transfer_analysis['status'] == 'success':
            total_transfer_cost = sum(
                sum(costs['cost'] for costs in cost_data)
                for cost_data in transfer_analysis['data'].values()
            )
            report['sections']['data_transfer_costs'] = {
                'total_monthly_cost': total_transfer_cost,
                'breakdown': transfer_analysis['data']
            }
        
        # NAT Gateway optimization
        nat_optimization = self.optimize_nat_gateway_costs()
        if nat_optimization['status'] == 'success':
            total_nat_savings = sum(
                rec['potential_monthly_savings']
                for rec in nat_optimization['recommendations']
            )
            report['sections']['nat_gateway_optimization'] = {
                'total_potential_savings': total_nat_savings,
                'recommendations': nat_optimization['recommendations']
            }
        
        # Sample CDN recommendations (would need actual domain metrics)
        sample_domains = {
            'static.example.com': {
                'requests_per_month': 1000000,
                'data_transfer_gb_per_month': 500,
                'geographic_distribution': {'US': 60, 'Europe': 30, 'Asia': 10}
            }
        }
        
        cdn_recommendations = self.recommend_cdn_strategy(sample_domains)
        total_cdn_savings = sum(rec['potential_monthly_savings'] for rec in cdn_recommendations)
        
        report['sections']['cdn_optimization'] = {
            'total_potential_savings': total_cdn_savings,
            'recommendations': cdn_recommendations
        }
        
        return report

# Usage Example
optimizer = NetworkCostOptimizer()
network_report = optimizer.generate_network_optimization_report()

print("Network Cost Optimization Report:")
print(f"Generated at: {network_report['generated_at']}")
print("\nSummary:")
for section, data in network_report['sections'].items():
    if 'total_potential_savings' in data:
        print(f"{section}: ${data['total_potential_savings']:.2f} potential monthly savings")
```

## Key Tools and Implementation

### Cost Management and Optimization
- **Cost Monitoring**: AWS Cost Explorer, Azure Cost Management, or cloud cost management tools
- **Resource Optimization**: CloudHealth, Turbonomic, or resource optimization platforms
- **Automated Scheduling**: Instance schedulers, auto-scaling groups, or workload management tools
- **Storage Optimization**: Storage analytics, lifecycle policies, or intelligent tiering services

### Financial Planning and Governance
- **Budgeting Tools**: CloudCheckr, Apptio, or financial planning platforms
- **Cost Allocation**: Tagging strategies, cost center allocation, or chargeback systems
- **Procurement Optimization**: Reserved instance planning, pricing negotiation tools

### Automation and Optimization Tools
- **Spot Instance Management**: SpotFleet, Spotinst, or automated spot management
- **Right-sizing Tools**: AWS Trusted Advisor, CloudWatch insights, or third-party optimization
- **Storage Optimization**: AWS S3 Intelligent Tiering, lifecycle policies, storage analytics

## Cost Optimization Maturity Assessment

### Level 1: Basic Cost Awareness (Reactive)
- Basic cost monitoring and monthly reports
- Manual resource management
- Limited cost allocation and tagging
- Ad-hoc cost optimization efforts

### Level 2: Managed Cost Control (Proactive)
- Automated cost monitoring and alerting
- Basic resource scheduling and right-sizing
- Standardized tagging and cost allocation
- Regular cost optimization reviews

### Level 3: Advanced Cost Optimization (Optimized)
- Automated resource optimization and lifecycle management
- Advanced pricing strategies (Reserved, Spot, Savings Plans)
- Comprehensive cost attribution and chargeback
- Continuous cost optimization processes

### Level 4: Strategic Cost Excellence (Predictive)
- AI-driven cost prediction and optimization
- Dynamic pricing strategy optimization
- Real-time cost optimization and automation
- Cost innovation and business value optimization

## Implementation Strategy

Start with cost visibility and basic optimization, then progressively implement advanced automation and governance practices.

### Phase 1: Foundation (Months 1-3)
1. **Cost Visibility**: Implement comprehensive cost tracking and tagging
2. **Basic Budgets**: Set up budget alerts and monitoring
3. **Right-sizing**: Initial resource right-sizing analysis
4. **Storage Optimization**: Implement basic storage lifecycle policies

### Phase 2: Enhancement (Months 4-6)
1. **Reserved Capacity**: Analyze and implement Reserved Instances/Savings Plans
2. **Automated Scheduling**: Implement resource scheduling for non-production
3. **Spot Instances**: Begin using Spot Instances for appropriate workloads
4. **Cost Allocation**: Implement detailed cost allocation and chargeback

### Phase 3: Optimization (Months 7-12)
1. **Advanced Automation**: Implement intelligent resource lifecycle management
2. **Predictive Analytics**: Use ML for cost forecasting and optimization
3. **Continuous Optimization**: Automated continuous cost optimization
4. **FinOps Culture**: Embed cost optimization in development practices

### Success Metrics
- **Cost Reduction**: Monthly cost savings achieved
- **Resource Efficiency**: Utilization rates and waste reduction
- **Budget Variance**: Actual vs. budgeted costs
- **Time to Optimize**: Speed of cost optimization implementation
- **ROI**: Return on investment for cost optimization initiatives