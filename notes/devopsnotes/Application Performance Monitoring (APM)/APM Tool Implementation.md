# APM Tool Implementation

APM tool implementation involves selecting, deploying, and configuring appropriate monitoring solutions for specific environments and requirements. This guide covers popular APM tools including New Relic, Datadog, AppDynamics, Elastic APM, and open-source alternatives, along with implementation strategies, configuration management, and enterprise deployment patterns.

## APM Tool Selection Framework

### Tool Comparison and Selection Matrix

```python
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from enum import Enum
import json

class DeploymentModel(Enum):
    SAAS = "saas"
    ON_PREMISE = "on_premise"
    HYBRID = "hybrid"
    
class PricingModel(Enum):
    PER_HOST = "per_host"
    PER_TRANSACTION = "per_transaction" 
    PER_USER = "per_user"
    VOLUME_BASED = "volume_based"
    FLAT_RATE = "flat_rate"

@dataclass
class APMToolCapability:
    feature: str
    supported: bool
    quality_rating: int  # 1-5 scale
    notes: str = ""

@dataclass
class APMTool:
    name: str
    vendor: str
    deployment_models: List[DeploymentModel]
    pricing_model: PricingModel
    language_support: List[str]
    capabilities: List[APMToolCapability]
    integrations: List[str]
    pros: List[str] = field(default_factory=list)
    cons: List[str] = field(default_factory=list)
    enterprise_features: List[str] = field(default_factory=list)

class APMToolSelector:
    def __init__(self):
        self.tools = self._initialize_tools()
        self.weights = {
            'language_support': 0.2,
            'feature_coverage': 0.25,
            'ease_of_implementation': 0.15,
            'cost_effectiveness': 0.15,
            'enterprise_readiness': 0.15,
            'vendor_support': 0.1
        }
    
    def _initialize_tools(self) -> Dict[str, APMTool]:
        """Initialize APM tool database"""
        
        tools = {}
        
        # New Relic
        tools['new_relic'] = APMTool(
            name="New Relic",
            vendor="New Relic Inc.",
            deployment_models=[DeploymentModel.SAAS],
            pricing_model=PricingModel.PER_HOST,
            language_support=[
                "Java", "Python", "Ruby", "PHP", "Node.js", 
                ".NET", "Go", "C/C++", "Mobile (iOS/Android)"
            ],
            capabilities=[
                APMToolCapability("Application Monitoring", True, 5, "Excellent real-time monitoring"),
                APMToolCapability("Database Monitoring", True, 4, "Good database performance insights"),
                APMToolCapability("Infrastructure Monitoring", True, 4, "Integrated infrastructure metrics"),
                APMToolCapability("Browser Monitoring", True, 5, "Best-in-class browser RUM"),
                APMToolCapability("Mobile Monitoring", True, 4, "Good mobile app monitoring"),
                APMToolCapability("Distributed Tracing", True, 4, "Solid tracing capabilities"),
                APMToolCapability("Custom Metrics", True, 4, "Flexible custom instrumentation"),
                APMToolCapability("Alerting", True, 5, "Advanced alerting and notifications"),
                APMToolCapability("Dashboards", True, 5, "Rich visualization and dashboards")
            ],
            integrations=[
                "Slack", "PagerDuty", "Jira", "ServiceNow", "Kubernetes", 
                "Docker", "AWS", "Azure", "GCP", "Jenkins"
            ],
            pros=[
                "User-friendly interface",
                "Comprehensive feature set", 
                "Strong community and documentation",
                "Quick setup and deployment",
                "Excellent alerting capabilities"
            ],
            cons=[
                "Can be expensive at scale",
                "Limited customization options",
                "SaaS-only deployment model",
                "Data retention limitations"
            ],
            enterprise_features=[
                "SSO integration", "RBAC", "Advanced security controls",
                "Custom retention policies", "White-glove onboarding"
            ]
        )
        
        # Datadog
        tools['datadog'] = APMTool(
            name="Datadog",
            vendor="Datadog Inc.",
            deployment_models=[DeploymentModel.SAAS],
            pricing_model=PricingModel.PER_HOST,
            language_support=[
                "Java", "Python", "Ruby", "PHP", "Node.js", 
                ".NET", "Go", "C++", "Mobile (iOS/Android)"
            ],
            capabilities=[
                APMToolCapability("Application Monitoring", True, 5, "Comprehensive APM features"),
                APMToolCapability("Database Monitoring", True, 5, "Excellent database monitoring"),
                APMToolCapability("Infrastructure Monitoring", True, 5, "Best-in-class infrastructure monitoring"),
                APMToolCapability("Browser Monitoring", True, 4, "Good browser monitoring"),
                APMToolCapability("Mobile Monitoring", True, 3, "Basic mobile monitoring"),
                APMToolCapability("Distributed Tracing", True, 5, "Excellent distributed tracing"),
                APMToolCapability("Custom Metrics", True, 5, "Powerful custom metrics"),
                APMToolCapability("Alerting", True, 4, "Good alerting capabilities"),
                APMToolCapability("Dashboards", True, 5, "Excellent dashboards and visualization")
            ],
            integrations=[
                "Slack", "PagerDuty", "Jira", "ServiceNow", "Kubernetes",
                "Docker", "AWS", "Azure", "GCP", "Terraform", "Ansible"
            ],
            pros=[
                "Unified platform for metrics, traces, and logs",
                "Excellent infrastructure monitoring",
                "Strong API and integrations",
                "Advanced analytics and machine learning",
                "Comprehensive documentation"
            ],
            cons=[
                "Complex pricing model",
                "Can be overwhelming for small teams",
                "SaaS-only deployment",
                "Learning curve for advanced features"
            ],
            enterprise_features=[
                "Advanced RBAC", "Audit logs", "SAML SSO",
                "Custom retention", "Professional services"
            ]
        )
        
        # AppDynamics
        tools['appdynamics'] = APMTool(
            name="AppDynamics",
            vendor="Cisco Systems",
            deployment_models=[DeploymentModel.SAAS, DeploymentModel.ON_PREMISE, DeploymentModel.HYBRID],
            pricing_model=PricingModel.PER_HOST,
            language_support=[
                "Java", "Python", "Ruby", "PHP", "Node.js", 
                ".NET", "C++", "Mobile (iOS/Android)"
            ],
            capabilities=[
                APMToolCapability("Application Monitoring", True, 5, "Enterprise-grade APM"),
                APMToolCapability("Database Monitoring", True, 4, "Good database monitoring"),
                APMToolCapability("Infrastructure Monitoring", True, 4, "Solid infrastructure monitoring"),
                APMToolCapability("Browser Monitoring", True, 4, "Good browser monitoring"),
                APMToolCapability("Mobile Monitoring", True, 4, "Good mobile monitoring"),
                APMToolCapability("Distributed Tracing", True, 4, "Good distributed tracing"),
                APMToolCapability("Custom Metrics", True, 4, "Flexible custom metrics"),
                APMToolCapability("Alerting", True, 4, "Good alerting capabilities"),
                APMToolCapability("Dashboards", True, 4, "Good visualization capabilities")
            ],
            integrations=[
                "ServiceNow", "Slack", "PagerDuty", "Jira", "Kubernetes",
                "Docker", "AWS", "Azure", "Jenkins", "Splunk"
            ],
            pros=[
                "Deployment flexibility (SaaS/On-premise)",
                "Strong enterprise features",
                "Automatic discovery and mapping",
                "Business-centric monitoring",
                "Excellent support"
            ],
            cons=[
                "Complex setup and configuration",
                "Expensive for large deployments",
                "Heavy resource consumption",
                "Steep learning curve"
            ],
            enterprise_features=[
                "On-premise deployment", "Advanced security",
                "Business journey monitoring", "Capacity planning"
            ]
        )
        
        # Elastic APM
        tools['elastic_apm'] = APMTool(
            name="Elastic APM",
            vendor="Elastic N.V.",
            deployment_models=[DeploymentModel.SAAS, DeploymentModel.ON_PREMISE, DeploymentModel.HYBRID],
            pricing_model=PricingModel.VOLUME_BASED,
            language_support=[
                "Java", "Python", "Ruby", "PHP", "Node.js",
                ".NET", "Go", "JavaScript/Browser"
            ],
            capabilities=[
                APMToolCapability("Application Monitoring", True, 4, "Good APM capabilities"),
                APMToolCapability("Database Monitoring", True, 3, "Basic database monitoring"),
                APMToolCapability("Infrastructure Monitoring", True, 4, "Good with Metricbeat"),
                APMToolCapability("Browser Monitoring", True, 4, "Good browser monitoring"),
                APMToolCapability("Mobile Monitoring", False, 0, "Not supported"),
                APMToolCapability("Distributed Tracing", True, 4, "Good distributed tracing"),
                APMToolCapability("Custom Metrics", True, 4, "Flexible custom metrics"),
                APMToolCapability("Alerting", True, 3, "Basic alerting capabilities"),
                APMToolCapability("Dashboards", True, 4, "Kibana dashboards")
            ],
            integrations=[
                "Kibana", "Logstash", "Beats", "Kubernetes",
                "Docker", "AWS", "Azure", "GCP"
            ],
            pros=[
                "Open source foundation",
                "Part of Elastic Stack",
                "Deployment flexibility",
                "Cost-effective at scale",
                "Strong search and analytics"
            ],
            cons=[
                "Requires Elastic Stack knowledge",
                "Limited mobile monitoring",
                "Complex configuration",
                "Fewer enterprise features"
            ],
            enterprise_features=[
                "Machine learning anomaly detection",
                "Advanced security features",
                "Professional support"
            ]
        )
        
        # Jaeger (Open Source)
        tools['jaeger'] = APMTool(
            name="Jaeger",
            vendor="CNCF",
            deployment_models=[DeploymentModel.ON_PREMISE],
            pricing_model=PricingModel.FLAT_RATE,
            language_support=[
                "Java", "Python", "Ruby", "PHP", "Node.js",
                ".NET", "Go", "C++", "JavaScript"
            ],
            capabilities=[
                APMToolCapability("Application Monitoring", True, 3, "Basic APM via tracing"),
                APMToolCapability("Database Monitoring", False, 0, "Not directly supported"),
                APMToolCapability("Infrastructure Monitoring", False, 0, "Not supported"),
                APMToolCapability("Browser Monitoring", False, 0, "Not supported"),
                APMToolCapability("Mobile Monitoring", False, 0, "Not supported"),
                APMToolCapability("Distributed Tracing", True, 5, "Excellent distributed tracing"),
                APMToolCapability("Custom Metrics", True, 3, "Limited custom metrics"),
                APMToolCapability("Alerting", False, 0, "Requires external system"),
                APMToolCapability("Dashboards", True, 3, "Basic visualization")
            ],
            integrations=[
                "Prometheus", "Grafana", "Kubernetes", "OpenTelemetry",
                "Istio", "Envoy"
            ],
            pros=[
                "Open source and free",
                "CNCF graduated project",
                "Excellent distributed tracing",
                "OpenTelemetry compatible",
                "Cloud-native design"
            ],
            cons=[
                "Limited APM features beyond tracing",
                "Requires additional tools for full observability",
                "Manual configuration and maintenance",
                "No commercial support"
            ],
            enterprise_features=[
                "Self-hosted deployment"
            ]
        )
        
        return tools
    
    def evaluate_tools(self, requirements: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Evaluate APM tools against requirements"""
        
        evaluations = []
        
        for tool_name, tool in self.tools.items():
            score = self._calculate_score(tool, requirements)
            
            evaluation = {
                'tool': tool_name,
                'name': tool.name,
                'vendor': tool.vendor,
                'overall_score': score['total'],
                'category_scores': score['categories'],
                'matching_requirements': score['matching_requirements'],
                'gaps': score['gaps'],
                'recommendation': self._generate_recommendation(tool, score, requirements)
            }
            
            evaluations.append(evaluation)
        
        # Sort by overall score
        evaluations.sort(key=lambda x: x['overall_score'], reverse=True)
        
        return evaluations
    
    def _calculate_score(self, tool: APMTool, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate score for a tool against requirements"""
        
        scores = {
            'language_support': 0,
            'feature_coverage': 0,
            'ease_of_implementation': 0,
            'cost_effectiveness': 0,
            'enterprise_readiness': 0,
            'vendor_support': 0
        }
        
        matching_requirements = []
        gaps = []
        
        # Language support score
        required_languages = requirements.get('languages', [])
        if required_languages:
            supported_count = sum(1 for lang in required_languages if lang in tool.language_support)
            scores['language_support'] = (supported_count / len(required_languages)) * 100
            
            if supported_count == len(required_languages):
                matching_requirements.append("All required languages supported")
            else:
                unsupported = [lang for lang in required_languages if lang not in tool.language_support]
                gaps.append(f"Missing support for: {', '.join(unsupported)}")
        
        # Feature coverage score
        required_features = requirements.get('features', [])
        if required_features:
            feature_scores = []
            for req_feature in required_features:
                matching_capability = next(
                    (cap for cap in tool.capabilities if req_feature.lower() in cap.feature.lower()), 
                    None
                )
                if matching_capability and matching_capability.supported:
                    feature_scores.append(matching_capability.quality_rating * 20)  # Convert to 100 scale
                    matching_requirements.append(f"{req_feature} supported with quality rating {matching_capability.quality_rating}/5")
                else:
                    feature_scores.append(0)
                    gaps.append(f"Missing or poor support for {req_feature}")
            
            scores['feature_coverage'] = sum(feature_scores) / len(feature_scores) if feature_scores else 0
        
        # Deployment model score
        required_deployment = requirements.get('deployment_model')
        if required_deployment:
            deployment_enum = DeploymentModel(required_deployment.lower())
            if deployment_enum in tool.deployment_models:
                scores['ease_of_implementation'] += 50
                matching_requirements.append(f"Supports {required_deployment} deployment")
            else:
                gaps.append(f"Does not support {required_deployment} deployment")
        
        # Enterprise features score
        required_enterprise = requirements.get('enterprise_features', [])
        if required_enterprise:
            enterprise_score = 0
            for feature in required_enterprise:
                if any(feature.lower() in ef.lower() for ef in tool.enterprise_features):
                    enterprise_score += 1
                    matching_requirements.append(f"Enterprise feature: {feature}")
                else:
                    gaps.append(f"Missing enterprise feature: {feature}")
            
            scores['enterprise_readiness'] = (enterprise_score / len(required_enterprise)) * 100 if required_enterprise else 0
        
        # Cost effectiveness (inverse of complexity for open source tools)
        if tool.pricing_model == PricingModel.FLAT_RATE:
            scores['cost_effectiveness'] = 90  # Open source
        elif tool.pricing_model in [PricingModel.PER_HOST, PricingModel.PER_USER]:
            scores['cost_effectiveness'] = 70  # Predictable pricing
        else:
            scores['cost_effectiveness'] = 50  # Volume-based or transaction-based
        
        # Vendor support score
        if tool.vendor in ["New Relic Inc.", "Datadog Inc.", "Cisco Systems"]:
            scores['vendor_support'] = 90  # Commercial vendors
        elif tool.vendor == "Elastic N.V.":
            scores['vendor_support'] = 75  # Commercial with open source
        else:
            scores['vendor_support'] = 60  # Open source/community
        
        # Calculate weighted total score
        total_score = sum(scores[category] * self.weights[category] for category in scores)
        
        return {
            'total': total_score,
            'categories': scores,
            'matching_requirements': matching_requirements,
            'gaps': gaps
        }
    
    def _generate_recommendation(self, tool: APMTool, score: Dict[str, Any], 
                               requirements: Dict[str, Any]) -> str:
        """Generate recommendation for the tool"""
        
        total_score = score['total']
        
        if total_score >= 80:
            recommendation = f"Highly Recommended - {tool.name} is an excellent fit for your requirements."
        elif total_score >= 65:
            recommendation = f"Recommended - {tool.name} meets most of your requirements with some gaps."
        elif total_score >= 50:
            recommendation = f"Consider with Caution - {tool.name} has significant gaps for your needs."
        else:
            recommendation = f"Not Recommended - {tool.name} does not align well with your requirements."
        
        # Add specific guidance
        top_strength = max(score['categories'].items(), key=lambda x: x[1])
        recommendation += f" Strongest area: {top_strength[0]} ({top_strength[1]:.0f}/100)."
        
        if score['gaps']:
            recommendation += f" Key gaps: {', '.join(score['gaps'][:2])}."
        
        return recommendation

# Implementation Configuration Generator
class APMImplementationGenerator:
    """Generate implementation configurations for different APM tools"""
    
    def __init__(self):
        self.implementations = {}
    
    def generate_new_relic_config(self, app_name: str, license_key: str, 
                                environment: str = "production") -> Dict[str, Any]:
        """Generate New Relic configuration"""
        
        config = {
            'agent_configs': {
                'java': {
                    'app_name': app_name,
                    'license_key': license_key,
                    'environment': environment,
                    'jvm_args': [
                        f'-javaagent:/path/to/newrelic.jar',
                        f'-Dnewrelic.config.app_name={app_name}',
                        f'-Dnewrelic.config.license_key={license_key}',
                        f'-Dnewrelic.config.environment={environment}',
                        '-Dnewrelic.config.distributed_tracing.enabled=true'
                    ]
                },
                'python': {
                    'config_file': 'newrelic.ini',
                    'environment_vars': {
                        'NEW_RELIC_APP_NAME': app_name,
                        'NEW_RELIC_LICENSE_KEY': license_key,
                        'NEW_RELIC_ENVIRONMENT': environment,
                        'NEW_RELIC_DISTRIBUTED_TRACING_ENABLED': 'true'
                    },
                    'pip_install': 'newrelic',
                    'initialization': 'newrelic-admin run-program python app.py'
                },
                'nodejs': {
                    'package': 'newrelic',
                    'require': "require('newrelic');",
                    'config_file': 'newrelic.js',
                    'environment_vars': {
                        'NEW_RELIC_APP_NAME': app_name,
                        'NEW_RELIC_LICENSE_KEY': license_key,
                        'NEW_RELIC_ENVIRONMENT': environment
                    }
                }
            },
            'kubernetes_deployment': {
                'deployment_spec': {
                    'env': [
                        {'name': 'NEW_RELIC_APP_NAME', 'value': app_name},
                        {'name': 'NEW_RELIC_LICENSE_KEY', 'valueFrom': {'secretKeyRef': {'name': 'newrelic-secret', 'key': 'license-key'}}},
                        {'name': 'NEW_RELIC_ENVIRONMENT', 'value': environment}
                    ]
                },
                'infrastructure_agent': {
                    'daemonset': 'newrelic-infrastructure',
                    'image': 'newrelic/infrastructure-k8s:latest'
                }
            },
            'alerts': [
                {
                    'name': f'{app_name} High Response Time',
                    'condition': 'response_time > 2000ms for 5 minutes',
                    'notification': 'email,slack'
                },
                {
                    'name': f'{app_name} High Error Rate', 
                    'condition': 'error_rate > 5% for 3 minutes',
                    'notification': 'pagerduty'
                }
            ]
        }
        
        return config
    
    def generate_datadog_config(self, api_key: str, app_key: str,
                              service_name: str, environment: str = "production") -> Dict[str, Any]:
        """Generate Datadog configuration"""
        
        config = {
            'agent_configs': {
                'java': {
                    'jvm_args': [
                        '-javaagent:/path/to/dd-java-agent.jar',
                        f'-Ddd.service={service_name}',
                        f'-Ddd.env={environment}',
                        '-Ddd.version=1.0.0',
                        '-Ddd.trace.enabled=true',
                        '-Ddd.jmxfetch.enabled=true'
                    ],
                    'environment_vars': {
                        'DD_API_KEY': api_key,
                        'DD_SITE': 'datadoghq.com'
                    }
                },
                'python': {
                    'pip_install': 'ddtrace',
                    'initialization': f'ddtrace-run python app.py',
                    'environment_vars': {
                        'DD_API_KEY': api_key,
                        'DD_SERVICE': service_name,
                        'DD_ENV': environment,
                        'DD_VERSION': '1.0.0',
                        'DD_TRACE_ENABLED': 'true'
                    }
                },
                'nodejs': {
                    'npm_install': 'dd-trace',
                    'require': "require('dd-trace').init();",
                    'environment_vars': {
                        'DD_API_KEY': api_key,
                        'DD_SERVICE': service_name,
                        'DD_ENV': environment,
                        'DD_VERSION': '1.0.0'
                    }
                }
            },
            'kubernetes_deployment': {
                'datadog_agent': {
                    'deployment_type': 'daemonset',
                    'image': 'gcr.io/datadoghq/agent:latest',
                    'env': [
                        {'name': 'DD_API_KEY', 'valueFrom': {'secretKeyRef': {'name': 'datadog-secret', 'key': 'api-key'}}},
                        {'name': 'DD_SITE', 'value': 'datadoghq.com'},
                        {'name': 'DD_KUBERNETES_KUBELET_HOST', 'valueFrom': {'fieldRef': {'fieldPath': 'status.hostIP'}}},
                        {'name': 'DD_APM_ENABLED', 'value': 'true'},
                        {'name': 'DD_PROCESS_AGENT_ENABLED', 'value': 'true'}
                    ]
                }
            },
            'custom_metrics': {
                'example': """
from datadog import initialize, statsd
import time

options = {
    'api_key': '{api_key}',
    'app_key': '{app_key}'
}

initialize(**options)

# Custom metric example
statsd.increment('custom.metric.counter', tags=[f'service:{service_name}', f'env:{environment}'])
statsd.histogram('custom.metric.histogram', 42, tags=[f'service:{service_name}'])
""".format(api_key=api_key, app_key=app_key, service_name=service_name, environment=environment)
            },
            'monitors': [
                {
                    'name': f'{service_name} High Latency',
                    'type': 'metric alert',
                    'query': f'avg(last_5m):avg:trace.web.request.duration{{service:{service_name},env:{environment}}} > 2',
                    'message': f'High latency detected for {service_name}'
                },
                {
                    'name': f'{service_name} High Error Rate',
                    'type': 'metric alert', 
                    'query': f'avg(last_5m):sum:trace.web.request.errors{{service:{service_name},env:{environment}}} / sum:trace.web.request.hits{{service:{service_name},env:{environment}}} > 0.05',
                    'message': f'High error rate detected for {service_name}'
                }
            ]
        }
        
        return config
    
    def generate_elastic_apm_config(self, service_name: str, environment: str = "production",
                                  elasticsearch_url: str = "http://elasticsearch:9200") -> Dict[str, Any]:
        """Generate Elastic APM configuration"""
        
        config = {
            'apm_server': {
                'docker_compose': f"""
version: '3.8'
services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.6.0
    environment:
      - discovery.type=single-node
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
    ports:
      - "9200:9200"
    
  kibana:
    image: docker.elastic.co/kibana/kibana:8.6.0
    ports:
      - "5601:5601"
    environment:
      - ELASTICSEARCH_HOSTS={elasticsearch_url}
    depends_on:
      - elasticsearch
  
  apm-server:
    image: docker.elastic.co/apm/apm-server:8.6.0
    ports:
      - "8200:8200"
    environment:
      - output.elasticsearch.hosts=["{elasticsearch_url}"]
      - apm-server.rum.enabled=true
    depends_on:
      - elasticsearch
""",
                'config_yml': f"""
apm-server:
  host: "0.0.0.0:8200"
  rum:
    enabled: true
    
output.elasticsearch:
  hosts: ["{elasticsearch_url}"]
  
setup.kibana:
  host: "kibana:5601"
"""
            },
            'agent_configs': {
                'java': {
                    'jvm_args': [
                        '-javaagent:/path/to/elastic-apm-agent.jar',
                        f'-Delastic.apm.service_name={service_name}',
                        f'-Delastic.apm.environment={environment}',
                        '-Delastic.apm.server_urls=http://apm-server:8200',
                        '-Delastic.apm.application_packages=com.yourcompany'
                    ]
                },
                'python': {
                    'pip_install': 'elastic-apm[flask]',  # or django, etc.
                    'config': f"""
from elasticapm.contrib.flask import ElasticAPM

app.config['ELASTIC_APM'] = {{
    'SERVICE_NAME': '{service_name}',
    'SECRET_TOKEN': '',
    'SERVER_URL': 'http://apm-server:8200',
    'ENVIRONMENT': '{environment}',
}}

apm = ElasticAPM(app)
"""
                },
                'nodejs': {
                    'npm_install': 'elastic-apm-node',
                    'require': f"""
const apm = require('elastic-apm-node').start({{
  serviceName: '{service_name}',
  serverUrl: 'http://apm-server:8200',
  environment: '{environment}'
}});
"""
                }
            },
            'kubernetes_deployment': {
                'configmap': f"""
apiVersion: v1
kind: ConfigMap
metadata:
  name: apm-server-config
data:
  apm-server.yml: |
    apm-server:
      host: "0.0.0.0:8200"
      rum:
        enabled: true
    output.elasticsearch:
      hosts: ["{elasticsearch_url}"]
""",
                'deployment': """
apiVersion: apps/v1
kind: Deployment
metadata:
  name: apm-server
spec:
  replicas: 1
  selector:
    matchLabels:
      app: apm-server
  template:
    metadata:
      labels:
        app: apm-server
    spec:
      containers:
      - name: apm-server
        image: docker.elastic.co/apm/apm-server:8.6.0
        ports:
        - containerPort: 8200
        volumeMounts:
        - name: config
          mountPath: /usr/share/apm-server/apm-server.yml
          subPath: apm-server.yml
      volumes:
      - name: config
        configMap:
          name: apm-server-config
"""
            }
        }
        
        return config

def demonstrate_apm_tool_implementation():
    """Demonstrate APM tool selection and implementation"""
    
    print("🛠️  APM Tool Implementation Demo")
    print("=" * 40)
    
    # Initialize tool selector
    selector = APMToolSelector()
    
    # Define requirements
    requirements = {
        'languages': ['Java', 'Python', 'Node.js'],
        'features': [
            'Application Monitoring', 
            'Distributed Tracing', 
            'Database Monitoring',
            'Alerting',
            'Dashboards'
        ],
        'deployment_model': 'saas',
        'enterprise_features': ['SSO integration', 'RBAC'],
        'team_size': 'medium',
        'budget': 'moderate'
    }
    
    print("📋 Requirements:")
    print(f"  Languages: {', '.join(requirements['languages'])}")
    print(f"  Key Features: {', '.join(requirements['features'])}")
    print(f"  Deployment: {requirements['deployment_model']}")
    print(f"  Enterprise Features: {', '.join(requirements['enterprise_features'])}")
    
    # Evaluate tools
    print(f"\n🔍 Evaluating APM tools...")
    evaluations = selector.evaluate_tools(requirements)
    
    print(f"\nTool Evaluation Results:")
    print("=" * 50)
    
    for i, eval_result in enumerate(evaluations, 1):
        print(f"\n{i}. {eval_result['name']} (Score: {eval_result['overall_score']:.1f}/100)")
        print(f"   Vendor: {eval_result['vendor']}")
        print(f"   Recommendation: {eval_result['recommendation']}")
        
        # Show top category scores
        sorted_categories = sorted(
            eval_result['category_scores'].items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:3]
        
        print("   Top Strengths:")
        for category, score in sorted_categories:
            print(f"     • {category.replace('_', ' ').title()}: {score:.0f}/100")
        
        if eval_result['gaps']:
            print("   Key Gaps:")
            for gap in eval_result['gaps'][:2]:
                print(f"     • {gap}")
    
    # Generate implementation configs for top tools
    print(f"\n⚙️  Generating Implementation Configurations...")
    
    config_generator = APMImplementationGenerator()
    
    # New Relic configuration
    print(f"\n📝 New Relic Configuration:")
    print("-" * 30)
    
    nr_config = config_generator.generate_new_relic_config(
        app_name="ecommerce-api",
        license_key="YOUR_LICENSE_KEY",
        environment="production"
    )
    
    print("Java Agent Setup:")
    print("  JVM Args:")
    for arg in nr_config['agent_configs']['java']['jvm_args']:
        print(f"    {arg}")
    
    print(f"\nPython Agent Setup:")
    print(f"  Install: pip install {nr_config['agent_configs']['python']['pip_install']}")
    print(f"  Run: {nr_config['agent_configs']['python']['initialization']}")
    
    print(f"\nKubernetes Environment Variables:")
    for env_var in nr_config['kubernetes_deployment']['deployment_spec']['env']:
        if 'valueFrom' not in env_var:
            print(f"  {env_var['name']}: {env_var['value']}")
    
    # Datadog configuration
    print(f"\n📝 Datadog Configuration:")
    print("-" * 30)
    
    dd_config = config_generator.generate_datadog_config(
        api_key="YOUR_API_KEY",
        app_key="YOUR_APP_KEY",
        service_name="ecommerce-api",
        environment="production"
    )
    
    print("Python Agent Setup:")
    print(f"  Install: pip install {dd_config['agent_configs']['python']['pip_install']}")
    print(f"  Run: {dd_config['agent_configs']['python']['initialization']}")
    
    print(f"\nNode.js Agent Setup:")
    print(f"  Install: npm install {dd_config['agent_configs']['nodejs']['npm_install']}")
    print(f"  Require: {dd_config['agent_configs']['nodejs']['require']}")
    
    # Elastic APM configuration  
    print(f"\n📝 Elastic APM Configuration:")
    print("-" * 30)
    
    elastic_config = config_generator.generate_elastic_apm_config(
        service_name="ecommerce-api",
        environment="production"
    )
    
    print("Docker Compose Setup Available")
    print("Java Agent JVM Args:")
    for arg in elastic_config['agent_configs']['java']['jvm_args']:
        print(f"  {arg}")
    
    print(f"\nPython Agent Setup:")
    print(f"  Install: pip install {elastic_config['agent_configs']['python']['pip_install']}")
    print("  Configuration code available in config")
    
    # Summary and recommendations
    print(f"\n💡 Implementation Recommendations:")
    print("=" * 40)
    
    top_tool = evaluations[0]
    print(f"Best Overall: {top_tool['name']}")
    print(f"  • {top_tool['recommendation']}")
    print(f"  • Score: {top_tool['overall_score']:.1f}/100")
    print(f"  • Consider for: Enterprise environments requiring comprehensive monitoring")
    
    print(f"\nCost-Effective Option: Look for tools with high cost_effectiveness scores")
    print(f"Open Source Option: Consider Jaeger for distributed tracing + Prometheus/Grafana")
    print(f"Hybrid Approach: Combine specialized tools (e.g., Jaeger + Prometheus + Grafana)")

if __name__ == "__main__":
    demonstrate_apm_tool_implementation()
```

This comprehensive APM tool implementation guide provides enterprise-grade tool selection frameworks and configuration generation capabilities essential for choosing and deploying the right monitoring solution for specific environments and requirements.