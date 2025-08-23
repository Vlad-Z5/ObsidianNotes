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
    "y":
```