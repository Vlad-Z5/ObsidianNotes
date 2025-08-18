# AWS Route 53

> **Service Type:** DNS & Domain Registration | **Tier:** Essential Services | **Global/Regional:** Global

## Overview

AWS Route 53 is a highly available and scalable Domain Name System (DNS) web service that performs three main functions: domain registration, DNS routing, and health checking. Route 53 effectively connects user requests to infrastructure running in AWS or on-premises, enabling global load balancing, disaster recovery, and high-performance application delivery.

## DevOps Use Cases

### Global Traffic Management
- **Multi-region load balancing** directing users to the nearest healthy endpoint
- **Latency-based routing** optimizing performance for global user bases
- **Geolocation routing** compliance with data sovereignty requirements
- **Traffic policy automation** managing complex routing scenarios with Infrastructure as Code

### Disaster Recovery and High Availability
- **Automated failover** switching traffic to backup regions during outages
- **Health check automation** continuous monitoring of application endpoints
- **DNS-based circuit breakers** preventing cascade failures across microservices
- **Multi-level failover** implementing tiered recovery strategies

### DevOps Pipeline Integration
- **Blue-green deployments** weighted routing for zero-downtime deployments
- **Canary releases** gradual traffic shifting to new application versions
- **Environment management** dynamic DNS routing for staging and production
- **Feature flag integration** DNS-based feature toggling and A/B testing

### Microservices Architecture
- **Service discovery** private DNS zones for internal service communication
- **Container orchestration** integration with ECS and EKS service discovery
- **API versioning** DNS routing to different API versions
- **Environment isolation** separate DNS namespaces for different environments

### Monitoring and Observability
- **Health check orchestration** comprehensive endpoint monitoring
- **DNS query analytics** analyzing traffic patterns and performance
- **Alerting integration** CloudWatch alarms for DNS and health check events
- **Compliance reporting** audit trails for DNS changes and domain management

## Service Components

|Component|Purpose|Use Case|
|---|---|---|
|**DNS Hosting**|Authoritative DNS service|Domain name resolution|
|**Domain Registration**|Register/transfer domains|One-stop domain management|
|**Health Checks**|Monitor endpoint health|Automated failover|
|**Traffic Flow**|Visual traffic policy editor|Complex routing scenarios|

---

## DNS Record Types

### Standard Records

|Type|Purpose|Example|TTL Recommendations|
|---|---|---|---|
|**A**|IPv4 address|`192.0.2.1`|300s (5min) - 86400s (24h)|
|**AAAA**|IPv6 address|`2001:db8::1`|300s - 86400s|
|**CNAME**|Canonical name|`www.example.com`|300s - 3600s|
|**MX**|Mail exchange|`10 mail.example.com`|3600s - 86400s|
|**TXT**|Text records|SPF, DKIM, verification|300s - 3600s|
|**NS**|Name server|`ns-123.awsdns-12.com`|86400s|
|**SOA**|Start of authority|Zone metadata|86400s|
|**SRV**|Service locator|`10 5 443 server.example.com`|300s - 3600s|
|**PTR**|Reverse DNS|IP to domain mapping|3600s - 86400s|

### AWS-Specific Records

|Type|Purpose|Benefits|
|---|---|---|
|**Alias**|Point to AWS resources|No charge, automatic IP updates|
|**CAA**|Certificate authority authorization|SSL/TLS security|

---

## Routing Policies

### Simple Routing

- **Use Case** - Single resource serving traffic
- **Configuration** - One record, one or multiple IP addresses
- **Behavior** - Returns all values in random order
- **Health Checks** - Not supported

### Weighted Routing

- **Use Case** - A/B testing, gradual deployments
- **Configuration** - Multiple records with weights (0-255)
- **Behavior** - Traffic split based on weight ratios
- **Health Checks** - Supported per record

```
Production: Weight 80 (80% traffic)
Staging:    Weight 20 (20% traffic)
```

### Latency-Based Routing

- **Use Case** - Global applications requiring low latency
- **Configuration** - Records associated with AWS regions
- **Behavior** - Routes to lowest latency region
- **Health Checks** - Supported per record
- **Requirements** - Must specify AWS region for each record

### Failover Routing

- **Use Case** - Active-passive disaster recovery
- **Configuration** - Primary and secondary records
- **Behavior** - Routes to secondary when primary fails health check
- **Health Checks** - Required for primary record

```
Primary:   Active endpoint (health checked)
Secondary: Backup endpoint (used when primary fails)
```

### Geolocation Routing

- **Use Case** - Content localization, compliance requirements
- **Configuration** - Records mapped to continents, countries, or states
- **Behavior** - Routes based on user's geographic location
- **Default Record** - Recommended for unmatched locations
- **Granularity** - Continent > Country > State (US only)

### Geoproximity Routing

- **Use Case** - Route based on location with bias adjustment
- **Configuration** - Geographic coordinates with bias values
- **Behavior** - Routes to closest resource, adjusted by bias
- **Bias Range** - -99 to +99 (shrink to expand coverage area)
- **Requirements** - Traffic Flow subscription required

### Multivalue Answer Routing

- **Use Case** - Simple load balancing, redundancy
- **Configuration** - Multiple records with same name
- **Behavior** - Returns up to 8 healthy records randomly
- **Health Checks** - Supported per record
- **Benefits** - Client-side load balancing

---

## Alias Records vs CNAME

### Alias Records

|Feature|Benefit|
|---|---|
|**AWS Resource Integration**|Direct mapping to ELB, CloudFront, S3, etc.|
|**No Additional Charges**|DNS queries to alias records are free|
|**Automatic IP Updates**|AWS manages IP address changes|
|**Zone Apex Support**|Can be used at domain root (example.com)|
|**Health Check Integration**|Native health checking support|

### Supported Alias Targets

```
Application/Network Load Balancer
Classic Load Balancer
CloudFront Distribution
API Gateway
Elastic Beanstalk Environment
S3 Website Endpoint
VPC Interface Endpoint
Global Accelerator
Another Route 53 Record (same hosted zone)
```

### CNAME Limitations

- Cannot be used at zone apex (root domain)
- Requires additional DNS lookup
- Charges apply for DNS queries
- Manual IP address management

---

## Health Checks

### Health Check Types

|Type|Monitors|Use Case|
|---|---|---|
|**HTTP/HTTPS**|Web endpoints|Web applications|
|**TCP**|Port connectivity|Database, custom services|
|**Calculated**|Other health checks|Complex dependencies|
|**CloudWatch Alarm**|AWS metrics|AWS resource health|

### Health Check Configuration

#### Basic Settings

- **Request Interval** - 30 seconds (standard) or 10 seconds (fast)
- **Failure Threshold** - 1-10 consecutive failures
- **Success Threshold** - 2-10 consecutive successes (TCP only)
- **Timeout** - 4 seconds (fast) or 2-60 seconds (standard)

#### Advanced Options

- **String Matching** - Search for text in response
- **Latency Measurement** - Track response times
- **SNS Notifications** - Alert on status changes
- **CloudWatch Integration** - Metrics and alarms

### Global Health Checking

- **Checker Locations** - 15+ global locations
- **Majority Rule** - >50% must report healthy
- **Regional Isolation** - Distributed checking prevents false positives

---

## Traffic Flow

### Visual Policy Editor

- **Drag-and-Drop Interface** - Visual routing policy creation
- **Complex Logic** - Combine multiple routing types
- **Version Control** - Policy versioning and rollback
- **Testing** - Test policies before activation

### Policy Components

