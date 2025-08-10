## Infrastructure Automation with Python

### Terraform Integration
```python
import subprocess
import json
import os
from typing import Dict, List, Optional, Any
from pathlib import Path

class TerraformManager:
    """Production Terraform automation with Python"""
    
    def __init__(self, terraform_dir: str, env: str = 'production'):
        self.terraform_dir = Path(terraform_dir)
        self.env = env
        self.state_file = f"terraform.{env}.tfstate"
        self.var_file = f"{env}.tfvars"
        self.logger = logging.getLogger(__name__)
    
    def init(self, backend_config: Optional[Dict[str, str]] = None) -> bool:
        """Initialize Terraform with backend configuration"""
        cmd = ['terraform', 'init']
        
        if backend_config:
            for key, value in backend_config.items():
                cmd.extend(['-backend-config', f'{key}={value}'])
        
        return self._run_terraform_command(cmd)
    
    def plan(self, var_file: Optional[str] = None, 
             destroy: bool = False) -> Tuple[bool, str]:
        """Generate Terraform plan"""
        cmd = ['terraform', 'plan']
        
        if var_file or self.var_file:
            cmd.extend(['-var-file', var_file or self.var_file])
        
        if destroy:
            cmd.append('-destroy')
        
        cmd.extend(['-out', f'{self.env}.tfplan'])
        
        success, output = self._run_terraform_command(cmd, capture_output=True)
        return success, output
    
    def apply(self, plan_file: Optional[str] = None, 
              auto_approve: bool = False) -> bool:
        """Apply Terraform changes"""
        cmd = ['terraform', 'apply']
        
        if plan_file:
            cmd.append(plan_file)
        elif auto_approve:
            cmd.append('-auto-approve')
        
        return self._run_terraform_command(cmd)
    
    def destroy(self, auto_approve: bool = False) -> bool:
        """Destroy Terraform-managed infrastructure"""
        if self.env == 'production' and not auto_approve:
            self.logger.error("Refusing to destroy production without explicit approval")
            return False
        
        cmd = ['terraform', 'destroy']
        
        if auto_approve:
            cmd.append('-auto-approve')
        
        if self.var_file:
            cmd.extend(['-var-file', self.var_file])
        
        return self._run_terraform_command(cmd)
    
    def get_outputs(self) -> Dict[str, Any]:
        """Get Terraform outputs as dictionary"""
        cmd = ['terraform', 'output', '-json']
        success, output = self._run_terraform_command(cmd, capture_output=True)
        
        if not success:
            return {}
        
        try:
            outputs = json.loads(output)
            # Extract values from Terraform output format
            return {k: v['value'] for k, v in outputs.items()}
        except json.JSONDecodeError:
            self.logger.error("Failed to parse Terraform outputs as JSON")
            return {}
    
    def validate_configuration(self) -> bool:
        """Validate Terraform configuration"""
        cmd = ['terraform', 'validate']
        return self._run_terraform_command(cmd)
    
    def format_code(self) -> bool:
        """Format Terraform code"""
        cmd = ['terraform', 'fmt', '-recursive']
        return self._run_terraform_command(cmd)
    
    def get_state_resources(self) -> List[Dict[str, Any]]:
        """Get resources from Terraform state"""
        cmd = ['terraform', 'state', 'list']
        success, output = self._run_terraform_command(cmd, capture_output=True)
        
        if not success:
            return []
        
        resources = []
        for line in output.strip().split('\n'):
            if line:
                # Get detailed resource info
                cmd_show = ['terraform', 'state', 'show', line]
                success_show, resource_output = self._run_terraform_command(
                    cmd_show, capture_output=True
                )
                
                if success_show:
                    resources.append({
                        'address': line,
                        'details': resource_output
                    })
        
        return resources
    
    def _run_terraform_command(self, cmd: List[str], 
                              capture_output: bool = False) -> Any:
        """Execute Terraform command with error handling"""
        env = os.environ.copy()
        env['TF_IN_AUTOMATION'] = '1'
        env['TF_INPUT'] = '0'
        
        try:
            self.logger.info(f"Executing: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                cwd=self.terraform_dir,
                env=env,
                capture_output=capture_output,
                text=True,
                timeout=1800  # 30 minutes timeout
            )
            
            if capture_output:
                if result.returncode == 0:
                    return True, result.stdout
                else:
                    self.logger.error(f"Command failed: {result.stderr}")
                    return False, result.stderr
            else:
                return result.returncode == 0
                
        except subprocess.TimeoutExpired:
            self.logger.error("Terraform command timed out")
            return (False, "Command timed out") if capture_output else False
        except Exception as e:
            self.logger.error(f"Failed to execute Terraform command: {e}")
            return (False, str(e)) if capture_output else False

# Infrastructure deployment automation
class InfrastructureDeployment:
    """Automated infrastructure deployment workflow"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.terraform = TerraformManager(
            config['terraform_dir'], 
            config['environment']
        )
        self.logger = logging.getLogger(__name__)
    
    def deploy(self, dry_run: bool = False) -> bool:
        """Complete infrastructure deployment workflow"""
        try:
            # Step 1: Validate configuration
            self.logger.info("Validating Terraform configuration...")
            if not self.terraform.validate_configuration():
                self.logger.error("Terraform validation failed")
                return False
            
            # Step 2: Initialize Terraform
            self.logger.info("Initializing Terraform...")
            backend_config = self.config.get('backend_config', {})
            if not self.terraform.init(backend_config):
                self.logger.error("Terraform initialization failed")
                return False
            
            # Step 3: Generate and review plan
            self.logger.info("Generating Terraform plan...")
            success, plan_output = self.terraform.plan()
            if not success:
                self.logger.error("Terraform plan generation failed")
                return False
            
            self.logger.info(f"Terraform plan:\n{plan_output}")
            
            # Step 4: Apply changes (if not dry run)
            if dry_run:
                self.logger.info("DRY RUN: Skipping Terraform apply")
                return True
            
            self.logger.info("Applying Terraform changes...")
            if not self.terraform.apply(f"{self.config['environment']}.tfplan"):
                self.logger.error("Terraform apply failed")
                return False
            
            # Step 5: Verify deployment
            self.logger.info("Verifying deployment...")
            return self._verify_deployment()
            
        except Exception as e:
            self.logger.error(f"Deployment failed: {e}")
            return False
    
    def _verify_deployment(self) -> bool:
        """Verify infrastructure deployment"""
        outputs = self.terraform.get_outputs()
        
        # Check required outputs exist
        required_outputs = self.config.get('required_outputs', [])
        for output_name in required_outputs:
            if output_name not in outputs:
                self.logger.error(f"Missing required output: {output_name}")
                return False
        
        # Health checks for deployed resources
        health_checks = self.config.get('health_checks', [])
        for check in health_checks:
            if not self._run_health_check(check, outputs):
                return False
        
        self.logger.info("Deployment verification successful")
        return True
    
    def _run_health_check(self, check: Dict[str, Any], 
                         outputs: Dict[str, Any]) -> bool:
        """Run individual health check"""
        check_type = check['type']
        
        if check_type == 'http':
            return self._http_health_check(check, outputs)
        elif check_type == 'tcp':
            return self._tcp_health_check(check, outputs)
        elif check_type == 'command':
            return self._command_health_check(check, outputs)
        
        self.logger.warning(f"Unknown health check type: {check_type}")
        return True
    
    def _http_health_check(self, check: Dict[str, Any], 
                          outputs: Dict[str, Any]) -> bool:
        """HTTP endpoint health check"""
        import requests
        
        url = check['url'].format(**outputs)
        expected_status = check.get('expected_status', 200)
        timeout = check.get('timeout', 30)
        
        try:
            response = requests.get(url, timeout=timeout)
            if response.status_code == expected_status:
                self.logger.info(f"HTTP health check passed: {url}")
                return True
            else:
                self.logger.error(f"HTTP health check failed: {url} returned {response.status_code}")
                return False
                
        except requests.RequestException as e:
            self.logger.error(f"HTTP health check failed: {url} - {e}")
            return False
```

