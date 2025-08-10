## Production Zero-Downtime Deployment Strategies

### Zero-Downtime Deployment Fundamentals

#### Circuit Breaker Pattern Implementation
```yaml
# circuit-breaker/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-app-circuit-breaker
  namespace: production
spec:
  replicas: 4
  selector:
    matchLabels:
      app: web-app
      component: circuit-breaker
  template:
    metadata:
      labels:
        app: web-app
        component: circuit-breaker
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/path: "/metrics"
        prometheus.io/port: "9090"
    spec:
      containers:
      - name: web-app
        image: web-app:v1.2.3
        ports:
        - containerPort: 8080
        - containerPort: 9090
        env:
        - name: CIRCUIT_BREAKER_ENABLED
          value: "true"
        - name: CIRCUIT_BREAKER_FAILURE_THRESHOLD
          value: "5"
        - name: CIRCUIT_BREAKER_RECOVERY_TIMEOUT
          value: "30s"
        - name: CIRCUIT_BREAKER_SUCCESS_THRESHOLD
          value: "3"
        resources:
          requests:
            cpu: 200m
            memory: 384Mi
          limits:
            cpu: 800m
            memory: 768Mi
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
          successThreshold: 1
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 2
          successThreshold: 1
        lifecycle:
          preStop:
            exec:
              command:
              - /bin/sh
              - -c
              - |
                # Graceful shutdown with circuit breaker
                echo "Initiating graceful shutdown..."
                curl -X POST http://localhost:8080/admin/circuit-breaker/open || true
                sleep 15  # Allow time for load balancer to detect and drain
                echo "Circuit breaker opened, shutting down..."
      terminationGracePeriodSeconds: 60
---
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: web-app-pdb
  namespace: production
spec:
  selector:
    matchLabels:
      app: web-app
  minAvailable: 75%  # Ensure high availability during deployments
```

### Comprehensive Zero-Downtime Deployment Script

