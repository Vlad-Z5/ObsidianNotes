# Linux Systemd Dependencies

**Systemd dependencies** define relationships between services, ensuring proper startup order, failure handling, and service coordination in complex system architectures.

## Dependency Types

### Hard Dependencies
```bash
# Requires: Hard dependency - fails if dependency fails
Requires=database.service       # Service cannot start without database

# Requisite: Must already be running
Requisite=network.service       # Network must be active before starting

# BindsTo: Lifecycle binding
BindsTo=device.mount           # Stop when device is unmounted
```

### Soft Dependencies
```bash
# Wants: Soft dependency - continues if dependency fails
Wants=cache.service            # Prefer cache but continue without it

# PartOf: Stop/restart together
PartOf=web-stack.service       # Stop when web-stack stops
```

### Ordering Dependencies
```bash
# After: Start after specified units
After=network.target database.service

# Before: Start before specified units
Before=web-frontend.service

# Note: Ordering doesn't imply dependency
# Use with Requires/Wants for complete dependency
```

### Conflict Resolution
```bash
# Conflicts: Cannot run simultaneously
Conflicts=apache2.service      # Either nginx or apache2, not both
```

## Dependency Examples

### Web Application Stack
```bash
# Database service
[Unit]
Description=PostgreSQL Database
After=network.target

[Service]
Type=notify
ExecStart=/usr/bin/postgres
User=postgres

# Application service
[Unit]
Description=Web Application
Wants=network-online.target
After=network-online.target
Requires=postgresql.service    # Hard dependency
After=postgresql.service       # Order dependency
Before=nginx.service          # Start before reverse proxy

[Service]
Type=simple
ExecStart=/usr/local/bin/webapp
User=webapp

# Reverse proxy service
[Unit]
Description=Nginx Reverse Proxy
Wants=webapp.service          # Soft dependency
After=webapp.service          # Order dependency

[Service]
Type=forking
ExecStart=/usr/sbin/nginx
```

### Load Balancer with Multiple Backends
```bash
# Load balancer service
[Unit]
Description=HAProxy Load Balancer
Documentation=https://company.com/docs/haproxy
Wants=webapp@1.service webapp@2.service webapp@3.service
After=webapp@1.service webapp@2.service webapp@3.service
Requires=network-online.target
After=network-online.target

[Service]
Type=forking
ExecStart=/usr/sbin/haproxy -f /etc/haproxy/haproxy.cfg
ExecReload=/bin/kill -USR2 $MAINPID
```

### Microservices Dependencies
```bash
# API Gateway service
[Unit]
Description=API Gateway
Wants=auth-service.service user-service.service order-service.service
After=auth-service.service user-service.service order-service.service
Requires=network-online.target consul.service
After=network-online.target consul.service

[Service]
Type=simple
ExecStart=/usr/local/bin/api-gateway

# Service discovery dependency
[Unit]
Description=User Service
Requires=consul.service database.service
After=consul.service database.service
PartOf=microservices.target

[Service]
Type=simple
ExecStart=/usr/local/bin/user-service
```

## Advanced Dependency Patterns

### Conditional Dependencies
```bash
# Service with conditional requirements
[Unit]
Description=Application Service
Wants=network-online.target
After=network-online.target

# Conditional dependencies based on system state
ConditionPathExists=/etc/app/enabled
ConditionHost=!development-server

# Runtime dependencies
Wants=redis.service
After=redis.service
```

### Backup Service Dependencies
```bash
# Backup service that conflicts with maintenance
[Unit]
Description=Database Backup Service
Requires=postgresql.service
After=postgresql.service
Conflicts=maintenance.service  # Cannot run during maintenance
Wants=network-online.target
After=network-online.target

[Service]
Type=oneshot
ExecStart=/usr/local/bin/backup-database.sh
```

### High Availability Dependencies
```bash
# Primary service
[Unit]
Description=Primary Application Server
Conflicts=secondary-app.service
Wants=shared-storage.mount
After=shared-storage.mount

# Secondary service (failover)
[Unit]
Description=Secondary Application Server
Conflicts=primary-app.service
Wants=shared-storage.mount
After=shared-storage.mount
```

## Target Dependencies

### Custom Target with Dependencies
```bash
# /etc/systemd/system/web-stack.target
[Unit]
Description=Complete Web Stack
Documentation=https://company.com/docs/deployment
Requires=postgresql.service redis.service
Wants=nginx.service webapp.service
After=postgresql.service redis.service nginx.service webapp.service
AllowIsolate=yes

[Install]
WantedBy=multi-user.target
```

### Development Environment Target
```bash
# /etc/systemd/system/dev-environment.target
[Unit]
Description=Development Environment
Requires=multi-user.target
After=multi-user.target
Wants=postgresql.service redis.service docker.service
After=postgresql.service redis.service docker.service

[Install]
WantedBy=multi-user.target
```

## Dependency Analysis

