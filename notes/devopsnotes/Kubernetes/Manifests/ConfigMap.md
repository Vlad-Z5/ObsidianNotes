# ConfigMap Manifest

## Overview

A **ConfigMap** is a Kubernetes object used to store non-confidential configuration data in key-value pairs. ConfigMaps decouple configuration from container images, making applications more portable and easier to manage across different environments.

**API Version:** `v1`
**Kind:** `ConfigMap`
**Scope:** Namespaced

## When to Use ConfigMap

### Ideal Use Cases

- Application configuration files (properties, YAML, JSON, XML, TOML)
- Environment-specific variables
- Command-line arguments
- Runtime configuration settings
- Feature flags and kill switches
- API endpoints, URLs, and service discovery
- Database connection strings (non-sensitive)
- Logging and monitoring configurations
- Caching and performance tuning parameters
- CI/CD pipeline configurations
- Application behavior toggles
- Regional and localization settings
- Third-party integration configs (non-sensitive)

### When NOT to Use ConfigMap

**Use Secrets instead for:**
- Passwords, passphrases
- API keys, tokens, authentication credentials
- TLS certificates and private keys
- SSH keys and credentials
- OAuth tokens and client secrets
- Database passwords
- Encryption keys
- Any sensitive, confidential, or security-critical data

**Use PersistentVolumes for:**
- Large files (>1MB)
- Binary data, media files
- Application artifacts
- Data that changes frequently
- User-generated content

## Basic ConfigMap Structure

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
  namespace: default
data:
  # Simple key-value pairs
  database.host: "postgres.example.com"
  database.port: "5432"
  log.level: "info"
  cache.ttl: "3600"
