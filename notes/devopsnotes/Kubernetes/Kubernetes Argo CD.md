Argo CD is a declarative, GitOps continuous delivery tool for Kubernetes.  
It continuously monitors Git repositories containing Kubernetes manifests (or Helm charts, Kustomize, etc.) and automatically applies changes to Kubernetes clusters, ensuring that the cluster state matches the desired state defined in Git.  

Argo CD supports version control, automated rollbacks, multi-cluster deployments, and integrates with Kubernetes RBAC.

Argo CD can be installed via manifests, Helm charts, or through the Argo CD Operator which manages Argo CD declaratively on the cluster.
## Components

- **Application:** Represents a deployment target with source repo and destination cluster/namespace  
- **Repository:** Git or Helm repository with manifests  
- **Sync:** Operation to apply changes from Git to cluster  
- **UI:** Web interface for visualizing applications, sync status, logs  
- **CLI:** Command line tool for managing Argo CD  
- **API Server:** Backend for requests and sync operations 
- **Controller:** Monitors applications and Git repo for changes  
- **Argo CD Operator:** Kubernetes Operator to install and manage Argo CD instances  
## Argo CD Operator

The Argo CD Operator simplifies installation and lifecycle management of Argo CD on Kubernetes.  
It manages upgrades, configuration, and scaling via the `ArgoCD` custom resource.

### Key features

- Declarative Argo CD management via `ArgoCD` CR  
- Automated upgrades and lifecycle hooks  
- Simplifies multi-environment and multi-cluster management  
- Integrates with Operator Lifecycle Manager (OLM)  
- Supports customization of Argo CD components (API server, repo server, Dex, etc.)  
## Installing Argo CD Operator

```bash
kubectl create namespace argocd
kubectl apply -f https://raw.githubusercontent.com/argoproj/argo-operator/stable/deploy/argo-operator.yaml
```

## Argo CD Resource to deploy Argo CD

```yaml
apiVersion: argoproj.io/v1alpha1
kind: ArgoCD
metadata:
  name: example-argocd
  namespace: argocd
spec:
  server:
    replicas: 2
  dex:
    enabled: true
  repo:
    timeoutSeconds: 20
  applicationController:
    resourceCustomizations: {}

```
## Argo CD Commands

```bash
argocd login <ARGOCD_SERVER> # Login to Argo CD server
argocd logout <ARGOCD_SERVER> # Logout from Argo CD server

# App management

argocd app list # List all applications
argocd app get <APP_NAME> # Get detailed status of an application
argocd app create <APP_NAME> # Create a new application
argocd app delete <APP_NAME> # Delete an application
argocd app sync <APP_NAME> # Synchronize app state from Git to cluster (deploy)
argocd app diff <APP_NAME> # Show diff between desired and live state
argocd app wait <APP_NAME> # Wait for app operation to complete
argocd app rollback <APP_NAME> <REVISION> # Rollback app to a previous revision
argocd app history <APP_NAME> # Show sync and deployment history

# Project management

argocd proj list # List all projects
argocd proj get <PROJECT_NAME> # Show project details
argocd proj create <PROJECT_NAME> # Create a new project
argocd proj delete <PROJECT_NAME> # Delete a project

# Repository management

argocd repo list # List configured Git repositories
argocd repo add <REPO_URL> # Add a new Git repository
argocd repo rm <REPO_URL> # Remove a Git repository

# Cluster management

argocd cluster list # List connected Kubernetes clusters
argocd cluster add <CONTEXT_NAME> # Add a Kubernetes cluster to Argo CD
argocd cluster rm <CONTEXT_NAME> # Remove a Kubernetes cluster from Argo CD

# User & account management

argocd account list # List Argo CD accounts/users
argocd account get <ACCOUNT> # Get details of an account
argocd account update-password # Change password for current account

# Sync & health

argocd app status <APP_NAME> # Show sync and health status of app
argocd app sync <APP_NAME> # Trigger sync (deploy) of application
argocd app wait <APP_NAME> # Wait for sync operation to finish
argocd app diff <APP_NAME> # Show differences between desired and live state

# Miscellaneous

argocd version # Show Argo CD client and server versions
argocd context # Show current Argo CD context (server)
argocd help # Show help for argocd CLI
```

