# kube-proxy

## Overview

**kube-proxy** is a network proxy that runs on each node in the Kubernetes cluster. It maintains network rules that allow network communication to pods from network sessions inside or outside the cluster. Essentially, kube-proxy implements the Kubernetes Service abstraction by maintaining network rules on nodes.

**Component Type:** Worker Node Network Proxy
**Process Name:** `kube-proxy`
**Default Port:** 10249 (metrics), 10256 (health check)
**Runs On:** All nodes (workers and masters)
**Mode Options:** iptables, ipvs, userspace (deprecated), kernelspace (Windows)

## What kube-proxy Actually Does

kube-proxy is the traffic cop of Kubernetes networking - it ensures that when you talk to a Service, your traffic gets routed to the right pods, with load balancing and high availability.

### Real-World Analogy
Think of kube-proxy like a hotel receptionist:
- **Guest arrives** → Client sends request to Service IP
- **Receptionist checks registry** → kube-proxy checks Service endpoints
- **Directs to room** → Routes traffic to healthy pod
- **Updates registry** → Watches for pod/service changes
- **Load distribution** → Spreads guests across available rooms

### Core Responsibilities

**1. Service Discovery & Load Balancing**
- Watches API server for Service and Endpoints objects
- Implements ClusterIP (virtual IP for services)
- Load balances traffic across pod endpoints
- Supports session affinity (sticky sessions)

**2. Network Rule Management**
- Creates iptables/ipvs rules for service routing
- Maintains NAT tables for ClusterIP translation
- Handles NodePort exposure
- Manages LoadBalancer traffic routing

**3. Health-Based Routing**
- Only routes to Ready endpoints
- Removes unhealthy pods from rotation
- Updates rules when endpoints change

## Architecture

### kube-proxy Modes

```
┌─────────────────────────────────────────────────────────────┐
│                    kube-proxy Modes                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌────────────────────────────────────────────────────┐   │
│  │  1. IPTABLES MODE (Default, most common)           │   │
│  ├────────────────────────────────────────────────────┤   │
│  │  - Uses netfilter/iptables rules                   │   │
│  │  - Random endpoint selection                       │   │
│  │  - Good for <1000 services                         │   │
│  │  - O(n) performance (linear)                       │   │
│  │  - No connection rebalancing                       │   │
│  └────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌────────────────────────────────────────────────────┐   │
│  │  2. IPVS MODE (High performance)                   │   │
│  ├────────────────────────────────────────────────────┤   │
│  │  - Uses Linux IPVS (IP Virtual Server)            │   │
│  │  - Multiple load balancing algorithms              │   │
│  │  - O(1) performance (constant time)                │   │
│  │  - Better for >1000 services                       │   │
│  │  - Supports connection rebalancing                 │   │
│  └────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌────────────────────────────────────────────────────┐   │
│  │  3. USERSPACE MODE (Deprecated)                    │   │
│  ├────────────────────────────────────────────────────┤   │
│  │  - kube-proxy handles traffic in userspace         │   │
│  │  - High latency, low throughput                    │   │
│  │  - Only for legacy compatibility                   │   │
│  └────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌────────────────────────────────────────────────────┐   │
│  │  4. KERNELSPACE MODE (Windows only)                │   │
│  ├────────────────────────────────────────────────────┤   │
│  │  - Uses Windows HNS (Host Network Service)         │   │
│  │  - Similar to iptables mode for Windows            │   │
│  └────────────────────────────────────────────────────┘   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Traffic Flow (iptables mode)

```
Client Pod (10.244.1.5)
         ↓
Sends request to Service ClusterIP (10.96.0.10:80)
         ↓
Packet enters OUTPUT chain
         ↓
iptables NAT PREROUTING chain
         ↓
KUBE-SERVICES chain (kube-proxy created)
         ↓
Match Service ClusterIP 10.96.0.10:80
         ↓
KUBE-SVC-XXXXX chain (specific service)
         ↓
Random selection via --probability
         ↓
KUBE-SEP-XXXXX chain (specific endpoint)
         ↓
DNAT to pod IP (10.244.2.10:8080)
         ↓
Packet routed to destination pod
         ↓
