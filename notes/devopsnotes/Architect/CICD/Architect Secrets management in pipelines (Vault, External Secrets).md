# Architect: Secrets management in pipelines (Vault, External Secrets)

Secrets include API keys, database credentials, TLS certificates, and other sensitive information. Proper management ensures they are never exposed in code, logs, or version control.

## 1. Core Principles
- ### Never store secrets in Git
	- No plaintext credentials in repositories or CI/CD pipelines.
- ### Centralized Secret Storage
	- Use dedicated secret management systems like HashiCorp Vault, AWS Secrets Manager, Azure Key Vault, or Kubernetes External Secrets.
- ### Dynamic Secrets
	- Generate ephemeral credentials that expire automatically.
	- Reduces risk of long-lived secrets being compromised.
- ### Least Privilege Access
	- Each service or pipeline step only accesses secrets it needs.
## 2. Pipeline Integration Patterns
- ### HashiCorp Vault
	- Secrets are requested dynamically at runtime.
	- Policies control who/what can access which secrets.
	- CI/CD integration: inject secrets as environment variables or files.
	- Example with Jenkins pipeline using withVault for secure credential injection.
- ### Kubernetes External Secrets
	- Sync secrets from external stores (AWS Secrets Manager, Vault) into Kubernetes Secrets.
	- Sidecars or initContainers inject secrets into pods without committing them to Git.
- ### CI/CD Environment Injection
	- Secrets are mounted at runtime rather than stored in pipeline code.
	- Use environment variables, files, or secret volumes.
	- Rotate secrets regularly and validate expiry.
## 3. Best Practices
- ### Audit Access
	- Monitor who accesses secrets and when.
	- Integrate audit logs with SIEM.
- ### Automatic Rotation
	- Rotate DB credentials, API keys, and certificates automatically.
- ### Encryption at Rest & Transit
	- Secrets should be encrypted in the secret store and during transit.
- ### Versioning
	- Maintain versions of secrets for rollback/recovery.
- ### Policy Enforcement
	- Use Vault policies or OPA/Kyverno policies to enforce secret access rules.
- ### Avoid Leaks
	- Mask secrets in logs and CI/CD output.
## 4. Observability & Security
- ### Audit Logs
	- Track secret access in pipelines.
- ### Alerts
	- Notify on unauthorized secret access attempts.
- ### Metrics
	- Monitor usage patterns and rotation schedules.