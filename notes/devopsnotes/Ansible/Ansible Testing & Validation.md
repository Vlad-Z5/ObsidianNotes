### Testing Pyramid for Ansible
```yaml
# Ansible Testing Layers
testing_layers:
  unit_tests:
    description: "Test individual modules and plugins"
    tools: ["pytest", "unittest", "mock"]
    scope: "Module logic, filter plugins, lookup plugins"
    
  integration_tests:
    description: "Test role and playbook functionality"
    tools: ["ansible-test", "molecule", "testinfra"]
    scope: "Role execution, task integration, system state"
    
  system_tests:
    description: "End-to-end infrastructure testing"
    tools: ["molecule", "kitchen", "terraform"]
    scope: "Complete deployments, multi-node scenarios"
    
  acceptance_tests:
    description: "Business requirement validation"
    tools: ["serverspec", "inspec", "goss"]
    scope: "Application functionality, compliance"
```

## Unit Testing Framework

### Testing Custom Modules
```python
# tests/unit/modules/test_custom_service_manager.py
import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from ansible.module_utils import basic
from ansible.module_utils._text import to_bytes

# Import the module to test
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..', 'plugins/modules'))
from custom_service_manager import ServiceManager, main

class TestCustomServiceManager:
    
    @pytest.fixture
    def mock_module(self):
        """Create a mock Ansible module"""
        mock_module = Mock()
        mock_module.params = {
            'name': 'test-service',
            'state': 'started',
            'config_file': '/etc/test-service/config.yml',
            'health_check_url': 'http://localhost:8080/health',
            'health_check_timeout': 30,
            'dependencies': ['database', 'redis']
        }
        mock_module.check_mode = False
        return mock_module
    
    @pytest.fixture
    def service_manager(self, mock_module):
        """Create ServiceManager instance"""
        return ServiceManager(mock_module)
    
    @patch('subprocess.run')
    def test_get_service_status_active(self, mock_subprocess, service_manager):
        """Test getting active service status"""
        # Mock subprocess response
        mock_result = Mock()
        mock_result.stdout.strip.return_value = 'active'
        mock_subprocess.return_value = mock_result
        
        status = service_manager.get_service_status()
        
        assert status == 'active'
        mock_subprocess.assert_called_once_with(
            ['systemctl', 'is-active', 'test-service'],
            capture_output=True,
            text=True
        )
    
    @patch('subprocess.run')
    def test_get_service_status_inactive(self, mock_subprocess, service_manager):
        """Test getting inactive service status"""
        mock_result = Mock()
        mock_result.stdout.strip.return_value = 'inactive'
        mock_subprocess.return_value = mock_result
        
        status = service_manager.get_service_status()
        assert status == 'inactive'
    
    @patch('subprocess.run')
    def test_check_dependencies_success(self, mock_subprocess, service_manager):
        """Test successful dependency check"""
        # Mock all dependencies as active
        mock_result = Mock()
        mock_result.stdout.strip.return_value = 'active'
        mock_subprocess.return_value = mock_result
        
        # Should not raise exception
        service_manager.check_dependencies()
        
        # Verify both dependencies were checked
        assert mock_subprocess.call_count == 2
        expected_calls = [
            patch.call(['systemctl', 'is-active', 'database'], 
                      capture_output=True, text=True),
            patch.call(['systemctl', 'is-active', 'redis'], 
                      capture_output=True, text=True)
        ]
        mock_subprocess.assert_has_calls(expected_calls, any_order=True)
    
    @patch('subprocess.run')
    def test_check_dependencies_failure(self, mock_subprocess, service_manager):
        """Test failed dependency check"""
        mock_result = Mock()
        mock_result.stdout.strip.return_value = 'inactive'
        mock_subprocess.return_value = mock_result
        
        # Should call module.fail_json
        service_manager.check_dependencies()
        service_manager.module.fail_json.assert_called_once()
    
    @patch('requests.get')
    def test_health_check_success(self, mock_requests, service_manager):
        """Test successful health check"""
        # Mock successful HTTP response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.elapsed.total_seconds.return_value = 0.5
        mock_requests.return_value = mock_response
        
        result = service_manager.health_check()
        
        assert result['status'] == 'healthy'
        assert result['status_code'] == 200
        assert result['response_time'] == 0.5
    
    @patch('requests.get')
    def test_health_check_failure(self, mock_requests, service_manager):
        """Test failed health check"""
        # Mock HTTP error
        mock_requests.side_effect = Exception('Connection refused')
        
        result = service_manager.health_check()
        
        assert result['status'] == 'unhealthy'
        assert 'error' in result
        assert result['response_time'] is None
    
    def test_health_check_no_url(self, service_manager):
        """Test health check when no URL provided"""
        service_manager.health_check_url = None
        
        result = service_manager.health_check()
        assert result is None

# Integration test for the main function
class TestModuleIntegration:
    
    @patch('custom_service_manager.ServiceManager')
    @patch('ansible.module_utils.basic.AnsibleModule')
    def test_main_success_scenario(self, mock_ansible_module, mock_service_manager):
        """Test main function success scenario"""
        # Setup mocks
        mock_module_instance = Mock()
        mock_module_instance.check_mode = False
        mock_ansible_module.return_value = mock_module_instance
        
        mock_service_manager_instance = Mock()
        mock_service_manager_instance.manage_service.return_value = True
        mock_service_manager_instance.get_service_status.return_value = 'active'
        mock_service_manager_instance.health_check.return_value = {
            'status': 'healthy',
            'status_code': 200,
            'response_time': 0.3
        }
        mock_service_manager.return_value = mock_service_manager_instance
        
        # Call main function
        with patch('sys.argv', ['custom_service_manager.py']):
            main()
        
        # Verify module.exit_json was called with expected results
        expected_result = {
            'changed': True,
            'service_status': 'active',
            'health_check_result': {
                'status': 'healthy',
                'status_code': 200,
                'response_time': 0.3
            }
        }
        mock_module_instance.exit_json.assert_called_once_with(**expected_result)

# Test runner configuration
if __name__ == '__main__':
    pytest.main([__file__, '-v'])
```

