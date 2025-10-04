## Resource Optimization

### CPU and Memory Limits

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: grafana
  namespace: monitoring
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: grafana
        image: grafana/grafana:10.2.3
        resources:
          requests:
            cpu: 500m
            memory: 1Gi
          limits:
            cpu: 2000m
            memory: 4Gi
        env:
        - name: GF_DATABASE_MAX_OPEN_CONN
          value: "100"
        - name: GF_DATABASE_MAX_IDLE_CONN
          value: "100"
```

### Horizontal Pod Autoscaling

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: grafana-hpa
  namespace: monitoring
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: grafana
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Percent
        value: 100
        periodSeconds: 30
```

### Vertical Pod Autoscaling

```yaml
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: grafana-vpa
  namespace: monitoring
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: grafana
  updatePolicy:
    updateMode: "Auto"
  resourcePolicy:
    containerPolicies:
    - containerName: grafana
      minAllowed:
        cpu: 250m
        memory: 512Mi
      maxAllowed:
        cpu: 4000m
        memory: 8Gi
      controlledResources:
      - cpu
      - memory
```

## Database Optimization

### PostgreSQL Configuration

```ini
# grafana.ini
[database]
type = postgres
host = postgres.example.com:5432
name = grafana
user = grafana
password = ${GF_DATABASE_PASSWORD}
ssl_mode = require
max_open_conn = 100
max_idle_conn = 100
conn_max_lifetime = 14400
log_queries = false
cache_mode = private
```

### PostgreSQL Tuning

```sql
-- Create indexes for performance
CREATE INDEX idx_dashboard_org_id ON dashboard(org_id);
CREATE INDEX idx_dashboard_uid ON dashboard(uid);
CREATE INDEX idx_dashboard_slug ON dashboard(slug);
CREATE INDEX idx_dashboard_is_folder ON dashboard(is_folder);
CREATE INDEX idx_dashboard_folder_id ON dashboard(folder_id);
CREATE INDEX idx_dashboard_version_dashboard_id ON dashboard_version(dashboard_id);
CREATE INDEX idx_annotation_org_id_alert_id_time ON annotation(org_id, alert_id, time);
CREATE INDEX idx_annotation_org_id_dashboard_id_panel_id_time ON annotation(org_id, dashboard_id, panel_id, time);

-- Analyze tables
ANALYZE dashboard;
ANALYZE dashboard_version;
ANALYZE annotation;
ANALYZE data_source;

-- Vacuum tables
VACUUM ANALYZE dashboard;
VACUUM ANALYZE annotation;
```

### PostgreSQL Connection Pooling (PgBouncer)

```ini
# pgbouncer.ini
[databases]
grafana = host=postgres port=5432 dbname=grafana

[pgbouncer]
listen_port = 6432
listen_addr = *
auth_type = md5
auth_file = /etc/pgbouncer/userlist.txt
pool_mode = transaction
max_client_conn = 1000
default_pool_size = 25
min_pool_size = 10
reserve_pool_size = 5
reserve_pool_timeout = 3
max_db_connections = 100
max_user_connections = 100
server_lifetime = 3600
server_idle_timeout = 600
```

```yaml
# PgBouncer Deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: pgbouncer
  namespace: monitoring
spec:
  replicas: 2
  selector:
    matchLabels:
      app: pgbouncer
  template:
    metadata:
      labels:
        app: pgbouncer
    spec:
      containers:
      - name: pgbouncer
        image: pgbouncer/pgbouncer:1.21.0
        ports:
        - containerPort: 6432
        resources:
          requests:
            cpu: 100m
            memory: 128Mi
          limits:
            cpu: 500m
            memory: 512Mi
        volumeMounts:
        - name: config
          mountPath: /etc/pgbouncer
      volumes:
      - name: config
        configMap:
          name: pgbouncer-config
```

### MySQL Optimization

