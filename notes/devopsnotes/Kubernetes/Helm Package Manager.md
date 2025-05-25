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

# Rollback release
helm rollback my-release 1

# Uninstall release
helm uninstall my-release
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
