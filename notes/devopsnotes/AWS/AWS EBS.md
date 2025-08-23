# AWS EBS (Elastic Block Store)

> **Service Type:** Storage | **Scope:** Regional | **Serverless:** No

## Overview

AWS EBS provides persistent, high-performance block-level storage for EC2 instances. EBS volumes are designed for mission-critical workloads, offering consistent and low-latency performance for both throughput and IOPS-intensive applications.

- **Type:** Persistent, block-level storage for EC2, limited to one AZ, to replicate use snapshot
- **Attached To:** One EC2 instance at a time (can detach/attach), while EC2 can be attached to many EBS volumes
- **Provisioned capacity**: size in GB and IOPS, can be increased
- **Persistence:** Data persists beyond instance termination (unless "Delete on Termination" is enabled)
- **Snapshot:** Point-in-time backup stored in S3 (incremental after first snapshot)
- **Encryption:** Can be encrypted at rest (AES-256), in transit, and during snapshot copy

## Core Architecture Components

### Volume Types

#### Performance Modes
- **gp3:** General-purpose SSD (baseline + provisioned IOPS/throughput)
- **gp2:** Older general-purpose SSD (baseline based on size)
- **io2/io1:** High-performance SSD for critical workloads (provisioned IOPS), has option to attach to multiple EC2
- **st1:** Throughput-optimized HDD (big, sequential workloads)
- **sc1:** Cold HDD (infrequently accessed)

### Volume Properties
- **Resize:** Volume size and type can be modified without downtime
- **Multi-Attach:** io1/io2 can attach to multiple instances in the same AZ (only for certain use cases)
- Main use cases: databases, file systems, boot volumes, and apps requiring persistent storage

## DevOps & Enterprise Use Cases

### Database Storage
- **Production Databases** - High IOPS io2 volumes for transactional workloads
- **Data Warehousing** - st1 volumes for sequential read/write patterns
- **Development/Test** - gp3 volumes for cost-effective performance
- **Backup Storage** - sc1 volumes for long-term retention

### Application Storage
- **Web Applications** - Root volumes and application data storage
- **Content Management** - File storage for CMS platforms
- **Log Storage** - High-throughput storage for application logs
- **Container Storage** - Persistent volumes for containerized applications

### DevOps Integration
```python
import boto3
from datetime import datetime

class EBSManager:
    def __init__(self):
        self.ec2 = boto3.client('ec2')
    
    def create_volume_for_environment(self, size, volume_type, az, environment, application):
        tags = [
            {'Key': 'Environment', 'Value': environment},
            {'Key': 'Application', 'Value': application},
            {'Key': 'CreatedAt', 'Value': datetime.now().isoformat()},
            {'Key': 'ManagedBy', 'Value': 'DevOps'}
        ]
        
        response = self.ec2.create_volume(
            Size=size,
            VolumeType=volume_type,
            AvailabilityZone=az,
            TagSpecifications=[{
                'ResourceType': 'volume',
                'Tags': tags
            }]
        )
        return response['VolumeId']
```

## Service Features & Capabilities

### Volume Management

#### Increasing EBS Volume Size
```bash
# Modify Volume Size
aws ec2 modify-volume --volume-id vol-<volume> --size NEW_SIZE # Resize command

aws ec2 describe-volumes-modifications --volume-ids vol-<volume> # Wait until resize is complete

# Resize filesystem
sudo growpart /dev/<volume> # Extend partition if needed

sudo resize2fs /dev/<volume> # Resize for ext4
sudo xfs_growfs -d / # Resize for XFS
```

#### Decreasing EBS Volume Size
```bash
# Shrink filesystem
sudo umount /dev/xvdf
sudo e2fsck -f /dev/xvdf
sudo resize2fs /dev/xvdf 20G

# Backup and Snapshot
aws ec2 create-snapshot --volume-id vol-<volume>

# Create smaller EBS volume from snapshot
aws ec2 create-volume --snapshot-id snap-<id> --availability-zone <az> --size <size>

# Attach new volume to instance
aws ec2 attach-volume --volume-id vol-<new> --instance-id i-<instance> --device /dev/xvdg

# Mount points
sudo mkdir -p /mnt/oldvolume
sudo mkdir -p /mnt/newvolume

# Mount volumes
sudo mount /dev/xvdf /mnt/oldvolume
sudo mount /dev/xvdg /mnt/newvolume

# Data transfer
sudo rsync -aAXv /mnt/oldvolume/ /mnt/newvolume/

# Unmount old
sudo umount /mnt/oldvolume

# Detach old
aws ec2 detach-volume --volume-id vol-<old>

# Mount new in place of old
sudo mount /dev/xvdg /mnt/<original-mountpoint>

# Optional: update /etc/fstab

# Delete old
aws ec2 delete-volume --volume-id vol-<old>
```

