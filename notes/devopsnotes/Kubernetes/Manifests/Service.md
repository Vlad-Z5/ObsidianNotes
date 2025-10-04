# Service Manifests

## Overview

A **Service** is an abstract way to expose an application running on a set of Pods as a network service. Services provide stable networking endpoints for dynamic pod sets, enabling service discovery and load balancing.

## Service Types

- **ClusterIP** - Internal cluster IP (default)
- **NodePort** - Exposes service on each node's IP at a static port
- **LoadBalancer** - Exposes service via cloud provider's load balancer
- **ExternalName** - Maps service to DNS name (CNAME)

## Basic Service Structure

```yaml
apiVersion: v1
kind: Service
metadata:
  name: my-service
spec:
  selector:
    app: myapp
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8080
  type: ClusterIP
```

## Complete Service Manifest with All Options

```yaml
apiVersion: v1
kind: Service
metadata:
  # ==================== Metadata ====================
  name: comprehensive-service
  namespace: production

  labels:
    app: web-app
    environment: production
    tier: frontend
    version: v2

  annotations:
    # Service description
    description: "Production web application service"

    # Prometheus scraping
    prometheus.io/scrape: "true"
    prometheus.io/port: "9090"
    prometheus.io/path: "/metrics"

    # AWS Load Balancer annotations
    service.beta.kubernetes.io/aws-load-balancer-type: "nlb"
    service.beta.kubernetes.io/aws-load-balancer-cross-zone-load-balancing-enabled: "true"
    service.beta.kubernetes.io/aws-load-balancer-backend-protocol: "tcp"
    service.beta.kubernetes.io/aws-load-balancer-ssl-cert: "arn:aws:acm:region:account:certificate/id"
    service.beta.kubernetes.io/aws-load-balancer-ssl-ports: "443"

    # GCP Load Balancer annotations
    cloud.google.com/neg: '{"ingress": true}'
    cloud.google.com/backend-config: '{"default": "backend-config"}'

    # Azure Load Balancer annotations
    service.beta.kubernetes.io/azure-load-balancer-internal: "false"
    service.beta.kubernetes.io/azure-dns-label-name: "myapp"

spec:
  # ==================== Service Type ====================
  type: LoadBalancer  # ClusterIP, NodePort, LoadBalancer, ExternalName

  # ==================== Selector ====================
  # Pods with these labels will be part of this service
  selector:
    app: web-app
    tier: frontend

  # ==================== Ports ====================
  ports:
  - name: http
    protocol: TCP
    port: 80          # Service port
    targetPort: 8080  # Container port (can be name or number)
    nodePort: 30080   # NodePort (30000-32767), optional for NodePort/LoadBalancer
    appProtocol: http # Optional: http, https, grpc, etc.

  - name: https
    protocol: TCP
    port: 443
    targetPort: https-port  # Named port from pod
    nodePort: 30443

  - name: metrics
    protocol: TCP
    port: 9090
    targetPort: 9090

  # ==================== ClusterIP Configuration ====================
  clusterIP: 10.96.100.50  # Static IP (optional), or "None" for headless
  clusterIPs:  # Dual-stack support
  - 10.96.100.50   # IPv4
  - fd00::1234      # IPv6

  # ==================== IP Families ====================
  ipFamilyPolicy: PreferDualStack  # SingleStack, PreferDualStack, RequireDualStack
  ipFamilies:
  - IPv4
  - IPv6

  # ==================== Session Affinity ====================
  sessionAffinity: ClientIP  # None or ClientIP
  sessionAffinityConfig:
    clientIP:
      timeoutSeconds: 10800  # 3 hours

  # ==================== External Traffic Policy ====================
  # Controls how external traffic is routed
  externalTrafficPolicy: Local  # Cluster or Local
  # Local: Preserves source IP, only routes to local pods
  # Cluster: May SNAT, routes to any pod

  # ==================== Internal Traffic Policy ====================
  # Controls how internal (cluster) traffic is routed
  internalTrafficPolicy: Local  # Cluster or Local

  # ==================== Health Check ====================
  healthCheckNodePort: 30100  # For externalTrafficPolicy: Local
  allocateLoadBalancerNodePorts: true  # For type: LoadBalancer

  # ==================== External IPs ====================
  externalIPs:
  - 192.168.1.100
  - 192.168.1.101

  # ==================== Load Balancer ====================
  loadBalancerIP: 203.0.113.100  # Deprecated, use annotations instead
  loadBalancerSourceRanges:
  - 10.0.0.0/8
  - 172.16.0.0/12
  - 192.168.0.0/16

  loadBalancerClass: service.k8s.io/nlb  # For custom load balancer implementations

  # ==================== Topology Aware Hints ====================
  # Route traffic to endpoints in same zone/region
  topologyKeys:  # Deprecated, use service.kubernetes.io/topology-aware-hints
  - kubernetes.io/hostname
  - topology.kubernetes.io/zone
  - topology.kubernetes.io/region
  - "*"

  # ==================== Publishing Services ====================
  publishNotReadyAddresses: false  # Include not-ready pods in endpoints

  # ==================== ExternalName Configuration ====================
  # Only for type: ExternalName
  # externalName: external-service.example.com
```

