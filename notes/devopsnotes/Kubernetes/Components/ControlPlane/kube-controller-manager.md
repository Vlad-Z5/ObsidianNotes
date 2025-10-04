# kube-controller-manager

## Overview

The **kube-controller-manager** is the brain of Kubernetes automation. It runs multiple controllers that continuously watch the cluster state and work to move the current state toward the desired state. Each controller is a control loop that watches resources via the API server and takes action to reconcile differences.

**Component Type:** Control Plane
**Process Name:** `kube-controller-manager`
**Default Port:** 10257 (HTTPS metrics)
**Runs On:** Control plane nodes
**Stateless:** Yes (reads state from API server/etcd)

## What Controller Manager Actually Does

Think of the controller manager as the cluster's autopilot system - it constantly monitors and adjusts to maintain the desired state.

### Real-World Analogy
Imagine a cruise control system in a car:
- **Monitors:** Current speed vs desired speed
- **Detects:** Difference (speed too low/high)
- **Acts:** Accelerate or brake to match desired speed
- **Repeats:** Continuously monitors and adjusts

Kubernetes controllers work the same way:
```
1. Watch cluster state (via API server)
2. Compare current state vs desired state
3. Take action to reconcile differences
4. Repeat forever (reconciliation loop)
```

### Core Controllers

The controller manager runs these critical controllers:

**1. Node Controller**
- Monitors node health
- Marks nodes as NotReady if unresponsive
- Evicts pods from failed nodes
- Assigns pod CIDRs to nodes

**2. ReplicaSet Controller**
- Ensures desired number of pod replicas
- Creates pods if count too low
- Deletes pods if count too high

**3. Deployment Controller**
- Manages ReplicaSets for deployments
- Handles rolling updates
- Manages rollbacks

**4. Service Controller**
- Creates cloud load balancers for LoadBalancer services
- Updates endpoints for services

**5. Endpoint Controller**
- Populates Endpoints objects (joins Services & Pods)
- Watches Services and Pods
- Updates endpoint IPs when pods change

**6. Namespace Controller**
- Deletes all resources when namespace is deleted
- Prevents deletion of system namespaces

**7. ServiceAccount Controller**
- Creates default ServiceAccounts in new namespaces
- Creates tokens for ServiceAccounts

**8. PersistentVolume Controller**
- Binds PVs to PVCs
- Manages volume lifecycle

**9. Job Controller**
- Creates pods for Jobs
- Tracks job completion
- Handles parallelism

**10. CronJob Controller**
- Creates Jobs on schedule
- Manages job history
- Handles missed executions

## Architecture

### Controller Loop Pattern

```
┌─────────────────────────────────────────────────────────────┐
│                     Controller Manager                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌────────────────────────────────────────────────────┐   │
│  │              Controller Loop (Example)              │   │
│  ├────────────────────────────────────────────────────┤   │
│  │                                                      │   │
│  │  1. Watch API Server for Resource Changes          │   │
│  │     (via Informer/SharedInformer)                   │   │
│  │                                                      │   │
│  │  2. Event Received (Add/Update/Delete)             │   │
│  │                                                      │   │
│  │  3. Compare Current State vs Desired State         │   │
│  │                                                      │   │
│  │  4. Calculate Required Actions                      │   │
│  │                                                      │   │
│  │  5. Execute Actions (via API Server)               │   │
│  │     - Create resources                              │   │
│  │     - Update resources                              │   │
│  │     - Delete resources                              │   │
│  │                                                      │   │
│  │  6. Update Status (if needed)                       │   │
│  │                                                      │   │
│  │  7. Requeue if needed (retry logic)                │   │
│  │                                                      │   │
│  └────────────────────────────────────────────────────┘   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Example: ReplicaSet Controller

```
User creates Deployment (replicas: 3)
         ↓
Deployment Controller creates ReplicaSet (replicas: 3)
         ↓
ReplicaSet Controller watches ReplicaSet
         ↓
Current pods: 0, Desired: 3 → Create 3 pods
         ↓
Current pods: 3, Desired: 3 → No action
         ↓
Pod deleted (current: 2, desired: 3) → Create 1 pod
         ↓
User scales to 5 (current: 3, desired: 5) → Create 2 pods
         ↓
User scales to 2 (current: 5, desired: 2) → Delete 3 pods
```

### How Controllers Use API Server

```go
// Example: Simplified ReplicaSet Controller logic
func (rc *ReplicaSetController) syncReplicaSet(rs *appsv1.ReplicaSet) error {
    // 1. List pods owned by this ReplicaSet
    pods, err := rc.podLister.Pods(rs.Namespace).List(selector)

    // 2. Count active pods
    activePods := filterActivePods(pods)

    // 3. Calculate difference
    diff := len(activePods) - int(*rs.Spec.Replicas)

    // 4. Take action
    if diff < 0 {
        // Need more pods
        rc.createPods(rs, -diff)
    } else if diff > 0 {
        // Too many pods
        rc.deletePods(rs, diff)
    }

    // 5. Update ReplicaSet status
    rc.updateReplicaSetStatus(rs, len(activePods))

    return nil
}
```

## Installation and Configuration

### Static Pod Manifest

```yaml
# /etc/kubernetes/manifests/kube-controller-manager.yaml
apiVersion: v1
kind: Pod
metadata:
  labels:
    component: kube-controller-manager
    tier: control-plane
  name: kube-controller-manager
  namespace: kube-system
