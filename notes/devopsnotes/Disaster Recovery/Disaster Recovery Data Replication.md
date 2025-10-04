# Disaster Recovery Data Replication

**Disaster Recovery Data Replication** ensures continuous data availability and consistency across multiple locations through real-time and near-real-time data synchronization techniques that minimize data loss and enable rapid recovery in disaster scenarios.

## Replication Architecture Patterns

### Synchronous vs Asynchronous Replication

#### Synchronous Replication Implementation
```yaml
synchronous_replication:
  characteristics:
    consistency: "Strong consistency guaranteed"
    rpo: "Zero data loss (RPO = 0)"
    rto: "Depends on failover automation (typically 1-5 minutes)"
    performance_impact: "Higher latency due to confirmation requirements"

  use_cases:
    - "Financial transactions and trading systems"
    - "Critical customer data and orders"
    - "Regulatory compliance data"
    - "Mission-critical applications requiring zero data loss"

  implementation_patterns:
    database_level:
      sql_server_always_on:
        configuration: |
          -- Enable Always On Availability Groups
          ALTER SERVER CONFIGURATION SET HADR CLUSTER CONTEXT = 'WSFC-Cluster'

          -- Create availability group with synchronous commit
          CREATE AVAILABILITY GROUP CriticalDataAG
          WITH (AUTOMATED_BACKUP_PREFERENCE = SECONDARY)
          FOR DATABASE [CustomerDB], [OrderDB], [PaymentDB]
          REPLICA ON
          'PRIMARY-SQL01' WITH (
              ENDPOINT_URL = 'TCP://primary-sql01.company.com:5022',
              AVAILABILITY_MODE = SYNCHRONOUS_COMMIT,
              FAILOVER_MODE = AUTOMATIC,
              SECONDARY_ROLE(ALLOW_CONNECTIONS = NO)
          ),
          'DR-SQL01' WITH (
              ENDPOINT_URL = 'TCP://dr-sql01.company.com:5022',
              AVAILABILITY_MODE = SYNCHRONOUS_COMMIT,
              FAILOVER_MODE = AUTOMATIC,
              SECONDARY_ROLE(ALLOW_CONNECTIONS = YES)
          )

      postgresql_streaming:
        primary_config: |
          # postgresql.conf on primary
          wal_level = replica
          max_wal_senders = 3
          wal_keep_segments = 64
          synchronous_standby_names = 'standby1'
          synchronous_commit = on

        standby_config: |
          # recovery.conf on standby
          standby_mode = 'on'
          primary_conninfo = 'host=primary.company.com port=5432 user=replicator'
          trigger_file = '/tmp/postgresql.trigger'

    storage_level:
      emc_recoverpoint:
        configuration: |
          # RecoverPoint consistency group configuration
          consistency_group create name=CriticalDataCG
          consistency_group add copy name=PrimaryCopy cluster=NYC-Cluster
          consistency_group add copy name=DRCopy cluster=CHI-Cluster
          consistency_group set replication_mode=synchronous
          consistency_group set rpo=0

      netapp_snapmirror:
        configuration: |
          # SnapMirror synchronous relationship
          snapmirror create -source-path svm1:vol_critical \
                           -destination-path dr_svm:vol_critical_dr \
                           -type sync \
                           -policy MirrorAllSnapshots

  monitoring_and_alerting:
    lag_monitoring:
      acceptable_threshold: "< 100ms"
      warning_threshold: "100ms - 500ms"
      critical_threshold: "> 500ms"

    health_checks:
      frequency: "Every 30 seconds"
      metrics:
        - "Replication lag time"
        - "Transaction commit success rate"
        - "Network connectivity status"
        - "Storage replication health"
```

