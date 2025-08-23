## GitOps & CI/CD Comprehensive Guide

### GitOps Fundamentals

GitOps is a declarative approach to continuous deployment where Git repositories serve as the single source of truth for infrastructure and application configuration.

#### GitOps Core Principles

1. **Declarative**: System state described declaratively
2. **Versioned**: Configuration stored in Git with full version history  
3. **Immutable**: No direct cluster changes, only through Git
4. **Pull-based**: Operators pull changes from Git repositories
5. **Continuously Reconciled**: Actual state continuously reconciled with desired state

### ArgoCD Deep Dive

ArgoCD is a declarative, GitOps continuous delivery tool for Kubernetes.

#### ArgoCD Installation and Configuration

**Install ArgoCD:**

```bash
# Create namespace
kubectl create namespace argocd

# Install ArgoCD
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# Get initial admin password
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d

# Port forward to access UI
kubectl port-forward svc/argocd-server -n argocd 8080:443
```

**ArgoCD Configuration:**

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: argocd-cm
  namespace: argocd
  labels:
    app.kubernetes.io/name: argocd-cm
    app.kubernetes.io/part-of: argocd
data:
  # Application instance label key
  application.instanceLabelKey: argocd.argoproj.io/instance
  
  # Server configuration
  server.insecure: "true"
  
  # Git repositories configuration
  repositories: |
    - type: git
      url: https://github.com/company/k8s-manifests
    - type: git
      url: https://github.com/company/helm-charts
      name: helm-charts
      
  # Resource customizations
  resource.customizations.health.argoproj.io_Application: |
    hs = {}
    hs.status = "Progressing"
    hs.message = ""
    if obj.status ~= nil then
      if obj.status.health ~= nil then
        hs.status = obj.status.health.status
        if obj.status.health.message ~= nil then
          hs.message = obj.status.health.message
        end
      end
    end
    return hs
    
  # OIDC configuration
  oidc.config: |
    name: OIDC
    issuer: https://your-oidc-provider.com
    clientId: argocd
    clientSecret: $oidc.clientSecret
    requestedScopes: ["openid", "profile", "email", "groups"]
    requestedIDTokenClaims: {"groups": {"essential": true}}
```

#### ArgoCD Application Configuration

**Basic Application:**

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: web-app
  namespace: argocd
  finalizers:
    - resources-finalizer.argocd.argoproj.io
spec:
  project: default
  source:
    repoURL: https://github.com/company/k8s-manifests
    targetRevision: HEAD
    path: apps/web-app
  destination:
    server: https://kubernetes.default.svc
    namespace: production
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
    - CreateNamespace=true
    retry:
      limit: 5
      backoff:
        duration: 5s
        factor: 2
        maxDuration: 3m0s
```

**Helm-based Application:**

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
  destination:
    server: https://kubernetes.default.svc
    namespace: monitoring
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
    - CreateNamespace=true
```

**Kustomize Application:**

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: api-service
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/company/k8s-configs
    targetRevision: HEAD
    path: overlays/production
  destination:
    server: https://kubernetes.default.svc
    namespace: api
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
    - CreateNamespace=true
    - ApplyOutOfSyncOnly=true
```

#### ArgoCD Projects and RBAC

**Project Configuration:**

```yaml
apiVersion: argoproj.io/v1alpha1
kind: AppProject
metadata:
  name: production
  namespace: argocd
spec:
  description: Production applications
  
  # Source repositories
  sourceRepos:
  - 'https://github.com/company/*'
  - 'https://helm.elastic.co'
  - 'https://charts.bitnami.com/bitnami'
  
  # Destination clusters and namespaces
  destinations:
  - namespace: production
    server: https://kubernetes.default.svc
  - namespace: monitoring
    server: https://kubernetes.default.svc
    
  # Cluster resource whitelist
  clusterResourceWhitelist:
  - group: ''
    kind: Namespace
  - group: rbac.authorization.k8s.io
    kind: ClusterRole
  - group: rbac.authorization.k8s.io
    kind: ClusterRoleBinding
    
  # Namespace resource whitelist
  namespaceResourceWhitelist:
  - group: ''
    kind: ConfigMap
  - group: ''
    kind: Secret
  - group: ''
    kind: Service
  - group: apps
    kind: Deployment
  - group: apps
    kind: StatefulSet
    
  # Roles for project
  roles:
  - name: admin
    description: Admin role for production project
    policies:
    - p, proj:production:admin, applications, *, production/*, allow
    - p, proj:production:admin, repositories, *, *, allow
    groups:
    - company:production-admins
    
  - name: developer
    description: Developer role for production project  
    policies:
    - p, proj:production:developer, applications, get, production/*, allow
    - p, proj:production:developer, applications, sync, production/*, allow
    groups:
    - company:developers
```

