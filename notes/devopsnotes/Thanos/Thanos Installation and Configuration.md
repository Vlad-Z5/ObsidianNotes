# Thanos Installation and Configuration

Complete installation guide, configuration management, and deployment strategies for Thanos across various environments including Kubernetes, Docker, and bare metal deployments.

**Installation Methods:** Helm deployment, Kubernetes manifests, Docker Compose, binary installation, operator-based deployment, development environments, production configuration

## Helm Deployment

### Thanos Helm Chart Installation

```bash
#!/bin/bash
# Thanos Helm Chart Installation Script
# Complete production-ready Thanos deployment using Helm

set -e

# Configuration
NAMESPACE="monitoring"
RELEASE_NAME="thanos"
HELM_CHART_VERSION="12.13.4"
CLUSTER_NAME="production"
STORAGE_TYPE="s3"  # s3, gcs, azure

# Create namespace
kubectl create namespace "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -

# Add Bitnami Helm repository
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update

# Create values file for production deployment
create_helm_values() {
    cat > thanos-values.yaml << EOF
# Global configuration
global:
  imageRegistry: ""
  imagePullSecrets: []
  storageClass: "fast-ssd"

# Object store configuration
objstoreConfig: |
  type: S3
  config:
    bucket: thanos-metrics-storage-${CLUSTER_NAME}
    endpoint: s3.amazonaws.com
    region: us-east-1
    access_key: \${AWS_ACCESS_KEY_ID}
    secret_key: \${AWS_SECRET_ACCESS_KEY}
    insecure: false
    signature_version2: false
    encrypt_sse: true
    put_user_metadata:
      env: production
      cluster: ${CLUSTER_NAME}

# Query configuration
query:
  enabled: true
  replicaCount: 3

  # Resource configuration
  resources:
    requests:
      memory: "1Gi"
      cpu: "500m"
    limits:
      memory: "2Gi"
      cpu: "1000m"

  # Service configuration
  service:
    type: ClusterIP
    ports:
      http: 9090
      grpc: 19090

  # Ingress configuration
  ingress:
    enabled: true
    hostname: thanos-query.company.com
    ingressClassName: nginx
    annotations:
      nginx.ingress.kubernetes.io/rewrite-target: /
      nginx.ingress.kubernetes.io/ssl-redirect: "true"
      cert-manager.io/cluster-issuer: "letsencrypt-prod"
    tls: true

  # Query configuration
  extraFlags:
    - --query.replica-label=replica
    - --query.replica-label=prometheus_replica
    - --query.auto-downsampling
    - --query.partial-response
    - --query.max-concurrent=20
    - --query.timeout=2m
    - --query.lookback-delta=5m
    - --query.max-concurrent-select=4

  # Store endpoints
  stores:
    - thanos-storegateway:19090
    - thanos-ruler:19090

  # Service discovery for sidecars
  sdConfig: |
    - targets:
      - prometheus-0.monitoring.svc.cluster.local:19090
      - prometheus-1.monitoring.svc.cluster.local:19090

# Query Frontend configuration
queryFrontend:
  enabled: true
  replicaCount: 2

  resources:
    requests:
      memory: "512Mi"
      cpu: "500m"
    limits:
      memory: "1Gi"
      cpu: "1000m"

  service:
    type: ClusterIP
    ports:
      http: 9090

  ingress:
    enabled: true
    hostname: thanos.company.com
    ingressClassName: nginx
    annotations:
      nginx.ingress.kubernetes.io/rewrite-target: /
      nginx.ingress.kubernetes.io/ssl-redirect: "true"
      cert-manager.io/cluster-issuer: "letsencrypt-prod"
    tls: true

  # Cache configuration
  extraFlags:
    - --query-range.split-interval=12h
    - --query-range.max-retries-per-request=5
    - --query-range.response-cache-max-freshness=1m
    - --cache-compression-type=snappy

  # Redis cache configuration
  config: |
    type: REDIS
    config:
      addr: redis.monitoring.svc.cluster.local:6379
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

# Store Gateway configuration
storegateway:
  enabled: true
  replicaCount: 2

  # Resource configuration
  resources:
    requests:
      memory: "4Gi"
      cpu: "1000m"
    limits:
      memory: "8Gi"
      cpu: "2000m"

  # Persistence configuration
  persistence:
    enabled: true
    size: 100Gi
    storageClass: fast-ssd

  # Service configuration
  service:
    type: ClusterIP
    ports:
      http: 19191
      grpc: 19090

  # Store configuration
  extraFlags:
    - --index-cache-size=2GB
    - --chunk-pool-size=2GB
    - --store.grpc.series-sample-limit=120000
    - --store.grpc.series-max-concurrency=20
    - --sync-block-duration=3m
    - --block-sync-concurrency=20
    - --min-time=-2w
    - --max-time=-1h

# Compactor configuration
compactor:
  enabled: true
  replicaCount: 1  # Only one compactor should run

  # Resource configuration
  resources:
    requests:
      memory: "2Gi"
      cpu: "1000m"
    limits:
      memory: "4Gi"
      cpu: "2000m"

  # Persistence configuration
  persistence:
    enabled: true
    size: 100Gi
    storageClass: fast-ssd

  # Service configuration
  service:
    type: ClusterIP
    ports:
      http: 19191

  # Compaction configuration
  extraFlags:
    - --retention.resolution-raw=30d
    - --retention.resolution-5m=90d
    - --retention.resolution-1h=2y
    - --consistency-delay=30m
    - --compact.concurrency=1
    - --downsample.concurrency=1
    - --deduplication.replica-label=replica
    - --deduplication.replica-label=prometheus_replica

  # Compactor strategy
  strategy:
    type: Recreate

# Ruler configuration
ruler:
  enabled: true
  replicaCount: 2

  # Resource configuration
  resources:
    requests:
      memory: "1Gi"
      cpu: "500m"
    limits:
      memory: "2Gi"
      cpu: "1000m"

  # Persistence configuration
  persistence:
    enabled: true
    size: 10Gi
    storageClass: fast-ssd

  # Service configuration
  service:
    type: ClusterIP
    ports:
      http: 19191
      grpc: 19090

  # Ruler configuration
  extraFlags:
    - --eval-interval=30s
    - --alertmanagers.url=http://alertmanager.monitoring.svc.cluster.local:9093
    - --query=thanos-query:9090
    - --label=ruler_cluster=production
    - --label=ruler_replica=\$(POD_NAME)

  # Rules configuration
  config: |
    groups:
    - name: thanos
      rules:
      - alert: ThanosCompactMultipleRunning
        expr: sum by (job) (up{job=~".*thanos-compact.*"}) > 1
        for: 5m
        annotations:
          description: Multiple Thanos Compact instances running
          summary: Thanos Compact has multiple instances running
        labels:
          severity: warning

# Bucket Web configuration
bucketweb:
  enabled: false  # Optional component
  replicaCount: 1

  service:
    type: ClusterIP
    ports:
      http: 19191

  ingress:
    enabled: true
    hostname: thanos-bucket.company.com
    ingressClassName: nginx
    tls: true

# Receive configuration (for remote write)
receive:
  enabled: false  # Enable if using remote write
  replicaCount: 3

  # Resource configuration
  resources:
    requests:
      memory: "2Gi"
      cpu: "1000m"
    limits:
      memory: "4Gi"
      cpu: "2000m"

  # Persistence configuration
  persistence:
    enabled: true
    size: 50Gi
    storageClass: fast-ssd

  # Service configuration
  service:
    type: ClusterIP
    ports:
      http: 19291
      grpc: 19090
      remote: 19291

  # Receive configuration
  extraFlags:
    - --receive.replication-factor=2
    - --receive.local-endpoint=\$(POD_IP):19090
    - --label=replica=\\"\$(POD_NAME)\\"

# Metrics configuration
metrics:
  enabled: true
  serviceMonitor:
    enabled: true
    interval: 30s
    scrapeTimeout: 30s
    labels:
      app: thanos

# RBAC configuration
rbac:
  create: true

# Service account configuration
serviceAccount:
  create: true
  annotations:
    eks.amazonaws.com/role-arn: arn:aws:iam::123456789012:role/thanos-role

# Security context
podSecurityContext:
  runAsNonRoot: true
  runAsUser: 1001
  fsGroup: 1001

# Network policies
networkPolicy:
  enabled: true
  ingress:
    enabled: true
    from:
    - namespaceSelector:
        matchLabels:
          name: monitoring
  egress:
    enabled: true

# Pod disruption budget
podDisruptionBudget:
  create: true
  minAvailable: 1

# Horizontal Pod Autoscaler
autoscaling:
  enabled: false
  query:
    enabled: false
    minReplicas: 2
    maxReplicas: 10
    targetCPU: 70
    targetMemory: 80
  queryFrontend:
    enabled: false
    minReplicas: 2
    maxReplicas: 5
    targetCPU: 70
    targetMemory: 80
  storegateway:
    enabled: false
    minReplicas: 2
    maxReplicas: 5
    targetCPU: 70
    targetMemory: 80

# Monitoring and alerting
monitoring:
  enabled: true
  serviceMonitor:
    enabled: true
    namespace: monitoring
    interval: 30s
    scrapeTimeout: 30s

# Grafana dashboards
grafanaDashboards:
  enabled: true
  namespace: monitoring
EOF
}

# Create secret for object storage credentials
create_storage_secret() {
    if [[ "$STORAGE_TYPE" == "s3" ]]; then
        kubectl create secret generic thanos-objstore-secret \
            --from-literal=AWS_ACCESS_KEY_ID="$AWS_ACCESS_KEY_ID" \
            --from-literal=AWS_SECRET_ACCESS_KEY="$AWS_SECRET_ACCESS_KEY" \
            --namespace="$NAMESPACE" \
            --dry-run=client -o yaml | kubectl apply -f -
    elif [[ "$STORAGE_TYPE" == "gcs" ]]; then
        kubectl create secret generic thanos-objstore-secret \
            --from-file=google-cloud-key.json="$GCS_SERVICE_ACCOUNT_KEY" \
            --namespace="$NAMESPACE" \
            --dry-run=client -o yaml | kubectl apply -f -
    elif [[ "$STORAGE_TYPE" == "azure" ]]; then
        kubectl create secret generic thanos-objstore-secret \
            --from-literal=AZURE_STORAGE_ACCOUNT="$AZURE_STORAGE_ACCOUNT" \
            --from-literal=AZURE_STORAGE_KEY="$AZURE_STORAGE_KEY" \
            --namespace="$NAMESPACE" \
            --dry-run=client -o yaml | kubectl apply -f -
    fi
}

# Install Thanos using Helm
install_thanos() {
    echo "Installing Thanos using Helm..."

    helm upgrade --install "$RELEASE_NAME" bitnami/thanos \
        --namespace="$NAMESPACE" \
        --version="$HELM_CHART_VERSION" \
        --values=thanos-values.yaml \
        --wait \
        --timeout=10m
}

# Verify installation
verify_installation() {
    echo "Verifying Thanos installation..."

    # Check pods
    kubectl get pods -n "$NAMESPACE" -l app.kubernetes.io/name=thanos

    # Check services
    kubectl get svc -n "$NAMESPACE" -l app.kubernetes.io/name=thanos

    # Check ingress
    kubectl get ingress -n "$NAMESPACE"

    # Test connectivity
    echo "Testing Thanos Query connectivity..."
    kubectl port-forward -n "$NAMESPACE" svc/thanos-query 9090:9090 &
    PF_PID=$!
    sleep 5

    if curl -s http://localhost:9090/-/healthy > /dev/null; then
        echo "✓ Thanos Query is healthy"
    else
        echo "✗ Thanos Query health check failed"
    fi

    kill $PF_PID 2>/dev/null || true
}

# Create monitoring dashboards
create_monitoring_dashboards() {
    cat > thanos-grafana-dashboards.yaml << 'EOF'
apiVersion: v1
kind: ConfigMap
metadata:
  name: thanos-dashboards
  namespace: monitoring
  labels:
    grafana_dashboard: "1"
data:
  thanos-overview.json: |
    {
      "dashboard": {
        "id": null,
        "title": "Thanos Overview",
        "tags": ["thanos"],
        "style": "dark",
        "timezone": "browser",
        "panels": [
          {
            "id": 1,
            "title": "Query Frontend Requests",
            "type": "graph",
            "targets": [
              {
                "expr": "rate(http_requests_total{job=~\".*thanos-query-frontend.*\"}[5m])",
                "legendFormat": "{{instance}} - {{handler}}"
              }
            ],
            "xAxis": {"show": true},
            "yAxes": [{"show": true}],
            "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0}
          },
          {
            "id": 2,
            "title": "Store Gateway Series",
            "type": "graph",
            "targets": [
              {
                "expr": "thanos_bucket_store_series_blocks_queried",
                "legendFormat": "{{instance}}"
              }
            ],
            "xAxis": {"show": true},
            "yAxes": [{"show": true}],
            "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0}
          },
          {
            "id": 3,
            "title": "Compactor Progress",
            "type": "graph",
            "targets": [
              {
                "expr": "thanos_compact_group_compactions_total",
                "legendFormat": "{{instance}}"
              }
            ],
            "xAxis": {"show": true},
            "yAxes": [{"show": true}],
            "gridPos": {"h": 8, "w": 12, "x": 0, "y": 8}
          },
          {
            "id": 4,
            "title": "Object Store Operations",
            "type": "graph",
            "targets": [
              {
                "expr": "rate(thanos_objstore_bucket_operations_total[5m])",
                "legendFormat": "{{instance}} - {{operation}}"
              }
            ],
            "xAxis": {"show": true},
            "yAxes": [{"show": true}],
            "gridPos": {"h": 8, "w": 12, "x": 12, "y": 8}
          }
        ],
        "time": {"from": "now-1h", "to": "now"},
        "refresh": "30s"
      }
    }
EOF

    kubectl apply -f thanos-grafana-dashboards.yaml
}

# Main execution
main() {
    echo "Starting Thanos Helm installation..."
    echo "Namespace: $NAMESPACE"
    echo "Release name: $RELEASE_NAME"
    echo "Chart version: $HELM_CHART_VERSION"
    echo "Cluster name: $CLUSTER_NAME"
    echo "Storage type: $STORAGE_TYPE"

    # Validate prerequisites
    if ! command -v helm &> /dev/null; then
        echo "Error: Helm is not installed"
        exit 1
    fi

    if ! command -v kubectl &> /dev/null; then
        echo "Error: kubectl is not installed"
        exit 1
    fi

    # Create configuration
    create_helm_values
    create_storage_secret

    # Install Thanos
    install_thanos

    # Verify installation
    verify_installation

    # Create monitoring dashboards
    create_monitoring_dashboards

    echo ""
    echo "Thanos installation completed successfully!"
    echo ""
    echo "Access URLs:"
    echo "- Thanos Query Frontend: https://thanos.company.com"
    echo "- Thanos Query: https://thanos-query.company.com"
    echo ""
    echo "To access locally:"
    echo "kubectl port-forward -n $NAMESPACE svc/thanos-query-frontend 9090:9090"
    echo ""
    echo "Configuration files:"
    echo "- Helm values: thanos-values.yaml"
    echo "- Grafana dashboards: thanos-grafana-dashboards.yaml"
}

# Execute main function
main "$@"
```

