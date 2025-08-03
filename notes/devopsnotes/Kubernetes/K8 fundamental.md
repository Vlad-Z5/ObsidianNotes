## Core Components & Architecture Deep Dive

### Control Plane Components

#### kube-apiserver

The API server is the central hub of all Kubernetes operations, serving REST APIs and handling all cluster communication.

**DevOps Responsibilities:**

- Configure API server flags for audit logging: `--audit-log-path`, `--audit-policy-file`
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
    ETCDCTL_API=3 etcdctl snapshot save /backup/etcd-snapshot-$(date +%Y%m%d-%H%M%S).db \  --endpoints=https://127.0.0.1:2379 \  --cacert=/etc/kubernetes/pki/etcd/ca.crt \  --cert=/etc/kubernetes/pki/etcd/server.crt \  --key=/etc/kubernetes/pki/etcd/server.key
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
    evictionHard:  memory.available: "100Mi"  nodefs.available: "10%"  imagefs.available: "15%"
    ```
    
- **Reserved Resources**: Reserve node resources for system components
    
    ```yaml
    systemReserved:  cpu: "100m"  memory: "100Mi"kubeReserved:  cpu: "100m"  memory: "100Mi"
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

**iptables mode** (default):

- Creates iptables rules for service load balancing
- Lower overhead than userspace mode
- Limited load balancing algorithms (random selection)
- Good for most use cases with moderate service count

**IPVS mode**:

- Uses IP Virtual Server for advanced load balancing
- Supports multiple algorithms: round-robin, least connection, shortest expected delay
- Better performance with large numbers of services
- Requires IPVS kernel modules

**userspace mode** (legacy):

- kube-proxy acts as proxy between clients and services
- Higher CPU overhead due to user-kernel space transitions
- More reliable but slower performance

**Configuration:**

```yaml
# kube-proxy-config.yaml
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

## Workload Resources Comprehensive Guide

### Pod Deep Dive

**Pod Lifecycle Phases:**

1. **Pending**: Pod accepted but not scheduled or containers not created
2. **Running**: Pod bound to node, all containers created, at least one running
3. **Succeeded**: All containers terminated successfully
4. **Failed**: All containers terminated, at least one failed
5. **Unknown**: Pod state cannot be determined

**Container Specifications:**

**Init Containers**: Run before app containers, must complete successfully

```yaml
spec:
  initContainers:
  - name: init-db
    image: busybox:1.35
    command: ['sh', '-c', 'until nslookup mydb; do sleep 2; done;']
  - name: init-permissions
    image: busybox:1.35
    command: ['sh', '-c', 'chmod 755 /shared-data']
    volumeMounts:
    - name: shared-storage
      mountPath: /shared-data
```

**Sidecar Containers**: Run alongside main application containers

```yaml
spec:
  containers:
  - name: web-server
    image: nginx:1.21
    ports:
    - containerPort: 80
  - name: log-collector
    image: fluentd:v1.14
    volumeMounts:
    - name: varlog
      mountPath: /var/log
```

**Probe Configurations:**

**startupProbe**: Validates container startup (especially for slow-starting applications)

```yaml
startupProbe:
  httpGet:
    path: /healthz
    port: 8080
  failureThreshold: 30
  periodSeconds: 10
  timeoutSeconds: 5
```

**livenessProbe**: Determines if container should be restarted

```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8080
    httpHeaders:
    - name: Custom-Header
      value: Awesome
  initialDelaySeconds: 15
  periodSeconds: 20
  timeoutSeconds: 5
  failureThreshold: 3
```

**readinessProbe**: Determines if container is ready to receive traffic

```yaml
readinessProbe:
  exec:
    command:
    - cat
    - /tmp/healthy
  initialDelaySeconds: 5
  periodSeconds: 5
  successThreshold: 1
  failureThreshold: 3
```

**Resource Management:**

```yaml
resources:
  requests:
    memory: "64Mi"
    cpu: "250m"
    ephemeral-storage: "1Gi"
  limits:
    memory: "128Mi"
    cpu: "500m"
    ephemeral-storage: "2Gi"
```

**Security Context:**

```yaml
securityContext:
  runAsUser: 1000
  runAsGroup: 3000
  runAsNonRoot: true
  fsGroup: 2000
  capabilities:
    add: ["NET_ADMIN", "SYS_TIME"]
    drop: ["ALL"]
  readOnlyRootFilesystem: true
  allowPrivilegeEscalation: false
```

**DevOps Pod Management:**

- Implement proper resource requests/limits for optimal scheduling
- Configure appropriate restart policies (Always, OnFailure, Never)
- Set up monitoring for pod resource utilization
- Implement proper logging and log rotation
- Configure pod disruption budgets for high availability
- Use multi-container patterns effectively (sidecar, adapter, ambassador)

### Deployment Strategies Deep Dive

**Rolling Update Strategy:**

```yaml
strategy:
  type: RollingUpdate
  rollingUpdate:
    maxUnavailable: 25%  # Can be percentage or absolute number
    maxSurge: 25%        # Additional pods during update
```

**Recreate Strategy:**

```yaml
strategy:
  type: Recreate  # All pods terminated before new ones created
```

**Advanced Deployment Patterns:**

**Blue-Green Deployment**: Maintain two identical environments

```yaml
# Blue deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app-blue
  labels:
    version: blue
spec:
  replicas: 3
  selector:
    matchLabels:
      app: myapp
      version: blue
---
# Service initially points to blue
apiVersion: v1
kind: Service
metadata:
  name: app-service
spec:
  selector:
    app: myapp
    version: blue  # Switch to green for cutover
```

**Canary Deployment with Traffic Splitting:**

```yaml
# Primary deployment (90% traffic)
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app-primary
spec:
  replicas: 9
  selector:
    matchLabels:
      app: myapp
      track: primary
---
# Canary deployment (10% traffic)  
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
---
# Service routes to both
apiVersion: v1
kind: Service
metadata:
  name: app-service
spec:
  selector:
    app: myapp  # Matches both primary and canary
```

**DevOps Deployment Best Practices:**

- Implement proper health checks before routing traffic
- Use deployment annotations for change tracking
- Configure appropriate replica counts for availability
- Implement automated rollback triggers based on metrics
- Monitor deployment progress and set timeouts
- Use labels effectively for deployment management
- Implement proper testing strategies for each deployment type

### StatefulSet Deep Dive

StatefulSets provide stable network identities and persistent storage for stateful applications.

**Key Features:**

- **Stable Network Identity**: Pods get predictable names (web-0, web-1, web-2)
- **Stable Storage**: Each pod gets persistent volume claims
- **Ordered Deployment**: Pods created sequentially (0, then 1, then 2)
- **Ordered Deletion**: Pods deleted in reverse order (2, then 1, then 0)

**StatefulSet Configuration:**

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgresql
spec:
  serviceName: postgresql-headless
  replicas: 3
  selector:
    matchLabels:
      app: postgresql
  template:
    metadata:
      labels:
        app: postgresql
    spec:
      containers:
      - name: postgresql
        image: postgres:13
        env:
        - name: POSTGRES_DB
          value: mydb
        - name: POSTGRES_USER
          value: admin
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: postgres-secret
              key: password
        volumeMounts:
        - name: postgresql-storage
          mountPath: /var/lib/postgresql/data
        ports:
        - containerPort: 5432
  volumeClaimTemplates:
  - metadata:
      name: postgresql-storage
    spec:
      accessModes: [ "ReadWriteOnce" ]
      storageClassName: fast-ssd
      resources:
        requests:
          storage: 10Gi
```

**Headless Service for StatefulSet:**

```yaml
apiVersion: v1
kind: Service
metadata:
  name: postgresql-headless
spec:
  clusterIP: None  # Headless service
  selector:
    app: postgresql
  ports:
  - port: 5432
    targetPort: 5432
```

**Scaling StatefulSets:**

- Scale up: New pods created sequentially with next ordinal
- Scale down: Highest ordinal pods terminated first
- Manual scaling: `kubectl scale statefulset postgresql --replicas=5`
- Automatic scaling: Use HPA with custom metrics

**DevOps StatefulSet Management:**

- Plan for data migration during scaling operations
- Implement proper backup strategies for persistent data
- Monitor pod startup and readiness times
- Configure appropriate resource limits for stateful workloads
- Implement proper storage class selection based on performance needs
- Plan for disaster recovery and data replication strategies

### DaemonSet Deep Dive

DaemonSets ensure pods run on all (or selected) nodes in the cluster.

**Common Use Cases:**

- **Log Collection**: Fluentd, Fluent Bit, Filebeat
- **Monitoring**: Node Exporter, Datadog agent, New Relic agent
- **Networking**: CNI agents, kube-proxy
- **Storage**: Storage daemons, CSI node drivers
- **Security**: Security scanning agents, runtime security tools

**DaemonSet Configuration:**

```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: fluentd-elasticsearch
  namespace: kube-system
spec:
  selector:
    matchLabels:
      name: fluentd-elasticsearch
  template:
    metadata:
      labels:
        name: fluentd-elasticsearch
    spec:
      tolerations:
      - key: node-role.kubernetes.io/master
        effect: NoSchedule  # Run on master nodes too
      containers:
      - name: fluentd-elasticsearch
        image: fluentd:v1.14-debian
        resources:
          limits:
            memory: 200Mi
          requests:
            cpu: 100m
            memory: 200Mi
        volumeMounts:
        - name: varlog
          mountPath: /var/log
        - name: varlibdockercontainers
          mountPath: /var/lib/docker/containers
          readOnly: true
      terminationGracePeriodSeconds: 30
      volumes:
      - name: varlog
        hostPath:
          path: /var/log
      - name: varlibdockercontainers
        hostPath:
          path: /var/lib/docker/containers
```

**Node Selection:**

```yaml
nodeSelector:
  disktype: ssd  # Only run on SSD nodes
```

**DevOps DaemonSet Management:**

- Monitor DaemonSet rollout status across all nodes
- Handle node maintenance scenarios (cordoning nodes)
- Configure appropriate resource limits to prevent node resource exhaustion
- Implement proper log rotation for DaemonSet pods
- Monitor DaemonSet pod distribution and health
- Plan for DaemonSet updates and rolling restart strategies

## Networking Comprehensive Deep Dive

### Service Types Detailed Analysis

#### ClusterIP Services

Default service type providing internal cluster communication.

**Use Cases:**

