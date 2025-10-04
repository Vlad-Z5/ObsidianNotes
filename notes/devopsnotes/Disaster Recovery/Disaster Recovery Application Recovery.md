# Disaster Recovery Application Recovery

**Disaster Recovery Application Recovery** encompasses comprehensive strategies and automated procedures for restoring application services, maintaining session state, ensuring data consistency, and orchestrating complex multi-tier application recovery across distributed infrastructure during disaster scenarios.

## Application-Tier Recovery Strategies

### Stateless Application Recovery

#### Container-Based Application Recovery
```yaml
kubernetes_application_dr:
  deployment_strategy:
    cross_region_deployment:
      primary_cluster: "production-east"
      dr_cluster: "production-west"
      replication_strategy: "active-passive"

  application_manifests:
    web_tier_deployment: |
      apiVersion: apps/v1
      kind: Deployment
      metadata:
        name: web-app-deployment
        namespace: production
        labels:
          app: web-app
          tier: frontend
          environment: production
      spec:
        replicas: 6
        strategy:
          type: RollingUpdate
          rollingUpdate:
            maxSurge: 2
            maxUnavailable: 1
        selector:
          matchLabels:
            app: web-app
            tier: frontend
        template:
          metadata:
            labels:
              app: web-app
              tier: frontend
          spec:
            affinity:
              podAntiAffinity:
                preferredDuringSchedulingIgnoredDuringExecution:
                - weight: 100
                  podAffinityTerm:
                    labelSelector:
                      matchLabels:
                        app: web-app
                    topologyKey: kubernetes.io/hostname
            containers:
            - name: web-app
              image: company/web-app:v1.2.3
              ports:
              - containerPort: 8080
                name: http
              env:
              - name: DATABASE_URL
                valueFrom:
                  secretKeyRef:
                    name: database-credentials
                    key: url
              - name: REDIS_URL
                valueFrom:
                  configMapKeyRef:
                    name: redis-config
                    key: url
              - name: ENVIRONMENT
                value: "production"
              resources:
                requests:
                  cpu: 500m
                  memory: 1Gi
                limits:
                  cpu: 1000m
                  memory: 2Gi
              livenessProbe:
                httpGet:
                  path: /health
                  port: 8080
                initialDelaySeconds: 30
                periodSeconds: 10
                timeoutSeconds: 5
                failureThreshold: 3
              readinessProbe:
                httpGet:
                  path: /ready
                  port: 8080
                initialDelaySeconds: 5
                periodSeconds: 5
                timeoutSeconds: 3
                failureThreshold: 2
              volumeMounts:
              - name: app-config
                mountPath: /app/config
                readOnly: true
              - name: logs
                mountPath: /app/logs
            volumes:
            - name: app-config
              configMap:
                name: web-app-config
            - name: logs
              emptyDir: {}
            imagePullSecrets:
            - name: registry-credentials

    service_configuration: |
      apiVersion: v1
      kind: Service
      metadata:
        name: web-app-service
        namespace: production
        labels:
          app: web-app
          tier: frontend
      spec:
        selector:
          app: web-app
          tier: frontend
        ports:
        - name: http
          port: 80
          targetPort: 8080
          protocol: TCP
        type: ClusterIP
        sessionAffinity: None

    ingress_configuration: |
      apiVersion: networking.k8s.io/v1
      kind: Ingress
      metadata:
        name: web-app-ingress
        namespace: production
        annotations:
          kubernetes.io/ingress.class: nginx
          cert-manager.io/cluster-issuer: letsencrypt-prod
          nginx.ingress.kubernetes.io/rate-limit: "100"
          nginx.ingress.kubernetes.io/rate-limit-window: "1m"
          nginx.ingress.kubernetes.io/ssl-redirect: "true"
          nginx.ingress.kubernetes.io/force-ssl-redirect: "true"
      spec:
        tls:
        - hosts:
          - app.company.com
          secretName: web-app-tls
        rules:
        - host: app.company.com
          http:
            paths:
            - path: /
              pathType: Prefix
              backend:
                service:
                  name: web-app-service
                  port:
                    number: 80

  dr_automation:
    argocd_application: |
      apiVersion: argoproj.io/v1alpha1
      kind: Application
      metadata:
        name: web-app-dr
        namespace: argocd
      spec:
        project: production
        source:
          repoURL: https://github.com/company/k8s-manifests
          targetRevision: main
          path: applications/web-app/overlays/dr
        destination:
          server: https://dr-cluster-api.company.com
          namespace: production
        syncPolicy:
          automated:
            prune: true
            selfHeal: true
            allowEmpty: false
          syncOptions:
          - CreateNamespace=true
          - PrunePropagationPolicy=foreground
          - PruneLast=true
          retry:
            limit: 5
            backoff:
              duration: 5s
              factor: 2
              maxDuration: 3m

    failover_script: |
      #!/bin/bash
      # Kubernetes Application DR Failover Script

      PRIMARY_CLUSTER="production-east"
      DR_CLUSTER="production-west"
      NAMESPACE="production"
      APPLICATION="web-app"

      trigger_application_failover() {
          echo "=== Triggering Application Failover ==="
          echo "Primary Cluster: $PRIMARY_CLUSTER"
          echo "DR Cluster: $DR_CLUSTER"
          echo "Application: $APPLICATION"

          # Step 1: Scale down primary cluster deployment
          echo "Scaling down primary cluster deployment..."
          kubectl --context="$PRIMARY_CLUSTER" scale deployment "$APPLICATION-deployment" \
                  --namespace="$NAMESPACE" --replicas=0

          # Step 2: Update DNS to point to DR cluster
          echo "Updating DNS to DR cluster..."
          update_dns_to_dr_cluster

          # Step 3: Scale up DR cluster deployment
          echo "Scaling up DR cluster deployment..."
          kubectl --context="$DR_CLUSTER" scale deployment "$APPLICATION-deployment" \
                  --namespace="$NAMESPACE" --replicas=6

          # Step 4: Wait for DR deployment to be ready
          echo "Waiting for DR deployment to be ready..."
          kubectl --context="$DR_CLUSTER" rollout status deployment "$APPLICATION-deployment" \
                  --namespace="$NAMESPACE" --timeout=300s

          # Step 5: Validate application health
          echo "Validating application health..."
          validate_application_health

          echo "Application failover completed successfully"
      }

      update_dns_to_dr_cluster() {
          # Get DR cluster ingress IP
          local dr_ingress_ip=$(kubectl --context="$DR_CLUSTER" get ingress "$APPLICATION-ingress" \
                                -n "$NAMESPACE" -o jsonpath='{.status.loadBalancer.ingress[0].ip}')

          # Update Route53 DNS record
          aws route53 change-resource-record-sets \
              --hosted-zone-id "$HOSTED_ZONE_ID" \
              --change-batch '{
                  "Changes": [{
                      "Action": "UPSERT",
                      "ResourceRecordSet": {
                          "Name": "app.company.com",
                          "Type": "A",
                          "TTL": 60,
                          "ResourceRecords": [{"Value": "'$dr_ingress_ip'"}]
                      }
                  }]
              }'
      }

      validate_application_health() {
          local max_attempts=30
          local attempt=1

          while [ $attempt -le $max_attempts ]; do
              local response=$(curl -s -o /dev/null -w "%{http_code}" "https://app.company.com/health")

              if [ "$response" = "200" ]; then
                  echo "✓ Application health validation successful"
                  return 0
              fi

              echo "Attempt $attempt/$max_attempts: Health check returned $response"
              sleep 10
              ((attempt++))
          done

          echo "✗ Application health validation failed after $max_attempts attempts"
          return 1
      }

      # Execute failover
      trigger_application_failover
```

