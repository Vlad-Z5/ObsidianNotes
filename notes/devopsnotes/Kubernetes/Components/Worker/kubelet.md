# kubelet

## Overview

The **kubelet** is the primary "node agent" that runs on every worker node (and optionally on control plane nodes). It's responsible for managing pods and containers on the node, ensuring they are running and healthy according to their specifications.

**Component Type:** Worker Node Agent
**Process Name:** `kubelet`
**Default Ports:**
- 10250 (HTTPS API)
- 10248 (Health check)
- 10255 (Read-only API - deprecated)
**Runs On:** All nodes (workers and masters)
**Stateless:** Yes (gets pod specs from API server)

## What Kubelet Actually Does

The kubelet is like a factory floor manager - it takes work orders (pod specs) from headquarters (API server) and makes sure the work gets done on its machine (node).

### Real-World Analogy
Imagine a warehouse manager:
- **Receives orders:** Gets shipping manifests from headquarters
- **Assigns work:** Tells workers (containers) what to do
- **Monitors progress:** Checks that work is being done correctly
- **Reports status:** Updates headquarters on completion and issues
- **Handles failures:** Restarts failed tasks, escalates problems

### Core Responsibilities

**1. Pod Lifecycle Management**
- Watches API server for pods assigned to its node
- Pulls container images
- Starts/stops containers via container runtime (containerd, CRI-O)
- Mounts volumes
- Manages secrets and configmaps

**2. Health Monitoring**
- Runs liveness probes (restart unhealthy containers)
- Runs readiness probes (control traffic routing)
- Runs startup probes (allow slow-starting containers)
- Reports pod/container status to API server

**3. Resource Management**
- Enforces resource requests and limits (CPU, memory)
- Implements QoS (Quality of Service) classes
- Evicts pods when node runs out of resources
- Reports node capacity and allocatable resources

**4. Volume Management**
- Mounts volumes (PVs, ConfigMaps, Secrets, etc.)
- Unmounts volumes when pods deleted
- Works with CSI drivers for cloud storage

**5. Node Status**
- Reports node conditions (Ready, DiskPressure, MemoryPressure, PIDPressure)
- Updates node heartbeat
- Reports node capacity (CPU, memory, pods)

## Architecture

### Kubelet Workflow

```
┌─────────────────────────────────────────────────────────────┐
│                         Kubelet                              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌────────────────────────────────────────────────────┐   │
│  │            1. Watch API Server                      │   │
│  │   - Watch pods assigned to this node               │   │
│  │   - Listen for pod create/update/delete events     │   │
│  └────────────────────────────────────────────────────┘   │
│                         ↓                                     │
│  ┌────────────────────────────────────────────────────┐   │
│  │            2. Sync Loop (every 1s)                  │   │
│  │   - Compare desired state vs current state         │   │
│  │   - Calculate actions needed                        │   │
│  └────────────────────────────────────────────────────┘   │
│                         ↓                                     │
│  ┌────────────────────────────────────────────────────┐   │
│  │            3. Pod Lifecycle                         │   │
│  │   - Pull images                                     │   │
│  │   - Create sandbox (pause container)               │   │
│  │   - Start init containers (sequential)             │   │
│  │   - Start app containers (parallel)                │   │
│  └────────────────────────────────────────────────────┘   │
│                         ↓                                     │
│  ┌────────────────────────────────────────────────────┐   │
│  │            4. Health Checks                         │   │
│  │   - Run liveness probes                            │   │
│  │   - Run readiness probes                           │   │
│  │   - Restart/report unhealthy containers            │   │
│  └────────────────────────────────────────────────────┘   │
│                         ↓                                     │
│  ┌────────────────────────────────────────────────────┐   │
│  │            5. Status Updates                        │   │
│  │   - Update pod status in API server                │   │
│  │   - Update node status (heartbeat)                 │   │
│  └────────────────────────────────────────────────────┘   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
                           ↓
        ┌──────────────────────────────────────┐
        │     Container Runtime (CRI)           │
        │  - containerd                         │
        │  - CRI-O                              │
        │  - Docker (deprecated)                │
        └──────────────────────────────────────┘
```

### Container Runtime Interface (CRI)

```
Kubelet communicates with container runtime via CRI (gRPC)

┌─────────────┐
│   Kubelet   │
└──────┬──────┘
       │ CRI API (gRPC)
       │
┌──────▼──────────────────────────┐
│   Container Runtime             │
│   (containerd, CRI-O, etc.)     │
└──────┬──────────────────────────┘
       │
┌──────▼──────────────────────────┐
│   Container (runc, runsc, etc.) │
└─────────────────────────────────┘

CRI Operations:
- RunPodSandbox: Create pod network namespace
- CreateContainer: Create container
- StartContainer: Start container
- StopContainer: Stop container
- RemoveContainer: Remove container
- ListContainers: List containers
- PodSandboxStatus: Get sandbox status
- ContainerStatus: Get container status
- PullImage: Pull container image
```

## Installation and Configuration

### Systemd Service Configuration

```ini
# /etc/systemd/system/kubelet.service
[Unit]
Description=kubelet: The Kubernetes Node Agent
Documentation=https://kubernetes.io/docs/
Wants=network-online.target
After=network-online.target

[Service]
ExecStart=/usr/bin/kubelet
Restart=always
StartLimitInterval=0
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Kubelet Configuration File

```yaml
# /var/lib/kubelet/config.yaml
apiVersion: kubelet.config.k8s.io/v1beta1
kind: KubeletConfiguration

# ==================== API Server Connection ====================
# How to authenticate to API server
authentication:
  anonymous:
    enabled: false
  webhook:
    enabled: true
    cacheTTL: 2m0s
  x509:
    clientCAFile: /etc/kubernetes/pki/ca.crt

authorization:
  mode: Webhook
  webhook:
    cacheAuthorizedTTL: 5m0s
    cacheUnauthorizedTTL: 30s

# ==================== Cluster Configuration ====================
clusterDomain: cluster.local
clusterDNS:
- 10.96.0.10  # CoreDNS service IP

# ==================== Node Configuration ====================
# Node IP address
nodeIP: 10.0.1.100

# Provider ID (set by cloud-controller-manager)
# providerID: aws:///us-east-1a/i-0123456789abcdef0

# ==================== Container Runtime ====================
# Container runtime endpoint (Unix socket)
containerRuntimeEndpoint: unix:///run/containerd/containerd.sock

# Image service endpoint (usually same as runtime)
imageServiceEndpoint: unix:///run/containerd/containerd.sock

# ==================== Resource Management ====================
# Maximum pods per node
maxPods: 110

# Pod PID limit
podPidsLimit: 4096

# Reserve resources for system daemons
systemReserved:
  cpu: 200m
  memory: 512Mi
  ephemeral-storage: 1Gi

# Reserve resources for kubelet and container runtime
kubeReserved:
  cpu: 200m
  memory: 512Mi
  ephemeral-storage: 1Gi

# Enforce node allocatable
enforceNodeAllocatable:
- pods
- system-reserved
- kube-reserved

