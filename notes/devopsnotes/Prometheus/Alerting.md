### Alert Rules

```yaml
# /etc/prometheus/rules/alerts.yml
groups:
  - name: system.alerts
    rules:
      - alert: HighCPU
        expr: instance:cpu_usage:rate5m > 80
        for: 5m
        labels:
          severity: warning
          team: sre
        annotations:
          summary: "High CPU usage on {{ $labels.instance }}"
          description: "CPU usage is {{ $value }}% on instance {{ $labels.instance }}"
          
      - alert: ServiceDown
        expr: up == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Service {{ $labels.job }} is down"
          description: "Service {{ $labels.job }} on {{ $labels.instance }} has been down for more than 1 minute"
          
      - alert: HighMemoryUsage
        expr: (node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes * 100 > 90
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage on {{ $labels.instance }}"
          description: "Memory usage is {{ $value }}% on {{ $labels.instance }}"
          
      - alert: DiskSpaceLow
        expr: (node_filesystem_size_bytes - node_filesystem_free_bytes) / node_filesystem_size_bytes * 100 > 85
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Low disk space on {{ $labels.instance }}"
          description: "Disk usage is {{ $value }}% on {{ $labels.instance }} mount {{ $labels.mountpoint }}"
```

### Complex Alert Examples

```yaml
groups:
  - name: application.alerts
    rules:
      - alert: HighErrorRate
        expr: |
          (
            sum(rate(http_requests_total{status=~"5.."}[5m])) by (job)
            /
            sum(rate(http_requests_total[5m])) by (job)
          ) * 100 > 5
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate for {{ $labels.job }}"
          description: "Error rate is {{ $value }}% for job {{ $labels.job }}"
          
      - alert: DatabaseConnectionsHigh
        expr: mysql_global_status_threads_connected / mysql_global_variables_max_connections * 100 > 80
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "High database connections"
          description: "Database connections are at {{ $value }}% of maximum"
```
