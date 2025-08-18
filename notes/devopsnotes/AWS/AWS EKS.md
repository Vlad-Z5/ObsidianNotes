# AWS EKS (Elastic Kubernetes Service)

> **Service Type:** Managed Kubernetes | **Tier:** Container Services | **Global/Regional:** Regional

## Overview

Amazon Elastic Kubernetes Service (EKS) is a fully managed Kubernetes service that makes it easy to run Kubernetes on AWS and on-premises. EKS automatically manages the availability and scalability of the Kubernetes control plane nodes responsible for scheduling containers, managing application availability, storing cluster data, and other key tasks.

## DevOps Use Cases

### Container Orchestration at Scale
- **Multi-tier applications** with complex microservice architectures
- **Auto scaling** based on custom metrics and business logic
- **Service mesh** implementation with Istio, Linkerd, or AWS App Mesh
- **Cross-availability zone** deployments for high availability

### Cloud-Native CI/CD
- **GitOps workflows** with ArgoCD, Flux, or Tekton pipelines
- **Canary deployments** with Flagger or Argo Rollouts
- **Blue-green deployments** across multiple environments
- **Feature flag management** with LaunchDarkly or Split integration

### Hybrid and Multi-Cloud Operations
- **EKS Anywhere** for on-premises Kubernetes clusters
- **EKS Distro** for self-managed Kubernetes environments
- **Multi-cloud workload** portability with standard Kubernetes APIs
- **Edge computing** with EKS on AWS Outposts or Wavelength

### Machine Learning and Data Processing
- **Kubernetes-native ML** with Kubeflow, MLflow, or SageMaker Operators
- **GPU workloads** for training and inference
- **Batch processing** with Kubernetes Jobs and CronJobs
- **Data pipeline orchestration** with Apache Airflow on Kubernetes

### Enterprise Platform Engineering
- **Multi-tenant clusters** with namespace isolation and resource quotas
- **Developer self-service** platforms with Backstage or Port
- **Compliance and governance** with Open Policy Agent (OPA) Gatekeeper
- **Cost optimization** with cluster autoscaling and Spot instances

## Core Components

### Control Plane
- **API Server** - Kubernetes API endpoint managed by AWS
- **etcd** - Distributed key-value store for cluster state
- **Scheduler** - Pod placement decisions across worker nodes
- **Controller Manager** - Maintains desired state of cluster resources
- **Cloud Controller Manager** - AWS-specific integrations

### Worker Nodes
- **Managed Node Groups** - AWS-managed EC2 instances with automatic updates
- **Self-Managed Nodes** - Customer-managed EC2 instances for custom configurations
- **Fargate** - Serverless compute for running pods without managing nodes
- **GPU Nodes** - Accelerated computing for ML and HPC workloads

### Networking
- **VPC CNI** - AWS-native networking for pod IP allocation
- **CoreDNS** - DNS service discovery within the cluster
- **Load Balancer Controller** - Integration with ALB/NLB for ingress
- **VPC Lattice** - Service-to-service communication across clusters

### Add-ons and Extensions
- **AWS Load Balancer Controller** - Native AWS load balancer integration
- **EBS CSI Driver** - Persistent volume support with Amazon EBS
- **EFS CSI Driver** - Shared file system support with Amazon EFS
- **Cluster Autoscaler** - Automatic node scaling based on pod requirements
- **Metrics Server** - Resource usage metrics for HPA and VPA

## Practical CLI Examples

### Cluster Management with eksctl

```bash
# Create EKS cluster with managed node group
eksctl create cluster \
  --name production-cluster \
  --version 1.28 \
  --region us-west-2 \
  --zones us-west-2a,us-west-2b,us-west-2c \
  --nodegroup-name workers \
  --node-type m5.large \
  --nodes 3 \
  --nodes-min 1 \
  --nodes-max 10 \
  --ssh-access \
  --ssh-public-key my-key \
  --managed \
  --enable-ssm \
  --tags Environment=Production,Team=Platform

# Create cluster with Fargate profile
eksctl create cluster \
  --name serverless-cluster \
  --version 1.28 \
  --region us-west-2 \
  --fargate \
  --tags Environment=Production,Type=Serverless

# Add managed node group to existing cluster
eksctl create nodegroup \
  --cluster production-cluster \
  --region us-west-2 \
  --name spot-workers \
  --node-type m5.large \
  --nodes 2 \
  --nodes-min 0 \
  --nodes-max 20 \
  --spot \
  --instance-types m5.large,m5.xlarge,m4.large \
  --managed \
  --tags NodeType=Spot,Environment=Production

# Create Fargate profile for specific namespaces
eksctl create fargateprofile \
  --cluster production-cluster \
  --region us-west-2 \
  --name fp-default \
  --namespace default \
  --namespace kube-system

# Update cluster endpoint access
eksctl utils update-cluster-endpoint-access \
  --cluster production-cluster \
  --region us-west-2 \
  --private-access=true \
  --public-access=true \
  --public-access-cidrs=203.0.113.0/24,198.51.100.0/24
```

### AWS CLI Cluster Operations

```bash
# Create EKS cluster using AWS CLI
aws eks create-cluster \
  --name production-cluster \
  --version 1.28 \
  --role-arn arn:aws:iam::123456789012:role/eks-service-role \
  --resources-vpc-config subnetIds=subnet-12345,subnet-67890,subnet-abcdef,securityGroupIds=sg-12345678 \
  --kubernetes-network-config serviceIpv4Cidr=172.20.0.0/16 \
  --logging '{"enable":[{"types":["api","audit","authenticator","controllerManager","scheduler"]}]}' \
  --tags Environment=Production,Team=Platform

# Create managed node group
aws eks create-nodegroup \
  --cluster-name production-cluster \
  --nodegroup-name managed-workers \
  --subnets subnet-12345 subnet-67890 \
  --instance-types m5.large m5.xlarge \
  --ami-type AL2_x86_64 \
  --node-role arn:aws:iam::123456789012:role/NodeInstanceRole \
  --scaling-config minSize=1,maxSize=10,desiredSize=3 \
  --disk-size 20 \
  --capacity-type ON_DEMAND \
  --tags Environment=Production,NodeType=Managed

# Update kubeconfig
aws eks update-kubeconfig \
  --region us-west-2 \
  --name production-cluster \
  --alias production

# Describe cluster
aws eks describe-cluster \
  --name production-cluster \
  --query 'cluster.{Name:name,Status:status,Endpoint:endpoint,Version:version}'

# List node groups
aws eks list-nodegroups \
  --cluster-name production-cluster

# Update node group configuration
aws eks update-nodegroup-config \
  --cluster-name production-cluster \
  --nodegroup-name managed-workers \
  --scaling-config minSize=2,maxSize=20,desiredSize=5
```

### Kubernetes Resource Management

