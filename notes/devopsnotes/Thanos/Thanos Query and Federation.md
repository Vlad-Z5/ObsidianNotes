# Thanos Query and Federation

Complete guide to global query setup, multi-cluster federation, query optimization, performance tuning, PromQL extensions, and distributed query execution for unified monitoring across multiple Prometheus instances.

**Key Concepts:** Global query view, StoreAPI protocol, deduplication at query time, query federation, partial response handling, query sharding, timeout management, caching strategies, query frontend optimization

## Query Architecture

### Thanos Query Overview

```yaml
thanos_query_architecture:
  query_layer_purpose:
    description: "Unified query interface across all Prometheus instances and storage"
    capabilities:
      - "Query data from multiple Prometheus instances simultaneously"
      - "Access historical data from object storage via Store Gateway"
      - "Deduplicate metrics from HA Prometheus replicas"
      - "Aggregate data across clusters and regions"
      - "Provide standard Prometheus API compatibility"

  storeapi_protocol:
    description: "gRPC protocol for querying Thanos components"
    store_types:
      sidecar: "Real-time data from Prometheus instances"
      store_gateway: "Historical data from object storage"
      ruler: "Recording and alerting rule results"
      receive: "Remote write ingested data"

  query_execution_flow:
    step_1: "Receive PromQL query from user/Grafana"
    step_2: "Fan-out query to all registered Store API endpoints"
    step_3: "Each store returns matching time series"
    step_4: "Thanos Query merges and deduplicates results"
    step_5: "Apply PromQL aggregations and functions"
    step_6: "Return unified result to client"

  deduplication:
    description: "Automatic deduplication of metrics from HA replicas"
    replica_labels: ["replica", "prometheus_replica"]
    algorithm: "Penalty-based selection (prefers earlier replica)"
    query_time: "Happens during query execution, not storage"
```

## Thanos Query Deployment

### Production Query Configuration

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: thanos-query
  namespace: monitoring
  labels:
    app: thanos-query
spec:
  replicas: 3  # Multiple replicas for HA and load distribution
  selector:
    matchLabels:
      app: thanos-query
  template:
    metadata:
      labels:
        app: thanos-query
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "10902"
    spec:
      serviceAccountName: thanos-query
      securityContext:
        fsGroup: 65534
        runAsUser: 65534
        runAsNonRoot: true

      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            podAffinityTerm:
              labelSelector:
                matchLabels:
                  app: thanos-query
              topologyKey: kubernetes.io/hostname

      containers:
      - name: thanos-query
        image: thanosio/thanos:v0.32.5
        args:
        # Basic configuration
        - query
        - --log.level=info
        - --log.format=logfmt
        - --grpc-address=0.0.0.0:10901
        - --http-address=0.0.0.0:9090

        # Deduplication configuration
        - --query.replica-label=replica
        - --query.replica-label=prometheus_replica
        - --query.replica-label=prometheus

        # Query behavior
        - --query.timeout=5m
        - --query.max-concurrent=20
        - --query.lookback-delta=5m
        - --query.max-concurrent-select=4

        # Partial response handling
        - --query.partial-response
        - --query.default-evaluation-interval=1m

        # Auto downsampling
        - --query.auto-downsampling

        # Store endpoints (static configuration)
        - --store=thanos-sidecar-0.thanos-sidecar.monitoring.svc.cluster.local:10901
        - --store=thanos-sidecar-1.thanos-sidecar.monitoring.svc.cluster.local:10901
        - --store=thanos-store.monitoring.svc.cluster.local:10901
        - --store=thanos-ruler.monitoring.svc.cluster.local:10901

        # DNS-based service discovery
        - --store=dnssrv+_grpc._tcp.thanos-sidecar.monitoring.svc.cluster.local
        - --store=dnssrv+_grpc._tcp.thanos-store.monitoring.svc.cluster.local

        # Store endpoint timeouts
        - --store.response-timeout=30s
        - --grpc-client-tls-secure
        - --grpc-client-server-name=thanos-query

        # Query metadata
        - --query.promql-engine=prometheus

        ports:
        - containerPort: 9090
          name: http
        - containerPort: 10901
          name: grpc

        livenessProbe:
          httpGet:
            path: /-/healthy
            port: 9090
          initialDelaySeconds: 30
          periodSeconds: 30
          timeoutSeconds: 10

        readinessProbe:
          httpGet:
            path: /-/ready
            port: 9090
          initialDelaySeconds: 10
          periodSeconds: 5
          timeoutSeconds: 10

        resources:
          requests:
            memory: 2Gi
            cpu: 1000m
          limits:
            memory: 4Gi
            cpu: 2000m

        volumeMounts:
        - name: query-config
          mountPath: /etc/thanos
          readOnly: true

      volumes:
      - name: query-config
        configMap:
          name: thanos-query-config

