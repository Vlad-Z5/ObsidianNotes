Managed relational database service that simplifies setup, operation, and scaling of databases in the cloud.

### **Supported Database Engines**

- **Amazon Aurora** (MySQL and PostgreSQL compatible)
- **MySQL** (5.7, 8.0)
- **PostgreSQL** (11, 12, 13, 14, 15)
- **MariaDB** (10.4, 10.5, 10.6)
- **Oracle** (12c, 19c, 21c)
- **SQL Server** (2016, 2017, 2019, 2022)

### **Core Features**

- Automated provisioning, patching, backups, and snapshots
- Multi-AZ deployments for high availability and disaster recovery
- Read replicas for read scalability (async replication for scaling, sync for DR)
- Encryption at rest (KMS) and in transit (TLS)
- Monitoring and metrics via CloudWatch
- Auto-scaling of compute and storage (vertical and horizontal)
- Storage backed by EBS

### **Deployment Options**

- **Single-AZ:** Standalone instance in one Availability Zone
- **Multi-AZ:** Synchronous replication to standby in different AZ
- **Multi-AZ DB Cluster:** 1 writer + 2 readers across 3 AZs (MySQL, PostgreSQL)

## **Storage Types**

### **General Purpose SSD (gp2)**

- **IOPS:** Baseline 3 IOPS per GB, burst to 3,000 IOPS
- **Size Range:** 20 GB to 65 TB
- **Use Cases:** General workloads with moderate I/O

### **General Purpose SSD (gp3)**

- **IOPS:** Baseline 3,000 IOPS (configurable up to 16,000)
- **Throughput:** 125 MB/s baseline (configurable up to 1,000 MB/s)
- **Size Range:** 20 GB to 65 TB
- **Cost:** More cost-effective than gp2 for most workloads

### **Provisioned IOPS SSD (io1)**

- **IOPS:** Up to 64,000 IOPS (50 IOPS per GB ratio)
- **Size Range:** 100 GB to 65 TB
- **Use Cases:** I/O-intensive workloads requiring consistent performance

### **Provisioned IOPS SSD (io2)**

- **IOPS:** Up to 256,000 IOPS (1,000 IOPS per GB ratio)
- **Durability:** 99.999% annual durability
- **Size Range:** 100 GB to 65 TB

### **Magnetic Storage**

- **Legacy:** Not recommended for new applications
- **Size Range:** 20 GB to 3 TB
- **Use Cases:** Backward compatibility only

## **Backup and Recovery**

### **Automated Backups**

- **Retention Period:** 0-35 days (0 disables automated backups)
- **Backup Window:** 30-minute window during low-activity period
- **Point-in-Time Recovery:** Restore to any second within retention period
- **Transaction Logs:** Backed up every 5 minutes to S3

### **Manual Snapshots**

- **Retention:** User-defined, persists beyond DB instance deletion
- **Cross-Region Copy:** Copy snapshots to different regions
- **Sharing:** Share snapshots with other AWS accounts
- **Encryption:** Can encrypt unencrypted snapshots during copy

### **Aurora Backtrack**

- **MySQL Compatible Only:** Rewind database to specific point in time
- **No Downtime:** Backtrack without restoring from backup
- **Time Range:** Up to 72 hours
- **Use Cases:** Quickly recover from user errors

## **High Availability and Disaster Recovery**

### **Multi-AZ Deployments**

- **Synchronous Replication:** Primary to standby instance
- **Automatic Failover:** Typically 1-2 minutes
- **Maintenance:** Updates applied to standby first
- **Endpoint:** Same DNS endpoint maintained during failover

### **Multi-AZ DB Cluster (MySQL/PostgreSQL)**

- **Architecture:** 1 writer + 2 readers across 3 AZs
- **Failover Time:** Under 35 seconds typically
- **Read Scaling:** Readers can serve read traffic
- **Storage:** Shared cluster storage

### **Read Replicas**

- **Asynchronous Replication:** From source to replica
- **Cross-Region:** Replicas in different regions
- **Promotion:** Can promote replica to standalone DB
- **Scaling:** Up to 5 read replicas for most engines (15 for Aurora)
- **Use Cases:** Read scaling, analytics, disaster recovery

### **Cross-Region Automated Backups**

- **Automated Replication:** Backups replicated to different region
- **Point-in-Time Recovery:** Cross-region PITR capability
- **Retention:** Independent retention settings per region

## **Security**

### **Network Security**

- **VPC:** Database instances launched in VPC subnets
- **Security Groups:** Control inbound/outbound traffic
- **DB Subnet Groups:** Define subnets for Multi-AZ deployment
- **Private Subnets:** Keep databases in private subnets

