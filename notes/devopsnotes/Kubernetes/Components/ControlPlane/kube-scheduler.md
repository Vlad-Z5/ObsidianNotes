# kube-scheduler

## Overview

The **kube-scheduler** is responsible for assigning pods to nodes. It watches for newly created pods that don't have a node assignment and selects the optimal node based on resource requirements, constraints, affinity rules, and cluster state.

**Component Type:** Control Plane
**Process Name:** `kube-scheduler`
**Default Port:** 10259 (HTTPS metrics)
**Runs On:** Control plane nodes
**Stateless:** Yes (reads cluster state from API server)

## What Scheduler Actually Does

The scheduler is like an intelligent matchmaker - it finds the best node for each pod based on hundreds of factors.

### Real-World Analogy
Imagine a logistics manager assigning delivery trucks to routes:
- **Filter:** Which trucks can handle this load? (fuel, capacity, location)
- **Score:** Which truck is the best choice? (fuel efficiency, distance, driver availability)
- **Assign:** Send package to selected truck
- **Constraints:** Must avoid certain areas, prefer certain routes

### Scheduling Process

```
1. Pod Created (no nodeName)
   ↓
2. Scheduler watches API server for unscheduled pods
   ↓
3. FILTERING PHASE (Predicates)
   - Eliminate nodes that can't run the pod
   - Check: resources, ports, node selectors, taints/tolerations
   ↓
4. SCORING PHASE (Priorities)
   - Rank remaining nodes (0-100 score)
   - Consider: resource balance, affinity, spreading
   ↓
5. BINDING PHASE
   - Select highest-scoring node
   - Update pod.spec.nodeName via API server
   ↓
6. Kubelet on assigned node sees pod and starts containers
```

### What Scheduler Considers

**Filtering (Must-Have Requirements):**
- **Resources:** Does node have enough CPU/memory/storage?
- **NodeSelector:** Does node have required labels?
- **NodeAffinity:** Does node match affinity rules?
- **Taints/Tolerations:** Can pod tolerate node taints?
- **Port Conflicts:** Is required port available?
- **PodFitsHostPorts:** Can hostPort be allocated?
- **PodFitsResources:** Resources available after existing pods?
- **Volume Availability:** Can node access required volumes?
- **Node Conditions:** Is node Ready? (not NotReady, Unknown)

**Scoring (Optimization Preferences):**
- **LeastRequestedPriority:** Prefer nodes with more available resources
- **BalancedResourceAllocation:** Balance CPU/memory usage
- **SelectorSpreadPriority:** Spread pods across nodes
- **NodeAffinityPriority:** Prefer nodes matching affinity
- **ImageLocalityPriority:** Prefer nodes with image already pulled
- **InterPodAffinityPriority:** Co-locate or spread based on pod affinity
- **TaintTolerationPriority:** Prefer nodes without taints

### Example Scheduling Decision

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: web-app
spec:
  containers:
  - name: nginx
    image: nginx:1.21
    resources:
      requests:
        cpu: 500m
        memory: 512Mi
  nodeSelector:
    disktype: ssd
  affinity:
    podAntiAffinity:
      preferredDuringSchedulingIgnoredDuringExecution:
      - weight: 100
        podAffinityTerm:
          labelSelector:
            matchLabels:
              app: web-app
          topologyKey: kubernetes.io/hostname
```

**Scheduling Process:**
```
Available Nodes: node1, node2, node3, node4, node5

FILTERING:
- node1: ❌ No disktype=ssd label
- node2: ✅ Has SSD, enough resources
- node3: ✅ Has SSD, enough resources
- node4: ❌ Insufficient memory (400Mi available)
- node5: ✅ Has SSD, enough resources

Remaining: node2, node3, node5

SCORING:
- node2: 85 (good resources, but already has 2 web-app pods)
- node3: 95 (good resources, no web-app pods, image cached)
- node5: 78 (good resources, no web-app pods, image not cached)

SELECTED: node3 (highest score)

