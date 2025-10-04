## Common Issues

### Grafana Won't Start

#### Check Logs

```bash
# Docker logs
docker logs grafana

# Kubernetes logs
kubectl logs -n monitoring deployment/grafana

# Systemd logs
journalctl -u grafana-server -f

# File logs
tail -f /var/log/grafana/grafana.log
```

#### Configuration Issues

```bash
# Validate grafana.ini syntax
grafana-server -config /etc/grafana/grafana.ini -check

# Test configuration
grafana-server -config /etc/grafana/grafana.ini -homepath /usr/share/grafana cfg:default.paths.data=/var/lib/grafana

# Check file permissions
ls -la /etc/grafana/grafana.ini
ls -la /var/lib/grafana

# Fix permissions
chown -R grafana:grafana /var/lib/grafana
chmod 640 /etc/grafana/grafana.ini
```

#### Port Conflicts

```bash
# Check if port 3000 is in use
netstat -tulpn | grep :3000
lsof -i :3000

# Change port in grafana.ini
[server]
http_port = 3001
```

#### Database Connection Issues

```bash
# Test PostgreSQL connection
psql -h postgres.example.com -U grafana -d grafana -c "SELECT 1"

# Test MySQL connection
mysql -h mysql.example.com -u grafana -p grafana -e "SELECT 1"

# Check database logs
kubectl logs -n monitoring statefulset/postgres

# Verify credentials
echo $GF_DATABASE_PASSWORD
```

### Login Issues

#### Password Reset

```bash
# Reset admin password (CLI)
grafana-cli admin reset-admin-password newpassword

# Reset via SQL (PostgreSQL)
psql -U grafana grafana -c "UPDATE \"user\" SET password = '59acf18b94d7eb0694c61e60ce44c110c7a683ac6a8f09580d626f90f4a242000746579358d77dd9e570e83fa24faa88a8a6', salt = 'F3FAxVm33R' WHERE login = 'admin';"
# Default password after this: admin

# Reset via SQL (MySQL)
mysql -u grafana -p grafana -e "UPDATE user SET password = '59acf18b94d7eb0694c61e60ce44c110c7a683ac6a8f09580d626f90f4a242000746579358d77dd9e570e83fa24faa88a8a6', salt = 'F3FAxVm33R' WHERE login = 'admin';"
```

#### OAuth Issues

```bash
# Enable OAuth debug logging
[log]
filters = oauth:debug

# Common OAuth errors:
# 1. Invalid redirect_uri - check callback URL
# 2. Invalid client_id/secret - verify credentials
# 3. Missing scopes - add required scopes

# Test OAuth configuration
curl -v "https://oauth-provider.com/authorize?client_id=YOUR_CLIENT_ID&redirect_uri=https://grafana.example.com/login/generic_oauth&response_type=code&scope=openid%20profile%20email"
```

#### LDAP Issues

```bash
# Test LDAP connection
ldapsearch -x -H ldap://ldap.example.com -D "cn=admin,dc=example,dc=com" -w password -b "dc=example,dc=com" "(uid=testuser)"

# Enable LDAP debug logging
[log]
filters = ldap:debug

# Test LDAP configuration
grafana-cli admin ldap-test

# Common LDAP errors:
# 1. Bind failed - check bind_dn and password
# 2. User not found - verify search_filter and search_base_dns
# 3. Group mapping failed - check group_mappings and member_of attribute
```

### Dashboard Issues

#### Dashboard Not Loading

```bash
# Check browser console for errors
# Press F12 → Console tab

# Common issues:
# 1. CORS errors - configure allowed_origins
# 2. Mixed content (HTTP/HTTPS) - use HTTPS everywhere
# 3. Plugin errors - check plugin compatibility

# Check data source connectivity
curl -H "Authorization: Bearer ${API_KEY}" \
  https://grafana.example.com/api/datasources/1/health

# Check dashboard JSON for errors
curl -H "Authorization: Bearer ${API_KEY}" \
  https://grafana.example.com/api/dashboards/uid/dashboard-uid | jq .
```

#### Missing Data

```bash
# Check time range
# - Verify dashboard time range matches data availability
# - Check browser timezone vs data timezone

# Test query directly against data source
curl -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${API_KEY}" \
  -d '{
    "queries": [
      {
        "refId": "A",
        "datasource": {"type": "prometheus", "uid": "prometheus-uid"},
        "expr": "up",
        "instant": false,
        "range": true
      }
    ],
    "from": "now-1h",
    "to": "now"
  }' \
  https://grafana.example.com/api/ds/query

# Check data source configuration
curl -H "Authorization: Bearer ${API_KEY}" \
  https://grafana.example.com/api/datasources/1

# Enable query logging
[log]
filters = tsdb.prometheus:debug
```

