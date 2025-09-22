# Kubernetes Production Best Practices

**Production Kubernetes** requires comprehensive planning, security hardening, reliability patterns, and operational excellence to ensure stable, scalable, and secure applications in enterprise environments.

## Resource Management

### Always Set Resource Requests and Limits

```yaml
# Production-ready resource configuration
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-app
  namespace: production
spec:
  template:
    spec:
      containers:
      - name: web-app
        image: app:v1.2.3
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
            ephemeral-storage: "1Gi"
          limits:
            memory: "512Mi"
            cpu: "500m"
            ephemeral-storage: "2Gi"
```

### Resource Quotas and Limits

```yaml
# Namespace resource quota
apiVersion: v1
kind: ResourceQuota
metadata:
  name: production-quota
  namespace: production
spec:
  hard:
    requests.cpu: "10"
    requests.memory: 20Gi
    limits.cpu: "20"
    limits.memory: 40Gi
    persistentvolumeclaims: "10"
    pods: "50"

---
# Limit ranges for defaults
apiVersion: v1
kind: LimitRange
metadata:
  name: production-limits
  namespace: production
spec:
  limits:
  - default:
      cpu: "500m"
      memory: "512Mi"
    defaultRequest:
      cpu: "100m"
      memory: "128Mi"
    type: Container
```

---

## Security Hardening

### Pod Security Standards

```yaml
# Security-hardened deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: secure-app
spec:
  template:
    spec:
      securityContext:
        runAsNonRoot: true
        runAsUser: 10001
        runAsGroup: 10001
        fsGroup: 10001
        seccompProfile:
          type: RuntimeDefault
      containers:
      - name: app
        securityContext:
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true
          runAsNonRoot: true
          runAsUser: 10001
          capabilities:
            drop:
            - ALL
```

### RBAC Configuration

```yaml
# Service account with minimal permissions
apiVersion: v1
kind: ServiceAccount
metadata:
  name: web-app-sa
  namespace: production

---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: production
  name: web-app-role
rules:
- apiGroups: [""]
  resources: ["configmaps", "secrets"]
  verbs: ["get", "list"]

---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: web-app-binding
  namespace: production
subjects:
- kind: ServiceAccount
  name: web-app-sa
roleRef:
  kind: Role
  name: web-app-role
  apiGroup: rbac.authorization.k8s.io
```

---

## High Availability & Reliability

### Pod Disruption Budget

```yaml
# Ensure minimum availability during disruptions
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: web-app-pdb
  namespace: production
spec:
  minAvailable: 2
  selector:
    matchLabels:
      app: web-app
```

### Health Checks

```yaml
# Comprehensive health checks
spec:
  containers:
  - name: app
    livenessProbe:
      httpGet:
        path: /health/live
        port: 8080
      initialDelaySeconds: 30
      periodSeconds: 10
      timeoutSeconds: 5
      failureThreshold: 3
    readinessProbe:
      httpGet:
        path: /health/ready
        port: 8080
      initialDelaySeconds: 5
      periodSeconds: 5
      timeoutSeconds: 3
      failureThreshold: 3
    startupProbe:
      httpGet:
        path: /health/startup
        port: 8080
      initialDelaySeconds: 10
      periodSeconds: 5
      failureThreshold: 30
```

---

## Performance Optimization

### Horizontal Pod Autoscaler

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: web-app-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: web-app
  minReplicas: 3
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

---

## Monitoring & Observability

### Prometheus Monitoring

```yaml
# ServiceMonitor for Prometheus
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: web-app-metrics
  namespace: production
spec:
  selector:
    matchLabels:
      app: web-app
  endpoints:
  - port: metrics
    interval: 30s
    path: /metrics
```

---

## Configuration Management

### Best Practices Checklist

- ✅ Use ConfigMaps for configuration
- ✅ Store secrets in Secret objects
- ✅ Use namespaces for isolation
- ✅ Implement proper RBAC
- ✅ Use specific image tags, avoid `latest`
- ✅ Set resource requests and limits
- ✅ Implement health checks
- ✅ Use Pod Disruption Budgets

---

## Deployment Strategies

### Blue-Green Deployment

```yaml
# Blue-green deployment with Argo Rollouts
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: web-app-rollout
spec:
  replicas: 5
  strategy:
    blueGreen:
      activeService: web-app-active
      previewService: web-app-preview
      autoPromotionEnabled: false
      scaleDownDelaySeconds: 30
  selector:
    matchLabels:
      app: web-app
  template:
    metadata:
      labels:
        app: web-app
    spec:
      containers:
      - name: web-app
        image: app:v1.2.3
```

### Canary Deployment

```yaml
# Canary deployment with traffic splitting
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: web-app-canary
spec:
  replicas: 10
  strategy:
    canary:
      steps:
      - setWeight: 10
      - pause: {duration: 5m}
      - setWeight: 20
      - pause: {duration: 5m}
      - setWeight: 50
      - pause: {duration: 10m}
      - setWeight: 100
```

---

## Operational Excellence

### Backup and Disaster Recovery

```yaml
# Velero backup configuration
apiVersion: velero.io/v1
kind: Schedule
metadata:
  name: production-daily-backup
spec:
  schedule: "0 2 * * *"
  template:
    includedNamespaces:
    - production
    storageLocation: default
    ttl: 168h0m0s
```

### GitOps Workflow

```yaml
# ArgoCD Application
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: web-app-production
  namespace: argocd
spec:
  project: production
  source:
    repoURL: https://github.com/company/k8s-manifests
    targetRevision: HEAD
    path: production/web-app
  destination:
    server: https://kubernetes.default.svc
    namespace: production
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
```

### Production Checklist

#### Security ✅
- [ ] Implement RBAC with least privilege
- [ ] Use Pod Security Standards
- [ ] Enable network policies
- [ ] Scan container images for vulnerabilities
- [ ] Encrypt etcd data at rest

#### Reliability ✅
- [ ] Configure resource requests and limits
- [ ] Implement health checks (liveness, readiness, startup)
- [ ] Set up Pod Disruption Budgets
- [ ] Use multiple replicas for high availability
- [ ] Configure proper restart policies

#### Performance ✅
- [ ] Monitor resource utilization
- [ ] Implement horizontal and vertical autoscaling
- [ ] Optimize container startup times
- [ ] Configure appropriate storage classes
- [ ] Use efficient container images

#### Operations ✅
- [ ] Set up comprehensive monitoring and alerting
- [ ] Implement centralized logging
- [ ] Automate deployments with GitOps
- [ ] Document runbooks and procedures
- [ ] Regular cluster upgrades and maintenance

---

## Cross-References

**Related Documentation:**
- [Kubernetes Security](Kubernetes%20Security.md) - RBAC, network policies, and security contexts
- [Kubernetes Monitoring and Troubleshooting](Kubernetes%20Monitoring%20and%20Troubleshooting.md) - Observability and incident response
- [Kubernetes Autoscaling & Resource Management](Kubernetes%20Autoscaling%20&%20Resource%20Management.md) - Scaling strategies and optimization
- [Kubernetes GitOps & CI-CD](Kubernetes%20GitOps%20&%20CI-CD.md) - Deployment automation and continuous delivery

**Integration Points:**
- **Infrastructure as Code**: Terraform, Pulumi for cluster provisioning
- **Container Security**: Image scanning, runtime protection, and compliance
- **Service Mesh**: Istio, Linkerd for advanced traffic management
- **Observability**: Prometheus, Grafana, Jaeger for comprehensive monitoring
