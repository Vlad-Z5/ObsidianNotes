# AWS EC2 (Elastic Compute Cloud)

> **Service Type:** Compute | **Scope:** Regional | **Serverless:** No

## Overview

Amazon EC2 provides scalable virtual servers in the cloud, forming the backbone of most AWS deployments. It offers complete control over computing resources with pay-as-you-use pricing.

## DevOps & Enterprise Use Cases

### Infrastructure Hosting
- **Web servers** running applications (Apache, Nginx, IIS)
- **Application servers** (Tomcat, Node.js, .NET)
- **Database servers** when managed services aren't suitable
- **CI/CD build agents** for compilation and testing

### Container Orchestration
- **ECS container instances** running Docker workloads
- **EKS worker nodes** for Kubernetes clusters
- **Self-managed Docker hosts** with custom orchestration

### Development & Testing
- **Development environments** with on-demand provisioning
- **Testing infrastructure** that scales with demand
- **Performance testing** with consistent baseline environments

### Automation & Tooling
- **Bastion hosts** for secure administrative access
- **NAT instances** for custom network routing (where NAT Gateway insufficient)
- **Monitoring servers** running Prometheus, Grafana, ELK stack

## Core Architecture Components

- **AMI (Amazon Machine Image):** Template containing OS, application software, and configuration. Region specific, can be copied across regions
- **Instance Type:** Defines CPU, memory, storage, and network capacity (e.g., t3.medium)
- **EBS (Elastic Block Store):** Persistent block storage volumes that attach to instances
- **Instance Store (Ephemeral Storage):** Temporary storage physically attached to host, data lost on stop/terminate. Best IO, good for buffer/cache/tmp
- **Security Groups:** Virtual firewalls controlling inbound/outbound traffic
- **Key Pair:** SSH credentials to securely access Linux instances
- **Elastic IP:** Static, public IPv4 address for dynamic cloud computing
- **Network Interface (ENI):** Virtual network card attached to an instance
- **VPC/Subnet:** Network isolation units defining IP range and placement
- **User Data:** Script or commands run on instance launch for initialisation
- **Placement Group:** Controls instance placement strategy (cluster, spread, partition)
- **Elastic Load Balancer (ELB):** Distributes incoming traffic across instances
- **Auto Scaling Group (ASG):** Automatically adjusts instance count based on demand

## Service Features & Capabilities

### **Instance Family Types**

- **General Purpose:** `t4g` (Graviton2), `t3` / `t3a` (Burstable), `m6i` / `m6a` / `m7i`
- **Compute Optimized:** `c6g` / `c6i` / `c7i`
- **Memory Optimized:** `r6i` / `r6a` / `r7i`, `x2idn` / `x2iedn` (High Memory)
- **Storage Optimized:** `i4i` / `i3` (High IOPS), `d3` / `d3en` (Dense HDD)
- **GPU Optimized:** `g4dn` / `g5` (General Purpose), `p3` / `p4` (ML Training)
- **Machine Learning Inference Optimized:** `inf1`
- **High Performance Computing Optimized:** `hpc6id` / `hpc6a`

### **Instance Sizing Convention**

- **Format:** `[family][generation][additional capabilities].[size]`
- **Example:** `m5.large` = General purpose (m), 5th gen, large size
- **Sizes:** `nano`, `micro`, `small`, `medium`, `large`, `xlarge`, `2xlarge`, `4xlarge`, etc.

## **Purchasing Options**

- **Reserved Instances (RI):** Specific **type**, **region**, **tenancy**, **OS**. Scope can be **regional** or **Availability Zone (AZ)**. Terms: **1 or 3 years**
    - **Convertible RI** allows changes to instance family, OS, tenancy, and region
    - **Standard RI** offers higher discount but less flexibility
- **On-Demand:** Pay for compute capacity by the **second** (Windows, Linux) or **hour** (other OS) without long-term commitments
- **Spot Instances:** Use spare capacity at up to 90% discount, can be interrupted. **2 min termination notice** via CloudWatch or instance metadata
- **Dedicated Instance:** EC2 runs on hardware dedicated to a single tenant but shared host. Shared hardware.
- **Dedicated Host:** Physical server fully dedicated to your use. Visibility into sockets, cores, and host ID.
- **Capacity Reservations:** Reserve capacity in a specific AZ for your EC2 instance types
- **Savings Plans:**
    - **Compute Savings Plan:** Applies to EC2, Fargate, Lambda across any region and family
    - **EC2 Instance Savings Plan:** Limited to a specific instance family in a region
    - Both require **1- or 3-year** commitment with **per-hour** billing

## **Storage Options**

### **EBS Volume Types**

- **gp3 (General Purpose SSD):** Latest generation, 3,000-16,000 IOPS, 125-1,000 MB/s throughput
- **gp2 (General Purpose SSD):** Baseline 3 IOPS/GB, burst to 3,000 IOPS
- **io2/io2 Block Express (Provisioned IOPS SSD):** Up to 64,000 IOPS, 99.999% durability
- **io1 (Provisioned IOPS SSD):** Up to 32,000 IOPS, for I/O intensive workloads
- **st1 (Throughput Optimized HDD):** Low cost, frequently accessed workloads
- **sc1 (Cold HDD):** Lowest cost, less frequently accessed workloads

### **EBS Features**

- **Snapshots:** Point-in-time backups stored in S3, incremental
- **Encryption:** At rest and in transit, uses AWS KMS keys
- **Multi-Attach:** Attach single EBS volume to multiple instances (io1/io2 only)
- **Fast Snapshot Restore:** Eliminates latency when restoring from snapshots

### **Instance Store**

- **Characteristics:** High-speed NVMe SSD, ephemeral, included in instance price
- **Use Cases:** Temporary storage, cache, buffer, scratch data
- **Limitations:** Data lost on stop/terminate, hibernate, or instance failure

## **Networking**

### **Security Groups**

- **Stateful:** Return traffic automatically allowed
- **Default Deny:** All inbound traffic blocked by default
- **Allow Rules Only:** Cannot create deny rules
- **Multiple Groups:** Instance can have multiple security groups
- **Source/Destination:** Can reference IP ranges, other security groups, or prefix lists

### **Network Interfaces (ENI)**

- **Primary ENI:** Cannot be detached from instance
- **Secondary ENI:** Can be detached and attached to other instances
- **Attributes:** Private IP, Elastic IP, MAC address, security groups
- **Use Cases:** Management networks, network appliances, dual-homed instances

### **Enhanced Networking**

- **SR-IOV:** Single Root I/O Virtualization for higher bandwidth and lower latency
- **Elastic Network Adapter (ENA):** Up to 100 Gbps network performance
- **Intel 82599 VF:** Legacy enhanced networking option

### **Placement Groups**

- **Cluster:** Packs instances close together in a single AZ for low latency and high throughput
- **Spread:** Distributes instances across different hardware (max 7 per AZ)
- **Partition:** Divides group into partitions with separate hardware (up to 7 partitions per AZ)

## Configuration & Setup

### **Launch Templates and Configuration**

```bash
# Create launch template
aws ec2 create-launch-template \
  --launch-template-name WebServerTemplate \
  --launch-template-data '{
    "ImageId": "ami-0abcdef1234567890",
    "InstanceType": "t3.medium",
    "KeyName": "my-key-pair",
    "SecurityGroupIds": ["sg-12345678"],
    "UserData": "'$(base64 -w 0 user-data.sh)'",
    "IamInstanceProfile": {
      "Name": "EC2-SSM-Role"
    },
    "BlockDeviceMappings": [{
      "DeviceName": "/dev/xvda",
      "Ebs": {
        "VolumeSize": 20,
        "VolumeType": "gp3",
        "Encrypted": true
      }
    }]
  }'
```

