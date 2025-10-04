### Prometheus Data Source

```yaml
# Via UI: Configuration > Data Sources > Add data source > Prometheus
URL: http://prometheus:9090
Access: Server (default)
Basic Auth: false
Skip TLS Verify: false

# Custom HTTP Headers
X-Custom-Header: value

# Query timeout: 60s
# Default editor: Code/Builder
```

### Advanced Prometheus Configuration

```json
{
  "name": "Prometheus-Production",
  "type": "prometheus", 
  "url": "https://prometheus.example.com",
  "access": "proxy",
  "basicAuth": true,
  "basicAuthUser": "admin",
  "secureJsonData": {
    "basicAuthPassword": "password"
  },
  "jsonData": {
    "httpMethod": "POST",
    "queryTimeout": "60s",
    "timeInterval": "30s",
    "customQueryParameters": "max_source_resolution=5m&partial_response=true",
    "exemplarTraceIdDestinations": [
      {
        "name": "trace_id",
        "datasourceUid": "jaeger_uid"
      }
    ]
  }
}
```

### InfluxDB Data Source

```json
{
  "name": "InfluxDB",
  "type": "influxdb",
  "url": "http://influxdb:8086",
  "database": "telegraf",
  "user": "admin",
  "secureJsonData": {
    "password": "password"
  },
  "jsonData": {
    "timeInterval": "10s",
    "httpMode": "GET",
    "version": "InfluxQL"
  }
}
```

### MySQL Data Source

```json
{
  "name": "MySQL-Production",
  "type": "mysql",
  "url": "mysql.example.com:3306",
  "database": "grafana",
  "user": "grafana_ro",
  "secureJsonData": {
    "password": "password"
  },
  "jsonData": {
    "maxOpenConns": 100,
    "maxIdleConns": 100,
    "connMaxLifetime": 14400
  }
}
```

### Loki Data Source

```json
{
  "name": "Loki",
  "type": "loki",
  "url": "http://loki:3100",
  "jsonData": {
    "timeout": "60s",
    "maxLines": 1000,
    "derivedFields": [
      {
        "matcherRegex": "trace_id=(\\w+)",
        "name": "TraceID",
        "url": "${__value.raw}",
        "datasourceUid": "jaeger_uid"
      }
    ]
  }
}
```

## Dashboard Creation

### Dashboard JSON Structure

```json
{
  "dashboard": {
    "id": null,
    "title": "System Overview",
    "description": "System monitoring dashboard",
    "tags": ["system", "monitoring"],
    "timezone": "browser",
    "refresh": "30s",
    "time": {
      "from": "now-1h",
      "to": "now"
    },
    "timepicker": {
      "refresh_intervals": ["5s", "10s", "30s", "1m", "5m", "15m", "30m", "1h"],
      "time_options": ["5m", "15m", "1h", "6h", "12h", "24h", "2d", "7d", "30d"]
    },
    "templating": {
      "list": []
    },
    "annotations": {
      "list": []
    },
    "panels": []
  },
  "overwrite": true
}
```

### Panel Configuration

```json
{
  "id": 1,
  "title": "CPU Usage",
  "type": "stat",
  "targets": [
    {
      "expr": "100 - (avg by (instance) (irate(node_cpu_seconds_total{mode=\"idle\"}[5m])) * 100)",
      "refId": "A",
      "legendFormat": "{{instance}}"
    }
  ],
  "gridPos": {
    "h": 8,
    "w": 12,
    "x": 0,
    "y": 0
  },
  "fieldConfig": {
    "defaults": {
      "unit": "percent",
      "thresholds": {
        "mode": "absolute",
        "steps": [
          {"color": "green", "value": null},
          {"color": "yellow", "value": 70},
          {"color": "red", "value": 90}
        ]
      }
    }
  }
}
```

### Thanos Data Source

```json
{
  "name": "Thanos",
  "type": "prometheus",
  "url": "http://thanos-query:9090",
  "access": "proxy",
  "jsonData": {
    "httpMethod": "POST",
    "queryTimeout": "300s",
    "timeInterval": "30s",
    "customQueryParameters": "partial_response=true",
    "prometheusType": "Thanos",
    "prometheusVersion": "2.45.0"
  }
}
```

### Elasticsearch Data Source

```json
{
  "name": "Elasticsearch",
  "type": "elasticsearch",
  "url": "http://elasticsearch:9200",
  "database": "[logs-]YYYY.MM.DD",
  "jsonData": {
    "esVersion": "8.0.0",
    "timeField": "@timestamp",
    "interval": "Daily",
    "logLevelField": "level",
    "logMessageField": "message"
  }
}
```

### Jaeger Data Source

```json
{
  "name": "Jaeger",
  "type": "jaeger",
  "url": "http://jaeger-query:16686",
  "access": "proxy",
  "jsonData": {
    "tracesToLogs": {
      "datasourceUid": "loki_uid",
      "tags": ["job", "instance", "pod"],
      "mappedTags": [{"key": "service.name", "value": "service"}],
      "mapTagNamesEnabled": true,
      "spanStartTimeShift": "1h",
      "spanEndTimeShift": "1h",
      "filterByTraceID": true,
      "filterBySpanID": false
    }
  }
}
```

