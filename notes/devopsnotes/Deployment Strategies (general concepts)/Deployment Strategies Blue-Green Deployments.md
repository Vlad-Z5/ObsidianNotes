## Production Blue-Green Deployment Implementation

### Blue-Green Deployment Fundamentals

#### Infrastructure Setup
```yaml
# infrastructure/blue-green/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: production-blue
  labels:
    environment: production
    deployment-slot: blue
---
apiVersion: v1
kind: Namespace
metadata:
  name: production-green
  labels:
    environment: production
    deployment-slot: green
```

#### Application Deployment Configuration
```yaml
# deployments/web-app-blue.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-app-blue
  namespace: production-blue
  labels:
    app: web-app
    version: blue
    deployment-strategy: blue-green
spec:
  replicas: 5
  selector:
    matchLabels:
      app: web-app
      version: blue
  template:
    metadata:
      labels:
        app: web-app
        version: blue
      annotations:
        deployment.kubernetes.io/revision: "1"
    spec:
      containers:
      - name: web-app
        image: web-app:v1.2.3
        ports:
        - containerPort: 8080
        env:
        - name: DEPLOYMENT_SLOT
          value: "blue"
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: database-credentials
              key: url
        resources:
          requests:
            cpu: 250m
            memory: 512Mi
          limits:
            cpu: 1000m
            memory: 1Gi
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: web-app-blue-service
  namespace: production-blue
spec:
  selector:
    app: web-app
    version: blue
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8080
  type: ClusterIP
```

### Blue-Green Deployment Automation

