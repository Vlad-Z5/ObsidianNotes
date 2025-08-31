### Understanding Collections
```yaml
# Collection structure overview
ansible_collections/
├── namespace/
│   └── collection_name/
│       ├── docs/
│       ├── galaxy.yml              # Collection metadata
│       ├── meta/
│       │   └── runtime.yml         # Runtime requirements
│       ├── plugins/
│       │   ├── modules/           # Custom modules
│       │   ├── inventory/         # Inventory plugins
│       │   ├── lookup/            # Lookup plugins
│       │   ├── filter/            # Filter plugins
│       │   ├── callback/          # Callback plugins
│       │   └── connection/        # Connection plugins
│       ├── roles/
│       │   └── role_name/         # Collection roles
│       ├── playbooks/             # Playbooks included in collection
│       ├── tests/
│       │   ├── integration/
│       │   └── unit/
│       └── README.md
```

### galaxy.yml Configuration
```yaml
# galaxy.yml - Collection metadata
namespace: company
name: infrastructure
version: 2.1.0
readme: README.md
authors:
  - "Infrastructure Team <infra@company.com>"
  - "DevOps Team <devops@company.com>"

description: Enterprise infrastructure automation collection
license:
  - Apache-2.0

tags:
  - infrastructure
  - networking
  - security
  - monitoring
  - cloud

dependencies:
  "ansible.posix": ">=1.4.0"
  "community.general": ">=5.0.0"
  "community.crypto": ">=2.0.0"
  "kubernetes.core": ">=2.3.0"

repository: https://github.com/company/ansible-infrastructure-collection
documentation: https://docs.company.com/ansible-collections/infrastructure
homepage: https://company.com/devops-tools
issues: https://github.com/company/ansible-infrastructure-collection/issues

build_ignore:
  - "*.pyc"
  - "*.retry"
  - ".git"
  - "__pycache__"
  - ".pytest_cache"
  - "tests/output"
  - ".vscode"
  - ".idea"

manifest:
  directives:
    - "recursive-include plugins *.py"
    - "recursive-include roles */tasks/*.yml"
    - "recursive-include roles */handlers/*.yml"
    - "recursive-include roles */templates/*"
    - "recursive-include docs *.md *.rst"
```

### Runtime Requirements
```yaml
# meta/runtime.yml - Runtime dependencies
requires_ansible: ">=2.12.0"

plugin_routing:
  # Redirect deprecated modules
  modules:
    old_module_name:
      redirect: company.infrastructure.new_module_name
      deprecation:
        removal_version: "3.0.0"
        warning_text: "This module has been deprecated. Use company.infrastructure.new_module_name instead."
  
  # Filter plugin routing
  filter:
    old_filter:
      redirect: company.infrastructure.new_filter

action_groups:
  # Group related modules for easier imports
  cloud:
    - company.infrastructure.aws_instance
    - company.infrastructure.aws_security_group
    - company.infrastructure.azure_vm
  
  networking:
    - company.infrastructure.firewall_rule
    - company.infrastructure.load_balancer
    - company.infrastructure.dns_record
```

## Collection Development

