# Networking IP Addressing & Subnetting

## Overview

IP addressing and subnetting form the foundation of network design, enabling logical addressing, network segmentation, and efficient routing. This guide covers IPv4/IPv6 addressing, CIDR notation, VLSM implementation, and enterprise subnetting strategies essential for DevOps engineers managing cloud and on-premises infrastructure.

## IPv4 Addressing Fundamentals

### Address Structure and Classes

#### IPv4 Format
```
192.168.1.100 = 11000000.10101000.00000001.01100100
32-bit address = Network Portion + Host Portion
```

#### Traditional Class-based Addressing
```python
# IPv4 address classes and their characteristics
class IPv4Classes:
    CLASSES = {
        'A': {
            'range': '1.0.0.0 to 126.255.255.255',
            'default_mask': '255.0.0.0 (/8)',
            'networks': 126,
            'hosts_per_network': 16777214,
            'usage': 'Large organizations, ISPs'
        },
        'B': {
            'range': '128.0.0.0 to 191.255.255.255', 
            'default_mask': '255.255.0.0 (/16)',
            'networks': 16384,
            'hosts_per_network': 65534,
            'usage': 'Medium-sized organizations'
        },
        'C': {
            'range': '192.0.0.0 to 223.255.255.255',
            'default_mask': '255.255.255.0 (/24)', 
            'networks': 2097152,
            'hosts_per_network': 254,
            'usage': 'Small organizations, branch offices'
        },
        'D': {
            'range': '224.0.0.0 to 239.255.255.255',
            'usage': 'Multicast addressing'
        },
        'E': {
            'range': '240.0.0.0 to 255.255.255.255',
            'usage': 'Experimental/Reserved'
        }
    }
```

#### Reserved and Special Addresses
```python
RESERVED_RANGES = {
    'private_class_a': '10.0.0.0/8',          # RFC 1918
    'private_class_b': '172.16.0.0/12',       # RFC 1918  
    'private_class_c': '192.168.0.0/16',      # RFC 1918
    'loopback': '127.0.0.0/8',                # RFC 1122
    'link_local': '169.254.0.0/16',           # RFC 3927
    'multicast': '224.0.0.0/4',               # RFC 3171
    'broadcast': '255.255.255.255/32',        # Limited broadcast
    'this_network': '0.0.0.0/8'               # RFC 1122
}
```

## CIDR Notation and Subnetting

### CIDR (Classless Inter-Domain Routing)

```python
import ipaddress

class CIDRCalculator:
    def __init__(self, network_address):
        self.network = ipaddress.IPv4Network(network_address, strict=False)
    
    def get_network_info(self):
        return {
            'network_address': str(self.network.network_address),
            'broadcast_address': str(self.network.broadcast_address),
            'subnet_mask': str(self.network.netmask),
            'prefix_length': self.network.prefixlen,
            'total_addresses': self.network.num_addresses,
            'usable_hosts': self.network.num_addresses - 2,
            'first_host': str(self.network.network_address + 1),
            'last_host': str(self.network.broadcast_address - 1)
        }
    
    def subnet_calculator(self, new_prefix):
        """Calculate subnets with new prefix length"""
        if new_prefix <= self.network.prefixlen:
            raise ValueError("New prefix must be larger than current")
        
        subnets = list(self.network.subnets(new_prefix=new_prefix))
        return [
            {
                'subnet': str(subnet),
                'network': str(subnet.network_address),
                'broadcast': str(subnet.broadcast_address),
                'hosts': subnet.num_addresses - 2,
                'first_host': str(subnet.network_address + 1),
                'last_host': str(subnet.broadcast_address - 1)
            }
            for subnet in subnets
        ]

# Example usage
calculator = CIDRCalculator('192.168.1.0/24')
network_info = calculator.get_network_info()
print(f"Network: {network_info['network_address']}")
print(f"Hosts: {network_info['usable_hosts']}")

# Subnet into /26 networks
subnets = calculator.subnet_calculator(26)
for i, subnet in enumerate(subnets):
    print(f"Subnet {i+1}: {subnet['subnet']} ({subnet['hosts']} hosts)")
```

### Variable Length Subnet Masking (VLSM)