#### Deployment Script
```bash
#!/bin/bash
# scripts/blue-green-deploy.sh - Production blue-green deployment

set -euo pipefail

readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly APP_NAME="web-app"
readonly INGRESS_NAME="web-app-ingress"
readonly HEALTH_CHECK_URL="/health"
readonly READY_CHECK_URL="/ready"
readonly DEPLOYMENT_TIMEOUT=600  # 10 minutes
readonly HEALTH_CHECK_TIMEOUT=300  # 5 minutes

# Colors
readonly GREEN='\033[0;32m'
readonly BLUE='\033[0;34m'
readonly RED='\033[0;31m'
readonly YELLOW='\033[1;33m'
readonly NC='\033[0m'

log_info() { echo -e "[$(date '+%H:%M:%S')] ${BLUE}INFO${NC}: $*"; }
log_success() { echo -e "[$(date '+%H:%M:%S')] ${GREEN}SUCCESS${NC}: $*"; }
log_warn() { echo -e "[$(date '+%H:%M:%S')] ${YELLOW}WARN${NC}: $*"; }
log_error() { echo -e "[$(date '+%H:%M:%S')] ${RED}ERROR${NC}: $*"; }

# Determine current active environment
get_active_environment() {
    local current_target
    current_target=$(kubectl get ingress "$INGRESS_NAME" -n production \
                    -o jsonpath='{.spec.rules[0].http.paths[0].backend.service.name}' 2>/dev/null || echo "")
    
    if [[ "$current_target" == *"blue"* ]]; then
        echo "blue"
    elif [[ "$current_target" == *"green"* ]]; then
        echo "green"
    else
        # Default to blue if no current deployment
        echo "blue"
    fi
}

# Get inactive environment
get_inactive_environment() {
    local active="$1"
    if [[ "$active" == "blue" ]]; then
        echo "green"
    else
        echo "blue"
    fi
}

# Deploy to inactive environment
deploy_to_inactive() {
    local image_tag="$1"
    local active_env="$2"
    local inactive_env="$3"
    
    log_info "Deploying $APP_NAME:$image_tag to $inactive_env environment"
    
    # Update deployment manifest with new image
    local deployment_file="deployments/${APP_NAME}-${inactive_env}.yaml"
    
    # Create deployment if it doesn't exist
    if [[ ! -f "$deployment_file" ]]; then
        log_info "Creating deployment file for $inactive_env environment"
        sed "s/blue/$inactive_env/g; s/v1\.2\.3/$image_tag/g" \
            "deployments/${APP_NAME}-blue.yaml" > "$deployment_file"
    else
        # Update existing deployment
        sed -i.bak "s/image: ${APP_NAME}:.*/image: ${APP_NAME}:${image_tag}/" "$deployment_file"
    fi
    
    # Apply deployment
    kubectl apply -f "$deployment_file"
    
    # Wait for deployment to complete
    log_info "Waiting for $inactive_env deployment to complete..."
    if ! kubectl rollout status deployment/"${APP_NAME}-${inactive_env}" \
         -n "production-${inactive_env}" --timeout="${DEPLOYMENT_TIMEOUT}s"; then
        log_error "Deployment to $inactive_env environment failed"
        return 1
    fi
    
    log_success "Deployment to $inactive_env environment completed"
}

# Health check for inactive environment
health_check_inactive() {
    local inactive_env="$1"
    local service_url="http://${APP_NAME}-${inactive_env}-service.production-${inactive_env}.svc.cluster.local"
    
    log_info "Running health checks for $inactive_env environment"
    
    local end_time=$(($(date +%s) + HEALTH_CHECK_TIMEOUT))
    
    while [[ $(date +%s) -lt $end_time ]]; do
        # Check readiness
        if curl -sf "${service_url}${READY_CHECK_URL}" >/dev/null 2>&1; then
            log_info "Readiness check passed for $inactive_env"
            
            # Check health
            if curl -sf "${service_url}${HEALTH_CHECK_URL}" >/dev/null 2>&1; then
                log_success "Health check passed for $inactive_env"
                return 0
            fi
        fi
        
        log_info "Health check in progress... ($(((end_time - $(date +%s)))) seconds remaining)"
        sleep 10
    done
    
    log_error "Health check failed for $inactive_env environment"
    return 1
}

# Run smoke tests
run_smoke_tests() {
    local inactive_env="$1"
    local service_url="http://${APP_NAME}-${inactive_env}-service.production-${inactive_env}.svc.cluster.local"
    
    log_info "Running smoke tests for $inactive_env environment"
    
    # Basic functionality tests
    local tests=(
        "GET ${service_url}/api/status 200"
        "GET ${service_url}/api/version 200"
        "POST ${service_url}/api/healthcheck 200"
    )
    
    for test in "${tests[@]}"; do
        local method url expected_code
        read -r method url expected_code <<< "$test"
        
        local response_code
        response_code=$(curl -s -o /dev/null -w "%{http_code}" -X "$method" "$url" || echo "000")
        
        if [[ "$response_code" == "$expected_code" ]]; then
            log_success "Smoke test passed: $method $url -> $response_code"
        else
            log_error "Smoke test failed: $method $url -> $response_code (expected $expected_code)"
            return 1
        fi
    done
    
    # Performance test
    log_info "Running performance test..."
    local avg_response_time
    avg_response_time=$(curl -s -w "%{time_total}" -o /dev/null "${service_url}/api/status")
    
    if (( $(echo "$avg_response_time < 1.0" | bc -l) )); then
        log_success "Performance test passed: ${avg_response_time}s response time"
    else
        log_warn "Performance test warning: ${avg_response_time}s response time (>1s)"
    fi
    
    log_success "Smoke tests completed for $inactive_env environment"
}

# Switch traffic to inactive environment
switch_traffic() {
    local inactive_env="$1"
    local active_env="$2"
    
    log_info "Switching traffic from $active_env to $inactive_env"
    
    # Update ingress to point to inactive environment
    kubectl patch ingress "$INGRESS_NAME" -n production \
            --type='json' \
            -p="[{\"op\": \"replace\", \"path\": \"/spec/rules/0/http/paths/0/backend/service/name\", \"value\": \"${APP_NAME}-${inactive_env}-service\"}]"
    
    # Update service selector if using a single service approach
    if kubectl get service "${APP_NAME}-service" -n production >/dev/null 2>&1; then
        kubectl patch service "${APP_NAME}-service" -n production \
                --type='json' \
                -p="[{\"op\": \"replace\", \"path\": \"/spec/selector/version\", \"value\": \"${inactive_env}\"}]"
    fi
    
    log_success "Traffic switched to $inactive_env environment"
}

# Monitor new deployment
monitor_deployment() {
    local new_active_env="$1"
    local monitor_duration="${2:-300}"  # 5 minutes default
    
    log_info "Monitoring $new_active_env deployment for ${monitor_duration}s"
    
    local service_url="http://${APP_NAME}-service.production.svc.cluster.local"
    local end_time=$(($(date +%s) + monitor_duration))
    local error_count=0
    local total_checks=0
    
    while [[ $(date +%s) -lt $end_time ]]; do
        ((total_checks++))
        
        # Check application health
        if ! curl -sf "${service_url}${HEALTH_CHECK_URL}" >/dev/null 2>&1; then
            ((error_count++))
            log_warn "Health check failed (${error_count}/${total_checks})"
            
            # Fail if error rate exceeds 10%
            if (( error_count * 100 / total_checks > 10 )); then
                log_error "Error rate exceeded 10%, triggering rollback"
                return 1
            fi
        fi
        
        # Check metrics if available
        check_deployment_metrics "$new_active_env"
        
        sleep 30
    done
    
    local success_rate=$(( (total_checks - error_count) * 100 / total_checks ))
    log_success "Monitoring completed: ${success_rate}% success rate"
    
    return 0
}

# Check deployment metrics
check_deployment_metrics() {
    local environment="$1"
    
    # Check error rate from Prometheus (if available)
    if command -v curl >/dev/null && [[ -n "${PROMETHEUS_URL:-}" ]]; then
        local error_rate
        error_rate=$(curl -s "${PROMETHEUS_URL}/api/v1/query?query=rate(http_requests_total{job=\"${APP_NAME}\",status=~\"5..\"}[5m])" | \
                    jq -r '.data.result[0].value[1] // "0"' 2>/dev/null || echo "0")
        
        if (( $(echo "$error_rate > 0.01" | bc -l) )); then  # >1% error rate
            log_warn "High error rate detected: $error_rate"
        fi
        
        # Check response time
        local p95_latency
        p95_latency=$(curl -s "${PROMETHEUS_URL}/api/v1/query?query=histogram_quantile(0.95,rate(http_request_duration_seconds_bucket{job=\"${APP_NAME}\"}[5m]))" | \
                     jq -r '.data.result[0].value[1] // "0"' 2>/dev/null || echo "0")
        
        if (( $(echo "$p95_latency > 2.0" | bc -l) )); then  # >2s p95
            log_warn "High latency detected: ${p95_latency}s"
        fi
    fi
}

# Rollback deployment
rollback_deployment() {
    local failed_env="$1"
    local rollback_env="$2"
    
    log_error "Rolling back from $failed_env to $rollback_env"
    
    # Switch traffic back
    switch_traffic "$rollback_env" "$failed_env"
    
    # Send alert
    send_deployment_alert "ROLLBACK" "$failed_env" "$rollback_env"
    
    log_success "Rollback completed"
}

# Clean up old environment
cleanup_old_environment() {
    local old_env="$1"
    local keep_for_rollback="${2:-true}"
    
    if [[ "$keep_for_rollback" == "true" ]]; then
        log_info "Keeping $old_env environment for potential rollback"
        # Scale down but don't delete
        kubectl scale deployment "${APP_NAME}-${old_env}" \
                --replicas=1 -n "production-${old_env}" || true
    else
        log_info "Cleaning up $old_env environment"
        kubectl delete deployment "${APP_NAME}-${old_env}" \
                -n "production-${old_env}" || true
    fi
}

# Send deployment notifications
send_deployment_alert() {
    local status="$1"
    local from_env="$2"
    local to_env="$3"
    
    if [[ -n "${SLACK_WEBHOOK_URL:-}" ]]; then
        local color="good"
        local icon="✅"
        
        if [[ "$status" == "ROLLBACK" ]]; then
            color="danger"
            icon="🔄"
        fi
        
        local payload=$(cat <<EOF
{
    "attachments": [
        {
            "color": "$color",
            "title": "$icon Blue-Green Deployment $status",
            "fields": [
                {
                    "title": "Application",
                    "value": "$APP_NAME",
                    "short": true
                },
                {
                    "title": "Action",
                    "value": "$from_env → $to_env",
                    "short": true
                },
                {
                    "title": "Time",
                    "value": "$(date)",
                    "short": false
                }
            ]
        }
    ]
}
EOF
)
        
        curl -X POST -H 'Content-type: application/json' \
             --data "$payload" \
             "$SLACK_WEBHOOK_URL" >/dev/null 2>&1 || log_warn "Failed to send notification"
    fi
}

# Main deployment function
main() {
    local action="${1:-deploy}"
    local image_tag="${2:-}"
    
    case "$action" in
        "deploy")
            [[ -z "$image_tag" ]] && { log_error "Image tag required"; exit 1; }
            
            local active_env
            active_env=$(get_active_environment)
            
            local inactive_env
            inactive_env=$(get_inactive_environment "$active_env")
            
            log_info "Starting blue-green deployment"
            log_info "Current active: $active_env, deploying to: $inactive_env"
            
            # Deploy to inactive environment
            if ! deploy_to_inactive "$image_tag" "$active_env" "$inactive_env"; then
                log_error "Deployment failed"
                exit 1
            fi
            
            # Health checks
            if ! health_check_inactive "$inactive_env"; then
                log_error "Health checks failed"
                exit 1
            fi
            
            # Smoke tests
            if ! run_smoke_tests "$inactive_env"; then
                log_error "Smoke tests failed"
                exit 1
            fi
            
            # Switch traffic
            switch_traffic "$inactive_env" "$active_env"
            
            # Monitor deployment
            if ! monitor_deployment "$inactive_env" 300; then
                rollback_deployment "$inactive_env" "$active_env"
                exit 1
            fi
            
            # Clean up old environment
            cleanup_old_environment "$active_env" true
            
            # Send success notification
            send_deployment_alert "SUCCESS" "$active_env" "$inactive_env"
            
            log_success "Blue-green deployment completed successfully"
            ;;
        "rollback")
            local current_env
            current_env=$(get_active_environment)
            
            local rollback_env
            rollback_env=$(get_inactive_environment "$current_env")
            
            log_info "Rolling back from $current_env to $rollback_env"
            
            switch_traffic "$rollback_env" "$current_env"
            send_deployment_alert "ROLLBACK" "$current_env" "$rollback_env"
            
            log_success "Rollback completed"
            ;;
        "status")
            local active_env
            active_env=$(get_active_environment)
            
            echo "Active environment: $active_env"
            kubectl get pods -n "production-$active_env" -l "app=$APP_NAME"
            ;;
        *)
            cat <<EOF
Blue-Green Deployment Tool

Usage: $0 <command> [options]

Commands:
  deploy <image-tag>    - Deploy new version using blue-green strategy
  rollback             - Rollback to previous environment
  status               - Show current deployment status

Examples:
  $0 deploy v1.2.3
  $0 rollback
  $0 status
EOF
            ;;
    esac
}

# Run main function if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
```

