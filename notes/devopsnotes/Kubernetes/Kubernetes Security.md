## Security Comprehensive Deep Dive

### RBAC (Role-Based Access Control) Implementation

RBAC provides fine-grained access control to Kubernetes resources using roles and bindings.

#### Core RBAC Components

**1. Role (Namespace-scoped permissions):**

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: development
  name: pod-reader
rules:
- apiGroups: [""]
  resources: ["pods"]
  verbs: ["get", "watch", "list"]
- apiGroups: [""]
  resources: ["pods/log"]
  verbs: ["get", "list"]
- apiGroups: ["apps"]
  resources: ["deployments", "replicasets"]
  verbs: ["get", "list", "watch"]
```

**2. ClusterRole (Cluster-wide permissions):**

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: node-reader
rules:
- apiGroups: [""]
  resources: ["nodes"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["metrics.k8s.io"]
  resources: ["nodes", "pods"]
  verbs: ["get", "list"]
```

**3. RoleBinding (Assigns Role to subjects in namespace):**

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: read-pods
  namespace: development
subjects:
- kind: User
  name: jane@company.com
  apiGroup: rbac.authorization.k8s.io
- kind: ServiceAccount
  name: pod-reader
  namespace: development
- kind: Group
  name: developers
  apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: Role
  name: pod-reader
  apiGroup: rbac.authorization.k8s.io
```

**4. ClusterRoleBinding (Assigns ClusterRole to subjects cluster-wide):**

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: read-nodes
subjects:
- kind: User
  name: monitoring@company.com
  apiGroup: rbac.authorization.k8s.io
- kind: ServiceAccount
  name: monitoring-agent
  namespace: monitoring
roleRef:
  kind: ClusterRole
  name: node-reader
  apiGroup: rbac.authorization.k8s.io
```

#### Advanced RBAC Patterns

**DevOps Team Role (Comprehensive permissions):**

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: devops-admin
rules:
# Core resources
- apiGroups: [""]
  resources: ["*"]
  verbs: ["*"]
# Apps resources
- apiGroups: ["apps"]
  resources: ["*"]
  verbs: ["*"]
# Networking
- apiGroups: ["networking.k8s.io"]
  resources: ["*"]
  verbs: ["*"]
# Storage
- apiGroups: ["storage.k8s.io"]
  resources: ["*"]
  verbs: ["*"]
# RBAC (limited)
- apiGroups: ["rbac.authorization.k8s.io"]
  resources: ["roles", "rolebindings"]
  verbs: ["*"]
# Exclude cluster-level RBAC
- apiGroups: ["rbac.authorization.k8s.io"]
  resources: ["clusterroles", "clusterrolebindings"]
  verbs: ["get", "list", "watch"]
```

**Developer Role (Limited permissions):**

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: development
  name: developer
rules:
- apiGroups: [""]
  resources: ["pods", "pods/log", "pods/exec"]
  verbs: ["create", "delete", "get", "list", "patch", "update", "watch"]
- apiGroups: [""]
  resources: ["configmaps", "secrets"]
  verbs: ["create", "delete", "get", "list", "patch", "update", "watch"]
- apiGroups: ["apps"]
  resources: ["deployments", "replicasets"]
  verbs: ["create", "delete", "get", "list", "patch", "update", "watch"]
- apiGroups: [""]
  resources: ["services", "endpoints"]
  verbs: ["create", "delete", "get", "list", "patch", "update", "watch"]
# Deny dangerous operations
- apiGroups: [""]
  resources: ["nodes"]
  verbs: ["get", "list", "watch"]
  resourceNames: [] # No access to modify nodes
```

#### Service Account Security

**Enhanced Service Account Configuration:**

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: app-service-account
  namespace: production
  annotations:
    kubernetes.io/description: "Service account for production application"
automountServiceAccountToken: false  # Disable automatic token mounting
---
# Custom token with expiration
apiVersion: v1
kind: Secret
metadata:
  name: app-service-account-token
  namespace: production
  annotations:
    kubernetes.io/service-account.name: app-service-account
type: kubernetes.io/service-account-token
```

**Pod with Service Account:**

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: secure-app-pod
  namespace: production
spec:
  serviceAccountName: app-service-account
  automountServiceAccountToken: true  # Explicitly enable if needed
  containers:
  - name: app
    image: myapp:latest
    env:
    - name: KUBERNETES_SERVICE_ACCOUNT
      value: app-service-account
```

### Pod Security Standards

