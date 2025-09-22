# Kubernetes Multi-cluster Management

**Multi-cluster Management** enables organizations to operate and manage multiple Kubernetes clusters across different environments, regions, and cloud providers while maintaining consistent policies, security, and observability.

## Multi-cluster Architectures

### Architecture Patterns

#### Hub and Spoke Model
```yaml
# Hub cluster configuration
apiVersion: v1
kind: ConfigMap
metadata:
  name: cluster-registry
  namespace: fleet-system
data:
  clusters.yaml: |
    clusters:
      - name: prod-us-east
        endpoint: https://prod-us-east.k8s.company.com
        region: us-east-1
        environment: production
        provider: aws
      - name: prod-eu-west
        endpoint: https://prod-eu-west.k8s.company.com
        region: eu-west-1
        environment: production
        provider: aws
      - name: staging-us-west
        endpoint: https://staging-us-west.k8s.company.com
        region: us-west-2
        environment: staging
        provider: aws
```

#### Mesh Architecture
```yaml
# Cross-cluster service discovery
apiVersion: networking.istio.io/v1alpha3
kind: ServiceEntry
metadata:
  name: remote-service
  namespace: production
spec:
  hosts:
  - remote-api.prod.svc.cluster.local
  location: MESH_EXTERNAL
  ports:
  - number: 443
    name: https
    protocol: HTTPS
  resolution: DNS
  addresses:
  - 240.0.0.1
  endpoints:
  - address: remote-api.cluster2.company.com
    ports:
      https: 443
```

#### Federation Model
```yaml
# Cluster federation configuration
apiVersion: core.federation.k8s.io/v1beta1
kind: FederatedDeployment
metadata:
  name: nginx-deployment
  namespace: default
spec:
  template:
    metadata:
      labels:
        app: nginx
    spec:
      replicas: 3
      selector:
        matchLabels:
          app: nginx
      template:
        metadata:
          labels:
            app: nginx
        spec:
          containers:
          - name: nginx
            image: nginx:1.21
            ports:
            - containerPort: 80
  placement:
    clusters:
    - name: cluster1
    - name: cluster2
  overrides:
  - clusterName: cluster1
    clusterOverrides:
    - path: "/spec/replicas"
      value: 5
  - clusterName: cluster2
    clusterOverrides:
    - path: "/spec/replicas"
      value: 2
```

## Cross-cluster Communication

### Service Mesh Integration

#### Istio Multi-cluster Setup
```bash
# Install Istio on primary cluster
istioctl install --set values.pilot.env.EXTERNAL_ISTIOD=true

# Create cross-cluster secret
kubectl create secret generic cacerts -n istio-system \
  --from-file=root-cert.pem \
  --from-file=cert-chain.pem \
  --from-file=ca-cert.pem \
  --from-file=ca-key.pem

# Expose Istio control plane
kubectl apply -f - <<EOF
apiVersion: networking.istio.io/v1alpha3
kind: Gateway
metadata:
  name: istiod-gateway
  namespace: istio-system
spec:
  selector:
    istio: eastwestgateway
  servers:
  - port:
      number: 15011
      name: tls
      protocol: TLS
    tls:
      mode: PASSTHROUGH
    hosts:
    - "*"
EOF
```

#### Cross-cluster Service Configuration
```yaml
# Primary cluster service export
apiVersion: networking.istio.io/v1alpha3
kind: ServiceEntry
metadata:
  name: cross-cluster-service
spec:
  hosts:
  - api.remote.local
  location: MESH_EXTERNAL
  ports:
  - number: 80
    name: http
    protocol: HTTP
  resolution: DNS
  addresses:
  - 240.0.0.10
  endpoints:
  - address: api-service.default.svc.cluster.local
    network: network1
    ports:
      http: 80

---
# Destination rule for cross-cluster traffic
apiVersion: networking.istio.io/v1alpha3
kind: DestinationRule
metadata:
  name: cross-cluster-dr
spec:
  host: api.remote.local
  trafficPolicy:
    connectionPool:
      tcp:
        maxConnections: 100
      http:
        http1MaxPendingRequests: 50
        maxRequestsPerConnection: 10
    loadBalancer:
      simple: LEAST_CONN
    circuitBreaker:
      consecutiveErrors: 3
      interval: 30s
      baseEjectionTime: 30s
```

