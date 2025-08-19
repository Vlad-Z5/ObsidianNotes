# AWS OpsWorks - Enterprise Configuration Management & DevOps Automation

AWS OpsWorks provides configuration management using Chef and Puppet for automated deployment, scaling, and management of applications across environments. This comprehensive platform enables organizations to implement Infrastructure as Code, automate configuration drift detection, and maintain consistent environments at scale.

## Enterprise OpsWorks Framework

```python
import boto3
import json
import logging
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import yaml
import base64
import hashlib

class StackType(Enum):
    CHEF_11 = "chef11"
    CHEF_12 = "chef12"
    PUPPET = "puppet"

class LayerType(Enum):
    AWS_FLOW_RUBY = "aws-flow-ruby"
    ECS_CLUSTER = "ecs-cluster"
    JAVA_APP = "java-app"
    LB = "lb"
    WEB = "web"
    PHP_APP = "php-app"
    RAILS_APP = "rails-app"
    NODEJS_APP = "nodejs-app"
    MEMCACHED = "memcached"
    DB_MASTER = "db-master"
    MONITORING_MASTER = "monitoring-master"
    CUSTOM = "custom"

class DeploymentCommandName(Enum):
    INSTALL_DEPENDENCIES = "install_dependencies"
    UPDATE_DEPENDENCIES = "update_dependencies"
    UPDATE_CUSTOM_COOKBOOKS = "update_custom_cookbooks"
    EXECUTE_RECIPES = "execute_recipes"
    CONFIGURE = "configure"
    SETUP = "setup"
    DEPLOY = "deploy"
    ROLLBACK = "rollback"
    START = "start"
    STOP = "stop"
    RESTART = "restart"
    UNDEPLOY = "undeploy"

@dataclass
class OpsWorksStack:
    name: str
    region: str
    vpc_id: str
    default_subnet_id: str
    service_role_arn: str
    default_instance_profile_arn: str
    configuration_manager_name: str = "Chef"
    configuration_manager_version: str = "12"
    use_custom_cookbooks: bool = True
    custom_cookbooks_source: Dict[str, Any] = field(default_factory=dict)
    default_ssh_key_name: str = ""
    default_root_device_type: str = "ebs"
    default_availability_zone: str = ""
    hostname_theme: str = "Layer_Dependent"
    use_opsworks_security_groups: bool = True
    custom_json: Dict[str, Any] = field(default_factory=dict)
    chef_version: str = "12"
    berkshelf_version: str = "3.2.0"
    manage_berkshelf: bool = True
    attributes: Dict[str, Any] = field(default_factory=dict)
    agent_version: str = "LATEST"

@dataclass
class OpsWorksLayer:
    stack_id: str
    type: LayerType
    name: str
    shortname: str
    custom_recipes: Dict[str, List[str]] = field(default_factory=dict)
    packages: List[str] = field(default_factory=list)
    volume_configurations: List[Dict[str, Any]] = field(default_factory=list)
    enable_auto_healing: bool = True
    auto_assign_elastic_ips: bool = False
    auto_assign_public_ips: bool = True
    custom_security_group_ids: List[str] = field(default_factory=list)
    install_updates_on_boot: bool = True
    use_ebs_optimized_instances: bool = False
    lifecycle_event_configuration: Dict[str, Any] = field(default_factory=dict)
    attributes: Dict[str, Any] = field(default_factory=dict)

@dataclass
class OpsWorksApp:
    stack_id: str
    name: str
    type: str
    app_source: Dict[str, Any] = field(default_factory=dict)
    domains: List[str] = field(default_factory=list)
    enable_ssl: bool = False
    ssl_configuration: Dict[str, Any] = field(default_factory=dict)
    attributes: Dict[str, Any] = field(default_factory=dict)
    environment: List[Dict[str, str]] = field(default_factory=list)
    data_sources: List[Dict[str, Any]] = field(default_factory=list)
    description: str = ""

class EnterpriseOpsWorksManager:
    """
    Enterprise AWS OpsWorks manager with advanced configuration management,
    automated deployments, and infrastructure automation.
    """
    
    def __init__(self, region: str = 'us-east-1'):
        self.opsworks_client = boto3.client('opsworks', region_name=region)
        self.ec2_client = boto3.client('ec2', region_name=region)
        self.iam_client = boto3.client('iam', region_name=region)
        self.s3_client = boto3.client('s3', region_name=region)
        self.cloudwatch_client = boto3.client('cloudwatch', region_name=region)
        self.sns_client = boto3.client('sns', region_name=region)
        self.region = region
        
        # Configure logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Pre-built cookbook configurations
        self.cookbook_templates = self._initialize_cookbook_templates()
        
    def _initialize_cookbook_templates(self) -> Dict[str, Dict[str, Any]]:
        """Initialize enterprise cookbook templates"""
        
        return {
            "web_application": {
                "source": {
                    "Type": "git",
                    "Url": "https://github.com/enterprise/web-app-cookbooks.git",
                    "Revision": "main",
                    "Username": "",
                    "Password": "",
                    "SshKey": ""
                },
                "recipes": {
                    "Setup": ["web-app::setup", "web-app::security"],
                    "Configure": ["web-app::configure", "web-app::database"],
                    "Deploy": ["web-app::deploy", "web-app::restart"],
                    "Undeploy": ["web-app::undeploy"],
                    "Shutdown": ["web-app::cleanup"]
                },
                "attributes": {
                    "web-app": {
                        "environment": "production",
                        "ssl_enabled": True,
                        "backup_enabled": True,
                        "monitoring_enabled": True
                    }
                }
            },
            "database": {
                "source": {
                    "Type": "git", 
                    "Url": "https://github.com/enterprise/database-cookbooks.git",
                    "Revision": "main"
                },
                "recipes": {
                    "Setup": ["database::install", "database::security", "database::backup-setup"],
                    "Configure": ["database::configure", "database::users"],
                    "Deploy": ["database::migrate", "database::optimize"],
                    "Shutdown": ["database::backup", "database::cleanup"]
                },
                "attributes": {
                    "database": {
                        "engine": "mysql",
                        "version": "8.0",
                        "backup_retention": 7,
                        "encryption_enabled": True
                    }
                }
            },
            "monitoring": {
                "source": {
                    "Type": "git",
                    "Url": "https://github.com/enterprise/monitoring-cookbooks.git",
                    "Revision": "main"
                },
                "recipes": {
                    "Setup": ["monitoring::install", "monitoring::agents"],
                    "Configure": ["monitoring::configure", "monitoring::dashboards"],
                    "Deploy": ["monitoring::update", "monitoring::alerts"]
                },
                "attributes": {
                    "monitoring": {
                        "retention_days": 90,
                        "alert_email": "ops-team@company.com",
                        "dashboard_enabled": True
                    }
                }
            }
        }
    
    def create_enterprise_stack(self, 
                              stack_config: OpsWorksStack,
                              enable_monitoring: bool = True) -> Dict[str, Any]:
        """Create enterprise OpsWorks stack with comprehensive configuration"""
        
        try:
            # Prepare stack configuration
            stack_params = {
                'Name': stack_config.name,
                'Region': stack_config.region,
                'VpcId': stack_config.vpc_id,
                'DefaultSubnetId': stack_config.default_subnet_id,
                'ServiceRoleArn': stack_config.service_role_arn,
                'DefaultInstanceProfileArn': stack_config.default_instance_profile_arn,
                'ConfigurationManager': {
                    'Name': stack_config.configuration_manager_name,
                    'Version': stack_config.configuration_manager_version
                },
                'UseCustomCookbooks': stack_config.use_custom_cookbooks,
                'DefaultSshKeyName': stack_config.default_ssh_key_name,
                'DefaultRootDeviceType': stack_config.default_root_device_type,
                'HostnameTheme': stack_config.hostname_theme,
                'UseOpsworksSecurityGroups': stack_config.use_opsworks_security_groups,
                'AgentVersion': stack_config.agent_version
            }
            
            # Add custom cookbooks if enabled
            if stack_config.use_custom_cookbooks and stack_config.custom_cookbooks_source:
                stack_params['CustomCookbooksSource'] = stack_config.custom_cookbooks_source
                
                # Add Chef/Berkshelf configuration
                if stack_config.configuration_manager_name.lower() == 'chef':
                    stack_params['ChefConfiguration'] = {
                        'ManageBerkshelf': stack_config.manage_berkshelf,
                        'BerkshelfVersion': stack_config.berkshelf_version
                    }
            
            # Add custom JSON configuration
            if stack_config.custom_json:
                stack_params['CustomJson'] = json.dumps(stack_config.custom_json)
            
            # Add default availability zone if specified
            if stack_config.default_availability_zone:
                stack_params['DefaultAvailabilityZone'] = stack_config.default_availability_zone
            
            # Add stack attributes
            if stack_config.attributes:
                stack_params['Attributes'] = stack_config.attributes
            
            # Create the stack
            response = self.opsworks_client.create_stack(**stack_params)
            stack_id = response['StackId']
            
            # Setup monitoring if enabled
            monitoring_config = {}
            if enable_monitoring:
                monitoring_config = self._setup_stack_monitoring(stack_id, stack_config.name)
            
            # Create default security group
            security_group_config = self._create_stack_security_group(
                stack_config.vpc_id,
                stack_config.name
            )
            
            self.logger.info(f"Created enterprise OpsWorks stack: {stack_config.name}")
            
            return {
                'status': 'success',
                'stack_id': stack_id,
                'stack_name': stack_config.name,
                'configuration_manager': f"{stack_config.configuration_manager_name} {stack_config.configuration_manager_version}",
                'monitoring_config': monitoring_config,
                'security_group': security_group_config,
                'cookbook_source': stack_config.custom_cookbooks_source
            }
            
        except Exception as e:
            self.logger.error(f"Failed to create OpsWorks stack: {str(e)}")
            raise
    
    def create_enterprise_layer(self, 
                              layer_config: OpsWorksLayer,
                              cookbook_template: str = "web_application") -> Dict[str, Any]:
        """Create enterprise layer with advanced configuration"""
        
        try:
            # Get cookbook template configuration
            template_config = self.cookbook_templates.get(cookbook_template, {})
            
            # Merge template recipes with custom recipes
            recipes = template_config.get('recipes', {})
            if layer_config.custom_recipes:
                for event, recipe_list in layer_config.custom_recipes.items():
                    if event in recipes:
                        recipes[event].extend(recipe_list)
                    else:
                        recipes[event] = recipe_list
            
            # Prepare layer configuration
            layer_params = {
                'StackId': layer_config.stack_id,
                'Type': layer_config.type.value,
                'Name': layer_config.name,
                'Shortname': layer_config.shortname,
                'CustomRecipes': recipes,
                'Packages': layer_config.packages,
                'VolumeConfigurations': layer_config.volume_configurations,
                'EnableAutoHealing': layer_config.enable_auto_healing,
                'AutoAssignElasticIps': layer_config.auto_assign_elastic_ips,
                'AutoAssignPublicIps': layer_config.auto_assign_public_ips,
                'CustomSecurityGroupIds': layer_config.custom_security_group_ids,
                'InstallUpdatesOnBoot': layer_config.install_updates_on_boot,
                'UseEbsOptimizedInstances': layer_config.use_ebs_optimized_instances
            }
            
            # Add lifecycle event configuration
            if layer_config.lifecycle_event_configuration:
                layer_params['LifecycleEventConfiguration'] = layer_config.lifecycle_event_configuration
            
            # Merge template attributes with layer attributes
            attributes = template_config.get('attributes', {})
            if layer_config.attributes:
                attributes.update(layer_config.attributes)
            
            if attributes:
                layer_params['Attributes'] = attributes
            
            # Create the layer
            response = self.opsworks_client.create_layer(**layer_params)
            layer_id = response['LayerId']
            
            # Setup layer-specific monitoring
            layer_monitoring = self._setup_layer_monitoring(layer_id, layer_config.name)
            
            self.logger.info(f"Created enterprise OpsWorks layer: {layer_config.name}")
            
            return {
                'status': 'success',
                'layer_id': layer_id,
                'layer_name': layer_config.name,
                'layer_type': layer_config.type.value,
                'cookbook_template': cookbook_template,
                'recipes': recipes,
                'monitoring': layer_monitoring,
                'auto_healing': layer_config.enable_auto_healing
            }
            
        except Exception as e:
            self.logger.error(f"Failed to create OpsWorks layer: {str(e)}")
            raise
    
    def create_enterprise_app(self, 
                            app_config: OpsWorksApp,
                            enable_ssl: bool = True) -> Dict[str, Any]:
        """Create enterprise application with advanced configuration"""
        
        try:
            # Prepare app configuration
            app_params = {
                'StackId': app_config.stack_id,
                'Name': app_config.name,
                'Type': app_config.type,
                'AppSource': app_config.app_source,
                'Domains': app_config.domains,
                'EnableSsl': enable_ssl,
                'Environment': app_config.environment,
                'DataSources': app_config.data_sources
            }
            
            # Add SSL configuration if enabled
            if enable_ssl and app_config.ssl_configuration:
                app_params['SslConfiguration'] = app_config.ssl_configuration
            
            # Add application attributes
            if app_config.attributes:
                app_params['Attributes'] = app_config.attributes
            
            # Add description if provided
            if app_config.description:
                app_params['Description'] = app_config.description
            
            # Create the application
            response = self.opsworks_client.create_app(**app_params)
            app_id = response['AppId']
            
            # Setup application monitoring
            app_monitoring = self._setup_app_monitoring(app_id, app_config.name)
            
            # Setup deployment automation
            deployment_automation = self._setup_deployment_automation(
                app_config.stack_id,
                app_id,
                app_config.name
            )
            
            self.logger.info(f"Created enterprise OpsWorks application: {app_config.name}")
            
            return {
                'status': 'success',
                'app_id': app_id,
                'app_name': app_config.name,
                'app_type': app_config.type,
                'ssl_enabled': enable_ssl,
                'domains': app_config.domains,
                'monitoring': app_monitoring,
                'deployment_automation': deployment_automation
            }
            
        except Exception as e:
            self.logger.error(f"Failed to create OpsWorks application: {str(e)}")
            raise
    
    def _setup_stack_monitoring(self, stack_id: str, stack_name: str) -> Dict[str, Any]:
        """Setup comprehensive monitoring for OpsWorks stack"""
        
        monitoring_config = {
            'cloudwatch_alarms': [],
            'custom_metrics': [],
            'log_groups': []
        }
        
        # Create CloudWatch alarms for stack health
        alarms = [
            {
                'alarm_name': f'opsworks-{stack_name}-instance-failures',
                'metric_name': 'InstanceFailures',
                'namespace': 'AWS/OpsWorks',
                'statistic': 'Sum',
                'threshold': 1,
                'comparison': 'GreaterThanOrEqualToThreshold',
                'dimensions': [{'Name': 'StackId', 'Value': stack_id}]
            },
            {
                'alarm_name': f'opsworks-{stack_name}-deployment-failures',
                'metric_name': 'DeploymentFailures',
                'namespace': 'AWS/OpsWorks',
                'statistic': 'Sum',
                'threshold': 1,
                'comparison': 'GreaterThanOrEqualToThreshold',
                'dimensions': [{'Name': 'StackId', 'Value': stack_id}]
            }
        ]
        
        for alarm in alarms:
            try:
                self.cloudwatch_client.put_metric_alarm(
                    AlarmName=alarm['alarm_name'],
                    MetricName=alarm['metric_name'],
                    Namespace=alarm['namespace'],
                    Statistic=alarm['statistic'],
                    Threshold=alarm['threshold'],
                    ComparisonOperator=alarm['comparison'],
                    Dimensions=alarm['dimensions'],
                    EvaluationPeriods=2,
                    Period=300,
                    AlarmActions=[
                        f'arn:aws:sns:{self.region}:123456789012:opsworks-alerts'
                    ]
                )
                
                monitoring_config['cloudwatch_alarms'].append(alarm['alarm_name'])
                
            except Exception as e:
                self.logger.warning(f"Failed to create alarm {alarm['alarm_name']}: {str(e)}")
        
        return monitoring_config
    
    def _setup_layer_monitoring(self, layer_id: str, layer_name: str) -> Dict[str, Any]:
        """Setup layer-specific monitoring"""
        
        return {
            'layer_id': layer_id,
            'metrics_enabled': True,
            'log_collection': True,
            'health_checks': True
        }
    
    def _setup_app_monitoring(self, app_id: str, app_name: str) -> Dict[str, Any]:
        """Setup application-specific monitoring"""
        
        return {
            'app_id': app_id,
            'performance_monitoring': True,
            'error_tracking': True,
            'deployment_tracking': True
        }
    
    def _create_stack_security_group(self, vpc_id: str, stack_name: str) -> Dict[str, Any]:
        """Create security group for OpsWorks stack"""
        
        try:
            # Create security group
            sg_response = self.ec2_client.create_security_group(
                GroupName=f'opsworks-{stack_name}-sg',
                Description=f'Security group for OpsWorks stack {stack_name}',
                VpcId=vpc_id
            )
            
            security_group_id = sg_response['GroupId']
            
            # Add ingress rules
            self.ec2_client.authorize_security_group_ingress(
                GroupId=security_group_id,
                IpPermissions=[
                    {
                        'IpProtocol': 'tcp',
                        'FromPort': 80,
                        'ToPort': 80,
                        'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
                    },
                    {
                        'IpProtocol': 'tcp',
                        'FromPort': 443,
                        'ToPort': 443,
                        'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
                    },
                    {
                        'IpProtocol': 'tcp',
                        'FromPort': 22,
                        'ToPort': 22,
                        'IpRanges': [{'CidrIp': '10.0.0.0/8'}]
                    }
                ]
            )
            
            return {
                'security_group_id': security_group_id,
                'group_name': f'opsworks-{stack_name}-sg',
                'vpc_id': vpc_id
            }
            
        except Exception as e:
            self.logger.warning(f"Failed to create security group: {str(e)}")
            return {}
    
    def _setup_deployment_automation(self, 
                                   stack_id: str,
                                   app_id: str,
                                   app_name: str) -> Dict[str, Any]:
        """Setup automated deployment workflows"""
        
        return {
            'stack_id': stack_id,
            'app_id': app_id,
            'automated_deployments': True,
            'rollback_enabled': True,
            'health_checks': True,
            'notification_enabled': True
        }

class ConfigurationDriftDetector:
    """
    Advanced configuration drift detection and remediation
    for OpsWorks environments.
    """
    
    def __init__(self, opsworks_manager: EnterpriseOpsWorksManager):
        self.opsworks_manager = opsworks_manager
        self.ssm_client = boto3.client('ssm')
        
    def detect_configuration_drift(self, 
                                 stack_id: str,
                                 baseline_config: Dict[str, Any]) -> Dict[str, Any]:
        """Detect configuration drift across stack instances"""
        
        try:
            # Get current stack configuration
            current_config = self._get_current_stack_configuration(stack_id)
            
            # Compare with baseline
            drift_analysis = self._analyze_configuration_drift(baseline_config, current_config)
            
            # Generate remediation recommendations
            remediation_plan = self._generate_remediation_plan(drift_analysis)
            
            return {
                'stack_id': stack_id,
                'drift_detected': len(drift_analysis['differences']) > 0,
                'drift_severity': self._calculate_drift_severity(drift_analysis),
                'differences': drift_analysis['differences'],
                'remediation_plan': remediation_plan,
                'analysis_timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to detect configuration drift: {str(e)}")
            raise
    
    def _get_current_stack_configuration(self, stack_id: str) -> Dict[str, Any]:
        """Get current configuration state of the stack"""
        
        # Get stack details
        stack_response = self.opsworks_manager.opsworks_client.describe_stacks(
            StackIds=[stack_id]
        )
        
        stack = stack_response['Stacks'][0]
        
        # Get layers
        layers_response = self.opsworks_manager.opsworks_client.describe_layers(
            StackId=stack_id
        )
        
        # Get instances
        instances_response = self.opsworks_manager.opsworks_client.describe_instances(
            StackId=stack_id
        )
        
        # Get applications
        apps_response = self.opsworks_manager.opsworks_client.describe_apps(
            StackId=stack_id
        )
        
        return {
            'stack': stack,
            'layers': layers_response['Layers'],
            'instances': instances_response['Instances'],
            'applications': apps_response['Apps']
        }
    
    def _analyze_configuration_drift(self, 
                                   baseline: Dict[str, Any],
                                   current: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze differences between baseline and current configuration"""
        
        differences = []
        
        # Compare stack configuration
        stack_diffs = self._compare_stack_config(
            baseline.get('stack', {}),
            current.get('stack', {})
        )
        differences.extend(stack_diffs)
        
        # Compare layers
        layer_diffs = self._compare_layers(
            baseline.get('layers', []),
            current.get('layers', [])
        )
        differences.extend(layer_diffs)
        
        # Compare instances
        instance_diffs = self._compare_instances(
            baseline.get('instances', []),
            current.get('instances', [])
        )
        differences.extend(instance_diffs)
        
        return {
            'differences': differences,
            'total_differences': len(differences)
        }
    
    def _compare_stack_config(self, baseline: Dict[str, Any], current: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Compare stack-level configuration"""
        
        differences = []
        
        # Compare key stack attributes
        compare_fields = [
            'ConfigurationManager',
            'UseCustomCookbooks',
            'CustomCookbooksSource',
            'DefaultSshKeyName',
            'UseOpsworksSecurityGroups'
        ]
        
        for field in compare_fields:
            baseline_value = baseline.get(field)
            current_value = current.get(field)
            
            if baseline_value != current_value:
                differences.append({
                    'type': 'stack_configuration',
                    'field': field,
                    'baseline_value': baseline_value,
                    'current_value': current_value,
                    'severity': 'medium'
                })
        
        return differences
    
    def _compare_layers(self, baseline: List[Dict[str, Any]], current: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Compare layer configurations"""
        
        differences = []
        
        # Create lookup dictionaries
        baseline_layers = {layer['Name']: layer for layer in baseline}
        current_layers = {layer['Name']: layer for layer in current}
        
        # Check for missing or added layers
        baseline_names = set(baseline_layers.keys())
        current_names = set(current_layers.keys())
        
        missing_layers = baseline_names - current_names
        added_layers = current_names - baseline_names
        
        for layer_name in missing_layers:
            differences.append({
                'type': 'layer_missing',
                'layer_name': layer_name,
                'severity': 'high'
            })
        
        for layer_name in added_layers:
            differences.append({
                'type': 'layer_added',
                'layer_name': layer_name,
                'severity': 'medium'
            })
        
        # Compare existing layers
        common_layers = baseline_names & current_names
        
        for layer_name in common_layers:
            baseline_layer = baseline_layers[layer_name]
            current_layer = current_layers[layer_name]
            
            # Compare layer attributes
            compare_fields = [
                'Type',
                'CustomRecipes',
                'Packages',
                'EnableAutoHealing',
                'AutoAssignElasticIps'
            ]
            
            for field in compare_fields:
                baseline_value = baseline_layer.get(field)
                current_value = current_layer.get(field)
                
                if baseline_value != current_value:
                    differences.append({
                        'type': 'layer_configuration',
                        'layer_name': layer_name,
                        'field': field,
                        'baseline_value': baseline_value,
                        'current_value': current_value,
                        'severity': 'medium'
                    })
        
        return differences
    
    def _compare_instances(self, baseline: List[Dict[str, Any]], current: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Compare instance configurations"""
        
        differences = []
        
        # Compare instance counts by layer
        baseline_counts = {}
        current_counts = {}
        
        for instance in baseline:
            layer_id = instance.get('LayerId')
            baseline_counts[layer_id] = baseline_counts.get(layer_id, 0) + 1
        
        for instance in current:
            layer_id = instance.get('LayerId')
            current_counts[layer_id] = current_counts.get(layer_id, 0) + 1
        
        # Check for instance count differences
        all_layers = set(baseline_counts.keys()) | set(current_counts.keys())
        
        for layer_id in all_layers:
            baseline_count = baseline_counts.get(layer_id, 0)
            current_count = current_counts.get(layer_id, 0)
            
            if baseline_count != current_count:
                differences.append({
                    'type': 'instance_count',
                    'layer_id': layer_id,
                    'baseline_count': baseline_count,
                    'current_count': current_count,
                    'severity': 'high' if abs(baseline_count - current_count) > 1 else 'medium'
                })
        
        return differences
    
    def _calculate_drift_severity(self, drift_analysis: Dict[str, Any]) -> str:
        """Calculate overall drift severity"""
        
        differences = drift_analysis['differences']
        
        if not differences:
            return 'none'
        
        high_severity_count = sum(1 for diff in differences if diff.get('severity') == 'high')
        medium_severity_count = sum(1 for diff in differences if diff.get('severity') == 'medium')
        
        if high_severity_count > 0:
            return 'high'
        elif medium_severity_count > 2:
            return 'medium'
        else:
            return 'low'
    
    def _generate_remediation_plan(self, drift_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate remediation plan for detected drift"""
        
        remediation_actions = []
        
        for difference in drift_analysis['differences']:
            action = self._get_remediation_action(difference)
            if action:
                remediation_actions.append(action)
        
        return remediation_actions
    
    def _get_remediation_action(self, difference: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get specific remediation action for a difference"""
        
        diff_type = difference['type']
        
        if diff_type == 'stack_configuration':
            return {
                'action': 'update_stack_configuration',
                'field': difference['field'],
                'target_value': difference['baseline_value'],
                'priority': 'medium'
            }
        
        elif diff_type == 'layer_missing':
            return {
                'action': 'create_layer',
                'layer_name': difference['layer_name'],
                'priority': 'high'
            }
        
        elif diff_type == 'layer_configuration':
            return {
                'action': 'update_layer_configuration',
                'layer_name': difference['layer_name'],
                'field': difference['field'],
                'target_value': difference['baseline_value'],
                'priority': 'medium'
            }
        
        elif diff_type == 'instance_count':
            return {
                'action': 'adjust_instance_count',
                'layer_id': difference['layer_id'],
                'target_count': difference['baseline_count'],
                'priority': 'high'
            }
        
        return None

# DevOps Integration Pipeline
class OpsWorksDevOpsPipeline:
    """
    DevOps pipeline integration for OpsWorks with automated
    cookbook management, deployment orchestration, and monitoring.
    """
    
    def __init__(self, pipeline_name: str):
        self.pipeline_name = pipeline_name
        self.opsworks_manager = EnterpriseOpsWorksManager()
        self.drift_detector = ConfigurationDriftDetector(self.opsworks_manager)
        
    def create_cookbook_management_pipeline(self, 
                                          cookbook_repository: str,
                                          test_kitchen_config: Dict[str, Any]) -> Dict[str, Any]:
        """Create automated cookbook development and deployment pipeline"""
        
        pipeline_config = {
            'pipeline_name': self.pipeline_name,
            'cookbook_repository': cookbook_repository,
            'test_kitchen_config': test_kitchen_config,
            'pipeline_stages': []
        }
        
        # Source stage
        source_stage = {
            'name': 'Source',
            'actions': [
                {
                    'name': 'SourceAction',
                    'action_type': 'Source',
                    'provider': 'CodeCommit',
                    'configuration': {
                        'RepositoryName': cookbook_repository.split('/')[-1],
                        'BranchName': 'main'
                    },
                    'output_artifacts': ['SourceOutput']
                }
            ]
        }
        pipeline_config['pipeline_stages'].append(source_stage)
        
        # Test stage
        test_stage = {
            'name': 'Test',
            'actions': [
                {
                    'name': 'CookbookLinting',
                    'action_type': 'Build',
                    'provider': 'CodeBuild',
                    'configuration': {
                        'ProjectName': f'{self.pipeline_name}-cookbook-lint'
                    },
                    'input_artifacts': ['SourceOutput'],
                    'output_artifacts': ['LintOutput']
                },
                {
                    'name': 'TestKitchen',
                    'action_type': 'Build',
                    'provider': 'CodeBuild',
                    'configuration': {
                        'ProjectName': f'{self.pipeline_name}-test-kitchen'
                    },
                    'input_artifacts': ['SourceOutput'],
                    'output_artifacts': ['TestOutput']
                }
            ]
        }
        pipeline_config['pipeline_stages'].append(test_stage)
        
        # Security scanning stage
        security_stage = {
            'name': 'SecurityScan',
            'actions': [
                {
                    'name': 'CookbookSecurityScan',
                    'action_type': 'Build',
                    'provider': 'CodeBuild',
                    'configuration': {
                        'ProjectName': f'{self.pipeline_name}-security-scan'
                    },
                    'input_artifacts': ['SourceOutput'],
                    'output_artifacts': ['SecurityOutput']
                }
            ]
        }
        pipeline_config['pipeline_stages'].append(security_stage)
        
        # Deployment stages
        deployment_stages = ['development', 'staging', 'production']
        
        for stage in deployment_stages:
            deploy_stage = {
                'name': f'Deploy{stage.capitalize()}',
                'actions': [
                    {
                        'name': f'Deploy{stage.capitalize()}Action',
                        'action_type': 'Invoke',
                        'provider': 'Lambda',
                        'configuration': {
                            'FunctionName': f'{self.pipeline_name}-deploy-cookbook',
                            'UserParameters': json.dumps({
                                'environment': stage,
                                'cookbook_source': cookbook_repository
                            })
                        },
                        'input_artifacts': ['SourceOutput']
                    }
                ]
            }
            
            if stage == 'production':
                # Add manual approval for production
                approval_action = {
                    'name': 'ProductionApproval',
                    'action_type': 'Approval',
                    'provider': 'Manual',
                    'configuration': {
                        'CustomData': 'Please review and approve production deployment'
                    }
                }
                deploy_stage['actions'].insert(0, approval_action)
            
            pipeline_config['pipeline_stages'].append(deploy_stage)
        
        # Setup monitoring for the pipeline
        monitoring_config = self._setup_pipeline_monitoring()
        pipeline_config['monitoring'] = monitoring_config
        
        return pipeline_config
    
    def create_deployment_automation(self, 
                                   stack_id: str,
                                   deployment_config: Dict[str, Any]) -> Dict[str, Any]:
        """Create automated deployment workflows"""
        
        automation_config = {
            'stack_id': stack_id,
            'deployment_strategies': [],
            'rollback_procedures': [],
            'health_checks': []
        }
        
        # Blue-green deployment strategy
        blue_green_strategy = {
            'name': 'blue_green',
            'description': 'Blue-green deployment with zero downtime',
            'steps': [
                'create_green_environment',
                'deploy_to_green',
                'run_health_checks',
                'switch_traffic',
                'monitor_green_environment',
                'terminate_blue_environment'
            ],
            'rollback_triggers': [
                'health_check_failure',
                'error_rate_threshold',
                'manual_trigger'
            ]
        }
        automation_config['deployment_strategies'].append(blue_green_strategy)
        
        # Canary deployment strategy
        canary_strategy = {
            'name': 'canary',
            'description': 'Gradual rollout with traffic splitting',
            'steps': [
                'deploy_to_canary_instances',
                'route_percentage_traffic',
                'monitor_canary_metrics',
                'increase_traffic_gradually',
                'complete_rollout'
            ],
            'traffic_splits': [10, 25, 50, 100],
            'monitoring_duration': 300  # 5 minutes per stage
        }
        automation_config['deployment_strategies'].append(canary_strategy)
        
        # Automated rollback procedures
        rollback_procedures = [
            {
                'trigger': 'health_check_failure',
                'action': 'immediate_rollback',
                'notification': True
            },
            {
                'trigger': 'error_rate_above_threshold',
                'threshold': 5,  # percentage
                'action': 'gradual_rollback',
                'notification': True
            },
            {
                'trigger': 'response_time_degradation',
                'threshold': 2000,  # milliseconds
                'action': 'investigation_alert',
                'notification': True
            }
        ]
        automation_config['rollback_procedures'] = rollback_procedures
        
        # Health check configuration
        health_checks = [
            {
                'type': 'endpoint_health',
                'url': '/',
                'expected_status': 200,
                'timeout': 5000
            },
            {
                'type': 'application_metrics',
                'metrics': ['cpu_utilization', 'memory_usage', 'response_time'],
                'thresholds': {'cpu': 80, 'memory': 85, 'response_time': 2000}
            },
            {
                'type': 'dependency_health',
                'dependencies': ['database', 'cache', 'external_api'],
                'timeout': 10000
            }
        ]
        automation_config['health_checks'] = health_checks
        
        return automation_config
    
    def _setup_pipeline_monitoring(self) -> Dict[str, Any]:
        """Setup monitoring for cookbook pipeline"""
        
        return {
            'pipeline_metrics': [
                'pipeline_execution_duration',
                'test_success_rate',
                'deployment_frequency',
                'lead_time_for_changes'
            ],
            'alerts': [
                {
                    'metric': 'pipeline_failure_rate',
                    'threshold': 20,  # percentage
                    'notification': 'ops-team@company.com'
                },
                {
                    'metric': 'cookbook_test_failures',
                    'threshold': 1,
                    'notification': 'dev-team@company.com'
                }
            ],
            'dashboards': [
                'cookbook_pipeline_overview',
                'deployment_success_rates',
                'infrastructure_drift_detection'
            ]
        }

# CLI Usage Examples
if __name__ == "__main__":
    # Initialize enterprise OpsWorks manager
    opsworks_mgr = EnterpriseOpsWorksManager(region='us-east-1')
    
    # Create enterprise stack
    stack_config = OpsWorksStack(
        name='enterprise-web-stack',
        region='us-east-1',
        vpc_id='vpc-12345678',
        default_subnet_id='subnet-87654321',
        service_role_arn='arn:aws:iam::123456789012:role/aws-opsworks-service-role',
        default_instance_profile_arn='arn:aws:iam::123456789012:instance-profile/aws-opsworks-ec2-role',
        configuration_manager_name='Chef',
        configuration_manager_version='12',
        use_custom_cookbooks=True,
        custom_cookbooks_source={
            'Type': 'git',
            'Url': 'https://github.com/enterprise/cookbooks.git',
            'Revision': 'main'
        },
        custom_json={
            'environment': 'production',
            'monitoring': {'enabled': True},
            'backup': {'retention_days': 30}
        }
    )
    
    stack_result = opsworks_mgr.create_enterprise_stack(
        stack_config=stack_config,
        enable_monitoring=True
    )
    
    # Create web application layer
    layer_config = OpsWorksLayer(
        stack_id=stack_result['stack_id'],
        type=LayerType.WEB,
        name='web-servers',
        shortname='web',
        custom_recipes={
            'Setup': ['web-app::ssl', 'web-app::monitoring'],
            'Deploy': ['web-app::deploy', 'web-app::health-check']
        },
        packages=['nginx', 'nodejs', 'pm2'],
        enable_auto_healing=True,
        auto_assign_public_ips=True,
        install_updates_on_boot=True
    )
    
    layer_result = opsworks_mgr.create_enterprise_layer(
        layer_config=layer_config,
        cookbook_template='web_application'
    )
    
    # Create application
    app_config = OpsWorksApp(
        stack_id=stack_result['stack_id'],
        name='enterprise-web-app',
        type='nodejs',
        app_source={
            'Type': 'git',
            'Url': 'https://github.com/enterprise/web-app.git',
            'Revision': 'main'
        },
        domains=['app.company.com'],
        enable_ssl=True,
        environment=[
            {'Key': 'NODE_ENV', 'Value': 'production'},
            {'Key': 'DATABASE_URL', 'Value': 'mysql://db.company.com:3306/app'}
        ]
    )
    
    app_result = opsworks_mgr.create_enterprise_app(
        app_config=app_config,
        enable_ssl=True
    )
    
    # Setup configuration drift detection
    drift_detector = ConfigurationDriftDetector(opsworks_mgr)
    baseline_config = {
        'stack': stack_config.__dict__,
        'layers': [layer_config.__dict__],
        'applications': [app_config.__dict__]
    }
    
    # Setup DevOps pipeline
    pipeline = OpsWorksDevOpsPipeline('enterprise-opsworks')
    cookbook_pipeline = pipeline.create_cookbook_management_pipeline(
        cookbook_repository='codecommit://enterprise-cookbooks',
        test_kitchen_config={
            'platforms': ['ubuntu-20.04', 'centos-8'],
            'suites': ['default', 'production']
        }
    )
    
    deployment_automation = pipeline.create_deployment_automation(
        stack_id=stack_result['stack_id'],
        deployment_config={
            'strategy': 'blue_green',
            'health_checks': True,
            'auto_rollback': True
        }
    )
    
    print(f"Enterprise OpsWorks setup completed: {stack_result['stack_id']}")

# Real-world Enterprise Use Cases

## Use Case 1: E-commerce Platform Configuration Management
"""
Large e-commerce company uses OpsWorks to manage complex multi-tier
application stack with automated scaling and configuration management.

Key Requirements:
- Multi-tier web application (web, app, database layers)
- Auto-scaling based on traffic patterns
- Blue-green deployments for zero downtime
- Configuration management for 100+ instances
- Compliance monitoring and drift detection
- Automated cookbook testing and deployment
"""

## Use Case 2: Financial Services Infrastructure Automation
"""
Investment bank implements OpsWorks for regulatory compliance and
automated infrastructure management across development environments.

Key Requirements:
- SOX compliance automation
- Immutable infrastructure patterns
- Automated security baseline enforcement
- Configuration drift detection and remediation
- Audit trail for all configuration changes
- Multi-environment cookbook management
"""

## Use Case 3: Healthcare Application Deployment
"""
Healthcare organization uses OpsWorks for HIPAA-compliant application
deployment with automated security and compliance monitoring.

Key Requirements:
- HIPAA compliance automation
- Encrypted data handling
- Automated security updates
- Configuration baseline enforcement
- Audit logging and monitoring
- Disaster recovery automation
"""

# Advanced Integration Patterns

## Pattern 1: OpsWorks + AWS Systems Manager
opsworks_ssm_integration = """
# Integration with Systems Manager for enhanced automation
# and patch management

def integrate_with_systems_manager():
    import boto3
    
    ssm_client = boto3.client('ssm')
    
    # Create maintenance window for OpsWorks instances
    maintenance_window = ssm_client.create_maintenance_window(
        Name='OpsWorks-Patch-Window',
        Description='Automated patching for OpsWorks instances',
        Duration=4,  # hours
        Cutoff=1,   # hour before end
        Schedule='cron(0 2 ? * SUN *)',  # Every Sunday at 2 AM
        ScheduleTimezone='UTC',
        AllowUnassociatedTargets=False
    )
    
    # Register OpsWorks instances as targets
    ssm_client.register_target_with_maintenance_window(
        WindowId=maintenance_window['WindowId'],
        ResourceType='INSTANCE',
        Targets=[
            {
                'Key': 'tag:opsworks:stack',
                'Values': ['enterprise-web-stack']
            }
        ]
    )
"""

## Pattern 2: OpsWorks + CloudWatch Integration
opsworks_cloudwatch_integration = """
# Advanced monitoring and alerting integration
# with CloudWatch and custom metrics

def setup_advanced_monitoring():
    import boto3
    
    cloudwatch = boto3.client('cloudwatch')
    
    # Create custom dashboard for OpsWorks metrics
    dashboard_body = {
        "widgets": [
            {
                "type": "metric",
                "properties": {
                    "metrics": [
                        ["AWS/OpsWorks", "InstancesOnline", "StackId", "stack-id"],
                        [".", "InstancesBooting", ".", "."],
                        [".", "InstancesShuttingDown", ".", "."]
                    ],
                    "period": 300,
                    "stat": "Average",
                    "region": "us-east-1",
                    "title": "OpsWorks Instance Status"
                }
            },
            {
                "type": "metric",
                "properties": {
                    "metrics": [
                        ["AWS/OpsWorks", "DeploymentsDuration", "StackId", "stack-id"],
                        [".", "DeploymentsSuccessful", ".", "."],
                        [".", "DeploymentsFailed", ".", "."]
                    ],
                    "period": 300,
                    "stat": "Sum",
                    "region": "us-east-1",
                    "title": "OpsWorks Deployments"
                }
            }
        ]
    }
    
    cloudwatch.put_dashboard(
        DashboardName='OpsWorks-Enterprise-Dashboard',
        DashboardBody=json.dumps(dashboard_body)
    )
"""

## DevOps Best Practices

### 1. Configuration Management
- Infrastructure as Code with Chef/Puppet cookbooks
- Version control for all configuration artifacts
- Automated testing with Test Kitchen
- Configuration drift detection and remediation

### 2. Deployment Automation
- Blue-green deployment strategies
- Canary releases with gradual traffic shifting
- Automated rollback on failure detection
- Health checks and monitoring integration

### 3. Security and Compliance
- Automated security baseline enforcement
- Regular security updates and patching
- Configuration compliance monitoring
- Audit trails for all changes

### 4. Monitoring and Observability
- Comprehensive application and infrastructure monitoring
- Real-time alerting and notification
- Performance metrics and capacity planning
- Log aggregation and analysis

This enterprise AWS OpsWorks framework provides comprehensive configuration management, automated deployments, and seamless DevOps integration for organizations requiring advanced infrastructure automation and compliance capabilities at scale.