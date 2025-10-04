# kube-apiserver

## Overview

The **kube-apiserver** is the central hub and front-end for the Kubernetes control plane. Every operation in Kubernetes - whether from kubectl, CI/CD pipelines, controllers, schedulers, or external tools - goes through the API server. It's the only component that directly communicates with etcd and serves as the single source of truth for cluster state.

**Component Type:** Control Plane
**Process Name:** `kube-apiserver`
**Default Port:** 6443 (HTTPS)
**Runs On:** Control plane nodes (master nodes)
**Stateless:** Yes (state stored in etcd)

## What API Server Actually Does

Think of the API server as a highly secure REST API gateway combined with a database proxy and event broadcaster.

### Real-World Analogy
Imagine a bank's main server:
- **Authentication/Authorization:** Verifies your identity and permissions
- **Request Validation:** Ensures transactions follow rules
- **Database Operations:** Reads/writes to secure vault (etcd)
- **Notifications:** Alerts relevant parties about account changes
- **Audit Trail:** Logs every transaction

### Core Functions

**1. Request Processing Pipeline**
```
kubectl create pod → API Server → Authenticate → Authorize → Validate →
Admission Control → Write to etcd → Notify Scheduler → Response
```

**2. State Management**
- Only component that reads/writes to etcd
- Validates all resource specifications
- Maintains consistency across cluster
- Handles optimistic concurrency control

**3. Watch Mechanism (Critical for Kubernetes)**
- Controllers watch for resource changes (e.g., ReplicaSet watches Pods)
- Uses long-polling HTTP connections
- Efficient change notifications without polling
- Enables real-time cluster automation

**4. API Versioning**
- Supports multiple API versions simultaneously (v1, v1beta1, v1alpha1)
- Allows gradual migration from deprecated APIs
- Converts between API versions transparently

## Architecture Deep Dive

### Request Flow

```
┌─────────────────────────────────────────────────────────────┐
│                        Client Request                        │
│          (kubectl, controller, scheduler, webhook)           │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│                      Authentication                          │
│  • Client certificates                                       │
│  • Bearer tokens (ServiceAccount, OIDC)                     │
│  • Bootstrap tokens                                          │
│  • Authentication webhooks                                   │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│                      Authorization                           │
│  • RBAC (Role-Based Access Control)                         │
│  • Node authorization (kubelet access)                       │
│  • Webhook authorization (external policy engine)           │
│  • ABAC (Attribute-Based Access Control - deprecated)       │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│                   Admission Controllers                      │
│  Mutating Admission Webhooks (modify request)               │
│  • Inject sidecars (Istio, Dapr)                           │
│  • Add default values                                        │
│  • Modify security contexts                                  │
│                                                              │
│  Validating Admission Webhooks (validate request)           │
│  • Policy enforcement (OPA, Kyverno)                        │
│  • Security scanning (Falco, Twistlock)                     │
│  • Custom business logic                                     │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│                        Validation                            │
│  • Schema validation (OpenAPI)                              │
│  • Field validation (required fields, types)                │
│  • Cross-field validation (e.g., limits > requests)         │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│                    Persistence (etcd)                        │
│  • Optimistic concurrency (resourceVersion)                 │
│  • Watch cache (reduce etcd load)                           │
│  • Encryption at rest (optional)                            │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│                  Response & Watch Events                     │
│  • Return response to client                                │
│  • Notify watchers (controllers, operators)                 │
│  • Trigger reconciliation loops                             │
└─────────────────────────────────────────────────────────────┘
```

### How Controllers Use API Server

```go
// Example: Deployment Controller watching ReplicaSets
watch, err := clientset.AppsV1().ReplicaSets(namespace).Watch(ctx, metav1.ListOptions{})
for event := range watch.ResultChan() {
    rs := event.Object.(*appsv1.ReplicaSet)
    switch event.Type {
    case watch.Added:
        // Handle new ReplicaSet
    case watch.Modified:
        // Handle ReplicaSet update
    case watch.Deleted:
        // Handle ReplicaSet deletion
    }
}
```

## Installation and Configuration

### Static Pod Manifest (Most Common - kubeadm)