```

## Complete ConfigMap with All Options

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: comprehensive-config
  namespace: production

  labels:
    app: myapp
    component: backend
    environment: production
    version: v2.1.0
    team: platform
    managed-by: helm

  annotations:
    description: "Comprehensive application configuration"
    owner: "platform-team@company.com"
    config.kubernetes.io/local-config: "true"
    config.reloader.stakater.com/match: "true"
    kubectl.kubernetes.io/last-applied-configuration: |
      {}

data:
  # ==================== Simple Key-Value Pairs ====================
  ENVIRONMENT: "production"
  LOG_LEVEL: "info"
  LOG_FORMAT: "json"
  DEBUG: "false"
  MAX_CONNECTIONS: "100"
  TIMEOUT: "30s"
  RETRY_COUNT: "3"
  RETRY_DELAY: "1s"

  # ==================== URLs and Endpoints ====================
  API_URL: "https://api.example.com"
  API_VERSION: "v2"
  DATABASE_URL: "postgresql://postgres:5432/mydb"
  REDIS_URL: "redis://redis-service:6379"
  REDIS_DB: "0"
  KAFKA_BROKERS: "kafka-1:9092,kafka-2:9092,kafka-3:9092"
  ELASTICSEARCH_URL: "http://elasticsearch:9200"
  RABBITMQ_URL: "amqp://rabbitmq:5672"
  MONGODB_URL: "mongodb://mongodb:27017/mydb"

  # ==================== Feature Flags ====================
  FEATURE_NEW_UI: "true"
  FEATURE_BETA_API: "false"
  FEATURE_EXPERIMENTAL: "false"
  FEATURE_DARK_MODE: "true"
  FEATURE_ANALYTICS: "true"
  FEATURE_A_B_TESTING: "true"

  # ==================== Rate Limiting ====================
  RATE_LIMIT_REQUESTS: "1000"
  RATE_LIMIT_WINDOW: "60s"
  RATE_LIMIT_BURST: "50"

  # ==================== Cache Configuration ====================
  CACHE_ENABLED: "true"
  CACHE_TTL: "3600"
  CACHE_MAX_SIZE: "1000"
  CACHE_EVICTION_POLICY: "lru"

  # ==================== Metrics and Observability ====================
  METRICS_ENABLED: "true"
  METRICS_PORT: "9090"
  METRICS_PATH: "/metrics"
  TRACING_ENABLED: "true"
  TRACING_SAMPLE_RATE: "0.1"
  JAEGER_ENDPOINT: "http://jaeger:14268/api/traces"

  # ==================== Application Properties (Spring Boot) ====================
  application.properties: |
    # Spring Boot Configuration
    spring.application.name=order-service
    spring.profiles.active=production

    # Server Configuration
    server.port=8080
    server.address=0.0.0.0
    server.shutdown=graceful
    server.tomcat.max-threads=200
    server.tomcat.min-spare-threads=10
    server.tomcat.accept-count=100
    server.tomcat.max-connections=10000
    server.compression.enabled=true
    server.compression.mime-types=application/json,application/xml,text/html,text/xml,text/plain
    spring.lifecycle.timeout-per-shutdown-phase=30s

    # Database Configuration
    spring.datasource.url=jdbc:postgresql://postgres:5432/orders
    spring.datasource.driver-class-name=org.postgresql.Driver
    spring.datasource.hikari.maximum-pool-size=20
    spring.datasource.hikari.minimum-idle=5
    spring.datasource.hikari.connection-timeout=30000
    spring.datasource.hikari.idle-timeout=600000
    spring.datasource.hikari.max-lifetime=1800000

    # JPA/Hibernate
    spring.jpa.hibernate.ddl-auto=validate
    spring.jpa.show-sql=false
    spring.jpa.properties.hibernate.dialect=org.hibernate.dialect.PostgreSQLDialect
    spring.jpa.properties.hibernate.format_sql=false
    spring.jpa.properties.hibernate.use_sql_comments=false
    spring.jpa.properties.hibernate.jdbc.batch_size=20
    spring.jpa.properties.hibernate.order_inserts=true
    spring.jpa.properties.hibernate.order_updates=true

    # Redis Cache
    spring.cache.type=redis
    spring.redis.host=redis-service
    spring.redis.port=6379
    spring.redis.timeout=2000
    spring.redis.lettuce.pool.max-active=8
    spring.redis.lettuce.pool.max-idle=8
    spring.redis.lettuce.pool.min-idle=0

    # Kafka
    spring.kafka.bootstrap-servers=kafka-1:9092,kafka-2:9092
    spring.kafka.consumer.group-id=order-service
    spring.kafka.consumer.auto-offset-reset=earliest
    spring.kafka.producer.acks=all
    spring.kafka.producer.retries=3

    # Actuator
    management.endpoints.web.exposure.include=health,info,metrics,prometheus
    management.endpoint.health.show-details=always
    management.metrics.export.prometheus.enabled=true
    management.metrics.tags.application=${spring.application.name}
    management.metrics.tags.environment=production

    # Logging
    logging.level.root=INFO
    logging.level.com.company=DEBUG
    logging.level.org.springframework.web=INFO
    logging.level.org.hibernate.SQL=DEBUG
    logging.pattern.console=%d{yyyy-MM-dd HH:mm:ss} - %msg%n
    logging.pattern.file=%d{yyyy-MM-dd HH:mm:ss} [%thread] %-5level %logger{36} - %msg%n

  # ==================== JSON Configuration ====================
  config.json: |
    {
      "server": {
        "host": "0.0.0.0",
        "port": 8080,
        "timeout": 30,
        "keepAliveTimeout": 65,
        "maxConnections": 1000,
        "compression": {
          "enabled": true,
          "level": 6,
          "types": ["application/json", "text/html", "text/css"]
        }
      },
      "database": {
        "host": "postgres",
        "port": 5432,
        "database": "mydb",
        "maxConnections": 100,
        "minConnections": 10,
        "connectionTimeout": 30,
        "idleTimeout": 600,
        "statementTimeout": 30
      },
      "redis": {
        "host": "redis-service",
        "port": 6379,
        "db": 0,
        "maxRetries": 3,
        "retryDelay": 1000,
        "connectTimeout": 5000,
        "commandTimeout": 5000
      },
      "logging": {
        "level": "info",
        "format": "json",
        "outputs": ["stdout", "file"],
        "file": {
          "path": "/var/log/app.log",
          "maxSize": "100MB",
          "maxBackups": 10,
          "maxAge": 30,
          "compress": true
        }
      },
      "metrics": {
        "enabled": true,
        "port": 9090,
        "path": "/metrics",
        "interval": 15
      },
      "tracing": {
        "enabled": true,
        "serviceName": "myapp",
        "samplingRate": 0.1,
        "endpoint": "http://jaeger:14268/api/traces"
      },
      "rateLimit": {
        "enabled": true,
        "maxRequests": 1000,
        "windowSize": 60,
        "burst": 50
      },
      "cors": {
        "enabled": true,
        "allowedOrigins": ["https://example.com", "https://www.example.com"],
        "allowedMethods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allowedHeaders": ["Content-Type", "Authorization"],
        "allowCredentials": true,
        "maxAge": 3600
      }
    }

  # ==================== YAML Configuration ====================
  config.yaml: |
    server:
      host: 0.0.0.0
      port: 8080
      timeout: 30s
      gracefulShutdown: 30s

    database:
      host: postgres
      port: 5432
      database: mydb
      maxConnections: 100
      minConnections: 10
      connectionTimeout: 30s
      pool:
        maxIdleTime: 10m
        maxLifetime: 30m
        healthCheckInterval: 30s

    cache:
      enabled: true
      type: redis
      ttl: 1h
      maxSize: 10000
      evictionPolicy: lru
      redis:
        host: redis-service
        port: 6379
        db: 0

    logging:
      level: info
      format: json
      outputs:
        - stdout
        - file
      file:
        path: /var/log/app.log
        maxSize: 100MB
        maxBackups: 10
        compress: true

    features:
      newUI: true
      betaAPI: false
      analytics: true
      darkMode: true

    security:
      cors:
        enabled: true
        allowedOrigins:
          - https://example.com
        allowedMethods:
          - GET
          - POST
        maxAge: 3600
      rateLimit:
        enabled: true
        requestsPerMinute: 1000
        burst: 50

  # ==================== XML Configuration ====================
  config.xml: |
    <?xml version="1.0" encoding="UTF-8"?>
    <configuration>
      <server>
        <host>0.0.0.0</host>
        <port>8080</port>
        <timeout>30</timeout>
      </server>
      <database>
        <host>postgres</host>
        <port>5432</port>
        <database>mydb</database>
        <maxConnections>100</maxConnections>
      </database>
      <logging>
        <level>info</level>
        <format>json</format>
      </logging>
      <features>
        <feature name="newUI" enabled="true"/>
        <feature name="betaAPI" enabled="false"/>
      </features>
    </configuration>

  # ==================== TOML Configuration ====================
  config.toml: |
    [server]
    host = "0.0.0.0"
    port = 8080
    timeout = "30s"
    maxConnections = 1000

    [database]
    host = "postgres"
    port = 5432
    database = "mydb"
    maxConnections = 100

    [cache]
    enabled = true
    ttl = "1h"
    maxSize = 10000

    [logging]
    level = "info"
    format = "json"

    [features]
    newUI = true
    betaAPI = false

  # ==================== INI Configuration ====================
  config.ini: |
    [server]
    host=0.0.0.0
    port=8080
    timeout=30

    [database]
    host=postgres
    port=5432
    database=mydb
    maxConnections=100

    [cache]
    enabled=true
    ttl=3600

    [logging]
    level=info
    format=json

  # ==================== Shell Script ====================
  init.sh: |
    #!/bin/bash
    set -euo pipefail

    echo "=== Application Initialization ==="
    echo "Environment: ${ENVIRONMENT:-unknown}"
    echo "Log level: ${LOG_LEVEL:-info}"
    echo "Timestamp: $(date -u +"%Y-%m-%dT%H:%M:%SZ")"

    # Wait for database
    echo "Waiting for database..."
    until nc -z postgres 5432; do
      echo "Database unavailable - sleeping"
      sleep 2
    done
    echo "Database is up!"

    # Wait for Redis
    echo "Waiting for Redis..."
    until nc -z redis-service 6379; do
      echo "Redis unavailable - sleeping"
      sleep 1
    done
    echo "Redis is up!"

    # Run database migrations
    if [ "${RUN_MIGRATIONS:-true}" = "true" ]; then
      echo "Running database migrations..."
      ./migrate.sh up
      echo "Migrations completed successfully"
    fi

    # Warm up cache
    if [ "${WARM_CACHE:-false}" = "true" ]; then
      echo "Warming up cache..."
      ./cache-warmup.sh
    fi

    echo "=== Initialization Complete ==="
    echo "Starting application..."
    exec "$@"

  # ==================== Nginx Configuration ====================
  nginx.conf: |
    user nginx;
    worker_processes auto;
    worker_rlimit_nofile 65535;
    error_log /var/log/nginx/error.log warn;
    pid /var/run/nginx.pid;

    events {
      worker_connections 2048;
      use epoll;
      multi_accept on;
    }

    http {
      include /etc/nginx/mime.types;
      default_type application/octet-stream;

      # Logging
      log_format json_combined escape=json
        '{'
          '"time_local":"$time_local",'
          '"remote_addr":"$remote_addr",'
          '"remote_user":"$remote_user",'
          '"request":"$request",'
          '"status":"$status",'
          '"body_bytes_sent":"$body_bytes_sent",'
          '"request_time":"$request_time",'
          '"upstream_response_time":"$upstream_response_time",'
          '"upstream_addr":"$upstream_addr",'
          '"http_referrer":"$http_referer",'
          '"http_user_agent":"$http_user_agent",'
          '"http_x_forwarded_for":"$http_x_forwarded_for"'
        '}';

      access_log /var/log/nginx/access.log json_combined;

      # Performance
      sendfile on;
      tcp_nopush on;
      tcp_nodelay on;
      keepalive_timeout 65;
      keepalive_requests 100;
      types_hash_max_size 2048;
      server_tokens off;

      # Buffers
      client_body_buffer_size 128k;
      client_max_body_size 20M;
      client_header_buffer_size 1k;
      large_client_header_buffers 4 16k;

      # Timeouts
      client_body_timeout 12;
      client_header_timeout 12;
      send_timeout 10;

      # Gzip Compression
      gzip on;
      gzip_vary on;
      gzip_proxied any;
      gzip_comp_level 6;
      gzip_min_length 1000;
      gzip_disable "msie6";
      gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/json
        application/javascript
        application/xml+rss
        application/rss+xml
        font/truetype
        font/opentype
        application/vnd.ms-fontobject
        image/svg+xml;

      # Rate limiting
      limit_req_zone $binary_remote_addr zone=api_limit:10m rate=100r/s;
      limit_conn_zone $binary_remote_addr zone=addr:10m;

      # Upstream backend
      upstream backend {
        least_conn;
        server backend-service:8080 max_fails=3 fail_timeout=30s weight=1;
        server backend-service:8081 max_fails=3 fail_timeout=30s weight=1 backup;
        keepalive 32;
        keepalive_requests 100;
        keepalive_timeout 60s;
      }

      # Cache
      proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=api_cache:10m max_size=1g inactive=60m use_temp_path=off;

      server {
        listen 80 default_server;
        listen [::]:80 default_server;
        server_name _;

        # Security headers
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-XSS-Protection "1; mode=block" always;
        add_header Referrer-Policy "no-referrer-when-downgrade" always;
        add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;

        # Health check
        location /health {
          access_log off;
          return 200 "healthy\n";
          add_header Content-Type text/plain;
        }

        # Metrics
        location /nginx_status {
          stub_status on;
          access_log off;
          allow 10.0.0.0/8;
          deny all;
        }

        # API endpoints
        location /api/ {
          limit_req zone=api_limit burst=20 nodelay;
          limit_conn addr 10;

          proxy_pass http://backend/;
          proxy_http_version 1.1;
          proxy_set_header Host $host;
          proxy_set_header X-Real-IP $remote_addr;
          proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
          proxy_set_header X-Forwarded-Proto $scheme;
          proxy_set_header X-Forwarded-Host $host;
          proxy_set_header X-Forwarded-Port $server_port;
          proxy_set_header Connection "";

          # Timeouts
          proxy_connect_timeout 30s;
          proxy_send_timeout 30s;
          proxy_read_timeout 30s;

          # Buffering
          proxy_buffering on;
          proxy_buffer_size 4k;
          proxy_buffers 8 4k;
          proxy_busy_buffers_size 8k;

          # Caching
          proxy_cache api_cache;
          proxy_cache_valid 200 302 10m;
          proxy_cache_valid 404 1m;
          proxy_cache_use_stale error timeout updating http_500 http_502 http_503 http_504;
          proxy_cache_background_update on;
          proxy_cache_lock on;
          add_header X-Cache-Status $upstream_cache_status;
        }

        # WebSocket support
        location /ws/ {
          proxy_pass http://backend/;
          proxy_http_version 1.1;
          proxy_set_header Upgrade $http_upgrade;
          proxy_set_header Connection "upgrade";
          proxy_set_header Host $host;
          proxy_set_header X-Real-IP $remote_addr;
          proxy_read_timeout 86400;
        }

        # Static files
        location / {
          root /usr/share/nginx/html;
          try_files $uri $uri/ /index.html;
          expires 1d;
          add_header Cache-Control "public, immutable";
        }

        # Assets with cache busting
        location ~* \.(jpg|jpeg|png|gif|ico|css|js|svg|woff|woff2|ttf|eot)$ {
          root /usr/share/nginx/html;
          expires 1y;
          add_header Cache-Control "public, immutable";
          access_log off;
        }
      }
    }

  # ==================== Apache Configuration ====================
  httpd.conf: |
    ServerRoot "/usr/local/apache2"
    Listen 80

    LoadModule mpm_event_module modules/mod_mpm_event.so
    LoadModule authn_file_module modules/mod_authn_file.so
    LoadModule authn_core_module modules/mod_authn_core.so
    LoadModule authz_host_module modules/mod_authz_host.so
    LoadModule authz_groupfile_module modules/mod_authz_groupfile.so
    LoadModule authz_user_module modules/mod_authz_user.so
    LoadModule authz_core_module modules/mod_authz_core.so
    LoadModule access_compat_module modules/mod_access_compat.so
    LoadModule auth_basic_module modules/mod_auth_basic.so
    LoadModule reqtimeout_module modules/mod_reqtimeout.so
    LoadModule filter_module modules/mod_filter.so
    LoadModule mime_module modules/mod_mime.so
    LoadModule log_config_module modules/mod_log_config.so
    LoadModule env_module modules/mod_env.so
    LoadModule headers_module modules/mod_headers.so
    LoadModule setenvif_module modules/mod_setenvif.so
    LoadModule version_module modules/mod_version.so
    LoadModule proxy_module modules/mod_proxy.so
    LoadModule proxy_http_module modules/mod_proxy_http.so
    LoadModule unixd_module modules/mod_unixd.so
    LoadModule status_module modules/mod_status.so
    LoadModule autoindex_module modules/mod_autoindex.so
    LoadModule dir_module modules/mod_dir.so
    LoadModule alias_module modules/mod_alias.so
    LoadModule rewrite_module modules/mod_rewrite.so

    <IfModule unixd_module>
      User daemon
      Group daemon
    </IfModule>

    ServerAdmin you@example.com
    ServerName localhost

    <Directory />
      AllowOverride none
      Require all denied
    </Directory>

    DocumentRoot "/usr/local/apache2/htdocs"
    <Directory "/usr/local/apache2/htdocs">
      Options Indexes FollowSymLinks
      AllowOverride None
      Require all granted
    </Directory>

    <IfModule dir_module>
      DirectoryIndex index.html
    </IfModule>

    <Files ".ht*">
      Require all denied
    </Files>

    ErrorLog /proc/self/fd/2
    LogLevel warn

    <IfModule log_config_module>
      LogFormat "%h %l %u %t \"%r\" %>s %b \"%{Referer}i\" \"%{User-Agent}i\"" combined
      LogFormat "%h %l %u %t \"%r\" %>s %b" common
      CustomLog /proc/self/fd/1 common
    </IfModule>

    <IfModule headers_module>
      RequestHeader unset Proxy early
    </IfModule>

    <IfModule proxy_module>
      ProxyPreserveHost On
      ProxyPass /api http://backend-service:8080/api
      ProxyPassReverse /api http://backend-service:8080/api
    </IfModule>

  # ==================== Logstash Configuration ====================
  logstash.conf: |
    input {
      beats {
        port => 5044
      }

      http {
        port => 8080
        codec => json
      }

      kafka {
        bootstrap_servers => "kafka-1:9092,kafka-2:9092"
        topics => ["application-logs"]
        group_id => "logstash"
        codec => json
      }
    }

    filter {
      if [type] == "application" {
        json {
          source => "message"
        }

        date {
          match => ["timestamp", "ISO8601"]
          target => "@timestamp"
        }

        mutate {
          add_field => {
            "environment" => "production"
            "cluster" => "us-east-1"
          }
        }

        grok {
          match => { "message" => "%{COMBINEDAPACHELOG}" }
        }
      }

      if [level] == "ERROR" {
        mutate {
          add_tag => ["error", "alert"]
        }
      }
    }

    output {
      elasticsearch {
        hosts => ["elasticsearch:9200"]
        index => "application-logs-%{+YYYY.MM.dd}"
        document_type => "_doc"
      }

      if "error" in [tags] {
        email {
          to => "ops@example.com"
          subject => "Application Error Alert"
          body => "Error detected: %{message}"
        }
      }
    }

  # ==================== Filebeat Configuration ====================
  filebeat.yml: |
    filebeat.inputs:
    - type: log
      enabled: true
      paths:
        - /var/log/app/*.log
      fields:
        app: myapp
        environment: production
      fields_under_root: true
      multiline.pattern: '^[0-9]{4}-[0-9]{2}-[0-9]{2}'
      multiline.negate: true
      multiline.match: after

    - type: docker
      containers.ids:
        - '*'
      processors:
        - add_docker_metadata: ~

    processors:
      - add_host_metadata: ~
      - add_cloud_metadata: ~
      - add_kubernetes_metadata:
          host: ${NODE_NAME}
          matchers:
            - logs_path:
                logs_path: "/var/log/containers/"

    output.elasticsearch:
      hosts: ["elasticsearch:9200"]
      index: "filebeat-%{[agent.version]}-%{+yyyy.MM.dd}"

    output.logstash:
      hosts: ["logstash:5044"]

    setup.kibana:
      host: "kibana:5601"

    logging.level: info
    logging.to_files: true
    logging.files:
      path: /var/log/filebeat
      name: filebeat
      keepfiles: 7
      permissions: 0644

  # ==================== Grafana Datasource Configuration ====================
  grafana-datasources.yaml: |
    apiVersion: 1

    datasources:
    - name: Prometheus
      type: prometheus
      access: proxy
      url: http://prometheus:9090
      isDefault: true
      editable: true
      jsonData:
        timeInterval: "15s"

    - name: Loki
      type: loki
      access: proxy
      url: http://loki:3100
      editable: true

    - name: Elasticsearch
      type: elasticsearch
      access: proxy
      url: http://elasticsearch:9200
      database: "application-logs-*"
      jsonData:
        timeField: "@timestamp"
        esVersion: 7
        logMessageField: message
        logLevelField: level

binaryData:
  # Binary data must be base64 encoded
  favicon.ico: AAABAAEAEBAAAAEAIABoBAAAFgAAACgAAAAQAAAAIAAAAAEAIAAAAAAAAAQAAAAAAAAAAAAAAAAAAAAAAA==

immutable: false  # Set to true to prevent updates (improves performance and consistency)
```

