# Kubernetes Configuration Management

**Kubernetes Configuration Management** provides centralized management of application configuration data, secrets, resource allocation, and namespace isolation, enabling secure and scalable configuration deployment across environments.

## Core Configuration Concepts

### Configuration Management Strategy

Kubernetes separates configuration from application code through:
- **ConfigMaps**: Non-sensitive configuration data
- **Secrets**: Sensitive information like passwords and tokens
- **External Secrets**: Integration with external secret management systems
- **Resource Quotas**: Namespace-level resource allocation limits
- **Limit Ranges**: Default and maximum resource constraints

### Configuration Injection Methods

1. **Environment Variables**: Direct injection into container environment
2. **Volume Mounts**: Files accessible through filesystem
3. **Init Containers**: Pre-processing configuration data
4. **Subpath Mounts**: Individual files from ConfigMaps/Secrets

---

## ConfigMaps

### Basic ConfigMap Creation

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
  namespace: production
  labels:
    app: web-application
    environment: production
data:
  # Simple key-value pairs
  database.host: "mysql.database.svc.cluster.local"
  database.port: "3306"
  cache.ttl: "3600"
  log.level: "INFO"

  # Multi-line configuration files
  nginx.conf: |
    upstream backend {
        server backend-service:8080;
        keepalive 32;
    }

    server {
        listen 80;
        server_name app.company.com;

        location /health {
            access_log off;
            return 200 "healthy\n";
        }

        location / {
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_connect_timeout 5s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
        }
    }

  application.yml: |
    server:
      port: 8080
      servlet:
        context-path: /api

    spring:
      datasource:
        url: jdbc:mysql://mysql:3306/mydb
        username: ${DB_USERNAME}
        hikari:
          maximum-pool-size: 20
          minimum-idle: 5
          connection-timeout: 30000

      jpa:
        hibernate:
          ddl-auto: validate
        show-sql: false

      cache:
        type: redis
        redis:
          host: redis.cache.svc.cluster.local
          port: 6379

    logging:
      level:
        org.springframework: INFO
        com.company: DEBUG
      pattern:
        console: "%d{yyyy-MM-dd HH:mm:ss} [%thread] %-5level %logger{36} - %msg%n"
```

### Advanced ConfigMap Usage Patterns

```yaml
# ConfigMap with binary data
apiVersion: v1
kind: ConfigMap
metadata:
  name: binary-config
binaryData:
  certificate.p12: <base64-encoded-binary-data>
data:
  keystore.password: "changeit"
---
# Immutable ConfigMap (Kubernetes 1.19+)
apiVersion: v1
kind: ConfigMap
metadata:
  name: immutable-config
immutable: true
data:
  readonly.config: "This cannot be modified"
```

### ConfigMap Volume Mounts

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: web-app
  template:
    metadata:
      labels:
        app: web-app
    spec:
      containers:
      - name: app
        image: nginx:1.21
        env:
        - name: DATABASE_HOST
          valueFrom:
            configMapKeyRef:
              name: app-config
              key: database.host
        - name: CACHE_TTL
          valueFrom:
            configMapKeyRef:
              name: app-config
              key: cache.ttl
        envFrom:
        - configMapRef:
            name: app-config
        volumeMounts:
        - name: nginx-config
          mountPath: /etc/nginx/nginx.conf
          subPath: nginx.conf
          readOnly: true
        - name: app-config-volume
          mountPath: /etc/config
        resources:
          requests:
            memory: 256Mi
            cpu: 250m
          limits:
            memory: 512Mi
            cpu: 500m
      volumes:
      - name: nginx-config
        configMap:
          name: app-config
          items:
          - key: nginx.conf
            path: nginx.conf
            mode: 0644
      - name: app-config-volume
        configMap:
          name: app-config
          defaultMode: 0644
          optional: false
```

---

## Secrets Management

### Secret Types and Creation