BINDING:
- Update pod spec: nodeName: node3
- Kubelet on node3 starts pod
```

## Installation and Configuration

### Static Pod Manifest

```yaml
# /etc/kubernetes/manifests/kube-scheduler.yaml
apiVersion: v1
kind: Pod
metadata:
  labels:
    component: kube-scheduler
    tier: control-plane
  name: kube-scheduler
  namespace: kube-system
spec:
  containers:
  - command:
    - kube-scheduler

    # ==================== API Server Connection ====================
    # kubeconfig for API server authentication
    - --kubeconfig=/etc/kubernetes/scheduler.conf

    # ==================== Leader Election ====================
    # Enable leader election (HA setup)
    - --leader-elect=true
    # Leader election namespace
    - --leader-elect-resource-namespace=kube-system
    # Lease duration (default: 15s)
    - --leader-elect-lease-duration=15s
    # Renew deadline (default: 10s)
    - --leader-elect-renew-deadline=10s
    # Retry period (default: 2s)
    - --leader-elect-retry-period=2s

    # ==================== Authentication & Authorization ====================
    # TLS certificates for HTTPS metrics endpoint
    - --tls-cert-file=/etc/kubernetes/pki/scheduler.crt
    - --tls-private-key-file=/etc/kubernetes/pki/scheduler.key
    # Authentication for metrics endpoint
    - --authentication-kubeconfig=/etc/kubernetes/scheduler.conf
    - --authorization-kubeconfig=/etc/kubernetes/scheduler.conf

    # ==================== Bind Address ====================
    # Bind address for HTTPS metrics/health (0.0.0.0 or specific IP)
    - --bind-address=0.0.0.0
    # Secure port for metrics and health checks
    - --secure-port=10259

    # ==================== Scheduling Configuration ====================
    # Scheduler configuration file (v1beta3+)
    - --config=/etc/kubernetes/scheduler-config.yaml

    # Legacy flags (deprecated, use config file instead):
    # --policy-config-file=/etc/kubernetes/scheduler-policy.json
    # --algorithm-provider=DefaultProvider

    # ==================== Profiling & Debugging ====================
    # Enable profiling (disable in production)
    - --profiling=false
    # Enable contention profiling
    - --contention-profiling=false

    # ==================== Logging ====================
    # Log verbosity (0-10, production: 2)
    - --v=2

    # ==================== Feature Gates ====================
    # Enable/disable alpha/beta features
    - --feature-gates=

    # ==================== Performance Tuning ====================
    # Percentage of nodes to schedule in parallel (default: 50%)
    - --parallelism=16
    # Number of worker threads (deprecated, use config file)
    # --kube-api-qps=50
    # --kube-api-burst=100

    image: registry.k8s.io/kube-scheduler:v1.28.0
    imagePullPolicy: IfNotPresent

    # ==================== Health Probes ====================
    livenessProbe:
      failureThreshold: 8
      httpGet:
        host: 127.0.0.1
        path: /healthz
        port: 10259
        scheme: HTTPS
      initialDelaySeconds: 10
      periodSeconds: 10
      timeoutSeconds: 15

    readinessProbe:
      failureThreshold: 3
      httpGet:
        host: 127.0.0.1
        path: /healthz
        port: 10259
        scheme: HTTPS
      periodSeconds: 1
      timeoutSeconds: 15

    startupProbe:
      failureThreshold: 24
      httpGet:
        host: 127.0.0.1
        path: /healthz
        port: 10259
        scheme: HTTPS
      initialDelaySeconds: 10
      periodSeconds: 10
      timeoutSeconds: 15

    name: kube-scheduler

    # ==================== Resource Limits ====================
    resources:
      requests:
        cpu: 100m
        memory: 128Mi
      limits:
        # No CPU limit to avoid throttling
        memory: 512Mi

    # ==================== Volume Mounts ====================
    volumeMounts:
    - mountPath: /etc/kubernetes/scheduler.conf
      name: kubeconfig
      readOnly: true
    - mountPath: /etc/kubernetes/scheduler-config.yaml
      name: scheduler-config
      readOnly: true
    - mountPath: /etc/kubernetes/pki
      name: k8s-certs
      readOnly: true

  hostNetwork: true
  priorityClassName: system-node-critical
  securityContext:
    seccompProfile:
      type: RuntimeDefault

  # ==================== Volumes ====================
  volumes:
  - hostPath:
      path: /etc/kubernetes/scheduler.conf
      type: FileOrCreate
    name: kubeconfig
  - hostPath:
      path: /etc/kubernetes/scheduler-config.yaml
      type: FileOrCreate
    name: scheduler-config
  - hostPath:
      path: /etc/kubernetes/pki
      type: DirectoryOrCreate
    name: k8s-certs