```ini
# grafana.ini
[database]
type = mysql
host = mysql.example.com:3306
name = grafana
user = grafana
password = ${GF_DATABASE_PASSWORD}
ssl_mode = true
max_open_conn = 100
max_idle_conn = 100
conn_max_lifetime = 14400
```

```sql
-- MySQL indexes
ALTER TABLE dashboard ADD INDEX idx_org_id (org_id);
ALTER TABLE dashboard ADD INDEX idx_uid (uid);
ALTER TABLE dashboard ADD INDEX idx_slug (slug);
ALTER TABLE dashboard ADD INDEX idx_folder_id (folder_id);
ALTER TABLE annotation ADD INDEX idx_org_alert_time (org_id, alert_id, epoch);

-- Optimize tables
OPTIMIZE TABLE dashboard;
OPTIMIZE TABLE dashboard_version;
OPTIMIZE TABLE annotation;
```

## Caching Strategy

### Query Caching

```ini
# grafana.ini
[dataproxy]
timeout = 30
keep_alive_seconds = 30
logging = false
send_user_header = false

[caching]
enabled = true
ttl = 300

[query_caching]
enabled = true
ttl = 300
backend = redis
```

### Redis Cache Backend

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
  namespace: monitoring
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
      - name: redis
        image: redis:7-alpine
        ports:
        - containerPort: 6379
        command:
        - redis-server
        - --maxmemory
        - "2gb"
        - --maxmemory-policy
        - allkeys-lru
        - --save
        - ""
        - --appendonly
        - "no"
        resources:
          requests:
            cpu: 100m
            memory: 256Mi
          limits:
            cpu: 500m
            memory: 2Gi
        volumeMounts:
        - name: redis-data
          mountPath: /data
      volumes:
      - name: redis-data
        emptyDir: {}
---
apiVersion: v1
kind: Service
metadata:
  name: redis
  namespace: monitoring
spec:
  selector:
    app: redis
  ports:
  - port: 6379
    targetPort: 6379
```

```ini
# grafana.ini with Redis
[remote_cache]
type = redis
connstr = addr=redis:6379,pool_size=100,db=0
```

### Memcached Backend

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: memcached
  namespace: monitoring
spec:
  replicas: 2
  selector:
    matchLabels:
      app: memcached
  template:
    metadata:
      labels:
        app: memcached
    spec:
      containers:
      - name: memcached
        image: memcached:1.6-alpine
        ports:
        - containerPort: 11211
        command:
        - memcached
        - -m 1024
        - -c 1024
        - -t 4
        resources:
          requests:
            cpu: 100m
            memory: 256Mi
          limits:
            cpu: 500m
            memory: 1Gi
```

```ini
# grafana.ini with Memcached
[remote_cache]
type = memcache
connstr = memcached:11211
```

## Query Optimization

### Query Timeout Configuration

```ini
# grafana.ini
[dataproxy]
timeout = 30
keep_alive_seconds = 30

[datasources]
query_timeout = 60s
```

### Data Source Query Optimization

```json
{
  "name": "Prometheus",
  "type": "prometheus",
  "url": "http://prometheus:9090",
  "jsonData": {
    "httpMethod": "POST",
    "queryTimeout": "60s",
    "timeInterval": "30s",
    "incrementalQuerying": true,
    "incrementalQueryOverlapWindow": "10m",
    "disableRecordingRules": false,
    "customQueryParameters": "max_source_resolution=5m"
  }
}
```

### Query Result Caching

```json
{
  "panels": [
    {
      "id": 1,
      "title": "CPU Usage",
      "cacheTimeout": "300",
      "interval": "30s",
      "targets": [
        {
          "expr": "rate(node_cpu_seconds_total[5m])",
          "refId": "A",
          "instant": false,
          "range": true
        }
      ]
    }
  ]
}
```

### Query Inspector Best Practices

