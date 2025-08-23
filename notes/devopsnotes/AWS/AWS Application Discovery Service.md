# AWS Application Discovery Service: Enterprise Migration Intelligence Platform

> **Service Type:** Migration & Transfer | **Scope:** Regional | **Serverless:** No

## Overview

AWS Application Discovery Service is an advanced migration intelligence platform that enables enterprises to systematically discover, analyze, and plan the migration of complex on-premises infrastructure to AWS. It provides automated application dependency mapping, performance analysis, and intelligent migration recommendations, empowering organizations to execute large-scale migrations with reduced risk, optimized costs, and accelerated timelines.

## Core Architecture Components

- **Discovery Engine:** Multi-modal data collection through agents, agentless connectors, and import capabilities for comprehensive infrastructure visibility
- **Dependency Mapping:** Automated network traffic analysis and process communication discovery for complete application relationship mapping
- **Performance Analytics:** Real-time resource utilization monitoring and historical performance pattern analysis
- **Migration Intelligence:** AI-driven migration strategy recommendations with cost optimization and risk assessment
- **Application Grouping:** Machine learning-based application component identification and logical grouping
- **Cost Calculator:** AWS pricing integration for accurate TCO analysis and ROI projections
- **Migration Planner:** Wave-based migration planning with dependency-aware sequencing and timeline optimization

## DevOps & Enterprise Use Cases

### Large-Scale Enterprise Migration Planning
- **Multi-Datacenter Discovery:** Comprehensive infrastructure discovery across global enterprise datacenters with unified reporting
- **Application Portfolio Rationalization:** Automated application inventory analysis with modernization and retirement recommendations
- **Migration Wave Planning:** Dependency-aware migration sequencing with parallel execution optimization
- **Risk Assessment Automation:** Automated migration risk analysis with mitigation strategy recommendations

### Cloud Migration Strategy Development
- **6R Strategy Assessment:** Automated rehost, replatform, refactor, retire, retain, and repurchase strategy recommendations
- **Cost-Benefit Analysis:** Comprehensive TCO analysis with AWS cost optimization recommendations
- **Timeline Estimation:** Accurate migration timeline projections based on application complexity and dependencies
- **Resource Right-Sizing:** Performance-based AWS instance type recommendations for cost optimization

### Compliance & Governance
- **Regulatory Compliance Mapping:** Compliance framework assessment with data sovereignty and regulatory requirement analysis
- **Audit Trail Management:** Complete discovery and migration audit trails for regulatory compliance and enterprise governance
- **Security Assessment:** Infrastructure security posture analysis with AWS security service recommendations
- **Data Classification:** Automated sensitive data identification and protection requirement mapping

### DevOps Pipeline Integration
- **Continuous Discovery:** Automated recurring discovery with infrastructure change detection and migration plan updates
- **CI/CD Integration:** Native integration with enterprise CI/CD pipelines for automated migration workflow execution
- **Infrastructure as Code:** Automated CloudFormation and Terraform template generation for discovered applications
- **Monitoring Integration:** CloudWatch and third-party monitoring tool integration for comprehensive migration visibility

## Enterprise Migration Automation Framework

```python
import json
import boto3
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Set, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
import networkx as nx
from botocore.exceptions import ClientError

class DiscoveryMode(Enum):
    AGENT_BASED = "agent_based"
    AGENTLESS = "agentless"
    IMPORT = "import"
    CONNECTOR = "connector"

class ApplicationTier(Enum):
    WEB = "web"
    APPLICATION = "application"
    DATABASE = "database"
    CACHE = "cache"
    QUEUE = "queue"
    STORAGE = "storage"

class MigrationStrategy(Enum):
    REHOST = "rehost"  # Lift and shift
    REPLATFORM = "replatform"  # Lift, tinker, and shift
    REFACTOR = "refactor"  # Re-architect
    RETIRE = "retire"  # Remove
    RETAIN = "retain"  # Keep on-premises
    REPURCHASE = "repurchase"  # Move to SaaS

class MigrationComplexity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"

class MigrationPriority(Enum):
    IMMEDIATE = "immediate"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    DEFERRED = "deferred"

@dataclass
class DiscoveredServer:
    server_id: str
    hostname: str
    ip_address: str
    os_name: str
    os_version: str
    cpu_cores: int
    memory_mb: int
    disk_gb: float
    network_interfaces: List[Dict[str, Any]]
    processes: List[Dict[str, Any]] = field(default_factory=list)
    connections: List[Dict[str, Any]] = field(default_factory=list)
    performance_data: Dict[str, Any] = field(default_factory=dict)
    tags: Dict[str, str] = field(default_factory=dict)

@dataclass
class ApplicationComponent:
    component_id: str
    name: str
    tier: ApplicationTier
    servers: List[str]
    dependencies: List[str]
    ports: List[int]
    protocols: List[str]
    data_flows: List[Dict[str, Any]] = field(default_factory=list)
    configuration: Dict[str, Any] = field(default_factory=dict)

@dataclass
class MigrationRecommendation:
    application_id: str
    component_id: str
    strategy: MigrationStrategy
    complexity: MigrationComplexity
    priority: MigrationPriority
    estimated_effort_weeks: int
    estimated_cost: float
    target_architecture: Dict[str, Any]
    prerequisites: List[str]
    risks: List[str]
    dependencies: List[str]

@dataclass
class MigrationConfig:
    discovery_modes: List[DiscoveryMode] = field(default_factory=lambda: [DiscoveryMode.AGENT_BASED])
    collection_duration_days: int = 14
    enable_dependency_mapping: bool = True
    enable_performance_analysis: bool = True
    migration_wave_size: int = 5
    parallel_migrations: int = 2
    cost_optimization: bool = True
    security_assessment: bool = True

class EnterpriseDiscoveryManager:
    """
    Enterprise AWS Application Discovery Service manager with automated
    migration planning, dependency mapping, and cost optimization.
    """
    
    def __init__(self, 
                 region: str = 'us-east-1',
                 config: MigrationConfig = None):
        self.discovery = boto3.client('discovery', region_name=region)
        self.ec2 = boto3.client('ec2', region_name=region)
        self.pricing = boto3.client('pricing', region_name='us-east-1')  # Pricing API only in us-east-1
        self.config = config or MigrationConfig()
        self.logger = self._setup_logging()
        
    def _setup_logging(self) -> logging.Logger:
        logger = logging.getLogger('ApplicationDiscovery')
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger

    def start_comprehensive_discovery(self, 
                                    discovery_mode: DiscoveryMode = None,
                                    tags: Dict[str, str] = None) -> Dict[str, Any]:
        """Start comprehensive application discovery with multiple data sources"""
        try:
            discovery_mode = discovery_mode or DiscoveryMode.AGENT_BASED
            
            discovery_session = {
                'session_id': f"discovery-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}",
                'start_time': datetime.utcnow().isoformat(),
                'discovery_mode': discovery_mode.value,
                'status': 'active',
                'discovered_servers': 0,
                'applications_identified': 0,
                'dependencies_mapped': 0
            }
            
            # Start data collection based on mode
            if discovery_mode == DiscoveryMode.AGENT_BASED:
                collection_status = self._start_agent_based_discovery(tags)
            elif discovery_mode == DiscoveryMode.AGENTLESS:
                collection_status = self._start_agentless_discovery(tags)
            elif discovery_mode == DiscoveryMode.CONNECTOR:
                collection_status = self._start_connector_discovery(tags)
            else:
                collection_status = {'status': 'not_implemented'}
            
            discovery_session.update(collection_status)
            
            # Schedule analysis after collection period
            analysis_schedule = datetime.utcnow() + timedelta(days=self.config.collection_duration_days)
            discovery_session['analysis_scheduled'] = analysis_schedule.isoformat()
            
            self.logger.info(f"Started discovery session: {discovery_session['session_id']}")
            return discovery_session
            
        except Exception as e:
            self.logger.error(f"Error starting discovery: {str(e)}")
            raise

    def _start_agent_based_discovery(self, tags: Dict[str, str] = None) -> Dict[str, Any]:
        """Start agent-based discovery"""
        try:
            # Start data collection
            response = self.discovery.start_data_collection_by_agent_ids(
                agentIds=[]  # Empty to start collection for all agents
            )
            
            return {
                'collection_type': 'agent_based',
                'agents_started': len(response.get('agentsConfigurationStatus', [])),
                'collection_status': 'started'
            }
            
        except ClientError as e:
            self.logger.error(f"Error starting agent-based discovery: {str(e)}")
            return {'collection_status': 'failed', 'error': str(e)}

    def _start_agentless_discovery(self, tags: Dict[str, str] = None) -> Dict[str, Any]:
        """Start agentless discovery using AWS Agentless Discovery Connector"""
        try:
            # Start continuous export
            response = self.discovery.start_continuous_export(
                maxRecords=10000
            )
            
            return {
                'collection_type': 'agentless',
                'export_id': response.get('exportId'),
                'collection_status': 'started'
            }
            
        except ClientError as e:
            self.logger.error(f"Error starting agentless discovery: {str(e)}")
            return {'collection_status': 'failed', 'error': str(e)}

    def _start_connector_discovery(self, tags: Dict[str, str] = None) -> Dict[str, Any]:
        """Start discovery using AWS Discovery Connector"""
        try:
            # Get available connectors
            connectors = self.discovery.describe_connectors()
            
            if not connectors['connectors']:
                return {
                    'collection_status': 'failed',
                    'error': 'No Discovery Connectors found. Please install and configure connectors.'
                }
            
            # Start data collection for all connectors
            connector_ids = [c['connectorId'] for c in connectors['connectors']]
            
            response = self.discovery.start_data_collection_by_agent_ids(
                agentIds=connector_ids
            )
            
            return {
                'collection_type': 'connector',
                'connectors_started': len(connector_ids),
                'collection_status': 'started'
            }
            
        except ClientError as e:
            self.logger.error(f"Error starting connector discovery: {str(e)}")
            return {'collection_status': 'failed', 'error': str(e)}

    def analyze_discovered_infrastructure(self, 
                                        session_id: str = None,
                                        include_performance: bool = True) -> Dict[str, Any]:
        """Analyze discovered infrastructure and generate migration insights"""
        try:
            # Get discovered servers
            servers = self._get_discovered_servers()
            
            # Build dependency graph
            dependency_graph = self._build_dependency_graph(servers)
            
            # Identify applications
            applications = self._identify_applications(servers, dependency_graph)
            
            # Analyze performance data
            performance_analysis = {}
            if include_performance:
                performance_analysis = self._analyze_performance_data(servers)
            
            # Generate migration recommendations
            migration_recommendations = self._generate_migration_recommendations(
                servers, applications, performance_analysis
            )
            
            # Calculate migration costs
            cost_analysis = self._calculate_migration_costs(
                servers, migration_recommendations
            )
            
            analysis_report = {
                'analysis_id': f"analysis-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}",
                'session_id': session_id,
                'generated_at': datetime.utcnow().isoformat(),
                'summary': {
                    'total_servers': len(servers),
                    'applications_identified': len(applications),
                    'dependencies_mapped': len(dependency_graph.edges()),
                    'migration_recommendations': len(migration_recommendations),
                    'estimated_total_cost': cost_analysis.get('total_cost', 0)
                },
                'servers': [self._serialize_server(server) for server in servers],
                'applications': [self._serialize_application(app) for app in applications],
                'dependency_graph': self._serialize_dependency_graph(dependency_graph),
                'performance_analysis': performance_analysis,
                'migration_recommendations': [
                    self._serialize_recommendation(rec) for rec in migration_recommendations
                ],
                'cost_analysis': cost_analysis,
                'migration_waves': self._plan_migration_waves(migration_recommendations)
            }
            
            return analysis_report
            
        except Exception as e:
            self.logger.error(f"Error analyzing infrastructure: {str(e)}")
            raise

    def _get_discovered_servers(self) -> List[DiscoveredServer]:
        """Retrieve discovered servers with detailed information"""
        try:
            servers = []
            
            # Get configuration items (servers)
            paginator = self.discovery.get_paginator('list_configurations')
            
            for page in paginator.paginate(
                configurationType='SERVER',
                maxResults=100
            ):
                for config in page['configurations']:
                    server = self._parse_server_configuration(config)
                    if server:
                        # Get additional details
                        server = self._enrich_server_data(server)
                        servers.append(server)
            
            return servers
            
        except Exception as e:
            self.logger.error(f"Error retrieving discovered servers: {str(e)}")
            return []

    def _parse_server_configuration(self, config: Dict[str, Any]) -> Optional[DiscoveredServer]:
        """Parse server configuration from discovery data"""
        try:
            return DiscoveredServer(
                server_id=config.get('configurationId', ''),
                hostname=config.get('hostName', ''),
                ip_address=config.get('serverType', {}).get('vmWare', {}).get('ipAddress', ''),
                os_name=config.get('osName', ''),
                os_version=config.get('osVersion', ''),
                cpu_cores=int(config.get('cpuType', '0').split()[0]) if config.get('cpuType') else 0,
                memory_mb=int(config.get('totalRam', 0)),
                disk_gb=float(config.get('totalDiskSpace', 0)) / 1024,  # Convert MB to GB
                network_interfaces=[],  # Will be populated in enrichment
                tags=config.get('tags', {})
            )
            
        except Exception as e:
            self.logger.warning(f"Error parsing server configuration: {str(e)}")
            return None

    def _enrich_server_data(self, server: DiscoveredServer) -> DiscoveredServer:
        """Enrich server data with additional discovery information"""
        try:
            # Get network connections
            connections = self._get_server_connections(server.server_id)
            server.connections = connections
            
            # Get running processes
            processes = self._get_server_processes(server.server_id)
            server.processes = processes
            
            # Get performance data
            performance = self._get_server_performance(server.server_id)
            server.performance_data = performance
            
            return server
            
        except Exception as e:
            self.logger.warning(f"Error enriching server data for {server.server_id}: {str(e)}")
            return server

    def _get_server_connections(self, server_id: str) -> List[Dict[str, Any]]:
        """Get network connections for a server"""
        try:
            # In real implementation, this would query the discovery service
            # for network connection data
            return []
            
        except Exception as e:
            self.logger.warning(f"Error getting connections for {server_id}: {str(e)}")
            return []

    def _get_server_processes(self, server_id: str) -> List[Dict[str, Any]]:
        """Get running processes for a server"""
        try:
            # In real implementation, this would query the discovery service
            # for process data
            return []
            
        except Exception as e:
            self.logger.warning(f"Error getting processes for {server_id}: {str(e)}")
            return []

    def _get_server_performance(self, server_id: str) -> Dict[str, Any]:
        """Get performance metrics for a server"""
        try:
            # In real implementation, this would query performance metrics
            # collected over the discovery period
            return {
                'cpu_utilization_avg': 0.0,
                'memory_utilization_avg': 0.0,
                'disk_iops_avg': 0.0,
                'network_throughput_avg': 0.0
            }
            
        except Exception as e:
            self.logger.warning(f"Error getting performance data for {server_id}: {str(e)}")
            return {}

    def _build_dependency_graph(self, servers: List[DiscoveredServer]) -> nx.DiGraph:
        """Build application dependency graph from discovered connections"""
        try:
            graph = nx.DiGraph()
            
            # Add servers as nodes
            for server in servers:
                graph.add_node(
                    server.server_id,
                    hostname=server.hostname,
                    ip_address=server.ip_address,
                    server_type=self._classify_server_type(server)
                )
            
            # Add connections as edges
            for server in servers:
                for connection in server.connections:
                    # Find target server by IP
                    target_server = next(
                        (s for s in servers if s.ip_address == connection.get('destinationIp')),
                        None
                    )
                    
                    if target_server:
                        graph.add_edge(
                            server.server_id,
                            target_server.server_id,
                            port=connection.get('destinationPort'),
                            protocol=connection.get('protocol'),
                            connection_count=connection.get('connectionCount', 1)
                        )
            
            return graph
            
        except Exception as e:
            self.logger.error(f"Error building dependency graph: {str(e)}")
            return nx.DiGraph()

    def _classify_server_type(self, server: DiscoveredServer) -> ApplicationTier:
        """Classify server type based on running processes and characteristics"""
        
        # Analyze running processes to determine server role
        process_indicators = {
            ApplicationTier.WEB: ['nginx', 'apache', 'iis', 'httpd'],
            ApplicationTier.APPLICATION: ['java', 'tomcat', 'node', 'python', 'dotnet'],
            ApplicationTier.DATABASE: ['mysql', 'postgres', 'oracle', 'sqlserver', 'mongodb'],
            ApplicationTier.CACHE: ['redis', 'memcached', 'elasticsearch'],
            ApplicationTier.QUEUE: ['rabbitmq', 'activemq', 'kafka']
        }
        
        for process in server.processes:
            process_name = process.get('name', '').lower()
            for tier, indicators in process_indicators.items():
                if any(indicator in process_name for indicator in indicators):
                    return tier
        
        # Default classification based on resource characteristics
        if server.memory_mb > 16384:  # 16GB+
            return ApplicationTier.DATABASE
        elif server.cpu_cores >= 8:
            return ApplicationTier.APPLICATION
        else:
            return ApplicationTier.WEB

    def _identify_applications(self, 
                             servers: List[DiscoveredServer], 
                             dependency_graph: nx.DiGraph) -> List[ApplicationComponent]:
        """Identify application components from server dependencies"""
        try:
            applications = []
            
            # Use community detection to identify application boundaries
            communities = list(nx.weakly_connected_components(dependency_graph))
            
            for i, community in enumerate(communities):
                if len(community) < 2:  # Skip single-server "applications"
                    continue
                
                # Analyze servers in this community
                community_servers = [s for s in servers if s.server_id in community]
                
                # Determine application tier distribution
                tiers = {}
                for server in community_servers:
                    tier = self._classify_server_type(server)
                    if tier not in tiers:
                        tiers[tier] = []
                    tiers[tier].append(server.server_id)
                
                # Create application component
                app_component = ApplicationComponent(
                    component_id=f"app-{i+1}",
                    name=f"Application-{i+1}",
                    tier=ApplicationTier.APPLICATION,  # Primary tier
                    servers=list(community),
                    dependencies=self._get_application_dependencies(community, dependency_graph),
                    ports=self._get_application_ports(community_servers),
                    protocols=self._get_application_protocols(community_servers)
                )
                
                applications.append(app_component)
            
            return applications
            
        except Exception as e:
            self.logger.error(f"Error identifying applications: {str(e)}")
            return []

    def _get_application_dependencies(self, 
                                   community: Set[str], 
                                   dependency_graph: nx.DiGraph) -> List[str]:
        """Get external dependencies for an application component"""
        dependencies = []
        
        for server_id in community:
            # Find connections to servers outside this community
            for successor in dependency_graph.successors(server_id):
                if successor not in community:
                    dependencies.append(successor)
        
        return list(set(dependencies))

    def _get_application_ports(self, servers: List[DiscoveredServer]) -> List[int]:
        """Get commonly used ports for application servers"""
        ports = set()
        
        for server in servers:
            for connection in server.connections:
                port = connection.get('destinationPort')
                if port:
                    ports.add(int(port))
        
        return sorted(list(ports))

    def _get_application_protocols(self, servers: List[DiscoveredServer]) -> List[str]:
        """Get protocols used by application servers"""
        protocols = set()
        
        for server in servers:
            for connection in server.connections:
                protocol = connection.get('protocol')
                if protocol:
                    protocols.add(protocol.upper())
        
        return sorted(list(protocols))

    def _analyze_performance_data(self, servers: List[DiscoveredServer]) -> Dict[str, Any]:
        """Analyze performance data across discovered servers"""
        try:
            if not servers:
                return {}
            
            # Aggregate performance metrics
            cpu_utilizations = []
            memory_utilizations = []
            disk_iops = []
            network_throughput = []
            
            for server in servers:
                perf = server.performance_data
                if perf:
                    cpu_utilizations.append(perf.get('cpu_utilization_avg', 0))
                    memory_utilizations.append(perf.get('memory_utilization_avg', 0))
                    disk_iops.append(perf.get('disk_iops_avg', 0))
                    network_throughput.append(perf.get('network_throughput_avg', 0))
            
            analysis = {
                'summary': {
                    'avg_cpu_utilization': sum(cpu_utilizations) / len(cpu_utilizations) if cpu_utilizations else 0,
                    'avg_memory_utilization': sum(memory_utilizations) / len(memory_utilizations) if memory_utilizations else 0,
                    'avg_disk_iops': sum(disk_iops) / len(disk_iops) if disk_iops else 0,
                    'avg_network_throughput': sum(network_throughput) / len(network_throughput) if network_throughput else 0
                },
                'optimization_opportunities': [],
                'rightsizing_recommendations': []
            }
            
            # Identify optimization opportunities
            for i, server in enumerate(servers):
                perf = server.performance_data
                if not perf:
                    continue
                
                cpu_util = perf.get('cpu_utilization_avg', 0)
                memory_util = perf.get('memory_utilization_avg', 0)
                
                if cpu_util < 20 and memory_util < 30:
                    analysis['optimization_opportunities'].append({
                        'server_id': server.server_id,
                        'hostname': server.hostname,
                        'recommendation': 'Downsize server - low resource utilization',
                        'cpu_utilization': cpu_util,
                        'memory_utilization': memory_util
                    })
                elif cpu_util > 80 or memory_util > 80:
                    analysis['rightsizing_recommendations'].append({
                        'server_id': server.server_id,
                        'hostname': server.hostname,
                        'recommendation': 'Upsize server - high resource utilization',
                        'cpu_utilization': cpu_util,
                        'memory_utilization': memory_util
                    })
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing performance data: {str(e)}")
            return {}

    def _generate_migration_recommendations(self, 
                                          servers: List[DiscoveredServer],
                                          applications: List[ApplicationComponent],
                                          performance_analysis: Dict[str, Any]) -> List[MigrationRecommendation]:
        """Generate migration recommendations for discovered infrastructure"""
        try:
            recommendations = []
            
            for app in applications:
                # Analyze application characteristics
                app_servers = [s for s in servers if s.server_id in app.servers]
                
                # Determine migration strategy
                strategy = self._determine_migration_strategy(app, app_servers)
                
                # Assess migration complexity
                complexity = self._assess_migration_complexity(app, app_servers)
                
                # Determine priority
                priority = self._determine_migration_priority(app, app_servers, performance_analysis)
                
                # Estimate effort and cost
                effort_weeks = self._estimate_migration_effort(app, app_servers, strategy, complexity)
                estimated_cost = self._estimate_migration_cost(app, app_servers, strategy)
                
                # Generate target architecture
                target_architecture = self._design_target_architecture(app, app_servers, strategy)
                
                # Identify prerequisites and risks
                prerequisites = self._identify_prerequisites(app, strategy)
                risks = self._identify_risks(app, strategy, complexity)
                
                recommendation = MigrationRecommendation(
                    application_id=app.component_id,
                    component_id=app.component_id,
                    strategy=strategy,
                    complexity=complexity,
                    priority=priority,
                    estimated_effort_weeks=effort_weeks,
                    estimated_cost=estimated_cost,
                    target_architecture=target_architecture,
                    prerequisites=prerequisites,
                    risks=risks,
                    dependencies=app.dependencies
                )
                
                recommendations.append(recommendation)
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Error generating migration recommendations: {str(e)}")
            return []

    def _determine_migration_strategy(self, 
                                    app: ApplicationComponent, 
                                    servers: List[DiscoveredServer]) -> MigrationStrategy:
        """Determine optimal migration strategy for application"""
        
        # Analyze application characteristics
        total_servers = len(servers)
        total_memory = sum(s.memory_mb for s in servers)
        has_database = any(self._classify_server_type(s) == ApplicationTier.DATABASE for s in servers)
        
        # Simple decision tree for strategy selection
        if total_servers == 1 and total_memory < 8192:  # Simple, small application
            return MigrationStrategy.REHOST
        elif has_database and total_servers > 5:  # Complex application with database
            return MigrationStrategy.REPLATFORM
        elif total_servers > 10:  # Large, complex application
            return MigrationStrategy.REFACTOR
        else:
            return MigrationStrategy.REHOST

    def _assess_migration_complexity(self, 
                                   app: ApplicationComponent, 
                                   servers: List[DiscoveredServer]) -> MigrationComplexity:
        """Assess migration complexity based on application characteristics"""
        
        complexity_score = 0
        
        # Server count factor
        if len(servers) > 10:
            complexity_score += 3
        elif len(servers) > 5:
            complexity_score += 2
        elif len(servers) > 2:
            complexity_score += 1
        
        # Dependency factor
        if len(app.dependencies) > 5:
            complexity_score += 2
        elif len(app.dependencies) > 2:
            complexity_score += 1
        
        # Technology stack factor
        has_database = any(self._classify_server_type(s) == ApplicationTier.DATABASE for s in servers)
        has_cache = any(self._classify_server_type(s) == ApplicationTier.CACHE for s in servers)
        
        if has_database:
            complexity_score += 2
        if has_cache:
            complexity_score += 1
        
        # Map score to complexity level
        if complexity_score >= 7:
            return MigrationComplexity.VERY_HIGH
        elif complexity_score >= 5:
            return MigrationComplexity.HIGH
        elif complexity_score >= 3:
            return MigrationComplexity.MEDIUM
        else:
            return MigrationComplexity.LOW

    def _determine_migration_priority(self, 
                                    app: ApplicationComponent,
                                    servers: List[DiscoveredServer],
                                    performance_analysis: Dict[str, Any]) -> MigrationPriority:
        """Determine migration priority based on various factors"""
        
        priority_score = 0
        
        # Performance factor
        optimization_servers = {
            opp['server_id'] for opp in 
            performance_analysis.get('optimization_opportunities', [])
        }
        
        app_optimization_servers = [s for s in servers if s.server_id in optimization_servers]
        if len(app_optimization_servers) > len(servers) * 0.5:  # More than 50% underutilized
            priority_score += 3
        
        # Age factor (based on OS version - simplified)
        old_servers = [s for s in servers if '2012' in s.os_version or '2008' in s.os_version]
        if len(old_servers) > 0:
            priority_score += 2
        
        # Size factor (larger applications get higher priority)
        if len(servers) > 5:
            priority_score += 1
        
        # Map score to priority
        if priority_score >= 5:
            return MigrationPriority.IMMEDIATE
        elif priority_score >= 3:
            return MigrationPriority.HIGH
        elif priority_score >= 2:
            return MigrationPriority.MEDIUM
        else:
            return MigrationPriority.LOW

    def _estimate_migration_effort(self, 
                                 app: ApplicationComponent,
                                 servers: List[DiscoveredServer],
                                 strategy: MigrationStrategy,
                                 complexity: MigrationComplexity) -> int:
        """Estimate migration effort in weeks"""
        
        base_weeks = {
            MigrationStrategy.REHOST: 2,
            MigrationStrategy.REPLATFORM: 6,
            MigrationStrategy.REFACTOR: 16,
            MigrationStrategy.RETIRE: 1,
            MigrationStrategy.RETAIN: 0,
            MigrationStrategy.REPURCHASE: 4
        }
        
        complexity_multiplier = {
            MigrationComplexity.LOW: 1.0,
            MigrationComplexity.MEDIUM: 1.5,
            MigrationComplexity.HIGH: 2.0,
            MigrationComplexity.VERY_HIGH: 3.0
        }
        
        base = base_weeks.get(strategy, 4)
        multiplier = complexity_multiplier.get(complexity, 1.5)
        
        # Add server count factor
        server_factor = 1 + (len(servers) - 1) * 0.2
        
        return int(base * multiplier * server_factor)

    def _estimate_migration_cost(self, 
                               app: ApplicationComponent,
                               servers: List[DiscoveredServer],
                               strategy: MigrationStrategy) -> float:
        """Estimate migration cost including AWS resources"""
        
        # Calculate equivalent AWS instance costs
        monthly_compute_cost = 0.0
        
        for server in servers:
            # Map server specs to EC2 instance type
            instance_type = self._map_to_ec2_instance_type(server)
            instance_cost = self._get_ec2_instance_cost(instance_type)
            monthly_compute_cost += instance_cost
        
        # Add strategy-specific costs
        strategy_multiplier = {
            MigrationStrategy.REHOST: 1.0,
            MigrationStrategy.REPLATFORM: 1.2,
            MigrationStrategy.REFACTOR: 2.0,
            MigrationStrategy.RETIRE: 0.0,
            MigrationStrategy.RETAIN: 0.0,
            MigrationStrategy.REPURCHASE: 0.8
        }
        
        multiplier = strategy_multiplier.get(strategy, 1.0)
        
        # Annual cost estimate
        return monthly_compute_cost * 12 * multiplier

    def _map_to_ec2_instance_type(self, server: DiscoveredServer) -> str:
        """Map server specifications to equivalent EC2 instance type"""
        
        # Simple mapping based on CPU and memory
        if server.cpu_cores <= 2 and server.memory_mb <= 4096:
            return 't3.medium'
        elif server.cpu_cores <= 4 and server.memory_mb <= 8192:
            return 't3.large'
        elif server.cpu_cores <= 8 and server.memory_mb <= 16384:
            return 'm5.xlarge'
        elif server.cpu_cores <= 16 and server.memory_mb <= 32768:
            return 'm5.2xlarge'
        else:
            return 'm5.4xlarge'

    def _get_ec2_instance_cost(self, instance_type: str) -> float:
        """Get monthly cost for EC2 instance type"""
        
        # Simplified pricing (actual implementation would use Pricing API)
        pricing = {
            't3.medium': 30.00,
            't3.large': 60.00,
            'm5.xlarge': 140.00,
            'm5.2xlarge': 280.00,
            'm5.4xlarge': 560.00
        }
        
        return pricing.get(instance_type, 100.00)

    def _design_target_architecture(self, 
                                  app: ApplicationComponent,
                                  servers: List[DiscoveredServer],
                                  strategy: MigrationStrategy) -> Dict[str, Any]:
        """Design target AWS architecture for application"""
        
        architecture = {
            'compute': [],
            'storage': [],
            'networking': [],
            'database': [],
            'security': []
        }
        
        # Design compute architecture
        for server in servers:
            server_type = self._classify_server_type(server)
            instance_type = self._map_to_ec2_instance_type(server)
            
            compute_config = {
                'service': 'EC2',
                'instance_type': instance_type,
                'original_server': server.hostname,
                'tier': server_type.value
            }
            
            # Add containerization for refactor strategy
            if strategy == MigrationStrategy.REFACTOR:
                compute_config.update({
                    'service': 'ECS',
                    'container_specs': {
                        'cpu': server.cpu_cores * 1024,
                        'memory': server.memory_mb
                    }
                })
            
            architecture['compute'].append(compute_config)
        
        # Add load balancer for multi-tier applications
        if len(servers) > 1:
            architecture['networking'].append({
                'service': 'ALB',
                'type': 'Application Load Balancer',
                'target_groups': [s.hostname for s in servers]
            })
        
        # Add database services
        db_servers = [s for s in servers if self._classify_server_type(s) == ApplicationTier.DATABASE]
        for db_server in db_servers:
            architecture['database'].append({
                'service': 'RDS',
                'engine': 'mysql',  # Simplified
                'instance_class': self._map_to_rds_instance_class(db_server),
                'multi_az': True,
                'backup_retention': 7
            })
        
        return architecture

    def _map_to_rds_instance_class(self, server: DiscoveredServer) -> str:
        """Map database server to RDS instance class"""
        
        if server.memory_mb <= 8192:
            return 'db.t3.large'
        elif server.memory_mb <= 16384:
            return 'db.m5.xlarge'
        else:
            return 'db.m5.2xlarge'

    def _identify_prerequisites(self, 
                              app: ApplicationComponent, 
                              strategy: MigrationStrategy) -> List[str]:
        """Identify prerequisites for migration"""
        
        prerequisites = [
            'AWS account setup and access configuration',
            'Network connectivity (VPN/Direct Connect)',
            'Security group and IAM policy configuration'
        ]
        
        if strategy == MigrationStrategy.REPLATFORM:
            prerequisites.extend([
                'Application modernization assessment',
                'Database migration testing',
                'Performance testing in AWS environment'
            ])
        elif strategy == MigrationStrategy.REFACTOR:
            prerequisites.extend([
                'Application architecture redesign',
                'Containerization strategy',
                'CI/CD pipeline setup',
                'Microservices decomposition plan'
            ])
        
        return prerequisites

    def _identify_risks(self, 
                       app: ApplicationComponent,
                       strategy: MigrationStrategy,
                       complexity: MigrationComplexity) -> List[str]:
        """Identify migration risks"""
        
        risks = []
        
        if complexity in [MigrationComplexity.HIGH, MigrationComplexity.VERY_HIGH]:
            risks.extend([
                'Extended downtime during migration',
                'Data loss risk during database migration',
                'Performance degradation post-migration'
            ])
        
        if len(app.dependencies) > 3:
            risks.append('Dependency mapping incomplete - hidden dependencies may exist')
        
        if strategy == MigrationStrategy.REFACTOR:
            risks.extend([
                'Application functionality changes required',
                'Extended development and testing timeline',
                'Team training on new architecture patterns'
            ])
        
        return risks

    def _plan_migration_waves(self, recommendations: List[MigrationRecommendation]) -> List[Dict[str, Any]]:
        """Plan migration waves based on dependencies and priorities"""
        
        # Sort by priority and complexity
        sorted_recs = sorted(
            recommendations,
            key=lambda x: (
                x.priority.value,
                x.complexity.value,
                len(x.dependencies)
            )
        )
        
        waves = []
        current_wave = []
        current_wave_effort = 0
        max_wave_effort = self.config.migration_wave_size * 4  # 4 weeks per application average
        
        for rec in sorted_recs:
            if (current_wave_effort + rec.estimated_effort_weeks <= max_wave_effort and
                len(current_wave) < self.config.migration_wave_size):
                current_wave.append(rec)
                current_wave_effort += rec.estimated_effort_weeks
            else:
                if current_wave:
                    waves.append({
                        'wave_number': len(waves) + 1,
                        'applications': [r.application_id for r in current_wave],
                        'total_effort_weeks': current_wave_effort,
                        'estimated_cost': sum(r.estimated_cost for r in current_wave),
                        'start_date': (datetime.utcnow() + timedelta(weeks=len(waves) * 12)).isoformat()
                    })
                
                current_wave = [rec]
                current_wave_effort = rec.estimated_effort_weeks
        
        # Add final wave
        if current_wave:
            waves.append({
                'wave_number': len(waves) + 1,
                'applications': [r.application_id for r in current_wave],
                'total_effort_weeks': current_wave_effort,
                'estimated_cost': sum(r.estimated_cost for r in current_wave),
                'start_date': (datetime.utcnow() + timedelta(weeks=len(waves) * 12)).isoformat()
            })
        
        return waves

    def _calculate_migration_costs(self, 
                                 servers: List[DiscoveredServer],
                                 recommendations: List[MigrationRecommendation]) -> Dict[str, Any]:
        """Calculate comprehensive migration costs"""
        
        total_infrastructure_cost = sum(rec.estimated_cost for rec in recommendations)
        
        # Add professional services costs
        professional_services = total_infrastructure_cost * 0.3  # 30% of infrastructure cost
        
        # Add training costs
        training_cost = len(servers) * 500  # $500 per server for training
        
        # Add contingency
        contingency = (total_infrastructure_cost + professional_services + training_cost) * 0.2
        
        return {
            'total_cost': total_infrastructure_cost + professional_services + training_cost + contingency,
            'infrastructure_cost': total_infrastructure_cost,
            'professional_services': professional_services,
            'training_cost': training_cost,
            'contingency': contingency,
            'cost_breakdown_by_strategy': self._calculate_cost_by_strategy(recommendations)
        }

    def _calculate_cost_by_strategy(self, recommendations: List[MigrationRecommendation]) -> Dict[str, float]:
        """Calculate costs broken down by migration strategy"""
        
        cost_by_strategy = {}
        
        for rec in recommendations:
            strategy = rec.strategy.value
            if strategy not in cost_by_strategy:
                cost_by_strategy[strategy] = 0.0
            cost_by_strategy[strategy] += rec.estimated_cost
        
        return cost_by_strategy

    def _serialize_server(self, server: DiscoveredServer) -> Dict[str, Any]:
        """Serialize server for JSON output"""
        return {
            'server_id': server.server_id,
            'hostname': server.hostname,
            'ip_address': server.ip_address,
            'os_name': server.os_name,
            'os_version': server.os_version,
            'cpu_cores': server.cpu_cores,
            'memory_mb': server.memory_mb,
            'disk_gb': server.disk_gb,
            'server_type': self._classify_server_type(server).value,
            'connection_count': len(server.connections),
            'process_count': len(server.processes)
        }

    def _serialize_application(self, app: ApplicationComponent) -> Dict[str, Any]:
        """Serialize application for JSON output"""
        return {
            'component_id': app.component_id,
            'name': app.name,
            'tier': app.tier.value,
            'server_count': len(app.servers),
            'dependency_count': len(app.dependencies),
            'ports': app.ports,
            'protocols': app.protocols
        }

    def _serialize_dependency_graph(self, graph: nx.DiGraph) -> Dict[str, Any]:
        """Serialize dependency graph for JSON output"""
        return {
            'nodes': list(graph.nodes()),
            'edges': list(graph.edges()),
            'node_count': graph.number_of_nodes(),
            'edge_count': graph.number_of_edges()
        }

    def _serialize_recommendation(self, rec: MigrationRecommendation) -> Dict[str, Any]:
        """Serialize migration recommendation for JSON output"""
        return {
            'application_id': rec.application_id,
            'strategy': rec.strategy.value,
            'complexity': rec.complexity.value,
            'priority': rec.priority.value,
            'estimated_effort_weeks': rec.estimated_effort_weeks,
            'estimated_cost': rec.estimated_cost,
            'target_architecture': rec.target_architecture,
            'prerequisites_count': len(rec.prerequisites),
            'risks_count': len(rec.risks),
            'dependency_count': len(rec.dependencies)
        }

# Example usage and enterprise patterns
def create_enterprise_migration_assessment():
    """Create comprehensive migration assessment for enterprise environments"""
    
    # Configure discovery settings
    config = MigrationConfig(
        discovery_modes=[DiscoveryMode.AGENT_BASED, DiscoveryMode.AGENTLESS],
        collection_duration_days=21,  # 3 weeks for comprehensive data
        enable_dependency_mapping=True,
        enable_performance_analysis=True,
        migration_wave_size=8,
        parallel_migrations=3,
        cost_optimization=True,
        security_assessment=True
    )
    
    # Create Discovery manager
    discovery_manager = EnterpriseDiscoveryManager(config=config)
    
    # Start discovery process
    discovery_session = discovery_manager.start_comprehensive_discovery(
        discovery_mode=DiscoveryMode.AGENT_BASED,
        tags={'Environment': 'Production', 'Owner': 'IT-Team'}
    )
    
    print(f"Started discovery session: {discovery_session['session_id']}")
    print(f"Discovery mode: {discovery_session['discovery_mode']}")
    print(f"Analysis scheduled for: {discovery_session['analysis_scheduled']}")
    
    # Simulate analysis after discovery period
    # In real implementation, this would run after collection period
    analysis_report = discovery_manager.analyze_discovered_infrastructure(
        session_id=discovery_session['session_id'],
        include_performance=True
    )
    
    print(f"\nAnalysis completed: {analysis_report['analysis_id']}")
    print(f"Servers discovered: {analysis_report['summary']['total_servers']}")
    print(f"Applications identified: {analysis_report['summary']['applications_identified']}")
    print(f"Migration waves planned: {len(analysis_report['migration_waves'])}")
    print(f"Estimated total cost: ${analysis_report['summary']['estimated_total_cost']:,.2f}")
    
    return analysis_report

if __name__ == "__main__":
    # Create enterprise migration assessment
    migration_report = create_enterprise_migration_assessment()
```

## DevOps Integration Patterns

### CI/CD Pipeline Integration

```yaml
# .github/workflows/migration-assessment.yml
name: AWS Migration Assessment

on:
  schedule:
    - cron: '0 2 * * SUN'  # Weekly on Sunday at 2 AM
  workflow_dispatch:
    inputs:
      discovery_duration:
        description: 'Discovery duration in days'
        required: false
        default: '14'

jobs:
  migration-assessment:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Configure AWS credentials
      uses: aws-actions/configure-aws-credentials@v2
      with:
        role-to-assume: ${{ secrets.AWS_DISCOVERY_ROLE }}
        aws-region: us-east-1
    
    - name: Run Migration Assessment
      run: |
        python scripts/migration_assessment.py \
          --discovery-mode agent_based \
          --collection-duration ${{ github.event.inputs.discovery_duration || '14' }} \
          --enable-performance-analysis \
          --output-format json
    
    - name: Generate Migration Report
      run: |
        python scripts/generate_migration_report.py \
          --analysis-file migration-analysis-*.json \
          --output-format pdf \
          --include-cost-breakdown
    
    - name: Upload Assessment Results
      uses: actions/upload-artifact@v3
      with:
        name: migration-assessment
        path: |
          migration-analysis-*.json
          migration-report-*.pdf
```

