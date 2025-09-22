# Architect: Service mesh patterns (mTLS, routing, observability)

A service mesh abstracts service-to-service communication, providing security, traffic management, and observability without changing application code.

## 1. Core Concepts
- ### mTLS (Mutual TLS)
	- Encrypts traffic between services and ensures authentication of both client and server.
- ### Traffic Routing
	- Control traffic flow between services (canary releases, A/B testing, blue/green deployments).
- ### Observability
	- Provides telemetry, metrics, tracing, and logs for service-to-service interactions.
- ### Policy Enforcement
	- Rate limiting, retries, circuit breaking, and access control.
- ### Popular Tools
	- Istio, Linkerd, Consul Connect, AWS App Mesh.
## 2. Security Patterns
- ### Encryption & Authentication
	- All pod-to-pod traffic encrypted via mTLS.
	- Certificates managed automatically by the mesh.
- ### Authorization
	- Define service-level policies (which services can call each other).
- ### Network Segmentation
	- Combine with Kubernetes NetworkPolicies for defense in depth.
- ### Secret Management
	- Use mesh-managed certificates and integrate with Vault or Secrets Manager.
## 3. Traffic Management
- ### Routing Rules
	- Canary releases: direct a % of traffic to new version.
	- Blue/green deployments: switch traffic from old to new version atomically.
	- A/B testing: split traffic based on headers or cookies.
- ### Resilience
	- Circuit breakers: prevent cascading failures.
	- Retries with backoff: handle transient errors.
	- Timeouts: avoid resource exhaustion.
## 4. Observability & Telemetry
- ### Metrics
	- Request rates, latencies, error rates (RED/GOLDEN signals).
- ### Tracing
	- Distributed traces across services (Jaeger, Zipkin, AWS X-Ray).
- ### Logging
	- Access logs with request context.
- ### Dashboards
	- Grafana or provider-native dashboards visualizing mesh metrics.
- ### Patterns
	- Centralized observability without touching application code.
	- Use sidecar proxies to capture metrics and enforce policies.
## 5. Deployment Patterns
- ### Sidecar Injection
	- Automatic: mesh injects proxy container into each pod.
	- Manual: inject proxy during deployment manifest creation.
- ### Namespace/Team Isolation
	- Mesh policies scoped per namespace for multi-tenancy.
- ### Gradual Adoption
	- Start with critical services; expand mesh gradually.
## 6. Best Practices
- ### Start with Security
	- Enable mTLS by default.
	- Gradually add authorization policies.
- ### Incremental Rollout
	- Start with monitoring only, then add routing & policies.
- ### Resource Management
	- Sidecars consume CPU/memory; adjust limits carefully.
- ### Integration with CI/CD
	- Ensure mesh configs are versioned with GitOps.
- ### Observability First
	- Always enable metrics/tracing before enabling complex routing.
## 7. Tools & Automation
- ### Service Mesh
	- Istio, Linkerd, Consul Connect, AWS App Mesh
- ### Observability
	- Prometheus, Grafana, Jaeger, AWS X-Ray, FluentBit
- ### Policy Management
	- OPA/Gatekeeper for mesh-level policies
- ### CI/CD Integration
	- ArgoCD/Flux for mesh manifests & routing configs
