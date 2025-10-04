# Thanos Object Storage

Complete guide to object storage backends, configuration management, data lifecycle policies, and cost optimization strategies for Thanos long-term metric retention in production environments.

**Storage Backends:** AWS S3, Google Cloud Storage, Azure Blob Storage, MinIO, Swift, Oracle Cloud Storage, multi-cloud strategies, cost optimization, lifecycle management

## Object Storage Architecture

### Storage Backend Overview

```yaml
thanos_storage_architecture:
  storage_integration:
    description: "Thanos uses object storage for unlimited retention"
    benefits:
      cost_effectiveness: "Pay only for storage used, scales to petabytes"
      durability: "11 nines durability with cloud providers"
      scalability: "Automatic scaling without capacity planning"
      multi_region: "Cross-region replication for disaster recovery"

  data_organization:
    block_structure:
      description: "Prometheus TSDB blocks uploaded to object storage"
      block_types:
        - "Raw 2-hour blocks from Prometheus"
        - "Compacted blocks (merged from multiple 2h blocks)"
        - "Downsampled 5m resolution blocks"
        - "Downsampled 1h resolution blocks"

    metadata_management:
      meta_json: "Block metadata including min/max time, labels, stats"
      index_cache: "Store Gateway caches block indices for fast queries"
      chunk_cache: "Store Gateway caches chunks for query performance"

  storage_operations:
    upload: "Thanos Sidecar uploads completed Prometheus blocks"
    query: "Store Gateway downloads and serves historical data"
    compaction: "Compactor merges and downsamples blocks"
    cleanup: "Compactor removes blocks exceeding retention"
```

## AWS S3 Configuration

### Production S3 Setup

```yaml
# Complete S3 Configuration
type: S3
config:
  # Bucket configuration
  bucket: "thanos-metrics-production"
  endpoint: "s3.us-east-1.amazonaws.com"
  region: "us-east-1"

  # Authentication
  access_key: "${AWS_ACCESS_KEY_ID}"
  secret_key: "${AWS_SECRET_ACCESS_KEY}"

  # Alternative: Use IAM roles (recommended for EKS)
  # Leave access_key and secret_key empty when using IAM roles

  # Security settings
  insecure: false
  signature_version2: false
  encrypt_sse: true  # Server-side encryption
  sse_encryption: "AES256"  # or "aws:kms" for KMS
  sse_kms_key_id: ""  # KMS key ID if using KMS encryption
  sse_kms_encryption_context: {}

  # Storage class optimization
  storage_class: "STANDARD"  # STANDARD, STANDARD_IA, INTELLIGENT_TIERING

  # Metadata tagging
  put_user_metadata:
    Environment: "production"
    Project: "monitoring"
    ManagedBy: "thanos"
    CostCenter: "infrastructure"

  # HTTP configuration
  http_config:
    idle_conn_timeout: 90s
    response_header_timeout: 2m
    insecure_skip_verify: false
    tls_handshake_timeout: 10s
    expect_continue_timeout: 1s
    max_idle_conns: 100
    max_idle_conns_per_host: 100
    max_conns_per_host: 0

  # Performance tuning
  trace:
    enable: false
  part_size: 134217728  # 128MB multipart upload size

  # Listing optimization
  list_objects_version: "v2"  # Use S3 ListObjectsV2 API

  # Prefix for organizing data
  prefix: ""  # Optional prefix for all objects

  # Bucket encryption settings
  bucket_lookup_type: "auto"  # auto, virtual-hosted, path
```

### S3 Bucket Creation Script

