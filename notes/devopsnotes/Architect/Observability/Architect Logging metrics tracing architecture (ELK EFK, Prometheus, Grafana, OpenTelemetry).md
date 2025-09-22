# Architect: Logging metrics tracing architecture (ELK EFK, Prometheus, Grafana, OpenTelemetry)

Observability answers:
- Logging → What happened?
- Metrics → What's the system health?
- Tracing → Why is a request slow/failing?

A solid architecture integrates all three into a cohesive platform.

## 1. Logging Architecture
- ### Goals
	- Centralize logs from apps, infra, and network devices.
	- Enable fast search and long-term retention.
	- Secure logs with immutability for compliance.
- ### Common Stacks
	- ELK (Elasticsearch, Logstash, Kibana)
	- EFK (Elasticsearch, Fluentd/FluentBit, Kibana)
	- Cloud-native: AWS CloudWatch, GCP Logging, Azure Monitor.
- ### Patterns
	- Use sidecar log agents (Fluentd, Vector).
	- Ship logs via DaemonSets for cluster-wide collection.
	- Store structured logs (JSON), not raw text.
	- Enforce log retention policies (hot, warm, cold tiers).
## 2. Metrics Architecture
- ### Goals
	- Provide real-time visibility into system and app health.
	- Feed autoscaling, alerting, and capacity planning.
- ### Tools
	- Prometheus: metrics scraping and alerting.
	- Grafana: visualization and dashboards.
	- Thanos / Cortex / Mimir: long-term, scalable Prometheus storage.
	- Cloud-native: CloudWatch Metrics, GCP Monitoring.
- ### Key Metrics
	- Golden Signals: Latency, Errors, Traffic, Saturation.
	- Resource Usage: CPU, memory, disk I/O, network.
	- Business Metrics: Transactions, conversions, SLA compliance.
## 3. Tracing Architecture
- ### Goals
	- Trace end-to-end request flows across microservices.
	- Identify latency bottlenecks and root causes.
- ### Tools
	- OpenTelemetry (OTel): industry standard for tracing & metrics.
	- Jaeger, Tempo, Zipkin: tracing backends.
	- Service Mesh (Istio, Linkerd): automatic tracing injection.
- ### Patterns
	- Every request has a trace ID passed across services.
	- Combine traces with logs + metrics for context.
	- Sampling strategies: full vs. probabilistic.
## 4. Integration Model
- ### Unified Observability Stack
	- Logs → ELK/EFK
	- Metrics → Prometheus + Grafana
	- Tracing → OTel + Jaeger/Tempo
- ### Correlation
	- Inject trace IDs into logs.
	- Grafana dashboards linking metrics → traces → logs.
- ### Alerting
	- Prometheus Alertmanager → Slack/PagerDuty/Email.
	- Alerts tied to runbooks.
