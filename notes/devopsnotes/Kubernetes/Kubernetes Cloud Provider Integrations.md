## Cloud Provider Integrations Comprehensive Guide

### Amazon EKS (Elastic Kubernetes Service)

EKS is AWS's managed Kubernetes service that runs upstream Kubernetes and is certified Kubernetes conformant.

#### EKS Cluster Creation and Configuration

**EKS Cluster with Terraform:**

```hcl
# eks-cluster.tf
resource "aws_eks_cluster" "main" {
  name     = var.cluster_name
  role_arn = aws_iam_role.eks_cluster.arn
  version  = "1.28"

  vpc_config {
    subnet_ids              = var.subnet_ids
    endpoint_private_access = true
    endpoint_public_access  = true
    public_access_cidrs     = ["0.0.0.0/0"]
    security_group_ids      = [aws_security_group.eks_cluster.id]
  }

  encryption_config {
    provider {
      key_arn = aws_kms_key.eks.arn
    }
    resources = ["secrets"]
  }

  enabled_cluster_log_types = [
    "api",
    "audit",
    "authenticator",
    "controllerManager",
    "scheduler"
  ]

  depends_on = [
    aws_iam_role_policy_attachment.eks_cluster_policy,
    aws_iam_role_policy_attachment.eks_vpc_resource_controller,
  ]

  tags = var.tags
}

resource "aws_eks_node_group" "main" {
  cluster_name    = aws_eks_cluster.main.name
  node_group_name = "${var.cluster_name}-nodes"
  node_role_arn   = aws_iam_role.eks_nodes.arn
  subnet_ids      = var.private_subnet_ids

  instance_types = ["m5.large", "m5.xlarge"]
  capacity_type  = "ON_DEMAND"

  scaling_config {
    desired_size = 3
    max_size     = 10
    min_size     = 1
  }

  update_config {
    max_unavailable_percentage = 25
  }

  ami_type               = "AL2_x86_64"
  disk_size             = 100
  force_update_version  = false

  labels = {
    role = "worker"
    env  = var.environment
  }

  taints {
    key    = "example-taint"
    value  = "true"
    effect = "NO_SCHEDULE"
  }

  depends_on = [
    aws_iam_role_policy_attachment.eks_worker_node_policy,
    aws_iam_role_policy_attachment.eks_cni_policy,
    aws_iam_role_policy_attachment.eks_container_registry_policy,
  ]

  tags = var.tags
}

# Fargate Profile
resource "aws_eks_fargate_profile" "main" {
  cluster_name           = aws_eks_cluster.main.name
  fargate_profile_name   = "${var.cluster_name}-fargate"
  pod_execution_role_arn = aws_iam_role.fargate_pod.arn
  subnet_ids             = var.private_subnet_ids

  selector {
    namespace = "fargate"
    labels = {
      compute-type = "fargate"
    }
  }

  selector {
    namespace = "kube-system"
    labels = {
      k8s-app = "coredns"
    }
  }

  depends_on = [
    aws_iam_role_policy_attachment.fargate_pod_execution_role_policy
  ]

  tags = var.tags
}
```

**EKS IAM Roles and Policies:**

```hcl
# iam.tf
resource "aws_iam_role" "eks_cluster" {
  name = "${var.cluster_name}-cluster-role"

  assume_role_policy = jsonencode({
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "eks.amazonaws.com"
      }
    }]
    Version = "2012-10-17"
  })
}

resource "aws_iam_role_policy_attachment" "eks_cluster_policy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSClusterPolicy"
  role       = aws_iam_role.eks_cluster.name
}

resource "aws_iam_role_policy_attachment" "eks_vpc_resource_controller" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSVPCResourceController"
  role       = aws_iam_role.eks_cluster.name
}

# EKS Node Group IAM Role
resource "aws_iam_role" "eks_nodes" {
  name = "${var.cluster_name}-node-group-role"

  assume_role_policy = jsonencode({
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "ec2.amazonaws.com"
      }
    }]
    Version = "2012-10-17"
  })
}

resource "aws_iam_role_policy_attachment" "eks_worker_node_policy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy"
  role       = aws_iam_role.eks_nodes.name
}

resource "aws_iam_role_policy_attachment" "eks_cni_policy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy"
  role       = aws_iam_role.eks_nodes.name
}

resource "aws_iam_role_policy_attachment" "eks_container_registry_policy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
  role       = aws_iam_role.eks_nodes.name
}

# IRSA (IAM Roles for Service Accounts)
resource "aws_iam_openid_connect_provider" "eks" {
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = [data.tls_certificate.eks.certificates[0].sha1_fingerprint]
  url             = aws_eks_cluster.main.identity[0].oidc[0].issuer

  tags = var.tags
}

data "tls_certificate" "eks" {
  url = aws_eks_cluster.main.identity[0].oidc[0].issuer
}
```

