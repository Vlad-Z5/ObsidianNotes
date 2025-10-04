# Thanos Operations and Maintenance

Complete operational guide covering deployment procedures, maintenance tasks, troubleshooting workflows, backup and disaster recovery, performance tuning, capacity planning, and monitoring best practices for production Thanos infrastructure.

**Key Concepts:** Deployment strategies, upgrade procedures, backup and restore, disaster recovery, performance optimization, capacity planning, troubleshooting workflows, health checks, monitoring dashboards, incident response

## Deployment Strategies

### Initial Deployment Workflow

```yaml
deployment_phases:
  phase_1_infrastructure:
    step_1: "Deploy object storage (S3, GCS, Azure Blob)"
    step_2: "Configure IAM roles and service accounts"
    step_3: "Create Kubernetes namespace and RBAC"
    step_4: "Deploy secrets (objstore config, credentials)"
    validation:
      - "Test object storage connectivity"
      - "Verify IAM permissions"
      - "Confirm namespace resources created"

  phase_2_core_components:
    step_1: "Deploy Prometheus with Thanos Sidecar"
    step_2: "Deploy Thanos Store Gateway"
    step_3: "Deploy Thanos Compactor"
    step_4: "Deploy Thanos Query"
    validation:
      - "Verify Sidecar uploads blocks to storage"
      - "Confirm Store Gateway reads from storage"
      - "Check Compactor compacts blocks"
      - "Test queries through Thanos Query"

  phase_3_optional_components:
    step_1: "Deploy Thanos Query Frontend (caching)"
    step_2: "Deploy Thanos Ruler (global alerting)"
    step_3: "Deploy Thanos Receive (remote write)"
    validation:
      - "Test query caching effectiveness"
      - "Verify rule evaluation"
      - "Confirm remote write ingestion"

  phase_4_integration:
    step_1: "Configure Grafana datasource"
    step_2: "Import monitoring dashboards"
    step_3: "Set up AlertManager integration"
    step_4: "Configure backup procedures"
    validation:
      - "Test Grafana queries"
      - "Verify dashboard functionality"
      - "Test alert delivery"
      - "Validate backup restoration"
```

### Deployment Checklist

```bash
#!/bin/bash
# Thanos Deployment Validation Script

set -e

NAMESPACE="monitoring"

echo "=== Thanos Deployment Validation ==="

# Check object storage connectivity
echo "✓ Checking object storage..."
kubectl exec -n $NAMESPACE deployment/thanos-store -- \
  thanos tools bucket ls --objstore.config-file=/etc/thanos/objstore.yml | head -5

# Check Sidecar connectivity
echo "✓ Checking Thanos Sidecar..."
kubectl get pods -n $NAMESPACE -l app=prometheus -o wide

# Check Store Gateway
echo "✓ Checking Store Gateway..."
kubectl get pods -n $NAMESPACE -l app=thanos-store -o wide
kubectl logs -n $NAMESPACE -l app=thanos-store --tail=20 | grep -i "store gateway is ready"

# Check Compactor
echo "✓ Checking Compactor..."
kubectl get pods -n $NAMESPACE -l app=thanos-compactor -o wide
kubectl exec -n $NAMESPACE deployment/thanos-compactor -- \
  wget -qO- http://localhost:10902/-/ready

# Check Query
echo "✓ Checking Thanos Query..."
kubectl get pods -n $NAMESPACE -l app=thanos-query -o wide
curl -s http://thanos-query.$NAMESPACE.svc.cluster.local:9090/-/healthy

# Check StoreAPI connections
echo "✓ Checking StoreAPI endpoints..."
kubectl exec -n $NAMESPACE deployment/thanos-query -- \
  wget -qO- http://localhost:9090/api/v1/stores | jq '.data'

# Test query
echo "✓ Testing query..."
kubectl exec -n $NAMESPACE deployment/thanos-query -- \
  wget -qO- 'http://localhost:9090/api/v1/query?query=up' | jq '.data.result | length'

echo ""
echo "=== Validation Complete ==="
```

## Upgrade Procedures

### Rolling Upgrade Strategy

