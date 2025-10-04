## Loki Data Source Configuration

### Basic Loki Data Source

```json
{
  "name": "Loki",
  "type": "loki",
  "url": "http://loki:3100",
  "access": "proxy",
  "jsonData": {
    "timeout": 60,
    "maxLines": 1000
  }
}
```

### Advanced Loki Configuration

```json
{
  "name": "Loki-Production",
  "type": "loki",
  "url": "http://loki-gateway:3100",
  "access": "proxy",
  "basicAuth": true,
  "basicAuthUser": "grafana",
  "secureJsonData": {
    "basicAuthPassword": "password"
  },
  "jsonData": {
    "timeout": 60,
    "maxLines": 5000,
    "derivedFields": [
      {
        "matcherRegex": "trace_id=(\\w+)",
        "name": "TraceID",
        "url": "${__value.raw}",
        "datasourceUid": "tempo"
      },
      {
        "matcherRegex": "request_id=(\\w+)",
        "name": "RequestID",
        "url": "/explore?left={\"queries\":[{\"expr\":\"{job=\\\"api\\\"} |= \\\"${__value.raw}\\\"\",\"refId\":\"A\"}]}"
      }
    ],
    "alertmanager": {
      "handleGrafanaManagedAlerts": true,
      "implementation": "prometheus"
    }
  }
}
```

### Provisioning Loki Data Source

```yaml
# /etc/grafana/provisioning/datasources/loki.yml
apiVersion: 1

datasources:
  - name: Loki
    type: loki
    access: proxy
    url: http://loki:3100
    isDefault: false
    editable: false
    jsonData:
      maxLines: 1000
      timeout: 60
      derivedFields:
        - matcherRegex: "trace_id=(\\w+)"
          name: TraceID
          url: "${__value.raw}"
          datasourceUid: tempo
        - matcherRegex: "traceID=(\\w+)"
          name: TraceID
          url: "${__value.raw}"
          datasourceUid: tempo
```

## LogQL Queries

### Basic LogQL Patterns

```logql
# Stream selector - all logs from job
{job="varlogs"}

# Filter logs containing "error"
{job="api"} |= "error"

# Filter logs NOT containing "debug"
{job="api"} != "debug"

# Regex filter
{job="api"} |~ "error|Error|ERROR"
{job="api"} !~ "debug|DEBUG"

# Multiple label matchers
{job="api", environment="production", level="error"}

# Line format parser
{job="nginx"} | json | line_format "{{.method}} {{.path}} {{.status}}"

# Label filter after parsing
{job="api"} | json | status_code >= 400
```

### Advanced LogQL Queries

```logql
# JSON parsing
{job="api"} | json | status_code=`500` | line_format "Error: {{.error_message}}"

# Logfmt parsing
{job="prometheus"} | logfmt | level="error"

# Regex pattern extraction
{job="nginx"} | regexp "(?P<method>\\w+) (?P<path>[\\w/]+) (?P<status>\\d+)"

# Multiple parsers
{job="api"} | json | line_format "{{.message}}" | logfmt

# Label filtering with operations
{job="api"} | json | duration > 1s
{job="api"} | json | bytes > 1024
{job="api"} | json | status_code >= 400 and status_code < 500

# Decolorize logs
{job="app"} | decolorize

# Unwrap for metrics
sum(rate({job="api"} | json | unwrap duration [5m]))
```

### Aggregation Queries

```logql
# Count log lines per second
rate({job="api"}[5m])

# Count by label
sum(rate({job="api"}[5m])) by (level)

# Count errors by status code
sum(rate({job="api"} |= "error" | json [5m])) by (status_code)

# Bytes per second
sum(rate({job="nginx"} | json | unwrap bytes [5m]))

# Quantiles
quantile_over_time(0.99, {job="api"} | json | unwrap duration [5m])

# Average duration
avg_over_time({job="api"} | json | unwrap duration [5m])

# Top N by count
topk(10, sum(rate({job="api"}[5m])) by (endpoint))

# Bottom N by count
bottomk(5, sum(rate({job="api"}[5m])) by (host))
```

### Pattern Matching

```logql
# Pattern extraction (structured logs)
{job="api"} | pattern "<method> <path> <status>"

# Pattern with types
{job="api"} | pattern "<method> <path> <status:int>"

# Multiple patterns
{job="api"}
  | pattern "<_> status=<status> duration=<duration>"
  | status >= 400

# Pattern with unwrap
sum(rate({job="api"}
  | pattern "duration=<duration>"
  | unwrap duration [5m])) by (endpoint)
```

## Dashboard Integration

### Log Panel with Variables

