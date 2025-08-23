# Networking VPN & Tunneling

## Overview

Virtual Private Networks (VPNs) and tunneling protocols enable secure communication over untrusted networks by creating encrypted tunnels between endpoints. This guide covers VPN architectures, tunneling protocols, site-to-site connectivity, remote access solutions, and enterprise VPN implementations essential for DevOps engineers managing hybrid cloud and distributed infrastructure.

## VPN Fundamentals and Architecture

### VPN Types and Use Cases

```python
from enum import Enum
from dataclasses import dataclass
from typing import List, Dict, Optional
import ipaddress

class VPNType(Enum):
    SITE_TO_SITE = "site-to-site"
    REMOTE_ACCESS = "remote-access"
    CLIENT_TO_SITE = "client-to-site"
    MESH = "mesh"
    HUB_AND_SPOKE = "hub-and-spoke"

class TunnelProtocol(Enum):
    IPSEC = "ipsec"
    OPENVPN = "openvpn"
    WIREGUARD = "wireguard"
    L2TP = "l2tp"
    PPTP = "pptp"
    SSTP = "sstp"
    GRETAP = "gretap"

@dataclass
class VPNEndpoint:
    name: str
    public_ip: str
    private_networks: List[str]
    location: str
    tunnel_protocol: TunnelProtocol
    authentication_method: str
    encryption_cipher: str

@dataclass
class VPNTunnel:
    name: str
    local_endpoint: VPNEndpoint
    remote_endpoint: VPNEndpoint
    tunnel_protocol: TunnelProtocol
    status: str
    bandwidth_mbps: int
    latency_ms: float
    packet_loss_percent: float

class EnterpriseVPNPlanner:
    def __init__(self):
        self.endpoints = []
        self.tunnels = []
        self.route_table = {}
    
    def add_endpoint(self, endpoint: VPNEndpoint):
        """Add VPN endpoint to the network"""
        self.endpoints.append(endpoint)
        return f"Added endpoint: {endpoint.name} ({endpoint.public_ip})"
    
    def create_site_to_site_tunnel(self, local_name: str, remote_name: str, 
                                 protocol: TunnelProtocol = TunnelProtocol.IPSEC):
        """Create site-to-site VPN tunnel between endpoints"""
        local_endpoint = next((ep for ep in self.endpoints if ep.name == local_name), None)
        remote_endpoint = next((ep for ep in self.endpoints if ep.name == remote_name), None)
        
        if not local_endpoint or not remote_endpoint:
            return {"error": "One or both endpoints not found"}
        
        tunnel_name = f"{local_name}-to-{remote_name}"
        tunnel = VPNTunnel(
            name=tunnel_name,
            local_endpoint=local_endpoint,
            remote_endpoint=remote_endpoint,
            tunnel_protocol=protocol,
            status="configured",
            bandwidth_mbps=100,
            latency_ms=0.0,
            packet_loss_percent=0.0
        )
        
        self.tunnels.append(tunnel)
        
        # Add routing entries
        self._add_route_entries(tunnel)
        
        return {
            "tunnel_name": tunnel_name,
            "local_endpoint": local_endpoint.name,
            "remote_endpoint": remote_endpoint.name,
            "protocol": protocol.value,
            "status": "created"
        }
    
    def _add_route_entries(self, tunnel: VPNTunnel):
        """Add routing entries for VPN tunnel"""
        # Routes from local to remote networks
        for remote_network in tunnel.remote_endpoint.private_networks:
            route_key = f"{tunnel.local_endpoint.name}->{remote_network}"
            self.route_table[route_key] = {
                "destination": remote_network,
                "gateway": tunnel.remote_endpoint.public_ip,
                "tunnel": tunnel.name,
                "metric": 100
            }
        
        # Routes from remote to local networks
        for local_network in tunnel.local_endpoint.private_networks:
            route_key = f"{tunnel.remote_endpoint.name}->{local_network}"
            self.route_table[route_key] = {
                "destination": local_network,
                "gateway": tunnel.local_endpoint.public_ip,
                "tunnel": tunnel.name,
                "metric": 100
            }
    
    def generate_network_diagram(self):
        """Generate network topology representation"""
        diagram = {
            "endpoints": len(self.endpoints),
            "tunnels": len(self.tunnels),
            "topology": {},
            "routing_table": self.route_table
        }
        
        for endpoint in self.endpoints:
            diagram["topology"][endpoint.name] = {
                "public_ip": endpoint.public_ip,
                "private_networks": endpoint.private_networks,
                "location": endpoint.location,
                "connected_to": []
            }
        
        for tunnel in self.tunnels:
            local_name = tunnel.local_endpoint.name
            remote_name = tunnel.remote_endpoint.name
            
            diagram["topology"][local_name]["connected_to"].append({
                "endpoint": remote_name,
                "tunnel": tunnel.name,
                "protocol": tunnel.tunnel_protocol.value
            })
            
            diagram["topology"][remote_name]["connected_to"].append({
                "endpoint": local_name,
                "tunnel": tunnel.name,
                "protocol": tunnel.tunnel_protocol.value
            })
        
        return diagram

# Example enterprise VPN setup
vpn_planner = EnterpriseVPNPlanner()

# Define company locations
headquarters = VPNEndpoint(
    name="headquarters",
    public_ip="203.0.113.10",
    private_networks=["10.0.0.0/16"],
    location="New York",
    tunnel_protocol=TunnelProtocol.IPSEC,
    authentication_method="PSK",
    encryption_cipher="AES-256-GCM"
)

branch_office_la = VPNEndpoint(
    name="branch-la",
    public_ip="203.0.113.20",
    private_networks=["10.1.0.0/16"],
    location="Los Angeles",
    tunnel_protocol=TunnelProtocol.IPSEC,
    authentication_method="PSK",
    encryption_cipher="AES-256-GCM"
)

aws_vpc_east = VPNEndpoint(
    name="aws-vpc-east",
    public_ip="203.0.113.30",
    private_networks=["10.2.0.0/16"],
    location="AWS us-east-1",
    tunnel_protocol=TunnelProtocol.IPSEC,
    authentication_method="Certificate",
    encryption_cipher="AES-256-GCM"
)

azure_vnet_west = VPNEndpoint(
    name="azure-vnet-west",
    public_ip="203.0.113.40", 
    private_networks=["10.3.0.0/16"],
    location="Azure West US 2",
    tunnel_protocol=TunnelProtocol.IPSEC,
    authentication_method="Certificate",
    encryption_cipher="AES-256-GCM"
)

# Add endpoints to planner
for endpoint in [headquarters, branch_office_la, aws_vpc_east, azure_vnet_west]:
    vpn_planner.add_endpoint(endpoint)

# Create site-to-site tunnels (hub-and-spoke topology)
tunnels = [
    ("headquarters", "branch-la"),
    ("headquarters", "aws-vpc-east"),
    ("headquarters", "azure-vnet-west"),
    ("aws-vpc-east", "azure-vnet-west")  # Direct cloud-to-cloud tunnel
]

print("Enterprise VPN Tunnel Setup")
print("=" * 40)

for local, remote in tunnels:
    result = vpn_planner.create_site_to_site_tunnel(local, remote)
    print(f"✅ {result['tunnel_name']}: {result['local_endpoint']} <-> {result['remote_endpoint']}")

# Generate network topology
topology = vpn_planner.generate_network_diagram()
print(f"\nNetwork Topology Summary:")
print(f"Endpoints: {topology['endpoints']}")
print(f"Tunnels: {topology['tunnels']}")
print(f"Routes: {len(topology['routing_table'])}")
```

