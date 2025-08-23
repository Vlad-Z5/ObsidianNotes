# Networking OSI Model & TCP/IP Stack

> **Service Type:** Networking & Content Delivery | **Scope:** Global | **Serverless:** N/A

## Overview

The OSI (Open Systems Interconnection) model and TCP/IP stack form the foundational frameworks for understanding network communication. These models provide systematic approaches to network design, troubleshooting, and protocol implementation in enterprise environments.

## OSI 7-Layer Model Deep Dive

### Layer 1 - Physical Layer
**Function**: Raw bit transmission over physical medium
- **Components**: Cables, hubs, repeaters, network interface cards
- **Protocols**: Ethernet (10BASE-T, 100BASE-TX, 1000BASE-T), fiber optic standards
- **DevOps Relevance**: Infrastructure cabling, data center connectivity, bandwidth planning

### Layer 2 - Data Link Layer  
**Function**: Frame formatting, error detection, MAC addressing
- **Components**: Switches, bridges, wireless access points
- **Protocols**: Ethernet, 802.11 (Wi-Fi), Point-to-Point Protocol (PPP)
- **DevOps Relevance**: VLAN configuration, switch management, network segmentation

### Layer 3 - Network Layer
**Function**: Routing, logical addressing, path determination
- **Components**: Routers, layer 3 switches, firewalls
- **Protocols**: IPv4, IPv6, ICMP, OSPF, BGP, RIP
- **DevOps Relevance**: Route table management, subnet design, cloud networking

### Layer 4 - Transport Layer
**Function**: Reliable data delivery, flow control, error recovery
- **Components**: TCP/UDP implementation in operating systems
- **Protocols**: TCP (Transmission Control Protocol), UDP (User Datagram Protocol)
- **DevOps Relevance**: Port management, load balancing, connection pooling

### Layer 5 - Session Layer
**Function**: Session establishment, management, and termination
- **Components**: API gateways, session management services
- **Protocols**: NetBIOS, RPC, SQL sessions, TLS sessions
- **DevOps Relevance**: Session persistence, API management, connection management

### Layer 6 - Presentation Layer
**Function**: Data encryption, compression, format translation
- **Components**: SSL/TLS terminators, encryption appliances
- **Protocols**: SSL/TLS, JPEG, MPEG, ASCII, EBCDIC
- **DevOps Relevance**: Certificate management, data encryption, content optimization

### Layer 7 - Application Layer
**Function**: Network services to applications
- **Components**: Web servers, application servers, load balancers
- **Protocols**: HTTP/HTTPS, FTP, SMTP, DNS, DHCP, SSH
- **DevOps Relevance**: Application deployment, service configuration, API design

## TCP/IP Stack Implementation

### Internet Protocol Suite Architecture

#### Network Access Layer (Link Layer)
```bash
# Ethernet frame analysis
tcpdump -i eth0 -e -n
# Output shows MAC addresses and frame information
```

#### Internet Layer
```python
# IP packet analysis with Python
import socket
import struct

def parse_ip_header(packet):
    ip_header = packet[0:20]
    iph = struct.unpack('!BBHHHBBH4s4s', ip_header)
    
    version_ihl = iph[0]
    version = version_ihl >> 4
    ihl = version_ihl & 0xF
    
    iph_length = ihl * 4
    
    ttl = iph[5]
    protocol = iph[6]
    s_addr = socket.inet_ntoa(iph[8])
    d_addr = socket.inet_ntoa(iph[9])
    
    return {
        'version': version,
        'header_length': iph_length,
        'ttl': ttl,
        'protocol': protocol,
        'source_ip': s_addr,
        'destination_ip': d_addr
    }
```

#### Transport Layer
```yaml
# TCP connection parameters
tcp_connection:
  establishment:
    - "SYN: Client initiates connection"
    - "SYN-ACK: Server acknowledges and responds"
    - "ACK: Client acknowledges, connection established"
  
  data_transfer:
    - "Sequence numbers ensure ordered delivery"
    - "Acknowledgments confirm receipt"
    - "Window size controls flow"
    
  termination:
    - "FIN: Initiate close"
    - "ACK: Acknowledge close"
    - "FIN: Other side closes"
    - "ACK: Final acknowledgment"
```

#### Application Layer
```bash
# HTTP request analysis
curl -v https://api.example.com/users
# Shows complete HTTP transaction with headers
```

## Protocol Encapsulation

