## Definitions

### SLI (Service Level Indicator)
A **quantitative measure** of some aspect of the service’s performance. Common SLIs include:
- Availability (e.g., successful requests / total requests)
- Latency (e.g., 95th percentile < 200ms)
- Error rate (e.g., 5xx errors / total requests)
- Throughput (e.g., requests per second)

### SLO (Service Level Objective)
A **target value or range** for an SLI over a time window. It represents internal reliability goals, e.g.:
- "99.9% of requests must succeed over a rolling 30-day window"
- "99% of requests should complete in <300ms in the last 7 days"

### SLA (Service Level Agreement)
An **external, contractual agreement** with customers. SLAs often include:
- Minimum availability guarantee (e.g., 99.95%)
- Penalties for breaches (e.g., service credits)
SLA thresholds are typically more lenient than SLOs to avoid frequent violations.

---

## Setting SLOs

### 1. Identify Critical User Journeys
Examples:
- API availability
- Web frontend latency
- Background job completion time

### 2. Choose SLIs
Pick metrics that:
- Reflect user experience
- Are measurable (preferably at the edge or user-facing)

Examples:
- Availability: success_rate = good_requests / total_requests
- Latency: latency_p95 < 300ms

### 3. Define SLO Targets
Use business and product context to decide:
- What is the minimum acceptable reliability?
- How much downtime or error is tolerable?

Examples:
- 99.9% availability = 43m 50s downtime/month
- 99% latency < 300ms = 1% of requests can exceed this

Don't default to "five nines" — balance reliability with development speed and cost.

---

## Setting SLAs

### 1. Start with Internal SLOs
Use well-defined SLOs as a baseline. SLAs should never be stricter than the system can reliably support.

### 2. Involve Legal and Business Teams
SLAs are contractual and must align with:
- Legal frameworks
- Business risk appetite
- Revenue and pricing tiers

### 3. Choose Conservative Targets
Set SLA thresholds slightly looser than your SLOs to provide a buffer.

Example:
- Internal SLO: 99.9% availability
- External SLA: 99.5% availability

This avoids breaching SLAs due to short-term incidents, while still motivating high reliability internally.

### 4. Define Penalty Structures
Decide:
- How penalties apply (e.g., service credits, discounts)
- Over what measurement window (monthly, quarterly)
- Any exclusions (e.g., scheduled maintenance, force majeure)

### 5. Communicate Clearly
SLAs must be:
- Documented in customer-facing agreements
- Easy to interpret
- Traceable to real metrics

Do not set SLAs without monitoring and reporting infrastructure to back them up.

---

## Error Budgets

### What is an Error Budget?
An **allowed margin of failure** within an SLO.

Error Budget = 1 - SLO

Examples:
- SLO: 99.9% → Error Budget = 0.1%
- For 1,000,000 requests/month → allowed errors = 1,000

### Why Error Budgets Matter
They balance:
- Reliability (user experience)
- Velocity (feature delivery)

If you're within budget: ship features.
If you're burning budget fast: pause releases, prioritize reliability.

---

## Burn Rate

### Definition
Burn rate is the speed at which the error budget is consumed.

Burn Rate = (Actual errors over a period) / (Allowed errors for that period)

### Example
SLO: 99.9% → Error budget = 0.1%
Budget for 30 days: 43.2 minutes

If 10 minutes are used in 1 day:
- Daily burn rate = 10 / (43.2 / 30) ≈ 6.94
- At this rate, budget will be exhausted in ~4.3 days

---

## Monitoring and Alerting

### Golden Signals to Track
- Success Rate (availability)
- Latency (p95/p99)
- Saturation (CPU, memory, etc.)
- Errors (4xx, 5xx, timeouts)

### Alerting on Burn Rate
Use short- and long-window burn rate SLO alerting:

- Fast-burn: 5% of budget in 1 hour → rapid degradation
- Slow-burn: 20% of budget in 6 hours → steady decline

Alert thresholds depend on your risk appetite and mitigation speed.

---

## Workflow: Setting and Operating SLOs

1. Define critical user journeys
2. Map to SLIs
3. Set SLOs with stakeholders
4. Implement monitoring (e.g., Prometheus + Alertmanager + Grafana)
5. Track error budgets
6. Alert on burn rate breaches
7. Review SLO breaches → postmortems and capacity planning
8. Adjust SLOs annually or after product changes

---

## What To Do With The Rest

Not all metrics need SLOs. Some are:
- Internal (e.g., CPU usage, job retries)
- Too volatile or non-critical

Track them via dashboards, not alerts.

Use SLOs only for:
- Critical user-facing behaviors
- Metrics with meaningful thresholds
- Areas where error budgets can guide decision-making