### Snapshot Management
```bash
# Create snapshot
aws ec2 create-snapshot --volume-id vol-123456 --description "Daily backup"

# Copy snapshot to another region
aws ec2 copy-snapshot --source-region us-east-1 --source-snapshot-id snap-123456 --destination-region us-west-2

# Create volume from snapshot
aws ec2 create-volume --snapshot-id snap-123456 --availability-zone us-east-1a --volume-type gp3
```

## Configuration & Setup

### Volume Creation and Attachment
```python
def create_and_attach_volume(instance_id, size, volume_type='gp3', device='/dev/sdf'):
    ec2 = boto3.client('ec2')
    
    # Get instance details to determine AZ
    instance = ec2.describe_instances(InstanceIds=[instance_id])
    az = instance['Reservations'][0]['Instances'][0]['Placement']['AvailabilityZone']
    
    # Create volume
    volume = ec2.create_volume(
        Size=size,
        VolumeType=volume_type,
        AvailabilityZone=az,
        Encrypted=True
    )
    volume_id = volume['VolumeId']
    
    # Wait for volume to be available
    waiter = ec2.get_waiter('volume_available')
    waiter.wait(VolumeIds=[volume_id])
    
    # Attach volume
    ec2.attach_volume(
        VolumeId=volume_id,
        InstanceId=instance_id,
        Device=device
    )
    
    return volume_id
```

### Performance Configuration
```python
def optimize_volume_performance(volume_id, target_iops=None, target_throughput=None):
    ec2 = boto3.client('ec2')
    
    modify_params = {'VolumeId': volume_id}
    
    if target_iops:
        modify_params['Iops'] = target_iops
    if target_throughput:
        modify_params['Throughput'] = target_throughput
    
    response = ec2.modify_volume(**modify_params)
    
    # Monitor modification progress
    modifications = ec2.describe_volumes_modifications(VolumeIds=[volume_id])
    return modifications['VolumesModifications'][0]['ModificationState']
```

## Enterprise Implementation Examples

### Multi-Tier Application Storage
```python
class ApplicationStorageManager:
    def __init__(self):
        self.ec2 = boto3.client('ec2')
    
    def provision_application_storage(self, app_config):
        volumes = {}
        
        # Database tier - high IOPS
        if app_config.get('database'):
            volumes['database'] = self.ec2.create_volume(
                Size=app_config['database']['size'],
                VolumeType='io2',
                Iops=app_config['database']['iops'],
                AvailabilityZone=app_config['az'],
                Encrypted=True,
                KmsKeyId=app_config.get('kms_key'),
                TagSpecifications=[{
                    'ResourceType': 'volume',
                    'Tags': [
                        {'Key': 'Tier', 'Value': 'Database'},
                        {'Key': 'Application', 'Value': app_config['app_name']},
                        {'Key': 'Environment', 'Value': app_config['environment']}
                    ]
                }]
            )
        
        # Application tier - balanced performance
        if app_config.get('application'):
            volumes['application'] = self.ec2.create_volume(
                Size=app_config['application']['size'],
                VolumeType='gp3',
                AvailabilityZone=app_config['az'],
                Encrypted=True,
                TagSpecifications=[{
                    'ResourceType': 'volume',
                    'Tags': [
                        {'Key': 'Tier', 'Value': 'Application'},
                        {'Key': 'Application', 'Value': app_config['app_name']}
                    ]
                }]
            )
        
        # Log storage - throughput optimized
        if app_config.get('logs'):
            volumes['logs'] = self.ec2.create_volume(
                Size=app_config['logs']['size'],
                VolumeType='st1',
                AvailabilityZone=app_config['az'],
                Encrypted=True,
                TagSpecifications=[{
                    'ResourceType': 'volume',
                    'Tags': [
                        {'Key': 'Tier', 'Value': 'Logs'},
                        {'Key': 'Application', 'Value': app_config['app_name']}
                    ]
                }]
            )
        
        return volumes
```