```yaml
# /etc/kubernetes/manifests/kube-apiserver.yaml
apiVersion: v1
kind: Pod
metadata:
  annotations:
    kubeadm.kubernetes.io/kube-apiserver.advertise-address.endpoint: 10.0.0.10:6443
  labels:
    component: kube-apiserver
    tier: control-plane
  name: kube-apiserver
  namespace: kube-system
spec:
  containers:
  - command:
    - kube-apiserver

    # ==================== ETCD Configuration ====================
    # Connection to etcd cluster
    - --etcd-servers=https://10.0.0.10:2379,https://10.0.0.11:2379,https://10.0.0.12:2379
    - --etcd-cafile=/etc/kubernetes/pki/etcd/ca.crt
    - --etcd-certfile=/etc/kubernetes/pki/apiserver-etcd-client.crt
    - --etcd-keyfile=/etc/kubernetes/pki/apiserver-etcd-client.key
    # etcd prefix for Kubernetes data (default: /registry)
    - --etcd-prefix=/registry
    # Timeout for etcd requests (default: 5s)
    - --etcd-servers-overrides=/events#https://etcd-events:2379  # Separate etcd for events

    # ==================== TLS & Certificates ====================
    # API Server TLS certificate (for HTTPS)
    - --tls-cert-file=/etc/kubernetes/pki/apiserver.crt
    - --tls-private-key-file=/etc/kubernetes/pki/apiserver.key
    # Client CA for authenticating clients
    - --client-ca-file=/etc/kubernetes/pki/ca.crt
    # Kubelet client certificates (API server → kubelet)
    - --kubelet-client-certificate=/etc/kubernetes/pki/apiserver-kubelet-client.crt
    - --kubelet-client-key=/etc/kubernetes/pki/apiserver-kubelet-client.key
    - --kubelet-certificate-authority=/etc/kubernetes/pki/ca.crt
    - --kubelet-preferred-address-types=InternalIP,ExternalIP,Hostname

    # ==================== Service Account Tokens ====================
    # Service account key for signing/verifying tokens
    - --service-account-key-file=/etc/kubernetes/pki/sa.pub
    - --service-account-signing-key-file=/etc/kubernetes/pki/sa.key
    - --service-account-issuer=https://kubernetes.default.svc.cluster.local
    # Service account token max age (default: 1h, extended tokens: true)
    - --service-account-extend-token-expiration=true
    # Multiple issuers for migration
    - --service-account-issuer=https://my-cluster.example.com
    # API audiences (who can use the tokens)
    - --api-audiences=https://kubernetes.default.svc.cluster.local

    # ==================== Authentication ====================
    # Enable bootstrap tokens (for node joining)
    - --enable-bootstrap-token-auth=true
    # Disable anonymous requests (SECURITY)
    - --anonymous-auth=false
    # OIDC authentication (Google, Okta, Keycloak, Dex)
    - --oidc-issuer-url=https://accounts.google.com
    - --oidc-client-id=kubernetes
    - --oidc-username-claim=email
    - --oidc-username-prefix=oidc:
    - --oidc-groups-claim=groups
    - --oidc-groups-prefix=oidc:
    - --oidc-ca-file=/etc/kubernetes/oidc-ca.crt
    # Token file authentication (legacy)
    # --token-auth-file=/etc/kubernetes/tokens.csv
    # Basic auth (DEPRECATED - DO NOT USE)
    # --basic-auth-file=/etc/kubernetes/basic-auth.csv

    # ==================== Authorization ====================
    # Authorization modes (evaluated in order)
    - --authorization-mode=Node,RBAC
    # Node: kubelet can only access resources for its own node
    # RBAC: Role-Based Access Control (production standard)
    # Webhook: external authorization service
    # --authorization-mode=Node,RBAC,Webhook
    # --authorization-webhook-config-file=/etc/kubernetes/webhook-authz.yaml
    # --authorization-webhook-cache-authorized-ttl=5m
    # --authorization-webhook-cache-unauthorized-ttl=30s

    # ==================== Admission Controllers ====================
    # Critical admission plugins for production
    - --enable-admission-plugins=NodeRestriction,PodSecurity,NamespaceLifecycle,LimitRanger,ServiceAccount,DefaultStorageClass,DefaultTolerationSeconds,MutatingAdmissionWebhook,ValidatingAdmissionWebhook,ResourceQuota,Priority,PersistentVolumeClaimResize,StorageObjectInUseProtection,RuntimeClass,CertificateApproval,CertificateSigning,CertificateSubjectRestriction,TaintNodesByCondition

    # Pod Security Admission (replaces PodSecurityPolicy in 1.25+)
    - --admission-control-config-file=/etc/kubernetes/admission-config.yaml

    # Disable specific plugins if needed
    # --disable-admission-plugins=ServiceAccount

    # ==================== API Server Settings ====================
    # Advertise address (external IP for HA)
    - --advertise-address=10.0.0.10
    # Bind to all interfaces (0.0.0.0) or specific IP
    - --bind-address=0.0.0.0
    # HTTPS port
    - --secure-port=6443
    # HTTP port (DISABLED for security)
    - --insecure-port=0

    # ==================== Service & Pod Networks ====================
    # Service CIDR (ClusterIP range)
    - --service-cluster-ip-range=10.96.0.0/12
    # NodePort range (default: 30000-32767)
    - --service-node-port-range=30000-32767

    # ==================== API Aggregation Layer ====================
    # For metrics-server, custom API servers
    - --requestheader-client-ca-file=/etc/kubernetes/pki/front-proxy-ca.crt
    - --requestheader-allowed-names=front-proxy-client
    - --requestheader-extra-headers-prefix=X-Remote-Extra-
    - --requestheader-group-headers=X-Remote-Group
    - --requestheader-username-headers=X-Remote-User
    - --proxy-client-cert-file=/etc/kubernetes/pki/front-proxy-client.crt
    - --proxy-client-key-file=/etc/kubernetes/pki/front-proxy-client.key
    - --enable-aggregator-routing=true

    # ==================== Performance & Scalability ====================
    # Max concurrent read requests (default: 400)
    - --max-requests-inflight=800
    # Max concurrent write requests (default: 200)
    - --max-mutating-requests-inflight=400
    # Request timeout (default: 60s)
    - --request-timeout=60s
    # Min timeout for long-running requests like watch (default: 1800s)
    - --min-request-timeout=1800
    # Watch cache (improves list/watch performance)
    - --watch-cache=true
    # Watch cache sizes per resource
    - --watch-cache-sizes=persistentvolumes#1000,persistentvolumeclaims#1000,nodes#1000,pods#5000
    # Target memory for watch caches (MB)
    - --target-ram-mb=1000
    # Default watch cache size (default: 100)
    - --default-watch-cache-size=200

    # ==================== Audit Logging ====================
    # Audit log file path
    - --audit-log-path=/var/log/kubernetes/audit/audit.log
    # Max days to retain logs
    - --audit-log-maxage=30
    # Max backup files
    - --audit-log-maxbackup=10
    # Max size in MB before rotation
    - --audit-log-maxsize=100
    # Audit policy configuration
    - --audit-policy-file=/etc/kubernetes/audit-policy.yaml
    # Audit webhook backend (send to external system)
    # --audit-webhook-config-file=/etc/kubernetes/audit-webhook.yaml
    # --audit-webhook-batch-max-size=100
    # --audit-webhook-batch-max-wait=5s

    # ==================== Encryption at Rest ====================
    # Encrypt secrets, configmaps in etcd
    - --encryption-provider-config=/etc/kubernetes/encryption-config.yaml

    # ==================== Feature Gates ====================
    # Enable/disable alpha/beta features
    - --feature-gates=
    # Example: ServerSideApply=true,EphemeralContainers=true

    # ==================== Event Rate Limiting ====================
    # Prevent event storms from overwhelming etcd
    - --event-ttl=1h

    # ==================== Logging ====================
    # Log verbosity (0-10, production: 2)
    - --v=2
    # Log to stderr
    - --logtostderr=true
    # Log file (if not using stderr)
    # --log-file=/var/log/kube-apiserver.log

    # ==================== Profiling & Debugging ====================
    # Enable profiling endpoint /debug/pprof (disable in production)
    - --profiling=false
    # Enable contention profiling
    - --contention-profiling=false

    # ==================== API Priority & Fairness ====================
    # Better than rate limiting, per-user flow control
    - --enable-priority-and-fairness=true
    # --max-requests-inflight and --max-mutating-requests-inflight still apply as global limits

    # ==================== Storage Versions ====================
    # Ensure consistent storage versions
    - --storage-backend=etcd3
    # Storage media type (application/vnd.kubernetes.protobuf is faster than JSON)
    - --storage-media-type=application/vnd.kubernetes.protobuf

    image: registry.k8s.io/kube-apiserver:v1.28.0
    imagePullPolicy: IfNotPresent

    # ==================== Health Probes ====================
    livenessProbe:
      failureThreshold: 8
      httpGet:
        host: 10.0.0.10
        path: /livez
        port: 6443
        scheme: HTTPS
      initialDelaySeconds: 10
      periodSeconds: 10
      timeoutSeconds: 15

    readinessProbe:
      failureThreshold: 3
      httpGet:
        host: 10.0.0.10
        path: /readyz
        port: 6443
        scheme: HTTPS
      periodSeconds: 1
      timeoutSeconds: 15

    startupProbe:
      failureThreshold: 24
      httpGet:
        host: 10.0.0.10
        path: /livez
        port: 6443
        scheme: HTTPS
      initialDelaySeconds: 10
      periodSeconds: 10
      timeoutSeconds: 15

    name: kube-apiserver

    # ==================== Resource Limits ====================
    resources:
      requests:
        cpu: 250m
        memory: 512Mi
      limits:
        # No CPU limit (avoid throttling critical component)
        memory: 2Gi

    # ==================== Volume Mounts ====================
    volumeMounts:
    - mountPath: /etc/ssl/certs
      name: ca-certs
      readOnly: true
    - mountPath: /etc/kubernetes/pki
      name: k8s-certs
      readOnly: true
    - mountPath: /var/log/kubernetes/audit
      name: audit-logs
    - mountPath: /etc/kubernetes/audit-policy.yaml
      name: audit-policy
      readOnly: true
    - mountPath: /etc/kubernetes/encryption-config.yaml
      name: encryption-config
      readOnly: true
    - mountPath: /etc/kubernetes/admission-config.yaml
      name: admission-config
      readOnly: true

  hostNetwork: true
  priorityClassName: system-node-critical
  securityContext:
    seccompProfile:
      type: RuntimeDefault

  # ==================== Volumes ====================
  volumes:
  - hostPath:
      path: /etc/ssl/certs
      type: DirectoryOrCreate
    name: ca-certs
  - hostPath:
      path: /etc/kubernetes/pki
      type: DirectoryOrCreate
    name: k8s-certs
  - hostPath:
      path: /var/log/kubernetes/audit
      type: DirectoryOrCreate
    name: audit-logs
  - hostPath:
      path: /etc/kubernetes/audit-policy.yaml
      type: File
    name: audit-policy
  - hostPath:
      path: /etc/kubernetes/encryption-config.yaml
      type: File
    name: encryption-config
  - hostPath:
      path: /etc/kubernetes/admission-config.yaml
      type: File
    name: admission-config
```

