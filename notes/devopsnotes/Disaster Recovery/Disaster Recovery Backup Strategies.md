# Disaster Recovery Backup Strategies

**Backup Strategies** form the cornerstone of disaster recovery by ensuring data protection, availability, and recovery capabilities through comprehensive backup methodologies, storage solutions, and automated processes.

## Backup Fundamentals

### 3-2-1 Backup Rule

#### Traditional 3-2-1 Strategy
```
3-2-1 Backup Rule:
├── 3 copies of critical data
│   ├── 1 primary/production copy
│   └── 2 backup copies
├── 2 different storage media types
│   ├── Local storage (fast recovery)
│   └── Remote/cloud storage (offsite protection)
└── 1 offsite/air-gapped copy
    └── Geographic separation for disaster protection
```

#### Modern 3-2-1-1-0 Enhanced Rule
```
Enhanced 3-2-1-1-0 Rule:
├── 3 copies of data
├── 2 different media types
├── 1 offsite copy
├── 1 offline/immutable copy (ransomware protection)
└── 0 errors in backup verification
```

### Backup Types and Methods

#### Full Backup Strategy
```yaml
full_backup:
  description: "Complete copy of all selected data"

  advantages:
    - "Fastest recovery time"
    - "Complete data set in single backup"
    - "Simple restoration process"
    - "No dependency on other backups"

  disadvantages:
    - "Longest backup window"
    - "Highest storage requirements"
    - "Most network bandwidth usage"
    - "Higher costs for large datasets"

  best_practices:
    schedule: "Weekly or monthly for large datasets"
    storage: "Deduplicated storage to reduce space"
    verification: "Full restore test quarterly"
    retention: "3-12 months depending on requirements"

  implementation_example: |
    # Weekly full backup script
    #!/bin/bash
    BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
    BACKUP_DEST="/backup/full_backup_$BACKUP_DATE"

    # Create backup directory
    mkdir -p "$BACKUP_DEST"

    # Full backup of critical directories
    tar -czf "$BACKUP_DEST/system_full.tar.gz" \
        /var/lib/mysql \
        /etc \
        /home \
        /var/www

    # Verify backup integrity
    tar -tzf "$BACKUP_DEST/system_full.tar.gz" > /dev/null
    if [ $? -eq 0 ]; then
        echo "Full backup completed successfully: $BACKUP_DEST"
    else
        echo "Full backup failed verification"
        exit 1
    fi
```

#### Incremental Backup Strategy
```yaml
incremental_backup:
  description: "Backs up only files changed since last backup"

  advantages:
    - "Fastest backup process"
    - "Minimal storage requirements"
    - "Reduced network usage"
    - "Frequent backup schedules possible"

  disadvantages:
    - "Slower recovery process"
    - "Complex restoration (needs all incrementals)"
    - "Higher risk if backup chain breaks"
    - "More complex management"

  implementation_example: |
    #!/bin/bash
    # Daily incremental backup script
    BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
    LAST_BACKUP=$(find /backup -name "*.backup" -type f -printf '%T@ %p\n' | sort -n | tail -1 | cut -d' ' -f2-)

    # Incremental backup using rsync
    rsync -av --link-dest="$LAST_BACKUP" \
        /var/lib/mysql/ \
        /backup/incremental_$BACKUP_DATE/

    # Create backup marker
    touch "/backup/incremental_$BACKUP_DATE.backup"
```

#### Differential Backup Strategy
```yaml
differential_backup:
  description: "Backs up files changed since last full backup"

  advantages:
    - "Faster than full backup"
    - "Simpler recovery than incremental"
    - "Only needs full + latest differential"
    - "Good balance of speed and simplicity"

  disadvantages:
    - "Larger than incremental backups"
    - "Backup size grows over time"
    - "Still requires full backup as base"

  implementation_example: |
    #!/bin/bash
    # Daily differential backup script
    BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
    FULL_BACKUP_DATE=$(cat /backup/.last_full_backup)

    # Find files modified since last full backup
    find /var/lib/mysql /etc /home /var/www \
        -newer "/backup/full_backup_$FULL_BACKUP_DATE.marker" \
        -type f -print0 | \
    tar -czf "/backup/differential_$BACKUP_DATE.tar.gz" --null -T -
```

## Advanced Backup Technologies

### Snapshot-Based Backups

