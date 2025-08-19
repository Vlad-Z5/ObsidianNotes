# AWS CodeBuild: Enterprise CI/CD Build Automation Platform

> **Service Type:** CI/CD Build Service | **Tier:** CI/CD and Automation | **Global/Regional:** Regional

## Overview

AWS CodeBuild is a comprehensive, fully managed continuous integration service designed for enterprise-scale build automation. It provides secure, scalable, and cost-effective build environments with deep integration into AWS DevOps ecosystems, supporting complex CI/CD pipelines with advanced automation capabilities.

## Enterprise CodeBuild Framework

### 1. Advanced Build Orchestration Manager

```python
import boto3
import json
import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import uuid
import asyncio
from concurrent.futures import ThreadPoolExecutor
import time
import base64
import yaml

class BuildEnvironmentType(Enum):
    LINUX_CONTAINER = "LINUX_CONTAINER"
    LINUX_GPU_CONTAINER = "LINUX_GPU_CONTAINER"
    WINDOWS_CONTAINER = "WINDOWS_CONTAINER"
    WINDOWS_SERVER_2019_CONTAINER = "WINDOWS_SERVER_2019_CONTAINER"
    ARM_CONTAINER = "ARM_CONTAINER"

class ComputeType(Enum):
    BUILD_GENERAL1_SMALL = "BUILD_GENERAL1_SMALL"
    BUILD_GENERAL1_MEDIUM = "BUILD_GENERAL1_MEDIUM"
    BUILD_GENERAL1_LARGE = "BUILD_GENERAL1_LARGE"
    BUILD_GENERAL1_2XLARGE = "BUILD_GENERAL1_2XLARGE"

class BuildPhase(Enum):
    SUBMITTED = "SUBMITTED"
    QUEUED = "QUEUED"
    PROVISIONING = "PROVISIONING"
    DOWNLOAD_SOURCE = "DOWNLOAD_SOURCE"
    INSTALL = "INSTALL"
    PRE_BUILD = "PRE_BUILD"
    BUILD = "BUILD"
    POST_BUILD = "POST_BUILD"
    UPLOAD_ARTIFACTS = "UPLOAD_ARTIFACTS"
    FINALIZING = "FINALIZING"
    COMPLETED = "COMPLETED"

@dataclass
class BuildEnvironment:
    type: BuildEnvironmentType
    image: str
    compute_type: ComputeType
    environment_variables: Dict[str, str] = field(default_factory=dict)
    privileged_mode: bool = False
    certificate_arn: Optional[str] = None
    registry_credential: Optional[Dict[str, str]] = None
    image_pull_credentials_type: str = "CODEBUILD"

@dataclass
class SourceConfig:
    type: str  # CODECOMMIT, GITHUB, GITHUB_ENTERPRISE, S3, etc.
    location: str
    buildspec: Optional[str] = None
    git_clone_depth: int = 1
    report_build_status: bool = True
    insecure_ssl: bool = False
    source_identifier: Optional[str] = None

@dataclass
class ArtifactConfig:
    type: str  # S3, NO_ARTIFACTS
    location: Optional[str] = None
    name: Optional[str] = None
    namespace_type: str = "NONE"
    packaging: str = "NONE"
    path: Optional[str] = None
    encryption_disabled: bool = False

@dataclass
class BuildProject:
    name: str
    description: str
    source: SourceConfig
    artifacts: ArtifactConfig
    environment: BuildEnvironment
    service_role_arn: str
    timeout_in_minutes: int = 60
    queued_timeout_in_minutes: int = 480
    cache_config: Optional[Dict[str, Any]] = None
    vpc_config: Optional[Dict[str, Any]] = None
    logs_config: Optional[Dict[str, Any]] = None
    file_system_locations: List[Dict[str, Any]] = field(default_factory=list)
    build_batch_config: Optional[Dict[str, Any]] = None
    concurrent_build_limit: int = 1
    tags: Dict[str, str] = field(default_factory=dict)

@dataclass
class BuildMetrics:
    total_builds: int
    successful_builds: int
    failed_builds: int
    avg_duration_seconds: float
    success_rate_percent: float
    cost_per_build: float
    cache_hit_rate_percent: float
    performance_score: int

class EnterpriseCodeBuildManager:
    """
    Enterprise-grade AWS CodeBuild manager with advanced automation,
    monitoring, cost optimization, and DevOps integration capabilities.
    """
    
    def __init__(self, region: str = 'us-east-1'):
        self.codebuild = boto3.client('codebuild', region_name=region)
        self.cloudwatch = boto3.client('cloudwatch', region_name=region)
        self.logs = boto3.client('logs', region_name=region)
        self.ssm = boto3.client('ssm', region_name=region)
        self.s3 = boto3.client('s3', region_name=region)
        self.sns = boto3.client('sns', region_name=region)
        self.region = region
        self.logger = self._setup_logging()
        
        # Build tracking
        self.build_projects = {}
        self.active_builds = {}
        self.build_templates = {}
        self.build_metrics = {}
        self.optimization_rules = {}
        
    def _setup_logging(self) -> logging.Logger:
        """Configure structured logging for CodeBuild operations"""
        logger = logging.getLogger('codebuild_manager')
        logger.setLevel(logging.INFO)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - '
            '%(project_name)s - %(build_id)s - %(message)s'
        )
        
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    def create_enterprise_build_project(self, 
                                      project_config: BuildProject,
                                      buildspec_content: Optional[Dict[str, Any]] = None,
                                      validation_rules: Optional[List] = None) -> Dict[str, Any]:
        """Create enterprise build project with advanced configuration"""
        
        # Validate project configuration
        self._validate_project_config(project_config, validation_rules or [])
        
        # Generate buildspec if content provided
        if buildspec_content:
            buildspec_yaml = self._generate_buildspec(buildspec_content)
            if not project_config.source.buildspec:
                project_config.source.buildspec = buildspec_yaml
        
        try:
            # Prepare CodeBuild project parameters
            project_params = self._prepare_project_params(project_config)
            
            # Create CodeBuild project
            response = self.codebuild.create_project(**project_params)
            
            # Store project configuration
            self.build_projects[project_config.name] = {
                'config': project_config,
                'arn': response['project']['arn'],
                'created_at': datetime.utcnow(),
                'build_count': 0,
                'metrics': BuildMetrics(
                    total_builds=0,
                    successful_builds=0,
                    failed_builds=0,
                    avg_duration_seconds=0.0,
                    success_rate_percent=100.0,
                    cost_per_build=0.0,
                    cache_hit_rate_percent=0.0,
                    performance_score=100
                )
            }
            
            # Set up monitoring
            self._setup_project_monitoring(project_config.name)
            
            # Configure automated optimization
            self._setup_build_optimization(project_config.name)
            
            self.logger.info(
                f"Build project created: {project_config.name}",
                extra={'project_name': project_config.name, 'build_id': 'project'}
            )
            
            return {
                'project_name': project_config.name,
                'project_arn': response['project']['arn'],
                'status': 'created',
                'monitoring_enabled': True,
                'optimization_enabled': True
            }
            
        except Exception as e:
            self.logger.error(
                f"Failed to create build project: {e}",
                extra={'project_name': project_config.name, 'build_id': 'project'}
            )
            raise
    
    def _validate_project_config(self, 
                               config: BuildProject,
                               validation_rules: List):
        """Validate build project configuration"""
        
        # Basic validation
        if not config.name or len(config.name) < 2:
            raise ValueError("Project name must be at least 2 characters")
        
        if not config.service_role_arn:
            raise ValueError("Service role ARN is required")
        
        # Environment validation
        if config.environment.privileged_mode and config.environment.type != BuildEnvironmentType.LINUX_CONTAINER:
            raise ValueError("Privileged mode only supported for Linux containers")
        
        # Timeout validation
        if config.timeout_in_minutes < 5 or config.timeout_in_minutes > 480:
            raise ValueError("Timeout must be between 5 and 480 minutes")
        
        # Enterprise validation rules
        for rule in validation_rules:
            rule(config)
        
        # Security validation
        self._validate_project_security(config)
    
    def _validate_project_security(self, config: BuildProject):
        """Validate project security requirements"""
        
        # Check for sensitive data in environment variables
        sensitive_keywords = ['password', 'secret', 'key', 'token', 'credential']
        
        for var_name, var_value in config.environment.environment_variables.items():
            if any(keyword in var_name.lower() for keyword in sensitive_keywords):
                self.logger.warning(
                    f"Potential sensitive data in environment variable: {var_name}"
                )
        
        # Validate VPC configuration if present
        if config.vpc_config:
            required_vpc_fields = ['vpcId', 'subnets', 'securityGroupIds']
            for field in required_vpc_fields:
                if field not in config.vpc_config:
                    raise ValueError(f"VPC configuration missing required field: {field}")
    
    def _prepare_project_params(self, config: BuildProject) -> Dict[str, Any]:
        """Prepare CodeBuild project parameters"""
        
        params = {
            'name': config.name,
            'description': config.description,
            'source': {
                'type': config.source.type,
                'location': config.source.location,
                'gitCloneDepth': config.source.git_clone_depth,
                'reportBuildStatus': config.source.report_build_status,
                'insecureSsl': config.source.insecure_ssl
            },
            'artifacts': {
                'type': config.artifacts.type
            },
            'environment': {
                'type': config.environment.type.value,
                'image': config.environment.image,
                'computeType': config.environment.compute_type.value,
                'privilegedMode': config.environment.privileged_mode,
                'imagePullCredentialsType': config.environment.image_pull_credentials_type
            },
            'serviceRole': config.service_role_arn,
            'timeoutInMinutes': config.timeout_in_minutes,
            'queuedTimeoutInMinutes': config.queued_timeout_in_minutes,
            'concurrentBuildLimit': config.concurrent_build_limit,
            'tags': [
                {'key': k, 'value': v} for k, v in config.tags.items()
            ]
        }
        
        # Add buildspec if provided
        if config.source.buildspec:
            params['source']['buildspec'] = config.source.buildspec
        
        # Add source identifier if provided
        if config.source.source_identifier:
            params['source']['sourceIdentifier'] = config.source.source_identifier
        
        # Add artifacts configuration
        if config.artifacts.location:
            params['artifacts']['location'] = config.artifacts.location
        if config.artifacts.name:
            params['artifacts']['name'] = config.artifacts.name
        if config.artifacts.namespace_type != "NONE":
            params['artifacts']['namespaceType'] = config.artifacts.namespace_type
        if config.artifacts.packaging != "NONE":
            params['artifacts']['packaging'] = config.artifacts.packaging
        if config.artifacts.path:
            params['artifacts']['path'] = config.artifacts.path
        
        params['artifacts']['encryptionDisabled'] = config.artifacts.encryption_disabled
        
        # Add environment variables
        if config.environment.environment_variables:
            params['environment']['environmentVariables'] = [
                {
                    'name': name,
                    'value': value,
                    'type': 'PLAINTEXT'
                }
                for name, value in config.environment.environment_variables.items()
            ]
        
        # Add certificate if provided
        if config.environment.certificate_arn:
            params['environment']['certificate'] = config.environment.certificate_arn
        
        # Add registry credential if provided
        if config.environment.registry_credential:
            params['environment']['registryCredential'] = config.environment.registry_credential
        
        # Add cache configuration
        if config.cache_config:
            params['cache'] = config.cache_config
        
        # Add VPC configuration
        if config.vpc_config:
            params['vpcConfig'] = config.vpc_config
        
        # Add logs configuration
        if config.logs_config:
            params['logsConfig'] = config.logs_config
        
        # Add file system locations
        if config.file_system_locations:
            params['fileSystemLocations'] = config.file_system_locations
        
        # Add build batch configuration
        if config.build_batch_config:
            params['buildBatchConfig'] = config.build_batch_config
        
        return params
    
    def _generate_buildspec(self, buildspec_content: Dict[str, Any]) -> str:
        """Generate buildspec YAML from configuration"""
        
        # Set default version if not provided
        if 'version' not in buildspec_content:
            buildspec_content['version'] = 0.2
        
        # Add enterprise defaults
        enterprise_defaults = {
            'env': {
                'variables': {
                    'BUILD_TIMESTAMP': '$(date -Iseconds)',
                    'BUILD_INITIATOR': '$(echo $CODEBUILD_INITIATOR)',
                    'BUILD_ID': '$(echo $CODEBUILD_BUILD_ID)',
                    'BUILD_NUMBER': '$(echo $CODEBUILD_BUILD_NUMBER)',
                    'COMMIT_ID': '$(echo $CODEBUILD_RESOLVED_SOURCE_VERSION)'
                }
            }
        }
        
        # Merge with provided content
        if 'env' in buildspec_content:
            if 'variables' in buildspec_content['env']:
                enterprise_defaults['env']['variables'].update(
                    buildspec_content['env']['variables']
                )
                buildspec_content['env']['variables'] = enterprise_defaults['env']['variables']
            else:
                buildspec_content['env'].update(enterprise_defaults['env'])
        else:
            buildspec_content.update(enterprise_defaults)
        
        # Add enterprise reporting if not present
        if 'reports' not in buildspec_content:
            buildspec_content['reports'] = {
                'build-reports': {
                    'files': ['**/*'],
                    'base-directory': 'reports',
                    'discard-paths': False
                }
            }
        
        return yaml.dump(buildspec_content, default_flow_style=False)
    
    async def execute_enterprise_build(self, 
                                     project_name: str,
                                     source_version: str = 'main',
                                     environment_variables_override: Optional[Dict[str, str]] = None,
                                     build_timeout_override: Optional[int] = None,
                                     privileged_mode_override: Optional[bool] = None,
                                     build_spec_override: Optional[str] = None,
                                     artifacts_override: Optional[Dict[str, Any]] = None,
                                     cache_override: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute enterprise build with comprehensive monitoring"""
        
        if project_name not in self.build_projects:
            raise ValueError(f"Build project '{project_name}' not found")
        
        # Prepare build parameters
        build_params = {
            'projectName': project_name,
            'sourceVersion': source_version
        }
        
        # Add overrides if provided
        if environment_variables_override:
            build_params['environmentVariablesOverride'] = [
                {
                    'name': name,
                    'value': value,
                    'type': 'PLAINTEXT'
                }
                for name, value in environment_variables_override.items()
            ]
        
        if build_timeout_override:
            build_params['timeoutInMinutesOverride'] = build_timeout_override
        
        if privileged_mode_override is not None:
            build_params['privilegedModeOverride'] = privileged_mode_override
        
        if build_spec_override:
            build_params['buildspecOverride'] = build_spec_override
        
        if artifacts_override:
            build_params['artifactsOverride'] = artifacts_override
        
        if cache_override:
            build_params['cacheOverride'] = cache_override
        
        try:
            # Start build
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.codebuild.start_build(**build_params)
            )
            
            build_info = response['build']
            build_id = build_info['id']
            
            # Track build
            build_context = {
                'project_name': project_name,
                'build_id': build_id,
                'source_version': source_version,
                'started_at': datetime.utcnow(),
                'status': 'IN_PROGRESS',
                'phases': [],
                'artifacts': [],
                'logs': None
            }
            
            self.active_builds[build_id] = build_context
            
            # Update project metrics
            self.build_projects[project_name]['build_count'] += 1
            
            self.logger.info(
                f"Build started: {build_id}",
                extra={'project_name': project_name, 'build_id': build_id}
            )
            
            # Start monitoring task
            asyncio.create_task(
                self._monitor_build_execution(build_context)
            )
            
            return {
                'build_id': build_id,
                'project_name': project_name,
                'build_arn': build_info['arn'],
                'build_number': build_info.get('buildNumber'),
                'status': 'started',
                'started_at': datetime.utcnow().isoformat(),
                'monitoring_enabled': True
            }
            
        except Exception as e:
            self.logger.error(
                f"Failed to start build: {e}",
                extra={'project_name': project_name, 'build_id': 'failed'}
            )
            raise
    
    async def _monitor_build_execution(self, build_context: Dict[str, Any]):
        """Monitor build execution with real-time updates"""
        
        build_id = build_context['build_id']
        project_name = build_context['project_name']
        
        while True:
            try:
                # Get build status
                response = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self.codebuild.batch_get_builds(ids=[build_id])
                )
                
                if not response.get('builds'):
                    break
                
                build_info = response['builds'][0]
                build_status = build_info['buildStatus']
                
                # Update build context
                build_context['status'] = build_status
                build_context['current_phase'] = build_info.get('currentPhase')
                build_context['phases'] = build_info.get('phases', [])
                
                # Check if build completed
                if build_status in ['SUCCEEDED', 'FAILED', 'FAULT', 'STOPPED', 'TIMED_OUT']:
                    await self._handle_build_completion(
                        build_context, 
                        build_info
                    )
                    break
                
                # Log phase transitions
                if build_context.get('last_phase') != build_context.get('current_phase'):
                    self.logger.info(
                        f"Build phase: {build_context.get('current_phase')}",
                        extra={'project_name': project_name, 'build_id': build_id}
                    )
                    build_context['last_phase'] = build_context.get('current_phase')
                
                # Wait before next check
                await asyncio.sleep(10)
                
            except Exception as e:
                self.logger.error(
                    f"Error monitoring build: {e}",
                    extra={'project_name': project_name, 'build_id': build_id}
                )
                await asyncio.sleep(30)
    
    async def _handle_build_completion(self, 
                                     build_context: Dict[str, Any],
                                     build_info: Dict[str, Any]):
        """Handle build completion with metrics and notifications"""
        
        project_name = build_context['project_name']
        build_id = build_context['build_id']
        build_status = build_info['buildStatus']
        
        # Calculate build duration
        start_time = build_info.get('startTime')
        end_time = build_info.get('endTime')
        
        if start_time and end_time:
            duration_seconds = (end_time - start_time).total_seconds()
        else:
            duration_seconds = (datetime.utcnow() - build_context['started_at']).total_seconds()
        
        # Update project metrics
        await self._update_build_metrics(
            project_name,
            build_status,
            duration_seconds,
            build_info
        )
        
        # Log completion
        if build_status == 'SUCCEEDED':
            self.logger.info(
                f"Build completed successfully in {duration_seconds:.1f}s",
                extra={'project_name': project_name, 'build_id': build_id}
            )
        else:
            self.logger.error(
                f"Build {build_status.lower()} after {duration_seconds:.1f}s",
                extra={'project_name': project_name, 'build_id': build_id}
            )
        
        # Send notifications
        await self._send_build_notification(
            project_name,
            build_id,
            build_status,
            duration_seconds,
            build_info
        )
        
        # Analyze build for optimization opportunities
        await self._analyze_build_performance(
            project_name,
            build_info
        )
        
        # Clean up tracking
        if build_id in self.active_builds:
            del self.active_builds[build_id]
    
    async def _update_build_metrics(self, 
                                  project_name: str,
                                  build_status: str,
                                  duration_seconds: float,
                                  build_info: Dict[str, Any]):
        """Update comprehensive build metrics"""
        
        if project_name not in self.build_projects:
            return
        
        metrics = self.build_projects[project_name]['metrics']
        
        # Update counters
        metrics.total_builds += 1
        
        if build_status == 'SUCCEEDED':
            metrics.successful_builds += 1
        else:
            metrics.failed_builds += 1
        
        # Update success rate
        metrics.success_rate_percent = (
            metrics.successful_builds / metrics.total_builds * 100
        )
        
        # Update average duration
        total_duration = metrics.avg_duration_seconds * (metrics.total_builds - 1)
        metrics.avg_duration_seconds = (
            total_duration + duration_seconds
        ) / metrics.total_builds
        
        # Calculate cost per build (rough estimate)
        compute_type = self.build_projects[project_name]['config'].environment.compute_type
        cost_per_minute = self._get_compute_cost_per_minute(compute_type)
        metrics.cost_per_build = (duration_seconds / 60) * cost_per_minute
        
        # Calculate performance score
        metrics.performance_score = self._calculate_performance_score(
            metrics.success_rate_percent,
            metrics.avg_duration_seconds,
            metrics.cache_hit_rate_percent
        )
        
        # Send metrics to CloudWatch
        await self._send_build_metrics(
            project_name,
            build_status,
            duration_seconds,
            metrics
        )
    
    def _get_compute_cost_per_minute(self, compute_type: ComputeType) -> float:
        """Get cost per minute for compute type"""
        
        cost_mapping = {
            ComputeType.BUILD_GENERAL1_SMALL: 0.005,
            ComputeType.BUILD_GENERAL1_MEDIUM: 0.01,
            ComputeType.BUILD_GENERAL1_LARGE: 0.02,
            ComputeType.BUILD_GENERAL1_2XLARGE: 0.04
        }
        
        return cost_mapping.get(compute_type, 0.01)
    
    def _calculate_performance_score(self, 
                                   success_rate: float,
                                   avg_duration: float,
                                   cache_hit_rate: float) -> int:
        """Calculate overall performance score (0-100)"""
        
        # Success rate component (40% weight)
        success_score = min(40, success_rate * 0.4)
        
        # Duration component (30% weight) - lower is better
        duration_score = max(0, 30 - (avg_duration / 60))
        
        # Cache efficiency component (30% weight)
        cache_score = cache_hit_rate * 0.3
        
        return int(success_score + duration_score + cache_score)
    
    def get_project_analytics(self, 
                            project_name: str,
                            days: int = 30) -> Dict[str, Any]:
        """Get comprehensive project analytics and insights"""
        
        if project_name not in self.build_projects:
            raise ValueError(f"Project '{project_name}' not found")
        
        project_data = self.build_projects[project_name]
        
        try:
            # Get recent builds
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=days)
            
            builds_data = self._get_builds_history(
                project_name,
                start_time,
                end_time
            )
            
            # Calculate detailed analytics
            analytics = {
                'project_name': project_name,
                'analysis_period_days': days,
                'project_info': {
                    'created_at': project_data['created_at'].isoformat(),
                    'total_builds': project_data['build_count'],
                    'environment_type': project_data['config'].environment.type.value,
                    'compute_type': project_data['config'].environment.compute_type.value,
                    'tags': project_data['config'].tags
                },
                'build_metrics': {
                    'total_builds': project_data['metrics'].total_builds,
                    'successful_builds': project_data['metrics'].successful_builds,
                    'failed_builds': project_data['metrics'].failed_builds,
                    'success_rate_percent': round(project_data['metrics'].success_rate_percent, 2),
                    'avg_duration_seconds': round(project_data['metrics'].avg_duration_seconds, 2),
                    'cost_per_build': round(project_data['metrics'].cost_per_build, 4),
                    'cache_hit_rate_percent': round(project_data['metrics'].cache_hit_rate_percent, 2),
                    'performance_score': project_data['metrics'].performance_score
                },
                'cost_analysis': self._calculate_cost_analysis(project_data['metrics'], days),
                'performance_trends': self._analyze_performance_trends(builds_data),
                'optimization_recommendations': self._generate_optimization_recommendations(
                    project_data['metrics']
                ),
                'security_analysis': self._analyze_security_posture(project_data['config'])
            }
            
            return analytics
            
        except Exception as e:
            self.logger.error(f"Failed to get project analytics: {e}")
            return {}

# Usage Example
if __name__ == "__main__":
    # Initialize CodeBuild manager
    cb_manager = EnterpriseCodeBuildManager()
    
    # Configure enterprise build environment
    build_env = BuildEnvironment(
        type=BuildEnvironmentType.LINUX_CONTAINER,
        image="aws/codebuild/amazonlinux2-x86_64-standard:4.0",
        compute_type=ComputeType.BUILD_GENERAL1_MEDIUM,
        environment_variables={
            "NODE_ENV": "production",
            "AWS_DEFAULT_REGION": "us-east-1",
            "BUILD_CACHE_ENABLED": "true"
        },
        privileged_mode=True
    )
    
    # Configure source
    source_config = SourceConfig(
        type="GITHUB",
        location="https://github.com/enterprise/web-app.git",
        buildspec="buildspec.yml",
        git_clone_depth=1,
        report_build_status=True
    )
    
    # Configure artifacts
    artifacts_config = ArtifactConfig(
        type="S3",
        location="enterprise-build-artifacts/web-app",
        name="web-app-$(date +%Y-%m-%d)",
        namespace_type="BUILD_ID",
        packaging="ZIP"
    )
    
    # Create build project
    project_config = BuildProject(
        name="enterprise-web-app",
        description="Enterprise web application build with advanced DevOps automation",
        source=source_config,
        artifacts=artifacts_config,
        environment=build_env,
        service_role_arn="arn:aws:iam::123456789012:role/CodeBuildServiceRole",
        timeout_in_minutes=60,
        cache_config={
            "type": "S3",
            "location": "enterprise-build-cache/web-app"
        },
        logs_config={
            "cloudWatchLogs": {
                "status": "ENABLED",
                "groupName": "/aws/codebuild/enterprise-web-app",
                "streamName": "builds"
            },
            "s3Logs": {
                "status": "ENABLED",
                "location": "enterprise-build-logs/web-app",
                "encryptionDisabled": False
            }
        },
        tags={
            "Environment": "Production",
            "Team": "DevOps",
            "Project": "WebApp",
            "CostCenter": "Engineering"
        }
    )
    
    # Define buildspec content
    buildspec_content = {
        "version": 0.2,
        "env": {
            "variables": {
                "NODE_ENV": "production",
                "REACT_APP_API_URL": "https://api.enterprise.com"
            },
            "parameter-store": {
                "DATABASE_URL": "/enterprise/web-app/database-url",
                "API_KEY": "/enterprise/web-app/api-key"
            }
        },
        "phases": {
            "install": {
                "runtime-versions": {
                    "nodejs": 18
                },
                "commands": [
                    "echo Installing dependencies...",
                    "npm ci --only=production",
                    "echo Installing security tools...",
                    "npm install -g audit-ci"
                ]
            },
            "pre_build": {
                "commands": [
                    "echo Running security audit...",
                    "audit-ci --moderate",
                    "echo Running lint checks...",
                    "npm run lint",
                    "echo Running unit tests...",
                    "npm run test:unit -- --coverage",
                    "echo Logging in to Amazon ECR...",
                    "aws ecr get-login-password --region $AWS_DEFAULT_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com"
                ]
            },
            "build": {
                "commands": [
                    "echo Building application...",
                    "npm run build",
                    "echo Running integration tests...",
                    "npm run test:integration",
                    "echo Building Docker image...",
                    "docker build -t $IMAGE_REPO_NAME:$IMAGE_TAG .",
                    "docker tag $IMAGE_REPO_NAME:$IMAGE_TAG $AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com/$IMAGE_REPO_NAME:$IMAGE_TAG"
                ]
            },
            "post_build": {
                "commands": [
                    "echo Running security scan on Docker image...",
                    "docker run --rm -v /var/run/docker.sock:/var/run/docker.sock aquasec/trivy:latest image $AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com/$IMAGE_REPO_NAME:$IMAGE_TAG",
                    "echo Pushing Docker image...",
                    "docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com/$IMAGE_REPO_NAME:$IMAGE_TAG",
                    "echo Creating deployment artifacts...",
                    "printf '[{\"name\":\"%s\",\"imageUri\":\"%s\"}]' $CONTAINER_NAME $AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com/$IMAGE_REPO_NAME:$IMAGE_TAG > imagedefinitions.json"
                ]
            }
        },
        "artifacts": {
            "files": [
                "imagedefinitions.json",
                "dist/**/*",
                "deployment/**/*"
            ],
            "name": "enterprise-web-app-$(date +%Y-%m-%d)"
        },
        "reports": {
            "unit-test-reports": {
                "files": [
                    "coverage/lcov.info",
                    "junit.xml"
                ],
                "file-format": "JUNITXML",
                "base-directory": "."
            },
            "integration-test-reports": {
                "files": [
                    "integration-test-results.xml"
                ],
                "file-format": "JUNITXML",
                "base-directory": "."
            },
            "security-scan-reports": {
                "files": [
                    "security-scan-results.json"
                ],
                "file-format": "CUCUMBERJSON",
                "base-directory": "."
            }
        },
        "cache": {
            "paths": [
                "/root/.npm/**/*",
                "node_modules/**/*",
                "/root/.cache/pip/**/*"
            ]
        }
    }
    
    async def run_enterprise_build():
        try:
            # Create build project
            result = cb_manager.create_enterprise_build_project(
                project_config,
                buildspec_content
            )
            
            print(f"Build project created: {result['project_name']}")
            
            # Execute build
            build_result = await cb_manager.execute_enterprise_build(
                "enterprise-web-app",
                source_version="main",
                environment_variables_override={
                    "BUILD_NUMBER": "123",
                    "DEPLOYMENT_ENV": "production",
                    "FEATURE_FLAGS": "advanced-analytics=true"
                }
            )
            
            print(f"Build started: {build_result['build_id']}")
            
            # Wait for build to complete
            await asyncio.sleep(300)  # Wait 5 minutes
            
            # Get analytics
            analytics = cb_manager.get_project_analytics("enterprise-web-app")
            print(f"Build analytics: {json.dumps(analytics, indent=2, default=str)}")
            
        except Exception as e:
            print(f"Build execution failed: {e}")
    
    # Run the example
    asyncio.run(run_enterprise_build())
```

### 2. CodeBuild DevOps Automation & Pipeline Integration

```python
import boto3
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import asyncio
from concurrent.futures import ThreadPoolExecutor
import yaml

@dataclass
class PipelineStage:
    name: str
    build_projects: List[str]
    parallel_execution: bool = True
    approval_required: bool = False
    timeout_minutes: int = 60
    environment_variables: Dict[str, str] = None

@dataclass
class BuildPipeline:
    name: str
    description: str
    stages: List[PipelineStage]
    trigger_config: Dict[str, Any]
    notification_config: Dict[str, Any]
    tags: Dict[str, str] = None

class CodeBuildDevOpsPipeline:
    """
    Enterprise DevOps pipeline manager for CodeBuild with advanced
    automation, quality gates, and deployment strategies.
    """
    
    def __init__(self):
        self.codebuild = boto3.client('codebuild')
        self.codepipeline = boto3.client('codepipeline')
        self.events = boto3.client('events')
        self.sns = boto3.client('sns')
        self.stepfunctions = boto3.client('stepfunctions')
        
        self.pipelines = {}
        self.quality_gates = {}
        self.deployment_strategies = {}
        
    def create_enterprise_pipeline(self, 
                                 pipeline_config: BuildPipeline) -> Dict[str, Any]:
        """Create enterprise CodeBuild pipeline with quality gates"""
        
        try:
            # Create Step Functions state machine for pipeline orchestration
            state_machine_definition = self._create_pipeline_state_machine(
                pipeline_config
            )
            
            sf_response = self.stepfunctions.create_state_machine(
                name=f"codebuild-pipeline-{pipeline_config.name}",
                definition=json.dumps(state_machine_definition),
                roleArn="arn:aws:iam::123456789012:role/StepFunctionsRole",
                type="STANDARD",
                loggingConfiguration={
                    'level': 'ALL',
                    'includeExecutionData': True
                },
                tracingConfiguration={
                    'enabled': True
                }
            )
            
            # Create EventBridge rule for pipeline triggers
            trigger_rule = self._create_pipeline_trigger(
                pipeline_config.name,
                pipeline_config.trigger_config,
                sf_response['stateMachineArn']
            )
            
            # Set up quality gates
            quality_gates = self._setup_quality_gates(
                pipeline_config.name,
                pipeline_config.stages
            )
            
            # Configure notifications
            notifications = self._setup_pipeline_notifications(
                pipeline_config.name,
                pipeline_config.notification_config
            )
            
            # Store pipeline configuration
            self.pipelines[pipeline_config.name] = {
                'config': pipeline_config,
                'state_machine_arn': sf_response['stateMachineArn'],
                'trigger_rule_arn': trigger_rule,
                'quality_gates': quality_gates,
                'notifications': notifications,
                'created_at': datetime.utcnow(),
                'execution_count': 0
            }
            
            return {
                'pipeline_name': pipeline_config.name,
                'state_machine_arn': sf_response['stateMachineArn'],
                'trigger_rule_arn': trigger_rule,
                'status': 'created',
                'quality_gates_enabled': len(quality_gates) > 0,
                'notifications_enabled': len(notifications) > 0
            }
            
        except Exception as e:
            print(f"Failed to create pipeline: {e}")
            raise
    
    def _create_pipeline_state_machine(self, 
                                     config: BuildPipeline) -> Dict[str, Any]:
        """Create Step Functions state machine for pipeline"""
        
        states = {}
        
        # Initialize pipeline
        states["InitializePipeline"] = {
            "Type": "Pass",
            "Parameters": {
                "pipelineName": config.name,
                "startTime.$": "$$.State.EnteredTime",
                "executionId.$": "$$.Execution.Name",
                "triggerEvent.$": "$"
            },
            "Next": "ExecuteStages"
        }
        
        # Execute stages
        states["ExecuteStages"] = {
            "Type": "Map",
            "ItemsPath": "$.stages",
            "MaxConcurrency": 3,
            "Iterator": {
                "StartAt": "ExecuteStage",
                "States": {
                    "ExecuteStage": {
                        "Type": "Task",
                        "Resource": "arn:aws:lambda:us-east-1:123456789012:function:ExecutePipelineStage",
                        "Parameters": {
                            "stageName.$": "$.name",
                            "buildProjects.$": "$.buildProjects",
                            "parallelExecution.$": "$.parallelExecution",
                            "environmentVariables.$": "$.environmentVariables"
                        },
                        "TimeoutSeconds": 3600,
                        "Retry": [
                            {
                                "ErrorEquals": ["Lambda.ServiceException"],
                                "IntervalSeconds": 2,
                                "MaxAttempts": 3,
                                "BackoffRate": 2.0
                            }
                        ],
                        "Catch": [
                            {
                                "ErrorEquals": ["States.ALL"],
                                "Next": "StageFailure",
                                "ResultPath": "$.error"
                            }
                        ],
                        "Next": "QualityGateCheck"
                    },
                    "QualityGateCheck": {
                        "Type": "Task",
                        "Resource": "arn:aws:lambda:us-east-1:123456789012:function:QualityGateCheck",
                        "Parameters": {
                            "stageName.$": "$.stageName",
                            "buildResults.$": "$.buildResults",
                            "qualityGates.$": "$.qualityGates"
                        },
                        "Next": "ApprovalCheck"
                    },
                    "ApprovalCheck": {
                        "Type": "Choice",
                        "Choices": [
                            {
                                "Variable": "$.approvalRequired",
                                "BooleanEquals": True,
                                "Next": "WaitForApproval"
                            }
                        ],
                        "Default": "StageSuccess"
                    },
                    "WaitForApproval": {
                        "Type": "Task",
                        "Resource": "arn:aws:states:::lambda:invoke.waitForTaskToken",
                        "Parameters": {
                            "FunctionName": "RequestApproval",
                            "Payload": {
                                "taskToken.$": "$$.Task.Token",
                                "stageName.$": "$.stageName",
                                "buildResults.$": "$.buildResults"
                            }
                        },
                        "Next": "StageSuccess"
                    },
                    "StageSuccess": {
                        "Type": "Pass",
                        "End": True
                    },
                    "StageFailure": {
                        "Type": "Fail",
                        "Cause": "Stage execution failed"
                    }
                }
            },
            "Next": "PipelineSuccess",
            "Catch": [
                {
                    "ErrorEquals": ["States.ALL"],
                    "Next": "PipelineFailure",
                    "ResultPath": "$.error"
                }
            ]
        }
        
        # Pipeline completion states
        states["PipelineSuccess"] = {
            "Type": "Task",
            "Resource": "arn:aws:lambda:us-east-1:123456789012:function:PipelineSuccess",
            "Parameters": {
                "pipelineName": config.name,
                "executionResults.$": "$",
                "endTime.$": "$$.State.EnteredTime"
            },
            "End": True
        }
        
        states["PipelineFailure"] = {
            "Type": "Task",
            "Resource": "arn:aws:lambda:us-east-1:123456789012:function:PipelineFailure",
            "Parameters": {
                "pipelineName": config.name,
                "error.$": "$.error",
                "endTime.$": "$$.State.EnteredTime"
            },
            "End": True
        }
        
        return {
            "Comment": f"Enterprise CodeBuild pipeline: {config.name}",
            "StartAt": "InitializePipeline",
            "States": states,
            "TimeoutSeconds": 7200  # 2 hours
        }
    
    def setup_advanced_quality_gates(self, 
                                   pipeline_name: str) -> Dict[str, Any]:
        """Set up comprehensive quality gates for build pipeline"""
        
        quality_gates = {
            'security_scan': {
                'name': 'Security Vulnerability Scan',
                'type': 'automated',
                'criteria': {
                    'max_critical_vulnerabilities': 0,
                    'max_high_vulnerabilities': 5,
                    'security_score_threshold': 80
                },
                'tools': ['snyk', 'sonarqube', 'checkmarx'],
                'blocking': True
            },
            'code_quality': {
                'name': 'Code Quality Assessment',
                'type': 'automated',
                'criteria': {
                    'min_code_coverage': 80,
                    'max_code_smells': 100,
                    'max_technical_debt_hours': 24,
                    'maintainability_rating': 'A'
                },
                'tools': ['sonarqube', 'eslint', 'codeclimate'],
                'blocking': True
            },
            'performance_test': {
                'name': 'Performance Testing',
                'type': 'automated',
                'criteria': {
                    'max_response_time_p95': 2000,  # milliseconds
                    'min_throughput_rps': 100,
                    'max_error_rate': 0.1  # percentage
                },
                'tools': ['jmeter', 'k6', 'artillery'],
                'blocking': False
            },
            'compliance_check': {
                'name': 'Compliance Validation',
                'type': 'automated',
                'criteria': {
                    'gdpr_compliance': True,
                    'sox_compliance': True,
                    'pci_compliance': True,
                    'data_classification_valid': True
                },
                'tools': ['prowler', 'chef-inspec', 'open-policy-agent'],
                'blocking': True
            },
            'architecture_review': {
                'name': 'Architecture Review',
                'type': 'manual',
                'criteria': {
                    'architecture_approved': True,
                    'scalability_reviewed': True,
                    'security_reviewed': True
                },
                'approvers': ['senior-architect', 'security-lead'],
                'blocking': True,
                'timeout_hours': 24
            },
            'business_approval': {
                'name': 'Business Stakeholder Approval',
                'type': 'manual',
                'criteria': {
                    'feature_approved': True,
                    'ux_approved': True,
                    'business_requirements_met': True
                },
                'approvers': ['product-owner', 'ux-lead'],
                'blocking': True,
                'timeout_hours': 48
            }
        }
        
        # Store quality gates
        self.quality_gates[pipeline_name] = quality_gates
        
        # Create quality gate execution functions
        self._create_quality_gate_functions(pipeline_name, quality_gates)
        
        return quality_gates
    
    def setup_deployment_strategies(self, 
                                  pipeline_name: str) -> Dict[str, Any]:
        """Set up advanced deployment strategies"""
        
        deployment_strategies = {
            'blue_green': {
                'name': 'Blue-Green Deployment',
                'description': 'Zero-downtime deployment with traffic switching',
                'stages': [
                    {
                        'name': 'deploy_green',
                        'description': 'Deploy to green environment',
                        'actions': [
                            'create_green_environment',
                            'deploy_application',
                            'run_smoke_tests',
                            'validate_health_checks'
                        ]
                    },
                    {
                        'name': 'traffic_shift',
                        'description': 'Gradually shift traffic to green',
                        'actions': [
                            'shift_10_percent_traffic',
                            'monitor_metrics_5_minutes',
                            'shift_50_percent_traffic',
                            'monitor_metrics_10_minutes',
                            'shift_100_percent_traffic'
                        ]
                    },
                    {
                        'name': 'cleanup',
                        'description': 'Clean up blue environment',
                        'actions': [
                            'terminate_blue_environment',
                            'update_dns_records',
                            'send_deployment_notification'
                        ]
                    }
                ],
                'rollback_strategy': 'immediate_traffic_switch',
                'monitoring_duration_minutes': 30
            },
            'canary': {
                'name': 'Canary Deployment',
                'description': 'Gradual rollout with risk mitigation',
                'stages': [
                    {
                        'name': 'canary_10',
                        'description': 'Deploy to 10% of infrastructure',
                        'traffic_percentage': 10,
                        'duration_minutes': 15,
                        'health_checks': ['response_time', 'error_rate', 'cpu_usage']
                    },
                    {
                        'name': 'canary_25',
                        'description': 'Expand to 25% of infrastructure',
                        'traffic_percentage': 25,
                        'duration_minutes': 30,
                        'health_checks': ['response_time', 'error_rate', 'memory_usage', 'business_metrics']
                    },
                    {
                        'name': 'canary_50',
                        'description': 'Expand to 50% of infrastructure',
                        'traffic_percentage': 50,
                        'duration_minutes': 60,
                        'health_checks': ['full_monitoring_suite']
                    },
                    {
                        'name': 'full_rollout',
                        'description': 'Complete deployment',
                        'traffic_percentage': 100,
                        'duration_minutes': 30,
                        'health_checks': ['comprehensive_validation']
                    }
                ],
                'rollback_triggers': [
                    'error_rate_increase_20_percent',
                    'response_time_increase_50_percent',
                    'cpu_usage_above_80_percent',
                    'memory_usage_above_85_percent',
                    'business_metric_degradation'
                ],
                'automatic_rollback': True
            },
            'rolling': {
                'name': 'Rolling Deployment',
                'description': 'Sequential instance-by-instance deployment',
                'batch_size': 2,
                'max_unhealthy_percentage': 20,
                'health_check_grace_period_minutes': 5,
                'stages': [
                    {
                        'name': 'batch_deployment',
                        'description': 'Deploy to batch of instances',
                        'actions': [
                            'select_batch_instances',
                            'drain_traffic',
                            'deploy_application',
                            'run_health_checks',
                            'restore_traffic'
                        ]
                    }
                ],
                'failure_handling': 'stop_and_rollback'
            },
            'feature_toggle': {
                'name': 'Feature Toggle Deployment',
                'description': 'Deployment with feature flag control',
                'stages': [
                    {
                        'name': 'deploy_with_flags_off',
                        'description': 'Deploy code with features disabled',
                        'feature_flags': {'all_new_features': False}
                    },
                    {
                        'name': 'enable_features_gradually',
                        'description': 'Gradually enable features for user segments',
                        'rollout_stages': [
                            {'segment': 'internal_users', 'percentage': 100},
                            {'segment': 'beta_users', 'percentage': 100},
                            {'segment': 'premium_users', 'percentage': 50},
                            {'segment': 'all_users', 'percentage': 10},
                            {'segment': 'all_users', 'percentage': 100}
                        ]
                    }
                ],
                'monitoring': 'feature_usage_analytics',
                'rollback_method': 'feature_flag_disable'
            }
        }
        
        # Store deployment strategies
        self.deployment_strategies[pipeline_name] = deployment_strategies
        
        return deployment_strategies

# Usage Example
if __name__ == "__main__":
    # Initialize pipeline manager
    pipeline_manager = CodeBuildDevOpsPipeline()
    
    # Define pipeline stages
    pipeline_stages = [
        PipelineStage(
            name="build_and_test",
            build_projects=["unit-test-build", "integration-test-build"],
            parallel_execution=True,
            environment_variables={
                "STAGE": "test",
                "RUN_SECURITY_SCAN": "true"
            }
        ),
        PipelineStage(
            name="security_and_quality",
            build_projects=["security-scan-build", "code-quality-build"],
            parallel_execution=True,
            approval_required=False
        ),
        PipelineStage(
            name="performance_testing",
            build_projects=["performance-test-build"],
            parallel_execution=False,
            timeout_minutes=120
        ),
        PipelineStage(
            name="staging_deployment",
            build_projects=["staging-deploy-build"],
            parallel_execution=False,
            approval_required=True,
            environment_variables={
                "DEPLOY_ENVIRONMENT": "staging",
                "DEPLOYMENT_STRATEGY": "blue_green"
            }
        ),
        PipelineStage(
            name="production_deployment",
            build_projects=["production-deploy-build"],
            parallel_execution=False,
            approval_required=True,
            environment_variables={
                "DEPLOY_ENVIRONMENT": "production",
                "DEPLOYMENT_STRATEGY": "canary"
            }
        )
    ]
    
    # Configure pipeline
    enterprise_pipeline = BuildPipeline(
        name="enterprise-web-app-pipeline",
        description="Comprehensive enterprise web application CI/CD pipeline",
        stages=pipeline_stages,
        trigger_config={
            "source": ["aws.codecommit"],
            "detail-type": ["CodeCommit Repository State Change"],
            "detail": {
                "event": ["referenceCreated", "referenceUpdated"],
                "referenceName": ["main", "develop"],
                "repositoryName": ["enterprise-web-app"]
            }
        },
        notification_config={
            "success_topic": "arn:aws:sns:us-east-1:123456789012:pipeline-success",
            "failure_topic": "arn:aws:sns:us-east-1:123456789012:pipeline-failure",
            "approval_topic": "arn:aws:sns:us-east-1:123456789012:pipeline-approval"
        },
        tags={
            "Environment": "Production",
            "Team": "DevOps",
            "Application": "WebApp"
        }
    )
    
    # Create enterprise pipeline
    result = pipeline_manager.create_enterprise_pipeline(enterprise_pipeline)
    print(f"Pipeline created: {result['pipeline_name']}")
    
    # Set up quality gates
    quality_gates = pipeline_manager.setup_advanced_quality_gates(
        "enterprise-web-app-pipeline"
    )
    print(f"Quality gates configured: {len(quality_gates)}")
    
    # Set up deployment strategies
    deployment_strategies = pipeline_manager.setup_deployment_strategies(
        "enterprise-web-app-pipeline"
    )
    print(f"Deployment strategies configured: {len(deployment_strategies)}")
```