```python
class VLSMPlanner:
    def __init__(self, base_network):
        self.base_network = ipaddress.IPv4Network(base_network)
        self.allocated_subnets = []
        self.available_space = [self.base_network]
    
    def calculate_required_prefix(self, required_hosts):
        """Calculate prefix length needed for required hosts"""
        # Add 2 for network and broadcast addresses
        total_addresses_needed = required_hosts + 2
        
        # Find the smallest power of 2 that fits
        bits_needed = 0
        while (2 ** bits_needed) < total_addresses_needed:
            bits_needed += 1
        
        # Calculate prefix length (32 - host bits)
        prefix_length = 32 - bits_needed
        return prefix_length
    
    def allocate_subnet(self, name, required_hosts):
        """Allocate a subnet for specified number of hosts"""
        required_prefix = self.calculate_required_prefix(required_hosts)
        
        # Find the first available space that can accommodate this subnet
        for i, available_space in enumerate(self.available_space):
            if available_space.prefixlen <= required_prefix:
                try:
                    # Create subnet with required prefix
                    new_subnet = list(available_space.subnets(
                        new_prefix=required_prefix
                    ))[0]
                    
                    # Remove allocated space and add remaining space back
                    self.available_space.pop(i)
                    
                    # Add remaining subnets back to available space
                    remaining_subnets = list(available_space.subnets(
                        new_prefix=required_prefix
                    ))[1:]
                    
                    self.available_space.extend(remaining_subnets)
                    self.available_space.sort(key=lambda x: x.network_address)
                    
                    # Record the allocation
                    allocation = {
                        'name': name,
                        'subnet': str(new_subnet),
                        'required_hosts': required_hosts,
                        'available_hosts': new_subnet.num_addresses - 2,
                        'network': str(new_subnet.network_address),
                        'broadcast': str(new_subnet.broadcast_address),
                        'first_host': str(new_subnet.network_address + 1),
                        'last_host': str(new_subnet.broadcast_address - 1)
                    }
                    
                    self.allocated_subnets.append(allocation)
                    return allocation
                    
                except Exception as e:
                    continue
        
        raise ValueError(f"Cannot allocate subnet for {required_hosts} hosts")
    
    def get_allocation_summary(self):
        """Get summary of all allocations"""
        return {
            'base_network': str(self.base_network),
            'allocated_subnets': self.allocated_subnets,
            'remaining_space': [str(space) for space in self.available_space],
            'utilization': len(self.allocated_subnets)
        }

# Enterprise VLSM example
vlsm = VLSMPlanner('10.0.0.0/16')

# Allocate subnets based on requirements
requirements = [
    ('Production Web Servers', 500),
    ('Production App Servers', 200), 
    ('Production DB Servers', 50),
    ('Staging Environment', 100),
    ('Development Environment', 30),
    ('Management Network', 20),
    ('DMZ Network', 10),
    ('Point-to-Point Links', 2)
]

print("VLSM Allocation Plan:")
print("=" * 50)

for name, hosts in requirements:
    try:
        allocation = vlsm.allocate_subnet(name, hosts)
        print(f"{name:25} | {allocation['subnet']:18} | {allocation['available_hosts']:3} hosts")
    except ValueError as e:
        print(f"Failed to allocate {name}: {e}")

print("\nRemaining unallocated space:")
summary = vlsm.get_allocation_summary()
for space in summary['remaining_space']:
    print(f"  {space}")
```

## IPv6 Addressing

### IPv6 Address Structure

