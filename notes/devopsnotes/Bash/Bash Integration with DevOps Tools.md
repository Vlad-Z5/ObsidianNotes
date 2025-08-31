# Bash Integration with DevOps Tools

## Overview
Bash integration with DevOps tools covers comprehensive automation patterns for seamlessly working with containerization platforms, orchestration systems, CI/CD pipelines, cloud providers, monitoring tools, and infrastructure as code solutions using shell scripts.

## Container Orchestration Integration

### 1. Docker Integration Framework
```bash
#!/bin/bash

# Docker management framework
readonly DOCKER_REGISTRY="${DOCKER_REGISTRY:-docker.io}"
readonly DOCKER_NAMESPACE="${DOCKER_NAMESPACE:-myorg}"
readonly DOCKER_TAG_PREFIX="${DOCKER_TAG_PREFIX:-v}"

# Docker wrapper functions with error handling
docker_safe() {
    local command=("$@")
    
    # Check if Docker daemon is running
    if ! docker info >/dev/null 2>&1; then
        log_error "Docker daemon is not running"
        return 1
    fi
    
    # Execute Docker command with retry logic
    local max_retries=3
    local retry_delay=2
    
    for ((attempt=1; attempt<=max_retries; attempt++)); do
        log_debug "Docker command attempt $attempt: ${command[*]}"
        
        if docker "${command[@]}"; then
            return 0
        else
            local exit_code=$?
            log_warn "Docker command failed (attempt $attempt/$max_retries): exit code $exit_code"
            
            if [[ $attempt -lt $max_retries ]]; then
                log_info "Retrying in ${retry_delay}s..."
                sleep $retry_delay
                retry_delay=$((retry_delay * 2))
            else
                log_error "Docker command failed after $max_retries attempts"
                return $exit_code
            fi
        fi
    done
}

# Build Docker image with optimization
docker_build_optimized() {
    local dockerfile_path="$1"
    local image_name="$2"
    local build_context="${3:-.}"
    local build_args="${4:-}"
    local no_cache="${5:-false}"
    
    log_info "Building Docker image: $image_name"
    
    # Build command array
    local build_cmd=(
        "build"
        "-f" "$dockerfile_path"
        "-t" "$image_name"
    )
    
    # Add build arguments
    if [[ -n "$build_args" ]]; then
        IFS=',' read -ra args <<< "$build_args"
        for arg in "${args[@]}"; do
            build_cmd+=("--build-arg" "$arg")
        done
    fi
    
    # Add cache option
    if [[ "$no_cache" == "true" ]]; then
        build_cmd+=("--no-cache")
    fi
    
    # Multi-stage build optimization
    build_cmd+=("--target" "production")
    
    # Build context
    build_cmd+=("$build_context")
    
    # Execute build
    if docker_safe "${build_cmd[@]}"; then
        log_success "Docker image built successfully: $image_name"
        
        # Display image size
        local image_size
        image_size=$(docker images --format "table {{.Size}}" "$image_name" | tail -n +2 | head -n 1)
        log_info "Image size: $image_size"
        
        return 0
    else
        log_error "Docker image build failed: $image_name"
        return 1
    fi
}

# Push image to registry
docker_push_with_retry() {
    local image_name="$1"
    local registry_url="${2:-$DOCKER_REGISTRY}"
    
    # Tag for registry
    local full_image_name="$registry_url/$DOCKER_NAMESPACE/$image_name"
    
    log_info "Pushing image to registry: $full_image_name"
    
    # Tag image
    if ! docker_safe tag "$image_name" "$full_image_name"; then
        log_error "Failed to tag image for registry"
        return 1
    fi
    
    # Push image
    if docker_safe push "$full_image_name"; then
        log_success "Image pushed successfully: $full_image_name"
        return 0
    else
        log_error "Failed to push image: $full_image_name"
        return 1
    fi
}

# Container health monitoring
monitor_container_health() {
    local container_name="$1"
    local max_wait="${2:-300}"
    local check_interval="${3:-10}"
    
    log_info "Monitoring container health: $container_name"
    
    local elapsed=0
    
    while [[ $elapsed -lt $max_wait ]]; do
        local health_status
        health_status=$(docker inspect --format='{{.State.Health.Status}}' "$container_name" 2>/dev/null)
        
        case "$health_status" in
            "healthy")
                log_success "Container is healthy: $container_name"
                return 0
                ;;
            "unhealthy")
                log_error "Container is unhealthy: $container_name"
                docker logs --tail 50 "$container_name"
                return 1
                ;;
            "starting")
                log_debug "Container is starting: $container_name"
                ;;
            *)
                # Check if container is running
                if ! docker ps --filter "name=$container_name" --filter "status=running" | grep -q "$container_name"; then
                    log_error "Container is not running: $container_name"
                    return 1
                fi
                ;;
        esac
        
        sleep "$check_interval"
        elapsed=$((elapsed + check_interval))
    done
    
    log_error "Timeout waiting for container to become healthy: $container_name"
    return 1
}

# Docker Compose integration
docker_compose_deploy() {
    local compose_file="$1"
    local environment="${2:-development}"
    local services="${3:-}"
    
    log_info "Deploying with Docker Compose: $compose_file (env: $environment)"
    
    # Set environment
    export ENVIRONMENT="$environment"
    
    # Build services first
    local compose_cmd=(
        "docker-compose"
        "-f" "$compose_file"
        "build"
    )
    
    if [[ -n "$services" ]]; then
        compose_cmd+=($services)
    fi
    
    if ! "${compose_cmd[@]}"; then
        log_error "Docker Compose build failed"
        return 1
    fi
    
    # Deploy services
    compose_cmd=(
        "docker-compose"
        "-f" "$compose_file"
        "up"
        "-d"
        "--remove-orphans"
    )
    
    if [[ -n "$services" ]]; then
        compose_cmd+=($services)
    fi
    
    if "${compose_cmd[@]}"; then
        log_success "Docker Compose deployment successful"
        
        # Wait for services to be healthy
        if [[ -z "$services" ]]; then
            services=$(docker-compose -f "$compose_file" config --services)
        fi
        
        for service in $services; do
            local container_name
            container_name=$(docker-compose -f "$compose_file" ps -q "$service")
            
            if [[ -n "$container_name" ]]; then
                monitor_container_health "$container_name" 120 5
            fi
        done
        
        return 0
    else
        log_error "Docker Compose deployment failed"
        return 1
    fi
}

# Container cleanup
cleanup_containers() {
    local max_age_hours="${1:-24}"
    local dry_run="${2:-false}"
    
    log_info "Cleaning up containers older than ${max_age_hours} hours"
    
    # Calculate cutoff time
    local cutoff_time
    cutoff_time=$(date -d "${max_age_hours} hours ago" +%s)
    
    # Get containers to cleanup
    local containers_to_remove=()
    
    while IFS= read -r container_id; do
        local created_time
        created_time=$(docker inspect --format='{{.Created}}' "$container_id")
        local created_epoch
        created_epoch=$(date -d "$created_time" +%s)
        
        if [[ $created_epoch -lt $cutoff_time ]]; then
            containers_to_remove+=("$container_id")
        fi
    done < <(docker ps -aq --filter "status=exited")
    
    if [[ ${#containers_to_remove[@]} -eq 0 ]]; then
        log_info "No containers to cleanup"
        return 0
    fi
    
    log_info "Found ${#containers_to_remove[@]} containers to cleanup"
    
    if [[ "$dry_run" == "true" ]]; then
        log_info "DRY RUN: Would remove containers:"
        for container_id in "${containers_to_remove[@]}"; do
            local container_name
            container_name=$(docker inspect --format='{{.Name}}' "$container_id" | sed 's|^/||')
            log_info "  $container_id ($container_name)"
        done
        return 0
    fi
    
    # Remove containers
    if docker_safe rm "${containers_to_remove[@]}"; then
        log_success "Removed ${#containers_to_remove[@]} containers"
        return 0
    else
        log_error "Failed to remove some containers"
        return 1
    fi
}

# Image cleanup
cleanup_images() {
    local keep_latest="${1:-true}"
    local dry_run="${2:-false}"
    
    log_info "Cleaning up unused Docker images"
    
    if [[ "$dry_run" == "true" ]]; then
        log_info "DRY RUN: Would remove images:"
        docker images --filter "dangling=true" --format "table {{.Repository}}\t{{.Tag}}\t{{.ID}}\t{{.Size}}"
        return 0
    fi
    
    # Remove dangling images
    local dangling_images
    dangling_images=$(docker images -f "dangling=true" -q)
    
    if [[ -n "$dangling_images" ]]; then
        if docker_safe rmi $dangling_images; then
            log_success "Removed dangling images"
        else
            log_warn "Some dangling images could not be removed"
        fi
    fi
    
    # Prune system
    if docker_safe system prune -f; then
        log_success "Docker system pruned successfully"
    else
        log_warn "Docker system prune had issues"
    fi
}
```

