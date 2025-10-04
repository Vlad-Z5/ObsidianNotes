# Thanos Architecture and Components

**Thanos Architecture and Components** provides comprehensive understanding of Thanos distributed architecture, core components, deployment patterns, and integration strategies for building highly available, scalable Prometheus infrastructure with unlimited retention.

## Thanos Architecture Overview

### Core Architecture Principles

#### Distributed Architecture Design
```yaml
thanos_architecture:
  design_principles:
    horizontal_scaling:
      description: "Components can be scaled independently based on workload"
      benefits:
        - "Handle increasing metric volumes"
        - "Scale query capacity separately from storage"
        - "Distribute load across multiple instances"
      implementation:
        - "Stateless query components"
        - "Distributed storage architecture"
        - "Independent component scaling"

    high_availability:
      description: "Built-in redundancy and fault tolerance"
      components:
        - "Multi-replica deployments"
        - "Cross-zone distribution"
        - "Graceful failure handling"
      strategies:
        - "Active-active query setup"
        - "Redundant storage backends"
        - "Health check integration"

    long_term_storage:
      description: "Unlimited retention with cost-effective storage"
      features:
        - "Object storage integration"
        - "Automatic data lifecycle management"
        - "Configurable retention policies"
      storage_backends:
        - "AWS S3"
        - "Google Cloud Storage"
        - "Azure Blob Storage"
        - "MinIO"

  system_components:
    prometheus_integration:
      sidecar_pattern: "Thanos Sidecar runs alongside Prometheus"
      data_upload: "Automatic upload to object storage"
      metadata_sync: "Real-time metadata synchronization"

    query_layer:
      global_view: "Unified query interface across all data"
      deduplication: "Automatic metric deduplication"
      federation: "Multi-cluster query federation"

    storage_layer:
      object_storage: "Cost-effective long-term storage"
      compaction: "Automatic data compaction and downsampling"
      retention: "Configurable data lifecycle management"
```

## Core Thanos Components

### Thanos Sidecar

#### Sidecar Configuration and Deployment
```yaml
thanos_sidecar:
  deployment_pattern: |
    # Kubernetes Deployment with Thanos Sidecar
    apiVersion: apps/v1
    kind: Deployment
    metadata:
      name: prometheus-with-thanos
      namespace: monitoring
    spec:
      replicas: 1
      selector:
        matchLabels:
          app: prometheus
      template:
        metadata:
          labels:
            app: prometheus
        spec:
          serviceAccountName: prometheus
          containers:
          - name: prometheus
            image: prom/prometheus:v2.45.0
            args:
              - --config.file=/etc/prometheus/prometheus.yml
              - --storage.tsdb.path=/prometheus/data
              - --storage.tsdb.retention.time=6h
              - --storage.tsdb.min-block-duration=2h
              - --storage.tsdb.max-block-duration=2h
              - --web.enable-lifecycle
              - --web.external-url=http://prometheus.monitoring.svc.cluster.local:9090
            ports:
            - containerPort: 9090
              name: prometheus
            volumeMounts:
            - name: prometheus-data
              mountPath: /prometheus/data
            - name: prometheus-config
              mountPath: /etc/prometheus
            resources:
              requests:
                memory: 2Gi
                cpu: 1000m
              limits:
                memory: 4Gi
                cpu: 2000m

          - name: thanos-sidecar
            image: thanosio/thanos:v0.32.0
            args:
              - sidecar
              - --prometheus.url=http://localhost:9090
              - --tsdb.path=/prometheus/data
              - --grpc-address=0.0.0.0:10901
              - --http-address=0.0.0.0:10902
              - --objstore.config-file=/etc/thanos/objstore.yml
              - --log.level=info
              - --log.format=logfmt
            ports:
            - containerPort: 10901
              name: grpc
            - containerPort: 10902
              name: http
            volumeMounts:
            - name: prometheus-data
              mountPath: /prometheus/data
            - name: thanos-objstore-config
              mountPath: /etc/thanos
            resources:
              requests:
                memory: 512Mi
                cpu: 500m
              limits:
                memory: 1Gi
                cpu: 1000m
            env:
            - name: POD_NAME
              valueFrom:
                fieldRef:
                  fieldPath: metadata.name

          volumes:
          - name: prometheus-data
            persistentVolumeClaim:
              claimName: prometheus-data
          - name: prometheus-config
            configMap:
              name: prometheus-config
          - name: thanos-objstore-config
            secret:
              secretName: thanos-objstore-config

  object_storage_config: |
    # Object Storage Configuration Secret
    apiVersion: v1
    kind: Secret
    metadata:
      name: thanos-objstore-config
      namespace: monitoring
    type: Opaque
    stringData:
      objstore.yml: |
        type: S3
        config:
          bucket: "thanos-metrics-storage"
          endpoint: "s3.us-east-1.amazonaws.com"
          region: "us-east-1"
          access_key: ""
          secret_key: ""
          insecure: false
          signature_version2: false
          encrypt_sse: true
          put_user_metadata: {}
          http_config:
            idle_conn_timeout: 90s
            response_header_timeout: 2m
            insecure_skip_verify: false
          trace:
            enable: false
          part_size: 67108864

  service_configuration: |
    # Thanos Sidecar Service
    apiVersion: v1
    kind: Service
    metadata:
      name: thanos-sidecar
      namespace: monitoring
      labels:
        app: thanos-sidecar
    spec:
      ports:
      - name: grpc
        port: 10901
        targetPort: 10901
      - name: http
        port: 10902
        targetPort: 10902
      selector:
        app: prometheus
      type: ClusterIP

  monitoring_configuration: |
    # ServiceMonitor for Thanos Sidecar
    apiVersion: monitoring.coreos.com/v1
    kind: ServiceMonitor
    metadata:
      name: thanos-sidecar
      namespace: monitoring
    spec:
      selector:
        matchLabels:
          app: thanos-sidecar
      endpoints:
      - port: http
        interval: 30s
        path: /metrics
```