```bash
# Apply cluster-wide resources
kubectl apply -f - <<EOF
apiVersion: v1
kind: Namespace
metadata:
  name: monitoring
  labels:
    name: monitoring
    istio-injection: enabled
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: aws-load-balancer-controller
  namespace: kube-system
  annotations:
    eks.amazonaws.com/role-arn: arn:aws:iam::123456789012:role/AmazonEKSLoadBalancerControllerRole
EOF

# Install AWS Load Balancer Controller
helm repo add eks https://aws.github.io/eks-charts
helm repo update

helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
  -n kube-system \
  --set clusterName=production-cluster \
  --set serviceAccount.create=false \
  --set serviceAccount.name=aws-load-balancer-controller \
  --set region=us-west-2 \
  --set vpcId=vpc-12345678

# Deploy cluster autoscaler
kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: cluster-autoscaler
  namespace: kube-system
  labels:
    app: cluster-autoscaler
spec:
  selector:
    matchLabels:
      app: cluster-autoscaler
  template:
    metadata:
      labels:
        app: cluster-autoscaler
    spec:
      serviceAccountName: cluster-autoscaler
      containers:
      - image: k8s.gcr.io/autoscaling/cluster-autoscaler:v1.21.0
        name: cluster-autoscaler
        resources:
          limits:
            cpu: 100m
            memory: 300Mi
          requests:
            cpu: 100m
            memory: 300Mi
        command:
        - ./cluster-autoscaler
        - --v=4
        - --stderrthreshold=info
        - --cloud-provider=aws
        - --skip-nodes-with-local-storage=false
        - --expander=least-waste
        - --node-group-auto-discovery=asg:tag=k8s.io/cluster-autoscaler/enabled,k8s.io/cluster-autoscaler/production-cluster
        env:
        - name: AWS_REGION
          value: us-west-2
EOF

# Create ingress with ALB
kubectl apply -f - <<EOF
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: web-app-ingress
  namespace: default
  annotations:
    kubernetes.io/ingress.class: alb
    alb.ingress.kubernetes.io/scheme: internet-facing
    alb.ingress.kubernetes.io/target-type: ip
    alb.ingress.kubernetes.io/certificate-arn: arn:aws:acm:us-west-2:123456789012:certificate/12345678-1234-1234-1234-123456789012
    alb.ingress.kubernetes.io/ssl-redirect: '443'
spec:
  rules:
  - host: myapp.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: web-app-service
            port:
              number: 80
EOF
```

### IAM Roles for Service Accounts (IRSA)

```bash
# Create OIDC identity provider
eksctl utils associate-iam-oidc-provider \
  --region us-west-2 \
  --cluster production-cluster \
  --approve

# Create service account with IAM role
eksctl create iamserviceaccount \
  --cluster production-cluster \
  --namespace default \
  --name s3-reader \
  --attach-policy-arn arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess \
  --override-existing-serviceaccounts \
  --approve

# Create custom policy for service account
cat > custom-policy.json << 'EOF'
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "secretsmanager:GetSecretValue",
                "secretsmanager:DescribeSecret"
            ],
            "Resource": "arn:aws:secretsmanager:us-west-2:123456789012:secret:prod/app/*"
        }
    ]
}
EOF

aws iam create-policy \
  --policy-name EKSSecretManagerAccess \
  --policy-document file://custom-policy.json

eksctl create iamserviceaccount \
  --cluster production-cluster \
  --namespace default \
  --name secret-reader \
  --attach-policy-arn arn:aws:iam::123456789012:policy/EKSSecretManagerAccess \
  --approve
```

## DevOps Automation Scripts

### EKS Cluster Deployment Automation

```bash
#!/bin/bash
# deploy-eks-cluster.sh - Comprehensive EKS cluster deployment

CLUSTER_NAME=$1
ENVIRONMENT=$2
REGION=${3:-us-west-2}
K8S_VERSION=${4:-1.28}

if [ $# -lt 2 ]; then
    echo "Usage: $0 <cluster-name> <environment> [region] [k8s-version]"
    exit 1
fi

echo "Deploying EKS cluster: $CLUSTER_NAME in $ENVIRONMENT environment"

# Create cluster configuration
cat > cluster-config.yaml << EOF
apiVersion: eksctl.io/v1alpha5
kind: ClusterConfig

metadata:
  name: $CLUSTER_NAME
  region: $REGION
  version: "$K8S_VERSION"
  tags:
    Environment: $ENVIRONMENT
    ManagedBy: eksctl
    Team: platform

vpc:
  enableDnsHostnames: true
  enableDnsSupport: true
  nat:
    gateway: HighlyAvailable

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
      name: ebs-csi-controller-sa
      namespace: kube-system
    wellKnownPolicies:
      ebsCSIController: true

managedNodeGroups:
- name: system-nodes
  instanceTypes: 
    - m5.large
    - m5.xlarge
  minSize: 2
  maxSize: 10
  desiredCapacity: 3
  volumeSize: 50
  volumeType: gp3
  ssh:
    allow: true
    publicKeyName: eks-workers
  iam:
    attachPolicyARNs:
    - arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy
    - arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy
    - arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly
    - arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore
  labels:
    nodegroup-type: system
    environment: $ENVIRONMENT
  taints:
    - key: CriticalAddonsOnly
      value: "true"
      effect: NoSchedule
  tags:
    k8s.io/cluster-autoscaler/enabled: "true"
    k8s.io/cluster-autoscaler/$CLUSTER_NAME: "owned"

- name: application-nodes
  instanceTypes:
    - m5.large
    - m5.xlarge
    - m5.2xlarge
  minSize: 1
  maxSize: 50
  desiredCapacity: 3
  volumeSize: 100
  volumeType: gp3
  spot: true
  ssh:
    allow: true
    publicKeyName: eks-workers
  iam:
    attachPolicyARNs:
    - arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy
    - arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy
    - arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly
    - arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore
  labels:
    nodegroup-type: application
    environment: $ENVIRONMENT
  tags:
    k8s.io/cluster-autoscaler/enabled: "true"
    k8s.io/cluster-autoscaler/$CLUSTER_NAME: "owned"

fargateProfiles:
- name: serverless-workloads
  selectors:
  - namespace: serverless
  - namespace: batch-jobs
    labels:
      compute-type: serverless

addons:
- name: vpc-cni
  version: latest
  attachPolicyARNs:
  - arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy
- name: coredns
  version: latest
- name: kube-proxy
  version: latest
- name: aws-ebs-csi-driver
  version: latest
  attachPolicyARNs:
  - arn:aws:iam::aws:policy/service-role/AmazonEBSCSIDriverPolicy

cloudWatch:
  clusterLogging:
    enableTypes: ["*"]
    logRetentionInDays: 30
EOF

# Create the cluster
echo "Creating EKS cluster..."
eksctl create cluster -f cluster-config.yaml

# Wait for cluster to be ready
echo "Waiting for cluster to be ready..."
aws eks wait cluster-active --name $CLUSTER_NAME --region $REGION

# Update kubeconfig
aws eks update-kubeconfig --region $REGION --name $CLUSTER_NAME

# Install essential add-ons
echo "Installing essential add-ons..."

# Install AWS Load Balancer Controller
helm repo add eks https://aws.github.io/eks-charts
helm repo update

helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
  -n kube-system \
  --set clusterName=$CLUSTER_NAME \
  --set serviceAccount.create=false \
  --set serviceAccount.name=aws-load-balancer-controller \
  --set region=$REGION

# Install Cluster Autoscaler
kubectl apply -f https://raw.githubusercontent.com/kubernetes/autoscaler/master/cluster-autoscaler/cloudprovider/aws/examples/cluster-autoscaler-autodiscover.yaml

# Patch the deployment to add cluster name and set image
kubectl patch deployment cluster-autoscaler \
  -n kube-system \
  -p '{"spec":{"template":{"metadata":{"annotations":{"cluster-autoscaler.kubernetes.io/safe-to-evict":"false"}},"spec":{"containers":[{"name":"cluster-autoscaler","command":["./cluster-autoscaler","--v=4","--stderrthreshold=info","--cloud-provider=aws","--skip-nodes-with-local-storage=false","--expander=least-waste","--node-group-auto-discovery=asg:tag=k8s.io/cluster-autoscaler/enabled,k8s.io/cluster-autoscaler/'$CLUSTER_NAME'"]}]}}}}'

# Install Metrics Server
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

# Create monitoring namespace
kubectl create namespace monitoring

# Install Prometheus and Grafana using Helm
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --set prometheus.prometheusSpec.serviceMonitorSelectorNilUsesHelmValues=false \
  --set prometheus.prometheusSpec.podMonitorSelectorNilUsesHelmValues=false

# Create sample application namespace and RBAC
kubectl create namespace applications

cat > rbac-config.yaml << EOF
apiVersion: v1
kind: ServiceAccount
metadata:
  name: app-deployer
  namespace: applications
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: applications
  name: app-deployer
rules:
- apiGroups: [""]
  resources: ["pods", "services", "configmaps", "secrets"]
  verbs: ["*"]
- apiGroups: ["apps"]
  resources: ["deployments", "replicasets"]
  verbs: ["*"]
- apiGroups: ["networking.k8s.io"]
  resources: ["ingresses"]
  verbs: ["*"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: app-deployer
  namespace: applications
subjects:
- kind: ServiceAccount
  name: app-deployer
  namespace: applications
roleRef:
  kind: Role
  name: app-deployer
  apiGroup: rbac.authorization.k8s.io
EOF

kubectl apply -f rbac-config.yaml

echo "EKS cluster $CLUSTER_NAME deployed successfully!"
echo "Cluster endpoint: $(aws eks describe-cluster --name $CLUSTER_NAME --region $REGION --query 'cluster.endpoint' --output text)"
echo "Configure kubectl: aws eks update-kubeconfig --region $REGION --name $CLUSTER_NAME"

# Clean up temporary files
rm -f cluster-config.yaml rbac-config.yaml
```

