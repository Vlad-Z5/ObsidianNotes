# Admission Controls (OPA / Gatekeeper / Kyverno)

Admission controls enforce policies on Kubernetes resources before they are persisted, ensuring compliance, security, and operational standards across clusters.

## 1. Core Concepts

**Admission Controllers:** Kubernetes components that intercept API requests before they reach etcd.

**MutatingAdmissionWebhook:** Can modify requests (e.g., inject sidecars).

**ValidatingAdmissionWebhook:** Can reject requests that don't meet policies.

**Policy-as-Code:** Define rules declaratively in YAML or Rego (OPA) for consistency.

**Goal:** Prevent misconfigurations, enforce standards, and maintain compliance without manual intervention.

## 2. Common Use Cases

### Security Policies

Enforce non-root containers, read-only file systems, disallow privileged containers.

### Resource Governance

Limit CPU/memory requests and limits, enforce quotas per namespace.

### Network Policies

Ensure every namespace has a default NetworkPolicy.

### Labeling & Tagging

Require standardized labels for tracking and cost allocation.

### Sidecar Injection

Ensure observability or service mesh sidecars are present.

## 3. Tools & Patterns

### A. Open Policy Agent (OPA)

Rego language: Declaratively write policies.

Integrates with Kubernetes as a Validating/Mutating Admission Webhook.

Example: Deny deployments without resource limits.

### B. Gatekeeper

OPA-based policy controller for Kubernetes.

Enforces constraints and constraint templates.

Supports audit mode to monitor violations before enforcement.

### C. Kyverno

Kubernetes-native policy engine using YAML instead of Rego.

Supports validation, mutation, and generation.

Example: Automatically inject sidecars, enforce labels, and apply defaults.

## 4. Best Practices

### Enforce Policies Early

Apply in dev/test clusters first to avoid blocking teams unnecessarily.

### Audit Before Enforce

Run in audit mode to detect violations before enforcing hard rules.

### Combine Tools for Coverage

Use OPA/Gatekeeper for complex logic, Kyverno for simpler, YAML-based policies.

### Integrate with CI/CD

Validate manifests during PRs before deploying to cluster.

### Version & Document Policies

Keep policies in Git with version control; tie them to release pipelines.

## 5. Observability & Remediation

**Monitoring:** Prometheus alerts on policy violations.

**Logging:** Store admission review logs for audit and troubleshooting.

**Remediation:** Automate mutation policies or trigger alerts for manual intervention.

# Content from previous subtopic: [[Service mesh patterns (mTLS, routing, observability)

• You’ve been asked to move from centralized logging to a service-mesh-based observability model. Your tradeoffs?
• Describe how you simulate production-level chaos in staging for Kubernetes.
• How do you handle pushback from leadership when your SLOs threaten velocity?

DevOps Architect — Atlassian style (expanded + answers)
Round 1 – Infra, Kubernetes, and Cloud Patterns (45 mins)
Q: Design a multi-tenant EKS cluster with isolation across dev, QA, and prod, with no noisy neighbours.

Model answer (high level):

Use separate AWS accounts or separate clusters for prod critical workloads; if single cluster, use strict tenancy model:

AWS IAM + OIDC + IRSA for least privilege.

Namespaces per team/env + NetworkPolicies (deny by default).

ResourceQuota + LimitRange to cap CPU/memory and ephemeral storage.

Node pools (managed nodegroups or managed node groups / fargate profiles) by tenant/workload class → isolate noisy workloads onto dedicated node groups.

PodDisruptionBudgets for critical workloads; taints/tolerations to keep noisy jobs off prod nodes.

Use KSM (Kubernetes metrics) + Vertical/Horizontal Pod Autoscalers with sensible thresholds.

Dedicated logging/monitoring namespaces with resource limits and sampling for noisy logs.
What they’re testing: tradeoffs between security vs. cost vs. isolation; multi-account vs multi-namespace; runtime isolation techniques.
Good follow-ups to ask: expected scale (# clusters, pods), compliance requirements, CI/CD model, cost sensitivity.
Checklist bullets: RBAC least privilege, network policy deny-all, quotas, taints/tolerations, separate node pools, observability & quotas on logging/metrics.

Q: What’s your approach to managing 10+ Kustomize overlays without drift or duplication?

Model answer:

Adopt a base + overlay pattern: one canonical base per app, overlays per environment.

Don’t duplicate resources — use Kustomize patches/vars and generators.

Keep environment config minimal (only environment-specific values).

Use templating for secrets/configMaps via sealed-secrets/External Secrets; store overlays in Git as branches or directories with clear naming convention.

Validate overlays in CI: kustomize build + kubectl apply --server-dry-run=client + schema validation (kubeval/custom schema).

Periodic automated drift detection: generate manifests from each overlay and compare to canonical base or golden images.
What they’re testing: reproducibility, GitOps hygiene, drift detection.
Keywords to use: base/overlay, kustomize patchesStrategicPatch, sealed-secrets, CI validation, schema validation, GitOps.

Q: Explain how you’d secure cross-region S3 replication and validate data integrity at scale.

Model answer: