## GitOps Production Implementation Guide

### GitOps Core Principles in Practice

#### 1. Declarative Infrastructure
```yaml
# infrastructure/prod/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: production
  labels:
    environment: prod
    managed-by: gitops
---
# infrastructure/prod/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
  namespace: production
data:
  database_url: "postgres://prod-db:5432/app"
  redis_url: "redis://prod-redis:6379"
  log_level: "INFO"
  max_connections: "100"
```

#### 2. Git as Single Source of Truth
```bash
# Repository Structure for Production GitOps
gitops-infrastructure/
├── environments/
│   ├── production/
│   │   ├── applications/
│   │   │   ├── web-app/
│   │   │   │   ├── deployment.yaml
│   │   │   │   ├── service.yaml
│   │   │   │   ├── ingress.yaml
│   │   │   │   └── hpa.yaml
│   │   │   └── api-service/
│   │   │       ├── deployment.yaml
│   │   │       └── service.yaml
│   │   ├── infrastructure/
│   │   │   ├── monitoring/
│   │   │   │   ├── prometheus.yaml
│   │   │   │   └── grafana.yaml
│   │   │   └── security/
│   │   │       ├── network-policies.yaml
│   │   │       └── rbac.yaml
│   │   └── base/
│   │       ├── namespace.yaml
│   │       └── secrets.yaml
│   ├── staging/
│   └── development/
├── shared/
│   ├── base/
│   └── components/
├── docs/
│   ├── runbooks/
│   └── architecture/
└── scripts/
    ├── deploy.sh
    ├── validate.sh
    └── rollback.sh
```

#### 3. Automated Synchronization Setup
```yaml
# argocd/applications/production-apps.yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: production-infrastructure
  namespace: argocd
  finalizers:
    - resources-finalizer.argocd.argoproj.io
spec:
  project: production
  source:
    repoURL: 'https://github.com/company/gitops-infrastructure'
    targetRevision: main
    path: environments/production
  destination:
    server: 'https://kubernetes.default.svc'
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
  revisionHistoryLimit: 10
```

### Production GitOps Workflow

#### 1. Change Management Process
```bash
#!/bin/bash
# scripts/production-change.sh - Controlled production changes

set -euo pipefail

readonly REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
readonly PROD_BRANCH="production"
readonly STAGING_BRANCH="staging"

validate_change_request() {
    local change_type="$1"
    local component="$2"
    local description="$3"
    
    log_info "Validating change request..."
    
    # Validate change type
    case "$change_type" in
        "hotfix"|"feature"|"config"|"security")
            log_info "Change type '$change_type' is valid"
            ;;
        *)
            error_exit "Invalid change type: $change_type. Must be: hotfix, feature, config, security"
            ;;
    esac
    
    # Check if component exists
    local component_path="$REPO_DIR/environments/production/applications/$component"
    if [[ ! -d "$component_path" ]]; then
        error_exit "Component '$component' not found in production applications"
    fi
    
    # Validate YAML syntax
    log_info "Validating YAML syntax..."
    find "$component_path" -name "*.yaml" -o -name "*.yml" | while read -r yaml_file; do
        if ! yamllint "$yaml_file" >/dev/null 2>&1; then
            error_exit "YAML validation failed for: $yaml_file"
        fi
    done
    
    log_success "Change request validation passed"
}

create_change_pr() {
    local change_type="$1"
    local component="$2"
    local description="$3"
    local ticket_id="$4"
    
    local branch_name="${change_type}/${component}-${ticket_id}-$(date +%Y%m%d)"
    
    log_info "Creating change branch: $branch_name"
    
    # Create and checkout new branch
    git checkout -b "$branch_name" "$STAGING_BRANCH"
    
    # Create PR template
    cat > .github/PULL_REQUEST_TEMPLATE.md <<EOF
## Production Change Request

**Type:** $change_type
**Component:** $component
**Ticket:** $ticket_id

### Description
$description

### Pre-deployment Checklist
- [ ] YAML syntax validated
- [ ] Resource quotas checked
- [ ] Security policies reviewed
- [ ] Monitoring alerts configured
- [ ] Rollback plan documented

### Testing
- [ ] Staging deployment successful
- [ ] Performance tests passed
- [ ] Security scan completed
- [ ] Integration tests passed

### Approval Required
- [ ] SRE Team Lead
- [ ] Security Team (for security changes)
- [ ] Architecture Team (for infrastructure changes)

### Post-deployment
- [ ] Health checks verified
- [ ] Metrics baseline established
- [ ] Documentation updated
EOF
    
    log_info "Push branch and create PR manually"
    log_info "Branch: $branch_name"
}

apply_production_change() {
    local pr_number="$1"
    
    log_info "Applying production change from PR #$pr_number"
    
    # Verify PR is approved
    local pr_status
    pr_status=$(gh pr view "$pr_number" --json state,reviews --jq '.state')
    
    if [[ "$pr_status" != "OPEN" ]]; then
        error_exit "PR #$pr_number is not open"
    fi
    
    # Check for required approvals
    local approvals
    approvals=$(gh pr view "$pr_number" --json reviews --jq '.reviews | map(select(.state == "APPROVED")) | length')
    
    if [[ $approvals -lt 2 ]]; then
        error_exit "PR #$pr_number requires at least 2 approvals (has: $approvals)"
    fi
    
    # Merge to staging first
    log_info "Merging to staging for final validation..."
    gh pr merge "$pr_number" --merge --delete-branch
    
    # Wait for staging deployment
    log_info "Waiting for staging deployment to complete..."
    wait_for_argo_sync "staging" "300"
    
    # Run production validation
    run_production_readiness_check
    
    # Create production deployment PR
    create_production_deployment_pr
}

wait_for_argo_sync() {
    local environment="$1"
    local timeout="${2:-180}"
    local app_name="${environment}-infrastructure"
    
    log_info "Waiting for ArgoCD sync: $app_name"
    
    local end_time=$(($(date +%s) + timeout))
    
    while [[ $(date +%s) -lt $end_time ]]; do
        local sync_status
        sync_status=$(argocd app get "$app_name" -o json | jq -r '.status.sync.status')
        
        local health_status
        health_status=$(argocd app get "$app_name" -o json | jq -r '.status.health.status')
        
        if [[ "$sync_status" == "Synced" && "$health_status" == "Healthy" ]]; then
            log_success "ArgoCD sync completed for $app_name"
            return 0
        fi
        
        log_info "Sync status: $sync_status, Health: $health_status"
        sleep 10
    done
    
    error_exit "ArgoCD sync timeout for $app_name"
}

run_production_readiness_check() {
    log_info "Running production readiness checks..."
    
    # Check resource quotas
    local resource_usage
    resource_usage=$(kubectl top nodes --no-headers | awk '{sum+=$3} END {print sum}')
    
    if [[ ${resource_usage%%\%} -gt 80 ]]; then
        error_exit "Cluster CPU usage too high: ${resource_usage}%"
    fi
    
    # Validate security policies
    log_info "Validating security policies..."
    if ! kubectl auth can-i create pods --as=system:serviceaccount:production:default; then
        log_success "Default service account properly restricted"
    else
        error_exit "Default service account has excessive permissions"
    fi
    
    # Check monitoring stack
    log_info "Verifying monitoring stack..."
    if ! kubectl get pods -n monitoring | grep -q "prometheus.*Running"; then
        error_exit "Prometheus not running in monitoring namespace"
    fi
    
    # Validate backup systems
    log_info "Checking backup systems..."
    local last_backup
    last_backup=$(kubectl get cronjob backup-job -o jsonpath='{.status.lastScheduleTime}' 2>/dev/null || echo "")
    
    if [[ -z "$last_backup" ]]; then
        log_warn "No recent backup job found"
    fi
    
    log_success "Production readiness checks passed"
}

create_production_deployment_pr() {
    local staging_commit
    staging_commit=$(git rev-parse "$STAGING_BRANCH")
    
    # Create production deployment branch
    git checkout "$PROD_BRANCH"
    git pull origin "$PROD_BRANCH"
    
    local deploy_branch="deploy/production-$(date +%Y%m%d-%H%M%S)"
    git checkout -b "$deploy_branch"
    
    # Merge staging changes
    git merge "$STAGING_BRANCH" --no-edit
    
    # Create deployment PR
    gh pr create \
        --title "Production Deployment - $(date '+%Y-%m-%d %H:%M')" \
        --body "Deploying changes from staging to production
        
        **Staging Commit:** $staging_commit
        **Deployment Time:** $(date)
        
        **Pre-deployment Actions Completed:**
        - Staging validation passed
        - Resource capacity verified
        - Security policies validated
        - Monitoring confirmed operational
        
        **Post-deployment Actions Required:**
        - Monitor application health
        - Verify metrics and alerts
        - Confirm user experience
        " \
        --base "$PROD_BRANCH" \
        --head "$deploy_branch"
}
```

#### 2. Rollback Procedures
```bash
#!/bin/bash
# scripts/emergency-rollback.sh - Emergency production rollback

emergency_rollback() {
    local app_name="$1"
    local target_revision="${2:-HEAD~1}"
    
    log_error "EMERGENCY ROLLBACK INITIATED for $app_name"
    log_info "Target revision: $target_revision"
    
    # Immediate rollback via ArgoCD
    argocd app sync "$app_name" --revision "$target_revision"
    
    # Force sync if needed
    if ! wait_for_argo_sync "$app_name" 60; then
        log_warn "Normal sync failed, forcing hard refresh"
        argocd app sync "$app_name" --force --revision "$target_revision"
    fi
    
    # Verify rollback
    local current_revision
    current_revision=$(argocd app get "$app_name" -o json | jq -r '.status.sync.revision')
    
    log_info "Rollback completed to revision: $current_revision"
    
    # Send notifications
    send_emergency_notification "$app_name" "$current_revision"
    
    # Create incident ticket
    create_incident_ticket "$app_name" "$target_revision"
}

# Progressive rollback with canary
progressive_rollback() {
    local app_name="$1"
    local target_revision="$2"
    local canary_percentage="${3:-10}"
    
    log_info "Starting progressive rollback for $app_name"
    
    # Update canary deployment
    kubectl patch deployment "${app_name}-canary" -n production \
        -p '{"spec":{"template":{"metadata":{"labels":{"version":"rollback"}}}}}'
    
    # Wait for canary to be healthy
    kubectl rollout status deployment/"${app_name}-canary" -n production --timeout=300s
    
    # Check canary metrics
    if check_canary_health "$app_name" "rollback"; then
        log_success "Canary rollback successful, proceeding with full rollback"
        
        # Full rollback
        kubectl patch deployment "$app_name" -n production \
            -p '{"spec":{"template":{"metadata":{"labels":{"version":"rollback"}}}}}'
            
        kubectl rollout status deployment/"$app_name" -n production --timeout=600s
    else
        log_error "Canary rollback failed, aborting"
        return 1
    fi
}

check_canary_health() {
    local app_name="$1"
    local version="$2"
    local check_duration=300  # 5 minutes
    
    log_info "Monitoring canary health for ${check_duration}s..."
    
    local end_time=$(($(date +%s) + check_duration))
    
    while [[ $(date +%s) -lt $end_time ]]; do
        # Check error rate
        local error_rate
        error_rate=$(curl -s "http://prometheus:9090/api/v1/query?query=rate(http_requests_total{job=\"$app_name\",version=\"$version\",status=~\"5..\"}[5m])" | \
                    jq -r '.data.result[0].value[1] // "0"')
        
        if (( $(echo "$error_rate > 0.01" | bc -l) )); then  # >1% error rate
            log_error "High error rate detected: $error_rate"
            return 1
        fi
        
        # Check response time
        local p95_latency
        p95_latency=$(curl -s "http://prometheus:9090/api/v1/query?query=histogram_quantile(0.95,rate(http_request_duration_seconds_bucket{job=\"$app_name\",version=\"$version\"}[5m]))" | \
                     jq -r '.data.result[0].value[1] // "0"')
        
        if (( $(echo "$p95_latency > 2.0" | bc -l) )); then  # >2s p95 latency
            log_error "High latency detected: ${p95_latency}s"
            return 1
        fi
        
        sleep 30
    done
    
    log_success "Canary health check passed"
    return 0
}
```

### GitOps Security and Compliance

#### 1. Security Policies in Git
```yaml
# security/network-policies/production.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: production-isolation
  namespace: production
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
    ports:
    - protocol: TCP
      port: 8080
  - from:
    - namespaceSelector:
        matchLabels:
          name: monitoring
    ports:
    - protocol: TCP
      port: 9090
  egress:
  - to:
    - namespaceSelector:
        matchLabels:
          name: kube-system
  - to: []
    ports:
    - protocol: TCP
      port: 443
    - protocol: TCP
      port: 53
    - protocol: UDP
      port: 53
---
# security/pod-security/production.yaml
apiVersion: v1
kind: LimitRange
metadata:
  name: production-limits
  namespace: production
spec:
  limits:
  - type: Container
    default:
      cpu: 100m
      memory: 128Mi
    defaultRequest:
      cpu: 50m
      memory: 64Mi
    max:
      cpu: 2000m
      memory: 4Gi
    min:
      cpu: 10m
      memory: 16Mi
```