#### Variables Not Working

```bash
# Check variable query
# Dashboard Settings → Variables → Test query

# Common issues:
# 1. Incorrect regex - test regex pattern
# 2. Circular dependencies - check variable dependencies
# 3. Data source not selected - verify data source

# Debug variable resolution
# Add this to panel query to see resolved value:
# label_replace(metric, "var", "$variable", "", "")
```

### Data Source Issues

#### Prometheus Data Source

```bash
# Test Prometheus connectivity
curl http://prometheus:9090/api/v1/query?query=up

# Check Prometheus logs
kubectl logs -n monitoring deployment/prometheus

# Common errors:
# 1. "Error reading Prometheus" - check URL and network
# 2. "Timeout" - increase timeout in data source settings
# 3. "Too many requests" - implement rate limiting

# Test query performance
time curl -g 'http://prometheus:9090/api/v1/query_range?query=up&start=1609459200&end=1609545600&step=60'

# Check Prometheus targets
curl http://prometheus:9090/api/v1/targets | jq .
```

#### Loki Data Source

```bash
# Test Loki connectivity
curl http://loki:3100/loki/api/v1/labels

# Test LogQL query
curl -G -s 'http://loki:3100/loki/api/v1/query_range' \
  --data-urlencode 'query={job="varlogs"}' \
  --data-urlencode 'start=1609459200000000000' \
  --data-urlencode 'end=1609545600000000000' | jq .

# Common errors:
# 1. "maximum of series reached" - reduce query scope
# 2. "parse error" - check LogQL syntax
# 3. "context deadline exceeded" - increase timeout

# Check Loki ingester status
curl http://loki:3100/ingester/ring | jq .
```

#### Tempo Data Source

```bash
# Test Tempo connectivity
curl http://tempo:3200/api/search/tags

# Search for trace
curl "http://tempo:3200/api/search?tags=service.name%3Dapi"

# Get trace by ID
curl "http://tempo:3200/api/traces/1234567890abcdef"

# Common errors:
# 1. "trace not found" - check retention period
# 2. "invalid trace ID format" - verify trace ID format
# 3. "backend not accessible" - check tempo-query service
```

### Performance Issues

#### Slow Dashboard Loading

```bash
# Enable profiling
[profiling]
enabled = true

# Access profiling endpoint
curl http://localhost:3000/debug/pprof/

# Check query performance with Query Inspector
# Dashboard → Panel → Edit → Query Inspector

# Optimize slow queries:
# 1. Reduce time range
# 2. Increase interval
# 3. Use recording rules
# 4. Limit series cardinality

# Check database performance
SELECT query, mean_exec_time, calls
FROM pg_stat_statements
WHERE query LIKE '%dashboard%'
ORDER BY mean_exec_time DESC
LIMIT 10;
```

#### High Memory Usage

```bash
# Check memory usage
docker stats grafana
kubectl top pod -n monitoring | grep grafana

# Enable memory profiling
curl http://localhost:3000/debug/pprof/heap > heap.prof
go tool pprof -http=:8080 heap.prof

# Common causes:
# 1. Too many concurrent queries - limit with proxy settings
# 2. Large dashboards - split into multiple dashboards
# 3. Memory leak - restart grafana, check for updates

# Reduce memory usage
[dataproxy]
max_idle_connections = 90
max_idle_connections_per_host = 90

[database]
max_idle_conn = 50
max_open_conn = 50
```

#### Database Performance

```bash
# PostgreSQL: Check slow queries
SELECT
  query,
  calls,
  mean_exec_time,
  max_exec_time
FROM pg_stat_statements
WHERE query LIKE '%grafana%'
ORDER BY mean_exec_time DESC
LIMIT 20;

# PostgreSQL: Check locks
SELECT
  pid,
  usename,
  application_name,
  state,
  query
FROM pg_stat_activity
WHERE datname = 'grafana' AND state != 'idle';

# PostgreSQL: Optimize
VACUUM ANALYZE dashboard;
REINDEX DATABASE grafana;

# MySQL: Check slow queries
SELECT
  DIGEST_TEXT,
  COUNT_STAR,
  AVG_TIMER_WAIT,
  MAX_TIMER_WAIT
FROM performance_schema.events_statements_summary_by_digest
WHERE DIGEST_TEXT LIKE '%grafana%'
ORDER BY AVG_TIMER_WAIT DESC
LIMIT 20;

# MySQL: Optimize
OPTIMIZE TABLE dashboard;
ANALYZE TABLE dashboard;
```