### Network Connectivity

#### VPN Gateway Configuration
```yaml
# AWS VPC peering for cross-cluster communication
apiVersion: v1
kind: ConfigMap
metadata:
  name: aws-vpc-config
data:
  setup.sh: |
    #!/bin/bash

    # Create VPC peering connection
    aws ec2 create-vpc-peering-connection \
      --vpc-id vpc-12345 \
      --peer-vpc-id vpc-67890 \
      --peer-region us-west-2

    # Accept peering connection
    aws ec2 accept-vpc-peering-connection \
      --vpc-peering-connection-id pcx-abcdef \
      --region us-west-2

    # Update route tables
    aws ec2 create-route \
      --route-table-id rtb-12345 \
      --destination-cidr-block 10.1.0.0/16 \
      --vpc-peering-connection-id pcx-abcdef
```

#### Load Balancer Cross-cluster
```yaml
# Global load balancer configuration
apiVersion: v1
kind: Service
metadata:
  name: global-load-balancer
  annotations:
    service.beta.kubernetes.io/aws-load-balancer-type: "nlb"
    service.beta.kubernetes.io/aws-load-balancer-cross-zone-load-balancing-enabled: "true"
    service.beta.kubernetes.io/aws-load-balancer-backend-protocol: "tcp"
spec:
  type: LoadBalancer
  selector:
    app: frontend
  ports:
  - port: 80
    targetPort: 8080
    protocol: TCP

---
# Health check configuration
apiVersion: v1
kind: ConfigMap
metadata:
  name: health-check-config
data:
  config.yaml: |
    health_checks:
      - name: cluster1-health
        endpoint: "https://cluster1.company.com/health"
        interval: 30s
        timeout: 5s
        healthy_threshold: 2
        unhealthy_threshold: 3
      - name: cluster2-health
        endpoint: "https://cluster2.company.com/health"
        interval: 30s
        timeout: 5s
        healthy_threshold: 2
        unhealthy_threshold: 3
```

## Cluster Federation Tools

### Rancher Multi-cluster Management

#### Rancher Installation
```bash
# Install Rancher using Helm
helm repo add rancher-latest https://releases.rancher.com/server-charts/latest
kubectl create namespace cattle-system

# Install cert-manager
kubectl apply --validate=false -f https://github.com/jetstack/cert-manager/releases/download/v1.5.1/cert-manager.crds.yaml
helm repo add jetstack https://charts.jetstack.io
helm install cert-manager jetstack/cert-manager \
  --namespace cert-manager \
  --create-namespace \
  --version v1.5.1

# Install Rancher
helm install rancher rancher-latest/rancher \
  --namespace cattle-system \
  --set hostname=rancher.company.com \
  --set bootstrapPassword=admin
```

#### Cluster Registration
```yaml
# Cluster registration manifest
apiVersion: management.cattle.io/v3
kind: Cluster
metadata:
  name: production-east
spec:
  displayName: "Production East"
  description: "Production cluster in US East"
  amazonElasticContainerServiceConfig:
    region: "us-east-1"
    kubernetesVersion: "1.21"
    nodeGroups:
    - name: "worker-nodes"
      instanceType: "m5.large"
      desiredCapacity: 3
      minSize: 1
      maxSize: 10
      diskSize: 20
      amiType: "AL2_x86_64"
  enableClusterMonitoring: true
  enableNetworkPolicy: true
```

### Admiral for Multi-cluster Service Mesh

#### Admiral Installation
```bash
# Install Admiral
kubectl create namespace admiral-system
kubectl apply -f https://github.com/istio-ecosystem/admiral/releases/download/v1.0/admiral.yaml

# Configure Admiral
kubectl apply -f - <<EOF
apiVersion: v1
kind: ConfigMap
metadata:
  name: admiral-config
  namespace: admiral-system
data:
  config.yaml: |
    admiral:
      clusters:
        cluster1:
          k8sConfigPath: /etc/admiral/cluster1/config
        cluster2:
          k8sConfigPath: /etc/admiral/cluster2/config
      dependencyNamespaceInjectionLabel: admiral.io/inject
      workloadIdentityKey: identity
      globalTrafficDeploymentLabel: admiral.io/ignore
EOF
```

