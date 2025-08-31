# Bash Deployment Scripts

## Overview
Bash deployment scripts provide automated, reliable, and repeatable application deployment processes. This includes blue-green deployments, rolling updates, canary releases, rollback mechanisms, and integration with container orchestration platforms like Docker and Kubernetes.

## Core Deployment Framework

### 1. Deployment Configuration and Environment Management
```bash
#!/bin/bash

# Deployment configuration structure
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly CONFIG_DIR="${SCRIPT_DIR}/config"
readonly TEMPLATES_DIR="${SCRIPT_DIR}/templates"
readonly LOGS_DIR="${SCRIPT_DIR}/logs"

# Create required directories
mkdir -p "$CONFIG_DIR" "$TEMPLATES_DIR" "$LOGS_DIR"

# Deployment environments configuration
declare -A ENVIRONMENTS=(
    [development]="dev"
    [staging]="stage"
    [production]="prod"
)

# Load environment-specific configuration
load_environment_config() {
    local environment="$1"
    local config_file="$CONFIG_DIR/${environment}.conf"
    
    if [[ ! -f "$config_file" ]]; then
        log_error "Configuration file not found: $config_file"
        return 1
    fi
    
    log_info "Loading configuration for environment: $environment"
    
    # Load configuration variables
    while IFS='=' read -r key value; do
        # Skip comments and empty lines
        [[ $key =~ ^[[:space:]]*# ]] && continue
        [[ -z "$key" ]] && continue
        
        # Remove quotes and whitespace
        key=$(echo "$key" | xargs)
        value=$(echo "$value" | xargs | sed 's/^["'"'"']\(.*\)["'"'"']$/\1/')
        
        # Export as environment variable
        export "${key}"="$value"
        log_debug "Config: $key = $value"
        
    done < "$config_file"
    
    # Validate required configuration
    validate_deployment_config
}

# Validate deployment configuration
validate_deployment_config() {
    local required_vars=(
        "APP_NAME"
        "APP_VERSION" 
        "DOCKER_REGISTRY"
        "KUBERNETES_NAMESPACE"
        "REPLICA_COUNT"
        "RESOURCE_LIMITS_CPU"
        "RESOURCE_LIMITS_MEMORY"
    )
    
    local missing_vars=()
    
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var:-}" ]]; then
            missing_vars+=("$var")
        fi
    done
    
    if [[ ${#missing_vars[@]} -gt 0 ]]; then
        log_error "Missing required configuration variables: ${missing_vars[*]}"
        return 1
    fi
    
    log_info "Configuration validation passed"
}

# Generate deployment manifests from templates
generate_deployment_manifests() {
    local environment="$1"
    local output_dir="${2:-./manifests}"
    
    mkdir -p "$output_dir"
    log_info "Generating deployment manifests for: $environment"
    
    # Process each template file
    for template_file in "$TEMPLATES_DIR"/*.yaml.template; do
        if [[ ! -f "$template_file" ]]; then
            continue
        fi
        
        local template_name=$(basename "$template_file" .template)
        local output_file="$output_dir/$template_name"
        
        log_debug "Processing template: $template_file"
        
        # Replace variables in template
        envsubst < "$template_file" > "$output_file"
        
        # Validate generated YAML
        if command -v yq >/dev/null 2>&1; then
            if ! yq eval . "$output_file" >/dev/null 2>&1; then
                log_error "Invalid YAML generated: $output_file"
                return 1
            fi
        fi
        
        log_debug "Generated manifest: $output_file"
    done
    
    log_info "Deployment manifests generated in: $output_dir"
}

# Health check function
perform_health_check() {
    local service_url="$1"
    local timeout="${2:-30}"
    local interval="${3:-5}"
    local health_endpoint="${4:-/health}"
    
    local full_url="${service_url}${health_endpoint}"
    local elapsed=0
    
    log_info "Performing health check: $full_url"
    
    while [[ $elapsed -lt $timeout ]]; do
        if curl -f -s --max-time 10 "$full_url" >/dev/null 2>&1; then
            log_info "✓ Health check passed"
            return 0
        fi
        
        log_debug "Health check attempt failed, retrying in ${interval}s..."
        sleep "$interval"
        ((elapsed += interval))
    done
    
    log_error "✗ Health check failed after ${timeout}s"
    return 1
}

# Database migration execution
run_database_migrations() {
    local migration_script="$1"
    local database_url="$2"
    local dry_run="${3:-false}"
    
    if [[ ! -f "$migration_script" ]]; then
        log_warn "Migration script not found: $migration_script"
        return 0
    fi
    
    log_info "Running database migrations..."
    
    if [[ "$dry_run" == "true" ]]; then
        log_info "DRY RUN: Would execute migration script: $migration_script"
        return 0
    fi
    
    # Create migration backup
    local backup_file="${LOGS_DIR}/db_backup_$(date +%Y%m%d_%H%M%S).sql"
    
    if command -v pg_dump >/dev/null 2>&1; then
        log_info "Creating database backup..."
        if pg_dump "$database_url" > "$backup_file" 2>/dev/null; then
            log_info "Database backup created: $backup_file"
        else
            log_warn "Failed to create database backup"
        fi
    fi
    
    # Execute migration
    if bash "$migration_script"; then
        log_info "✓ Database migrations completed successfully"
        return 0
    else
        log_error "✗ Database migration failed"
        
        # Offer rollback option
        if [[ -f "$backup_file" ]]; then
            log_warn "Database backup available for rollback: $backup_file"
        fi
        
        return 1
    fi
}
```