#### LVM Snapshots for Linux
```bash
#!/bin/bash
# LVM snapshot backup script

VOLUME_GROUP="vg_data"
LOGICAL_VOLUME="lv_mysql"
SNAPSHOT_NAME="snap_mysql_$(date +%Y%m%d_%H%M%S)"
SNAPSHOT_SIZE="5G"
MOUNT_POINT="/mnt/snapshot"

# Create LVM snapshot
echo "Creating LVM snapshot: $SNAPSHOT_NAME"
lvcreate -L$SNAPSHOT_SIZE -s -n $SNAPSHOT_NAME /dev/$VOLUME_GROUP/$LOGICAL_VOLUME

if [ $? -eq 0 ]; then
    echo "Snapshot created successfully"

    # Mount snapshot
    mkdir -p $MOUNT_POINT
    mount /dev/$VOLUME_GROUP/$SNAPSHOT_NAME $MOUNT_POINT

    # Backup from snapshot
    tar -czf "/backup/mysql_snapshot_$(date +%Y%m%d_%H%M%S).tar.gz" -C $MOUNT_POINT .

    # Cleanup
    umount $MOUNT_POINT
    lvremove -f /dev/$VOLUME_GROUP/$SNAPSHOT_NAME

    echo "Snapshot backup completed and cleaned up"
else
    echo "Failed to create snapshot"
    exit 1
fi
```

#### ZFS Snapshots
```bash
#!/bin/bash
# ZFS snapshot backup script

POOL_NAME="tank"
DATASET="tank/mysql"
SNAPSHOT_NAME="backup_$(date +%Y%m%d_%H%M%S)"
BACKUP_DEST="/backup/zfs"

# Create ZFS snapshot
echo "Creating ZFS snapshot: $DATASET@$SNAPSHOT_NAME"
zfs snapshot $DATASET@$SNAPSHOT_NAME

if [ $? -eq 0 ]; then
    # Send snapshot to backup location
    zfs send $DATASET@$SNAPSHOT_NAME | gzip > "$BACKUP_DEST/${SNAPSHOT_NAME}.gz"

    # Verify backup
    if [ $? -eq 0 ]; then
        echo "ZFS snapshot backup completed: $BACKUP_DEST/${SNAPSHOT_NAME}.gz"

        # Optional: Remove old snapshots (keep last 7 days)
        zfs list -t snapshot -o name,creation -s creation | \
        grep "^$DATASET@backup_" | \
        head -n -7 | \
        awk '{print $1}' | \
        xargs -I {} zfs destroy {}
    else
        echo "Failed to send snapshot"
        exit 1
    fi
else
    echo "Failed to create ZFS snapshot"
    exit 1
fi
```

### Database-Specific Backup Strategies

#### MySQL/MariaDB Backup Solutions
```bash
#!/bin/bash
# Comprehensive MySQL backup script

DB_USER="backup_user"
DB_PASS="secure_password"
BACKUP_DIR="/backup/mysql"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p "$BACKUP_DIR/$DATE"

# Full logical backup with mysqldump
echo "Starting MySQL full backup..."
mysqldump --user="$DB_USER" --password="$DB_PASS" \
    --single-transaction \
    --routines \
    --triggers \
    --events \
    --all-databases \
    --master-data=2 \
    --flush-logs | gzip > "$BACKUP_DIR/$DATE/full_backup.sql.gz"

# Binary log backup for point-in-time recovery
echo "Backing up binary logs..."
mysql --user="$DB_USER" --password="$DB_PASS" -e "FLUSH LOGS;"
cp /var/lib/mysql/mysql-bin.* "$BACKUP_DIR/$DATE/"

# Backup MySQL configuration
cp /etc/mysql/my.cnf "$BACKUP_DIR/$DATE/"

# Verify backup integrity
echo "Verifying backup integrity..."
gunzip -t "$BACKUP_DIR/$DATE/full_backup.sql.gz"
if [ $? -eq 0 ]; then
    echo "MySQL backup completed successfully: $BACKUP_DIR/$DATE"

    # Create restore script
    cat > "$BACKUP_DIR/$DATE/restore.sh" << 'EOF'
#!/bin/bash
# MySQL restore script
echo "Restoring MySQL backup..."
gunzip -c full_backup.sql.gz | mysql --user=root --password
echo "Restore completed. Don't forget to restore binary logs if needed."
EOF
    chmod +x "$BACKUP_DIR/$DATE/restore.sh"
else
    echo "Backup verification failed"
    exit 1
fi
```

