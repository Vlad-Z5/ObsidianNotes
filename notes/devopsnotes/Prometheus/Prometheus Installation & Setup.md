### Docker Installation

```bash
# Run Prometheus with custom config
docker run -d --name prometheus \
  -p 9090:9090 \
  -v /path/to/prometheus.yml:/etc/prometheus/prometheus.yml \
  prom/prometheus

# With data persistence
docker run -d --name prometheus \
  -p 9090:9090 \
  -v prometheus-data:/prometheus \
  -v /path/to/prometheus.yml:/etc/prometheus/prometheus.yml \
  prom/prometheus --storage.tsdb.path=/prometheus
```

### Binary Installation

```bash
# Download and extract
wget https://github.com/prometheus/prometheus/releases/download/v2.45.0/prometheus-2.45.0.linux-amd64.tar.gz
tar xvfz prometheus-*.tar.gz
cd prometheus-*

# Create user and directories
sudo useradd --no-create-home --shell /bin/false prometheus
sudo mkdir /etc/prometheus /var/lib/prometheus
sudo chown prometheus:prometheus /etc/prometheus /var/lib/prometheus

# Install binaries
sudo cp prometheus promtool /usr/local/bin/
sudo chown prometheus:prometheus /usr/local/bin/prometheus /usr/local/bin/promtool

# Copy configuration
sudo cp -r consoles/ console_libraries/ /etc/prometheus/
sudo chown -R prometheus:prometheus /etc/prometheus/consoles /etc/prometheus/console_libraries
```

### Systemd Service

```ini
# /etc/systemd/system/prometheus.service
[Unit]
Description=Prometheus
Wants=network-online.target
After=network-online.target

[Service]
User=prometheus
Group=prometheus
Type=simple
ExecStart=/usr/local/bin/prometheus \
  --config.file /etc/prometheus/prometheus.yml \
  --storage.tsdb.path /var/lib/prometheus/ \
  --web.console.templates=/etc/prometheus/consoles \
  --web.console.libraries=/etc/prometheus/console_libraries \
  --web.listen-address=0.0.0.0:9090 \
  --web.enable-lifecycle

[Install]
WantedBy=multi-user.target
```