#### Global Traffic Policy
```yaml
# Global traffic routing
apiVersion: admiral.io/v1alpha1
kind: GlobalTrafficPolicy
metadata:
  name: payment-service-gtp
spec:
  policy:
  - dns: payment.global
    match:
    - headers:
        region:
          exact: "us-east"
    route:
    - cluster: "cluster-east"
      weight: 100
  - dns: payment.global
    match:
    - headers:
        region:
          exact: "eu-west"
    route:
    - cluster: "cluster-europe"
      weight: 100
  - dns: payment.global
    route:
    - cluster: "cluster-east"
      weight: 50
    - cluster: "cluster-europe"
      weight: 50
```

### Anthos Multi-cluster Management

#### Anthos Configuration
```yaml
# Anthos cluster configuration
apiVersion: gke.io/v1
kind: Cluster
metadata:
  name: prod-cluster-1
spec:
  type: gke
  projectID: my-project-id
  location: us-central1-a
  initialNodeCount: 3
  machineType: n1-standard-4
  enableNetworkPolicy: true
  enableIPAlias: true
  masterAuth:
    username: ""
    password: ""
    clientCertificateConfig:
      issueClientCertificate: false

---
# Multi-cluster ingress
apiVersion: networking.gke.io/v1
kind: MultiClusterIngress
metadata:
  name: global-ingress
  annotations:
    networking.gke.io/static-ip: global-web-ip
spec:
  template:
    spec:
      backend:
        serviceName: web-service
        servicePort: 80
      rules:
      - host: app.company.com
        http:
          paths:
          - path: /api/*
            backend:
              serviceName: api-service
              servicePort: 80
          - path: /*
            backend:
              serviceName: web-service
              servicePort: 80
```

## Policy Management

### Open Policy Agent (OPA) Gatekeeper

#### Cluster-wide Policy Configuration
```yaml
# Constraint template for security policies
apiVersion: templates.gatekeeper.sh/v1beta1
kind: ConstraintTemplate
metadata:
  name: k8srequiredsecuritycontext
spec:
  crd:
    spec:
      names:
        kind: K8sRequiredSecurityContext
      validation:
        type: object
        properties:
          runAsNonRoot:
            type: boolean
          runAsUser:
            type: integer
          fsGroup:
            type: integer
  targets:
    - target: admission.k8s.gatekeeper.sh
      rego: |
        package k8srequiredsecuritycontext

        violation[{"msg": msg}] {
          container := input.review.object.spec.containers[_]
          not container.securityContext.runAsNonRoot
          msg := "Container must run as non-root user"
        }

        violation[{"msg": msg}] {
          not input.review.object.spec.securityContext.fsGroup
          msg := "Pod must specify fsGroup"
        }

---
# Apply security constraint across clusters
apiVersion: constraints.gatekeeper.sh/v1beta1
kind: K8sRequiredSecurityContext
metadata:
  name: security-context-constraint
spec:
  match:
    kinds:
      - apiGroups: [""]
        kinds: ["Pod"]
    namespaces: ["production", "staging"]
  parameters:
    runAsNonRoot: true
    runAsUser: 1000
    fsGroup: 2000
```

#### Config Sync for Policy Distribution
```yaml
# Config Sync configuration
apiVersion: configsync.gke.io/v1beta1
kind: RootSync
metadata:
  name: root-sync
  namespace: config-management-system
spec:
  sourceFormat: unstructured
  git:
    repo: https://github.com/company/k8s-config
    branch: main
    dir: clusters
    auth: none
    period: 30s

---
# Namespace sync configuration
apiVersion: configsync.gke.io/v1beta1
kind: RepoSync
metadata:
  name: repo-sync
  namespace: production
spec:
  sourceFormat: unstructured
  git:
    repo: https://github.com/company/production-config
    branch: main
    dir: manifests
    auth: none
    period: 15s
```

### Falco Security Monitoring

