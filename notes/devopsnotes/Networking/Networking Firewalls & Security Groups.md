# Networking Firewalls & Security Groups

## Overview

Network security through firewalls and security groups provides essential protection for infrastructure by controlling traffic flow based on defined rules. This guide covers firewall architectures, security group management, network segmentation, intrusion detection, and enterprise security implementations crucial for DevOps engineers securing cloud and on-premises environments.

## Firewall Fundamentals and Architecture

### Firewall Types and Deployment Models

```python
from enum import Enum
from dataclasses import dataclass
from typing import List, Dict, Optional, Union
import ipaddress
import json

class FirewallType(Enum):
    PACKET_FILTER = "packet_filter"
    STATEFUL = "stateful"
    APPLICATION = "application"
    PROXY = "proxy"
    NEXT_GEN = "next_generation"
    WEB_APPLICATION = "web_application"

class RuleAction(Enum):
    ALLOW = "allow"
    DENY = "deny"
    LOG = "log"
    RATE_LIMIT = "rate_limit"

class Protocol(Enum):
    TCP = "tcp"
    UDP = "udp"
    ICMP = "icmp"
    ALL = "all"

@dataclass
class FirewallRule:
    name: str
    source: Union[str, List[str]]  # IP address, CIDR, or security group
    destination: Union[str, List[str]]
    protocol: Protocol
    ports: Union[str, List[int]]  # "any" or list of ports
    action: RuleAction
    priority: int
    description: str = ""
    enabled: bool = True

@dataclass
class SecurityGroup:
    name: str
    description: str
    vpc_id: str
    ingress_rules: List[FirewallRule]
    egress_rules: List[FirewallRule]
    tags: Dict[str, str]

class EnterpriseFirewallManager:
    def __init__(self):
        self.security_groups = {}
        self.firewall_rules = []
        self.network_zones = {}
        
    def create_security_group(self, name: str, description: str, vpc_id: str) -> SecurityGroup:
        """Create a new security group"""
        sg = SecurityGroup(
            name=name,
            description=description,
            vpc_id=vpc_id,
            ingress_rules=[],
            egress_rules=[],
            tags={}
        )
        
        self.security_groups[name] = sg
        return sg
    
    def add_ingress_rule(self, sg_name: str, rule: FirewallRule):
        """Add ingress rule to security group"""
        if sg_name in self.security_groups:
            self.security_groups[sg_name].ingress_rules.append(rule)
            return f"Added ingress rule '{rule.name}' to {sg_name}"
        return f"Security group {sg_name} not found"
    
    def add_egress_rule(self, sg_name: str, rule: FirewallRule):
        """Add egress rule to security group"""
        if sg_name in self.security_groups:
            self.security_groups[sg_name].egress_rules.append(rule)
            return f"Added egress rule '{rule.name}' to {sg_name}"
        return f"Security group {sg_name} not found"
    
    def create_tiered_security_groups(self, vpc_id: str):
        """Create enterprise tiered security groups"""
        
        # Web Tier Security Group
        web_sg = self.create_security_group(
            "web-tier-sg",
            "Security group for web tier servers",
            vpc_id
        )
        
        # Web tier ingress rules
        web_rules = [
            FirewallRule(
                name="allow-http",
                source="0.0.0.0/0",
                destination="web-tier-sg",
                protocol=Protocol.TCP,
                ports=[80],
                action=RuleAction.ALLOW,
                priority=100,
                description="Allow HTTP traffic from internet"
            ),
            FirewallRule(
                name="allow-https",
                source="0.0.0.0/0", 
                destination="web-tier-sg",
                protocol=Protocol.TCP,
                ports=[443],
                action=RuleAction.ALLOW,
                priority=101,
                description="Allow HTTPS traffic from internet"
            ),
            FirewallRule(
                name="allow-ssh-bastion",
                source="bastion-sg",
                destination="web-tier-sg",
                protocol=Protocol.TCP,
                ports=[22],
                action=RuleAction.ALLOW,
                priority=110,
                description="Allow SSH from bastion host"
            )
        ]
        
        for rule in web_rules:
            self.add_ingress_rule("web-tier-sg", rule)
        
        # Application Tier Security Group  
        app_sg = self.create_security_group(
            "app-tier-sg",
            "Security group for application tier servers",
            vpc_id
        )
        
        app_rules = [
            FirewallRule(
                name="allow-app-from-web",
                source="web-tier-sg",
                destination="app-tier-sg", 
                protocol=Protocol.TCP,
                ports=[8080, 3000, 5000],
                action=RuleAction.ALLOW,
                priority=100,
                description="Allow application traffic from web tier"
            ),
            FirewallRule(
                name="allow-ssh-bastion",
                source="bastion-sg",
                destination="app-tier-sg",
                protocol=Protocol.TCP,
                ports=[22],
                action=RuleAction.ALLOW,
                priority=110,
                description="Allow SSH from bastion host"
            )
        ]
        
        for rule in app_rules:
            self.add_ingress_rule("app-tier-sg", rule)
        
        # Database Tier Security Group
        db_sg = self.create_security_group(
            "db-tier-sg", 
            "Security group for database tier servers",
            vpc_id
        )
        
        db_rules = [
            FirewallRule(
                name="allow-mysql-from-app",
                source="app-tier-sg",
                destination="db-tier-sg",
                protocol=Protocol.TCP,
                ports=[3306],
                action=RuleAction.ALLOW,
                priority=100,
                description="Allow MySQL from application tier"
            ),
            FirewallRule(
                name="allow-postgres-from-app",
                source="app-tier-sg", 
                destination="db-tier-sg",
                protocol=Protocol.TCP,
                ports=[5432],
                action=RuleAction.ALLOW,
                priority=101,
                description="Allow PostgreSQL from application tier"
            ),
            FirewallRule(
                name="allow-redis-from-app",
                source="app-tier-sg",
                destination="db-tier-sg",
                protocol=Protocol.TCP,
                ports=[6379],
                action=RuleAction.ALLOW,
                priority=102,
                description="Allow Redis from application tier"
            ),
            FirewallRule(
                name="allow-ssh-bastion",
                source="bastion-sg",
                destination="db-tier-sg",
                protocol=Protocol.TCP,
                ports=[22],
                action=RuleAction.ALLOW,
                priority=110,
                description="Allow SSH from bastion host"
            )
        ]
        
        for rule in db_rules:
            self.add_ingress_rule("db-tier-sg", rule)
        
        # Bastion Host Security Group
        bastion_sg = self.create_security_group(
            "bastion-sg",
            "Security group for bastion host",
            vpc_id
        )
        
        bastion_rule = FirewallRule(
            name="allow-ssh-admin",
            source="203.0.113.0/24",  # Admin IP range
            destination="bastion-sg",
            protocol=Protocol.TCP,
            ports=[22],
            action=RuleAction.ALLOW,
            priority=100,
            description="Allow SSH from admin networks"
        )
        
        self.add_ingress_rule("bastion-sg", bastion_rule)
        
        return {
            "web_sg": web_sg,
            "app_sg": app_sg, 
            "db_sg": db_sg,
            "bastion_sg": bastion_sg
        }
    
    def analyze_security_posture(self):
        """Analyze security posture of all security groups"""
        analysis = {
            "total_groups": len(self.security_groups),
            "security_issues": [],
            "recommendations": [],
            "compliance_score": 0
        }
        
        total_score = 0
        max_score = 0
        
        for sg_name, sg in self.security_groups.items():
            # Check for overly permissive rules
            for rule in sg.ingress_rules:
                max_score += 1
                
                if rule.source == "0.0.0.0/0" and rule.protocol == Protocol.TCP:
                    if 22 in rule.ports or rule.ports == "any":
                        analysis["security_issues"].append(
                            f"{sg_name}: SSH (port 22) open to internet in rule '{rule.name}'"
                        )
                    elif 3389 in rule.ports:
                        analysis["security_issues"].append(
                            f"{sg_name}: RDP (port 3389) open to internet in rule '{rule.name}'"
                        )
                    elif rule.ports == "any":
                        analysis["security_issues"].append(
                            f"{sg_name}: All ports open to internet in rule '{rule.name}'"
                        )
                    else:
                        total_score += 0.5  # Partially secure
                else:
                    total_score += 1  # Secure rule
            
            # Check for unused security groups
            if not sg.ingress_rules and not sg.egress_rules:
                analysis["recommendations"].append(
                    f"Security group '{sg_name}' has no rules - consider removing if unused"
                )
        
        analysis["compliance_score"] = int((total_score / max_score) * 100) if max_score > 0 else 100
        
        return analysis

# Example usage
firewall_mgr = EnterpriseFirewallManager()

# Create tiered security groups
vpc_id = "vpc-12345678"
security_groups = firewall_mgr.create_tiered_security_groups(vpc_id)

print("Enterprise Security Groups Created:")
print("=" * 40)
for name, sg in security_groups.items():
    print(f"{name}: {sg.description}")
    print(f"  Ingress rules: {len(sg.ingress_rules)}")
    print(f"  Egress rules: {len(sg.egress_rules)}")

# Analyze security posture
analysis = firewall_mgr.analyze_security_posture()
print(f"\nSecurity Posture Analysis:")
print(f"Compliance Score: {analysis['compliance_score']}%")
print(f"Security Issues: {len(analysis['security_issues'])}")
for issue in analysis['security_issues']:
    print(f"  ⚠️  {issue}")
```