#### 2. RBAC for GitOps
```yaml
# security/rbac/argocd.yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: argocd-production
rules:
- apiGroups: [""]
  resources: ["*"]
  verbs: ["*"]
- apiGroups: ["apps"]
  resources: ["*"]
  verbs: ["*"]
- apiGroups: ["networking.k8s.io"]
  resources: ["*"]
  verbs: ["*"]
- apiGroups: ["policy"]
  resources: ["*"]
  verbs: ["*"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: argocd-production
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: argocd-production
subjects:
- kind: ServiceAccount
  name: argocd-application-controller
  namespace: argocd
---
# Restricted role for developers
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: production
  name: developer-read
rules:
- apiGroups: [""]
  resources: ["pods", "pods/log", "services", "configmaps"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["apps"]
  resources: ["deployments", "replicasets"]
  verbs: ["get", "list", "watch"]
```

#### 3. Compliance and Auditing
```bash
#!/bin/bash
# scripts/compliance-check.sh - GitOps compliance validation

check_git_compliance() {
    log_info "Checking Git compliance..."
    
    # Verify all changes are signed
    local unsigned_commits
    unsigned_commits=$(git log --pretty="format:%H %G?" | grep -v " G" | wc -l)
    
    if [[ $unsigned_commits -gt 0 ]]; then
        log_error "Found $unsigned_commits unsigned commits"
        git log --pretty="format:%H %s %G?" | grep -v " G"
        return 1
    fi
    
    # Check branch protection
    local protected_branches=("main" "production" "staging")
    for branch in "${protected_branches[@]}"; do
        if ! gh api "repos/:owner/:repo/branches/$branch/protection" >/dev/null 2>&1; then
            log_error "Branch $branch is not protected"
            return 1
        fi
    done
    
    # Verify required reviews
    local min_reviewers
    min_reviewers=$(gh api "repos/:owner/:repo/branches/production/protection" | \
                   jq -r '.required_pull_request_reviews.required_approving_review_count')
    
    if [[ $min_reviewers -lt 2 ]]; then
        log_error "Production branch requires at least 2 reviewers (current: $min_reviewers)"
        return 1
    fi
    
    log_success "Git compliance checks passed"
}

audit_deployment_history() {
    log_info "Auditing deployment history..."
    
    # Generate deployment audit report
    local report_file="/tmp/deployment_audit_$(date +%Y%m%d).txt"
    
    {
        echo "=== GitOps Deployment Audit Report ==="
        echo "Generated: $(date)"
        echo "Repository: $(git remote get-url origin)"
        echo "======================================"
        echo
        
        echo "Recent Production Deployments (Last 30 days):"
        git log --since="30 days ago" --grep="Merge.*production" \
            --pretty="format:%ad | %s | %an" --date=short
        echo
        
        echo "Security-related Changes:"
        git log --since="30 days ago" --grep="security\|CVE\|vulnerability" \
            --pretty="format:%ad | %s | %an | %H" --date=short
        echo
        
        echo "Rollback Events:"
        git log --since="30 days ago" --grep="rollback\|revert" \
            --pretty="format:%ad | %s | %an | %H" --date=short
        echo
        
        echo "Configuration Changes:"
        git log --since="30 days ago" --name-only \
            --pretty="format:%ad | %s | %an" --date=short \
            -- "*.yaml" "*.yml" | grep -E "\.(yaml|yml)$" | sort | uniq -c
            
    } > "$report_file"
    
    log_info "Audit report generated: $report_file"
    
    # Send to compliance system if configured
    if [[ -n "${COMPLIANCE_WEBHOOK:-}" ]]; then
        curl -X POST -H "Content-Type: text/plain" \
             --data-binary "@$report_file" \
             "$COMPLIANCE_WEBHOOK"
    fi
}

validate_security_policies() {
    log_info "Validating security policies..."
    
    # Check for required security annotations
    local security_files
    security_files=$(find . -name "*.yaml" -o -name "*.yml" | xargs grep -l "kind: Deployment")
    
    while IFS= read -r file; do
        if ! grep -q "securityContext" "$file"; then
            log_warn "Deployment missing securityContext: $file"
        fi
        
        if ! grep -q "resources:" "$file"; then
            log_warn "Deployment missing resource limits: $file"
        fi
        
        if grep -q "privileged: true" "$file"; then
            log_error "Privileged container found: $file"
        fi
        
    done <<< "$security_files"
}
```

This provides a complete production GitOps implementation with proper change management, security policies, compliance checking, and emergency procedures.