## Kubernetes Cluster Upgrades & Maintenance Guide

### Upgrade Planning and Strategy

Kubernetes follows a release cycle with minor versions every 3-4 months and patch versions as needed for security and bug fixes.

#### Version Support Policy

**Kubernetes Version Support:**
- **Latest 3 minor versions** are supported
- **N-2 support policy**: Current version (N) and two previous minor versions
- **Patch versions**: Critical security and bug fixes backported
- **End of life**: Versions older than N-2 are no longer supported

**Example Support Matrix:**
```
Supported Versions (as of K8s 1.28):
├── 1.28.x (Current)
├── 1.27.x (N-1)
└── 1.26.x (N-2)

Deprecated/EOL:
├── 1.25.x (EOL)
└── 1.24.x (EOL)
```

#### Pre-Upgrade Planning

**Version Compatibility Assessment:**

```bash
# Check current cluster version
kubectl version --short

# Check node versions
kubectl get nodes -o wide

# Check API deprecations
kubectl api-resources --verbs=list --api-group=extensions -o name
kubectl api-resources --verbs=list --api-group=apps/v1beta1 -o name

# Check for deprecated API usage
kubectl get events --all-namespaces --field-selector type=Warning

# Validate cluster health
kubectl get componentstatuses
kubectl get nodes
kubectl top nodes
```

**Backup Strategy:**

```bash
# Backup etcd
ETCDCTL_API=3 etcdctl snapshot save backup.db \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/healthcheck-client.crt \
  --key=/etc/kubernetes/pki/etcd/healthcheck-client.key

# Backup cluster configuration
kubectl get all --all-namespaces -o yaml > cluster-backup.yaml
kubectl get pv -o yaml > persistent-volumes-backup.yaml
kubectl get pvc --all-namespaces -o yaml > persistent-volume-claims-backup.yaml

# Backup important secrets and configmaps
kubectl get secrets --all-namespaces -o yaml > secrets-backup.yaml
kubectl get configmaps --all-namespaces -o yaml > configmaps-backup.yaml
```

### Control Plane Upgrade Procedures

#### kubeadm Cluster Upgrade

**Upgrade Control Plane Node:**

```bash
# On the first control plane node
# Update kubeadm
apt-get update
apt-get install -y kubeadm=1.28.1-00

# Verify kubeadm version
kubeadm version

# Plan the upgrade
kubeadm upgrade plan

# Apply the upgrade
sudo kubeadm upgrade apply v1.28.1

# Drain the node
kubectl drain cp1 --ignore-daemonsets

# Upgrade kubelet and kubectl
apt-get install -y kubelet=1.28.1-00 kubectl=1.28.1-00

# Restart kubelet
sudo systemctl daemon-reload
sudo systemctl restart kubelet

# Uncordon the node
kubectl uncordon cp1

# Verify the upgrade
kubectl get nodes
kubectl version --short
```

**Upgrade Additional Control Plane Nodes:**

```bash
# On each additional control plane node
# Update kubeadm
apt-get update
apt-get install -y kubeadm=1.28.1-00

# Upgrade the control plane
sudo kubeadm upgrade node

# Drain the node (from another control plane node)
kubectl drain cp2 --ignore-daemonsets

# Upgrade kubelet and kubectl
apt-get install -y kubelet=1.28.1-00 kubectl=1.28.1-00

# Restart services
sudo systemctl daemon-reload
sudo systemctl restart kubelet

# Uncordon the node
kubectl uncordon cp2
```

#### Manual Control Plane Component Upgrade

**Static Pod Manifests Update:**

