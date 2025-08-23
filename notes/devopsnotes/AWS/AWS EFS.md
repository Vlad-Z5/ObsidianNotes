# AWS EFS: Enterprise Elastic File System & Scalable NFS Storage

> **Service Type:** Storage | **Scope:** Regional | **Serverless:** Yes

## Overview

Amazon Elastic File System (EFS) provides fully managed, scalable, and elastic NFS storage for Linux-based workloads. It automatically grows and shrinks as files are added or removed, delivering consistent performance and durability across multiple Availability Zones with seamless integration into AWS services and on-premises environments.

## Core Architecture Components

- **Protocol:** Managed **NFS v4.1** with POSIX-compliant file system semantics
- **Accessibility:** Mountable by **multiple EC2 instances** concurrently across AZs
- **Scalability:** Auto-scales from GB to PB with no pre-provisioning required
- **Performance Modes:**
  - **General Purpose:** Up to 7,000 file operations/second with low latency
  - **Max I/O:** Higher aggregate throughput and operations per second (>7,000 ops/sec)
- **Throughput Modes:**
  - **Bursting:** Scales throughput with file system size
  - **Provisioned:** Consistent throughput independent of storage size
- **Storage Classes:**
  - **Standard:** Frequent access storage with 99.999% durability
  - **Infrequent Access (IA):** Cost-optimized for files accessed less frequently
- **Security:** Encryption at rest and in transit, VPC isolation, IAM integration

## Enterprise Use Cases & Step-by-Step Implementation

### Use Case 1: High-Availability WordPress Multi-Site Network

**Business Requirement:** Deploy WordPress multi-site network serving 500,000+ monthly visitors across multiple regions with shared media storage.

**Step-by-Step Implementation:**
1. **Architecture Planning**
   - Estimate storage needs: 200GB media files, 50GB WordPress core files
   - Calculate traffic: 2M page views/month = ~770 requests/hour peak
   - Plan for global content distribution via CloudFront

2. **EFS File System Creation**
   ```bash
   # Create EFS file system with encryption
   aws efs create-file-system \
     --creation-token wordpress-shared-storage-$(date +%s) \
     --performance-mode generalPurpose \
     --throughput-mode provisioned \
     --provisioned-throughput-in-mibps 100 \
     --encrypted \
     --tags Key=Name,Value=WordPress-Shared-Storage
   ```

3. **Multi-AZ Mount Targets Setup**
   ```bash
   # Create mount targets in each availability zone
   for subnet in subnet-12345678 subnet-87654321 subnet-11223344; do
     aws efs create-mount-target \
       --file-system-id fs-xxxxxxxxx \
       --subnet-id $subnet \
       --security-groups sg-xxxxxxxxx
   done
   ```

4. **WordPress Configuration**
   - Deploy WordPress on Auto Scaling Group across 3 AZs
   - Mount EFS at `/var/www/html/wp-content/uploads` for media files
   - Configure WordPress multisite with shared uploads directory
   - Implement Redis ElastiCache for object caching

5. **Performance Optimization**
   ```bash
   # Optimize EFS mount options for WordPress
   echo "fs-xxxxxxxxx.efs.us-east-1.amazonaws.com:/ /var/www/html/wp-content/uploads efs tls,_netdev,iam" >> /etc/fstab
   mount -a
   
   # Configure nginx for static file caching
   location ~* \.(jpg|jpeg|png|gif|ico|css|js)$ {
     expires 1y;
     add_header Cache-Control "public, immutable";
   }
   ```

**Expected Outcome:** 99.9% uptime, automatic scaling to handle traffic spikes, 40% cost reduction on storage

### Use Case 2: Container-Based Microservices with Shared Configuration

**Business Requirement:** Deploy microservices architecture on EKS with shared configuration files and persistent logging across 50+ services.

**Step-by-Step Implementation:**
1. **Microservices Assessment**
   - Service count: 50 microservices across 3 environments (dev/staging/prod)
   - Configuration files: 500MB per environment
   - Log retention: 30 days with 10GB daily log generation
   - Shared assets: 5GB of common templates and resources

2. **EFS CSI Driver Installation**
   ```bash
   # Install EFS CSI driver on EKS cluster
   kubectl apply -k "github.com/kubernetes-sigs/aws-efs-csi-driver/deploy/kubernetes/overlays/stable/?ref=master"
   
   # Create storage class for EFS
   cat <<EOF | kubectl apply -f -
   apiVersion: storage.k8s.io/v1
   kind: StorageClass
   metadata:
     name: efs-sc
   provisioner: efs.csi.aws.com
   parameters:
     provisioningMode: efs-ap
     fileSystemId: fs-xxxxxxxxx
     directoryPerms: "0755"
   EOF
   ```