Pod receives traffic on port 8080
         ↓
Response packet returns
         ↓
SNAT applied (source becomes Service IP)
         ↓
Client receives response from Service IP
```

### Traffic Flow (IPVS mode)

```
Client Pod (10.244.1.5)
         ↓
Sends request to Service ClusterIP (10.96.0.10:80)
         ↓
Packet intercepted by IPVS
         ↓
IPVS virtual server: 10.96.0.10:80
         ↓
Load balancing algorithm (rr, lc, sh, etc.)
         ↓
Select real server (pod endpoint)
         ↓
Direct routing to pod IP (10.244.2.10:8080)
         ↓
Pod receives traffic
         ↓
Response returns via IPVS
         ↓
Client receives response
```

## Installation and Configuration

### DaemonSet Deployment

```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: kube-proxy
  namespace: kube-system
  labels:
    k8s-app: kube-proxy
spec:
  selector:
    matchLabels:
      k8s-app: kube-proxy
  updateStrategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 1
  template:
    metadata:
      labels:
        k8s-app: kube-proxy
    spec:
      priorityClassName: system-node-critical
      hostNetwork: true
      serviceAccountName: kube-proxy
      tolerations:
      - operator: Exists
        effect: NoSchedule
      - operator: Exists
        effect: NoExecute
      containers:
      - name: kube-proxy
        image: registry.k8s.io/kube-proxy:v1.28.0
        command:
        - /usr/local/bin/kube-proxy
        - --config=/var/lib/kube-proxy/config.conf
        - --hostname-override=$(NODE_NAME)

        env:
        - name: NODE_NAME
          valueFrom:
            fieldRef:
              fieldPath: spec.nodeName

        securityContext:
          privileged: true

        volumeMounts:
        - name: kube-proxy
          mountPath: /var/lib/kube-proxy
        - name: xtables-lock
          mountPath: /run/xtables.lock
        - name: lib-modules
          mountPath: /lib/modules
          readOnly: true

        resources:
          requests:
            cpu: 100m
            memory: 128Mi
          limits:
            memory: 256Mi

        livenessProbe:
          httpGet:
            host: 127.0.0.1
            path: /healthz
            port: 10256
          initialDelaySeconds: 15
          periodSeconds: 10
          failureThreshold: 3

      volumes:
      - name: kube-proxy
        configMap:
          name: kube-proxy
      - name: xtables-lock
        hostPath:
          path: /run/xtables.lock
          type: FileOrCreate
      - name: lib-modules
        hostPath:
          path: /lib/modules
```

### ConfigMap Configuration

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: kube-proxy
  namespace: kube-system
data:
  config.conf: |
    apiVersion: kubeproxy.config.k8s.io/v1alpha1
    kind: KubeProxyConfiguration

    # ==================== API Server Connection ====================
    clientConnection:
      kubeconfig: /var/lib/kube-proxy/kubeconfig.conf
      qps: 5
      burst: 10

    # ==================== Proxy Mode ====================
    mode: "ipvs"  # iptables, ipvs, or userspace

    # ==================== IPVS Configuration ====================
    ipvs:
      # Load balancing algorithms:
      # - rr: Round Robin (default)
      # - lc: Least Connection
      # - dh: Destination Hashing
      # - sh: Source Hashing
      # - sed: Shortest Expected Delay
      # - nq: Never Queue
      scheduler: "rr"

      # Enable connection rebalancing
      minSyncPeriod: 0s
      syncPeriod: 30s

      # Exclude CIDRs from IPVS masquerading
      excludeCIDRs: []

      # Strict ARP mode (for MetalLB compatibility)
      strictARP: false

      # TCP timeout
      tcpTimeout: 0s
      tcpFinTimeout: 0s
      udpTimeout: 0s

    # ==================== IPTables Configuration ====================
    iptables:
      masqueradeAll: false
      masqueradeBit: 14
      minSyncPeriod: 0s
      syncPeriod: 30s

      # Localhost NodePort access
      localhostNodePorts: true

    # ==================== Cluster Configuration ====================
    clusterCIDR: "10.244.0.0/16"

    # ==================== Feature Gates ====================
    featureGates:
      # Enable service topology awareness
      # ServiceTopology: true
      # Enable endpoint slices
      # EndpointSliceProxying: true

    # ==================== NodePort Configuration ====================
    nodePortAddresses: []  # Empty = all interfaces, or specify CIDRs

    # ==================== Conntrack Configuration ====================
    conntrack:
      maxPerCore: 32768
      min: 131072
      tcpEstablishedTimeout: 24h
      tcpCloseWaitTimeout: 1h

    # ==================== Health & Metrics ====================
    healthzBindAddress: 0.0.0.0:10256
    metricsBindAddress: 0.0.0.0:10249

    # ==================== Logging ====================
    logging:
      format: text  # text or json
      verbosity: 2

    # ==================== OOM Score ====================
    oomScoreAdj: -999  # Protect from OOM killer

    # ==================== Hostname Override ====================
    # hostnameOverride: ""  # Set via --hostname-override flag

  kubeconfig.conf: |
    apiVersion: v1
    kind: Config
    clusters:
    - cluster:
        certificate-authority: /var/run/secrets/kubernetes.io/serviceaccount/ca.crt
        server: https://kubernetes.default.svc.cluster.local
      name: default
    contexts:
    - context:
        cluster: default
        namespace: default
        user: default
      name: default
    current-context: default
    users:
    - name: default
      user:
        tokenFile: /var/run/secrets/kubernetes.io/serviceaccount/token
```