## Kubernetes Manifests

### Manual Kubernetes Deployment

```yaml
# Complete Kubernetes Manifests for Thanos
# Deploy Thanos components manually using kubectl

# Namespace
apiVersion: v1
kind: Namespace
metadata:
  name: monitoring
  labels:
    name: monitoring

---
# Object Store Secret
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
      endpoint: "s3.amazonaws.com"
      region: "us-east-1"
      access_key: "${AWS_ACCESS_KEY_ID}"
      secret_key: "${AWS_SECRET_ACCESS_KEY}"
      insecure: false
      signature_version2: false
      encrypt_sse: true

---
# Service Account
apiVersion: v1
kind: ServiceAccount
metadata:
  name: thanos
  namespace: monitoring
  annotations:
    eks.amazonaws.com/role-arn: arn:aws:iam::123456789012:role/thanos-role

---
# ClusterRole
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: thanos
rules:
- apiGroups: [""]
  resources: ["nodes", "nodes/proxy", "services", "endpoints", "pods"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["extensions"]
  resources: ["ingresses"]
  verbs: ["get", "list", "watch"]

---
# ClusterRoleBinding
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: thanos
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: thanos
subjects:
- kind: ServiceAccount
  name: thanos
  namespace: monitoring

---
# Thanos Query Deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: thanos-query
  namespace: monitoring
  labels:
    app: thanos-query
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
      serviceAccountName: thanos
      containers:
      - name: thanos-query
        image: thanosio/thanos:v0.32.5
        args:
        - query
        - --grpc-address=0.0.0.0:19090
        - --http-address=0.0.0.0:9090
        - --log.level=info
        - --log.format=logfmt
        - --query.replica-label=replica
        - --query.replica-label=prometheus_replica
        - --query.auto-downsampling
        - --query.partial-response
        - --query.max-concurrent=20
        - --query.timeout=2m
        - --query.lookback-delta=5m
        - --query.max-concurrent-select=4
        - --store=thanos-store:19090
        - --store=thanos-ruler:19090
        - --store=dnssrv+_grpc._tcp.thanos-sidecar
        ports:
        - containerPort: 9090
          name: http
        - containerPort: 19090
          name: grpc
        livenessProbe:
          httpGet:
            path: /-/healthy
            port: 9090
          initialDelaySeconds: 30
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /-/ready
            port: 9090
          initialDelaySeconds: 10
          periodSeconds: 5
        resources:
          requests:
            memory: 1Gi
            cpu: 500m
          limits:
            memory: 2Gi
            cpu: 1000m

---
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
  - port: 9090
    targetPort: 9090
    name: http
  - port: 19090
    targetPort: 19090
    name: grpc
  selector:
    app: thanos-query

---
# Thanos Query Frontend Deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: thanos-query-frontend
  namespace: monitoring
  labels:
    app: thanos-query-frontend
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
      serviceAccountName: thanos
      containers:
      - name: thanos-query-frontend
        image: thanosio/thanos:v0.32.5
        args:
        - query-frontend
        - --http-address=0.0.0.0:9090
        - --query-frontend.downstream-url=http://thanos-query:9090
        - --query-frontend.compress-responses
        - --query-range.partial-response
        - --query-range.split-interval=12h
        - --query-range.max-retries-per-request=5
        - --query-range.response-cache-max-freshness=1m
        - --cache-compression-type=snappy
        ports:
        - containerPort: 9090
          name: http
        livenessProbe:
          httpGet:
            path: /-/healthy
            port: 9090
          initialDelaySeconds: 30
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /-/ready
            port: 9090
          initialDelaySeconds: 10
          periodSeconds: 5
        resources:
          requests:
            memory: 512Mi
            cpu: 500m
          limits:
            memory: 1Gi
            cpu: 1000m

---
# Thanos Query Frontend Service
apiVersion: v1
kind: Service
metadata:
  name: thanos-query-frontend
  namespace: monitoring
  labels:
    app: thanos-query-frontend
spec:
  ports:
  - port: 9090
    targetPort: 9090
    name: http
  selector:
    app: thanos-query-frontend

---
# Thanos Store Gateway StatefulSet
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: thanos-store
  namespace: monitoring
  labels:
    app: thanos-store
spec:
  serviceName: thanos-store
  replicas: 2
  selector:
    matchLabels:
      app: thanos-store
  template:
    metadata:
      labels:
        app: thanos-store
    spec:
      serviceAccountName: thanos
      containers:
      - name: thanos-store
        image: thanosio/thanos:v0.32.5
        args:
        - store
        - --grpc-address=0.0.0.0:19090
        - --http-address=0.0.0.0:19191
        - --data-dir=/data
        - --objstore.config-file=/etc/thanos/objstore.yml
        - --log.level=info
        - --log.format=logfmt
        - --index-cache-size=2GB
        - --chunk-pool-size=2GB
        - --store.grpc.series-sample-limit=120000
        - --store.grpc.series-max-concurrency=20
        - --sync-block-duration=3m
        - --block-sync-concurrency=20
        ports:
        - containerPort: 19090
          name: grpc
        - containerPort: 19191
          name: http
        volumeMounts:
        - name: data
          mountPath: /data
        - name: objstore-config
          mountPath: /etc/thanos
        livenessProbe:
          httpGet:
            path: /-/healthy
            port: 19191
          initialDelaySeconds: 30
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /-/ready
            port: 19191
          initialDelaySeconds: 10
          periodSeconds: 5
        resources:
          requests:
            memory: 4Gi
            cpu: 1000m
          limits:
            memory: 8Gi
            cpu: 2000m
      volumes:
      - name: objstore-config
        secret:
          secretName: thanos-objstore-config
  volumeClaimTemplates:
  - metadata:
      name: data
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 100Gi
      storageClassName: fast-ssd

---
# Thanos Store Gateway Service
apiVersion: v1
kind: Service
metadata:
  name: thanos-store
  namespace: monitoring
  labels:
    app: thanos-store
spec:
  ports:
  - port: 19090
    targetPort: 19090
    name: grpc
  - port: 19191
    targetPort: 19191
    name: http
  selector:
    app: thanos-store

---
# Thanos Compactor StatefulSet
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: thanos-compactor
  namespace: monitoring
  labels:
    app: thanos-compactor
spec:
  serviceName: thanos-compactor
  replicas: 1
  selector:
    matchLabels:
      app: thanos-compactor
  template:
    metadata:
      labels:
        app: thanos-compactor
    spec:
      serviceAccountName: thanos
      containers:
      - name: thanos-compactor
        image: thanosio/thanos:v0.32.5
        args:
        - compact
        - --wait
        - --http-address=0.0.0.0:19191
        - --data-dir=/data
        - --objstore.config-file=/etc/thanos/objstore.yml
        - --log.level=info
        - --log.format=logfmt
        - --retention.resolution-raw=30d
        - --retention.resolution-5m=90d
        - --retention.resolution-1h=2y
        - --consistency-delay=30m
        - --compact.concurrency=1
        - --downsample.concurrency=1
        - --deduplication.replica-label=replica
        - --deduplication.replica-label=prometheus_replica
        ports:
        - containerPort: 19191
          name: http
        volumeMounts:
        - name: data
          mountPath: /data
        - name: objstore-config
          mountPath: /etc/thanos
        livenessProbe:
          httpGet:
            path: /-/healthy
            port: 19191
          initialDelaySeconds: 30
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /-/ready
            port: 19191
          initialDelaySeconds: 10
          periodSeconds: 5
        resources:
          requests:
            memory: 2Gi
            cpu: 1000m
          limits:
            memory: 4Gi
            cpu: 2000m
      volumes:
      - name: objstore-config
        secret:
          secretName: thanos-objstore-config
  volumeClaimTemplates:
  - metadata:
      name: data
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 100Gi
      storageClassName: fast-ssd

---
# Thanos Compactor Service
apiVersion: v1
kind: Service
metadata:
  name: thanos-compactor
  namespace: monitoring
  labels:
    app: thanos-compactor
spec:
  ports:
  - port: 19191
    targetPort: 19191
    name: http
  selector:
    app: thanos-compactor

---
# Thanos Ruler StatefulSet
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: thanos-ruler
  namespace: monitoring
  labels:
    app: thanos-ruler
spec:
  serviceName: thanos-ruler
  replicas: 2
  selector:
    matchLabels:
      app: thanos-ruler
  template:
    metadata:
      labels:
        app: thanos-ruler
    spec:
      serviceAccountName: thanos
      containers:
      - name: thanos-ruler
        image: thanosio/thanos:v0.32.5
        args:
        - rule
        - --grpc-address=0.0.0.0:19090
        - --http-address=0.0.0.0:19191
        - --log.level=info
        - --log.format=logfmt
        - --data-dir=/data
        - --eval-interval=30s
        - --rule-file=/etc/thanos/rules/*.yml
        - --objstore.config-file=/etc/thanos/objstore.yml
        - --query=thanos-query:9090
        - --alertmanagers.url=http://alertmanager:9093
        - --label=replica="$(POD_NAME)"
        - --label=ruler_cluster="prod"
        env:
        - name: POD_NAME
          valueFrom:
            fieldRef:
              fieldPath: metadata.name
        ports:
        - containerPort: 19090
          name: grpc
        - containerPort: 19191
          name: http
        volumeMounts:
        - name: data
          mountPath: /data
        - name: objstore-config
          mountPath: /etc/thanos
        - name: rules
          mountPath: /etc/thanos/rules
        livenessProbe:
          httpGet:
            path: /-/healthy
            port: 19191
          initialDelaySeconds: 30
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /-/ready
            port: 19191
          initialDelaySeconds: 10
          periodSeconds: 5
        resources:
          requests:
            memory: 1Gi
            cpu: 500m
          limits:
            memory: 2Gi
            cpu: 1000m
      volumes:
      - name: objstore-config
        secret:
          secretName: thanos-objstore-config
      - name: rules
        configMap:
          name: thanos-ruler-rules
  volumeClaimTemplates:
  - metadata:
      name: data
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 10Gi
      storageClassName: fast-ssd

---
# Thanos Ruler Service
apiVersion: v1
kind: Service
metadata:
  name: thanos-ruler
  namespace: monitoring
  labels:
    app: thanos-ruler
spec:
  ports:
  - port: 19090
    targetPort: 19090
    name: grpc
  - port: 19191
    targetPort: 19191
    name: http
  selector:
    app: thanos-ruler

---
# Ingress for Thanos Query Frontend
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: thanos-query-frontend
  namespace: monitoring
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - thanos.company.com
    secretName: thanos-tls
  rules:
  - host: thanos.company.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: thanos-query-frontend
            port:
              number: 9090

---
# Pod Disruption Budget for Query
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: thanos-query-pdb
  namespace: monitoring
spec:
  minAvailable: 1
  selector:
    matchLabels:
      app: thanos-query

---
# Pod Disruption Budget for Store
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: thanos-store-pdb
  namespace: monitoring
spec:
  minAvailable: 1
  selector:
    matchLabels:
      app: thanos-store

---
# Pod Disruption Budget for Ruler
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

---
# ServiceMonitor for Prometheus Operator
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: thanos
  namespace: monitoring
  labels:
    app: thanos
spec:
  selector:
    matchLabels:
      app: thanos-query
  endpoints:
  - port: http
    interval: 30s
    path: /metrics
---
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: thanos-store
  namespace: monitoring
  labels:
    app: thanos-store
spec:
  selector:
    matchLabels:
      app: thanos-store
  endpoints:
  - port: http
    interval: 30s
    path: /metrics
---
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: thanos-compactor
  namespace: monitoring
  labels:
    app: thanos-compactor
spec:
  selector:
    matchLabels:
      app: thanos-compactor
  endpoints:
  - port: http
    interval: 30s
    path: /metrics
---
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: thanos-ruler
  namespace: monitoring
  labels:
    app: thanos-ruler
spec:
  selector:
    matchLabels:
      app: thanos-ruler
  endpoints:
  - port: http
    interval: 30s
    path: /metrics
```