```python
class IPv6Analyzer:
    def __init__(self, ipv6_address):
        self.address = ipaddress.IPv6Address(ipv6_address)
        self.network = ipaddress.IPv6Network(f"{ipv6_address}/64", strict=False)
    
    def analyze_address(self):
        """Analyze IPv6 address components"""
        address_str = str(self.address)
        
        # Expand compressed address
        expanded = self.address.exploded
        
        # Identify address type
        address_type = self._identify_address_type()
        
        # Extract network and host portions (assuming /64)
        network_portion = expanded[:19]  # First 4 hextets
        host_portion = expanded[20:]     # Last 4 hextets
        
        return {
            'original': address_str,
            'expanded': expanded,
            'compressed': self.address.compressed,
            'type': address_type,
            'network_portion': network_portion,
            'host_portion': host_portion,
            'is_multicast': self.address.is_multicast,
            'is_private': self.address.is_private,
            'is_global': self.address.is_global,
            'is_link_local': self.address.is_link_local,
            'is_loopback': self.address.is_loopback
        }
    
    def _identify_address_type(self):
        """Identify IPv6 address type based on prefix"""
        if self.address.is_loopback:
            return "Loopback (::1)"
        elif self.address.is_link_local:
            return "Link Local (fe80::/10)"
        elif self.address.is_multicast:
            return "Multicast (ff00::/8)"
        elif self.address.is_private:
            return "Unique Local (fc00::/7)"
        elif self.address.is_global:
            return "Global Unicast (2000::/3)"
        else:
            return "Other/Reserved"

# IPv6 addressing examples
ipv6_examples = [
    "2001:db8:85a3::8a2e:370:7334",
    "fe80::1%eth0",
    "::1",
    "ff02::1",
    "fc00::1"
]

for addr in ipv6_examples:
    try:
        # Remove interface identifier for analysis
        clean_addr = addr.split('%')[0]
        analyzer = IPv6Analyzer(clean_addr)
        info = analyzer.analyze_address()
        
        print(f"Address: {info['original']}")
        print(f"Type: {info['type']}")
        print(f"Expanded: {info['expanded']}")
        print("-" * 40)
    except Exception as e:
        print(f"Error analyzing {addr}: {e}")
```

## Enterprise Subnetting Strategies

### Cloud Network Design with Terraform

