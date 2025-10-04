# Cloud Controller Manager

## Overview

The **Cloud Controller Manager (CCM)** is a Kubernetes component that embeds cloud-specific control logic. It allows cloud providers to integrate with Kubernetes without modifying the core Kubernetes codebase. The CCM runs cloud-specific controllers that manage cloud resources like load balancers, storage volumes, and node lifecycle.

**Component Type:** Control Plane (Cloud-Specific)
**Process Name:** `cloud-controller-manager`
**Default Port:** 10258 (HTTPS metrics)
**Runs On:** Control plane nodes
**Stateless:** Yes (reads state from API server)
**Cloud Providers:** AWS, GCP, Azure, OpenStack, vSphere, etc.

## What Cloud Controller Manager Actually Does

The CCM is the bridge between Kubernetes and your cloud provider. It handles cloud-specific operations that were previously managed by kube-controller-manager.

### Real-World Analogy
Think of CCM as a translator between Kubernetes (universal language) and cloud providers (regional dialects):
- **Kubernetes says:** "Create a LoadBalancer service"
- **CCM translates to AWS:** "Create an ELB/NLB/ALB with these settings"
- **CCM translates to GCP:** "Create a Cloud Load Balancer"
- **CCM translates to Azure:** "Create an Azure Load Balancer"

### Why CCM Exists

**Before CCM (Legacy):**
```
kube-controller-manager (single binary)
├── Core controllers (Deployment, ReplicaSet, etc.)
├── AWS-specific code
├── GCP-specific code
├── Azure-specific code
└── vSphere-specific code

Problems:
- Cloud code mixed with core Kubernetes
- Hard to add new cloud providers
- Kubernetes release tied to cloud provider updates
- Security: Cloud credentials in core component
```

**After CCM (Modern):**
```
kube-controller-manager (cloud-agnostic)
├── Core controllers only
└── No cloud-specific code

cloud-controller-manager (separate binary)
├── Cloud provider specific
├── Maintained by cloud provider
├── Independent release cycle
└── Isolated cloud credentials
```

## Architecture

### Core Controllers in CCM

**1. Node Controller**
- Initializes nodes with cloud provider metadata
- Adds cloud-specific labels (region, zone, instance-type)
- Monitors node health with cloud provider APIs
- Deletes nodes when cloud instances terminated

**2. Service Controller**
- Creates/updates/deletes cloud load balancers
- Manages LoadBalancer service types
- Updates service status with external IPs

**3. Route Controller**
- Configures routes in cloud network
- Enables pod-to-pod communication across nodes
- Updates VPC routing tables (AWS), VPC routes (GCP), etc.

**4. PersistentVolume Controller** (in some CCMs)
- Provisions cloud storage volumes
- Attaches/detaches volumes to nodes
- Note: Being replaced by CSI drivers

### CCM vs In-Tree Cloud Provider

```
┌─────────────────────────────────────────────────────────────┐
│                 Legacy (In-Tree) Architecture                │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  kube-controller-manager                                     │
│  ├── --cloud-provider=aws                                   │
│  ├── Core controllers                                        │
│  └── Cloud-specific controllers (built-in)                  │
│                                                              │
│  kube-apiserver                                             │
│  └── --cloud-provider=aws                                   │
│                                                              │
│  kubelet                                                     │
│  └── --cloud-provider=aws                                   │
│                                                              │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                Modern (CCM + CSI) Architecture               │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  kube-controller-manager                                     │
│  ├── --cloud-provider=external                              │
│  └── Core controllers only                                   │
│                                                              │
│  kube-apiserver                                             │
│  └── --cloud-provider=external                              │
│                                                              │
│  kubelet                                                     │
│  └── --cloud-provider=external                              │
│                                                              │
│  cloud-controller-manager (separate deployment)             │
│  ├── Node controller                                         │
│  ├── Service controller (LoadBalancer)                      │
│  └── Route controller                                        │
│                                                              │
│  CSI Driver (separate deployment)                           │
│  └── Volume provisioning/attachment                         │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Installation and Configuration

### AWS Cloud Controller Manager

#### Prerequisites

```bash
# 1. Tag EC2 instances and resources
# All instances must have this tag:
kubernetes.io/cluster/<cluster-name>=owned

