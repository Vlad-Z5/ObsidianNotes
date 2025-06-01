Virtual Private Cloud allows you to provision a logically isolated section of AWS cloud
- **Subnets:** Segments within a VPC, can be public or private
- **Size**: min /28 16 addresses, max /16 65536 addresses, can't overlap with other networks
- **Route Tables:** Control traffic routing between subnets and to the internet
- **Internet Gateway (IGW):** Enables internet access for public subnets
- **NAT Gateway:** Allows private subnet instances to access the internet securely
- **Security Groups:** Virtual firewalls controlling inbound/outbound traffic for instances
- **Network ACLs:** Stateless firewalls controlling traffic at subnet level
- **Elastic IPs:** Static public IPv4 addresses for dynamic cloud computing
- **VPC Peering:** Connects two VPCs privately without traversing the internet
- **Endpoints:** Private connection to AWS services without internet traffic

VPC Flow Logs

- **Purpose:** Capture information about IP traffic going to and from network interfaces in a VPC  
- **Collected Data:** Source/destination IP, ports, protocol, packets, bytes, action, log status  
- **Delivery:** Logs sent to Amazon CloudWatch Logs or S3  
- **Granularity:** Can be created at VPC, subnet, or ENI (Elastic Network Interface) level  
- **Use Case:** Troubleshooting, security analysis, monitoring traffic, audit compliance  
- **Limitations:** Does not capture traffic to/from DNS, Windows activation, or link-local addresses (169.254.x.x)

