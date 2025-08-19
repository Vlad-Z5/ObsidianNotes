# AWS VPC Peering - Enterprise Connectivity Automation Framework

AWS VPC Peering connects VPCs for private communication with automated deployment, intelligent routing management, and enterprise-scale connectivity orchestration across accounts and regions.

## Enterprise VPC Peering Automation Framework

```python
import json
import boto3
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple, Set
from concurrent.futures import ThreadPoolExecutor, as_completed
import ipaddress
import time
from botocore.exceptions import ClientError

class PeeringConnectionState(Enum):
    INITIATING_REQUEST = "initiating-request"
    PENDING_ACCEPTANCE = "pending-acceptance"
    ACTIVE = "active"
    DELETED = "deleted"
    REJECTED = "rejected"
    FAILED = "failed"
    EXPIRED = "expired"
    PROVISIONING = "provisioning"
    DELETING = "deleting"

class PeeringType(Enum):
    INTRA_REGION = "intra-region"
    INTER_REGION = "inter-region"
    CROSS_ACCOUNT = "cross-account"
    CROSS_ACCOUNT_INTER_REGION = "cross-account-inter-region"

class NetworkTier(Enum):
    PRODUCTION = "production"
    STAGING = "staging"
    DEVELOPMENT = "development"
    SHARED_SERVICES = "shared-services"

class RouteScope(Enum):
    FULL_VPC = "full-vpc"
    SPECIFIC_SUBNETS = "specific-subnets"
    CONDITIONAL = "conditional"

@dataclass
class VPCEndpoint:
    vpc_id: str
    account_id: str
    region: str
    cidr_blocks: List[str] = field(default_factory=list)
    owner_id: Optional[str] = None
    name: Optional[str] = None
    environment: Optional[str] = None

@dataclass
class PeeringConnectionConfig:
    requester_vpc: VPCEndpoint
    accepter_vpc: VPCEndpoint
    peering_type: PeeringType
    auto_accept: bool = False
    allow_dns_resolution: bool = True
    allow_classic_link_dns: bool = False
    allow_vpc_to_remote_classic_link: bool = False
    tags: Dict[str, str] = field(default_factory=dict)
    route_scope: RouteScope = RouteScope.FULL_VPC
    specific_routes: List[str] = field(default_factory=list)

@dataclass
class ManagedPeeringConnection:
    id: str
    requester_vpc_info: VPCEndpoint
    accepter_vpc_info: VPCEndpoint
    state: PeeringConnectionState
    peering_type: PeeringType
    status_code: Optional[str] = None
    status_message: Optional[str] = None
    creation_time: Optional[datetime] = None
    expiration_time: Optional[datetime] = None
    tags: Dict[str, str] = field(default_factory=dict)

@dataclass
class RouteTableEntry:
    route_table_id: str
    destination_cidr: str
    vpc_peering_connection_id: str
    state: str
    origin: str

@dataclass
class ConnectivityMatrix:
    vpc_endpoints: List[VPCEndpoint]
    peering_connections: List[ManagedPeeringConnection]
    routing_table: Dict[str, List[RouteTableEntry]]
    reachability_matrix: Dict[Tuple[str, str], bool]

class EnterpriseVPCPeeringManager:
    """
    Enterprise AWS VPC Peering manager with automated connectivity,
    intelligent routing, and cross-account orchestration.
    """
    
    def __init__(self, 
                 region: str = 'us-east-1',
                 cross_account_role: str = None):
        self.ec2 = boto3.client('ec2', region_name=region)
        self.organizations = boto3.client('organizations', region_name=region)
        self.sts = boto3.client('sts', region_name=region)
        self.cloudwatch = boto3.client('cloudwatch', region_name=region)
        self.region = region
        self.cross_account_role = cross_account_role
        self.logger = self._setup_logging()
        
    def _setup_logging(self) -> logging.Logger:
        logger = logging.getLogger('VPCPeering')
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger

    def create_enterprise_peering_mesh(self, 
                                     vpc_endpoints: List[VPCEndpoint],
                                     network_tier: NetworkTier = NetworkTier.PRODUCTION,
                                     enable_transitive_routing: bool = False) -> Dict[str, Any]:
        """Create comprehensive VPC peering mesh with intelligent routing"""
        try:
            mesh_start = datetime.utcnow()
            
            # Validate VPC endpoints and check for CIDR conflicts
            validation_results = self._validate_vpc_endpoints(vpc_endpoints)
            if not validation_results['valid']:
                raise ValueError(f"VPC endpoint validation failed: {validation_results['errors']}")
            
            # Generate optimal peering topology
            peering_topology = self._generate_optimal_topology(
                vpc_endpoints, network_tier, enable_transitive_routing
            )
            
            # Create peering connections
            peering_connections = self._create_peering_connections(peering_topology)
            
            # Configure routing tables
            routing_configuration = self._configure_mesh_routing(
                vpc_endpoints, peering_connections, enable_transitive_routing
            )
            
            # Setup monitoring and health checks
            monitoring_setup = self._setup_peering_monitoring(peering_connections)
            
            # Generate connectivity matrix
            connectivity_matrix = self._generate_connectivity_matrix(
                vpc_endpoints, peering_connections
            )
            
            mesh_time = (datetime.utcnow() - mesh_start).total_seconds()
            
            result = {
                'mesh_id': f"vpc-mesh-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}",
                'network_tier': network_tier.value,
                'vpc_endpoints': len(vpc_endpoints),
                'peering_connections': [self._serialize_peering_connection(pc) for pc in peering_connections],
                'routing_configuration': routing_configuration,
                'connectivity_matrix': self._serialize_connectivity_matrix(connectivity_matrix),
                'monitoring_setup': monitoring_setup,
                'transitive_routing_enabled': enable_transitive_routing,
                'creation_time_seconds': mesh_time,
                'estimated_monthly_cost': self._calculate_mesh_cost(peering_connections),
                'created_at': mesh_start.isoformat()
            }
            
            self.logger.info(f"Created enterprise peering mesh: {result['mesh_id']}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error creating enterprise peering mesh: {str(e)}")
            raise

    def _validate_vpc_endpoints(self, vpc_endpoints: List[VPCEndpoint]) -> Dict[str, Any]:
        """Validate VPC endpoints for peering compatibility"""
        validation_errors = []
        warnings = []
        
        # Check for CIDR overlaps
        cidr_conflicts = self._check_cidr_conflicts(vpc_endpoints)
        if cidr_conflicts:
            validation_errors.extend([f"CIDR conflict: {conflict}" for conflict in cidr_conflicts])
        
        # Validate VPC existence and accessibility
        for endpoint in vpc_endpoints:
            try:
                # Check if VPC exists and is accessible
                vpc_info = self._get_vpc_info(endpoint)
                if not vpc_info:
                    validation_errors.append(f"VPC {endpoint.vpc_id} not found or not accessible")
                
                # Update endpoint with actual CIDR blocks if not provided
                if not endpoint.cidr_blocks and vpc_info:
                    endpoint.cidr_blocks = [vpc_info['CidrBlock']]
                    for cidr_assoc in vpc_info.get('CidrBlockAssociationSet', []):
                        if cidr_assoc['CidrBlockState']['State'] == 'associated':
                            endpoint.cidr_blocks.append(cidr_assoc['CidrBlock'])
                
            except Exception as e:
                validation_errors.append(f"Error validating VPC {endpoint.vpc_id}: {str(e)}")
        
        # Check for reasonable number of peering connections
        potential_connections = len(vpc_endpoints) * (len(vpc_endpoints) - 1) // 2
        if potential_connections > 50:  # AWS default limit is 50 per VPC
            warnings.append(f"Potential connections ({potential_connections}) may exceed VPC peering limits")
        
        return {
            'valid': len(validation_errors) == 0,
            'errors': validation_errors,
            'warnings': warnings,
            'potential_connections': potential_connections
        }

    def _check_cidr_conflicts(self, vpc_endpoints: List[VPCEndpoint]) -> List[str]:
        """Check for CIDR block conflicts between VPCs"""
        conflicts = []
        
        for i, endpoint1 in enumerate(vpc_endpoints):
            for j, endpoint2 in enumerate(vpc_endpoints[i+1:], i+1):
                for cidr1 in endpoint1.cidr_blocks:
                    for cidr2 in endpoint2.cidr_blocks:
                        try:
                            network1 = ipaddress.ip_network(cidr1, strict=False)
                            network2 = ipaddress.ip_network(cidr2, strict=False)
                            
                            if network1.overlaps(network2):
                                conflicts.append(
                                    f"VPC {endpoint1.vpc_id} ({cidr1}) overlaps with "
                                    f"VPC {endpoint2.vpc_id} ({cidr2})"
                                )
                        except ValueError as e:
                            conflicts.append(f"Invalid CIDR format: {str(e)}")
        
        return conflicts

    def _generate_optimal_topology(self, 
                                 vpc_endpoints: List[VPCEndpoint],
                                 network_tier: NetworkTier,
                                 enable_transitive: bool) -> Dict[str, Any]:
        """Generate optimal peering topology based on requirements"""
        
        topology = {
            'connections': [],
            'hub_and_spoke': False,
            'full_mesh': False,
            'hybrid': False
        }
        
        num_vpcs = len(vpc_endpoints)
        
        if network_tier == NetworkTier.SHARED_SERVICES:
            # Hub and spoke topology with shared services VPC as hub
            hub_vpc = next((vpc for vpc in vpc_endpoints if vpc.environment == 'shared-services'), vpc_endpoints[0])
            topology['hub_and_spoke'] = True
            
            for vpc in vpc_endpoints:
                if vpc.vpc_id != hub_vpc.vpc_id:
                    topology['connections'].append({
                        'requester': hub_vpc,
                        'accepter': vpc,
                        'priority': 'high'
                    })
        
        elif num_vpcs <= 5 or network_tier == NetworkTier.PRODUCTION:
            # Full mesh for small numbers or production environments
            topology['full_mesh'] = True
            
            for i, vpc1 in enumerate(vpc_endpoints):
                for vpc2 in vpc_endpoints[i+1:]:
                    topology['connections'].append({
                        'requester': vpc1,
                        'accepter': vpc2,
                        'priority': 'high' if network_tier == NetworkTier.PRODUCTION else 'medium'
                    })
        
        else:
            # Hybrid topology for larger environments
            topology['hybrid'] = True
            
            # Group VPCs by environment/account
            env_groups = {}
            for vpc in vpc_endpoints:
                env_key = f"{vpc.environment or 'default'}_{vpc.account_id}"
                if env_key not in env_groups:
                    env_groups[env_key] = []
                env_groups[env_key].append(vpc)
            
            # Create full mesh within each environment group
            for group_vpcs in env_groups.values():
                for i, vpc1 in enumerate(group_vpcs):
                    for vpc2 in group_vpcs[i+1:]:
                        topology['connections'].append({
                            'requester': vpc1,
                            'accepter': vpc2,
                            'priority': 'high'
                        })
            
            # Create selective inter-group connections
            group_representatives = [vpcs[0] for vpcs in env_groups.values()]
            for i, vpc1 in enumerate(group_representatives):
                for vpc2 in group_representatives[i+1:]:
                    topology['connections'].append({
                        'requester': vpc1,
                        'accepter': vpc2,
                        'priority': 'medium'
                    })
        
        return topology

    def _create_peering_connections(self, topology: Dict[str, Any]) -> List[ManagedPeeringConnection]:
        """Create VPC peering connections based on topology"""
        peering_connections = []
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {}
            
            for connection_spec in topology['connections']:
                requester = connection_spec['requester']
                accepter = connection_spec['accepter']
                
                # Determine peering type
                peering_type = self._determine_peering_type(requester, accepter)
                
                config = PeeringConnectionConfig(
                    requester_vpc=requester,
                    accepter_vpc=accepter,
                    peering_type=peering_type,
                    auto_accept=(requester.account_id == accepter.account_id),
                    tags={
                        'Name': f"Peering-{requester.name or requester.vpc_id}-{accepter.name or accepter.vpc_id}",
                        'RequesterVPC': requester.vpc_id,
                        'AccepterVPC': accepter.vpc_id,
                        'PeeringType': peering_type.value,
                        'Priority': connection_spec['priority'],
                        'ManagedBy': 'EnterpriseVPCPeeringManager'
                    }
                )
                
                future = executor.submit(self._create_single_peering_connection, config)
                futures[future] = config
            
            for future in as_completed(futures):
                try:
                    peering_connection = future.result()
                    peering_connections.append(peering_connection)
                    
                    config = futures[future]
                    self.logger.info(
                        f"Created peering connection: {peering_connection.id} "
                        f"({config.requester_vpc.vpc_id} <-> {config.accepter_vpc.vpc_id})"
                    )
                    
                except Exception as e:
                    config = futures[future]
                    self.logger.error(
                        f"Failed to create peering connection "
                        f"({config.requester_vpc.vpc_id} <-> {config.accepter_vpc.vpc_id}): {str(e)}"
                    )
        
        return peering_connections

    def _create_single_peering_connection(self, config: PeeringConnectionConfig) -> ManagedPeeringConnection:
        """Create individual VPC peering connection"""
        try:
            # Determine which EC2 client to use based on peering type
            ec2_client = self._get_ec2_client_for_peering(config)
            
            create_params = {
                'VpcId': config.requester_vpc.vpc_id,
                'TagSpecifications': [{
                    'ResourceType': 'vpc-peering-connection',
                    'Tags': [{'Key': k, 'Value': v} for k, v in config.tags.items()]
                }]
            }
            
            # Add peer VPC parameters based on peering type
            if config.peering_type in [PeeringType.CROSS_ACCOUNT, PeeringType.CROSS_ACCOUNT_INTER_REGION]:
                create_params['PeerOwnerId'] = config.accepter_vpc.account_id
            
            if config.peering_type in [PeeringType.INTER_REGION, PeeringType.CROSS_ACCOUNT_INTER_REGION]:
                create_params['PeerRegion'] = config.accepter_vpc.region
            
            create_params['PeerVpcId'] = config.accepter_vpc.vpc_id
            
            # Create the peering connection
            response = ec2_client.create_vpc_peering_connection(**create_params)
            peering_data = response['VpcPeeringConnection']
            
            # Wait for the connection to be in pending-acceptance state
            peering_id = peering_data['VpcPeeringConnectionId']
            self._wait_for_peering_state(peering_id, PeeringConnectionState.PENDING_ACCEPTANCE, ec2_client)
            
            # Accept the connection if auto-accept is enabled and it's same account
            if config.auto_accept and config.requester_vpc.account_id == config.accepter_vpc.account_id:
                self._accept_peering_connection(peering_id, config, ec2_client)
                self._wait_for_peering_state(peering_id, PeeringConnectionState.ACTIVE, ec2_client)
            
            # Configure DNS resolution options
            if config.allow_dns_resolution:
                self._configure_dns_resolution(peering_id, config, ec2_client)
            
            # Get updated peering connection details
            describe_response = ec2_client.describe_vpc_peering_connections(
                VpcPeeringConnectionIds=[peering_id]
            )
            updated_data = describe_response['VpcPeeringConnections'][0]
            
            return ManagedPeeringConnection(
                id=peering_id,
                requester_vpc_info=config.requester_vpc,
                accepter_vpc_info=config.accepter_vpc,
                state=PeeringConnectionState(updated_data['Status']['Code']),
                peering_type=config.peering_type,
                status_code=updated_data['Status']['Code'],
                status_message=updated_data['Status'].get('Message', ''),
                creation_time=updated_data.get('CreationTime'),
                expiration_time=updated_data.get('ExpirationTime'),
                tags=config.tags
            )
            
        except Exception as e:
            self.logger.error(f"Error creating peering connection: {str(e)}")
            raise

    def setup_intelligent_routing_automation(self, 
                                           peering_connections: List[ManagedPeeringConnection],
                                           enable_conditional_routing: bool = False) -> Dict[str, Any]:
        """Setup intelligent routing automation for peering connections"""
        try:
            routing_setup = {}
            
            # Create routing Lambda function
            routing_function = self._create_routing_automation_lambda()
            routing_setup['routing_function'] = routing_function
            
            # Setup route table monitoring
            route_monitoring = self._setup_route_table_monitoring(peering_connections)
            routing_setup['route_monitoring'] = route_monitoring
            
            # Create automatic route propagation
            if enable_conditional_routing:
                conditional_routing = self._setup_conditional_routing(peering_connections)
                routing_setup['conditional_routing'] = conditional_routing
            
            # Setup failover routing
            failover_routing = self._setup_failover_routing(peering_connections)
            routing_setup['failover_routing'] = failover_routing
            
            # Create routing optimization dashboard
            dashboard = self._create_routing_dashboard(peering_connections)
            routing_setup['dashboard'] = dashboard
            
            return {
                'routing_id': f"routing-auto-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}",
                'peering_connections_managed': len(peering_connections),
                'routing_setup': routing_setup,
                'conditional_routing_enabled': enable_conditional_routing,
                'setup_timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error setting up routing automation: {str(e)}")
            raise

    def analyze_peering_performance(self, 
                                  peering_connection_ids: List[str] = None,
                                  time_period_hours: int = 24) -> Dict[str, Any]:
        """Analyze performance and utilization of VPC peering connections"""
        try:
            if not peering_connection_ids:
                peering_connection_ids = self._get_all_peering_connection_ids()
            
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=time_period_hours)
            
            performance_data = {}
            total_data_transfer = 0
            total_connections = len(peering_connection_ids)
            
            for peering_id in peering_connection_ids:
                # Get detailed performance metrics
                metrics = self._get_peering_connection_metrics(peering_id, start_time, end_time)
                
                # Analyze traffic patterns
                traffic_analysis = self._analyze_traffic_patterns(metrics)
                
                # Check for potential issues
                health_check = self._perform_peering_health_check(peering_id)
                
                # Calculate efficiency scores
                efficiency_score = self._calculate_peering_efficiency(metrics)
                
                performance_data[peering_id] = {
                    'metrics': metrics,
                    'traffic_analysis': traffic_analysis,
                    'health_check': health_check,
                    'efficiency_score': efficiency_score,
                    'optimization_recommendations': self._generate_peering_recommendations(
                        metrics, traffic_analysis, health_check
                    )
                }
                
                total_data_transfer += metrics.get('total_bytes', 0)
            
            # Generate summary insights
            summary = {
                'total_peering_connections': total_connections,
                'time_period_hours': time_period_hours,
                'total_data_transfer_gb': total_data_transfer / (1024**3),
                'average_efficiency_score': sum(
                    data['efficiency_score'] for data in performance_data.values()
                ) / total_connections if total_connections > 0 else 0,
                'healthy_connections': len([
                    data for data in performance_data.values() 
                    if data['health_check']['status'] == 'healthy'
                ])
            }
            
            return {
                'analysis_id': f"peering-analysis-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}",
                'generated_at': datetime.utcnow().isoformat(),
                'summary': summary,
                'peering_performance': performance_data,
                'network_topology_insights': self._analyze_network_topology(performance_data),
                'cost_optimization_opportunities': self._identify_cost_optimizations(performance_data)
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing peering performance: {str(e)}")
            raise

    def automated_cross_account_setup(self, 
                                    account_pairs: List[Tuple[str, str]],
                                    peering_configs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Setup automated cross-account VPC peering"""
        try:
            setup_results = {}
            
            for (requester_account, accepter_account), config in zip(account_pairs, peering_configs):
                try:
                    # Setup cross-account roles and permissions
                    role_setup = self._setup_cross_account_peering_roles(
                        requester_account, accepter_account
                    )
                    
                    # Create the peering connection
                    peering_connection = self._create_cross_account_peering(
                        requester_account, accepter_account, config
                    )
                    
                    # Setup automated acceptance workflow
                    acceptance_workflow = self._setup_acceptance_workflow(
                        peering_connection, accepter_account
                    )
                    
                    # Configure cross-account routing
                    routing_config = self._configure_cross_account_routing(
                        peering_connection, config
                    )
                    
                    setup_results[f"{requester_account}-{accepter_account}"] = {
                        'role_setup': role_setup,
                        'peering_connection': self._serialize_peering_connection(peering_connection),
                        'acceptance_workflow': acceptance_workflow,
                        'routing_configuration': routing_config,
                        'status': 'success'
                    }
                    
                except Exception as e:
                    self.logger.error(
                        f"Error setting up cross-account peering "
                        f"({requester_account} -> {accepter_account}): {str(e)}"
                    )
                    setup_results[f"{requester_account}-{accepter_account}"] = {
                        'error': str(e),
                        'status': 'failed'
                    }
            
            return {
                'setup_id': f"cross-account-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}",
                'account_pairs_processed': len(account_pairs),
                'successful_setups': len([r for r in setup_results.values() if r['status'] == 'success']),
                'setup_results': setup_results,
                'setup_timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error in cross-account setup: {str(e)}")
            raise

    def _determine_peering_type(self, requester: VPCEndpoint, accepter: VPCEndpoint) -> PeeringType:
        """Determine the type of peering connection needed"""
        
        same_account = requester.account_id == accepter.account_id
        same_region = requester.region == accepter.region
        
        if same_account and same_region:
            return PeeringType.INTRA_REGION
        elif same_account and not same_region:
            return PeeringType.INTER_REGION
        elif not same_account and same_region:
            return PeeringType.CROSS_ACCOUNT
        else:
            return PeeringType.CROSS_ACCOUNT_INTER_REGION

    def _get_ec2_client_for_peering(self, config: PeeringConnectionConfig):
        """Get appropriate EC2 client for peering operation"""
        
        if config.peering_type in [PeeringType.CROSS_ACCOUNT, PeeringType.CROSS_ACCOUNT_INTER_REGION]:
            # Use STS to assume role in requester account if needed
            if self.cross_account_role:
                return self._assume_role_and_get_client(
                    config.requester_vpc.account_id, 
                    config.requester_vpc.region
                )
        
        return self.ec2

    def _wait_for_peering_state(self, 
                              peering_id: str, 
                              target_state: PeeringConnectionState,
                              ec2_client,
                              max_wait_time: int = 300) -> None:
        """Wait for peering connection to reach target state"""
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            try:
                response = ec2_client.describe_vpc_peering_connections(
                    VpcPeeringConnectionIds=[peering_id]
                )
                
                if response['VpcPeeringConnections']:
                    current_state = PeeringConnectionState(
                        response['VpcPeeringConnections'][0]['Status']['Code']
                    )
                    
                    if current_state == target_state:
                        return
                    elif current_state in [PeeringConnectionState.FAILED, PeeringConnectionState.REJECTED]:
                        status_message = response['VpcPeeringConnections'][0]['Status'].get('Message', '')
                        raise Exception(f"Peering connection {peering_id} failed: {status_message}")
                
                time.sleep(10)
                
            except Exception as e:
                if 'InvalidVpcPeeringConnectionID.NotFound' in str(e):
                    time.sleep(5)
                    continue
                else:
                    raise
        
        raise Exception(f"Peering connection {peering_id} did not reach {target_state.value} within {max_wait_time} seconds")

    def _serialize_peering_connection(self, peering: ManagedPeeringConnection) -> Dict[str, Any]:
        """Serialize peering connection for JSON output"""
        return {
            'id': peering.id,
            'requester_vpc': {
                'vpc_id': peering.requester_vpc_info.vpc_id,
                'account_id': peering.requester_vpc_info.account_id,
                'region': peering.requester_vpc_info.region,
                'cidr_blocks': peering.requester_vpc_info.cidr_blocks
            },
            'accepter_vpc': {
                'vpc_id': peering.accepter_vpc_info.vpc_id,
                'account_id': peering.accepter_vpc_info.account_id,
                'region': peering.accepter_vpc_info.region,
                'cidr_blocks': peering.accepter_vpc_info.cidr_blocks
            },
            'state': peering.state.value,
            'peering_type': peering.peering_type.value,
            'status_code': peering.status_code,
            'status_message': peering.status_message,
            'creation_time': peering.creation_time.isoformat() if peering.creation_time else None,
            'tags': peering.tags
        }

    def _serialize_connectivity_matrix(self, matrix: ConnectivityMatrix) -> Dict[str, Any]:
        """Serialize connectivity matrix for JSON output"""
        return {
            'vpc_count': len(matrix.vpc_endpoints),
            'peering_connections': len(matrix.peering_connections),
            'total_possible_connections': len(matrix.vpc_endpoints) * (len(matrix.vpc_endpoints) - 1) // 2,
            'reachability_percentage': (
                sum(matrix.reachability_matrix.values()) / len(matrix.reachability_matrix) * 100
                if matrix.reachability_matrix else 0
            )
        }

# VPC Peering Orchestrator for Enterprise Environments
class VPCPeeringOrchestrator:
    """
    Orchestrates VPC peering across multiple accounts, regions,
    and organizational units with centralized management.
    """
    
    def __init__(self, regions: List[str], organization_id: str = None):
        self.regions = regions
        self.organization_id = organization_id
        self.managers = {}
        self.logger = logging.getLogger('VPCPeeringOrchestrator')
        
        # Initialize managers for each region
        for region in regions:
            self.managers[region] = EnterpriseVPCPeeringManager(region=region)

    def deploy_organization_wide_connectivity(self, 
                                            connectivity_config: Dict[str, Any]) -> Dict[str, Any]:
        """Deploy VPC peering connectivity across entire organization"""
        
        deployment_results = {}
        total_connections = 0
        
        try:
            # Get all VPC endpoints across the organization
            vpc_inventory = self._discover_organization_vpcs()
            
            # Generate connectivity requirements based on config
            connectivity_requirements = self._generate_connectivity_requirements(
                vpc_inventory, connectivity_config
            )
            
            # Deploy peering connections in parallel across regions
            with ThreadPoolExecutor(max_workers=len(self.regions)) as executor:
                futures = {}
                
                for region, requirements in connectivity_requirements.items():
                    if requirements['peering_connections']:
                        manager = self.managers[region]
                        
                        future = executor.submit(
                            manager.create_enterprise_peering_mesh,
                            requirements['vpc_endpoints'],
                            NetworkTier(requirements.get('network_tier', 'production')),
                            requirements.get('enable_transitive_routing', False)
                        )
                        futures[future] = region
                
                for future in as_completed(futures):
                    region = futures[future]
                    try:
                        result = future.result()
                        deployment_results[region] = result
                        total_connections += len(result['peering_connections'])
                        
                        self.logger.info(f"Successfully deployed peering mesh in {region}")
                        
                    except Exception as e:
                        self.logger.error(f"Failed to deploy peering mesh in {region}: {str(e)}")
                        deployment_results[region] = {'error': str(e)}
            
            # Setup inter-region connectivity if required
            inter_region_setup = None
            if connectivity_config.get('enable_inter_region', False):
                inter_region_setup = self._setup_inter_region_connectivity(
                    deployment_results, connectivity_config
                )
            
            return {
                'deployment_id': f"org-connectivity-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}",
                'organization_id': self.organization_id,
                'regions_deployed': len([r for r in deployment_results.values() if 'error' not in r]),
                'total_regions': len(self.regions),
                'total_peering_connections': total_connections,
                'regional_deployments': deployment_results,
                'inter_region_setup': inter_region_setup,
                'deployed_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error in organization-wide connectivity deployment: {str(e)}")
            raise

# Example usage and enterprise patterns
def create_enterprise_vpc_mesh():
    """Create comprehensive enterprise VPC peering mesh"""
    
    # Define VPC endpoints
    vpc_endpoints = [
        VPCEndpoint(
            vpc_id='vpc-prod-web-12345',
            account_id='123456789012',
            region='us-east-1',
            name='production-web',
            environment='production'
        ),
        VPCEndpoint(
            vpc_id='vpc-prod-db-67890',
            account_id='123456789012',
            region='us-east-1',
            name='production-database',
            environment='production'
        ),
        VPCEndpoint(
            vpc_id='vpc-shared-svc-11111',
            account_id='123456789012',
            region='us-east-1',
            name='shared-services',
            environment='shared-services'
        ),
        VPCEndpoint(
            vpc_id='vpc-dev-22222',
            account_id='123456789013',
            region='us-east-1',
            name='development',
            environment='development'
        )
    ]
    
    # Create VPC peering manager
    peering_manager = EnterpriseVPCPeeringManager(region='us-east-1')
    
    # Create enterprise peering mesh
    mesh_result = peering_manager.create_enterprise_peering_mesh(
        vpc_endpoints=vpc_endpoints,
        network_tier=NetworkTier.PRODUCTION,
        enable_transitive_routing=False
    )
    
    print(f"Created VPC peering mesh: {mesh_result['mesh_id']}")
    print(f"Peering connections: {len(mesh_result['peering_connections'])}")
    print(f"Estimated monthly cost: ${mesh_result['estimated_monthly_cost']:.2f}")
    
    # Setup intelligent routing automation
    peering_connections = []  # Would be populated from mesh_result
    routing_automation = peering_manager.setup_intelligent_routing_automation(
        peering_connections,
        enable_conditional_routing=True
    )
    
    print(f"Routing automation setup: {routing_automation['routing_id']}")
    
    return mesh_result, routing_automation

def setup_cross_account_peering():
    """Setup automated cross-account VPC peering"""
    
    peering_manager = EnterpriseVPCPeeringManager()
    
    # Define cross-account peering requirements
    account_pairs = [
        ('123456789012', '123456789013'),  # Production -> Development
        ('123456789012', '123456789014'),  # Production -> Staging
        ('123456789013', '123456789014')   # Development -> Staging
    ]
    
    peering_configs = [
        {
            'requester_vpc_id': 'vpc-prod-12345',
            'accepter_vpc_id': 'vpc-dev-67890',
            'auto_accept': False,
            'allow_dns_resolution': True
        },
        {
            'requester_vpc_id': 'vpc-prod-12345',
            'accepter_vpc_id': 'vpc-staging-11111',
            'auto_accept': False,
            'allow_dns_resolution': True
        },
        {
            'requester_vpc_id': 'vpc-dev-67890',
            'accepter_vpc_id': 'vpc-staging-11111',
            'auto_accept': True,
            'allow_dns_resolution': False
        }
    ]
    
    # Setup cross-account peering
    cross_account_result = peering_manager.automated_cross_account_setup(
        account_pairs, peering_configs
    )
    
    print(f"Cross-account setup: {cross_account_result['setup_id']}")
    print(f"Successful setups: {cross_account_result['successful_setups']}/{cross_account_result['account_pairs_processed']}")
    
    return cross_account_result

if __name__ == "__main__":
    # Create enterprise VPC mesh
    mesh_result, routing_automation = create_enterprise_vpc_mesh()
    
    # Setup cross-account peering
    cross_account_result = setup_cross_account_peering()
```