# 2. IAM permissions for CCM
# Create IAM role with these policies:
# - EC2 (DescribeInstances, DescribeRouteTables, CreateRoute, etc.)
# - ELB (CreateLoadBalancer, DescribeLoadBalancers, etc.)
# - IAM (if using IRSA)
```

#### Deployment Manifest

```yaml
# ServiceAccount for CCM
apiVersion: v1
kind: ServiceAccount
metadata:
  name: cloud-controller-manager
  namespace: kube-system
  annotations:
    # IRSA (IAM Roles for Service Accounts) - EKS only
    eks.amazonaws.com/role-arn: arn:aws:iam::123456789:role/eks-ccm-role

---
# ClusterRole
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: system:cloud-controller-manager
rules:
- apiGroups: [""]
  resources: ["events"]
  verbs: ["create", "patch", "update"]
- apiGroups: [""]
  resources: ["nodes"]
  verbs: ["*"]
- apiGroups: [""]
  resources: ["nodes/status"]
  verbs: ["patch"]
- apiGroups: [""]
  resources: ["services"]
  verbs: ["list", "patch", "update", "watch"]
- apiGroups: [""]
  resources: ["services/status"]
  verbs: ["patch"]
- apiGroups: [""]
  resources: ["serviceaccounts"]
  verbs: ["create", "get"]
- apiGroups: [""]
  resources: ["persistentvolumes"]
  verbs: ["get", "list", "update", "watch"]
- apiGroups: [""]
  resources: ["endpoints"]
  verbs: ["create", "get", "list", "watch", "update"]
- apiGroups: ["coordination.k8s.io"]
  resources: ["leases"]
  verbs: ["get", "create", "update"]

---
# ClusterRoleBinding
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: system:cloud-controller-manager
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: system:cloud-controller-manager
subjects:
- kind: ServiceAccount
  name: cloud-controller-manager
  namespace: kube-system

---
# DaemonSet (one CCM per control plane node)
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: aws-cloud-controller-manager
  namespace: kube-system
  labels:
    k8s-app: aws-cloud-controller-manager
spec:
  selector:
    matchLabels:
      k8s-app: aws-cloud-controller-manager
  updateStrategy:
    type: RollingUpdate
  template:
    metadata:
      labels:
        k8s-app: aws-cloud-controller-manager
    spec:
      serviceAccountName: cloud-controller-manager
      nodeSelector:
        node-role.kubernetes.io/control-plane: ""
      tolerations:
      - key: node.cloudprovider.kubernetes.io/uninitialized
        value: "true"
        effect: NoSchedule
      - key: node-role.kubernetes.io/control-plane
        effect: NoSchedule
      - key: node-role.kubernetes.io/master
        effect: NoSchedule
      hostNetwork: true
      priorityClassName: system-node-critical
      containers:
      - name: aws-cloud-controller-manager
        image: registry.k8s.io/provider-aws/cloud-controller-manager:v1.28.0
        args:
        # Cloud provider
        - --cloud-provider=aws

        # Cluster configuration
        - --cluster-name=my-k8s-cluster
        - --cluster-cidr=10.244.0.0/16

        # Leader election
        - --leader-elect=true
        - --leader-elect-lease-duration=15s
        - --leader-elect-renew-deadline=10s
        - --leader-elect-retry-period=2s

        # Controllers to run
        - --controllers=node,service,route
        # Disable specific controllers if needed:
        # - --controllers=*,-route

        # Node configuration
        - --configure-cloud-routes=true
        - --allocate-node-cidrs=true
        - --use-service-account-credentials=true

        # AWS specific
        - --aws-region=us-east-1
        # - --aws-access-key-id=<key>  # Don't use if using IRSA
        # - --aws-secret-access-key=<secret>  # Don't use if using IRSA

        # Bind address
        - --bind-address=0.0.0.0
        - --secure-port=10258

        # Logging
        - --v=2

        env:
        # AWS region (if not using flag)
        - name: AWS_REGION
          value: us-east-1
        # Use IRSA for credentials (recommended)
        - name: AWS_ROLE_ARN
          value: arn:aws:iam::123456789:role/eks-ccm-role
        - name: AWS_WEB_IDENTITY_TOKEN_FILE
          value: /var/run/secrets/eks.amazonaws.com/serviceaccount/token

        resources:
          requests:
            cpu: 200m
            memory: 128Mi
          limits:
            memory: 256Mi

        volumeMounts:
        - name: ca-certs
          mountPath: /etc/ssl/certs
          readOnly: true
        - name: k8s-certs
          mountPath: /etc/kubernetes/pki
          readOnly: true
        - name: aws-token
          mountPath: /var/run/secrets/eks.amazonaws.com/serviceaccount
          readOnly: true

        livenessProbe:
          httpGet:
            path: /healthz
            port: 10258
            scheme: HTTPS
          initialDelaySeconds: 20
          periodSeconds: 10
          timeoutSeconds: 15

      volumes:
      - name: ca-certs
        hostPath:
          path: /etc/ssl/certs
      - name: k8s-certs
        hostPath:
          path: /etc/kubernetes/pki
      - name: aws-token
        projected:
          sources:
          - serviceAccountToken:
              audience: sts.amazonaws.com
              expirationSeconds: 86400
              path: token