### 2. Kubernetes Integration
```bash
#!/bin/bash

# Kubernetes management framework
readonly K8S_NAMESPACE="${K8S_NAMESPACE:-default}"
readonly K8S_CONTEXT="${K8S_CONTEXT:-}"
readonly KUBECTL_TIMEOUT="${KUBECTL_TIMEOUT:-300s}"

# Kubectl wrapper with context management
kubectl_safe() {
    local command=("$@")
    
    # Check kubectl availability
    if ! command -v kubectl >/dev/null 2>&1; then
        log_error "kubectl not found in PATH"
        return 1
    fi
    
    # Build kubectl command
    local kubectl_cmd=("kubectl")
    
    # Add context if specified
    if [[ -n "$K8S_CONTEXT" ]]; then
        kubectl_cmd+=("--context" "$K8S_CONTEXT")
    fi
    
    # Add namespace
    kubectl_cmd+=("--namespace" "$K8S_NAMESPACE")
    
    # Add timeout
    kubectl_cmd+=("--timeout" "$KUBECTL_TIMEOUT")
    
    # Add original command
    kubectl_cmd+=("${command[@]}")
    
    # Execute with retry for network issues
    local max_retries=3
    for ((attempt=1; attempt<=max_retries; attempt++)); do
        log_debug "Kubectl attempt $attempt: ${kubectl_cmd[*]}"
        
        if "${kubectl_cmd[@]}"; then
            return 0
        else
            local exit_code=$?
            
            # Don't retry for certain errors
            if [[ $exit_code -eq 1 ]]; then
                # Resource not found, permission denied, etc.
                return $exit_code
            fi
            
            log_warn "Kubectl command failed (attempt $attempt/$max_retries): exit code $exit_code"
            
            if [[ $attempt -lt $max_retries ]]; then
                sleep 2
            else
                return $exit_code
            fi
        fi
    done
}

# Deploy Kubernetes manifests
k8s_deploy_manifests() {
    local manifest_dir="$1"
    local deployment_name="$2"
    local wait_for_ready="${3:-true}"
    
    log_info "Deploying Kubernetes manifests from: $manifest_dir"
    
    # Validate manifest directory
    if [[ ! -d "$manifest_dir" ]]; then
        log_error "Manifest directory not found: $manifest_dir"
        return 1
    fi
    
    # Apply manifests
    if kubectl_safe apply -f "$manifest_dir" --record; then
        log_success "Manifests applied successfully"
    else
        log_error "Failed to apply manifests"
        return 1
    fi
    
    # Wait for deployment if specified
    if [[ "$wait_for_ready" == "true" && -n "$deployment_name" ]]; then
        if kubectl_safe rollout status deployment "$deployment_name"; then
            log_success "Deployment rolled out successfully: $deployment_name"
        else
            log_error "Deployment rollout failed: $deployment_name"
            return 1
        fi
    fi
}

# Scale Kubernetes deployment
k8s_scale_deployment() {
    local deployment_name="$1"
    local replica_count="$2"
    local wait_for_ready="${3:-true}"
    
    log_info "Scaling deployment $deployment_name to $replica_count replicas"
    
    if kubectl_safe scale deployment "$deployment_name" --replicas="$replica_count"; then
        log_success "Deployment scaled successfully"
    else
        log_error "Failed to scale deployment"
        return 1
    fi
    
    if [[ "$wait_for_ready" == "true" ]]; then
        if kubectl_safe rollout status deployment "$deployment_name"; then
            log_success "Scaling completed successfully"
        else
            log_error "Scaling rollout failed"
            return 1
        fi
    fi
}

# Monitor pod health
k8s_monitor_pods() {
    local selector="$1"
    local max_wait="${2:-300}"
    local expected_count="${3:-}"
    
    log_info "Monitoring pods with selector: $selector"
    
    local elapsed=0
    local check_interval=10
    
    while [[ $elapsed -lt $max_wait ]]; do
        local pod_status
        pod_status=$(kubectl_safe get pods -l "$selector" -o jsonpath='{.items[*].status.phase}')
        
        if [[ -z "$pod_status" ]]; then
            log_debug "No pods found yet..."
            sleep $check_interval
            elapsed=$((elapsed + check_interval))
            continue
        fi
        
        # Count pods by status
        local running_count=0
        local total_count=0
        
        for status in $pod_status; do
            ((total_count++))
            if [[ "$status" == "Running" ]]; then
                ((running_count++))
            fi
        done
        
        log_debug "Pod status: $running_count/$total_count running"
        
        # Check if we have expected count and all are running
        if [[ -n "$expected_count" ]]; then
            if [[ $total_count -eq $expected_count && $running_count -eq $expected_count ]]; then
                log_success "All $expected_count pods are running"
                return 0
            fi
        else
            if [[ $total_count -gt 0 && $running_count -eq $total_count ]]; then
                log_success "All $total_count pods are running"
                return 0
            fi
        fi
        
        sleep $check_interval
        elapsed=$((elapsed + check_interval))
    done
    
    log_error "Timeout waiting for pods to be ready"
    kubectl_safe get pods -l "$selector"
    return 1
}

# Kubernetes rollback
k8s_rollback_deployment() {
    local deployment_name="$1"
    local revision="${2:-}"
    
    log_info "Rolling back deployment: $deployment_name"
    
    local rollback_cmd=("rollout" "undo" "deployment" "$deployment_name")
    
    if [[ -n "$revision" ]]; then
        rollback_cmd+=("--to-revision=$revision")
    fi
    
    if kubectl_safe "${rollback_cmd[@]}"; then
        log_success "Rollback initiated for: $deployment_name"
        
        # Wait for rollback to complete
        if kubectl_safe rollout status deployment "$deployment_name"; then
            log_success "Rollback completed successfully"
            return 0
        else
            log_error "Rollback failed"
            return 1
        fi
    else
        log_error "Failed to initiate rollback"
        return 1
    fi
}

# Get deployment status
k8s_get_deployment_status() {
    local deployment_name="$1"
    
    if ! kubectl_safe get deployment "$deployment_name" >/dev/null 2>&1; then
        echo "not_found"
        return 1
    fi
    
    local ready_replicas
    ready_replicas=$(kubectl_safe get deployment "$deployment_name" -o jsonpath='{.status.readyReplicas}')
    local desired_replicas
    desired_replicas=$(kubectl_safe get deployment "$deployment_name" -o jsonpath='{.spec.replicas}')
    
    if [[ "${ready_replicas:-0}" -eq "${desired_replicas:-0}" && "${desired_replicas:-0}" -gt 0 ]]; then
        echo "ready"
    else
        echo "not_ready"
    fi
}

# Execute command in pod
k8s_exec_in_pod() {
    local pod_selector="$1"
    local container_name="${2:-}"
    shift 2
    local command=("$@")
    
    # Get first matching pod
    local pod_name
    pod_name=$(kubectl_safe get pods -l "$pod_selector" -o jsonpath='{.items[0].metadata.name}')
    
    if [[ -z "$pod_name" ]]; then
        log_error "No pods found with selector: $pod_selector"
        return 1
    fi
    
    log_info "Executing command in pod: $pod_name"
    
    local exec_cmd=("exec" "$pod_name")
    
    if [[ -n "$container_name" ]]; then
        exec_cmd+=("-c" "$container_name")
    fi
    
    exec_cmd+=("--" "${command[@]}")
    
    kubectl_safe "${exec_cmd[@]}"
}
```