### Stateful Application Recovery

#### Session State Management
```bash
#!/bin/bash
# Stateful Application Recovery with Session Management

REDIS_PRIMARY="redis-primary.company.com"
REDIS_DR="redis-dr.company.com"
APPLICATION_TIER="web-app"

manage_session_state_failover() {
    echo "=== Managing Session State During Failover ==="

    # Step 1: Sync session data to DR Redis
    sync_redis_data

    # Step 2: Update application configuration
    update_application_session_config

    # Step 3: Graceful application switchover
    perform_graceful_switchover

    # Step 4: Validate session continuity
    validate_session_continuity
}

sync_redis_data() {
    echo "Syncing Redis session data to DR cluster..."

    # Use Redis replication or manual sync
    redis-cli -h "$REDIS_PRIMARY" --rdb /tmp/redis_backup.rdb

    # Transfer to DR Redis
    redis-cli -h "$REDIS_DR" --pipe < /tmp/redis_backup.rdb

    # Verify data sync
    local primary_keys=$(redis-cli -h "$REDIS_PRIMARY" dbsize | cut -d: -f2)
    local dr_keys=$(redis-cli -h "$REDIS_DR" dbsize | cut -d: -f2)

    if [ "$primary_keys" -eq "$dr_keys" ]; then
        echo "✓ Redis data sync successful ($primary_keys keys)"
    else
        echo "⚠ Redis data sync partial (Primary: $primary_keys, DR: $dr_keys)"
    fi
}

update_application_session_config() {
    echo "Updating application session configuration..."

    # Update Kubernetes ConfigMap
    kubectl patch configmap redis-config \
        --namespace production \
        --patch='{"data":{"redis-host":"'$REDIS_DR'"}}'

    # Rolling restart of application pods
    kubectl rollout restart deployment "$APPLICATION_TIER-deployment" \
        --namespace production

    # Wait for rollout to complete
    kubectl rollout status deployment "$APPLICATION_TIER-deployment" \
        --namespace production --timeout=300s
}

perform_graceful_switchover() {
    echo "Performing graceful application switchover..."

    # Drain existing connections gradually
    for replica in $(seq 6 -1 1); do
        kubectl scale deployment "$APPLICATION_TIER-deployment" \
            --namespace production --replicas=$replica

        echo "Scaled down to $replica replicas, waiting for connections to drain..."
        sleep 30
    done

    # Update load balancer to point to DR
    update_load_balancer_to_dr

    # Scale up to full capacity
    kubectl scale deployment "$APPLICATION_TIER-deployment" \
        --namespace production --replicas=6
}

validate_session_continuity() {
    echo "Validating session continuity..."

    # Test session persistence
    local session_test_result=$(curl -s -c /tmp/cookies.txt -b /tmp/cookies.txt \
        "https://app.company.com/api/session/test" | jq -r '.session_valid')

    if [ "$session_test_result" = "true" ]; then
        echo "✓ Session continuity validated"
    else
        echo "✗ Session continuity validation failed"
        return 1
    fi
}

# Database connection failover for stateful apps
database_connection_failover() {
    local app_name="$1"
    local primary_db="$2"
    local dr_db="$3"

    echo "Failing over database connections for $app_name..."

    # Update database connection strings
    kubectl patch secret database-credentials \
        --namespace production \
        --patch="{\"data\":{\"url\":\"$(echo -n "$dr_db" | base64)\"}}"

    # Restart application pods to pick up new config
    kubectl delete pods -l app="$app_name" --namespace production

    # Wait for pods to be ready
    kubectl wait --for=condition=ready pod -l app="$app_name" \
        --namespace production --timeout=300s

    echo "Database connection failover completed"
}

# Application configuration management during DR
manage_application_config_dr() {
    echo "Managing application configuration during DR..."

    # Create DR-specific ConfigMap
    cat > /tmp/dr-config.yaml << EOF
apiVersion: v1
kind: ConfigMap
metadata:
  name: web-app-config-dr
  namespace: production
data:
  database.host: "dr-database.company.com"
  redis.host: "redis-dr.company.com"
  external.api.endpoint: "https://api-dr.company.com"
  logging.level: "INFO"
  feature.flags: |
    maintenance_mode: false
    read_only_mode: false
    dr_mode: true
  environment: "disaster-recovery"
EOF

    kubectl apply -f /tmp/dr-config.yaml

    # Update deployment to use DR config
    kubectl patch deployment "$APPLICATION_TIER-deployment" \
        --namespace production \
        --patch='{
            "spec": {
                "template": {
                    "spec": {
                        "containers": [{
                            "name": "web-app",
                            "env": [{
                                "name": "CONFIG_MAP_NAME",
                                "value": "web-app-config-dr"
                            }]
                        }]
                    }
                }
            }
        }'
}
```