```

### GCP Cloud Controller Manager

```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: gcp-cloud-controller-manager
  namespace: kube-system
spec:
  selector:
    matchLabels:
      component: cloud-controller-manager
  template:
    metadata:
      labels:
        component: cloud-controller-manager
    spec:
      serviceAccountName: cloud-controller-manager
      nodeSelector:
        node-role.kubernetes.io/control-plane: ""
      tolerations:
      - key: node.cloudprovider.kubernetes.io/uninitialized
        value: "true"
        effect: NoSchedule
      - key: node-role.kubernetes.io/control-plane
        effect: NoSchedule
      hostNetwork: true
      containers:
      - name: gcp-cloud-controller-manager
        image: gcr.io/cloud-provider-gcp/cloud-controller-manager:latest
        args:
        - --cloud-provider=gce
        - --cluster-name=my-gke-cluster
        - --cluster-cidr=10.244.0.0/16
        - --allocate-node-cidrs=true
        - --configure-cloud-routes=true
        - --leader-elect=true
        - --use-service-account-credentials=true
        - --controllers=node,service,route
        - --v=2

        env:
        # GCP project
        - name: GCE_PROJECT
          value: my-gcp-project
        # GCP zone/region
        - name: GCE_ZONE
          value: us-central1-a
        # Use workload identity (recommended)
        - name: GOOGLE_APPLICATION_CREDENTIALS
          value: /var/secrets/google/key.json

        volumeMounts:
        - name: gcp-creds
          mountPath: /var/secrets/google
          readOnly: true

      volumes:
      - name: gcp-creds
        secret:
          secretName: gcp-cloud-controller-credentials
```

### Azure Cloud Controller Manager

```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: azure-cloud-controller-manager
  namespace: kube-system
spec:
  selector:
    matchLabels:
      component: cloud-controller-manager
  template:
    metadata:
      labels:
        component: cloud-controller-manager
    spec:
      serviceAccountName: cloud-controller-manager
      nodeSelector:
        node-role.kubernetes.io/control-plane: ""
      tolerations:
      - key: node.cloudprovider.kubernetes.io/uninitialized
        value: "true"
        effect: NoSchedule
      - key: node-role.kubernetes.io/control-plane
        effect: NoSchedule
      hostNetwork: true
      containers:
      - name: azure-cloud-controller-manager
        image: mcr.microsoft.com/oss/kubernetes/azure-cloud-controller-manager:v1.28.0
        args:
        - --cloud-provider=azure
        - --cloud-config=/etc/kubernetes/azure.json
        - --cluster-name=my-aks-cluster
        - --allocate-node-cidrs=true
        - --configure-cloud-routes=true
        - --leader-elect=true
        - --v=2

        volumeMounts:
        - name: azure-config
          mountPath: /etc/kubernetes/azure.json
          readOnly: true

      volumes:
      - name: azure-config
        hostPath:
          path: /etc/kubernetes/azure.json
          type: File
