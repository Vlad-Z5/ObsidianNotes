Helm is a package manager for K8, just like apt is for Debian, that uses Chart Repositories to install needed resources for the cluster; Helm has version control and configuration management through values. Helm uses {{ .Values.value }} templating for values, charts, releases, etc.
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
