## Production Variables & Templating Runbook

### Essential Variables for Production Dashboards

#### 1. Environment Variable (Critical)
```json
{
  "name": "environment",
  "label": "Environment",
  "type": "query",
  "datasource": "Loki",
  "query": "label_values(environment)",
  "current": {
    "value": "prod",
    "text": "Production"
  },
  "options": [],
  "includeAll": false,
  "multi": false,
  "allValue": null,
  "refresh": 1,
  "regex": "",
  "sort": 1,
  "hide": 0
}
```

#### 2. Service Variable (For Multi-Service Monitoring)
```json
{
  "name": "service",
  "label": "Service",
  "type": "query", 
  "datasource": "Loki",
  "query": "label_values({environment=\"$environment\"}, service)",
  "current": {
    "value": ["All"],
    "text": ["All"]
  },
  "options": [],
  "includeAll": true,
  "multi": true,
  "allValue": ".*",
  "refresh": 1,
  "regex": "",
  "sort": 1,
  "hide": 0
}
```

#### 3. Instance Variable (Node-Level Filtering)
```json
{
  "name": "instance",
  "label": "Instance",
  "type": "query",
  "datasource": "Loki", 
  "query": "label_values({environment=\"$environment\", service=~\"$service\"}, instance)",
  "current": {
    "value": ["All"],
    "text": ["All"]
  },
  "options": [],
  "includeAll": true,
  "multi": true,
  "allValue": ".*",
  "refresh": 2,
  "regex": "/([^:]+):.*/",
  "sort": 1,
  "hide": 0
}
```

#### 4. Log Level Variable (Error Filtering)
```json
{
  "name": "log_level",
  "label": "Log Level",
  "type": "custom",
  "options": [
    {"text": "All", "value": ".*", "selected": true},
    {"text": "ERROR", "value": "ERROR", "selected": false},
    {"text": "WARN", "value": "WARN", "selected": false},
    {"text": "INFO", "value": "INFO", "selected": false},
    {"text": "DEBUG", "value": "DEBUG", "selected": false}
  ],
  "current": {
    "value": ".*",
    "text": "All"
  },
  "includeAll": false,
  "multi": true,
  "allValue": ".*",
  "refresh": 0,
  "hide": 0
}
```

#### 5. Time Window Variable (Incident Analysis)
```json
{
  "name": "time_window",
  "label": "Time Window",
  "type": "custom",
  "options": [
    {"text": "1 minute", "value": "1m", "selected": false},
    {"text": "5 minutes", "value": "5m", "selected": true},
    {"text": "15 minutes", "value": "15m", "selected": false},
    {"text": "1 hour", "value": "1h", "selected": false},
    {"text": "4 hours", "value": "4h", "selected": false}
  ],
  "current": {
    "value": "5m",
    "text": "5 minutes"
  },
  "includeAll": false,
  "multi": false,
  "refresh": 0,
  "hide": 0
}
```

### Advanced Loki Variables

#### User ID Variable (Customer Impact Analysis)
```json
{
  "name": "user_id",
  "label": "User ID",
  "type": "textbox",
  "current": {
    "value": "",
    "text": ""
  },
  "options": [],
  "query": "",
  "hide": 0
}
```

#### Error Pattern Variable (Dynamic Error Filtering)
```json
{
  "name": "error_pattern",
  "label": "Error Pattern",
  "type": "query",
  "datasource": "Loki",
  "query": "label_values({environment=\"$environment\", service=~\"$service\"} |= \"ERROR\" | json, error_type)",
  "current": {
    "value": ["All"],
    "text": ["All"]
  },
  "options": [],
  "includeAll": true,
  "multi": true,
  "allValue": ".*",
  "refresh": 2,
  "sort": 1,
  "hide": 0
}
```