### **Encryption**

- **At Rest:** AES-256 encryption using AWS KMS
- **In Transit:** SSL/TLS encryption for all connections
- **Transparent Data Encryption (TDE):** Oracle and SQL Server
- **Key Management:** Customer-managed or AWS-managed keys

### **Access Control**

- **IAM Database Authentication:** Use IAM roles instead of passwords
- **Database Users:** Traditional username/password authentication
- **Master User:** Administrative access to database
- **Resource-Level Permissions:** IAM policies for RDS resources

### **Auditing and Monitoring**

- **Database Activity Streams:** Real-time stream of database activity
- **Performance Insights:** Enhanced monitoring for database performance
- **CloudWatch Logs:** Database logs exported to CloudWatch
- **AWS CloudTrail:** API-level logging for RDS actions

## **Performance and Monitoring**

### **Performance Insights**

- **Database Performance:** Visualize database load and bottlenecks
- **Wait Events:** Identify what's causing database slowdowns
- **Top SQL:** Most resource-intensive queries
- **Retention:** 7 days free, up to 2 years with additional cost

### **Enhanced Monitoring**

- **Real-Time Metrics:** CPU, memory, I/O, network at 1-second intervals
- **Process List:** Real-time view of database processes
- **CloudWatch Integration:** Custom dashboards and alarms

### **Parameter Groups**

- **Database Configuration:** Manage database engine parameters
- **Dynamic Parameters:** Apply changes without restart
- **Static Parameters:** Require restart to apply
- **Custom Groups:** Create custom configurations for different workloads

### **Option Groups**

- **Database Features:** Enable additional database features
- **Engine-Specific:** Oracle and SQL Server primarily
- **Examples:** Oracle Advanced Security, SQL Server Agent

## **Scaling**

### **Vertical Scaling**

- **Instance Class:** Change CPU, memory, and network capacity
- **Storage Scaling:** Increase storage size (cannot decrease)
- **IOPS Scaling:** Modify provisioned IOPS for io1/io2
- **Downtime:** Brief downtime during instance class change

### **Horizontal Scaling**

- **Read Replicas:** Scale read capacity across multiple instances
- **Aurora Auto Scaling:** Automatically add/remove replicas
- **Connection Pooling:** Use RDS Proxy for connection management
- **Sharding:** Application-level data partitioning

### **Aurora Serverless Scaling**

- **Automatic:** Scales based on database load
- **Scaling Events:** CPU utilization, connection count
- **Scaling Time:** Typically seconds to minutes
- **Capacity Units:** Measure of compute and memory capacity

## **RDS Proxy**

### **Connection Management**

- **Connection Pooling:** Efficient connection sharing
- **Failover Handling:** Transparent failover for applications
- **Security:** IAM authentication, Secrets Manager integration

### **Benefits**

- **Improved Scalability:** Handle more concurrent connections
- **Enhanced Availability:** Faster failover times
- **Better Security:** Centralized credential management
- **Reduced Database Load:** Connection pooling reduces overhead

### **Use Cases**

- **Serverless Applications:** Lambda functions with database connections
- **Microservices:** Multiple services sharing database connections
- **Applications with Variable Load:** Connection bursts and idle periods

## **Migration**

### **AWS Database Migration Service (DMS)**

- **Homogeneous Migration:** Same database engine (Oracle to Oracle)
- **Heterogeneous Migration:** Different engines (Oracle to MySQL)
- **Continuous Replication:** Ongoing replication for minimal downtime
- **Schema Conversion Tool:** Convert database schemas

### **Native Tools**

- **mysqldump/pg_dump:** Export/import for smaller databases
- **AWS CLI:** Restore from snapshots or backup files
- **Third-Party Tools:** Use vendor-specific migration tools

### **Blue/Green Deployments**

- **RDS Blue/Green:** Clone environment for testing changes
- **Automatic Switchover:** Seamless traffic switch
- **Rollback Capability:** Quick rollback if issues occur

## **Cost Optimization**

### **Instance Sizing**

- **Right-Sizing:** Match instance size to workload requirements
- **Burstable Instances:** t3/t4g for variable workloads
- **Reserved Instances:** 1-3 year commitments for steady workloads

### **Storage Optimization**

- **Storage Type Selection:** Choose appropriate storage for IOPS needs
- **Storage Auto Scaling:** Automatic storage increase when needed
- **Snapshot Management:** Delete unnecessary snapshots

### **Multi-AZ Considerations**

- **Development/Testing:** Single-AZ for non-production
- **Production:** Multi-AZ for high availability requirements
- **Read Replicas:** Cost-effective read scaling vs. larger instances

### **Aurora Serverless**