```yaml
# Generic Opaque Secret
apiVersion: v1
kind: Secret
metadata:
  name: app-secrets
  namespace: production
  labels:
    app: web-application
type: Opaque
data:
  database-username: YWRtaW4=  # admin (base64)
  database-password: cGFzc3dvcmQxMjM=  # password123 (base64)
stringData:
  api-key: "live-api-key-12345"  # Auto-encoded to base64
  jwt-secret: "super-secret-jwt-signing-key"
---
# TLS Certificate Secret
apiVersion: v1
kind: Secret
metadata:
  name: tls-certificate
  namespace: production
type: kubernetes.io/tls
data:
  tls.crt: LS0tLS1CRUdJTi4uLi...  # Certificate (base64)
  tls.key: LS0tLS1CRUdJTi4uLi...  # Private key (base64)
---
# Docker Registry Secret
apiVersion: v1
kind: Secret
metadata:
  name: docker-registry-secret
  namespace: production
type: kubernetes.io/dockerconfigjson
data:
  .dockerconfigjson: eyJhdXRocyI6eyJyZWdpc3RyeS5jb21wYW55LmNvbSI6eyJ1c2VybmFtZSI6InVzZXIiLCJwYXNzd29yZCI6InBhc3MiLCJhdXRoIjoiZFhObGNqcHdZWE56In19fQ==
---
# Service Account Token Secret
apiVersion: v1
kind: Secret
metadata:
  name: build-robot-secret
  annotations:
    kubernetes.io/service-account.name: build-robot
type: kubernetes.io/service-account-token
```

### Secret Usage in Workloads

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: secure-app
spec:
  replicas: 2
  selector:
    matchLabels:
      app: secure-app
  template:
    metadata:
      labels:
        app: secure-app
    spec:
      serviceAccountName: app-service-account
      imagePullSecrets:
      - name: docker-registry-secret
      containers:
      - name: app
        image: registry.company.com/secure-app:v1.0.0
        env:
        - name: DB_USERNAME
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: database-username
        - name: DB_PASSWORD
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: database-password
        - name: API_KEY
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: api-key
        volumeMounts:
        - name: tls-certs
          mountPath: /etc/ssl/certs
          readOnly: true
        - name: jwt-secret
          mountPath: /etc/secrets/jwt
          readOnly: true
        securityContext:
          runAsNonRoot: true
          runAsUser: 1000
          readOnlyRootFilesystem: true
          allowPrivilegeEscalation: false
      volumes:
      - name: tls-certs
        secret:
          secretName: tls-certificate
          defaultMode: 0400
      - name: jwt-secret
        secret:
          secretName: app-secrets
          items:
          - key: jwt-secret
            path: token
            mode: 0400
```

### Secret Rotation Strategy

```yaml
# Rolling update with secret rotation
apiVersion: v1
kind: Secret
metadata:
  name: app-secrets-v2
  namespace: production
type: Opaque
stringData:
  database-password: "new-secure-password-456"
  api-key: "new-api-key-67890"
---
# Update deployment to use new secret
apiVersion: apps/v1
kind: Deployment
metadata:
  name: secure-app
spec:
  template:
    metadata:
      annotations:
        secret-version: "v2"  # Force pod restart
    spec:
      containers:
      - name: app
        env:
        - name: DB_PASSWORD
          valueFrom:
            secretKeyRef:
              name: app-secrets-v2  # Updated secret reference
              key: database-password
```

---

## External Secrets

### External Secrets Operator Setup

```bash
# Install External Secrets Operator
helm repo add external-secrets https://charts.external-secrets.io
helm install external-secrets external-secrets/external-secrets -n external-secrets --create-namespace
```

### AWS Secrets Manager Integration

```yaml
# AWS Secrets Manager SecretStore
apiVersion: external-secrets.io/v1beta1
kind: SecretStore
metadata:
  name: aws-secrets-manager
  namespace: production
spec:
  provider:
    aws:
      service: SecretsManager
      region: us-west-2
      auth:
        jwt:
          serviceAccountRef:
            name: external-secrets-sa
---
# External Secret with refresh interval
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: database-credentials
  namespace: production
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: aws-secrets-manager
    kind: SecretStore
  target:
    name: database-secret
    creationPolicy: Owner
    template:
      engineVersion: v2
      data:
        username: "{{ .username }}"
        password: "{{ .password }}"
        connection-string: "postgresql://{{ .username }}:{{ .password }}@postgres:5432/mydb"
  data:
  - secretKey: username
    remoteRef:
      key: prod/database/credentials
      property: username
  - secretKey: password
    remoteRef:
      key: prod/database/credentials
      property: password
```

### HashiCorp Vault Integration

```yaml
# Vault SecretStore with Kubernetes auth
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
            name: vault-sa
---
# Vault ExternalSecret
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: vault-secret
  namespace: production
spec:
  refreshInterval: 10m
  secretStoreRef:
    name: vault-backend
    kind: SecretStore
  target:
    name: vault-generated-secret
    creationPolicy: Owner
  data:
  - secretKey: api-token
    remoteRef:
      key: secret/production/api
      property: token
  - secretKey: signing-key
    remoteRef:
      key: secret/production/jwt
      property: signing-key