### Thanos Query

#### Query Component Setup
```yaml
thanos_query:
  deployment: |
    # Thanos Query Deployment
    apiVersion: apps/v1
    kind: Deployment
    metadata:
      name: thanos-query
      namespace: monitoring
    spec:
      replicas: 3
      selector:
        matchLabels:
          app: thanos-query
      template:
        metadata:
          labels:
            app: thanos-query
        spec:
          containers:
          - name: thanos-query
            image: thanosio/thanos:v0.32.0
            args:
              - query
              - --grpc-address=0.0.0.0:10901
              - --http-address=0.0.0.0:9090
              - --log.level=info
              - --log.format=logfmt
              - --query.replica-label=replica
              - --query.replica-label=prometheus_replica
              - --store=thanos-sidecar.monitoring.svc.cluster.local:10901
              - --store=thanos-store.monitoring.svc.cluster.local:10901
              - --store=thanos-receive.monitoring.svc.cluster.local:10901
              - --query.timeout=2m
              - --query.max-concurrent=20
              - --query.lookback-delta=15m
              - --query.max-concurrent-select=4
              - --store.response-timeout=30s
            ports:
            - containerPort: 9090
              name: http
            - containerPort: 10901
              name: grpc
            resources:
              requests:
                memory: 1Gi
                cpu: 500m
              limits:
                memory: 2Gi
                cpu: 1000m
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

  service_configuration: |
    # Thanos Query Service
    apiVersion: v1
    kind: Service
    metadata:
      name: thanos-query
      namespace: monitoring
      labels:
        app: thanos-query
    spec:
      ports:
      - name: http
        port: 9090
        targetPort: 9090
      - name: grpc
        port: 10901
        targetPort: 10901
      selector:
        app: thanos-query
      type: ClusterIP

  ingress_configuration: |
    # Thanos Query Ingress
    apiVersion: networking.k8s.io/v1
    kind: Ingress
    metadata:
      name: thanos-query
      namespace: monitoring
      annotations:
        kubernetes.io/ingress.class: nginx
        cert-manager.io/cluster-issuer: letsencrypt-prod
        nginx.ingress.kubernetes.io/auth-type: basic
        nginx.ingress.kubernetes.io/auth-secret: thanos-basic-auth
    spec:
      tls:
      - hosts:
        - thanos-query.company.com
        secretName: thanos-query-tls
      rules:
      - host: thanos-query.company.com
        http:
          paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: thanos-query
                port:
                  number: 9090

  hpa_configuration: |
    # Horizontal Pod Autoscaler for Thanos Query
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
            name: thanos_query_concurrent_queries
          target:
            type: AverageValue
            averageValue: "15"
```