#### Multi-cluster Falco Deployment
```yaml
# Falco DaemonSet for security monitoring
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: falco
  namespace: falco-system
spec:
  selector:
    matchLabels:
      app: falco
  template:
    metadata:
      labels:
        app: falco
    spec:
      serviceAccountName: falco
      hostNetwork: true
      hostPID: true
      containers:
      - name: falco
        image: falcosecurity/falco:latest
        securityContext:
          privileged: true
        volumeMounts:
        - name: dev
          mountPath: /host/dev
        - name: proc
          mountPath: /host/proc
        - name: boot
          mountPath: /host/boot
        - name: modules
          mountPath: /host/lib/modules
        - name: usr
          mountPath: /host/usr
        - name: etc
          mountPath: /host/etc
        env:
        - name: FALCO_GRPC_ENABLED
          value: "true"
        - name: FALCO_GRPC_BIND_ADDRESS
          value: "0.0.0.0:5060"
      volumes:
      - name: dev
        hostPath:
          path: /dev
      - name: proc
        hostPath:
          path: /proc
      - name: boot
        hostPath:
          path: /boot
      - name: modules
        hostPath:
          path: /lib/modules
      - name: usr
        hostPath:
          path: /usr
      - name: etc
        hostPath:
          path: /etc
```

## GitOps Multi-cluster Deployment

### ArgoCD Multi-cluster Setup

#### ArgoCD Installation and Configuration
```bash
# Install ArgoCD
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# Add external clusters
argocd cluster add cluster1-context
argocd cluster add cluster2-context

# Create application sets for multi-cluster deployment
kubectl apply -f - <<EOF
apiVersion: argoproj.io/v1alpha1
kind: ApplicationSet
metadata:
  name: multi-cluster-apps
  namespace: argocd
spec:
  generators:
  - clusters: {}
  template:
    metadata:
      name: '{{name}}-nginx'
    spec:
      project: default
      source:
        repoURL: https://github.com/company/k8s-manifests
        targetRevision: HEAD
        path: nginx
      destination:
        server: '{{server}}'
        namespace: default
      syncPolicy:
        automated:
          prune: true
          selfHeal: true
        syncOptions:
        - CreateNamespace=true
EOF
```

#### Application Set for Multi-environment
```yaml
# Environment-specific application set
apiVersion: argoproj.io/v1alpha1
kind: ApplicationSet
metadata:
  name: env-specific-apps
  namespace: argocd
spec:
  generators:
  - list:
      elements:
      - cluster: prod-us-east
        url: https://kubernetes.prod-us-east.company.com
        env: production
        region: us-east-1
      - cluster: prod-eu-west
        url: https://kubernetes.prod-eu-west.company.com
        env: production
        region: eu-west-1
      - cluster: staging-us-west
        url: https://kubernetes.staging-us-west.company.com
        env: staging
        region: us-west-2
  template:
    metadata:
      name: '{{cluster}}-app'
    spec:
      project: default
      source:
        repoURL: https://github.com/company/app-manifests
        targetRevision: HEAD
        path: overlays/{{env}}
      destination:
        server: '{{url}}'
        namespace: '{{env}}'
      syncPolicy:
        automated:
          prune: true
          selfHeal: true
        syncOptions:
        - CreateNamespace=true
      ignoreDifferences:
      - group: apps
        kind: Deployment
        jsonPointers:
        - /spec/replicas
```

### Flux Multi-cluster Configuration

#### Flux Bootstrap
```bash
# Bootstrap Flux on management cluster
flux bootstrap github \
  --owner=company \
  --repository=fleet-infra \
  --branch=main \
  --path=./clusters/management

# Create cluster definitions
mkdir -p clusters/production clusters/staging

# Production cluster configuration
cat > clusters/production/cluster.yaml <<EOF
apiVersion: gitops.toolkit.fluxcd.io/v1beta1
kind: GitRepository
metadata:
  name: production-cluster
  namespace: flux-system
spec:
  interval: 30s
  ref:
    branch: main
  url: https://github.com/company/production-cluster
---
apiVersion: kustomize.toolkit.fluxcd.io/v1beta2
kind: Kustomization
metadata:
  name: production-cluster
  namespace: flux-system
spec:
  interval: 10m
  sourceRef:
    kind: GitRepository
    name: production-cluster
  path: "./manifests"
  prune: true
  validation: client
EOF
```

