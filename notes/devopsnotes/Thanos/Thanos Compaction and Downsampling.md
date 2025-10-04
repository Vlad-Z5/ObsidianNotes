# Thanos Compaction and Downsampling

Complete guide to data compaction strategies, downsampling configuration, storage optimization techniques, and deduplication management for efficient long-term metric retention in Thanos.

**Key Concepts:** Block compaction, downsampling resolutions, deduplication strategies, retention policies, storage optimization, compaction performance, consistency delays, vertical and horizontal compaction

## Compaction Architecture

### Compaction Overview

```yaml
thanos_compaction_architecture:
  compaction_purpose:
    description: "Merge multiple small blocks into larger ones"
    benefits:
      - "Reduces object storage API calls"
      - "Improves query performance"
      - "Enables deduplication across Prometheus replicas"
      - "Handles downsampling for long-term storage"
      - "Manages data retention and deletion"

  compaction_types:
    vertical_compaction:
      description: "Merge time-overlapping blocks (same time range)"
      use_case: "Deduplicate metrics from Prometheus replicas"
      example: "replica-0 and replica-1 blocks for same time period"

    horizontal_compaction:
      description: "Merge sequential blocks (adjacent time ranges)"
      use_case: "Create larger blocks for better query efficiency"
      example: "Combine twelve 2h blocks into one 24h block"

  downsampling_tiers:
    raw_data:
      resolution: "Original scrape interval (e.g., 15s)"
      retention: "30 days (configurable)"
      use_case: "Recent detailed metrics"

    5_minute_downsampled:
      resolution: "5 minutes"
      retention: "90 days (configurable)"
      aggregations: ["min", "max", "sum", "count", "counter"]
      use_case: "Medium-term trend analysis"

    1_hour_downsampled:
      resolution: "1 hour"
      retention: "2 years (configurable)"
      aggregations: ["min", "max", "sum", "count", "counter"]
      use_case: "Long-term capacity planning"
```

## Compactor Deployment

### Production Compactor Configuration

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: thanos-compactor
  namespace: monitoring
  labels:
    app: thanos-compactor
spec:
  serviceName: thanos-compactor
  replicas: 1  # MUST be 1 - only one compactor per bucket
  selector:
    matchLabels:
      app: thanos-compactor
  template:
    metadata:
      labels:
        app: thanos-compactor
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "10902"
    spec:
      serviceAccountName: thanos-compactor
      securityContext:
        fsGroup: 65534
        runAsUser: 65534
        runAsNonRoot: true

      containers:
      - name: thanos-compactor
        image: thanosio/thanos:v0.32.5
        args:
        # Compaction mode
        - compact
        - --wait
        - --wait-interval=5m

        # Storage configuration
        - --objstore.config-file=/etc/thanos/objstore.yml
        - --data-dir=/var/thanos/compactor

        # Retention policies (CRITICAL CONFIGURATION)
        - --retention.resolution-raw=30d
        - --retention.resolution-5m=90d
        - --retention.resolution-1h=730d  # 2 years

        # Consistency and safety
        - --consistency-delay=30m
        - --delete-delay=48h

        # Compaction performance
        - --compact.concurrency=1
        - --downsample.concurrency=1
        - --block-sync-concurrency=20
        - --compact.cleanup-interval=5m

        # Deduplication configuration
        - --deduplication.replica-label=replica
        - --deduplication.replica-label=prometheus_replica
        - --deduplication.func=penalty

        # Block filtering
        - --selector.relabel-config-file=/etc/thanos/compactor-relabel.yml

        # Logging and monitoring
        - --log.level=info
        - --log.format=logfmt
        - --http-address=0.0.0.0:10902

        ports:
        - containerPort: 10902
          name: http

        volumeMounts:
        - name: data
          mountPath: /var/thanos/compactor
        - name: objstore-config
          mountPath: /etc/thanos
          readOnly: true

        resources:
          requests:
            memory: 4Gi
            cpu: 2000m
          limits:
            memory: 8Gi
            cpu: 4000m

        livenessProbe:
          httpGet:
            path: /-/healthy
            port: 10902
          initialDelaySeconds: 30
          periodSeconds: 30
          timeoutSeconds: 10
          failureThreshold: 3

        readinessProbe:
          httpGet:
            path: /-/ready
            port: 10902
          initialDelaySeconds: 10
          periodSeconds: 5
          timeoutSeconds: 10

      volumes:
      - name: objstore-config
        secret:
          secretName: thanos-objstore-config

  volumeClaimTemplates:
  - metadata:
      name: data
    spec:
      accessModes: ["ReadWriteOnce"]
      storageClassName: fast-ssd
      resources:
        requests:
          storage: 200Gi  # Should be 2-3x largest block size

