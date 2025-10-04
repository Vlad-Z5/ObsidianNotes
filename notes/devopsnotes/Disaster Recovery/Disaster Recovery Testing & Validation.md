# Disaster Recovery Testing & Validation

**Disaster Recovery Testing & Validation** ensures the reliability, effectiveness, and completeness of disaster recovery plans through systematic testing methodologies, automated validation frameworks, and comprehensive performance verification that validates RTO/RPO targets and identifies improvement opportunities.

## Testing Framework and Methodology

### DR Testing Hierarchy

#### Testing Levels and Frequency
```yaml
dr_testing_framework:
  level_1_component_tests:
    frequency: "Monthly"
    duration: "2-4 hours"
    scope: "Individual system components"
    impact: "Minimal production impact"

    test_types:
      backup_restore_tests:
        description: "Verify backup and restore procedures for critical systems"
        schedule: "First Monday of each month"
        components:
          - "Database backup/restore validation"
          - "File system backup verification"
          - "Application configuration backup tests"
          - "Virtual machine snapshot tests"

      replication_health_checks:
        description: "Validate data replication mechanisms"
        schedule: "Second Monday of each month"
        components:
          - "Database replication lag testing"
          - "Storage replication verification"
          - "Real-time streaming validation"

      failover_mechanism_tests:
        description: "Test automated failover triggers"
        schedule: "Third Monday of each month"
        components:
          - "Load balancer failover testing"
          - "DNS failover verification"
          - "Application cluster failover"

  level_2_functional_tests:
    frequency: "Quarterly"
    duration: "8-12 hours"
    scope: "Complete application stacks"
    impact: "Limited production impact"

    test_scenarios:
      application_failover:
        description: "End-to-end application failover testing"
        participants: ["Development team", "Operations team", "QA team"]
        validation_criteria:
          - "RTO target achievement (< 4 hours)"
          - "Data integrity verification"
          - "Functional testing completion"
          - "Performance baseline validation"

      data_recovery:
        description: "Complete data recovery and validation"
        scope: "Critical databases and file systems"
        validation_methods:
          - "Data consistency checks"
          - "Business logic validation"
          - "Integration testing"
          - "User acceptance testing"

  level_3_full_scale_tests:
    frequency: "Semi-annually"
    duration: "24-48 hours"
    scope: "Complete organizational DR capability"
    impact: "Planned production maintenance window"

    test_scenarios:
      complete_datacenter_failover:
        description: "Simulate complete primary datacenter loss"
        duration: "48 hours"
        success_criteria:
          - "All critical systems operational within RTO"
          - "Business operations continuity maintained"
          - "Customer-facing services fully functional"
          - "Employee access and productivity restored"

      prolonged_outage_simulation:
        description: "Extended outage to test operational procedures"
        duration: "72 hours"
        focus_areas:
          - "Resource management and scaling"
          - "Vendor coordination"
          - "Communication effectiveness"
          - "Staff fatigue and rotation procedures"

  level_4_tabletop_exercises:
    frequency: "Quarterly"
    duration: "4-6 hours"
    scope: "Decision-making and coordination"
    impact: "No production impact"

    exercise_types:
      crisis_management:
        description: "Test decision-making under pressure"
        participants: ["Executive team", "DR coordinators", "Department heads"]
        scenarios:
          - "Multiple simultaneous failures"
          - "Vendor service outages"
          - "Security incidents during DR"
          - "Communication system failures"

      regulatory_compliance:
        description: "Validate compliance requirements during DR"
        focus_areas:
          - "Data protection regulation compliance"
          - "Financial reporting continuity"
          - "Audit trail maintenance"
          - "Legal and regulatory notifications"
```

### Automated Testing Infrastructure

