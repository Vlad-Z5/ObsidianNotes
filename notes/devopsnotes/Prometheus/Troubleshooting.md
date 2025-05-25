### Common Issues and Solutions

```bash
# Check Prometheus status
systemctl status prometheus
journalctl -u prometheus -f

# Check configuration
promtool check config /etc/prometheus/prometheus.yml
promtool check rules /etc/prometheus/rules/*.yml

# Check web interface
curl -s http://localhost:9090/-/healthy
curl -s http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | select(.health != "up")'

# Check disk space
df -h /var/lib/prometheus
du -sh /var/lib/prometheus/*

# Check memory usage
ps aux | grep prometheus
cat /proc/$(pgrep prometheus)/status | grep -E "VmRSS|VmSize"
```

### Debugging Queries

```bash
# Query performance
curl 'http://localhost:9090/api/v1/query?query=up&debug=true'

# Explain query
promtool query explain 'rate(http_requests_total[5m])'

# Series cardinality
curl 'http://localhost:9090/api/v1/label/__name__/values' | jq '. | length'
```

### Log Analysis

```bash
# Common log locations
tail -f /var/log/prometheus/prometheus.log
journalctl -u prometheus --since "1 hour ago"

# Query log analysis
grep "query=" /var/log/prometheus/query.log | awk -F'query=' '{print $2}' | sort | uniq -c | sort -nr

# Error patterns
grep -E "(error|ERROR|failed|FAILED)" /var/log/prometheus/prometheus.log
```

### Performance Monitoring

```promql
# Prometheus self-monitoring queries
prometheus_config_last_reload_successful
prometheus_tsdb_reloads_total
prometheus_rule_evaluation_duration_seconds
prometheus_query_duration_seconds
prometheus_engine_query_duration_seconds_sum
prometheus_notifications_total
prometheus_remote_storage_samples_total
```