## Advanced Enterprise Use Cases

### Multi-Cloud Build Orchestration
- **Hybrid Cloud Builds**: Coordinate builds across AWS, Azure, GCP
- **Cross-Platform Compilation**: ARM, x86, multiple OS targets
- **Global Build Distribution**: Regional build optimization
- **Resource Cost Optimization**: Dynamic compute type selection

### Security-First DevOps
- **Container Image Scanning**: Multi-layer vulnerability detection
- **Infrastructure as Code Validation**: Security policy enforcement
- **Secrets Management Integration**: Dynamic secret injection
- **Compliance Automation**: SOX, PCI, GDPR validation

### AI/ML Pipeline Integration
- **Model Training Builds**: Large-scale ML model compilation
- **Data Pipeline Validation**: ETL quality assurance
- **A/B Testing Infrastructure**: Automated experiment deployment
- **Model Performance Monitoring**: Continuous model validation

### Enterprise Governance
- **Cost Attribution**: Team/project-based cost tracking
- **Resource Quota Management**: Build resource governance
- **Audit Trail Generation**: Comprehensive build logging
- **Performance Benchmarking**: Cross-team build optimization

## Enterprise DevOps Use Cases

### Continuous Integration
- **Automated builds** triggered by source code commits
- **Multi-branch builds** for feature development and releases
- **Parallel testing** across multiple environments and configurations
- **Code quality gates** with static analysis and security scanning

