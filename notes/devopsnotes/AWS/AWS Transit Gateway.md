# AWS Transit Gateway - Enterprise Network Orchestration Platform

Centralized network hub that connects VPCs, on-premises networks, and remote locations through a single managed service with enterprise automation, advanced routing, and comprehensive network orchestration capabilities.

## Core Features & Components

- **Centralized connectivity hub** for VPCs, VPN connections, Direct Connect, and peered Transit Gateways
- **Multi-account network sharing** with AWS Resource Access Manager (RAM) integration
- **Advanced routing control** with route tables, propagation, and association automation
- **Inter-region peering** for global network connectivity and disaster recovery
- **High-performance networking** with up to 50 Gbps per VPC attachment
- **Multicast support** for distributed applications and real-time data streaming
- **Security groups integration** with centralized network access control
- **VPN and Direct Connect** hybrid connectivity with automated failover
- **Network monitoring** with VPC Flow Logs and CloudWatch metrics integration
- **Cost optimization** through intelligent routing and bandwidth management
- **Compliance automation** with network segmentation and audit trail capabilities
- **DNS resolution control** with Route 53 Resolver integration

## Enterprise Transit Gateway Orchestration Framework

```python
import json
import boto3
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Union
from botocore.exceptions import ClientError
import time
import uuid

class AttachmentType(Enum):
    VPC = "vpc"
    VPN = "vpn"
    DIRECT_CONNECT_GATEWAY = "direct-connect-gateway"
    PEERING = "peering"

class AttachmentState(Enum):
    INITIATING = "initiating"
    PENDING_ACCEPTANCE = "pendingAcceptance"
    ROLLING_BACK = "rollingBack"
    PENDING = "pending"
    AVAILABLE = "available"
    MODIFYING = "modifying"
    DELETING = "deleting"
    DELETED = "deleted"
    FAILED = "failed"
    REJECTED = "rejected"

class RouteState(Enum):
    PENDING = "pending"
    ACTIVE = "active"
    BLACKHOLE = "blackhole"

class PropagationState(Enum):
    ENABLING = "enabling"
    ENABLED = "enabled"
    DISABLING = "disabling"
    DISABLED = "disabled"

@dataclass
class NetworkCIDR:
    cidr_block: str
    description: str
    region: Optional[str] = None
    availability_zone: Optional[str] = None

@dataclass
class RouteTableEntry:
    destination_cidr: str
    target_attachment_id: str
    route_type: str = "static"
    state: RouteState = RouteState.PENDING

@dataclass
class TransitGatewayConfig:
    description: str
    amazon_side_asn: int = 64512
    auto_accept_shared_attachments: str = "disable"
    auto_cross_account_attachment: str = "disable"
    default_route_table_association: str = "enable"
    default_route_table_propagation: str = "enable"
    dns_support: str = "enable"
    multicast_support: str = "disable"
    vpn_ecmp_support: str = "enable"
    tags: Dict[str, str] = field(default_factory=dict)

@dataclass
class VPCAttachmentConfig:
    vpc_id: str
    subnet_ids: List[str]
    route_table_id: Optional[str] = None
    dns_support: str = "enable"
    ipv6_support: str = "disable"
    appliance_mode_support: str = "disable"
    tags: Dict[str, str] = field(default_factory=dict)

@dataclass
class VPNAttachmentConfig:
    customer_gateway_id: str
    vpn_connection_id: Optional[str] = None
    static_routes_only: bool = False
    tags: Dict[str, str] = field(default_factory=dict)

@dataclass
class DirectConnectAttachmentConfig:
    direct_connect_gateway_id: str
    tags: Dict[str, str] = field(default_factory=dict)

@dataclass
class PeeringAttachmentConfig:
    peer_transit_gateway_id: str
    peer_account_id: str
    peer_region: str
    tags: Dict[str, str] = field(default_factory=dict)

class EnterpriseTransitGatewayManager:
    """
    Enterprise AWS Transit Gateway manager with automated network orchestration,
    multi-account connectivity, and comprehensive routing management.
    """
    
    def __init__(self, region: str = 'us-east-1'):
        self.ec2 = boto3.client('ec2', region_name=region)
        self.ram = boto3.client('ram', region_name=region)
        self.cloudwatch = boto3.client('cloudwatch', region_name=region)
        self.region = region
        self.logger = self._setup_logging()
        
    def _setup_logging(self) -> logging.Logger:
        logger = logging.getLogger('TransitGatewayManager')
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger

    def create_transit_gateway(self, config: TransitGatewayConfig) -> Dict[str, Any]:
        """Create Transit Gateway with enterprise configuration"""
        try:
            response = self.ec2.create_transit_gateway(
                Description=config.description,
                Options={
                    'AmazonSideAsn': config.amazon_side_asn,
                    'AutoAcceptSharedAttachments': config.auto_accept_shared_attachments,
                    'DefaultRouteTableAssociation': config.default_route_table_association,
                    'DefaultRouteTablePropagation': config.default_route_table_propagation,
                    'DnsSupport': config.dns_support,
                    'MulticastSupport': config.multicast_support,
                    'VpnEcmpSupport': config.vpn_ecmp_support
                },
                TagSpecifications=[
                    {
                        'ResourceType': 'transit-gateway',
                        'Tags': [
                            {'Key': k, 'Value': v} 
                            for k, v in config.tags.items()
                        ]
                    }
                ]
            )
            
            transit_gateway_id = response['TransitGateway']['TransitGatewayId']
            
            # Wait for Transit Gateway to become available
            self._wait_for_transit_gateway_available(transit_gateway_id)
            
            self.logger.info(f"Created Transit Gateway: {transit_gateway_id}")
            
            return {
                'transit_gateway_id': transit_gateway_id,
                'transit_gateway_arn': response['TransitGateway']['TransitGatewayArn'],
                'state': response['TransitGateway']['State'],
                'owner_id': response['TransitGateway']['OwnerId'],
                'description': config.description,
                'status': 'created'
            }
            
        except ClientError as e:
            self.logger.error(f"Error creating Transit Gateway: {str(e)}")
            raise

    def attach_vpc(self, transit_gateway_id: str, config: VPCAttachmentConfig) -> Dict[str, Any]:
        """Attach VPC to Transit Gateway with advanced configuration"""
        try:
            response = self.ec2.create_transit_gateway_vpc_attachment(
                TransitGatewayId=transit_gateway_id,
                VpcId=config.vpc_id,
                SubnetIds=config.subnet_ids,
                Options={
                    'DnsSupport': config.dns_support,
                    'Ipv6Support': config.ipv6_support,
                    'ApplianceModeSupport': config.appliance_mode_support
                },
                TagSpecifications=[
                    {
                        'ResourceType': 'transit-gateway-attachment',
                        'Tags': [
                            {'Key': k, 'Value': v} 
                            for k, v in config.tags.items()
                        ]
                    }
                ]
            )
            
            attachment_id = response['TransitGatewayVpcAttachment']['TransitGatewayAttachmentId']
            
            # Wait for attachment to become available
            self._wait_for_attachment_available(attachment_id)
            
            # Associate with route table if specified
            if config.route_table_id:
                self.associate_route_table(config.route_table_id, attachment_id)
            
            self.logger.info(f"Attached VPC {config.vpc_id} to Transit Gateway: {attachment_id}")
            
            return {
                'attachment_id': attachment_id,
                'transit_gateway_id': transit_gateway_id,
                'vpc_id': config.vpc_id,
                'state': response['TransitGatewayVpcAttachment']['State'],
                'subnet_ids': config.subnet_ids,
                'status': 'attached'
            }
            
        except ClientError as e:
            self.logger.error(f"Error attaching VPC: {str(e)}")
            raise

    def attach_vpn(self, transit_gateway_id: str, config: VPNAttachmentConfig) -> Dict[str, Any]:
        """Attach VPN connection to Transit Gateway"""
        try:
            # Create VPN connection if not provided
            if not config.vpn_connection_id:
                vpn_response = self.ec2.create_vpn_connection(
                    CustomerGatewayId=config.customer_gateway_id,
                    Type='ipsec.1',
                    TransitGatewayId=transit_gateway_id,
                    StaticRoutesOnly=config.static_routes_only,
                    TagSpecifications=[
                        {
                            'ResourceType': 'vpn-connection',
                            'Tags': [
                                {'Key': k, 'Value': v} 
                                for k, v in config.tags.items()
                            ]
                        }
                    ]
                )
                vpn_connection_id = vpn_response['VpnConnection']['VpnConnectionId']
            else:
                vpn_connection_id = config.vpn_connection_id
            
            # Wait for VPN connection to become available
            self._wait_for_vpn_available(vpn_connection_id)
            
            self.logger.info(f"Attached VPN {vpn_connection_id} to Transit Gateway")
            
            return {
                'vpn_connection_id': vpn_connection_id,
                'transit_gateway_id': transit_gateway_id,
                'customer_gateway_id': config.customer_gateway_id,
                'static_routes_only': config.static_routes_only,
                'status': 'attached'
            }
            
        except ClientError as e:
            self.logger.error(f"Error attaching VPN: {str(e)}")
            raise

    def attach_direct_connect_gateway(self, transit_gateway_id: str, 
                                    config: DirectConnectAttachmentConfig) -> Dict[str, Any]:
        """Attach Direct Connect Gateway to Transit Gateway"""
        try:
            response = self.ec2.create_transit_gateway_direct_connect_gateway_attachment(
                TransitGatewayId=transit_gateway_id,
                DirectConnectGatewayId=config.direct_connect_gateway_id,
                TagSpecifications=[
                    {
                        'ResourceType': 'transit-gateway-attachment',
                        'Tags': [
                            {'Key': k, 'Value': v} 
                            for k, v in config.tags.items()
                        ]
                    }
                ]
            )
            
            attachment_id = response['TransitGatewayDirectConnectGatewayAttachment']['TransitGatewayAttachmentId']
            
            # Wait for attachment to become available
            self._wait_for_attachment_available(attachment_id)
            
            self.logger.info(f"Attached Direct Connect Gateway to Transit Gateway: {attachment_id}")
            
            return {
                'attachment_id': attachment_id,
                'transit_gateway_id': transit_gateway_id,
                'direct_connect_gateway_id': config.direct_connect_gateway_id,
                'state': response['TransitGatewayDirectConnectGatewayAttachment']['State'],
                'status': 'attached'
            }
            
        except ClientError as e:
            self.logger.error(f"Error attaching Direct Connect Gateway: {str(e)}")
            raise

    def create_peering_connection(self, transit_gateway_id: str, 
                                config: PeeringAttachmentConfig) -> Dict[str, Any]:
        """Create Transit Gateway peering connection for inter-region connectivity"""
        try:
            response = self.ec2.create_transit_gateway_peering_attachment(
                TransitGatewayId=transit_gateway_id,
                PeerTransitGatewayId=config.peer_transit_gateway_id,
                PeerAccountId=config.peer_account_id,
                PeerRegion=config.peer_region,
                TagSpecifications=[
                    {
                        'ResourceType': 'transit-gateway-attachment',
                        'Tags': [
                            {'Key': k, 'Value': v} 
                            for k, v in config.tags.items()
                        ]
                    }
                ]
            )
            
            attachment_id = response['TransitGatewayPeeringAttachment']['TransitGatewayAttachmentId']
            
            self.logger.info(f"Created peering connection: {attachment_id}")
            
            return {
                'attachment_id': attachment_id,
                'transit_gateway_id': transit_gateway_id,
                'peer_transit_gateway_id': config.peer_transit_gateway_id,
                'peer_account_id': config.peer_account_id,
                'peer_region': config.peer_region,
                'state': response['TransitGatewayPeeringAttachment']['State'],
                'status': 'created'
            }
            
        except ClientError as e:
            self.logger.error(f"Error creating peering connection: {str(e)}")
            raise

    def create_route_table(self, transit_gateway_id: str, 
                          description: str, tags: Dict[str, str] = None) -> Dict[str, Any]:
        """Create Transit Gateway route table"""
        try:
            response = self.ec2.create_transit_gateway_route_table(
                TransitGatewayId=transit_gateway_id,
                TagSpecifications=[
                    {
                        'ResourceType': 'transit-gateway-route-table',
                        'Tags': [
                            {'Key': 'Description', 'Value': description},
                            *[{'Key': k, 'Value': v} for k, v in (tags or {}).items()]
                        ]
                    }
                ]
            )
            
            route_table_id = response['TransitGatewayRouteTable']['TransitGatewayRouteTableId']
            
            # Wait for route table to become available
            self._wait_for_route_table_available(route_table_id)
            
            self.logger.info(f"Created Transit Gateway route table: {route_table_id}")
            
            return {
                'route_table_id': route_table_id,
                'transit_gateway_id': transit_gateway_id,
                'state': response['TransitGatewayRouteTable']['State'],
                'description': description,
                'status': 'created'
            }
            
        except ClientError as e:
            self.logger.error(f"Error creating route table: {str(e)}")
            raise

    def create_routes(self, route_table_id: str, routes: List[RouteTableEntry]) -> Dict[str, Any]:
        """Create multiple routes in Transit Gateway route table"""
        try:
            created_routes = []
            failed_routes = []
            
            for route in routes:
                try:
                    response = self.ec2.create_transit_gateway_route(
                        DestinationCidrBlock=route.destination_cidr,
                        TransitGatewayRouteTableId=route_table_id,
                        TransitGatewayAttachmentId=route.target_attachment_id,
                        Blackhole=route.state == RouteState.BLACKHOLE
                    )
                    
                    created_routes.append({
                        'destination_cidr': route.destination_cidr,
                        'target_attachment_id': route.target_attachment_id,
                        'state': response['Route']['State'],
                        'type': response['Route']['Type']
                    })
                    
                except ClientError as route_error:
                    self.logger.warning(f"Failed to create route {route.destination_cidr}: {str(route_error)}")
                    failed_routes.append({
                        'destination_cidr': route.destination_cidr,
                        'error': str(route_error)
                    })
            
            self.logger.info(f"Created {len(created_routes)} routes, failed {len(failed_routes)} routes")
            
            return {
                'route_table_id': route_table_id,
                'created_routes': created_routes,
                'failed_routes': failed_routes,
                'total_routes': len(routes),
                'success_rate': len(created_routes) / len(routes) * 100
            }
            
        except Exception as e:
            self.logger.error(f"Error creating routes: {str(e)}")
            raise

    def associate_route_table(self, route_table_id: str, attachment_id: str) -> Dict[str, Any]:
        """Associate attachment with route table"""
        try:
            response = self.ec2.associate_transit_gateway_route_table(
                TransitGatewayAttachmentId=attachment_id,
                TransitGatewayRouteTableId=route_table_id
            )
            
            self.logger.info(f"Associated attachment {attachment_id} with route table {route_table_id}")
            
            return {
                'route_table_id': route_table_id,
                'attachment_id': attachment_id,
                'association_state': response['Association']['State'],
                'status': 'associated'
            }
            
        except ClientError as e:
            self.logger.error(f"Error associating route table: {str(e)}")
            raise

    def enable_route_propagation(self, route_table_id: str, attachment_id: str) -> Dict[str, Any]:
        """Enable route propagation for attachment"""
        try:
            response = self.ec2.enable_transit_gateway_route_table_propagation(
                TransitGatewayRouteTableId=route_table_id,
                TransitGatewayAttachmentId=attachment_id
            )
            
            self.logger.info(f"Enabled propagation for attachment {attachment_id}")
            
            return {
                'route_table_id': route_table_id,
                'attachment_id': attachment_id,
                'propagation_state': response['Propagation']['State'],
                'status': 'enabled'
            }
            
        except ClientError as e:
            self.logger.error(f"Error enabling route propagation: {str(e)}")
            raise

    def share_transit_gateway(self, transit_gateway_id: str, 
                            principal_accounts: List[str], 
                            share_name: str) -> Dict[str, Any]:
        """Share Transit Gateway with other AWS accounts using RAM"""
        try:
            # Create resource share
            response = self.ram.create_resource_share(
                name=share_name,
                resourceArns=[
                    f"arn:aws:ec2:{self.region}:{self._get_account_id()}:transit-gateway/{transit_gateway_id}"
                ],
                principals=principal_accounts,
                allowExternalPrincipals=True,
                tags=[
                    {'key': 'Purpose', 'value': 'TransitGatewaySharing'},
                    {'key': 'ManagedBy', 'value': 'EnterpriseTransitGatewayManager'}
                ]
            )
            
            share_arn = response['resourceShare']['resourceShareArn']
            
            self.logger.info(f"Shared Transit Gateway {transit_gateway_id} with accounts: {principal_accounts}")
            
            return {
                'resource_share_arn': share_arn,
                'transit_gateway_id': transit_gateway_id,
                'principal_accounts': principal_accounts,
                'share_name': share_name,
                'status': 'shared'
            }
            
        except ClientError as e:
            self.logger.error(f"Error sharing Transit Gateway: {str(e)}")
            raise

    def monitor_transit_gateway_metrics(self, transit_gateway_id: str, 
                                      period_hours: int = 24) -> Dict[str, Any]:
        """Monitor Transit Gateway performance metrics"""
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=period_hours)
            
            metrics_data = {}
            
            # Get bytes in/out metrics
            for metric_name in ['BytesIn', 'BytesOut', 'PacketsIn', 'PacketsOut']:
                try:
                    response = self.cloudwatch.get_metric_statistics(
                        Namespace='AWS/TransitGateway',
                        MetricName=metric_name,
                        Dimensions=[
                            {
                                'Name': 'TransitGateway',
                                'Value': transit_gateway_id
                            }
                        ],
                        StartTime=start_time,
                        EndTime=end_time,
                        Period=3600,
                        Statistics=['Sum', 'Average', 'Maximum']
                    )
                    
                    datapoints = response.get('Datapoints', [])
                    if datapoints:
                        metrics_data[metric_name] = {
                            'total': sum(point['Sum'] for point in datapoints),
                            'average': sum(point['Average'] for point in datapoints) / len(datapoints),
                            'peak': max(point['Maximum'] for point in datapoints)
                        }
                    
                except Exception as metric_error:
                    self.logger.warning(f"Could not retrieve {metric_name}: {str(metric_error)}")
                    metrics_data[metric_name] = {'error': str(metric_error)}
            
            return {
                'transit_gateway_id': transit_gateway_id,
                'monitoring_period_hours': period_hours,
                'metrics': metrics_data,
                'report_timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error monitoring Transit Gateway metrics: {str(e)}")
            raise

    def get_network_topology(self, transit_gateway_id: str) -> Dict[str, Any]:
        """Get comprehensive network topology for Transit Gateway"""
        try:
            # Get Transit Gateway details
            tgw_response = self.ec2.describe_transit_gateways(
                TransitGatewayIds=[transit_gateway_id]
            )
            
            # Get all attachments
            attachments_response = self.ec2.describe_transit_gateway_attachments(
                Filters=[
                    {
                        'Name': 'transit-gateway-id',
                        'Values': [transit_gateway_id]
                    }
                ]
            )
            
            # Get route tables
            route_tables_response = self.ec2.describe_transit_gateway_route_tables(
                Filters=[
                    {
                        'Name': 'transit-gateway-id',
                        'Values': [transit_gateway_id]
                    }
                ]
            )
            
            # Process attachments by type
            attachments_by_type = {}
            for attachment in attachments_response['TransitGatewayAttachments']:
                attachment_type = attachment['ResourceType']
                if attachment_type not in attachments_by_type:
                    attachments_by_type[attachment_type] = []
                
                attachments_by_type[attachment_type].append({
                    'attachment_id': attachment['TransitGatewayAttachmentId'],
                    'resource_id': attachment['ResourceId'],
                    'state': attachment['State'],
                    'tags': attachment.get('Tags', [])
                })
            
            # Process route tables
            route_tables_info = []
            for rt in route_tables_response['TransitGatewayRouteTables']:
                # Get routes for this route table
                routes_response = self.ec2.search_transit_gateway_routes(
                    TransitGatewayRouteTableId=rt['TransitGatewayRouteTableId'],
                    Filters=[
                        {
                            'Name': 'state',
                            'Values': ['active', 'blackhole']
                        }
                    ]
                )
                
                route_tables_info.append({
                    'route_table_id': rt['TransitGatewayRouteTableId'],
                    'state': rt['State'],
                    'default_association_route_table': rt.get('DefaultAssociationRouteTable', False),
                    'default_propagation_route_table': rt.get('DefaultPropagationRouteTable', False),
                    'routes': [
                        {
                            'destination_cidr': route['DestinationCidrBlock'],
                            'state': route['State'],
                            'route_origin': route['Origin'],
                            'attachment_id': route.get('TransitGatewayAttachments', [{}])[0].get('TransitGatewayAttachmentId')
                        }
                        for route in routes_response.get('Routes', [])
                    ]
                })
            
            topology = {
                'transit_gateway': {
                    'id': transit_gateway_id,
                    'state': tgw_response['TransitGateways'][0]['State'],
                    'owner_id': tgw_response['TransitGateways'][0]['OwnerId'],
                    'description': tgw_response['TransitGateways'][0].get('Description', ''),
                    'amazon_side_asn': tgw_response['TransitGateways'][0]['Options']['AmazonSideAsn']
                },
                'attachments': attachments_by_type,
                'route_tables': route_tables_info,
                'summary': {
                    'total_attachments': len(attachments_response['TransitGatewayAttachments']),
                    'total_route_tables': len(route_tables_response['TransitGatewayRouteTables']),
                    'attachment_types': list(attachments_by_type.keys())
                },
                'topology_generated': datetime.utcnow().isoformat()
            }
            
            return topology
            
        except Exception as e:
            self.logger.error(f"Error getting network topology: {str(e)}")
            raise

    def _wait_for_transit_gateway_available(self, transit_gateway_id: str, timeout: int = 600) -> None:
        """Wait for Transit Gateway to become available"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = self.ec2.describe_transit_gateways(
                    TransitGatewayIds=[transit_gateway_id]
                )
                state = response['TransitGateways'][0]['State']
                if state == 'available':
                    return
                elif state in ['deleted', 'deleting', 'failed']:
                    raise Exception(f"Transit Gateway {transit_gateway_id} is in {state} state")
                time.sleep(30)
            except ClientError as e:
                if e.response['Error']['Code'] != 'InvalidTransitGatewayID.NotFound':
                    raise
                time.sleep(30)
        raise Exception(f"Timeout waiting for Transit Gateway {transit_gateway_id} to become available")

    def _wait_for_attachment_available(self, attachment_id: str, timeout: int = 600) -> None:
        """Wait for attachment to become available"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = self.ec2.describe_transit_gateway_attachments(
                    TransitGatewayAttachmentIds=[attachment_id]
                )
                state = response['TransitGatewayAttachments'][0]['State']
                if state == 'available':
                    return
                elif state in ['deleted', 'deleting', 'failed']:
                    raise Exception(f"Attachment {attachment_id} is in {state} state")
                time.sleep(30)
            except ClientError as e:
                if e.response['Error']['Code'] != 'InvalidTransitGatewayAttachmentID.NotFound':
                    raise
                time.sleep(30)
        raise Exception(f"Timeout waiting for attachment {attachment_id} to become available")

    def _wait_for_route_table_available(self, route_table_id: str, timeout: int = 300) -> None:
        """Wait for route table to become available"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = self.ec2.describe_transit_gateway_route_tables(
                    TransitGatewayRouteTableIds=[route_table_id]
                )
                state = response['TransitGatewayRouteTables'][0]['State']
                if state == 'available':
                    return
                elif state in ['deleted', 'deleting', 'failed']:
                    raise Exception(f"Route table {route_table_id} is in {state} state")
                time.sleep(15)
            except ClientError as e:
                if e.response['Error']['Code'] != 'InvalidRouteTableID.NotFound':
                    raise
                time.sleep(15)
        raise Exception(f"Timeout waiting for route table {route_table_id} to become available")

    def _wait_for_vpn_available(self, vpn_connection_id: str, timeout: int = 600) -> None:
        """Wait for VPN connection to become available"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = self.ec2.describe_vpn_connections(
                    VpnConnectionIds=[vpn_connection_id]
                )
                state = response['VpnConnections'][0]['State']
                if state == 'available':
                    return
                elif state in ['deleted', 'deleting', 'failed']:
                    raise Exception(f"VPN connection {vpn_connection_id} is in {state} state")
                time.sleep(30)
            except ClientError as e:
                if e.response['Error']['Code'] != 'InvalidVpnConnectionID.NotFound':
                    raise
                time.sleep(30)
        raise Exception(f"Timeout waiting for VPN connection {vpn_connection_id} to become available")

    def _get_account_id(self) -> str:
        """Get current AWS account ID"""
        try:
            sts = boto3.client('sts')
            return sts.get_caller_identity()['Account']
        except Exception:
            return "123456789012"  # Fallback for examples

# Practical Real-World Examples

def create_enterprise_hub_spoke_architecture():
    """Create enterprise hub-and-spoke network architecture"""
    
    manager = EnterpriseTransitGatewayManager()
    
    # Create central Transit Gateway
    tgw_config = TransitGatewayConfig(
        description="Enterprise Hub Transit Gateway",
        amazon_side_asn=64512,
        auto_accept_shared_attachments="enable",
        auto_cross_account_attachment="enable",
        dns_support="enable",
        vpn_ecmp_support="enable",
        tags={
            'Environment': 'Production',
            'Purpose': 'CentralHub',
            'CostCenter': 'Infrastructure',
            'ManagedBy': 'NetworkTeam'
        }
    )
    
    tgw_result = manager.create_transit_gateway(tgw_config)
    transit_gateway_id = tgw_result['transit_gateway_id']
    print(f"Created Transit Gateway: {transit_gateway_id}")
    
    # Create segmented route tables
    production_rt = manager.create_route_table(
        transit_gateway_id,
        "Production Environment Route Table",
        {'Environment': 'Production', 'Tier': 'Isolated'}
    )
    
    staging_rt = manager.create_route_table(
        transit_gateway_id,
        "Staging Environment Route Table", 
        {'Environment': 'Staging', 'Tier': 'Development'}
    )
    
    shared_services_rt = manager.create_route_table(
        transit_gateway_id,
        "Shared Services Route Table",
        {'Environment': 'Shared', 'Tier': 'Services'}
    )
    
    # Attach production VPCs
    prod_vpc_configs = [
        VPCAttachmentConfig(
            vpc_id="vpc-prod-web-12345",
            subnet_ids=["subnet-prod-web-1", "subnet-prod-web-2"],
            route_table_id=production_rt['route_table_id'],
            tags={'Tier': 'Web', 'Environment': 'Production'}
        ),
        VPCAttachmentConfig(
            vpc_id="vpc-prod-app-67890",
            subnet_ids=["subnet-prod-app-1", "subnet-prod-app-2"],
            route_table_id=production_rt['route_table_id'],
            tags={'Tier': 'Application', 'Environment': 'Production'}
        ),
        VPCAttachmentConfig(
            vpc_id="vpc-prod-db-11111",
            subnet_ids=["subnet-prod-db-1", "subnet-prod-db-2"],
            route_table_id=production_rt['route_table_id'],
            tags={'Tier': 'Database', 'Environment': 'Production'}
        )
    ]
    
    prod_attachments = []
    for vpc_config in prod_vpc_configs:
        attachment = manager.attach_vpc(transit_gateway_id, vpc_config)
        prod_attachments.append(attachment)
    
    # Attach shared services VPC
    shared_services_config = VPCAttachmentConfig(
        vpc_id="vpc-shared-services-22222",
        subnet_ids=["subnet-shared-1", "subnet-shared-2"],
        route_table_id=shared_services_rt['route_table_id'],
        tags={'Tier': 'SharedServices', 'Purpose': 'DNS-AD-Monitoring'}
    )
    
    shared_attachment = manager.attach_vpc(transit_gateway_id, shared_services_config)
    
    # Attach on-premises via VPN
    vpn_config = VPNAttachmentConfig(
        customer_gateway_id="cgw-onprem-33333",
        static_routes_only=False,
        tags={'Purpose': 'OnPremisesConnectivity', 'Location': 'DataCenter'}
    )
    
    vpn_attachment = manager.attach_vpn(transit_gateway_id, vpn_config)
    
    return {
        'transit_gateway': tgw_result,
        'route_tables': {
            'production': production_rt,
            'staging': staging_rt,
            'shared_services': shared_services_rt
        },
        'attachments': {
            'production_vpcs': prod_attachments,
            'shared_services': shared_attachment,
            'vpn_connection': vpn_attachment
        }
    }

def create_multi_region_transit_network():
    """Create multi-region Transit Gateway network with peering"""
    
    # Primary region manager
    primary_manager = EnterpriseTransitGatewayManager(region='us-east-1')
    secondary_manager = EnterpriseTransitGatewayManager(region='us-west-2')
    
    # Create Transit Gateways in both regions
    primary_tgw_config = TransitGatewayConfig(
        description="Primary Region Transit Gateway",
        amazon_side_asn=64512,
        tags={
            'Region': 'Primary',
            'Environment': 'Production',
            'Purpose': 'MultiRegionHub'
        }
    )
    
    secondary_tgw_config = TransitGatewayConfig(
        description="Secondary Region Transit Gateway",
        amazon_side_asn=64513,
        tags={
            'Region': 'Secondary', 
            'Environment': 'Production',
            'Purpose': 'DisasterRecovery'
        }
    )
    
    primary_tgw = primary_manager.create_transit_gateway(primary_tgw_config)
    secondary_tgw = secondary_manager.create_transit_gateway(secondary_tgw_config)
    
    # Create inter-region peering
    peering_config = PeeringAttachmentConfig(
        peer_transit_gateway_id=secondary_tgw['transit_gateway_id'],
        peer_account_id=primary_manager._get_account_id(),
        peer_region='us-west-2',
        tags={'Purpose': 'InterRegionConnectivity', 'Type': 'DisasterRecovery'}
    )
    
    peering_attachment = primary_manager.create_peering_connection(
        primary_tgw['transit_gateway_id'], peering_config
    )
    
    # Accept peering in secondary region
    secondary_manager.ec2.accept_transit_gateway_peering_attachment(
        TransitGatewayAttachmentId=peering_attachment['attachment_id']
    )
    
    # Create cross-region routes
    primary_rt = primary_manager.create_route_table(
        primary_tgw['transit_gateway_id'],
        "Cross Region Route Table"
    )
    
    secondary_rt = secondary_manager.create_route_table(
        secondary_tgw['transit_gateway_id'],
        "Cross Region Route Table"
    )
    
    # Add routes for disaster recovery traffic
    dr_routes = [
        RouteTableEntry(
            destination_cidr="10.1.0.0/16",  # Secondary region CIDR
            target_attachment_id=peering_attachment['attachment_id']
        )
    ]
    
    primary_manager.create_routes(primary_rt['route_table_id'], dr_routes)
    
    return {
        'primary_region': {
            'transit_gateway': primary_tgw,
            'route_table': primary_rt
        },
        'secondary_region': {
            'transit_gateway': secondary_tgw,
            'route_table': secondary_rt
        },
        'inter_region_peering': peering_attachment
    }

def create_shared_services_architecture():
    """Create shared services architecture with Transit Gateway"""
    
    manager = EnterpriseTransitGatewayManager()
    
    # Create Transit Gateway for shared services
    shared_tgw_config = TransitGatewayConfig(
        description="Shared Services Transit Gateway",
        amazon_side_asn=64514,
        auto_accept_shared_attachments="enable",
        tags={
            'Purpose': 'SharedServices',
            'Environment': 'Production',
            'Service': 'DNS-AD-Monitoring-Security'
        }
    )
    
    shared_tgw = manager.create_transit_gateway(shared_tgw_config)
    transit_gateway_id = shared_tgw['transit_gateway_id']
    
    # Share Transit Gateway with multiple accounts
    shared_accounts = [
        "111111111111",  # Development account
        "222222222222",  # Staging account  
        "333333333333",  # Production account
        "444444444444"   # Security account
    ]
    
    sharing_result = manager.share_transit_gateway(
        transit_gateway_id,
        shared_accounts,
        "SharedServicesTransitGateway"
    )
    
    # Create segregated route tables for different environments
    environment_route_tables = {}
    environments = ['Development', 'Staging', 'Production', 'Security']
    
    for env in environments:
        rt = manager.create_route_table(
            transit_gateway_id,
            f"{env} Environment Route Table",
            {
                'Environment': env,
                'Purpose': 'EnvironmentSegmentation',
                'AccessLevel': 'Restricted' if env in ['Production', 'Security'] else 'Standard'
            }
        )
        environment_route_tables[env.lower()] = rt
    
    # Attach shared services VPCs
    shared_services_vpcs = [
        VPCAttachmentConfig(
            vpc_id="vpc-shared-dns-12345",
            subnet_ids=["subnet-dns-1", "subnet-dns-2"],
            tags={'Service': 'DNS', 'Tier': 'Infrastructure'}
        ),
        VPCAttachmentConfig(
            vpc_id="vpc-shared-ad-67890",
            subnet_ids=["subnet-ad-1", "subnet-ad-2"],
            tags={'Service': 'ActiveDirectory', 'Tier': 'Infrastructure'}
        ),
        VPCAttachmentConfig(
            vpc_id="vpc-shared-monitor-11111",
            subnet_ids=["subnet-monitor-1", "subnet-monitor-2"],
            tags={'Service': 'Monitoring', 'Tier': 'Infrastructure'}
        )
    ]
    
    shared_attachments = []
    for vpc_config in shared_services_vpcs:
        attachment = manager.attach_vpc(transit_gateway_id, vpc_config)
        shared_attachments.append(attachment)
        
        # Associate shared services with all environment route tables
        for rt_info in environment_route_tables.values():
            manager.associate_route_table(rt_info['route_table_id'], attachment['attachment_id'])
    
    return {
        'shared_transit_gateway': shared_tgw,
        'resource_sharing': sharing_result,
        'environment_route_tables': environment_route_tables,
        'shared_services_attachments': shared_attachments,
        'shared_accounts': shared_accounts
    }
```