### **Instance Bootstrap with User Data**

```bash
#!/bin/bash
# User Data script for web server setup
yum update -y
yum install -y httpd
systemctl start httpd
systemctl enable httpd

# Install CloudWatch agent
wget https://s3.amazonaws.com/amazoncloudwatch-agent/amazon_linux/amd64/latest/amazon-cloudwatch-agent.rpm
rpm -U amazon-cloudwatch-agent.rpm

# Configure application
echo "<h1>Web Server $(hostname -f)</h1>" > /var/www/html/index.html

# Signal AutoScaling that instance is ready
/opt/aws/bin/cfn-signal -e $? --stack ${AWS::StackName} --resource AutoScalingGroup --region ${AWS::Region}
```

## **Auto Scaling Groups (ASG)**

### **Launch Configuration vs Launch Template**

- **Launch Template (Recommended):** Supports latest features, versioning, mixed instance types
- **Launch Configuration (Legacy):** Basic configuration, being phased out

### **Scaling Policies**

- **Target Tracking:** Maintain specific metric (CPU, network, ALB requests)
- **Step Scaling:** Scale based on CloudWatch alarm thresholds
- **Simple Scaling:** Single scaling action based on alarm
- **Predictive Scaling:** Uses ML to predict and scale ahead of demand

### **Health Checks**

- **EC2 Health Check:** Based on EC2 system status checks
- **ELB Health Check:** Based on load balancer health checks
- **Custom Health Check:** Application-defined health status

### **Termination Policies**

- **Default:** Oldest launch configuration, then closest to next billing hour
- **OldestInstance:** Terminate oldest instance first
- **NewestInstance:** Terminate newest instance first
- **OldestLaunchConfiguration:** Terminate instances with oldest launch config

## **Load Balancing**

### **Application Load Balancer (ALB)**

- **Layer 7:** HTTP/HTTPS traffic routing
- **Path/Host-based Routing:** Route based on URL path or hostname
- **Target Types:** Instances, IP addresses, Lambda functions
- **Features:** WebSocket, HTTP/2, sticky sessions, WAF integration

### **Network Load Balancer (NLB)**

- **Layer 4:** TCP/UDP/TLS traffic
- **Ultra-high Performance:** Millions of requests per second
- **Static IP:** One static IP per AZ
- **Use Cases:** Gaming, IoT, real-time applications

### **Gateway Load Balancer (GWLB)**

- **Layer 3:** Network traffic inspection and filtering
- **Use Cases:** Firewalls, intrusion detection, deep packet inspection

### **Classic Load Balancer (CLB)**

- **Legacy:** HTTP/HTTPS and TCP
- **Layer 4 & 7:** Basic load balancing features
- **Status:** Not recommended for new applications

## Monitoring & Observability

### Key Metrics to Monitor
| Metric | Description | Threshold | Action |
|--------|-------------|-----------|--------|
| **CPU Utilization** | Percentage of allocated CPU capacity | Warning: >80%, Critical: >90% | Scale up/out, optimize application |
| **Memory Utilization** | RAM usage percentage | Warning: >85%, Critical: >95% | Increase instance size, optimize memory |
| **Disk IOPS** | Input/output operations per second | Warning: >80% of limit, Critical: >95% | Upgrade to higher IOPS volume |
| **Network Utilization** | Network bandwidth usage | Warning: >80% of limit, Critical: >95% | Upgrade instance type, optimize network |

### CloudWatch Integration

```bash
# Create comprehensive EC2 dashboard
aws cloudwatch put-dashboard \
  --dashboard-name "EC2-Enterprise-Dashboard" \
  --dashboard-body '{
    "widgets": [
      {
        "type": "metric",
        "properties": {
          "metrics": [
            ["AWS/EC2", "CPUUtilization", "InstanceId", "i-1234567890abcdef0"],
            [".", "NetworkIn", ".", "."],
            [".", "NetworkOut", ".", "."],
            ["AWS/EBS", "VolumeReadOps", "VolumeId", "vol-1234567890abcdef0"],
            [".", "VolumeWriteOps", ".", "."]
          ],
          "period": 300,
          "stat": "Average",
          "region": "us-east-1",
          "title": "EC2 Instance Performance"
        }
      }
    ]
  }'

# Set up automated alarms
aws cloudwatch put-metric-alarm \
  --alarm-name "EC2-High-CPU-Utilization" \
  --alarm-description "High CPU utilization on EC2 instance" \
  --metric-name "CPUUtilization" \
  --namespace "AWS/EC2" \
  --statistic Average \
  --period 300 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold \
  --dimensions Name=InstanceId,Value=i-1234567890abcdef0 \
  --alarm-actions arn:aws:sns:us-east-1:123456789012:ec2-alerts

# Create composite alarm for comprehensive monitoring
aws cloudwatch put-composite-alarm \
  --alarm-name "EC2-System-Health" \
  --alarm-description "Overall system health for EC2 instance" \
  --actions-enabled \
  --alarm-actions arn:aws:sns:us-east-1:123456789012:critical-alerts \
  --alarm-rule "(ALARM(\"EC2-High-CPU-Utilization\") OR ALARM(\"EC2-Low-Disk-Space\") OR ALARM(\"EC2-High-Memory-Usage\"))"
```

### Custom Monitoring

```python
import boto3
import json
import psutil
import time
from datetime import datetime

class EC2Monitor:
    def __init__(self):
        self.cloudwatch = boto3.client('cloudwatch')
        self.ec2 = boto3.client('ec2')
        self.instance_id = self._get_instance_id()
        
    def _get_instance_id(self):
        """Get current instance ID from metadata"""
        import urllib.request
        try:
            response = urllib.request.urlopen('http://169.254.169.254/latest/meta-data/instance-id', timeout=2)
            return response.read().decode('utf-8')
        except:
            return 'unknown'
    
    def publish_custom_metrics(self):
        """Publish custom system metrics to CloudWatch"""
        try:
            # Get system metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            network = psutil.net_io_counters()
            
            # Prepare metric data
            metric_data = [
                {
                    'MetricName': 'MemoryUtilization',
                    'Value': memory.percent,
                    'Unit': 'Percent',
                    'Dimensions': [
                        {
                            'Name': 'InstanceId',
                            'Value': self.instance_id
                        }
                    ]
                },
                {
                    'MetricName': 'DiskUtilization',
                    'Value': (disk.used / disk.total) * 100,
                    'Unit': 'Percent',
                    'Dimensions': [
                        {
                            'Name': 'InstanceId',
                            'Value': self.instance_id
                        }
                    ]
                },
                {
                    'MetricName': 'ProcessCount',
                    'Value': len(psutil.pids()),
                    'Unit': 'Count',
                    'Dimensions': [
                        {
                            'Name': 'InstanceId',
                            'Value': self.instance_id
                        }
                    ]
                }
            ]
            
            # Send to CloudWatch
            self.cloudwatch.put_metric_data(
                Namespace='Custom/EC2',
                MetricData=metric_data
            )
            
            print(f"Custom metrics published for instance {self.instance_id}")
            
        except Exception as e:
            print(f"Failed to publish custom metrics: {e}")
    
    def generate_health_report(self):
        """Generate comprehensive instance health report"""
        try:
            # Get instance details
            instance_response = self.ec2.describe_instances(InstanceIds=[self.instance_id])
            instance = instance_response['Reservations'][0]['Instances'][0]
            
            # Get system information
            system_info = {
                'instance_id': self.instance_id,
                'instance_type': instance['InstanceType'],
                'state': instance['State']['Name'],
                'launch_time': instance['LaunchTime'].isoformat(),
                'cpu_utilization': psutil.cpu_percent(interval=1),
                'memory_usage': psutil.virtual_memory()._asdict(),
                'disk_usage': psutil.disk_usage('/')._asdict(),
                'network_stats': psutil.net_io_counters()._asdict(),
                'uptime_seconds': time.time() - psutil.boot_time()
            }
            
            return system_info
            
        except Exception as e:
            print(f"Failed to generate health report: {e}")
            return {'error': str(e)}

# Usage
if __name__ == "__main__":
    monitor = EC2Monitor()
    
    # Publish metrics every 5 minutes
    while True:
        monitor.publish_custom_metrics()
        time.sleep(300)
```