---
apiVersion: v1
kind: Service
metadata:
  name: thanos-query
  namespace: monitoring
  labels:
    app: thanos-query
spec:
  type: ClusterIP
  ports:
  - port: 9090
    targetPort: 9090
    name: http
  - port: 10901
    targetPort: 10901
    name: grpc
  selector:
    app: thanos-query

---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: thanos-query-hpa
  namespace: monitoring
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: thanos-query
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  - type: Pods
    pods:
      metric:
        name: thanos_query_concurrent_selects_in_flight
      target:
        type: AverageValue
        averageValue: "15"

---
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: thanos-query-pdb
  namespace: monitoring
spec:
  minAvailable: 2
  selector:
    matchLabels:
      app: thanos-query
```

## Query Frontend for Caching and Splitting

### Query Frontend Configuration

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: thanos-query-frontend
  namespace: monitoring
spec:
  replicas: 2
  selector:
    matchLabels:
      app: thanos-query-frontend
  template:
    metadata:
      labels:
        app: thanos-query-frontend
    spec:
      containers:
      - name: thanos-query-frontend
        image: thanosio/thanos:v0.32.5
        args:
        - query-frontend
        - --log.level=info
        - --http-address=0.0.0.0:9090

        # Downstream Thanos Query
        - --query-frontend.downstream-url=http://thanos-query:9090

        # Query splitting
        - --query-range.split-interval=24h
        - --query-range.max-retries-per-request=5
        - --query-range.max-query-length=0  # unlimited
        - --query-range.max-query-parallelism=14

        # Response compression
        - --query-frontend.compress-responses
        - --cache-compression-type=snappy

        # Partial response
        - --query-range.partial-response

        # Cache configuration
        - --query-range.response-cache-max-freshness=1m
        - --query-range.response-cache-config-file=/etc/thanos/cache-config.yml

        # Alignment
        - --query-range.align-range-with-step

        ports:
        - containerPort: 9090
          name: http

        volumeMounts:
        - name: cache-config
          mountPath: /etc/thanos
          readOnly: true

        resources:
          requests:
            memory: 1Gi
            cpu: 500m
          limits:
            memory: 2Gi
            cpu: 1000m

      volumes:
      - name: cache-config
        configMap:
          name: thanos-query-frontend-cache

---
apiVersion: v1
kind: ConfigMap
metadata:
  name: thanos-query-frontend-cache
  namespace: monitoring
data:
  cache-config.yml: |
    type: REDIS
    config:
      addr: "redis.monitoring.svc.cluster.local:6379"
      username: ""
      password: ""
      db: 0
      dial_timeout: 5s
      read_timeout: 3s
      write_timeout: 3s
      max_get_multi_concurrency: 100
      get_multi_batch_size: 100
      max_set_multi_concurrency: 100
      set_multi_batch_size: 100
      expiration: 24h
      max_item_size: 5MiB
      set_async_circuit_breaker_config:
        enabled: true
        half_open_max_requests: 10
        open_duration: 5s
        min_requests: 50
        consecutive_failures: 5
        failure_percent: 0.05

---
apiVersion: v1
kind: Service
metadata:
  name: thanos-query-frontend
  namespace: monitoring
spec:
  type: ClusterIP
  ports:
  - port: 9090
    targetPort: 9090
    name: http
  selector:
    app: thanos-query-frontend
```