```json
{
  "type": "logs",
  "title": "Application Logs",
  "targets": [
    {
      "expr": "{job=\"$job\", environment=\"$environment\"} |= \"$search\" | json | level=~\"$level\"",
      "refId": "A"
    }
  ],
  "options": {
    "showTime": true,
    "showLabels": true,
    "showCommonLabels": false,
    "wrapLogMessage": true,
    "prettifyLogMessage": false,
    "enableLogDetails": true,
    "dedupStrategy": "none",
    "sortOrder": "Descending"
  }
}
```

### Log Volume Panel

```json
{
  "type": "graph",
  "title": "Log Volume",
  "targets": [
    {
      "expr": "sum(rate({job=\"$job\"}[1m])) by (level)",
      "refId": "A",
      "legendFormat": "{{level}}"
    }
  ],
  "fieldConfig": {
    "defaults": {
      "custom": {
        "drawStyle": "bars",
        "fillOpacity": 50
      },
      "unit": "logs/s"
    }
  }
}
```

### Error Rate Panel

```json
{
  "type": "stat",
  "title": "Error Rate",
  "targets": [
    {
      "expr": "sum(rate({job=\"$job\"} |= \"error\" [5m]))",
      "refId": "A"
    }
  ],
  "fieldConfig": {
    "defaults": {
      "unit": "logs/s",
      "thresholds": {
        "mode": "absolute",
        "steps": [
          {"value": null, "color": "green"},
          {"value": 1, "color": "yellow"},
          {"value": 10, "color": "red"}
        ]
      }
    }
  }
}
```

### Log Table with Extracted Fields

```json
{
  "type": "table",
  "title": "API Requests",
  "targets": [
    {
      "expr": "{job=\"api\"} | json | line_format \"{{.timestamp}}|{{.method}}|{{.path}}|{{.status_code}}|{{.duration}}\"",
      "refId": "A"
    }
  ],
  "transformations": [
    {
      "id": "extractFields",
      "options": {
        "source": "Line",
        "format": "auto"
      }
    }
  ],
  "options": {
    "showHeader": true,
    "sortBy": []
  }
}
```

## Derived Fields and Trace Correlation

### Tempo Trace Correlation

```json
{
  "name": "Loki",
  "type": "loki",
  "url": "http://loki:3100",
  "jsonData": {
    "derivedFields": [
      {
        "matcherRegex": "trace_id=(\\w+)",
        "name": "TraceID",
        "url": "${__value.raw}",
        "datasourceUid": "tempo",
        "urlDisplayLabel": "View Trace"
      },
      {
        "matcherRegex": "traceID=(\\w+)",
        "name": "TraceID",
        "url": "${__value.raw}",
        "datasourceUid": "tempo"
      },
      {
        "matcherRegex": "trace\"?:\"?([\\w-]+)",
        "name": "TraceID",
        "url": "${__value.raw}",
        "datasourceUid": "tempo"
      }
    ]
  }
}
```

### Jaeger Trace Correlation

```json
{
  "name": "Loki",
  "type": "loki",
  "url": "http://loki:3100",
  "jsonData": {
    "derivedFields": [
      {
        "matcherRegex": "trace_id=(\\w+)",
        "name": "TraceID",
        "url": "http://jaeger:16686/trace/${__value.raw}",
        "urlDisplayLabel": "View in Jaeger"
      }
    ]
  }
}
```

### Custom Log Links

```json
{
  "name": "Loki",
  "type": "loki",
  "url": "http://loki:3100",
  "jsonData": {
    "derivedFields": [
      {
        "matcherRegex": "pod=(\\w+-\\w+-\\w+)",
        "name": "Pod",
        "url": "/explore?left={\"datasource\":\"Loki\",\"queries\":[{\"expr\":\"{pod=\\\"${__value.raw}\\\"}\"}]}",
        "urlDisplayLabel": "View Pod Logs"
      },
      {
        "matcherRegex": "request_id=(\\w+)",
        "name": "RequestID",
        "url": "/explore?left={\"datasource\":\"Loki\",\"queries\":[{\"expr\":\"{job=~\\\".*\\\"} |= \\\"${__value.raw}\\\"\"}]}",
        "urlDisplayLabel": "View Request"
      },
      {
        "matcherRegex": "user_id=(\\d+)",
        "name": "UserID",
        "url": "https://admin.example.com/users/${__value.raw}",
        "urlDisplayLabel": "View User"
      }
    ]
  }
}
```

## Log Aggregation Patterns

### HTTP Request Metrics

```json
{
  "type": "graph",
  "title": "HTTP Request Rate by Status",
  "targets": [
    {
      "expr": "sum(rate({job=\"nginx\"} | json | __error__=\"\" [5m])) by (status)",
      "refId": "A",
      "legendFormat": "{{status}}"
    }
  ]
}
```

### Request Duration Percentiles