#### ArgoCD Multi-Cluster Setup

**Cluster Registration:**

```bash
# List clusters
argocd cluster list

# Add external cluster
argocd cluster add staging-cluster --name staging

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

**Cross-Cluster Application:**

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: staging-app
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/company/k8s-manifests
    targetRevision: develop
    path: apps/web-app
  destination:
    server: https://staging-k8s-api.company.com
    namespace: staging
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
```

### Flux v2 Deep Dive

Flux v2 is a next-generation GitOps toolkit for Kubernetes.

#### Flux v2 Installation

**Bootstrap Flux:**

```bash
# Install Flux CLI
curl -s https://fluxcd.io/install.sh | sudo bash

# Bootstrap Flux with GitHub
flux bootstrap github \
  --owner=company \
  --repository=k8s-cluster \
  --branch=main \
  --path=./clusters/production \
  --personal

# Bootstrap with GitLab
flux bootstrap gitlab \
  --hostname=gitlab.company.com \
  --owner=devops \
  --repository=k8s-gitops \
  --branch=main \
  --path=./clusters/production
```

#### Flux v2 Source Management

**Git Repository Source:**

```yaml
apiVersion: source.toolkit.fluxcd.io/v1beta2
kind: GitRepository
metadata:
  name: app-manifests
  namespace: flux-system
spec:
  interval: 1m
  ref:
    branch: main
  url: https://github.com/company/k8s-manifests
  secretRef:
    name: git-credentials
---
apiVersion: v1
kind: Secret
metadata:
  name: git-credentials
  namespace: flux-system
type: Opaque
data:
  username: <base64-encoded-username>
  password: <base64-encoded-token>
```

**Helm Repository Source:**

```yaml
apiVersion: source.toolkit.fluxcd.io/v1beta2
kind: HelmRepository
metadata:
  name: bitnami
  namespace: flux-system
spec:
  interval: 10m
  url: https://charts.bitnami.com/bitnami
---
apiVersion: source.toolkit.fluxcd.io/v1beta2
kind: HelmRepository
metadata:
  name: prometheus-community
  namespace: flux-system
spec:
  interval: 10m
  url: https://prometheus-community.github.io/helm-charts
```

**OCI Repository Source:**

```yaml
apiVersion: source.toolkit.fluxcd.io/v1beta2
kind: OCIRepository
metadata:
  name: podinfo
  namespace: flux-system
spec:
  interval: 10m
  url: oci://ghcr.io/stefanprodan/manifests/podinfo
  ref:
    tag: 6.3.5
```

#### Flux v2 Kustomization

**Application Kustomization:**

```yaml
apiVersion: kustomize.toolkit.fluxcd.io/v1beta2
kind: Kustomization
metadata:
  name: web-app
  namespace: flux-system
spec:
  interval: 5m
  path: "./apps/web-app"
  prune: true
  sourceRef:
    kind: GitRepository
    name: app-manifests
  targetNamespace: production
  healthChecks:
  - apiVersion: apps/v1
    kind: Deployment
    name: web-app
    namespace: production
  dependsOn:
  - name: infrastructure
```

**Infrastructure Kustomization:**

