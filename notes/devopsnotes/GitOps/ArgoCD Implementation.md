## Production ArgoCD Implementation

### ArgoCD Installation and Configuration

#### High-Availability ArgoCD Setup
```yaml
# argocd/install/argocd-ha.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: argocd
---
apiVersion: argoproj.io/v1alpha1
kind: ArgoCD
metadata:
  name: argocd
  namespace: argocd
spec:
  server:
    replicas: 3
    ingress:
      enabled: true
      ingressClassName: nginx
      annotations:
        cert-manager.io/cluster-issuer: letsencrypt-prod
        nginx.ingress.kubernetes.io/ssl-redirect: "true"
        nginx.ingress.kubernetes.io/force-ssl-redirect: "true"
      hosts:
      - argocd.company.com
      tls:
      - secretName: argocd-server-tls
        hosts:
        - argocd.company.com
    config:
      users.anonymous.enabled: "false"
      oidc.config: |
        name: SSO
        issuer: https://auth.company.com/realms/company
        clientId: argocd
        clientSecret: $oidc.clientSecret
        requestedScopes: ["openid", "profile", "email", "groups"]
        requestedIDTokenClaims: {"groups": {"essential": true}}
      policy.default: role:readonly
      policy.csv: |
        p, role:admin, applications, *, */*, allow
        p, role:admin, clusters, *, *, allow
        p, role:admin, repositories, *, *, allow
        p, role:developer, applications, get, */*, allow
        p, role:developer, applications, sync, */*, allow
        p, role:sre, applications, *, */*, allow
        p, role:sre, clusters, get, *, allow
        g, argocd-admins, role:admin
        g, developers, role:developer
        g, sre-team, role:sre
  
  controller:
    replicas: 3
    resources:
      requests:
        cpu: 500m
        memory: 1Gi
      limits:
        cpu: 2000m
        memory: 4Gi
    env:
    - name: ARGOCD_CONTROLLER_REPLICAS
      value: "3"
    - name: ARGOCD_CONTROLLER_HEARTBEAT_TIME
      value: "5s"
    - name: ARGOCD_APPLICATION_CONTROLLER_REPO_SERVER_TIMEOUT_SECONDS
      value: "300"
  
  redis:
    replicas: 3
    resources:
      requests:
        cpu: 100m
        memory: 128Mi
      limits:
        cpu: 500m
        memory: 512Mi
  
  repo:
    replicas: 3
    resources:
      requests:
        cpu: 250m
        memory: 512Mi
      limits:
        cpu: 1000m
        memory: 2Gi
    env:
    - name: ARGOCD_EXEC_TIMEOUT
      value: "300s"
    - name: ARGOCD_GIT_ATTEMPTS_COUNT
      value: "3"
  
  applicationSet:
    replicas: 2
    resources:
      requests:
        cpu: 100m
        memory: 128Mi
      limits:
        cpu: 500m
        memory: 512Mi
```