### Thanos Store Gateway

#### Store Gateway Configuration
```yaml
thanos_store:
  deployment: |
    # Thanos Store Gateway Deployment
    apiVersion: apps/v1
    kind: Deployment
    metadata:
      name: thanos-store
      namespace: monitoring
    spec:
      replicas: 3
      selector:
        matchLabels:
          app: thanos-store
      template:
        metadata:
          labels:
            app: thanos-store
        spec:
          containers:
          - name: thanos-store
            image: thanosio/thanos:v0.32.0
            args:
              - store
              - --grpc-address=0.0.0.0:10901
              - --http-address=0.0.0.0:10902
              - --data-dir=/var/thanos/store
              - --objstore.config-file=/etc/thanos/objstore.yml
              - --log.level=info
              - --log.format=logfmt
              - --index-cache-size=2GB
              - --chunk-pool-size=2GB
              - --store.grpc.series-sample-limit=120000
              - --store.grpc.series-max-concurrency=20
              - --sync-block-duration=5m
              - --block-sync-concurrency=20
              - --min-time=-6h
              - --max-time=-2h
            ports:
            - containerPort: 10901
              name: grpc
            - containerPort: 10902
              name: http
            volumeMounts:
            - name: thanos-store-data
              mountPath: /var/thanos/store
            - name: thanos-objstore-config
              mountPath: /etc/thanos
            resources:
              requests:
                memory: 4Gi
                cpu: 1000m
              limits:
                memory: 8Gi
                cpu: 2000m
            livenessProbe:
              httpGet:
                path: /-/healthy
                port: 10902
              initialDelaySeconds: 30
              periodSeconds: 30
            readinessProbe:
              httpGet:
                path: /-/ready
                port: 10902
              initialDelaySeconds: 10
              periodSeconds: 5

          volumes:
          - name: thanos-store-data
            persistentVolumeClaim:
              claimName: thanos-store-data
          - name: thanos-objstore-config
            secret:
              secretName: thanos-objstore-config

  storage_configuration: |
    # Persistent Volume Claim for Store Gateway
    apiVersion: v1
    kind: PersistentVolumeClaim
    metadata:
      name: thanos-store-data
      namespace: monitoring
    spec:
      accessModes:
        - ReadWriteOnce
      storageClassName: fast-ssd
      resources:
        requests:
          storage: 50Gi

  service_configuration: |
    # Thanos Store Service
    apiVersion: v1
    kind: Service
    metadata:
      name: thanos-store
      namespace: monitoring
      labels:
        app: thanos-store
    spec:
      ports:
      - name: grpc
        port: 10901
        targetPort: 10901
      - name: http
        port: 10902
        targetPort: 10902
      selector:
        app: thanos-store
      type: ClusterIP

  caching_configuration: |
    # Redis Cache for Store Gateway
    apiVersion: apps/v1
    kind: Deployment
    metadata:
      name: thanos-cache-redis
      namespace: monitoring
    spec:
      replicas: 1
      selector:
        matchLabels:
          app: thanos-cache-redis
      template:
        metadata:
          labels:
            app: thanos-cache-redis
        spec:
          containers:
          - name: redis
            image: redis:7-alpine
            ports:
            - containerPort: 6379
            resources:
              requests:
                memory: 1Gi
                cpu: 200m
              limits:
                memory: 2Gi
                cpu: 500m
            volumeMounts:
            - name: redis-data
              mountPath: /data
          volumes:
          - name: redis-data
            persistentVolumeClaim:
              claimName: thanos-cache-redis-data
```

### Thanos Compactor