#### EKS-Specific Configurations

**AWS Load Balancer Controller:**

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: aws-load-balancer-controller
  namespace: kube-system
  annotations:
    eks.amazonaws.com/role-arn: arn:aws:iam::ACCOUNT-ID:role/AmazonEKSLoadBalancerControllerRole
---
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
        image: amazon/aws-load-balancer-controller:v2.4.7
        args:
        - --cluster-name=my-cluster
        - --ingress-class=alb
        resources:
          limits:
            cpu: 200m
            memory: 500Mi
          requests:
            cpu: 100m
            memory: 200Mi
        securityContext:
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true
          runAsNonRoot: true
```

**Application Load Balancer Ingress:**

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: web-app-alb
  annotations:
    kubernetes.io/ingress.class: alb
    alb.ingress.kubernetes.io/scheme: internet-facing
    alb.ingress.kubernetes.io/target-type: ip
    alb.ingress.kubernetes.io/certificate-arn: arn:aws:acm:region:account:certificate/cert-id
    alb.ingress.kubernetes.io/ssl-policy: ELBSecurityPolicy-TLS-1-2-2017-01
    alb.ingress.kubernetes.io/backend-protocol: HTTP
    alb.ingress.kubernetes.io/healthcheck-path: /health
    alb.ingress.kubernetes.io/healthcheck-interval-seconds: '30'
    alb.ingress.kubernetes.io/healthy-threshold-count: '2'
    alb.ingress.kubernetes.io/unhealthy-threshold-count: '5'
    alb.ingress.kubernetes.io/success-codes: '200'
spec:
  rules:
  - host: app.company.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: web-app-service
            port:
              number: 80
```

**EBS CSI Driver Configuration:**

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: ebs-gp3
  annotations:
    storageclass.kubernetes.io/is-default-class: "true"
provisioner: ebs.csi.aws.com
parameters:
  type: gp3
  iops: "3000"
  throughput: "125"
  encrypted: "true"
volumeBindingMode: WaitForFirstConsumer
allowVolumeExpansion: true
reclaimPolicy: Delete
```

**EFS CSI Driver for Shared Storage:**

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: efs-sc
provisioner: efs.csi.aws.com
parameters:
  provisioningMode: efs-ap
  fileSystemId: fs-0123456789abcdef0
  directoryPerms: "0755"
  basePath: "/dynamic_provisioning"
```

#### EKS Security Best Practices

**Pod Security Standards:**

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: production
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/warn: restricted
```

**Network Policy for EKS:**

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-all-ingress
  namespace: production
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
  egress:
  - to: []
    ports:
    - protocol: TCP
      port: 53
    - protocol: UDP
      port: 53
  - to:
    - namespaceSelector:
        matchLabels:
          name: kube-system
```

### Azure AKS (Azure Kubernetes Service)

AKS is Microsoft Azure's managed Kubernetes service with deep integration into Azure ecosystem.

#### AKS Cluster Creation with Terraform

**AKS Cluster Configuration:**