## DevOps Integration Patterns

### Infrastructure as Code (Terraform)

```hcl
# transit_gateway_infrastructure.tf
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# Central Transit Gateway
resource "aws_ec2_transit_gateway" "enterprise_hub" {
  description                     = "Enterprise Hub Transit Gateway"
  amazon_side_asn                = var.amazon_side_asn
  auto_accept_shared_attachments = "enable"
  default_route_table_association = "disable"  # Custom route tables
  default_route_table_propagation = "disable"  # Controlled propagation
  dns_support                    = "enable"
  vpn_ecmp_support              = "enable"
  
  tags = {
    Name        = "enterprise-hub-tgw"
    Environment = var.environment
    Purpose     = "CentralNetworkHub"
    ManagedBy   = "Terraform"
  }
}

# Production Environment Route Table
resource "aws_ec2_transit_gateway_route_table" "production" {
  transit_gateway_id = aws_ec2_transit_gateway.enterprise_hub.id
  
  tags = {
    Name        = "production-route-table"
    Environment = "Production"
    Tier        = "Isolated"
  }
}

# Staging Environment Route Table
resource "aws_ec2_transit_gateway_route_table" "staging" {
  transit_gateway_id = aws_ec2_transit_gateway.enterprise_hub.id
  
  tags = {
    Name        = "staging-route-table"
    Environment = "Staging"
    Tier        = "Development"
  }
}

# Shared Services Route Table
resource "aws_ec2_transit_gateway_route_table" "shared_services" {
  transit_gateway_id = aws_ec2_transit_gateway.enterprise_hub.id
  
  tags = {
    Name        = "shared-services-route-table"
    Environment = "Shared"
    Tier        = "Services"
  }
}

# VPC Attachments for Production
resource "aws_ec2_transit_gateway_vpc_attachment" "production_web" {
  subnet_ids         = var.production_web_subnet_ids
  transit_gateway_id = aws_ec2_transit_gateway.enterprise_hub.id
  vpc_id            = var.production_web_vpc_id
  
  dns_support                    = "enable"
  ipv6_support                  = "disable"
  appliance_mode_support        = "disable"
  
  tags = {
    Name        = "production-web-attachment"
    Environment = "Production"
    Tier        = "Web"
  }
}

resource "aws_ec2_transit_gateway_vpc_attachment" "production_app" {
  subnet_ids         = var.production_app_subnet_ids
  transit_gateway_id = aws_ec2_transit_gateway.enterprise_hub.id
  vpc_id            = var.production_app_vpc_id
  
  dns_support                    = "enable"
  ipv6_support                  = "disable"
  appliance_mode_support        = "disable"
  
  tags = {
    Name        = "production-app-attachment"
    Environment = "Production"
    Tier        = "Application"
  }
}

# Shared Services VPC Attachment
resource "aws_ec2_transit_gateway_vpc_attachment" "shared_services" {
  subnet_ids         = var.shared_services_subnet_ids
  transit_gateway_id = aws_ec2_transit_gateway.enterprise_hub.id
  vpc_id            = var.shared_services_vpc_id
  
  dns_support                    = "enable"
  ipv6_support                  = "disable"
  
  tags = {
    Name        = "shared-services-attachment"
    Environment = "Shared"
    Tier        = "Services"
  }
}

# Route Table Associations
resource "aws_ec2_transit_gateway_route_table_association" "production_web" {
  transit_gateway_attachment_id  = aws_ec2_transit_gateway_vpc_attachment.production_web.id
  transit_gateway_route_table_id = aws_ec2_transit_gateway_route_table.production.id
}

resource "aws_ec2_transit_gateway_route_table_association" "production_app" {
  transit_gateway_attachment_id  = aws_ec2_transit_gateway_vpc_attachment.production_app.id
  transit_gateway_route_table_id = aws_ec2_transit_gateway_route_table.production.id
}

resource "aws_ec2_transit_gateway_route_table_association" "shared_services" {
  transit_gateway_attachment_id  = aws_ec2_transit_gateway_vpc_attachment.shared_services.id
  transit_gateway_route_table_id = aws_ec2_transit_gateway_route_table.shared_services.id
}

# Cross-Environment Routes (Production to Shared Services)
resource "aws_ec2_transit_gateway_route" "production_to_shared_dns" {
  destination_cidr_block         = "10.100.0.0/16"  # DNS VPC CIDR
  transit_gateway_attachment_id  = aws_ec2_transit_gateway_vpc_attachment.shared_services.id
  transit_gateway_route_table_id = aws_ec2_transit_gateway_route_table.production.id
}

resource "aws_ec2_transit_gateway_route" "shared_to_production" {
  destination_cidr_block         = "10.0.0.0/8"     # Production CIDR range
  transit_gateway_attachment_id  = aws_ec2_transit_gateway_vpc_attachment.production_web.id
  transit_gateway_route_table_id = aws_ec2_transit_gateway_route_table.shared_services.id
}

# VPN Connection for On-Premises
resource "aws_customer_gateway" "onpremises" {
  bgp_asn    = var.onpremises_bgp_asn
  ip_address = var.onpremises_public_ip
  type       = "ipsec.1"
  
  tags = {
    Name = "onpremises-customer-gateway"
  }
}

resource "aws_vpn_connection" "onpremises" {
  customer_gateway_id = aws_customer_gateway.onpremises.id
  type               = "ipsec.1"
  transit_gateway_id = aws_ec2_transit_gateway.enterprise_hub.id
  static_routes_only = false
  
  tags = {
    Name = "onpremises-vpn-connection"
  }
}

# Inter-Region Peering for Disaster Recovery
resource "aws_ec2_transit_gateway_peering_attachment" "dr_region" {
  count = var.enable_disaster_recovery ? 1 : 0
  
  peer_account_id         = data.aws_caller_identity.current.account_id
  peer_region            = var.disaster_recovery_region
  peer_transit_gateway_id = var.dr_transit_gateway_id
  transit_gateway_id     = aws_ec2_transit_gateway.enterprise_hub.id
  
  tags = {
    Name = "disaster-recovery-peering"
    Type = "InterRegion"
  }
}

# RAM Resource Share for Cross-Account Access
resource "aws_ram_resource_share" "transit_gateway" {
  name                      = "transit-gateway-share"
  allow_external_principals = true
  
  tags = {
    Environment = var.environment
    Purpose     = "CrossAccountNetworking"
  }
}

resource "aws_ram_resource_association" "transit_gateway" {
  resource_arn       = aws_ec2_transit_gateway.enterprise_hub.arn
  resource_share_arn = aws_ram_resource_share.transit_gateway.arn
}

resource "aws_ram_principal_association" "cross_account" {
  for_each = toset(var.shared_account_ids)
  
  principal          = each.value
  resource_share_arn = aws_ram_resource_share.transit_gateway.arn
}

# CloudWatch Alarms for Monitoring
resource "aws_cloudwatch_metric_alarm" "bytes_in_high" {
  alarm_name          = "tgw-high-bytes-in"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "BytesIn"
  namespace           = "AWS/TransitGateway"
  period             = "300"
  statistic          = "Sum"
  threshold          = var.bytes_in_threshold
  alarm_description  = "This metric monitors high inbound traffic on Transit Gateway"
  alarm_actions      = [var.sns_alert_topic_arn]
  
  dimensions = {
    TransitGateway = aws_ec2_transit_gateway.enterprise_hub.id
  }
  
  tags = {
    Environment = var.environment
    Purpose     = "NetworkMonitoring"
  }
}

resource "aws_cloudwatch_metric_alarm" "attachment_count" {
  alarm_name          = "tgw-attachment-count-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "AttachmentCount"
  namespace           = "AWS/TransitGateway"
  period             = "300"
  statistic          = "Maximum"
  threshold          = var.max_attachments_threshold
  alarm_description  = "This metric monitors Transit Gateway attachment count"
  alarm_actions      = [var.sns_alert_topic_arn]
  
  dimensions = {
    TransitGateway = aws_ec2_transit_gateway.enterprise_hub.id
  }
}

# Data source for current AWS account
data "aws_caller_identity" "current" {}

# Variables
variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "amazon_side_asn" {
  description = "Private ASN for the Amazon side of the Transit Gateway"
  type        = number
  default     = 64512
}

variable "production_web_vpc_id" {
  description = "Production web tier VPC ID"
  type        = string
}

variable "production_web_subnet_ids" {
  description = "Production web tier subnet IDs"
  type        = list(string)
}

variable "production_app_vpc_id" {
  description = "Production application tier VPC ID"
  type        = string
}

variable "production_app_subnet_ids" {
  description = "Production application tier subnet IDs"
  type        = list(string)
}

variable "shared_services_vpc_id" {
  description = "Shared services VPC ID"
  type        = string
}

variable "shared_services_subnet_ids" {
  description = "Shared services subnet IDs"
  type        = list(string)
}

variable "shared_account_ids" {
  description = "List of AWS account IDs to share Transit Gateway with"
  type        = list(string)
  default     = []
}

variable "onpremises_bgp_asn" {
  description = "BGP ASN of on-premises customer gateway"
  type        = number
  default     = 65000
}

variable "onpremises_public_ip" {
  description = "Public IP of on-premises VPN endpoint"
  type        = string
}

variable "enable_disaster_recovery" {
  description = "Enable disaster recovery peering"
  type        = bool
  default     = false
}

variable "disaster_recovery_region" {
  description = "Disaster recovery region"
  type        = string
  default     = "us-west-2"
}

variable "dr_transit_gateway_id" {
  description = "Disaster recovery Transit Gateway ID"
  type        = string
  default     = ""
}

variable "sns_alert_topic_arn" {
  description = "SNS topic ARN for alerts"
  type        = string
}

variable "bytes_in_threshold" {
  description = "Threshold for BytesIn alarm (bytes)"
  type        = number
  default     = 10000000000  # 10 GB
}

variable "max_attachments_threshold" {
  description = "Maximum number of attachments threshold"
  type        = number
  default     = 100
}

# Outputs
output "transit_gateway_id" {
  description = "Transit Gateway ID"
  value       = aws_ec2_transit_gateway.enterprise_hub.id
}

output "transit_gateway_arn" {
  description = "Transit Gateway ARN"
  value       = aws_ec2_transit_gateway.enterprise_hub.arn
}

output "production_route_table_id" {
  description = "Production route table ID"
  value       = aws_ec2_transit_gateway_route_table.production.id
}

output "shared_services_route_table_id" {
  description = "Shared services route table ID"
  value       = aws_ec2_transit_gateway_route_table.shared_services.id
}

output "resource_share_arn" {
  description = "RAM resource share ARN"
  value       = aws_ram_resource_share.transit_gateway.arn
}

output "vpc_attachments" {
  description = "VPC attachment IDs"
  value = {
    production_web    = aws_ec2_transit_gateway_vpc_attachment.production_web.id
    production_app    = aws_ec2_transit_gateway_vpc_attachment.production_app.id
    shared_services   = aws_ec2_transit_gateway_vpc_attachment.shared_services.id
  }
}
```