spec:
  containers:
  - command:
    - kube-controller-manager

    # ==================== API Server Connection ====================
    # kubeconfig for API server authentication
    - --kubeconfig=/etc/kubernetes/controller-manager.conf
    # Authentication for secure metrics endpoint
    - --authentication-kubeconfig=/etc/kubernetes/controller-manager.conf
    - --authorization-kubeconfig=/etc/kubernetes/controller-manager.conf

    # ==================== Leader Election ====================
    # Enable leader election (HA setup)
    - --leader-elect=true
    - --leader-elect-lease-duration=15s
    - --leader-elect-renew-deadline=10s
    - --leader-elect-retry-period=2s
    - --leader-elect-resource-namespace=kube-system

    # ==================== Service Account & Token Management ====================
    # Service account private key for signing tokens
    - --service-account-private-key-file=/etc/kubernetes/pki/sa.key
    # Root CA for validating service account tokens
    - --root-ca-file=/etc/kubernetes/pki/ca.crt
    # Cluster signing certificate (for CSR approval)
    - --cluster-signing-cert-file=/etc/kubernetes/pki/ca.crt
    - --cluster-signing-key-file=/etc/kubernetes/pki/ca.key
    # Certificate duration for approved CSRs (default: 8760h = 1 year)
    - --cluster-signing-duration=8760h

    # ==================== Controllers Configuration ====================
    # Controllers to enable (default: * = all)
    - --controllers=*,bootstrapsigner,tokencleaner
    # Can disable specific controllers:
    # - --controllers=*,-ttl,-bootstrapsigner,-tokencleaner

    # ==================== Node Controller ====================
    # How long to wait before marking node unhealthy (default: 40s)
    - --node-monitor-period=5s
    # Grace period before marking node NotReady (default: 40s)
    - --node-monitor-grace-period=40s
    # Time to wait before evicting pods from unhealthy node (default: 5m)
    - --pod-eviction-timeout=5m0s
    # Enable node lifecycle controller
    - --enable-dynamic-provisioning=true
    # Large cluster optimization
    - --large-cluster-size-threshold=50
    - --unhealthy-zone-threshold=0.55

    # ==================== Service & Endpoint Controller ====================
    # Concurrent service syncs (default: 1)
    - --concurrent-service-syncs=1
    # Concurrent endpoint syncs (default: 5)
    - --concurrent-endpoint-syncs=5
    # Concurrent service endpoint slices (default: 5)
    - --concurrent-serviceendpoint-syncs=5

    # ==================== ReplicaSet & Deployment Controller ====================
    # Concurrent ReplicaSet syncs (default: 5)
    - --concurrent-replicaset-syncs=5
    # Concurrent Deployment syncs (default: 5)
    - --concurrent-deployment-syncs=5
    # Concurrent StatefulSet syncs (default: 5)
    - --concurrent-statefulset-syncs=5
    # Concurrent DaemonSet syncs (default: 2)
    - --concurrent-daemonset-syncs=2

    # ==================== Garbage Collection ====================
    # Concurrent garbage collector workers (default: 20)
    - --concurrent-gc-syncs=20
    # Enable garbage collection
    - --enable-garbage-collector=true

    # ==================== Resource Quota ====================
    # Concurrent resource quota syncs (default: 5)
    - --concurrent-resource-quota-syncs=5

    # ==================== Namespace Controller ====================
    # Concurrent namespace syncs (default: 10)
    - --concurrent-namespace-syncs=10

    # ==================== Job & CronJob Controller ====================
    # Concurrent job syncs (default: 5)
    - --concurrent-job-syncs=5
    # Concurrent CronJob syncs (default: 5)
    - --concurrent-cronjob-syncs=5

    # ==================== Horizontal Pod Autoscaler ====================
    # HPA sync period (default: 15s)
    - --horizontal-pod-autoscaler-sync-period=15s
    # HPA upscale stabilization window (default: 0s)
    - --horizontal-pod-autoscaler-upscale-delay=3m0s
    # HPA downscale stabilization window (default: 5m)
    - --horizontal-pod-autoscaler-downscale-stabilization=5m0s
    # HPA CPU initialization period (default: 5m)
    - --horizontal-pod-autoscaler-cpu-initialization-period=5m0s
    # HPA initial readiness delay (default: 30s)
    - --horizontal-pod-autoscaler-initial-readiness-delay=30s
    # HPA tolerance (default: 0.1 = 10%)
    - --horizontal-pod-autoscaler-tolerance=0.1

    # ==================== Volume Controllers ====================
    # PV claim binder sync period (default: 15s)
    - --pvclaimbinder-sync-period=15s
    # Volume attach/detach reconciler sync period (default: 1m)
    - --attach-detach-reconcile-sync-period=1m0s
    # Disable attach/detach reconciler (if using CSI)
    # - --disable-attach-detach-reconcile-sync=false

    # ==================== Cloud Provider ====================
    # Cloud provider integration (aws, gce, azure, vsphere, openstack)
    # - --cloud-provider=aws
    # - --cloud-config=/etc/kubernetes/cloud-config.conf
    # External cloud controller manager (recommended for modern clusters)
    - --cloud-provider=external

    # ==================== Cluster CIDR & Networking ====================
    # Pod CIDR range (if using --allocate-node-cidrs)
    - --cluster-cidr=10.244.0.0/16
    # Service CIDR range
    - --service-cluster-ip-range=10.96.0.0/12
    # Allocate pod CIDRs to nodes
    - --allocate-node-cidrs=true
    # Node CIDR mask size (default: /24 for IPv4)
    - --node-cidr-mask-size=24

    # ==================== TLS & Security ====================
    # TLS cert for HTTPS metrics endpoint
    - --tls-cert-file=/etc/kubernetes/pki/controller-manager.crt
    - --tls-private-key-file=/etc/kubernetes/pki/controller-manager.key
    # Client CA for authenticating metric requests
    # - --client-ca-file=/etc/kubernetes/pki/ca.crt
    # Minimum TLS version
    - --tls-min-version=VersionTLS12

    # ==================== Bind Address ====================
    # Bind address for metrics/health
    - --bind-address=0.0.0.0
    # Secure port for metrics
    - --secure-port=10257

    # ==================== Feature Gates ====================
    # Enable/disable alpha/beta features
    - --feature-gates=

    # ==================== Logging ====================
    # Log verbosity (0-10, production: 2)
    - --v=2

    # ==================== Profiling ====================
    # Enable profiling (disable in production)
    - --profiling=false

    # ==================== Deprecated/Legacy Flags ====================
    # Port 0 = disable insecure port
    - --port=0
    # Use ServiceAccount credentials
    - --use-service-account-credentials=true

    image: registry.k8s.io/kube-controller-manager:v1.28.0
    imagePullPolicy: IfNotPresent

    # ==================== Health Probes ====================
    livenessProbe:
      failureThreshold: 8
      httpGet:
        host: 127.0.0.1
        path: /healthz
        port: 10257
        scheme: HTTPS
      initialDelaySeconds: 10
      periodSeconds: 10
      timeoutSeconds: 15

    readinessProbe:
      failureThreshold: 3
      httpGet:
        host: 127.0.0.1
        path: /healthz
        port: 10257
        scheme: HTTPS
      periodSeconds: 1
      timeoutSeconds: 15

    startupProbe:
      failureThreshold: 24
      httpGet:
        host: 127.0.0.1
        path: /healthz
        port: 10257
        scheme: HTTPS
      initialDelaySeconds: 10
      periodSeconds: 10
      timeoutSeconds: 15

    name: kube-controller-manager

    # ==================== Resource Limits ====================
    resources:
      requests:
        cpu: 200m
        memory: 256Mi
      limits:
        # No CPU limit to avoid throttling
        memory: 512Mi

    # ==================== Volume Mounts ====================
    volumeMounts:
    - mountPath: /etc/ssl/certs
      name: ca-certs
      readOnly: true
    - mountPath: /etc/kubernetes/pki
      name: k8s-certs
      readOnly: true
    - mountPath: /etc/kubernetes/controller-manager.conf
      name: kubeconfig
      readOnly: true
    - mountPath: /usr/libexec/kubernetes/kubelet-plugins/volume/exec
      name: flexvolume-dir

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
      path: /etc/kubernetes/controller-manager.conf
      type: FileOrCreate
    name: kubeconfig
  - hostPath:
      path: /usr/libexec/kubernetes/kubelet-plugins/volume/exec
      type: DirectoryOrCreate
    name: flexvolume-dir
