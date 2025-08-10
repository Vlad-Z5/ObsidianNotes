## Production Queries & Transformations Runbook

### Essential LogQL Query Patterns

#### Basic Log Filtering
```bash
# Service-specific error logs
{job="webapp", environment="prod"} |= "ERROR"

# Multi-service error tracking
{environment="prod", service=~"api|web|auth"} |= "ERROR"

# Exclude specific log types
{job="webapp"} |= "ERROR" != "health check"

# Case-insensitive matching
{job="webapp"} |~ "(?i)error|exception|failed"

# JSON log parsing with field filtering
{job="webapp"} | json | level="error" | message!=""
```

#### Advanced LogQL Operations
```bash
# Extract specific fields from structured logs
{job="webapp"} | json | line_format "{{.timestamp}} [{{.level}}] {{.message}}"

# Pattern extraction with regex
{job="webapp"} | regexp "user_id=(?P<user>\\d+)" | user != ""

# Label formatting for better visualization  
{job="webapp"} | json | label_format level="{{.level | upper}}"

# Unwrap numeric values for calculations
{job="webapp"} | json | unwrap duration

# Filter by numeric values
{job="webapp"} | json | duration > 1000
```

#### Log Aggregation Queries
```bash
# Error count by service (last 5 minutes)
sum by (service) (count_over_time({environment="prod"} |= "ERROR" [5m]))

# Error rate calculation
sum by (service) (rate({environment="prod"} |= "ERROR" [5m]))

# Top 10 error messages
topk(10, sum by (message) (count_over_time({job="webapp"} |= "ERROR" | json [1h])))

# Unique user count affected by errors
count by (service) (count by (user_id, service) ({environment="prod"} |= "ERROR" | json | user_id != "" [1h]))

# Average response time
avg_over_time({service="api"} | json | unwrap duration [5m])
```

#### Performance Analysis Queries
```bash
# Response time percentiles
quantile_over_time(0.95, {service="api"} | json | unwrap duration [5m])

# Request volume by endpoint
sum by (endpoint) (count_over_time({service="api"} | json [5m]))

# Slow query detection
{service="database"} | json | duration > 5000 | line_format "Slow query: {{.query}} ({{.duration}}ms)"

# Memory usage tracking
{job="app"} | json | unwrap memory_mb | memory_mb > 1000

# Disk space monitoring
{job="system"} |~ "disk.*full|no.*space" | json
```

### Data Transformations

#### 1. Organize Transformation
```json
{
  "id": "organize",
  "options": {
    "excludeByName": {
      "__name__": true,
      "job": true
    },
    "indexByName": {
      "service": 0,
      "error_count": 1,
      "timestamp": 2
    },
    "renameByName": {
      "Value": "Error Count",
      "service": "Service Name",
      "Time": "Timestamp"
    }
  }
}
```

#### 2. Filter Data by Value
```json
{
  "id": "filterFieldsByName",
  "options": {
    "include": {
      "pattern": "/(error|warning|critical)/i"
    }
  }
}
```

#### 3. Group By Transformation
```json
{
  "id": "groupBy",
  "options": {
    "fields": {
      "service": {
        "aggregations": [],
        "operation": "groupby"
      },
      "error_count": {
        "aggregations": ["sum", "count"],
        "operation": "aggregate"
      },
      "response_time": {
        "aggregations": ["mean", "max"],
        "operation": "aggregate"
      }
    }
  }
}
```

#### 4. Add Field from Calculation
```json
{
  "id": "calculateField",
  "options": {
    "alias": "error_rate_percent",
    "binary": {
      "left": "errors",
      "operator": "/",
      "reducer": "sum",
      "right": "total_requests"
    },
    "mode": "binary",
    "reduce": {
      "reducer": "sum"
    },
    "replaceNonNumeric": true
  }
}
```

#### 5. Sort Data
```json
{
  "id": "sortBy",
  "options": {
    "fields": {},
    "sort": [
      {
        "field": "error_count",
        "desc": true
      }
    ]
  }
}
```

### Complex Query Examples