### Application Deployment with GitOps

```bash
#!/bin/bash
# setup-gitops.sh - Setup GitOps workflow with ArgoCD

CLUSTER_NAME=$1
GITHUB_REPO=$2
GITHUB_TOKEN=$3

if [ $# -lt 3 ]; then
    echo "Usage: $0 <cluster-name> <github-repo-url> <github-token>"
    exit 1
fi

echo "Setting up GitOps for cluster: $CLUSTER_NAME"

# Install ArgoCD
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# Wait for ArgoCD to be ready
echo "Waiting for ArgoCD to be ready..."
kubectl wait --for=condition=available --timeout=600s deployment/argocd-server -n argocd

# Create ArgoCD ingress
cat > argocd-ingress.yaml << EOF
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: argocd-server-ingress
  namespace: argocd
  annotations:
    kubernetes.io/ingress.class: alb
    alb.ingress.kubernetes.io/scheme: internet-facing
    alb.ingress.kubernetes.io/target-type: ip
    alb.ingress.kubernetes.io/backend-protocol: HTTPS
    alb.ingress.kubernetes.io/listen-ports: '[{"HTTP": 80}, {"HTTPS": 443}]'
    alb.ingress.kubernetes.io/ssl-redirect: '443'
    alb.ingress.kubernetes.io/healthcheck-protocol: HTTPS
    alb.ingress.kubernetes.io/healthcheck-path: /healthz
spec:
  rules:
  - host: argocd.${CLUSTER_NAME}.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: argocd-server
            port:
              number: 443
EOF

kubectl apply -f argocd-ingress.yaml

# Configure ArgoCD server for ALB
kubectl patch configmap argocd-cmd-params-cm -n argocd --type merge -p '{"data":{"server.insecure":"true"}}'
kubectl patch deployment argocd-server -n argocd --type merge -p '{"spec":{"template":{"spec":{"containers":[{"name":"argocd-server","command":["argocd-server","--insecure"]}]}}}}'

# Get ArgoCD admin password
ARGOCD_PASSWORD=$(kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d)
echo "ArgoCD admin password: $ARGOCD_PASSWORD"

# Install ArgoCD CLI
curl -sSL -o /usr/local/bin/argocd https://github.com/argoproj/argo-cd/releases/latest/download/argocd-linux-amd64
chmod +x /usr/local/bin/argocd

# Wait for ArgoCD server to be accessible
echo "Waiting for ArgoCD server to be accessible..."
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=argocd-server -n argocd --timeout=300s

# Port forward to access ArgoCD
kubectl port-forward svc/argocd-server -n argocd 8080:443 &
PORTFORWARD_PID=$!

sleep 10

# Login to ArgoCD
argocd login localhost:8080 --username admin --password $ARGOCD_PASSWORD --insecure

# Create repository secret for GitHub
kubectl create secret generic github-repo -n argocd \
  --from-literal=type=git \
  --from-literal=url=$GITHUB_REPO \
  --from-literal=password=$GITHUB_TOKEN \
  --from-literal=username=not-used

kubectl label secret github-repo -n argocd argocd.argoproj.io/secret-type=repository

# Create ArgoCD application
cat > application.yaml << EOF
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: sample-app
  namespace: argocd
  finalizers:
    - resources-finalizer.argocd.argoproj.io
spec:
  project: default
  source:
    repoURL: $GITHUB_REPO
    targetRevision: HEAD
    path: k8s-manifests
  destination:
    server: https://kubernetes.default.svc
    namespace: applications
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
    - CreateNamespace=true
    retry:
      limit: 3
      backoff:
        duration: 5s
        factor: 2
        maxDuration: 3m
EOF

kubectl apply -f application.yaml

# Create sample application manifests directory structure
mkdir -p sample-app-manifests/k8s-manifests

cat > sample-app-manifests/k8s-manifests/deployment.yaml << EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: sample-app
  namespace: applications
  labels:
    app: sample-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: sample-app
  template:
    metadata:
      labels:
        app: sample-app
    spec:
      containers:
      - name: app
        image: nginx:1.21
        ports:
        - containerPort: 80
        resources:
          requests:
            memory: "64Mi"
            cpu: "50m"
          limits:
            memory: "128Mi"
            cpu: "100m"
        livenessProbe:
          httpGet:
            path: /
            port: 80
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /
            port: 80
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: sample-app-service
  namespace: applications
spec:
  selector:
    app: sample-app
  ports:
    - protocol: TCP
      port: 80
      targetPort: 80
  type: ClusterIP
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: sample-app-ingress
  namespace: applications
  annotations:
    kubernetes.io/ingress.class: alb
    alb.ingress.kubernetes.io/scheme: internet-facing
    alb.ingress.kubernetes.io/target-type: ip
spec:
  rules:
  - host: sample-app.${CLUSTER_NAME}.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: sample-app-service
            port:
              number: 80
EOF

# Kill port forward
kill $PORTFORWARD_PID

echo "GitOps setup completed!"
echo "ArgoCD URL: https://argocd.${CLUSTER_NAME}.example.com"
echo "Username: admin"
echo "Password: $ARGOCD_PASSWORD"
echo ""
echo "Sample application manifests created in: sample-app-manifests/"
echo "Commit these to your GitHub repository to see GitOps in action!"

# Clean up temporary files
rm -f argocd-ingress.yaml application.yaml
```

### EKS Cluster Monitoring and Alerting

```python
# eks-monitoring.py - Comprehensive EKS cluster monitoring and alerting
import boto3
import json
import logging
from datetime import datetime, timedelta
from kubernetes import client, config
from typing import Dict, List

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EKSMonitor:
    def __init__(self, cluster_name: str, region: str = 'us-west-2'):
        self.cluster_name = cluster_name
        self.region = region
        self.eks_client = boto3.client('eks', region_name=region)
        self.cloudwatch_client = boto3.client('cloudwatch', region_name=region)
        self.sns_client = boto3.client('sns', region_name=region)
        
        # Initialize Kubernetes client
        try:
            config.load_kube_config()
            self.k8s_client = client.ApiClient()
            self.core_v1 = client.CoreV1Api()
            self.apps_v1 = client.AppsV1Api()
            self.metrics_v1 = client.CustomObjectsApi()
        except Exception as e:
            logger.error(f"Failed to initialize Kubernetes client: {e}")
    
    def get_cluster_health(self) -> Dict:
        """Get comprehensive cluster health status"""
        
        health_status = {
            'cluster_name': self.cluster_name,
            'timestamp': datetime.now().isoformat(),
            'control_plane': {},
            'nodes': {},
            'workloads': {},
            'networking': {},
            'storage': {}
        }
        
        # Check control plane health
        try:
            cluster_info = self.eks_client.describe_cluster(name=self.cluster_name)
            control_plane = cluster_info['cluster']
            
            health_status['control_plane'] = {
                'status': control_plane['status'],
                'version': control_plane['version'],
                'endpoint': control_plane['endpoint'],
                'platform_version': control_plane['platformVersion']
            }
            
            # Check cluster logging
            logging_config = control_plane.get('logging', {}).get('clusterLogging', {}).get('enabledTypes', [])
            health_status['control_plane']['logging_enabled'] = [log['type'] for log in logging_config]
            
        except Exception as e:
            logger.error(f"Failed to get control plane status: {e}")
            health_status['control_plane']['error'] = str(e)
        
        # Check node health
        try:
            nodes = self.core_v1.list_node()
            node_stats = {
                'total': len(nodes.items),
                'ready': 0,
                'not_ready': 0,
                'unknown': 0,
                'node_details': []
            }
            
            for node in nodes.items:
                node_info = {
                    'name': node.metadata.name,
                    'status': 'Unknown',
                    'roles': [],
                    'version': node.status.node_info.kubelet_version,
                    'instance_type': node.metadata.labels.get('node.kubernetes.io/instance-type', 'unknown')
                }
                
                # Determine node roles
                for label in node.metadata.labels:
                    if 'node-role.kubernetes.io' in label:
                        role = label.split('/')[-1]
                        if role:
                            node_info['roles'].append(role)
                
                # Check node conditions
                for condition in node.status.conditions:
                    if condition.type == 'Ready':
                        if condition.status == 'True':
                            node_stats['ready'] += 1
                            node_info['status'] = 'Ready'
                        elif condition.status == 'False':
                            node_stats['not_ready'] += 1
                            node_info['status'] = 'NotReady'
                        else:
                            node_stats['unknown'] += 1
                            node_info['status'] = 'Unknown'
                        break
                
                node_stats['node_details'].append(node_info)
            
            health_status['nodes'] = node_stats
            
        except Exception as e:
            logger.error(f"Failed to get node status: {e}")
            health_status['nodes']['error'] = str(e)
        
        # Check workload health
        try:
            # Get deployment status
            deployments = self.apps_v1.list_deployment_for_all_namespaces()
            deployment_stats = {
                'total': len(deployments.items),
                'available': 0,
                'unavailable': 0,
                'failed_deployments': []
            }
            
            for deployment in deployments.items:
                if deployment.status.available_replicas == deployment.spec.replicas:
                    deployment_stats['available'] += 1
                else:
                    deployment_stats['unavailable'] += 1
                    deployment_stats['failed_deployments'].append({
                        'name': deployment.metadata.name,
                        'namespace': deployment.metadata.namespace,
                        'desired': deployment.spec.replicas,
                        'available': deployment.status.available_replicas or 0
                    })
            
            # Get pod status
            pods = self.core_v1.list_pod_for_all_namespaces()
            pod_stats = {
                'total': len(pods.items),
                'running': 0,
                'pending': 0,
                'failed': 0,
                'unknown': 0,
                'failed_pods': []
            }
            
            for pod in pods.items:
                phase = pod.status.phase
                if phase == 'Running':
                    pod_stats['running'] += 1
                elif phase == 'Pending':
                    pod_stats['pending'] += 1
                elif phase == 'Failed':
                    pod_stats['failed'] += 1
                    pod_stats['failed_pods'].append({
                        'name': pod.metadata.name,
                        'namespace': pod.metadata.namespace,
                        'reason': pod.status.reason,
                        'message': pod.status.message
                    })
                else:
                    pod_stats['unknown'] += 1
            
            health_status['workloads'] = {
                'deployments': deployment_stats,
                'pods': pod_stats
            }
            
        except Exception as e:
            logger.error(f"Failed to get workload status: {e}")
            health_status['workloads']['error'] = str(e)
        
        return health_status
    
    def get_resource_utilization(self) -> Dict:
        """Get cluster resource utilization metrics"""
        
        try:
            # Get node metrics from metrics server
            node_metrics = self.metrics_v1.list_cluster_custom_object(
                group="metrics.k8s.io",
                version="v1beta1",
                plural="nodes"
            )
            
            # Get pod metrics
            pod_metrics = self.metrics_v1.list_cluster_custom_object(
                group="metrics.k8s.io",
                version="v1beta1",
                plural="pods"
            )
            
            utilization = {
                'timestamp': datetime.now().isoformat(),
                'node_utilization': [],
                'cluster_totals': {
                    'cpu_usage': 0,
                    'memory_usage': 0,
                    'cpu_capacity': 0,
                    'memory_capacity': 0
                }
            }
            
            # Process node metrics
            for node_metric in node_metrics['items']:
                node_name = node_metric['metadata']['name']
                cpu_usage = self._parse_cpu_value(node_metric['usage']['cpu'])
                memory_usage = self._parse_memory_value(node_metric['usage']['memory'])
                
                # Get node capacity
                node = self.core_v1.read_node(name=node_name)
                cpu_capacity = self._parse_cpu_value(node.status.capacity['cpu'])
                memory_capacity = self._parse_memory_value(node.status.capacity['memory'])
                
                node_util = {
                    'name': node_name,
                    'cpu_usage': cpu_usage,
                    'cpu_capacity': cpu_capacity,
                    'cpu_percentage': (cpu_usage / cpu_capacity) * 100 if cpu_capacity > 0 else 0,
                    'memory_usage': memory_usage,
                    'memory_capacity': memory_capacity,
                    'memory_percentage': (memory_usage / memory_capacity) * 100 if memory_capacity > 0 else 0
                }
                
                utilization['node_utilization'].append(node_util)
                
                # Add to cluster totals
                utilization['cluster_totals']['cpu_usage'] += cpu_usage
                utilization['cluster_totals']['cpu_capacity'] += cpu_capacity
                utilization['cluster_totals']['memory_usage'] += memory_usage
                utilization['cluster_totals']['memory_capacity'] += memory_capacity
            
            # Calculate cluster utilization percentages
            if utilization['cluster_totals']['cpu_capacity'] > 0:
                utilization['cluster_totals']['cpu_percentage'] = (
                    utilization['cluster_totals']['cpu_usage'] / 
                    utilization['cluster_totals']['cpu_capacity']
                ) * 100
            
            if utilization['cluster_totals']['memory_capacity'] > 0:
                utilization['cluster_totals']['memory_percentage'] = (
                    utilization['cluster_totals']['memory_usage'] / 
                    utilization['cluster_totals']['memory_capacity']
                ) * 100
            
            return utilization
            
        except Exception as e:
            logger.error(f"Failed to get resource utilization: {e}")
            return {'error': str(e)}
    
    def _parse_cpu_value(self, cpu_string: str) -> float:
        """Parse CPU value from Kubernetes format to cores"""
        if cpu_string.endswith('n'):
            return float(cpu_string[:-1]) / 1_000_000_000
        elif cpu_string.endswith('u'):
            return float(cpu_string[:-1]) / 1_000_000
        elif cpu_string.endswith('m'):
            return float(cpu_string[:-1]) / 1_000
        else:
            return float(cpu_string)
    
    def _parse_memory_value(self, memory_string: str) -> int:
        """Parse memory value from Kubernetes format to bytes"""
        units = {
            'Ki': 1024,
            'Mi': 1024**2,
            'Gi': 1024**3,
            'Ti': 1024**4,
            'K': 1000,
            'M': 1000**2,
            'G': 1000**3,
            'T': 1000**4
        }
        
        for unit, multiplier in units.items():
            if memory_string.endswith(unit):
                return int(float(memory_string[:-len(unit)]) * multiplier)
        
        return int(memory_string)
    
    def check_security_compliance(self) -> Dict:
        """Check cluster security compliance"""
        
        compliance_report = {
            'timestamp': datetime.now().isoformat(),
            'cluster_name': self.cluster_name,
            'security_checks': [],
            'compliance_score': 0,
            'total_checks': 0
        }
        
        checks_passed = 0
        
        try:
            # Check 1: Private endpoint access
            cluster_info = self.eks_client.describe_cluster(name=self.cluster_name)
            endpoint_config = cluster_info['cluster']['resourcesVpcConfig']
            
            private_access = endpoint_config.get('endpointPrivateAccess', False)
            public_access = endpoint_config.get('endpointPublicAccess', True)
            
            compliance_report['security_checks'].append({
                'check': 'Private Endpoint Access',
                'status': 'PASS' if private_access else 'FAIL',
                'description': 'Cluster should have private endpoint access enabled',
                'remediation': 'Enable private endpoint access for the cluster'
            })
            
            if private_access:
                checks_passed += 1
            compliance_report['total_checks'] += 1
            
            # Check 2: Public endpoint restrictions
            public_cidrs = endpoint_config.get('publicAccessCidrs', ['0.0.0.0/0'])
            restricted_public = '0.0.0.0/0' not in public_cidrs
            
            compliance_report['security_checks'].append({
                'check': 'Public Endpoint Restrictions',
                'status': 'PASS' if restricted_public else 'FAIL',
                'description': 'Public endpoint should have CIDR restrictions',
                'remediation': 'Restrict public endpoint access to specific CIDR blocks'
            })
            
            if restricted_public:
                checks_passed += 1
            compliance_report['total_checks'] += 1
            
            # Check 3: Cluster logging enabled
            logging_config = cluster_info['cluster'].get('logging', {}).get('clusterLogging', {})
            enabled_logs = logging_config.get('enabledTypes', [])
            required_logs = ['api', 'audit', 'authenticator']
            
            logging_enabled = all(
                any(log['type'] == req_log for log in enabled_logs) 
                for req_log in required_logs
            )
            
            compliance_report['security_checks'].append({
                'check': 'Control Plane Logging',
                'status': 'PASS' if logging_enabled else 'FAIL',
                'description': 'Essential control plane logging should be enabled',
                'remediation': 'Enable API, audit, and authenticator logging'
            })
            
            if logging_enabled:
                checks_passed += 1
            compliance_report['total_checks'] += 1
            
            # Check 4: Network policies
            network_policies = self.core_v1.list_network_policy_for_all_namespaces()
            has_network_policies = len(network_policies.items) > 0
            
            compliance_report['security_checks'].append({
                'check': 'Network Policies',
                'status': 'PASS' if has_network_policies else 'FAIL',
                'description': 'Network policies should be implemented for security',
                'remediation': 'Implement network policies to control pod-to-pod communication'
            })
            
            if has_network_policies:
                checks_passed += 1
            compliance_report['total_checks'] += 1
            
            # Check 5: Pod Security Standards
            namespaces = self.core_v1.list_namespace()
            pss_compliant = True
            
            for namespace in namespaces.items:
                labels = namespace.metadata.labels or {}
                if not any('pod-security' in label for label in labels):
                    pss_compliant = False
                    break
            
            compliance_report['security_checks'].append({
                'check': 'Pod Security Standards',
                'status': 'PASS' if pss_compliant else 'FAIL',
                'description': 'Namespaces should have Pod Security Standards labels',
                'remediation': 'Add pod-security.kubernetes.io labels to namespaces'
            })
            
            if pss_compliant:
                checks_passed += 1
            compliance_report['total_checks'] += 1
            
            # Calculate compliance score
            compliance_report['compliance_score'] = (
                checks_passed / compliance_report['total_checks'] * 100
                if compliance_report['total_checks'] > 0 else 0
            )
            
        except Exception as e:
            logger.error(f"Security compliance check failed: {e}")
            compliance_report['error'] = str(e)
        
        return compliance_report
    
    def send_alerts(self, health_status: Dict, utilization: Dict, compliance: Dict, 
                   sns_topic_arn: str):
        """Send alerts based on monitoring data"""
        
        alerts = []
        
        # Check for critical issues
        if health_status.get('nodes', {}).get('not_ready', 0) > 0:
            alerts.append(f"🔴 {health_status['nodes']['not_ready']} nodes are not ready")
        
        if health_status.get('workloads', {}).get('pods', {}).get('failed', 0) > 0:
            alerts.append(f"🔴 {health_status['workloads']['pods']['failed']} pods failed")
        
        # Check resource utilization
        cluster_cpu = utilization.get('cluster_totals', {}).get('cpu_percentage', 0)
        cluster_memory = utilization.get('cluster_totals', {}).get('memory_percentage', 0)
        
        if cluster_cpu > 80:
            alerts.append(f"⚠️ High CPU utilization: {cluster_cpu:.1f}%")
        
        if cluster_memory > 80:
            alerts.append(f"⚠️ High memory utilization: {cluster_memory:.1f}%")
        
        # Check compliance score
        compliance_score = compliance.get('compliance_score', 100)
        if compliance_score < 80:
            alerts.append(f"🔒 Security compliance score low: {compliance_score:.1f}%")
        
        # Send alerts if any issues found
        if alerts:
            message = f"""
EKS Cluster Alert: {self.cluster_name}

Critical Issues Detected:
{chr(10).join(alerts)}

Cluster Status:
- Control Plane: {health_status.get('control_plane', {}).get('status', 'Unknown')}
- Ready Nodes: {health_status.get('nodes', {}).get('ready', 0)}/{health_status.get('nodes', {}).get('total', 0)}
- Running Pods: {health_status.get('workloads', {}).get('pods', {}).get('running', 0)}
- CPU Utilization: {cluster_cpu:.1f}%
- Memory Utilization: {cluster_memory:.1f}%
- Security Compliance: {compliance_score:.1f}%

Timestamp: {datetime.now().isoformat()}
"""
            
            try:
                self.sns_client.publish(
                    TopicArn=sns_topic_arn,
                    Message=message,
                    Subject=f"EKS Alert: {self.cluster_name} - {len(alerts)} issues detected"
                )
                logger.info(f"Alert sent for {len(alerts)} issues")
            except Exception as e:
                logger.error(f"Failed to send alert: {e}")

def main():
    """Main monitoring workflow"""
    
    cluster_name = 'production-cluster'
    sns_topic_arn = 'arn:aws:sns:us-west-2:123456789012:eks-alerts'
    
    monitor = EKSMonitor(cluster_name)
    
    # Get cluster health
    logger.info("Checking cluster health...")
    health_status = monitor.get_cluster_health()
    
    # Get resource utilization
    logger.info("Checking resource utilization...")
    utilization = monitor.get_resource_utilization()
    
    # Check security compliance
    logger.info("Checking security compliance...")
    compliance = monitor.check_security_compliance()
    
    # Send alerts if needed
    monitor.send_alerts(health_status, utilization, compliance, sns_topic_arn)
    
    # Print summary
    print(f"Cluster Health Summary for {cluster_name}:")
    print(f"- Control Plane: {health_status.get('control_plane', {}).get('status', 'Unknown')}")
    print(f"- Ready Nodes: {health_status.get('nodes', {}).get('ready', 0)}/{health_status.get('nodes', {}).get('total', 0)}")
    print(f"- Running Pods: {health_status.get('workloads', {}).get('pods', {}).get('running', 0)}")
    
    if 'cluster_totals' in utilization:
        print(f"- CPU Utilization: {utilization['cluster_totals'].get('cpu_percentage', 0):.1f}%")
        print(f"- Memory Utilization: {utilization['cluster_totals'].get('memory_percentage', 0):.1f}%")
    
    print(f"- Security Compliance: {compliance.get('compliance_score', 0):.1f}%")

if __name__ == "__main__":
    main()
```