- **Internal APIs**: Backend services accessed only by other cluster components
- **Databases**: Database services accessed by application pods
- **Caching**: Redis, Memcached services for internal use
- **Message Queues**: RabbitMQ, Kafka for internal messaging

**Configuration:**

```yaml
apiVersion: v1
kind: Service
metadata:
  name: backend-service
spec:
  type: ClusterIP
  selector:
    app: backend
  ports:
  - port: 80        # Service port
    targetPort: 8080 # Pod port
    protocol: TCP
    name: http
  - port: 443
    targetPort: 8443
    protocol: TCP
    name: https
```

**Advanced ClusterIP Features:**

```yaml
spec:
  clusterIP: 10.96.240.10  # Static IP assignment
  clusterIPs:
  - 10.96.240.10  # IPv4
  - fd00::1       # IPv6 (dual-stack)
  ipFamilies:
  - IPv4
  - IPv6
  ipFamilyPolicy: PreferDualStack
```

#### NodePort Services

Exposes services on each node's IP at a static port (30000-32767 range).

**Use Cases:**

- **Development/Testing**: Direct access to services during development
- **Legacy Integration**: Systems that can't use load balancers
- **On-Premises**: Environments without cloud load balancer integration
- **Debugging**: Direct access to specific pods for troubleshooting

**Configuration:**

```yaml
apiVersion: v1
kind: Service
metadata:
  name: web-service
spec:
  type: NodePort
  selector:
    app: web
  ports:
  - port: 80
    targetPort: 8080
    nodePort: 30080  # Optional: specific port (30000-32767)
    protocol: TCP
```

**DevOps Considerations:**

- Security implications: NodePort exposes services on all nodes
- Firewall configuration required for external access
- Load balancing needs external solution (e.g., external load balancer)
- Port conflicts possible in multi-service environments

#### LoadBalancer Services

Integrates with cloud provider load balancers.

**Use Cases:**

- **Public Web Applications**: Frontend applications requiring external access
- **APIs**: REST/GraphQL APIs for external consumption
- **Mobile Backends**: Services for mobile applications
- **Third-party Integrations**: Services requiring external partner access

**AWS LoadBalancer Configuration:**

```yaml
apiVersion: v1
kind: Service
metadata:
  name: web-service
  annotations:
    service.beta.kubernetes.io/aws-load-balancer-type: "nlb"
    service.beta.kubernetes.io/aws-load-balancer-cross-zone-load-balancing-enabled: "true"
    service.beta.kubernetes.io/aws-load-balancer-backend-protocol: "tcp"
    service.beta.kubernetes.io/aws-load-balancer-ssl-cert: "arn:aws:acm:region:account:certificate/cert-id"
    service.beta.kubernetes.io/aws-load-balancer-ssl-ports: "443"
spec:
  type: LoadBalancer
  selector:
    app: web
  ports:
  - port: 80
    targetPort: 8080
    protocol: TCP
  - port: 443
    targetPort: 8080
    protocol: TCP
```

**Azure LoadBalancer Configuration:**

```yaml
metadata:
  annotations:
    service.beta.kubernetes.io/azure-load-balancer-internal: "true"
    service.beta.kubernetes.io/azure-load-balancer-internal-subnet: "apps-subnet"
    service.beta.kubernetes.io/azure-load-balancer-resource-group: "myResourceGroup"
```

**GCP LoadBalancer Configuration:**

```yaml
metadata:
  annotations:
    cloud.google.com/load-balancer-type: "Internal"
    networking.gke.io/load-balancer-type: "Internal"
```

#### ExternalName Services

Provides DNS alias for external services.

**Use Cases:**

- **Database Migration**: Gradual migration from external to internal databases
- **Service Abstraction**: Abstract external dependencies
- **Environment Consistency**: Same service names across environments
- **Legacy Integration**: Integrate external services into Kubernetes DNS

**Configuration:**

```yaml
apiVersion: v1
kind: Service
metadata:
  name: external-database
spec:
  type: ExternalName
  externalName: db.example.com
  ports:
  - port: 5432
    protocol: TCP
```

#### Headless Services

Services without cluster IP for direct pod access.

**Use Cases:**

- **StatefulSets**: Direct access to individual pods
- **Service Discovery**: Applications that need to discover all pod IPs
- **Load Balancing**: Custom load balancing algorithms
- **Peer-to-Peer Applications**: Applications requiring direct pod communication

**Configuration:**

```yaml
apiVersion: v1
kind: Service
metadata:
  name: headless-service
spec:
  clusterIP: None  # This makes it headless
  selector:
    app: stateful-app
  ports:
  - port: 80
    targetPort: 8080
```

### Ingress Deep Dive

Ingress manages external HTTP/HTTPS access with advanced routing capabilities.

**Ingress Controllers Comparison:**

#### nginx-ingress-controller

**Best For**: General-purpose HTTP/HTTPS ingress with advanced features **Features**:

- SSL/TLS termination and certificate management
- URL rewriting and redirects
- Rate limiting and authentication
- WebSocket and gRPC support
- Custom error pages and maintenance mode

**Configuration:**

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: web-ingress
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/rate-limit: "100"
    nginx.ingress.kubernetes.io/auth-basic: "Authentication Required"
    nginx.ingress.kubernetes.io/auth-basic-realm: "Protected Area"
spec:
  tls:
  - hosts:
    - api.example.com
    secretName: api-tls-secret
  rules:
  - host: api.example.com
    http:
      paths:
      - path: /v1
        pathType: Prefix
        backend:
          service:
            name: api-v1-service
            port:
              number: 80
      - path: /v2
        pathType: Prefix
        backend:
          service:
            name: api-v2-service
            port:
              number: 80
```

#### traefik-ingress-controller

**Best For**: Dynamic service discovery and automatic SSL **Features**:

- Automatic Let's Encrypt certificate generation
- Dynamic configuration updates
- Multiple protocol support (HTTP, HTTPS, TCP, UDP)
- Built-in metrics and tracing
- Advanced middleware support

**Configuration:**

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: traefik-ingress
  annotations:
    traefik.ingress.kubernetes.io/router.middlewares: "default-auth@kubernetescrd"
    traefik.ingress.kubernetes.io/router.tls.certresolver: "letsencrypt"
spec:
  tls:
  - hosts:
    - app.example.com
  rules:
  - host: app.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: app-service
            port:
              number: 80
```

#### aws-load-balancer-controller

**Best For**: AWS-native integration with ALB/NLB **Features**:

- AWS Application Load Balancer integration
- Network Load Balancer support
- AWS WAF integration
- Target group binding
- SSL certificate integration with ACM

**Configuration:**

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: aws-ingress
  annotations:
    kubernetes.io/ingress.class: alb
    alb.ingress.kubernetes.io/scheme: internet-facing
    alb.ingress.kubernetes.io/target-type: ip
    alb.ingress.kubernetes.io/certificate-arn: arn:aws:acm:region:account:certificate/cert-id
    alb.ingress.kubernetes.io/ssl-policy: ELBSecurityPolicy-TLS-1-2-2017-01
    alb.ingress.kubernetes.io/backend-protocol: HTTP
spec:
  rules:
  - host: app.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: app-service
            port:
              number: 80
```

### Network Policies Deep Dive

Network policies provide micro-segmentation and security for pod communication.

**Default Deny All Policy:**

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
  namespace: production
spec:
  podSelector: {}  # Applies to all pods in namespace
  policyTypes:
  - Ingress
  - Egress
```

**Allow from Specific Namespace:**

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-from-frontend
  namespace: backend
spec:
  podSelector:
    matchLabels:
      tier: database
  policyTypes:
  - Ingress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: frontend
    - podSelector:
        matchLabels:
          app: web-server
    ports:
    - protocol: TCP
      port: 5432
```

**Egress Policy for External Access:**

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-external-egress
spec:
  podSelector:
    matchLabels:
      app: web-app
  policyTypes:
  - Egress
  egress:
  - to: []  # Allow all egress
    ports:
    - protocol: TCP
      port: 443  # HTTPS only
    - protocol: TCP
      port: 53   # DNS
    - protocol: UDP
      port: 53   # DNS
```

### Service Mesh Deep Dive

#### Istio Service Mesh

**Components:**

- **Envoy Proxy**: Sidecar proxy for traffic management
- **Istiod**: Control plane for configuration and certificate management
- **Ingress Gateway**: Entry point for external traffic

**Traffic Management:**

```yaml
# VirtualService for traffic routing
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: reviews-route
spec:
  http:
  - match:
    - headers:
        end-user:
          exact: jason
    route:
    - destination:
        host: reviews
        subset: v2
  - route:
    - destination:
        host: reviews
        subset: v1
---
# DestinationRule for load balancing
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: reviews-destination
spec:
  host: reviews
  trafficPolicy:
    loadBalancer:
      simple: LEAST_CONN
  subsets:
  - name: v1
    labels:
      version: v1
  - name: v2
    labels:
      version: v2
```

**Security Policies:**

```yaml
# Enable mTLS
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: default
spec:
  mtls:
    mode: STRICT
---
# Authorization policy
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: frontend-ingress
spec:
  selector:
    matchLabels:
      app: frontend
  rules:
  - from:
    - source:
        principals: ["cluster.local/ns/istio-system/sa/istio-ingressgateway-service-account"]
    to:
    - operation:
        methods: ["GET", "POST"]
```

#### Linkerd Service Mesh

**Lightweight Alternative to Istio:**

- **Linkerd2-proxy**: Ultra-light Rust-based proxy
- **Controller**: Manages proxy configuration
- **Web UI**: Dashboard for observability

**Installation and Configuration:**

```bash
# Install Linkerd CLI
curl -sL https://run.linkerd.io/install | sh

# Pre-flight check
linkerd check --pre

# Install control plane
linkerd install | kubectl apply -f -

# Inject proxy into deployment
kubectl get deploy webapp -o yaml | linkerd inject - | kubectl apply -f -
```

## Storage Comprehensive Deep Dive

### Volume Types Detailed Analysis

#### Persistent Volumes (PV) and Claims (PVC)

**Static Provisioning:**

```yaml
# Persistent Volume
apiVersion: v1
kind: PersistentVolume
metadata:
  name: mysql-pv
spec:
  capacity:
    storage: 10Gi
  accessModes:
  - ReadWriteOnce
  persistentVolumeReclaimPolicy: Retain
  storageClassName: manual
  local:
    path: /mnt/disks/mysql
  nodeAffinity:
    required:
      nodeSelectorTerms:
      - matchExpressions:
        - key: kubernetes.io/hostname
          operator: In
          values:
          - worker-node-1
---
# Persistent Volume Claim
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: mysql-pvc
spec:
  accessModes:
  - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
  storageClassName: manual
```