### RBAC Configuration

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: kube-proxy
  namespace: kube-system

---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: system:kube-proxy
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: system:node-proxier
subjects:
- kind: ServiceAccount
  name: kube-proxy
  namespace: kube-system
```

## iptables Mode Deep Dive

### How iptables Rules Work

```bash
# View kube-proxy created chains
sudo iptables -t nat -L -n -v

# Main chains created by kube-proxy:
# - KUBE-SERVICES: Entry point for service traffic
# - KUBE-NODEPORTS: NodePort services
# - KUBE-POSTROUTING: SNAT for outbound traffic
# - KUBE-SVC-*: Per-service chains
# - KUBE-SEP-*: Per-endpoint chains
```

### Example Service Rules

```yaml
# Service definition
apiVersion: v1
kind: Service
metadata:
  name: web-app
spec:
  type: ClusterIP
  clusterIP: 10.96.100.10
  selector:
    app: web
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8080

# Endpoints (3 pods)
# - 10.244.1.10:8080
# - 10.244.2.20:8080
# - 10.244.3.30:8080
```

**Generated iptables rules:**

```bash
# Entry point - match service ClusterIP
-A KUBE-SERVICES -d 10.96.100.10/32 -p tcp -m tcp --dport 80 -j KUBE-SVC-ABCDEF123456

# Service chain - load balance across endpoints
-A KUBE-SVC-ABCDEF123456 -m statistic --mode random --probability 0.33333 -j KUBE-SEP-ENDPOINT1
-A KUBE-SVC-ABCDEF123456 -m statistic --mode random --probability 0.50000 -j KUBE-SEP-ENDPOINT2
-A KUBE-SVC-ABCDEF123456 -j KUBE-SEP-ENDPOINT3

# Endpoint 1 chain - DNAT to pod
-A KUBE-SEP-ENDPOINT1 -p tcp -m tcp -j DNAT --to-destination 10.244.1.10:8080

# Endpoint 2 chain - DNAT to pod
-A KUBE-SEP-ENDPOINT2 -p tcp -m tcp -j DNAT --to-destination 10.244.2.20:8080

# Endpoint 3 chain - DNAT to pod
-A KUBE-SEP-ENDPOINT3 -p tcp -m tcp -j DNAT --to-destination 10.244.3.30:8080

# SNAT for return traffic
-A KUBE-POSTROUTING -m mark --mark 0x4000/0x4000 -j MASQUERADE
```

### NodePort Service Rules

```yaml
apiVersion: v1
kind: Service
metadata:
  name: web-app
spec:
  type: NodePort
  clusterIP: 10.96.100.10
  selector:
    app: web
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8080
    nodePort: 30080