3. **Persistent Volume Configuration**
   ```yaml
   # Create PersistentVolume for shared config
   apiVersion: v1
   kind: PersistentVolume
   metadata:
     name: shared-config-pv
   spec:
     capacity:
       storage: 100Gi
     volumeMode: Filesystem
     accessModes:
       - ReadWriteMany
     persistentVolumeReclaimPolicy: Retain
     csi:
       driver: efs.csi.aws.com
       volumeHandle: fs-xxxxxxxxx
   ```

4. **Microservice Deployment with Shared Volumes**
   ```yaml
   # Deploy microservice with EFS mount
   apiVersion: apps/v1
   kind: Deployment
   metadata:
     name: user-service
   spec:
     replicas: 3
     template:
       spec:
         containers:
         - name: user-service
           image: user-service:v1.2.0
           volumeMounts:
           - name: shared-config
             mountPath: /app/config
           - name: shared-logs
             mountPath: /app/logs
         volumes:
         - name: shared-config
           persistentVolumeClaim:
             claimName: shared-config-pvc
         - name: shared-logs
           persistentVolumeClaim:
             claimName: shared-logs-pvc
   ```

**Expected Outcome:** Zero-downtime configuration updates, centralized logging, 60% faster deployment times

### Use Case 3: Machine Learning Training Pipeline with Shared Datasets

**Business Requirement:** Implement ML training pipeline for computer vision models requiring access to 10TB shared dataset across multiple training nodes.

**Step-by-Step Implementation:**
1. **Dataset and Compute Planning**
   - Training dataset: 10TB of images and annotations
   - Training cluster: 16 GPU instances (p3.8xlarge) for distributed training
   - Model checkpoints: 50GB per experiment, 100 experiments/month
   - Inference deployment: Real-time model serving

2. **High-Performance EFS Configuration**
   ```bash
   # Create EFS with Max I/O performance mode
   aws efs create-file-system \
     --creation-token ml-training-datasets-$(date +%s) \
     --performance-mode maxIO \
     --throughput-mode provisioned \
     --provisioned-throughput-in-mibps 2000 \
     --encrypted
   ```

3. **Training Infrastructure Setup**
   ```python
   # PyTorch distributed training with EFS datasets
   import torch
   import torch.distributed as dist
   from torch.utils.data import DataLoader, DistributedSampler
   from torchvision import datasets, transforms
   
   def setup_distributed_training():
       # Mount EFS dataset directory
       dataset_path = "/mnt/efs/training-data"
       checkpoint_path = "/mnt/efs/model-checkpoints"
       
       # Initialize distributed training
       dist.init_process_group(backend='nccl')
       
       # Load dataset from EFS
       transform = transforms.Compose([
           transforms.Resize((224, 224)),
           transforms.ToTensor(),
           transforms.Normalize(mean=[0.485, 0.456, 0.406],
                              std=[0.229, 0.224, 0.225])
       ])
       
       dataset = datasets.ImageFolder(dataset_path, transform=transform)
       sampler = DistributedSampler(dataset)
       dataloader = DataLoader(dataset, batch_size=32, sampler=sampler)
       
       return dataloader, checkpoint_path
   ```

4. **Performance Monitoring and Optimization**
   ```bash
   # Monitor EFS performance metrics
   aws cloudwatch get-metric-statistics \
     --namespace AWS/EFS \
     --metric-name TotalIOBytes \
     --dimensions Name=FileSystemId,Value=fs-xxxxxxxxx \
     --start-time 2024-01-01T00:00:00Z \
     --end-time 2024-01-02T00:00:00Z \
     --period 3600 \
     --statistics Sum
   
   # Optimize mount options for ML workload
   mount -t efs -o tls,_netdev,fsc,iam fs-xxxxxxxxx.efs.us-east-1.amazonaws.com:/ /mnt/efs
   ```

**Expected Outcome:** 30% faster training times, seamless dataset versioning, automated model checkpoint management

### Use Case 4: Enterprise Content Management and Collaboration Platform

**Business Requirement:** Deploy enterprise document management system supporting 5,000 concurrent users with document versioning and full-text search.

**Step-by-Step Implementation:**
1. **System Requirements Analysis**
   - User base: 5,000 concurrent users, 25,000 total users
   - Document storage: 50TB initial, 10TB annual growth
   - Search index: 5TB Elasticsearch cluster
   - Collaboration features: Real-time editing, version control, audit trails

2. **EFS with Access Points Configuration**
   ```bash
   # Create EFS access points for different user groups
   aws efs create-access-point \
     --file-system-id fs-xxxxxxxxx \
     --posix-user Uid=1000,Gid=1000 \
     --root-directory Path=/documents,CreationInfo='{OwnerUid=1000,OwnerGid=1000,Permissions=755}' \
     --tags Key=Department,Value=HR
   
   aws efs create-access-point \
     --file-system-id fs-xxxxxxxxx \
     --posix-user Uid=2000,Gid=2000 \
     --root-directory Path=/finance,CreationInfo='{OwnerUid=2000,OwnerGid=2000,Permissions=750}' \
     --tags Key=Department,Value=Finance
   ```