## IPSec VPN Implementation

### StrongSwan IPSec Configuration

```bash
#!/bin/bash
# ipsec-setup.sh - StrongSwan IPSec VPN setup script

# Configuration variables
LOCAL_PUBLIC_IP="203.0.113.10"
LOCAL_PRIVATE_NETWORK="10.0.0.0/16"
REMOTE_PUBLIC_IP="203.0.113.20"
REMOTE_PRIVATE_NETWORK="10.1.0.0/16"
PSK="your-very-secure-pre-shared-key-here"
VPN_NAME="site-to-site-vpn"

echo "Setting up StrongSwan IPSec VPN"
echo "==============================="

# Install StrongSwan
if command -v apt-get &> /dev/null; then
    sudo apt-get update
    sudo apt-get install -y strongswan strongswan-pki
elif command -v yum &> /dev/null; then
    sudo yum install -y strongswan
fi

# Configure IPSec secrets
sudo tee /etc/ipsec.secrets << EOF
# IPSec secrets for site-to-site VPN
$LOCAL_PUBLIC_IP $REMOTE_PUBLIC_IP : PSK "$PSK"
EOF

# Configure IPSec connection
sudo tee /etc/ipsec.conf << EOF
# StrongSwan IPSec configuration
config setup
    charondebug="ike 1, knl 1, cfg 0"
    uniqueids=no

conn %default
    ikelifetime=60m
    keylife=20m
    rekeymargin=3m
    keyingtries=1
    keyexchange=ikev2
    authby=secret

conn $VPN_NAME
    left=$LOCAL_PUBLIC_IP
    leftsubnet=$LOCAL_PRIVATE_NETWORK
    leftid=$LOCAL_PUBLIC_IP
    leftfirewall=yes
    
    right=$REMOTE_PUBLIC_IP
    rightsubnet=$REMOTE_PRIVATE_NETWORK
    rightid=$REMOTE_PUBLIC_IP
    
    # Phase 1 (IKE) parameters
    ike=aes256-sha256-modp2048!
    
    # Phase 2 (ESP) parameters  
    esp=aes256-sha256!
    
    # Connection behavior
    auto=start
    dpdaction=restart
    dpddelay=30s
    dpdtimeout=120s
    
    # Enable compression if needed
    compress=no
EOF

# Configure firewall rules
sudo tee /etc/ipsec-firewall-rules.sh << 'EOF'
#!/bin/bash
# IPSec firewall rules

# Allow IPSec traffic
iptables -A INPUT -p esp -j ACCEPT
iptables -A INPUT -p udp --dport 500 -j ACCEPT  # IKE
iptables -A INPUT -p udp --dport 4500 -j ACCEPT # NAT-T

# Allow traffic between VPN subnets
iptables -A FORWARD -s $LOCAL_PRIVATE_NETWORK -d $REMOTE_PRIVATE_NETWORK -j ACCEPT
iptables -A FORWARD -s $REMOTE_PRIVATE_NETWORK -d $LOCAL_PRIVATE_NETWORK -j ACCEPT

# Enable IP forwarding
echo 1 > /proc/sys/net/ipv4/ip_forward
echo "net.ipv4.ip_forward=1" >> /etc/sysctl.conf
EOF

sudo chmod +x /etc/ipsec-firewall-rules.sh
sudo /etc/ipsec-firewall-rules.sh

# Start and enable StrongSwan
sudo systemctl enable strongswan
sudo systemctl start strongswan

echo "IPSec VPN configuration completed"
echo "Connection name: $VPN_NAME"
echo "Local network: $LOCAL_PRIVATE_NETWORK"
echo "Remote network: $REMOTE_PRIVATE_NETWORK"

# Test connection
echo ""
echo "Testing VPN connection..."
sudo ipsec up $VPN_NAME

# Show status
echo ""
echo "VPN Status:"
sudo ipsec status
```

