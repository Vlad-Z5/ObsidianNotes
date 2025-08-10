## Production Provisioning Runbook

### Infrastructure as Code for Grafana

#### Directory Structure
```bash
/etc/grafana/provisioning/
├── datasources/
│   ├── loki.yml
│   ├── prometheus.yml
│   └── elasticsearch.yml
├── dashboards/
│   ├── dashboard-config.yml
│   └── dashboards/
│       ├── infrastructure/
│       ├── applications/
│       └── business/
├── alerting/
│   ├── rules.yml
│   ├── contact-points.yml
│   └── policies.yml
├── plugins/
│   └── plugins.yml
└── notifiers/
    └── notification-channels.yml
```

### Data Source Provisioning

#### Loki Data Source (Production)
```yaml
# /etc/grafana/provisioning/datasources/loki.yml
apiVersion: 1
datasources:
  - name: Loki-Production
    type: loki
    access: proxy
    url: http://loki.monitoring.svc.cluster.local:3100
    uid: loki_prod_uid
    isDefault: false
    version: 1
    editable: false
    jsonData:
      maxLines: 1000
      timeout: "60s"
      derivedFields:
        - datasourceUid: "jaeger_uid"
          matcherRegex: "trace_id=(\\w+)"
          name: "TraceID"
          url: "${__value.raw}"
        - datasourceUid: "prometheus_uid"
          matcherRegex: "request_id=(\\w+)"
          name: "RequestID"
          url: "/d/request-details?var-request_id=${__value.raw}"
    secureJsonData:
      basicAuthPassword: "${LOKI_PASSWORD}"
    basicAuth: true
    basicAuthUser: "${LOKI_USER}"

  - name: Loki-Staging
    type: loki
    access: proxy
    url: http://loki-staging.monitoring.svc.cluster.local:3100
    uid: loki_staging_uid
    isDefault: false
    editable: true
    jsonData:
      maxLines: 5000
      timeout: "30s"
```

#### Prometheus Data Source
```yaml
# /etc/grafana/provisioning/datasources/prometheus.yml
apiVersion: 1
datasources:
  - name: Prometheus-Production
    type: prometheus
    access: proxy
    url: http://prometheus.monitoring.svc.cluster.local:9090
    uid: prometheus_prod_uid
    isDefault: true
    version: 1
    editable: false
    jsonData:
      httpMethod: POST
      queryTimeout: "60s"
      timeInterval: "30s"
      customQueryParameters: "max_source_resolution=5m&partial_response=true"
      exemplarTraceIdDestinations:
        - name: "trace_id"
          datasourceUid: "jaeger_uid"
          urlDisplayLabel: "View Trace"
    secureJsonData:
      httpHeaderValue1: "${PROMETHEUS_API_KEY}"
    httpHeaderName1: "X-API-Key"
```

#### Mixed Data Source Configuration
```yaml
# /etc/grafana/provisioning/datasources/mixed.yml
apiVersion: 1
datasources:
  - name: Mixed-Observability
    type: mixed
    access: proxy
    uid: mixed_observability_uid
    isDefault: false
    jsonData:
      datasources:
        - name: "Logs"
          datasourceUid: "loki_prod_uid"
        - name: "Metrics"
          datasourceUid: "prometheus_prod_uid"
        - name: "Traces"
          datasourceUid: "jaeger_uid"
```

### Dashboard Provisioning

#### Dashboard Provider Configuration
```yaml
# /etc/grafana/provisioning/dashboards/dashboard-config.yml
apiVersion: 1
providers:
  - name: 'infrastructure'
    orgId: 1
    folder: 'Infrastructure'
    type: file
    disableDeletion: true
    updateIntervalSeconds: 30
    allowUiUpdates: false
    options:
      path: /etc/grafana/provisioning/dashboards/infrastructure

  - name: 'applications'
    orgId: 1
    folder: 'Applications'
    type: file
    disableDeletion: false
    updateIntervalSeconds: 60
    allowUiUpdates: true
    options:
      path: /etc/grafana/provisioning/dashboards/applications

  - name: 'sla-monitoring'
    orgId: 1
    folder: 'SLA & Business'
    type: file
    disableDeletion: true
    updateIntervalSeconds: 300
    allowUiUpdates: false
    options:
      path: /etc/grafana/provisioning/dashboards/business
```

