# Bash Advanced Patterns

## Overview
Bash advanced patterns cover sophisticated scripting techniques, design patterns, architectural approaches, and expert-level programming constructs for building complex, maintainable, and scalable shell script applications in DevOps environments.

## Design Patterns in Bash

### 1. Factory Pattern Implementation
```bash
#!/bin/bash

# Factory pattern for creating different types of deployment handlers
declare -A DEPLOYMENT_FACTORIES=()

# Register deployment factory
register_deployment_factory() {
    local deployment_type="$1"
    local factory_function="$2"
    
    DEPLOYMENT_FACTORIES["$deployment_type"]="$factory_function"
    log_debug "Registered deployment factory: $deployment_type"
}

# Create deployment handler using factory pattern
create_deployment_handler() {
    local deployment_type="$1"
    shift
    local config=("$@")
    
    local factory_function="${DEPLOYMENT_FACTORIES[$deployment_type]:-}"
    
    if [[ -z "$factory_function" ]]; then
        log_error "No factory registered for deployment type: $deployment_type"
        return 1
    fi
    
    # Call factory function to create handler
    "$factory_function" "${config[@]}"
}

# Kubernetes deployment factory
create_kubernetes_deployment() {
    local namespace="$1"
    local deployment_name="$2"
    local image="$3"
    
    # Create deployment handler object (associative array)
    declare -A handler=(
        [type]="kubernetes"
        [namespace]="$namespace"
        [deployment_name]="$deployment_name"
        [image]="$image"
    )
    
    # Create handler functions
    eval "
    deploy_${deployment_name}() {
        kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: $deployment_name
  namespace: $namespace
spec:
  replicas: \${1:-1}
  selector:
    matchLabels:
      app: $deployment_name
  template:
    metadata:
      labels:
        app: $deployment_name
    spec:
      containers:
      - name: $deployment_name
        image: $image
        ports:
        - containerPort: 8080
EOF
    }
    
    rollback_${deployment_name}() {
        kubectl rollout undo deployment/$deployment_name -n $namespace
    }
    
    status_${deployment_name}() {
        kubectl rollout status deployment/$deployment_name -n $namespace
    }
    "
    
    log_info "Created Kubernetes deployment handler: $deployment_name"
}

# Docker deployment factory
create_docker_deployment() {
    local container_name="$1"
    local image="$2"
    local port_mapping="${3:-8080:8080}"
    
    eval "
    deploy_${container_name}() {
        docker run -d \\
            --name $container_name \\
            -p $port_mapping \\
            --restart unless-stopped \\
            $image
    }
    
    rollback_${container_name}() {
        local previous_image=\$(docker inspect $container_name --format '{{.Config.Image}}')
        docker stop $container_name
        docker rm $container_name
        deploy_${container_name}
    }
    
    status_${container_name}() {
        docker ps --filter name=$container_name --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
    }
    "
    
    log_info "Created Docker deployment handler: $container_name"
}

# Register factories
register_deployment_factory "kubernetes" "create_kubernetes_deployment"
register_deployment_factory "docker" "create_docker_deployment"

# Usage example
# create_deployment_handler "kubernetes" "default" "web-app" "nginx:latest"
# deploy_web-app 3
```

