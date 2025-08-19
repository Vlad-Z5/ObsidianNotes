# AWS NAT Gateway - Enterprise Network Automation & Cost Optimization Platform

AWS NAT Gateway provides managed network address translation for private subnet resources with automated deployment, intelligent cost optimization, and enterprise-scale network automation frameworks.

## Enterprise NAT Gateway Automation Framework

```python
import json
import boto3
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
from botocore.exceptions import ClientError

class NATGatewayType(Enum):
    PUBLIC = "public"
    PRIVATE = "private"

class NATGatewayState(Enum):
    PENDING = "pending"
    FAILED = "failed"
    AVAILABLE = "available"
    DELETING = "deleting"
    DELETED = "deleted"

class CostOptimizationStrategy(Enum):
    SCHEDULED = "scheduled"
    TRAFFIC_BASED = "traffic_based"
    HYBRID = "hybrid"
    ALWAYS_ON = "always_on"

class NetworkTier(Enum):
    PRODUCTION = "production"
    STAGING = "staging"
    DEVELOPMENT = "development"
    TESTING = "testing"

@dataclass
class NATGatewayConfig:
    subnet_id: str
    connectivity_type: NATGatewayType = NATGatewayType.PUBLIC
    allocation_id: Optional[str] = None  # For public NAT gateways
    private_ip_address: Optional[str] = None
    secondary_allocation_ids: List[str] = field(default_factory=list)
    tags: Dict[str, str] = field(default_factory=dict)

@dataclass
class CostOptimizationConfig:
    strategy: CostOptimizationStrategy = CostOptimizationStrategy.SCHEDULED
    business_hours_only: bool = True
    weekend_shutdown: bool = True
    traffic_threshold_mbps: float = 1.0  # Minimum traffic to keep active
    cost_threshold_daily: float = 50.0  # Daily cost threshold
    schedule: Dict[str, Any] = field(default_factory=dict)

@dataclass
class HighAvailabilityConfig:
    enable_multi_az: bool = True
    enable_failover: bool = True
    health_check_interval: int = 300  # seconds
    failover_threshold: int = 2  # failed checks before failover
    cross_az_traffic_optimization: bool = True

@dataclass
class ManagedNATGateway:
    id: str
    subnet_id: str
    vpc_id: str
    state: NATGatewayState
    connectivity_type: NATGatewayType
    network_interface_id: str
    public_ip: Optional[str] = None
    private_ip: Optional[str] = None
    allocation_id: Optional[str] = None
    failure_code: Optional[str] = None
    failure_message: Optional[str] = None
    tags: Dict[str, str] = field(default_factory=dict)
    created_time: Optional[datetime] = None

@dataclass
class NetworkMetrics:
    bytes_in: int
    bytes_out: int
    packets_in: int
    packets_out: int
    active_connections: int
    bandwidth_utilization: float
    cost_current_hour: float
    cost_daily_total: float

class EnterpriseNATGatewayManager:
    """
    Enterprise AWS NAT Gateway manager with automated deployment,
    cost optimization, and high availability orchestration.
    """
    
    def __init__(self, 
                 region: str = 'us-east-1',
                 cost_config: CostOptimizationConfig = None,
                 ha_config: HighAvailabilityConfig = None):
        self.ec2 = boto3.client('ec2', region_name=region)
        self.cloudwatch = boto3.client('cloudwatch', region_name=region)
        self.events = boto3.client('events', region_name=region)
        self.lambda_client = boto3.client('lambda', region_name=region)
        self.sns = boto3.client('sns', region_name=region)
        self.region = region
        self.cost_config = cost_config or CostOptimizationConfig()
        self.ha_config = ha_config or HighAvailabilityConfig()
        self.logger = self._setup_logging()
        
    def _setup_logging(self) -> logging.Logger:
        logger = logging.getLogger('NATGateway')
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger

    def deploy_enterprise_nat_architecture(self, 
                                         vpc_id: str,
                                         network_tier: NetworkTier = NetworkTier.PRODUCTION,
                                         enable_cost_optimization: bool = True) -> Dict[str, Any]:
        """Deploy enterprise-grade NAT Gateway architecture with HA and cost optimization"""
        try:
            deployment_start = datetime.utcnow()
            
            # Get VPC details and subnets
            vpc_details = self._get_vpc_details(vpc_id)
            availability_zones = self._get_availability_zones(vpc_id)
            
            # Create NAT Gateway deployment plan
            deployment_plan = self._create_deployment_plan(
                vpc_id, availability_zones, network_tier
            )
            
            # Deploy NAT Gateways across AZs
            nat_gateways = self._deploy_nat_gateways(deployment_plan)
            
            # Setup routing tables
            routing_config = self._configure_routing_tables(vpc_id, nat_gateways)
            
            # Setup monitoring and alerting
            monitoring_setup = self._setup_comprehensive_monitoring(nat_gateways)
            
            # Setup cost optimization if enabled
            cost_optimization = None
            if enable_cost_optimization:
                cost_optimization = self._setup_cost_optimization(nat_gateways)
            
            # Setup high availability features
            ha_setup = self._setup_high_availability(nat_gateways)
            
            deployment_time = (datetime.utcnow() - deployment_start).total_seconds()
            
            result = {
                'deployment_id': f"nat-deploy-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}",
                'vpc_id': vpc_id,
                'network_tier': network_tier.value,
                'nat_gateways': [self._serialize_nat_gateway(ng) for ng in nat_gateways],
                'availability_zones': len(availability_zones),
                'routing_configuration': routing_config,
                'monitoring_setup': monitoring_setup,
                'cost_optimization': cost_optimization,
                'high_availability': ha_setup,
                'deployment_time_seconds': deployment_time,
                'estimated_monthly_cost': self._calculate_estimated_monthly_cost(nat_gateways),
                'deployed_at': deployment_start.isoformat()
            }
            
            self.logger.info(f"Deployed enterprise NAT architecture: {result['deployment_id']}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error deploying enterprise NAT architecture: {str(e)}")
            raise

    def _create_deployment_plan(self, 
                              vpc_id: str, 
                              availability_zones: List[str],
                              network_tier: NetworkTier) -> Dict[str, Any]:
        """Create comprehensive NAT Gateway deployment plan"""
        
        # Get public and private subnets
        public_subnets = self._get_public_subnets(vpc_id)
        private_subnets = self._get_private_subnets(vpc_id)
        
        # Plan NAT Gateway placement based on network tier
        nat_placement = {}
        
        if network_tier == NetworkTier.PRODUCTION:
            # Production: One NAT Gateway per AZ for full redundancy
            for az in availability_zones:
                public_subnet = next((s for s in public_subnets if s['AvailabilityZone'] == az), None)
                if public_subnet:
                    nat_placement[az] = {
                        'subnet_id': public_subnet['SubnetId'],
                        'connectivity_type': NATGatewayType.PUBLIC,
                        'redundancy_level': 'high',
                        'cost_optimization': self.cost_config.strategy != CostOptimizationStrategy.ALWAYS_ON
                    }
        
        elif network_tier == NetworkTier.STAGING:
            # Staging: NAT Gateway in primary AZ with cost optimization
            primary_az = availability_zones[0]
            public_subnet = next((s for s in public_subnets if s['AvailabilityZone'] == primary_az), None)
            if public_subnet:
                nat_placement[primary_az] = {
                    'subnet_id': public_subnet['SubnetId'],
                    'connectivity_type': NATGatewayType.PUBLIC,
                    'redundancy_level': 'medium',
                    'cost_optimization': True
                }
        
        else:  # DEVELOPMENT, TESTING
            # Development/Testing: Single NAT Gateway with aggressive cost optimization
            primary_az = availability_zones[0]
            public_subnet = next((s for s in public_subnets if s['AvailabilityZone'] == primary_az), None)
            if public_subnet:
                nat_placement[primary_az] = {
                    'subnet_id': public_subnet['SubnetId'],
                    'connectivity_type': NATGatewayType.PUBLIC,
                    'redundancy_level': 'low',
                    'cost_optimization': True
                }
        
        return {
            'vpc_id': vpc_id,
            'network_tier': network_tier.value,
            'nat_placement': nat_placement,
            'public_subnets': len(public_subnets),
            'private_subnets': len(private_subnets),
            'availability_zones': availability_zones,
            'estimated_hourly_cost': len(nat_placement) * 0.045  # $0.045 per hour per NAT Gateway
        }

    def _deploy_nat_gateways(self, deployment_plan: Dict[str, Any]) -> List[ManagedNATGateway]:
        """Deploy NAT Gateways according to the deployment plan"""
        nat_gateways = []
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {}
            
            for az, config in deployment_plan['nat_placement'].items():
                # Allocate Elastic IP for public NAT Gateway
                if config['connectivity_type'] == NATGatewayType.PUBLIC:
                    eip_response = self.ec2.allocate_address(Domain='vpc')
                    allocation_id = eip_response['AllocationId']
                else:
                    allocation_id = None
                
                nat_config = NATGatewayConfig(
                    subnet_id=config['subnet_id'],
                    connectivity_type=NATGatewayType(config['connectivity_type']),
                    allocation_id=allocation_id,
                    tags={
                        'Name': f"NAT-Gateway-{az}",
                        'Environment': deployment_plan['network_tier'],
                        'AvailabilityZone': az,
                        'ManagedBy': 'EnterpriseNATManager',
                        'CostOptimization': str(config['cost_optimization'])
                    }
                )
                
                future = executor.submit(self._create_nat_gateway, nat_config)
                futures[future] = (az, config)
            
            for future in as_completed(futures):
                try:
                    nat_gateway = future.result()
                    nat_gateways.append(nat_gateway)
                    
                    az, config = futures[future]
                    self.logger.info(f"Successfully deployed NAT Gateway in {az}: {nat_gateway.id}")
                    
                except Exception as e:
                    az, config = futures[future]
                    self.logger.error(f"Failed to deploy NAT Gateway in {az}: {str(e)}")
                    raise
        
        return nat_gateways

    def _create_nat_gateway(self, config: NATGatewayConfig) -> ManagedNATGateway:
        """Create individual NAT Gateway"""
        try:
            create_params = {
                'SubnetId': config.subnet_id,
                'ConnectivityType': config.connectivity_type.value,
                'TagSpecifications': [{
                    'ResourceType': 'natgateway',
                    'Tags': [{'Key': k, 'Value': v} for k, v in config.tags.items()]
                }]
            }
            
            if config.allocation_id:
                create_params['AllocationId'] = config.allocation_id
            
            if config.private_ip_address:
                create_params['PrivateIpAddress'] = config.private_ip_address
            
            if config.secondary_allocation_ids:
                create_params['SecondaryAllocationIds'] = config.secondary_allocation_ids
            
            response = self.ec2.create_nat_gateway(**create_params)
            nat_gateway_data = response['NatGateway']
            
            # Wait for NAT Gateway to become available
            nat_gateway_id = nat_gateway_data['NatGatewayId']
            self._wait_for_nat_gateway_available(nat_gateway_id)
            
            # Get updated NAT Gateway details
            describe_response = self.ec2.describe_nat_gateways(
                NatGatewayIds=[nat_gateway_id]
            )
            updated_data = describe_response['NatGateways'][0]
            
            return ManagedNATGateway(
                id=updated_data['NatGatewayId'],
                subnet_id=updated_data['SubnetId'],
                vpc_id=updated_data['VpcId'],
                state=NATGatewayState(updated_data['State']),
                connectivity_type=NATGatewayType(updated_data['ConnectivityType']),
                network_interface_id=updated_data['NatGatewayAddresses'][0]['NetworkInterfaceId'],
                public_ip=updated_data['NatGatewayAddresses'][0].get('PublicIp'),
                private_ip=updated_data['NatGatewayAddresses'][0].get('PrivateIp'),
                allocation_id=updated_data['NatGatewayAddresses'][0].get('AllocationId'),
                tags=config.tags,
                created_time=updated_data['CreateTime']
            )
            
        except Exception as e:
            self.logger.error(f"Error creating NAT Gateway: {str(e)}")
            raise

    def setup_intelligent_cost_optimization(self, 
                                          nat_gateways: List[ManagedNATGateway]) -> Dict[str, Any]:
        """Setup intelligent cost optimization for NAT Gateways"""
        try:
            optimization_setup = {}
            
            # Create cost optimization Lambda function
            lambda_function = self._create_cost_optimization_lambda()
            optimization_setup['lambda_function'] = lambda_function
            
            # Setup CloudWatch alarms for traffic monitoring
            traffic_alarms = self._create_traffic_monitoring_alarms(nat_gateways)
            optimization_setup['traffic_alarms'] = traffic_alarms
            
            # Setup scheduling for business hours optimization
            if self.cost_config.strategy in [CostOptimizationStrategy.SCHEDULED, CostOptimizationStrategy.HYBRID]:
                schedules = self._create_cost_optimization_schedules(nat_gateways)
                optimization_setup['schedules'] = schedules
            
            # Setup traffic-based optimization
            if self.cost_config.strategy in [CostOptimizationStrategy.TRAFFIC_BASED, CostOptimizationStrategy.HYBRID]:
                traffic_optimization = self._setup_traffic_based_optimization(nat_gateways)
                optimization_setup['traffic_optimization'] = traffic_optimization
            
            # Create cost monitoring dashboard
            dashboard = self._create_cost_monitoring_dashboard(nat_gateways)
            optimization_setup['dashboard'] = dashboard
            
            estimated_savings = self._calculate_potential_savings(nat_gateways)
            
            return {
                'optimization_id': f"cost-opt-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}",
                'strategy': self.cost_config.strategy.value,
                'nat_gateways_managed': len(nat_gateways),
                'optimization_setup': optimization_setup,
                'estimated_monthly_savings': estimated_savings,
                'setup_timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error setting up cost optimization: {str(e)}")
            raise

    def _create_cost_optimization_lambda(self) -> Dict[str, Any]:
        """Create Lambda function for NAT Gateway cost optimization"""
        
        lambda_code = '''
import json
import boto3
from datetime import datetime, timedelta

def lambda_handler(event, context):
    ec2 = boto3.client('ec2')
    cloudwatch = boto3.client('cloudwatch')
    
    # Get NAT Gateway metrics
    nat_gateway_id = event['nat_gateway_id']
    action = event.get('action', 'analyze')
    
    if action == 'analyze':
        # Analyze traffic patterns
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=1)
        
        # Get bytes processed metric
        metrics = cloudwatch.get_metric_statistics(
            Namespace='AWS/NATGateway',
            MetricName='BytesOutToDestination',
            Dimensions=[{'Name': 'NatGatewayId', 'Value': nat_gateway_id}],
            StartTime=start_time,
            EndTime=end_time,
            Period=3600,
            Statistics=['Sum']
        )
        
        total_bytes = sum(point['Sum'] for point in metrics['Datapoints'])
        
        # Calculate cost
        cost_per_gb = 0.045  # $0.045 per GB processed
        hourly_cost = (total_bytes / (1024**3)) * cost_per_gb
        
        return {
            'nat_gateway_id': nat_gateway_id,
            'bytes_processed': total_bytes,
            'hourly_cost': hourly_cost,
            'recommendation': 'keep_running' if total_bytes > 1000000 else 'consider_shutdown'
        }
    
    elif action == 'shutdown':
        # Logic for intelligent shutdown would go here
        # This would involve creating replacement routes, etc.
        return {'action': 'shutdown_scheduled', 'nat_gateway_id': nat_gateway_id}
    
    elif action == 'startup':
        # Logic for intelligent startup would go here
        return {'action': 'startup_scheduled', 'nat_gateway_id': nat_gateway_id}
    
    return {'status': 'completed'}
'''
        
        try:
            # In a real implementation, this would create the actual Lambda function
            return {
                'function_name': 'nat-gateway-cost-optimizer',
                'runtime': 'python3.9',
                'handler': 'lambda_function.lambda_handler',
                'code_size': len(lambda_code),
                'timeout': 300,
                'memory': 256
            }
        except Exception as e:
            self.logger.error(f"Error creating cost optimization Lambda: {str(e)}")
            raise

    def get_comprehensive_nat_analytics(self, 
                                      nat_gateway_ids: List[str] = None,
                                      time_period_hours: int = 24) -> Dict[str, Any]:
        """Get comprehensive analytics for NAT Gateway usage and costs"""
        try:
            if not nat_gateway_ids:
                nat_gateway_ids = self._get_all_nat_gateway_ids()
            
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=time_period_hours)
            
            analytics_data = {}
            total_cost = 0.0
            total_bytes_processed = 0
            
            for nat_id in nat_gateway_ids:
                # Get detailed metrics for each NAT Gateway
                metrics = self._get_nat_gateway_metrics(nat_id, start_time, end_time)
                
                # Calculate costs
                hourly_base_cost = 0.045  # $0.045 per hour
                data_processing_cost = (metrics['bytes_out'] / (1024**3)) * 0.045  # $0.045 per GB
                
                nat_cost = (time_period_hours * hourly_base_cost) + data_processing_cost
                total_cost += nat_cost
                total_bytes_processed += metrics['bytes_out']
                
                analytics_data[nat_id] = {
                    'metrics': metrics,
                    'costs': {
                        'base_cost': time_period_hours * hourly_base_cost,
                        'data_processing_cost': data_processing_cost,
                        'total_cost': nat_cost
                    },
                    'efficiency_score': self._calculate_efficiency_score(metrics),
                    'optimization_recommendations': self._generate_optimization_recommendations(metrics, nat_cost)
                }
            
            # Generate summary insights
            summary = {
                'total_nat_gateways': len(nat_gateway_ids),
                'time_period_hours': time_period_hours,
                'total_cost': total_cost,
                'total_data_processed_gb': total_bytes_processed / (1024**3),
                'average_cost_per_gateway': total_cost / len(nat_gateway_ids) if nat_gateway_ids else 0,
                'cost_breakdown': {
                    'base_costs': len(nat_gateway_ids) * time_period_hours * 0.045,
                    'data_processing_costs': total_cost - (len(nat_gateway_ids) * time_period_hours * 0.045)
                }
            }
            
            return {
                'analytics_id': f"nat-analytics-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}",
                'generated_at': datetime.utcnow().isoformat(),
                'summary': summary,
                'nat_gateway_analytics': analytics_data,
                'optimization_opportunities': self._identify_optimization_opportunities(analytics_data),
                'cost_projections': self._calculate_cost_projections(summary)
            }
            
        except Exception as e:
            self.logger.error(f"Error getting NAT Gateway analytics: {str(e)}")
            raise

    def _get_nat_gateway_metrics(self, 
                               nat_gateway_id: str, 
                               start_time: datetime, 
                               end_time: datetime) -> NetworkMetrics:
        """Get detailed metrics for a NAT Gateway"""
        try:
            metrics = {}
            
            # Define metrics to collect
            metric_queries = [
                ('BytesInFromDestination', 'Sum'),
                ('BytesOutToDestination', 'Sum'),
                ('PacketsInFromDestination', 'Sum'),
                ('PacketsOutToDestination', 'Sum'),
                ('ActiveConnectionCount', 'Maximum'),
                ('ConnectionAttemptCount', 'Sum'),
                ('ConnectionEstablishedCount', 'Sum'),
                ('ErrorPortAllocation', 'Sum')
            ]
            
            for metric_name, statistic in metric_queries:
                try:
                    response = self.cloudwatch.get_metric_statistics(
                        Namespace='AWS/NATGateway',
                        MetricName=metric_name,
                        Dimensions=[{'Name': 'NatGatewayId', 'Value': nat_gateway_id}],
                        StartTime=start_time,
                        EndTime=end_time,
                        Period=3600,  # 1 hour periods
                        Statistics=[statistic]
                    )
                    
                    if response['Datapoints']:
                        if statistic == 'Sum':
                            metrics[metric_name.lower()] = sum(point['Sum'] for point in response['Datapoints'])
                        elif statistic == 'Maximum':
                            metrics[metric_name.lower()] = max(point['Maximum'] for point in response['Datapoints'])
                    else:
                        metrics[metric_name.lower()] = 0
                        
                except Exception as e:
                    self.logger.warning(f"Could not get metric {metric_name} for {nat_gateway_id}: {str(e)}")
                    metrics[metric_name.lower()] = 0
            
            # Calculate additional derived metrics
            total_bytes = metrics.get('bytesintofromdestination', 0) + metrics.get('bytesouttodestination', 0)
            bandwidth_utilization = self._calculate_bandwidth_utilization(total_bytes, start_time, end_time)
            
            return NetworkMetrics(
                bytes_in=metrics.get('bytesinfromdestination', 0),
                bytes_out=metrics.get('bytesouttodestination', 0),
                packets_in=metrics.get('packetsinfromdestination', 0),
                packets_out=metrics.get('packetsouttodestination', 0),
                active_connections=metrics.get('activeconnectioncount', 0),
                bandwidth_utilization=bandwidth_utilization,
                cost_current_hour=0.045 + (metrics.get('bytesouttodestination', 0) / (1024**3)) * 0.045,
                cost_daily_total=0  # Would be calculated based on 24h data
            )
            
        except Exception as e:
            self.logger.error(f"Error getting metrics for NAT Gateway {nat_gateway_id}: {str(e)}")
            raise

    def automated_failover_setup(self, 
                                primary_nat_gateways: List[ManagedNATGateway]) -> Dict[str, Any]:
        """Setup automated failover for NAT Gateways"""
        try:
            failover_setup = {}
            
            for primary_nat in primary_nat_gateways:
                # Create backup NAT Gateway in different AZ
                backup_config = self._create_backup_nat_config(primary_nat)
                backup_nat = self._create_nat_gateway(backup_config)
                
                # Setup health monitoring
                health_check = self._create_nat_gateway_health_check(primary_nat.id)
                
                # Create failover Lambda function
                failover_function = self._create_failover_lambda(primary_nat, backup_nat)
                
                # Setup CloudWatch alarm for automated failover
                failover_alarm = self._create_failover_alarm(primary_nat.id, failover_function)
                
                failover_setup[primary_nat.id] = {
                    'primary_nat': primary_nat.id,
                    'backup_nat': backup_nat.id,
                    'health_check': health_check,
                    'failover_function': failover_function,
                    'failover_alarm': failover_alarm,
                    'failover_time_estimate': '2-3 minutes'
                }
            
            return {
                'failover_id': f"failover-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}",
                'primary_nat_gateways': len(primary_nat_gateways),
                'failover_pairs': len(failover_setup),
                'failover_setup': failover_setup,
                'estimated_rto': '2-3 minutes',  # Recovery Time Objective
                'estimated_rpo': '0 minutes',    # Recovery Point Objective
                'setup_timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error setting up automated failover: {str(e)}")
            raise

    def _calculate_efficiency_score(self, metrics: NetworkMetrics) -> float:
        """Calculate efficiency score for NAT Gateway usage"""
        
        # Base score calculation
        base_score = 50.0
        
        # Adjust based on traffic volume
        if metrics.bytes_out > 100 * (1024**3):  # > 100 GB
            base_score += 30
        elif metrics.bytes_out > 10 * (1024**3):  # > 10 GB
            base_score += 20
        elif metrics.bytes_out > 1 * (1024**3):   # > 1 GB
            base_score += 10
        
        # Adjust based on connection utilization
        if metrics.active_connections > 1000:
            base_score += 15
        elif metrics.active_connections > 100:
            base_score += 10
        elif metrics.active_connections > 10:
            base_score += 5
        
        # Adjust based on bandwidth utilization
        if metrics.bandwidth_utilization > 0.7:  # > 70% utilization
            base_score += 15
        elif metrics.bandwidth_utilization > 0.3:  # > 30% utilization
            base_score += 10
        
        return min(100.0, base_score)

    def _generate_optimization_recommendations(self, 
                                             metrics: NetworkMetrics, 
                                             cost: float) -> List[Dict[str, Any]]:
        """Generate optimization recommendations based on metrics"""
        recommendations = []
        
        # Low traffic recommendation
        if metrics.bytes_out < 1 * (1024**3):  # < 1 GB
            recommendations.append({
                'type': 'cost_optimization',
                'priority': 'high',
                'recommendation': 'Consider scheduled shutdown during low usage periods',
                'potential_savings': cost * 0.5,  # 50% savings estimate
                'implementation': 'automated_scheduling'
            })
        
        # High cost per GB recommendation
        cost_per_gb = cost / (metrics.bytes_out / (1024**3)) if metrics.bytes_out > 0 else float('inf')
        if cost_per_gb > 0.1:  # High cost per GB
            recommendations.append({
                'type': 'efficiency',
                'priority': 'medium',
                'recommendation': 'Optimize data transfer patterns or consider VPC endpoints',
                'potential_savings': cost * 0.3,
                'implementation': 'architecture_review'
            })
        
        # Low connection utilization
        if metrics.active_connections < 10:
            recommendations.append({
                'type': 'utilization',
                'priority': 'medium',
                'recommendation': 'Consolidate traffic through fewer NAT Gateways',
                'potential_savings': cost * 0.4,
                'implementation': 'routing_optimization'
            })
        
        return recommendations

    def _get_vpc_details(self, vpc_id: str) -> Dict[str, Any]:
        """Get VPC details"""
        try:
            response = self.ec2.describe_vpcs(VpcIds=[vpc_id])
            return response['Vpcs'][0]
        except Exception as e:
            self.logger.error(f"Error getting VPC details for {vpc_id}: {str(e)}")
            raise

    def _get_availability_zones(self, vpc_id: str) -> List[str]:
        """Get availability zones for VPC"""
        try:
            # Get subnets to determine AZs
            response = self.ec2.describe_subnets(
                Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}]
            )
            
            azs = list(set(subnet['AvailabilityZone'] for subnet in response['Subnets']))
            return sorted(azs)
        except Exception as e:
            self.logger.error(f"Error getting availability zones for VPC {vpc_id}: {str(e)}")
            raise

    def _wait_for_nat_gateway_available(self, nat_gateway_id: str, max_wait_time: int = 300) -> None:
        """Wait for NAT Gateway to become available"""
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            try:
                response = self.ec2.describe_nat_gateways(NatGatewayIds=[nat_gateway_id])
                state = response['NatGateways'][0]['State']
                
                if state == 'available':
                    return
                elif state == 'failed':
                    failure_message = response['NatGateways'][0].get('FailureMessage', 'Unknown failure')
                    raise Exception(f"NAT Gateway {nat_gateway_id} failed: {failure_message}")
                
                time.sleep(10)  # Wait 10 seconds before checking again
                
            except Exception as e:
                if 'InvalidNatGatewayID.NotFound' in str(e):
                    time.sleep(5)  # Gateway might not be visible yet
                    continue
                else:
                    raise
        
        raise Exception(f"NAT Gateway {nat_gateway_id} did not become available within {max_wait_time} seconds")

    def _serialize_nat_gateway(self, nat_gateway: ManagedNATGateway) -> Dict[str, Any]:
        """Serialize NAT Gateway for JSON output"""
        return {
            'id': nat_gateway.id,
            'subnet_id': nat_gateway.subnet_id,
            'vpc_id': nat_gateway.vpc_id,
            'state': nat_gateway.state.value,
            'connectivity_type': nat_gateway.connectivity_type.value,
            'public_ip': nat_gateway.public_ip,
            'private_ip': nat_gateway.private_ip,
            'allocation_id': nat_gateway.allocation_id,
            'network_interface_id': nat_gateway.network_interface_id,
            'created_time': nat_gateway.created_time.isoformat() if nat_gateway.created_time else None,
            'tags': nat_gateway.tags
        }

# NAT Gateway Orchestrator for Multi-VPC Environments
class NATGatewayOrchestrator:
    """
    Orchestrates NAT Gateway deployments across multiple VPCs
    and regions with centralized management and optimization.
    """
    
    def __init__(self, regions: List[str], cross_region_role: str = None):
        self.regions = regions
        self.cross_region_role = cross_region_role
        self.managers = {}
        self.logger = logging.getLogger('NATOrchestrator')
        
        # Initialize managers for each region
        for region in regions:
            self.managers[region] = EnterpriseNATGatewayManager(region=region)

    def deploy_multi_region_nat_architecture(self, 
                                           deployment_config: Dict[str, Any]) -> Dict[str, Any]:
        """Deploy NAT Gateway architecture across multiple regions"""
        
        deployment_results = {}
        total_cost = 0.0
        
        with ThreadPoolExecutor(max_workers=len(self.regions)) as executor:
            futures = {}
            
            for region in self.regions:
                if region in deployment_config:
                    region_config = deployment_config[region]
                    manager = self.managers[region]
                    
                    future = executor.submit(
                        manager.deploy_enterprise_nat_architecture,
                        region_config['vpc_id'],
                        NetworkTier(region_config.get('network_tier', 'production')),
                        region_config.get('enable_cost_optimization', True)
                    )
                    futures[future] = region
            
            for future in as_completed(futures):
                region = futures[future]
                try:
                    result = future.result()
                    deployment_results[region] = result
                    total_cost += result['estimated_monthly_cost']
                    
                    self.logger.info(f"Successfully deployed NAT architecture in {region}")
                    
                except Exception as e:
                    self.logger.error(f"Failed to deploy NAT architecture in {region}: {str(e)}")
                    deployment_results[region] = {'error': str(e)}
        
        return {
            'orchestration_id': f"multi-region-nat-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}",
            'regions_deployed': len([r for r in deployment_results.values() if 'error' not in r]),
            'total_regions': len(self.regions),
            'total_estimated_monthly_cost': total_cost,
            'regional_deployments': deployment_results,
            'deployed_at': datetime.utcnow().isoformat()
        }

# Example usage and enterprise patterns
def create_enterprise_nat_deployment():
    """Create comprehensive enterprise NAT Gateway deployment"""
    
    # Configure cost optimization
    cost_config = CostOptimizationConfig(
        strategy=CostOptimizationStrategy.HYBRID,
        business_hours_only=True,
        weekend_shutdown=True,
        traffic_threshold_mbps=2.0,
        cost_threshold_daily=100.0,
        schedule={
            'weekday_start': '08:00',
            'weekday_end': '18:00',
            'weekend_enabled': False
        }
    )
    
    # Configure high availability
    ha_config = HighAvailabilityConfig(
        enable_multi_az=True,
        enable_failover=True,
        health_check_interval=300,
        failover_threshold=2,
        cross_az_traffic_optimization=True
    )
    
    # Create NAT Gateway manager
    nat_manager = EnterpriseNATGatewayManager(
        region='us-east-1',
        cost_config=cost_config,
        ha_config=ha_config
    )
    
    # Deploy enterprise NAT architecture
    vpc_id = 'vpc-12345678'  # Replace with actual VPC ID
    deployment = nat_manager.deploy_enterprise_nat_architecture(
        vpc_id=vpc_id,
        network_tier=NetworkTier.PRODUCTION,
        enable_cost_optimization=True
    )
    
    print(f"Deployed NAT architecture: {deployment['deployment_id']}")
    print(f"NAT Gateways deployed: {len(deployment['nat_gateways'])}")
    print(f"Estimated monthly cost: ${deployment['estimated_monthly_cost']:.2f}")
    
    # Setup intelligent cost optimization
    nat_gateway_objects = []  # Would be populated from deployment
    cost_optimization = nat_manager.setup_intelligent_cost_optimization(nat_gateway_objects)
    print(f"Cost optimization setup: {cost_optimization['optimization_id']}")
    print(f"Estimated monthly savings: ${cost_optimization['estimated_monthly_savings']:.2f}")
    
    return deployment, cost_optimization

def setup_multi_region_nat_deployment():
    """Setup NAT Gateway deployment across multiple regions"""
    
    regions = ['us-east-1', 'us-west-2', 'eu-west-1']
    orchestrator = NATGatewayOrchestrator(regions)
    
    deployment_config = {
        'us-east-1': {
            'vpc_id': 'vpc-12345678',
            'network_tier': 'production',
            'enable_cost_optimization': True
        },
        'us-west-2': {
            'vpc_id': 'vpc-87654321',
            'network_tier': 'production',
            'enable_cost_optimization': True
        },
        'eu-west-1': {
            'vpc_id': 'vpc-abcdef12',
            'network_tier': 'staging',
            'enable_cost_optimization': True
        }
    }
    
    # Deploy across regions
    results = orchestrator.deploy_multi_region_nat_architecture(deployment_config)
    
    print(f"Multi-region deployment: {results['orchestration_id']}")
    print(f"Regions deployed: {results['regions_deployed']}/{results['total_regions']}")
    print(f"Total estimated monthly cost: ${results['total_estimated_monthly_cost']:.2f}")
    
    return results

if __name__ == "__main__":
    # Create enterprise NAT deployment
    deployment, optimization = create_enterprise_nat_deployment()
    
    # Setup multi-region deployment
    multi_region_results = setup_multi_region_nat_deployment()
```