### Container Workflows
- **Docker image building** with multi-stage builds and optimization
- **Container security scanning** using ECR image scanning
- **Multi-architecture builds** for ARM and x86 platforms
- **Container registry publishing** to ECR, Docker Hub, or private registries

### Testing Automation
- **Unit test execution** with coverage reporting
- **Integration testing** against real AWS services
- **Performance testing** with load testing frameworks
- **Security testing** with SAST/DAST tools integration

### Package Management
- **Artifact creation** for deployment pipelines
- **Dependency management** with caching for faster builds
- **Multi-environment packaging** with environment-specific configurations
- **Version tagging** and semantic versioning automation

### Infrastructure Testing
- **Infrastructure as Code validation** for CloudFormation and Terraform
- **Configuration testing** using tools like Terratest
- **Compliance scanning** for security and governance requirements
- **Cost estimation** for infrastructure changes

## Build Environment Types

### Linux Environments
- **Amazon Linux 2** - Standard AWS Linux environment
- **Ubuntu 18.04/20.04** - Popular development environment
- **Custom Docker images** - Your own containerized build environment

### Windows Environments
- **Windows Server 2019** - .NET applications and Windows-specific builds
- **Windows Server Core** - Lightweight Windows environment

### ARM Environments
- **Graviton2-based builds** - Cost-effective ARM64 builds
- **Multi-architecture** - Build for both x86 and ARM platforms