#### ArgoCD Configuration Management
```yaml
# argocd/config/argocd-cm.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: argocd-cmd-params-cm
  namespace: argocd
  labels:
    app.kubernetes.io/name: argocd-cmd-params-cm
    app.kubernetes.io/part-of: argocd
data:
  # Controller
  controller.status.processors: "20"
  controller.operation.processors: "10" 
  controller.self.heal.timeout.seconds: "5"
  controller.repo.server.timeout.seconds: "300"
  
  # Server
  server.insecure: "false"
  server.enable.proxy.extension: "true"
  server.grpc.max.size: "104857600"  # 100MB
  
  # Repository server
  repo.server.git.request.timeout: "300s"
  repo.server.max.combined.directory.manifests.size: "104857600"  # 100MB
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: argocd-cm
  namespace: argocd
data:
  # Repository credentials
  repositories: |
    - type: git
      url: https://github.com/company/gitops-infrastructure
    - type: git
      url: https://github.com/company/helm-charts
      name: helm-charts
  
  # Repository credentials template
  repository.credentials: |
    - url: https://github.com/company
      passwordSecret:
        name: github-secret
        key: password
      usernameSecret:
        name: github-secret
        key: username
  
  # Resource exclusions
  resource.exclusions: |
    - apiGroups:
      - tekton.dev
      clusters:
      - '*'
      kinds:
      - TaskRun
      - PipelineRun
    - apiGroups:
      - ""
      kinds:
      - Event
  
  # Resource inclusions
  resource.inclusions: |
    - apiGroups:
      - ""
      kinds:
      - ConfigMap
      - Secret
      - Service
      - PersistentVolumeClaim
    - apiGroups:
      - apps
      kinds:
      - Deployment
      - StatefulSet
      - DaemonSet
  
  # Health checks
  resource.customizations.health.argoproj.io_Application: |
    hs = {}
    hs.status = "Progressing"
    hs.message = ""
    if obj.status ~= nil then
      if obj.status.health ~= nil then
        hs.status = obj.status.health.status
        if obj.status.health.message ~= nil then
          hs.message = obj.status.health.message
        end
      end
    end
    return hs
  
  # Ignore differences
  resource.customizations.ignoreDifferences.apps_Deployment: |
    - group: apps
      kind: Deployment
      jsonPointers:
      - /spec/replicas
      - /status
```

### Production Application Patterns

#### Multi-Environment Application Setup
```yaml
# applications/web-app-production.yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: web-app-production
  namespace: argocd
  finalizers:
    - resources-finalizer.argocd.argoproj.io
  annotations:
    argocd.argoproj.io/sync-wave: "10"
    notifications.argoproj.io/subscribe.on-sync-succeeded.slack: production-deployments
    notifications.argoproj.io/subscribe.on-sync-failed.slack: production-alerts
spec:
  project: production
  source:
    repoURL: https://github.com/company/gitops-infrastructure
    targetRevision: production
    path: environments/production/applications/web-app
    helm:
      parameters:
      - name: image.tag
        value: "v1.2.3"
      - name: replicaCount
        value: "5"
      - name: resources.requests.memory
        value: "512Mi"
      - name: resources.requests.cpu
        value: "250m"
      valueFiles:
      - values-production.yaml
  destination:
    server: https://kubernetes.default.svc
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
    - RespectIgnoreDifferences=true
    retry:
      limit: 5
      backoff:
        duration: 5s
        factor: 2
        maxDuration: 3m
  revisionHistoryLimit: 10
  ignoreDifferences:
  - group: apps
    kind: Deployment
    jsonPointers:
    - /spec/replicas  # Ignore HPA scaling
```

#### ApplicationSet for Multi-Cluster Management
```yaml
# applicationsets/multi-cluster-apps.yaml
apiVersion: argoproj.io/v1alpha1
kind: ApplicationSet
metadata:
  name: production-services
  namespace: argocd
spec:
  generators:
  - clusters:
      selector:
        matchLabels:
          environment: production
      values:
        clusterName: '{{name}}'
        server: '{{server}}'
  - git:
      repoURL: https://github.com/company/gitops-infrastructure
      revision: HEAD
      directories:
      - path: environments/production/applications/*
      - path: environments/production/applications/*/
        exclude: environments/production/applications/disabled-*
  template:
    metadata:
      name: '{{path.basename}}-{{values.clusterName}}'
      namespace: argocd
      finalizers:
        - resources-finalizer.argocd.argoproj.io
      annotations:
        argocd.argoproj.io/sync-wave: "{{path.index}}"
    spec:
      project: production
      source:
        repoURL: https://github.com/company/gitops-infrastructure
        targetRevision: production
        path: '{{path}}'
        helm:
          valueFiles:
          - values.yaml
          - values-{{values.clusterName}}.yaml
      destination:
        server: '{{values.server}}'
        namespace: production
      syncPolicy:
        automated:
          prune: true
          selfHeal: true
        syncOptions:
        - CreateNamespace=true
        - PrunePropagationPolicy=foreground
        retry:
          limit: 3
          backoff:
            duration: 5s
            factor: 2
            maxDuration: 1m
```