### Data Encapsulation Process
```
Application Data
    ↓
[TCP Header][Application Data] ← Transport Layer
    ↓  
[IP Header][TCP Header][Application Data] ← Network Layer
    ↓
[Ethernet Header][IP Header][TCP Header][Application Data][Ethernet Trailer] ← Data Link Layer
    ↓
Physical transmission as bits
```

## Enterprise Network Troubleshooting

### Systematic Layer-by-Layer Approach

#### Layer 1 Troubleshooting
```bash
# Check physical connectivity
ethtool eth0  # Check link status and speed
ip link show  # Display interface status
```

#### Layer 2 Troubleshooting  
```bash
# ARP table analysis
arp -a
# MAC address table on switches
show mac address-table
```

#### Layer 3 Troubleshooting
```bash
# Routing analysis
ip route show
traceroute 8.8.8.8
ping -c 4 8.8.8.8
```

#### Layer 4 Troubleshooting
```bash
# Port connectivity testing  
telnet google.com 80
nmap -sS -O target_ip
netstat -tulpn
```

## DevOps Integration Patterns

### Network as Code Implementation
```yaml
# Terraform: VPC with proper layered design
resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true
  
  tags = {
    Name = "production-vpc"
    Layer = "Network-L3"
  }
}

resource "aws_subnet" "private" {
  count             = length(var.availability_zones)
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.${count.index + 1}.0/24"
  availability_zone = var.availability_zones[count.index]
  
  tags = {
    Name = "private-subnet-${count.index + 1}"
    Layer = "Network-L3"
    Type = "Private"
  }
}
```

### Container Network Monitoring
```python
# Docker network inspection
import docker
import json

client = docker.from_env()

def analyze_container_networks():
    networks = client.networks.list()
    
    for network in networks:
        print(f"Network: {network.name}")
        print(f"Driver: {network.attrs['Driver']}")
        print(f"Scope: {network.attrs['Scope']}")
        
        # Analyze connected containers
        containers = network.attrs['Containers']
        for container_id, container_info in containers.items():
            print(f"  Container: {container_info['Name']}")
            print(f"  IPv4: {container_info['IPv4Address']}")
            print(f"  MAC: {container_info['MacAddress']}")

analyze_container_networks()
```

## Performance Optimization

### Network Stack Tuning
```bash
# TCP buffer optimization
echo 'net.core.rmem_max = 134217728' >> /etc/sysctl.conf
echo 'net.core.wmem_max = 134217728' >> /etc/sysctl.conf
echo 'net.ipv4.tcp_rmem = 4096 65536 134217728' >> /etc/sysctl.conf
echo 'net.ipv4.tcp_wmem = 4096 65536 134217728' >> /etc/sysctl.conf

# Apply settings
sysctl -p
```

### Application Layer Optimization
```nginx
# Nginx HTTP/2 and connection optimization
server {
    listen 443 ssl http2;
    
    # HTTP/2 push for critical resources
    http2_push /css/critical.css;
    http2_push /js/critical.js;
    
    # Connection keep-alive
    keepalive_timeout 65;
    keepalive_requests 100;
    
    # TCP optimization
    tcp_nopush on;
    tcp_nodelay on;
}
```

## Security Implementation

### Network Layer Security
```bash
# iptables rules by layer
# Layer 3 (Network) - IP filtering
iptables -A INPUT -s 10.0.0.0/8 -j ACCEPT
iptables -A INPUT -s 192.168.0.0/16 -j ACCEPT

# Layer 4 (Transport) - Port filtering  
iptables -A INPUT -p tcp --dport 22 -j ACCEPT
iptables -A INPUT -p tcp --dport 80 -j ACCEPT
iptables -A INPUT -p tcp --dport 443 -j ACCEPT

# Layer 7 (Application) - Deep packet inspection
# Implemented through specialized firewall appliances
```

## Best Practices

### Enterprise Network Design
- **Layer separation**: Clear boundaries between network layers for better troubleshooting
- **Protocol standardization**: Consistent protocol choices across environments
- **Monitoring at each layer**: Layer-specific monitoring and alerting
- **Security in depth**: Security controls at multiple layers
- **Documentation**: Clear network diagrams showing layer relationships
- **Change management**: Version-controlled network configurations

### DevOps Integration
- **Infrastructure as Code**: Network configurations in version control
- **Automated testing**: Network connectivity and performance validation
- **Monitoring integration**: Network metrics in observability platforms
- **Incident response**: Runbooks for layer-specific troubleshooting
- **Capacity planning**: Network performance trending and scaling