## Production Rolling Deployment Implementation

### Rolling Deployment Strategy

#### Rolling Update Configuration
```yaml
# deployments/web-app-rolling.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-app
  namespace: production
  labels:
    app: web-app
    deployment-strategy: rolling
spec:
  replicas: 6
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 1        # Only 1 pod can be unavailable
      maxSurge: 2              # Can have 2 extra pods during update
  selector:
    matchLabels:
      app: web-app
  template:
    metadata:
      labels:
        app: web-app
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
        - containerPort: 9090  # Metrics
        env:
        - name: DEPLOYMENT_STRATEGY
          value: "rolling"
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
          initialDelaySeconds: 45
          periodSeconds: 15
          timeoutSeconds: 5
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 10
          periodSeconds: 5
          timeoutSeconds: 3
          successThreshold: 1
          failureThreshold: 3
        # Graceful shutdown
        lifecycle:
          preStop:
            exec:
              command:
              - /bin/sh
              - -c
              - sleep 20  # Allow load balancer to drain connections
      terminationGracePeriodSeconds: 30
      # Pod disruption budget
      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            podAffinityTerm:
              labelSelector:
                matchExpressions:
                - key: app
                  operator: In
                  values:
                  - web-app
              topologyKey: kubernetes.io/hostname
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
  maxUnavailable: 1  # Maintain availability during rolling updates
---
apiVersion: v1
kind: Service
metadata:
  name: web-app-service
  namespace: production
  labels:
    app: web-app
spec:
  selector:
    app: web-app
  ports:
  - name: http
    protocol: TCP
    port: 80
    targetPort: 8080
  - name: metrics
    protocol: TCP
    port: 9090
    targetPort: 9090
  type: ClusterIP
```

### Automated Rolling Deployment Script