**Dynamic Provisioning with Storage Classes:**

**AWS EBS Storage Class:**

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: fast-ebs
provisioner: ebs.csi.aws.com
parameters:
  type: gp3
  iops: "3000"
  throughput: "125"
  encrypted: "true"
  kmsKeyId: "arn:aws:kms:region:account:key/key-id"
volumeBindingMode: WaitForFirstConsumer
allowVolumeExpansion: true
reclaimPolicy: Delete
```

**Azure Disk Storage Class:**

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: managed-premium-ssd
provisioner: disk.csi.azure.com
parameters:
  storageaccounttype: Premium_LRS
  kind: managed
  cachingmode: ReadOnly
volumeBindingMode: WaitForFirstConsumer
allowVolumeExpansion: true
```

**GCP Persistent Disk Storage Class:**

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: fast-ssd
provisioner: pd.csi.storage.gke.io
parameters:
  type: pd-ssd
  zones: us-central1-a,us-central1-b
volumeBindingMode: WaitForFirstConsumer
allowVolumeExpansion: true
```

### CSI Drivers Deep Dive

#### AWS EBS CSI Driver

**Installation:**

```bash
# Add IAM policy to nodes
aws iam attach-role-policy \
  --role-name eksctl-cluster-nodegroup-NodeInstanceRole \
  --policy-arn arn:aws:iam::aws:policy/service-role/Amazon_EBS_CSI_DriverPolicy

# Deploy CSI driver
kubectl apply -k "github.com/kubernetes-sigs/aws-ebs-csi-driver/deploy/kubernetes/overlays/stable/?ref=master"
```

**Volume Snapshot Configuration:**

```yaml
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshotClass
metadata:
  name: ebs-snapshot-class
driver: ebs.csi.aws.com
deletionPolicy: Delete
---
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshot
metadata:
  name: mysql-snapshot
spec:
  volumeSnapshotClassName: ebs-snapshot-class
  source:
    persistentVolumeClaimName: mysql-pvc
```

#### Azure File CSI Driver

**Configuration for Shared Storage:**

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: azure-file
provisioner: file.csi.azure.com
parameters:
  storageAccount: mystorageaccount
  resourceGroup: myResourceGroup
  shareName: myshare
volumeBindingMode: Immediate
allowVolumeExpansion: true
mountOptions:
  - dir_mode=0755
  - file_mode=0755
  - uid=0
  - gid=0
  - mfsymlinks
  - cache=strict
```

### Volume Management Best Practices

**Volume Expansion:**

```yaml
# Enable in StorageClass  
allowVolumeExpansion: true

# Expand PVC
spec:
  resources:
    requests:
      storage: 20Gi  # Increased from 10Gi
```

**Backup Strategies:**

```yaml
# Using Velero for backup
apiVersion: velero.io/v1
kind: Backup
metadata:
  name: mysql-backup
spec:
  includedNamespaces:
  - database
  includedResources:
  - persistentvolumeclaims
  - persistentvolumes
  storageLocation: aws-s3
  ttl: 720h0m0s
```

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

## Security & Access Control Comprehensive

### RBAC Deep Dive

**Role Hierarchy and Best Practices:**

**Namespace-scoped Roles:**

```yaml
# Developer role for application namespace
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: myapp
  name: developer
rules:
- apiGroups: [""]
  resources: ["pods", "pods/log", "pods/exec"]
  verbs: ["get", "list", "create", "update", "patch", "delete"]
- apiGroups: [""]
  resources: ["services", "configmaps", "secrets"]
  verbs: ["get", "list", "create", "update", "patch", "delete"]
- apiGroups: ["apps"]
  resources: ["deployments", "replicasets"]
  verbs: ["get", "list", "create", "update", "patch", "delete"]
- apiGroups: [""]
  resources: ["persistentvolumeclaims"]
  verbs: ["get", "list"]
---
# Bind role to user
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: developer-binding
  namespace: myapp
subjects:
- kind: User
  name: john.doe@company.com
  apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: Role
  name: developer
  apiGroup: rbac.authorization.k8s.io
```

**Cluster-wide Roles:**

```yaml
# SRE cluster role
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: sre
rules:
- apiGroups: [""]
  resources: ["nodes", "nodes/metrics", "nodes/stats"]
  verbs: ["get", "list", "watch"]
- apiGroups: [""]
  resources: ["pods", "pods/log"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["apps"]
  resources: ["deployments", "daemonsets", "statefulsets"]
  verbs: ["get", "list", "watch", "update", "patch"]
- apiGroups: ["metrics.k8s.io"]
  resources: ["nodes", "pods"]
  verbs: ["get", "list"]
---
# Service account for SRE tools
apiVersion: v1
kind: ServiceAccount
metadata:
  name: sre-service-account
  namespace: monitoring
---
# Bind cluster role to service account
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: sre-binding
subjects:
- kind: ServiceAccount
  name: sre-service-account
  namespace: monitoring
roleRef:
  kind: ClusterRole
  name: sre
  apiGroup: rbac.authorization.k8s.io
```

### Pod Security Standards

**Pod Security Policy Replacement:**

```yaml
# Namespace with pod security standard
apiVersion: v1
kind: Namespace
metadata:
  name: secure-apps
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/warn: restricted
```

**Security Context Examples:**

```yaml
# Highly secure pod
apiVersion: v1
kind: Pod
metadata:
  name: secure-pod
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 10001
    runAsGroup: 10001
    fsGroup: 10001
    seccompProfile:
      type: RuntimeDefault
  containers:
  - name: app
    image: myapp:1.0
    securityContext:
      allowPrivilegeEscalation: false
      capabilities:
        drop:
        - ALL
      readOnlyRootFilesystem: true
    volumeMounts:
    - name: tmp
      mountPath: /tmp
    - name: var-run
      mountPath: /var/run
  volumes:
  - name: tmp
    emptyDir: {}
  - name: var-run
    emptyDir: {}
```

## Resource Management & Autoscaling

### Horizontal Pod Autoscaler (HPA) Deep Dive

**CPU-based Autoscaling:**

```yaml
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
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 10
        periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 0
      policies:
      - type: Percent
        value: 100
        periodSeconds: 15
      - type: Pods
        value: 4
        periodSeconds: 15
      selectPolicy: Max
```

**Custom Metrics Autoscaling:**

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: queue-processor-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: queue-processor
  minReplicas: 1
  maxReplicas: 50
  metrics:
  - type: External
    external:
      metric:
        name: queue_messages_ready
        selector:
          matchLabels:
            queue: "work-queue"
      target:
        type: AverageValue
        averageValue: "10"
```

### Vertical Pod Autoscaler (VPA)

**VPA Configuration:**

```yaml
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: web-app-vpa
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: web-app
  updatePolicy:
    updateMode: "Auto"  # Auto, Off, Initial
  resourcePolicy:
    containerPolicies:
    - containerName: web-server
      minAllowed:
        cpu: 100m
        memory: 50Mi
      maxAllowed:
        cpu: 1000m
        memory: 500Mi
      controlledResources: ["cpu", "memory"]
```

### Cluster Autoscaler

**Node Group Configuration:**

```yaml
# AWS EKS Node Group with autoscaling
apiVersion: v1
kind: ConfigMap
metadata:
  name: cluster-autoscaler-status
  namespace: kube-system
data:
  nodes.max: "100"
  nodes.min: "3"  
  scale-down-delay-after-add: "10m"
  scale-down-unneeded-time: "10m"
  skip-nodes-with-local-storage: "false"
  skip-nodes-with-system-pods: "false"
```

## Advanced Scheduling Deep Dive

### Taints and Tolerations

**Node Taints for Dedicated Workloads:**

```bash
# Taint node for GPU workloads
kubectl taint nodes gpu-node-1 nvidia.com/gpu=true:NoSchedule

# Taint node for database workloads  
kubectl taint nodes db-node-1 workload=database:NoSchedule

# Taint node for maintenance
kubectl taint nodes node-1 maintenance=true:NoExecute
```

**Pod Tolerations:**

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: gpu-pod
spec:
  tolerations:
  - key: "nvidia.com/gpu"
    operator: "Equal"
    value: "true"
    effect: "NoSchedule"
  - key: "maintenance"
    operator: "Exists"
    effect: "NoExecute"
    tolerationSeconds: 3600  # Tolerate for 1 hour
  containers:
  - name: gpu-app
    image: tensorflow/tensorflow:latest-gpu
    resources:
      limits:
        nvidia.com/gpu: 1
```

### Affinity Rules Deep Dive

**Node Affinity:**

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: database-pod
spec:
  affinity:
    nodeAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        nodeSelectorTerms:
        - matchExpressions:
          - key: disktype
            operator: In
            values:
            - ssd
          - key: node-size
            operator: In
            values:
            - large
            - xlarge
      preferredDuringSchedulingIgnoredDuringExecution:
      - weight: 100
        preference:
          matchExpressions:
          - key: zone
            operator: In
            values:
            - us-west-2a
```

**Pod Affinity and Anti-Affinity:**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-app
spec:
  replicas: 3
  template:
    spec:
      affinity:
        # Co-locate with cache pods
        podAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            podAffinityTerm:
              labelSelector:
                matchExpressions:
                - key: app
                  operator: In
                  values:
                  - cache
              topologyKey: kubernetes.io/hostname
        
        # Spread across zones for HA
        podAntiAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
          - labelSelector:
              matchExpressions:
              - key: app
                operator: In
                values:
                - web-app
            topologyKey: failure-domain.beta.kubernetes.io/zone
          
          # Prefer not to co-locate on same node
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            podAffinityTerm:
              labelSelector:
                matchExpressions:
                - key: app
                  operator: In
                  values:
                  - web-app
              topologyKey: kubernetes.io/hostname
```

## Monitoring & Observability Comprehensive

### Prometheus Stack Deep Dive

