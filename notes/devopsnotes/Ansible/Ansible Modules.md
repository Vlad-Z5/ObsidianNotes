# Enterprise Ansible Modules Guide

Comprehensive module development and utilization patterns for enterprise automation at scale.

## Table of Contents
1. [Core Module Categories](#core-module-categories)
2. [Custom Module Development](#custom-module-development)
3. [Advanced Module Patterns](#advanced-module-patterns)
4. [Cloud Provider Modules](#cloud-provider-modules)
5. [Enterprise Integration](#enterprise-integration)
6. [Module Testing & Quality](#module-testing--quality)
7. [Performance Optimization](#performance-optimization)

## Core Module Categories

### System Management

#### Package Management
```yaml
# Advanced package management with multiple sources
- name: Install packages from multiple sources
  package:
    name: "{{ item.name }}"
    state: "{{ item.state | default('present') }}"
    source: "{{ item.source | default(omit) }}"
  loop:
    - name: nginx
      state: present
    - name: custom-app
      source: https://repo.company.com/custom-app.rpm
    - name: legacy-tool
      state: absent
  register: package_results
  retries: 3
  delay: 10
  until: package_results is succeeded

# Enterprise package verification
- name: Verify package signatures
  shell: |
    {% for pkg in installed_packages %}
    rpm -K {{ pkg }} | grep -q "gpg OK" || exit 1
    {% endfor %}
  vars:
    installed_packages: "{{ ansible_facts.packages.keys() | list }}"
  when: ansible_os_family == "RedHat"
```

#### Service Management
```yaml
# Advanced service orchestration
- name: Orchestrated service management
  block:
    - name: Stop dependent services
      service:
        name: "{{ item }}"
        state: stopped
      loop: "{{ service_dependencies[target_service] | default([]) }}"
      register: dependent_services
      
    - name: Update main service
      service:
        name: "{{ target_service }}"
        state: "{{ target_state }}"
        enabled: "{{ target_enabled | default(true) }}"
      register: main_service
      
    - name: Restart dependent services
      service:
        name: "{{ item }}"
        state: started
      loop: "{{ service_dependencies[target_service] | default([]) }}"
      when: main_service is changed
      
  rescue:
    - name: Rollback service changes
      service:
        name: "{{ item.item }}"
        state: started
      loop: "{{ dependent_services.results | selectattr('changed', 'equalto', true) | list }}"
      ignore_errors: yes
      
  vars:
    service_dependencies:
      nginx:
        - php-fpm
        - redis
      mysql:
        - backup-agent
```

### File Operations

#### Template Processing
```yaml
# Advanced template with validation
- name: Deploy configuration with validation
  block:
    - name: Generate configuration
      template:
        src: "{{ item.template }}"
        dest: "{{ item.dest }}"
        owner: "{{ item.owner | default('root') }}"
        group: "{{ item.group | default('root') }}"
        mode: "{{ item.mode | default('0644') }}"
        backup: yes
        validate: "{{ item.validate | default(omit) }}"
      loop:
        - template: nginx.conf.j2
          dest: /etc/nginx/nginx.conf
          validate: nginx -t -c %s
        - template: app.properties.j2
          dest: /opt/app/config/application.properties
          owner: app
          group: app
          mode: '0600'
      register: template_results
      notify:
        - restart nginx
        - restart application
        
    - name: Verify configuration syntax
      command: "{{ item.item.validate.split()[0] }} -t"
      loop: "{{ template_results.results | selectattr('item.validate', 'defined') | list }}"
      when: item is changed
      changed_when: false
```

## Custom Module Development

### Python Module Structure
```python
#!/usr/bin/env python3
# library/enterprise_database.py

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.database import Database
import json
import traceback

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: enterprise_database
short_description: Enterprise database management module
description:
    - Manages enterprise database operations including schema migration,
      user management, and performance monitoring
version_added: "2.9"
author:
    - Enterprise DevOps Team
options:
    database_url:
        description:
            - Database connection URL
        required: true
        type: str
    operation:
        description:
            - Operation to perform
        required: true
        choices: ['migrate', 'user_create', 'user_delete', 'backup', 'restore']
        type: str
    migration_version:
        description:
            - Target migration version
        required: false
        type: str
    user_config:
        description:
            - User configuration for user operations
        required: false
        type: dict
        suboptions:
            username:
                description: Database username
                type: str
                required: true
            password:
                description: User password
                type: str
                required: true
                no_log: true
            privileges:
                description: User privileges
                type: list
                elements: str
'''

EXAMPLES = '''
- name: Migrate database to latest version
  enterprise_database:
    database_url: "postgresql://user:pass@localhost/mydb"
    operation: migrate
    migration_version: "20231201_001"

- name: Create database user
  enterprise_database:
    database_url: "postgresql://admin:pass@localhost/mydb"
    operation: user_create
    user_config:
      username: app_user
      password: "{{ vault_db_password }}"
      privileges:
        - SELECT
        - INSERT
        - UPDATE
'''

RETURN = '''
operation_result:
    description: Result of the database operation
    returned: always
    type: dict
    sample: {
        "status": "success",
        "affected_rows": 150,
        "migration_version": "20231201_001"
    }
changed:
    description: Whether the operation changed the database state
    returned: always
    type: bool
    sample: true
'''

class EnterpriseDatabase:
    def __init__(self, module):
        self.module = module
        self.database_url = module.params['database_url']
        self.operation = module.params['operation']
        self.migration_version = module.params.get('migration_version')
        self.user_config = module.params.get('user_config', {})
        
    def connect(self):
        try:
            self.db = Database(self.database_url)
            return True
        except Exception as e:
            self.module.fail_json(msg=f"Database connection failed: {str(e)}")
            
    def migrate_database(self):
        try:
            current_version = self.db.get_schema_version()
            target_version = self.migration_version or self.db.get_latest_version()
            
            if current_version == target_version:
                return {'changed': False, 'version': current_version}
                
            migration_result = self.db.migrate_to_version(target_version)
            return {
                'changed': True,
                'previous_version': current_version,
                'current_version': target_version,
                'applied_migrations': migration_result['migrations']
            }
        except Exception as e:
            self.module.fail_json(msg=f"Migration failed: {str(e)}")
            
    def create_user(self):
        try:
            username = self.user_config['username']
            password = self.user_config['password']
            privileges = self.user_config.get('privileges', [])
            
            user_exists = self.db.user_exists(username)
            if user_exists:
                return {'changed': False, 'user': username, 'exists': True}
                
            self.db.create_user(username, password, privileges)
            return {'changed': True, 'user': username, 'privileges': privileges}
        except Exception as e:
            self.module.fail_json(msg=f"User creation failed: {str(e)}")
            
    def execute_operation(self):
        if not self.connect():
            return
            
        operations = {
            'migrate': self.migrate_database,
            'user_create': self.create_user,
            'user_delete': self.delete_user,
            'backup': self.backup_database,
            'restore': self.restore_database
        }
        
        operation_func = operations.get(self.operation)
        if not operation_func:
            self.module.fail_json(msg=f"Unsupported operation: {self.operation}")
            
        return operation_func()

def main():
    module = AnsibleModule(
        argument_spec=dict(
            database_url=dict(type='str', required=True, no_log=True),
            operation=dict(
                type='str',
                required=True,
                choices=['migrate', 'user_create', 'user_delete', 'backup', 'restore']
            ),
            migration_version=dict(type='str', required=False),
            user_config=dict(
                type='dict',
                required=False,
                options=dict(
                    username=dict(type='str', required=True),
                    password=dict(type='str', required=True, no_log=True),
                    privileges=dict(type='list', elements='str', required=False)
                )
            )
        ),
        supports_check_mode=True
    )
    
    try:
        db_manager = EnterpriseDatabase(module)
        result = db_manager.execute_operation()
        module.exit_json(**result)
    except Exception as e:
        module.fail_json(
            msg=f"Module execution failed: {str(e)}",
            traceback=traceback.format_exc()
        )

if __name__ == '__main__':
    main()
```

### Module Usage Examples
```yaml
# Custom module implementation
- name: Enterprise database operations
  block:
    - name: Run database migrations
      enterprise_database:
        database_url: "{{ database_connection_string }}"
        operation: migrate
        migration_version: "{{ target_migration | default(omit) }}"
      register: migration_result
      
    - name: Create application users
      enterprise_database:
        database_url: "{{ database_connection_string }}"
        operation: user_create
        user_config:
          username: "{{ item.username }}"
          password: "{{ item.password }}"
          privileges: "{{ item.privileges }}"
      loop: "{{ database_users }}"
      no_log: true
      
  vars:
    database_users:
      - username: app_readonly
        password: "{{ vault_readonly_password }}"
        privileges: ["SELECT"]
      - username: app_writer
        password: "{{ vault_writer_password }}"
        privileges: ["SELECT", "INSERT", "UPDATE"]
```

## Advanced Module Patterns

### Module Composition
```yaml
# Complex orchestration using multiple modules
- name: Deploy microservice with full stack
  block:
    - name: Configure load balancer
      include_tasks: configure_lb.yml
      vars:
        service_name: "{{ microservice.name }}"
        backend_servers: "{{ microservice.instances }}"
        
    - name: Deploy application containers
      docker_container:
        name: "{{ microservice.name }}-{{ item.id }}"
        image: "{{ microservice.image }}:{{ microservice.version }}"
        ports:
          - "{{ item.port }}:8080"
        env:
          DATABASE_URL: "{{ database_connection_string }}"
          REDIS_URL: "{{ redis_connection_string }}"
          SERVICE_PORT: "{{ item.port }}"
        networks:
          - name: microservice_network
        restart_policy: unless-stopped
        healthcheck:
          test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
          interval: 30s
          timeout: 10s
          retries: 3
      loop: "{{ microservice.instances }}"
      register: container_results
      
    - name: Configure service discovery
      consul_kv:
        key: "services/{{ microservice.name }}/instances/{{ item.item.id }}"
        value: |
          {
            "address": "{{ item.item.address }}",
            "port": {{ item.item.port }},
            "health_check_url": "http://{{ item.item.address }}:{{ item.item.port }}/health",
            "version": "{{ microservice.version }}",
            "deployed_at": "{{ ansible_date_time.iso8601 }}"
          }
      loop: "{{ container_results.results | selectattr('changed', 'equalto', true) | list }}"
      
  rescue:
    - name: Rollback on failure
      include_tasks: rollback_deployment.yml
      vars:
        failed_service: "{{ microservice.name }}"
        rollback_version: "{{ previous_version | default('latest-stable') }}"
```

### Error Handling and Recovery
```yaml
# Comprehensive error handling pattern
- name: Resilient database operation
  block:
    - name: Attempt primary database operation
      postgresql_query:
        db: "{{ primary_database }}"
        query: "{{ complex_query }}"
        positional_args: "{{ query_parameters }}"
      register: primary_result
      timeout: 300
      
  rescue:
    - name: Log primary database failure
      debug:
        msg: "Primary database operation failed: {{ ansible_failed_result.msg }}"
        
    - name: Attempt fallback to read replica
      postgresql_query:
        db: "{{ replica_database }}"
        query: "{{ readonly_fallback_query }}"
        positional_args: "{{ query_parameters }}"
      register: replica_result
      when: operation_type == 'read'
      
    - name: Queue operation for retry
      uri:
        url: "{{ retry_queue_endpoint }}"
        method: POST
        body_format: json
        body:
          operation: "{{ operation_name }}"
          parameters: "{{ query_parameters }}"
          priority: high
          retry_count: 0
          max_retries: 5
      when: operation_type != 'read'
      
  always:
    - name: Record operation metrics
      uri:
        url: "{{ metrics_endpoint }}/database_operations"
        method: POST
        body_format: json
        body:
          operation: "{{ operation_name }}"
          status: "{{ 'success' if primary_result is succeeded else 'failure' }}"
          duration_ms: "{{ (ansible_date_time.epoch | int - operation_start_time | int) * 1000 }}"
          database: "{{ primary_database if primary_result is succeeded else replica_database }}"
      ignore_errors: yes
```

## Cloud Provider Modules

### AWS Integration
```yaml
# Advanced AWS resource management
- name: Deploy AWS infrastructure stack
  block:
    - name: Create VPC with advanced networking
      amazon.aws.ec2_vpc_net:
        name: "{{ environment }}-vpc"
        cidr_block: "{{ vpc_cidr }}"
        dns_support: yes
        dns_hostnames: yes
        tags:
          Environment: "{{ environment }}"
          Project: "{{ project_name }}"
          ManagedBy: ansible
        state: present
      register: vpc_result
      
    - name: Create subnets across availability zones
      amazon.aws.ec2_vpc_subnet:
        vpc_id: "{{ vpc_result.vpc.id }}"
        cidr: "{{ item.cidr }}"
        az: "{{ item.az }}"
        tags:
          Name: "{{ item.name }}"
          Type: "{{ item.type }}"
          Environment: "{{ environment }}"
        state: present
      loop:
        - name: "{{ environment }}-public-subnet-1"
          cidr: "{{ public_subnet_cidrs[0] }}"
          az: "{{ availability_zones[0] }}"
          type: public
        - name: "{{ environment }}-private-subnet-1"
          cidr: "{{ private_subnet_cidrs[0] }}"
          az: "{{ availability_zones[0] }}"
          type: private
      register: subnet_results
      
    - name: Configure auto scaling groups
      amazon.aws.ec2_asg:
        name: "{{ item.name }}"
        launch_config_name: "{{ item.launch_config }}"
        min_size: "{{ item.min_size }}"
        max_size: "{{ item.max_size }}"
        desired_capacity: "{{ item.desired_capacity }}"
        vpc_zone_identifier: "{{ item.subnets }}"
        target_group_arns: "{{ item.target_groups | default([]) }}"
        health_check_type: "{{ item.health_check_type | default('EC2') }}"
        health_check_grace_period: "{{ item.health_check_grace | default(300) }}"
        tags:
          - key: Environment
            value: "{{ environment }}"
            propagate_at_launch: yes
          - key: Service
            value: "{{ item.service }}"
            propagate_at_launch: yes
      loop: "{{ auto_scaling_groups }}"
```

### Azure Integration
```yaml
# Azure Resource Manager operations
- name: Deploy Azure infrastructure
  block:
    - name: Create resource group
      azure.azcollection.azure_rm_resourcegroup:
        name: "{{ resource_group_name }}"
        location: "{{ azure_region }}"
        tags:
          environment: "{{ environment }}"
          project: "{{ project_name }}"
          
    - name: Deploy ARM template
      azure.azcollection.azure_rm_deployment:
        resource_group: "{{ resource_group_name }}"
        template: "{{ arm_template_content }}"
        parameters:
          environment: "{{ environment }}"
          vmSize: "{{ vm_size }}"
          adminPassword: "{{ vault_admin_password }}"
        state: present
      register: arm_deployment
      
    - name: Configure application insights
      azure.azcollection.azure_rm_applicationinsights:
        resource_group: "{{ resource_group_name }}"
        name: "{{ application_insights_name }}"
        location: "{{ azure_region }}"
        application_type: web
        tags:
          environment: "{{ environment }}"
      register: app_insights
```

## Enterprise Integration

### LDAP/Active Directory
```yaml
# Enterprise directory integration
- name: Manage enterprise users and groups
  block:
    - name: Query LDAP for user information
      ldap_search:
        dn: "{{ ldap_base_dn }}"
        scope: subtree
        filter: "(&(objectClass=person)(memberOf={{ required_group_dn }}))"
        attrs:
          - uid
          - mail
          - displayName
          - department
      register: ldap_users
      
    - name: Create local system accounts
      user:
        name: "{{ item.uid[0] }}"
        comment: "{{ item.displayName[0] }}"
        shell: /bin/bash
        groups:
          - "{{ user_groups_mapping[item.department[0]] | default(['users']) }}"
        state: present
      loop: "{{ ldap_users.results }}"
      when: item.uid is defined
      
    - name: Configure SSH access
      authorized_key:
        user: "{{ item.uid[0] }}"
        key: "{{ lookup('file', ssh_key_directory + '/' + item.uid[0] + '.pub') }}"
        state: present
      loop: "{{ ldap_users.results }}"
      when: 
        - item.uid is defined
        - ssh_access_enabled | default(false)
```

### ServiceNow Integration
```yaml
# ServiceNow ticket integration
- name: Create change request for deployment
  uri:
    url: "{{ servicenow_instance }}/api/now/table/change_request"
    method: POST
    headers:
      Authorization: "Bearer {{ servicenow_token }}"
      Content-Type: application/json
    body_format: json
    body:
      short_description: "Automated deployment: {{ application_name }} v{{ version }}"
      description: |
        Automated deployment initiated by Ansible
        Application: {{ application_name }}
        Version: {{ version }}
        Environment: {{ environment }}
        Requested by: {{ ansible_user }}
        Deployment window: {{ deployment_window }}
      category: "Software"
      subcategory: "Application"
      priority: "3"
      risk: "Low"
      impact: "2"
      urgency: "3"
      state: "1"
      requested_by: "{{ servicenow_user_id }}"
  register: change_request
  
- name: Update change request with deployment status
  uri:
    url: "{{ servicenow_instance }}/api/now/table/change_request/{{ change_request.json.result.sys_id }}"
    method: PUT
    headers:
      Authorization: "Bearer {{ servicenow_token }}"
      Content-Type: application/json
    body_format: json
    body:
      state: "{{ '3' if deployment_successful else '4' }}"
      work_notes: |
        Deployment {% if deployment_successful %}completed successfully{% else %}failed{% endif %}
        Deployment time: {{ ansible_date_time.iso8601 }}
        Duration: {{ deployment_duration }} minutes
        {% if not deployment_successful %}
        Error details: {{ deployment_error_details }}
        {% endif %}
  when: change_request is succeeded
```

## Module Testing & Quality

### Unit Testing
```python
# tests/unit/modules/test_enterprise_database.py
import pytest
from unittest.mock import Mock, patch
import sys
import os

# Add the library path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'library'))

from enterprise_database import EnterpriseDatabase, main

class TestEnterpriseDatabase:
    @pytest.fixture
    def mock_module(self):
        module = Mock()
        module.params = {
            'database_url': 'postgresql://test:test@localhost/testdb',
            'operation': 'migrate',
            'migration_version': 'v1.0.0'
        }
        return module
        
    @pytest.fixture
    def enterprise_db(self, mock_module):
        return EnterpriseDatabase(mock_module)
        
    @patch('enterprise_database.Database')
    def test_connect_success(self, mock_database, enterprise_db):
        mock_db_instance = Mock()
        mock_database.return_value = mock_db_instance
        
        result = enterprise_db.connect()
        
        assert result is True
        assert enterprise_db.db == mock_db_instance
        
    @patch('enterprise_database.Database')
    def test_migrate_database_no_change(self, mock_database, enterprise_db):
        mock_db_instance = Mock()
        mock_db_instance.get_schema_version.return_value = 'v1.0.0'
        mock_database.return_value = mock_db_instance
        enterprise_db.db = mock_db_instance
        
        result = enterprise_db.migrate_database()
        
        assert result['changed'] is False
        assert result['version'] == 'v1.0.0'
        
    def test_module_argument_validation(self):
        # Test that invalid arguments are properly handled
        with patch('ansible.module_utils.basic.AnsibleModule') as mock_ansible_module:
            mock_module = Mock()
            mock_module.params = {
                'database_url': 'invalid-url',
                'operation': 'invalid-operation'
            }
            mock_ansible_module.return_value = mock_module
            
            with pytest.raises(Exception):
                main()
```

### Integration Testing
```yaml
# tests/integration/test_enterprise_modules.yml
- name: Test enterprise database module integration
  block:
    - name: Setup test database
      postgresql_db:
        name: ansible_test_db
        state: present
        
    - name: Test database migration
      enterprise_database:
        database_url: "postgresql://postgres:{{ test_db_password }}@localhost/ansible_test_db"
        operation: migrate
        migration_version: "{{ test_migration_version }}"
      register: migration_result
      
    - name: Verify migration result
      assert:
        that:
          - migration_result is succeeded
          - migration_result.changed == true
          - migration_result.current_version == test_migration_version
          
    - name: Test user creation
      enterprise_database:
        database_url: "postgresql://postgres:{{ test_db_password }}@localhost/ansible_test_db"
        operation: user_create
        user_config:
          username: test_user
          password: test_password
          privileges:
            - SELECT
            - INSERT
      register: user_creation_result
      
    - name: Verify user creation
      assert:
        that:
          - user_creation_result is succeeded
          - user_creation_result.changed == true
          - user_creation_result.user == 'test_user'
          
  always:
    - name: Cleanup test database
      postgresql_db:
        name: ansible_test_db
        state: absent
```

## Performance Optimization

### Parallel Execution
```yaml
# Optimized parallel module execution
- name: Parallel system updates
  block:
    - name: Update packages in parallel
      package:
        name: "{{ item }}"
        state: latest
      loop: "{{ system_packages }}"
      async: 600
      poll: 0
      register: package_updates
      
    - name: Wait for package updates to complete
      async_status:
        jid: "{{ item.ansible_job_id }}"
      register: package_update_results
      until: package_update_results.finished
      retries: 60
      delay: 10
      loop: "{{ package_updates.results }}"
      
    - name: Parallel service restarts
      service:
        name: "{{ item }}"
        state: restarted
      loop: "{{ services_to_restart }}"
      async: 300
      poll: 0
      register: service_restarts
      when: package_update_results | selectattr('changed', 'equalto', true) | list | length > 0
      
  vars:
    system_packages:
      - nginx
      - postgresql
      - redis
      - python3
    services_to_restart:
      - nginx
      - postgresql
      - redis
```

### Caching and Optimization
```yaml
# Module result caching for performance
- name: Cached infrastructure queries
  block:
    - name: Check cache for infrastructure state
      stat:
        path: "/tmp/infra_cache_{{ environment }}.json"
      register: cache_file
      
    - name: Load cached infrastructure data
      set_fact:
        infrastructure_state: "{{ lookup('file', '/tmp/infra_cache_' + environment + '.json') | from_json }}"
      when: 
        - cache_file.stat.exists
        - (ansible_date_time.epoch | int - cache_file.stat.mtime) < cache_ttl_seconds
        
    - name: Query infrastructure state
      block:
        - name: Get AWS EC2 instances
          amazon.aws.ec2_instance_info:
            filters:
              "tag:Environment": "{{ environment }}"
              "instance-state-name": running
          register: ec2_instances
          
        - name: Get RDS instances
          amazon.aws.rds_instance_info:
            filters:
              "tag:Environment": "{{ environment }}"
          register: rds_instances
          
        - name: Build infrastructure state
          set_fact:
            infrastructure_state:
              ec2_instances: "{{ ec2_instances.instances }}"
              rds_instances: "{{ rds_instances.instances }}"
              last_updated: "{{ ansible_date_time.epoch }}"
              
        - name: Cache infrastructure state
          copy:
            content: "{{ infrastructure_state | to_nice_json }}"
            dest: "/tmp/infra_cache_{{ environment }}.json"
            
      when: infrastructure_state is not defined
      
  vars:
    cache_ttl_seconds: 3600  # 1 hour cache
```

This comprehensive guide provides enterprise-ready module development patterns, advanced usage examples, and production-quality implementations for Ansible automation at scale.