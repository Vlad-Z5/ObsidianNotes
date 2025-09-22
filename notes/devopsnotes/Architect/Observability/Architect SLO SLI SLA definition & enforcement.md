# Architect: SLO SLI SLA definition & enforcement

Understanding and enforcing service-level objectives is key for balancing reliability, risk, and business needs.

## 1. Definitions
- ### SLI (Service Level Indicator)
	- Quantitative measure of a system attribute.
	- Examples: request latency, error rate, uptime.
	- "What you actually measure."
- ### SLO (Service Level Objective)
	- Target value for an SLI over a specific period.
	- Example: 99.9% requests < 300ms over 30 days.
	- "The reliability goal you aim for."
- ### SLA (Service Level Agreement)
	- Formal agreement with business/customers.
	- Typically includes penalties if SLOs are violated.
	- Example: 99.9% uptime with credit for downtime exceeding the SLA.
## 2. SLO/SLI Selection
- ### Common SLIs
	- Error Rate: % of failed requests.
	- Latency / Response Time: P95/P99 for critical endpoints.
	- Availability: Uptime per service or component.
	- Throughput: Transactions per second, message processing rate.
	- Resource Saturation: CPU, memory, disk I/O thresholds.
- ### Selection Tip
	- Focus on user-impacting metrics rather than purely system-level metrics.
## 3. Implementation Patterns
- ### Metrics Collection
	- Use Prometheus or Cloud-native metrics to record SLIs.
	- Track rolling windows (e.g., 7-day, 30-day) for SLO evaluation.
- ### Alerting
	- Alert when SLOs approach error budget burn rate.
	- Integrate with PagerDuty, Slack, or Opsgenie.
- ### Error Budgets
	- Error budget = 1 – SLO.
	- Allows controlled risk: if error budget consumed, feature releases pause.
	- Enables tradeoffs between velocity and reliability.
- ### Dashboards
	- Show SLO compliance, remaining error budget, and historical trends.
	- Include business-facing views for leadership.
## 4. Enforcement & Governance
- ### Automation
	- CI/CD can pause deployments if error budget is exceeded.
	- Rollbacks triggered automatically when SLO thresholds are violated.
- ### RCA Integration
	- Post-incident analysis checks which SLOs were violated.
	- Guides operational improvements.
- ### Cross-team Alignment
	- Devs, SREs, and product teams agree on realistic SLOs.
	- Use error budgets to communicate trade-offs.
## 5. Best Practices
- ### Start Simple
	- Start with a few critical SLIs; avoid over-monitoring.
- ### Realistic Goals
	- Ensure SLOs are realistic and measurable.
- ### Business Focus
	- Link SLOs to business impact, not just technical thresholds.
- ### Continuous Monitoring
	- Use automated dashboards and alerts to track compliance continuously.
- ### Process Integration
	- Incorporate error budget policy into deployment workflows.
- ### Regular Review
	- Review and update SLOs periodically as usage patterns change.