## Service Type Examples

### 1. ClusterIP Service (Default)

```yaml
apiVersion: v1
kind: Service
metadata:
  name: backend-service
  namespace: production
spec:
  type: ClusterIP
  selector:
    app: backend
    tier: api
  ports:
  - name: http
    port: 80
    targetPort: 8080
  - name: grpc
    port: 9090
    targetPort: 9090
```

**Use case:** Internal communication between services
**Accessible:** Only within cluster
**DNS:** `backend-service.production.svc.cluster.local`

### 2. Headless Service (ClusterIP: None)

```yaml
apiVersion: v1
kind: Service
metadata:
  name: database-headless
spec:
  clusterIP: None  # No load balancing, returns all pod IPs
  selector:
    app: postgres
    role: primary
  ports:
  - port: 5432
    targetPort: 5432
  publishNotReadyAddresses: true  # Include starting pods
```

**Use case:** StatefulSets, direct pod-to-pod communication
**DNS:** Returns A records for all pods (no load balancing)
```bash
# DNS returns:
postgres-0.database-headless.default.svc.cluster.local -> 10.244.1.5
postgres-1.database-headless.default.svc.cluster.local -> 10.244.2.6
postgres-2.database-headless.default.svc.cluster.local -> 10.244.3.7
```

### 3. NodePort Service

```yaml
apiVersion: v1
kind: Service
metadata:
  name: web-nodeport
spec:
  type: NodePort
  selector:
    app: web
  ports:
  - name: http
    port: 80
    targetPort: 8080
    nodePort: 30080  # Optional, auto-assigned if not specified
  - name: https
    port: 443
    targetPort: 8443
    nodePort: 30443
  externalTrafficPolicy: Local  # Preserve source IP
```

**Use case:** External access without cloud load balancer
**Accessible:**
- Within cluster: `web-nodeport.default.svc.cluster.local:80`
- External: `<any-node-ip>:30080`

**NodePort range:** 30000-32767 (configurable in kube-apiserver)

### 4. LoadBalancer Service (Cloud Provider)

```yaml
apiVersion: v1
kind: Service
metadata:
  name: web-loadbalancer
  annotations:
    # AWS NLB
    service.beta.kubernetes.io/aws-load-balancer-type: "nlb"
    service.beta.kubernetes.io/aws-load-balancer-cross-zone-load-balancing-enabled: "true"
    service.beta.kubernetes.io/aws-load-balancer-backend-protocol: "tcp"
    service.beta.kubernetes.io/aws-load-balancer-ssl-cert: "arn:aws:acm:us-east-1:123:certificate/abc"
    service.beta.kubernetes.io/aws-load-balancer-ssl-ports: "443"
spec:
  type: LoadBalancer
  selector:
    app: web
  ports:
  - name: http
    port: 80
    targetPort: 8080
  - name: https
    port: 443
    targetPort: 8443
  externalTrafficPolicy: Local
  loadBalancerSourceRanges:
  - 0.0.0.0/0  # Allow all (default)
```

**Use case:** Production applications with external access
**Cloud Provider creates:**
- AWS: ELB/NLB/ALB
- GCP: Cloud Load Balancer
- Azure: Azure Load Balancer

