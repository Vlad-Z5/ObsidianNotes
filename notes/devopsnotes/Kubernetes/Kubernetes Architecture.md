## Core Components & Architecture Deep Dive

### Control Plane Components

#### kube-apiserver

The API server is the central hub of all Kubernetes operations, serving REST APIs and handling all cluster communication.

**DevOps Responsibilities:**

- Configure API server flags for audit logging: `--audit-log-path`, `--audit-policy-file`
- Manage API server profiling endpoints for performance analysis
- Set up webhook authentication and authorization configurations
- Configure admission controllers (ValidatingAdmissionWebhook, MutatingAdmissionWebhook)
- Implement rate limiting to prevent API abuse
- Monitor API server metrics: request latency, error rates, certificate expiration
- Manage multiple API versions and deprecation policies
- Configure OIDC authentication providers for SSO integration
- Set up encryption providers for etcd data encryption
- Handle API server certificate rotation and PKI management

**Production Considerations:**

- Run multiple API server replicas behind a load balancer for HA
- Configure proper resource limits and requests
- Implement network policies to restrict API server access
- Set up monitoring alerts for API server unavailability
- Regular backup of API server configuration and certificates

#### kube-controller-manager

Runs all core Kubernetes controllers that implement the reconciliation loops.

**Individual Controllers Deep Dive:**

**deployment-controller**: Manages deployment rollouts and rollbacks

- Handles rolling update strategy parameters (maxSurge, maxUnavailable)
- Manages revision history and rollback operations
- Coordinates with ReplicaSet controller for pod management
- DevOps monitoring: deployment rollout status, failed deployments

**replicaset-controller**: Ensures desired pod replica count

- Handles pod creation/deletion based on selector matching
- Manages pod disruption during node failures
- Coordinates with scheduler for pod placement

**endpoint-controller**: Manages service endpoints

- Updates endpoint objects when pods are created/deleted/become ready
- Critical for service discovery functionality
- Monitors pod readiness probes to determine endpoint eligibility

**namespace-controller**: Manages namespace lifecycle

- Handles namespace deletion and cleanup of contained resources
- Enforces namespace finalizers and deletion policies

**serviceaccount-controller**: Manages service account tokens

- Creates default service accounts in namespaces
- Handles token creation and rotation
- Manages projected service account tokens (bound tokens)

**statefulset-controller**: Manages stateful application deployments

- Handles ordered deployment and deletion
- Manages persistent volume claim creation and binding
- Implements rolling update strategies for stateful apps

**hpa-controller**: Implements horizontal pod autoscaling

- Queries metrics API for scaling decisions
- Calculates desired replica count based on target metrics
- Implements scaling algorithms and stability windows

**cronjob-controller**: Manages scheduled job execution

- Creates job objects based on cron schedule
- Handles job history cleanup and concurrency policies
- Manages timezone considerations and missed job handling

**volume-controller**: Manages persistent volume lifecycle

- Handles PV/PVC binding operations
- Coordinates with CSI drivers for dynamic provisioning
- Manages volume attachment/detachment operations

**DevOps Configuration:**

- Set controller-specific flags for behavior tuning
- Monitor controller queue depths and processing rates
- Configure leader election for controller manager HA
- Set appropriate resource limits and requests
- Implement monitoring for controller loop execution times

#### kube-scheduler

The scheduler is responsible for optimal pod placement across cluster nodes.

**Scheduling Process Deep Dive:**

1. **Filtering Phase**: Eliminates unsuitable nodes based on:
    
    - Resource requirements (CPU, memory, storage)
    - Node selectors and affinity rules
    - Taints and tolerations
    - Volume constraints
    - Policy constraints
2. **Scoring Phase**: Ranks suitable nodes based on:
    
    - Resource utilization balance
    - Affinity/anti-affinity preferences
    - Image locality
    - Priority and preemption policies

**Advanced Scheduling Features:**

**priorityclasses**: Define pod importance levels

```yaml
apiVersion: scheduling.k8s.io/v1
kind: PriorityClass
metadata:
  name: high-priority
value: 1000
globalDefault: false
description: "High priority class for critical workloads"
```

**preemption**: Higher priority pods can evict lower priority ones

- Configure preemption policies to balance resource allocation
- Monitor preemption events for cluster resource pressure
- Implement pod disruption budgets to limit preemption impact

**topology-spread-constraints**: Distribute pods across zones/nodes

```yaml
topologySpreadConstraints:
- maxSkew: 1
  topologyKey: topology.kubernetes.io/zone
  whenUnsatisfiable: DoNotSchedule
  labelSelector:
    matchLabels:
      app: web-server
```

**DevOps Scheduler Management:**

- Configure scheduler profiles for different workload types
- Implement custom schedulers for specialized requirements
- Monitor scheduler performance metrics (scheduling latency, queue depths)
- Set up alerts for unschedulable pods
- Tune scheduler algorithm parameters for cluster characteristics
- Implement node scoring strategies based on cost/performance requirements

#### etcd

The distributed key-value store that persists all Kubernetes cluster state.

**etcd Cluster Architecture:**