### Custom Modules Development
```python
#!/usr/bin/python
# plugins/modules/custom_service_manager.py

DOCUMENTATION = '''
---
module: custom_service_manager
short_description: Manage custom application services
description:
  - Start, stop, restart, and manage custom application services
  - Provides advanced health checking and dependency management
version_added: "1.0.0"
options:
  name:
    description:
      - Name of the service to manage
    required: true
    type: str
  state:
    description:
      - Desired state of the service
    choices: ['started', 'stopped', 'restarted', 'reloaded']
    default: started
    type: str
  config_file:
    description:
      - Path to service configuration file
    type: path
  health_check_url:
    description:
      - HTTP endpoint for health checking
    type: str
  health_check_timeout:
    description:
      - Timeout for health check in seconds
    default: 30
    type: int
  dependencies:
    description:
      - List of services that must be running before this service
    type: list
    elements: str
author:
  - Infrastructure Team (@company-infra)
'''

EXAMPLES = '''
- name: Start web application service
  company.infrastructure.custom_service_manager:
    name: webapp
    state: started
    config_file: /etc/webapp/config.yml
    health_check_url: http://localhost:8080/health
    dependencies:
      - database
      - redis

- name: Restart service with dependency check
  company.infrastructure.custom_service_manager:
    name: api-service
    state: restarted
    health_check_timeout: 60
    dependencies:
      - message-queue
'''

RETURN = '''
service_status:
  description: Current status of the service
  returned: always
  type: str
  sample: "running"
health_check_result:
  description: Result of health check if performed
  returned: when health_check_url is provided
  type: dict
  sample:
    status: "healthy"
    response_time: 0.245
    status_code: 200
changed:
  description: Whether the service state was changed
  returned: always
  type: bool
  sample: true
'''

from ansible.module_utils.basic import AnsibleModule
import subprocess
import requests
import time
import json

class ServiceManager:
    def __init__(self, module):
        self.module = module
        self.name = module.params['name']
        self.state = module.params['state']
        self.config_file = module.params['config_file']
        self.health_check_url = module.params['health_check_url']
        self.health_check_timeout = module.params['health_check_timeout']
        self.dependencies = module.params['dependencies'] or []
    
    def get_service_status(self):
        """Get current service status"""
        try:
            result = subprocess.run(
                ['systemctl', 'is-active', self.name],
                capture_output=True,
                text=True
            )
            return result.stdout.strip()
        except Exception as e:
            self.module.fail_json(msg=f"Failed to get service status: {str(e)}")
    
    def check_dependencies(self):
        """Check if all dependencies are running"""
        for dep in self.dependencies:
            try:
                result = subprocess.run(
                    ['systemctl', 'is-active', dep],
                    capture_output=True,
                    text=True
                )
                if result.stdout.strip() != 'active':
                    self.module.fail_json(
                        msg=f"Dependency '{dep}' is not running"
                    )
            except Exception as e:
                self.module.fail_json(
                    msg=f"Failed to check dependency '{dep}': {str(e)}"
                )
    
    def manage_service(self):
        """Manage service state"""
        current_status = self.get_service_status()
        changed = False
        
        if self.state == 'started' and current_status != 'active':
            self.check_dependencies()
            subprocess.run(['systemctl', 'start', self.name], check=True)
            changed = True
        elif self.state == 'stopped' and current_status == 'active':
            subprocess.run(['systemctl', 'stop', self.name], check=True)
            changed = True
        elif self.state == 'restarted':
            self.check_dependencies()
            subprocess.run(['systemctl', 'restart', self.name], check=True)
            changed = True
        elif self.state == 'reloaded':
            subprocess.run(['systemctl', 'reload', self.name], check=True)
            changed = True
        
        return changed
    
    def health_check(self):
        """Perform health check if URL provided"""
        if not self.health_check_url:
            return None
        
        try:
            response = requests.get(
                self.health_check_url,
                timeout=self.health_check_timeout
            )
            return {
                'status': 'healthy' if response.status_code == 200 else 'unhealthy',
                'status_code': response.status_code,
                'response_time': response.elapsed.total_seconds()
            }
        except requests.RequestException as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'response_time': None
            }

def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(type='str', required=True),
            state=dict(
                type='str',
                default='started',
                choices=['started', 'stopped', 'restarted', 'reloaded']
            ),
            config_file=dict(type='path'),
            health_check_url=dict(type='str'),
            health_check_timeout=dict(type='int', default=30),
            dependencies=dict(type='list', elements='str')
        ),
        supports_check_mode=True
    )
    
    service_mgr = ServiceManager(module)
    
    try:
        if module.check_mode:
            current_status = service_mgr.get_service_status()
            module.exit_json(
                changed=False,
                service_status=current_status
            )
        
        changed = service_mgr.manage_service()
        final_status = service_mgr.get_service_status()
        health_result = service_mgr.health_check()
        
        result = {
            'changed': changed,
            'service_status': final_status
        }
        
        if health_result:
            result['health_check_result'] = health_result
        
        module.exit_json(**result)
        
    except subprocess.CalledProcessError as e:
        module.fail_json(msg=f"Service management failed: {str(e)}")
    except Exception as e:
        module.fail_json(msg=f"Unexpected error: {str(e)}")

if __name__ == '__main__':
    main()
```

