**Core Principles:** Enterprise-grade DevOps architecture focusing on scalability, reliability, security, and operational excellence across cloud-native platforms and traditional infrastructure.

## Infrastructure
### [[Multi-cloud / hybrid networking patterns (AWS–GCP, AWS–Azure, private cloud integration)]]
### [[Account/Project/Org structure for isolation, governance, and cost allocation]]
### [[VPC design (subnets, routing, transit gateways, private endpoints)]]
### [[DR patterns (active-active, active-passive, backup/restore)]]
### [[IaC design standards (Terraform/Pulumi modules, state management, drift detection)]]
### [[Auto-scaling patterns (infra and application layers)]]
### [[Immutable infrastructure practices (golden AMIs/images, container baselines)]]

## Kubernetes
### [[Multi-tenant cluster architecture & workload isolation (RBAC, quotas, node pools)]]
### [[Cluster lifecycle management (upgrades, patching, node replacement)]]
### [[Service mesh patterns (mTLS, routing, observability)]]
### [[Admission controls (OPA/Gatekeeper/Kyverno)]]
### [[Namespace and resource quota strategy]]
### [[Secure ingress/egress patterns (WAF, egress control, mTLS)]]
### [[Zero-downtime deployments (rolling, blue-green, canary)]]

## CICD
### [[Standardized pipeline templates for all teams]]
### [[GitOps flows (ArgoCD, Flux) and their security implications]]
### [[Automated testing integration (unit, integration, performance)]]
### [[Secrets management in pipelines (Vault, External Secrets)]]
### [[Artifact management (signing, provenance, SBOM)]]
### [[Canary and feature-flag rollouts]]
### [[Rollback and release freeze procedures]]

## Observability
### [[Logging/metrics/tracing architecture (ELK/EFK, Prometheus, Grafana, OpenTelemetry)]]
### [[SLO/SLI/SLA definition & enforcement]]
### [[Alerting rules with actionable runbooks]]
### [[Distributed tracing and service dependency maps]]
### [[Chaos engineering practice in staging]]
### [[Capacity and performance testing pipelines]]

## Security
### [[IAM best practices (least privilege, JIT access, federated SSO)]]
### [[Network segmentation and microsegmentation (NetworkPolicies, firewalls)]]
### [[Supply chain security (SLSA, sigstore, container scanning)]]
### [[Compliance automation (CIS, SOC2, HIPAA, PCI)]]
### [[Runtime security (Falco, Sysdig, Aqua)]]
### [[Data encryption at rest & in transit]]
### [[Audit logging and immutable log storage]]

## Operations
### [[Incident management process (on-call, RCA, postmortems)]]
### [[Change management (approvals, phased rollouts)]]
### [[Backup/restore validation (frequency, retention, tested restores)]]
### [[Config management baseline (OS hardening, patching schedule)]]
### [[Node and workload health remediation automation]]
### [[Disaster recovery testing schedule & reporting]]

## Leadership
### [[Developer self-service platform with guardrails]]
### [[Documentation and internal training programs]]
### [[Communication of SLO tradeoffs to leadership]]
### [[Cross-team design reviews and alignment meetings]]
### [[Vendor/tool evaluation and ROI assessment]]
### [[Mentorship plan for DevOps/SRE engineers]]
### [[Conflict resolution between speed and safety]]

## Cost
### [[Cost visibility dashboards per team/project]]
### [[Auto-scaling and scheduling for cost optimization]]
### [[Use of spot/preemptible instances where safe]]
### [[Cloud-native cost control tools (AWS Cost Explorer, GCP Billing, Kubecost)]]
### [[Chargeback/showback reporting]]