# Architect: Alerting Rules with Actionable Runbooks

A strong alerting system does more than notify; it guides teams to diagnose and resolve issues quickly, reducing MTTR (Mean Time to Recovery).

## 1. Core Concepts

### Alerting Rules

Define conditions or thresholds that indicate a problem.

Examples:

CPU > 90% for 5 minutes

Error rate > 5% on a service endpoint

Request latency (P95) > 500ms

### Actionable Alerts

Alerts should be actionable, avoiding noise (“pager fatigue”).

Include context, metrics, logs, and runbook links.

### Runbooks

Step-by-step procedures for troubleshooting and remediation.

Include:

What the alert means

Immediate mitigation steps

Escalation contacts

Postmortem guidance

## 2. Implementation Patterns
### A. Prometheus Alertmanager

Define alert rules in Prometheus YAML:

```yaml
groups:
- name: cpu_alerts
  rules:
  - alert: HighCPU
    expr: node_cpu_seconds_total{mode="idle"} < 10
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "CPU usage is over 90%"
      runbook: "https://wiki.company.com/runbooks/high-cpu"
```


Alertmanager routes alerts to Slack, PagerDuty, Opsgenie, or email.

### B. Cloud-native Alerting

AWS CloudWatch Alarms, GCP Monitoring Alerts, Azure Monitor.

Link alerts to automated remediation Lambda/Cloud Function or runbooks.

### C. Service Mesh / App-level Alerts

Istio or Linkerd metrics (latency, error rates) feed Prometheus alerts.

Include trace IDs in alert context for faster RCA.

## 3. Best Practices

### Actionable First

Alerts must indicate what to do next, not just that something is wrong.

### Severity Tiers

Critical, Warning, Info — define escalation accordingly.

### Runbooks Versioning

Keep runbooks in Git for updates and auditing.

### Avoid Noise

Deduplicate alerts; use aggregation and thresholds.

### Automated Remediation

Integrate with scripts, auto-scaling, or self-healing workflows when possible.

### Observability Integration

Include links to dashboards, logs, and traces in the alert.