## Critical Configuration Files

### Audit Policy Configuration

```yaml
# /etc/kubernetes/audit-policy.yaml
apiVersion: audit.k8s.io/v1
kind: Policy
omitStages:
  - RequestReceived

rules:
# ==================== Don't Log (Reduce Noise) ====================
# Don't log read-only requests (get, list, watch)
- level: None
  verbs: ["get", "list", "watch"]

# Don't log system components (reduce noise)
- level: None
  users:
  - system:kube-proxy
  - system:kube-scheduler
  - system:kube-controller-manager
  userGroups:
  - system:nodes

# Don't log health checks
- level: None
  nonResourceURLs:
  - /healthz*
  - /livez*
  - /readyz*
  - /metrics
  - /version

# ==================== Metadata Level (Log Request Info) ====================
# Log configmap/secret reads at metadata level (who accessed what)
- level: Metadata
  verbs: ["get", "list", "watch"]
  resources:
  - group: ""
    resources: ["secrets", "configmaps"]

# ==================== Request Level (Log Request Body) ====================
# Log all secret/configmap changes with request body
- level: Request
  verbs: ["create", "update", "patch", "delete"]
  resources:
  - group: ""
    resources: ["secrets", "configmaps"]

# Log RBAC changes (roles, rolebindings, clusterroles, clusterrolebindings)
- level: RequestResponse
  verbs: ["create", "update", "patch", "delete"]
  resources:
  - group: "rbac.authorization.k8s.io"
    resources: ["roles", "rolebindings", "clusterroles", "clusterrolebindings"]

# Log pod exec/attach/portforward (security critical)
- level: RequestResponse
  verbs: ["create"]
  resources:
  - group: ""
    resources: ["pods/exec", "pods/attach", "pods/portforward"]

# Log all authentication token requests
- level: RequestResponse
  verbs: ["create"]
  resources:
  - group: "authentication.k8s.io"
    resources: ["tokenreviews"]

# ==================== Namespace-Specific Logging ====================
# Detailed logging for production namespace
- level: RequestResponse
  namespaces: ["production"]
  verbs: ["create", "update", "patch", "delete"]

# ==================== Default Catch-All ====================
# Log everything else at Metadata level
- level: Metadata
  omitStages:
  - RequestReceived
```

### Encryption at Rest Configuration

```yaml
# /etc/kubernetes/encryption-config.yaml
apiVersion: apiserver.config.k8s.io/v1
kind: EncryptionConfiguration
resources:
# Encrypt secrets
- resources:
  - secrets
  providers:
  # Primary encryption method (used for new writes)
  - aescbc:
      keys:
      - name: key1
        secret: <base64-encoded-32-byte-key>
  # Secondary key (for key rotation)
  - aescbc:
      keys:
      - name: key2
        secret: <base64-encoded-32-byte-key>
  # Fallback identity (for reading old unencrypted data)
  - identity: {}

# Encrypt configmaps
- resources:
  - configmaps
  providers:
  - aescbc:
      keys:
      - name: key1
        secret: <base64-encoded-32-byte-key>
  - identity: {}
```