# ==================== Eviction Configuration ====================
# Evict pods when resources are low
evictionHard:
  memory.available: 100Mi
  nodefs.available: 10%
  nodefs.inodesFree: 5%
  imagefs.available: 15%

evictionSoft:
  memory.available: 200Mi
  nodefs.available: 15%
  nodefs.inodesFree: 10%
  imagefs.available: 20%

evictionSoftGracePeriod:
  memory.available: 1m30s
  nodefs.available: 2m
  nodefs.inodesFree: 2m
  imagefs.available: 2m

evictionPressureTransitionPeriod: 30s
evictionMaxPodGracePeriod: 30

# ==================== Image Management ====================
# Image garbage collection
imageGCHighThresholdPercent: 85
imageGCLowThresholdPercent: 80

# Image pull policy
imagePullProgressDeadline: 1m

# Serial image pulls (prevent overwhelming network)
serializeImagePulls: true
maxParallelImagePulls: 5  # If serializeImagePulls=false

# ==================== Logging ====================
logging:
  format: text  # or json
  verbosity: 2
  vmodule: ""

# Log rotation
containerLogMaxSize: 10Mi
containerLogMaxFiles: 5

# ==================== Health ====================
# Health check server
healthzBindAddress: 127.0.0.1
healthzPort: 10248

# Node lease (heartbeat)
nodeStatusUpdateFrequency: 10s
nodeStatusReportFrequency: 5m

# ==================== Feature Gates ====================
featureGates:
  RotateKubeletServerCertificate: true
  # CSINodeInfo: true
  # PodSecurity: true

# ==================== TLS ====================
# Server TLS
tlsCertFile: /var/lib/kubelet/pki/kubelet.crt
tlsPrivateKeyFile: /var/lib/kubelet/pki/kubelet.key

# Client TLS (kubelet → API server)
tlsCipherSuites:
- TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256
- TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256

# Rotate certificates
rotateCertificates: true
serverTLSBootstrap: true

# ==================== Metrics ====================
enableMetrics: true

# ==================== CNI Configuration ====================
# Network plugin binary directory
cniConfDir: /etc/cni/net.d
cniBinDir: /opt/cni/bin

# ==================== Other Settings ====================
# Read-only port (deprecated, disable in production)
readOnlyPort: 0

# Enable debugging handlers
enableDebuggingHandlers: true

# Enable profiling
enableProfilingHandler: false

# Fail if swap enabled
failSwapOn: true

# Cgroup driver (cgroupfs or systemd)
cgroupDriver: systemd

# Cgroup root
cgroupRoot: /

# CPU CFS quota enforcement
cpuCFSQuota: true
cpuCFSQuotaPeriod: 100ms

# Topology manager
topologyManagerPolicy: none  # none, best-effort, restricted, single-numa-node

# Memory manager
memoryManagerPolicy: None  # None or Static

# ==================== Volume Plugin Dir ====================
volumePluginDir: /usr/libexec/kubernetes/kubelet-plugins/volume/exec

# ==================== Static Pods ====================
# Directory for static pod manifests
staticPodPath: /etc/kubernetes/manifests

# Static pod URL (alternative to staticPodPath)
# staticPodURL: ""

# ==================== Registering with API Server ====================
# Register node with API server
registerNode: true

# Register with taints
registerWithTaints:
- key: node.kubernetes.io/not-ready
  effect: NoSchedule

# ==================== Security ====================
# Seccomp profile root
seccompDefault: false

# ==================== Pod Lifecycle ====================
# Max wait for graceful termination
shutdownGracePeriod: 0s
shutdownGracePeriodCriticalPods: 0s

# ==================== Hairpin Mode ====================
# Hairpin mode for traffic hairpinning
hairpinMode: promiscuous-bridge  # or hairpin-veth

# ==================== Protection ====================
# Protect kernel defaults
protectKernelDefaults: true

# ==================== Streaming ====================
# Enable content type streaming
streamingConnectionIdleTimeout: 4h
```

### Kubelet Command Line Flags

```bash
# /etc/systemd/system/kubelet.service.d/10-kubeadm.conf
[Service]
Environment="KUBELET_CONFIG_ARGS=--config=/var/lib/kubelet/config.yaml"
Environment="KUBELET_KUBECONFIG_ARGS=--kubeconfig=/etc/kubernetes/kubelet.conf --bootstrap-kubeconfig=/etc/kubernetes/bootstrap-kubelet.conf"
Environment="KUBELET_EXTRA_ARGS=--cloud-provider=external --container-runtime-endpoint=unix:///run/containerd/containerd.sock"

ExecStart=
ExecStart=/usr/bin/kubelet $KUBELET_CONFIG_ARGS $KUBELET_KUBECONFIG_ARGS $KUBELET_EXTRA_ARGS
```

## Pod Lifecycle Management

### Pod Creation Flow

```
1. API Server assigns pod to node (scheduler decision)
         ↓
2. Kubelet watches API server, sees new pod
         ↓
3. Kubelet pulls container images (if not cached)
         ↓
4. Kubelet calls CRI: RunPodSandbox
   - Creates pod network namespace
   - Starts pause container (holds namespace)
   - Sets up networking (CNI)
         ↓
5. Kubelet starts init containers (one by one, in order)
   - Wait for each to complete
   - If init container fails, restart pod
         ↓
6. Kubelet starts app containers (in parallel)
   - Mount volumes
   - Create containers (CRI: CreateContainer)
   - Start containers (CRI: StartContainer)
         ↓
7. Kubelet runs startup probes (if defined)
   - Wait for startup probe to succeed
   - Timeout if startup takes too long
         ↓
8. Pod Running
   - Kubelet runs liveness probes
   - Kubelet runs readiness probes
   - Update pod status regularly
         ↓
9. Pod Termination (when deleted or evicted)
   - Send SIGTERM to containers
   - Wait for grace period (default: 30s)
   - Send SIGKILL if still running
   - Remove pod sandbox
   - Update pod status to Terminated
```

### Init Containers Example

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: myapp
spec:
  initContainers:
  # Init container 1: Wait for database
  - name: wait-for-db
    image: busybox:1.36
    command:
    - sh
    - -c
    - |
      until nslookup postgres-service; do
        echo "Waiting for postgres-service..."
        sleep 2
      done

  # Init container 2: Run migrations
  - name: db-migration
    image: myapp:migrations
    command: ["/app/migrate.sh"]

  # Init container 3: Download config
  - name: fetch-config
    image: busybox:1.36
    command:
    - sh
    - -c
    - wget -O /config/app-config.json http://config-server/config
    volumeMounts:
    - name: config
      mountPath: /config

  containers:
  # Main application (starts after all init containers complete)
  - name: app
    image: myapp:v1
    volumeMounts:
    - name: config
      mountPath: /app/config

  volumes:
  - name: config
    emptyDir: {}
```

**Kubelet execution:**
```
1. Kubelet sees pod assigned to node
2. Pull image: busybox:1.36
3. Start init container: wait-for-db
4. Init container completes → exit code 0
5. Pull image: myapp:migrations
6. Start init container: db-migration
7. Init container completes → exit code 0
8. Pull image: busybox:1.36 (cached)
9. Start init container: fetch-config
10. Init container completes → exit code 0
11. Pull image: myapp:v1
12. Start app container: app
13. Pod status: Running
```