### Ansible Integration
```python
import ansible_runner
from ansible.parsing.dataloader import DataLoader
from ansible.vars.manager import VariableManager
from ansible.inventory.manager import InventoryManager
from ansible.executor.playbook_executor import PlaybookExecutor
import tempfile
import yaml

class AnsibleAutomation:
    """Python-Ansible integration for configuration management"""
    
    def __init__(self, inventory_path: str, vault_password: Optional[str] = None):
        self.inventory_path = inventory_path
        self.vault_password = vault_password
        self.logger = logging.getLogger(__name__)
    
    def run_playbook(self, playbook_path: str, 
                    extra_vars: Optional[Dict[str, Any]] = None,
                    limit: Optional[str] = None,
                    dry_run: bool = False) -> bool:
        """Execute Ansible playbook"""
        
        # Prepare extra variables
        if extra_vars is None:
            extra_vars = {}
        
        if dry_run:
            extra_vars['ansible_check_mode'] = True
        
        try:
            # Run playbook using ansible-runner
            result = ansible_runner.run(
                playbook=playbook_path,
                inventory=self.inventory_path,
                extravars=extra_vars,
                limit=limit,
                quiet=False,
                verbosity=1
            )
            
            # Check results
            if result.status == 'successful':
                self.logger.info(f"Playbook {playbook_path} completed successfully")
                return True
            else:
                self.logger.error(f"Playbook {playbook_path} failed: {result.status}")
                self._log_ansible_failures(result)
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to run playbook {playbook_path}: {e}")
            return False
    
    def run_ad_hoc_command(self, module: str, module_args: str,
                          hosts: str = 'all') -> Dict[str, Any]:
        """Run ad-hoc Ansible command"""
        try:
            result = ansible_runner.run(
                module=module,
                module_args=module_args,
                inventory=self.inventory_path,
                host_pattern=hosts
            )
            
            return {
                'status': result.status,
                'events': list(result.events),
                'stats': result.stats
            }
            
        except Exception as e:
            self.logger.error(f"Failed to run ad-hoc command: {e}")
            return {'status': 'failed', 'error': str(e)}
    
    def generate_dynamic_inventory(self, aws_instances: List[Dict]) -> str:
        """Generate Ansible inventory from AWS instances"""
        inventory = {
            'all': {
                'hosts': {},
                'vars': {}
            },
            '_meta': {
                'hostvars': {}
            }
        }
        
        for instance in aws_instances:
            instance_id = instance['InstanceId']
            private_ip = instance.get('PrivateIpAddress')
            public_ip = instance.get('PublicIpAddress')
            tags = instance.get('Tags', {})
            
            # Use private IP if available, otherwise public IP
            ansible_host = private_ip or public_ip
            if not ansible_host:
                continue
            
            inventory['all']['hosts'][instance_id] = {}
            inventory['_meta']['hostvars'][instance_id] = {
                'ansible_host': ansible_host,
                'instance_type': instance.get('InstanceType'),
                'aws_instance_id': instance_id,
                'aws_state': instance.get('State', {}).get('Name'),
                'aws_tags': tags
            }
            
            # Group by environment and service tags
            environment = tags.get('Environment', 'unknown')
            service = tags.get('Service', 'unknown')
            
            for group_name in [environment, service, f"{environment}_{service}"]:
                if group_name not in inventory:
                    inventory[group_name] = {'hosts': []}
                inventory[group_name]['hosts'].append(instance_id)
        
        # Write to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            yaml.dump(inventory, f, default_flow_style=False)
            return f.name
    
    def _log_ansible_failures(self, result):
        """Log detailed failure information"""
        for event in result.events:
            if event.get('event') == 'runner_on_failed':
                host = event.get('event_data', {}).get('host')
                task = event.get('event_data', {}).get('task')
                msg = event.get('event_data', {}).get('res', {}).get('msg', 'Unknown error')
                self.logger.error(f"Task '{task}' failed on host '{host}': {msg}")

# Configuration deployment workflow
class ConfigurationDeployment:
    """Automated configuration deployment using Ansible"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.ansible = AnsibleAutomation(config['inventory_path'])
        self.logger = logging.getLogger(__name__)
    
    def deploy_configuration(self, service: str, environment: str, 
                           dry_run: bool = False) -> bool:
        """Deploy service configuration to environment"""
        
        playbook_path = self.config['playbooks'][service]
        extra_vars = {
            'environment': environment,
            'service': service,
            **self.config.get('extra_vars', {})
        }
        
        # Add environment-specific variables
        env_vars_file = f"vars/{environment}.yml"
        if os.path.exists(env_vars_file):
            with open(env_vars_file, 'r') as f:
                env_vars = yaml.safe_load(f)
                extra_vars.update(env_vars)
        
        self.logger.info(f"Deploying {service} configuration to {environment}")
        
        return self.ansible.run_playbook(
            playbook_path=playbook_path,
            extra_vars=extra_vars,
            limit=f"{environment}_{service}",
            dry_run=dry_run
        )
    
    def health_check_services(self, services: List[str], 
                            environment: str) -> Dict[str, bool]:
        """Run health checks on deployed services"""
        results = {}
        
        for service in services:
            self.logger.info(f"Health checking {service} in {environment}")
            
            result = self.ansible.run_ad_hoc_command(
                module='uri',
                module_args=f'url=http://localhost:{self.config["service_ports"][service]}/health',
                hosts=f"{environment}_{service}"
            )
            
            results[service] = result['status'] == 'successful'
        
        return results
```