```

## Controller Details

### Node Controller

**Responsibilities:**
- Monitor node health via node heartbeats
- Mark nodes NotReady if heartbeat missing
- Evict pods from failed nodes
- Delete nodes that remain NotReady

**Configuration:**
```bash
# How often to check node status
--node-monitor-period=5s

# How long to wait before marking NotReady
--node-monitor-grace-period=40s

# How long to wait before evicting pods
--pod-eviction-timeout=5m
```

**Behavior:**
```
Node heartbeat missed
         ↓
Wait 40s (grace period)
         ↓
Mark node NotReady
         ↓
Wait 5m (eviction timeout)
         ↓
Evict pods → Scheduler assigns to other nodes
```

### Deployment Controller

**Responsibilities:**
- Watch Deployment resources
- Create/update ReplicaSets
- Manage rolling updates
- Handle rollbacks

**Rolling Update Process:**
```
Deployment updated (new image)
         ↓
1. Create new ReplicaSet (replicas: 0)
         ↓
2. Scale new ReplicaSet up (1 pod)
         ↓
3. Wait for pod to be Ready
         ↓
4. Scale old ReplicaSet down (1 pod less)
         ↓
5. Repeat until new ReplicaSet has all replicas
         ↓
6. Scale old ReplicaSet to 0
```

**RollingUpdate Strategy:**
```yaml
spec:
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 25%        # Max extra pods during update
      maxUnavailable: 25%  # Max unavailable during update
```

### Job Controller

**Responsibilities:**
- Create pods for Jobs
- Track job completion
- Handle parallelism
- Retry failed pods
- Clean up completed jobs

**Job Execution:**
```
Job created (completions: 5, parallelism: 2)
         ↓
Create 2 pods (parallel workers)
         ↓
Pod 1 completes (1/5 done)
         ↓
Create 1 more pod (maintain parallelism)
         ↓
Pod 2 completes (2/5 done)
         ↓
Continue until 5 completions
         ↓
Mark Job complete
```

### Service Controller

**Responsibilities:**
- Watch Service resources
- Create cloud load balancers (AWS ELB, GCP LB, Azure LB)
- Update load balancer configuration
- Delete load balancers when service deleted

**LoadBalancer Service Flow:**
```yaml
apiVersion: v1
kind: Service
metadata:
  name: web-app
spec:
  type: LoadBalancer
  selector:
    app: web-app
  ports:
  - port: 80
    targetPort: 8080
```

```
Service created (type: LoadBalancer)
         ↓
Service Controller detects new service
         ↓
Call cloud provider API
         ↓
Create load balancer (AWS ELB/NLB/ALB)
         ↓
Get external IP/DNS
         ↓
Update Service status with LoadBalancer IP
         ↓