### **Traditional CloudWatch Metrics**

- **Basic Monitoring:** 5-minute intervals (free)
- **Detailed Monitoring:** 1-minute intervals (additional cost)
- **Custom Metrics:** Application-specific metrics via CloudWatch agent

### **Instance Metadata and User Data**

- **Metadata Service:** `http://169.254.169.254/latest/meta-data/`
- **IMDSv2:** Session-oriented, more secure version
- **User Data:** `http://169.254.169.254/latest/user-data/`
- **Common Metadata:** Instance ID, AMI ID, instance type, security groups, IAM role

### **Systems Manager Integration**

- **Session Manager:** Browser-based shell access without SSH
- **Patch Manager:** Automated patching of instances
- **Run Command:** Execute commands across multiple instances
- **Parameter Store:** Secure storage for configuration data

## Security & Compliance

### Security Best Practices
- **Network Isolation:** Deploy instances in private subnets with security groups and NACLs for defense in depth
- **Identity and Access Management:** Use IAM roles instead of access keys, implement least privilege access
- **Data Protection:** Enable EBS encryption at rest, use HTTPS/TLS for data in transit
- **Security Monitoring:** Enable CloudTrail, GuardDuty, and Security Hub for comprehensive security monitoring

### Compliance Frameworks
- **SOC 2 Type II:** EC2 infrastructure supports SOC 2 compliance with automated audit trails and access controls
- **HIPAA:** EC2 can be configured for HIPAA compliance with encryption, access logging, and secure network configuration
- **PCI DSS:** Supports PCI DSS requirements with network isolation, encryption, and security monitoring
- **FedRAMP:** EC2 instances can be deployed in FedRAMP authorized environments with appropriate security controls

### IAM Policies for EC2
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ec2:RunInstances",
        "ec2:TerminateInstances",
        "ec2:StartInstances",
        "ec2:StopInstances",
        "ec2:DescribeInstances"
      ],
      "Resource": [
        "arn:aws:ec2:*:*:instance/*",
        "arn:aws:ec2:*:*:volume/*",
        "arn:aws:ec2:*:*:network-interface/*",
        "arn:aws:ec2:*:*:security-group/*"
      ],
      "Condition": {
        "StringEquals": {
          "ec2:InstanceType": ["t3.micro", "t3.small", "t3.medium"],
          "aws:RequestedRegion": "us-west-2"
        }
      }
    },
    {
      "Effect": "Allow",
      "Action": [
        "ec2:CreateTags",
        "ec2:DescribeTags"
      ],
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "ec2:CreateAction": "RunInstances"
        }
      }
    },
    {
      "Effect": "Deny",
      "Action": [
        "ec2:ModifyInstanceAttribute",
        "ec2:ModifyNetworkInterfaceAttribute"
      ],
      "Resource": "*",
      "Condition": {
        "StringNotEquals": {
          "aws:PrincipalTag/Department": "Security"
        }
      }
    }
  ]
}
```

### **Traditional Security Features**

#### **IAM Roles for EC2**

- **Instance Profile:** Wrapper around IAM role for EC2
- **Temporary Credentials:** Automatically rotated
- **Best Practice:** Use roles instead of storing credentials on instances

#### **Key Management**

- **EC2 Key Pairs:** For SSH access to Linux instances
- **Windows Password:** Retrieved using EC2 key pair
- **AWS Systems Manager:** Alternative secure access method

#### **Security Best Practices**

- **Principle of Least Privilege:** Minimal required permissions
- **Security Group Rules:** Restrict to necessary ports and sources
- **Regular Patching:** Keep OS and applications updated
- **Encryption:** Enable EBS encryption and in-transit encryption

## **High Availability and Disaster Recovery**

### **Multi-AZ Deployment**

- **Auto Scaling Groups:** Span multiple AZs automatically
- **Load Balancers:** Distribute traffic across AZs
- **EBS Snapshots:** Cross-region backup capability

### **Backup Strategies**

- **EBS Snapshots:** Automated via Data Lifecycle Manager
- **AMI Creation:** Full instance backup including configuration
- **Cross-Region Replication:** Disaster recovery in different regions

## Cost Optimization

### Pricing Model
- **On-Demand Instances:** Pay by the second for Linux/Windows instances with no long-term commitments
- **Reserved Instances:** Up to 75% savings with 1 or 3-year commitments for predictable workloads
- **Spot Instances:** Up to 90% savings using spare capacity for fault-tolerant applications
- **Dedicated Hosts:** Physical servers for regulatory requirements or licensing constraints

### Cost Optimization Strategies
```bash
# Implement automated cost controls and monitoring
aws budgets create-budget \
  --account-id 123456789012 \
  --budget '{
    "BudgetName": "EC2-Monthly-Budget",
    "BudgetLimit": {
      "Amount": "1000",
      "Unit": "USD"
    },
    "TimeUnit": "MONTHLY",
    "BudgetType": "COST",
    "CostFilters": {
      "Service": ["Amazon Elastic Compute Cloud - Compute"]
    }
  }' \
  --notifications '[{
    "NotificationType": "ACTUAL",
    "ComparisonOperator": "GREATER_THAN",
    "Threshold": 80,
    "SubscriberAddress": "admin@company.com",
    "SubscriberType": "EMAIL"
  }]'

# Automated right-sizing recommendations
#!/bin/bash
# right-sizing-check.sh - Analyze instance utilization and recommend optimizations

CLOUDWATCH_NAMESPACE="AWS/EC2"
LOOKBACK_DAYS=30
THRESHOLD_CPU=20  # Low CPU threshold for downsizing recommendations

echo "Analyzing EC2 instances for right-sizing opportunities..."

# Get all running instances
aws ec2 describe-instances \
  --filters "Name=instance-state-name,Values=running" \
  --query 'Reservations[].Instances[].[InstanceId,InstanceType,Tags[?Key==`Name`].Value|[0]]' \
  --output text | \