## Docker Compose Deployment

### Development Environment

```yaml
# docker-compose.yml for Thanos Development Environment
version: '3.8'

services:
  # MinIO for object storage
  minio:
    image: minio/minio:RELEASE.2023-10-25T06-33-25Z
    container_name: thanos-minio
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: minio
      MINIO_ROOT_PASSWORD: minio123
    ports:
      - "9000:9000"
      - "9001:9001"
    volumes:
      - minio-data:/data
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 30s
      timeout: 20s
      retries: 3

  # Create MinIO bucket
  minio-setup:
    image: minio/mc:RELEASE.2023-10-24T21-42-22Z
    container_name: thanos-minio-setup
    depends_on:
      - minio
    entrypoint: >
      /bin/sh -c "
      /usr/bin/mc alias set myminio http://minio:9000 minio minio123;
      /usr/bin/mc mb myminio/thanos-bucket;
      /usr/bin/mc policy set public myminio/thanos-bucket;
      exit 0;
      "

  # Prometheus instance 1
  prometheus-1:
    image: prom/prometheus:v2.45.0
    container_name: thanos-prometheus-1
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--storage.tsdb.retention.time=2h'
      - '--storage.tsdb.min-block-duration=2h'
      - '--storage.tsdb.max-block-duration=2h'
      - '--web.enable-lifecycle'
      - '--storage.tsdb.no-lockfile'
      - '--web.route-prefix=/'
      - '--web.external-url=http://localhost:9091'
    ports:
      - "9091:9090"
    volumes:
      - ./prometheus-1.yml:/etc/prometheus/prometheus.yml
      - prometheus-1-data:/prometheus
    depends_on:
      - minio-setup

  # Thanos Sidecar for Prometheus 1
  thanos-sidecar-1:
    image: thanosio/thanos:v0.32.5
    container_name: thanos-sidecar-1
    command:
      - 'sidecar'
      - '--tsdb.path=/prometheus'
      - '--prometheus.url=http://prometheus-1:9090'
      - '--grpc-address=0.0.0.0:19090'
      - '--http-address=0.0.0.0:19191'
      - '--objstore.config-file=/etc/thanos/bucket.yml'
      - '--log.level=debug'
    ports:
      - "19090:19090"
      - "19191:19191"
    volumes:
      - ./bucket.yml:/etc/thanos/bucket.yml
      - prometheus-1-data:/prometheus
    depends_on:
      - prometheus-1
      - minio-setup

  # Prometheus instance 2
  prometheus-2:
    image: prom/prometheus:v2.45.0
    container_name: thanos-prometheus-2
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--storage.tsdb.retention.time=2h'
      - '--storage.tsdb.min-block-duration=2h'
      - '--storage.tsdb.max-block-duration=2h'
      - '--web.enable-lifecycle'
      - '--storage.tsdb.no-lockfile'
      - '--web.route-prefix=/'
      - '--web.external-url=http://localhost:9092'
    ports:
      - "9092:9090"
    volumes:
      - ./prometheus-2.yml:/etc/prometheus/prometheus.yml
      - prometheus-2-data:/prometheus
    depends_on:
      - minio-setup

  # Thanos Sidecar for Prometheus 2
  thanos-sidecar-2:
    image: thanosio/thanos:v0.32.5
    container_name: thanos-sidecar-2
    command:
      - 'sidecar'
      - '--tsdb.path=/prometheus'
      - '--prometheus.url=http://prometheus-2:9090'
      - '--grpc-address=0.0.0.0:19090'
      - '--http-address=0.0.0.0:19191'
      - '--objstore.config-file=/etc/thanos/bucket.yml'
      - '--log.level=debug'
    ports:
      - "19092:19090"
      - "19193:19191"
    volumes:
      - ./bucket.yml:/etc/thanos/bucket.yml
      - prometheus-2-data:/prometheus
    depends_on:
      - prometheus-2
      - minio-setup

  # Thanos Query
  thanos-query:
    image: thanosio/thanos:v0.32.5
    container_name: thanos-query
    command:
      - 'query'
      - '--grpc-address=0.0.0.0:19090'
      - '--http-address=0.0.0.0:9090'
      - '--log.level=debug'
      - '--query.replica-label=replica'
      - '--store=thanos-sidecar-1:19090'
      - '--store=thanos-sidecar-2:19090'
      - '--store=thanos-store:19090'
      - '--store=thanos-ruler:19090'
    ports:
      - "9090:9090"
      - "19190:19090"
    depends_on:
      - thanos-sidecar-1
      - thanos-sidecar-2

  # Thanos Store Gateway
  thanos-store:
    image: thanosio/thanos:v0.32.5
    container_name: thanos-store
    command:
      - 'store'
      - '--grpc-address=0.0.0.0:19090'
      - '--http-address=0.0.0.0:19191'
      - '--data-dir=/data'
      - '--objstore.config-file=/etc/thanos/bucket.yml'
      - '--log.level=debug'
      - '--index-cache-size=500MB'
      - '--chunk-pool-size=500MB'
    ports:
      - "19094:19090"
      - "19194:19191"
    volumes:
      - ./bucket.yml:/etc/thanos/bucket.yml
      - store-data:/data
    depends_on:
      - minio-setup

  # Thanos Compactor
  thanos-compactor:
    image: thanosio/thanos:v0.32.5
    container_name: thanos-compactor
    command:
      - 'compact'
      - '--wait'
      - '--http-address=0.0.0.0:19191'
      - '--data-dir=/data'
      - '--objstore.config-file=/etc/thanos/bucket.yml'
      - '--log.level=debug'
      - '--retention.resolution-raw=7d'
      - '--retention.resolution-5m=30d'
      - '--retention.resolution-1h=365d'
      - '--consistency-delay=30m'
      - '--compact.concurrency=1'
      - '--deduplication.replica-label=replica'
    ports:
      - "19195:19191"
    volumes:
      - ./bucket.yml:/etc/thanos/bucket.yml
      - compactor-data:/data
    depends_on:
      - minio-setup

  # Thanos Ruler
  thanos-ruler:
    image: thanosio/thanos:v0.32.5
    container_name: thanos-ruler
    command:
      - 'rule'
      - '--grpc-address=0.0.0.0:19090'
      - '--http-address=0.0.0.0:19191'
      - '--log.level=debug'
      - '--data-dir=/data'
      - '--eval-interval=30s'
      - '--rule-file=/etc/thanos/rules/*.yml'
      - '--objstore.config-file=/etc/thanos/bucket.yml'
      - '--query=thanos-query:9090'
      - '--label=ruler_cluster=docker'
    ports:
      - "19096:19090"
      - "19196:19191"
    volumes:
      - ./bucket.yml:/etc/thanos/bucket.yml
      - ./rules:/etc/thanos/rules
      - ruler-data:/data
    depends_on:
      - thanos-query
      - minio-setup

  # Redis for Query Frontend caching
  redis:
    image: redis:7-alpine
    container_name: thanos-redis
    command: redis-server --maxmemory 512mb --maxmemory-policy allkeys-lru
    ports:
      - "6379:6379"

  # Thanos Query Frontend
  thanos-query-frontend:
    image: thanosio/thanos:v0.32.5
    container_name: thanos-query-frontend
    command:
      - 'query-frontend'
      - '--http-address=0.0.0.0:9090'
      - '--query-frontend.downstream-url=http://thanos-query:9090'
      - '--query-frontend.compress-responses'
      - '--query-range.partial-response'
      - '--query-range.split-interval=12h'
      - '--query-range.max-retries-per-request=5'
      - '--query-range.response-cache-max-freshness=1m'
      - '--cache-compression-type=snappy'
      - '--query-range.results-cache-config-file=/etc/thanos/cache.yml'
    ports:
      - "9093:9090"
    volumes:
      - ./cache.yml:/etc/thanos/cache.yml
    depends_on:
      - thanos-query
      - redis

  # Grafana for visualization
  grafana:
    image: grafana/grafana:10.2.0
    container_name: thanos-grafana
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    ports:
      - "3000:3000"
    volumes:
      - grafana-data:/var/lib/grafana
      - ./grafana/provisioning:/etc/grafana/provisioning
    depends_on:
      - thanos-query-frontend

volumes:
  minio-data:
  prometheus-1-data:
  prometheus-2-data:
  store-data:
  compactor-data:
  ruler-data:
  grafana-data:

networks:
  default:
    name: thanos-network
```