## Health Probes

### Liveness Probe (Restart Unhealthy Containers)

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: liveness-example
spec:
  containers:
  - name: app
    image: myapp:v1
    ports:
    - containerPort: 8080

    livenessProbe:
      httpGet:
        path: /healthz
        port: 8080
        httpHeaders:
        - name: X-Custom-Header
          value: Awesome
      initialDelaySeconds: 30  # Wait 30s before first probe
      periodSeconds: 10        # Probe every 10s
      timeoutSeconds: 5        # Probe timeout 5s
      successThreshold: 1      # 1 success = healthy
      failureThreshold: 3      # 3 failures = restart container
```

**Kubelet behavior:**
```
Container starts
         ↓
Wait 30s (initialDelaySeconds)
         ↓
Probe: GET http://localhost:8080/healthz
         ↓
Success → Container healthy
         ↓
Wait 10s (periodSeconds)
         ↓
Probe: GET http://localhost:8080/healthz
         ↓
Failure (timeout or non-200 response)
         ↓
Wait 10s, probe again → Failure (2/3)
         ↓
Wait 10s, probe again → Failure (3/3)
         ↓
Kill container → Restart container
         ↓
Restart count incremented
```

### Readiness Probe (Control Traffic Routing)

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: readiness-example
spec:
  containers:
  - name: app
    image: myapp:v1
    ports:
    - containerPort: 8080

    readinessProbe:
      exec:
        command:
        - /app/ready-check.sh
      initialDelaySeconds: 5
      periodSeconds: 5
      failureThreshold: 1  # Immediately mark unready on failure
```

**Kubelet behavior:**
```
Container starts
         ↓
Wait 5s (initialDelaySeconds)
         ↓
Probe: exec /app/ready-check.sh
         ↓
Exit code 0 → Container Ready
         ↓
Kubelet updates pod condition: Ready=True
         ↓
Endpoints controller adds pod IP to service endpoints
         ↓
Service starts routing traffic to pod
         ↓
Probe every 5s
         ↓
If failure → Ready=False → Remove from endpoints → Stop traffic
         ↓
When success → Ready=True → Add back to endpoints → Resume traffic
```

### Startup Probe (Allow Slow-Starting Containers)

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: startup-example
spec:
  containers:
  - name: slow-start-app
    image: legacy-app:v1
    ports:
    - containerPort: 8080

    startupProbe:
      httpGet:
        path: /startup
        port: 8080
      initialDelaySeconds: 0
      periodSeconds: 10
      failureThreshold: 30  # 30 * 10s = 5 minutes max startup time

    livenessProbe:
      httpGet:
        path: /healthz
        port: 8080
      periodSeconds: 10
      failureThreshold: 3

    readinessProbe:
      httpGet:
        path: /ready
        port: 8080
      periodSeconds: 5
```

**Kubelet behavior:**
```
Container starts
         ↓
Startup probe takes over (liveness/readiness disabled)
         ↓
Probe /startup every 10s
         ↓
Failure → Keep trying (up to 30 attempts = 5 min)
         ↓
Success → Startup probe succeeds
         ↓
Liveness probe activates (monitor health)
         ↓
Readiness probe activates (control traffic)
```

## Resource Management and QoS

### QoS Classes

```yaml
# ==================== Guaranteed QoS ====================
# All containers have limits = requests for CPU and memory
apiVersion: v1
kind: Pod
metadata:
  name: guaranteed-pod
spec:
  containers:
  - name: app
    image: myapp:v1
    resources:
      requests:
        cpu: 1000m
        memory: 1Gi
      limits:
        cpu: 1000m    # Same as request
        memory: 1Gi   # Same as request

# ==================== Burstable QoS ====================
# At least one container has request < limit
apiVersion: v1
kind: Pod
metadata:
  name: burstable-pod
spec:
  containers:
  - name: app
    image: myapp:v1
    resources:
      requests:
        cpu: 500m
        memory: 512Mi
      limits:
        cpu: 2000m    # Can burst to 2 CPU
        memory: 2Gi   # Can burst to 2Gi memory

# ==================== BestEffort QoS ====================
# No requests or limits specified
apiVersion: v1
kind: Pod
metadata:
  name: besteffort-pod
spec:
  containers:
  - name: app
    image: myapp:v1
    # No resources specified
```

**Kubelet eviction order (when node under pressure):**
```
1. BestEffort pods (evicted first)
2. Burstable pods (exceeding requests)
3. Burstable pods (within requests)
4. Guaranteed pods (evicted last)
```

### Node Resource Management

```bash
# Check node capacity and allocatable
kubectl describe node worker-1

# Output:
# Capacity:
#   cpu:                4
#   ephemeral-storage:  100Gi
#   memory:             16Gi
#   pods:               110

# Allocatable:  (Capacity - Reserved)
#   cpu:                3600m  (4000m - 200m system - 200m kube)
#   memory:             14.5Gi (16Gi - 512Mi system - 512Mi kube - 512Mi eviction)
#   pods:               110

# Allocated resources:
#   CPU Requests:    2800m (77% of allocatable)
#   CPU Limits:      5600m (155% of allocatable - overcommit)
#   Memory Requests: 10Gi (68% of allocatable)
#   Memory Limits:   18Gi (124% of allocatable - overcommit)
```

## Volume Management

### Volume Types Handled by Kubelet

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: volume-example
spec:
  containers:
  - name: app
    image: myapp:v1
    volumeMounts:
    # ConfigMap (kubelet fetches from API server)
    - name: config
      mountPath: /etc/config

    # Secret (kubelet fetches from API server)
    - name: secret
      mountPath: /etc/secret
      readOnly: true

    # EmptyDir (kubelet creates on node)
    - name: cache
      mountPath: /cache

    # HostPath (kubelet mounts from host)
    - name: host-logs
      mountPath: /var/log/app

    # PersistentVolumeClaim (kubelet coordinates with CSI driver)
    - name: data
      mountPath: /data

  volumes:
  - name: config
    configMap:
      name: app-config

  - name: secret
    secret:
      secretName: app-secret

  - name: cache
    emptyDir:
      sizeLimit: 1Gi

  - name: host-logs
    hostPath:
      path: /var/log/myapp
      type: DirectoryOrCreate

  - name: data
    persistentVolumeClaim:
      claimName: app-data-pvc
```

**Kubelet volume operations:**
```
Pod scheduled to node
         ↓
Kubelet sees pod needs volumes
         ↓
For ConfigMap/Secret:
  - Fetch from API server
  - Write to tmpfs (in-memory filesystem)
  - Mount to container
         ↓
For EmptyDir:
  - Create directory on node
  - Mount to container
         ↓
For HostPath:
  - Verify path exists (or create if DirectoryOrCreate)
  - Bind mount to container
         ↓
For PersistentVolumeClaim:
  - Check if volume already attached to node
  - If not, call CSI driver: ControllerPublishVolume
  - Wait for volume attachment
  - Call CSI driver: NodeStageVolume
  - Call CSI driver: NodePublishVolume
  - Mount to container
         ↓
Start containers with volumes mounted
```