### 2. Strategy Pattern Implementation
```bash
#!/bin/bash

# Strategy pattern for different backup strategies
declare -A BACKUP_STRATEGIES=()

# Register backup strategy
register_backup_strategy() {
    local strategy_name="$1"
    local strategy_function="$2"
    
    BACKUP_STRATEGIES["$strategy_name"]="$strategy_function"
    log_debug "Registered backup strategy: $strategy_name"
}

# Execute backup using specified strategy
execute_backup() {
    local strategy_name="$1"
    local source_path="$2"
    local destination="$3"
    shift 3
    local options=("$@")
    
    local strategy_function="${BACKUP_STRATEGIES[$strategy_name]:-}"
    
    if [[ -z "$strategy_function" ]]; then
        log_error "Unknown backup strategy: $strategy_name"
        return 1
    fi
    
    log_info "Executing backup strategy: $strategy_name"
    "$strategy_function" "$source_path" "$destination" "${options[@]}"
}

# Full backup strategy
full_backup_strategy() {
    local source_path="$1"
    local destination="$2"
    shift 2
    local options=("$@")
    
    log_info "Performing full backup: $source_path -> $destination"
    
    local backup_name="full_backup_$(date +%Y%m%d_%H%M%S)"
    local backup_file="$destination/$backup_name.tar.gz"
    
    # Create compressed archive
    if tar -czf "$backup_file" -C "$(dirname "$source_path")" "$(basename "$source_path")"; then
        log_success "Full backup completed: $backup_file"
        
        # Calculate checksum
        local checksum
        checksum=$(sha256sum "$backup_file" | cut -d' ' -f1)
        echo "$checksum" > "$backup_file.sha256"
        
        log_info "Backup checksum: $checksum"
        return 0
    else
        log_error "Full backup failed"
        return 1
    fi
}

# Incremental backup strategy
incremental_backup_strategy() {
    local source_path="$1"
    local destination="$2"
    shift 2
    local options=("$@")
    
    log_info "Performing incremental backup: $source_path -> $destination"
    
    local backup_name="incremental_backup_$(date +%Y%m%d_%H%M%S)"
    local backup_file="$destination/$backup_name.tar.gz"
    local snapshot_file="$destination/.backup_snapshot"
    
    # Find files newer than last backup
    local find_opts=()
    if [[ -f "$snapshot_file" ]]; then
        find_opts=("-newer" "$snapshot_file")
        log_debug "Using snapshot file: $snapshot_file"
    else
        log_info "No previous snapshot found, performing full backup"
    fi
    
    # Create file list
    local file_list
    file_list=$(mktemp)
    
    if find "$source_path" "${find_opts[@]}" -type f > "$file_list"; then
        local file_count
        file_count=$(wc -l < "$file_list")
        
        if [[ $file_count -gt 0 ]]; then
            if tar -czf "$backup_file" -T "$file_list"; then
                log_success "Incremental backup completed: $backup_file ($file_count files)"
                
                # Update snapshot
                touch "$snapshot_file"
                
                # Calculate checksum
                local checksum
                checksum=$(sha256sum "$backup_file" | cut -d' ' -f1)
                echo "$checksum" > "$backup_file.sha256"
                
                rm -f "$file_list"
                return 0
            else
                log_error "Incremental backup failed"
                rm -f "$file_list"
                return 1
            fi
        else
            log_info "No new files to backup"
            rm -f "$file_list"
            return 0
        fi
    else
        log_error "Failed to find files for incremental backup"
        rm -f "$file_list"
        return 1
    fi
}

# Differential backup strategy
differential_backup_strategy() {
    local source_path="$1"
    local destination="$2"
    shift 2
    local options=("$@")
    
    log_info "Performing differential backup: $source_path -> $destination"
    
    local backup_name="differential_backup_$(date +%Y%m%d_%H%M%S)"
    local backup_file="$destination/$backup_name.tar.gz"
    local base_snapshot="$destination/.base_backup_snapshot"
    
    if [[ ! -f "$base_snapshot" ]]; then
        log_warn "No base backup snapshot found, creating one"
        touch "$base_snapshot"
    fi
    
    # Find files changed since base backup
    local file_list
    file_list=$(mktemp)
    
    if find "$source_path" -newer "$base_snapshot" -type f > "$file_list"; then
        local file_count
        file_count=$(wc -l < "$file_list")
        
        if [[ $file_count -gt 0 ]]; then
            if tar -czf "$backup_file" -T "$file_list"; then
                log_success "Differential backup completed: $backup_file ($file_count files)"
                
                # Calculate checksum
                local checksum
                checksum=$(sha256sum "$backup_file" | cut -d' ' -f1)
                echo "$checksum" > "$backup_file.sha256"
                
                rm -f "$file_list"
                return 0
            else
                log_error "Differential backup failed"
                rm -f "$file_list"
                return 1
            fi
        else
            log_info "No changed files to backup"
            rm -f "$file_list"
            return 0
        fi
    else
        log_error "Failed to find files for differential backup"
        rm -f "$file_list"
        return 1
    fi
}

# Register strategies
register_backup_strategy "full" "full_backup_strategy"
register_backup_strategy "incremental" "incremental_backup_strategy"
register_backup_strategy "differential" "differential_backup_strategy"

# Backup context manager
backup_context() {
    local strategy="$1"
    local source="$2"
    local destination="$3"
    shift 3
    local options=("$@")
    
    # Pre-backup hooks
    if command -v pre_backup_hook >/dev/null 2>&1; then
        log_info "Executing pre-backup hook"
        pre_backup_hook "$source" "$destination"
    fi
    
    # Execute backup
    local backup_result=0
    if execute_backup "$strategy" "$source" "$destination" "${options[@]}"; then
        log_success "Backup completed successfully"
    else
        log_error "Backup failed"
        backup_result=1
    fi
    
    # Post-backup hooks
    if command -v post_backup_hook >/dev/null 2>&1; then
        log_info "Executing post-backup hook"
        post_backup_hook "$source" "$destination" "$backup_result"
    fi
    
    return $backup_result
}
```