## AWS Security Groups Management

### Terraform Security Groups Configuration

```hcl
# security-groups.tf - Comprehensive AWS Security Groups

variable "vpc_id" {
  description = "VPC ID for security groups"
  type        = string
}

variable "allowed_cidr_blocks" {
  description = "CIDR blocks allowed for admin access"
  type        = list(string)
  default     = ["203.0.113.0/24"]
}

# Bastion Host Security Group
resource "aws_security_group" "bastion" {
  name_prefix = "bastion-sg"
  vpc_id      = var.vpc_id
  description = "Security group for bastion host"

  # SSH access from admin networks only
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = var.allowed_cidr_blocks
    description = "SSH access from admin networks"
  }

  # Outbound internet access for updates
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "All outbound traffic"
  }

  tags = {
    Name = "bastion-security-group"
    Tier = "Management"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Load Balancer Security Group
resource "aws_security_group" "alb" {
  name_prefix = "alb-sg"
  vpc_id      = var.vpc_id
  description = "Security group for Application Load Balancer"

  # HTTP access from internet
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "HTTP access from internet"
  }

  # HTTPS access from internet
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "HTTPS access from internet"
  }

  # Outbound to web tier
  egress {
    from_port       = 80
    to_port         = 80
    protocol        = "tcp"
    security_groups = [aws_security_group.web_tier.id]
    description     = "HTTP to web tier"
  }

  egress {
    from_port       = 443
    to_port         = 443
    protocol        = "tcp"
    security_groups = [aws_security_group.web_tier.id]
    description     = "HTTPS to web tier"
  }

  tags = {
    Name = "alb-security-group"
    Tier = "Load Balancer"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Web Tier Security Group
resource "aws_security_group" "web_tier" {
  name_prefix = "web-tier-sg"
  vpc_id      = var.vpc_id
  description = "Security group for web tier instances"

  # HTTP from Load Balancer
  ingress {
    from_port       = 80
    to_port         = 80
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
    description     = "HTTP from load balancer"
  }

  # HTTPS from Load Balancer
  ingress {
    from_port       = 80
    to_port         = 80
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
    description     = "HTTPS from load balancer"
  }

  # SSH from bastion
  ingress {
    from_port       = 22
    to_port         = 22
    protocol        = "tcp"
    security_groups = [aws_security_group.bastion.id]
    description     = "SSH from bastion host"
  }

  # Outbound to app tier
  egress {
    from_port       = 8080
    to_port         = 8080
    protocol        = "tcp"
    security_groups = [aws_security_group.app_tier.id]
    description     = "Application traffic to app tier"
  }

  # Outbound internet for updates
  egress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "HTTP for package updates"
  }

  egress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "HTTPS for package updates"
  }

  tags = {
    Name = "web-tier-security-group"
    Tier = "Web"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Application Tier Security Group
resource "aws_security_group" "app_tier" {
  name_prefix = "app-tier-sg"
  vpc_id      = var.vpc_id
  description = "Security group for application tier instances"

  # Application traffic from web tier
  ingress {
    from_port       = 8080
    to_port         = 8080
    protocol        = "tcp"
    security_groups = [aws_security_group.web_tier.id]
    description     = "Application traffic from web tier"
  }

  # Additional app ports
  ingress {
    from_port       = 3000
    to_port         = 3000
    protocol        = "tcp"
    security_groups = [aws_security_group.web_tier.id]
    description     = "Node.js application from web tier"
  }

  ingress {
    from_port       = 5000
    to_port         = 5000
    protocol        = "tcp"
    security_groups = [aws_security_group.web_tier.id]
    description     = "Python/Flask application from web tier"
  }

  # SSH from bastion
  ingress {
    from_port       = 22
    to_port         = 22
    protocol        = "tcp"
    security_groups = [aws_security_group.bastion.id]
    description     = "SSH from bastion host"
  }

  # Outbound to database tier
  egress {
    from_port       = 3306
    to_port         = 3306
    protocol        = "tcp"
    security_groups = [aws_security_group.db_tier.id]
    description     = "MySQL to database tier"
  }

  egress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.db_tier.id]
    description     = "PostgreSQL to database tier"
  }

  egress {
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [aws_security_group.db_tier.id]
    description     = "Redis to database tier"
  }

  # Outbound internet for API calls and updates
  egress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "HTTP for external APIs and updates"
  }

  egress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "HTTPS for external APIs and updates"
  }

  tags = {
    Name = "app-tier-security-group"
    Tier = "Application"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Database Tier Security Group
resource "aws_security_group" "db_tier" {
  name_prefix = "db-tier-sg"
  vpc_id      = var.vpc_id
  description = "Security group for database tier instances"

  # MySQL from app tier
  ingress {
    from_port       = 3306
    to_port         = 3306
    protocol        = "tcp"
    security_groups = [aws_security_group.app_tier.id]
    description     = "MySQL from application tier"
  }

  # PostgreSQL from app tier
  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.app_tier.id]
    description     = "PostgreSQL from application tier"
  }

  # Redis from app tier
  ingress {
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [aws_security_group.app_tier.id]
    description     = "Redis from application tier"
  }

  # SSH from bastion for maintenance
  ingress {
    from_port       = 22
    to_port         = 22
    protocol        = "tcp"
    security_groups = [aws_security_group.bastion.id]
    description     = "SSH from bastion host"
  }

  # Outbound for database replication and backups
  egress {
    from_port   = 3306
    to_port     = 3306
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/8"]  # Internal networks only
    description = "MySQL replication"
  }

  egress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/8"]  # Internal networks only
    description = "PostgreSQL replication"
  }

  # HTTPS for managed database service communications
  egress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "HTTPS for managed service communications"
  }

  tags = {
    Name = "db-tier-security-group"
    Tier = "Database"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Monitoring Security Group
resource "aws_security_group" "monitoring" {
  name_prefix = "monitoring-sg"
  vpc_id      = var.vpc_id
  description = "Security group for monitoring and logging instances"

  # Grafana web interface
  ingress {
    from_port       = 3000
    to_port         = 3000
    protocol        = "tcp"
    security_groups = [aws_security_group.bastion.id]
    description     = "Grafana web interface from bastion"
  }

  # Prometheus from all tiers
  ingress {
    from_port       = 9090
    to_port         = 9090
    protocol        = "tcp"
    security_groups = [
      aws_security_group.web_tier.id,
      aws_security_group.app_tier.id,
      aws_security_group.db_tier.id
    ]
    description = "Prometheus metrics collection"
  }

  # Node exporter from all tiers
  ingress {
    from_port       = 9100
    to_port         = 9100
    protocol        = "tcp"
    security_groups = [
      aws_security_group.web_tier.id,
      aws_security_group.app_tier.id,
      aws_security_group.db_tier.id
    ]
    description = "Node exporter metrics"
  }

  # SSH from bastion
  ingress {
    from_port       = 22
    to_port         = 22
    protocol        = "tcp"
    security_groups = [aws_security_group.bastion.id]
    description     = "SSH from bastion host"
  }

  # Outbound for alerting and external integrations
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "All outbound for monitoring integrations"
  }

  tags = {
    Name = "monitoring-security-group"
    Tier = "Monitoring"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Output security group IDs
output "security_group_ids" {
  description = "Map of security group names to IDs"
  value = {
    bastion    = aws_security_group.bastion.id
    alb        = aws_security_group.alb.id
    web_tier   = aws_security_group.web_tier.id
    app_tier   = aws_security_group.app_tier.id
    db_tier    = aws_security_group.db_tier.id
    monitoring = aws_security_group.monitoring.id
  }
}
```