```hcl
# vpc-subnetting.tf - AWS VPC with hierarchical subnetting
variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "Availability zones for subnet placement"
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b", "us-east-1c"]
}

# VPC Creation
resource "aws_vpc" "enterprise" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true
  
  tags = {
    Name = "enterprise-vpc"
    Environment = "production"
  }
}

# Subnet allocation following VLSM principles
locals {
  # Calculate subnet CIDRs using VLSM
  # 10.0.0.0/16 divided into /18 blocks for tiers
  
  subnet_config = {
    public = {
      cidr_newbits = 8    # /24 subnets from /16
      cidr_offset  = 0    # 10.0.0.0/24, 10.0.1.0/24, 10.0.2.0/24
    }
    private_web = {
      cidr_newbits = 6    # /22 subnets from /16  
      cidr_offset  = 16   # 10.0.16.0/22, 10.0.20.0/22, 10.0.24.0/22
    }
    private_app = {
      cidr_newbits = 6    # /22 subnets from /16
      cidr_offset  = 32   # 10.0.32.0/22, 10.0.36.0/22, 10.0.40.0/22
    }
    private_db = {
      cidr_newbits = 8    # /24 subnets from /16
      cidr_offset  = 64   # 10.0.64.0/24, 10.0.65.0/24, 10.0.66.0/24
    }
    management = {
      cidr_newbits = 8    # /24 subnets from /16
      cidr_offset  = 80   # 10.0.80.0/24, 10.0.81.0/24, 10.0.82.0/24
    }
  }
}

# Public Subnets (Internet Gateway access)
resource "aws_subnet" "public" {
  count = length(var.availability_zones)
  
  vpc_id            = aws_vpc.enterprise.id
  availability_zone = var.availability_zones[count.index]
  
  cidr_block = cidrsubnet(
    var.vpc_cidr,
    local.subnet_config.public.cidr_newbits,
    local.subnet_config.public.cidr_offset + count.index
  )
  
  map_public_ip_on_launch = true
  
  tags = {
    Name = "public-subnet-${substr(var.availability_zones[count.index], -1, 1)}"
    Type = "Public"
    Tier = "DMZ"
  }
}

# Private Web Tier Subnets
resource "aws_subnet" "private_web" {
  count = length(var.availability_zones)
  
  vpc_id            = aws_vpc.enterprise.id
  availability_zone = var.availability_zones[count.index]
  
  cidr_block = cidrsubnet(
    var.vpc_cidr,
    local.subnet_config.private_web.cidr_newbits,
    local.subnet_config.private_web.cidr_offset + count.index
  )
  
  tags = {
    Name = "private-web-${substr(var.availability_zones[count.index], -1, 1)}"
    Type = "Private"
    Tier = "Web"
  }
}

# Private Application Tier Subnets
resource "aws_subnet" "private_app" {
  count = length(var.availability_zones)
  
  vpc_id            = aws_vpc.enterprise.id
  availability_zone = var.availability_zones[count.index]
  
  cidr_block = cidrsubnet(
    var.vpc_cidr,
    local.subnet_config.private_app.cidr_newbits,
    local.subnet_config.private_app.cidr_offset + count.index
  )
  
  tags = {
    Name = "private-app-${substr(var.availability_zones[count.index], -1, 1)}"
    Type = "Private"
    Tier = "Application"
  }
}

# Private Database Tier Subnets
resource "aws_subnet" "private_db" {
  count = length(var.availability_zones)
  
  vpc_id            = aws_vpc.enterprise.id
  availability_zone = var.availability_zones[count.index]
  
  cidr_block = cidrsubnet(
    var.vpc_cidr,
    local.subnet_config.private_db.cidr_newbits,
    local.subnet_config.private_db.cidr_offset + count.index
  )
  
  tags = {
    Name = "private-db-${substr(var.availability_zones[count.index], -1, 1)}"
    Type = "Private"
    Tier = "Database"
  }
}

# Management Subnets
resource "aws_subnet" "management" {
  count = length(var.availability_zones)
  
  vpc_id            = aws_vpc.enterprise.id
  availability_zone = var.availability_zones[count.index]
  
  cidr_block = cidrsubnet(
    var.vpc_cidr,
    local.subnet_config.management.cidr_newbits,
    local.subnet_config.management.cidr_offset + count.index
  )
  
  tags = {
    Name = "management-${substr(var.availability_zones[count.index], -1, 1)}"
    Type = "Private"
    Tier = "Management"
  }
}

# Output subnet information
output "subnet_allocation" {
  description = "Subnet allocation summary"
  value = {
    vpc_cidr = var.vpc_cidr
    public_subnets = [
      for i, subnet in aws_subnet.public : {
        name = subnet.tags.Name
        cidr = subnet.cidr_block
        az   = subnet.availability_zone
      }
    ]
    private_web_subnets = [
      for i, subnet in aws_subnet.private_web : {
        name = subnet.tags.Name
        cidr = subnet.cidr_block
        az   = subnet.availability_zone
      }
    ]
    private_app_subnets = [
      for i, subnet in aws_subnet.private_app : {
        name = subnet.tags.Name
        cidr = subnet.cidr_block
        az   = subnet.availability_zone
      }
    ]
    private_db_subnets = [
      for i, subnet in aws_subnet.private_db : {
        name = subnet.tags.Name
        cidr = subnet.cidr_block
        az   = subnet.availability_zone
      }
    ]
    management_subnets = [
      for i, subnet in aws_subnet.management : {
        name = subnet.tags.Name
        cidr = subnet.cidr_block
        az   = subnet.availability_zone
      }
    ]
  }
}
```

### Kubernetes Network Policy with IP-based Rules

```yaml
# Network policy using IP addressing for precise control
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: database-tier-security
  namespace: production
spec:
  podSelector:
    matchLabels:
      tier: database
  
  policyTypes:
  - Ingress
  - Egress
  
  ingress:
  # Allow access from application tier subnets only
  - from:
    - namespaceSelector:
        matchLabels:
          name: production
    - podSelector:
        matchLabels:
          tier: application
    # Restrict to specific IP ranges
    - ipBlock:
        cidr: 10.0.32.0/22  # Application tier subnet
    - ipBlock:
        cidr: 10.0.36.0/22  # Application tier subnet AZ-B
    - ipBlock:
        cidr: 10.0.40.0/22  # Application tier subnet AZ-C
    ports:
    - protocol: TCP
      port: 5432  # PostgreSQL
    - protocol: TCP
      port: 3306  # MySQL
  
  # Allow monitoring from management network
  - from:
    - ipBlock:
        cidr: 10.0.80.0/24  # Management subnet
        except:
        - 10.0.80.100/32    # Exclude specific monitoring server
    ports:
    - protocol: TCP
      port: 9100  # Node exporter
    - protocol: TCP
      port: 9187  # PostgreSQL exporter
  
  egress:
  # Allow DNS resolution
  - to: []
    ports:
    - protocol: UDP
      port: 53
    - protocol: TCP
      port: 53
  
  # Allow backup to specific storage subnet
  - to:
    - ipBlock:
        cidr: 10.0.100.0/24  # Backup storage network
    ports:
    - protocol: TCP
      port: 443   # HTTPS for cloud storage
    - protocol: TCP
      port: 22    # SSH for backup servers

---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: web-tier-security
  namespace: production
spec:
  podSelector:
    matchLabels:
      tier: web
  
  policyTypes:
  - Ingress
  - Egress
  
  ingress:
  # Allow traffic from load balancer subnet
  - from:
    - ipBlock:
        cidr: 10.0.0.0/24   # Public subnet AZ-A
    - ipBlock:
        cidr: 10.0.1.0/24   # Public subnet AZ-B  
    - ipBlock:
        cidr: 10.0.2.0/24   # Public subnet AZ-C
    ports:
    - protocol: TCP
      port: 8080  # Application port
  
  egress:
  # Allow access to application tier
  - to:
    - ipBlock:
        cidr: 10.0.32.0/20  # All application tier subnets
    ports:
    - protocol: TCP
      port: 3000
    - protocol: TCP
      port: 8080
  
  # Allow external API calls
  - to: []
    ports:
    - protocol: TCP
      port: 443   # HTTPS
    - protocol: TCP
      port: 80    # HTTP (for redirects)
```