while read instance_id instance_type instance_name; do
  
  # Get average CPU utilization for the last 30 days
  avg_cpu=$(aws cloudwatch get-metric-statistics \
    --namespace $CLOUDWATCH_NAMESPACE \
    --metric-name CPUUtilization \
    --dimensions Name=InstanceId,Value=$instance_id \
    --start-time $(date -d "$LOOKBACK_DAYS days ago" --iso-8601) \
    --end-time $(date --iso-8601) \
    --period 86400 \
    --statistics Average \
    --query 'Datapoints[].Average' \
    --output text | \
    awk '{sum+=$1; count++} END {if(count>0) print sum/count; else print 0}')
  
  # Recommend downsizing if CPU is consistently low
  if (( $(echo "$avg_cpu < $THRESHOLD_CPU" | bc -l) )); then
    echo "RECOMMENDATION: Instance $instance_id ($instance_name) - $instance_type"
    echo "  Average CPU: ${avg_cpu}%"
    echo "  Consider downsizing to save costs"
    echo "  Estimated monthly savings: \$XXX (run AWS Compute Optimizer for precise estimates)"
    echo ""
  fi
done

# Generate Spot Instance recommendations for fault-tolerant workloads
echo "Spot Instance Opportunities:"
aws ec2 describe-spot-price-history \
  --instance-types t3.medium t3.large c5.large c5.xlarge \
  --product-descriptions "Linux/UNIX" \
  --max-results 4 \
  --query 'SpotPrices[].[InstanceType,SpotPrice,AvailabilityZone]' \
  --output table
```

### **Traditional Cost Optimization**

#### **Right Sizing**

- **CloudWatch Metrics:** Monitor CPU, memory, network utilization
- **AWS Compute Optimizer:** ML-powered recommendations
- **Instance Types:** Match workload requirements to instance capabilities

#### **Storage Optimization**

- **EBS Volume Types:** Choose appropriate performance tier
- **Snapshot Lifecycle:** Automated deletion of old snapshots
- **EBS Optimization:** Enable for consistent storage performance

#### **Reserved Capacity**

- **Reserved Instances:** Long-term workloads with predictable usage
- **Savings Plans:** Flexible commitment-based pricing
- **Spot Instances:** Fault-tolerant workloads with flexible timing

## Troubleshooting & Operations

### Common Issues & Solutions

#### Issue 1: High CPU Utilization and Performance Degradation
**Symptoms:** Applications responding slowly, high CPU utilization metrics in CloudWatch
**Cause:** Insufficient compute capacity, inefficient application code, or resource contention
**Solution:**
```bash
# Diagnose CPU and memory usage
aws cloudwatch get-metric-statistics \
  --namespace AWS/EC2 \
  --metric-name CPUUtilization \
  --dimensions Name=InstanceId,Value=i-1234567890abcdef0 \
  --start-time 2024-01-15T00:00:00Z \
  --end-time 2024-01-15T23:59:59Z \
  --period 300 \
  --statistics Maximum,Average

# Check system processes and resource usage
aws ssm send-command \
  --instance-ids "i-1234567890abcdef0" \
  --document-name "AWS-RunShellScript" \
  --parameters 'commands=["top -bn1", "free -m", "df -h", "iostat 1 1"]'

# Scale up instance if needed
aws ec2 stop-instances --instance-ids i-1234567890abcdef0
aws ec2 modify-instance-attribute \
  --instance-id i-1234567890abcdef0 \
  --instance-type Value=c5.xlarge
aws ec2 start-instances --instance-ids i-1234567890abcdef0
```

#### Issue 2: Instance Connection and Network Problems
**Symptoms:** Unable to connect via SSH/RDP, network timeouts, application connectivity issues
**Cause:** Security group misconfigurations, network ACL blocks, routing issues
**Solution:**
```python
import boto3
from datetime import datetime

def diagnose_connectivity_issues(instance_id):
    """Comprehensive connectivity diagnostics for EC2 instances"""
    
    ec2 = boto3.client('ec2')
    
    try:
        # Get instance details
        response = ec2.describe_instances(InstanceIds=[instance_id])
        instance = response['Reservations'][0]['Instances'][0]
        
        diagnostics = {
            'instance_id': instance_id,
            'state': instance['State']['Name'],
            'public_ip': instance.get('PublicIpAddress', 'None'),
            'private_ip': instance.get('PrivateIpAddress', 'None'),
            'vpc_id': instance['VpcId'],
            'subnet_id': instance['SubnetId'],
            'security_groups': [sg['GroupId'] for sg in instance['SecurityGroups']],
            'issues': []
        }
        
        # Check instance state
        if instance['State']['Name'] != 'running':
            diagnostics['issues'].append(f"Instance is in {instance['State']['Name']} state")
        
        # Check security groups
        sg_response = ec2.describe_security_groups(
            GroupIds=[sg['GroupId'] for sg in instance['SecurityGroups']]
        )
        
        has_ssh_access = False
        has_http_access = False
        
        for sg in sg_response['SecurityGroups']:
            for rule in sg['IpPermissions']:
                if rule.get('FromPort') == 22:
                    has_ssh_access = True
                if rule.get('FromPort') == 80:
                    has_http_access = True
        
        if not has_ssh_access:
            diagnostics['issues'].append("No SSH access (port 22) found in security groups")
        
        if not has_http_access:
            diagnostics['issues'].append("No HTTP access (port 80) found in security groups")
        
        # Check subnet route table
        subnet_response = ec2.describe_subnets(SubnetIds=[instance['SubnetId']])
        subnet = subnet_response['Subnets'][0]
        
        # Get route table for subnet
        rt_response = ec2.describe_route_tables(
            Filters=[
                {'Name': 'association.subnet-id', 'Values': [instance['SubnetId']]}
            ]
        )
        
        if rt_response['RouteTables']:
            route_table = rt_response['RouteTables'][0]
            has_internet_route = any(
                route.get('GatewayId', '').startswith('igw-') 
                for route in route_table['Routes']
                if route.get('DestinationCidrBlock') == '0.0.0.0/0'
            )
            
            if not has_internet_route and not diagnostics['public_ip']:
                diagnostics['issues'].append("Instance in private subnet without NAT gateway route")
        
        # Check instance status
        status_response = ec2.describe_instance_status(InstanceIds=[instance_id])
        if status_response['InstanceStatuses']:
            status = status_response['InstanceStatuses'][0]
            
            if status['InstanceStatus']['Status'] != 'ok':
                diagnostics['issues'].append(f"Instance status check failed: {status['InstanceStatus']['Status']}")
            
            if status['SystemStatus']['Status'] != 'ok':
                diagnostics['issues'].append(f"System status check failed: {status['SystemStatus']['Status']}")
        
        return diagnostics
        
    except Exception as e:
        return {
            'instance_id': instance_id,
            'error': str(e),
            'issues': [f"Failed to diagnose connectivity: {e}"]
        }

# Usage
diagnostics = diagnose_connectivity_issues('i-1234567890abcdef0')
print(f"Connectivity diagnostics for {diagnostics['instance_id']}:")
for issue in diagnostics.get('issues', []):
    print(f"  - {issue}")