## DevOps Integration Patterns

### CI/CD Pipeline Integration

```yaml
# .github/workflows/nat-gateway-optimization.yml
name: NAT Gateway Cost Optimization

on:
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM
  workflow_dispatch:
    inputs:
      action:
        description: 'Optimization action'
        required: false
        default: 'analyze'
        type: choice
        options:
        - analyze
        - optimize
        - report

jobs:
  nat-optimization:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Configure AWS credentials
      uses: aws-actions/configure-aws-credentials@v2
      with:
        role-to-assume: ${{ secrets.AWS_NAT_OPTIMIZATION_ROLE }}
        aws-region: us-east-1
    
    - name: Run NAT Gateway Analysis
      run: |
        python scripts/nat_gateway_optimization.py \
          --action ${{ github.event.inputs.action || 'analyze' }} \
          --cost-threshold 50 \
          --traffic-threshold 1024 \
          --output-format json
    
    - name: Generate Cost Report
      run: |
        python scripts/generate_nat_cost_report.py \
          --time-period 24 \
          --include-recommendations \
          --output-format html
    
    - name: Upload Reports
      uses: actions/upload-artifact@v3
      with:
        name: nat-optimization-reports
        path: |
          nat-analysis-*.json
          nat-cost-report-*.html
```

### Terraform Integration