```
Start Point       - Entry point for DNS queries
Endpoint          - Final destination (IP/domain)
Rule              - Routing decision logic
Geolocation Rule  - Geographic-based routing
Latency Rule      - Performance-based routing
Weighted Rule     - Percentage-based routing
Failover Rule     - Backup routing
Health Check      - Endpoint monitoring
```

---

## Domain Registration

### Domain Management

|Feature|Description|
|---|---|
|**Registration**|Register new domains|
|**Transfer**|Transfer domains from other registrars|
|**Renewal**|Automatic domain renewal|
|**Contact Information**|Manage registrant details|
|**Name Servers**|Configure DNS delegation|
|**Domain Lock**|Transfer protection|

### Supported TLDs

```
Generic: .com, .net, .org, .info, .biz
Country: .us, .uk, .de, .fr, .ca, .au
New gTLDs: .app, .dev, .cloud, .tech
```

### Auto-Renewal

- **Default** - Enabled for new registrations
- **Grace Period** - 30 days after expiration
- **Billing** - Charges to AWS account

---

## Private DNS

### Private Hosted Zones

- **VPC Association** - Link to specific VPCs
- **Cross-Account** - Share across AWS accounts
- **Hybrid Connectivity** - Works with Direct Connect/VPN
- **Resolution** - Only within associated VPCs

### Use Cases

```
Internal Applications    - Private service discovery
Microservices           - Container service names
Development/Testing     - Isolated DNS namespaces
Compliance              - Private domain requirements
```

---

## Monitoring & Logging

### CloudWatch Metrics

#### DNS Queries

```
QueryCount           - Number of DNS queries
ResponseTime         - Query response time
```

#### Health Checks

```
HealthCheckStatus         - 1 (healthy) or 0 (unhealthy)
HealthCheckPercentHealthy - Percentage of healthy checkers
ConnectionTime           - Time to establish connection
TimeToFirstByte         - Time to receive first response byte
```

### Query Logging

- **Destination** - CloudWatch Logs
- **Configuration** - Per hosted zone
- **Content** - Query name, type, response code, client IP
- **Use Cases** - Security analysis, troubleshooting

---

## Pricing Model

### DNS Hosting

- **Hosted Zone** - $0.50 per month per zone
- **DNS Queries** - $0.40 per million queries (first 1B)
- **Alias Queries** - Free for AWS resources

### Health Checks

- **Basic** - $0.50 per health check per month
- **Optional Features** - Additional charges for fast interval, HTTPS, string matching

### Domain Registration

- **Variable Pricing** - Depends on TLD (.com ~$12/year)
- **Transfer Fees** - Same as registration cost
- **Premium Domains** - Market-based pricing

---

## Best Practices

### Performance Optimization

#### TTL Strategy

```
Static Content:    3600s - 86400s (1-24 hours)
Dynamic Content:   300s - 900s (5-15 minutes)
Testing/Development: 60s (1 minute)
Emergency Changes:   30s (minimum practical)
```

#### Geographic Distribution

- **Multi-Region Deployment** - Use latency-based routing
- **Edge Locations** - Leverage CloudFront integration
- **Health Check Placement** - Monitor from multiple regions

### Security Best Practices

- **Domain Lock** - Enable transfer protection
- **DNSSEC** - Enable for supported domains
- **Private Zones** - Use for internal resources
- **Access Control** - IAM policies for Route 53 operations

### Disaster Recovery

#### Failover Configuration

```
Primary Site:     Active endpoint with health checks
Secondary Site:   Standby endpoint in different region
Health Check:     Monitor primary site availability
TTL:              Low TTL for faster failover (60-300s)
```

#### Multi-Level Failover

```
Level 1: Primary region (active)
Level 2: Secondary region (standby)
Level 3: Static maintenance page (S3)
```

---

## Integration Patterns

### Load Balancer Integration

```
Internet → Route 53 → Application Load Balancer → Targets
```

### Multi-Region Architecture

```
Users → Route 53 (Latency-based) → Regional ALB → Application
```

### Microservices Discovery

```
Service A → Private DNS → Service B (internal.company.com)
```

### CDN Integration

```
Users → Route 53 → CloudFront → Origin (S3/ALB)
```

## Common Use Cases

- **Global Load Balancing** - Route traffic to optimal regions
- **Disaster Recovery** - Automatic failover to backup sites
- **Blue-Green Deployments** - Weighted routing for safe deployments
- **Geoblocking** - Restrict access by geographic location
- **Service Discovery** - Internal DNS for microservices
- **Domain Management** - Centralized domain and DNS management

## Practical CLI Examples

### Hosted Zone Management

```bash
# Create public hosted zone
aws route53 create-hosted-zone \
  --name example.com \
  --caller-reference "$(date +%s)" \
  --hosted-zone-config Comment="Production domain for example.com"

# Create private hosted zone
aws route53 create-hosted-zone \
  --name internal.company.com \
  --caller-reference "private-$(date +%s)" \
  --vpc VPCRegion=us-west-2,VPCId=vpc-12345678 \
  --hosted-zone-config Comment="Private DNS for internal services",PrivateZone=true

# List hosted zones
aws route53 list-hosted-zones \
  --query 'HostedZones[*].{Name:Name,Id:Id,RecordCount:ResourceRecordSetCount,Comment:Config.Comment}' \
  --output table

# Get hosted zone details
aws route53 get-hosted-zone \
  --id Z123456789012345678

# Delete hosted zone (must delete all records except NS and SOA first)
aws route53 delete-hosted-zone \
  --id Z123456789012345678
```

### DNS Record Management

