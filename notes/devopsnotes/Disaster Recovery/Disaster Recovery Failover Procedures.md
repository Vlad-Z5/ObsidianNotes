# Disaster Recovery Failover Procedures

**Disaster Recovery Failover Procedures** provide systematic, automated, and manual processes for transitioning critical systems from primary to secondary infrastructure during disasters, ensuring minimal downtime and data integrity throughout the recovery process.

## Failover Architecture Patterns

### Automated Failover Systems

#### Database Failover Automation
```yaml
automated_database_failover:
  sql_server_always_on:
    configuration:
      availability_group: "CriticalDataAG"
      failover_mode: "AUTOMATIC"
      health_check_timeout: "30000"  # 30 seconds
      failure_condition_level: "3"   # Moderate conditions

    automatic_failover_script: |
      -- Monitor primary replica health
      DECLARE @primary_health INT
      DECLARE @failover_threshold INT = 3

      WHILE 1 = 1
      BEGIN
          -- Check primary replica health
          SELECT @primary_health = COUNT(*)
          FROM sys.dm_hadr_availability_replica_states ars
          INNER JOIN sys.availability_replicas ar ON ars.replica_id = ar.replica_id
          WHERE ar.availability_group_id = (
              SELECT availability_group_id FROM sys.availability_groups WHERE name = 'CriticalDataAG'
          )
          AND ars.role = 1  -- Primary
          AND ars.connected_state = 1  -- Connected

          IF @primary_health = 0
          BEGIN
              -- Primary is down, initiate automatic failover
              PRINT 'Primary replica unavailable. Initiating automatic failover...'

              -- Force failover to secondary with data loss allowance in emergency
              ALTER AVAILABILITY GROUP CriticalDataAG FORCE_FAILOVER_ALLOW_DATA_LOSS

              BREAK
          END

          WAITFOR DELAY '00:00:30'  -- Check every 30 seconds
      END

    monitoring_integration: |
      # PowerShell monitoring script
      param(
          [string]$InstanceName = "SQLPROD01",
          [string]$AvailabilityGroup = "CriticalDataAG"
      )

      $connectionString = "Server=$InstanceName;Database=master;Integrated Security=true"

      while ($true) {
          try {
              $connection = New-Object System.Data.SqlClient.SqlConnection($connectionString)
              $connection.Open()

              $query = @"
                  SELECT
                      ar.replica_server_name,
                      ars.role_desc,
                      ars.connected_state_desc,
                      ars.synchronization_health_desc,
                      ars.last_connect_error_description
                  FROM sys.dm_hadr_availability_replica_states ars
                  INNER JOIN sys.availability_replicas ar ON ars.replica_id = ar.replica_id
                  INNER JOIN sys.availability_groups ag ON ar.availability_group_id = ag.group_id
                  WHERE ag.name = '$AvailabilityGroup'
              "@

              $command = New-Object System.Data.SqlClient.SqlCommand($query, $connection)
              $adapter = New-Object System.Data.SqlClient.SqlDataAdapter($command)
              $dataset = New-Object System.Data.DataSet
              $adapter.Fill($dataset)

              foreach ($row in $dataset.Tables[0].Rows) {
                  $replicaStatus = @{
                      Server = $row["replica_server_name"]
                      Role = $row["role_desc"]
                      ConnectionState = $row["connected_state_desc"]
                      SyncHealth = $row["synchronization_health_desc"]
                      LastError = $row["last_connect_error_description"]
                      Timestamp = Get-Date
                  }

                  # Send to monitoring system
                  Send-MonitoringAlert -Status $replicaStatus -AlertLevel "INFO"

                  # Check for failure conditions
                  if ($row["role_desc"] -eq "PRIMARY" -and $row["connected_state_desc"] -ne "CONNECTED") {
                      Send-MonitoringAlert -Status $replicaStatus -AlertLevel "CRITICAL"
                  }
              }

              $connection.Close()
          }
          catch {
              Write-Error "Failed to check AG status: $($_.Exception.Message)"
              Send-MonitoringAlert -Message "AG monitoring failed: $($_.Exception.Message)" -AlertLevel "ERROR"
          }

          Start-Sleep -Seconds 30
      }

  postgresql_streaming:
    automatic_promotion: |
      #!/bin/bash
      # PostgreSQL automatic failover script

      MASTER_HOST="postgres-master.company.com"
      STANDBY_HOST="postgres-standby.company.com"
      TRIGGER_FILE="/tmp/postgresql.trigger"
      CHECK_INTERVAL=10
      FAILURE_THRESHOLD=3

      failure_count=0

      monitor_master() {
          while true; do
              if pg_isready -h "$MASTER_HOST" -p 5432; then
                  echo "$(date): Master is healthy"
                  failure_count=0
              else
                  ((failure_count++))
                  echo "$(date): Master check failed. Failure count: $failure_count"

                  if [ $failure_count -ge $FAILURE_THRESHOLD ]; then
                      echo "$(date): Master failure threshold reached. Initiating failover..."
                      initiate_failover
                      break
                  fi
              fi

              sleep $CHECK_INTERVAL
          done
      }

      initiate_failover() {
          echo "$(date): Creating trigger file for standby promotion"

          # Create trigger file on standby to promote it
          ssh postgres@"$STANDBY_HOST" "touch $TRIGGER_FILE"

          # Wait for promotion to complete
          sleep 30

          # Verify new master is accepting connections
          if pg_isready -h "$STANDBY_HOST" -p 5432; then
              echo "$(date): Failover successful. New master: $STANDBY_HOST"

              # Update DNS or load balancer to point to new master
              update_dns_failover "$STANDBY_HOST"

              # Send notifications
              send_failover_notification "PostgreSQL" "$MASTER_HOST" "$STANDBY_HOST" "SUCCESS"
          else
              echo "$(date): Failover failed. New master not responding"
              send_failover_notification "PostgreSQL" "$MASTER_HOST" "$STANDBY_HOST" "FAILED"
          fi
      }

      update_dns_failover() {
          local new_master="$1"

          # Update Route53 DNS record
          aws route53 change-resource-record-sets \
              --hosted-zone-id Z1234567890 \
              --change-batch '{
                  "Changes": [{
                      "Action": "UPSERT",
                      "ResourceRecordSet": {
                          "Name": "postgres-master.company.com",
                          "Type": "A",
                          "TTL": 60,
                          "ResourceRecords": [{"Value": "'$(dig +short "$new_master")'"}]
                      }
                  }]
              }'

          echo "DNS updated to point to new master: $new_master"
      }

      # Start monitoring
      monitor_master

  mysql_master_slave:
    failover_automation: |
      #!/bin/bash
      # MySQL Master-Slave Automatic Failover

      MASTER_HOST="mysql-master.company.com"
      SLAVE_HOST="mysql-slave.company.com"
      MYSQL_USER="failover_user"
      MYSQL_PASSWORD="secure_password"
      VIP="10.1.1.100"

      check_master_health() {
          mysqladmin ping -h "$MASTER_HOST" -u "$MYSQL_USER" -p"$MYSQL_PASSWORD" > /dev/null 2>&1
          return $?
      }

      promote_slave_to_master() {
          echo "$(date): Promoting slave to master"

          # Stop slave replication
          mysql -h "$SLAVE_HOST" -u "$MYSQL_USER" -p"$MYSQL_PASSWORD" -e "STOP SLAVE;"

          # Reset slave configuration
          mysql -h "$SLAVE_HOST" -u "$MYSQL_USER" -p"$MYSQL_PASSWORD" -e "RESET SLAVE ALL;"

          # Enable writes on new master
          mysql -h "$SLAVE_HOST" -u "$MYSQL_USER" -p"$MYSQL_PASSWORD" -e "SET GLOBAL read_only = 0;"

          # Move VIP to new master
          move_vip "$SLAVE_HOST"

          echo "$(date): Slave promotion completed"
      }

      move_vip() {
          local new_master="$1"

          # Remove VIP from old master (if accessible)
          ssh root@"$MASTER_HOST" "ip addr del $VIP/24 dev eth0" 2>/dev/null || true

          # Add VIP to new master
          ssh root@"$new_master" "ip addr add $VIP/24 dev eth0"

          # Send gratuitous ARP
          ssh root@"$new_master" "arping -c 3 -I eth0 $VIP"

          echo "VIP $VIP moved to $new_master"
      }

      # Main monitoring loop
      failure_count=0
      while true; do
          if check_master_health; then
              failure_count=0
              echo "$(date): Master is healthy"
          else
              ((failure_count++))
              echo "$(date): Master health check failed ($failure_count/3)"

              if [ $failure_count -ge 3 ]; then
                  echo "$(date): Master failure confirmed. Initiating failover..."
                  promote_slave_to_master
                  break
              fi
          fi

          sleep 10
      done
```

