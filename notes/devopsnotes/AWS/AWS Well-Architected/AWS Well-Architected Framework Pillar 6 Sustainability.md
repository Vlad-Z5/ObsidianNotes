# AWS Well-Architected Framework - Pillar 6: Sustainability

## Strategic Context

Sustainability represents both environmental responsibility and business efficiency. Organizations with strong sustainability practices achieve better resource utilization, reduced operational costs, and improved stakeholder relationships while supporting global environmental goals.

### Business Impact of Sustainability Excellence
- **Environmental Leadership**: Contribute to global climate goals and environmental stewardship
- **Cost Reduction**: 15-25% reduction in operational costs through efficiency improvements
- **Regulatory Compliance**: Meet increasing environmental regulations and reporting requirements
- **Brand Value**: Enhanced reputation and customer loyalty through sustainability leadership
- **Innovation Driver**: Sustainability challenges drive technological innovation and efficiency

### Sustainability Design Principles
1. **Understand your impact**: Measure and monitor environmental impact across the entire workload lifecycle
2. **Establish sustainability goals**: Set long-term sustainability goals and work backwards from them
3. **Maximize utilization**: Right-size workloads and implement efficient design patterns
4. **Anticipate and adopt new hardware and software**: Stay current with energy-efficient technologies
5. **Use managed services**: Leverage cloud provider investments in sustainability infrastructure
6. **Reduce the downstream impact of cloud workloads**: Minimize the energy and resources required by users

## Core Principles and Best Practices

### Energy Efficiency

**Workload Optimization**
Optimize workloads to minimize energy consumption through efficient algorithms, resource scheduling, and capacity planning. Use serverless architectures and auto-scaling to reduce idle resource consumption.

