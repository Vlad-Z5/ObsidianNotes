# Observability & Control Planes (Centralized Logging, Metrics, Tracing, Chaos Testing)

A DevOps Architect is expected to design observability as a first-class citizen — not bolted on later. This ensures systems are measurable, debuggable, and resilient.

## 1. Core Pillars of Observability

**Metrics** → Time-series numbers (latency, throughput, error rate, resource utilization).

Helps answer "What is happening?"

Tools: CloudWatch, Prometheus, Datadog.

**Logs** → Event-based, structured preferably (JSON).

Helps answer "Why is it happening?"

Tools: CloudWatch Logs, ELK/Opensearch, Fluentd/FluentBit.

**Traces** → Distributed request path across microservices.

Helps answer "Where exactly is it breaking or slow?"

Tools: AWS X-Ray, OpenTelemetry, Jaeger.

**Events** → Audit and change logs (infrastructure + apps).

Helps answer "Who/what changed the system?"

Tools: CloudTrail, Config, Audit logs.

Together, these form the Golden Signals (from Google SRE):

- Latency
- Traffic
- Errors
- Saturation

## 2. Centralized Logging Patterns

### A. Cloud-Native

CloudWatch Logs for AWS workloads.

Log groups per service, shipped via agents (CW Agent, FluentBit).

Cross-account aggregation into a central logging account.

### B. Self-Managed

Fluentd/FluentBit sidecars → Kafka → Elasticsearch/OpenSearch + Kibana.

Provides more control but higher operational overhead.

### C. Hybrid

Logs flow to central SIEM (Splunk, ELK, Datadog, New Relic).

Cloud + on-prem workloads normalized via structured JSON.

**Best Practices:**

Standardize JSON log format across apps.

Enforce correlation IDs across logs & traces.

Apply lifecycle policies (short retention in hot tier, archive in S3/Glacier).

## 3. Metrics Collection & Aggregation

**System/Infra Metrics:**

AWS → CloudWatch.

On-Prem → Prometheus Node Exporter.

**App Metrics:**

Expose /metrics endpoint in services (Prometheus scrape).

**Custom Business Metrics:**

Transactions/sec, claim processing times, etc.

**Aggregation Strategy:**

Use Prometheus federation or Thanos/Cortex for global view.

CloudWatch Metric Streams → Kinesis → Datadog/NewRelic for unified dashboards.

## 4. Distributed Tracing

**Challenge:** Microservices often fail silently unless traced end-to-end.

**AWS X-Ray:**

Native for Lambda, API Gateway, ECS/EKS.

Provides service maps, latency distribution.

**OpenTelemetry:**

Vendor-neutral, works across hybrid/on-prem.

Exports to Jaeger, Tempo, Datadog, etc.

**Key Practice:**

Propagate trace IDs via headers (W3C TraceContext).

Link logs ↔ traces ↔ metrics (triple correlation).

## 5. Control Plane for Observability

A control plane governs:

- Policy enforcement (what must be logged, how metrics are tagged).
- Cross-environment consistency (prod vs dev).
- Access control (who can see logs/metrics/traces).

**AWS Implementation:**

Centralized Observability account in AWS Org.

All VPC Flow Logs, CloudTrail, Config data aggregated here.

Cross-account IAM roles grant read-only dashboards to teams.

## 6. Chaos Testing & Continuous Resilience

Observability is only useful if tested under stress.

### Chaos Testing Patterns

**Fault Injection Simulator (FIS) in AWS:**

Terminate instances, throttle APIs, inject network latency.

**Chaos Mesh / LitmusChaos in Kubernetes:**

Kill pods, disrupt network, simulate node failures.

### Best Practices

Run chaos experiments in staging environments with prod-like data.

Automate Game Days — simulate failure, verify observability catches it.

Measure MTTD (Mean Time to Detect) and MTTR (Mean Time to Recover) as SLOs.