## DevOps Integration Patterns

### CI/CD Pipeline Integration

```yaml
# .github/workflows/vpc-peering-automation.yml
name: VPC Peering Automation

on:
  schedule:
    - cron: '0 6 * * MON'  # Weekly on Monday at 6 AM
  workflow_dispatch:
    inputs:
      action:
        description: 'Peering action'
        required: false
        default: 'analyze'
        type: choice
        options:
        - analyze
        - create
        - optimize
        - cleanup

jobs:
  vpc-peering-management:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Configure AWS credentials
      uses: aws-actions/configure-aws-credentials@v2
      with:
        role-to-assume: ${{ secrets.AWS_VPC_PEERING_ROLE }}
        aws-region: us-east-1
    
    - name: Run VPC Peering Analysis
      run: |
        python scripts/vpc_peering_management.py \
          --action ${{ github.event.inputs.action || 'analyze' }} \
          --include-cross-account \
          --include-inter-region \
          --output-format json
    
    - name: Generate Connectivity Report
      run: |
        python scripts/generate_connectivity_report.py \
          --include-topology-diagram \
          --include-cost-analysis \
          --output-format html
    
    - name: Upload Reports
      uses: actions/upload-artifact@v3
      with:
        name: vpc-peering-reports
        path: |
          peering-analysis-*.json
          connectivity-report-*.html
          topology-diagram-*.png
```

