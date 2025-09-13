# Architect: Rollback and Release Freeze Procedures

When deploying frequently, failures are inevitable — what matters is how quickly and safely you can recover or pause changes.

## 1. Rollback Procedures
### A. Rollback Triggers

Metrics degrade (latency, error rate, SLO violation).

Logs show critical failures.

Customer-facing issues reported.

Deployment health checks fail.

### B. Rollback Mechanisms

#### Kubernetes Deployments

kubectl rollout undo deployment/my-app

Restores previous ReplicaSet.

#### Helm

helm rollback release-name revision

Returns app to a known good state.

#### GitOps (ArgoCD/Flux)

Revert Git commit or tag.

Sync cluster back to stable manifest.

#### Infrastructure (Terraform)

Maintain versioned state.

Use terraform apply with previous plan or rollback to prior module version.

#### Blue-Green Deployments

Switch traffic back to stable environment instantly.

## 2. Release Freeze Procedures

A release freeze halts all new changes temporarily to stabilize production.

### When to Freeze

During peak business events (Black Friday, product launch).

After a major outage or during RCA.

When critical infra/security patching is ongoing.

### How to Enforce

#### Pipeline Guardrails

Disable auto-deploy pipelines.

Block merges in Git (via branch protection rules).

#### Feature Flag Overrides

Freeze new feature exposure while allowing bug fixes.

#### Change Management Approval

Require explicit approvals during freeze windows.

#### Communication

Freeze window documented and communicated across teams.

## 3. Operational Practices

Predefined Runbooks: Teams know exactly how to rollback or freeze.

Monitoring & Alerts: Automatically detect conditions requiring rollback/freeze.

Audit Logging: Track who initiated rollback or freeze, and why.

Gradual Unfreeze: Resume deployments in low-risk environments first.

## 4. Best Practices

Automate rollbacks based on SLO violations, not just manual decisions.

Test rollback paths regularly in staging.

Document rollback SLA (e.g., rollback within 5 minutes).

Keep release freeze rare and short-lived — use it only for stability, not as a substitute for safe delivery.

Combine with progressive delivery (canary/blue-green) to reduce need for rollbacks.