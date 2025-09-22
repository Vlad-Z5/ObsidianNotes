# Architect: Runtime security (Falco, Sysdig, Aqua)

Runtime security focuses on detecting and responding to threats in active systems, beyond static scanning or pre-deployment checks.

## 1. Core Concepts
- ### Purpose
	- Detect anomalous or malicious activity in running workloads.
	- Protect containers, VMs, and Kubernetes clusters from attacks such as privilege escalation, crypto mining, or lateral movement.
- ### Key Capabilities
	- Behavioral monitoring
	- File integrity monitoring
	- Process and network activity monitoring
	- Alerting and automated response
- ### Scope
	- Kubernetes pods, Docker containers, serverless functions, cloud VMs.
## 2. Implementation Patterns
- ### Falco (Open-source, CNCF)
	- Behavioral security engine for Kubernetes and Linux hosts.
	- Detects suspicious activity based on rules:
		- Unexpected network connections
		- Unauthorized file access
		- Privilege escalation attempts
	- Integrates with Prometheus, Grafana, or SIEM for alerts.
- ### Sysdig Secure
	- Full runtime security and monitoring platform.
	- Features:
		- Runtime threat detection
		- Compliance validation
		- Forensics and audit logs
	- Supports container and Kubernetes environments.
- ### Aqua Security
	- Enterprise-grade container and cloud-native security.
	- Runtime enforcement:
		- Block anomalous process execution
		- Restrict network access
		- Detect privilege escalation
	- Integrates with CI/CD for shift-left scanning.
- ### Policies and Enforcement
	- Define runtime policies for allowed system calls, network, and process behavior.
	- Automatic remediation for detected violations (kill container, isolate node).
## 3. Best Practices
- ### Define Behavioral Baselines
	- Understand normal workloads and traffic patterns.
- ### Centralized Alerting
	- Integrate runtime alerts with SIEM, PagerDuty, or Slack.
- ### Shift-Left Integration
	- Combine runtime security with image scanning and IaC policies.
- ### Policy Granularity
	- Limit permissions, enforce capabilities, and restrict host access.
- ### Regular Updates
	- Update rules and policies to adapt to new threats.
## 4. Operational Benefits
- ### Threat Detection
	- Detects attacks that bypass static scans.
	- Protects Kubernetes clusters and containers without downtime.
- ### Compliance
	- Supports compliance reporting with audit trails.
- ### Response
	- Enables proactive threat detection and remediation.
