# Communication of SLO tradeoffs to leadership

# Content from previous subtopic: [[Auto-scaling and scheduling for cost optimization

• Autoscaling isn’t kicking in despite the CPU crossing the threshold. What’s broken — metrics, HPA, or API server?
• Prod users reporting 504s, but ELB health checks are green. Explain your isolation + triage process.
• Systemd journal logs vanish on reboot across some AMIs. What do you check in the image build and boot sequence?
• A production pod was OOMKilled, but you can’t find logs. Walk through a forensic-level debug.
• Kernel panic on a GKE node mid-deploy. How do you identify if it’s infra, base image, or app-level?

Round 3 – Leadership, Engineering Influence & Production Principles (30 mins)
• How do you design infrastructure that empowers devs without giving them footguns?
• What’s your Linux-level checklist before approving any custom AMI to production?
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