```python
# Example: Sustainable Workload Orchestration
import asyncio
import psutil
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

class SustainableWorkloadManager:
    def __init__(self):
        self.energy_efficiency_targets = {
            'cpu_utilization_min': 70,  # Minimum acceptable CPU utilization
            'memory_utilization_min': 60,  # Minimum acceptable memory utilization
            'carbon_intensity_threshold': 250,  # gCO2/kWh threshold
            'peak_hours': [(9, 17)],  # Business hours for workload scheduling
        }
        self.workload_queue = []
        self.running_workloads = {}
        self.energy_metrics = {
            'total_cpu_hours': 0,
            'total_memory_gb_hours': 0,
            'estimated_carbon_footprint_kg': 0
        }
    
    async def schedule_sustainable_workload(self, 
                                          workload_id: str,
                                          cpu_requirement: int,
                                          memory_requirement_gb: int,
                                          deadline: datetime,
                                          carbon_budget_kg: float = None) -> Dict:
        """Schedule workload considering sustainability metrics"""
        
        current_time = datetime.now()
        current_hour = current_time.hour
        
        # Get current carbon intensity (would integrate with real carbon intensity API)
        carbon_intensity = await self._get_carbon_intensity()
        
        # Calculate optimal execution time
        optimal_time = await self._calculate_optimal_execution_time(
            workload_id, cpu_requirement, memory_requirement_gb, 
            deadline, carbon_intensity
        )
        
        # Check if we should defer workload for better carbon efficiency
        if optimal_time > current_time and optimal_time < deadline:
            delay_minutes = (optimal_time - current_time).total_seconds() / 60
            
            workload_info = {
                'workload_id': workload_id,
                'cpu_requirement': cpu_requirement,
                'memory_requirement_gb': memory_requirement_gb,
                'scheduled_time': optimal_time,
                'carbon_intensity_at_schedule': await self._get_carbon_intensity(optimal_time),
                'estimated_carbon_impact_kg': self._estimate_carbon_impact(
                    cpu_requirement, memory_requirement_gb, 1.0, carbon_intensity
                )
            }
            
            self.workload_queue.append(workload_info)
            
            return {
                'status': 'scheduled',
                'execution_time': optimal_time,
                'delay_minutes': delay_minutes,
                'carbon_savings_kg': self._calculate_carbon_savings(workload_info),
                'reason': 'Deferred for optimal carbon efficiency'
            }
        
        # Execute immediately if optimal time is now or past deadline
        return await self._execute_workload_immediately(
            workload_id, cpu_requirement, memory_requirement_gb
        )
    
    async def _calculate_optimal_execution_time(self,
                                              workload_id: str,
                                              cpu_req: int,
                                              memory_req: int,
                                              deadline: datetime,
                                              current_carbon_intensity: float) -> datetime:
        """Calculate the most carbon-efficient execution time"""
        
        # Get carbon intensity forecast for the next 24 hours
        forecast = await self._get_carbon_intensity_forecast(24)
        
        optimal_time = datetime.now()
        min_carbon_impact = float('inf')
        
        for hour_offset in range(24):
            candidate_time = datetime.now() + timedelta(hours=hour_offset)
            
            # Skip if past deadline
            if candidate_time > deadline:
                continue
            
            # Get carbon intensity for this time
            carbon_intensity = forecast.get(hour_offset, current_carbon_intensity)
            
            # Calculate carbon impact for this time slot
            carbon_impact = self._estimate_carbon_impact(
                cpu_req, memory_req, 1.0, carbon_intensity
            )
            
            # Consider grid load and renewable energy availability
            renewable_factor = self._get_renewable_energy_factor(candidate_time)
            adjusted_carbon_impact = carbon_impact * (1 - renewable_factor)
            
            if adjusted_carbon_impact < min_carbon_impact:
                min_carbon_impact = adjusted_carbon_impact
                optimal_time = candidate_time
        
        return optimal_time
    
    def _estimate_carbon_impact(self, 
                               cpu_cores: int, 
                               memory_gb: int, 
                               duration_hours: float, 
                               carbon_intensity: float) -> float:
        """Estimate carbon footprint for workload execution"""
        
        # Rough estimates based on typical server power consumption
        cpu_power_watts = cpu_cores * 25  # ~25W per CPU core under load
        memory_power_watts = memory_gb * 3  # ~3W per GB of RAM
        base_power_watts = 50  # Base server power consumption
        
        total_power_watts = cpu_power_watts + memory_power_watts + base_power_watts
        total_power_kwh = (total_power_watts * duration_hours) / 1000
        
        # Apply Power Usage Effectiveness (PUE) for datacenter overhead
        pue = 1.4  # Typical cloud datacenter PUE
        total_energy_kwh = total_power_kwh * pue
        
        # Calculate carbon footprint
        carbon_footprint_kg = (total_energy_kwh * carbon_intensity) / 1000
        
        return carbon_footprint_kg
    
    async def _get_carbon_intensity(self, timestamp: datetime = None) -> float:
        """Get current or forecasted carbon intensity (gCO2/kWh)"""
        # In real implementation, this would call a carbon intensity API
        # For now, return simulated values based on time of day
        
        if timestamp is None:
            timestamp = datetime.now()
        
        hour = timestamp.hour
        
        # Simulate lower carbon intensity during off-peak hours
        if 22 <= hour or hour <= 6:  # Night hours
            return 200 + (hour % 12) * 10  # Lower carbon intensity
        elif 9 <= hour <= 17:  # Business hours
            return 350 + (hour - 9) * 15  # Higher carbon intensity
        else:  # Transition hours
            return 275 + (hour % 6) * 20
    
    async def _get_carbon_intensity_forecast(self, hours: int) -> Dict[int, float]:
        """Get carbon intensity forecast for next N hours"""
        forecast = {}
        base_time = datetime.now()
        
        for hour_offset in range(hours):
            future_time = base_time + timedelta(hours=hour_offset)
            forecast[hour_offset] = await self._get_carbon_intensity(future_time)
        
        return forecast
    
    def _get_renewable_energy_factor(self, timestamp: datetime) -> float:
        """Get renewable energy availability factor (0-1)"""
        hour = timestamp.hour
        
        # Simulate higher renewable availability during midday (solar)
        if 10 <= hour <= 16:
            return 0.4 + (0.3 * (1 - abs(hour - 13) / 3))  # Peak at 1 PM
        elif 18 <= hour <= 22:  # Evening wind
            return 0.3
        else:
            return 0.2  # Base renewable availability
    
    def _calculate_carbon_savings(self, workload_info: Dict) -> float:
        """Calculate carbon savings from optimal scheduling"""
        current_carbon_intensity = 300  # Assume current intensity
        scheduled_carbon_intensity = workload_info['carbon_intensity_at_schedule']
        
        current_impact = self._estimate_carbon_impact(
            workload_info['cpu_requirement'],
            workload_info['memory_requirement_gb'],
            1.0,
            current_carbon_intensity
        )
        
        scheduled_impact = workload_info['estimated_carbon_impact_kg']
        
        return max(0, current_impact - scheduled_impact)
    
    async def _execute_workload_immediately(self, 
                                          workload_id: str,
                                          cpu_requirement: int,
                                          memory_requirement_gb: int) -> Dict:
        """Execute workload immediately with sustainability tracking"""
        
        start_time = datetime.now()
        carbon_intensity = await self._get_carbon_intensity()
        
        # Track resource usage
        initial_cpu_percent = psutil.cpu_percent(interval=1)
        initial_memory = psutil.virtual_memory()
        
        # Simulate workload execution (in real implementation, this would orchestrate actual workload)
        await asyncio.sleep(2)  # Simulate work
        
        end_time = datetime.now()
        duration_hours = (end_time - start_time).total_seconds() / 3600
        
        # Calculate actual resource usage and carbon impact
        final_cpu_percent = psutil.cpu_percent(interval=1)
        final_memory = psutil.virtual_memory()
        
        avg_cpu_usage = (initial_cpu_percent + final_cpu_percent) / 2
        carbon_impact = self._estimate_carbon_impact(
            cpu_requirement, memory_requirement_gb, duration_hours, carbon_intensity
        )
        
        # Update sustainability metrics
        self.energy_metrics['total_cpu_hours'] += (avg_cpu_usage / 100) * duration_hours
        self.energy_metrics['total_memory_gb_hours'] += memory_requirement_gb * duration_hours
        self.energy_metrics['estimated_carbon_footprint_kg'] += carbon_impact
        
        return {
            'status': 'completed',
            'execution_time': duration_hours,
            'carbon_impact_kg': carbon_impact,
            'carbon_intensity_gco2_kwh': carbon_intensity,
            'resource_efficiency': self._calculate_resource_efficiency(
                avg_cpu_usage, final_memory.percent
            )
        }
    
    def _calculate_resource_efficiency(self, cpu_percent: float, memory_percent: float) -> Dict:
        """Calculate resource efficiency metrics"""
        return {
            'cpu_efficiency': min(100, (cpu_percent / self.energy_efficiency_targets['cpu_utilization_min']) * 100),
            'memory_efficiency': min(100, (memory_percent / self.energy_efficiency_targets['memory_utilization_min']) * 100),
            'overall_efficiency': (cpu_percent + memory_percent) / 2
        }
    
    def get_sustainability_report(self) -> Dict:
        """Generate sustainability metrics report"""
        total_estimated_energy_kwh = (
            self.energy_metrics['total_cpu_hours'] * 0.025 +  # 25W per CPU hour
            self.energy_metrics['total_memory_gb_hours'] * 0.003  # 3W per GB hour
        )
        
        return {
            'period': 'current_session',
            'metrics': {
                'total_cpu_hours': self.energy_metrics['total_cpu_hours'],
                'total_memory_gb_hours': self.energy_metrics['total_memory_gb_hours'],
                'estimated_energy_consumption_kwh': total_estimated_energy_kwh,
                'estimated_carbon_footprint_kg': self.energy_metrics['estimated_carbon_footprint_kg'],
                'carbon_intensity_average_gco2_kwh': self.energy_metrics['estimated_carbon_footprint_kg'] / max(total_estimated_energy_kwh, 0.001) * 1000
            },
            'efficiency_targets': self.energy_efficiency_targets,
            'recommendations': self._generate_sustainability_recommendations()
        }
    
    def _generate_sustainability_recommendations(self) -> List[str]:
        """Generate sustainability improvement recommendations"""
        recommendations = []
        
        if self.energy_metrics['total_cpu_hours'] > 0:
            avg_utilization = (self.energy_metrics['total_cpu_hours'] / 
                             max(1, len(self.running_workloads))) * 100
            
            if avg_utilization < self.energy_efficiency_targets['cpu_utilization_min']:
                recommendations.append(
                    f"Consider consolidating workloads to improve CPU utilization "
                    f"(current: {avg_utilization:.1f}%, target: {self.energy_efficiency_targets['cpu_utilization_min']}%)"
                )
        
        recommendations.extend([
            "Use serverless architectures for variable workloads to minimize idle resources",
            "Schedule non-urgent workloads during low carbon intensity periods",
            "Implement auto-scaling to match resource provisioning with actual demand",
            "Consider using ARM-based instances for improved energy efficiency"
        ])
        
        return recommendations

# Usage Example
async def demonstrate_sustainable_workloads():
    manager = SustainableWorkloadManager()
    
    # Schedule various workloads
    workload1_result = await manager.schedule_sustainable_workload(
        workload_id="data-processing-1",
        cpu_requirement=4,
        memory_requirement_gb=8,
        deadline=datetime.now() + timedelta(hours=6)
    )
    
    workload2_result = await manager.schedule_sustainable_workload(
        workload_id="ml-training-1",
        cpu_requirement=8,
        memory_requirement_gb=16,
        deadline=datetime.now() + timedelta(hours=12)
    )
    
    print("Workload 1 Result:", workload1_result)
    print("Workload 2 Result:", workload2_result)
    
    # Generate sustainability report
    report = manager.get_sustainability_report()
    print("\\nSustainability Report:")
    print(f"Total Carbon Footprint: {report['metrics']['estimated_carbon_footprint_kg']:.4f} kg CO2")
    print(f"Energy Consumption: {report['metrics']['estimated_energy_consumption_kwh']:.4f} kWh")
    print("\\nRecommendations:")
    for rec in report['recommendations']:
        print(f"- {rec}")

# Run the demonstration
# asyncio.run(demonstrate_sustainable_workloads())
```