## Creating ConfigMaps

### Method 1: From Literal Values

```bash
# Create with single key-value
kubectl create configmap simple-config \
  --from-literal=env=production

# Create with multiple key-value pairs
kubectl create configmap app-config \
  --from-literal=database.host=postgres \
  --from-literal=database.port=5432 \
  --from-literal=log.level=info \
  --from-literal=max.connections=100

# Create with namespace
kubectl create configmap app-config \
  --from-literal=env=production \
  --namespace=production

# Dry-run to preview
kubectl create configmap app-config \
  --from-literal=env=production \
  --dry-run=client -o yaml

# Apply with labels
kubectl create configmap app-config \
  --from-literal=env=production \
  --dry-run=client -o yaml | \
  kubectl label --local -f - app=myapp version=v1 -o yaml | \
  kubectl apply -f -
```

### Method 2: From File

```bash
# Create from single file
kubectl create configmap nginx-config \
  --from-file=nginx.conf

# Create from single file with custom key name
kubectl create configmap nginx-config \
  --from-file=custom-nginx.conf=nginx.conf

# Create from multiple files
kubectl create configmap app-configs \
  --from-file=config.yaml \
  --from-file=config.json \
  --from-file=settings.ini \
  --from-file=app.properties

# Create from directory (all files in directory)
kubectl create configmap configs \
  --from-file=configs/

# Mix files and literals
kubectl create configmap mixed-config \
  --from-file=nginx.conf \
  --from-literal=environment=production
```

### Method 3: From Env File

```bash
# Create from .env file
kubectl create configmap app-env \
  --from-env-file=app.env

# Create from multiple env files
kubectl create configmap combined-env \
  --from-env-file=base.env \
  --from-env-file=production.env
```

**app.env:**
```bash
DATABASE_HOST=postgres
DATABASE_PORT=5432
DATABASE_NAME=mydb
LOG_LEVEL=info
DEBUG=false
MAX_CONNECTIONS=100
TIMEOUT=30
```

**production.env:**
```bash
ENVIRONMENT=production
API_URL=https://api.example.com
REDIS_URL=redis://redis:6379
KAFKA_BROKERS=kafka-1:9092,kafka-2:9092
```

### Method 4: From YAML Manifest

```bash
# Apply from file
kubectl apply -f configmap.yaml

# Create with server-side apply
kubectl apply -f configmap.yaml --server-side

# Replace if exists
kubectl replace -f configmap.yaml --force

# Create or update
kubectl apply -f configmap.yaml
```

### Method 5: From Generator (Kustomize)

**kustomization.yaml:**
```yaml
configMapGenerator:
- name: app-config
  literals:
  - environment=production
  - log.level=info
  files:
  - config.yaml
  - nginx.conf
  envs:
  - app.env
  options:
    labels:
      app: myapp
    annotations:
      version: v1

generatorOptions:
  disableNameSuffixHash: false  # Adds hash suffix for versioning
```

```bash
kubectl apply -k .
```

## Using ConfigMaps in Pods