### Plugin Issues

#### Plugin Not Loading

```bash
# Check plugin installation
ls -la /var/lib/grafana/plugins/

# Check plugin logs
tail -f /var/log/grafana/grafana.log | grep plugin

# Verify plugin.json
cat /var/lib/grafana/plugins/my-plugin/plugin.json | jq .

# Check plugin permissions
chown -R grafana:grafana /var/lib/grafana/plugins/
chmod -R 755 /var/lib/grafana/plugins/

# Unsigned plugin issue
[plugins]
allow_loading_unsigned_plugins = myorg-custom-panel

# Reinstall plugin
grafana-cli plugins remove my-plugin
grafana-cli plugins install my-plugin
systemctl restart grafana-server
```

#### Plugin Compatibility

```bash
# Check Grafana version
grafana-cli -v

# Check plugin compatibility
cat /var/lib/grafana/plugins/my-plugin/plugin.json | jq .dependencies

# Update plugin
grafana-cli plugins update my-plugin

# List available versions
grafana-cli plugins list-versions my-plugin

# Install specific version
grafana-cli plugins install my-plugin 1.2.3
```

### Alert Issues

#### Alerts Not Firing

```bash
# Check alert rule status
curl -H "Authorization: Bearer ${API_KEY}" \
  https://grafana.example.com/api/alerts

# Check alert evaluation
curl -H "Authorization: Bearer ${API_KEY}" \
  https://grafana.example.com/api/alerts/1

# Test alert query
curl -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${API_KEY}" \
  -d '{
    "queries": [...],
    "from": "now-5m",
    "to": "now"
  }' \
  https://grafana.example.com/api/ds/query

# Check alertmanager connectivity
curl http://alertmanager:9093/api/v2/status

# Enable alert debug logging
[log]
filters = alerting:debug
```

#### Unified Alerting Issues

```bash
# Check alert rules
curl -H "Authorization: Bearer ${API_KEY}" \
  https://grafana.example.com/api/ruler/grafana/api/v1/rules

# Check alert state
curl -H "Authorization: Bearer ${API_KEY}" \
  https://grafana.example.com/api/v1/rules

# Check contact points
curl -H "Authorization: Bearer ${API_KEY}" \
  https://grafana.example.com/api/v1/provisioning/contact-points

# Test notification
curl -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${API_KEY}" \
  -d '{
    "name": "test-alert",
    "message": "Test notification"
  }' \
  https://grafana.example.com/api/v1/provisioning/contact-points/test

# Check Grafana alerting logs
kubectl logs -n monitoring deployment/grafana | grep alerting
```

### Image Rendering Issues

#### Rendering Timeout

```bash
# Increase timeout
[rendering]
server_url = http://grafana-image-renderer:8081/render
concurrent_render_request_limit = 10

# Check renderer logs
kubectl logs -n monitoring deployment/grafana-image-renderer

# Test renderer directly
curl http://grafana-image-renderer:8081/render \
  -d url=http://grafana:3000/d/dashboard-uid \
  -d width=1920 \
  -d height=1080 \
  -d timeout=60

# Common issues:
# 1. Timeout - increase timeout in config
# 2. Out of memory - increase renderer memory limits
# 3. Fonts missing - install required fonts in renderer
```

#### Image Quality Issues

```bash
# Adjust rendering settings
[rendering]
server_url = http://grafana-image-renderer:8081/render
callback_url = http://grafana:3000/

# Renderer environment variables
RENDERING_VIEWPORT_WIDTH=1920
RENDERING_VIEWPORT_HEIGHT=1080
RENDERING_VIEWPORT_DEVICE_SCALE_FACTOR=2
RENDERING_IGNORE_HTTPS_ERRORS=false
RENDERING_TIMING_TIMEOUT=30
```

### Network Issues

#### CORS Errors

```bash
# Configure CORS in grafana.ini
[server]
root_url = https://grafana.example.com

[security]
allow_embedding = false

# For embedding in iframe
[security]
allow_embedding = true
cookie_samesite = none

# Add specific origins
[cors]
allow_origin = https://example.com,https://app.example.com
```

#### SSL/TLS Issues

```bash
# Verify certificate
openssl s_client -connect grafana.example.com:443 -servername grafana.example.com

# Check certificate expiry
echo | openssl s_client -connect grafana.example.com:443 2>/dev/null | openssl x509 -noout -dates

# Disable certificate verification (not recommended for production)
[dataproxy]
skip_tls_verify = true

# Use custom CA certificate
[database]
ssl_mode = verify-ca
ca_cert_path = /etc/grafana/ssl/ca.crt
```