```hcl
# aks-cluster.tf
resource "azurerm_kubernetes_cluster" "main" {
  name                = var.cluster_name
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  dns_prefix          = var.cluster_name
  kubernetes_version  = "1.28.0"

  default_node_pool {
    name                = "default"
    node_count          = 3
    min_count          = 1
    max_count          = 10
    enable_auto_scaling = true
    vm_size            = "Standard_D2s_v3"
    os_disk_size_gb    = 100
    os_disk_type       = "Managed"
    vnet_subnet_id     = azurerm_subnet.aks.id
    
    upgrade_settings {
      max_surge = "10%"
    }

    node_labels = {
      "nodepool-type" = "system"
      "environment"   = var.environment
    }

    node_taints = []
  }

  # Additional node pools
  additional_node_pools = {
    user = {
      vm_size             = "Standard_D4s_v3"
      node_count          = 2
      min_count          = 1
      max_count          = 5
      enable_auto_scaling = true
      node_labels = {
        "nodepool-type" = "user"
      }
      node_taints = [
        "workload=user:NoSchedule"
      ]
    }
  }

  identity {
    type = "SystemAssigned"
  }

  network_profile {
    network_plugin    = "azure"
    network_policy    = "azure"
    load_balancer_sku = "standard"
    service_cidr      = "10.0.16.0/24"
    dns_service_ip    = "10.0.16.10"
  }

  addon_profile {
    azure_policy {
      enabled = true
    }
    
    oms_agent {
      enabled                    = true
      log_analytics_workspace_id = azurerm_log_analytics_workspace.main.id
    }

    ingress_application_gateway {
      enabled    = true
      gateway_id = azurerm_application_gateway.main.id
    }
  }

  role_based_access_control {
    enabled = true

    azure_active_directory {
      managed                = true
      admin_group_object_ids = [var.aks_admin_group_id]
      azure_rbac_enabled     = true
    }
  }

  private_cluster_enabled = true

  tags = var.tags
}

# Additional Node Pool
resource "azurerm_kubernetes_cluster_node_pool" "user" {
  name                  = "user"
  kubernetes_cluster_id = azurerm_kubernetes_cluster.main.id
  vm_size              = "Standard_D4s_v3"
  node_count           = 2
  min_count           = 1
  max_count           = 5
  enable_auto_scaling  = true
  vnet_subnet_id       = azurerm_subnet.aks.id

  node_labels = {
    "nodepool-type" = "user"
    "workload"      = "applications"
  }

  node_taints = [
    "workload=user:NoSchedule"
  ]

  tags = var.tags
}
```

#### AKS-Specific Integrations

**Azure Application Gateway Ingress Controller:**

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: web-app-ingress
  annotations:
    kubernetes.io/ingress.class: azure/application-gateway
    appgw.ingress.kubernetes.io/ssl-redirect: "true"
    appgw.ingress.kubernetes.io/connection-draining: "true"
    appgw.ingress.kubernetes.io/connection-draining-timeout: "30"
    appgw.ingress.kubernetes.io/cookie-based-affinity: "true"
    appgw.ingress.kubernetes.io/backend-path-prefix: "/"
spec:
  tls:
  - hosts:
    - app.company.com
    secretName: app-tls-secret
  rules:
  - host: app.company.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: web-app-service
            port:
              number: 80
```

**Azure Disk Storage Class:**

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: managed-premium-retain
provisioner: disk.csi.azure.com
parameters:
  storageaccounttype: Premium_LRS
  kind: managed
  cachingmode: ReadOnly
reclaimPolicy: Retain
allowVolumeExpansion: true
volumeBindingMode: WaitForFirstConsumer
```

**Azure Files Storage Class:**

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: azure-file-premium
provisioner: file.csi.azure.com
parameters:
  storageAccount: mystorageaccount
  resourceGroup: myResourceGroup
  shareName: myshare
  protocol: nfs
mountOptions:
  - dir_mode=0755
  - file_mode=0755
  - uid=0
  - gid=0
  - mfsymlinks
  - cache=strict
  - nosharesock
allowVolumeExpansion: true
```

#### AKS Workload Identity

**Workload Identity Setup:**

```bash
# Enable workload identity on cluster
az aks update \
  --resource-group myResourceGroup \
  --name myAKSCluster \
  --enable-workload-identity \
  --enable-oidc-issuer

# Create managed identity
az identity create \
  --name myWorkloadIdentity \
  --resource-group myResourceGroup \
  --location eastus

# Get the identity details
export USER_ASSIGNED_CLIENT_ID="$(az identity show --resource-group myResourceGroup --name myWorkloadIdentity --query 'clientId' -otsv)"
export IDENTITY_TENANT=$(az aks show --name myAKSCluster --resource-group myResourceGroup --query identity.tenantId -otsv)
export OIDC_ISSUER="$(az aks show -n myAKSCluster -g myResourceGroup --query "oidcIssuerProfile.issuerUrl" -otsv)"

