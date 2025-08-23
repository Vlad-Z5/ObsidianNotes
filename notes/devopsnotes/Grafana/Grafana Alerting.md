## Production Alerting Runbook

### Critical Loki-Based Alerts

#### 1. High Error Rate Alert
```json
{
  "alert": {
    "uid": "error-rate-high",
    "title": "High Error Rate Detected",
    "condition": "B",
    "data": [
      {
        "refId": "A",
        "queryType": "",
        "relativeTimeRange": {
          "from": 300,
          "to": 0
        },
        "datasourceUid": "loki_uid",
        "model": {
          "expr": "sum by (service) (rate({environment=\"prod\"} |= \"ERROR\" [5m]))",
          "intervalMs": 1000,
          "maxDataPoints": 43200
        }
      },
      {
        "refId": "B",
        "queryType": "",
        "relativeTimeRange": {
          "from": 0,
          "to": 0
        },
        "datasourceUid": "__expr__",
        "model": {
          "conditions": [
            {
              "evaluator": {
                "params": [5],
                "type": "gt"
              },
              "operator": {
                "type": "and"
              },
              "query": {
                "params": ["A"]
              },
              "reducer": {
                "params": [],
                "type": "last"
              },
              "type": "query"
            }
          ],
          "expression": "A > 5",
          "intervalMs": 1000,
          "maxDataPoints": 43200,
          "reducer": "last",
          "type": "threshold"
        }
      }
    ],
    "intervalSeconds": 60,
    "maxDataPoints": 43200,
    "noDataState": "NoData",
    "execErrState": "Alerting",
    "for": "2m",
    "annotations": {
      "description": "Service {{$labels.service}} error rate is {{$value}} errors/sec",
      "runbook_url": "https://runbooks.company.com/high-error-rate",
      "summary": "Error rate above threshold"
    },
    "labels": {
      "severity": "critical",
      "team": "platform"
    }
  }
}
```

#### 2. Service Down Alert (Log-Based)
```json
{
  "alert": {
    "uid": "service-down",
    "title": "Service Unavailable",
    "condition": "B", 
    "data": [
      {
        "refId": "A",
        "datasourceUid": "loki_uid",
        "model": {
          "expr": "sum by (service) (count_over_time({environment=\"prod\", job=\"healthcheck\"} |= \"healthy\" [5m]))",
          "intervalMs": 1000
        }
      },
      {
        "refId": "B",
        "datasourceUid": "__expr__",
        "model": {
          "expression": "A < 1",
          "type": "threshold"
        }
      }
    ],
    "intervalSeconds": 30,
    "for": "1m",
    "annotations": {
      "description": "Service {{$labels.service}} has not reported healthy status in 5 minutes",
      "runbook_url": "https://runbooks.company.com/service-down",
      "summary": "Service down detected"
    },
    "labels": {
      "severity": "critical",
      "team": "sre"
    }
  }
}
```

#### 3. Application Crash Detection
```json
{
  "alert": {
    "uid": "app-crash",
    "title": "Application Crash Detected",
    "condition": "B",
    "data": [
      {
        "refId": "A",
        "datasourceUid": "loki_uid",
        "model": {
          "expr": "sum by (service, pod) (count_over_time({environment=\"prod\"} |~ \"crashed|panic|fatal|segmentation fault\" [5m]))",
          "intervalMs": 1000
        }
      },
      {
        "refId": "B",
        "datasourceUid": "__expr__",
        "model": {
          "expression": "A > 0",
          "type": "threshold"
        }
      }
    ],
    "intervalSeconds": 60,
    "for": "0m",
    "annotations": {
      "description": "Application crash detected in {{$labels.service}} pod {{$labels.pod}}",
      "runbook_url": "https://runbooks.company.com/app-crash",
      "summary": "Application crash event"
    },
    "labels": {
      "severity": "critical",
      "team": "platform"
    }
  }
}
```

#### 4. Database Connection Issues
```json
{
  "alert": {
    "uid": "db-connection-issues",
    "title": "Database Connection Problems",
    "condition": "B",
    "data": [
      {
        "refId": "A", 
        "datasourceUid": "loki_uid",
        "model": {
          "expr": "sum by (service) (rate({environment=\"prod\"} |~ \"connection timeout|connection refused|connection pool exhausted|database.*error\" [5m]))",
          "intervalMs": 1000
        }
      },
      {
        "refId": "B",
        "datasourceUid": "__expr__",
        "model": {
          "expression": "A > 1",
          "type": "threshold"
        }
      }
    ],
    "intervalSeconds": 60,
    "for": "2m",
    "annotations": {
      "description": "Database connection issues detected for service {{$labels.service}} - {{$value}} errors/sec",
      "runbook_url": "https://runbooks.company.com/database-issues",
      "summary": "Database connectivity problems"
    },
    "labels": {
      "severity": "warning",
      "team": "platform"
    }
  }
}
```