#### PostgreSQL Backup Solutions
```bash
#!/bin/bash
# Comprehensive PostgreSQL backup script

PG_USER="postgres"
PG_HOST="localhost"
PG_PORT="5432"
BACKUP_DIR="/backup/postgresql"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p "$BACKUP_DIR/$DATE"

# Full cluster backup with pg_dumpall
echo "Starting PostgreSQL cluster backup..."
pg_dumpall -U "$PG_USER" -h "$PG_HOST" -p "$PG_PORT" \
    --clean --if-exists | gzip > "$BACKUP_DIR/$DATE/cluster_backup.sql.gz"

# Individual database backups
echo "Creating individual database backups..."
psql -U "$PG_USER" -h "$PG_HOST" -p "$PG_PORT" -t -c "SELECT datname FROM pg_database WHERE NOT datistemplate AND datname != 'postgres';" | \
while read db; do
    if [ -n "$db" ]; then
        echo "Backing up database: $db"
        pg_dump -U "$PG_USER" -h "$PG_HOST" -p "$PG_PORT" \
            --format=custom --compress=9 \
            "$db" > "$BACKUP_DIR/$DATE/${db}.dump"
    fi
done

# WAL archive backup for point-in-time recovery
echo "Backing up WAL files..."
WAL_DIR=$(psql -U "$PG_USER" -h "$PG_HOST" -p "$PG_PORT" -t -c "SHOW data_directory;" | tr -d ' ')/pg_wal
if [ -d "$WAL_DIR" ]; then
    cp "$WAL_DIR"/0* "$BACKUP_DIR/$DATE/" 2>/dev/null || true
fi

# Configuration backup
CONFIG_DIR=$(psql -U "$PG_USER" -h "$PG_HOST" -p "$PG_PORT" -t -c "SHOW data_directory;" | tr -d ' ')
cp "$CONFIG_DIR/postgresql.conf" "$BACKUP_DIR/$DATE/" 2>/dev/null || true
cp "$CONFIG_DIR/pg_hba.conf" "$BACKUP_DIR/$DATE/" 2>/dev/null || true

echo "PostgreSQL backup completed: $BACKUP_DIR/$DATE"
```

## Cloud Backup Strategies

### AWS Backup Implementation

#### Comprehensive AWS Backup Plan
```yaml
# AWS Backup plan configuration
Resources:
  BackupVault:
    Type: AWS::Backup::BackupVault
    Properties:
      BackupVaultName: ProductionBackupVault
      EncryptionKeyArn: !Ref BackupKMSKey
      AccessPolicy:
        Version: '2012-10-17'
        Statement:
          - Effect: Allow
            Principal:
              AWS: !Sub 'arn:aws:iam::${AWS::AccountId}:root'
            Action:
              - backup:*
            Resource: '*'

  BackupPlan:
    Type: AWS::Backup::BackupPlan
    Properties:
      BackupPlan:
        BackupPlanName: ComprehensiveBackupPlan
        BackupPlanRule:
          - RuleName: DailyBackups
            TargetBackupVault: !Ref BackupVault
            ScheduleExpression: 'cron(0 5 ? * * *)'
            StartWindowMinutes: 480
            CompletionWindowMinutes: 10080
            Lifecycle:
              MoveToColdStorageAfterDays: 30
              DeleteAfterDays: 365
            RecoveryPointTags:
              BackupType: Daily
              Environment: Production

          - RuleName: WeeklyBackups
            TargetBackupVault: !Ref BackupVault
            ScheduleExpression: 'cron(0 3 ? * SUN *)'
            StartWindowMinutes: 480
            CompletionWindowMinutes: 10080
            Lifecycle:
              MoveToColdStorageAfterDays: 7
              DeleteAfterDays: 2555  # 7 years
            RecoveryPointTags:
              BackupType: Weekly
              Environment: Production

  BackupSelection:
    Type: AWS::Backup::BackupSelection
    Properties:
      BackupPlanId: !Ref BackupPlan
      BackupSelection:
        SelectionName: ProductionResources
        IamRoleArn: !GetAtt BackupRole.Arn
        Resources:
          - !Sub 'arn:aws:ec2:${AWS::Region}:${AWS::AccountId}:volume/*'
          - !Sub 'arn:aws:rds:${AWS::Region}:${AWS::AccountId}:db:*'
          - !Sub 'arn:aws:dynamodb:${AWS::Region}:${AWS::AccountId}:table/*'
        Conditions:
          StringEquals:
            'aws:ResourceTag/BackupRequired': 'true'
```

