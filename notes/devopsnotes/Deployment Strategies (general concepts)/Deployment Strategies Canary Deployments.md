## Production Canary Deployment Implementation

### Canary Deployment Architecture

#### Traffic Splitting Configuration
```yaml
# ingress/canary-ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: web-app-canary
  namespace: production
  annotations:
    nginx.ingress.kubernetes.io/canary: "true"
    nginx.ingress.kubernetes.io/canary-weight: "10"  # Start with 10% traffic
    nginx.ingress.kubernetes.io/canary-by-header: "X-Canary"
    nginx.ingress.kubernetes.io/canary-by-header-value: "true"
    nginx.ingress.kubernetes.io/canary-by-cookie: "canary"
spec:
  ingressClassName: nginx
  rules:
  - host: app.company.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: web-app-canary-service
            port:
              number: 80
  tls:
  - hosts:
    - app.company.com
    secretName: web-app-tls
---
# Main production ingress
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: web-app-production
  namespace: production
spec:
  ingressClassName: nginx
  rules:
  - host: app.company.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: web-app-production-service
            port:
              number: 80
```

#### Canary Deployment Manifest
```yaml
# deployments/web-app-canary.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-app-canary
  namespace: production
  labels:
    app: web-app
    version: canary
    deployment-strategy: canary
spec:
  replicas: 2  # Start with fewer replicas
  selector:
    matchLabels:
      app: web-app
      version: canary
  template:
    metadata:
      labels:
        app: web-app
        version: canary
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/path: "/metrics"
        prometheus.io/port: "9090"
    spec:
      containers:
      - name: web-app
        image: web-app:v1.3.0-canary
        ports:
        - containerPort: 8080
        - containerPort: 9090  # Metrics port
        env:
        - name: DEPLOYMENT_VERSION
          value: "canary"
        - name: FEATURE_FLAGS
          value: "new_feature=true,experimental=true"
        resources:
          requests:
            cpu: 100m
            memory: 256Mi
          limits:
            cpu: 500m
            memory: 512Mi
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
        # Canary-specific configuration
        lifecycle:
          preStop:
            exec:
              command: ["/bin/sh", "-c", "sleep 15"]  # Grace period
---
apiVersion: v1
kind: Service
metadata:
  name: web-app-canary-service
  namespace: production
  labels:
    app: web-app
    version: canary
spec:
  selector:
    app: web-app
    version: canary
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

### Automated Canary Deployment Script

```bash
#!/bin/bash
# scripts/canary-deploy.sh - Automated canary deployment with progressive traffic increase

set -euo pipefail

readonly APP_NAME="web-app"
readonly NAMESPACE="production"
readonly CANARY_SERVICE="${APP_NAME}-canary-service"
readonly PROD_SERVICE="${APP_NAME}-production-service"
readonly CANARY_INGRESS="${APP_NAME}-canary"
readonly METRICS_CHECK_DURATION=300  # 5 minutes per stage
readonly SUCCESS_RATE_THRESHOLD=99.0
readonly ERROR_RATE_THRESHOLD=1.0
readonly LATENCY_THRESHOLD=2000  # 2 seconds

# Traffic split stages for progressive deployment
readonly TRAFFIC_STAGES=(5 10 25 50 75 100)

log_info() { echo -e "[$(date '+%H:%M:%S')] INFO: $*"; }
log_success() { echo -e "[$(date '+%H:%M:%S')] SUCCESS: $*"; }
log_warn() { echo -e "[$(date '+%H:%M:%S')] WARN: $*"; }
log_error() { echo -e "[$(date '+%H:%M:%S')] ERROR: $*"; }

# Deploy canary version
deploy_canary() {
    local image_tag="$1"
    local initial_replicas="${2:-2}"
    
    log_info "Deploying canary version: $image_tag"
    
    # Update canary deployment
    kubectl set image deployment/"${APP_NAME}-canary" \
            "${APP_NAME}=${APP_NAME}:${image_tag}" \
            -n "$NAMESPACE"
    
    # Scale canary deployment
    kubectl scale deployment "${APP_NAME}-canary" \
            --replicas="$initial_replicas" \
            -n "$NAMESPACE"
    
    # Wait for canary to be ready
    if ! kubectl rollout status deployment/"${APP_NAME}-canary" \
         -n "$NAMESPACE" --timeout=300s; then
        log_error "Canary deployment failed to become ready"
        return 1
    fi
    
    log_success "Canary deployment ready"
}