```

### Performance Optimization

#### Optimization Strategy 1: Compute Resource Optimization
- **Current State Analysis:** Monitor CPU, memory, and network utilization using CloudWatch and custom metrics
- **Optimization Steps:** Right-size instances, enable enhanced networking, optimize application performance
- **Expected Improvement:** 20-40% performance improvement, reduced latency, better resource utilization

#### Optimization Strategy 2: Storage Performance Tuning
- **Monitoring Approach:** Track IOPS usage, throughput, and queue depth using CloudWatch EBS metrics
- **Tuning Parameters:** Optimize EBS volume types, enable EBS optimization, implement storage tiering
- **Validation Methods:** Benchmark testing, real-world performance monitoring, cost-performance analysis

### **Traditional Troubleshooting**

#### **Common Connection Issues**

- **App Times Out:** Likely a **Security Group or firewall** issue (port not open)
- **Connection Refused:** Likely an **application error**; try restarting the app or the instance
- **Permission Denied (SSH):** Check:
    - **Private key permissions:** `chmod 400 /path/to/your-key.pem`
    - **Correct key used**
    - **Security Group settings** (port 22 open)
    - **IAM role or user permissions**

#### **Instance Issues**

- **Instance Not Starting:** Check service limits, subnet capacity, security group rules
- **Performance Issues:** Monitor CloudWatch metrics, check instance type suitability
- **Storage Issues:** Verify EBS volume attachment, check disk space, IOPS limits

#### **Network Issues**

- **No Internet Access:** Check route tables, internet gateway, NAT gateway/instance
- **Cross-VPC Communication:** Verify VPC peering, transit gateway, or VPN configuration
- **DNS Resolution:** Check VPC DNS settings, security groups for port 53

## **Advanced Features**

### **Hibernation**

- **Supported Instances:** M3, M4, M5, C3, C4, C5, R3, R4, R5 families
- **Requirements:** EBS root volume, encrypted, specific instance sizes
- **Use Cases:** Long-running applications with extensive initialization

### **Nitro System**

- **Components:** Nitro cards, Nitro security chip, Nitro hypervisor
- **Benefits:** Enhanced performance, security, and feature innovation
- **Instance Types:** Most current generation instances use Nitro

### **Elastic Fabric Adapter (EFA)**

- **Purpose:** High-performance computing and machine learning workloads
- **Features:** Bypass kernel for low-latency communication
- **Use Cases:** MPI applications, distributed ML training

### **GPU and Machine Learning**

- **GPU Instances:** P3, P4, G4, G5 families for ML training and inference
- **AWS Inferentia:** Custom ML inference chips (Inf1 instances)
- **Use Cases:** Deep learning, high-performance computing, graphics workloads

## **Compliance and Governance**

### **AWS Config**

- **Configuration Compliance:** Monitor EC2 configuration changes
- **Compliance Rules:** Automated checks against security baselines
- **Remediation:** Automated fixes for non-compliant resources

### **AWS CloudTrail**

- **API Logging:** Track all EC2 API calls
- **Security Analysis:** Detect unusual activity patterns
- **Compliance Auditing:** Maintain audit trail for compliance requirements

### **Resource Tagging**

- **Cost Allocation:** Track costs by project, environment, team
- **Automation:** Use tags to trigger automated actions
- **Governance:** Enforce tagging policies via AWS Organizations

## **Migration and Modernization**

### **AWS Application Migration Service**

- **Lift and Shift:** Migrate applications without changes
- **Continuous Replication:** Real-time data sync during migration
- **Testing:** Non-disruptive testing of migrated applications

### **VM Import/Export**

- **Supported Formats:** VMware, Hyper-V, KVM virtual machines
- **Use Cases:** Migrate existing VMs to EC2
- **Limitations:** Some OS versions and configurations not supported

### **AWS Image Builder**

- **Automated AMI Creation:** Build and maintain golden images
- **Security Patching:** Automated security updates
- **Compliance:** Ensure images meet organizational standards

## **Practical CLI Examples**

### **Instance Management**

```bash
# Launch instance with user data
aws ec2 run-instances \
  --image-id ami-0abcdef1234567890 \
  --instance-type t3.micro \
  --key-name my-key-pair \
  --security-group-ids sg-123abc12 \
  --subnet-id subnet-6e7f829e \
  --user-data file://startup-script.sh \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=WebServer},{Key=Environment,Value=Production}]'

# Stop and start instance
aws ec2 stop-instances --instance-ids i-1234567890abcdef0
aws ec2 start-instances --instance-ids i-1234567890abcdef0

# Create AMI from instance
aws ec2 create-image \
  --instance-id i-1234567890abcdef0 \
  --name "WebServer-$(date +%Y%m%d)" \
  --description "Production web server AMI" \
  --no-reboot

# Modify instance type (requires stop)
aws ec2 stop-instances --instance-ids i-1234567890abcdef0
aws ec2 modify-instance-attribute \
  --instance-id i-1234567890abcdef0 \
  --instance-type Value=t3.medium
aws ec2 start-instances --instance-ids i-1234567890abcdef0
```

### **Security Group Management**

```bash
# Create security group
aws ec2 create-security-group \
  --group-name web-servers \
  --description "Security group for web servers" \
  --vpc-id vpc-12345678

# Add HTTP/HTTPS rules
aws ec2 authorize-security-group-ingress \
  --group-id sg-123abc12 \
  --protocol tcp \
  --port 80 \
  --cidr 0.0.0.0/0

aws ec2 authorize-security-group-ingress \
  --group-id sg-123abc12 \
  --protocol tcp \
  --port 443 \
  --cidr 0.0.0.0/0

# Add SSH from bastion host security group
aws ec2 authorize-security-group-ingress \
  --group-id sg-123abc12 \
  --protocol tcp \
  --port 22 \
  --source-group sg-bastion123
```

### **Auto Scaling Examples**

```bash
# Create launch template
aws ec2 create-launch-template \
  --launch-template-name WebServerTemplate \
  --launch-template-data '{
    "ImageId":"ami-0abcdef1234567890",
    "InstanceType":"t3.micro",
    "KeyName":"my-key-pair",
    "SecurityGroupIds":["sg-123abc12"],
    "UserData":"IyEvYmluL2Jhc2gKZWNobyAiSGVsbG8gV29ybGQi"
  }'

# Create Auto Scaling Group
aws autoscaling create-auto-scaling-group \
  --auto-scaling-group-name WebServerASG \
  --launch-template LaunchTemplateName=WebServerTemplate,Version=1 \
  --min-size 2 \
  --max-size 10 \
  --desired-capacity 3 \
  --vpc-zone-identifier "subnet-12345678,subnet-87654321" \
  --target-group-arns arn:aws:elasticloadbalancing:us-west-2:123456789012:targetgroup/WebServerTG/1234567890123456

# Create scaling policies
aws autoscaling put-scaling-policy \
  --auto-scaling-group-name WebServerASG \
  --policy-name ScaleUpPolicy \
  --policy-type TargetTrackingScaling \
  --target-tracking-configuration '{
    "TargetValue": 70.0,
    "PredefinedMetricSpecification": {
      "PredefinedMetricType": "ASGAverageCPUUtilization"
    }
  }'
```

### **Instance Metadata Usage**

```bash
# Get instance metadata (run from EC2 instance)
curl http://169.254.169.254/latest/meta-data/instance-id
curl http://169.254.169.254/latest/meta-data/public-ipv4
curl http://169.254.169.254/latest/meta-data/placement/availability-zone
curl http://169.254.169.254/latest/meta-data/iam/security-credentials/

# Get user data
curl http://169.254.169.254/latest/user-data

# Instance identity document
curl http://169.254.169.254/latest/dynamic/instance-identity/document
```

### **EBS Volume Operations**

```bash
# Create and attach EBS volume
aws ec2 create-volume \
  --size 100 \
  --volume-type gp3 \
  --availability-zone us-west-2a \
  --tag-specifications 'ResourceType=volume,Tags=[{Key=Name,Value=DataVolume}]'