### 5. ExternalName Service (DNS CNAME)

```yaml
apiVersion: v1
kind: Service
metadata:
  name: external-database
spec:
  type: ExternalName
  externalName: db.prod.example.com
  ports:
  - port: 5432
```

**Use case:** Alias external services
**DNS:** CNAME record pointing to `db.prod.example.com`
**No selector, no endpoints**

### 6. Service with Multiple Selectors

```yaml
apiVersion: v1
kind: Service
metadata:
  name: multi-version-service
spec:
  selector:
    app: myapp
    # Does NOT select version - will load balance across all versions
  ports:
  - port: 80
    targetPort: 8080
```

### 7. Service without Selector (Manual Endpoints)

```yaml
apiVersion: v1
kind: Service
metadata:
  name: external-api
spec:
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8080

---
# Manual endpoints
apiVersion: v1
kind: Endpoints
metadata:
  name: external-api  # Must match service name
subsets:
- addresses:
  - ip: 192.168.1.100
  - ip: 192.168.1.101
  ports:
  - port: 8080
```

**Use case:** External services, legacy systems, manual endpoint management

## Real-World Production Patterns

### 1. Multi-Port Service with Named Ports

```yaml
apiVersion: v1
kind: Service
metadata:
  name: web-service
spec:
  selector:
    app: web
  ports:
  - name: http
    port: 80
    targetPort: http-port  # Named port in pod
  - name: https
    port: 443
    targetPort: https-port
  - name: metrics
    port: 9090
    targetPort: metrics
  - name: health
    port: 8081
    targetPort: health

---
# Pod with named ports
apiVersion: v1
kind: Pod
metadata:
  name: web-pod
  labels:
    app: web
spec:
  containers:
  - name: nginx
    image: nginx:1.25
    ports:
    - name: http-port
      containerPort: 8080
    - name: https-port
      containerPort: 8443
    - name: metrics
      containerPort: 9090
    - name: health
      containerPort: 8081
```

### 2. Service with Session Affinity (Sticky Sessions)

```yaml
apiVersion: v1
kind: Service
metadata:
  name: stateful-app
spec:
  selector:
    app: stateful-app
  ports:
  - port: 80
    targetPort: 8080
  sessionAffinity: ClientIP
  sessionAffinityConfig:
    clientIP:
      timeoutSeconds: 10800  # 3 hours
```

**Behavior:**
- Same client IP always routes to same pod
- Timeout: 3 hours of inactivity
- Based on client IP (not cookies)

### 3. Internal Load Balancer (Cloud Provider)

```yaml
# AWS Internal NLB
apiVersion: v1
kind: Service
metadata:
  name: internal-api
  annotations:
    service.beta.kubernetes.io/aws-load-balancer-internal: "true"
    service.beta.kubernetes.io/aws-load-balancer-type: "nlb"
spec:
  type: LoadBalancer
  selector:
    app: api
  ports:
  - port: 443
    targetPort: 8443

---
# GCP Internal Load Balancer
apiVersion: v1
kind: Service
metadata:
  name: internal-api
  annotations:
    networking.gke.io/load-balancer-type: "Internal"
spec:
  type: LoadBalancer
  selector:
    app: api
  ports:
  - port: 443
    targetPort: 8443

---
# Azure Internal Load Balancer
apiVersion: v1
kind: Service
metadata:
  name: internal-api
  annotations:
    service.beta.kubernetes.io/azure-load-balancer-internal: "true"
spec:
  type: LoadBalancer
  selector:
    app: api
  ports:
  - port: 443
    targetPort: 8443
```

### 4. Service with Topology-Aware Routing

```yaml
apiVersion: v1
kind: Service
metadata:
  name: geo-distributed-app
  annotations:
    service.kubernetes.io/topology-aware-hints: auto
spec:
  selector:
    app: web
  ports:
  - port: 80
    targetPort: 8080
  internalTrafficPolicy: Local  # Prefer same-node pods
```

**Behavior:**
- Routes traffic to pods in same zone/region
- Reduces cross-AZ traffic costs
- Falls back to any pod if no local pods available

### 5. Service with Health Check Node Port