```yaml
# /etc/kubernetes/manifests/kube-apiserver.yaml
apiVersion: v1
kind: Pod
metadata:
  name: kube-apiserver
  namespace: kube-system
spec:
  containers:
  - command:
    - kube-apiserver
    - --advertise-address=192.168.1.10
    - --allow-privileged=true
    - --authorization-mode=Node,RBAC
    - --client-ca-file=/etc/kubernetes/pki/ca.crt
    - --enable-admission-plugins=NodeRestriction
    - --enable-bootstrap-token-auth=true
    - --etcd-cafile=/etc/kubernetes/pki/etcd/ca.crt
    - --etcd-certfile=/etc/kubernetes/pki/apiserver-etcd-client.crt
    - --etcd-keyfile=/etc/kubernetes/pki/apiserver-etcd-client.key
    - --etcd-servers=https://127.0.0.1:2379
    - --kubelet-client-certificate=/etc/kubernetes/pki/apiserver-kubelet-client.crt
    - --kubelet-client-key=/etc/kubernetes/pki/apiserver-kubelet-client.key
    - --kubelet-preferred-address-types=InternalIP,ExternalIP,Hostname
    - --proxy-client-cert-file=/etc/kubernetes/pki/front-proxy-client.crt
    - --proxy-client-key-file=/etc/kubernetes/pki/front-proxy-client.key
    - --requestheader-allowed-names=front-proxy-client
    - --requestheader-client-ca-file=/etc/kubernetes/pki/front-proxy-ca.crt
    - --requestheader-extra-headers-prefix=X-Remote-Extra-
    - --requestheader-group-headers=X-Remote-Group
    - --requestheader-username-headers=X-Remote-User
    - --secure-port=6443
    - --service-account-issuer=https://kubernetes.default.svc.cluster.local
    - --service-account-key-file=/etc/kubernetes/pki/sa.pub
    - --service-account-signing-key-file=/etc/kubernetes/pki/sa.key
    - --service-cluster-ip-range=10.96.0.0/12
    - --tls-cert-file=/etc/kubernetes/pki/apiserver.crt
    - --tls-private-key-file=/etc/kubernetes/pki/apiserver.key
    image: registry.k8s.io/kube-apiserver:v1.28.1
    imagePullPolicy: IfNotPresent
    name: kube-apiserver
    resources:
      requests:
        cpu: 250m
    volumeMounts:
    - mountPath: /etc/ssl/certs
      name: ca-certs
      readOnly: true
    - mountPath: /etc/ca-certificates
      name: etc-ca-certificates
      readOnly: true
    - mountPath: /etc/kubernetes/pki
      name: k8s-certs
      readOnly: true
    - mountPath: /usr/local/share/ca-certificates
      name: usr-local-share-ca-certificates
      readOnly: true
    - mountPath: /usr/share/ca-certificates
      name: usr-share-ca-certificates
      readOnly: true
  hostNetwork: true
  priorityClassName: system-node-critical
  securityContext:
    seccompProfile:
      type: RuntimeDefault
  volumes:
  - hostPath:
      path: /etc/ssl/certs
      type: DirectoryOrCreate
    name: ca-certs
  - hostPath:
      path: /etc/ca-certificates
      type: DirectoryOrCreate
    name: etc-ca-certificates
  - hostPath:
      path: /etc/kubernetes/pki
      type: DirectoryOrCreate
    name: k8s-certs
  - hostPath:
      path: /usr/local/share/ca-certificates
      type: DirectoryOrCreate
    name: usr-local-share-ca-certificates
  - hostPath:
      path: /usr/share/ca-certificates
      type: DirectoryOrCreate
    name: usr-share-ca-certificates
```

### Worker Node Upgrade Procedures

#### Rolling Node Upgrades

**Automated Rolling Upgrade Script:**

```bash
#!/bin/bash
# rolling-upgrade.sh

NODES=$(kubectl get nodes -o jsonpath='{.items[*].metadata.name}')
NEW_VERSION="1.28.1-00"

for node in $NODES; do
    echo "Upgrading node: $node"
    
    # Check if node is a control plane node
    if kubectl get node $node -o jsonpath='{.metadata.labels.node-role\.kubernetes\.io/control-plane}' >/dev/null 2>&1; then
        echo "Skipping control plane node: $node"
        continue
    fi
    
    # Drain the node
    echo "Draining node: $node"
    kubectl drain $node --ignore-daemonsets --delete-emptydir-data --timeout=300s
    
    # SSH to node and upgrade
    echo "Upgrading packages on node: $node"
    ssh $node << EOF
        # Update package cache
        sudo apt-get update
        
        # Upgrade kubeadm
        sudo apt-get install -y kubeadm=$NEW_VERSION
        
        # Upgrade node configuration
        sudo kubeadm upgrade node
        
        # Upgrade kubelet and kubectl
        sudo apt-get install -y kubelet=$NEW_VERSION kubectl=$NEW_VERSION
        
        # Restart kubelet
        sudo systemctl daemon-reload
        sudo systemctl restart kubelet
EOF
    
    # Wait for node to be ready
    echo "Waiting for node to be ready: $node"
    kubectl wait --for=condition=Ready node/$node --timeout=300s
    
    # Uncordon the node
    echo "Uncordoning node: $node"
    kubectl uncordon $node
    
    # Wait for pods to be scheduled
    sleep 30
    
    echo "Node $node upgrade completed"
done

echo "All nodes upgraded successfully"
```