```yaml
upgrade_order:
  # Upgrade order matters - follow this sequence
  step_1_compactor:
    component: "Thanos Compactor"
    reason: "Stateful, only one instance, upgrade first"
    procedure:
      - "Check no compaction is running"
      - "Scale down to 0"
      - "Upgrade StatefulSet image"
      - "Scale up to 1"
      - "Verify compaction resumes"

  step_2_store_gateway:
    component: "Thanos Store Gateway"
    reason: "Stateful with local cache"
    procedure:
      - "Rolling update one pod at a time"
      - "Wait for pod ready before next"
      - "Verify queries still work"

  step_3_ruler:
    component: "Thanos Ruler"
    reason: "Stateful with HA support"
    procedure:
      - "Rolling update"
      - "Monitor alert delivery during upgrade"

  step_4_query:
    component: "Thanos Query"
    reason: "Stateless, can upgrade quickly"
    procedure:
      - "Rolling update all pods"
      - "PodDisruptionBudget ensures availability"

  step_5_query_frontend:
    component: "Thanos Query Frontend"
    reason: "Stateless with cache"
    procedure:
      - "Rolling update"
      - "Cache will rebuild automatically"

  step_6_sidecar:
    component: "Thanos Sidecar"
    reason: "Upgrade with Prometheus"
    procedure:
      - "Upgrade Prometheus + Sidecar together"
      - "One replica at a time in HA setup"
```

### Upgrade Script

```bash
#!/bin/bash
# Thanos Component Upgrade Script

NAMESPACE="monitoring"
NEW_VERSION="v0.32.5"

upgrade_component() {
  local COMPONENT=$1
  local TYPE=$2  # deployment or statefulset

  echo "Upgrading $COMPONENT to $NEW_VERSION..."

  kubectl set image $TYPE/$COMPONENT -n $NAMESPACE \
    thanos-$COMPONENT=thanosio/thanos:$NEW_VERSION

  kubectl rollout status $TYPE/$COMPONENT -n $NAMESPACE --timeout=5m

  echo "✓ $COMPONENT upgraded successfully"
}

# Upgrade in correct order
echo "=== Starting Thanos Upgrade to $NEW_VERSION ==="

# 1. Compactor (scale down, upgrade, scale up)
echo "Step 1: Upgrading Compactor..."
kubectl scale statefulset/thanos-compactor -n $NAMESPACE --replicas=0
sleep 10
upgrade_component "compactor" "statefulset"
kubectl scale statefulset/thanos-compactor -n $NAMESPACE --replicas=1

# 2. Store Gateway
echo "Step 2: Upgrading Store Gateway..."
upgrade_component "store" "statefulset"

# 3. Ruler
echo "Step 3: Upgrading Ruler..."
upgrade_component "ruler" "statefulset"

# 4. Query
echo "Step 4: Upgrading Query..."
upgrade_component "query" "deployment"

# 5. Query Frontend
echo "Step 5: Upgrading Query Frontend..."
upgrade_component "query-frontend" "deployment"

echo ""
echo "=== Upgrade Complete ==="
echo "Verify all components:"
kubectl get pods -n $NAMESPACE -l 'app.kubernetes.io/name=thanos'
```

## Backup and Disaster Recovery

### Backup Strategy

```yaml
backup_components:
  object_storage_data:
    description: "Metric blocks stored in S3/GCS/Azure"
    backup_method: "Cloud provider replication"
    strategies:
      cross_region_replication:
        s3: "S3 Cross-Region Replication"
        gcs: "GCS Multi-Region or Dual-Region"
        azure: "Azure Geo-Redundant Storage (GRS)"
      versioning:
        enabled: true
        retention: "30 days of versions"
      lifecycle_policies:
        transition_to_archive: "After 90 days"

  configuration_backups:
    kubernetes_resources:
      - "ConfigMaps (rules, configs)"
      - "Secrets (objstore configs)"
      - "StatefulSets and Deployments"
    backup_method: "GitOps or etcd snapshots"
    frequency: "On every change (GitOps) or daily (etcd)"

  ruler_wal:
    description: "Write-Ahead Log for Ruler"
    location: "/var/thanos/ruler"
    backup: "PersistentVolume snapshots"
    frequency: "Daily"
```

### S3 Backup Configuration

```bash
#!/bin/bash
# S3 Cross-Region Replication Setup

PRIMARY_BUCKET="thanos-metrics-us-east-1"
DR_BUCKET="thanos-metrics-us-west-2"
REPLICATION_ROLE="arn:aws:iam::ACCOUNT_ID:role/s3-replication-role"

# Enable versioning (required for replication)
aws s3api put-bucket-versioning \
  --bucket $PRIMARY_BUCKET \
  --versioning-configuration Status=Enabled

aws s3api put-bucket-versioning \
  --bucket $DR_BUCKET \
  --versioning-configuration Status=Enabled

# Configure replication
cat > replication-config.json <<EOF
{
  "Role": "$REPLICATION_ROLE",
  "Rules": [
    {
      "ID": "ReplicateAll",
      "Status": "Enabled",
      "Priority": 1,
      "Filter": {},
      "Destination": {
        "Bucket": "arn:aws:s3:::$DR_BUCKET",
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
EOF

aws s3api put-bucket-replication \
  --bucket $PRIMARY_BUCKET \
  --replication-configuration file://replication-config.json

echo "✓ Cross-region replication configured"
```

### Disaster Recovery Procedures

```yaml
disaster_recovery_scenarios:
  scenario_1_complete_object_storage_loss:
    impact: "Loss of all historical metrics"
    recovery:
      step_1: "Restore from replicated bucket or backup"
      step_2: "Update objstore.yml to point to DR bucket"
      step_3: "Restart all Thanos components"
      step_4: "Verify Store Gateway reads from DR bucket"
      step_5: "Reconfigure replication to new primary"
    rto: "2 hours"
    rpo: "15 minutes (with S3 RTC)"

  scenario_2_kubernetes_cluster_loss:
    impact: "Loss of Thanos infrastructure"
    recovery:
      step_1: "Provision new Kubernetes cluster"
      step_2: "Restore configurations from GitOps repo"
      step_3: "Deploy Thanos components"
      step_4: "Verify connectivity to object storage"
      step_5: "Historical data intact, real-time resumes"
    rto: "4 hours"
    rpo: "0 (object storage unaffected)"

  scenario_3_compactor_corruption:
    impact: "Corrupted blocks in object storage"
    recovery:
      step_1: "Stop compactor immediately"
      step_2: "Identify corrupted blocks"
      step_3: "Mark for deletion or restore from backup"
      step_4: "Verify block integrity"
      step_5: "Restart compactor"
    command: |
      # Find and mark corrupted blocks
      thanos tools bucket verify --objstore.config-file=/etc/thanos/objstore.yml
      thanos tools bucket mark --id=<block-id> --marker=deletion

  scenario_4_prometheus_data_loss:
    impact: "Loss of recent metrics (not uploaded yet)"
    recovery:
      step_1: "Most recent data lost (last 2 hours)"
      step_2: "Prometheus restarts with empty TSDB"
      step_3: "Sidecar resumes uploading new blocks"
      step_4: "Historical data in object storage unaffected"
    rto: "Immediate"
    rpo: "2 hours (typical block duration)"
```

### Restore Procedures

```bash
#!/bin/bash
# Restore Thanos from DR Bucket

DR_BUCKET="thanos-metrics-us-west-2"
NAMESPACE="monitoring"

# Step 1: Update object storage configuration
kubectl create secret generic thanos-objstore-config \
  --from-file=objstore.yml=<(cat <<EOF
type: S3
config:
  bucket: "$DR_BUCKET"
  region: "us-west-2"
  endpoint: "s3.us-west-2.amazonaws.com"
EOF
) \
  --namespace=$NAMESPACE \
  --dry-run=client -o yaml | kubectl apply -f -

# Step 2: Restart all Thanos components
kubectl rollout restart statefulset/thanos-compactor -n $NAMESPACE
kubectl rollout restart statefulset/thanos-store -n $NAMESPACE
kubectl rollout restart statefulset/thanos-ruler -n $NAMESPACE
kubectl rollout restart deployment/thanos-query -n $NAMESPACE

# Step 3: Verify connectivity
echo "Waiting for components to be ready..."
kubectl wait --for=condition=ready pod -l app=thanos-store -n $NAMESPACE --timeout=5m

# Step 4: Test data access
kubectl exec -n $NAMESPACE deployment/thanos-query -- \
  wget -qO- 'http://localhost:9090/api/v1/query?query=up' | jq '.status'

echo "✓ Disaster recovery complete"
```

## Performance Tuning

### Component Resource Optimization

```yaml
resource_tuning:
  thanos_store:
    problem: "High memory usage, slow queries"
    solutions:
      increase_cache:
        index_cache: "2GB → 4GB"
        chunk_cache: "2GB → 4GB"
      adjust_concurrency:
        series_sample_limit: "120000 → 200000"
        series_max_concurrency: "20 → 40"
      use_memcached:
        index_cache: "Use distributed Memcached"
        caching_bucket: "Cache chunk data in Memcached"

  thanos_query:
    problem: "Query timeouts, high latency"
    solutions:
      increase_timeout:
        query_timeout: "2m → 5m"
      increase_concurrency:
        max_concurrent: "20 → 40"
        max_concurrent_select: "4 → 8"
      add_query_frontend:
        benefit: "Query splitting and caching"
        cache_backend: "Redis or Memcached"

  thanos_compactor:
    problem: "Slow compaction, OOM"
    solutions:
      increase_resources:
        memory: "4Gi → 8Gi"
        cpu: "2 cores → 4 cores"
        disk: "100Gi → 200Gi"
      tune_concurrency:
        compact_concurrency: "Keep at 1"
        block_sync_concurrency: "20 → 40"
```