```yaml
apiVersion: v1
kind: Service
metadata:
  name: web-with-health-check
spec:
  type: LoadBalancer
  externalTrafficPolicy: Local
  selector:
    app: web
  ports:
  - port: 80
    targetPort: 8080
  # Health check port for load balancer
  healthCheckNodePort: 30100  # Auto-assigned if not specified
```

**Behavior:**
- Load balancer checks `<node-ip>:30100/healthz`
- Only routes to nodes with healthy pods
- Required for `externalTrafficPolicy: Local`

### 6. Multi-Cluster Service (Service Export)

```yaml
# Export service to other clusters
apiVersion: multicluster.x-k8s.io/v1alpha1
kind: ServiceExport
metadata:
  name: web-service
  namespace: production

---
# Service remains the same
apiVersion: v1
kind: Service
metadata:
  name: web-service
  namespace: production
spec:
  selector:
    app: web
  ports:
  - port: 80
    targetPort: 8080
```

### 7. gRPC Service with Protocol

```yaml
apiVersion: v1
kind: Service
metadata:
  name: grpc-service
  annotations:
    cloud.google.com/app-protocols: '{"grpc":"HTTP2"}'
spec:
  type: LoadBalancer
  selector:
    app: grpc-server
  ports:
  - name: grpc
    port: 9090
    targetPort: 9090
    appProtocol: grpc  # Kubernetes 1.20+
```

### 8. Service with IP Whitelisting

```yaml
apiVersion: v1
kind: Service
metadata:
  name: admin-api
spec:
  type: LoadBalancer
  selector:
    app: admin-api
  ports:
  - port: 443
    targetPort: 8443
  # Only allow specific IP ranges
  loadBalancerSourceRanges:
  - 10.0.0.0/8      # Corporate network
  - 203.0.113.0/24  # Office IP range
```

### 9. Database Service for StatefulSet

```yaml
# Headless service for StatefulSet
apiVersion: v1
kind: Service
metadata:
  name: postgres-headless
spec:
  clusterIP: None
  selector:
    app: postgres
  ports:
  - name: postgres
    port: 5432
    targetPort: 5432
  publishNotReadyAddresses: true

---
# Read-only service (replicas only)
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
    targetPort: 5432

---
# Primary-only service
apiVersion: v1
kind: Service
metadata:
  name: postgres-primary
spec:
  selector:
    app: postgres
    role: primary
  ports:
  - port: 5432
    targetPort: 5432
```

**Application connection strings:**
```bash
# Write to primary
DB_WRITE=postgres-primary.default.svc.cluster.local:5432

# Read from replicas (load balanced)
DB_READ=postgres-read.default.svc.cluster.local:5432

# Direct pod access via headless service
postgres-0.postgres-headless.default.svc.cluster.local:5432
postgres-1.postgres-headless.default.svc.cluster.local:5432
```

### 10. Canary/Blue-Green Service Switching

```yaml
# Blue deployment (current)
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app-blue
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

---
# Green deployment (new)
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app-green
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

---
# Service switches between blue and green
apiVersion: v1
kind: Service
metadata:
  name: myapp-service
spec:
  selector:
    app: myapp
    version: blue  # Change to "green" for instant cutover
  ports:
  - port: 80
    targetPort: 8080
```

**Cutover:**
```bash
# Switch to green
kubectl patch svc myapp-service -p '{"spec":{"selector":{"version":"green"}}}'

# Rollback to blue
kubectl patch svc myapp-service -p '{"spec":{"selector":{"version":"blue"}}}'
```

### 11. Weighted Traffic Splitting (Canary)

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
# Service selects both (10:1 ratio = 10% canary)
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

**Traffic distribution:**
- 9 stable pods + 1 canary pod = 10 total
- ~10% traffic goes to canary
- Increase canary replicas to increase canary traffic

## Cloud Provider Specific Annotations

### AWS Load Balancer Annotations