### Tempo Data Source

```json
{
  "name": "Tempo",
  "type": "tempo",
  "url": "http://tempo:3200",
  "jsonData": {
    "tracesToLogs": {
      "datasourceUid": "loki_uid",
      "tags": ["job", "instance"],
      "mappedTags": [{"key": "service.name", "value": "service"}],
      "mapTagNamesEnabled": true,
      "spanStartTimeShift": "1h",
      "spanEndTimeShift": "1h"
    },
    "tracesToMetrics": {
      "datasourceUid": "prometheus_uid",
      "tags": [{"key": "service.name", "value": "service"}],
      "queries": [
        {
          "name": "Sample query",
          "query": "sum(rate(tempo_spanmetrics_latency_bucket{$__tags}[5m]))"
        }
      ]
    },
    "serviceMap": {
      "datasourceUid": "prometheus_uid"
    },
    "nodeGraph": {
      "enabled": true
    },
    "search": {
      "hide": false
    },
    "lokiSearch": {
      "datasourceUid": "loki_uid"
    }
  }
}
```

### PostgreSQL Data Source

```json
{
  "name": "PostgreSQL",
  "type": "postgres",
  "url": "postgres.example.com:5432",
  "database": "monitoring",
  "user": "grafana_ro",
  "secureJsonData": {
    "password": "password"
  },
  "jsonData": {
    "sslmode": "require",
    "maxOpenConns": 100,
    "maxIdleConns": 100,
    "connMaxLifetime": 14400,
    "postgresVersion": 1400,
    "timescaledb": false
  }
}
```

### Cloudwatch Data Source

```json
{
  "name": "CloudWatch",
  "type": "cloudwatch",
  "jsonData": {
    "authType": "default",
    "defaultRegion": "us-east-1",
    "assumeRoleArn": "arn:aws:iam::ACCOUNT_ID:role/grafana-cloudwatch-role",
    "externalId": "grafana-cloudwatch"
  }
}
```

### Azure Monitor Data Source

```json
{
  "name": "Azure Monitor",
  "type": "grafana-azure-monitor-datasource",
  "jsonData": {
    "azureAuthType": "msi",
    "cloudName": "azuremonitor",
    "subscriptionId": "SUBSCRIPTION_ID",
    "tenantId": "TENANT_ID"
  }
}
```

## Data Source Provisioning

### Provisioning Configuration File

```yaml
# /etc/grafana/provisioning/datasources/datasources.yml
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: false
    jsonData:
      httpMethod: POST
      queryTimeout: 60s
      timeInterval: 30s

  - name: Loki
    type: loki
    access: proxy
    url: http://loki:3100
    editable: false
    jsonData:
      maxLines: 1000
      derivedFields:
        - matcherRegex: "trace_id=(\\w+)"
          name: TraceID
          url: "$${__value.raw}"
          datasourceUid: tempo

  - name: Tempo
    type: tempo
    access: proxy
    url: http://tempo:3200
    uid: tempo
    editable: false
    jsonData:
      tracesToLogs:
        datasourceUid: loki
        tags: ['job', 'instance']
      tracesToMetrics:
        datasourceUid: prometheus
      nodeGraph:
        enabled: true

  - name: Thanos
    type: prometheus
    access: proxy
    url: http://thanos-query:9090
    editable: false
    jsonData:
      httpMethod: POST
      queryTimeout: 300s
      customQueryParameters: "partial_response=true"
      prometheusType: Thanos

deleteDatasources:
  - name: Old-Prometheus
    orgId: 1
```

## Data Source Security

### TLS Configuration

```yaml
datasources:
  - name: Prometheus-Secure
    type: prometheus
    url: https://prometheus.example.com
    access: proxy
    basicAuth: true
    basicAuthUser: admin
    secureJsonData:
      basicAuthPassword: ${PROMETHEUS_PASSWORD}
      tlsCACert: |
        -----BEGIN CERTIFICATE-----
        ...
        -----END CERTIFICATE-----
      tlsClientCert: |
        -----BEGIN CERTIFICATE-----
        ...
        -----END CERTIFICATE-----
      tlsClientKey: |
        -----BEGIN PRIVATE KEY-----
        ...
        -----END PRIVATE KEY-----
    jsonData:
      tlsAuth: true
      tlsAuthWithCACert: true
      tlsSkipVerify: false
```

### Using Environment Variables

```yaml
datasources:
  - name: Prometheus
    type: prometheus
    url: ${PROMETHEUS_URL}
    basicAuth: true
    basicAuthUser: ${PROMETHEUS_USER}
    secureJsonData:
      basicAuthPassword: ${PROMETHEUS_PASSWORD}
```

### OAuth2 Authentication

```yaml
datasources:
  - name: Grafana-Cloud
    type: prometheus
    url: https://prometheus.grafana.net/api/prom
    access: proxy
    basicAuth: true
    basicAuthUser: ${GRAFANA_CLOUD_USER}
    secureJsonData:
      basicAuthPassword: ${GRAFANA_CLOUD_API_KEY}
    jsonData:
      oauthPassThru: true
```
```