## Advanced Production Patterns

### Multi-Cluster Management

```terraform
# Advanced multi-cluster EKS setup with cross-cluster networking
module "production_clusters" {
  source = "./modules/eks-cluster"
  
  for_each = {
    "prod-us-east-1" = {
      region = "us-east-1"
      availability_zones = ["us-east-1a", "us-east-1b", "us-east-1c"]
      node_groups = {
        system = {
          instance_types = ["m6i.large", "m6i.xlarge"]
          capacity_type = "ON_DEMAND"
          min_size = 3
          max_size = 10
          desired_size = 3
        }
        application = {
          instance_types = ["m6i.large", "m6i.xlarge", "m6i.2xlarge"]
          capacity_type = "SPOT"
          min_size = 2
          max_size = 50
          desired_size = 5
        }
      }
    }
    "prod-us-west-2" = {
      region = "us-west-2"
      availability_zones = ["us-west-2a", "us-west-2b", "us-west-2c"]
      node_groups = {
        system = {
          instance_types = ["m6i.large", "m6i.xlarge"]
          capacity_type = "ON_DEMAND"
          min_size = 3
          max_size = 10
          desired_size = 3
        }
        application = {
          instance_types = ["m6i.large", "m6i.xlarge", "m6i.2xlarge"]
          capacity_type = "SPOT"
          min_size = 2
          max_size = 50
          desired_size = 5
        }
      }
    }
  }
  
  cluster_name = each.key
  region = each.value.region
  availability_zones = each.value.availability_zones
  node_groups = each.value.node_groups
  
  # Advanced security configuration
  cluster_encryption_config = {
    provider_key_arn = aws_kms_key.eks[each.value.region].arn
    resources = ["secrets"]
  }
  
  # Enhanced logging
  cluster_enabled_log_types = ["api", "audit", "authenticator", "controllerManager", "scheduler"]
  
  # Network configuration
  cluster_endpoint_private_access = true
  cluster_endpoint_public_access = false
  cluster_endpoint_public_access_cidrs = []
  
  # Add-ons with specific versions
  cluster_addons = {
    coredns = {
      addon_version = "v1.10.1-eksbuild.1"
      resolve_conflicts = "OVERWRITE"
    }
    kube-proxy = {
      addon_version = "v1.28.1-eksbuild.1"
      resolve_conflicts = "OVERWRITE"
    }
    vpc-cni = {
      addon_version = "v1.13.4-eksbuild.1"
      resolve_conflicts = "OVERWRITE"
      configuration_values = jsonencode({
        env = {
          ENABLE_PREFIX_DELEGATION = "true"
          ENABLE_POD_ENI = "true"
          POD_SECURITY_GROUP_ENFORCING_MODE = "standard"
        }
      })
    }
    aws-ebs-csi-driver = {
      addon_version = "v1.22.0-eksbuild.2"
      resolve_conflicts = "OVERWRITE"
    }
  }
  
  tags = {
    Environment = "production"
    ManagedBy = "terraform"
    Team = "platform"
    CostCenter = "engineering"
  }
}

# Cross-cluster service mesh with Istio
resource "helm_release" "istio_base" {
  for_each = module.production_clusters
  
  name       = "istio-base"
  repository = "https://istio-release.storage.googleapis.com/charts"
  chart      = "base"
  namespace  = "istio-system"
  version    = "1.19.0"
  
  create_namespace = true
  
  depends_on = [each.value.cluster_endpoint]
}

resource "helm_release" "istiod" {
  for_each = module.production_clusters
  
  name       = "istiod"
  repository = "https://istio-release.storage.googleapis.com/charts"
  chart      = "istiod"
  namespace  = "istio-system"
  version    = "1.19.0"
  
  values = [
    yamlencode({
      pilot = {
        env = {
          EXTERNAL_ISTIOD = true
        }
      }
      global = {
        meshID = "mesh1"
        network = each.key
        externalIstiod = true
      }
    })
  ]
  
  depends_on = [helm_release.istio_base[each.key]]
}
```