User sees external IP in kubectl get svc
```

## Monitoring and Metrics

### Prometheus Metrics

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: kube-controller-manager
  namespace: kube-system
spec:
  jobLabel: component
  selector:
    matchLabels:
      component: kube-controller-manager
  namespaceSelector:
    matchNames:
    - kube-system
  endpoints:
  - port: https-metrics
    interval: 30s
    scheme: https
    tlsConfig:
      caFile: /var/run/secrets/kubernetes.io/serviceaccount/ca.crt
      serverName: kube-controller-manager
    bearerTokenFile: /var/run/secrets/kubernetes.io/serviceaccount/token
```

### Key Metrics

```promql
# Work queue depth (pending items)
workqueue_depth{name="deployment"}
workqueue_depth{name="replicaset"}

# Work queue processing rate
rate(workqueue_adds_total{name="deployment"}[5m])

# Work queue latency
histogram_quantile(0.99, rate(workqueue_queue_duration_seconds_bucket[5m]))

# Controller sync duration
histogram_quantile(0.99, rate(controller_sync_duration_seconds_bucket{controller="deployment"}[5m]))

# Node evictions
rate(node_collector_evictions_total[5m])

# Pod creation/deletion rate
rate(pod_collector_pods_deleted_total[5m])
rate(pod_collector_pods_created_total[5m])

# Leader election status
leader_election_master_status

# Controller errors
rate(controller_sync_errors_total[5m])
```

## Troubleshooting

### Pods Not Being Created/Deleted

```bash
# Check controller manager status
kubectl get pods -n kube-system -l component=kube-controller-manager

# View logs
kubectl logs -n kube-system kube-controller-manager-master1

# Check specific controller
kubectl logs -n kube-system kube-controller-manager-master1 | grep -i replicaset

# Common issues:

# 1. Controller not running
kubectl get pods -n kube-system | grep controller-manager

# 2. No leader elected (HA setup)
kubectl logs -n kube-system kube-controller-manager-master1 | grep -i leader

# 3. Permission errors
kubectl logs -n kube-system kube-controller-manager-master1 | grep -i forbidden

# 4. API server connectivity
kubectl logs -n kube-system kube-controller-manager-master1 | grep -i "connection refused"
```

### Deployment Rollout Stuck

```bash
# Check deployment status
kubectl rollout status deployment/myapp

# Check deployment events
kubectl describe deployment myapp

# Check ReplicaSet
kubectl get rs -l app=myapp

# Check controller manager logs
kubectl logs -n kube-system kube-controller-manager-master1 | grep -i deployment

# Common causes:
# - Image pull errors
# - Insufficient resources
# - Pod disruption budget blocking
# - Incorrect maxUnavailable/maxSurge settings
```

### Nodes Not Being Marked NotReady

```bash
# Check node controller settings
kubectl get pod -n kube-system kube-controller-manager-master1 -o yaml | grep node-monitor

# Expected flags:
# --node-monitor-period=5s
# --node-monitor-grace-period=40s
# --pod-eviction-timeout=5m

# Check node status
kubectl get nodes
kubectl describe node <node-name>

# Check last heartbeat
kubectl get node <node-name> -o jsonpath='{.status.conditions[?(@.type=="Ready")].lastHeartbeatTime}'
```

### Service Load Balancer Not Created

```bash
# Check service status
kubectl get svc <service-name>
kubectl describe svc <service-name>

# Check controller manager logs
kubectl logs -n kube-system kube-controller-manager-master1 | grep -i service

# Verify cloud provider configuration
kubectl get pod -n kube-system kube-controller-manager-master1 -o yaml | grep cloud-provider

# Common issues:
# - Cloud provider not configured (--cloud-provider=external)
# - Cloud controller manager not running
# - Insufficient cloud provider permissions
# - Cloud provider API errors
```

### High Memory Usage

```bash
# Check resource usage
kubectl top pod -n kube-system kube-controller-manager-master1

# Check work queue sizes
kubectl get --raw /metrics | grep workqueue_depth

# Increase memory limits
# Edit /etc/kubernetes/manifests/kube-controller-manager.yaml
resources:
  limits:
    memory: 1Gi
  requests:
    memory: 512Mi

# Tune controller concurrency (reduce if needed)
--concurrent-replicaset-syncs=3
--concurrent-deployment-syncs=3
```

## Performance Tuning

### Large Cluster Optimizations (1000+ nodes)

```bash
# Node controller
--node-monitor-period=10s          # Reduce check frequency
--node-monitor-grace-period=60s    # Increase grace period
--large-cluster-size-threshold=100

# Increase concurrency for high pod churn
--concurrent-replicaset-syncs=10
--concurrent-deployment-syncs=10
--concurrent-statefulset-syncs=10
--concurrent-daemonset-syncs=5

# Garbage collection
--concurrent-gc-syncs=30

# Service endpoints
--concurrent-endpoint-syncs=10
--concurrent-serviceendpoint-syncs=10

# Resource limits
resources:
  requests:
    cpu: 500m
    memory: 1Gi
  limits:
    memory: 2Gi
```

### Small Cluster Optimizations

```bash
# Faster reconciliation
--node-monitor-period=3s
--node-monitor-grace-period=20s
--pod-eviction-timeout=2m

# Lower concurrency (save resources)
--concurrent-replicaset-syncs=2
--concurrent-deployment-syncs=2
--concurrent-gc-syncs=10
```

## Security Best Practices

```bash
# Use service account credentials per controller
--use-service-account-credentials=true

# Disable profiling in production
--profiling=false

# Disable insecure port
--port=0

# Use TLS for metrics
--secure-port=10257
--tls-cert-file=/etc/kubernetes/pki/controller-manager.crt
--tls-private-key-file=/etc/kubernetes/pki/controller-manager.key

# Client authentication
--authentication-kubeconfig=/etc/kubernetes/controller-manager.conf
--authorization-kubeconfig=/etc/kubernetes/controller-manager.conf

# Certificate rotation
--cluster-signing-duration=8760h  # 1 year
```