### Custom Filter Plugins
```python
# plugins/filter/infrastructure_filters.py

import re
import ipaddress
from ansible.errors import AnsibleFilterError

class FilterModule:
    """Custom filters for infrastructure automation"""
    
    def filters(self):
        return {
            'extract_version': self.extract_version,
            'normalize_hostname': self.normalize_hostname,
            'subnet_hosts': self.subnet_hosts,
            'service_port_map': self.service_port_map,
            'health_status': self.health_status,
            'resource_tags': self.resource_tags
        }
    
    def extract_version(self, value, pattern=r'v?(\d+\.\d+\.\d+)'):
        """Extract semantic version from string"""
        if not isinstance(value, str):
            raise AnsibleFilterError('extract_version filter requires string input')
        
        match = re.search(pattern, value)
        if match:
            return match.group(1)
        return None
    
    def normalize_hostname(self, hostname, max_length=63):
        """Normalize hostname according to RFC standards"""
        if not isinstance(hostname, str):
            raise AnsibleFilterError('normalize_hostname filter requires string input')
        
        # Convert to lowercase
        normalized = hostname.lower()
        
        # Replace invalid characters with hyphens
        normalized = re.sub(r'[^a-z0-9\-]', '-', normalized)
        
        # Remove leading/trailing hyphens
        normalized = normalized.strip('-')
        
        # Ensure length limit
        if len(normalized) > max_length:
            normalized = normalized[:max_length].rstrip('-')
        
        return normalized
    
    def subnet_hosts(self, subnet_cidr, exclude_network=True, exclude_broadcast=True):
        """Generate list of host IPs from subnet CIDR"""
        try:
            network = ipaddress.ip_network(subnet_cidr, strict=False)
            hosts = list(network.hosts())
            
            if not exclude_network and not exclude_broadcast:
                return [str(ip) for ip in network]
            elif not exclude_network:
                return [str(network.network_address)] + [str(ip) for ip in hosts]
            elif not exclude_broadcast:
                return [str(ip) for ip in hosts] + [str(network.broadcast_address)]
            else:
                return [str(ip) for ip in hosts]
                
        except ValueError as e:
            raise AnsibleFilterError(f'Invalid subnet CIDR: {e}')
    
    def service_port_map(self, services, default_ports=None):
        """Map services to their default ports"""
        if default_ports is None:
            default_ports = {
                'http': 80,
                'https': 443,
                'ssh': 22,
                'ftp': 21,
                'mysql': 3306,
                'postgresql': 5432,
                'redis': 6379,
                'mongodb': 27017,
                'elasticsearch': 9200,
                'kibana': 5601,
                'grafana': 3000,
                'prometheus': 9090
            }
        
        if isinstance(services, str):
            services = [services]
        
        result = {}
        for service in services:
            service_name = service.lower()
            result[service] = default_ports.get(service_name, None)
        
        return result
    
    def health_status(self, checks):
        """Aggregate health check results"""
        if not isinstance(checks, list):
            raise AnsibleFilterError('health_status filter requires list input')
        
        healthy_count = 0
        total_count = len(checks)
        
        for check in checks:
            if isinstance(check, dict) and check.get('status') == 'healthy':
                healthy_count += 1
            elif check == 'healthy' or check is True:
                healthy_count += 1
        
        health_percentage = (healthy_count / total_count * 100) if total_count > 0 else 0
        
        return {
            'overall_status': 'healthy' if healthy_count == total_count else 'degraded' if healthy_count > 0 else 'unhealthy',
            'healthy_count': healthy_count,
            'total_count': total_count,
            'health_percentage': round(health_percentage, 2)
        }
    
    def resource_tags(self, resources, tag_key, tag_value=None):
        """Filter resources by tags"""
        if not isinstance(resources, list):
            raise AnsibleFilterError('resource_tags filter requires list input')
        
        filtered = []
        
        for resource in resources:
            if not isinstance(resource, dict):
                continue
            
            tags = resource.get('tags', {})
            
            if tag_value is None:
                # Just check if tag key exists
                if tag_key in tags:
                    filtered.append(resource)
            else:
                # Check for specific tag value
                if tags.get(tag_key) == tag_value:
                    filtered.append(resource)
        
        return filtered
```