**Generate encryption key:**
```bash
head -c 32 /dev/urandom | base64
# Example output: r3FyN2xXNGhKcjZkN3NrOGZhc2RmYXNkZmFzZGZh
```

**Encrypt existing secrets:**
```bash
# After enabling encryption, re-encrypt all existing secrets
kubectl get secrets --all-namespaces -o json | kubectl replace -f -
```

**Key rotation process:**
```bash
# 1. Add new key as first entry in encryption config
# 2. Restart API server
# 3. Re-encrypt all secrets with new key
kubectl get secrets --all-namespaces -o json | kubectl replace -f -
# 4. Remove old key from encryption config after verification
```

### Pod Security Admission Configuration

```yaml
# /etc/kubernetes/admission-config.yaml
apiVersion: apiserver.config.k8s.io/v1
kind: AdmissionConfiguration
plugins:
- name: PodSecurity
  configuration:
    apiVersion: pod-security.admission.config.k8s.io/v1
    kind: PodSecurityConfiguration
    defaults:
      enforce: "baseline"
      enforce-version: "latest"
      audit: "restricted"
      audit-version: "latest"
      warn: "restricted"
      warn-version: "latest"
    exemptions:
      usernames: []
      runtimeClasses: []
      namespaces: ["kube-system", "kube-public", "kube-node-lease"]
```

### Webhook Authorization Configuration

```yaml
# /etc/kubernetes/webhook-authz.yaml
apiVersion: v1
kind: Config
clusters:
- name: authz-webhook
  cluster:
    certificate-authority: /etc/kubernetes/pki/authz-ca.crt
    server: https://authz.example.com:8443/authorize

users:
- name: apiserver
  user:
    client-certificate: /etc/kubernetes/pki/apiserver.crt
    client-key: /etc/kubernetes/pki/apiserver.key

current-context: webhook
contexts:
- context:
    cluster: authz-webhook
    user: apiserver
  name: webhook
```

## High Availability Configuration

### Load Balancer Setup (HAProxy)

```bash
# /etc/haproxy/haproxy.cfg
global
    log /dev/log local0
    log /dev/log local1 notice
    chroot /var/lib/haproxy
    stats socket /run/haproxy/admin.sock mode 660 level admin
    stats timeout 30s
    user haproxy
    group haproxy
    daemon

    # TLS configuration
    ssl-default-bind-ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256
    ssl-default-bind-options ssl-min-ver TLSv1.2 no-tls-tickets

defaults
    log     global
    mode    http
    option  httplog
    option  dontlognull
    timeout connect 5000
    timeout client  50000
    timeout server  50000

# Statistics page
listen stats
    bind *:9000
    mode http
    stats enable
    stats uri /stats
    stats refresh 10s
    stats admin if TRUE

# Kubernetes API Server frontend
frontend kubernetes-apiserver-frontend
    bind *:6443
    mode tcp
    option tcplog
    default_backend kubernetes-apiserver-backend

# Kubernetes API Server backend
backend kubernetes-apiserver-backend
    mode tcp
    balance roundrobin
    option tcp-check

    # Health check (HTTPS GET /healthz)
    option httpchk GET /healthz
    http-check expect status 200

    # Master nodes
    server master1 10.0.0.10:6443 check check-ssl verify none inter 2000 fall 3 rise 2
    server master2 10.0.0.11:6443 check check-ssl verify none inter 2000 fall 3 rise 2
    server master3 10.0.0.12:6443 check check-ssl verify none inter 2000 fall 3 rise 2
```

### NGINX Load Balancer

```nginx
# /etc/nginx/nginx.conf
stream {
    upstream kubernetes {
        least_conn;
        server 10.0.0.10:6443 max_fails=3 fail_timeout=30s;
        server 10.0.0.11:6443 max_fails=3 fail_timeout=30s;
        server 10.0.0.12:6443 max_fails=3 fail_timeout=30s;
    }

    server {
        listen 6443;
        proxy_pass kubernetes;
        proxy_timeout 10s;
        proxy_connect_timeout 5s;
    }
}
```

### Keepalived for Virtual IP (VIP)

```bash
# /etc/keepalived/keepalived.conf
vrrp_script check_apiserver {
    script "/etc/keepalived/check_apiserver.sh"
    interval 3
    weight -2
    fall 10
    rise 2
}

vrrp_instance VI_1 {
    state MASTER
    interface eth0
    virtual_router_id 51
    priority 101
    authentication {
        auth_type PASS
        auth_pass K8s_VIP_Pass
    }
    virtual_ipaddress {
        10.0.0.100/24
    }
    track_script {
        check_apiserver
    }
}
```

```bash
# /etc/keepalived/check_apiserver.sh
#!/bin/bash
errorExit() {
    echo "*** $*" 1>&2
    exit 1
}

curl --silent --max-time 2 --insecure https://localhost:6443/healthz -o /dev/null || errorExit "Error GET https://localhost:6443/healthz"
if ip addr | grep -q 10.0.0.100; then
    curl --silent --max-time 2 --insecure https://10.0.0.100:6443/healthz -o /dev/null || errorExit "Error GET https://10.0.0.100:6443/healthz"
fi
```

## External Integrations

### OIDC Authentication (Google, Okta, Keycloak)

#### Google OIDC Setup

```bash
# 1. Create OAuth 2.0 credentials in Google Cloud Console
# 2. Configure API server with OIDC flags

--oidc-issuer-url=https://accounts.google.com
--oidc-client-id=<your-client-id>.apps.googleusercontent.com
--oidc-username-claim=email
--oidc-username-prefix=google:
--oidc-groups-claim=groups
```

#### Keycloak OIDC Setup

```bash
# Keycloak OIDC configuration
--oidc-issuer-url=https://keycloak.example.com/auth/realms/kubernetes
--oidc-client-id=kubernetes
--oidc-username-claim=preferred_username
--oidc-username-prefix=keycloak:
--oidc-groups-claim=groups
--oidc-ca-file=/etc/kubernetes/keycloak-ca.crt
```