```

### Scheduler Configuration File

```yaml
# /etc/kubernetes/scheduler-config.yaml
apiVersion: kubescheduler.config.k8s.io/v1
kind: KubeSchedulerConfiguration

# ==================== Client Connection ====================
clientConnection:
  kubeconfig: /etc/kubernetes/scheduler.conf
  # QPS and burst for API server requests
  qps: 50
  burst: 100

# ==================== Leader Election ====================
leaderElection:
  leaderElect: true
  resourceNamespace: kube-system
  resourceName: kube-scheduler
  leaseDuration: 15s
  renewDeadline: 10s
  retryPeriod: 2s

# ==================== Parallelism ====================
# Percentage of nodes to process in parallel during scheduling cycle
parallelism: 16

# ==================== Profiles ====================
# Multiple scheduler profiles for different workload types
profiles:
- schedulerName: default-scheduler

  # Plugins configuration
  plugins:
    # Queue Sort: Order pods in scheduling queue
    queueSort:
      enabled:
      - name: PrioritySort

    # PreFilter: Quick checks before filtering
    preFilter:
      enabled:
      - name: NodeResourcesFit
      - name: NodePorts
      - name: VolumeRestrictions
      - name: PodTopologySpread
      - name: InterPodAffinity
      - name: VolumeBinding
      - name: NodeAffinity

    # Filter: Eliminate nodes that can't run pod
    filter:
      enabled:
      - name: NodeUnschedulable
      - name: NodeName
      - name: TaintToleration
      - name: NodeAffinity
      - name: NodePorts
      - name: NodeResourcesFit
      - name: VolumeRestrictions
      - name: EBSLimits
      - name: GCEPDLimits
      - name: AzureDiskLimits
      - name: VolumeBinding
      - name: VolumeZone
      - name: PodTopologySpread
      - name: InterPodAffinity

    # PostFilter: Run if no nodes pass filter (preemption)
    postFilter:
      enabled:
      - name: DefaultPreemption

    # PreScore: Prepare data for scoring
    preScore:
      enabled:
      - name: InterPodAffinity
      - name: PodTopologySpread
      - name: TaintToleration
      - name: NodeAffinity

    # Score: Rank nodes (0-100)
    score:
      enabled:
      - name: NodeResourcesFit
        weight: 1
      - name: InterPodAffinity
        weight: 1
      - name: NodeAffinity
        weight: 1
      - name: TaintToleration
        weight: 1
      - name: PodTopologySpread
        weight: 2
      - name: ImageLocality
        weight: 1
      - name: NodeResourcesBalancedAllocation
        weight: 1

    # Reserve: Reserve resources on selected node
    reserve:
      enabled:
      - name: VolumeBinding

    # Permit: Final approval before binding
    permit: {}

    # PreBind: Final preparations before binding
    preBind:
      enabled:
      - name: VolumeBinding

    # Bind: Bind pod to node
    bind:
      enabled:
      - name: DefaultBinder

    # PostBind: Cleanup after successful bind
    postBind: {}

  # Plugin configuration arguments
  pluginConfig:
  - name: NodeResourcesFit
    args:
      scoringStrategy:
        type: LeastAllocated
        resources:
        - name: cpu
          weight: 1
        - name: memory
          weight: 1

  - name: PodTopologySpread
    args:
      defaultConstraints:
      - maxSkew: 3
        topologyKey: kubernetes.io/hostname
        whenUnsatisfiable: ScheduleAnyway
      - maxSkew: 5
        topologyKey: topology.kubernetes.io/zone
        whenUnsatisfiable: ScheduleAnyway

  - name: InterPodAffinity
    args:
      hardPodAffinityWeight: 1

# ==================== High-Performance Profile ====================
- schedulerName: high-performance-scheduler
  plugins:
    score:
      enabled:
      - name: NodeResourcesFit
        weight: 5  # Heavily prioritize resource availability
      - name: ImageLocality
        weight: 3  # Prefer nodes with images cached
      disabled:
      - name: PodTopologySpread  # Don't spread for performance

  pluginConfig:
  - name: NodeResourcesFit
    args:
      scoringStrategy:
        type: MostAllocated  # Pack pods tightly for better performance
        resources:
        - name: cpu
          weight: 1
        - name: memory
          weight: 1

# ==================== Balanced Profile ====================
- schedulerName: balanced-scheduler
  plugins:
    score:
      enabled:
      - name: NodeResourcesBalancedAllocation
        weight: 5  # Heavily prioritize balanced allocation

  pluginConfig:
  - name: NodeResourcesFit
    args:
      scoringStrategy:
        type: LeastAllocated
        resources:
        - name: cpu
          weight: 1
        - name: memory
          weight: 1
        - name: ephemeral-storage
          weight: 1
```

### Custom Scheduler Profile Example

```yaml
# Deploy custom scheduler as separate deployment
apiVersion: v1
kind: ServiceAccount
metadata:
  name: custom-scheduler
  namespace: kube-system

---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: custom-scheduler
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: system:kube-scheduler
subjects:
- kind: ServiceAccount
  name: custom-scheduler
  namespace: kube-system

---
apiVersion: v1
kind: ConfigMap
metadata:
  name: custom-scheduler-config
  namespace: kube-system
data:
  scheduler-config.yaml: |
    apiVersion: kubescheduler.config.k8s.io/v1
    kind: KubeSchedulerConfiguration
    profiles:
    - schedulerName: custom-scheduler
      plugins:
        score:
          enabled:
          - name: NodeResourcesFit
            weight: 10
          - name: ImageLocality
            weight: 5

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: custom-scheduler
  namespace: kube-system
spec:
  replicas: 1
  selector:
    matchLabels:
      component: custom-scheduler
  template:
    metadata:
      labels:
        component: custom-scheduler
    spec:
      serviceAccountName: custom-scheduler
      containers:
      - name: kube-scheduler
        image: registry.k8s.io/kube-scheduler:v1.28.0
        command:
        - kube-scheduler
        - --config=/etc/kubernetes/scheduler-config.yaml
        - --v=2
        volumeMounts:
        - name: config
          mountPath: /etc/kubernetes
      volumes:
      - name: config
        configMap:
          name: custom-scheduler-config
```

**Using Custom Scheduler:**

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: pod-with-custom-scheduler
spec:
  schedulerName: custom-scheduler  # Use custom scheduler
  containers:
  - name: nginx
    image: nginx:1.21
```

## Advanced Scheduling Features

### Pod Priority and Preemption

```yaml
# Create PriorityClass
apiVersion: scheduling.k8s.io/v1
kind: PriorityClass
metadata:
  name: high-priority
value: 1000000
globalDefault: false
description: "High priority for critical workloads"

---
apiVersion: scheduling.k8s.io/v1
kind: PriorityClass
metadata:
  name: low-priority
value: 100
globalDefault: false
description: "Low priority for batch jobs"

---
# High priority pod
apiVersion: v1
kind: Pod
metadata:
  name: critical-pod
spec:
  priorityClassName: high-priority
  containers:
  - name: nginx
    image: nginx:1.21
    resources:
      requests:
        cpu: 2000m
        memory: 4Gi

---
# Low priority pod (can be preempted)
apiVersion: v1
kind: Pod
metadata:
  name: batch-job
spec:
  priorityClassName: low-priority
  containers:
  - name: batch
    image: batch-processor:1.0
    resources:
      requests:
        cpu: 2000m
        memory: 4Gi
```