### Custom Inventory Plugin
```python
# plugins/inventory/custom_cmdb.py

DOCUMENTATION = '''
    inventory: custom_cmdb
    plugin_type: inventory
    short_description: Custom CMDB inventory source
    description:
        - Generates inventory from custom Configuration Management Database
        - Supports filtering by environment, service type, and location
        - Provides automatic grouping and host variables
    options:
        plugin:
            description: Token that ensures this is a source file for the plugin
            required: True
            choices: ['custom_cmdb', 'company.infrastructure.custom_cmdb']
        cmdb_url:
            description: URL of the CMDB API endpoint
            required: True
            type: str
            env:
                - name: CMDB_URL
        api_token:
            description: API token for CMDB authentication
            required: True
            type: str
            env:
                - name: CMDB_API_TOKEN
        environment:
            description: Filter by environment
            type: str
            choices: ['production', 'staging', 'development']
        service_types:
            description: Filter by service types
            type: list
            elements: str
        locations:
            description: Filter by datacenter locations
            type: list
            elements: str
        include_inactive:
            description: Include inactive hosts
            type: bool
            default: false
'''

EXAMPLES = '''
# inventory.yml
plugin: company.infrastructure.custom_cmdb
cmdb_url: https://cmdb.company.com/api/v1
api_token: "{{ vault_cmdb_token }}"
environment: production
service_types:
  - webserver
  - database
  - loadbalancer
locations:
  - us-east-1
  - us-west-2
include_inactive: false

# Compose host variables
compose:
  ansible_host: network.primary_ip
  ansible_user: "{{ 'root' if os_family == 'RedHat' else 'ubuntu' }}"
  instance_type: hardware.instance_type
  
# Create groups
keyed_groups:
  - key: service_type
    prefix: service
  - key: environment
    prefix: env
  - key: location
    prefix: location
  - key: os_family
    prefix: os
'''

from ansible.plugins.inventory import BaseInventoryPlugin, Constructable, Cacheable
from ansible.errors import AnsibleError, AnsibleParserError
import requests
import json

class InventoryModule(BaseInventoryPlugin, Constructable, Cacheable):
    
    NAME = 'company.infrastructure.custom_cmdb'
    
    def __init__(self):
        super(InventoryModule, self).__init__()
        self.cmdb_url = None
        self.api_token = None
        self.session = None
    
    def verify_file(self, path):
        """Verify that the source file is applicable for this plugin"""
        valid = False
        if super(InventoryModule, self).verify_file(path):
            if path.endswith(('.cmdb.yml', '.cmdb.yaml')):
                valid = True
            elif self.get_option('plugin') in ('custom_cmdb', 'company.infrastructure.custom_cmdb'):
                valid = True
        return valid
    
    def parse(self, inventory, loader, path, cache=True):
        """Parse the inventory file"""
        super(InventoryModule, self).parse(inventory, loader, path, cache)
        
        # Get configuration
        self._read_config_data(path)
        
        self.cmdb_url = self.get_option('cmdb_url')
        self.api_token = self.get_option('api_token')
        
        if not self.cmdb_url or not self.api_token:
            raise AnsibleParserError('cmdb_url and api_token are required')
        
        # Setup HTTP session
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {self.api_token}',
            'Content-Type': 'application/json'
        })
        
        # Get cache key
        cache_key = self.get_cache_key(path)
        
        # Try to use cache
        user_cache_setting = self.get_option('cache')
        attempt_to_read_cache = user_cache_setting and cache
        cache_needs_update = user_cache_setting and not cache
        
        if attempt_to_read_cache:
            try:
                results = self.cache.get(cache_key)
                if results:
                    self._populate_inventory(results)
                    return
            except KeyError:
                cache_needs_update = True
        
        # Fetch data from CMDB
        try:
            results = self._fetch_hosts()
            self._populate_inventory(results)
            
            # Update cache if needed
            if user_cache_setting:
                self.cache.set(cache_key, results)
                
        except Exception as e:
            raise AnsibleError(f'Failed to fetch inventory from CMDB: {str(e)}')
    
    def _fetch_hosts(self):
        """Fetch hosts from CMDB API"""
        # Build query parameters
        params = {}
        
        if self.get_option('environment'):
            params['environment'] = self.get_option('environment')
        
        if self.get_option('service_types'):
            params['service_types'] = ','.join(self.get_option('service_types'))
        
        if self.get_option('locations'):
            params['locations'] = ','.join(self.get_option('locations'))
        
        if not self.get_option('include_inactive'):
            params['status'] = 'active'
        
        # Make API request
        url = f"{self.cmdb_url}/hosts"
        response = self.session.get(url, params=params)
        response.raise_for_status()
        
        return response.json()
    
    def _populate_inventory(self, data):
        """Populate inventory with CMDB data"""
        
        # Process each host
        for host_data in data.get('hosts', []):
            hostname = host_data.get('hostname')
            if not hostname:
                continue
            
            # Add host to inventory
            self.inventory.add_host(hostname)
            
            # Set host variables
            for key, value in host_data.items():
                if key != 'hostname':
                    self.inventory.set_variable(hostname, key, value)
            
            # Create groups based on attributes
            self._create_groups(hostname, host_data)
        
        # Apply constructed features (compose, keyed_groups, groups)
        for host in self.inventory.hosts:
            host_vars = self.inventory.get_host(host).get_vars()
            
            # Apply compose
            self._set_composite_vars(
                self.get_option('compose'),
                host_vars,
                host
            )
            
            # Apply keyed_groups
            self._add_host_to_keyed_groups(
                self.get_option('keyed_groups'),
                host_vars,
                host
            )
            
            # Apply groups
            self._add_host_to_composed_groups(
                self.get_option('groups'),
                host_vars,
                host
            )
    
    def _create_groups(self, hostname, host_data):
        """Create standard groups"""
        
        # Environment group
        if 'environment' in host_data:
            env_group = f"env_{host_data['environment']}"
            self.inventory.add_group(env_group)
            self.inventory.add_host_to_group(env_group, hostname)
        
        # Service type group
        if 'service_type' in host_data:
            service_group = f"service_{host_data['service_type']}"
            self.inventory.add_group(service_group)
            self.inventory.add_host_to_group(service_group, hostname)
        
        # Location group
        if 'location' in host_data:
            location_group = f"location_{host_data['location']}"
            self.inventory.add_group(location_group)
            self.inventory.add_host_to_group(location_group, hostname)
        
        # OS family group
        if 'os_family' in host_data:
            os_group = f"os_{host_data['os_family']}"
            self.inventory.add_group(os_group)
            self.inventory.add_host_to_group(os_group, hostname)
```

