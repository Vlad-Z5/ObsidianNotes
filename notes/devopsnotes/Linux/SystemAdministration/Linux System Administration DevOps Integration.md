# Linux System Administration DevOps Integration

**DevOps-Specific System Administration** covers container integration, configuration management, monitoring setup, and security hardening specifically tailored for DevOps environments.

## Container Integration

### Systemd and Container Services

#### Podman Systemd Integration
```bash
# Generate systemd service for container
podman generate systemd --name mycontainer --files --new
systemctl --user daemon-reload
systemctl --user enable container-mycontainer.service
systemctl --user start container-mycontainer.service

# Rootless container service management
systemctl --user status container-mycontainer.service
systemctl --user stop container-mycontainer.service
systemctl --user restart container-mycontainer.service

# Auto-start containers at boot (rootless)
loginctl enable-linger username       # Enable user services at boot
systemctl --user enable container-mycontainer.service
```

#### Docker with Systemd Service
```bash
# Docker container as systemd service
cat << 'EOF' > /etc/systemd/system/docker-myapp.service
[Unit]
Description=My Dockerized Application
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=true
ExecStart=/usr/bin/docker run -d --name myapp --restart=unless-stopped \
  -p 8080:8080 \
  -v /opt/myapp/data:/data \
  -v /opt/myapp/config:/config:ro \
  --memory=512m \
  --cpus=1 \
  myapp:latest
ExecStop=/usr/bin/docker stop myapp
ExecStopPost=/usr/bin/docker rm myapp
TimeoutStartSec=300
TimeoutStopSec=30

[Install]
WantedBy=multi-user.target
EOF

# Enable and manage the service
systemctl daemon-reload
systemctl enable docker-myapp.service
systemctl start docker-myapp.service
```

#### Container Health Monitoring
```bash
# Container service monitoring
systemctl status docker-myapp.service
journalctl -u docker-myapp.service -f
docker logs -f myapp
docker stats myapp

# Health check integration
cat << 'EOF' > /etc/systemd/system/docker-webapp.service
[Unit]
Description=Web Application Container
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=true
ExecStart=/usr/bin/docker run -d --name webapp \
  --restart=unless-stopped \
  --health-cmd="curl -f http://localhost:8080/health || exit 1" \
  --health-interval=30s \
  --health-timeout=10s \
  --health-retries=3 \
  -p 8080:8080 \
  webapp:latest
ExecStop=/usr/bin/docker stop webapp
ExecStopPost=/usr/bin/docker rm webapp

[Install]
WantedBy=multi-user.target
EOF
```

## Configuration Management Integration

### Ansible Integration

#### System Facts and Information Gathering
```bash
# Gather system facts
ansible localhost -m setup              # Gather all system facts
ansible localhost -m setup -a 'filter=ansible_memory_mb'  # Specific facts
ansible localhost -m setup -a 'filter=ansible_distribution*'  # OS info
ansible localhost -m setup -a 'gather_subset=hardware'  # Hardware facts only

# Custom fact gathering
mkdir -p /etc/ansible/facts.d
cat << 'EOF' > /etc/ansible/facts.d/custom.fact
#!/bin/bash
echo "{\"custom_metric\": \"$(uptime | awk '{print $3}')\"}"
EOF
chmod +x /etc/ansible/facts.d/custom.fact

# Test custom facts
ansible localhost -m setup -a 'filter=ansible_local'
```