---
apiVersion: v1
kind: Service
metadata:
  name: thanos-compactor
  namespace: monitoring
  labels:
    app: thanos-compactor
spec:
  ports:
  - port: 10902
    targetPort: 10902
    name: http
  selector:
    app: thanos-compactor
  clusterIP: None  # Headless service

---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: thanos-compactor
  namespace: monitoring
  annotations:
    eks.amazonaws.com/role-arn: arn:aws:iam::ACCOUNT_ID:role/thanos-compactor-role

---
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: thanos-compactor-pdb
  namespace: monitoring
spec:
  minAvailable: 1
  selector:
    matchLabels:
      app: thanos-compactor
```

### Compactor Relabeling Configuration

```yaml
# /etc/thanos/compactor-relabel.yml
# Filter which blocks to compact based on labels
- action: keep
  source_labels: [cluster]
  regex: production

- action: drop
  source_labels: [__block_id]
  regex: "01HXXX.*"  # Exclude specific blocks if needed
```

## Downsampling Deep Dive

### How Downsampling Works

```yaml
downsampling_process:
  raw_to_5m:
    description: "Aggregate 15s data into 5-minute resolution"
    process:
      - "Read raw 2-hour blocks"
      - "Group samples into 5-minute windows"
      - "Calculate aggregations (min, max, sum, count)"
      - "Write new 5m resolution block"
    aggregation_functions:
      min: "Minimum value in 5-minute window"
      max: "Maximum value in 5-minute window"
      sum: "Sum of all values (for counters)"
      count: "Number of samples in window"
      counter: "Special handling for Prometheus counters with resets"

  5m_to_1h:
    description: "Aggregate 5-minute data into 1-hour resolution"
    process:
      - "Read 5m downsampled blocks"
      - "Group samples into 1-hour windows"
      - "Calculate aggregations from 5m data"
      - "Write new 1h resolution block"

  query_behavior:
    automatic_selection:
      description: "Thanos Query automatically uses appropriate resolution"
      rules:
        - "Query range < 40h: Use raw data"
        - "Query range 40h-10d: Mix raw and 5m data"
        - "Query range > 10d: Use 5m and 1h data"

    manual_override:
      max_source_resolution: "0s"   # Force raw data
      max_source_resolution: "5m"   # Use 5m or better
      max_source_resolution: "1h"   # Use 1h or better
```

### Downsampling Example

```promql
# Original raw data (15s scrape interval)
# 1 hour = 240 data points
http_requests_total{job="api"} [1h]
# Points: t0=100, t15=102, t30=105, ... t3600=350

# After 5m downsampling
# 1 hour = 12 data points (5m resolution)
http_requests_total:5m{job="api"} [1h]
# Points:
#   t0:5m   -> min=100, max=120, sum=1320, count=20
#   t5m:10m -> min=120, max=140, sum=1560, count=20
#   ... (12 windows total)

