# Disaster Recovery Database Disaster Recovery

**Disaster Recovery Database Disaster Recovery** provides comprehensive strategies, technologies, and procedures for protecting database systems against failures through advanced replication, backup, clustering, and automated recovery mechanisms that ensure data integrity and minimize recovery time objectives.

## Database-Specific DR Strategies

### SQL Server Disaster Recovery

#### Always On Availability Groups
```sql
-- SQL Server Always On Availability Groups Configuration

-- Enable Always On Availability Groups
ALTER SERVER CONFIGURATION SET HADR CLUSTER CONTEXT = 'WSFC-Cluster'

-- Create database master key
CREATE MASTER KEY ENCRYPTION BY PASSWORD = 'StrongPassword123!'

-- Create certificate for endpoint encryption
CREATE CERTIFICATE AvailabilityGroupCert
WITH SUBJECT = 'Availability Group Certificate'

-- Create mirroring endpoint
CREATE ENDPOINT Hadr_endpoint
    AS TCP (LISTENER_PORT = 5022, LISTENER_IP = ALL)
    FOR DATABASE_MIRRORING (
        ROLE = ALL,
        AUTHENTICATION = CERTIFICATE AvailabilityGroupCert,
        ENCRYPTION = REQUIRED ALGORITHM AES
    )

-- Grant permissions to service account
GRANT CONNECT ON ENDPOINT::Hadr_endpoint TO [DOMAIN\SQLService]

-- Create Availability Group
CREATE AVAILABILITY GROUP CriticalSystemsAG
WITH (
    AUTOMATED_BACKUP_PREFERENCE = SECONDARY,
    FAILURE_CONDITION_LEVEL = 3,
    HEALTH_CHECK_TIMEOUT = 30000
)
FOR DATABASE [CustomerDB], [OrderDB], [InventoryDB]
REPLICA ON
    'SQLPROD01' WITH (
        ENDPOINT_URL = 'TCP://sqlprod01.company.com:5022',
        AVAILABILITY_MODE = SYNCHRONOUS_COMMIT,
        FAILOVER_MODE = AUTOMATIC,
        BACKUP_PRIORITY = 50,
        SECONDARY_ROLE(ALLOW_CONNECTIONS = NO)
    ),
    'SQLPROD02' WITH (
        ENDPOINT_URL = 'TCP://sqlprod02.company.com:5022',
        AVAILABILITY_MODE = SYNCHRONOUS_COMMIT,
        FAILOVER_MODE = AUTOMATIC,
        BACKUP_PRIORITY = 100,
        SECONDARY_ROLE(ALLOW_CONNECTIONS = READ_ONLY)
    ),
    'SQLDR01' WITH (
        ENDPOINT_URL = 'TCP://sqldr01.company.com:5022',
        AVAILABILITY_MODE = ASYNCHRONOUS_COMMIT,
        FAILOVER_MODE = MANUAL,
        BACKUP_PRIORITY = 30,
        SECONDARY_ROLE(ALLOW_CONNECTIONS = READ_ONLY)
    )

-- Join secondary replicas to availability group
-- Run on each secondary replica
ALTER AVAILABILITY GROUP CriticalSystemsAG JOIN

-- Add databases to availability group on secondary replicas
ALTER DATABASE [CustomerDB] SET HADR AVAILABILITY GROUP = CriticalSystemsAG
ALTER DATABASE [OrderDB] SET HADR AVAILABILITY GROUP = CriticalSystemsAG
ALTER DATABASE [InventoryDB] SET HADR AVAILABILITY GROUP = CriticalSystemsAG

-- Configure listener for client connections
ALTER AVAILABILITY GROUP CriticalSystemsAG
ADD LISTENER 'CriticalSystemsListener' (
    WITH IP (
        ('10.1.1.100', '255.255.255.0'),
        ('10.2.1.100', '255.255.255.0')
    ),
    PORT = 1433
)
```