```bash
# Create A record
aws route53 change-resource-record-sets \
  --hosted-zone-id Z123456789012345678 \
  --change-batch '{
    "Comment": "Create A record for www",
    "Changes": [{
      "Action": "CREATE",
      "ResourceRecordSet": {
        "Name": "www.example.com",
        "Type": "A",
        "TTL": 300,
        "ResourceRecords": [{"Value": "192.0.2.1"}]
      }
    }]
  }'

# Create alias record for ALB
aws route53 change-resource-record-sets \
  --hosted-zone-id Z123456789012345678 \
  --change-batch '{
    "Comment": "Create alias for load balancer",
    "Changes": [{
      "Action": "CREATE",
      "ResourceRecordSet": {
        "Name": "app.example.com",
        "Type": "A",
        "AliasTarget": {
          "DNSName": "my-alb-1234567890.us-west-2.elb.amazonaws.com",
          "EvaluateTargetHealth": true,
          "HostedZoneId": "Z1D633PJN98FT9"
        }
      }
    }]
  }'

# Create weighted routing records for blue-green deployment
aws route53 change-resource-record-sets \
  --hosted-zone-id Z123456789012345678 \
  --change-batch '{
    "Comment": "Blue-green deployment setup",
    "Changes": [
      {
        "Action": "CREATE",
        "ResourceRecordSet": {
          "Name": "api.example.com",
          "Type": "A",
          "SetIdentifier": "blue",
          "Weight": 100,
          "TTL": 60,
          "ResourceRecords": [{"Value": "192.0.2.10"}]
        }
      },
      {
        "Action": "CREATE",
        "ResourceRecordSet": {
          "Name": "api.example.com",
          "Type": "A",
          "SetIdentifier": "green",
          "Weight": 0,
          "TTL": 60,
          "ResourceRecords": [{"Value": "192.0.2.20"}]
        }
      }
    ]
  }'

# Update weighted routing for traffic shift
aws route53 change-resource-record-sets \
  --hosted-zone-id Z123456789012345678 \
  --change-batch '{
    "Comment": "Shift 20% traffic to green",
    "Changes": [
      {
        "Action": "UPSERT",
        "ResourceRecordSet": {
          "Name": "api.example.com",
          "Type": "A",
          "SetIdentifier": "blue",
          "Weight": 80,
          "TTL": 60,
          "ResourceRecords": [{"Value": "192.0.2.10"}]
        }
      },
      {
        "Action": "UPSERT",
        "ResourceRecordSet": {
          "Name": "api.example.com",
          "Type": "A",
          "SetIdentifier": "green",
          "Weight": 20,
          "TTL": 60,
          "ResourceRecords": [{"Value": "192.0.2.20"}]
        }
      }
    ]
  }'

# Create latency-based routing
aws route53 change-resource-record-sets \
  --hosted-zone-id Z123456789012345678 \
  --change-batch '{
    "Comment": "Latency-based routing setup",
    "Changes": [
      {
        "Action": "CREATE",
        "ResourceRecordSet": {
          "Name": "global.example.com",
          "Type": "A",
          "SetIdentifier": "us-west-2",
          "Region": "us-west-2",
          "TTL": 300,
          "ResourceRecords": [{"Value": "192.0.2.100"}]
        }
      },
      {
        "Action": "CREATE",
        "ResourceRecordSet": {
          "Name": "global.example.com",
          "Type": "A",
          "SetIdentifier": "eu-west-1",
          "Region": "eu-west-1",
          "TTL": 300,
          "ResourceRecords": [{"Value": "192.0.2.200"}]
        }
      }
    ]
  }'

# Create failover routing
aws route53 change-resource-record-sets \
  --hosted-zone-id Z123456789012345678 \
  --change-batch '{
    "Comment": "Failover routing setup",
    "Changes": [
      {
        "Action": "CREATE",
        "ResourceRecordSet": {
          "Name": "service.example.com",
          "Type": "A",
          "SetIdentifier": "primary",
          "Failover": "PRIMARY",
          "TTL": 60,
          "ResourceRecords": [{"Value": "192.0.2.50"}],
          "HealthCheckId": "12345678-1234-1234-1234-123456789012"
        }
      },
      {
        "Action": "CREATE",
        "ResourceRecordSet": {
          "Name": "service.example.com",
          "Type": "A",
          "SetIdentifier": "secondary",
          "Failover": "SECONDARY",
          "TTL": 60,
          "ResourceRecords": [{"Value": "192.0.2.60"}]
        }
      }
    ]
  }'

# List all records in hosted zone
aws route53 list-resource-record-sets \
  --hosted-zone-id Z123456789012345678 \
  --query 'ResourceRecordSets[*].{Name:Name,Type:Type,TTL:TTL,Values:ResourceRecords[*].Value}' \
  --output table
```

### Health Check Management

```bash
# Create HTTP health check
aws route53 create-health-check \
  --caller-reference "web-check-$(date +%s)" \
  --health-check-config '{
    "Type": "HTTP",
    "ResourcePath": "/health",
    "FullyQualifiedDomainName": "api.example.com",
    "Port": 80,
    "RequestInterval": 30,
    "FailureThreshold": 3,
    "EnableSNI": false
  }' \
  --tags '["Key=Name,Value=API Health Check","Key=Environment,Value=Production"]'

# Create HTTPS health check with string matching
aws route53 create-health-check \
  --caller-reference "https-check-$(date +%s)" \
  --health-check-config '{
    "Type": "HTTPS",
    "ResourcePath": "/api/status",
    "FullyQualifiedDomainName": "secure.example.com",
    "Port": 443,
    "RequestInterval": 30,
    "FailureThreshold": 3,
    "SearchString": "\"status\":\"healthy\"",
    "EnableSNI": true
  }'

# Create calculated health check
aws route53 create-health-check \
  --caller-reference "calculated-check-$(date +%s)" \
  --health-check-config '{
    "Type": "CALCULATED",
    "ChildHealthChecks": [
      "12345678-1234-1234-1234-123456789012",
      "87654321-4321-4321-4321-210987654321"
    ],
    "ChildHealthCheckCount": 1,
    "Inverted": false
  }'

# Create CloudWatch alarm health check
aws route53 create-health-check \
  --caller-reference "cloudwatch-check-$(date +%s)" \
  --health-check-config '{
    "Type": "CLOUDWATCH_METRIC",
    "AlarmRegion": "us-west-2",
    "AlarmName": "HighErrorRate",
    "InsufficientDataHealthStatus": "Failure"
  }'

# List health checks
aws route53 list-health-checks \
  --query 'HealthChecks[*].{Id:Id,Type:Config.Type,FQDN:Config.FullyQualifiedDomainName,Path:Config.ResourcePath}' \
  --output table

# Get health check status
aws route53 get-health-check-status \
  --health-check-id 12345678-1234-1234-1234-123456789012

# Update health check
aws route53 update-health-check \
  --health-check-id 12345678-1234-1234-1234-123456789012 \
  --failure-threshold 2 \
  --resource-path "/healthz"

# Delete health check
aws route53 delete-health-check \
  --health-check-id 12345678-1234-1234-1234-123456789012
```

### Domain Registration Operations

```bash
# Check domain availability
aws route53domains check-domain-availability \
  --domain-name example.org

# Get domain suggestions
aws route53domains get-domain-suggestions \
  --domain-name mycompany \
  --suggestion-count 10 \
  --only-available

# Register domain
aws route53domains register-domain \
  --domain-name example.org \
  --duration-in-years 1 \
  --auto-renew \
  --admin-contact '{
    "FirstName": "John",
    "LastName": "Doe",
    "ContactType": "PERSON",
    "OrganizationName": "",
    "AddressLine1": "123 Main St",
    "City": "Seattle",
    "State": "WA",
    "CountryCode": "US",
    "ZipCode": "98101",
    "PhoneNumber": "+1.2065551234",
    "Email": "admin@example.org"
  }' \
  --registrant-contact file://registrant-contact.json \
  --tech-contact file://tech-contact.json

# List domains
aws route53domains list-domains \
  --query 'Domains[*].{Name:DomainName,Expiry:Expiry,AutoRenew:AutoRenew,Status:StatusList[0]}' \
  --output table

# Transfer domain
aws route53domains transfer-domain \
  --domain-name example.net \
  --duration-in-years 1 \
  --auth-code TRANSFER_AUTH_CODE_HERE \
  --admin-contact file://admin-contact.json \
  --registrant-contact file://registrant-contact.json \
  --tech-contact file://tech-contact.json

# Update domain nameservers
aws route53domains update-domain-nameservers \
  --domain-name example.com \
  --nameservers Name=ns-123.awsdns-12.com Name=ns-456.awsdns-45.net Name=ns-789.awsdns-78.org Name=ns-012.awsdns-01.co.uk

# Enable/disable domain lock
aws route53domains update-domain-contact-privacy \
  --domain-name example.com \
  --admin-privacy \
  --registrant-privacy \
  --tech-privacy

# Check operation status
aws route53domains get-operation-detail \
  --operation-id 12345678-1234-1234-1234-123456789012
```

## DevOps Automation Scripts

### DNS Record Automation Script