aws ec2 attach-volume \
  --volume-id vol-1234567890abcdef0 \
  --instance-id i-1234567890abcdef0 \
  --device /dev/xvdf

# Create snapshot
aws ec2 create-snapshot \
  --volume-id vol-1234567890abcdef0 \
  --description "Daily backup $(date +%Y-%m-%d)"

# Copy snapshot to another region
aws ec2 copy-snapshot \
  --source-region us-west-2 \
  --source-snapshot-id snap-1234567890abcdef0 \
  --destination-region us-east-1 \
  --description "DR backup $(date +%Y-%m-%d)"
```

## **DevOps Automation Scripts**

### **Instance Health Check Script**

```bash
#!/bin/bash
# health-check.sh - Monitor EC2 instance health

INSTANCE_ID="i-1234567890abcdef0"
SNS_TOPIC="arn:aws:sns:us-west-2:123456789012:alerts"

# Check instance status
STATUS=$(aws ec2 describe-instance-status \
  --instance-ids $INSTANCE_ID \
  --query 'InstanceStatuses[0].InstanceStatus.Status' \
  --output text)

if [ "$STATUS" != "ok" ]; then
    aws sns publish \
      --topic-arn $SNS_TOPIC \
      --message "Instance $INSTANCE_ID health check failed: $STATUS"
    
    # Attempt to recover
    aws ec2 reboot-instances --instance-ids $INSTANCE_ID
fi
```

### **Automated AMI Creation**

```bash
#!/bin/bash
# backup-ami.sh - Create daily AMI backups

INSTANCE_ID="i-1234567890abcdef0"
AMI_NAME="WebServer-Backup-$(date +%Y%m%d-%H%M)"
RETENTION_DAYS=7

# Create AMI
AMI_ID=$(aws ec2 create-image \
  --instance-id $INSTANCE_ID \
  --name "$AMI_NAME" \
  --description "Automated daily backup" \
  --no-reboot \
  --query 'ImageId' \
  --output text)

echo "Created AMI: $AMI_ID"

# Clean up old AMIs
aws ec2 describe-images \
  --owners self \
  --filters "Name=name,Values=WebServer-Backup-*" \
  --query "Images[?CreationDate<='$(date -d "$RETENTION_DAYS days ago" -Iseconds)'].ImageId" \
  --output text | xargs -n 1 aws ec2 deregister-image --image-id
```

### **Auto Scaling Notification Script**

```bash
#!/bin/bash
# Handle Auto Scaling lifecycle hooks

INSTANCE_ID=$1
LIFECYCLE_HOOK_NAME=$2
AUTO_SCALING_GROUP_NAME=$3
LIFECYCLE_ACTION_TOKEN=$4

# Perform custom setup/cleanup
case "$LIFECYCLE_HOOK_NAME" in
  "launch-hook")
    # Install monitoring agent, register with load balancer, etc.
    sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
      -a fetch-config -m ec2 -c file:/opt/aws/amazon-cloudwatch-agent/config.json -s
    ;;
  "terminate-hook")
    # Drain connections, backup logs, etc.
    sudo service nginx stop
    aws logs create-export-task --log-group-name /var/log/nginx --from $(date +%s)000
    ;;
esac

# Complete lifecycle action
aws autoscaling complete-lifecycle-action \
  --lifecycle-hook-name "$LIFECYCLE_HOOK_NAME" \
  --auto-scaling-group-name "$AUTO_SCALING_GROUP_NAME" \
  --instance-id "$INSTANCE_ID" \
  --lifecycle-action-token "$LIFECYCLE_ACTION_TOKEN" \
  --lifecycle-action-result CONTINUE
```

## Enterprise Implementation Examples

### **Multi-Tier Application Architecture**

```python
import boto3
from datetime import datetime

class EnterpriseEC2Manager:
    def __init__(self):
        self.ec2 = boto3.client('ec2')
        self.autoscaling = boto3.client('autoscaling')
        self.elbv2 = boto3.client('elbv2')
    
    def deploy_three_tier_architecture(self, config):
        """Deploy web, app, and database tiers"""
        
        # Web Tier - Auto Scaling Group with ALB
        web_template = self.create_launch_template(
            name=f"{config['app_name']}-web-template",
            ami_id=config['web_ami'],
            instance_type='t3.medium',
            security_groups=config['web_sg'],
            user_data=self._get_web_tier_user_data()
        )
        
        web_asg = self.create_auto_scaling_group(
            name=f"{config['app_name']}-web-asg",
            template_id=web_template,
            subnets=config['public_subnets'],
            min_size=2,
            max_size=10,
            desired_capacity=2
        )
        
        # Application Tier - Auto Scaling Group
        app_template = self.create_launch_template(
            name=f"{config['app_name']}-app-template",
            ami_id=config['app_ami'],
            instance_type='c5.large',
            security_groups=config['app_sg'],
            user_data=self._get_app_tier_user_data()
        )
        
        app_asg = self.create_auto_scaling_group(
            name=f"{config['app_name']}-app-asg",
            template_id=app_template,
            subnets=config['private_subnets'],
            min_size=2,
            max_size=8,
            desired_capacity=2
        )
        
        # Database Tier - Individual instances for control
        db_instances = self.launch_database_instances(
            config['db_ami'],
            config['db_instance_type'],
            config['db_subnets'],
            config['db_sg']
        )
        
        return {
            'web_asg': web_asg,
            'app_asg': app_asg,
            'db_instances': db_instances
        }
```

### **Blue-Green Deployment Strategy**

```python
class BlueGreenDeployment:
    def __init__(self, app_name):
        self.app_name = app_name
        self.ec2 = boto3.client('ec2')
        self.autoscaling = boto3.client('autoscaling')
        self.elbv2 = boto3.client('elbv2')
    
    def execute_blue_green_deployment(self, new_ami_id):
        """Execute blue-green deployment with EC2 Auto Scaling"""
        
        # Create new launch template version with updated AMI
        green_template_version = self.update_launch_template(new_ami_id)
        
        # Create green Auto Scaling Group
        green_asg_name = f"{self.app_name}-green-{int(datetime.now().timestamp())}"
        green_asg = self.create_auto_scaling_group(
            name=green_asg_name,
            template_version=green_template_version,
            desired_capacity=self._get_current_capacity()
        )
        
        # Wait for green instances to be healthy
        self.wait_for_healthy_instances(green_asg_name)
        
        # Switch traffic from blue to green
        self.switch_target_group_traffic(green_asg_name)
        
        # Scale down blue environment
        blue_asg_name = f"{self.app_name}-blue"
        self.scale_down_asg(blue_asg_name)
        
        return {
            'status': 'success',
            'green_asg': green_asg_name,
            'deployment_time': datetime.now().isoformat()
        }
```

### **Enterprise Auto Scaling Strategy**

```yaml
# CloudFormation template for enterprise auto scaling
AWSTemplateFormatVersion: '2010-09-09'

Parameters:
  Environment:
    Type: String
    AllowedValues: [dev, staging, prod]
  
  ApplicationName:
    Type: String