### Redis Cache for Query Frontend

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis-cache
  namespace: monitoring
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis-cache
  template:
    metadata:
      labels:
        app: redis-cache
    spec:
      containers:
      - name: redis
        image: redis:7-alpine
        command:
        - redis-server
        - --maxmemory
        - "2gb"
        - --maxmemory-policy
        - allkeys-lru
        - --save
        - ""  # Disable persistence for cache
        ports:
        - containerPort: 6379
          name: redis
        resources:
          requests:
            memory: 2Gi
            cpu: 500m
          limits:
            memory: 3Gi
            cpu: 1000m
        livenessProbe:
          tcpSocket:
            port: 6379
          initialDelaySeconds: 30
          periodSeconds: 10

---
apiVersion: v1
kind: Service
metadata:
  name: redis
  namespace: monitoring
spec:
  ports:
  - port: 6379
    targetPort: 6379
  selector:
    app: redis-cache
```

## Multi-Cluster Federation

### Global Query Setup

```yaml
multi_cluster_architecture:
  cluster_1_us_east:
    prometheus_instances:
      - prometheus-0 (replica: "0")
      - prometheus-1 (replica: "1")
    thanos_sidecar: "thanos-sidecar.us-east.svc.cluster.local:10901"
    external_labels:
      cluster: us-east
      region: us-east-1

  cluster_2_us_west:
    prometheus_instances:
      - prometheus-0 (replica: "0")
      - prometheus-1 (replica: "1")
    thanos_sidecar: "thanos-sidecar.us-west.svc.cluster.local:10901"
    external_labels:
      cluster: us-west
      region: us-west-2

  cluster_3_eu_central:
    prometheus_instances:
      - prometheus-0 (replica: "0")
      - prometheus-1 (replica: "1")
    thanos_sidecar: "thanos-sidecar.eu-central.svc.cluster.local:10901"
    external_labels:
      cluster: eu-central
      region: eu-central-1

  global_query:
    location: "Central monitoring cluster"
    stores:
      - "thanos-sidecar.us-east.svc.cluster.local:10901"
      - "thanos-sidecar.us-west.svc.cluster.local:10901"
      - "thanos-sidecar.eu-central.svc.cluster.local:10901"
      - "thanos-store.central.svc.cluster.local:10901"  # Historical data
```

### Cross-Cluster Query Configuration

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: thanos-query-stores
  namespace: monitoring
data:
  stores.yml: |
    # US East cluster
    - targets:
      - thanos-sidecar-0.us-east-1.example.com:10901
      - thanos-sidecar-1.us-east-1.example.com:10901
      labels:
        cluster: us-east
        region: us-east-1

    # US West cluster
    - targets:
      - thanos-sidecar-0.us-west-2.example.com:10901
      - thanos-sidecar-1.us-west-2.example.com:10901
      labels:
        cluster: us-west
        region: us-west-2

    # EU Central cluster
    - targets:
      - thanos-sidecar-0.eu-central-1.example.com:10901
      - thanos-sidecar-1.eu-central-1.example.com:10901
      labels:
        cluster: eu-central
        region: eu-central-1

    # Store Gateway (historical data)
    - targets:
      - thanos-store.monitoring.svc.cluster.local:10901
```

### Querying Across Clusters

```promql
# Query metric across all clusters
http_requests_total

# Query specific cluster
http_requests_total{cluster="us-east"}

# Aggregate across regions
sum by (region) (http_requests_total)

# Compare clusters
sum by (cluster) (rate(http_requests_total[5m]))

# Multi-cluster availability
avg by (cluster) (up)

# Cross-cluster error rates
sum by (cluster) (rate(http_requests_total{status=~"5.."}[5m]))
/ sum by (cluster) (rate(http_requests_total[5m]))
```