#### WebSocket Issues

```bash
# Check WebSocket connectivity
wscat -c wss://grafana.example.com/api/live/ws

# Configure nginx for WebSocket
location /api/live/ {
    proxy_pass http://grafana_backend;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_read_timeout 86400;
}

# Enable live features
[live]
max_connections = 100
```

### Kubernetes-Specific Issues

#### Pod CrashLoopBackOff

```bash
# Check pod status
kubectl get pods -n monitoring | grep grafana

# Check pod events
kubectl describe pod -n monitoring grafana-xxx

# Check logs
kubectl logs -n monitoring grafana-xxx --previous

# Common causes:
# 1. Missing ConfigMap/Secret - check references
# 2. Permission issues - check securityContext
# 3. Resource limits - check OOMKilled events
# 4. Liveness probe failing - adjust probe settings

# Debug with ephemeral container
kubectl debug -n monitoring grafana-xxx -it --image=busybox
```

#### Persistent Volume Issues

```bash
# Check PVC status
kubectl get pvc -n monitoring | grep grafana

# Check PV
kubectl get pv | grep grafana

# Check events
kubectl get events -n monitoring --sort-by='.lastTimestamp' | grep grafana

# Fix permission issues
kubectl exec -n monitoring grafana-xxx -- chown -R 472:472 /var/lib/grafana

# Check storage class
kubectl get storageclass
```

#### Service Discovery Issues

```bash
# Check service endpoints
kubectl get endpoints -n monitoring grafana

# Test service connectivity
kubectl run test-pod --rm -it --image=busybox -- sh
wget -O- http://grafana.monitoring.svc.cluster.local:3000/api/health

# Check DNS resolution
kubectl exec -n monitoring grafana-xxx -- nslookup prometheus

# Check NetworkPolicy
kubectl get networkpolicy -n monitoring
kubectl describe networkpolicy -n monitoring grafana
```

## Debugging Tools

### Enable Debug Logging

```ini
# grafana.ini
[log]
mode = console file
level = debug
filters = alerting:debug,oauth:debug,ldap:debug,tsdb.prometheus:debug,plugins:debug

[log.console]
level = debug
format = json

[log.file]
level = debug
format = json
log_rotate = true
max_lines = 1000000
max_size_shift = 28
daily_rotate = true
max_days = 7
```

### Query Inspector

```yaml
# Access Query Inspector in UI:
# 1. Open dashboard
# 2. Edit panel
# 3. Click "Query Inspector" button
# 4. View:
#    - Query
#    - Response
#    - Stats (duration, rows)
#    - JSON model

# Use to debug:
# - Slow queries
# - No data issues
# - Unexpected results
# - Data source errors
```

### API Health Check

```bash
#!/bin/bash
# health-check.sh

GRAFANA_URL="https://grafana.example.com"
API_KEY="${GRAFANA_API_KEY}"

echo "=== Grafana Health Check ==="

# Basic health
health=$(curl -s "${GRAFANA_URL}/api/health")
echo "Health: ${health}"

# Database health
db_health=$(echo "${health}" | jq -r '.database')
echo "Database: ${db_health}"

# Check API
api_check=$(curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer ${API_KEY}" \
  "${GRAFANA_URL}/api/org")
echo "API Status: ${api_check}"

# Check data sources
datasources=$(curl -s -H "Authorization: Bearer ${API_KEY}" \
  "${GRAFANA_URL}/api/datasources")
echo "Data Sources: $(echo ${datasources} | jq length)"

# Test each data source
echo "${datasources}" | jq -r '.[].id' | while read ds_id; do
  ds_name=$(echo "${datasources}" | jq -r ".[] | select(.id == ${ds_id}) | .name")
  ds_health=$(curl -s -X POST \
    -H "Authorization: Bearer ${API_KEY}" \
    "${GRAFANA_URL}/api/datasources/${ds_id}/health" | jq -r '.status')
  echo "  ${ds_name}: ${ds_health}"
done
```

### Performance Profiling

```bash
# CPU profiling
curl http://localhost:3000/debug/pprof/profile?seconds=30 > cpu.prof
go tool pprof -http=:8080 cpu.prof

# Memory profiling
curl http://localhost:3000/debug/pprof/heap > mem.prof
go tool pprof -http=:8080 mem.prof

# Goroutine profiling
curl http://localhost:3000/debug/pprof/goroutine > goroutine.prof
go tool pprof -http=:8080 goroutine.prof

# Block profiling
curl http://localhost:3000/debug/pprof/block > block.prof
go tool pprof -http=:8080 block.prof
```

### Database Diagnostics