## IP Address Management (IPAM) Tools

### IPAM Automation with Python

```python
import ipaddress
import sqlite3
from datetime import datetime
import json

class EnterpriseIPAM:
    def __init__(self, db_path="ipam.db"):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize IPAM database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Networks table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS networks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                network_cidr TEXT UNIQUE NOT NULL,
                description TEXT,
                vlan_id INTEGER,
                environment TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # IP allocations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ip_allocations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ip_address TEXT NOT NULL,
                network_id INTEGER,
                hostname TEXT,
                mac_address TEXT,
                allocation_type TEXT,
                status TEXT DEFAULT 'allocated',
                description TEXT,
                allocated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (network_id) REFERENCES networks (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_network(self, cidr, description=None, vlan_id=None, environment=None):
        """Add a new network to IPAM"""
        try:
            network = ipaddress.IPv4Network(cidr, strict=False)
        except ValueError as e:
            return {'error': f'Invalid CIDR: {e}'}
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO networks (network_cidr, description, vlan_id, environment)
                VALUES (?, ?, ?, ?)
            ''', (str(network), description, vlan_id, environment))
            
            network_id = cursor.lastrowid
            conn.commit()
            
            return {
                'success': True,
                'network_id': network_id,
                'network': str(network),
                'total_ips': network.num_addresses,
                'usable_ips': network.num_addresses - 2 if network.prefixlen < 31 else network.num_addresses
            }
            
        except sqlite3.IntegrityError:
            return {'error': 'Network already exists'}
        finally:
            conn.close()
    
    def allocate_ip(self, network_cidr, hostname=None, mac_address=None, 
                   allocation_type='static', description=None):
        """Allocate next available IP in network"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get network ID
        cursor.execute('SELECT id FROM networks WHERE network_cidr = ?', (network_cidr,))
        network_row = cursor.fetchone()
        
        if not network_row:
            conn.close()
            return {'error': 'Network not found'}
        
        network_id = network_row[0]
        network = ipaddress.IPv4Network(network_cidr)
        
        # Get already allocated IPs
        cursor.execute('''
            SELECT ip_address FROM ip_allocations 
            WHERE network_id = ? AND status = 'allocated'
        ''', (network_id,))
        
        allocated_ips = {row[0] for row in cursor.fetchall()}
        
        # Find next available IP
        for ip in network.hosts() if network.prefixlen < 31 else network:
            if str(ip) not in allocated_ips:
                # Allocate this IP
                cursor.execute('''
                    INSERT INTO ip_allocations 
                    (ip_address, network_id, hostname, mac_address, allocation_type, description)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (str(ip), network_id, hostname, mac_address, allocation_type, description))
                
                conn.commit()
                conn.close()
                
                return {
                    'success': True,
                    'ip_address': str(ip),
                    'network': network_cidr,
                    'hostname': hostname,
                    'allocation_type': allocation_type
                }
        
        conn.close()
        return {'error': 'No available IPs in network'}
    
    def get_network_utilization(self, network_cidr):
        """Calculate network utilization"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get network info
        cursor.execute('SELECT id FROM networks WHERE network_cidr = ?', (network_cidr,))
        network_row = cursor.fetchone()
        
        if not network_row:
            conn.close()
            return {'error': 'Network not found'}
        
        network_id = network_row[0]
        network = ipaddress.IPv4Network(network_cidr)
        
        # Count allocated IPs
        cursor.execute('''
            SELECT COUNT(*) FROM ip_allocations 
            WHERE network_id = ? AND status = 'allocated'
        ''', (network_id,))
        
        allocated_count = cursor.fetchone()[0]
        conn.close()
        
        total_ips = network.num_addresses
        usable_ips = total_ips - 2 if network.prefixlen < 31 else total_ips
        utilization_percent = (allocated_count / usable_ips) * 100 if usable_ips > 0 else 0
        
        return {
            'network': network_cidr,
            'total_ips': total_ips,
            'usable_ips': usable_ips,
            'allocated_ips': allocated_count,
            'available_ips': usable_ips - allocated_count,
            'utilization_percent': round(utilization_percent, 2)
        }
    
    def generate_network_report(self):
        """Generate comprehensive network utilization report"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT network_cidr, description, vlan_id, environment
            FROM networks
            ORDER BY network_cidr
        ''')
        
        networks = cursor.fetchall()
        report = []
        
        for network_cidr, description, vlan_id, environment in networks:
            utilization = self.get_network_utilization(network_cidr)
            
            report.append({
                'network': network_cidr,
                'description': description,
                'vlan_id': vlan_id,
                'environment': environment,
                'utilization': utilization
            })
        
        conn.close()
        return report

# Example usage
ipam = EnterpriseIPAM()

# Add networks
networks = [
    ('10.0.0.0/24', 'Public DMZ', 100, 'production'),
    ('10.0.16.0/22', 'Web Tier', 200, 'production'),
    ('10.0.32.0/22', 'App Tier', 300, 'production'),
    ('10.0.64.0/24', 'DB Tier', 400, 'production'),
    ('10.0.80.0/24', 'Management', 500, 'production')
]

for cidr, desc, vlan, env in networks:
    result = ipam.add_network(cidr, desc, vlan, env)
    print(f"Added {cidr}: {result}")

# Allocate some IPs
allocations = [
    ('10.0.0.0/24', 'load-balancer-1', None, 'static', 'Primary load balancer'),
    ('10.0.0.0/24', 'load-balancer-2', None, 'static', 'Secondary load balancer'),
    ('10.0.16.0/22', 'web-server-1', None, 'static', 'Production web server'),
    ('10.0.32.0/22', 'app-server-1', None, 'static', 'Production app server'),
    ('10.0.64.0/24', 'db-primary', None, 'static', 'Primary database server')
]

for network, hostname, mac, alloc_type, desc in allocations:
    result = ipam.allocate_ip(network, hostname, mac, alloc_type, desc)
    print(f"Allocated IP: {result}")

# Generate utilization report
report = ipam.generate_network_report()
print("\nNetwork Utilization Report:")
print("=" * 80)
for network_info in report:
    util = network_info['utilization']
    print(f"{network_info['network']:15} | {network_info['description']:20} | "
          f"{util['utilization_percent']:6.1f}% | {util['allocated_ips']:3}/{util['usable_ips']:3}")
```

## Best Practices for Enterprise IP Management

### Network Segmentation Strategy
- **Hierarchical addressing** with clear organizational structure
- **VLAN alignment** with IP subnetting for consistent network design
- **Growth planning** with reserved address space for future expansion
- **Documentation** of all network allocations and their purposes

### IP Address Conservation
- **VLSM implementation** for efficient address space utilization
- **NAT configuration** for private to public address translation
- **IPv6 migration planning** for long-term address availability
- **Regular auditing** of unused address allocations

### Security Considerations
- **Private addressing** for internal networks (RFC 1918)
- **Network isolation** through proper subnet design
- **Access control lists** based on IP address ranges
- **Monitoring and logging** of IP address usage patterns

This comprehensive guide provides the foundation for effective IP addressing and subnetting in enterprise environments, with practical tools and examples for DevOps implementation.