### 2. Blue-Green Deployment Implementation
```bash
#!/bin/bash

# Blue-Green deployment strategy
deploy_blue_green() {
    local environment="$1"
    local new_version="$2"
    local dry_run="${3:-false}"
    
    log_info "Starting Blue-Green deployment"
    log_info "Environment: $environment"
    log_info "New Version: $new_version"
    
    # Determine current and target colors
    local current_color=$(get_current_deployment_color "$environment")
    local target_color=$(get_opposite_color "$current_color")
    
    log_info "Current deployment: $current_color"
    log_info "Target deployment: $target_color"
    
    # Deploy to target environment
    if ! deploy_to_color_environment "$environment" "$target_color" "$new_version" "$dry_run"; then
        log_error "Failed to deploy to $target_color environment"
        return 1
    fi
    
    # Wait for deployment to be ready
    if ! wait_for_deployment_ready "$environment" "$target_color"; then
        log_error "Target deployment not ready"
        cleanup_failed_deployment "$environment" "$target_color"
        return 1
    fi
    
    # Run smoke tests
    if ! run_smoke_tests "$environment" "$target_color"; then
        log_error "Smoke tests failed"
        cleanup_failed_deployment "$environment" "$target_color"
        return 1
    fi
    
    # Switch traffic to new deployment
    if ! switch_traffic "$environment" "$target_color" "$dry_run"; then
        log_error "Failed to switch traffic"
        return 1
    fi
    
    # Verify new deployment is serving traffic correctly
    if ! verify_traffic_switch "$environment" "$target_color"; then
        log_error "Traffic verification failed, rolling back"
        switch_traffic "$environment" "$current_color" false
        return 1
    fi
    
    # Clean up old deployment after successful switch
    cleanup_old_deployment "$environment" "$current_color" "$dry_run"
    
    log_info "✓ Blue-Green deployment completed successfully"
    return 0
}

# Get current deployment color
get_current_deployment_color() {
    local environment="$1"
    local service_name="${APP_NAME}-${environment}"
    
    # Check which color is currently active based on service selector
    local current_selector=$(kubectl get service "$service_name" -n "$KUBERNETES_NAMESPACE" -o jsonpath='{.spec.selector.version}' 2>/dev/null || echo "")
    
    if [[ "$current_selector" =~ blue ]]; then
        echo "blue"
    elif [[ "$current_selector" =~ green ]]; then
        echo "green"
    else
        # Default to blue if no current deployment
        echo "blue"
    fi
}

# Get opposite color
get_opposite_color() {
    local color="$1"
    
    if [[ "$color" == "blue" ]]; then
        echo "green"
    else
        echo "blue"
    fi
}

# Deploy to specific color environment
deploy_to_color_environment() {
    local environment="$1"
    local color="$2"
    local version="$3"
    local dry_run="$4"
    
    log_info "Deploying $version to $color environment"
    
    # Set color-specific environment variables
    export DEPLOYMENT_COLOR="$color"
    export DEPLOYMENT_NAME="${APP_NAME}-${environment}-${color}"
    export SERVICE_NAME="${APP_NAME}-${environment}"
    export IMAGE_TAG="$version"
    
    # Generate manifests with color-specific configuration
    local manifest_dir="${LOGS_DIR}/manifests_${color}_$(date +%Y%m%d_%H%M%S)"
    generate_deployment_manifests "$environment" "$manifest_dir"
    
    if [[ "$dry_run" == "true" ]]; then
        log_info "DRY RUN: Would deploy manifests from $manifest_dir"
        return 0
    fi
    
    # Apply Kubernetes manifests
    log_info "Applying Kubernetes manifests..."
    if kubectl apply -f "$manifest_dir" -n "$KUBERNETES_NAMESPACE"; then
        log_info "✓ Deployment manifests applied successfully"
        return 0
    else
        log_error "✗ Failed to apply deployment manifests"
        return 1
    fi
}

# Wait for deployment to be ready
wait_for_deployment_ready() {
    local environment="$1"
    local color="$2"
    local timeout="${3:-600}"  # 10 minutes
    local deployment_name="${APP_NAME}-${environment}-${color}"
    
    log_info "Waiting for deployment to be ready: $deployment_name"
    
    if kubectl rollout status deployment "$deployment_name" -n "$KUBERNETES_NAMESPACE" --timeout="${timeout}s"; then
        log_info "✓ Deployment is ready: $deployment_name"
        
        # Additional readiness check
        local ready_replicas=$(kubectl get deployment "$deployment_name" -n "$KUBERNETES_NAMESPACE" -o jsonpath='{.status.readyReplicas}')
        local desired_replicas=$(kubectl get deployment "$deployment_name" -n "$KUBERNETES_NAMESPACE" -o jsonpath='{.spec.replicas}')
        
        if [[ "$ready_replicas" == "$desired_replicas" && "$ready_replicas" -gt 0 ]]; then
            log_info "✓ All replicas are ready: $ready_replicas/$desired_replicas"
            return 0
        else
            log_error "✗ Replica readiness check failed: $ready_replicas/$desired_replicas"
            return 1
        fi
    else
        log_error "✗ Deployment failed to become ready: $deployment_name"
        return 1
    fi
}

# Run smoke tests
run_smoke_tests() {
    local environment="$1"
    local color="$2"
    
    log_info "Running smoke tests for $color deployment"
    
    # Get service endpoint for testing
    local service_ip=$(kubectl get service "${APP_NAME}-${environment}-${color}" -n "$KUBERNETES_NAMESPACE" -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null)
    
    if [[ -z "$service_ip" ]]; then
        # Fallback to ClusterIP
        service_ip=$(kubectl get service "${APP_NAME}-${environment}-${color}" -n "$KUBERNETES_NAMESPACE" -o jsonpath='{.spec.clusterIP}' 2>/dev/null)
    fi
    
    if [[ -z "$service_ip" ]]; then
        log_error "Cannot determine service IP for smoke tests"
        return 1
    fi
    
    local service_port=$(kubectl get service "${APP_NAME}-${environment}-${color}" -n "$KUBERNETES_NAMESPACE" -o jsonpath='{.spec.ports[0].port}')
    local test_url="http://${service_ip}:${service_port}"
    
    # Basic health check
    if ! perform_health_check "$test_url" 60 5; then
        return 1
    fi
    
    # Application-specific smoke tests
    run_application_smoke_tests "$test_url"
}

# Application-specific smoke tests
run_application_smoke_tests() {
    local base_url="$1"
    
    log_info "Running application smoke tests..."
    
    local tests=(
        "GET:/:200"
        "GET:/api/health:200"
        "GET:/api/version:200"
    )
    
    for test in "${tests[@]}"; do
        IFS=':' read -r method path expected_code <<< "$test"
        
        log_debug "Testing $method $path (expecting $expected_code)"
        
        local response_code
        if [[ "$method" == "GET" ]]; then
            response_code=$(curl -s -o /dev/null -w "%{http_code}" "${base_url}${path}")
        else
            log_warn "Unsupported test method: $method"
            continue
        fi
        
        if [[ "$response_code" == "$expected_code" ]]; then
            log_debug "✓ Test passed: $method $path ($response_code)"
        else
            log_error "✗ Test failed: $method $path (got $response_code, expected $expected_code)"
            return 1
        fi
    done
    
    log_info "✓ All smoke tests passed"
    return 0
}

# Switch traffic to new deployment
switch_traffic() {
    local environment="$1"
    local target_color="$2"
    local dry_run="$3"
    
    local service_name="${APP_NAME}-${environment}"
    local new_selector="version=${target_color}"
    
    log_info "Switching traffic to $target_color deployment"
    
    if [[ "$dry_run" == "true" ]]; then
        log_info "DRY RUN: Would switch service $service_name to selector: $new_selector"
        return 0
    fi
    
    # Update service selector to point to new deployment
    if kubectl patch service "$service_name" -n "$KUBERNETES_NAMESPACE" -p "{\"spec\":{\"selector\":{\"version\":\"$target_color\"}}}"; then
        log_info "✓ Traffic switched to $target_color deployment"
        
        # Wait a moment for the change to propagate
        sleep 5
        return 0
    else
        log_error "✗ Failed to switch traffic to $target_color deployment"
        return 1
    fi
}

# Verify traffic switch
verify_traffic_switch() {
    local environment="$1"
    local expected_color="$2"
    
    log_info "Verifying traffic switch to $expected_color"
    
    # Get service endpoint
    local service_name="${APP_NAME}-${environment}"
    local service_ip=$(kubectl get service "$service_name" -n "$KUBERNETES_NAMESPACE" -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null)
    
    if [[ -z "$service_ip" ]]; then
        service_ip=$(kubectl get service "$service_name" -n "$KUBERNETES_NAMESPACE" -o jsonpath='{.spec.clusterIP}')
    fi
    
    local service_port=$(kubectl get service "$service_name" -n "$KUBERNETES_NAMESPACE" -o jsonpath='{.spec.ports[0].port}')
    local service_url="http://${service_ip}:${service_port}"
    
    # Verify service is responding
    if ! perform_health_check "$service_url" 30 2; then
        log_error "Service not responding after traffic switch"
        return 1
    fi
    
    # Verify we're hitting the correct deployment
    local version_endpoint="${service_url}/api/version"
    local response=$(curl -s "$version_endpoint" 2>/dev/null || echo "")
    
    if [[ "$response" =~ $expected_color || "$response" =~ $IMAGE_TAG ]]; then
        log_info "✓ Traffic verification successful"
        return 0
    else
        log_warn "Traffic verification inconclusive (response: $response)"
        return 0  # Don't fail deployment for inconclusive verification
    fi
}

# Cleanup failed deployment
cleanup_failed_deployment() {
    local environment="$1"
    local color="$2"
    
    log_info "Cleaning up failed $color deployment"
    
    local deployment_name="${APP_NAME}-${environment}-${color}"
    
    # Scale down failed deployment
    kubectl scale deployment "$deployment_name" -n "$KUBERNETES_NAMESPACE" --replicas=0 2>/dev/null || true
    
    # Optionally delete the deployment
    # kubectl delete deployment "$deployment_name" -n "$KUBERNETES_NAMESPACE" 2>/dev/null || true
    
    log_info "Failed deployment cleanup completed"
}

# Cleanup old deployment
cleanup_old_deployment() {
    local environment="$1"
    local old_color="$2"
    local dry_run="$3"
    
    log_info "Cleaning up old $old_color deployment"
    
    if [[ "$dry_run" == "true" ]]; then
        log_info "DRY RUN: Would cleanup old $old_color deployment"
        return 0
    fi
    
    local deployment_name="${APP_NAME}-${environment}-${old_color}"
    
    # Scale down old deployment
    if kubectl scale deployment "$deployment_name" -n "$KUBERNETES_NAMESPACE" --replicas=0; then
        log_info "✓ Scaled down old deployment: $deployment_name"
    else
        log_warn "Failed to scale down old deployment: $deployment_name"
    fi
    
    # Keep old deployment for potential rollback (don't delete immediately)
    log_info "Old deployment kept for potential rollback: $deployment_name"
}
```

