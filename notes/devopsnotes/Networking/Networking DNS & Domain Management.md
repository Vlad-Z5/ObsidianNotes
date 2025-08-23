# Networking DNS & Domain Management

## Overview

Domain Name System (DNS) serves as the internet's phone book, translating human-readable domain names into IP addresses. This guide covers DNS architecture, record types, zone management, DNS security (DNSSEC), load balancing strategies, and enterprise DNS implementations essential for DevOps engineers managing modern distributed applications.

## DNS Architecture & Fundamentals

### DNS Hierarchy and Resolution Process

```python
import dns.resolver
import dns.query
import dns.rdatatype
import time
from dataclasses import dataclass
from typing import List, Dict, Optional

@dataclass
class DNSQuery:
    domain: str
    record_type: str
    nameserver: str
    response_time: float
    ttl: int
    answers: List[str]

class DNSAnalyzer:
    def __init__(self):
        self.root_servers = [
            '198.41.0.4',    # a.root-servers.net
            '199.9.14.201',  # b.root-servers.net
            '192.33.4.12',   # c.root-servers.net
            '199.7.91.13',   # d.root-servers.net
        ]
    
    def trace_dns_resolution(self, domain: str, record_type: str = 'A'):
        """Trace DNS resolution from root to final answer"""
        trace_steps = []
        current_servers = self.root_servers
        query_domain = domain
        
        while current_servers and query_domain:
            try:
                # Query first available server
                for server in current_servers:
                    try:
                        start_time = time.time()
                        
                        # Create DNS query
                        query = dns.message.make_query(query_domain, record_type)
                        response = dns.query.udp(query, server, timeout=5)
                        
                        response_time = (time.time() - start_time) * 1000
                        
                        step = {
                            'server': server,
                            'query_domain': query_domain,
                            'record_type': record_type,
                            'response_time_ms': round(response_time, 2),
                            'status': 'success',
                            'answers': [],
                            'authority': [],
                            'additional': []
                        }
                        
                        # Process response sections
                        if response.answer:
                            for rrset in response.answer:
                                for rr in rrset:
                                    step['answers'].append(str(rr))
                        
                        if response.authority:
                            for rrset in response.authority:
                                for rr in rrset:
                                    step['authority'].append(str(rr))
                        
                        if response.additional:
                            for rrset in response.additional:
                                if rrset.rdtype in [dns.rdatatype.A, dns.rdatatype.AAAA]:
                                    for rr in rrset:
                                        step['additional'].append(str(rr))
                        
                        trace_steps.append(step)
                        
                        # Check if we have final answer
                        if response.answer:
                            return trace_steps
                        
                        # Get next level nameservers from authority section
                        next_servers = []
                        for rrset in response.additional:
                            if rrset.rdtype == dns.rdatatype.A:
                                for rr in rrset:
                                    next_servers.append(str(rr))
                        
                        if next_servers:
                            current_servers = next_servers
                            break
                        
                    except Exception as e:
                        continue
                
                break
                
            except Exception as e:
                trace_steps.append({
                    'server': server,
                    'query_domain': query_domain,
                    'error': str(e),
                    'status': 'error'
                })
                break
        
        return trace_steps
    
    def analyze_dns_performance(self, domains: List[str], nameservers: List[str]):
        """Analyze DNS performance across multiple domains and nameservers"""
        results = []
        
        for domain in domains:
            for nameserver in nameservers:
                try:
                    # Configure resolver
                    resolver = dns.resolver.Resolver()
                    resolver.nameservers = [nameserver]
                    resolver.timeout = 5
                    
                    start_time = time.time()
                    answers = resolver.resolve(domain, 'A')
                    response_time = (time.time() - start_time) * 1000
                    
                    query_result = DNSQuery(
                        domain=domain,
                        record_type='A',
                        nameserver=nameserver,
                        response_time=response_time,
                        ttl=answers.rrset.ttl,
                        answers=[str(rr) for rr in answers]
                    )
                    
                    results.append(query_result)
                    
                except Exception as e:
                    results.append(DNSQuery(
                        domain=domain,
                        record_type='A',
                        nameserver=nameserver,
                        response_time=-1,
                        ttl=0,
                        answers=[f"Error: {str(e)}"]
                    ))
        
        return results

# Example DNS performance analysis
analyzer = DNSAnalyzer()

# Test domains
test_domains = [
    'google.com',
    'github.com',
    'stackoverflow.com',
    'aws.amazon.com'
]

# Test nameservers
test_nameservers = [
    '8.8.8.8',      # Google DNS
    '1.1.1.1',      # Cloudflare DNS
    '208.67.222.222', # OpenDNS
    '9.9.9.9'       # Quad9
]

print("DNS Performance Analysis")
print("=" * 60)

results = analyzer.analyze_dns_performance(test_domains, test_nameservers)

# Group by nameserver for comparison
ns_performance = {}
for result in results:
    if result.nameserver not in ns_performance:
        ns_performance[result.nameserver] = []
    ns_performance[result.nameserver].append(result)

for ns, queries in ns_performance.items():
    avg_response = sum(q.response_time for q in queries if q.response_time > 0) / len([q for q in queries if q.response_time > 0])
    print(f"\nNameserver: {ns}")
    print(f"Average Response Time: {avg_response:.2f}ms")
    
    for query in queries:
        if query.response_time > 0:
            print(f"  {query.domain:20} | {query.response_time:6.2f}ms | TTL: {query.ttl:5}s")
        else:
            print(f"  {query.domain:20} | ERROR: {query.answers[0]}")
```