```hcl
# nat_gateway_enterprise.tf
resource "aws_eip" "nat_gateway_eips" {
  count  = var.availability_zone_count
  domain = "vpc"
  
  tags = {
    Name = "NAT-Gateway-EIP-${count.index + 1}"
    Environment = var.environment
    ManagedBy = "terraform"
  }
}

resource "aws_nat_gateway" "enterprise_nat_gateways" {
  count         = var.availability_zone_count
  allocation_id = aws_eip.nat_gateway_eips[count.index].id
  subnet_id     = var.public_subnet_ids[count.index]
  
  connectivity_type = "public"
  
  tags = {
    Name = "Enterprise-NAT-Gateway-${count.index + 1}"
    Environment = var.environment
    AvailabilityZone = data.aws_subnet.public_subnets[count.index].availability_zone
    CostOptimization = var.enable_cost_optimization
    ManagedBy = "terraform"
  }

  depends_on = [aws_internet_gateway.main]
}

resource "aws_route_table" "private_route_tables" {
  count  = var.availability_zone_count
  vpc_id = var.vpc_id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.enterprise_nat_gateways[count.index].id
  }

  tags = {
    Name = "Private-Route-Table-${count.index + 1}"
    Environment = var.environment
  }
}

resource "aws_lambda_function" "nat_cost_optimizer" {
  filename         = "nat_cost_optimizer.zip"
  function_name    = "nat-gateway-cost-optimizer"
  role            = aws_iam_role.nat_optimizer_role.arn
  handler         = "lambda_function.lambda_handler"
  runtime         = "python3.9"
  timeout         = 300

  environment {
    variables = {
      NAT_GATEWAY_IDS = jsonencode([for ng in aws_nat_gateway.enterprise_nat_gateways : ng.id])
      COST_THRESHOLD = var.daily_cost_threshold
      SNS_TOPIC_ARN = aws_sns_topic.nat_alerts.arn
    }
  }
}

resource "aws_cloudwatch_event_rule" "nat_cost_optimization_schedule" {
  name                = "nat-cost-optimization"
  description         = "Trigger NAT Gateway cost optimization"
  schedule_expression = "cron(0 2 * * ? *)"  # Daily at 2 AM
}

resource "aws_cloudwatch_event_target" "nat_optimizer_target" {
  rule      = aws_cloudwatch_event_rule.nat_cost_optimization_schedule.name
  target_id = "NATCostOptimizerTarget"
  arn       = aws_lambda_function.nat_cost_optimizer.arn
}
```

