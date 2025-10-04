# Thanos Ruler and Alerting

Complete guide to rule evaluation, recording rules, alerting rules, high availability alerting, AlertManager integration, and distributed rule management for global alerting across federated Prometheus infrastructure.

**Key Concepts:** Recording rules, alerting rules, rule evaluation, partial response in rules, stateful rule execution, AlertManager integration, rule deduplication, rule sharding, ruler high availability, query federation for rules

## Ruler Architecture

### Thanos Ruler Overview

```yaml
thanos_ruler_architecture:
  ruler_purpose:
    description: "Evaluate recording and alerting rules against Thanos Query"
    capabilities:
      - "Execute recording rules for pre-aggregated metrics"
      - "Evaluate alerting rules for global alerting"
      - "Store rule evaluation results in object storage"
      - "Send alerts to AlertManager"
      - "Support high availability with multiple ruler instances"
      - "Access data across all Prometheus instances"

  why_use_ruler:
    recording_rules:
      - "Pre-compute expensive queries"
      - "Create rollup metrics for dashboards"
      - "Reduce query load on Thanos Query"
    alerting_rules:
      - "Alert on global metrics across clusters"
      - "Centralized alerting logic"
      - "Alert on historical data from object storage"

  ruler_vs_prometheus_rules:
    prometheus_rules:
      scope: "Single Prometheus instance"
      data_access: "Local TSDB only"
      ha_complexity: "Manual configuration per instance"

    thanos_ruler:
      scope: "Global across all Prometheus instances"
      data_access: "All data via Thanos Query"
      ha_complexity: "Built-in HA with deduplication"

  data_flow:
    step_1: "Ruler queries Thanos Query for rule evaluation"
    step_2: "Thanos Query fans out to all Store APIs"
    step_3: "Ruler evaluates rules and generates results"
    step_4: "Recording rule results stored in object storage"
    step_5: "Alerting rule results sent to AlertManager"
    step_6: "Results become queryable through Store Gateway"
```

## Ruler Deployment

### Production Ruler Configuration

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: thanos-ruler
  namespace: monitoring
  labels:
    app: thanos-ruler
