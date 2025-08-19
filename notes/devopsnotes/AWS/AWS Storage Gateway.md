Bridge between on-prem and cloud data

**Types**: S3, FSx, volume, tape GW

## File Gateway (S3)
- **Purpose**: NFS/SMB file shares backed by S3
- **Use Case**: File archival, content distribution, backup to cloud
- **Protocols**: NFS v3/v4.1, SMB v2/v3
- **Local Cache**: Frequently accessed data cached locally on gateway
- **Benefits**: Seamless integration with existing file-based applications
- **Pricing**: Pay for S3 storage + data transfer + gateway usage

### Practical Setup Example
```bash
# 1. Deploy gateway VM/hardware appliance
# 2. Configure local cache storage (SSD recommended)
# 3. Create file share
aws storagegateway create-nfs-file-share \
    --client-token $(date +%s) \
    --gateway-arn arn:aws:storagegateway:us-east-1:123456789012:gateway/sgw-12345678 \
    --location-arn arn:aws:s3:::my-file-gateway-bucket \
    --role-arn arn:aws:iam::123456789012:role/StorageGatewayRole \
    --default-storage-class S3_STANDARD_IA

# 4. Mount on clients
sudo mount -t nfs -o nfsvers=4.1 \
    192.168.1.100:/my-file-gateway-bucket /mnt/s3-files
```

### Real-World Use Cases
- **Media Production**: Store video assets in S3, access via NFS for editing
- **Backup Solutions**: Legacy backup software writing to "local" storage (actually S3)
- **Content Distribution**: Share files across multiple locations via S3 backend
- **Log Archival**: Application logs written locally, automatically archived to S3

## Volume Gateway
- **Purpose**: iSCSI block storage backed by S3 and EBS snapshots
- **Modes**: Stored Volumes (primary on-prem) vs Cached Volumes (primary in S3)
- **Protocols**: iSCSI
- **Integration**: Works with existing backup software and disk-based applications

### Stored Volumes
```bash
# Create stored volume (1GB - 16TB)
aws storagegateway create-stored-iscsi-volume \
    --gateway-arn arn:aws:storagegateway:us-east-1:123456789012:gateway/sgw-12345678 \
    --disk-id /dev/xvdb \
    --snapshot-id snap-1234567890abcdef0 \
    --preserve-existing-data \
    --volume-size-in-bytes 107374182400 \
    --target-name my-stored-volume

# Connect from iSCSI initiator
sudo iscsiadm -m discovery -t st -p 192.168.1.100:3260
sudo iscsiadm -m node --login
```

### Cached Volumes
```bash
# Create cached volume (1GB - 32TB)
aws storagegateway create-cached-iscsi-volume \
    --gateway-arn arn:aws:storagegateway:us-east-1:123456789012:gateway/sgw-12345678 \
    --volume-size-in-bytes 107374182400 \
    --snapshot-id snap-1234567890abcdef0 \
    --target-name my-cached-volume \
    --source-volume-arn arn:aws:storagegateway:us-east-1:123456789012:gateway/sgw-12345678/volume/vol-12345678
```

### Practical Applications
- **Database Backups**: Oracle/SQL Server backup to iSCSI volumes
- **VM Storage**: VMware/Hyper-V VM storage with cloud backup
- **Enterprise Applications**: SAP, SharePoint requiring block storage
- **Disaster Recovery**: Quick restore from EBS snapshots

## FSx File Gateway
- **Purpose**: Optimized access to Amazon FSx file systems
- **File Systems**: FSx for Windows File Server, FSx for Lustre
- **Protocols**: SMB for Windows File Server, NFS for Lustre
- **Benefits**: Lower latency, local caching, bandwidth optimization

### Windows File Server Example
```powershell
# Create FSx file share
aws storagegateway create-smb-file-share `
    --gateway-arn arn:aws:storagegateway:us-east-1:123456789012:gateway/sgw-12345678 `
    --location-arn arn:aws:fsx:us-east-1:123456789012:file-system/fs-12345678 `
    --role-arn arn:aws:iam::123456789012:role/StorageGatewayRole `
    --authentication ActiveDirectory `
    --case-sensitivity CaseSensitive

# Mount on Windows client
net use Z: \\192.168.1.100\my-fsx-share /persistent:yes
```

### Lustre High-Performance Computing
```bash
# Mount FSx Lustre via gateway
sudo mount -t nfs -o nfsvers=4.1,flock \
    192.168.1.100:/lustre-share /mnt/hpc-data

# Typical HPC workflow
cd /mnt/hpc-data
# Process large datasets with optimized S3 integration
```

## Tape Gateway (Virtual Tape Library)
- **Purpose**: Replace physical tape infrastructure with cloud storage
- **Protocols**: iSCSI-based VTL (Virtual Tape Library)
- **Storage Classes**: S3, S3 Glacier, S3 Glacier Deep Archive
- **Tape Sizes**: 100GB to 5TB virtual tapes
- **Capacity**: Up to 1PB per gateway

### Enterprise Backup Integration
```bash
# Create virtual tape
aws storagegateway create-tapes \
    --gateway-arn arn:aws:storagegateway:us-east-1:123456789012:gateway/sgw-12345678 \
    --tape-size-in-bytes 107374182400 \
    --client-token $(date +%s) \
    --num-tapes-to-create 10 \
    --tape-barcode-prefix COMP