### Automated Backup Strategy
```python
class EBSBackupManager:
    def __init__(self):
        self.ec2 = boto3.client('ec2')
    
    def create_application_backup(self, app_name, environment):
        # Find all volumes for the application
        volumes = self.ec2.describe_volumes(
            Filters=[
                {'Name': 'tag:Application', 'Values': [app_name]},
                {'Name': 'tag:Environment', 'Values': [environment]},
                {'Name': 'state', 'Values': ['in-use', 'available']}
            ]
        )
        
        snapshot_ids = []
        for volume in volumes['Volumes']:
            volume_id = volume['VolumeId']
            
            # Create snapshot
            snapshot = self.ec2.create_snapshot(
                VolumeId=volume_id,
                Description=f"Automated backup for {app_name}-{environment}",
                TagSpecifications=[{
                    'ResourceType': 'snapshot',
                    'Tags': [
                        {'Key': 'Application', 'Value': app_name},
                        {'Key': 'Environment', 'Value': environment},
                        {'Key': 'BackupType', 'Value': 'Automated'},
                        {'Key': 'CreatedAt', 'Value': datetime.now().isoformat()}
                    ]
                }]
            )
            snapshot_ids.append(snapshot['SnapshotId'])
        
        return snapshot_ids
```

## Monitoring & Observability

### CloudWatch Metrics
```python
def setup_ebs_monitoring(volume_id):
    cloudwatch = boto3.client('cloudwatch')
    
    # Create alarm for high IOPS utilization
    cloudwatch.put_metric_alarm(
        AlarmName=f'EBS-HighIOPS-{volume_id}',
        ComparisonOperator='GreaterThanThreshold',
        EvaluationPeriods=2,
        MetricName='VolumeReadOps',
        Namespace='AWS/EBS',
        Period=300,
        Statistic='Sum',
        Threshold=10000.0,
        ActionsEnabled=True,
        AlarmActions=['arn:aws:sns:region:account:topic'],
        AlarmDescription='EBS volume experiencing high IOPS',
        Dimensions=[
            {'Name': 'VolumeId', 'Value': volume_id}
        ]
    )
    
    # Create alarm for queue depth
    cloudwatch.put_metric_alarm(
        AlarmName=f'EBS-HighQueueDepth-{volume_id}',
        ComparisonOperator='GreaterThanThreshold',
        EvaluationPeriods=3,
        MetricName='VolumeQueueLength',
        Namespace='AWS/EBS',
        Period=300,
        Statistic='Average',
        Threshold=32.0,
        ActionsEnabled=True,
        AlarmActions=['arn:aws:sns:region:account:topic']
    )
```

### Performance Monitoring
```bash
# Monitor volume performance
aws cloudwatch get-metric-statistics \
  --namespace AWS/EBS \
  --metric-name VolumeReadOps \
  --dimensions Name=VolumeId,Value=vol-123456 \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum

# Check volume utilization
iostat -x 1
```

## Security & Compliance

### Encryption Configuration
```python
def create_encrypted_volume_with_cmk(size, volume_type, az, kms_key_id):
    ec2 = boto3.client('ec2')
    
    response = ec2.create_volume(
        Size=size,
        VolumeType=volume_type,
        AvailabilityZone=az,
        Encrypted=True,
        KmsKeyId=kms_key_id,
        TagSpecifications=[{
            'ResourceType': 'volume',
            'Tags': [
                {'Key': 'Encrypted', 'Value': 'true'},
                {'Key': 'KMSKey', 'Value': kms_key_id},
                {'Key': 'Compliance', 'Value': 'Required'}
            ]
        }]
    )
    return response['VolumeId']
```

