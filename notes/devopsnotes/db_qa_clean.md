1. Q: How do you handle database deadlocks?
A: Identify using pg_locks or SHOW ENGINE INNODB STATUS; resolve by killing one transaction or redesigning queries to acquire locks in consistent order; use retry logic in app.

2. Q: What is a materialized view and when would you use it?
A: Precomputed query results stored like a table; used to speed up complex queries; refresh periodically or on demand.

3. Q: How do you detect and remove unused indexes?
A: Monitor usage (pg_stat_user_indexes, pg_stat_statements), drop indexes with no read hits to improve write performance.

4. Q: Difference between soft delete and hard delete?
A: Soft delete: mark as deleted (is_deleted=true); preserves history. Hard delete: physically removes rows; frees space but irreversible.

5. Q: How do you design a multi-tenant database?
A: Approaches: separate database per tenant, shared database with separate schema, or shared schema with tenant_id column; balance isolation vs cost.

6. Q: How do you implement auditing in a DB?
A: Enable triggers or built-in audit logs (pgAudit, MySQL audit plugin), store user, timestamp, operation, before/after values.

7. Q: How do you prevent N+1 query problems?
A: Use joins or IN clauses, batch queries, or ORM eager loading to avoid multiple sequential queries.

8. Q: What is database connection storm and how to mitigate?
A: Sudden surge of connections causing overload; mitigate with connection pooling, throttling, and queueing.

9. Q: How do you migrate a large table without downtime?
A: Use shadow table with background sync, incremental data copy, dual-write strategy, then swap tables or rename.

10. Q: How do you handle schema version drift across environments?
A: Use migration scripts with versioning, CI/CD enforcement, checksum validation, and drift detection tools.

11. Q: Difference between synchronous and asynchronous replication?
A: Synchronous: primary waits for replica acknowledgment (strong consistency, slower writes). Asynchronous: primary does not wait (faster writes, eventual consistency).

12. Q: How do you monitor replication health in MySQL/PostgreSQL?
A: Check replication lag (SHOW SLAVE STATUS, pg_stat_replication), replication errors, and delayed transactions.

13. Q: What is optimistic vs pessimistic locking?
A: Optimistic: assume low conflicts, check version on commit. Pessimistic: lock row/table during transaction to prevent conflicts.

14. Q: How do you detect and prevent database bloating?
A: Monitor table and index size, vacuum/analyze (PostgreSQL), optimize/defragment tables, archive old data.

15. Q: How do you store time-series data efficiently?
A: Use partitioning (range by date), compression, specialized TSDBs (InfluxDB, TimescaleDB), and retention policies.

16. Q: How do you secure sensitive columns in a DB?
A: Column-level encryption, masking, role-based access, TLS for transit, KMS-managed keys.

17. Q: What strategies exist for handling hot partitions in DynamoDB?
A: Use high-cardinality partition keys, add randomness/sharding suffix, use adaptive capacity, or TTL for old data.

18. Q: How do you implement database failover testing?
A: Simulate primary failure in staging, monitor replica promotion, validate application handles failover gracefully.

19. Q: How do you scale search-heavy workloads in a relational DB?
A: Use full-text indexes, materialized views, caching, or offload to dedicated search engine (Elasticsearch, OpenSearch).

20. Q: How do you ensure transactional consistency across microservices?
A: Use distributed transactions (XA), or prefer eventual consistency with saga patterns and compensating actions.

## 1. Database Operations & Reliability

1. Q: How do you perform a point-in-time recovery?
A: Restore full backup, then apply WAL/binlogs up to a specific timestamp.

2. Q: How do you automate failover in RDS?
A: Enable Multi-AZ; RDS automatically promotes standby if primary fails.

3. Q: How do you handle long-running transactions blocking writes?
A: Monitor locks, kill or batch transactions, optimize queries, use appropriate isolation levels.

4. Q: How do you test backups?
A: Restore to staging, validate schema and sample data, run integrity checks.

5. Q: How do you perform zero-downtime DB migrations?
A: Use backward-compatible schema changes, dual writes, feature flags, and rolling deployments.

## 2. Performance & Monitoring

1. Q: How do you identify slow queries in PostgreSQL?
A: Enable pg_stat_statements and slow query logs, analyze with EXPLAIN ANALYZE.

2. Q: How do you optimize write-heavy workloads?
A: Batch inserts, disable autocommit, proper indexing, use SSD storage, partition tables if needed.

3. Q: How do you monitor replica lag in MySQL?
A: SHOW SLAVE STATUS\G → Seconds_Behind_Master; alert if lag exceeds threshold.

4. Q: How do you detect deadlocks?
A: PostgreSQL: pg_locks and deadlock logs; MySQL: SHOW ENGINE INNODB STATUS.

5. Q: How do you monitor DB health in cloud?
A: CloudWatch (AWS), Stackdriver (GCP), Azure Monitor; track CPU, memory, IOPS, connections, replication lag.

## 3. Scaling & Architecture

1. Q: How do you scale a relational DB for millions of users?
A: Use read replicas, partition/shard tables, cache frequently accessed data, connection pooling, vertical scaling as needed.

2. Q: How do you shard a database?
A: Split data by key (user_id, region), route queries via app or proxy; rebalance shards periodically.

3. Q: How do you implement high availability?
A: Multi-AZ deployments, replication, automatic failover, health checks, backups.

4. Q: Difference between vertical and horizontal scaling?
A: Vertical: increase CPU/RAM/IO; Horizontal: add nodes/replicas/shards.

5. Q: How do you handle hot partitions in DynamoDB?
A: High-cardinality keys, randomized suffix, adaptive capacity, or TTL for old items.

## 4. Schema & Data Design

1. Q: How do you design a schema for multi-tenant apps?
A: Options: separate DB per tenant, shared schema per tenant, shared table with tenant_id. Balance isolation vs cost.

2. Q: How do you store user preferences efficiently?
A: JSONB in PostgreSQL, key-value table, or NoSQL store like DynamoDB.

3. Q: How do you design a messaging app schema?
A: Tables: users, conversations, participants, messages; index on conversation_id, timestamp; shard messages by conversation_id for scale.

4. Q: How do you handle time-series data?
A: Partition by date, compress old data, consider TimescaleDB, InfluxDB; retention policies.

5. Q: How do you normalize a database?
A: Apply 1NF–4NF rules to reduce redundancy; denormalize selectively for performance.

6. Q: Difference between clustered and non-clustered index?
A: Clustered: table data stored in index order (one per table). Non-clustered: separate structure pointing to data (multiple allowed).

7. Q: When to create a composite index?
A: When queries filter/order by multiple columns together frequently.

8. Q: How do indexes affect write performance?
A: Each write/update requires index maintenance; more indexes → slower writes.

9. Q: How do you detect unused indexes?
A: PostgreSQL: pg_stat_user_indexes usage stats; drop if unused.

10. Q: What are GIN / GiST indexes used for?
A: Full-text search, arrays, JSONB queries in PostgreSQL.

## 6. Transactions & Consistency

1. Q: ACID vs BASE?
A: ACID: strict consistency and isolation (RDBMS). BASE: eventual consistency, high availability (NoSQL).

2. Q: Isolation levels?
A: Read Uncommitted, Read Committed, Repeatable Read, Serializable.

3. Q: Optimistic vs Pessimistic locking?
A: Optimistic: assume low conflict, validate version on commit. Pessimistic: lock row/table during transaction.

4. Q: How does DynamoDB handle consistency?
A: Default: eventual consistency; optionally strong consistency; writes are atomic per item.

