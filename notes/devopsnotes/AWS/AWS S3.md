Object storage service that offers industry-leading scalability, data availability, security, and performance.

### **Key Features**

- **Object Storage:** Stores files as objects in buckets (flat namespace), great for larger files rather than small ones so zipping them is a good idea (max object size 5 TB)
- **Durability:** 99.999999999% (11 9s) - designed to sustain loss of data in two facilities
- **Availability:** Varies by storage class (99.99% to 99.5%)
- **Versioning:** Preserve, retrieve, restore any version of object (can be suspended)
- **Encryption:** SSE-S3 (default), SSE-KMS, SSE-C, or client-side
- **Cross-Region Replication (CRR):** For disaster recovery and compliance
- **Same-Region Replication (SRR):** For log aggregation, compliance, or backups
- **Cross-Origin Resource Sharing (CORS):** Access S3 from different domains
- **Pre-Signed URLs:** Temporary access for specific actions
- **Virtually Unlimited Storage:** No capacity planning required
- **Global Namespace:** Bucket names must be globally unique

## **S3 Storage Classes**

### **Frequent Access**

- **S3 Standard:**
    - **Availability:** 99.99%
    - **Use Cases:** Frequently accessed data, websites, content distribution
    - **Minimum Storage Duration:** None
    - **Retrieval Time:** Milliseconds

### **Infrequent Access**

- **S3 Standard-IA (Infrequent Access):**
    
    - **Availability:** 99.9%
    - **Cost:** Lower storage cost, retrieval fee applies
    - **Minimum Storage Duration:** 30 days
    - **Use Cases:** Backups, disaster recovery, long-term storage
    
- **S3 One Zone-IA:**
    
    - **Availability:** 99.5%
    - **Durability:** 99.999999999% (single AZ)
    - **Cost:** 20% less than Standard-IA
    - **Use Cases:** Easily recreatable data, secondary backups

### **Archive Classes**

- **S3 Glacier Instant Retrieval:**
    
    - **Retrieval Time:** Milliseconds (same as Standard)
    - **Use Cases:** Data accessed quarterly, medical images, news media
    - **Minimum Storage Duration:** 90 days
    - **Cost:** Lowest for instant retrieval archive

- **S3 Glacier Flexible Retrieval (formerly Glacier):**
    
    - **Retrieval Options:**
        - Expedited: 1-5 minutes
        - Standard: 3-5 hours
        - Bulk: 5-12 hours
    - **Minimum Storage Duration:** 90 days
    - **Use Cases:** Archives, backup, disaster recovery

- **S3 Glacier Deep Archive:**
    
    - **Retrieval Time:** 12-48 hours
    - **Minimum Storage Duration:** 180 days
    - **Cost:** Lowest storage cost
    - **Use Cases:** Long-term retention, compliance, digital preservation

### **Intelligent Storage**

- **S3 Intelligent-Tiering:**
    - **Automatic Optimization:** Moves objects between access tiers
    - **No Retrieval Fees:** Between frequent and infrequent tiers
    - **Monitoring Fee:** Small monthly fee per object
    - **Tiers:**
        - Frequent Access (automatic)
        - Infrequent Access (automatic, 30+ days)
        - Archive Instant Access (optional, 90+ days)
        - Archive Access (optional, 90+ days)
        - Deep Archive Access (optional, 180+ days)

### **Storage Class Comparison**

|Class|Durability|Availability|Min Duration|Retrieval Time|Use Case|
|---|---|---|---|---|---|
|Standard|11 9s|99.99%|None|Milliseconds|Frequent access|
|Standard-IA|11 9s|99.9%|30 days|Milliseconds|Infrequent access|
|One Zone-IA|11 9s|99.5%|30 days|Milliseconds|Non-critical data|
|Glacier Instant|11 9s|99.9%|90 days|Milliseconds|Archive with instant access|
|Glacier Flexible|11 9s|99.99%|90 days|1min-12hrs|Archive|
|Glacier Deep|11 9s|99.99%|180 days|12-48 hours|Long-term archive|
|Intelligent-Tiering|11 9s|99.9%|None|Variable|Unknown/changing patterns|

## **Security and Access Control**

### **Bucket Policies**

- **JSON-Based:** Define permissions using AWS policy language
- **Resource-Based:** Attached to buckets, not users
- **Conditions:** IP addresses, time of day, SSL requirements
- **Cross-Account Access:** Grant permissions to other AWS accounts
- **Example Elements:** Principal, Action, Resource, Condition

### **IAM Policies**

- **User-Based:** Attached to IAM users, groups, or roles
- **Fine-Grained Control:** Specific actions on specific resources
- **Cross-Service:** Can include permissions for other AWS services
- **Policy Evaluation:** IAM + Bucket Policy = Union of permissions

### **Access Control Lists (ACLs)**

- **Legacy Method:** Pre-dates IAM and bucket policies
- **Object-Level:** Can be applied to individual objects
- **Limited Permissions:** Read, write, read ACP, write ACP, full control
- **Canned ACLs:** Pre-defined ACL templates
- **Best Practice:** Use IAM and bucket policies instead

### **Block Public Access**

- **Account-Level:** Apply to entire AWS account
- **Bucket-Level:** Apply to specific buckets
- **Settings:**
    - Block public ACLs
    - Ignore public ACLs
    - Block public bucket policies
    - Restrict public buckets
- **Override:** Can be overridden at bucket level (if account allows)

### **Encryption**

#### **Server-Side Encryption (SSE)**

- **SSE-S3 (AES-256):**
    
    - **Default:** Applied to all new objects
    - **AWS Managed:** AWS handles key management
    - **Header:** `x-amz-server-side-encryption: AES256`
- **SSE-KMS:**
    
    - **AWS KMS Keys:** Customer-managed or AWS-managed
    - **Audit Trail:** CloudTrail logs key usage
    - **Request Quotas:** KMS API call limits apply
    - **Header:** `x-amz-server-side-encryption: aws:kms`
- **SSE-C (Customer-Provided):**
    
    - **Customer Keys:** You provide encryption keys
    - **HTTPS Required:** Keys transmitted over SSL
    - **No Key Storage:** AWS doesn't store the keys
    - **Your Responsibility:** Key management and rotation

#### **Client-Side Encryption**

- **Encrypt Before Upload:** Data encrypted on client side
- **AWS Encryption SDK:** Tools for client-side encryption
- **Key Management:** Fully managed by customer
- **Use Cases:** Highly sensitive data, compliance requirements

### **Access Logging**

- **Server Access Logs:** Detailed records of requests
- **Log Format:** Standard fields including requester, bucket, time, action
- **Destination:** Store logs in another S3 bucket
- **CloudTrail Integration:** API-level logging for S3 actions
- **Best Practice:** Enable for security auditing and compliance

## **Data Management**

### **Versioning**

- **Object Versions:** Multiple versions of same object key
- **Version ID:** Unique identifier for each version
- **States:** Enabled, Suspended, Never Enabled
- **Delete Behavior:** Creates delete marker (soft delete)
- **Permanent Delete:** Specify version ID to permanently delete
- **Storage Cost:** Each version consumes storage
- **Lifecycle Integration:** Can manage versions with lifecycle rules

### **Lifecycle Management**

- **Transition Actions:** Move objects between storage classes
- **Expiration Actions:** Delete objects after specified time
- **Rule Scope:** Apply to entire bucket, prefix, or tags
- **Versioned Objects:** Can manage current and non-current versions
- **Incomplete Multipart Uploads:** Clean up failed uploads
- **Examples:**
    - Transition to IA after 30 days
    - Archive to Glacier after 90 days
    - Delete after 365 days

### **Cross-Region Replication (CRR)**

- **Requirements:**
    - Versioning enabled on both buckets
    - IAM role with replication permissions
    - Buckets in different regions
- **What Replicates:** New objects, metadata, ACLs, tags
- **What Doesn't:** Existing objects (before rule), objects encrypted with SSE-C
- **Storage Class:** Can replicate to different storage class
- **Use Cases:** Compliance, disaster recovery, latency reduction

### **Same-Region Replication (SRR)**

- **Similar to CRR:** Same requirements and behavior
- **Use Cases:** Log aggregation, production/test environments, compliance
- **Benefits:** Lower replication costs, faster replication

### **Replication Features**

- **Replica Modification Sync:** Replicate metadata changes
- **Delete Marker Replication:** Replicate delete markers
- **Existing Object Replication:** Replicate objects created before rule
- **Two-Way Replication:** Bidirectional replication between buckets
- **Multiple Destinations:** Replicate to multiple destination buckets

## **Performance and Access**

### **Request Patterns**