```

#### Azure Configuration File

```json
{
  "cloud": "AzurePublicCloud",
  "tenantId": "00000000-0000-0000-0000-000000000000",
  "subscriptionId": "00000000-0000-0000-0000-000000000000",
  "aadClientId": "00000000-0000-0000-0000-000000000000",
  "aadClientSecret": "client-secret",
  "resourceGroup": "my-resource-group",
  "location": "eastus",
  "vnetName": "aks-vnet",
  "vnetResourceGroup": "network-rg",
  "subnetName": "aks-subnet",
  "securityGroupName": "aks-nsg",
  "routeTableName": "aks-routetable",
  "loadBalancerSku": "Standard",
  "useManagedIdentityExtension": true,
  "useInstanceMetadata": true
}
```

## Cloud Provider Specific Features

### AWS Cloud Provider

#### LoadBalancer Service Annotations

```yaml
apiVersion: v1
kind: Service
metadata:
  name: my-service
  annotations:
    # Load balancer type
    service.beta.kubernetes.io/aws-load-balancer-type: "nlb"  # nlb, nlb-ip, or external (ALB)

    # Internal vs External
    service.beta.kubernetes.io/aws-load-balancer-internal: "false"

    # Cross-zone load balancing
    service.beta.kubernetes.io/aws-load-balancer-cross-zone-load-balancing-enabled: "true"

    # SSL/TLS
    service.beta.kubernetes.io/aws-load-balancer-ssl-cert: "arn:aws:acm:region:account:certificate/id"
    service.beta.kubernetes.io/aws-load-balancer-ssl-ports: "443"
    service.beta.kubernetes.io/aws-load-balancer-backend-protocol: "tcp"

    # Target type
    service.beta.kubernetes.io/aws-load-balancer-target-type: "instance"  # instance or ip

    # Subnets
    service.beta.kubernetes.io/aws-load-balancer-subnets: "subnet-xxxx,subnet-yyyy"

    # Security groups
    service.beta.kubernetes.io/aws-load-balancer-security-groups: "sg-xxxx"

    # Proxy protocol
    service.beta.kubernetes.io/aws-load-balancer-proxy-protocol: "*"

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

    # Access logs
    service.beta.kubernetes.io/aws-load-balancer-access-log-enabled: "true"
    service.beta.kubernetes.io/aws-load-balancer-access-log-s3-bucket-name: "my-logs-bucket"
    service.beta.kubernetes.io/aws-load-balancer-access-log-s3-bucket-prefix: "nlb-logs"

    # IP address type
    service.beta.kubernetes.io/aws-load-balancer-ip-address-type: "ipv4"  # ipv4 or dualstack

    # EIP allocation
    service.beta.kubernetes.io/aws-load-balancer-eip-allocations: "eipalloc-xxxxxx,eipalloc-yyyyyy"

spec:
  type: LoadBalancer
  selector:
    app: my-app
  ports:
  - port: 80
    targetPort: 8080
```

#### Node Labels Added by AWS CCM

```bash
# Check node labels added by CCM
kubectl get nodes -L topology.kubernetes.io/region,topology.kubernetes.io/zone,node.kubernetes.io/instance-type

# Example output:
NAME                REGION      ZONE          INSTANCE-TYPE
ip-10-0-1-100.ec2   us-east-1   us-east-1a    t3.medium
ip-10-0-2-200.ec2   us-east-1   us-east-1b    t3.large

# Full labels:
kubectl describe node ip-10-0-1-100.ec2 | grep -A 20 "Labels:"