5. Q: How to maintain transactional consistency across microservices?
A: Use saga patterns or distributed transactions; prefer eventual consistency.

## 7. Backups & Disaster Recovery

1. Q: How do you restore from a logical backup?
A: PostgreSQL: psql db < dump.sql or pg_restore -d db dumpfile.dump; MySQL: mysql db < dump.sql.

2. Q: How do you automate backups in the cloud?
A: Enable automated snapshots, configure retention policies, schedule manual snapshots for migrations.

3. Q: How do you test disaster recovery?
A: Restore backups in staging, verify integrity and app connectivity.

4. Q: Difference between hot/warm/cold standby?
A: Hot: immediately available (HA), Warm: slightly delayed, Cold: offline, requires restore/startup.

5. Q: How do you implement cross-region DR?
A: Replicate DB to another region, periodic snapshots, optionally read-replicas with failover testing.

## 8. Security & Secrets

1. Q: How do you secure a database?
A: TLS/SSL, role-based access, encrypted storage, network isolation (VPC), auditing, secrets management.

2. Q: How to rotate DB credentials automatically?
A: Use AWS Secrets Manager rotation, HashiCorp Vault dynamic credentials.

3. Q: Column-level encryption?
A: Encrypt sensitive columns (AES-256), optionally use application-side encryption; manage keys securely.

4. Q: How do you handle tenant isolation in multi-tenant DBs?
A: Row-level security, separate schemas, or separate databases per tenant.

5. Q: How do you audit DB changes?
A: Enable triggers or audit plugins, log user, timestamp, operation, and before/after values.

## 9. Practical Scenarios

1. Q: Replication lag detected on read replica, next steps?
A: Check IOPS, long queries, network, replica errors, load; tune queries or add more replicas if needed.

2. Q: DB server runs out of disk space, what to do?
A: Archive or truncate old data, rotate logs, add storage, clean temp tables, vacuum/analyze (PostgreSQL).

3. Q: Schema migration in production with active traffic?
A: Use non-breaking changes, dual writes, feature flags, background data migration, phased rollout.

4. Q: How to migrate from one DB system to another?
A: Export schema/data, use migration tools (pgloader, AWS DMS), validate queries, dual-write or shadow migration, cutover when verified.

5. Q: How to handle large table updates without locking?
A: Batch updates, partitioned updates, CREATE TABLE AS SELECT or background jobs.

## 1. Database Fundamentals

1. Q: Difference between SQL and NoSQL?
A: SQL: relational, structured schema, ACID, good for complex queries; NoSQL: key-value, document, columnar, or graph, schema-flexible, BASE consistency, high scalability.

2. Q: What is ACID?
A: Atomicity, Consistency, Isolation, Durability; ensures transactional integrity.

3. Q: What is BASE?
A: Basically Available, Soft state, Eventual consistency; prioritizes availability over strict consistency.

4. Q: Explain normalization and its normal forms.
A: Reduces redundancy; 1NF–4NF/BNCF remove duplicates, dependencies, multi-valued attributes.

5. Q: Denormalization – when and why?
A: For read-heavy workloads or reporting to improve performance; trades storage and write complexity for faster reads.

6. Q: Difference between primary key and foreign key?
A: Primary key uniquely identifies rows; foreign key enforces referential integrity between tables.

7. Q: What are indexes and why are they important?
A: Data structures for faster lookups; improve SELECT performance, can slow down writes.

8. Q: Clustered vs non-clustered index?
A: Clustered: table data sorted physically; one per table; non-clustered: separate structure pointing to data; multiple allowed.

9. Q: Composite index?
A: Index on multiple columns for queries filtering or ordering by those columns.

10. Q: Unique index vs primary key?
A: Both enforce uniqueness; primary key also identifies row; unique index can allow NULLs depending on DB.

## 2. Transactions & Isolation

1. Q: What are transactions?
A: Group of operations executed atomically; either all succeed or none.

2. Q: Isolation levels?
A: Read Uncommitted, Read Committed, Repeatable Read, Serializable; control visibility of uncommitted data.

3. Q: Dirty read, non-repeatable read, phantom read?
A: Dirty: read uncommitted data; Non-repeatable: data changes between reads; Phantom: new rows appear in repeated query.

4. Q: Optimistic vs Pessimistic locking?
A: Optimistic: check version at commit; Pessimistic: lock rows during transaction to prevent conflicts.

5. Q: Savepoints and nested transactions?
A: Savepoints allow partial rollback inside a transaction; nested transactions can commit/rollback independently in some DBs.

## 3. Backups & Recovery

1. Q: Logical vs physical backups?
A: Logical: SQL dump; portable, slower; Physical: raw files, faster, OS-level restore.

2. Q: Point-in-Time Recovery?
A: Restore DB to a specific timestamp using WAL/binlogs and base backup.

3. Q: Hot vs warm vs cold standby?
A: Hot: immediately available; Warm: slight delay; Cold: offline, requires start/restore.

4. Q: How to test backups?
A: Restore in staging, validate schema and data, run application tests.

5. Q: Disaster Recovery strategies?
A: Multi-region replication, snapshots, read replicas, periodic drills, PITR.

6. Q: Vertical vs horizontal scaling?
A: Vertical: more CPU/RAM/IO; Horizontal: add nodes, replicas, or shard data.

7. Q: Read replicas?
A: Offload read traffic; asynchronous replication; improves scalability.

8. Q: Failover replica?
A: Standby for HA; promoted if primary fails; synchronous or near-sync replication.

9. Q: Partitioning vs sharding?
A: Partitioning: split table internally by range/list/hash; Sharding: split DB across servers.

10. Q: Connection pooling?
A: Reuse connections to reduce overhead; PgBouncer, ProxySQL, HikariCP.

11. Q: Caching strategies?
A: Redis/Memcached for hot data; write-through/write-back cache; invalidate on updates.

12. Q: Handling hot partitions?
A: Randomize partition key, increase cardinality, use adaptive capacity (DynamoDB), or TTL for old items.

## 5. Schema & Data Design

1. Q: Multi-tenant schema strategies?
A: Separate DB per tenant, separate schema per tenant, shared schema with tenant_id; trade isolation vs cost.

2. Q: Messaging app schema?
A: Tables: users, conversations, participants, messages; index conversation_id, timestamp; shard messages by conversation_id.

3. Q: Time-series data design?
A: Partition by date, compress old data, retention policies, consider TimescaleDB or InfluxDB.

4. Q: User preferences storage?
A: JSONB column (PostgreSQL), key-value table, or NoSQL store like DynamoDB.

5. Q: Audit logging schema?
A: Track user, timestamp, operation, before/after values; use triggers or plugins.

6. Q: Difference between key-value, document, columnar, and graph DB?
7. Q: How does DynamoDB handle consistency?
A: Default eventual consistency; optional strong consistency; atomic per-item writes; conditional updates prevent overwrite.

8. Q: DynamoDB capacity modes?
A: On-demand: auto-scaling, pay-per-request; Provisioned: define RCUs/WCUs; use adaptive capacity for hot keys.

9. Q: Global and local secondary indexes?
A: Local: same partition key, different sort key; Global: different partition/sort keys; both speed queries but consume RCU/WCU.

10. Q: TTL in DynamoDB?
A: Time-to-live deletes items automatically; reduces storage; background cleanup, eventual deletion.

11. Q: How to handle hot partitions?
A: Add randomness to partition keys, increase cardinality, avoid “all writes to same key”; use adaptive capacity.

12. Q: MongoDB replica sets?
A: Primary handles writes, secondaries replicate asynchronously; automatic failover; optional hidden/read-only nodes for backups.