**Data Center Efficiency**
Choose cloud providers and data centers with strong sustainability practices including renewable energy usage and efficient cooling systems. Consider geographic distribution for optimal energy efficiency.

```terraform
# Example: Sustainable Infrastructure Deployment
variable "sustainability_requirements" {
  description = "Sustainability requirements for infrastructure"
  type = object({
    renewable_energy_percentage = number
    carbon_intensity_threshold  = number
    pue_requirement            = number
    sustainability_reporting   = bool
  })
  default = {
    renewable_energy_percentage = 80
    carbon_intensity_threshold  = 250
    pue_requirement            = 1.4
    sustainability_reporting   = true
  }
}

# Data source for sustainable regions
data "aws_regions" "sustainable" {
  all_regions = true
  
  filter {
    name   = "opt-in-status"
    values = ["opt-in-not-required", "opted-in"]
  }
}

# Local values for sustainable region selection
locals {
  # Prioritize regions with high renewable energy usage
  sustainable_regions = {
    "us-west-2"    = { renewable_percentage = 95, carbon_intensity = 180, pue = 1.2 }
    "us-west-1"    = { renewable_percentage = 85, carbon_intensity = 200, pue = 1.3 }
    "ca-central-1" = { renewable_percentage = 90, carbon_intensity = 160, pue = 1.25 }
    "eu-west-1"    = { renewable_percentage = 75, carbon_intensity = 220, pue = 1.35 }
    "eu-north-1"   = { renewable_percentage = 98, carbon_intensity = 120, pue = 1.15 }
    "ap-southeast-2" = { renewable_percentage = 70, carbon_intensity = 240, pue = 1.4 }
  }
  
  # Filter regions based on sustainability requirements
  qualified_regions = {
    for region, metrics in local.sustainable_regions :
    region => metrics
    if metrics.renewable_percentage >= var.sustainability_requirements.renewable_energy_percentage &&
       metrics.carbon_intensity <= var.sustainability_requirements.carbon_intensity_threshold &&
       metrics.pue <= var.sustainability_requirements.pue_requirement
  }
  
  # Select the most sustainable region
  primary_region = keys(local.qualified_regions)[0]
}

# Sustainable compute instances
resource "aws_launch_template" "sustainable_compute" {
  name_prefix   = "sustainable-compute"
  image_id      = data.aws_ami.arm_based.id  # ARM-based instances for better efficiency
  instance_type = "m6g.large"  # Graviton2 instances use ~20% less energy
  
  vpc_security_group_ids = [aws_security_group.sustainable.id]
  
  # Enable detailed monitoring for better optimization
  monitoring {
    enabled = true
  }
  
  # Use GP3 volumes for better price/performance
  block_device_mappings {
    device_name = "/dev/xvda"
    ebs {
      volume_type = "gp3"
      volume_size = 20
      iops        = 3000
      throughput  = 125
      encrypted   = true
      
      tags = {
        SustainabilityOptimized = "true"
        VolumeType              = "gp3-optimized"
      }
    }
  }
  
  tag_specifications {
    resource_type = "instance"
    tags = {
      Name                    = "sustainable-compute-instance"
      SustainabilityOptimized = "true"
      CarbonAware            = "true"
      EnergyEfficient        = "true"
      Region                 = local.primary_region
      RenewableEnergy        = local.qualified_regions[local.primary_region].renewable_percentage
    }
  }
  
  user_data = base64encode(templatefile("${path.module}/sustainable_userdata.sh", {
    enable_power_management = true
    cpu_governor           = "powersave"
    enable_monitoring      = true
  }))
}

# Auto Scaling Group with sustainability-aware scaling
resource "aws_autoscaling_group" "sustainable" {
  name             = "sustainable-asg"
  min_size         = 1
  max_size         = 20
  desired_capacity = 2
  
  vpc_zone_identifier = data.aws_subnets.sustainable.ids
  
  launch_template {
    id      = aws_launch_template.sustainable_compute.id
    version = "$Latest"
  }
  
  # Health check configuration
  health_check_type         = "ELB"
  health_check_grace_period = 300
  
  # Termination policies to optimize for sustainability
  termination_policies = ["OldestInstance", "Default"]
  
  # Enable instance refresh for gradual updates
  instance_refresh {
    strategy = "Rolling"
    preferences {
      min_healthy_percentage = 50
      instance_warmup       = 300
    }
  }
  
  tag {
    key                 = "Name"
    value               = "sustainable-compute"
    propagate_at_launch = true
  }
  
  tag {
    key                 = "SustainabilityOptimized"
    value               = "true"
    propagate_at_launch = true
  }
  
  tag {
    key                 = "CarbonAware"
    value               = "true"
    propagate_at_launch = true
  }
}

# Sustainability-aware Application Load Balancer
resource "aws_lb" "sustainable" {
  name               = "sustainable-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.sustainable.id]
  subnets           = data.aws_subnets.sustainable.ids
  
  enable_deletion_protection = false
  enable_http2              = true
  
  # Enable access logs for sustainability analysis
  access_logs {
    bucket  = aws_s3_bucket.sustainability_logs.bucket
    prefix  = "alb-logs"
    enabled = true
  }
  
  tags = {
    Name                    = "sustainable-alb"
    SustainabilityOptimized = "true"
    EnergyEfficient        = "true"
  }
}

# S3 bucket with intelligent tiering for sustainability
resource "aws_s3_bucket" "sustainability_logs" {
  bucket = "sustainability-logs-${random_string.bucket_suffix.result}"
  
  tags = {
    Purpose                 = "SustainabilityLogging"
    SustainabilityOptimized = "true"
  }
}

resource "aws_s3_bucket_intelligent_tiering_configuration" "sustainability_logs" {
  bucket = aws_s3_bucket.sustainability_logs.id
  name   = "EntireBucket"
  
  tiering {
    access_tier = "ARCHIVE_ACCESS"
    days        = 90
  }
  
  tiering {
    access_tier = "DEEP_ARCHIVE_ACCESS"
    days        = 180
  }
}

# Random string for unique bucket naming
resource "random_string" "bucket_suffix" {
  length  = 8
  special = false
  upper   = false
}

# CloudWatch dashboard for sustainability metrics
resource "aws_cloudwatch_dashboard" "sustainability" {
  dashboard_name = "Sustainability-Metrics"
  
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
            ["AWS/EC2", "CPUUtilization", "AutoScalingGroupName", aws_autoscaling_group.sustainable.name],
            ["AWS/ApplicationELB", "RequestCount", "LoadBalancer", aws_lb.sustainable.arn_suffix],
            ["AWS/ApplicationELB", "TargetResponseTime", "LoadBalancer", aws_lb.sustainable.arn_suffix]
          ]
          period = 300
          stat   = "Average"
          region = local.primary_region
          title  = "Sustainability Metrics"
          view   = "timeSeries"
          annotations = {
            horizontal = [
              {
                label = "CPU Efficiency Target (70%)"
                value = 70
              }
            ]
          }
        }
      }
    ]
  })
}

# Output sustainability information
output "sustainability_report" {
  description = "Sustainability configuration report"
  value = {
    primary_region          = local.primary_region
    renewable_energy_percentage = local.qualified_regions[local.primary_region].renewable_percentage
    carbon_intensity       = local.qualified_regions[local.primary_region].carbon_intensity
    pue                   = local.qualified_regions[local.primary_region].pue
    instance_types        = ["m6g.large"]  # ARM-based for efficiency
    storage_optimization  = "gp3-with-intelligent-tiering"
    auto_scaling_enabled  = true
    sustainability_monitoring = "enabled"
  }
}
```