# Output:
# topology.kubernetes.io/region=us-east-1
# topology.kubernetes.io/zone=us-east-1a
# node.kubernetes.io/instance-type=t3.medium
# failure-domain.beta.kubernetes.io/region=us-east-1  # deprecated
# failure-domain.beta.kubernetes.io/zone=us-east-1a   # deprecated
# alpha.eksctl.io/instance-id=i-0123456789abcdef0
# eks.amazonaws.com/nodegroup=my-nodegroup
```

### GCP Cloud Provider

#### LoadBalancer Service Annotations

```yaml
apiVersion: v1
kind: Service
metadata:
  name: my-service
  annotations:
    # Internal load balancer
    networking.gke.io/load-balancer-type: "Internal"

    # Backend service
    cloud.google.com/backend-config: '{"default": "my-backend-config"}'

    # NEG (Network Endpoint Groups)
    cloud.google.com/neg: '{"ingress": true}'

    # Session affinity
    cloud.google.com/session-affinity-type: "CLIENT_IP"
    cloud.google.com/session-affinity-timeout-sec: "10800"

    # Connection draining
    cloud.google.com/connection-draining-timeout-sec: "60"

spec:
  type: LoadBalancer
  selector:
    app: my-app
  ports:
  - port: 80
    targetPort: 8080
```

#### Node Labels Added by GCP CCM

```bash
# GCP node labels
kubectl get nodes -L topology.kubernetes.io/region,topology.kubernetes.io/zone,node.kubernetes.io/instance-type

# Additional GCP labels:
# cloud.google.com/gke-nodepool=my-nodepool
# cloud.google.com/gke-os-distribution=cos
# cloud.google.com/machine-family=n1
```

### Azure Cloud Provider

#### LoadBalancer Service Annotations

```yaml
apiVersion: v1
kind: Service
metadata:
  name: my-service
  annotations:
    # Internal load balancer
    service.beta.kubernetes.io/azure-load-balancer-internal: "true"

    # Subnet for internal LB
    service.beta.kubernetes.io/azure-load-balancer-internal-subnet: "my-subnet"

    # Resource group
    service.beta.kubernetes.io/azure-load-balancer-resource-group: "my-rg"

    # IP address
    service.beta.kubernetes.io/azure-load-balancer-ipv4: "10.0.1.100"
    service.beta.kubernetes.io/azure-dns-label-name: "my-app-lb"

    # Health probe
    service.beta.kubernetes.io/azure-load-balancer-health-probe-protocol: "tcp"
    service.beta.kubernetes.io/azure-load-balancer-health-probe-request-path: "/healthz"

    # Session persistence
    service.beta.kubernetes.io/azure-load-balancer-disable-tcp-reset: "false"

spec:
  type: LoadBalancer
  selector:
    app: my-app
  ports:
  - port: 80
    targetPort: 8080
```

## Real-World Use Cases

### Use Case 1: Multi-AZ High Availability with AWS

```yaml
# Service with cross-zone load balancing
apiVersion: v1
kind: Service
metadata:
  name: ha-web-app
  annotations:
    service.beta.kubernetes.io/aws-load-balancer-type: "nlb"
    service.beta.kubernetes.io/aws-load-balancer-cross-zone-load-balancing-enabled: "true"
    service.beta.kubernetes.io/aws-load-balancer-subnets: "subnet-us-east-1a,subnet-us-east-1b,subnet-us-east-1c"
spec:
  type: LoadBalancer
  selector:
    app: web-app
  ports:
  - port: 443
    targetPort: 8443

---
# Deployment with zone anti-affinity
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-app
spec:
  replicas: 6
  selector:
    matchLabels:
      app: web-app
  template:
    metadata:
      labels:
        app: web-app
    spec:
      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            podAffinityTerm:
              labelSelector:
                matchLabels:
                  app: web-app
              topologyKey: topology.kubernetes.io/zone
      containers:
      - name: web
        image: myapp:v1
        ports:
        - containerPort: 8443