#### Multi-Step Error Analysis
```bash
# Step 1: Get error logs with extracted fields
{environment="prod"} |= "ERROR" | json | __error__="" | service!="" | error_type!=""

# Step 2: Aggregate by service and error type  
sum by (service, error_type) (count_over_time({environment="prod"} |= "ERROR" | json | __error__="" [1h]))

# Step 3: Calculate error distribution
(
  sum by (service, error_type) (count_over_time({environment="prod"} |= "ERROR" | json [1h]))
  /
  sum by (service) (count_over_time({environment="prod"} |= "ERROR" | json [1h]))
) * 100
```

#### User Journey Analysis
```bash
# Track user actions with errors
{service="webapp"} | json | user_id!="" | 
line_format "{{.timestamp}} User:{{.user_id}} Action:{{.action}} {{if eq .level \"ERROR\"}}❌{{else}}✅{{end}}"

# User error session correlation
sum by (user_id) (count_over_time({service="webapp"} |= "ERROR" | json | user_id!="" [30m]))

# User impact by feature
sum by (feature, error_type) (count_over_time({service="webapp"} |= "ERROR" | json | user_id!="" [1h]))
```

#### Performance Correlation
```bash
# Correlate errors with response times
# Query A: Error rate
sum by (service) (rate({environment="prod"} |= "ERROR" [5m]))

# Query B: Average response time
avg by (service) (avg_over_time({environment="prod"} | json | unwrap duration [5m]))

# Use math expression: A * 1000 + B to combine metrics
```

### Advanced Transformation Patterns

#### Time Series Alignment
```json
{
  "id": "joinByField",
  "options": {
    "byField": "Time",
    "mode": "outer"
  }
}
```

#### Data Formatting
```json
{
  "id": "convertFieldType",
  "options": {
    "conversions": [
      {
        "destinationType": "number",
        "targetField": "duration_ms"
      },
      {
        "destinationType": "time",
        "targetField": "timestamp"
      }
    ]
  }
}
```

#### Conditional Formatting
```json
{
  "id": "fieldOverride",
  "matcher": {
    "id": "byName",
    "options": "error_count"
  },
  "properties": [
    {
      "id": "mappings",
      "value": [
        {
          "options": {
            "from": 0,
            "result": {
              "color": "green",
              "index": 0,
              "text": "Healthy"
            },
            "to": 5
          },
          "type": "range"
        },
        {
          "options": {
            "from": 6,
            "result": {
              "color": "red",
              "index": 1,
              "text": "Unhealthy"
            },
            "to": null
          },
          "type": "range"
        }
      ]
    }
  ]
}
```

### Query Optimization Techniques

#### Performance Best Practices
```bash
# 1. Use specific label filters first
{service="api", environment="prod"} |= "ERROR"  # Good
{} |= "ERROR" | json | service="api"  # Bad - filters after parsing

# 2. Limit time range for expensive operations
sum by (service) (count_over_time({job="webapp"} [5m]))  # Good
sum by (service) (count_over_time({job="webapp"} [24h])) # Expensive

# 3. Use line filters before JSON parsing
{job="webapp"} |= "ERROR" | json  # Good
{job="webapp"} | json | level="error"  # Less efficient

# 4. Avoid regex when possible
{job="webapp"} |= "ERROR" != "health"  # Good
{job="webapp"} |~ "ERROR.*(?!health)"  # More expensive

# 5. Use recording rules for complex aggregations
recorded_error_rate  # Pre-calculated rule
sum(rate(error_total[5m])) / sum(rate(requests_total[5m]))  # Calculate each time
```

#### Query Caching Strategies
```bash
# Cache expensive aggregation queries
sum by (service) (count_over_time({environment="prod"} [1h]))

# Use dashboard variables to reduce query variations
{environment="$environment", service=~"$service"}

# Implement query result caching in dashboard settings
"cacheTimeout": "5m"
```

### Multi-Source Query Patterns