## Controller-Specific Configuration

### Horizontal Pod Autoscaler Tuning

```bash
# Sync period (how often to check metrics)
--horizontal-pod-autoscaler-sync-period=15s

# Prevent flapping
--horizontal-pod-autoscaler-upscale-delay=3m
--horizontal-pod-autoscaler-downscale-stabilization=5m

# Tolerance (prevent minor fluctuations)
--horizontal-pod-autoscaler-tolerance=0.1  # 10%

# CPU initialization period
--horizontal-pod-autoscaler-cpu-initialization-period=5m
```

### PersistentVolume Controller

```bash
# Binding sync period
--pvclaimbinder-sync-period=15s

# Volume attachment
--attach-detach-reconcile-sync-period=1m

# Disable if using CSI exclusively
# --enable-dynamic-provisioning=false
```

## Quick Reference Commands

```bash
# View controller manager
kubectl get pods -n kube-system -l component=kube-controller-manager

# Logs
kubectl logs -n kube-system kube-controller-manager-master1 -f

# Specific controller logs
kubectl logs -n kube-system kube-controller-manager-master1 | grep -i "deployment\|replicaset\|job"

# Health check
curl -k https://localhost:10257/healthz

# Metrics
kubectl get --raw /metrics | grep controller

# Check leader election
kubectl get lease -n kube-system kube-controller-manager -o yaml

# Check enabled controllers
kubectl get pod -n kube-system kube-controller-manager-master1 -o yaml | grep -A 1 controllers

# Restart controller manager
kubectl delete pod -n kube-system kube-controller-manager-master1

# Check node evictions
kubectl get events --all-namespaces | grep -i evict
```

## Practical Use Cases and Real-World Scenarios

### Use Case 1: Blue-Green Deployment with Deployment Controller

```yaml
# Blue deployment (current production)
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app-blue
  labels:
    version: blue
spec:
  replicas: 5
  selector:
    matchLabels:
      app: myapp
      version: blue
  template:
    metadata:
      labels:
        app: myapp
        version: blue
    spec:
      containers:
      - name: app
        image: myapp:v1.0
        ports:
        - containerPort: 8080

---
# Green deployment (new version)
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app-green
  labels:
    version: green
spec:
  replicas: 5
  selector:
    matchLabels:
      app: myapp
      version: green
  template:
    metadata:
      labels:
        app: myapp
        version: green
    spec:
      containers:
      - name: app
        image: myapp:v2.0
        ports:
        - containerPort: 8080

---
# Service switches between blue and green
apiVersion: v1
kind: Service
metadata:
  name: myapp-service
spec:
  selector:
    app: myapp
    version: blue  # Switch to 'green' for cutover
  ports:
  - port: 80
    targetPort: 8080
```

**Deployment Controller Behavior:**
```bash
# Deploy green version (parallel to blue)
kubectl apply -f app-green-deployment.yaml
# Deployment Controller creates new ReplicaSet with 5 pods

# Test green version
kubectl port-forward svc/myapp-service-test 8080:80

# Cutover (instant switch)
kubectl patch service myapp-service -p '{"spec":{"selector":{"version":"green"}}}'
# Service Controller updates endpoints to green pods instantly

# Rollback if needed
kubectl patch service myapp-service -p '{"spec":{"selector":{"version":"blue"}}}'

# Cleanup blue deployment
kubectl delete deployment app-blue
# Deployment Controller scales down blue ReplicaSet to 0
# Garbage Collector eventually deletes pods and ReplicaSet
```

### Use Case 2: Canary Deployment with Multiple ReplicaSets

```yaml
# Stable version (90% traffic)
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app-stable
spec:
  replicas: 9
  selector:
    matchLabels:
      app: myapp
      track: stable
  template:
    metadata:
      labels:
        app: myapp
        track: stable
    spec:
      containers:
      - name: app
        image: myapp:v1.5

---
# Canary version (10% traffic)
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app-canary
spec:
  replicas: 1
  selector:
    matchLabels:
      app: myapp
      track: canary
  template:
    metadata:
      labels:
        app: myapp
        track: canary
    spec:
      containers:
      - name: app
        image: myapp:v2.0

---
# Service selects both
apiVersion: v1
kind: Service
metadata:
  name: myapp
spec:
  selector:
    app: myapp  # Selects both stable and canary
  ports:
  - port: 80
    targetPort: 8080
```

**Traffic Distribution:**
```
Total pods: 10 (9 stable + 1 canary)
Traffic split: ~90% stable, ~10% canary

Endpoint Controller automatically:
1. Watches Service and Pod changes
2. Lists all pods matching selector (app=myapp)
3. Includes both stable and canary pods in endpoints
4. Service load balances across all 10 pods
```

**Progressive Rollout:**
```bash
# Increase canary traffic gradually
kubectl scale deployment app-canary --replicas=2  # 20% traffic
kubectl scale deployment app-stable --replicas=8

kubectl scale deployment app-canary --replicas=5  # 50% traffic
kubectl scale deployment app-stable --replicas=5

# Full rollout
kubectl scale deployment app-canary --replicas=10  # 100% traffic
kubectl delete deployment app-stable
```

### Use Case 3: Batch Processing with Job Controller

