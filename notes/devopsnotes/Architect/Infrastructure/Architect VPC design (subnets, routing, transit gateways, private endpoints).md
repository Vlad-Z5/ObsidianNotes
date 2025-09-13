# VPC Design (Subnets, Routing, Transit Gateways, Private Endpoints)

Focus: AWS + on-prem hybrid connectivity

## 1. Core Principles of VPC Design

### Isolation & Segmentation

Separate workloads by environment (prod, staging, dev) and purpose (app, DB, logging).

Use VPC per environment or per business unit, depending on scale.

### Subnet Planning

Public subnets: resources exposed to the internet (ALBs, NAT gateways for egress).

Private subnets: resources that should not have direct internet access (DBs, internal services).

Isolated subnets: no NAT, no internet, strictly internal for sensitive workloads (PCI, HIPAA).

### Addressing

Plan CIDRs to avoid overlap with on-prem and other VPCs.

Use RFC1918 ranges, leave space for growth and peering/transit expansions.

### High Availability

Subnets across multiple Availability Zones (AZs) to survive single-AZ failures.

Align subnet placement with routing & NAT/IGW design.

## 2. Routing Architecture

### Internet Gateway (IGW)

Public subnets → IGW → Internet.

NAT for private subnet egress.

### NAT Gateway / NAT Instances

Private subnets use NAT for outbound internet.

Prefer managed NAT Gateways for HA and scalability.

### On-Prem Connectivity

VPN or Direct Connect → attach to VPC via Virtual Private Gateway (VGW) or Transit Gateway (TGW).

Configure BGP dynamic routing for automatic failover.

Route tables:

Private subnets route on-prem traffic to VGW/TGW.

Public subnets route on-prem traffic optionally (depends on need).

### Transit Gateway (TGW)

Central hub for multi-VPC and hybrid networks.

Supports attachments: VPCs, DX gateways, VPNs, inter-region TGW peering.

Simplifies routing by reducing mesh complexity (no N*(N-1) VPC peering).

### Private Endpoints

AWS services (S3, DynamoDB, KMS) accessed privately via VPC Endpoints.

Eliminates need for NAT for service access.

Improves security by removing public traffic paths.

## 3. Subnet & AZ Design Patterns

### Example: Three-tier app

VPC CIDR: 10.10.0.0/16
- Public Subnets (10.10.0.0/24, 10.10.1.0/24) -> ALBs, Bastion
- Private App Subnets (10.10.10.0/24, 10.10.11.0/24) -> App Servers
- Private DB Subnets (10.10.20.0/24, 10.10.21.0/24) -> RDS, Redis


Each subnet spans a different AZ.

Private subnets route outbound traffic via NAT Gateway in public subnet in the same AZ.

On-prem traffic routed via TGW/VGW.

## 4. Security & Isolation

### Network ACLs (stateless)

Optional extra layer; block unwanted ingress/egress.

### Security Groups (stateful)

Per workload; least privilege.

Separate SGs for each tier (ALB → App → DB).

### Private Endpoints & VPC Endpoint Policies

Restrict which principals can access AWS services through endpoint.

Avoid sending traffic over internet.

### Transit Gateway Policies

Route tables per attachment type (prod/non-prod isolation, on-prem routing).

## 5. Resiliency & HA Patterns

### Redundant NATs / Gateways

NAT Gateway per AZ for HA.

IGWs are redundant per VPC automatically.

### Multi-TGW / DX

Multiple TGWs if large-scale cross-region and hybrid requirements.

DX gateway attachments can be multi-region.

### Failover Routing

BGP over VPN/DX handles primary/secondary path automatically.

## 6. Operational Best Practices

Tag all subnets, route tables, endpoints, and TGW attachments by environment and purpose.

Document route tables and ensure no overlapping routes.

Use CIDR planning tools (IPAM, NetBox) to avoid collisions.

Enable flow logs at subnet/TGW level for traffic monitoring.

Automate creation & updates via Terraform or CloudFormation for reproducibility.