```bash
#!/bin/bash
# Create and configure S3 bucket for Thanos

set -e

BUCKET_NAME="thanos-metrics-production"
REGION="us-east-1"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# Create bucket
aws s3api create-bucket \
  --bucket "$BUCKET_NAME" \
  --region "$REGION" \
  --create-bucket-configuration LocationConstraint="$REGION"

# Enable versioning for disaster recovery
aws s3api put-bucket-versioning \
  --bucket "$BUCKET_NAME" \
  --versioning-configuration Status=Enabled

# Enable server-side encryption
aws s3api put-bucket-encryption \
  --bucket "$BUCKET_NAME" \
  --server-side-encryption-configuration '{
    "Rules": [{
      "ApplyServerSideEncryptionByDefault": {
        "SSEAlgorithm": "AES256"
      },
      "BucketKeyEnabled": true
    }]
  }'

# Block public access
aws s3api put-public-access-block \
  --bucket "$BUCKET_NAME" \
  --public-access-block-configuration \
    "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"

# Enable lifecycle policy
aws s3api put-bucket-lifecycle-configuration \
  --bucket "$BUCKET_NAME" \
  --lifecycle-configuration file://lifecycle-policy.json

# Add bucket tags
aws s3api put-bucket-tagging \
  --bucket "$BUCKET_NAME" \
  --tagging 'TagSet=[
    {Key=Environment,Value=production},
    {Key=Project,Value=monitoring},
    {Key=ManagedBy,Value=thanos}
  ]'

echo "Bucket $BUCKET_NAME created and configured successfully"
```

### S3 Lifecycle Policy for Cost Optimization

```json
{
  "Rules": [
    {
      "Id": "ThanosRawDataTransition",
      "Status": "Enabled",
      "Filter": {
        "Prefix": ""
      },
      "Transitions": [
        {
          "Days": 30,
          "StorageClass": "STANDARD_IA"
        },
        {
          "Days": 90,
          "StorageClass": "INTELLIGENT_TIERING"
        },
        {
          "Days": 365,
          "StorageClass": "GLACIER_IR"
        },
        {
          "Days": 730,
          "StorageClass": "DEEP_ARCHIVE"
        }
      ],
      "NoncurrentVersionTransitions": [
        {
          "NoncurrentDays": 7,
          "StorageClass": "GLACIER"
        }
      ],
      "NoncurrentVersionExpiration": {
        "NoncurrentDays": 30
      }
    },
    {
      "Id": "ThanosIncompleteMultipartUploadCleanup",
      "Status": "Enabled",
      "Filter": {},
      "AbortIncompleteMultipartUpload": {
        "DaysAfterInitiation": 7
      }
    }
  ]
}
```

### IAM Policy for Thanos

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ThanosObjectStorageAccess",
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:DeleteObject",
        "s3:ListBucket",
        "s3:GetBucketLocation",
        "s3:ListMultipartUploadParts",
        "s3:AbortMultipartUpload"
      ],
      "Resource": [
        "arn:aws:s3:::thanos-metrics-production",
        "arn:aws:s3:::thanos-metrics-production/*"
      ]
    },
    {
      "Sid": "ThanosKMSAccess",
      "Effect": "Allow",
      "Action": [
        "kms:Decrypt",
        "kms:Encrypt",
        "kms:GenerateDataKey"
      ],
      "Resource": "arn:aws:kms:us-east-1:ACCOUNT_ID:key/KEY_ID"
    }
  ]
}
```

## Google Cloud Storage Configuration

### Production GCS Setup

```yaml
type: GCS
config:
  # Bucket configuration
  bucket: "thanos-metrics-production"

  # Service account authentication
  service_account: |
    {
      "type": "service_account",
      "project_id": "your-project-id",
      "private_key_id": "key-id",
      "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n",
      "client_email": "thanos@your-project.iam.gserviceaccount.com",
      "client_id": "123456789",
      "auth_uri": "https://accounts.google.com/o/oauth2/auth",
      "token_uri": "https://oauth2.googleapis.com/token",
      "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
      "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/thanos%40your-project.iam.gserviceaccount.com"
    }
```

### GCS Bucket Creation with Terraform

```hcl
# Terraform configuration for GCS bucket
resource "google_storage_bucket" "thanos_metrics" {
  name     = "thanos-metrics-production"
  location = "US"
  project  = var.project_id

  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }

  lifecycle_rule {
    condition {
      age = 30
    }
    action {
      type          = "SetStorageClass"
      storage_class = "NEARLINE"
    }
  }

  lifecycle_rule {
    condition {
      age = 90
    }
    action {
      type          = "SetStorageClass"
      storage_class = "COLDLINE"
    }
  }

  lifecycle_rule {
    condition {
      age = 365
    }
    action {
      type          = "SetStorageClass"
      storage_class = "ARCHIVE"
    }
  }

  encryption {
    default_kms_key_name = google_kms_crypto_key.thanos_key.id
  }

  labels = {
    environment = "production"
    project     = "monitoring"
    managed_by  = "terraform"
  }
}