#### SQL Server Backup Strategy
```powershell
# PowerShell script for SQL Server backup automation

param(
    [string]$InstanceName = "SQLPROD01",
    [string]$BackupPath = "\\backup-server\SQLBackups",
    [string]$LogPath = "C:\Logs\SQLBackup.log"
)

# Import SQL Server module
Import-Module SQLPS -DisableNameChecking

# Function to write log messages
function Write-BackupLog {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] [$Level] $Message"
    Write-Host $logEntry
    Add-Content -Path $LogPath -Value $logEntry
}

# Function to perform full backup
function Backup-Database {
    param(
        [string]$DatabaseName,
        [string]$BackupType = "FULL"
    )

    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $backupFileName = "${DatabaseName}_${BackupType}_${timestamp}.bak"
    $backupFilePath = Join-Path $BackupPath $backupFileName

    try {
        Write-BackupLog "Starting $BackupType backup for database: $DatabaseName"

        switch ($BackupType) {
            "FULL" {
                $backupQuery = @"
                BACKUP DATABASE [$DatabaseName]
                TO DISK = '$backupFilePath'
                WITH COMPRESSION,
                     CHECKSUM,
                     VERIFY,
                     STATS = 10,
                     DESCRIPTION = 'Full backup of $DatabaseName - $timestamp'
"@
            }
            "DIFF" {
                $backupQuery = @"
                BACKUP DATABASE [$DatabaseName]
                TO DISK = '$backupFilePath'
                WITH DIFFERENTIAL,
                     COMPRESSION,
                     CHECKSUM,
                     VERIFY,
                     STATS = 10,
                     DESCRIPTION = 'Differential backup of $DatabaseName - $timestamp'
"@
            }
            "LOG" {
                $backupFileName = "${DatabaseName}_LOG_${timestamp}.trn"
                $backupFilePath = Join-Path $BackupPath $backupFileName
                $backupQuery = @"
                BACKUP LOG [$DatabaseName]
                TO DISK = '$backupFilePath'
                WITH COMPRESSION,
                     CHECKSUM,
                     VERIFY,
                     STATS = 10,
                     DESCRIPTION = 'Transaction log backup of $DatabaseName - $timestamp'
"@
            }
        }

        # Execute backup
        Invoke-Sqlcmd -ServerInstance $InstanceName -Query $backupQuery -QueryTimeout 0

        # Verify backup
        $verifyQuery = "RESTORE VERIFYONLY FROM DISK = '$backupFilePath'"
        Invoke-Sqlcmd -ServerInstance $InstanceName -Query $verifyQuery

        Write-BackupLog "Successfully completed $BackupType backup for $DatabaseName"

        # Clean up old backups (keep 7 days)
        $cleanupDate = (Get-Date).AddDays(-7)
        Get-ChildItem -Path $BackupPath -Filter "${DatabaseName}_${BackupType}_*.bak" |
            Where-Object { $_.CreationTime -lt $cleanupDate } |
            Remove-Item -Force

        return $backupFilePath

    } catch {
        Write-BackupLog "Backup failed for database $DatabaseName : $($_.Exception.Message)" "ERROR"
        throw
    }
}

# Function to test backup restoration
function Test-BackupRestore {
    param([string]$BackupFilePath, [string]$DatabaseName)

    $testDBName = "${DatabaseName}_RestoreTest"

    try {
        Write-BackupLog "Testing restore of backup: $BackupFilePath"

        # Drop test database if exists
        $dropQuery = @"
        IF EXISTS (SELECT name FROM sys.databases WHERE name = '$testDBName')
        BEGIN
            ALTER DATABASE [$testDBName] SET SINGLE_USER WITH ROLLBACK IMMEDIATE
            DROP DATABASE [$testDBName]
        END
"@
        Invoke-Sqlcmd -ServerInstance $InstanceName -Query $dropQuery

        # Restore backup to test database
        $restoreQuery = @"
        RESTORE DATABASE [$testDBName]
        FROM DISK = '$BackupFilePath'
        WITH MOVE '${DatabaseName}' TO 'C:\Data\${testDBName}.mdf',
             MOVE '${DatabaseName}_Log' TO 'C:\Data\${testDBName}_Log.ldf',
             REPLACE,
             CHECKDB,
             VERIFY
"@
        Invoke-Sqlcmd -ServerInstance $InstanceName -Query $restoreQuery -QueryTimeout 0

        # Run DBCC CHECKDB on restored database
        $checkQuery = "DBCC CHECKDB('$testDBName') WITH NO_INFOMSGS"
        Invoke-Sqlcmd -ServerInstance $InstanceName -Query $checkQuery

        # Drop test database
        Invoke-Sqlcmd -ServerInstance $InstanceName -Query "DROP DATABASE [$testDBName]"

        Write-BackupLog "Backup restore test successful for: $BackupFilePath"
        return $true

    } catch {
        Write-BackupLog "Backup restore test failed: $($_.Exception.Message)" "ERROR"
        return $false
    }
}

# Main backup execution
try {
    Write-BackupLog "Starting automated backup process"

    # Get list of databases to backup (exclude system databases)
    $databases = Invoke-Sqlcmd -ServerInstance $InstanceName -Query @"
        SELECT name FROM sys.databases
        WHERE name NOT IN ('master', 'model', 'msdb', 'tempdb')
        AND state = 0  -- ONLINE
        AND is_read_only = 0
"@

    foreach ($db in $databases) {
        $dbName = $db.name

        # Full backup on Sunday, differential backup on other days
        if ((Get-Date).DayOfWeek -eq "Sunday") {
            $backupPath = Backup-Database -DatabaseName $dbName -BackupType "FULL"
            Test-BackupRestore -BackupFilePath $backupPath -DatabaseName $dbName
        } else {
            Backup-Database -DatabaseName $dbName -BackupType "DIFF"
        }

        # Transaction log backup every 15 minutes (if full recovery model)
        $recoveryModel = Invoke-Sqlcmd -ServerInstance $InstanceName -Query @"
            SELECT recovery_model_desc FROM sys.databases WHERE name = '$dbName'
"@

        if ($recoveryModel.recovery_model_desc -eq "FULL") {
            Backup-Database -DatabaseName $dbName -BackupType "LOG"
        }
    }

    Write-BackupLog "Automated backup process completed successfully"

} catch {
    Write-BackupLog "Automated backup process failed: $($_.Exception.Message)" "ERROR"
    exit 1
}
```