## Iptables Firewall Configuration

### Advanced Iptables Rules Management

```bash
#!/bin/bash
# enterprise-firewall.sh - Enterprise iptables configuration

set -euo pipefail

# Configuration variables
LOG_FILE="/var/log/firewall-setup.log"
BACKUP_DIR="/etc/iptables/backup"
WEB_PORTS="80,443"
SSH_PORT="22"
DB_PORTS="3306,5432,6379"
MONITORING_PORTS="9090,9100,9187"

# Network definitions
DMZ_NETWORK="10.0.0.0/24"
WEB_NETWORK="10.0.16.0/22"
APP_NETWORK="10.0.32.0/22"
DB_NETWORK="10.0.64.0/24"
MGMT_NETWORK="10.0.80.0/24"
ADMIN_NETWORKS="203.0.113.0/24,198.51.100.0/24"

echo "Setting up Enterprise Firewall Rules"
echo "====================================="

# Logging function
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# Backup existing rules
backup_rules() {
    mkdir -p "$BACKUP_DIR"
    iptables-save > "$BACKUP_DIR/iptables-backup-$(date +%Y%m%d-%H%M%S).rules"
    log "Existing iptables rules backed up"
}

# Flush existing rules
flush_rules() {
    log "Flushing existing iptables rules"
    iptables -F
    iptables -X
    iptables -Z
    iptables -t nat -F
    iptables -t nat -X
    iptables -t mangle -F
    iptables -t mangle -X
}

# Set default policies
set_default_policies() {
    log "Setting default policies"
    iptables -P INPUT DROP
    iptables -P FORWARD DROP
    iptables -P OUTPUT ACCEPT
}

# Basic security rules
basic_security_rules() {
    log "Configuring basic security rules"
    
    # Allow loopback
    iptables -A INPUT -i lo -j ACCEPT
    iptables -A OUTPUT -o lo -j ACCEPT
    
    # Allow established and related connections
    iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT
    iptables -A FORWARD -m state --state ESTABLISHED,RELATED -j ACCEPT
    
    # Drop invalid packets
    iptables -A INPUT -m state --state INVALID -j DROP
    iptables -A FORWARD -m state --state INVALID -j DROP
    
    # Anti-spoofing rules
    iptables -A INPUT -s 127.0.0.0/8 ! -i lo -j DROP
    iptables -A INPUT -s 0.0.0.0/8 -j DROP
    iptables -A INPUT -s 224.0.0.0/3 -j DROP
    
    # Rate limiting for SSH (prevent brute force)
    iptables -A INPUT -p tcp --dport "$SSH_PORT" -m state --state NEW -m recent --set --name SSH
    iptables -A INPUT -p tcp --dport "$SSH_PORT" -m state --state NEW -m recent --update --seconds 60 --hitcount 4 --name SSH -j LOG --log-prefix "SSH_BRUTE_FORCE: "
    iptables -A INPUT -p tcp --dport "$SSH_PORT" -m state --state NEW -m recent --update --seconds 60 --hitcount 4 --name SSH -j DROP
}

# DMZ tier rules (Load balancers, reverse proxies)
dmz_tier_rules() {
    log "Configuring DMZ tier rules"
    
    # Allow HTTP/HTTPS from internet
    iptables -A INPUT -p tcp -m multiport --dports "$WEB_PORTS" -s 0.0.0.0/0 -m state --state NEW -j ACCEPT
    
    # Allow SSH from admin networks only
    for admin_net in $(echo "$ADMIN_NETWORKS" | tr ',' ' '); do
        iptables -A INPUT -p tcp --dport "$SSH_PORT" -s "$admin_net" -m state --state NEW -j ACCEPT
    done
    
    # Forward HTTP/HTTPS to web tier
    iptables -A FORWARD -p tcp -m multiport --dports "$WEB_PORTS" -s 0.0.0.0/0 -d "$WEB_NETWORK" -m state --state NEW -j ACCEPT
    
    # Log dropped packets in DMZ
    iptables -A INPUT -j LOG --log-prefix "DMZ_DROP: " --log-level 4
    iptables -A FORWARD -j LOG --log-prefix "DMZ_FORWARD_DROP: " --log-level 4
}

# Web tier rules
web_tier_rules() {
    log "Configuring Web tier rules"
    
    # Allow HTTP/HTTPS from DMZ
    iptables -A INPUT -p tcp -m multiport --dports "$WEB_PORTS" -s "$DMZ_NETWORK" -d "$WEB_NETWORK" -m state --state NEW -j ACCEPT
    
    # Allow SSH from management network
    iptables -A INPUT -p tcp --dport "$SSH_PORT" -s "$MGMT_NETWORK" -d "$WEB_NETWORK" -m state --state NEW -j ACCEPT
    
    # Forward to application tier
    iptables -A FORWARD -p tcp -m multiport --dports "8080,3000,5000" -s "$WEB_NETWORK" -d "$APP_NETWORK" -m state --state NEW -j ACCEPT
    
    # Allow monitoring
    iptables -A INPUT -p tcp -m multiport --dports "$MONITORING_PORTS" -s "$MGMT_NETWORK" -d "$WEB_NETWORK" -m state --state NEW -j ACCEPT
}

# Application tier rules
app_tier_rules() {
    log "Configuring Application tier rules"
    
    # Allow application ports from web tier
    iptables -A INPUT -p tcp -m multiport --dports "8080,3000,5000" -s "$WEB_NETWORK" -d "$APP_NETWORK" -m state --state NEW -j ACCEPT
    
    # Allow SSH from management network
    iptables -A INPUT -p tcp --dport "$SSH_PORT" -s "$MGMT_NETWORK" -d "$APP_NETWORK" -m state --state NEW -j ACCEPT
    
    # Forward to database tier
    iptables -A FORWARD -p tcp -m multiport --dports "$DB_PORTS" -s "$APP_NETWORK" -d "$DB_NETWORK" -m state --state NEW -j ACCEPT
    
    # Allow monitoring
    iptables -A INPUT -p tcp -m multiport --dports "$MONITORING_PORTS" -s "$MGMT_NETWORK" -d "$APP_NETWORK" -m state --state NEW -j ACCEPT
}

# Database tier rules
db_tier_rules() {
    log "Configuring Database tier rules"
    
    # Allow database ports from application tier only
    iptables -A INPUT -p tcp -m multiport --dports "$DB_PORTS" -s "$APP_NETWORK" -d "$DB_NETWORK" -m state --state NEW -j ACCEPT
    
    # Allow SSH from management network
    iptables -A INPUT -p tcp --dport "$SSH_PORT" -s "$MGMT_NETWORK" -d "$DB_NETWORK" -m state --state NEW -j ACCEPT
    
    # Allow database monitoring
    iptables -A INPUT -p tcp -m multiport --dports "$MONITORING_PORTS,9187" -s "$MGMT_NETWORK" -d "$DB_NETWORK" -m state --state NEW -j ACCEPT
    
    # Log database access attempts
    iptables -A INPUT -p tcp -m multiport --dports "$DB_PORTS" -j LOG --log-prefix "DB_ACCESS: " --log-level 6
}

# Management network rules
management_tier_rules() {
    log "Configuring Management tier rules"
    
    # Allow SSH from admin networks
    for admin_net in $(echo "$ADMIN_NETWORKS" | tr ',' ' '); do
        iptables -A INPUT -p tcp --dport "$SSH_PORT" -s "$admin_net" -d "$MGMT_NETWORK" -m state --state NEW -j ACCEPT
    done
    
    # Allow monitoring tools (Grafana, Prometheus, etc.)
    iptables -A INPUT -p tcp -m multiport --dports "3000,9090,9093" -s "$ADMIN_NETWORKS" -d "$MGMT_NETWORK" -m state --state NEW -j ACCEPT
    
    # Allow SNMP monitoring
    iptables -A INPUT -p udp --dport 161 -s "$MGMT_NETWORK" -j ACCEPT
}

# NAT rules for outbound internet access
nat_rules() {
    log "Configuring NAT rules"
    
    # Enable IP forwarding
    echo 1 > /proc/sys/net/ipv4/ip_forward
    echo "net.ipv4.ip_forward=1" >> /etc/sysctl.conf
    
    # NAT for outbound internet access
    iptables -t nat -A POSTROUTING -s "$WEB_NETWORK" -o eth0 -j MASQUERADE
    iptables -t nat -A POSTROUTING -s "$APP_NETWORK" -o eth0 -j MASQUERADE
    iptables -t nat -A POSTROUTING -s "$MGMT_NETWORK" -o eth0 -j MASQUERADE
    
    # Port forwarding for load balancer
    iptables -t nat -A PREROUTING -p tcp --dport 80 -j DNAT --to-destination 10.0.0.10:80
    iptables -t nat -A PREROUTING -p tcp --dport 443 -j DNAT --to-destination 10.0.0.10:443
}

# DDoS protection rules
ddos_protection() {
    log "Configuring DDoS protection rules"
    
    # Limit new TCP connections per IP
    iptables -A INPUT -p tcp --syn -m limit --limit 1/s --limit-burst 3 -j ACCEPT
    iptables -A INPUT -p tcp --syn -j DROP
    
    # Limit ping requests
    iptables -A INPUT -p icmp --icmp-type echo-request -m limit --limit 1/s --limit-burst 3 -j ACCEPT
    iptables -A INPUT -p icmp --icmp-type echo-request -j DROP
    
    # Protect against port scanning
    iptables -A INPUT -m recent --name portscan --rcheck --seconds 86400 -j DROP
    iptables -A FORWARD -m recent --name portscan --rcheck --seconds 86400 -j DROP
    
    # Drop packets from blacklisted IPs
    iptables -A INPUT -m recent --name blacklist --rcheck --seconds 3600 -j DROP
}

# Logging and monitoring rules
logging_rules() {
    log "Configuring logging rules"
    
    # Log all dropped packets (with rate limiting)
    iptables -A INPUT -m limit --limit 5/min -j LOG --log-prefix "IPTABLES_DROPPED: "
    iptables -A FORWARD -m limit --limit 5/min -j LOG --log-prefix "IPTABLES_FORWARD_DROPPED: "
    
    # Log new SSH connections
    iptables -A INPUT -p tcp --dport "$SSH_PORT" -m state --state NEW -j LOG --log-prefix "SSH_CONNECTION: " --log-level 6
    
    # Log new web connections (with rate limiting)
    iptables -A INPUT -p tcp -m multiport --dports "$WEB_PORTS" -m state --state NEW -m limit --limit 10/min -j LOG --log-prefix "WEB_CONNECTION: " --log-level 6
}

# Save rules
save_rules() {
    log "Saving iptables rules"
    
    # Save rules for different distributions
    if command -v iptables-save > /dev/null; then
        if [[ -f /etc/redhat-release ]]; then
            iptables-save > /etc/sysconfig/iptables
            systemctl enable iptables
        elif [[ -f /etc/debian_version ]]; then
            iptables-save > /etc/iptables/rules.v4
            systemctl enable netfilter-persistent
        fi
    fi
}

# Create monitoring script
create_monitoring_script() {
    cat > /usr/local/bin/firewall-monitor << 'EOF'
#!/bin/bash
# Firewall monitoring script

LOG_FILE="/var/log/firewall-monitor.log"

# Function to check dropped packets
check_dropped_packets() {
    dropped_count=$(iptables -L -n -v | grep "DROP" | awk '{sum += $1} END {print sum+0}')
    echo "$(date): Dropped packets in last check: $dropped_count" >> "$LOG_FILE"
    
    if [ "$dropped_count" -gt 1000 ]; then
        echo "High number of dropped packets detected: $dropped_count" | mail -s "Firewall Alert" admin@company.com
    fi
}

# Function to check active connections
check_connections() {
    active_connections=$(netstat -an | grep ESTABLISHED | wc -l)
    echo "$(date): Active connections: $active_connections" >> "$LOG_FILE"
}

# Function to analyze logs for attacks
analyze_logs() {
    # Check for brute force attempts
    ssh_attacks=$(grep "SSH_BRUTE_FORCE" /var/log/messages | tail -100 | wc -l)
    if [ "$ssh_attacks" -gt 10 ]; then
        echo "SSH brute force attacks detected: $ssh_attacks attempts" | mail -s "Security Alert" admin@company.com
    fi
}

# Run checks
check_dropped_packets
check_connections
analyze_logs

# Cleanup old logs
find /var/log -name "firewall-*.log" -mtime +30 -delete
EOF

    chmod +x /usr/local/bin/firewall-monitor
    
    # Add to crontab
    (crontab -l 2>/dev/null; echo "*/5 * * * * /usr/local/bin/firewall-monitor") | crontab -
}

# Main execution
main() {
    log "Starting Enterprise Firewall Setup"
    
    backup_rules
    flush_rules
    set_default_policies
    basic_security_rules
    dmz_tier_rules
    web_tier_rules
    app_tier_rules
    db_tier_rules
    management_tier_rules
    nat_rules
    ddos_protection
    logging_rules
    save_rules
    create_monitoring_script
    
    log "Enterprise Firewall Setup Complete"
    
    # Display rules summary
    echo ""
    echo "Firewall Rules Summary:"
    echo "======================"
    iptables -L -n --line-numbers | head -50
    
    echo ""
    echo "NAT Rules:"
    echo "=========="
    iptables -t nat -L -n --line-numbers
}

# Execute main function
main "$@"
```