## Query Optimization

### Query Performance Tuning

```yaml
query_optimization_strategies:
  query_timeout_tuning:
    default: "2m"
    long_queries: "5m"
    recommendation: "Set based on P99 query duration"
    flag: "--query.timeout=5m"

  concurrent_query_limits:
    max_concurrent: 20
    max_concurrent_select: 4
    reasoning: "Prevent query queue buildup and OOM"
    flags:
      - "--query.max-concurrent=20"
      - "--query.max-concurrent-select=4"

  lookback_delta:
    default: "5m"
    description: "How far back to look for samples"
    use_case: "Match with Prometheus scrape interval"
    flag: "--query.lookback-delta=5m"

  store_response_timeout:
    default: "30s"
    recommendation: "Increase if Store Gateway is slow"
    flag: "--store.response-timeout=30s"

  auto_downsampling:
    enabled: true
    benefit: "Automatically use downsampled data for long ranges"
    flag: "--query.auto-downsampling"
```

### Query Sharding and Splitting

```yaml
query_frontend_optimization:
  horizontal_sharding:
    description: "Split query across time ranges"
    split_interval: "24h"
    example:
      original_query: "rate(http_requests_total[1h])[7d:]"
      split_into:
        - "rate(http_requests_total[1h])[7d:6d]"
        - "rate(http_requests_total[1h])[6d:5d]"
        - "rate(http_requests_total[1h])[5d:4d]"
        # ... 7 queries total

  vertical_sharding:
    description: "Split by series (future feature)"
    status: "Experimental in Thanos"

  query_parallelism:
    max_parallelism: 14
    recommendation: "Set to number of CPU cores"
    flag: "--query-range.max-query-parallelism=14"
```

## Partial Response Handling

### Partial Response Strategy

```yaml
partial_response_config:
  concept:
    description: "Return results even if some stores fail"
    use_case: "Maintain availability during partial outages"

  behavior:
    enabled:
      - "Query succeeds with available data"
      - "Warning headers indicate missing stores"
      - "Useful for dashboards that must always work"

    disabled:
      - "Query fails if any store is unavailable"
      - "Ensures complete data accuracy"
      - "Useful for alerting and critical queries"

  configuration:
    global_enable: "--query.partial-response"
    per_query_override:
      enable: "?partial_response=true"
      disable: "?partial_response=false"

  grafana_integration:
    datasource_config: |
      {
        "url": "http://thanos-query:9090",
        "access": "proxy",
        "jsonData": {
          "customQueryParameters": "partial_response=true"
        }
      }
```

### Handling Store Failures

```promql
# Query with partial response warning
up{job="api"}

# Response headers:
# Warning: 299 - "Partial response: store thanos-sidecar-1:10901 unavailable"

# Check store availability
thanos_store_nodes_grpc_connections

# Query execution info
thanos_query_concurrent_selects_in_flight
thanos_query_concurrent_queries
```

## Query Monitoring

### Essential Query Metrics

```promql
# Query latency (p95, p99)
histogram_quantile(0.95,
  rate(http_request_duration_seconds_bucket{handler="query_range"}[5m]))

histogram_quantile(0.99,
  rate(http_request_duration_seconds_bucket{handler="query_range"}[5m]))

# Query throughput
rate(http_requests_total{handler="query_range"}[5m])

# Query errors
rate(http_requests_total{handler="query_range",code=~"5.."}[5m])

# Concurrent queries
thanos_query_concurrent_selects_in_flight
thanos_query_concurrent_queries

# Store API connections
thanos_store_nodes_grpc_connections

# Partial response rate
rate(thanos_query_api_instant_query_partial_response_warnings_total[5m])

# Query queue depth
thanos_query_gate_queries_concurrent_max
thanos_query_gate_queries_in_flight

# Store response times
histogram_quantile(0.99,
  rate(thanos_query_store_api_query_duration_seconds_bucket[5m]))
```