### Testing Filter Plugins
```python
# tests/unit/plugins/test_infrastructure_filters.py
import pytest
from ansible.errors import AnsibleFilterError

# Import filter plugin
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..', 'plugins/filter'))
from infrastructure_filters import FilterModule

class TestInfrastructureFilters:
    
    @pytest.fixture
    def filter_module(self):
        """Create filter module instance"""
        return FilterModule()
    
    def test_extract_version_semantic(self, filter_module):
        """Test semantic version extraction"""
        filters = filter_module.filters()
        extract_version = filters['extract_version']
        
        # Test cases
        test_cases = [
            ('v1.2.3', '1.2.3'),
            ('release-2.1.0', '2.1.0'),
            ('app_v3.0.15_build', '3.0.15'),
            ('1.0.0', '1.0.0'),
            ('no-version-here', None)
        ]
        
        for input_val, expected in test_cases:
            result = extract_version(input_val)
            assert result == expected, f"Failed for input: {input_val}"
    
    def test_extract_version_custom_pattern(self, filter_module):
        """Test version extraction with custom pattern"""
        filters = filter_module.filters()
        extract_version = filters['extract_version']
        
        result = extract_version('build-123', r'build-(\d+)')
        assert result == '123'
    
    def test_extract_version_invalid_input(self, filter_module):
        """Test version extraction with invalid input"""
        filters = filter_module.filters()
        extract_version = filters['extract_version']
        
        with pytest.raises(AnsibleFilterError):
            extract_version(123)  # Non-string input
    
    def test_normalize_hostname(self, filter_module):
        """Test hostname normalization"""
        filters = filter_module.filters()
        normalize_hostname = filters['normalize_hostname']
        
        test_cases = [
            ('My-Server_01', 'my-server-01'),
            ('SERVER.EXAMPLE.COM', 'server-example-com'),
            ('web@server#1', 'web-server-1'),
            ('-leading-trailing-', 'leading-trailing'),
            ('a' * 70, 'a' * 63)  # Length limit
        ]
        
        for input_val, expected in test_cases:
            result = normalize_hostname(input_val)
            assert result == expected, f"Failed for input: {input_val}"
    
    def test_subnet_hosts(self, filter_module):
        """Test subnet host generation"""
        filters = filter_module.filters()
        subnet_hosts = filters['subnet_hosts']
        
        # Test /30 network (2 hosts)
        result = subnet_hosts('192.168.1.0/30')
        expected = ['192.168.1.1', '192.168.1.2']
        assert result == expected
        
        # Test with network and broadcast included
        result = subnet_hosts('192.168.1.0/30', 
                            exclude_network=False, 
                            exclude_broadcast=False)
        expected = ['192.168.1.0', '192.168.1.1', '192.168.1.2', '192.168.1.3']
        assert result == expected
    
    def test_service_port_map(self, filter_module):
        """Test service port mapping"""
        filters = filter_module.filters()
        service_port_map = filters['service_port_map']
        
        # Test single service
        result = service_port_map('http')
        assert result == {'http': 80}
        
        # Test multiple services
        result = service_port_map(['http', 'https', 'ssh'])
        expected = {'http': 80, 'https': 443, 'ssh': 22}
        assert result == expected
        
        # Test unknown service
        result = service_port_map('unknown-service')
        assert result == {'unknown-service': None}
    
    def test_health_status(self, filter_module):
        """Test health status aggregation"""
        filters = filter_module.filters()
        health_status = filters['health_status']
        
        # All healthy
        checks = [
            {'status': 'healthy'},
            {'status': 'healthy'},
            'healthy'
        ]
        result = health_status(checks)
        assert result['overall_status'] == 'healthy'
        assert result['healthy_count'] == 3
        assert result['health_percentage'] == 100.0
        
        # Mixed health
        checks = [
            {'status': 'healthy'},
            {'status': 'unhealthy'},
            'healthy'
        ]
        result = health_status(checks)
        assert result['overall_status'] == 'degraded'
        assert result['healthy_count'] == 2
        assert result['health_percentage'] == 66.67
    
    def test_resource_tags(self, filter_module):
        """Test resource tag filtering"""
        filters = filter_module.filters()
        resource_tags = filters['resource_tags']
        
        resources = [
            {'name': 'web01', 'tags': {'Environment': 'production', 'Role': 'web'}},
            {'name': 'db01', 'tags': {'Environment': 'production', 'Role': 'db'}},
            {'name': 'test01', 'tags': {'Environment': 'staging', 'Role': 'web'}}
        ]
        
        # Filter by environment
        result = resource_tags(resources, 'Environment', 'production')
        assert len(result) == 2
        assert all(r['tags']['Environment'] == 'production' for r in result)
        
        # Filter by tag existence
        result = resource_tags(resources, 'Role')
        assert len(result) == 3  # All have Role tag
```

## Integration Testing with Molecule

### Molecule Configuration
```yaml
# molecule/default/molecule.yml
---
dependency:
  name: galaxy
  options:
    requirements-file: requirements.yml
    force: true

driver:
  name: docker

platforms:
  - name: ubuntu-20.04
    image: ubuntu:20.04
    dockerfile: ../common/Dockerfile.ubuntu.j2
    command: /lib/systemd/systemd
    volumes:
      - /sys/fs/cgroup:/sys/fs/cgroup:ro
    privileged: true
    published_ports:
      - "8080:8080"
    environment:
      container: docker
    
  - name: centos-8
    image: centos:8
    dockerfile: ../common/Dockerfile.centos.j2
    command: /usr/lib/systemd/systemd
    volumes:
      - /sys/fs/cgroup:/sys/fs/cgroup:ro
    privileged: true
    environment:
      container: docker

provisioner:
  name: ansible
  inventory:
    host_vars:
      ubuntu-20.04:
        ansible_python_interpreter: /usr/bin/python3
        test_service_port: 8080
      centos-8:
        ansible_python_interpreter: /usr/bin/python3
        test_service_port: 8081
    group_vars:
      all:
        test_environment: molecule
  config_options:
    defaults:
      callbacks_enabled: timer,profile_tasks
      stdout_callback: yaml
      host_key_checking: false
    ssh_connection:
      pipelining: true
  
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

### Dockerfile Templates
```dockerfile
# molecule/common/Dockerfile.ubuntu.j2
FROM ubuntu:20.04