3. **Application Architecture with EFS**
   ```bash
   # Deploy document management application
   docker run -d \
     --name document-management \
     -p 8080:8080 \
     -v /mnt/efs/documents:/app/storage/documents \
     -v /mnt/efs/search-index:/app/elasticsearch/data \
     -e DATABASE_URL=postgresql://rds-endpoint:5432/docmgmt \
     -e ELASTICSEARCH_URL=https://es-cluster-endpoint:9200 \
     enterprise/document-management:latest
   ```

4. **Backup and Lifecycle Management**
   ```bash
   # Configure EFS backup policy
   aws efs put-backup-policy \
     --file-system-id fs-xxxxxxxxx \
     --backup-policy Status=ENABLED
   
   # Set up lifecycle policy for cost optimization
   aws efs put-lifecycle-configuration \
     --file-system-id fs-xxxxxxxxx \
     --lifecycle-policies \
     TransitionToIA=AFTER_30_DAYS,TransitionToPrimaryStorageClass=AFTER_1_ACCESS
   ```

**Expected Outcome:** 99.95% availability, 50% storage cost reduction, enterprise-grade security and compliance

## Advanced Implementation Patterns

### Performance Optimization Strategies
```bash
# Optimize for different workload patterns

# High-throughput scientific workloads
mount -t efs -o nfsvers=4.1,rsize=1048576,wsize=1048576 fs-xxxxxxxxx.efs.region.amazonaws.com:/ /mnt/data

# General purpose web applications  
mount -t efs -o nfsvers=4.1,rsize=65536,wsize=65536 fs-xxxxxxxxx.efs.region.amazonaws.com:/ /var/www/shared

# Database and log files (optimize for small files)
mount -t efs -o nfsvers=4.1,rsize=32768,wsize=32768 fs-xxxxxxxxx.efs.region.amazonaws.com:/ /var/log/shared
```

### Multi-Region Backup and Disaster Recovery
```bash
# Configure cross-region EFS replication
aws efs create-replication-configuration \
  --source-file-system-id fs-xxxxxxxxx \
  --destinations Region=us-west-2,KmsKeyId=arn:aws:kms:us-west-2:account:key/key-id

# Monitor replication status
aws efs describe-replication-configurations \
  --file-system-id fs-xxxxxxxxx
```

### Security and Compliance Implementation
- **Encryption:** Transit and at-rest encryption with AWS KMS integration
- **Access Control:** IAM policies, POSIX permissions, and EFS Access Points
- **Network Security:** VPC isolation, security groups, and VPC endpoints
- **Audit Logging:** CloudTrail integration for API calls and file access monitoring
- **Compliance:** Support for HIPAA, PCI DSS, and SOC compliance frameworks

### Cost Optimization Techniques
1. **Storage Classes:** Automatic transition to IA storage class for infrequently accessed files
2. **Lifecycle Policies:** Automated file archival based on access patterns
3. **Provisioned Throughput:** Match throughput capacity to actual workload requirements  
4. **Regional Optimization:** Choose regions based on data locality and cost structure
5. **Monitoring:** CloudWatch metrics for storage utilization and access patterns analysis

### Integration with AWS Services
- **EKS/ECS:** Container orchestration with persistent volumes
- **Lambda:** Serverless file processing and transformation
- **SageMaker:** Machine learning model storage and dataset management
- **AWS Backup:** Automated backup policies and point-in-time recovery
- **CloudFormation:** Infrastructure as Code deployment templates

## Service Features & Capabilities

### Storage Performance Modes

#### General Purpose Mode
- **Max File Operations:** 7,000 operations per second
- **Latency:** Lowest latency per operation
- **Use Cases:** Web applications, content management, general file sharing
- **Burst Credits:** Accumulates during low activity periods

#### Max I/O Mode
- **Max File Operations:** >7,000 operations per second (virtually unlimited)
- **Latency:** Slightly higher latency per operation
- **Use Cases:** Highly parallel workloads, big data analytics
- **Scalability:** Linear scaling with concurrent clients

### Throughput Configuration

```python
def configure_efs_throughput(file_system_id, throughput_mode, provisioned_mibps=None):
    efs = boto3.client('efs')
    
    modify_params = {
        'FileSystemId': file_system_id,
        'ThroughputMode': throughput_mode
    }
    
    if throughput_mode == 'provisioned' and provisioned_mibps:
        modify_params['ProvisionedThroughputInMibps'] = provisioned_mibps
    
    response = efs.modify_file_system(**modify_params)
    return response
```