- **Request Rate:** 3,500 PUT/COPY/POST/DELETE and 5,500 GET/HEAD per prefix per second
- **Prefix Optimization:** Distribute requests across multiple prefixes
- **Hot Spotting:** Avoid sequential naming patterns
- **Performance Scaling:** Automatically scales to high request rates

### **Transfer Acceleration**

- **CloudFront Edge Locations:** Upload via nearest edge location
- **Global Acceleration:** Faster uploads from distant locations
- **Cost:** Additional charges apply
- **Compatibility:** Works with multipart uploads and PUT operations
- **Testing:** AWS provides speed comparison tool

### **Multipart Upload**

- **Large Objects:** Recommended for objects > 100 MB
- **Required:** Objects > 5 GB must use multipart
- **Parallel Uploads:** Upload parts simultaneously
- **Resume Capability:** Resume interrupted uploads
- **Part Size:** 5 MB to 5 GB per part
- **Maximum Parts:** 10,000 parts per object

### **S3 Select**

- **Query in Place:** Use SQL to query object contents
- **Supported Formats:** CSV, JSON, Parquet
- **Performance:** Retrieve only needed data (up to 400% faster)
- **Cost Savings:** Pay for scanned data, not entire object
- **Compression:** Works with GZIP and BZIP2

### **S3 Batch Operations**

- **Large-Scale Operations:** Perform actions on billions of objects
- **Supported Operations:** Copy, set tags, ACLs, restore from Glacier
- **Job Management:** Create, monitor, and manage batch jobs
- **Inventory Integration:** Use S3 Inventory as input
- **Cost Control:** Built-in retry logic and progress tracking

## **Access Methods and URLs**

### **REST API Endpoints**

- **Virtual-Hosted Style:** `https://bucket-name.s3.region.amazonaws.com/key`
- **Path Style:** `https://s3.region.amazonaws.com/bucket-name/key` (deprecated)
- **Legacy Global:** `https://bucket-name.s3.amazonaws.com/key` (us-east-1 only)

### **Pre-Signed URLs**

- **Temporary Access:** Time-limited URLs for specific operations
- **Security:** Inherits permissions of signing entity
- **Expiration:** Configurable expiry time (max 7 days for IAM users)
- **Use Cases:** File uploads from web apps, temporary downloads
- **Generation:** AWS CLI, SDKs, or manual signing process

### **AWS CLI and SDKs**

- **AWS CLI:** Command-line interface for S3 operations
- **High-Level Commands:** `aws s3 cp`, `aws s3 sync`
- **Low-Level Commands:** `aws s3api` for direct API access
- **SDKs:** Available for most programming languages
- **Configuration:** Supports profiles, regions, output formats

## **Event Notifications**

### **Supported Events**

- **Object Operations:** Created, Removed, Restore initiated/completed
- **Event Types:**
    - s3:ObjectCreated:* (Put, Post, Copy, CompleteMultipartUpload)
    - s3:ObjectRemoved:* (Delete, DeleteMarkerCreated)
    - s3:ObjectRestore:* (Post, Completed)
    - s3:Replication:* (OperationFailedReplication, etc.)

### **Destinations**

- **Amazon SNS:** Simple Notification Service topics
- **Amazon SQS:** Simple Queue Service queues
- **AWS Lambda:** Direct function invocation
- **Amazon EventBridge:** Advanced event routing

### **Configuration**

- **Event Filters:** Filter by object key prefix/suffix
- **Multiple Notifications:** Same event to multiple destinations
- **Event Message:** JSON format with bucket and object details
- **Delivery:** At-least-once delivery guarantee

## **Website Hosting**

### **Static Website Hosting**

- **Configuration:** Enable in bucket properties
- **Index Document:** Default page (e.g., index.html)
- **Error Document:** Custom error page (e.g., error.html)
- **Endpoint:** `http://bucket-name.s3-website-region.amazonaws.com`
- **Public Access:** Requires public read permissions

### **Custom Domain**

- **DNS Configuration:** CNAME or Route 53 alias
- **SSL/TLS:** Use CloudFront for HTTPS
- **Requirements:** Bucket name must match domain name
- **Redirects:** Support for redirect rules and routing

### **Redirect Configuration**

- **Website Redirects:** Redirect all requests to another host
- **Routing Rules:** Conditional redirects based on key prefix/HTTP code
- **Use Cases:** Domain migration, URL restructuring