#### Node Pool Upgrade (Managed Clusters)

**EKS Node Group Upgrade:**

```hcl
# Update Terraform configuration
resource "aws_eks_node_group" "main" {
  cluster_name    = aws_eks_cluster.main.name
  node_group_name = "main-nodes"
  node_role_arn   = aws_iam_role.eks_nodes.arn
  subnet_ids      = var.private_subnet_ids

  # Update AMI version
  ami_type = "AL2_x86_64"
  version  = "1.28"

  instance_types = ["m5.large"]
  capacity_type  = "ON_DEMAND"

  scaling_config {
    desired_size = 3
    max_size     = 6
    min_size     = 1
  }

  update_config {
    max_unavailable_percentage = 25
  }

  # Force replacement if needed
  force_update_version = true

  depends_on = [
    aws_iam_role_policy_attachment.eks_worker_node_policy,
    aws_iam_role_policy_attachment.eks_cni_policy,
    aws_iam_role_policy_attachment.eks_container_registry_policy,
  ]
}
```

**AKS Node Pool Upgrade:**

```bash
# Upgrade AKS cluster control plane
az aks upgrade \
    --resource-group myResourceGroup \
    --name myAKSCluster \
    --kubernetes-version 1.28.1

# Upgrade specific node pool
az aks nodepool upgrade \
    --resource-group myResourceGroup \
    --cluster-name myAKSCluster \
    --name mynodepool \
    --kubernetes-version 1.28.1

# Check upgrade progress
az aks show \
    --resource-group myResourceGroup \
    --name myAKSCluster \
    --query "agentPoolProfiles[0].orchestratorVersion"
```

**GKE Node Pool Upgrade:**

```bash
# Upgrade cluster master
gcloud container clusters upgrade my-cluster \
    --zone=us-central1-a \
    --master \
    --cluster-version=1.28.1-gke.1

# Upgrade node pool
gcloud container clusters upgrade my-cluster \
    --zone=us-central1-a \
    --node-pool=default-pool \
    --cluster-version=1.28.1-gke.1

# Check upgrade status
gcloud container operations list \
    --filter="TYPE=UPGRADE_MASTER OR TYPE=UPGRADE_NODES"
```

### Application and Addon Upgrades

#### CNI Plugin Upgrades

**Cilium Upgrade:**

```bash
# Check current version
cilium version

# Upgrade Cilium using Helm
helm repo update
helm upgrade cilium cilium/cilium \
    --version 1.14.1 \
    --namespace kube-system \
    --reuse-values

# Verify upgrade
cilium status
kubectl get pods -n kube-system -l k8s-app=cilium
```

**Calico Upgrade:**

```yaml
# Update Calico manifest
kubectl apply -f https://raw.githubusercontent.com/projectcalico/calico/v3.26.1/manifests/calico.yaml

# Wait for upgrade to complete
kubectl rollout status daemonset/calico-node -n kube-system
kubectl rollout status deployment/calico-kube-controllers -n kube-system

# Verify upgrade
kubectl get pods -n kube-system -l k8s-app=calico-node
```

#### DNS and Service Mesh Upgrades

**CoreDNS Upgrade:**

```bash
# Check current CoreDNS version
kubectl get deployment coredns -n kube-system -o jsonpath='{.spec.template.spec.containers[0].image}'

# Update CoreDNS (usually handled by kubeadm)
kubectl set image deployment/coredns coredns=registry.k8s.io/coredns/coredns:v1.10.1 -n kube-system

# Verify upgrade
kubectl rollout status deployment/coredns -n kube-system
```

**Istio Upgrade:**

```bash
# Download new Istio version
curl -L https://istio.io/downloadIstio | ISTIO_VERSION=1.18.1 TARGET_ARCH=x86_64 sh -

# Install new version alongside current
istioctl install --set values.pilot.env.PILOT_ENABLE_CROSS_CLUSTER_WORKLOAD_ENTRY=true --set revision=1-18-1

# Update namespace labels for canary upgrade
kubectl label namespace production istio.io/rev=1-18-1 --overwrite

# Restart pods to use new version
kubectl rollout restart deployment -n production

# Verify upgrade
istioctl proxy-status

# Remove old version after verification
istioctl x uninstall --revision=1-17-2
```