13. Q: Sharding in MongoDB?
A: Split collection across shards by shard key; balances load; requires careful key selection to avoid hot shards.

14. Q: Consistency in MongoDB?
A: Strong reads from primary by default; secondary reads can be eventual consistent.

15. Q: When to choose NoSQL vs RDBMS?
A: NoSQL: high-scale, schema-flexible, fast writes; RDBMS: strong consistency, complex joins, transactional integrity.

16. Q: Managed DB vs self-hosted?
A: Managed: provisioning, backups, patching, monitoring automated; self-hosted: full control, manual management.

17. Q: How to perform zero-downtime deployment on managed DB?
A: Blue-green deployments, dual-write, backward-compatible schema, feature flags, phased rollout.

18. Q: Multi-AZ vs multi-region deployments?
A: Multi-AZ: HA within region; automatic failover. Multi-region: DR and low-latency reads globally.

19. Q: RDS, Aurora, Cloud SQL differences?
A: RDS: managed, single/multi-AZ, snapshots. Aurora: MySQL/Postgres compatible, auto-scaling, high throughput. Cloud SQL: fully managed GCP service, automated backups and replication.

20. Q: Automating backups in cloud?
A: Enable automated snapshots, schedule manual snapshots before migrations, configure retention policies, test restores regularly.

21. Q: Secrets management integration?
A: Vault dynamic credentials, AWS Secrets Manager rotation, application fetches secrets via IAM/Vault agent; avoid hardcoding credentials.

22. Q: Monitoring cloud DBs?
A: Metrics: CPU, memory, connections, query latency, replication lag; tools: CloudWatch, Stackdriver, Prometheus exporters, Datadog, NewRelic.

23. Q: Scaling cloud DBs?
A: Vertical: increase instance class; Horizontal: add read replicas, partition/shard, serverless options (Aurora Serverless, DynamoDB on-demand).

24. Q: How to handle schema changes in production?
A: Backward-compatible changes first (add columns), dual-write, phased app deployment, remove old schema later.

25. Q: Point-in-time recovery in cloud?
A: Restore from snapshot + apply logs up to a specific timestamp; ensures minimal data loss.

## 8. Replication & Failover

1. Q: Synchronous vs asynchronous replication?
A: Synchronous: primary waits for replica acknowledgment (strong consistency, slower writes); asynchronous: primary doesn’t wait (eventual consistency, faster writes).

2. Q: Read replica vs failover replica?
A: Read replica: read-only, offloads queries; Failover replica: standby for HA, promoted on primary failure.

3. Q: Detecting replication lag?
A: Check lag metrics (pg_stat_replication, SHOW SLAVE STATUS), monitor IOPS, long queries, network latency.

4. Q: How to handle replication failures?
A: Identify error, skip/break replication, re-sync missing WAL/binlogs, promote standby if needed.

5. Q: Cross-region replication strategies?
A: Asynchronous global replicas, periodic snapshots, geo-partitioned data, eventual consistency across regions.

## 9. Security & Compliance

1. Q: How do you secure DB connections?
A: TLS/SSL, network isolation (VPC, subnet), firewall rules, IAM authentication.

2. Q: How to rotate credentials safely?
A: Use Secrets Manager or Vault dynamic secrets with rotation policies; apps fetch updated credentials automatically.

3. Q: Column-level encryption?
A: Encrypt sensitive columns; keys managed via KMS or Vault; application decrypts on read.

4. Q: Role-based access control?
A: Use least privilege, create roles/groups, assign permissions, avoid using root/admin users in apps.

5. Q: Auditing database activity?
A: Enable audit plugins (pgAudit, MySQL Audit), log DML operations, user, timestamp, before/after data.

6. Q: Replication lag detected; next steps?
A: Check replica health, long-running queries, disk/IO, network; tune queries or add replicas.

7. Q: DB server disk full; what to do?
A: Archive/truncate old data, rotate logs, increase storage, clean temp tables, vacuum/analyze.

8. Q: Schema migration with active traffic?
A: Use non-breaking changes, dual writes, feature flags, background migration, phased cutover.

9. Q: Migrating DB system?
A: Export schema/data, migration tools (pgloader, AWS DMS), dual-write/shadow migration, validate app queries, switch traffic when verified.

10. Q: Large table updates without locking?
A: Batch updates, partitioned updates, background jobs, CREATE TABLE AS SELECT then swap.

11. Q: How to handle N+1 query problems?
A: Use joins, IN clauses, batch queries, ORM eager loading.

12. Q: How to test failover?
A: Simulate primary failure in staging, monitor replica promotion, verify app resilience.

13. Q: How to scale read-heavy workloads?
A: Read replicas, caching, materialized views, query optimization, offload reporting to BI DB.

14. Q: How to detect unused indexes?
A: Monitor usage (pg_stat_user_indexes, query stats); drop if not used to improve write performance.

15. Q: How to manage schema drift?
A: Use migration scripts versioned in VCS, CI/CD enforcement, checksum validation, periodic audits.

## 11. Advanced Performance Tuning

1. Q: How to debug slow queries?
A: Use EXPLAIN/EXPLAIN ANALYZE (PostgreSQL), EXPLAIN (MySQL), monitor execution plans, check indexes, avoid sequential scans, optimize joins.

2. Q: How to improve write-heavy workloads?
A: Batch inserts/updates, disable autocommit, use proper indexing, partition large tables, optimize transactions.

3. Q: How to monitor query performance over time?
A: PostgreSQL: pg_stat_statements; MySQL: performance_schema; cloud metrics dashboards; log slow queries.

4. Q: What is table bloat and how to fix it?
A: Accumulated dead tuples in PostgreSQL; fix with VACUUM, ANALYZE, or pg_repack.

5. Q: How do you optimize indexes?
A: Remove unused indexes, create composite or partial indexes, consider covering indexes, monitor index usage stats.

6. Q: How do you handle locking and contention?
A: Monitor lock tables (pg_locks), optimize transactions, avoid long-running writes, consider row-level locking.

7. Q: How to profile DB performance?
A: Use EXPLAIN ANALYZE, slow query logs, pg_stat_statements, cloud metrics (CPU, memory, IOPS), query profiler tools (Datadog, NewRelic).

8. Q: How to tune connection pools?
A: Match pool size to max DB connections, use short-lived connections for burst traffic, avoid connection leaks.

9. Q: How to reduce replication lag?
A: Optimize writes on primary, increase replica IO capacity, adjust WAL settings, add read replicas, monitor network latency.

10. Q: How to handle N+1 query problems?
A: Batch queries, use joins, eager-loading in ORM, prefetch related data.

11. Q: How to integrate DB migrations into CI/CD?
A: Versioned migration scripts (Flyway, Liquibase, Alembic), run in pipeline pre-production, automated rollback scripts, test on staging.

12. Q: How to ensure schema consistency across environments?
A: Run migration checks, checksum validation, enforce migration order, versioned scripts stored in VCS.

13. Q: How to implement zero-downtime migrations?
A: Backward-compatible changes first, dual writes, feature flags, phased rollout, shadow tables for heavy changes.

14. Q: How to manage multi-environment pipelines?
A: Separate staging/production configs, automated promotion of migration scripts, pre/post-deploy validation tests.

15. Q: How to roll back a migration?
A: Use undo scripts, restore snapshots if destructive changes occurred, or leverage blue-green deployment.

16. Q: How to handle concurrent migrations?
A: Serialize migrations in pipeline, use advisory locks (Postgres), or a migration table to track applied versions.

17. Q: How to validate migration success?
A: Row counts, integrity checks, test queries, application feature verification.