#### Asynchronous Replication Strategy
```yaml
asynchronous_replication:
  characteristics:
    consistency: "Eventual consistency"
    rpo: "Minutes to hours depending on configuration"
    rto: "Varies based on failover process"
    performance_impact: "Minimal impact on primary systems"

  use_cases:
    - "Reporting and analytics data"
    - "Content management systems"
    - "Long-distance replication (cross-region)"
    - "High-volume transactional systems where performance is critical"

  implementation_examples:
    mysql_master_slave:
      master_configuration: |
        # my.cnf on master
        [mysqld]
        server-id = 1
        log-bin = mysql-bin
        binlog-format = ROW
        binlog-do-db = production_db
        expire_logs_days = 7

      slave_configuration: |
        # my.cnf on slave
        [mysqld]
        server-id = 2
        relay-log = relay-bin
        read-only = 1

        # Start replication
        CHANGE MASTER TO
          MASTER_HOST='master.company.com',
          MASTER_USER='replication',
          MASTER_PASSWORD='secure_password',
          MASTER_LOG_FILE='mysql-bin.000001',
          MASTER_LOG_POS=107;
        START SLAVE;

    mongodb_replica_set:
      configuration: |
        // MongoDB replica set configuration
        rs.initiate({
          _id: "prodReplicaSet",
          members: [
            { _id: 0, host: "primary.company.com:27017", priority: 10 },
            { _id: 1, host: "secondary1.company.com:27017", priority: 5 },
            { _id: 2, host: "dr.company.com:27017", priority: 1 }
          ]
        })

    oracle_data_guard:
      primary_database: |
        -- Enable archive log mode
        ALTER DATABASE ARCHIVELOG;

        -- Configure Data Guard parameters
        ALTER SYSTEM SET LOG_ARCHIVE_CONFIG='DG_CONFIG=(PROD,STANDBY)';
        ALTER SYSTEM SET LOG_ARCHIVE_DEST_2='SERVICE=standby ASYNC VALID_FOR=(ONLINE_LOGFILES,PRIMARY_ROLE) DB_UNIQUE_NAME=STANDBY';
        ALTER SYSTEM SET STANDBY_FILE_MANAGEMENT=AUTO;

      standby_database: |
        -- Create standby database from backup
        DUPLICATE TARGET DATABASE FOR STANDBY FROM ACTIVE DATABASE;

        -- Start managed recovery
        ALTER DATABASE RECOVER MANAGED STANDBY DATABASE DISCONNECT FROM SESSION;
```

### Multi-Master Replication