Pod Security Standards replace Pod Security Policies in Kubernetes 1.25+.

#### Security Profiles

**1. Privileged Profile (Most permissive):**

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: privileged-apps
  labels:
    pod-security.kubernetes.io/enforce: privileged
    pod-security.kubernetes.io/audit: privileged
    pod-security.kubernetes.io/warn: privileged
```

**2. Baseline Profile (Balanced security):**

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: standard-apps
  labels:
    pod-security.kubernetes.io/enforce: baseline
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/warn: restricted
```

**3. Restricted Profile (Maximum security):**

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: secure-apps
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/warn: restricted
    pod-security.kubernetes.io/enforce-version: v1.28
```

#### Compliant Pod Configurations

**Baseline-compliant Pod:**

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: baseline-pod
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 1000
    fsGroup: 2000
    seccompProfile:
      type: RuntimeDefault
  containers:
  - name: app
    image: nginx:1.21
    securityContext:
      allowPrivilegeEscalation: false
      capabilities:
        drop:
        - ALL
        add:
        - NET_BIND_SERVICE  # Only specific capabilities
      readOnlyRootFilesystem: true
    resources:
      requests:
        memory: "64Mi"
        cpu: "250m"
      limits:
        memory: "128Mi"
        cpu: "500m"
```

**Restricted-compliant Pod:**

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: restricted-pod
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
    image: nginx:1.21
    securityContext:
      allowPrivilegeEscalation: false
      capabilities:
        drop:
        - ALL
      readOnlyRootFilesystem: true
      runAsNonRoot: true
      runAsUser: 1000
      seccompProfile:
        type: RuntimeDefault
    resources:
      requests:
        memory: "64Mi"
        cpu: "250m"
      limits:
        memory: "128Mi"
        cpu: "500m"
    volumeMounts:
    - name: cache-volume
      mountPath: /cache
    - name: tmp-volume
      mountPath: /tmp
  volumes:
  - name: cache-volume
    emptyDir: {}
  - name: tmp-volume
    emptyDir: {}
```

### Security Context Deep Dive

**Container Security Context:**

```yaml
securityContext:
  # User and group settings
  runAsUser: 1000
  runAsGroup: 3000
  runAsNonRoot: true
  
  # Filesystem settings
  readOnlyRootFilesystem: true
  
  # Privilege settings
  allowPrivilegeEscalation: false
  privileged: false
  
  # Capabilities
  capabilities:
    drop:
    - ALL
    add:
    - NET_BIND_SERVICE
    - SYS_TIME
  
  # Security profiles
  seccompProfile:
    type: RuntimeDefault
  seLinuxOptions:
    level: "s0:c123,c456"
  windowsOptions:
    gmsaCredentialSpec: "credspec-name"
```

**Pod Security Context:**

```yaml
spec:
  securityContext:
    runAsUser: 1000
    runAsGroup: 3000
    runAsNonRoot: true
    fsGroup: 2000
    fsGroupChangePolicy: "OnRootMismatch"
    seccompProfile:
      type: RuntimeDefault
    supplementalGroups:
    - 1000
    - 2000
```

### Network Security with Network Policies

**Default Deny All Network Policy:**

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
  namespace: production
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
```

**Database Access Control:**

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: database-access
  namespace: production
spec:
  podSelector:
    matchLabels:
      tier: database
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: backend
    - podSelector:
        matchLabels:
          app: api-server
    ports:
    - protocol: TCP
      port: 5432
  egress:
  - to: []  # Allow DNS
    ports:
    - protocol: TCP
      port: 53
    - protocol: UDP
      port: 53
```

### Image Security

**Image Scanning and Admission Controllers:**

```yaml
apiVersion: admissionregistration.k8s.io/v1
kind: ValidatingAdmissionWebhook
metadata:
  name: image-security-webhook
webhooks:
- name: image-scanner.security.company.com
  clientConfig:
    service:
      name: image-scanner-service
      namespace: security-system
      path: "/validate"
  rules:
  - operations: ["CREATE", "UPDATE"]
    apiGroups: [""]
    apiVersions: ["v1"]
    resources: ["pods"]
  admissionReviewVersions: ["v1", "v1beta1"]
```

**Secure Image Pull:**

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: secure-image-pod
spec:
  containers:
  - name: app
    image: registry.company.com/secure-app:v1.2.3@sha256:abc123...
    imagePullPolicy: Always
  imagePullSecrets:
  - name: registry-credentials
```

### Secret Management and Encryption

**External Secrets Operator with Vault:**