## DNS Record Types and Management

### Comprehensive DNS Record Management

```python
import boto3
from typing import Dict, List, Any
import json

class EnterpriseRoute53Manager:
    def __init__(self, profile_name=None):
        session = boto3.Session(profile_name=profile_name)
        self.route53 = session.client('route53')
        self.route53_domains = session.client('route53domains')
    
    def create_hosted_zone(self, domain_name: str, comment: str = ""):
        """Create a new hosted zone"""
        try:
            response = self.route53.create_hosted_zone(
                Name=domain_name,
                CallerReference=str(int(time.time())),
                HostedZoneConfig={
                    'Comment': comment,
                    'PrivateZone': False
                }
            )
            
            zone_id = response['HostedZone']['Id'].split('/')[-1]
            nameservers = [ns for ns in response['DelegationSet']['NameServers']]
            
            return {
                'zone_id': zone_id,
                'domain': domain_name,
                'nameservers': nameservers,
                'status': 'created'
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def create_record_set(self, zone_id: str, name: str, record_type: str, 
                         values: List[str], ttl: int = 300, weight: int = None,
                         set_identifier: str = None, health_check_id: str = None):
        """Create DNS record with advanced routing policies"""
        
        record_data = {
            'Name': name,
            'Type': record_type,
            'TTL': ttl,
            'ResourceRecords': [{'Value': value} for value in values]
        }
        
        # Add weighted routing if specified
        if weight is not None and set_identifier:
            record_data['Weight'] = weight
            record_data['SetIdentifier'] = set_identifier
        
        # Add health check if specified
        if health_check_id:
            record_data['HealthCheckId'] = health_check_id
        
        try:
            response = self.route53.change_resource_record_sets(
                HostedZoneId=zone_id,
                ChangeBatch={
                    'Comment': f'Create {record_type} record for {name}',
                    'Changes': [{
                        'Action': 'CREATE',
                        'ResourceRecordSet': record_data
                    }]
                }
            )
            
            return {
                'change_id': response['ChangeInfo']['Id'],
                'status': response['ChangeInfo']['Status'],
                'record': record_data
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def create_alias_record(self, zone_id: str, name: str, alias_target: Dict[str, Any]):
        """Create alias record for AWS resources"""
        try:
            response = self.route53.change_resource_record_sets(
                HostedZoneId=zone_id,
                ChangeBatch={
                    'Comment': f'Create alias record for {name}',
                    'Changes': [{
                        'Action': 'CREATE',
                        'ResourceRecordSet': {
                            'Name': name,
                            'Type': 'A',
                            'AliasTarget': alias_target
                        }
                    }]
                }
            )
            
            return {
                'change_id': response['ChangeInfo']['Id'],
                'status': response['ChangeInfo']['Status'],
                'alias_target': alias_target
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def setup_enterprise_dns_architecture(self, domain: str):
        """Setup comprehensive DNS architecture for enterprise domain"""
        
        # Create hosted zone
        zone_result = self.create_hosted_zone(
            domain, 
            f"Enterprise DNS zone for {domain}"
        )
        
        if 'error' in zone_result:
            return zone_result
        
        zone_id = zone_result['zone_id']
        records_created = []
        
        # Enterprise DNS records configuration
        dns_records = [
            # Root domain A record (multiple IPs for redundancy)
            {
                'name': domain,
                'type': 'A',
                'values': ['203.0.113.1', '203.0.113.2'],
                'ttl': 300
            },
            # WWW CNAME
            {
                'name': f'www.{domain}',
                'type': 'CNAME',
                'values': [domain],
                'ttl': 300
            },
            # Mail servers (MX records)
            {
                'name': domain,
                'type': 'MX',
                'values': [
                    '10 mail1.{}'.format(domain),
                    '20 mail2.{}'.format(domain)
                ],
                'ttl': 3600
            },
            # Mail server A records
            {
                'name': f'mail1.{domain}',
                'type': 'A',
                'values': ['203.0.113.10'],
                'ttl': 300
            },
            {
                'name': f'mail2.{domain}',
                'type': 'A', 
                'values': ['203.0.113.11'],
                'ttl': 300
            },
            # SPF record for email security
            {
                'name': domain,
                'type': 'TXT',
                'values': ['"v=spf1 include:_spf.{} ~all"'.format(domain)],
                'ttl': 3600
            },
            # DKIM record
            {
                'name': f'default._domainkey.{domain}',
                'type': 'TXT',
                'values': ['"v=DKIM1; k=rsa; p=MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQC..."'],
                'ttl': 3600
            },
            # DMARC record
            {
                'name': f'_dmarc.{domain}',
                'type': 'TXT',
                'values': ['"v=DMARC1; p=quarantine; rua=mailto:dmarc@{}"'.format(domain)],
                'ttl': 3600
            },
            # API subdomain
            {
                'name': f'api.{domain}',
                'type': 'A',
                'values': ['203.0.113.20', '203.0.113.21'],
                'ttl': 300
            },
            # CDN subdomain
            {
                'name': f'cdn.{domain}',
                'type': 'CNAME',
                'values': [f'{domain}.cloudfront.net'],
                'ttl': 3600
            },
            # Status page
            {
                'name': f'status.{domain}',
                'type': 'CNAME',
                'values': ['statuspage.example.com'],
                'ttl': 300
            },
            # Monitoring subdomain
            {
                'name': f'monitoring.{domain}',
                'type': 'A',
                'values': ['203.0.113.30'],
                'ttl': 300
            }
        ]
        
        # Create all DNS records
        for record in dns_records:
            result = self.create_record_set(
                zone_id=zone_id,
                name=record['name'],
                record_type=record['type'],
                values=record['values'],
                ttl=record['ttl']
            )
            
            if 'error' not in result:
                records_created.append({
                    'name': record['name'],
                    'type': record['type'],
                    'status': 'created'
                })
            else:
                records_created.append({
                    'name': record['name'],
                    'type': record['type'],
                    'status': 'failed',
                    'error': result['error']
                })
        
        return {
            'hosted_zone': zone_result,
            'records_created': records_created,
            'nameservers': zone_result['nameservers'],
            'next_steps': [
                f"Update domain registrar to use these nameservers: {', '.join(zone_result['nameservers'])}",
                "Configure monitoring for DNS resolution",
                "Set up health checks for critical endpoints",
                "Review and update TTL values based on change frequency"
            ]
        }

# Example usage
route53_manager = EnterpriseRoute53Manager()

# Setup enterprise DNS
domain = "example-company.com"
result = route53_manager.setup_enterprise_dns_architecture(domain)

print(f"DNS Setup Results for {domain}")
print("=" * 50)

if 'error' not in result:
    print(f"Hosted Zone ID: {result['hosted_zone']['zone_id']}")
    print(f"Nameservers: {', '.join(result['hosted_zone']['nameservers'])}")
    print(f"\nRecords Created: {len([r for r in result['records_created'] if r['status'] == 'created'])}")
    
    for record in result['records_created']:
        status_icon = "✅" if record['status'] == 'created' else "❌"
        print(f"  {status_icon} {record['name']} ({record['type']})")
    
    print(f"\nNext Steps:")
    for step in result['next_steps']:
        print(f"  • {step}")
else:
    print(f"Error: {result['error']}")
```

