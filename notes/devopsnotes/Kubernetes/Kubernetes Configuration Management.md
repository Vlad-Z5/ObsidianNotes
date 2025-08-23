## Configuration Management Deep Dive

### ConfigMaps Advanced Usage

**File-based ConfigMaps:**

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
data:
  # Property-like keys
  database.host: "mysql.database.svc.cluster.local"
  database.port: "3306"
  
  # File-like keys
  nginx.conf: |
    server {
        listen 80;
        server_name localhost;
        
        location / {
            proxy_pass http://backend-service;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }
    }
  
  application.properties: |
    spring.datasource.url=jdbc:mysql://mysql:3306/mydb
    spring.datasource.username=admin
    spring.jpa.hibernate.ddl-auto=update
    logging.level.org.springframework=INFO
```

**ConfigMap Usage Patterns:**

```yaml
# Environment variables from ConfigMap
env:
- name: DATABASE_HOST
  valueFrom:
    configMapKeyRef:
      name: app-config
      key: database.host

# All keys as environment variables
envFrom:
- configMapRef:
    name: app-config

# Mount as volume
volumes:
- name: config-volume
  configMap:
    name: app-config
    items:
    - key: nginx.conf
      path: nginx.conf
      mode: 0644
```

### Secrets Management Deep Dive

**Secret Types:**

- **Opaque**: Generic secrets (default)
- **kubernetes.io/service-account-token**: Service account tokens
- **kubernetes.io/dockercfg**: Docker registry credentials
- **kubernetes.io/tls**: TLS certificates

**TLS Secret Creation:**

```bash
# Create TLS secret from certificate files
kubectl create secret tls tls-secret \
  --cert=path/to/tls.crt \
  --key=path/to/tls.key
```

```yaml
# Or from YAML
apiVersion: v1
kind: Secret
metadata:
  name: tls-secret
type: kubernetes.io/tls
data:
  tls.crt: LS0tLS1CRUdJTi... # base64 encoded
  tls.key: LS0tLS1CRUdJTi... # base64 encoded
```

**Docker Registry Secret:**

```bash
kubectl create secret docker-registry regcred \
  --docker-server=https://index.docker.io/v1/ \
  --docker-username=myuser \
  --docker-password=mypass \
  --docker-email=my@email.com
```

```yaml
# Use in pod spec
spec:
  imagePullSecrets:
  - name: regcred
```

**External Secrets Operator:**

```yaml
# SecretStore for AWS Secrets Manager
apiVersion: external-secrets.io/v1beta1
kind: SecretStore
metadata:
  name: aws-secretstore
spec:
  provider:
    aws:
      service: SecretsManager
      region: us-west-2
      auth:
        secretRef:
          accessKeyID:
            name: aws-secret
            key: access-key
          secretAccessKey:
            name: aws-secret
            key: secret-access-key
---
# External Secret
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: app-secret
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: aws-secretstore
    kind: SecretStore
  target:
    name: app-secret
    creationPolicy: Owner
  data:
  - secretKey: password
    remoteRef:
      key: prod/myapp/db
      property: password
```

### Basic ConfigMap Usage

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

### Basic Secret Usage

Stores sensitive data like passwords, tokens, keys

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: app-secret
type: Opaque
data:
  username: YWRtaW4= # base64 encoded
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