## **Monitoring and Analytics**

### **CloudWatch Metrics**

- **Storage Metrics:** Bucket size, object count by storage class
- **Request Metrics:** Request count, errors, latency
- **Data Retrieval Metrics:** Bytes downloaded, upload/download rates
- **Replication Metrics:** Replication latency, failure count

### **S3 Storage Lens**

- **Organization-Wide:** Visibility across all accounts and buckets
- **Cost Optimization:** Identify optimization opportunities
- **Data Protection:** Monitor encryption and versioning compliance
- **Access Patterns:** Understand usage patterns and trends
- **Default Dashboard:** Free metrics with 28-day retention
- **Advanced Metrics:** Detailed metrics with longer retention (additional cost)

### **S3 Inventory**

- **Bucket Contents:** Scheduled reports of objects and metadata
- **Output Formats:** CSV, ORC, or Parquet
- **Delivery:** Daily or weekly to destination bucket
- **Use Cases:** Audit, compliance, lifecycle management planning
- **Encryption:** Can be encrypted with SSE-S3 or SSE-KMS

### **Access Analyzer for S3**

- **Public Access Detection:** Identify buckets with public access
- **External Access:** Buckets accessible from outside your account
- **Policy Analysis:** Analyze bucket policies and ACLs
- **Integration:** Part of AWS IAM Access Analyzer

## **Cost Optimization**

### **Storage Cost Optimization**

- **Right Storage Class:** Choose appropriate class for access patterns
- **Lifecycle Policies:** Automatic transitions to lower-cost storage
- **Intelligent-Tiering:** Automatic optimization for unknown patterns
- **Delete Incomplete Uploads:** Clean up failed multipart uploads
- **Versioning Management:** Delete unnecessary object versions

### **Request Cost Optimization**

- **Request Patterns:** Minimize LIST operations
- **CloudFront Integration:** Cache frequently accessed content
- **S3 Select:** Query only needed data instead of entire objects
- **Batch Operations:** Efficient large-scale operations

### **Data Transfer Optimization**

- **Transfer Acceleration:** May reduce costs for global users
- **Direct Connect:** Dedicated network connection for large transfers
- **CloudFront:** Reduce origin requests through caching
- **Same-Region Resources:** Minimize cross-region transfer costs

## **Integration with Other AWS Services**

### **Compute Services**

- **Lambda:** Event-driven processing, data transformation
- **EC2:** Direct access via IAM roles or access keys
- **ECS/EKS:** Container-based applications accessing S3
- **Batch:** Large-scale processing jobs using S3 data

### **Analytics Services**

- **Athena:** Query S3 data using SQL
- **Redshift Spectrum:** Query S3 data from Redshift
- **EMR:** Big data processing with Hadoop/Spark
- **Glue:** ETL service for data preparation
- **QuickSight:** Business intelligence and visualization

### **Database Services**

- **RDS:** Backup storage, data import/export
- **DynamoDB:** Backup storage, data archival
- **DocumentDB:** Backup and restore operations

### **Content Delivery**

- **CloudFront:** Global content distribution network
- **Origin Access Identity:** Secure CloudFront to S3 access
- **Cache Behaviors:** Custom caching rules for different content

## **Compliance and Governance**

### **Compliance Standards**

- **SOC 1, 2, 3:** System and Organization Controls
- **PCI DSS:** Payment Card Industry compliance
- **HIPAA:** Healthcare data protection
- **FedRAMP:** Federal government compliance
- **ISO 27001:** Information security management

### **Data Governance**

- **Object Lock:** WORM (Write Once Read Many) compliance
- **Legal Hold:** Indefinite retention for legal purposes
- **Retention Periods:** Compliance-driven retention policies
- **MFA Delete:** Multi-factor authentication for deletions
- **Bucket Notifications:** Audit trail for data access

### **Object Lock**

- **Compliance Mode:** Objects cannot be deleted or modified by anyone
- **Governance Mode:** Users with special permissions can modify settings
- **Retention Period:** Specified time period for protection
- **Legal Hold:** Indefinite protection regardless of retention period

## **Troubleshooting**

### **Common Access Issues**

- **403 Forbidden:** Check bucket policy, IAM permissions, ACLs
- **404 Not Found:** Verify bucket/object exists, correct region
- **Access Denied:** Review IAM policies and bucket policies
- **Block Public Access:** May override bucket policies

