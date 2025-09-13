# Immutable Infrastructure & Golden Images / Container Baselines

Immutable infrastructure is the practice of never modifying running servers or containers in production. Instead, you deploy new instances/images for every change. This eliminates configuration drift and improves repeatability.

## 1. Core Concepts

**Immutable Infrastructure:** Once deployed, instances or containers are not updated manually. Changes require building a new image or artifact and redeploying.

**Golden AMIs / Images:** Pre-baked VM or container images containing OS, runtime, libraries, and security patches.

**Container Baselines:** Standardized container images with approved dependencies, security patches, and configurations.

### Benefits:

- Predictable deployments
- Reduced downtime and rollback complexity
- Enhanced security (no ad-hoc changes)
- Easier compliance and auditing

## 2. Patterns & Practices

### A. VM / Cloud Instances

**Golden AMI Pipeline:**

Use Packer or AWS Image Builder to bake AMIs with OS patches, monitoring agents, and application dependencies.

Test AMIs in staging before production deployment.

**Immutable Deployment:**

Deploy new AMI via Auto Scaling Group (ASG) or instance replacement.

Old instances terminated after new instances are healthy.

**Blue/Green or Canary Deployments:**

Ensure zero downtime when rolling out new AMIs.

### B. Containers

**Container Image Baselines:**

Start from minimal, official base images (e.g., Alpine, Debian slim).

Include only necessary dependencies.

Pre-install security tools and config files.

**Image Scanning & Signing:**

Scan for vulnerabilities (Trivy, Aqua, Prisma Cloud).

Sign images (Sigstore / Cosign) to enforce supply chain integrity.

**CI/CD Integration:**

Every commit triggers build of a new image.

Images tagged immutably (SHA digest) and deployed via GitOps or pipelines.

## 3. Best Practices

**Automate Image Creation**

Packer, AWS Image Builder, Dockerfile pipelines.

**Version & Tag Images**

Use semantic versioning or commit SHA digests.

**Enforce Security Compliance**

Pre-install patches, configure logging agents, disable unused services.

**Replace, Don't Patch**

Rolling updates replace old instances/images rather than patching in place.

**Integrate Observability**

Bake monitoring and tracing agents into images to avoid manual post-deployment installs.

**Test Before Deployment**

Validate performance, security, and configuration in staging before production rollout.

## 4. Tools & Automation

**VM Images:** Packer, AWS Image Builder, Terraform AMI pipelines.

**Containers:** Docker, BuildKit, Kaniko, Sigstore/Cosign for signing.

**CI/CD Integration:** Jenkins, GitHub Actions, GitLab CI, ArgoCD.

**Security Scanning:** Trivy, Aqua, Prisma Cloud, Clair.

**Configuration & Compliance:** Ansible, Chef, Puppet (baked into images), or baked scripts.

# Content from previous subtopic: [[Auto-scaling patterns (infra and application layers)

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

# Content from previous subtopic: [[Capacity and performance testing pipelines

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

Adjacent Skills

Linux internals, systemd, kernel tuning.

Networking (L3–L7 load balancing, DNS, VPN, BGP).