**How Preemption Works:**
```
1. High-priority pod arrives, no nodes have enough resources
2. Scheduler checks if evicting low-priority pods would free space
3. If yes, scheduler preempts (evicts) low-priority pods
4. Scheduler waits for pods to terminate gracefully
5. Scheduler assigns high-priority pod to node
```

### Pod Topology Spread Constraints

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-app
spec:
  replicas: 10
  selector:
    matchLabels:
      app: web-app
  template:
    metadata:
      labels:
        app: web-app
    spec:
      topologySpreadConstraints:
      # Spread evenly across availability zones
      - maxSkew: 1
        topologyKey: topology.kubernetes.io/zone
        whenUnsatisfiable: DoNotSchedule
        labelSelector:
          matchLabels:
            app: web-app

      # Spread evenly across nodes (best effort)
      - maxSkew: 2
        topologyKey: kubernetes.io/hostname
        whenUnsatisfiable: ScheduleAnyway
        labelSelector:
          matchLabels:
            app: web-app

      containers:
      - name: web-app
        image: web-app:1.0
```

**Explanation:**
```
Zone constraint (DoNotSchedule):
- Zone A: 3 pods
- Zone B: 3 pods
- Zone C: 4 pods (maxSkew=1, difference is 1, OK)
- Cannot schedule in Zone C if it would make skew > 1

Node constraint (ScheduleAnyway):
- Tries to keep maxSkew ≤ 2 across nodes
- If impossible, schedules anyway (best effort)
```

### Node Affinity Examples

```yaml
# Required node affinity (must match)
apiVersion: v1
kind: Pod
metadata:
  name: gpu-pod
spec:
  affinity:
    nodeAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        nodeSelectorTerms:
        - matchExpressions:
          # Must have GPU
          - key: accelerator
            operator: In
            values:
            - nvidia-tesla-v100
            - nvidia-tesla-p100
          # Must be in us-east region
          - key: topology.kubernetes.io/region
            operator: In
            values:
            - us-east-1

  containers:
  - name: ml-training
    image: tensorflow:2.10
    resources:
      limits:
        nvidia.com/gpu: 1

---
# Preferred node affinity (soft requirement)
apiVersion: v1
kind: Pod
metadata:
  name: web-app
spec:
  affinity:
    nodeAffinity:
      preferredDuringSchedulingIgnoredDuringExecution:
      # Prefer SSD nodes (weight: 80)
      - weight: 80
        preference:
          matchExpressions:
          - key: disktype
            operator: In
            values:
            - ssd

      # Prefer newer kernel (weight: 20)
      - weight: 20
        preference:
          matchExpressions:
          - key: kernel-version
            operator: Gt
            values:
            - "5.10"

  containers:
  - name: nginx
    image: nginx:1.21
```

### Pod Affinity and Anti-Affinity

```yaml
# Co-locate with database pods
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: backend
  template:
    metadata:
      labels:
        app: backend
    spec:
      affinity:
        # Prefer same node as database (performance)
        podAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            podAffinityTerm:
              labelSelector:
                matchLabels:
                  app: database
              topologyKey: kubernetes.io/hostname

        # Never schedule on same node as other backend pods (HA)
        podAntiAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
          - labelSelector:
              matchLabels:
                app: backend
            topologyKey: kubernetes.io/hostname

      containers:
      - name: backend
        image: backend:1.0
```

### Taints and Tolerations

```yaml
# Taint a node (dedicated for GPU workloads)
# kubectl taint nodes node1 workload=gpu:NoSchedule

# Pod tolerates the taint
apiVersion: v1
kind: Pod
metadata:
  name: gpu-job