ENV DEBIAN_FRONTEND=noninteractive

# Install systemd and other requirements
RUN apt-get update && \
    apt-get install -y \
        systemd \
        systemd-sysv \
        python3 \
        python3-pip \
        sudo \
        curl \
        wget \
        ca-certificates \
        gnupg \
        lsb-release && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Configure systemd
RUN systemctl set-default multi-user.target && \
    systemctl mask \
        dev-hugepages.mount \
        sys-fs-fuse-connections.mount \
        sys-kernel-config.mount \
        display-manager.service \
        getty@.service \
        systemd-logind.service \
        systemd-remount-fs.service \
        getty.target \
        graphical.target

# Create ansible user
RUN useradd -m -s /bin/bash ansible && \
    echo 'ansible ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers

VOLUME ["/sys/fs/cgroup"]

CMD ["/lib/systemd/systemd"]
```

### Molecule Test Scenarios
```yaml
# molecule/default/prepare.yml
---
- name: Prepare test environment
  hosts: all
  become: true
  gather_facts: false
  
  tasks:
    - name: Wait for system to become reachable
      wait_for_connection:
        timeout: 60
    
    - name: Gather facts
      setup:
    
    - name: Install test dependencies
      package:
        name:
          - curl
          - netcat
        state: present
    
    - name: Create test application directory
      file:
        path: /opt/test-app
        state: directory
        owner: root
        group: root
        mode: '0755'
    
    - name: Create test service script
      copy:
        dest: /opt/test-app/test-service.py
        mode: '0755'
        content: |
          #!/usr/bin/env python3
          import http.server
          import socketserver
          import json
          import os
          
          PORT = int(os.environ.get('PORT', 8080))
          
          class HealthHandler(http.server.SimpleHTTPRequestHandler):
              def do_GET(self):
                  if self.path == '/health':
                      self.send_response(200)
                      self.send_header('Content-type', 'application/json')
                      self.end_headers()
                      response = {'status': 'healthy', 'service': 'test-app'}
                      self.wfile.write(json.dumps(response).encode())
                  else:
                      self.send_response(404)
                      self.end_headers()
          
          with socketserver.TCPServer(("", PORT), HealthHandler) as httpd:
              print(f"Serving on port {PORT}")
              httpd.serve_forever()
    
    - name: Create systemd service file
      copy:
        dest: /etc/systemd/system/test-app.service
        content: |
          [Unit]
          Description=Test Application
          After=network.target
          
          [Service]
          Type=simple
          User=root
          WorkingDirectory=/opt/test-app
          ExecStart=/usr/bin/python3 /opt/test-app/test-service.py
          Environment=PORT={{ test_service_port }}
          Restart=always
          RestartSec=3
          
          [Install]
          WantedBy=multi-user.target
      notify: reload systemd
    
    - name: Enable test service
      systemd:
        name: test-app
        enabled: yes
        daemon_reload: yes
  
  handlers:
    - name: reload systemd
      systemd:
        daemon_reload: yes