### Load Balancer and Network Failover

#### HAProxy Automatic Failover Configuration
```yaml
haproxy_failover:
  configuration: |
    # HAProxy configuration with automatic failover
    global
        daemon
        maxconn 4096
        log 127.0.0.1:514 local0
        stats socket /var/run/haproxy.sock mode 600 level admin
        stats timeout 2m

    defaults
        mode http
        timeout connect 5000ms
        timeout client 50000ms
        timeout server 50000ms
        option httplog
        option dontlognull
        retries 3
        option redispatch

    # Frontend configuration
    frontend web_frontend
        bind *:80
        bind *:443 ssl crt /etc/ssl/certs/company.pem
        redirect scheme https if !{ ssl_fc }
        default_backend web_servers

    # Backend with health checks and failover
    backend web_servers
        balance roundrobin
        option httpchk GET /health
        http-check expect status 200

        # Primary data center servers
        server web1 10.1.1.10:8080 check inter 5s fall 3 rise 2 weight 100
        server web2 10.1.1.11:8080 check inter 5s fall 3 rise 2 weight 100
        server web3 10.1.1.12:8080 check inter 5s fall 3 rise 2 weight 100

        # DR data center servers (backup with lower weight)
        server dr-web1 10.2.1.10:8080 check inter 5s fall 3 rise 2 weight 50 backup
        server dr-web2 10.2.1.11:8080 check inter 5s fall 3 rise 2 weight 50 backup

    # Database backend with failover
    backend database_servers
        mode tcp
        balance leastconn
        option tcp-check

        server db-master 10.1.1.20:3306 check inter 10s fall 3 rise 2
        server db-slave 10.1.1.21:3306 check inter 10s fall 3 rise 2 backup

    # Stats interface
    listen stats
        bind *:8404
        stats enable
        stats uri /stats
        stats refresh 30s
        stats admin if TRUE

  health_check_script: |
    #!/bin/bash
    # Advanced health check script for HAProxy

    SERVICE_NAME="$1"
    SERVICE_PORT="$2"
    SERVICE_HOST="$3"

    case "$SERVICE_NAME" in
        "web")
            # HTTP health check with application-specific validation
            response=$(curl -s -o /dev/null -w "%{http_code}" "http://$SERVICE_HOST:$SERVICE_PORT/health")
            if [ "$response" = "200" ]; then
                # Additional check for database connectivity
                db_status=$(curl -s "http://$SERVICE_HOST:$SERVICE_PORT/health/db" | jq -r '.status')
                if [ "$db_status" = "healthy" ]; then
                    exit 0  # Healthy
                else
                    exit 1  # Database connection issue
                fi
            else
                exit 1  # HTTP health check failed
            fi
            ;;

        "database")
            # Database-specific health check
            if mysqladmin ping -h "$SERVICE_HOST" -P "$SERVICE_PORT" > /dev/null 2>&1; then
                # Check replication lag
                lag=$(mysql -h "$SERVICE_HOST" -P "$SERVICE_PORT" -e "SHOW SLAVE STATUS\G" | grep "Seconds_Behind_Master" | awk '{print $2}')
                if [ "$lag" -lt 60 ]; then
                    exit 0  # Healthy with acceptable lag
                else
                    exit 1  # Replication lag too high
                fi
            else
                exit 1  # Database not responding
            fi
            ;;
    esac

nginx_failover:
  upstream_configuration: |
    # NGINX upstream with failover
    upstream web_backend {
        # Primary servers
        server 10.1.1.10:8080 weight=3 max_fails=3 fail_timeout=30s;
        server 10.1.1.11:8080 weight=3 max_fails=3 fail_timeout=30s;
        server 10.1.1.12:8080 weight=3 max_fails=3 fail_timeout=30s;

        # Backup servers
        server 10.2.1.10:8080 weight=1 max_fails=3 fail_timeout=30s backup;
        server 10.2.1.11:8080 weight=1 max_fails=3 fail_timeout=30s backup;

        # Health check configuration
        keepalive 32;
    }

    upstream database_backend {
        server 10.1.1.20:3306 weight=10 max_fails=1 fail_timeout=10s;
        server 10.1.1.21:3306 weight=1 max_fails=1 fail_timeout=10s backup;
    }

    server {
        listen 80;
        listen 443 ssl http2;
        server_name company.com www.company.com;

        # SSL configuration
        ssl_certificate /etc/ssl/certs/company.crt;
        ssl_certificate_key /etc/ssl/private/company.key;

        location / {
            proxy_pass http://web_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;

            # Health check
            proxy_next_upstream error timeout invalid_header http_500 http_502 http_503 http_504;
            proxy_connect_timeout 5s;
            proxy_send_timeout 10s;
            proxy_read_timeout 10s;
        }

        location /health {
            access_log off;
            return 200 "healthy\n";
            add_header Content-Type text/plain;
        }
    }

  lua_health_check: |
    -- NGINX Lua health check script
    local http = require "resty.http"
    local json = require "cjson"

    local function check_backend_health()
        local httpc = http.new()
        local backends = {
            "http://10.1.1.10:8080/health",
            "http://10.1.1.11:8080/health",
            "http://10.1.1.12:8080/health"
        }

        local healthy_backends = 0
        local total_backends = #backends

        for _, backend_url in ipairs(backends) do
            local res, err = httpc:request_uri(backend_url, {
                method = "GET",
                timeout = 5000,
                keepalive = false
            })

            if res and res.status == 200 then
                healthy_backends = healthy_backends + 1
                ngx.log(ngx.INFO, "Backend healthy: " .. backend_url)
            else
                ngx.log(ngx.ERR, "Backend unhealthy: " .. backend_url .. " Error: " .. (err or "unknown"))
            end
        end

        local health_ratio = healthy_backends / total_backends

        if health_ratio < 0.5 then
            -- Less than 50% backends healthy - trigger DR
            ngx.log(ngx.CRIT, "Critical: Only " .. healthy_backends .. "/" .. total_backends .. " backends healthy")
            -- Trigger DR procedures
            trigger_dr_failover()
        end

        return health_ratio
    end

    local function trigger_dr_failover()
        -- Send signal to DR automation system
        local httpc = http.new()
        local res, err = httpc:request_uri("http://dr-controller.company.com:8080/trigger-failover", {
            method = "POST",
            body = json.encode({
                trigger_reason = "backend_health_critical",
                healthy_ratio = health_ratio,
                timestamp = ngx.time()
            }),
            headers = {
                ["Content-Type"] = "application/json",
                ["Authorization"] = "Bearer " .. os.getenv("DR_API_TOKEN")
            }
        })

        if res and res.status == 200 then
            ngx.log(ngx.INFO, "DR failover triggered successfully")
        else
            ngx.log(ngx.ERR, "Failed to trigger DR failover: " .. (err or "unknown"))
        end
    end

    -- Run health check
    check_backend_health()
```

