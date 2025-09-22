# Architect: Change management (approvals, phased rollouts)

Change management ensures that infrastructure and application updates are applied safely, minimizing production risk while maintaining velocity.

## 1. Core Concepts
- ### Change Management Objectives
	- Reduce production incidents due to changes.
	- Ensure visibility, accountability, and traceability of all modifications.
	- Balance speed vs. stability in continuous delivery.
- ### Types of Changes
	- Standard Changes: Pre-approved, low-risk (e.g., configuration tweaks).
	- Normal Changes: Require review and approval (e.g., infra updates, DB schema changes).
	- Emergency Changes: Must be implemented immediately with post-facto review.
## 2. Implementation Patterns
- ### Approval Workflows
	- CI/CD gates can enforce approval steps.
	- Use tools like ServiceNow, Jira, GitHub PRs for review and authorization.
	- Ensure segregation of duties: devs cannot approve their own high-risk changes.
- ### Phased / Progressive Rollouts
	- Blue-Green Deployments: Switch traffic to a new environment after validation.
	- Canary Releases: Deploy to a subset of users/services; monitor before full rollout.
	- Feature Flags: Enable/disable features dynamically for controlled exposure.
- ### Automated Validation
	- Pre-deploy automated tests (unit, integration, performance, security).
	- Post-deploy monitoring for anomalies (metrics, logs, traces).
- ### Emergency Change Handling
	- Document process for rapid approvals.
	- Post-incident review ensures lessons are captured.
## 3. Best Practices
- ### Policy as Code
	- Enforce approvals, rollouts, and validation steps via CI/CD pipelines.
- ### Observability Integration
	- Tie rollouts to real-time dashboards for fast detection of failures.
- ### Audit & Documentation
	- Track all changes with timestamps, approvers, and status for compliance.
- ### Minimal Blast Radius
	- Deploy to isolated environments or subsets first; rollback if issues arise.
- ### Continuous Improvement
	- Use post-deploy reviews to refine approval thresholds, test coverage, and automation.
## 4. Operational Benefits
- ### Risk Reduction
	- Reduces incidents due to misconfigurations or faulty code.
- ### Experimentation
	- Enables safe experimentation in production.
- ### Compliance
	- Provides audit trails for compliance.
- ### Collaboration
	- Improves collaboration between development, operations, and security teams.
