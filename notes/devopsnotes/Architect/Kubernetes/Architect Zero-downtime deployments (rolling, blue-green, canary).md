# Architect: Zero-downtime deployments (rolling, blue-green, canary)

Zero-downtime deployments ensure that applications are upgraded without service interruptions. In Kubernetes, this means carefully orchestrating pod replacements, traffic routing, and rollback strategies.

## 1. Deployment Strategies
- ### Rolling Updates
	- Default in Kubernetes Deployments.
	- Gradually replaces old pods with new ones.
	- Config knobs: maxUnavailable, maxSurge.
	- Pros: Simple, minimal resource overhead.
	- Cons: Risk of propagating a bad release quickly.
	- Example strategy configuration with type: RollingUpdate, maxUnavailable: 1, maxSurge: 1
- ### Blue-Green Deployments
	- Run two identical environments: blue (current) and green (new).
	- Traffic is switched to green once validation passes.
	- Pros: Instant rollback, no overlap of versions.
	- Cons: Requires double infrastructure temporarily.
	- K8s tools: Argo Rollouts, external traffic managers (NGINX, Istio, AWS ALB).
- ### Canary Deployments
	- Release new version to a subset of users/traffic.
	- Gradually increase traffic share (5% → 20% → 50% → 100%).
	- Requires metrics + automated rollback triggers.
	- Pros: Early detection of issues, safer than blue-green.
	- Cons: More complex setup with monitoring + traffic splitting.
	- K8s tools: Argo Rollouts, Flagger, Istio, Linkerd, AWS App Mesh.
## 2. Supporting Techniques
- ### Health Checks
	- Readiness Probes: Ensure new pods only receive traffic when healthy.
	- Liveness Probes: Auto-restart unhealthy pods.
- ### Pod Management
	- PodDisruptionBudgets (PDBs): Prevent too many pods being drained during rollout.
- ### Traffic Control
	- Service Mesh Routing: Istio/Linkerd for weighted traffic splits in canary rollouts.
	- Feature Flags: Roll out new features independent of deployments.
## 3. Rollback Strategies
- ### Strategy-Specific Rollbacks
	- Rolling: Roll back by redeploying the previous version.
	- Blue-Green: Instant rollback = switch traffic back to blue.
	- Canary: Halt traffic at current stage or revert to baseline release.
- ### Automation
	- Automation via Argo Rollouts, Flagger, or CI/CD pipelines.
## 4. Observability Integration
- ### Monitoring
	- Metrics: Success rate, error rate, latency (Prometheus, Datadog).
	- Logs: Capture both old and new version outputs.
	- Traces: Monitor distributed impact of changes.
- ### Automated Response
	- Automated rollback triggers based on SLO breaches.
## 5. Best Practices
- ### Reliability
	- Always define readiness/liveness probes.
	- Use progressive rollouts with observability gates.
- ### Automation
	- Automate rollback for error thresholds (e.g., >1% 5xx errors).
- ### Data Safety
	- Validate DB migrations in advance; use backward-compatible schema changes.
- ### Testing
	- Run chaos tests in staging to validate deployment resilience.