Resources:
  LaunchTemplate:
    Type: AWS::EC2::LaunchTemplate
    Properties:
      LaunchTemplateName: !Sub '${ApplicationName}-${Environment}-template'
      LaunchTemplateData:
        ImageId: ami-0abcdef1234567890
        InstanceType: 
          !If [IsProd, 'c5.xlarge', 't3.medium']
        SecurityGroupIds:
          - !Ref ApplicationSecurityGroup
        IamInstanceProfile:
          Arn: !GetAtt InstanceProfile.Arn
        UserData:
          Fn::Base64: !Sub |
            #!/bin/bash
            yum update -y
            /opt/aws/bin/cfn-init -v --stack ${AWS::StackName} --resource LaunchTemplate --region ${AWS::Region}
            /opt/aws/bin/cfn-signal -e $? --stack ${AWS::StackName} --resource AutoScalingGroup --region ${AWS::Region}

  AutoScalingGroup:
    Type: AWS::AutoScaling::AutoScalingGroup
    Properties:
      LaunchTemplate:
        LaunchTemplateId: !Ref LaunchTemplate
        Version: !GetAtt LaunchTemplate.LatestVersionNumber
      MinSize: !If [IsProd, 3, 1]
      MaxSize: !If [IsProd, 20, 5]
      DesiredCapacity: !If [IsProd, 6, 2]
      VPCZoneIdentifier: !Ref PrivateSubnets
      TargetGroupARNs:
        - !Ref ApplicationTargetGroup
      HealthCheckType: ELB
      HealthCheckGracePeriod: 300
```

## **Real-World DevOps Scenarios**

### **Blue-Green Deployment**

```bash
# Blue-Green deployment script
#!/bin/bash

GREEN_ASG="WebServer-Green-ASG"
BLUE_ASG="WebServer-Blue-ASG"
TARGET_GROUP="WebServerTG"

# Scale up green environment
aws autoscaling update-auto-scaling-group \
  --auto-scaling-group-name $GREEN_ASG \
  --desired-capacity 3

# Wait for green instances to be healthy
while [ $(aws elbv2 describe-target-health \
  --target-group-arn $TARGET_GROUP \
  --query 'TargetHealthDescriptions[?TargetHealth.State==`healthy`] | length(@)') -lt 3 ]; do
  echo "Waiting for green instances to be healthy..."
  sleep 30
done

# Switch traffic to green
aws elbv2 modify-listener \
  --listener-arn $LISTENER_ARN \
  --default-actions Type=forward,TargetGroupArn=$GREEN_TARGET_GROUP

# Scale down blue environment
aws autoscaling update-auto-scaling-group \
  --auto-scaling-group-name $BLUE_ASG \
  --desired-capacity 0
```

### **CI/CD Integration**

```bash
# Deploy script for CI/CD pipeline
#!/bin/bash

APP_VERSION=$1
DEPLOYMENT_GROUP="WebServerDeployment"

# Create deployment
DEPLOYMENT_ID=$(aws deploy create-deployment \
  --application-name MyWebApp \
  --deployment-group-name $DEPLOYMENT_GROUP \
  --s3-location bucket=my-deployments,key=app-$APP_VERSION.zip,bundleType=zip \
  --query 'deploymentId' \
  --output text)

echo "Deployment ID: $DEPLOYMENT_ID"

# Monitor deployment
aws deploy wait deployment-successful --deployment-id $DEPLOYMENT_ID

if [ $? -eq 0 ]; then
  echo "Deployment successful"
  # Update load balancer tags, send notifications, etc.
else
  echo "Deployment failed"
  # Rollback, send alerts, etc.
  aws deploy stop-deployment --deployment-id $DEPLOYMENT_ID --auto-rollback-enabled
fi
```

## Automation & Infrastructure as Code

### **CloudFormation Templates**

```yaml
# Complete EC2 Auto Scaling infrastructure
AWSTemplateFormatVersion: '2010-09-09'

Parameters:
  KeyName:
    Type: AWS::EC2::KeyPair::KeyName
    Description: Name of an existing EC2 KeyPair
  
  VpcId:
    Type: AWS::EC2::VPC::Id
    Description: VPC ID where resources will be created

Resources:
  ApplicationSecurityGroup:
    Type: AWS::EC2::SecurityGroup
    Properties:
      GroupDescription: Security group for web application
      VpcId: !Ref VpcId
      SecurityGroupIngress:
        - IpProtocol: tcp
          FromPort: 80
          ToPort: 80
          SourceSecurityGroupId: !Ref LoadBalancerSecurityGroup
        - IpProtocol: tcp
          FromPort: 443
          ToPort: 443
          SourceSecurityGroupId: !Ref LoadBalancerSecurityGroup
      SecurityGroupEgress:
        - IpProtocol: -1
          CidrIp: 0.0.0.0/0

  LaunchTemplate:
    Type: AWS::EC2::LaunchTemplate
    Properties:
      LaunchTemplateName: !Sub '${AWS::StackName}-launch-template'
      LaunchTemplateData:
        ImageId: ami-0abcdef1234567890
        InstanceType: t3.medium
        KeyName: !Ref KeyName
        SecurityGroupIds:
          - !Ref ApplicationSecurityGroup
        IamInstanceProfile:
          Arn: !GetAtt InstanceProfile.Arn
        UserData:
          Fn::Base64: !Sub |
            #!/bin/bash
            yum update -y
            yum install -y httpd
            systemctl start httpd
            systemctl enable httpd
            echo "<h1>Hello from ${AWS::Region}</h1>" > /var/www/html/index.html

  AutoScalingGroup:
    Type: AWS::AutoScaling::AutoScalingGroup
    Properties:
      LaunchTemplate:
        LaunchTemplateId: !Ref LaunchTemplate
        Version: !GetAtt LaunchTemplate.LatestVersionNumber
      MinSize: 2
      MaxSize: 10
      DesiredCapacity: 2
      VPCZoneIdentifier: !Ref PrivateSubnets
      TargetGroupARNs:
        - !Ref TargetGroup
```

### **Terraform Configuration**

```hcl
# EC2 Auto Scaling with Load Balancer
resource "aws_launch_template" "app" {
  name_prefix   = "${var.app_name}-"
  image_id      = var.ami_id
  instance_type = var.instance_type
  key_name      = var.key_name

  vpc_security_group_ids = [aws_security_group.app.id]

  iam_instance_profile {
    name = aws_iam_instance_profile.app.name
  }

  user_data = base64encode(templatefile("user_data.sh", {
    app_name = var.app_name
  }))

  block_device_mappings {
    device_name = "/dev/xvda"
    ebs {
      volume_size = var.root_volume_size
      volume_type = "gp3"
      encrypted   = true
    }
  }

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name        = var.app_name
      Environment = var.environment
    }
  }
}

resource "aws_autoscaling_group" "app" {
  name                = "${var.app_name}-asg"
  vpc_zone_identifier = var.private_subnet_ids
  target_group_arns   = [aws_lb_target_group.app.arn]
  
  min_size         = var.min_instances
  max_size         = var.max_instances
  desired_capacity = var.desired_instances

  launch_template {
    id      = aws_launch_template.app.id
    version = "$Latest"
  }

  tag {
    key                 = "Name"
    value               = "${var.app_name}-asg"
    propagate_at_launch = false
  }
}
```

### **Ansible Playbooks**

```yaml
# EC2 provisioning and configuration
---
- name: Deploy EC2 instances
  hosts: localhost
  gather_facts: false
  vars:
    instance_type: t3.medium
    ami_id: ami-0abcdef1234567890
    key_name: my-key-pair
    
  tasks:
    - name: Launch EC2 instances
      amazon.aws.ec2_instance:
        name: "{{ item }}"
        image_id: "{{ ami_id }}"
        instance_type: "{{ instance_type }}"
        key_name: "{{ key_name }}"
        vpc_subnet_id: "{{ subnet_id }}"
        security_groups:
          - "{{ security_group_id }}"
        state: running
        wait: true
        user_data: |
          #!/bin/bash
          yum update -y
          yum install -y python3 python3-pip
        tags:
          Environment: "{{ env }}"
          Project: "{{ project_name }}"
      loop: "{{ instance_names }}"
      register: ec2_instances

    - name: Add instances to inventory
      add_host:
        name: "{{ item.public_ip_address }}"
        groups: webservers
        ansible_user: ec2-user
        ansible_ssh_private_key_file: "{{ key_file }}"
      loop: "{{ ec2_instances.results }}"