### Cluster Configuration Updates

#### API Server Configuration

**Feature Gate Updates:**

```yaml
# Update API server manifest with new feature gates
apiVersion: v1
kind: Pod
metadata:
  name: kube-apiserver
  namespace: kube-system
spec:
  containers:
  - name: kube-apiserver
    image: registry.k8s.io/kube-apiserver:v1.28.1
    command:
    - kube-apiserver
    - --feature-gates=RemoveSelfLink=false,WatchBookmark=true
    - --runtime-config=api/v1=true
    # Other flags...
```

#### Admission Controller Updates

**Pod Security Standards Migration:**

```yaml
# Namespace configuration for Pod Security Standards
apiVersion: v1
kind: Namespace
metadata:
  name: production
  labels:
    # Enforce restricted profile
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/enforce-version: v1.28
    
    # Audit and warn with baseline
    pod-security.kubernetes.io/audit: baseline
    pod-security.kubernetes.io/audit-version: v1.28
    pod-security.kubernetes.io/warn: baseline
    pod-security.kubernetes.io/warn-version: v1.28
```

### Rollback Procedures

#### Control Plane Rollback

**kubeadm Rollback Process:**

```bash
# Stop kubelet on all control plane nodes
sudo systemctl stop kubelet

# Restore etcd from backup
ETCDCTL_API=3 etcdctl snapshot restore backup.db \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/healthcheck-client.crt \
  --key=/etc/kubernetes/pki/etcd/healthcheck-client.key \
  --data-dir=/var/lib/etcd

# Downgrade kubeadm, kubelet, and kubectl
apt-get install -y kubeadm=1.27.5-00 kubelet=1.27.5-00 kubectl=1.27.5-00

# Update static pod manifests to previous versions
# Edit /etc/kubernetes/manifests/kube-apiserver.yaml
# Edit /etc/kubernetes/manifests/kube-controller-manager.yaml  
# Edit /etc/kubernetes/manifests/kube-scheduler.yaml

# Start kubelet
sudo systemctl start kubelet

# Verify rollback
kubectl version --short
kubectl get nodes
```

#### Application Rollback

**Deployment Rollback:**

```bash
# Check rollout history
kubectl rollout history deployment/web-app

# Rollback to previous version
kubectl rollout undo deployment/web-app

# Rollback to specific revision
kubectl rollout undo deployment/web-app --to-revision=2

# Monitor rollback progress
kubectl rollout status deployment/web-app
```

### Upgrade Validation and Testing

#### Post-Upgrade Validation

**Cluster Health Validation:**

```bash
#!/bin/bash
# post-upgrade-validation.sh

echo "=== Cluster Health Validation ==="

# Check node status
echo "Checking node status..."
kubectl get nodes
if [ $? -ne 0 ]; then
    echo "ERROR: Node status check failed"
    exit 1
fi

# Check system pods
echo "Checking system pods..."
kubectl get pods -n kube-system
if [ $? -ne 0 ]; then
    echo "ERROR: System pods check failed"
    exit 1
fi

# Check cluster version
echo "Checking cluster version..."
kubectl version --short

# Check API server health
echo "Checking API server health..."
kubectl get --raw='/readyz?verbose'
if [ $? -ne 0 ]; then
    echo "ERROR: API server health check failed"
    exit 1
fi

# Check cluster info
echo "Checking cluster info..."
kubectl cluster-info
if [ $? -ne 0 ]; then
    echo "ERROR: Cluster info check failed"
    exit 1
fi

# Test pod creation
echo "Testing pod creation..."
kubectl run test-pod --image=nginx:alpine --rm -it --restart=Never -- echo "Test successful"
if [ $? -ne 0 ]; then
    echo "ERROR: Pod creation test failed"
    exit 1
fi

# Check networking
echo "Testing networking..."
kubectl run network-test --image=busybox --rm -it --restart=Never -- nslookup kubernetes.default
if [ $? -ne 0 ]; then
    echo "ERROR: Networking test failed"
    exit 1
fi

echo "=== All validation checks passed ==="
```

#### Application Testing

