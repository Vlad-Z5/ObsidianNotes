Route 53 is AWS's scalable DNS web service providing domain registration, DNS routing, and health monitoring.

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