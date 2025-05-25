### Metric Types

```promql
# Counter - always increasing
http_requests_total
process_cpu_seconds_total

# Gauge - can go up and down
node_memory_MemFree_bytes
cpu_usage_percent

# Histogram - observations in buckets
http_request_duration_seconds_bucket
http_request_duration_seconds_count
http_request_duration_seconds_sum

# Summary - quantiles
http_request_duration_seconds{quantile="0.5"}
http_request_duration_seconds{quantile="0.95"}
```

### Label Management

```promql
# Label replace
label_replace(up, "new_label", "$1", "instance", "([^:]+).*")

# Label join
label_join(up, "endpoint", ":", "instance", "job")
```

### Recording Rules

```yaml
# /etc/prometheus/rules/app.yml
groups:
  - name: app.rules
    interval: 30s
    rules:
      - record: job:http_requests:rate5m
        expr: sum(rate(http_requests_total[5m])) by (job)
        
      - record: job:http_request_duration:p95
        expr: histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (job, le))
        
      - record: instance:cpu_usage:rate5m
        expr: 100 * (1 - avg by (instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])))
```