18. Q: How to run migrations in a cloud-managed DB?
A: Use CI/CD pipelines with credentials from Secrets Manager/Vault; avoid downtime using non-blocking changes.

19. Q: How to backfill data safely during migration?
A: Incremental batch processing, dual writes, monitor performance, avoid locking production tables.

20. Q: How to handle environment drift?
A: Track schema versions, compare staging vs prod, enforce migration order, alert on drift.

21. Q: What is IaC for databases?
A: Define DB schema, configuration, users, backups, and monitoring as code; automates provisioning and reduces human error.

22. Q: Examples of IaC tools for DBs?
A: Terraform, CloudFormation, Crossplane, Pulumi, Kubernetes CRDs (PostgresOperator, MySQLOperator).

23. Q: How to provision RDS via Terraform?
A: Define aws_db_instance, configure engine, storage, backups, multi-AZ, monitoring, security groups.

24. Q: How to manage DB secrets in IaC?
A: Use Vault or Secrets Manager references, dynamic secrets, avoid hardcoding passwords.

25. Q: How to automate backup policies via IaC?
A: Terraform or CloudFormation can configure snapshot retention, automated backups, multi-AZ replication.

26. Q: How to enforce DB security via IaC?
A: Apply parameter groups, enforce TLS, define IAM roles, network isolation, encryption at rest.

27. Q: How to deploy DB migrations via IaC?
A: Combine migration scripts with IaC pipelines; apply migration as part of provisioning or post-deploy step.

28. Q: How to test IaC DB changes safely?
A: Apply to staging DB clones, validate schema/data, use rollback scripts.

29. Q: How to handle environment-specific DB parameters?
A: Use variables or parameter files per environment in Terraform, CloudFormation, or Kubernetes.

30. Q: How to monitor IaC-managed DBs?
A: Integrate CloudWatch/Prometheus metrics during provisioning, alerting pipelines, resource usage dashboards.

## 14. Chaos Testing & Reliability Drills

1. Q: How to simulate DB failures?
A: Stop primary DB, simulate disk full, network partition, replica lag; test app recovery and failover.

2. Q: How to test failover of read replicas?
A: Promote replica in staging, redirect traffic, validate consistency and app behavior.

3. Q: How to validate backups?
A: Restore snapshot in isolated environment, run sample queries, check integrity.

4. Q: How to measure RTO/RPO?
A: RTO: time to recover; RPO: max data loss tolerated; test with failover drills.

5. Q: How to handle transactional retries during failure?
A: Idempotent writes, retry logic with backoff, avoid double-processing.

## 15. Caching Strategies

1. Q: When to use caching?
A: Frequently-read or heavy queries, read-heavy workloads, to reduce DB load and latency.

2. Q: Cache invalidation strategies?
A: Time-based TTL, write-through (update cache on write), write-back, event-driven invalidation.

3. Q: How to combine caching with DB scaling?
A: Cache hot keys in Redis/Memcached, use cache-aside pattern, reduce read replica pressure.

4. Q: How to handle cache consistency?
A: Use TTL, pub/sub for invalidation, cache versioning, or distributed locks for writes.

5. Q: How to monitor cache performance?
A: Hit/miss ratio, eviction counts, memory usage, latency metrics.

16. Multi-Region Scaling

6. Q: How to replicate DB across regions?
A: Asynchronous replication, global tables (DynamoDB), cross-region read replicas (RDS/Aurora).

7. Q: How to handle cross-region latency?
A: Read local replicas, geo-partition data, minimize cross-region writes.

8. Q: How to manage global consistency?
A: Use eventual consistency for non-critical data; synchronous replication for critical data if supported.

9. Q: How to do disaster recovery across regions?
A: Multi-region snapshots, cold standby, automated failover, DR runbooks.

10. Q: How to test global failover?
A: Simulate primary region failure in staging, validate replica promotion, application routing.

17. Real-World Operational Scenarios

11. Q: How do you handle a corrupted database?
A: Restore latest backup, apply binlogs/WALs to minimize data loss, validate schema and app functionality.

12. Q: How do you resolve replication conflicts?
A: Analyze conflicting transactions, use last-write-wins or conflict resolution logic, re-sync replicas.

13. Q: How to handle primary DB crash under load?
A: Promote failover replica, redirect traffic, restore primary from snapshot if needed, analyze root cause.

14. Q: How to recover from accidental data deletion?
A: Restore from point-in-time snapshot, validate affected rows, communicate with stakeholders before cutover.

15. Q: How to handle runaway queries consuming all resources?
A: Identify with pg_stat_activity or slow query logs, terminate offending queries, consider resource limits.

16. Q: How to troubleshoot replication lag spikes?
A: Check IOPS, long-running writes, network latency, large transactions; consider additional read replicas.

17. Q: How to handle disk full error in production?
A: Archive/truncate old data, rotate logs, increase storage dynamically if cloud-managed, monitor space trends.

18. Q: How to scale DB under sudden traffic spike?
A: Add read replicas, scale instance vertically, enable serverless/autoscaling options, increase cache layer.

19. Q: How to handle schema changes on large tables?
A: Backfill data in batches, use shadow tables, dual writes, phased migration, CREATE INDEX CONCURRENTLY in Postgres.

20. Q: How to debug deadlocks in production?
A: Capture lock graphs, identify conflicting queries, re-order queries, implement retry logic.

## 18. Security Edge Cases

1. Q: How to prevent SQL injection?
A: Use parameterized queries, ORM query builders, input validation, avoid string concatenation for queries.

2. Q: How to audit access to sensitive data?
A: Enable audit logging, track user, timestamp, operation; integrate with SIEM systems.

3. Q: How to enforce row-level security?
A: Postgres: CREATE POLICY; apply filter per role/tenant; NoSQL: application-level filtering.

4. Q: How to rotate encryption keys safely?
A: Use KMS or Vault; re-encrypt data in background; maintain key versioning for old data access.

5. Q: How to detect suspicious DB activity?
A: Monitor abnormal query patterns, failed login attempts, sudden high resource usage, integrate with alerts.

6. Q: How to secure DB in multi-cloud environment?
A: Enforce TLS, IAM policies, VPC peering, private endpoints, key management, audit trails.

7. Q: How to protect against privilege escalation?
A: Least-privilege roles, monitor grants, periodic access reviews, avoid shared admin accounts.

8. Q: How to encrypt data at rest and in transit?
A: At rest: TDE, KMS-managed keys; In transit: TLS/SSL for connections; optionally encrypt sensitive columns.

9. Q: How to safely expose read-only replicas to public APIs?
A: Use API layer or proxy, limit queries, enforce authentication/authorization, throttle requests.

10. Q: How to prevent accidental mass deletion?
A: Use WHERE clauses, soft deletes, triggers for auditing, backup snapshots before destructive operations.

19. Cloud-Specific Operations

11. Q: How to monitor RDS/Aurora?
A: CloudWatch metrics: CPU, memory, connections, IOPS, replication lag; enable enhanced monitoring.

12. Q: How to restore from Cloud SQL backup?
A: Use automated backups or manual snapshot; optionally PITR; restore to staging first for validation.

13. Q: How to migrate from on-prem to cloud DB?
A: Use DMS/AWS SCT, ensure schema compatibility, dual writes during cutover, validate data integrity.

14. Q: How to implement cross-region failover in cloud?
A: Enable global replication, promote standby, update DNS/app routing, monitor replication lag.

15. Q: How to reduce cloud DB cost?
A: Rightsize instances, use serverless/autoscaling, archive old data, optimize queries to reduce IOPS.

16. Q: How to perform blue-green deployment for DB?
A: Clone DB, apply schema changes, dual-write during validation, switch traffic to new DB.