#### Dashboard JSON Template
```json
{
  "__inputs": [
    {
      "name": "DS_LOKI",
      "label": "Loki",
      "description": "",
      "type": "datasource",
      "pluginId": "loki",
      "pluginName": "Loki"
    }
  ],
  "__elements": {},
  "__requires": [
    {
      "type": "grafana",
      "id": "grafana",
      "name": "Grafana",
      "version": "10.0.0"
    },
    {
      "type": "datasource",
      "id": "loki",
      "name": "Loki",
      "version": "1.0.0"
    }
  ],
  "dashboard": {
    "id": null,
    "uid": "infrastructure-overview",
    "title": "Infrastructure Overview",
    "description": "Production infrastructure monitoring dashboard",
    "tags": ["infrastructure", "production", "monitoring"],
    "timezone": "browser",
    "refresh": "30s",
    "schemaVersion": 39,
    "version": 1,
    "time": {
      "from": "now-1h",
      "to": "now"
    },
    "timepicker": {
      "refresh_intervals": ["5s", "10s", "30s", "1m", "5m", "15m", "30m", "1h", "2h", "1d"],
      "time_options": ["5m", "15m", "1h", "6h", "12h", "24h", "2d", "7d", "30d"]
    },
    "templating": {
      "list": [
        {
          "name": "environment",
          "type": "query",
          "datasource": "${DS_LOKI}",
          "query": "label_values(environment)",
          "refresh": 1,
          "includeAll": false,
          "multi": false,
          "current": {
            "value": "prod",
            "text": "Production"
          }
        }
      ]
    },
    "panels": []
  },
  "overwrite": true
}
```

### Alert Provisioning

#### Alert Rules Configuration
```yaml
# /etc/grafana/provisioning/alerting/rules.yml
apiVersion: 1
groups:
  - name: "production-critical"
    orgId: 1
    interval: "1m"
    rules:
      - uid: "high-error-rate"
        title: "High Error Rate - Production"
        condition: "B"
        data:
          - refId: "A"
            queryType: ""
            relativeTimeRange:
              from: 300
              to: 0
            datasourceUid: "loki_prod_uid"
            model:
              expr: 'sum by (service) (rate({environment="prod"} |= "ERROR" [5m]))'
              intervalMs: 1000
              maxDataPoints: 43200
          - refId: "B"
            queryType: ""
            relativeTimeRange:
              from: 0
              to: 0
            datasourceUid: "__expr__"
            model:
              expression: "A > 5"
              intervalMs: 1000
              maxDataPoints: 43200
              type: "threshold"
        intervalSeconds: 60
        maxDataPoints: 43200
        for: "2m"
        noDataState: "NoData"
        execErrState: "Alerting"
        annotations:
          description: "Error rate for service {{$labels.service}} is {{$value}} errors/sec"
          runbook_url: "https://runbooks.company.com/high-error-rate"
          summary: "High error rate detected"
        labels:
          severity: "critical"
          team: "platform"
          environment: "production"

  - name: "application-warnings"
    orgId: 1
    interval: "5m"
    rules:
      - uid: "slow-response-time"
        title: "Slow Response Time"
        condition: "B"
        data:
          - refId: "A"
            datasourceUid: "loki_prod_uid"
            model:
              expr: 'avg_over_time({service="api", environment="prod"} | json | __error__="" | unwrap duration [5m]) / 1000'
          - refId: "B"
            datasourceUid: "__expr__"
            model:
              expression: "A > 2"
              type: "threshold"
        for: "5m"
        annotations:
          description: "API response time is {{$value}}s (threshold: 2s)"
          summary: "API performance degradation"
        labels:
          severity: "warning"
          team: "backend"
```