# Configure backup software (e.g., Veeam, NetBackup, TSM)
# Point backup jobs to VTL at: 192.168.1.100:3260
```

### Backup Software Configuration Examples

#### Veeam Integration
```powershell
# Add tape library in Veeam console
Add-VBRTapeLibrary -Name "AWS VTL" -Address "192.168.1.100"

# Create tape jobs targeting virtual tapes
New-VBRTapeJob -Name "Monthly Archive" -Library "AWS VTL" -MediaPool "Monthly"
```

#### IBM Spectrum Protect (TSM)
```bash
# Define tape library
define library AWSVTL libtype=scsi device=/dev/sg0 
shared=yes autolabel=yes

# Define drive
define drive AWSVTL drive1 device=/dev/st0 library=AWSVTL

# Create storage pool
define stgpool AWSTAPEPOOL AWSVTL description="AWS Virtual Tapes"
```

## Monitoring and Management

### CloudWatch Metrics
```bash
# Monitor gateway performance
aws cloudwatch get-metric-statistics \
    --namespace AWS/StorageGateway \
    --metric-name CachePercentageUsed \
    --dimensions Name=GatewayId,Value=sgw-12345678 \
    --start-time 2024-01-01T00:00:00Z \
    --end-time 2024-01-02T00:00:00Z \
    --period 3600 \
    --statistics Average

# Key metrics to monitor:
# - CachePercentageUsed
# - UploadBufferPercentageUsed  
# - WorkingStoragePercentageUsed
# - FilesFailingUpload
# - CloudWatchLogEvents
```

### Automated Maintenance
```bash
#!/bin/bash
# Gateway health check script

GATEWAY_ARN="arn:aws:storagegateway:us-east-1:123456789012:gateway/sgw-12345678"

# Check gateway status
STATUS=$(aws storagegateway describe-gateway-information \
    --gateway-arn $GATEWAY_ARN \
    --query 'GatewayState' --output text)

if [ "$STATUS" != "RUNNING" ]; then
    echo "Gateway not running: $STATUS"
    # Send alert via SNS
    aws sns publish \
        --topic-arn arn:aws:sns:us-east-1:123456789012:storage-gateway-alerts \
        --message "Storage Gateway $GATEWAY_ARN is $STATUS"
fi