### **Performance Issues**

- **Slow Uploads:** Use multipart upload, Transfer Acceleration
- **High Latency:** Consider CloudFront, optimize request patterns
- **Throttling:** Distribute requests across prefixes
- **Mixed Workloads:** Separate frequent and infrequent access patterns

### **Replication Issues**

- **Objects Not Replicating:** Check IAM role, versioning, filters
- **Replication Lag:** Monitor CloudWatch metrics
- **Failed Replication:** Review CloudWatch events and logs
- **Encryption Conflicts:** Ensure KMS key permissions

### **Website Hosting Issues**

- **403 Error:** Check public read permissions, index document
- **404 Error:** Verify index document exists and is named correctly
- **HTTPS Issues:** Use CloudFront for SSL/TLS termination
- **Custom Domain:** Verify DNS configuration

## **Best Practices**

### **Security Best Practices**

- **Principle of Least Privilege:** Grant minimum required permissions
- **Enable Versioning:** Protect against accidental deletion/modification
- **Enable Logging:** Monitor access and API calls
- **Use IAM Roles:** Avoid hardcoded credentials
- **Block Public Access:** Enable unless specifically needed
- **Encrypt Sensitive Data:** Use appropriate encryption method
- **Regular Audits:** Review permissions and access patterns

### **Performance Best Practices**

- **Request Distribution:** Use random prefixes for high request rates
- **Multipart Upload:** For objects larger than 100 MB
- **CloudFront Integration:** Cache frequently accessed content
- **Transfer Acceleration:** For global user base
- **S3 Select:** Query specific data instead of entire objects
- **Lifecycle Policies:** Automate storage class transitions

### **Cost Optimization Best Practices**

- **Storage Class Analysis:** Use S3 Analytics to understand access patterns
- **Lifecycle Policies:** Implement automated transitions and deletions
- **Intelligent-Tiering:** For unpredictable access patterns
- **Delete Unnecessary Data:** Regular cleanup of old/unused objects
- **Monitor Costs:** Use Cost Explorer and budgets
- **Incomplete Upload Cleanup:** Delete failed multipart uploads

### **Operational Best Practices**

- **Naming Conventions:** Consistent bucket and object naming
- **Tagging Strategy:** Comprehensive tagging for cost allocation and management
- **Backup Strategy:** Cross-region replication for critical data
- **Monitoring:** Set up CloudWatch alarms for key metrics
- **Documentation:** Maintain documentation of bucket purposes and policies
- **Automation:** Use Infrastructure as Code (CloudFormation/Terraform)

## **Advanced Features**

### **S3 Object Lambda**

- **Data Transformation:** Transform data as it's retrieved
- **Use Cases:** Data masking, format conversion, image resizing
- **Lambda Functions:** Custom processing logic
- **Access Points:** Control access to transformed data

### **S3 Multi-Region Access Points**

- **Global Endpoints:** Single endpoint for multi-region buckets
- **Request Routing:** Automatic routing to optimal region
- **Failover:** Automatic failover between regions
- **Replication:** Works with Cross-Region Replication

### **S3 Access Points**

- **Policy Management:** Simplify access control for shared buckets
- **Network Controls:** VPC-only access points
- **Naming:** Unique names within account and region
- **Use Cases:** Large shared datasets, application-specific access

### **S3 Control Tower Integration**

- **Guardrails:** Automatic policy enforcement
- **Compliance:** Organization-wide compliance monitoring
- **Account Management:** Consistent S3 configuration across accounts

## **Miscellaneous Tips**

- **Bucket Naming:** Must be globally unique, DNS-compliant
- **Object Key Length:** Maximum 1,024 UTF-8 characters
- **Object Size:** Single object up to 5 TB
- **Bucket Limit:** 100 buckets per account by default (can be increased)
- **Request Rate:** Automatically scales, no pre-warming needed
- **Consistency:** Strong read-after-write consistency for all operations
- **Metadata:** Custom metadata with x-amz-meta- prefix
- **Tags:** Up to 10 key-value pairs per object
- **CORS Configuration:** Required for cross-domain web requests
- **Requester Pays:** Bucket owner can configure requesters to pay transfer costs
- **Event Notifications:** Can trigger Lambda, SNS, SQS
- **Server Access Logs:** Detailed request logs for auditing
- **Object Lock:** WORM compliance for regulatory requirements