### MySQL Disaster Recovery

#### MySQL Master-Slave with GTID
```bash
#!/bin/bash
# MySQL Master-Slave Replication with GTID Setup

# Configuration variables
MASTER_HOST="mysql-master.company.com"
SLAVE_HOST="mysql-slave.company.com"
REPLICATION_USER="repl_user"
REPLICATION_PASSWORD="SecureReplPassword123"

setup_mysql_gtid_replication() {
    echo "=== Setting up MySQL GTID Replication ==="

    # Configure master server
    configure_mysql_master

    # Configure slave server
    configure_mysql_slave

    # Start replication
    start_gtid_replication

    # Verify replication
    verify_replication_status
}

configure_mysql_master() {
    echo "Configuring MySQL master server..."

    # Create MySQL configuration for master
    cat > "/tmp/master.cnf" << EOF
[mysqld]
# Server identification
server-id = 1

# Binary logging
log-bin = mysql-bin
binlog-format = ROW
binlog-row-image = FULL

# GTID configuration
gtid-mode = ON
enforce-gtid-consistency = ON
log-slave-updates = ON

# Binary log retention
expire_logs_days = 7
max_binlog_size = 512M

# Replication settings
sync_binlog = 1
innodb_flush_log_at_trx_commit = 1

# Performance settings
innodb_buffer_pool_size = 4G
innodb_log_file_size = 512M
innodb_log_buffer_size = 64M

# Security
ssl_ca = /etc/mysql/certs/ca-cert.pem
ssl_cert = /etc/mysql/certs/server-cert.pem
ssl_key = /etc/mysql/certs/server-key.pem
EOF

    # Apply configuration to master
    scp /tmp/master.cnf root@$MASTER_HOST:/etc/mysql/mysql.conf.d/
    ssh root@$MASTER_HOST "systemctl restart mysql"

    # Wait for MySQL to start
    sleep 30

    # Create replication user
    mysql -h $MASTER_HOST -u root -p << SQL
CREATE USER IF NOT EXISTS '$REPLICATION_USER'@'%' IDENTIFIED BY '$REPLICATION_PASSWORD';
GRANT REPLICATION SLAVE ON *.* TO '$REPLICATION_USER'@'%';
GRANT REPLICATION CLIENT ON *.* TO '$REPLICATION_USER'@'%';
FLUSH PRIVILEGES;

-- Show master status
SHOW MASTER STATUS;
SHOW GLOBAL VARIABLES LIKE 'gtid_executed';
SQL

    echo "Master configuration completed"
}

configure_mysql_slave() {
    echo "Configuring MySQL slave server..."

    # Create MySQL configuration for slave
    cat > "/tmp/slave.cnf" << EOF
[mysqld]
# Server identification
server-id = 2

# Binary logging (for cascading replication)
log-bin = mysql-bin
binlog-format = ROW

# GTID configuration
gtid-mode = ON
enforce-gtid-consistency = ON
log-slave-updates = ON

# Relay log configuration
relay-log = relay-bin
relay-log-recovery = ON

# Read-only (can be changed for failover)
read-only = 1
super-read-only = 1

# Performance settings
innodb_buffer_pool_size = 2G
innodb_log_file_size = 256M

# Slave settings
slave-skip-errors = 1062,1032
slave-net-timeout = 60
slave-parallel-type = LOGICAL_CLOCK
slave-parallel-workers = 4

# Security
ssl_ca = /etc/mysql/certs/ca-cert.pem
ssl_cert = /etc/mysql/certs/server-cert.pem
ssl_key = /etc/mysql/certs/server-key.pem
EOF

    # Apply configuration to slave
    scp /tmp/slave.cnf root@$SLAVE_HOST:/etc/mysql/mysql.conf.d/
    ssh root@$SLAVE_HOST "systemctl restart mysql"

    # Wait for MySQL to start
    sleep 30

    echo "Slave configuration completed"
}

start_gtid_replication() {
    echo "Starting GTID-based replication..."

    # Configure slave to replicate from master
    mysql -h $SLAVE_HOST -u root -p << SQL
-- Stop any existing replication
STOP SLAVE;
RESET SLAVE ALL;

-- Configure master connection
CHANGE MASTER TO
    MASTER_HOST='$MASTER_HOST',
    MASTER_USER='$REPLICATION_USER',
    MASTER_PASSWORD='$REPLICATION_PASSWORD',
    MASTER_AUTO_POSITION=1,
    MASTER_SSL=1,
    MASTER_CONNECT_RETRY=10,
    MASTER_RETRY_COUNT=3;

-- Start replication
START SLAVE;

-- Show slave status
SHOW SLAVE STATUS\G
SQL

    echo "GTID replication started"
}

verify_replication_status() {
    echo "Verifying replication status..."

    # Check slave status
    mysql -h $SLAVE_HOST -u root -p << SQL
SELECT
    SLAVE_IO_RUNNING,
    SLAVE_SQL_RUNNING,
    SECONDS_BEHIND_MASTER,
    LAST_IO_ERROR,
    LAST_SQL_ERROR,
    RETRIEVED_GTID_SET,
    EXECUTED_GTID_SET
FROM performance_schema.replication_connection_status
JOIN performance_schema.replication_applier_status_by_worker USING (CHANNEL_NAME);
SQL

    # Test replication with sample data
    test_replication_functionality
}

test_replication_functionality() {
    echo "Testing replication functionality..."

    local test_db="replication_test"
    local timestamp=$(date +%s)

    # Create test on master
    mysql -h $MASTER_HOST -u root -p << SQL
CREATE DATABASE IF NOT EXISTS $test_db;
USE $test_db;
CREATE TABLE IF NOT EXISTS test_table (
    id INT AUTO_INCREMENT PRIMARY KEY,
    test_data VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
INSERT INTO test_table (test_data) VALUES ('Test data $timestamp');
SQL

    # Wait for replication
    sleep 10

    # Verify on slave
    local replicated_data=$(mysql -h $SLAVE_HOST -u root -p -e "SELECT test_data FROM $test_db.test_table WHERE test_data LIKE '%$timestamp%';" | tail -n 1)

    if [[ "$replicated_data" == *"$timestamp"* ]]; then
        echo "✓ Replication test successful"
    else
        echo "✗ Replication test failed"
        return 1
    fi

    # Cleanup
    mysql -h $MASTER_HOST -u root -p -e "DROP DATABASE $test_db;"
}

# MySQL automated failover script
mysql_automated_failover() {
    local master_host="$1"
    local slave_host="$2"
    local vip="$3"

    echo "=== MySQL Automated Failover ==="
    echo "Master: $master_host"
    echo "Slave: $slave_host"
    echo "VIP: $vip"

    # Check master health
    if ! mysql -h "$master_host" -u root -p -e "SELECT 1;" > /dev/null 2>&1; then
        echo "Master is down, initiating failover..."

        # Promote slave to master
        mysql -h "$slave_host" -u root -p << SQL
-- Stop slave processes
STOP SLAVE;

-- Reset slave configuration
RESET SLAVE ALL;

-- Enable writes
SET GLOBAL read_only = 0;
SET GLOBAL super_read_only = 0;

-- Create replication user for future slaves
CREATE USER IF NOT EXISTS '$REPLICATION_USER'@'%' IDENTIFIED BY '$REPLICATION_PASSWORD';
GRANT REPLICATION SLAVE ON *.* TO '$REPLICATION_USER'@'%';
FLUSH PRIVILEGES;
SQL

        # Move VIP to new master
        ssh root@"$master_host" "ip addr del $vip/24 dev eth0" 2>/dev/null || true
        ssh root@"$slave_host" "ip addr add $vip/24 dev eth0"
        ssh root@"$slave_host" "arping -c 3 -I eth0 $vip"

        echo "Failover completed. $slave_host is now the master."

        # Send notification
        send_failover_notification "MySQL" "$master_host" "$slave_host" "SUCCESS"
    else
        echo "Master is healthy, no failover needed."
    fi
}

# MySQL backup and recovery
mysql_backup_and_recovery() {
    local backup_type="$1"
    local database_name="$2"

    case "$backup_type" in
        "logical")
            mysql_logical_backup "$database_name"
            ;;
        "physical")
            mysql_physical_backup "$database_name"
            ;;
        "binlog")
            mysql_binlog_backup
            ;;
        *)
            echo "Invalid backup type. Use: logical, physical, or binlog"
            return 1
            ;;
    esac
}

mysql_logical_backup() {
    local database_name="$1"
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_file="/backup/mysql/${database_name}_logical_${timestamp}.sql"

    echo "Creating logical backup of $database_name..."

    # Create compressed logical backup
    mysqldump \
        --host="$MASTER_HOST" \
        --user=backup_user \
        --password="$BACKUP_PASSWORD" \
        --single-transaction \
        --routines \
        --triggers \
        --events \
        --gtid \
        --master-data=2 \
        --flush-logs \
        --databases "$database_name" | gzip > "${backup_file}.gz"

    if [ $? -eq 0 ]; then
        echo "✓ Logical backup completed: ${backup_file}.gz"

        # Test backup integrity
        zcat "${backup_file}.gz" | head -n 50 | grep -q "MySQL dump"
        if [ $? -eq 0 ]; then
            echo "✓ Backup integrity verified"
        else
            echo "✗ Backup integrity check failed"
            return 1
        fi
    else
        echo "✗ Logical backup failed"
        return 1
    fi
}

mysql_physical_backup() {
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_dir="/backup/mysql/physical_${timestamp}"

    echo "Creating physical backup using Percona XtraBackup..."

    # Create physical backup
    xtrabackup \
        --host="$MASTER_HOST" \
        --user=backup_user \
        --password="$BACKUP_PASSWORD" \
        --backup \
        --target-dir="$backup_dir" \
        --compress \
        --compress-threads=4 \
        --parallel=4

    if [ $? -eq 0 ]; then
        echo "✓ Physical backup completed: $backup_dir"

        # Prepare backup for restoration
        xtrabackup \
            --prepare \
            --target-dir="$backup_dir" \
            --decompress

        echo "✓ Backup prepared for restoration"
    else
        echo "✗ Physical backup failed"
        return 1
    fi
}

# Main execution
case "$1" in
    "setup")
        setup_mysql_gtid_replication
        ;;
    "failover")
        mysql_automated_failover "$2" "$3" "$4"
        ;;
    "backup")
        mysql_backup_and_recovery "$2" "$3"
        ;;
    *)
        echo "Usage: $0 {setup|failover|backup}"
        echo ""
        echo "Commands:"
        echo "  setup                           - Setup GTID replication"
        echo "  failover <master> <slave> <vip> - Execute failover"
        echo "  backup <type> <database>        - Create backup"
        exit 1
        ;;
esac
```