```bash
#!/bin/bash
# scripts/rolling-deploy.sh - Production rolling deployment automation

set -euo pipefail

readonly APP_NAME="web-app"
readonly NAMESPACE="production"
readonly DEPLOYMENT_TIMEOUT=900  # 15 minutes
readonly HEALTH_CHECK_DURATION=300  # 5 minutes
readonly ROLLBACK_THRESHOLD_PERCENT=5  # 5% failure rate triggers rollback

log_info() { echo -e "[$(date '+%H:%M:%S')] INFO: $*"; }
log_success() { echo -e "[$(date '+%H:%M:%S')] SUCCESS: $*"; }
log_warn() { echo -e "[$(date '+%H:%M:%S')] WARN: $*"; }
log_error() { echo -e "[$(date '+%H:%M:%S')] ERROR: $*"; }

# Pre-deployment validation
validate_deployment_readiness() {
    local new_image="$1"
    
    log_info "Validating deployment readiness..."
    
    # Check if image exists
    if ! docker manifest inspect "$new_image" >/dev/null 2>&1; then
        log_error "Image $new_image not found or not accessible"
        return 1
    fi
    
    # Check cluster resources
    local node_capacity
    node_capacity=$(kubectl top nodes --no-headers | awk '{sum+=$3} END {print sum}')
    
    if [[ -z "$node_capacity" ]]; then
        log_warn "Unable to retrieve node capacity metrics"
    fi
    
    # Verify PodDisruptionBudget exists
    if ! kubectl get pdb "${APP_NAME}-pdb" -n "$NAMESPACE" >/dev/null 2>&1; then
        log_warn "PodDisruptionBudget not found - deployment may cause availability issues"
    fi
    
    # Check current deployment health
    local unhealthy_pods
    unhealthy_pods=$(kubectl get pods -n "$NAMESPACE" -l "app=$APP_NAME" \
                    --field-selector=status.phase!=Running -o name 2>/dev/null | wc -l)
    
    if [[ "$unhealthy_pods" -gt 0 ]]; then
        log_error "Found $unhealthy_pods unhealthy pods - fix before deploying"
        return 1
    fi
    
    log_success "Deployment readiness validation completed"
}

# Execute rolling deployment
execute_rolling_deployment() {
    local new_image="$1"
    local current_replicas="$2"
    
    log_info "Starting rolling deployment to $new_image with $current_replicas replicas"
    
    # Record deployment start time
    local deployment_start=$(date +%s)
    
    # Update deployment image
    kubectl set image deployment/"$APP_NAME" \
            "$APP_NAME=$new_image" \
            -n "$NAMESPACE"
    
    # Annotate deployment with metadata
    kubectl annotate deployment/"$APP_NAME" \
            deployment.kubernetes.io/change-cause="Rolling update to $new_image at $(date)" \
            -n "$NAMESPACE"
    
    log_info "Deployment triggered, monitoring rollout progress..."
    
    # Monitor rollout with timeout
    if ! kubectl rollout status deployment/"$APP_NAME" \
         -n "$NAMESPACE" --timeout="${DEPLOYMENT_TIMEOUT}s"; then
        log_error "Rolling deployment timed out or failed"
        return 1
    fi
    
    local deployment_duration=$(($(date +%s) - deployment_start))
    log_success "Rolling deployment completed in ${deployment_duration}s"
    
    return 0
}

# Monitor deployment progress
monitor_rollout_progress() {
    local monitoring_duration="$1"
    
    log_info "Monitoring rollout progress for ${monitoring_duration}s..."
    
    local end_time=$(($(date +%s) + monitoring_duration))
    local check_interval=15
    
    while [[ $(date +%s) -lt $end_time ]]; do
        # Get deployment status
        local deployment_status
        deployment_status=$(kubectl get deployment "$APP_NAME" -n "$NAMESPACE" -o json)
        
        local ready_replicas available_replicas updated_replicas desired_replicas
        ready_replicas=$(echo "$deployment_status" | jq -r '.status.readyReplicas // 0')
        available_replicas=$(echo "$deployment_status" | jq -r '.status.availableReplicas // 0')
        updated_replicas=$(echo "$deployment_status" | jq -r '.status.updatedReplicas // 0')
        desired_replicas=$(echo "$deployment_status" | jq -r '.spec.replicas')
        
        log_info "Progress: Ready=$ready_replicas/$desired_replicas, Available=$available_replicas, Updated=$updated_replicas"
        
        # Check if rollout is complete
        if [[ "$ready_replicas" -eq "$desired_replicas" ]] && \
           [[ "$updated_replicas" -eq "$desired_replicas" ]]; then
            log_success "Rollout completed successfully"
            break
        fi
        
        # Check for rollout issues
        local rollout_conditions
        rollout_conditions=$(echo "$deployment_status" | jq -r '.status.conditions[]?')
        
        if echo "$rollout_conditions" | jq -r 'select(.type=="Progressing" and .status=="False") | .reason' | grep -q "ProgressDeadlineExceeded"; then
            log_error "Rollout progress deadline exceeded"
            return 1
        fi
        
        sleep $check_interval
    done
}

# Health validation post-deployment
validate_deployment_health() {
    local validation_duration="$1"
    
    log_info "Validating deployment health for ${validation_duration}s..."
    
    local end_time=$(($(date +%s) + validation_duration))
    local total_checks=0
    local failed_checks=0
    
    while [[ $(date +%s) -lt $end_time ]]; do
        ((total_checks++))
        
        # Get service endpoint
        local service_ip
        service_ip=$(kubectl get service "${APP_NAME}-service" -n "$NAMESPACE" -o jsonpath='{.spec.clusterIP}')
        
        # Health check
        if ! curl -sf "http://${service_ip}/health" >/dev/null 2>&1; then
            ((failed_checks++))
            log_warn "Health check failed (${failed_checks}/${total_checks})"
        fi
        
        # Check pod readiness
        local unready_pods
        unready_pods=$(kubectl get pods -n "$NAMESPACE" -l "app=$APP_NAME" \
                      -o jsonpath='{.items[?(@.status.phase!="Running")].metadata.name}')
        
        if [[ -n "$unready_pods" ]]; then
            ((failed_checks++))
            log_warn "Unready pods detected: $unready_pods"
        fi
        
        # Calculate failure rate
        local failure_rate=$((failed_checks * 100 / total_checks))
        
        if [[ $failure_rate -gt $ROLLBACK_THRESHOLD_PERCENT ]]; then
            log_error "Failure rate ${failure_rate}% exceeds threshold ${ROLLBACK_THRESHOLD_PERCENT}%"
            return 1
        fi
        
        sleep 30
    done
    
    local final_failure_rate=$((failed_checks * 100 / total_checks))
    log_info "Health validation completed: ${final_failure_rate}% failure rate"
    
    if [[ $final_failure_rate -gt $ROLLBACK_THRESHOLD_PERCENT ]]; then
        log_error "Final failure rate too high: ${final_failure_rate}%"
        return 1
    fi
    
    log_success "Deployment health validation passed"
    return 0
}

# Performance validation
validate_deployment_performance() {
    log_info "Validating deployment performance..."
    
    # Check average response time
    local service_ip
    service_ip=$(kubectl get service "${APP_NAME}-service" -n "$NAMESPACE" -o jsonpath='{.spec.clusterIP}')
    
    local total_time=0
    local request_count=10
    
    for i in $(seq 1 $request_count); do
        local response_time
        response_time=$(curl -s -w "%{time_total}" -o /dev/null "http://${service_ip}/health" || echo "999")
        total_time=$(echo "$total_time + $response_time" | bc)
    done
    
    local avg_response_time
    avg_response_time=$(echo "scale=3; $total_time / $request_count" | bc)
    
    log_info "Average response time: ${avg_response_time}s"
    
    # Check if response time is acceptable (< 2s)
    if (( $(echo "$avg_response_time > 2.0" | bc -l) )); then
        log_warn "Response time degradation detected: ${avg_response_time}s"
        return 1
    fi
    
    # Get resource utilization from metrics
    if command -v curl >/dev/null && [[ -n "${PROMETHEUS_URL:-}" ]]; then
        # Check CPU utilization
        local cpu_usage
        cpu_usage=$(curl -s "${PROMETHEUS_URL}/api/v1/query?query=avg(rate(container_cpu_usage_seconds_total{pod=~\"${APP_NAME}.*\"}[5m]))*100" | \
                   jq -r '.data.result[0].value[1] // "0"' 2>/dev/null || echo "0")
        
        log_info "Average CPU utilization: ${cpu_usage}%"
        
        if (( $(echo "$cpu_usage > 80.0" | bc -l) )); then
            log_warn "High CPU utilization detected: ${cpu_usage}%"
        fi
        
        # Check memory utilization
        local memory_usage
        memory_usage=$(curl -s "${PROMETHEUS_URL}/api/v1/query?query=avg(container_memory_usage_bytes{pod=~\"${APP_NAME}.*\"}/container_spec_memory_limit_bytes)*100" | \
                      jq -r '.data.result[0].value[1] // "0"' 2>/dev/null || echo "0")
        
        log_info "Average memory utilization: ${memory_usage}%"
        
        if (( $(echo "$memory_usage > 80.0" | bc -l) )); then
            log_warn "High memory utilization detected: ${memory_usage}%"
        fi
    fi
    
    log_success "Performance validation completed"
}

# Rollback deployment
rollback_deployment() {
    local reason="${1:-Manual rollback requested}"
    
    log_error "Rolling back deployment: $reason"
    
    # Get current revision
    local current_revision
    current_revision=$(kubectl rollout history deployment/"$APP_NAME" -n "$NAMESPACE" | tail -1 | awk '{print $1}')
    
    # Rollback to previous revision
    kubectl rollout undo deployment/"$APP_NAME" -n "$NAMESPACE"
    
    # Wait for rollback to complete
    if ! kubectl rollout status deployment/"$APP_NAME" -n "$NAMESPACE" --timeout=300s; then
        log_error "Rollback failed or timed out"
        return 1
    fi
    
    # Verify rollback success
    local rollback_revision
    rollback_revision=$(kubectl rollout history deployment/"$APP_NAME" -n "$NAMESPACE" | tail -1 | awk '{print $1}')
    
    log_success "Rollback completed from revision $current_revision to $rollback_revision"
    
    # Send notification
    send_rollback_notification "$reason" "$current_revision" "$rollback_revision"
}

# Generate deployment report
generate_deployment_report() {
    local deployment_result="$1"
    local new_image="$2"
    local deployment_duration="$3"
    
    local report_file="/tmp/rolling-deployment-report-$(date +%Y%m%d_%H%M%S).json"
    
    # Get deployment details
    local deployment_info
    deployment_info=$(kubectl get deployment "$APP_NAME" -n "$NAMESPACE" -o json)
    
    local current_replicas ready_replicas
    current_replicas=$(echo "$deployment_info" | jq -r '.spec.replicas')
    ready_replicas=$(echo "$deployment_info" | jq -r '.status.readyReplicas // 0')
    
    # Create report
    cat > "$report_file" <<EOF
{
  "deployment_report": {
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)",
    "application": "$APP_NAME",
    "namespace": "$NAMESPACE",
    "strategy": "rolling",
    "result": "$deployment_result",
    "image": "$new_image",
    "duration_seconds": $deployment_duration,
    "replicas": {
      "desired": $current_replicas,
      "ready": $ready_replicas
    },
    "rollout_history": [
$(kubectl rollout history deployment/"$APP_NAME" -n "$NAMESPACE" --output json | jq -r '.items[] | "      {\"revision\": \(.revision), \"change_cause\": \"\(.metadata.annotations["deployment.kubernetes.io/change-cause"] // "")\"}"' | tail -5)
    ]
  }
}
EOF
    
    log_info "Deployment report generated: $report_file"
    
    # Send to monitoring system if configured
    if [[ -n "${DEPLOYMENT_WEBHOOK:-}" ]]; then
        curl -X POST -H "Content-Type: application/json" \
             -d "@$report_file" \
             "$DEPLOYMENT_WEBHOOK" || log_warn "Failed to send report to webhook"
    fi
}

# Send notifications
send_rollback_notification() {
    local reason="$1"
    local from_revision="$2" 
    local to_revision="$3"
    
    if [[ -n "${SLACK_WEBHOOK_URL:-}" ]]; then
        local payload=$(cat <<EOF
{
    "attachments": [
        {
            "color": "danger",
            "title": "🔄 Rolling Deployment Rollback",
            "fields": [
                {
                    "title": "Application",
                    "value": "$APP_NAME",
                    "short": true
                },
                {
                    "title": "Reason",
                    "value": "$reason",
                    "short": true
                },
                {
                    "title": "Rollback",
                    "value": "Revision $from_revision → $to_revision",
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
            
            local deployment_start=$(date +%s)
            
            # Get current replica count
            local current_replicas
            current_replicas=$(kubectl get deployment "$APP_NAME" -n "$NAMESPACE" -o jsonpath='{.spec.replicas}' 2>/dev/null || echo "3")
            
            log_info "Starting rolling deployment for $APP_NAME"
            
            # Validate readiness
            if ! validate_deployment_readiness "$new_image"; then
                exit 1
            fi
            
            # Execute deployment
            if ! execute_rolling_deployment "$new_image" "$current_replicas"; then
                rollback_deployment "Deployment execution failed"
                exit 1
            fi
            
            # Monitor progress
            if ! monitor_rollout_progress 180; then
                rollback_deployment "Rollout monitoring failed"
                exit 1
            fi
            
            # Validate health
            if ! validate_deployment_health "$HEALTH_CHECK_DURATION"; then
                rollback_deployment "Health validation failed"
                exit 1
            fi
            
            # Validate performance
            if ! validate_deployment_performance; then
                log_warn "Performance validation failed, but continuing deployment"
            fi
            
            local deployment_duration=$(($(date +%s) - deployment_start))
            generate_deployment_report "SUCCESS" "$new_image" "$deployment_duration"
            
            log_success "Rolling deployment completed successfully in ${deployment_duration}s"
            ;;
            
        "rollback")
            rollback_deployment "${2:-Manual rollback}"
            ;;
            
        "status")
            kubectl rollout status deployment/"$APP_NAME" -n "$NAMESPACE"
            kubectl rollout history deployment/"$APP_NAME" -n "$NAMESPACE"
            ;;
            
        "history")
            kubectl rollout history deployment/"$APP_NAME" -n "$NAMESPACE" --revision="${2:-}"
            ;;
            
        *)
            cat <<EOF
Rolling Deployment Tool

Usage: $0 <command> [options]

Commands:
  deploy <image-tag>        - Execute rolling deployment
  rollback [reason]         - Rollback to previous revision
  status                    - Show rollout status
  history [revision]        - Show rollout history

Examples:
  $0 deploy web-app:v1.2.3
  $0 rollback "Health check failed"
  $0 status
  $0 history 5
EOF
            ;;
    esac
}

# Run main function if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
```

This provides comprehensive rolling deployment implementation with progressive rollout monitoring, health validation, performance checks, and automated rollback capabilities - all production-ready patterns for safe, zero-downtime deployments.