## Microservices Recovery Orchestration

### Service Mesh Disaster Recovery

#### Istio Service Mesh DR Configuration
```yaml
istio_dr_configuration:
  virtual_service_failover: |
    apiVersion: networking.istio.io/v1beta1
    kind: VirtualService
    metadata:
      name: user-service-vs
      namespace: production
    spec:
      hosts:
      - user-service
      http:
      - match:
        - headers:
            x-dr-region:
              exact: west
        route:
        - destination:
            host: user-service
            subset: west-region
      - route:
        - destination:
            host: user-service
            subset: east-region
          weight: 100
        - destination:
            host: user-service
            subset: west-region
          weight: 0
        fault:
          abort:
            percentage:
              value: 0
        timeout: 30s
        retries:
          attempts: 3
          perTryTimeout: 10s
          retryOn: gateway-error,connect-failure,refused-stream

  destination_rule: |
    apiVersion: networking.istio.io/v1beta1
    kind: DestinationRule
    metadata:
      name: user-service-dr
      namespace: production
    spec:
      host: user-service
      trafficPolicy:
        connectionPool:
          tcp:
            maxConnections: 100
          http:
            http1MaxPendingRequests: 50
            maxRequestsPerConnection: 2
        loadBalancer:
          simple: LEAST_CONN
        outlierDetection:
          consecutiveErrors: 3
          interval: 30s
          baseEjectionTime: 30s
          maxEjectionPercent: 50
      subsets:
      - name: east-region
        labels:
          region: east
        trafficPolicy:
          connectionPool:
            tcp:
              maxConnections: 50
      - name: west-region
        labels:
          region: west
        trafficPolicy:
          connectionPool:
            tcp:
              maxConnections: 30

  circuit_breaker_policy: |
    apiVersion: networking.istio.io/v1beta1
    kind: DestinationRule
    metadata:
      name: circuit-breaker
      namespace: production
    spec:
      host: "*.company.local"
      trafficPolicy:
        outlierDetection:
          consecutiveGatewayErrors: 5
          consecutive5xxErrors: 5
          interval: 10s
          baseEjectionTime: 30s
          maxEjectionPercent: 50
          minHealthPercent: 30

service_mesh_automation:
  failover_script: |
    #!/bin/bash
    # Istio Service Mesh DR Failover

    NAMESPACE="production"
    PRIMARY_REGION="east"
    DR_REGION="west"

    trigger_service_mesh_failover() {
        echo "=== Triggering Service Mesh Failover ==="

        # Update VirtualService to route traffic to DR region
        for service in user-service order-service payment-service; do
            echo "Updating $service VirtualService for DR failover..."

            kubectl patch virtualservice "$service-vs" \
                --namespace "$NAMESPACE" \
                --type='json' \
                --patch='[{
                    "op": "replace",
                    "path": "/spec/http/0/route/0/weight",
                    "value": 0
                }, {
                    "op": "replace",
                    "path": "/spec/http/0/route/1/weight",
                    "value": 100
                }]'
        done

        # Wait for configuration to propagate
        sleep 30

        # Validate traffic routing
        validate_traffic_routing

        echo "Service mesh failover completed"
    }

    validate_traffic_routing() {
        echo "Validating traffic routing to DR region..."

        local test_endpoint="https://api.company.com/health"
        local dr_responses=0
        local total_tests=10

        for i in $(seq 1 $total_tests); do
            local response_region=$(curl -s "$test_endpoint" | jq -r '.region')
            if [ "$response_region" = "$DR_REGION" ]; then
                ((dr_responses++))
            fi
            sleep 1
        done

        local dr_percentage=$((dr_responses * 100 / total_tests))
        echo "DR region responses: $dr_percentage%"

        if [ $dr_percentage -ge 90 ]; then
            echo "✓ Traffic routing validation successful"
        else
            echo "✗ Traffic routing validation failed"
            return 1
        fi
    }

    # Execute failover
    trigger_service_mesh_failover
```