### Terraform Integration

```hcl
# migration_infrastructure.tf
resource "aws_iam_role" "discovery_service_role" {
  name = "AWSApplicationDiscoveryServiceRole"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "discovery.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_policy" "discovery_policy" {
  name = "ApplicationDiscoveryServicePolicy"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "discovery:*",
          "ec2:DescribeInstances",
          "ec2:DescribeImages",
          "ec2:DescribeSnapshots",
          "ec2:DescribeVolumes",
          "application-autoscaling:*",
          "pricing:GetProducts"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_lambda_function" "migration_analyzer" {
  filename         = "migration_analyzer.zip"
  function_name    = "aws-migration-analyzer"
  role            = aws_iam_role.discovery_service_role.arn
  handler         = "lambda_function.lambda_handler"
  runtime         = "python3.9"
  timeout         = 900
  memory_size     = 1024

  environment {
    variables = {
      DISCOVERY_DURATION_DAYS = "14"
      ENABLE_COST_OPTIMIZATION = "true"
      S3_BUCKET = aws_s3_bucket.migration_reports.bucket
    }
  }
}

resource "aws_s3_bucket" "migration_reports" {
  bucket = "enterprise-migration-reports-${random_id.bucket_suffix.hex}"
}

resource "aws_s3_bucket_versioning" "migration_reports_versioning" {
  bucket = aws_s3_bucket.migration_reports.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "random_id" "bucket_suffix" {
  byte_length = 4
}
```