**kubeconfig for OIDC:**
```yaml
apiVersion: v1
kind: Config
clusters:
- name: kubernetes
  cluster:
    certificate-authority-data: <base64-ca-cert>
    server: https://10.0.0.100:6443

users:
- name: user@example.com
  user:
    auth-provider:
      name: oidc
      config:
        client-id: kubernetes
        client-secret: <client-secret>
        id-token: <id-token>
        idp-issuer-url: https://accounts.google.com
        refresh-token: <refresh-token>

contexts:
- name: kubernetes
  context:
    cluster: kubernetes
    user: user@example.com

current-context: kubernetes
```

### Webhook Authorization (Open Policy Agent)

```yaml
# OPA Authorization Webhook
apiVersion: v1
kind: ConfigMap
metadata:
  name: opa-policy
  namespace: opa
data:
  policy.rego: |
    package kubernetes.authz

    # Default deny
    default allow = false

    # Allow cluster admins
    allow {
        input.spec.user.groups[_] == "system:masters"
    }

    # Allow users to read their own namespace
    allow {
        input.spec.resourceAttributes.namespace == input.spec.user.username
        input.spec.resourceAttributes.verb == "get"
    }

    # Production namespace requires approval
    allow {
        input.spec.resourceAttributes.namespace != "production"
    }

    allow {
        input.spec.resourceAttributes.namespace == "production"
        input.spec.user.groups[_] == "prod-deployers"
    }
```

### Admission Webhooks (Mutating & Validating)

#### Mutating Webhook Example (Inject Sidecar)

```yaml
apiVersion: admissionregistration.k8s.io/v1
kind: MutatingWebhookConfiguration
metadata:
  name: istio-sidecar-injector
webhooks:
- name: sidecar-injector.istio.io
  clientConfig:
    service:
      name: istio-sidecar-injector
      namespace: istio-system
      path: "/inject"
    caBundle: <base64-ca-cert>
  rules:
  - operations: ["CREATE"]
    apiGroups: [""]
    apiVersions: ["v1"]
    resources: ["pods"]
  namespaceSelector:
    matchLabels:
      istio-injection: enabled
  admissionReviewVersions: ["v1", "v1beta1"]
  sideEffects: None
  timeoutSeconds: 30
  failurePolicy: Fail
```

#### Validating Webhook Example (Policy Enforcement)

```yaml
apiVersion: admissionregistration.k8s.io/v1
kind: ValidatingWebhookConfiguration
metadata:
  name: pod-policy-webhook
webhooks:
- name: validate.pods.example.com
  clientConfig:
    service:
      name: pod-policy-service
      namespace: default
      path: "/validate"
    caBundle: <base64-ca-cert>
  rules:
  - operations: ["CREATE", "UPDATE"]
    apiGroups: [""]
    apiVersions: ["v1"]
    resources: ["pods"]
  namespaceSelector:
    matchExpressions:
    - key: environment
      operator: In
      values: ["production"]
  admissionReviewVersions: ["v1"]
  sideEffects: None
  timeoutSeconds: 10
  failurePolicy: Fail
```

### API Server Metrics (Prometheus)

```yaml
# ServiceMonitor for API Server
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: kube-apiserver
  namespace: kube-system
  labels:
    k8s-app: apiserver
spec:
  jobLabel: component
  selector:
    matchLabels:
      component: apiserver
      provider: kubernetes
  namespaceSelector:
    matchNames:
    - default
  endpoints:
  - port: https
    interval: 30s
    scheme: https
    tlsConfig:
      caFile: /var/run/secrets/kubernetes.io/serviceaccount/ca.crt
      serverName: kubernetes
    bearerTokenFile: /var/run/secrets/kubernetes.io/serviceaccount/token
```

**Key Prometheus Metrics:**
```promql
# API server request rate
rate(apiserver_request_total[5m])

# API server request latency (P95)
histogram_quantile(0.95, rate(apiserver_request_duration_seconds_bucket[5m]))

# API server error rate
rate(apiserver_request_total{code=~"5.."}[5m])

# etcd request latency
histogram_quantile(0.99, rate(etcd_request_duration_seconds_bucket[5m]))

# Watch events
rate(apiserver_watch_events_total[5m])

# In-flight requests
apiserver_current_inflight_requests

# Dropped requests (overload indicator)
rate(apiserver_dropped_requests_total[5m])
```

### Audit Log Integration (ELK Stack)

```yaml
# Filebeat configuration for audit logs
apiVersion: v1
kind: ConfigMap
metadata:
  name: filebeat-config
  namespace: kube-system
data:
  filebeat.yml: |
    filebeat.inputs:
    - type: log
      enabled: true
      paths:
        - /var/log/kubernetes/audit/audit.log
      json.keys_under_root: true
      json.add_error_key: true
      fields:
        log_type: kubernetes-audit

    output.elasticsearch:
      hosts: ["elasticsearch:9200"]
      index: "kubernetes-audit-%{+yyyy.MM.dd}"

    setup.template.name: "kubernetes-audit"
    setup.template.pattern: "kubernetes-audit-*"
```

## Cluster Operations

### Upgrading API Server

#### Pre-Upgrade Checklist

```bash
# 1. Check current version
kubectl version --short
kubeadm version

# 2. Review release notes
# https://kubernetes.io/docs/setup/release/notes/

# 3. Check deprecated APIs
kubectl get --raw /metrics | grep apiserver_requested_deprecated_apis

# 4. Backup etcd
ETCDCTL_API=3 etcdctl snapshot save /backup/etcd-snapshot-$(date +%Y%m%d-%H%M%S).db \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key

# 5. Backup API server configuration
cp -r /etc/kubernetes /backup/kubernetes-$(date +%Y%m%d-%H%M%S)

# 6. Check cluster health
kubectl get nodes
kubectl get pods --all-namespaces
kubectl get componentstatuses  # deprecated but useful
```

#### Upgrade Process (kubeadm - HA Cluster)