#### Compactor Service Setup
```yaml
thanos_compactor:
  deployment: |
    # Thanos Compactor Deployment
    apiVersion: apps/v1
    kind: Deployment
    metadata:
      name: thanos-compactor
      namespace: monitoring
    spec:
      replicas: 1
      selector:
        matchLabels:
          app: thanos-compactor
      template:
        metadata:
          labels:
            app: thanos-compactor
        spec:
          containers:
          - name: thanos-compactor
            image: thanosio/thanos:v0.32.0
            args:
              - compact
              - --wait
              - --log.level=info
              - --log.format=logfmt
              - --objstore.config-file=/etc/thanos/objstore.yml
              - --data-dir=/var/thanos/compactor
              - --consistency-delay=30m
              - --retention.resolution-raw=30d
              - --retention.resolution-5m=180d
              - --retention.resolution-1h=2y
              - --compact.concurrency=1
              - --downsample.concurrency=1
              - --delete-delay=48h
              - --deduplication.replica-label=replica
              - --deduplication.replica-label=prometheus_replica
            ports:
            - containerPort: 10902
              name: http
            volumeMounts:
            - name: thanos-compactor-data
              mountPath: /var/thanos/compactor
            - name: thanos-objstore-config
              mountPath: /etc/thanos
            resources:
              requests:
                memory: 2Gi
                cpu: 1000m
              limits:
                memory: 4Gi
                cpu: 2000m
            livenessProbe:
              httpGet:
                path: /-/healthy
                port: 10902
              initialDelaySeconds: 30
              periodSeconds: 30

          volumes:
          - name: thanos-compactor-data
            persistentVolumeClaim:
              claimName: thanos-compactor-data
          - name: thanos-objstore-config
            secret:
              secretName: thanos-objstore-config

  storage_configuration: |
    # Persistent Volume for Compactor
    apiVersion: v1
    kind: PersistentVolumeClaim
    metadata:
      name: thanos-compactor-data
      namespace: monitoring
    spec:
      accessModes:
        - ReadWriteOnce
      storageClassName: fast-ssd
      resources:
        requests:
          storage: 100Gi

  cronjob_configuration: |
    # CronJob for Compactor Cleanup
    apiVersion: batch/v1
    kind: CronJob
    metadata:
      name: thanos-compactor-cleanup
      namespace: monitoring
    spec:
      schedule: "0 2 * * *"  # Daily at 2 AM
      jobTemplate:
        spec:
          template:
            spec:
              containers:
              - name: cleanup
                image: thanosio/thanos:v0.32.0
                args:
                  - tools
                  - bucket
                  - cleanup
                  - --objstore.config-file=/etc/thanos/objstore.yml
                  - --log.level=info
                volumeMounts:
                - name: thanos-objstore-config
                  mountPath: /etc/thanos
              volumes:
              - name: thanos-objstore-config
                secret:
                  secretName: thanos-objstore-config
              restartPolicy: OnFailure
```

## High Availability Setup

### Multi-Zone Deployment

#### HA Architecture Configuration
```yaml
high_availability_setup:
  anti_affinity_rules: |
    # Pod Anti-Affinity for High Availability
    spec:
      affinity:
        podAntiAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
          - labelSelector:
              matchLabels:
                app: thanos-query
            topologyKey: kubernetes.io/hostname
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            podAffinityTerm:
              labelSelector:
                matchLabels:
                  app: thanos-query
              topologyKey: topology.kubernetes.io/zone

  load_balancing: |
    # Load Balancer Configuration
    apiVersion: v1
    kind: Service
    metadata:
      name: thanos-query-lb
      namespace: monitoring
      annotations:
        service.beta.kubernetes.io/aws-load-balancer-type: nlb
        service.beta.kubernetes.io/aws-load-balancer-cross-zone-load-balancing-enabled: "true"
    spec:
      type: LoadBalancer
      ports:
      - name: http
        port: 9090
        targetPort: 9090
      - name: grpc
        port: 10901
        targetPort: 10901
      selector:
        app: thanos-query

  disaster_recovery: |
    # Cross-Region DR Setup
    apiVersion: v1
    kind: Secret
    metadata:
      name: thanos-objstore-dr-config
      namespace: monitoring
    type: Opaque
    stringData:
      objstore.yml: |
        type: S3
        config:
          bucket: "thanos-metrics-storage-dr"
          endpoint: "s3.us-west-2.amazonaws.com"
          region: "us-west-2"
          access_key: ""
          secret_key: ""
          insecure: false
          signature_version2: false
          encrypt_sse: true

  backup_strategy: |
    # Backup Configuration
    apiVersion: batch/v1
    kind: CronJob
    metadata:
      name: thanos-metadata-backup
      namespace: monitoring
    spec:
      schedule: "0 1 * * *"  # Daily at 1 AM
      jobTemplate:
        spec:
          template:
            spec:
              containers:
              - name: backup
                image: thanosio/thanos:v0.32.0
                args:
                  - tools
                  - bucket
                  - replicate
                  - --objstore.config-file=/etc/thanos/objstore.yml
                  - --objstore-to.config-file=/etc/thanos/objstore-dr.yml
                  - --log.level=info
                volumeMounts:
                - name: thanos-objstore-config
                  mountPath: /etc/thanos
              volumes:
              - name: thanos-objstore-config
                secret:
                  secretName: thanos-objstore-config
              restartPolicy: OnFailure
```

