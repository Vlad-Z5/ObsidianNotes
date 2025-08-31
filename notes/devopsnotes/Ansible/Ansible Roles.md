# Enterprise Ansible Roles Architecture

Advanced role development, modular design patterns, and enterprise-grade automation components for scalable infrastructure management.

## Table of Contents
1. [Enterprise Role Architecture](#enterprise-role-architecture)
2. [Advanced Role Development](#advanced-role-development)
3. [Role Composition Patterns](#role-composition-patterns)
4. [Testing & Quality Assurance](#testing--quality-assurance)
5. [Role Lifecycle Management](#role-lifecycle-management)
6. [Performance Optimization](#performance-optimization)
7. [Enterprise Integration](#enterprise-integration)
8. [Security & Compliance](#security--compliance)

## Enterprise Role Architecture

### Complete Role Directory Structure
```
roles/
└── enterprise-webserver/
    ├── README.md                    # Comprehensive documentation
    ├── meta/
    │   ├── main.yml                 # Role metadata and dependencies
    │   ├── requirements.yml         # External role requirements
    │   └── argument_specs.yml       # Input validation specifications
    ├── defaults/
    │   ├── main.yml                 # Default variables
    │   ├── environments/
    │   │   ├── development.yml      # Environment-specific defaults
    │   │   ├── staging.yml
    │   │   └── production.yml
    │   └── security.yml             # Security-related defaults
    ├── vars/
    │   ├── main.yml                 # Internal role variables
    │   ├── platform/
    │   │   ├── RedHat.yml           # Platform-specific variables
    │   │   ├── Debian.yml
    │   │   └── Windows.yml
    │   └── versions/
    │       ├── nginx-1.20.yml       # Version-specific configurations
    │       └── nginx-1.21.yml
    ├── tasks/
    │   ├── main.yml                 # Main task orchestration
    │   ├── install.yml              # Installation tasks
    │   ├── configure.yml            # Configuration tasks
    │   ├── security.yml             # Security hardening tasks
    │   ├── monitoring.yml           # Monitoring setup tasks
    │   ├── backup.yml               # Backup configuration tasks
    │   ├── platform/
    │   │   ├── RedHat.yml           # Platform-specific tasks
    │   │   └── Debian.yml
    │   └── validation/
    │       ├── pre_tasks.yml        # Pre-deployment validation
    │       └── post_tasks.yml       # Post-deployment verification
    ├── handlers/
    │   ├── main.yml                 # Primary handlers
    │   ├── services.yml             # Service management handlers
    │   └── cleanup.yml              # Cleanup handlers
    ├── templates/
    │   ├── nginx.conf.j2            # Main configuration templates
    │   ├── ssl/
    │   │   └── ssl.conf.j2          # SSL configuration
    │   ├── monitoring/
    │   │   ├── nginx_status.conf.j2
    │   │   └── log_config.conf.j2
    │   └── security/
    │       └── security_headers.conf.j2
    ├── files/
    │   ├── scripts/
    │   │   ├── health_check.sh      # Health check scripts
    │   │   └── backup_config.sh     # Backup scripts
    │   ├── certificates/
    │   │   └── ca-bundle.crt        # Certificate files
    │   └── policies/
    │       └── security_policy.json
    ├── library/                     # Custom modules
    │   └── nginx_config_validator.py
    ├── module_utils/                # Shared module utilities
    │   └── nginx_utils.py
    ├── filter_plugins/              # Custom filters
    │   └── nginx_filters.py
    ├── lookup_plugins/              # Custom lookups
    │   └── nginx_config_lookup.py
    ├── tests/
    │   ├── inventory               # Test inventory
    │   ├── test.yml               # Test playbook
    │   ├── group_vars/
    │   └── host_vars/
    └── molecule/                   # Molecule testing
        ├── default/
        │   ├── converge.yml
        │   ├── molecule.yml
        │   └── verify.yml
        └── docker/
            ├── converge.yml
            ├── molecule.yml
            └── Dockerfile
```

### Meta Configuration (meta/main.yml)
```yaml
---
galaxy_info:
  role_name: enterprise_webserver
  namespace: company
  author: "Enterprise DevOps Team"
  description: "Enterprise-grade web server configuration with security, monitoring, and high availability"
  company: "Your Company Name"
  license: "MIT"
  min_ansible_version: "2.12"
  
  platforms:
    - name: "EL"
      versions:
        - "8"
        - "9"
    - name: "Ubuntu"
      versions:
        - "20.04"
        - "22.04"
    - name: "Debian"
      versions:
        - "10"
        - "11"
  
  galaxy_tags:
    - webserver
    - nginx
    - security
    - monitoring
    - enterprise
    - high-availability

dependencies:
  - role: company.common
    vars:
      common_packages:
        - curl
        - wget
        - htop
        - vim
  - role: company.security_baseline
    when: security_hardening_enabled | default(true)
  - role: company.monitoring_agent
    vars:
      monitoring_services:
        - nginx
    when: monitoring_enabled | default(true)
  - role: company.log_aggregation
    vars:
      log_sources:
        - "/var/log/nginx/access.log"
        - "/var/log/nginx/error.log"
    when: centralized_logging_enabled | default(false)

collections:
  - community.general
  - ansible.posix
  - community.crypto
```

### Argument Specifications (meta/argument_specs.yml)
```yaml
---
argument_specs:
  main:
    short_description: "Enterprise web server role"
    description:
      - "Configures nginx web server with enterprise features"
      - "Includes security hardening, SSL/TLS configuration, monitoring, and backup"
    author:
      - "Enterprise DevOps Team"
    options:
      nginx_version:
        type: "str"
        required: false
        default: "1.20"
        description: "Nginx version to install"
        choices: ["1.18", "1.20", "1.21", "latest"]
      
      environment:
        type: "str"
        required: true
        description: "Deployment environment"
        choices: ["development", "staging", "production"]
      
      ssl_enabled:
        type: "bool"
        required: false
        default: true
        description: "Enable SSL/TLS configuration"
      
      ssl_certificate_path:
        type: "str"
        required: false
        description: "Path to SSL certificate file"
      
      ssl_private_key_path:
        type: "str"
        required: false
        description: "Path to SSL private key file"
      
      virtual_hosts:
        type: "list"
        elements: "dict"
        required: false
        default: []
        description: "List of virtual hosts to configure"
        options:
          server_name:
            type: "str"
            required: true
            description: "Server name for virtual host"
          document_root:
            type: "str"
            required: true
            description: "Document root directory"
          ssl_enabled:
            type: "bool"
            default: false
            description: "Enable SSL for this virtual host"
      
      backup_enabled:
        type: "bool"
        default: true
        description: "Enable configuration backup"
      
      monitoring_enabled:
        type: "bool"
        default: true
        description: "Enable monitoring configuration"
```

## Advanced Role Development

### Main Task Orchestration (tasks/main.yml)
```yaml
---
# Pre-flight validation
- name: "Validate role parameters"
  include_tasks: validation/pre_tasks.yml
  tags: [validation, pre-validation]

# Platform detection and variable loading
- name: "Load platform-specific variables"
  include_vars: "platform/{{ ansible_os_family }}.yml"
  tags: [variables]

- name: "Load environment-specific defaults"
  include_vars: "environments/{{ environment }}.yml"
  when: environment is defined
  tags: [variables]

- name: "Load version-specific variables"
  include_vars: "versions/nginx-{{ nginx_version }}.yml"
  when: nginx_version != 'latest'
  tags: [variables]

# Core installation and configuration
- name: "Install nginx web server"
  include_tasks: install.yml
  tags: [install, nginx]

- name: "Configure nginx web server"
  include_tasks: configure.yml
  tags: [configure, nginx]

# Security hardening
- name: "Apply security hardening"
  include_tasks: security.yml
  when: security_hardening_enabled | default(true)
  tags: [security, hardening]

# Monitoring setup
- name: "Configure monitoring"
  include_tasks: monitoring.yml
  when: monitoring_enabled | default(true)
  tags: [monitoring]

# Backup configuration
- name: "Setup backup procedures"
  include_tasks: backup.yml
  when: backup_enabled | default(true)
  tags: [backup]

# Post-deployment validation
- name: "Validate deployment"
  include_tasks: validation/post_tasks.yml
  tags: [validation, post-validation]

# Service management
- name: "Ensure nginx is running and enabled"
  service:
    name: "{{ nginx_service_name }}"
    state: started
    enabled: true
  tags: [service]
```

### Advanced Installation Tasks (tasks/install.yml)
```yaml
---
- name: "Create nginx user and group"
  block:
    - name: "Create nginx group"
      group:
        name: "{{ nginx_group }}"
        system: true
        state: present
        
    - name: "Create nginx user"
      user:
        name: "{{ nginx_user }}"
        group: "{{ nginx_group }}"
        system: true
        shell: /sbin/nologin
        home: /var/cache/nginx
        createhome: false
        state: present
  tags: [user-management]

- name: "Install nginx using platform-specific method"
  include_tasks: "platform/{{ ansible_os_family }}.yml"
  tags: [platform-install]

- name: "Create required directories"
  file:
    path: "{{ item.path }}"
    state: directory
    owner: "{{ item.owner | default('root') }}"
    group: "{{ item.group | default('root') }}"
    mode: "{{ item.mode | default('0755') }}"
  loop:
    - path: "{{ nginx_conf_dir }}"
    - path: "{{ nginx_conf_dir }}/conf.d"
    - path: "{{ nginx_conf_dir }}/sites-available"
    - path: "{{ nginx_conf_dir }}/sites-enabled"
    - path: "{{ nginx_conf_dir }}/ssl"
      mode: "0700"
    - path: "{{ nginx_log_dir }}"
      owner: "{{ nginx_user }}"
      group: "{{ nginx_group }}"
    - path: "{{ nginx_cache_dir }}"
      owner: "{{ nginx_user }}"
      group: "{{ nginx_group }}"
    - path: "{{ nginx_pid_dir }}"
      owner: "{{ nginx_user }}"
      group: "{{ nginx_group }}"
  tags: [directories]

- name: "Install additional nginx modules"
  package:
    name: "{{ item }}"
    state: present
  loop: "{{ nginx_additional_modules }}"
  when: nginx_additional_modules is defined
  notify: restart nginx
  tags: [modules]

- name: "Verify nginx installation"
  command: "nginx -v"
  register: nginx_version_check
  changed_when: false
  failed_when: nginx_version_check.rc != 0
  tags: [verification]

- name: "Display installed nginx version"
  debug:
    msg: "Installed nginx version: {{ nginx_version_check.stderr | regex_search('nginx/(\\S+)', '\\1') | first }}"
  tags: [verification]
```

### Comprehensive Configuration (tasks/configure.yml)
```yaml
---
- name: "Generate main nginx configuration"
  template:
    src: nginx.conf.j2
    dest: "{{ nginx_conf_dir }}/nginx.conf"
    owner: root
    group: root
    mode: '0644'
    backup: true
    validate: 'nginx -t -c %s'
  notify:
    - reload nginx
    - validate nginx config
  tags: [main-config]

- name: "Configure virtual hosts"
  block:
    - name: "Create virtual host configurations"
      template:
        src: vhost.conf.j2
        dest: "{{ nginx_conf_dir }}/sites-available/{{ item.server_name }}.conf"
        owner: root
        group: root
        mode: '0644'
        backup: true
      loop: "{{ virtual_hosts }}"
      register: vhost_configs
      notify: reload nginx
      
    - name: "Enable virtual hosts"
      file:
        src: "{{ nginx_conf_dir }}/sites-available/{{ item.server_name }}.conf"
        dest: "{{ nginx_conf_dir }}/sites-enabled/{{ item.server_name }}.conf"
        state: link
        force: true
      loop: "{{ virtual_hosts }}"
      when: item.enabled | default(true)
      notify: reload nginx
      
    - name: "Create document root directories"
      file:
        path: "{{ item.document_root }}"
        state: directory
        owner: "{{ nginx_user }}"
        group: "{{ nginx_group }}"
        mode: '0755'
      loop: "{{ virtual_hosts }}"
      
    - name: "Deploy default index pages"
      template:
        src: index.html.j2
        dest: "{{ item.document_root }}/index.html"
        owner: "{{ nginx_user }}"
        group: "{{ nginx_group }}"
        mode: '0644'
      loop: "{{ virtual_hosts }}"
      when: item.deploy_default_page | default(false)
      
  when: virtual_hosts is defined and virtual_hosts | length > 0
  tags: [vhosts]

- name: "Configure SSL/TLS"
  block:
    - name: "Generate DH parameters"
      openssl_dhparam:
        path: "{{ nginx_conf_dir }}/ssl/dhparam.pem"
        size: 2048
        owner: root
        group: root
        mode: '0600'
      when: ssl_generate_dhparam | default(true)
      
    - name: "Configure SSL certificates"
      include_tasks: ssl_certificates.yml
      loop: "{{ virtual_hosts | selectattr('ssl_enabled', 'defined') | selectattr('ssl_enabled') | list }}"
      loop_control:
        loop_var: vhost
        
  when: ssl_enabled | default(true)
  tags: [ssl, tls]

- name: "Configure log rotation"
  template:
    src: nginx.logrotate.j2
    dest: /etc/logrotate.d/nginx
    owner: root
    group: root
    mode: '0644'
  tags: [logging]

- name: "Setup custom error pages"
  block:
    - name: "Create error pages directory"
      file:
        path: "{{ nginx_error_pages_dir }}"
        state: directory
        owner: root
        group: root
        mode: '0755'
        
    - name: "Deploy custom error pages"
      template:
        src: "errors/{{ item }}.html.j2"
        dest: "{{ nginx_error_pages_dir }}/{{ item }}.html"
        owner: root
        group: root
        mode: '0644'
      loop:
        - 404
        - 500
        - 502
        - 503
        - 504
      when: nginx_custom_error_pages | default(false)
      
  tags: [error-pages]

- name: "Configure rate limiting"
  template:
    src: rate_limiting.conf.j2
    dest: "{{ nginx_conf_dir }}/conf.d/rate_limiting.conf"
    owner: root
    group: root
    mode: '0644'
  when: nginx_rate_limiting_enabled | default(false)
  notify: reload nginx
  tags: [rate-limiting]
```

## Role Composition Patterns

### Advanced Dependencies (meta/main.yml)
```yaml
dependencies:
  # Base system configuration
  - role: company.common
    vars:
      common_timezone: "{{ deployment_timezone | default('UTC') }}"
      common_ntp_enabled: true
      common_packages:
        - curl
        - wget
        - htop
        - vim
        - openssl
        - ca-certificates
    tags: [common]
    
  # Security baseline
  - role: company.security_baseline
    vars:
      security_ssh_hardening: true
      security_firewall_enabled: true
      security_fail2ban_enabled: true
      security_audit_enabled: "{{ environment == 'production' }}"
    when: security_hardening_enabled | default(true)
    tags: [security]
    
  # Certificate management
  - role: company.certificate_manager
    vars:
      cert_domains: "{{ virtual_hosts | selectattr('ssl_enabled', 'defined') | selectattr('ssl_enabled') | map(attribute='server_name') | list }}"
      cert_email: "{{ ssl_admin_email }}"
      cert_provider: "{{ ssl_cert_provider | default('letsencrypt') }}"
    when: ssl_enabled | default(true) and ssl_auto_cert | default(false)
    tags: [certificates]
    
  # Monitoring and observability
  - role: company.prometheus_exporter
    vars:
      exporter_type: nginx
      exporter_port: 9113
      nginx_stub_status_enabled: true
    when: monitoring_enabled | default(true)
    tags: [monitoring]
    
  # Log aggregation
  - role: company.filebeat
    vars:
      filebeat_inputs:
        - type: log
          paths:
            - "{{ nginx_log_dir }}/access.log"
          fields:
            service: nginx
            log_type: access
        - type: log
          paths:
            - "{{ nginx_log_dir }}/error.log"
          fields:
            service: nginx
            log_type: error
    when: centralized_logging_enabled | default(false)
    tags: [logging]
```

### Role Inclusion Patterns
```yaml
# Dynamic role inclusion based on conditions
- name: "Include platform-specific tasks"
  include_role:
    name: "{{ nginx_platform_role }}"
    tasks_from: "{{ nginx_platform_tasks | default('main') }}"
  vars:
    nginx_platform_role: >
      {{
        'RedHat': 'company.nginx_redhat',
        'Debian': 'company.nginx_debian',
        'Windows': 'company.nginx_windows'
      }[ansible_os_family]
      }}
  when: nginx_platform_role is defined

# Conditional role application
- name: "Apply high availability configuration"
  include_role:
    name: company.nginx_ha
    apply:
      tags: [ha, clustering]
  vars:
    ha_cluster_nodes: "{{ groups['nginx_cluster'] }}"
    ha_vip_address: "{{ nginx_cluster_vip }}"
    ha_sync_configuration: true
  when: 
    - nginx_ha_enabled | default(false)
    - groups['nginx_cluster'] is defined
    - groups['nginx_cluster'] | length > 1

# Environment-specific role inclusion
- name: "Apply environment-specific configuration"
  include_role:
    name: "company.nginx_{{ environment }}"
  vars:
    environment_config: "{{ environments[environment] }}"
  when: 
    - environment is defined
    - environment in ['development', 'staging', 'production']
```

## Testing & Quality Assurance

### Molecule Testing Configuration (molecule/default/molecule.yml)
```yaml
---
dependency:
  name: galaxy
  options:
    requirements-file: requirements.yml
    
driver:
  name: docker
  
platforms:
  - name: nginx-ubuntu2004
    image: geerlingguy/docker-ubuntu2004-ansible:latest
    pre_build_image: true
    privileged: true
    volumes:
      - /sys/fs/cgroup:/sys/fs/cgroup:rw
    cgroupns_mode: host
    command: "/lib/systemd/systemd"
    tmpfs:
      - /run
      - /tmp
    groups:
      - webservers
      
  - name: nginx-centos8
    image: geerlingguy/docker-centos8-ansible:latest
    pre_build_image: true
    privileged: true
    volumes:
      - /sys/fs/cgroup:/sys/fs/cgroup:rw
    cgroupns_mode: host
    command: "/lib/systemd/systemd"
    tmpfs:
      - /run
      - /tmp
    groups:
      - webservers
      
provisioner:
  name: ansible
  inventory:
    host_vars:
      nginx-ubuntu2004:
        environment: development
        nginx_version: "1.20"
        virtual_hosts:
          - server_name: test.example.com
            document_root: /var/www/test
            ssl_enabled: false
      nginx-centos8:
        environment: staging
        nginx_version: "1.21"
        ssl_enabled: true
        virtual_hosts:
          - server_name: secure.example.com
            document_root: /var/www/secure
            ssl_enabled: true
  config_options:
    defaults:
      callback_whitelist: profile_tasks, timer
      stdout_callback: yaml
    ssh_connection:
      pipelining: true
      
verifier:
  name: ansible
  
scenario:
  test_sequence:
    - dependency
    - create
    - prepare
    - converge
    - idempotence
    - side_effect
    - verify
    - cleanup
    - destroy
```

### Test Verification (molecule/default/verify.yml)
```yaml
---
- name: Verify nginx deployment
  hosts: all
  gather_facts: true
  tasks:
    - name: "Test nginx is installed"
      command: nginx -v
      register: nginx_version
      changed_when: false
      
    - name: "Verify nginx version"
      assert:
        that:
          - nginx_version.rc == 0
          - "'nginx/' in nginx_version.stderr"
        fail_msg: "Nginx installation verification failed"
        
    - name: "Test nginx service is running"
      service_facts:
      
    - name: "Verify nginx service status"
      assert:
        that:
          - ansible_facts.services['nginx.service'].state == 'running'
          - ansible_facts.services['nginx.service'].status == 'enabled'
        fail_msg: "Nginx service is not running or not enabled"
        
    - name: "Test nginx configuration is valid"
      command: nginx -t
      register: nginx_test
      changed_when: false
      
    - name: "Verify nginx configuration"
      assert:
        that:
          - nginx_test.rc == 0
          - "'syntax is ok' in nginx_test.stderr"
          - "'test is successful' in nginx_test.stderr"
        fail_msg: "Nginx configuration test failed"
        
    - name: "Test HTTP response"
      uri:
        url: "http://{{ ansible_default_ipv4.address }}/"
        method: GET
        status_code: 200
      register: http_response
      
    - name: "Verify HTTP response"
      assert:
        that:
          - http_response.status == 200
        fail_msg: "HTTP request failed"
        
    - name: "Test SSL configuration (if enabled)"
      block:
        - name: "Test HTTPS response"
          uri:
            url: "https://{{ item.server_name }}/"
            method: GET
            status_code: 200
            validate_certs: false
          register: https_response
          loop: "{{ virtual_hosts | selectattr('ssl_enabled', 'defined') | selectattr('ssl_enabled') | list }}"
          
        - name: "Verify HTTPS response"
          assert:
            that:
              - https_response.results | selectattr('status', 'equalto', 200) | list | length == virtual_hosts | selectattr('ssl_enabled', 'defined') | selectattr('ssl_enabled') | list | length
            fail_msg: "HTTPS requests failed"
      when: ssl_enabled | default(false)
```

## Role Lifecycle Management

### Semantic Versioning and Releases
```yaml
# .github/workflows/release.yml
name: Release Role

on:
  push:
    tags:
      - 'v*.*.*'

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.8, 3.9]
        molecule-scenario: [default, docker]
        
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}
          
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install molecule[docker] ansible-lint yamllint
          
      - name: Run Molecule tests
        run: molecule test -s ${{ matrix.molecule-scenario }}
        env:
          PY_COLORS: '1'
          ANSIBLE_FORCE_COLOR: '1'
          
  release:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Import role to Ansible Galaxy
        run: |
          ansible-galaxy role import --api-key ${{ secrets.GALAXY_API_KEY }} \
            ${{ github.repository_owner }} $(echo ${{ github.repository }} | cut -d'/' -f2)
```

### Role Documentation Template
```markdown
# Enterprise Web Server Role

[![CI](https://github.com/company/ansible-role-nginx/workflows/CI/badge.svg)](https://github.com/company/ansible-role-nginx/actions)
[![Ansible Galaxy](https://img.shields.io/badge/galaxy-company.nginx-blue.svg)](https://galaxy.ansible.com/company/nginx)

## Description

Enterprise-grade Nginx web server role with advanced security, monitoring, and high availability features.

## Requirements

- Ansible >= 2.12
- Python >= 3.6
- Target systems: RHEL/CentOS 8+, Ubuntu 20.04+, Debian 10+

## Role Variables

### Required Variables

| Variable | Type | Description |
|----------|------| ----------- |
| `environment` | string | Deployment environment (development/staging/production) |
| `virtual_hosts` | list | List of virtual host configurations |

### Optional Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `nginx_version` | `1.20` | Nginx version to install |
| `ssl_enabled` | `true` | Enable SSL/TLS configuration |
| `monitoring_enabled` | `true` | Enable monitoring setup |
| `backup_enabled` | `true` | Enable configuration backup |

## Dependencies

- `company.common`: Base system configuration
- `company.security_baseline`: Security hardening (optional)
- `company.monitoring_agent`: Monitoring setup (optional)

## Example Playbook

```yaml
---
- hosts: webservers
  become: true
  vars:
    environment: production
    nginx_version: "1.21"
    ssl_enabled: true
    virtual_hosts:
      - server_name: example.com
        document_root: /var/www/example
        ssl_enabled: true
      - server_name: api.example.com
        document_root: /var/www/api
        ssl_enabled: true
        custom_config: |
          location /api/ {
              proxy_pass http://backend_servers;
              proxy_set_header Host $host;
          }
  roles:
    - company.nginx
```

## Testing

```bash
# Install dependencies
pip install molecule[docker] ansible-lint yamllint

# Run all tests
molecule test

# Test specific scenario
molecule test -s docker
```

## License

MIT

## Author Information

This role was created by the Enterprise DevOps Team.
```

This comprehensive enterprise role architecture provides production-ready patterns, extensive testing, and maintainable code structure for large-scale Ansible automation projects.