resource "google_storage_bucket_iam_member" "thanos_access" {
  bucket = google_storage_bucket.thanos_metrics.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.thanos.email}"
}

resource "google_service_account" "thanos" {
  account_id   = "thanos-storage"
  display_name = "Thanos Object Storage Service Account"
  project      = var.project_id
}
```

## Azure Blob Storage Configuration

### Production Azure Setup

```yaml
type: AZURE
config:
  # Storage account configuration
  storage_account: "thanosmetricsprod"
  storage_account_key: "${AZURE_STORAGE_KEY}"

  # Alternative: Use managed identity (recommended for AKS)
  # msi_resource: ""  # Managed Service Identity resource

  # Container configuration
  container: "thanos-metrics"
  endpoint: ""  # Optional custom endpoint

  # Connection settings
  max_retries: 3

  # HTTP configuration
  http_config:
    idle_conn_timeout: 90s
    response_header_timeout: 2m
    insecure_skip_verify: false

  # Performance tuning
  reader_config:
    max_retry_requests: 3
  pipeline_config:
    max_tries: 3
    try_timeout: 10m
    retry_delay: 1s
    max_retry_delay: 5s
```

### Azure Storage Account Creation

```bash
#!/bin/bash
# Create Azure Storage Account for Thanos

RESOURCE_GROUP="monitoring-rg"
STORAGE_ACCOUNT="thanosmetricsprod"
LOCATION="eastus"
CONTAINER="thanos-metrics"

# Create resource group
az group create \
  --name "$RESOURCE_GROUP" \
  --location "$LOCATION"

# Create storage account
az storage account create \
  --name "$STORAGE_ACCOUNT" \
  --resource-group "$RESOURCE_GROUP" \
  --location "$LOCATION" \
  --sku Standard_LRS \
  --encryption-services blob \
  --https-only true \
  --min-tls-version TLS1_2 \
  --allow-blob-public-access false

# Create container
ACCOUNT_KEY=$(az storage account keys list \
  --resource-group "$RESOURCE_GROUP" \
  --account-name "$STORAGE_ACCOUNT" \
  --query '[0].value' -o tsv)

az storage container create \
  --name "$CONTAINER" \
  --account-name "$STORAGE_ACCOUNT" \
  --account-key "$ACCOUNT_KEY" \
  --public-access off

# Set lifecycle management policy
az storage account management-policy create \
  --account-name "$STORAGE_ACCOUNT" \
  --resource-group "$RESOURCE_GROUP" \
  --policy @lifecycle-policy.json
```

### Azure Lifecycle Policy

```json
{
  "rules": [
    {
      "enabled": true,
      "name": "MoveToArchive",
      "type": "Lifecycle",
      "definition": {
        "actions": {
          "baseBlob": {
            "tierToCool": {
              "daysAfterModificationGreaterThan": 30
            },
            "tierToArchive": {
              "daysAfterModificationGreaterThan": 90
            },
            "delete": {
              "daysAfterModificationGreaterThan": 730
            }
          }
        },
        "filters": {
          "blobTypes": ["blockBlob"],
          "prefixMatch": [""]
        }
      }
    }
  ]
}
```

## MinIO Configuration (On-Premise)

### MinIO Development/Testing Setup

```yaml
type: S3
config:
  bucket: "thanos-bucket"
  endpoint: "minio.monitoring.svc.cluster.local:9000"
  access_key: "minioadmin"
  secret_key: "minioadmin"
  insecure: true
  signature_version2: false
  http_config:
    idle_conn_timeout: 90s
    response_header_timeout: 2m