```

**Additional iptables rules:**

```bash
# KUBE-NODEPORTS chain - match NodePort
-A KUBE-NODEPORTS -p tcp -m tcp --dport 30080 -j KUBE-SVC-ABCDEF123456

# Allow NodePort on all interfaces (or specific IPs)
-A KUBE-SERVICES ! -s 10.244.0.0/16 -d 10.96.100.10/32 -p tcp -m tcp --dport 80 -j KUBE-MARK-MASQ

# Masquerade external traffic
-A KUBE-POSTROUTING -m mark --mark 0x4000/0x4000 -j MASQUERADE
```

### Session Affinity (Sticky Sessions)

```yaml
apiVersion: v1
kind: Service
metadata:
  name: web-app
spec:
  sessionAffinity: ClientIP
  sessionAffinityConfig:
    clientIP:
      timeoutSeconds: 10800  # 3 hours
  selector:
    app: web
  ports:
  - port: 80
    targetPort: 8080
```

**iptables rules with session affinity:**

```bash
# Use recent module to track client IPs
-A KUBE-SVC-ABCDEF123456 -m recent --name KUBE-SEP-ENDPOINT1 --rcheck --seconds 10800 --reap -j KUBE-SEP-ENDPOINT1
-A KUBE-SVC-ABCDEF123456 -m recent --name KUBE-SEP-ENDPOINT2 --rcheck --seconds 10800 --reap -j KUBE-SEP-ENDPOINT2
-A KUBE-SVC-ABCDEF123456 -m recent --name KUBE-SEP-ENDPOINT3 --rcheck --seconds 10800 --reap -j KUBE-SEP-ENDPOINT3

# Random selection with recent tracking
-A KUBE-SVC-ABCDEF123456 -m statistic --mode random --probability 0.33333 -j KUBE-SEP-ENDPOINT1
-A KUBE-SEP-ENDPOINT1 -m recent --name KUBE-SEP-ENDPOINT1 --set -p tcp -m tcp -j DNAT --to-destination 10.244.1.10:8080
```

## IPVS Mode Deep Dive

### IPVS vs iptables Comparison

| Feature | iptables | IPVS |
|---------|----------|------|
| Performance | O(n) - Linear | O(1) - Constant |
| Max Services | ~1,000 | 10,000+ |
| Load Balancing | Random only | 8+ algorithms |
| Connection Tracking | Yes | Yes |
| Session Affinity | Limited | Full support |
| Rule Management | Complex | Simpler |

### IPVS Load Balancing Algorithms

**1. Round Robin (rr) - Default**
```bash
# Distributes connections evenly
Request 1 → Pod A
Request 2 → Pod B
Request 3 → Pod C
Request 4 → Pod A (cycle repeats)
```

**2. Least Connection (lc)**
```bash
# Sends to pod with fewest active connections
Pod A: 5 connections → Skip
Pod B: 2 connections → Selected ✓
Pod C: 8 connections → Skip
```

**3. Source Hashing (sh)**
```bash
# Same client always goes to same pod
Client 192.168.1.10 → hash(192.168.1.10) → Pod B
Client 192.168.1.11 → hash(192.168.1.11) → Pod A
Client 192.168.1.10 → hash(192.168.1.10) → Pod B (consistent)
```

**4. Destination Hashing (dh)**
```bash
# Based on destination IP (less common in k8s)
```

**5. Shortest Expected Delay (sed)**
```bash
# (Connections + 1) / Weight
Pod A: (5 + 1) / 10 = 0.6 → Skip
Pod B: (2 + 1) / 10 = 0.3 → Selected ✓
Pod C: (8 + 1) / 10 = 0.9 → Skip
```

**6. Never Queue (nq)**
```bash
# Like SED but never queue if server with 0 connections exists
```

### IPVS Configuration and Viewing

```bash
# Install ipvsadm
sudo apt-get install ipvsadm

# View IPVS virtual servers
sudo ipvsadm -L -n

# Example output:
# IP Virtual Server version 1.2.1 (size=4096)
# Prot LocalAddress:Port Scheduler Flags
#   -> RemoteAddress:Port           Forward Weight ActiveConn InActConn
# TCP  10.96.100.10:80 rr
#   -> 10.244.1.10:8080             Masq    1      0          0
#   -> 10.244.2.20:8080             Masq    1      0          0
#   -> 10.244.3.30:8080             Masq    1      0          0