#### Combining Loki with Prometheus
```bash
# Panel with mixed data sources
# Query A (Loki): Error count from logs
sum by (service) (count_over_time({environment="prod"} |= "ERROR" [5m]))

# Query B (Prometheus): Request rate from metrics
sum by (service) (rate(http_requests_total[5m]))

# Query C (Expression): Error percentage
(A / B) * 100
```

#### Cross-Service Correlation
```bash
# Frontend errors correlated with backend issues
# Query A: Frontend errors
sum by (page) (count_over_time({service="frontend"} |= "ERROR" [5m]))

# Query B: Backend API errors  
sum by (endpoint) (count_over_time({service="backend"} |= "ERROR" [5m]))

# Use table transformation to join by time
```

### Troubleshooting Queries

#### Common Query Issues
```bash
# Issue: "parse error" in LogQL
# Fix: Check JSON structure and field names
{job="webapp"} | json | __error__="" | field_name!=""

# Issue: No data returned
# Fix: Verify label existence and time range
curl "http://loki:3100/loki/api/v1/labels"
curl "http://loki:3100/loki/api/v1/label/job/values"

# Issue: Query timeout
# Fix: Add more specific filters and reduce time range
{job="webapp", service="api"} |= "ERROR" [5m]  # Not [24h]

# Issue: Incorrect aggregation results
# Fix: Check grouping labels and time alignment
sum by (service) (rate({job="webapp"} |= "ERROR" [5m]))
```

#### Query Debugging Tools
```bash
# Test LogQL directly against Loki
logcli query '{job="webapp"} |= "ERROR"' --limit=10 --stats

# Check query performance
curl -G "http://loki:3100/loki/api/v1/query" \
  --data-urlencode 'query=sum by (service) (rate({environment="prod"} |= "ERROR" [5m]))' \
  --data-urlencode 'stats=true'

# Validate JSON parsing
echo '{"level":"error","message":"test"}' | \
curl -X POST "http://loki:3100/loki/api/v1/push" \
  -H "Content-Type: application/json" \
  -d @-
```

### Production Query Templates

#### Incident Response Queries
```bash
# Error spike detection
sum by (service) (increase({environment="prod"} |= "ERROR" [5m]))

# User impact assessment
count by (service) (count by (user_id, service) ({environment="prod"} |= "ERROR" | json | user_id!="" [15m]))

# Service dependency failure
{service=~"database|cache|queue"} |~ "connection|timeout|unavailable"

# Performance degradation
avg_over_time({service="api"} | json | unwrap response_time [10m]) > 2000
```

#### Capacity Planning Queries
```bash
# Log volume growth
sum by (service) (count_over_time({environment="prod"} [1h]))

# Peak usage patterns
max_over_time(sum by (service) (rate({environment="prod"} [1m])) [24h])

# Resource utilization correlation
{job="system"} | json | unwrap cpu_percent | cpu_percent > 80
```

#### Security Monitoring Queries
```bash
# Failed authentication attempts
{service="auth"} |~ "authentication.*failed|login.*failed|invalid.*credentials"

# Suspicious access patterns
{service="api"} | json | status_code="401" | rate > 10

# Data access violations
{service="database"} |~ "access.*denied|permission.*denied|unauthorized"

# Network security events
{job="firewall"} |~ "blocked|denied|rejected" | json
```

### Best Practices Summary

#### Query Design Principles
```bash
1. Start with specific labels, add filters progressively
2. Use line filters before JSON parsing
3. Avoid overly broad regex patterns
4. Implement proper error handling (__error__="")
5. Use appropriate aggregation time windows

6. Test queries with small time ranges first
7. Monitor query performance and resource usage
8. Use recording rules for frequently used complex queries
9. Document query logic for team understanding
10. Implement query versioning for dashboard changes
```

#### Performance Guidelines
```bash
# Query execution time targets:
- Simple filters: <100ms
- JSON parsing + aggregation: <1s
- Complex multi-step queries: <5s
- Historical analysis: <30s

# Resource usage limits:
- Concurrent queries per dashboard: <10
- Memory usage per query: <100MB
- Query result size: <1M data points
```