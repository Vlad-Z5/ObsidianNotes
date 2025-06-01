Managed **NFS (Network File System)**

- **Use Case:** Shared file system for Linux-based workloads
- **Access:** Mountable by **multiple EC2 instances** across AZs
- **Scalability:** Auto-scales storage and throughput
- **Performance Modes:**
	- **General Purpose:** Low latency, default
	- **Max I/O:** Higher throughput, higher latency
- **Storage Classes:**
	- **Standard** (frequent access)
	- **IA (Infrequent Access)** for cost savings
- **Backup & Encryption:** Supports automatic backups, encryption at rest and in transit
