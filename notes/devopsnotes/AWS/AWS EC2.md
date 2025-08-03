## **Main EC2 Components**

- **AMI (Amazon Machine Image):** Template containing OS, application software, and configuration. Region specific, can be copied across regions
- **Instance Type:** Defines CPU, memory, storage, and network capacity (e.g., t3.medium)
- **EBS (Elastic Block Store):** Persistent block storage volumes that attach to instances
- **Instance Store (Ephemeral Storage):** Temporary storage physically attached to host, data lost on stop/terminate. Best IO, good for buffer/cache/tmp
- **Security Groups:** Virtual firewalls controlling inbound/outbound traffic
- **Key Pair:** SSH credentials to securely access Linux instances
- **Elastic IP:** Static, public IPv4 address for dynamic cloud computing
- **Network Interface (ENI):** Virtual network card attached to an instance
- **VPC/Subnet:** Network isolation units defining IP range and placement
- **User Data:** Script or commands run on instance launch for initialisation
- **Placement Group:** Controls instance placement strategy (cluster, spread, partition)
- **Elastic Load Balancer (ELB):** Distributes incoming traffic across instances
- **Auto Scaling Group (ASG):** Automatically adjusts instance count based on demand

## **Instance Family Types**

- **General Purpose:** `t4g` (Graviton2), `t3` / `t3a` (Burstable), `m6i` / `m6a` / `m7i`
- **Compute Optimized:** `c6g` / `c6i` / `c7i`
- **Memory Optimized:** `r6i` / `r6a` / `r7i`, `x2idn` / `x2iedn` (High Memory)
- **Storage Optimized:** `i4i` / `i3` (High IOPS), `d3` / `d3en` (Dense HDD)
- **GPU Optimized:** `g4dn` / `g5` (General Purpose), `p3` / `p4` (ML Training)
- **Machine Learning Inference Optimized:** `inf1`
- **High Performance Computing Optimized:** `hpc6id` / `hpc6a`

### **Instance Sizing Convention**

- **Format:** `[family][generation][additional capabilities].[size]`
- **Example:** `m5.large` = General purpose (m), 5th gen, large size
- **Sizes:** `nano`, `micro`, `small`, `medium`, `large`, `xlarge`, `2xlarge`, `4xlarge`, etc.

## **Purchasing Options**

- **Reserved Instances (RI):** Specific **type**, **region**, **tenancy**, **OS**. Scope can be **regional** or **Availability Zone (AZ)**. Terms: **1 or 3 years**
    - **Convertible RI** allows changes to instance family, OS, tenancy, and region
    - **Standard RI** offers higher discount but less flexibility
- **On-Demand:** Pay for compute capacity by the **second** (Windows, Linux) or **hour** (other OS) without long-term commitments
- **Spot Instances:** Use spare capacity at up to 90% discount, can be interrupted. **2 min termination notice** via CloudWatch or instance metadata
- **Dedicated Instance:** EC2 runs on hardware dedicated to a single tenant but shared host. Shared hardware.
- **Dedicated Host:** Physical server fully dedicated to your use. Visibility into sockets, cores, and host ID.
- **Capacity Reservations:** Reserve capacity in a specific AZ for your EC2 instance types
- **Savings Plans:**
    - **Compute Savings Plan:** Applies to EC2, Fargate, Lambda across any region and family
    - **EC2 Instance Savings Plan:** Limited to a specific instance family in a region
    - Both require **1- or 3-year** commitment with **per-hour** billing

## **Storage Options**

### **EBS Volume Types**

- **gp3 (General Purpose SSD):** Latest generation, 3,000-16,000 IOPS, 125-1,000 MB/s throughput
- **gp2 (General Purpose SSD):** Baseline 3 IOPS/GB, burst to 3,000 IOPS
- **io2/io2 Block Express (Provisioned IOPS SSD):** Up to 64,000 IOPS, 99.999% durability
- **io1 (Provisioned IOPS SSD):** Up to 32,000 IOPS, for I/O intensive workloads
- **st1 (Throughput Optimized HDD):** Low cost, frequently accessed workloads
- **sc1 (Cold HDD):** Lowest cost, less frequently accessed workloads

### **EBS Features**

- **Snapshots:** Point-in-time backups stored in S3, incremental
- **Encryption:** At rest and in transit, uses AWS KMS keys
- **Multi-Attach:** Attach single EBS volume to multiple instances (io1/io2 only)
- **Fast Snapshot Restore:** Eliminates latency when restoring from snapshots

### **Instance Store**

- **Characteristics:** High-speed NVMe SSD, ephemeral, included in instance price
- **Use Cases:** Temporary storage, cache, buffer, scratch data
- **Limitations:** Data lost on stop/terminate, hibernate, or instance failure

## **Networking**

### **Security Groups**