```yaml
apiVersion: external-secrets.io/v1beta1
kind: SecretStore
metadata:
  name: vault-secretstore
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
          role: "myapp-role"
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
    name: vault-secretstore
    kind: SecretStore
  target:
    name: app-secret
    creationPolicy: Owner
  data:
  - secretKey: database-password
    remoteRef:
      key: secret/myapp
      property: db_password
```

**Sealed Secrets for GitOps:**

```yaml
apiVersion: bitnami.com/v1alpha1
kind: SealedSecret
metadata:
  name: app-secret
  namespace: production
spec:
  encryptedData:
    password: AgBy3i4OJSWK+PiTySYZZA9rO43cGDEQAx...
  template:
    metadata:
      name: app-secret
      namespace: production
    type: Opaque
```

### Runtime Security

**Falco Runtime Security Rules:**

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: falco-rules
data:
  custom_rules.yaml: |
    - rule: Detect shell in container
      desc: Detect shell spawned in container
      condition: >
        spawned_process and container and
        shell_procs and proc.pname exists
      output: >
        Shell spawned in container (user=%user.name container=%container.name
        shell=%proc.name parent=%proc.pname cmdline=%proc.cmdline)
      priority: WARNING
      
    - rule: Detect suspicious network activity
      desc: Detect suspicious network connections
      condition: >
        inbound_outbound and fd.typechar=4 and
        (fd.net.proto=tcp or fd.net.proto=udp) and
        not trusted_network_connections
      output: >
        Suspicious network activity (user=%user.name command=%proc.cmdline
        connection=%fd.name)
      priority: WARNING
```

### Security Hardening Checklist

#### Cluster Hardening

**1. API Server Security:**

```bash
# Enable audit logging
kube-apiserver \
  --audit-log-path=/var/log/audit.log \
  --audit-policy-file=/etc/kubernetes/audit-policy.yaml \
  --audit-log-maxage=30 \
  --audit-log-maxbackup=3 \
  --audit-log-maxsize=100

# Enable admission controllers
kube-apiserver \
  --enable-admission-plugins=NodeRestriction,PodSecurityPolicy,ServiceAccount \
  --disable-admission-plugins=AlwaysAdmit
```

**2. etcd Security:**

```bash
# Enable TLS for etcd
etcd \
  --cert-file=/etc/kubernetes/pki/etcd/server.crt \
  --key-file=/etc/kubernetes/pki/etcd/server.key \
  --trusted-ca-file=/etc/kubernetes/pki/etcd/ca.crt \
  --client-cert-auth=true
```

**3. kubelet Security:**

```yaml
apiVersion: kubelet.config.k8s.io/v1beta1
kind: KubeletConfiguration
authentication:
  webhook:
    enabled: true
authorization:
  mode: Webhook
serverTLSBootstrap: true
readOnlyPort: 0
```

#### DevOps Security Best Practices

**1. Image Security:**
- Use minimal base images (distroless, alpine)
- Scan images for vulnerabilities regularly
- Sign images with cosign or notary
- Use specific image tags, not latest
- Implement image pull policies

**2. Secrets Management:**
- Never commit secrets to version control
- Use external secret management systems
- Rotate secrets regularly
- Implement least privilege access
- Encrypt secrets at rest

**3. Network Security:**
- Implement network policies by default
- Use service mesh for advanced traffic control
- Segment networks by trust zones
- Monitor and log network traffic
- Implement egress filtering

**4. Access Control:**
- Implement RBAC with least privilege
- Use service accounts for applications
- Audit access regularly
- Implement multi-factor authentication
- Monitor suspicious activities

**5. Monitoring and Compliance:**
- Implement comprehensive logging
- Monitor for security events
- Regular security scanning
- Compliance reporting
- Incident response procedures

### Legacy Examples

**Basic RBAC Role:**

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: development
  name: pod-reader
rules:
- apiGroups: [""]
  resources: ["pods"]
  verbs: ["get", "watch", "list"]
```

**Basic Service Account:**

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: app-service-account
  namespace: default
---
apiVersion: v1
kind: Pod
metadata:
  name: app-pod
spec:
  serviceAccountName: app-service-account
  containers:
  - name: app
    image: myapp:latest
```

**Basic Security Context:**

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: secure-pod
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 1000
    fsGroup: 2000
  containers:
  - name: app
    image: nginx
    securityContext:
      allowPrivilegeEscalation: false
      readOnlyRootFilesystem: true
      capabilities:
        drop:
        - ALL
```