```

### Azure Key Vault Integration

```yaml
# Azure Key Vault SecretStore
apiVersion: external-secrets.io/v1beta1
kind: SecretStore
metadata:
  name: azure-keyvault
  namespace: production
spec:
  provider:
    azurekv:
      vaultUrl: "https://my-keyvault.vault.azure.net/"
      authType: ManagedIdentity
      identityId: "/subscriptions/subscription-id/resourceGroups/rg/providers/Microsoft.ManagedIdentity/userAssignedIdentities/identity"
---
# Azure ExternalSecret
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: azure-secret
  namespace: production
spec:
  refreshInterval: 5m
  secretStoreRef:
    name: azure-keyvault
    kind: SecretStore
  target:
    name: azure-generated-secret
    creationPolicy: Owner
  data:
  - secretKey: database-connection
    remoteRef:
      key: database-connection-string
```

---

## Namespace Management

### Production Namespace Configuration

```yaml
# Production namespace with labels and annotations
apiVersion: v1
kind: Namespace
metadata:
  name: production
  labels:
    name: production
    environment: prod
    team: platform
    cost-center: engineering
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/warn: restricted
  annotations:
    scheduler.alpha.kubernetes.io/node-selector: "environment=production"
    kubernetes.io/managed-by: "platform-team"
---
# Development namespace
apiVersion: v1
kind: Namespace
metadata:
  name: development
  labels:
    name: development
    environment: dev
    team: development
    pod-security.kubernetes.io/enforce: baseline
  annotations:
    scheduler.alpha.kubernetes.io/node-selector: "environment=development"
---
# Staging namespace
apiVersion: v1
kind: Namespace
metadata:
  name: staging
  labels:
    name: staging
    environment: staging
    team: qa
    pod-security.kubernetes.io/enforce: restricted
```

### Namespace-scoped RBAC

```yaml
# ServiceAccount for applications
apiVersion: v1
kind: ServiceAccount
metadata:
  name: app-service-account
  namespace: production
  labels:
    app: web-application
automountServiceAccountToken: false
---
# Role with minimal permissions
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: production
  name: app-role
rules:
- apiGroups: [""]
  resources: ["configmaps", "secrets"]
  verbs: ["get", "list"]
- apiGroups: [""]
  resources: ["events"]
  verbs: ["create"]
---
# RoleBinding
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: app-role-binding
  namespace: production
subjects:
- kind: ServiceAccount
  name: app-service-account
  namespace: production
roleRef:
  kind: Role
  name: app-role
  apiGroup: rbac.authorization.k8s.io
```

---

## Resource Management

### Comprehensive Resource Quotas

```yaml
# CPU and memory quotas
apiVersion: v1
kind: ResourceQuota
metadata:
  name: compute-quota
  namespace: production
spec:
  hard:
    requests.cpu: "10"
    requests.memory: 20Gi
    limits.cpu: "20"
    limits.memory: 40Gi
    requests.nvidia.com/gpu: "2"
    limits.nvidia.com/gpu: "4"
---
# Storage quotas
apiVersion: v1
kind: ResourceQuota
metadata:
  name: storage-quota
  namespace: production
spec:
  hard:
    persistentvolumeclaims: "10"
    requests.storage: "100Gi"
    fast-ssd.storageclass.storage.k8s.io/requests.storage: "50Gi"
---
# Object count quotas
apiVersion: v1
kind: ResourceQuota
metadata:
  name: object-quota
  namespace: production
spec:
  hard:
    pods: "50"
    services: "10"
    secrets: "20"
    configmaps: "15"
    replicationcontrollers: "0"
    count/deployments.apps: "20"
    count/jobs.batch: "5"
```

### Advanced Limit Ranges

```yaml
# Container limits
apiVersion: v1
kind: LimitRange
metadata:
  name: container-limits
  namespace: production
spec:
  limits:
  - type: Container
    default:
      memory: "512Mi"
      cpu: "500m"
      ephemeral-storage: "1Gi"
    defaultRequest:
      memory: "256Mi"
      cpu: "250m"
      ephemeral-storage: "500Mi"
    max:
      memory: "2Gi"
      cpu: "2000m"
      ephemeral-storage: "5Gi"
    min:
      memory: "64Mi"
      cpu: "50m"
      ephemeral-storage: "100Mi"
---
# Pod limits
apiVersion: v1
kind: LimitRange
metadata:
  name: pod-limits
  namespace: production
spec:
  limits:
  - type: Pod
    max:
      memory: "4Gi"
      cpu: "4000m"
    min:
      memory: "64Mi"
      cpu: "50m"
