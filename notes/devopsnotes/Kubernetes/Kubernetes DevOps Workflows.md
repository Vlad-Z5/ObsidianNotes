# Kubernetes DevOps Workflows

**DevOps Workflows in Kubernetes** integrate continuous integration, continuous deployment, infrastructure as code, and automated testing to create robust, scalable, and maintainable software delivery pipelines.

## CI/CD Pipeline Integration

### GitOps Workflow Architecture

#### Complete GitOps Pipeline
```yaml
# GitOps repository structure
my-app-gitops/
├── applications/
│   ├── dev/
│   │   ├── deployment.yaml
│   │   ├── service.yaml
│   │   └── configmap.yaml
│   ├── staging/
│   │   ├── deployment.yaml
│   │   ├── service.yaml
│   │   └── configmap.yaml
│   └── production/
│       ├── deployment.yaml
│       ├── service.yaml
│       └── configmap.yaml
├── infrastructure/
│   ├── namespaces/
│   ├── rbac/
│   ├── network-policies/
│   └── monitoring/
└── environments/
    ├── dev/
    ├── staging/
    └── production/
```

#### ArgoCD Application Set for Multi-Environment
```yaml
# Application set for environment promotion
apiVersion: argoproj.io/v1alpha1
kind: ApplicationSet
metadata:
  name: microservice-apps
  namespace: argocd
spec:
  generators:
  - list:
      elements:
      - env: dev
        cluster: dev-cluster
        revision: HEAD
        replicas: "1"
      - env: staging
        cluster: staging-cluster
        revision: release-candidate
        replicas: "2"
      - env: production
        cluster: prod-cluster
        revision: stable
        replicas: "3"
  template:
    metadata:
      name: 'myapp-{{env}}'
      labels:
        environment: '{{env}}'
    spec:
      project: default
      source:
        repoURL: https://github.com/company/app-manifests
        targetRevision: '{{revision}}'
        path: 'applications/{{env}}'
        kustomize:
          images:
          - 'myapp=myregistry/myapp:{{revision}}'
      destination:
        server: '{{cluster}}'
        namespace: 'myapp-{{env}}'
      syncPolicy:
        automated:
          prune: true
          selfHeal: true
          allowEmpty: false
        syncOptions:
        - CreateNamespace=true
        - PrunePropagationPolicy=foreground
      revisionHistoryLimit: 10
```

### GitHub Actions CI/CD Pipeline

#### Complete Workflow Configuration
```yaml
# .github/workflows/ci-cd.yml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
    tags: ['v*']
  pull_request:
    branches: [main]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}
  KUBECONFIG_FILE: ${{ secrets.KUBECONFIG }}

jobs:
  # Unit and Integration Tests
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3

    - name: Setup Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '18'
        cache: 'npm'

    - name: Install dependencies
      run: npm ci

    - name: Run unit tests
      run: npm run test:unit

    - name: Run integration tests
      run: npm run test:integration

    - name: Upload test results
      uses: actions/upload-artifact@v3
      if: always()
      with:
        name: test-results
        path: |
          coverage/
          test-results.xml

  # Security Scanning
  security:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3

    - name: Run Trivy vulnerability scanner
      uses: aquasecurity/trivy-action@master
      with:
        scan-type: 'fs'
        scan-ref: '.'
        format: 'sarif'
        output: 'trivy-results.sarif'

    - name: Upload Trivy scan results
      uses: github/codeql-action/upload-sarif@v2
      with:
        sarif_file: 'trivy-results.sarif'

  # Build and Push Container Image
  build:
    needs: [test, security]
    runs-on: ubuntu-latest
    outputs:
      image-digest: ${{ steps.build.outputs.digest }}
      image-tag: ${{ steps.meta.outputs.tags }}
    steps:
    - name: Checkout
      uses: actions/checkout@v3

    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v2

    - name: Log in to Container Registry
      uses: docker/login-action@v2
      with:
        registry: ${{ env.REGISTRY }}
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}

    - name: Extract metadata
      id: meta
      uses: docker/metadata-action@v4
      with:
        images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
        tags: |
          type=ref,event=branch
          type=ref,event=pr
          type=semver,pattern={{version}}
          type=semver,pattern={{major}}.{{minor}}
          type=sha,prefix={{branch}}-

    - name: Build and push
      id: build
      uses: docker/build-push-action@v4
      with:
        context: .
        platforms: linux/amd64,linux/arm64
        push: true
        tags: ${{ steps.meta.outputs.tags }}
        labels: ${{ steps.meta.outputs.labels }}
        cache-from: type=gha
        cache-to: type=gha,mode=max

  # Deploy to Development
  deploy-dev:
    if: github.ref == 'refs/heads/develop'
    needs: build
    runs-on: ubuntu-latest
    environment: development
    steps:
    - name: Checkout GitOps repo
      uses: actions/checkout@v3
      with:
        repository: company/app-gitops
        token: ${{ secrets.GITOPS_TOKEN }}
        path: gitops

    - name: Update development manifests
      run: |
        cd gitops
        sed -i "s|image: .*|image: ${{ needs.build.outputs.image-tag }}|" applications/dev/deployment.yaml
        git config user.name "GitHub Actions"
        git config user.email "actions@github.com"
        git add applications/dev/deployment.yaml
        git commit -m "Update dev image to ${{ needs.build.outputs.image-tag }}"
        git push

  # Deploy to Staging
  deploy-staging:
    if: startsWith(github.ref, 'refs/tags/v')
    needs: build
    runs-on: ubuntu-latest
    environment: staging
    steps:
    - name: Checkout GitOps repo
      uses: actions/checkout@v3
      with:
        repository: company/app-gitops
        token: ${{ secrets.GITOPS_TOKEN }}
        path: gitops

    - name: Update staging manifests
      run: |
        cd gitops
        sed -i "s|image: .*|image: ${{ needs.build.outputs.image-tag }}|" applications/staging/deployment.yaml
        git config user.name "GitHub Actions"
        git config user.email "actions@github.com"
        git add applications/staging/deployment.yaml
        git commit -m "Update staging image to ${{ needs.build.outputs.image-tag }}"
        git push

    - name: Run staging tests
      run: |
        # Wait for deployment to be ready
        kubectl wait --for=condition=available --timeout=300s deployment/myapp -n myapp-staging

        # Run smoke tests
        kubectl run staging-test --rm -i --restart=Never \
          --image=postman/newman \
          -- run /tests/staging-tests.json \
          --environment /tests/staging-env.json

  # Production Deployment (Manual Approval)
  deploy-production:
    if: startsWith(github.ref, 'refs/tags/v')
    needs: [build, deploy-staging]
    runs-on: ubuntu-latest
    environment: production
    steps:
    - name: Checkout GitOps repo
      uses: actions/checkout@v3
      with:
        repository: company/app-gitops
        token: ${{ secrets.GITOPS_TOKEN }}
        path: gitops

    - name: Create production deployment PR
      run: |
        cd gitops
        git checkout -b "deploy-prod-${{ github.sha }}"
        sed -i "s|image: .*|image: ${{ needs.build.outputs.image-tag }}|" applications/production/deployment.yaml
        git config user.name "GitHub Actions"
        git config user.email "actions@github.com"
        git add applications/production/deployment.yaml
        git commit -m "Deploy to production: ${{ needs.build.outputs.image-tag }}"
        git push origin "deploy-prod-${{ github.sha }}"

        # Create PR for manual review
        gh pr create \
          --title "Production Deployment: ${{ needs.build.outputs.image-tag }}" \
          --body "Automated production deployment for release ${{ github.ref_name }}" \
          --base main \
          --head "deploy-prod-${{ github.sha }}"
```