**Smoke Test Suite:**

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: smoke-test-config
data:
  test.sh: |
    #!/bin/bash
    
    # Test database connectivity
    echo "Testing database connectivity..."
    curl -f http://database-service:5432/health || exit 1
    
    # Test API endpoints
    echo "Testing API endpoints..."
    curl -f http://api-service:8080/health || exit 1
    curl -f http://api-service:8080/ready || exit 1
    
    # Test external dependencies
    echo "Testing external dependencies..."
    curl -f https://api.external-service.com/health || exit 1
    
    echo "All smoke tests passed"
---
apiVersion: batch/v1
kind: Job
metadata:
  name: post-upgrade-smoke-test
spec:
  template:
    spec:
      containers:
      - name: smoke-test
        image: curlimages/curl:latest
        command: ["/bin/sh"]
        args: ["/scripts/test.sh"]
        volumeMounts:
        - name: test-scripts
          mountPath: /scripts
      volumes:
      - name: test-scripts
        configMap:
          name: smoke-test-config
          defaultMode: 0755
      restartPolicy: Never
```

### Upgrade Automation and CI/CD

#### GitOps-Based Upgrades

**ArgoCD Application for Cluster Upgrades:**

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: cluster-upgrade
  namespace: argocd
spec:
  project: infrastructure
  source:
    repoURL: https://github.com/company/k8s-cluster-config
    targetRevision: HEAD
    path: cluster-upgrades
    helm:
      values: |
        kubernetesVersion: "1.28.1"
        nodeGroupVersion: "1.28.1-20230901"
        upgradeStrategy: "rolling"
        maxUnavailable: "25%"
  destination:
    server: https://kubernetes.default.svc
    namespace: kube-system
  syncPolicy:
    automated:
      prune: false
      selfHeal: false
    syncOptions:
    - CreateNamespace=false
  ignoreDifferences:
  - group: ""
    kind: Node
    jsonPointers:
    - /status
```

#### Terraform-Based Cluster Upgrades

**Automated EKS Upgrade:**

```hcl
# versions.tf
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# variables.tf
variable "cluster_version" {
  description = "Kubernetes version for the cluster"
  type        = string
  default     = "1.28"
}

variable "node_group_version" {
  description = "AMI version for node groups"
  type        = string
  default     = "1.28.1-20230901"
}

# main.tf with versioned upgrades
resource "aws_eks_cluster" "main" {
  name     = var.cluster_name
  role_arn = aws_iam_role.eks_cluster.arn
  version  = var.cluster_version

  # Enable gradual upgrade
  upgrade_policy {
    support_type = "STANDARD"
  }

  vpc_config {
    subnet_ids = var.subnet_ids
  }
}

# Gradual node group upgrade
resource "aws_eks_node_group" "blue" {
  count           = var.upgrade_in_progress ? 1 : 0
  cluster_name    = aws_eks_cluster.main.name
  node_group_name = "${var.cluster_name}-blue"
  node_role_arn   = aws_iam_role.eks_nodes.arn
  subnet_ids      = var.private_subnet_ids
  
  version = var.node_group_version
  
  scaling_config {
    desired_size = var.node_count
    max_size     = var.node_count * 2
    min_size     = 1
  }
  
  lifecycle {
    create_before_destroy = true
  }
}
```

### Maintenance Windows and Scheduling

#### Planned Maintenance Strategy

**Maintenance Window Configuration:**

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: maintenance-schedule
  namespace: kube-system
data:
  maintenance.yaml: |
    schedule:
      - window: "weekly-maintenance"
        day: "saturday"
        time: "02:00"
        duration: "4h"
        timezone: "UTC"
        actions:
          - type: "node-upgrade"
            max_unavailable: "25%"
          - type: "addon-upgrade"
            components: ["coredns", "kube-proxy"]
      - window: "security-patches"
        day: "tuesday"
        time: "01:00"
        duration: "2h"
        timezone: "UTC"
        actions:
          - type: "security-update"
            auto_approve: true