```

```yaml
# molecule/default/converge.yml
---
- name: Converge
  hosts: all
  become: true
  
  roles:
    - role: test_role
      vars:
        service_name: test-app
        service_port: "{{ test_service_port }}"
        health_check_enabled: true
        health_check_url: "http://localhost:{{ test_service_port }}/health"
```

```yaml
# molecule/default/verify.yml
---
- name: Verify deployment
  hosts: all
  become: true
  gather_facts: false
  
  tasks:
    - name: Check if service is running
      systemd:
        name: test-app
      register: service_status
    
    - name: Assert service is active
      assert:
        that:
          - service_status.status.ActiveState == "active"
        fail_msg: "Service is not running"
    
    - name: Wait for service to be ready
      wait_for:
        port: "{{ test_service_port }}"
        host: "{{ ansible_host | default('localhost') }}"
        delay: 5
        timeout: 30
    
    - name: Test health endpoint
      uri:
        url: "http://localhost:{{ test_service_port }}/health"
        method: GET
        return_content: yes
        status_code: 200
      register: health_response
    
    - name: Verify health response
      assert:
        that:
          - health_response.json.status == "healthy"
          - health_response.json.service == "test-app"
        fail_msg: "Health check failed"
    
    - name: Test service restart functionality
      systemd:
        name: test-app
        state: restarted
    
    - name: Wait after restart
      wait_for:
        port: "{{ test_service_port }}"
        host: "{{ ansible_host | default('localhost') }}"
        delay: 5
        timeout: 30
    
    - name: Verify service still healthy after restart
      uri:
        url: "http://localhost:{{ test_service_port }}/health"
        method: GET
        status_code: 200
```

## Advanced Testing Patterns

### Testinfra Integration
```python
# molecule/default/tests/test_default.py
import os
import pytest
import testinfra.utils.ansible_runner

testinfra_hosts = testinfra.utils.ansible_runner.AnsibleRunner(
    os.environ['MOLECULE_INVENTORY_FILE']
).get_hosts('all')

class TestApplicationDeployment:
    
    def test_service_file_exists(self, host):
        """Test that systemd service file exists"""
        service_file = host.file("/etc/systemd/system/test-app.service")
        assert service_file.exists
        assert service_file.user == "root"
        assert service_file.group == "root"
        assert service_file.mode == 0o644
    
    def test_application_directory(self, host):
        """Test application directory structure"""
        app_dir = host.file("/opt/test-app")
        assert app_dir.exists
        assert app_dir.is_directory
        assert app_dir.user == "root"
        assert app_dir.group == "root"
        assert app_dir.mode == 0o755
    
    def test_application_script(self, host):
        """Test application script exists and is executable"""
        script = host.file("/opt/test-app/test-service.py")
        assert script.exists
        assert script.is_file
        assert script.mode == 0o755
    
    def test_service_is_running(self, host):
        """Test that the service is running"""
        service = host.service("test-app")
        assert service.is_running
        assert service.is_enabled
    
    def test_service_listening_on_port(self, host):
        """Test that service is listening on correct port"""
        # Get port from host variables (default to 8080)
        port = host.ansible.get_variables().get('test_service_port', 8080)
        
        socket = host.socket(f"tcp://0.0.0.0:{port}")
        assert socket.is_listening
    
    def test_health_endpoint_responds(self, host):
        """Test health endpoint is accessible"""
        port = host.ansible.get_variables().get('test_service_port', 8080)
        
        # Use curl to test the endpoint
        cmd = host.run(f"curl -s http://localhost:{port}/health")
        assert cmd.rc == 0
        assert "healthy" in cmd.stdout
        assert "test-app" in cmd.stdout
    
    def test_service_logs(self, host):
        """Test service generates logs"""
        cmd = host.run("journalctl -u test-app --no-pager -n 10")
        assert cmd.rc == 0
        assert "Serving on port" in cmd.stdout or len(cmd.stdout) > 0
    
    def test_service_restart_resilience(self, host):
        """Test service can be restarted successfully"""
        # Restart the service
        cmd = host.run("systemctl restart test-app")
        assert cmd.rc == 0
        
        # Wait a moment for startup
        import time
        time.sleep(2)
        
        # Check it's still running
        service = host.service("test-app")
        assert service.is_running
        
        # Check health endpoint still works
        port = host.ansible.get_variables().get('test_service_port', 8080)
        cmd = host.run(f"curl -s http://localhost:{port}/health")
        assert cmd.rc == 0
        assert "healthy" in cmd.stdout