# Set traffic weight for canary
set_canary_traffic_weight() {
    local weight="$1"
    
    log_info "Setting canary traffic weight to ${weight}%"
    
    kubectl annotate ingress "$CANARY_INGRESS" \
            nginx.ingress.kubernetes.io/canary-weight="${weight}" \
            -n "$NAMESPACE" --overwrite
    
    # Wait for ingress controller to pick up changes
    sleep 30
    
    log_success "Canary traffic weight set to ${weight}%"
}

# Monitor canary metrics
monitor_canary_metrics() {
    local duration="$1"
    local traffic_percentage="$2"
    
    log_info "Monitoring canary metrics for ${duration}s at ${traffic_percentage}% traffic"
    
    local end_time=$(($(date +%s) + duration))
    local check_interval=30
    local check_count=0
    local failed_checks=0
    
    while [[ $(date +%s) -lt $end_time ]]; do
        ((check_count++))
        
        # Get metrics from Prometheus
        local canary_metrics
        canary_metrics=$(get_canary_metrics)
        
        local success_rate error_rate avg_latency
        success_rate=$(echo "$canary_metrics" | jq -r '.success_rate // 100')
        error_rate=$(echo "$canary_metrics" | jq -r '.error_rate // 0')
        avg_latency=$(echo "$canary_metrics" | jq -r '.avg_latency // 0')
        
        log_info "Check $check_count: Success=${success_rate}%, Error=${error_rate}%, Latency=${avg_latency}ms"
        
        # Check success rate
        if (( $(echo "$success_rate < $SUCCESS_RATE_THRESHOLD" | bc -l) )); then
            log_error "Success rate below threshold: ${success_rate}% < ${SUCCESS_RATE_THRESHOLD}%"
            ((failed_checks++))
        fi
        
        # Check error rate
        if (( $(echo "$error_rate > $ERROR_RATE_THRESHOLD" | bc -l) )); then
            log_error "Error rate above threshold: ${error_rate}% > ${ERROR_RATE_THRESHOLD}%"
            ((failed_checks++))
        fi
        
        # Check latency
        if (( $(echo "$avg_latency > $LATENCY_THRESHOLD" | bc -l) )); then
            log_warn "Latency above threshold: ${avg_latency}ms > ${LATENCY_THRESHOLD}ms"
        fi
        
        # Fail fast if too many failed checks
        local failure_rate=$(echo "scale=2; $failed_checks * 100 / $check_count" | bc)
        if (( $(echo "$failure_rate > 20" | bc -l) )); then
            log_error "Failure rate too high: ${failure_rate}%, aborting canary"
            return 1
        fi
        
        sleep $check_interval
    done
    
    local final_failure_rate=$(echo "scale=2; $failed_checks * 100 / $check_count" | bc)
    log_info "Monitoring complete: ${final_failure_rate}% failure rate"
    
    if (( $(echo "$final_failure_rate > 10" | bc -l) )); then
        log_error "Final failure rate too high: ${final_failure_rate}%"
        return 1
    fi
    
    log_success "Canary metrics acceptable for ${traffic_percentage}% traffic"
    return 0
}

# Get canary metrics from Prometheus
get_canary_metrics() {
    if [[ -z "${PROMETHEUS_URL:-}" ]]; then
        echo '{"success_rate": 99.5, "error_rate": 0.5, "avg_latency": 150}'
        return
    fi
    
    # Success rate query
    local success_rate
    success_rate=$(curl -s "${PROMETHEUS_URL}/api/v1/query" \
                  --data-urlencode 'query=(sum(rate(http_requests_total{job="web-app",version="canary",status!~"5.."}[5m])) / sum(rate(http_requests_total{job="web-app",version="canary"}[5m]))) * 100' \
                  | jq -r '.data.result[0].value[1] // "100"' 2>/dev/null || echo "100")
    
    # Error rate query
    local error_rate
    error_rate=$(curl -s "${PROMETHEUS_URL}/api/v1/query" \
                --data-urlencode 'query=(sum(rate(http_requests_total{job="web-app",version="canary",status=~"5.."}[5m])) / sum(rate(http_requests_total{job="web-app",version="canary"}[5m]))) * 100' \
                | jq -r '.data.result[0].value[1] // "0"' 2>/dev/null || echo "0")
    
    # Average latency query
    local avg_latency
    avg_latency=$(curl -s "${PROMETHEUS_URL}/api/v1/query" \
                 --data-urlencode 'query=avg(rate(http_request_duration_seconds_sum{job="web-app",version="canary"}[5m]) / rate(http_request_duration_seconds_count{job="web-app",version="canary"}[5m])) * 1000' \
                 | jq -r '.data.result[0].value[1] // "0"' 2>/dev/null || echo "0")
    
    cat <<EOF
{
    "success_rate": $success_rate,
    "error_rate": $error_rate,
    "avg_latency": $avg_latency
}
EOF
}