**Carbon Footprint Management**
Implement carbon footprint tracking and reduction strategies. Use sustainability metrics alongside traditional performance and cost metrics in architectural decisions.

```python
# Example: Comprehensive Carbon Footprint Tracking
import json
import boto3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import pandas as pd

class CarbonFootprintTracker:
    def __init__(self):
        self.ce_client = boto3.client('ce')  # Cost Explorer
        self.cloudwatch_client = boto3.client('cloudwatch')
        self.ec2_client = boto3.client('ec2')
        
        # Carbon intensity factors by region (gCO2/kWh)
        self.regional_carbon_intensity = {
            'us-east-1': 390,      # Virginia - mixed grid
            'us-east-2': 350,      # Ohio - mixed grid
            'us-west-1': 220,      # N. California - high renewable
            'us-west-2': 180,      # Oregon - very high renewable
            'ca-central-1': 160,   # Canada - hydro power
            'eu-west-1': 220,      # Ireland - wind + mixed
            'eu-north-1': 120,     # Stockholm - very high renewable
            'eu-central-1': 280,   # Frankfurt - mixed grid
            'ap-southeast-1': 450, # Singapore - fossil heavy
            'ap-southeast-2': 240, # Sydney - mixed grid
            'ap-northeast-1': 350, # Tokyo - mixed grid
        }
        
        # Power consumption estimates (Watts) by instance family
        self.instance_power_consumption = {
            # CPU-optimized instances
            'c5.large': 45, 'c5.xlarge': 90, 'c5.2xlarge': 180,
            'c6g.large': 35, 'c6g.xlarge': 70, 'c6g.2xlarge': 140,  # ARM - more efficient
            
            # General purpose instances
            'm5.large': 50, 'm5.xlarge': 100, 'm5.2xlarge': 200,
            'm6g.large': 40, 'm6g.xlarge': 80, 'm6g.2xlarge': 160,  # ARM - more efficient
            
            # Memory optimized instances
            'r5.large': 60, 'r5.xlarge': 120, 'r5.2xlarge': 240,
            'r6g.large': 45, 'r6g.xlarge': 90, 'r6g.2xlarge': 180,  # ARM - more efficient
            
            # Storage optimized instances
            'i3.large': 70, 'i3.xlarge': 140, 'i3.2xlarge': 280,
            
            # GPU instances
            'p3.2xlarge': 400, 'p3.8xlarge': 1600,
            'g4dn.xlarge': 180, 'g4dn.2xlarge': 360,
        }
    
    def calculate_instance_carbon_footprint(self, 
                                          instance_type: str,
                                          region: str,
                                          runtime_hours: float,
                                          cpu_utilization: float = 0.7) -> Dict:
        """Calculate carbon footprint for EC2 instance usage"""
        
        base_power = self.instance_power_consumption.get(instance_type, 100)  # Default 100W
        carbon_intensity = self.regional_carbon_intensity.get(region, 300)  # Default 300 gCO2/kWh
        
        # Adjust power consumption based on CPU utilization
        actual_power = base_power * (0.3 + 0.7 * cpu_utilization)  # 30% base + 70% variable
        
        # Calculate energy consumption
        energy_kwh = (actual_power * runtime_hours) / 1000
        
        # Apply datacenter Power Usage Effectiveness (PUE)
        pue = 1.4  # Typical cloud datacenter PUE
        total_energy_kwh = energy_kwh * pue
        
        # Calculate carbon footprint
        carbon_footprint_kg = (total_energy_kwh * carbon_intensity) / 1000
        
        return {
            'instance_type': instance_type,
            'region': region,
            'runtime_hours': runtime_hours,
            'cpu_utilization': cpu_utilization,
            'base_power_watts': base_power,
            'actual_power_watts': actual_power,
            'energy_consumption_kwh': energy_kwh,
            'total_energy_with_pue_kwh': total_energy_kwh,
            'carbon_intensity_gco2_kwh': carbon_intensity,
            'carbon_footprint_kg': carbon_footprint_kg,
            'carbon_footprint_g': carbon_footprint_kg * 1000
        }
    
    def get_fleet_carbon_footprint(self, 
                                  start_date: str, 
                                  end_date: str,
                                  tag_filters: Dict = None) -> Dict:
        """Calculate carbon footprint for entire EC2 fleet"""
        
        try:
            # Get usage data from Cost Explorer
            filter_dict = {
                'Dimensions': {
                    'Key': 'SERVICE',
                    'Values': ['Amazon Elastic Compute Cloud - Compute']
                }
            }
            
            # Add tag filters if provided
            if tag_filters:
                and_filters = [filter_dict]
                for tag_key, tag_values in tag_filters.items():
                    and_filters.append({
                        'Tags': {
                            'Key': tag_key,
                            'Values': tag_values if isinstance(tag_values, list) else [tag_values]
                        }
                    })
                filter_dict = {'And': and_filters}
            
            response = self.ce_client.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date,
                    'End': end_date
                },
                Granularity='DAILY',
                Metrics=['UsageQuantity'],
                GroupBy=[
                    {'Type': 'DIMENSION', 'Key': 'INSTANCE_TYPE'},
                    {'Type': 'DIMENSION', 'Key': 'REGION'}
                ],
                Filter=filter_dict
            )
            
            total_carbon_footprint = 0
            detailed_breakdown = []
            
            for result in response['ResultsByTime']:
                date = result['TimePeriod']['Start']
                
                for group in result['Groups']:
                    if len(group['Keys']) >= 2:
                        instance_type = group['Keys'][0]
                        region = group['Keys'][1]
                        usage_hours = float(group['Metrics']['UsageQuantity']['Amount'])
                        
                        if usage_hours > 0:
                            # Get average CPU utilization (would need CloudWatch integration)
                            avg_cpu_utilization = self._get_average_cpu_utilization(
                                instance_type, region, date
                            )
                            
                            carbon_calc = self.calculate_instance_carbon_footprint(
                                instance_type, region, usage_hours, avg_cpu_utilization
                            )
                            
                            carbon_calc['date'] = date
                            detailed_breakdown.append(carbon_calc)
                            total_carbon_footprint += carbon_calc['carbon_footprint_kg']
            
            return {
                'status': 'success',
                'period': f"{start_date} to {end_date}",
                'total_carbon_footprint_kg': total_carbon_footprint,
                'total_carbon_footprint_tons': total_carbon_footprint / 1000,
                'detailed_breakdown': detailed_breakdown,
                'summary_by_region': self._summarize_by_region(detailed_breakdown),
                'summary_by_instance_type': self._summarize_by_instance_type(detailed_breakdown)
            }
            
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def _get_average_cpu_utilization(self, 
                                   instance_type: str, 
                                   region: str, 
                                   date: str) -> float:
        """Get average CPU utilization for instance type in region on date"""
        # In real implementation, this would query CloudWatch metrics
        # For now, return estimated utilization based on instance type
        
        utilization_estimates = {
            'c5': 0.75,   # CPU-optimized typically higher utilization
            'c6g': 0.75,
            'm5': 0.65,   # General purpose moderate utilization
            'm6g': 0.65,
            'r5': 0.60,   # Memory-optimized often lower CPU utilization
            'r6g': 0.60,
            'i3': 0.70,   # Storage-optimized variable
            'p3': 0.85,   # GPU instances typically high utilization
            'g4dn': 0.80
        }
        
        instance_family = instance_type.split('.')[0]
        return utilization_estimates.get(instance_family, 0.70)  # Default 70%
    
    def _summarize_by_region(self, breakdown: List[Dict]) -> Dict:
        """Summarize carbon footprint by region"""
        region_summary = {}
        
        for item in breakdown:
            region = item['region']
            if region not in region_summary:
                region_summary[region] = {
                    'total_carbon_kg': 0,
                    'total_energy_kwh': 0,
                    'total_runtime_hours': 0,
                    'carbon_intensity': item['carbon_intensity_gco2_kwh']
                }
            
            region_summary[region]['total_carbon_kg'] += item['carbon_footprint_kg']
            region_summary[region]['total_energy_kwh'] += item['total_energy_with_pue_kwh']
            region_summary[region]['total_runtime_hours'] += item['runtime_hours']
        
        return region_summary
    
    def _summarize_by_instance_type(self, breakdown: List[Dict]) -> Dict:
        """Summarize carbon footprint by instance type"""
        instance_summary = {}
        
        for item in breakdown:
            instance_type = item['instance_type']
            if instance_type not in instance_summary:
                instance_summary[instance_type] = {
                    'total_carbon_kg': 0,
                    'total_energy_kwh': 0,
                    'total_runtime_hours': 0,
                    'avg_power_watts': item['actual_power_watts']
                }
            
            instance_summary[instance_type]['total_carbon_kg'] += item['carbon_footprint_kg']
            instance_summary[instance_type]['total_energy_kwh'] += item['total_energy_with_pue_kwh']
            instance_summary[instance_type]['total_runtime_hours'] += item['runtime_hours']
        
        return instance_summary
    
    def generate_sustainability_recommendations(self, 
                                              carbon_footprint_data: Dict) -> List[Dict]:
        """Generate recommendations to reduce carbon footprint"""
        recommendations = []
        
        if carbon_footprint_data['status'] == 'success':
            region_summary = carbon_footprint_data['summary_by_region']
            instance_summary = carbon_footprint_data['summary_by_instance_type']
            
            # Region optimization recommendations
            high_carbon_regions = [
                region for region, data in region_summary.items()
                if data['carbon_intensity'] > 300
            ]
            
            if high_carbon_regions:
                total_high_carbon = sum(
                    region_summary[region]['total_carbon_kg']
                    for region in high_carbon_regions
                )
                
                recommendations.append({
                    'type': 'region_optimization',
                    'priority': 'high',
                    'impact_kg_co2': total_high_carbon * 0.4,  # Estimated 40% reduction
                    'description': f"Migrate workloads from high-carbon regions: {', '.join(high_carbon_regions)}",
                    'recommended_regions': ['us-west-2', 'eu-north-1', 'ca-central-1'],
                    'implementation_effort': 'medium'
                })
            
            # Instance type optimization recommendations
            x86_instances = [
                inst_type for inst_type in instance_summary.keys()
                if not any(arm_family in inst_type for arm_family in ['6g', '7g'])
            ]
            
            if x86_instances:
                total_x86_carbon = sum(
                    instance_summary[inst_type]['total_carbon_kg']
                    for inst_type in x86_instances
                )
                
                recommendations.append({
                    'type': 'instance_optimization',
                    'priority': 'medium',
                    'impact_kg_co2': total_x86_carbon * 0.2,  # Estimated 20% reduction with ARM
                    'description': 'Migrate to ARM-based instances (Graviton2/3) for better energy efficiency',
                    'current_instances': x86_instances,
                    'recommended_instances': {
                        'm5.large': 'm6g.large',
                        'm5.xlarge': 'm6g.xlarge',
                        'c5.large': 'c6g.large',
                        'c5.xlarge': 'c6g.xlarge',
                        'r5.large': 'r6g.large',
                        'r5.xlarge': 'r6g.xlarge'
                    },
                    'implementation_effort': 'low'
                })
            
            # Utilization optimization
            low_utilization_instances = [
                inst_type for inst_type, data in instance_summary.items()
                if (data['total_runtime_hours'] > 0 and 
                    data['total_energy_kwh'] / data['total_runtime_hours'] < 0.05)  # Low energy/hour ratio
            ]
            
            if low_utilization_instances:
                recommendations.append({
                    'type': 'utilization_optimization',
                    'priority': 'high',
                    'impact_kg_co2': carbon_footprint_data['total_carbon_footprint_kg'] * 0.3,
                    'description': 'Improve resource utilization through right-sizing and auto-scaling',
                    'target_instances': low_utilization_instances,
                    'recommended_actions': [
                        'Implement auto-scaling based on demand',
                        'Right-size instances based on actual usage',
                        'Use Spot instances for batch workloads',
                        'Implement workload scheduling during low-carbon periods'
                    ],
                    'implementation_effort': 'medium'
                })
        
        return sorted(recommendations, key=lambda x: x['impact_kg_co2'], reverse=True)
    
    def generate_carbon_footprint_report(self, 
                                       start_date: str, 
                                       end_date: str,
                                       include_recommendations: bool = True) -> Dict:
        """Generate comprehensive carbon footprint report"""
        
        # Get overall fleet footprint
        fleet_data = self.get_fleet_carbon_footprint(start_date, end_date)
        
        if fleet_data['status'] != 'success':
            return fleet_data
        
        # Calculate equivalent metrics for context
        carbon_kg = fleet_data['total_carbon_footprint_kg']
        equivalent_metrics = {
            'tree_seedlings_grown_for_10_years': int(carbon_kg / 0.060),  # 60g CO2/seedling/year
            'miles_driven_by_average_car': int(carbon_kg / 0.411),        # 411g CO2/mile
            'gallons_of_gasoline_consumed': carbon_kg / 8.887,            # 8.887 kg CO2/gallon
            'smartphones_charged': int(carbon_kg / 0.012),                # 12g CO2/charge
        }
        
        report = {
            'report_metadata': {
                'generated_at': datetime.now().isoformat(),
                'period': fleet_data['period'],
                'scope': 'AWS EC2 Infrastructure'
            },
            'executive_summary': {
                'total_carbon_footprint_kg': carbon_kg,
                'total_carbon_footprint_tons': fleet_data['total_carbon_footprint_tons'],
                'equivalent_metrics': equivalent_metrics,
                'primary_carbon_sources': self._identify_primary_sources(fleet_data)
            },
            'detailed_analysis': {
                'by_region': fleet_data['summary_by_region'],
                'by_instance_type': fleet_data['summary_by_instance_type'],
                'daily_breakdown': fleet_data['detailed_breakdown']
            }
        }
        
        if include_recommendations:
            recommendations = self.generate_sustainability_recommendations(fleet_data)
            total_potential_reduction = sum(rec['impact_kg_co2'] for rec in recommendations)
            
            report['recommendations'] = {
                'total_potential_reduction_kg': total_potential_reduction,
                'potential_reduction_percentage': (total_potential_reduction / carbon_kg) * 100,
                'action_items': recommendations
            }
        
        return report
    
    def _identify_primary_sources(self, fleet_data: Dict) -> List[Dict]:
        """Identify primary sources of carbon emissions"""
        region_summary = fleet_data['summary_by_region']
        instance_summary = fleet_data['summary_by_instance_type']
        
        # Top regions by carbon footprint
        top_regions = sorted(
            region_summary.items(),
            key=lambda x: x[1]['total_carbon_kg'],
            reverse=True
        )[:3]
        
        # Top instance types by carbon footprint
        top_instances = sorted(
            instance_summary.items(),
            key=lambda x: x[1]['total_carbon_kg'],
            reverse=True
        )[:3]
        
        return {
            'top_carbon_regions': [
                {
                    'region': region,
                    'carbon_kg': data['total_carbon_kg'],
                    'percentage': (data['total_carbon_kg'] / fleet_data['total_carbon_footprint_kg']) * 100
                }
                for region, data in top_regions
            ],
            'top_carbon_instance_types': [
                {
                    'instance_type': inst_type,
                    'carbon_kg': data['total_carbon_kg'],
                    'percentage': (data['total_carbon_kg'] / fleet_data['total_carbon_footprint_kg']) * 100
                }
                for inst_type, data in top_instances
            ]
        }

# Usage Example
def demonstrate_carbon_tracking():
    tracker = CarbonFootprintTracker()
    
    # Calculate carbon footprint for specific instance
    single_instance = tracker.calculate_instance_carbon_footprint(
        instance_type='m5.large',
        region='us-east-1',
        runtime_hours=720,  # 30 days
        cpu_utilization=0.65
    )
    
    print("Single Instance Carbon Footprint:")
    print(f"Instance: {single_instance['instance_type']} in {single_instance['region']}")
    print(f"Carbon Footprint: {single_instance['carbon_footprint_kg']:.3f} kg CO2")
    print(f"Energy Consumption: {single_instance['total_energy_with_pue_kwh']:.2f} kWh")
    
    # Generate fleet report
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    
    report = tracker.generate_carbon_footprint_report(start_date, end_date)
    
    if report.get('executive_summary'):
        print(f"\\nFleet Carbon Footprint: {report['executive_summary']['total_carbon_footprint_kg']:.2f} kg CO2")
        print(f"Equivalent to {report['executive_summary']['equivalent_metrics']['miles_driven_by_average_car']} miles driven")
        
        if report.get('recommendations'):
            print(f"\\nPotential Reduction: {report['recommendations']['potential_reduction_percentage']:.1f}%")
            print("Top Recommendations:")
            for rec in report['recommendations']['action_items'][:3]:
                print(f"- {rec['description']} (Impact: {rec['impact_kg_co2']:.2f} kg CO2)")

# Run demonstration
demonstrate_carbon_tracking()
```