**Prometheus Configuration:**

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-config
data:
  prometheus.yml: |
    global:
      scrape_interval: 15s
      evaluation_interval: 15s
    
    rule_files:
    - "/etc/prometheus/rules/*.yml"
    
    alerting:
      alertmanagers:
      - static_configs:
        - targets:
          - alertmanager:9093
    
    scrape_configs:
    - job_name: 'kubernetes-apiserver'
      kubernetes_sd_configs:
      - role: endpoints
      scheme: https
      tls_config:
        ca_file: /var/run/secrets/kubernetes.io/serviceaccount/ca.crt
      bearer_token_file: /var/run/secrets/kubernetes.io/serviceaccount/token
      relabel_configs:
      - source_labels: [__meta_kubernetes_namespace, __meta_kubernetes_service_name, __meta_kubernetes_endpoint_port_name]
        action: keep
        regex: default;kubernetes;https
    
    - job_name: 'kubernetes-nodes'
      kubernetes_sd_configs:
      - role: node
      scheme: https
      tls_config:
        ca_file: /var/run/secrets/kubernetes.io/serviceaccount/ca.crt
      bearer_token_file: /var/run/secrets/kubernetes.io/serviceaccount/token
      relabel_configs:
      - action: labelmap
        regex: __meta_kubernetes_node_label_(.+)
      - target_label: __address__
        replacement: kubernetes.default.svc:443
      - source_labels: [__meta_kubernetes_node_name]
        regex: (.+)
        target_label: __metrics_path__
        replacement: /api/v1/nodes/${1}/proxy/metrics
    
    - job_name: 'kubernetes-pods'
      kubernetes_sd_configs:
      - role: pod
      relabel_configs:
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
        action: keep
        regex: true
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_path]
        action: replace
        target_label: __metrics_path__
        regex: (.+)
```

**AlertManager Configuration:**

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: alertmanager-config
data:
  alertmanager.yml: |
    global:
      smtp_smarthost: 'localhost:587'
      smtp_from: 'alerts@company.com'
      slack_api_url: 'https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK'
    
    route:
      group_by: ['alertname', 'cluster', 'service']
      group_wait: 10s
      group_interval: 10s
      repeat_interval: 1h
      receiver: 'default'
      routes:
      - match:
          severity: critical
        receiver: 'critical-alerts'
      - match:
          service: database
        receiver: 'database-team'
    
    receivers:
    - name: 'default'
      slack_configs:
      - channel: '#alerts'
        title: 'Alert: {{ .GroupLabels.alertname }}'
        text: '{{ range .Alerts }}{{ .Annotations.summary }}{{ end }}'
    
    - name: 'critical-alerts'
      email_configs:
      - to: 'oncall@company.com'
        subject: 'CRITICAL: {{ .GroupLabels.alertname }}'
        body: |
          {{ range .Alerts }}
          Alert: {{ .Annotations.summary }}
          Description: {{ .Annotations.description }}
          {{ end }}
      slack_configs:
      - channel: '#critical-alerts'
        title: 'CRITICAL: {{ .GroupLabels.alertname }}'
        text: '{{ range .Alerts }}{{ .Annotations.summary }}{{ end }}'
    
    - name: 'database-team'
      email_configs:
      - to: 'database-team@company.com'
        subject: 'Database Alert: {{ .GroupLabels.alertname }}'
```

**Prometheus Rules:**

```yaml
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: kubernetes-rules
spec:
  groups:
  - name: kubernetes.rules
    rules:
    - alert: KubePodCrashLooping
      expr: rate(kube_pod_container_status_restarts_total[15m]) * 60 * 15 > 0
      for: 15m
      labels:
        severity: critical
      annotations:
        summary: "Pod {{ $labels.namespace }}/{{ $labels.pod }} is crash looping"
        description: "Pod {{ $labels.namespace }}/{{ $labels.pod }} has been restarting {{ $value }} times in the last 15 minutes"
    
    - alert: KubeNodeNotReady
      expr: kube_node_status_condition{condition="Ready",status="true"} == 0
      for: 5m
      labels:
        severity: critical
      annotations:
        summary: "Node {{ $labels.node }} is not ready"
        description: "Node {{ $labels.node }} has been not ready for more than 5 minutes"
    
    - alert: KubePodNotReady
      expr: kube_pod_status_ready{condition="true"} == 0
      for: 15m
      labels:
        severity: warning
      annotations:
        summary: "Pod {{ $labels.namespace }}/{{ $labels.pod }} is not ready"
        description: "Pod {{ $labels.namespace }}/{{ $labels.pod }} has been not ready for more than 15 minutes"
    
    - alert: KubeDeploymentReplicasMismatch
      expr: kube_deployment_status_replicas_available != kube_deployment_status_replicas
      for: 5m
      labels:
        severity: warning
      annotations:
        summary: "Deployment {{ $labels.namespace }}/{{ $labels.deployment }} has mismatched replicas"
        description: "Deployment {{ $labels.namespace }}/{{ $labels.deployment }} has {{ $labels.replicas }} desired replicas but only {{ $labels.available_replicas }} are available"
```

### Logging Stack Deep Dive

**Fluentd Configuration for EFK Stack:**

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: fluentd-config
data:
  fluent.conf: |
    <source>
      @type tail
      path /var/log/containers/*.log
      pos_file /var/log/fluentd-containers.log.pos
      tag kubernetes.*
      read_from_head true
      <parse>
        @type json
        time_format %Y-%m-%dT%H:%M:%S.%NZ
      </parse>
    </source>
    
    <filter kubernetes.**>
      @type kubernetes_metadata
    </filter>
    
    # Exclude system namespace logs
    <filter kubernetes.**>
      @type grep
      <exclude>
        key $.kubernetes.namespace_name
        pattern ^(kube-system|kube-public)$
      </exclude>
    </filter>
    
    # Parse application logs
    <filter kubernetes.**>
      @type parser
      key_name log
      reserve_data true
      remove_key_name_field true
      <parse>
        @type multi_format
        <pattern>
          format json
        </pattern>
        <pattern>
          format none
        </pattern>
      </parse>
    </filter>
    
    <match kubernetes.**>
      @type elasticsearch
      host elasticsearch.logging.svc.cluster.local
      port 9200
      logstash_format true
      logstash_prefix kubernetes
      <buffer>
        @type file
        path /var/log/fluentd-buffers/kubernetes.system.buffer
        flush_mode interval
        retry_type exponential_backoff
        flush_thread_count 2
        flush_interval 5s
        retry_forever
        retry_max_interval 30
        chunk_limit_size 2M
        queue_limit_length 8
        overflow_action block
      </buffer>
    </match>
```

## Cluster Upgrade Comprehensive Guide

### Cluster Upgrade Planning

**Pre-Upgrade Checklist:**

1. **Version Compatibility**: Check Kubernetes version skew policy
2. **Backup**: Complete etcd backup and application data backup
3. **Node Capacity**: Ensure sufficient capacity for rolling updates
4. **Application Compatibility**: Test applications against new Kubernetes version
5. **Add-on Compatibility**: Verify CNI, CSI, and other add-ons compatibility
6. **Monitoring**: Ensure monitoring and alerting is functional

### kubeadm Cluster Upgrade Process

**Control Plane Upgrade:**

```bash
# 1. Upgrade kubeadm on first control plane node
apt-mark unhold kubeadm && \
apt-get update && apt-get install -y kubeadm=1.28.0-00 && \
apt-mark hold kubeadm

# 2. Verify upgrade plan
kubeadm upgrade plan

# 3. Apply upgrade
kubeadm upgrade apply v1.28.0

# 4. Drain the node
kubectl drain cp-node-1 --ignore-daemonsets

# 5. Upgrade kubelet and kubectl
apt-mark unhold kubelet kubectl && \
apt-get update && apt-get install -y kubelet=1.28.0-00 kubectl=1.28.0-00 && \
apt-mark hold kubelet kubectl

# 6. Restart kubelet
systemctl daemon-reload
systemctl restart kubelet

# 7. Uncordon the node
kubectl uncordon cp-node-1

# 8. For additional control plane nodes
kubeadm upgrade node
```

**Worker Node Upgrade:**

```bash
# 1. On control plane, drain worker node
kubectl drain worker-node-1 --ignore-daemonsets --force

# 2. On worker node, upgrade kubeadm
apt-mark unhold kubeadm && \
apt-get update && apt-get install -y kubeadm=1.28.0-00 && \
apt-mark hold kubeadm

# 3. Upgrade node configuration
kubeadm upgrade node

# 4. Upgrade kubelet and kubectl  
apt-mark unhold kubelet kubectl && \
apt-get update && apt-get install -y kubelet=1.28.0-00 kubectl=1.28.0-00 && \
apt-mark hold kubelet kubectl

# 5. Restart kubelet
systemctl daemon-reload
systemctl restart kubelet

# 6. Uncordon the node
kubectl uncordon worker-node-1
```

### Managed Kubernetes Upgrades

**EKS Cluster Upgrade:**

```bash
# 1. Upgrade control plane
aws eks update-cluster-version \
  --region us-west-2 \
  --name my-cluster \
  --kubernetes-version 1.28

# 2. Wait for upgrade completion
aws eks wait cluster-active \
  --region us-west-2 \
  --name my-cluster

# 3. Update node groups
aws eks update-nodegroup-version \
  --cluster-name my-cluster \
  --nodegroup-name workers \
  --kubernetes-version 1.28

# 4. Update add-ons
aws eks update-addon \
  --cluster-name my-cluster \
  --addon-name vpc-cni \
  --addon-version v1.13.4-eksbuild.1

aws eks update-addon \
  --cluster-name my-cluster \
  --addon-name coredns \
  --addon-version v1.10.1-eksbuild.2
```

**AKS Cluster Upgrade:**

```bash
# 1. Check available versions
az aks get-upgrades --resource-group myResourceGroup --name myAKSCluster

# 2. Upgrade control plane
az aks upgrade \
  --resource-group myResourceGroup \
  --name myAKSCluster \
  --kubernetes-version 1.28.0 \
  --control-plane-only

# 3. Upgrade node pools
az aks nodepool upgrade \
  --resource-group myResourceGroup \
  --cluster-name myAKSCluster \
  --name nodepool1 \
  --kubernetes-version 1.28.0
```

**GKE Cluster Upgrade:**

```bash
# 1. Upgrade master/control plane
gcloud container clusters upgrade my-cluster \
  --master \
  --cluster-version 1.28.0 \
  --zone us-central1-a

# 2. Upgrade node pools
gcloud container clusters upgrade my-cluster \
  --node-pool default-pool \
  --cluster-version 1.28.0 \
  --zone us-central1-a
```

### Post-Upgrade Verification

**Verification Checklist:**

```bash
# 1. Verify cluster version
kubectl version --short

# 2. Check node status
kubectl get nodes -o wide

# 3. Verify system pods
kubectl get pods -n kube-system

# 4. Check cluster components
kubectl get componentstatus

# 5. Verify workload functionality
kubectl get pods --all-namespaces
kubectl get services --all-namespaces

# 6. Run connectivity tests
kubectl run test-pod --image=busybox:1.35 --rm -it -- nslookup kubernetes.default

# 7. Verify persistent volumes
kubectl get pv,pvc --all-namespaces

# 8. Test autoscaling
kubectl get hpa --all-namespaces
```

## GitOps & CI/CD Deep Dive

### ArgoCD Comprehensive Setup

**ArgoCD Installation and Configuration:**

```yaml
# ArgoCD namespace
apiVersion: v1
kind: Namespace
metadata:
  name: argocd
---
# ArgoCD configuration
apiVersion: v1
kind: ConfigMap
metadata:
  name: argocd-cmd-params-cm
  namespace: argocd
data:
  # Enable gRPC-Web (for UI access through ingress)
  server.grpc.web: "true"
  # Disable internal TLS
  server.insecure: "true"
  # Enable local users
  server.enable.proxy.extension: "true"
---
# ArgoCD RBAC configuration
apiVersion: v1
kind: ConfigMap
metadata:
  name: argocd-rbac-cm
  namespace: argocd
data:
  policy.default: role:readonly
  policy.csv: |
    p, role:admin, applications, *, */*, allow
    p, role:admin, clusters, *, *, allow
    p, role:admin, repositories, *, *, allow
    g, argocd-admins, role:admin
    
    p, role:developer, applications, get, */*, allow
    p, role:developer, applications, sync, */*, allow
    g, developers, role:developer