```yaml
# Optimize queries:
# 1. Use recording rules for complex queries
# 2. Adjust time range and resolution
# 3. Limit series cardinality
# 4. Use proper aggregation
# 5. Avoid regex matching when possible

# Bad query (high cardinality)
sum(rate(http_requests_total[5m]))

# Good query (with aggregation)
sum(rate(http_requests_total[5m])) by (job, status)

# Better query (with recording rule)
sum(job:http_requests:rate5m) by (job, status)
```

## Image Rendering Optimization

### Remote Image Renderer

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: grafana-image-renderer
  namespace: monitoring
spec:
  replicas: 2
  selector:
    matchLabels:
      app: grafana-image-renderer
  template:
    metadata:
      labels:
        app: grafana-image-renderer
    spec:
      containers:
      - name: renderer
        image: grafana/grafana-image-renderer:3.8.4
        ports:
        - containerPort: 8081
        env:
        - name: BROWSER_TZ
          value: UTC
        - name: ENABLE_METRICS
          value: "true"
        - name: HTTP_HOST
          value: "0.0.0.0"
        - name: HTTP_PORT
          value: "8081"
        - name: LOG_LEVEL
          value: info
        resources:
          requests:
            cpu: 250m
            memory: 512Mi
          limits:
            cpu: 1000m
            memory: 2Gi
        livenessProbe:
          httpGet:
            path: /
            port: 8081
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /
            port: 8081
          initialDelaySeconds: 10
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: grafana-image-renderer
  namespace: monitoring
spec:
  selector:
    app: grafana-image-renderer
  ports:
  - port: 8081
    targetPort: 8081
```

```ini
# grafana.ini
[rendering]
server_url = http://grafana-image-renderer:8081/render
callback_url = http://grafana:3000/
concurrent_render_request_limit = 10
```

### Image Rendering HPA

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: grafana-image-renderer-hpa
  namespace: monitoring
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: grafana-image-renderer
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 75
```

## Frontend Optimization

### CDN Configuration

```ini
# grafana.ini
[server]
cdn_url = https://cdn.example.com/grafana
root_url = https://grafana.example.com

[panels]
disable_sanitize_html = false
enable_alpha = false
```

### Asset Optimization

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: nginx-config
  namespace: monitoring
data:
  nginx.conf: |
    server {
      listen 80;
      server_name grafana.example.com;

      gzip on;
      gzip_vary on;
      gzip_min_length 1024;
      gzip_types text/plain text/css text/xml text/javascript application/x-javascript application/xml+rss application/json;

      location /public/ {
        expires 1y;
        add_header Cache-Control "public, immutable";
      }

      location / {
        proxy_pass http://grafana:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_buffering on;
        proxy_buffer_size 4k;
        proxy_buffers 8 4k;
        proxy_busy_buffers_size 8k;
      }
    }
```

### Browser Caching

```ini
# grafana.ini
[server]
static_root_path = public
enable_gzip = true

[users]
viewers_can_edit = false
editors_can_admin = false
```

## Load Balancing

### NGINX Load Balancer

```nginx
upstream grafana_backend {
    least_conn;
    server grafana-1:3000 max_fails=3 fail_timeout=30s;
    server grafana-2:3000 max_fails=3 fail_timeout=30s;
    server grafana-3:3000 max_fails=3 fail_timeout=30s;
    keepalive 32;
}

server {
    listen 80;
    server_name grafana.example.com;

    location / {
        proxy_pass http://grafana_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;

        proxy_buffering on;
        proxy_buffer_size 4k;
        proxy_buffers 8 4k;
    }

    # WebSocket support
    location /api/live/ {
        proxy_pass http://grafana_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_read_timeout 86400;
    }
}
```

### Kubernetes Service with Session Affinity

```yaml
apiVersion: v1
kind: Service
metadata:
  name: grafana
  namespace: monitoring