17. Q: How to enable auditing in managed DB?
A: Enable RDS/Aurora logging, export to CloudWatch/Stackdriver, set retention and alerting.

18. Q: How to handle multi-tenant cloud DB?
A: Separate schema/DB per tenant, row-level security, monitor usage per tenant, enforce quota limits.

19. Q: How to automate backups in multi-region DB?
A: Cloud snapshots, cross-region replication, PITR enabled, automated testing of restores.

20. Q: How to debug slow queries in Aurora Serverless?
A: Use Performance Insights, slow query logs, EXPLAIN plans, monitor scaling events.

## 20. Mega Practical Scenario Drills

1. Q: App reports inconsistent data on read replicas. Next steps?
A: Check replication lag, ensure eventual consistency, confirm read routing, analyze write patterns.

2. Q: Unexpected failover triggers in production. What to do?
A: Validate replica promotion, check application connectivity, investigate root cause (network/CPU/disk), ensure monitoring/alerts functional.

3. Q: Replica disk usage grows too fast.
A: Archive old logs, enable compression, monitor table bloat, consider vertical scaling.

4. Q: Latency spikes in multi-region DB queries.
A: Check network, shard data by region, replicate read-only data locally, use caching.

5. Q: Migration script failed mid-deployment.
A: Rollback via undo script or restore snapshot, re-run migration on staging first, verify sequencing.

6. Q: Multiple read replicas lagging simultaneously.
A: Check primary write spikes, network throughput, WAL/log shipping, consider adding replicas or scaling primary.

7. Q: Database under DoS from app misbehavior.
A: Implement query throttling, connection limits, caching, and rate-limiting at API layer.

8. Q: Query performance degrades after schema changes.
A: Analyze indexes, vacuum/analyze, update statistics, check query plans, possibly rewrite queries.

9. Q: Large batch job causing lock contention.
A: Run in off-peak, use smaller batches, consider partitioned updates, use row-level locking.

10. Q: Unexpected version drift between staging and prod.
A: Compare schema via migration version table, validate applied migrations, re-sync staging DB, enforce pipeline controls.

21. NoSQL Databases

11. Q: Difference between key-value, document, columnar, and graph DB?
A: Key-value: simple mapping (Redis, DynamoDB), fast lookups; Document: JSON-like flexible docs (MongoDB), semi-structured queries; Columnar: optimized for analytics (Cassandra, Bigtable), wide rows; Graph: relationships first (Neo4j), queries on connections.

12. Q: How does DynamoDB handle consistency?
A: Default eventual consistency; optional strong consistency; atomic per-item writes; conditional updates prevent overwrite.

13. Q: DynamoDB capacity modes?
A: On-demand: auto-scaling, pay-per-request; Provisioned: define RCUs/WCUs; adaptive capacity handles hot keys.

14. Q: Global and local secondary indexes?
A: Local: same partition key, different sort key; Global: different partition/sort keys; both speed queries but consume RCU/WCU.

15. Q: TTL in DynamoDB?
A: Time-to-live deletes items automatically; reduces storage; deletion is eventual.

16. Q: How to handle hot partitions?
A: Add randomness to partition keys, increase cardinality, avoid “all writes to same key”, use adaptive capacity.

17. Q: MongoDB replica sets?
A: Primary handles writes, secondaries replicate asynchronously; automatic failover; hidden/read-only nodes for backups.

18. Q: Sharding in MongoDB?
A: Split collection across shards by shard key; balances load; careful key selection avoids hot shards.

19. Q: Consistency in MongoDB?
A: Strong reads from primary by default; secondary reads may be eventual consistent.

20. Q: When to choose NoSQL vs RDBMS?
A: NoSQL: high-scale, schema-flexible, fast writes; RDBMS: strong consistency, complex joins, transactional integrity.

22. Cloud-Managed Databases

21. Q: Managed DB vs self-hosted?
A: Managed: provisioning, backups, patching, monitoring automated; Self-hosted: full control, manual management.

22. Q: How to perform zero-downtime deployment on managed DB?
A: Blue-green deployments, dual-write, backward-compatible schema, feature flags, phased rollout.

23. Q: Multi-AZ vs multi-region deployments?
A: Multi-AZ: HA within region; automatic failover. Multi-region: DR and low-latency reads globally.

24. Q: RDS, Aurora, Cloud SQL differences?
A: RDS: managed, single/multi-AZ, snapshots; Aurora: MySQL/Postgres compatible, auto-scaling, high throughput; Cloud SQL: fully managed GCP service, automated backups and replication.

25. Q: Automating backups in cloud?
A: Enable automated snapshots, schedule manual snapshots before migrations, configure retention policies, test restores.

26. Q: Secrets management integration?
A: Vault dynamic credentials, AWS Secrets Manager rotation, application fetches secrets via IAM/Vault agent; avoid hardcoding credentials.

27. Q: Monitoring cloud DBs?
A: Metrics: CPU, memory, connections, query latency, replication lag; tools: CloudWatch, Stackdriver, Prometheus exporters, Datadog, NewRelic.

28. Q: Scaling cloud DBs?
A: Vertical: increase instance class; Horizontal: add read replicas, partition/shard, serverless options (Aurora Serverless, DynamoDB on-demand).

29. Q: How to handle schema changes in production?
A: Backward-compatible changes first (add columns), dual-write, phased app deployment, remove old schema later.

30. Q: Point-in-time recovery in cloud?
A: Restore from snapshot + apply logs up to a specific timestamp; ensures minimal data loss.

## 23. Replication & Failover

1. Q: Synchronous vs asynchronous replication?
A: Synchronous: primary waits for replica acknowledgment (strong consistency, slower writes); asynchronous: primary doesn’t wait (eventual consistency, faster writes).

2. Q: Read replica vs failover replica?
A: Read replica: read-only, offloads queries; Failover replica: standby for HA, promoted on primary failure.

3. Q: Detecting replication lag?
A: Check lag metrics (pg_stat_replication, SHOW SLAVE STATUS), monitor IOPS, long queries, network latency.

4. Q: How to handle replication failures?
A: Identify error, skip/break replication, re-sync missing WAL/binlogs, promote standby if needed.

5. Q: Cross-region replication strategies?
A: Asynchronous global replicas, periodic snapshots, geo-partitioned data, eventual consistency across regions.

## 24. Cloud DB Monitoring & Debugging

1. Q: How to monitor slow queries?
A: Enable slow query logs, analyze with EXPLAIN, check index usage, query plan, and performance insights dashboards.

2. Q: How to debug replication lag?
A: Monitor replica IOPS, network, long-running transactions, large batch inserts, adjust WAL/log shipping frequency.

3. Q: How to detect unused indexes?
A: Use DB stats tables (pg_stat_user_indexes), query plan analysis; drop unused indexes to improve write performance.

4. Q: How to monitor connection saturation?
A: Track active connections, pool stats, cloud metrics, alert when near max connections.

5. Q: How to alert on DB health issues?
A: Use monitoring tools (CloudWatch, Prometheus, Datadog), set thresholds for CPU, memory, IOPS, replication lag, error rates.


## 25. Security & Compliance

1. Q: How do you secure DB connections?
A: Use TLS/SSL, network isolation (VPC, subnet), firewall rules, IAM authentication, VPN/private endpoints.

2. Q: How to rotate credentials safely?
A: Use Vault or AWS Secrets Manager dynamic secrets with rotation policies; apps fetch updated credentials automatically.

3. Q: Column-level encryption?
A: Encrypt sensitive columns; keys managed via KMS or Vault; application decrypts on read.