```yaml
apiVersion: kustomize.toolkit.fluxcd.io/v1beta2
kind: Kustomization
metadata:
  name: infrastructure
  namespace: flux-system
spec:
  interval: 10m
  path: "./infrastructure"
  prune: true
  sourceRef:
    kind: GitRepository
    name: app-manifests
  patches:
  - patch: |-
      apiVersion: v1
      kind: ConfigMap
      metadata:
        name: cluster-info
      data:
        cluster-name: production
    target:
      kind: ConfigMap
      name: cluster-info
```

#### Flux v2 Helm Releases

**Basic Helm Release:**

```yaml
apiVersion: helm.toolkit.fluxcd.io/v2beta1
kind: HelmRelease
metadata:
  name: nginx-ingress
  namespace: flux-system
spec:
  interval: 10m
  chart:
    spec:
      chart: ingress-nginx
      version: 4.5.2
      sourceRef:
        kind: HelmRepository
        name: ingress-nginx
        namespace: flux-system
  targetNamespace: ingress-nginx
  createNamespace: true
  values:
    controller:
      service:
        type: LoadBalancer
        annotations:
          service.beta.kubernetes.io/aws-load-balancer-type: nlb
      metrics:
        enabled: true
        serviceMonitor:
          enabled: true
```

**Advanced Helm Release with Dependencies:**

```yaml
apiVersion: helm.toolkit.fluxcd.io/v2beta1
kind: HelmRelease
metadata:
  name: monitoring-stack
  namespace: flux-system
spec:
  interval: 15m
  chart:
    spec:
      chart: kube-prometheus-stack
      version: 45.7.1
      sourceRef:
        kind: HelmRepository
        name: prometheus-community
        namespace: flux-system
  targetNamespace: monitoring
  createNamespace: true
  dependsOn:
  - name: nginx-ingress
  values:
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
      adminPassword: ${GRAFANA_ADMIN_PASSWORD}
      ingress:
        enabled: true
        ingressClassName: nginx
        hosts:
        - grafana.company.com
        tls:
        - secretName: grafana-tls
          hosts:
          - grafana.company.com
  postRenderers:
  - kustomize:
      patches:
      - target:
          kind: Deployment
          name: monitoring-stack-grafana
        patch: |-
          - op: add
            path: /spec/template/spec/containers/0/env/-
            value:
              name: GF_SECURITY_ADMIN_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: grafana-credentials
                  key: admin-password
```

### Tekton Pipelines Deep Dive

Tekton provides Kubernetes-native CI/CD pipeline building blocks.

#### Tekton Installation

```bash
# Install Tekton Pipelines
kubectl apply --filename https://storage.googleapis.com/tekton-releases/pipeline/latest/release.yaml

# Install Tekton Triggers
kubectl apply --filename https://storage.googleapis.com/tekton-releases/triggers/latest/release.yaml

# Install Tekton Dashboard
kubectl apply --filename https://storage.googleapis.com/tekton-releases/dashboard/latest/tekton-dashboard-release.yaml
```

#### Tekton Tasks

**Build Task:**

```yaml
apiVersion: tekton.dev/v1beta1
kind: Task
metadata:
  name: build-and-push
spec:
  params:
  - name: image-name
    description: Name of the image to build
  - name: image-tag
    description: Tag for the image
    default: latest
  - name: dockerfile
    description: Path to Dockerfile
    default: ./Dockerfile
  workspaces:
  - name: source
    description: Source code workspace
  - name: dockerconfig
    description: Docker registry credentials
  steps:
  - name: build-and-push
    image: gcr.io/kaniko-project/executor:latest
    env:
    - name: DOCKER_CONFIG
      value: /tekton/creds/.docker
    command:
    - /kaniko/executor
    args:
    - --dockerfile=$(params.dockerfile)
    - --context=$(workspaces.source.path)
    - --destination=$(params.image-name):$(params.image-tag)
    - --cache=true
    - --cache-ttl=6h
    volumeMounts:
    - name: $(workspaces.dockerconfig.volume)
      mountPath: /tekton/creds/.docker
```

**Test Task:**