### Query Performance Dashboard

```yaml
dashboard_panels:
  query_rate:
    query: "sum(rate(http_requests_total{job='thanos-query'}[5m]))"
    description: "Total queries per second"

  query_latency_p99:
    query: |
      histogram_quantile(0.99,
        sum by (le) (rate(http_request_duration_seconds_bucket{job="thanos-query"}[5m])))
    description: "99th percentile query latency"

  error_rate:
    query: |
      sum(rate(http_requests_total{job="thanos-query",code=~"5.."}[5m]))
      / sum(rate(http_requests_total{job="thanos-query"}[5m]))
    description: "Error rate percentage"

  concurrent_queries:
    query: "thanos_query_concurrent_selects_in_flight"
    description: "Number of queries executing"

  store_latency:
    query: |
      histogram_quantile(0.99,
        rate(thanos_query_store_api_query_duration_seconds_bucket[5m]))
    description: "Store API response time"

  cache_hit_rate:
    query: |
      sum(rate(thanos_cache_operations_total{operation="hit"}[5m]))
      / sum(rate(thanos_cache_operations_total[5m]))
    description: "Query cache effectiveness"
```

### Alerting Rules for Query

```yaml
groups:
- name: thanos-query
  interval: 30s
  rules:
  - alert: ThanosQueryHttpRequestQueryErrorRateHigh
    expr: |
      (
        sum by (job) (rate(http_requests_total{code=~"5..", job=~"thanos-query.*", handler="query"}[5m]))
        / sum by (job) (rate(http_requests_total{job=~"thanos-query.*", handler="query"}[5m]))
      ) * 100 > 5
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "Thanos Query error rate is high"
      description: "{{ $value | humanizePercentage }} of queries are failing"

  - alert: ThanosQueryHighDNSFailures
    expr: |
      rate(thanos_query_store_apis_dns_failures_total[5m]) > 0.01
    for: 15m
    labels:
      severity: warning
    annotations:
      summary: "Thanos Query has high DNS failure rate"

  - alert: ThanosQueryInstantLatencyHigh
    expr: |
      histogram_quantile(0.99,
        sum by (job, le) (rate(http_request_duration_seconds_bucket{job=~"thanos-query.*", handler="query"}[5m]))
      ) > 10
    for: 10m
    labels:
      severity: warning
    annotations:
      summary: "Thanos Query latency is high"
      description: "P99 latency is {{ $value }}s"

  - alert: ThanosQueryOverload
    expr: |
      max_over_time(thanos_query_concurrent_selects_in_flight[5m])
      / thanos_query_concurrent_selects_gate > 0.9
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "Thanos Query is overloaded"

  - alert: ThanosQueryStoreUnhealthy
    expr: |
      thanos_query_store_apis_dns_provider_results == 0
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "Thanos Query cannot discover stores"
```

## Advanced Query Patterns

### Query Optimization Techniques

```promql
# BAD: Query all data then filter
sum(rate(http_requests_total[5m])) by (job) > 100

# GOOD: Filter first, then aggregate
sum(rate(http_requests_total{job="api"}[5m]))

# BAD: Wide time range with raw resolution
rate(http_requests_total[7d])

# GOOD: Use appropriate downsampling
rate(http_requests_total[7d:5m])  # 5m resolution for 7d range

# BAD: Multiple separate queries in dashboard
http_requests_total{endpoint="/api/v1"}
http_requests_total{endpoint="/api/v2"}

# GOOD: Single query with regex
http_requests_total{endpoint=~"/api/.*"}

# Efficient aggregation across clusters
sum by (cluster) (
  rate(http_requests_total[5m])
) > 1000

# Time-based SLA calculation
avg_over_time(
  (1 - (
    rate(http_requests_total{status=~"5.."}[5m])
    / rate(http_requests_total[5m])
  ))[30d:]
) > 0.999
```

This comprehensive guide provides production-ready configurations for deploying and managing Thanos Query for global metric federation and query optimization.