#### Namespace Variable (Kubernetes Integration)
```json
{
  "name": "namespace",
  "label": "Namespace",
  "type": "query",
  "datasource": "Loki",
  "query": "label_values({environment=\"$environment\"}, namespace)",
  "current": {
    "value": "default",
    "text": "default"
  },
  "options": [],
  "includeAll": true,
  "multi": true,
  "allValue": ".*",
  "refresh": 1,
  "sort": 1,
  "hide": 0
}
```

## Variable Usage in Loki Queries

### Basic LogQL with Variables
```bash
# Environment and service filtering
{environment=\"$environment\", service=~\"$service\"}

# Multi-service with log level filtering
{environment=\"$environment\", service=~\"$service\"} |~ \"$log_level\"

# Instance-specific logs with error pattern
{environment=\"$environment\", instance=~\"$instance\"} |= \"ERROR\" | json | error_type=~\"$error_pattern\"

# User-specific error tracking
{environment=\"$environment\", service=~\"$service\"} |= \"ERROR\" | json | user_id=\"$user_id\"

# Time window aggregation
sum by (service) (rate({environment=\"$environment\"} |= \"ERROR\" [$time_window]))
```

### Advanced LogQL Patterns
```bash
# Dynamic error rate calculation
sum by (service) (rate({environment=\"$environment\", service=~\"$service\"} |~ \"$log_level\" [$time_window])) / 
sum by (service) (rate({environment=\"$environment\", service=~\"$service\"} [$time_window])) * 100

# User impact analysis with variables
count by (service) (
  count by (user_id, service) (
    {environment=\"$environment\", service=~\"$service\"} |= \"ERROR\" | json | user_id!=\"\"
  ) [$time_window]
)

# Performance degradation detection
avg_over_time({environment=\"$environment\", service=~\"$service\"} | json | __error__=\"\" | unwrap duration [$time_window]) > 2000

# Resource usage correlation
{environment=\"$environment\", service=~\"$service\"} |~ \"memory|cpu\" | json | resource_usage > 80
```

## Template Functions & Formatting

### Label Formatting
```bash
# Service name cleanup
${service:regex:/(.*)-service/}

# Instance hostname extraction  
${instance:regex:/([^:]+):.*/}

# Environment abbreviation
${environment:regex:/(prod|production)/Production/}

# Multiple value joining
${service:pipe}  # service1|service2|service3
${service:csv}   # service1,service2,service3
${service:json}  # ["service1","service2","service3"]
```

### URL Parameter Variables
```bash
# Dashboard linking with variables
/d/dashboard-uid?var-environment=$environment&var-service=$service

# External URL generation
https://logs.company.com/search?query={environment="$environment"}

# Runbook linking
https://runbooks.company.com/services/$service/alerts
```

### Conditional Templating
```bash
# Show different panels based on environment
{{#if environment == "prod"}}
  Show production-specific panels
{{else}}
  Show development panels  
{{/if}}

# Dynamic panel titles
Error Rate - $service ($environment)

# Conditional queries
{{#if user_id}}
  {environment="$environment"} | json | user_id="$user_id"
{{else}}
  {environment="$environment"}
{{/if}}
```

## Production Variable Patterns

### Multi-Tenant Dashboard Variables
```json
{
  "variables": [
    {
      "name": "tenant",
      "query": "label_values(tenant_id)",
      "hide": 0
    },
    {
      "name": "environment", 
      "query": "label_values({tenant_id=\"$tenant\"}, environment)",
      "hide": 0
    },
    {
      "name": "service",
      "query": "label_values({tenant_id=\"$tenant\", environment=\"$environment\"}, service)",
      "hide": 0
    }
  ]
}
```

### Incident Response Variables
```json
{
  "variables": [
    {
      "name": "incident_start",
      "type": "textbox",
      "current": {"value": "2023-10-15T10:00:00Z"},
      "hide": 0
    },
    {
      "name": "incident_duration", 
      "type": "custom",
      "options": [
        {"text": "15 minutes", "value": "15m"},
        {"text": "1 hour", "value": "1h"},
        {"text": "4 hours", "value": "4h"}
      ],
      "hide": 0
    },
    {
      "name": "affected_services",
      "type": "query",
      "query": "label_values({environment=\"prod\"} |= \"ERROR\", service)",
      "multi": true,
      "hide": 0
    }
  ]
}
```