#### 5. Memory Leak Detection
```json
{
  "alert": {
    "uid": "memory-leak",
    "title": "Potential Memory Leak",
    "condition": "B",
    "data": [
      {
        "refId": "A",
        "datasourceUid": "loki_uid", 
        "model": {
          "expr": "sum by (service, pod) (count_over_time({environment=\"prod\"} |~ \"OutOfMemoryError|memory.*exhausted|GC.*overhead\" [10m]))",
          "intervalMs": 1000
        }
      },
      {
        "refId": "B",
        "datasourceUid": "__expr__",
        "model": {
          "expression": "A > 2",
          "type": "threshold"
        }
      }
    ],
    "intervalSeconds": 300,
    "for": "5m",
    "annotations": {
      "description": "Memory issues detected in {{$labels.service}} pod {{$labels.pod}}",
      "runbook_url": "https://runbooks.company.com/memory-leak",
      "summary": "Potential memory leak detected"
    },
    "labels": {
      "severity": "warning",
      "team": "platform"
    }
  }
}
```

### Advanced Loki Alert Patterns

#### Log Volume Anomaly Detection
```json
{
  "alert": {
    "uid": "log-volume-anomaly",
    "title": "Abnormal Log Volume",
    "condition": "C",
    "data": [
      {
        "refId": "A",
        "datasourceUid": "loki_uid",
        "model": {
          "expr": "sum by (service) (rate({environment=\"prod\"} [5m]))",
          "intervalMs": 1000
        }
      },
      {
        "refId": "B",
        "datasourceUid": "loki_uid", 
        "model": {
          "expr": "sum by (service) (rate({environment=\"prod\"} [5m] offset 24h))",
          "intervalMs": 1000
        }
      },
      {
        "refId": "C",
        "datasourceUid": "__expr__",
        "model": {
          "expression": "(A / B) > 3 OR (B / A) > 3",
          "type": "math"
        }
      }
    ],
    "intervalSeconds": 300,
    "for": "5m",
    "annotations": {
      "description": "Log volume for {{$labels.service}} is {{$value}}x different from 24h ago",
      "summary": "Unusual log volume pattern detected"
    },
    "labels": {
      "severity": "info",
      "team": "platform"
    }
  }
}
```

#### User Impact Alert
```json
{
  "alert": {
    "uid": "user-impact",
    "title": "High User Error Impact",
    "condition": "B",
    "data": [
      {
        "refId": "A",
        "datasourceUid": "loki_uid",
        "model": {
          "expr": "count by (service) (count by (user_id, service) ({environment=\"prod\"} |= \"ERROR\" | json | user_id!=\"\" [5m]))",
          "intervalMs": 1000
        }
      },
      {
        "refId": "B",
        "datasourceUid": "__expr__",
        "model": {
          "expression": "A > 10",
          "type": "threshold"
        }
      }
    ],
    "intervalSeconds": 180,
    "for": "3m",
    "annotations": {
      "description": "{{$value}} users affected by errors in {{$labels.service}}",
      "runbook_url": "https://runbooks.company.com/user-impact",
      "summary": "Multiple users experiencing errors"
    },
    "labels": {
      "severity": "critical",
      "team": "product"
    }
  }
}
```

## Alert Rule Management