---
# ArgoCD ingress
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: argocd-server-ingress
  namespace: argocd
  annotations:
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/backend-protocol: "GRPC"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  tls:
  - hosts:
    - argocd.company.com
    secretName: argocd-tls
  rules:
  - host: argocd.company.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: argocd-server
            port:
              number: 80
```

**Application of Applications Pattern:**

```yaml
# Root application
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: app-of-apps
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/company/k8s-apps
    targetRevision: HEAD
    path: apps
  destination:
    server: https://kubernetes.default.svc
    namespace: argocd
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
    - CreateNamespace=true
---
# Individual application
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: web-app
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/company/web-app-config
    targetRevision: HEAD
    path: k8s
    helm:
      values: |
        image:
          tag: v1.2.3
        replicas: 3
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "200m"
  destination:
    server: https://kubernetes.default.svc
    namespace: production
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
    - CreateNamespace=true
    retry:
      limit: 5
      backoff:
        duration: 5s
        factor: 2
        maxDuration: 3m
```

### Flux CD Deep Dive

**Flux Installation:**

```bash
# Install Flux CLI
curl -s https://fluxcd.io/install.sh | sudo bash

# Bootstrap Flux
flux bootstrap github \
  --owner=company \
  --repository=k8s-fleet \
  --branch=main \
  --path=clusters/production \
  --personal
```

**Flux Source and Kustomization:**

```yaml
# Git source
apiVersion: source.fluxcd.io/v1beta2
kind: GitRepository
metadata:
  name: web-app-source
  namespace: flux-system
spec:
  interval: 1m
  ref:
    branch: main
  url: https://github.com/company/web-app-config
---
# Kustomization
apiVersion: kustomize.fluxcd.io/v1beta2
kind: Kustomization
metadata:
  name: web-app
  namespace: flux-system
spec:
  interval: 10m
  path: "./k8s/overlays/production"
  prune: true
  sourceRef:
    kind: GitRepository
    name: web-app-source
  targetNamespace: production
  healthChecks:
  - apiVersion: apps/v1
    kind: Deployment
    name: web-app
    namespace: production
```

**Helm Controller:**

```yaml
# Helm repository
apiVersion: source.fluxcd.io/v1beta2
kind: HelmRepository
metadata:
  name: bitnami
  namespace: flux-system
spec:
  interval: 1h
  url: https://charts.bitnami.com/bitnami
---
# Helm release
apiVersion: helm.fluxcd.io/v2beta1
kind: HelmRelease
metadata:
  name: postgresql
  namespace: database
spec:
  interval: 15m
  chart:
    spec:
      chart: postgresql
      version: "12.x.x"
      sourceRef:
        kind: HelmRepository
        name: bitnami
        namespace: flux-system
  values:
    auth:
      postgresPassword: "changeme"
      database: "myapp"
    primary:
      persistence:
        enabled: true
        size: 10Gi
        storageClass: "fast-ssd"
    metrics:
      enabled: true
  install:
    remediation:
      retries: 3
  upgrade:
    remediation:
      retries: 3
```

### Tekton Pipelines Deep Dive

**Pipeline Components:**

```yaml
# Task definition
apiVersion: tekton.dev/v1beta1
kind: Task
metadata:
  name: build-push-image
spec:
  params:
  - name: image-name
    type: string
  - name: dockerfile
    type: string
    default: "Dockerfile"
  workspaces:
  - name: source
  - name: dockerconfig
    mountPath: /kaniko/.docker
  steps:
  - name: build-and-push
    image: gcr.io/kaniko-project/executor:latest
    args:
    - --dockerfile=$(params.dockerfile)
    - --destination=$(params.image-name)
    - --context=dir://$(workspaces.source.path)
    - --cache=true
---
# Pipeline definition
apiVersion: tekton.dev/v1beta1
kind: Pipeline
metadata:
  name: build-deploy-pipeline
spec:
  params:
  - name: git-url
    type: string
  - name: git-revision
    type: string
    default: main
  - name: image-name
    type: string
  - name: deployment-name
    type: string
  workspaces:
  - name: shared-data
  - name: docker-credentials
  tasks:
  - name: fetch-source
    taskRef:
      name: git-clone
    workspaces:
    - name: output
      workspace: shared-data
    params:
    - name: url
      value: $(params.git-url)
    - name: revision
      value: $(params.git-revision)
  
  - name: run-tests
    taskRef:
      name: golang-test
    runAfter: ["fetch-source"]
    workspaces:
    - name: source
      workspace: shared-data
  
  - name: build-image
    taskRef:
      name: build-push-image
    runAfter: ["run-tests"]  
    workspaces:
    - name: source
      workspace: shared-data
    - name: dockerconfig
      workspace: docker-credentials
    params:
    - name: image-name
      value: $(params.image-name)
  
  - name: deploy-app
    taskRef:
      name: kubernetes-deploy
    runAfter: ["build-image"]
    params:
    - name: deployment-name
      value: $(params.deployment-name)
    - name: image-name
      value: $(params.image-name)
---
# Pipeline Run
apiVersion: tekton.dev/v1beta1
kind: PipelineRun
metadata:
  name: build-deploy-run
spec:
  pipelineRef:
    name: build-deploy-pipeline
  params:
  - name: git-url
    value: https://github.com/company/web-app
  - name: git-revision
    value: main
  - name: image-name
    value: registry.company.com/web-app:latest
  - name: deployment-name
    value: web-app
  workspaces:
  - name: shared-data
    volumeClaimTemplate:
      spec:
        accessModes:
        - ReadWriteOnce
        resources:
          requests:
            storage: 1Gi
  - name: docker-credentials
    secret:
      secretName: docker-credentials
```

## Operators & Custom Resources Deep Dive

### Custom Resource Definitions (CRDs)

**Database Operator CRD:**

```yaml
apiVersion: apiextensions.k8s.io/v1
kind: CustomResourceDefinition
metadata:
  name: databases.db.company.com
spec:
  group: db.company.com
  versions:
  - name: v1
    served: true
    storage: true
    schema:
      openAPIV3Schema:
        type: object
        properties:
          spec:
            type: object
            properties:
              engine:
                type: string
                enum: ["mysql", "postgresql", "mongodb"]
              version:
                type: string
              storage:
                type: object
                properties:
                  size:
                    type: string
                  storageClass:
                    type: string
              backup:
                type: object
                properties:
                  enabled:
                    type: boolean
                  schedule:
                    type: string
                  retention:
                    type: string
              monitoring:
                type: object
                properties:
                  enabled:
                    type: boolean
                  exporterImage:
                    type: string
            required:
            - engine
            - version
            - storage
          status:
            type: object
            properties:
              phase:
                type: string
                enum: ["Pending", "Running", "Failed"]
              conditions:
                type: array
                items:
                  type: object
                  properties:
                    type:
                      type: string
                    status:
                      type: string
                    reason:
                      type: string
                    message:
                      type: string
  scope: Namespaced
  names:
    plural: databases
    singular: database
    kind: Database
    shortNames:
    - db
```

**Custom Resource Instance:**

```yaml
apiVersion: db.company.com/v1
kind: Database
metadata:
  name: user-database
  namespace: production
spec:
  engine: postgresql
  version: "13.7"
  storage:
    size: 100Gi
    storageClass: fast-ssd
  backup:
    enabled: true
    schedule: "0 2 * * *"  # Daily at 2 AM
    retention: "30d"
  monitoring:
    enabled: true
    exporterImage: postgres-exporter:v0.10.1
```

### Operator Development

**Controller Implementation (Go):**

```go
// Database controller structure
type DatabaseReconciler struct {
    client.Client
    Scheme *runtime.Scheme
    Log    logr.Logger
}

// Reconcile implements the reconciliation logic
func (r *DatabaseReconciler) Reconcile(ctx context.Context, req ctrl.Request) (ctrl.Result, error) {
    log := r.Log.WithValues("database", req.NamespacedName)
    
    // Fetch the Database instance
    var database dbv1.Database
    if err := r.Get(ctx, req.NamespacedName, &database); err != nil {
        if errors.IsNotFound(err) {
            return ctrl.Result{}, nil
        }
        return ctrl.Result{}, err
    }
    
    // Reconcile StatefulSet
    if err := r.reconcileStatefulSet(ctx, &database); err != nil {
        return ctrl.Result{}, err
    }
    
    // Reconcile Service
    if err := r.reconcileService(ctx, &database); err != nil {
        return ctrl.Result{}, err
    }
    
    // Reconcile PVC
    if err := r.reconcilePVC(ctx, &database); err != nil {
        return ctrl.Result{}, err
    }
    
    // Update status
    if err := r.updateStatus(ctx, &database); err != nil {
        return ctrl.Result{}, err
    }
    
    return ctrl.Result{RequeueAfter: time.Minute * 5}, nil
}