```

**CCM Behavior:**
```
1. Service created → Service Controller detects
2. Parse AWS annotations
3. Create NLB in 3 AZs (us-east-1a, us-east-1b, us-east-1c)
4. Enable cross-zone load balancing
5. Register EC2 instances from all zones as targets
6. Health check all targets
7. Return NLB DNS → Update Service status
8. Pods spread across zones via anti-affinity
9. NLB routes traffic to healthy pods in any zone
```

### Use Case 2: Internal Service with GCP

```yaml
# Internal load balancer for database access
apiVersion: v1
kind: Service
metadata:
  name: postgres-internal
  annotations:
    networking.gke.io/load-balancer-type: "Internal"
    cloud.google.com/backend-config: '{"default": "postgres-backend"}'
spec:
  type: LoadBalancer
  selector:
    app: postgres
  ports:
  - port: 5432
    targetPort: 5432

---
# Backend config for connection draining
apiVersion: cloud.google.com/v1
kind: BackendConfig
metadata:
  name: postgres-backend
spec:
  connectionDraining:
    drainingTimeoutSec: 60
  sessionAffinity:
    affinityType: "CLIENT_IP"
    affinityCookieTtlSec: 3600
  timeoutSec: 300
```

**CCM Behavior:**
```
1. Service created → GCP Service Controller detects
2. Create internal TCP/UDP load balancer
3. LB gets private IP from VPC subnet
4. Configure backend service with session affinity
5. Set connection draining timeout (60s)
6. Create health check for port 5432
7. Add GKE node instances to backend
8. Update Service status with internal IP
9. Other pods/services access via internal LB
```

### Use Case 3: SSL Termination on Azure

```yaml
# HTTPS service with SSL termination
apiVersion: v1
kind: Service
metadata:
  name: web-https
  annotations:
    service.beta.kubernetes.io/azure-load-balancer-internal: "false"
    service.beta.kubernetes.io/azure-dns-label-name: "myapp-prod"
spec:
  type: LoadBalancer
  selector:
    app: web-app
  ports:
  - name: https
    port: 443
    targetPort: 8080

---
# Ingress for SSL termination (alternative)
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: web-ingress
  annotations:
    kubernetes.io/ingress.class: azure/application-gateway
    appgw.ingress.kubernetes.io/ssl-redirect: "true"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  tls:
  - hosts:
    - myapp.example.com
    secretName: myapp-tls
  rules:
  - host: myapp.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: web-app
            port:
              number: 8080
```

### Use Case 4: Node Lifecycle Management

```bash
# CCM automatically handles node lifecycle

# Scenario 1: EC2 instance terminated (spot instance interrupted)
# 1. AWS terminates EC2 instance
# 2. Node Controller (in CCM) detects instance gone (via AWS API)
# 3. Node Controller marks node as NotReady
# 4. After grace period, node deleted from cluster
# 5. Pods rescheduled by scheduler to other nodes

# Scenario 2: New node joins cluster
# 1. New EC2 instance launched (via Auto Scaling Group)
# 2. kubelet starts and registers with API server
# 3. Node Controller (in CCM) enriches node with AWS metadata:
#    - Adds region/zone labels
#    - Adds instance type label
#    - Sets provider ID
# 4. Node becomes Ready and schedulable

# Check node provider ID
kubectl get nodes -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.providerID}{"\n"}{end}'

# Output:
# ip-10-0-1-100    aws:///us-east-1a/i-0123456789abcdef0
# ip-10-0-2-200    aws:///us-east-1b/i-0fedcba9876543210
```

### Use Case 5: Route Configuration for Pod Network

```yaml
# CCM configures cloud routes for pod CIDR ranges

# AWS example: VPC route table entries
# Created automatically by Route Controller

# Check node pod CIDRs
kubectl get nodes -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.podCIDR}{"\n"}{end}'

# Output:
# node-1    10.244.0.0/24
# node-2    10.244.1.0/24
# node-3    10.244.2.0/24

# CCM creates routes in AWS VPC:
# Destination          Target
# 10.244.0.0/24   →   ENI of node-1
# 10.244.1.0/24   →   ENI of node-2
# 10.244.2.0/24   →   ENI of node-3

# This enables direct pod-to-pod communication across nodes
```

**AWS Route Table (created by CCM):**
```bash
# View routes created by CCM
aws ec2 describe-route-tables \
  --filters "Name=tag:kubernetes.io/cluster/my-cluster,Values=owned" \
  --query 'RouteTables[*].Routes[?GatewayId==null]'

# Output:
# {
#   "DestinationCidrBlock": "10.244.0.0/24",
#   "InstanceId": "i-0123456789abcdef0",
#   "InstanceOwnerId": "123456789",
#   "NetworkInterfaceId": "eni-xxxxx",
#   "State": "active"
# }
```

## Monitoring and Troubleshooting

### Prometheus Metrics

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: cloud-controller-manager
  namespace: kube-system
spec:
  selector:
    matchLabels:
      k8s-app: aws-cloud-controller-manager
  endpoints:
  - port: metrics
    interval: 30s
    scheme: https
    tlsConfig:
      insecureSkipVerify: true
```

### Key Metrics

```promql
# Cloud provider API call duration
histogram_quantile(0.99, rate(cloudprovider_api_request_duration_seconds_bucket[5m]))

# Cloud provider API errors
rate(cloudprovider_api_request_errors_total[5m])

# Load balancer sync duration
histogram_quantile(0.95, rate(service_controller_loadbalancer_sync_duration_seconds_bucket[5m]))

# Route sync errors
rate(route_controller_route_sync_errors_total[5m])

# Node lifecycle operations
rate(nodelifecycle_controller_node_deletions_total[5m])
```

### Common Issues and Solutions

#### Issue 1: LoadBalancer Service Stuck in Pending

```bash
# Check service status
kubectl describe svc my-loadbalancer

# Events show:
# Error creating load balancer (will retry): failed to ensure load balancer: UnauthorizedOperation

# Solution 1: Check IAM permissions
aws iam get-role-policy \
  --role-name eks-ccm-role \
  --policy-name eks-ccm-policy

# Solution 2: Check CCM logs
kubectl logs -n kube-system -l k8s-app=aws-cloud-controller-manager

# Solution 3: Verify CCM is running
kubectl get pods -n kube-system -l k8s-app=aws-cloud-controller-manager

# Solution 4: Check service annotations
kubectl get svc my-loadbalancer -o yaml | grep -A 10 annotations
```

#### Issue 2: Nodes Not Getting Cloud Labels

```bash
# Check if CCM is running
kubectl get pods -n kube-system -l k8s-app=aws-cloud-controller-manager

# Check CCM logs for errors
kubectl logs -n kube-system aws-cloud-controller-manager-xxxxx

# Common issues:
# 1. CCM not running → Deploy CCM
# 2. IAM permissions missing → Add EC2:DescribeInstances permission
# 3. Instance tags missing → Add kubernetes.io/cluster/<name>=owned tag
# 4. Wrong cloud-provider flag → Set --cloud-provider=external in kubelet

# Manually trigger node initialization
kubectl delete node <node-name>
# Wait for kubelet to re-register
# CCM will enrich with cloud metadata
```

#### Issue 3: Route Creation Failed

```bash
# Check route controller logs
kubectl logs -n kube-system aws-cloud-controller-manager-xxxxx | grep -i route

# Common errors:
# Error: "InvalidRoute.AlreadyExists"
# Solution: Delete duplicate routes in VPC route table

# Error: "Route table not found"
# Solution: Tag route table with kubernetes.io/cluster/<name>=owned

# Error: "UnauthorizedOperation"
# Solution: Add EC2:CreateRoute, EC2:DeleteRoute permissions

# Verify route table tags
aws ec2 describe-route-tables \
  --filters "Name=tag:kubernetes.io/cluster/my-cluster,Values=owned"
```

#### Issue 4: LoadBalancer Health Checks Failing