## Web Application Firewall (WAF) Configuration

### CloudFlare WAF Rules with Terraform

```hcl
# cloudflare-waf.tf - CloudFlare WAF configuration

terraform {
  required_providers {
    cloudflare = {
      source  = "cloudflare/cloudflare"
      version = "~> 4.0"
    }
  }
}

variable "zone_id" {
  description = "CloudFlare Zone ID"
  type        = string
}

variable "domain" {
  description = "Domain name"
  type        = string
  default     = "example-company.com"
}

# Rate limiting rule for API endpoints
resource "cloudflare_rate_limit" "api_rate_limit" {
  zone_id = var.zone_id
  
  threshold = 100
  period    = 60
  
  match {
    request {
      url_pattern = "${var.domain}/api/*"
      schemes     = ["HTTP", "HTTPS"]
      methods     = ["GET", "POST", "PUT", "DELETE"]
    }
  }
  
  action {
    mode    = "simulate"  # Change to "ban" for enforcement
    timeout = 300
    
    response {
      content_type = "application/json"
      body         = jsonencode({
        error = "Rate limit exceeded"
        retry_after = 300
      })
    }
  }
  
  disabled = false
  description = "Rate limiting for API endpoints"
}

# DDoS protection rules
resource "cloudflare_zone_settings_override" "security_settings" {
  zone_id = var.zone_id
  
  settings {
    # Security level
    security_level = "medium"
    
    # Challenge passage
    challenge_ttl = 1800
    
    # Browser integrity check
    browser_check = "on"
    
    # DDoS protection
    ddos_protection = "on"
    
    # Bot fight mode
    bot_fight_mode = true
    
    # SSL/TLS settings
    ssl = "strict"
    always_use_https = "on"
    min_tls_version = "1.2"
    tls_1_3 = "on"
    
    # HSTS settings
    security_header {
      enabled = true
      max_age = 31536000
      include_subdomains = true
      preload = true
    }
  }
}

# Custom WAF rules
resource "cloudflare_ruleset" "waf_custom_rules" {
  zone_id = var.zone_id
  name    = "Custom WAF Rules"
  kind    = "zone"
  phase   = "http_request_firewall_custom"
  
  # Block SQL injection attempts
  rules {
    action = "block"
    enabled = true
    description = "Block SQL injection attempts"
    
    expression = "(lower(http.request.uri.query) contains \"union select\") or (lower(http.request.uri.query) contains \"' or '1'='1\") or (lower(http.request.uri.query) contains \"drop table\") or (lower(http.request.body) contains \"union select\") or (lower(http.request.body) contains \"' or '1'='1\") or (lower(http.request.body) contains \"drop table\")"
    
    action_parameters {
      response {
        status_code = 403
        content = "Access Denied - Security Policy Violation"
        content_type = "text/plain"
      }
    }
  }
  
  # Block XSS attempts
  rules {
    action = "block"
    enabled = true
    description = "Block XSS attempts"
    
    expression = "(lower(http.request.uri.query) contains \"<script\") or (lower(http.request.uri.query) contains \"javascript:\") or (lower(http.request.uri.query) contains \"onload=\") or (lower(http.request.body) contains \"<script\") or (lower(http.request.body) contains \"javascript:\") or (lower(http.request.body) contains \"onload=\")"
    
    action_parameters {
      response {
        status_code = 403
        content = "Access Denied - XSS Detected"
        content_type = "text/plain"
      }
    }
  }
  
  # Block requests from known bad user agents
  rules {
    action = "block"
    enabled = true
    description = "Block malicious user agents"
    
    expression = "(lower(http.user_agent) contains \"sqlmap\") or (lower(http.user_agent) contains \"nikto\") or (lower(http.user_agent) contains \"nessus\") or (lower(http.user_agent) contains \"masscan\") or (lower(http.user_agent) contains \"nmap\")"
    
    action_parameters {
      response {
        status_code = 403
        content = "Access Denied - Suspicious User Agent"
        content_type = "text/plain"
      }
    }
  }
  
  # Geographic restrictions
  rules {
    action = "block"
    enabled = true
    description = "Block access from restricted countries"
    
    expression = "(ip.geoip.country in {\"CN\" \"RU\" \"KP\" \"IR\"})"
    
    action_parameters {
      response {
        status_code = 403
        content = "Access not permitted from your location"
        content_type = "text/plain"
      }
    }
  }
  
  # Challenge suspicious requests
  rules {
    action = "challenge"
    enabled = true
    description = "Challenge requests without common headers"
    
    expression = "(not http.request.headers[\"accept\"][0] or not http.request.headers[\"accept-language\"][0] or not http.request.headers[\"accept-encoding\"][0]) and (http.request.method eq \"GET\")"
  }
  
  # Rate limit admin areas
  rules {
    action = "block"
    enabled = true
    description = "Strict rate limiting for admin areas"
    
    expression = "(http.request.uri.path contains \"/admin\") and (rate(60s) > 10)"
    
    action_parameters {
      response {
        status_code = 429
        content = "Rate limit exceeded for administrative area"
        content_type = "text/plain"
      }
    }
  }
}

# Custom firewall rules for specific applications
resource "cloudflare_filter" "wordpress_security" {
  zone_id = var.zone_id
  description = "WordPress security filter"
  expression = "(http.request.uri.path contains \"/wp-admin\" or http.request.uri.path contains \"/wp-login.php\") and ip.geoip.country ne \"US\""
}

resource "cloudflare_firewall_rule" "block_wordpress_international" {
  zone_id = var.zone_id
  description = "Block WordPress admin access from outside US"
  filter_id = cloudflare_filter.wordpress_security.id
  action = "block"
  priority = 1000
}

# Access rules for known good IPs
resource "cloudflare_access_rule" "office_ips" {
  zone_id = var.zone_id
  mode = "whitelist"
  configuration {
    target = "ip"
    value = "203.0.113.0/24"  # Office IP range
  }
  notes = "Office IP range - always allow"
}

# Bot management
resource "cloudflare_bot_management" "bot_config" {
  zone_id = var.zone_id
  enable_js = true
  fight_mode = true
  using_latest_model = true
}

# Analytics and logging
resource "cloudflare_logpush_job" "security_events" {
  enabled = true
  zone_id = var.zone_id
  name = "security-events-log"
  logpull_options = "fields=ClientIP,ClientRequestHost,ClientRequestMethod,ClientRequestURI,EdgeStartTimestamp,EdgeEndTimestamp,EdgeResponseStatus,SecurityLevel,WAFAction,WAFMatchedVar,WAFProfile,WAFRuleID,WAFRuleMessage&timestamps=rfc3339"
  destination_conf = "s3://security-logs-bucket/cloudflare-waf/?region=us-east-1"
}

# Output configuration
output "waf_configuration" {
  value = {
    rate_limits = [cloudflare_rate_limit.api_rate_limit.id]
    security_level = cloudflare_zone_settings_override.security_settings.settings[0].security_level
    custom_rules_count = length(cloudflare_ruleset.waf_custom_rules.rules)
    bot_management_enabled = cloudflare_bot_management.bot_config.enable_js
  }
}
```

