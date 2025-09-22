# Architect: GitOps flows (ArgoCD, Flux) and their security implications

GitOps is the practice of using Git as the single source of truth for declarative infrastructure and applications. Tools like ArgoCD and Flux continuously reconcile what's running in Kubernetes against what's declared in Git.

## 1. Core GitOps Flow
- ### Declarative Config in Git
	- Kubernetes manifests, Helm charts, or Kustomize overlays stored in a repo.
- ### Continuous Reconciliation
	- ArgoCD or Flux pulls desired state from Git.
	- Compares with the actual state in the cluster.
	- Automatically applies changes or raises drift alerts.
- ### Auditability
	- All changes flow through Git commits, reviews, and merges.
	- Git history = audit trail of infra/app lifecycle.
## 2. GitOps Tooling
- ### ArgoCD
	- Pull-based reconciliation (controller runs in cluster).
	- GUI + CLI for visibility and rollbacks.
	- Supports Helm, Kustomize, plain YAML.
	- RBAC + SSO integration for multi-tenant clusters.
- ### Flux
	- Also pull-based, operator-driven.
	- Strong GitOps primitives for multi-repo workflows.
	- Deep integration with Helm and Kustomize.
	- CLI-driven, lightweight compared to ArgoCD.
## 3. Security Implications
- ### Git Repository Security
	- Git repo becomes the critical trust anchor.
	- Must enforce:
		- Branch protection + PR reviews.
		- Signed commits and tags.
		- Secret scanning in repos (no plaintext secrets).
- ### Secrets Management
	- Never store secrets in Git.
	- Use External Secrets Operator, HashiCorp Vault, AWS Secrets Manager, or SOPS+KMS.
	- ArgoCD Vault Plugin or External Secrets syncers integrate secrets securely.
- ### Access Control
	- ArgoCD/Flux should have least-privilege RBAC in the cluster.
	- Multi-tenant setups require RBAC per project/namespace.
	- Avoid giving GitOps controllers cluster-admin in production.
- ### Drift Detection & Policy Enforcement
	- GitOps ensures drift is auto-reconciled, but:
		- Malicious/manual changes in cluster are overwritten.
		- Policies (OPA/Gatekeeper, Kyverno) enforce compliance before apply.
- ### Supply Chain Security
	- Ensure manifests reference signed, trusted container images.
	- Integrate cosign / sigstore for image signature verification.
	- SBOM (Software Bill of Materials) stored alongside manifests.
## 4. Operational Benefits
- ### Auditability
	- Every change is tracked in Git.
- ### Stability
	- Auto-healing ensures drift corrections.
- ### Rollback
	- Git revert = instant rollback.
- ### Compliance
	- Easier evidence for audits (SOC2, HIPAA, PCI).
## 5. Best Practices
- ### Code Review
	- Enforce code review on GitOps repos.
- ### Branching Strategy
	- Use branching strategy (dev → stage → prod) for environments.
- ### Repository Organization
	- Keep infra and app repos separate if scaling across teams.
- ### Policy Integration
	- Integrate policy-as-code checks in PRs before merge.
- ### Security Operations
	- Rotate GitOps controller tokens/credentials regularly.
- ### Monitoring
	- Monitor GitOps tools themselves (Prometheus metrics, audit logs).