## CI/CD Pipeline Integration

### 1. Jenkins Integration
```bash
#!/bin/bash

# Jenkins API interaction
jenkins_api_call() {
    local endpoint="$1"
    local method="${2:-GET}"
    local data="${3:-}"
    local jenkins_url="${JENKINS_URL:-http://localhost:8080}"
    local jenkins_user="${JENKINS_USER:-}"
    local jenkins_token="${JENKINS_TOKEN:-}"
    
    local curl_opts=(
        --silent
        --show-error
        --fail
        --max-time 30
        --request "$method"
    )
    
    # Add authentication if provided
    if [[ -n "$jenkins_user" && -n "$jenkins_token" ]]; then
        curl_opts+=(--user "$jenkins_user:$jenkins_token")
    fi
    
    # Add data for POST/PUT requests
    if [[ -n "$data" ]]; then
        curl_opts+=(--data "$data" --header "Content-Type: application/json")
    fi
    
    # Make API call
    curl "${curl_opts[@]}" "$jenkins_url/$endpoint"
}

# Trigger Jenkins job
trigger_jenkins_job() {
    local job_name="$1"
    local parameters="${2:-}"
    local wait_for_completion="${3:-false}"
    
    log_info "Triggering Jenkins job: $job_name"
    
    local trigger_endpoint="job/$job_name/build"
    
    if [[ -n "$parameters" ]]; then
        trigger_endpoint="job/$job_name/buildWithParameters"
    fi
    
    # Trigger job
    local response
    if [[ -n "$parameters" ]]; then
        response=$(jenkins_api_call "$trigger_endpoint" "POST" "$parameters")
    else
        response=$(jenkins_api_call "$trigger_endpoint" "POST")
    fi
    
    if [[ $? -eq 0 ]]; then
        log_success "Jenkins job triggered: $job_name"
        
        if [[ "$wait_for_completion" == "true" ]]; then
            wait_for_jenkins_job "$job_name"
        fi
    else
        log_error "Failed to trigger Jenkins job: $job_name"
        return 1
    fi
}

# Wait for Jenkins job completion
wait_for_jenkins_job() {
    local job_name="$1"
    local timeout="${2:-3600}"  # 1 hour default
    local check_interval="${3:-30}"
    
    log_info "Waiting for Jenkins job completion: $job_name"
    
    # Get latest build number
    local build_number
    build_number=$(jenkins_api_call "job/$job_name/lastBuild/api/json" | jq -r '.number')
    
    if [[ -z "$build_number" || "$build_number" == "null" ]]; then
        log_error "Could not get build number for job: $job_name"
        return 1
    fi
    
    log_info "Monitoring build #$build_number"
    
    local elapsed=0
    
    while [[ $elapsed -lt $timeout ]]; do
        local build_info
        build_info=$(jenkins_api_call "job/$job_name/$build_number/api/json")
        
        if [[ $? -ne 0 ]]; then
            log_warn "Failed to get build info, retrying..."
            sleep $check_interval
            elapsed=$((elapsed + check_interval))
            continue
        fi
        
        local building
        building=$(echo "$build_info" | jq -r '.building')
        
        if [[ "$building" == "false" ]]; then
            local result
            result=$(echo "$build_info" | jq -r '.result')
            
            case "$result" in
                SUCCESS)
                    log_success "Jenkins job completed successfully: $job_name #$build_number"
                    return 0
                    ;;
                FAILURE|ABORTED|UNSTABLE)
                    log_error "Jenkins job failed: $job_name #$build_number ($result)"
                    return 1
                    ;;
                *)
                    log_warn "Jenkins job completed with unknown result: $result"
                    return 1
                    ;;
            esac
        fi
        
        log_debug "Job still running..."
        sleep $check_interval
        elapsed=$((elapsed + check_interval))
    done
    
    log_error "Timeout waiting for Jenkins job: $job_name"
    return 1
}

# Get Jenkins build logs
get_jenkins_build_logs() {
    local job_name="$1"
    local build_number="${2:-lastBuild}"
    local follow="${3:-false}"
    
    if [[ "$follow" == "true" ]]; then
        # Stream logs
        jenkins_api_call "job/$job_name/$build_number/logText/progressiveText?start=0"
    else
        # Get complete logs
        jenkins_api_call "job/$job_name/$build_number/consoleText"
    fi
}
```

