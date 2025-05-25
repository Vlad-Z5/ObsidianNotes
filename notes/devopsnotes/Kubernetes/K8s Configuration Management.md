### ConfigMap

Stores non-confidential configuration data

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
data:
  database_url: "postgresql://db:5432/myapp"
  debug_mode: "true"
  config.properties: |
    property1=value1
    property2=value2
```

**Using ConfigMap in Pod:**

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: app-pod
spec:
  containers:
  - name: app
    image: myapp:latest
    env:
    - name: DATABASE_URL
      valueFrom:
        configMapKeyRef:
          name: app-config
          key: database_url
    volumeMounts:
    - name: config-volume
      mountPath: /etc/config
  volumes:
  - name: config-volume
    configMap:
      name: app-config
```

### Secret

Stores sensitive data like passwords, tokens, keys

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: app-secret
type: Opaque
data:
  username: YWRtaW4=        # base64 encoded
  password: MWYyZDFlMmU2N2Rm # base64 encoded
```

**Using Secret in Pod:**

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: app-pod
spec:
  containers:
  - name: app
    image: myapp:latest
    env:
    - name: DB_USERNAME
      valueFrom:
        secretKeyRef:
          name: app-secret
          key: username
    volumeMounts:
    - name: secret-volume
      mountPath: /etc/secrets
      readOnly: true
  volumes:
  - name: secret-volume
    secret:
      secretName: app-secret
```

### Namespaces

Logical cluster partitioning

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: development
```

```bash
# Working with namespaces
kubectl get namespaces
kubectl create namespace dev
kubectl apply -f deployment.yaml -n dev
kubectl get pods -n dev
kubectl config set-context --current --namespace=dev
```

### Resource Quotas

Limit resource consumption per namespace

```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: compute-quota
  namespace: development
spec:
  hard:
    requests.cpu: "1"
    requests.memory: 1Gi
    limits.cpu: "2"
    limits.memory: 2Gi
    persistentvolumeclaims: "4"
    pods: "10"
```

### Limit Ranges

Set default and maximum resource limits

```yaml
apiVersion: v1
kind: LimitRange
metadata:
  name: limit-range
  namespace: development
spec:
  limits:
  - default:
      memory: "256Mi"
      cpu: "200m"
    defaultRequest:
      memory: "128Mi"
      cpu: "100m"
    max:
      memory: "512Mi"
      cpu: "500m"
    type: Container
```