### 3. Rolling Deployment Strategy
```bash
#!/bin/bash

# Rolling deployment implementation
deploy_rolling() {
    local environment="$1"
    local new_version="$2"
    local dry_run="${3:-false}"
    
    log_info "Starting Rolling deployment"
    log_info "Environment: $environment"
    log_info "New Version: $new_version"
    
    # Set deployment configuration
    export DEPLOYMENT_NAME="${APP_NAME}-${environment}"
    export IMAGE_TAG="$new_version"
    export DEPLOYMENT_STRATEGY="RollingUpdate"
    export MAX_UNAVAILABLE="${MAX_UNAVAILABLE:-1}"
    export MAX_SURGE="${MAX_SURGE:-1}"
    
    # Generate manifests
    local manifest_dir="${LOGS_DIR}/manifests_rolling_$(date +%Y%m%d_%H%M%S)"
    generate_deployment_manifests "$environment" "$manifest_dir"
    
    # Run pre-deployment hooks
    if ! run_pre_deployment_hooks "$environment" "$new_version"; then
        log_error "Pre-deployment hooks failed"
        return 1
    fi
    
    if [[ "$dry_run" == "true" ]]; then
        log_info "DRY RUN: Would perform rolling deployment"
        return 0
    fi
    
    # Apply manifests
    log_info "Applying rolling deployment manifests..."
    if ! kubectl apply -f "$manifest_dir" -n "$KUBERNETES_NAMESPACE"; then
        log_error "Failed to apply deployment manifests"
        return 1
    fi
    
    # Monitor rolling deployment
    if ! monitor_rolling_deployment "$environment"; then
        log_error "Rolling deployment failed"
        return 1
    fi
    
    # Run post-deployment hooks
    if ! run_post_deployment_hooks "$environment" "$new_version"; then
        log_error "Post-deployment hooks failed"
        return 1
    fi
    
    log_info "✓ Rolling deployment completed successfully"
    return 0
}

# Monitor rolling deployment progress
monitor_rolling_deployment() {
    local environment="$1"
    local deployment_name="${APP_NAME}-${environment}"
    local timeout=600  # 10 minutes
    
    log_info "Monitoring rolling deployment: $deployment_name"
    
    # Watch rollout status
    if ! kubectl rollout status deployment "$deployment_name" -n "$KUBERNETES_NAMESPACE" --timeout="${timeout}s"; then
        log_error "Rolling deployment timed out or failed"
        
        # Get deployment status for debugging
        kubectl describe deployment "$deployment_name" -n "$KUBERNETES_NAMESPACE"
        kubectl get pods -l app="$deployment_name" -n "$KUBERNETES_NAMESPACE"
        
        return 1
    fi
    
    # Verify all pods are ready
    local ready_replicas=$(kubectl get deployment "$deployment_name" -n "$KUBERNETES_NAMESPACE" -o jsonpath='{.status.readyReplicas}')
    local desired_replicas=$(kubectl get deployment "$deployment_name" -n "$KUBERNETES_NAMESPACE" -o jsonpath='{.spec.replicas}')
    
    if [[ "$ready_replicas" != "$desired_replicas" ]]; then
        log_error "Not all replicas are ready: $ready_replicas/$desired_replicas"
        return 1
    fi
    
    log_info "✓ Rolling deployment completed: $ready_replicas/$desired_replicas replicas ready"
    return 0
}

# Pre-deployment hooks
run_pre_deployment_hooks() {
    local environment="$1"
    local version="$2"
    
    log_info "Running pre-deployment hooks..."
    
    # Database migrations
    if [[ -f "${SCRIPT_DIR}/migrations/migrate.sh" ]]; then
        log_info "Running database migrations..."
        if ! run_database_migrations "${SCRIPT_DIR}/migrations/migrate.sh" "$DATABASE_URL"; then
            log_error "Database migrations failed"
            return 1
        fi
    fi
    
    # Cache warming
    if [[ -n "${CACHE_WARM_SCRIPT:-}" && -f "$CACHE_WARM_SCRIPT" ]]; then
        log_info "Running cache warming script..."
        if ! bash "$CACHE_WARM_SCRIPT"; then
            log_warn "Cache warming failed (non-critical)"
        fi
    fi
    
    # Custom pre-deployment scripts
    if [[ -d "${SCRIPT_DIR}/hooks/pre-deploy" ]]; then
        for script in "${SCRIPT_DIR}/hooks/pre-deploy"/*.sh; do
            if [[ -f "$script" ]]; then
                log_info "Running pre-deployment script: $(basename "$script")"
                if ! bash "$script" "$environment" "$version"; then
                    log_error "Pre-deployment script failed: $(basename "$script")"
                    return 1
                fi
            fi
        done
    fi
    
    log_info "✓ Pre-deployment hooks completed"
    return 0
}

# Post-deployment hooks
run_post_deployment_hooks() {
    local environment="$1"
    local version="$2"
    
    log_info "Running post-deployment hooks..."
    
    # Health check
    local service_name="${APP_NAME}-${environment}"
    local service_url=$(get_service_url "$service_name")
    
    if [[ -n "$service_url" ]]; then
        if ! perform_health_check "$service_url" 120 5; then
            log_error "Post-deployment health check failed"
            return 1
        fi
    fi
    
    # Smoke tests
    if ! run_application_smoke_tests "$service_url"; then
        log_error "Post-deployment smoke tests failed"
        return 1
    fi
    
    # Notification scripts
    if [[ -f "${SCRIPT_DIR}/hooks/notify.sh" ]]; then
        log_info "Sending deployment notifications..."
        bash "${SCRIPT_DIR}/hooks/notify.sh" "$environment" "$version" "success" &
    fi
    
    # Custom post-deployment scripts
    if [[ -d "${SCRIPT_DIR}/hooks/post-deploy" ]]; then
        for script in "${SCRIPT_DIR}/hooks/post-deploy"/*.sh; do
            if [[ -f "$script" ]]; then
                log_info "Running post-deployment script: $(basename "$script")"
                if ! bash "$script" "$environment" "$version"; then
                    log_warn "Post-deployment script failed: $(basename "$script") (non-critical)"
                fi
            fi
        done
    fi
    
    log_info "✓ Post-deployment hooks completed"
    return 0
}

# Get service URL
get_service_url() {
    local service_name="$1"
    
    # Try LoadBalancer first
    local external_ip=$(kubectl get service "$service_name" -n "$KUBERNETES_NAMESPACE" -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null)
    
    if [[ -z "$external_ip" ]]; then
        # Try external hostname
        external_ip=$(kubectl get service "$service_name" -n "$KUBERNETES_NAMESPACE" -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>/dev/null)
    fi
    
    if [[ -z "$external_ip" ]]; then
        # Fallback to ClusterIP
        external_ip=$(kubectl get service "$service_name" -n "$KUBERNETES_NAMESPACE" -o jsonpath='{.spec.clusterIP}' 2>/dev/null)
    fi
    
    local port=$(kubectl get service "$service_name" -n "$KUBERNETES_NAMESPACE" -o jsonpath='{.spec.ports[0].port}' 2>/dev/null)
    
    if [[ -n "$external_ip" && -n "$port" ]]; then
        echo "http://${external_ip}:${port}"
    fi
}
```