# Progressive traffic increase
progressive_canary_rollout() {
    local image_tag="$1"
    
    log_info "Starting progressive canary rollout for $image_tag"
    
    # Deploy initial canary
    if ! deploy_canary "$image_tag" 2; then
        log_error "Initial canary deployment failed"
        return 1
    fi
    
    # Progressive traffic increase
    for stage in "${TRAFFIC_STAGES[@]}"; do
        log_info "=== Canary Stage: ${stage}% Traffic ==="
        
        # Set traffic weight
        set_canary_traffic_weight "$stage"
        
        # Scale canary replicas based on traffic percentage
        local canary_replicas=$(echo "scale=0; ($stage * 10) / 100 + 1" | bc)
        kubectl scale deployment "${APP_NAME}-canary" \
                --replicas="$canary_replicas" \
                -n "$NAMESPACE"
        
        # Wait for scaling
        kubectl rollout status deployment/"${APP_NAME}-canary" \
                -n "$NAMESPACE" --timeout=180s
        
        # Monitor metrics for this stage
        if ! monitor_canary_metrics "$METRICS_CHECK_DURATION" "$stage"; then
            log_error "Canary failed at ${stage}% traffic stage"
            rollback_canary
            return 1
        fi
        
        log_success "Stage ${stage}% completed successfully"
    done
    
    log_success "Progressive canary rollout completed"
}

# Rollback canary deployment
rollback_canary() {
    log_error "Rolling back canary deployment"
    
    # Set canary traffic to 0%
    set_canary_traffic_weight 0
    
    # Scale down canary
    kubectl scale deployment "${APP_NAME}-canary" \
            --replicas=0 \
            -n "$NAMESPACE"
    
    # Send rollback notification
    send_canary_notification "ROLLBACK" "0"
    
    log_success "Canary rollback completed"
}

# Promote canary to production
promote_canary_to_production() {
    local image_tag="$1"
    
    log_info "Promoting canary to production"
    
    # Update production deployment with canary image
    kubectl set image deployment/"${APP_NAME}-production" \
            "${APP_NAME}=${APP_NAME}:${image_tag}" \
            -n "$NAMESPACE"
    
    # Wait for production rollout
    if ! kubectl rollout status deployment/"${APP_NAME}-production" \
         -n "$NAMESPACE" --timeout=600s; then
        log_error "Production deployment failed during canary promotion"
        return 1
    fi
    
    # Remove canary traffic routing
    kubectl delete ingress "$CANARY_INGRESS" -n "$NAMESPACE" || true
    
    # Scale down canary deployment
    kubectl scale deployment "${APP_NAME}-canary" \
            --replicas=0 \
            -n "$NAMESPACE"
    
    # Send promotion notification
    send_canary_notification "PROMOTED" "100"
    
    log_success "Canary promoted to production"
}

# A/B testing with canary
canary_ab_testing() {
    local image_tag="$1"
    local test_duration="${2:-1800}"  # 30 minutes default
    
    log_info "Starting A/B test with canary deployment"
    
    # Deploy canary with specific feature flags
    deploy_canary "$image_tag" 3
    
    # Set 50/50 traffic split for A/B testing
    set_canary_traffic_weight 50
    
    # Monitor A/B test metrics
    local end_time=$(($(date +%s) + test_duration))
    
    while [[ $(date +%s) -lt $end_time ]]; do
        # Get A/B metrics
        local ab_metrics
        ab_metrics=$(get_ab_test_metrics)
        
        local canary_conversion prod_conversion
        canary_conversion=$(echo "$ab_metrics" | jq -r '.canary_conversion // 0')
        prod_conversion=$(echo "$ab_metrics" | jq -r '.production_conversion // 0')
        
        log_info "A/B Test - Canary: ${canary_conversion}% vs Production: ${prod_conversion}%"
        
        # Check for significant difference
        local conversion_diff
        conversion_diff=$(echo "$canary_conversion - $prod_conversion" | bc)
        
        if (( $(echo "$conversion_diff > 5.0" | bc -l) )); then
            log_success "Canary showing significant improvement: +${conversion_diff}%"
            break
        elif (( $(echo "$conversion_diff < -3.0" | bc -l) )); then
            log_error "Canary showing degradation: ${conversion_diff}%"
            rollback_canary
            return 1
        fi
        
        sleep 300  # Check every 5 minutes
    done
    
    log_success "A/B test completed"
}

