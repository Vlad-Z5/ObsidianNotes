## Production Dashboard Creation Runbook

### Quick Dashboard Creation (5-minute setup)
```bash
# 1. Create dashboard via API (faster than UI)
curl -X POST \
  -H "Authorization: Bearer $GRAFANA_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "dashboard": {
      "title": "Production System Monitor",
      "tags": ["production", "monitoring"],
      "refresh": "30s",
      "time": {"from": "now-1h", "to": "now"}
    }
  }' \
  http://grafana:3000/api/dashboards/db

# 2. Get dashboard UID from response, then add panels
```

### Essential Production Dashboard Layout

#### Row 1: System Health (Always at top)
```json
{
  "title": "System Health Overview",
  "panels": [
    {
      "title": "Services Up",
      "type": "stat",
      "targets": [{
        "expr": "up == 1",
        "legendFormat": "{{job}}"
      }],
      "gridPos": {"h": 4, "w": 6, "x": 0, "y": 0}
    },
    {
      "title": "Error Rate",
      "type": "stat", 
      "targets": [{
        "expr": "rate(http_requests_total{status=~\"5..\"}[5m]) / rate(http_requests_total[5m]) * 100",
        "legendFormat": "Error %"
      }],
      "gridPos": {"h": 4, "w": 6, "x": 6, "y": 0}
    }
  ]
}
```

#### Row 2: Loki Log Analysis (Critical for troubleshooting)
```json
{
  "title": "Application Errors (Last 15min)",
  "type": "logs",
  "datasource": "Loki",
  "targets": [{
    "expr": "{job=\"webapp\"} |= \"ERROR\" | json",
    "refId": "A"
  }],
  "gridPos": {"h": 8, "w": 24, "x": 0, "y": 8},
  "options": {
    "showTime": true,
    "showLabels": false,
    "showCommonLabels": false,
    "wrapLogMessage": false,
    "prettifyLogMessage": true,
    "enableLogDetails": true,
    "deduplication": true,
    "sortOrder": "Descending"
  }
}
```

## Loki Integration Patterns (Production Ready)

### 1. Error Detection Dashboard
```json
{
  "title": "Error Pattern Analysis",
  "type": "table",
  "datasource": "Loki",
  "targets": [{
    "expr": "sum by (level, service) (count_over_time({environment=\"prod\"} |= \"ERROR\" [1h]))",
    "refId": "A",
    "legendFormat": "{{service}} - {{level}}"
  }],
  "transformations": [{
    "id": "groupBy",
    "options": {
      "fields": {
        "service": {"aggregations": [], "operation": "groupby"},
        "Value": {"aggregations": ["sum"], "operation": "aggregate"}
      }
    }
  }]
}
```

### 2. Log Volume Monitoring (Prevent log storage issues)
```json
{
  "title": "Log Ingestion Rate by Service",
  "type": "timeseries",
  "datasource": "Loki", 
  "targets": [{
    "expr": "rate(loki_distributor_lines_received_total[5m])",
    "refId": "A",
    "legendFormat": "{{job}}"
  }],
  "fieldConfig": {
    "defaults": {
      "unit": "logs/sec",
      "thresholds": {
        "steps": [
          {"color": "green", "value": null},
          {"color": "yellow", "value": 1000},
          {"color": "red", "value": 5000}
        ]
      }
    }
  }
}
```

### 3. Deployment Correlation (Link logs to deployments)
```json
{
  "title": "Deployment vs Error Rate",
  "type": "timeseries",
  "datasource": "Mixed",
  "targets": [
    {
      "datasource": "Loki",
      "expr": "sum(rate({job=\"webapp\"} |= \"ERROR\" [5m]))",
      "refId": "A",
      "legendFormat": "Error Rate"
    },
    {
      "datasource": "Prometheus", 
      "expr": "changes(deployment_version[5m])",
      "refId": "B",
      "legendFormat": "Deployments"
    }
  ]
}
```

## Advanced Loki Query Patterns

### LogQL Runbook Commands
```bash
# Real-time error tracking
{job="webapp"} |= "ERROR" | json | level="error"

# Performance issue detection
{service="api"} | json | duration > 5s

# User impact analysis
{service="frontend"} |= "user_id" | regexp "user_id=(?P<user>\\w+)" | user != ""

# Memory leak detection
{job="app"} |= "memory" | regexp "memory: (?P<memory>\\d+)" | memory > 1000000000

# Authentication failures
{service="auth"} |~ "login.*failed|authentication.*error" | json

# Database slow queries  
{job="postgres"} | json | duration > 1000ms | __error__ = ""

# Network connectivity issues
{job="networking"} |= "timeout" or "connection refused" or "dns resolution failed"
```