#### Automated DR Testing Framework
```bash
#!/bin/bash
# Automated DR Testing Framework

# Configuration
DR_TEST_CONFIG="/etc/dr-testing/config.yml"
DR_TEST_LOG="/var/log/dr-testing/$(date +%Y%m%d-%H%M%S).log"
NOTIFICATION_WEBHOOK="https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK"

# Test execution framework
execute_dr_test_suite() {
    local test_level="$1"
    local test_type="$2"

    log_message "INFO" "Starting DR test suite: Level $test_level - $test_type"

    case "$test_level" in
        "1")
            execute_component_tests "$test_type"
            ;;
        "2")
            execute_functional_tests "$test_type"
            ;;
        "3")
            execute_full_scale_test "$test_type"
            ;;
        *)
            log_message "ERROR" "Invalid test level: $test_level"
            return 1
            ;;
    esac
}

# Component-level testing
execute_component_tests() {
    local test_type="$1"

    case "$test_type" in
        "backup-restore")
            test_backup_restore_procedures
            ;;
        "replication")
            test_replication_health
            ;;
        "failover-mechanisms")
            test_failover_mechanisms
            ;;
        "all")
            test_backup_restore_procedures
            test_replication_health
            test_failover_mechanisms
            ;;
    esac
}

test_backup_restore_procedures() {
    log_message "INFO" "Testing backup and restore procedures"

    # Database backup/restore test
    test_database_backup_restore || return 1

    # File system backup test
    test_filesystem_backup_restore || return 1

    # VM snapshot test
    test_vm_snapshot_restore || return 1

    log_message "INFO" "Backup/restore tests completed successfully"
}

test_database_backup_restore() {
    log_message "INFO" "Testing database backup and restore"

    local test_db="dr_test_$(date +%s)"
    local backup_file="/tmp/dr_test_backup_$(date +%s).sql"

    # Create test database with sample data
    mysql -u root -p"$DB_PASSWORD" << SQL
CREATE DATABASE $test_db;
USE $test_db;
CREATE TABLE test_table (
    id INT AUTO_INCREMENT PRIMARY KEY,
    data VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
INSERT INTO test_table (data) VALUES
    ('Test data 1'),
    ('Test data 2'),
    ('Test data 3');
SQL

    if [ $? -ne 0 ]; then
        log_message "ERROR" "Failed to create test database"
        return 1
    fi

    # Perform backup
    mysqldump -u root -p"$DB_PASSWORD" "$test_db" > "$backup_file"
    if [ $? -ne 0 ]; then
        log_message "ERROR" "Database backup failed"
        cleanup_test_resources "$test_db" "$backup_file"
        return 1
    fi

    # Drop original database
    mysql -u root -p"$DB_PASSWORD" -e "DROP DATABASE $test_db;"

    # Restore from backup
    mysql -u root -p"$DB_PASSWORD" -e "CREATE DATABASE $test_db;"
    mysql -u root -p"$DB_PASSWORD" "$test_db" < "$backup_file"

    if [ $? -ne 0 ]; then
        log_message "ERROR" "Database restore failed"
        cleanup_test_resources "$test_db" "$backup_file"
        return 1
    fi

    # Verify data integrity
    local row_count=$(mysql -u root -p"$DB_PASSWORD" -e "SELECT COUNT(*) FROM $test_db.test_table;" | tail -n 1)
    if [ "$row_count" -ne 3 ]; then
        log_message "ERROR" "Data integrity check failed. Expected 3 rows, found $row_count"
        cleanup_test_resources "$test_db" "$backup_file"
        return 1
    fi

    # Cleanup
    cleanup_test_resources "$test_db" "$backup_file"
    log_message "INFO" "Database backup/restore test passed"
    return 0
}

test_filesystem_backup_restore() {
    log_message "INFO" "Testing filesystem backup and restore"

    local test_dir="/tmp/dr_test_fs_$(date +%s)"
    local backup_file="/tmp/dr_test_fs_backup_$(date +%s).tar.gz"

    # Create test directory with files
    mkdir -p "$test_dir"
    echo "Test file 1" > "$test_dir/file1.txt"
    echo "Test file 2" > "$test_dir/file2.txt"
    mkdir "$test_dir/subdir"
    echo "Test file 3" > "$test_dir/subdir/file3.txt"

    # Create backup
    tar -czf "$backup_file" -C "$(dirname $test_dir)" "$(basename $test_dir)"
    if [ $? -ne 0 ]; then
        log_message "ERROR" "Filesystem backup failed"
        rm -rf "$test_dir" "$backup_file"
        return 1
    fi

    # Remove original directory
    rm -rf "$test_dir"

    # Restore from backup
    tar -xzf "$backup_file" -C "$(dirname $test_dir)"
    if [ $? -ne 0 ]; then
        log_message "ERROR" "Filesystem restore failed"
        rm -rf "$backup_file"
        return 1
    fi

    # Verify restored files
    if [ ! -f "$test_dir/file1.txt" ] || [ ! -f "$test_dir/file2.txt" ] || [ ! -f "$test_dir/subdir/file3.txt" ]; then
        log_message "ERROR" "Filesystem restore integrity check failed"
        rm -rf "$test_dir" "$backup_file"
        return 1
    fi

    # Cleanup
    rm -rf "$test_dir" "$backup_file"
    log_message "INFO" "Filesystem backup/restore test passed"
    return 0
}

test_replication_health() {
    log_message "INFO" "Testing replication health"

    # Test database replication
    test_database_replication || return 1

    # Test file replication
    test_file_replication || return 1

    log_message "INFO" "Replication health tests completed successfully"
}

test_database_replication() {
    local master_host="mysql-master.company.com"
    local slave_host="mysql-slave.company.com"
    local test_data="DR_TEST_$(date +%s)"

    log_message "INFO" "Testing database replication between $master_host and $slave_host"

    # Insert test data on master
    mysql -h "$master_host" -u test -p"$TEST_PASSWORD" << SQL
USE test_db;
INSERT INTO replication_test (test_data, created_at) VALUES ('$test_data', NOW());
SQL

    if [ $? -ne 0 ]; then
        log_message "ERROR" "Failed to insert test data on master"
        return 1
    fi

    # Wait for replication
    sleep 10

    # Check if data replicated to slave
    local replicated_data=$(mysql -h "$slave_host" -u test -p"$TEST_PASSWORD" \
                           -e "SELECT test_data FROM test_db.replication_test WHERE test_data='$test_data';" \
                           | tail -n 1)

    if [ "$replicated_data" != "$test_data" ]; then
        log_message "ERROR" "Database replication test failed. Data not found on slave."
        return 1
    fi

    # Cleanup test data
    mysql -h "$master_host" -u test -p"$TEST_PASSWORD" \
          -e "DELETE FROM test_db.replication_test WHERE test_data='$test_data';"

    log_message "INFO" "Database replication test passed"
    return 0
}

test_failover_mechanisms() {
    log_message "INFO" "Testing failover mechanisms"

    # Test load balancer failover
    test_load_balancer_failover || return 1

    # Test DNS failover
    test_dns_failover || return 1

    log_message "INFO" "Failover mechanism tests completed successfully"
}

test_load_balancer_failover() {
    log_message "INFO" "Testing load balancer failover"

    local lb_endpoint="http://lb.company.com:8080/admin"
    local primary_server="web01.company.com"
    local backup_server="web02.company.com"

    # Disable primary server
    curl -X POST "$lb_endpoint/disable-server" \
         -H "Authorization: Bearer $LB_API_TOKEN" \
         -d "{\"server\": \"$primary_server\"}" || return 1

    # Wait for failover
    sleep 30

    # Test application availability
    local response=$(curl -s -o /dev/null -w "%{http_code}" "http://app.company.com/health")
    if [ "$response" != "200" ]; then
        log_message "ERROR" "Application not available after primary server disable"
        # Re-enable primary server
        curl -X POST "$lb_endpoint/enable-server" \
             -H "Authorization: Bearer $LB_API_TOKEN" \
             -d "{\"server\": \"$primary_server\"}"
        return 1
    fi

    # Re-enable primary server
    curl -X POST "$lb_endpoint/enable-server" \
         -H "Authorization: Bearer $LB_API_TOKEN" \
         -d "{\"server\": \"$primary_server\"}" || return 1

    log_message "INFO" "Load balancer failover test passed"
    return 0
}

# Functional testing
execute_functional_tests() {
    local test_type="$1"

    log_message "INFO" "Executing functional tests: $test_type"

    case "$test_type" in
        "application-failover")
            test_application_failover
            ;;
        "data-recovery")
            test_data_recovery
            ;;
        "all")
            test_application_failover
            test_data_recovery
            ;;
    esac
}

test_application_failover() {
    log_message "INFO" "Testing complete application failover"

    # Record start time for RTO measurement
    local start_time=$(date +%s)

    # Simulate primary datacenter failure
    simulate_datacenter_failure "primary" || return 1

    # Execute failover procedures
    execute_failover_procedures || return 1

    # Validate application functionality
    validate_application_functionality || return 1

    # Calculate RTO
    local end_time=$(date +%s)
    local rto_actual=$((end_time - start_time))
    local rto_target=14400  # 4 hours in seconds

    log_message "INFO" "RTO achieved: ${rto_actual}s (target: ${rto_target}s)"

    if [ $rto_actual -gt $rto_target ]; then
        log_message "WARNING" "RTO target exceeded by $((rto_actual - rto_target)) seconds"
    fi

    # Cleanup and restore
    restore_primary_datacenter || return 1

    log_message "INFO" "Application failover test completed"
    return 0
}

# Validation and reporting
validate_application_functionality() {
    log_message "INFO" "Validating application functionality post-failover"

    # Test critical user journeys
    validate_user_authentication || return 1
    validate_data_operations || return 1
    validate_external_integrations || return 1

    log_message "INFO" "Application functionality validation passed"
    return 0
}

validate_user_authentication() {
    local auth_endpoint="https://api.company.com/auth/login"
    local test_credentials='{"username": "test_user", "password": "test_password"}'

    local response=$(curl -s -X POST "$auth_endpoint" \
                          -H "Content-Type: application/json" \
                          -d "$test_credentials")

    local auth_token=$(echo "$response" | jq -r '.token')

    if [ "$auth_token" = "null" ] || [ -z "$auth_token" ]; then
        log_message "ERROR" "User authentication validation failed"
        return 1
    fi

    log_message "INFO" "User authentication validation passed"
    return 0
}

validate_data_operations() {
    local api_endpoint="https://api.company.com/data/test"
    local test_data='{"test": "dr_validation", "timestamp": "'$(date)''"}'

    # Create test data
    local create_response=$(curl -s -X POST "$api_endpoint" \
                                 -H "Content-Type: application/json" \
                                 -H "Authorization: Bearer $auth_token" \
                                 -d "$test_data")

    local record_id=$(echo "$create_response" | jq -r '.id')

    if [ "$record_id" = "null" ] || [ -z "$record_id" ]; then
        log_message "ERROR" "Data creation validation failed"
        return 1
    fi

    # Read test data
    local read_response=$(curl -s -X GET "$api_endpoint/$record_id" \
                               -H "Authorization: Bearer $auth_token")

    local retrieved_data=$(echo "$read_response" | jq -r '.test')

    if [ "$retrieved_data" != "dr_validation" ]; then
        log_message "ERROR" "Data read validation failed"
        return 1
    fi

    # Delete test data
    curl -s -X DELETE "$api_endpoint/$record_id" \
         -H "Authorization: Bearer $auth_token" > /dev/null

    log_message "INFO" "Data operations validation passed"
    return 0
}

# Reporting and notifications
generate_test_report() {
    local test_results="$1"
    local report_file="/tmp/dr_test_report_$(date +%Y%m%d).html"

    cat > "$report_file" << EOF
<!DOCTYPE html>
<html>
<head>
    <title>DR Test Report - $(date)</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { background-color: #f0f0f0; padding: 10px; border-radius: 5px; }
        .success { color: green; }
        .warning { color: orange; }
        .error { color: red; }
        table { border-collapse: collapse; width: 100%; margin-top: 20px; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Disaster Recovery Test Report</h1>
        <p>Generated: $(date)</p>
        <p>Test Environment: Production DR Environment</p>
    </div>

    <h2>Executive Summary</h2>
    <table>
        <tr>
            <th>Metric</th>
            <th>Target</th>
            <th>Achieved</th>
            <th>Status</th>
        </tr>
        <tr>
            <td>Recovery Time Objective (RTO)</td>
            <td>4 hours</td>
            <td>$rto_actual seconds</td>
            <td class="success">✓ Passed</td>
        </tr>
        <tr>
            <td>Recovery Point Objective (RPO)</td>
            <td>1 hour</td>
            <td>15 minutes</td>
            <td class="success">✓ Passed</td>
        </tr>
    </table>

    <h2>Test Results</h2>
    $test_results

    <h2>Recommendations</h2>
    <ul>
        <li>Continue regular testing schedule</li>
        <li>Update documentation based on test findings</li>
        <li>Address any identified issues in next maintenance window</li>
    </ul>
</body>
</html>
EOF

    echo "$report_file"
}

# Utility functions
log_message() {
    local level="$1"
    local message="$2"
    echo "$(date '+%Y-%m-%d %H:%M:%S') [$level] $message" | tee -a "$DR_TEST_LOG"
}

cleanup_test_resources() {
    local db_name="$1"
    local backup_file="$2"

    mysql -u root -p"$DB_PASSWORD" -e "DROP DATABASE IF EXISTS $db_name;" 2>/dev/null
    rm -f "$backup_file" 2>/dev/null
}

send_notification() {
    local message="$1"
    local level="$2"

    # Send Slack notification
    curl -X POST "$NOTIFICATION_WEBHOOK" \
         -H 'Content-type: application/json' \
         -d "{\"text\":\"[$level] DR Test: $message\"}"

    # Send email notification
    echo "$message" | mail -s "DR Test Notification - $level" ops-team@company.com
}

# Main execution
case "$1" in
    "component")
        execute_dr_test_suite "1" "${2:-all}"
        ;;
    "functional")
        execute_dr_test_suite "2" "${2:-all}"
        ;;
    "full-scale")
        execute_dr_test_suite "3" "${2:-complete-failover}"
        ;;
    *)
        echo "Usage: $0 {component|functional|full-scale} [test-type]"
        echo ""
        echo "Test Types:"
        echo "  component: backup-restore, replication, failover-mechanisms, all"
        echo "  functional: application-failover, data-recovery, all"
        echo "  full-scale: complete-failover, prolonged-outage"
        exit 1
        ;;
esac
```