#### Ansible Playbook Examples
```bash
# Service management playbook
cat << 'EOF' > service-management.yml
---
- hosts: all
  become: yes
  tasks:
    - name: Ensure nginx is installed
      package:
        name: nginx
        state: present

    - name: Start and enable nginx
      systemd:
        name: nginx
        state: started
        enabled: yes
        daemon_reload: yes

    - name: Configure firewall for nginx
      firewalld:
        service: http
        permanent: yes
        state: enabled
        immediate: yes
      when: ansible_os_family == "RedHat"

    - name: Configure UFW for nginx
      ufw:
        rule: allow
        port: '80'
        proto: tcp
      when: ansible_os_family == "Debian"

    - name: Verify nginx is running
      uri:
        url: http://localhost
        method: GET
        status_code: 200
      register: nginx_check
      failed_when: false

    - name: Display nginx status
      debug:
        msg: "Nginx is {{ 'running' if nginx_check.status == 200 else 'not responding' }}"
EOF

# Run playbook with different options
ansible-playbook -C service-management.yml        # Dry run (check mode)
ansible-playbook service-management.yml           # Normal run
ansible-playbook -v service-management.yml        # Verbose output
```

#### Ansible Vault for Secrets Management
```bash
# Create encrypted variables
ansible-vault encrypt_string 'secret_password' --name 'db_password'
ansible-vault encrypt_string 'api_key_12345' --name 'api_key'

# Vault file management
ansible-vault create secrets.yml        # Create encrypted file
ansible-vault edit secrets.yml          # Edit encrypted file
ansible-vault view secrets.yml          # View encrypted file
ansible-vault decrypt secrets.yml       # Decrypt file
ansible-vault encrypt secrets.yml       # Encrypt existing file

# Use vault in playbooks
cat << 'EOF' > secure-deployment.yml
---
- hosts: all
  vars_files:
    - secrets.yml
  tasks:
    - name: Deploy application with secrets
      docker_container:
        name: myapp
        image: myapp:latest
        env:
          DB_PASSWORD: "{{ db_password }}"
          API_KEY: "{{ api_key }}"
EOF

# Run playbook with vault
ansible-playbook --ask-vault-pass secure-deployment.yml
```

## Monitoring and Observability

### Prometheus Node Exporter Setup
```bash
# Create node_exporter user
useradd --no-create-home --shell /bin/false node_exporter

# Node exporter service configuration
cat << 'EOF' > /etc/systemd/system/node_exporter.service
[Unit]
Description=Prometheus Node Exporter
After=network.target

[Service]
Type=simple
User=node_exporter
Group=node_exporter
ExecStart=/usr/local/bin/node_exporter \
  --web.listen-address=:9100 \
  --path.procfs=/proc \
  --path.sysfs=/sys \
  --collector.filesystem.ignored-mount-points="^/(sys|proc|dev|host|etc|rootfs/var/lib/docker/containers|rootfs/var/lib/docker/overlay2|rootfs/run/docker/netns|rootfs/var/lib/docker/aufs)($|/)" \
  --collector.netdev.ignored-devices="^(veth.*|docker.*|br-.*|lo)$" \
  --collector.textfile.directory=/var/lib/node_exporter/textfile_collector
Restart=always
RestartSec=5
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/var/lib/node_exporter

[Install]
WantedBy=multi-user.target
EOF

# Create textfile collector directory
mkdir -p /var/lib/node_exporter/textfile_collector
chown node_exporter:node_exporter /var/lib/node_exporter/textfile_collector

# Enable and start service
systemctl daemon-reload
systemctl enable node_exporter
systemctl start node_exporter

# Verify metrics endpoint
curl http://localhost:9100/metrics | head -20
```