### DNS Load Balancing and Failover

```python
class DNSLoadBalancer:
    def __init__(self, route53_client):
        self.route53 = route53_client
    
    def create_health_check(self, ip_address: str, port: int = 80, 
                           path: str = "/health", protocol: str = "HTTP"):
        """Create health check for endpoint"""
        try:
            response = self.route53.create_health_check(
                Type='HTTP',
                ResourcePath=path,
                FullyQualifiedDomainName=ip_address,
                Port=port,
                RequestInterval=30,
                FailureThreshold=3,
                Tags=[
                    {
                        'Key': 'Name',
                        'Value': f'HealthCheck-{ip_address}:{port}'
                    },
                    {
                        'Key': 'Purpose',
                        'Value': 'DNS-LoadBalancing'
                    }
                ]
            )
            
            return {
                'health_check_id': response['HealthCheck']['Id'],
                'status': 'created',
                'endpoint': f"{ip_address}:{port}{path}"
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def setup_weighted_routing(self, zone_id: str, domain: str, endpoints: List[Dict]):
        """Setup weighted routing for load balancing"""
        records_created = []
        
        for i, endpoint in enumerate(endpoints):
            # Create health check for endpoint
            health_check = self.create_health_check(
                endpoint['ip'],
                endpoint.get('port', 80),
                endpoint.get('health_path', '/health')
            )
            
            if 'error' in health_check:
                records_created.append({
                    'endpoint': endpoint['ip'],
                    'status': 'failed',
                    'error': f"Health check creation failed: {health_check['error']}"
                })
                continue
            
            # Create weighted DNS record
            try:
                response = self.route53.change_resource_record_sets(
                    HostedZoneId=zone_id,
                    ChangeBatch={
                        'Comment': f'Weighted routing for {domain}',
                        'Changes': [{
                            'Action': 'CREATE',
                            'ResourceRecordSet': {
                                'Name': domain,
                                'Type': 'A',
                                'SetIdentifier': f"endpoint-{i+1}",
                                'Weight': endpoint.get('weight', 100),
                                'TTL': 60,  # Low TTL for quick failover
                                'ResourceRecords': [{'Value': endpoint['ip']}],
                                'HealthCheckId': health_check['health_check_id']
                            }
                        }]
                    }
                )
                
                records_created.append({
                    'endpoint': endpoint['ip'],
                    'weight': endpoint.get('weight', 100),
                    'health_check_id': health_check['health_check_id'],
                    'change_id': response['ChangeInfo']['Id'],
                    'status': 'created'
                })
                
            except Exception as e:
                records_created.append({
                    'endpoint': endpoint['ip'],
                    'status': 'failed',
                    'error': str(e)
                })
        
        return records_created
    
    def setup_failover_routing(self, zone_id: str, domain: str, 
                              primary_ip: str, secondary_ip: str):
        """Setup primary/secondary failover routing"""
        
        # Create health checks
        primary_health = self.create_health_check(primary_ip)
        secondary_health = self.create_health_check(secondary_ip)
        
        if 'error' in primary_health or 'error' in secondary_health:
            return {'error': 'Failed to create health checks'}
        
        records_created = []
        
        # Primary record
        try:
            primary_response = self.route53.change_resource_record_sets(
                HostedZoneId=zone_id,
                ChangeBatch={
                    'Comment': f'Primary failover record for {domain}',
                    'Changes': [{
                        'Action': 'CREATE',
                        'ResourceRecordSet': {
                            'Name': domain,
                            'Type': 'A',
                            'SetIdentifier': 'primary',
                            'Failover': 'PRIMARY',
                            'TTL': 60,
                            'ResourceRecords': [{'Value': primary_ip}],
                            'HealthCheckId': primary_health['health_check_id']
                        }
                    }]
                }
            )
            
            records_created.append({
                'type': 'primary',
                'ip': primary_ip,
                'health_check_id': primary_health['health_check_id'],
                'change_id': primary_response['ChangeInfo']['Id'],
                'status': 'created'
            })
            
        except Exception as e:
            records_created.append({
                'type': 'primary',
                'ip': primary_ip,
                'status': 'failed',
                'error': str(e)
            })
        
        # Secondary record
        try:
            secondary_response = self.route53.change_resource_record_sets(
                HostedZoneId=zone_id,
                ChangeBatch={
                    'Comment': f'Secondary failover record for {domain}',
                    'Changes': [{
                        'Action': 'CREATE',
                        'ResourceRecordSet': {
                            'Name': domain,
                            'Type': 'A',
                            'SetIdentifier': 'secondary',
                            'Failover': 'SECONDARY',
                            'TTL': 60,
                            'ResourceRecords': [{'Value': secondary_ip}],
                            'HealthCheckId': secondary_health['health_check_id']
                        }
                    }]
                }
            )
            
            records_created.append({
                'type': 'secondary',
                'ip': secondary_ip,
                'health_check_id': secondary_health['health_check_id'],
                'change_id': secondary_response['ChangeInfo']['Id'],
                'status': 'created'
            })
            
        except Exception as e:
            records_created.append({
                'type': 'secondary',
                'ip': secondary_ip,
                'status': 'failed',
                'error': str(e)
            })
        
        return {
            'failover_setup': records_created,
            'primary_ip': primary_ip,
            'secondary_ip': secondary_ip,
            'ttl': 60
        }

# Example: Setup load balancing for API endpoints
load_balancer = DNSLoadBalancer(boto3.client('route53'))

# Define endpoints with weights
api_endpoints = [
    {
        'ip': '203.0.113.20',
        'weight': 70,  # 70% of traffic
        'port': 443,
        'health_path': '/api/health'
    },
    {
        'ip': '203.0.113.21', 
        'weight': 30,  # 30% of traffic
        'port': 443,
        'health_path': '/api/health'
    }
]

# Setup weighted routing
zone_id = "Z1234567890123"
domain = "api.example-company.com"

weighted_result = load_balancer.setup_weighted_routing(zone_id, domain, api_endpoints)

print("Weighted DNS Load Balancing Setup")
print("=" * 40)
for record in weighted_result:
    if record['status'] == 'created':
        print(f"✅ {record['endpoint']} (Weight: {record['weight']})")
    else:
        print(f"❌ {record['endpoint']} - Error: {record['error']}")

# Setup failover for main website
failover_result = load_balancer.setup_failover_routing(
    zone_id, 
    "www.example-company.com",
    "203.0.113.1",  # Primary
    "203.0.113.2"   # Secondary
)

print(f"\nFailover DNS Setup")
print("=" * 40)
for record in failover_result['failover_setup']:
    if record['status'] == 'created':
        print(f"✅ {record['type'].upper()}: {record['ip']}")
    else:
        print(f"❌ {record['type'].upper()}: {record['ip']} - Error: {record['error']}")
```