# Check cache utilization
CACHE_USAGE=$(aws cloudwatch get-metric-statistics \
    --namespace AWS/StorageGateway \
    --metric-name CachePercentageUsed \
    --dimensions Name=GatewayId,Value=${GATEWAY_ARN##*/} \
    --start-time $(date -d '1 hour ago' -u +%Y-%m-%dT%H:%M:%SZ) \
    --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
    --period 3600 \
    --statistics Average \
    --query 'Datapoints[0].Average' --output text)

if (( $(echo "$CACHE_USAGE > 80" | bc -l) )); then
    echo "High cache usage: ${CACHE_USAGE}%"
    # Consider adding more cache storage
fi
```

## Cost Optimization Strategies

### Data Lifecycle Management
```bash
# Set up S3 lifecycle policies for File Gateway
aws s3api put-bucket-lifecycle-configuration \
    --bucket my-file-gateway-bucket \
    --lifecycle-configuration file://lifecycle.json

# lifecycle.json
{
    "Rules": [
        {
            "ID": "TransitionToIA",
            "Status": "Enabled",
            "Filter": {"Prefix": "archive/"},
            "Transitions": [
                {
                    "Days": 30,
                    "StorageClass": "STANDARD_IA"
                },
                {
                    "Days": 90,
                    "StorageClass": "GLACIER"
                },
                {
                    "Days": 365,
                    "StorageClass": "DEEP_ARCHIVE"
                }
            ]
        }
    ]
}
```

### Right-Sizing Gateway Resources
```bash
# Analyze gateway performance for sizing
aws storagegateway describe-gateway-information \
    --gateway-arn arn:aws:storagegateway:us-east-1:123456789012:gateway/sgw-12345678

# Typical sizing recommendations:
# Small office (< 100GB): 4 vCPU, 16GB RAM, 150GB cache
# Medium business (< 1TB): 8 vCPU, 32GB RAM, 500GB cache  
# Enterprise (> 1TB): 16 vCPU, 64GB RAM, 2TB+ cache
```

## Security Best Practices

### Network Security
```bash
# Security group for gateway (port 80, 443, 53, 123, 2049, 3260)
aws ec2 create-security-group \
    --group-name storage-gateway-sg \
    --description "Storage Gateway security group"

# Allow required ports
aws ec2 authorize-security-group-ingress \
    --group-name storage-gateway-sg \
    --protocol tcp \
    --port 80 \
    --source-group sg-12345678  # Management subnet

aws ec2 authorize-security-group-ingress \
    --group-name storage-gateway-sg \
    --protocol tcp \
    --port 3260 \
    --source-group sg-87654321  # Client subnet
```

### Encryption Configuration
```bash
# Enable encryption for File Gateway shares
aws storagegateway create-nfs-file-share \
    --gateway-arn arn:aws:storagegateway:us-east-1:123456789012:gateway/sgw-12345678 \
    --location-arn arn:aws:s3:::my-encrypted-bucket \
    --role-arn arn:aws:iam::123456789012:role/StorageGatewayRole \
    --kms-encrypted \
    --kms-key arn:aws:kms:us-east-1:123456789012:key/12345678-1234-1234-1234-123456789012
```

## Troubleshooting Common Issues

### Performance Problems
```bash
# Check bandwidth utilization
aws storagegateway describe-bandwidth-rate-limit \
    --gateway-arn arn:aws:storagegateway:us-east-1:123456789012:gateway/sgw-12345678

# Update bandwidth limits
aws storagegateway update-bandwidth-rate-limit \
    --gateway-arn arn:aws:storagegateway:us-east-1:123456789012:gateway/sgw-12345678 \
    --average-upload-rate-limit-in-bits-per-sec 104857600  # 100 Mbps
    --average-download-rate-limit-in-bits-per-sec 104857600
```

### Storage Issues
```bash
# Add local cache storage
aws storagegateway add-cache \
    --gateway-arn arn:aws:storagegateway:us-east-1:123456789012:gateway/sgw-12345678 \
    --disk-ids /dev/xvdc

# Add upload buffer storage  
aws storagegateway add-upload-buffer \
    --gateway-arn arn:aws:storagegateway:us-east-1:123456789012:gateway/sgw-12345678 \
    --disk-ids /dev/xvdd
```

### Connection Problems
```bash
# Test gateway connectivity
aws storagegateway list-gateways
aws storagegateway describe-gateway-information \
    --gateway-arn arn:aws:storagegateway:us-east-1:123456789012:gateway/sgw-12345678

# Refresh cache
aws storagegateway refresh-cache \
    --file-share-arn arn:aws:storagegateway:us-east-1:123456789012:share/share-12345678
```

## Enterprise Deployment Patterns

### Multi-Site Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Site A        │    │   Site B        │    │   Site C        │
│ File Gateway    │    │ Volume Gateway  │    │ Tape Gateway    │
│                 │    │                 │    │                 │
│ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │Local Cache  │ │    │ │Local Storage│ │    │ │Backup Software│ │
│ │150GB SSD    │ │    │ │2TB RAID     │ │    │ │Integration  │ │
│ └─────────────┘ │    │ └─────────────┘ │    │ └─────────────┘ │
└─────────────────┘    └─────────────────┘    └─────────────────┘
          │                       │                       │
          └───────────────────────┼───────────────────────┘
                                  │
                        ┌─────────────────┐
                        │   AWS Cloud     │
                        │                 │
                        │ ┌─────────────┐ │
                        │ │S3 Buckets   │ │
                        │ │EBS Snapshots│ │
                        │ │Virtual Tapes│ │
                        │ └─────────────┘ │
                        └─────────────────┘
```

### Disaster Recovery Setup
```bash
# Primary site setup
PRIMARY_GATEWAY="arn:aws:storagegateway:us-east-1:123456789012:gateway/sgw-primary"

# DR site setup  
DR_GATEWAY="arn:aws:storagegateway:us-west-2:123456789012:gateway/sgw-dr"

# Cross-region replication for File Gateway
aws s3api put-bucket-replication \
    --bucket primary-site-bucket \
    --replication-configuration file://replication.json

# Volume Gateway DR with cross-region snapshots
aws storagegateway create-snapshot \
    --volume-arn arn:aws:storagegateway:us-east-1:123456789012:gateway/sgw-primary/volume/vol-12345678 \
    --snapshot-description "DR snapshot $(date)"
```

## Migration Strategies

### Legacy to Cloud Migration
```bash
# Phase 1: Install gateway alongside existing storage
# Phase 2: Sync existing data
rsync -av /legacy/file/server/ /mnt/storage-gateway/

# Phase 3: Cut over applications
# Update mount points from legacy NFS to gateway NFS

# Phase 4: Decommission legacy storage
# Verify all data migrated and applications working
```

### Cloud-to-Cloud Migration
```bash
# DataSync for large migrations
aws datasync create-task \
    --source-location-arn arn:aws:datasync:us-east-1:123456789012:location/loc-source \
    --destination-location-arn arn:aws:datasync:us-east-1:123456789012:location/loc-dest \
    --name "Legacy-to-StorageGateway"

# Start migration task
aws datasync start-task-execution \
    --task-arn arn:aws:datasync:us-east-1:123456789012:task/task-12345678
```