### 3. Observer Pattern Implementation
```bash
#!/bin/bash

# Observer pattern for event-driven architecture
declare -A EVENT_OBSERVERS=()
declare -A EVENT_HISTORY=()

# Register event observer
register_observer() {
    local event_type="$1"
    local observer_function="$2"
    local observer_id="${3:-$(date +%s%N)}"
    
    # Store observer
    local observers="${EVENT_OBSERVERS[$event_type]:-}"
    EVENT_OBSERVERS["$event_type"]="$observers$observer_id:$observer_function;"
    
    log_debug "Registered observer for event '$event_type': $observer_function"
    echo "$observer_id"
}

# Unregister event observer
unregister_observer() {
    local event_type="$1"
    local observer_id="$2"
    
    local observers="${EVENT_OBSERVERS[$event_type]:-}"
    local new_observers=""
    
    # Remove observer from list
    IFS=';' read -ra observer_list <<< "$observers"
    for observer in "${observer_list[@]}"; do
        if [[ -n "$observer" && "$observer" != "$observer_id:"* ]]; then
            new_observers="$new_observers$observer;"
        fi
    done
    
    EVENT_OBSERVERS["$event_type"]="$new_observers"
    log_debug "Unregistered observer for event '$event_type': $observer_id"
}

# Emit event to all observers
emit_event() {
    local event_type="$1"
    local event_data="$2"
    local event_timestamp="${3:-$(date +%s)}"
    
    log_debug "Emitting event: $event_type"
    
    # Store event in history
    local event_id="${event_type}_${event_timestamp}_$$"
    EVENT_HISTORY["$event_id"]="$event_timestamp|$event_type|$event_data"
    
    # Get observers for this event type
    local observers="${EVENT_OBSERVERS[$event_type]:-}"
    
    if [[ -z "$observers" ]]; then
        log_debug "No observers registered for event: $event_type"
        return 0
    fi
    
    local notification_count=0
    
    # Notify all observers
    IFS=';' read -ra observer_list <<< "$observers"
    for observer in "${observer_list[@]}"; do
        if [[ -n "$observer" ]]; then
            IFS=':' read -r observer_id observer_function <<< "$observer"
            
            log_debug "Notifying observer: $observer_function"
            
            # Call observer function with event data
            if "$observer_function" "$event_type" "$event_data" "$event_timestamp"; then
                ((notification_count++))
            else
                log_warn "Observer failed to process event: $observer_function"
            fi
        fi
    done
    
    log_debug "Notified $notification_count observers for event: $event_type"
}

# Event observers for deployment pipeline
deployment_started_observer() {
    local event_type="$1"
    local event_data="$2"
    local timestamp="$3"
    
    log_info "🚀 Deployment started: $event_data"
    
    # Send notification
    send_slack_notification "Deployment started for: $event_data"
    
    # Update deployment dashboard
    update_deployment_dashboard "started" "$event_data"
    
    return 0
}

deployment_completed_observer() {
    local event_type="$1"
    local event_data="$2"
    local timestamp="$3"
    
    log_success "✅ Deployment completed: $event_data"
    
    # Send notification
    send_slack_notification "✅ Deployment completed successfully: $event_data"
    
    # Update deployment dashboard
    update_deployment_dashboard "completed" "$event_data"
    
    # Trigger post-deployment tests
    emit_event "post_deployment_tests" "$event_data"
    
    return 0
}

deployment_failed_observer() {
    local event_type="$1"
    local event_data="$2"
    local timestamp="$3"
    
    log_error "❌ Deployment failed: $event_data"
    
    # Send notification
    send_slack_notification "❌ Deployment failed: $event_data"
    
    # Update deployment dashboard
    update_deployment_dashboard "failed" "$event_data"
    
    # Trigger rollback
    emit_event "deployment_rollback" "$event_data"
    
    return 0
}

# Helper functions for observers
send_slack_notification() {
    local message="$1"
    
    if [[ -n "${SLACK_WEBHOOK_URL:-}" ]]; then
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"text\":\"$message\"}" \
            "$SLACK_WEBHOOK_URL" >/dev/null 2>&1 || true
    fi
}

update_deployment_dashboard() {
    local status="$1"
    local deployment_info="$2"
    
    # Update dashboard (placeholder implementation)
    local dashboard_file="/tmp/deployment_dashboard.json"
    
    local entry="{\"timestamp\":\"$(date -Iseconds)\",\"status\":\"$status\",\"deployment\":\"$deployment_info\"}"
    
    if [[ -f "$dashboard_file" ]]; then
        # Add to existing dashboard
        jq ". += [$entry]" "$dashboard_file" > "${dashboard_file}.tmp" && mv "${dashboard_file}.tmp" "$dashboard_file"
    else
        # Create new dashboard
        echo "[$entry]" > "$dashboard_file"
    fi
}

# Register deployment observers
register_observer "deployment_started" "deployment_started_observer"
register_observer "deployment_completed" "deployment_completed_observer"
register_observer "deployment_failed" "deployment_failed_observer"

# Usage example
# emit_event "deployment_started" "web-app:v1.2.3"
```