## DNSSEC Implementation

### DNS Security Extensions

```bash
#!/bin/bash
# dnssec-setup.sh - DNSSEC implementation script

DOMAIN=$1
ZONE_FILE="/var/named/zones/$DOMAIN.db"
KEYS_DIR="/var/named/keys/$DOMAIN"

if [ -z "$DOMAIN" ]; then
    echo "Usage: $0 <domain>"
    exit 1
fi

# Create keys directory
mkdir -p $KEYS_DIR
cd $KEYS_DIR

echo "Setting up DNSSEC for $DOMAIN"
echo "================================="

# Generate Zone Signing Key (ZSK)
echo "1. Generating Zone Signing Key (ZSK)..."
dnssec-keygen -a RSASHA256 -b 1024 -n ZONE $DOMAIN

# Generate Key Signing Key (KSK) 
echo "2. Generating Key Signing Key (KSK)..."
dnssec-keygen -a RSASHA256 -b 2048 -f KSK -n ZONE $DOMAIN

# Sign the zone
echo "3. Signing the zone file..."
dnssec-signzone -A -3 $(head -c 1000 /dev/random | sha1sum | cut -b 1-16) \
                -N INCREMENT -o $DOMAIN -t $ZONE_FILE

# Create DNSSEC policy file
cat > /etc/named/dnssec-policy.conf << EOF
# DNSSEC Policy for $DOMAIN
options {
    dnssec-enable yes;
    dnssec-validation yes;
    dnssec-lookaside auto;
};

# Key timing policy
policy "enterprise" {
    keys {
        ksk key-directory "$KEYS_DIR";
        zsk key-directory "$KEYS_DIR";
    };
    
    # Key timing
    ksk lifetime P1Y;  # 1 year
    zsk lifetime P3M;  # 3 months
    
    # Algorithm
    algorithm 8;  # RSASHA256
    
    # Key sizes
    ksk-size 2048;
    zsk-size 1024;
};

zone "$DOMAIN" {
    type master;
    file "$ZONE_FILE.signed";
    dnssec-policy "enterprise";
    inline-signing yes;
};
EOF

echo "4. DNSSEC setup completed for $DOMAIN"
echo "   - Zone file: $ZONE_FILE.signed"
echo "   - Keys directory: $KEYS_DIR"
echo "   - Policy file: /etc/named/dnssec-policy.conf"

# Display DS record for parent zone
echo ""
echo "5. DS Record for parent zone delegation:"
echo "========================================"
dnssec-dsfromkey -2 K${DOMAIN}.*.key

echo ""
echo "6. Next steps:"
echo "   - Add the DS record to the parent zone"
echo "   - Test DNSSEC validation with: dig +dnssec $DOMAIN"
echo "   - Monitor key expiration dates"
echo "   - Set up automated key rotation"
```