spec:
  tolerations:
  - key: workload
    operator: Equal
    value: gpu
    effect: NoSchedule

  nodeSelector:
    accelerator: nvidia-tesla-v100

  containers:
  - name: ml-job
    image: ml-training:1.0
    resources:
      limits:
        nvidia.com/gpu: 1

---
# Multiple tolerations
apiVersion: v1
kind: Pod
metadata:
  name: system-pod
spec:
  tolerations:
  # Tolerate master node taint
  - key: node-role.kubernetes.io/control-plane
    operator: Exists
    effect: NoSchedule

  # Tolerate NotReady nodes (for critical system pods)
  - key: node.kubernetes.io/not-ready
    operator: Exists
    effect: NoExecute
    tolerationSeconds: 300

  # Tolerate Unreachable nodes
  - key: node.kubernetes.io/unreachable
    operator: Exists
    effect: NoExecute
    tolerationSeconds: 300

  containers:
  - name: monitoring-agent
    image: datadog/agent:latest
```

**Taint Effects:**
```
NoSchedule: Don't schedule new pods (existing pods unaffected)
PreferNoSchedule: Try to avoid scheduling (soft)
NoExecute: Don't schedule + evict existing pods without toleration
```

## Monitoring and Metrics

### Prometheus Metrics

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: kube-scheduler
  namespace: kube-system
spec:
  jobLabel: component
  selector:
    matchLabels:
      component: kube-scheduler
  namespaceSelector:
    matchNames:
    - kube-system
  endpoints:
  - port: https-metrics
    interval: 30s
    scheme: https
    tlsConfig:
      caFile: /var/run/secrets/kubernetes.io/serviceaccount/ca.crt
      serverName: kube-scheduler
    bearerTokenFile: /var/run/secrets/kubernetes.io/serviceaccount/token
```

### Key Metrics

```promql
# Scheduling latency (P95)
histogram_quantile(0.95, rate(scheduler_scheduling_duration_seconds_bucket[5m]))

# Scheduling attempts
rate(scheduler_schedule_attempts_total[5m])

# Failed scheduling attempts
rate(scheduler_schedule_attempts_total{result="error"}[5m])

# Unschedulable pods
scheduler_pending_pods{queue="unschedulable"}

# Pod preemption attempts
rate(scheduler_preemption_attempts_total[5m])

# Framework extension point duration
histogram_quantile(0.99, rate(scheduler_framework_extension_point_duration_seconds_bucket[5m]))

# Scheduling algorithm latency by operation
histogram_quantile(0.99, rate(scheduler_scheduling_algorithm_duration_seconds_bucket[5m]))

# Queue incoming pods rate
rate(scheduler_queue_incoming_pods_total[5m])

# Plugin execution duration
histogram_quantile(0.95, rate(scheduler_plugin_execution_duration_seconds_bucket[5m]))
```

## Troubleshooting

### Pods Stuck in Pending

```bash
# Check pod status
kubectl get pods

# Describe pod to see scheduling errors
kubectl describe pod <pod-name>

# Common errors and solutions:

# 1. Insufficient resources
# Error: 0/5 nodes are available: 5 Insufficient cpu
kubectl describe nodes | grep -A 5 "Allocated resources"
# Solution: Add more nodes or reduce pod resource requests

# 2. No nodes match node selector
# Error: 0/5 nodes are available: 5 node(s) didn't match node selector
kubectl get nodes --show-labels
# Solution: Fix node selector or add label to nodes

# 3. Taints
# Error: 0/5 nodes are available: 5 node(s) had taint {key: value}, that the pod didn't tolerate
kubectl describe nodes | grep Taints
# Solution: Add toleration to pod or remove taint

# 4. Pod affinity not satisfied
# Error: 0/5 nodes are available: 5 node(s) didn't match pod affinity rules
kubectl get pods -o wide -l app=target-app
# Solution: Check if required pods exist and are running

# 5. Volume zone conflicts
# Error: 0/5 nodes are available: 5 node(s) had volume node affinity conflict
kubectl get pv <pv-name> -o yaml | grep zone
kubectl get nodes -L topology.kubernetes.io/zone
# Solution: Ensure pod scheduled in same zone as PV
```