### Terraform AWS VPN Gateway Setup

```hcl
# aws-vpn-gateway.tf - AWS VPN Gateway with customer gateway

variable "customer_gateway_ip" {
  description = "Public IP of customer gateway"
  type        = string
  default     = "203.0.113.10"
}

variable "customer_network_cidr" {
  description = "Customer on-premises network CIDR"
  type        = string
  default     = "10.0.0.0/16"
}

variable "aws_vpc_cidr" {
  description = "AWS VPC CIDR block"
  type        = string
  default     = "10.2.0.0/16"
}

# VPC for AWS resources
resource "aws_vpc" "main" {
  cidr_block           = var.aws_vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true
  
  tags = {
    Name = "vpn-gateway-vpc"
  }
}

# Customer Gateway (on-premises endpoint)
resource "aws_customer_gateway" "main" {
  bgp_asn    = 65000
  ip_address = var.customer_gateway_ip
  type       = "ipsec.1"
  
  tags = {
    Name = "main-customer-gateway"
  }
}

# VPN Gateway (AWS endpoint)
resource "aws_vpn_gateway" "main" {
  vpc_id = aws_vpc.main.id
  
  tags = {
    Name = "main-vpn-gateway"
  }
}

# Site-to-Site VPN Connection
resource "aws_vpn_connection" "main" {
  customer_gateway_id = aws_customer_gateway.main.id
  type                = "ipsec.1"
  vpn_gateway_id      = aws_vpn_gateway.main.id
  static_routes_only  = true
  
  tags = {
    Name = "main-vpn-connection"
  }
}

# VPN Connection Route (for customer network)
resource "aws_vpn_connection_route" "office" {
  vpn_connection_id      = aws_vpn_connection.main.id
  destination_cidr_block = var.customer_network_cidr
}

# Route table for VPN traffic
resource "aws_route_table" "vpn" {
  vpc_id = aws_vpc.main.id
  
  tags = {
    Name = "vpn-route-table"
  }
}

# Route to customer network via VPN
resource "aws_route" "to_customer" {
  route_table_id         = aws_route_table.vpn.id
  destination_cidr_block = var.customer_network_cidr
  vpn_gateway_id         = aws_vpn_gateway.main.id
}

# Private subnet for VPN resources
resource "aws_subnet" "private" {
  count = 2
  
  vpc_id            = aws_vpc.main.id
  cidr_block        = cidrsubnet(var.aws_vpc_cidr, 8, count.index + 1)
  availability_zone = data.aws_availability_zones.available.names[count.index]
  
  tags = {
    Name = "private-subnet-${count.index + 1}"
  }
}

# Associate route table with subnets
resource "aws_route_table_association" "private" {
  count = length(aws_subnet.private)
  
  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.vpn.id
}

# Security group for VPN resources
resource "aws_security_group" "vpn_resources" {
  name_prefix = "vpn-resources"
  vpc_id      = aws_vpc.main.id
  
  # Allow traffic from customer network
  ingress {
    from_port   = 0
    to_port     = 65535
    protocol    = "tcp"
    cidr_blocks = [var.customer_network_cidr]
  }
  
  ingress {
    from_port   = 0
    to_port     = 65535
    protocol    = "udp"
    cidr_blocks = [var.customer_network_cidr]
  }
  
  # Allow ICMP for testing
  ingress {
    from_port   = -1
    to_port     = -1
    protocol    = "icmp"
    cidr_blocks = [var.customer_network_cidr]
  }
  
  # Outbound traffic
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  tags = {
    Name = "vpn-resources-sg"
  }
}

# CloudWatch monitoring for VPN
resource "aws_cloudwatch_metric_alarm" "vpn_tunnel_state" {
  count = 2
  
  alarm_name          = "vpn-tunnel-${count.index + 1}-down"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "TunnelState"
  namespace           = "AWS/VPN"
  period              = "300"
  statistic           = "Maximum"
  threshold           = "1"
  alarm_description   = "VPN Tunnel ${count.index + 1} is down"
  
  dimensions = {
    VpnId    = aws_vpn_connection.main.id
    TunnelId = aws_vpn_connection.main.tunnel_details[count.index].tunnel_id
  }
  
  alarm_actions = [aws_sns_topic.vpn_alerts.arn]
}

# SNS topic for VPN alerts
resource "aws_sns_topic" "vpn_alerts" {
  name = "vpn-alerts"
}

# Data source for availability zones
data "aws_availability_zones" "available" {
  state = "available"
}

# Output VPN connection details
output "vpn_connection_id" {
  value = aws_vpn_connection.main.id
}

output "customer_gateway_configuration" {
  value     = aws_vpn_connection.main.customer_gateway_configuration
  sensitive = true
}

output "tunnel_details" {
  value = [
    for tunnel in aws_vpn_connection.main.tunnel_details : {
      tunnel_id                = tunnel.tunnel_id
      outside_ip_address      = tunnel.outside_ip_address
      pre_shared_key         = tunnel.pre_shared_key
      tunnel_inside_cidr     = tunnel.tunnel_inside_cidr
    }
  ]
  sensitive = true
}
```