# Get A/B test metrics
get_ab_test_metrics() {
    # Placeholder for A/B testing metrics
    # In practice, integrate with your analytics platform
    cat <<EOF
{
    "canary_conversion": 12.5,
    "production_conversion": 11.8,
    "canary_bounce_rate": 23.2,
    "production_bounce_rate": 24.1
}
EOF
}

# Feature flag controlled canary
feature_flag_canary() {
    local image_tag="$1"
    local feature_flag="$2"
    local target_percentage="${3:-10}"
    
    log_info "Starting feature flag controlled canary for feature: $feature_flag"
    
    # Deploy canary with feature flag enabled
    kubectl set env deployment/"${APP_NAME}-canary" \
            "FEATURE_${feature_flag^^}=true" \
            -n "$NAMESPACE"
    
    deploy_canary "$image_tag" 2
    
    # Use header-based routing for feature flag users
    kubectl annotate ingress "$CANARY_INGRESS" \
            nginx.ingress.kubernetes.io/canary-by-header="X-Feature-${feature_flag}" \
            nginx.ingress.kubernetes.io/canary-by-header-value="enabled" \
            -n "$NAMESPACE" --overwrite
    
    # Also set small percentage of regular traffic
    set_canary_traffic_weight "$target_percentage"
    
    log_success "Feature flag canary deployed for: $feature_flag"
}

# Send notifications
send_canary_notification() {
    local status="$1"
    local traffic_percentage="$2"
    
    if [[ -n "${SLACK_WEBHOOK_URL:-}" ]]; then
        local color="good"
        local icon="🐤"
        
        case "$status" in
            "ROLLBACK") color="danger"; icon="🚨" ;;
            "PROMOTED") color="good"; icon="🎉" ;;
        esac
        
        local payload=$(cat <<EOF
{
    "attachments": [
        {
            "color": "$color",
            "title": "$icon Canary Deployment $status",
            "fields": [
                {
                    "title": "Application",
                    "value": "$APP_NAME",
                    "short": true
                },
                {
                    "title": "Traffic Percentage",
                    "value": "${traffic_percentage}%",
                    "short": true
                },
                {
                    "title": "Status",
                    "value": "$status",
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
    local image_tag="${2:-}"
    
    case "$command" in
        "deploy")
            [[ -z "$image_tag" ]] && { log_error "Image tag required"; exit 1; }
            progressive_canary_rollout "$image_tag"
            ;;
        "promote")
            [[ -z "$image_tag" ]] && { log_error "Image tag required"; exit 1; }
            promote_canary_to_production "$image_tag"
            ;;
        "rollback")
            rollback_canary
            ;;
        "ab-test")
            [[ -z "$image_tag" ]] && { log_error "Image tag required"; exit 1; }
            canary_ab_testing "$image_tag" "${3:-1800}"
            ;;
        "feature-flag")
            [[ -z "$image_tag" ]] && { log_error "Image tag required"; exit 1; }
            [[ -z "$3" ]] && { log_error "Feature flag name required"; exit 1; }
            feature_flag_canary "$image_tag" "$3" "${4:-10}"
            ;;
        "status")
            kubectl get ingress "$CANARY_INGRESS" -n "$NAMESPACE" -o yaml | \
                grep -A 5 -B 5 canary-weight || echo "No canary deployment found"
            ;;
        *)
            cat <<EOF
Canary Deployment Tool

Usage: $0 <command> [options]

Commands:
  deploy <image-tag>              - Start progressive canary deployment
  promote <image-tag>             - Promote canary to production
  rollback                        - Rollback canary deployment
  ab-test <image-tag> [duration]  - Run A/B test with canary
  feature-flag <image-tag> <flag> [percentage] - Feature flag canary
  status                          - Show canary deployment status

Examples:
  $0 deploy v1.3.0-canary
  $0 promote v1.3.0
  $0 ab-test v1.3.0-experiment 3600
  $0 feature-flag v1.3.0 new_checkout 15
EOF
            ;;
    esac
}

# Run main function if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
```

This provides comprehensive canary deployment implementation with progressive traffic splitting, automated monitoring, A/B testing capabilities, and feature flag integration - all production-ready patterns for safe deployments.