```json
{
  "type": "graph",
  "title": "Request Duration Percentiles",
  "targets": [
    {
      "expr": "quantile_over_time(0.50, {job=\"api\"} | json | unwrap duration [5m])",
      "refId": "A",
      "legendFormat": "p50"
    },
    {
      "expr": "quantile_over_time(0.95, {job=\"api\"} | json | unwrap duration [5m])",
      "refId": "B",
      "legendFormat": "p95"
    },
    {
      "expr": "quantile_over_time(0.99, {job=\"api\"} | json | unwrap duration [5m])",
      "refId": "C",
      "legendFormat": "p99"
    }
  ]
}
```

### Error Rate by Service

```json
{
  "type": "graph",
  "title": "Error Rate by Service",
  "targets": [
    {
      "expr": "sum(rate({job=~\".*\"} |~ \"error|Error|ERROR\" [5m])) by (job)",
      "refId": "A",
      "legendFormat": "{{job}}"
    }
  ]
}
```

### Log Volume Heatmap

```json
{
  "type": "heatmap",
  "title": "Log Volume Over Time",
  "targets": [
    {
      "expr": "sum(count_over_time({job=\"$job\"}[1m])) by (level)",
      "refId": "A"
    }
  ],
  "options": {
    "calculate": false,
    "yAxis": {
      "format": "short",
      "decimals": 0
    }
  }
}
```

## Multi-tenancy Patterns

### Tenant Filtering

```logql
# Filter by tenant label
{job="api", tenant="customer-a"}

# Dynamic tenant variable
{job="api", tenant="$tenant"}

# Multiple tenants
{job="api", tenant=~"customer-a|customer-b"}

# Exclude tenants
{job="api", tenant!~"internal|test"}
```

### Tenant Dashboard

```json
{
  "templating": {
    "list": [
      {
        "name": "tenant",
        "type": "query",
        "datasource": "Loki",
        "query": "label_values({job=\"api\"}, tenant)",
        "multi": false,
        "includeAll": false
      }
    ]
  },
  "panels": [
    {
      "type": "logs",
      "targets": [
        {
          "expr": "{job=\"api\", tenant=\"$tenant\"}"
        }
      ]
    }
  ]
}
```

## Performance Optimization

### Query Optimization

```logql
# Bad: Unfiltered query
{job="api"}

# Good: Add time-based filters
{job="api"} | json | timestamp > now() - 1h

# Bad: Regex on every log line
{job="api"} |~ ".*error.*"

# Good: Exact match then filter
{job="api"} |= "error"

# Bad: Parse all logs
{job="api"} | json

# Good: Filter first, then parse
{job="api"} |= "error" | json

# Bad: Complex regex
{job="api"} |~ "(?i)error|exception|failed|timeout"

# Good: Multiple simple filters
{job="api"} |= "error" or {job="api"} |= "exception"

# Use label filters when possible
{job="api", level="error"}  # Better than filtering in LogQL
```

### Caching Strategy

```yaml
# Loki configuration for caching
query_range:
  results_cache:
    cache:
      redis:
        endpoint: redis:6379
        expiration: 1h

# Split queries for better caching
query_range:
  split_queries_by_interval: 24h
  align_queries_with_step: true
```

### Rate Limiting

```yaml
# Loki configuration
limits_config:
  max_query_length: 721h
  max_query_parallelism: 32
  max_streams_per_user: 10000
  max_global_streams_per_user: 0
  max_chunks_per_query: 2000000
  max_entries_limit_per_query: 5000
```

## Alerting on Logs

### Log-Based Alerts

```yaml
apiVersion: 1
groups:
  - name: log-alerts
    interval: 1m
    rules:
      - alert: HighErrorRate
        expr: |
          sum(rate({job="api"} |= "error" [5m])) > 10
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }} errors/sec"

      - alert: CriticalErrors
        expr: |
          sum(rate({job="api"} |~ "CRITICAL|FATAL" [5m])) > 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Critical errors detected"
          description: "{{ $value }} critical errors/sec"

      - alert: HighLatency
        expr: |
          quantile_over_time(0.99, {job="api"} | json | unwrap duration [5m]) > 1000
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High latency detected"
          description: "P99 latency is {{ $value }}ms"

      - alert: FailedLogins
        expr: |
          sum(rate({job="auth"} |= "failed login" [5m])) by (username) > 5
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "Multiple failed login attempts"
          description: "{{ $labels.username }} has {{ $value }} failed logins/sec"
```

### Pattern-Based Alerts

```yaml
apiVersion: 1
groups:
  - name: pattern-alerts
    interval: 1m
    rules:
      - alert: OutOfMemory
        expr: |
          sum(rate({job=~".*"} |~ "OutOfMemoryError|OOM" [5m])) > 0
        labels:
          severity: critical
        annotations:
          summary: "Out of memory errors detected"

      - alert: DatabaseConnectionFailure
        expr: |
          sum(rate({job="api"} |~ "connection.*refused|connection.*timeout" [5m])) > 1
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Database connection issues"

      - alert: SSLCertificateExpiring
        expr: |
          sum(rate({job=~".*"} |~ "certificate.*expir" [1h])) > 0
        labels:
          severity: warning
        annotations:
          summary: "SSL certificate expiring soon"
```