### Access Control Policy
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "ec2:CreateVolume",
                "ec2:AttachVolume",
                "ec2:DetachVolume"
            ],
            "Resource": "*",
            "Condition": {
                "Bool": {
                    "ec2:Encrypted": "true"
                },
                "StringEquals": {
                    "ec2:VolumeType": ["gp3", "io2"]
                }
            }
        },
        {
            "Effect": "Allow",
            "Action": [
                "ec2:CreateSnapshot",
                "ec2:DeleteSnapshot"
            ],
            "Resource": "*",
            "Condition": {
                "StringEquals": {
                    "aws:RequestedRegion": ["us-east-1", "us-west-2"]
                }
            }
        }
    ]
}
```

## Cost Optimization

### Volume Type Optimization
```python
class EBSCostOptimizer:
    def __init__(self):
        self.ec2 = boto3.client('ec2')
        self.cloudwatch = boto3.client('cloudwatch')
    
    def analyze_volume_utilization(self, volume_id, days=30):
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)
        
        # Get IOPS utilization
        iops_metrics = self.cloudwatch.get_metric_statistics(
            Namespace='AWS/EBS',
            MetricName='VolumeReadOps',
            Dimensions=[{'Name': 'VolumeId', 'Value': volume_id}],
            StartTime=start_time,
            EndTime=end_time,
            Period=3600,
            Statistics=['Average', 'Maximum']
        )
        
        # Get throughput utilization
        throughput_metrics = self.cloudwatch.get_metric_statistics(
            Namespace='AWS/EBS',
            MetricName='VolumeReadBytes',
            Dimensions=[{'Name': 'VolumeId', 'Value': volume_id}],
            StartTime=start_time,
            EndTime=end_time,
            Period=3600,
            Statistics=['Average', 'Maximum']
        )
        
        return {
            'volume_id': volume_id,
            'avg_iops': sum(d['Average'] for d in iops_metrics['Datapoints']) / len(iops_metrics['Datapoints']) if iops_metrics['Datapoints'] else 0,
            'max_iops': max(d['Maximum'] for d in iops_metrics['Datapoints']) if iops_metrics['Datapoints'] else 0,
            'avg_throughput_bytes': sum(d['Average'] for d in throughput_metrics['Datapoints']) / len(throughput_metrics['Datapoints']) if throughput_metrics['Datapoints'] else 0,
            'recommendation': self._get_volume_type_recommendation(volume_id, iops_metrics, throughput_metrics)
        }
    
    def _get_volume_type_recommendation(self, volume_id, iops_metrics, throughput_metrics):
        # Implementation for volume type recommendations based on usage patterns
        avg_iops = sum(d['Average'] for d in iops_metrics['Datapoints']) / len(iops_metrics['Datapoints']) if iops_metrics['Datapoints'] else 0
        
        if avg_iops < 100:
            return "Consider sc1 for cost savings if sequential workload"
        elif avg_iops < 3000:
            return "gp3 is likely optimal"
        else:
            return "Consider io2 for consistent high IOPS"
```

### Snapshot Lifecycle Management
```python
def setup_snapshot_lifecycle():
    dlm = boto3.client('dlm')
    
    response = dlm.create_lifecycle_policy(
        ExecutionRoleArn='arn:aws:iam::account:role/AWSDataLifecycleManagerDefaultRole',
        Description='Automated EBS snapshot management',
        State='ENABLED',
        PolicyDetails={
            'PolicyType': 'EBS_SNAPSHOT_MANAGEMENT',
            'ResourceTypes': ['VOLUME'],
            'TargetTags': [
                {'Key': 'Environment', 'Value': 'production'}
            ],
            'Schedules': [
                {
                    'Name': 'DailySnapshots',
                    'CreateRule': {
                        'Interval': 24,
                        'IntervalUnit': 'HOURS',
                        'Times': ['03:00']
                    },
                    'RetainRule': {
                        'Count': 7
                    },
                    'TagsToAdd': [
                        {'Key': 'CreatedBy', 'Value': 'DLM'}
                    ],
                    'CopyTags': True
                }
            ]
        }
    )
    return response['PolicyId']
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
  VolumeSize:
    Type: Number
    Default: 100
    MinValue: 20
    MaxValue: 16384

Resources:
  ApplicationVolume:
    Type: AWS::EC2::Volume
    Properties:
      Size: !Ref VolumeSize
      VolumeType: gp3
      AvailabilityZone: !GetAZs
        - !Select [0, !GetAZs '']
      Encrypted: true
      Tags:
        - Key: Environment
          Value: !Ref Environment
        - Key: Purpose
          Value: ApplicationData
        - Key: ManagedBy
          Value: CloudFormation

  VolumeAttachment:
    Type: AWS::EC2::VolumeAttachment
    Properties:
      VolumeId: !Ref ApplicationVolume
      InstanceId: !Ref EC2Instance
      Device: /dev/sdf

  SnapshotPolicy:
    Type: AWS::DLM::LifecyclePolicy
    Properties:
      Description: !Sub 'Snapshot policy for ${Environment} volumes'
      State: ENABLED
      ExecutionRoleArn: !Sub 'arn:aws:iam::${AWS::AccountId}:role/AWSDataLifecycleManagerDefaultRole'
      PolicyDetails:
        PolicyType: EBS_SNAPSHOT_MANAGEMENT
        ResourceTypes:
          - VOLUME
        TargetTags:
          - Key: Environment
            Value: !Ref Environment
        Schedules:
          - Name: DailySnapshots
            CreateRule:
              Interval: 24
              IntervalUnit: HOURS
              Times:
                - '03:00'
            RetainRule:
              Count: 7
```

### Terraform Configuration
```hcl
resource "aws_ebs_volume" "application_data" {
  availability_zone = data.aws_availability_zones.available.names[0]
  size              = var.volume_size
  type              = "gp3"
  encrypted         = true
  kms_key_id        = aws_kms_key.ebs_key.arn

  tags = {
    Name        = "${var.application_name}-data-${var.environment}"
    Environment = var.environment
    Application = var.application_name
    Backup      = "required"
  }
}