- Deploy odd number of members (3, 5, 7) for HA
- Understand etcd raft consensus algorithm implications
- Configure proper network topology (separate etcd network recommended)
- Implement TLS encryption for etcd peer and client communication

**Data Management:**

- **Backup Strategies**: Implement automated etcd snapshots
    
    ```bash
    ETCDCTL_API=3 etcdctl snapshot save /backup/etcd-snapshot-$(date +%Y%m%d-%H%M%S).db \
      --endpoints=https://127.0.0.1:2379 \
      --cacert=/etc/kubernetes/pki/etcd/ca.crt \
      --cert=/etc/kubernetes/pki/etcd/server.crt \
      --key=/etc/kubernetes/pki/etcd/server.key
    ```
    
- **Restoration Procedures**: Practice disaster recovery scenarios
- **Compaction**: Regular database compaction to manage size
- **Defragmentation**: Periodic defragmentation for performance

**Performance Optimization:**

- Monitor etcd metrics: request latency, database size, commit duration
- Configure appropriate disk I/O settings (preferably SSD)
- Set proper etcd resource limits and requests
- Implement etcd-encryption for data at rest
- Monitor etcd cluster health and member status

**Security Configuration:**

- Enable peer-to-peer and client-to-server TLS
- Implement proper RBAC for etcd access
- Regular certificate rotation
- Network segmentation for etcd cluster

### Node Components Deep Dive

#### kubelet

The primary node agent responsible for pod lifecycle management on each node.

**Core Responsibilities:**

- **Container Runtime Interface (CRI)**: Communicates with container runtimes
    - **containerd**: Modern, lightweight container runtime
    - **dockershim**: Deprecated Docker support (removed in 1.24+)
    - **CRI-O**: OCI-compliant container runtime

**Pod Lifecycle Management:**

- Pod creation and startup sequence
- Container image pulling and caching
- Volume mounting and management
- Network namespace setup
- Health check execution (liveness, readiness, startup probes)
- Pod termination and cleanup

**Node Management:**

- **Node Conditions**: Reports node status to API server
    - Ready: Node can accept pods
    - MemoryPressure: Node memory is low
    - DiskPressure: Node disk space is low
    - PIDPressure: Node has too many processes
    - NetworkUnavailable: Node network is not configured

**Kubelet Configuration:**

```yaml
# /var/lib/kubelet/config.yaml
apiVersion: kubelet.config.k8s.io/v1beta1
kind: KubeletConfiguration
authentication:
  webhook:
    enabled: true
authorization:
  mode: Webhook
clusterDNS:
- 10.96.0.10
clusterDomain: cluster.local
resolvConf: /etc/resolv.conf
runtimeRequestTimeout: 10m
```

**Resource Management:**

- **Eviction Policies**: Handle node resource pressure
    
    ```yaml
    evictionHard:
      memory.available: "100Mi"
      nodefs.available: "10%"
      imagefs.available: "15%"
    ```
    
- **Reserved Resources**: Reserve node resources for system components
    
    ```yaml
    systemReserved:
      cpu: "100m"
      memory: "100Mi"
    kubeReserved:
      cpu: "100m"
      memory: "100Mi"
    ```
    

**DevOps Kubelet Management:**

- Monitor kubelet metrics and logs
- Configure log rotation for kubelet logs
- Implement proper certificate management and rotation
- Set up monitoring for node resource utilization
- Configure garbage collection policies for images and containers
- Implement node maintenance procedures (drain, cordon, uncordon)

#### kube-proxy

Implements Kubernetes networking services on each node.

**Proxy Modes:**

**iptables mode** (default):

- Creates iptables rules for service load balancing
- Lower overhead than userspace mode
- Limited load balancing algorithms (random selection)
- Good for most use cases with moderate service count

**IPVS mode**:

- Uses IP Virtual Server for advanced load balancing
- Supports multiple algorithms: round-robin, least connection, shortest expected delay
- Better performance with large numbers of services
- Requires IPVS kernel modules

**userspace mode** (legacy):

- kube-proxy acts as proxy between clients and services
- Higher CPU overhead due to user-kernel space transitions
- More reliable but slower performance

**Configuration:**

```yaml
apiVersion: kubeproxy.config.k8s.io/v1alpha1
kind: KubeProxyConfiguration
mode: "ipvs"
ipvs:
  scheduler: "rr"  # round-robin
  tcpTimeout: 900s
  tcpFinTimeout: 120s
  udpTimeout: 300s
```

**DevOps Proxy Management:**

- Monitor service endpoint updates and proxy rule generation
- Troubleshoot connectivity issues between services
- Optimize proxy mode based on cluster size and requirements
- Monitor proxy performance metrics
- Handle service mesh integration considerations

#### Container Runtime

The container runtime interface handles low-level container operations.

**Container Runtime Options:**

- **containerd**: CNCF-graduated, lightweight, focus on simplicity and robustness
- **CRI-O**: OCI-compliant runtime designed for Kubernetes
- **Docker Engine**: Deprecated kubelet dockershim removed in v1.24

**Runtime Configuration:**

- Configure image pulling policies and registry authentication
- Set up container log rotation and storage
- Implement security policies and constraints
- Monitor runtime performance and resource usage