```bash
# ==================== FIRST CONTROL PLANE NODE ====================

# 1. Find latest patch version
apt update
apt-cache madison kubeadm | grep 1.28

# 2. Upgrade kubeadm
apt-mark unhold kubeadm
apt-get update && apt-get install -y kubeadm=1.28.3-00
apt-mark hold kubeadm

# 3. Verify upgrade plan
kubeadm upgrade plan

# 4. Drain node
kubectl drain master1 --ignore-daemonsets --delete-emptydir-data

# 5. Apply upgrade
sudo kubeadm upgrade apply v1.28.3

# 6. Upgrade kubelet and kubectl
apt-mark unhold kubelet kubectl
apt-get update && apt-get install -y kubelet=1.28.3-00 kubectl=1.28.3-00
apt-mark hold kubelet kubectl

# 7. Restart kubelet
sudo systemctl daemon-reload
sudo systemctl restart kubelet

# 8. Uncordon node
kubectl uncordon master1

# 9. Verify upgrade
kubectl get nodes
kubectl version

# ==================== ADDITIONAL CONTROL PLANE NODES ====================

# On master2 and master3:

# Drain node
kubectl drain master2 --ignore-daemonsets --delete-emptydir-data

# Upgrade kubeadm
apt-mark unhold kubeadm
apt-get update && apt-get install -y kubeadm=1.28.3-00
apt-mark hold kubeadm

# Apply upgrade (node, not apply)
sudo kubeadm upgrade node

# Upgrade kubelet and kubectl
apt-mark unhold kubelet kubectl
apt-get update && apt-get install -y kubelet=1.28.3-00 kubectl=1.28.3-00
apt-mark hold kubelet kubectl

# Restart kubelet
sudo systemctl daemon-reload
sudo systemctl restart kubelet

# Uncordon node
kubectl uncordon master2

# Verify
kubectl get nodes
```

#### Manual Upgrade (Changing API Server Image)

```bash
# 1. Backup current manifest
cp /etc/kubernetes/manifests/kube-apiserver.yaml \
   /backup/kube-apiserver-$(date +%Y%m%d-%H%M%S).yaml

# 2. Edit manifest
sudo vi /etc/kubernetes/manifests/kube-apiserver.yaml

# Change:
# image: registry.k8s.io/kube-apiserver:v1.27.3
# To:
# image: registry.k8s.io/kube-apiserver:v1.28.3

# 3. Kubelet automatically restarts the pod
# Watch the process
kubectl get pods -n kube-system -w

# 4. Verify new version
kubectl version --short

# 5. Check API server logs
kubectl logs -n kube-system kube-apiserver-master1

# 6. Check health
curl -k https://localhost:6443/livez?verbose
curl -k https://localhost:6443/readyz?verbose
```

### Backup and Restore

#### Backup API Server State (via etcd)

```bash
# Full etcd backup (includes all API server state)
ETCDCTL_API=3 etcdctl snapshot save /backup/etcd-snapshot-$(date +%Y%m%d-%H%M%S).db \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key

# Verify snapshot
ETCDCTL_API=3 etcdctl snapshot status /backup/etcd-snapshot-*.db --write-out=table

# Backup encryption keys
cp /etc/kubernetes/encryption-config.yaml /backup/

# Backup certificates
tar -czf /backup/pki-backup-$(date +%Y%m%d-%H%M%S).tar.gz /etc/kubernetes/pki/

# Backup all manifests
tar -czf /backup/manifests-$(date +%Y%m%d-%H%M%S).tar.gz /etc/kubernetes/manifests/
```

#### Restore from Backup

```bash
# 1. Stop API server (remove from manifests directory)
mv /etc/kubernetes/manifests/kube-apiserver.yaml /tmp/

# 2. Stop etcd
mv /etc/kubernetes/manifests/etcd.yaml /tmp/

# 3. Restore etcd from snapshot
ETCDCTL_API=3 etcdctl snapshot restore /backup/etcd-snapshot-20231015.db \
  --data-dir=/var/lib/etcd-restore \
  --name=master1 \
  --initial-cluster=master1=https://10.0.0.10:2380 \
  --initial-advertise-peer-urls=https://10.0.0.10:2380

# 4. Update etcd manifest to use new data directory
sed -i 's|/var/lib/etcd|/var/lib/etcd-restore|g' /tmp/etcd.yaml

# 5. Restore etcd manifest
mv /tmp/etcd.yaml /etc/kubernetes/manifests/

# 6. Wait for etcd to start
sleep 30

# 7. Restore API server manifest
mv /tmp/kube-apiserver.yaml /etc/kubernetes/manifests/

# 8. Verify cluster
kubectl get nodes
kubectl get pods --all-namespaces
```

### Maintenance Operations

#### Certificate Management

```bash
# Check certificate expiration
kubeadm certs check-expiration

# Output:
# CERTIFICATE                EXPIRES                  RESIDUAL TIME   CERTIFICATE AUTHORITY
# admin.conf                 Oct 15, 2024 12:00 UTC   364d            ca
# apiserver                  Oct 15, 2024 12:00 UTC   364d            ca
# apiserver-etcd-client      Oct 15, 2024 12:00 UTC   364d            etcd-ca
# apiserver-kubelet-client   Oct 15, 2024 12:00 UTC   364d            ca
# front-proxy-client         Oct 15, 2024 12:00 UTC   364d            front-proxy-ca

# Renew all certificates
kubeadm certs renew all

# Renew specific certificate
kubeadm certs renew apiserver
kubeadm certs renew apiserver-kubelet-client

# After renewal, restart API server
kubectl delete pod -n kube-system kube-apiserver-master1

# Update kubeconfig with new client certs
kubeadm init phase kubeconfig all

# Verify new certificates
openssl x509 -in /etc/kubernetes/pki/apiserver.crt -text -noout | grep -A 2 Validity
```

#### Rotating Encryption Keys

```bash
# 1. Generate new encryption key
NEW_KEY=$(head -c 32 /dev/urandom | base64)

# 2. Edit encryption config, add new key as first entry
cat > /etc/kubernetes/encryption-config.yaml <<EOF
apiVersion: apiserver.config.k8s.io/v1
kind: EncryptionConfiguration
resources:
- resources:
  - secrets
  providers:
  - aescbc:
      keys:
      - name: key2
        secret: $NEW_KEY
  - aescbc:
      keys:
      - name: key1
        secret: <old-key>
  - identity: {}
EOF

# 3. Restart API server (it will pick up new config)
kubectl delete pod -n kube-system kube-apiserver-master1

# 4. Re-encrypt all secrets with new key
kubectl get secrets --all-namespaces -o json | kubectl replace -f -

# 5. Remove old key from config after verification
# Edit /etc/kubernetes/encryption-config.yaml, remove key1

# 6. Restart API server again
kubectl delete pod -n kube-system kube-apiserver-master1
```