```python
# dns-automation.py - Automated DNS record management for deployments
import boto3
import json
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Route53Manager:
    def __init__(self, region_name: str = 'us-west-2'):
        self.route53_client = boto3.client('route53', region_name=region_name)
        self.cloudwatch_client = boto3.client('cloudwatch', region_name=region_name)
        
    def get_hosted_zone_id(self, domain_name: str) -> Optional[str]:
        """Get hosted zone ID for a domain"""
        
        try:
            response = self.route53_client.list_hosted_zones()
            
            for zone in response['HostedZones']:
                if zone['Name'].rstrip('.') == domain_name or zone['Name'] == f"{domain_name}.":
                    return zone['Id'].split('/')[-1]  # Extract ID from full ARN
            
            logger.error(f"Hosted zone not found for domain: {domain_name}")
            return None
            
        except Exception as e:
            logger.error(f"Error getting hosted zone for {domain_name}: {e}")
            return None
    
    def create_or_update_record(self, zone_id: str, record_config: Dict) -> bool:
        """Create or update a DNS record"""
        
        try:
            change_batch = {
                'Comment': record_config.get('comment', f"Automated update - {datetime.now().isoformat()}"),
                'Changes': [{
                    'Action': 'UPSERT',
                    'ResourceRecordSet': record_config['record_set']
                }]
            }
            
            response = self.route53_client.change_resource_record_sets(
                HostedZoneId=zone_id,
                ChangeBatch=change_batch
            )
            
            change_id = response['ChangeInfo']['Id']
            logger.info(f"DNS change initiated: {change_id}")
            
            # Wait for change to propagate
            self._wait_for_change(change_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Error creating/updating record: {e}")
            return False
    
    def implement_blue_green_deployment(self, zone_id: str, domain: str, 
                                      blue_target: str, green_target: str, 
                                      traffic_percentage: int = 0) -> bool:
        """Implement blue-green deployment with weighted routing"""
        
        try:
            blue_weight = 100 - traffic_percentage
            green_weight = traffic_percentage
            
            logger.info(f"Setting traffic distribution: Blue {blue_weight}%, Green {green_weight}%")
            
            # Create change batch for both records
            change_batch = {
                'Comment': f"Blue-green deployment: {green_weight}% to green",
                'Changes': [
                    {
                        'Action': 'UPSERT',
                        'ResourceRecordSet': {
                            'Name': domain,
                            'Type': 'A',
                            'SetIdentifier': 'blue',
                            'Weight': blue_weight,
                            'TTL': 60,
                            'ResourceRecords': [{'Value': blue_target}]
                        }
                    },
                    {
                        'Action': 'UPSERT',
                        'ResourceRecordSet': {
                            'Name': domain,
                            'Type': 'A',
                            'SetIdentifier': 'green',
                            'Weight': green_weight,
                            'TTL': 60,
                            'ResourceRecords': [{'Value': green_target}]
                        }
                    }
                ]
            }
            
            response = self.route53_client.change_resource_record_sets(
                HostedZoneId=zone_id,
                ChangeBatch=change_batch
            )
            
            change_id = response['ChangeInfo']['Id']
            self._wait_for_change(change_id)
            
            logger.info(f"Blue-green deployment updated successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error implementing blue-green deployment: {e}")
            return False
    
    def setup_failover_routing(self, zone_id: str, domain: str, 
                              primary_target: str, secondary_target: str,
                              health_check_id: str) -> bool:
        """Setup failover routing with health checks"""
        
        try:
            change_batch = {
                'Comment': f"Failover routing setup for {domain}",
                'Changes': [
                    {
                        'Action': 'UPSERT',
                        'ResourceRecordSet': {
                            'Name': domain,
                            'Type': 'A',
                            'SetIdentifier': 'primary',
                            'Failover': 'PRIMARY',
                            'TTL': 60,
                            'ResourceRecords': [{'Value': primary_target}],
                            'HealthCheckId': health_check_id
                        }
                    },
                    {
                        'Action': 'UPSERT',
                        'ResourceRecordSet': {
                            'Name': domain,
                            'Type': 'A',
                            'SetIdentifier': 'secondary',
                            'Failover': 'SECONDARY',
                            'TTL': 60,
                            'ResourceRecords': [{'Value': secondary_target}]
                        }
                    }
                ]
            }
            
            response = self.route53_client.change_resource_record_sets(
                HostedZoneId=zone_id,
                ChangeBatch=change_batch
            )
            
            change_id = response['ChangeInfo']['Id']
            self._wait_for_change(change_id)
            
            logger.info("Failover routing configured successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error setting up failover routing: {e}")
            return False
    
    def create_health_check(self, check_config: Dict) -> Optional[str]:
        """Create a health check and return its ID"""
        
        try:
            response = self.route53_client.create_health_check(
                CallerReference=f"health-check-{int(time.time())}",
                HealthCheckConfig=check_config
            )
            
            health_check_id = response['HealthCheck']['Id']
            logger.info(f"Health check created: {health_check_id}")
            
            return health_check_id
            
        except Exception as e:
            logger.error(f"Error creating health check: {e}")
            return None
    
    def monitor_health_checks(self, health_check_ids: List[str]) -> Dict:
        """Monitor multiple health checks and return status"""
        
        health_status = {}
        
        for health_check_id in health_check_ids:
            try:
                response = self.route53_client.get_health_check_status(
                    HealthCheckId=health_check_id
                )
                
                # Get latest status from checkers
                latest_status = response['StatusList'][-1] if response['StatusList'] else None
                
                if latest_status:
                    health_status[health_check_id] = {
                        'status': latest_status['Status'],
                        'checked_at': latest_status['CheckedAt'],
                        'region': latest_status.get('Region', 'Unknown')
                    }
                else:
                    health_status[health_check_id] = {'status': 'Unknown'}
                    
            except Exception as e:
                logger.error(f"Error checking health for {health_check_id}: {e}")
                health_status[health_check_id] = {'status': 'Error', 'error': str(e)}
        
        return health_status
    
    def setup_latency_routing(self, zone_id: str, domain: str, endpoints: List[Dict]) -> bool:
        """Setup latency-based routing for multiple regions"""
        
        try:
            changes = []
            
            for endpoint in endpoints:
                change = {
                    'Action': 'UPSERT',
                    'ResourceRecordSet': {
                        'Name': domain,
                        'Type': 'A',
                        'SetIdentifier': endpoint['region'],
                        'Region': endpoint['region'],
                        'TTL': 300,
                        'ResourceRecords': [{'Value': endpoint['ip']}]
                    }
                }
                
                # Add health check if provided
                if endpoint.get('health_check_id'):
                    change['ResourceRecordSet']['HealthCheckId'] = endpoint['health_check_id']
                
                changes.append(change)
            
            change_batch = {
                'Comment': f"Latency-based routing setup for {domain}",
                'Changes': changes
            }
            
            response = self.route53_client.change_resource_record_sets(
                HostedZoneId=zone_id,
                ChangeBatch=change_batch
            )
            
            change_id = response['ChangeInfo']['Id']
            self._wait_for_change(change_id)
            
            logger.info("Latency-based routing configured successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error setting up latency routing: {e}")
            return False
    
    def cleanup_old_records(self, zone_id: str, record_pattern: str, dry_run: bool = True) -> List[str]:
        """Clean up old DNS records matching a pattern"""
        
        try:
            response = self.route53_client.list_resource_record_sets(
                HostedZoneId=zone_id
            )
            
            records_to_delete = []
            
            for record in response['ResourceRecordSets']:
                if (record_pattern in record['Name'] and 
                    record['Type'] not in ['NS', 'SOA']):  # Never delete NS or SOA records
                    
                    records_to_delete.append({
                        'name': record['Name'],
                        'type': record['Type'],
                        'record_set': record
                    })
            
            if dry_run:
                logger.info(f"DRY RUN: Would delete {len(records_to_delete)} records")
                for record in records_to_delete:
                    logger.info(f"  - {record['name']} ({record['type']})")
                return [r['name'] for r in records_to_delete]
            
            # Actually delete records
            if records_to_delete:
                changes = []
                for record in records_to_delete:
                    changes.append({
                        'Action': 'DELETE',
                        'ResourceRecordSet': record['record_set']
                    })
                
                change_batch = {
                    'Comment': f"Cleanup old records matching: {record_pattern}",
                    'Changes': changes
                }
                
                response = self.route53_client.change_resource_record_sets(
                    HostedZoneId=zone_id,
                    ChangeBatch=change_batch
                )
                
                change_id = response['ChangeInfo']['Id']
                self._wait_for_change(change_id)
                
                logger.info(f"Deleted {len(records_to_delete)} records")
            
            return [r['name'] for r in records_to_delete]
            
        except Exception as e:
            logger.error(f"Error cleaning up records: {e}")
            return []
    
    def _wait_for_change(self, change_id: str, timeout: int = 300):
        """Wait for Route 53 change to propagate"""
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                response = self.route53_client.get_change(Id=change_id)
                status = response['ChangeInfo']['Status']
                
                if status == 'INSYNC':
                    logger.info(f"Change {change_id} completed successfully")
                    return True
                
                logger.info(f"Waiting for change {change_id} to propagate... (Status: {status})")
                time.sleep(10)
                
            except Exception as e:
                logger.error(f"Error checking change status: {e}")
                break
        
        logger.warning(f"Change {change_id} did not complete within timeout")
        return False

def main():
    """Example usage of Route53Manager"""
    
    # Initialize manager
    route53_manager = Route53Manager()
    
    # Example: Blue-green deployment
    zone_id = route53_manager.get_hosted_zone_id("example.com")
    if zone_id:
        # Start with 100% traffic to blue
        route53_manager.implement_blue_green_deployment(
            zone_id=zone_id,
            domain="api.example.com",
            blue_target="192.0.2.10",
            green_target="192.0.2.20",
            traffic_percentage=0
        )
        
        # Gradually shift traffic to green
        for percentage in [10, 25, 50, 75, 100]:
            print(f"Shifting {percentage}% traffic to green...")
            route53_manager.implement_blue_green_deployment(
                zone_id=zone_id,
                domain="api.example.com",
                blue_target="192.0.2.10",
                green_target="192.0.2.20",
                traffic_percentage=percentage
            )
            
            # Wait between traffic shifts
            time.sleep(60)
    
    # Example: Setup health checks and failover
    health_check_config = {
        'Type': 'HTTP',
        'ResourcePath': '/health',
        'FullyQualifiedDomainName': 'api.example.com',
        'Port': 80,
        'RequestInterval': 30,
        'FailureThreshold': 3
    }
    
    health_check_id = route53_manager.create_health_check(health_check_config)
    
    if health_check_id and zone_id:
        route53_manager.setup_failover_routing(
            zone_id=zone_id,
            domain="service.example.com",
            primary_target="192.0.2.50",
            secondary_target="192.0.2.60",
            health_check_id=health_check_id
        )

if __name__ == "__main__":
    main()
```