## Static Pods

Static pods are managed directly by kubelet (not by API server).

```yaml
# /etc/kubernetes/manifests/static-nginx.yaml
apiVersion: v1
kind: Pod
metadata:
  name: static-nginx
spec:
  containers:
  - name: nginx
    image: nginx:1.21
    ports:
    - containerPort: 80
```

**Kubelet behavior:**
```
1. Kubelet watches /etc/kubernetes/manifests/ directory
2. Detects new file: static-nginx.yaml
3. Kubelet creates pod directly (no API server)
4. Kubelet creates mirror pod in API server (for visibility)
5. Mirror pod visible in kubectl get pods
6. Cannot delete via kubectl (file-based only)
7. To delete: remove YAML file from manifests directory
```

**Use cases for static pods:**
```
- Control plane components (kube-apiserver, etcd, kube-scheduler)
- Critical system daemons
- Bootstrap components
- Emergency/recovery pods
```

## Troubleshooting

### Pod Not Starting

```bash
# Check kubelet logs
journalctl -u kubelet -f

# Check pod events
kubectl describe pod <pod-name>

# Common issues:

# 1. Image pull failure
# Events: Failed to pull image "myapp:v999": not found
# Solution: Check image name/tag, check registry credentials

# 2. Volume mount failure
# Events: Unable to attach or mount volumes: error finding PVC
# Solution: Check PVC exists, check PV bound

# 3. Resource constraints
# Events: 0/3 nodes available: insufficient cpu
# Solution: Reduce resource requests or add nodes

# 4. Node selector mismatch
# Events: 0/3 nodes available: node(s) didn't match node selector
# Solution: Add required labels to nodes or fix pod spec
```

### Container Crashing

```bash
# Check container logs
kubectl logs <pod-name> -c <container-name>
kubectl logs <pod-name> -c <container-name> --previous  # Previous instance

# Check liveness probe logs
kubectl describe pod <pod-name> | grep -A 10 Liveness

# Common issues:

# 1. Application error
# Solution: Fix application code, check logs for errors

# 2. Liveness probe too aggressive
# Events: Liveness probe failed: HTTP probe failed with statuscode: 503
# Solution: Increase initialDelaySeconds, increase failureThreshold

# 3. Resource limits too low (OOMKilled)
# Events: Container killed (137), reason: OOMKilled
# Solution: Increase memory limits

# Check resource usage
kubectl top pod <pod-name> --containers
```

### Kubelet Not Ready

```bash
# Check kubelet status
systemctl status kubelet

# Check kubelet logs
journalctl -u kubelet -n 100

# Common issues:

# 1. Cannot connect to API server
# Error: Unable to authenticate the request due to an error
# Solution: Check kubeconfig, check certificates

# 2. Container runtime not available
# Error: Failed to get runtime info: rpc error: connection refused
# Solution: Start containerd, check runtime socket path

# 3. Certificate expired
# Error: x509: certificate has expired
# Solution: Renew certificates

# 4. Disk pressure
# Node condition: DiskPressure=True
# Solution: Clean up disk space, increase disk size
```

### Node NotReady

```bash
# Check node conditions
kubectl describe node <node-name> | grep -A 5 Conditions

# Possible conditions:
# Ready: False (kubelet not posting status)
# MemoryPressure: True (low memory)
# DiskPressure: True (low disk)
# PIDPressure: True (too many processes)
# NetworkUnavailable: True (network plugin not ready)

# Solutions:

# 1. Kubelet not running
sudo systemctl start kubelet

# 2. Memory pressure
kubectl describe node <node-name> | grep -A 20 "Allocated resources"
# Evict or resize pods

# 3. Disk pressure
df -h
# Clean up images: sudo crictl rmi --prune
# Clean up containers: sudo crictl rm $(sudo crictl ps -aq --state=exited)

# 4. Network unavailable
kubectl get pods -n kube-system | grep -E "calico|flannel|cilium"
# Restart CNI pods
```

## Best Practices

### Resource Requests and Limits

```yaml
# Always set requests (for scheduler)
# Set limits to prevent resource hogging
apiVersion: v1
kind: Pod
metadata:
  name: best-practice-pod
spec:
  containers:
  - name: app
    image: myapp:v1
    resources:
      requests:
        cpu: 100m       # Guaranteed CPU
        memory: 128Mi   # Guaranteed memory
      limits:
        cpu: 500m       # Can burst to 500m
        memory: 512Mi   # Hard limit (OOMKilled if exceeded)
```

### Health Probes

```yaml
# Use all three probes for production apps
spec:
  containers:
  - name: app
    image: myapp:v1

    startupProbe:
      httpGet:
        path: /startup
        port: 8080
      initialDelaySeconds: 0
      periodSeconds: 10
      failureThreshold: 30  # 5 min max startup

    livenessProbe:
      httpGet:
        path: /healthz
        port: 8080
      initialDelaySeconds: 0  # Startup probe handles delay
      periodSeconds: 10
      failureThreshold: 3

    readinessProbe:
      httpGet:
        path: /ready
        port: 8080
      initialDelaySeconds: 0
      periodSeconds: 5
      failureThreshold: 1
```

### Node Maintenance

```bash
# Before maintenance:

# 1. Cordon node (prevent new pods)
kubectl cordon <node-name>

# 2. Drain node (evict pods gracefully)
kubectl drain <node-name> \
  --ignore-daemonsets \
  --delete-emptydir-data \
  --grace-period=300

# 3. Perform maintenance

# 4. Uncordon node (allow scheduling)
kubectl uncordon <node-name>
```

## Advanced Kubelet Features

### CPU Management Policies

```yaml
# /var/lib/kubelet/config.yaml
apiVersion: kubelet.config.k8s.io/v1beta1
kind: KubeletConfiguration

# CPU Manager - Pin pods to specific CPU cores
cpuManagerPolicy: static  # none (default) or static
cpuManagerReconcilePeriod: 10s

# Reserved CPUs (not used by CPU manager)
reservedSystemCPUs: "0-1"  # Reserve first 2 CPUs for system
```

**Static CPU Manager Example:**

```yaml
# Pod with guaranteed QoS and integer CPU request
apiVersion: v1
kind: Pod
metadata:
  name: cpu-pinned-pod
spec:
  containers:
  - name: app
    image: cpu-intensive-app:v1
    resources:
      requests:
        cpu: 2          # Integer CPU (required for pinning)
        memory: 2Gi
      limits:
        cpu: 2          # Must equal request
        memory: 2Gi
```

**Kubelet CPU allocation:**
```bash
# Check CPU manager state
cat /var/lib/kubelet/cpu_manager_state

# Output:
# {
#   "policyName": "static",
#   "defaultCpuSet": "0-1,4-7",
#   "entries": {
#     "pod-uid-abc-container-app": "2-3"  # Exclusive CPUs for this container
#   }
# }

# Verify CPU pinning
taskset -cp $(pgrep -f "cpu-intensive-app")
# Output: pid 12345's current affinity list: 2,3
```