### Jenkins Pipeline Integration

#### Jenkinsfile for Kubernetes Deployment
```groovy
// Jenkinsfile
pipeline {
    agent {
        kubernetes {
            yaml """
                apiVersion: v1
                kind: Pod
                spec:
                  containers:
                  - name: docker
                    image: docker:20.10.12-dind
                    securityContext:
                      privileged: true
                    volumeMounts:
                    - name: docker-sock
                      mountPath: /var/run/docker.sock
                  - name: kubectl
                    image: bitnami/kubectl:latest
                    command:
                    - cat
                    tty: true
                  - name: helm
                    image: alpine/helm:latest
                    command:
                    - cat
                    tty: true
                  volumes:
                  - name: docker-sock
                    hostPath:
                      path: /var/run/docker.sock
            """
        }
    }

    environment {
        DOCKER_REGISTRY = 'myregistry.company.com'
        IMAGE_NAME = 'myapp'
        KUBECONFIG = credentials('kubeconfig')
        DOCKER_CREDENTIALS = credentials('docker-registry-creds')
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
                script {
                    env.GIT_COMMIT_SHORT = sh(
                        script: 'git rev-parse --short HEAD',
                        returnStdout: true
                    ).trim()
                    env.IMAGE_TAG = "${env.BRANCH_NAME}-${env.GIT_COMMIT_SHORT}-${env.BUILD_NUMBER}"
                }
            }
        }

        stage('Test') {
            parallel {
                stage('Unit Tests') {
                    steps {
                        container('docker') {
                            sh '''
                                docker build --target test -t ${IMAGE_NAME}:test .
                                docker run --rm ${IMAGE_NAME}:test npm test
                            '''
                        }
                    }
                    post {
                        always {
                            publishTestResults testResultsPattern: 'test-results.xml'
                            publishCoverage adapters: [
                                istanbulCoberturaAdapter('coverage/cobertura-coverage.xml')
                            ]
                        }
                    }
                }

                stage('Security Scan') {
                    steps {
                        container('docker') {
                            sh '''
                                docker run --rm -v $(pwd):/app -w /app \
                                  aquasec/trivy:latest fs --format json --output trivy-report.json .
                            '''
                        }
                        archiveArtifacts artifacts: 'trivy-report.json'
                    }
                }
            }
        }

        stage('Build Image') {
            steps {
                container('docker') {
                    sh '''
                        echo $DOCKER_CREDENTIALS_PSW | docker login -u $DOCKER_CREDENTIALS_USR --password-stdin $DOCKER_REGISTRY
                        docker build -t $DOCKER_REGISTRY/$IMAGE_NAME:$IMAGE_TAG .
                        docker push $DOCKER_REGISTRY/$IMAGE_NAME:$IMAGE_TAG
                    '''
                }
            }
        }

        stage('Deploy to Development') {
            when {
                branch 'develop'
            }
            steps {
                container('helm') {
                    sh '''
                        helm upgrade --install myapp-dev ./helm/myapp \
                          --namespace myapp-dev \
                          --create-namespace \
                          --set image.tag=$IMAGE_TAG \
                          --set environment=development \
                          --set replicaCount=1 \
                          --wait --timeout=5m
                    '''
                }
            }
        }

        stage('Deploy to Staging') {
            when {
                anyOf {
                    branch 'main'
                    tag 'v*'
                }
            }
            steps {
                container('helm') {
                    sh '''
                        helm upgrade --install myapp-staging ./helm/myapp \
                          --namespace myapp-staging \
                          --create-namespace \
                          --set image.tag=$IMAGE_TAG \
                          --set environment=staging \
                          --set replicaCount=2 \
                          --wait --timeout=5m
                    '''
                }

                // Run integration tests
                container('kubectl') {
                    sh '''
                        kubectl wait --for=condition=available --timeout=300s \
                          deployment/myapp-staging -n myapp-staging

                        kubectl run integration-test --rm -i --restart=Never \
                          --image=postman/newman:alpine \
                          -- run /tests/integration-tests.json
                    '''
                }
            }
        }

        stage('Deploy to Production') {
            when {
                tag 'v*'
            }
            steps {
                input message: 'Deploy to production?', ok: 'Deploy',
                      parameters: [choice(name: 'DEPLOYMENT_STRATEGY',
                                         choices: ['rolling', 'blue-green', 'canary'],
                                         description: 'Deployment strategy')]

                script {
                    if (params.DEPLOYMENT_STRATEGY == 'blue-green') {
                        container('helm') {
                            sh '''
                                # Blue-Green deployment
                                helm upgrade --install myapp-green ./helm/myapp \
                                  --namespace myapp-production \
                                  --create-namespace \
                                  --set image.tag=$IMAGE_TAG \
                                  --set environment=production \
                                  --set replicaCount=3 \
                                  --set service.selector.version=green \
                                  --wait --timeout=10m

                                # Switch traffic after verification
                                kubectl patch service myapp -n myapp-production \
                                  -p '{"spec":{"selector":{"version":"green"}}}'
                            '''
                        }
                    } else {
                        container('helm') {
                            sh '''
                                helm upgrade --install myapp-prod ./helm/myapp \
                                  --namespace myapp-production \
                                  --create-namespace \
                                  --set image.tag=$IMAGE_TAG \
                                  --set environment=production \
                                  --set replicaCount=3 \
                                  --wait --timeout=10m
                            '''
                        }
                    }
                }
            }
        }
    }

    post {
        always {
            container('kubectl') {
                sh 'kubectl get pods -A'
            }
        }
        success {
            slackSend channel: '#deployments',
                     color: 'good',
                     message: "✅ Deployment successful: ${env.JOB_NAME} - ${env.BUILD_NUMBER}"
        }
        failure {
            slackSend channel: '#deployments',
                     color: 'danger',
                     message: "❌ Deployment failed: ${env.JOB_NAME} - ${env.BUILD_NUMBER}"
        }
    }
}
```