## Core Features

### Build Specifications
- **buildspec.yml** - Declarative build configuration
- **Inline build commands** - Simple command execution
- **Multi-phase builds** - Pre-build, build, post-build phases
- **Environment variables** - Dynamic configuration injection

### Source Integration
- **GitHub/GitHub Enterprise** - Direct integration with webhooks
- **AWS CodeCommit** - Native AWS Git repository service
- **Bitbucket** - Atlassian source code management
- **S3** - Source code stored in S3 buckets

### Advanced Features
- **Build caching** - S3-based caching for dependencies and artifacts
- **VPC support** - Access to private resources in your VPC
- **Batch builds** - Multiple related builds in a single operation
- **Report groups** - Test results and code coverage reporting

## Practical CLI Examples

### Project Management

```bash
# Create CodeBuild project
aws codebuild create-project \
  --name my-web-app-build \
  --description "Build project for web application" \
  --source '{
    "type": "GITHUB",
    "location": "https://github.com/myorg/web-app.git",
    "gitCloneDepth": 1,
    "buildspec": "buildspec.yml",
    "reportBuildStatus": true
  }' \
  --artifacts '{
    "type": "S3",
    "location": "my-build-artifacts/web-app"
  }' \
  --environment '{
    "type": "LINUX_CONTAINER",
    "image": "aws/codebuild/amazonlinux2-x86_64-standard:3.0",
    "computeType": "BUILD_GENERAL1_MEDIUM",
    "environmentVariables": [
      {
        "name": "NODE_ENV",
        "value": "production"
      },
      {
        "name": "AWS_DEFAULT_REGION",
        "value": "us-west-2"
      }
    ]
  }' \
  --service-role arn:aws:iam::123456789012:role/CodeBuildServiceRole

# Update project configuration
aws codebuild update-project \
  --name my-web-app-build \
  --environment '{
    "type": "LINUX_CONTAINER",
    "image": "aws/codebuild/amazonlinux2-x86_64-standard:4.0",
    "computeType": "BUILD_GENERAL1_LARGE",
    "environmentVariables": [
      {
        "name": "NODE_ENV",
        "value": "production"
      },
      {
        "name": "BUILD_CACHE",
        "value": "enabled"
      }
    ]
  }'

# Start build
aws codebuild start-build \
  --project-name my-web-app-build \
  --source-version main \
  --environment-variables-override name=BUILD_NUMBER,value=123 name=DEPLOYMENT_ENV,value=staging

# Start batch build
aws codebuild start-build-batch \
  --project-name my-web-app-build \
  --source-version main
```