### Access Points Management

```python
class EFSAccessPointManager:
    def __init__(self):
        self.efs = boto3.client('efs')
    
    def create_department_access_point(self, file_system_id, department, uid, gid):
        access_point = self.efs.create_access_point(
            FileSystemId=file_system_id,
            PosixUser={
                'Uid': uid,
                'Gid': gid
            },
            RootDirectory={
                'Path': f'/{department.lower()}',
                'CreationInfo': {
                    'OwnerUid': uid,
                    'OwnerGid': gid,
                    'Permissions': '755'
                }
            },
            Tags=[
                {'Key': 'Department', 'Value': department},
                {'Key': 'Purpose', 'Value': 'DepartmentStorage'}
            ]
        )
        return access_point['AccessPointArn']
    
    def list_access_points(self, file_system_id):
        response = self.efs.describe_access_points(FileSystemId=file_system_id)
        return response['AccessPoints']
```

## Configuration & Setup

### Basic EFS Creation

```python
import boto3
from datetime import datetime

def create_efs_file_system(name, performance_mode='generalPurpose', throughput_mode='bursting'):
    efs = boto3.client('efs')
    
    response = efs.create_file_system(
        CreationToken=f"{name}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        PerformanceMode=performance_mode,
        ThroughputMode=throughput_mode,
        Encrypted=True,
        Tags=[
            {'Key': 'Name', 'Value': name},
            {'Key': 'CreatedAt', 'Value': datetime.now().isoformat()}
        ]
    )
    return response['FileSystemId']
```

### Mount Targets Setup

```bash
#!/bin/bash
# Create mount targets across all subnets in VPC

FILE_SYSTEM_ID="fs-xxxxxxxxx"
SECURITY_GROUP_ID="sg-xxxxxxxxx"

# Get all subnets in the VPC
SUBNETS=$(aws ec2 describe-subnets \
  --filters "Name=vpc-id,Values=$VPC_ID" \
  --query 'Subnets[].SubnetId' \
  --output text)

# Create mount target in each subnet
for subnet in $SUBNETS; do
  aws efs create-mount-target \
    --file-system-id $FILE_SYSTEM_ID \
    --subnet-id $subnet \
    --security-groups $SECURITY_GROUP_ID
  echo "Created mount target in subnet: $subnet"
done
```

### Client Configuration

```bash
# Install EFS utilities
sudo yum install -y amazon-efs-utils  # Amazon Linux
sudo apt-get install -y amazon-efs-utils  # Ubuntu

# Mount with IAM authentication
sudo mkdir -p /mnt/efs
echo "fs-xxxxxxxxx.efs.us-east-1.amazonaws.com:/ /mnt/efs efs tls,_netdev,iam" >> /etc/fstab
sudo mount -a

# Mount with encryption in transit
sudo mount -t efs -o tls fs-xxxxxxxxx.efs.us-east-1.amazonaws.com:/ /mnt/efs

# Mount with access point
sudo mount -t efs -o tls,accesspoint=fsap-xxxxxxxxx fs-xxxxxxxxx.efs.us-east-1.amazonaws.com:/ /mnt/efs
```

## Monitoring & Observability

### CloudWatch Metrics Monitoring

```python
class EFSMonitoring:
    def __init__(self):
        self.cloudwatch = boto3.client('cloudwatch')
        self.efs = boto3.client('efs')
    
    def setup_efs_alarms(self, file_system_id, sns_topic_arn):
        # High burst credit consumption alarm
        self.cloudwatch.put_metric_alarm(
            AlarmName=f'EFS-LowBurstCredits-{file_system_id}',
            ComparisonOperator='LessThanThreshold',
            EvaluationPeriods=2,
            MetricName='BurstCreditBalance',
            Namespace='AWS/EFS',
            Period=300,
            Statistic='Average',
            Threshold=1000000000.0,  # 1 GB worth of credits
            ActionsEnabled=True,
            AlarmActions=[sns_topic_arn],
            AlarmDescription='EFS burst credit balance is low',
            Dimensions=[
                {'Name': 'FileSystemId', 'Value': file_system_id}
            ]
        )
        
        # High I/O utilization alarm
        self.cloudwatch.put_metric_alarm(
            AlarmName=f'EFS-HighIOUtilization-{file_system_id}',
            ComparisonOperator='GreaterThanThreshold',
            EvaluationPeriods=3,
            MetricName='PercentIOLimit',
            Namespace='AWS/EFS',
            Period=300,
            Statistic='Average',
            Threshold=80.0,
            ActionsEnabled=True,
            AlarmActions=[sns_topic_arn],
            AlarmDescription='EFS I/O utilization is high'
        )
    
    def get_file_system_metrics(self, file_system_id, start_time, end_time):
        metrics = {}
        
        # Get storage size metrics
        size_response = self.cloudwatch.get_metric_statistics(
            Namespace='AWS/EFS',
            MetricName='SizeInBytes',
            Dimensions=[
                {'Name': 'FileSystemId', 'Value': file_system_id},
                {'Name': 'StorageClass', 'Value': 'Standard'}
            ],
            StartTime=start_time,
            EndTime=end_time,
            Period=3600,
            Statistics=['Average']
        )
        metrics['storage_size'] = size_response['Datapoints']
        
        # Get I/O metrics
        io_response = self.cloudwatch.get_metric_statistics(
            Namespace='AWS/EFS',
            MetricName='TotalIOBytes',
            Dimensions=[{'Name': 'FileSystemId', 'Value': file_system_id}],
            StartTime=start_time,
            EndTime=end_time,
            Period=3600,
            Statistics=['Sum']
        )
        metrics['total_io'] = io_response['Datapoints']
        
        return metrics
```