## Network Intrusion Detection System (NIDS)

### Suricata IDS Configuration

```python
import yaml
import subprocess
import json
import time
from datetime import datetime
import sqlite3
import re

class SuricataManager:
    def __init__(self, config_path="/etc/suricata/suricata.yaml"):
        self.config_path = config_path
        self.rules_dir = "/etc/suricata/rules"
        self.log_dir = "/var/log/suricata"
        self.db_path = "/var/lib/suricata/alerts.db"
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database for alert storage"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                signature TEXT NOT NULL,
                classification TEXT,
                priority INTEGER,
                source_ip TEXT,
                source_port INTEGER,
                dest_ip TEXT,
                dest_port INTEGER,
                protocol TEXT,
                raw_alert TEXT,
                processed BOOLEAN DEFAULT FALSE
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def generate_suricata_config(self):
        """Generate comprehensive Suricata configuration"""
        
        config = {
            'vars': {
                'address-groups': {
                    'HOME_NET': '[10.0.0.0/8,192.168.0.0/16,172.16.0.0/12]',
                    'EXTERNAL_NET': '!$HOME_NET',
                    'HTTP_SERVERS': '$HOME_NET',
                    'SMTP_SERVERS': '$HOME_NET',
                    'SQL_SERVERS': '$HOME_NET',
                    'DNS_SERVERS': '$HOME_NET',
                    'TELNET_SERVERS': '$HOME_NET',
                    'AIM_SERVERS': '$EXTERNAL_NET',
                    'DC_SERVERS': '$HOME_NET',
                    'DNP3_SERVER': '$HOME_NET',
                    'DNP3_CLIENT': '$HOME_NET',
                    'MODBUS_CLIENT': '$HOME_NET',
                    'MODBUS_SERVER': '$HOME_NET',
                    'ENIP_CLIENT': '$HOME_NET',
                    'ENIP_SERVER': '$HOME_NET'
                },
                'port-groups': {
                    'HTTP_PORTS': '80',
                    'SHELLCODE_PORTS': '!80',
                    'ORACLE_PORTS': '1521',
                    'SSH_PORTS': '22',
                    'DNP3_PORTS': '20000',
                    'MODBUS_PORTS': '502',
                    'FILE_DATA_PORTS': '[$HTTP_PORTS,110,143]',
                    'FTP_PORTS': '21',
                    'GENEVE_PORTS': '6081',
                    'VXLAN_PORTS': '4789',
                    'TEREDO_PORTS': '3544'
                }
            },
            'default-log-dir': '/var/log/suricata/',
            'stats': {
                'enabled': True,
                'interval': 8
            },
            'outputs': [
                {
                    'eve-log': {
                        'enabled': True,
                        'filetype': 'regular',
                        'filename': 'eve.json',
                        'types': [
                            {'alert': {'tagged-packets': True}},
                            {'http': {'extended': True}},
                            {'dns': {'query': True, 'answer': True}},
                            {'tls': {'extended': True}},
                            {'files': {'force-magic': False}},
                            {'smtp': {}},
                            {'ssh': {}},
                            {'flow': {}}
                        ]
                    }
                },
                {
                    'unified2-alert': {
                        'enabled': False,
                        'filename': 'unified2.alert'
                    }
                },
                {
                    'http-log': {
                        'enabled': False,
                        'filename': 'http.log'
                    }
                }
            ],
            'logging': {
                'default-log-level': 'notice',
                'outputs': [
                    {
                        'console': {
                            'enabled': False
                        }
                    },
                    {
                        'file': {
                            'enabled': True,
                            'level': 'info',
                            'filename': '/var/log/suricata/suricata.log'
                        }
                    },
                    {
                        'syslog': {
                            'enabled': False,
                            'facility': 'local5',
                            'format': '[%i] <%d> -- '
                        }
                    }
                ]
            },
            'af-packet': [
                {
                    'interface': 'eth0',
                    'threads': 'auto',
                    'cluster-id': 99,
                    'cluster-type': 'cluster_flow',
                    'defrag': True,
                    'use-mmap': True,
                    'mmap-locked': True,
                    'tpacket-v3': True,
                    'ring-size': 2048,
                    'block-size': 32768,
                    'use-emergency-flush': True
                }
            ],
            'pcap-file': {
                'checksum-checks': 'auto'
            },
            'app-layer': {
                'protocols': {
                    'tls': {
                        'enabled': True,
                        'detection-ports': {
                            'dp': '443,993,995,5061'
                        }
                    },
                    'http': {
                        'enabled': True,
                        'memcap': '128mb',
                        'libhtp': {
                            'default-config': {
                                'personality': 'IDS',
                                'request-body-limit': '100kb',
                                'response-body-limit': '100kb',
                                'request-body-minimal-inspect-size': '32kb',
                                'request-body-inspect-window': '4kb',
                                'response-body-minimal-inspect-size': '40kb',
                                'response-body-inspect-window': '16kb',
                                'response-body-decompress-layer-limit': 2,
                                'http-body-inline': 'auto',
                                'double-decode-path': False,
                                'double-decode-query': False
                            }
                        }
                    },
                    'ftp': {
                        'enabled': True,
                        'memcap': '64mb'
                    },
                    'smtp': {
                        'enabled': True,
                        'mime': {
                            'decode-mime': True,
                            'decode-base64': True,
                            'decode-quoted-printable': True,
                            'header-value-depth': 2000,
                            'extract-urls': True,
                            'body-md5': False
                        },
                        'inspected-tracker': {
                            'content-limit': 100000,
                            'content-inspect-min-size': 32768,
                            'content-inspect-window': 4096
                        }
                    },
                    'dns': {
                        'tcp': {
                            'enabled': True,
                            'detection-ports': {
                                'dp': 53
                            }
                        },
                        'udp': {
                            'enabled': True,
                            'detection-ports': {
                                'dp': 53
                            }
                        }
                    },
                    'ssh': {
                        'enabled': True
                    },
                    'nfs': {
                        'enabled': True
                    },
                    'smb': {
                        'enabled': True,
                        'detection-ports': {
                            'dp': '139,445'
                        }
                    }
                }
            },
            'asn1-max-frames': 256,
            'run-as': {
                'user': 'suricata',
                'group': 'suricata'
            },
            'threading': {
                'cpu-affinity': [
                    {'management-cpu-set': {'cpu': ['0']}},
                    {'receive-cpu-set': {'cpu': ['1']}},
                    {'worker-cpu-set': {'cpu': ['2', '3', '4', '5']}}
                ]
            },
            'profiling': {
                'rules': {
                    'enabled': True,
                    'filename': 'rule_perf.log',
                    'append': True,
                    'sort': 'avgticks',
                    'limit': 100,
                    'json': False
                }
            },
            'detect': {
                'profile': 'high',
                'custom-values': {
                    'toclient-groups': 3,
                    'toserver-groups': 25
                },
                'sgh-mpm-context': 'auto',
                'inspection-recursion-limit': 3000,
                'prefilter': {
                    'default': 'mpm'
                },
                'grouping': [
                    {'tcp': 'whitelist'},
                    {'udp': 'hash'},
                    {'other': 'pkt'}
                ]
            }
        }
        
        # Write configuration
        with open(self.config_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, indent=2)
        
        return "Suricata configuration generated successfully"
    
    def create_custom_rules(self):
        """Create custom detection rules"""
        
        custom_rules = [
            # SQL Injection detection
            'alert tcp any any -> $HTTP_SERVERS $HTTP_PORTS (msg:"SQL Injection Attempt"; flow:to_server,established; content:"union"; nocase; content:"select"; nocase; distance:0; within:100; classtype:web-application-attack; sid:1000001; rev:1;)',
            
            # XSS detection
            'alert tcp any any -> $HTTP_SERVERS $HTTP_PORTS (msg:"Cross Site Scripting Attempt"; flow:to_server,established; content:"<script"; nocase; http_client_body; classtype:web-application-attack; sid:1000002; rev:1;)',
            
            # Brute force SSH detection
            'alert tcp any any -> $SSH_SERVERS $SSH_PORTS (msg:"SSH Brute Force Attempt"; flow:to_server,established; content:"SSH-"; depth:4; detection_filter:track by_src, count 5, seconds 60; classtype:attempted-user; sid:1000003; rev:1;)',
            
            # Suspicious file uploads
            'alert tcp any any -> $HTTP_SERVERS $HTTP_PORTS (msg:"Suspicious File Upload"; flow:to_server,established; content:"Content-Type|3A 20|"; content:"multipart/form-data"; distance:0; within:50; content:".exe"; nocase; distance:0; classtype:policy-violation; sid:1000004; rev:1;)',
            
            # DNS tunneling detection
            'alert udp any any -> $DNS_SERVERS 53 (msg:"Possible DNS Tunneling"; content:"|01 00 00 01 00 00 00 00 00 00|"; depth:10; byte_test:1,>,50,2; classtype:policy-violation; sid:1000005; rev:1;)',
            
            # Cryptocurrency mining detection
            'alert tcp any any -> any any (msg:"Cryptocurrency Mining Pool Connection"; content:"stratum+tcp://"; classtype:policy-violation; sid:1000006; rev:1;)',
            
            # Suspicious PowerShell execution
            'alert tcp any any -> any any (msg:"Suspicious PowerShell Execution"; content:"powershell"; nocase; content:"-enc"; nocase; distance:0; within:100; classtype:trojan-activity; sid:1000007; rev:1;)',
            
            # Data exfiltration via HTTP POST
            'alert tcp any any -> any any (msg:"Large HTTP POST - Possible Data Exfiltration"; flow:to_server,established; content:"POST"; http_method; byte_test:4,>,1000000,0,relative; classtype:policy-violation; sid:1000008; rev:1;)',
            
            # Suspicious user agent strings
            'alert tcp any any -> $HTTP_SERVERS $HTTP_PORTS (msg:"Suspicious User Agent - Security Scanner"; flow:to_server,established; content:"User-Agent|3A 20|"; http_header; content:"sqlmap"; nocase; distance:0; within:100; classtype:web-application-attack; sid:1000009; rev:1;)',
            
            # Command injection attempts
            'alert tcp any any -> $HTTP_SERVERS $HTTP_PORTS (msg:"Command Injection Attempt"; flow:to_server,established; content:"|3B|"; http_client_body; content:"wget"; nocase; distance:0; within:50; classtype:web-application-attack; sid:1000010; rev:1;)'
        ]
        
        rules_file = f"{self.rules_dir}/local.rules"
        with open(rules_file, 'w') as f:
            for rule in custom_rules:
                f.write(rule + '\n')
        
        return f"Custom rules written to {rules_file}"
    
    def parse_eve_logs(self, limit=100):
        """Parse Suricata EVE JSON logs"""
        eve_log_path = f"{self.log_dir}/eve.json"
        alerts = []
        
        try:
            with open(eve_log_path, 'r') as f:
                lines = f.readlines()[-limit:]  # Get last N lines
                
            for line in lines:
                try:
                    log_entry = json.loads(line.strip())
                    if log_entry.get('event_type') == 'alert':
                        alert = {
                            'timestamp': log_entry.get('timestamp'),
                            'signature': log_entry.get('alert', {}).get('signature'),
                            'classification': log_entry.get('alert', {}).get('category'),
                            'priority': log_entry.get('alert', {}).get('severity'),
                            'source_ip': log_entry.get('src_ip'),
                            'source_port': log_entry.get('src_port'),
                            'dest_ip': log_entry.get('dest_ip'),
                            'dest_port': log_entry.get('dest_port'),
                            'protocol': log_entry.get('proto'),
                            'raw_alert': line.strip()
                        }
                        alerts.append(alert)
                except json.JSONDecodeError:
                    continue
                    
        except FileNotFoundError:
            return []
        
        return alerts
    
    def store_alerts(self, alerts):
        """Store alerts in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for alert in alerts:
            cursor.execute('''
                INSERT INTO alerts 
                (timestamp, signature, classification, priority, source_ip, source_port, 
                 dest_ip, dest_port, protocol, raw_alert)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                alert['timestamp'], alert['signature'], alert['classification'],
                alert['priority'], alert['source_ip'], alert['source_port'],
                alert['dest_ip'], alert['dest_port'], alert['protocol'],
                alert['raw_alert']
            ))
        
        conn.commit()
        conn.close()
        return f"Stored {len(alerts)} alerts in database"
    
    def get_alert_statistics(self):
        """Get alert statistics from database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Total alerts
        cursor.execute("SELECT COUNT(*) FROM alerts")
        total_alerts = cursor.fetchone()[0]
        
        # Alerts by classification
        cursor.execute("""
            SELECT classification, COUNT(*) 
            FROM alerts 
            GROUP BY classification 
            ORDER BY COUNT(*) DESC 
            LIMIT 10
        """)
        by_classification = cursor.fetchall()
        
        # Top source IPs
        cursor.execute("""
            SELECT source_ip, COUNT(*) 
            FROM alerts 
            GROUP BY source_ip 
            ORDER BY COUNT(*) DESC 
            LIMIT 10
        """)
        top_sources = cursor.fetchall()
        
        # Recent alerts
        cursor.execute("""
            SELECT timestamp, signature, source_ip, dest_ip 
            FROM alerts 
            ORDER BY timestamp DESC 
            LIMIT 10
        """)
        recent_alerts = cursor.fetchall()
        
        conn.close()
        
        return {
            'total_alerts': total_alerts,
            'by_classification': by_classification,
            'top_sources': top_sources,
            'recent_alerts': recent_alerts
        }
    
    def update_rules(self):
        """Update Suricata rules from ET Open"""
        try:
            # Update ET Open rules
            subprocess.run([
                'suricata-update',
                '--suricata', '/usr/bin/suricata',
                '--suricata-conf', self.config_path,
                '--no-test', 
                '--no-reload'
            ], check=True)
            
            # Reload Suricata
            subprocess.run(['systemctl', 'reload', 'suricata'], check=True)
            
            return "Rules updated and Suricata reloaded successfully"
            
        except subprocess.CalledProcessError as e:
            return f"Error updating rules: {e}"

# Example usage
if __name__ == "__main__":
    suricata_mgr = SuricataManager()
    
    # Generate configuration
    print(suricata_mgr.generate_suricata_config())
    
    # Create custom rules
    print(suricata_mgr.create_custom_rules())
    
    # Parse recent alerts
    alerts = suricata_mgr.parse_eve_logs()
    if alerts:
        print(f"Found {len(alerts)} recent alerts")
        suricata_mgr.store_alerts(alerts)
    
    # Get statistics
    stats = suricata_mgr.get_alert_statistics()
    print(f"\nAlert Statistics:")
    print(f"Total Alerts: {stats['total_alerts']}")
    print(f"Top Classifications: {stats['by_classification'][:5]}")
    print(f"Top Source IPs: {stats['top_sources'][:5]}")
```

## Best Practices for Enterprise Network Security

### Security Architecture Design
- **Defense in depth** with multiple security layers
- **Network segmentation** using VLANs and security groups
- **Zero trust principles** with explicit verification
- **Principle of least privilege** for all network access

### Firewall Management
- **Regular rule audits** to remove unused or overly permissive rules
- **Automated rule deployment** with version control
- **Centralized logging and monitoring** for all firewall events
- **Change management processes** for firewall modifications

### Incident Response
- **Real-time alerting** for security events
- **Automated blocking** of malicious traffic
- **Forensic logging** for security investigations
- **Regular security assessments** and penetration testing

This comprehensive firewall and security group guide provides enterprise-grade network security solutions essential for protecting modern DevOps infrastructure across cloud and on-premises environments.