### Scheduler Not Working

```bash
# Check scheduler pod status
kubectl get pods -n kube-system -l component=kube-scheduler

# View scheduler logs
kubectl logs -n kube-system kube-scheduler-master1

# Check scheduler leader election
kubectl get lease -n kube-system kube-scheduler -o yaml

# Check scheduler metrics endpoint
kubectl get --raw /metrics | grep scheduler

# Common issues:

# 1. Scheduler not running
kubectl get pods -n kube-system | grep scheduler
# Restart kubelet on master node
sudo systemctl restart kubelet

# 2. Multiple schedulers fighting (no leader election)
kubectl logs -n kube-system kube-scheduler-master1 | grep -i leader
# Check --leader-elect=true flag

# 3. Permission errors
kubectl logs -n kube-system kube-scheduler-master1 | grep -i forbidden
# Check RBAC permissions for scheduler service account
```

### Debugging Scheduling Decisions

```bash
# Enable verbose logging temporarily
kubectl edit pod -n kube-system kube-scheduler-master1
# Change: --v=2 to --v=4 (or higher)

# View detailed scheduling logs
kubectl logs -n kube-system kube-scheduler-master1 | grep -A 20 "Attempting to schedule pod"

# Check scheduling events
kubectl get events --sort-by='.lastTimestamp' | grep -i schedul

# Use scheduler extender for custom logging
# (requires custom scheduler configuration)
```

### Performance Issues

```bash
# Check scheduling latency
kubectl get --raw /metrics | grep scheduler_scheduling_duration_seconds

# Check pending pods
kubectl get pods --all-namespaces --field-selector=status.phase=Pending

# Increase scheduler parallelism
# Edit scheduler config: parallelism: 32

# Increase API server QPS
# Edit scheduler config:
# clientConnection:
#   qps: 100
#   burst: 200

# Check for slow plugins
kubectl get --raw /metrics | grep scheduler_framework_extension_point_duration_seconds
```

## Best Practices

### Resource Requests and Limits

```yaml
# Always set resource requests (scheduler needs this!)
apiVersion: v1
kind: Pod
metadata:
  name: good-pod
spec:
  containers:
  - name: app
    image: app:1.0
    resources:
      requests:
        cpu: 500m      # Scheduler uses this
        memory: 512Mi  # Scheduler uses this
      limits:
        cpu: 1000m     # Runtime enforcement only
        memory: 1Gi    # Runtime enforcement only
```

### Use Appropriate Spread Strategies

```yaml
# For HA: Use pod anti-affinity
apiVersion: apps/v1
kind: Deployment
metadata:
  name: critical-app
spec:
  replicas: 3
  template:
    spec:
      affinity:
        podAntiAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
          - labelSelector:
              matchLabels:
                app: critical-app
            topologyKey: kubernetes.io/hostname

# For cost optimization: Use topology spread with ScheduleAnyway
      topologySpreadConstraints:
      - maxSkew: 3
        topologyKey: kubernetes.io/hostname
        whenUnsatisfiable: ScheduleAnyway
```

### Priority Classes Strategy

```yaml
# System critical (highest)
apiVersion: scheduling.k8s.io/v1
kind: PriorityClass
metadata:
  name: system-critical
value: 2000000000
globalDefault: false
description: "Reserved for system components"

---
# Production critical
apiVersion: scheduling.k8s.io/v1
kind: PriorityClass
metadata:
  name: production-critical
value: 1000000
description: "Production critical workloads"

---
# Production normal
apiVersion: scheduling.k8s.io/v1
kind: PriorityClass
metadata:
  name: production-normal
value: 100000
globalDefault: true
description: "Production normal workloads"

---
# Development/test
apiVersion: scheduling.k8s.io/v1
kind: PriorityClass
metadata:
  name: development
value: 1000
description: "Development and test workloads"

---
# Batch/low priority
apiVersion: scheduling.k8s.io/v1
kind: PriorityClass
metadata:
  name: batch
value: 100
description: "Batch jobs, can be preempted"
```