### Viewing Dependencies
```bash
# Show service dependencies
systemctl list-dependencies service_name
systemctl list-dependencies --reverse service_name
systemctl list-dependencies --all service_name

# Show specific dependency properties
systemctl show service_name --property=Requires
systemctl show service_name --property=Wants
systemctl show service_name --property=After
systemctl show service_name --property=Before
systemctl show service_name --property=Conflicts
```

### Dependency Visualization
```bash
# Generate dependency graph
systemd-analyze dot service_name.service | dot -Tsvg > deps.svg
systemd-analyze dot | dot -Tpng > system-deps.png

# Critical path analysis
systemd-analyze critical-chain service_name
systemd-analyze critical-chain
```

### Dependency Debugging
```bash
# Check failed dependencies
systemctl list-dependencies service_name --failed
systemctl --failed

# Verify dependency states
systemctl is-active dependency.service
systemctl is-enabled dependency.service
systemctl status dependency.service
```

## Complex Dependency Scenarios

### Database Cluster Dependencies
```bash
# PostgreSQL Primary
[Unit]
Description=PostgreSQL Primary
Conflicts=postgresql-standby.service
Wants=shared-storage.mount
After=shared-storage.mount

# PostgreSQL Standby
[Unit]
Description=PostgreSQL Standby
Conflicts=postgresql-primary.service
Requires=postgresql-primary.service
After=postgresql-primary.service
```

### Container Orchestration Dependencies
```bash
# Docker daemon
[Unit]
Description=Docker Engine
Requires=network.target docker.socket
After=network.target docker.socket

# Container service
[Unit]
Description=Application Container
Requires=docker.service
After=docker.service
PartOf=container-stack.target

[Service]
Type=forking
ExecStart=/usr/bin/docker run --name myapp myapp:latest
ExecStop=/usr/bin/docker stop myapp
```

### Message Queue Dependencies
```bash
# Message broker
[Unit]
Description=RabbitMQ Message Broker
Wants=network-online.target
After=network-online.target

# Publisher service
[Unit]
Description=Message Publisher
Requires=rabbitmq.service
After=rabbitmq.service
PartOf=messaging.target

# Consumer service
[Unit]
Description=Message Consumer
Requires=rabbitmq.service application.service
After=rabbitmq.service application.service
```

## Dependency Best Practices

### Production Service Template
```bash
# /etc/systemd/system/production-app.service
[Unit]
Description=Production Application
Documentation=https://company.com/docs/app

# Network dependencies
Wants=network-online.target
After=network-online.target

# Service dependencies
Requires=postgresql.service redis.service
After=postgresql.service redis.service

# Optional dependencies
Wants=monitoring.service
After=monitoring.service

# Startup constraints
StartLimitBurst=3
StartLimitIntervalSec=300

[Service]
Type=notify
ExecStart=/usr/local/bin/production-app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Dependency Health Check
```bash
#!/bin/bash
# dependency-check.sh

SERVICE="$1"

echo "=== Dependency Analysis for $SERVICE ==="

echo "Required dependencies:"
systemctl show "$SERVICE" --property=Requires --value

echo "Wanted dependencies:"
systemctl show "$SERVICE" --property=Wants --value

echo "Dependency status:"
systemctl list-dependencies "$SERVICE" --no-pager

echo "Failed dependencies:"
systemctl list-dependencies "$SERVICE" --failed --no-pager

echo "Reverse dependencies (what depends on this service):"
systemctl list-dependencies --reverse "$SERVICE" --no-pager
```

## Circular Dependency Resolution

### Detecting Circular Dependencies
```bash
# Check for circular dependencies
systemd-analyze verify service_name.service

# Manual detection
systemctl list-dependencies service1 | grep service2
systemctl list-dependencies service2 | grep service1
```

### Breaking Circular Dependencies
```bash
# Use socket activation to break cycles
# Instead of: A requires B, B requires A
# Use: A requires B.socket, B.socket starts B

# Service A
[Unit]
Requires=serviceB.socket
After=serviceB.socket

# Service B socket
[Unit]
PartOf=serviceB.service

[Socket]
ListenStream=8080

# Service B
[Unit]
Requires=serviceA.service
After=serviceA.service
```

## Emergency Dependency Handling

### Dependency Override
```bash
# Temporarily ignore dependencies
systemctl --no-deps start service_name

# Start service in isolation
systemctl isolate service_name.service

# Emergency dependency bypass
systemctl edit service_name.service
# Add: [Unit] section with modified dependencies
```

### Dependency Recovery Script
```bash
#!/bin/bash
# dependency-recovery.sh

FAILED_SERVICE="$1"

echo "Recovering dependencies for $FAILED_SERVICE"

# Stop failed service
systemctl stop "$FAILED_SERVICE"

# Check and restart dependencies
DEPS=$(systemctl show "$FAILED_SERVICE" --property=Requires --value)
for dep in $DEPS; do
    echo "Checking dependency: $dep"
    if ! systemctl is-active --quiet "$dep"; then
        echo "Restarting failed dependency: $dep"
        systemctl restart "$dep"
    fi
done

# Restart original service
systemctl start "$FAILED_SERVICE"
systemctl status "$FAILED_SERVICE"
```