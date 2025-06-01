High-performance, fully managed relational database compatible with MySQL (3306 port) and PostgreSQL (5432 port)

### **Key Features**

- Up to **5x faster** than standard MySQL, **3x faster** than PostgreSQL
- Storage auto-scales in increments of **10 GB** up to **128 TB**
- Fault-tolerant with distributed, self-healing storage across multiple Availability Zones
- Supports **Global Database** for cross-region replication and disaster recovery (1 primary region, rest read-only)
- Automated backups, snapshots, and point-in-time recovery
- Multi-AZ deployments with automated failover
- Read replicas for horizontal scaling (up to **15 replicas**)
- Supports **serverless mode** (Aurora Serverless) for on-demand, auto-scaling compute capacity
- Encryption at rest and in transit
- **Aurora DB Cloning** is faster than snapshot and restore

### **Aurora Architecture**

- **Cluster Volume:** Shared storage layer across 6 copies in 3 AZs
- **Writer Instance:** Single primary instance for writes
- **Reader Instances:** Up to 15 read-only instances
- **Custom Endpoints:** Route connections to specific instance groups
- **Aurora Replica Auto Scaling:** Automatically add/remove replicas based on metrics

### **Aurora Serverless**

- **v1:** Scales between 0.5-256 ACUs (Aurora Capacity Units), pauses when inactive
- **v2:** Instant scaling, scales to 0, supports more features than v1
- **Use Cases:** Infrequent, intermittent, or unpredictable workloads

### **Aurora Global Database**

- **Primary Region:** Single writer cluster
- **Secondary Regions:** Up to 5 read-only regions
- **Replication Lag:** Typically under 1 second
- **Recovery Time:** Less than 1 minute for region-wide outages
- **Cross-Region Read Replicas:** Up to 16 per secondary region

### **Aurora Multi-Master**

- **Multiple Writers:** All instances can accept writes
- **Conflict Detection:** Built-in conflict resolution
- **Use Cases:** Applications requiring continuous write availability

### **Use Cases**

- Applications requiring high throughput and availability
- Enterprise-grade workloads needing MySQL or PostgreSQL compatibility with enhanced performance
- Global applications needing cross-region replication