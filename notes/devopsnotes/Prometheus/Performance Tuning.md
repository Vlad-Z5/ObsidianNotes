### Memory Optimization

```bash
# Reduce memory usage
prometheus \
  --storage.tsdb.head-chunks-write-queue-size=1000 \
  --query.max-concurrency=10 \
  --query.max-samples=5000000

# For high cardinality
prometheus \
  --storage.tsdb.head-chunks-write-queue-size=10000 \
  --storage.tsdb.wal-segment-size=256MB
```

### CPU Optimization

```yaml
# Reduce scrape frequency for non-critical metrics
scrape_configs:
  - job_name: 'slow-metrics'
    scrape_interval: 5m
    scrape_timeout: 30s
    static_configs:
      - targets: ['app:8080']
    metric_relabel_configs:
      - source_labels: [__name__]
        regex: 'debug_.*'
        action: drop
```

### Cardinality Management

```yaml
# Drop high cardinality metrics
metric_relabel_configs:
  - source_labels: [__name__]
    regex: 'high_cardinality_metric.*'
    action: drop
  - source_labels: [user_id]
    regex: '.*'
    action: drop
  - source_labels: [__name__]
    regex: 'histogram_metric_bucket'
    target_label: __tmp_le
    replacement: ${1}
  - source_labels: [__tmp_le]
    regex: '(0\.05|0\.1|0\.5|1|5)'
    action: keep
```