```yaml
# One-time data migration job
apiVersion: batch/v1
kind: Job
metadata:
  name: data-migration
spec:
  completions: 100  # Process 100 chunks
  parallelism: 10   # 10 workers at a time
  backoffLimit: 3   # Retry failed chunks 3 times
  activeDeadlineSeconds: 3600  # 1 hour timeout
  template:
    spec:
      containers:
      - name: migrator
        image: data-migrator:v1
        env:
        - name: CHUNK_ID
          valueFrom:
            fieldRef:
              fieldPath: metadata.labels['batch.kubernetes.io/job-completion-index']
        command:
        - /bin/sh
        - -c
        - |
          echo "Processing chunk $CHUNK_ID"
          ./migrate-chunk.sh $CHUNK_ID
      restartPolicy: OnFailure
```

**Job Controller Execution:**
```
Job created (completions: 100, parallelism: 10)
         ↓
Job Controller creates 10 pods (indexed 0-9)
         ↓
Pods 0,1,2 complete successfully (3/100 done)
         ↓
Job Controller creates pods 10,11,12 (maintain parallelism)
         ↓
Pod 3 fails → Pod recreated (retry 1/3)
         ↓
Pod 3 fails again → Pod recreated (retry 2/3)
         ↓
Pod 3 succeeds (4/100 done)
         ↓
Continue until all 100 completions
         ↓
Job marked Complete
```

**Monitor job progress:**
```bash
# Watch job status
kubectl get jobs -w

# Check completions
kubectl describe job data-migration | grep -A 2 "Pods Statuses"

# View failed pods
kubectl get pods -l job-name=data-migration --field-selector=status.phase=Failed

# Clean up completed jobs after 1 hour
kubectl patch job data-migration -p '{"spec":{"ttlSecondsAfterFinished":3600}}'
```

### Use Case 4: Scheduled Backups with CronJob Controller

```yaml
# Daily database backup
apiVersion: batch/v1
kind: CronJob
metadata:
  name: database-backup
spec:
  schedule: "0 2 * * *"  # 2 AM daily
  timeZone: "America/New_York"
  concurrencyPolicy: Forbid  # Don't run if previous still running
  successfulJobsHistoryLimit: 7
  failedJobsHistoryLimit: 3
  jobTemplate:
    spec:
      backoffLimit: 2
      template:
        spec:
          containers:
          - name: backup
            image: postgres:15
            command:
            - /bin/sh
            - -c
            - |
              TIMESTAMP=$(date +%Y%m%d_%H%M%S)
              pg_dump -h postgres-service -U admin dbname > /backups/backup_${TIMESTAMP}.sql
              gzip /backups/backup_${TIMESTAMP}.sql
              aws s3 cp /backups/backup_${TIMESTAMP}.sql.gz s3://backups/

              # Cleanup old backups (keep 30 days)
              find /backups -name "*.sql.gz" -mtime +30 -delete
            env:
            - name: PGPASSWORD
              valueFrom:
                secretKeyRef:
                  name: postgres-secret
                  key: password
            volumeMounts:
            - name: backup-storage
              mountPath: /backups
          volumes:
          - name: backup-storage
            persistentVolumeClaim:
              claimName: backup-pvc
          restartPolicy: OnFailure
```

**CronJob Controller Behavior:**
```bash
# View CronJob schedule
kubectl get cronjobs

# Check last execution
kubectl get cronjobs database-backup -o jsonpath='{.status.lastScheduleTime}'

# View job history
kubectl get jobs -l job-name=database-backup --sort-by=.metadata.creationTimestamp

# Manually trigger backup
kubectl create job backup-manual --from=cronjob/database-backup

# Suspend scheduled backups
kubectl patch cronjob database-backup -p '{"spec":{"suspend":true}}'
```

### Use Case 5: Auto-Scaling with HPA Controller

```yaml
# Deployment to auto-scale
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-app
spec:
  replicas: 2  # Initial replicas (HPA will override)
  selector:
    matchLabels:
      app: web-app
  template:
    metadata:
      labels:
        app: web-app
    spec:
      containers:
      - name: web
        image: nginx:1.21
        resources:
          requests:
            cpu: 100m
            memory: 128Mi
          limits:
            cpu: 500m
            memory: 512Mi

---
# Horizontal Pod Autoscaler
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: web-app-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: web-app
  minReplicas: 2
  maxReplicas: 20
  metrics:
  # CPU utilization
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70

  # Memory utilization
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80

  # Custom metric (requests per second)
  - type: Pods
    pods:
      metric:
        name: http_requests_per_second
      target:
        type: AverageValue
        averageValue: "1000"

  behavior:
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Percent
        value: 50  # Scale up by 50% of current
        periodSeconds: 60
      - type: Pods
        value: 5  # Or add 5 pods
        periodSeconds: 60
      selectPolicy: Max  # Use larger of the two

    scaleDown:
      stabilizationWindowSeconds: 300  # 5 min cooldown
      policies:
      - type: Percent
        value: 10  # Scale down by 10%
        periodSeconds: 60
      selectPolicy: Min
```

**HPA Controller in Action:**
```
Current: 2 pods, CPU 80% (target: 70%)
         ↓
HPA Controller calculates: desiredReplicas = ceil(2 * 80/70) = 3
         ↓
Scale up policy: max(50% of 2, 5 pods) = 5 pods limit
         ↓
HPA Controller updates Deployment replicas to 3
         ↓
Deployment Controller scales ReplicaSet to 3
         ↓
Wait for stabilization (60s)
         ↓
CPU drops to 50% (below 70% target)
         ↓
Wait for scale-down stabilization (300s)
         ↓
Scale down by 10% if still below target
```