// Setup with manager
func (r *DatabaseReconciler) SetupWithManager(mgr ctrl.Manager) error {
    return ctrl.NewControllerManagedBy(mgr).
        For(&dbv1.Database{}).
        Owns(&appsv1.StatefulSet{}).
        Owns(&corev1.Service{}).
        Owns(&corev1.PersistentVolumeClaim{}).
        Complete(r)
}
```

### Popular Operators

**Prometheus Operator:**

```yaml
# ServiceMonitor for custom application
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: web-app-metrics
  labels:
    app: web-app
spec:
  selector:
    matchLabels:
      app: web-app
  endpoints:
  - port: metrics
    path: /metrics
    interval: 30s
---
# PrometheusRule for custom alerts
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: web-app-rules
spec:
  groups:
  - name: web-app.rules
    rules:
    - alert: WebAppHighResponseTime
      expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 0.5
      for: 10m
      labels:
        severity: warning
      annotations:
        summary: "Web app high response time"
        description: "95th percentile response time is {{ $value }}s"
```

**Cert-Manager:**

```yaml
# ClusterIssuer for Let's Encrypt
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: admin@company.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
    - dns01:
        route53:
          region: us-west-2
          accessKeyID: AKIAIOSFODNN7EXAMPLE
          secretAccessKeySecretRef:
            name: route53-credentials
            key: secret-access-key
---
# Certificate resource
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: web-app-tls
  namespace: production
spec:
  secretName: web-app-tls-secret
  issuerRef:
    name: letsencrypt-prod
    kind: ClusterIssuer
  dnsNames:
  - app.company.com
  - api.company.com
```

## Cloud Provider Integrations Deep Dive

### AWS EKS Deep Dive

**EKS Cluster Configuration:**

```yaml
# eksctl cluster config
apiVersion: eksctl.io/v1alpha5
kind: ClusterConfig

metadata:
  name: production-cluster
  region: us-west-2
  version: "1.28"

vpc:
  cidr: 10.0.0.0/16
  clusterEndpoints:
    privateAccess: true
    publicAccess: true
    publicAccessCIDRs: ["203.0.113.0/24"]

iam:
  withOIDC: true
  serviceAccounts:
  - metadata:
      name: aws-load-balancer-controller
      namespace: kube-system
    wellKnownPolicies:
      awsLoadBalancerController: true
  - metadata:
      name: cluster-autoscaler
      namespace: kube-system
    wellKnownPolicies:
      autoScaler: true
  - metadata:
      name: external-dns
      namespace: kube-system
    wellKnownPolicies:
      externalDNS: true

managedNodeGroups:
- name: general-purpose
  instanceType: m5.large
  minSize: 2
  maxSize: 10
  desiredCapacity: 3
  volumeSize: 50
  volumeType: gp3
  amiFamily: AmazonLinux2
  iam:
    attachPolicyARNs:
    - arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy
    - arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy
    - arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly
    - arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore
  tags:
    Environment: production
    Team: platform
  labels:
    role: general
  taints:
  - key: node.kubernetes.io/instance-type
    value: m5.large
    effect: NoSchedule

- name: compute-optimized
  instanceType: c5.xlarge
  minSize: 0
  maxSize: 20
  desiredCapacity: 0
  volumeSize: 100
  amiFamily: AmazonLinux2
  labels:
    role: compute
    workload: cpu-intensive
  taints:
  - key: workload
    value: cpu-intensive
    effect: NoSchedule

addons:
- name: vpc-cni
  version: latest
- name: coredns  
  version: latest
- name: kube-proxy
  version: latest
- name: aws-ebs-csi-driver
  version: latest

cloudWatch:
  clusterLogging:
    enableTypes: ["*"]
    logRetentionInDays: 30
```

**AWS Load Balancer Controller:**

```yaml
# Service account with IRSA
apiVersion: v1
kind: ServiceAccount
metadata:
  name: aws-load-balancer-controller
  namespace: kube-system
  annotations:
    eks.amazonaws.com/role-arn: arn:aws:iam::ACCOUNT-ID:role/AmazonEKSLoadBalancerControllerRole
---
# Deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: aws-load-balancer-controller
  namespace: kube-system
spec:
  replicas: 2
  selector:
    matchLabels:
      app.kubernetes.io/name: aws-load-balancer-controller
  template:
    metadata:
      labels:
        app.kubernetes.io/name: aws-load-balancer-controller
    spec:
      serviceAccountName: aws-load-balancer-controller  
      containers:
      - name: controller
        image: amazon/aws-load-balancer-controller:v2.6.0
        args:
        - --cluster-name=production-cluster
        - --ingress-class=alb
        - --aws-vpc-id=vpc-12345678
        - --aws-region=us-west-2
        env:
        - name: AWS_DEFAULT_REGION
          value: us-west-2
        resources:
          requests:
            cpu: 100m
            memory: 200Mi
          limits:
            cpu: 200m
            memory: 500Mi
```

**EKS Fargate Profile:**

```yaml
# Fargate profile for serverless pods
apiVersion: eksctl.io/v1alpha5
kind: ClusterConfig

metadata:
  name: production-cluster
  region: us-west-2

fargateProfiles:
- name: serverless-workloads
  selectors:
  - namespace: serverless
    labels:
      compute: fargate
  - namespace: batch-jobs
  subnets:
  - subnet-12345678
  - subnet-87654321
  tags:
    Environment: production
    Compute: fargate
```

### Azure AKS Deep Dive

**AKS Cluster with Advanced Features:**

```bash
# Create resource group
az group create --name myResourceGroup --location eastus

# Create AKS cluster with advanced networking
az aks create \
  --resource-group myResourceGroup \
  --name myAKSCluster \
  --node-count 3 \
  --node-vm-size Standard_D4s_v3 \
  --network-plugin azure \
  --network-policy calico \
  --service-cidr 10.0.0.0/16 \
  --dns-service-ip 10.0.0.10 \
  --docker-bridge-address 172.17.0.1/16 \
  --vnet-subnet-id /subscriptions/SUBSCRIPTION-ID/resourceGroups/myResourceGroup/providers/Microsoft.Network/virtualNetworks/myVnet/subnets/mySubnet \
  --enable-managed-identity \
  --enable-addons monitoring,azure-policy,azure-keyvault-secrets-provider \
  --enable-cluster-autoscaler \
  --min-count 1 \
  --max-count 10 \
  --enable-pod-identity \
  --kubernetes-version 1.28.0
```

**Azure Key Vault Integration:**

```yaml
# SecretProviderClass for Key Vault
apiVersion: secrets-store.csi.x-k8s.io/v1
kind: SecretProviderClass
metadata:
  name: azure-keyvault-secrets
spec:
  provider: azure
  parameters:
    usePodIdentity: "false"
    useVMManagedIdentity: "true"
    userAssignedIdentityID: "CLIENT-ID"
    keyvaultName: "myKeyVault"
    objects: |
      array:
        - |
          objectName: database-password
          objectType: secret
          objectVersion: ""
        - |
          objectName: api-key
          objectType: secret
          objectVersion: ""
    tenantId: "TENANT-ID"
  secretObjects:
  - secretName: app-secrets
    type: Opaque
    data:
    - objectName: database-password
      key: db-password
    - objectName: api-key
      key: api-key
---
# Pod using secrets from Key Vault
apiVersion: v1
kind: Pod
metadata:
  name: web-app
spec:
  containers:
  - name: app
    image: myapp:latest
    env:
    - name: DB_PASSWORD
      valueFrom:
        secretKeyRef:
          name: app-secrets
          key: db-password
    volumeMounts:
    - name: secrets-store
      mountPath: /mnt/secrets-store
      readOnly: true
  volumes:
  - name: secrets-store
    csi:
      driver: secrets-store.csi.k8s.io
      readOnly: true
      volumeAttributes:
        secretProviderClass: azure-keyvault-secrets
```

### Google GKE Deep Dive

**GKE Autopilot vs Standard:**

**Autopilot Cluster:**

```bash
# Create Autopilot cluster (serverless nodes)
gcloud container clusters create-auto my-autopilot-cluster \
  --region=us-central1 \
  --release-channel=regular \
  --network=my-vpc \
  --subnetwork=my-subnet \
  --cluster-secondary-range-name=pods \
  --services-secondary-range-name=services \
  --enable-ip-alias \
  --enable-private-nodes \
  --master-ipv4-cidr-block=172.16.0.0/28
```

**Standard Cluster with Advanced Features:**

```bash
# Create standard cluster
gcloud container clusters create my-standard-cluster \
  --zone=us-central1-a \
  --machine-type=e2-standard-4 \
  --num-nodes=3 \
  --enable-autoscaling \
  --min-nodes=1 \
  --max-nodes=10 \
  --enable-autorepair \
  --enable-autoupgrade \
  --network=my-vpc \
  --subnetwork=my-subnet \
  --enable-ip-alias \
  --cluster-secondary-range-name=pods \
  --services-secondary-range-name=services \
  --enable-private-nodes \
  --master-ipv4-cidr-block=172.16.0.0/28 \
  --enable-network-policy \
  --enable-pod-security-policy \
  --enable-binary-authorization \
  --workload-pool=PROJECT-ID.svc.id.goog
```

**Workload Identity Configuration:**

```bash
# Enable Workload Identity
gcloud container clusters update my-cluster \
  --workload-pool=PROJECT-ID.svc.id.goog

# Create Google Service Account
gcloud iam service-accounts create gsa-name

# Create Kubernetes Service Account
kubectl create serviceaccount ksa-name

# Bind accounts
gcloud iam service-accounts add-iam-policy-binding \
  --role roles/iam.workloadIdentityUser \
  --member "serviceAccount:PROJECT-ID.svc.id.goog[NAMESPACE/ksa-name]" \
  gsa-name@PROJECT-ID.iam.gserviceaccount.com

# Annotate Kubernetes Service Account
kubectl annotate serviceaccount ksa-name \
  iam.gke.io/gcp-service-account=gsa-name@PROJECT-ID.iam.gserviceaccount.com
```

## Troubleshooting & Debugging Deep Dive

### Common Issues and Solutions

#### Pod Scheduling Issues

**Pending Pods Troubleshooting:**

```bash
# Check pod events
kubectl describe pod pending-pod

# Common reasons and solutions:
# 1. Insufficient resources
kubectl top nodes
kubectl describe nodes

# 2. Node selector not matching
kubectl get nodes --show-labels
kubectl get pod pending-pod -o yaml | grep nodeSelector

# 3. Taints and tolerations
kubectl get nodes -o json | jq '.items[] | {name:.metadata.name, taints:.spec.taints}'