### Blue-Green with Database Migrations
```bash
#!/bin/bash
# scripts/blue-green-with-migrations.sh - Blue-green with database handling

# Database migration strategy for blue-green deployments
handle_database_migration() {
    local image_tag="$1"
    local inactive_env="$2"
    local migration_strategy="${3:-backward-compatible}"
    
    log_info "Handling database migration strategy: $migration_strategy"
    
    case "$migration_strategy" in
        "backward-compatible")
            # Safe: Deploy first, migrate after traffic switch
            log_info "Using backward-compatible migration strategy"
            
            # Deploy application first
            deploy_to_inactive "$image_tag" "$active_env" "$inactive_env"
            
            # Switch traffic
            switch_traffic "$inactive_env" "$active_env"
            
            # Run migrations after traffic switch
            run_database_migrations "$inactive_env"
            ;;
            
        "forward-only")
            # Risky: Migrate first, then deploy
            log_warn "Using forward-only migration strategy - requires careful planning"
            
            # Create database backup
            create_database_backup
            
            # Run migrations first
            run_database_migrations "$inactive_env"
            
            # Deploy application
            deploy_to_inactive "$image_tag" "$active_env" "$inactive_env"
            
            # Switch traffic
            switch_traffic "$inactive_env" "$active_env"
            ;;
            
        "parallel-run")
            # Complex: Run both versions simultaneously
            log_info "Using parallel-run strategy with dual writes"
            
            # Enable dual writes in active environment
            enable_dual_writes "$active_env"
            
            # Deploy to inactive environment
            deploy_to_inactive "$image_tag" "$active_env" "$inactive_env"
            
            # Gradually shift read traffic
            gradual_traffic_shift "$active_env" "$inactive_env"
            
            # Switch all traffic after validation
            switch_traffic "$inactive_env" "$active_env"
            
            # Disable dual writes
            disable_dual_writes "$inactive_env"
            ;;
    esac
}

# Run database migrations
run_database_migrations() {
    local environment="$1"
    
    log_info "Running database migrations for $environment"
    
    kubectl run migration-job-$(date +%s) \
        --image="${APP_NAME}:${image_tag}" \
        --rm -it --restart=Never \
        --namespace="production-${environment}" \
        -- /app/migrate.sh
}

# Create database backup
create_database_backup() {
    log_info "Creating database backup before migration"
    
    kubectl run backup-job-$(date +%s) \
        --image=postgres:13 \
        --rm -it --restart=Never \
        --namespace=production \
        -- pg_dump -h postgres-service -U postgres production > backup_$(date +%Y%m%d_%H%M%S).sql
}
```

This provides comprehensive blue-green deployment implementation with proper health checks, monitoring, rollback procedures, and database migration handling - all production-ready patterns.