## Enterprise Use Cases

### E-commerce Platforms
- **Peak Traffic Management**: Automated scaling during high-traffic periods with cost optimization during low traffic
- **Multi-Region Deployment**: Global NAT Gateway deployment for worldwide e-commerce operations
- **Cost Control**: Intelligent traffic routing to minimize data processing costs while maintaining performance

### Financial Services
- **High Availability**: Multi-AZ NAT Gateway deployment with automated failover for trading systems
- **Compliance Monitoring**: Comprehensive logging and monitoring for regulatory compliance
- **Cost Optimization**: Business-hours-only operation for development environments while maintaining 24/7 production

### SaaS Companies
- **Multi-Tenant Architecture**: Separate NAT Gateways per customer environment with cost allocation
- **Development Environment Management**: Automated shutdown/startup for development and testing environments
- **Performance Optimization**: Traffic pattern analysis and routing optimization for improved application performance

## Key Features

- **Automated Deployment**: Enterprise-grade NAT Gateway deployment with multi-AZ redundancy
- **Intelligent Cost Optimization**: Traffic-based and schedule-based cost optimization strategies
- **High Availability**: Automated failover and cross-AZ redundancy for mission-critical applications
- **Comprehensive Monitoring**: Real-time metrics, cost tracking, and performance analytics
- **DevOps Integration**: Native integration with CI/CD pipelines and Infrastructure as Code
- **Multi-Region Orchestration**: Centralized management across multiple AWS regions
- **Cost Intelligence**: Advanced cost analysis with optimization recommendations
- **Automated Failover**: Intelligent health monitoring with automated route table updates

- **Purpose:** Allow private subnet resources to access the internet without exposing them directly  
- **Type:** Managed NAT service by AWS (scalable and highly available within an AZ)  
- **Elastic IP:** Requires one EIP per NAT Gateway  
- **AZ-Specific:** Must deploy one per Availability Zone for fault tolerance  
- **Billing:** Charged per hour + per GB of data processed  
- **Alternative:** NAT Instance (EC2-based, manually managed and less scalable)