#### Active-Active Replication Architecture
```bash
#!/bin/bash
# Multi-Master MySQL Replication Setup Script

setup_multi_master_replication() {
    local node1_ip="$1"
    local node2_ip="$2"
    local replication_user="$3"
    local replication_password="$4"

    echo "=== Setting up Multi-Master MySQL Replication ==="
    echo "Node 1: $node1_ip"
    echo "Node 2: $node2_ip"

    # Configure Node 1
    configure_mysql_node "$node1_ip" "1" "$node2_ip" "$replication_user" "$replication_password"

    # Configure Node 2
    configure_mysql_node "$node2_ip" "2" "$node1_ip" "$replication_user" "$replication_password"

    # Verify replication status
    verify_replication_health "$node1_ip" "$node2_ip"
}

configure_mysql_node() {
    local node_ip="$1"
    local server_id="$2"
    local master_ip="$3"
    local repl_user="$4"
    local repl_password="$5"

    echo "Configuring MySQL Node: $node_ip (Server ID: $server_id)"

    # Create MySQL configuration
    cat > "/tmp/mysql_node${server_id}.cnf" << EOF
[mysqld]
server-id = $server_id
log-bin = mysql-bin
binlog-format = ROW
auto-increment-increment = 2
auto-increment-offset = $server_id
expire_logs_days = 7
sync_binlog = 1
innodb_flush_log_at_trx_commit = 1

# Conflict resolution
slave-skip-errors = 1062,1032
replicate-ignore-table = mysql.user
replicate-ignore-table = mysql.db
EOF

    # Apply configuration (assuming remote access is configured)
    echo "Applying configuration to $node_ip..."

    # Create replication user
    mysql -h "$node_ip" -u root -p << SQL
CREATE USER IF NOT EXISTS '$repl_user'@'%' IDENTIFIED BY '$repl_password';
GRANT REPLICATION SLAVE ON *.* TO '$repl_user'@'%';
FLUSH PRIVILEGES;

-- Get master status
SHOW MASTER STATUS;
SQL

    # Configure as slave to the other node
    mysql -h "$node_ip" -u root -p << SQL
STOP SLAVE;
CHANGE MASTER TO
    MASTER_HOST='$master_ip',
    MASTER_USER='$repl_user',
    MASTER_PASSWORD='$repl_password',
    MASTER_AUTO_POSITION=1;
START SLAVE;
SQL
}

verify_replication_health() {
    local node1="$1"
    local node2="$2"

    echo "=== Verifying Replication Health ==="

    # Check Node 1 slave status
    echo "Node 1 Slave Status:"
    mysql -h "$node1" -u root -p -e "SHOW SLAVE STATUS\G" | grep -E "(Slave_IO_Running|Slave_SQL_Running|Seconds_Behind_Master)"

    # Check Node 2 slave status
    echo "Node 2 Slave Status:"
    mysql -h "$node2" -u root -p -e "SHOW SLAVE STATUS\G" | grep -E "(Slave_IO_Running|Slave_SQL_Running|Seconds_Behind_Master)"

    # Test bidirectional replication
    test_bidirectional_replication "$node1" "$node2"
}

test_bidirectional_replication() {
    local node1="$1"
    local node2="$2"
    local test_db="replication_test"
    local timestamp=$(date +%s)

    echo "Testing bidirectional replication..."

    # Create test database and table on Node 1
    mysql -h "$node1" -u root -p << SQL
CREATE DATABASE IF NOT EXISTS $test_db;
USE $test_db;
CREATE TABLE IF NOT EXISTS test_table (
    id INT AUTO_INCREMENT PRIMARY KEY,
    node VARCHAR(10),
    timestamp BIGINT,
    data VARCHAR(255)
);
INSERT INTO test_table (node, timestamp, data) VALUES ('node1', $timestamp, 'Test from Node 1');
SQL

    # Wait for replication
    sleep 5

    # Insert on Node 2 and verify
    mysql -h "$node2" -u root -p << SQL
USE $test_db;
INSERT INTO test_table (node, timestamp, data) VALUES ('node2', $timestamp, 'Test from Node 2');
SELECT * FROM test_table WHERE timestamp = $timestamp;
SQL

    # Verify on Node 1
    mysql -h "$node1" -u root -p << SQL
USE $test_db;
SELECT * FROM test_table WHERE timestamp = $timestamp;
SQL

    echo "Bidirectional replication test completed"
}

# Conflict resolution monitoring
monitor_replication_conflicts() {
    local node_ip="$1"

    while true; do
        conflict_count=$(mysql -h "$node_ip" -u root -p -e "SHOW SLAVE STATUS\G" | grep "Last_Error" | wc -l)

        if [ "$conflict_count" -gt 0 ]; then
            echo "ALERT: Replication conflicts detected on $node_ip"
            mysql -h "$node_ip" -u root -p -e "SHOW SLAVE STATUS\G" | grep -A 5 -B 5 "Last_Error"

            # Auto-resolution for common conflicts
            mysql -h "$node_ip" -u root -p << SQL
STOP SLAVE;
SET GLOBAL SQL_SLAVE_SKIP_COUNTER = 1;
START SLAVE;
SQL
        fi

        sleep 30
    done
}

# Example usage
setup_multi_master_replication "10.1.1.10" "10.1.2.10" "repl_user" "secure_password123"
```

## Cross-Platform Replication

### Database Cross-Platform Replication