### Advanced Workload Scheduling

```yaml
# Sophisticated workload scheduling with node affinity and taints
apiVersion: apps/v1
kind: Deployment
metadata:
  name: high-performance-app
  namespace: production
spec:
  replicas: 6
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 1
      maxSurge: 2
  selector:
    matchLabels:
      app: high-performance-app
  template:
    metadata:
      labels:
        app: high-performance-app
        version: v1.2.3
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8080"
        prometheus.io/path: "/metrics"
    spec:
      # Advanced scheduling constraints
      affinity:
        nodeAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
            nodeSelectorTerms:
            - matchExpressions:
              - key: node.kubernetes.io/instance-type
                operator: In
                values: ["m6i.xlarge", "m6i.2xlarge", "c6i.xlarge"]
              - key: topology.kubernetes.io/zone
                operator: In
                values: ["us-west-2a", "us-west-2b", "us-west-2c"]
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            preference:
              matchExpressions:
              - key: node-type
                operator: In
                values: ["compute-optimized"]
        podAntiAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
          - labelSelector:
              matchExpressions:
              - key: app
                operator: In
                values: ["high-performance-app"]
            topologyKey: kubernetes.io/hostname
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            podAffinityTerm:
              labelSelector:
                matchExpressions:
                - key: app
                  operator: In
                  values: ["high-performance-app"]
              topologyKey: topology.kubernetes.io/zone
      
      # Tolerate specific taints
      tolerations:
      - key: "high-performance"
        operator: "Equal"
        value: "true"
        effect: "NoSchedule"
      - key: "node.kubernetes.io/instance-type"
        operator: "Equal"
        value: "c6i.xlarge"
        effect: "NoSchedule"
      
      # Security context
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        runAsGroup: 1000
        fsGroup: 1000
        seccompProfile:
          type: RuntimeDefault
      
      # Service account with IRSA
      serviceAccountName: high-performance-app
      
      # Init containers for setup
      initContainers:
      - name: migration
        image: migrate/migrate:v4.16.2
        command:
        - migrate
        - "-path"
        - "/migrations"
        - "-database"
        - "$(DATABASE_URL)"
        - "up"
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: database-credentials
              key: url
        volumeMounts:
        - name: migrations
          mountPath: /migrations
        securityContext:
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true
          capabilities:
            drop: ["ALL"]
      
      containers:
      - name: app
        image: mycompany/high-performance-app:v1.2.3
        ports:
        - containerPort: 8080
          name: http
          protocol: TCP
        - containerPort: 9090
          name: metrics
          protocol: TCP
        
        # Resource management
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
            ephemeral-storage: "2Gi"
          limits:
            memory: "2Gi"
            cpu: "1000m"
            ephemeral-storage: "4Gi"
        
        # Environment configuration
        env:
        - name: NODE_NAME
          valueFrom:
            fieldRef:
              fieldPath: spec.nodeName
        - name: POD_NAME
          valueFrom:
            fieldRef:
              fieldPath: metadata.name
        - name: POD_NAMESPACE
          valueFrom:
            fieldRef:
              fieldPath: metadata.namespace
        - name: POD_IP
          valueFrom:
            fieldRef:
              fieldPath: status.podIP
        
        envFrom:
        - configMapRef:
            name: app-config
        - secretRef:
            name: app-secrets
        
        # Health checks
        livenessProbe:
          httpGet:
            path: /health/live
            port: 8080
            httpHeaders:
            - name: Custom-Header
              value: liveness-check
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          successThreshold: 1
          failureThreshold: 3
        
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
          timeoutSeconds: 3
          successThreshold: 1
          failureThreshold: 3
        
        startupProbe:
          httpGet:
            path: /health/startup
            port: 8080
          initialDelaySeconds: 10
          periodSeconds: 2
          timeoutSeconds: 1
          successThreshold: 1
          failureThreshold: 30
        
        # Security context
        securityContext:
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true
          capabilities:
            drop: ["ALL"]
            add: ["NET_BIND_SERVICE"]
        
        # Volume mounts
        volumeMounts:
        - name: tmp
          mountPath: /tmp
        - name: cache
          mountPath: /app/cache
        - name: config
          mountPath: /app/config
          readOnly: true
        - name: tls-certs
          mountPath: /app/certs
          readOnly: true
      
      # Volumes
      volumes:
      - name: tmp
        emptyDir: {}
      - name: cache
        emptyDir:
          sizeLimit: 1Gi
      - name: config
        configMap:
          name: app-config
          defaultMode: 0644
      - name: migrations
        configMap:
          name: database-migrations
      - name: tls-certs
        secret:
          secretName: tls-certificates
          defaultMode: 0600
      
      # DNS configuration
      dnsPolicy: ClusterFirst
      dnsConfig:
        options:
        - name: ndots
          value: "2"
        - name: edns0
      
      # Priority and preemption
      priorityClassName: high-priority
      
      # Graceful termination
      terminationGracePeriodSeconds: 60
---
# Horizontal Pod Autoscaler with custom metrics
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: high-performance-app-hpa
  namespace: production
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: high-performance-app
  minReplicas: 6
  maxReplicas: 100
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
  - type: Pods
    pods:
      metric:
        name: custom_requests_per_second
      target:
        type: AverageValue
        averageValue: "100"
  - type: External
    external:
      metric:
        name: sqs_queue_length
        selector:
          matchLabels:
            queue: high-priority-queue
      target:
        type: Value
        value: "30"
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 10
        periodSeconds: 60
      - type: Pods
        value: 2
        periodSeconds: 60
      selectPolicy: Min
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Percent
        value: 50
        periodSeconds: 30
      - type: Pods
        value: 4
        periodSeconds: 60
      selectPolicy: Max
---
# Pod Disruption Budget
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: high-performance-app-pdb
  namespace: production
spec:
  minAvailable: 50%
  selector:
    matchLabels:
      app: high-performance-app
```