```yaml
apiVersion: tekton.dev/v1beta1
kind: Task
metadata:
  name: run-tests
spec:
  params:
  - name: test-command
    description: Command to run tests
    default: npm test
  workspaces:
  - name: source
    description: Source code workspace
  steps:
  - name: install-dependencies
    image: node:16
    workingDir: $(workspaces.source.path)
    script: |
      #!/bin/bash
      set -e
      npm ci
  - name: run-tests
    image: node:16
    workingDir: $(workspaces.source.path)
    script: |
      #!/bin/bash
      set -e
      $(params.test-command)
      
  - name: upload-coverage
    image: node:16
    workingDir: $(workspaces.source.path)
    script: |
      #!/bin/bash
      if [ -f coverage/lcov.info ]; then
        npx codecov
      fi
    env:
    - name: CODECOV_TOKEN
      valueFrom:
        secretKeyRef:
          name: codecov-secret
          key: token
```

**Deploy Task:**

```yaml
apiVersion: tekton.dev/v1beta1
kind: Task
metadata:
  name: deploy-to-k8s
spec:
  params:
  - name: image-name
    description: Name of the image to deploy
  - name: image-tag
    description: Tag of the image to deploy
  - name: namespace
    description: Target namespace
    default: default
  - name: deployment-name
    description: Name of the deployment
  workspaces:
  - name: manifests
    description: Kubernetes manifests workspace
  steps:
  - name: update-image
    image: mikefarah/yq:4
    workingDir: $(workspaces.manifests.path)
    script: |
      #!/bin/bash
      set -e
      yq eval '.spec.template.spec.containers[0].image = "$(params.image-name):$(params.image-tag)"' \
        -i deployment.yaml
        
  - name: apply-manifests
    image: bitnami/kubectl:latest
    workingDir: $(workspaces.manifests.path)
    script: |
      #!/bin/bash
      set -e
      kubectl apply -f . -n $(params.namespace)
      kubectl rollout status deployment/$(params.deployment-name) -n $(params.namespace)
```

#### Tekton Pipelines

**Complete CI/CD Pipeline:**

```yaml
apiVersion: tekton.dev/v1beta1
kind: Pipeline
metadata:
  name: web-app-pipeline
spec:
  params:
  - name: git-url
    description: Git repository URL
  - name: git-revision
    description: Git revision to build
    default: main
  - name: image-name
    description: Name of the image to build
  - name: image-tag
    description: Tag for the image
  - name: deployment-name
    description: Name of the deployment
  - name: namespace
    description: Target namespace
    default: production
    
  workspaces:
  - name: shared-workspace
    description: Shared workspace for pipeline
  - name: docker-credentials
    description: Docker registry credentials
    
  tasks:
  - name: clone-repository
    taskRef:
      name: git-clone
      kind: ClusterTask
    params:
    - name: url
      value: $(params.git-url)
    - name: revision
      value: $(params.git-revision)
    workspaces:
    - name: output
      workspace: shared-workspace
      
  - name: run-tests
    taskRef:
      name: run-tests
    runAfter:
    - clone-repository
    workspaces:
    - name: source
      workspace: shared-workspace
      
  - name: build-and-push
    taskRef:
      name: build-and-push
    runAfter:
    - run-tests
    params:
    - name: image-name
      value: $(params.image-name)
    - name: image-tag
      value: $(params.image-tag)
    workspaces:
    - name: source
      workspace: shared-workspace
    - name: dockerconfig
      workspace: docker-credentials
      
  - name: deploy
    taskRef:
      name: deploy-to-k8s
    runAfter:
    - build-and-push
    params:
    - name: image-name
      value: $(params.image-name)
    - name: image-tag
      value: $(params.image-tag)
    - name: deployment-name
      value: $(params.deployment-name)
    - name: namespace
      value: $(params.namespace)
    workspaces:
    - name: manifests
      workspace: shared-workspace
```

#### Tekton Triggers

**EventListener and Trigger:**

