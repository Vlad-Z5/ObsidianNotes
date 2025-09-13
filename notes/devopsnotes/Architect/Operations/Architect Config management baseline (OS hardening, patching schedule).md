# Architect: Config Management Baseline (OS Hardening, Patching Schedule)

Configuration management ensures that all systems are secure, consistent, and up-to-date, reducing vulnerabilities and drift.

## 1. Core Concepts

### Configuration Baseline

A defined set of standardized settings, packages, and security controls for hosts and nodes.

Provides predictable, auditable system behavior.

### OS Hardening

Reduces attack surface by disabling unnecessary services, users, ports, and features.

Examples:

Disable root SSH login

Remove unused packages

Enforce strong password policies

Enable host-based firewalls (iptables, ufw)

### Patching Schedule

Regularly apply OS and software updates to close vulnerabilities.

Balance security vs. stability by defining patch windows.

Include critical security patches immediately; routine updates on a defined cadence.

## 2. Implementation Patterns
### A. Configuration Management Tools

Ansible, Puppet, Chef, SaltStack to enforce baselines.

Example: Use Ansible playbooks to:

Ensure required packages are installed

Apply security configurations

Disable unnecessary services

### B. Immutable Infrastructure

Build golden images (AMIs, container baselines) with OS hardening and patches applied.

Replace nodes rather than patching in place for consistency.

### C. Patch Automation

Use OS-native package managers with automated security updates (yum-cron, apt unattended-upgrades).

Schedule non-critical updates during maintenance windows.

### D. Auditing and Compliance

Periodically scan nodes for drift from baseline using tools like OpenSCAP, Lynis, or CIS-CAT.

Report and remediate deviations automatically.

## 3. Best Practices

### Define and Version Baselines

Keep baseline configurations in version control.

### Automation

Apply configurations and patches automatically to all nodes consistently.

### Immutable and Replaceable Nodes

Prefer rebuilds over manual patching for cloud-native environments.

### Monitoring & Drift Detection

Continuously monitor for unauthorized changes.

### Documentation

Maintain standard operating procedures for baseline enforcement and patching.

## 4. Operational Benefits

Reduces vulnerabilities and attack surface.

Ensures consistency across environments, preventing “works on dev but fails in prod.”

Simplifies auditing and compliance (CIS, SOC2, HIPAA, PCI).

Enables rapid, predictable recovery when nodes are replaced or rebuilt.