### Taint Strategies

```bash
# Dedicated nodes for specific workloads
kubectl taint nodes node-gpu workload=gpu:NoSchedule
kubectl taint nodes node-gpu workload=gpu:NoExecute

# Temporary maintenance (don't evict, just don't schedule new)
kubectl taint nodes node1 maintenance=true:NoSchedule

# Drain node (evict existing, don't schedule new)
kubectl taint nodes node1 maintenance=true:NoExecute

# Master nodes (prevent workload scheduling)
kubectl taint nodes master1 node-role.kubernetes.io/control-plane:NoSchedule

# Spot/preemptible instances (mark as lower priority)
kubectl taint nodes spot-1 node.kubernetes.io/preemptible:PreferNoSchedule
```

## Advanced Configuration

### Scheduler Extender (Webhook)

```yaml
# Scheduler configuration with extender
apiVersion: kubescheduler.config.k8s.io/v1
kind: KubeSchedulerConfiguration
extenders:
- urlPrefix: "http://custom-scheduler-extender:8080"
  filterVerb: "filter"
  prioritizeVerb: "prioritize"
  preemptVerb: "preempt"
  bindVerb: "bind"
  weight: 5
  enableHTTPS: false
  nodeCacheCapable: true
  managedResources:
  - name: custom.io/gpu
    ignoredByScheduler: false
  ignorable: false
```

### Multiple Scheduler Profiles

```yaml
# Different profiles for different workload types
apiVersion: kubescheduler.config.k8s.io/v1
kind: KubeSchedulerConfiguration
profiles:
# Default balanced scheduler
- schedulerName: default-scheduler
  plugins:
    score:
      enabled:
      - name: NodeResourcesBalancedAllocation
        weight: 5

# High-density packing (cost optimization)
- schedulerName: bin-packing
  plugins:
    score:
      enabled:
      - name: NodeResourcesFit
        weight: 10
  pluginConfig:
  - name: NodeResourcesFit
    args:
      scoringStrategy:
        type: MostAllocated

# Spread for HA (avoid packing)
- schedulerName: spread
  plugins:
    score:
      enabled:
      - name: NodeResourcesFit
        weight: 1
      - name: PodTopologySpread
        weight: 10
```

## Quick Reference Commands

```bash
# View scheduler pod
kubectl get pods -n kube-system -l component=kube-scheduler

# Scheduler logs
kubectl logs -n kube-system kube-scheduler-master1 -f

# Check pending pods
kubectl get pods --all-namespaces --field-selector=status.phase=Pending

# Describe pod (see scheduling errors)
kubectl describe pod <pod-name>

# View scheduler configuration
kubectl get cm -n kube-system kube-scheduler-config -o yaml

# Check node resources
kubectl describe nodes | grep -A 5 "Allocated resources"

# View node labels
kubectl get nodes --show-labels

# Taint node
kubectl taint nodes node1 key=value:NoSchedule

# Remove taint
kubectl taint nodes node1 key=value:NoSchedule-

# Create priority class
kubectl apply -f priorityclass.yaml

# View priority classes
kubectl get priorityclasses

# Check scheduler metrics
kubectl get --raw /metrics | grep scheduler_

# View scheduling events
kubectl get events --sort-by='.lastTimestamp' | grep -i scheduled
```

## References

- [Kubernetes Scheduler Documentation](https://kubernetes.io/docs/concepts/scheduling-eviction/kube-scheduler/)
- [Scheduler Configuration](https://kubernetes.io/docs/reference/scheduling/config/)
- [Scheduling Framework](https://kubernetes.io/docs/concepts/scheduling-eviction/scheduling-framework/)
- [Pod Priority and Preemption](https://kubernetes.io/docs/concepts/scheduling-eviction/pod-priority-preemption/)
- [Topology Spread Constraints](https://kubernetes.io/docs/concepts/scheduling-eviction/topology-spread-constraints/)