## Advanced Control Structures

### 1. State Machine Implementation
```bash
#!/bin/bash

# State machine for deployment workflow
declare -A STATE_MACHINE=()
declare -A STATE_TRANSITIONS=()
declare -A STATE_ACTIONS=()

# Initialize state machine
init_state_machine() {
    local machine_name="$1"
    local initial_state="$2"
    
    STATE_MACHINE["$machine_name"]="$initial_state"
    log_debug "Initialized state machine '$machine_name' with state: $initial_state"
}

# Define state transition
define_transition() {
    local machine_name="$1"
    local from_state="$2"
    local event="$3"
    local to_state="$4"
    local action_function="${5:-}"
    
    local transition_key="${machine_name}:${from_state}:${event}"
    STATE_TRANSITIONS["$transition_key"]="$to_state"
    
    if [[ -n "$action_function" ]]; then
        STATE_ACTIONS["$transition_key"]="$action_function"
    fi
    
    log_debug "Defined transition: $from_state --($event)--> $to_state"
}

# Process event in state machine
process_event() {
    local machine_name="$1"
    local event="$2"
    shift 2
    local event_data=("$@")
    
    local current_state="${STATE_MACHINE[$machine_name]:-}"
    
    if [[ -z "$current_state" ]]; then
        log_error "State machine not found: $machine_name"
        return 1
    fi
    
    local transition_key="${machine_name}:${current_state}:${event}"
    local next_state="${STATE_TRANSITIONS[$transition_key]:-}"
    
    if [[ -z "$next_state" ]]; then
        log_warn "No transition defined for: $current_state --($event)"
        return 1
    fi
    
    log_info "State transition: $current_state --($event)--> $next_state"
    
    # Execute transition action if defined
    local action_function="${STATE_ACTIONS[$transition_key]:-}"
    if [[ -n "$action_function" ]]; then
        log_debug "Executing transition action: $action_function"
        
        if "$action_function" "$machine_name" "$current_state" "$next_state" "$event" "${event_data[@]}"; then
            # Update state only if action succeeded
            STATE_MACHINE["$machine_name"]="$next_state"
            log_success "State machine '$machine_name' transitioned to: $next_state"
            return 0
        else
            log_error "Transition action failed, state unchanged: $current_state"
            return 1
        fi
    else
        # No action, just change state
        STATE_MACHINE["$machine_name"]="$next_state"
        log_success "State machine '$machine_name' transitioned to: $next_state"
        return 0
    fi
}

# Get current state
get_current_state() {
    local machine_name="$1"
    echo "${STATE_MACHINE[$machine_name]:-}"
}

# Deployment state machine example
setup_deployment_state_machine() {
    local deployment_name="$1"
    
    # Initialize with 'idle' state
    init_state_machine "$deployment_name" "idle"
    
    # Define transitions
    define_transition "$deployment_name" "idle" "start_deployment" "building" "action_start_build"
    define_transition "$deployment_name" "building" "build_success" "testing" "action_start_tests"
    define_transition "$deployment_name" "building" "build_failed" "failed" "action_build_failed"
    define_transition "$deployment_name" "testing" "tests_passed" "deploying" "action_start_deployment"
    define_transition "$deployment_name" "testing" "tests_failed" "failed" "action_tests_failed"
    define_transition "$deployment_name" "deploying" "deployment_success" "completed" "action_deployment_success"
    define_transition "$deployment_name" "deploying" "deployment_failed" "failed" "action_deployment_failed"
    define_transition "$deployment_name" "failed" "retry" "building" "action_retry_deployment"
    define_transition "$deployment_name" "completed" "rollback" "rolling_back" "action_start_rollback"
    define_transition "$deployment_name" "rolling_back" "rollback_success" "idle" "action_rollback_success"
}

# State machine action functions
action_start_build() {
    local machine_name="$1"
    local from_state="$2"
    local to_state="$3"
    local event="$4"
    shift 4
    local event_data=("$@")
    
    log_info "Starting build for: $machine_name"
    
    # Emit event for observers
    emit_event "build_started" "$machine_name"
    
    # Simulate build process (replace with actual build logic)
    if build_application "${event_data[@]}"; then
        # Trigger next event
        process_event "$machine_name" "build_success" "${event_data[@]}"
    else
        process_event "$machine_name" "build_failed" "${event_data[@]}"
    fi
    
    return 0
}

action_start_tests() {
    local machine_name="$1"
    local from_state="$2"
    local to_state="$3"
    local event="$4"
    shift 4
    local event_data=("$@")
    
    log_info "Starting tests for: $machine_name"
    
    # Emit event for observers
    emit_event "tests_started" "$machine_name"
    
    # Simulate test process
    if run_tests "${event_data[@]}"; then
        process_event "$machine_name" "tests_passed" "${event_data[@]}"
    else
        process_event "$machine_name" "tests_failed" "${event_data[@]}"
    fi
    
    return 0
}

action_start_deployment() {
    local machine_name="$1"
    local from_state="$2"
    local to_state="$3"
    local event="$4"
    shift 4
    local event_data=("$@")
    
    log_info "Starting deployment for: $machine_name"
    
    # Emit event for observers
    emit_event "deployment_started" "$machine_name"
    
    # Simulate deployment process
    if deploy_application "${event_data[@]}"; then
        process_event "$machine_name" "deployment_success" "${event_data[@]}"
    else
        process_event "$machine_name" "deployment_failed" "${event_data[@]}"
    fi
    
    return 0
}

action_deployment_success() {
    local machine_name="$1"
    local from_state="$2"
    local to_state="$3"
    local event="$4"
    shift 4
    local event_data=("$@")
    
    log_success "Deployment completed successfully: $machine_name"
    
    # Emit event for observers
    emit_event "deployment_completed" "$machine_name"
    
    return 0
}

action_deployment_failed() {
    local machine_name="$1"
    local from_state="$2"
    local to_state="$3"
    local event="$4"
    shift 4
    local event_data=("$@")
    
    log_error "Deployment failed: $machine_name"
    
    # Emit event for observers
    emit_event "deployment_failed" "$machine_name"
    
    return 0
}

# Placeholder functions for actual implementation
build_application() {
    # Replace with actual build logic
    log_info "Building application..."
    sleep 2
    return 0  # Simulate success
}

run_tests() {
    # Replace with actual test logic
    log_info "Running tests..."
    sleep 1
    return 0  # Simulate success
}

deploy_application() {
    # Replace with actual deployment logic
    log_info "Deploying application..."
    sleep 3
    return 0  # Simulate success
}

# Usage example
# setup_deployment_state_machine "web-app"
# process_event "web-app" "start_deployment" "web-app:v1.2.3"
```

