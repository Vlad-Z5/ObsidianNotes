# Kubernetes Helm Package Manager

**Helm** is the package manager for Kubernetes, providing templating, dependency management, and release lifecycle control for complex application deployments in production environments.

## Helm Fundamentals

**Core Concepts:**
- **Charts**: Kubernetes application packages with templates and configuration
- **Releases**: Deployed instances of charts with specific configurations
- **Repositories**: Chart storage and distribution locations
- **Values**: Configuration parameters for chart customization
- **Templates**: Kubernetes manifests with Go templating for dynamic generation

**Helm Architecture:**
- Chart repositories for package distribution
- Tiller-less architecture (Helm 3+) for improved security
- Client-side rendering and server-side application
- Release history and rollback capabilities
## Components
- **Chart.yaml:** Metadata about the chart (name, version, etc.)
- **values.yaml:** Default configuration values
- **templates/**: Directory containing Kubernetes manifests as templates
- **charts/**: Directory for chart dependencies
### Basic Helm Commands

```bash
# Add repository
helm repo add stable https://charts.helm.sh/stable
helm repo update

# Search charts
helm search repo nginx
helm search hub wordpress

# Install chart
helm install my-release stable/nginx
helm install my-app ./my-chart
helm install my-app stable/nginx --values values.yaml

# List releases
helm list
helm list --all-namespaces

# Upgrade release
helm upgrade my-release stable/nginx
helm upgrade my-release stable/nginx --set service.type=LoadBalancer

helm rollback my-release 1 # Rollback release to revision 1

helm uninstall my-release # Uninstall release and delete all associated resources

helm create app # Create a new chart scaffold

helm show values bitnami/nginx # List all configurable values in the chart

helm template my-nginx bitnami/nginx # Render Kubernetes manifest without installing

helm upgrade my-nginx bitnami/nginx --set service.type=NodePort # Upgrade release with new values

helm status my-nginx # Check the status of a release
```

### Chart Structure

```
my-chart/
├── Chart.yaml          # Chart metadata
├── values.yaml         # Default values
├── charts/             # Chart dependencies
├── templates/          # Kubernetes manifests
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── configmap.yaml
│   └── NOTES.txt
└── .helmignore        # Files to ignore
```

**Chart.yaml:**

```yaml
apiVersion: v2
name: my-app
description: A Helm chart for my application
type: application
version: 0.1.0
appVersion: "1.0"
dependencies:
- name: postgresql
  version: 11.6.12
  repository: https://charts.bitnami.com/bitnami
```

**values.yaml:**

```yaml
replicaCount: 1

image:
  repository: nginx
  pullPolicy: Always
  tag: "latest"

service:
  type: ClusterIP
  port: 80

ingress:
  enabled: false
  hosts:
    - host: chart-example.local
      paths: []

resources:
  limits:
    cpu: 500m
    memory: 512Mi
  requests:
    cpu: 250m
    memory: 256Mi
```

---

## Advanced Templating

### Template Functions and Pipelines

```yaml
# Template with functions and conditionals
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "app.fullname" . }}
  labels:
    {{- include "app.labels" . | nindent 4 }}
spec:
  {{- if not .Values.autoscaling.enabled }}
  replicas: {{ .Values.replicaCount }}
  {{- end }}
  selector:
    matchLabels:
      {{- include "app.selectorLabels" . | nindent 6 }}
  template:
    metadata:
      annotations:
        checksum/config: {{ include (print $.Template.BasePath "/configmap.yaml") . | sha256sum }}
      labels:
        {{- include "app.selectorLabels" . | nindent 8 }}
    spec:
      containers:
      - name: {{ .Chart.Name }}
        image: "{{ .Values.image.repository }}:{{ .Values.image.tag | default .Chart.AppVersion }}"
        {{- with .Values.env }}
        env:
        {{- range $key, $value := . }}
        - name: {{ $key }}
          value: {{ $value | quote }}
        {{- end }}
        {{- end }}
```

### Helper Templates (_helpers.tpl)

```yaml
{{/*
Expand the name of the chart.
*/}}
{{- define "app.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "app.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "app.labels" -}}
helm.sh/chart: {{ include "app.chart" . }}
{{ include "app.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "app.selectorLabels" -}}
app.kubernetes.io/name: {{ include "app.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}
```

### Values Schema Validation

```yaml
# values.schema.json
{
  "$schema": "https://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "replicaCount": {
      "type": "integer",
      "minimum": 1,
      "maximum": 10
    },
    "image": {
      "type": "object",
      "properties": {
        "repository": {
          "type": "string"
        },
        "tag": {
          "type": "string",
          "pattern": "^[a-zA-Z0-9.-]+$"
        }
      },
      "required": ["repository", "tag"]
    },
    "resources": {
      "type": "object",
      "properties": {
        "limits": {
          "type": "object",
          "properties": {
            "cpu": {"type": "string"},
            "memory": {"type": "string"}
          }
        }
      }
    }
  },
  "required": ["image"]
}
```

---

## Release Management

### Advanced Release Commands

```bash
# Release management with detailed options
helm install web-app ./my-chart \
  --namespace production \
  --create-namespace \
  --values values-production.yaml \
  --set image.tag=v1.2.3 \
  --wait \
  --timeout 600s \
  --atomic

# Upgrade with rollback on failure
helm upgrade web-app ./my-chart \
  --namespace production \
  --values values-production.yaml \
  --set image.tag=v1.2.4 \
  --wait \
  --timeout 600s \
  --atomic \
  --cleanup-on-fail

# Release history and rollback
helm history web-app -n production
helm rollback web-app 2 -n production

# Test releases
helm test web-app -n production
helm test web-app -n production --logs

# Release status and values
helm status web-app -n production
helm get values web-app -n production
helm get manifest web-app -n production
```

### Multi-Environment Values

```yaml
# values-base.yaml
replicaCount: 3
image:
  repository: myapp
  pullPolicy: IfNotPresent

service:
  type: ClusterIP
  port: 80

resources:
  limits:
    cpu: 500m
    memory: 512Mi
  requests:
    cpu: 250m
    memory: 256Mi

---
# values-production.yaml
replicaCount: 5

image:
  tag: "v1.2.3"

ingress:
  enabled: true
  hosts:
    - host: app.company.com
      paths:
        - path: /
          pathType: Prefix

resources:
  limits:
    cpu: 1000m
    memory: 1Gi
  requests:
    cpu: 500m
    memory: 512Mi

autoscaling:
  enabled: true
  minReplicas: 5
  maxReplicas: 20
  targetCPUUtilizationPercentage: 70
```

---

## Repository Management

### Private Helm Repository

```bash
# Add private repository with authentication
helm repo add private-repo https://charts.company.com \
  --username $HELM_REPO_USERNAME \
  --password $HELM_REPO_PASSWORD

# OCI registry support
helm registry login registry.company.com
helm push my-chart-1.0.0.tgz oci://registry.company.com/helm-charts
helm install web-app oci://registry.company.com/helm-charts/my-chart --version 1.0.0

# Repository management
helm repo list
helm repo update
helm repo remove private-repo

# Search and inspect charts
helm search repo company
helm search hub nginx --max-col-width=80
helm show chart company/web-app
helm show values company/web-app
helm show readme company/web-app
```

### Chart Dependencies

```yaml
# Chart.yaml with dependencies
apiVersion: v2
name: web-application
version: 1.0.0
dependencies:
  - name: postgresql
    version: 11.6.12
    repository: https://charts.bitnami.com/bitnami
    condition: postgresql.enabled
  - name: redis
    version: 17.3.7
    repository: https://charts.bitnami.com/bitnami
    condition: redis.enabled
  - name: monitoring
    version: 1.0.0
    repository: file://../monitoring
```

```bash
# Dependency management
helm dependency update
helm dependency build
helm dependency list

# Install with dependency conditions
helm install web-app ./web-application \
  --set postgresql.enabled=true \
  --set redis.enabled=false
```

---

## Production Patterns

### Blue-Green Deployment with Helm

```bash
#!/bin/bash
# Blue-green deployment script

CHART_PATH="./web-app"
RELEASE_NAME="web-app"
NAMESPACE="production"
NEW_VERSION="$1"

# Deploy to blue environment
helm upgrade ${RELEASE_NAME}-blue $CHART_PATH \
  --namespace $NAMESPACE \
  --set image.tag=$NEW_VERSION \
  --set service.selector.version=blue \
  --wait

# Run tests
helm test ${RELEASE_NAME}-blue -n $NAMESPACE

# Switch traffic (update main service)
helm upgrade $RELEASE_NAME $CHART_PATH \
  --namespace $NAMESPACE \
  --set image.tag=$NEW_VERSION \
  --set service.selector.version=blue \
  --wait

# Cleanup old green environment
helm uninstall ${RELEASE_NAME}-green -n $NAMESPACE
```

### Canary Deployment

```yaml
# values-canary.yaml
replicaCount: 2
image:
  tag: "v1.2.4"

service:
  canary:
    enabled: true
    weight: 10  # 10% traffic to canary

ingress:
  annotations:
    nginx.ingress.kubernetes.io/canary: "true"
    nginx.ingress.kubernetes.io/canary-weight: "10"
```

```bash
# Canary deployment workflow
helm install web-app-canary ./web-app \
  --namespace production \
  --values values-canary.yaml

# Monitor metrics and gradually increase traffic
helm upgrade web-app-canary ./web-app \
  --namespace production \
  --set service.canary.weight=50

# Promote canary to main
helm upgrade web-app ./web-app \
  --namespace production \
  --set image.tag=v1.2.4
```

---

## Security & Best Practices

### Chart Security

```yaml
# Security-focused values
securityContext:
  runAsNonRoot: true
  runAsUser: 10001
  runAsGroup: 10001
  fsGroup: 10001
  seccompProfile:
    type: RuntimeDefault

podSecurityContext:
  fsGroup: 10001

resources:
  limits:
    cpu: 500m
    memory: 512Mi
  requests:
    cpu: 250m
    memory: 256Mi

networkPolicy:
  enabled: true
  ingress:
    - from:
      - namespaceSelector:
          matchLabels:
            name: ingress-nginx
  egress:
    - to:
      - namespaceSelector:
          matchLabels:
            name: database
```

### Chart Testing

```yaml
# templates/tests/test-connection.yaml
apiVersion: v1
kind: Pod
metadata:
  name: "{{ include "app.fullname" . }}-test"
  labels:
    {{- include "app.labels" . | nindent 4 }}
  annotations:
    "helm.sh/hook": test
    "helm.sh/hook-delete-policy": before-hook-creation,hook-succeeded
spec:
  restartPolicy: Never
  containers:
  - name: test
    image: curlimages/curl:latest
    command:
      - /bin/sh
      - -c
      - |
        curl -f http://{{ include "app.fullname" . }}:{{ .Values.service.port }}/health
```

---

## CI/CD Integration

### GitHub Actions with Helm

```yaml
# .github/workflows/deploy.yml
name: Deploy with Helm
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3

    - name: Configure AWS credentials
      uses: aws-actions/configure-aws-credentials@v2
      with:
        aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
        aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        aws-region: us-west-2

    - name: Install Helm
      uses: azure/setup-helm@v3
      with:
        version: '3.10.0'

    - name: Configure kubectl
      run: |
        aws eks update-kubeconfig --name production-cluster

    - name: Lint Helm Chart
      run: |
        helm lint ./charts/web-app

    - name: Deploy to staging
      run: |
        helm upgrade --install web-app-staging ./charts/web-app \
          --namespace staging \
          --create-namespace \
          --values ./charts/web-app/values-staging.yaml \
          --set image.tag=${{ github.sha }} \
          --wait

    - name: Run tests
      run: |
        helm test web-app-staging -n staging

    - name: Deploy to production
      if: github.ref == 'refs/heads/main'
      run: |
        helm upgrade --install web-app ./charts/web-app \
          --namespace production \
          --create-namespace \
          --values ./charts/web-app/values-production.yaml \
          --set image.tag=${{ github.sha }} \
          --wait
```

### GitLab CI with Helm

```yaml
# .gitlab-ci.yml
stages:
  - lint
  - deploy-staging
  - deploy-production

variables:
  HELM_VERSION: "3.10.0"

before_script:
  - curl https://get.helm.sh/helm-v${HELM_VERSION}-linux-amd64.tar.gz | tar xz
  - mv linux-amd64/helm /usr/local/bin/
  - kubectl config use-context $KUBE_CONTEXT

lint-chart:
  stage: lint
  script:
    - helm lint ./charts/web-app
    - helm template web-app ./charts/web-app --values ./charts/web-app/values-staging.yaml

deploy-staging:
  stage: deploy-staging
  script:
    - helm upgrade --install web-app-staging ./charts/web-app
        --namespace staging
        --create-namespace
        --values ./charts/web-app/values-staging.yaml
        --set image.tag=$CI_COMMIT_SHA
        --wait
    - helm test web-app-staging -n staging

deploy-production:
  stage: deploy-production
  script:
    - helm upgrade --install web-app ./charts/web-app
        --namespace production
        --create-namespace
        --values ./charts/web-app/values-production.yaml
        --set image.tag=$CI_COMMIT_SHA
        --wait
  only:
    - main
  when: manual
```

---

## Troubleshooting

### Common Issues and Solutions

**Issue**: Chart validation errors
```bash
# Debug chart issues
helm lint ./my-chart
helm template my-app ./my-chart --debug
helm install my-app ./my-chart --dry-run --debug

# Validate with specific values
helm template my-app ./my-chart \
  --values values-production.yaml \
  --set image.tag=v1.2.3 \
  --debug
```

**Issue**: Template rendering problems
```bash
# Debug template functions
helm template my-app ./my-chart --debug | grep -A 10 -B 10 "error"

# Validate helper templates
helm template my-app ./my-chart --show-only templates/deployment.yaml
```

**Issue**: Release stuck or failed
```bash
# Check release status
helm status my-app -n production
helm history my-app -n production

# Force delete stuck release
helm uninstall my-app -n production --no-hooks

# Manual cleanup if needed
kubectl delete all -l app.kubernetes.io/instance=my-app -n production
```

**Issue**: Dependency problems
```bash
# Debug dependencies
helm dependency list
helm dependency update --debug

# Clear dependency cache
rm -rf charts/
helm dependency update
```

### Debug Commands

```bash
# Comprehensive debugging workflow
helm install my-app ./my-chart \
  --namespace production \
  --dry-run \
  --debug \
  --values values-production.yaml > debug-output.yaml

# Validate generated manifests
kubectl apply --dry-run=client -f debug-output.yaml
kubectl apply --dry-run=server -f debug-output.yaml

# Monitor release deployment
helm install my-app ./my-chart \
  --namespace production \
  --wait \
  --timeout 600s \
  --debug

# Check release resources
kubectl get all -l app.kubernetes.io/instance=my-app -n production
kubectl describe deployment my-app -n production
```

---

## Cross-References

**Related Documentation:**
- [Kubernetes Commands](Kubernetes%20Commands.md) - kubectl commands for Helm resource management
- [Kubernetes GitOps & CI-CD](Kubernetes%20GitOps%20&%20CI-CD.md) - Automated deployment workflows
- [Kubernetes Production Best Practices](Kubernetes%20Production%20Best%20Practices.md) - Security and reliability patterns
- [Kubernetes Troubleshooting](Kubernetes%20Troubleshooting.md) - Application debugging and issue resolution

**Integration Points:**
- **GitOps**: ArgoCD, Flux for automated Helm deployments
- **CI/CD**: GitHub Actions, GitLab CI, Jenkins for chart testing and deployment
- **Monitoring**: Prometheus, Grafana for release monitoring and alerting
- **Security**: Chart scanning, policy enforcement, and compliance validation