# View with statistics
sudo ipvsadm -L -n --stats

# View connection tracking
sudo ipvsadm -L -n --connection

# Save IPVS rules
sudo ipvsadm-save > ipvs-rules.txt

# Restore IPVS rules
sudo ipvsadm-restore < ipvs-rules.txt
```

### IPVS Kernel Modules

```bash
# Required kernel modules for IPVS
sudo modprobe ip_vs
sudo modprobe ip_vs_rr     # Round Robin
sudo modprobe ip_vs_wrr    # Weighted Round Robin
sudo modprobe ip_vs_sh     # Source Hashing
sudo modprobe ip_vs_dh     # Destination Hashing
sudo modprobe nf_conntrack_ipv4

# Verify modules loaded
lsmod | grep -e ip_vs -e nf_conntrack

# Auto-load on boot
cat >> /etc/modules-load.d/ipvs.conf <<EOF
ip_vs
ip_vs_rr
ip_vs_wrr
ip_vs_sh
nf_conntrack
EOF
```

### IPVS with Calico/Cilium

```yaml
# kube-proxy IPVS mode with Calico
apiVersion: kubeproxy.config.k8s.io/v1alpha1
kind: KubeProxyConfiguration
mode: ipvs
ipvs:
  scheduler: rr
  strictARP: true  # Required for MetalLB
  excludeCIDRs:
  - 192.168.0.0/16  # Exclude Calico pod CIDR from masquerade
```

## Service Types and kube-proxy Behavior

### ClusterIP (Internal Only)

```yaml
apiVersion: v1
kind: Service
metadata:
  name: backend
spec:
  type: ClusterIP
  clusterIP: 10.96.50.100
  selector:
    app: backend
  ports:
  - port: 80
    targetPort: 8080
```

**kube-proxy behavior:**
- Creates rules for ClusterIP (10.96.50.100:80)
- Only accessible within cluster
- Load balances to pod endpoints
- No external access

### NodePort (External via Node IP)

```yaml
apiVersion: v1
kind: Service
metadata:
  name: web
spec:
  type: NodePort
  selector:
    app: web
  ports:
  - port: 80
    targetPort: 8080
    nodePort: 30080
```

**kube-proxy behavior:**
- Creates ClusterIP rules (10.96.x.x:80)
- Opens port 30080 on ALL nodes
- Traffic to NodeIP:30080 → Pod endpoints
- Supports externalTrafficPolicy: Local/Cluster

**Access methods:**
```bash
# Via ClusterIP (internal)
curl http://10.96.x.x:80

# Via NodePort (external)
curl http://node1-ip:30080
curl http://node2-ip:30080  # Any node works
```

### LoadBalancer (Cloud Provider LB)

```yaml
apiVersion: v1
kind: Service
metadata:
  name: web
spec:
  type: LoadBalancer
  selector:
    app: web
  ports:
  - port: 80
    targetPort: 8080
```

**kube-proxy behavior:**
- Creates ClusterIP + NodePort rules
- Cloud provider creates external LB
- LB forwards to NodePort on nodes
- Traffic: LB → NodePort → Pods

### ExternalName (DNS CNAME)

```yaml
apiVersion: v1
kind: Service
metadata:
  name: external-db
spec:
  type: ExternalName
  externalName: db.example.com
```

**kube-proxy behavior:**
- No iptables/IPVS rules created
- CoreDNS creates CNAME record
- Pods resolve external-db → db.example.com

### Headless Service (No ClusterIP)

```yaml
apiVersion: v1
kind: Service
metadata:
  name: database
spec:
  clusterIP: None  # Headless
  selector:
    app: database
  ports:
  - port: 5432
```

**kube-proxy behavior:**
- No ClusterIP allocated
- No load balancing
- DNS returns all pod IPs (A records)
- Client handles load balancing

## Advanced Features

### External Traffic Policy

```yaml
apiVersion: v1
kind: Service
metadata:
  name: web
spec:
  type: NodePort
  externalTrafficPolicy: Local  # or Cluster (default)
  selector:
    app: web
  ports:
  - port: 80
    targetPort: 8080
    nodePort: 30080