## Infrastructure as Code

### Terraform Kubernetes Provider

#### Complete EKS Cluster Setup
```hcl
# terraform/main.tf
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.23"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.10"
    }
  }

  backend "s3" {
    bucket = "company-terraform-state"
    key    = "kubernetes/terraform.tfstate"
    region = "us-west-2"
  }
}

# VPC Configuration
module "vpc" {
  source = "terraform-aws-modules/vpc/aws"

  name = "${var.cluster_name}-vpc"
  cidr = var.vpc_cidr

  azs             = var.availability_zones
  private_subnets = var.private_subnet_cidrs
  public_subnets  = var.public_subnet_cidrs

  enable_nat_gateway   = true
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    "kubernetes.io/cluster/${var.cluster_name}" = "shared"
    Environment = var.environment
  }
}

# EKS Cluster
module "eks" {
  source = "terraform-aws-modules/eks/aws"

  cluster_name    = var.cluster_name
  cluster_version = var.kubernetes_version

  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets

  # Cluster endpoint configuration
  cluster_endpoint_public_access       = true
  cluster_endpoint_private_access      = true
  cluster_endpoint_public_access_cidrs = var.allowed_cidr_blocks

  # Cluster logging
  cluster_enabled_log_types = ["api", "audit", "authenticator", "controllerManager", "scheduler"]

  # Node groups
  eks_managed_node_groups = {
    general = {
      name = "general"

      instance_types = ["t3.medium"]
      capacity_type  = "ON_DEMAND"

      min_size     = 1
      max_size     = 10
      desired_size = 3

      subnet_ids = module.vpc.private_subnets

      k8s_labels = {
        Environment = var.environment
        NodeGroup   = "general"
      }

      tags = {
        ExtraTag = "general-nodes"
      }
    }

    spot = {
      name = "spot"

      instance_types = ["t3.medium", "t3.large"]
      capacity_type  = "SPOT"

      min_size     = 0
      max_size     = 5
      desired_size = 2

      subnet_ids = module.vpc.private_subnets

      k8s_labels = {
        Environment = var.environment
        NodeGroup   = "spot"
      }

      taints = {
        spot = {
          key    = "spot"
          value  = "true"
          effect = "NO_SCHEDULE"
        }
      }
    }
  }

  # Cluster add-ons
  cluster_addons = {
    coredns = {
      most_recent = true
    }
    kube-proxy = {
      most_recent = true
    }
    vpc-cni = {
      most_recent = true
    }
    aws-ebs-csi-driver = {
      most_recent = true
    }
  }

  tags = {
    Environment = var.environment
  }
}

# Kubernetes provider configuration
provider "kubernetes" {
  host                   = module.eks.cluster_endpoint
  cluster_ca_certificate = base64decode(module.eks.cluster_certificate_authority_data)

  exec {
    api_version = "client.authentication.k8s.io/v1beta1"
    command     = "aws"
    args        = ["eks", "get-token", "--cluster-name", module.eks.cluster_name]
  }
}

provider "helm" {
  kubernetes {
    host                   = module.eks.cluster_endpoint
    cluster_ca_certificate = base64decode(module.eks.cluster_certificate_authority_data)

    exec {
      api_version = "client.authentication.k8s.io/v1beta1"
      command     = "aws"
      args        = ["eks", "get-token", "--cluster-name", module.eks.cluster_name]
    }
  }
}

# Install core applications
module "cluster_applications" {
  source = "./modules/cluster-applications"

  cluster_name = module.eks.cluster_name
  environment  = var.environment

  depends_on = [module.eks]
}
```