### Health Check Orchestration

```bash
#!/bin/bash
# health-check-orchestrator.sh - Comprehensive health check management

DOMAIN=$1
ENVIRONMENT=${2:-production}
ACTION=${3:-create}

if [ $# -lt 1 ]; then
    echo "Usage: $0 <domain> [environment] [action]"
    echo "Actions: create, update, delete, monitor"
    exit 1
fi

# Configuration
HEALTH_CHECK_CONFIG_DIR="./health-checks"
NOTIFICATION_TOPIC="arn:aws:sns:us-west-2:123456789012:health-check-alerts"

# Create health check configuration file
create_health_check_config() {
    local service_name=$1
    local endpoint=$2
    local path=$3
    local port=${4:-80}
    
    cat > "${HEALTH_CHECK_CONFIG_DIR}/${service_name}.json" << EOF
{
  "Type": "HTTP",
  "ResourcePath": "${path}",
  "FullyQualifiedDomainName": "${endpoint}",
  "Port": ${port},
  "RequestInterval": 30,
  "FailureThreshold": 3,
  "SearchString": "healthy",
  "MeasureLatency": true,
  "Regions": [
    "us-east-1",
    "us-west-1",
    "us-west-2",
    "eu-west-1",
    "ap-southeast-1"
  ]
}
EOF
}

# Create health checks for all services
create_health_checks() {
    echo "Creating health checks for ${DOMAIN} (${ENVIRONMENT})..."
    
    mkdir -p $HEALTH_CHECK_CONFIG_DIR
    
    # Define services and their health check endpoints
    declare -A services=(
        ["web"]="${DOMAIN}:/health:80"
        ["api"]="api.${DOMAIN}:/api/health:80"
        ["auth"]="auth.${DOMAIN}:/auth/status:443"
        ["database"]="db.${DOMAIN}:/status:5432"
    )
    
    for service in "${!services[@]}"; do
        IFS=':' read -r endpoint path port <<< "${services[$service]}"
        
        echo "Creating health check for ${service}..."
        
        # Create configuration
        create_health_check_config "$service" "$endpoint" "$path" "$port"
        
        # Create health check
        HEALTH_CHECK_ID=$(aws route53 create-health-check \
            --caller-reference "${service}-${ENVIRONMENT}-$(date +%s)" \
            --health-check-config file://"${HEALTH_CHECK_CONFIG_DIR}/${service}.json" \
            --query 'HealthCheck.Id' \
            --output text)
        
        if [ $? -eq 0 ]; then
            echo "Created health check for ${service}: ${HEALTH_CHECK_ID}"
            
            # Tag the health check
            aws route53 change-tags-for-resource \
                --resource-type healthcheck \
                --resource-id "$HEALTH_CHECK_ID" \
                --add-tags Key=Name,Value="${service}-${ENVIRONMENT}" \
                       Key=Environment,Value="$ENVIRONMENT" \
                       Key=Service,Value="$service" \
                       Key=Domain,Value="$DOMAIN"
            
            # Store health check ID for later use
            echo "$HEALTH_CHECK_ID" > "${HEALTH_CHECK_CONFIG_DIR}/${service}.id"
            
            # Set up CloudWatch alarm for this health check
            setup_cloudwatch_alarm "$service" "$HEALTH_CHECK_ID"
        else
            echo "Failed to create health check for ${service}"
        fi
    done
}

# Setup CloudWatch alarm for health check
setup_cloudwatch_alarm() {
    local service_name=$1
    local health_check_id=$2
    
    echo "Setting up CloudWatch alarm for ${service_name}..."
    
    aws cloudwatch put-metric-alarm \
        --alarm-name "${service_name}-${ENVIRONMENT}-health-check-failed" \
        --alarm-description "Health check failed for ${service_name} in ${ENVIRONMENT}" \
        --metric-name HealthCheckStatus \
        --namespace AWS/Route53 \
        --statistic Minimum \
        --period 300 \
        --threshold 1 \
        --comparison-operator LessThanThreshold \
        --evaluation-periods 2 \
        --alarm-actions "$NOTIFICATION_TOPIC" \
        --ok-actions "$NOTIFICATION_TOPIC" \
        --dimensions Name=HealthCheckId,Value="$health_check_id" \
        --tags Key=Environment,Value="$ENVIRONMENT" Key=Service,Value="$service_name"
}

# Monitor all health checks
monitor_health_checks() {
    echo "Monitoring health checks for ${DOMAIN} (${ENVIRONMENT})..."
    
    # Get all health checks for this environment
    HEALTH_CHECK_IDS=$(aws route53 list-health-checks \
        --query "HealthChecks[?Tags[?Key=='Environment' && Value=='${ENVIRONMENT}']].Id" \
        --output text)
    
    if [ -z "$HEALTH_CHECK_IDS" ]; then
        echo "No health checks found for environment: $ENVIRONMENT"
        return
    fi
    
    echo "Found health checks: $HEALTH_CHECK_IDS"
    echo ""
    echo "Health Check Status Report - $(date)"
    echo "======================================="
    
    for health_check_id in $HEALTH_CHECK_IDS; do
        # Get health check details
        HEALTH_CHECK_INFO=$(aws route53 get-health-check \
            --health-check-id "$health_check_id" \
            --query 'HealthCheck.{FQDN:Config.FullyQualifiedDomainName,Path:Config.ResourcePath,Type:Config.Type}' \
            --output json)
        
        FQDN=$(echo "$HEALTH_CHECK_INFO" | jq -r '.FQDN')
        PATH=$(echo "$HEALTH_CHECK_INFO" | jq -r '.Path')
        TYPE=$(echo "$HEALTH_CHECK_INFO" | jq -r '.Type')
        
        # Get health check status
        STATUS_INFO=$(aws route53 get-health-check-status \
            --health-check-id "$health_check_id" \
            --query 'StatusList[-1].{Status:Status,Region:Region,CheckedAt:CheckedAt}' \
            --output json 2>/dev/null)
        
        if [ $? -eq 0 ]; then
            STATUS=$(echo "$STATUS_INFO" | jq -r '.Status')
            REGION=$(echo "$STATUS_INFO" | jq -r '.Region')
            CHECKED_AT=$(echo "$STATUS_INFO" | jq -r '.CheckedAt')
            
            # Color coding for status
            if [ "$STATUS" = "Success" ]; then
                STATUS_DISPLAY="✅ $STATUS"
            else
                STATUS_DISPLAY="❌ $STATUS"
            fi
            
            echo "Health Check: $health_check_id"
            echo "  Endpoint: $FQDN$PATH ($TYPE)"
            echo "  Status: $STATUS_DISPLAY (from $REGION)"
            echo "  Last Checked: $CHECKED_AT"
            echo ""
        else
            echo "Health Check: $health_check_id"
            echo "  Endpoint: $FQDN$PATH ($TYPE)"
            echo "  Status: ❓ Unable to retrieve status"
            echo ""
        fi
    done
}

# Update health check configurations
update_health_checks() {
    echo "Updating health checks for ${DOMAIN} (${ENVIRONMENT})..."
    
    # Find health checks for this environment
    HEALTH_CHECKS=$(aws route53 list-health-checks \
        --query "HealthChecks[?Tags[?Key=='Environment' && Value=='${ENVIRONMENT}']].[Id,Config.FullyQualifiedDomainName]" \
        --output text)
    
    while IFS=$'\t' read -r health_check_id fqdn; do
        echo "Updating health check $health_check_id for $fqdn..."
        
        # Update failure threshold to be more sensitive
        aws route53 update-health-check \
            --health-check-id "$health_check_id" \
            --failure-threshold 2 \
            --request-interval 30
        
        if [ $? -eq 0 ]; then
            echo "  ✅ Updated successfully"
        else
            echo "  ❌ Update failed"
        fi
    done <<< "$HEALTH_CHECKS"
}

# Delete health checks
delete_health_checks() {
    echo "Deleting health checks for ${DOMAIN} (${ENVIRONMENT})..."
    
    # Get health checks for this environment
    HEALTH_CHECK_IDS=$(aws route53 list-health-checks \
        --query "HealthChecks[?Tags[?Key=='Environment' && Value=='${ENVIRONMENT}']].Id" \
        --output text)
    
    for health_check_id in $HEALTH_CHECK_IDS; do
        echo "Deleting health check: $health_check_id"
        
        # Delete CloudWatch alarm first
        ALARM_NAME="${ENVIRONMENT}-health-check-${health_check_id}"
        aws cloudwatch delete-alarms --alarm-names "$ALARM_NAME" 2>/dev/null
        
        # Delete health check
        aws route53 delete-health-check --health-check-id "$health_check_id"
        
        if [ $? -eq 0 ]; then
            echo "  ✅ Deleted successfully"
        else
            echo "  ❌ Deletion failed"
        fi
    done
    
    # Cleanup local files
    rm -rf "$HEALTH_CHECK_CONFIG_DIR"
}

# Generate health check report
generate_report() {
    echo "Generating health check report for ${DOMAIN} (${ENVIRONMENT})..."
    
    REPORT_FILE="health-check-report-${ENVIRONMENT}-$(date +%Y%m%d-%H%M%S).json"
    
    # Get all health checks
    aws route53 list-health-checks \
        --query "HealthChecks[?Tags[?Key=='Environment' && Value=='${ENVIRONMENT}']]" \
        --output json > "$REPORT_FILE"
    
    echo "Report saved to: $REPORT_FILE"
    
    # Generate summary
    TOTAL_CHECKS=$(jq length "$REPORT_FILE")
    HEALTHY_CHECKS=$(aws route53 list-health-checks \
        --query "length(HealthChecks[?Tags[?Key=='Environment' && Value=='${ENVIRONMENT}']])" \
        --output text)
    
    echo ""
    echo "Health Check Summary:"
    echo "  Total Checks: $TOTAL_CHECKS"
    echo "  Environment: $ENVIRONMENT"
    echo "  Domain: $DOMAIN"
    echo "  Report File: $REPORT_FILE"
}

# Main execution
case $ACTION in
    "create")
        create_health_checks
        ;;
    "monitor")
        monitor_health_checks
        ;;
    "update")
        update_health_checks
        ;;
    "delete")
        delete_health_checks
        ;;
    "report")
        generate_report
        ;;
    *)
        echo "Unknown action: $ACTION"
        echo "Supported actions: create, monitor, update, delete, report"
        exit 1
        ;;
esac

echo "Health check orchestration completed for ${DOMAIN} (${ENVIRONMENT})"
```

