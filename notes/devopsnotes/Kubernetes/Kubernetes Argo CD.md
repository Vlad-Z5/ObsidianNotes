# Kubernetes Argo CD

**Argo CD** is a declarative, GitOps continuous delivery tool for Kubernetes that automatically monitors Git repositories and applies changes to ensure cluster state matches the desired state defined in Git.


## Core Concepts

### What is Argo CD?

Argo CD is a **declarative GitOps continuous delivery tool** for Kubernetes that continuously monitors Git repositories containing Kubernetes manifests and automatically applies changes to clusters, ensuring the cluster state matches the desired state defined in Git.

### Key Components

- **Application**: Represents a deployment target with source repository and destination cluster/namespace
- **Repository**: Git or Helm repository containing Kubernetes manifests
- **Sync**: Operation to apply changes from Git repository to cluster
- **Project**: Provides logical grouping and access control for applications
- **UI**: Web interface for visualizing applications, sync status, and logs
- **CLI**: Command-line tool for managing Argo CD operations
- **API Server**: Backend service handling requests and sync operations
- **Controller**: Monitors applications and Git repositories for changes
- **Repository Server**: Service responsible for cloning Git repos and generating manifests

### GitOps Benefits

- **Version Control**: Infrastructure configurations tracked in Git with full history
- **Automated Deployment**: Continuous synchronization between Git and cluster state
- **Rollback Capability**: Easy rollback using Git history and Argo CD sync operations
- **Multi-Cluster Support**: Manage deployments across multiple Kubernetes clusters
- **RBAC Integration**: Fine-grained access control using Kubernetes RBAC
- **Audit Trail**: Complete audit trail of all deployment activities

---

## Installation & Setup

### Installation Methods

#### Method 1: Standard Installation

```bash
# Create namespace
kubectl create namespace argocd

# Install Argo CD
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# Wait for pods to be ready
kubectl wait --for=condition=available --timeout=300s deployment/argocd-server -n argocd

# Get initial admin password
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d && echo

# Port forward to access UI
kubectl port-forward svc/argocd-server -n argocd 8080:443
```

#### Method 2: Argo CD Operator

```bash
# Install Argo CD Operator
kubectl create namespace argocd
kubectl apply -f https://raw.githubusercontent.com/argoproj-labs/argocd-operator/master/deploy/service_account.yaml
kubectl apply -f https://raw.githubusercontent.com/argoproj-labs/argocd-operator/master/deploy/role.yaml
kubectl apply -f https://raw.githubusercontent.com/argoproj-labs/argocd-operator/master/deploy/role_binding.yaml
kubectl apply -f https://raw.githubusercontent.com/argoproj-labs/argocd-operator/master/deploy/crds/
kubectl apply -f https://raw.githubusercontent.com/argoproj-labs/argocd-operator/master/deploy/operator.yaml

# Create Argo CD instance
kubectl apply -f - <<EOF
apiVersion: argoproj.io/v1alpha1
kind: ArgoCD
metadata:
  name: example-argocd
  namespace: argocd
spec:
  server:
    replicas: 2
    route:
      enabled: true
  dex:
    enabled: true
  applicationSet:
    enabled: true
  notifications:
    enabled: true
EOF
```

#### Method 3: Helm Installation

```bash
# Add Argo CD Helm repository
helm repo add argo https://argoproj.github.io/argo-helm
helm repo update

# Install with custom values
helm install argocd argo/argo-cd \
  --namespace argocd \
  --create-namespace \
  --values - <<EOF
global:
  image:
    tag: v2.8.4
server:
  replicas: 2
  service:
    type: LoadBalancer
  config:
    url: https://argocd.company.com
  ingress:
    enabled: true
    hosts:
    - argocd.company.com
    tls:
    - secretName: argocd-tls
      hosts:
      - argocd.company.com
repoServer:
  replicas: 2
controller:
  replicas: 1
dex:
  enabled: true
applicationSet:
  enabled: true
notifications:
  enabled: true
EOF
```