## WireGuard Modern VPN Implementation

### WireGuard Server Setup

```bash
#!/bin/bash
# wireguard-server-setup.sh - WireGuard VPN server setup

SERVER_PUBLIC_IP="203.0.113.10"
SERVER_WG_IP="10.200.200.1/24"
SERVER_WG_PORT="51820"
WG_INTERFACE="wg0"

echo "Setting up WireGuard VPN Server"
echo "==============================="

# Install WireGuard
if command -v apt-get &> /dev/null; then
    sudo apt-get update
    sudo apt-get install -y wireguard wireguard-tools
elif command -v yum &> /dev/null; then
    sudo yum install -y wireguard-tools
fi

# Generate server keys
cd /etc/wireguard
sudo wg genkey | sudo tee server_private.key | wg pubkey | sudo tee server_public.key

# Set permissions
sudo chmod 600 server_private.key
sudo chmod 644 server_public.key

# Read keys
SERVER_PRIVATE_KEY=$(sudo cat server_private.key)
SERVER_PUBLIC_KEY=$(sudo cat server_public.key)

# Create server configuration
sudo tee /etc/wireguard/$WG_INTERFACE.conf << EOF
[Interface]
PrivateKey = $SERVER_PRIVATE_KEY
Address = $SERVER_WG_IP
ListenPort = $SERVER_WG_PORT
SaveConfig = true

# Enable IP forwarding
PostUp = echo 1 > /proc/sys/net/ipv4/ip_forward
PostUp = iptables -A FORWARD -i %i -j ACCEPT
PostUp = iptables -A FORWARD -o %i -j ACCEPT
PostUp = iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE

# Disable IP forwarding on shutdown
PostDown = iptables -D FORWARD -i %i -j ACCEPT
PostDown = iptables -D FORWARD -o %i -j ACCEPT
PostDown = iptables -t nat -D POSTROUTING -o eth0 -j MASQUERADE

EOF

# Enable IP forwarding permanently
echo "net.ipv4.ip_forward=1" | sudo tee -a /etc/sysctl.conf
sudo sysctl -p

# Start and enable WireGuard
sudo systemctl enable wg-quick@$WG_INTERFACE
sudo systemctl start wg-quick@$WG_INTERFACE

echo "WireGuard server setup completed"
echo "Server public key: $SERVER_PUBLIC_KEY"
echo "Server endpoint: $SERVER_PUBLIC_IP:$SERVER_WG_PORT"
echo "Server VPN IP: $SERVER_WG_IP"

# Create client management script
sudo tee /usr/local/bin/wg-add-client << 'EOF'
#!/bin/bash
# Add WireGuard client

if [ $# -ne 2 ]; then
    echo "Usage: $0 <client-name> <client-ip>"
    echo "Example: $0 laptop 10.200.200.10"
    exit 1
fi

CLIENT_NAME="$1"
CLIENT_IP="$2"
WG_INTERFACE="wg0"
SERVER_PUBLIC_KEY=$(cat /etc/wireguard/server_public.key)
SERVER_ENDPOINT="203.0.113.10:51820"

cd /etc/wireguard/clients || mkdir -p /etc/wireguard/clients && cd /etc/wireguard/clients

# Generate client keys
wg genkey | tee ${CLIENT_NAME}_private.key | wg pubkey > ${CLIENT_NAME}_public.key
CLIENT_PRIVATE_KEY=$(cat ${CLIENT_NAME}_private.key)
CLIENT_PUBLIC_KEY=$(cat ${CLIENT_NAME}_public.key)

# Create client configuration
cat > ${CLIENT_NAME}.conf << EOL
[Interface]
PrivateKey = $CLIENT_PRIVATE_KEY
Address = $CLIENT_IP/24
DNS = 8.8.8.8

[Peer]
PublicKey = $SERVER_PUBLIC_KEY
Endpoint = $SERVER_ENDPOINT
AllowedIPs = 0.0.0.0/0
PersistentKeepalive = 25
EOL

# Add peer to server
wg set $WG_INTERFACE peer $CLIENT_PUBLIC_KEY allowed-ips $CLIENT_IP/32

# Save configuration
wg-quick save $WG_INTERFACE

echo "Client '$CLIENT_NAME' added successfully"
echo "Client config saved to: /etc/wireguard/clients/${CLIENT_NAME}.conf"
echo "Client public key: $CLIENT_PUBLIC_KEY"

# Generate QR code for mobile clients
if command -v qrencode &> /dev/null; then
    qrencode -t ansiutf8 < ${CLIENT_NAME}.conf
fi
EOF

sudo chmod +x /usr/local/bin/wg-add-client

# Create client removal script
sudo tee /usr/local/bin/wg-remove-client << 'EOF'
#!/bin/bash
# Remove WireGuard client

if [ $# -ne 1 ]; then
    echo "Usage: $0 <client-name>"
    exit 1
fi

CLIENT_NAME="$1"
WG_INTERFACE="wg0"

cd /etc/wireguard/clients

if [ ! -f "${CLIENT_NAME}_public.key" ]; then
    echo "Client '$CLIENT_NAME' not found"
    exit 1
fi

CLIENT_PUBLIC_KEY=$(cat ${CLIENT_NAME}_public.key)

# Remove peer from server
wg set $WG_INTERFACE peer $CLIENT_PUBLIC_KEY remove

# Save configuration
wg-quick save $WG_INTERFACE

# Remove client files
rm -f ${CLIENT_NAME}_private.key ${CLIENT_NAME}_public.key ${CLIENT_NAME}.conf

echo "Client '$CLIENT_NAME' removed successfully"
EOF

sudo chmod +x /usr/local/bin/wg-remove-client

echo ""
echo "Client management scripts created:"
echo "  - Add client: sudo wg-add-client <name> <ip>"
echo "  - Remove client: sudo wg-remove-client <name>"
```