spec:
  type: ClusterIP
  sessionAffinity: ClientIP
  sessionAffinityConfig:
    clientIP:
      timeoutSeconds: 10800
  selector:
    app: grafana
  ports:
  - port: 3000
    targetPort: 3000
    protocol: TCP
```

### HAProxy Configuration

```cfg
global
    maxconn 4096
    daemon

defaults
    mode http
    timeout connect 5s
    timeout client 30s
    timeout server 30s
    option httplog
    option dontlognull
    option http-server-close
    option redispatch
    retries 3

frontend grafana_frontend
    bind *:80
    bind *:443 ssl crt /etc/ssl/certs/grafana.pem
    default_backend grafana_backend

    # Health check endpoint
    acl is_health_check path /api/health
    use_backend grafana_health if is_health_check

backend grafana_backend
    balance leastconn
    option httpchk GET /api/health
    http-check expect status 200

    server grafana1 grafana-1:3000 check inter 2s fall 3 rise 2
    server grafana2 grafana-2:3000 check inter 2s fall 3 rise 2
    server grafana3 grafana-3:3000 check inter 2s fall 3 rise 2

backend grafana_health
    server health grafana-1:3000
```

## Monitoring Grafana Performance

### Grafana Metrics

```yaml
apiVersion: v1
kind: Service
metadata:
  name: grafana-metrics
  namespace: monitoring
  labels:
    app: grafana
spec:
  selector:
    app: grafana
  ports:
  - name: metrics
    port: 3000
    targetPort: 3000
---
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: grafana
  namespace: monitoring
spec:
  selector:
    matchLabels:
      app: grafana
  endpoints:
  - port: metrics
    path: /metrics
    interval: 30s
```

### Performance Dashboards

```json
{
  "dashboard": {
    "title": "Grafana Performance",
    "panels": [
      {
        "title": "Request Rate",
        "targets": [
          {
            "expr": "rate(grafana_http_request_duration_seconds_count[5m])"
          }
        ]
      },
      {
        "title": "Request Duration p99",
        "targets": [
          {
            "expr": "histogram_quantile(0.99, rate(grafana_http_request_duration_seconds_bucket[5m]))"
          }
        ]
      },
      {
        "title": "Database Query Duration",
        "targets": [
          {
            "expr": "histogram_quantile(0.99, rate(grafana_database_queries_duration_seconds_bucket[5m]))"
          }
        ]
      },
      {
        "title": "Active Users",
        "targets": [
          {
            "expr": "grafana_stat_active_users"
          }
        ]
      },
      {
        "title": "Memory Usage",
        "targets": [
          {
            "expr": "process_resident_memory_bytes{job=\"grafana\"}"
          }
        ]
      }
    ]
  }
}
```

### Alerting Rules

```yaml
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: grafana-performance
  namespace: monitoring
spec:
  groups:
  - name: grafana-performance
    interval: 30s
    rules:
    - alert: GrafanaHighRequestLatency
      expr: histogram_quantile(0.99, rate(grafana_http_request_duration_seconds_bucket[5m])) > 5
      for: 5m
      labels:
        severity: warning
      annotations:
        summary: "Grafana high request latency"
        description: "Grafana p99 latency is {{ $value }}s"

    - alert: GrafanaHighDatabaseLatency
      expr: histogram_quantile(0.99, rate(grafana_database_queries_duration_seconds_bucket[5m])) > 1
      for: 5m
      labels:
        severity: warning
      annotations:
        summary: "Grafana high database query latency"
        description: "Database query p99 latency is {{ $value }}s"

    - alert: GrafanaHighMemoryUsage
      expr: process_resident_memory_bytes{job="grafana"} / 1024 / 1024 / 1024 > 3
      for: 5m
      labels:
        severity: warning
      annotations:
        summary: "Grafana high memory usage"
        description: "Grafana memory usage is {{ $value }}GB"

    - alert: GrafanaHighErrorRate
      expr: rate(grafana_http_request_duration_seconds_count{status_code=~"5.."}[5m]) > 0.05
      for: 5m
      labels:
        severity: critical
      annotations:
        summary: "Grafana high error rate"
        description: "Grafana error rate is {{ $value }} req/s"