#### Enabling/Disabling Admission Controllers

```bash
# 1. Edit API server manifest
sudo vi /etc/kubernetes/manifests/kube-apiserver.yaml

# 2. Add new admission controller
# Find line: --enable-admission-plugins=...
# Add: ,PodSecurity

# Before:
# --enable-admission-plugins=NodeRestriction,NamespaceLifecycle

# After:
# --enable-admission-plugins=NodeRestriction,NamespaceLifecycle,PodSecurity

# 3. Kubelet automatically restarts API server

# 4. Verify
kubectl get --raw /metrics | grep admission_controller
```

#### Changing API Server Flags

```bash
# Example: Increase request limits for high-traffic cluster

# 1. Edit manifest
sudo vi /etc/kubernetes/manifests/kube-apiserver.yaml

# 2. Update flags
# Find:
# --max-requests-inflight=400
# --max-mutating-requests-inflight=200

# Change to:
# --max-requests-inflight=800
# --max-mutating-requests-inflight=400

# 3. API server restarts automatically

# 4. Monitor metrics
kubectl get --raw /metrics | grep apiserver_current_inflight_requests
kubectl get --raw /metrics | grep apiserver_rejected_requests_total
```

## Troubleshooting

### API Server Won't Start

```bash
# 1. Check kubelet logs
sudo journalctl -u kubelet -f

# 2. Check container status
sudo crictl ps -a | grep kube-apiserver
sudo crictl logs <container-id>

# 3. Check manifest syntax
sudo kubelet --dry-run --pod-manifest-path=/etc/kubernetes/manifests/kube-apiserver.yaml

# 4. Verify certificates
ls -l /etc/kubernetes/pki/
openssl x509 -in /etc/kubernetes/pki/apiserver.crt -text -noout

# 5. Check etcd connectivity
ETCDCTL_API=3 etcdctl endpoint health \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key

# 6. Check port conflicts
sudo netstat -tulpn | grep 6443
sudo lsof -i :6443

# 7. Common issues:
# - Certificate expiration (check with kubeadm certs check-expiration)
# - etcd not running (check etcd pod)
# - Invalid flags (check manifest syntax)
# - Missing volumes/mounts (check hostPath volumes)
# - Port 6443 in use (check for orphaned processes)
```

### API Server High Latency

```bash
# 1. Check API server resource usage
kubectl top pod -n kube-system kube-apiserver-master1

# 2. Check request latency metrics
kubectl get --raw /metrics | grep apiserver_request_duration_seconds

# 3. Check etcd latency (common bottleneck)
ETCDCTL_API=3 etcdctl check perf \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key

# 4. Check for slow requests
kubectl get --raw /metrics | grep apiserver_request_duration_seconds_bucket | grep le=\"10\"

# 5. Increase resource limits
# Edit /etc/kubernetes/manifests/kube-apiserver.yaml
resources:
  limits:
    cpu: 4000m
    memory: 4Gi
  requests:
    cpu: 1000m
    memory: 1Gi

# 6. Tune request limits
# --max-requests-inflight=800
# --max-mutating-requests-inflight=400

# 7. Enable watch cache for specific resources
# --watch-cache-sizes=pods#10000,nodes#1000,services#1000
```

### Connection Refused / Timeout

```bash
# 1. Verify API server is running
kubectl get pods -n kube-system | grep apiserver

# 2. Check if API server is listening
sudo netstat -tulpn | grep 6443
sudo ss -tulpn | grep 6443

# 3. Test local connectivity
curl -k https://localhost:6443/version
curl -k https://127.0.0.1:6443/healthz

# 4. Test from worker node
curl -k https://<master-ip>:6443/version

# 5. Check firewall (master node)
sudo iptables -L -n | grep 6443
sudo firewall-cmd --list-ports  # If using firewalld

# Open port if needed:
sudo firewall-cmd --permanent --add-port=6443/tcp
sudo firewall-cmd --reload

# 6. Check load balancer (HA setup)
curl -k https://<lb-ip>:6443/version

# 7. Verify kubeconfig
kubectl config view
kubectl config get-contexts

# 8. Check API server address
kubectl cluster-info
```

### Certificate Errors

```bash
# Error: x509: certificate has expired or is not yet valid

# 1. Check certificate expiration
kubeadm certs check-expiration

# 2. Verify current date/time (time sync issues)
date
timedatectl status

# 3. Renew certificates
sudo kubeadm certs renew all

# 4. Restart API server
kubectl delete pod -n kube-system kube-apiserver-master1

# 5. Update kubeconfig
sudo cp /etc/kubernetes/admin.conf ~/.kube/config

# Error: x509: certificate signed by unknown authority

# 1. Verify CA certificate
openssl x509 -in /etc/kubernetes/pki/ca.crt -text -noout

# 2. Check client certificate chain
openssl verify -CAfile /etc/kubernetes/pki/ca.crt /etc/kubernetes/pki/apiserver.crt

# 3. Regenerate certificates if needed
sudo rm /etc/kubernetes/pki/apiserver.*
sudo kubeadm init phase certs apiserver

# 4. Restart API server
```

### Audit Log Issues

```bash
# Problem: Audit log not being created

# 1. Check audit log directory exists
ls -ld /var/log/kubernetes/audit/

# 2. Create directory if missing
sudo mkdir -p /var/log/kubernetes/audit/

# 3. Check disk space
df -h /var/log/

# 4. Check audit policy file
cat /etc/kubernetes/audit-policy.yaml

# 5. Verify API server flags
kubectl get pod -n kube-system kube-apiserver-master1 -o yaml | grep audit

# 6. Check API server logs for errors
kubectl logs -n kube-system kube-apiserver-master1 | grep -i audit

# Problem: Audit log filling up disk

# 1. Check current size
du -sh /var/log/kubernetes/audit/

# 2. Rotate logs
sudo logrotate -f /etc/logrotate.d/kube-apiserver

# 3. Set up log rotation
cat > /etc/logrotate.d/kube-apiserver <<EOF
/var/log/kubernetes/audit/*.log {
    daily
    rotate 7
    compress
    missingok
    notifempty
    create 0644 root root
}
EOF

# 4. Adjust audit policy to reduce verbosity
# Edit /etc/kubernetes/audit-policy.yaml
# Change level from "RequestResponse" to "Metadata" for less critical resources
```