```yaml
apiVersion: triggers.tekton.dev/v1beta1
kind: EventListener
metadata:
  name: github-webhook
spec:
  serviceAccountName: tekton-triggers-admin
  triggers:
  - name: github-push-trigger
    interceptors:
    - ref:
        name: "github"
      params:
      - name: "secretRef"
        value:
          secretName: github-webhook-secret
          secretKey: token
      - name: "eventTypes"
        value: ["push"]
    bindings:
    - ref: github-push-binding
    template:
      ref: web-app-pipeline-template
---
apiVersion: triggers.tekton.dev/v1beta1
kind: TriggerBinding
metadata:
  name: github-push-binding
spec:
  params:
  - name: git-url
    value: $(body.repository.clone_url)
  - name: git-revision
    value: $(body.head_commit.id)
  - name: image-tag
    value: $(body.head_commit.id[0:7])
---
apiVersion: triggers.tekton.dev/v1beta1
kind: TriggerTemplate
metadata:
  name: web-app-pipeline-template
spec:
  params:
  - name: git-url
  - name: git-revision
  - name: image-tag
  resourcetemplates:
  - apiVersion: tekton.dev/v1beta1
    kind: PipelineRun
    metadata:
      name: web-app-pipeline-run-$(uid)
    spec:
      pipelineRef:
        name: web-app-pipeline
      params:
      - name: git-url
        value: $(tt.params.git-url)
      - name: git-revision
        value: $(tt.params.git-revision)
      - name: image-name
        value: registry.company.com/web-app
      - name: image-tag
        value: $(tt.params.image-tag)
      - name: deployment-name
        value: web-app
      workspaces:
      - name: shared-workspace
        volumeClaimTemplate:
          spec:
            accessModes:
            - ReadWriteOnce
            resources:
              requests:
                storage: 1Gi
      - name: docker-credentials
        secret:
          secretName: docker-registry-credentials
```

### Advanced GitOps Patterns

#### Multi-Environment Promotion

**Repository Structure:**

```
k8s-gitops/
├── apps/
│   └── web-app/
│       ├── base/
│       │   ├── deployment.yaml
│       │   ├── service.yaml
│       │   └── kustomization.yaml
│       └── overlays/
│           ├── development/
│           │   ├── kustomization.yaml
│           │   └── patches/
│           ├── staging/
│           │   ├── kustomization.yaml
│           │   └── patches/
│           └── production/
│               ├── kustomization.yaml
│               └── patches/
└── clusters/
    ├── development/
    │   └── apps/
    ├── staging/
    │   └── apps/
    └── production/
        └── apps/
```

**Progressive Delivery with Flagger:**

```yaml
apiVersion: flagger.app/v1beta1
kind: Canary
metadata:
  name: web-app
  namespace: production
spec:
  provider: istio
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: web-app
  progressDeadlineSeconds: 60
  service:
    port: 9898
    targetPort: 9898
    gateways:
    - public-gateway
    hosts:
    - app.company.com
  analysis:
    interval: 1m
    threshold: 5
    maxWeight: 50
    stepWeight: 10
    metrics:
    - name: request-success-rate
      thresholdRange:
        min: 99
      interval: 1m
    - name: request-duration
      thresholdRange:
        max: 500
      interval: 30s
    webhooks:
    - name: acceptance-test
      type: pre-rollout
      url: http://flagger-loadtester.test/
      timeout: 30s
      metadata:
        type: bash
        cmd: "curl -sd 'test' http://web-app-canary:9898/token | grep token"
    - name: load-test
      url: http://flagger-loadtester.test/
      timeout: 5s
      metadata:
        cmd: "hey -z 1m -q 10 -c 2 http://web-app-canary.production:9898/"
```

#### Secrets Management with External Secrets

**External Secrets Operator:**

```yaml
apiVersion: external-secrets.io/v1beta1
kind: SecretStore
metadata:
  name: vault-backend
  namespace: production
spec:
  provider:
    vault:
      server: "https://vault.company.com"
      path: "secret"
      version: "v2"
      auth:
        kubernetes:
          mountPath: "kubernetes"
          role: "production-role"
          serviceAccountRef:
            name: external-secrets-sa
---
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: app-secrets
  namespace: production
spec:
  refreshInterval: 5m
  secretStoreRef:
    name: vault-backend
    kind: SecretStore
  target:
    name: app-secret
    creationPolicy: Owner
  data:
  - secretKey: database-password
    remoteRef:
      key: secret/production/database
      property: password
  - secretKey: api-key
    remoteRef:
      key: secret/production/external-api
      property: key
```