# After 1h downsampling
# 1 hour = 1 data point
http_requests_total:1h{job="api"} [1h]
# Point: t0:1h -> min=100, max=350, sum=19200, count=240
```

## Deduplication Strategies

### Replica Label Deduplication

```yaml
deduplication_configuration:
  replica_labels:
    description: "Labels identifying duplicate data from HA replicas"
    common_labels:
      - "replica"
      - "prometheus_replica"
      - "prometheus"

  prometheus_setup:
    replica_0:
      external_labels:
        cluster: production
        region: us-east-1
        replica: "0"

    replica_1:
      external_labels:
        cluster: production
        region: us-east-1
        replica: "1"

  deduplication_process:
    before_compaction:
      metric_1:
        replica_0: {value: 100, labels: {cluster: production, replica: "0"}}
        replica_1: {value: 100, labels: {cluster: production, replica: "1"}}

    after_compaction:
      metric_1: {value: 100, labels: {cluster: production}}
      # replica label removed, single deduplicated series

  deduplication_functions:
    penalty:
      description: "Prefer samples from earlier replicas (default)"
      use_case: "Stable, predictable deduplication"

    latest:
      description: "Prefer most recent sample"
      use_case: "When clock skew is minimal"
```

### Compactor Arguments for Deduplication

```bash
# Multiple replica labels
--deduplication.replica-label=replica
--deduplication.replica-label=prometheus_replica
--deduplication.replica-label=prometheus

# Deduplication function
--deduplication.func=penalty  # default, recommended
--deduplication.func=latest   # alternative
```

## Retention Policies

### Comprehensive Retention Strategy

```yaml
retention_configurations:
  aggressive_cost_optimization:
    description: "Minimize storage costs, suitable for high-volume environments"
    raw_data: 7d
    5m_downsampled: 30d
    1h_downsampled: 365d
    estimated_compression: "95% reduction after 30 days"

  balanced_production:
    description: "Recommended for most production environments"
    raw_data: 30d
    5m_downsampled: 90d
    1h_downsampled: 730d  # 2 years
    estimated_compression: "90% reduction after 90 days"

  compliance_extended:
    description: "For regulatory compliance requiring long retention"
    raw_data: 90d
    5m_downsampled: 365d
    1h_downsampled: 2555d  # 7 years
    estimated_compression: "85% reduction after 365 days"

  development_testing:
    description: "Short retention for dev/test environments"
    raw_data: 7d
    5m_downsampled: 14d
    1h_downsampled: 30d
```

### Dynamic Retention with Block Metadata

```yaml
# Advanced: Selectively retain blocks based on labels
retention_rules:
  - source_labels: [environment]
    regex: production
    retention_override:
      raw: 90d
      5m: 180d
      1h: 1095d  # 3 years

  - source_labels: [team]
    regex: critical-services
    retention_override:
      raw: 60d
      5m: 120d
      1h: 730d

  - source_labels: [environment]
    regex: development
    retention_override:
      raw: 3d
      5m: 7d
      1h: 14d
```

## Compaction Performance Tuning

### Resource Sizing Guidelines

```yaml
compactor_sizing:
  small_deployment:
    description: "< 1000 series, < 100GB storage"
    cpu: "1 core"
    memory: "2Gi"
    disk: "50Gi"

  medium_deployment:
    description: "1000-10000 series, 100GB-1TB storage"
    cpu: "2 cores"
    memory: "4Gi"
    disk: "100Gi"

  large_deployment:
    description: "10000-100000 series, 1TB-10TB storage"
    cpu: "4 cores"
    memory: "8Gi"
    disk: "200Gi"

  very_large_deployment:
    description: "> 100000 series, > 10TB storage"
    cpu: "8 cores"
    memory: "16Gi"
    disk: "500Gi"
    considerations:
      - "Consider multiple compactors with different block filters"
      - "Increase --compact.concurrency carefully (still keep at 1 per bucket)"
      - "Monitor compaction duration and queue depths"
```

### Compaction Optimization Flags

```bash
# Consistency delay (wait for block uploads to stabilize)
--consistency-delay=30m    # Default, safe for most cases
--consistency-delay=1h     # For slow/unreliable uploads
--consistency-delay=15m    # For fast, reliable storage

# Delete delay (safety period before permanent deletion)
--delete-delay=48h         # Recommended minimum
--delete-delay=168h        # 7 days for extra safety

# Block sync concurrency
--block-sync-concurrency=20    # Default
--block-sync-concurrency=50    # For faster sync with high bandwidth

# Compact cleanup interval
--compact.cleanup-interval=5m   # How often to check for cleanup