## Manual Failover Procedures

### Step-by-Step Failover Processes

#### Web Application Failover Runbook
```bash
#!/bin/bash
# Manual Web Application Failover Runbook

# Global variables
PRIMARY_DC="NYC"
DR_DC="Chicago"
FAILOVER_LOG="/var/log/failover-$(date +%Y%m%d-%H%M%S).log"

# Logging function
log_message() {
    local level="$1"
    local message="$2"
    echo "$(date '+%Y-%m-%d %H:%M:%S') [$level] $message" | tee -a "$FAILOVER_LOG"
}

# Pre-failover validation
validate_dr_readiness() {
    log_message "INFO" "Starting DR readiness validation"

    # Check DR data center connectivity
    if ! ping -c 3 dr-gateway.company.com > /dev/null 2>&1; then
        log_message "ERROR" "DR data center not reachable"
        return 1
    fi

    # Validate database replication status
    local replication_lag=$(check_database_replication_lag)
    if [ "$replication_lag" -gt 300 ]; then
        log_message "WARNING" "Database replication lag is high: ${replication_lag}s"
        read -p "Continue with failover? (y/N): " continue_failover
        if [[ ! "$continue_failover" =~ ^[Yy]$ ]]; then
            log_message "INFO" "Failover aborted by operator"
            return 1
        fi
    fi

    # Check DR infrastructure status
    check_dr_infrastructure || return 1

    log_message "INFO" "DR readiness validation completed successfully"
    return 0
}

check_database_replication_lag() {
    local lag=$(mysql -h dr-database.company.com -u monitor -p"$DB_PASSWORD" \
        -e "SHOW SLAVE STATUS\G" | grep "Seconds_Behind_Master" | awk '{print $2}')
    echo "${lag:-999999}"  # Return high value if unable to determine
}

check_dr_infrastructure() {
    log_message "INFO" "Checking DR infrastructure components"

    local components=(
        "dr-web01.company.com:8080"
        "dr-web02.company.com:8080"
        "dr-database.company.com:3306"
        "dr-cache.company.com:6379"
        "dr-queue.company.com:5672"
    )

    local failed_components=()

    for component in "${components[@]}"; do
        local host=$(echo "$component" | cut -d: -f1)
        local port=$(echo "$component" | cut -d: -f2)

        if ! nc -z "$host" "$port" 2>/dev/null; then
            failed_components+=("$component")
            log_message "ERROR" "Component not responsive: $component"
        else
            log_message "INFO" "Component healthy: $component"
        fi
    done

    if [ ${#failed_components[@]} -gt 0 ]; then
        log_message "ERROR" "Failed components: ${failed_components[*]}"
        return 1
    fi

    return 0
}

# Main failover procedure
execute_web_failover() {
    log_message "INFO" "Starting web application failover from $PRIMARY_DC to $DR_DC"

    # Step 1: Validate readiness
    if ! validate_dr_readiness; then
        log_message "ERROR" "DR readiness validation failed. Aborting failover."
        return 1
    fi

    # Step 2: Stop traffic to primary
    log_message "INFO" "Step 2: Stopping traffic to primary data center"
    stop_primary_traffic || { log_message "ERROR" "Failed to stop primary traffic"; return 1; }

    # Step 3: Promote DR database to primary
    log_message "INFO" "Step 3: Promoting DR database to primary"
    promote_dr_database || { log_message "ERROR" "Database promotion failed"; return 1; }

    # Step 4: Update DNS and load balancer
    log_message "INFO" "Step 4: Updating DNS and load balancer configuration"
    update_dns_to_dr || { log_message "ERROR" "DNS update failed"; return 1; }

    # Step 5: Start DR application services
    log_message "INFO" "Step 5: Starting DR application services"
    start_dr_services || { log_message "ERROR" "Failed to start DR services"; return 1; }

    # Step 6: Validate failover success
    log_message "INFO" "Step 6: Validating failover success"
    validate_failover_success || { log_message "ERROR" "Failover validation failed"; return 1; }

    # Step 7: Notify stakeholders
    log_message "INFO" "Step 7: Notifying stakeholders"
    send_failover_notifications "SUCCESS"

    log_message "INFO" "Web application failover completed successfully"
    return 0
}

stop_primary_traffic() {
    # Update load balancer to drain primary servers
    curl -X POST "http://lb-manager.company.com/api/servers/drain" \
         -H "Authorization: Bearer $LB_API_TOKEN" \
         -d '{"datacenter": "NYC", "action": "drain"}' || return 1

    # Wait for connections to drain
    log_message "INFO" "Waiting 60 seconds for connection draining"
    sleep 60

    # Stop primary application servers
    ssh admin@web01.company.com "sudo systemctl stop nginx application"
    ssh admin@web02.company.com "sudo systemctl stop nginx application"

    return 0
}

promote_dr_database() {
    # Stop slave replication
    mysql -h dr-database.company.com -u admin -p"$DB_PASSWORD" \
          -e "STOP SLAVE;" || return 1

    # Reset slave configuration
    mysql -h dr-database.company.com -u admin -p"$DB_PASSWORD" \
          -e "RESET SLAVE ALL;" || return 1

    # Enable writes
    mysql -h dr-database.company.com -u admin -p"$DB_PASSWORD" \
          -e "SET GLOBAL read_only = 0;" || return 1

    log_message "INFO" "Database promoted successfully"
    return 0
}

update_dns_to_dr() {
    # Update DNS records to point to DR
    local dns_changes='
    {
        "Changes": [
            {
                "Action": "UPSERT",
                "ResourceRecordSet": {
                    "Name": "app.company.com",
                    "Type": "A",
                    "TTL": 60,
                    "ResourceRecords": [{"Value": "10.2.1.100"}]
                }
            },
            {
                "Action": "UPSERT",
                "ResourceRecordSet": {
                    "Name": "api.company.com",
                    "Type": "A",
                    "TTL": 60,
                    "ResourceRecords": [{"Value": "10.2.1.101"}]
                }
            }
        ]
    }'

    aws route53 change-resource-record-sets \
        --hosted-zone-id "$HOSTED_ZONE_ID" \
        --change-batch "$dns_changes" || return 1

    log_message "INFO" "DNS updated to point to DR data center"
    return 0
}

start_dr_services() {
    # Start application services on DR servers
    local dr_servers=("dr-web01.company.com" "dr-web02.company.com")

    for server in "${dr_servers[@]}"; do
        log_message "INFO" "Starting services on $server"

        ssh admin@"$server" << 'EOF'
sudo systemctl start redis
sudo systemctl start rabbitmq-server
sudo systemctl start application
sudo systemctl start nginx

# Verify services are running
sleep 10
sudo systemctl is-active --quiet redis application nginx
EOF

        if [ $? -ne 0 ]; then
            log_message "ERROR" "Failed to start services on $server"
            return 1
        fi
    done

    return 0
}

validate_failover_success() {
    # Test application endpoints
    local endpoints=(
        "https://app.company.com/health"
        "https://api.company.com/health"
        "https://app.company.com/api/status"
    )

    for endpoint in "${endpoints[@]}"; do
        local response=$(curl -s -o /dev/null -w "%{http_code}" "$endpoint")
        if [ "$response" != "200" ]; then
            log_message "ERROR" "Endpoint validation failed: $endpoint (HTTP $response)"
            return 1
        fi
        log_message "INFO" "Endpoint validated: $endpoint"
    done

    # Test database connectivity
    if ! mysql -h dr-database.company.com -u app -p"$APP_DB_PASSWORD" \
               -e "SELECT 1" > /dev/null 2>&1; then
        log_message "ERROR" "Database connectivity validation failed"
        return 1
    fi

    log_message "INFO" "All validation checks passed"
    return 0
}

send_failover_notifications() {
    local status="$1"
    local message="Web application failover to $DR_DC completed with status: $status"

    # Send email notification
    echo "$message" | mail -s "URGENT: Failover Completed - $status" ops-team@company.com

    # Send Slack notification
    curl -X POST "$SLACK_WEBHOOK_URL" \
         -H 'Content-type: application/json' \
         -d "{\"text\":\"🚨 $message\"}"

    # Send SMS to on-call personnel
    aws sns publish \
        --topic-arn "$SMS_TOPIC_ARN" \
        --message "$message"

    log_message "INFO" "Notifications sent"
}

# Rollback procedure
execute_failback() {
    log_message "INFO" "Starting failback procedure from $DR_DC to $PRIMARY_DC"

    # Verify primary datacenter is ready
    if ! validate_primary_readiness; then
        log_message "ERROR" "Primary datacenter not ready for failback"
        return 1
    fi

    # Sync data from DR to primary
    sync_data_to_primary || { log_message "ERROR" "Data sync failed"; return 1; }

    # Update DNS back to primary
    update_dns_to_primary || { log_message "ERROR" "DNS update failed"; return 1; }

    # Start primary services
    start_primary_services || { log_message "ERROR" "Failed to start primary services"; return 1; }

    # Stop DR services
    stop_dr_services || { log_message "WARNING" "Failed to cleanly stop DR services"; }

    log_message "INFO" "Failback completed successfully"
    send_failover_notifications "FAILBACK_SUCCESS"
}

# Main execution
case "$1" in
    "validate")
        validate_dr_readiness
        ;;
    "failover")
        execute_web_failover
        ;;
    "failback")
        execute_failback
        ;;
    *)
        echo "Usage: $0 {validate|failover|failback}"
        echo "  validate - Check DR readiness"
        echo "  failover - Execute failover to DR"
        echo "  failback - Execute failback to primary"
        exit 1
        ;;
esac
```