### CI/CD Security Best Practices

#### Secure Pipeline Configuration

**Pod Security Standards:**

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: tekton-pipelines
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/warn: restricted
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: secure-pipeline-sa
  namespace: tekton-pipelines
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: tekton-pipelines
  name: pipeline-runner
rules:
- apiGroups: [""]
  resources: ["pods", "configmaps", "secrets"]
  verbs: ["get", "list", "create", "update", "patch", "delete"]
- apiGroups: ["apps"]
  resources: ["deployments"]
  verbs: ["get", "list", "create", "update", "patch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: pipeline-runner-binding
  namespace: tekton-pipelines
subjects:
- kind: ServiceAccount
  name: secure-pipeline-sa
  namespace: tekton-pipelines
roleRef:
  kind: Role
  name: pipeline-runner
  apiGroup: rbac.authorization.k8s.io
```

**Secure Task with Non-Root User:**

```yaml
apiVersion: tekton.dev/v1beta1
kind: Task
metadata:
  name: secure-build
spec:
  params:
  - name: image-name
    description: Name of the image to build
  workspaces:
  - name: source
  stepTemplate:
    securityContext:
      runAsNonRoot: true
      runAsUser: 1000
      allowPrivilegeEscalation: false
      readOnlyRootFilesystem: true
      capabilities:
        drop:
        - ALL
  steps:
  - name: secure-build
    image: gcr.io/kaniko-project/executor:latest
    command:
    - /kaniko/executor
    args:
    - --dockerfile=Dockerfile
    - --context=$(workspaces.source.path)
    - --destination=$(params.image-name)
    - --cache=true
```

### Monitoring and Observability

#### GitOps Metrics and Monitoring

**ArgoCD Metrics:**

```yaml
apiVersion: v1
kind: ServiceMonitor
metadata:
  name: argocd-metrics
  namespace: monitoring
spec:
  selector:
    matchLabels:
      app.kubernetes.io/name: argocd-server-metrics
  endpoints:
  - port: metrics
    interval: 30s
    path: /metrics
---
apiVersion: v1
kind: ServiceMonitor
metadata:
  name: argocd-repo-server-metrics
  namespace: monitoring
spec:
  selector:
    matchLabels:
      app.kubernetes.io/name: argocd-repo-server
  endpoints:
  - port: metrics
    interval: 30s
    path: /metrics
```

**Flux Metrics:**

```yaml
apiVersion: v1
kind: ServiceMonitor
metadata:
  name: flux-system
  namespace: monitoring
spec:
  namespaceSelector:
    matchNames:
    - flux-system
  selector:
    matchLabels:
      app: kustomize-controller
  endpoints:
  - port: http-prom
    interval: 30s
    path: /metrics
---
apiVersion: v1
kind: ServiceMonitor
metadata:
  name: helm-controller
  namespace: monitoring
spec:
  namespaceSelector:
    matchNames:
    - flux-system
  selector:
    matchLabels:
      app: helm-controller
  endpoints:
  - port: http-prom
    interval: 30s
    path: /metrics
```

### DevOps Best Practices

#### GitOps Implementation Checklist

**✅ Repository Structure:**
- Separate repositories for application code and manifests
- Clear directory structure for environments
- Proper branching strategy for promotions
- Version tagging and release management

**✅ Security:**
- RBAC configuration for GitOps operators
- Secret management with external systems
- Image signing and verification
- Secure webhook configurations

**✅ Operational Excellence:**
- Comprehensive monitoring and alerting
- Backup and disaster recovery procedures
- Documentation and runbooks
- Regular security audits and updates

**✅ Pipeline Optimization:**
- Parallel execution where possible
- Caching strategies for builds
- Resource limits and requests
- Proper error handling and retries