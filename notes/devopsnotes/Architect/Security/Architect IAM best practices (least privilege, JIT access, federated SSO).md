# Architect: IAM best practices (least privilege, JIT access, federated SSO)

Identity and Access Management (IAM) ensures that users, services, and applications have only the permissions they need, reducing the attack surface and preventing accidental misconfigurations.

## 1. Core Principles
- ### Least Privilege
	- Grant only the permissions required for a user or service to perform their job.
	- Example: A CI/CD pipeline only needs write access to the artifact repository, not full cluster admin rights.
- ### Just-In-Time (JIT) Access
	- Grant temporary elevated permissions only when needed.
	- Reduces standing privileges and risk of compromise.
- ### Federated Single Sign-On (SSO)
	- Integrate corporate identity providers (Okta, Azure AD, Google Workspace) with cloud IAM.
	- Centralizes authentication and simplifies user lifecycle management.
## 2. Implementation Patterns
- ### A. AWS Example
	- Use IAM roles and policies instead of long-lived credentials.
	- Cross-account roles for temporary access to production resources.
	- Enable AWS SSO / IAM Identity Center with corporate IdP.
	- Use session policies for JIT access, e.g., allow admin only for 1 hour.
- ### B. Kubernetes Example
	- Map IAM roles to Kubernetes RBAC roles via IRSA (IAM Roles for Service Accounts) in EKS.
	- Restrict pod/service permissions to the minimum needed API access.
- ### C. CI/CD Integration
	- Pipelines assume ephemeral service accounts with scoped permissions.
	- Rotate secrets and keys automatically; never store credentials in Git.
## 3. Best Practices
- ### Role-Based Access Control (RBAC)
	- Assign permissions via roles, not individual users.
	- Apply consistently across cloud accounts and services.
- ### Policy Granularity
	- Use fine-grained IAM policies instead of broad permissions.
	- Example: s3:GetObject instead of s3:*.
- ### JIT / Temporary Credentials
	- Implement session expiration and automated revocation.
	- Use tools like AWS STS, Vault dynamic credentials, or Azure PIM.
- ### Audit and Monitoring
	- Enable CloudTrail, CloudWatch, or GCP Audit Logs.
	- Monitor for unexpected privilege escalations.
- ### Federation
	- Centralize identity with SSO.
	- Enforce MFA and strong authentication policies.
- ### Secrets Management Integration
	- Avoid embedding IAM credentials in code.
	- Use Vault, External Secrets, or cloud-native secret managers.
## 4. Operational Benefits
- ### Risk Reduction
	- Reduces risk of accidental or malicious access.
- ### Compliance
	- Improves auditing and compliance for SOC2, HIPAA, PCI.
- ### User Management
	- Simplifies user onboarding/offboarding.
- ### Temporary Access
	- Enables temporary elevated access without leaving standing admin privileges.