```bash
#!/bin/bash
# db-diagnostics.sh

DB_HOST="postgres.example.com"
DB_NAME="grafana"
DB_USER="grafana"

# Connection count
psql -h ${DB_HOST} -U ${DB_USER} ${DB_NAME} -c "
SELECT count(*) as connections
FROM pg_stat_activity
WHERE datname = '${DB_NAME}';"

# Table sizes
psql -h ${DB_HOST} -U ${DB_USER} ${DB_NAME} -c "
SELECT
  tablename,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;"

# Long-running queries
psql -h ${DB_HOST} -U ${DB_USER} ${DB_NAME} -c "
SELECT
  pid,
  now() - query_start AS duration,
  query
FROM pg_stat_activity
WHERE state = 'active'
  AND now() - query_start > interval '1 minute'
ORDER BY duration DESC;"

# Index usage
psql -h ${DB_HOST} -U ${DB_USER} ${DB_NAME} -c "
SELECT
  schemaname,
  tablename,
  indexname,
  idx_scan,
  idx_tup_read,
  idx_tup_fetch
FROM pg_stat_user_indexes
WHERE idx_scan = 0
  AND schemaname = 'public'
ORDER BY tablename;"
```

### Log Analysis

```bash
#!/bin/bash
# analyze-logs.sh

LOG_FILE="/var/log/grafana/grafana.log"

echo "=== Error Summary ==="
grep -i error ${LOG_FILE} | tail -100 | jq -r '.msg' | sort | uniq -c | sort -rn | head -20

echo ""
echo "=== Slow Queries (> 1s) ==="
jq -r 'select(.logger == "tsdb.prometheus" and .duration > 1000) | "\(.duration)ms - \(.expr)"' ${LOG_FILE} | sort -rn | head -20

echo ""
echo "=== Failed Login Attempts ==="
jq -r 'select(.msg == "Invalid username or password") | "\(.remote_addr) - \(.username)"' ${LOG_FILE} | sort | uniq -c | sort -rn | head -20

echo ""
echo "=== API Errors (5xx) ==="
jq -r 'select(.status >= 500) | "\(.status) - \(.method) \(.path)"' ${LOG_FILE} | sort | uniq -c | sort -rn | head -20

echo ""
echo "=== Plugin Errors ==="
grep -i "plugin" ${LOG_FILE} | grep -i "error" | tail -20
```

## Recovery Procedures

### Restore from Backup

```bash
#!/bin/bash
# restore-grafana.sh

BACKUP_FILE="${1}"
GRAFANA_URL="https://grafana.example.com"
API_KEY="${GRAFANA_API_KEY}"

if [ -z "${BACKUP_FILE}" ]; then
  echo "Usage: $0 <backup.tar.gz>"
  exit 1
fi

# Extract backup
TEMP_DIR=$(mktemp -d)
tar xzf "${BACKUP_FILE}" -C "${TEMP_DIR}"

# Restore data sources
for ds in "${TEMP_DIR}"/datasources/*.json; do
  curl -X POST \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer ${API_KEY}" \
    -d @"${ds}" \
    "${GRAFANA_URL}/api/datasources"
done

# Restore folders
for folder in "${TEMP_DIR}"/folders/*.json; do
  curl -X POST \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer ${API_KEY}" \
    -d @"${folder}" \
    "${GRAFANA_URL}/api/folders"
done

# Restore dashboards
for dash in "${TEMP_DIR}"/dashboards/*.json; do
  jq '{dashboard: ., overwrite: true}' "${dash}" | \
    curl -X POST \
      -H "Content-Type: application/json" \
      -H "Authorization: Bearer ${API_KEY}" \
      -d @- \
      "${GRAFANA_URL}/api/dashboards/db"
done

rm -rf "${TEMP_DIR}"
echo "Restore completed"
```

### Emergency Rollback

```bash
#!/bin/bash
# rollback-grafana.sh

NAMESPACE="monitoring"
DEPLOYMENT="grafana"

# Get previous revision
PREVIOUS_REVISION=$(kubectl rollout history deployment/${DEPLOYMENT} -n ${NAMESPACE} | tail -2 | head -1 | awk '{print $1}')

echo "Rolling back to revision ${PREVIOUS_REVISION}"

# Rollback
kubectl rollout undo deployment/${DEPLOYMENT} -n ${NAMESPACE} --to-revision=${PREVIOUS_REVISION}

# Wait for rollback
kubectl rollout status deployment/${DEPLOYMENT} -n ${NAMESPACE} --timeout=5m

# Verify
kubectl get pods -n ${NAMESPACE} | grep ${DEPLOYMENT}
```