## Enterprise DNS Monitoring

### DNS Performance and Health Monitoring

```python
import asyncio
import aiohttp
import aiodns
import time
from dataclasses import dataclass
from typing import List, Dict
import json

@dataclass
class DNSMonitoringResult:
    domain: str
    nameserver: str
    record_type: str
    response_time: float
    success: bool
    error_message: str = ""
    ttl: int = 0
    answers: List[str] = None

class DNSMonitor:
    def __init__(self):
        self.resolver = aiodns.DNSResolver()
    
    async def check_dns_resolution(self, domain: str, nameserver: str, 
                                 record_type: str = 'A') -> DNSMonitoringResult:
        """Check DNS resolution for a specific domain and nameserver"""
        try:
            # Configure resolver for specific nameserver
            resolver = aiodns.DNSResolver(nameservers=[nameserver])
            
            start_time = time.time()
            
            if record_type == 'A':
                result = await resolver.gethostbyname(domain, socket.AF_INET)
                answers = [result.addresses[0]] if result.addresses else []
            elif record_type == 'AAAA':
                result = await resolver.gethostbyname(domain, socket.AF_INET6) 
                answers = [result.addresses[0]] if result.addresses else []
            else:
                # For other record types, use query method
                result = await resolver.query(domain, record_type)
                answers = [str(r) for r in result] if result else []
            
            response_time = (time.time() - start_time) * 1000
            
            return DNSMonitoringResult(
                domain=domain,
                nameserver=nameserver,
                record_type=record_type,
                response_time=response_time,
                success=True,
                answers=answers
            )
            
        except Exception as e:
            return DNSMonitoringResult(
                domain=domain,
                nameserver=nameserver,
                record_type=record_type,
                response_time=-1,
                success=False,
                error_message=str(e)
            )
    
    async def monitor_dns_infrastructure(self, monitoring_config: Dict) -> Dict:
        """Monitor comprehensive DNS infrastructure"""
        tasks = []
        
        for domain_config in monitoring_config['domains']:
            domain = domain_config['name']
            record_types = domain_config.get('record_types', ['A'])
            
            for nameserver in monitoring_config['nameservers']:
                for record_type in record_types:
                    task = self.check_dns_resolution(domain, nameserver, record_type)
                    tasks.append(task)
        
        # Execute all checks concurrently
        results = await asyncio.gather(*tasks)
        
        # Organize results
        organized_results = {
            'timestamp': time.time(),
            'total_checks': len(results),
            'successful_checks': len([r for r in results if r.success]),
            'failed_checks': len([r for r in results if not r.success]),
            'average_response_time': sum(r.response_time for r in results if r.response_time > 0) / len([r for r in results if r.response_time > 0]),
            'results_by_domain': {},
            'results_by_nameserver': {},
            'alerts': []
        }
        
        # Group by domain
        for result in results:
            if result.domain not in organized_results['results_by_domain']:
                organized_results['results_by_domain'][result.domain] = []
            organized_results['results_by_domain'][result.domain].append(result)
        
        # Group by nameserver
        for result in results:
            if result.nameserver not in organized_results['results_by_nameserver']:
                organized_results['results_by_nameserver'][result.nameserver] = []
            organized_results['results_by_nameserver'][result.nameserver].append(result)
        
        # Generate alerts
        for result in results:
            if not result.success:
                organized_results['alerts'].append({
                    'level': 'critical',
                    'message': f"DNS resolution failed for {result.domain} via {result.nameserver}",
                    'error': result.error_message
                })
            elif result.response_time > monitoring_config.get('response_time_threshold', 1000):
                organized_results['alerts'].append({
                    'level': 'warning', 
                    'message': f"Slow DNS response for {result.domain} via {result.nameserver}",
                    'response_time': result.response_time
                })
        
        return organized_results

# DNS monitoring configuration
monitoring_config = {
    'nameservers': [
        '8.8.8.8',      # Google DNS
        '1.1.1.1',      # Cloudflare DNS
        '208.67.222.222', # OpenDNS
    ],
    'domains': [
        {
            'name': 'example-company.com',
            'record_types': ['A', 'MX', 'TXT']
        },
        {
            'name': 'api.example-company.com', 
            'record_types': ['A']
        },
        {
            'name': 'www.example-company.com',
            'record_types': ['A']
        },
        {
            'name': 'mail.example-company.com',
            'record_types': ['A', 'MX']
        }
    ],
    'response_time_threshold': 500  # milliseconds
}

async def run_dns_monitoring():
    """Run DNS monitoring and display results"""
    monitor = DNSMonitor()
    
    print("Starting DNS Infrastructure Monitoring...")
    print("=" * 50)
    
    results = await monitor.monitor_dns_infrastructure(monitoring_config)
    
    # Display summary
    print(f"Monitoring Results Summary")
    print(f"Total Checks: {results['total_checks']}")
    print(f"Successful: {results['successful_checks']}")
    print(f"Failed: {results['failed_checks']}")
    print(f"Average Response Time: {results['average_response_time']:.2f}ms")
    print("")
    
    # Display alerts
    if results['alerts']:
        print("🚨 ALERTS:")
        for alert in results['alerts']:
            level_icon = "🔴" if alert['level'] == 'critical' else "🟡"
            print(f"{level_icon} {alert['message']}")
            if 'error' in alert:
                print(f"   Error: {alert['error']}")
            if 'response_time' in alert:
                print(f"   Response Time: {alert['response_time']:.2f}ms")
        print("")
    
    # Display performance by nameserver
    print("Performance by Nameserver:")
    print("-" * 30)
    for ns, ns_results in results['results_by_nameserver'].items():
        successful = [r for r in ns_results if r.success]
        if successful:
            avg_time = sum(r.response_time for r in successful) / len(successful)
            success_rate = len(successful) / len(ns_results) * 100
            print(f"{ns:15} | {avg_time:6.2f}ms | {success_rate:5.1f}% success")
        else:
            print(f"{ns:15} | FAILED  | 0.0% success")

# Run the monitoring
# asyncio.run(run_dns_monitoring())
```

## Best Practices for Enterprise DNS

### DNS Architecture Design
- **Redundant nameservers** across multiple geographic locations
- **Authoritative DNS separation** from recursive DNS services
- **Zone delegation strategy** for organizational boundaries
- **TTL optimization** balancing performance and flexibility

### Security Implementation
- **DNSSEC deployment** for authentication and integrity
- **DNS filtering** to block malicious domains
- **Query logging** for security monitoring and analysis
- **Rate limiting** to prevent DNS amplification attacks

### Performance Optimization
- **Anycast DNS** for global performance
- **Caching strategies** with appropriate TTL values
- **Load balancing** with health checks and failover
- **Monitoring and alerting** for DNS service availability

### Operational Excellence
- **Automation** for zone updates and key rotation
- **Change management** with version control and testing
- **Documentation** of DNS architecture and procedures
- **Disaster recovery** planning for DNS infrastructure

This comprehensive DNS guide provides enterprise-grade solutions for domain management, security, and performance optimization essential for modern DevOps operations.