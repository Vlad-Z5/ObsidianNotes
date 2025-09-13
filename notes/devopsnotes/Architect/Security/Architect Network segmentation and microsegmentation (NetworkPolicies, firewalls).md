# Architect: Network Segmentation and Microsegmentation (NetworkPolicies, Firewalls)

Segmentation reduces risk by isolating workloads, environments, and services, making it harder for attackers or misconfigurations to propagate.

## 1. Core Concepts

### Network Segmentation

Divides networks into subnets, VPCs, or security zones.

Example: Separate dev, QA, and prod networks to prevent accidental access.

### Microsegmentation

Applies fine-grained policies at the workload or pod level.

Controls pod-to-pod or service-to-service communication.

Common in Kubernetes and zero-trust architectures.

### Zero Trust Networking

Assume no implicit trust between network entities.

Enforce authentication, authorization, and encryption on all communication.

## 2. Implementation Patterns
### A. Cloud (AWS / GCP / Azure)

Use VPCs, subnets, and security groups to isolate environments.

Use NACLs for subnet-level restrictions and firewalls for per-service access.

Implement private endpoints and service perimeters to prevent cross-region exposure.

### B. Kubernetes

NetworkPolicies define allowed ingress and egress between pods.

Example:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-frontend
spec:
  podSelector:
    matchLabels:
      app: frontend
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: backend
```


Tools for microsegmentation:

Calico, Cilium, Weave Net (advanced policy enforcement, eBPF-based).

### C. Service Mesh

Istio, Linkerd: enforce mTLS, allowlist communication, and traffic encryption.

Can implement policy-based routing and service-level isolation.

## 3. Best Practices

### Environment Isolation

Separate dev, staging, and prod networks/subnets.

### Least Privilege Networking

Only allow required traffic; deny all else.

### Pod/Service Microsegmentation

Define ingress/egress policies per namespace or workload.

### Encrypt Traffic

Use TLS/mTLS for all internal communications.

### Audit and Monitoring

Track firewall and NetworkPolicy changes.

Detect unexpected traffic flows.

### Automation

Manage NetworkPolicies and firewall rules via IaC (Terraform, Pulumi).

## 4. Operational Benefits

Reduces blast radius in case of compromise or misconfiguration.

Prevents lateral movement of attackers within clusters or cloud networks.

Supports regulatory compliance (HIPAA, PCI, SOC2).

Improves visibility into service dependencies and communication flows.