### Alert Rule Groups
```yaml
# /etc/grafana/provisioning/alerting/rules.yaml
apiVersion: 1
groups:
  - name: "critical-errors"
    interval: 1m
    rules:
      - uid: "error-rate-high"
        title: "High Error Rate"
        condition: "B"
        data:
          - refId: "A"
            queryType: ""
            datasourceUid: "loki_uid"
            model:
              expr: 'sum by (service) (rate({environment="prod"} |= "ERROR" [5m]))'
          - refId: "B"
            queryType: ""
            datasourceUid: "__expr__"
            model:
              expression: "A > 5"
              type: "threshold"
        intervalSeconds: 60
        for: "2m"
        annotations:
          description: "Service {{$labels.service}} error rate: {{$value}}/sec"
          runbook: "https://runbooks.company.com/high-error-rate"
        labels:
          severity: "critical"
          team: "platform"

  - name: "performance-degradation"
    interval: 2m
    rules:
      - uid: "slow-response-time"
        title: "Slow Response Time"
        condition: "B"
        data:
          - refId: "A"
            datasourceUid: "loki_uid"
            model:
              expr: 'avg_over_time({environment="prod", service="api"} | json | __error__="" | unwrap duration [5m]) / 1000'
          - refId: "B"
            datasourceUid: "__expr__"
            model:
              expression: "A > 2"
              type: "threshold"
        for: "5m"
        annotations:
          description: "API response time: {{$value}}s (threshold: 2s)"
        labels:
          severity: "warning"
```

### Notification Channels

#### Slack Integration
```json
{
  "name": "slack-alerts",
  "type": "slack",
  "settings": {
    "url": "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK",
    "channel": "#alerts-critical",
    "username": "Grafana",
    "title": "{{ range .Alerts }}{{ .Annotations.summary }}{{ end }}",
    "text": "{{ range .Alerts }}*Service:* {{ .Labels.service }}\n*Severity:* {{ .Labels.severity }}\n*Description:* {{ .Annotations.description }}\n*Runbook:* {{ .Annotations.runbook_url }}{{ end }}"
  }
}
```

#### PagerDuty Integration
```json
{
  "name": "pagerduty-critical",
  "type": "pagerduty",
  "settings": {
    "integrationKey": "YOUR_PAGERDUTY_INTEGRATION_KEY",
    "severity": "{{ .CommonLabels.severity }}",
    "component": "{{ .CommonLabels.service }}",
    "summary": "{{ range .Alerts }}{{ .Annotations.summary }}{{ end }}",
    "source": "Grafana"
  }
}
```

#### Email Notifications
```json
{
  "name": "email-platform-team",
  "type": "email", 
  "settings": {
    "addresses": "platform-team@company.com;sre-team@company.com",
    "subject": "[{{ .Status | toUpper }}] {{ .GroupLabels.service }} - {{ range .Alerts }}{{ .Annotations.summary }}{{ end }}",
    "message": "{{ range .Alerts }}Service: {{ .Labels.service }}\nSeverity: {{ .Labels.severity }}\nDescription: {{ .Annotations.description }}\nRunbook: {{ .Annotations.runbook_url }}\nTime: {{ .StartsAt.Format \"2006-01-02 15:04:05\" }}{{ end }}"
  }
}
```

### Contact Points & Routing

#### Contact Point Configuration
```yaml
# /etc/grafana/provisioning/alerting/contact-points.yaml
apiVersion: 1
contactPoints:
  - name: "critical-alerts"
    receivers:
      - uid: "slack-critical"
        type: "slack"
        settings:
          url: "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK"
          channel: "#alerts-critical"
          title: "🚨 CRITICAL: {{.GroupLabels.service}}"
          text: |
            {{range .Alerts}}
            *Alert:* {{.Annotations.summary}}
            *Service:* {{.Labels.service}}
            *Description:* {{.Annotations.description}}
            *Runbook:* {{.Annotations.runbook_url}}
            {{end}}
      - uid: "pagerduty-critical"
        type: "pagerduty"
        settings:
          integrationKey: "YOUR_INTEGRATION_KEY"

  - name: "warning-alerts"
    receivers:
      - uid: "slack-warnings"
        type: "slack" 
        settings:
          url: "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK"
          channel: "#alerts-warnings"
          title: "⚠️ WARNING: {{.GroupLabels.service}}"
```

#### Notification Policies
```yaml
# /etc/grafana/provisioning/alerting/policies.yaml
apiVersion: 1
policies:
  - receiver: "critical-alerts"
    group_by: ["service", "severity"]
    group_wait: "30s"
    group_interval: "5m"
    repeat_interval: "12h"
    matchers:
      - ["severity", "=", "critical"]
    
  - receiver: "warning-alerts"
    group_by: ["service"]
    group_wait: "2m"
    group_interval: "10m" 
    repeat_interval: "24h"
    matchers:
      - ["severity", "=", "warning"]
    
  - receiver: "info-alerts"
    group_by: ["team"]
    group_wait: "5m"
    group_interval: "30m"
    repeat_interval: "7d"
    matchers:
      - ["severity", "=", "info"]
```