# 4. Pod affinity/anti-affinity conflicts  
kubectl get pods -o wide --all-namespaces
```

**Resource Debugging:**

```bash
# Check resource quotas
kubectl describe resourcequota -n namespace

# Check limit ranges
kubectl describe limitrange -n namespace

# Check PVC binding issues
kubectl get events --field-selector involvedObject.kind=PersistentVolumeClaim
```

#### Networking Issues

**Service Discovery Problems:**

```bash
# Test DNS resolution
kubectl run test-pod --image=busybox:1.35 --rm -it -- nslookup kubernetes.default
kubectl run test-pod --image=busybox:1.35 --rm -it -- nslookup my-service.my-namespace

# Check CoreDNS logs
kubectl logs -n kube-system -l k8s-app=kube-dns

# Verify service endpoints
kubectl get endpoints my-service

# Test connectivity between pods
kubectl exec -it pod1 -- nc -zv service-name 80
```

**Network Policy Debugging:**

```bash
# Check if network policies are blocking traffic
kubectl get networkpolicies --all-namespaces

# Test connectivity
kubectl run test-client --image=busybox:1.35 --rm -it -- wget -qO- http://service-name

# Check CNI logs
kubectl logs -n kube-system -l k8s-app=calico-node
```

#### Storage Issues

**PVC Binding Problems:**

```bash
# Check PVC status
kubectl get pvc

# Check available PVs
kubectl get pv

# Check storage class
kubectl get storageclass

# Check CSI driver logs
kubectl logs -n kube-system -l app=ebs-csi-controller
```

### Performance Monitoring

**Resource Utilization:**

```bash
# Node resource usage
kubectl top nodes

# Pod resource usage
kubectl top pods --all-namespaces

# Container resource usage
kubectl top pods --containers

# Historical resource usage (if metrics-server available)
kubectl get --raw "/apis/metrics.k8s.io/v1beta1/nodes" | jq
```

**Application Performance:**

```yaml
# Resource monitoring sidecar
apiVersion: v1
kind: Pod
metadata:
  name: app-with-monitoring
spec:
  containers:
  - name: main-app
    image: myapp:latest
    resources:
      requests:
        memory: "128Mi"
        cpu: "100m"
      limits:
        memory: "256Mi"
        cpu: "200m"
  - name: metrics-exporter
    image: prom/node-exporter:latest
    ports:
    - containerPort: 9100
      name: metrics
```

## Best Practices Summary

### Production Readiness Checklist

**Security:**

- [ ] Enable RBAC with least privilege principle
- [ ] Implement Pod Security Standards
- [ ] Use network policies for micro-segmentation
- [ ] Enable audit logging
- [ ] Regular security scanning of images
- [ ] Secrets encryption at rest
- [ ] Regular certificate rotation
- [ ] Implement admission controllers for policy enforcement

**High Availability:**

- [ ] Multi-zone control plane deployment
- [ ] Multi-zone worker node distribution
- [ ] Pod disruption budgets for critical applications
- [ ] Anti-affinity rules for application pods
- [ ] Load balancer health checks configured
- [ ] Database clustering and replication
- [ ] Cross-region backup strategies

**Monitoring & Observability:**

- [ ] Comprehensive metrics collection (Prometheus)
- [ ] Centralized logging (EFK/ELK stack)
- [ ] Distributed tracing (Jaeger/Zipkin)
- [ ] Alerting rules for critical components
- [ ] SLA/SLO monitoring and dashboards
- [ ] Capacity planning metrics
- [ ] Application performance monitoring

**Resource Management:**

- [ ] Resource requests and limits defined for all pods
- [ ] Horizontal Pod Autoscaler configured
- [ ] Vertical Pod Autoscaler for right-sizing
- [ ] Cluster autoscaler for node scaling
- [ ] Resource quotas per namespace
- [ ] Limit ranges configured
- [ ] Quality of Service classes properly assigned

**Backup & Disaster Recovery:**

- [ ] Automated etcd backups
- [ ] Persistent volume snapshots
- [ ] Application data backup strategies
- [ ] Cross-region replication for critical data
- [ ] Disaster recovery runbooks
- [ ] Regular disaster recovery testing
- [ ] RTO/RPO targets defined and tested

**Development Workflow:**

- [ ] GitOps deployment pipeline
- [ ] Automated testing in CI/CD
- [ ] Container image scanning
- [ ] Deployment strategies (blue-green, canary)
- [ ] Feature flags for controlled rollouts
- [ ] Environment parity (dev/staging/prod)
- [ ] Infrastructure as Code (Terraform/Pulumi)

### DevOps Operational Procedures

#### Daily Operations

**Morning Cluster Health Check:**

```bash
#!/bin/bash
# Daily cluster health script

echo "=== Kubernetes Cluster Health Check ==="
echo "Date: $(date)"
echo

# Check cluster info
echo "Cluster Info:"
kubectl cluster-info

# Check node status
echo -e "\nNode Status:"
kubectl get nodes -o wide

# Check system pods
echo -e "\nSystem Pods Status:"
kubectl get pods -n kube-system

# Check failed pods across all namespaces
echo -e "\nFailed Pods:"
kubectl get pods --all-namespaces --field-selector=status.phase=Failed

# Check pending pods
echo -e "\nPending Pods:"
kubectl get pods --all-namespaces --field-selector=status.phase=Pending

# Check persistent volume claims
echo -e "\nPVC Status:"
kubectl get pvc --all-namespaces

# Check ingress status
echo -e "\nIngress Status:"
kubectl get ingress --all-namespaces

# Resource utilization
echo -e "\nResource Utilization:"
kubectl top nodes
kubectl top pods --all-namespaces --sort-by=cpu | head -10

# Check recent events
echo -e "\nRecent Events:"
kubectl get events --sort-by=.metadata.creationTimestamp --all-namespaces | tail -20
```

**Application Deployment Checklist:**

```yaml
# Pre-deployment validation
apiVersion: v1
kind: ConfigMap
metadata:
  name: deployment-checklist
data:
  checklist.md: |
    # Pre-Deployment Checklist
    
    ## Code Quality
    - [ ] Unit tests passing (>80% coverage)
    - [ ] Integration tests passing
    - [ ] Security scan passed
    - [ ] Code review completed
    - [ ] Documentation updated
    
    ## Container Image
    - [ ] Image vulnerability scan passed
    - [ ] Image size optimized (<500MB for web apps)
    - [ ] Non-root user configured
    - [ ] Health check endpoints implemented
    - [ ] Image tagged with semantic version
    
    ## Kubernetes Manifests
    - [ ] Resource requests/limits defined
    - [ ] Liveness/readiness probes configured
    - [ ] Security context specified
    - [ ] Labels and annotations properly set
    - [ ] ConfigMaps/Secrets externalized
    - [ ] Network policies defined (if applicable)
    
    ## Monitoring
    - [ ] Metrics endpoints exposed
    - [ ] Logging configured
    - [ ] Alerting rules defined
    - [ ] Dashboard created/updated
    - [ ] SLI/SLO defined
    
    ## Testing
    - [ ] Staging environment tested
    - [ ] Load testing completed
    - [ ] Failover testing done
    - [ ] Rollback plan verified
    
    ## Post-Deployment
    - [ ] Health checks passing
    - [ ] Metrics being collected
    - [ ] Logs flowing correctly
    - [ ] Performance within SLA
    - [ ] Alerts configured and firing correctly
```

#### Weekly Maintenance

**Cluster Maintenance Script:**

```bash
#!/bin/bash
# Weekly cluster maintenance

echo "=== Weekly Cluster Maintenance ==="

# Update cluster components
echo "Checking for available updates..."
kubectl version --short