**Use cases:**
- High-performance computing
- Real-time applications
- Network packet processing (DPDK)
- Machine learning inference
- Database workloads requiring consistent latency

### Memory Management Policies

```yaml
apiVersion: kubelet.config.k8s.io/v1beta1
kind: KubeletConfiguration

# Memory Manager - NUMA awareness
memoryManagerPolicy: Static  # None (default) or Static

# Reserved memory
reservedMemory:
- numaNode: 0
  limits:
    memory: 1Gi
- numaNode: 1
  limits:
    memory: 1Gi
```

**NUMA-aware pod:**

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: numa-pod
spec:
  containers:
  - name: app
    image: myapp:v1
    resources:
      requests:
        cpu: 4
        memory: 8Gi
      limits:
        cpu: 4
        memory: 8Gi  # Guaranteed QoS required
```

**Kubelet NUMA allocation:**
```bash
# Check NUMA topology
numactl --hardware

# Check memory manager allocation
cat /var/lib/kubelet/memory_manager_state

# Verify pod NUMA binding
numastat -p $(pgrep -f "myapp")
```

### Topology Manager

```yaml
apiVersion: kubelet.config.k8s.io/v1beta1
kind: KubeletConfiguration

# Topology Manager - Coordinate CPU and device alignment
topologyManagerPolicy: single-numa-node  # none, best-effort, restricted, single-numa-node
topologyManagerScope: container  # container or pod
```

**Policies explained:**
```
none: No topology alignment
best-effort: Prefer NUMA alignment, but allow if not possible
restricted: Require NUMA alignment, fail if not possible
single-numa-node: All resources on single NUMA node (strictest)
```

**GPU + CPU affinity example:**

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: ml-training
spec:
  containers:
  - name: training
    image: tensorflow:gpu
    resources:
      requests:
        cpu: 8
        memory: 16Gi
        nvidia.com/gpu: 1
      limits:
        cpu: 8
        memory: 16Gi
        nvidia.com/gpu: 1
```

**Kubelet behavior with single-numa-node:**
```
1. Find NUMA node with GPU
2. Check if NUMA node has 8 CPUs available
3. Check if NUMA node has 16Gi memory available
4. If all conditions met: Allocate on same NUMA node
5. If conditions not met: Pod fails to schedule
```

### Device Plugin Framework

```yaml
# Kubelet discovers device plugins via Unix socket
# Device plugin socket path: /var/lib/kubelet/device-plugins/

# Example: NVIDIA GPU Plugin
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: nvidia-device-plugin
  namespace: kube-system
spec:
  selector:
    matchLabels:
      name: nvidia-device-plugin
  template:
    metadata:
      labels:
        name: nvidia-device-plugin
    spec:
      tolerations:
      - key: nvidia.com/gpu
        operator: Exists
        effect: NoSchedule
      containers:
      - name: nvidia-device-plugin
        image: nvcr.io/nvidia/k8s-device-plugin:v0.14.0
        env:
        - name: FAIL_ON_INIT_ERROR
          value: "false"
        securityContext:
          allowPrivilegeEscalation: false
          capabilities:
            drop: ["ALL"]
        volumeMounts:
        - name: device-plugin
          mountPath: /var/lib/kubelet/device-plugins
      volumes:
      - name: device-plugin
        hostPath:
          path: /var/lib/kubelet/device-plugins
```

**Using GPU resources:**

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: cuda-app
spec:
  containers:
  - name: cuda-container
    image: nvidia/cuda:11.8.0-base
    command: ["nvidia-smi"]
    resources:
      limits:
        nvidia.com/gpu: 2  # Request 2 GPUs
```

### Pod Overhead

```yaml
# RuntimeClass with pod overhead
apiVersion: node.k8s.io/v1
kind: RuntimeClass
metadata:
  name: kata-containers
handler: kata
overhead:
  podFixed:
    cpu: 250m      # Overhead for VM-based runtime
    memory: 120Mi

---
# Pod using RuntimeClass
apiVersion: v1
kind: Pod
metadata:
  name: secure-pod
spec:
  runtimeClassName: kata-containers
  containers:
  - name: app
    image: myapp:v1
    resources:
      requests:
        cpu: 1000m
        memory: 1Gi
```

**Kubelet resource calculation:**
```
Pod requests from scheduler perspective:
  CPU: 1000m (container) + 250m (overhead) = 1250m
  Memory: 1Gi (container) + 120Mi (overhead) = 1.12Gi

Node allocatable check:
  Available CPU: 2000m
  Required: 1250m ✓
  Available Memory: 4Gi
  Required: 1.12Gi ✓
```

### Graceful Node Shutdown

```yaml
apiVersion: kubelet.config.k8s.io/v1beta1
kind: KubeletConfiguration

# Graceful shutdown configuration
shutdownGracePeriod: 30s
shutdownGracePeriodCriticalPods: 10s

# Priority-based shutdown order
shutdownGracePeriodByPodPriority:
- priority: 100000
  shutdownGracePeriodSeconds: 10
- priority: 10000
  shutdownGracePeriodSeconds: 20
- priority: 1000
  shutdownGracePeriodSeconds: 30
- priority: 0
  shutdownGracePeriodSeconds: 60
```

**Shutdown sequence:**
```
1. Node receives shutdown signal (systemd, ACPI)
2. Kubelet detects shutdown
3. Mark node as NotReady
4. Start terminating pods by priority:
   - Critical pods (priority ≥100000): 10s grace period
   - High priority (10000-99999): 20s grace period
   - Normal priority (1000-9999): 30s grace period
   - Low priority (<1000): 60s grace period
5. Send SIGTERM to containers
6. Wait for grace period
7. Send SIGKILL to remaining containers
8. Node shuts down
```

### Eviction Signals and Thresholds

```yaml
apiVersion: kubelet.config.k8s.io/v1beta1
kind: KubeletConfiguration

# Hard eviction thresholds (immediate eviction)
evictionHard:
  memory.available: 100Mi
  nodefs.available: 10%
  nodefs.inodesFree: 5%
  imagefs.available: 15%
  pid.available: 10%

# Soft eviction thresholds (with grace period)
evictionSoft:
  memory.available: 500Mi
  nodefs.available: 15%
  nodefs.inodesFree: 10%
  imagefs.available: 20%

# Soft eviction grace periods
evictionSoftGracePeriod:
  memory.available: 1m30s
  nodefs.available: 2m
  nodefs.inodesFree: 2m
  imagefs.available: 2m

# Minimum reclaim
evictionMinimumReclaim:
  memory.available: 500Mi
  nodefs.available: 5%
  imagefs.available: 5%

# Pressure transition period
evictionPressureTransitionPeriod: 30s

# Maximum grace period for evicted pods
evictionMaxPodGracePeriod: 60
```

**Eviction scenario:**
```bash
# Node starts running low on memory
# Available memory: 450Mi (below soft threshold 500Mi)

# Kubelet behavior:
1. Start eviction grace period (1m30s)
2. Mark node condition: MemoryPressure=True
3. Scheduler stops placing BestEffort pods
4. Wait 1m30s
5. If still low memory after grace period:
   - Calculate pods to evict
   - Start with BestEffort pods
   - Then Burstable pods exceeding requests
   - Evict until memory.available > 500Mi + evictionMinimumReclaim (1000Mi)