**Monitor HPA:**
```bash
# Watch HPA status
kubectl get hpa -w

# Detailed HPA info
kubectl describe hpa web-app-hpa

# View scaling events
kubectl get events --field-selector involvedObject.name=web-app-hpa

# Test scaling (generate load)
kubectl run -i --tty load-generator --rm --image=busybox --restart=Never -- /bin/sh
# Inside the pod:
while true; do wget -q -O- http://web-app; done
```

### Use Case 6: StatefulSet Controller for Databases

```yaml
# PostgreSQL StatefulSet with ordered deployment
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
spec:
  serviceName: postgres-headless
  replicas: 3
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:15
        ports:
        - containerPort: 5432
          name: postgres
        env:
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: postgres-secret
              key: password
        - name: POD_NAME
          valueFrom:
            fieldRef:
              fieldPath: metadata.name
        - name: PGDATA
          value: /var/lib/postgresql/data/pgdata
        volumeMounts:
        - name: postgres-storage
          mountPath: /var/lib/postgresql/data
        - name: config
          mountPath: /etc/postgresql/postgresql.conf
          subPath: postgresql.conf
      volumes:
      - name: config
        configMap:
          name: postgres-config
  volumeClaimTemplates:
  - metadata:
      name: postgres-storage
    spec:
      accessModes: ["ReadWriteOnce"]
      storageClassName: fast-ssd
      resources:
        requests:
          storage: 100Gi

---
# Headless service for stable network identities
apiVersion: v1
kind: Service
metadata:
  name: postgres-headless
spec:
  clusterIP: None
  selector:
    app: postgres
  ports:
  - port: 5432
```

**StatefulSet Controller Behavior:**
```
StatefulSet created (replicas: 3)
         ↓
Create PVC postgres-storage-postgres-0
         ↓
PV Controller binds PVC to PV
         ↓
Create Pod postgres-0 with volume
         ↓
Wait for postgres-0 to be Running and Ready
         ↓
Create PVC postgres-storage-postgres-1
         ↓
Create Pod postgres-1
         ↓
Wait for postgres-1 Ready
         ↓
Create PVC postgres-storage-postgres-2
         ↓
Create Pod postgres-2
         ↓
All pods ready, StatefulSet complete

Scaling down (3 → 1):
         ↓
Delete postgres-2 (highest ordinal first)
         ↓
Wait for deletion to complete
         ↓
Delete postgres-1
         ↓
postgres-0 remains (PVCs preserved)
```

**Stable Network Identities:**
```bash
# Pod DNS names (stable)
postgres-0.postgres-headless.default.svc.cluster.local
postgres-1.postgres-headless.default.svc.cluster.local
postgres-2.postgres-headless.default.svc.cluster.local

# Application connects to master
psql -h postgres-0.postgres-headless -U admin -d mydb
```

### Use Case 7: DaemonSet Controller for Node Monitoring

```yaml
# Node exporter on every node
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: node-exporter
  namespace: monitoring
spec:
  selector:
    matchLabels:
      app: node-exporter
  updateStrategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 1
  template:
    metadata:
      labels:
        app: node-exporter
    spec:
      hostNetwork: true
      hostPID: true
      tolerations:
      # Run on master nodes too
      - key: node-role.kubernetes.io/control-plane
        operator: Exists
        effect: NoSchedule
      # Run on tainted nodes
      - operator: Exists
        effect: NoExecute
      containers:
      - name: node-exporter
        image: prom/node-exporter:v1.6.0
        args:
        - --path.procfs=/host/proc
        - --path.sysfs=/host/sys
        - --path.rootfs=/host/root
        - --collector.filesystem.mount-points-exclude=^/(sys|proc|dev|host|etc)($$|/)
        ports:
        - containerPort: 9100
          hostPort: 9100
          name: metrics
        volumeMounts:
        - name: proc
          mountPath: /host/proc
          readOnly: true
        - name: sys
          mountPath: /host/sys
          readOnly: true
        - name: root
          mountPath: /host/root
          mountPropagation: HostToContainer
          readOnly: true
        resources:
          requests:
            cpu: 100m
            memory: 128Mi
          limits:
            cpu: 200m
            memory: 256Mi
      volumes:
      - name: proc
        hostPath:
          path: /proc
      - name: sys
        hostPath:
          path: /sys
      - name: root
        hostPath:
          path: /
```

**DaemonSet Controller Behavior:**
```
DaemonSet created
         ↓
DaemonSet Controller lists all nodes
         ↓
For each node:
  - Check if pod already running
  - Check node taints/tolerations
  - Check node selector match
  - Create pod if needed
         ↓
Node added to cluster
         ↓
DaemonSet Controller detects new node
         ↓
Create node-exporter pod on new node
         ↓
Node removed from cluster
         ↓
DaemonSet Controller deletes pod automatically
```

**Selective DaemonSet (specific nodes only):**
```yaml
spec:
  template:
    spec:
      nodeSelector:
        monitoring: "true"  # Only nodes with this label

      # Or use affinity
      affinity:
        nodeAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
            nodeSelectorTerms:
            - matchExpressions:
              - key: node-role.kubernetes.io/worker
                operator: Exists
```

### Use Case 8: TTL Controller for Automatic Cleanup

```yaml
# Job with TTL (auto-cleanup after completion)
apiVersion: batch/v1
kind: Job
metadata:
  name: log-cleanup
spec:
  ttlSecondsAfterFinished: 3600  # Delete 1 hour after completion
  template:
    spec:
      containers:
      - name: cleanup
        image: busybox
        command:
        - /bin/sh
        - -c
        - |
          # Cleanup old logs
          find /var/log -name "*.log" -mtime +7 -delete
          echo "Cleanup complete"
        volumeMounts:
        - name: logs
          mountPath: /var/log
      volumes:
      - name: logs
        hostPath:
          path: /var/log
      restartPolicy: OnFailure
```