### CLI Setup

```bash
# Download and install Argo CD CLI
curl -sSL -o argocd-linux-amd64 https://github.com/argoproj/argo-cd/releases/latest/download/argocd-linux-amd64
sudo install -m 555 argocd-linux-amd64 /usr/local/bin/argocd
rm argocd-linux-amd64

# Login to Argo CD
argocd login localhost:8080 --username admin --password <initial-password> --insecure

# Change admin password
argocd account update-password

# Add repository
argocd repo add https://github.com/company/k8s-manifests --username <username> --password <token>
```

---

## Application Management

### Basic Application Configuration

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: web-application
  namespace: argocd
  labels:
    environment: production
    team: platform
  annotations:
    argocd.argoproj.io/sync-wave: "1"
  finalizers:
    - resources-finalizer.argocd.argoproj.io
spec:
  project: production
  source:
    repoURL: https://github.com/company/k8s-manifests
    targetRevision: HEAD
    path: applications/web-app
  destination:
    server: https://kubernetes.default.svc
    namespace: production
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
      allowEmpty: false
    syncOptions:
    - CreateNamespace=true
    - PrunePropagationPolicy=foreground
    - PruneLast=true
    retry:
      limit: 5
      backoff:
        duration: 5s
        factor: 2
        maxDuration: 3m0s
```

### Helm-Based Application

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: monitoring-stack
  namespace: argocd
spec:
  project: infrastructure
  source:
    repoURL: https://prometheus-community.github.io/helm-charts
    chart: kube-prometheus-stack
    targetRevision: 45.7.1
    helm:
      releaseName: prometheus
      values: |
        prometheus:
          prometheusSpec:
            retention: 30d
            storageSpec:
              volumeClaimTemplate:
                spec:
                  storageClassName: fast-ssd
                  accessModes: ["ReadWriteOnce"]
                  resources:
                    requests:
                      storage: 50Gi
        grafana:
          adminPassword: $grafana.adminPassword
          persistence:
            enabled: true
            storageClassName: fast-ssd
            size: 10Gi
          dashboardProviders:
            dashboardproviders.yaml:
              apiVersion: 1
              providers:
              - name: 'grafana-dashboards-kubernetes'
                orgId: 1
                folder: 'kubernetes'
                type: file
                disableDeletion: true
                editable: true
                options:
                  path: /var/lib/grafana/dashboards/kubernetes
      parameters:
      - name: prometheus.prometheusSpec.replicas
        value: "2"
      - name: grafana.replicas
        value: "2"
  destination:
    server: https://kubernetes.default.svc
    namespace: monitoring
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
    - CreateNamespace=true
    - ServerSideApply=true
```

### Kustomize Application

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: api-service
  namespace: argocd
spec:
  project: microservices
  source:
    repoURL: https://github.com/company/k8s-configs
    targetRevision: HEAD
    path: overlays/production
    kustomize:
      namePrefix: prod-
      nameSuffix: -v1
      images:
      - newName: registry.company.com/api-service
        newTag: v2.1.0
      commonLabels:
        environment: production
        version: v2.1.0
      patchesStrategicMerge:
      - |-
        apiVersion: apps/v1
        kind: Deployment
        metadata:
          name: api-service
        spec:
          replicas: 5
          template:
            spec:
              containers:
              - name: api-service
                resources:
                  requests:
                    memory: 512Mi
                    cpu: 500m
                  limits:
                    memory: 1Gi
                    cpu: 1000m
  destination:
    server: https://kubernetes.default.svc
    namespace: api-production
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
    - CreateNamespace=true
    - ApplyOutOfSyncOnly=true
```

---

## Project & RBAC Configuration

### Project Configuration

```yaml
apiVersion: argoproj.io/v1alpha1
kind: AppProject
metadata:
  name: production
  namespace: argocd