### Advanced Security Configuration

```yaml
# Comprehensive security setup with PSS, Network Policies, and RBAC
apiVersion: v1
kind: Namespace
metadata:
  name: secure-production
  labels:
    # Pod Security Standards
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/warn: restricted
    # Istio injection
    istio-injection: enabled
    # Monitoring
    prometheus.io/scrape: "true"
---
# Network Policy for micro-segmentation
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: secure-app-netpol
  namespace: secure-production
spec:
  podSelector:
    matchLabels:
      app: secure-app
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: istio-system
    - namespaceSelector:
        matchLabels:
          name: monitoring
      podSelector:
        matchLabels:
          app: prometheus
    - podSelector:
        matchLabels:
          app: frontend
    ports:
    - protocol: TCP
      port: 8080
    - protocol: TCP
      port: 9090  # metrics
  egress:
  - to:
    - namespaceSelector:
        matchLabels:
          name: database
      podSelector:
        matchLabels:
          app: postgresql
    ports:
    - protocol: TCP
      port: 5432
  - to:
    - namespaceSelector:
        matchLabels:
          name: cache
      podSelector:
        matchLabels:
          app: redis
    ports:
    - protocol: TCP
      port: 6379
  - to: []  # DNS
    ports:
    - protocol: UDP
      port: 53
  - to: []  # HTTPS to external services
    ports:
    - protocol: TCP
      port: 443
---
# Service Account with minimal RBAC
apiVersion: v1
kind: ServiceAccount
metadata:
  name: secure-app
  namespace: secure-production
  annotations:
    eks.amazonaws.com/role-arn: arn:aws:iam::123456789012:role/SecureAppRole
automountServiceAccountToken: false
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: secure-production
  name: secure-app-role
rules:
- apiGroups: [""]
  resources: ["configmaps"]
  verbs: ["get", "list"]
  resourceNames: ["app-config", "feature-flags"]
- apiGroups: [""]
  resources: ["secrets"]
  verbs: ["get"]
  resourceNames: ["app-secrets"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: secure-app-binding
  namespace: secure-production
subjects:
- kind: ServiceAccount
  name: secure-app
  namespace: secure-production
roleRef:
  kind: Role
  name: secure-app-role
  apiGroup: rbac.authorization.k8s.io
---
# Security Context Constraints
apiVersion: v1
kind: Secret
metadata:
  name: app-secrets
  namespace: secure-production
type: Opaque
data:
  database-password: <base64-encoded-password>
  api-key: <base64-encoded-api-key>
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
  namespace: secure-production
data:
  app.properties: |
    server.port=8080
    management.endpoints.web.exposure.include=health,metrics,prometheus
    management.endpoint.health.show-details=when-authorized
    logging.level.com.company=INFO
    security.require-ssl=true
---
# OPA Gatekeeper Policy
apiVersion: templates.gatekeeper.sh/v1beta1
kind: ConstraintTemplate
metadata:
  name: requiresecuritycontext
spec:
  crd:
    spec:
      names:
        kind: RequireSecurityContext
      validation:
        openAPIV3Schema:
          type: object
  targets:
    - target: admission.k8s.gatekeeper.sh
      rego: |
        package requiresecuritycontext
        
        violation[{"msg": msg}] {
          container := input.review.object.spec.containers[_]
          not container.securityContext.runAsNonRoot
          msg := "Container must run as non-root user"
        }
        
        violation[{"msg": msg}] {
          container := input.review.object.spec.containers[_]
          container.securityContext.allowPrivilegeEscalation == true
          msg := "Container must not allow privilege escalation"
        }
        
        violation[{"msg": msg}] {
          container := input.review.object.spec.containers[_]
          not container.securityContext.readOnlyRootFilesystem
          msg := "Container must have read-only root filesystem"
        }
---
apiVersion: constraints.gatekeeper.sh/v1beta1
kind: RequireSecurityContext
metadata:
  name: must-have-security-context
spec:
  match:
    kinds:
      - apiGroups: ["apps"]
        kinds: ["Deployment"]
    namespaces: ["secure-production"]
  parameters: {}
```