### Memory Pressure

```bash
# Symptoms: API server OOMKilled, high memory usage

# 1. Check current usage
kubectl top pod -n kube-system kube-apiserver-master1

# 2. Check memory limits
kubectl get pod -n kube-system kube-apiserver-master1 -o jsonpath='{.spec.containers[0].resources}'

# 3. Increase memory limits
# Edit /etc/kubernetes/manifests/kube-apiserver.yaml
resources:
  limits:
    memory: 4Gi  # Increase from 2Gi
  requests:
    memory: 2Gi

# 4. Reduce watch cache sizes if needed
# --watch-cache-sizes=pods#5000,nodes#500
# --target-ram-mb=1000

# 5. Check for resource leaks
kubectl get --raw /metrics | grep go_memstats

# 6. Monitor memory over time
kubectl top pod -n kube-system kube-apiserver-master1 --use-protocol-buffers
```

### Deprecated API Warnings

```bash
# Problem: Using deprecated APIs

# 1. Check which deprecated APIs are being used
kubectl get --raw /metrics | grep apiserver_requested_deprecated_apis

# 2. Enable audit logging to see who's using deprecated APIs
# Add to audit policy:
# - level: Request
#   verbs: ["*"]
#   resources: []
#   deprecatedVersion: ["v1beta1"]

# 3. Find resources using deprecated APIs
kubectl get all --all-namespaces -o json | jq -r '.items[] | select(.apiVersion | contains("v1beta1")) | "\(.kind)/\(.metadata.name) in \(.metadata.namespace)"'

# 4. Update resources to use new API versions
# Example: Update Ingress from extensions/v1beta1 to networking.k8s.io/v1
kubectl convert -f old-ingress.yaml --output-version networking.k8s.io/v1

# 5. Update Helm charts, operators, and custom controllers
```

## Performance Tuning

### For Large Clusters (1000+ nodes)

```bash
# API Server flags for large clusters
--max-requests-inflight=1600
--max-mutating-requests-inflight=800
--watch-cache-sizes=nodes#2000,pods#20000,services#2000,deployments#1000
--target-ram-mb=4000
--min-request-timeout=3600

# etcd tuning (in etcd manifest)
--quota-backend-bytes=8589934592  # 8GB
--heartbeat-interval=200
--election-timeout=2000

# Resource limits
resources:
  requests:
    cpu: 2000m
    memory: 4Gi
  limits:
    memory: 8Gi
    # No CPU limit to avoid throttling

# Network optimizations
--max-mutating-requests-inflight=800
--enable-priority-and-fairness=true
```

### For High-Traffic Workloads

```bash
# Increase concurrent requests
--max-requests-inflight=2000
--max-mutating-requests-inflight=1000

# Reduce timeouts for faster failure detection
--request-timeout=30s

# Enable profiling temporarily for debugging
--profiling=true

# Monitor throttling
kubectl get --raw /metrics | grep apiserver_flowcontrol_rejected_requests_total
```

## Security Hardening

### Production Security Checklist

```bash
# Authentication
--anonymous-auth=false
--enable-bootstrap-token-auth=true
--oidc-issuer-url=https://your-idp.com

# Authorization
--authorization-mode=Node,RBAC

# Admission
--enable-admission-plugins=NodeRestriction,PodSecurity,NamespaceLifecycle,LimitRanger,ServiceAccount,DefaultStorageClass,ResourceQuota,MutatingAdmissionWebhook,ValidatingAdmissionWebhook

# Encryption
--encryption-provider-config=/etc/kubernetes/encryption-config.yaml

# Audit
--audit-log-path=/var/log/kubernetes/audit/audit.log
--audit-policy-file=/etc/kubernetes/audit-policy.yaml

# Network
--bind-address=0.0.0.0  # Or specific IP
--insecure-port=0
--secure-port=6443

# TLS
--tls-min-version=VersionTLS12
--tls-cipher-suites=TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256,TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256

# Profiling (disable in production)
--profiling=false
```

## Quick Reference Commands

```bash
# View API server pod
kubectl get pods -n kube-system -l component=kube-apiserver

# API server logs
kubectl logs -n kube-system kube-apiserver-master1 -f

# Health checks
curl -k https://localhost:6443/livez?verbose
curl -k https://localhost:6443/readyz?verbose

# Check version
kubectl version --short

# View metrics
kubectl get --raw /metrics | less

# Check certificates
kubeadm certs check-expiration

# Renew certificates
kubeadm certs renew all

# Backup etcd (API server state)
ETCDCTL_API=3 etcdctl snapshot save /backup/snapshot.db \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key

# Restart API server
kubectl delete pod -n kube-system kube-apiserver-master1

# Check API resources
kubectl api-resources
kubectl api-versions

# Test API access
kubectl auth can-i create pods
kubectl auth can-i create pods --as system:serviceaccount:default:mysa
```

## References

- [Official kube-apiserver Reference](https://kubernetes.io/docs/reference/command-line-tools-reference/kube-apiserver/)
- [API Server Configuration](https://kubernetes.io/docs/reference/config-api/apiserver-config.v1/)
- [Audit Logging](https://kubernetes.io/docs/tasks/debug/debug-cluster/audit/)
- [Encryption at Rest](https://kubernetes.io/docs/tasks/administer-cluster/encrypt-data/)
- [Admission Controllers](https://kubernetes.io/docs/reference/access-authn-authz/admission-controllers/)
- [Authentication](https://kubernetes.io/docs/reference/access-authn-authz/authentication/)
- [Authorization](https://kubernetes.io/docs/reference/access-authn-authz/authorization/)