6. Update node condition: MemoryPressure=False (after 30s transition period)
```

**Manual eviction testing:**
```bash
# Simulate memory pressure
stress-ng --vm 1 --vm-bytes 90% --timeout 60s

# Watch kubelet eviction
journalctl -u kubelet -f | grep -i evict

# Check evicted pods
kubectl get pods -A | grep Evicted

# View eviction events
kubectl get events -A --field-selector reason=Evicted
```

### Image Lifecycle Management

```yaml
apiVersion: kubelet.config.k8s.io/v1beta1
kind: KubeletConfiguration

# Image garbage collection
imageGCHighThresholdPercent: 85  # Start GC at 85% disk usage
imageGCLowThresholdPercent: 80   # Stop GC at 80% disk usage

# Image pull configuration
imagePullProgressDeadline: 1m
serializeImagePulls: true  # Pull one image at a time
maxParallelImagePulls: 5   # If serializeImagePulls=false

# Registry configuration
registryPullQPS: 5         # QPS for registry pulls
registryBurst: 10          # Burst for registry pulls
```

**Image garbage collection:**
```bash
# Check disk usage
df -h /var/lib/containerd

# Output: 86% used → Triggers imageGC

# Kubelet GC process:
1. List all images
2. Calculate total size
3. If disk usage > 85%:
   - Sort images by last used time (oldest first)
   - Delete unused images
   - Stop when disk usage < 80%
4. Never delete images currently in use by pods

# Manual image cleanup
sudo crictl images
sudo crictl rmi --prune  # Remove unused images
```

### Container Log Rotation

```yaml
apiVersion: kubelet.config.k8s.io/v1beta1
kind: KubeletConfiguration

# Container log rotation
containerLogMaxSize: 10Mi
containerLogMaxFiles: 5

# Example: Container logs location
# /var/log/pods/<namespace>_<pod-name>_<pod-uid>/<container-name>/
#   0.log (current)
#   0.log.20231015-120000.gz
#   0.log.20231015-110000.gz
#   ...
```

**Log rotation behavior:**
```
Container writes logs → stdout/stderr
         ↓
Container runtime captures logs
         ↓
Writes to: /var/log/pods/.../container-name/0.log
         ↓
When 0.log reaches 10Mi:
  - Rename: 0.log → 0.log.20231015-120000.gz (compressed)
  - Create new: 0.log
  - Keep max 5 files (delete oldest)
         ↓
kubectl logs shows: Current 0.log + previous compressed logs
```

## Production Use Cases

### Use Case 1: High-Performance Trading Application

```yaml
# Node with dedicated cores and NUMA alignment
apiVersion: v1
kind: Pod
metadata:
  name: trading-engine
spec:
  nodeSelector:
    node-type: high-frequency-trading
  priorityClassName: critical-trading
  containers:
  - name: engine
    image: trading-engine:v2.1
    resources:
      requests:
        cpu: 8          # Exclusive CPU cores
        memory: 16Gi    # Guaranteed memory
      limits:
        cpu: 8
        memory: 16Gi
    securityContext:
      capabilities:
        add:
        - SYS_NICE      # Allow RT scheduling
        - IPC_LOCK      # Lock memory
    env:
    - name: GOMAXPROCS
      value: "8"
    - name: NUMA_NODE
      valueFrom:
        fieldRef:
          fieldPath: metadata.annotations['topology.kubernetes.io/numa-node']
```

**Kubelet configuration for HFT node:**
```yaml
# /var/lib/kubelet/config.yaml
apiVersion: kubelet.config.k8s.io/v1beta1
kind: KubeletConfiguration

# CPU pinning
cpuManagerPolicy: static
reservedSystemCPUs: "0-1"

# NUMA alignment
memoryManagerPolicy: Static
topologyManagerPolicy: single-numa-node

# No swap
failSwapOn: true

# Aggressive eviction to protect critical pods
evictionHard:
  memory.available: 1Gi
  nodefs.available: 5%

# Reserved resources
systemReserved:
  cpu: 2
  memory: 4Gi
kubeReserved:
  cpu: 0
  memory: 1Gi
```

### Use Case 2: Machine Learning Training Cluster

```yaml
# GPU workload with topology awareness
apiVersion: v1
kind: Pod
metadata:
  name: ml-training-job
spec:
  restartPolicy: OnFailure
  containers:
  - name: trainer
    image: pytorch:gpu-2.0
    command:
    - python
    - train.py
    - --distributed
    resources:
      requests:
        cpu: 16
        memory: 64Gi
        nvidia.com/gpu: 4
      limits:
        cpu: 16
        memory: 64Gi
        nvidia.com/gpu: 4
    volumeMounts:
    - name: dataset
      mountPath: /data
      readOnly: true
    - name: checkpoints
      mountPath: /checkpoints
    - name: shm
      mountPath: /dev/shm
  volumes:
  - name: dataset
    persistentVolumeClaim:
      claimName: imagenet-dataset
  - name: checkpoints
    persistentVolumeClaim:
      claimName: model-checkpoints
  - name: shm
    emptyDir:
      medium: Memory
      sizeLimit: 32Gi
```

**Kubelet ML node configuration:**
```yaml
apiVersion: kubelet.config.k8s.io/v1beta1
kind: KubeletConfiguration

# GPU + CPU affinity
topologyManagerPolicy: single-numa-node
cpuManagerPolicy: static

# Large shared memory
allowedUnsafeSysctls:
- kernel.shm*

# Huge pages support
featureGates:
  HugePages: true

# Reserved for system
systemReserved:
  cpu: 4
  memory: 16Gi
```

### Use Case 3: Database with Persistent Storage

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: postgres-primary
spec:
  priorityClassName: database-critical
  containers:
  - name: postgres
    image: postgres:15-alpine
    resources:
      requests:
        cpu: 4
        memory: 16Gi
      limits:
        cpu: 8
        memory: 32Gi
    env:
    - name: POSTGRES_PASSWORD
      valueFrom:
        secretKeyRef:
          name: postgres-secret
          key: password
    - name: PGDATA
      value: /var/lib/postgresql/data/pgdata
    volumeMounts:
    - name: data
      mountPath: /var/lib/postgresql/data
    - name: config
      mountPath: /etc/postgresql/postgresql.conf
      subPath: postgresql.conf
    - name: wal
      mountPath: /var/lib/postgresql/wal
    livenessProbe:
      exec:
        command:
        - pg_isready
        - -U
        - postgres
      initialDelaySeconds: 30
      periodSeconds: 10
      timeoutSeconds: 5
      failureThreshold: 3
    readinessProbe:
      exec:
        command:
        - pg_isready
        - -U
        - postgres
      initialDelaySeconds: 5
      periodSeconds: 5
      timeoutSeconds: 3
      failureThreshold: 1
  volumes:
  - name: data
    persistentVolumeClaim:
      claimName: postgres-data
  - name: config
    configMap:
      name: postgres-config
  - name: wal
    persistentVolumeClaim:
      claimName: postgres-wal
```