```

**Cluster vs Local:**

| externalTrafficPolicy | Cluster (default) | Local |
|----------------------|-------------------|-------|
| Load balancing | Across all pods | Only local node pods |
| Source IP | Lost (SNAT) | Preserved |
| Availability | Always available | Node without pods returns error |
| Use case | General traffic | Need source IP, geo-routing |

**Example scenario:**
```bash
# Cluster mode:
Traffic to node1:30080 → SNAT → Any pod (node1, node2, node3)
Source IP seen by pod: 10.244.x.x (node IP)

# Local mode:
Traffic to node1:30080 → Only pods on node1
Source IP seen by pod: Original client IP
Traffic to node2:30080 → Fails if no pods on node2
```

### Internal Traffic Policy

```yaml
apiVersion: v1
kind: Service
metadata:
  name: cache
spec:
  type: ClusterIP
  internalTrafficPolicy: Local  # or Cluster (default)
  selector:
    app: cache
  ports:
  - port: 6379
```

**Benefit:**
- Keeps traffic on same node (reduces network hops)
- Better performance for node-local caching

### Topology Aware Hints (Topology Keys)

```yaml
apiVersion: v1
kind: Service
metadata:
  name: web
  annotations:
    service.kubernetes.io/topology-aware-hints: auto
spec:
  selector:
    app: web
  ports:
  - port: 80
```

**Behavior:**
- Routes traffic to endpoints in same zone/region
- Reduces cross-AZ traffic costs
- Falls back to normal routing if no local endpoints

## Real-World Use Cases

### Use Case 1: High-Traffic Web Application

```yaml
# Service with session affinity for stateful connections
apiVersion: v1
kind: Service
metadata:
  name: web-app
  annotations:
    service.kubernetes.io/topology-aware-hints: auto
spec:
  type: LoadBalancer
  sessionAffinity: ClientIP
  sessionAffinityConfig:
    clientIP:
      timeoutSeconds: 3600  # 1 hour sticky sessions
  selector:
    app: web
  ports:
  - name: http
    port: 80
    targetPort: 8080
  - name: https
    port: 443
    targetPort: 8443
```

**kube-proxy (IPVS mode):**
```bash
# Configure for high performance
mode: ipvs
ipvs:
  scheduler: sh  # Source hashing for session affinity
  syncPeriod: 10s  # Faster endpoint updates

conntrack:
  maxPerCore: 65536  # Higher connection tracking
  tcpEstablishedTimeout: 1h  # Match session timeout
```

### Use Case 2: Database with Regional Routing

```yaml
# StatefulSet Service - headless for direct pod access
apiVersion: v1
kind: Service
metadata:
  name: postgres-headless
spec:
  clusterIP: None
  publishNotReadyAddresses: true
  selector:
    app: postgres
  ports:
  - port: 5432

---
# ClusterIP for read replicas with zone routing
apiVersion: v1
kind: Service
metadata:
  name: postgres-read
  annotations:
    service.kubernetes.io/topology-aware-hints: auto
spec:
  selector:
    app: postgres
    role: replica
  ports:
  - port: 5432
```

**Application connection:**
```go
// Write to primary (direct pod DNS)
writeDB := "postgres-0.postgres-headless.default.svc.cluster.local:5432"

// Read from local zone replicas (load balanced)
readDB := "postgres-read.default.svc.cluster.local:5432"
```

### Use Case 3: Microservices with Service Mesh

```yaml
# Service without kube-proxy (service mesh handles routing)
apiVersion: v1
kind: Service
metadata:
  name: orders-api
  labels:
    service: orders
spec:
  selector:
    app: orders
  ports:
  - name: grpc
    port: 9090
    targetPort: 9090
  - name: http
    port: 8080
    targetPort: 8080
```

**With Istio/Linkerd:**
```yaml
# kube-proxy can run in parallel
# Service mesh (Envoy) intercepts traffic before kube-proxy
# Provides advanced features:
# - Retries, timeouts, circuit breaking
# - Mutual TLS
# - Traffic shifting (canary, blue-green)
# - Distributed tracing
```

### Use Case 4: Multi-Port Service

```yaml
apiVersion: v1
kind: Service
metadata:
  name: app-server