### Configuration Files for Docker Compose

```bash
#!/bin/bash
# Create configuration files for Docker Compose Thanos setup

# Create bucket configuration
cat > bucket.yml << 'EOF'
type: S3
config:
  bucket: "thanos-bucket"
  endpoint: "minio:9000"
  access_key: "minio"
  secret_key: "minio123"
  insecure: true
  signature_version2: false
  put_user_metadata: {}
  http_config:
    idle_conn_timeout: 1m30s
    response_header_timeout: 2m
    insecure_skip_verify: false
  trace:
    enable: false
  part_size: 134217728
EOF

# Create Redis cache configuration
cat > cache.yml << 'EOF'
type: REDIS
config:
  addr: "redis:6379"
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
EOF

# Create Prometheus configuration for replica 1
cat > prometheus-1.yml << 'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    cluster: docker
    replica: "1"
    prometheus_replica: "1"

scrape_configs:
- job_name: 'prometheus-1'
  static_configs:
  - targets: ['localhost:9090']

- job_name: 'thanos'
  static_configs:
  - targets:
    - 'thanos-query:9090'
    - 'thanos-sidecar-1:19191'
    - 'thanos-store:19191'
    - 'thanos-compactor:19191'
    - 'thanos-ruler:19191'

- job_name: 'node-exporter'
  static_configs:
  - targets: ['host.docker.internal:9100']

- job_name: 'cadvisor'
  static_configs:
  - targets: ['host.docker.internal:8080']
EOF

# Create Prometheus configuration for replica 2
cat > prometheus-2.yml << 'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    cluster: docker
    replica: "2"
    prometheus_replica: "2"

scrape_configs:
- job_name: 'prometheus-2'
  static_configs:
  - targets: ['localhost:9090']

- job_name: 'thanos'
  static_configs:
  - targets:
    - 'thanos-query:9090'
    - 'thanos-sidecar-2:19191'
    - 'thanos-store:19191'
    - 'thanos-compactor:19191'
    - 'thanos-ruler:19191'

- job_name: 'node-exporter'
  static_configs:
  - targets: ['host.docker.internal:9100']

- job_name: 'cadvisor'
  static_configs:
  - targets: ['host.docker.internal:8080']
EOF

# Create Thanos rules directory and sample rules
mkdir -p rules
cat > rules/thanos.yml << 'EOF'
groups:
- name: thanos
  rules:
  - alert: ThanosCompactMultipleRunning
    expr: sum by (job) (up{job=~".*thanos-compact.*"}) > 1
    for: 5m
    annotations:
      description: Multiple Thanos Compact instances running
      summary: Thanos Compact has multiple instances running
    labels:
      severity: warning

  - alert: ThanosQueryHttpRequestQueryErrorRateHigh
    expr: |
      (
        sum by (job) (rate(http_requests_total{code=~"5..", job=~".*thanos-query.*", handler="query"}[5m]))
      /
        sum by (job) (rate(http_requests_total{job=~".*thanos-query.*", handler="query"}[5m]))
      ) * 100 > 5
    for: 5m
    annotations:
      description: Thanos Query is failing to handle requests
      summary: Thanos Query is failing to handle requests
    labels:
      severity: critical
EOF

# Create Grafana provisioning
mkdir -p grafana/provisioning/datasources
cat > grafana/provisioning/datasources/thanos.yml << 'EOF'
apiVersion: 1

datasources:
- name: Thanos
  type: prometheus
  access: proxy
  url: http://thanos-query-frontend:9090
  isDefault: true
  editable: true

- name: Prometheus-1
  type: prometheus
  access: proxy
  url: http://prometheus-1:9090
  isDefault: false
  editable: true

- name: Prometheus-2
  type: prometheus
  access: proxy
  url: http://prometheus-2:9090
  isDefault: false
  editable: true
EOF

mkdir -p grafana/provisioning/dashboards
cat > grafana/provisioning/dashboards/dashboards.yml << 'EOF'
apiVersion: 1

providers:
- name: 'Thanos'
  orgId: 1
  folder: 'Thanos'
  type: file
  disableDeletion: false
  updateIntervalSeconds: 10
  allowUiUpdates: true
  options:
    path: /etc/grafana/provisioning/dashboards
EOF

echo "Configuration files created successfully!"
echo ""
echo "To start the Thanos development environment:"
echo "docker-compose up -d"
echo ""
echo "Access URLs:"
echo "- Thanos Query Frontend: http://localhost:9093"
echo "- Thanos Query: http://localhost:9090"
echo "- Prometheus 1: http://localhost:9091"
echo "- Prometheus 2: http://localhost:9092"
echo "- Grafana: http://localhost:3000 (admin/admin)"
echo "- MinIO Console: http://localhost:9001 (minio/minio123)"
echo ""
echo "To stop the environment:"
echo "docker-compose down -v"
```

<function_calls>
<invoke name="TodoWrite">
<parameter name="todos">[{"content": "Create Thanos Architecture and Components documentation", "status": "completed", "activeForm": "Creating Thanos Architecture and Components documentation"}, {"content": "Create Thanos Installation and Configuration documentation", "status": "completed", "activeForm": "Creating Thanos Installation and Configuration documentation"}, {"content": "Create Thanos Object Storage documentation", "status": "in_progress", "activeForm": "Creating Thanos Object Storage documentation"}]