---
# PVC limits
apiVersion: v1
kind: LimitRange
metadata:
  name: pvc-limits
  namespace: production
spec:
  limits:
  - type: PersistentVolumeClaim
    max:
      storage: "500Gi"
    min:
      storage: "1Gi"
    default:
      storage: "10Gi"
```

---

## Configuration Security

### Secure Configuration Patterns

```yaml
# Pod with security context and read-only root filesystem
apiVersion: apps/v1
kind: Deployment
metadata:
  name: secure-config-app
spec:
  replicas: 2
  selector:
    matchLabels:
      app: secure-config-app
  template:
    metadata:
      labels:
        app: secure-config-app
    spec:
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        runAsGroup: 3000
        fsGroup: 2000
        seccompProfile:
          type: RuntimeDefault
      containers:
      - name: app
        image: secure-app:latest
        securityContext:
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true
          capabilities:
            drop:
            - ALL
        env:
        - name: CONFIG_PATH
          value: "/etc/config"
        - name: SECRET_PATH
          value: "/etc/secrets"
        volumeMounts:
        - name: config-volume
          mountPath: /etc/config
          readOnly: true
        - name: secret-volume
          mountPath: /etc/secrets
          readOnly: true
        - name: tmp-volume
          mountPath: /tmp
        - name: cache-volume
          mountPath: /app/cache
        resources:
          requests:
            memory: 256Mi
            cpu: 250m
          limits:
            memory: 512Mi
            cpu: 500m
      volumes:
      - name: config-volume
        configMap:
          name: app-config
          defaultMode: 0444
      - name: secret-volume
        secret:
          secretName: app-secrets
          defaultMode: 0400
      - name: tmp-volume
        emptyDir: {}
      - name: cache-volume
        emptyDir:
          sizeLimit: 1Gi
```

### Network Policies for Configuration Security

```yaml
# Network policy restricting access to configuration services
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: config-access-policy
  namespace: production
spec:
  podSelector:
    matchLabels:
      app: web-application
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: monitoring
    - podSelector:
        matchLabels:
          app: ingress-controller
    ports:
    - protocol: TCP
      port: 8080
  egress:
  - to:
    - namespaceSelector:
        matchLabels:
          name: database
    ports:
    - protocol: TCP
      port: 5432
  - to:
    - namespaceSelector:
        matchLabels:
          name: cache
    ports:
    - protocol: TCP
      port: 6379
  - to: []  # DNS
    ports:
    - protocol: UDP
      port: 53
```

---

## Production Patterns

### Multi-Environment Configuration

```yaml
# Base ConfigMap
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-base-config
data:
  log.format: "json"
  metrics.enabled: "true"
  health.endpoint: "/health"
---
# Environment-specific overlay (production)
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-production-config
data:
  log.level: "WARN"
  database.pool.size: "20"
  cache.ttl: "3600"
  feature.flags: |
    {
      "new-feature": true,
      "beta-feature": false,
      "debug-mode": false
    }
---
# Environment-specific overlay (development)
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-development-config
data:
  log.level: "DEBUG"
  database.pool.size: "5"
  cache.ttl: "300"
  feature.flags: |
    {
      "new-feature": true,
      "beta-feature": true,
      "debug-mode": true
    }
```

### Configuration Validation

```yaml
# Init container for configuration validation
apiVersion: apps/v1
kind: Deployment
metadata:
  name: validated-app
spec:
  template:
    spec:
      initContainers:
      - name: config-validator
        image: config-validator:latest
        command: ['sh', '-c']
        args:
        - |
          echo "Validating configuration..."

          # Validate required environment variables
          if [ -z "$DATABASE_HOST" ]; then
            echo "ERROR: DATABASE_HOST not set"
            exit 1
          fi

          # Validate configuration files
          if ! nginx -t -c /etc/nginx/nginx.conf; then
            echo "ERROR: Invalid nginx configuration"
            exit 1
          fi

          # Validate JSON configuration
          if ! jq empty /etc/config/feature.flags; then
            echo "ERROR: Invalid JSON in feature flags"
            exit 1
          fi

          echo "Configuration validation passed"
        env:
        - name: DATABASE_HOST
          valueFrom:
            configMapKeyRef:
              name: app-config
              key: database.host
        volumeMounts:
        - name: config-volume
          mountPath: /etc/config
        - name: nginx-config
          mountPath: /etc/nginx
      containers:
      - name: app
        image: app:latest
        # ... main container configuration
```

### ConfigMap and Secret Reloading

```yaml
# Deployment with configuration reload sidecar
apiVersion: apps/v1
kind: Deployment
metadata:
  name: reloadable-app