spec:
  type: NodePort
  selector:
    app: server
  ports:
  - name: http
    port: 80
    targetPort: 8080
    nodePort: 30080
    protocol: TCP
  - name: https
    port: 443
    targetPort: 8443
    nodePort: 30443
    protocol: TCP
  - name: metrics
    port: 9090
    targetPort: 9090
    protocol: TCP  # No NodePort
```

**kube-proxy rules:**
```bash
# Creates separate chains for each port
KUBE-SVC-HTTP-XXXXX    (ClusterIP:80, NodePort:30080)
KUBE-SVC-HTTPS-XXXXX   (ClusterIP:443, NodePort:30443)
KUBE-SVC-METRICS-XXXXX (ClusterIP:9090, internal only)
```

### Use Case 5: External Service Integration

```yaml
# Service pointing to external database
apiVersion: v1
kind: Service
metadata:
  name: external-mysql
spec:
  type: ClusterIP
  ports:
  - port: 3306

---
# Manual endpoints (no selector)
apiVersion: v1
kind: Endpoints
metadata:
  name: external-mysql
subsets:
- addresses:
  - ip: 192.168.1.100  # External DB server
  - ip: 192.168.1.101  # External DB replica
  ports:
  - port: 3306
```

**kube-proxy behavior:**
- Creates ClusterIP service
- Load balances to external IPs
- Pods access via service DNS: external-mysql.default.svc.cluster.local

## Monitoring and Troubleshooting

### Prometheus Metrics

```bash
# Get kube-proxy metrics
curl http://localhost:10249/metrics

# Key metrics:
kubeproxy_sync_proxy_rules_duration_seconds  # Rule sync latency
kubeproxy_sync_proxy_rules_last_timestamp_seconds  # Last sync time
kubeproxy_network_programming_duration_seconds  # Network programming latency
```

### iptables Mode Debugging

```bash
# View all kube-proxy chains
sudo iptables -t nat -L -n -v | grep KUBE

# View specific service
sudo iptables -t nat -L KUBE-SERVICES -n -v | grep <service-ip>

# Trace packet flow
sudo iptables -t raw -A PREROUTING -p tcp --dport 80 -j TRACE
sudo iptables -t raw -A OUTPUT -p tcp --dport 80 -j TRACE

# View trace logs (requires iptables logging enabled)
sudo tail -f /var/log/syslog | grep TRACE

# Count rules
sudo iptables -t nat -L -n | wc -l

# Check for duplicates
sudo iptables -t nat -L -n | sort | uniq -d
```

### IPVS Mode Debugging

```bash
# View all virtual servers
sudo ipvsadm -L -n

# View specific service
sudo ipvsadm -L -n -t 10.96.100.10:80

# View connection statistics
sudo ipvsadm -L -n --stats

# View real-time connections
sudo ipvsadm -L -n -c

# Check if endpoints are reachable
sudo ipvsadm -L -n --rate

# Test connectivity
nc -zv 10.96.100.10 80
```

### Common Issues

#### Issue 1: Service Not Accessible

```bash
# 1. Check service exists
kubectl get svc <service-name>

# 2. Check endpoints exist
kubectl get endpoints <service-name>

# 3. Check kube-proxy running
kubectl get pods -n kube-system -l k8s-app=kube-proxy

# 4. Check kube-proxy logs
kubectl logs -n kube-system <kube-proxy-pod>

# 5. Verify iptables/IPVS rules
# iptables mode:
sudo iptables -t nat -L -n | grep <service-ip>

# IPVS mode:
sudo ipvsadm -L -n | grep <service-ip>

# 6. Test from pod
kubectl run -it --rm debug --image=busybox --restart=Never -- sh
wget -O- http://<service-ip>:<port>
```

#### Issue 2: Session Affinity Not Working

```bash
# Check service configuration
kubectl get svc <service-name> -o yaml | grep -A 5 sessionAffinity

# iptables mode: Check recent module
sudo iptables -t nat -L -n -v | grep recent