- **Stateful:** Return traffic automatically allowed
- **Default Deny:** All inbound traffic blocked by default
- **Allow Rules Only:** Cannot create deny rules
- **Multiple Groups:** Instance can have multiple security groups
- **Source/Destination:** Can reference IP ranges, other security groups, or prefix lists

### **Network Interfaces (ENI)**

- **Primary ENI:** Cannot be detached from instance
- **Secondary ENI:** Can be detached and attached to other instances
- **Attributes:** Private IP, Elastic IP, MAC address, security groups
- **Use Cases:** Management networks, network appliances, dual-homed instances

### **Enhanced Networking**

- **SR-IOV:** Single Root I/O Virtualization for higher bandwidth and lower latency
- **Elastic Network Adapter (ENA):** Up to 100 Gbps network performance
- **Intel 82599 VF:** Legacy enhanced networking option

### **Placement Groups**

- **Cluster:** Packs instances close together in a single AZ for low latency and high throughput
- **Spread:** Distributes instances across different hardware (max 7 per AZ)
- **Partition:** Divides group into partitions with separate hardware (up to 7 partitions per AZ)

## **Auto Scaling Groups (ASG)**

### **Launch Configuration vs Launch Template**

- **Launch Template (Recommended):** Supports latest features, versioning, mixed instance types
- **Launch Configuration (Legacy):** Basic configuration, being phased out

### **Scaling Policies**

- **Target Tracking:** Maintain specific metric (CPU, network, ALB requests)
- **Step Scaling:** Scale based on CloudWatch alarm thresholds
- **Simple Scaling:** Single scaling action based on alarm
- **Predictive Scaling:** Uses ML to predict and scale ahead of demand

### **Health Checks**

- **EC2 Health Check:** Based on EC2 system status checks
- **ELB Health Check:** Based on load balancer health checks
- **Custom Health Check:** Application-defined health status

### **Termination Policies**

- **Default:** Oldest launch configuration, then closest to next billing hour
- **OldestInstance:** Terminate oldest instance first
- **NewestInstance:** Terminate newest instance first
- **OldestLaunchConfiguration:** Terminate instances with oldest launch config

## **Load Balancing**

### **Application Load Balancer (ALB)**

- **Layer 7:** HTTP/HTTPS traffic routing
- **Path/Host-based Routing:** Route based on URL path or hostname
- **Target Types:** Instances, IP addresses, Lambda functions
- **Features:** WebSocket, HTTP/2, sticky sessions, WAF integration

### **Network Load Balancer (NLB)**

- **Layer 4:** TCP/UDP/TLS traffic
- **Ultra-high Performance:** Millions of requests per second
- **Static IP:** One static IP per AZ
- **Use Cases:** Gaming, IoT, real-time applications

### **Gateway Load Balancer (GWLB)**

- **Layer 3:** Network traffic inspection and filtering
- **Use Cases:** Firewalls, intrusion detection, deep packet inspection

### **Classic Load Balancer (CLB)**

- **Legacy:** HTTP/HTTPS and TCP
- **Layer 4 & 7:** Basic load balancing features
- **Status:** Not recommended for new applications

## **Monitoring and Management**

### **CloudWatch Metrics**

- **Basic Monitoring:** 5-minute intervals (free)
- **Detailed Monitoring:** 1-minute intervals (additional cost)
- **Custom Metrics:** Application-specific metrics via CloudWatch agent

### **Instance Metadata and User Data**

- **Metadata Service:** `http://169.254.169.254/latest/meta-data/`
- **IMDSv2:** Session-oriented, more secure version
- **User Data:** `http://169.254.169.254/latest/user-data/`
- **Common Metadata:** Instance ID, AMI ID, instance type, security groups, IAM role

### **Systems Manager**

- **Session Manager:** Browser-based shell access without SSH
- **Patch Manager:** Automated patching of instances
- **Run Command:** Execute commands across multiple instances
- **Parameter Store:** Secure storage for configuration data

## **Security**

### **IAM Roles for EC2**

- **Instance Profile:** Wrapper around IAM role for EC2
- **Temporary Credentials:** Automatically rotated
- **Best Practice:** Use roles instead of storing credentials on instances

### **Key Management**

- **EC2 Key Pairs:** For SSH access to Linux instances
- **Windows Password:** Retrieved using EC2 key pair
- **AWS Systems Manager:** Alternative secure access method

### **Security Best Practices**

- **Principle of Least Privilege:** Minimal required permissions
- **Security Group Rules:** Restrict to necessary ports and sources
- **Regular Patching:** Keep OS and applications updated
- **Encryption:** Enable EBS encryption and in-transit encryption

## **High Availability and Disaster Recovery**

### **Multi-AZ Deployment**

- **Auto Scaling Groups:** Span multiple AZs automatically
- **Load Balancers:** Distribute traffic across AZs
- **EBS Snapshots:** Cross-region backup capability

### **Backup Strategies**