## Alert Testing & Validation

### Manual Alert Testing
```bash
# Test alert query directly in Loki
curl -G "http://loki:3100/loki/api/v1/query" \
  --data-urlencode 'query=sum by (service) (rate({environment="prod"} |= "ERROR" [5m]))' \
  --data-urlencode 'time=2023-01-01T12:00:00Z'

# Simulate alert condition
# Inject ERROR logs to trigger alert
for i in {1..10}; do
  echo "$(date) ERROR: Test alert condition" >> /var/log/app.log
  sleep 1
done

# Verify alert state via API
curl -H "Authorization: Bearer $GRAFANA_TOKEN" \
  "http://grafana:3000/api/alerts"
```

### Alert Validation Checklist
```bash
# 1. Query validation
- Test LogQL query returns expected results
- Verify time range and aggregation period
- Check label filters work correctly

# 2. Threshold validation  
- Confirm threshold triggers at expected values
- Test edge cases (exactly at threshold)
- Verify mathematical expressions work

# 3. Timing validation
- Test evaluation interval (intervalSeconds)
- Verify "for" duration works as expected
- Check alert resolution timing

# 4. Notification validation
- Test all contact points receive alerts
- Verify message formatting and content
- Check routing rules work correctly
```

## Runbook Integration

### Alert Annotations Best Practices
```json
{
  "annotations": {
    "summary": "Brief description for notification",
    "description": "Detailed description with context and values",
    "runbook_url": "Direct link to troubleshooting steps",
    "dashboard_url": "Link to relevant dashboard",
    "query_url": "Direct link to Loki query",
    "impact": "Customer-facing impact description",
    "action_required": "Immediate actions needed"
  }
}
```

### Dynamic Runbook URLs
```bash
# Service-specific runbooks
runbook_url: "https://runbooks.company.com/services/{{$labels.service}}/alerts"

# Error-specific runbooks  
runbook_url: "https://runbooks.company.com/errors/{{$labels.error_type}}"

# Environment-specific procedures
runbook_url: "https://runbooks.company.com/{{$labels.environment}}/incident-response"
```

## Alert Maintenance

### Alert Lifecycle Management
```bash
# 1. Alert Creation
- Define clear success/failure criteria
- Set appropriate thresholds based on SLO
- Include comprehensive runbook links
- Test thoroughly before deployment

# 2. Alert Tuning
- Monitor false positive rate
- Adjust thresholds based on historical data
- Refine query logic to reduce noise
- Update notification frequency

# 3. Alert Retirement
- Archive alerts for deprecated services
- Update queries for service changes
- Maintain alert documentation
- Clean up unused notification channels
```

### Performance Monitoring
```bash
# Monitor alert evaluation performance
curl -H "Authorization: Bearer $GRAFANA_TOKEN" \
  "http://grafana:3000/api/alerts/rules" | \
  jq '.[] | select(.evalDuration > "5s")'

# Check Loki query performance for alerts
logcli query 'sum by (service) (rate({environment="prod"} |= "ERROR" [5m]))' \
  --stats --limit=1

# Alert rule resource usage
kubectl top pods -l app=grafana -n monitoring
```

## Troubleshooting Alerts

### Common Alert Issues
```bash
# Alert not firing when expected
1. Check LogQL query syntax and results
2. Verify data source connectivity
3. Confirm threshold values and operators
4. Check evaluation interval and "for" duration

# False positive alerts
1. Review threshold appropriateness
2. Add more specific label filters
3. Increase evaluation period ("for")
4. Use rate() vs count_over_time() appropriately

# Missing notifications
1. Test contact point configuration
2. Check notification policy routing
3. Verify webhook endpoints are accessible
4. Review Grafana logs for delivery errors
```

### Alert Debugging Commands
```bash
# Check alert rule status
curl -H "Authorization: Bearer $TOKEN" \
  "http://grafana:3000/api/alerts/rules" | \
  jq '.[] | {uid, title, state, health}'

# View alert evaluation history
curl -H "Authorization: Bearer $TOKEN" \
  "http://grafana:3000/api/alerts/history" | \
  jq '.[] | select(.alertRuleUID == "error-rate-high")'

# Test notification delivery
curl -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"receivers":["critical-alerts"],"annotations":{"summary":"Test alert"}}' \
  "http://grafana:3000/api/alerts/test"
```