# Create federated identity credential
az identity federated-credential create \
  --name myFederatedIdentity \
  --identity-name myWorkloadIdentity \
  --resource-group myResourceGroup \
  --issuer ${OIDC_ISSUER} \
  --subject system:serviceaccount:default:workload-identity-sa
```

**Service Account with Workload Identity:**

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: workload-identity-sa
  namespace: default
  annotations:
    azure.workload.identity/client-id: "${USER_ASSIGNED_CLIENT_ID}"
    azure.workload.identity/tenant-id: "${IDENTITY_TENANT}"
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: workload-identity-deployment
spec:
  replicas: 1
  selector:
    matchLabels:
      app: workload-identity
  template:
    metadata:
      labels:
        app: workload-identity
        azure.workload.identity/use: "true"
    spec:
      serviceAccountName: workload-identity-sa
      containers:
      - name: app
        image: myapp:latest
        env:
        - name: AZURE_CLIENT_ID
          value: "${USER_ASSIGNED_CLIENT_ID}"
        - name: AZURE_TENANT_ID
          value: "${IDENTITY_TENANT}"
        - name: AZURE_FEDERATED_TOKEN_FILE
          value: "/var/run/secrets/azure/tokens/azure-identity-token"
```

### Google GKE (Google Kubernetes Engine)

GKE is Google Cloud's managed Kubernetes service with advanced security and operational features.

#### GKE Cluster Creation with Terraform

**GKE Autopilot Cluster:**

```hcl
# gke-autopilot.tf
resource "google_container_cluster" "autopilot" {
  name             = var.cluster_name
  location         = var.region
  project          = var.project_id
  enable_autopilot = true

  network    = google_compute_network.vpc.self_link
  subnetwork = google_compute_subnetwork.subnet.self_link

  ip_allocation_policy {
    cluster_secondary_range_name  = "pods"
    services_secondary_range_name = "services"
  }

  private_cluster_config {
    enable_private_nodes    = true
    enable_private_endpoint = false
    master_ipv4_cidr_block  = "172.16.0.0/28"
  }

  master_authorized_networks_config {
    cidr_blocks {
      cidr_block   = "10.0.0.0/8"
      display_name = "VPC"
    }
  }

  workload_identity_config {
    workload_pool = "${var.project_id}.svc.id.goog"
  }

  binary_authorization {
    evaluation_mode = "PROJECT_SINGLETON_POLICY_ENFORCE"
  }

  addons_config {
    http_load_balancing {
      disabled = false
    }
    horizontal_pod_autoscaling {
      disabled = false
    }
    network_policy_config {
      disabled = false
    }
    dns_cache_config {
      enabled = true
    }
  }

  maintenance_policy {
    recurring_window {
      start_time = "2023-01-01T09:00:00Z"
      end_time   = "2023-01-01T17:00:00Z"
      recurrence = "FREQ=WEEKLY;BYDAY=SA,SU"
    }
  }

  release_channel {
    channel = "STABLE"
  }

  deletion_protection = true
}
```

**GKE Standard Cluster:**