class TestSystemConfiguration:
    
    def test_python3_installed(self, host):
        """Test Python 3 is installed"""
        python = host.package("python3")
        assert python.is_installed
    
    def test_curl_installed(self, host):
        """Test curl is installed"""
        curl = host.package("curl")
        assert curl.is_installed
    
    def test_systemd_available(self, host):
        """Test systemd is available"""
        cmd = host.run("systemctl --version")
        assert cmd.rc == 0
        assert "systemd" in cmd.stdout
    
    @pytest.mark.parametrize("user", [
        "root",
        "ansible"
    ])
    def test_users_exist(self, host, user):
        """Test required users exist"""
        user_obj = host.user(user)
        assert user_obj.exists
    
    def test_sudo_configuration(self, host):
        """Test sudo is configured correctly"""
        cmd = host.run("sudo -l -U ansible")
        assert cmd.rc == 0
        assert "NOPASSWD:ALL" in cmd.stdout
```

### Property-Based Testing
```python
# tests/property/test_inventory_generation.py
from hypothesis import given, strategies as st, assume
import json
from ansible.inventory.manager import InventoryManager
from ansible.parsing.dataloader import DataLoader

class TestInventoryProperties:
    
    @given(
        hostnames=st.lists(
            st.text(
                alphabet=st.characters(whitelist_categories=['Ll', 'Lu', 'Nd']),
                min_size=1, 
                max_size=20
            ),
            min_size=1,
            max_size=50,
            unique=True
        ),
        environments=st.sampled_from(['dev', 'staging', 'production'])
    )
    def test_inventory_generation_properties(self, hostnames, environments):
        """Property-based test for inventory generation"""
        assume(all(len(h) > 0 for h in hostnames))
        assume(all(h.isalnum() for h in hostnames))
        
        # Create test inventory data
        inventory_data = {
            'all': {
                'children': {
                    environments: {
                        'hosts': {
                            host: {
                                'ansible_host': f"192.168.1.{i+1}",
                                'environment': environments
                            }
                            for i, host in enumerate(hostnames)
                        }
                    }
                }
            }
        }
        
        # Test properties that should always hold
        loader = DataLoader()
        inventory = InventoryManager(loader=loader)
        
        # Add hosts to inventory
        for host in hostnames:
            inventory.add_host(host, group=environments)
            inventory.set_variable(host, 'environment', environments)
        
        # Properties to verify
        assert len(inventory.get_hosts()) == len(hostnames)
        assert all(inventory.get_host(host) is not None for host in hostnames)
        assert environments in inventory.groups
        assert len(inventory.get_hosts(pattern=environments)) == len(hostnames)
    
    @given(
        group_names=st.lists(
            st.text(alphabet='abcdefghijklmnopqrstuvwxyz', min_size=1, max_size=10),
            min_size=1,
            max_size=10,
            unique=True
        )
    )
    def test_group_hierarchy_properties(self, group_names):
        """Test group hierarchy maintains consistency"""
        assume(all(len(g) > 0 for g in group_names))
        
        loader = DataLoader()
        inventory = InventoryManager(loader=loader)
        
        # Create group hierarchy
        for i, group_name in enumerate(group_names):
            inventory.add_group(group_name)
            if i > 0:
                # Make each group a child of the previous one
                parent_group = group_names[i-1]
                inventory.add_child(parent_group, group_name)
        
        # Properties that should hold
        assert len(inventory.groups) >= len(group_names)  # Including 'all' and 'ungrouped'
        
        # Each group should exist
        for group_name in group_names:
            assert group_name in inventory.groups
        
        # Parent-child relationships should be consistent
        for i in range(1, len(group_names)):
            child_group = group_names[i]
            parent_group = group_names[i-1]
            assert child_group in inventory.groups[parent_group].child_groups