### Traffic Management Automation

```python
# traffic-manager.py - Advanced traffic management and canary deployments
import boto3
import json
import time
import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TrafficManager:
    def __init__(self, region_name: str = 'us-west-2'):
        self.route53_client = boto3.client('route53', region_name=region_name)
        self.cloudwatch_client = boto3.client('cloudwatch', region_name=region_name)
        self.sns_client = boto3.client('sns', region_name=region_name)
        
    def gradual_traffic_shift(self, zone_id: str, domain: str, 
                            current_target: str, new_target: str,
                            shift_schedule: List[Tuple[int, int]],
                            health_check_id: Optional[str] = None,
                            rollback_on_failure: bool = True) -> bool:
        """
        Perform gradual traffic shift with monitoring and automatic rollback
        
        Args:
            zone_id: Route53 hosted zone ID
            domain: Domain name to update
            current_target: Current endpoint (blue)
            new_target: New endpoint (green) 
            shift_schedule: List of (percentage, wait_minutes) tuples
            health_check_id: Health check to monitor during shift
            rollback_on_failure: Whether to rollback automatically on failure
        """
        
        try:
            logger.info(f"Starting gradual traffic shift for {domain}")
            logger.info(f"Schedule: {shift_schedule}")
            
            for percentage, wait_minutes in shift_schedule:
                logger.info(f"Shifting {percentage}% traffic to new target...")
                
                # Update DNS records
                success = self._update_weighted_records(
                    zone_id, domain, current_target, new_target, percentage
                )
                
                if not success:
                    logger.error(f"Failed to update DNS records at {percentage}%")
                    if rollback_on_failure:
                        self._rollback_traffic(zone_id, domain, current_target, new_target)
                    return False
                
                # Wait for DNS propagation
                time.sleep(60)
                
                # Monitor health during wait period
                if health_check_id and wait_minutes > 0:
                    healthy = self._monitor_health_during_shift(
                        health_check_id, wait_minutes
                    )
                    
                    if not healthy and rollback_on_failure:
                        logger.error(f"Health check failed during {percentage}% shift")
                        self._rollback_traffic(zone_id, domain, current_target, new_target)
                        return False
                
                # Additional monitoring metrics
                if percentage > 0:
                    metrics_healthy = self._check_application_metrics(domain, wait_minutes)
                    if not metrics_healthy and rollback_on_failure:
                        logger.error(f"Application metrics degraded during {percentage}% shift")
                        self._rollback_traffic(zone_id, domain, current_target, new_target)
                        return False
                
                if wait_minutes > 0 and percentage < 100:
                    logger.info(f"Waiting {wait_minutes} minutes before next shift...")
                    time.sleep(wait_minutes * 60)
            
            logger.info("Gradual traffic shift completed successfully")
            
            # Final cleanup - remove old target
            self._cleanup_old_target(zone_id, domain, current_target, new_target)
            
            return True
            
        except Exception as e:
            logger.error(f"Error during traffic shift: {e}")
            if rollback_on_failure:
                self._rollback_traffic(zone_id, domain, current_target, new_target)
            return False
    
    def _update_weighted_records(self, zone_id: str, domain: str, 
                               current_target: str, new_target: str, 
                               new_percentage: int) -> bool:
        """Update weighted routing records"""
        
        try:
            current_weight = 100 - new_percentage
            new_weight = new_percentage
            
            change_batch = {
                'Comment': f"Traffic shift: {new_percentage}% to new target",
                'Changes': [
                    {
                        'Action': 'UPSERT',
                        'ResourceRecordSet': {
                            'Name': domain,
                            'Type': 'A',
                            'SetIdentifier': 'current',
                            'Weight': current_weight,
                            'TTL': 60,
                            'ResourceRecords': [{'Value': current_target}]
                        }
                    },
                    {
                        'Action': 'UPSERT',
                        'ResourceRecordSet': {
                            'Name': domain,
                            'Type': 'A',
                            'SetIdentifier': 'new',
                            'Weight': new_weight,
                            'TTL': 60,
                            'ResourceRecords': [{'Value': new_target}]
                        }
                    }
                ]
            }
            
            response = self.route53_client.change_resource_record_sets(
                HostedZoneId=zone_id,
                ChangeBatch=change_batch
            )
            
            # Wait for propagation
            change_id = response['ChangeInfo']['Id']
            self._wait_for_change(change_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating weighted records: {e}")
            return False
    
    def _monitor_health_during_shift(self, health_check_id: str, 
                                   duration_minutes: int) -> bool:
        """Monitor health check during traffic shift"""
        
        logger.info(f"Monitoring health check {health_check_id} for {duration_minutes} minutes")
        
        end_time = datetime.utcnow() + timedelta(minutes=duration_minutes)
        check_interval = 30  # seconds
        failure_count = 0
        max_failures = 3
        
        while datetime.utcnow() < end_time:
            try:
                response = self.route53_client.get_health_check_status(
                    HealthCheckId=health_check_id
                )
                
                if response['StatusList']:
                    latest_status = response['StatusList'][-1]
                    if latest_status['Status'] != 'Success':
                        failure_count += 1
                        logger.warning(f"Health check failure {failure_count}/{max_failures}")
                        
                        if failure_count >= max_failures:
                            logger.error("Health check failed too many times")
                            return False
                    else:
                        failure_count = 0  # Reset on success
                
                time.sleep(check_interval)
                
            except Exception as e:
                logger.error(f"Error checking health: {e}")
                failure_count += 1
                
                if failure_count >= max_failures:
                    return False
        
        return True
    
    def _check_application_metrics(self, domain: str, duration_minutes: int) -> bool:
        """Check application metrics during traffic shift"""
        
        logger.info(f"Monitoring application metrics for {domain}")
        
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(minutes=duration_minutes)
        
        try:
            # Check error rate
            error_rate_response = self.cloudwatch_client.get_metric_statistics(
                Namespace='AWS/ApplicationELB',
                MetricName='HTTPCode_Target_5XX_Count',
                Dimensions=[
                    {'Name': 'LoadBalancer', 'Value': f'app/{domain.replace(".", "-")}'}
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=300,
                Statistics=['Sum']
            )
            
            # Check request count for context
            request_count_response = self.cloudwatch_client.get_metric_statistics(
                Namespace='AWS/ApplicationELB',
                MetricName='RequestCount',
                Dimensions=[
                    {'Name': 'LoadBalancer', 'Value': f'app/{domain.replace(".", "-")}'}
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=300,
                Statistics=['Sum']
            )
            
            total_errors = sum(dp['Sum'] for dp in error_rate_response['Datapoints'])
            total_requests = sum(dp['Sum'] for dp in request_count_response['Datapoints'])
            
            if total_requests > 0:
                error_rate = (total_errors / total_requests) * 100
                logger.info(f"Error rate: {error_rate:.2f}%")
                
                if error_rate > 5.0:  # 5% error rate threshold
                    logger.error(f"High error rate detected: {error_rate:.2f}%")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking application metrics: {e}")
            return False
    
    def _rollback_traffic(self, zone_id: str, domain: str, 
                         current_target: str, new_target: str) -> bool:
        """Rollback traffic to original target"""
        
        logger.info("Rolling back traffic to original target")
        
        try:
            # Set 100% traffic back to current target
            return self._update_weighted_records(
                zone_id, domain, current_target, new_target, 0
            )
            
        except Exception as e:
            logger.error(f"Error during rollback: {e}")
            return False
    
    def _cleanup_old_target(self, zone_id: str, domain: str, 
                          old_target: str, new_target: str) -> bool:
        """Clean up old target after successful migration"""
        
        logger.info("Cleaning up old target records")
        
        try:
            # Remove weighted records and create simple record
            change_batch = {
                'Comment': "Cleanup after successful traffic migration",
                'Changes': [
                    {
                        'Action': 'DELETE',
                        'ResourceRecordSet': {
                            'Name': domain,
                            'Type': 'A',
                            'SetIdentifier': 'current',
                            'Weight': 0,
                            'TTL': 60,
                            'ResourceRecords': [{'Value': old_target}]
                        }
                    },
                    {
                        'Action': 'DELETE',
                        'ResourceRecordSet': {
                            'Name': domain,
                            'Type': 'A',
                            'SetIdentifier': 'new',
                            'Weight': 100,
                            'TTL': 60,
                            'ResourceRecords': [{'Value': new_target}]
                        }
                    },
                    {
                        'Action': 'CREATE',
                        'ResourceRecordSet': {
                            'Name': domain,
                            'Type': 'A',
                            'TTL': 300,
                            'ResourceRecords': [{'Value': new_target}]
                        }
                    }
                ]
            }
            
            response = self.route53_client.change_resource_record_sets(
                HostedZoneId=zone_id,
                ChangeBatch=change_batch
            )
            
            change_id = response['ChangeInfo']['Id']
            self._wait_for_change(change_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Error cleaning up old target: {e}")
            return False
    
    def implement_canary_deployment(self, zone_id: str, domain: str,
                                  stable_target: str, canary_target: str,
                                  canary_percentage: int = 5,
                                  monitoring_duration: int = 30,
                                  success_criteria: Dict = None) -> bool:
        """
        Implement canary deployment with automated promotion or rollback
        
        Args:
            zone_id: Route53 hosted zone ID
            domain: Domain name
            stable_target: Stable version endpoint
            canary_target: Canary version endpoint
            canary_percentage: Percentage of traffic for canary (default 5%)
            monitoring_duration: Minutes to monitor before decision
            success_criteria: Dict with success thresholds
        """
        
        if success_criteria is None:
            success_criteria = {
                'max_error_rate': 2.0,  # 2%
                'min_success_rate': 98.0,  # 98%
                'max_response_time': 2000  # 2 seconds
            }
        
        logger.info(f"Starting canary deployment: {canary_percentage}% to canary")
        
        try:
            # Deploy canary with small traffic percentage
            success = self._update_weighted_records(
                zone_id, domain, stable_target, canary_target, canary_percentage
            )
            
            if not success:
                logger.error("Failed to deploy canary")
                return False
            
            # Monitor canary for specified duration
            logger.info(f"Monitoring canary for {monitoring_duration} minutes...")
            
            # Run monitoring in background
            monitoring_results = self._monitor_canary_metrics(
                domain, monitoring_duration, success_criteria
            )
            
            # Decide whether to promote or rollback
            if monitoring_results['success']:
                logger.info("Canary metrics passed - promoting to full deployment")
                
                # Gradual promotion schedule
                promotion_schedule = [
                    (20, 10),   # 20% for 10 minutes
                    (50, 10),   # 50% for 10 minutes
                    (80, 5),    # 80% for 5 minutes
                    (100, 0)    # 100% 
                ]
                
                return self.gradual_traffic_shift(
                    zone_id, domain, stable_target, canary_target,
                    promotion_schedule, rollback_on_failure=True
                )
            else:
                logger.error("Canary metrics failed - rolling back")
                self._rollback_traffic(zone_id, domain, stable_target, canary_target)
                
                # Send failure notification
                self._send_canary_notification(
                    domain, "FAILED", monitoring_results
                )
                
                return False
                
        except Exception as e:
            logger.error(f"Error in canary deployment: {e}")
            return False
    
    def _monitor_canary_metrics(self, domain: str, duration_minutes: int, 
                              success_criteria: Dict) -> Dict:
        """Monitor canary metrics and return success/failure decision"""
        
        results = {
            'success': True,
            'metrics': {},
            'failures': []
        }
        
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(minutes=duration_minutes)
        
        try:
            # Monitor error rate
            error_rate = self._get_error_rate(domain, start_time, end_time)
            results['metrics']['error_rate'] = error_rate
            
            if error_rate > success_criteria['max_error_rate']:
                results['success'] = False
                results['failures'].append(f"Error rate {error_rate:.2f}% exceeds threshold {success_criteria['max_error_rate']}%")
            
            # Monitor response time
            avg_response_time = self._get_response_time(domain, start_time, end_time)
            results['metrics']['response_time'] = avg_response_time
            
            if avg_response_time > success_criteria['max_response_time']:
                results['success'] = False
                results['failures'].append(f"Response time {avg_response_time}ms exceeds threshold {success_criteria['max_response_time']}ms")
            
            # Calculate success rate
            success_rate = 100 - error_rate
            results['metrics']['success_rate'] = success_rate
            
            if success_rate < success_criteria['min_success_rate']:
                results['success'] = False
                results['failures'].append(f"Success rate {success_rate:.2f}% below threshold {success_criteria['min_success_rate']}%")
            
            logger.info(f"Canary metrics: Error rate {error_rate:.2f}%, Response time {avg_response_time}ms, Success rate {success_rate:.2f}%")
            
        except Exception as e:
            logger.error(f"Error monitoring canary metrics: {e}")
            results['success'] = False
            results['failures'].append(f"Monitoring error: {str(e)}")
        
        return results
    
    def _get_error_rate(self, domain: str, start_time: datetime, end_time: datetime) -> float:
        """Calculate error rate from CloudWatch metrics"""
        
        try:
            # Get error count
            error_response = self.cloudwatch_client.get_metric_statistics(
                Namespace='AWS/ApplicationELB',
                MetricName='HTTPCode_Target_5XX_Count',
                Dimensions=[
                    {'Name': 'LoadBalancer', 'Value': f'app/{domain.replace(".", "-")}'}
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=300,
                Statistics=['Sum']
            )
            
            # Get total request count
            request_response = self.cloudwatch_client.get_metric_statistics(
                Namespace='AWS/ApplicationELB',
                MetricName='RequestCount',
                Dimensions=[
                    {'Name': 'LoadBalancer', 'Value': f'app/{domain.replace(".", "-")}'}
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=300,
                Statistics=['Sum']
            )
            
            total_errors = sum(dp['Sum'] for dp in error_response['Datapoints'])
            total_requests = sum(dp['Sum'] for dp in request_response['Datapoints'])
            
            if total_requests > 0:
                return (total_errors / total_requests) * 100
            
            return 0.0
            
        except Exception as e:
            logger.error(f"Error calculating error rate: {e}")
            return 100.0  # Assume worst case
    
    def _get_response_time(self, domain: str, start_time: datetime, end_time: datetime) -> float:
        """Get average response time from CloudWatch metrics"""
        
        try:
            response = self.cloudwatch_client.get_metric_statistics(
                Namespace='AWS/ApplicationELB',
                MetricName='TargetResponseTime',
                Dimensions=[
                    {'Name': 'LoadBalancer', 'Value': f'app/{domain.replace(".", "-")}'}
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=300,
                Statistics=['Average']
            )
            
            if response['Datapoints']:
                avg_response_time = sum(dp['Average'] for dp in response['Datapoints']) / len(response['Datapoints'])
                return avg_response_time * 1000  # Convert to milliseconds
            
            return 0.0
            
        except Exception as e:
            logger.error(f"Error getting response time: {e}")
            return 10000.0  # Assume worst case
    
    def _send_canary_notification(self, domain: str, status: str, results: Dict):
        """Send notification about canary deployment results"""
        
        try:
            message = f"""
Canary Deployment {status} for {domain}

Status: {status}
Timestamp: {datetime.utcnow().isoformat()}

Metrics:
- Error Rate: {results['metrics'].get('error_rate', 'N/A'):.2f}%
- Response Time: {results['metrics'].get('response_time', 'N/A')}ms
- Success Rate: {results['metrics'].get('success_rate', 'N/A'):.2f}%

Failures:
{chr(10).join(f"- {failure}" for failure in results['failures'])}
"""
            
            self.sns_client.publish(
                TopicArn='arn:aws:sns:us-west-2:123456789012:canary-deployment-alerts',
                Message=message,
                Subject=f"Canary Deployment {status}: {domain}"
            )
            
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
    
    def _wait_for_change(self, change_id: str, timeout: int = 300):
        """Wait for Route 53 change to propagate"""
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                response = self.route53_client.get_change(Id=change_id)
                status = response['ChangeInfo']['Status']
                
                if status == 'INSYNC':
                    return True
                
                time.sleep(10)
                
            except Exception as e:
                logger.error(f"Error checking change status: {e}")
                break
        
        return False

def main():
    """Example usage of TrafficManager"""
    
    # Initialize traffic manager
    traffic_manager = TrafficManager()
    
    # Example: Canary deployment
    zone_id = "Z123456789012345678"
    domain = "api.example.com"
    stable_target = "192.0.2.10"
    canary_target = "192.0.2.20"
    
    # Run canary deployment
    success = traffic_manager.implement_canary_deployment(
        zone_id=zone_id,
        domain=domain,
        stable_target=stable_target,
        canary_target=canary_target,
        canary_percentage=5,
        monitoring_duration=15,
        success_criteria={
            'max_error_rate': 1.0,
            'min_success_rate': 99.0,
            'max_response_time': 1500
        }
    )
    
    if success:
        print("Canary deployment completed successfully")
    else:
        print("Canary deployment failed and was rolled back")

if __name__ == "__main__":
    main()
```

## Best Practices