```yaml
apiVersion: v1
kind: Service
metadata:
  name: aws-nlb-service
  annotations:
    # Load balancer type
    service.beta.kubernetes.io/aws-load-balancer-type: "nlb"  # nlb, nlb-ip, external (ALB)

    # Internal vs External
    service.beta.kubernetes.io/aws-load-balancer-internal: "false"

    # Scheme
    service.beta.kubernetes.io/aws-load-balancer-scheme: "internet-facing"  # or internal

    # Cross-zone load balancing
    service.beta.kubernetes.io/aws-load-balancer-cross-zone-load-balancing-enabled: "true"

    # Proxy protocol
    service.beta.kubernetes.io/aws-load-balancer-proxy-protocol: "*"

    # SSL/TLS
    service.beta.kubernetes.io/aws-load-balancer-ssl-cert: "arn:aws:acm:region:account:certificate/id"
    service.beta.kubernetes.io/aws-load-balancer-ssl-ports: "443,8443"
    service.beta.kubernetes.io/aws-load-balancer-ssl-negotiation-policy: "ELBSecurityPolicy-TLS-1-2-2017-01"
    service.beta.kubernetes.io/aws-load-balancer-backend-protocol: "tcp"  # tcp, http, https

    # Target type
    service.beta.kubernetes.io/aws-load-balancer-target-type: "instance"  # instance or ip

    # Subnets
    service.beta.kubernetes.io/aws-load-balancer-subnets: "subnet-xxx,subnet-yyy"

    # Security groups
    service.beta.kubernetes.io/aws-load-balancer-security-groups: "sg-xxx,sg-yyy"

    # EIP allocation IDs (for NLB)
    service.beta.kubernetes.io/aws-load-balancer-eip-allocations: "eipalloc-xxx,eipalloc-yyy"

    # Access logs
    service.beta.kubernetes.io/aws-load-balancer-access-log-enabled: "true"
    service.beta.kubernetes.io/aws-load-balancer-access-log-s3-bucket-name: "my-logs-bucket"
    service.beta.kubernetes.io/aws-load-balancer-access-log-s3-bucket-prefix: "nlb-logs"

    # Connection draining
    service.beta.kubernetes.io/aws-load-balancer-connection-draining-enabled: "true"
    service.beta.kubernetes.io/aws-load-balancer-connection-draining-timeout: "60"

    # Health check
    service.beta.kubernetes.io/aws-load-balancer-healthcheck-protocol: "TCP"
    service.beta.kubernetes.io/aws-load-balancer-healthcheck-port: "traffic-port"
    service.beta.kubernetes.io/aws-load-balancer-healthcheck-interval: "10"
    service.beta.kubernetes.io/aws-load-balancer-healthcheck-timeout: "5"
    service.beta.kubernetes.io/aws-load-balancer-healthcheck-healthy-threshold: "2"
    service.beta.kubernetes.io/aws-load-balancer-healthcheck-unhealthy-threshold: "2"

spec:
  type: LoadBalancer
  selector:
    app: web
  ports:
  - port: 443
    targetPort: 8443
```

### GCP Load Balancer Annotations

```yaml
apiVersion: v1
kind: Service
metadata:
  name: gcp-lb-service
  annotations:
    # Internal load balancer
    networking.gke.io/load-balancer-type: "Internal"

    # Backend service
    cloud.google.com/backend-config: '{"default": "backend-config"}'

    # NEG (Network Endpoint Groups)
    cloud.google.com/neg: '{"ingress": true}'

    # Session affinity
    cloud.google.com/session-affinity-type: "CLIENT_IP"
    cloud.google.com/session-affinity-timeout-sec: "10800"

    # Connection draining
    cloud.google.com/connection-draining-timeout-sec: "60"

    # App protocol
    cloud.google.com/app-protocols: '{"http":"HTTP","https":"HTTPS"}'

spec:
  type: LoadBalancer
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

### Azure Load Balancer Annotations

```yaml
apiVersion: v1
kind: Service
metadata:
  name: azure-lb-service
  annotations:
    # Internal load balancer
    service.beta.kubernetes.io/azure-load-balancer-internal: "true"

    # Subnet for internal LB
    service.beta.kubernetes.io/azure-load-balancer-internal-subnet: "my-subnet"

    # Resource group
    service.beta.kubernetes.io/azure-load-balancer-resource-group: "my-rg"

    # Static IP
    service.beta.kubernetes.io/azure-load-balancer-ipv4: "10.0.1.100"

    # DNS label
    service.beta.kubernetes.io/azure-dns-label-name: "myapp"

    # Health probe
    service.beta.kubernetes.io/azure-load-balancer-health-probe-protocol: "tcp"
    service.beta.kubernetes.io/azure-load-balancer-health-probe-request-path: "/healthz"
    service.beta.kubernetes.io/azure-load-balancer-health-probe-interval: "5"
    service.beta.kubernetes.io/azure-load-balancer-health-probe-num-of-probe: "2"

    # Session persistence
    service.beta.kubernetes.io/azure-load-balancer-disable-tcp-reset: "false"