### 2. GitLab CI Integration
```bash
#!/bin/bash

# GitLab API interaction
gitlab_api_call() {
    local endpoint="$1"
    local method="${2:-GET}"
    local data="${3:-}"
    local gitlab_url="${GITLAB_URL:-https://gitlab.com}"
    local gitlab_token="${GITLAB_TOKEN:-}"
    
    if [[ -z "$gitlab_token" ]]; then
        log_error "GitLab token not provided"
        return 1
    fi
    
    local curl_opts=(
        --silent
        --show-error
        --fail
        --max-time 30
        --request "$method"
        --header "PRIVATE-TOKEN: $gitlab_token"
    )
    
    if [[ -n "$data" ]]; then
        curl_opts+=(--data "$data" --header "Content-Type: application/json")
    fi
    
    curl "${curl_opts[@]}" "$gitlab_url/api/v4/$endpoint"
}

# Trigger GitLab pipeline
trigger_gitlab_pipeline() {
    local project_id="$1"
    local ref="${2:-main}"
    local variables="${3:-}"
    
    log_info "Triggering GitLab pipeline for project $project_id (ref: $ref)"
    
    local pipeline_data="{\"ref\":\"$ref\""
    
    if [[ -n "$variables" ]]; then
        pipeline_data="$pipeline_data,\"variables\":$variables"
    fi
    
    pipeline_data="$pipeline_data}"
    
    local response
    response=$(gitlab_api_call "projects/$project_id/pipeline" "POST" "$pipeline_data")
    
    if [[ $? -eq 0 ]]; then
        local pipeline_id
        pipeline_id=$(echo "$response" | jq -r '.id')
        log_success "GitLab pipeline triggered: #$pipeline_id"
        echo "$pipeline_id"
    else
        log_error "Failed to trigger GitLab pipeline"
        return 1
    fi
}

# Monitor GitLab pipeline
monitor_gitlab_pipeline() {
    local project_id="$1"
    local pipeline_id="$2"
    local timeout="${3:-3600}"
    
    log_info "Monitoring GitLab pipeline: $project_id/#$pipeline_id"
    
    local elapsed=0
    local check_interval=30
    
    while [[ $elapsed -lt $timeout ]]; do
        local pipeline_info
        pipeline_info=$(gitlab_api_call "projects/$project_id/pipelines/$pipeline_id")
        
        if [[ $? -ne 0 ]]; then
            log_warn "Failed to get pipeline info, retrying..."
            sleep $check_interval
            elapsed=$((elapsed + check_interval))
            continue
        fi
        
        local status
        status=$(echo "$pipeline_info" | jq -r '.status')
        
        case "$status" in
            success)
                log_success "GitLab pipeline completed successfully"
                return 0
                ;;
            failed|canceled)
                log_error "GitLab pipeline failed: $status"
                return 1
                ;;
            running|pending|created)
                log_debug "Pipeline status: $status"
                ;;
            *)
                log_warn "Unknown pipeline status: $status"
                ;;
        esac
        
        sleep $check_interval
        elapsed=$((elapsed + check_interval))
    done
    
    log_error "Timeout waiting for GitLab pipeline"
    return 1
}

# Get GitLab job logs
get_gitlab_job_logs() {
    local project_id="$1"
    local job_id="$2"
    
    gitlab_api_call "projects/$project_id/jobs/$job_id/trace"
}
```