#### Cluster Applications Module
```hcl
# terraform/modules/cluster-applications/main.tf

# AWS Load Balancer Controller
resource "helm_release" "aws_load_balancer_controller" {
  name       = "aws-load-balancer-controller"
  repository = "https://aws.github.io/eks-charts"
  chart      = "aws-load-balancer-controller"
  namespace  = "kube-system"
  version    = "1.6.0"

  set {
    name  = "clusterName"
    value = var.cluster_name
  }

  set {
    name  = "serviceAccount.create"
    value = "false"
  }

  set {
    name  = "serviceAccount.name"
    value = "aws-load-balancer-controller"
  }

  depends_on = [kubernetes_service_account.aws_load_balancer_controller]
}

# External DNS
resource "helm_release" "external_dns" {
  name       = "external-dns"
  repository = "https://kubernetes-sigs.github.io/external-dns/"
  chart      = "external-dns"
  namespace  = "kube-system"
  version    = "1.13.0"

  set {
    name  = "provider"
    value = "aws"
  }

  set {
    name  = "aws.zoneType"
    value = "public"
  }

  set {
    name  = "txtOwnerId"
    value = var.cluster_name
  }

  set {
    name  = "domainFilters[0]"
    value = var.domain_name
  }
}

# Cluster Autoscaler
resource "helm_release" "cluster_autoscaler" {
  name       = "cluster-autoscaler"
  repository = "https://kubernetes.github.io/autoscaler"
  chart      = "cluster-autoscaler"
  namespace  = "kube-system"
  version    = "9.29.0"

  set {
    name  = "autoDiscovery.clusterName"
    value = var.cluster_name
  }

  set {
    name  = "awsRegion"
    value = data.aws_region.current.name
  }

  set {
    name  = "rbac.serviceAccount.create"
    value = "false"
  }

  set {
    name  = "rbac.serviceAccount.name"
    value = "cluster-autoscaler"
  }
}

# Metrics Server
resource "helm_release" "metrics_server" {
  name       = "metrics-server"
  repository = "https://kubernetes-sigs.github.io/metrics-server/"
  chart      = "metrics-server"
  namespace  = "kube-system"
  version    = "3.11.0"

  set {
    name  = "args[0]"
    value = "--kubelet-insecure-tls"
  }
}

# ArgoCD
resource "kubernetes_namespace" "argocd" {
  metadata {
    name = "argocd"

    labels = {
      name        = "argocd"
      environment = var.environment
    }
  }
}

resource "helm_release" "argocd" {
  name       = "argocd"
  repository = "https://argoproj.github.io/argo-helm"
  chart      = "argo-cd"
  namespace  = kubernetes_namespace.argocd.metadata[0].name
  version    = "5.45.0"

  values = [
    yamlencode({
      global = {
        domain = "argocd.${var.domain_name}"
      }

      server = {
        extraArgs = [
          "--insecure"
        ]

        service = {
          type = "ClusterIP"
        }

        ingress = {
          enabled = true
          ingressClassName = "alb"
          annotations = {
            "alb.ingress.kubernetes.io/scheme"      = "internet-facing"
            "alb.ingress.kubernetes.io/target-type" = "ip"
            "alb.ingress.kubernetes.io/backend-protocol" = "HTTP"
            "external-dns.alpha.kubernetes.io/hostname" = "argocd.${var.domain_name}"
          }
          hosts = ["argocd.${var.domain_name}"]
        }
      }

      configs = {
        secret = {
          argocdServerAdminPassword = bcrypt(var.argocd_admin_password)
        }

        cm = {
          "application.instanceLabelKey" = "argocd.argoproj.io/instance"

          repositories = yamlencode([
            {
              type = "git"
              url  = var.gitops_repo_url
            }
          ])
        }
      }
    })
  ]

  depends_on = [kubernetes_namespace.argocd]
}
```

### Pulumi Infrastructure

#### TypeScript Pulumi Configuration
```typescript
// infrastructure/index.ts
import * as pulumi from "@pulumi/pulumi";
import * as awsx from "@pulumi/awsx";
import * as eks from "@pulumi/eks";
import * as k8s from "@pulumi/kubernetes";

const config = new pulumi.Config();
const clusterName = config.require("clusterName");
const environment = config.require("environment");

// Create VPC
const vpc = new awsx.ec2.Vpc(`${clusterName}-vpc`, {
    cidrBlock: "10.0.0.0/16",
    enableDnsHostnames: true,
    enableDnsSupport: true,
    tags: {
        Name: `${clusterName}-vpc`,
        Environment: environment,
    },
});

// Create EKS cluster
const cluster = new eks.Cluster(clusterName, {
    vpcId: vpc.vpcId,
    subnetIds: vpc.privateSubnetIds,
    instanceType: "t3.medium",
    desiredCapacity: 3,
    minSize: 1,
    maxSize: 10,
    enabledClusterLogTypes: ["api", "audit", "authenticator"],
    tags: {
        Environment: environment,
    },
});

// Create Kubernetes provider
const k8sProvider = new k8s.Provider("k8s-provider", {
    kubeconfig: cluster.kubeconfig,
});

// Install ArgoCD
const argoCDNamespace = new k8s.core.v1.Namespace("argocd", {
    metadata: {
        name: "argocd",
        labels: {
            name: "argocd",
            environment: environment,
        },
    },
}, { provider: k8sProvider });

const argoCD = new k8s.helm.v3.Release("argocd", {
    chart: "argo-cd",
    version: "5.45.0",
    repositoryOpts: {
        repo: "https://argoproj.github.io/argo-helm",
    },
    namespace: argoCDNamespace.metadata.name,
    values: {
        global: {
            domain: `argocd.${config.require("domainName")}`,
        },
        server: {
            service: {
                type: "LoadBalancer",
                annotations: {
                    "service.beta.kubernetes.io/aws-load-balancer-type": "nlb",
                },
            },
        },
    },
}, { provider: k8sProvider });

// Install monitoring stack
const monitoringNamespace = new k8s.core.v1.Namespace("monitoring", {
    metadata: {
        name: "monitoring",
        labels: {
            name: "monitoring",
            environment: environment,
        },
    },
}, { provider: k8sProvider });

const prometheus = new k8s.helm.v3.Release("prometheus", {
    chart: "kube-prometheus-stack",
    version: "51.0.0",
    repositoryOpts: {
        repo: "https://prometheus-community.github.io/helm-charts",
    },
    namespace: monitoringNamespace.metadata.name,
    values: {
        grafana: {
            enabled: true,
            adminPassword: config.requireSecret("grafanaPassword"),
            service: {
                type: "LoadBalancer",
            },
        },
        prometheus: {
            prometheusSpec: {
                retention: "30d",
                storageSpec: {
                    volumeClaimTemplate: {
                        spec: {
                            storageClassName: "gp2",
                            accessModes: ["ReadWriteOnce"],
                            resources: {
                                requests: {
                                    storage: "50Gi",
                                },
                            },
                        },
                    },
                },
            },
        },
    },
}, { provider: k8sProvider });

// Export important values
export const clusterEndpoint = cluster.core.endpoint;
export const kubeconfig = cluster.kubeconfig;
export const vpcId = vpc.vpcId;
export const privateSubnetIds = vpc.privateSubnetIds;
export const publicSubnetIds = vpc.publicSubnetIds;
```