#### AWS Backup Automation Script
```python
#!/usr/bin/env python3
"""
AWS Backup Management Script
Automates backup operations and monitoring
"""

import boto3
import json
import datetime
from typing import Dict, List

class AWSBackupManager:
    def __init__(self, region: str = 'us-west-2'):
        self.backup_client = boto3.client('backup', region_name=region)
        self.ec2_client = boto3.client('ec2', region_name=region)
        self.rds_client = boto3.client('rds', region_name=region)
        self.region = region

    def create_on_demand_backup(self, resource_arn: str, backup_vault: str) -> str:
        """Create an on-demand backup for a specific resource."""
        try:
            response = self.backup_client.start_backup_job(
                BackupVaultName=backup_vault,
                ResourceArn=resource_arn,
                IamRoleArn=f'arn:aws:iam::{self._get_account_id()}:role/aws-backup-default-service-role',
                StartWindowMinutes=60,
                CompleteWindowMinutes=120
            )
            return response['BackupJobId']
        except Exception as e:
            print(f"Failed to create backup for {resource_arn}: {str(e)}")
            return None

    def list_backup_jobs(self, days: int = 7) -> List[Dict]:
        """List backup jobs from the last N days."""
        end_date = datetime.datetime.now()
        start_date = end_date - datetime.timedelta(days=days)

        try:
            response = self.backup_client.list_backup_jobs(
                ByCreatedAfter=start_date,
                ByCreatedBefore=end_date
            )
            return response['BackupJobs']
        except Exception as e:
            print(f"Failed to list backup jobs: {str(e)}")
            return []

    def monitor_backup_status(self) -> Dict:
        """Monitor current backup job status."""
        jobs = self.list_backup_jobs(days=1)
        status_summary = {
            'COMPLETED': 0,
            'RUNNING': 0,
            'FAILED': 0,
            'ABORTED': 0
        }

        failed_jobs = []

        for job in jobs:
            state = job['State']
            status_summary[state] = status_summary.get(state, 0) + 1

            if state == 'FAILED':
                failed_jobs.append({
                    'JobId': job['BackupJobId'],
                    'ResourceArn': job.get('ResourceArn', 'Unknown'),
                    'StatusMessage': job.get('StatusMessage', 'No message')
                })

        return {
            'summary': status_summary,
            'failed_jobs': failed_jobs
        }

    def verify_backup_integrity(self, backup_vault: str) -> List[Dict]:
        """Verify backup integrity by attempting restore validation."""
        try:
            response = self.backup_client.list_recovery_points_by_backup_vault(
                BackupVaultName=backup_vault,
                ByCreatedAfter=datetime.datetime.now() - datetime.timedelta(days=1)
            )

            verified_backups = []
            for recovery_point in response['RecoveryPoints']:
                # Perform restore validation test
                validation_result = self._validate_recovery_point(recovery_point)
                verified_backups.append({
                    'RecoveryPointArn': recovery_point['RecoveryPointArn'],
                    'ResourceArn': recovery_point['ResourceArn'],
                    'IsValid': validation_result
                })

            return verified_backups
        except Exception as e:
            print(f"Failed to verify backup integrity: {str(e)}")
            return []

    def _validate_recovery_point(self, recovery_point: Dict) -> bool:
        """Validate a specific recovery point."""
        # Implementation would depend on resource type
        # This is a placeholder for actual validation logic
        return recovery_point['Status'] == 'COMPLETED'

    def _get_account_id(self) -> str:
        """Get current AWS account ID."""
        sts_client = boto3.client('sts')
        return sts_client.get_caller_identity()['Account']

# Usage example
if __name__ == "__main__":
    backup_manager = AWSBackupManager()

    # Monitor backup status
    status = backup_manager.monitor_backup_status()
    print(f"Backup Status Summary: {json.dumps(status, indent=2)}")

    # List recent backup jobs
    recent_jobs = backup_manager.list_backup_jobs()
    print(f"Found {len(recent_jobs)} backup jobs in the last 7 days")

    # Verify backup integrity
    verified = backup_manager.verify_backup_integrity('ProductionBackupVault')
    print(f"Verified {len(verified)} backups")
```