## Cloud Provider Integration

### 1. AWS CLI Integration
```bash
#!/bin/bash

# AWS CLI wrapper with error handling
aws_safe() {
    local command=("$@")
    
    # Check AWS CLI availability
    if ! command -v aws >/dev/null 2>&1; then
        log_error "AWS CLI not found"
        return 1
    fi
    
    # Check credentials
    if ! aws sts get-caller-identity >/dev/null 2>&1; then
        log_error "AWS credentials not configured"
        return 1
    fi
    
    # Execute AWS command with retry logic
    local max_retries=3
    for ((attempt=1; attempt<=max_retries; attempt++)); do
        log_debug "AWS command attempt $attempt: ${command[*]}"
        
        if aws "${command[@]}"; then
            return 0
        else
            local exit_code=$?
            log_warn "AWS command failed (attempt $attempt/$max_retries): exit code $exit_code"
            
            # Don't retry for authentication/permission errors
            if [[ $exit_code -eq 255 || $exit_code -eq 254 ]]; then
                return $exit_code
            fi
            
            if [[ $attempt -lt $max_retries ]]; then
                sleep $((attempt * 2))
            else
                return $exit_code
            fi
        fi
    done
}

# Deploy to ECS
deploy_to_ecs() {
    local cluster_name="$1"
    local service_name="$2"
    local task_definition="$3"
    local desired_count="${4:-2}"
    
    log_info "Deploying to ECS: $service_name on $cluster_name"
    
    # Register new task definition
    local task_def_arn
    task_def_arn=$(aws_safe ecs register-task-definition --cli-input-json "file://$task_definition" --query 'taskDefinition.taskDefinitionArn' --output text)
    
    if [[ -z "$task_def_arn" ]]; then
        log_error "Failed to register task definition"
        return 1
    fi
    
    log_info "Registered task definition: $task_def_arn"
    
    # Update service
    if aws_safe ecs update-service \
        --cluster "$cluster_name" \
        --service "$service_name" \
        --task-definition "$task_def_arn" \
        --desired-count "$desired_count"; then
        
        log_success "Service update initiated"
        
        # Wait for deployment to complete
        if aws_safe ecs wait services-stable \
            --cluster "$cluster_name" \
            --services "$service_name"; then
            log_success "ECS deployment completed successfully"
            return 0
        else
            log_error "ECS deployment failed or timed out"
            return 1
        fi
    else
        log_error "Failed to update ECS service"
        return 1
    fi
}

# Update Lambda function
update_lambda_function() {
    local function_name="$1"
    local zip_file="$2"
    local environment_vars="${3:-}"
    
    log_info "Updating Lambda function: $function_name"
    
    # Update function code
    if aws_safe lambda update-function-code \
        --function-name "$function_name" \
        --zip-file "fileb://$zip_file"; then
        log_success "Lambda function code updated"
    else
        log_error "Failed to update Lambda function code"
        return 1
    fi
    
    # Update environment variables if provided
    if [[ -n "$environment_vars" ]]; then
        if aws_safe lambda update-function-configuration \
            --function-name "$function_name" \
            --environment "$environment_vars"; then
            log_success "Lambda function configuration updated"
        else
            log_error "Failed to update Lambda function configuration"
            return 1
        fi
    fi
    
    # Wait for function to be updated
    if aws_safe lambda wait function-updated \
        --function-name "$function_name"; then
        log_success "Lambda function update completed"
        return 0
    else
        log_error "Lambda function update failed"
        return 1
    fi
}

# S3 deployment with sync
deploy_to_s3() {
    local local_path="$1"
    local s3_bucket="$2"
    local s3_prefix="${3:-}"
    local cache_control="${4:-max-age=86400}"
    
    log_info "Deploying to S3: $local_path -> s3://$s3_bucket/$s3_prefix"
    
    local sync_opts=(
        --delete
        --cache-control "$cache_control"
    )
    
    # Add content encoding for specific files
    if aws_safe s3 sync "$local_path" "s3://$s3_bucket/$s3_prefix" "${sync_opts[@]}"; then
        log_success "S3 deployment completed"
        
        # Invalidate CloudFront if distribution ID provided
        if [[ -n "${CLOUDFRONT_DISTRIBUTION_ID:-}" ]]; then
            log_info "Invalidating CloudFront distribution"
            aws_safe cloudfront create-invalidation \
                --distribution-id "$CLOUDFRONT_DISTRIBUTION_ID" \
                --paths "/*"
        fi
        
        return 0
    else
        log_error "S3 deployment failed"
        return 1
    fi
}
```