## Collection Testing & Validation

### Molecule Testing Framework
```yaml
# molecule/default/molecule.yml
---
dependency:
  name: galaxy
  options:
    requirements-file: requirements.yml
    
driver:
  name: docker

platforms:
  - name: ubuntu-20-04
    image: ubuntu:20.04
    dockerfile: ../common/Dockerfile.ubuntu.j2
    command: /lib/systemd/systemd
    volumes:
      - /sys/fs/cgroup:/sys/fs/cgroup:ro
    privileged: true
    
  - name: centos-8
    image: centos:8
    dockerfile: ../common/Dockerfile.centos.j2
    command: /usr/lib/systemd/systemd
    volumes:
      - /sys/fs/cgroup:/sys/fs/cgroup:ro
    privileged: true

provisioner:
  name: ansible
  inventory:
    host_vars:
      ubuntu-20-04:
        ansible_python_interpreter: /usr/bin/python3
      centos-8:
        ansible_python_interpreter: /usr/bin/python3
  config_options:
    defaults:
      callbacks_enabled: timer,profile_tasks
      stdout_callback: yaml
  
verifier:
  name: ansible
  
scenario:
  test_sequence:
    - dependency
    - cleanup
    - destroy
    - syntax
    - create
    - prepare
    - converge
    - idempotence
    - side_effect
    - verify
    - cleanup
    - destroy
```

### Integration Tests
```yaml
# tests/integration/targets/custom_service_manager/tasks/main.yml
---
- name: Test service manager module
  block:
    - name: Install test service
      copy:
        dest: /etc/systemd/system/test-service.service
        content: |
          [Unit]
          Description=Test Service
          After=network.target
          
          [Service]
          Type=simple
          ExecStart=/bin/bash -c 'while true; do echo "Service running"; sleep 10; done'
          Restart=always
          
          [Install]
          WantedBy=multi-user.target
      notify: reload systemd
    
    - name: Flush handlers
      meta: flush_handlers
    
    - name: Test starting service
      company.infrastructure.custom_service_manager:
        name: test-service
        state: started
      register: result
    
    - name: Assert service was started
      assert:
        that:
          - result.changed
          - result.service_status == 'active'
    
    - name: Test idempotent start
      company.infrastructure.custom_service_manager:
        name: test-service
        state: started
      register: result
    
    - name: Assert no change on idempotent run
      assert:
        that:
          - not result.changed
          - result.service_status == 'active'
    
    - name: Test stopping service
      company.infrastructure.custom_service_manager:
        name: test-service
        state: stopped
      register: result
    
    - name: Assert service was stopped
      assert:
        that:
          - result.changed
          - result.service_status == 'inactive'
    
    - name: Test service with health check
      company.infrastructure.custom_service_manager:
        name: test-service
        state: started
        health_check_url: http://localhost:8080/health
      register: result
      ignore_errors: yes
    
    - name: Assert health check was performed
      assert:
        that:
          - result.health_check_result is defined
          - result.health_check_result.status == 'unhealthy'

  handlers:
    - name: reload systemd
      systemd:
        daemon_reload: yes

  always:
    - name: Cleanup test service
      file:
        path: /etc/systemd/system/test-service.service
        state: absent
      notify: reload systemd
    
    - name: Stop test service if running
      systemd:
        name: test-service
        state: stopped
      ignore_errors: yes
```