## Log Sampling

### Recording Rules for Logs

```yaml
# Loki ruler configuration
ruler:
  enable_api: true
  storage:
    type: local
    local:
      directory: /tmp/loki/rules

# Recording rules
apiVersion: 1
groups:
  - name: log-metrics
    interval: 1m
    rules:
      - record: job:log_rate:5m
        expr: sum(rate({job=~".*"}[5m])) by (job)

      - record: job:error_rate:5m
        expr: sum(rate({job=~".*"} |= "error" [5m])) by (job)

      - record: job_status:http_requests:rate5m
        expr: sum(rate({job="nginx"} | json [5m])) by (job, status)

      - record: job:latency_p99:5m
        expr: quantile_over_time(0.99, {job="api"} | json | unwrap duration [5m]) by (job)
```

### Sampling Configuration

```yaml
# Promtail sampling
scrape_configs:
  - job_name: high-volume-app
    pipeline_stages:
      # Sample 10% of debug logs
      - match:
          selector: '{app="high-volume"} |= "DEBUG"'
          stages:
            - sampling:
                rate: 0.1
      # Keep all error logs
      - match:
          selector: '{app="high-volume"} |= "ERROR"'
          stages:
            - labels:
                sampled: "false"
```

## Log Exploration Workflows

### Explore Mode Best Practices

```logql
# 1. Start with stream selector
{job="api"}

# 2. Add label filters
{job="api", environment="production"}

# 3. Add line filters
{job="api", environment="production"} |= "error"

# 4. Parse structured logs
{job="api", environment="production"} |= "error" | json

# 5. Filter on parsed fields
{job="api", environment="production"} |= "error" | json | status_code >= 500

# 6. Format output
{job="api", environment="production"}
  |= "error"
  | json
  | status_code >= 500
  | line_format "{{.timestamp}} [{{.level}}] {{.message}}"
```

### Live Tail

```yaml
# Enable live tail in Grafana
# Explore → Loki → Click "Live" button

# Useful for:
# - Debugging in real-time
# - Monitoring deployments
# - Watching specific requests
# - Investigating incidents

# Live tail with filters
{job="api", environment="production"}
  |= "user_id=12345"
  | json
```

## Complete Example Dashboard

```json
{
  "dashboard": {
    "title": "Application Logs",
    "tags": ["logs", "loki"],
    "timezone": "browser",
    "refresh": "30s",
    "templating": {
      "list": [
        {
          "name": "job",
          "type": "query",
          "datasource": "Loki",
          "query": "label_values(job)",
          "multi": true,
          "includeAll": true
        },
        {
          "name": "level",
          "type": "query",
          "datasource": "Loki",
          "query": "label_values({job=\"$job\"}, level)",
          "multi": true,
          "includeAll": true
        },
        {
          "name": "search",
          "type": "textbox",
          "label": "Search"
        }
      ]
    },
    "panels": [
      {
        "id": 1,
        "type": "stat",
        "title": "Total Log Rate",
        "gridPos": {"x": 0, "y": 0, "w": 6, "h": 4},
        "targets": [
          {
            "expr": "sum(rate({job=~\"$job\"}[5m]))",
            "refId": "A"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "logs/s"
          }
        }
      },
      {
        "id": 2,
        "type": "stat",
        "title": "Error Rate",
        "gridPos": {"x": 6, "y": 0, "w": 6, "h": 4},
        "targets": [
          {
            "expr": "sum(rate({job=~\"$job\"} |= \"error\" [5m]))",
            "refId": "A"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "logs/s",
            "thresholds": {
              "steps": [
                {"value": null, "color": "green"},
                {"value": 1, "color": "yellow"},
                {"value": 10, "color": "red"}
              ]
            }
          }
        }
      },
      {
        "id": 3,
        "type": "graph",
        "title": "Log Volume by Level",
        "gridPos": {"x": 0, "y": 4, "w": 12, "h": 8},
        "targets": [
          {
            "expr": "sum(rate({job=~\"$job\"}[1m])) by (level)",
            "refId": "A",
            "legendFormat": "{{level}}"
          }
        ]
      },
      {
        "id": 4,
        "type": "logs",
        "title": "Logs",
        "gridPos": {"x": 0, "y": 12, "w": 24, "h": 12},
        "targets": [
          {
            "expr": "{job=~\"$job\"} |= \"$search\" | json | level=~\"$level\"",
            "refId": "A"
          }
        ],
        "options": {
          "showTime": true,
          "showLabels": true,
          "wrapLogMessage": true,
          "enableLogDetails": true
        }
      }
    ]
  }
}
```