**TTL Controller Behavior:**
```
Job completes successfully
         ↓
TTL Controller detects completion
         ↓
Wait 3600 seconds (1 hour)
         ↓
TTL Controller deletes Job
         ↓
Garbage Collector cascades deletion to pods
```

### Use Case 9: ResourceQuota Controller

```yaml
# Namespace resource limits
apiVersion: v1
kind: ResourceQuota
metadata:
  name: dev-team-quota
  namespace: dev-team
spec:
  hard:
    # Compute resources
    requests.cpu: "20"
    requests.memory: 40Gi
    limits.cpu: "40"
    limits.memory: 80Gi

    # Storage
    requests.storage: 500Gi
    persistentvolumeclaims: "10"

    # Object counts
    pods: "50"
    services: "20"
    services.loadbalancers: "3"
    services.nodeports: "5"
    configmaps: "50"
    secrets: "50"

  scopeSelector:
    matchExpressions:
    - operator: In
      scopeName: PriorityClass
      values: ["high", "medium"]
```

**ResourceQuota Controller Behavior:**
```
Pod creation requested
         ↓
ResourceQuota Controller intercepts
         ↓
Check current usage:
  - CPU requests: 18/20 (90%)
  - Memory requests: 35Gi/40Gi (87.5%)
  - Pod count: 45/50
         ↓
New pod requests: 1 CPU, 3Gi memory
         ↓
Check: 18 + 1 = 19 ≤ 20 ✓
       35 + 3 = 38 ≤ 40 ✓
       45 + 1 = 46 ≤ 50 ✓
         ↓
Allow creation, update quota usage
         ↓
Next pod requests: 3 CPU, 5Gi memory
         ↓
Check: 19 + 3 = 22 > 20 ✗
         ↓
REJECT: "exceeded quota: requests.cpu"
```

**Monitor quota usage:**
```bash
# Check quota status
kubectl describe resourcequota -n dev-team

# Output:
# Name:            dev-team-quota
# Resource         Used    Hard
# --------         ----    ----
# requests.cpu     19      20
# requests.memory  38Gi    40Gi
# pods             46      50

# View quota events
kubectl get events -n dev-team --field-selector reason=FailedCreate
```

### Use Case 10: Cloud Provider Integration (AWS EKS)

```yaml
# LoadBalancer Service with AWS annotations
apiVersion: v1
kind: Service
metadata:
  name: web-app-lb
  annotations:
    # AWS Load Balancer Controller annotations
    service.beta.kubernetes.io/aws-load-balancer-type: "nlb"  # Network Load Balancer
    service.beta.kubernetes.io/aws-load-balancer-cross-zone-load-balancing-enabled: "true"
    service.beta.kubernetes.io/aws-load-balancer-backend-protocol: "tcp"
    service.beta.kubernetes.io/aws-load-balancer-ssl-cert: "arn:aws:acm:us-east-1:123456789:certificate/xxx"
    service.beta.kubernetes.io/aws-load-balancer-ssl-ports: "443"
    service.beta.kubernetes.io/aws-load-balancer-internal: "false"  # Public LB
    service.beta.kubernetes.io/aws-load-balancer-subnets: "subnet-xxx,subnet-yyy"
    service.beta.kubernetes.io/aws-load-balancer-security-groups: "sg-xxx"
spec:
  type: LoadBalancer
  selector:
    app: web-app
  ports:
  - name: http
    port: 80
    targetPort: 8080
  - name: https
    port: 443
    targetPort: 8080

---
# PersistentVolume with AWS EBS
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: app-data
spec:
  accessModes:
  - ReadWriteOnce
  storageClassName: gp3-encrypted
  resources:
    requests:
      storage: 100Gi

---
# StorageClass for AWS EBS
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: gp3-encrypted
provisioner: ebs.csi.aws.com
parameters:
  type: gp3
  encrypted: "true"
  kmsKeyId: "arn:aws:kms:us-east-1:123456789:key/xxx"
  iops: "3000"
  throughput: "125"
allowVolumeExpansion: true
volumeBindingMode: WaitForFirstConsumer
```

**Cloud Controllers in Action:**
```
Service created (type: LoadBalancer)
         ↓
Service Controller (or AWS Load Balancer Controller) detects
         ↓
Parse AWS annotations
         ↓
AWS API call: CreateLoadBalancer
  - Type: NLB
  - Subnets: subnet-xxx, subnet-yyy
  - SecurityGroups: sg-xxx
  - CrossZone: enabled
         ↓
Register targets (worker node IPs:NodePort)
         ↓
AWS returns LB DNS name
         ↓
Update Service status:
  status.loadBalancer.ingress:
  - hostname: xxx.elb.us-east-1.amazonaws.com
         ↓
User sees external hostname:
kubectl get svc web-app-lb
NAME         TYPE           EXTERNAL-IP
web-app-lb   LoadBalancer   xxx.elb.us-east-1.amazonaws.com
```

## References

- [Controller Manager Documentation](https://kubernetes.io/docs/reference/command-line-tools-reference/kube-controller-manager/)
- [Controllers Concept](https://kubernetes.io/docs/concepts/architecture/controller/)
- [Cloud Controller Manager](https://kubernetes.io/docs/concepts/architecture/cloud-controller/)
- [Writing Controllers](https://kubernetes.io/docs/concepts/architecture/controller/)
- [AWS Load Balancer Controller](https://kubernetes-sigs.github.io/aws-load-balancer-controller/)
- [StatefulSet Basics](https://kubernetes.io/docs/tutorials/stateful-application/basic-stateful-set/)