### Terraform Integration

```hcl
# vpc_peering_mesh.tf
locals {
  vpc_peering_pairs = [
    for pair in setproduct(var.vpc_configs, var.vpc_configs) : {
      requester = pair[0]
      accepter  = pair[1]
    }
    if pair[0].vpc_id != pair[1].vpc_id && pair[0].priority >= pair[1].priority
  ]
}

resource "aws_vpc_peering_connection" "enterprise_mesh" {
  for_each = {
    for pair in local.vpc_peering_pairs :
    "${pair.requester.name}-${pair.accepter.name}" => pair
  }

  vpc_id      = each.value.requester.vpc_id
  peer_vpc_id = each.value.accepter.vpc_id
  
  peer_owner_id = each.value.accepter.account_id != each.value.requester.account_id ? each.value.accepter.account_id : null
  peer_region   = each.value.accepter.region != each.value.requester.region ? each.value.accepter.region : null
  
  auto_accept = each.value.accepter.account_id == each.value.requester.account_id

  accepter {
    allow_remote_vpc_dns_resolution = var.enable_dns_resolution
  }

  requester {
    allow_remote_vpc_dns_resolution = var.enable_dns_resolution
  }

  tags = {
    Name = "Peering-${each.value.requester.name}-${each.value.accepter.name}"
    RequesterVPC = each.value.requester.vpc_id
    AccepterVPC  = each.value.accepter.vpc_id
    Environment  = each.value.requester.environment
    ManagedBy    = "terraform"
  }
}

resource "aws_vpc_peering_connection_accepter" "cross_account" {
  for_each = {
    for k, v in aws_vpc_peering_connection.enterprise_mesh :
    k => v if v.peer_owner_id != null
  }

  vpc_peering_connection_id = each.value.id
  auto_accept              = true

  tags = {
    Name = "Accepter-${each.key}"
    Side = "Accepter"
  }
}

resource "aws_route" "peering_routes" {
  for_each = {
    for route in flatten([
      for pair_key, pair in local.vpc_peering_pairs : [
        for rt in pair.requester.route_table_ids : {
          route_table_id = rt
          destination_cidr_block = pair.accepter.cidr_block
          vpc_peering_connection_id = aws_vpc_peering_connection.enterprise_mesh["${pair.requester.name}-${pair.accepter.name}"].id
          key = "${pair_key}-${rt}-${pair.accepter.cidr_block}"
        }
      ]
    ]) : route.key => route
  }

  route_table_id            = each.value.route_table_id
  destination_cidr_block    = each.value.destination_cidr_block
  vpc_peering_connection_id = each.value.vpc_peering_connection_id
}

resource "aws_lambda_function" "peering_monitor" {
  filename         = "peering_monitor.zip"
  function_name    = "vpc-peering-monitor"
  role            = aws_iam_role.peering_monitor_role.arn
  handler         = "lambda_function.lambda_handler"
  runtime         = "python3.9"
  timeout         = 300

  environment {
    variables = {
      PEERING_CONNECTION_IDS = jsonencode([for pc in aws_vpc_peering_connection.enterprise_mesh : pc.id])
      SNS_TOPIC_ARN = aws_sns_topic.peering_alerts.arn
    }
  }
}
```