# IPVS mode: Check scheduler
sudo ipvsadm -L -n | grep sh  # Should show "sh" scheduler

# Test from same client
for i in {1..10}; do curl http://<service-ip>; done
# Should hit same pod
```

#### Issue 3: Source IP Lost

```bash
# Check externalTrafficPolicy
kubectl get svc <service-name> -o yaml | grep externalTrafficPolicy

# If Cluster (default), source IP is SNAT'd
# Change to Local to preserve source IP:
kubectl patch svc <service-name> -p '{"spec":{"externalTrafficPolicy":"Local"}}'

# Verify in pod
kubectl exec <pod> -- env | grep X-Forwarded-For
```

#### Issue 4: High Latency/Packet Loss

```bash
# Check conntrack table size
sudo sysctl net.netfilter.nf_conntrack_count
sudo sysctl net.netfilter.nf_conntrack_max

# Increase if needed
sudo sysctl -w net.netfilter.nf_conntrack_max=524288

# Permanent setting
echo "net.netfilter.nf_conntrack_max = 524288" >> /etc/sysctl.conf

# Check kube-proxy conntrack settings
kubectl get cm -n kube-system kube-proxy -o yaml | grep -A 5 conntrack
```

## Performance Tuning

### iptables Mode Optimization

```yaml
apiVersion: kubeproxy.config.k8s.io/v1alpha1
kind: KubeProxyConfiguration
mode: iptables
iptables:
  minSyncPeriod: 1s  # Minimum time between syncs
  syncPeriod: 30s     # Maximum time between syncs
  masqueradeAll: false  # Only masquerade when necessary

conntrack:
  maxPerCore: 32768      # Max conntrack entries per CPU core
  min: 131072            # Minimum total entries
  tcpEstablishedTimeout: 24h
  tcpCloseWaitTimeout: 1h
```

### IPVS Mode Optimization

```yaml
apiVersion: kubeproxy.config.k8s.io/v1alpha1
kind: KubeProxyConfiguration
mode: ipvs
ipvs:
  scheduler: lc  # Least connection for better distribution
  minSyncPeriod: 0s
  syncPeriod: 30s
  tcpTimeout: 900s
  tcpFinTimeout: 120s
  udpTimeout: 300s

conntrack:
  maxPerCore: 65536  # Higher for IPVS
  min: 262144
```

### Kernel Tuning

```bash
# /etc/sysctl.conf
# Increase conntrack table
net.netfilter.nf_conntrack_max = 1048576

# Increase conntrack buckets
net.netfilter.nf_conntrack_buckets = 262144

# TCP keepalive
net.ipv4.tcp_keepalive_time = 600
net.ipv4.tcp_keepalive_intvl = 60
net.ipv4.tcp_keepalive_probes = 3

# Increase local port range
net.ipv4.ip_local_port_range = 10000 65535

# Enable TCP fast recycling (use with caution)
net.ipv4.tcp_tw_reuse = 1

# Apply
sudo sysctl -p
```

## Migration from iptables to IPVS

```bash
# 1. Ensure IPVS kernel modules loaded
sudo modprobe ip_vs ip_vs_rr ip_vs_wrr ip_vs_sh

# 2. Update kube-proxy ConfigMap
kubectl edit cm kube-proxy -n kube-system
# Change: mode: "iptables" to mode: "ipvs"

# 3. Rolling restart kube-proxy
kubectl rollout restart ds kube-proxy -n kube-system

# 4. Verify IPVS mode active
kubectl logs -n kube-system -l k8s-app=kube-proxy | grep "Using ipvs Proxier"

# 5. Verify rules
sudo ipvsadm -L -n

# 6. Test services
kubectl run -it --rm test --image=busybox --restart=Never -- wget -O- http://<service-ip>
```

## References

- [kube-proxy Documentation](https://kubernetes.io/docs/reference/command-line-tools-reference/kube-proxy/)
- [Service Networking](https://kubernetes.io/docs/concepts/services-networking/service/)
- [IPVS Mode](https://kubernetes.io/blog/2018/07/09/ipvs-based-in-cluster-load-balancing-deep-dive/)
- [Network Policies](https://kubernetes.io/docs/concepts/services-networking/network-policies/)