- **EBS Snapshots:** Automated via Data Lifecycle Manager
- **AMI Creation:** Full instance backup including configuration
- **Cross-Region Replication:** Disaster recovery in different regions

## **Cost Optimization**

### **Right Sizing**

- **CloudWatch Metrics:** Monitor CPU, memory, network utilization
- **AWS Compute Optimizer:** ML-powered recommendations
- **Instance Types:** Match workload requirements to instance capabilities

### **Storage Optimization**

- **EBS Volume Types:** Choose appropriate performance tier
- **Snapshot Lifecycle:** Automated deletion of old snapshots
- **EBS Optimization:** Enable for consistent storage performance

### **Reserved Capacity**

- **Reserved Instances:** Long-term workloads with predictable usage
- **Savings Plans:** Flexible commitment-based pricing
- **Spot Instances:** Fault-tolerant workloads with flexible timing

## **Troubleshooting**

### **Common Connection Issues**

- **App Times Out:** Likely a **Security Group or firewall** issue (port not open)
- **Connection Refused:** Likely an **application error**; try restarting the app or the instance
- **Permission Denied (SSH):** Check:
    - **Private key permissions:** `chmod 400 /path/to/your-key.pem`
    - **Correct key used**
    - **Security Group settings** (port 22 open)
    - **IAM role or user permissions**

### **Instance Issues**

- **Instance Not Starting:** Check service limits, subnet capacity, security group rules
- **Performance Issues:** Monitor CloudWatch metrics, check instance type suitability
- **Storage Issues:** Verify EBS volume attachment, check disk space, IOPS limits

### **Network Issues**

- **No Internet Access:** Check route tables, internet gateway, NAT gateway/instance
- **Cross-VPC Communication:** Verify VPC peering, transit gateway, or VPN configuration
- **DNS Resolution:** Check VPC DNS settings, security groups for port 53

## **Advanced Features**

### **Hibernation**

- **Supported Instances:** M3, M4, M5, C3, C4, C5, R3, R4, R5 families
- **Requirements:** EBS root volume, encrypted, specific instance sizes
- **Use Cases:** Long-running applications with extensive initialization

### **Nitro System**

- **Components:** Nitro cards, Nitro security chip, Nitro hypervisor
- **Benefits:** Enhanced performance, security, and feature innovation
- **Instance Types:** Most current generation instances use Nitro

### **Elastic Fabric Adapter (EFA)**

- **Purpose:** High-performance computing and machine learning workloads
- **Features:** Bypass kernel for low-latency communication
- **Use Cases:** MPI applications, distributed ML training

### **GPU and Machine Learning**

- **GPU Instances:** P3, P4, G4, G5 families for ML training and inference
- **AWS Inferentia:** Custom ML inference chips (Inf1 instances)
- **Use Cases:** Deep learning, high-performance computing, graphics workloads

## **Compliance and Governance**

### **AWS Config**

- **Configuration Compliance:** Monitor EC2 configuration changes
- **Compliance Rules:** Automated checks against security baselines
- **Remediation:** Automated fixes for non-compliant resources

### **AWS CloudTrail**

- **API Logging:** Track all EC2 API calls
- **Security Analysis:** Detect unusual activity patterns
- **Compliance Auditing:** Maintain audit trail for compliance requirements

### **Resource Tagging**

- **Cost Allocation:** Track costs by project, environment, team
- **Automation:** Use tags to trigger automated actions
- **Governance:** Enforce tagging policies via AWS Organizations

## **Migration and Modernization**

### **AWS Application Migration Service**

- **Lift and Shift:** Migrate applications without changes
- **Continuous Replication:** Real-time data sync during migration
- **Testing:** Non-disruptive testing of migrated applications

### **VM Import/Export**

- **Supported Formats:** VMware, Hyper-V, KVM virtual machines
- **Use Cases:** Migrate existing VMs to EC2
- **Limitations:** Some OS versions and configurations not supported

### **AWS Image Builder**

- **Automated AMI Creation:** Build and maintain golden images
- **Security Patching:** Automated security updates
- **Compliance:** Ensure images meet organizational standards

## **Miscellaneous Tips**

- **Unused or unattached EIPs** incur **hourly charges**
- **AWS Instance Connect:** Browser-based SSH without needing a key (requires IAM permissions)
- **Instance metadata endpoint:** `curl http://169.254.169.254/latest/meta-data/`
- **EC2 User Data** runs scripts at boot time (found in Advanced Details during launch)
- **Status Checks:** System status (AWS infrastructure) vs Instance status (guest OS)
- **Maintenance Windows:** AWS schedules maintenance, instances may be rebooted
- **Service Limits:** Default limits on instance count, EBS volumes, etc. (can be increased via support)
- **Billing:** Partial instance-hours billed as full hours (except for per-second billing on Linux/Windows)
- **Instance Recovery:** Automatic recovery can restart instances on new hardware if underlying hardware fails