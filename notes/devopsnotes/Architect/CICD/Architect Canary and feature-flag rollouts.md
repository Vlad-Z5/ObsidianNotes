# Architect: Canary and feature-flag rollouts

Both techniques aim to ship features safely, by controlling blast radius and enabling quick rollbacks.

## 1. Core Concepts
- ### Canary Deployment
	- Release a new version of an app to a small subset of users or traffic.
	- Monitor performance and errors before full rollout.
	- Gradually shift more traffic if stable.
- ### Feature Flags
	- Control feature availability dynamically via config, without redeploying code.
	- Enable per-user, per-region, or per-environment rollouts.
	- Useful for A/B testing, dark launches, and emergency kill switches.
## 2. Patterns & Implementations
- ### Canary Deployment Approaches
	- Kubernetes Native
		- Use Deployment strategies (progressive rollout with replicas).
		- Example: 90% traffic old version, 10% traffic new version.
		- Tools: Argo Rollouts, Flagger.
	- Service Mesh Canary
		- Offload routing to Istio, Linkerd, Consul.
		- Define weighted routing (e.g., 5% → 25% → 100%).
		- Fine-grained telemetry for rollback decisions.
	- Load Balancer Canary
		- Use AWS ALB, GCP Load Balancer rules to route traffic percentages.
- ### Feature Flags
	- Types
		- Release flags (new features on/off).
		- Experiment flags (A/B testing).
		- Ops flags (enable/disable services quickly).
	- Tools
		- LaunchDarkly, Unleash, Flipt, OpenFeature.
		- Homegrown solutions (configmaps + env vars).
	- Patterns
		- Store flag state in central service.
		- Dynamically update without redeployment.
		- Audit flag changes for compliance.
## 3. Monitoring & Rollback
- ### Metrics to Watch
	- Error rate
	- Latency (p95/p99)
	- CPU/memory usage
	- User engagement
- ### Rollback Strategies
	- Canary: shift traffic back to stable version.
	- Feature flags: toggle feature off instantly.
	- Automate rollback with tools like Argo Rollouts or Flagger.
## 4. Best Practices
- ### Traffic Management
	- Start with low % traffic (1–5%) before ramping up.
- ### Automation
	- Automate promotion/rollback with metrics-based triggers.
- ### Flag Management
	- Keep feature flags short-lived; remove stale flags from code.
	- Store flags in config service, not in code constants.
	- Ensure auditability of flag changes.
- ### Combined Strategy
	- Combine both strategies: Canary rollout + feature flags for internal toggles.