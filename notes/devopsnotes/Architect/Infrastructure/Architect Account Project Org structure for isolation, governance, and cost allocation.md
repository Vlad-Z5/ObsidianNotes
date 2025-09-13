# Account/Project/Org structure for isolation, governance, and cost allocation

This is crucial in AWS + multi-cloud environments because improper structuring leads to security risks, billing chaos, and operational headaches.

## 1. Core Principles

### Isolation by environment / business unit / workload

Separate production from non-prod (dev, QA, staging) to prevent accidental access.

Segregate sensitive workloads (PCI, HIPAA, or internal critical apps).

### Least privilege & centralized governance

Organize accounts/projects so policies can be applied consistently.

Enforce Service Control Policies (SCPs) and identity federation.

### Cost visibility & allocation

Use tagging, consolidated billing, or linked accounts to track spend by team/project.

Prevent cross-charging confusion for internal teams.

### Scalability

Structure should accommodate adding new teams, regions, and projects without redesign.

## 2. AWS Account Strategies

### A. Multi-Account via AWS Organizations

**Structure Options**

Environment-Based

Root Org
  ├─ Prod Account
  ├─ Staging Account
  └─ Dev/QA Account

Team/Business Unit Based

Root Org
  ├─ Marketing Account
  ├─ Engineering Account
  └─ Analytics Account

Hybrid

Root Org
  ├─ Prod Accounts (per BU)
  └─ Non-Prod Accounts (shared by multiple BUs)

**Benefits**

Strong isolation (resource, billing, IAM boundaries)

Enables SCP enforcement

Simplifies compliance audits

**Best Practice**

Enforce separate prod accounts, never share with non-prod.

Use AWS Control Tower or Landing Zone to automate baseline setup.

### B. Single Account with Multiple Projects

**When to use**

Small orgs, low number of teams.

Simpler billing, fewer accounts to manage.

**Drawbacks**

Harder to enforce environment isolation.

IAM policies become complex and brittle.

Risk of accidental access to prod from dev.

## 3. GCP / Azure Analogy

### GCP Projects

Similar to AWS accounts, but billing and IAM can be at Org or Folder level.

Recommended: one project per environment or workload.

### Azure Subscriptions

Acts like AWS account.

Resource Groups inside subscriptions for resource segregation.

### Hybrid Consistency

Keep one logical pattern across clouds to reduce mental mapping mistakes.

## 4. Governance Mechanisms

### AWS Service Control Policies (SCP)

Restrict which services or actions are allowed per account.

Example: Deny creation of public S3 buckets in prod accounts.

### IAM Identity Federation

SSO via SAML/OIDC (Okta, Azure AD) → reduces need to manage individual AWS users.

### Tagging & Resource Organization

Tags: env=prod, team=analytics, cost-center=1234

Mandatory tagging enforced via policies.

Use for cost allocation, automation, and compliance.

### Landing Zone / Baseline

Pre-created network, logging, monitoring, and security guardrails.

Automates account setup with best practices baked in.

## 5. Cost Allocation & Reporting

### AWS Organizations + Consolidated Billing

Single payer account; child accounts report usage.

### Cost Explorer / Budgets

Track by tags, account, region.

### Guardrails

Alert if spend exceeds thresholds per environment or BU.

### Chargeback / Showback

Optionally, show teams their own usage to drive efficiency.

## 6. Operational Best Practices

Automate new account creation with Control Tower or Landing Zone.

Maintain separate VPCs per account to enforce isolation.

Use cross-account IAM roles for controlled access.

Enforce mandatory logging (CloudTrail, Config, GuardDuty) in all accounts.

Standardize naming and tagging across all accounts/projects.

Periodically audit accounts for unused resources, open permissions, or drift from policies.

# Content from previous subtopic: [[Multi-cloud / hybrid networking patterns (AWS–GCP, AWS–Azure, private cloud integration)

Round 1 – Infra, Kubernetes, and Cloud Patterns (45 mins)
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