# Downsampling concurrency
--downsample.concurrency=1      # Keep at 1 to avoid resource spikes
```

## Monitoring Compaction

### Essential Compactor Metrics

```promql
# Compaction lag (time since last successful run)
time() - thanos_compact_last_successful_run_unix_seconds

# Alert if compaction hasn't run in 6 hours
ALERT ThanosCompactorNotRun
  IF time() - thanos_compact_last_successful_run_unix_seconds > 21600
  FOR 5m
  LABELS {severity="warning"}
  ANNOTATIONS {
    summary="Thanos Compactor hasn't run recently",
    description="Compactor hasn't completed a run in {{ $value }}s"
  }

# Compaction halted (critical error)
thanos_compact_halted > 0

# Compaction iteration duration
thanos_compact_iterations_duration_seconds

# Pending compaction groups
thanos_compact_group_compactions_total

# Compaction failures
rate(thanos_compact_group_compactions_failures_total[5m])

# Downsampling progress
rate(thanos_compact_downsample_total[5m])
rate(thanos_compact_downsample_failures_total[5m])

# Blocks loaded
thanos_compact_blocks_cleaned_total
thanos_compact_block_cleanup_failures_total
```

### Compaction Dashboard Queries

```promql
# Compaction efficiency: blocks before/after
sum(thanos_compact_group_compactions_total) by (group)

# Storage savings from compaction
(
  sum(thanos_compact_group_compaction_runs_started_total)
  - sum(thanos_compact_group_compaction_runs_completed_total)
) * avg(thanos_objstore_bucket_operation_duration_seconds)

# Average compaction duration
avg_over_time(thanos_compact_iterations_duration_seconds[1h])

# Blocks per resolution
count by (resolution) (thanos_blocks_meta_synced)

# Compactor CPU and memory usage
rate(container_cpu_usage_seconds_total{pod=~"thanos-compactor.*"}[5m])
container_memory_working_set_bytes{pod=~"thanos-compactor.*"}
```

### Compactor Alerting Rules

```yaml
groups:
- name: thanos-compactor
  interval: 30s
  rules:
  - alert: ThanosCompactHalted
    expr: thanos_compact_halted > 0
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "Thanos compaction has been halted"
      description: "Thanos Compact {{$labels.instance}} has failed and is halted"
      runbook: "https://docs.company.com/runbooks/thanos-compact-halted"

  - alert: ThanosCompactHighCompactionFailures
    expr: |
      rate(thanos_compact_group_compactions_failures_total[5m])
      / rate(thanos_compact_group_compactions_total[5m]) > 0.05
    for: 15m
    labels:
      severity: warning
    annotations:
      summary: "High compaction failure rate"
      description: "{{ $value | humanizePercentage }} of compactions are failing"

  - alert: ThanosCompactBucketHighOperationFailures
    expr: |
      rate(thanos_objstore_bucket_operation_failures_total{component="compact"}[5m])
      / rate(thanos_objstore_bucket_operations_total{component="compact"}[5m]) > 0.01
    for: 15m
    labels:
      severity: warning
    annotations:
      summary: "High object storage operation failure rate"

  - alert: ThanosCompactHasNotRun
    expr: time() - thanos_compact_last_successful_run_unix_seconds > 86400
    labels:
      severity: warning
    annotations:
      summary: "Thanos compaction hasn't run in 24 hours"
      description: "Compactor last ran {{ $value | humanizeDuration }} ago"

  - alert: ThanosCompactMultipleRunning
    expr: sum by (job) (up{job=~".*thanos-compact.*"}) > 1
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "Multiple Thanos Compactor instances running"
      description: "{{ $value }} compactor instances detected - only 1 should run"

  - alert: ThanosCompactorHighMemoryUsage
    expr: |
      container_memory_working_set_bytes{pod=~"thanos-compactor.*"}
      / container_spec_memory_limit_bytes{pod=~"thanos-compactor.*"} > 0.9
    for: 15m
    labels:
      severity: warning
    annotations:
      summary: "Thanos Compactor memory usage is high"
```

## Troubleshooting Compaction Issues

### Common Problems and Solutions

```bash
# Problem: Compaction is halted
# Check halted reason
kubectl logs -n monitoring thanos-compactor | grep "critical error"

