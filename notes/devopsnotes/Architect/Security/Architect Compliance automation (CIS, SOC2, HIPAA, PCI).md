# Architect: Compliance automation (CIS, SOC2, HIPAA, PCI)

Automation is essential for continuous compliance, reducing manual effort, avoiding human error, and ensuring audit readiness.

## 1. Core Concepts
- ### Compliance Frameworks
	- CIS Benchmarks: Best practices for secure configuration of OS, cloud, containers.
	- SOC2: Security, Availability, Processing Integrity, Confidentiality, Privacy.
	- HIPAA: Protects healthcare information (PHI).
	- PCI-DSS: Payment card security standards.
- ### Automation Goal
	- Enforce policies, perform continuous audits, and generate reports automatically.
## 2. Implementation Patterns
- ### Cloud Security Posture Management (CSPM)
	- Tools: Terraform Compliance, Prisma Cloud, Dome9, AWS Config, GCP Forseti.
	- Continuously monitor cloud resources for:
		- Publicly exposed S3 buckets
		- Over-permissive IAM roles
		- Unencrypted storage
		- Misconfigured network access
- ### IaC Scanning
	- Scan Terraform, CloudFormation, Pulumi templates before deployment.
	- Tools: Checkov, tfsec, Terrascan.
	- Catch security misconfigurations early.
- ### Container & Kubernetes Compliance
	- Enforce CIS Kubernetes Benchmarks using tools like Kube-bench, Polaris, OPA Gatekeeper.
	- Audit container images for vulnerabilities and misconfigurations.
- ### Policy-as-Code
	- Define compliance rules in code or declarative format.
	- Integrate into pipelines for pre-deployment enforcement.
- ### Reporting & Audit Automation
	- Auto-generate compliance reports for auditors.
	- Maintain immutable logs for change history and incident investigation.
## 3. Best Practices
- ### Shift-left Compliance
	- Integrate compliance checks into CI/CD pipelines.
- ### Continuous Monitoring
	- Use CSPM and automated scanners to detect drift or violations.
- ### Policy Enforcement
	- Use OPA, Gatekeeper, or Kyverno to enforce rules at runtime in Kubernetes.
- ### Documentation & Evidence
	- Automatically generate evidence for SOC2, HIPAA, PCI audits.
- ### Version-Controlled Policies
	- Keep policies and remediation scripts in Git for transparency and audit.
## 4. Operational Benefits
- ### Efficiency
	- Reduces manual audit work and risk of non-compliance.
- ### Prevention
	- Detects misconfigurations before they reach production.
- ### Assurance
	- Provides continuous assurance to leadership and regulators.
- ### DevOps Integration
	- Supports secure DevOps practices and fast delivery without sacrificing compliance.