```

## Advanced Implementation Patterns

### Multi-Region Architecture
```bash
# Deploy EC2 infrastructure across multiple regions
regions=("us-east-1" "us-west-2" "eu-west-1")

for region in "${regions[@]}"; do
  aws ec2 run-instances \
    --region $region \
    --image-id $(aws ec2 describe-images --region $region --owners amazon --filters "Name=name,Values=amzn2-ami-hvm-*" --query 'Images[0].ImageId' --output text) \
    --instance-type t3.medium \
    --key-name global-keypair \
    --security-group-ids $(aws ec2 describe-security-groups --region $region --group-names default --query 'SecurityGroups[0].GroupId' --output text) \
    --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=global-app-$region},{Key=Region,Value=$region}]"
done
```

### High Availability Setup
```yaml
# HA configuration with Auto Scaling and Load Balancing
HighAvailabilityConfiguration:
  AutoScalingGroups:
    WebTier:
      MinSize: 2
      MaxSize: 20
      DesiredCapacity: 4
      AvailabilityZones: ["us-east-1a", "us-east-1b", "us-east-1c"]
    AppTier:
      MinSize: 2
      MaxSize: 15
      DesiredCapacity: 3
      AvailabilityZones: ["us-east-1a", "us-east-1b", "us-east-1c"]
  LoadBalancing:
    WebTierALB:
      Type: ApplicationLoadBalancer
      Scheme: internet-facing
      CrossZone: true
    AppTierNLB:
      Type: NetworkLoadBalancer
      Scheme: internal
      CrossZone: true
  HealthChecks:
    HealthCheckGracePeriod: 300
    HealthCheckType: ELB
    UnhealthyThreshold: 2
```

### Disaster Recovery
- **RTO (Recovery Time Objective):** 4 hours for complete infrastructure rebuild
- **RPO (Recovery Point Objective):** 1 hour maximum data loss using automated EBS snapshots
- **Backup Strategy:** Automated AMI creation, EBS snapshots, cross-region replication
- **Recovery Procedures:** Infrastructure as Code deployment, automated failover procedures

## Integration Patterns

### API Integration
```python
class EC2APIIntegration:
    def __init__(self, region_name='us-east-1'):
        self.ec2 = boto3.client('ec2', region_name=region_name)
        
    def integrate_with_monitoring_system(self, instance_data):
        """Integration with external monitoring system"""
        try:
            response = requests.post(
                "https://monitoring-api.company.com/instances",
                json=instance_data,
                headers={'Content-Type': 'application/json'}
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Monitoring integration failed: {e}")
            raise
```

### Event-Driven Architecture
```bash
# Set up event-driven EC2 management
aws events put-rule \
  --name "EC2-State-Change-Rule" \
  --event-pattern '{
    "source": ["aws.ec2"],
    "detail-type": ["EC2 Instance State-change Notification"],
    "detail": {
      "state": ["running", "terminated", "stopped"]
    }
  }'

# Add Lambda target for automated processing
aws events put-targets \
  --rule "EC2-State-Change-Rule" \
  --targets "Id"="1","Arn"="arn:aws:lambda:us-east-1:123456789012:function:process-ec2-events"
```

## Best Practices Summary

### Development & Deployment
1. **Infrastructure as Code:** Use CloudFormation, Terraform, or CDK for consistent, repeatable deployments
2. **Immutable Infrastructure:** Create new AMIs for application updates rather than in-place modifications
3. **Environment Parity:** Maintain consistent configurations across development, staging, and production
4. **Automated Testing:** Implement comprehensive testing including infrastructure validation and application testing

### Operations & Maintenance
1. **Monitoring Strategy:** Implement comprehensive monitoring with CloudWatch, custom metrics, and third-party tools
2. **Automated Scaling:** Use Auto Scaling Groups with predictive scaling for optimal performance and cost
3. **Patch Management:** Establish regular patching schedules with automated rollback capabilities
4. **Capacity Planning:** Monitor trends and plan for capacity needs using historical data and growth projections

### Security & Governance
1. **Network Security:** Implement defense in depth with VPCs, security groups, NACLs, and WAF
2. **Access Control:** Use IAM roles, MFA, and least privilege principles for all access
3. **Data Protection:** Enable encryption at rest and in transit, implement secure backup strategies
4. **Compliance Monitoring:** Maintain continuous compliance monitoring and automated remediation

## **Miscellaneous Tips**

- **Unused or unattached EIPs** incur **hourly charges**
- **AWS Instance Connect:** Browser-based SSH without needing a key (requires IAM permissions)
- **Instance metadata endpoint:** `curl http://169.254.169.254/latest/meta-data/`
- **EC2 User Data** runs scripts at boot time (found in Advanced Details during launch)
- **Status Checks:** System status (AWS infrastructure) vs Instance status (guest OS)
- **Maintenance Windows:** AWS schedules maintenance, instances may be rebooted
- **Service Limits:** Default limits on instance count, EBS volumes, etc. (can be increased via support)
- **Billing:** Partial instance-hours billed as full hours (except for per-second billing on Linux/Windows)
- **Instance Recovery:** Automatic recovery can restart instances on new hardware if underlying hardware fails

## Additional Resources

### AWS Documentation
- [Amazon EC2 User Guide](https://docs.aws.amazon.com/ec2/latest/userguide/)
- [EC2 Instance Types](https://aws.amazon.com/ec2/instance-types/)
- [Auto Scaling User Guide](https://docs.aws.amazon.com/autoscaling/ec2/userguide/)
- [Elastic Load Balancing User Guide](https://docs.aws.amazon.com/elasticloadbalancing/latest/userguide/)

### Tools & SDKs
- **AWS CLI** - Command-line interface for EC2 operations
- **AWS SDKs** - Programmatic access to EC2 APIs
- **EC2 Instance Connect** - Browser-based SSH access
- **Systems Manager Session Manager** - Secure shell access without SSH

### Best Practices Guides
- [EC2 Best Practices](https://docs.aws.amazon.com/ec2/latest/userguide/ec2-best-practices.html)
- [Security Best Practices](https://docs.aws.amazon.com/ec2/latest/userguide/ec2-security.html)
- [Cost Optimization Guide](https://aws.amazon.com/ec2/cost-and-capacity/)
- [Performance Guidelines](https://docs.aws.amazon.com/ec2/latest/userguide/ec2-instance-recommendations.html)

### Community Resources
- **AWS Architecture Center** - Reference architectures and best practices
- **AWS Well-Architected Framework** - Design principles and best practices
- **AWS Solutions Library** - Pre-built solutions and patterns