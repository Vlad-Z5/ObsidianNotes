# Cost Optimization & FinOps

(Cloud Economics, Right-Sizing, Reserved/Spot, Chargeback Models)

A DevOps Architect must not only deliver performance and reliability, but also control costs — a key responsibility in multi-cloud and hybrid environments.

## 1. FinOps Mindset

Treat cloud spend like a utility bill → visibility, allocation, optimization, forecasting.

Cross-functional ownership: Engineers must understand costs of their design choices.

Shift-left FinOps: Discuss cost impact at design & architecture stage, not after deployment.

## 2. Visibility & Tagging

### Tagging/Labeling → every resource must have:

- owner
- environment (dev/test/prod)
- application/service
- cost-center

### AWS Tools:

Cost Explorer, Budgets, CUR (Cost & Usage Reports).

AWS Billing Alarms (CloudWatch).

Trusted Advisor for savings recommendations.

### On-Prem / Hybrid:

Chargeback/showback → map cluster & VM usage to cost centers.

Tools: CloudHealth, Cloudability, Kubecost.

## 3. Right-Sizing

### Compute:

Scale instances/pods dynamically.

Use Auto Scaling Groups + Kubernetes HPA/VPA.

Match instance type to workload (don't run memory-heavy apps on compute-optimized nodes).

### Storage:

Move infrequent data → S3 Glacier/Archive tiers.

Delete unused EBS snapshots/volumes.

### Networking:

Consolidate NAT Gateways per VPC (big hidden cost).

Optimize data transfer (use PrivateLink, not public egress).

## 4. Pricing Models

On-Demand: Flexible, most expensive.

Reserved Instances (RIs): 1 or 3-year commitment, up to 72% cheaper.

Savings Plans: More flexible than RIs (applies across services).

Spot Instances: Up to 90% cheaper, good for batch & CI/CD workloads.

Dedicated Hosts: For compliance-heavy workloads.

**Pattern:**

Baseline load → RIs / Savings Plans.

Variable workloads → On-Demand.

Non-critical workloads → Spot.

## 5. Containers & K8s Cost Efficiency

Cluster Autoscaler: Scale nodes up/down.

Pod Priorities: Ensure prod workloads preempt dev/test.

Kubecost/OpenCost: Real-time cost monitoring per namespace/pod.

Bin Packing: Schedule workloads efficiently (Cilium, Karpenter).

## 6. Chargeback / Showback

Showback: Show teams their costs (visibility only).

Chargeback: Bill costs back to teams/departments.

### On-Prem + AWS Hybrid:

Allocate shared infra costs fairly (network, storage, monitoring).

Use Kubecost or CloudHealth for per-namespace chargeback.

## 7. Forecasting & Budgeting

Build predictive models (CloudWatch Anomaly Detection, AWS Forecast).

Compare actuals vs. forecast → adjust RIs/Savings Plans.

Set budgets per environment (Dev $1K/month cap, Prod $10K/month).

## 8. Cost Automation

### Lambda Functions for unused resource cleanup:

Stop dev EC2s at night.

Delete unattached EBS volumes.

Rotate S3 lifecycle policies.

### Infrastructure Policy-as-Code:

Prevent deploying large instances unless whitelisted.

OPA / Terraform Sentinel for budget guardrails.