```bash
# Check service health check configuration
kubectl get svc my-service -o yaml | grep health

# AWS NLB health check issues:
# 1. Security group blocking health check
aws ec2 describe-security-groups --group-ids sg-xxxxx

# 2. Network ACL blocking traffic
aws ec2 describe-network-acls

# 3. Incorrect health check port/protocol
kubectl annotate svc my-service \
  service.beta.kubernetes.io/aws-load-balancer-healthcheck-port="8080" \
  --overwrite

# View NLB target health
aws elbv2 describe-target-health \
  --target-group-arn arn:aws:elasticloadbalancing:...
```

## Migration from In-Tree to Out-of-Tree CCM

### Step-by-Step Migration

```bash
# ==================== Phase 1: Prepare ====================

# 1. Backup current configuration
kubectl get all --all-namespaces -o yaml > cluster-backup.yaml

# 2. Check current cloud provider setting
kubectl get cm -n kube-system kube-apiserver -o yaml | grep cloud-provider
kubectl get cm -n kube-system kube-controller-manager -o yaml | grep cloud-provider

# 3. Install CCM (without starting controllers)
kubectl apply -f aws-ccm-daemonset.yaml

# ==================== Phase 2: Update Control Plane ====================

# 4. Update kube-apiserver flags
# Edit /etc/kubernetes/manifests/kube-apiserver.yaml
# Change: --cloud-provider=aws
# To: --cloud-provider=external

# 5. Update kube-controller-manager flags
# Edit /etc/kubernetes/manifests/kube-controller-manager.yaml
# Change: --cloud-provider=aws
# To: --cloud-provider=external

# 6. Restart control plane components
kubectl delete pod -n kube-system kube-apiserver-master1
kubectl delete pod -n kube-system kube-controller-manager-master1

# ==================== Phase 3: Update Worker Nodes ====================

# 7. For each worker node, update kubelet
# Edit /var/lib/kubelet/config.yaml
# Add: cloudProvider: external

# Or edit systemd service:
# /etc/systemd/system/kubelet.service.d/10-kubeadm.conf
# Add: --cloud-provider=external

# Restart kubelet
sudo systemctl daemon-reload
sudo systemctl restart kubelet

# 8. Verify node re-registration
kubectl get nodes -w

# ==================== Phase 4: Enable CCM Controllers ====================

# 9. Enable CCM controllers
kubectl patch ds -n kube-system aws-cloud-controller-manager \
  -p '{"spec":{"template":{"spec":{"containers":[{"name":"aws-cloud-controller-manager","args":["--cloud-provider=aws","--controllers=node,service,route","--leader-elect=true"]}]}}}}'

# 10. Verify CCM is running and leading
kubectl logs -n kube-system -l k8s-app=aws-cloud-controller-manager

# ==================== Phase 5: Verification ====================

# 11. Verify node labels
kubectl get nodes -L topology.kubernetes.io/region,topology.kubernetes.io/zone

# 12. Test LoadBalancer service
kubectl create deployment nginx --image=nginx
kubectl expose deployment nginx --type=LoadBalancer --port=80

# 13. Verify load balancer created
kubectl get svc nginx -w
aws elbv2 describe-load-balancers

# 14. Cleanup test resources
kubectl delete deployment nginx
kubectl delete svc nginx
```

## References

- [Cloud Controller Manager Concepts](https://kubernetes.io/docs/concepts/architecture/cloud-controller/)
- [AWS Cloud Provider](https://kubernetes.io/docs/concepts/cluster-administration/cloud-providers/#aws)
- [GCP Cloud Provider](https://cloud.google.com/kubernetes-engine/docs/concepts/cloud-controller-manager)
- [Azure Cloud Provider](https://cloud-provider-azure.sigs.k8s.io/)
- [Kubernetes Cloud Provider](https://github.com/kubernetes/cloud-provider)
- [Migrating to CCM](https://kubernetes.io/docs/tasks/administer-cluster/running-cloud-controller/)