## Automated Testing Strategies

### End-to-End Testing Framework

#### Playwright Kubernetes Testing
```typescript
// tests/e2e/kubernetes.spec.ts
import { test, expect } from '@playwright/test';
import { execSync } from 'child_process';

class KubernetesTestHelper {
    private namespace: string;

    constructor(namespace: string) {
        this.namespace = namespace;
    }

    async deployTestApp(appName: string, image: string) {
        const deployment = `
            apiVersion: apps/v1
            kind: Deployment
            metadata:
              name: ${appName}
              namespace: ${this.namespace}
            spec:
              replicas: 1
              selector:
                matchLabels:
                  app: ${appName}
              template:
                metadata:
                  labels:
                    app: ${appName}
                spec:
                  containers:
                  - name: ${appName}
                    image: ${image}
                    ports:
                    - containerPort: 8080
            ---
            apiVersion: v1
            kind: Service
            metadata:
              name: ${appName}
              namespace: ${this.namespace}
            spec:
              selector:
                app: ${appName}
              ports:
              - protocol: TCP
                port: 80
                targetPort: 8080
        `;

        execSync(`echo '${deployment}' | kubectl apply -f -`);

        // Wait for deployment to be ready
        execSync(`kubectl wait --for=condition=available --timeout=300s deployment/${appName} -n ${this.namespace}`);
    }

    async getServiceEndpoint(serviceName: string): Promise<string> {
        const result = execSync(`kubectl get service ${serviceName} -n ${this.namespace} -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'`);
        return result.toString().trim();
    }

    async cleanup(appName: string) {
        execSync(`kubectl delete deployment,service ${appName} -n ${this.namespace} --ignore-not-found=true`);
    }

    async portForward(serviceName: string, localPort: number, servicePort: number): Promise<() => void> {
        const process = execSync(`kubectl port-forward service/${serviceName} ${localPort}:${servicePort} -n ${this.namespace} &`);

        // Wait for port-forward to be ready
        await new Promise(resolve => setTimeout(resolve, 3000));

        return () => {
            execSync(`pkill -f "kubectl port-forward"`);
        };
    }
}