### 1. As Environment Variables (Individual Keys)

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: app-pod
spec:
  containers:
  - name: app
    image: myapp:v1
    env:
    # Single key
    - name: DATABASE_HOST
      valueFrom:
        configMapKeyRef:
          name: app-config
          key: database.host

    # With optional flag
    - name: DATABASE_PORT
      valueFrom:
        configMapKeyRef:
          name: app-config
          key: database.port
          optional: false  # Pod fails if key missing (default)

    # Optional key (pod continues if missing)
    - name: OPTIONAL_FEATURE
      valueFrom:
        configMapKeyRef:
          name: feature-flags
          key: experimental.feature
          optional: true  # Pod continues if key missing
```

### 2. As Environment Variables (All Keys)

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: app-pod
spec:
  containers:
  - name: app
    image: myapp:v1

    # Load all keys from ConfigMap
    envFrom:
    - configMapRef:
        name: app-config
        optional: false

    # Load with prefix
    - prefix: APP_
      configMapRef:
        name: feature-flags

    # Load from multiple ConfigMaps
    - configMapRef:
        name: base-config
    - configMapRef:
        name: env-config
    - prefix: FEATURE_
      configMapRef:
        name: feature-flags
        optional: true
```

**Result:**
```bash
# From app-config
DATABASE_HOST=postgres
DATABASE_PORT=5432

# From feature-flags (with prefix)
APP_FEATURE_NEW_UI=true
APP_FEATURE_BETA_API=false

# From base-config
TIMEOUT=30s
MAX_CONNECTIONS=100

# From env-config
ENVIRONMENT=production
LOG_LEVEL=info
```

### 3. As Volume Mount (Single File)

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: nginx-pod
spec:
  containers:
  - name: nginx
    image: nginx:1.25
    volumeMounts:
    # Mount single file
    - name: config
      mountPath: /etc/nginx/nginx.conf
      subPath: nginx.conf
      readOnly: true

    # Mount another file
    - name: config
      mountPath: /etc/nginx/conf.d/default.conf
      subPath: default.conf
      readOnly: true

  volumes:
  - name: config
    configMap:
      name: nginx-config
      items:
      - key: nginx.conf
        path: nginx.conf
        mode: 0644
      - key: default.conf
        path: default.conf
        mode: 0644
      defaultMode: 0644
```

### 4. As Volume Mount (All Keys as Files)

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: app-pod
spec:
  containers:
  - name: app
    image: myapp:v1
    volumeMounts:
    - name: config
      mountPath: /etc/config
      readOnly: true

  volumes:
  - name: config
    configMap:
      name: app-config
      defaultMode: 0644  # File permissions
```

**Result:**
```
/etc/config/
├── database.host        # Content: postgres
├── database.port        # Content: 5432
├── log.level           # Content: info
├── config.json         # Full JSON file
├── config.yaml         # Full YAML file
└── application.properties  # Full properties file
```

### 5. As Volume Mount (Selective Keys with Custom Paths)

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: app-pod
spec:
  containers:
  - name: app
    image: myapp:v1
    volumeMounts:
    - name: config
      mountPath: /config

  volumes:
  - name: config
    configMap:
      name: app-config
      items:
      # Map config.yaml to application.yaml
      - key: config.yaml
        path: application.yaml
        mode: 0644

      # Map config.json to settings.json
      - key: config.json
        path: settings.json
        mode: 0600  # More restrictive permissions

      # Map to subdirectory
      - key: nginx.conf
        path: nginx/nginx.conf
        mode: 0644
      defaultMode: 0644
```

**Result:**
```
/config/
├── application.yaml    # From config.yaml
├── settings.json      # From config.json
└── nginx/
    └── nginx.conf     # From nginx.conf
```

### 6. As Command Arguments

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: app-pod
spec:
  containers:
  - name: app
    image: myapp:v1
    command:
    - /app/server
    args:
    - --host=$(DATABASE_HOST)
    - --port=$(DATABASE_PORT)
    - --log-level=$(LOG_LEVEL)
    - --max-connections=$(MAX_CONNECTIONS)
    env:
    - name: DATABASE_HOST
      valueFrom:
        configMapKeyRef:
          name: app-config
          key: database.host
    - name: DATABASE_PORT
      valueFrom:
        configMapKeyRef:
          name: app-config
          key: database.port
    - name: LOG_LEVEL
      valueFrom:
        configMapKeyRef:
          name: app-config
          key: log.level
    - name: MAX_CONNECTIONS
      valueFrom:
        configMapKeyRef:
          name: app-config
          key: max.connections
```

### 7. Multiple ConfigMaps in Single Pod

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: multi-config-pod
spec:
  containers:
  - name: app
    image: myapp:v1

    # Environment variables from multiple ConfigMaps
    envFrom:
    - configMapRef:
        name: base-config
    - configMapRef:
        name: app-config
    - prefix: FEATURE_
      configMapRef:
        name: feature-flags

    # Volume mounts from multiple ConfigMaps
    volumeMounts:
    - name: app-config
      mountPath: /etc/app
      readOnly: true
    - name: nginx-config
      mountPath: /etc/nginx/nginx.conf
      subPath: nginx.conf
      readOnly: true
    - name: scripts
      mountPath: /scripts
      readOnly: false

  volumes:
  - name: app-config
    configMap:
      name: app-config
  - name: nginx-config
    configMap:
      name: nginx-config
  - name: scripts
    configMap:
      name: init-scripts
      defaultMode: 0755  # Executable
```

## Real-World Production Patterns

### 1. Node.js Application Configuration

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: nodejs-config
  namespace: production
  labels:
    app: nodejs-api
    environment: production
data:
  # Environment variables
  NODE_ENV: "production"
  PORT: "3000"
  LOG_LEVEL: "info"

  # Application config
  config.json: |
    {
      "server": {
        "port": 3000,
        "host": "0.0.0.0",
        "cors": {
          "enabled": true,
          "origin": ["https://example.com"],
          "credentials": true
        }
      },
      "database": {
        "client": "postgresql",
        "connection": {
          "host": "postgres",
          "port": 5432,
          "database": "myapp"
        },
        "pool": {
          "min": 2,
          "max": 10
        },
        "migrations": {
          "directory": "./migrations"
        }
      },
      "redis": {
        "host": "redis-service",
        "port": 6379,
        "db": 0,
        "keyPrefix": "myapp:"
      },
      "logging": {
        "level": "info",
        "format": "json",
        "console": true,
        "file": {
          "enabled": true,
          "path": "/var/log/app.log",
          "maxSize": "100m",
          "maxFiles": 10
        }
      },
      "security": {
        "rateLimit": {
          "windowMs": 900000,
          "max": 100
        },
        "helmet": {
          "enabled": true
        }
      }
    }

  # PM2 configuration
  ecosystem.config.js: |
    module.exports = {
      apps: [{
        name: 'api',
        script: './dist/server.js',
        instances: 'max',
        exec_mode: 'cluster',
        max_memory_restart: '1G',
        env: {
          NODE_ENV: 'production',
          PORT: 3000
        },
        error_file: '/var/log/pm2/err.log',
        out_file: '/var/log/pm2/out.log',
        log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
        merge_logs: true,
        autorestart: true,
        watch: false,
        max_restarts: 10,
        min_uptime: '10s'
      }]
    };

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nodejs-api
  namespace: production
spec:
  replicas: 3
  selector:
    matchLabels:
      app: nodejs-api
  template:
    metadata:
      labels:
        app: nodejs-api
    spec:
      containers:
      - name: api
        image: nodejs-api:v2.1.0
        ports:
        - containerPort: 3000
        envFrom:
        - configMapRef:
            name: nodejs-config
        volumeMounts:
        - name: config
          mountPath: /app/config
          readOnly: true
        - name: pm2-config
          mountPath: /app/ecosystem.config.js
          subPath: ecosystem.config.js
          readOnly: true
      volumes:
      - name: config
        configMap:
          name: nodejs-config
          items:
          - key: config.json
            path: config.json
      - name: pm2-config
        configMap:
          name: nodejs-config
```

### 2. Python Django/Flask Application

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: python-app-config
  namespace: production