#### Contact Points Configuration
```yaml
# /etc/grafana/provisioning/alerting/contact-points.yml
apiVersion: 1
contactPoints:
  - name: "critical-alerts"
    receivers:
      - uid: "slack-critical"
        type: "slack"
        settings:
          url: "${SLACK_WEBHOOK_CRITICAL}"
          channel: "#alerts-critical"
          username: "Grafana Alert"
          title: "🚨 CRITICAL: {{.GroupLabels.service}}"
          text: |
            {{range .Alerts}}
            *Alert:* {{.Annotations.summary}}
            *Service:* {{.Labels.service}}
            *Environment:* {{.Labels.environment}}
            *Description:* {{.Annotations.description}}
            *Runbook:* {{.Annotations.runbook_url}}
            *Dashboard:* http://grafana.company.com/d/{{.Labels.dashboard_uid}}
            {{end}}
        disableResolveMessage: false
      - uid: "pagerduty-critical"
        type: "pagerduty"
        settings:
          integrationKey: "${PAGERDUTY_INTEGRATION_KEY}"
          severity: "{{ .CommonLabels.severity }}"
          component: "{{ .CommonLabels.service }}"
          summary: "{{ range .Alerts }}{{ .Annotations.summary }}{{ end }}"
          source: "Grafana"

  - name: "warning-alerts"
    receivers:
      - uid: "slack-warnings"
        type: "slack"
        settings:
          url: "${SLACK_WEBHOOK_WARNINGS}"
          channel: "#alerts-warnings"
          title: "⚠️ WARNING: {{.GroupLabels.service}}"
          text: |
            *Service:* {{.GroupLabels.service}}
            *Description:* {{ range .Alerts }}{{ .Annotations.description }}{{ end }}

  - name: "email-platform-team"
    receivers:
      - uid: "email-platform"
        type: "email"
        settings:
          addresses: "${PLATFORM_TEAM_EMAIL}"
          subject: "[{{.Status | upper}}] {{.GroupLabels.service}} Alert"
          message: |
            Alert Details:
            {{ range .Alerts }}
            Service: {{ .Labels.service }}
            Environment: {{ .Labels.environment }}
            Severity: {{ .Labels.severity }}
            Description: {{ .Annotations.description }}
            Time: {{ .StartsAt.Format "2006-01-02 15:04:05" }}
            {{ end }}
```

#### Notification Policies
```yaml
# /etc/grafana/provisioning/alerting/policies.yml
apiVersion: 1
policies:
  - receiver: "critical-alerts"
    group_by: ["service", "environment"]
    group_wait: "30s"
    group_interval: "5m"
    repeat_interval: "12h"
    matchers:
      - ["severity", "=", "critical"]
      - ["environment", "=", "production"]
    
  - receiver: "warning-alerts"
    group_by: ["service"]
    group_wait: "2m"
    group_interval: "10m"
    repeat_interval: "24h"
    matchers:
      - ["severity", "=", "warning"]
    
  - receiver: "email-platform-team"
    group_by: ["team"]
    group_wait: "5m"
    group_interval: "30m"
    repeat_interval: "7d"
    matchers:
      - ["team", "=", "platform"]
```

### Plugin Provisioning

#### Essential Plugins Configuration
```yaml
# /etc/grafana/provisioning/plugins/plugins.yml
apiVersion: 1
apps:
  - type: "grafana-piechart-panel"
    name: "piechart"
    disabled: false
  - type: "grafana-worldmap-panel"
    name: "worldmap"
    disabled: false
  - type: "grafana-clock-panel"
    name: "clock"
    disabled: false

datasources:
  - type: "grafana-elasticsearch-datasource"
    name: "elasticsearch"
    disabled: false
  - type: "grafana-influxdb-datasource"
    name: "influxdb"
    disabled: false
```

### Organization & User Provisioning

#### Organization Setup
```yaml
# /etc/grafana/provisioning/organizations/orgs.yml
apiVersion: 1
organizations:
  - name: "Production"
    orgId: 1
  - name: "Staging"
    orgId: 2
  - name: "Development"
    orgId: 3
```