#### Heterogeneous Database Replication
```yaml
cross_platform_replication:
  oracle_to_postgresql:
    method: "Oracle GoldenGate with PostgreSQL adapter"

    oracle_configuration: |
      -- Oracle source configuration
      ALTER DATABASE ADD SUPPLEMENTAL LOG DATA;
      ALTER DATABASE ADD SUPPLEMENTAL LOG DATA (PRIMARY KEY, UNIQUE) COLUMNS;

      -- Create GoldenGate user
      CREATE USER ggadmin IDENTIFIED BY secure_password;
      GRANT DBA TO ggadmin;
      GRANT SELECT ANY DICTIONARY TO ggadmin;

    goldengate_setup: |
      # Extract process configuration
      EXTRACT ext_ora
      USERID ggadmin, PASSWORD secure_password
      EXTTRAIL ./dirdat/lt
      TABLE schema.customers;
      TABLE schema.orders;
      TABLE schema.products;

    postgresql_target: |
      -- PostgreSQL target preparation
      CREATE USER gg_postgres WITH PASSWORD 'secure_password';
      GRANT ALL PRIVILEGES ON DATABASE target_db TO gg_postgres;

      -- Install and configure replication slot
      SELECT pg_create_logical_replication_slot('oracle_replication', 'pgoutput');

  mysql_to_sqlserver:
    method: "Custom ETL pipeline with real-time CDC"

    mysql_cdc_setup: |
      # Enable MySQL binary logging
      [mysqld]
      server-id = 1
      log-bin = mysql-bin
      binlog-format = ROW
      binlog-row-image = FULL

    debezium_connector: |
      {
        "name": "mysql-sqlserver-connector",
        "config": {
          "connector.class": "io.debezium.connector.mysql.MySqlConnector",
          "database.hostname": "mysql.company.com",
          "database.port": "3306",
          "database.user": "debezium",
          "database.password": "dbz_password",
          "database.server.id": "184054",
          "database.server.name": "mysql_source",
          "database.include.list": "inventory,orders,customers",
          "database.history.kafka.bootstrap.servers": "kafka:9092",
          "database.history.kafka.topic": "schema-changes.inventory"
        }
      }

    sqlserver_sink: |
      -- SQL Server sink configuration
      CREATE LOGIN debezium_sink WITH PASSWORD = 'secure_password';
      CREATE USER debezium_sink FOR LOGIN debezium_sink;
      ALTER ROLE db_datareader ADD MEMBER debezium_sink;
      ALTER ROLE db_datawriter ADD MEMBER debezium_sink;
      ALTER ROLE db_ddladmin ADD MEMBER debezium_sink;

  nosql_to_relational:
    mongodb_to_postgresql:
      method: "MongoDB Change Streams with custom transformation"

      mongodb_changestream: |
        // MongoDB Change Stream listener
        const pipeline = [
          { $match: { 'fullDocument.status': { $in: ['active', 'pending'] } } }
        ];

        const changeStream = db.collection('orders').watch(pipeline);

        changeStream.on('change', (change) => {
          switch(change.operationType) {
            case 'insert':
              replicateInsert(change.fullDocument);
              break;
            case 'update':
              replicateUpdate(change.documentKey, change.updateDescription);
              break;
            case 'delete':
              replicateDelete(change.documentKey);
              break;
          }
        });

      transformation_logic: |
        const replicateInsert = async (document) => {
          const pgClient = new Client(pgConfig);
          await pgClient.connect();

          const query = `
            INSERT INTO orders (mongo_id, customer_id, order_date, total_amount, status, items)
            VALUES ($1, $2, $3, $4, $5, $6)
          `;

          const values = [
            document._id.toString(),
            document.customer_id,
            document.order_date,
            document.total_amount,
            document.status,
            JSON.stringify(document.items)
          ];

          await pgClient.query(query, values);
          await pgClient.end();
        };
```

### File and Object Storage Replication