resource "aws_volume_attachment" "application_data" {
  device_name = "/dev/sdf"
  volume_id   = aws_ebs_volume.application_data.id
  instance_id = aws_instance.application.id
}

resource "aws_dlm_lifecycle_policy" "ebs_backup" {
  description        = "EBS snapshot lifecycle policy"
  execution_role_arn = aws_iam_role.dlm_lifecycle_role.arn
  state              = "ENABLED"

  policy_details {
    resource_types   = ["VOLUME"]
    target_tags = {
      Backup = "required"
    }

    schedule {
      name = "daily-snapshots"

      create_rule {
        interval      = 24
        interval_unit = "HOURS"
        times         = ["03:00"]
      }

      retain_rule {
        count = 7
      }

      tags_to_add = {
        SnapshotCreator = "DLM"
      }

      copy_tags = true
    }
  }
}
```

## Troubleshooting & Operations

### Common Issues and Solutions

#### Volume Performance Issues
```bash
# Check volume performance metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/EBS \
  --metric-name VolumeQueueLength \
  --dimensions Name=VolumeId,Value=vol-123456 \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Average

# Monitor disk I/O patterns
sudo iotop -o
sudo iostat -x 1 5
```

#### Attachment Issues
```python
def troubleshoot_volume_attachment(volume_id, instance_id):
    ec2 = boto3.client('ec2')
    
    # Check volume state
    volume = ec2.describe_volumes(VolumeIds=[volume_id])
    volume_state = volume['Volumes'][0]['State']
    
    # Check instance state
    instance = ec2.describe_instances(InstanceIds=[instance_id])
    instance_state = instance['Reservations'][0]['Instances'][0]['State']['Name']
    
    # Check if volume and instance are in same AZ
    volume_az = volume['Volumes'][0]['AvailabilityZone']
    instance_az = instance['Reservations'][0]['Instances'][0]['Placement']['AvailabilityZone']
    
    issues = []
    if volume_state != 'available':
        issues.append(f"Volume state is {volume_state}, expected 'available'")
    if instance_state != 'running':
        issues.append(f"Instance state is {instance_state}, expected 'running'")
    if volume_az != instance_az:
        issues.append(f"Volume AZ ({volume_az}) differs from instance AZ ({instance_az})")
    
    return issues
```

#### Snapshot Failures
```python
def verify_snapshot_status(snapshot_id):
    ec2 = boto3.client('ec2')
    
    try:
        snapshot = ec2.describe_snapshots(SnapshotIds=[snapshot_id])
        status = snapshot['Snapshots'][0]['State']
        progress = snapshot['Snapshots'][0].get('Progress', 'N/A')
        
        return {
            'status': status,
            'progress': progress,
            'encrypted': snapshot['Snapshots'][0].get('Encrypted', False),
            'volume_size': snapshot['Snapshots'][0]['VolumeSize']
        }
    except Exception as e:
        return {'error': str(e)}
```

## Best Practices

### Performance Optimization
- Choose appropriate volume type based on workload patterns
- Use gp3 for most general-purpose workloads
- Reserve io2 for applications requiring consistent high IOPS
- Monitor queue depth to identify I/O bottlenecks
- Use EBS-optimized instances for better throughput

### Backup and Recovery
- Implement automated snapshot schedules using DLM
- Test snapshot restoration procedures regularly
- Use cross-region snapshot copying for disaster recovery
- Tag snapshots consistently for lifecycle management

### Security
- Enable encryption for all volumes containing sensitive data
- Use customer-managed KMS keys for enhanced control
- Implement least-privilege IAM policies
- Regularly audit volume access patterns

## Additional Resources

### AWS Documentation
- [Amazon EBS User Guide](https://docs.aws.amazon.com/ebs/latest/userguide/)
- [EBS Performance Guidelines](https://docs.aws.amazon.com/ebs/latest/userguide/ebs-performance.html)
- [EBS Encryption](https://docs.aws.amazon.com/ebs/latest/userguide/ebs-encryption.html)

### Tools & Utilities
- **AWS CLI** - Command-line interface for EBS operations
- **EBS Direct APIs** - Direct access to EBS snapshots
- **CloudWatch** - Monitoring and alerting for EBS metrics

### Best Practices Guides
- [EBS Performance Best Practices](https://docs.aws.amazon.com/ebs/latest/userguide/ebs-performance.html)
- [EBS Cost Optimization](https://aws.amazon.com/ebs/pricing/)
- [Backup and Recovery Strategies](https://docs.aws.amazon.com/ebs/latest/userguide/ebs-creating-snapshot.html)