```bash
#!/bin/bash
# scripts/zero-downtime-deploy.sh - Zero-downtime deployment orchestration

set -euo pipefail

readonly APP_NAME="web-app"
readonly NAMESPACE="production"
readonly LB_HEALTH_CHECK_PATH="/health"
readonly CIRCUIT_BREAKER_ENDPOINT="/admin/circuit-breaker"
readonly DEPLOYMENT_TIMEOUT=1200  # 20 minutes
readonly DRAIN_TIMEOUT=180        # 3 minutes
readonly MIN_HEALTHY_PODS=2       # Minimum pods to maintain service

log_info() { echo -e "[$(date '+%H:%M:%S')] INFO: $*"; }
log_success() { echo -e "[$(date '+%H:%M:%S')] SUCCESS: $*"; }
log_warn() { echo -e "[$(date '+%H:%M:%S')] WARN: $*"; }
log_error() { echo -e "[$(date '+%H:%M:%S')] ERROR: $*"; }

# Pre-deployment environment validation
validate_zero_downtime_readiness() {
    local new_image="$1"
    
    log_info "Validating zero-downtime deployment readiness..."
    
    # Check current pod count
    local current_pods
    current_pods=$(kubectl get pods -n "$NAMESPACE" -l "app=$APP_NAME" --field-selector=status.phase=Running -o name | wc -l)
    
    if [[ "$current_pods" -lt "$MIN_HEALTHY_PODS" ]]; then
        log_error "Insufficient healthy pods ($current_pods) for zero-downtime deployment"
        return 1
    fi
    
    # Verify PodDisruptionBudget
    if ! kubectl get pdb "${APP_NAME}-pdb" -n "$NAMESPACE" >/dev/null 2>&1; then
        log_error "PodDisruptionBudget required for zero-downtime deployment"
        return 1
    fi
    
    # Check load balancer configuration
    local service_type
    service_type=$(kubectl get service "${APP_NAME}-service" -n "$NAMESPACE" -o jsonpath='{.spec.type}')
    
    if [[ "$service_type" != "LoadBalancer" ]] && [[ "$service_type" != "ClusterIP" ]]; then
        log_warn "Service type $service_type may not support zero-downtime deployments"
    fi
    
    # Validate image accessibility
    if ! docker manifest inspect "$new_image" >/dev/null 2>&1; then
        log_error "Image $new_image not accessible"
        return 1
    fi
    
    # Check cluster resource capacity
    validate_cluster_resources
    
    log_success "Zero-downtime readiness validation passed"
}

# Validate cluster has sufficient resources
validate_cluster_resources() {
    log_info "Validating cluster resource capacity..."
    
    # Get resource requests for new deployment
    local deployment_info
    deployment_info=$(kubectl get deployment "$APP_NAME" -n "$NAMESPACE" -o json)
    
    local cpu_request memory_request replica_count
    cpu_request=$(echo "$deployment_info" | jq -r '.spec.template.spec.containers[0].resources.requests.cpu // "200m"')
    memory_request=$(echo "$deployment_info" | jq -r '.spec.template.spec.containers[0].resources.requests.memory // "384Mi"')
    replica_count=$(echo "$deployment_info" | jq -r '.spec.replicas')
    
    # Calculate additional resources needed during rolling update
    local max_surge
    max_surge=$(echo "$deployment_info" | jq -r '.spec.strategy.rollingUpdate.maxSurge // "25%"')
    
    if [[ "$max_surge" == *"%" ]]; then
        local surge_percent=${max_surge%\%}
        local additional_pods=$(( replica_count * surge_percent / 100 ))
    else
        local additional_pods=$max_surge
    fi
    
    log_info "Resource requirements: ${additional_pods} additional pods (CPU: $cpu_request, Memory: $memory_request each)"
    
    # Check node capacity (simplified check)
    local available_nodes
    available_nodes=$(kubectl get nodes --no-headers | grep -c Ready || echo "0")
    
    if [[ "$available_nodes" -lt 2 ]]; then
        log_warn "Limited node capacity may affect zero-downtime deployment"
    fi
}

# Gracefully drain traffic from old pods
graceful_traffic_drain() {
    local pod_name="$1"
    local drain_timeout="$2"
    
    log_info "Draining traffic from pod: $pod_name"
    
    # Enable circuit breaker on the pod
    local pod_ip
    pod_ip=$(kubectl get pod "$pod_name" -n "$NAMESPACE" -o jsonpath='{.status.podIP}')
    
    if [[ -n "$pod_ip" ]]; then
        # Open circuit breaker to stop accepting new requests
        if curl -s -X POST "http://${pod_ip}:8080${CIRCUIT_BREAKER_ENDPOINT}/open" >/dev/null 2>&1; then
            log_info "Circuit breaker opened for pod $pod_name"
        else
            log_warn "Failed to open circuit breaker for pod $pod_name"
        fi
        
        # Wait for connection draining
        local end_time=$(($(date +%s) + drain_timeout))
        
        while [[ $(date +%s) -lt $end_time ]]; do
            # Check active connections (simplified)
            local health_status
            health_status=$(curl -s "http://${pod_ip}:8080/health" | jq -r '.status // "unknown"' 2>/dev/null || echo "unknown")
            
            if [[ "$health_status" == "draining" ]]; then
                log_info "Pod $pod_name is draining connections..."
                sleep 10
            else
                break
            fi
        done
    fi
    
    log_info "Traffic drain completed for pod: $pod_name"
}

# Execute zero-downtime deployment
execute_zero_downtime_deployment() {
    local new_image="$1"
    
    log_info "Executing zero-downtime deployment to $new_image"
    
    # Get current deployment configuration
    local current_deployment
    current_deployment=$(kubectl get deployment "$APP_NAME" -n "$NAMESPACE" -o json)
    
    local current_replicas max_unavailable max_surge
    current_replicas=$(echo "$current_deployment" | jq -r '.spec.replicas')
    max_unavailable=$(echo "$current_deployment" | jq -r '.spec.strategy.rollingUpdate.maxUnavailable // "1"')
    max_surge=$(echo "$current_deployment" | jq -r '.spec.strategy.rollingUpdate.maxSurge // "1"')
    
    log_info "Deployment config: replicas=$current_replicas, maxUnavailable=$max_unavailable, maxSurge=$max_surge"
    
    # Store deployment state for potential rollback
    kubectl get deployment "$APP_NAME" -n "$NAMESPACE" -o yaml > "/tmp/${APP_NAME}-pre-deployment.yaml"
    
    # Update deployment image
    kubectl set image deployment/"$APP_NAME" \
            "$APP_NAME=$new_image" \
            -n "$NAMESPACE"
    
    # Annotate deployment
    kubectl annotate deployment/"$APP_NAME" \
            deployment.kubernetes.io/change-cause="Zero-downtime deployment to $new_image" \
            deployment.company.com/deployed-by="$(whoami)" \
            deployment.company.com/deployment-time="$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)" \
            -n "$NAMESPACE" --overwrite
    
    # Monitor deployment progress with enhanced validation
    monitor_zero_downtime_rollout "$new_image"
}

# Monitor zero-downtime rollout with comprehensive checks
monitor_zero_downtime_rollout() {
    local new_image="$1"
    
    log_info "Monitoring zero-downtime rollout progress..."
    
    local deployment_start=$(date +%s)
    local end_time=$((deployment_start + DEPLOYMENT_TIMEOUT))
    local check_interval=15
    local consecutive_healthy_checks=0
    local required_consecutive_checks=3
    
    while [[ $(date +%s) -lt $end_time ]]; do
        # Get deployment status
        local deployment_json
        deployment_json=$(kubectl get deployment "$APP_NAME" -n "$NAMESPACE" -o json)
        
        local desired_replicas ready_replicas available_replicas updated_replicas
        desired_replicas=$(echo "$deployment_json" | jq -r '.spec.replicas')
        ready_replicas=$(echo "$deployment_json" | jq -r '.status.readyReplicas // 0')
        available_replicas=$(echo "$deployment_json" | jq -r '.status.availableReplicas // 0')
        updated_replicas=$(echo "$deployment_json" | jq -r '.status.updatedReplicas // 0')
        
        # Check service availability
        local healthy_endpoints
        healthy_endpoints=$(kubectl get endpoints "${APP_NAME}-service" -n "$NAMESPACE" \
                          -o jsonpath='{.subsets[*].addresses[*].ip}' | wc -w)
        
        log_info "Status: Ready=$ready_replicas/$desired_replicas, Available=$available_replicas, Updated=$updated_replicas, Endpoints=$healthy_endpoints"
        
        # Validate zero-downtime criteria
        local is_healthy=true
        
        # Must maintain minimum available replicas
        if [[ "$available_replicas" -lt "$MIN_HEALTHY_PODS" ]]; then
            log_warn "Available replicas ($available_replicas) below minimum threshold ($MIN_HEALTHY_PODS)"
            is_healthy=false
        fi
        
        # Must have healthy endpoints for service
        if [[ "$healthy_endpoints" -eq 0 ]]; then
            log_error "No healthy endpoints available - service is down!"
            return 1
        fi
        
        # Validate service responsiveness
        if ! validate_service_responsiveness; then
            log_warn "Service responsiveness check failed"
            is_healthy=false
        fi
        
        # Check if rollout is complete and healthy
        if [[ "$ready_replicas" -eq "$desired_replicas" ]] && \
           [[ "$updated_replicas" -eq "$desired_replicas" ]] && \
           [[ "$is_healthy" == "true" ]]; then
            ((consecutive_healthy_checks++))
            
            if [[ "$consecutive_healthy_checks" -ge "$required_consecutive_checks" ]]; then
                local deployment_duration=$(($(date +%s) - deployment_start))
                log_success "Zero-downtime deployment completed in ${deployment_duration}s"
                return 0
            fi
        else
            consecutive_healthy_checks=0
        fi
        
        # Check for rollout failure conditions
        local rollout_condition
        rollout_condition=$(echo "$deployment_json" | jq -r '.status.conditions[]? | select(.type=="Progressing")')
        
        if [[ -n "$rollout_condition" ]]; then
            local condition_status condition_reason
            condition_status=$(echo "$rollout_condition" | jq -r '.status')
            condition_reason=$(echo "$rollout_condition" | jq -r '.reason // ""')
            
            if [[ "$condition_status" == "False" ]] && [[ "$condition_reason" == "ProgressDeadlineExceeded" ]]; then
                log_error "Deployment progress deadline exceeded"
                return 1
            fi
        fi
        
        sleep $check_interval
    done
    
    log_error "Zero-downtime deployment monitoring timed out"
    return 1
}

# Validate service responsiveness during deployment
validate_service_responsiveness() {
    local service_ip
    service_ip=$(kubectl get service "${APP_NAME}-service" -n "$NAMESPACE" -o jsonpath='{.spec.clusterIP}')
    
    if [[ -z "$service_ip" ]]; then
        log_warn "Unable to get service IP for responsiveness check"
        return 1
    fi
    
    # Perform multiple health checks
    local success_count=0
    local total_checks=3
    
    for i in $(seq 1 $total_checks); do
        if curl -sf --max-time 5 "http://${service_ip}${LB_HEALTH_CHECK_PATH}" >/dev/null 2>&1; then
            ((success_count++))
        fi
        
        [[ $i -lt $total_checks ]] && sleep 2
    done
    
    # Require majority of checks to pass
    local success_rate=$((success_count * 100 / total_checks))
    
    if [[ $success_rate -lt 67 ]]; then  # Less than 67% success
        return 1
    fi
    
    return 0
}

# Comprehensive post-deployment validation
validate_zero_downtime_success() {
    local validation_duration="${1:-300}"  # 5 minutes default
    
    log_info "Validating zero-downtime deployment success for ${validation_duration}s..."
    
    local end_time=$(($(date +%s) + validation_duration))
    local total_checks=0
    local failed_checks=0
    local response_times=()
    
    while [[ $(date +%s) -lt $end_time ]]; do
        ((total_checks++))
        
        # Health check with timing
        local service_ip
        service_ip=$(kubectl get service "${APP_NAME}-service" -n "$NAMESPACE" -o jsonpath='{.spec.clusterIP}')
        
        local response_time
        response_time=$(curl -s -w "%{time_total}" -o /dev/null --max-time 10 "http://${service_ip}${LB_HEALTH_CHECK_PATH}" 2>/dev/null || echo "999")
        
        if [[ "$response_time" == "999" ]] || (( $(echo "$response_time > 5.0" | bc -l) )); then
            ((failed_checks++))
            log_warn "Health check failed or slow (${response_time}s) - check ${failed_checks}/${total_checks}"
        else
            response_times+=("$response_time")
        fi
        
        # Check pod readiness
        local unready_pods
        unready_pods=$(kubectl get pods -n "$NAMESPACE" -l "app=$APP_NAME" \
                      --field-selector=status.phase!=Running -o name | wc -l)
        
        if [[ "$unready_pods" -gt 0 ]]; then
            ((failed_checks++))
            log_warn "Found $unready_pods unready pods"
        fi
        
        # Early failure detection
        local failure_rate=$((failed_checks * 100 / total_checks))
        if [[ $total_checks -gt 10 ]] && [[ $failure_rate -gt 10 ]]; then
            log_error "High failure rate detected: ${failure_rate}%"
            return 1
        fi
        
        sleep 30
    done
    
    # Calculate final metrics
    local final_failure_rate=$((failed_checks * 100 / total_checks))
    local avg_response_time=0
    
    if [[ ${#response_times[@]} -gt 0 ]]; then
        local sum=0
        for time in "${response_times[@]}"; do
            sum=$(echo "$sum + $time" | bc)
        done
        avg_response_time=$(echo "scale=3; $sum / ${#response_times[@]}" | bc)
    fi
    
    log_info "Validation completed: ${final_failure_rate}% failure rate, avg response time: ${avg_response_time}s"
    
    # Success criteria
    if [[ $final_failure_rate -le 2 ]]; then  # <= 2% failure rate
        log_success "Zero-downtime deployment validation passed"
        return 0
    else
        log_error "Zero-downtime deployment validation failed: ${final_failure_rate}% failure rate"
        return 1
    fi
}

# Emergency rollback with zero-downtime principles
emergency_zero_downtime_rollback() {
    local reason="${1:-Emergency rollback initiated}"
    
    log_error "Performing emergency zero-downtime rollback: $reason"
    
    # Get rollback target
    local rollback_deployment
    if [[ -f "/tmp/${APP_NAME}-pre-deployment.yaml" ]]; then
        rollback_deployment="/tmp/${APP_NAME}-pre-deployment.yaml"
    else
        log_warn "Pre-deployment state not found, using kubectl rollback"
        kubectl rollout undo deployment/"$APP_NAME" -n "$NAMESPACE"
        
        # Wait for rollback
        if kubectl rollout status deployment/"$APP_NAME" -n "$NAMESPACE" --timeout=300s; then
            log_success "Emergency rollback completed"
            send_emergency_notification "$reason" "SUCCESS"
            return 0
        else
            log_error "Emergency rollback failed"
            send_emergency_notification "$reason" "FAILED"
            return 1
        fi
    fi
    
    # Apply previous deployment state
    kubectl apply -f "$rollback_deployment"
    
    # Monitor rollback progress
    if ! kubectl rollout status deployment/"$APP_NAME" -n "$NAMESPACE" --timeout=600s; then
        log_error "Emergency rollback timed out or failed"
        send_emergency_notification "$reason" "FAILED"
        return 1
    fi
    
    # Validate rollback success
    if validate_service_responsiveness; then
        log_success "Emergency rollback completed successfully"
        send_emergency_notification "$reason" "SUCCESS"
    else
        log_error "Emergency rollback completed but service is not responsive"
        send_emergency_notification "$reason" "PARTIAL"
        return 1
    fi
}

# Send emergency notifications
send_emergency_notification() {
    local reason="$1"
    local status="$2"
    
    # Critical alert for emergency situations
    if [[ -n "${PAGERDUTY_INTEGRATION_KEY:-}" ]]; then
        local severity="critical"
        [[ "$status" == "SUCCESS" ]] && severity="warning"
        
        local payload=$(cat <<EOF
{
  "routing_key": "$PAGERDUTY_INTEGRATION_KEY",
  "event_action": "trigger",
  "payload": {
    "summary": "Zero-Downtime Deployment Emergency: $APP_NAME - $status",
    "source": "zero-downtime-deployment",
    "severity": "$severity",
    "custom_details": {
      "reason": "$reason",
      "status": "$status",
      "application": "$APP_NAME",
      "namespace": "$NAMESPACE"
    }
  }
}
EOF
)
        
        curl -X POST -H "Content-Type: application/json" \
             -d "$payload" \
             "https://events.pagerduty.com/v2/enqueue" >/dev/null 2>&1 || true
    fi
    
    # Slack notification
    if [[ -n "${SLACK_WEBHOOK_URL:-}" ]]; then
        local color="danger"
        [[ "$status" == "SUCCESS" ]] && color="warning"
        
        local payload=$(cat <<EOF
{
    "attachments": [
        {
            "color": "$color",
            "title": "🚨 Zero-Downtime Deployment Emergency",
            "fields": [
                {
                    "title": "Application",
                    "value": "$APP_NAME",
                    "short": true
                },
                {
                    "title": "Status",
                    "value": "$status",
                    "short": true
                },
                {
                    "title": "Reason",
                    "value": "$reason",
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
             "$SLACK_WEBHOOK_URL" >/dev/null 2>&1 || true
    fi
}

# Main function
main() {
    local command="${1:-deploy}"
    local new_image="${2:-}"
    
    case "$command" in
        "deploy")
            [[ -z "$new_image" ]] && { log_error "Image tag required"; exit 1; }
            
            log_info "Starting zero-downtime deployment for $APP_NAME to $new_image"
            
            # Validate environment
            if ! validate_zero_downtime_readiness "$new_image"; then
                log_error "Environment not ready for zero-downtime deployment"
                exit 1
            fi
            
            # Execute deployment
            if ! execute_zero_downtime_deployment "$new_image"; then
                log_error "Zero-downtime deployment failed"
                emergency_zero_downtime_rollback "Deployment execution failed"
                exit 1
            fi
            
            # Post-deployment validation
            if ! validate_zero_downtime_success 300; then
                log_error "Post-deployment validation failed"
                emergency_zero_downtime_rollback "Post-deployment validation failed"
                exit 1
            fi
            
            log_success "Zero-downtime deployment completed successfully"
            ;;
            
        "rollback")
            emergency_zero_downtime_rollback "${2:-Manual emergency rollback}"
            ;;
            
        "validate")
            validate_zero_downtime_readiness "${2:-current}"
            ;;
            
        "monitor")
            monitor_zero_downtime_rollout "${2:-current}"
            ;;
            
        *)
            cat <<EOF
Zero-Downtime Deployment Tool

Usage: $0 <command> [options]

Commands:
  deploy <image-tag>      - Execute zero-downtime deployment
  rollback [reason]       - Emergency rollback with zero-downtime
  validate [image-tag]    - Validate zero-downtime readiness
  monitor [image-tag]     - Monitor deployment progress

Examples:
  $0 deploy web-app:v1.2.3
  $0 rollback "Service degradation detected"
  $0 validate web-app:v1.2.4
  $0 monitor
EOF
            ;;
    esac
}

# Run main function if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
```

This provides comprehensive zero-downtime deployment implementation with circuit breaker patterns, traffic draining, comprehensive monitoring, and emergency rollback capabilities - ensuring true zero-downtime deployments in production environments.