#### Multi-Cloud Storage Replication
```bash
#!/bin/bash
# Multi-Cloud Storage Replication Script

setup_multicloud_replication() {
    local source_bucket="$1"
    local aws_target_bucket="$2"
    local azure_target_container="$3"
    local gcp_target_bucket="$4"

    echo "=== Setting up Multi-Cloud Storage Replication ==="
    echo "Source: $source_bucket"
    echo "AWS Target: $aws_target_bucket"
    echo "Azure Target: $azure_target_container"
    echo "GCP Target: $gcp_target_bucket"

    # Configure AWS S3 replication
    setup_s3_cross_region_replication "$source_bucket" "$aws_target_bucket"

    # Configure Azure Blob replication
    setup_azure_blob_replication "$source_bucket" "$azure_target_container"

    # Configure GCP Cloud Storage replication
    setup_gcp_storage_replication "$source_bucket" "$gcp_target_bucket"

    # Set up monitoring and verification
    setup_replication_monitoring "$source_bucket"
}

setup_s3_cross_region_replication() {
    local source_bucket="$1"
    local target_bucket="$2"

    echo "Configuring S3 Cross-Region Replication..."

    # Create replication role
    aws iam create-role --role-name S3ReplicationRole --assume-role-policy-document '{
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": "s3.amazonaws.com"
                },
                "Action": "sts:AssumeRole"
            }
        ]
    }'

    # Attach replication policy
    aws iam attach-role-policy --role-name S3ReplicationRole --policy-arn arn:aws:iam::aws:policy/service-role/AWSS3ReplicationServiceRolePolicy

    # Enable versioning on both buckets
    aws s3api put-bucket-versioning --bucket "$source_bucket" --versioning-configuration Status=Enabled
    aws s3api put-bucket-versioning --bucket "$target_bucket" --versioning-configuration Status=Enabled

    # Create replication configuration
    cat > "/tmp/replication-config.json" << EOF
{
    "Role": "arn:aws:iam::ACCOUNT:role/S3ReplicationRole",
    "Rules": [
        {
            "ID": "ReplicateEverything",
            "Status": "Enabled",
            "Priority": 1,
            "Filter": {"Prefix": ""},
            "Destination": {
                "Bucket": "arn:aws:s3:::$target_bucket",
                "StorageClass": "STANDARD_IA",
                "ReplicationTime": {
                    "Status": "Enabled",
                    "Time": {
                        "Minutes": 15
                    }
                },
                "Metrics": {
                    "Status": "Enabled",
                    "EventThreshold": {
                        "Minutes": 15
                    }
                }
            }
        }
    ]
}
EOF

    aws s3api put-bucket-replication --bucket "$source_bucket" --replication-configuration file:///tmp/replication-config.json
}

setup_azure_blob_replication() {
    local source_bucket="$1"
    local azure_container="$2"

    echo "Setting up Azure Blob Storage replication..."

    # Create Azure storage account and container if not exists
    az storage account create \
        --name "drreplication$(date +%s)" \
        --resource-group "disaster-recovery-rg" \
        --location "East US 2" \
        --sku "Standard_GRS"

    # Create container
    az storage container create \
        --name "$azure_container" \
        --account-name "drreplication$(date +%s)"

    # Set up sync script
    cat > "/opt/scripts/azure_sync.sh" << 'EOF'
#!/bin/bash
SOURCE_BUCKET="$1"
AZURE_CONTAINER="$2"

# Install and configure azcopy
wget -O azcopy.tar.gz https://aka.ms/downloadazcopy-v10-linux
tar -xf azcopy.tar.gz --strip-components=1

# Sync from S3 to Azure
while true; do
    aws s3 sync "s3://$SOURCE_BUCKET" "/tmp/s3_staging" --delete
    ./azcopy sync "/tmp/s3_staging" "https://storage.blob.core.windows.net/$AZURE_CONTAINER" --recursive --delete-destination=true

    echo "Azure sync completed at $(date)"
    sleep 300  # Sync every 5 minutes
done
EOF

    chmod +x /opt/scripts/azure_sync.sh
    nohup /opt/scripts/azure_sync.sh "$source_bucket" "$azure_container" &
}

setup_gcp_storage_replication() {
    local source_bucket="$1"
    local gcp_bucket="$2"

    echo "Setting up GCP Cloud Storage replication..."

    # Create GCP bucket with appropriate settings
    gsutil mb -p "disaster-recovery-project" -c "STANDARD" -l "us-central1" "gs://$gcp_bucket"

    # Enable object versioning
    gsutil versioning set on "gs://$gcp_bucket"

    # Set up Cloud Function for real-time replication
    cat > "/tmp/gcp_replication_function.py" << 'EOF'
import functions_framework
from google.cloud import storage
import boto3
import os

@functions_framework.cloud_event
def replicate_s3_to_gcs(cloud_event):
    """Replicate S3 object changes to GCS"""

    # Initialize clients
    s3_client = boto3.client('s3')
    gcs_client = storage.Client()

    # Parse S3 event
    bucket_name = cloud_event.data['Records'][0]['s3']['bucket']['name']
    object_key = cloud_event.data['Records'][0]['s3']['object']['key']

    # Download from S3
    response = s3_client.get_object(Bucket=bucket_name, Key=object_key)
    object_data = response['Body'].read()

    # Upload to GCS
    gcs_bucket = gcs_client.bucket(os.environ['GCS_TARGET_BUCKET'])
    blob = gcs_bucket.blob(object_key)
    blob.upload_from_string(object_data)

    print(f"Replicated {object_key} from S3 to GCS")
EOF

    # Deploy Cloud Function
    gcloud functions deploy s3-to-gcs-replication \
        --runtime python39 \
        --trigger-topic s3-object-changes \
        --entry-point replicate_s3_to_gcs \
        --set-env-vars GCS_TARGET_BUCKET="$gcp_bucket"
}

setup_replication_monitoring() {
    local source_bucket="$1"

    echo "Setting up replication monitoring..."

    cat > "/opt/scripts/replication_monitor.py" << 'EOF'
#!/usr/bin/env python3

import boto3
import json
import time
import logging
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ReplicationMonitor:
    def __init__(self, source_bucket):
        self.source_bucket = source_bucket
        self.s3_client = boto3.client('s3')

    def check_replication_status(self):
        """Check replication status and lag"""
        try:
            # Get replication metrics
            response = self.s3_client.get_bucket_replication(Bucket=self.source_bucket)

            for rule in response['ReplicationConfiguration']['Rules']:
                if rule['Status'] == 'Enabled':
                    logging.info(f"Replication rule {rule['ID']} is active")

                    # Check replication metrics
                    self.check_replication_metrics(rule['ID'])

        except Exception as e:
            logging.error(f"Error checking replication status: {e}")

    def check_replication_metrics(self, rule_id):
        """Check detailed replication metrics"""
        cloudwatch = boto3.client('cloudwatch')

        # Get replication latency metrics
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=1)

        response = cloudwatch.get_metric_statistics(
            Namespace='AWS/S3',
            MetricName='ReplicationLatency',
            Dimensions=[
                {'Name': 'SourceBucket', 'Value': self.source_bucket},
                {'Name': 'RuleId', 'Value': rule_id}
            ],
            StartTime=start_time,
            EndTime=end_time,
            Period=300,
            Statistics=['Average', 'Maximum']
        )

        if response['Datapoints']:
            latest_metric = max(response['Datapoints'], key=lambda x: x['Timestamp'])
            avg_latency = latest_metric['Average']
            max_latency = latest_metric['Maximum']

            logging.info(f"Replication latency - Average: {avg_latency}s, Maximum: {max_latency}s")

            # Alert if latency is too high
            if max_latency > 900:  # 15 minutes
                logging.warning(f"High replication latency detected: {max_latency}s")
                self.send_alert(f"Replication latency high: {max_latency}s")

    def send_alert(self, message):
        """Send alert notification"""
        sns = boto3.client('sns')
        sns.publish(
            TopicArn='arn:aws:sns:us-east-1:ACCOUNT:replication-alerts',
            Message=message,
            Subject='S3 Replication Alert'
        )

if __name__ == "__main__":
    monitor = ReplicationMonitor("SOURCE_BUCKET")

    while True:
        monitor.check_replication_status()
        time.sleep(300)  # Check every 5 minutes
EOF

    # Make script executable and start monitoring
    chmod +x /opt/scripts/replication_monitor.py
    nohup python3 /opt/scripts/replication_monitor.py &

    echo "Replication monitoring started"
}

# Replication verification and testing
verify_replication_integrity() {
    local source_bucket="$1"
    local target_buckets=("$@")

    echo "=== Verifying Replication Integrity ==="

    # Create test file
    test_file="/tmp/replication_test_$(date +%s).txt"
    echo "Replication test file created at $(date)" > "$test_file"

    # Upload to source bucket
    aws s3 cp "$test_file" "s3://$source_bucket/"

    # Wait for replication
    sleep 60

    # Verify in all target buckets
    for target_bucket in "${target_buckets[@]:1}"; do
        echo "Checking replication to $target_bucket..."

        if aws s3 ls "s3://$target_bucket/$(basename $test_file)" > /dev/null 2>&1; then
            echo "✓ File replicated successfully to $target_bucket"
        else
            echo "✗ File NOT found in $target_bucket"
        fi
    done

    # Cleanup
    rm -f "$test_file"
}

# Example usage
setup_multicloud_replication "primary-data-bucket" "aws-dr-bucket" "azure-dr-container" "gcp-dr-bucket"
verify_replication_integrity "primary-data-bucket" "aws-dr-bucket" "azure-dr-container" "gcp-dr-bucket"
```