## OpenVPN Enterprise Setup

### OpenVPN Server Configuration

```python
import os
import subprocess
import ipaddress
from datetime import datetime, timedelta

class OpenVPNManager:
    def __init__(self, server_dir="/etc/openvpn/server"):
        self.server_dir = server_dir
        self.ca_dir = f"{server_dir}/easy-rsa"
        self.client_configs_dir = f"{server_dir}/client-configs"
        self.server_ip = "203.0.113.10"
        self.vpn_network = ipaddress.IPv4Network("10.8.0.0/24")
        
    def setup_certificate_authority(self):
        """Setup Certificate Authority for OpenVPN"""
        print("Setting up Certificate Authority...")
        
        # Create directories
        os.makedirs(self.ca_dir, exist_ok=True)
        os.makedirs(self.client_configs_dir, exist_ok=True)
        
        # Download easy-rsa
        subprocess.run([
            "wget", "-O", "/tmp/easy-rsa.tgz",
            "https://github.com/OpenVPN/easy-rsa/releases/latest/download/EasyRSA-unix.tgz"
        ])
        subprocess.run(["tar", "xzf", "/tmp/easy-rsa.tgz", "-C", self.server_dir])
        
        # Initialize PKI
        env = os.environ.copy()
        env.update({
            "EASYRSA_BATCH": "1",
            "EASYRSA_REQ_COUNTRY": "US",
            "EASYRSA_REQ_PROVINCE": "NY",
            "EASYRSA_REQ_CITY": "New York",
            "EASYRSA_REQ_ORG": "Enterprise VPN",
            "EASYRSA_REQ_EMAIL": "admin@company.com",
            "EASYRSA_REQ_OU": "IT Department"
        })
        
        os.chdir(self.ca_dir)
        subprocess.run(["./easyrsa", "init-pki"], env=env)
        subprocess.run(["./easyrsa", "build-ca", "nopass"], env=env)
        subprocess.run(["./easyrsa", "gen-dh"], env=env)
        subprocess.run(["./easyrsa", "build-server-full", "server", "nopass"], env=env)
        
        # Generate HMAC key
        subprocess.run(["openvpn", "--genkey", "--secret", "ta.key"])
        
        return "Certificate Authority setup completed"
    
    def generate_server_config(self):
        """Generate OpenVPN server configuration"""
        config = f"""# OpenVPN Server Configuration
port 1194
proto udp
dev tun

# SSL/TLS root certificate (ca), certificate (cert), and private key (key)
ca {self.ca_dir}/pki/ca.crt
cert {self.ca_dir}/pki/issued/server.crt
key {self.ca_dir}/pki/private/server.key
dh {self.ca_dir}/pki/dh.pem

# Network topology
topology subnet

# Configure server mode for ethernet bridging
server {self.vpn_network.network_address} {self.vpn_network.netmask}

# Maintain a record of client <-> virtual IP address associations
ifconfig-pool-persist ipp.txt

# Configure server mode for ethernet bridging using a DHCP-proxy
push "redirect-gateway def1 bypass-dhcp"

# Push DNS servers to clients
push "dhcp-option DNS 8.8.8.8"
push "dhcp-option DNS 8.8.4.4"

# Allow clients to see each other
client-to-client

# Keep connections alive
keepalive 10 120

# Enable compression
compress lz4-v2
push "compress lz4-v2"

# Maximum number of concurrently connected clients
max-clients 100

# Run OpenVPN as non-privileged user
user nobody
group nogroup

# Persist keys across restarts
persist-key
persist-tun

# Log settings
status openvpn-status.log
log-append /var/log/openvpn.log
verb 3

# Silence repeating messages
mute 20

# HMAC authentication
tls-auth {self.ca_dir}/ta.key 0

# Additional security
cipher AES-256-GCM
auth SHA256
tls-version-min 1.2
tls-cipher TLS-DHE-RSA-WITH-AES-256-GCM-SHA384
"""
        
        config_path = f"{self.server_dir}/server.conf"
        with open(config_path, 'w') as f:
            f.write(config)
        
        return f"Server configuration saved to {config_path}"
    
    def create_client_certificate(self, client_name):
        """Create client certificate and configuration"""
        os.chdir(self.ca_dir)
        
        # Generate client certificate
        env = os.environ.copy()
        env["EASYRSA_BATCH"] = "1"
        subprocess.run(["./easyrsa", "build-client-full", client_name, "nopass"], env=env)
        
        # Read certificate files
        with open(f"pki/ca.crt", 'r') as f:
            ca_cert = f.read()
        
        with open(f"pki/issued/{client_name}.crt", 'r') as f:
            client_cert = f.read()
        
        with open(f"pki/private/{client_name}.key", 'r') as f:
            client_key = f.read()
        
        with open("ta.key", 'r') as f:
            tls_auth = f.read()
        
        # Generate client configuration
        client_config = f"""# OpenVPN Client Configuration for {client_name}
client
dev tun
proto udp
remote {self.server_ip} 1194
resolv-retry infinite
nobind
persist-key
persist-tun
remote-cert-tls server
cipher AES-256-GCM
auth SHA256
verb 3
compress lz4-v2

# Certificates and keys
<ca>
{ca_cert}
</ca>

<cert>
{client_cert}
</cert>

<key>
{client_key}
</key>

<tls-auth>
{tls_auth}
</tls-auth>
key-direction 1
"""
        
        # Save client configuration
        client_config_path = f"{self.client_configs_dir}/{client_name}.ovpn"
        with open(client_config_path, 'w') as f:
            f.write(client_config)
        
        return {
            "client_name": client_name,
            "config_file": client_config_path,
            "status": "created"
        }
    
    def revoke_client_certificate(self, client_name):
        """Revoke client certificate"""
        os.chdir(self.ca_dir)
        
        # Revoke certificate
        env = os.environ.copy()
        env["EASYRSA_BATCH"] = "1"
        subprocess.run(["./easyrsa", "revoke", client_name], env=env)
        subprocess.run(["./easyrsa", "gen-crl"], env=env)
        
        # Update CRL
        subprocess.run(["cp", "pki/crl.pem", f"{self.server_dir}/crl.pem"])
        
        # Remove client configuration
        client_config_path = f"{self.client_configs_dir}/{client_name}.ovpn"
        if os.path.exists(client_config_path):
            os.remove(client_config_path)
        
        return f"Client certificate for {client_name} revoked"
    
    def get_connected_clients(self):
        """Get list of currently connected clients"""
        try:
            with open(f"{self.server_dir}/openvpn-status.log", 'r') as f:
                content = f.read()
            
            clients = []
            in_client_section = False
            
            for line in content.split('\n'):
                if line.startswith("Common Name,Real Address"):
                    in_client_section = True
                    continue
                elif line.startswith("ROUTING TABLE"):
                    in_client_section = False
                    continue
                
                if in_client_section and line.strip():
                    parts = line.split(',')
                    if len(parts) >= 5:
                        clients.append({
                            "name": parts[0],
                            "real_address": parts[1],
                            "virtual_address": parts[2] if len(parts) > 2 else "",
                            "bytes_received": parts[3] if len(parts) > 3 else "0",
                            "bytes_sent": parts[4] if len(parts) > 4 else "0",
                            "connected_since": parts[5] if len(parts) > 5 else ""
                        })
            
            return clients
        except FileNotFoundError:
            return []

# Example usage
openvpn_mgr = OpenVPNManager()

# Setup CA and server
print("Setting up OpenVPN server...")
# openvpn_mgr.setup_certificate_authority()
# openvpn_mgr.generate_server_config()

# Create client certificates
clients = ["john-laptop", "mary-mobile", "dev-server"]
for client in clients:
    result = openvpn_mgr.create_client_certificate(client)
    print(f"Created client config: {result['client_name']} -> {result['config_file']}")

# Monitor connected clients
print("\nConnected Clients:")
connected = openvpn_mgr.get_connected_clients()
for client in connected:
    print(f"  {client['name']:15} | {client['real_address']:15} | {client['virtual_address']}")
```