```

#### Cluster Drain Strategies

**Custom Drain Controller:**

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: node-drain-controller
spec:
  template:
    spec:
      serviceAccountName: node-drain-sa
      containers:
      - name: drain-controller
        image: kubectl:latest
        command:
        - /bin/bash
        - -c
        - |
          # Intelligent draining with application awareness
          for node in $(kubectl get nodes -l maintenance=scheduled -o name); do
            echo "Draining $node with graceful shutdown"
            
            # Check for stateful workloads
            kubectl get pods --all-namespaces --field-selector spec.nodeName=${node#node/} \
              -o jsonpath='{.items[?(@.metadata.ownerReferences[0].kind=="StatefulSet")].metadata.name}'
            
            # Gradual drain with delays
            kubectl drain $node \
              --ignore-daemonsets \
              --delete-emptydir-data \
              --force \
              --grace-period=300 \
              --timeout=600s
              
            # Wait for pods to reschedule
            sleep 60
          done
      restartPolicy: Never
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: node-drain-sa
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: node-drain-role
rules:
- apiGroups: [""]
  resources: ["nodes"]
  verbs: ["get", "list", "patch", "update"]
- apiGroups: [""]
  resources: ["pods"]
  verbs: ["get", "list", "delete"]
- apiGroups: [""]
  resources: ["pods/eviction"]
  verbs: ["create"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: node-drain-binding
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: node-drain-role
subjects:
- kind: ServiceAccount
  name: node-drain-sa
  namespace: default
```

### DevOps Best Practices for Upgrades

#### Upgrade Readiness Checklist

**✅ Pre-Upgrade Preparation:**
- Review Kubernetes changelog and breaking changes
- Test upgrade in staging environment first
- Backup etcd and cluster configuration
- Document current cluster state and versions
- Plan rollback strategy and procedures
- Schedule maintenance window
- Notify stakeholders and teams

**✅ During Upgrade:**
- Monitor cluster health continuously
- Follow rolling upgrade practices
- Validate each step before proceeding
- Maintain communication with team
- Document any issues or deviations
- Keep rollback plan readily available

**✅ Post-Upgrade Validation:**
- Verify all nodes are healthy and ready
- Test application functionality
- Check system and application logs
- Validate networking and DNS resolution
- Confirm monitoring and alerting work
- Update documentation and runbooks
- Conduct post-upgrade retrospective

#### Upgrade Safety Measures

**Automated Safety Checks:**

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: upgrade-safety-checks
data:
  safety-check.sh: |
    #!/bin/bash
    
    # Function to check cluster health
    check_cluster_health() {
        echo "Checking cluster health..."
        
        # Check node readiness
        NOT_READY=$(kubectl get nodes --no-headers | grep -v Ready | wc -l)
        if [ "$NOT_READY" -gt 0 ]; then
            echo "ERROR: $NOT_READY nodes are not ready"
            return 1
        fi
        
        # Check system pods
        FAILING_PODS=$(kubectl get pods -n kube-system --no-headers | grep -v Running | grep -v Completed | wc -l)
        if [ "$FAILING_PODS" -gt 0 ]; then
            echo "ERROR: $FAILING_PODS system pods are not running"
            return 1
        fi
        
        # Check API server responsiveness
        if ! kubectl get --raw='/readyz' >/dev/null 2>&1; then
            echo "ERROR: API server health check failed"
            return 1
        fi
        
        echo "Cluster health check passed"
        return 0
    }
    
    # Function to check application health
    check_application_health() {
        echo "Checking application health..."
        
        # Check deployment status
        FAILED_DEPLOYMENTS=$(kubectl get deployments --all-namespaces -o json | \
            jq -r '.items[] | select(.status.replicas != .status.readyReplicas) | .metadata.name' | wc -l)
        
        if [ "$FAILED_DEPLOYMENTS" -gt 0 ]; then
            echo "WARNING: $FAILED_DEPLOYMENTS deployments have unready replicas"
        fi
        
        echo "Application health check completed"
        return 0
    }
    
    # Main execution
    check_cluster_health || exit 1
    check_application_health || exit 1
    
    echo "All safety checks passed"
```

#### Upgrade Communication Template

**Upgrade Notification Template:**

```markdown
# Kubernetes Cluster Upgrade Notification

## Upgrade Details
- **Cluster**: Production EKS Cluster
- **Current Version**: 1.27.5
- **Target Version**: 1.28.1
- **Upgrade Date**: 2023-09-15
- **Maintenance Window**: 02:00-06:00 UTC

## Expected Impact
- Brief service interruptions during node upgrades
- Estimated downtime: < 5 minutes per service
- Rolling upgrade to minimize impact

## Rollback Plan
- Automated rollback triggers if health checks fail
- Manual rollback procedures documented and tested
- Expected rollback time: 30 minutes

## Contact Information
- **Primary**: DevOps Team (devops@company.com)
- **Secondary**: SRE Team (sre@company.com)
- **Escalation**: Engineering Manager

## Status Updates
Updates will be provided every 30 minutes during the maintenance window.
```