### PostgreSQL Disaster Recovery

#### PostgreSQL Streaming Replication with Hot Standby
```bash
#!/bin/bash
# PostgreSQL Streaming Replication Setup

MASTER_HOST="postgres-master.company.com"
STANDBY_HOST="postgres-standby.company.com"
POSTGRES_USER="postgres"
REPLICATION_USER="replicator"
DATA_DIR="/var/lib/postgresql/13/main"

setup_postgresql_streaming_replication() {
    echo "=== Setting up PostgreSQL Streaming Replication ==="

    # Configure master server
    configure_postgresql_master

    # Create base backup for standby
    create_base_backup

    # Configure standby server
    configure_postgresql_standby

    # Start replication
    start_postgresql_replication

    # Verify replication
    verify_postgresql_replication
}

configure_postgresql_master() {
    echo "Configuring PostgreSQL master server..."

    # Update postgresql.conf on master
    ssh postgres@$MASTER_HOST << 'EOF'
cat >> /etc/postgresql/13/main/postgresql.conf << CONFIG

# Replication settings
wal_level = replica
max_wal_senders = 10
max_replication_slots = 10
wal_keep_segments = 64
archive_mode = on
archive_command = 'cp %p /var/lib/postgresql/wal_archive/%f'

# Hot standby settings
hot_standby = on
hot_standby_feedback = on

# Performance settings
shared_buffers = 2GB
effective_cache_size = 6GB
wal_buffers = 64MB
checkpoint_completion_target = 0.9
checkpoint_timeout = 15min

# Logging
log_destination = 'stderr'
logging_collector = on
log_directory = 'pg_log'
log_filename = 'postgresql-%Y-%m-%d_%H%M%S.log'
log_replication_commands = on
log_checkpoints = on

CONFIG
EOF

    # Update pg_hba.conf for replication
    ssh postgres@$MASTER_HOST << 'EOF'
cat >> /etc/postgresql/13/main/pg_hba.conf << HBA_CONFIG

# Replication connections
host replication replicator 10.1.1.0/24 md5
host replication replicator 10.2.1.0/24 md5

HBA_CONFIG
EOF

    # Create replication user
    ssh postgres@$MASTER_HOST << EOF
sudo -u postgres psql << SQL
CREATE USER $REPLICATION_USER WITH REPLICATION LOGIN ENCRYPTED PASSWORD 'SecureReplPassword123';
SELECT pg_create_physical_replication_slot('standby_slot');
\q
SQL
EOF

    # Create WAL archive directory
    ssh postgres@$MASTER_HOST "mkdir -p /var/lib/postgresql/wal_archive && chown postgres:postgres /var/lib/postgresql/wal_archive"

    # Restart PostgreSQL to apply configuration
    ssh postgres@$MASTER_HOST "sudo systemctl restart postgresql"

    echo "Master configuration completed"
}

create_base_backup() {
    echo "Creating base backup for standby..."

    # Create base backup
    ssh postgres@$MASTER_HOST << EOF
sudo -u postgres pg_basebackup \
    -h $MASTER_HOST \
    -D /tmp/standby_backup \
    -U $REPLICATION_USER \
    -v \
    -P \
    -W \
    -R \
    -X stream
EOF

    # Transfer backup to standby server
    ssh postgres@$MASTER_HOST "sudo tar -czf /tmp/standby_backup.tar.gz -C /tmp standby_backup"
    scp postgres@$MASTER_HOST:/tmp/standby_backup.tar.gz /tmp/
    scp /tmp/standby_backup.tar.gz postgres@$STANDBY_HOST:/tmp/

    echo "Base backup creation completed"
}

configure_postgresql_standby() {
    echo "Configuring PostgreSQL standby server..."

    # Stop PostgreSQL on standby
    ssh postgres@$STANDBY_HOST "sudo systemctl stop postgresql"

    # Remove existing data directory and restore from backup
    ssh postgres@$STANDBY_HOST << EOF
sudo rm -rf $DATA_DIR/*
sudo tar -xzf /tmp/standby_backup.tar.gz -C /tmp/
sudo cp -R /tmp/standby_backup/* $DATA_DIR/
sudo chown -R postgres:postgres $DATA_DIR
EOF

    # Create recovery configuration
    ssh postgres@$STANDBY_HOST << EOF
sudo -u postgres cat > $DATA_DIR/recovery.conf << RECOVERY_CONFIG
standby_mode = 'on'
primary_conninfo = 'host=$MASTER_HOST port=5432 user=$REPLICATION_USER password=SecureReplPassword123 application_name=standby1'
primary_slot_name = 'standby_slot'
trigger_file = '/tmp/postgresql.trigger'
restore_command = 'cp /var/lib/postgresql/wal_archive/%f %p'
archive_cleanup_command = 'pg_archivecleanup /var/lib/postgresql/wal_archive %r'
RECOVERY_CONFIG
EOF

    # Update postgresql.conf for standby-specific settings
    ssh postgres@$STANDBY_HOST << 'EOF'
cat >> /etc/postgresql/13/main/postgresql.conf << CONFIG

# Standby-specific settings
hot_standby = on
max_standby_streaming_delay = 30s
max_standby_archive_delay = 60s
wal_receiver_status_interval = 10s
hot_standby_feedback = on

CONFIG
EOF

    echo "Standby configuration completed"
}

start_postgresql_replication() {
    echo "Starting PostgreSQL replication..."

    # Start PostgreSQL on standby
    ssh postgres@$STANDBY_HOST "sudo systemctl start postgresql"

    # Wait for replication to start
    sleep 10

    echo "PostgreSQL replication started"
}

verify_postgresql_replication() {
    echo "Verifying PostgreSQL replication..."

    # Check replication status on master
    echo "Master replication status:"
    ssh postgres@$MASTER_HOST << 'EOF'
sudo -u postgres psql << SQL
SELECT
    client_addr,
    application_name,
    state,
    sent_lsn,
    write_lsn,
    flush_lsn,
    replay_lsn,
    write_lag,
    flush_lag,
    replay_lag
FROM pg_stat_replication;
\q
SQL
EOF

    # Check standby status
    echo "Standby status:"
    ssh postgres@$STANDBY_HOST << 'EOF'
sudo -u postgres psql << SQL
SELECT
    pg_is_in_recovery(),
    pg_last_wal_receive_lsn(),
    pg_last_wal_replay_lsn(),
    pg_last_xact_replay_timestamp();
\q
SQL
EOF

    # Test replication with sample data
    test_postgresql_replication
}

test_postgresql_replication() {
    echo "Testing PostgreSQL replication functionality..."

    local test_table="replication_test_$(date +%s)"

    # Create test data on master
    ssh postgres@$MASTER_HOST << EOF
sudo -u postgres psql << SQL
CREATE TABLE $test_table (
    id SERIAL PRIMARY KEY,
    test_data VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW()
);
INSERT INTO $test_table (test_data) VALUES ('Test replication data');
\q
SQL
EOF

    # Wait for replication
    sleep 5

    # Verify data on standby
    local replicated_count=$(ssh postgres@$STANDBY_HOST "sudo -u postgres psql -t -c \"SELECT COUNT(*) FROM $test_table;\"" | tr -d ' ')

    if [ "$replicated_count" -eq 1 ]; then
        echo "✓ Replication test successful"
    else
        echo "✗ Replication test failed"
        return 1
    fi

    # Cleanup
    ssh postgres@$MASTER_HOST "sudo -u postgres psql -c \"DROP TABLE $test_table;\""
}

# PostgreSQL automated failover
postgresql_automated_failover() {
    local master_host="$1"
    local standby_host="$2"
    local vip="$3"

    echo "=== PostgreSQL Automated Failover ==="

    # Check master health
    if ! ssh postgres@"$master_host" "sudo -u postgres pg_isready" > /dev/null 2>&1; then
        echo "Master is down, initiating failover..."

        # Promote standby to master
        ssh postgres@"$standby_host" << EOF
# Create trigger file to promote standby
sudo -u postgres touch /tmp/postgresql.trigger

# Wait for promotion to complete
sleep 30

# Verify promotion
sudo -u postgres psql -c "SELECT pg_is_in_recovery();"
EOF

        # Update application connection strings or VIP
        update_postgresql_vip "$standby_host" "$vip"

        echo "PostgreSQL failover completed. $standby_host is now the master."

        # Send notification
        send_failover_notification "PostgreSQL" "$master_host" "$standby_host" "SUCCESS"
    else
        echo "Master is healthy, no failover needed."
    fi
}

# PostgreSQL backup strategies
postgresql_backup_strategies() {
    local backup_type="$1"

    case "$backup_type" in
        "logical")
            postgresql_logical_backup
            ;;
        "physical")
            postgresql_physical_backup
            ;;
        "continuous")
            postgresql_continuous_archiving
            ;;
        *)
            echo "Invalid backup type. Use: logical, physical, or continuous"
            return 1
            ;;
    esac
}

postgresql_logical_backup() {
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_file="/backup/postgresql/logical_backup_${timestamp}.sql"

    echo "Creating PostgreSQL logical backup..."

    # Create logical backup using pg_dump
    ssh postgres@$MASTER_HOST << EOF
sudo -u postgres pg_dumpall \
    --clean \
    --if-exists \
    --verbose \
    --file="$backup_file"

# Compress backup
gzip "$backup_file"
EOF

    if [ $? -eq 0 ]; then
        echo "✓ Logical backup completed: ${backup_file}.gz"
    else
        echo "✗ Logical backup failed"
        return 1
    fi
}

postgresql_physical_backup() {
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_dir="/backup/postgresql/physical_${timestamp}"

    echo "Creating PostgreSQL physical backup..."

    # Create physical backup using pg_basebackup
    ssh postgres@$MASTER_HOST << EOF
sudo -u postgres pg_basebackup \
    -D "$backup_dir" \
    -Ft \
    -z \
    -P \
    -v \
    -X stream \
    -c fast
EOF

    if [ $? -eq 0 ]; then
        echo "✓ Physical backup completed: $backup_dir"
    else
        echo "✗ Physical backup failed"
        return 1
    fi
}

# Main execution
case "$1" in
    "setup")
        setup_postgresql_streaming_replication
        ;;
    "failover")
        postgresql_automated_failover "$2" "$3" "$4"
        ;;
    "backup")
        postgresql_backup_strategies "$2"
        ;;
    *)
        echo "Usage: $0 {setup|failover|backup}"
        echo ""
        echo "Commands:"
        echo "  setup                              - Setup streaming replication"
        echo "  failover <master> <standby> <vip>  - Execute failover"
        echo "  backup <type>                      - Create backup (logical/physical/continuous)"
        exit 1
        ;;
esac
```