### Database Failover Procedures

#### MySQL Master-Slave Manual Failover
```bash
#!/bin/bash
# MySQL Master-Slave Manual Failover Procedure

MASTER_HOST="mysql-master.company.com"
SLAVE_HOST="mysql-slave.company.com"
VIP="10.1.1.100"
MYSQL_USER="admin"
MYSQL_PASSWORD="$DB_ADMIN_PASSWORD"

mysql_manual_failover() {
    echo "=== MySQL Manual Failover Procedure ==="
    echo "Master: $MASTER_HOST"
    echo "Slave: $SLAVE_HOST"
    echo "VIP: $VIP"

    # Step 1: Assess current replication status
    echo "Step 1: Checking current replication status"
    check_replication_status || exit 1

    # Step 2: Stop writes to master (if accessible)
    echo "Step 2: Stopping writes to master"
    stop_writes_to_master

    # Step 3: Ensure slave is caught up
    echo "Step 3: Ensuring slave is caught up"
    wait_for_slave_catchup || exit 1

    # Step 4: Promote slave to master
    echo "Step 4: Promoting slave to master"
    promote_slave_to_master || exit 1

    # Step 5: Update application configuration
    echo "Step 5: Updating application configuration"
    update_application_config || exit 1

    # Step 6: Move VIP to new master
    echo "Step 6: Moving VIP to new master"
    move_vip_to_new_master || exit 1

    # Step 7: Validate new master
    echo "Step 7: Validating new master"
    validate_new_master || exit 1

    echo "MySQL failover completed successfully!"
}

check_replication_status() {
    echo "Checking slave replication status..."

    local slave_status=$(mysql -h "$SLAVE_HOST" -u "$MYSQL_USER" -p"$MYSQL_PASSWORD" \
                        -e "SHOW SLAVE STATUS\G" 2>/dev/null)

    if [ $? -ne 0 ]; then
        echo "ERROR: Cannot connect to slave server"
        return 1
    fi

    local io_running=$(echo "$slave_status" | grep "Slave_IO_Running:" | awk '{print $2}')
    local sql_running=$(echo "$slave_status" | grep "Slave_SQL_Running:" | awk '{print $2}')
    local seconds_behind=$(echo "$slave_status" | grep "Seconds_Behind_Master:" | awk '{print $2}')

    echo "Slave_IO_Running: $io_running"
    echo "Slave_SQL_Running: $sql_running"
    echo "Seconds_Behind_Master: $seconds_behind"

    if [ "$io_running" != "Yes" ] || [ "$sql_running" != "Yes" ]; then
        echo "WARNING: Slave replication is not running properly"
        read -p "Continue with failover? (y/N): " continue_prompt
        if [[ ! "$continue_prompt" =~ ^[Yy]$ ]]; then
            return 1
        fi
    fi

    if [ "$seconds_behind" != "0" ] && [ "$seconds_behind" != "NULL" ]; then
        echo "WARNING: Slave is $seconds_behind seconds behind master"
    fi

    return 0
}

stop_writes_to_master() {
    echo "Attempting to stop writes to master..."

    # Try to set master to read-only
    if mysql -h "$MASTER_HOST" -u "$MYSQL_USER" -p"$MYSQL_PASSWORD" \
            -e "SET GLOBAL read_only = 1;" 2>/dev/null; then
        echo "Master set to read-only successfully"

        # Flush tables with read lock to ensure consistency
        mysql -h "$MASTER_HOST" -u "$MYSQL_USER" -p"$MYSQL_PASSWORD" \
              -e "FLUSH TABLES WITH READ LOCK;" 2>/dev/null

        echo "Tables locked on master"
    else
        echo "WARNING: Cannot connect to master - proceeding with emergency failover"
    fi
}

wait_for_slave_catchup() {
    echo "Waiting for slave to catch up with master..."

    local max_wait=300  # 5 minutes
    local wait_time=0

    while [ $wait_time -lt $max_wait ]; do
        local slave_status=$(mysql -h "$SLAVE_HOST" -u "$MYSQL_USER" -p"$MYSQL_PASSWORD" \
                            -e "SHOW SLAVE STATUS\G" 2>/dev/null)

        local seconds_behind=$(echo "$slave_status" | grep "Seconds_Behind_Master:" | awk '{print $2}')

        if [ "$seconds_behind" = "0" ] || [ "$seconds_behind" = "NULL" ]; then
            echo "Slave is caught up with master"
            return 0
        fi

        echo "Slave is still $seconds_behind seconds behind. Waiting..."
        sleep 10
        wait_time=$((wait_time + 10))
    done

    echo "WARNING: Slave did not catch up within $max_wait seconds"
    read -p "Continue with failover? (y/N): " continue_prompt
    if [[ "$continue_prompt" =~ ^[Yy]$ ]]; then
        return 0
    else
        return 1
    fi
}

promote_slave_to_master() {
    echo "Promoting slave to master..."

    # Stop slave processes
    mysql -h "$SLAVE_HOST" -u "$MYSQL_USER" -p"$MYSQL_PASSWORD" \
          -e "STOP SLAVE;" || return 1

    # Reset slave configuration
    mysql -h "$SLAVE_HOST" -u "$MYSQL_USER" -p"$MYSQL_PASSWORD" \
          -e "RESET SLAVE ALL;" || return 1

    # Enable writes on new master
    mysql -h "$SLAVE_HOST" -u "$MYSQL_USER" -p"$MYSQL_PASSWORD" \
          -e "SET GLOBAL read_only = 0;" || return 1

    # Create replication user for future slaves
    mysql -h "$SLAVE_HOST" -u "$MYSQL_USER" -p"$MYSQL_PASSWORD" << SQL
GRANT REPLICATION SLAVE ON *.* TO 'replication'@'%' IDENTIFIED BY '$REPLICATION_PASSWORD';
FLUSH PRIVILEGES;
SQL

    echo "Slave promoted to master successfully"
    return 0
}

update_application_config() {
    echo "Updating application configuration..."

    # Update database configuration in application servers
    local app_servers=("app01.company.com" "app02.company.com" "app03.company.com")

    for server in "${app_servers[@]}"; do
        echo "Updating configuration on $server"

        ssh admin@"$server" << EOF
# Backup current config
sudo cp /etc/app/database.conf /etc/app/database.conf.backup

# Update database host
sudo sed -i 's/host=mysql-master.company.com/host=mysql-slave.company.com/g' /etc/app/database.conf

# Restart application
sudo systemctl restart application

# Verify application is running
sleep 5
sudo systemctl is-active --quiet application
EOF

        if [ $? -ne 0 ]; then
            echo "ERROR: Failed to update configuration on $server"
            return 1
        fi
    done

    echo "Application configuration updated successfully"
    return 0
}

move_vip_to_new_master() {
    echo "Moving VIP from old master to new master..."

    # Remove VIP from old master (if accessible)
    ssh root@"$MASTER_HOST" "ip addr del $VIP/24 dev eth0" 2>/dev/null || echo "Could not remove VIP from old master"

    # Add VIP to new master
    ssh root@"$SLAVE_HOST" "ip addr add $VIP/24 dev eth0" || return 1

    # Send gratuitous ARP to update network
    ssh root@"$SLAVE_HOST" "arping -c 5 -I eth0 $VIP" || return 1

    echo "VIP moved successfully to new master"
    return 0
}

validate_new_master() {
    echo "Validating new master functionality..."

    # Test database connectivity
    if ! mysql -h "$VIP" -u "$MYSQL_USER" -p"$MYSQL_PASSWORD" \
              -e "SELECT 1;" > /dev/null 2>&1; then
        echo "ERROR: Cannot connect to new master via VIP"
        return 1
    fi

    # Test write capability
    local test_db="failover_test"
    local test_table="failover_validation"

    mysql -h "$VIP" -u "$MYSQL_USER" -p"$MYSQL_PASSWORD" << SQL
CREATE DATABASE IF NOT EXISTS $test_db;
USE $test_db;
CREATE TABLE IF NOT EXISTS $test_table (
    id INT AUTO_INCREMENT PRIMARY KEY,
    test_data VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
INSERT INTO $test_table (test_data) VALUES ('Failover test - $(date)');
SELECT * FROM $test_table ORDER BY id DESC LIMIT 1;
DROP TABLE $test_table;
DROP DATABASE $test_db;
SQL

    if [ $? -eq 0 ]; then
        echo "New master validation successful - reads and writes working"
        return 0
    else
        echo "ERROR: New master validation failed"
        return 1
    fi
}

# Recovery procedure for old master
recover_old_master_as_slave() {
    echo "=== Configuring old master as slave ==="

    local new_master="$SLAVE_HOST"
    local old_master="$MASTER_HOST"

    # Get master status from new master
    local master_status=$(mysql -h "$new_master" -u "$MYSQL_USER" -p"$MYSQL_PASSWORD" \
                         -e "SHOW MASTER STATUS\G")

    local log_file=$(echo "$master_status" | grep "File:" | awk '{print $2}')
    local log_pos=$(echo "$master_status" | grep "Position:" | awk '{print $2}')

    echo "New master log file: $log_file"
    echo "New master log position: $log_pos"

    # Configure old master as slave
    mysql -h "$old_master" -u "$MYSQL_USER" -p"$MYSQL_PASSWORD" << SQL
CHANGE MASTER TO
    MASTER_HOST='$new_master',
    MASTER_USER='replication',
    MASTER_PASSWORD='$REPLICATION_PASSWORD',
    MASTER_LOG_FILE='$log_file',
    MASTER_LOG_POS=$log_pos;

START SLAVE;
SHOW SLAVE STATUS\G;
SQL

    echo "Old master configured as slave to new master"
}

# Main execution
case "$1" in
    "failover")
        mysql_manual_failover
        ;;
    "recover-old-master")
        recover_old_master_as_slave
        ;;
    *)
        echo "Usage: $0 {failover|recover-old-master}"
        echo "  failover         - Execute MySQL failover procedure"
        echo "  recover-old-master - Configure old master as slave"
        exit 1
        ;;
esac
```

This comprehensive Failover Procedures document provides detailed automation scripts, manual procedures, monitoring configurations, and validation steps for executing reliable disaster recovery failovers across database, application, and infrastructure layers.