spec:
  template:
    metadata:
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "9090"
    spec:
      containers:
      - name: app
        image: app:latest
        ports:
        - containerPort: 8080
        volumeMounts:
        - name: config-volume
          mountPath: /etc/config
        - name: reload-trigger
          mountPath: /etc/reload
      - name: config-reloader
        image: jimmidyson/configmap-reload:latest
        args:
        - --volume-dir=/etc/config
        - --webhook-url=http://localhost:8080/reload
        - --webhook-method=POST
        volumeMounts:
        - name: config-volume
          mountPath: /etc/config
          readOnly: true
        resources:
          requests:
            memory: 32Mi
            cpu: 10m
          limits:
            memory: 64Mi
            cpu: 50m
      volumes:
      - name: config-volume
        configMap:
          name: app-config
      - name: reload-trigger
        emptyDir: {}
```

---

## Troubleshooting

### Configuration Debugging Commands

```bash
# Check ConfigMaps and Secrets
kubectl get configmaps,secrets -n production
kubectl describe configmap app-config -n production
kubectl describe secret app-secrets -n production

# View ConfigMap/Secret data
kubectl get configmap app-config -o yaml -n production
kubectl get secret app-secrets -o yaml -n production

# Decode secret values
kubectl get secret app-secrets -o jsonpath='{.data.password}' -n production | base64 --decode

# Check resource quotas and limits
kubectl describe quota -n production
kubectl describe limitrange -n production

# Check namespace resource usage
kubectl top pods -n production
kubectl top nodes --show-capacity

# Test configuration in pod
kubectl run debug-pod --image=busybox --rm -it --restart=Never -- sh
kubectl exec -it pod-name -- printenv | grep CONFIG
kubectl exec -it pod-name -- ls -la /etc/config/
kubectl exec -it pod-name -- cat /etc/config/app.properties
```

### Configuration Validation Issues

```yaml
# Debug pod for configuration testing
apiVersion: v1
kind: Pod
metadata:
  name: config-debug
  namespace: production
spec:
  containers:
  - name: debug
    image: busybox:latest
    command: ['sleep', '3600']
    env:
    - name: DEBUG_MODE
      value: "true"
    envFrom:
    - configMapRef:
        name: app-config
    - secretRef:
        name: app-secrets
    volumeMounts:
    - name: config-volume
      mountPath: /etc/config
    - name: secret-volume
      mountPath: /etc/secrets
  volumes:
  - name: config-volume
    configMap:
      name: app-config
  - name: secret-volume
    secret:
      secretName: app-secrets
  restartPolicy: Never
```

### Resource Quota Debugging

```bash
# Check quota usage
kubectl describe quota -n production

# View resource consumption by pod
kubectl top pods -n production --sort-by=memory
kubectl top pods -n production --sort-by=cpu

# Check failed pod creation due to quotas
kubectl get events -n production --field-selector reason=FailedCreate

# Inspect resource requests and limits
kubectl get pods -n production -o custom-columns=NAME:.metadata.name,MEMORY_REQ:.spec.containers[*].resources.requests.memory,MEMORY_LIM:.spec.containers[*].resources.limits.memory,CPU_REQ:.spec.containers[*].resources.requests.cpu,CPU_LIM:.spec.containers[*].resources.limits.cpu
```

---

## Cross-References

**Related Documentation:**
- [Kubernetes Security](Kubernetes%20Security.md) - RBAC, Pod Security Standards, and access control
- [Kubernetes Production Best Practices](Kubernetes%20Production%20Best%20Practices.md) - Configuration management in production environments
- [Kubernetes Workload Controllers](Kubernetes%20Workload%20Controllers.md) - Deployment patterns with configuration management
- [Kubernetes Troubleshooting](Kubernetes%20Troubleshooting.md) - Configuration-related debugging techniques

**Configuration Patterns:**
- **Environment Separation**: Namespace-based isolation with environment-specific configurations
- **Secret Management**: External secret integration with rotation strategies
- **Resource Control**: Quota and limit management for multi-tenant environments
- **Security Hardening**: Secure configuration injection and access control

**Best Practices Summary:**
- Separate sensitive data in Secrets from non-sensitive data in ConfigMaps
- Use external secret management systems for production environments
- Implement proper RBAC for configuration access
- Apply resource quotas and limits to prevent resource exhaustion
- Use immutable ConfigMaps for critical configuration data
- Validate configuration before deployment
- Implement configuration reload mechanisms for zero-downtime updates
- Monitor configuration changes and access patterns