### API Gateway Disaster Recovery

#### Kong API Gateway DR Setup
```bash
#!/bin/bash
# Kong API Gateway Disaster Recovery Configuration

KONG_PRIMARY="kong-primary.company.com:8001"
KONG_DR="kong-dr.company.com:8001"

setup_kong_dr() {
    echo "=== Setting up Kong API Gateway DR ==="

    # Export configuration from primary
    export_kong_configuration

    # Import configuration to DR
    import_kong_configuration

    # Configure health checks and failover
    configure_kong_health_checks

    # Set up automated sync
    setup_kong_config_sync
}

export_kong_configuration() {
    echo "Exporting Kong configuration from primary..."

    # Export all Kong entities
    curl -s "$KONG_PRIMARY/config" | jq '.' > /tmp/kong_primary_config.json

    # Export specific entities for validation
    local entities=("services" "routes" "plugins" "consumers" "certificates")

    for entity in "${entities[@]}"; do
        curl -s "$KONG_PRIMARY/$entity" | jq '.data' > "/tmp/kong_${entity}.json"
        echo "Exported $entity: $(jq length "/tmp/kong_${entity}.json") items"
    done
}

import_kong_configuration() {
    echo "Importing Kong configuration to DR..."

    # Import configuration to DR Kong
    curl -X POST "$KONG_DR/config" \
         -F config=@/tmp/kong_primary_config.json

    # Verify import
    local primary_services=$(curl -s "$KONG_PRIMARY/services" | jq '.data | length')
    local dr_services=$(curl -s "$KONG_DR/services" | jq '.data | length')

    echo "Primary services: $primary_services"
    echo "DR services: $dr_services"

    if [ "$primary_services" -eq "$dr_services" ]; then
        echo "✓ Kong configuration sync successful"
    else
        echo "✗ Kong configuration sync incomplete"
        return 1
    fi
}

configure_kong_health_checks() {
    echo "Configuring Kong health checks..."

    # Add health check service
    cat > /tmp/health_check_service.json << EOF
{
    "name": "health-check-service",
    "url": "http://health-check.company.com",
    "path": "/health",
    "retries": 3,
    "connect_timeout": 5000,
    "read_timeout": 10000,
    "write_timeout": 10000
}
EOF

    curl -X POST "$KONG_PRIMARY/services" \
         -H "Content-Type: application/json" \
         -d @/tmp/health_check_service.json

    curl -X POST "$KONG_DR/services" \
         -H "Content-Type: application/json" \
         -d @/tmp/health_check_service.json

    # Add health check route
    local primary_service_id=$(curl -s "$KONG_PRIMARY/services/health-check-service" | jq -r '.id')
    local dr_service_id=$(curl -s "$KONG_DR/services/health-check-service" | jq -r '.id')

    cat > /tmp/health_check_route.json << EOF
{
    "name": "health-check-route",
    "paths": ["/health"],
    "methods": ["GET"],
    "strip_path": false
}
EOF

    curl -X POST "$KONG_PRIMARY/services/$primary_service_id/routes" \
         -H "Content-Type: application/json" \
         -d @/tmp/health_check_route.json

    curl -X POST "$KONG_DR/services/$dr_service_id/routes" \
         -H "Content-Type: application/json" \
         -d @/tmp/health_check_route.json
}

# Kong failover automation
kong_failover_automation() {
    echo "Implementing Kong failover automation..."

    cat > /tmp/kong_failover.py << 'EOF'
#!/usr/bin/env python3
import requests
import json
import time
import sys

class KongFailoverManager:
    def __init__(self, primary_url, dr_url):
        self.primary_url = primary_url
        self.dr_url = dr_url
        self.current_active = "primary"

    def check_kong_health(self, kong_url):
        """Check Kong instance health"""
        try:
            response = requests.get(f"{kong_url}/status", timeout=5)
            return response.status_code == 200
        except:
            return False

    def get_kong_config(self, kong_url):
        """Get Kong configuration"""
        try:
            response = requests.get(f"{kong_url}/config")
            return response.json() if response.status_code == 200 else None
        except:
            return None

    def sync_config(self, source_url, target_url):
        """Sync configuration from source to target"""
        try:
            # Export from source
            config = self.get_kong_config(source_url)
            if not config:
                return False

            # Import to target
            response = requests.post(
                f"{target_url}/config",
                files={'config': ('config.json', json.dumps(config))}
            )
            return response.status_code == 201
        except:
            return False

    def failover_to_dr(self):
        """Failover from primary to DR"""
        print("Initiating failover to DR Kong...")

        # Sync latest config to DR
        if self.sync_config(self.primary_url, self.dr_url):
            print("✓ Configuration synced to DR")
        else:
            print("⚠ Configuration sync failed, proceeding with existing DR config")

        # Update DNS or load balancer to point to DR
        self.update_dns_to_dr()

        # Verify DR is handling traffic
        if self.verify_dr_traffic():
            self.current_active = "dr"
            print("✓ Failover to DR completed successfully")
            return True
        else:
            print("✗ DR verification failed")
            return False

    def update_dns_to_dr(self):
        """Update DNS to point to DR Kong"""
        # Implementation depends on DNS provider
        print("Updating DNS to point to DR Kong...")
        # Example: Update Route53, CloudFlare, etc.

    def verify_dr_traffic(self):
        """Verify DR Kong is handling traffic correctly"""
        try:
            response = requests.get("https://api.company.com/health", timeout=10)
            return response.status_code == 200
        except:
            return False

    def monitor_and_failover(self):
        """Monitor Kong health and trigger failover if needed"""
        failure_count = 0
        max_failures = 3

        while True:
            if self.current_active == "primary":
                primary_healthy = self.check_kong_health(self.primary_url)
                dr_healthy = self.check_kong_health(self.dr_url)

                if not primary_healthy:
                    failure_count += 1
                    print(f"Primary Kong unhealthy (failures: {failure_count}/{max_failures})")

                    if failure_count >= max_failures and dr_healthy:
                        self.failover_to_dr()
                        failure_count = 0
                else:
                    failure_count = 0

            elif self.current_active == "dr":
                # Monitor for primary recovery
                primary_healthy = self.check_kong_health(self.primary_url)
                if primary_healthy:
                    print("Primary Kong recovered, consider failback")

            time.sleep(30)

if __name__ == "__main__":
    manager = KongFailoverManager(
        "http://kong-primary.company.com:8001",
        "http://kong-dr.company.com:8001"
    )
    manager.monitor_and_failover()
EOF

    chmod +x /tmp/kong_failover.py
    python3 /tmp/kong_failover.py &
}

# Main execution
case "$1" in
    "setup")
        setup_kong_dr
        ;;
    "failover")
        kong_failover_automation
        ;;
    *)
        echo "Usage: $0 {setup|failover}"
        exit 1
        ;;
esac
```