### Performance Analysis

```bash
# Monitor EFS performance from client side
nfsstat -m  # Show mount statistics
iostat -x 1 5  # Monitor I/O statistics

# Check EFS throughput utilization
aws cloudwatch get-metric-statistics \
  --namespace AWS/EFS \
  --metric-name PercentIOLimit \
  --dimensions Name=FileSystemId,Value=fs-xxxxxxxxx \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Average
```

## Security & Compliance

### Encryption Configuration

```python
def create_encrypted_efs():
    efs = boto3.client('efs')
    kms = boto3.client('kms')
    
    # Create customer-managed KMS key for EFS
    key_response = kms.create_key(
        Description='EFS encryption key for enterprise data',
        Usage='ENCRYPT_DECRYPT'
    )
    kms_key_id = key_response['KeyMetadata']['KeyId']
    
    # Create encrypted EFS file system
    file_system = efs.create_file_system(
        CreationToken=f'encrypted-efs-{datetime.now().strftime("%Y%m%d%H%M%S")}',
        PerformanceMode='generalPurpose',
        Encrypted=True,
        KmsKeyId=kms_key_id,
        Tags=[
            {'Key': 'Encryption', 'Value': 'CustomerManagedKMS'},
            {'Key': 'Compliance', 'Value': 'Required'}
        ]
    )
    
    return file_system['FileSystemId'], kms_key_id
```

### Access Control Policies

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "elasticfilesystem:ClientMount",
                "elasticfilesystem:ClientWrite",
                "elasticfilesystem:ClientRootAccess"
            ],
            "Resource": "*",
            "Condition": {
                "Bool": {
                    "aws:SecureTransport": "true"
                },
                "StringEquals": {
                    "elasticfilesystem:AccessPointArn": "arn:aws:elasticfilesystem:region:account:access-point/fsap-xxxxxxxxx"
                }
            }
        },
        {
            "Effect": "Deny",
            "Action": "*",
            "Resource": "*",
            "Condition": {
                "Bool": {
                    "aws:SecureTransport": "false"
                }
            }
        }
    ]
}
```

### VPC Endpoint Configuration

```python
def create_efs_vpc_endpoint(vpc_id, subnet_ids, security_group_id):
    ec2 = boto3.client('ec2')
    
    response = ec2.create_vpc_endpoint(
        VpcId=vpc_id,
        ServiceName='com.amazonaws.region.elasticfilesystem',
        VpcEndpointType='Interface',
        SubnetIds=subnet_ids,
        SecurityGroupIds=[security_group_id],
        PolicyDocument=json.dumps({
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": "*",
                    "Action": [
                        "elasticfilesystem:*"
                    ],
                    "Resource": "*"
                }
            ]
        })
    )
    return response['VpcEndpoint']['VpcEndpointId']