## Enterprise Use Cases

### Large Enterprise Migration
- **Multi-Datacenter Discovery**: Comprehensive discovery across multiple on-premises datacenters
- **Application Portfolio Rationalization**: Automated application grouping and modernization recommendations
- **Cost Optimization**: ROI analysis and TCO calculations for cloud migration
- **Risk Assessment**: Automated risk analysis and mitigation strategies

### Financial Services Migration
- **Regulatory Compliance**: Compliance-aware migration planning with security assessments
- **Zero-Downtime Requirements**: Migration strategies focused on business continuity
- **Data Sovereignty**: Geographic and regulatory constraints in migration planning
- **Audit Trail**: Complete audit trail for regulatory compliance

### Healthcare Migration
- **HIPAA Compliance**: Security-first migration planning with data protection validation
- **Critical System Identification**: Priority-based migration for patient-critical systems
- **Disaster Recovery**: Enhanced DR planning in target cloud architecture
- **Performance Requirements**: SLA-aware migration planning for healthcare applications

## Key Features

- **Intelligent Discovery**: Multi-mode discovery with agent-based, agentless, and connector options
- **Dependency Mapping**: Automated application dependency discovery and visualization
- **Migration Planning**: AI-driven migration strategy recommendations and wave planning
- **Cost Optimization**: Comprehensive cost analysis with AWS pricing integration
- **Performance Analysis**: Resource utilization analysis and rightsizing recommendations
- **Enterprise Scale**: Multi-account and multi-datacenter discovery capabilities
- **DevOps Integration**: Native CI/CD integration with automated reporting
- **Compliance Ready**: Security and compliance assessment with audit trails