### CI/CD Pipeline Integration

```yaml
# .github/workflows/transit-gateway-deployment.yml
name: Transit Gateway Network Deployment

on:
  push:
    branches: [main]
    paths: ['network/transit-gateway/**']
  workflow_dispatch:
    inputs:
      action:
        description: 'Deployment action'
        required: true
        type: choice
        options:
          - deploy
          - plan
          - destroy
          - test_connectivity
      environment:
        description: 'Target environment'
        required: true
        type: choice
        options:
          - development
          - staging
          - production

jobs:
  network-validation:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    
    - name: Install Dependencies
      run: |
        pip install boto3 netaddr ipaddress
    
    - name: Validate Network Design
      run: |
        python scripts/validate_network_design.py \
          --config network/transit-gateway/config.json \
          --environment ${{ github.event.inputs.environment || 'development' }}
    
    - name: Check CIDR Conflicts
      run: |
        python scripts/check_cidr_conflicts.py \
          --vpc-config network/vpc-configurations.json \
          --on-premises-cidrs network/onprem-cidrs.json

  terraform-plan:
    needs: network-validation
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup Terraform
      uses: hashicorp/setup-terraform@v2
      with:
        terraform_version: 1.5.0
    
    - name: Configure AWS credentials
      uses: aws-actions/configure-aws-credentials@v2
      with:
        role-to-assume: ${{ secrets.AWS_TGW_ROLE }}
        aws-region: us-east-1
    
    - name: Terraform Init
      run: |
        cd network/transit-gateway
        terraform init -backend-config="bucket=${{ secrets.TF_STATE_BUCKET }}"
    
    - name: Terraform Plan
      run: |
        cd network/transit-gateway
        terraform plan \
          -var-file="environments/${{ github.event.inputs.environment || 'development' }}.tfvars" \
          -out=tfplan
    
    - name: Upload Terraform Plan
      uses: actions/upload-artifact@v3
      with:
        name: terraform-plan
        path: network/transit-gateway/tfplan

  terraform-apply:
    needs: terraform-plan
    runs-on: ubuntu-latest
    if: github.event.inputs.action == 'deploy' || github.event.inputs.action == ''
    environment: ${{ github.event.inputs.environment || 'development' }}
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup Terraform
      uses: hashicorp/setup-terraform@v2
      with:
        terraform_version: 1.5.0
    
    - name: Configure AWS credentials
      uses: aws-actions/configure-aws-credentials@v2
      with:
        role-to-assume: ${{ secrets.AWS_TGW_ROLE }}
        aws-region: us-east-1
    
    - name: Download Terraform Plan
      uses: actions/download-artifact@v3
      with:
        name: terraform-plan
        path: network/transit-gateway/
    
    - name: Terraform Init
      run: |
        cd network/transit-gateway
        terraform init -backend-config="bucket=${{ secrets.TF_STATE_BUCKET }}"
    
    - name: Terraform Apply
      run: |
        cd network/transit-gateway
        terraform apply -auto-approve tfplan
    
    - name: Extract Outputs
      run: |
        cd network/transit-gateway
        terraform output -json > terraform-outputs.json
    
    - name: Upload Terraform Outputs
      uses: actions/upload-artifact@v3
      with:
        name: terraform-outputs
        path: network/transit-gateway/terraform-outputs.json

  network-testing:
    needs: terraform-apply
    runs-on: ubuntu-latest
    if: github.event.inputs.action == 'test_connectivity' || github.event.inputs.action == 'deploy'
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    
    - name: Install Dependencies
      run: |
        pip install boto3 paramiko ping3
    
    - name: Configure AWS credentials
      uses: aws-actions/configure-aws-credentials@v2
      with:
        role-to-assume: ${{ secrets.AWS_TGW_ROLE }}
        aws-region: us-east-1
    
    - name: Download Terraform Outputs
      uses: actions/download-artifact@v3
      with:
        name: terraform-outputs
        path: ./
    
    - name: Test VPC Connectivity
      run: |
        python scripts/test_vpc_connectivity.py \
          --terraform-outputs terraform-outputs.json \
          --environment ${{ github.event.inputs.environment || 'development' }}
    
    - name: Test Route Propagation
      run: |
        python scripts/test_route_propagation.py \
          --terraform-outputs terraform-outputs.json \
          --expected-routes network/expected-routes.json
    
    - name: Test Cross-Account Access
      if: github.event.inputs.environment == 'production'
      run: |
        python scripts/test_cross_account_access.py \
          --shared-accounts ${{ secrets.SHARED_ACCOUNT_IDS }} \
          --transit-gateway-id $(cat terraform-outputs.json | jq -r '.transit_gateway_id.value')
    
    - name: Generate Network Topology
      run: |
        python scripts/generate_network_topology.py \
          --transit-gateway-id $(cat terraform-outputs.json | jq -r '.transit_gateway_id.value') \
          --output-format html \
          --output-file network-topology.html
    
    - name: Upload Network Topology
      uses: actions/upload-artifact@v3
      with:
        name: network-topology
        path: network-topology.html

  monitoring-setup:
    needs: terraform-apply
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    
    - name: Configure AWS credentials
      uses: aws-actions/configure-aws-credentials@v2
      with:
        role-to-assume: ${{ secrets.AWS_TGW_ROLE }}
        aws-region: us-east-1
    
    - name: Download Terraform Outputs
      uses: actions/download-artifact@v3
      with:
        name: terraform-outputs
        path: ./
    
    - name: Setup CloudWatch Dashboards
      run: |
        python scripts/setup_tgw_dashboards.py \
          --terraform-outputs terraform-outputs.json \
          --dashboard-name "TransitGateway-${{ github.event.inputs.environment || 'development' }}"
    
    - name: Configure VPC Flow Logs
      run: |
        python scripts/configure_flow_logs.py \
          --terraform-outputs terraform-outputs.json \
          --log-destination-type s3 \
          --s3-bucket ${{ secrets.FLOW_LOGS_BUCKET }}

  notification:
    needs: [terraform-apply, network-testing, monitoring-setup]
    runs-on: ubuntu-latest
    if: always()
    steps:
    - name: Send Deployment Summary
      uses: 8398a7/action-slack@v3
      with:
        status: ${{ job.status }}
        channel: '#network-ops'
        message: |
          Transit Gateway Deployment completed
          - Environment: ${{ github.event.inputs.environment || 'development' }}
          - Action: ${{ github.event.inputs.action || 'deploy' }}
          - Status: ${{ job.status }}
          - Network topology and test results available in artifacts
      env:
        SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
```

