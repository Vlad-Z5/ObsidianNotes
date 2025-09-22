# Architect: IaC design standards (Terraform Pulumi modules, state management, drift detection)

As a DevOps Architect, you're expected to establish best practices for building, managing, and scaling infrastructure code across multiple teams and environments. This ensures consistency, security, and reliability.

- ### Terraform/Pulumi Modules
	- **Why Modules?**
		- Standardize infrastructure components (VPCs, clusters, IAM roles, S3 buckets, etc.).
		- Promote reusability and reduce duplication.
		- Enforce compliance and security guardrails.
	- **Best Practices**
		- **Module Structure**
			- Separate root modules (environment-specific) and child modules (reusable patterns).
			- Example: A network module provisions VPC, subnets, routes; teams just consume it.
		- **Version Control**
			- Version modules in Git or private registries (Terraform Registry, Pulumi's package manager).
			- Tag stable releases and enforce semantic versioning.
		- **Inputs/Outputs**
			- Minimize required variables, set secure defaults, and expose only necessary outputs.
		- **Documentation**
			- Every module should have README, usage examples, and dependency notes.

- ### State Management
	- **Why It Matters**
		- Terraform and Pulumi track real-world infrastructure in a state file.
		- Incorrect handling can cause drift, data loss, or corrupted infra.
	- **Best Practices**
		- **Remote Backends**
			- Store state in S3 + DynamoDB (Terraform) or Pulumi Service / Blob storage.
			- Prevents local file corruption and enables team collaboration.
		- **Locking**
			- DynamoDB locks (Terraform) or Pulumi's concurrency controls prevent race conditions.
		- **State Separation**
			- Split state by environment (dev, qa, prod) and domain (networking, compute, IAM).
			- Prevents blast radius of accidental changes.
		- **Backups**
			- Enable automated state snapshots. Treat state as a critical asset.
		- **State Migration**
			- When moving backends, always run a plan + validate before final cutover.

- ### Drift Detection
	- **What Is Drift?**
		- Drift = when actual infrastructure diverges from what IaC defines (e.g., manual console edits).
	- **Best Practices**
		- **Terraform**
			- Run terraform plan in pipelines regularly.
			- Use Terraform Cloud drift detection or scheduled jobs.
		- **Pulumi**
			- pulumi refresh syncs stack with real-world infra.
			- Use Pulumi Deployments with drift detection in CI/CD.
		- **Automation**
			- Integrate drift checks into nightly jobs or GitOps pipelines.
			- Alert teams if drift is detected.
		- **Policy-as-Code**
			- Prevent manual changes by enforcing IAM least privilege and cloud policies (e.g., Service Control Policies in AWS).

- ### Operational Benefits
	- Consistency: No "snowflake" infrastructure.
	- Scalability: Modules let multiple teams reuse patterns without reinventing.
	- Resilience: State management reduces risks of accidental corruption.
	- Security: Drift detection + policy enforcement ensures infra matches compliance.
	- Velocity: Teams move faster with safe, reusable, versioned modules.