### Azure Backup Implementation

#### Azure Backup Configuration
```powershell
# Azure Backup PowerShell script
# Install required modules: Install-Module -Name Az

# Connect to Azure
Connect-AzAccount

# Variables
$resourceGroupName = "rg-backup-prod"
$recoveryServicesVaultName = "rsv-prod-backup"
$location = "East US"
$storageType = "GeoRedundant"

# Create Recovery Services Vault
$vault = New-AzRecoveryServicesVault -ResourceGroupName $resourceGroupName `
    -Name $recoveryServicesVaultName `
    -Location $location

# Set backup storage redundancy
Set-AzRecoveryServicesBackupProperty -Vault $vault `
    -BackupStorageRedundancy $storageType

# Configure backup policy for VMs
$policy = New-AzRecoveryServicesBackupProtectionPolicy `
    -Name "DailyVMBackupPolicy" `
    -WorkloadType "AzureVM" `
    -BackupManagementType "AzureVM" `
    -RetentionPolicy (New-AzRecoveryServicesBackupRetentionPolicyObject `
        -DailyRetention -DaysOfRetention 30) `
    -SchedulePolicy (New-AzRecoveryServicesBackupSchedulePolicyObject `
        -ScheduleRunFrequency "Daily" `
        -ScheduleRunTimes "02:00")

# Enable backup for specific VMs
$vmResourceGroup = "rg-production-vms"
$vmNames = @("web-server-01", "db-server-01", "app-server-01")

foreach ($vmName in $vmNames) {
    $vm = Get-AzVM -ResourceGroupName $vmResourceGroup -Name $vmName
    Enable-AzRecoveryServicesBackupProtection `
        -ResourceGroupName $vmResourceGroup `
        -Name $vmName `
        -Policy $policy `
        -VaultId $vault.ID

    Write-Output "Backup enabled for VM: $vmName"
}

# Configure SQL Server backup
$sqlPolicy = New-AzRecoveryServicesBackupProtectionPolicy `
    -Name "SQLServerBackupPolicy" `
    -WorkloadType "MSSQL" `
    -BackupManagementType "AzureWorkload" `
    -RetentionPolicy (New-AzRecoveryServicesBackupRetentionPolicyObject `
        -DailyRetention -DaysOfRetention 90) `
    -SchedulePolicy (New-AzRecoveryServicesBackupSchedulePolicyObject `
        -ScheduleRunFrequency "Daily" `
        -ScheduleRunTimes "01:00")

Write-Output "Azure Backup configuration completed"
```

## Backup Automation and Orchestration

### Comprehensive Backup Orchestration Script

#### Master Backup Controller
```bash
#!/bin/bash
# Master backup orchestration script
# Coordinates multiple backup strategies and validates results

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="$SCRIPT_DIR/backup.conf"
LOG_FILE="/var/log/backup/backup_$(date +%Y%m%d).log"
NOTIFICATION_EMAIL="admin@company.com"
SLACK_WEBHOOK_URL="${SLACK_WEBHOOK_URL:-}"

# Create log directory
mkdir -p "$(dirname "$LOG_FILE")"

# Logging function
log() {
    local level=$1
    shift
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [$level] $*" | tee -a "$LOG_FILE"
}

# Load configuration
if [[ -f "$CONFIG_FILE" ]]; then
    source "$CONFIG_FILE"
else
    log "ERROR" "Configuration file not found: $CONFIG_FILE"
    exit 1
fi

# Notification functions
send_email_notification() {
    local subject="$1"
    local body="$2"

    echo "$body" | mail -s "$subject" "$NOTIFICATION_EMAIL"
}

send_slack_notification() {
    local message="$1"
    local color="$2"

    if [[ -n "$SLACK_WEBHOOK_URL" ]]; then
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"attachments\":[{\"color\":\"$color\",\"text\":\"$message\"}]}" \
            "$SLACK_WEBHOOK_URL"
    fi
}

# Backup validation function
validate_backup() {
    local backup_file="$1"
    local backup_type="$2"

    log "INFO" "Validating backup: $backup_file"

    case "$backup_type" in
        "tar")
            if tar -tzf "$backup_file" >/dev/null 2>&1; then
                log "INFO" "Tar backup validation successful"
                return 0
            else
                log "ERROR" "Tar backup validation failed"
                return 1
            fi
            ;;
        "mysql")
            if gunzip -t "$backup_file" >/dev/null 2>&1; then
                log "INFO" "MySQL backup validation successful"
                return 0
            else
                log "ERROR" "MySQL backup validation failed"
                return 1
            fi
            ;;
        "postgresql")
            if pg_restore -l "$backup_file" >/dev/null 2>&1; then
                log "INFO" "PostgreSQL backup validation successful"
                return 0
            else
                log "ERROR" "PostgreSQL backup validation failed"
                return 1
            fi
            ;;
        *)
            log "WARN" "Unknown backup type for validation: $backup_type"
            return 0
            ;;
    esac
}