### Build Monitoring

```bash
# List builds for project
aws codebuild list-builds-for-project \
  --project-name my-web-app-build \
  --sort-order DESCENDING

# Get build details
aws codebuild batch-get-builds \
  --ids my-web-app-build:12345678-1234-1234-1234-123456789012

# Get build logs
aws logs get-log-events \
  --log-group-name /aws/codebuild/my-web-app-build \
  --log-stream-name 12345678-1234-1234-1234-123456789012

# Stop build
aws codebuild stop-build \
  --id my-web-app-build:12345678-1234-1234-1234-123456789012
```

### Report Groups

```bash
# Create test report group
aws codebuild create-report-group \
  --name my-web-app-test-reports \
  --type TEST \
  --export-config '{
    "exportConfigType": "S3",
    "s3Destination": {
      "bucket": "my-test-reports",
      "path": "codebuild-reports",
      "packaging": "ZIP"
    }
  }'

# Create code coverage report group
aws codebuild create-report-group \
  --name my-web-app-coverage-reports \
  --type CODE_COVERAGE \
  --export-config '{
    "exportConfigType": "S3",
    "s3Destination": {
      "bucket": "my-coverage-reports",
      "path": "coverage"
    }
  }'
```

## Build Specification Examples

### Node.js Application Build

```yaml
# buildspec.yml for Node.js application
version: 0.2

env:
  variables:
    NODE_ENV: production
  parameter-store:
    DATABASE_URL: /myapp/database-url
    API_KEY: /myapp/api-key

phases:
  install:
    runtime-versions:
      nodejs: 18
    commands:
      - echo "Installing dependencies..."
      - npm ci --only=production
      
  pre_build:
    commands:
      - echo "Running pre-build tasks..."
      - npm run lint
      - npm run test:unit
      - echo "Logging in to Amazon ECR..."
      - aws ecr get-login-password --region $AWS_DEFAULT_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com
      
  build:
    commands:
      - echo "Building application..."
      - npm run build
      - echo "Building Docker image..."
      - docker build -t $IMAGE_REPO_NAME:$IMAGE_TAG .
      - docker tag $IMAGE_REPO_NAME:$IMAGE_TAG $AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com/$IMAGE_REPO_NAME:$IMAGE_TAG
      
  post_build:
    commands:
      - echo "Pushing Docker image..."
      - docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com/$IMAGE_REPO_NAME:$IMAGE_TAG
      - echo "Creating deployment artifact..."
      - printf '[{"name":"web-app","imageUri":"%s"}]' $AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com/$IMAGE_REPO_NAME:$IMAGE_TAG > imagedefinitions.json

artifacts:
  files:
    - imagedefinitions.json
    - dist/**/*
  name: web-app-$(date +%Y-%m-%d)

reports:
  test-reports:
    files:
      - 'coverage/lcov.info'
      - 'junit.xml'
    file-format: 'JUNITXML'
    base-directory: '.'

cache:
  paths:
    - '/root/.npm/**/*'
    - 'node_modules/**/*'
```