### Resource Lifecycle Management

**Circular Economy Principles**
Implement resource sharing, reuse, and recycling strategies. Use multi-tenant architectures and shared services to maximize resource utilization.

**Sustainable Development Practices**
Integrate sustainability considerations into development processes including code efficiency, testing optimization, and deployment strategies.

## Key Tools and Implementation

### Sustainability Monitoring and Optimization
- **Carbon Tracking**: Cloud provider sustainability dashboards, carbon footprint calculators
- **Energy Monitoring**: Power usage effectiveness monitoring, energy consumption analytics
- **Resource Efficiency**: Utilization monitoring, efficiency optimization tools
- **Sustainable Architecture**: Green software development practices, efficiency-focused design patterns

### Cloud Provider Sustainability Tools
- **AWS Carbon Footprint Tool**: Track and reduce carbon emissions
- **Google Cloud Carbon Footprint**: Detailed carbon impact reporting
- **Microsoft Sustainability Calculator**: Azure carbon footprint analysis
- **Third-party Tools**: CloudZero, CloudHealth sustainability features

## Sustainability Maturity Assessment

### Level 1: Basic Awareness (Reactive)
- Limited sustainability tracking
- Basic energy efficiency practices
- Minimal consideration in architectural decisions
- Ad-hoc sustainability initiatives