```

## Cost Optimization

### Storage Class Management

```python
class EFSCostOptimizer:
    def __init__(self):
        self.efs = boto3.client('efs')
        self.cloudwatch = boto3.client('cloudwatch')
    
    def setup_lifecycle_policy(self, file_system_id, transition_to_ia='AFTER_30_DAYS'):
        lifecycle_policy = self.efs.put_lifecycle_configuration(
            FileSystemId=file_system_id,
            LifecyclePolicies=[
                {
                    'TransitionToIA': transition_to_ia,
                    'TransitionToPrimaryStorageClass': 'AFTER_1_ACCESS'
                }
            ]
        )
        return lifecycle_policy
    
    def analyze_storage_costs(self, file_system_id, days=30):
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)
        
        # Get standard storage size
        standard_storage = self.cloudwatch.get_metric_statistics(
            Namespace='AWS/EFS',
            MetricName='SizeInBytes',
            Dimensions=[
                {'Name': 'FileSystemId', 'Value': file_system_id},
                {'Name': 'StorageClass', 'Value': 'Standard'}
            ],
            StartTime=start_time,
            EndTime=end_time,
            Period=86400,
            Statistics=['Average']
        )
        
        # Get IA storage size
        ia_storage = self.cloudwatch.get_metric_statistics(
            Namespace='AWS/EFS',
            MetricName='SizeInBytes',
            Dimensions=[
                {'Name': 'FileSystemId', 'Value': file_system_id},
                {'Name': 'StorageClass', 'Value': 'InfrequentAccess'}
            ],
            StartTime=start_time,
            EndTime=end_time,
            Period=86400,
            Statistics=['Average']
        )
        
        # Calculate cost savings
        if standard_storage['Datapoints'] and ia_storage['Datapoints']:
            latest_standard = standard_storage['Datapoints'][-1]['Average'] / (1024**3)  # GB
            latest_ia = ia_storage['Datapoints'][-1]['Average'] / (1024**3)  # GB
            
            # Estimated monthly costs (example pricing)
            standard_cost = latest_standard * 0.30  # $0.30/GB
            ia_cost = latest_ia * 0.0125  # $0.0125/GB
            
            return {
                'standard_storage_gb': latest_standard,
                'ia_storage_gb': latest_ia,
                'estimated_monthly_cost': standard_cost + ia_cost,
                'potential_savings': (latest_standard + latest_ia) * 0.30 - (standard_cost + ia_cost)
            }
```

### Throughput Optimization

```python
def optimize_throughput_mode(file_system_id):
    efs = boto3.client('efs')
    cloudwatch = boto3.client('cloudwatch')
    
    # Analyze throughput usage over past week
    end_time = datetime.now()
    start_time = end_time - timedelta(days=7)
    
    throughput_metrics = cloudwatch.get_metric_statistics(
        Namespace='AWS/EFS',
        MetricName='MeteredIOBytes',
        Dimensions=[{'Name': 'FileSystemId', 'Value': file_system_id}],
        StartTime=start_time,
        EndTime=end_time,
        Period=3600,
        Statistics=['Average', 'Maximum']
    )
    
    if throughput_metrics['Datapoints']:
        avg_throughput = sum(d['Average'] for d in throughput_metrics['Datapoints']) / len(throughput_metrics['Datapoints'])
        max_throughput = max(d['Maximum'] for d in throughput_metrics['Datapoints'])
        
        # Convert to MiBps (approximate)
        avg_mibps = (avg_throughput / (1024*1024)) / 3600
        max_mibps = (max_throughput / (1024*1024)) / 3600
        
        # Recommend throughput mode
        if avg_mibps > 100:
            recommendation = f"Consider provisioned throughput mode with {int(max_mibps * 1.2)} MiBps"
        else:
            recommendation = "Bursting throughput mode is optimal for current usage"
        
        return {
            'current_avg_mibps': avg_mibps,
            'current_max_mibps': max_mibps,
            'recommendation': recommendation
        }
```

## Automation & Infrastructure as Code

### CloudFormation Template

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Parameters:
  Environment:
    Type: String
    Default: dev
    AllowedValues: [dev, staging, prod]
  PerformanceMode:
    Type: String
    Default: generalPurpose
    AllowedValues: [generalPurpose, maxIO]
  ThroughputMode:
    Type: String
    Default: bursting
    AllowedValues: [bursting, provisioned]

Resources:
  EFSFileSystem:
    Type: AWS::EFS::FileSystem
    Properties:
      PerformanceMode: !Ref PerformanceMode
      ThroughputMode: !Ref ThroughputMode
      Encrypted: true
      FileSystemTags:
        - Key: Name
          Value: !Sub '${AWS::StackName}-EFS-${Environment}'
        - Key: Environment
          Value: !Ref Environment

  EFSMountTarget1:
    Type: AWS::EFS::MountTarget
    Properties:
      FileSystemId: !Ref EFSFileSystem
      SubnetId: !Ref PrivateSubnet1
      SecurityGroups:
        - !Ref EFSSecurityGroup

  EFSMountTarget2:
    Type: AWS::EFS::MountTarget
    Properties:
      FileSystemId: !Ref EFSFileSystem
      SubnetId: !Ref PrivateSubnet2
      SecurityGroups:
        - !Ref EFSSecurityGroup

  EFSAccessPoint:
    Type: AWS::EFS::AccessPoint
    Properties:
      FileSystemId: !Ref EFSFileSystem
      PosixUser:
        Uid: 1000
        Gid: 1000
      RootDirectory:
        Path: "/shared"
        CreationInfo:
          OwnerUid: 1000
          OwnerGid: 1000
          Permissions: "755"
      AccessPointTags:
        - Key: Name
          Value: SharedAccessPoint

  EFSSecurityGroup:
    Type: AWS::EC2::SecurityGroup
    Properties:
      GroupDescription: Security group for EFS mount targets
      VpcId: !Ref VPC
      SecurityGroupIngress:
        - IpProtocol: tcp
          FromPort: 2049
          ToPort: 2049
          SourceSecurityGroupId: !Ref ApplicationSecurityGroup
      Tags:
        - Key: Name
          Value: EFS-SecurityGroup

Outputs:
  FileSystemId:
    Description: EFS File System ID
    Value: !Ref EFSFileSystem
    Export:
      Name: !Sub '${AWS::StackName}-EFS-ID'
  
  AccessPointArn:
    Description: EFS Access Point ARN
    Value: !GetAtt EFSAccessPoint.Arn
    Export:
      Name: !Sub '${AWS::StackName}-EFS-AccessPoint-ARN'
```