## Best Practices

### Cluster Configuration
- **Node Groups:** Use managed node groups for easier maintenance and updates
- **Fargate:** Use for serverless workloads that don't require persistent storage
- **Spot Instances:** Implement for cost-effective, fault-tolerant workloads
- **Multi-AZ:** Deploy across multiple availability zones for high availability
- **Instance Types:** Use latest generation instances (m6i, c6i) for better performance and cost
- **Cluster Autoscaler:** Configure with appropriate scaling policies and instance diversity

### Security Best Practices
- **IRSA:** Use IAM Roles for Service Accounts for fine-grained permissions
- **Private Endpoints:** Enable private endpoint access and restrict public access
- **Pod Security:** Implement Pod Security Standards and Network Policies
- **Image Scanning:** Enable ECR vulnerability scanning for container images
- **Secrets Management:** Use AWS Secrets Manager or External Secrets Operator
- **Network Policies:** Implement default-deny network policies with explicit allow rules
- **OPA Gatekeeper:** Use admission controllers for policy enforcement

### Operational Excellence
- **GitOps:** Implement GitOps workflows with ArgoCD or Flux
- **Monitoring:** Deploy comprehensive monitoring with Prometheus and Grafana
- **Logging:** Enable control plane logging and structured application logging
- **Backup:** Implement backup strategies for persistent data and cluster configurations
- **Disaster Recovery:** Test and automate disaster recovery procedures
- **Chaos Engineering:** Regular fault injection testing with tools like Chaos Monkey

### Performance Optimization
- **Resource Management:** Set appropriate requests and limits for all containers
- **Horizontal Pod Autoscaling:** Configure HPA with multiple metrics (CPU, memory, custom)
- **Vertical Pod Autoscaling:** Use VPA for right-sizing recommendations
- **Node Affinity:** Use node affinity and anti-affinity for optimal workload placement
- **Topology Spread Constraints:** Ensure even distribution across zones and nodes

### Cost Optimization
- **Right-sizing:** Regularly review and optimize resource requests and limits
- **Cluster Autoscaler:** Implement automatic node scaling based on demand
- **Spot Instances:** Use spot instances for non-critical workloads (up to 70% savings)
- **Resource Quotas:** Implement namespace-level resource quotas and limits
- **Scheduled Scaling:** Use scheduled autoscaling for predictable workload patterns
- **Karpenter:** Consider Karpenter for more efficient and faster node provisioning

### Sustainability
- **Graviton Instances:** Use ARM-based Graviton instances for better energy efficiency
- **Right-sizing:** Optimize resource allocation to reduce waste
- **Cluster Consolidation:** Consolidate workloads to improve resource utilization
- **Green Regions:** Deploy in regions with higher renewable energy usage