**Kubelet volume attachment:**
```bash
# Kubelet coordinates with CSI driver
1. Pod scheduled to node
2. Kubelet calls CSI ControllerPublishVolume (attach EBS to EC2)
3. Wait for volume attachment (AWS attaches EBS to instance)
4. Kubelet calls CSI NodeStageVolume (format + global mount)
   # mkfs.ext4 /dev/nvme1n1
   # mount /dev/nvme1n1 /var/lib/kubelet/plugins/.../global
5. Kubelet calls CSI NodePublishVolume (bind mount to pod)
   # mount --bind /var/lib/kubelet/plugins/.../global /var/lib/kubelet/pods/.../postgres-data
6. Start container with volume mounted

# Verify volume mount
lsblk
kubectl exec postgres-primary -- df -h /var/lib/postgresql/data
```

### Use Case 4: Web Application with Auto-Scaling

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: web-app-xyz
  labels:
    app: web
    version: v2.1
spec:
  containers:
  - name: nginx
    image: nginx:1.25-alpine
    ports:
    - containerPort: 80
      name: http
    resources:
      requests:
        cpu: 100m
        memory: 128Mi
      limits:
        cpu: 500m
        memory: 512Mi
    startupProbe:
      httpGet:
        path: /health/startup
        port: 80
      failureThreshold: 30
      periodSeconds: 10
    livenessProbe:
      httpGet:
        path: /health/live
        port: 80
      periodSeconds: 10
      failureThreshold: 3
    readinessProbe:
      httpGet:
        path: /health/ready
        port: 80
      periodSeconds: 5
      failureThreshold: 1
    lifecycle:
      preStop:
        exec:
          command:
          - /bin/sh
          - -c
          - sleep 15 && nginx -s quit
```

**Kubelet lifecycle hooks:**
```
Container starts
         ↓
Startup probe (max 5 min)
         ↓
Container ready, accepting traffic
         ↓
Liveness/Readiness probes running
         ↓
Pod deletion initiated
         ↓
Kubelet executes preStop hook:
  - Sleep 15s (allow load balancer to deregister)
  - nginx -s quit (graceful shutdown)
         ↓
Wait for preStop completion (max 30s)
         ↓
Send SIGTERM to container
         ↓
Wait 30s grace period
         ↓
Send SIGKILL if still running
         ↓
Container terminated
```

### Use Case 5: Batch Job with Spot Instances

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: batch-processor
spec:
  restartPolicy: Never
  nodeSelector:
    node-lifecycle: spot
  tolerations:
  - key: spot-instance
    operator: Exists
    effect: NoSchedule
  priorityClassName: batch-low-priority
  containers:
  - name: processor
    image: batch-processor:v1
    command:
    - python
    - process.py
    - --checkpoint-dir=/checkpoints
    - --resume-on-failure
    resources:
      requests:
        cpu: 2
        memory: 4Gi
      limits:
        cpu: 4
        memory: 8Gi
    env:
    - name: SPOT_INSTANCE
      value: "true"
    - name: CHECKPOINT_INTERVAL
      value: "300"  # Checkpoint every 5 min
    volumeMounts:
    - name: checkpoints
      mountPath: /checkpoints
  volumes:
  - name: checkpoints
    persistentVolumeClaim:
      claimName: batch-checkpoints
  terminationGracePeriodSeconds: 120  # Allow time for checkpoint
```

**Kubelet spot instance handling:**
```
Spot instance receives termination notice (2 min warning)
         ↓
Node drains (kubectl drain node-spot-123)
         ↓
Kubelet receives pod deletion request
         ↓
Kubelet sends SIGTERM to container
         ↓
Application checkpoint handler:
  1. Receive SIGTERM
  2. Save current state to /checkpoints
  3. Exit gracefully
         ↓
Kubelet waits up to 120s (terminationGracePeriodSeconds)
         ↓
Container exits → Pod Completed
         ↓
Job controller creates new pod
         ↓
New pod resumes from checkpoint
```

## Advanced Debugging and Troubleshooting

### Kubelet Debug Endpoints

```bash
# Enable debug endpoints (non-production only)
curl -k https://localhost:10250/debug/pprof/

# CPU profile (30 seconds)
curl -k https://localhost:10250/debug/pprof/profile?seconds=30 > cpu.pprof
go tool pprof cpu.pprof

# Memory profile
curl -k https://localhost:10250/debug/pprof/heap > mem.pprof
go tool pprof mem.pprof

# Goroutine dump
curl -k https://localhost:10250/debug/pprof/goroutine?debug=2

# Check flags
curl -k https://localhost:10250/configz | jq .

# Check pod status
curl -k https://localhost:10250/pods | jq '.items[] | {name: .metadata.name, phase: .status.phase}'
```

### Kubelet Metrics Analysis

```bash
# Get all kubelet metrics
curl -k https://localhost:10250/metrics

# Key metrics to monitor:

# Pod start duration
kubelet_pod_start_duration_seconds

# Container runtime operations
kubelet_runtime_operations_duration_seconds

# Volume operations
storage_operation_duration_seconds

# PLEG (Pod Lifecycle Event Generator) relist
kubelet_pleg_relist_duration_seconds
kubelet_pleg_relist_interval_seconds

# Eviction stats
kubelet_evictions

# Node conditions
kubelet_node_status_capacity
kubelet_node_status_allocatable
```

**Prometheus queries for kubelet monitoring:**
```promql
# Pod start latency P99
histogram_quantile(0.99, rate(kubelet_pod_start_duration_seconds_bucket[5m]))

# PLEG unhealthy (should be 0)
kubelet_pleg_relist_duration_seconds > 3

# Eviction rate
rate(kubelet_evictions[5m])

# Node filesystem usage
1 - (kubelet_node_status_capacity{resource="ephemeral_storage"} - kubelet_node_status_allocatable{resource="ephemeral_storage"}) / kubelet_node_status_capacity{resource="ephemeral_storage"}
```

### Common Production Issues

#### Issue 1: PLEG is not healthy

```bash
# Symptom: Node becomes NotReady
# Error in kubelet logs: "PLEG is not healthy: pleg was last seen active 3m0s ago"

# Root causes:
# 1. High container churn rate
# 2. Slow container runtime
# 3. Network issues with container runtime

# Debug:
journalctl -u kubelet | grep PLEG

# Check container runtime
sudo crictl ps -a | wc -l  # Total containers
sudo crictl stats  # Container resource usage

# Solutions:
# 1. Increase PLEG interval (if high churn)
cat >> /var/lib/kubelet/config.yaml <<EOF
plegRelistPeriod: 3s  # Default: 1s
EOF

# 2. Tune container runtime (containerd)
cat >> /etc/containerd/config.toml <<EOF
[plugins."io.containerd.grpc.v1.cri"]
  max_container_log_line_size = 16384
  stream_server_address = "127.0.0.1"
  stream_server_port = "0"
EOF

sudo systemctl restart containerd kubelet
```

#### Issue 2: OOMKilled containers but memory available