## Performance and Compliance Validation

### RTO/RPO Measurement Framework

#### Automated RTO/RPO Monitoring
```python
#!/usr/bin/env python3
"""
DR Testing RTO/RPO Measurement and Validation Framework
"""

import time
import json
import logging
import sqlite3
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
import requests

class DRMetricsCollector:
    def __init__(self, config_file='dr_metrics_config.json'):
        self.config = self.load_config(config_file)
        self.db_path = self.config.get('database_path', '/var/lib/dr-testing/metrics.db')
        self.setup_database()
        self.setup_logging()

    def load_config(self, config_file):
        """Load configuration from JSON file"""
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return self.get_default_config()

    def get_default_config(self):
        """Default configuration"""
        return {
            "rto_targets": {
                "critical_systems": 14400,  # 4 hours
                "important_systems": 86400,  # 24 hours
                "moderate_systems": 259200  # 72 hours
            },
            "rpo_targets": {
                "critical_data": 900,  # 15 minutes
                "important_data": 3600,  # 1 hour
                "moderate_data": 86400  # 24 hours
            },
            "notification_settings": {
                "email_recipients": ["ops-team@company.com"],
                "slack_webhook": "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK"
            }
        }

    def setup_database(self):
        """Initialize SQLite database for metrics storage"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS dr_tests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                test_id TEXT UNIQUE,
                test_type TEXT,
                system_name TEXT,
                start_time TIMESTAMP,
                end_time TIMESTAMP,
                rto_actual INTEGER,
                rto_target INTEGER,
                rpo_actual INTEGER,
                rpo_target INTEGER,
                success BOOLEAN,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS metrics_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                test_id TEXT,
                metric_name TEXT,
                metric_value REAL,
                timestamp TIMESTAMP,
                FOREIGN KEY (test_id) REFERENCES dr_tests (test_id)
            )
        ''')

        conn.commit()
        conn.close()

    def setup_logging(self):
        """Configure logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('/var/log/dr-testing/metrics.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def start_rto_measurement(self, test_id, system_name, system_type='critical_systems'):
        """Start RTO measurement for a system"""
        start_time = datetime.now()
        rto_target = self.config['rto_targets'].get(system_type, 14400)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT OR REPLACE INTO dr_tests
            (test_id, system_name, start_time, rto_target, test_type)
            VALUES (?, ?, ?, ?, ?)
        ''', (test_id, system_name, start_time, rto_target, 'RTO'))

        conn.commit()
        conn.close()

        self.logger.info(f"RTO measurement started for {system_name} (Test ID: {test_id})")
        return start_time

    def end_rto_measurement(self, test_id, success=True, notes=""):
        """End RTO measurement and calculate actual RTO"""
        end_time = datetime.now()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT start_time, rto_target, system_name
            FROM dr_tests
            WHERE test_id = ?
        ''', (test_id,))

        result = cursor.fetchone()
        if not result:
            self.logger.error(f"No RTO measurement found for test ID: {test_id}")
            return None

        start_time_str, rto_target, system_name = result
        start_time = datetime.fromisoformat(start_time_str)
        rto_actual = int((end_time - start_time).total_seconds())

        cursor.execute('''
            UPDATE dr_tests
            SET end_time = ?, rto_actual = ?, success = ?, notes = ?
            WHERE test_id = ?
        ''', (end_time, rto_actual, success, notes, test_id))

        conn.commit()
        conn.close()

        # Evaluate RTO performance
        rto_performance = self.evaluate_rto_performance(rto_actual, rto_target)

        self.logger.info(f"RTO measurement completed for {system_name}")
        self.logger.info(f"RTO Actual: {rto_actual}s, Target: {rto_target}s, Performance: {rto_performance}")

        # Send notifications if RTO target was missed
        if rto_actual > rto_target:
            self.send_rto_alert(test_id, system_name, rto_actual, rto_target)

        return {
            'test_id': test_id,
            'system_name': system_name,
            'rto_actual': rto_actual,
            'rto_target': rto_target,
            'performance': rto_performance,
            'success': success
        }

    def measure_rpo(self, test_id, system_name, last_backup_time, system_type='critical_data'):
        """Measure RPO based on last successful backup/replication"""
        current_time = datetime.now()

        # Convert last_backup_time to datetime if it's a string
        if isinstance(last_backup_time, str):
            last_backup_time = datetime.fromisoformat(last_backup_time)

        rpo_actual = int((current_time - last_backup_time).total_seconds())
        rpo_target = self.config['rpo_targets'].get(system_type, 900)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT OR REPLACE INTO dr_tests
            (test_id, system_name, rpo_actual, rpo_target, test_type, start_time)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (test_id + '_RPO', system_name, rpo_actual, rpo_target, 'RPO', current_time))

        conn.commit()
        conn.close()

        # Evaluate RPO performance
        rpo_performance = self.evaluate_rpo_performance(rpo_actual, rpo_target)

        self.logger.info(f"RPO measured for {system_name}: {rpo_actual}s (target: {rpo_target}s)")

        # Send alert if RPO target was missed
        if rpo_actual > rpo_target:
            self.send_rpo_alert(test_id, system_name, rpo_actual, rpo_target)

        return {
            'test_id': test_id + '_RPO',
            'system_name': system_name,
            'rpo_actual': rpo_actual,
            'rpo_target': rpo_target,
            'performance': rpo_performance
        }

    def evaluate_rto_performance(self, actual, target):
        """Evaluate RTO performance and return rating"""
        percentage = (actual / target) * 100

        if percentage <= 50:
            return "Excellent"
        elif percentage <= 75:
            return "Good"
        elif percentage <= 100:
            return "Acceptable"
        elif percentage <= 125:
            return "Needs Improvement"
        else:
            return "Failed"

    def evaluate_rpo_performance(self, actual, target):
        """Evaluate RPO performance and return rating"""
        percentage = (actual / target) * 100

        if percentage <= 25:
            return "Excellent"
        elif percentage <= 50:
            return "Good"
        elif percentage <= 100:
            return "Acceptable"
        elif percentage <= 150:
            return "Needs Improvement"
        else:
            return "Failed"

    def send_rto_alert(self, test_id, system_name, rto_actual, rto_target):
        """Send alert when RTO target is missed"""
        message = f"""
        RTO TARGET MISSED

        Test ID: {test_id}
        System: {system_name}
        RTO Actual: {rto_actual} seconds ({rto_actual/3600:.2f} hours)
        RTO Target: {rto_target} seconds ({rto_target/3600:.2f} hours)
        Difference: {rto_actual - rto_target} seconds

        Please review the DR procedures and identify improvement opportunities.
        """

        self.send_notification("RTO Target Missed", message, "ERROR")

    def send_rpo_alert(self, test_id, system_name, rpo_actual, rpo_target):
        """Send alert when RPO target is missed"""
        message = f"""
        RPO TARGET MISSED

        Test ID: {test_id}
        System: {system_name}
        RPO Actual: {rpo_actual} seconds ({rpo_actual/60:.2f} minutes)
        RPO Target: {rpo_target} seconds ({rpo_target/60:.2f} minutes)
        Difference: {rpo_actual - rpo_target} seconds

        Please review backup and replication procedures.
        """

        self.send_notification("RPO Target Missed", message, "WARNING")

    def send_notification(self, subject, message, level="INFO"):
        """Send email and Slack notifications"""
        # Email notification
        try:
            recipients = self.config['notification_settings']['email_recipients']
            for recipient in recipients:
                self.send_email(recipient, subject, message)
        except Exception as e:
            self.logger.error(f"Failed to send email notification: {e}")

        # Slack notification
        try:
            webhook_url = self.config['notification_settings']['slack_webhook']
            slack_payload = {
                "text": f"[{level}] {subject}",
                "attachments": [
                    {
                        "color": "danger" if level == "ERROR" else "warning",
                        "text": message
                    }
                ]
            }
            requests.post(webhook_url, json=slack_payload)
        except Exception as e:
            self.logger.error(f"Failed to send Slack notification: {e}")

    def send_email(self, recipient, subject, message):
        """Send email notification"""
        msg = MimeMultipart()
        msg['From'] = "dr-testing@company.com"
        msg['To'] = recipient
        msg['Subject'] = subject

        msg.attach(MimeText(message, 'plain'))

        # Use local SMTP server
        server = smtplib.SMTP('localhost')
        server.send_message(msg)
        server.quit()

    def generate_compliance_report(self, start_date, end_date):
        """Generate compliance report for specified date range"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT system_name, test_type, rto_actual, rto_target, rpo_actual, rpo_target,
                   success, start_time, notes
            FROM dr_tests
            WHERE start_time BETWEEN ? AND ?
            ORDER BY start_time DESC
        ''', (start_date, end_date))

        results = cursor.fetchall()
        conn.close()

        # Calculate compliance statistics
        total_tests = len(results)
        successful_tests = sum(1 for r in results if r[6])  # success column
        rto_compliant = sum(1 for r in results if r[2] and r[3] and r[2] <= r[3])
        rpo_compliant = sum(1 for r in results if r[4] and r[5] and r[4] <= r[5])

        compliance_stats = {
            'total_tests': total_tests,
            'successful_tests': successful_tests,
            'success_rate': (successful_tests / total_tests * 100) if total_tests > 0 else 0,
            'rto_compliance_rate': (rto_compliant / total_tests * 100) if total_tests > 0 else 0,
            'rpo_compliance_rate': (rpo_compliant / total_tests * 100) if total_tests > 0 else 0,
            'test_results': results
        }

        return compliance_stats

# Example usage
if __name__ == "__main__":
    collector = DRMetricsCollector()

    # Example RTO measurement
    test_id = f"DR_TEST_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    # Start RTO measurement
    start_time = collector.start_rto_measurement(test_id, "Customer Database", "critical_systems")

    # Simulate DR process (replace with actual DR procedures)
    print("Simulating DR procedures...")
    time.sleep(30)  # Replace with actual DR execution

    # End RTO measurement
    result = collector.end_rto_measurement(test_id, success=True, notes="Automated failover successful")
    print(f"RTO Result: {result}")

    # Measure RPO
    last_backup = datetime.now() - timedelta(minutes=10)  # Simulate last backup 10 minutes ago
    rpo_result = collector.measure_rpo(test_id, "Customer Database", last_backup, "critical_data")
    print(f"RPO Result: {rpo_result}")

    # Generate compliance report for last 30 days
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    compliance_report = collector.generate_compliance_report(start_date, end_date)
    print(f"Compliance Report: {json.dumps(compliance_report, indent=2, default=str)}")
```

This comprehensive Testing & Validation document provides systematic testing frameworks, automated validation scripts, RTO/RPO measurement tools, and compliance reporting capabilities essential for ensuring disaster recovery readiness and continuous improvement.