### Query API

```bash
# Instant query
curl 'http://localhost:9090/api/v1/query?query=up'
curl 'http://localhost:9090/api/v1/query?query=rate(http_requests_total[5m])'

# Range query
curl 'http://localhost:9090/api/v1/query_range?query=up&start=2023-01-01T00:00:00Z&end=2023-01-01T01:00:00Z&step=15s'

# Series metadata
curl 'http://localhost:9090/api/v1/series?match[]=up'
curl 'http://localhost:9090/api/v1/series?match[]=http_requests_total{job="api"}'

# Label values
curl 'http://localhost:9090/api/v1/label/job/values'
curl 'http://localhost:9090/api/v1/labels'
```

### Admin API

```bash
curl -X POST http://localhost:9090/-/reload # Reload configuration
curl -X POST http://localhost:9090/-/quit # Quit Prometheus
curl http://localhost:9090/-/healthy # Health check
curl http://localhost:9090/-/ready # Ready check
curl http://localhost:9090/api/v1/status/config # Configuration
curl http://localhost:9090/api/v1/status/runtimeinfo # Runtime information
curl http://localhost:9090/api/v1/status/buildinfo # Build information
```

### Targets and Rules API

```bash
curl http://localhost:9090/api/v1/targets # Active targets
curl http://localhost:9090/api/v1/rules # Rules
curl http://localhost:9090/api/v1/alerts # Alerts
```
