# Security & Compliance (IAM, Zero-Trust, Secrets, Supply Chain, Governance)

A DevOps Architect must treat security as a core design principle, not a bolt-on. This includes identity, access, secrets, runtime security, and compliance frameworks across AWS, on-prem, and hybrid environments.

## 1. Identity & Access Management (IAM)

### AWS

IAM Roles > IAM Users.

Principle of Least Privilege (PoLP).

IRSA (IAM Roles for Service Accounts) in EKS → fine-grained pod-level access.

SCPs (Service Control Policies) in AWS Organizations → guardrails across accounts.

### On-Prem

Integrate LDAP/AD for RBAC.

Kubernetes → map RBAC to corporate identity provider (OIDC/SAML).

**Best Practice:**
All human access → SSO + MFA. No long-lived keys.

## 2. Zero-Trust Networking

### Segmentation:

Kubernetes Network Policies (Calico, Cilium).

AWS Security Groups + NACLs per workload.

### mTLS Everywhere:

Service mesh (Istio/App Mesh) for pod-to-pod encryption.

### Boundary Enforcement:

API Gateway / WAF at ingress.

PrivateLink / Transit Gateway for internal traffic.

**Pattern:** Trust nothing by default → authenticate + authorize every request.

## 3. Secrets Management

AWS → Secrets Manager, SSM Parameter Store (with KMS).

On-Prem → HashiCorp Vault, CyberArk.

Kubernetes → External Secrets Operator (ESO) to inject from AWS/Vault.

**Best Practice:**

Rotate secrets automatically.

No plain-text in Git.

Audit secret usage.

## 4. Supply Chain Security

### CI/CD Controls:

Code scanning (Semgrep, SonarQube).

Dependency scanning (Snyk, Dependabot).

### Image Security:

Scan images in CI (Trivy, Aqua, Prisma).

Sign images with Cosign/Notary (SLSA compliance).

### SBOM (Software Bill of Materials):

Generate via Syft/Anchore.

Store alongside artifacts for audit.

**Goal:** Prevent tampering, ensure provenance, guarantee integrity.

## 5. Runtime Security

**Tools:** Falco, Aqua, Prisma Cloud.

### Detection:

Privilege escalation attempts.

Suspicious syscalls (e.g., crypto mining).

Unexpected outbound traffic.

### Response:

Quarantine pods/nodes.

Auto-revoke compromised IAM tokens.

Integrate alerts with SOAR/SIEM.

## 6. Compliance & Governance

### Frameworks:

SOC 2, HIPAA, PCI-DSS, FedRAMP (depending on org).

### AWS Services:

AWS Config → compliance checks.

Security Hub → central findings.

GuardDuty → threat detection.

Macie → sensitive data in S3.

### Policy-as-Code:

OPA, Conftest, Checkov → enforce compliance at build & deploy.

**Pattern:** Shift-left compliance (scan Terraform, Helm, Dockerfiles before prod).

## 7. Observability for Security

Centralize logs (CloudWatch, ELK, Loki).

Use CloudTrail + GuardDuty for AWS activity monitoring.

On-prem → Syslog → SIEM (Splunk, ELK).

Correlate auth logs, network flows, and app traces.

## 8. Hybrid/On-Prem Security

### Connectivity:

Encrypted VPN/DX tunnels (IPSec, TLS).

Rotate keys + certs regularly.

### Key Management:

AWS KMS multi-region keys.

On-prem HSM (HashiCorp Vault, Thales).

### Federated Identity:

SSO spanning AWS + on-prem AD.