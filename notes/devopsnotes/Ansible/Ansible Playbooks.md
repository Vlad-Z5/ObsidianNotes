# Enterprise Ansible Playbooks

Advanced playbook architecture, orchestration patterns, and enterprise deployment strategies for scalable automation workflows.

## Table of Contents
1. [Playbook Design Patterns](#playbook-design-patterns)
2. [Advanced Task Management](#advanced-task-management)
3. [Deployment Strategies](#deployment-strategies)
4. [Error Handling & Recovery](#error-handling--recovery)
5. [Performance Optimization](#performance-optimization)
6. [Testing & Validation](#testing--validation)
7. [Enterprise Integration](#enterprise-integration)
8. [Monitoring & Observability](#monitoring--observability)

## Playbook Design Patterns
```yaml
# Enterprise playbook architectural patterns
playbook_patterns:
  orchestration_pattern:
    description: "Main playbooks that coordinate multiple sub-playbooks"
    structure: "site.yml -> environment-specific -> role-specific"
    use_cases: ["Complex deployments", "Multi-tier applications", "Infrastructure provisioning"]
    
  service_pattern:
    description: "Service-specific playbooks with standardized structure"
    structure: "One playbook per service with consistent lifecycle management"
    use_cases: ["Microservices", "Application deployment", "Service maintenance"]
    
  workflow_pattern:
    description: "Sequential execution with dependency management"
    structure: "Ordered execution with rollback capabilities"
    use_cases: ["Database migrations", "Blue-green deployments", "Disaster recovery"]
    
  matrix_pattern:
    description: "Cross-environment and cross-service execution"
    structure: "Dynamic targeting based on inventory groups and variables"
    use_cases: ["Multi-cloud deployments", "A/B testing", "Canary releases"]
```

## Advanced Playbook Structures

### Main Orchestration Playbook
```yaml
# site.yml - Master orchestration playbook
---
- name: Enterprise Infrastructure Management
  hosts: localhost
  connection: local
  gather_facts: false
  vars:
    deployment_timestamp: "{{ ansible_date_time.iso8601 }}"
    deployment_id: "{{ deployment_timestamp | regex_replace('[^0-9]', '') }}"
    
  pre_tasks:
    - name: Validate deployment parameters
      assert:
        that:
          - target_environment is defined
          - target_environment in ['development', 'staging', 'production']
          - app_version is defined
          - app_version | regex_search('^v\d+\.\d+\.\d+$')
        fail_msg: "Invalid deployment parameters. Required: target_environment, app_version"
    
    - name: Set deployment facts
      set_fact:
        deployment_config:
          id: "{{ deployment_id }}"
          timestamp: "{{ deployment_timestamp }}"
          environment: "{{ target_environment }}"
          version: "{{ app_version }}"
          strategy: "{{ deployment_strategy | default('rolling') }}"
          user: "{{ ansible_user_id }}"
          
    - name: Create deployment tracking
      uri:
        url: "{{ deployment_tracker_api }}/deployments"
        method: POST
        body_format: json
        body: "{{ deployment_config }}"
        headers:
          Authorization: "Bearer {{ deployment_api_token }}"
      when: deployment_tracker_api is defined
  
  tasks:
    - name: Import environment-specific deployment
      import_playbook: "environments/{{ target_environment }}.yml"
      vars:
        deployment_metadata: "{{ deployment_config }}"
  
  post_tasks:
    - name: Update deployment status
      uri:
        url: "{{ deployment_tracker_api }}/deployments/{{ deployment_id }}"
        method: PATCH
        body_format: json
        body:
          status: "completed"
          end_time: "{{ ansible_date_time.iso8601 }}"
        headers:
          Authorization: "Bearer {{ deployment_api_token }}"
      when: deployment_tracker_api is defined
```

### Environment-Specific Playbooks
```yaml
# environments/production.yml - Production deployment workflow
---
- name: Production Infrastructure Health Check
  hosts: "{{ target_environment }}"
  gather_facts: yes
  vars:
    health_check_timeout: 30
    
  pre_tasks:
    - name: Verify system requirements
      assert:
        that:
          - ansible_memtotal_mb >= 4096
          - ansible_processor_vcpus >= 2
          - ansible_mounts | selectattr('mount', 'equalto', '/') | map(attribute='size_available') | first > 10737418240  # 10GB
        fail_msg: "System does not meet minimum requirements"
    
    - name: Check critical services
      service_facts:
      
    - name: Ensure critical services are running
      assert:
        that:
          - ansible_facts.services[item + '.service']['state'] == 'running'
        fail_msg: "Critical service {{ item }} is not running"
      loop: "{{ critical_services | default(['ssh', 'rsyslog']) }}"
      when: ansible_facts.services[item + '.service'] is defined

- name: Production Database Tier Deployment
  import_playbook: ../tiers/database.yml
  when: "'database' in deployment_tiers"

- name: Production Application Tier Deployment
  import_playbook: ../tiers/application.yml
  when: "'application' in deployment_tiers"

- name: Production Web Tier Deployment
  import_playbook: ../tiers/web.yml
  when: "'web' in deployment_tiers"

- name: Production Infrastructure Tier Deployment
  import_playbook: ../tiers/infrastructure.yml
  when: "'infrastructure' in deployment_tiers"

- name: Production Post-Deployment Validation
  hosts: "{{ target_environment }}"
  gather_facts: false
  
  tasks:
    - name: Run comprehensive health checks
      include_tasks: ../tasks/health_check.yml
      vars:
        health_check_suite: production
        
    - name: Execute smoke tests
      include_tasks: ../tasks/smoke_tests.yml
      vars:
        test_suite: production
        
    - name: Update monitoring configuration
      include_tasks: ../tasks/monitoring_setup.yml
      vars:
        monitoring_profile: production
        deployment_info: "{{ deployment_metadata }}"
```

### Tier-Specific Playbooks
```yaml
# tiers/application.yml - Application tier deployment
---
- name: Application Services Deployment
  hosts: "{{ target_environment }}:&application_tier"
  become: yes
  serial: "{{ deployment_parallelism | default('25%') }}"
  max_fail_percentage: "{{ max_failure_rate | default(10) }}"
  
  vars:
    app_deployment_dir: "/opt/{{ app_name }}"
    app_config_dir: "/etc/{{ app_name }}"
    app_user: "{{ app_name }}"
    app_group: "{{ app_name }}"
    
  pre_tasks:
    - name: Create deployment backup
      include_tasks: ../tasks/create_backup.yml
      vars:
        backup_type: pre_deployment
        backup_components:
          - application_binaries
          - configuration_files
          - database_schema
          
    - name: Drain load balancer traffic
      include_tasks: ../tasks/load_balancer_drain.yml
      when: deployment_strategy == 'rolling'
      
    - name: Stop application services gracefully
      include_tasks: ../tasks/service_stop.yml
      vars:
        services: "{{ app_services }}"
        stop_timeout: 30
        
  tasks:
    - name: Application Deployment Block
      block:
        - name: Download application artifacts
          get_url:
            url: "{{ artifact_repository_url }}/{{ app_name }}/{{ app_version }}/{{ app_name }}-{{ app_version }}.tar.gz"
            dest: "/tmp/{{ app_name }}-{{ app_version }}.tar.gz"
            headers:
              Authorization: "Bearer {{ artifact_repo_token }}"
            timeout: 300
          
        - name: Verify artifact checksums
          get_url:
            url: "{{ artifact_repository_url }}/{{ app_name }}/{{ app_version }}/{{ app_name }}-{{ app_version }}.tar.gz.sha256"
            dest: "/tmp/{{ app_name }}-{{ app_version }}.tar.gz.sha256"
            headers:
              Authorization: "Bearer {{ artifact_repo_token }}"
          
        - name: Validate artifact integrity
          command: sha256sum -c "/tmp/{{ app_name }}-{{ app_version }}.tar.gz.sha256"
          args:
            chdir: /tmp
            
        - name: Extract application artifacts
          unarchive:
            src: "/tmp/{{ app_name }}-{{ app_version }}.tar.gz"
            dest: "{{ app_deployment_dir }}"
            remote_src: yes
            owner: "{{ app_user }}"
            group: "{{ app_group }}"
            mode: '0755'
            
        - name: Apply configuration templates
          template:
            src: "{{ item.src }}"
            dest: "{{ app_config_dir }}/{{ item.dest }}"
            owner: "{{ app_user }}"
            group: "{{ app_group }}"
            mode: "{{ item.mode | default('0640') }}"
            backup: yes
          loop: "{{ app_config_templates }}"
          notify: reload application configuration
          
        - name: Update application permissions
          file:
            path: "{{ item.path }}"
            owner: "{{ item.owner | default(app_user) }}"
            group: "{{ item.group | default(app_group) }}"
            mode: "{{ item.mode }}"
            state: "{{ item.state | default('file') }}"
          loop: "{{ app_file_permissions }}"
          
        - name: Install application dependencies
          package:
            name: "{{ app_system_dependencies }}"
            state: present
          when: app_system_dependencies is defined
          
        - name: Run database migrations
          command: "{{ app_deployment_dir }}/bin/migrate"
          args:
            chdir: "{{ app_deployment_dir }}"
          environment: "{{ app_environment_vars }}"
          become_user: "{{ app_user }}"
          when: run_migrations | default(false)
          register: migration_result
          
        - name: Start application services
          systemd:
            name: "{{ item }}"
            state: started
            enabled: yes
            daemon_reload: yes
          loop: "{{ app_services }}"
          
        - name: Wait for application to be ready
          uri:
            url: "{{ app_health_check_url }}"
            method: GET
            status_code: 200
            timeout: 10
          register: health_check
          until: health_check.status == 200
          retries: 30
          delay: 10
          
      rescue:
        - name: Application deployment failed - initiating rollback
          include_tasks: ../tasks/rollback.yml
          vars:
            rollback_type: application
            backup_id: "{{ deployment_metadata.id }}"
            
        - name: Notify deployment failure
          include_tasks: ../tasks/notify_failure.yml
          vars:
            failure_type: deployment
            error_details: "{{ ansible_failed_result }}"
            
        - fail:
            msg: "Application deployment failed and rollback completed"
            
      always:
        - name: Cleanup temporary files
          file:
            path: "{{ item }}"
            state: absent
          loop:
            - "/tmp/{{ app_name }}-{{ app_version }}.tar.gz"
            - "/tmp/{{ app_name }}-{{ app_version }}.tar.gz.sha256"
            
  post_tasks:
    - name: Re-enable load balancer traffic
      include_tasks: ../tasks/load_balancer_enable.yml
      when: deployment_strategy == 'rolling'
      
    - name: Register deployment completion
      include_tasks: ../tasks/deployment_registry.yml
      vars:
        deployment_status: success
        
  handlers:
    - name: reload application configuration
      systemd:
        name: "{{ item }}"
        state: reloaded
      loop: "{{ app_services }}"
```

### Advanced Task Management
```yaml
# tasks/health_check.yml - Comprehensive health check framework
---
- name: System Health Check Suite
  block:
    - name: Initialize health check results
      set_fact:
        health_check_results: {}
        health_check_failed: false
        
    - name: System Resource Health Check
      block:
        - name: Check CPU utilization
          shell: |
            awk '{u=$2+$4; t=$2+$4+$5; if (NR==1){u1=u; t1=t;} else print ($2+$4-u1) * 100 / (t-t1); }' \
            <(grep 'cpu ' /proc/stat; sleep 1; grep 'cpu ' /proc/stat)
          register: cpu_usage
          
        - name: Check memory utilization
          shell: |
            free | grep Mem | awk '{printf "%.1f", $3/$2 * 100.0}'
          register: memory_usage
          
        - name: Check disk space
          shell: |
            df -h / | awk 'NR==2 {print $5}' | sed 's/%//'
          register: disk_usage
          
        - name: Evaluate system resources
          set_fact:
            health_check_results: "{{ health_check_results | combine({
              'system_resources': {
                'cpu_usage': cpu_usage.stdout | float,
                'memory_usage': memory_usage.stdout | float,
                'disk_usage': disk_usage.stdout | int,
                'status': 'healthy' if (
                  cpu_usage.stdout | float < resource_thresholds.cpu_warning and
                  memory_usage.stdout | float < resource_thresholds.memory_warning and
                  disk_usage.stdout | int < resource_thresholds.disk_warning
                ) else 'warning'
              }
            }) }}"
            
    - name: Service Health Check
      block:
        - name: Get service status
          service_facts:
          
        - name: Check critical services
          set_fact:
            service_status: "{{ service_status | default({}) | combine({
              item: {
                'status': ansible_facts.services[item + '.service']['state'] if (item + '.service') in ansible_facts.services else 'not_found',
                'enabled': ansible_facts.services[item + '.service']['status'] if (item + '.service') in ansible_facts.services else 'unknown'
              }
            }) }}"
          loop: "{{ critical_services }}"
          
        - name: Evaluate service health
          set_fact:
            health_check_results: "{{ health_check_results | combine({
              'services': {
                'details': service_status,
                'status': 'healthy' if (
                  service_status.values() | map(attribute='status') | select('equalto', 'running') | list | length
                  == critical_services | length
                ) else 'critical'
              }
            }) }}"
            
    - name: Network Connectivity Health Check
      block:
        - name: Test external connectivity
          uri:
            url: "{{ item.url }}"
            method: "{{ item.method | default('GET') }}"
            timeout: "{{ item.timeout | default(10) }}"
            status_code: "{{ item.expected_status | default(200) }}"
          loop: "{{ external_endpoints | default([]) }}"
          register: connectivity_results
          failed_when: false
          
        - name: Test internal service connectivity
          wait_for:
            host: "{{ item.host }}"
            port: "{{ item.port }}"
            timeout: "{{ item.timeout | default(5) }}"
          loop: "{{ internal_endpoints | default([]) }}"
          register: internal_connectivity_results
          failed_when: false
          
        - name: Evaluate network health
          set_fact:
            health_check_results: "{{ health_check_results | combine({
              'connectivity': {
                'external_endpoints': connectivity_results.results | map(attribute='status') | list,
                'internal_endpoints': internal_connectivity_results.results | map(attribute='msg') | list,
                'status': 'healthy' if (
                  connectivity_results.results | selectattr('status', 'equalto', 200) | list | length
                  == external_endpoints | length and
                  internal_connectivity_results.results | selectattr('msg', 'search', 'port is open') | list | length
                  == internal_endpoints | length
                ) else 'degraded'
              }
            }) }}"
            
    - name: Application-Specific Health Check
      block:
        - name: Check application endpoints
          uri:
            url: "{{ item.url }}"
            method: "{{ item.method | default('GET') }}"
            headers: "{{ item.headers | default({}) }}"
            body: "{{ item.body | default(omit) }}"
            timeout: "{{ item.timeout | default(30) }}"
            status_code: "{{ item.expected_status | default(200) }}"
          loop: "{{ app_health_endpoints | default([]) }}"
          register: app_health_results
          failed_when: false
          
        - name: Check database connectivity
          shell: |
            {{ app_deployment_dir }}/bin/health-check --component=database --timeout=10
          register: db_health_check
          failed_when: false
          become_user: "{{ app_user }}"
          when: check_database_health | default(true)
          
        - name: Check cache connectivity
          shell: |
            {{ app_deployment_dir }}/bin/health-check --component=cache --timeout=10
          register: cache_health_check
          failed_when: false
          become_user: "{{ app_user }}"
          when: check_cache_health | default(true)
          
        - name: Evaluate application health
          set_fact:
            health_check_results: "{{ health_check_results | combine({
              'application': {
                'endpoints': app_health_results.results | map(attribute='status') | list,
                'database': db_health_check.rc | default(0),
                'cache': cache_health_check.rc | default(0),
                'status': 'healthy' if (
                  app_health_results.results | selectattr('status', 'defined') | selectattr('status', 'equalto', 200) | list | length
                  == app_health_endpoints | length and
                  (db_health_check.rc | default(0)) == 0 and
                  (cache_health_check.rc | default(0)) == 0
                ) else 'critical'
              }
            }) }}"
            
    - name: Aggregate health check results
      set_fact:
        overall_health_status: "{{
          'healthy' if (
            health_check_results.values() | map(attribute='status') | select('equalto', 'healthy') | list | length
            == health_check_results | length
          ) else (
            'degraded' if 'critical' not in (health_check_results.values() | map(attribute='status') | list)
            else 'critical'
          )
        }}"
        health_check_failed: "{{
          'critical' in (health_check_results.values() | map(attribute='status') | list)
        }}"
        
    - name: Generate health check report
      template:
        src: health_check_report.j2
        dest: "/var/log/ansible-health-check-{{ ansible_date_time.epoch }}.json"
        mode: '0644'
      vars:
        health_summary:
          timestamp: "{{ ansible_date_time.iso8601 }}"
          hostname: "{{ ansible_hostname }}"
          overall_status: "{{ overall_health_status }}"
          details: "{{ health_check_results }}"
          
    - name: Send health check notifications
      uri:
        url: "{{ monitoring_webhook_url }}"
        method: POST
        body_format: json
        body:
          source: "ansible-health-check"
          severity: "{{ 'critical' if health_check_failed else 'info' }}"
          message: "Health check {{ 'failed' if health_check_failed else 'passed' }} on {{ ansible_hostname }}"
          details: "{{ health_check_results }}"
          timestamp: "{{ ansible_date_time.iso8601 }}"
      when: monitoring_webhook_url is defined
      
  rescue:
    - name: Handle health check execution failure
      set_fact:
        health_check_failed: true
        health_check_results: "{{ health_check_results | combine({
          'execution_error': {
            'status': 'critical',
            'error': '{{ ansible_failed_result }}'
          }
        }) }}"
        
  always:
    - name: Log health check completion
      debug:
        msg: "Health check completed with status: {{ overall_health_status | default('unknown') }}"
        
    - name: Fail if critical health issues detected
      fail:
        msg: "Critical health issues detected: {{ health_check_results }}"
      when: health_check_failed and fail_on_health_check | default(true)

# Default health check configuration
- name: Set default health check parameters
  set_fact:
    resource_thresholds:
      cpu_warning: 80
      memory_warning: 85
      disk_warning: 90
    critical_services: "{{ critical_services | default(['ssh', 'rsyslog']) }}"
    external_endpoints: "{{ external_endpoints | default([]) }}"
    internal_endpoints: "{{ internal_endpoints | default([]) }}"
    app_health_endpoints: "{{ app_health_endpoints | default([]) }}"
  when: resource_thresholds is not defined
```

### Blue-Green Deployment Pattern
```yaml
# playbooks/deployment_strategies/blue_green.yml
---
- name: Blue-Green Deployment Strategy
  hosts: "{{ target_environment }}:&{{ service_group }}"
  gather_facts: yes
  vars:
    deployment_strategy: blue_green
    
  pre_tasks:
    - name: Validate blue-green deployment requirements
      assert:
        that:
          - blue_pool is defined
          - green_pool is defined
          - load_balancer_config is defined
        fail_msg: "Blue-green deployment requires blue_pool, green_pool, and load_balancer_config"
        
    - name: Determine current active pool
      uri:
        url: "{{ load_balancer_config.api_url }}/config"
        method: GET
        headers:
          Authorization: "Bearer {{ load_balancer_config.api_token }}"
      register: current_lb_config
      
    - name: Set deployment pools
      set_fact:
        active_pool: "{{ current_lb_config.json.active_pool }}"
        inactive_pool: "{{ 'green' if current_lb_config.json.active_pool == 'blue' else 'blue' }}"
        target_hosts: "{{ groups[inactive_pool + '_pool'] }}"
        
  tasks:
    - name: Deploy to inactive pool
      block:
        - name: Update inactive pool hosts
          include_tasks: ../tasks/application_deployment.yml
          vars:
            target_hosts: "{{ groups[inactive_pool + '_pool'] }}"
            
        - name: Run health checks on inactive pool
          include_tasks: ../tasks/health_check.yml
          vars:
            target_hosts: "{{ groups[inactive_pool + '_pool'] }}"
            health_check_suite: comprehensive
            
        - name: Run smoke tests on inactive pool
          include_tasks: ../tasks/smoke_tests.yml
          vars:
            target_hosts: "{{ groups[inactive_pool + '_pool'] }}"
            test_environment: "{{ inactive_pool }}"
            
        - name: Switch load balancer to inactive pool
          uri:
            url: "{{ load_balancer_config.api_url }}/switch"
            method: POST
            body_format: json
            body:
              target_pool: "{{ inactive_pool }}"
              switch_mode: gradual
              switch_duration: "{{ switch_duration | default(300) }}"
            headers:
              Authorization: "Bearer {{ load_balancer_config.api_token }}"
          register: switch_result
          
        - name: Wait for traffic switch completion
          uri:
            url: "{{ load_balancer_config.api_url }}/status"
            method: GET
            headers:
              Authorization: "Bearer {{ load_balancer_config.api_token }}"
          register: switch_status
          until: switch_status.json.active_pool == inactive_pool
          retries: 60
          delay: 5
          
        - name: Verify post-switch health
          include_tasks: ../tasks/health_check.yml
          vars:
            health_check_suite: post_deployment
            
        - name: Update deployment registry
          uri:
            url: "{{ deployment_registry_url }}/deployments"
            method: POST
            body_format: json
            body:
              deployment_id: "{{ deployment_metadata.id }}"
              strategy: blue_green
              active_pool: "{{ inactive_pool }}"
              inactive_pool: "{{ active_pool }}"
              switch_timestamp: "{{ ansible_date_time.iso8601 }}"
            headers:
              Authorization: "Bearer {{ deployment_registry_token }}"
              
      rescue:
        - name: Blue-green deployment failed - maintaining current pool
          debug:
            msg: "Deployment to {{ inactive_pool }} pool failed, maintaining traffic on {{ active_pool }} pool"
            
        - name: Rollback inactive pool to previous version
          include_tasks: ../tasks/rollback.yml
          vars:
            target_hosts: "{{ groups[inactive_pool + '_pool'] }}"
            rollback_version: "{{ previous_version }}"
            
        - fail:
            msg: "Blue-green deployment failed"
            
  post_tasks:
    - name: Cleanup old version on previously active pool
      include_tasks: ../tasks/cleanup_old_version.yml
      vars:
        target_hosts: "{{ groups[active_pool + '_pool'] }}"
        cleanup_delay: "{{ cleanup_delay | default(1800) }}"  # 30 minutes delay
      when: cleanup_old_versions | default(true)
```

### Canary Deployment Pattern
```yaml
# playbooks/deployment_strategies/canary.yml
---
- name: Canary Deployment Strategy
  hosts: "{{ target_environment }}:&{{ service_group }}"
  gather_facts: yes
  vars:
    deployment_strategy: canary
    canary_percentage: "{{ canary_traffic_percentage | default(10) }}"
    
  pre_tasks:
    - name: Calculate canary host count
      set_fact:
        total_hosts: "{{ groups[service_group] | length }}"
        canary_host_count: "{{ ((groups[service_group] | length * canary_percentage / 100) | round | int) | max(1) }}"
        
    - name: Select canary hosts
      set_fact:
        canary_hosts: "{{ groups[service_group][:canary_host_count] }}"
        production_hosts: "{{ groups[service_group][canary_host_count:] }}"
        
  tasks:
    - name: Phase 1 - Deploy to canary hosts
      block:
        - name: Deploy application to canary hosts
          include_tasks: ../tasks/application_deployment.yml
          vars:
            target_hosts: "{{ canary_hosts }}"
            deployment_phase: canary
            
        - name: Configure load balancer for canary traffic
          uri:
            url: "{{ load_balancer_config.api_url }}/canary"
            method: POST
            body_format: json
            body:
              canary_hosts: "{{ canary_hosts }}"
              traffic_percentage: "{{ canary_percentage }}"
              routing_rules: "{{ canary_routing_rules | default({}) }}"
            headers:
              Authorization: "Bearer {{ load_balancer_config.api_token }}"
              
        - name: Monitor canary deployment metrics
          include_tasks: ../tasks/canary_monitoring.yml
          vars:
            monitoring_duration: "{{ canary_monitoring_duration | default(900) }}"  # 15 minutes
            success_criteria: "{{ canary_success_criteria }}"
            
        - name: Evaluate canary deployment success
          include_tasks: ../tasks/canary_evaluation.yml
          
      rescue:
        - name: Canary deployment failed - rolling back canary hosts
          include_tasks: ../tasks/rollback.yml
          vars:
            target_hosts: "{{ canary_hosts }}"
            
        - name: Remove canary traffic routing
          uri:
            url: "{{ load_balancer_config.api_url }}/canary/remove"
            method: POST
            headers:
              Authorization: "Bearer {{ load_balancer_config.api_token }}"
              
        - fail:
            msg: "Canary deployment failed"
            
    - name: Phase 2 - Full deployment (conditional)
      block:
        - name: Deploy to remaining production hosts
          include_tasks: ../tasks/application_deployment.yml
          vars:
            target_hosts: "{{ production_hosts }}"
            deployment_phase: production
            
        - name: Switch all traffic to new version
          uri:
            url: "{{ load_balancer_config.api_url }}/canary/promote"
            method: POST
            headers:
              Authorization: "Bearer {{ load_balancer_config.api_token }}"
              
      when: canary_evaluation_result.success | default(false)
      
  post_tasks:
    - name: Final health check and monitoring setup
      include_tasks: ../tasks/post_deployment_setup.yml
      when: canary_evaluation_result.success | default(false)
```

This comprehensive playbook guide provides enterprise-grade patterns for complex deployment workflows, advanced task management, error handling, and modern deployment strategies suitable for production environments.