## Monitoring and Observability

### Prometheus Federation

#### Prometheus Federation Configuration
```yaml
# Global Prometheus configuration
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "rules/*.yml"

scrape_configs:
  # Federate from cluster Prometheus instances
  - job_name: 'federate'
    scrape_interval: 15s
    honor_labels: true
    metrics_path: '/federate'
    params:
      'match[]':
        - '{job="kubernetes-apiservers"}'
        - '{job="kubernetes-nodes"}'
        - '{job="kubernetes-pods"}'
        - '{__name__=~"cluster:.*"}'
    static_configs:
      - targets:
        - 'prometheus.cluster1.company.com:9090'
        - 'prometheus.cluster2.company.com:9090'
        - 'prometheus.cluster3.company.com:9090'

  # Direct scraping of cluster metrics
  - job_name: 'cluster-health'
    static_configs:
      - targets:
        - 'api.cluster1.company.com:6443'
        - 'api.cluster2.company.com:6443'
        - 'api.cluster3.company.com:6443'
    metrics_path: '/livez'
    scheme: https
    tls_config:
      insecure_skip_verify: true

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager.monitoring.svc.cluster.local:9093
```

#### Multi-cluster Grafana Dashboard
```yaml
# Grafana configuration for multi-cluster view
apiVersion: v1
kind: ConfigMap
metadata:
  name: grafana-dashboard-multicluster
data:
  multicluster.json: |
    {
      "dashboard": {
        "title": "Multi-cluster Overview",
        "tags": ["kubernetes", "multicluster"],
        "panels": [
          {
            "title": "Cluster Health Status",
            "type": "stat",
            "targets": [
              {
                "expr": "up{job=\"cluster-health\"}",
                "legendFormat": "{{instance}}"
              }
            ],
            "fieldConfig": {
              "defaults": {
                "color": {
                  "mode": "thresholds"
                },
                "thresholds": {
                  "steps": [
                    {"color": "red", "value": 0},
                    {"color": "green", "value": 1}
                  ]
                }
              }
            }
          },
          {
            "title": "Cross-cluster Network Latency",
            "type": "graph",
            "targets": [
              {
                "expr": "histogram_quantile(0.95, rate(istio_request_duration_milliseconds_bucket{source_cluster!=\"unknown\",destination_cluster!=\"unknown\"}[5m]))",
                "legendFormat": "{{source_cluster}} -> {{destination_cluster}}"
              }
            ]
          }
        ]
      }
    }
```

### Distributed Tracing

#### Jaeger Multi-cluster Setup
```yaml
# Jaeger collector configuration
apiVersion: apps/v1
kind: Deployment
metadata:
  name: jaeger-collector
  namespace: observability
spec:
  replicas: 3
  selector:
    matchLabels:
      app: jaeger-collector
  template:
    metadata:
      labels:
        app: jaeger-collector
    spec:
      containers:
      - name: jaeger-collector
        image: jaegertracing/jaeger-collector:latest
        env:
        - name: SPAN_STORAGE_TYPE
          value: elasticsearch
        - name: ES_SERVER_URLS
          value: http://elasticsearch:9200
        - name: ES_USERNAME
          value: elastic
        - name: ES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: elasticsearch-credentials
              key: password
        - name: COLLECTOR_OTLP_ENABLED
          value: "true"
        ports:
        - containerPort: 14250
          name: grpc
        - containerPort: 14268
          name: http
        - containerPort: 4317
          name: otlp-grpc
        - containerPort: 4318
          name: otlp-http

---
# OpenTelemetry collector for multi-cluster
apiVersion: opentelemetry.io/v1alpha1
kind: OpenTelemetryCollector
metadata:
  name: multi-cluster-collector
spec:
  config: |
    receivers:
      otlp:
        protocols:
          grpc:
            endpoint: 0.0.0.0:4317
          http:
            endpoint: 0.0.0.0:4318
      jaeger:
        protocols:
          grpc:
            endpoint: 0.0.0.0:14250

    processors:
      batch:
      resource:
        attributes:
          - key: cluster.name
            value: "${CLUSTER_NAME}"
            action: upsert

    exporters:
      jaeger:
        endpoint: jaeger-collector.observability.svc.cluster.local:14250
        tls:
          insecure: true
      logging:
        loglevel: debug

    service:
      pipelines:
        traces:
          receivers: [otlp, jaeger]
          processors: [resource, batch]
          exporters: [jaeger]
```