```bash
# Symptom: Containers killed with OOMKilled even though node has free memory

# Root cause: Memory limit set lower than actual usage

# Debug:
# Check pod memory usage vs limits
kubectl top pod <pod-name>
kubectl describe pod <pod-name> | grep -A 5 Limits

# Check cgroup memory stats
POD_UID=$(kubectl get pod <pod-name> -o jsonpath='{.metadata.uid}')
cat /sys/fs/cgroup/memory/kubepods/burstable/pod${POD_UID}/memory.stat
cat /sys/fs/cgroup/memory/kubepods/burstable/pod${POD_UID}/memory.limit_in_bytes

# Check kernel logs
dmesg | grep -i oom

# Solutions:
# 1. Increase memory limits
kubectl set resources deployment <name> --limits=memory=2Gi

# 2. Identify memory leaks
kubectl exec <pod-name> -- ps aux --sort=-%mem | head -10

# 3. Use memory profiling
kubectl exec <pod-name> -- wget -O- localhost:6060/debug/pprof/heap > heap.pprof
```

#### Issue 3: ImagePullBackOff loops

```bash
# Symptom: Pod stuck in ImagePullBackOff

# Debug:
kubectl describe pod <pod-name> | grep -A 10 Events

# Common causes:

# 1. Image doesn't exist
# Events: Failed to pull image "myapp:v999": not found
# Solution: Fix image tag

# 2. Registry authentication failure
# Events: Failed to pull image: unauthorized
# Solution: Create/update image pull secret
kubectl create secret docker-registry regcred \
  --docker-server=registry.example.com \
  --docker-username=user \
  --docker-password=pass

# Add to pod spec:
# imagePullSecrets:
# - name: regcred

# 3. Rate limit exceeded (Docker Hub)
# Events: toomanyrequests: You have reached your pull rate limit
# Solution: Use authenticated pulls or mirror registry

# 4. Network issues
# Check kubelet can reach registry
curl -v https://registry.example.com/v2/

# Check DNS resolution
nslookup registry.example.com

# 5. Large image timeout
# Increase image pull deadline
cat >> /var/lib/kubelet/config.yaml <<EOF
imagePullProgressDeadline: 5m  # Default: 1m
EOF
sudo systemctl restart kubelet
```

#### Issue 4: Volume mount failures

```bash
# Symptom: Pod stuck in ContainerCreating with volume mount errors

# Debug:
kubectl describe pod <pod-name> | grep -A 20 Events

# Common causes:

# 1. PVC not bound
# Events: persistentvolumeclaim "data" not found
kubectl get pvc
kubectl describe pvc data

# 2. Volume already attached to another node
# Events: Volume is already exclusively attached to one node
# Solution: Force detach or delete old pod
kubectl delete pod <old-pod> --grace-period=0 --force

# 3. CSI driver not running
kubectl get pods -n kube-system | grep csi
kubectl logs -n kube-system <csi-pod>

# 4. Node doesn't have CSI plugin
# Check CSI node plugin daemonset
kubectl get ds -n kube-system | grep csi

# 5. Volume mount timeout
# Check kubelet logs
journalctl -u kubelet | grep -i "mount\|volume"

# Increase timeout (if slow storage)
cat >> /var/lib/kubelet/config.yaml <<EOF
volumePluginDir: /usr/libexec/kubernetes/kubelet-plugins/volume/exec
EOF
```

#### Issue 5: Pods evicted due to DiskPressure

```bash
# Symptom: Pods evicted with reason "The node was low on resource: ephemeral-storage"

# Debug:
# Check disk usage
df -h
df -i  # Check inodes

# Check which directory is full
du -sh /var/lib/kubelet/* | sort -h
du -sh /var/lib/containerd/* | sort -h

# Common causes:

# 1. Container logs filling disk
# Solution: Increase log rotation
cat >> /var/lib/kubelet/config.yaml <<EOF
containerLogMaxSize: 10Mi
containerLogMaxFiles: 3
EOF

# 2. Unused container images
# Solution: Manual cleanup
sudo crictl images
sudo crictl rmi --prune

# 3. Unused containers
sudo crictl ps -a --state=exited
sudo crictl rm $(sudo crictl ps -a --state=exited -q)

# 4. Emptydir volumes too large
kubectl get pods -o json | jq -r '.items[] | select(.spec.volumes[]?.emptyDir) | .metadata.name'

# 5. Adjust eviction thresholds
cat >> /var/lib/kubelet/config.yaml <<EOF
evictionHard:
  nodefs.available: 5%  # More aggressive
  imagefs.available: 10%
EOF
sudo systemctl restart kubelet
```

## Performance Optimization Checklist

```yaml
# Production-ready kubelet configuration
apiVersion: kubelet.config.k8s.io/v1beta1
kind: KubeletConfiguration

# ==================== CPU/Memory Management ====================
cpuManagerPolicy: static  # For latency-sensitive workloads
memoryManagerPolicy: Static  # For NUMA systems
topologyManagerPolicy: best-effort  # Or single-numa-node for strict alignment

# ==================== Resource Reservation ====================
systemReserved:
  cpu: 500m
  memory: 1Gi
  ephemeral-storage: 10Gi
kubeReserved:
  cpu: 200m
  memory: 512Mi
  ephemeral-storage: 5Gi
enforceNodeAllocatable:
- pods

# ==================== Eviction Tuning ====================
evictionHard:
  memory.available: 500Mi
  nodefs.available: 10%
  imagefs.available: 15%
evictionSoft:
  memory.available: 1Gi
  nodefs.available: 15%
evictionSoftGracePeriod:
  memory.available: 2m
  nodefs.available: 3m

# ==================== Image Management ====================
imageGCHighThresholdPercent: 85
imageGCLowThresholdPercent: 80
serializeImagePulls: false  # Parallel pulls for faster pod starts
maxParallelImagePulls: 5

# ==================== Logging ====================
containerLogMaxSize: 10Mi
containerLogMaxFiles: 5

# ==================== Security ====================
protectKernelDefaults: true
tlsCipherSuites:
- TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384
- TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384
rotateCertificates: true
serverTLSBootstrap: true

# ==================== Performance ====================
maxPods: 110  # Or higher for large nodes
podPidsLimit: 4096
cgroupDriver: systemd
cpuCFSQuota: true

# ==================== Stability ====================
nodeStatusUpdateFrequency: 10s
syncFrequency: 1m
eventRecordQPS: 5
eventBurst: 10
```

## References

- [Kubelet Documentation](https://kubernetes.io/docs/reference/command-line-tools-reference/kubelet/)
- [Kubelet Configuration](https://kubernetes.io/docs/tasks/administer-cluster/kubelet-config-file/)
- [Pod Lifecycle](https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/)
- [Container Runtime Interface (CRI)](https://kubernetes.io/docs/concepts/architecture/cri/)
- [Quality of Service](https://kubernetes.io/docs/concepts/workloads/pods/pod-qos/)
- [Node Pressure Eviction](https://kubernetes.io/docs/concepts/scheduling-eviction/node-pressure-eviction/)
- [Device Plugin](https://kubernetes.io/docs/concepts/extend-kubernetes/compute-storage-net/device-plugins/)
- [Topology Manager](https://kubernetes.io/docs/tasks/administer-cluster/topology-manager/)
