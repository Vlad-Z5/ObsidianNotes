# AWS VPC (Virtual Private Cloud)

> **Service Type:** Network Foundation | **Tier:** Essential DevOps | **Global/Regional:** Regional

## Overview

AWS VPC allows you to provision a logically isolated section of the AWS cloud where you can launch AWS resources in a virtual network that you define. It provides complete control over your virtual networking environment.

## DevOps Use Cases

### Network Architecture
- **Multi-tier applications** with public and private subnets
- **Microservices isolation** using separate subnets per service
- **Development environments** with network-level separation
- **Hybrid cloud connectivity** via VPN or Direct Connect

### Security Implementation
- **Network segmentation** for compliance and security
- **DMZ implementation** with public-facing load balancers
- **Database isolation** in private subnets without internet access
- **Multi-account networking** with centralized connectivity

### High Availability
- **Multi-AZ deployments** across availability zones
- **Load balancer distribution** across multiple subnets
- **Auto Scaling Groups** spanning multiple subnets
- **Cross-region disaster recovery** networking

### Service Integration
- **EKS cluster networking** with pod and service networking
- **ECS task networking** with ENI attachments
- **Lambda function VPC access** for private resource access
- **RDS subnet groups** for database high availability

## Core Components

### VPC Foundation
- **CIDR Block:** IP address range for your VPC (min /28, max /16)
- **Tenancy:** Default (shared) or Dedicated (single-tenant hardware)
- **DNS Resolution:** Enable DNS hostnames and resolution
- **IPv6 Support:** Optional IPv6 CIDR block assignment

### Subnets
- **Purpose:** Segments within a VPC for resource placement
- **Types:** Public (internet access) or Private (no direct internet)
- **Availability Zones:** Each subnet exists in exactly one AZ
- **Size Constraints:** Cannot overlap with other networks
- **Auto-assign IPs:** Automatic public IP assignment for public subnets

### Routing and Connectivity

#### Route Tables
- **Purpose:** Control traffic routing between subnets and destinations
- **Association:** Each subnet must be associated with one route table
- **Default Route:** 0.0.0.0/0 for internet traffic via Internet Gateway
- **Local Route:** Automatic route for VPC CIDR communication

#### Internet Gateway (IGW)
- **Function:** Enables internet access for public subnets
- **Attachment:** One per VPC, horizontally scaled and highly available
- **Requirements:** Public subnet + route to IGW + public IP/Elastic IP
- **NAT:** Performs 1:1 NAT for instances with public IPs

#### NAT Gateway
- **Purpose:** Allows private subnet instances to access internet securely
- **Placement:** Deployed in public subnet, serves private subnets
- **Bandwidth:** Up to 45 Gbps, automatically scales
- **High Availability:** Deploy one per AZ for fault tolerance
- **Alternative:** NAT Instance (EC2-based, more configuration required)

#### VPC Endpoints
- **Purpose:** Private connection to AWS services without internet traffic
- **Types:** Interface Endpoints (ENI-based) and Gateway Endpoints (route-based)
- **Benefits:** Enhanced security, reduced data transfer costs
- **Supported Services:** S3, DynamoDB (Gateway), most other AWS services (Interface)

#### VPC Peering
- **Purpose:** Connects two VPCs privately without internet transit
- **Routing:** Non-transitive, requires explicit routing configuration
- **Limitations:** No overlapping CIDR blocks, same or different accounts/regions
- **Use Cases:** Shared services, multi-environment connectivity

### Security Components

#### Security Groups
- **Function:** Virtual firewalls controlling inbound/outbound traffic for instances
- **Stateful:** Return traffic automatically allowed
- **Default Behavior:** All outbound allowed, all inbound denied
- **Rules:** Allow rules only (no deny rules)
- **Scope:** Instance-level, can apply multiple security groups

#### Network ACLs (Access Control Lists)
- **Function:** Stateless firewalls controlling traffic at subnet level
- **Default Behavior:** Default NACL allows all traffic
- **Rules:** Both allow and deny rules, numbered priority
- **Stateless:** Return traffic must be explicitly allowed
- **Scope:** Subnet-level, one NACL per subnet

## VPC Flow Logs

- **Purpose:** Capture information about IP traffic going to and from network interfaces in a VPC  
- **Collected Data:** Source/destination IP, ports, protocol, packets, bytes, action, log status  
- **Delivery:** Logs sent to Amazon CloudWatch Logs or S3  
- **Granularity:** Can be created at VPC, subnet, or ENI (Elastic Network Interface) level  
- **Use Case:** Troubleshooting, security analysis, monitoring traffic, audit compliance  
- **Limitations:** Does not capture traffic to/from DNS, Windows activation, or link-local addresses (169.254.x.x)