## Disaster Recovery

### Backup and Restore Strategy

#### Velero Multi-cluster Backup
```bash
# Install Velero on each cluster
velero install \
  --provider aws \
  --plugins velero/velero-plugin-for-aws:v1.2.1 \
  --bucket velero-backup-company \
  --backup-location-config region=us-west-2 \
  --snapshot-location-config region=us-west-2

# Create backup schedule for critical resources
kubectl apply -f - <<EOF
apiVersion: velero.io/v1
kind: Schedule
metadata:
  name: daily-backup
  namespace: velero
spec:
  schedule: "0 2 * * *"
  template:
    includedNamespaces:
    - production
    - staging
    - default
    excludedResources:
    - events
    - events.events.k8s.io
    storageLocation: default
    volumeSnapshotLocations:
    - default
    ttl: 720h
EOF
```

#### Cross-cluster Restore Script
```bash
#!/bin/bash
# Multi-cluster disaster recovery script

BACKUP_NAME="$1"
TARGET_CLUSTER="$2"
SOURCE_CLUSTER="$3"

if [[ -z "$BACKUP_NAME" || -z "$TARGET_CLUSTER" ]]; then
    echo "Usage: $0 <backup_name> <target_cluster> [source_cluster]"
    exit 1
fi

echo "Starting disaster recovery process..."
echo "Backup: $BACKUP_NAME"
echo "Target cluster: $TARGET_CLUSTER"

# Switch to target cluster context
kubectl config use-context "$TARGET_CLUSTER"

# Verify Velero is installed
if ! kubectl get ns velero >/dev/null 2>&1; then
    echo "ERROR: Velero not found on target cluster"
    exit 1
fi

# List available backups
echo "Available backups:"
velero backup get

# Create restore
echo "Creating restore from backup: $BACKUP_NAME"
velero restore create "${BACKUP_NAME}-restore-$(date +%Y%m%d-%H%M%S)" \
  --from-backup "$BACKUP_NAME" \
  --wait

# Verify restore status
echo "Restore status:"
velero restore get

# Check pod status in restored namespaces
echo "Checking pod status in restored namespaces:"
for ns in production staging default; do
    if kubectl get ns "$ns" >/dev/null 2>&1; then
        echo "Namespace: $ns"
        kubectl get pods -n "$ns" --no-headers | wc -l | xargs echo "  Pods:"
        kubectl get pods -n "$ns" --field-selector=status.phase!=Running --no-headers | wc -l | xargs echo "  Non-running pods:"
    fi
done

echo "Disaster recovery process completed"
```

## Security and Compliance

### Certificate Management

#### cert-manager Multi-cluster Configuration
```yaml
# Cluster issuer for Let's Encrypt
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: admin@company.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - dns01:
        route53:
          region: us-west-2
          accessKeyID: AKIAIOSFODNN7EXAMPLE
          secretAccessKeySecretRef:
            name: route53-credentials
            key: secret-access-key

---
# Certificate for multi-cluster service
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: multi-cluster-tls
  namespace: istio-system
spec:
  secretName: multi-cluster-tls-secret
  issuerRef:
    name: letsencrypt-prod
    kind: ClusterIssuer
  dnsNames:
  - api.company.com
  - "*.cluster1.company.com"
  - "*.cluster2.company.com"
  - "*.cluster3.company.com"
```

#### RBAC Federation
```yaml
# Cluster role for cross-cluster access
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: multi-cluster-admin
rules:
- apiGroups: [""]
  resources: ["*"]
  verbs: ["*"]
- apiGroups: ["apps", "extensions"]
  resources: ["*"]
  verbs: ["*"]
- apiGroups: ["networking.k8s.io"]
  resources: ["*"]
  verbs: ["*"]

---
# Service account for cross-cluster operations
apiVersion: v1
kind: ServiceAccount
metadata:
  name: multi-cluster-sa
  namespace: kube-system

---
# Cluster role binding
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: multi-cluster-binding
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: multi-cluster-admin
subjects:
- kind: ServiceAccount
  name: multi-cluster-sa
  namespace: kube-system
```