### Python Application with Testing

```yaml
# buildspec.yml for Python application
version: 0.2

env:
  variables:
    PYTHONPATH: /codebuild/output/src123456789/src
  parameter-store:
    DATABASE_PASSWORD: /myapp/db-password

phases:
  install:
    runtime-versions:
      python: 3.9
    commands:
      - echo "Installing dependencies..."
      - pip install --upgrade pip
      - pip install -r requirements.txt
      - pip install -r requirements-dev.txt
      
  pre_build:
    commands:
      - echo "Running security and quality checks..."
      - bandit -r src/
      - flake8 src/
      - mypy src/
      - echo "Running unit tests..."
      - python -m pytest tests/unit/ --cov=src --cov-report=xml --junitxml=test-results.xml
      
  build:
    commands:
      - echo "Running integration tests..."
      - python -m pytest tests/integration/ --junitxml=integration-results.xml
      - echo "Building package..."
      - python setup.py sdist bdist_wheel
      
  post_build:
    commands:
      - echo "Uploading to PyPI..."
      - twine upload dist/* --repository-url $PYPI_REPOSITORY_URL

artifacts:
  files:
    - dist/*
  name: python-package-$(date +%Y-%m-%d)

reports:
  unit-test-reports:
    files:
      - test-results.xml
    file-format: JUNITXML
  integration-test-reports:
    files:
      - integration-results.xml
    file-format: JUNITXML
  coverage-reports:
    files:
      - coverage.xml
    file-format: COBERTURAXML

cache:
  paths:
    - '/root/.cache/pip/**/*'
```

### Infrastructure as Code Validation

```yaml
# buildspec.yml for Terraform validation
version: 0.2

env:
  variables:
    TF_VERSION: 1.5.0
    TF_IN_AUTOMATION: true

phases:
  install:
    commands:
      - echo "Installing Terraform..."
      - wget https://releases.hashicorp.com/terraform/${TF_VERSION}/terraform_${TF_VERSION}_linux_amd64.zip
      - unzip terraform_${TF_VERSION}_linux_amd64.zip
      - mv terraform /usr/local/bin/
      - echo "Installing additional tools..."
      - curl -L "$(curl -s https://api.github.com/repos/aquasecurity/tfsec/releases/latest | grep -o -E "https://.+?_linux_amd64.tar.gz")" > tfsec.tar.gz
      - tar -xzf tfsec.tar.gz
      - mv tfsec /usr/local/bin/
      
  pre_build:
    commands:
      - echo "Terraform version"
      - terraform version
      - echo "Initializing Terraform..."
      - terraform init -backend=false
      - echo "Validating Terraform syntax..."
      - terraform validate
      - echo "Running security scan..."
      - tfsec . --format junit > tfsec-results.xml
      
  build:
    commands:
      - echo "Planning Terraform changes..."
      - terraform plan -out=tfplan
      - echo "Generating plan summary..."
      - terraform show -json tfplan > tfplan.json
      
  post_build:
    commands:
      - echo "Terraform validation completed"
      - echo "Plan summary:"
      - terraform show tfplan

artifacts:
  files:
    - tfplan
    - tfplan.json
  name: terraform-plan-$(date +%Y-%m-%d)

reports:
  security-scan:
    files:
      - tfsec-results.xml
    file-format: JUNITXML
```

## DevOps Automation Scripts

### Multi-Environment Build Script

```bash
#!/bin/bash
# multi-env-build.sh - Build application for multiple environments

PROJECT_NAME="my-web-app-build"
ENVIRONMENTS=("development" "staging" "production")
SOURCE_VERSION=${1:-main}

echo "Starting multi-environment builds for ${PROJECT_NAME}"

BUILD_IDS=()

# Start builds for each environment
for env in "${ENVIRONMENTS[@]}"; do
    echo "Starting build for ${env} environment..."
    
    BUILD_ID=$(aws codebuild start-build \
        --project-name ${PROJECT_NAME} \
        --source-version ${SOURCE_VERSION} \
        --environment-variables-override \
            name=ENVIRONMENT,value=${env} \
            name=BUILD_TIMESTAMP,value=$(date -Iseconds) \
        --query 'build.id' \
        --output text)
    
    BUILD_IDS+=($BUILD_ID)
    echo "Build started for ${env}: ${BUILD_ID}"
done

echo "Monitoring build progress..."

# Monitor all builds
ALL_COMPLETE=false
while [ "$ALL_COMPLETE" = false ]; do
    ALL_COMPLETE=true
    
    for build_id in "${BUILD_IDS[@]}"; do
        STATUS=$(aws codebuild batch-get-builds \
            --ids ${build_id} \
            --query 'builds[0].buildStatus' \
            --output text)
        
        if [ "$STATUS" = "IN_PROGRESS" ]; then
            ALL_COMPLETE=false
        fi
        
        echo "Build ${build_id}: ${STATUS}"
    done
    
    if [ "$ALL_COMPLETE" = false ]; then
        echo "Waiting for builds to complete..."
        sleep 30
    fi
done

# Report final results
echo "All builds completed. Final status:"
for i in "${!BUILD_IDS[@]}"; do
    build_id=${BUILD_IDS[$i]}
    env=${ENVIRONMENTS[$i]}
    
    RESULT=$(aws codebuild batch-get-builds \
        --ids ${build_id} \
        --query 'builds[0].buildStatus' \
        --output text)
    
    echo "${env}: ${RESULT}"
    
    if [ "$RESULT" != "SUCCEEDED" ]; then
        echo "Build failed for ${env}. Check logs:"
        echo "aws logs get-log-events --log-group-name /aws/codebuild/${PROJECT_NAME} --log-stream-name ${build_id}"
    fi
done
```