### Terraform Configuration

```hcl
resource "aws_efs_file_system" "main" {
  creation_token   = "${var.application_name}-efs-${var.environment}"
  performance_mode = var.performance_mode
  throughput_mode  = var.throughput_mode
  encrypted        = true
  kms_key_id       = aws_kms_key.efs.arn

  lifecycle_policy {
    transition_to_ia                    = "AFTER_30_DAYS"
    transition_to_primary_storage_class = "AFTER_1_ACCESS"
  }

  tags = {
    Name        = "${var.application_name}-EFS-${var.environment}"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

resource "aws_efs_mount_target" "main" {
  count           = length(var.private_subnet_ids)
  file_system_id  = aws_efs_file_system.main.id
  subnet_id       = var.private_subnet_ids[count.index]
  security_groups = [aws_security_group.efs.id]
}

resource "aws_efs_access_point" "shared" {
  file_system_id = aws_efs_file_system.main.id

  posix_user {
    gid = 1000
    uid = 1000
  }

  root_directory {
    path = "/shared"
    creation_info {
      owner_gid   = 1000
      owner_uid   = 1000
      permissions = "755"
    }
  }

  tags = {
    Name = "${var.application_name}-shared-access-point"
  }
}

resource "aws_efs_backup_policy" "main" {
  file_system_id = aws_efs_file_system.main.id

  backup_policy {
    status = "ENABLED"
  }
}
```

### Automated Deployment Script

```python
class EFSDeploymentManager:
    def __init__(self):
        self.efs = boto3.client('efs')
        self.ec2 = boto3.client('ec2')
    
    def deploy_efs_infrastructure(self, config):
        # Create EFS file system
        file_system = self.efs.create_file_system(
            CreationToken=f"{config['name']}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            PerformanceMode=config.get('performance_mode', 'generalPurpose'),
            ThroughputMode=config.get('throughput_mode', 'bursting'),
            Encrypted=True,
            Tags=config.get('tags', [])
        )
        file_system_id = file_system['FileSystemId']
        
        # Wait for file system to be available
        waiter = self.efs.get_waiter('file_system_available')
        waiter.wait(FileSystemId=file_system_id)
        
        # Create mount targets
        mount_target_ids = []
        for subnet_id in config['subnet_ids']:
            mount_target = self.efs.create_mount_target(
                FileSystemId=file_system_id,
                SubnetId=subnet_id,
                SecurityGroups=config['security_group_ids']
            )
            mount_target_ids.append(mount_target['MountTargetId'])
        
        # Create access points
        access_point_arns = []
        for ap_config in config.get('access_points', []):
            access_point = self.efs.create_access_point(
                FileSystemId=file_system_id,
                PosixUser=ap_config['posix_user'],
                RootDirectory=ap_config['root_directory'],
                Tags=ap_config.get('tags', [])
            )
            access_point_arns.append(access_point['AccessPointArn'])
        
        return {
            'file_system_id': file_system_id,
            'mount_target_ids': mount_target_ids,
            'access_point_arns': access_point_arns
        }
```

## Troubleshooting & Operations

### Common Issues and Solutions