4. Q: Role-based access control (RBAC)?
A: Use least privilege, define roles/groups, assign permissions, avoid using root/admin accounts in apps.

5. Q: Auditing database activity?
A: Enable audit plugins (pgAudit, MySQL Audit), log DML operations, user, timestamp, before/after data, integrate with SIEM.

6. Q: Row-level security?
A: Enforce per-row access policies, e.g., PostgreSQL CREATE POLICY; useful for multi-tenant apps.

7. Q: How to detect suspicious activity?
A: Monitor abnormal query patterns, failed logins, sudden resource spikes; integrate alerts.

8. Q: Encrypt data at rest and in transit?
A: At rest: TDE or KMS-managed keys; In transit: TLS/SSL; optionally encrypt sensitive columns.

9. Q: How to prevent SQL injection?
A: Parameterized queries, ORM query builders, input validation; avoid string concatenation.

10. Q: How to safely expose read-only replicas?
A: Use API/proxy layer, limit queries, enforce auth, throttle requests, avoid direct public access.

26. CI/CD & Database Migrations

11. Q: How to integrate DB migrations into CI/CD?
A: Versioned migration scripts (Flyway, Liquibase, Alembic); run in pipeline pre-prod; automated rollback scripts; test on staging.

12. Q: How to ensure schema consistency across environments?
A: Run migration checks, checksum validation, enforce migration order, versioned scripts in VCS.

13. Q: Zero-downtime migrations?
A: Backward-compatible changes first, dual writes, feature flags, phased rollout, shadow tables if needed.

14. Q: Rollback failed migration?
A: Use undo scripts, restore snapshot if destructive, test rollback in staging first.

15. Q: Concurrent migrations handling?
A: Serialize migrations, use advisory locks, track applied versions.

16. Q: Validate migration success?
A: Row counts, integrity checks, test queries, app feature verification.

17. Q: Backfill data safely?
A: Incremental batch processing, dual writes, monitor performance, avoid locking production tables.

18. Q: Multi-environment pipelines?
A: Separate staging/prod configs, automated promotion of migration scripts, pre/post-deploy validation.

19. Q: Migration in cloud-managed DB?
A: Use CI/CD pipelines with secrets management; avoid blocking production traffic.

20. Q: Environment drift handling?
A: Track schema versions, periodic audits, enforce migration pipeline.

27. Infrastructure as Code (IaC)

21. Q: IaC for databases?
A: Define schema, users, backups, monitoring, configs as code; enables reproducible provisioning.

22. Q: Examples of IaC tools for DBs?
A: Terraform, CloudFormation, Pulumi, Crossplane, Kubernetes operators.

23. Q: Provision RDS via Terraform?
A: Define aws_db_instance, engine, storage, backups, multi-AZ, security groups, monitoring.

24. Q: Secrets management in IaC?
A: Reference Vault or Secrets Manager; avoid hardcoding passwords.

25. Q: Backup policies via IaC?
A: Configure snapshot retention, automated backups, multi-AZ replication in Terraform/CloudFormation.

26. Q: Security via IaC?
A: Parameter groups, TLS, IAM roles, encryption at rest, VPC isolation.

27. Q: Run migrations via IaC?
A: Migration scripts executed post-provisioning as part of pipeline.

28. Q: Test IaC DB changes?
A: Apply to staging clones, validate schema/data, rollback if needed.

29. Q: Handle env-specific DB params?
A: Use variables or parameter files per environment.

30. Q: Monitor IaC-managed DBs?
A: Integrate monitoring during provisioning; alert on thresholds.

## 28. Chaos Testing & Reliability

1. Q: Simulate DB failures?
A: Stop primary, simulate disk full, network partition, replica lag; test app recovery/failover.

2. Q: Test read replica failover?
A: Promote replica in staging, redirect traffic, validate consistency and app behavior.

3. Q: Validate backups?
A: Restore in isolated environment, run queries, verify integrity.

4. Q: Measure RTO/RPO?
A: RTO: recovery time; RPO: max data loss tolerated; test via failover drills.

5. Q: Transaction retries during failure?
A: Idempotent writes, retry with backoff, avoid double-processing.

## 29. Caching Strategies

1. Q: When to use caching?
A: Frequently-read queries, read-heavy workloads, reduce DB load/latency.

2. Q: Cache invalidation strategies?
A: TTL, write-through, write-back, event-driven invalidation.

3. Q: Combine caching with DB scaling?
A: Cache hot keys, cache-aside pattern, reduce read replica pressure.

4. Q: Handle cache consistency?
A: TTL, pub/sub invalidation, cache versioning, distributed locks.

5. Q: Monitor cache performance?
A: Hit/miss ratio, eviction counts, memory usage, latency metrics.

30. Multi-Region & Advanced Scenarios

6. Q: Replicate DB across regions?
A: Asynchronous global replicas, DynamoDB global tables, cross-region read replicas.

7. Q: Handle cross-region latency?
A: Read local replicas, geo-partition data, minimize cross-region writes.

8. Q: Global consistency management?
A: Eventual consistency for non-critical data; synchronous for critical if supported.

9. Q: Disaster recovery across regions?
A: Multi-region snapshots, cold standby, automated failover, DR runbooks.

10. Q: Test global failover?
A: Simulate primary region failure, validate replica promotion, app routing.

11. Q: Handle corrupted database?
A: Restore latest backup, apply binlogs/WAL, validate schema/app.

12. Q: Runaway queries consuming resources?
A: Identify via stats/slow logs, terminate, optimize query plan, limit connections.

13. Q: Primary DB crash under load?
A: Promote failover replica, redirect traffic, restore primary if needed, analyze root cause.

14. Q: Large table schema change without downtime?
A: Shadow tables, batch backfill, dual-write, phased migration, CREATE INDEX CONCURRENTLY.

15. Q: Unexpected version drift between staging and prod?
A: Compare migration version tables, validate applied migrations, re-sync staging, enforce pipeline controls.

## 31. Production Performance & Troubleshooting

1. Q: How to debug slow writes?
A: Check indexes, WAL/log settings, transaction batching, table locks, disk I/O, and connection pool saturation.

2. Q: How to detect table bloat in PostgreSQL?
A: Query pg_stat_all_tables and pgstattuple, monitor dead tuples, use VACUUM/ANALYZE.

3. Q: How to handle lock contention under heavy traffic?
A: Reduce transaction scope, optimize queries, batch updates, use row-level locks, monitor pg_locks.

4. Q: How to diagnose deadlocks?
A: Enable deadlock logs, examine conflicting queries, reorder transactions, implement retry logic.

5. Q: Slow replica?
A: Check replication lag, network throughput, primary write spikes, large WAL/binlog files.

6. Q: Identify hot partitions in NoSQL?
A: Monitor access patterns, uneven request distribution; mitigate with partition key randomness or sharding.

7. Q: Unexpected CPU spike?
A: Check long-running queries, missing indexes, large aggregations, batch jobs; profile queries.

8. Q: High memory usage in DB?
A: Check caching settings, connection pool size, unoptimized queries, temporary table usage.

9. Q: Disk I/O bottleneck?
A: Monitor read/write latency, large sequential scans, table bloat, insufficient disk throughput; optimize queries and indexes.

10. Q: Debugging query plan regressions?
A: Compare EXPLAIN plans before/after schema or stats changes, check index usage, force plan hints if needed.

## 32. Backups & Restoration Scenarios

1. Q: Restore DB from logical snapshot?
A: Export/import SQL dump, validate schema, test app queries.

2. Q: Point-in-time recovery?
A: Restore latest snapshot, replay WAL/binlogs to desired timestamp, validate data.