spec:
  description: Production applications and infrastructure

  # Source repositories allowed for this project
  sourceRepos:
  - 'https://github.com/company/*'
  - 'https://charts.bitnami.com/bitnami'
  - 'https://prometheus-community.github.io/helm-charts'
  - 'https://helm.elastic.co'

  # Destination clusters and namespaces
  destinations:
  - namespace: 'production'
    server: https://kubernetes.default.svc
  - namespace: 'monitoring'
    server: https://kubernetes.default.svc
  - namespace: 'logging'
    server: https://kubernetes.default.svc

  # Cluster resource whitelist
  clusterResourceWhitelist:
  - group: ''
    kind: Namespace
  - group: rbac.authorization.k8s.io
    kind: ClusterRole
  - group: rbac.authorization.k8s.io
    kind: ClusterRoleBinding
  - group: apiextensions.k8s.io
    kind: CustomResourceDefinition

  # Namespace resource whitelist
  namespaceResourceWhitelist:
  - group: ''
    kind: ConfigMap
  - group: ''
    kind: Secret
  - group: ''
    kind: Service
  - group: ''
    kind: ServiceAccount
  - group: apps
    kind: Deployment
  - group: apps
    kind: StatefulSet
  - group: apps
    kind: DaemonSet
  - group: networking.k8s.io
    kind: Ingress
  - group: networking.k8s.io
    kind: NetworkPolicy

  # Project roles and permissions
  roles:
  - name: admin
    description: Full access to production project
    policies:
    - p, proj:production:admin, applications, *, production/*, allow
    - p, proj:production:admin, repositories, *, *, allow
    - p, proj:production:admin, certificates, *, *, allow
    - p, proj:production:admin, clusters, *, *, allow
    groups:
    - company:production-admins
    - company:platform-team

  - name: developer
    description: Developer access to production project
    policies:
    - p, proj:production:developer, applications, get, production/*, allow
    - p, proj:production:developer, applications, sync, production/*, allow
    - p, proj:production:developer, applications, action/*, production/*, allow
    - p, proj:production:developer, repositories, get, *, allow
    groups:
    - company:developers
    - company:backend-team

  - name: readonly
    description: Read-only access to production project
    policies:
    - p, proj:production:readonly, applications, get, production/*, allow
    - p, proj:production:readonly, repositories, get, *, allow
    groups:
    - company:auditors
    - company:managers

  # Sync windows for controlled deployments
  syncWindows:
  - kind: allow
    schedule: '0 9-17 * * MON-FRI'
    duration: 8h
    applications:
    - '*'
    manualSync: true
  - kind: deny
    schedule: '0 0-6 * * *'
    duration: 6h
    applications:
    - 'critical-*'
    manualSync: false
```

---

## Advanced Features

### Application Sets for Multi-Environment

```yaml
apiVersion: argoproj.io/v1alpha1
kind: ApplicationSet
metadata:
  name: microservices-environments
  namespace: argocd
spec:
  generators:
  - clusters:
      selector:
        matchLabels:
          environment: production
  - git:
      repoURL: https://github.com/company/k8s-manifests
      revision: HEAD
      directories:
      - path: microservices/*
  template:
    metadata:
      name: '{{path.basename}}-{{name}}'
      labels:
        environment: '{{metadata.labels.environment}}'
        service: '{{path.basename}}'
    spec:
      project: microservices
      source:
        repoURL: https://github.com/company/k8s-manifests
        targetRevision: HEAD
        path: '{{path}}'
        kustomize:
          commonLabels:
            environment: '{{metadata.labels.environment}}'
            cluster: '{{name}}'
      destination:
        server: '{{server}}'
        namespace: '{{path.basename}}-{{metadata.labels.environment}}'
      syncPolicy:
        automated:
          prune: true
          selfHeal: true
        syncOptions:
        - CreateNamespace=true
```

### Progressive Sync with Waves

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: full-stack-app
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/company/full-stack-manifests
    targetRevision: HEAD
    path: .
  destination:
    server: https://kubernetes.default.svc
    namespace: application
  syncPolicy:
    syncOptions:
    - ApplyOutOfSyncOnly=true
    - PrunePropagationPolicy=foreground
  # Sync waves defined in manifests:
  # Wave -1: Namespaces, CRDs
  # Wave 0:  ConfigMaps, Secrets
  # Wave 1:  Databases, Storage
  # Wave 2:  Backend Services
  # Wave 3:  Frontend Services
  # Wave 4:  Ingress, Monitoring
```

### Resource Hooks

```yaml
# pre-sync-hook.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: database-migration
  annotations:
    argocd.argoproj.io/hook: PreSync
    argocd.argoproj.io/hook-delete-policy: BeforeHookCreation
    argocd.argoproj.io/sync-wave: "-1"
spec:
  template:
    spec:
      restartPolicy: Never
      containers:
      - name: migrate
        image: migrate/migrate:latest
        command:
        - migrate
        - -path
        - /migrations
        - -database
        - postgres://user:pass@postgres:5432/dbname?sslmode=disable
        - up
        volumeMounts:
        - name: migrations
          mountPath: /migrations
      volumes:
      - name: migrations
        configMap:
          name: database-migrations
---
# post-sync-hook.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: cache-warmup
  annotations:
    argocd.argoproj.io/hook: PostSync
    argocd.argoproj.io/hook-delete-policy: HookSucceeded
spec:
  template:
    spec:
      restartPolicy: Never
      containers:
      - name: warmup
        image: curl:latest
        command:
        - curl
        - -f
        - http://web-service:80/api/warmup
```

---

## Multi-Cluster Deployment

### Cluster Registration

```bash
# Add external cluster
argocd cluster add staging-cluster --name staging --upsert

# Add cluster with specific context
argocd cluster add staging-cluster --name staging --upsert --kube-context staging-context

# List clusters
argocd cluster list

# Create cluster secret manually
kubectl create secret generic staging-cluster-secret \
  --from-literal=name=staging \
  --from-literal=server=https://staging-k8s-api.company.com \
  --from-file=config=/path/to/staging-kubeconfig \
  -n argocd

kubectl label secret staging-cluster-secret \
  argocd.argoproj.io/secret-type=cluster \
  -n argocd
```

### Cross-Cluster Application

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: staging-web-app
  namespace: argocd
spec:
  project: multi-cluster
  source:
    repoURL: https://github.com/company/k8s-manifests
    targetRevision: develop
    path: applications/web-app
    kustomize:
      images:
      - newTag: develop-latest
  destination:
    server: https://staging-k8s-api.company.com
    namespace: web-app-staging
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
    - CreateNamespace=true
```

---

## Security & Authentication

### OIDC Configuration

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: argocd-cm
  namespace: argocd
data:
  # OIDC configuration
  oidc.config: |
    name: Company SSO
    issuer: https://auth.company.com
    clientId: argocd
    clientSecret: $oidc.clientSecret
    requestedScopes: ["openid", "profile", "email", "groups"]
    requestedIDTokenClaims: {"groups": {"essential": true}}

  # RBAC configuration
  policy.default: role:readonly
  policy.csv: |
    p, role:admin, applications, *, */*, allow
    p, role:admin, clusters, *, *, allow
    p, role:admin, repositories, *, *, allow

    p, role:developer, applications, get, */*, allow
    p, role:developer, applications, sync, */*, allow
    p, role:developer, applications, action/*, */*, allow

    p, role:readonly, applications, get, */*, allow
    p, role:readonly, repositories, get, *, allow

    g, company:platform-team, role:admin
    g, company:developers, role:developer
    g, company:auditors, role:readonly

  # Resource customizations for health checks
  resource.customizations.health.argoproj.io_Application: |
    hs = {}
    hs.status = "Progressing"
    hs.message = ""
    if obj.status ~= nil then
      if obj.status.health ~= nil then
        hs.status = obj.status.health.status
        hs.message = obj.status.health.message
      end
    end
    return hs
```

### Repository Access with SSH

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: private-repo-creds
  namespace: argocd
  labels:
    argocd.argoproj.io/secret-type: repository
stringData:
  type: git
  url: git@github.com:company/private-manifests.git
  sshPrivateKey: |
    -----BEGIN OPENSSH PRIVATE KEY-----
    <private-key-content>
    -----END OPENSSH PRIVATE KEY-----
```

---

## Monitoring & Troubleshooting

### Application Health Monitoring

```yaml
# Custom health check for applications
apiVersion: v1
kind: ConfigMap
metadata:
  name: argocd-cm
  namespace: argocd
data:
  resource.customizations.health.apps_Deployment: |
    hs = {}
    if obj.status ~= nil then
      if obj.status.replicas ~= nil and obj.status.updatedReplicas ~= nil and obj.status.readyReplicas ~= nil and obj.status.availableReplicas ~= nil then
        if obj.status.updatedReplicas == obj.status.replicas and obj.status.readyReplicas == obj.status.replicas and obj.status.availableReplicas == obj.status.replicas then
          hs.status = "Healthy"
          hs.message = "Deployment is healthy"
          return hs
        end
      end
    end
    hs.status = "Progressing"
    hs.message = "Waiting for deployment to complete"
    return hs
```

### Notification Configuration

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: argocd-notifications-cm
  namespace: argocd
data:
  service.slack: |
    token: $slack-token

  template.app-deployed: |
    email:
      subject: New version of an application {{.app.metadata.name}} is up and running.
    message: |
      {{if eq .serviceType "slack"}}:white_check_mark:{{end}} Application {{.app.metadata.name}} is now running new version.
    slack:
      attachments: |
        [{
          "title": "{{.app.metadata.name}}",
          "title_link":"{{.context.argocdUrl}}/applications/{{.app.metadata.name}}",
          "color": "#18be52",
          "fields": [
          {
            "title": "Sync Status",
            "value": "{{.app.status.sync.status}}",
            "short": true
          },
          {
            "title": "Repository",
            "value": "{{.app.spec.source.repoURL}}",
            "short": true
          },
          {
            "title": "Revision",
            "value": "{{.app.status.sync.revision}}",
            "short": true
          }
          {{range $index, $c := .app.status.conditions}}
          ,{
            "title": "{{$c.type}}",
            "value": "{{$c.message}}",
            "short": true
          }
          {{end}}
          ]
        }]

  trigger.on-deployed: |
    - description: Application is synced and healthy
      send:
      - app-deployed
      when: app.status.operationState.phase in ['Succeeded'] and app.status.health.status == 'Healthy'

  trigger.on-health-degraded: |
    - description: Application has degraded
      send:
      - app-health-degraded
      when: app.status.health.status == 'Degraded'

  trigger.on-sync-failed: |
    - description: Application sync is failed
      send:
      - app-sync-failed
      when: app.status.operationState.phase in ['Error', 'Failed']
```

### Troubleshooting Commands

```bash
# Check application status
argocd app get myapp
argocd app sync myapp
argocd app diff myapp
argocd app history myapp

# View application logs
argocd app logs myapp
argocd app logs myapp --kind Pod --name myapp-pod

# Check sync status
argocd app wait myapp
argocd app wait myapp --health

# Refresh application
argocd app get myapp --refresh
argocd app get myapp --hard-refresh

# Debug sync issues
kubectl get events -n argocd
kubectl logs -n argocd deployment/argocd-application-controller
kubectl logs -n argocd deployment/argocd-repo-server
```

---

## Production Best Practices

### High Availability Setup

```yaml
# HA Argo CD configuration
apiVersion: argoproj.io/v1alpha1
kind: ArgoCD
metadata:
  name: argocd-ha
  namespace: argocd
spec:
  ha:
    enabled: true
    redisProxyImage: haproxy:2.6.2-alpine
    redisProxyVersion: 2.6.2-alpine

  controller:
    replicas: 2
    resources:
      requests:
        cpu: 500m
        memory: 1Gi
      limits:
        cpu: 2000m
        memory: 4Gi

  server:
    replicas: 3
    resources:
      requests:
        cpu: 250m
        memory: 512Mi
      limits:
        cpu: 500m
        memory: 1Gi
    service:
      type: LoadBalancer

  repoServer:
    replicas: 3
    resources:
      requests:
        cpu: 250m
        memory: 512Mi
      limits:
        cpu: 1000m
        memory: 2Gi

  redis:
    enabled: true

  applicationSet:
    enabled: true
    replicas: 2
    resources:
      requests:
        cpu: 100m
        memory: 128Mi
      limits:
        cpu: 500m
        memory: 512Mi
```

### Backup Strategy

```bash
#!/bin/bash
# Argo CD backup script

BACKUP_DIR="/backup/argocd/$(date +%Y-%m-%d)"
mkdir -p "$BACKUP_DIR"

# Export applications
kubectl get applications -n argocd -o yaml > "$BACKUP_DIR/applications.yaml"

# Export projects
kubectl get appprojects -n argocd -o yaml > "$BACKUP_DIR/projects.yaml"

# Export repositories
kubectl get secrets -n argocd -l argocd.argoproj.io/secret-type=repository -o yaml > "$BACKUP_DIR/repositories.yaml"

# Export clusters
kubectl get secrets -n argocd -l argocd.argoproj.io/secret-type=cluster -o yaml > "$BACKUP_DIR/clusters.yaml"

# Export configuration
kubectl get configmaps -n argocd -o yaml > "$BACKUP_DIR/configmaps.yaml"

# Export certificates
kubectl get secrets -n argocd -l argocd.argoproj.io/secret-type=tls -o yaml > "$BACKUP_DIR/certificates.yaml"

echo "Backup completed: $BACKUP_DIR"
```

### Resource Management

```yaml
# Resource limits for Argo CD components
apiVersion: v1
kind: LimitRange
metadata:
  name: argocd-limits
  namespace: argocd
spec:
  limits:
  - default:
      cpu: 500m
      memory: 1Gi
    defaultRequest:
      cpu: 100m
      memory: 256Mi
    type: Container
---
apiVersion: v1
kind: ResourceQuota
metadata:
  name: argocd-quota
  namespace: argocd
spec:
  hard:
    requests.cpu: "4"
    requests.memory: 8Gi
    limits.cpu: "8"
    limits.memory: 16Gi
    persistentvolumeclaims: "5"
```

---

## Cross-References

**Related Documentation:**
- [Kubernetes GitOps & CI-CD](Kubernetes%20GitOps%20&%20CI-CD.md) - Comprehensive GitOps patterns and CI/CD integration
- [Kubernetes Production Best Practices](Kubernetes%20Production%20Best%20Practices.md) - Production deployment strategies
- [Kubernetes Security](Kubernetes%20Security.md) - RBAC, authentication, and security policies
- [Kubernetes Helm Package Manager](Kubernetes%20Helm%20Package%20Manager.md) - Helm integration with Argo CD

**Integration Points:**
- **Source Control**: Git repository management and webhook integration
- **CI/CD Pipelines**: Integration with GitHub Actions, GitLab CI, Jenkins
- **Monitoring**: Prometheus metrics and Grafana dashboards
- **Security**: OIDC authentication, RBAC, and secret management
- **Multi-Cluster**: Cross-cluster application deployment and management

**Best Practices Summary:**
- Use declarative configuration stored in Git repositories
- Implement proper RBAC and project-based access control
- Configure automated sync policies with appropriate safety measures
- Monitor application health and deployment status
- Maintain regular backups of Argo CD configuration
- Use ApplicationSets for managing multiple environments
- Implement proper secret management and rotation
- Configure notifications for deployment events