### Infrastructure Monitoring
```python
import psutil
import time
from typing import Dict, List, Any
from dataclasses import dataclass
from datetime import datetime

@dataclass
class SystemMetrics:
    """System metrics data class"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    network_bytes_sent: int
    network_bytes_recv: int
    process_count: int

class InfrastructureMonitor:
    """Infrastructure monitoring and alerting"""
    
    def __init__(self, alert_thresholds: Dict[str, float]):
        self.alert_thresholds = alert_thresholds
        self.metrics_history: List[SystemMetrics] = []
        self.logger = logging.getLogger(__name__)
    
    def collect_system_metrics(self) -> SystemMetrics:
        """Collect current system metrics"""
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Memory usage
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        
        # Disk usage (root partition)
        disk = psutil.disk_usage('/')
        disk_percent = (disk.used / disk.total) * 100
        
        # Network statistics
        network = psutil.net_io_counters()
        
        # Process count
        process_count = len(psutil.pids())
        
        metrics = SystemMetrics(
            timestamp=datetime.now(),
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            disk_percent=disk_percent,
            network_bytes_sent=network.bytes_sent,
            network_bytes_recv=network.bytes_recv,
            process_count=process_count
        )
        
        self.metrics_history.append(metrics)
        
        # Keep only last 100 metrics
        if len(self.metrics_history) > 100:
            self.metrics_history.pop(0)
        
        return metrics
    
    def check_alert_conditions(self, metrics: SystemMetrics) -> List[str]:
        """Check if any alert conditions are met"""
        alerts = []
        
        if metrics.cpu_percent > self.alert_thresholds.get('cpu', 80):
            alerts.append(f"High CPU usage: {metrics.cpu_percent:.1f}%")
        
        if metrics.memory_percent > self.alert_thresholds.get('memory', 80):
            alerts.append(f"High memory usage: {metrics.memory_percent:.1f}%")
        
        if metrics.disk_percent > self.alert_thresholds.get('disk', 80):
            alerts.append(f"High disk usage: {metrics.disk_percent:.1f}%")
        
        if metrics.process_count > self.alert_thresholds.get('processes', 500):
            alerts.append(f"High process count: {metrics.process_count}")
        
        return alerts
    
    def get_top_processes(self, by: str = 'cpu', limit: int = 10) -> List[Dict]:
        """Get top processes by CPU or memory usage"""
        processes = []
        
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                processes.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        # Sort by specified metric
        if by == 'cpu':
            processes.sort(key=lambda x: x['cpu_percent'] or 0, reverse=True)
        elif by == 'memory':
            processes.sort(key=lambda x: x['memory_percent'] or 0, reverse=True)
        
        return processes[:limit]
    
    def generate_health_report(self) -> Dict[str, Any]:
        """Generate comprehensive system health report"""
        current_metrics = self.collect_system_metrics()
        alerts = self.check_alert_conditions(current_metrics)
        top_cpu_processes = self.get_top_processes('cpu', 5)
        top_memory_processes = self.get_top_processes('memory', 5)
        
        # Calculate trends if we have enough history
        trends = {}
        if len(self.metrics_history) >= 10:
            recent = self.metrics_history[-10:]
            older = self.metrics_history[-20:-10] if len(self.metrics_history) >= 20 else recent
            
            trends['cpu'] = sum(m.cpu_percent for m in recent) / len(recent) - sum(m.cpu_percent for m in older) / len(older)
            trends['memory'] = sum(m.memory_percent for m in recent) / len(recent) - sum(m.memory_percent for m in older) / len(older)
        
        return {
            'timestamp': current_metrics.timestamp.isoformat(),
            'current_metrics': {
                'cpu_percent': current_metrics.cpu_percent,
                'memory_percent': current_metrics.memory_percent,
                'disk_percent': current_metrics.disk_percent,
                'process_count': current_metrics.process_count
            },
            'alerts': alerts,
            'trends': trends,
            'top_processes': {
                'cpu': top_cpu_processes,
                'memory': top_memory_processes
            }
        }
```

This provides comprehensive Python tooling for infrastructure automation, covering Terraform integration, Ansible automation, and system monitoring with practical, production-ready examples.