```

### MinIO Production Deployment

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: minio-pvc
  namespace: monitoring
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 500Gi
  storageClassName: fast-ssd

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: minio
  namespace: monitoring
spec:
  replicas: 1
  selector:
    matchLabels:
      app: minio
  template:
    metadata:
      labels:
        app: minio
    spec:
      containers:
      - name: minio
        image: minio/minio:RELEASE.2023-10-25T06-33-25Z
        args:
        - server
        - /data
        - --console-address
        - ":9001"
        env:
        - name: MINIO_ROOT_USER
          valueFrom:
            secretKeyRef:
              name: minio-credentials
              key: root-user
        - name: MINIO_ROOT_PASSWORD
          valueFrom:
            secretKeyRef:
              name: minio-credentials
              key: root-password
        ports:
        - containerPort: 9000
          name: api
        - containerPort: 9001
          name: console
        volumeMounts:
        - name: data
          mountPath: /data
        resources:
          requests:
            memory: 2Gi
            cpu: 1000m
          limits:
            memory: 4Gi
            cpu: 2000m
        livenessProbe:
          httpGet:
            path: /minio/health/live
            port: 9000
          initialDelaySeconds: 30
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /minio/health/ready
            port: 9000
          initialDelaySeconds: 10
          periodSeconds: 5
      volumes:
      - name: data
        persistentVolumeClaim:
          claimName: minio-pvc

---
apiVersion: v1
kind: Service
metadata:
  name: minio
  namespace: monitoring
spec:
  ports:
  - port: 9000
    targetPort: 9000
    name: api
  - port: 9001
    targetPort: 9001
    name: console
  selector:
    app: minio
  type: ClusterIP
```

## Kubernetes Secret Management

### Creating Object Storage Secrets

```bash
#!/bin/bash
# Create Kubernetes secret for Thanos object storage

NAMESPACE="monitoring"

# AWS S3 Secret
kubectl create secret generic thanos-objstore-config \
  --from-file=objstore.yml=<(cat <<EOF
type: S3
config:
  bucket: "thanos-metrics-production"
  endpoint: "s3.us-east-1.amazonaws.com"
  region: "us-east-1"
  access_key: "${AWS_ACCESS_KEY_ID}"
  secret_key: "${AWS_SECRET_ACCESS_KEY}"
  insecure: false
  signature_version2: false
  encrypt_sse: true
EOF
) \
  --namespace="$NAMESPACE" \
  --dry-run=client -o yaml | kubectl apply -f -

# Using IAM roles (EKS with IRSA)
kubectl create secret generic thanos-objstore-config \
  --from-file=objstore.yml=<(cat <<EOF
type: S3
config:
  bucket: "thanos-metrics-production"
  endpoint: "s3.us-east-1.amazonaws.com"
  region: "us-east-1"
  # No access_key/secret_key when using IAM roles
EOF
) \
  --namespace="$NAMESPACE" \
  --dry-run=client -o yaml | kubectl apply -f -
```

### External Secrets Operator Integration

```yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: thanos-objstore-config
  namespace: monitoring
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: aws-secrets-manager
    kind: SecretStore
  target:
    name: thanos-objstore-config
    creationPolicy: Owner
    template:
      data:
        objstore.yml: |
          type: S3
          config:
            bucket: "thanos-metrics-production"
            endpoint: "s3.us-east-1.amazonaws.com"
            region: "us-east-1"
            access_key: "{{ .AWS_ACCESS_KEY_ID }}"
            secret_key: "{{ .AWS_SECRET_ACCESS_KEY }}"
  data:
  - secretKey: AWS_ACCESS_KEY_ID
    remoteRef:
      key: thanos/storage-credentials
      property: access_key_id
  - secretKey: AWS_SECRET_ACCESS_KEY
    remoteRef:
      key: thanos/storage-credentials
      property: secret_access_key
```

## Multi-Cloud and Disaster Recovery

### Multi-Region Replication

```yaml
# Primary region (us-east-1)
primary_storage:
  type: S3
  config:
    bucket: "thanos-metrics-us-east-1"
    region: "us-east-1"
    endpoint: "s3.us-east-1.amazonaws.com"

# DR region (us-west-2)
dr_storage:
  type: S3
  config:
    bucket: "thanos-metrics-us-west-2"
    region: "us-west-2"
    endpoint: "s3.us-west-2.amazonaws.com"
```

