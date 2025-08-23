### Command Line Options

```bash
# Basic storage configuration
prometheus \
  --storage.tsdb.path=/var/lib/prometheus \
  --storage.tsdb.retention.time=15d \
  --storage.tsdb.retention.size=10GB \
  --storage.tsdb.min-block-duration=2h \
  --storage.tsdb.max-block-duration=36h

# Advanced options
prometheus \
  --storage.tsdb.wal-compression \
  --storage.tsdb.no-lockfile \
  --storage.remote.flush-deadline=1m
```

### Remote Storage

```yaml
# Remote write
remote_write:
  - url: "https://prometheus-remote-write.example.com/write"
    basic_auth:
      username: user
      password: pass
    write_relabel_configs:
      - source_labels: [__name__]
        regex: 'expensive_metric.*'
        action: drop

# Remote read
remote_read:
  - url: "https://prometheus-remote-read.example.com/read"
    basic_auth:
      username: user
      password: pass
    read_recent: true
```