#### Mount Issues
```python
def diagnose_mount_issues(file_system_id, instance_id):
    efs = boto3.client('efs')
    ec2 = boto3.client('ec2')
    
    issues = []
    
    # Check file system state
    fs_response = efs.describe_file_systems(FileSystemIds=[file_system_id])
    fs_state = fs_response['FileSystems'][0]['LifeCycleState']
    
    if fs_state != 'available':
        issues.append(f"File system state is {fs_state}, expected 'available'")
    
    # Check mount targets
    mt_response = efs.describe_mount_targets(FileSystemId=file_system_id)
    mount_targets = mt_response['MountTargets']
    
    # Get instance details
    instance_response = ec2.describe_instances(InstanceIds=[instance_id])
    instance_subnet = instance_response['Reservations'][0]['Instances'][0]['SubnetId']
    
    # Check if mount target exists in instance subnet
    mt_in_subnet = any(mt['SubnetId'] == instance_subnet for mt in mount_targets)
    if not mt_in_subnet:
        issues.append(f"No mount target found in instance subnet {instance_subnet}")
    
    # Check mount target states
    for mt in mount_targets:
        if mt['LifeCycleState'] != 'available':
            issues.append(f"Mount target {mt['MountTargetId']} state is {mt['LifeCycleState']}")
    
    return issues

def fix_dns_resolution_issue():
    """Fix DNS resolution for EFS mount targets"""
    commands = [
        "sudo yum update -y",
        "sudo yum install -y amazon-efs-utils",
        "echo '169.254.169.253 fs-xxxxxxxxx.efs.region.amazonaws.com' | sudo tee -a /etc/hosts",
        "sudo service amazon-ssm-agent restart"
    ]
    return commands
```

#### Performance Issues
```bash
#!/bin/bash
# Diagnose EFS performance issues

echo "Checking EFS mount options..."
mount | grep efs

echo "Checking NFS statistics..."
nfsstat -m

echo "Checking I/O patterns..."
iostat -x 1 5

echo "Testing EFS performance..."
# Write test
dd if=/dev/zero of=/mnt/efs/testfile bs=1M count=1000

# Read test
dd if=/mnt/efs/testfile of=/dev/null bs=1M

# Clean up
rm /mnt/efs/testfile
```

#### Network Connectivity
```python
def test_efs_connectivity(file_system_id, region):
    import socket
    import subprocess
    
    efs_hostname = f"{file_system_id}.efs.{region}.amazonaws.com"
    
    # Test DNS resolution
    try:
        ip_address = socket.gethostbyname(efs_hostname)
        print(f"DNS resolution successful: {efs_hostname} -> {ip_address}")
    except socket.gaierror:
        print(f"DNS resolution failed for {efs_hostname}")
        return False
    
    # Test port connectivity
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((ip_address, 2049))
        sock.close()
        
        if result == 0:
            print("NFS port 2049 is accessible")
            return True
        else:
            print("NFS port 2049 is not accessible")
            return False
    except Exception as e:
        print(f"Connectivity test failed: {e}")
        return False
```

#### Backup and Recovery Operations
```python
def restore_from_backup(backup_id, new_file_system_name):
    efs = boto3.client('efs')
    
    # Create file system from backup
    restore_response = efs.restore_file_system(
        BackupId=backup_id,
        CreationToken=f"{new_file_system_name}-restore-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    )
    
    return restore_response['FileSystemId']

def create_point_in_time_backup(file_system_id):
    backup = boto3.client('backup')
    
    backup_job = backup.start_backup_job(
        BackupVaultName='default',
        ResourceArn=f"arn:aws:elasticfilesystem:region:account:file-system/{file_system_id}",
        IamRoleArn='arn:aws:iam::account:role/aws-backup-service-role'
    )
    
    return backup_job['BackupJobId']
```

## Best Practices

### Performance Optimization
- **Choose the right performance mode** based on your I/O patterns
- **Use provisioned throughput** for consistent high-performance requirements
- **Optimize mount options** for your specific workload (rsize, wsize)
- **Enable EFS Intelligent Tiering** for automatic cost optimization
- **Use multiple mount targets** across availability zones for high availability

### Security Best Practices
- **Enable encryption** at rest and in transit for all file systems
- **Use access points** for fine-grained access control
- **Implement least-privilege IAM policies** for EFS operations
- **Monitor file system access** with CloudTrail logging
- **Use VPC endpoints** to keep traffic within AWS network

### Cost Management
- **Implement lifecycle policies** to transition files to IA storage
- **Monitor storage utilization** with CloudWatch metrics
- **Right-size throughput provisioning** based on actual usage
- **Use burst credits efficiently** for variable workloads
- **Regular cleanup** of unused files and directories

## Additional Resources

### AWS Documentation
- [Amazon EFS User Guide](https://docs.aws.amazon.com/efs/latest/ug/)
- [EFS Performance Guidelines](https://docs.aws.amazon.com/efs/latest/ug/performance.html)
- [EFS Security Best Practices](https://docs.aws.amazon.com/efs/latest/ug/security-considerations.html)

### Tools & Utilities
- **EFS Utils** - Enhanced mount helper and performance tools
- **AWS CLI** - Command-line interface for EFS management
- **CloudFormation/Terraform** - Infrastructure as Code templates

### Integration Guides
- [EFS with Containers](https://docs.aws.amazon.com/efs/latest/ug/efs-containers.html)
- [EFS with Lambda](https://docs.aws.amazon.com/lambda/latest/dg/services-efs.html)
- [EFS Backup Strategies](https://docs.aws.amazon.com/efs/latest/ug/awsbackup.html)