### Custom Metrics Collection
```bash
# Custom metrics script
cat << 'EOF' > /usr/local/bin/custom-metrics
#!/bin/bash
# Custom metrics collector

TEXTFILE_COLLECTOR_DIR="/var/lib/node_exporter/textfile_collector"
METRICS_FILE="$TEXTFILE_COLLECTOR_DIR/custom.prom"

# Collect custom metrics
{
    echo "# HELP custom_disk_usage_percent Disk usage percentage"
    echo "# TYPE custom_disk_usage_percent gauge"
    df / | awk 'NR==2 {print "custom_disk_usage_percent{mount=\"/\"} " $5}' | sed 's/%//'

    echo "# HELP custom_load_average System load average"
    echo "# TYPE custom_load_average gauge"
    uptime | awk -F'load average:' '{print $2}' | awk -F, '{print "custom_load_average{period=\"1m\"} " $1; print "custom_load_average{period=\"5m\"} " $2; print "custom_load_average{period=\"15m\"} " $3}'

    echo "# HELP custom_service_status Service status (1=active, 0=inactive)"
    echo "# TYPE custom_service_status gauge"
    for service in nginx docker sshd; do
        status=$(systemctl is-active $service 2>/dev/null)
        value=$([ "$status" = "active" ] && echo 1 || echo 0)
        echo "custom_service_status{service=\"$service\"} $value"
    done
} > "$METRICS_FILE.$$"

mv "$METRICS_FILE.$$" "$METRICS_FILE"
EOF

chmod +x /usr/local/bin/custom-metrics

# Set up cron job for custom metrics
cat << 'EOF' > /etc/cron.d/custom-metrics
# Collect custom metrics every minute
* * * * * node_exporter /usr/local/bin/custom-metrics
EOF

# Test custom metrics
/usr/local/bin/custom-metrics
cat /var/lib/node_exporter/textfile_collector/custom.prom
```

### Log Aggregation Configuration

#### Rsyslog Configuration
```bash
# Configure rsyslog for centralized logging
cat << 'EOF' >> /etc/rsyslog.conf
# Load modules for remote logging
module(load="imudp")
input(type="imudp" port="514")

# Forward all logs to central server
*.* @@logserver.example.com:514

# Local log filtering and formatting
$template CustomFormat,"%timegenerated% %HOSTNAME% %syslogtag% %msg%\n"

# Application-specific log routing
local0.info     /var/log/myapp.log;CustomFormat
local0.warn     /var/log/myapp-warnings.log;CustomFormat
& stop

# High-priority alerts
*.emerg         :omusrmsg:*
*.alert         /var/log/alerts.log
*.crit          /var/log/critical.log

# Performance tuning
$MainMsgQueueSize 50000
$WorkDirectory /var/spool/rsyslog
$ActionQueueType LinkedList
$ActionQueueFileName queue
$ActionResumeRetryCount -1
$ActionQueueSaveOnShutdown on
EOF

# Restart rsyslog
systemctl restart rsyslog
systemctl status rsyslog
```

#### Journald Configuration for DevOps
```bash
# Configure journald for better DevOps integration
cat << 'EOF' > /etc/systemd/journald.conf.d/devops.conf
[Journal]
# Storage configuration
Storage=persistent
SystemMaxUse=1G
SystemKeepFree=2G
SystemMaxFileSize=100M
MaxRetentionSec=1month

# Forward to external systems
ForwardToSyslog=yes
MaxLevelStore=info
MaxLevelSyslog=debug

# Performance tuning
RateLimitInterval=30s
RateLimitBurst=10000
EOF

systemctl restart systemd-journald

# Verify journald configuration
journalctl --disk-usage
systemctl status systemd-journald
```

## Security Hardening

### SSH Hardening Configuration
```bash
# Comprehensive SSH hardening
cat << 'EOF' > /etc/ssh/sshd_config.d/99-hardening.conf
# Protocol and encryption
Protocol 2
Ciphers chacha20-poly1305@openssh.com,aes256-gcm@openssh.com,aes128-gcm@openssh.com,aes256-ctr,aes192-ctr,aes128-ctr
MACs hmac-sha2-256-etm@openssh.com,hmac-sha2-512-etm@openssh.com,hmac-sha2-256,hmac-sha2-512
KexAlgorithms curve25519-sha256@libssh.org,diffie-hellman-group16-sha512,diffie-hellman-group18-sha512

# Authentication
MaxAuthTries 3
LoginGraceTime 60
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
AuthenticationMethods publickey
MaxStartups 3:30:10

# Access control
AllowGroups sshusers
DenyUsers root guest
DenyGroups wheel

# Session management
ClientAliveInterval 300
ClientAliveCountMax 2
MaxSessions 2

# Logging and monitoring
LogLevel VERBOSE
SyslogFacility AUTHPRIV

# Disable unused features
PermitEmptyPasswords no
PermitUserEnvironment no
AllowAgentForwarding no
AllowTcpForwarding no
X11Forwarding no
PrintMotd no
EOF

# Validate SSH configuration
sshd -t
systemctl restart sshd
```