data:
  # Django settings
  settings.py: |
    import os
    from pathlib import Path

    BASE_DIR = Path(__file__).resolve().parent.parent

    SECRET_KEY = os.getenv('SECRET_KEY')
    DEBUG = os.getenv('DEBUG', 'False') == 'True'
    ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '*').split(',')

    INSTALLED_APPS = [
        'django.contrib.admin',
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'django.contrib.messages',
        'django.contrib.staticfiles',
        'rest_framework',
        'corsheaders',
        'myapp',
    ]

    MIDDLEWARE = [
        'django.middleware.security.SecurityMiddleware',
        'whitenoise.middleware.WhiteNoiseMiddleware',
        'corsheaders.middleware.CorsMiddleware',
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.middleware.common.CommonMiddleware',
        'django.middleware.csrf.CsrfViewMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware',
        'django.contrib.messages.middleware.MessageMiddleware',
        'django.middleware.clickjacking.XFrameOptionsMiddleware',
    ]

    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.getenv('DB_NAME', 'mydb'),
            'USER': os.getenv('DB_USER', 'postgres'),
            'PASSWORD': os.getenv('DB_PASSWORD'),
            'HOST': os.getenv('DB_HOST', 'postgres'),
            'PORT': os.getenv('DB_PORT', '5432'),
            'CONN_MAX_AGE': 600,
            'OPTIONS': {
                'connect_timeout': 10,
            }
        }
    }

    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': os.getenv('REDIS_URL', 'redis://redis:6379/0'),
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                'CONNECTION_POOL_KWARGS': {'max_connections': 50}
            }
        }
    }

    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'verbose': {
                'format': '{levelname} {asctime} {module} {message}',
                'style': '{',
            },
            'json': {
                '()': 'pythonjsonlogger.jsonlogger.JsonFormatter',
                'format': '%(asctime)s %(name)s %(levelname)s %(message)s'
            }
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'formatter': 'json',
            },
        },
        'root': {
            'handlers': ['console'],
            'level': os.getenv('LOG_LEVEL', 'INFO'),
        },
    }

    # CORS
    CORS_ALLOWED_ORIGINS = os.getenv('CORS_ORIGINS', '').split(',')
    CORS_ALLOW_CREDENTIALS = True

    # Security
    SECURE_SSL_REDIRECT = not DEBUG
    SESSION_COOKIE_SECURE = not DEBUG
    CSRF_COOKIE_SECURE = not DEBUG
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'

  # uWSGI configuration
  uwsgi.ini: |
    [uwsgi]
    module = myapp.wsgi:application
    master = true
    processes = 4
    threads = 2
    socket = :8000
    chmod-socket = 666
    vacuum = true
    die-on-term = true
    harakiri = 30
    max-requests = 5000
    buffer-size = 32768

    # Logging
    log-format = %(addr) - %(user) [%(ltime)] "%(method) %(uri) %(proto)" %(status) %(size) "%(referer)" "%(uagent)"
    logto = /var/log/uwsgi/uwsgi.log
    log-maxsize = 100000000
    log-backupname = /var/log/uwsgi/uwsgi.log.old

    # Performance
    lazy-apps = true
    single-interpreter = true
    need-app = true

    # Health check
    stats = :9191
    stats-http = true

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: python-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: python-app
  template:
    metadata:
      labels:
        app: python-app
    spec:
      containers:
      - name: app
        image: python-app:v1.0.0
        env:
        - name: DJANGO_SETTINGS_MODULE
          value: "myapp.settings"
        envFrom:
        - configMapRef:
            name: python-app-config
        volumeMounts:
        - name: config
          mountPath: /app/myapp/settings.py
          subPath: settings.py
        - name: uwsgi-config
          mountPath: /etc/uwsgi/uwsgi.ini
          subPath: uwsgi.ini
      volumes:
      - name: config
        configMap:
          name: python-app-config
      - name: uwsgi-config
        configMap:
          name: python-app-config
```

### 3. Java Spring Boot Microservice

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: spring-boot-config
  namespace: production
  labels:
    app: order-service
    component: backend
data:
  application.yml: |
    spring:
      application:
        name: order-service
      profiles:
        active: production

      datasource:
        url: jdbc:postgresql://postgres:5432/orders
        username: ${DB_USER}
        password: ${DB_PASSWORD}
        driver-class-name: org.postgresql.Driver
        hikari:
          maximum-pool-size: 20
          minimum-idle: 5
          connection-timeout: 30000
          idle-timeout: 600000
          max-lifetime: 1800000
          pool-name: OrderServicePool
          auto-commit: true

      jpa:
        hibernate:
          ddl-auto: validate
          naming:
            physical-strategy: org.hibernate.boot.model.naming.PhysicalNamingStrategyStandardImpl
        show-sql: false
        properties:
          hibernate:
            dialect: org.hibernate.dialect.PostgreSQLDialect
            format_sql: false
            jdbc:
              batch_size: 20
              fetch_size: 50
            order_inserts: true
            order_updates: true
            query:
              in_clause_parameter_padding: true

      cache:
        type: redis
        redis:
          time-to-live: 3600000
          key-prefix: "order-service:"

      redis:
        host: redis-service
        port: 6379
        timeout: 2000ms
        lettuce:
          pool:
            max-active: 8
            max-idle: 8
            min-idle: 2
            max-wait: -1ms
          shutdown-timeout: 100ms

      kafka:
        bootstrap-servers: kafka-1:9092,kafka-2:9092,kafka-3:9092
        consumer:
          group-id: order-service-group
          auto-offset-reset: earliest
          enable-auto-commit: false
          key-deserializer: org.apache.kafka.common.serialization.StringDeserializer
          value-deserializer: org.springframework.kafka.support.serializer.JsonDeserializer
          properties:
            spring.json.trusted.packages: "*"
        producer:
          acks: all
          retries: 3
          key-serializer: org.apache.kafka.common.serialization.StringSerializer
          value-serializer: org.springframework.kafka.support.serializer.JsonSerializer
          properties:
            max.in.flight.requests.per.connection: 5
            enable.idempotence: true
        listener:
          ack-mode: manual
          concurrency: 3

    server:
      port: 8080
      shutdown: graceful
      compression:
        enabled: true
        mime-types: application/json,application/xml,text/html,text/xml,text/plain
        min-response-size: 1024
      tomcat:
        threads:
          max: 200
          min-spare: 10
        max-connections: 10000
        accept-count: 100
        connection-timeout: 20000

    management:
      endpoints:
        web:
          exposure:
            include: health,info,metrics,prometheus
          base-path: /actuator
      endpoint:
        health:
          show-details: always
          probes:
            enabled: true
      metrics:
        export:
          prometheus:
            enabled: true
        tags:
          application: ${spring.application.name}
          environment: production
        distribution:
          percentiles-histogram:
            http.server.requests: true
          slo:
            http.server.requests: 50ms,100ms,200ms,500ms,1s,2s
      health:
        livenessstate:
          enabled: true
        readinessstate:
          enabled: true

    logging:
      level:
        root: INFO
        com.company: DEBUG
        org.springframework.web: INFO
        org.springframework.security: INFO
        org.hibernate.SQL: DEBUG
        org.hibernate.type.descriptor.sql.BasicBinder: TRACE
      pattern:
        console: "%d{yyyy-MM-dd HH:mm:ss} - %msg%n"
        file: "%d{yyyy-MM-dd HH:mm:ss} [%thread] %-5level %logger{36} - %msg%n"
      file:
        name: /var/log/application.log
        max-size: 100MB
        max-history: 10
        total-size-cap: 1GB

    # Custom application properties
    app:
      security:
        jwt:
          expiration: 3600000
        cors:
          allowed-origins: https://example.com,https://www.example.com
          allowed-methods: GET,POST,PUT,DELETE,OPTIONS
          allowed-headers: "*"
          max-age: 3600
      features:
        new-ui-enabled: true
        beta-api-enabled: false
      rate-limit:
        requests-per-minute: 1000
        burst-capacity: 50

  logback-spring.xml: |
    <?xml version="1.0" encoding="UTF-8"?>
    <configuration>
      <include resource="org/springframework/boot/logging/logback/defaults.xml"/>

      <property name="LOG_FILE" value="${LOG_FILE:-${LOG_PATH:-${LOG_TEMP:-${java.io.tmpdir:-/tmp}}/}spring.log}"/>

      <appender name="CONSOLE" class="ch.qos.logback.core.ConsoleAppender">
        <encoder class="net.logstash.logback.encoder.LogstashEncoder">
          <customFields>{"app":"order-service","environment":"production"}</customFields>
        </encoder>
      </appender>

      <appender name="FILE" class="ch.qos.logback.core.rolling.RollingFileAppender">
        <file>${LOG_FILE}</file>
        <rollingPolicy class="ch.qos.logback.core.rolling.SizeAndTimeBasedRollingPolicy">
          <fileNamePattern>${LOG_FILE}.%d{yyyy-MM-dd}.%i.gz</fileNamePattern>
          <maxFileSize>100MB</maxFileSize>
          <maxHistory>30</maxHistory>
          <totalSizeCap>10GB</totalSizeCap>
        </rollingPolicy>
        <encoder class="net.logstash.logback.encoder.LogstashEncoder"/>
      </appender>

      <root level="INFO">
        <appender-ref ref="CONSOLE"/>
        <appender-ref ref="FILE"/>
      </root>
    </configuration>

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: order-service
  namespace: production
spec:
  replicas: 3
  selector:
    matchLabels:
      app: order-service
  template:
    metadata:
      labels:
        app: order-service
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8080"
        prometheus.io/path: "/actuator/prometheus"
    spec:
      containers:
      - name: app
        image: order-service:v2.1.0
        ports:
        - name: http
          containerPort: 8080
        - name: actuator
          containerPort: 8080
        env:
        - name: SPRING_CONFIG_LOCATION
          value: "file:/config/application.yml"
        - name: LOGGING_CONFIG
          value: "file:/config/logback-spring.xml"
        envFrom:
        - configMapRef:
            name: spring-boot-env
        - secretRef:
            name: spring-boot-secrets
        volumeMounts:
        - name: config
          mountPath: /config
          readOnly: true
        livenessProbe:
          httpGet:
            path: /actuator/health/liveness
            port: 8080
          initialDelaySeconds: 60
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /actuator/health/readiness
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 5
      volumes:
      - name: config
        configMap:
          name: spring-boot-config
```