3. Q: Corrupted table?
A: Restore table from backup, use dump/restore or logical replication, rebuild indexes.

4. Q: Replica fails during restoration?
A: Rebuild replica from snapshot or base backup, ensure replication slot/log positions match.

5. Q: Backups filling disk?
A: Rotate snapshots, compress backups, delete old retention, use off-site storage.

6. Q: Cloud backup cost optimization?
A: Tiered storage, incremental snapshots, automated retention policies, compression.

7. Q: Test backup integrity?
A: Restore to staging, run queries, validate row counts, sample data, check foreign keys.

8. Q: Multi-region backup validation?
A: Restore cross-region copy in staging, ensure replication, monitor latency.

9. Q: Automated disaster recovery drill?
A: Failover primary, restore backups, validate app connectivity, document RTO/RPO.

10. Q: Backup during high-load periods?
A: Use snapshots or non-blocking backups, avoid full table locks, schedule off-peak.

## 33. Scaling & High Availability

1. Q: DB server running out of connections?
A: Check pool size, active queries, slow queries; scale replicas; limit max connections per user.

2. Q: Scale relational DB for millions of users?
A: Read replicas, sharding, partitioning, caching, optimize queries, consider serverless or distributed DB.

3. Q: Scaling NoSQL DB?
A: Increase partition count, on-demand capacity, horizontal scaling, monitor hot keys.

4. Q: Active-active vs active-passive?
A: Active-active: multi-primary writes, high availability, conflict resolution needed; active-passive: primary handles writes, standby takes over on failover.

5. Q: Multi-region failover?
A: Replicate data asynchronously, promote standby, update DNS/app routing, monitor consistency.

6. Q: Long-running transactions blocking writes?
A: Kill or optimize transaction, batch updates, monitor lock tables.

7. Q: Read-heavy traffic spikes?
A: Add read replicas, enable caching, use CDN for static content, query optimization.

8. Q: Write-heavy traffic spikes?
A: Batch inserts/updates, optimize indexes, consider queue-based ingestion, partitioning.

9. Q: Monitor active-active setup?
A: Track replication conflicts, latency, resource usage, cross-region consistency.

10. Q: High availability in cloud DB?
A: Multi-AZ deployments, automated failover, backups, monitoring, alerting.

## 34. Security & Compliance Scenarios

1. Q: Detecting unauthorized DB access?
A: Enable audit logs, monitor login attempts, integrate SIEM alerts, track abnormal queries.

2. Q: Privilege escalation?
A: Enforce least privilege, monitor GRANTs, periodic access reviews, avoid shared admin accounts.

3. Q: Data leaks?
A: Encrypt sensitive columns, TLS for in-transit, audit access logs, monitor unusual queries.

4. Q: Multi-tenant isolation?
A: Separate schema/DB per tenant, row-level security, network isolation, enforce quotas.

5. Q: Regulatory compliance?
A: Retention policies, audit logs, encryption, access reviews, documentation for HIPAA/GDPR.

6. Q: Rotate encryption keys?
A: Use KMS/Vault, re-encrypt in background, maintain key versions.

7. Q: Prevent accidental mass deletion?
A: Soft deletes, triggers, pre-delete backups, confirmations, application-level safeguards.

8. Q: SQL injection prevention?
A: Parameterized queries, ORM query builders, input validation, strict user permissions.

9. Q: Exposing read replicas to public?
A: Use proxy/API, throttle queries, authenticate, read-only, private endpoints.

10. Q: Handling security incidents?
A: Isolate affected DB, restore from backup if needed, audit logs, rotate credentials, apply patches.

## 35. Query Optimization

1. Q: How to find slow queries?
A: Enable slow query logs, monitor execution time, use EXPLAIN/EXPLAIN ANALYZE to review query plans.

2. Q: How to optimize a JOIN-heavy query?
A: Ensure proper indexes on join columns, avoid unnecessary joins, consider denormalization if read-heavy.

3. Q: Optimize aggregations?
A: Use pre-aggregated tables, materialized views, partitioning, proper indexing, avoid scanning full tables.

4. Q: Detect N+1 query problem?
A: Monitor repeated queries per object in ORM; solve with eager loading, batch queries, or joins.

5. Q: Optimize queries on large tables?
A: Partition tables, create indexes, vacuum/analyze (PostgreSQL), avoid sequential scans, use covering indexes.

6. Q: How to handle queries with high latency in cloud DB?
A: Review network latency, add read replicas, caching layer, query plan optimization, monitor metrics.

7. Q: Optimize text search queries?
A: Use full-text indexes, inverted indexes, search-specific engines (Elasticsearch, PostgreSQL tsvector), avoid LIKE '%pattern%' scans.

8. Q: Detect missing indexes?
A: Use query plan analysis (EXPLAIN), DB stats tables, slow query logs; monitor index usage stats.

9. Q: How to handle large IN clauses?
A: Use temporary tables or joins instead of long IN lists; consider batch queries.

10. Q: Optimize multi-tenant queries?
A: Index on tenant_id, consider separate schema/DB for heavy tenants, cache frequent tenant queries.

## 36. Indexing Strategies

1. Q: Clustered vs non-clustered index?
A: Clustered: table physically ordered, one per table, faster range queries; Non-clustered: separate structure, multiple allowed, slower for range queries.

2. Q: Composite indexes?
A: Index multiple columns; order matters; speeds up queries filtering/ordering by those columns.

3. Q: Partial indexes?
A: Index subset of rows meeting condition; reduces storage, improves performance.

4. Q: Covering indexes?
A: Index includes all columns needed for a query; avoids fetching table rows.

5. Q: Unique indexes?
A: Enforces uniqueness, can include NULLs depending on DB; improves lookups.

6. Q: Index maintenance?
A: Rebuild or reindex periodically, monitor fragmentation, especially for high-write tables.

7. Q: Indexing in NoSQL?
A: DynamoDB: primary key + GSIs/LSIs; MongoDB: single/multi-field, unique, TTL indexes; optimize for query patterns.

8. Q: Tradeoffs of indexing?
A: Speeds reads, slows writes, increases storage; balance based on workload.

9. Q: Index selection for analytics?
A: Columnar/bitmap indexes for low-cardinality columns; consider materialized views.

10. Q: Monitor index usage?
A: PostgreSQL: pg_stat_user_indexes; MySQL: SHOW INDEX; remove unused indexes.

## 37. Database Scaling Scenarios

1. Q: Read-heavy workload?
A: Add read replicas, caching, optimize queries, shard read-only data if needed.

2. Q: Write-heavy workload?
A: Partition/shard, batch writes, optimize indexes, queue-based ingestion.

3. Q: Multi-region scaling?
A: Use global tables (NoSQL), cross-region replicas, geo-partitioning, eventual consistency.

4. Q: High availability setup?
A: Multi-AZ deployments, automatic failover, backups, replication monitoring, connection retries.

5. Q: Scaling relational DB to millions of users?
A: Partition/shard, read replicas, caching, query optimization, consider serverless/autoscaling DB options.

6. Q: Scaling NoSQL DB to millions of users?
A: Horizontal scaling, partition keys, adaptive capacity, on-demand throughput, monitor hot keys.

7. Q: Handling spike traffic?
A: Use caching, queue-based ingestion, auto-scaling replicas, rate-limiting, query optimization.

8. Q: Database connection saturation?
A: Connection pooling, limit max connections per user, monitor pool stats, scale replicas if needed.

9. Q: Replica lag mitigation?
A: Optimize writes on primary, add replicas, monitor WAL/binlog, check network throughput.