### ArgoCD Operations Scripts

#### Deployment Management
```bash
#!/bin/bash
# scripts/argocd-ops.sh - ArgoCD operational tools

set -euo pipefail

readonly ARGOCD_SERVER="argocd.company.com"
readonly ARGOCD_NAMESPACE="argocd"

# Login to ArgoCD
argocd_login() {
    local username="${1:-admin}"
    local password="${2:-}"
    
    if [[ -z "$password" ]]; then
        password=$(kubectl -n "$ARGOCD_NAMESPACE" get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d)
    fi
    
    argocd login "$ARGOCD_SERVER" --username "$username" --password "$password" --insecure
    log_success "Logged into ArgoCD as $username"
}

# Deploy application with verification
deploy_application() {
    local app_name="$1"
    local target_revision="${2:-HEAD}"
    local wait_timeout="${3:-600}"
    
    log_info "Deploying application: $app_name to revision: $target_revision"
    
    # Update target revision
    argocd app set "$app_name" --revision "$target_revision"
    
    # Trigger sync
    argocd app sync "$app_name" --prune
    
    # Wait for sync to complete
    if ! argocd app wait "$app_name" --timeout "$wait_timeout" --health; then
        log_error "Deployment failed or timed out"
        
        # Get application status for debugging
        argocd app get "$app_name" -o yaml > "/tmp/${app_name}-failed-deployment.yaml"
        log_error "Application status saved to /tmp/${app_name}-failed-deployment.yaml"
        
        # Show recent events
        kubectl get events -n production --sort-by='.lastTimestamp' | tail -10
        
        return 1
    fi
    
    log_success "Deployment completed successfully"
    
    # Verify deployment health
    verify_deployment_health "$app_name"
}

# Verify deployment health
verify_deployment_health() {
    local app_name="$1"
    
    log_info "Verifying deployment health for $app_name"
    
    # Get application details
    local app_json
    app_json=$(argocd app get "$app_name" -o json)
    
    local sync_status
    sync_status=$(echo "$app_json" | jq -r '.status.sync.status')
    
    local health_status  
    health_status=$(echo "$app_json" | jq -r '.status.health.status')
    
    log_info "Sync Status: $sync_status"
    log_info "Health Status: $health_status"
    
    if [[ "$sync_status" != "Synced" ]]; then
        log_error "Application is not synced"
        return 1
    fi
    
    if [[ "$health_status" != "Healthy" ]]; then
        log_error "Application is not healthy"
        
        # Show unhealthy resources
        echo "$app_json" | jq -r '.status.resources[] | select(.health.status != "Healthy") | "\(.kind)/\(.name): \(.health.status) - \(.health.message // "")"'
        
        return 1
    fi
    
    # Additional health checks
    local namespace
    namespace=$(echo "$app_json" | jq -r '.spec.destination.namespace')
    
    # Check if all pods are ready
    local unready_pods
    unready_pods=$(kubectl get pods -n "$namespace" -l "app.kubernetes.io/instance=$app_name" --field-selector=status.phase!=Running -o name 2>/dev/null || true)
    
    if [[ -n "$unready_pods" ]]; then
        log_warn "Some pods are not ready:"
        echo "$unready_pods"
    fi
    
    log_success "Deployment health verification completed"
}

# Rollback application
rollback_application() {
    local app_name="$1"
    local target_revision="${2:-}"
    
    if [[ -z "$target_revision" ]]; then
        # Get previous successful revision
        target_revision=$(argocd app history "$app_name" --output json | \
                         jq -r '.[] | select(.deployedAt != null) | .revision' | \
                         head -2 | tail -1)
        
        if [[ -z "$target_revision" ]]; then
            error_exit "No previous revision found for rollback"
        fi
        
        log_info "Rolling back to previous revision: $target_revision"
    else
        log_info "Rolling back to specified revision: $target_revision"
    fi
    
    # Perform rollback
    argocd app rollback "$app_name" "$target_revision"
    
    # Wait for rollback to complete
    if ! argocd app wait "$app_name" --timeout 300 --health; then
        log_error "Rollback failed or timed out"
        return 1
    fi
    
    log_success "Rollback completed successfully"
    
    # Send notification
    send_rollback_notification "$app_name" "$target_revision"
}

# Bulk operations
bulk_sync_applications() {
    local app_pattern="$1"
    local max_parallel="${2:-5}"
    
    log_info "Bulk syncing applications matching: $app_pattern"
    
    local apps
    apps=$(argocd app list -o name | grep "$app_pattern")
    
    if [[ -z "$apps" ]]; then
        log_warn "No applications found matching pattern: $app_pattern"
        return 0
    fi
    
    log_info "Found $(echo "$apps" | wc -l) applications to sync"
    
    # Sync applications in parallel
    echo "$apps" | xargs -P "$max_parallel" -I {} bash -c '
        app_name="{}"
        echo "Syncing: $app_name"
        if argocd app sync "$app_name" --timeout 300; then
            echo "✅ $app_name: Sync successful"
        else
            echo "❌ $app_name: Sync failed"
        fi
    '
    
    log_info "Bulk sync completed"
}

# Application health monitoring
monitor_application_health() {
    local duration="${1:-300}"  # 5 minutes default
    local interval="${2:-30}"   # 30 seconds default
    
    log_info "Monitoring application health for ${duration}s..."
    
    local end_time=$(($(date +%s) + duration))
    
    while [[ $(date +%s) -lt $end_time ]]; do
        local unhealthy_apps
        unhealthy_apps=$(argocd app list -o json | \
                        jq -r '.[] | select(.status.health.status != "Healthy") | .metadata.name')
        
        if [[ -n "$unhealthy_apps" ]]; then
            log_warn "Unhealthy applications detected:"
            echo "$unhealthy_apps" | while IFS= read -r app; do
                local health_message
                health_message=$(argocd app get "$app" -o json | jq -r '.status.health.message // "No message"')
                echo "  ❌ $app: $health_message"
            done
            
            # Send alert for critical applications
            echo "$unhealthy_apps" | grep -E "(production|critical)" | while IFS= read -r critical_app; do
                send_critical_alert "$critical_app"
            done
        else
            log_info "All applications healthy at $(date '+%H:%M:%S')"
        fi
        
        sleep "$interval"
    done
    
    log_info "Health monitoring completed"
}

# Sync drift detection
detect_sync_drift() {
    local threshold_hours="${1:-1}"
    
    log_info "Detecting sync drift (threshold: ${threshold_hours}h)"
    
    local drift_apps
    drift_apps=$(argocd app list -o json | \
                jq -r --arg threshold "$threshold_hours" '
                    .[] | 
                    select(
                        .status.operationState.finishedAt != null and 
                        (now - (.status.operationState.finishedAt | fromdateiso8601)) > ($threshold | tonumber * 3600)
                    ) | 
                    .metadata.name')
    
    if [[ -n "$drift_apps" ]]; then
        log_warn "Applications with sync drift detected:"
        echo "$drift_apps" | while IFS= read -r app; do
            local last_sync
            last_sync=$(argocd app get "$app" -o json | jq -r '.status.operationState.finishedAt')
            echo "  ⚠️  $app: Last sync $last_sync"
        done
    else
        log_success "No sync drift detected"
    fi
}

# Generate operational report
generate_ops_report() {
    local output_file="/tmp/argocd-ops-report-$(date +%Y%m%d).txt"
    
    {
        echo "=== ArgoCD Operational Report ==="
        echo "Generated: $(date)"
        echo "Server: $ARGOCD_SERVER"
        echo "================================"
        echo
        
        echo "Application Summary:"
        argocd app list -o wide
        echo
        
        echo "Unhealthy Applications:"
        argocd app list -o json | jq -r '.[] | select(.status.health.status != "Healthy") | "\(.metadata.name): \(.status.health.status) - \(.status.health.message // "No message")"'
        echo
        
        echo "Out-of-Sync Applications:"
        argocd app list -o json | jq -r '.[] | select(.status.sync.status != "Synced") | "\(.metadata.name): \(.status.sync.status)"'
        echo
        
        echo "Recent Operations:"
        argocd app list -o json | jq -r '.[] | select(.status.operationState.finishedAt != null) | "\(.metadata.name): \(.status.operationState.phase) at \(.status.operationState.finishedAt)"' | head -20
        
    } > "$output_file"
    
    log_info "Operational report generated: $output_file"
    
    # Send to monitoring system if configured
    if [[ -n "${MONITORING_WEBHOOK:-}" ]]; then
        curl -X POST -H "Content-Type: text/plain" \
             --data-binary "@$output_file" \
             "$MONITORING_WEBHOOK" || log_warn "Failed to send report to monitoring system"
    fi
}

# Main menu
main() {
    local command="${1:-help}"
    
    case "$command" in
        "login")
            argocd_login "${2:-admin}" "${3:-}"
            ;;
        "deploy")
            deploy_application "${2:?Application name required}" "${3:-HEAD}" "${4:-600}"
            ;;
        "rollback")
            rollback_application "${2:?Application name required}" "${3:-}"
            ;;
        "bulk-sync")
            bulk_sync_applications "${2:?App pattern required}" "${3:-5}"
            ;;
        "monitor")
            monitor_application_health "${2:-300}" "${3:-30}"
            ;;
        "drift")
            detect_sync_drift "${2:-1}"
            ;;
        "report")
            generate_ops_report
            ;;
        "help"|*)
            cat <<EOF
ArgoCD Operations Tool

Usage: $0 <command> [options]

Commands:
  login [username] [password]     - Login to ArgoCD
  deploy <app> [revision] [timeout] - Deploy application
  rollback <app> [revision]       - Rollback application
  bulk-sync <pattern> [parallel]  - Bulk sync applications
  monitor [duration] [interval]   - Monitor application health
  drift [threshold_hours]         - Detect sync drift
  report                          - Generate operational report

Examples:
  $0 deploy web-app-production v1.2.3
  $0 rollback api-service
  $0 bulk-sync "production-*" 3
  $0 monitor 600 60
EOF
            ;;
    esac
}

# Helper functions
send_rollback_notification() {
    local app_name="$1"
    local revision="$2"
    
    if [[ -n "${SLACK_WEBHOOK:-}" ]]; then
        curl -X POST -H 'Content-type: application/json' \
             --data "{\"text\":\"🔄 Rollback completed: $app_name to revision $revision\"}" \
             "$SLACK_WEBHOOK" >/dev/null 2>&1 || true
    fi
}

send_critical_alert() {
    local app_name="$1"
    
    if [[ -n "${PAGERDUTY_INTEGRATION_KEY:-}" ]]; then
        local payload=$(cat <<EOF
{
  "routing_key": "$PAGERDUTY_INTEGRATION_KEY",
  "event_action": "trigger",
  "payload": {
    "summary": "ArgoCD: Critical application $app_name is unhealthy",
    "source": "argocd",
    "severity": "critical"
  }
}
EOF
)
        curl -X POST -H "Content-Type: application/json" \
             -d "$payload" \
             "https://events.pagerduty.com/v2/enqueue" >/dev/null 2>&1 || true
    fi
}

# Run main function if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
```

This provides comprehensive ArgoCD production implementation with high availability setup, RBAC, operational scripts, and monitoring capabilities.