- **Variable Workloads:** Pay only for actual usage
- **Development/Testing:** Automatic pause during inactivity
- **Capacity Planning:** No need to provision for peak capacity

## **Troubleshooting**

### **Common Connection Issues**

- **Security Groups:** Ensure database port is open (3306 MySQL, 5432 PostgreSQL)
- **Network ACLs:** Verify subnet-level access rules
- **DNS Resolution:** Check endpoint resolution in VPC
- **SSL/TLS:** Verify SSL requirements and certificates

### **Performance Issues**

- **Slow Queries:** Use Performance Insights to identify bottlenecks
- **IOPS Limitations:** Monitor I/O metrics, consider io1/io2 storage
- **Connection Limits:** Check max_connections parameter
- **Memory Pressure:** Monitor memory utilization, consider larger instance

### **Backup and Recovery Issues**

- **Backup Window:** Ensure adequate backup window duration
- **Snapshot Failures:** Check storage space and IAM permissions
- **Cross-Region Issues:** Verify KMS key permissions for encryption
- **Point-in-Time Recovery:** Ensure binary logging is enabled

### **Multi-AZ Issues**

- **Failover Testing:** Regularly test failover procedures
- **Replication Lag:** Monitor replica lag in Multi-AZ setup
- **Standby Instance:** Verify standby is in sync with primary

## **Best Practices**

### **Security Best Practices**

- **Network Isolation:** Place databases in private subnets
- **Encryption:** Enable encryption at rest and in transit
- **Access Control:** Use IAM database authentication where possible
- **Regular Updates:** Keep database engines updated
- **Audit Logging:** Enable appropriate audit logging

### **Performance Best Practices**

- **Connection Pooling:** Use RDS Proxy or application-level pooling
- **Query Optimization:** Regular query performance analysis
- **Indexing Strategy:** Proper index design and maintenance
- **Parameter Tuning:** Optimize database parameters for workload

### **Operational Best Practices**

- **Monitoring:** Set up CloudWatch alarms for key metrics
- **Backup Strategy:** Regular backup testing and validation
- **Maintenance Windows:** Schedule during low-traffic periods
- **Change Management:** Test changes in non-production first
- **Documentation:** Maintain runbooks for common procedures

### **Cost Management Best Practices**

- **Resource Tagging:** Tag all RDS resources for cost allocation
- **Regular Review:** Monitor costs and optimize regularly
- **Reserved Instances:** Use for predictable workloads
- **Development Practices:** Use smaller instances for dev/test

## **Engine-Specific Considerations**

### **MySQL**

- **InnoDB:** Default and recommended storage engine
- **Binary Logging:** Required for read replicas and PITR
- **Character Sets:** UTF-8 recommended for international applications

### **PostgreSQL**

- **Extensions:** Rich ecosystem of extensions available
- **Logical Replication:** Native logical replication support
- **JSON Support:** Advanced JSON data type support

### **Oracle**

- **License Included vs BYOL:** Choose appropriate licensing model
- **RAC:** Not supported, use Multi-AZ for high availability
- **Advanced Features:** Available through option groups

### **SQL Server**

- **Edition Support:** Express, Web, Standard, Enterprise editions
- **Windows Authentication:** Not supported, use SQL authentication
- **Linked Servers:** Not supported in RDS

## **Compliance and Governance**

### **Compliance Standards**

- **SOC 1, 2, 3:** System and Organization Controls compliance
- **PCI DSS:** Payment Card Industry compliance
- **HIPAA:** Healthcare data compliance
- **FedRAMP:** Federal government compliance

### **Data Governance**

- **Data Classification:** Tag and classify sensitive data
- **Data Retention:** Implement appropriate retention policies
- **Data Privacy:** GDPR and other privacy regulation compliance
- **Audit Requirements:** Maintain audit trails for compliance

### **Resource Management**

- **AWS Config:** Track configuration changes
- **AWS CloudFormation:** Infrastructure as code for RDS resources
- **AWS Organizations:** Centralized account management
- **Service Control Policies:** Restrict actions across accounts

## **Miscellaneous Tips**

- **Default Ports:** MySQL (3306), PostgreSQL (5432), Oracle (1521), SQL Server (1433)
- **Connection Limits:** Vary by instance class and engine
- **Maintenance Windows:** Automatic updates applied during maintenance window
- **Force Failover:** Can manually trigger Multi-AZ failover for testing
- **Cross-Region Snapshots:** Useful for disaster recovery and compliance
- **Database Activity Streams:** Real-time audit capabilities for supported engines
- **Blue/Green Deployments:** Available for testing major changes safely
- **RDS Extended Support:** Continue receiving updates for older engine versions