```hcl
# gke-standard.tf
resource "google_container_cluster" "standard" {
  name               = var.cluster_name
  location           = var.region
  project            = var.project_id
  initial_node_count = 1

  remove_default_node_pool = true

  network    = google_compute_network.vpc.self_link
  subnetwork = google_compute_subnetwork.subnet.self_link

  networking_mode = "VPC_NATIVE"
  ip_allocation_policy {
    cluster_secondary_range_name  = "pods"
    services_secondary_range_name = "services"
  }

  private_cluster_config {
    enable_private_nodes    = true
    enable_private_endpoint = false
    master_ipv4_cidr_block  = "172.16.0.0/28"
  }

  workload_identity_config {
    workload_pool = "${var.project_id}.svc.id.goog"
  }

  addons_config {
    http_load_balancing {
      disabled = false
    }
    horizontal_pod_autoscaling {
      disabled = false
    }
    network_policy_config {
      disabled = false
    }
    gcp_filestore_csi_driver_config {
      enabled = true
    }
    gce_persistent_disk_csi_driver_config {
      enabled = true
    }
  }

  cluster_autoscaling {
    enabled = true
    resource_limits {
      resource_type = "cpu"
      minimum       = 1
      maximum       = 100
    }
    resource_limits {
      resource_type = "memory"
      minimum       = 1
      maximum       = 1000
    }
  }

  binary_authorization {
    evaluation_mode = "PROJECT_SINGLETON_POLICY_ENFORCE"
  }

  enable_shielded_nodes = true
  enable_legacy_abac    = false

  master_auth {
    client_certificate_config {
      issue_client_certificate = false
    }
  }
}

resource "google_container_node_pool" "primary" {
  name       = "primary-pool"
  location   = var.region
  cluster    = google_container_cluster.standard.name
  node_count = 3

  autoscaling {
    min_node_count = 1
    max_node_count = 10
  }

  upgrade_settings {
    max_surge       = 1
    max_unavailable = 0
  }

  node_config {
    preemptible  = false
    machine_type = "e2-medium"
    disk_size_gb = 100
    disk_type    = "pd-ssd"

    service_account = google_service_account.gke_nodes.email
    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform"
    ]

    workload_metadata_config {
      mode = "GKE_METADATA"
    }

    shielded_instance_config {
      enable_secure_boot          = true
      enable_integrity_monitoring = true
    }

    labels = {
      env = var.environment
    }

    taint {
      key    = "example-taint"
      value  = "true"
      effect = "NO_SCHEDULE"
    }

    tags = ["gke-node"]
  }

  management {
    auto_repair  = true
    auto_upgrade = true
  }
}
```

#### GKE-Specific Features

**GKE Ingress with Cloud Load Balancer:**

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: web-app-ingress
  annotations:
    kubernetes.io/ingress.class: "gce"
    kubernetes.io/ingress.global-static-ip-name: "web-static-ip"
    networking.gke.io/managed-certificates: "web-ssl-cert"
    kubernetes.io/ingress.allow-http: "false"