### Build Performance Monitor

```bash
#!/bin/bash
# build-performance-monitor.sh - Monitor build performance and costs

PROJECT_NAME=$1
DAYS=${2:-7}

if [ -z "$PROJECT_NAME" ]; then
    echo "Usage: $0 <project-name> [days]"
    exit 1
fi

echo "Analyzing build performance for ${PROJECT_NAME} over the last ${DAYS} days"

# Get builds from the last N days
START_TIME=$(date -d "${DAYS} days ago" -Iseconds)
BUILD_IDS=$(aws codebuild list-builds-for-project \
    --project-name ${PROJECT_NAME} \
    --query "ids[?@]" \
    --output text)

if [ -z "$BUILD_IDS" ]; then
    echo "No builds found for project ${PROJECT_NAME}"
    exit 1
fi

echo "Found $(echo $BUILD_IDS | wc -w) builds"

# Analyze build metrics
TOTAL_DURATION=0
TOTAL_BUILDS=0
SUCCESSFUL_BUILDS=0
FAILED_BUILDS=0

for build_id in $BUILD_IDS; do
    BUILD_INFO=$(aws codebuild batch-get-builds \
        --ids ${build_id} \
        --query 'builds[0].[buildStatus,startTime,endTime,currentPhase]' \
        --output text)
    
    read -r STATUS START_TIME_STR END_TIME_STR PHASE <<< "$BUILD_INFO"
    
    # Skip builds that haven't completed
    if [ "$STATUS" = "IN_PROGRESS" ] || [ -z "$END_TIME_STR" ]; then
        continue
    fi
    
    # Calculate duration
    START_EPOCH=$(date -d "$START_TIME_STR" +%s)
    END_EPOCH=$(date -d "$END_TIME_STR" +%s)
    DURATION=$((END_EPOCH - START_EPOCH))
    
    TOTAL_DURATION=$((TOTAL_DURATION + DURATION))
    TOTAL_BUILDS=$((TOTAL_BUILDS + 1))
    
    if [ "$STATUS" = "SUCCEEDED" ]; then
        SUCCESSFUL_BUILDS=$((SUCCESSFUL_BUILDS + 1))
    else
        FAILED_BUILDS=$((FAILED_BUILDS + 1))
    fi
    
    echo "Build ${build_id}: ${STATUS} (${DURATION}s)"
done

# Calculate averages
if [ $TOTAL_BUILDS -gt 0 ]; then
    AVERAGE_DURATION=$((TOTAL_DURATION / TOTAL_BUILDS))
    SUCCESS_RATE=$((SUCCESSFUL_BUILDS * 100 / TOTAL_BUILDS))
    
    echo ""
    echo "=== Build Performance Summary ==="
    echo "Total builds: ${TOTAL_BUILDS}"
    echo "Successful builds: ${SUCCESSFUL_BUILDS}"
    echo "Failed builds: ${FAILED_BUILDS}"
    echo "Success rate: ${SUCCESS_RATE}%"
    echo "Average build duration: ${AVERAGE_DURATION} seconds"
    echo "Total build time: ${TOTAL_DURATION} seconds"
    
    # Cost estimation (rough calculation)
    # Assuming BUILD_GENERAL1_MEDIUM at $0.005 per minute
    TOTAL_MINUTES=$((TOTAL_DURATION / 60))
    ESTIMATED_COST=$(echo "scale=2; ${TOTAL_MINUTES} * 0.005" | bc)
    echo "Estimated cost: \$${ESTIMATED_COST}"
fi
```

### Build Cache Optimization Script

```python
# optimize-build-cache.py - Analyze and optimize build cache usage
import boto3
import json
from datetime import datetime, timedelta

def analyze_build_cache(project_name, days=30):
    """Analyze build cache effectiveness for a CodeBuild project"""
    
    codebuild = boto3.client('codebuild')
    s3 = boto3.client('s3')
    
    # Get recent builds
    builds_response = codebuild.list_builds_for_project(
        projectName=project_name,
        sortOrder='DESCENDING'
    )
    
    build_ids = builds_response['ids'][:50]  # Analyze last 50 builds
    
    if not build_ids:
        print(f"No builds found for project {project_name}")
        return
    
    # Get detailed build information
    builds_detail = codebuild.batch_get_builds(ids=build_ids)
    
    cache_hits = 0
    cache_misses = 0
    total_duration = 0
    cached_duration = 0
    non_cached_duration = 0
    
    for build in builds_detail['builds']:
        if build['buildStatus'] not in ['SUCCEEDED', 'FAILED']:
            continue
            
        duration = (build['endTime'] - build['startTime']).total_seconds()
        total_duration += duration
        
        # Check if build used cache
        cache_used = False
        if 'cache' in build and build['cache']['type'] != 'NO_CACHE':
            # Look for cache-related log entries
            log_group = f"/aws/codebuild/{project_name}"
            log_stream = build['id']
            
            try:
                logs_client = boto3.client('logs')
                log_events = logs_client.get_log_events(
                    logGroupName=log_group,
                    logStreamName=log_stream,
                    startTime=int(build['startTime'].timestamp() * 1000),
                    endTime=int(build['endTime'].timestamp() * 1000)
                )
                
                for event in log_events['events']:
                    if 'cache hit' in event['message'].lower():
                        cache_used = True
                        break
                        
            except Exception as e:
                print(f"Could not retrieve logs for build {build['id']}: {e}")
        
        if cache_used:
            cache_hits += 1
            cached_duration += duration
        else:
            cache_misses += 1
            non_cached_duration += duration
    
    total_builds = cache_hits + cache_misses
    
    if total_builds > 0:
        cache_hit_rate = (cache_hits / total_builds) * 100
        avg_cached_duration = cached_duration / cache_hits if cache_hits > 0 else 0
        avg_non_cached_duration = non_cached_duration / cache_misses if cache_misses > 0 else 0
        
        time_saved = (avg_non_cached_duration - avg_cached_duration) * cache_hits
        
        print(f"\n=== Build Cache Analysis for {project_name} ===")
        print(f"Total builds analyzed: {total_builds}")
        print(f"Cache hits: {cache_hits}")
        print(f"Cache misses: {cache_misses}")
        print(f"Cache hit rate: {cache_hit_rate:.1f}%")
        print(f"Average cached build duration: {avg_cached_duration:.0f} seconds")
        print(f"Average non-cached build duration: {avg_non_cached_duration:.0f} seconds")
        print(f"Total time saved by caching: {time_saved:.0f} seconds ({time_saved/60:.1f} minutes)")
        
        # Cost savings calculation
        cost_per_minute = 0.005  # BUILD_GENERAL1_MEDIUM rate
        cost_saved = (time_saved / 60) * cost_per_minute
        print(f"Estimated cost saved: ${cost_saved:.2f}")
        
        # Recommendations
        print(f"\n=== Recommendations ===")
        if cache_hit_rate < 50:
            print("- Cache hit rate is low. Consider optimizing cache paths in buildspec.yml")
            print("- Ensure dependencies are cached properly")
        
        if avg_non_cached_duration > 600:  # 10 minutes
            print("- Long build times detected. Consider:")
            print("  - Using a larger compute type")
            print("  - Optimizing build scripts")
            print("  - Implementing better caching strategies")
        
        if cache_hits == 0:
            print("- No cache usage detected. Enable caching in buildspec.yml:")
            print("  cache:")
            print("    paths:")
            print("      - '/root/.npm/**/*'")
            print("      - 'node_modules/**/*'")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python optimize-build-cache.py <project-name> [days]")
        sys.exit(1)
    
    project_name = sys.argv[1]
    days = int(sys.argv[2]) if len(sys.argv) > 2 else 30
    
    analyze_build_cache(project_name, days)
```

## Best Practices

### Performance Optimization
- **Use caching** for dependencies and build artifacts
- **Choose appropriate compute type** based on build requirements
- **Optimize Docker builds** with multi-stage builds and layer caching
- **Parallel builds** for independent components

### Security Best Practices
- **Use IAM roles** with least privilege principle
- **Store secrets** in Parameter Store or Secrets Manager
- **Enable VPC** for builds that need private resource access
- **Scan container images** for vulnerabilities

### Cost Management
- **Right-size compute types** based on actual build requirements
- **Use build caching** to reduce build times and costs
- **Clean up old artifacts** to minimize storage costs
- **Monitor build patterns** to optimize resource usage

### Monitoring and Debugging
- **Use CloudWatch metrics** for build performance monitoring
- **Implement proper logging** with structured log formats
- **Set up build notifications** for success/failure alerts
- **Create build dashboards** for team visibility