spec:
  type: LoadBalancer
  selector:
    app: web
  ports:
  - port: 80
    targetPort: 8080
```

## Service Discovery

### DNS Resolution

```bash
# Service DNS format:
# <service-name>.<namespace>.svc.<cluster-domain>

# ClusterIP service
my-service.default.svc.cluster.local

# Headless service (returns all pod IPs)
my-headless.default.svc.cluster.local

# Pod DNS (for headless service with StatefulSet)
pod-0.my-headless.default.svc.cluster.local
pod-1.my-headless.default.svc.cluster.local

# Short forms (within same namespace)
my-service
my-service.default
my-service.default.svc

# Port-specific SRV records
_http._tcp.my-service.default.svc.cluster.local
_https._tcp.my-service.default.svc.cluster.local
```

### Environment Variables

When a pod is created, Kubernetes automatically creates environment variables for all services:

```bash
# For service named "database" in namespace "default"
DATABASE_SERVICE_HOST=10.96.0.10
DATABASE_SERVICE_PORT=5432
DATABASE_PORT=tcp://10.96.0.10:5432
DATABASE_PORT_5432_TCP=tcp://10.96.0.10:5432
DATABASE_PORT_5432_TCP_PROTO=tcp
DATABASE_PORT_5432_TCP_PORT=5432
DATABASE_PORT_5432_TCP_ADDR=10.96.0.10
```

**Note:** Environment variables are only created for services that exist when the pod starts.

## Troubleshooting Services

### Debug Service Not Working

```bash
# 1. Check service exists
kubectl get svc my-service

# 2. Check service endpoints
kubectl get endpoints my-service
# Should show pod IPs

# 3. Describe service
kubectl describe svc my-service

# 4. Check service selector matches pod labels
kubectl get pods --show-labels
kubectl get svc my-service -o yaml | grep -A 5 selector

# 5. Test DNS resolution from pod
kubectl run -it --rm debug --image=busybox --restart=Never -- nslookup my-service

# 6. Test connectivity from pod
kubectl run -it --rm debug --image=busybox --restart=Never -- wget -O- http://my-service

# 7. Check kube-proxy logs
kubectl logs -n kube-system -l k8s-app=kube-proxy

# 8. Verify iptables rules (on node)
sudo iptables -t nat -L -n | grep my-service

# 9. Check for network policies blocking traffic
kubectl get networkpolicies
```

### Common Issues

**No endpoints:**
- Selector doesn't match pod labels
- Pods not ready (failing readiness probes)
- Pods don't exist

**Can't connect to service:**
- Network policy blocking traffic
- kube-proxy not running
- Service port doesn't match container port

**LoadBalancer pending:**
- Cloud provider integration not configured
- Insufficient permissions
- Quota exceeded

## Performance Optimization

### Use Topology-Aware Routing

```yaml
metadata:
  annotations:
    service.kubernetes.io/topology-aware-hints: auto
spec:
  internalTrafficPolicy: Local
```

### Minimize Cross-AZ Traffic

```yaml
spec:
  externalTrafficPolicy: Local  # For external traffic
  internalTrafficPolicy: Local  # For internal traffic
```

### Session Affinity for Stateful Apps

```yaml
spec:
  sessionAffinity: ClientIP
  sessionAffinityConfig:
    clientIP:
      timeoutSeconds: 10800
```

## References

- [Service Specification](https://kubernetes.io/docs/reference/kubernetes-api/service-resources/service-v1/)
- [Service Networking](https://kubernetes.io/docs/concepts/services-networking/service/)
- [DNS for Services and Pods](https://kubernetes.io/docs/concepts/services-networking/dns-pod-service/)
- [Topology-Aware Routing](https://kubernetes.io/docs/concepts/services-networking/topology-aware-routing/)