### Log Aggregation for Alerting
```bash
# Critical error rate (for alerting rules)
sum(rate({environment="prod"} |= "CRITICAL" [5m])) > 0

# Application response time degradation
avg_over_time({service="api"} | json | __error__ = "" | unwrap duration [5m]) > 2000

# Failed authentication spike
sum(rate({service="auth"} |= "login failed" [1m])) > 10

# Disk space issues
sum by (instance) (rate({job="node"} |= "disk.*full" [5m])) > 0
```

## Dashboard Variables for Dynamic Filtering

### Environment Variable (Essential for multi-env)
```json
{
  "name": "environment",
  "type": "query",
  "datasource": "Loki",
  "query": "label_values(environment)",
  "current": {"value": "prod"},
  "multi": true,
  "includeAll": true
}
```

### Service Variable (For service-specific views)
```json
{
  "name": "service",
  "type": "query", 
  "datasource": "Loki",
  "query": "label_values({environment=\"$environment\"}, service)",
  "current": {"value": "All"},
  "multi": true,
  "includeAll": true
}
```

### Time Window Variable (For incident analysis)
```json
{
  "name": "time_window",
  "type": "custom",
  "options": [
    {"text": "5 minutes", "value": "5m"},
    {"text": "15 minutes", "value": "15m"},
    {"text": "1 hour", "value": "1h"},
    {"text": "4 hours", "value": "4h"}
  ],
  "current": {"value": "15m"}
}
```

## Production Dashboard Patterns

### 1. Incident Response Dashboard
```bash
# Purpose: Quick incident identification and root cause
Row 1: Service health status (all services, 4x stat panels)
Row 2: Error rate trends (timeseries, 24w)
Row 3: Critical logs (Loki logs panel, 24w, last 30min)
Row 4: Performance metrics (CPU/Memory, 2x12w)
Row 5: Recent deployments (annotations + table)
```

### 2. Application Performance Dashboard  
```bash
# Purpose: Ongoing performance monitoring
Row 1: KPIs (Response time, Throughput, Error rate - 3x8w)
Row 2: Request patterns (timeseries by endpoint, 24w)
Row 3: Slow queries (Loki table, top 10 slowest, 12w)
Row 4: User activity (Loki pattern analysis, 12w)
```

### 3. Infrastructure Health Dashboard
```bash
# Purpose: System-level monitoring
Row 1: Node status (up/down, 6x4w)
Row 2: Resource usage (CPU, Memory, Disk, Network - 4x6w) 
Row 3: System logs (Loki, critical/error level, 24w)
Row 4: Network connectivity (service mesh status, 24w)
```

## Alert Integration

### Dashboard Alerts with Loki
```json
{
  "alert": {
    "name": "High Error Rate",
    "frequency": "1m",
    "conditions": [
      {
        "query": {
          "queryType": "",
          "refId": "A",
          "datasource": "Loki",
          "model": {
            "expr": "sum(rate({environment=\"prod\"} |= \"ERROR\" [5m])) > 5"
          }
        }
      }
    ],
    "message": "Error rate exceeded threshold\nRunbook: https://docs.company.com/runbooks/high-error-rate"
  }
}
```

## Troubleshooting Common Issues

### Dashboard Not Loading
```bash
# 1. Check data source connectivity
curl -H "Authorization: Bearer $TOKEN" http://grafana:3000/api/datasources

# 2. Verify Loki is accessible
curl http://loki:3100/ready

# 3. Test LogQL query directly
curl -G -s "http://loki:3100/loki/api/v1/query" \
  --data-urlencode 'query={job="webapp"}' \
  --data-urlencode 'time=2023-01-01T12:00:00Z'
```

### No Data in Loki Panels
```bash
# 1. Check log ingestion
curl -s "http://loki:3100/loki/api/v1/labels"

# 2. Verify promtail is running  
curl http://promtail:9080/metrics | grep promtail_targets_active_total

# 3. Check log format compatibility
tail -f /var/log/app.log | grep -E "ERROR|WARN"
```

### Slow Dashboard Performance
```bash
# 1. Optimize LogQL queries (add more specific labels)
{job="webapp", environment="prod"} |= "ERROR"  # Good
{} |= "ERROR"  # Bad - too broad

# 2. Reduce time range for expensive queries
# 3. Use recording rules for complex aggregations
# 4. Implement dashboard query caching
```

## Dashboard Export/Import for Reproducibility

### Export with Variables
```bash
# Export dashboard with all settings
curl -H "Authorization: Bearer $TOKEN" \
  "http://grafana:3000/api/dashboards/uid/$UID" | \
  jq '.dashboard' > production-dashboard.json

# Import to different Grafana instance
curl -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d @production-dashboard.json \
  http://grafana-staging:3000/api/dashboards/db
```

### Version Control Integration
```bash
# Store dashboards in git
mkdir -p grafana/dashboards/production/
cp *.json grafana/dashboards/production/

# Automated deployment
for dashboard in grafana/dashboards/production/*.json; do
  curl -X POST -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d @"$dashboard" \
    http://grafana:3000/api/dashboards/db
done
```