# Check certificate expiration
echo -e "\nChecking certificate expiration:"
for cert in /etc/kubernetes/pki/*.crt; do
    echo "Certificate: $cert"
    openssl x509 -in "$cert" -noout -enddate
done

# Clean up completed jobs
echo -e "\nCleaning up completed jobs:"
kubectl delete jobs --all-namespaces --field-selector=status.successful=1

# Clean up evicted pods
echo -e "\nCleaning up evicted pods:"
kubectl get pods --all-namespaces --field-selector=status.phase=Failed -o json | \
  jq -r '.items[] | select(.status.reason == "Evicted") | "\(.metadata.namespace) \(.metadata.name)"' | \
  while read namespace pod; do
    kubectl delete pod "$pod" -n "$namespace"
  done

# Check for unused PVs
echo -e "\nChecking for unused persistent volumes:"
kubectl get pv -o json | \
  jq -r '.items[] | select(.status.phase == "Available") | .metadata.name'

# Restart system pods if needed
echo -e "\nRestarting system pods (if needed):"
kubectl rollout restart daemonset/kube-proxy -n kube-system
kubectl rollout restart deployment/coredns -n kube-system

# Generate cluster report
echo -e "\nGenerating cluster report..."
kubectl cluster-info dump > cluster-report-$(date +%Y%m%d).txt
```

#### Monthly Operations

**Capacity Planning Analysis:**

```bash
#!/bin/bash
# Monthly capacity planning script

echo "=== Monthly Capacity Planning Report ==="

# Historical resource usage
echo "Resource Usage Trends (last 30 days):"
# This would typically query Prometheus for historical data
# prometheus-query --query='node_memory_MemAvailable_bytes' --range=30d

# Growth projections
echo -e "\nGrowth Analysis:"
echo "Namespace resource consumption:"
kubectl get resourcequota --all-namespaces -o json | \
  jq -r '.items[] | "\(.metadata.namespace): CPU=\(.status.used.cpu // "0"), Memory=\(.status.used.memory // "0")"'

# Node capacity analysis
echo -e "\nNode Capacity Analysis:"
kubectl describe nodes | grep -A 5 "Allocated resources"

# Storage usage trends
echo -e "\nStorage Usage:"
kubectl get pvc --all-namespaces -o json | \
  jq -r '.items[] | "\(.metadata.namespace)/\(.metadata.name): \(.spec.resources.requests.storage)"'

# Recommendation engine
echo -e "\nRecommendations:"
echo "1. Node scaling recommendations based on usage patterns"
echo "2. Storage expansion needs"
echo "3. Application right-sizing opportunities"
echo "4. Cost optimization suggestions"
```

### Advanced Troubleshooting Scenarios

#### Memory Pressure and OOMKilled Containers

**Diagnosis Steps:**

```bash
# Check for OOMKilled containers
kubectl get pods --all-namespaces -o json | \
  jq -r '.items[] | select(.status.containerStatuses[]?.lastState.terminated.reason == "OOMKilled") | "\(.metadata.namespace)/\(.metadata.name)"'

# Analyze memory usage patterns
kubectl top pods --all-namespaces --sort-by=memory

# Check node memory pressure
kubectl describe nodes | grep -A 10 "Conditions"

# Examine container memory limits
kubectl get pods -o json | \
  jq -r '.items[] | "\(.metadata.name): \(.spec.containers[].resources.limits.memory // "unlimited")"'
```

**Resolution Strategies:**

1. **Increase Memory Limits**: Adjust container memory limits based on actual usage
2. **Optimize Application**: Profile application memory usage and optimize
3. **Implement Memory Requests**: Set appropriate memory requests for better scheduling
4. **Add Nodes**: Scale cluster if overall memory pressure is high

#### Network Connectivity Issues

**Service Mesh Debugging:**

```bash
# Istio service mesh debugging
kubectl get pods -n istio-system

# Check sidecar injection
kubectl get pods -o json | jq -r '.items[] | select(.spec.containers | length > 1) | .metadata.name'

# Analyze traffic policies
kubectl get virtualservices --all-namespaces
kubectl get destinationrules --all-namespaces

# Check envoy proxy configuration
kubectl exec -it pod-name -c istio-proxy -- curl localhost:15000/config_dump
```

#### Storage Performance Issues

**CSI Driver Troubleshooting:**

```bash
# Check CSI driver logs
kubectl logs -n kube-system -l app=ebs-csi-controller

# Verify storage class configuration
kubectl describe storageclass

# Check volume attachment issues
kubectl get volumeattachments

# Monitor I/O performance
kubectl exec -it pod-name -- iostat -x 1
```

### Security Hardening Deep Dive

#### Runtime Security with Falco

**Falco Configuration:**

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: falco-config
  namespace: falco
data:
  falco.yaml: |
    rules_file:
    - /etc/falco/falco_rules.yaml
    - /etc/falco/falco_rules.local.yaml
    - /etc/falco/k8s_audit_rules.yaml
    
    time_format_iso_8601: true
    json_output: true
    json_include_output_property: true
    
    log_stderr: true
    log_syslog: true
    log_level: info
    
    outputs:
      rate: 1
      max_burst: 1000
    
    syscall_event_drops:
      threshold: 0.1
      actions:
      - log
      - alert
    
    output_timeout: 2000
    
    grpc:
      enabled: true
      bind_address: "0.0.0.0:5060"
      threadiness: 0
    
    grpc_output:
      enabled: false
  
  custom_rules.yaml: |
    # Custom security rules
    - rule: Detect crypto mining
      desc: Detect cryptocurrency mining activities
      condition: >
        spawned_process and
        (proc.name in (xmrig, cpuminer, ccminer) or
         proc.cmdline contains "stratum+tcp" or
         proc.cmdline contains "pool.minergate.com")
      output: >
        Crypto mining activity detected (user=%user.name command=%proc.cmdline 
        container=%container.name image=%container.image.repository)
      priority: CRITICAL
    
    - rule: Detect suspicious network connections
      desc: Detect connections to suspicious domains
      condition: >
        (inbound_outbound) and
        (fd.name contains ".onion" or
         fd.name contains "torproject.org" or
         fd.name contains "suspicious-domain.com")
      output: >
        Suspicious network connection (user=%user.name connection=%fd.name 
        container=%container.name image=%container.image.repository)
      priority: WARNING
```

#### OPA Gatekeeper Policies

**Resource Quota Enforcement:**

```yaml
apiVersion: templates.gatekeeper.sh/v1beta1
kind: ConstraintTemplate
metadata:
  name: k8srequiredresources
spec:
  crd:
    spec:
      names:
        kind: K8sRequiredResources
      validation:
        properties:
          exemptNamespaces:
            type: array
            items:
              type: string
  targets:
    - target: admission.k8s.gatekeeper.sh
      rego: |
        package k8srequiredresources
        
        violation[{"msg": msg}] {
          container := input.review.object.spec.containers[_]
          not container.resources.requests.memory
          msg := sprintf("Container %v is missing memory request", [container.name])
        }
        
        violation[{"msg": msg}] {
          container := input.review.object.spec.containers[_]
          not container.resources.requests.cpu
          msg := sprintf("Container %v is missing CPU request", [container.name])
        }
        
        violation[{"msg": msg}] {
          container := input.review.object.spec.containers[_]
          not container.resources.limits.memory
          msg := sprintf("Container %v is missing memory limit", [container.name])
        }
---
apiVersion: constraints.gatekeeper.sh/v1beta1
kind: K8sRequiredResources
metadata:
  name: must-have-resources
spec:
  match:
    kinds:
      - apiGroups: [""]
        kinds: ["Pod"]
    excludedNamespaces: ["kube-system", "gatekeeper-system"]
  parameters:
    exemptNamespaces: ["monitoring", "logging"]
```

### Cost Optimization Strategies

#### Resource Right-sizing

**Automated Right-sizing Recommendations:**

```bash
#!/bin/bash
# Resource optimization script

echo "=== Resource Optimization Analysis ==="

# Find over-provisioned pods
kubectl get pods --all-namespaces -o json | \
  jq -r '.items[] | 
    select(.spec.containers[].resources.requests.cpu and .spec.containers[].resources.requests.memory) |
    {
      namespace: .metadata.namespace,
      name: .metadata.name,
      cpu_request: .spec.containers[].resources.requests.cpu,
      memory_request: .spec.containers[].resources.requests.memory,
      cpu_limit: .spec.containers[].resources.limits.cpu,
      memory_limit: .spec.containers[].resources.limits.memory
    }'

# Calculate waste percentage
echo -e "\nResource Utilization vs Requests:"
# This would integrate with metrics server for actual usage data
```

#### Spot Instance Integration

**AWS Spot Instance Configuration:**

```yaml
# Spot instance node group
apiVersion: eksctl.io/v1alpha5
kind: ClusterConfig

metadata:
  name: cost-optimized-cluster
  region: us-west-2

managedNodeGroups:
- name: spot-workers
  instanceTypes: 
  - m5.large
  - m5.xlarge
  - m4.large
  - m4.xlarge
  spot: true
  minSize: 2
  maxSize: 20
  desiredCapacity: 5
  volumeSize: 50
  labels:
    lifecycle: spot
    cost-optimization: enabled
  taints:
  - key: spot-instance
    value: "true"
    effect: NoSchedule
  tags:
    NodeType: spot
    CostOptimization: enabled
```

**Spot Instance Tolerations:**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: batch-processor
spec:
  replicas: 10
  template:
    spec:
      tolerations:
      - key: spot-instance
        operator: Equal
        value: "true"
        effect: NoSchedule
      - key: node.kubernetes.io/not-ready
        operator: Exists
        effect: NoExecute
        tolerationSeconds: 300
      - key: node.kubernetes.io/unreachable
        operator: Exists
        effect: NoExecute
        tolerationSeconds: 300
      nodeSelector:
        lifecycle: spot
      containers:
      - name: processor
        image: batch-processor:latest
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
```

### Disaster Recovery Procedures

#### Multi-Region Setup

**Cross-Region Replication Strategy:**

```yaml
# Primary region cluster (us-west-2)
apiVersion: v1
kind: ConfigMap
metadata:
  name: disaster-recovery-config
  namespace: kube-system
data:
  primary-region: us-west-2
  backup-regions: us-east-1,eu-west-1
  rto-target: "15min"
  rpo-target: "5min"
  
  backup-schedule: |
    # etcd backup: every 4 hours
    0 */4 * * * /usr/local/bin/etcd-backup.sh
    
    # Application data backup: every hour
    0 * * * * /usr/local/bin/app-backup.sh
    
    # Configuration backup: daily
    0 2 * * * /usr/local/bin/config-backup.sh
```

**Velero Backup Configuration:**

```yaml
# Backup schedule for critical applications
apiVersion: velero.io/v1
kind: Schedule
metadata:
  name: daily-backup
  namespace: velero
spec:
  schedule: "0 2 * * *"  # Daily at 2 AM
  template:
    includedNamespaces:
    - production
    - staging
    - monitoring
    includedResources:
    - persistentvolumeclaims
    - persistentvolumes
    - secrets
    - configmaps
    excludedResources:
    - events
    - events.events.k8s.io
    storageLocation: aws-s3
    volumeSnapshotLocations:
    - aws-ebs
    ttl: 720h0m0s  # 30 days retention
    hooks:
      resources:
      - name: database-backup-hook
        includedNamespaces:
        - production
        includedResources:
        - pods
        labelSelector:
          matchLabels:
            app: database
        pre:
        - exec:
            command:
            - /bin/bash
            - -c
            - "pg_dump mydb > /backup/db-$(date +%Y%m%d-%H%M%S).sql"
            container: postgres
            timeout: 5m
```

#### Failover Procedures

**Automated Failover Script:**

```bash
#!/bin/bash
# Disaster recovery failover script

BACKUP_REGION="us-east-1"
PRIMARY_REGION="us-west-2"
CLUSTER_NAME="production-cluster"

echo "=== Disaster Recovery Failover ==="
echo "Failing over from $PRIMARY_REGION to $BACKUP_REGION"

# 1. Verify primary region is down
echo "Checking primary region health..."
if kubectl --context="primary-cluster" cluster-info &>/dev/null; then
    echo "Primary cluster is still accessible. Aborting failover."
    exit 1
fi

# 2. Switch to backup region
echo "Switching to backup region..."
kubectl config use-context backup-cluster

# 3. Restore from latest backup
echo "Restoring from latest backup..."
velero restore create \
    --from-backup daily-backup-$(date +%Y%m%d) \
    --wait

# 4. Update DNS to point to backup region
echo "Updating DNS records..."
aws route53 change-resource-record-sets \
    --hosted-zone-id Z123456789 \
    --change-batch file://dns-update.json

# 5. Verify application health
echo "Verifying application health..."
kubectl get pods --all-namespaces
kubectl get services --all-namespaces

# 6. Send notifications
echo "Sending failover notifications..."
curl -X POST -H 'Content-type: application/json' \
    --data '{"text":"🚨 Disaster recovery failover completed to backup region"}' \
    $SLACK_WEBHOOK_URL

echo "Failover completed successfully!"
```

This comprehensive guide covers every aspect of Kubernetes from a DevOps perspective, including detailed explanations of when to use different services, complete upgrade procedures, troubleshooting strategies, security hardening, cost optimization, and disaster recovery procedures. Each section provides practical, actionable information that DevOps engineers can use in production environments.