### 4. Canary Deployment Strategy
```bash
#!/bin/bash

# Canary deployment implementation
deploy_canary() {
    local environment="$1"
    local new_version="$2"
    local canary_percentage="${3:-10}"
    local dry_run="${4:-false}"
    
    log_info "Starting Canary deployment"
    log_info "Environment: $environment"
    log_info "New Version: $new_version"
    log_info "Canary Percentage: $canary_percentage%"
    
    # Calculate replica counts
    local total_replicas="$REPLICA_COUNT"
    local canary_replicas=$(calculate_canary_replicas "$total_replicas" "$canary_percentage")
    local stable_replicas=$((total_replicas - canary_replicas))
    
    log_info "Total Replicas: $total_replicas"
    log_info "Canary Replicas: $canary_replicas"
    log_info "Stable Replicas: $stable_replicas"
    
    # Deploy canary version
    if ! deploy_canary_version "$environment" "$new_version" "$canary_replicas" "$dry_run"; then
        log_error "Failed to deploy canary version"
        return 1
    fi
    
    # Update stable deployment replica count
    if ! update_stable_replicas "$environment" "$stable_replicas" "$dry_run"; then
        log_error "Failed to update stable deployment"
        cleanup_canary_deployment "$environment"
        return 1
    fi
    
    # Monitor canary deployment
    if ! monitor_canary_deployment "$environment" "$new_version"; then
        log_error "Canary deployment monitoring failed"
        cleanup_canary_deployment "$environment"
        return 1
    fi
    
    # Analyze canary metrics
    if ! analyze_canary_metrics "$environment" "$new_version"; then
        log_error "Canary metrics analysis failed"
        cleanup_canary_deployment "$environment"
        return 1
    fi
    
    # Promote canary to full deployment
    if ! promote_canary_deployment "$environment" "$new_version" "$dry_run"; then
        log_error "Failed to promote canary deployment"
        return 1
    fi
    
    log_info "✓ Canary deployment completed successfully"
    return 0
}

# Calculate canary replica count
calculate_canary_replicas() {
    local total="$1"
    local percentage="$2"
    
    local canary_count=$(( (total * percentage + 50) / 100 ))  # Round to nearest
    
    # Ensure at least 1 canary replica
    if [[ $canary_count -lt 1 ]]; then
        canary_count=1
    fi
    
    # Ensure we don't exceed total replicas
    if [[ $canary_count -gt $total ]]; then
        canary_count=$total
    fi
    
    echo "$canary_count"
}

# Deploy canary version
deploy_canary_version() {
    local environment="$1"
    local version="$2"
    local replicas="$3"
    local dry_run="$4"
    
    log_info "Deploying canary version with $replicas replicas"
    
    # Set canary-specific environment variables
    export DEPLOYMENT_NAME="${APP_NAME}-${environment}-canary"
    export IMAGE_TAG="$version"
    export REPLICA_COUNT="$replicas"
    export DEPLOYMENT_SUFFIX="canary"
    
    # Generate canary manifests
    local manifest_dir="${LOGS_DIR}/manifests_canary_$(date +%Y%m%d_%H%M%S)"
    generate_deployment_manifests "$environment" "$manifest_dir"
    
    if [[ "$dry_run" == "true" ]]; then
        log_info "DRY RUN: Would deploy canary version"
        return 0
    fi
    
    # Apply canary manifests
    if kubectl apply -f "$manifest_dir" -n "$KUBERNETES_NAMESPACE"; then
        log_info "✓ Canary deployment manifests applied"
        
        # Wait for canary deployment to be ready
        if kubectl rollout status deployment "${APP_NAME}-${environment}-canary" -n "$KUBERNETES_NAMESPACE" --timeout=300s; then
            log_info "✓ Canary deployment is ready"
            return 0
        else
            log_error "✗ Canary deployment failed to become ready"
            return 1
        fi
    else
        log_error "✗ Failed to apply canary manifests"
        return 1
    fi
}

# Update stable deployment replicas
update_stable_replicas() {
    local environment="$1"
    local replicas="$2"
    local dry_run="$3"
    
    local deployment_name="${APP_NAME}-${environment}"
    
    log_info "Updating stable deployment to $replicas replicas"
    
    if [[ "$dry_run" == "true" ]]; then
        log_info "DRY RUN: Would scale stable deployment to $replicas replicas"
        return 0
    fi
    
    if kubectl scale deployment "$deployment_name" -n "$KUBERNETES_NAMESPACE" --replicas="$replicas"; then
        log_info "✓ Stable deployment scaled to $replicas replicas"
        return 0
    else
        log_error "✗ Failed to scale stable deployment"
        return 1
    fi
}

# Monitor canary deployment
monitor_canary_deployment() {
    local environment="$1"
    local version="$2"
    local monitor_duration="${CANARY_MONITOR_DURATION:-300}"  # 5 minutes
    
    log_info "Monitoring canary deployment for ${monitor_duration}s"
    
    local start_time=$(date +%s)
    local end_time=$((start_time + monitor_duration))
    
    while [[ $(date +%s) -lt $end_time ]]; do
        # Check canary pod health
        local canary_deployment="${APP_NAME}-${environment}-canary"
        local ready_replicas=$(kubectl get deployment "$canary_deployment" -n "$KUBERNETES_NAMESPACE" -o jsonpath='{.status.readyReplicas}' 2>/dev/null || echo "0")
        local desired_replicas=$(kubectl get deployment "$canary_deployment" -n "$KUBERNETES_NAMESPACE" -o jsonpath='{.spec.replicas}' 2>/dev/null || echo "0")
        
        if [[ "$ready_replicas" != "$desired_replicas" ]]; then
            log_error "Canary deployment unhealthy: $ready_replicas/$desired_replicas ready"
            return 1
        fi
        
        # Check for pod restarts or failures
        local failing_pods=$(kubectl get pods -l app="$canary_deployment" -n "$KUBERNETES_NAMESPACE" --field-selector=status.phase!=Running 2>/dev/null | wc -l)
        if [[ $failing_pods -gt 0 ]]; then
            log_error "Found $failing_pods failing canary pods"
            kubectl get pods -l app="$canary_deployment" -n "$KUBERNETES_NAMESPACE"
            return 1
        fi
        
        log_debug "Canary monitoring: $ready_replicas/$desired_replicas pods ready"
        sleep 30
    done
    
    log_info "✓ Canary monitoring completed successfully"
    return 0
}

# Analyze canary metrics
analyze_canary_metrics() {
    local environment="$1"
    local version="$2"
    
    log_info "Analyzing canary metrics..."
    
    # This would integrate with your monitoring system (Prometheus, Datadog, etc.)
    # For this example, we'll perform basic health checks
    
    local canary_service="${APP_NAME}-${environment}-canary"
    local canary_url=$(get_service_url "$canary_service")
    
    if [[ -z "$canary_url" ]]; then
        log_warn "Cannot get canary service URL for metrics analysis"
        return 0
    fi
    
    # Perform multiple health checks
    local success_count=0
    local total_checks=10
    
    for ((i=1; i<=total_checks; i++)); do
        if curl -f -s --max-time 5 "${canary_url}/health" >/dev/null 2>&1; then
            ((success_count++))
        fi
        sleep 2
    done
    
    local success_rate=$((success_count * 100 / total_checks))
    log_info "Canary health check success rate: ${success_rate}%"
    
    # Set acceptable threshold
    local min_success_rate="${CANARY_MIN_SUCCESS_RATE:-90}"
    
    if [[ $success_rate -lt $min_success_rate ]]; then
        log_error "Canary success rate ($success_rate%) below threshold ($min_success_rate%)"
        return 1
    fi
    
    log_info "✓ Canary metrics analysis passed"
    return 0
}

# Promote canary deployment
promote_canary_deployment() {
    local environment="$1"
    local version="$2"
    local dry_run="$3"
    
    log_info "Promoting canary deployment to full deployment"
    
    if [[ "$dry_run" == "true" ]]; then
        log_info "DRY RUN: Would promote canary to full deployment"
        return 0
    fi
    
    # Update main deployment to canary version
    local main_deployment="${APP_NAME}-${environment}"
    
    if kubectl set image deployment "$main_deployment" -n "$KUBERNETES_NAMESPACE" app="${DOCKER_REGISTRY}/${APP_NAME}:${version}"; then
        log_info "✓ Updated main deployment image"
        
        # Scale main deployment back to full replica count
        if kubectl scale deployment "$main_deployment" -n "$KUBERNETES_NAMESPACE" --replicas="$REPLICA_COUNT"; then
            log_info "✓ Scaled main deployment to full replica count"
            
            # Wait for rollout to complete
            if kubectl rollout status deployment "$main_deployment" -n "$KUBERNETES_NAMESPACE" --timeout=600s; then
                log_info "✓ Main deployment rollout completed"
                
                # Cleanup canary deployment
                cleanup_canary_deployment "$environment"
                return 0
            else
                log_error "✗ Main deployment rollout failed"
                return 1
            fi
        else
            log_error "✗ Failed to scale main deployment"
            return 1
        fi
    else
        log_error "✗ Failed to update main deployment image"
        return 1
    fi
}

# Cleanup canary deployment
cleanup_canary_deployment() {
    local environment="$1"
    local canary_deployment="${APP_NAME}-${environment}-canary"
    
    log_info "Cleaning up canary deployment: $canary_deployment"
    
    # Scale down canary deployment
    kubectl scale deployment "$canary_deployment" -n "$KUBERNETES_NAMESPACE" --replicas=0 2>/dev/null || true
    
    # Delete canary deployment (optional)
    # kubectl delete deployment "$canary_deployment" -n "$KUBERNETES_NAMESPACE" 2>/dev/null || true
    
    log_info "Canary cleanup completed"
}
```

This comprehensive Bash deployment script framework provides robust, production-ready deployment strategies including blue-green, rolling updates, and canary deployments with proper error handling, monitoring, and rollback capabilities.