## Real-Time Data Streaming

### Apache Kafka Replication

#### Kafka Cross-Datacenter Replication
```yaml
kafka_replication:
  mirrormaker2_configuration:
    clusters:
      primary:
        bootstrap_servers: "kafka1.nyc.company.com:9092,kafka2.nyc.company.com:9092,kafka3.nyc.company.com:9092"
        security_protocol: "SASL_SSL"
        sasl_mechanism: "PLAIN"

      disaster_recovery:
        bootstrap_servers: "kafka1.chi.company.com:9092,kafka2.chi.company.com:9092,kafka3.chi.company.com:9092"
        security_protocol: "SASL_SSL"
        sasl_mechanism: "PLAIN"

    connectors:
      primary_to_dr:
        name: "primary-to-dr-replication"
        config:
          connector.class: "org.apache.kafka.connect.mirror.MirrorSourceConnector"
          source.cluster.alias: "primary"
          target.cluster.alias: "dr"
          source.cluster.bootstrap.servers: "kafka1.nyc.company.com:9092,kafka2.nyc.company.com:9092"
          target.cluster.bootstrap.servers: "kafka1.chi.company.com:9092,kafka2.chi.company.com:9092"
          topics: "orders,payments,inventory,user-activity"
          groups: "order-processor,payment-service,inventory-updater"
          replication.factor: 3
          sync.topic.acls.enabled: true

  replication_monitoring:
    lag_monitoring: |
      #!/bin/bash
      # Kafka replication lag monitoring script

      check_mirrormaker_lag() {
          local source_cluster="$1"
          local target_cluster="$2"

          # Get consumer group lag for MirrorMaker
          lag_output=$(kafka-consumer-groups.sh \
              --bootstrap-server "$target_cluster" \
              --group mirrormaker2-cluster \
              --describe 2>/dev/null)

          echo "$lag_output" | while read line; do
              if echo "$line" | grep -q "primary\."; then
                  topic=$(echo "$line" | awk '{print $1}')
                  lag=$(echo "$line" | awk '{print $5}')

                  if [ "$lag" -gt 1000 ]; then
                      echo "ALERT: High replication lag for $topic: $lag messages"
                      send_alert "Kafka replication lag alert" "Topic $topic has lag of $lag messages"
                  fi
              fi
          done
      }

      # Monitor continuously
      while true; do
          check_mirrormaker_lag "kafka1.nyc.company.com:9092" "kafka1.chi.company.com:9092"
          sleep 30
      done

    throughput_monitoring: |
      # Kafka JMX metrics monitoring
      jmx_metrics:
        - "kafka.server:type=BrokerTopicMetrics,name=MessagesInPerSec,topic=orders"
        - "kafka.server:type=BrokerTopicMetrics,name=BytesInPerSec,topic=orders"
        - "kafka.connect:type=connector-metrics,connector=primary-to-dr-replication"
        - "kafka.connect:type=connector-task-metrics,connector=primary-to-dr-replication,task=0"

confluent_replicator:
  configuration: |
    # Confluent Replicator configuration
    name=replicator-primary-to-dr
    connector.class=io.confluent.connect.replicator.ReplicatorSourceConnector
    key.converter=io.confluent.connect.replicator.util.ByteArrayConverter
    value.converter=io.confluent.connect.replicator.util.ByteArrayConverter

    # Source cluster
    src.kafka.bootstrap.servers=kafka1.nyc.company.com:9092,kafka2.nyc.company.com:9092
    src.kafka.security.protocol=SASL_SSL
    src.kafka.sasl.mechanism=PLAIN
    src.kafka.sasl.jaas.config=org.apache.kafka.common.security.plain.PlainLoginModule required username="replicator" password="replicator_password";

    # Destination cluster
    dest.kafka.bootstrap.servers=kafka1.chi.company.com:9092,kafka2.chi.company.com:9092
    dest.kafka.security.protocol=SASL_SSL
    dest.kafka.sasl.mechanism=PLAIN
    dest.kafka.sasl.jaas.config=org.apache.kafka.common.security.plain.PlainLoginModule required username="replicator" password="replicator_password";

    # Replication settings
    topic.whitelist=orders,payments,inventory,user-activity
    topic.preserve.partitions=true
    topic.auto.create=true
    topic.config.sync=true
    offset.translator.tasks.max=10

    # Performance tuning
    tasks.max=8
    confluent.topic.replication.factor=3
    provenance.header.enable=true
```

This comprehensive Data Replication document provides detailed implementation strategies for synchronous and asynchronous replication, cross-platform data synchronization, multi-cloud storage replication, and real-time streaming replication using Apache Kafka and other enterprise-grade technologies.