### Memcached for Caching

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: memcached
  namespace: monitoring
spec:
  replicas: 3
  selector:
    matchLabels:
      app: memcached
  template:
    metadata:
      labels:
        app: memcached
    spec:
      containers:
      - name: memcached
        image: memcached:1.6-alpine
        args:
        - -m 2048        # 2GB memory
        - -I 5m          # Max item size 5MB
        - -c 1024        # Max connections
        - -v             # Verbose logging
        ports:
        - containerPort: 11211
          name: memcached
        resources:
          requests:
            memory: 2Gi
            cpu: 500m
          limits:
            memory: 2.5Gi
            cpu: 1000m

---
apiVersion: v1
kind: Service
metadata:
  name: memcached
  namespace: monitoring
spec:
  ports:
  - port: 11211
    targetPort: 11211
  selector:
    app: memcached
  clusterIP: None  # Headless for client-side load balancing
```

### Store Gateway with Memcached

```yaml
# Add to Store Gateway configuration
args:
- --index-cache.config-file=/etc/thanos/index-cache.yml
- --store.caching-bucket.config-file=/etc/thanos/caching-bucket.yml

# Index cache configuration
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: thanos-store-cache-config
data:
  index-cache.yml: |
    type: MEMCACHED
    config:
      addresses:
      - memcached-0.memcached.monitoring.svc.cluster.local:11211
      - memcached-1.memcached.monitoring.svc.cluster.local:11211
      - memcached-2.memcached.monitoring.svc.cluster.local:11211
      max_idle_connections: 100
      max_async_concurrency: 50
      timeout: 500ms
      max_get_multi_concurrency: 100
      max_item_size: 5MiB
      max_async_buffer_size: 25000

  caching-bucket.yml: |
    type: MEMCACHED
    config:
      addresses:
      - memcached-0.memcached.monitoring.svc.cluster.local:11211
      - memcached-1.memcached.monitoring.svc.cluster.local:11211
      - memcached-2.memcached.monitoring.svc.cluster.local:11211
      max_idle_connections: 100
      chunk_subrange_size: 16000
      chunk_object_attrs_ttl: 24h
      chunk_subrange_ttl: 24h
      max_item_size: 5MiB
```

## Troubleshooting Workflows

### Common Issues and Solutions

```yaml
issue_1_query_timeouts:
  symptoms:
    - "Queries timing out in Grafana"
    - "502 Bad Gateway errors"
  diagnosis:
    check_query_metrics: |
      histogram_quantile(0.99,
        rate(http_request_duration_seconds_bucket{handler="query"}[5m]))
    check_concurrent_queries: "thanos_query_concurrent_selects_in_flight"
  solutions:
    - "Increase --query.timeout flag"
    - "Add more Query replicas"
    - "Enable Query Frontend for caching"
    - "Optimize PromQL queries"

issue_2_store_gateway_oom:
  symptoms:
    - "Store Gateway pods OOMKilled"
    - "High memory usage"
  diagnosis:
    check_cache_usage: |
      thanos_store_index_cache_items_added_total
      thanos_store_index_cache_items_evicted_total
    check_series_limit: "thanos_store_bucket_series_queried_total"
  solutions:
    - "Increase memory limits"
    - "Reduce --index-cache-size and --chunk-pool-size"
    - "Use external Memcached for caching"
    - "Implement --store.grpc.series-sample-limit"

issue_3_compactor_halted:
  symptoms:
    - "Compaction stopped"
    - "Alert: ThanosCompactHalted firing"
  diagnosis:
    check_logs: "kubectl logs -n monitoring thanos-compactor"
    check_halted_metric: "thanos_compact_halted > 0"
  solutions:
    - "Check for corrupted blocks: thanos tools bucket verify"
    - "Mark bad blocks for deletion"
    - "Restart compactor after fixing issues"
    - "Review consistency-delay setting"

issue_4_high_object_storage_costs:
  symptoms:
    - "Unexpected S3/GCS bills"
    - "High operation counts"
  diagnosis:
    check_operations: |
      rate(thanos_objstore_bucket_operations_total[1d])
    check_storage_size: "AWS S3 console or CloudWatch metrics"
  solutions:
    - "Review retention policies (reduce if possible)"
    - "Enable lifecycle policies for tiered storage"
    - "Increase consistency-delay to reduce re-uploads"
    - "Implement caching to reduce GET operations"