## Prometheus Integration

### Prometheus Configuration for Thanos

#### Prometheus Setup with Thanos Integration
```yaml
prometheus_thanos_integration:
  prometheus_config: |
    # Prometheus Configuration for Thanos
    global:
      scrape_interval: 15s
      evaluation_interval: 15s
      external_labels:
        cluster: production
        region: us-east-1
        replica: prometheus-0

    rule_files:
      - "/etc/prometheus/rules/*.yml"

    scrape_configs:
      - job_name: 'prometheus'
        static_configs:
          - targets: ['localhost:9090']

      - job_name: 'thanos-sidecar'
        static_configs:
          - targets: ['localhost:10902']

      - job_name: 'thanos-query'
        kubernetes_sd_configs:
          - role: endpoints
            namespaces:
              names:
                - monitoring
        relabel_configs:
          - source_labels: [__meta_kubernetes_service_name]
            action: keep
            regex: thanos-query

      - job_name: 'thanos-store'
        kubernetes_sd_configs:
          - role: endpoints
            namespaces:
              names:
                - monitoring
        relabel_configs:
          - source_labels: [__meta_kubernetes_service_name]
            action: keep
            regex: thanos-store

  recording_rules: |
    # Recording Rules for Thanos Metrics
    groups:
    - name: thanos.rules
      rules:
      - record: thanos:query_duration_seconds:rate5m
        expr: rate(thanos_query_duration_seconds_sum[5m]) / rate(thanos_query_duration_seconds_count[5m])

      - record: thanos:store_series_blocks_queried:rate5m
        expr: rate(thanos_bucket_store_series_blocks_queried_sum[5m])

      - record: thanos:compactor_iterations:rate5m
        expr: rate(thanos_compact_iterations_total[5m])

      - record: thanos:objstore_operation_duration:rate5m
        expr: rate(thanos_objstore_operation_duration_seconds_sum[5m]) / rate(thanos_objstore_operation_duration_seconds_count[5m])

  alerting_rules: |
    # Alerting Rules for Thanos
    groups:
    - name: thanos.alerts
      rules:
      - alert: ThanosQueryHttpRequestQueryErrorRateHigh
        expr: rate(http_requests_total{code=~"5..", job=~"thanos-query.*", handler="query"}[5m]) > 0.01
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Thanos Query is failing to handle requests"
          description: "Thanos Query {{ $labels.instance }} is failing to handle {{ $value | humanizePercentage }} of requests."

      - alert: ThanosStoreGrpcErrorRate
        expr: rate(grpc_server_handled_total{grpc_code=~"Unknown|ResourceExhausted|Internal|Unavailable|DataLoss|DeadlineExceeded", job=~"thanos-store.*"}[5m]) > 0.01
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Thanos Store is failing to handle requests"
          description: "Thanos Store {{ $labels.instance }} is failing to handle {{ $value | humanizePercentage }} of requests."

      - alert: ThanosCompactHalted
        expr: thanos_compact_halted > 0
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Thanos compaction has failed to run"
          description: "Thanos Compact {{ $labels.instance }} has failed to run and is halted."
```

This comprehensive Thanos Architecture and Components document provides detailed understanding of Thanos distributed architecture, component configurations, high availability setup, and Prometheus integration essential for building enterprise-grade monitoring infrastructure with unlimited retention capabilities.