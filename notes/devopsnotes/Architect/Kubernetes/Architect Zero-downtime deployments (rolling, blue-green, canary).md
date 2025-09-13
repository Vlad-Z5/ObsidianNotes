# Zero-Downtime Deployments (Rolling, Blue-Green, Canary)

Zero-downtime deployments ensure that applications are upgraded without service interruptions. In Kubernetes, this means carefully orchestrating pod replacements, traffic routing, and rollback strategies.

## 1. Deployment Strategies

### A. Rolling Updates

Default in Kubernetes Deployments.

Gradually replaces old pods with new ones.

Config knobs: maxUnavailable, maxSurge.

Pros: Simple, minimal resource overhead.

Cons: Risk of propagating a bad release quickly.

**Example:**

```yaml
strategy:
  type: RollingUpdate
  rollingUpdate:
    maxUnavailable: 1
    maxSurge: 1
```

### B. Blue-Green Deployments

Run two identical environments: blue (current) and green (new).

Traffic is switched to green once validation passes.

Pros: Instant rollback, no overlap of versions.

Cons: Requires double infrastructure temporarily.

K8s tools: Argo Rollouts, external traffic managers (NGINX, Istio, AWS ALB).

### C. Canary Deployments

Release new version to a subset of users/traffic.

Gradually increase traffic share (5% → 20% → 50% → 100%).

Requires metrics + automated rollback triggers.

Pros: Early detection of issues, safer than blue-green.

Cons: More complex setup with monitoring + traffic splitting.

K8s tools: Argo Rollouts, Flagger, Istio, Linkerd, AWS App Mesh.

## 2. Supporting Techniques

**Readiness Probes:** Ensure new pods only receive traffic when healthy.

**Liveness Probes:** Auto-restart unhealthy pods.

**PodDisruptionBudgets (PDBs):** Prevent too many pods being drained during rollout.

**Service Mesh Routing:** Istio/Linkerd for weighted traffic splits in canary rollouts.

**Feature Flags:** Roll out new features independent of deployments.

## 3. Rollback Strategies

**Rolling:** Roll back by redeploying the previous version.

**Blue-Green:** Instant rollback = switch traffic back to blue.

**Canary:** Halt traffic at current stage or revert to baseline release.

Automation via Argo Rollouts, Flagger, or CI/CD pipelines.

## 4. Observability Integration

**Metrics:** Success rate, error rate, latency (Prometheus, Datadog).

**Logs:** Capture both old and new version outputs.

**Traces:** Monitor distributed impact of changes.

Automated rollback triggers based on SLO breaches.

## 5. Best Practices

Always define readiness/liveness probes.

Use progressive rollouts with observability gates.

Automate rollback for error thresholds (e.g., >1% 5xx errors).

Validate DB migrations in advance; use backward-compatible schema changes.

Run chaos tests in staging to validate deployment resilience.

# Content from previous subtopic: [[Secure ingress/egress patterns (WAF, egress control, mTLS)

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