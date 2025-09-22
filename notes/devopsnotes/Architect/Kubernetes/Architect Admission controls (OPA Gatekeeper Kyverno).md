# Architect: Admission controls (OPA Gatekeeper Kyverno)

Admission controls enforce policies on Kubernetes resources before they are persisted, ensuring compliance, security, and operational standards across clusters.

## 1. Core Concepts
- ### Admission Controllers
	- Kubernetes components that intercept API requests before they reach etcd.
- ### Webhook Types
	- MutatingAdmissionWebhook: Can modify requests (e.g., inject sidecars).
	- ValidatingAdmissionWebhook: Can reject requests that don't meet policies.
- ### Policy-as-Code
	- Define rules declaratively in YAML or Rego (OPA) for consistency.
- ### Goal
	- Prevent misconfigurations, enforce standards, and maintain compliance without manual intervention.
## 2. Common Use Cases
- ### Security Policies
	- Enforce non-root containers, read-only file systems, disallow privileged containers.
- ### Resource Governance
	- Limit CPU/memory requests and limits, enforce quotas per namespace.
- ### Network Policies
	- Ensure every namespace has a default NetworkPolicy.
- ### Labeling & Tagging
	- Require standardized labels for tracking and cost allocation.
- ### Sidecar Injection
	- Ensure observability or service mesh sidecars are present.
## 3. Tools & Patterns
- ### Open Policy Agent (OPA)
	- Rego language: Declaratively write policies.
	- Integrates with Kubernetes as a Validating/Mutating Admission Webhook.
	- Example: Deny deployments without resource limits.
- ### Gatekeeper
	- OPA-based policy controller for Kubernetes.
	- Enforces constraints and constraint templates.
	- Supports audit mode to monitor violations before enforcement.
- ### Kyverno
	- Kubernetes-native policy engine using YAML instead of Rego.
	- Supports validation, mutation, and generation.
	- Example: Automatically inject sidecars, enforce labels, and apply defaults.
## 4. Best Practices
- ### Enforce Policies Early
	- Apply in dev/test clusters first to avoid blocking teams unnecessarily.
- ### Audit Before Enforce
	- Run in audit mode to detect violations before enforcing hard rules.
- ### Combine Tools for Coverage
	- Use OPA/Gatekeeper for complex logic, Kyverno for simpler, YAML-based policies.
- ### Integrate with CI/CD
	- Validate manifests during PRs before deploying to cluster.
- ### Version & Document Policies
	- Keep policies in Git with version control; tie them to release pipelines.
## 5. Observability & Remediation
- ### Monitoring
	- Prometheus alerts on policy violations.
- ### Logging
	- Store admission review logs for audit and troubleshooting.
- ### Remediation
	- Automate mutation policies or trigger alerts for manual intervention.
