# Disaster Recovery (DR) Patterns – Active-Active, Active-Passive, Backup/Restore

Disaster Recovery is a core responsibility for a DevOps Architect: balancing RTO (Recovery Time Objective), RPO (Recovery Point Objective), and cost.

## 1. Core Principles

RTO (Recovery Time Objective): How fast must we recover? (minutes vs hours vs days).

RPO (Recovery Point Objective): How much data can we afford to lose? (seconds vs hours).

Cost vs Resiliency tradeoff:

High availability (HA) ≠ DR, but DR often builds on HA.

Lower RTO/RPO requires more infra & spend.

## 2. Common DR Patterns

### A. Backup & Restore (Lowest Cost)

**Mechanism:**

Backups taken (EBS snapshots, RDS snapshots, S3 versioning).

Stored in a secondary region or on-prem archive.

Restore workloads in target region/site when disaster occurs.

RTO: Hours to days.

RPO: 24 hours typical (depends on backup schedule).

Cost: Low (pay for storage only).

Use Case: Non-critical systems, dev/test environments.

**AWS Services:**

AWS Backup, S3 Cross-Region Replication, DynamoDB PITR, RDS automated backups.

### B. Pilot Light

**Mechanism:**

Minimal critical infra (e.g., DB replicas) always running in DR region.

Compute/app tier spun up during disaster.

RTO: Hours.

RPO: Minutes to hours (replication latency).

Cost: Medium (storage + minimal compute).

Use Case: Critical but not real-time apps.

**AWS Services:**

RDS Cross-Region Read Replicas.

EBS snapshot copy.

CloudFormation/Terraform to recreate infra quickly.

### C. Warm Standby

**Mechanism:**

Scaled-down but fully functional environment running in DR region.

Can be scaled up quickly if disaster strikes.

RTO: 30–60 minutes.

RPO: Near real-time with async replication.

Cost: Higher (compute + storage always on).

Use Case: Mid-size orgs with tighter SLAs.

**AWS Services:**

Auto Scaling to scale standby infra up.

Elastic Disaster Recovery (AWS DRS) for server replication.

### D. Active-Passive (Hot Standby)

**Mechanism:**

Full replica environment running in DR site, but traffic is routed only to primary until disaster.

Failover handled by DNS (Route 53 health checks) or Global Accelerator.

RTO: Minutes.

RPO: Seconds to minutes (depending on replication).

Cost: High (full infra always running).

Use Case: Customer-facing prod workloads.

**AWS Services:**

Route 53 health-based failover.

RDS Multi-AZ or Aurora Global Database (for DB failover).

### E. Active-Active (Multi-Region)

**Mechanism:**

Fully active deployments in multiple regions.

Traffic distributed globally via DNS or global LB.

Writes replicated via multi-master DBs or conflict resolution.

RTO: Near zero (always running).

RPO: Zero or near zero.

Cost: Very high (duplicate infra everywhere).

Use Case: Mission-critical, global services (e.g., SaaS platforms, fintech).

**AWS Services:**

Amazon Aurora Global Database (read/write local, cross-region replication <1s).

DynamoDB Global Tables.

Route 53 latency-based routing.

AWS Global Accelerator for low-latency failover.

## 3. Hybrid DR (AWS + On-Prem)

### On-Prem Primary, AWS DR

Use AWS as secondary site.

AWS Elastic Disaster Recovery (AWS DRS) replicates on-prem VMs → EC2.

RPO: seconds, RTO: minutes.

### AWS Primary, On-Prem DR

Less common, but some regulated industries require local DR.

Periodic EBS/S3 snapshot copy to on-prem storage.

## 4. Key Design Considerations

### DNS & Traffic Routing

Route 53 health checks for failover.

Latency-based routing for active-active.

TTL tuning — lower TTL = faster failover, but higher DNS traffic.

### Data Replication

Asynchronous vs synchronous.

Aurora Global DB → <1s lag.

DynamoDB Global Tables → multi-master.

S3 Cross-Region Replication.

### Testing

Regular DR drills ("game days") to validate RTO/RPO.

Chaos testing to simulate region-wide outages.

### Cost Control

Pilot light/warm standby for balance.

Only go active-active for workloads where downtime = massive revenue loss.