### 2. Pipeline Pattern Implementation
```bash
#!/bin/bash

# Pipeline pattern for data processing
declare -a PIPELINE_STAGES=()
declare -a PIPELINE_FILTERS=()

# Define pipeline stage
add_pipeline_stage() {
    local stage_name="$1"
    local stage_function="$2"
    local stage_config="${3:-}"
    
    PIPELINE_STAGES+=("$stage_name:$stage_function:$stage_config")
    log_debug "Added pipeline stage: $stage_name"
}

# Add pipeline filter
add_pipeline_filter() {
    local filter_function="$1"
    local filter_config="${2:-}"
    
    PIPELINE_FILTERS+=("$filter_function:$filter_config")
    log_debug "Added pipeline filter: $filter_function"
}

# Execute pipeline
execute_pipeline() {
    local input_data="$1"
    local pipeline_name="${2:-default}"
    
    log_info "Executing pipeline: $pipeline_name"
    
    local current_data="$input_data"
    local stage_count=0
    
    # Apply filters first
    for filter_spec in "${PIPELINE_FILTERS[@]}"; do
        IFS=':' read -r filter_function filter_config <<< "$filter_spec"
        
        log_debug "Applying filter: $filter_function"
        
        if current_data=$(apply_filter "$filter_function" "$current_data" "$filter_config"); then
            log_debug "Filter applied successfully: $filter_function"
        else
            log_error "Filter failed: $filter_function"
            return 1
        fi
    done
    
    # Execute pipeline stages
    for stage_spec in "${PIPELINE_STAGES[@]}"; do
        IFS=':' read -r stage_name stage_function stage_config <<< "$stage_spec"
        ((stage_count++))
        
        log_info "Executing stage $stage_count: $stage_name"
        
        local stage_start_time=$(date +%s.%N)
        
        if current_data=$(execute_stage "$stage_function" "$current_data" "$stage_config"); then
            local stage_end_time=$(date +%s.%N)
            local stage_duration=$(echo "$stage_end_time - $stage_start_time" | bc -l)
            
            log_success "Stage completed: $stage_name (${stage_duration}s)"
        else
            log_error "Stage failed: $stage_name"
            return 1
        fi
    done
    
    log_success "Pipeline completed: $pipeline_name ($stage_count stages)"
    echo "$current_data"
}

# Apply pipeline filter
apply_filter() {
    local filter_function="$1"
    local input_data="$2"
    local filter_config="$3"
    
    # Call filter function
    "$filter_function" "$input_data" "$filter_config"
}

# Execute pipeline stage
execute_stage() {
    local stage_function="$1"
    local input_data="$2"
    local stage_config="$3"
    
    # Call stage function
    "$stage_function" "$input_data" "$stage_config"
}

# Example pipeline filters
filter_validate_json() {
    local input_data="$1"
    local config="$2"
    
    if echo "$input_data" | jq . >/dev/null 2>&1; then
        echo "$input_data"
    else
        log_error "Invalid JSON data"
        return 1
    fi
}

filter_size_limit() {
    local input_data="$1"
    local max_size="${2:-1048576}"  # 1MB default
    
    local data_size=${#input_data}
    
    if [[ $data_size -le $max_size ]]; then
        echo "$input_data"
    else
        log_error "Data size ($data_size) exceeds limit ($max_size)"
        return 1
    fi
}

# Example pipeline stages
stage_extract_data() {
    local input_data="$1"
    local config="$2"
    
    log_debug "Extracting data from input"
    
    # Extract specific fields from JSON
    if [[ "$config" =~ json ]]; then
        echo "$input_data" | jq '.data'
    else
        echo "$input_data"
    fi
}

stage_transform_data() {
    local input_data="$1"
    local config="$2"
    
    log_debug "Transforming data"
    
    # Transform data based on configuration
    case "$config" in
        "uppercase")
            echo "$input_data" | tr '[:lower:]' '[:upper:]'
            ;;
        "lowercase")
            echo "$input_data" | tr '[:upper:]' '[:lower:]'
            ;;
        "trim")
            echo "$input_data" | xargs
            ;;
        *)
            echo "$input_data"
            ;;
    esac
}

stage_load_data() {
    local input_data="$1"
    local config="$2"
    
    log_debug "Loading data to destination: $config"
    
    # Load data to specified destination
    case "$config" in
        "file:"*)
            local file_path="${config#file:}"
            echo "$input_data" > "$file_path"
            echo "Data loaded to file: $file_path"
            ;;
        "database:"*)
            local db_config="${config#database:}"
            log_info "Loading data to database: $db_config"
            echo "Data loaded to database"
            ;;
        *)
            echo "$input_data"
            ;;
    esac
}

# Clear pipeline
clear_pipeline() {
    PIPELINE_STAGES=()
    PIPELINE_FILTERS=()
    log_debug "Pipeline cleared"
}

# Usage example of pipeline
setup_data_processing_pipeline() {
    clear_pipeline
    
    # Add filters
    add_pipeline_filter "filter_validate_json"
    add_pipeline_filter "filter_size_limit" "2097152"  # 2MB limit
    
    # Add stages
    add_pipeline_stage "extract" "stage_extract_data" "json"
    add_pipeline_stage "transform" "stage_transform_data" "lowercase"
    add_pipeline_stage "load" "stage_load_data" "file:/tmp/processed_data.txt"
}

# Example usage
# setup_data_processing_pipeline
# result=$(execute_pipeline '{"data": "HELLO WORLD"}' "data_processing")
```

