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
curl 'http://localhost:9090/api/v1/query?query=up&debug=true' # Query performance with debug info

promtool query explain 'rate(http_requests_total[5m])' # Explain query execution plan

curl 'http://localhost:9090/api/v1/label/__name__/values' | jq '. | length' # Get series cardinality

```

### Log Analysis

```bash
tail -f /var/log/prometheus/prometheus.log # Follow Prometheus main log
journalctl -u prometheus --since "1 hour ago" # Recent logs from systemd journal

grep "query=" /var/log/prometheus/query.log | awk -F'query=' '{print $2}' | sort | uniq -c | sort -nr # Query log frequency

grep -E "(error|ERROR|failed|FAILED)" /var/log/prometheus/prometheus.log # Search for errors in logs
```

### Performance Monitoring

```promql
# Prometheus self-monitoring queries
prometheus_config_last_reload_successful # Last config reload status
prometheus_tsdb_reloads_total # Total TSDB reloads
prometheus_rule_evaluation_duration_seconds # Rule evaluation duration
prometheus_query_duration_seconds # Query duration
prometheus_engine_query_duration_seconds_sum # Engine query duration sum
prometheus_notifications_total # Notification count
prometheus_remote_storage_samples_total # Remote storage samples
```