issue_5_missing_metrics:
  symptoms:
    - "Gaps in metric data"
    - "Historical queries return no data"
  diagnosis:
    check_sidecar_uploads: |
      thanos_shipper_uploads_total
      thanos_shipper_upload_failures_total
    check_blocks: "thanos tools bucket ls"
  solutions:
    - "Verify Sidecar has object storage credentials"
    - "Check Prometheus external_labels are set"
    - "Confirm blocks are being uploaded"
    - "Verify Store Gateway can read blocks"
```

### Debug Commands

```bash
#!/bin/bash
# Thanos Troubleshooting Commands

NAMESPACE="monitoring"

# Check component health
echo "=== Component Health ==="
kubectl get pods -n $NAMESPACE -l 'app.kubernetes.io/name=thanos'
kubectl top pods -n $NAMESPACE -l 'app.kubernetes.io/name=thanos'

# Check StoreAPI endpoints
echo -e "\n=== StoreAPI Endpoints ==="
kubectl exec -n $NAMESPACE deployment/thanos-query -- \
  wget -qO- http://localhost:9090/api/v1/stores | jq '.data[] | {name, lastCheck, lastError}'

# Check object storage connectivity
echo -e "\n=== Object Storage Connectivity ==="
kubectl exec -n $NAMESPACE deployment/thanos-store -- \
  thanos tools bucket ls --objstore.config-file=/etc/thanos/objstore.yml | head -10

# Verify block compaction
echo -e "\n=== Recent Compactions ==="
kubectl logs -n $NAMESPACE -l app=thanos-compactor --tail=50 | grep -i "compact"

# Check query performance
echo -e "\n=== Query Performance ==="
kubectl exec -n $NAMESPACE deployment/thanos-query -- \
  wget -qO- http://localhost:9090/metrics | grep -E "thanos_query_concurrent|http_request_duration"

# Check for errors
echo -e "\n=== Recent Errors ==="
for pod in $(kubectl get pods -n $NAMESPACE -l 'app.kubernetes.io/name=thanos' -o name); do
  echo "=== $pod ==="
  kubectl logs -n $NAMESPACE $pod --tail=20 | grep -i error
done
```

## Capacity Planning

### Sizing Guidelines

```yaml
capacity_planning:
  metrics_volume_estimation:
    inputs:
      active_series: "Number of unique time series"
      scrape_interval: "15s typical"
      retention: "30d raw, 90d 5m, 2y 1h"

    storage_calculation:
      raw_data: "active_series * (86400/15) * 2 bytes * 30 days"
      5m_downsampled: "active_series * (86400/300) * 6 bytes * 90 days"
      1h_downsampled: "active_series * 24 * 6 bytes * 730 days"

    example:
      active_series: 100000
      raw_storage: "~3.5 TB"
      5m_storage: "~3.2 TB"
      1h_storage: "~10.5 TB"
      total: "~17.2 TB"

  component_scaling:
    thanos_query:
      scale_trigger: "Query latency P99 > 5s OR CPU > 70%"
      scale_method: "Horizontal (add replicas)"
      recommended_replicas: "3-10 based on query load"

    thanos_store:
      scale_trigger: "Memory usage > 80% OR query timeouts"
      scale_method: "Vertical (increase resources) or Horizontal (block sharding)"
      recommended_resources:
        memory: "4-8Gi per 100K series"
        cpu: "1-2 cores per replica"

    thanos_compactor:
      scale_trigger: "Compaction duration > 1 hour"
      scale_method: "Vertical only (single instance)"
      recommended_resources:
        memory: "4-8Gi"
        cpu: "2-4 cores"
        disk: "2-3x largest block size"
```

## Monitoring Best Practices

### Essential Dashboards

```yaml
dashboard_requirements:
  thanos_overview:
    panels:
      - "Component health (up/down status)"
      - "Query throughput and latency"
      - "Object storage operations"
      - "Store Gateway cache hit rate"
      - "Compaction progress"

  thanos_query:
    panels:
      - "Query rate by handler"
      - "Query latency P50/P95/P99"
      - "Concurrent queries"
      - "StoreAPI endpoint health"
      - "Error rate"

  thanos_store:
    panels:
      - "Blocks loaded"
      - "Cache hit ratio"
      - "Query duration"
      - "Memory usage"
      - "Series queried"

  thanos_compactor:
    panels:
      - "Compaction lag"
      - "Blocks compacted"
      - "Compaction duration"
      - "Object storage operations"
      - "Retention enforcement"
```

This comprehensive guide provides all operational procedures and troubleshooting workflows needed for managing Thanos in production environments.