## Enterprise Use Cases

### Multi-Account Organizations
- **Account Isolation**: Secure connectivity between production, staging, and development accounts
- **Shared Services**: Centralized connectivity to shared services VPC across all accounts
- **Compliance Boundaries**: Separate peering configurations for different compliance requirements

### Global Enterprises
- **Multi-Region Connectivity**: Inter-region VPC peering for global application deployment
- **Disaster Recovery**: Automated failover connectivity between primary and DR regions
- **Data Sovereignty**: Region-specific peering configurations for data residency requirements

### Microservices Architectures
- **Service Mesh Connectivity**: VPC-level connectivity for microservices across different VPCs
- **Environment Promotion**: Automated peering setup for promoting services between environments
- **Traffic Segmentation**: Controlled connectivity between different service tiers

## Key Features

- **Automated Mesh Creation**: Intelligent topology generation with full mesh, hub-and-spoke, or hybrid patterns
- **Cross-Account Orchestration**: Automated cross-account role setup and peering establishment
- **Inter-Region Connectivity**: Seamless inter-region VPC peering with intelligent routing
- **CIDR Conflict Detection**: Automatic validation and conflict resolution for overlapping CIDR blocks
- **Intelligent Routing**: Automated route table management with conditional and failover routing
- **Performance Analytics**: Comprehensive traffic analysis and optimization recommendations
- **DevOps Integration**: Native integration with CI/CD pipelines and Infrastructure as Code
- **Cost Optimization**: Analysis and recommendations for optimizing peering connection costs

Connects two VPCs for private communication, their CIDR ranges can't overlap
- **Peer types:** Same or different AWS accounts and regions (inter-region peering)
- **No transitive routing:** Must create peering for each VPC pair
- **Traffic:** Uses private IPs, no internet or gateway needed
- **Limits:** Max peering connections per VPC apply
- **Use cases:** Shared services, cross-account access, hybrid architectures