## Application Data Recovery

### File System and Object Storage Recovery

#### Application File Recovery Automation
```bash
#!/bin/bash
# Application File Recovery Automation

APP_DATA_PRIMARY="/mnt/app-data"
APP_DATA_DR="/mnt/app-data-dr"
S3_PRIMARY_BUCKET="app-data-primary"
S3_DR_BUCKET="app-data-dr"

application_file_recovery() {
    local recovery_type="$1"
    local recovery_point="$2"

    echo "=== Application File Recovery ==="
    echo "Recovery Type: $recovery_type"
    echo "Recovery Point: $recovery_point"

    case "$recovery_type" in
        "local")
            recover_local_files "$recovery_point"
            ;;
        "s3")
            recover_s3_files "$recovery_point"
            ;;
        "snapshot")
            recover_from_snapshot "$recovery_point"
            ;;
        *)
            echo "Invalid recovery type. Use: local, s3, or snapshot"
            return 1
            ;;
    esac
}

recover_local_files() {
    local recovery_point="$1"

    echo "Recovering local application files..."

    # Stop application services
    systemctl stop web-app api-service

    # Create backup of current state
    tar -czf "/backup/current_state_$(date +%Y%m%d_%H%M%S).tar.gz" -C "$APP_DATA_PRIMARY" .

    # Restore from backup
    if [ -f "/backup/app_data_${recovery_point}.tar.gz" ]; then
        echo "Restoring from backup: app_data_${recovery_point}.tar.gz"

        # Clear current data
        rm -rf "${APP_DATA_PRIMARY:?}"/*

        # Extract backup
        tar -xzf "/backup/app_data_${recovery_point}.tar.gz" -C "$APP_DATA_PRIMARY"

        # Verify restoration
        if verify_file_integrity "$APP_DATA_PRIMARY"; then
            echo "✓ Local file recovery successful"
        else
            echo "✗ Local file recovery failed - integrity check failed"
            return 1
        fi
    else
        echo "✗ Backup file not found: app_data_${recovery_point}.tar.gz"
        return 1
    fi

    # Restart application services
    systemctl start web-app api-service

    # Verify application functionality
    verify_application_functionality
}

recover_s3_files() {
    local recovery_point="$1"

    echo "Recovering files from S3..."

    # Stop application services
    systemctl stop web-app api-service

    # Sync from S3 DR bucket
    aws s3 sync "s3://$S3_DR_BUCKET" "$APP_DATA_PRIMARY" --delete

    # If specific recovery point requested, restore from versioned objects
    if [ -n "$recovery_point" ]; then
        echo "Restoring S3 objects to version: $recovery_point"

        # List all objects and restore to specific version
        aws s3api list-object-versions --bucket "$S3_DR_BUCKET" \
            --query 'Versions[?LastModified<=`'$recovery_point'`].[Key,VersionId]' \
            --output text | while read key version_id; do

            echo "Restoring $key to version $version_id"
            aws s3api get-object \
                --bucket "$S3_DR_BUCKET" \
                --key "$key" \
                --version-id "$version_id" \
                "${APP_DATA_PRIMARY}/${key}"
        done
    fi

    # Verify S3 sync
    local local_count=$(find "$APP_DATA_PRIMARY" -type f | wc -l)
    local s3_count=$(aws s3 ls "s3://$S3_DR_BUCKET" --recursive | wc -l)

    echo "Local files: $local_count"
    echo "S3 files: $s3_count"

    # Restart application services
    systemctl start web-app api-service

    echo "✓ S3 file recovery completed"
}

recover_from_snapshot() {
    local snapshot_id="$1"

    echo "Recovering from EBS snapshot: $snapshot_id"

    # Create volume from snapshot
    local volume_id=$(aws ec2 create-volume \
        --snapshot-id "$snapshot_id" \
        --availability-zone "$(curl -s http://169.254.169.254/latest/meta-data/placement/availability-zone)" \
        --volume-type gp3 \
        --query 'VolumeId' \
        --output text)

    echo "Created volume: $volume_id"

    # Wait for volume to be available
    aws ec2 wait volume-available --volume-ids "$volume_id"

    # Get instance ID
    local instance_id=$(curl -s http://169.254.169.254/latest/meta-data/instance-id)

    # Attach volume to instance
    aws ec2 attach-volume \
        --volume-id "$volume_id" \
        --instance-id "$instance_id" \
        --device /dev/xvdf

    # Wait for attachment
    sleep 30

    # Mount the restored volume
    mkdir -p /mnt/recovery
    mount /dev/xvdf /mnt/recovery

    # Stop application services
    systemctl stop web-app api-service

    # Copy data from recovered volume
    rsync -av /mnt/recovery/ "$APP_DATA_PRIMARY/"

    # Unmount and detach recovery volume
    umount /mnt/recovery
    aws ec2 detach-volume --volume-id "$volume_id"

    # Wait for detachment and delete volume
    aws ec2 wait volume-available --volume-ids "$volume_id"
    aws ec2 delete-volume --volume-id "$volume_id"

    # Restart application services
    systemctl start web-app api-service

    echo "✓ Snapshot recovery completed"
}

verify_file_integrity() {
    local data_dir="$1"

    echo "Verifying file integrity..."

    # Check for required application files
    local required_files=(
        "config/app.conf"
        "static/css/app.css"
        "static/js/app.js"
        "templates/index.html"
    )

    for file in "${required_files[@]}"; do
        if [ ! -f "$data_dir/$file" ]; then
            echo "✗ Required file missing: $file"
            return 1
        fi
    done

    # Verify file checksums if available
    if [ -f "$data_dir/.checksums" ]; then
        cd "$data_dir" && sha256sum -c .checksums > /dev/null 2>&1
        if [ $? -eq 0 ]; then
            echo "✓ File integrity verified via checksums"
        else
            echo "⚠ Some files failed checksum verification"
        fi
    fi

    echo "✓ File integrity verification completed"
    return 0
}

verify_application_functionality() {
    echo "Verifying application functionality..."

    local health_checks=(
        "http://localhost:8080/health"
        "http://localhost:8080/api/status"
        "http://localhost:8080/static/css/app.css"
    )

    for endpoint in "${health_checks[@]}"; do
        local response=$(curl -s -o /dev/null -w "%{http_code}" "$endpoint")
        if [ "$response" = "200" ]; then
            echo "✓ Health check passed: $endpoint"
        else
            echo "✗ Health check failed: $endpoint (HTTP $response)"
            return 1
        fi
    done

    echo "✓ Application functionality verified"
    return 0
}

# Main execution
case "$1" in
    "recover")
        application_file_recovery "$2" "$3"
        ;;
    *)
        echo "Usage: $0 recover <type> <recovery-point>"
        echo ""
        echo "Types: local, s3, snapshot"
        echo "Recovery Point: timestamp or snapshot-id"
        exit 1
        ;;
esac
```

This comprehensive Application Recovery document provides detailed strategies for stateless and stateful application recovery, microservices orchestration, service mesh disaster recovery, API gateway failover, and application data recovery automation essential for enterprise application resilience.