## Infrastructure as Code Integration

### 1. Terraform Integration
```bash
#!/bin/bash

# Terraform wrapper with state management
terraform_safe() {
    local command=("$@")
    local tf_dir="${TF_DIR:-.}"
    
    # Check Terraform availability
    if ! command -v terraform >/dev/null 2>&1; then
        log_error "Terraform not found"
        return 1
    fi
    
    # Change to Terraform directory
    pushd "$tf_dir" >/dev/null || {
        log_error "Cannot access Terraform directory: $tf_dir"
        return 1
    }
    
    # Initialize if needed
    if [[ ! -d ".terraform" ]]; then
        log_info "Initializing Terraform..."
        terraform init
    fi
    
    # Execute Terraform command
    log_debug "Terraform command: ${command[*]}"
    terraform "${command[@]}"
    local exit_code=$?
    
    popd >/dev/null
    return $exit_code
}

# Plan Terraform changes
terraform_plan() {
    local var_file="${1:-}"
    local out_file="${2:-tfplan}"
    local target="${3:-}"
    
    log_info "Planning Terraform changes"
    
    local plan_opts=(-out="$out_file")
    
    if [[ -n "$var_file" ]]; then
        plan_opts+=(-var-file="$var_file")
    fi
    
    if [[ -n "$target" ]]; then
        plan_opts+=(-target="$target")
    fi
    
    if terraform_safe plan "${plan_opts[@]}"; then
        log_success "Terraform plan completed"
        
        # Show plan summary
        terraform_safe show -no-color "$out_file" | grep -E "^(Plan:|No changes.)"
        return 0
    else
        log_error "Terraform plan failed"
        return 1
    fi
}

# Apply Terraform changes
terraform_apply() {
    local plan_file="${1:-tfplan}"
    local auto_approve="${2:-false}"
    
    log_info "Applying Terraform changes"
    
    local apply_opts=()
    
    if [[ "$auto_approve" == "true" ]]; then
        apply_opts+=(-auto-approve)
    fi
    
    if [[ -f "$plan_file" ]]; then
        apply_opts+=("$plan_file")
    fi
    
    if terraform_safe apply "${apply_opts[@]}"; then
        log_success "Terraform apply completed"
        return 0
    else
        log_error "Terraform apply failed"
        return 1
    fi
}

# Destroy Terraform resources
terraform_destroy() {
    local var_file="${1:-}"
    local auto_approve="${2:-false}"
    local target="${3:-}"
    
    log_warn "Destroying Terraform resources"
    
    local destroy_opts=()
    
    if [[ "$auto_approve" == "true" ]]; then
        destroy_opts+=(-auto-approve)
    fi
    
    if [[ -n "$var_file" ]]; then
        destroy_opts+=(-var-file="$var_file")
    fi
    
    if [[ -n "$target" ]]; then
        destroy_opts+=(-target="$target")
    fi
    
    if terraform_safe destroy "${destroy_opts[@]}"; then
        log_success "Terraform destroy completed"
        return 0
    else
        log_error "Terraform destroy failed"
        return 1
    fi
}
```