test.describe('Kubernetes Application Tests', () => {
    let k8sHelper: KubernetesTestHelper;
    const testNamespace = 'e2e-testing';

    test.beforeAll(async () => {
        k8sHelper = new KubernetesTestHelper(testNamespace);

        // Create test namespace
        execSync(`kubectl create namespace ${testNamespace} --dry-run=client -o yaml | kubectl apply -f -`);
    });

    test.afterAll(async () => {
        // Cleanup test namespace
        execSync(`kubectl delete namespace ${testNamespace} --ignore-not-found=true`);
    });

    test('should deploy and access web application', async ({ page }) => {
        const appName = 'test-webapp';
        const image = 'nginx:alpine';

        try {
            // Deploy test application
            await k8sHelper.deployTestApp(appName, image);

            // Set up port forwarding
            const stopPortForward = await k8sHelper.portForward(appName, 8081, 80);

            // Test application
            await page.goto('http://localhost:8081');
            await expect(page.locator('h1')).toContainText('Welcome to nginx!');

            // Test application health
            const response = await page.request.get('http://localhost:8081');
            expect(response.status()).toBe(200);

            // Cleanup
            stopPortForward();
        } finally {
            await k8sHelper.cleanup(appName);
        }
    });

    test('should handle application scaling', async () => {
        const appName = 'test-scaling';
        const image = 'httpd:alpine';

        try {
            await k8sHelper.deployTestApp(appName, image);

            // Scale up
            execSync(`kubectl scale deployment ${appName} --replicas=3 -n ${testNamespace}`);
            execSync(`kubectl wait --for=condition=available --timeout=300s deployment/${appName} -n ${testNamespace}`);

            // Verify scaling
            const replicaCount = execSync(`kubectl get deployment ${appName} -n ${testNamespace} -o jsonpath='{.status.replicas}'`);
            expect(replicaCount.toString().trim()).toBe('3');

            // Scale down
            execSync(`kubectl scale deployment ${appName} --replicas=1 -n ${testNamespace}`);
            execSync(`kubectl wait --for=condition=available --timeout=300s deployment/${appName} -n ${testNamespace}`);

            const scaledDownCount = execSync(`kubectl get deployment ${appName} -n ${testNamespace} -o jsonpath='{.status.replicas}'`);
            expect(scaledDownCount.toString().trim()).toBe('1');
        } finally {
            await k8sHelper.cleanup(appName);
        }
    });

    test('should validate resource limits and requests', async () => {
        const deploymentWithResources = `
            apiVersion: apps/v1
            kind: Deployment
            metadata:
              name: resource-test
              namespace: ${testNamespace}
            spec:
              replicas: 1
              selector:
                matchLabels:
                  app: resource-test
              template:
                metadata:
                  labels:
                    app: resource-test
                spec:
                  containers:
                  - name: resource-test
                    image: nginx:alpine
                    resources:
                      requests:
                        cpu: 100m
                        memory: 128Mi
                      limits:
                        cpu: 200m
                        memory: 256Mi
        `;

        try {
            execSync(`echo '${deploymentWithResources}' | kubectl apply -f -`);
            execSync(`kubectl wait --for=condition=available --timeout=300s deployment/resource-test -n ${testNamespace}`);

            // Verify resource configuration
            const resources = execSync(`kubectl get deployment resource-test -n ${testNamespace} -o jsonpath='{.spec.template.spec.containers[0].resources}'`);
            const resourcesObj = JSON.parse(resources.toString());

            expect(resourcesObj.requests.cpu).toBe('100m');
            expect(resourcesObj.requests.memory).toBe('128Mi');
            expect(resourcesObj.limits.cpu).toBe('200m');
            expect(resourcesObj.limits.memory).toBe('256Mi');
        } finally {
            await k8sHelper.cleanup('resource-test');
        }
    });
});
```

### Load Testing with K6

#### Kubernetes Load Testing Script
```javascript
// tests/load/kubernetes-load.js
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('errors');