# Main backup execution
execute_backup_plan() {
    local plan_name="$1"
    local backup_scripts=("${@:2}")

    log "INFO" "Starting backup plan: $plan_name"

    local failed_backups=0
    local total_backups=${#backup_scripts[@]}

    for script in "${backup_scripts[@]}"; do
        log "INFO" "Executing backup script: $script"

        if [[ -x "$SCRIPT_DIR/$script" ]]; then
            if "$SCRIPT_DIR/$script"; then
                log "INFO" "Backup script completed successfully: $script"
            else
                log "ERROR" "Backup script failed: $script"
                ((failed_backups++))
            fi
        else
            log "ERROR" "Backup script not found or not executable: $script"
            ((failed_backups++))
        fi
    done

    # Report results
    local success_rate=$(( (total_backups - failed_backups) * 100 / total_backups ))

    if [[ $failed_backups -eq 0 ]]; then
        log "INFO" "All backups completed successfully for plan: $plan_name"
        send_slack_notification "✅ Backup plan '$plan_name' completed successfully" "good"
    else
        log "ERROR" "Backup plan '$plan_name' had $failed_backups/$total_backups failures"
        send_slack_notification "❌ Backup plan '$plan_name' had $failed_backups failures" "danger"
        send_email_notification "Backup Failures - $plan_name" \
            "Backup plan '$plan_name' completed with $failed_backups failures out of $total_backups total backups. Success rate: $success_rate%. Check logs: $LOG_FILE"
    fi

    return $failed_backups
}

# Cleanup old backups
cleanup_old_backups() {
    local retention_days="$1"
    local backup_dirs=("${@:2}")

    log "INFO" "Cleaning up backups older than $retention_days days"

    for backup_dir in "${backup_dirs[@]}"; do
        if [[ -d "$backup_dir" ]]; then
            find "$backup_dir" -type f -mtime +$retention_days -delete
            find "$backup_dir" -type d -empty -delete
            log "INFO" "Cleanup completed for: $backup_dir"
        else
            log "WARN" "Backup directory not found: $backup_dir"
        fi
    done
}

# Main execution
main() {
    log "INFO" "Starting comprehensive backup orchestration"

    local overall_exit_code=0

    # Execute daily backup plan
    if execute_backup_plan "daily" \
        "mysql_backup.sh" \
        "postgresql_backup.sh" \
        "file_backup.sh" \
        "config_backup.sh"; then
        log "INFO" "Daily backup plan completed successfully"
    else
        log "ERROR" "Daily backup plan had failures"
        overall_exit_code=1
    fi

    # Execute weekly backup plan (if today is Sunday)
    if [[ $(date +%u) -eq 7 ]]; then
        if execute_backup_plan "weekly" \
            "full_system_backup.sh" \
            "archive_backup.sh"; then
            log "INFO" "Weekly backup plan completed successfully"
        else
            log "ERROR" "Weekly backup plan had failures"
            overall_exit_code=1
        fi
    fi

    # Cleanup old backups
    cleanup_old_backups 30 \
        "/backup/mysql" \
        "/backup/postgresql" \
        "/backup/files" \
        "/backup/config"

    # Final status
    if [[ $overall_exit_code -eq 0 ]]; then
        log "INFO" "All backup operations completed successfully"
    else
        log "ERROR" "Some backup operations failed"
    fi

    exit $overall_exit_code
}

# Execute main function
main "$@"
```

This comprehensive Backup Strategies file provides detailed, practical guidance on implementing robust backup solutions across different technologies and environments, ensuring data protection and recovery capabilities for disaster recovery scenarios.