spec:
  serviceName: thanos-ruler
  replicas: 2  # HA setup with 2+ replicas
  selector:
    matchLabels:
      app: thanos-ruler
  template:
    metadata:
      labels:
        app: thanos-ruler
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "10902"
    spec:
      serviceAccountName: thanos-ruler
      securityContext:
        fsGroup: 65534
        runAsUser: 65534
        runAsNonRoot: true

      affinity:
        podAntiAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
          - labelSelector:
              matchLabels:
                app: thanos-ruler
            topologyKey: kubernetes.io/hostname

      containers:
      - name: thanos-ruler
        image: thanosio/thanos:v0.32.5
        args:
        # Basic configuration
        - rule
        - --log.level=info
        - --log.format=logfmt
        - --grpc-address=0.0.0.0:10901
        - --http-address=0.0.0.0:10902

        # Data directory for WAL and local storage
        - --data-dir=/var/thanos/ruler

        # Query endpoint
        - --query=thanos-query.monitoring.svc.cluster.local:9090

        # Rule files
        - --rule-file=/etc/thanos/rules/*.yml

        # Object storage for recording rule results
        - --objstore.config-file=/etc/thanos/objstore.yml

        # Evaluation interval
        - --eval-interval=30s

        # AlertManager configuration
        - --alertmanagers.url=http://alertmanager.monitoring.svc.cluster.local:9093
        - --alertmanagers.send-timeout=10s
        - --alert.query-url=https://thanos-query.example.com

        # Labels for identifying ruler instance
        - --label=ruler_cluster="production"
        - --label=ruler_replica="$(POD_NAME)"

        # High availability
        - --alert.label-drop=ruler_replica

        # Query configuration for rule evaluation
        - --query.http-method=POST
        - --query.timeout=2m

        # Restore from object storage on startup
        - --resend-delay=5m

        env:
        - name: POD_NAME
          valueFrom:
            fieldRef:
              fieldPath: metadata.name

        ports:
        - containerPort: 10902
          name: http
        - containerPort: 10901
          name: grpc

        volumeMounts:
        - name: data
          mountPath: /var/thanos/ruler
        - name: rules
          mountPath: /etc/thanos/rules
          readOnly: true
        - name: objstore-config
          mountPath: /etc/thanos
          readOnly: true

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
          timeoutSeconds: 10

        readinessProbe:
          httpGet:
            path: /-/ready
            port: 10902
          initialDelaySeconds: 10
          periodSeconds: 5
          timeoutSeconds: 10

      volumes:
      - name: rules
        configMap:
          name: thanos-ruler-rules
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
          storage: 50Gi

---
apiVersion: v1
kind: Service
metadata:
  name: thanos-ruler
  namespace: monitoring
  labels:
    app: thanos-ruler
spec:
  type: ClusterIP
  clusterIP: None  # Headless for StatefulSet
  ports:
  - port: 10902
    targetPort: 10902
    name: http
  - port: 10901
    targetPort: 10901
    name: grpc
  selector:
    app: thanos-ruler

---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: thanos-ruler
  namespace: monitoring
  annotations:
    eks.amazonaws.com/role-arn: arn:aws:iam::ACCOUNT_ID:role/thanos-ruler-role

---
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: thanos-ruler-pdb
  namespace: monitoring
spec:
  minAvailable: 1
  selector:
    matchLabels:
      app: thanos-ruler
```

## Recording Rules

### Recording Rules Configuration

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: thanos-ruler-rules
  namespace: monitoring
data:
  recording-rules.yml: |
    groups:
    # Pre-aggregated metrics for faster queries
    - name: instance_metrics
      interval: 30s
      rules:
      # CPU usage by instance
      - record: instance:cpu_usage:rate5m
        expr: |
          100 * (
            1 - avg by (instance) (
              irate(node_cpu_seconds_total{mode="idle"}[5m])
            )
          )

      # Memory usage by instance
      - record: instance:memory_usage:ratio
        expr: |
          (
            node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes
          ) / node_memory_MemTotal_bytes

      # Disk usage by instance and device
      - record: instance:disk_usage:ratio
        expr: |
          (
            node_filesystem_size_bytes - node_filesystem_free_bytes
          ) / node_filesystem_size_bytes

    # Application-level recording rules
    - name: application_metrics
      interval: 30s
      rules:
      # Request rate by job
      - record: job:http_requests:rate5m
        expr: sum by (job) (rate(http_requests_total[5m]))

      # Error rate by job
      - record: job:http_errors:rate5m
        expr: sum by (job) (rate(http_requests_total{status=~"5.."}[5m]))

      # Request duration p95 by job
      - record: job:http_request_duration:p95
        expr: |
          histogram_quantile(0.95,
            sum by (job, le) (
              rate(http_request_duration_seconds_bucket[5m])
            )
          )

      # Request duration p99 by job
      - record: job:http_request_duration:p99
        expr: |
          histogram_quantile(0.99,
            sum by (job, le) (
              rate(http_request_duration_seconds_bucket[5m])
            )
          )

    # Multi-cluster aggregations
    - name: cluster_metrics
      interval: 1m
      rules:
      # Total requests across all clusters
      - record: cluster:http_requests:rate5m
        expr: sum by (cluster) (job:http_requests:rate5m)

      # Cluster-wide error rate
      - record: cluster:http_error_rate:ratio
        expr: |
          sum by (cluster) (job:http_errors:rate5m)
          / sum by (cluster) (job:http_requests:rate5m)

      # Available capacity by cluster
      - record: cluster:capacity_available:ratio
        expr: |
          sum by (cluster) (
            kube_node_status_allocatable{resource="cpu"}
            - kube_pod_container_resource_requests{resource="cpu"}
          )
          / sum by (cluster) (
            kube_node_status_allocatable{resource="cpu"}
          )

    # SLO calculations
    - name: slo_metrics
      interval: 1m
      rules:
      # API availability (99.9% SLO)
      - record: slo:api_availability:ratio30d
        expr: |
          1 - (
            sum(rate(http_requests_total{status=~"5..", job="api"}[30d]))
            / sum(rate(http_requests_total{job="api"}[30d]))
          )

      # Error budget remaining
      - record: slo:api_error_budget:ratio30d
        expr: |
          (0.999 - slo:api_availability:ratio30d) / (1 - 0.999)

      # Request latency SLO (95% < 500ms)
      - record: slo:api_latency:ratio30d
        expr: |
          sum(
            rate(http_request_duration_seconds_bucket{le="0.5", job="api"}[30d])
          )
          / sum(rate(http_request_duration_seconds_count{job="api"}[30d]))

    # Cost optimization metrics
    - name: cost_metrics
      interval: 5m
      rules:
      # Resource utilization for cost analysis
      - record: namespace:cpu_usage:sum
        expr: |
          sum by (namespace) (
            rate(container_cpu_usage_seconds_total[5m])
          )

      - record: namespace:memory_usage:sum
        expr: |
          sum by (namespace) (
            container_memory_working_set_bytes
          )

      # Idle resource detection
      - record: namespace:cpu_idle:ratio
        expr: |
          (
            sum by (namespace) (kube_pod_container_resource_requests{resource="cpu"})
            - namespace:cpu_usage:sum
          )
          / sum by (namespace) (kube_pod_container_resource_requests{resource="cpu"})
```

## Alerting Rules

### Alerting Rules Configuration

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: thanos-ruler-rules
  namespace: monitoring
data:
  alerting-rules.yml: |
    groups:
    # Infrastructure alerts
    - name: infrastructure_alerts
      interval: 30s
      rules:
      - alert: InstanceDown
        expr: up == 0
        for: 5m
        labels:
          severity: critical
          team: sre
        annotations:
          summary: "Instance {{ $labels.instance }} is down"
          description: |
            Instance {{ $labels.instance }} of job {{ $labels.job }}
            has been down for more than 5 minutes.
          runbook: "https://docs.company.com/runbooks/instance-down"
          dashboard: "https://grafana.company.com/d/instance"

      - alert: HighCPUUsage
        expr: instance:cpu_usage:rate5m > 85
        for: 10m
        labels:
          severity: warning
          team: sre
        annotations:
          summary: "High CPU usage on {{ $labels.instance }}"
          description: |
            CPU usage is {{ $value | humanizePercentage }} on instance {{ $labels.instance }}

      - alert: HighMemoryUsage
        expr: instance:memory_usage:ratio > 0.90
        for: 10m
        labels:
          severity: warning
          team: sre
        annotations:
          summary: "High memory usage on {{ $labels.instance }}"
          description: |
            Memory usage is {{ $value | humanizePercentage }} on {{ $labels.instance }}

      - alert: DiskSpaceLow
        expr: instance:disk_usage:ratio > 0.85
        for: 5m
        labels:
          severity: warning
          team: sre
        annotations:
          summary: "Low disk space on {{ $labels.instance }}"
          description: |
            Disk usage is {{ $value | humanizePercentage }} on {{ $labels.instance }}
            mount {{ $labels.mountpoint }}

    # Application alerts
    - name: application_alerts
      interval: 30s
      rules:
      - alert: HighErrorRate
        expr: |
          (
            sum by (job) (job:http_errors:rate5m)
            / sum by (job) (job:http_requests:rate5m)
          ) > 0.05
        for: 5m
        labels:
          severity: critical
          team: backend
        annotations:
          summary: "High error rate for {{ $labels.job }}"
          description: |
            Error rate is {{ $value | humanizePercentage }} for job {{ $labels.job }}

      - alert: HighLatency
        expr: job:http_request_duration:p99 > 2
        for: 10m
        labels:
          severity: warning
          team: backend
        annotations:
          summary: "High latency for {{ $labels.job }}"
          description: |
            P99 latency is {{ $value }}s for job {{ $labels.job }}

      - alert: APIThroughputLow
        expr: |
          sum by (job) (job:http_requests:rate5m) < 10
          and
          hour() >= 9 and hour() <= 17  # During business hours
        for: 15m
        labels:
          severity: warning
          team: backend
        annotations:
          summary: "Unusually low API throughput"
          description: |
            API {{ $labels.job }} throughput is only {{ $value }} req/s during business hours

    # SLO alerts
    - name: slo_alerts
      interval: 1m
      rules:
      - alert: SLOErrorBudgetBurn
        expr: |
          (
            1 - slo:api_availability:ratio30d
          ) / (1 - 0.999) > 0.1
        for: 1h
        labels:
          severity: warning
          team: sre
        annotations:
          summary: "Error budget is burning fast"
          description: |
            API error budget has consumed {{ $value | humanizePercentage }}
            in the last 30 days. SLO target is 99.9%.

      - alert: SLOErrorBudgetExhausted
        expr: slo:api_error_budget:ratio30d < 0
        labels:
          severity: critical
          team: sre
        annotations:
          summary: "Error budget exhausted"
          description: |
            API has exceeded error budget for 99.9% SLO target.
            Current availability: {{ $value | humanizePercentage }}

    # Multi-cluster alerts
    - name: cluster_alerts
      interval: 1m
      rules:
      - alert: ClusterErrorRateHigh
        expr: cluster:http_error_rate:ratio > 0.01
        for: 5m
        labels:
          severity: warning
          team: sre
        annotations:
          summary: "High error rate in {{ $labels.cluster }}"
          description: |
            Cluster {{ $labels.cluster }} error rate is {{ $value | humanizePercentage }}

      - alert: ClusterCapacityLow
        expr: cluster:capacity_available:ratio < 0.2
        for: 10m
        labels:
          severity: warning
          team: sre
        annotations:
          summary: "Low capacity in {{ $labels.cluster }}"
          description: |
            Cluster {{ $labels.cluster }} has only {{ $value | humanizePercentage }}
            capacity remaining

    # Cost optimization alerts
    - name: cost_alerts
      interval: 5m
      rules:
      - alert: HighIdleResources
        expr: namespace:cpu_idle:ratio > 0.5
        for: 6h
        labels:
          severity: info
          team: finops
        annotations:
          summary: "High idle resources in {{ $labels.namespace }}"
          description: |
            Namespace {{ $labels.namespace }} has {{ $value | humanizePercentage }}
            idle CPU resources. Consider rightsizing.

    # Thanos component health
    - name: thanos_alerts
      interval: 30s
      rules:
      - alert: ThanosRulerQueueIsFull
        expr: |
          prometheus_rule_group_last_duration_seconds
          / prometheus_rule_group_interval_seconds > 1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Thanos Ruler evaluation is falling behind"

      - alert: ThanosRulerSendAlertsFailing
        expr: rate(thanos_alert_sender_errors_total[5m]) > 0.01
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Thanos Ruler failing to send alerts to AlertManager"

      - alert: ThanosRulerHighRuleEvaluationFailures
        expr: |
          rate(prometheus_rule_evaluation_failures_total[5m]) > 0.01
        for: 15m
        labels:
          severity: warning
        annotations:
          summary: "Thanos Ruler has high rule evaluation failure rate"
```

## AlertManager Integration

### AlertManager Configuration

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: alertmanager-config
  namespace: monitoring
data:
  alertmanager.yml: |
    global:
      resolve_timeout: 5m
      slack_api_url: 'https://hooks.slack.com/services/XXX/YYY/ZZZ'
      pagerduty_url: 'https://events.pagerduty.com/v2/enqueue'

    # Inhibit rules - suppress certain alerts based on others
    inhibit_rules:
    - source_match:
        severity: 'critical'
      target_match:
        severity: 'warning'
      equal: ['instance', 'job']

    - source_match:
        alertname: 'InstanceDown'
      target_match_re:
        alertname: '.*'
      equal: ['instance']

    # Route alerts to different receivers
    route:
      receiver: 'default'
      group_by: ['alertname', 'cluster', 'job']
      group_wait: 30s
      group_interval: 5m
      repeat_interval: 12h

      routes:
      # Critical alerts to PagerDuty
      - match:
          severity: critical
        receiver: 'pagerduty'
        continue: true

      # Team-specific routing
      - match:
          team: sre
        receiver: 'sre-slack'
        group_by: ['alertname', 'cluster']
        routes:
        - match:
            severity: critical
          receiver: 'sre-pagerduty'

      - match:
          team: backend
        receiver: 'backend-slack'

      - match:
          team: finops
        receiver: 'finops-email'
        group_wait: 10m
        group_interval: 1h
        repeat_interval: 24h

    # Receivers configuration
    receivers:
    - name: 'default'
      slack_configs:
      - channel: '#alerts'
        title: 'Alert: {{ .GroupLabels.alertname }}'
        text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'

    - name: 'pagerduty'
      pagerduty_configs:
      - service_key: 'YOUR_PAGERDUTY_KEY'
        description: '{{ .GroupLabels.alertname }}'

    - name: 'sre-slack'
      slack_configs:
      - channel: '#sre-alerts'
        title: '[{{ .Status | toUpper }}] {{ .GroupLabels.alertname }}'
        text: |
          {{ range .Alerts }}
          *Alert:* {{ .Labels.alertname }}
          *Severity:* {{ .Labels.severity }}
          *Summary:* {{ .Annotations.summary }}
          *Description:* {{ .Annotations.description }}
          *Runbook:* {{ .Annotations.runbook }}
          {{ end }}

    - name: 'sre-pagerduty'
      pagerduty_configs:
      - routing_key: 'SRE_PAGERDUTY_KEY'
        severity: '{{ .GroupLabels.severity }}'

    - name: 'backend-slack'
      slack_configs:
      - channel: '#backend-alerts'

    - name: 'finops-email'
      email_configs:
      - to: 'finops@company.com'
        from: 'alerts@company.com'
        smarthost: 'smtp.company.com:587'
        auth_username: 'alerts@company.com'
        auth_password: 'password'
```

### AlertManager Deployment

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: alertmanager
  namespace: monitoring
spec:
  serviceName: alertmanager
  replicas: 3
  selector:
    matchLabels:
      app: alertmanager
  template:
    metadata:
      labels:
        app: alertmanager
    spec:
      containers:
      - name: alertmanager
        image: prom/alertmanager:v0.26.0
        args:
        - --config.file=/etc/alertmanager/alertmanager.yml
        - --storage.path=/alertmanager
        - --cluster.listen-address=0.0.0.0:9094
        - --cluster.peer=alertmanager-0.alertmanager:9094
        - --cluster.peer=alertmanager-1.alertmanager:9094
        - --cluster.peer=alertmanager-2.alertmanager:9094
        - --web.external-url=https://alertmanager.company.com
        ports:
        - containerPort: 9093
          name: http
        - containerPort: 9094
          name: cluster
        volumeMounts:
        - name: config
          mountPath: /etc/alertmanager
        - name: data
          mountPath: /alertmanager
        resources:
          requests:
            memory: 256Mi
            cpu: 100m
          limits:
            memory: 512Mi
            cpu: 200m
      volumes:
      - name: config
        configMap:
          name: alertmanager-config
  volumeClaimTemplates:
  - metadata:
      name: data
    spec:
      accessModes: ["ReadWriteOnce"]
      storageClassName: fast-ssd
      resources:
        requests:
          storage: 10Gi

---
apiVersion: v1
kind: Service
metadata:
  name: alertmanager
  namespace: monitoring
spec:
  type: ClusterIP
  clusterIP: None
  ports:
  - port: 9093
    targetPort: 9093
    name: http
  - port: 9094
    targetPort: 9094
    name: cluster
  selector:
    app: alertmanager
```

## High Availability and Deduplication

### Ruler HA Configuration

```yaml
ha_ruler_setup:
  multiple_replicas:
    replicas: 2
    description: "Run multiple ruler instances for HA"
    behavior:
      - "Each replica evaluates all rules"
      - "Each replica sends alerts to AlertManager"
      - "AlertManager deduplicates identical alerts"

  alert_deduplication:
    mechanism: "AlertManager clustering"
    labels_to_drop:
      - "ruler_replica"  # Drop replica label so alerts deduplicate
    configuration:
      ruler: "--alert.label-drop=ruler_replica"
      alertmanager: "Cluster gossip protocol"

  external_labels:
    description: "Labels added to all ruler alerts"
    recommended:
      - "ruler_cluster: production"
      - "ruler_replica: $(POD_NAME)"
    usage: "Identify alert source and enable deduplication"
```

### AlertManager Clustering

```yaml
alertmanager_ha:
  cluster_mode:
    description: "AlertManager instances form gossip cluster"
    replicas: 3
    peer_discovery:
      - "alertmanager-0.alertmanager:9094"
      - "alertmanager-1.alertmanager:9094"
      - "alertmanager-2.alertmanager:9094"

  deduplication:
    window: "Based on group_wait and group_interval"
    algorithm: "Alerts with same labels are deduplicated"

  notification_distribution:
    behavior: "Only one instance sends notification"
    mechanism: "Consistent hashing across cluster"
```

## Monitoring Ruler

### Ruler Metrics

```promql
# Rule evaluation duration
prometheus_rule_group_last_duration_seconds

# Rule evaluation lag
prometheus_rule_group_last_duration_seconds
/ prometheus_rule_group_interval_seconds

# Rule evaluation failures
rate(prometheus_rule_evaluation_failures_total[5m])

# Alerts firing
sum by (alertname) (ALERTS{alertstate="firing"})

# Alert send failures
rate(thanos_alert_sender_errors_total[5m])

# Ruler write to object storage
rate(thanos_objstore_bucket_operations_total{component="rule"}[5m])
```

### Ruler Alerting

```yaml
groups:
- name: thanos-ruler
  rules:
  - alert: ThanosRulerQueueIsFull
    expr: |
      prometheus_rule_group_last_duration_seconds
      / prometheus_rule_group_interval_seconds > 1
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "Thanos Ruler is falling behind in rule evaluation"

  - alert: ThanosRulerHighRuleEvaluationFailures
    expr: |
      rate(prometheus_rule_evaluation_failures_total[5m]) > 0.01
    for: 15m
    labels:
      severity: warning
    annotations:
      summary: "Thanos Ruler has high rule evaluation failure rate"

  - alert: ThanosRulerSendAlertsFailure
    expr: rate(thanos_alert_sender_errors_total[5m]) > 0.01
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "Thanos Ruler cannot send alerts to AlertManager"
```

This comprehensive guide provides production-ready configurations for implementing global alerting and recording rules with Thanos Ruler and AlertManager integration.