### Cross-Region Replication Setup

```bash
#!/bin/bash
# Setup S3 cross-region replication

PRIMARY_BUCKET="thanos-metrics-us-east-1"
DR_BUCKET="thanos-metrics-us-west-2"
REPLICATION_ROLE="arn:aws:iam::ACCOUNT_ID:role/s3-replication-role"

# Enable versioning on both buckets (required for replication)
aws s3api put-bucket-versioning \
  --bucket "$PRIMARY_BUCKET" \
  --versioning-configuration Status=Enabled

aws s3api put-bucket-versioning \
  --bucket "$DR_BUCKET" \
  --versioning-configuration Status=Enabled

# Create replication configuration
aws s3api put-bucket-replication \
  --bucket "$PRIMARY_BUCKET" \
  --replication-configuration file://replication-config.json
```

### Replication Configuration

```json
{
  "Role": "arn:aws:iam::ACCOUNT_ID:role/s3-replication-role",
  "Rules": [
    {
      "ID": "ThanosMetricsReplication",
      "Status": "Enabled",
      "Priority": 1,
      "Filter": {},
      "Destination": {
        "Bucket": "arn:aws:s3:::thanos-metrics-us-west-2",
        "StorageClass": "STANDARD_IA",
        "ReplicationTime": {
          "Status": "Enabled",
          "Time": {
            "Minutes": 15
          }
        },
        "Metrics": {
          "Status": "Enabled",
          "EventThreshold": {
            "Minutes": 15
          }
        }
      },
      "DeleteMarkerReplication": {
        "Status": "Enabled"
      }
    }
  ]
}
```

## Storage Monitoring and Troubleshooting

### Key Metrics

```promql
# Total objects in bucket
thanos_objstore_bucket_objects

# Storage operations rate
rate(thanos_objstore_bucket_operations_total[5m])

# Operation latency (p99)
histogram_quantile(0.99,
  rate(thanos_objstore_bucket_operation_duration_seconds_bucket[5m]))

# Failed operations
rate(thanos_objstore_bucket_operation_failures_total[5m])

# Bucket size (requires custom exporter or CloudWatch)
thanos_objstore_bucket_size_bytes
```

### Troubleshooting Commands

```bash
# List all blocks in bucket
thanos tools bucket ls \
  --objstore.config-file=/etc/thanos/objstore.yml

# Verify block integrity
thanos tools bucket verify \
  --objstore.config-file=/etc/thanos/objstore.yml \
  --objstore-backup-config-file=/etc/thanos/objstore-backup.yml

# Inspect block metadata
thanos tools bucket inspect \
  --objstore.config-file=/etc/thanos/objstore.yml

# Replicate blocks to another bucket
thanos tools bucket replicate \
  --objstore.config-file=/etc/thanos/objstore-source.yml \
  --objstore-to.config-file=/etc/thanos/objstore-dest.yml

# Mark blocks for deletion
thanos tools bucket mark \
  --objstore.config-file=/etc/thanos/objstore.yml \
  --id=01HXXX... \
  --marker=deletion

# Cleanup deleted blocks
thanos tools bucket cleanup \
  --objstore.config-file=/etc/thanos/objstore.yml
```

### Performance Optimization

```yaml
# Optimize Store Gateway caching
store_gateway_optimization:
  index_cache:
    type: "memcached"
    config:
      addresses: ["memcached:11211"]
      max_idle_connections: 100
      max_async_concurrency: 50
      max_get_multi_concurrency: 100
      max_item_size: 5MiB
      timeout: 500ms

  caching_bucket:
    type: "memcached"
    config:
      addresses: ["memcached:11211"]
      max_idle_connections: 100
      chunk_subrange_size: 16000
      chunk_object_attrs_ttl: 24h
      chunk_subrange_ttl: 24h
```

This comprehensive guide provides production-ready object storage configurations for Thanos across all major cloud providers and on-premise solutions.