```

### Compliance Testing Framework
```yaml
# tests/compliance/security_compliance.yml
---
- name: Security Compliance Tests
  hosts: all
  become: true
  gather_facts: true
  
  vars:
    compliance_checks:
      - name: ssh_config
        description: "SSH configuration meets security standards"
      - name: user_accounts
        description: "User account security"
      - name: file_permissions
        description: "Critical file permissions"
      - name: service_security
        description: "Service security configuration"
  
  tasks:
    - name: Check SSH configuration
      block:
        - name: Verify SSH protocol version
          lineinfile:
            path: /etc/ssh/sshd_config
            regexp: '^Protocol'
            line: 'Protocol 2'
          check_mode: yes
          register: ssh_protocol
        
        - name: Verify root login disabled
          lineinfile:
            path: /etc/ssh/sshd_config
            regexp: '^PermitRootLogin'
            line: 'PermitRootLogin no'
          check_mode: yes
          register: root_login
        
        - name: Record SSH compliance
          set_fact:
            ssh_compliance:
              protocol_v2: "{{ not ssh_protocol.changed }}"
              root_login_disabled: "{{ not root_login.changed }}"
      
      tags: ssh_config
    
    - name: Check user account security
      block:
        - name: Get user accounts with shell access
          shell: |
            getent passwd | awk -F: '$7 ~ /bash|sh/ {print $1}' | grep -v root
          register: shell_users
          changed_when: false
        
        - name: Check for accounts without passwords
          shell: |
            awk -F: '($2 == "") {print $1}' /etc/shadow
          register: no_password_users
          changed_when: false
        
        - name: Record user account compliance
          set_fact:
            user_compliance:
              shell_user_count: "{{ shell_users.stdout_lines | length }}"
              accounts_without_password: "{{ no_password_users.stdout_lines | length == 0 }}"
      
      tags: user_accounts
    
    - name: Check critical file permissions
      block:
        - name: Check /etc/passwd permissions
          stat:
            path: /etc/passwd
          register: passwd_stat
        
        - name: Check /etc/shadow permissions
          stat:
            path: /etc/shadow
          register: shadow_stat
        
        - name: Record file permission compliance
          set_fact:
            file_compliance:
              passwd_permissions: "{{ passwd_stat.stat.mode == '0644' }}"
              shadow_permissions: "{{ shadow_stat.stat.mode == '0600' }}"
              shadow_owner: "{{ shadow_stat.stat.uid == 0 }}"
      
      tags: file_permissions
    
    - name: Generate compliance report
      template:
        src: compliance_report.j2
        dest: /tmp/compliance_report_{{ ansible_hostname }}.json
      vars:
        compliance_results:
          hostname: "{{ ansible_hostname }}"
          timestamp: "{{ ansible_date_time.iso8601 }}"
          checks:
            ssh:
              status: "{{ ssh_compliance.protocol_v2 and ssh_compliance.root_login_disabled }}"
              details: "{{ ssh_compliance }}"
            users:
              status: "{{ user_compliance.accounts_without_password }}"
              details: "{{ user_compliance }}"
            files:
              status: "{{ file_compliance.passwd_permissions and file_compliance.shadow_permissions and file_compliance.shadow_owner }}"
              details: "{{ file_compliance }}"
      
      tags: report
```

This comprehensive testing framework provides multiple layers of validation for Ansible automation, from unit testing of individual components to full system compliance verification, ensuring reliable and secure infrastructure deployment.