## Practical Use Cases

### 1. Enterprise Hub-and-Spoke Architecture
- **Centralized connectivity** for hundreds of VPCs across multiple AWS accounts
- **Segmented routing** with environment-specific route tables (Dev/Stage/Prod)
- **On-premises integration** via VPN and Direct Connect with automated failover
- **Cost optimization** through centralized NAT Gateway and internet egress

### 2. Multi-Region Disaster Recovery Network
- **Inter-region Transit Gateway peering** for seamless cross-region connectivity
- **Automated failover routing** with health check integration
- **Disaster recovery traffic** isolation with dedicated route tables
- **Cross-region replication** support for databases and storage systems

### 3. Multi-Account Network Governance
- **AWS RAM integration** for sharing Transit Gateway across AWS Organizations
- **Centralized network security** with shared inspection VPC
- **Cross-account DNS resolution** with Route 53 Resolver endpoints
- **Compliance enforcement** through network segmentation and audit trails

### 4. Hybrid Cloud Network Architecture
- **SD-WAN integration** with multiple customer gateways and ECMP
- **Direct Connect redundancy** across multiple locations
- **Dynamic routing** with BGP for optimal path selection
- **Network performance monitoring** with real-time metrics and alerting

### 5. Microservices Network Mesh
- **Service-to-service connectivity** across multiple VPCs and regions
- **Network load balancing** with Transit Gateway and ALB integration
- **Service mesh integration** with Istio and AWS App Mesh
- **Container networking** optimization for EKS and ECS workloads

## Advanced Network Orchestration Features

- **Intelligent routing** with dynamic path selection based on performance metrics
- **Network segmentation** enforcement through route table associations
- **Bandwidth monitoring** and cost optimization through traffic analysis
- **Security inspection** integration with centralized firewall appliances
- **DNS resolution** automation across VPCs and on-premises networks
- **Multicast support** for distributed applications and media streaming

## Network Performance Optimization

- **Route propagation optimization** to minimize convergence time
- **ECMP load balancing** for high-throughput VPN connections  
- **Attachment-level monitoring** for granular traffic analysis
- **Network path optimization** based on latency and throughput metrics
- **Capacity planning** with predictive scaling based on traffic patterns
- **Cost allocation** tracking per attachment and route table

## Network Security and Compliance

- **Network access control** through route table associations and propagation
- **Traffic inspection** integration with security appliances and WAF
- **Compliance automation** with network segmentation enforcement
- **Audit trail generation** for all network configuration changes
- **Encryption enforcement** for all inter-VPC and hybrid connections
- **Zero-trust networking** principles with micro-segmentation support