#### User and Team Configuration
```yaml
# /etc/grafana/provisioning/users/users.yml
apiVersion: 1
users:
  - name: "SRE Team"
    email: "sre@company.com"
    login: "sre-team"
    orgId: 1
    role: "Admin"
  - name: "Development Team"
    email: "dev@company.com"
    login: "dev-team"
    orgId: 1
    role: "Editor"
  - name: "Business Team"
    email: "business@company.com"
    login: "business-team"
    orgId: 1
    role: "Viewer"
```

### Environment-Specific Provisioning

#### Production Environment
```yaml
# /etc/grafana/provisioning/environments/production.yml
apiVersion: 1
environment: production
datasources:
  - name: Loki-Production
    url: http://loki-prod.monitoring.svc.cluster.local:3100
    timeout: 60s
    readonly: true
  - name: Prometheus-Production
    url: http://prometheus-prod.monitoring.svc.cluster.local:9090
    timeout: 60s
    readonly: true
alerting:
  evaluation_interval: 30s
  notification_timeout: 30s
  max_annotation_age: 7d
```

#### Staging Environment
```yaml
# /etc/grafana/provisioning/environments/staging.yml
apiVersion: 1
environment: staging
datasources:
  - name: Loki-Staging
    url: http://loki-staging.monitoring.svc.cluster.local:3100
    timeout: 30s
    readonly: false
  - name: Prometheus-Staging
    url: http://prometheus-staging.monitoring.svc.cluster.local:9090
    timeout: 30s
    readonly: false
alerting:
  evaluation_interval: 60s
  notification_timeout: 10s
```

### Deployment Automation

#### Docker Compose with Provisioning
```yaml
# docker-compose.yml
version: '3.8'
services:
  grafana:
    image: grafana/grafana:latest
    container_name: grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${ADMIN_PASSWORD}
      - GF_USERS_ALLOW_SIGN_UP=false
      - GF_PROVISIONING_PATH=/etc/grafana/provisioning
    volumes:
      - grafana-data:/var/lib/grafana
      - ./provisioning:/etc/grafana/provisioning:ro
    restart: unless-stopped
    networks:
      - monitoring

volumes:
  grafana-data:

networks:
  monitoring:
    external: true
```

#### Kubernetes Deployment
```yaml
# grafana-deployment.yml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: grafana
  namespace: monitoring
spec:
  replicas: 1
  selector:
    matchLabels:
      app: grafana
  template:
    metadata:
      labels:
        app: grafana
    spec:
      containers:
      - name: grafana
        image: grafana/grafana:latest
        ports:
        - containerPort: 3000
        env:
        - name: GF_SECURITY_ADMIN_PASSWORD
          valueFrom:
            secretKeyRef:
              name: grafana-secrets
              key: admin-password
        volumeMounts:
        - name: grafana-provisioning
          mountPath: /etc/grafana/provisioning
          readOnly: true
        - name: grafana-storage
          mountPath: /var/lib/grafana
      volumes:
      - name: grafana-provisioning
        configMap:
          name: grafana-provisioning
      - name: grafana-storage
        persistentVolumeClaim:
          claimName: grafana-pvc

---
apiVersion: v1
kind: ConfigMap
metadata:
  name: grafana-provisioning
  namespace: monitoring
data:
  datasources.yml: |
    apiVersion: 1
    datasources:
    - name: Loki
      type: loki
      url: http://loki:3100
      access: proxy
  dashboards.yml: |
    apiVersion: 1
    providers:
    - name: 'default'
      folder: ''
      type: file
      path: /etc/grafana/provisioning/dashboards
```

### Provisioning Best Practices

#### Version Control Integration
```bash
# Git repository structure
grafana-provisioning/
├── environments/
│   ├── production/
│   ├── staging/
│   └── development/
├── dashboards/
│   ├── infrastructure/
│   ├── applications/
│   └── business/
├── alerts/
│   ├── critical/
│   ├── warnings/
│   └── info/
└── scripts/
    ├── deploy.sh
    ├── validate.sh
    └── backup.sh
```