10. Q: Sharding and partitioning strategy?
A: Shard by tenant or range/hash key; partition large tables for better write/read performance.

## 38. Advanced Practical Scenarios

1. Q: App shows inconsistent reads from replica?
A: Check replication lag, routing logic, eventual consistency, monitor pending WAL/binlogs.

2. Q: Accidental deletion of critical data?
A: Restore from backup, replay logs for PITR, validate rows, communicate cutover.

3. Q: Migration script failed mid-deploy?
A: Rollback via undo script or restore snapshot, debug staging first, resume migration carefully.

4. Q: Disk full error in production?
A: Archive/truncate old data, rotate logs, dynamically increase storage if cloud-managed, alert monitoring.

5. Q: Large batch job causing deadlocks?
A: Run in smaller batches, off-peak, optimize indexes, use row-level locking, retry logic.

6. Q: Query performance degrades after schema changes?
A: Update statistics, analyze table, rebuild indexes, check query plan, rewrite slow queries.

7. Q: Multi-tenant environment performance issue?
A: Monitor heavy tenants, consider dedicated schema/DB, index on tenant_id, caching.

8. Q: Replica failing repeatedly?
A: Rebuild replica, check network, monitor primary write spikes, validate WAL/binlogs.

9. Q: Cloud DB cost too high?
A: Rightsize instances, archive old data, optimize queries, enable serverless/autoscaling, monitor IOPS.

10. Q: Unexpected failover triggered?
A: Validate replica promotion, check monitoring/alerts, investigate primary health, ensure app reconnect logic.

39. Multi-Database & Cloud Operations

11. Q: How do you orchestrate multiple database types in one system?
A: Use microservice architecture; each service owns its DB; use APIs for communication; enforce data contracts; monitor each DB separately.

12. Q: How to handle cross-database joins?
A: Prefer application-side joins or ETL/analytics layer; avoid real-time cross-DB joins in production; use materialized views or data warehouse.

13. Q: How to synchronize data between SQL and NoSQL?
A: Use CDC (change data capture), event-driven pipelines, Kafka/stream processing, periodic batch updates.

14. Q: How to manage secrets across multiple cloud DBs?
A: Centralize in Vault or Secrets Manager; dynamic credentials; rotate keys; IAM-based access; logging access events.

15. Q: How to monitor multi-cloud databases?
A: Unified monitoring dashboards (Datadog, Prometheus, CloudWatch, Stackdriver); alert on latency, errors, replication lag, and resource usage.

16. Q: How to handle failover in hybrid cloud DBs?
A: Implement cross-region replication, automated promotion policies, monitor replication lag, plan for DNS/app routing updates.

17. Q: How to debug cloud DB connectivity issues?
A: Check VPC/subnet/security groups, network routes, firewall rules, TLS certificates, DB logs, client retries.

18. Q: Multi-tenant cloud DB monitoring?
A: Track resource usage per tenant, query performance, storage, error rates, and implement per-tenant alerting.

19. Q: How to manage schema versioning in multi-environment pipelines?
A: Use versioned migration scripts, environment-specific configs, CI/CD pipelines, automated pre-deploy checks, rollback plans.

20. Q: Cross-region latency mitigation strategies?
A: Geo-partitioning, read replicas near consumers, caching layers, asynchronous replication for non-critical data.

## 40. Performance Troubleshooting Scenarios

1. Q: How to debug slow cloud DB queries?
A: Enable slow query logging, use EXPLAIN plans, monitor resource usage, check indexes, optimize schema, consider caching.

2. Q: How to debug high write latency?
A: Monitor disk I/O, WAL/binlog throughput, transaction batching, indexing overhead, table partitioning, and hot partitions.

3. Q: Detecting runaway queries?
A: Monitor active sessions, slow query logs, resource usage; terminate offending queries; consider query throttling.

4. Q: High replica lag suddenly?
A: Check for long-running transactions on primary, network issues, disk bottlenecks, batch inserts, insufficient replication threads.

5. Q: High CPU/memory in DB?
A: Check query plans, indexing, caching, long-running jobs, concurrent connections; profile queries; optimize queries.

6. Q: How to identify inefficient joins?
A: Use EXPLAIN/ANALYZE, check join order, missing indexes, use smaller datasets for testing, optimize schema.

7. Q: Query plan changes after schema migration?
A: Update statistics, rebuild/reindex, analyze query plan, check optimizer changes, test in staging first.

8. Q: Disk I/O bottlenecks?
A: Monitor read/write latency, table scans, logs; move hot tables to faster storage, optimize queries, partition data.

9. Q: Detecting index bloat?
A: Postgres: pg_stat_all_indexes, pgstattuple; rebuild/reindex if fragmentation high; monitor usage.

10. Q: Slow aggregation queries?
A: Use pre-aggregated tables, materialized views, partitioning, appropriate indexes, and caching.

## 41. Disaster Recovery & Chaos Testing

1. Q: How to simulate DB failure in staging?
A: Stop primary, failover replicas, simulate disk full, network partition, monitor app behavior.

2. Q: Validate backups during DR drill?
A: Restore backup to staging, run queries, verify schema, row counts, referential integrity, app validation.

3. Q: Test replication recovery?
A: Stop replica, apply WAL/binlogs, check data consistency, monitor lag.

4. Q: Validate point-in-time recovery (PITR)?
A: Restore snapshot, replay logs to target timestamp, verify data integrity.

5. Q: Monitor failover events?
A: Track primary promotion, replica promotion, connectivity, alerting for unexpected failovers.

6. Q: Test read/write separation under load?
A: Direct reads to replicas, writes to primary; monitor replication lag; measure query performance.

7. Q: Simulate network latency or partition?
A: Use chaos tools or firewall rules, observe DB and app behavior, ensure retry logic works.

8. Q: Validate cross-region DR?
A: Restore copy in secondary region, promote standby, test application routing.

9. Q: Test schema migration rollback?
A: Apply migration to staging, simulate failure, rollback, validate data and schema integrity.

10. Q: Validate multi-tenant isolation?
A: Run queries from multiple tenants, verify row-level security, performance isolation, and quotas.

## 42. Miscellaneous Practical Questions

1. Q: How to find the second highest salary?
A: Use ORDER BY salary DESC LIMIT 1 OFFSET 1 or MAX(salary) WHERE salary < MAX(salary).

2. Q: How to store user preferences at scale?
A: JSONB columns (Postgres), key-value tables, NoSQL stores like DynamoDB; use caching.

3. Q: What happens when you delete a row with foreign key references?
A: Depending on FK constraints: CASCADE deletes, RESTRICT prevents deletion, SET NULL updates referencing rows.

4. Q: How to scale relational DB for millions of users?
A: Read replicas, partitioning/sharding, caching, query optimization, vertical/horizontal scaling.

5. Q: How to integrate secrets management with DB?
A: Vault or Secrets Manager for dynamic credentials; apps fetch secrets via secure APIs; avoid hardcoding.

6. Q: Difference between logical vs physical backups?
A: Logical: SQL dump, portable, slower; Physical: raw file copy, faster restore, OS-level recovery.

7. Q: Explain clustered vs non-clustered indexes.
A: Clustered: table physically ordered, one per table; Non-clustered: separate structure pointing to table rows, multiple allowed.

8. Q: Difference between read replica and failover replica.
A: Read replica: read-only, offloads queries; Failover replica: standby, promoted on primary failure.

9. Q: How do you debug slow queries/writes and improve?
A: Analyze query plan, check indexes, monitor locks/transactions, cache hot data, optimize schema.

10. Q: How to handle schema changes without downtime?
A: Backward-compatible changes, dual-write, shadow tables, phased migration, feature flags.