export const options = {
  stages: [
    { duration: '2m', target: 10 }, // Ramp up
    { duration: '5m', target: 50 }, // Stay at 50 users
    { duration: '2m', target: 100 }, // Ramp up to 100 users
    { duration: '5m', target: 100 }, // Stay at 100 users
    { duration: '2m', target: 0 }, // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'], // 95% of requests under 500ms
    http_req_failed: ['rate<0.1'], // Error rate under 10%
    errors: ['rate<0.1'],
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8080';

export default function () {
  // Test main application endpoint
  const mainResponse = http.get(`${BASE_URL}/`);
  check(mainResponse, {
    'main page status is 200': (r) => r.status === 200,
    'main page response time < 500ms': (r) => r.timings.duration < 500,
  }) || errorRate.add(1);

  // Test API endpoints
  const apiResponse = http.get(`${BASE_URL}/api/health`);
  check(apiResponse, {
    'health endpoint status is 200': (r) => r.status === 200,
    'health endpoint response time < 200ms': (r) => r.timings.duration < 200,
  }) || errorRate.add(1);

  // Test POST endpoint
  const payload = JSON.stringify({
    name: 'test-user',
    email: 'test@example.com',
  });

  const params = {
    headers: {
      'Content-Type': 'application/json',
    },
  };

  const postResponse = http.post(`${BASE_URL}/api/users`, payload, params);
  check(postResponse, {
    'create user status is 201': (r) => r.status === 201,
    'create user response time < 1000ms': (r) => r.timings.duration < 1000,
  }) || errorRate.add(1);

  sleep(1);
}

export function handleSummary(data) {
  return {
    'load-test-results.json': JSON.stringify(data, null, 2),
    'load-test-summary.html': htmlReport(data),
  };
}

function htmlReport(data) {
  return `
    <!DOCTYPE html>
    <html>
    <head>
        <title>Load Test Results</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .metric { margin: 10px 0; }
            .pass { color: green; }
            .fail { color: red; }
        </style>
    </head>
    <body>
        <h1>Load Test Results</h1>
        <div class="metric">
            <strong>Duration:</strong> ${data.state.testRunDurationMs}ms
        </div>
        <div class="metric">
            <strong>Virtual Users:</strong> ${data.metrics.vus.values.max}
        </div>
        <div class="metric">
            <strong>HTTP Requests:</strong> ${data.metrics.http_reqs.values.count}
        </div>
        <div class="metric">
            <strong>Failed Requests:</strong> ${data.metrics.http_req_failed.values.rate * 100}%
        </div>
        <div class="metric">
            <strong>Avg Response Time:</strong> ${data.metrics.http_req_duration.values.avg}ms
        </div>
        <div class="metric">
            <strong>95th Percentile:</strong> ${data.metrics.http_req_duration.values['p(95)']}ms
        </div>
    </body>
    </html>
  `;
}
```

## Security Integration

### Security Scanning Pipeline

#### Comprehensive Security Workflow
```yaml
# .github/workflows/security.yml
name: Security Scanning

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]
  schedule:
    - cron: '0 2 * * *' # Daily at 2 AM

jobs:
  # Static Application Security Testing (SAST)
  sast:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3

    - name: CodeQL Analysis
      uses: github/codeql-action/init@v2
      with:
        languages: javascript, typescript

    - name: Autobuild
      uses: github/codeql-action/autobuild@v2

    - name: Perform CodeQL Analysis
      uses: github/codeql-action/analyze@v2

    - name: SonarCloud Scan
      uses: SonarSource/sonarcloud-github-action@master
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        SONAR_TOKEN: ${{ secrets.SONAR_TOKEN }}

  # Dependency Scanning
  dependency-scan:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3

    - name: Run Snyk to check for vulnerabilities
      uses: snyk/actions/node@master
      env:
        SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}
      with:
        args: --severity-threshold=high

    - name: Upload results to GitHub Code Scanning
      uses: github/codeql-action/upload-sarif@v2
      with:
        sarif_file: snyk.sarif

  # Container Security Scanning
  container-scan:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3

    - name: Build test image
      run: docker build -t test-image:latest .

    - name: Run Trivy vulnerability scanner
      uses: aquasecurity/trivy-action@master
      with:
        image-ref: 'test-image:latest'
        format: 'sarif'
        output: 'trivy-results.sarif'

    - name: Upload Trivy scan results
      uses: github/codeql-action/upload-sarif@v2
      with:
        sarif_file: 'trivy-results.sarif'

    - name: Run Grype vulnerability scanner
      uses: anchore/scan-action@v3
      with:
        image: "test-image:latest"
        fail-build: true
        severity-cutoff: high

  # Infrastructure Security Scanning
  iac-scan:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3

    - name: Checkov IaC Security Scan
      uses: bridgecrewio/checkov-action@master
      with:
        directory: .
        framework: terraform,kubernetes,dockerfile
        output_format: sarif
        output_file_path: checkov-results.sarif

    - name: Upload Checkov scan results
      uses: github/codeql-action/upload-sarif@v2
      with:
        sarif_file: 'checkov-results.sarif'

  # Kubernetes Security Scanning
  k8s-security:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3

    - name: Kube-score security analysis
      run: |
        wget https://github.com/zegl/kube-score/releases/download/v1.16.1/kube-score_1.16.1_linux_amd64.tar.gz
        tar -xzf kube-score_1.16.1_linux_amd64.tar.gz
        ./kube-score score k8s/*.yaml --output-format json > kube-score-results.json

    - name: Polaris security validation
      run: |
        docker run --rm -v $(pwd):/app quay.io/fairwinds/polaris:latest polaris audit --audit-path /app/k8s --format json > polaris-results.json

    - name: Upload security scan results
      uses: actions/upload-artifact@v3
      with:
        name: security-scan-results
        path: |
          kube-score-results.json
          polaris-results.json

  # Runtime Security Setup
  runtime-security:
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
    - uses: actions/checkout@v3

    - name: Setup kubectl
      uses: azure/setup-kubectl@v3

    - name: Deploy Falco security monitoring
      run: |
        kubectl apply -f - <<EOF
        apiVersion: v1
        kind: Namespace
        metadata:
          name: falco-system
        ---
        apiVersion: apps/v1
        kind: DaemonSet
        metadata:
          name: falco
          namespace: falco-system
        spec:
          selector:
            matchLabels:
              app: falco
          template:
            metadata:
              labels:
                app: falco
            spec:
              hostNetwork: true
              hostPID: true
              containers:
              - name: falco
                image: falcosecurity/falco:latest
                securityContext:
                  privileged: true
                volumeMounts:
                - name: dev
                  mountPath: /host/dev
                - name: proc
                  mountPath: /host/proc
                  readOnly: true
                - name: boot
                  mountPath: /host/boot
                  readOnly: true
                - name: lib-modules
                  mountPath: /host/lib/modules
                  readOnly: true
                - name: usr
                  mountPath: /host/usr
                  readOnly: true
                - name: etc
                  mountPath: /host/etc
                  readOnly: true
              volumes:
              - name: dev
                hostPath:
                  path: /dev
              - name: proc
                hostPath:
                  path: /proc
              - name: boot
                hostPath:
                  path: /boot
              - name: lib-modules
                hostPath:
                  path: /lib/modules
              - name: usr
                hostPath:
                  path: /usr
              - name: etc
                hostPath:
                  path: /etc
        EOF
```

## Monitoring and Observability

### Comprehensive Monitoring Stack

#### Prometheus and Grafana Configuration
```yaml
# monitoring/prometheus-values.yaml
prometheus:
  prometheusSpec:
    retention: 30d
    storageSpec:
      volumeClaimTemplate:
        spec:
          storageClassName: gp2
          accessModes: ["ReadWriteOnce"]
          resources:
            requests:
              storage: 100Gi

    additionalScrapeConfigs:
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
      - source_labels: [__address__, __meta_kubernetes_pod_annotation_prometheus_io_port]
        action: replace
        regex: ([^:]+)(?::\d+)?;(\d+)
        replacement: $1:$2
        target_label: __address__

    - job_name: 'kubernetes-services'
      kubernetes_sd_configs:
      - role: service
      relabel_configs:
      - source_labels: [__meta_kubernetes_service_annotation_prometheus_io_scrape]
        action: keep
        regex: true
      - source_labels: [__meta_kubernetes_service_annotation_prometheus_io_path]
        action: replace
        target_label: __metrics_path__
        regex: (.+)
      - source_labels: [__address__, __meta_kubernetes_service_annotation_prometheus_io_port]
        action: replace
        regex: ([^:]+)(?::\d+)?;(\d+)
        replacement: $1:$2
        target_label: __address__

grafana:
  enabled: true
  adminPassword: ${GRAFANA_ADMIN_PASSWORD}

  persistence:
    enabled: true
    storageClassName: gp2
    size: 10Gi

  grafana.ini:
    server:
      root_url: https://grafana.company.com
    auth.github:
      enabled: true
      allow_sign_up: true
      client_id: ${GITHUB_CLIENT_ID}
      client_secret: ${GITHUB_CLIENT_SECRET}
      scopes: user:email,read:org
      auth_url: https://github.com/login/oauth/authorize
      token_url: https://github.com/login/oauth/access_token
      allowed_organizations: company

  datasources:
    datasources.yaml:
      apiVersion: 1
      datasources:
      - name: Prometheus
        type: prometheus
        url: http://prometheus-server
        access: proxy
        isDefault: true
      - name: Loki
        type: loki
        url: http://loki:3100
        access: proxy
      - name: Jaeger
        type: jaeger
        url: http://jaeger-query:16686
        access: proxy

  dashboardProviders:
    dashboardproviders.yaml:
      apiVersion: 1
      providers:
      - name: 'default'
        orgId: 1
        folder: ''
        type: file
        disableDeletion: false
        editable: true
        options:
          path: /var/lib/grafana/dashboards/default

  dashboards:
    default:
      kubernetes-cluster:
        gnetId: 7249
        revision: 1
        datasource: Prometheus
      kubernetes-pods:
        gnetId: 6417
        revision: 1
        datasource: Prometheus
      nginx-ingress:
        gnetId: 9614
        revision: 1
        datasource: Prometheus

alertmanager:
  alertmanagerSpec:
    storage:
      volumeClaimTemplate:
        spec:
          storageClassName: gp2
          accessModes: ["ReadWriteOnce"]
          resources:
            requests:
              storage: 10Gi

  config:
    global:
      slack_api_url: ${SLACK_WEBHOOK_URL}

    route:
      group_by: ['alertname', 'cluster', 'service']
      group_wait: 10s
      group_interval: 10s
      repeat_interval: 1h
      receiver: 'web.hook'
      routes:
      - match:
          severity: critical
        receiver: 'critical-alerts'
      - match:
          severity: warning
        receiver: 'warning-alerts'

    receivers:
    - name: 'web.hook'
      slack_configs:
      - channel: '#alerts'
        title: 'Kubernetes Alert'
        text: 'Summary: {{ .CommonAnnotations.summary }}\nDescription: {{ .CommonAnnotations.description }}'

    - name: 'critical-alerts'
      slack_configs:
      - channel: '#critical-alerts'
        title: 'CRITICAL: {{ .GroupLabels.alertname }}'
        text: 'Summary: {{ .CommonAnnotations.summary }}\nDescription: {{ .CommonAnnotations.description }}'
        send_resolved: true

    - name: 'warning-alerts'
      slack_configs:
      - channel: '#warnings'
        title: 'Warning: {{ .GroupLabels.alertname }}'
        text: 'Summary: {{ .CommonAnnotations.summary }}\nDescription: {{ .CommonAnnotations.description }}'
```

#### Application Performance Monitoring
```yaml
# monitoring/apm-stack.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: apm
  labels:
    name: apm

---
# Jaeger Tracing
apiVersion: jaegertracing.io/v1
kind: Jaeger
metadata:
  name: jaeger
  namespace: apm
spec:
  strategy: production
  storage:
    type: elasticsearch
    elasticsearch:
      nodeCount: 3
      storage:
        storageClassName: gp2
        size: 50Gi

---
# OpenTelemetry Collector
apiVersion: opentelemetry.io/v1alpha1
kind: OpenTelemetryCollector
metadata:
  name: otel-collector
  namespace: apm
spec:
  config: |
    receivers:
      otlp:
        protocols:
          grpc:
            endpoint: 0.0.0.0:4317
          http:
            endpoint: 0.0.0.0:4318
      jaeger:
        protocols:
          grpc:
            endpoint: 0.0.0.0:14250
          thrift_http:
            endpoint: 0.0.0.0:14268
          thrift_compact:
            endpoint: 0.0.0.0:6831
      prometheus:
        config:
          scrape_configs:
          - job_name: 'otel-collector'
            scrape_interval: 10s
            static_configs:
            - targets: ['0.0.0.0:8888']

    processors:
      batch:
        timeout: 1s
        send_batch_size: 1024
      memory_limiter:
        limit_mib: 512
      resource:
        attributes:
        - key: environment
          value: ${ENVIRONMENT}
          action: insert

    exporters:
      jaeger:
        endpoint: jaeger-collector.apm.svc.cluster.local:14250
        tls:
          insecure: true
      prometheus:
        endpoint: "0.0.0.0:8889"
      logging:
        loglevel: debug

    service:
      pipelines:
        traces:
          receivers: [otlp, jaeger]
          processors: [memory_limiter, resource, batch]
          exporters: [jaeger]
        metrics:
          receivers: [otlp, prometheus]
          processors: [memory_limiter, resource, batch]
          exporters: [prometheus]

      extensions: [health_check]

---
# Application instrumentation example
apiVersion: apps/v1
kind: Deployment
metadata:
  name: sample-app
  namespace: default
spec:
  replicas: 3
  selector:
    matchLabels:
      app: sample-app
  template:
    metadata:
      labels:
        app: sample-app
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8080"
        prometheus.io/path: "/metrics"
    spec:
      containers:
      - name: app
        image: sample-app:latest
        ports:
        - containerPort: 8080
        env:
        - name: OTEL_EXPORTER_OTLP_ENDPOINT
          value: "http://otel-collector.apm.svc.cluster.local:4318"
        - name: OTEL_SERVICE_NAME
          value: "sample-app"
        - name: OTEL_RESOURCE_ATTRIBUTES
          value: "service.name=sample-app,service.version=1.0.0,environment=production"
        resources:
          requests:
            cpu: 100m
            memory: 128Mi
          limits:
            cpu: 500m
            memory: 512Mi
```

This comprehensive Kubernetes DevOps Workflows file covers the essential aspects of implementing robust CI/CD pipelines, infrastructure as code, automated testing, security integration, and monitoring in Kubernetes environments. Each section provides practical, production-ready examples that can be adapted to specific organizational needs.