### Firewall Configuration
```bash
# Comprehensive firewall setup with firewalld
systemctl enable firewalld
systemctl start firewalld

# Basic configuration
firewall-cmd --set-default-zone=public
firewall-cmd --permanent --add-service=ssh
firewall-cmd --permanent --add-service=http
firewall-cmd --permanent --add-service=https

# Custom service definitions
cat << 'EOF' > /etc/firewalld/services/node-exporter.xml
<?xml version="1.0" encoding="utf-8"?>
<service>
  <short>Node Exporter</short>
  <description>Prometheus Node Exporter</description>
  <port protocol="tcp" port="9100"/>
</service>
EOF

cat << 'EOF' > /etc/firewalld/services/myapp.xml
<?xml version="1.0" encoding="utf-8"?>
<service>
  <short>MyApp</short>
  <description>Custom Application</description>
  <port protocol="tcp" port="8080"/>
</service>
EOF

# Apply custom services
firewall-cmd --permanent --add-service=node-exporter --zone=internal
firewall-cmd --permanent --add-service=myapp

# Rich rules for specific access
firewall-cmd --permanent --add-rich-rule='rule family="ipv4" source address="10.0.0.0/8" service name="node-exporter" accept'
firewall-cmd --permanent --add-rich-rule='rule family="ipv4" source address="192.168.1.100" port protocol="tcp" port="22" accept'

# Reload firewall
firewall-cmd --reload
firewall-cmd --list-all
```

### System Security Limits
```bash
# Security limits configuration
cat << 'EOF' > /etc/security/limits.d/99-security.conf
# Security limits for all users
* hard core 0                          # Disable core dumps
* soft nproc 4096                      # Process limits
* hard nproc 8192
* soft nofile 8192                     # File descriptor limits
* hard nofile 16384

# Specific limits for service accounts
nginx soft nproc 2048
nginx hard nproc 4096
mysql soft nofile 16384
mysql hard nofile 32768

# Root limits
root soft nproc 32768
root hard nproc 65536
EOF

# Kernel security parameters
cat << 'EOF' > /etc/sysctl.d/99-security.conf
# Network security
net.ipv4.conf.all.send_redirects = 0
net.ipv4.conf.default.send_redirects = 0
net.ipv4.conf.all.accept_redirects = 0
net.ipv4.conf.default.accept_redirects = 0
net.ipv4.conf.all.accept_source_route = 0
net.ipv4.conf.default.accept_source_route = 0
net.ipv4.icmp_echo_ignore_broadcasts = 1
net.ipv4.icmp_ignore_bogus_error_responses = 1
net.ipv4.ip_forward = 0
net.ipv4.tcp_syncookies = 1

# IPv6 security
net.ipv6.conf.all.accept_redirects = 0
net.ipv6.conf.default.accept_redirects = 0
net.ipv6.conf.all.accept_source_route = 0
net.ipv6.conf.default.accept_source_route = 0

# System security
kernel.dmesg_restrict = 1
kernel.kptr_restrict = 2
kernel.yama.ptrace_scope = 1
kernel.randomize_va_space = 2
fs.suid_dumpable = 0
fs.protected_hardlinks = 1
fs.protected_symlinks = 1

# Memory and process security
vm.mmap_rnd_bits = 32
vm.mmap_rnd_compat_bits = 16
kernel.unprivileged_bpf_disabled = 1
net.core.bpf_jit_harden = 2
EOF

# Apply security settings
sysctl --system

# Verify settings
sysctl -a | grep -E "(net\.ipv4\.ip_forward|kernel\.dmesg_restrict)"
```