## NoSQL Database Disaster Recovery

### MongoDB Replica Set DR

#### MongoDB Replica Set Configuration
```javascript
// MongoDB Replica Set Configuration for DR

// Initialize replica set
rs.initiate({
    _id: "prodReplicaSet",
    members: [
        {
            _id: 0,
            host: "mongo-primary.company.com:27017",
            priority: 10,
            tags: { "datacenter": "primary", "region": "east" }
        },
        {
            _id: 1,
            host: "mongo-secondary1.company.com:27017",
            priority: 5,
            tags: { "datacenter": "primary", "region": "east" }
        },
        {
            _id: 2,
            host: "mongo-secondary2.company.com:27017",
            priority: 5,
            tags: { "datacenter": "primary", "region": "east" }
        },
        {
            _id: 3,
            host: "mongo-dr1.company.com:27017",
            priority: 1,
            tags: { "datacenter": "dr", "region": "west" },
            hidden: true,
            votes: 1
        },
        {
            _id: 4,
            host: "mongo-dr2.company.com:27017",
            priority: 1,
            tags: { "datacenter": "dr", "region": "west" },
            hidden: true,
            votes: 1
        },
        {
            _id: 5,
            host: "mongo-arbiter.company.com:27017",
            arbiterOnly: true,
            priority: 0,
            votes: 1
        }
    ],
    settings: {
        chainingAllowed: false,
        heartbeatIntervalMillis: 2000,
        heartbeatTimeoutSecs: 10,
        electionTimeoutMillis: 10000,
        getLastErrorModes: {
            "majorityDataCenter": {
                "datacenter": 2
            }
        }
    }
});

// Configure read preferences for DR
db.getMongo().setReadPref("primaryPreferred", [
    { "datacenter": "primary" }
]);

// Configure write concern for durability
db.runCommand({
    setDefaultRWConcern: 1,
    defaultWriteConcern: {
        w: "majorityDataCenter",
        j: true,
        wtimeout: 30000
    }
});
```

This comprehensive Database Disaster Recovery document provides detailed implementation strategies for SQL Server, MySQL, PostgreSQL, and MongoDB disaster recovery, including replication setup, automated failover procedures, backup strategies, and monitoring configurations essential for enterprise database protection.