## VPN Monitoring and Management

### VPN Health Monitoring Script

```python
import subprocess
import json
import time
import logging
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
from typing import Dict, List
import psutil
import requests

class VPNHealthMonitor:
    def __init__(self, config_file="/etc/vpn-monitor.json"):
        self.config = self._load_config(config_file)
        self.setup_logging()
        
    def _load_config(self, config_file):
        """Load monitoring configuration"""
        default_config = {
            "tunnels": [
                {
                    "name": "headquarters-to-aws",
                    "type": "ipsec",
                    "local_ip": "10.0.1.1",
                    "remote_ip": "10.2.1.1",
                    "connection_name": "site-to-site-vpn"
                },
                {
                    "name": "wireguard-server",
                    "type": "wireguard", 
                    "interface": "wg0",
                    "expected_peers": 5
                }
            ],
            "monitoring": {
                "check_interval": 60,
                "ping_timeout": 5,
                "alert_threshold": 3,
                "email_alerts": True,
                "smtp_server": "localhost",
                "alert_email": "admin@company.com"
            }
        }
        
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            with open(config_file, 'w') as f:
                json.dump(default_config, f, indent=4)
            return default_config
    
    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('/var/log/vpn-monitor.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def check_ipsec_tunnel(self, tunnel_config):
        """Check IPSec tunnel status"""
        try:
            # Check tunnel status with strongswan
            result = subprocess.run(
                ["ipsec", "status", tunnel_config["connection_name"]],
                capture_output=True, text=True, timeout=10
            )
            
            tunnel_status = {
                "name": tunnel_config["name"],
                "type": "ipsec",
                "status": "down",
                "details": result.stdout
            }
            
            if "ESTABLISHED" in result.stdout:
                tunnel_status["status"] = "up"
                
                # Test connectivity
                ping_result = subprocess.run(
                    ["ping", "-c", "3", "-W", str(self.config["monitoring"]["ping_timeout"]), 
                     tunnel_config["remote_ip"]],
                    capture_output=True, text=True, timeout=15
                )
                
                if ping_result.returncode == 0:
                    tunnel_status["ping_success"] = True
                    # Extract latency from ping output
                    for line in ping_result.stdout.split('\n'):
                        if 'avg' in line:
                            tunnel_status["avg_latency"] = line.split('/')[-2]
                else:
                    tunnel_status["ping_success"] = False
                    tunnel_status["status"] = "degraded"
            
            return tunnel_status
            
        except Exception as e:
            self.logger.error(f"Error checking IPSec tunnel {tunnel_config['name']}: {e}")
            return {
                "name": tunnel_config["name"],
                "type": "ipsec",
                "status": "error",
                "error": str(e)
            }
    
    def check_wireguard_tunnel(self, tunnel_config):
        """Check WireGuard tunnel status"""
        try:
            interface = tunnel_config["interface"]
            
            # Check if interface exists
            result = subprocess.run(
                ["wg", "show", interface],
                capture_output=True, text=True, timeout=10
            )
            
            tunnel_status = {
                "name": tunnel_config["name"],
                "type": "wireguard",
                "status": "down",
                "peers": [],
                "interface": interface
            }
            
            if result.returncode == 0:
                tunnel_status["status"] = "up"
                
                # Parse WireGuard status
                current_peer = None
                for line in result.stdout.split('\n'):
                    line = line.strip()
                    if line.startswith('peer:'):
                        if current_peer:
                            tunnel_status["peers"].append(current_peer)
                        current_peer = {"public_key": line.split(':', 1)[1].strip()}
                    elif current_peer and ':' in line:
                        key, value = line.split(':', 1)
                        current_peer[key.strip()] = value.strip()
                
                if current_peer:
                    tunnel_status["peers"].append(current_peer)
                
                # Check expected peer count
                expected_peers = tunnel_config.get("expected_peers", 0)
                actual_peers = len(tunnel_status["peers"])
                tunnel_status["peer_count_ok"] = actual_peers >= expected_peers
                
                if not tunnel_status["peer_count_ok"]:
                    tunnel_status["status"] = "degraded"
                    tunnel_status["warning"] = f"Expected {expected_peers} peers, found {actual_peers}"
            
            return tunnel_status
            
        except Exception as e:
            self.logger.error(f"Error checking WireGuard tunnel {tunnel_config['name']}: {e}")
            return {
                "name": tunnel_config["name"],
                "type": "wireguard",
                "status": "error",
                "error": str(e)
            }
    
    def check_system_resources(self):
        """Check system resources affecting VPN performance"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Check network interfaces
            network_stats = {}
            for interface, stats in psutil.net_io_counters(pernic=True).items():
                if interface.startswith(('wg', 'tun', 'tap')):
                    network_stats[interface] = {
                        "bytes_sent": stats.bytes_sent,
                        "bytes_recv": stats.bytes_recv,
                        "packets_sent": stats.packets_sent,
                        "packets_recv": stats.packets_recv,
                        "errors_in": stats.errin,
                        "errors_out": stats.errout
                    }
            
            return {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "disk_percent": disk.percent,
                "network_interfaces": network_stats,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error checking system resources: {e}")
            return {"error": str(e)}
    
    def send_alert(self, subject, message):
        """Send email alert"""
        if not self.config["monitoring"]["email_alerts"]:
            return
        
        try:
            msg = MIMEText(message)
            msg['Subject'] = subject
            msg['From'] = "vpn-monitor@company.com"
            msg['To'] = self.config["monitoring"]["alert_email"]
            
            server = smtplib.SMTP(self.config["monitoring"]["smtp_server"])
            server.send_message(msg)
            server.quit()
            
            self.logger.info(f"Alert sent: {subject}")
            
        except Exception as e:
            self.logger.error(f"Error sending alert: {e}")
    
    def run_health_check(self):
        """Run complete health check"""
        self.logger.info("Starting VPN health check...")
        
        health_report = {
            "timestamp": datetime.now().isoformat(),
            "tunnels": [],
            "system_resources": self.check_system_resources(),
            "overall_status": "healthy"
        }
        
        # Check all configured tunnels
        for tunnel_config in self.config["tunnels"]:
            if tunnel_config["type"] == "ipsec":
                tunnel_status = self.check_ipsec_tunnel(tunnel_config)
            elif tunnel_config["type"] == "wireguard":
                tunnel_status = self.check_wireguard_tunnel(tunnel_config)
            else:
                tunnel_status = {
                    "name": tunnel_config["name"],
                    "status": "unsupported",
                    "error": f"Unknown tunnel type: {tunnel_config['type']}"
                }
            
            health_report["tunnels"].append(tunnel_status)
            
            # Check for alerts
            if tunnel_status["status"] in ["down", "error"]:
                health_report["overall_status"] = "critical"
                self.send_alert(
                    f"VPN Tunnel Down: {tunnel_status['name']}",
                    f"Tunnel {tunnel_status['name']} is {tunnel_status['status']}\n\n"
                    f"Details: {tunnel_status.get('details', tunnel_status.get('error', 'No details available'))}"
                )
            elif tunnel_status["status"] == "degraded":
                health_report["overall_status"] = "degraded"
                self.send_alert(
                    f"VPN Tunnel Degraded: {tunnel_status['name']}",
                    f"Tunnel {tunnel_status['name']} is experiencing issues\n\n"
                    f"Warning: {tunnel_status.get('warning', 'Performance degraded')}"
                )
        
        return health_report
    
    def start_monitoring(self):
        """Start continuous monitoring"""
        self.logger.info("Starting VPN monitoring daemon...")
        
        while True:
            try:
                health_report = self.run_health_check()
                
                # Log summary
                tunnel_count = len(health_report["tunnels"])
                healthy_tunnels = len([t for t in health_report["tunnels"] if t["status"] == "up"])
                
                self.logger.info(
                    f"Health check complete: {healthy_tunnels}/{tunnel_count} tunnels healthy, "
                    f"Overall status: {health_report['overall_status']}"
                )
                
                time.sleep(self.config["monitoring"]["check_interval"])
                
            except KeyboardInterrupt:
                self.logger.info("Monitoring stopped by user")
                break
            except Exception as e:
                self.logger.error(f"Monitoring error: {e}")
                time.sleep(self.config["monitoring"]["check_interval"])

# Example usage
if __name__ == "__main__":
    monitor = VPNHealthMonitor()
    
    # Run single health check
    report = monitor.run_health_check()
    print(json.dumps(report, indent=2))
    
    # Start continuous monitoring (uncomment to run)
    # monitor.start_monitoring()
```

## Best Practices for Enterprise VPN Implementation

### Security Best Practices
- **Strong authentication** with certificate-based or multi-factor authentication
- **Perfect Forward Secrecy** using ephemeral key exchange algorithms
- **Regular key rotation** and certificate management procedures
- **Network segmentation** to limit VPN access to specific resources

### Performance Optimization
- **Protocol selection** based on use case (WireGuard for performance, IPSec for compatibility)
- **MTU optimization** to prevent fragmentation and improve throughput
- **Load balancing** across multiple VPN endpoints for redundancy
- **Bandwidth monitoring** and Quality of Service (QoS) implementation

### Operational Excellence  
- **Automated provisioning** of VPN clients and certificates
- **Centralized monitoring** with alerting for tunnel failures
- **Documentation** of network topology and routing configurations
- **Disaster recovery** planning for VPN infrastructure failures

This comprehensive VPN and tunneling guide provides enterprise-grade solutions for secure network connectivity, essential for modern DevOps infrastructure management across hybrid and multi-cloud environments.