## Cost Management

### Resource Optimization

#### Vertical Pod Autoscaler (VPA) Configuration
```yaml
# VPA for multi-cluster resource optimization
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: webapp-vpa
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: webapp
  updatePolicy:
    updateMode: "Auto"
  resourcePolicy:
    containerPolicies:
    - containerName: webapp
      minAllowed:
        cpu: 100m
        memory: 128Mi
      maxAllowed:
        cpu: 2
        memory: 4Gi
      controlledResources: ["cpu", "memory"]

---
# Horizontal Pod Autoscaler
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: webapp-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: webapp
  minReplicas: 2
  maxReplicas: 50
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
```

#### Cost Monitoring Dashboard
```yaml
# Cost monitoring configuration
apiVersion: v1
kind: ConfigMap
metadata:
  name: cost-monitoring-config
data:
  config.yaml: |
    clusters:
      - name: prod-us-east
        provider: aws
        region: us-east-1
        cost_allocation_tags:
          - Environment
          - Team
          - Application
      - name: prod-eu-west
        provider: aws
        region: eu-west-1
        cost_allocation_tags:
          - Environment
          - Team
          - Application

    cost_optimization:
      rules:
        - name: underutilized-nodes
          threshold:
            cpu: 20
            memory: 30
          action: recommend_downsize
        - name: oversized-pods
          threshold:
            cpu_request_utilization: 10
            memory_request_utilization: 15
          action: recommend_vpa
```

## Troubleshooting

### Multi-cluster Debugging Tools

#### Cross-cluster Connectivity Test
```bash
#!/bin/bash
# Multi-cluster connectivity test script

CLUSTERS=("cluster1" "cluster2" "cluster3")
TEST_NAMESPACE="connectivity-test"

for cluster in "${CLUSTERS[@]}"; do
    echo "Testing cluster: $cluster"
    kubectl config use-context "$cluster"

    # Create test namespace
    kubectl create namespace "$TEST_NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -

    # Deploy test pod
    kubectl run connectivity-test \
        --image=nicolaka/netshoot \
        --namespace="$TEST_NAMESPACE" \
        --rm -it --restart=Never \
        -- sh -c "
            echo 'Testing DNS resolution...'
            nslookup kubernetes.default.svc.cluster.local

            echo 'Testing external connectivity...'
            curl -s -o /dev/null -w '%{http_code}' https://google.com

            echo 'Testing cross-cluster service...'
            for target_cluster in ${CLUSTERS[@]}; do
                if [ '$cluster' != '\$target_cluster' ]; then
                    echo 'Testing connection to \$target_cluster'
                    # Add specific cross-cluster connectivity tests here
                fi
            done
        "

    # Cleanup
    kubectl delete namespace "$TEST_NAMESPACE" --ignore-not-found=true
done
```

#### Service Mesh Troubleshooting
```yaml
# Istio troubleshooting configuration
apiVersion: install.istio.io/v1alpha1
kind: IstioOperator
metadata:
  name: troubleshooting-config
spec:
  values:
    pilot:
      env:
        PILOT_ENABLE_WORKLOAD_ENTRY_AUTOREGISTRATION: true
        PILOT_ENABLE_CROSS_CLUSTER_WORKLOAD_ENTRY: true
        EXTERNAL_ISTIOD: true
    global:
      logging:
        level: "default:debug"
      proxy:
        logLevel: debug
        componentLogLevel: "misc:error"

---
# Debug service entry
apiVersion: networking.istio.io/v1alpha3
kind: ServiceEntry
metadata:
  name: debug-external
spec:
  hosts:
  - httpbin.org
  ports:
  - number: 80
    name: http
    protocol: HTTP
  location: MESH_EXTERNAL
  resolution: DNS

---
# Virtual service for debugging
apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: debug-routing
spec:
  hosts:
  - httpbin.org
  http:
  - fault:
      delay:
        percentage:
          value: 100.0
        fixedDelay: 5s
    route:
    - destination:
        host: httpbin.org
```