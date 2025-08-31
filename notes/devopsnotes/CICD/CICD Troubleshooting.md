# CICD Troubleshooting

Comprehensive troubleshooting methodologies, diagnostic tools, and systematic problem resolution for CICD pipeline failures and performance issues.

## Table of Contents
1. [Troubleshooting Framework](#troubleshooting-framework)
2. [Common Pipeline Failures](#common-pipeline-failures)
3. [Diagnostic Tools & Techniques](#diagnostic-tools--techniques)
4. [Performance Issue Resolution](#performance-issue-resolution)
5. [Security & Compliance Issues](#security--compliance-issues)
6. [Infrastructure Problems](#infrastructure-problems)
7. [Advanced Debugging](#advanced-debugging)
8. [Automated Problem Detection](#automated-problem-detection)

## Troubleshooting Framework

### Systematic CICD Problem Resolution
```yaml
troubleshooting_framework:
  incident_classification:
    severity_levels:
      critical:
        - production_deployment_failure
        - security_breach_detected
        - complete_pipeline_outage
        - data_loss_or_corruption
        response_time: "< 15 minutes"
        escalation: ["on_call_engineer", "engineering_manager", "cto"]
      
      high:
        - staging_deployment_failure
        - test_environment_down
        - build_failures_blocking_releases
        - performance_degradation
        response_time: "< 1 hour"
        escalation: ["team_lead", "devops_engineer"]
      
      medium:
        - intermittent_test_failures
        - slow_pipeline_execution
        - non_critical_feature_issues
        - documentation_problems
        response_time: "< 4 hours"
        escalation: ["assigned_developer"]
      
      low:
        - cosmetic_issues
        - enhancement_requests
        - minor_configuration_tweaks
        response_time: "< 1 day"
        escalation: ["backlog"]

  diagnostic_approach:
    initial_assessment:
      steps:
        - gather_basic_information
        - identify_affected_components
        - determine_timeline_of_issue
        - check_recent_changes
        - review_monitoring_alerts
      
      information_collection:
        - pipeline_logs
        - system_metrics
        - error_messages
        - configuration_changes
        - deployment_history
    
    root_cause_analysis:
      methodology: "5_whys_technique"
      investigation_layers:
        - application_layer
        - platform_layer
        - infrastructure_layer
        - network_layer
        - security_layer
      
      analysis_tools:
        - log_analysis
        - metrics_correlation
        - trace_analysis
        - configuration_diff
        - dependency_analysis
    
    resolution_workflow:
      immediate_actions:
        - stabilize_production
        - implement_workarounds
        - communicate_status
        - gather_diagnostics
      
      permanent_fix:
        - identify_root_cause
        - develop_solution
        - test_solution
        - implement_fix
        - verify_resolution
        - document_lessons_learned

  monitoring_integration:
    alerting_rules:
      pipeline_failures:
        - consecutive_build_failures: "> 2"
        - deployment_failure_rate: "> 5%"
        - test_failure_spike: "> 20%"
        - pipeline_duration_increase: "> 50%"
      
      infrastructure_issues:
        - build_agent_availability: "< 80%"
        - artifact_storage_errors: "> 1%"
        - network_connectivity_issues: "> 5%"
        - resource_exhaustion: "> 90%"
    
    automated_diagnostics:
      trigger_conditions:
        - pipeline_failure_detected
        - performance_degradation
        - error_rate_threshold_exceeded
        - resource_utilization_high
      
      diagnostic_actions:
        - collect_system_metrics
        - export_relevant_logs
        - capture_configuration_state
        - run_connectivity_tests
        - generate_diagnostic_report

troubleshooting_playbooks:
  build_failures:
    compilation_errors:
      investigation_steps:
        - check_source_code_changes
        - verify_dependency_versions
        - validate_build_environment
        - review_compiler_settings
      
      common_causes:
        - syntax_errors_in_code
        - missing_dependencies
        - version_incompatibilities
        - environment_configuration_issues
      
      resolution_actions:
        - fix_syntax_errors
        - update_dependencies
        - rollback_problematic_changes
        - restore_working_configuration
    
    test_failures:
      investigation_steps:
        - identify_failing_tests
        - analyze_test_output
        - check_test_environment
        - verify_test_data_integrity
      
      common_causes:
        - code_changes_breaking_tests
        - test_environment_issues
        - flaky_tests
        - test_data_corruption
      
      resolution_actions:
        - fix_broken_tests
        - stabilize_test_environment
        - quarantine_flaky_tests
        - refresh_test_data
    
    deployment_failures:
      investigation_steps:
        - check_deployment_logs
        - verify_target_environment
        - validate_configuration
        - test_connectivity
      
      common_causes:
        - insufficient_resources
        - configuration_errors
        - network_connectivity_issues
        - permission_problems
      
      resolution_actions:
        - scale_resources
        - fix_configuration_issues
        - resolve_network_problems
        - update_permissions
```

### Advanced Pipeline Diagnostics Tool
```python
# Comprehensive CICD troubleshooting system
import json
import requests
import subprocess
import time
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import asyncio
import aiohttp
from datetime import datetime, timedelta

class SeverityLevel(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

class ComponentType(Enum):
    PIPELINE = "pipeline"
    BUILD_AGENT = "build_agent"
    ARTIFACT_STORAGE = "artifact_storage"
    DEPLOYMENT_TARGET = "deployment_target"
    DATABASE = "database"
    NETWORK = "network"
    SECURITY = "security"

@dataclass
class DiagnosticResult:
    component: ComponentType
    test_name: str
    status: str
    severity: SeverityLevel
    message: str
    details: Dict[str, Any]
    timestamp: datetime
    remediation_steps: List[str]

@dataclass
class TroubleshootingReport:
    incident_id: str
    summary: str
    affected_components: List[ComponentType]
    severity: SeverityLevel
    diagnostic_results: List[DiagnosticResult]
    root_cause: Optional[str]
    resolution_steps: List[str]
    lessons_learned: List[str]
    prevention_measures: List[str]

class CICDTroubleshooter:
    def __init__(self, config: Dict):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize monitoring clients
        self.prometheus_url = config.get('prometheus_url', 'http://localhost:9090')
        self.jenkins_url = config.get('jenkins_url', 'http://localhost:8080')
        self.jenkins_auth = (config.get('jenkins_user'), config.get('jenkins_token'))
        
        # Diagnostic test registry
        self.diagnostic_tests = {
            ComponentType.PIPELINE: [
                self._test_pipeline_connectivity,
                self._test_build_queue_status,
                self._test_pipeline_permissions,
                self._test_webhook_configuration,
            ],
            ComponentType.BUILD_AGENT: [
                self._test_agent_connectivity,
                self._test_agent_resources,
                self._test_agent_tools,
                self._test_agent_workspace,
            ],
            ComponentType.ARTIFACT_STORAGE: [
                self._test_artifact_storage_connectivity,
                self._test_storage_permissions,
                self._test_storage_capacity,
                self._test_artifact_integrity,
            ],
            ComponentType.DEPLOYMENT_TARGET: [
                self._test_deployment_connectivity,
                self._test_deployment_permissions,
                self._test_service_health,
                self._test_resource_availability,
            ],
            ComponentType.NETWORK: [
                self._test_network_connectivity,
                self._test_dns_resolution,
                self._test_firewall_rules,
                self._test_ssl_certificates,
            ],
            ComponentType.SECURITY: [
                self._test_authentication,
                self._test_authorization,
                self._test_secrets_access,
                self._test_compliance_policies,
            ]
        }
    
    async def comprehensive_diagnosis(
        self, 
        incident_description: str,
        affected_components: List[ComponentType] = None
    ) -> TroubleshootingReport:
        """Perform comprehensive diagnosis of CICD pipeline issues"""
        
        incident_id = f"INC-{int(time.time())}"
        self.logger.info(f"Starting comprehensive diagnosis for incident {incident_id}")
        
        # Determine affected components if not specified
        if affected_components is None:
            affected_components = await self._identify_affected_components(incident_description)
        
        # Run diagnostic tests
        all_results = []
        for component in affected_components:
            component_results = await self._run_component_diagnostics(component)
            all_results.extend(component_results)
        
        # Analyze results and determine severity
        severity = self._determine_incident_severity(all_results)
        
        # Perform root cause analysis
        root_cause = await self._perform_root_cause_analysis(all_results)
        
        # Generate resolution steps
        resolution_steps = self._generate_resolution_steps(all_results, root_cause)
        
        # Extract lessons learned
        lessons_learned = self._extract_lessons_learned(all_results, root_cause)
        
        # Generate prevention measures
        prevention_measures = self._generate_prevention_measures(all_results, root_cause)
        
        report = TroubleshootingReport(
            incident_id=incident_id,
            summary=incident_description,
            affected_components=affected_components,
            severity=severity,
            diagnostic_results=all_results,
            root_cause=root_cause,
            resolution_steps=resolution_steps,
            lessons_learned=lessons_learned,
            prevention_measures=prevention_measures
        )
        
        # Store report for future reference
        await self._store_troubleshooting_report(report)
        
        return report
    
    async def quick_health_check(self) -> Dict[ComponentType, List[DiagnosticResult]]:
        """Perform quick health check of all CICD components"""
        
        self.logger.info("Performing quick health check")
        
        health_results = {}
        
        for component_type in ComponentType:
            # Run only critical tests for quick check
            critical_tests = [test for test in self.diagnostic_tests[component_type][:2]]
            component_results = []
            
            for test in critical_tests:
                try:
                    result = await test()
                    component_results.append(result)
                except Exception as e:
                    component_results.append(DiagnosticResult(
                        component=component_type,
                        test_name=test.__name__,
                        status="error",
                        severity=SeverityLevel.HIGH,
                        message=f"Test execution failed: {str(e)}",
                        details={},
                        timestamp=datetime.now(),
                        remediation_steps=["Check test configuration", "Review system logs"]
                    ))
            
            health_results[component_type] = component_results
        
        return health_results
    
    async def diagnose_build_failure(self, build_id: str, job_name: str) -> DiagnosticResult:
        """Diagnose specific build failure"""
        
        self.logger.info(f"Diagnosing build failure: {job_name}#{build_id}")
        
        try:
            # Get build details from Jenkins
            build_info = await self._get_build_info(job_name, build_id)
            build_log = await self._get_build_log(job_name, build_id)
            
            # Analyze build failure
            failure_analysis = self._analyze_build_failure(build_info, build_log)
            
            return DiagnosticResult(
                component=ComponentType.PIPELINE,
                test_name="build_failure_analysis",
                status="failed",
                severity=failure_analysis['severity'],
                message=failure_analysis['message'],
                details=failure_analysis['details'],
                timestamp=datetime.now(),
                remediation_steps=failure_analysis['remediation_steps']
            )
            
        except Exception as e:
            return DiagnosticResult(
                component=ComponentType.PIPELINE,
                test_name="build_failure_analysis",
                status="error",
                severity=SeverityLevel.HIGH,
                message=f"Failed to analyze build failure: {str(e)}",
                details={'build_id': build_id, 'job_name': job_name},
                timestamp=datetime.now(),
                remediation_steps=[
                    "Check Jenkins connectivity",
                    "Verify build ID and job name",
                    "Review Jenkins logs"
                ]
            )
    
    async def diagnose_performance_issue(
        self, 
        pipeline_name: str, 
        time_range_hours: int = 24
    ) -> DiagnosticResult:
        """Diagnose pipeline performance issues"""
        
        self.logger.info(f"Diagnosing performance issues for {pipeline_name}")
        
        try:
            # Get performance metrics
            metrics = await self._get_pipeline_metrics(pipeline_name, time_range_hours)
            
            # Analyze performance patterns
            performance_analysis = self._analyze_performance_metrics(metrics)
            
            return DiagnosticResult(
                component=ComponentType.PIPELINE,
                test_name="performance_analysis",
                status=performance_analysis['status'],
                severity=performance_analysis['severity'],
                message=performance_analysis['message'],
                details=performance_analysis['details'],
                timestamp=datetime.now(),
                remediation_steps=performance_analysis['remediation_steps']
            )
            
        except Exception as e:
            return DiagnosticResult(
                component=ComponentType.PIPELINE,
                test_name="performance_analysis",
                status="error",
                severity=SeverityLevel.MEDIUM,
                message=f"Failed to analyze performance: {str(e)}",
                details={'pipeline': pipeline_name},
                timestamp=datetime.now(),
                remediation_steps=[
                    "Check monitoring system connectivity",
                    "Verify pipeline name",
                    "Review metrics collection"
                ]
            )
    
    # Component-specific diagnostic tests
    async def _test_pipeline_connectivity(self) -> DiagnosticResult:
        """Test pipeline system connectivity"""
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.jenkins_url}/api/json",
                    auth=aiohttp.BasicAuth(*self.jenkins_auth),
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return DiagnosticResult(
                            component=ComponentType.PIPELINE,
                            test_name="pipeline_connectivity",
                            status="passed",
                            severity=SeverityLevel.INFO,
                            message="Pipeline system is accessible",
                            details={"jenkins_version": data.get("version", "unknown")},
                            timestamp=datetime.now(),
                            remediation_steps=[]
                        )
                    else:
                        return DiagnosticResult(
                            component=ComponentType.PIPELINE,
                            test_name="pipeline_connectivity",
                            status="failed",
                            severity=SeverityLevel.HIGH,
                            message=f"Pipeline system returned HTTP {response.status}",
                            details={"status_code": response.status},
                            timestamp=datetime.now(),
                            remediation_steps=[
                                "Check Jenkins service status",
                                "Verify network connectivity",
                                "Review authentication credentials"
                            ]
                        )
        except Exception as e:
            return DiagnosticResult(
                component=ComponentType.PIPELINE,
                test_name="pipeline_connectivity",
                status="error",
                severity=SeverityLevel.CRITICAL,
                message=f"Cannot connect to pipeline system: {str(e)}",
                details={"error": str(e)},
                timestamp=datetime.now(),
                remediation_steps=[
                    "Check if Jenkins is running",
                    "Verify URL configuration",
                    "Check network connectivity",
                    "Review firewall rules"
                ]
            )
    
    async def _test_agent_connectivity(self) -> DiagnosticResult:
        """Test build agent connectivity and availability"""
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.jenkins_url}/computer/api/json",
                    auth=aiohttp.BasicAuth(*self.jenkins_auth)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        computers = data.get("computer", [])
                        
                        online_agents = [c for c in computers if not c.get("offline", True)]
                        total_agents = len([c for c in computers if c.get("displayName") != "master"])
                        
                        if len(online_agents) == 0:
                            return DiagnosticResult(
                                component=ComponentType.BUILD_AGENT,
                                test_name="agent_connectivity",
                                status="failed",
                                severity=SeverityLevel.CRITICAL,
                                message="No build agents are online",
                                details={"total_agents": total_agents, "online_agents": 0},
                                timestamp=datetime.now(),
                                remediation_steps=[
                                    "Check agent connectivity",
                                    "Restart offline agents",
                                    "Verify agent configuration",
                                    "Review network connectivity"
                                ]
                            )
                        elif len(online_agents) < total_agents * 0.8:  # Less than 80% online
                            return DiagnosticResult(
                                component=ComponentType.BUILD_AGENT,
                                test_name="agent_connectivity",
                                status="warning",
                                severity=SeverityLevel.MEDIUM,
                                message=f"Some build agents are offline ({len(online_agents)}/{total_agents} online)",
                                details={"total_agents": total_agents, "online_agents": len(online_agents)},
                                timestamp=datetime.now(),
                                remediation_steps=[
                                    "Investigate offline agents",
                                    "Check agent logs",
                                    "Verify connectivity to master"
                                ]
                            )
                        else:
                            return DiagnosticResult(
                                component=ComponentType.BUILD_AGENT,
                                test_name="agent_connectivity",
                                status="passed",
                                severity=SeverityLevel.INFO,
                                message=f"Build agents are healthy ({len(online_agents)}/{total_agents} online)",
                                details={"total_agents": total_agents, "online_agents": len(online_agents)},
                                timestamp=datetime.now(),
                                remediation_steps=[]
                            )
                    else:
                        return DiagnosticResult(
                            component=ComponentType.BUILD_AGENT,
                            test_name="agent_connectivity",
                            status="error",
                            severity=SeverityLevel.HIGH,
                            message=f"Failed to get agent status: HTTP {response.status}",
                            details={"status_code": response.status},
                            timestamp=datetime.now(),
                            remediation_steps=[
                                "Check Jenkins API accessibility",
                                "Verify authentication",
                                "Review Jenkins logs"
                            ]
                        )
        except Exception as e:
            return DiagnosticResult(
                component=ComponentType.BUILD_AGENT,
                test_name="agent_connectivity",
                status="error",
                severity=SeverityLevel.HIGH,
                message=f"Agent connectivity test failed: {str(e)}",
                details={"error": str(e)},
                timestamp=datetime.now(),
                remediation_steps=[
                    "Check network connectivity",
                    "Verify Jenkins configuration",
                    "Review system logs"
                ]
            )
    
    async def _test_network_connectivity(self) -> DiagnosticResult:
        """Test network connectivity to critical services"""
        
        critical_endpoints = self.config.get('critical_endpoints', [
            'github.com:443',
            'registry.hub.docker.com:443',
            'amazonaws.com:443'
        ])
        
        failed_endpoints = []
        slow_endpoints = []
        
        for endpoint in critical_endpoints:
            try:
                host, port = endpoint.split(':')
                port = int(port)
                
                start_time = time.time()
                
                # Test TCP connectivity
                import socket
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(10)
                result = sock.connect_ex((host, port))
                sock.close()
                
                connection_time = time.time() - start_time
                
                if result == 0:
                    if connection_time > 5.0:  # Slow connection
                        slow_endpoints.append({
                            'endpoint': endpoint,
                            'connection_time': connection_time
                        })
                else:
                    failed_endpoints.append({
                        'endpoint': endpoint,
                        'error_code': result
                    })
                    
            except Exception as e:
                failed_endpoints.append({
                    'endpoint': endpoint,
                    'error': str(e)
                })
        
        if failed_endpoints:
            return DiagnosticResult(
                component=ComponentType.NETWORK,
                test_name="network_connectivity",
                status="failed",
                severity=SeverityLevel.HIGH,
                message=f"Cannot connect to {len(failed_endpoints)} critical endpoints",
                details={
                    "failed_endpoints": failed_endpoints,
                    "slow_endpoints": slow_endpoints
                },
                timestamp=datetime.now(),
                remediation_steps=[
                    "Check network connectivity",
                    "Review firewall rules",
                    "Verify DNS resolution",
                    "Check proxy configuration"
                ]
            )
        elif slow_endpoints:
            return DiagnosticResult(
                component=ComponentType.NETWORK,
                test_name="network_connectivity",
                status="warning",
                severity=SeverityLevel.MEDIUM,
                message=f"Slow connectivity to {len(slow_endpoints)} endpoints",
                details={"slow_endpoints": slow_endpoints},
                timestamp=datetime.now(),
                remediation_steps=[
                    "Check network performance",
                    "Review bandwidth utilization",
                    "Consider CDN or caching"
                ]
            )
        else:
            return DiagnosticResult(
                component=ComponentType.NETWORK,
                test_name="network_connectivity",
                status="passed",
                severity=SeverityLevel.INFO,
                message="Network connectivity to critical endpoints is healthy",
                details={"tested_endpoints": len(critical_endpoints)},
                timestamp=datetime.now(),
                remediation_steps=[]
            )
    
    def _analyze_build_failure(self, build_info: Dict, build_log: str) -> Dict[str, Any]:
        """Analyze build failure and provide diagnosis"""
        
        failure_patterns = {
            'compilation_error': {
                'patterns': ['error: ', 'Error:', 'compilation terminated'],
                'severity': SeverityLevel.HIGH,
                'remediation': [
                    "Review compilation errors in the log",
                    "Check source code syntax",
                    "Verify compiler version and flags"
                ]
            },
            'test_failure': {
                'patterns': ['Tests run:', 'FAILED', 'AssertionError', 'Test failed'],
                'severity': SeverityLevel.MEDIUM,
                'remediation': [
                    "Review failed test cases",
                    "Check test data and environment",
                    "Run tests locally to reproduce"
                ]
            },
            'dependency_error': {
                'patterns': ['Could not resolve', 'Package not found', 'dependency failed'],
                'severity': SeverityLevel.HIGH,
                'remediation': [
                    "Check dependency versions",
                    "Verify package repository access",
                    "Review dependency configuration"
                ]
            },
            'timeout_error': {
                'patterns': ['Timeout', 'timed out', 'Build timed out'],
                'severity': SeverityLevel.MEDIUM,
                'remediation': [
                    "Increase build timeout",
                    "Optimize build performance",
                    "Check resource availability"
                ]
            },
            'permission_error': {
                'patterns': ['Permission denied', 'Access denied', 'Forbidden'],
                'severity': SeverityLevel.HIGH,
                'remediation': [
                    "Check file permissions",
                    "Verify user credentials",
                    "Review access policies"
                ]
            }
        }
        
        detected_issues = []
        
        for issue_type, config in failure_patterns.items():
            for pattern in config['patterns']:
                if pattern in build_log:
                    detected_issues.append({
                        'type': issue_type,
                        'severity': config['severity'],
                        'remediation': config['remediation']
                    })
                    break
        
        if detected_issues:
            primary_issue = detected_issues[0]
            return {
                'severity': primary_issue['severity'],
                'message': f"Build failed due to {primary_issue['type'].replace('_', ' ')}",
                'details': {
                    'build_result': build_info.get('result'),
                    'duration': build_info.get('duration'),
                    'detected_issues': detected_issues
                },
                'remediation_steps': primary_issue['remediation']
            }
        else:
            return {
                'severity': SeverityLevel.HIGH,
                'message': "Build failed with unknown error",
                'details': {
                    'build_result': build_info.get('result'),
                    'duration': build_info.get('duration')
                },
                'remediation_steps': [
                    "Review complete build log",
                    "Check recent code changes",
                    "Verify build environment",
                    "Contact development team"
                ]
            }
    
    def generate_troubleshooting_guide(self, report: TroubleshootingReport) -> str:
        """Generate human-readable troubleshooting guide"""
        
        guide = f"""
# CICD Troubleshooting Guide
**Incident ID:** {report.incident_id}
**Severity:** {report.severity.value.upper()}
**Summary:** {report.summary}

## Affected Components
{', '.join([comp.value for comp in report.affected_components])}

## Diagnostic Results
"""
        
        for result in report.diagnostic_results:
            status_icon = "✅" if result.status == "passed" else "❌" if result.status == "failed" else "⚠️"
            guide += f"""
### {status_icon} {result.test_name} ({result.component.value})
**Status:** {result.status.upper()}
**Message:** {result.message}
"""
            if result.remediation_steps:
                guide += "**Remediation Steps:**\n"
                for step in result.remediation_steps:
                    guide += f"- {step}\n"
        
        if report.root_cause:
            guide += f"""
## Root Cause Analysis
{report.root_cause}
"""
        
        if report.resolution_steps:
            guide += f"""
## Resolution Steps
"""
            for i, step in enumerate(report.resolution_steps, 1):
                guide += f"{i}. {step}\n"
        
        if report.prevention_measures:
            guide += f"""
## Prevention Measures
"""
            for measure in report.prevention_measures:
                guide += f"- {measure}\n"
        
        return guide

# Usage example
async def main():
    config = {
        'prometheus_url': 'http://prometheus:9090',
        'jenkins_url': 'http://jenkins:8080',
        'jenkins_user': 'admin',
        'jenkins_token': 'your-token',
        'critical_endpoints': [
            'github.com:443',
            'registry.hub.docker.com:443',
            'my-nexus.company.com:443'
        ]
    }
    
    troubleshooter = CICDTroubleshooter(config)
    
    # Example: Comprehensive diagnosis
    report = await troubleshooter.comprehensive_diagnosis(
        "Pipeline failing with deployment errors",
        [ComponentType.PIPELINE, ComponentType.DEPLOYMENT_TARGET, ComponentType.NETWORK]
    )
    
    # Generate troubleshooting guide
    guide = troubleshooter.generate_troubleshooting_guide(report)
    print(guide)
    
    # Example: Quick health check
    health_status = await troubleshooter.quick_health_check()
    for component, results in health_status.items():
        print(f"{component.value}: {len([r for r in results if r.status == 'passed'])} passed, "
              f"{len([r for r in results if r.status == 'failed'])} failed")

if __name__ == "__main__":
    asyncio.run(main())
```

## Common Pipeline Failures

### Build Failure Resolution Matrix
```yaml
build_failure_patterns:
  compilation_errors:
    java_compilation:
      symptoms:
        - "error: cannot find symbol"
        - "error: package does not exist"
        - "error: incompatible types"
      
      root_causes:
        - missing_dependencies
        - wrong_java_version
        - classpath_issues
        - syntax_errors
      
      diagnostic_commands:
        - "javac -version"
        - "mvn dependency:tree"
        - "gradle dependencies"
        - "echo $CLASSPATH"
      
      resolution_steps:
        - verify_java_version: "Check JDK version matches requirements"
        - update_dependencies: "Update or add missing dependencies"
        - clean_build: "Run clean build to clear cache"
        - check_imports: "Verify import statements"
    
    nodejs_compilation:
      symptoms:
        - "Module not found"
        - "SyntaxError: Unexpected token"
        - "TypeError: Cannot read property"
      
      root_causes:
        - missing_node_modules
        - version_mismatch
        - syntax_errors
        - environment_variables
      
      diagnostic_commands:
        - "node --version"
        - "npm list"
        - "npm audit"
        - "npm config list"
      
      resolution_steps:
        - reinstall_modules: "Delete node_modules and run npm install"
        - check_versions: "Verify Node.js and npm versions"
        - fix_syntax: "Review and fix syntax errors"
        - set_environment: "Configure environment variables"
  
  test_failures:
    unit_test_failures:
      symptoms:
        - "Test failed: AssertionError"
        - "Tests run: X, Failures: Y"
        - "Expected X but was Y"
      
      root_causes:
        - code_logic_errors
        - test_data_issues
        - environment_differences
        - dependency_conflicts
      
      diagnostic_commands:
        - "run specific failed test"
        - "check test database state"
        - "verify test configuration"
        - "compare environments"
      
      resolution_steps:
        - fix_logic_errors: "Debug and fix application logic"
        - update_test_data: "Refresh or fix test data"
        - sync_environments: "Align test and dev environments"
        - resolve_conflicts: "Fix dependency conflicts"
    
    integration_test_failures:
      symptoms:
        - "Connection refused"
        - "Service unavailable"
        - "Timeout waiting for response"
      
      root_causes:
        - service_not_running
        - network_connectivity
        - configuration_errors
        - resource_constraints
      
      diagnostic_commands:
        - "curl -I service_endpoint"
        - "telnet host port"
        - "check service logs"
        - "monitor resource usage"
      
      resolution_steps:
        - start_services: "Ensure all required services are running"
        - fix_network: "Resolve network connectivity issues"
        - update_config: "Fix service configuration"
        - scale_resources: "Increase available resources"
  
  deployment_failures:
    kubernetes_deployment:
      symptoms:
        - "ImagePullBackOff"
        - "CrashLoopBackOff"
        - "Insufficient resources"
        - "CreateContainerConfigError"
      
      root_causes:
        - image_not_found
        - container_crashes
        - resource_limits
        - configuration_errors
      
      diagnostic_commands:
        - "kubectl describe pod"
        - "kubectl logs pod_name"
        - "kubectl get events"
        - "kubectl top nodes"
      
      resolution_steps:
        - fix_image_reference: "Correct image name or tag"
        - debug_container: "Fix container startup issues"
        - adjust_resources: "Modify resource requests/limits"
        - fix_configuration: "Correct ConfigMaps or Secrets"
    
    docker_deployment:
      symptoms:
        - "docker: Error response from daemon"
        - "Container exited with code 1"
        - "Port already in use"
      
      root_causes:
        - dockerfile_errors
        - port_conflicts
        - volume_mount_issues
        - permission_problems
      
      diagnostic_commands:
        - "docker logs container_id"
        - "docker inspect container_id"
        - "netstat -tulpn"
        - "ls -la /path/to/volume"
      
      resolution_steps:
        - fix_dockerfile: "Correct Dockerfile syntax and commands"
        - change_ports: "Use different port mappings"
        - fix_volumes: "Correct volume mount paths and permissions"
        - update_permissions: "Fix file and directory permissions"
```

This comprehensive troubleshooting system provides systematic approaches to diagnosing and resolving CICD pipeline issues, with automated diagnostic tools, detailed failure analysis, and structured resolution guidance.