## Advanced Error Handling Patterns

### 1. Circuit Breaker with Retry Pattern
```bash
#!/bin/bash

# Advanced circuit breaker with exponential backoff and jitter
declare -A CIRCUIT_BREAKERS_ADVANCED=()
declare -A CB_FAILURE_COUNTS=()
declare -A CB_SUCCESS_COUNTS=()
declare -A CB_LAST_FAILURE=()
declare -A CB_NEXT_ATTEMPT=()

# Circuit breaker states
readonly CB_CLOSED_STATE=0
readonly CB_OPEN_STATE=1
readonly CB_HALF_OPEN_STATE=2

# Initialize advanced circuit breaker
init_advanced_circuit_breaker() {
    local name="$1"
    local failure_threshold="${2:-5}"
    local timeout_seconds="${3:-60}"
    local success_threshold="${4:-3}"
    
    CIRCUIT_BREAKERS_ADVANCED["$name"]="$CB_CLOSED_STATE:$failure_threshold:$timeout_seconds:$success_threshold"
    CB_FAILURE_COUNTS["$name"]=0
    CB_SUCCESS_COUNTS["$name"]=0
    CB_LAST_FAILURE["$name"]=0
    CB_NEXT_ATTEMPT["$name"]=0
    
    log_debug "Initialized advanced circuit breaker: $name"
}

# Execute with circuit breaker and retry
execute_with_circuit_breaker() {
    local breaker_name="$1"
    local max_retries="${2:-3}"
    local base_delay="${3:-1}"
    local max_delay="${4:-60}"
    shift 4
    local command=("$@")
    
    if [[ -z "${CIRCUIT_BREAKERS_ADVANCED[$breaker_name]:-}" ]]; then
        init_advanced_circuit_breaker "$breaker_name"
    fi
    
    local current_time=$(date +%s)
    
    # Check circuit breaker state
    if ! check_circuit_breaker_state "$breaker_name" "$current_time"; then
        log_error "Circuit breaker '$breaker_name' is OPEN"
        return 1
    fi
    
    # Execute with retry logic
    local attempt=1
    local delay="$base_delay"
    
    while [[ $attempt -le $max_retries ]]; do
        log_debug "Attempt $attempt/$max_retries: ${command[*]}"
        
        if "${command[@]}"; then
            # Success
            record_circuit_breaker_success "$breaker_name"
            log_debug "Command succeeded on attempt $attempt"
            return 0
        else
            local exit_code=$?
            
            # Record failure
            record_circuit_breaker_failure "$breaker_name" "$current_time"
            
            if [[ $attempt -eq $max_retries ]]; then
                log_error "Command failed after $max_retries attempts"
                return $exit_code
            fi
            
            # Calculate delay with jitter
            local jitter=$((RANDOM % delay + 1))
            local total_delay=$((delay + jitter))
            
            log_warn "Attempt $attempt failed, retrying in ${total_delay}s"
            sleep "$total_delay"
            
            # Exponential backoff
            delay=$((delay * 2))
            if [[ $delay -gt $max_delay ]]; then
                delay=$max_delay
            fi
            
            ((attempt++))
        fi
    done
}

# Check circuit breaker state
check_circuit_breaker_state() {
    local name="$1"
    local current_time="$2"
    
    local breaker_config="${CIRCUIT_BREAKERS_ADVANCED[$name]}"
    IFS=':' read -r state failure_threshold timeout_seconds success_threshold <<< "$breaker_config"
    
    case "$state" in
        "$CB_OPEN_STATE")
            # Check if timeout period has passed
            local last_failure="${CB_LAST_FAILURE[$name]}"
            local next_attempt="${CB_NEXT_ATTEMPT[$name]}"
            
            if [[ $current_time -ge $next_attempt ]]; then
                log_info "Circuit breaker '$name' transitioning to HALF_OPEN"
                CIRCUIT_BREAKERS_ADVANCED["$name"]="$CB_HALF_OPEN_STATE:$failure_threshold:$timeout_seconds:$success_threshold"
                CB_SUCCESS_COUNTS["$name"]=0
                return 0
            else
                return 1
            fi
            ;;
        "$CB_HALF_OPEN_STATE")
            return 0
            ;;
        "$CB_CLOSED_STATE")
            return 0
            ;;
        *)
            return 0
            ;;
    esac
}

# Record circuit breaker success
record_circuit_breaker_success() {
    local name="$1"
    
    local breaker_config="${CIRCUIT_BREAKERS_ADVANCED[$name]}"
    IFS=':' read -r state failure_threshold timeout_seconds success_threshold <<< "$breaker_config"
    
    CB_SUCCESS_COUNTS["$name"]=$((CB_SUCCESS_COUNTS["$name"] + 1))
    
    if [[ "$state" == "$CB_HALF_OPEN_STATE" ]]; then
        local success_count="${CB_SUCCESS_COUNTS[$name]}"
        
        if [[ $success_count -ge $success_threshold ]]; then
            log_info "Circuit breaker '$name' transitioning to CLOSED"
            CIRCUIT_BREAKERS_ADVANCED["$name"]="$CB_CLOSED_STATE:$failure_threshold:$timeout_seconds:$success_threshold"
            CB_FAILURE_COUNTS["$name"]=0
            CB_SUCCESS_COUNTS["$name"]=0
        fi
    elif [[ "$state" == "$CB_CLOSED_STATE" ]]; then
        # Reset failure count on success
        CB_FAILURE_COUNTS["$name"]=0
    fi
}

# Record circuit breaker failure
record_circuit_breaker_failure() {
    local name="$1"
    local current_time="$2"
    
    local breaker_config="${CIRCUIT_BREAKERS_ADVANCED[$name]}"
    IFS=':' read -r state failure_threshold timeout_seconds success_threshold <<< "$breaker_config"
    
    CB_FAILURE_COUNTS["$name"]=$((CB_FAILURE_COUNTS["$name"] + 1))
    CB_LAST_FAILURE["$name"]="$current_time"
    
    local failure_count="${CB_FAILURE_COUNTS[$name]}"
    
    if [[ "$state" != "$CB_OPEN_STATE" && $failure_count -ge $failure_threshold ]]; then
        log_warn "Circuit breaker '$name' transitioning to OPEN (failures: $failure_count)"
        CIRCUIT_BREAKERS_ADVANCED["$name"]="$CB_OPEN_STATE:$failure_threshold:$timeout_seconds:$success_threshold"
        CB_NEXT_ATTEMPT["$name"]=$((current_time + timeout_seconds))
    fi
}

# Bulkhead pattern for resource isolation
create_bulkhead() {
    local bulkhead_name="$1"
    local max_concurrent="${2:-5}"
    local queue_size="${3:-10}"
    
    local bulkhead_dir="/tmp/bulkhead_$bulkhead_name"
    mkdir -p "$bulkhead_dir"
    
    # Initialize semaphore
    echo "$max_concurrent" > "$bulkhead_dir/semaphore"
    echo "0" > "$bulkhead_dir/current"
    echo "$queue_size" > "$bulkhead_dir/max_queue"
    echo "0" > "$bulkhead_dir/queue_size"
    
    log_debug "Created bulkhead: $bulkhead_name (max: $max_concurrent, queue: $queue_size)"
}

# Execute with bulkhead isolation
execute_with_bulkhead() {
    local bulkhead_name="$1"
    local timeout="${2:-30}"
    shift 2
    local command=("$@")
    
    local bulkhead_dir="/tmp/bulkhead_$bulkhead_name"
    
    if [[ ! -d "$bulkhead_dir" ]]; then
        create_bulkhead "$bulkhead_name"
    fi
    
    # Try to acquire resource
    if acquire_bulkhead_resource "$bulkhead_name" "$timeout"; then
        log_debug "Acquired bulkhead resource: $bulkhead_name"
        
        # Execute command
        local exit_code=0
        "${command[@]}" || exit_code=$?
        
        # Release resource
        release_bulkhead_resource "$bulkhead_name"
        
        return $exit_code
    else
        log_error "Failed to acquire bulkhead resource: $bulkhead_name"
        return 1
    fi
}

# Acquire bulkhead resource
acquire_bulkhead_resource() {
    local bulkhead_name="$1"
    local timeout="$2"
    local bulkhead_dir="/tmp/bulkhead_$bulkhead_name"
    
    local waited=0
    local check_interval=1
    
    while [[ $waited -lt $timeout ]]; do
        (
            flock -x 200
            
            local max_concurrent
            max_concurrent=$(cat "$bulkhead_dir/semaphore")
            local current
            current=$(cat "$bulkhead_dir/current")
            
            if [[ $current -lt $max_concurrent ]]; then
                echo $((current + 1)) > "$bulkhead_dir/current"
                exit 0
            else
                exit 1
            fi
            
        ) 200>"$bulkhead_dir/lock"
        
        if [[ $? -eq 0 ]]; then
            return 0
        fi
        
        sleep $check_interval
        waited=$((waited + check_interval))
    done
    
    return 1
}

# Release bulkhead resource
release_bulkhead_resource() {
    local bulkhead_name="$1"
    local bulkhead_dir="/tmp/bulkhead_$bulkhead_name"
    
    (
        flock -x 200
        
        local current
        current=$(cat "$bulkhead_dir/current")
        echo $((current - 1)) > "$bulkhead_dir/current"
        
    ) 200>"$bulkhead_dir/lock"
    
    log_debug "Released bulkhead resource: $bulkhead_name"
}
```

This comprehensive advanced patterns framework provides sophisticated design patterns, state management, pipeline processing, and resilience patterns for building complex, maintainable Bash applications in enterprise DevOps environments.