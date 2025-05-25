### Basic prometheus.yml

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    cluster: 'production'
    region: 'us-west-1'

rule_files:
  - "rules/*.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node1:9100', 'node2:9100']
    scrape_interval: 30s
    metrics_path: /metrics
    
  - job_name: 'kubernetes-pods'
    kubernetes_sd_configs:
      - role: pod
    relabel_configs:
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
        action: keep
        regex: true
```

### Advanced Configuration Options

```yaml
global:
  scrape_interval: 15s
  scrape_timeout: 10s
  evaluation_interval: 15s
  query_log_file: /var/log/prometheus/query.log
  
scrape_configs:
  - job_name: 'custom-app'
    honor_labels: true
    honor_timestamps: true
    scrape_interval: 30s
    scrape_timeout: 10s
    metrics_path: /custom/metrics
    scheme: https
    params:
      format: ['prometheus']
    basic_auth:
      username: admin
      password: secret
    tls_config:
      ca_file: /etc/ssl/certs/ca.pem
      cert_file: /etc/ssl/certs/client.pem
      key_file: /etc/ssl/private/client.key
      insecure_skip_verify: false
    static_configs:
      - targets: ['app1:8080', 'app2:8080']
        labels:
          environment: production
          team: backend
```
