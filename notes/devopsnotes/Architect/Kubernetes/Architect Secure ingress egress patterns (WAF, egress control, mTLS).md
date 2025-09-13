# Secure Ingress/Egress Patterns

This subtopic focuses on controlling traffic into and out of your cluster to enforce security, compliance, and resilience.

## 1. Core Concepts

**Ingress:** Traffic entering the cluster (external → services).

**Egress:** Traffic leaving the cluster (services → external systems).

**WAF (Web Application Firewall):** Protects against web-layer attacks (SQLi, XSS, DDoS).

**mTLS (Mutual TLS):** Encrypts traffic between services and authenticates both client and server.

**Egress Controls:** Restrict external access to only approved destinations.

**Goal:** Prevent unauthorized access, enforce data confidentiality, and mitigate lateral movement risks.

## 2. Ingress Security Patterns

### A. API Gateway / Ingress Controller

Use Ingress controllers (NGINX, AWS ALB Ingress, GKE Ingress) to route traffic.

Enable TLS termination at ingress.

Integrate with WAF for layer-7 filtering.

### B. WAF

AWS WAF, Cloudflare, Azure WAF.

Apply rule sets for OWASP Top 10 protection.

Can block IP ranges, inspect headers, detect SQLi/XSS attempts.

### C. Rate Limiting & Authentication

Enforce rate limiting to prevent DoS attacks.

Use JWT/OAuth2 for service authentication.

Combine with RBAC and service accounts.

## 3. Egress Security Patterns

### A. Network Policies

Kubernetes NetworkPolicies restrict which pods can initiate connections outside the cluster.

Example: only allow pods to reach internal APIs, block all other external access.

### B. Proxy / Firewall

Use egress proxies or cloud firewall rules.

Inspect traffic for compliance and audit requirements.

### C. DNS & IP Whitelisting

Restrict egress to approved IPs or FQDNs (e.g., internal databases, SaaS services).

## 4. mTLS for Internal Traffic

Encrypt all pod-to-pod traffic within the cluster.

Authenticate both client and server to prevent unauthorized access.

Service Mesh (Istio, Linkerd, App Mesh) handles certificate management and rotation automatically.

## 5. Best Practices

### Enforce TLS everywhere

Ingress, service-to-service, and egress.

### Zero-trust approach

Default deny all inbound/outbound; allow only what is required.

### Combine policies

WAF + network policies + service mesh.

### Audit & observability

Log all ingress/egress traffic.

Alert on anomalies or policy violations.

### Automate certificate rotation

Avoid expired certs causing downtime or breaches.

## 6. Tools & Automation

**Ingress / API Gateway:** AWS ALB, NGINX, GKE Ingress, Istio Gateway.

**WAF:** AWS WAF, Azure WAF, Cloudflare.

**Egress Control:** Calico, Cilium, Istio egress policies, cloud firewall rules.

**mTLS:** Istio, Linkerd, App Mesh.

**Monitoring & Auditing:** Prometheus, Grafana, FluentBit, CloudTrail/Stackdriver.

# Content from previous subtopic: [[Namespace and resource quota strategy

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

Secure replication:

Use S3 Replication (CRR/Cross-Region Replication) with AWS KMS — use separate CMKs in source/dest and grant replication role permissions.

Enforce bucket policies & VPC endpoints, block public access.

Use IAM replication role restricted to necessary actions.

Use S3 Object Lock (if immutability required).

Validate integrity:

Rely on S3 ETag/Checksum support (S3 supports MD5/CRC/sha256 depending on upload type).

Enable S3 Replication Time Control + Replication metrics & notifications for failures.