spec:
  rules:
  - host: app.company.com
    http:
      paths:
      - path: /*
        pathType: ImplementationSpecific
        backend:
          service:
            name: web-app-service
            port:
              number: 80
---
apiVersion: networking.gke.io/v1
kind: ManagedCertificate
metadata:
  name: web-ssl-cert
spec:
  domains:
  - app.company.com
  - api.company.com
```

**GKE Persistent Disk Storage:**

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: ssd-retain
provisioner: pd.csi.storage.gke.io
parameters:
  type: pd-ssd
  zones: us-central1-a,us-central1-b
reclaimPolicy: Retain
allowVolumeExpansion: true
volumeBindingMode: WaitForFirstConsumer
```

**GKE Filestore CSI:**

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: filestore-csi
provisioner: filestore.csi.storage.gke.io
parameters:
  tier: standard
  network: projects/PROJECT_ID/global/networks/VPC_NAME
allowVolumeExpansion: true
```

#### GKE Workload Identity

**Workload Identity Configuration:**

```bash
# Enable Workload Identity on cluster
gcloud container clusters update CLUSTER_NAME \
    --workload-pool=PROJECT_ID.svc.id.goog

# Enable on node pool
gcloud container node-pools update NODEPOOL_NAME \
    --cluster=CLUSTER_NAME \
    --workload-metadata=GKE_METADATA

# Create Google Service Account
gcloud iam service-accounts create GSA_NAME

# Create Kubernetes Service Account
kubectl create serviceaccount KSA_NAME \
    --namespace NAMESPACE

# Bind Kubernetes SA to Google SA
gcloud iam service-accounts add-iam-policy-binding \
    --role roles/iam.workloadIdentityUser \
    --member "serviceAccount:PROJECT_ID.svc.id.goog[NAMESPACE/KSA_NAME]" \
    GSA_NAME@PROJECT_ID.iam.gserviceaccount.com

# Annotate Kubernetes SA
kubectl annotate serviceaccount KSA_NAME \
    --namespace NAMESPACE \
    iam.gke.io/gcp-service-account=GSA_NAME@PROJECT_ID.iam.gserviceaccount.com
```

**Using Workload Identity:**

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: workload-identity-sa
  namespace: default
  annotations:
    iam.gke.io/gcp-service-account: gsa-name@project-id.iam.gserviceaccount.com
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: workload-identity-deployment
spec:
  replicas: 1
  selector:
    matchLabels:
      app: workload-identity
  template:
    metadata:
      labels:
        app: workload-identity
    spec:
      serviceAccountName: workload-identity-sa
      containers:
      - name: app
        image: gcr.io/google-samples/hello-app:1.0
        env:
        - name: GOOGLE_APPLICATION_CREDENTIALS
          value: "/var/secrets/google/key.json"
```

### Multi-Cloud and Hybrid Configurations

#### Cross-Cloud Networking

**Istio Multi-Cluster Setup:**

```yaml
# Primary cluster configuration
apiVersion: install.istio.io/v1alpha1
kind: IstioOperator
metadata:
  name: control-plane
spec:
  values:
    pilot:
      env:
        EXTERNAL_ISTIOD: true
        ENABLE_CROSS_CLUSTER_WORKLOAD_ENTRY: true
  components:
    pilot:
      k8s:
        env:
        - name: PILOT_ENABLE_CROSS_CLUSTER_WORKLOAD_ENTRY
          value: true
        - name: PILOT_ENABLE_WORKLOAD_ENTRY_AUTOREGISTRATION
          value: true
---
# Remote cluster configuration
apiVersion: install.istio.io/v1alpha1
kind: IstioOperator
metadata:
  name: remote
spec:
  istiodRemote:
    enabled: true
  values:
    istiodRemote:
      injectionURL: https://DISCOVERY_ADDRESS:15017/inject
    pilot:
      env:
        EXTERNAL_ISTIOD: true
```

#### Cluster API for Multi-Cloud

**Cluster API Provider Configuration:**

```yaml
apiVersion: cluster.x-k8s.io/v1beta1
kind: Cluster
metadata:
  name: multi-cloud-cluster
  namespace: default
spec:
  clusterNetwork:
    pods:
      cidrBlocks: ["192.168.0.0/16"]
  infrastructureRef:
    apiVersion: infrastructure.cluster.x-k8s.io/v1beta1
    kind: AWSCluster
    name: multi-cloud-cluster
  controlPlaneRef:
    kind: KubeadmControlPlane
    apiVersion: controlplane.cluster.x-k8s.io/v1beta1
    name: multi-cloud-cluster-control-plane
---
apiVersion: infrastructure.cluster.x-k8s.io/v1beta1
kind: AWSCluster
metadata:
  name: multi-cloud-cluster
  namespace: default
spec:
  region: us-west-2
  sshKeyName: default
```

### Cost Optimization Strategies

#### Spot Instances and Preemptible Nodes

**EKS Spot Node Group:**

```hcl
resource "aws_eks_node_group" "spot" {
  cluster_name    = aws_eks_cluster.main.name
  node_group_name = "${var.cluster_name}-spot-nodes"
  node_role_arn   = aws_iam_role.eks_nodes.arn
  subnet_ids      = var.private_subnet_ids

  capacity_type   = "SPOT"
  instance_types  = ["m5.large", "m5a.large", "m4.large"]

  scaling_config {
    desired_size = 2
    max_size     = 10
    min_size     = 0
  }

  labels = {
    lifecycle = "spot"
  }

  taints {
    key    = "spot"
    value  = "true"
    effect = "NO_SCHEDULE"
  }
}
```

**GKE Preemptible Node Pool:**

```hcl
resource "google_container_node_pool" "preemptible" {
  name       = "preemptible-pool"
  location   = var.region
  cluster    = google_container_cluster.standard.name
  node_count = 2

  node_config {
    preemptible     = true
    machine_type    = "e2-medium"
    service_account = google_service_account.gke_nodes.email

    labels = {
      lifecycle = "preemptible"
    }

    taint {
      key    = "preemptible"
      value  = "true"
      effect = "NO_SCHEDULE"
    }
  }
}
```

#### Pod Tolerations for Spot/Preemptible Workloads

**Batch Workload on Spot Nodes:**

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: batch-processing-spot
spec:
  template:
    spec:
      tolerations:
      - key: "spot"
        operator: "Equal"
        value: "true"
        effect: "NoSchedule"
      - key: "preemptible"
        operator: "Equal"
        value: "true"
        effect: "NoSchedule"
      nodeSelector:
        lifecycle: spot
      containers:
      - name: batch-worker
        image: batch-processor:latest
        resources:
          requests:
            cpu: 100m
            memory: 256Mi
      restartPolicy: OnFailure
```

### Monitoring and Observability

#### Cloud-Native Monitoring Integration

**AWS CloudWatch Container Insights:**

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: cwagentconfig
  namespace: amazon-cloudwatch
data:
  cwagentconfig.json: |
    {
      "logs": {
        "metrics_collected": {
          "kubernetes": {
            "cluster_name": "${CLUSTER_NAME}",
            "metrics_collection_interval": 60
          }
        },
        "force_flush_interval": 5
      }
    }
---
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: cloudwatch-agent
  namespace: amazon-cloudwatch
spec:
  selector:
    matchLabels:
      name: cloudwatch-agent
  template:
    metadata:
      labels:
        name: cloudwatch-agent
    spec:
      serviceAccountName: cloudwatch-agent
      containers:
      - name: cloudwatch-agent
        image: amazon/cloudwatch-agent:1.247352.0b251814
        resources:
          limits:
            cpu: 200m
            memory: 200Mi
          requests:
            cpu: 200m
            memory: 200Mi
        env:
        - name: CW_CONFIG_CONTENT
          valueFrom:
            configMapKeyRef:
              name: cwagentconfig
              key: cwagentconfig.json
```

**Azure Monitor for Containers:**

```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: omsagent
  namespace: kube-system
spec:
  selector:
    matchLabels:
      component: oms-agent
  template:
    metadata:
      labels:
        component: oms-agent
    spec:
      serviceAccountName: omsagent
      containers:
      - name: omsagent
        image: mcr.microsoft.com/azuremonitor/containerinsights/ciprod:latest
        resources:
          limits:
            cpu: 150m
            memory: 600Mi
          requests:
            cpu: 75m
            memory: 225Mi
        env:
        - name: WSID
          valueFrom:
            secretKeyRef:
              name: omsagent-secret
              key: WSID
        - name: KEY
          valueFrom:
            secretKeyRef:
              name: omsagent-secret
              key: KEY
```

**Google Cloud Monitoring:**

```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: gke-metadata-server
  namespace: kube-system
spec:
  selector:
    matchLabels:
      k8s-app: gke-metadata-server
  template:
    metadata:
      labels:
        k8s-app: gke-metadata-server
    spec:
      hostNetwork: true
      dnsPolicy: ClusterFirstWithHostNet
      containers:
      - name: gke-metadata-server
        image: gke.gcr.io/gke-metadata-server:v0.4.1
        command:
        - /gke-metadata-server
        - --v=2
        - --logtostderr
        resources:
          requests:
            memory: 50Mi
            cpu: 40m
        securityContext:
          privileged: true
```

### DevOps Best Practices for Cloud Providers

#### Security Hardening Checklist

**✅ EKS Security:**
- Enable private endpoints and restrict public access
- Use IAM roles for service accounts (IRSA)
- Enable audit logging and monitor CloudTrail
- Implement Pod Security Standards
- Use AWS Secrets Manager or Parameter Store
- Enable GuardDuty for threat detection

**✅ AKS Security:**
- Enable private clusters and authorized networks
- Use Azure AD integration with RBAC
- Implement Azure Policy for governance
- Enable Azure Defender for Kubernetes
- Use Azure Key Vault for secrets
- Configure network security groups

**✅ GKE Security:**
- Enable private clusters and authorized networks
- Use Workload Identity for secure access
- Enable Binary Authorization for image security
- Use Google Secret Manager
- Enable GKE audit logging
- Implement Pod Security Standards

#### Cost Management

**✅ Cost Optimization:**
- Use spot/preemptible instances for non-critical workloads
- Implement cluster autoscaling
- Right-size node pools and instances
- Use reserved instances for predictable workloads
- Monitor and optimize storage usage
- Implement resource quotas and limits
- Regular cleanup of unused resources

#### Operational Excellence

**✅ Operations:**
- Implement GitOps for cluster configuration
- Use Infrastructure as Code for reproducibility
- Set up comprehensive monitoring and alerting
- Implement proper backup and disaster recovery
- Regular security scanning and updates
- Documentation and runbook maintenance