### 4. Go Microservice Configuration

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: go-service-config
  namespace: production
data:
  config.yaml: |
    server:
      host: 0.0.0.0
      port: 8080
      readTimeout: 30s
      writeTimeout: 30s
      idleTimeout: 60s
      shutdownTimeout: 30s

    database:
      driver: postgres
      host: postgres
      port: 5432
      database: mydb
      maxOpenConns: 25
      maxIdleConns: 25
      connMaxLifetime: 30m
      connMaxIdleTime: 10m

    redis:
      host: redis-service
      port: 6379
      db: 0
      poolSize: 10
      minIdleConns: 5
      maxRetries: 3
      dialTimeout: 5s
      readTimeout: 3s
      writeTimeout: 3s
      poolTimeout: 4s
      idleTimeout: 5m

    logging:
      level: info
      format: json
      output: stdout
      caller: true
      stacktrace: true

    metrics:
      enabled: true
      port: 9090
      path: /metrics

    tracing:
      enabled: true
      serviceName: go-service
      samplingRate: 0.1
      jaegerEndpoint: http://jaeger:14268/api/traces

    security:
      cors:
        allowedOrigins:
          - https://example.com
        allowedMethods:
          - GET
          - POST
          - PUT
          - DELETE
        allowedHeaders:
          - "*"
        allowCredentials: true
        maxAge: 3600
      rateLimit:
        enabled: true
        requestsPerSecond: 100
        burst: 200

  # Go environment file
  .env: |
    ENVIRONMENT=production
    LOG_LEVEL=info
    DEBUG=false
    GOMAXPROCS=4
    GOGC=100
    GOMEMLIMIT=1GiB

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: go-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: go-service
  template:
    metadata:
      labels:
        app: go-service
    spec:
      containers:
      - name: service
        image: go-service:v1.0.0
        env:
        - name: CONFIG_FILE
          value: /config/config.yaml
        envFrom:
        - configMapRef:
            name: go-service-config
        volumeMounts:
        - name: config
          mountPath: /config
          readOnly: true
      volumes:
      - name: config
        configMap:
          name: go-service-config
```

### 5. Kafka Configuration

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: kafka-config
  namespace: kafka
data:
  server.properties: |
    # Broker settings
    broker.id=0
    listeners=PLAINTEXT://:9092
    advertised.listeners=PLAINTEXT://kafka-0.kafka-headless.kafka.svc.cluster.local:9092
    listener.security.protocol.map=PLAINTEXT:PLAINTEXT
    inter.broker.listener.name=PLAINTEXT

    # ZooKeeper
    zookeeper.connect=zookeeper:2181
    zookeeper.connection.timeout.ms=18000

    # Log settings
    log.dirs=/var/lib/kafka/data
    num.partitions=3
    default.replication.factor=3
    min.insync.replicas=2
    auto.create.topics.enable=false
    delete.topic.enable=true

    # Log retention
    log.retention.hours=168
    log.retention.bytes=1073741824
    log.segment.bytes=1073741824
    log.retention.check.interval.ms=300000
    log.cleaner.enable=true
    log.cleanup.policy=delete

    # Performance
    num.network.threads=8
    num.io.threads=8
    socket.send.buffer.bytes=102400
    socket.receive.buffer.bytes=102400
    socket.request.max.bytes=104857600
    num.replica.fetchers=4
    replica.fetch.min.bytes=1
    replica.fetch.wait.max.ms=500
    replica.high.watermark.checkpoint.interval.ms=5000
    replica.socket.timeout.ms=30000
    replica.socket.receive.buffer.bytes=65536
    replica.lag.time.max.ms=30000

    # Group coordinator
    group.initial.rebalance.delay.ms=3000
    group.max.session.timeout.ms=300000
    group.min.session.timeout.ms=6000

    # Compression
    compression.type=producer

    # Metrics
    metric.reporters=
    auto.leader.rebalance.enable=true
    leader.imbalance.check.interval.seconds=300
    leader.imbalance.per.broker.percentage=10

    # Security
    authorizer.class.name=
    allow.everyone.if.no.acl.found=true
```

### 6. Elasticsearch Configuration

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: elasticsearch-config
  namespace: logging
data:
  elasticsearch.yml: |
    cluster.name: production-cluster
    node.name: ${HOSTNAME}
    node.master: true
    node.data: true
    node.ingest: true

    path.data: /usr/share/elasticsearch/data
    path.logs: /usr/share/elasticsearch/logs

    network.host: 0.0.0.0
    http.port: 9200
    transport.tcp.port: 9300

    discovery.seed_hosts:
      - elasticsearch-0.elasticsearch-headless
      - elasticsearch-1.elasticsearch-headless
      - elasticsearch-2.elasticsearch-headless
    cluster.initial_master_nodes:
      - elasticsearch-0
      - elasticsearch-1
      - elasticsearch-2

    bootstrap.memory_lock: true

    # Performance
    indices.memory.index_buffer_size: 30%
    indices.queries.cache.size: 10%
    indices.fielddata.cache.size: 20%
    thread_pool.write.queue_size: 1000
    thread_pool.search.queue_size: 1000

    # Security
    xpack.security.enabled: false
    xpack.monitoring.enabled: true
    xpack.ml.enabled: false

  jvm.options: |
    -Xms2g
    -Xmx2g
    -XX:+UseConcMarkSweepGC
    -XX:CMSInitiatingOccupancyFraction=75
    -XX:+UseCMSInitiatingOccupancyOnly
    -Djava.awt.headless=true
    -Dfile.encoding=UTF-8
    -Djna.nosys=true
    -XX:-OmitStackTraceInFastThrow
    -Dio.netty.noUnsafe=true
    -Dio.netty.noKeySetOptimization=true
    -Dio.netty.recycler.maxCapacityPerThread=0
    -Dlog4j.shutdownHookEnabled=false
    -Dlog4j2.disable.jmx=true
    -Djava.io.tmpdir=${ES_TMPDIR}
    -XX:+HeapDumpOnOutOfMemoryError
    -XX:HeapDumpPath=/usr/share/elasticsearch/logs
    -XX:ErrorFile=/usr/share/elasticsearch/logs/hs_err_pid%p.log
```

### 7. MongoDB Configuration

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: mongodb-config
  namespace: database
data:
  mongod.conf: |
    systemLog:
      destination: file
      path: /var/log/mongodb/mongod.log
      logAppend: true
      logRotate: reopen
      verbosity: 0

    storage:
      dbPath: /data/db
      journal:
        enabled: true
      engine: wiredTiger
      wiredTiger:
        engineConfig:
          cacheSizeGB: 2
          journalCompressor: snappy
        collectionConfig:
          blockCompressor: snappy
        indexConfig:
          prefixCompression: true

    processManagement:
      fork: false
      pidFilePath: /var/run/mongodb/mongod.pid
      timeZoneInfo: /usr/share/zoneinfo

    net:
      port: 27017
      bindIp: 0.0.0.0
      maxIncomingConnections: 1000
      wireObjectCheck: true
      ipv6: false

    security:
      authorization: enabled
      javascriptEnabled: false

    replication:
      replSetName: rs0
      oplogSizeMB: 1024

    setParameter:
      enableLocalhostAuthBypass: false

    operationProfiling:
      mode: slowOp
      slowOpThresholdMs: 100
```

### 8. Redis Configuration

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: redis-config
  namespace: cache
data:
  redis.conf: |
    # Network
    bind 0.0.0.0
    port 6379
    protected-mode no
    tcp-backlog 511
    timeout 0
    tcp-keepalive 300

    # General
    daemonize no
    supervised no
    pidfile /var/run/redis/redis.pid
    loglevel notice
    logfile ""
    databases 16

    # Snapshotting
    save 900 1
    save 300 10
    save 60 10000
    stop-writes-on-bgsave-error yes
    rdbcompression yes
    rdbchecksum yes
    dbfilename dump.rdb
    dir /data

    # Replication
    replica-serve-stale-data yes
    replica-read-only yes
    repl-diskless-sync no
    repl-diskless-sync-delay 5
    repl-disable-tcp-nodelay no
    replica-priority 100

    # Security
    requirepass ${REDIS_PASSWORD}
    rename-command CONFIG ""
    rename-command FLUSHDB ""
    rename-command FLUSHALL ""

    # Limits
    maxclients 10000
    maxmemory 2gb
    maxmemory-policy allkeys-lru
    maxmemory-samples 5

    # Append only mode
    appendonly yes
    appendfilename "appendonly.aof"
    appendfsync everysec
    no-appendfsync-on-rewrite no
    auto-aof-rewrite-percentage 100
    auto-aof-rewrite-min-size 64mb
    aof-load-truncated yes
    aof-use-rdb-preamble yes

    # Slow log
    slowlog-log-slower-than 10000
    slowlog-max-len 128

    # Latency monitor
    latency-monitor-threshold 100

    # Notifications
    notify-keyspace-events ""

    # Advanced
    hash-max-ziplist-entries 512
    hash-max-ziplist-value 64
    list-max-ziplist-size -2
    set-max-intset-entries 512
    zset-max-ziplist-entries 128
    zset-max-ziplist-value 64
    hll-sparse-max-bytes 3000
    stream-node-max-bytes 4096
    stream-node-max-entries 100
    activerehashing yes
    client-output-buffer-limit normal 0 0 0
    client-output-buffer-limit replica 256mb 64mb 60
    client-output-buffer-limit pubsub 32mb 8mb 60
    hz 10
    dynamic-hz yes
    aof-rewrite-incremental-fsync yes
    rdb-save-incremental-fsync yes
```

## ConfigMap Auto-Reload Patterns

### Using Reloader (stakater/reloader)

```yaml
# Install Reloader first
# helm repo add stakater https://stakater.github.io/stakater-charts
# helm install reloader stakater/reloader

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp
  namespace: production
  annotations:
    # Reload when these ConfigMaps change
    configmap.reloader.stakater.com/reload: "app-config,feature-flags,nginx-config"
    # Or reload on any ConfigMap change
    # reloader.stakater.com/auto: "true"
spec:
  replicas: 3
  selector:
    matchLabels:
      app: myapp
  template:
    metadata:
      labels:
        app: myapp
    spec:
      containers:
      - name: app
        image: myapp:v1
        envFrom:
        - configMapRef:
            name: app-config
        volumeMounts:
        - name: features
          mountPath: /config/features
        - name: nginx
          mountPath: /etc/nginx/nginx.conf
          subPath: nginx.conf
      volumes:
      - name: features
        configMap:
          name: feature-flags
      - name: nginx
        configMap:
          name: nginx-config
```

**How Reloader works:**
1. Watches ConfigMaps and Secrets for changes
2. Automatically triggers rolling restart of Deployments/StatefulSets
3. No code changes needed in your application
4. Supports annotations for fine-grained control

### Manual Checksum Annotation

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp
spec:
  replicas: 3
  selector:
    matchLabels:
      app: myapp
  template:
    metadata:
      labels:
        app: myapp
      annotations:
        # Checksum of ConfigMap - triggers restart when changed
        checksum/config: {{ include (print $.Template.BasePath "/configmap.yaml") . | sha256sum }}
    spec:
      containers:
      - name: app
        image: myapp:v1
        envFrom:
        - configMapRef:
            name: app-config
```

**Helm template function to calculate checksum:**
```bash
# Update ConfigMap
kubectl create configmap app-config \
  --from-file=config.yaml \
  --dry-run=client -o yaml | kubectl apply -f -

# Calculate checksum and update deployment annotation
CONFIG_HASH=$(kubectl get configmap app-config -o yaml | sha256sum | awk '{print $1}')
kubectl patch deployment myapp \
  -p "{\"spec\":{\"template\":{\"metadata\":{\"annotations\":{\"configmap-hash\":\"${CONFIG_HASH}\"}}}}}"
```

### Using Kustomize ConfigMap Generator

```yaml
# kustomization.yaml
configMapGenerator:
- name: app-config
  files:
  - config.yaml
  - nginx.conf
  options:
    disableNameSuffixHash: false  # Adds hash suffix

resources:
- deployment.yaml
```

**Result:**
```yaml
# Generated ConfigMap name with hash
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config-m8f2h7k9g5
data:
  config.yaml: |
    ...

---
# Deployment automatically references hashed name
apiVersion: apps/v1
kind: Deployment
spec:
  template:
    spec:
      volumes:
      - name: config
        configMap:
          name: app-config-m8f2h7k9g5
```

### Application-Level Hot Reload

**For applications that support config hot-reload:**

```go
// Go example using fsnotify
func WatchConfig(configPath string) {
    watcher, _ := fsnotify.NewWatcher()
    watcher.Add(configPath)

    for {
        select {
        case event := <-watcher.Events:
            if event.Op&fsnotify.Write == fsnotify.Write {
                log.Println("Config file modified, reloading...")
                loadConfig(configPath)
            }
        }
    }
}
```

```python
# Python example using watchdog
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class ConfigReloader(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path.endswith('config.yaml'):
            print("Config modified, reloading...")
            load_config(event.src_path)

observer = Observer()
observer.schedule(ConfigReloader(), path='/config', recursive=False)
observer.start()
```

## ConfigMap Limits and Best Practices

### Size Limits

**Hard Limits:**
- **Maximum size per ConfigMap:** 1 MiB (1,048,576 bytes)
- **Maximum total etcd database size:** Typically 2-8 GB (cluster dependent)
- **Recommended max keys per ConfigMap:** No hard limit, but keep under 100 for manageability

**Working with large configurations:**

```yaml
# BAD: Single large ConfigMap (>1MB)
apiVersion: v1
kind: ConfigMap
metadata:
  name: huge-config
data:
  large-file.json: |
    # 2MB of JSON data - WILL FAIL

---
# GOOD: Split into multiple ConfigMaps
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config-1
data:
  config.yaml: |
    # 500KB

---
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config-2
data:
  features.json: |
    # 500KB
```

### Best Practices

#### 1. Immutability for Stability

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config-v2.1.0
  labels:
    app: myapp
    version: v2.1.0
data:
  config.yaml: |
    ...
immutable: true  # Cannot be modified - must create new ConfigMap
```

**Benefits:**
- Prevents accidental updates
- Improves kube-apiserver performance (no watch needed)
- Forces versioning discipline
- Enables easy rollback

**Drawbacks:**
- Must create new ConfigMap for changes
- Must update Deployment to reference new ConfigMap
- More ConfigMaps to manage

#### 2. Versioning Strategies

**Strategy A: Version in name**
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config-v1
  labels:
    app: myapp
    config-version: "1"
```

**Strategy B: Git SHA in name**
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config-abc123f
  labels:
    git-sha: abc123f
```

**Strategy C: Semantic versioning**
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config-2.1.0
  labels:
    version: 2.1.0
```

**Strategy D: Kustomize hash suffix**
```yaml
# Automatically generated
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config-k4h7t8m9b2
```

#### 3. Separation of Concerns

```yaml
# Application settings
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
data:
  server.port: "8080"
  timeout: "30s"

# Feature flags
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: feature-flags
data:
  newUI: "true"
  betaAPI: "false"

# Database configuration
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: database-config
data:
  host: "postgres"
  port: "5432"

# Environment-specific
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: env-config
  namespace: production
data:
  environment: "production"
  logLevel: "info"
```

**Benefits:**
- Change one without affecting others
- Different update cycles
- Clearer organization
- Better RBAC control

#### 4. Use subPath to Avoid Overwriting

```yaml
# BAD: Overwrites entire directory
volumeMounts:
- name: config
  mountPath: /etc/nginx  # Replaces ALL files in /etc/nginx

---
# GOOD: Only replaces specific file
volumeMounts:
- name: config
  mountPath: /etc/nginx/nginx.conf
  subPath: nginx.conf  # Only this file
- name: config
  mountPath: /etc/nginx/conf.d/default.conf
  subPath: default.conf  # And this file
```

#### 5. Set readOnly for Security

```yaml
volumeMounts:
- name: config
  mountPath: /config
  readOnly: true  # Container cannot modify

- name: writable
  mountPath: /data
  readOnly: false  # Container can write
```

#### 6. Use Optional for Non-Critical Configs

```yaml
env:
- name: CRITICAL_CONFIG
  valueFrom:
    configMapKeyRef:
      name: app-config
      key: critical.setting
      optional: false  # Pod fails if missing

- name: OPTIONAL_FEATURE
  valueFrom:
    configMapKeyRef:
      name: feature-flags
      key: experimental
      optional: true  # Pod continues if missing
```

#### 7. Label Everything

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
  labels:
    app: myapp
    component: backend
    environment: production
    version: v2.1.0
    managed-by: helm
    team: platform
    cost-center: engineering
```

**Query by labels:**
```bash
kubectl get configmaps -l app=myapp
kubectl get configmaps -l environment=production
kubectl get configmaps -l team=platform
```

#### 8. Document with Annotations

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
  annotations:
    description: "Production application configuration"
    owner: "platform-team@company.com"
    docs: "https://docs.company.com/configs/app-config"
    last-updated: "2024-01-15"
    jira: "PLAT-1234"
    contact: "slack://platform-team"
```

## Kubectl Commands Reference

```bash
# ==================== Create ====================
# From literal
kubectl create configmap app-config \
  --from-literal=key1=value1 \
  --from-literal=key2=value2

# From file
kubectl create configmap nginx-config \
  --from-file=nginx.conf

# From file with custom key
kubectl create configmap nginx-config \
  --from-file=my-nginx.conf=nginx.conf

# From multiple files
kubectl create configmap configs \
  --from-file=config1.yaml \
  --from-file=config2.json \
  --from-file=settings.ini

# From directory
kubectl create configmap configs \
  --from-file=configs/

# From env file
kubectl create configmap env-config \
  --from-env-file=.env

# Mix everything
kubectl create configmap mixed-config \
  --from-file=nginx.conf \
  --from-literal=env=production \
  --from-env-file=.env

# With namespace and labels
kubectl create configmap app-config \
  --from-file=config.yaml \
  --namespace=production \
  --dry-run=client -o yaml | \
  kubectl label --local -f - app=myapp -o yaml | \
  kubectl apply -f -

# ==================== Read ====================
# List ConfigMaps
kubectl get configmaps
kubectl get cm
kubectl get cm -A  # All namespaces
kubectl get cm -n production
kubectl get cm --show-labels
kubectl get cm -l app=myapp

# Describe ConfigMap
kubectl describe cm app-config
kubectl describe cm app-config -n production

# View YAML
kubectl get cm app-config -o yaml
kubectl get cm app-config -o json

# View specific key
kubectl get cm app-config -o jsonpath='{.data.config\.yaml}'
kubectl get cm app-config -o jsonpath='{.data}' | jq .

# View all keys
kubectl get cm app-config -o jsonpath='{.data}' | jq 'keys'

# ==================== Update ====================
# Edit interactively
kubectl edit cm app-config

# Replace from file
kubectl create cm app-config \
  --from-file=config.yaml \
  --dry-run=client -o yaml | \
  kubectl replace -f -

# Patch specific key
kubectl patch cm app-config \
  -p '{"data":{"key1":"new-value"}}'

# Update from literal
kubectl create cm app-config \
  --from-literal=key1=value1 \
  --dry-run=client -o yaml | \
  kubectl apply -f -

# ==================== Delete ====================
# Delete single ConfigMap
kubectl delete cm app-config

# Delete multiple
kubectl delete cm config1 config2 config3

# Delete by label
kubectl delete cm -l app=myapp

# Delete all in namespace
kubectl delete cm --all -n development

# ==================== Export ====================
# Export to file
kubectl get cm app-config -o yaml > configmap.yaml

# Export without metadata
kubectl get cm app-config -o yaml \
  | yq eval 'del(.metadata.creationTimestamp, .metadata.resourceVersion, .metadata.selfLink, .metadata.uid)' - \
  > clean-configmap.yaml

# Export all ConfigMaps
kubectl get cm -o yaml > all-configmaps.yaml

# ==================== Debugging ====================
# Check which pods use ConfigMap
kubectl get pods -o json | \
  jq '.items[] | select(.spec.volumes[]?.configMap.name=="app-config") | .metadata.name'

# Check ConfigMap size
kubectl get cm app-config -o json | \
  jq '.data | to_entries | map(.value | length) | add'

# Watch ConfigMap changes
kubectl get cm app-config --watch

# ==================== Advanced ====================
# Dry-run and preview
kubectl create cm test --from-literal=key=value --dry-run=client -o yaml

# Server-side apply
kubectl apply -f configmap.yaml --server-side

# Force delete
kubectl delete cm app-config --force --grace-period=0

# Create with annotation
kubectl create cm app-config \
  --from-literal=key=value \
  --dry-run=client -o yaml | \
  kubectl annotate --local -f - description="My config" -o yaml | \
  kubectl apply -f -
```

## Troubleshooting

### ConfigMap Not Found

```bash
# Check if ConfigMap exists
kubectl get cm app-config

# Check namespace
kubectl get cm app-config -n production

# Check all namespaces
kubectl get cm app-config -A

# List all ConfigMaps
kubectl get cm -A | grep app-config
```

### ConfigMap Not Mounting

```bash
# 1. Check if ConfigMap exists
kubectl get cm app-config -o yaml

# 2. Check ConfigMap has data
kubectl describe cm app-config

# 3. Check pod events
kubectl describe pod <pod-name>

# 4. Check volume configuration
kubectl get pod <pod-name> -o yaml | grep -A 20 volumes

# 5. Check volume mounts
kubectl get pod <pod-name> -o yaml | grep -A 10 volumeMounts

# 6. Check inside pod
kubectl exec -it <pod-name> -- ls -la /config
kubectl exec -it <pod-name> -- cat /config/config.yaml

# 7. Check permissions
kubectl exec -it <pod-name> -- ls -la /config
```

### Environment Variables Not Set

```bash
# 1. Check pod environment
kubectl exec -it <pod-name> -- env | grep DATABASE

# 2. Check ConfigMap key exists
kubectl get cm app-config -o jsonpath='{.data}' | jq .

# 3. Check envFrom reference
kubectl get pod <pod-name> -o yaml | grep -A 5 envFrom

# 4. Check for typos in key names
kubectl describe cm app-config

# 5. Restart pod to pick up env vars
kubectl delete pod <pod-name>
```

### ConfigMap Too Large

```bash
# Check ConfigMap size
kubectl get cm app-config -o json | \
  jq '[.data | to_entries[] | {key: .key, size: (.value | length)}] | sort_by(.size) | reverse'

# Total size
kubectl get cm app-config -o json | \
  jq '.data | to_entries | map(.value | length) | add'

# If > 1MB, split into multiple ConfigMaps
```

### Changes Not Reflecting

```bash
# For environment variables: Pod restart required
kubectl rollout restart deployment myapp

# For volume mounts: Wait for kubelet sync (max 60s)
# Or force restart
kubectl delete pod -l app=myapp

# Check if ConfigMap is immutable
kubectl get cm app-config -o jsonpath='{.immutable}'

# If immutable, must create new ConfigMap
kubectl create cm app-config-v2 --from-file=config.yaml
```

### Permission Denied

```bash
# Check file permissions in pod
kubectl exec -it <pod-name> -- ls -la /config

# Check defaultMode in volume
kubectl get pod <pod-name> -o yaml | grep -A 5 defaultMode

# Update permissions
# In ConfigMap volume spec:
volumes:
- name: config
  configMap:
    name: app-config
    defaultMode: 0644  # or 0755 for executable
```

### Key Not Found

```bash
# Check exact key names
kubectl get cm app-config -o jsonpath='{.data}' | jq 'keys'

# Key names are case-sensitive
DATABASE_HOST != database_host

# Check for special characters
kubectl get cm app-config -o json | jq '.data | keys'
```

## Integration Patterns

### ConfigMap + Secret

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: app-with-config-and-secrets
spec:
  containers:
  - name: app
    image: myapp:v1

    # Mix ConfigMaps and Secrets
    envFrom:
    - configMapRef:
        name: app-config  # Non-sensitive config
    - secretRef:
        name: app-secrets  # Sensitive data

    volumeMounts:
    - name: config
      mountPath: /config
    - name: secrets
      mountPath: /secrets
      readOnly: true

  volumes:
  - name: config
    configMap:
      name: app-config
  - name: secrets
    secret:
      secretName: app-secrets
      defaultMode: 0400  # More restrictive
```

### ConfigMap + Helm

```yaml
# templates/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: {{ include "myapp.fullname" . }}
  labels:
    {{- include "myapp.labels" . | nindent 4 }}
data:
  config.yaml: |
    server:
      port: {{ .Values.server.port }}
      host: {{ .Values.server.host }}
    database:
      host: {{ .Values.database.host }}
      port: {{ .Values.database.port }}
    {{- if .Values.features.newUI }}
    features:
      newUI: {{ .Values.features.newUI }}
    {{- end }}

---
# values.yaml
server:
  port: 8080
  host: "0.0.0.0"

database:
  host: postgres
  port: 5432

features:
  newUI: true
```

### ConfigMap + Kustomize

```yaml
# base/kustomization.yaml
configMapGenerator:
- name: app-config
  files:
  - config.yaml
  literals:
  - environment=base

---
# overlays/production/kustomization.yaml
bases:
- ../../base

configMapGenerator:
- name: app-config
  behavior: merge
  literals:
  - environment=production
  - logLevel=warn

---
# overlays/development/kustomization.yaml
bases:
- ../../base

configMapGenerator:
- name: app-config
  behavior: merge
  literals:
  - environment=development
  - logLevel=debug
```

## References

- [Official ConfigMap Documentation](https://kubernetes.io/docs/concepts/configuration/configmap/)
- [Configure Pods with ConfigMaps](https://kubernetes.io/docs/tasks/configure-pod-container/configure-pod-configmap/)
- [Immutable ConfigMaps](https://kubernetes.io/docs/concepts/configuration/configmap/#configmap-immutable)
- [ConfigMap API Reference](https://kubernetes.io/docs/reference/kubernetes-api/config-and-storage-resources/config-map-v1/)
- [Stakater Reloader](https://github.com/stakater/Reloader)
- [Kustomize ConfigMap Generator](https://kubectl.docs.kubernetes.io/references/kustomize/kustomization/configmapgenerator/)
