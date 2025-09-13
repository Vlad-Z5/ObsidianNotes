# Namespace & Resource Quota Strategy

Namespaces and resource quotas ensure logical separation, fair resource allocation, and operational stability in Kubernetes clusters, especially in multi-tenant environments.

## 1. Core Concepts

**Namespace:** Logical partition within a cluster to isolate workloads, resources, and permissions.

**Resource Quota:** Limits on CPU, memory, and object counts (pods, services, configmaps) per namespace.

**LimitRange:** Sets default/min/max CPU and memory for containers within a namespace.

**Pod Disruption Budget (PDB):** Ensures minimum number of pods remain available during maintenance or scaling.

**Goal:** Prevent one team or workload from consuming excessive resources, maintain isolation, and enforce governance.

## 2. Patterns & Best Practices

### A. Namespace Design

One namespace per team, project, or environment.

Use clear naming conventions: teamA-dev, teamA-prod.

Apply labels and annotations for cost allocation, auditing, and observability.

### B. Resource Quotas

Define hard limits on CPU, memory, and object counts.

**Example:**

```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: team-a-quota
  namespace: team-a
spec:
  hard:
    requests.cpu: "4"
    requests.memory: 8Gi
    limits.cpu: "8"
    limits.memory: 16Gi
    pods: "10"
```

Prevents noisy neighbor issues and ensures cluster stability.

### C. LimitRange

Set default requests/limits for containers in the namespace.

Helps enforce consistency and avoid pod eviction due to overcommit.

### D. Pod Disruption Budgets (PDB)

Ensure high availability during node replacement or cluster upgrades.

Example: At least 80% of replicas remain available during disruptions.

### E. Multi-Tenancy Governance

Combine namespace, quota, and RBAC to isolate teams.

Enforce admission policies (Kyverno/OPA) to require quotas on new namespaces.

## 3. Operational Benefits

Prevents resource contention across teams.

Supports predictable performance for critical workloads.

Enables cost tracking per namespace for FinOps.

Integrates with autoscaling (HPA/Cluster Autoscaler) for dynamic workloads without exceeding quotas.

## 4. Observability & Auditing

**Prometheus:** Track quota usage and alerts for nearing limits.

**Kubernetes Dashboard / Lens:** Visualize namespace and resource usage.

**Audit logs:** Track creation of namespaces and resource usage violations.