### Level 2: Managed Sustainability (Proactive)
- Regular sustainability reporting
- Energy-efficient infrastructure choices
- Sustainability metrics in operations
- Basic carbon footprint tracking

### Level 3: Advanced Sustainability (Integrated)
- Comprehensive carbon footprint management
- Sustainability-driven architectural decisions
- Automated optimization for energy efficiency
- Integration with business sustainability goals

### Level 4: Sustainability Leadership (Innovative)
- Carbon-neutral or carbon-negative operations
- Industry-leading sustainability practices
- Innovation in sustainable technologies
- Sustainability as competitive advantage

## Implementation Strategy

Begin with energy efficiency improvements and resource optimization, then progressively implement comprehensive sustainability practices and carbon footprint management.

### Phase 1: Foundation (Months 1-3)
1. **Sustainability Assessment**: Baseline carbon footprint and energy usage
2. **Efficient Infrastructure**: ARM instances, GP3 storage, sustainable regions
3. **Basic Monitoring**: Energy and sustainability metrics tracking
4. **Resource Optimization**: Right-sizing and utilization improvements

### Phase 2: Enhancement (Months 4-6)
1. **Carbon Tracking**: Comprehensive carbon footprint monitoring
2. **Sustainable Scheduling**: Workload scheduling based on carbon intensity
3. **Green Regions**: Prioritize regions with renewable energy
4. **Lifecycle Management**: Automated resource lifecycle optimization

### Phase 3: Optimization (Months 7-12)
1. **Carbon-Aware Computing**: Real-time carbon intensity optimization
2. **Sustainable Architecture**: Design patterns for environmental efficiency
3. **Supply Chain**: Sustainable vendor and service selection
4. **Innovation**: Advanced sustainability technologies and practices

### Success Metrics
- **Carbon Footprint**: Total CO2 emissions reduction
- **Energy Efficiency**: kWh per workload or transaction
- **Resource Utilization**: Compute and storage efficiency rates
- **Renewable Energy**: Percentage of renewable energy usage
- **Sustainability ROI**: Cost savings from sustainability initiatives