#### Deployment Pipeline
```bash
#!/bin/bash
# deploy.sh - Automated provisioning deployment

set -euo pipefail

ENVIRONMENT=${1:-production}
GRAFANA_URL="http://grafana.${ENVIRONMENT}.company.com"
API_KEY="${GRAFANA_API_KEY}"

echo "Deploying Grafana provisioning to ${ENVIRONMENT}..."

# Validate configuration files
echo "Validating configurations..."
for file in provisioning/**/*.yml; do
  yq eval '.' "$file" > /dev/null || {
    echo "Error: Invalid YAML in $file"
    exit 1
  }
done

# Deploy data sources
echo "Provisioning data sources..."
curl -X POST \
  -H "Authorization: Bearer ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d @provisioning/datasources/${ENVIRONMENT}.yml \
  "${GRAFANA_URL}/api/admin/provisioning/datasources/reload"

# Deploy dashboards
echo "Provisioning dashboards..."
for dashboard in provisioning/dashboards/${ENVIRONMENT}/*.json; do
  curl -X POST \
    -H "Authorization: Bearer ${API_KEY}" \
    -H "Content-Type: application/json" \
    -d @"$dashboard" \
    "${GRAFANA_URL}/api/dashboards/db"
done

# Deploy alerts
echo "Provisioning alert rules..."
curl -X POST \
  -H "Authorization: Bearer ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d @provisioning/alerting/${ENVIRONMENT}/rules.yml \
  "${GRAFANA_URL}/api/admin/provisioning/alerting/reload"

echo "Deployment completed successfully!"
```

#### Configuration Validation
```bash
#!/bin/bash
# validate.sh - Configuration validation script

echo "Validating Grafana provisioning configurations..."

# Validate YAML syntax
find provisioning -name "*.yml" -o -name "*.yaml" | while read -r file; do
  if ! yq eval '.' "$file" > /dev/null 2>&1; then
    echo "ERROR: Invalid YAML syntax in $file"
    exit 1
  fi
  echo "✓ $file"
done

# Validate JSON syntax
find provisioning -name "*.json" | while read -r file; do
  if ! jq '.' "$file" > /dev/null 2>&1; then
    echo "ERROR: Invalid JSON syntax in $file"
    exit 1
  fi
  echo "✓ $file"
done

# Check required fields in dashboard JSON
find provisioning/dashboards -name "*.json" | while read -r file; do
  if ! jq -e '.dashboard.title' "$file" > /dev/null; then
    echo "ERROR: Missing dashboard title in $file"
    exit 1
  fi
  if ! jq -e '.dashboard.uid' "$file" > /dev/null; then
    echo "ERROR: Missing dashboard UID in $file"
    exit 1
  fi
  echo "✓ Dashboard $file has required fields"
done

echo "All configurations validated successfully!"
```

### Troubleshooting Provisioning

#### Common Issues
```bash
# Issue: Data source not loading
# Check: /var/log/grafana/grafana.log for errors
tail -f /var/log/grafana/grafana.log | grep -i "provisioning\|datasource"

# Issue: Dashboard not appearing
# Verify: File permissions and JSON syntax
ls -la /etc/grafana/provisioning/dashboards/
jq '.' dashboard.json

# Issue: Alerts not firing
# Check: Alert rule validation and data source connectivity
curl -H "Authorization: Bearer $API_KEY" \
  "http://grafana:3000/api/alerts/rules" | jq '.[] | select(.state == "NoData")'

# Issue: Variables not working
# Validate: Variable queries against data source
curl -G "http://loki:3100/loki/api/v1/labels"
```

#### Monitoring Provisioning Health
```bash
# Check provisioning status
curl -H "Authorization: Bearer $API_KEY" \
  "http://grafana:3000/api/admin/provisioning/dashboards/reload"

# Monitor configuration reload
tail -f /var/log/grafana/grafana.log | grep "provisioning.*reload"

# Validate data source connectivity
curl -H "Authorization: Bearer $API_KEY" \
  "http://grafana:3000/api/datasources" | \
  jq '.[] | {name: .name, type: .type, url: .url}'
```