```

## Best Practices

### Configuration Tuning

```ini
# grafana.ini - Production optimized
[server]
protocol = https
http_port = 3000
enable_gzip = true

[database]
type = postgres
max_open_conn = 100
max_idle_conn = 100
conn_max_lifetime = 14400
log_queries = false
cache_mode = private

[session]
provider = redis
provider_config = addr=redis:6379,pool_size=100,db=0
cookie_secure = true
session_life_time = 86400

[dataproxy]
timeout = 30
keep_alive_seconds = 30
max_conns_per_host = 0
max_idle_connections = 90

[analytics]
reporting_enabled = false
check_for_updates = false

[dashboards]
versions_to_keep = 20
min_refresh_interval = 5s

[users]
viewers_can_edit = false
editors_can_admin = false

[auth]
disable_login_form = false
oauth_auto_login = false
disable_signout_menu = false

[security]
admin_password = ${GF_SECURITY_ADMIN_PASSWORD}
secret_key = ${GF_SECURITY_SECRET_KEY}
disable_gravatar = true
cookie_secure = true
cookie_samesite = strict

[remote_cache]
type = redis
connstr = addr=redis:6379,pool_size=100,db=0

[rendering]
server_url = http://grafana-image-renderer:8081/render
concurrent_render_request_limit = 10

[unified_alerting]
enabled = true
ha_listen_address = 0.0.0.0:9094
ha_advertise_address = ${POD_IP}:9094
ha_peers = grafana-0.grafana:9094,grafana-1.grafana:9094,grafana-2.grafana:9094
```

### Dashboard Performance Tips

```yaml
# 1. Limit time ranges
defaultTimeRange:
  from: now-1h
  to: now

# 2. Use appropriate refresh intervals
refresh: 30s  # Don't use < 5s

# 3. Limit number of queries per panel
maxDataPoints: 1000

# 4. Use query caching
cacheTimeout: 300

# 5. Optimize queries
# - Use recording rules
# - Limit cardinality
# - Use proper aggregations
# - Avoid regex when possible

# 6. Limit panels per dashboard
# Recommended: < 20 panels per dashboard

# 7. Use dashboard variables efficiently
# - Limit multi-value selections
# - Use query result caching

# 8. Disable unnecessary features
# - Disable annotations if not needed
# - Disable template variable updates
```

### Capacity Planning

```bash
#!/bin/bash
# capacity-planning.sh

# Calculate required resources based on:
# - Number of users
# - Dashboards
# - Data sources
# - Query rate

USERS=500
DASHBOARDS=200
DATASOURCES=10
QPS=1000  # Queries per second

# CPU calculation (rough estimate)
CPU_PER_USER=0.01
CPU_PER_QUERY=0.001
REQUIRED_CPU=$(echo "${USERS} * ${CPU_PER_USER} + ${QPS} * ${CPU_PER_QUERY}" | bc)

# Memory calculation
MEMORY_BASE=512  # MB
MEMORY_PER_USER=2  # MB
MEMORY_PER_DASHBOARD=5  # MB
REQUIRED_MEMORY=$(echo "${MEMORY_BASE} + ${USERS} * ${MEMORY_PER_USER} + ${DASHBOARDS} * ${MEMORY_PER_DASHBOARD}" | bc)

# Replica calculation
TARGET_CPU_PER_POD=2000  # millicores
REPLICAS=$(echo "scale=0; (${REQUIRED_CPU} * 1000) / ${TARGET_CPU_PER_POD} + 1" | bc)

echo "Estimated Requirements:"
echo "  CPU: ${REQUIRED_CPU} cores"
echo "  Memory: ${REQUIRED_MEMORY} MB"
echo "  Replicas: ${REPLICAS}"
```