### Performance Analysis Variables
```json
{
  "variables": [
    {
      "name": "percentile",
      "type": "custom", 
      "options": [
        {"text": "50th", "value": "0.5"},
        {"text": "90th", "value": "0.9"},
        {"text": "95th", "value": "0.95"},
        {"text": "99th", "value": "0.99"}
      ],
      "current": {"value": "0.95"},
      "hide": 0
    },
    {
      "name": "threshold_ms",
      "type": "custom",
      "options": [
        {"text": "100ms", "value": "100"},
        {"text": "500ms", "value": "500"},
        {"text": "1s", "value": "1000"},
        {"text": "2s", "value": "2000"}
      ],
      "hide": 0
    }
  ]
}
```

## Variable Chaining & Dependencies

### Cascading Variable Setup
```bash
# Level 1: Environment
environment -> label_values(environment)

# Level 2: Region (depends on environment)
region -> label_values({environment="$environment"}, region)

# Level 3: Cluster (depends on environment + region)
cluster -> label_values({environment="$environment", region="$region"}, cluster)

# Level 4: Service (depends on all above)
service -> label_values({environment="$environment", region="$region", cluster="$cluster"}, service)
```

### Variable Refresh Settings
```bash
# Refresh on dashboard load (refresh: 1)
- Use for: environment, region, cluster
- Query cost: Low
- User experience: Good

# Refresh on time range change (refresh: 2)  
- Use for: dynamic service discovery
- Query cost: Medium
- User experience: Excellent

# Never refresh (refresh: 0)
- Use for: static options (log levels, percentiles)
- Query cost: None
- User experience: Fast
```

## Troubleshooting Variables

### Common Variable Issues
```bash
# Variable returns no values
1. Check Loki label existence: curl "http://loki:3100/loki/api/v1/labels"
2. Verify time range includes data
3. Test query syntax in Loki directly

# Variable refresh is slow
1. Reduce query scope with more specific labels
2. Use refresh: 0 for static variables
3. Implement variable caching

# Multi-select not working
1. Set multi: true and includeAll: true
2. Use regex format for allValue: ".*"
3. Test with |= vs =~ in LogQL
```

### Variable Debugging
```bash
# Check variable values in browser console
console.log(templateSrv.getVariables())

# Test variable interpolation
console.log(templateSrv.replace("$service"))

# Validate LogQL with variables
curl -G "http://loki:3100/loki/api/v1/query" \
  --data-urlencode 'query={environment="prod", service=~"api|web"}' \
  --data-urlencode 'time=2023-01-01T12:00:00Z'
```

## Best Practices

### Variable Organization
```bash
# Order variables logically (broadest to narrowest)
1. Environment
2. Region/Datacenter  
3. Cluster/Namespace
4. Service/Application
5. Instance/Pod
6. Specific filters (user_id, error_type)

# Group related variables
Infrastructure: environment, region, cluster
Application: service, version, instance  
Analysis: time_window, log_level, error_pattern
```

### Performance Optimization
```bash
# Efficient variable queries
label_values({environment="$environment"}, service)  # Good - filtered
label_values(service)  # Bad - unfiltered

# Use appropriate refresh settings
- Static lists: refresh: 0
- Environment-dependent: refresh: 1  
- Time-dependent: refresh: 2

# Limit multi-select options
- Max 50 services in dropdown
- Use regex to filter large label sets
- Implement search/filter in variable query
```

### Security Considerations
```bash
# Validate user input for text box variables
- Escape special characters in LogQL
- Limit query scope with label filters
- Prevent injection attacks

# Restrict variable values
- Use custom type with predefined options
- Implement regex validation
- Hide sensitive variables (hide: 2)

# Audit variable usage
- Log variable changes in dashboard
- Monitor query patterns for abuse
- Implement rate limiting on expensive variables
```