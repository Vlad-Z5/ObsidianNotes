# Secrets management in pipelines (Vault, External Secrets)

# Content from previous subtopic: [[Multi-tenant cluster architecture & workload isolation (RBAC, quotas, node pools)

• Design a multi-tenant EKS cluster with isolation across dev, QA, and prod, with no noisy neighbors.
• What’s your approach to managing 10+ Kustomize overlays without drift or duplication?
• Explain how you’d secure cross-region S3 replication and validate data integrity at scale.
• What happens when systemd hits a failing unit in a containerized node? How would you auto-recover?
• Walk through your strategy to detect & mitigate pod-to-pod lateral movement inside a cluster.
• How do you perform zero-downtime upgrades for a stateful workload using Helm 3?
• Describe a hybrid cloud routing architecture between GCP and AWS. Where do you enforce boundaries?
• Your Terraform state got corrupted during a backend migration. Rebuild strategy?
• Bash One-liner: Find all running containers using more than 500MB RSS memory on a node.

Round 2 – Real Fire, RCA, and Chaos Control (75 mins)
• A new AWS ALB config caused TLS handshakes to fail intermittently. Walk through your full RCA path.
• Kubernetes nodes are healthy. But kubectl logs is blank for critical pods. What’s happening?
• You deployed a sidecar logging agent. Suddenly, CPU throttling spikes. Diagnose and rollback.
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

# Content from previous subtopic: [[Secrets management in pipelines (Vault, External Secrets)

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

Periodic validation: use S3 Inventory + manifest to compare object checksums between source and destination (or use AWS SDK to compute/check checksums).

For very large scales: use checksumming pipeline (Lambda/EMR) that samples or parallel compares objects; use Batch Operations to trigger validation jobs.
What they’re testing: KMS & IAM, practical integrity checks at scale, monitoring/alerts.
Checklist bullets: KMS keys & grants, replication config, S3 Inventory, metrics & alerts, batch validation jobs.

Q: What happens when systemd hits a failing unit in a containerized node? How would you auto-recover?

Model answer:

On a failing systemd unit on the host: systemd will follow unit's Restart= policy. If it’s critical (network, docker/containerd), services can fail and pods degrade.

Auto-recover:

Systemd: set Restart=on-failure, RestartSec, StartLimitBurst/IntervalSec.

Build OS image with proper service dependencies; enable WatchdogSec and liveness checks for critical services.

At cluster level: Node health checks + Node auto-replace (ASG + lifecycle + instance refresh or managed nodegroup auto-replace). Use cloud provider health checks to replace unhealthy nodes.

Use a machine agent (e.g., SSM, or cloud-provided) to run remediation scripts. Consider self-healing DaemonSet that reports host problems to operators and can cordon/drain the node.
What they’re testing: host-level resilience vs cluster-level; how to tie systemd behavior to cluster autoscaling/replace.

# Content from previous subtopic: [[Audit logging and immutable log storage

Audit logging and immutable log storage.

6. Operational Excellence

 Incident management process (on-call, RCA, postmortems).

 Change management (approvals, phased rollouts).

 Backup/restore validation (frequency, retention, tested restores).

 Config management baseline (OS hardening, patching schedule).

 Node and workload health remediation automation.

 Disaster recovery testing schedule & reporting.

7. Leadership & Culture

 Developer self-service platform with guardrails.

 Documentation and internal training programs.

 Communication of SLO tradeoffs to leadership.

 Cross-team design reviews and alignment meetings.

 Vendor/tool evaluation and ROI assessment.

 Mentorship plan for DevOps/SRE engineers.

 Conflict resolution between speed and safety.

8. Cost & Efficiency

 Cost visibility dashboards per team/project.

 Auto-scaling and scheduling for cost optimization.

 Use of spot/preemptible instances where safe.

 Cloud-native cost control tools (AWS Cost Explorer, GCP Billing, Kubecost).

 Chargeback/showback reporting.

9. Personal Preparation

 Hands-on labs for all major cloud providers you claim expertise in.

 Build/tear down a multi-region EKS/GKE cluster with IaC.

# Content from previous subtopic: [[Incident management process (on-call, RCA, postmortems)

Incident Management: Postmortems, RCA frameworks, automated recovery patterns.

Change Management: Controlled rollouts, approvals, feature flagging.

Configuration Management: Standard OS builds, agent baselines, patching strategy.

Performance Engineering: Load testing, capacity validation, performance regression detection.

4. Leadership & Influence

Mentorship: Guide engineers in infrastructure patterns, CI/CD best practices, and cloud-native development.

Cross-team Facilitation: Align platform features with application team needs.

Executive Communication: Translate technical metrics into business outcomes.

Vendor/Tool Evaluation: Run POCs, negotiate contracts, ensure ROI.

5. Key Deliverables

Cloud landing zone architecture diagrams.

IaC module library with documentation and examples.

Golden base container images & AMIs.

Standardized CI/CD templates.

Observability dashboards and alerting policies.

Disaster recovery runbooks & test results.

Security baselines and compliance audit reports.

Cost optimization reports & recommendations.

6. Skill Set Map

Core Skills

Cloud architecture (AWS, GCP, Azure) at an advanced level.

Kubernetes internals, networking, and security.

Infrastructure as Code (Terraform/Pulumi) design patterns.

GitOps, CI/CD best practices, pipeline orchestration.

Observability stack engineering.

# Content from previous subtopic: [[Backup/restore validation (frequency, retention, tested restores)

Checklist: backup & restore tested, migration backwards-compatibility, incremental partitioned upgrade, health checks & probes, canary.

Q: Describe a hybrid cloud routing architecture between GCP and AWS. Where do you enforce boundaries?

Model answer:

Routing architecture:

Use VPC/VPC-peer or Transit Gateway on AWS, Cloud Router + VPN/Interconnect on GCP. Connect via an encrypted transit (VPN/MPLS/direct connect via partner).

Use Transit Gateway / Shared VPC hubs and enforce egress/ingress via firewall appliances (NGFW) or cloud-native routes with next-hop appliances.

Use service mesh or API gateway for cross-cloud service calls; prefer egress through centralized gateways to enforce policies and observe traffic.

Boundaries enforcement:

Identity/auth: central identity (Okta) + federated IAM; enforce at service layer and API gateway.

Data boundaries: encryption, DLP, region residency — enforce at storage & gateway layer.

Network boundaries: restrict routes, central firewall, NAT, and egress filtering.
What they’re testing: networking fundamentals & operational boundaries.

Q: Your Terraform state got corrupted during a backend migration. Rebuild strategy?

Model answer:

Immediately: snapshot/back up the corrupt state file (do not overwrite).

Try recover:

Use terraform state pull to get current, or check backend provider (S3 versioning) for prior object versions.

Use terraform state rm to remove problematic resources, then terraform import to rebuild resource mapping, or reconstruct state manually with terraform state commands.

If unrecoverable:

Recreate clean state by importing each resource (scripted with SDKs) — prioritize critical infra first.

Add automated tests and enable state locking and backend versioning after recovery.
Checklist: backend object versioning, state locking, automated backups, import scripts, test in staging.

Q: Bash one-liner: Find all running containers using more than 500MB RSS memory on a node.

Answer:

ps aux --sort=-rss | awk '$6>500*1024 {print $0}'


or using docker/crictl: