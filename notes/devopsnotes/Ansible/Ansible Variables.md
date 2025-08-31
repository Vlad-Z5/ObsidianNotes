# Enterprise Ansible Variables Management

Advanced variable management patterns, dynamic data structures, and enterprise configuration strategies for scalable automation.

## Table of Contents
1. [Variable Precedence & Architecture](#variable-precedence--architecture)
2. [Advanced Variable Types](#advanced-variable-types)
3. [Dynamic Variable Generation](#dynamic-variable-generation)
4. [Environment-Specific Management](#environment-specific-management)
5. [Secret Management Integration](#secret-management-integration)
6. [Variable Validation & Security](#variable-validation--security)
7. [Performance Optimization](#performance-optimization)
8. [Enterprise Patterns](#enterprise-patterns)

## Variable Precedence & Architecture

### Complete Precedence Hierarchy
```yaml
# 1. Extra vars (command line) - HIGHEST PRECEDENCE
# ansible-playbook -e "debug_mode=true override_port=8080"

# 2. Task vars
- name: Deploy with task-specific config
  template:
    src: app.conf.j2
    dest: /etc/app/app.conf
  vars:
    app_config:
      port: 9090
      debug: "{{ debug_mode | default(false) }}"
      cache_size: "{{ cache_size_override | default('128MB') }}"

# 3. Block vars
- name: Database configuration block
  block:
    - name: Configure primary database
      template:
        src: db_primary.conf.j2
        dest: /etc/mysql/conf.d/primary.cnf
    - name: Configure replica database
      template:
        src: db_replica.conf.j2
        dest: /etc/mysql/conf.d/replica.cnf
  vars:
    db_config:
      max_connections: 1000
      innodb_buffer_pool_size: "{{ (ansible_memtotal_mb * 0.7) | int }}MB"
      replication_format: "{{ replication_format | default('ROW') }}"

# 4. Role and include vars
# roles/database/vars/main.yml
database_settings:
  connection_pool:
    min_size: 5
    max_size: "{{ db_max_connections | default(50) }}"
    timeout: 30
  performance:
    query_cache_size: "{{ db_query_cache | default('64MB') }}"
    tmp_table_size: "{{ db_tmp_table_size | default('32MB') }}"

# 5. Play vars
- hosts: web_servers
  vars:
    application_config:
      name: "{{ app_name }}"
      version: "{{ app_version }}"
      environment: "{{ deployment_environment }}"
      features:
        authentication: "{{ auth_enabled | default(true) }}"
        monitoring: "{{ monitoring_enabled | default(true) }}"
        caching: "{{ cache_enabled | default(false) }}"
```

### Enterprise Variable Architecture
```yaml
# group_vars/all/global.yml - Global enterprise settings
enterprise_config:
  organization: "{{ vault_org_name }}"
  domain: "{{ company_domain }}"
  timezone: "{{ default_timezone | default('UTC') }}"
  
networking:
  dns_servers:
    - "{{ primary_dns }}"
    - "{{ secondary_dns }}"
  ntp_servers:
    - "{{ primary_ntp }}"
    - "{{ secondary_ntp }}"
    
security_standards:
  ssl_cipher_suites: "{{ vault_ssl_ciphers }}"
  password_policy:
    min_length: 12
    complexity: high
    rotation_days: 90
  audit_logging: true

# group_vars/production/environment.yml - Production-specific
deployment_config:
  replica_count: 3
  resource_limits:
    cpu: "2"
    memory: "4Gi"
  auto_scaling:
    enabled: true
    min_replicas: 3
    max_replicas: 10
    cpu_threshold: 70
    
monitoring:
  alerting_enabled: true
  log_level: "WARNING"
  metrics_retention: "30d"
  
backup_config:
  enabled: true
  schedule: "0 2 * * *"
  retention_policy: "7d"
  encryption: true

# host_vars/web01.prod.company.com/host_specific.yml
host_specific:
  server_role: "primary_web"
  maintenance_window: "02:00-04:00"
  backup_priority: "high"
  
local_storage:
  data_partition: "/data"
  log_partition: "/var/log"
  temp_partition: "/tmp"
```

## Advanced Variable Types

### Complex Data Structures
```yaml
# Multi-layered configuration structures
application_services:
  web_tier:
    nginx:
      version: "{{ nginx_version | default('1.20') }}"
      config:
        worker_processes: "{{ ansible_processor_vcpus }}"
        worker_connections: 1024
        keepalive_timeout: 65
        client_max_body_size: "10m"
      modules:
        - http_ssl_module
        - http_realip_module
        - http_gzip_static_module
      ssl:
        protocols:
          - TLSv1.2
          - TLSv1.3
        ciphers: "{{ vault_ssl_ciphers }}"
        
  app_tier:
    application:
      name: "{{ app_name }}"
      version: "{{ app_version }}"
      instances: "{{ app_instances | default(2) }}"
      runtime:
        jvm_opts: >
          -Xms{{ (ansible_memtotal_mb * 0.25) | int }}m
          -Xmx{{ (ansible_memtotal_mb * 0.5) | int }}m
          -XX:+UseG1GC
          -XX:G1HeapRegionSize=16m
      database:
        connection_string: "{{ vault_db_connection }}"
        pool_size: "{{ db_pool_size | default(20) }}"
        
  data_tier:
    postgresql:
      version: "{{ postgres_version | default('13') }}"
      config:
        shared_buffers: "{{ (ansible_memtotal_mb * 0.25) | int }}MB"
        effective_cache_size: "{{ (ansible_memtotal_mb * 0.75) | int }}MB"
        work_mem: "{{ ((ansible_memtotal_mb * 0.25) / 16) | int }}MB"
        maintenance_work_mem: "{{ (ansible_memtotal_mb * 0.05) | int }}MB"
      replication:
        enabled: "{{ postgres_replication | default(false) }}"
        mode: "{{ replication_mode | default('async') }}"
        replicas: "{{ postgres_replicas | default([]) }}"
```

### Conditional Variable Assignment
```yaml
# Environment-aware variable assignment
environment_settings: >
  {{
    {
      'development': {
        'log_level': 'DEBUG',
        'debug_mode': true,
        'cache_ttl': 60,
        'replica_count': 1,
        'resource_requests': {
          'cpu': '100m',
          'memory': '256Mi'
        }
      },
      'staging': {
        'log_level': 'INFO',
        'debug_mode': false,
        'cache_ttl': 300,
        'replica_count': 2,
        'resource_requests': {
          'cpu': '200m',
          'memory': '512Mi'
        }
      },
      'production': {
        'log_level': 'WARNING',
        'debug_mode': false,
        'cache_ttl': 3600,
        'replica_count': 5,
        'resource_requests': {
          'cpu': '500m',
          'memory': '1Gi'
        }
      }
    }[deployment_environment]
  }}

# Dynamic resource allocation based on server specifications
compute_resources: >
  {{
    {
      'small': {
        'cpu_cores': 2,
        'memory_gb': 4,
        'storage_gb': 50,
        'max_connections': 100
      },
      'medium': {
        'cpu_cores': 4,
        'memory_gb': 8,
        'storage_gb': 100,
        'max_connections': 200
      },
      'large': {
        'cpu_cores': 8,
        'memory_gb': 16,
        'storage_gb': 200,
        'max_connections': 500
      },
      'xlarge': {
        'cpu_cores': 16,
        'memory_gb': 32,
        'storage_gb': 500,
        'max_connections': 1000
      }
    }[
      server_size if server_size is defined else
      ('xlarge' if ansible_memtotal_mb > 30000 else
       'large' if ansible_memtotal_mb > 14000 else
       'medium' if ansible_memtotal_mb > 6000 else
       'small')
    ]
  }}
```

## Dynamic Variable Generation

### Runtime Variable Construction
```yaml
# Dynamic service discovery
- name: Build dynamic service registry
  set_fact:
    service_registry: >
      {{
        service_registry | default({}) | combine({
          hostvars[item]['service_name']: {
            'host': hostvars[item]['ansible_default_ipv4']['address'],
            'port': hostvars[item]['service_port'],
            'health_check': 'http://' + hostvars[item]['ansible_default_ipv4']['address'] + ':' + (hostvars[item]['service_port'] | string) + '/health',
            'weight': hostvars[item]['load_balancer_weight'] | default(1),
            'datacenter': hostvars[item]['datacenter'],
            'environment': hostvars[item]['environment'],
            'version': hostvars[item]['app_version']
          }
        })
      }}
  loop: "{{ groups['app_servers'] }}"
  run_once: true
  delegate_to: localhost

# Dynamic configuration based on infrastructure
- name: Generate load balancer configuration
  set_fact:
    lb_backend_config: |
      upstream {{ service_name }} {
      {% for service, details in service_registry.items() %}
      {% if details.environment == deployment_environment %}
        server {{ details.host }}:{{ details.port }} weight={{ details.weight }};
      {% endif %}
      {% endfor %}
      }
      
      server {
        listen 80;
        server_name {{ service_name }}.{{ company_domain }};
        
        location /health {
          access_log off;
          return 200 "healthy\n";
        }
        
        location / {
          proxy_pass http://{{ service_name }};
          proxy_set_header Host $host;
          proxy_set_header X-Real-IP $remote_addr;
          proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        }
      }
  delegate_to: "{{ item }}"
  loop: "{{ groups['load_balancers'] }}"
```

### Template-Based Variable Generation
```yaml
# Advanced Jinja2 templating for configuration
- name: Generate complex application configuration
  template:
    src: application.yml.j2
    dest: /opt/app/config/application.yml
  vars:
    app_config_template: |
      # Application Configuration - Generated by Ansible
      # Environment: {{ deployment_environment }}
      # Generated: {{ ansible_date_time.iso8601 }}
      
      server:
        port: {{ app_port | default(8080) }}
        servlet:
          context-path: /{{ app_name }}
        tomcat:
          threads:
            max: {{ (ansible_processor_vcpus * 50) | int }}
            min-spare: {{ (ansible_processor_vcpus * 10) | int }}
      
      spring:
        application:
          name: {{ app_name }}
        profiles:
          active: {{ spring_profiles | default([deployment_environment]) | join(',') }}
        
        datasource:
          url: {{ vault_database_url }}
          username: {{ vault_database_username }}
          password: {{ vault_database_password }}
          hikari:
            pool-size: {{ db_pool_size | default(20) }}
            connection-timeout: {{ db_connection_timeout | default(30000) }}
            idle-timeout: {{ db_idle_timeout | default(600000) }}
            max-lifetime: {{ db_max_lifetime | default(1800000) }}
        
        redis:
          host: {{ redis_host | default('localhost') }}
          port: {{ redis_port | default(6379) }}
          {% if redis_password is defined %}
          password: {{ redis_password }}
          {% endif %}
          lettuce:
            pool:
              max-active: {{ redis_pool_max | default(50) }}
              max-idle: {{ redis_pool_idle | default(10) }}
        
        jpa:
          hibernate:
            ddl-auto: {{ hibernate_ddl_auto | default('validate') }}
          properties:
            hibernate:
              dialect: {{ hibernate_dialect | default('org.hibernate.dialect.PostgreSQLDialect') }}
              show_sql: {{ hibernate_show_sql | default(false) }}
              format_sql: {{ hibernate_format_sql | default(false) }}
      
      logging:
        level:
          com.company.{{ app_name }}: {{ app_log_level | default('INFO') }}
          org.springframework: {{ spring_log_level | default('WARN') }}
          org.hibernate: {{ hibernate_log_level | default('WARN') }}
        pattern:
          console: "%d{yyyy-MM-dd HH:mm:ss} [%thread] %-5level %logger{36} - %msg%n"
          file: "%d{yyyy-MM-dd HH:mm:ss} [%thread] %-5level %logger{36} - %msg%n"
        file:
          name: /var/log/{{ app_name }}/application.log
          max-size: {{ log_max_size | default('100MB') }}
          max-history: {{ log_max_history | default(30) }}
      
      management:
        endpoints:
          web:
            exposure:
              include: {{ actuator_endpoints | default(['health', 'info', 'metrics']) | join(',') }}
        endpoint:
          health:
            show-details: {{ health_show_details | default('when-authorized') }}
        metrics:
          export:
            prometheus:
              enabled: {{ prometheus_metrics | default(true) }}
      
      # Custom application properties
      {% for key, value in custom_properties.items() %}
      {{ key }}: {{ value }}
      {% endfor %}
```

## Environment-Specific Management

### Multi-Environment Variable Structure
```yaml
# group_vars/all/environments.yml
environments:
  development:
    domain: "dev.company.com"
    database:
      host: "dev-db.company.com"
      port: 5432
      ssl_mode: "prefer"
    cache:
      host: "dev-redis.company.com"
      ttl: 300
    monitoring:
      enabled: false
    security:
      ssl_required: false
      session_timeout: 3600
      
  staging:
    domain: "staging.company.com"
    database:
      host: "staging-db.company.com"
      port: 5432
      ssl_mode: "require"
    cache:
      host: "staging-redis.company.com"
      ttl: 1800
    monitoring:
      enabled: true
    security:
      ssl_required: true
      session_timeout: 1800
      
  production:
    domain: "company.com"
    database:
      host: "prod-db-cluster.company.com"
      port: 5432
      ssl_mode: "require"
      read_replicas:
        - "prod-db-read1.company.com"
        - "prod-db-read2.company.com"
    cache:
      host: "prod-redis-cluster.company.com"
      ttl: 3600
      cluster_mode: true
    monitoring:
      enabled: true
      alerting: true
    security:
      ssl_required: true
      session_timeout: 900
      mfa_required: true

# Dynamic environment selection
current_env_config: "{{ environments[deployment_environment] }}"

# Environment-specific resource scaling
resource_scaling:
  development:
    web_servers: 1
    app_servers: 1
    db_servers: 1
    load_balancers: 0
    
  staging:
    web_servers: 2
    app_servers: 2
    db_servers: 1
    load_balancers: 1
    
  production:
    web_servers: 4
    app_servers: 6
    db_servers: 3
    load_balancers: 2

current_scaling: "{{ resource_scaling[deployment_environment] }}"
```

### Region-Specific Configuration
```yaml
# Multi-region deployment variables
regional_config:
  us_east_1:
    aws_region: "us-east-1"
    availability_zones:
      - "us-east-1a"
      - "us-east-1b"
      - "us-east-1c"
    vpc_cidr: "10.1.0.0/16"
    nat_gateways: 3
    rds_multi_az: true
    s3_bucket_suffix: "use1"
    cloudfront_price_class: "PriceClass_All"
    
  us_west_2:
    aws_region: "us-west-2"
    availability_zones:
      - "us-west-2a"
      - "us-west-2b"
      - "us-west-2c"
    vpc_cidr: "10.2.0.0/16"
    nat_gateways: 3
    rds_multi_az: true
    s3_bucket_suffix: "usw2"
    cloudfront_price_class: "PriceClass_All"
    
  eu_west_1:
    aws_region: "eu-west-1"
    availability_zones:
      - "eu-west-1a"
      - "eu-west-1b"
      - "eu-west-1c"
    vpc_cidr: "10.3.0.0/16"
    nat_gateways: 3
    rds_multi_az: true
    s3_bucket_suffix: "euw1"
    cloudfront_price_class: "PriceClass_100"

current_region: "{{ regional_config[aws_region] }}"
```

## Secret Management Integration

### HashiCorp Vault Integration
```yaml
# Vault secret retrieval patterns
- name: Retrieve application secrets from Vault
  set_fact:
    application_secrets:
      database:
        username: "{{ lookup('hashi_vault', 'secret/{{ app_name }}/{{ deployment_environment }}/database:username') }}"
        password: "{{ lookup('hashi_vault', 'secret/{{ app_name }}/{{ deployment_environment }}/database:password') }}"
      api_keys:
        payment_gateway: "{{ lookup('hashi_vault', 'secret/{{ app_name }}/{{ deployment_environment }}/api_keys:payment_gateway') }}"
        email_service: "{{ lookup('hashi_vault', 'secret/{{ app_name }}/{{ deployment_environment }}/api_keys:email_service') }}"
      certificates:
        ssl_cert: "{{ lookup('hashi_vault', 'secret/{{ app_name }}/{{ deployment_environment }}/ssl:certificate') }}"
        ssl_key: "{{ lookup('hashi_vault', 'secret/{{ app_name }}/{{ deployment_environment }}/ssl:private_key') }}"
  no_log: true
  delegate_to: localhost
  run_once: true

# Dynamic secret path generation
vault_secret_paths:
  database: "secret/data/{{ app_name }}/{{ deployment_environment }}/database"
  api_keys: "secret/data/{{ app_name }}/{{ deployment_environment }}/api"
  certificates: "secret/data/{{ app_name }}/{{ deployment_environment }}/tls"
  monitoring: "secret/data/shared/monitoring/{{ deployment_environment }}"
```

### AWS Secrets Manager Integration
```yaml
# AWS Secrets Manager secret retrieval
- name: Retrieve secrets from AWS Secrets Manager
  set_fact:
    aws_secrets:
      rds_credentials: "{{ lookup('aws_secret', 'prod/myapp/database', region='us-west-2') | from_json }}"
      api_tokens: "{{ lookup('aws_secret', 'prod/myapp/external-apis', region='us-west-2') | from_json }}"
      encryption_keys: "{{ lookup('aws_secret', 'prod/myapp/encryption', region='us-west-2') | from_json }}"
  no_log: true
  when: cloud_provider == 'aws'
```

## Variable Validation & Security

### Input Validation
```yaml
# Comprehensive variable validation
- name: Validate required variables
  assert:
    that:
      - deployment_environment is defined
      - deployment_environment in ['development', 'staging', 'production']
      - app_name is defined
      - app_name | length > 0
      - app_version is defined
      - app_version is match('^\d+\.\d+\.\d+$')
      - database_host is defined
      - database_port is defined
      - database_port | int > 0
      - database_port | int < 65536
    fail_msg: "Required variables are missing or invalid"
    success_msg: "All required variables are valid"

# Security validation
- name: Validate security configuration
  assert:
    that:
      - ssl_enabled | default(false) | bool == true
      - session_timeout | default(0) | int >= 900  # Minimum 15 minutes
      - password_min_length | default(0) | int >= 12
      - backup_encryption | default(false) | bool == true
    fail_msg: "Security configuration does not meet minimum requirements"
  when: deployment_environment == 'production'

# Data type validation
- name: Validate data types and formats
  assert:
    that:
      - memory_limit is match('^\d+[MGT]i?$')
      - cpu_limit is match('^\d+m?$')
      - email_address is match('^[\w\.-]+@[\w\.-]+\.[a-zA-Z]{2,}$')
      - ip_address is match('^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$')
    fail_msg: "Variable format validation failed"
```

### Sensitive Data Protection
```yaml
# Sensitive variable handling
sensitive_vars:
  - database_password
  - api_secret_key
  - ssl_private_key
  - jwt_signing_key
  - encryption_key

- name: Ensure sensitive variables are not logged
  set_fact:
    "{{ item }}": "{{ hostvars[inventory_hostname][item] }}"
  loop: "{{ sensitive_vars }}"
  no_log: true
  when: hostvars[inventory_hostname][item] is defined

# Variable masking in outputs
- name: Display configuration (masked)
  debug:
    msg: |
      Application Configuration:
      - Name: {{ app_name }}
      - Version: {{ app_version }}
      - Environment: {{ deployment_environment }}
      - Database Host: {{ database_host }}
      - Database Password: {{ '***MASKED***' if database_password is defined else 'Not Set' }}
      - SSL Enabled: {{ ssl_enabled | default(false) }}
```

## Performance Optimization

### Variable Caching
```yaml
# Cache expensive lookups
- name: Cache infrastructure information
  set_fact:
    infrastructure_cache:
      timestamp: "{{ ansible_date_time.epoch }}"
      aws_instances: "{{ groups['aws_instances'] | map('extract', hostvars, 'ec2_instance_id') | list }}"
      security_groups: "{{ groups['aws_instances'] | map('extract', hostvars, 'ec2_security_groups') | list | flatten | unique }}"
      availability_zones: "{{ groups['aws_instances'] | map('extract', hostvars, 'ec2_placement_availability_zone') | list | unique }}"
  run_once: true
  delegate_to: localhost
  when: infrastructure_cache is not defined or (ansible_date_time.epoch | int - infrastructure_cache.timestamp | int) > 3600

# Lazy loading of variables
- name: Load heavy configuration only when needed
  include_vars: "{{ deployment_environment }}_detailed_config.yml"
  when: detailed_config_required | default(false)
```

### Memory-Efficient Variable Handling
```yaml
# Stream processing for large datasets
- name: Process large configuration files efficiently
  set_fact:
    processed_configs: []
    
- name: Process configurations in batches
  set_fact:
    processed_configs: "{{ processed_configs + [item | combine({'processed': true, 'batch': batch_index})] }}"
  loop: "{{ large_config_list | batch(batch_size) | list }}"
  loop_control:
    index_var: batch_index
  vars:
    batch_size: 100
```

## Enterprise Patterns

### Configuration Management Database (CMDB) Integration
```yaml
# CMDB integration for dynamic inventory
- name: Query CMDB for server configuration
  uri:
    url: "{{ cmdb_api_endpoint }}/servers"
    headers:
      Authorization: "Bearer {{ cmdb_api_token }}"
      Content-Type: "application/json"
    method: GET
    body_format: json
    body:
      filters:
        environment: "{{ deployment_environment }}"
        application: "{{ app_name }}"
        status: "active"
  register: cmdb_servers
  delegate_to: localhost
  run_once: true

- name: Build configuration from CMDB data
  set_fact:
    server_configs: >
      {{
        cmdb_servers.json.results | map('extract', ['hostname', 'ip_address', 'role', 'specifications']) |
        map('combine', {'ansible_host': item.ip_address, 'server_role': item.role}) | list
      }}
  loop: "{{ cmdb_servers.json.results }}"
```

### Multi-Tenant Configuration
```yaml
# Multi-tenant variable management
tenant_configurations:
  tenant_a:
    database:
      schema: "tenant_a_schema"
      connection_pool: 10
    storage:
      bucket: "tenant-a-storage"
      encryption: "AES256"
    features:
      advanced_analytics: true
      custom_branding: true
      
  tenant_b:
    database:
      schema: "tenant_b_schema"
      connection_pool: 5
    storage:
      bucket: "tenant-b-storage"
      encryption: "AES128"
    features:
      advanced_analytics: false
      custom_branding: false

# Dynamic tenant selection
current_tenant_config: "{{ tenant_configurations[tenant_id] }}"

# Tenant-specific resource allocation
tenant_resources: >
  {{
    {
      'small': {'cpu': '200m', 'memory': '512Mi', 'storage': '10Gi'},
      'medium': {'cpu': '500m', 'memory': '1Gi', 'storage': '50Gi'},
      'large': {'cpu': '1000m', 'memory': '2Gi', 'storage': '100Gi'},
      'enterprise': {'cpu': '2000m', 'memory': '4Gi', 'storage': '500Gi'}
    }[tenant_configurations[tenant_id].tier | default('small')]
  }}
```

This comprehensive guide provides enterprise-grade variable management patterns, advanced templating techniques, and scalable configuration strategies for complex Ansible automation environments.