# Solution: Usually requires manual intervention
# 1. Check for corrupted blocks
thanos tools bucket verify --objstore.config-file=/etc/thanos/objstore.yml

# 2. Mark problematic blocks for deletion
thanos tools bucket mark --objstore.config-file=/etc/thanos/objstore.yml \
  --id=01HXXX... --marker=deletion

# 3. Restart compactor
kubectl rollout restart statefulset/thanos-compactor -n monitoring

# Problem: Slow compaction
# Check block sizes and counts
thanos tools bucket inspect --objstore.config-file=/etc/thanos/objstore.yml

# Solution: Increase resources or adjust concurrency
# Edit StatefulSet to increase CPU/memory
kubectl edit statefulset thanos-compactor -n monitoring

# Problem: Out of disk space
# Check current disk usage
kubectl exec -n monitoring thanos-compactor-0 -- df -h /var/thanos/compactor

# Solution: Increase PVC size or reduce retention
kubectl patch pvc data-thanos-compactor-0 -n monitoring \
  -p '{"spec":{"resources":{"requests":{"storage":"300Gi"}}}}'

# Problem: Deduplication not working
# Verify replica labels in Prometheus
kubectl exec -n monitoring prometheus-0 -- curl http://localhost:9090/api/v1/status/config | jq .external_labels

# Check compactor deduplication config
kubectl get statefulset thanos-compactor -n monitoring -o yaml | grep deduplication

# Problem: Blocks not being compacted
# Check for blocks in object storage
thanos tools bucket ls --objstore.config-file=/etc/thanos/objstore.yml | head -20

# Verify consistency delay isn't too aggressive
# Blocks must be older than consistency delay to be compacted
```

### Manual Compaction Operations

```bash
# Force immediate compaction run
kubectl exec -n monitoring thanos-compactor-0 -- kill -HUP 1

# Compact specific blocks only
thanos compact \
  --data-dir=/tmp/thanos-compact \
  --objstore.config-file=/etc/thanos/objstore.yml \
  --wait \
  --selector.relabel-config='
    - source_labels: [__block_id]
      regex: "(01HXXX|01HYYY)"
      action: keep
  '

# Clean up deletion marks
thanos tools bucket cleanup \
  --objstore.config-file=/etc/thanos/objstore.yml \
  --delete-delay=0s

# Rewrite block metadata (advanced)
thanos tools bucket rewrite \
  --objstore.config-file=/etc/thanos/objstore.yml \
  --id=01HXXX... \
  --rewrite.to-relabel-config=/tmp/relabel.yml
```

## Best Practices

### Compaction Strategy Recommendations

```yaml
best_practices:
  singleton_compactor:
    rule: "Run exactly one compactor per object storage bucket"
    reason: "Multiple compactors cause race conditions and data corruption"
    enforcement: "Use PodDisruptionBudget with minAvailable: 1"

  consistency_delay:
    rule: "Set appropriate consistency delay"
    recommendation: "30m for stable environments, 1h for flaky storage"
    reason: "Prevents compacting incomplete blocks"

  delete_delay:
    rule: "Keep delete delay at minimum 48h"
    recommendation: "168h (7 days) for critical environments"
    reason: "Allows recovery from accidental deletions"

  resource_allocation:
    disk: "Allocate 2-3x the size of your largest block"
    memory: "4-8Gi for typical deployments, scale with series count"
    cpu: "2-4 cores, compaction is CPU-intensive"

  monitoring:
    critical_alerts:
      - "Compaction halted"
      - "Multiple compactors running"
      - "Compaction hasn't run in 24h"
    warning_alerts:
      - "High compaction failure rate"
      - "High memory usage"
      - "Slow compaction duration"

  retention_planning:
    strategy: "Balance cost vs query performance"
    recommendation: "30d raw, 90d 5m, 2y 1h for production"
    review: "Quarterly review of retention based on usage patterns"
```

This comprehensive guide provides all necessary configurations and operational procedures for managing Thanos compaction and downsampling in production environments.