## Collection Distribution & Management

### Private Galaxy Server Setup
```yaml
# docker-compose.yml for private Galaxy
version: '3.8'

services:
  galaxy-web:
    image: ansible/galaxy:4.6.0
    environment:
      - GALAXY_API_ROOT=/api/galaxy
      - GALAXY_UI_ROOT=/
      - GALAXY_CONTENT_PATH=/var/lib/galaxy
      - DATABASE_URL=postgresql://galaxy:galaxypassword@postgres:5432/galaxy
      - REDIS_URL=redis://redis:6379/0
    ports:
      - "80:8000"
    volumes:
      - galaxy_data:/var/lib/galaxy
    depends_on:
      - postgres
      - redis
    
  galaxy-worker:
    image: ansible/galaxy:4.6.0
    environment:
      - DATABASE_URL=postgresql://galaxy:galaxypassword@postgres:5432/galaxy
      - REDIS_URL=redis://redis:6379/0
    command: manage.py celeryd
    volumes:
      - galaxy_data:/var/lib/galaxy
    depends_on:
      - postgres
      - redis
  
  postgres:
    image: postgres:13
    environment:
      - POSTGRES_DB=galaxy
      - POSTGRES_USER=galaxy
      - POSTGRES_PASSWORD=galaxypassword
    volumes:
      - postgres_data:/var/lib/postgresql/data
  
  redis:
    image: redis:6.2
    volumes:
      - redis_data:/data

volumes:
  galaxy_data:
  postgres_data:
  redis_data:
```

### Collection CI/CD Pipeline
```yaml
# .github/workflows/collection-ci.yml
name: Collection CI/CD

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]
  release:
    types: [ published ]

jobs:
  sanity:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.8, 3.9, '3.10']
        ansible-version: [2.12, 2.13, 2.14]
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v3
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install Ansible ${{ matrix.ansible-version }}
      run: |
        pip install ansible-core==${{ matrix.ansible-version }}.*
    
    - name: Run sanity tests
      run: |
        ansible-test sanity --docker -v
  
  integration:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        test-target:
          - custom_service_manager
          - infrastructure_filters
          - custom_cmdb
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v3
      with:
        python-version: '3.10'
    
    - name: Install dependencies
      run: |
        pip install ansible-core docker
    
    - name: Run integration tests
      run: |
        ansible-test integration ${{ matrix.test-target }} --docker -v
  
  molecule:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        scenario: [default, centos, ubuntu]
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v3
      with:
        python-version: '3.10'
    
    - name: Install dependencies
      run: |
        pip install molecule[docker] ansible-core
    
    - name: Run Molecule tests
      run: |
        molecule test -s ${{ matrix.scenario }}
      env:
        PY_COLORS: '1'
        ANSIBLE_FORCE_COLOR: '1'
  
  build-and-publish:
    if: github.event_name == 'release'
    runs-on: ubuntu-latest
    needs: [sanity, integration, molecule]
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v3
      with:
        python-version: '3.10'
    
    - name: Install dependencies
      run: |
        pip install ansible-core
    
    - name: Build collection
      run: |
        ansible-galaxy collection build
    
    - name: Publish to Galaxy
      run: |
        ansible-galaxy collection publish *.tar.gz --api-key=${{ secrets.GALAXY_API_KEY }}
    
    - name: Publish to private Galaxy
      run: |
        ansible-galaxy collection publish *.tar.gz \
          --server https://galaxy.company.com \
          --api-key=${{ secrets.PRIVATE_GALAXY_API_KEY }}
```

This comprehensive guide provides enterprise-level collection development practices with custom modules, plugins, testing frameworks, and distribution strategies for managing Ansible content at scale.