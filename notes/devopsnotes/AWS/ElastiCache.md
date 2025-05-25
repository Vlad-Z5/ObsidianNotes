Fully managed in-memory data store and cache service

- **Engine Options:**
	- **Redis:** In-memory key-value store with persistence, replication, Pub/Sub, Lua scripting, etc.
	- **Memcached:** Simple, high-performance, multi-threaded memory object caching system

- **Key Features:**
	- Microsecond latency and high throughput
	- Supports Multi-AZ with automatic failover (Redis only)
	- Backup and restore capabilities (Redis)
	- Data partitioning (sharding) and replication
	- Secure with VPC, IAM, encryption at rest and in transit
	- Integrated with CloudWatch for monitoring

- **Use Cases:**
	- Caching frequently accessed data (e.g., DB queries, session state)
	- Reduces DB load
	- Real-time analytics
	- Leaderboards, pub/sub systems, and rate limiting