### 2. Ansible Integration
```bash
#!/bin/bash

# Ansible playbook execution
ansible_playbook_run() {
    local playbook="$1"
    local inventory="${2:-hosts}"
    local extra_vars="${3:-}"
    local limit="${4:-}"
    local tags="${5:-}"
    
    log_info "Running Ansible playbook: $playbook"
    
    # Check Ansible availability
    if ! command -v ansible-playbook >/dev/null 2>&1; then
        log_error "ansible-playbook not found"
        return 1
    fi
    
    local ansible_opts=(
        -i "$inventory"
        -v
    )
    
    if [[ -n "$extra_vars" ]]; then
        ansible_opts+=(--extra-vars "$extra_vars")
    fi
    
    if [[ -n "$limit" ]]; then
        ansible_opts+=(--limit "$limit")
    fi
    
    if [[ -n "$tags" ]]; then
        ansible_opts+=(--tags "$tags")
    fi
    
    # Execute playbook
    if ansible-playbook "${ansible_opts[@]}" "$playbook"; then
        log_success "Ansible playbook completed successfully"
        return 0
    else
        log_error "Ansible playbook failed"
        return 1
    fi
}

# Test Ansible connectivity
ansible_ping() {
    local inventory="${1:-hosts}"
    local limit="${2:-all}"
    
    log_info "Testing Ansible connectivity"
    
    if ansible "$limit" -i "$inventory" -m ping; then
        log_success "Ansible connectivity test passed"
        return 0
    else
        log_error "Ansible connectivity test failed"
        return 1
    fi
}
```

This comprehensive DevOps tools integration framework provides seamless automation capabilities for containerization, orchestration, CI/CD pipelines, cloud services, and infrastructure management using Bash scripts.